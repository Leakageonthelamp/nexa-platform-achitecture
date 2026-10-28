# Delivery & Dispatch

Delivery & Dispatch is the trip and the rider. One Go app covers dispatch and the rider workforce. One port talks to every fleet: our own riders, the shared pool, ZEEK, and Grab Express. Swapping a provider later is a new package behind that port. One ledger records rider earnings. A payout is real money, so it leaves as a command to Payment, which calls TrueMoney.

Dispatch starts when the kitchen accepts, not when the order is placed. A shopper can ask for a quote while they wait. The quote uses straight-line distance, and Google Maps only when the distance is above a threshold. It does not call the fleet. FAAS brands have no kitchen accept, so `partner-bff` starts the delivery on `CreateDelivery`.

Riders use `brand_id = mfg`, because one pool serves every brand. The delivery itself stays on the order's brand.

| | |
| --- | --- |
| **Owns** | The delivery, the quote, the fee, the provider job, the rider, the roster, and the earnings ledger. |
| **Does not own** | The store zone (Brand & Store), the order (Cart & Order), or a real-money payout (Payment). |
| **How it is called** | `customer-bff` calls `Quote`. Order calls `GetQuote` at `PlaceOrder` and stores that fee. Dispatch calls Identity `GetAddress` and does not copy it. `admin-bff` assigns, cancels, redispatches, and approves a rider. Fleet webhooks arrive as `delivery.requested` through `partner-adapter`. |
| **Kafka** | Publishes `delivery.events` and `payment.requested` (payout). Consumes `order.events`, `delivery.requested`, `store.changed`, and `payment.events`. |

## v3 note: legacy

Fleet Management, FAAS, and Driver Management are the legacy side of the cutover in O-18. Baseline v3 allows that cutover per capability and per brand through a legacy bridge behind the same ports. See [`legacy-bridge.md`](../../docs/design/legacy-bridge.md). The LLD below has sixteen pages as drawn.
## v-next (2026-10-25): not used for table service

Postpaid QR table ordering ([`postpaid-table-ordering.md`](../../docs/design/postpaid-table-ordering.md), P-46) does **not** use this domain. "Deliver to table" is table service by store staff, shown from POS and staff signals. There is no quote, fee, rider, or provider job. Because Delivery starts dispatch on `order.events{accepted}` (P-21), the postpaid `accepted` event carries `fulfillment = dine_in` and Delivery must act only on delivery orders. To verify in the LLD page 2 that it filters on fulfillment.

## Diagrams

**Overview** — `delivery-overview.drawio`

`domain-overview.md` is the plain reading of the HLD and the LLD. Read that instead of the overview page.

Quote, dispatch, tracking, and rider pay. A solid line is another domain asking. A dashed line is Kafka. Not a replacement for the SHLD. The rulebook is [`overview-guideline.md`](../../docs/overview-guideline.md).

**SHLD** — `delivery-dispatch-shld.drawio` *(not yet drawn: this file is not in the repo)*

Quote, dispatch, tracking, and rider pay: the kitchen accepts, a rider is sent, the trip is delivered, and the rider is paid.

**HLD** — `delivery-dispatch-hld.drawio`

One page: quote and create, the seven delivery states, the fleet port, and the rider workforce under the same schema.

**LLD** — `delivery-dispatch-lld.drawio`

| Page | Flow |
| --- | --- |
| 1 | Quote and GetQuote |
| 2 | Kitchen accepted → dispatch |
| 3 | Provider update |
| 4 | No-rider sweeper |
| 5 | Scheduled dispatch |
| 6 | Cancel |
| 7 | Ops |
| 8 | FAAS create |
| 9 | Store sync |
| 10 | Rider sync |
| 11 | Roster |
| 12 | Earnings |
| 13 | Payout |
| 14 | Workforce admin |
| 15 | End to end |
| 16 | Payout reconcile |
