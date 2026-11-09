# Sharing payment methods across brands, with Minor ID consent

**Status: proposal, first draft, design phase (P-62 to P-64, 2026-10-28).** Nothing here is final. It answers a new requirement, and the design depends on gateway, PCI, finance, and legal answers that are not yet known. Rules that bind the design stay in [`architecture.md`](../architecture.md). Where this note and the rulebook disagree, the rulebook wins until a decision is signed off.

**The requirement** (owner, 2026-10-28): *"Payment information can choose btw share or not with minor_id."*

Labels used below: **Proposal** is what this note recommends. **Alternative** is a real choice that was not taken. **Assumption** is a working guess. **To confirm** is unchecked and needs the gateway, the PCI assessor, finance, or legal. **First draft** and **Later** mark scope.

This note states no legal, tax, or PCI fact as settled. Thai PDPA wording, PCI scope, and merchant-of-record effects are **To confirm** (O-61, O-62). The facts about the gateway (Omise) come from its public documentation and are cited in [section 4](#4-the-gateway-limit-and-the-options). Nothing is assumed about NEXA's own Omise contract.

**An honest note first.** The existing design has **no saved-card design at all**. [`platform-concept.md`](../platform-concept.md) (a 2029 concept) shows a "saved card" travelling with Minor ID, and the Identity domain description says Identity does **not** own saved cards. Payment & Billing owns the transaction, the gateway keys per brand, the invoice, and the receipt, and no saved method. So this note first has to say where a saved method lives, and then how it may be shared. Both are proposals.

---

## 1. What changes, in one page

**Proposal, in eight sentences.**

1. A **saved payment method** is a card that a customer chose to keep. NEXA stores only a gateway reference and display fields, never a card number or a security code.
2. Payment & Billing **owns** the saved methods, because it is the only domain that talks to the gateway.
3. Whether a customer's saved methods may be used in **other brands** is a **consent** that the customer chooses. It is a new consent purpose, `payment_method_sharing`, owned by **Identity** (Minor ID), apart from the profile consent of P-33.
4. The default is **not shared**. A method saved in a brand works only in that brand. The customer can switch sharing on, and off again at any time.
5. When sharing is on, a method saved in brand A is listed and usable in brand B only if both brands use **the same gateway account**, because a saved card is created inside one gateway account. A brand with its own account cannot use it.
6. Payment reads the consent **live** from Identity when it lists or uses a method that belongs to another brand. Nothing is copied to Payment.
7. The bus carries ids only (`payment_method_id`, `order_id`, `brand_id`), never a card detail. No topic is added.
8. Withdrawing the consent takes effect at once. It deletes nothing. The card stays in its own brand.

**What it changes in the rulebook.** It extends P-33 and P-40, adds saved-method storage to Payment (new), and creates one third-hop call that [section 11](#11-conflicts-and-flags) flags against the two-hop rule. D-11 (wallet and loyalty per brand) and "one provider per brand" are not changed by it, but the second one **limits** it (section 4).

---

## 2. Where the setting lives

Two things are needed: the **customer's choice** (shared or not), and the **saved methods** themselves. They have different owners.

| Piece | Owner | Why |
| --- | --- | --- |
| The choice, with its audit (purpose, time, policy version, channel) | Identity & Profile (Minor ID) | consents are Identity's (P-33). It already holds the PDPA consent for the shared profile |
| The saved methods (gateway reference and display fields) | Payment & Billing | only Payment talks to the gateway and holds its keys |
| Which brands use which gateway account (`payment_account_group`) | Payment & Billing | it already holds the gateway keys per brand |
| Whether a brand membership is `enabled` | Identity | P-40 |
| The audit of every use of a method | Payment & Billing | it is the one that charges |

### Where to put the saved methods (a real choice)

| Option | What it is | For | Against | Verdict |
| --- | --- | --- | --- | --- |
| A. Identity holds the methods | the "saved card travels with Minor ID" picture of the 2029 concept | one place for "my data". Matches the concept | Identity would hold payment data and talk to the gateway or Payment. It changes Identity's "does not own" line. It widens what the login service stores. One more domain in PCI conversations | Alternative, not taken |
| **B. Payment holds the methods, Identity holds only the consent** | the proposal | each domain keeps its role. Payment already is the gateway door. Identity stores no payment data | a cross-brand use needs a live read of the consent from Identity (a third hop on that path, section 11) | **Proposal (P-62)** |
| C. Payment holds the methods and the consent | the consent is a Payment setting | no cross-domain read. Two hops hold | the PDPA consent record would live outside Identity, against P-33 ("Identity owns consent"). A customer would see two places for consents. Withdrawal and deletion would need a second path | Alternative, not taken |

**Who chooses.** The **customer** chooses, in Minor ID, once for all their brands. The brand does not choose for the customer. A brand takes part in sharing only because it uses the same gateway account as another brand (section 4), which is a payment setting and not a customer one. A brand-level kill switch (`saved_methods_enabled`, default off) lets a brand decide to offer saved cards at all. This is a proposal, and the owner may prefer to let a brand veto sharing (O-63).

---

## 3. Vocabulary and how the requirement is read

| Term | Meaning |
| --- | --- |
| Payment method | a saved way to pay: in the first draft a **card** saved through the gateway |
| Owner brand | the brand where the method was first saved |
| Sharing (consent) | the customer allows methods saved in one brand to be listed and used in other brands |
| Account group (`payment_account_group`) | a set of brands that pay through the same gateway account. A brand with its own account is a group of one |
| Gateway customer | the gateway's record that holds a customer's cards inside one gateway account |
| Display fields | card brand, last four digits, expiry month and year, status. Safe to show. **To confirm with the PCI assessor** that this set is allowed |

**How the requirement is read (O-63).** *"Payment information can choose btw share or not with minor_id"* is read as: **the customer can choose whether their saved payment information is shared across brands through their Minor ID, or kept in the brand where it was saved.** In this reading Minor ID holds the **choice**, and Payment holds the card reference. Two other readings exist: the **brand** chooses, or **Minor ID itself stores** the payment information (option A above). The note records them and does not build them.

**Payment information that is covered.** Saved cards. A wallet is **not** a payment method here: it stays per brand and is never shared (D-11). PromptPay QR and e-wallet payments are one-off and have nothing to save. Billing and tax-invoice details are profile data, not payment data, and are a later question (O-63).

---

## 4. The gateway limit and the options

This is the hard part, and it is mostly not NEXA's to decide. What the public Omise documentation says (checked 2026-10-28; to confirm against NEXA's own contract):

| Fact | Source |
| --- | --- |
| The card goes from the customer's browser to Omise using Omise.js (or the mobile SDKs). Omise returns a **single-use token**. NEXA's servers never handle the card number. Sending card data server-side is only for merchants who are PCI DSS certified | [Collecting Cards](https://www.omise.co/collecting-card-information), [Security Best Practices](https://www.omise.co/security-best-practices) |
| A token is voided after one charge or one customer creation. It "is valid for one merchant only" | [Tokens API](https://www.omise.co/tokens-api), [Security Best Practices](https://www.omise.co/security-best-practices) |
| To keep a card, create an Omise **customer** with the token. A customer can hold several cards. Later charges pass the customer id and the card id (or only the customer id for the default card) | [Credit Card Payments](https://www.omise.co/charging-cards) |
| Secret keys do all other operations (charge, refund, customer data). The public key only tokenizes | [Security Best Practices](https://www.omise.co/security-best-practices) |

**What this means (an inference, to confirm with the gateway).** Omise customers and cards live inside one Omise account, and they are used with that account's secret key. NEXA's design holds **one Omise account per brand** (Payment description). So a card saved by brand A in A's account is **not usable** with brand B's account. I found no public documentation of a way to share a saved card across Omise accounts. That does not prove none exists. It is the first question for the gateway (O-62).

### Options

| Option | What it is | For | Against | Verdict |
| --- | --- | --- | --- | --- |
| **A. Account groups: brands that share an account share methods** | `payment_account_group` links brands that use the same Omise account. Sharing works inside a group | uses what the gateway documents. NEXA still holds no card data. The consent still applies | a group account changes **who is the merchant of record, how money is settled, and how fees and reports are split per brand**. That is a finance and legal decision. The "one provider per brand" guardrail then needs a reading: still one provider (Omise), but not one account per brand (O-22 is related) | **Proposal for the first draft: build the model, and keep every brand in its own group of one until finance decides.** Until then, nothing is shared at the gateway |
| B. Gateway-side sharing across accounts | the gateway lets a saved card be used across the merchant accounts of one group | keeps one account per brand and still shares | **not found in public documentation. Unknown.** May depend on the contract | **To confirm with the gateway (O-62).** Not assumed |
| C. A NEXA vault of card data | NEXA stores the card (or a network token) and charges each brand's account | full control | brings NEXA into PCI DSS scope (the gateway documents that server-side card handling needs PCI DSS certification). A large cost and risk for one convenience feature | Alternative, **not recommended** |
| D. No gateway sharing: only a hint | brand B shows "you used a card ending 4242 in another brand" (only with consent) and the customer types the card again. B may then save it in its own account | no account change, no PCI change | still shares payment information (the last four digits), so it still needs the consent. The shopper types the card again, so it is a poor experience | A fallback if A and B fail. **First draft: not built** |
| E. Apple Pay, Google Pay, and similar | the wallet app holds the card and supplies it per brand | no NEXA storage | not a NEXA feature, and not a sharing of NEXA's information. **To confirm** per gateway | Out of scope, noted |

**So the honest answer today:** with "one Omise account per brand", sharing a saved card between **different** brand accounts is **not possible with documented gateway features**. The first draft builds the model (the consent, the saved-method store, the group table, the audit), so that the day finance chooses a group account or the gateway confirms option B, no redesign is needed. Until then every brand is its own group, and the sharing switch has nothing to share across. **Say this plainly to the owner.**

---

## 5. What is shared and what is not

| Item | Shared when consent is on | Notes |
| --- | --- | --- |
| Saved card (gateway reference) | yes, **inside one account group** | the use is a charge by the group account's secret key |
| Display fields (brand, last four, expiry) | yes, to brands in the group | shown in the payment picker |
| Card number, security code | **never stored, never shared** | not in NEXA at all |
| Default method | per brand. One brand's default does not change another's | first draft |
| Wallet balance | **no** (D-11) | |
| Loyalty points | **no** (D-11) | |
| Order history | **no**. Shared profile is a different consent (P-33) | |
| Billing and tax-invoice details | not in this note (O-63) | |
| Saved methods of a brand the customer **disabled** (P-40) | no. Not listed, not usable | |

---

## 6. Withdrawal, audit, and the bus

| Topic | Rule |
| --- | --- |
| Withdraw the consent | the customer switches it off in the app. Identity records the withdrawal (time, policy version, channel). From the next call, Payment sees "not shared". Listing across brands and use across brands stop **at once**, because Payment reads the consent live |
| What withdrawal does **not** do | it deletes nothing. A method saved in brand A stays in brand A. A payment already authorized before the withdrawal completes. An open `pending_payment` order that uses a shared method is not charged: the shopper picks another method |
| Remove one method | the customer removes it. Payment deletes the gateway card and marks the row `removed`. It disappears from every brand |
| Delete the customer (Minor ID) | Identity's delete calls Payment `EraseCustomerMethods(customer_id)`, which deletes the gateway customers and cards and the saved-method rows, keeping the audit rows as the law needs (O-61). How a delete works across brands is O-33 |
| Brand membership disabled (P-40) | that brand can neither list nor use shared methods for that customer. The methods stay in their own brands |
| Audit | every add, remove, and cross-brand use writes a row in `payment_method_audit` in the **same transaction** (actor, customer, method, brand where it was used, action, `correlation_id`). The consent change itself is in Identity's consent record. Retention is O-61 (with O-07) |
| The bus | **ids only**: `payment_method_id`, `order_id`, `brand_id`, `transaction_id`. Never a card detail, never a last-four value. The `payment.events` payloads do not change. **No new topic** (principle 8, P-65) |
| Logs | no card field in a log. A gateway response is kept without card fields. The order payload log (P-38) must not hold card data. **To confirm** how the current log masks payment fields |

---

## 7. Flows

All names are **proposals**. A solid arrow is gRPC. The card never passes through a NEXA service.

### 7.1 First payment, and save the card (brand A)

```
 1  customer-bff (A) ── shows the card form (Omise.js, A's public key) in the customer's browser
 2  browser ───────── card ───────▶ Omise            Omise returns a single-use token. NEXA sees only the token
 3  customer-bff ──gRPC PlaceOrder(…, payment = new card, save = true)──▶ Order            (the order flow is unchanged)
 4  Order ─────────gRPC CreateTransaction(idempotency_key, token, save = true)──▶ Payment
 5  Payment ───────▶ Omise (A's account)   create the Omise customer with the token (or add the card to the customer), then charge customer + card id
 6  Payment: in one transaction, a payment_method row (owner brand A, account group of A, gateway refs, display fields) + an audit row
 7  Payment ──▶ Order   authorize_url when 3-D Secure is needed
```

The save is an explicit tick the shopper makes ("save this card"). The consent for sharing is a separate switch (7.3). Whether a saved card still needs 3-D Secure for each charge is **To confirm** with the gateway.

### 7.2 Reuse the saved method in another brand (brand B)

```
 1  app (B) → customer-bff (B) ──gRPC ListPaymentMethods(customer_id)──▶ Payment            hop 1
 2  Payment: methods of (B, customer) + methods of other brands in B's account group
    for any method whose owner brand is not B: Payment ──gRPC GetConsent(customer_id, payment_method_sharing)──▶ Identity   hop 2
    consent granted and B's membership enabled → list them. Otherwise list only B's own
 3  the shopper picks one. customer-bff ──gRPC PlaceOrder(…, payment_method_id)──▶ Order
 4  Order ──gRPC CreateTransaction(idempotency_key, payment_method_id)──▶ Payment             hop 2
 5  Payment: for a method of another brand, GetConsent again (live), then the charge on the account group's gateway account, then an audit row.
    The consent read here is a third hop on the shopper's path (section 11)
 6  the rest is the normal checkout
```

If Identity does not answer at step 5, the shared method is **not used** and the shopper is asked for another method. The order is not affected.

### 7.3 Choose sharing, and withdraw

```
 1  app → customer-bff ──gRPC SetConsent(customer_id, payment_method_sharing, granted | withdrawn, channel, policy_version)──▶ Identity
 2  Identity: one transaction: consent record + audit row. Nothing is published
 3  the next list or charge in any brand sees the new state (Payment reads it live)
 4  on withdrawal: the app can offer "remove saved cards from other brands" (Payment RemovePaymentMethod). Nothing is removed on its own
```

### Where the consent is read (a real choice)

| Option | What it is | For | Against | Verdict |
| --- | --- | --- | --- | --- |
| **A. Payment reads Identity live** | `GetConsent` on each cross-brand list and charge | always current. No copy (D-07). Withdrawal takes effect at once | a third hop on the cross-brand charge path. Identity down blocks sharing. Adds a call per use | **Proposal (P-62).** Only the cross-brand path pays the cost |
| B. Payment keeps a consent copy, refreshed by an event | `customer.changed` (a candidate topic today) | no live call | a copy of another domain's data (D-07). A topic is registered. A stale copy can charge after a withdrawal | Alternative, not taken |
| C. Order reads the consent, then tells Payment | Order calls Identity (a second hop, a sibling of Payment) and passes the result | keeps two hops | Payment would trust a claim from Order, and the rule "the owner guards its own data" weakens. Two places to get it wrong | Alternative, not taken |
| D. The consent decision rides in a signed value | Identity signs a short-lived grant that the app passes along | no extra call at charge time | a new token type to build and revoke. A withdrawal waits for expiry | Alternative, not taken |

---

## 8. Data and contract changes

All names are **proposals**. **Align with the boilerplates when shared.**

### Payment & Billing (Postgres)

| Table | Key fields |
| --- | --- |
| `payment_account_group` | `group_id`, `gateway`, `vault_ref` (the keys stay in Vault) |
| `brand_payment_account` | `brand_id`, `group_id` (default: a group of one) |
| `gateway_customer` | `(group_id, customer_id)`, `gateway_customer_ref` |
| `payment_method` | `payment_method_id`, `owner_brand_id`, `customer_id`, `group_id`, `gateway_card_ref`, `card_brand`, `last4`, `expiry_month`, `expiry_year`, `status` (`active`, `expired`, `removed`), `created_at`. Unique on `(group_id, customer_id, gateway_card_ref)`. **No card number, no cardholder name** in the first draft |
| `payment_method_audit` | `id`, `at`, `actor`, `customer_id`, `payment_method_id`, `used_in_brand_id`, `action` (`add`, `remove`, `use`, `list_cross_brand`), `correlation_id` |
| `transaction` | gains `payment_method_id` (nullable) |

### Identity & Profile (Postgres)

| Table | Key fields |
| --- | --- |
| `consent_record` | `(customer_id, purpose)`, `status` (`granted`, `withdrawn`), `at`, `policy_version`, `channel`. `purpose = payment_method_sharing` is new. `profile_sharing` (P-33) stays separate |

### Settings (one owner each)

| Setting | Owner | Meaning | Default |
| --- | --- | --- | --- |
| `saved_methods_enabled` | Payment | the brand lets customers save a card | off |
| `payment_account_group` | Payment | which gateway account group the brand pays through | a group of one |

### gRPC (proposals)

| Domain | Calls |
| --- | --- |
| Payment | `SavePaymentMethod` (from a token), `ListPaymentMethods`, `RemovePaymentMethod`, `EraseCustomerMethods`. `CreateTransaction` gains `payment_method_id` and `save` |
| Identity | `SetConsent`, `GetConsent` (the purpose is a parameter) |

All mutating calls take an `idempotency_key` (P-01).

### REST at the edge (proposals, `customer-bff`)

| Route | What |
| --- | --- |
| `GET /v1/payment-methods` | the methods usable in this brand (own, plus shared ones in the group when consent is on) |
| `POST /v1/payment-methods` | save a card from a token |
| `DELETE /v1/payment-methods/{id}` | remove one |
| `GET /v1/me/consents`, `PUT /v1/me/consents/payment_method_sharing` | read and set the choice |

### Kafka

**No new topic and no new variant.** The audit stays in Postgres. A consent change publishes nothing (Identity publishes nothing by design). `customer.changed` remains a candidate and is not promoted by this feature, because Payment reads the consent live.

---

## 9. Scale assumptions (recommended, to be rewritten)

These are **Assumptions** (P-66), not facts.

| Parameter | Assumed value |
| --- | --- |
| Members who save a card | 30 percent |
| Cards per saving member | 1.3 |
| Members who switch sharing on | 20 percent of those who saved a card |
| Share of charges that use a card saved in another brand | 2 percent of card charges |

| Derived | Value | Note |
| --- | --- | --- |
| Saved-method rows | about 0.4 per member (0.3 times 1.3) | for one million members, about 400 thousand rows. Tiny for Aurora |
| Extra `GetConsent` calls | at most one per cross-brand list and one per cross-brand charge, so about 2 percent of card charges plus the list calls | a small read load on Identity |
| Audit rows | one per use | partition by month, purge by retention (O-61) |

The figures in [`scale-assumptions.md`](scale-assumptions.md) do not change.

---

## 10. Edge cases

| # | Case | What happens |
| --- | --- | --- |
| 1 | The customer withdraws while a shared-card order is `pending_payment` | the next use is refused. The shopper picks another method. An already authorized payment completes |
| 2 | Identity is down at a cross-brand charge | the shared method is refused for that attempt and the app offers another method |
| 3 | The brand has its own gateway account and the card was saved in another account | not listed. The shopper enters a card for this brand |
| 4 | The card expired | `status = expired`, not offered. The gateway may also decline |
| 5 | The gateway declines a saved card | a normal `payment.events{failed}`. The method stays unless the gateway says it is invalid |
| 6 | Two brands save the same card in the same account | unique on `(group_id, customer_id, gateway_card_ref)`, so one row, with the first brand as owner |
| 7 | The owner brand is later disabled for the customer | the method stays in the group. It is listed in other brands only if the customer still has sharing on and the **using** brand is enabled. Whether it should follow the owner brand is O-63 |
| 8 | The customer is deleted | Payment erases the gateway customers and cards. Audit rows stay as the law needs (O-61, O-33) |
| 9 | A guest | a guest has no Minor ID, so nothing is saved or shared |
| 10 | A postpaid table bill | pays like any order. A saved card may be used if the customer is signed in. "Card on file, charge later" stays a Later option of the postpaid note |
| 11 | Two devices set the consent at once | the last write wins, each with its own audit row |
| 12 | A brand turns off `saved_methods_enabled` | its own saved methods are not listed in that brand. They are not deleted. Whether to delete them is O-63 |

---

## 11. Conflicts and flags

| Rule or decision | How this design touches it | Handling |
| --- | --- | --- |
| §4: no sync chain longer than two hops on the shopper's path | A cross-brand charge: BFF, Order, Payment, then Identity | **A third hop, on the cross-brand path only.** Options B, C, and D (section 7) avoid it and each costs something. Proposal: accept the exception, written as an explicit one. The listing path is two hops (BFF, Payment, Identity). **Flagged for the owner** |
| D-07: no copies of another domain's data | Payment needs the consent | it reads live and keeps no copy |
| One provider per brand ([§10](../architecture.md#10-simplicity-guardrails)), one Omise account per brand | Sharing a card needs one gateway account | A group of brands in one account **reverses the "one account per brand" half**. The guardrail is stated as "one provider per brand", and Omise stays the provider. Built as `payment_account_group`, with every brand alone until finance decides (O-22, O-62). **Flagged** |
| P-33: consent for a shared profile is Identity's, opt-in, withdrawable | A second consent purpose | The same owner and the same shape, and a **separate** record, so one cannot be bundled into the other without legal advice (O-61) |
| P-40: the customer token is for one brand, and only for an enabled membership | A cross-brand use needs the other brand's membership | The check is `enabled` in the **using** brand (the token), and the consent is read from Identity. No cross-brand token |
| Principle 8: no personal data on the bus | Card data is the most sensitive | Ids only. No topic. No variant |
| D-11: wallet and loyalty per brand | Payment information is shared, wallet is not | A wallet is not a payment method here. D-11 is untouched |
| Identity description: "does not own saved cards" | The 2029 concept shows the card with Minor ID | **Consistent with the proposal:** Identity owns the consent only, and Payment owns the cards. The concept's picture is a user-facing view and is not a data-ownership statement. **Flagged** as a mismatch of wording |
| PCI | NEXA stores a gateway reference and display fields | The design is built so NEXA never handles a card number. **To confirm** with the PCI assessor that the display fields are allowed, and that no other component (logs, the order payload log) holds card data |
| Payment description: "owns the transaction, the keys, the invoice, the receipt" | Payment gains saved methods | An added responsibility. The description gets a v-next note |

---

## 12. Impact on other files

| File | Change | State |
| --- | --- | --- |
| [`architecture.md`](../architecture.md) | §3 (Payment and Identity rows), §13: P-62 to P-64, O-61 to O-63, §14 rows | Done in this pass |
| [`identity-model.md`](identity-model.md) | the new consent purpose, beside P-33 | Done in this pass |
| [`brand-configuration.md`](brand-configuration.md) | `saved_methods_enabled`, `payment_account_group` | Done in this pass |
| [Payment & Billing description](../../domains/payment-and-billing/description.md) and [Identity description](../../domains/identity-and-customer/description.md) | a v-next note | Done in this pass |
| Payment and Identity HLD and LLD | no saved method, no consent call | **Diagram not updated.** Row in [`architecture.md` §14](../architecture.md#14-known-drift) |
| [`diagrams/16-payment-methods-sharing.drawio`](../../diagrams/16-payment-methods-sharing.drawio) | three pages | Done in this pass |

---

## 13. Decisions and open questions

New ids continue the register in [`architecture.md` §13](../architecture.md#13-decision-register). The text there is the binding one.

| Id | Decision (proposed) | Section | Cost |
| --- | --- | --- | --- |
| P-62 | **Sharing saved payment methods is a Minor ID consent, owned by Identity, default off.** Whether saved payment methods are shared across brands is a consent purpose, `payment_method_sharing`. Identity records it beside the P-33 profile consent but apart from it, with the purpose, time, policy version, and channel. The default is not shared. The customer opts in and can withdraw at any time. Payment owns the saved methods and reads the consent live from Identity when it lists or uses a method that belongs to another brand. Wording and bundling are to confirm with legal (Thai PDPA). **Extends P-33 and P-40** | [`payment-methods-sharing.md`](payment-methods-sharing.md#2-where-the-setting-lives) | a cross-brand charge adds a live Identity call, a third hop on that path only (flagged against the two-hop rule of §4); a lost Identity call blocks the shared method, and the customer pays with another one (O-61) |
| P-63 | **What is shared: tokenized method references only, and only inside one gateway account.** Payment stores a saved method as a gateway reference plus display fields (card brand, last four digits, expiry, status). NEXA never stores or sees a card number or a security code: the card goes from the customer's browser to the gateway, which returns a single-use token. Other domains see only a `payment_method_id` and the display fields. A saved card is created in one gateway account, so it works only for brands that use that same account (a `payment_account_group`). A brand with its own account cannot use it, and the customer enters the card again. The guardrail "one provider per brand" may therefore make sharing impossible for some brands. Options (a shared group account, gateway-side token sharing) need finance, legal, and gateway answers | [`payment-methods-sharing.md`](payment-methods-sharing.md#4-the-gateway-limit-and-the-options) | sharing works only inside an account group, and building a group account changes who is the merchant of record (O-62); Payment gains saved-method storage, which the docs did not have before |
| P-64 | **Withdrawal, audit, and the bus for shared payment methods.** Withdrawing consent stops cross-brand listing and use at once and deletes nothing: a method stays in its own brand. Deleting the customer deletes the gateway customers and cards. Every add, remove, and cross-brand use writes an audit row in the same transaction. The bus carries ids only (`payment_method_id`, `order_id`, `brand_id`) and never a card detail, and no topic is added. A brand that is disabled for the customer in Minor ID (P-40) can neither list nor use shared methods. Wallet and loyalty stay per brand (D-11), and a wallet is not a payment method here | [`payment-methods-sharing.md`](payment-methods-sharing.md#6-withdrawal-audit-and-the-bus) | withdrawal does not delete the card in its own brand; the audit table grows with every use (retention is O-61) |
| P-65 | **No new Kafka topic for the four updates of 2026-10-28.** The three-answers rule was applied to each. Postpaid: there is no POS status, so fewer events. Catalog sync: one thin `pos_menu_changed` variant on `catalog.requested`, and the outbound push is Catalog's own outbox worker. The basket: each child uses `order.events`, and the parent has no events. Payment-method sharing: no event. The registry stays at twelve. Candidates, not registered: `catalog.sync.events` (if a second consumer wants sync results) and `basket.events` (if a consumer needs the parent) | [`../kafka-topics.md`](../kafka-topics.md#growth-policy) | a candidate waits for a named consumer; the two candidates may be promoted sooner if analytics or support tools need them |
| P-66 | **The numbers of the 2026-10-28 features are assumptions.** Menu sizes, sync intervals, payload sizes, basket sizes, the gate window, and the send retry window are recommended assumptions for the owner to rewrite, the same status as P-43 and P-52 | [`catalog-sync-and-sot.md`](catalog-sync-and-sot.md#10-scale-assumptions-recommended-to-be-rewritten), [`multi-brand-cart.md`](multi-brand-cart.md#9-scale-assumptions-recommended-to-be-rewritten) | sync schedules and the gate window depend on the answers to O-01, O-04, and O-53 |

| Id | Open question (needs a business answer) | Blocks |
| --- | --- | --- |
| O-61 | Payment-method sharing, Thai PDPA: the consent wording, whether it may be asked together with the profile consent (P-33), the default, how long consent and audit rows are kept, and how a delete works. To confirm with legal | the consent record (P-62, P-64), with O-07 and O-33 |
| O-62 | Payment-method sharing, gateway: can a saved card be used across the MFG merchant accounts of different brands, or does it need one shared account, a group account, or gateway-side token sharing? What changes in PCI scope, fees, and merchant of record? Which brands share an account? To confirm with the gateway and the PCI assessor. Extends O-22 | the account groups (P-63) |
| O-63 | Payment-method sharing, scope and reading: the requirement says payment information may be shared or not "with minor_id". Proposed reading: the customer chooses whether saved methods are usable across brands, with Minor ID holding the choice and not the card. Is that right, or should the brand choose, or should Minor ID itself hold the payment data? Also: saved cards only, or also a default method, PromptPay or e-wallet hints, and billing or tax-invoice details? What happens to saved methods when a brand membership is disabled (with O-33)? | the method model (P-63) |

Related and already open: O-07 (retention under PDPA), O-22 (more than one payment partner), and O-33 (Minor ID defaults and delete).
