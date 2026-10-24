# Cart & Order

Cart & Order is the checkout. One Go engine owns the cart, the order, and the POS ticket. It runs the saga: price the basket, authorize the payment, send the ticket to the store, then capture after the POS accepts or void if the kitchen rejects.

The shopper waits on gRPC. The bus carries what already happened. Own-app checkout does not enter through Kafka. `PlaceOrder` takes an `idempotency_key`, so a double tap never makes two orders. A wallet order runs the same saga: Payment holds the balance at once, so there is no `authorize_url`. Aggregator orders (Grab, LINE MAN, Shopee Food) skip payment: the partner has already collected the money, and `partner-adapter` publishes `order.requested`.

Order does not recompute the price or the delivery fee, and does not keep a copy of the store. At checkout it asks Brand & Store for `ResolveStore`, Catalog for `PriceLines`, and Delivery for `GetQuote`, live.

The cart is lines and coupon codes, not prices. There is one open cart per brand and customer, and `GetCart` and `UpdateCart` price it live with `PriceLines`, then apply deals with Voucher & Campaign `EvaluateBasket`, on every read. `PlaceOrder` checks out that cart by `cart_version` and the total the shopper saw. If the live total differs, it returns `price_changed`, so the shopper never pays a total they did not see. Its last call before the commit is `ReserveRedemptions`, keyed by `order_id`, which holds the deals; Campaign commits the hold on `order.events{placed}` and releases it on `cancelled` or `rejected`. The cart is deleted when its order is placed. A guest cart stays on the device; at login the app merges it in with one `UpdateCart`. Aggregator orders have no cart. Deals at the cart are a draft answer to O-21.

| | |
| --- | --- |
| **Owns** | The cart, the order, the price lines, discount lines, and delivery fee agreed at checkout, the POS ticket, and the checkout saga. |
| **Does not own** | The menu price (Catalog), the deals, coupons, and their budgets (Voucher & Campaign), the charge (Payment), the store (Brand & Store), or the quote and the delivery (Delivery). |
| **How it is called** | `customer-bff` calls `GetCart` and `UpdateCart`, then `PlaceOrder` with a `quote_id` for a delivery order. Order calls Brand & Store, Catalog, Delivery, Voucher & Campaign, and Payment over gRPC while the shopper waits. Capture and void leave as a command after the POS answers. |
| **Kafka** | Publishes `order.events` and `payment.requested` (capture or void). Consumes `order.requested` (aggregator create, replace, cancel, POS status), `payment.events`, and `delivery.events` (delivered, failed, cancelled). The cart has no topic. |

## v3 additions: the OMS, POS vendors, and the payload log

Cart & Order is the Order Management System (OMS) of NEXA. Baseline v3 (2026-10-24) adds three things. The diagrams below do not show them yet (see [`architecture.md` §14](../../docs/architecture.md#14-known-drift)).

- **POS adapter port.** Order does not call one POS directly. It calls a `PosGateway` port, and a registry picks the vendor adapter for the store from `pos_connection` data. BSL is the first adapter. Promise, VIVI, and others come when a brand needs them. POS updates are applied by rank and version, a POS update never rewrites the price lines, and a reconciliation cron finds a POS that disagrees with the priced order. See [`pos-adapters.md`](../../docs/design/pos-adapters.md).
- **Per-brand and per-store settings.** What differs per brand is data: the POS connection, capability flags, aggregator mapping. See [`brand-configuration.md`](../../docs/design/brand-configuration.md).
- **Order payload log.** A parallel MongoDB log of every raw and converted payload, linked by `order_id`. It is written best effort and never blocks checkout. See [`order-payload-log.md`](../../docs/design/order-payload-log.md).

The line above that says the ticket "goes to the store" means the store's POS vendor adapter in v3.

## Diagrams

**Overview** — `cart-order-overview.drawio`

`domain-overview.md` is the plain reading of the HLD and the LLD. Read that instead of the overview page.

The cart, placing an order, the kitchen, and closing the order. A solid line is someone asking. A dashed line is Kafka. Not a replacement for the SHLD. The rulebook is [`overview-guideline.md`](../../docs/overview-guideline.md).

**SHLD** — `cart-order-shld.drawio` *(not yet drawn: this file is not in the repo)*

Own-app checkout from the delivery fee and the payment hold through the kitchen ticket and capture, with aggregator orders joining at the kitchen.

**HLD** — `cart-order-hld.drawio`

One page: the cart, `PlaceOrder`, the authorize-then-capture saga, the POS worker, and the three consumes.

**LLD** — `cart-order-lld.drawio`

| Page | Flow |
| --- | --- |
| 1 | PlaceOrder |
| 2 | `payment.events` consumer |
| 3 | POS dispatch and status |
| 4 | Checkout sweeper cron |
| 5 | Aggregator create |
| 6 | `delivery.events` consumer |
| 7 | Cart: GetCart and UpdateCart |

Page 1 is the reference layout for every other LLD page.
