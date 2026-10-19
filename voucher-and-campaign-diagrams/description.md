# Voucher & Campaign

Voucher & Campaign is the deal. One Go engine owns the campaign rules, the vouchers, the member cards, and the redemption book. Orders asks it to price a basket and to hold the deals at checkout. The hold is spent when the order is placed, and given back when the order is cancelled or rejected.

The shopper waits on the price and the hold. Settling the hold rides `order.events`, because nobody is waiting once the order is committed. A message to the customer leaves as `notification.requested`, a send or a broadcast. This domain does not deliver it.

| | |
| --- | --- |
| **Owns** | The campaign rules, vouchers, member cards, holds, the redemption ledger, and the broadcast audience file. |
| **Does not own** | The menu price (Catalog), the cart and the agreed total (Orders), the charge (Payment), points (Loyalty), or message delivery (Notification). |
| **How it is called** | Orders calls `EvaluateBasket` on every cart read, then `ReserveRedemptions` at `PlaceOrder`, keyed by `order_id`. `admin-bff` writes campaigns, vouchers, member cards, and audiences. `customer-bff` reads the shopper's own vouchers and member card. A shopper never writes. |
| **Kafka** | Consumes `order.events` (`placed` spends the hold, `cancelled` and `rejected` release it). Sends `notification.requested` (`send` or `broadcast`). There is no campaign topic. |

Deals on the cart are a draft answer to O-21. v1 applies the rules in a fixed order. It does not search for the best stack, and it does not enforce a margin floor.

## Diagrams

**Overview** — `voucher-campaign-overview.drawio`

`domain-overview.md` is the plain reading of the HLD and the LLD. Read that instead of the overview page.

Deals, the hold, settling it, and who may write or read the book. A solid line is someone asking. A dashed line is Kafka. Not a replacement for an SHLD. The rulebook is [`overview-guideline.md`](../overview-guideline.md).

**HLD** — `voucher-campaign-hld.drawio`

One page: the four doors, the book, `order.events` in, and `notification.requested` out.

**LLD** — `voucher-campaign-lld.drawio`

| Page | Flow |
| --- | --- |
| 1 | EvaluateBasket |
| 2 | ReserveRedemptions |
| 3 | `order.events` consumer |
| 4 | Admin write |
| 5 | ListVouchers and GetMembercard |
| 6 | Schedule cron |
