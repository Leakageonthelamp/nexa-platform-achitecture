# Cart & Order — system overview

Plain reading of [`cart-order-hld.drawio`](cart-order-hld.drawio) and [`cart-order-lld.drawio`](cart-order-lld.drawio).
Ownership stays in [`description.md`](description.md).

<!-- ai:anchor:sentence -->
## Sentence

The cart, the order, and the ticket to the kitchen. The shopper waits on checkout. Kafka carries what already happened.

<!-- ai:anchor:features -->
## Features

### Cart
- **Contact:** Customers ask
- **Technology:** gRPC
- **From:** HLD Cart · LLD GetCart and UpdateCart
- One open cart per brand and customer
- The whole cart is replaced, and the version must match
- The price and the deals are worked out live, every time
- A guest cart stays on the device

### Pay
- **Contact:** Customers ask
- **Technology:** gRPC
- **From:** HLD PlaceOrder · LLD PlaceOrder
- Checkout uses the cart the shopper just saw
- The store, the price, the delivery quote, and the deals are checked while they wait
- A card or a QR comes back with a page to finish paying
- A wallet comes back at once, already held

### From outside
- **Contact:** Kafka from partners and the kitchen
- **Technology:** Kafka
- **From:** HLD order.requested · LLD Aggregator create, POS dispatch and status
- An aggregator order is already paid, so it is placed at once
- The kitchen ticket goes out through the point-of-sale proxy, not as a message
- The kitchen’s answer comes back as a message
- Accept captures the money. Reject gives it back

### After checkout
- **Contact:** Kafka from Payments and Delivery
- **Technology:** Kafka
- **From:** HLD payment.events and delivery.events · LLD payment.events consumer, delivery.events consumer
- Authorized means the order is placed
- Failed cancels it
- Delivered completes it
- A repeat of the same version does nothing

<!-- ai:anchor:shared -->
## Shared

**The order** — the status row is the saga

On the bar: the cart, the order, the prices the shopper agreed, and the kitchen ticket. A crash resumes from the last committed status. There is no workflow engine.

<!-- ai:anchor:neighbours -->
## Neighbours

- **Customers** — solid, both ends, `asks`. The cart and checkout.
- **Catalog, Brand & Store, Delivery, Voucher, Payments** — solid, both ends, `asks`. Price, the store, the quote, the deals, and the charge, while the shopper waits.
- **Partners and the kitchen** — dashed into this domain, `Kafka`. A new aggregator order, or the kitchen’s answer.
- **Payments** — dashed out, `Kafka`. Capture or void.
- **Payments** — dashed into this domain, `Kafka`. Authorized, captured, failed, or voided.
- **Delivery** — dashed into this domain, `Kafka`. Delivered, failed, or cancelled.
- **Delivery, Notification, Loyalty, Voucher, and partners** — dashed out, `Kafka`. The order’s life: placed, accepted, rejected, ready, completed, cancelled.
- **Nightly check** — solid, `inside Orders`. Technology: Daily job. Closes an unpaid checkout or a kitchen that never answered, then voids the hold.

<!-- ai:anchor:infrastructure -->
## Infrastructure

- **Aurora PostgreSQL** — The cart, the order, and the kitchen ticket.
- **Kafka** — The dashed lines run on this.

No cache of the store or the menu. Both are read live.

<!-- ai:anchor:not-here -->
## Not here

The menu price, the charge, the store’s hours, and the rider.

## v3 changes not yet in the diagrams

Baseline v3 (2026-10-24) changes three things in this domain. The HLD and LLD are not redrawn yet, so the reading above is the v2 picture.

- **The kitchen ticket** goes out through a POS adapter port with one adapter per vendor, not a single BSL proxy. [`pos-adapters.md`](../../docs/design/pos-adapters.md).
- **The kitchen's answer** is applied by rank and version, so a duplicate or late answer changes nothing, and it never rewrites the agreed prices.
- **A parallel log** of raw and converted order payloads is kept in MongoDB, best effort. [`order-payload-log.md`](../../docs/design/order-payload-log.md).

Per-brand settings are in [`brand-configuration.md`](../../docs/design/brand-configuration.md).
