# NEXA — architecture baseline

**Baseline v3 · 2026-10-24, with an addendum on 2026-10-25** (postpaid QR table ordering: P-44 to P-52, O-37 to O-48). This is the rulebook for designing and building any domain on NEXA (next generation experience architecture), the Minor Food platform that was called "MFG ePlatform" until v2. Read it before drawing a high-level design (HLD), a low-level design (LLD), or writing the first line of a service.

**Status: first draft, design phase.** It is built from best practice and is not yet refined by business requirements or brand limits. Nothing in it is final, and there is plenty of room to improve. Where a section is a recommendation or an assumption, it says so. Baseline v2 (2026-10-05) is superseded by this file; v2 content is kept, and every change is listed in [`CHANGELOG.md`](CHANGELOG.md).

**This file wins over everything else in this repo:** the diagrams, the presenter scripts, the domain descriptions, and the 2029 concept.

- **Accepted** rules and decisions are binding for HLD, LLD, and code.
- **Proposed** decisions ([§13](#13-decision-register)) are the defaults development starts with. They stay in force until they are signed off or changed here.
- **Open** decisions need a business answer. Each one names the work it blocks.

If a diagram or the code breaks a rule here, either it changes, or this file changes first with the reason written down in [§13](#13-decision-register).

- **System overview:** [`domains/platform-overview/mfg-eplatform-hld.drawio`](../domains/platform-overview/mfg-eplatform-hld.drawio) (the title inside the picture still says MFG ePlatform) is the master map of channels, edge, domains, the event backbone, and data. Domain HLDs zoom into one box on that map. They do not redraw it.
- **Management view (SHLD):** not yet drawn. Earlier versions of this file pointed at `SHLD-guideline.md` and `mfg-eplatform-shld.drawio`. Neither file is in this repo, so the links were removed (see [§14](#14-known-drift)). The overview rules are in [`overview-guideline.md`](overview-guideline.md).
- **Design documents (v3):** [`design/tech-stack.md`](design/tech-stack.md), [`design/pos-adapters.md`](design/pos-adapters.md), [`design/brand-configuration.md`](design/brand-configuration.md), [`design/order-payload-log.md`](design/order-payload-log.md), [`design/legacy-bridge.md`](design/legacy-bridge.md), [`design/scale-assumptions.md`](design/scale-assumptions.md), [`design/identity-model.md`](design/identity-model.md), and, added 2026-10-25, [`design/postpaid-table-ordering.md`](design/postpaid-table-ordering.md). They explain and extend this file. If one disagrees with this file, this file wins.
- **Target concept (2029):** [`platform-concept.md`](platform-concept.md) is where the platform is heading: one Minor ID, wallet, and points balance across brands, AI ordering, and smart payment routing. It is direction, not a rule. Where it disagrees with this file, this file wins until an Open decision ([O-19 to O-26](#open--needs-a-business-answer)) is answered. The cross-brand wallet and points (O-19, O-20) are a deferred, later option: D-11 was confirmed on 2026-10-24.
- **Kafka topics:** [`kafka-topics.md`](kafka-topics.md) is the only list of topics. A topic that is not in that file does not exist.
- **Reference HLD:** [`domains/catalog-and-menu/catalog-menu-hld.drawio`](../domains/catalog-and-menu/catalog-menu-hld.drawio) is the layout every other HLD copies. [`domains/wallet/wallet-hld.drawio`](../domains/wallet/wallet-hld.drawio) is the reference for the relation lines ([§11](#required-lines-on-every-hld)).
- **Baseline files** are the ones without a suffix. The old `-v2.drawio` drafts, including the overview, are in [`_archive/2026-10-05-v2-drafts/`](../_archive/2026-10-05-v2-drafts/).
- **Diagrams lag the text.** The v3 text is ahead of some diagrams. [§14](#14-known-drift) lists which ones, and a domain does not start coding until its rows are closed.

---

## 1. What we are building

A multi-brand food platform: one shared stack, with `brand_id` on every hop. TPC, SW, BC, and the other brands are rows in that stack, not separate deployments. The core is event-driven on Confluent Kafka, and the shopper's path stays synchronous.

**One central platform, many brands.** Each brand can have its own requirements, so the platform must allow every difference **by configuration, not by code per brand** (P-37). Brands are still rows (principle 6). What differs per brand, who owns each setting, and how a new brand plugs in are in [`design/brand-configuration.md`](design/brand-configuration.md). One layer cannot be configured away: the POS is vendor software, and each brand may use a different vendor. OMS (the Cart & Order domain) therefore talks to the POS through a multi-vendor adapter port (P-36, [`design/pos-adapters.md`](design/pos-adapters.md)).

**Tech stack in one line.** Confluent Kafka for events. Bun and Elysia v2 at the edge, REST only. Go with a hexagonal structure in the core. Aurora PostgreSQL as the system of record, plus a MongoDB parallel log of order payloads (P-38). Infrastructure is fixed and run by the DevOps team on AWS (Cloudflare, Kong, EKS, Aurora, Valkey, S3, Vault, Confluent Cloud, CloudWatch and OpenTelemetry). Details, and what is verified against what is still to verify, are in [`design/tech-stack.md`](design/tech-stack.md).

**Some parts are not rebuilt.** Some domains reuse legacy code for some brands. A legacy bridge keeps the new contracts clean while that lasts ([`design/legacy-bridge.md`](design/legacy-bridge.md), P-39).

```
 Channels             Edge                 BFFs · adapters (Bun/Elysia)   Domains (Go)               Backbone
┌──────────────┐    ┌──────────────┐     ┌──────────────────┐          ┌────────────────────┐      ┌──────────────┐
│ Customer app │    │ Cloudflare   │     │ customer-bff     │          │ Cart & Order       │─pub─▶│ Confluent    │
│ Guest        │───▶│ WAF · TLS    │────▶│ guest-bff        │──gRPC───▶│ Catalog · Payment  │◀─sub─│ Kafka +      │
│ Admin · CSC  │    │      │       │     │ admin-bff        │          │ Brand & Store · …  │      │ Schema Reg.  │
│ Partner API  │    │      ▼       │     │ partner-bff      │          └─────────┬──────────┘      └──────▲───────┘
├──────────────┤    │ Kong (PEP)   │     ├──────────────────┤                    │ commit                 │
│ Aggregators  │───▶│ JWT routes   │────▶│ partner-adapter  │───── command ──────┼────────────────────────┘
│ POS · PSP    │    │ signed hooks │     │ webhook-adapter  │                    ▼
│ SES·SMS·LINE │    └──────────────┘     └──────────────────┘    Aurora PostgreSQL · Valkey · S3 · Vault
└──────────────┘
```

**Where it is heading.** The [2029 concept](platform-concept.md) groups the platform into 8 shared building blocks: Customer ID & profile, Membership & CRM, Orders & menu, Campaign & coupon, Payment & wallet, Data platform, AI operating brain, and Back office. Most map onto the domains in [§3](#3-components). The AI operating brain and the real-time part of the Data platform have no domain yet, and the cross-brand wallet and points conflict with D-11. [`platform-concept.md` §7](platform-concept.md#7-gaps-against-the-current-baseline) has the full mapping. New designs should not close off that direction, but they build to this file.

---

## 2. Principles

Use these in order. When two of them conflict, the earlier one wins.

1. **Simplest thing that works.** Before adding a service, a topic, a cache, or a cron, check whether an existing one already covers it. Something nobody consumes is not built.
2. **Sync when someone is waiting.** If a person, a partner, or a gateway callback is waiting on the answer, the call is gRPC. Kafka is for work nobody is waiting on.
3. **One owner, one write path.** Each piece of state has one domain that writes it, through one door. Admin writes go through `admin-bff` only. Shoppers only read.
4. **Commit, then the fact.** State and the outbox row are written in the same Postgres transaction. A fact leaves only after that commit.
5. **Every consumer is idempotent.** A redelivery is a no-op. Facts are deduplicated on `version`, and commands on `event_id` ([§5](#consumer-apply-then-ack)).
6. **Brands are rows.** `brand_id` is on every gRPC call, every Kafka key, and every table. There are no per-brand topics, services, or databases.
7. **One edge, one policy point.** Kong is the only place a request is allowed through or stopped. Nothing behind it validates the token again or calls Azure AD.
8. **No personal data on the bus.** A record carries `customer_id`, never a phone number, an email, an address, or a LINE user id. A domain that needs contact details reads them from Identity at the moment it needs them.

---

## 3. Components

### Edge, BFFs, and adapters (Bun/Elysia)

| Component | Who calls it | What it does | Never does |
| --- | --- | --- | --- |
| `customer-bff` | the customer app, with a customer JWT | shopper reads, the cart (`GetCart`, `UpdateCart`), `PlaceOrder`, wallet top-up, the inbox, and the WebSocket | write catalog, store, or admin state |
| `guest-bff` | the app with no login | `ListNearest` and `GetMenu`, and (proposed, P-45) the dine-in table routes, which accept only a guest token with scope `dine_in` | anything else that needs a principal |
| `admin-bff` | the admin console and CSC, with an admin JWT | every admin write, after it checks the grant in `X-Roles` | serve a shopper |
| `partner-bff` | partners with a partner JWT (`client_credentials`) | the partner API and the partner token endpoint | accept a customer or admin token |
| `partner-adapter` | aggregators (Grab, LINE MAN, Shopee Food), POS vendors (BSL first, then others), and fleet providers (ZEEK, Grab Express) | checks the signature, runs the vendor mapper (one per POS vendor, aggregator, and fleet provider) that turns the payload into one canonical command, publishes `order.requested`, `catalog.requested`, or `delivery.requested`, consumes facts and pushes them to the aggregator or the FAAS brand | own any state except its delivery log |
| `webhook-adapter` | the payment gateway (Omise) and the message providers (SES via SNS, SMS, LINE) | checks the signature, publishes `payment.requested` or `notification.requested` | call a domain over gRPC, or retry a provider |

A BFF talks to domains over gRPC. The one exception is `customer-bff`, which subscribes to Valkey pub/sub to push WebSocket frames. That path is at-most-once, and the app re-reads over gRPC when it reconnects.

### Domains (Go)

| Domain | Owns | Never owns |
| --- | --- | --- |
| Identity & Profile | the customer (the Minor ID: one account across brands), the brand membership (enabled or disabled per brand), login, the customer signing key (and the guest tokens it signs for dine-in, proposed in P-45), OTP generate and verify, the shared profile, addresses, contacts, PDPA consent | admin or partner identity, message delivery, loyalty or wallet balances |
| Admin & Partner | the admin principal, the grant, the session, the partner OAuth client, the only call to Azure AD | the customer |
| Brand & Store | the brand, the store, the group, the hours, the zone, the brand's feature switches and onboarding state (proposed, [`design/brand-configuration.md`](design/brand-configuration.md)), the table registry and QR key versions for postpaid table ordering (proposed, P-45) | menu, delivery fee, payment keys, other domains' settings |
| Catalog | SKUs, modifiers, menu versions, the sold-out flag, the price book | the store, the order |
| Cart & Order (the OMS) | the cart, the order, the POS ticket and its `pos_connection` per store, the POS adapter port and one adapter per vendor, the checkout saga, the order payload log in MongoDB, the table session and the postpaid tab with its rounds and bill (proposed, P-44) | the price (it asks Catalog), the charge (it asks Payment) |
| Payment & Billing | the transaction, gateway keys per brand, invoices and receipts | the order status, the wallet balance |
| Delivery | the delivery, the quote, the fee, the provider job, the rider, the roster, the earnings ledger | the store zone, the order, a real-money payout |
| Loyalty | points, the tier, and the card you scan | the order, voucher codes |
| Voucher & Campaign | vouchers, campaigns, holds, the redemption book, audiences | the member card, message delivery, points |
| Wallet | the wallet per brand and customer, the stored-value ledger, holds | real money, the charge, loyalty points |
| Notification | templates, the message log, the inbox, device tokens, reachability | the contact, the consent, the OTP code |

Each domain has one owner of truth. A second domain that needs that data calls the owner over gRPC, live, at the moment it needs it. It never writes the owner's table, and it keeps no copy of it unless a written decision says why (D-07).

### OMS and the POS adapter port

Cart & Order is the Order Management System (OMS). It does not call a POS vendor directly. It calls a `PosGateway` port, and a registry picks the vendor adapter for the store from `pos_connection` data.

```
 Order use case ──▶ PosGateway port ──▶ registry (brand, store) ──▶ adapter pos/bsl     ──▶ BSL
   (Go, OMS)                                                     ├─▶ adapter pos/promise ──▶ Promise
                                                                 └─▶ adapter pos/vivi    ──▶ VIVI
 vendor webhook ──▶ partner-adapter (vendor mapper, Bun) ──▶ order.requested{pos_status} ──▶ Order
```

- **Out:** one Go adapter package per vendor, behind the port. The BSL proxy is the transport of the BSL adapter until replaced.
- **In:** `partner-adapter` stays the only webhook entry. It checks the signature, maps the vendor payload to one canonical `PosUpdate`, and publishes `order.requested{pos_status}`. Per-vendor mapping lives in two small places: the Go adapter and the Bun mapper (the same shape as fleet providers, P-18).
- **Rules for updates:** apply by rank and version, never blindly. A POS update never rewrites the order's price lines. Reconciliation finds a POS that disagrees with the priced order. See [`design/pos-adapters.md`](design/pos-adapters.md).
- **Capabilities** (for example `supports_delivery`, `supports_promotions_passthrough`) are data per vendor, per brand, and per store. Postpaid table ordering adds open-check flags and port operations (`supports_open_check`, `supports_external_payment`, and others; P-49, [`design/postpaid-table-ordering.md`](design/postpaid-table-ordering.md#8-pos-adapter-implications)).

### Topics and diagram status

| Domain | Publishes | Consumes | HLD | LLD (draft) |
| --- | --- | --- | --- | --- |
| Identity & Profile | — | — | [`identity-customer-hld`](../domains/identity-and-customer/identity-customer-hld.drawio) | [`identity-customer-lld`](../domains/identity-and-customer/identity-customer-lld.drawio) |
| Admin & Partner | — | — | [`admin-partner-hld`](../domains/admin-and-partner/admin-partner-hld.drawio) | [`admin-partner-lld`](../domains/admin-and-partner/admin-partner-lld.drawio) |
| Brand & Store | `brand.changed`, `store.changed` | — | [`brand-store-hld`](../domains/brand-and-store/brand-store-hld.drawio) | [`brand-store-lld`](../domains/brand-and-store/brand-store-lld.drawio) |
| Catalog | `catalog.menu.published`, `catalog.availability.changed` | `catalog.requested`, `brand.changed`, `store.changed` | [`catalog-menu-hld`](../domains/catalog-and-menu/catalog-menu-hld.drawio) | [`catalog-menu-lld`](../domains/catalog-and-menu/catalog-menu-lld.drawio) |
| Cart & Order | `order.events`, `payment.requested` | `order.requested`, `payment.events`, `delivery.events` | [`cart-order-hld`](../domains/cart-and-order/cart-order-hld.drawio) | [`cart-order-lld`](../domains/cart-and-order/cart-order-lld.drawio) |
| Payment & Billing | `payment.events` | `payment.requested`, `delivery.events` (FAAS invoice on `delivered`) | [`payment-billing-hld`](../domains/payment-and-billing/payment-billing-hld.drawio) | [`payment-billing-lld`](../domains/payment-and-billing/payment-billing-lld.drawio) |
| Delivery | `delivery.events`, `payment.requested` (payout) | `order.events`, `store.changed`, `delivery.requested`, `payment.events` | [`delivery-dispatch-hld`](../domains/delivery-and-dispatch/delivery-dispatch-hld.drawio) | [`delivery-dispatch-lld`](../domains/delivery-and-dispatch/delivery-dispatch-lld.drawio) |
| Loyalty & MemberCard | `notification.requested` | `order.events` | [`loyalty-membercard-hld`](../domains/loyalty-and-membercard/loyalty-membercard-hld.drawio) | [`loyalty-membercard-lld`](../domains/loyalty-and-membercard/loyalty-membercard-lld.drawio) |
| Voucher & Campaign | `notification.requested` | `order.events` | [`voucher-campaign-hld`](../domains/voucher-and-campaign/voucher-campaign-hld.drawio) | [`voucher-campaign-lld`](../domains/voucher-and-campaign/voucher-campaign-lld.drawio) |
| Wallet | `notification.requested` | `payment.events` | [`wallet-hld`](../domains/wallet/wallet-hld.drawio) | [`wallet-lld`](../domains/wallet/wallet-lld.drawio) |
| Notification | — | `order.events`, `payment.events`, `delivery.events`, `notification.requested` | [`notification-hld`](../domains/notification/notification-hld.drawio) | [`notification-lld`](../domains/notification/notification-lld.drawio) |

Each LLD covers five core flows per domain, as a draft to be aligned with the business. The remaining entry points are added one page each, using the [template](#lld-page-template). The Identity draft has six pages and publishes nothing: every caller is waiting, so there is no topic (principle 1). The Wallet draft instead has one page for every entry point (seven), plus page 8, the end-to-end pay-with-wallet checkout. The Delivery draft has one page per entry point (fourteen), plus page 15, the end-to-end delivery order, and page 16, the payout reconcile (sixteen pages in the file; see [§14](#14-known-drift)). The Cart & Order draft adds page 6, the `delivery.events` consumer, and page 7, the cart. The Voucher & Campaign draft has one page per entry point (seven, including `IssueReward`). The Loyalty & MemberCard draft has six pages and publishes no fact of its own. The Notification draft adds a `delivery.events` consumer. The Payment draft adds the wallet tender on charge and refund, and a Statement page for the FAAS invoice. The Catalog draft adds `ListSkus`.

This table must agree with the registry in [`kafka-topics.md`](kafka-topics.md). If they differ, the registry wins and this table is fixed.

---

## 4. Interaction rules

### Pick the transport

```
Is someone waiting for the answer?
 ├─ yes ─▶ gRPC (domain to domain) or HTTPS (client to BFF). No Ack.
 └─ no
     ├─ Does another service need to react?        ─▶ publish a fact (after commit)
     ├─ Is the sender outside the domain and
     │  nobody waits (aggregator, POS, gateway)?   ─▶ send a command on <domain>.requested
     └─ Is it only this service's own background work?
                                                   ─▶ outbox table + worker in the same app. No topic.
```

### Rules

- **Clients talk to BFFs. BFFs talk to domains. Domains talk to domains.** All three are synchronous: client to BFF is HTTPS, and everything behind the BFF is gRPC.
- **External callbacks enter once.** A POS, aggregator, or fleet-provider webhook lands at `partner-adapter`, on a route per vendor, and the vendor's mapper turns it into one canonical command. A gateway or message-provider webhook lands at `webhook-adapter`. The adapter checks the signature, then publishes a command. A domain never exposes a webhook to the internet.
- **No chains of sync calls longer than two hops** on the shopper's path. If a third hop is needed, redesign the call first; a projection is the last resort and needs a written reason (D-07).
- **Partner aggregators** sit behind `partner-adapter`. A domain never calls an aggregator. The adapter consumes facts and pushes them to the aggregator.
- **POS vendors** sit behind the `PosGateway` port in Cart & Order. Only Order's POS worker sends a ticket. A BFF never calls a POS. Status comes back through `partner-adapter` ([`design/pos-adapters.md`](design/pos-adapters.md)).

### gRPC contract

| Rule | Detail |
| --- | --- |
| Packages | One `proto/` tree in the mono-repo, with packages named `mfg.<domain>.v1`. `buf lint` and `buf breaking` run in CI. A breaking change is a new `v2` package. |
| Metadata | Every call carries `x-brand-id`, `x-principal-id`, `x-roles`, and `traceparent`. The BFF copies them from the headers Kong injected. A domain rejects a call with no `x-brand-id` as `INVALID_ARGUMENT`. |
| Deadline | Every call sets a deadline. A domain passes the remaining time on to the next hop and never resets it. Budgets are in [§13 Open](#open--needs-a-business-answer). |
| Idempotency | Every mutating call that a client may retry carries an `idempotency_key`. The callee stores it in a unique column in the same transaction and returns the first result on a repeat. It is required on `PlaceOrder`, `CreateTransaction`, and `Refund`. |
| Retries | Retry only on `UNAVAILABLE`, at most twice with jittered backoff, and only for reads or calls that carry an `idempotency_key`. |
| Writes on a versioned aggregate | Carry the expected `version`. A stale version returns `ABORTED`, and the caller reloads. |

The BFF maps gRPC status codes to HTTP once, for every route:

| gRPC | HTTP | gRPC | HTTP |
| --- | --- | --- | --- |
| `INVALID_ARGUMENT` | 400 | `ALREADY_EXISTS`, `ABORTED`, `FAILED_PRECONDITION` | 409 |
| `UNAUTHENTICATED` | 401 | `RESOURCE_EXHAUSTED` | 429 |
| `PERMISSION_DENIED` | 403 | `UNAVAILABLE` | 503 |
| `NOT_FOUND` | 404 | `DEADLINE_EXCEEDED` | 504 |

Anything else is a 500. The HTTP body is `{ "code", "message", "trace_id" }`. It never contains a stack trace or another domain's internals.

---

## 5. Event-driven rules (Confluent Kafka)

These are the rules behind [`kafka-topics.md`](kafka-topics.md). They come from Confluent's topic-design guidance and from how food-delivery checkouts run in production:

- [Should you put several event types in the same Kafka topic?](https://www.confluent.io/blog/put-several-event-types-kafka-topic/)
- [Multiple event types in the same topic, revisited](https://www.confluent.io/blog/multiple-event-types-in-the-same-kafka-topic/)
- [DoorDash: a more reliable checkout service](https://careersatdoordash.com/blog/building-a-more-reliable-checkout-service-with-kotlin/)

### Which topics exist

1. **A topic must cross a service boundary.** A service never publishes a topic that only it consumes. Internal work queues are an outbox table plus a worker.
2. **At most one inbound command topic per domain:** `<domain>.requested`. It carries one Protobuf `oneof` and is keyed by the aggregate id, so a cancel cannot pass the create for the same order.
3. **One fact topic per aggregate.** Events about the same entity share one topic and one key, because Kafka only keeps order within a partition.
4. **Split a topic only when the throughput or the owner differs.** `catalog.availability.changed` is separate from `catalog.menu.published` because sold-out changes far more often than menus do.
5. **A new topic needs three answers:** who produces it, who consumes it, and why a gRPC call or an existing topic does not cover it. Add it to `kafka-topics.md` before it appears on a diagram.

### Topic names and shapes

| Suffix | Kind | Retention | Example |
| --- | --- | --- | --- |
| `.requested` | command into one domain, `oneof` | 7 days | `order.requested` |
| `.changed` | compacted state, latest value per key | compact | `store.changed` |
| `.published` | compacted, a thin version pointer | compact | `catalog.menu.published` |
| `.events` | lifecycle facts, `oneof` | 7 days | `order.events` |

- **Compacted state replaces snapshot topics.** A new consumer reads the latest value per key, then Acks. Nobody replays history.
- **Thin events for large payloads.** Kafka's default limit is 1 MB. A menu publish carries only the version, and the consumer calls `GetMenu(version)`.

### Record contract

```
key:     brand_id:<aggregate id>
headers: event_id, event_type, brand_id, occurred_at, version, traceparent
value:   Protobuf oneof · Schema Registry · BACKWARD compatible
```

- `event_id` is a UUID and the idempotency key. `version` increases for each key.
- **Partitions:** 6 by default, 12 for `order.*` and `payment.*`.
- **The bus never carries** a token, a secret, a client assertion, a full card number, a full menu body, or personal contact data.

### Producer: the outbox

```
 domain transaction                         worker mode · one active relay per domain
┌──────────────────────────────┐          ┌──────────────────────────────────────────┐
│ UPDATE state, version + 1    │          │ read unpublished rows in id order        │
│ INSERT outbox row            │──commit─▶│ produce (idempotent producer, acks=all)  │──▶ Kafka
└──────────────────────────────┘          │ set published_at after the broker ack    │
                                          └──────────────────────────────────────────┘
```

- **Outbox row:** `id` (bigserial), `topic`, `key`, `event_id`, `event_type`, `headers`, `payload` (Protobuf bytes), `created_at`, `published_at`.
- **One active relay per domain.** It holds a Postgres advisory lock, so a second replica waits. This keeps per-key order without coordination.
- **A crash between produce and `published_at`** publishes the row again. That is safe because every consumer is idempotent.
- **Rows published more than 7 days ago are deleted** by the domain's cron.
- `ponytail:` one relay per domain. Ceiling: the throughput of one producer loop. Upgrade: shard the relay by a hash of `key`, with one lock per shard.
- There is no Debezium and no Kafka Connect cluster of our own.

### Consumer: apply, then Ack

```
poll ─▶ dedupe ─▶ apply + commit (Postgres) ─▶ Ack (commit offset)
          │ already seen ──────────────────────▶ Ack, no work
          └ fails ─▶ retry 3× with backoff in the app ─▶ <service>.dlq ─▶ Ack
```

- **Facts** (`.changed`, `.published`, `.events`) are deduplicated on `version`: apply only if it is newer than the stored one.
- **Commands** (`.requested`) are deduplicated on `event_id`: insert it into the domain's `processed_event` table in the same transaction as the change. A unique-key conflict means "already done".
- **Ack** means committing the Kafka offset after the Postgres commit. Auto-commit is off.
- There are no per-topic retry topics. A DLQ is operational and is not drawn as a domain topic. Replaying a DLQ is a manual runbook step.

---

## 6. State and data rules

- **Aurora PostgreSQL** is the system of record for every domain, with one schema and one database role per domain. A role can read and write only its own schema. A second database engine needs a written reason in that domain's Decisions lane.
- **MongoDB (Atlas on AWS, to confirm with DevOps) is allowed for one use only: the order payload log in Cart & Order (P-38).** It is a parallel, append-only trace of the raw and converted payloads of every outside party, linked to the Postgres order by `order_id`. It is never the truth, never read on the shopper path, and never blocks checkout. Payloads are masked before they are stored, so principle 8 holds. **The written reason** (this is the Decisions-lane entry for Cart & Order, to be copied into its HLD at the next diagram update): order payload shapes differ per brand, POS vendor, and aggregator and change without notice, so a fixed table needs a migration for each change; the log is write-heavy, expires per document, and is never joined; and a separate engine keeps its outage and its size away from checkout. The cost is a second engine to run, a second place with personal-data rules, and a link by id with no foreign key. Postgres JSONB is a credible simpler alternative, and P-38 says to revisit if the cost is not worth it. Full text: [`design/order-payload-log.md`](design/order-payload-log.md). Any other use of MongoDB needs its own written reason and decision.
- **ElastiCache Valkey** is the only in-memory store. It is allowed for four things: a read cache filled after the commit, short-lived auth state (refresh-token family, auth code, PKCE verifier), rate-limit token buckets, and WebSocket pub/sub. Losing Valkey can log users out or drop a frame. It must never lose an order, a payment, or a balance.
- **S3** holds files: images (served through the Cloudflare CDN with a presigned PUT), imports, broadcast audiences, invoices, and the data-lake sink.
- **Vault** holds signing keys and gateway and provider secrets. They never appear on the bus or in a log.
- **Version every writable aggregate.** Every write bumps `version`, so consumers can drop stale or duplicate records.
- **Derive, don't store, anything computed from other fields.** Open-now comes from hours, status, and the current time. Daypart is applied when the menu is read. Neither one is a column or a topic.
- **No copies of the store or the menu.** Everything is online and real-time, and nothing is kept offline at the store. A domain that needs a store or a menu calls `ResolveStore` or `GetMenu` live. A consumer of `brand.changed` or `store.changed` reacts by changing its own rows (Catalog hides a brand that is not live); it does not store the other domain's fields.
- **A projection is the exception, not the default.** It is allowed only when a live call can't meet the need (for example, geo queries at dispatch volume) and the domain's Decisions lane says so. It holds only the fields that domain needs and is rebuilt from the compacted topic.
- **Two things that look like copies but are not:**
  - The **menu version** is the published state of a menu, not an offline copy. It keeps a half-edited draft away from shoppers, allows a scheduled publish, tells aggregators which menu they have, and keys a cache that can never be stale. Sold-out stays outside it and is real-time.
  - The **order's price lines** are the order's record of what the shopper agreed to pay. The receipt, the tax invoice, a refund, loyalty points, and a dispute all need the price at order time, even after the menu changes.
- **Don't write "snapshot"** in a diagram or a doc. Say "menu version", "price lines", or "projection", so nobody reads it as an offline copy.
- **Time.** Store every timestamp as `timestamptz` in UTC. Business times (store hours, quiet hours, cron schedules) are written in `Asia/Bangkok`.
- **Money.** Store amounts as integer minor units (satang) with an ISO currency column. Never use floats.
- **Migrations** live with the domain app and run as a pre-deploy job. A migration must work with the previous release still running (expand, then contract).

---

## 7. Sagas and long-running flows

- **The domain that owns the outcome runs the saga.** Order runs checkout: it asks Brand & Store whether the store can take the order, Catalog for the price, Delivery for the quote, Voucher for the deals, and Payment for an authorization, then dispatches to the POS and sends capture or void.
- **Saga state is a status column plus the outbox,** in the owning domain's Postgres. Each step commits before the next one starts. A crash resumes from the last committed status.
- **Food payments are authorized first and captured later.** Payment holds the money at authorize. Capture happens only after the POS accepts the ticket; a rejection becomes a void. Postpaid table orders are the one exception: they are charged and captured at the end ([below](#postpaid-flow-qr-table-ordering-proposal)).
- **Timeouts are a sweeper, not a timer service.** Order's cron finds checkouts that never got `authorized` and tickets the POS never answered, then closes them and sends a void.
- **No workflow engine in v1.** Temporal or Cadence comes in only when a step needs a durable timer that a sweeper cron can't cover. That limit is written on the Order HLD as a `ponytail:` note.

### Reference flow: own-app checkout

This is the cross-domain baseline every Order and Payment LLD follows. The shopper waits on steps 1 to 5 only.

```
 0  customer-bff ──gRPC GetCart / UpdateCart──▶ Order ──gRPC PriceLines──▶ Catalog
    then ──gRPC EvaluateBasket──▶ Voucher                                        the cart, priced live
 1  customer-bff ──gRPC PlaceOrder(idempotency_key, cart_version, expected total)──▶ Order
 2  Order ──gRPC ResolveStore──▶ Brand & Store, then ──gRPC PriceLines──▶ Catalog,
    then ──gRPC GetQuote──▶ Delivery, then ──gRPC EvaluateBasket──▶ Voucher
 3  Order ──gRPC ReserveRedemptions(order_id)──▶ Voucher, then commits the order
    with its price lines and the quoted fee (not placed yet)
 4  Order ──gRPC CreateTransaction(idempotency_key)──▶ Payment ──HTTP──▶ Omise
    (a wallet tender calls Wallet Hold here instead; see below)
 5  authorize_url ──▶ Order ──▶ customer-bff                  shopper finishes 3DS / QR at the gateway
 ─────────────────────────────────────────────── nobody waits from here ───────────────────────────────
 6  Omise ──webhook──▶ webhook-adapter ──payment.requested{webhook}──▶ Payment
 7  Payment commits ──▶ payment.events{authorized}                                              · Ack
 8  Order commits placed, deletes the cart ──▶ order.events{placed}                            · Ack
    Voucher spends the hold on that fact
 9  Order POS worker ──PosGateway port──▶ the store's vendor adapter ──▶ POS ticket
    (the adapter comes from pos_connection; BSL is the first one, through the BSL proxy)
10  POS ──webhook──▶ partner-adapter (vendor mapper) ──order.requested{pos_status}──▶ Order
    Order applies it by rank and version: duplicates and late updates are dropped (P-36)
11  accepted: commit accepted + capture ──▶ order.events{accepted} · payment.requested{capture} · Ack
    rejected: commit rejected + void    ──▶ order.events{rejected} · payment.requested{void}    · Ack
    Delivery starts dispatch on accepted
12  Payment captures or voids ──▶ payment.events{captured | voided} ──▶ Order closes the step  · Ack
```

| Failure | What happens |
| --- | --- |
| Store hidden, not live, or closed at step 2 | `PlaceOrder` returns `FAILED_PRECONDITION`. Nothing is committed. |
| Live total differs from the total the shopper saw at step 2 | `PlaceOrder` returns `FAILED_PRECONDITION` (`price_changed`). Nothing is committed. The app re-reads the cart. |
| Brand & Store, Catalog, Delivery, or Voucher down at step 2 or 3 | `PlaceOrder` returns `UNAVAILABLE`. Nothing is committed. The app retries with the same `idempotency_key`. |
| Quote expired, used, or for another brand | `PlaceOrder` returns `FAILED_PRECONDITION`. Nothing is committed. |
| Payment down at step 4 | The order stays unplaced. A retry with the same key returns the same order and calls `CreateTransaction` again. |
| Shopper abandons 3DS | No `authorized` arrives. The sweeper closes the order after the payment window and sends `payment.requested{void}`. |
| `payment.events{failed}` | Order commits `cancelled` with reason `payment_failed` and publishes `order.events{cancelled}`. Notification messages from that fact only. |
| POS never answers | The sweeper rejects the ticket after the POS window and sends a void. |
| POS update is a duplicate, late, or out of order | Dropped or recorded as stale. A lower rank never moves a ticket backward ([`design/pos-adapters.md`](design/pos-adapters.md#5-applying-an-update-order-duplicates-and-totals)). |
| POS reports a total that differs from the priced order (a dropped promotion, a reset total) | The order's price lines never change. A reconciliation row and a CSC queue entry are written. The rule for fixing the difference is open (O-32). |
| The store's POS cannot take this fulfillment (for example delivery) | `PlaceOrder` returns `FAILED_PRECONDITION` (`fulfillment_not_supported`). Nothing is committed. |
| Crash anywhere | The step resumes from the last committed status. A redelivered record is a no-op. |

**Aggregator orders** skip steps 1 to 7. The aggregator has already collected the money, so `partner-adapter` publishes `order.requested{create}` and Order commits `placed` straight away. Steps 9 to 11 are the same, without capture or void.

**The payload log is not a step.** At steps 9 and 10, and when an aggregator order enters, adapters and Order capture the raw and converted payloads in memory. A writer sends them to MongoDB later, best effort. Nothing waits for it and a failure does not touch the order ([`design/order-payload-log.md`](design/order-payload-log.md#6-write-path-how-it-gets-written-without-breaking-commit-then-the-fact)).

**Wallet orders** use the same steps with `method = wallet`. At step 4, Payment calls Wallet `Hold` instead of Omise. Step 5 returns `authorized` with no `authorize_url`, and step 6 is skipped. At step 12, Payment calls Wallet `Capture` or `Release`. A short balance at step 4 is `FAILED_PRECONDITION`, and the app offers a card for the whole order (P-16). See [Wallet LLD 8](../domains/wallet/wallet-lld.drawio).

### Postpaid flow: QR table ordering (proposal)

**Proposal (P-44 to P-52), first draft.** Postpaid inverts the reference flow: the order goes to the kitchen first, and the money moves at the end. Cart & Order owns the table session and the tab (an order with `order_type = dine_in_postpaid`, with one round per "send to kitchen"). The full design, the alternatives, and the open questions are in [`design/postpaid-table-ordering.md`](design/postpaid-table-ordering.md).

```
 1  guest-bff or customer-bff ──gRPC StartTableSession(qr, table code)──▶ Order ──gRPC ResolveTable──▶ Brand & Store
 2  guest-bff or customer-bff ──gRPC PlaceRound(idempotency_key, lines, expected total)──▶ Order
    Order prices live with Catalog, commits the round and the outbox row; the first round publishes order.events{placed}. No payment.
 3  Order POS worker ──PosGateway: OpenCheck once, AddItems per round (or one ticket per round)──▶ the store's POS
 4  POS ──webhook──▶ partner-adapter ──order.requested{pos_status}──▶ Order applies by rank and version ──▶ order.events{round_updated}
 5  diner RequestBill ──▶ Order builds the bill from the agreed lines, with EvaluateBasket, service charge, and tip
 6  diner PayBill ──▶ Order locks the tab, ReserveRedemptions, ──gRPC CreateTransaction(purpose=table_bill)──▶ Payment ──▶ gateway
 ─────────────────────────────────────────────── nobody waits from here ─────────────────────────────
 7  gateway ──webhook──▶ webhook-adapter ──payment.requested{webhook}──▶ Payment ──▶ payment.events{captured}
 8  Order commits paid; the POS worker calls ApplyPayment and CloseCheck; Order commits closed ──▶ order.events{completed}
 9  Voucher commits its hold, Loyalty earns points, Notification messages a signed-in diner, Statement writes the receipt
```

| Failure | What happens |
| --- | --- |
| The POS never answers a round | The sweeper rejects the round after the POS window. Nothing is billed. The tab stays open |
| Payment fails at step 6 | `payment.events{failed}` returns the tab to `bill_requested`. The diner retries |
| The POS check cannot be closed after the diner paid | The tab stays `paid`. The close is retried, then goes to a staff queue. No second charge and no automatic refund |
| The diner pays at the counter | The POS update closes the tab (`settlement = counter`), or staff use `ForceCloseTab` |
| The diner walks out | Staff flag the tab (`MarkTabUnpaid`). No timer ever closes a tab as paid or unpaid |

What differs from the reference flow: `placed` happens at the first round (an extension of P-09, in P-46), the charge is captured at authorize (as P-17, in P-47), no Kafka topic is added (P-51), and the bill never takes its total from the POS (P-49, R5).

---

## 8. Edge, identity, and security

- **Cloudflare** handles bots, WAF, and TLS. **Kong** is the only policy enforcement point (PEP). It picks the JWKS by `iss`, strips `Authorization`, and injects `X-Principal-Id`, `X-Roles`, and `X-Brand-Id`. Everything downstream reads those headers.
- **There are three token families, each with its own signing key:** customer (issued by Identity), admin (Admin), and partner (Partner). A token from one family is rejected on the routes of another.
- **Azure AD** is the admin identity provider. Only the Admin & Partner domain calls it, through a port. No other domain, Identity included, imports an Azure SDK.
- **Partners** use `client_credentials` with `private_key_jwt`. We store the partner's public key, never a long-lived API key. There is no partner refresh token: the client asks again.
- **Webhooks** pass through Cloudflare and Kong on routes with no JWT, but with a rate limit. The adapter checks the provider's signature and timestamp. A bad signature is rejected before anything reaches Kafka.
- **Revocation:** access tokens live 5 minutes. Revoking an admin session kills the refresh-token family. Suspending a partner bites on the next token request, because a partner has no refresh token. There is no denylist projector. The cost is that a revoked token can last until it expires.
- **Audit** is an append-only table written in the same transaction as the change. It is not a topic.
- **Logs** carry `brand_id`, `trace_id`, and ids. They never carry a token, a secret, an OTP, a card number, or contact data.

---

## 9. Runtime shape

- **Domains are Go, and BFFs and adapters are Bun and Elysia v2.** They live in one mono-repo, with one app per domain. Elysia 2 is a release candidate as of 2026-10-19 (verified): pin the exact version, and see [`design/tech-stack.md`](design/tech-stack.md) for what is verified and what is still to verify.
- **The edge API is REST only for now.** Behind the edge it stays gRPC. An AI assistant comes later, so the edge keeps stable OpenAPI contracts, idempotent operations, scoped tokens, and audit (P-41). P-34 still holds: the AI writes only through `UpdateCart`.
- **Go domains use a hexagonal structure** (ports and adapters): the domain and its use cases know no gRPC, Kafka, Postgres, or vendor. Each mode below is a different driving adapter on the same core: `api` is `adapters/in/grpc`, `consumer` is `adapters/in/kafka`, `worker` is the outbox relay and background loops, and `cron` is `adapters/in/cron`. The layout is proposed. **Align with the boilerplate when the owner shares it.** Details: [`design/tech-stack.md`](design/tech-stack.md#3-core-go-with-a-hexagonal-structure).
- **Infrastructure is run by the DevOps team,** stays on AWS as much as possible, and is fixed for the core pieces listed in [`design/tech-stack.md`](design/tech-stack.md#1-what-is-fixed-and-what-is-open). A new tool may be non-AWS when it is clearly better, and needs a decision row.
- **Each domain app runs in modes:** `api` (gRPC), `consumer` (Kafka), `worker` (the outbox relay and background jobs), and `cron`. Choose modes before adding a new service. Statement is a mode of the Payment app, and Brand and Store are one app.
- **Each mode is its own Kubernetes workload** from the same image, so a slow consumer never takes the `api` pods down with it.
- **`cron` mode runs as a Kubernetes CronJob** with `concurrencyPolicy: Forbid` and `timeZone: Asia/Bangkok`. Every job is safe to run twice. Its schedule and its flow go in that service's `docs/cron-flow.md`.
- **Health:** `api` mode serves `grpc.health.v1`. Every mode serves HTTP `/healthz` (liveness) and `/readyz` (readiness, which checks Postgres and, for `consumer` and `worker`, Kafka). Each service documents this in its `docs/health-check.md`.
- **EKS** runs the apps. **Lambda** is only for headless, scheduled glue that has no domain state.
- **Observability:** CloudWatch and OpenTelemetry. `traceparent` travels in gRPC metadata and Kafka headers, so a trace crosses the bus.

---

## 10. Simplicity guardrails

These were cut on purpose. Do not bring them back without a written reason and a named consumer.

| Cut | Use instead | What it costs |
| --- | --- | --- |
| Snapshot topics | compacted `.changed` | consumers ignore fields they don't need |
| A copy of the store or menu in another domain | `ResolveStore` and `GetMenu`, live | the caller fails when the owner is down |
| A topic per field change (hours, status, zone, group) | one `store.changed` | a fatter record |
| A cron that publishes derived state (open-now) | derive when reading | each reader computes it |
| An import command topic | a worker reads S3 or Excel | none, because nothing else consumed the file |
| Internal request/result topics (`order.bsl.*`, `payment.gw.request`) | outbox + worker + gRPC | none |
| Admin and partner security facts | the audit table | no streaming fraud detection |
| A fraud worker and a Kong denylist projector | 5-minute access tokens + refresh revoke | up to 5 minutes of a revoked session |
| Two engines for brand and store | one Brand & Store app | one deploy for both |
| A store portal and a Store BFF | `admin-bff` with a store-manager grant | store staff use the admin console |
| A bank-failover payment path and a ledger service | one provider per brand, the transactions table | no automatic second PSP; the 2029 concept asks for routing across partners (O-22) |
| A workflow engine | status column + outbox + sweeper cron | no durable timers |
| OpenSearch for menus | Postgres + Valkey | search is fed from facts later |
| ~~Several POS proxies from day one~~ **Reversed in v3 (P-36).** | A `PosGateway` port with one adapter per vendor. BSL is the first adapter, and others are added when a brand onboards | The port, the registry, the per-store `pos_connection`, and capability flags are built before the second vendor exists, and every vendor needs a Go adapter plus a Bun mapper. **Why it was reversed:** the owner decided each brand may use its own POS vendor and that OMS must not be BSL-strict. A BSL-only proxy would put BSL's behavior into the order state machine, and removing it later would cost more than the port. Only the BSL adapter is built now: a second adapter is written only when a brand needs it |
| A Notification fact topic and a socket service | the message log, Valkey pub/sub in `customer-bff` | a dropped frame; stats are read over gRPC |
| A copy of contacts and consent outside Identity | `BatchGetContacts` at send time | a send waits when Identity is down |

**Kept on purpose:** the channel price book (aggregator prices differ), the thin menu publish, Valkey keyed by menu version (lunch peak), PostGIS zones, and per-brand gateway accounts.

**Added in v3, each with a cost and a flag:** the POS adapter port (P-36), the MongoDB order payload log (P-38, flagged against principles 1 and 3), and the legacy bridge (P-39, flagged against principle 3 while a capability is still on legacy). No topic was added in v3 ([`kafka-topics.md`](kafka-topics.md#growth-policy)).

**Added 2026-10-25:** the postpaid table tab (P-44 to P-52), with its own cost list in [`design/postpaid-table-ordering.md`](design/postpaid-table-ordering.md#15-conflicts-and-flags). It adds no topic, service, or database engine. It extends P-09, P-01, and the `guest-bff` scope, and it is flagged against P-16 and the three token families of §8.

---

## 11. Diagram standard

### What each level contains

| | HLD (`<domain>-hld.drawio`) | LLD (`<domain>-lld.drawio`) |
| --- | --- | --- |
| Question it answers | What does this domain own, what goes in and out, and what did we cut? | How does each flow run, step by step, including failures? |
| Content | callers, Kafka in, the engine's building blocks, facts out, consumers, data, decisions, not this domain | one page per entry point: trigger, each hop, commit, publish, Ack, and failure or retry |
| Payloads | topic name, key, and `oneof` variants | field-level message shapes, tables touched, and outbox rows |
| Count | one page per domain | one page per gRPC method, consumer, cron, and webhook |

Both files live in `domains/<domain>/`. An LLD must not introduce a topic, a service, or an owner that the HLD doesn't show. If it needs one, change the HLD and `kafka-topics.md` first.

### LLD page template

Every LLD page is one strip that runs left to right through the same stages. A stage that does not apply is left out. The Ack follows the commit, because the relay publishes later and nobody waits for it, so the publish is drawn as a branch below the commit.

```
 Trigger ─▶ Validate ─▶ Load + check version ─▶ Apply rule ─▶ Commit (state + outbox) ─▶ Ack
              │                    │                              │ async
              ▼                    ▼                              ▼
         failure exit         failure exit                 Outbox relay ─▶ publish fact or command
       INVALID_ARGUMENT    same version → Ack          (a gateway or POS worker sits here too)
                           error → retry 3× → <service>.dlq → Ack
```

Below the strip, every page has four panels: **Contract** (field-level messages), **Writes** (tables and outbox rows), **Dedupe · deadline · retry**, and **Notes** (decision ids cited). Failure exits are red boxes under the step that fails, joined by a dashed red line. The [Cart & Order LLD](../domains/cart-and-order/cart-order-lld.drawio) is the reference page.

Each page also names: the deadline or timeout, the `idempotency_key` or `version` used for dedupe, the tables it writes, the outbox records it adds, and every failure exit with its gRPC status or DLQ.

### HLD page layout (copy it from the Catalog HLD)

```
 y=12   Title (22px bold)  ·  y=46 subtitle (12px grey)
 y=86   [ gRPC ] [ JWKS / HTTP ] [ Kafka command ] [ Kafka fact ]        ← legend pills

 x=16            x=392                          x=1188         x=1524
 ┌──────────┐    ┌───────────────────────────┐
 │1 Callers │    │3 Engine · Go              │
 │360 × 520 │    │780 × 944                  │  ┌──────────┐  ┌───────────┐
 ├──────────┤    │                           │  │4 Facts   │  │5 Consumers│
 │2 Kafka in│    │                           │  │out       │  │           │
 │360 × 408 │    │                           │  │320 × 552 │  │420 × 552  │
 └──────────┘    └───────────────────────────┘  └──────────┘  └───────────┘
                 Contract strip (y=1084)
 ┌──────────┐    ┌───────────────────────────┐  ┌───────────────────────────┐
 │6 Data    │    │Decisions · what it costs  │  │Not this domain            │
 │500 × 350 │    │640 × 350                  │  │756 × 350                  │
 └──────────┘    └───────────────────────────┘  └───────────────────────────┘
 page 1980 × 1540
```

- **Every lane is always present.** If a lane has nothing in it, it says why in one line, for example "No Kafka in. Every write has an admin waiting, so it is gRPC."
- **The Decisions lane** lists each simplification together with what it costs. **Not this domain** lists what a reader might expect here and which domain owns it instead.
- **The Contract strip** says in two lines who writes, who reads, what is published, and which path has no Ack.

### Colors and shapes

| Meaning | Stroke | Fill |
| --- | --- | --- |
| gRPC, sync, client waits | `#EA580C` | `#FFF7ED` |
| JWKS / HTTP, edge, external | `#2563EB` | `#EFF6FF` |
| Kafka command | `#7C3AED` | `#F5F3FF` |
| Kafka fact | `#059669` | `#ECFDF5` |
| Engine lane | `#EAB308` | `#FEF9C3` |
| Engine box (HLD) | `#EAB308` | `#FFFFFF` |
| Data, decisions | `#64748B` | `#F8FAFC` |
| Callers, Consumers, Not this domain lanes | `#94A3B8` | `#F8FAFC` |
| Failure exit (LLD) | `#DC2626` | `#FEF2F2` |

HTTP is blue, not teal. Teal was too close to the Kafka fact green to tell apart.

- **Box color is the legend, never decoration.** A box takes the color of the pill that describes it:
  - A gRPC door, a gRPC caller, or a gRPC callee is orange.
  - A third party reached over HTTP, and the edge (Cloudflare, Kong, Azure AD), is blue.
  - A topic box, the engine door that consumes it, and every consumer of it take the topic's color: green for a fact, purple for a command.
  - Anything inside the engine that is not a door (state, workers, crons, the outbox relay, adapters behind a port) is engine yellow, even when it makes an HTTP or gRPC call. The line carries the transport color; the box does not.
  - Aurora, Valkey, S3, and Vault are data grey.
- **Detail lines** use the darker ink of the box color: `#C2410C` gRPC, `#1D4ED8` HTTP, `#6D28D9` command, `#047857` fact, `#854D0E` engine, `#64748B` data.
- **Lanes:** only Kafka in, the engine, Facts out, and the data lanes are colored. Callers, Consumers, and Not this domain are neutral, so a lane never reads as a transport.
- **Boxes:** rounded with `arcSize=10`, 12px bold title, 11px detail lines, and at most three detail lines. If text doesn't fit, shorten it before making the box bigger.
- **External or not-shipped** components use a dashed border.
- **Logos:** any third-party box carries its logo at 30×30, placed 16px from the left edge and centered vertically, with 8px between logos and the label starting 16px after the last logo. Logos are embedded as data URIs. Every topic box carries the Kafka logo.
- **Ack:** a green ellipse (`#059669`, 72×28, white label "Ack") at the end of every Kafka consume. Sync paths and publishes never get one.

### Lines

- **Draw only real relationships:** a call, a publish, a consume, or a commit. Every line has a verb label, or sits right next to one that does.
- **A line never passes through a box.** Between lanes, route it through the gap between the lanes. Inside a lane, connect only neighboring boxes.
- **Fan-out:** one fact to several consumers runs as one trunk in the gap, with one `consume` label on the first branch.
- If a line can't be drawn without crossing boxes, move the boxes. If it still can't, leave the line out and say it in the box text, such as "Delivery reads `store.changed`".

### Required lines on every HLD

A box with no line in or out is a sign that something is missing. Before an HLD is reviewed, it must have each of these lines. The [Wallet HLD](../domains/wallet/wallet-hld.drawio) is the reference.

| From | To | Label |
| --- | --- | --- |
| each caller in lane 1 | the engine box it calls | `gRPC` (or `HTTP`) |
| each topic in lane 2 | the engine box that consumes it, followed by an Ack | `consume` |
| each engine door (an API, a consumer, a cron) | the state box it writes or reads | a verb: `hold`, `credit`, `read`, `check` |
| the state box | the outbox relay | `same commit` |
| the outbox relay | each topic in lane 4 | `publish` |
| each topic in lane 4 | each consumer in lane 5, followed by an Ack | `consume` |
| the engine lane | the Data lane | `commit · read` |

- **Align a caller with the box it calls.** Put each engine door at the same height as its caller, so the line is straight across the gap between the lanes.
- **Leave 48px between engine columns,** so each line's label has room and does not sit on another line.
- **Route between lanes at the gap's midpoint** (for example x=384 between Callers and the engine, and x=1180 between the engine and Facts out). Use waypoints, not a straight diagonal.
- **Check it by eye.** Export a PNG (`draw.io -x -f png`) and look at it before handing in. A line through a box or a label sitting on another line fails review.

### Overbuild check

Before an HLD is reviewed, try to delete each item below. Keep it only if the answer to its question is yes. Each item cut from the Wallet draft is noted next to its question.

- **A timer or sweeper.** Does no other domain already close this step? (Wallet's hold timer was cut: Order's sweeper already voids, and the void releases the hold.)
- **A status or admin operation.** Did someone ask for it? (Freeze and `SetWalletStatus` were cut.)
- **A second table for one fact.** Does each row in the first table ever have more than one row in the second? (`wallet_txns` was merged into `wallet_entries`.)
- **A partial or optional variant.** Does a v1 flow need it? (Partial capture was cut; a partial refund covers it.)
- **A topic, a cache, or a cron.** Is there a named consumer, and does no gRPC call or existing topic already cover it? (Principle 1.)

Write each cut in the Decisions lane with its cost.

---

## 12. Checklists

### Before drawing the LLD

Answer each of these in the HLD.

1. **Owner.** What state does this domain own, and who is the single writer? Which part of it is "not this domain"?
2. **Doors.** Who calls in, and is each caller waiting? Waiting means gRPC through a BFF. Not waiting means a command on `<domain>.requested`.
3. **Facts.** Which other domain reacts to a change here? Name the consumer. With no consumer, there is no fact.
4. **Topic fit.** Can an existing topic carry it as one more `oneof` variant? Only if not, add a topic to `kafka-topics.md` with its owner, key, kind, retention, producers, and consumers.
5. **Key and version.** What is the aggregate id, and where does `version` bump?
6. **Commit.** Is the state change and its outbox row in one transaction?
7. **Idempotency.** What happens when the same record arrives twice? When it arrives out of order? Which mutating gRPC call takes an `idempotency_key`?
8. **Failure.** What happens when a downstream service is down, a retry runs out, a step never gets an answer, or the process crashes before Ack?
9. **Tenancy.** Is `brand_id` on the key, the headers, the metadata, and the table? Is a missing `brand_id` a reject?
10. **Personal data.** Does any record or log carry contact data? It must not.
11. **Cut list.** What did you choose not to build, and what does that cost? Write it in Decisions.
12. **Diagram.** Is it on the grid, with every lane present, logos placed, an Ack on every consume, and no line through a box? Does every box take its color from the legend, per [Colors and shapes](#colors-and-shapes)?
13. **Lines.** Does every row of [Required lines on every HLD](#required-lines-on-every-hld) have its line? Is there a box with no line in or out? Was the PNG export checked by eye?
14. **Overbuild.** Did every item in the [Overbuild check](#overbuild-check) keep its yes, and is each cut written in Decisions with its cost?
15. **Brand variation.** What can differ per brand or per store here, and is it data owned by this domain ([`design/brand-configuration.md`](design/brand-configuration.md)) rather than a brand name in code? Is the default for an unset setting "off"?
16. **Vendors and legacy.** Does an outside system (a POS, a provider, a legacy system) sit behind a port with capability flags, and does a duplicate, late, or wrong answer from it have a rule?

### Ready for development

A domain starts coding only when all of these are true.

- [ ] The HLD is reviewed, and no row in [§14](#14-known-drift) is open for this domain. (In v3 several rows are open on purpose: the text moved ahead of the diagrams.)
- [ ] Every topic it produces or consumes is in `kafka-topics.md`, and the table in [§3](#topics-and-diagram-status) matches.
- [ ] The `.proto` for every gRPC method and every topic value it owns is merged, and `buf lint` and `buf breaking` pass.
- [ ] The LLD has one page per entry point, using the [template](#lld-page-template), with every failure exit drawn.
- [ ] Every table is listed with its schema, `version` column, outbox, and `processed_event` table where it is needed.
- [ ] Every Open decision in [§13](#open--needs-a-business-answer) that blocks this domain is answered.
- [ ] The service repo has its `README.md` and `docs/` scaffolded to the team documentation standard (`/mfg-docs`).

---

## 13. Decision register

Every decision has an id. HLD Decisions lanes and LLD notes cite it, for example "per D-04". To change a decision, edit its row and say why.

### Accepted

These settle conflicts between the existing HLDs. They are binding.

| Id | Decision | Why | Cost |
| --- | --- | --- | --- |
| D-01 | Azure AD is called only by Admin & Partner. Identity owns the customer login only. | one owner per identity provider | none; the Catalog and Brand & Store HLDs are updated |
| D-02 | Order calls `CreateTransaction` for every order payment. `customer-bff` calls Payment directly only for a wallet top-up. | the domain that owns the outcome runs the saga | Payment trusts the amount Order sends |
| D-03 | The edge has four BFFs (`customer`, `guest`, `admin`, `partner`) and two adapters (`partner-adapter` for aggregators, POS, and fleet providers, `webhook-adapter` for the gateway and message providers). Fleet webhooks were added in P-18. | a payment webhook never queues behind an aggregator menu push | two Bun apps instead of one |
| D-04 | Valkey is limited to the four uses in [§6](#6-state-and-data-rules). It is never the truth for an order, a payment, or a balance. | Postgres is the truth | losing Valkey logs users out |
| D-05 | No personal data on the bus (principle 8). | PDPA has a single copy to manage | a send waits on Identity |
| D-06 | Files without a suffix are the baseline. `-v2.drawio` files are superseded. | one source per domain | the `-v2` files move to `archive/` |
| D-07 | No domain keeps a copy of the store or the menu. Order checks the store live with `ResolveStore` at `PlaceOrder` and no longer consumes `store.changed`. | the store and menu are online and real-time; one owner, no stale copy | checkout fails if Brand & Store is down; it is Order's third sync dependency |
| D-08 | A price change from the BSL feed reaches shoppers at the next menu publish, not immediately. | shoppers and aggregators see one consistent, approved price per version | a POS price change waits for a publish |
| D-09 | A wallet spend goes through Payment. Payment calls Wallet (`Hold`, `Capture`, `Release`, `Refund`) the way it calls Omise. That call is the second hop, the same slot as the gateway, so the two-hop rule holds. | the domain that owns the outcome runs the saga (D-02) | a wallet checkout fails when Wallet is down |
| D-10 | The stored-value ledger lives only in Wallet. Payment's transactions table is real money, and reconciling it excludes `provider=wallet`. | one owner per piece of state | finance reconciles two ledgers |
| D-11 | One wallet per `(brand_id, customer_id)`, unique, and it does not reference the loyalty profile. Loyalty is also one profile per `(brand_id, customer_id)`. One customer account across brands means many wallets and many loyalty profiles. **Confirmed 2026-10-24** by the owner: the loyalty profile and the e-wallet stay separate per brand because of marketing conditions. | brands are rows, and a balance does not cross brands | no transfer between brands; the 2029 concept asks for one balance and one points level across brands, which is now a deferred, later option (O-19, O-20) |

### Proposed — the default until signed off

Development starts on these. Change them here before code depends on something else.

| Id | Decision | Section | Cost |
| --- | --- | --- | --- |
| P-01 | `idempotency_key` on retryable mutating gRPC; required on `PlaceOrder`, `CreateTransaction`, and `Refund` | [§4](#grpc-contract) | one unique column per write table |
| P-02 | Deadline on every call, passed on; retries only on `UNAVAILABLE`, at most twice | [§4](#grpc-contract) | budgets wait on O-02 |
| P-03 | One gRPC-to-HTTP error mapping at the BFFs | [§4](#grpc-contract) | none |
| P-04 | `proto/` tree with `mfg.<domain>.v1`, `buf breaking` in CI; the same Protobuf for gRPC and Kafka | [§4](#grpc-contract) | a CI gate on every contract change |
| P-05 | One active outbox relay per domain behind an advisory lock; published rows purged after 7 days | [§5](#producer-the-outbox) | single-relay throughput ceiling |
| P-06 | Facts dedupe on `version`, commands on `event_id` in `processed_event`; offsets committed after Postgres | [§5](#consumer-apply-then-ack) | one extra table per consuming domain |
| P-07 | `cron` mode is a Kubernetes CronJob, `Forbid`, in `Asia/Bangkok` | [§9](#9-runtime-shape) | a pod start per run, even every minute |
| P-08 | One Aurora cluster per environment, one schema and role per domain; Order and Payment move to their own cluster when load needs it | [§6](#6-state-and-data-rules) | a shared blast radius until they move |
| P-09 | `placed` means the kitchen may see it: after `authorized` for own-app orders, at create for aggregator orders | [§7](#reference-flow-own-app-checkout) | Notification never sees an unpaid order |
| P-10 | Order's sweeper cron closes unpaid checkouts and unanswered POS tickets, then voids | [§7](#7-sagas-and-long-running-flows) | timeouts are only as precise as the cron interval |
| P-11 | The data-lake sink is Confluent Cloud's managed S3 sink connector | [§6](#6-state-and-data-rules) | a managed connector to pay for, but no Connect cluster to run |
| P-12 | Money as integer minor units; timestamps as UTC `timestamptz`; expand-then-contract migrations | [§6](#6-state-and-data-rules) | none |
| P-13 | LLD is one `<domain>-lld.drawio` per domain, one page per entry point. Nine drafts exist. Identity covers six flows and publishes nothing; six others cover five core flows; Wallet covers every entry point (seven pages) plus the end-to-end spend (page 8); Delivery covers every entry point (fourteen pages) plus the end-to-end delivery (page 15) and the payout reconcile (page 16). The page counts as drawn are in [§14](#14-known-drift) | [§11](#11-diagram-standard) | none |
| P-14 | Wallet has no hold timer. Payment's capture or void closes every hold, and Order's sweeper drives the void (P-10). The nightly reconciliation flags a hold still open after 24 hours | Wallet HLD | a hold Payment never closes waits for CSC to ask Payment for a void |
| P-15 | An admin adjust needs the `wallet.adjust` grant, a reason code, and an amount at or under that grant's limit. The audit row is in the same transaction. No maker-checker and no wallet freeze in v1 | Wallet HLD | one CSC agent can act alone up to the limit; a suspect wallet is handled with a debit, not a freeze |
| P-16 | One tender per order. No split between wallet and card. A short balance returns `FAILED_PRECONDITION` and the app offers a card | Wallet HLD | a short balance means the whole order is paid by card |
| P-17 | A wallet top-up is captured at authorize. It cannot be refunded to the card in v1. A correction is an admin debit (`Adjust`) | Wallet HLD | a mistaken top-up needs CSC, not a gateway refund |
| P-18 | Fleet providers sit behind one `FleetProvider` port. A ZEEK account (pool, MFG, ZEEKAGG) is a config row, and Grab Express is the second package. `partner-adapter` checks the signature, maps the payload to one canonical update, and publishes `delivery.requested` | Delivery HLD | provider knowledge lives in two small places: a Go package and a Bun mapper |
| P-19 | Each store has an ordered provider list, falling back to the brand default. The next provider is tried when create fails or the no-rider wait expires. When the list is exhausted the delivery is `failed`. No external fleet-priority service and no time-of-day schedule | Delivery HLD | a bad first provider costs one timeout; a store cannot vary its list by hour |
| P-20 | A delivery has seven states: `pending`, `dispatching`, `assigned`, `picked_up`, then `delivered`, `failed`, or `cancelled`. An update applies only when its rank is higher. `delivered` and `cancelled` never change. Provider sub-steps are timestamps on the status log | Delivery HLD | the timeline keeps the detail the seven states drop |
| P-21 | Dispatch starts on `order.events{accepted}`. A scheduled order waits in `pending` until the dispatch cron | Delivery HLD | an order is not dispatched before the kitchen accepts it |
| P-22 | Delivery owns the quote. `PlaceOrder` carries `quote_id`, and Order calls `GetQuote` live | Delivery HLD | Order gains a fourth sync dependency |
| P-23 | Riders, rosters, and earnings (with their payout status) use the reserved group tenant `brand_id = mfg`. A delivery stays on the order's brand | Delivery HLD | an explicit exception to principle 6, because one rider pool serves every brand |
| P-24 | No rider or customer contact on the bus. A ZEEK rider comes from the registry. A Grab rider is read with `GetRider` at assignment. The customer address is read from Identity when the job is created | Delivery HLD | a dispatch waits when Identity or the provider is down |
| P-25 | A rider payout is `payment.requested{payout}`, written in the same commit as `delivered`. One payout per delivery. Payment calls TrueMoney and publishes `payment.events{paid_out}` or `{payout_failed}`. The payout status lives on the trip's earnings row; there is no payouts table, and an earnings amount is never edited. The workforce cron reconciles; it does not send money | Delivery HLD | a payout waits on Payment; a failed trip is flagged, not paid again by the cron |
| P-26 | FAAS is the same Quote and CreateDelivery, called from `partner-bff`. Brand callbacks go out through `partner-adapter` on `delivery.events`. Payment Statement invoices the brand | Delivery HLD | an external brand waits on the same gRPC budget as a shopper |
| P-27 | Ops and finance reports are the data-lake sink, plus an admin export worker that writes a file to S3. No report app reads Delivery's database | Delivery HLD | a report is as fresh as the sink, not a live query |
| P-28 | No Zendesk webhook and no automatic ticket. CSC records a ticket reference on an earnings adjustment | Delivery HLD | a claim is a manual adjust, not an automatic ticket |
| P-29 | Quote does not call the fleet provider. Distance is straight-line, then Google road distance above a threshold. ETA is distance over a configured speed | Delivery HLD | the ETA is approximate until `rider_assigned` |
| P-30 | An admin principal and an admin session have no `brand_id`. The grant carries `brand_id` (or `*` for a platform role). A partner client carries `brand_ids[]` | Admin HLD | one person can hold grants on many brands; the principal is not stored per brand |
| P-31 | The cart lives in Cart & Order's Postgres: one open cart per `(brand_id, customer_id)`, lines only, no stored price. `GetCart` and `UpdateCart` price it live with `PriceLines`. `UpdateCart` replaces the whole cart and checks `version`. A guest cart stays on the device. No cart topic and no expiry | Cart & Order HLD | every cart view is a Catalog call; an abandoned cart stays until the next checkout |
| P-32 | `PlaceOrder` checks out the cart with `cart_version` and `expected_total_satang`, not lines. A different live total is `FAILED_PRECONDITION` (`price_changed`). One `pending_payment` order per brand and customer: a new key cancels the old one and voids its hold. The cart is deleted when its order is placed | Cart & Order HLD | a price change between the cart and Pay sends the shopper back to the cart |
| P-33 | Minor ID is the Identity customer account, already one account across brands (D-11). Sharing a profile across brands is a PDPA consent purpose that Identity owns. The customer opts in and can withdraw at any time. Without that consent, a brand sees only its own rows | [`platform-concept.md`](platform-concept.md) step 1 | every cross-brand read checks consent at Identity |
| P-34 | AI ordering owns no menu, price, stock, or cart. It reads with the existing gRPC (`GetMenu`, availability, `PriceLines`, order history) and writes only through `UpdateCart`, so manual and AI orders share one cart and one price | [`platform-concept.md`](platform-concept.md) step 5 | each answer costs several live calls; its home and vendor wait on O-24 |
| P-35 | The 2029 concept adds no Kafka topic by itself. Each feature uses gRPC or an existing topic until a named consumer needs a new one (principle 1) | [`kafka-topics.md`](kafka-topics.md#2029-concept--no-new-topics-yet) | none |
| P-36 | **Multi-vendor POS adapter port in OMS.** Cart & Order talks to a POS through one `PosGateway` port with one Go adapter per vendor, picked per store from `pos_connection` data. Inbound, `partner-adapter` runs a Bun mapper per vendor and publishes one canonical `PosUpdate` on `order.requested{pos_status}`. Updates apply by rank and version: duplicates and lower ranks are dropped, terminal states never change, and a POS update never writes the order's price lines. A reconciliation cron finds a POS that disagrees with the priced order. Capability flags (`supports_delivery`, `supports_promotions_passthrough`, and others) are data. BSL is the first adapter and its behavior is covered by generic rules, not hardcoded. **Flag:** this reverses the [§10](#10-simplicity-guardrails) guardrail "Several POS proxies from day one". | [`design/pos-adapters.md`](design/pos-adapters.md) | the port, registry, and flags exist before a second vendor does; each vendor costs a Go package plus a Bun mapper; the BSL proxy stays as the BSL adapter's transport |
| P-37 | **Per-brand configuration and capability model.** Brands stay rows (principle 6). Each domain owns its own per-brand and per-store settings, keyed by `brand_id` (and `store_id`), written through `admin-bff`, versioned and audited. Brand & Store owns only brand feature switches and the onboarding state. A shopper action is allowed when vendor capability AND brand feature AND store setup all say yes. An unset setting is off. A new brand needs code only for a new kind of outside system (a POS vendor, a payment provider, an aggregator, a channel). A readiness check reads each owner before the live flag turns on | [`design/brand-configuration.md`](design/brand-configuration.md) | no central config service means the readiness check reads many owners; who owns brand configuration as a whole is open (O-27) |
| P-38 | **MongoDB order payload log.** A parallel, append-only log in MongoDB (Atlas on AWS, to confirm with DevOps) of every raw and converted request, response, and later webhook update, linked to the Postgres order by `order_id`, `correlation_id` (the trace id), and `external_ref`. It is owned by Cart & Order, never the truth, never read on the shopper path. Payloads are masked and tokenized before insert, expire by TTL, and are written by an async writer from adapter-level capture, best effort: a log failure never fails an order. No topic carries payloads. **Flags:** a second database engine (§6, written reason inside) against principle 1; several writers against principle 3, limited to insert-only through one shared library and one role. Revisit if Postgres JSONB proves simpler | [`design/order-payload-log.md`](design/order-payload-log.md) | a second engine to run, gaps in the trace after a crash or an outage, and a two-step lookup by id; completeness is open (O-30) |
| P-39 | **Legacy bridge.** Legacy systems sit behind the same domain port as native code, as an anti-corruption adapter (`adapters/out/legacy/<system>`), moved to native by a strangler route per capability and per brand: `legacy`, `shadow`, `canary`, `native`. One source of truth per capability and brand at any moment. The bridge publishes legacy changes as the domain's normal facts on existing topics. Old clients use compat routes inside the existing BFFs. **Flag:** while a capability is on legacy, the old system holds that state, which strains principle 3; the route table names the owner and two live writers are never allowed | [`design/legacy-bridge.md`](design/legacy-bridge.md) | code that is later deleted, a rollback rule per capability, and a bridge worker per legacy system. Related to O-18 |
| P-40 | **Minor ID enabled or disabled per brand, with a shared profile.** One Minor ID works across all brands (extends P-33). Each `(customer_id, brand_id)` membership is `enabled` or `disabled`; a customer may stay in one brand. The customer token is issued for one brand and only for an enabled membership. The profile is shared across brands with PDPA consent, with `origin_brand_id` on each row; without consent a brand sees its own rows. Loyalty and wallet stay per brand (D-11, confirmed 2026-10-24) | [`design/identity-model.md`](design/identity-model.md) | a disable takes effect at the next token refresh (up to 5 minutes); every cross-brand read checks consent at Identity; what happens to a balance when a brand is disabled is open (O-33) |
| P-41 | **Tech stack for the draft.** Core domains are Go with a hexagonal structure (ports and adapters), mapped onto the modes `api`, `consumer`, `worker`, and `cron`. The edge is Bun and Elysia v2, REST only, with stable OpenAPI contracts and AI-ready rules (idempotent operations, scoped tokens, audit). Infrastructure is run by DevOps on AWS as much as possible; new tools may be non-AWS if clearly better. Names of domains, protos, topics, and the tenant `mfg` do not change. **Align with the owner's boilerplates when shared** | [`design/tech-stack.md`](design/tech-stack.md), [§9](#9-runtime-shape) | Elysia 2 is a release candidate, so a version pin and a re-check at the final release are needed (O-34) |
| P-42 | **Kafka topic growth policy.** Keep topics minimal in the first draft. Twelve is considered low, and more may be added when each passes the three-answers rule (producer, consumer, why gRPC or an existing topic does not cover it). Candidates not yet registered are listed, with the trigger that would promote each. No topic was added in v3 | [`kafka-topics.md`](kafka-topics.md#growth-policy) | a candidate waits until it has a named consumer; some later work may need a topic sooner |
| P-43 | **Scale and uptime numbers are recommendations, not facts.** The sizing tiers, load figures, latency and availability targets, RPO and RTO, and partition counts in the scale file are assumptions that the owner will rewrite. They give the design a shape to size against until O-01 to O-03 are answered | [`design/scale-assumptions.md`](design/scale-assumptions.md) | decisions that depend on a number (partition counts, Aurora split) wait for the business answer |
| P-44 | **Postpaid table ordering is one tab in Cart & Order.** A QR table order is an order with `order_type = dine_in_postpaid` and many rounds, each round fired to the POS at once. Cart & Order owns and writes the table session, the tab, the rounds, and the bill. Alternatives not taken: Brand & Store owning the session, a new Dining domain, and the Delivery domain | [`design/postpaid-table-ordering.md`](design/postpaid-table-ordering.md#2-where-it-lives) | the Order aggregate grows from one ticket to a tab with many tickets; a Dining domain stays an option if dine-in grows |
| P-45 | **Tables, QR, and guest access.** Brand & Store owns the table registry and QR key versions. The QR is signed and holds no personal data. A session starts through `guest-bff` or `customer-bff`. A guest uses a guest token: a customer-family JWT with scope `dine_in`, issued by Identity (`IssueGuestToken`, callable by `guest-bff` only). Guard levels G1 (always) to G4 are a per-store setting, G2 (table code) proposed as the default. **Flags:** extends the `guest-bff` scope and the meaning of the customer token family; the text of §8 is unchanged until this is signed off | [`design/postpaid-table-ordering.md`](design/postpaid-table-ordering.md#4-table-qr-and-session) | a guest token is a token with no customer behind it; a table code adds a little staff effort; the guard level waits on O-39 |
| P-46 | **Tab and round lifecycle.** Tab states: `open`, `active`, `bill_requested`, `payment_pending`, `paid`, `closed`, `cancelled`, `abandoned_unpaid`. Round states follow the POS ranks (`fired` to `served`, plus `rejected` and `voided`). `placed` happens when the first round commits, with no payment (this extends P-09). `completed` is the close. "Served" is derived. "Deliver to table" is table service shown from POS and staff signals, and does not use the Delivery domain | [`design/postpaid-table-ordering.md`](design/postpaid-table-ordering.md#5-lifecycle-tab-rounds-and-deliver-to-table) | P-09's cost "Notification never sees an unpaid order" no longer holds for postpaid; a POS that never says served needs a staff tap (O-48) |
| P-47 | **Pay at the end.** The bill is built from the lines agreed at each round and never from POS totals. Payment charges it with `purpose = table_bill`, captured at authorize (as P-17). The money moves first, then Order closes the POS check. The voucher hold is made at pay time and committed on `completed`. The first draft pays the whole bill. Equal split is next, by item later. **Flag:** several payments on one order read as one tender per payment (P-16) | [`design/postpaid-table-ordering.md`](design/postpaid-table-ordering.md#7-payment-at-the-end) | no cover against a walk-out unless P-48 is on; a paid tab whose check cannot be closed waits for staff; the split scope waits on O-40 |
| P-48 | **Optional card hold.** A brand may require a `table_preauth` card hold at the first round, up to `max_open_amount`, released or partly captured at close. Cards only. It needs gateway support | [`design/postpaid-table-ordering.md`](design/postpaid-table-ordering.md#how-payment-handles-a-pay-later-transaction) | a partial capture on a hold is new for Payment; the hold shows on the card statement; legal wording and gateway settings are open (O-38, O-43) |
| P-49 | **POS port for open checks.** `PosGateway` gains `OpenCheck`, `AddItems`, `GetCheck`, `ApplyPayment`, `CloseCheck`, and `TransferTable`, with flags `supports_dine_in`, `supports_open_check`, `supports_add_items`, `supports_get_check`, `supports_external_payment`, `supports_table_transfer`, and `supports_check_webhooks`. Adapters degrade to `ticket_per_round` or `staff_settle` per store. The new flags are unknown for BSL and treated as false until the vendor confirms | [`design/pos-adapters.md`](design/pos-adapters.md#14-open-checks-and-table-service-proposal-p-49) | each vendor needs a capability answer before the clean mode works (O-42); the fallback modes leave payment or closing to staff |
| P-50 | **Counter settlement and staff control.** A POS update that shows the check paid or closed closes the tab (`settlement = counter`). Staff can mark a round served, void a round, move a tab, force-close a tab, or flag a walk-out from the admin console, with new grants (`table.manage`, `tab.view`, `tab.serve`, `tab.manage`, `tab.override`), a reason, and an audit row. No timer closes a tab as paid or unpaid | [`design/postpaid-table-ordering.md`](design/postpaid-table-ordering.md#pay-at-the-counter-fallback) | staff time per walk-out; an app payment and a counter settlement can collide and need a CSC refund |
| P-51 | **No new topic for postpaid.** `order.events` gains one variant, `round_updated`. `payment` records carry a `purpose`. The POS status variant carries round and check references. The payload log records the postpaid POS traffic. `PlaceRound`, `PayBill`, `ForceCloseTab`, and `MarkTabUnpaid` take an `idempotency_key` (extends P-01). Voucher commits a postpaid hold on `completed` | [`design/postpaid-table-ordering.md`](design/postpaid-table-ordering.md#kafka-no-new-topic), [`kafka-topics.md`](kafka-topics.md) | a change to Voucher's consumer; `order.events` volume rises, see P-52 |
| P-52 | **Dine-in numbers are recommended assumptions.** Time limits, caps, defaults, and the load figures are examples for the owner to rewrite, the same status as P-43 | [`design/postpaid-table-ordering.md`](design/postpaid-table-ordering.md#11-scale-assumptions-recommended-to-be-rewritten) | the poll load and the `order.events` partition count depend on them (O-01, O-46) |

### Open — needs a business answer

| Id | Question | Blocks |
| --- | --- | --- |
| O-01 | Peak orders per minute at the lunch peak, per brand and in total. **Still open.** [`design/scale-assumptions.md`](design/scale-assumptions.md) gives a recommended shape with example values, all assumptions | partition counts, Aurora sizing, P-08 |
| O-02 | Availability and p99 latency target for `PlaceOrder` and `GetMenu`. **Still open.** Example targets and a deadline budget are in [`design/scale-assumptions.md`](design/scale-assumptions.md) | deadline budgets (P-02), replica counts |
| O-03 | RPO and RTO; multi-AZ only, or a second region. **Still open.** Example targets per tier are in [`design/scale-assumptions.md`](design/scale-assumptions.md) | Aurora and Kafka setup, the DR runbook |
| O-04 | The payment window (abandoned 3DS or QR) and the POS answer window | the sweeper (P-10) |
| O-05 | If capture fails after the kitchen accepted, is the order kept, retried, or sent to CSC? | the Order and Payment LLDs |
| O-06 | Answered for sharing: one customer account is shared across brands (D-11). Still open: how Kong sets `X-Brand-Id` when that customer uses more than one brand. A proposal (brand from the brand app, brand-scoped token) is in [`design/identity-model.md`](design/identity-model.md) | the Identity HLD |
| O-07 | Retention under PDPA for the message log, audit, and order history | partitioning and purge crons |
| O-09 | Which partners call `partner-bff` with a token, rather than integrating through `partner-adapter` webhooks? | the partner API scope |
| O-10 | Balance cap, top-up minimum and maximum, whether stored value expires, and which BOT e-money rules apply | Wallet limits, the top-up and Adjust flows |
| O-11 | Is the tax invoice issued when the wallet is topped up, or when the balance is spent? | Payment Statement mode, the Wallet top-up |
| O-12 | What amount limit sits on the `wallet.adjust` grant? | the Adjust flow (P-15) |
| O-13 | No-rider timeout per provider, the maximum number of attempts, and how long before the due time a scheduled order is dispatched | the dispatch sweeper and the scheduled-order cron (P-19, P-21) |
| O-14 | When every provider fails, does the order auto-cancel and refund, or wait for CSC? | Order's reaction to `delivery.events{failed}` |
| O-15 | Quote time-to-live, the maximum distance, the road-distance threshold, and the fee scheme per brand | Quote and `GetQuote` (P-22) |
| O-16 | The TrueMoney merchant account for a rider payout; whether hourly and incentive pay exist and who writes them; when an adjust is paid; the reconcile window | the payout on `delivered` (P-25) |
| O-17 | How long rider documents are kept under PDPA | the rider registry and the purge cron |
| O-18 | How the cutover from Fleet Management, FAAS, and Driver Management runs, and whether it is per brand. Related: the SDM to BSL move of `mfg-tpc-api`. [`design/legacy-bridge.md`](design/legacy-bridge.md) allows a per-capability, per-brand cutover; the plan is not written (see O-31) | the migration plan, not the shape of the domain |
| O-19 | **Deferred, a later option (owner, 2026-10-24: wallet stays per brand, D-11).** Does one Minor Wallet balance work in every brand, as the 2029 concept shows? If it does, D-11 changes to a group wallet (perhaps the `mfg` tenant, as P-23 does for riders), and BOT e-money rules apply to the group (O-10) | a Wallet HLD v2, auto top-up, top-up bonus |
| O-20 | **Deferred, a later option (owner, 2026-10-24: loyalty stays per brand, D-11).** Do points and member level work across brands? If so, who funds points earned in one brand and spent in another? | the Loyalty HLD, member price on the menu |
| O-21 | Where do member price and deal stacking run (Catalog price book, Campaign, or Cart), and who sets the margin floor per campaign? | the Voucher & Campaign HLD, the cart pricing path (P-31) |
| O-22 | More than one payment partner per brand, with routing by fee and success rate and failover to the next partner? This reverses the "one provider per brand" guardrail ([§10](#10-simplicity-guardrails)) | the Payment provider port, PromptPay QR in app |
| O-23 | Pay Later: which licensed lending partner, and is it a tender behind Payment, the way the wallet is (D-09)? | Payment, the pay screen |
| O-24 | AI ordering: which model and vendor, which component hosts it, and which data it may read under PDPA consent | an AI HLD, P-34 |
| O-25 | Does personalization (time, weather, habits) need real-time customer features beyond the data-lake sink (P-11)? | the Data platform design, the personal home page |
| O-26 | When a franchised brand joins Minor ID, what customer data does the franchisor see? | the Identity HLD, P-33 |
| O-27 | Who owns brand configuration as a whole, who approves a change, and is there a maker-checker step for risky settings (a POS vendor change, a payment key)? | the brand configuration model (P-37), the readiness check |
| O-28 | POS vendor contract limits and the real capability matrix per vendor: rate limits, webhook guarantees (retry, signature, ordering), versioning, delivery support dates. The BSL values in the POS file are assumptions from the owner's testing | the POS adapter flags and rules (P-36) |
| O-29 | MongoDB Atlas hosting: AWS region, private connectivity, backup, encryption keys, and DevOps ownership | the payload log (P-38) |
| O-30 | Is the payload log a debugging aid or an audit record? That decides completeness (async best effort or a Postgres capture row), retention, the right to delete under PDPA, and whether several insert-only writers are acceptable | P-38, the write path, the retention value (with O-07) |
| O-31 | Which capabilities run on legacy, per brand, in what order they cut over, and the rollback rule for each | the legacy bridge (P-39), the migration plan with O-18 |
| O-32 | When the POS disagrees with the order Order priced (a dropped promotion, a wrong total), what is the rule: keep the shopper's price, adjust, or send to CSC? | the reconciliation action (P-36) |
| O-33 | Minor ID: the default consent state and when it is asked; which fields are the sign-in minimum; what happens to a wallet balance, points, and notifications when a membership is disabled; how a delete works across brands | the Identity HLD, P-40 |
| O-34 | Elysia 2: the final release date, the exact version to pin, and whether the HTTP error body stays our `{ code, message, trace_id }` or moves to RFC 9457 problem details | the edge apps (P-41) |
| O-35 | AI assistant identity: does it act as the customer with a scoped token, or as a service principal, and which operations are allowed? | the AI-ready edge (P-41), with O-24 |
| O-36 | How Kafka topics, schemas, and ACLs are created: by DevOps from the registry, or by us? | the topic growth policy (P-42) |
| O-37 | Postpaid: which brands and stores, and which formats (full table service only, or also order-at-counter with a table number)? Which store is the pilot? | the scope and the guard defaults (P-44, P-45) |
| O-38 | Postpaid: the walk-out policy. Is a card hold required, who bears an unpaid loss, may a signed-in member be blocked, and what wording may be shown when a hold can be captured? | P-48, `max_open_amount` |
| O-39 | Postpaid: which QR guard level, and how much staff effort at seating is acceptable (a table code, a staff confirm)? | the `qr_guard` default (P-45) |
| O-40 | Postpaid: which split bill is needed (equal, by item, by person, custom), in which release, and is several payments on one order accepted next to P-16? | the split model (P-47) |
| O-41 | Postpaid: service charge, tip, VAT display, and the tax invoice for a guest, per brand, with finance and legal confirmation, and e-tax | the bill and Statement mode (P-47) |
| O-42 | Postpaid: the real open-check capability of each POS vendor (BSL, Promise, VIVI): open check, add items, outside payment, table transfer, check webhooks, table reference. Extends O-28. Also whether any brand feeds its kitchen from outside the POS | the flags and degrade mode per vendor (P-49) |
| O-43 | Postpaid: the gateway's card hold and partial capture on MFG's merchant accounts, the hold time limit, fees, a hold amount increase, and PromptPay QR for a tab | P-48 |
| O-44 | Postpaid: how staff learn of a bill request or a call for help (the admin board only, a POS-side alert, or a staff recipient type in Notification), and on which devices | the table board, Notification |
| O-45 | Postpaid: who earns points when several diners share a tab, may a voucher be used after rounds were sent, may points be spent, and may POS-added lines be billed? | Loyalty and Voucher behavior, the bill (P-47) |
| O-46 | Postpaid: idle and maximum session time, the payment window, the caps, the tip margin, and polling versus push | P-52, the tab sweeper |
| O-47 | Postpaid: a guest receipt on screen only or by email (which needs a Notification call that keeps no address), taxpayer details, and how long guest tab records are kept (PDPA, with O-07) | Statement mode, retention |
| O-48 | Postpaid: who confirms "served", how a "never arrived" dispute and a bill dispute are settled, and the table move and merge rules | the served signal and staff tools (P-46, P-50) |

---

## 14. Known drift

These diagrams disagree with this file. Fix the diagram, then delete the row.

### Open: diagrams the v3 text has moved ahead of

The text of v3 is ahead of these diagrams. The `.drawio` files were not edited in the v3 pass. A domain starts coding only when its rows are closed ([§12](#ready-for-development)).

| File | What is wrong | Fix |
| --- | --- | --- |
| `domains/cart-and-order/cart-order-hld.drawio` | Shows the BSL proxy only. No POS adapter port, no registry, no Mongo box in the Data lane, no written reason for the second engine in Decisions | Redraw the POS worker as the port plus vendor adapters, add the Mongo log (P-36, P-38) |
| `domains/cart-and-order/cart-order-lld.drawio` page 3 | POS dispatch and status has no rank, dedupe, or reported-total rules, and no reconcile step | Add rules R1 to R7 and the reconcile cron ([`design/pos-adapters.md`](design/pos-adapters.md)) |
| `domains/brand-and-store/brand-store-hld.drawio` | No brand feature switches or onboarding state | Add them to the engine and Decisions (P-37) |
| `domains/identity-and-customer/identity-customer-hld.drawio` and `identity-customer-lld.drawio` page 3 (`JoinBrand`) | No membership status (enabled or disabled), no brand-scoped token | Add them (P-40) |
| `domains/platform-overview/mfg-eplatform-hld.drawio` and `mfg-eplatform-overview.drawio` | Title says MFG ePlatform. No MongoDB box. Partner adapter lane says BSL only | Rename to NEXA, add MongoDB, name POS vendors (P-36, P-38) |
| `domains/cart-and-order/cart-order-hld-script.md` | The presenter script says "BSL only" and "Promise and VIVI wait" | Marked as a v2 script at the top. Rewrite it after the HLD is redrawn |
| `domains/cart-and-order/cart-order-hld.drawio` and `cart-order-lld.drawio` (added 2026-10-25) | No table session, postpaid tab, rounds, bill, or open-check POS calls | Add them with the POS port work above (P-44, P-49). A first view is in [`diagrams/13-postpaid-table-ordering.drawio`](../diagrams/13-postpaid-table-ordering.drawio) |
| `domains/brand-and-store/brand-store-hld.drawio`, `domains/payment-and-billing/payment-billing-hld.drawio`, `domains/identity-and-customer/identity-customer-hld.drawio` (added 2026-10-25) | No table registry and QR keys; no `table_bill` or `table_preauth` purpose; no guest token | Add them (P-45, P-47, P-48) |

### Fixed in the v3 pass

| File | What was wrong | Fix |
| --- | --- | --- |
| `README.md` | Linked the 2029 demo and the references folder under a name that did not match the real folder | Rewritten. The folder is now `references/` (details in [`CHANGELOG.md`](CHANGELOG.md)) |
| `platform-concept.md` | Linked `Bonchon_App_2029_Concept_Demo.html`, but the file is `2029_Concept_Demo.html` | Link points at `references/2029_Concept_Demo.html` |
| This file, `overview-guideline.md`, and the domain descriptions | Referred to `SHLD-guideline.md`, `mfg-eplatform-shld.drawio`, and one `*-shld.drawio` per domain. None of those files is in the repo | Dangling links removed. Each name is marked "not yet drawn". No file was invented |
| This file, §12 | Linked `#topics-and-hld-status`, but the heading is "Topics and diagram status" | Anchor fixed |
| Delivery description and this file | The description said 16 LLD pages. This file said 14 plus page 15 | The file has 16 pages (14 entry points, 15 end to end, 16 payout reconcile). Text fixed in P-13 and §3 |

LLD page counts as they are drawn in the `.drawio` files (counted from the `<diagram` elements on 2026-10-24):

| Domain | HLD pages | LLD pages | Note |
| --- | --- | --- | --- |
| Identity & Profile | 1 | 6 | |
| Admin & Partner | 1 | 5 | |
| Brand & Store | 1 | 5 | |
| Catalog & Menu | 2 | 6 | The HLD file has a second page named "Page-2". The rulebook says one page per domain. Check what it holds |
| Cart & Order | 1 | 7 | |
| Payment & Billing | 1 | 6 | |
| Delivery & Dispatch | 1 | 16 | |
| Loyalty & MemberCard | 1 | 6 | |
| Voucher & Campaign | 1 | 7 | |
| Wallet | 1 | 8 | |
| Notification | 1 | 17 | |
| Platform | 1 | none | no platform LLD |

Add a row to the open table when a diagram next disagrees with this file.

---

## 15. Glossary

| Term | Meaning |
| --- | --- |
| NEXA | Next generation experience architecture. The name of this platform. Former name: MFG ePlatform. |
| Minor ID | The one customer account across all Minor Food brands (P-33). It can be enabled or disabled per brand (P-40). See [`platform-concept.md`](platform-concept.md) and [`design/identity-model.md`](design/identity-model.md). |
| OMS | Order Management System. In this repo, the Cart & Order domain. |
| POS adapter | The Go adapter behind the `PosGateway` port that talks to one POS vendor, plus its Bun mapper at the edge (P-36). |
| Capability flag | Data that says what a vendor or provider can do, for example `supports_delivery`. Effective capability is the AND of vendor, brand feature, and store setup. |
| Payload log | The parallel MongoDB log of raw and converted order payloads (P-38). Not a source of truth. |
| Legacy bridge | An anti-corruption adapter that puts a legacy system behind a domain port, moved to native one capability and one brand at a time (P-39). |
| Hexagonal | Ports and adapters. The domain core knows no transport, database, or vendor. |
| Table session | The period one party of diners uses one table, started by scanning the table QR. One open session per table (P-44). |
| Tab | The order of a table session (`order_type = dine_in_postpaid`). It stays open until it is paid and closed. The "open check" on the POS side. |
| Round | One "send to kitchen" action in a tab, fired to the POS at once (P-44). |
| Building block | One of the 8 shared capabilities in the 2029 concept. A block maps to one or more domains. |
| Command | A request to one domain to change its state. Lives on `<domain>.requested`. The sender does not wait. |
| Fact | Something that already happened and was committed. Lives on `.changed`, `.published`, or `.events`. |
| Ack | The consumer commits its Kafka offset after its own Postgres commit. |
| Outbox | A table written in the same transaction as the state. A relay publishes from it. |
| Projection | A local, rebuildable copy of another domain's fact, holding only the fields this domain needs. The exception, never the default (D-07). |
| Menu version | The published, unchangeable state of a menu. Not an offline copy. |
| Price lines | The prices an order was placed at, stored on the order as its record. |
| BFF | Backend for frontend. A Bun app that one kind of client calls over HTTPS; it calls domains over gRPC. |
| Adapter | A Bun app at the edge that turns a signed third-party webhook into a command, or a fact into a third-party push. |
| Idempotency key | A client-chosen id on a mutating gRPC call. A repeat with the same key returns the first result. |
| Deadline | The time by which a gRPC call must finish, passed down every hop. |
| Sweeper | A cron that closes saga steps that never got an answer. |
| PEP | Policy enforcement point. For us, only Kong. |
| Saga | A multi-step flow across domains, run by the domain that owns the outcome. |
| `ponytail:` | A note marking a deliberate simplification, its limit, and the upgrade path. |
