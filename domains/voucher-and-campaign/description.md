# Voucher & Campaign

Voucher & Campaign is the deal. One Go engine owns the campaign rules, the vouchers, and the redemption book. It does not own the card you scan. Orders asks it to price a basket and to hold the deals at checkout. The hold is spent when the order is placed, and given back when the order is cancelled or rejected. Loyalty calls `IssueReward` when points buy a code, or when a level change replaces one.

The shopper waits on the price and the hold. Settling the hold rides `order.events`, because nobody is waiting once the order is committed. A message to the customer leaves as `notification.requested`, a send or a broadcast. This domain does not deliver it.

| | |
| --- | --- |
| **Owns** | The campaign rules, vouchers, holds, the redemption ledger, and the broadcast audience file. |
| **Does not own** | The menu price (Catalog), the cart and the agreed total (Orders), the charge (Payment), points and the card you scan (Loyalty), or message delivery (Notification). |
| **How it is called** | Orders calls `EvaluateBasket` on every cart read, then `ReserveRedemptions` at `PlaceOrder`, keyed by `order_id`. Loyalty calls `IssueReward` and waits; the key is the redemption id, and this is not the admin write. `admin-bff` writes campaigns, vouchers, and audiences, and may `IssueVoucher` for staff. `customer-bff` reads the shopper's own vouchers. A shopper never writes. |
| **Kafka** | Consumes `order.events` (`placed` spends the hold, `cancelled` and `rejected` release it). Sends `notification.requested` (`send` or `broadcast`). There is no campaign topic. |

Deals on the cart are a draft answer to O-21. v1 applies the rules in a fixed order. It does not search for the best stack, and it does not enforce a margin floor.

## v-next (2026-10-25): vouchers at the table bill (proposal)

For postpaid table ordering ([`postpaid-table-ordering.md`](../../docs/design/postpaid-table-ordering.md), P-47, P-51), Order calls `EvaluateBasket` on the whole tab at bill time (`channel = dine_in`) and `ReserveRedemptions(order_id)` only when the diner pays. A postpaid hold is committed on `order.events{completed}` and released on `cancelled`, not committed on `placed`. This is a change to this domain's consumer. Whether a voucher may be used after rounds were sent is open (O-45).

## Diagrams

**Overview** — `voucher-campaign-overview.drawio`

`domain-overview.md` is the plain reading of the HLD and the LLD. Read that instead of the overview page.

Deals, the hold, settling it, and who may write or read the book. A solid line is someone asking. A dashed line is Kafka. Not a replacement for an SHLD. The rulebook is [`overview-guideline.md`](../../docs/overview-guideline.md).

**HLD** — `voucher-campaign-hld.drawio`

One page: the doors, the book, `order.events` in, `IssueReward` from Loyalty, and `notification.requested` out. The card you scan is Loyalty.

**LLD** — `voucher-campaign-lld.drawio`

| Page | Flow |
| --- | --- |
| 1 | EvaluateBasket |
| 2 | ReserveRedemptions |
| 3 | `order.events` consumer |
| 4 | Admin write |
| 5 | ListVouchers |
| 6 | Schedule cron |
| 7 | IssueReward |
