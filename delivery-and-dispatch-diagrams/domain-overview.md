# Delivery & Dispatch — system overview

Plain reading of [`delivery-dispatch-hld.drawio`](delivery-dispatch-hld.drawio) and [`delivery-dispatch-lld.drawio`](delivery-dispatch-lld.drawio).
Ownership stays in [`description.md`](description.md).

<!-- ai:anchor:sentence -->
## Sentence

The quote, the rider job, and the rider’s earnings. The shopper waits only for the price. Dispatch starts when the kitchen accepts.

<!-- ai:anchor:features -->
## Features

### Quote
- **Contact:** Customers and Orders ask
- **Technology:** gRPC
- **From:** HLD Quote · LLD Quote and GetQuote
- The fee, the distance, and a rough arrival time
- No fleet provider is called for a quote
- Road distance is used only past a threshold
- Checkout must carry the quote it was shown

### Dispatch
- **Contact:** Kafka from Orders
- **Technology:** Kafka
- **From:** HLD order.events door · LLD accepted to dispatch, cancel, scheduled dispatch, no-rider sweeper
- The kitchen’s accept starts the job
- A future order waits until it is due
- A cancel tells the provider to stop
- No rider in time means the next provider, then a failure

### On the road
- **Contact:** Kafka from the fleet
- **Technology:** Kafka
- **From:** HLD delivery.requested · LLD provider update, rider sync, roster, store sync
- A status applies only if it is further along
- A rider arrives as a reference, never a phone number
- A store change updates the merchant at the provider
- This domain does not keep a copy of the store

### Rider pay
- **Contact:** Kafka to Payments
- **Technology:** Kafka
- **From:** HLD earnings ledger and payment.requested · LLD earnings, payout
- A delivered trip writes one earnings row
- That same commit asks Payments to pay it
- Paid or failed comes back as a message
- Staff can assign, redispatch, or mark delivered while they wait

An external brand uses the same quote and then asks for a job at once, because there is no kitchen. That path is not a separate feature. The end-to-end page only confirms these doors.

<!-- ai:anchor:shared -->
## Shared

**The delivery** — seven steps, and a delivered trip never changes

On the bar: the quote, the job, the status log, and the earnings row. Riders and their pay use the group tenant, not the order’s brand. One port talks to every fleet. An account is a config row.

<!-- ai:anchor:neighbours -->
## Neighbours

- **Customers** — solid, both ends, `asks`. A quote, or the status of their job.
- **Orders** — solid, both ends, `asks`. The quote at checkout.
- **Identity** — solid, one way, `asks`. The drop-off address, when the job is created. It is not copied.
- **Partners** — solid, both ends, `asks`. A quote and a job for an external brand.
- **Customer service** — solid, both ends, `asks`. Assign, cancel, redispatch, mark delivered, and rider admin.
- **Orders** — dashed into this domain, `Kafka`. Accepted starts dispatch. Cancelled stops it.
- **The fleet** — dashed into this domain, `Kafka`. Status, rider, and roster, after the edge has checked the signature.
- **Brand & Store** — dashed into this domain, `Kafka`. Sync the merchant. The store is not copied.
- **Payments** — dashed into this domain, `Kafka`. Paid out, or payout failed.
- **Orders, Notification, partners, and Payments** — dashed out, `Kafka`. Dispatched through delivered, failed, or cancelled.
- **Payments** — dashed out, `Kafka`. Pay this trip.
- **Nightly check** — solid, `inside Delivery`. Technology: Daily job. Tries the next provider when no rider comes, starts a scheduled job before it is due, and checks payouts against Payments. It never sends the money.

<!-- ai:anchor:infrastructure -->
## Infrastructure

- **Aurora PostgreSQL** — Jobs, quotes, riders, earnings, and shifts.
- **S3** — Rider documents, the shift file, and exports.
- **Vault** — Fleet secrets.
- **Kafka** — The dashed lines run on this.

No cache of the delivery. Amounts are integer minor units.

<!-- ai:anchor:not-here -->
## Not here

The order, the store’s zone, the customer’s address (read live), and the payout itself. Payments calls the payout partner. This domain does not.
