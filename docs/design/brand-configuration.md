# Brand configuration and capabilities

**Status: first draft, proposed (P-37).** Nothing here is final. It is not yet refined by business requirements or brand limits. Rules that bind the design stay in [`architecture.md`](../architecture.md).

NEXA is one central platform. Every brand has its own needs, so the platform must handle every difference **by configuration, not by code per brand**. This file says what differs, who owns each setting, how capabilities decide what is allowed, and how a new brand plugs in.

Principle 6 stays: brands are rows. There are no per-brand services, topics or databases. This file adds the model for the rows.

Labels: **Assumption** is a working guess. **To verify** is unchecked.

---

## 1. What can differ per brand

This list comes from the baseline docs and the owner's chat. It is the starting set, not the final one. Brand requirements are not refined yet.

| Axis | Examples | Source |
| --- | --- | --- |
| POS vendor and setup | BSL, Promise, VIVI; routing values per store; promotion handling | [`pos-adapters.md`](pos-adapters.md) |
| Payment account | one Omise account per brand; later maybe several partners | Payment HLD, O-22 |
| Menu and prices | master feed, price book per channel, dayparts | Catalog |
| Ownership | owned or franchised; what a franchisor sees | O-26 |
| Aggregators | Grab, LINE MAN, Shopee Food on or off, per store | `partner-adapter` |
| Fulfillment | pickup, delivery, FAAS | POS capability and Delivery |
| Table ordering | postpaid QR table ordering on or off, tables, QR guard level, open-amount cap, tip and service charge, card hold, split bill | [`postpaid-table-ordering.md`](postpaid-table-ordering.md), P-44 to P-52 |
| Delivery fleet | ordered provider list per store | P-19 |
| Notification | channels, templates, sender settings | Notification (brand channel config) |
| Loyalty | earn rules, tiers, reward prices | Loyalty (D-11: per brand) |
| Wallet | limits, top-up rules | Wallet, O-10 |
| Campaigns | deal rules, budgets | Voucher & Campaign |
| Identity | brand app client, consent wording, whether the brand is enabled for a Minor ID | [`identity-model.md`](identity-model.md) |
| Legal and tax | invoice header, tax details | Payment Statement |
| Store facts | hours, zone, status, group | Brand & Store |
| Legacy | which capabilities still run on a legacy system | [`legacy-bridge.md`](legacy-bridge.md) |

If a brand needs something that is not on this list, add the axis here first, then decide the owner.

---

## 2. Who owns which setting

Each setting has one owning domain (principle 3). There is no central "config service" and no shared config table. Other domains read a setting from its owner, live, and keep no copy (D-07).

| Slice | Owner domain | Key | Written through | Read by |
| --- | --- | --- | --- | --- |
| Brand identity, live flag, feature switches, onboarding state | Brand & Store | `brand_id` | `admin-bff` | every domain that needs a switch, over gRPC |
| Store facts: hours, zone, status, group | Brand & Store | `brand_id:store_id` | `admin-bff` | as today (`ResolveStore`, `ListNearest`) |
| POS connection and capability overrides | Cart & Order | `brand_id:store_id` | `admin-bff` | Cart & Order |
| Aggregator mapping and enablement | Cart & Order | `brand_id:store_id:aggregator` | `admin-bff` | `partner-adapter` through Cart & Order |
| Gateway keys and provider choice | Payment & Billing | `brand_id` | `admin-bff` | Payment |
| Menu, price book, channel prices | Catalog | `brand_id` | `admin-bff` | as today |
| Provider list per store, quote scheme | Delivery & Dispatch | `brand_id:store_id` | `admin-bff` | Delivery |
| Postpaid table ordering switch, tables, QR key version | Brand & Store | `brand_id:store_id`, `table_id` | `admin-bff` | Cart & Order (`ResolveTable`) |
| Postpaid settings: guard level, POS mode, caps, TTLs, service charge, tip, split mode | Cart & Order | `brand_id:store_id` | `admin-bff` | Cart & Order |
| Postpaid card hold and table-bill methods | Payment & Billing | `brand_id` | `admin-bff` | Payment |
| Channel config and templates | Notification | `brand_id` | `admin-bff` | Notification |
| Earn rules, tiers, reward prices | Loyalty & MemberCard | `brand_id` | `admin-bff` | Loyalty |
| Wallet limits | Wallet | `brand_id` | `admin-bff` | Wallet |
| Campaign rules | Voucher & Campaign | `brand_id` | `admin-bff` | Voucher & Campaign |
| Brand membership and consent | Identity & Profile | `customer_id:brand_id` | `customer-bff`, `admin-bff` | Identity |
| Legacy routing per capability | the domain that has the legacy adapter | `brand_id:capability` | `admin-bff` | that domain |

