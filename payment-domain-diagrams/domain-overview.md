# Payment & Billing — system overview

Plain reading of [`payment-billing-hld.drawio`](payment-billing-hld.drawio) and [`payment-billing-lld.drawio`](payment-billing-lld.drawio).
Ownership stays in [`description.md`](description.md).

<!-- ai:anchor:sentence -->
## Sentence

The charge, the capture, the refund, and the rider payout. The shopper waits for the pay page. Capture, the gateway’s answer, and a rider payout travel as messages.

<!-- ai:anchor:features -->
## Features

### Charge
- **Contact:** Orders ask
- **Technology:** gRPC
- **From:** HLD Checkout and Top-up · LLD CreateTransaction
- A card or a QR waits for a page to finish paying
- A wallet hold comes back at once, with no page
- The charge is saved before the gateway, or Wallet, is called
- A top-up uses the same call and is captured at once

### Capture
- **Contact:** Kafka from Orders
- **Technology:** Kafka
- **From:** HLD Capture · void · LLD Capture and void, Gateway webhook
- The kitchen’s accept captures the money
- A reject or a timeout voids it
- The gateway’s own answer arrives as a message, after the signature is checked
- The invoice is written in the same app, after capture

### Refund
- **Contact:** Customer service asks
- **Technology:** gRPC
- **From:** HLD Refund · LLD Refund
- Part or all of a captured payment
- The agent waits for “accepted”, not for the gateway
- The gateway is called after the commit
- A wallet tender is credited back through Wallet, not the card

### Rider pay
- **Contact:** Kafka from Delivery
- **Technology:** Kafka
- **From:** HLD payout · LLD Rider payout
- One payout when a trip is delivered
- This domain calls the payout partner
- The result goes back as paid or failed
- Delivery settles its own row from that result

<!-- ai:anchor:shared -->
## Shared

**The transaction** — one table, one brand on every row

On the bar: the attempt, the brand’s gateway account, and the outbox. Food is authorized first and captured after the kitchen accepts. There is no second ledger.

<!-- ai:anchor:neighbours -->
## Neighbours

- **Orders** — solid, both ends, `asks`. The charge at checkout.
- **Customers** — solid, both ends, `asks`. A wallet top-up.
- **Customer service** — solid, both ends, `asks`. A refund.
- **Orders** — dashed into this domain, `Kafka`. Capture or void.
- **The gateway** — dashed into this domain, `Kafka`. The pay result, after the edge has checked the signature.
- **Delivery** — dashed into this domain, `Kafka`. A rider payout, and a delivered trip to invoice.
- **Orders, Wallet, Delivery, and Notification** — dashed out, `Kafka`. Authorized, captured, failed, voided, refunded, paid out, or payout failed. Notification keeps a refund only.

<!-- ai:anchor:infrastructure -->
## Infrastructure

- **Aurora PostgreSQL** — The transactions and each brand’s gateway account.
- **S3** — The tax invoice and the receipt.
- **Kafka** — The dashed lines run on this.

Gateway secrets stay in the brand’s payment config. They are not on the bus.

<!-- ai:anchor:not-here -->
## Not here

The order, the store, and the wallet balance. A top-up’s stored value is credited by the wallet when this domain says the charge was captured. The gateway never calls this domain directly.
