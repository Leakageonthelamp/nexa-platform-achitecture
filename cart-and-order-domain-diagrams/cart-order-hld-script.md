# Cart & Order HLD — presenter script

Source: [`cart-order-hld.drawio`](cart-order-hld.drawio). About 12 minutes, then questions. Screen-share the diagram and leave it zoomed out until a section says to zoom.

The sentence on the title is the whole talk: **the shopper waits on gRPC, the bus carries what already happened.**

This domain owns two topics: `order.requested` and `order.events`. It consumes `payment.events` and `delivery.events`. It does not consume `store.changed`: it checks the store live with `ResolveStore` and keeps no copy. The full list lives in [`kafka-topics.md`](../kafka-topics.md).

---

## 0. Open (45 seconds)

Point at the title, then the grey subtitle.

> One Go engine. It owns the cart, the order, and the POS ticket. It is the saga: authorize, then capture after the POS accepts. Promise and VIVI wait until a brand needs them. `brand_id` is on every hop.

Walk the four pills once:

1. Orange — gRPC. `GetCart`, `UpdateCart`, `PlaceOrder`, `ResolveStore`, `PriceLines`, `GetQuote`, `CreateTransaction`.
2. Blue — HTTP. The BSL proxy and the POS ticket.
3. Purple — the command, `order.requested`.
4. Green — the fact, `order.events`.

---

## 1. Callers (2 minutes)

Zoom to **1. Callers**.

> **customer-bff** builds the cart with `GetCart` and `UpdateCart`, then calls `PlaceOrder` with an `idempotency_key`, the cart version and total the shopper saw, plus a `quote_id` for a delivery order. The shopper waits, and `authorize_url` comes back on the gRPC. A wallet order gets no URL, because Payment holds the balance straight away. A retry with the same key returns the first answer, so a double tap never makes two orders.
>
> The **partner-adapter** carries Grab, LINE MAN, and Shopee Food: create, replace, cancel.
>
> **BSL order state** is a POS webhook, not a fact. The adapter publishes the command.
>
> Order calls out to four places. **Brand & Store** for `ResolveStore`, live. **Catalog** for `PriceLines`, sync, so Order never recomputes the price. **Delivery** for `GetQuote`, sync, so the fee on the order is the fee the shopper was quoted. **Payment** for `CreateTransaction`, sync. Capture and void leave as a command.

> Own-app checkout does not enter through Kafka. The shopper is waiting.

---

## 2. Kafka in (1 minute)

Zoom to **2. Kafka in**.

> `order.requested` is one `oneof`: create, replace, cancel, POS status. It is keyed `brand_id:order_id`, so a cancel cannot pass the create.
>
> `payment.events` is Payment's lifecycle.
>
> `delivery.events` is Delivery's lifecycle. Order acts on three variants: delivered, failed, and cancelled. The rest are an Ack with no work.
>
> Three consumes. Each Ack is the end of that consume. A repeat of the same version is a no-op.
>
> There is no `store.changed` here. Order asks Brand & Store at checkout instead of keeping a copy of the store.

---

## 3. The engine (4 minutes)

Zoom to **3. Cart & Order engine**.

> **Cart** is the top row. It is lines only: no price is stored. `GetCart` and `UpdateCart` price it live with `PriceLines` every time, so a sold-out item or a new menu shows up on the next read. `UpdateCart` sends the whole cart with the version it last saw; a stale version gets `ABORTED` and the current cart. One open cart per brand and customer. A guest cart stays on the device.
>
> **PlaceOrder** checks out the cart. It is gRPC, the shopper waits, and there is no Ack on this path. If the live total differs from the total the shopper saw, it returns `price_changed` and commits nothing. A second checkout with a new key cancels the first pending order and voids its hold, so one cart never holds money twice. The cart is deleted when the order is placed.
>
> **Check, price, then pay**: `ResolveStore` on Brand & Store rejects a hidden, not-live, or closed store. Then `PriceLines` on Catalog, `GetQuote` on Delivery for a delivery order, then `CreateTransaction` on Payment. Order stores the price lines and the fee it was given, because the receipt and any refund need the price at order time. **authorize_url** returns on the gRPC for a card or QR, and 3DS finishes on the webhook. A wallet order has no URL.
>
> **State machine**: rows in Postgres, and the status is the recovery point. **Auth, then capture**: hold at authorize, capture only after the POS accepts.
>
> **Outbox relay**: state and outbox in one commit, and facts leave after the commit. **POS dispatch worker**: outbox, then the BSL proxy over gRPC. Not a topic.
>
> **Replace** cancels the live POS ticket, then creates the new one.
>
> **Checkout sweeper** is a cron. Every minute it closes orders still waiting for payment or for the POS after their window, and sends a void for the held money. That is how timeouts work without a timer service.

