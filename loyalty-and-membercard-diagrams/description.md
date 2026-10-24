# Loyalty & MemberCard

Loyalty & MemberCard is the points book and the card you scan. One Go engine holds one profile per brand per customer: the level, the card, and an append-only points ledger. Balance is the sum of postings. It is not a column.

A completed order earns points. The first one enrols the member, because Identity publishes no join. A cancel writes a reversing posting when points were already posted. A guest earns nothing. Points buy a reward voucher; they are not a way to pay for an order.

| | |
| --- | --- |
| **Owns** | The member per brand, the level, the card you scan, receipts, earn rules, the points ledger, and reward prices. |
| **Does not own** | The person (Identity), voucher codes and the redemption book (Voucher & Campaign), the basket price (Voucher & Campaign), stored value (Wallet), the order, or message delivery. |
| **How it is called** | `customer-bff` reads the profile and calls `RedeemPoints`. `admin-bff` calls `AdjustPoints` and publishes rules, with the `loyalty.adjust` grant, a reason, and a limit. Orders never call. `RedeemPoints` calls Voucher `IssueReward` with the redemption id. |
| **Kafka** | Consumes `order.events` (`completed` earns, `cancelled` reverses). Sends `notification.requested`. There is no loyalty topic. |

The source is the [Loyalty target architecture](https://minordigital.atlassian.net/wiki/spaces/BackEnd/pages/3898146819/Loyalty+Domain+-+Target+Architecture) (reviewed 2026-10-15). Topics are the ones in [`kafka-topics.md`](../kafka-topics.md). `loyalty.events`, `customer.lifecycle.fact`, and a consume of `payment.events` are not drawn: they are not in that list. The card you scan lives here. Voucher owns the code. `RedeemPoints` and a level change call `IssueReward` and wait.

## Diagrams

**Overview** — `loyalty-membercard-overview.drawio`

`domain-overview.md` is the plain reading of the HLD and the LLD. Read that instead of the overview page.

Redeem, earn, a correction, and a lookup. A solid line is someone asking. A dashed line is Kafka. Not a replacement for an SHLD. The rulebook is [`overview-guideline.md`](../overview-guideline.md).

**HLD** — `loyalty-membercard-hld.drawio`

One page: the doors, the member and the ledger, `order.events` in, and `notification.requested` out.

**LLD** — `loyalty-membercard-lld.drawio`

| Page | Flow |
| --- | --- |
| 1 | `order.events` — earn, enrol, reverse |
| 2 | RedeemPoints |
| 3 | AdjustPoints and card replace |
| 4 | GetMember, GetBalance, ListPostings, GetCard |
| 5 | Points expiry cron `0 1 * * *` |
| 6 | Tier review cron `0 2 * * *` |
