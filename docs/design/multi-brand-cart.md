# Multi-brand shared cart: one basket, split into brand orders

**Status: proposal, first draft, design phase (P-59 to P-61, 2026-10-28).** Nothing here is final. It answers a new requirement and is not yet refined by business answers or brand limits. Rules that bind the design stay in [`architecture.md`](../architecture.md). Where this note and the rulebook disagree, the rulebook wins until a decision is signed off.

**The requirement** (owner, 2026-10-28): *"Multibrand and use the same cart to shard order."* The word "shard" is read as "share" (see [section 3](#3-vocabulary-and-how-the-requirement-is-read)).

Labels used below: **Proposal** is what this note recommends. **Alternative** is a real choice that was not taken. **Assumption** is a working guess the owner will rewrite. **To confirm** is unchecked and needs a business, finance, or legal answer. **First draft** and **Later** mark scope.

This note states no legal, tax, or finance fact. Who is the merchant of record, how several brands invoice one shopper, and how money is settled between brands are marked **To confirm** with finance and legal (O-57).

---

## 1. What changes, in one page

Today ([P-31](../architecture.md#proposed--the-default-until-signed-off)): one open cart per `(brand_id, customer_id)`, lines only, and `PlaceOrder` makes one order for one brand. A shopper who wants food from two brands has two carts and two checkouts.

**Proposal, in nine sentences.**

1. The shopper has **one basket** that can hold lines from several brands. The shopper sees one cart.
2. The basket belongs to the brand app the shopper is in, the **entry brand**. That keeps `brand_id` on every call and the brand-scoped customer token (P-40) exactly as they are.
3. **Each line carries its own `brand_id`.** The lines of one brand form a **brand group** with its own store, fulfillment (delivery or pickup), and voucher codes.
4. A line of another brand is allowed only when that brand has the cross-brand switch on, the customer has an `enabled` Minor ID membership in it, and the brand has a live store for the shopper.
5. Pricing, vouchers, store resolution, the delivery quote, and loyalty all run **per brand group**, with that brand's id. Nothing is shared between brands except the basket and the shopper.
6. At checkout, `PlaceBasket` splits the basket into **one ordinary order per brand group**, grouped under a parent basket order that holds only the gate state.
7. Each child order has its **own payment** on its brand's gateway account, its own POS ticket, its own Kafka key (`brand_id:order_id`), and its own delivery or pickup. The wallet and loyalty stay per brand (D-11).
8. **No child is placed until every child is authorized** (a gate). If one payment fails or the window ends, the other holds are voided and the basket returns to the cart. After the gate each child runs alone: if one brand's POS rejects, only that child is voided and refunded.
9. The first draft adds no Kafka topic, no service, and no database engine. A postpaid table tab stays single-brand.

**What it changes in the rulebook.** It amends P-31 (the cart key and the brand on a line), extends P-09 (the gate), adds `PlaceBasket`, and touches principle 6 in the way [section 11](#11-conflicts-and-flags) lists, without breaking it. D-11 and P-16 are not changed.

---

## 2. Where it lives

| Piece | Owner | Why |
| --- | --- | --- |
| The basket, its lines and brand groups, `PlaceBasket`, the parent basket order, the child orders | Cart & Order | it already owns the cart and the order, and runs the saga |
| Per-brand prices | Catalog | `PriceLines`, called once per brand group with that brand's id |
| Per-brand deals | Voucher & Campaign | `EvaluateBasket` and `ReserveRedemptions`, per brand group and per child order |
| The store for each brand group | Brand & Store | `ResolveStore`, per brand |
| The cross-brand switch | Brand & Store (feature switch, P-37) | one on or off setting per brand |
| Membership check (is the customer enabled in this brand) | Identity & Profile | it owns the membership (P-40) |
| One payment per child order | Payment & Billing | one provider per brand holds |
| One quote and one delivery per child order | Delivery & Dispatch | unchanged |
| Points | Loyalty & MemberCard | per brand, on each child's `completed` (D-11) |

No new service. The basket is a change inside Cart & Order.

---

## 3. Vocabulary and how the requirement is read

| Term | Meaning |
| --- | --- |
| Entry brand | the brand app the shopper is using. The basket is stored under it |
| Basket | the cross-brand cart: lines from one or more brands |
| Brand group | the lines of one brand in the basket, with that brand's store, fulfillment, and codes |
| Basket order | the parent of the child orders made by one `PlaceBasket`. It only groups and holds the gate state |
| Child order | an ordinary order for one brand group. It is exactly what `PlaceOrder` makes today |

**How "shard" is read (needs a business answer, O-56).** The owner wrote *"use the same cart to shard order"*. This note reads it as **"share"**: one cart that holds items from several brands and is shared across them, with the order then split ("sharded") per brand at placement. Both readings of the word end in the same design, a shared basket and one order per brand.

**Not designed:** a cart shared by **several people** (for example everyone at a table, or a group order where friends add to one basket). That is a different feature with merge, ownership, and payer questions. It is not in this note, and it is recorded as part of O-56.

---

## 4. The basket: ownership and keys

### The choice

| Option | What it is | For | Against | Verdict |
| --- | --- | --- | --- | --- |
| A. Single-brand carts only | the status quo (P-31). One cart per brand | no change | does not meet the requirement. Two carts, two checkouts | Alternative, not taken |
| **B. One basket, brand on every line, split at placement** | one cart row per `(entry brand, customer)`. Each line has its `brand_id` | **one cart and one write path**, one `UpdateCart` with one `version`. The shopper sees one cart. P-31's key shape holds, with `brand_id` read as the entry brand | the cart is cross-brand for the first time, so each line must be checked against its brand. A version conflict can come from any brand's lines. Each read fans out per brand | **Proposal (P-59)** |
| C. A cart group of per-brand child carts | the existing per-brand carts, tied together by a group id | P-31 is untouched. `brand_id` stays on the cart. A version conflict stays inside one brand | the app calls `UpdateCart` once per child to edit. Two write paths (a child cart alone, or the group). More tables. The shopper sees several carts under one cover | Alternative. The fallback if putting `brand_id` on a line is judged too risky |

### Keys and identities

| Thing | Key | Note |
| --- | --- | --- |
| Basket | `(entry_brand_id, customer_id)`, one open basket | the same key shape as P-31. The entry brand is the `x-brand-id` of every basket call |
| Basket line | `(basket_id, line_id)`, with its own `brand_id` | a single-brand shopper sees no difference: every line has the entry brand |
| Brand group | `(basket_id, brand_id)` | holds `store_id`, fulfillment, `quote_id`, coupon codes |
| Basket order (parent) | `basket_order_id` | the idempotency key of `PlaceBasket` is unique on it |
| Child order | `(brand_id, order_id)` | the Kafka key is `brand_id:order_id`, as today |
| Payment | `(brand_id, transaction_id)` | key `brand_id:transaction_id`, as today |

### How `brand_id` stays on every hop

- **Calls from the shopper's app:** `x-brand-id` is the entry brand, from Kong as today. The brand-scoped token (P-40) is checked by Kong against the route, and nothing about that changes. The customer never holds a token for another brand.
- **Calls from Order to another domain for a brand group:** Order sets `x-brand-id` to that group's brand for the downstream call (`PriceLines`, `EvaluateBasket`, `ResolveStore`, `GetQuote`). This is **new**: today a domain's `x-brand-id` is copied from Kong. It is allowed only after Order has checked, for that brand, the cross-brand switch and the `enabled` membership. Flagged in [section 11](#11-conflicts-and-flags).
- **Kafka:** each child order publishes on `order.events` with its own brand in the key and headers. The parent publishes nothing. The child's `placed` payload carries `basket_order_id`, so a consumer that wants the group can find it. The envelope in [`kafka-topics.md`](../kafka-topics.md#envelope) does not change.
- **Tables:** every table has `brand_id`. `basket_line` has the line's brand, and `basket` has the entry brand.

### When a line of another brand is allowed

| Check | Where | If it fails |
| --- | --- | --- |
| The entry brand has `cross_brand_basket` on | Brand & Store switch | `FAILED_PRECONDITION` (`cross_brand_not_enabled`) |
| The line's brand has `cross_brand_basket` on | the same | the same |
| The customer is `enabled` in the line's brand | Identity (`GetMembership`, new, proposed) | `FAILED_PRECONDITION` (`membership_disabled`). The app offers to join the brand |
| The brand is live and has a store for the shopper | Brand & Store `ResolveStore` | `FAILED_PRECONDITION` (`store_not_available`) |
| The brands may share a basket (a named group) | brand setting `basket_group` | **Open (O-59).** First draft: any two brands that both have the switch on |

An unset switch is off (P-37). A guest cart stays on the device (P-31), so a **guest basket is single-brand**: a cross-brand basket needs a signed-in customer, because the membership check needs a customer.

**Where the basket is hosted** is open: a brand app (the proposal, so the entry brand is that brand), or a Minor-level app for all brands. A Minor-level app would need the group tenant `mfg` as the entry brand, the same exception P-23 made for riders, and a token with no brand scope. That would weaken principle 6 and P-40, so it is **not** in the first draft (O-59).

---

## 5. Pricing, vouchers, and store resolution per brand group

`GetCart` and `UpdateCart` still price the cart live and store no price. For a basket they do it per brand group.

```
 UpdateCart / GetCart (basket, version)
   for each brand group, in parallel, with x-brand-id = that brand:
     Catalog     PriceLines(lines)             the price of each line
     Voucher     EvaluateBasket(lines, codes)  the deals of this brand only
   the answer: per group priced lines, discounts, subtotal. Plus a grand total for display only
```

| Topic | Rule |
| --- | --- |
| Prices | per brand. A price never crosses brands. The grand total is the sum for display and is not stored |
| Vouchers and codes | a code belongs to one brand. A code typed on a basket is checked against each group and attached to the group it is valid for. A code valid for no group returns `invalid_for_brand`. **First draft: no voucher or campaign spans brands** (O-60) |
| Store | per brand group. For delivery, Brand & Store picks the store near the shopper's address for each brand. For pickup, the shopper picks a store per brand. Fulfillment may differ per group (one delivery, one pickup) |
| Delivery quote | one `GetQuote` per delivery group. Each child has its own `quote_id` |
| Loyalty and wallet | untouched here. Points are earned per child order. A wallet is spent by the child of its brand (D-11) |
| Latency | the fan-out is parallel, so a basket of N brands costs about one round of calls plus a little, not N rounds. The deadline is passed on and never reset (P-02). The budget is an Assumption (section 9) |
| Version | one `version` on the whole basket, as today. `UpdateCart` replaces the whole basket and checks the version, so a stale write returns `ABORTED` and the app reloads |

---

## 6. Checkout, the saga, and partial failure

Payments, kitchens, and deliveries are per brand, so the checkout is the existing own-app checkout ([`architecture.md` §7](../architecture.md#reference-flow-own-app-checkout)) run once for each brand group, with one gate added.

### Recommended: split into child orders, gate on authorization

```
 0  customer-bff ──gRPC GetCart──▶ Order       one basket, priced per brand group (section 5)
 1  customer-bff ──gRPC PlaceBasket(idempotency_key, basket_version, expected total per group)──▶ Order
 2  Order, per group in parallel: ResolveStore, PriceLines, GetQuote, EvaluateBasket
    a changed total in any group, a closed store, or an expired quote ──▶ FAILED_PRECONDITION naming the group. Nothing is committed
 3  Order, one transaction: the basket order (gate = authorizing) + one child order per group (pending_payment)
    then ReserveRedemptions per child. The basket is locked (no UpdateCart)
 4  Order, per child: CreateTransaction(idempotency_key = basket_order_id:brand_id:attempt) ──▶ Payment ──▶ that brand's gateway account
    the answer is one authorize_url per child (a wallet child holds at once and has none)
 5  the app shows one pay step per child: "Pay brand A", "Pay brand B". The shopper finishes each at its gateway
 ───────────────────────────────────────────────── nobody waits from here ──────────────────────────────
 6  each gateway ──webhook──▶ webhook-adapter ──payment.requested{webhook}──▶ Payment ──▶ payment.events{authorized | failed}
 7  Order marks each child authorized as its event arrives. Nothing is placed yet
 8  GATE: when every child is authorized, Order in one commit marks every child placed, sets the gate to placed,
    deletes the basket, and publishes order.events{placed} for each child (key brand_id:order_id, payload with basket_order_id)
 9  from here each child is an ordinary order: POS ticket, accepted or rejected, capture or void, delivery, completed
```

The gate is what makes "nothing is cooked unless everything is paid" true. It costs the shopper some waiting while all payments finish.

### Partial failure policy

| When | What happens | Why |
| --- | --- | --- |
| Before the gate: a payment fails, the shopper abandons 3DS, or the window ends | **All-or-nothing.** The sweeper (or the failed event) cancels every unplaced child, sends `payment.requested{void}` for each authorized one, releases the voucher holds, and unlocks the basket. The shopper sees one clear message. The shopper may **retry one failed payment** inside the window (a new attempt key) before the window ends | nothing was cooked, so a void is clean. This is the same void path as an abandoned checkout today (P-10) |
| After the gate: one brand's POS rejects, or its kitchen cancels | **Independent.** Only that child is `rejected` and voided or refunded, as today. The other children continue. The shopper is told per child | the other kitchens are already working and cannot be recalled. All-or-nothing after the gate would mean cancelling cooked food |
| After the gate: one brand's delivery fails | Delivery's normal path for that child (O-14). The others continue | each delivery is separate |
| Crash anywhere | resumes from the last committed status. A redelivered record is a no-op | the same as the reference flow |

**Alternative not taken: independent orders from the start** (no gate). Each child is placed as soon as it is authorized. Simpler, and one slow payment never delays the others. But a shopper could pay and cook brand A, then fail on brand B, with half a meal and a half-refunded basket. The gate costs a wait and avoids that. **The policy is a business choice (O-58).**

**Alternative not taken: one combined payment.** One gateway charge for the whole basket, then NEXA allocates it to brands. It needs a group merchant account, a settlement split, and one tax invoice per brand from one payment. It reverses the "one provider per brand" guardrail (O-22) and P-16's one tender per order would need a new reading for the parent. It is a finance and legal decision (O-57). **Later.**

### The parent basket order

It is a grouping row, not a saga. It holds the `basket_order_id`, the idempotency key, the entry brand, the customer, and the gate state (`authorizing`, `placed`, `failed`). Every other status is derived from the children. It publishes no event and has no topic. `GetBasketOrder` reads the children from Order's own tables.

### Idempotency

| Operation | Key |
| --- | --- |
| `PlaceBasket` | `idempotency_key`, unique on the basket order. A repeat returns the same basket order and the same children (the same rule as P-32, which says one pending order per brand and customer: here one pending basket order per entry brand and customer) |
| Each child payment | `basket_order_id:brand_id:attempt`. A retry of one child never touches another |
| The gate commit | deduped on the basket order `version`. A replay is a no-op |

---

## 7. What stays per brand

| Concern | Per brand how | First draft |
| --- | --- | --- |
| Payment provider and account | each child pays on its brand's Omise account (one provider per brand holds) | yes |
| Tender | one tender per child order (P-16 holds). A shopper may pay brand A with its wallet and brand B with a card | yes |
| Wallet | the child's brand wallet. No cross-brand balance (D-11, O-19) | yes |
| Loyalty | points per child, on its `completed` (D-11, O-20) | yes |
| Vouchers and campaigns | per brand. A code or campaign does not span brands | yes. Cross-brand deals are **Later** (O-60) |
| Delivery and fee | one delivery, one quote, one fee per child. No fee allocation is needed. One rider for several stores is **Later** (O-59) | yes |
| Invoice and receipt | Payment's Statement mode issues one per child with that brand's invoice header (brand-configuration: legal and tax). Who the legal seller is for each brand is **To confirm** (O-57) | yes |
| Order tracking | `GetBasketOrder` groups the children. Each child has its own status. WebSocket frames per child carry `basket_order_id` | yes |
| Notification | per child, as today. A combined message is a **Later** polish | yes |
| Refund | per child, as today | yes |
| Legacy brands | a brand still on legacy (P-39) gets its child through the legacy adapter. The gate needs that brand's authorization like any other | yes, to verify |
| **Postpaid table tab** | **always one brand, one store.** `PlaceRound` is its only path, and a basket never makes a `dine_in_postpaid` order. A table shared by several brands (a food court) is a **Later** question (O-59) | rule |
| AI assistant | the AI writes only through `UpdateCart` (P-34), so it may add lines of several brands under the same checks. It cannot place a basket | yes |
| Aggregator orders | no cart, unaffected | n/a |

**First draft:** the basket, the per-brand split, the gate, per-brand payments, per-brand delivery, tracking. **Later:** one combined payment, one rider for several stores or a shared fee, cross-brand deals, a combined notification, a basket shared by several people, and a Minor-level basket host.

---

## 8. Data and contract changes

All names are **proposals**. **Align with the boilerplates when shared.**

### Cart & Order (Postgres)

| Table or field | What |
| --- | --- |
| `cart` (the basket) | keeps `(brand_id = entry brand, customer_id)`, `version`. A single-brand cart is a basket with one group |
| `cart_line` | gains `brand_id` (default: the cart's brand) |
| `cart_group` | `(cart_id, brand_id)`, `store_id`, `fulfillment`, `quote_id`, `coupon_codes`. Written by `UpdateCart` |
| `basket_order` | `basket_order_id`, `entry_brand_id`, `customer_id`, `gate_status`, `idempotency_key` (unique), `window_expires_at`, `version` |
| `order` | gains `basket_order_id` (nullable). Nothing else changes: a child is an ordinary order |
| `processed_event`, outbox | unchanged shape. The `placed` event payload gains `basket_order_id` |

### Settings (one owner each)

| Setting | Owner | Meaning | Default |
| --- | --- | --- | --- |
| `cross_brand_basket` | Brand & Store (feature switch) | the brand lets its lines be in a basket of another brand's app, and lets other brands' lines into its own | off |
| `basket_group` | Brand & Store | named group of brands that may share a basket | unset (O-59) |
| `basket_pay_window` | Cart & Order | how long the gate waits for all payments | an Assumption: 15 minutes (with O-04) |

### gRPC (proposals)

| Domain | Calls |
| --- | --- |
| Cart & Order | `GetCart` and `UpdateCart` (lines carry `brand_id`, the answer is grouped), `PlaceBasket`, `GetBasketOrder`, `RetryBasketPayment`, `CancelBasketOrder` |
| Identity | `GetMembership(customer_id, brand_id)` (a read: is the membership `enabled`) |
| Brand & Store | `GetBrandFeatures(brand_id)` (the switch). May already be covered by the feature-switch read in P-37 |
| Catalog, Voucher, Delivery, Brand & Store | unchanged calls, made with the group's brand in `x-brand-id` |

`PlaceBasket` and `RetryBasketPayment` take an `idempotency_key` (extends P-01).

### REST at the edge (proposals, `customer-bff`)

| Route | What |
| --- | --- |
| `GET /v1/cart`, `PUT /v1/cart` | the basket. The body has groups. A single-brand cart looks the same as today with one group |
| `POST /v1/baskets/place` | `PlaceBasket`, with an `Idempotency-Key` header. Returns the basket order and one `authorize_url` per child |
| `GET /v1/basket-orders/{id}` | the children and their statuses |
| `POST /v1/basket-orders/{id}/payments/{brand_id}/retry` | retry one failed child payment inside the window |
| `POST /v1/basket-orders/{id}/cancel` | cancel before the gate |

### Kafka

**No new topic.** Each child uses `order.events`, `order.requested`, `payment.requested`, and `payment.events` as today. The three-answers rule for a possible `basket.events`: the producer would be Order, the only consumer would be the app (which reads over gRPC and WebSocket), and an existing table covers it. **No topic.** A topic would be justified if analytics or support needs the parent as a fact. The `placed` variant gains `basket_order_id` (BACKWARD compatible).

---

## 9. Scale assumptions (recommended, to be rewritten)

These are **Assumptions** (P-66), not facts.

| Parameter | Assumed value |
| --- | --- |
| Share of orders that come from a multi-brand basket | 5 percent |
| Average brands per basket | 2.2 |
| Payment window | 15 minutes |
| Time to finish one 3DS step | about 1 minute, so a two-brand basket takes about 2 to 3 minutes |

| Derived | Value | Note |
| --- | --- | --- |
| Extra orders | none: 100 baskets of 2.2 brands are about 220 orders, as if they had been bought separately | the order count is the same as separate checkouts |
| Extra downstream calls | about 5 percent more than the same number of single-brand orders | the fan-out is per brand, and it is parallel |
| Gate rows held open at the peak | a few hundred | trivial for Aurora |
| Abandoned baskets | the void path of P-10, not new work | it is the same sweeper |

The figures in [`scale-assumptions.md`](scale-assumptions.md) do not change.

---

## 10. Edge cases

| # | Case | What happens |
| --- | --- | --- |
| 1 | One brand's store is closed at `PlaceBasket` | `FAILED_PRECONDITION` (`store_not_available`) naming the group. Nothing is committed. The app offers to remove that group and retry |
| 2 | A price changed in one group | `FAILED_PRECONDITION` (`price_changed`) naming the group. The app re-reads the basket |
| 3 | The shopper pays brand A and abandons brand B | the window ends, the sweeper voids A's hold, cancels both children, and returns the basket to the cart |
| 4 | Brand B's POS rejects after the gate | only B is voided and refunded. A continues. The shopper sees B as `rejected` |
| 5 | Brand B's gateway is down at step 4 | B's child stays `pending_payment`. A may pay. The window ends if B never comes back, and everything is voided |
| 6 | The customer disables a brand membership after adding its lines | `PlaceBasket` fails for that group (`membership_disabled`). `GetCart` flags the group |
| 7 | The brand has `cross_brand_basket` off | `UpdateCart` refuses its lines (`cross_brand_not_enabled`) |
| 8 | A voucher code is for another brand | it attaches to the right group, or returns `invalid_for_brand` |
| 9 | The shopper edits the basket while paying | the basket is locked while the gate is `authorizing` (`FAILED_PRECONDITION`, `basket_locked`). The shopper may cancel the basket order |
| 10 | Two brands deliver to one address | two deliveries, two quotes, two fees. A combined delivery is Later (O-59) |
| 11 | One group is delivery and one is pickup | allowed. Fulfillment is per group |
| 12 | `PlaceBasket` is sent twice | the same basket order and children are returned |
| 13 | A crash between the last authorization and the gate commit | the next consume of an `authorized` event, or the sweeper, finds all children authorized and commits the gate. The commit is idempotent |
| 14 | A guest tries a cross-brand basket | not allowed. Sign in first (the membership check needs a customer) |
| 15 | Refund of one child after `completed` | the normal refund of that order. The others are untouched |
| 16 | The wallet of brand A is short | `FAILED_PRECONDITION` for A's child, and the app offers a card for A (P-16). B is unaffected |
| 17 | A table tab | never a basket (section 7) |

---

## 11. Conflicts and flags

| Rule or decision | How this design touches it | Handling |
| --- | --- | --- |
| Principle 6: brands are rows, `brand_id` on every call, key, and table | The cart now holds several brands | `brand_id` is on the cart (the entry brand) and on every line, group, and child order. Order sets the downstream `x-brand-id` per group after checking the switch and the membership. **New: a call's brand is not always the Kong header.** Flagged. Not broken |
| P-31: one open cart per `(brand_id, customer_id)`, lines only | A line gains its own brand | **Amended by P-59.** The key shape holds, with `brand_id` read as the entry brand |
| P-32: `PlaceOrder` checks out with `cart_version` and expected total, one pending order per brand and customer | `PlaceBasket` checks out several groups | Each child follows P-32. One pending basket order per entry brand and customer |
| P-09: `placed` after `authorized` | A child waits for its siblings | **Extended by P-60.** `authorized` is still necessary, and the gate adds a second condition for basket children |
| P-16: one tender per order | Several payments for one basket | Each child order has one tender, so P-16 holds per order. The parent has no tender. Only the Later "one combined payment" would need a new reading (O-57) |
| D-11: wallet and loyalty per `(brand_id, customer_id)` | A basket spans brands | Untouched. Each child uses its own brand's wallet and earns its own brand's points |
| P-40: the customer token is for one brand | The shopper adds another brand's lines | The token stays the entry brand's. The other brand is checked by `GetMembership` at Identity. No cross-brand token |
| P-33: shared profile only with consent | A basket does not read another brand's profile | It reads the membership status only, not the profile |
| One provider per brand ([§10](../architecture.md#10-simplicity-guardrails)) | Several payments in one checkout | Holds: each child pays on its own brand's account. A combined payment would reverse it (O-22, O-57) |
| §4: no sync chain longer than two hops on the shopper's path | Order fans out to many calls | Still two hops from the BFF. The fan-out is parallel, not a chain |
| Principle 3: one owner, one write path | The basket is written by `UpdateCart` only, and children by Order only | Holds |
| Kafka key `brand_id:<aggregate id>` | Children keep their own brand key | Holds. The parent publishes nothing |
| P-34: the AI writes only through `UpdateCart` | The AI can add multi-brand lines | Holds, under the same checks |
| Postpaid (P-44) | A tab is not a basket | Written as a rule (section 7) |

---

## 12. Impact on other files

| File | Change | State |
| --- | --- | --- |
| [`architecture.md`](../architecture.md) | §3 (Cart & Order row), §13: P-59 to P-61, O-56 to O-60, §14 rows | Done in this pass |
| [`kafka-topics.md`](../kafka-topics.md) | the `placed` payload note, a "no new topic" row | Done in this pass |
| [Cart & Order description](../../domains/cart-and-order/description.md) | a v-next note | Done in this pass |
| [`brand-configuration.md`](brand-configuration.md) | the `cross_brand_basket` switch | Done in this pass |
| Cart & Order HLD and LLD (page 1 PlaceOrder, page 7 cart) | no basket, group, gate, or `PlaceBasket` | **Diagram not updated.** Row added to [`architecture.md` §14](../architecture.md#14-known-drift) |
| [`diagrams/15-multi-brand-cart.drawio`](../../diagrams/15-multi-brand-cart.drawio) | three pages | Done in this pass |
| Diagrams 04 (checkout), 10 (domain map) | add the basket path | **Not updated** |

---

## 13. Decisions and open questions

New ids continue the register in [`architecture.md` §13](../architecture.md#13-decision-register). The text there is the binding one.

| Id | Decision (proposed) | Section | Cost |
| --- | --- | --- | --- |
| P-59 | **A shared cart across brands: one basket, with a brand on every line.** The shopper has one open basket per `(entry brand, customer)`. P-31 keeps its key, and each line gains its own `brand_id`, with a `store_id` and a fulfillment per brand group. The entry brand is the brand app where the shopper is, so `x-brand-id` on every call and the brand-scoped token (P-40) still hold. A line of another brand needs that brand's cross-brand switch on, an `enabled` Minor ID membership in it (checked at Identity), and a live store for it. Pricing, vouchers, store resolution, the delivery quote, and loyalty run **per brand group**. **Amends P-31.** Alternatives not taken: single-brand carts only (the status quo), and a cart group of per-brand child carts | [`multi-brand-cart.md`](multi-brand-cart.md#4-the-basket-ownership-and-keys) | `UpdateCart` replaces the whole basket, so a version conflict can come from any brand's lines; each cart read fans out to Catalog and Voucher once per brand; the cart is cross-brand for the first time, so a missing brand check on a line would leak across brands (O-59) |
| P-60 | **Checkout splits the basket into per-brand orders, with one payment per brand order.** `PlaceBasket` (new, idempotent, with `basket_version` and the expected total per brand) creates a parent basket order that only groups, and one child order per brand group, through the same steps as `PlaceOrder` (P-32). Each child is an ordinary order: its own brand key on Kafka, its own POS ticket, one tender and one payment on that brand's gateway account (P-16 holds per order, and one provider per brand holds). Nothing is placed until every child is authorized (a gate that extends P-09). If one authorization fails or the window ends, the other holds are voided and the basket returns to the cart. After the gate the children run alone: a POS rejection voids and refunds only that child. The parent has no topic and no state machine of its own | [`multi-brand-cart.md`](multi-brand-cart.md#6-checkout-the-saga-and-partial-failure) | the shopper completes one payment per brand (more 3DS steps); the gate holds good children behind a slow one; one combined payment is a business option (O-57, O-58) |
| P-61 | **Everything else stays per brand, and postpaid stays single-brand.** Vouchers, loyalty, wallet, the delivery quote and fee, the invoice, and tax run on each child order (D-11 unchanged). A voucher or campaign never spans brands in the first draft. Delivery is one delivery per child order (a combined rider is a later option). Order tracking groups the children in `GetBasketOrder` and the existing WebSocket frames, with no new topic. A postpaid table tab is always one brand and one store. Scope: the first draft is the basket, the per-brand split, per-brand payments, and per-brand delivery. Later: one combined payment, one rider for several stores, cross-brand deals, and a basket shared by several people | [`multi-brand-cart.md`](multi-brand-cart.md#7-what-stays-per-brand) | a shopper sees several fees, several receipts, and several deliveries; cross-brand loyalty and vouchers wait for O-19, O-20, and O-60 |
| P-65 | **No new Kafka topic for the four updates of 2026-10-28.** The three-answers rule was applied to each. Postpaid: there is no POS status, so fewer events. Catalog sync: one thin `pos_menu_changed` variant on `catalog.requested`, and the outbound push is Catalog's own outbox worker. The basket: each child uses `order.events`, and the parent has no events. Payment-method sharing: no event. The registry stays at twelve. Candidates, not registered: `catalog.sync.events` (if a second consumer wants sync results) and `basket.events` (if a consumer needs the parent) | [`../kafka-topics.md`](../kafka-topics.md#growth-policy) | a candidate waits for a named consumer; the two candidates may be promoted sooner if analytics or support tools need them |
| P-66 | **The numbers of the 2026-10-28 features are assumptions.** Menu sizes, sync intervals, payload sizes, basket sizes, the gate window, and the send retry window are recommended assumptions for the owner to rewrite, the same status as P-43 and P-52 | [`catalog-sync-and-sot.md`](catalog-sync-and-sot.md#10-scale-assumptions-recommended-to-be-rewritten), [`multi-brand-cart.md`](multi-brand-cart.md#9-scale-assumptions-recommended-to-be-rewritten) | sync schedules and the gate window depend on the answers to O-01, O-04, and O-53 |

| Id | Open question (needs a business answer) | Blocks |
| --- | --- | --- |
| O-56 | Shared cart: confirm the meaning. Proposed reading: one cart that holds items from several brands, split into one order per brand at checkout. Not designed: a cart shared by several people at a table or in a group order | the basket model (P-59) |
| O-57 | Shared cart payment: one combined payment for several brands (a group merchant of record, a settlement split, the legal entities, a tax invoice per brand), or one payment per brand order (the proposal)? To confirm with finance and legal. Reverses the one-provider-per-brand guardrail if combined | `PlaceBasket` payment steps (P-60), O-22 |
| O-58 | Shared cart partial failure: all-or-nothing before the order is placed (the proposal), or independent orders? What the shopper sees, and how fast a refund is shown, when one brand rejects after placing | the gate and the compensation rules (P-60) |
| O-59 | Shared cart scope: which brands may share a basket (all, or named groups such as one site or food court), which app hosts the basket (a brand app, or a Minor-level app under the group tenant `mfg`), and whether delivery from several stores may be combined (one rider, one fee) | the cross-brand switch, the token scope (P-59, P-61) |
| O-60 | Shared cart deals: may a voucher, a campaign, or points span brands in one basket (against D-11, O-19, O-20)? How are the delivery fee and any service fee shown when there are several brands? | Voucher and Loyalty behavior (P-61) |

Related and already open: O-04 (the payment window), O-14 (all providers fail), O-19 and O-20 (cross-brand wallet and points, deferred), O-22 (more than one payment partner), and O-33 (what a disabled membership means).
