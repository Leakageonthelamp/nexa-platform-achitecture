# Loyalty & MemberCard — system overview

Plain reading of [`loyalty-membercard-hld.drawio`](loyalty-membercard-hld.drawio) and [`loyalty-membercard-lld.drawio`](loyalty-membercard-lld.drawio).
Ownership stays in [`description.md`](description.md).

<!-- ai:anchor:sentence -->
## Sentence

Points, the level, and the card you scan, one profile per brand. A completed order earns the points. Points buy a reward, and they are not a way to pay.

<!-- ai:anchor:features -->
## Features

### Earn
- **Contact:** Kafka from Orders
- **Technology:** Kafka
- **From:** HLD Earn · LLD Earn
- A completed order earns points
- The first one enrols the member and issues the card
- A cancel gives the points back, as a new line
- A guest earns nothing

### Redeem
- **Contact:** Customers ask
- **Technology:** gRPC
- **From:** HLD Redeem · LLD Redeem points
- Points buy a reward voucher
- Oldest points are spent first
- Voucher `IssueReward` issues the code, and a retry cannot issue it twice
- A failed issue is given back

### Correct
- **Contact:** Customer service asks
- **Technology:** gRPC
- **From:** HLD Admin adjust · LLD Adjust
- Credit or debit
- A reason is required
- Only up to their limit
- Replace a card without resetting the points

### Look up
- **Contact:** Customers read
- **Technology:** gRPC
- **From:** HLD Reads · LLD Reads
- Their points and their level
- Their history
- Their member card
- A shopper never writes

<!-- ai:anchor:shared -->
## Shared

**The points book** — balance = sum of postings

On the bar: one member per brand, the card, and append-only postings. A posting is never edited. A cancel or a failed reward writes a new line the other way.

<!-- ai:anchor:neighbours -->
## Neighbours

- **Customers** — solid, both ends, `asks`. Redeem, or read their own profile.
- **Customer service** — solid, both ends, `asks`. A correction, new rules, or a replacement card.
- **Voucher** — solid, one way, `asks`. `IssueReward`. Voucher does not call here.
- **Orders** — dashed into this domain, `Kafka`. Completed earns. Cancelled reverses. Orders do not ask.
- **Notifications** — dashed out, `Kafka`. Earned, reversed, expiring, expired, a new level, or a reward. There is no loyalty fact.
- **Nightly check** — solid, `inside Loyalty`. Technology: Daily job. Points expire at 01:00. The level is reviewed at 02:00. A level change calls `IssueReward` for the new code. The card itself stays here.

<!-- ai:anchor:infrastructure -->
## Infrastructure

- **Aurora PostgreSQL** — The member, the card, and the points book.
- **Kafka** — The dashed lines run on this.

No cache and no file bucket. Points are integers.

<!-- ai:anchor:not-here -->
## Not here

Voucher codes, the basket price, stored value, the order, and the person. A refund does not reverse points. In-store scan waits on the point-of-sale vendor. Points do not cross brands.
