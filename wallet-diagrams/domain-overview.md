# Wallet — system overview

Plain reading of [`wallet-hld.drawio`](wallet-hld.drawio) and [`wallet-lld.drawio`](wallet-lld.drawio).
Ownership stays in [`description.md`](description.md).

<!-- ai:anchor:sentence -->
## Sentence

One wallet per brand. It pays like any other tender, and the real money stays in Payments.

<!-- ai:anchor:features -->
## Features

### Spend
- **Contact:** Payments asks
- **Technology:** gRPC
- **From:** HLD Payment port · LLD Hold, Capture and release, Refund to wallet
- Hold at checkout, and only the held amount moves
- Spend when the kitchen accepts
- Give the hold back on a reject or a void
- A refund of a wallet spend credits the balance

The end-to-end pay-with-wallet page confirms this door. It is not its own feature. Orders do not call here.

### Top up
- **Contact:** Kafka from Payments
- **Technology:** Kafka
- **From:** HLD Top-up credit · LLD Top-up credit
- Only a captured top-up is credited
- Every other payment message is ignored
- The wallet is created if it is new
- The shopper is told after the credit

### Correct
- **Contact:** Customer service asks
- **Technology:** gRPC
- **From:** HLD Admin adjust · LLD Adjust
- Credit or debit
- A reason is required
- Only up to their limit
- The audit row is in the same commit

### Look up
- **Contact:** Customers read
- **Technology:** gRPC
- **From:** HLD Reads · LLD GetWallet and ListEntries
- Their own balance
- Their own history
- A shopper never writes
- A missing wallet reads as zero

<!-- ai:anchor:shared -->
## Shared

**The ledger** — available = balance − held

On the bar: the wallet row, holds, and append-only entries. One wallet per brand and customer. Only an entry moves the balance. A hold moves what is held.

<!-- ai:anchor:neighbours -->
## Neighbours

- **Payments** — solid, both ends, `asks`. Hold, capture, release, and refund.
- **Payments** — dashed into this domain, `Kafka`. A captured top-up.
- **Notifications** — dashed out, `Kafka`. Top-up, correction, or refund. There is no wallet fact.
- **Nightly check** — solid, `inside Wallet`. Technology: Daily job. Every day at 03:00. Flags a mismatch and an old hold. Never fixes them.

<!-- ai:anchor:infrastructure -->
## Infrastructure

- **Aurora PostgreSQL** — The ledger is stored here.
- **Kafka** — The dashed lines run on this.

No cache and no file bucket. A balance is never cached.

<!-- ai:anchor:not-here -->
## Not here

The card charge, the tax invoice, loyalty points, and the checkout timeout. Orders, vouchers, and member cards do not call Wallet.
