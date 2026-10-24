# Voucher & Campaign — system overview

Plain reading of [`voucher-campaign-hld.drawio`](voucher-campaign-hld.drawio) and [`voucher-campaign-lld.drawio`](voucher-campaign-lld.drawio).
Ownership stays in [`description.md`](description.md).

<!-- ai:anchor:sentence -->
## Sentence

The deals and the vouchers on the basket. The shopper waits for the price and the hold. Settling the hold rides the order, because nobody is waiting once it is placed. The card you scan is Loyalty.

<!-- ai:anchor:features -->
## Features

### Price
- **Contact:** Orders ask
- **Technology:** gRPC
- **From:** HLD Basket · LLD EvaluateBasket
- Every cart read, after the menu price
- Rules run in a fixed order
- A code that does not apply comes back on the reply
- Nothing is spent

### Hold
- **Contact:** Orders ask
- **Technology:** gRPC
- **From:** HLD Hold · LLD ReserveRedemptions
- At checkout, keyed by the order
- The hold counts against the cap
- The same order does not hold twice
- Spending it waits for the order message

### Settle
- **Contact:** Kafka from Orders
- **Technology:** Kafka
- **From:** HLD Order facts · LLD order.events consumer
- Placed spends the hold
- Cancelled or rejected gives it back
- Accepted, ready, and completed do nothing
- A second delivery of the same version does nothing

### Write and read
- **Contact:** Staff ask, customers read
- **Technology:** gRPC
- **From:** HLD Admin write and Reads · LLD Admin write, ListVouchers, IssueReward
- Staff write campaigns, vouchers, and an audience
- Loyalty asks for a reward code, and waits
- A message to the customer is written in that same commit
- A shopper reads their own vouchers
- A shopper never writes

<!-- ai:anchor:shared -->
## Shared

**The book** — rules, what was issued, and one hold per order

On the bar: campaigns, vouchers, holds, and the redemption record. A hold is a row, so it cannot be spent twice by a cache miss. The card you scan is not on this bar.

<!-- ai:anchor:neighbours -->
## Neighbours

- **Orders** — solid, both ends, `asks`. Price the basket, then hold the deals.
- **Customers** — solid, both ends, `asks`. Their own vouchers.
- **Staff** — solid, both ends, `asks`. Campaigns, vouchers, and the audience.
- **Loyalty** — solid, one way, `asks`. `IssueReward`. This domain does not call Loyalty.
- **Catalog** — solid, one way, `asks`. The item list, only when a rule names items.
- **Orders** — dashed into this domain, `Kafka`. Placed, cancelled, or rejected.
- **Notifications** — dashed out, `Kafka`. A send, or a broadcast. There is no campaign fact.
- **Nightly check** — solid, `inside Voucher`. Technology: Daily job. Every five minutes: open a campaign whose time has come, close one whose time has passed, and expire a hold the order never closed.

<!-- ai:anchor:infrastructure -->
## Infrastructure

- **Aurora PostgreSQL** — Rules, vouchers, holds, and redemptions.
- **S3** — The broadcast audience. Customer ids only.
- **Kafka** — The dashed lines run on this.

No cache. Amounts are integer minor units.

<!-- ai:anchor:not-here -->
## Not here

The cart, the agreed total, the menu price, points, the card you scan, and message delivery. The shopper reads their own vouchers. Orders price and hold the deals. Loyalty asks for a reward code.