"Brand & Store owns feature switches" is a **proposal**. It does not make Brand & Store the owner of other domains' settings. It owns only the on/off switches that say which capabilities a brand has bought, and the onboarding state. Who owns brand config as a whole, and who approves changes, is open (O-27).

---

## 3. Capabilities and features

Two ideas, kept apart:

| Term | Meaning | Set by | Example |
| --- | --- | --- | --- |
| **Capability** | what a vendor or provider can do | the vendor profile, with a per-store override | the POS supports delivery tickets |
| **Feature** | what the brand has switched on | brand configuration | the brand offers delivery |

A shopper action is allowed when **capability AND feature AND store setup** all say yes. This is the **effective capability**.

```mermaid
flowchart LR
  V["Vendor capability\nPOS supports delivery"] --> E{"AND"}
  F["Brand feature\ndelivery switched on"] --> E
  S["Store setup\nfleet provider listed"] --> E
  E -->|yes| OK["Offer delivery in the app"]
  E -->|no| NO["Hide the option\nPlaceOrder returns FAILED_PRECONDITION"]
```

Rules:

- **Default is off.** A capability or feature that is not set is false. A new brand starts with nothing on.
- **Most specific wins.** Store override, then brand, then vendor profile. Never the other direction.
- **A flag has a behavior for false.** A flag whose false case nobody handles is not added.
- **The app asks, it does not guess.** Whether to show an option comes from the owning domain, not from a hardcoded brand name. Proposed: Cart & Order exposes `GetFulfillmentOptions(brand, store)`. This gRPC method is not drawn yet.
- Capability names for POS are in [`pos-adapters.md`](pos-adapters.md#6-capability-flags). Provider capabilities for payment and fleet follow the same pattern when a second vendor appears.

---

## 4. Onboarding a new brand

A new brand is mostly configuration. The steps, with the owner of each:

```mermaid
stateDiagram-v2
  [*] --> draft
  draft --> configured: all slices written
  configured --> ready: readiness check passes
  ready --> testing: test orders on a test store
  testing --> live: owner approves, live flag on
  live --> hidden: live flag off
  hidden --> live
```

| # | Step | Owner domain | Needs code? |
| --- | --- | --- | --- |
| 1 | Create the brand (`brand_id`, name, owned or franchised, live flag off) | Brand & Store | no |
| 2 | Create stores: address, hours, zone, group | Brand & Store | no |
| 3 | Choose the POS vendor and write a `pos_connection` per store (routing values, credentials in Vault) | Cart & Order | **yes**, only if the vendor has no adapter yet |
| 4 | Load the menu through the master feed or file, then publish | Catalog | no |
| 5 | Set up the payment account and keys | Payment & Billing | **yes**, only for a new provider |
| 6 | Turn on aggregators per store, with their mapping | Cart & Order | **yes**, only for a new aggregator |
| 7 | Set the delivery provider list per store, or leave delivery off | Delivery & Dispatch | no |
| 8 | Set notification channels and templates | Notification | no |
| 9 | Set loyalty rules, wallet limits, first campaigns | Loyalty, Wallet, Voucher & Campaign | no |
| 10 | Enable the brand for Minor ID and set consent wording | Identity & Profile | no |
| 11 | Run the readiness check | admin-bff, reading each owner | no |
| 12 | Place test orders on a test store, through every enabled channel | owner and QA | no |
| 13 | Turn the live flag on | Brand & Store | no |

**Readiness check (proposed).** `admin-bff` asks each owning domain one read-only question, "is this brand ready?", and shows the answers on one page. Examples: every store has a valid `pos_connection`; every enabled fulfillment has a capability; every store has a menu version; a gateway key exists. It is a set of gRPC reads. It adds no topic and no new service. The method name `CheckBrandReadiness` is a placeholder and is not drawn yet.

**When code is needed.** Only for a new kind of external thing: a POS vendor, a payment provider, an aggregator, a message provider, or a fleet provider. Each already sits behind a port, so the code is one adapter package plus (at the edge) one mapper. A new brand on an existing vendor needs no deploy.

---

## 5. Data or code

| Data (a row, changed by an admin) | Code (a deploy) |
| --- | --- |
| which POS vendor a store uses, and its routing values | a new POS adapter and mapper |
| capability overrides, feature switches | a new capability flag and its behavior |
| gateway account per brand | a new payment provider |
| aggregator on or off, SKU mapping | a new aggregator mapper |
| earn rules, tiers, deal parameters | a new type of rule in the deal engine |
| templates, channel settings | a new channel type |
| provider order per store | a new fleet provider |
| which capability runs on a legacy system | a new legacy adapter |

If a request is "make brand X behave differently" and the answer is code, check first whether the difference can be a typed setting that the existing code reads.

---

## 6. How configuration is stored and changed

- **Typed columns for what is queried or checked, JSONB for vendor-specific blobs.** A JSONB blob is validated against a JSON schema for that vendor on write. A bad blob is rejected at write time, not at order time.
- **Versioned.** Every config row has `version`, and every write carries the expected version (rulebook §6). A stale write returns `ABORTED`.
- **Audited.** Every change writes an audit row in the same transaction (rulebook §8). The audit says who, what, and the old and new values with secrets removed.
- **No secrets in rows.** A row holds a Vault path, never the secret.
- **Read live, cache by version.** A reader may cache in Valkey keyed by version, as the menu does. The cache is never the truth (D-04).
- **A change takes effect on the next read.** It does not rewrite an open cart or an order in flight. An order keeps the capabilities it was placed under.
- **No topic per setting.** Brand and store changes already travel on `brand.changed` and `store.changed`. Other settings are read by gRPC. A new topic needs the three answers ([`kafka-topics.md`](../kafka-topics.md#growth-policy)).
- **Platform defaults live in the vendor profiles and in code constants.** We do not use the group tenant `mfg` for defaults. `mfg` is the exception made for riders (P-23). Extending it would weaken principle 6.

---

## 7. Postpaid table ordering switches (proposal)

Added 2026-10-25. Postpaid QR table ordering is a feature a brand switches on, and it follows the same rules as every other one: an unset setting is off, the owner of each setting is one domain, and the effective capability is the AND of the POS vendor flags (`supports_dine_in`, `supports_pay_later_marker`, and the others in [`pos-adapters.md` §14](pos-adapters.md#14-fire-only-table-service-for-postpaid-p-54); amended 2026-10-28, the open-check flags of 2026-10-25 are a later upgrade), the brand feature, and the store setup (registered tables, a POS mode, a payment method).

| Setting | Owner | Default |
| --- | --- | --- |
| `postpaid_table_ordering` (brand and store) | Brand & Store | off |
| `qr_guard`, `postpaid_pos_mode`, `allow_guest`, `max_open_amount_satang`, `max_rounds_per_10min`, `max_lines_per_round`, `session_idle_ttl`, `session_max_ttl`, `service_charge_bps`, `tip_enabled`, `tip_presets`, `split_mode` | Cart & Order | off or the proposed default in the design note |
| `preauth_required`, `preauth_amount`, `table_bill_methods` | Payment & Billing | off, and the brand's checkout methods |

The values and their meaning are in [`postpaid-table-ordering.md` §9](postpaid-table-ordering.md#9-data-and-contract-changes). The readiness check gains: every store with the switch on has at least one active table, a valid `pos_connection` with a `postpaid_pos_mode`, and a payment method for a table bill. `GetFulfillmentOptions` gains the option `dine_in_postpaid`.

---

## 7b. Settings added on 2026-10-28 (proposal)

Four updates add settings. They follow the same rules: an unset setting is off, and each setting has one owning domain. The values and their meaning are in the design notes.

| Setting | Owner | Default | Note |
| --- | --- | --- | --- |
| `postpaid_pos_mode` | Cart & Order (`pos_connection`) | unset, so off. One value in the first draft: `fire_only` | [`postpaid-table-ordering.md` §9](postpaid-table-ordering.md#9-data-and-contract-changes) (replaces the three modes of 2026-10-25) |
| `pos_payment_report` | Cart & Order (`pos_connection`) | `marker` (proposal). Also `none` and `marker_and_report` | what the POS learns about a payment made in NEXA (O-49) |
| `send_retry_window` | Cart & Order | an Assumption: 2 minutes | when a round that could not be sent needs staff (O-50) |
| `catalog_sync_mode` (brand, with an optional store override): `service`, `pos`, or `mixed` with `field_owner.<group>` | Catalog | unset: today's behavior, nothing synced outward | who is the source of truth for menu and catalog (P-56, O-52). A switch needs a dry run and an audit row |
| `inbound_publish` (`review` or `auto`), `inbound_guard`, `poll_interval`, `sync_retry_window`, `pos_menu_connection` | Catalog | `review`, and Assumptions in the note | [`catalog-sync-and-sot.md` §9](catalog-sync-and-sot.md#9-settings-grpc-and-rest-proposals) (O-54, O-55) |
| `cross_brand_basket` | Brand & Store (feature switch) | off | the brand's lines may be in a basket of another brand's app, and other brands' lines may be in its own (P-59) |
| `basket_group` | Brand & Store | unset | which brands may share a basket (O-59) |
| `basket_pay_window` | Cart & Order | an Assumption: 15 minutes | how long the gate waits for all payments (P-60, O-04) |
| `saved_methods_enabled` | Payment & Billing | off | the brand lets customers save a card (P-62) |
| `payment_account_group` | Payment & Billing | a group of one brand | which gateway account group the brand pays through (P-63, O-62) |

The readiness check gains: a brand with `catalog_sync_mode = pos` has a working `PosMenuGateway` connection and a first import that was reviewed and published; a brand with the basket switch on has a live store for each brand it shares with. The payment-method sharing consent is **not** a brand setting. It is the customer's choice in Minor ID ([`payment-methods-sharing.md`](payment-methods-sharing.md#2-where-the-setting-lives)).

---

## 8. Open items

| Id | Question |
| --- | --- |
| O-27 | Who owns brand configuration, who approves a change, and is there a maker-checker step for risky settings (a POS vendor change, a payment key)? |
| O-28 | The real capability matrix for each POS vendor (needs vendor input) |
| O-26 | What a franchisor sees (already open) |
| O-31 | Which capabilities run on a legacy system, per brand ([`legacy-bridge.md`](legacy-bridge.md)) |
| O-37 | Which brands and stores offer postpaid table ordering, and in which formats |
| O-42 | The fire-only capability of each POS vendor (amended 2026-10-28) |
| O-49 to O-51 | Postpaid: what the POS learns about a payment, what "the kitchen has it" means, and counter settlement by staff |
| O-52 to O-55 | Catalog source of truth, vendor menu capability, vendor connection data and payload home, and the inbound publish policy |
| O-56 to O-60 | The shared cart: meaning, payment, partial failure, scope, and deals |
| O-61 to O-63 | Payment-method sharing: PDPA, gateway, and scope |
