# Payment & Billing HLD — presenter script

Source: [`payment-billing-hld.drawio`](payment-billing-hld.drawio). About 12 minutes, then questions. Screen-share the diagram and leave it zoomed out until a section says to zoom.

The sentence on the title is the whole talk: **charge is sync, capture and the webhook are the bus, and a rider payout calls TrueMoney.**

This domain owns two topics: `payment.requested` and `payment.events`. The full list lives in [`kafka-topics.md`](../../docs/kafka-topics.md).

---

## 0. Open (45 seconds)

Point at the title, then the grey subtitle.

> One Go engine. Checkout returns `authorize_url` on the gRPC. Capture, void, and the gateway webhook are one command. Statement is a mode of this app, not a second service. There is one transactions table, and `brand_id` is on every hop.

Walk the four pills once:

1. Orange — gRPC. Checkout, refund, and top-up. They return `authorize_url`.
2. Blue — HTTP. Omise for a charge, TrueMoney for a rider payout, plus the webhook in at the edge.
3. Purple — the command, `payment.requested`.
4. Green — the fact, `payment.events`.

---

## 1. Callers (2 minutes)

Zoom to **1. Callers**.

> **Order** runs the checkout saga. It calls `CreateTransaction` with an `idempotency_key`, so a retry never charges twice. Later it publishes capture after the POS accepts, or void if the kitchen rejects.
>
> **customer-bff** calls `CreateTransaction` only for a wallet top-up: 3DS, QR, and PromptPay. An order checkout always goes through Order.
>
> **admin-bff**: refund, with an `idempotency_key`, and partial refunds are allowed. The admin is waiting.
>
> **webhook-adapter**: HTTP comes in and the signature is checked here, then it publishes the command.
>
> **Omise** is the gateway that ships for a charge, with one account per brand.
>
> **TrueMoney** is the rider payout channel. Payment calls it. It does not call Payment. Checkout stays on Omise.
>
> **Delivery** is not a gRPC caller. It publishes `payout` when a trip is delivered.
>
> Omise never calls Payment directly.

---

## 2. Kafka in (1 minute)

Zoom to **2. Kafka in**.

> `payment.requested` is one `oneof`: capture, void, webhook, payout. It is keyed `brand_id:transaction_id`, so they stay in order. Charge and refund are not on this topic. Delivery publishes `payout` in the delivered commit, one per trip, with `brand_id = mfg`. Payment uses that id as the transaction id.
>
> Ack after the transaction row and the outbox commit. A replay of the same `event_id` is a no-op.
>
> Refund stays gRPC. The admin is waiting, and the outbox worker calls the gateway after the commit.

---

## 3. The engine (4 minutes)

Zoom to **3. Payment engine**.

> **Checkout** persists, then makes a sync charge, and `authorize_url` comes back on the gRPC.
>
> **Transactions** is one table, with `brand_id` as a column and `payment_ref` on the attempt.
>
> **Brand config** holds that brand's provider and keys. One gateway per transaction.

Walk the left column.

> **Top-up** uses the same charge path as checkout. Wallet reads the fact later.
>
> **Refund** is an admin gRPC, then the outbox. **Gateway worker**: the outbox calls Omise for a charge, or TrueMoney for a rider payout. 2C2P is a port and is not shipped.
>
> **Payout** is the same consumer as capture and void. The worker calls TrueMoney. The fact comes back as `paid_out` or `payout_failed`.
>
> **Capture, void, webhook**: match `payment_ref`, then the outbox.

Point at the right column.

> **Statement mode** is the same app. It writes the invoice after capture. It is not a topic and not a service.
>
> **No charge failover.** One Omise account per brand. TrueMoney is payout only. 2C2P is still the unshipped charge port.

Point at the note at the bottom.

> Food is auth-then-capture. Authorize places a hold. Money moves at captured, and only after Order has accepted the POS ticket. The ledger is this table.

---

## 4. Facts out (1 minute)

> `payment.events` is the lifecycle, kept 7 days: authorized, captured, failed, voided, refunded, paid_out, payout_failed.
>
> Wallet keeps the records whose purpose is a top-up. There is no wallet topic.

---

## 5. Consumers (1 minute)

> **Order** moves the order status. **Wallet** keeps purpose equals top-up. **Delivery** keeps `paid_out` and `payout_failed`, and settles the trip row. **Notification** keeps refunded, per [`kafka-topics.md`](../../docs/kafka-topics.md).
>
> Statement does not subscribe. It runs after the same commit.

---

## 6. Data, decisions, not this domain (2 minutes)

> Aurora holds transactions, attempts, brand config, outbox, and audit. S3 holds the tax invoice and receipt that Statement mode writes. Keys live in brand config, not on the bus and not in Brand.

Read the bold words in **Decisions**. Then the cost line:

> A consumer that starts late only sees 7 days of `payment.events`. Older rows are read from Postgres, not replayed.

**Not this domain**: Order runs the saga, Brand is who the brand is, Wallet owns the balance, Catalog owns the price, Identity owns the shopper.

---

## 7. Close (30 seconds)

> The shopper waits on gRPC. Capture, void, and the webhook ride one command. The lifecycle goes out as one fact. One table is the ledger.

Stop talking. Take questions.

---

## If they ask

**Why is charge not a command?**
The shopper is waiting for `authorize_url`. A command cannot return it.

**What about a forged webhook?**
A bad signature dies at the edge and never reaches the topic.

**Why no second charge gateway?**
One charge provider per brand. 2C2P is a port, shipped when a brand needs a second live provider. TrueMoney is not that port. It pays the rider.

**Why TrueMoney for the rider?**
Delivery publishes `payout` and does not call a wallet itself. Payment calls TrueMoney and publishes `paid_out` or `payout_failed`. The rider's wallet id is not on the bus. Payment resolves it from `rider_id`. Where that ref is stored is still open.

**Where is the ledger service?**
The transactions table is the ledger. A separate service waits until finance asks for one.