Point at the ponytail note.

> The saga is the status column plus the outbox. Ceiling: a crash retries from the last committed status, not from mid-call. Upgrade: Temporal or Cadence, when a step needs a durable timer.

Point at the three consume handlers at the bottom.

> **Aggregator and POS status**: apply if newer, then run the state machine. **Payment result** moves the order status: authorized makes the order placed, failed cancels it, captured and voided close the payment step. **Delivery result**: delivered completes the order. Failed and cancelled are open (O-14): auto-cancel and refund, or hand to CSC. Until that is decided, they go to the CSC queue.

> BSL only. Promise and VIVI are the same worker with another proxy, added when a brand onboards.

---

## 4. Facts out (1 minute)

> `order.events` is the lifecycle, kept 7 days: placed, accepted, rejected, ready, completed, cancelled. Published only after the commit. `placed` leaves only after Payment says authorized, so the kitchen never sees an unpaid order. Create and replace do not get their own topics.

---

## 5. Consumers (1 minute)

> **Delivery** dispatches on accepted and cancels the provider job on cancelled. **Notification** sends push, SMS, and status. **Loyalty** earns on completed. **Voucher** redeems on completed. The **partner-adapter** sends status back to the aggregator.

---

## 6. Data, decisions, not this domain (2 minutes)

> Aurora holds carts, orders, price lines, status, the POS ticket, the outbox, and history. The status row is the saga. There is no workflow engine and no internal topic for the POS call.

Read the bold words in **Decisions**: `PlaceOrder` is gRPC, one command topic, the POS is a worker, one lifecycle topic, cart is lines not prices, live store check, live delivery quote, sweeper not a timer service, BSL only for now.

**Not this domain**: Catalog owns the price, Payment the charge, capture, and refund, Brand & Store the hours, zone, and hidden flag (read live with `ResolveStore`), Delivery the fleet, the ETA, and the fee (read live with `GetQuote`), Identity the shopper.

---

## 7. Close (30 seconds)

> The shopper waits on gRPC. Aggregators and the POS ride one command. The lifecycle goes out as one fact. The saga is a status column.

Stop talking. Take questions.

---

## If they ask

**What if the process crashes mid-saga?**
It resumes from the last committed status. A redelivery of the same version is a no-op.

**Why no Temporal?**
No step needs a durable timer yet. Timeouts are the checkout sweeper cron. That is the ponytail ceiling, with the upgrade path written down.

**Can a cancel overtake a create?**
No. Both are on `order.requested` with the same key, so they share one partition.

**Why is the POS call not a topic?**
Only this app would consume it. That makes it a worker with a gRPC call to the BSL proxy.

**Why not keep a copy of the store?**
The store is online and real-time. `ResolveStore` is a Valkey hit on Brand & Store, so checkout always sees the current status. The cost: checkout fails if Brand & Store is down.

**Why does Order call `GetQuote` instead of computing the fee?**
Delivery owns the quote (P-22). The shopper saw a fee before tapping Pay, and `GetQuote` returns exactly that fee. An expired, used, or wrong-brand quote is `FAILED_PRECONDITION`, and nothing is committed. The cost: a fourth sync dependency at checkout.

**How is a wallet order different?**
Only inside Payment. Order still calls `CreateTransaction`, and Payment calls Wallet instead of Omise (D-09). The hold is immediate, so there is no `authorize_url`, and the order is still placed only on `payment.events{authorized}`. A short balance is `FAILED_PRECONDITION`, and the app offers a card for the whole order (P-16).

**Why not store the price in the cart?**
A stored price goes stale the moment Catalog publishes a menu or an item sells out. The cart keeps lines, and the price is derived live (P-31). The cost: every cart view is a `PriceLines` call, which Catalog serves from its Valkey menu cache.

**What if the price changes between the cart and Pay?**
`PlaceOrder` prices again and compares with the total the shopper saw. A difference is `price_changed`, nothing is committed, and the app shows the new total (P-32).

**Why is there no cart topic, and do carts expire?**
No other domain reads a cart, so a topic would have no consumer. There is no expiry: one row per brand and customer, kept until the next checkout. That is a ponytail ceiling; the upgrade is a purge in the checkout sweeper.

**What happens when no rider can be found?**
Delivery publishes `delivery.events{failed}`. Whether Order auto-cancels and refunds or waits for CSC is open (O-14). Until then it goes to the CSC queue.
