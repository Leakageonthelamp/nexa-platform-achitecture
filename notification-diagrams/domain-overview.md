# Notification — system overview

Plain reading of [`notification-hld.drawio`](notification-hld.drawio) and [`notification-lld.drawio`](notification-lld.drawio).
Ownership stays in [`description.md`](description.md).

<!-- ai:anchor:sentence -->
## Sentence

Templates, the message log, the inbox, and every outbound channel. The contact stays with the customer domain and is read at send time, so no phone number rides the bus.

<!-- ai:anchor:features -->
## Features

### From an order or a refund
- **Contact:** Kafka from Orders and Payments
- **Technology:** Kafka
- **From:** HLD Intake · LLD order.events consumer, payment.events refunded, Channel sender
- An order’s life becomes one message row per channel
- A refund is the only payment that becomes a message
- The contact is read at send time
- A provider failure retries, then the row is failed

### A direct send
- **Contact:** Kafka from Loyalty, Wallet, and Voucher
- **Technology:** Kafka
- **From:** HLD notification.requested · LLD send, Broadcast, Provider receipt
- One customer, and no phone number on the message
- A broadcast is a file of customer ids, read after the commit
- A delivery receipt updates the row
- Marketing waits for quiet hours. A receipt and a one-time code do not

### The shopper
- **Contact:** Customers ask
- **Technology:** gRPC
- **From:** HLD Inbox · devices · LLD RegisterDevice, UnregisterDevice, Inbox, Preferences
- Register a push token, and drop it on logout
- Their own inbox, for this brand
- Which marketing channels they want
- A live frame can be dropped. The app reads again

### One-time code and staff
- **Contact:** Identity asks, staff ask
- **Technology:** gRPC
- **From:** HLD SendOtp and Templates · LLD SendOtp, Templates, Brand channel config, CSC log and resend, Campaign stats
- Identity waits a few seconds for the text
- The code is never written in the log
- Staff edit templates and each brand’s channel setup
- Campaign asks for counts. There is no message fact to subscribe to

<!-- ai:anchor:shared -->
## Shared

**The message log** — one row per person and channel

On the bar: the template, the inbox, the device token, and whether that channel can still be reached. The row keeps the customer id, not the phone or the email.

<!-- ai:anchor:neighbours -->
## Neighbours

- **Identity** — solid, both ends, `asks`. Deliver a one-time code. This domain asks Identity for the contact and consent at send time.
- **Customers** — solid, both ends, `asks`. Inbox, preferences, and the push token.
- **Staff** — solid, both ends, `asks`. Templates, channel setup, the log, and a resend.
- **Campaign** — solid, both ends, `asks`. Counts for a broadcast.
- **Orders** — dashed into this domain, `Kafka`. The order’s life.
- **Payments** — dashed into this domain, `Kafka`. A refund only.
- **Loyalty, Wallet, Voucher, and the edge** — dashed into this domain, `Kafka`. A send, a broadcast, or a provider receipt.
- **Push, email, text, and LINE** — solid, `HTTP`, outward. Not a consume, so there is no ack on that hop.

Nothing is published. A dropped live frame is not a message on the bus.

<!-- ai:anchor:infrastructure -->
## Infrastructure

- **Aurora PostgreSQL** — Templates, the message log, the inbox, and device tokens.
- **Valkey** — Rate limits, a short dedupe, and the live frame. A miss reads the database.
- **S3** — The broadcast audience, written by Campaign and read here.
- **Vault** — Push, email, and LINE secrets per brand.
- **Kafka** — The dashed lines run on this.

<!-- ai:anchor:not-here -->
## Not here

The phone number, the email, consent, and the one-time code itself. The order and the charge are read from messages that already exist. This domain does not call those owners to ask what happened.
