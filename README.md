# MFG ePlatform

[![Documentation](https://img.shields.io/badge/docs-draw.io%20%2B%20markdown-blue.svg)](https://www.diagrams.net/)

Design record for the Minor Food multi-brand platform. One shared stack serves
every brand as a row (`brand_id`). Domains are Go. BFFs and adapters are
Bun/Elysia. Confluent Kafka carries work that nobody is waiting on. This
repository holds the rulebook, the topic registry, and the draw.io diagrams.
Service code lives in the mono-repo.

<!-- ai:anchor:overview -->
## Overview

[`architecture.md`](architecture.md) is the rulebook (baseline v2, 2026-10-05).
It wins when a diagram, a presenter script, or the 2029 concept disagrees
with it. [`kafka-topics.md`](kafka-topics.md) is the complete list of topics.

[`platform-concept.md`](platform-concept.md) is the 2029 direction: one Minor
ID, one wallet and points balance across brands, AI ordering, and payment
routing. Accepted decisions in the rulebook stay in force until the decision
register changes them.

### Architecture

```text
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

The master map is
[`overview-diagrams/mfg-eplatform-hld.drawio`](overview-diagrams/mfg-eplatform-hld.drawio).
Domain HLDs zoom into one box on that map. The system overview for a technical
reader is
[`overview-diagrams/mfg-eplatform-overview.drawio`](overview-diagrams/mfg-eplatform-overview.drawio).

### Flow Summary

A shopper request stays synchronous. Kafka starts only after the answer has already been given.

1. The app, guest, admin console, partner, aggregator, POS, or gateway hits
   Cloudflare, then Kong. Kong is the only place a request is allowed through
   or stopped. It injects the principal, roles, and brand.
2. The matching BFF or adapter calls a domain. Client to BFF is HTTPS.
   Everything behind the BFF is gRPC.
3. If someone is waiting, the call stays on gRPC. State and the outbox row
   commit in one Postgres transaction. The fact is published after that commit.
4. A consumer applies the record when `version` is newer, then Ack. A
   redelivery is a no-op.

Own-app checkout, the reference saga, is in
[`architecture.md` §7](architecture.md#reference-flow-own-app-checkout). The
shopper waits through `PlaceOrder` and the gateway hand-off. Capture or void
happens after the POS accepts or rejects the ticket.

### Reading order

1. [`architecture.md`](architecture.md) — principles, components, transports, and the decision register.
2. [`kafka-topics.md`](kafka-topics.md) — the twelve business topics, their keys, and what was removed.
3. [`overview-diagrams/description.md`](overview-diagrams/description.md) — the platform pictures.
4. The domain folder below. Each `description.md` says what the domain owns and which diagram files are current.
5. [`platform-concept.md`](platform-concept.md) — where the platform is heading,
   and where that picture still disagrees with the baseline.
6. [`overview-guideline.md`](overview-guideline.md) — before drawing a system overview page.

When those files disagree, `architecture.md` wins, then `kafka-topics.md`, then
the domain `description.md`, then the HLD.

<!-- ai:anchor:features -->
## Features

- Binding architecture baseline: eight principles, component ownership, gRPC and
  Kafka rules, and a decision register (accepted, proposed, open).
- Twelve Kafka business topics, with producers, consumers, keys, retention, and
  partition counts.
- Domain diagrams in draw.io: a system overview, an HLD, and an LLD. Presenter
  scripts sit next to the HLDs that have one.
- A 2029 platform concept and a clickable demo at
  [`refs/2029_Concept_Demo.html`](refs/2029_Concept_Demo.html).
- Diagram rules for HLD layout, LLD page strips, colors, logos, and the Ack on
  a Kafka consume.

<!-- ai:anchor:installation -->
## Installation & Setup

### Prerequisites

- A draw.io editor: [diagrams.net](https://app.diagrams.net/) in the browser, or the draw.io desktop app.
- A Markdown preview for the rulebook. Any editor preview is enough.

### Opening a diagram

1. Clone this repository.
2. Open the `.drawio` file in diagrams.net (File → Open From → Device) or in the desktop app.
3. Read the folder's `description.md` before the picture. It names which file is current. For a system overview, read `domain-overview.md` and do not open `*-overview.drawio` for the words.
4. Export a PNG with `draw.io -x -f png` only to check layout by eye. Leave the PNG uncommitted.

Files without a suffix are the baseline. Superseded `-v2` drafts live in
[`archive/`](archive/). The overview `-v2` file is still in
[`overview-diagrams/`](overview-diagrams/) and is called out as drift in
[`architecture.md` §14](architecture.md#14-known-drift).

<!-- ai:anchor:structure -->
## Project Structure

```text
.
├── architecture.md                 Rulebook. Read this first.
├── kafka-topics.md                 The only topic list.
├── platform-concept.md             2029 target picture.
├── overview-guideline.md           How to draw a system overview page.
├── overview-diagrams/              Platform overview and HLD.
├── identity-and-customer-diagrams/ Customer, login, OTP, addresses, PDPA consent.
├── admin-and-partner-diagrams/     Admin principal, grants, partner OAuth clients.
├── brand-and-store-diagrams/       Brand, store, hours, zone.
├── catalog-and-menu-diagrams/      SKUs, menu versions, sold-out, price book.
├── cart-and-order-domain-diagrams/ Cart, order, POS ticket, checkout saga.
├── payment-domain-diagrams/        Transactions, invoices, receipts.
├── delivery-and-dispatch-diagrams/ Quote, dispatch, rider, earnings ledger.
├── wallet-diagrams/                Stored-value ledger and holds. Overview reference.
├── loyalty-and-membercard-diagrams/ Points, tier, and the member card.
├── voucher-and-campaign-diagrams/  Campaigns, vouchers, member cards.
├── notification-diagrams/          Templates, inbox, and outbound channels.
├── refs/                           Source notes and the 2029 HTML demo.
└── archive/                        Pre-EDA and v2 drafts. Historical.
```

Loyalty & MemberCard is drawn from the [Loyalty target architecture](https://minordigital.atlassian.net/wiki/spaces/BackEnd/pages/3898146819/Loyalty+Domain+-+Target+Architecture). Topics follow [`kafka-topics.md`](kafka-topics.md): `order.events` in, `notification.requested` out.

| Domain | Diagrams |
| --- | --- |
| Platform | [overview-diagrams](overview-diagrams/description.md) |
| Identity & Profile | [identity-and-customer-diagrams](identity-and-customer-diagrams/description.md) |
| Admin & Partner | [admin-and-partner-diagrams](admin-and-partner-diagrams/description.md) |
| Brand & Store | [brand-and-store-diagrams](brand-and-store-diagrams/description.md) |
| Catalog & Menu | [catalog-and-menu-diagrams](catalog-and-menu-diagrams/description.md) |
| Cart & Order | [cart-and-order-domain-diagrams](cart-and-order-domain-diagrams/description.md) |
| Payment & Billing | [payment-domain-diagrams](payment-domain-diagrams/description.md) |
| Delivery & Dispatch | [delivery-and-dispatch-diagrams](delivery-and-dispatch-diagrams/description.md) |
| Wallet | [wallet-diagrams](wallet-diagrams/description.md) |
| Loyalty & MemberCard | [loyalty-and-membercard-diagrams](loyalty-and-membercard-diagrams/description.md) |
| Voucher & Campaign | [voucher-and-campaign-diagrams](voucher-and-campaign-diagrams/description.md) |
| Notification | [notification-diagrams](notification-diagrams/description.md) |

<!-- ai:anchor:infrastructure -->
## Infrastructure / Integrations

The pictures name these contracts. The rules for each one are in [`architecture.md`](architecture.md).

| Piece | Role |
| --- | --- |
| Cloudflare | Bots, WAF, TLS |
| Kong | The only policy enforcement point. JWT routes and signed webhook routes |
| Confluent Kafka + Schema Registry | Facts and commands. Protobuf, BACKWARD compatible |
| Aurora PostgreSQL | System of record per domain, including the transactional outbox |
| Valkey | The four cache uses in the rulebook. The truth stays in Postgres |
| S3 | Files such as a campaign audience. The command carries the key |
| Vault | Signing keys |
| Azure AD | Admin identity. Only Admin & Partner calls it |
| Omise | Card and QR gateway. One account per brand |
| TrueMoney | Rider payouts, called by Payment |
| SES, SMS, LINE | Message providers. Receipts enter through `webhook-adapter` |
| Grab, LINE MAN, Shopee Food | Aggregators, behind `partner-adapter` |
| ZEEK, Grab Express | Fleet providers, behind the Delivery port |
| BSL | POS. Order talks to it through the BSL proxy |

<!-- ai:anchor:development -->
## Development

### Changing a fact

1. If the change breaks a rule, edit [`architecture.md`](architecture.md) first
   and write the reason in the decision register.
2. Add or remove a topic in [`kafka-topics.md`](kafka-topics.md) before it
   appears on a diagram. A new topic needs a producer, a consumer, and a reason
   a gRPC call or an existing topic does not already cover it.
3. Update that domain's `description.md`, then the HLD, then the LLD. An LLD
   stays inside the topics, services, and owners the HLD already shows.
4. Copy styles from the reference file for that level. Do not invent a new look.

### Reference files

| Level | Copy from |
| --- | --- |
| HLD layout | [`catalog-and-menu-diagrams/catalog-menu-hld.drawio`](catalog-and-menu-diagrams/catalog-menu-hld.drawio) |
| HLD relation lines | [`wallet-diagrams/wallet-hld.drawio`](wallet-diagrams/wallet-hld.drawio) |
| LLD page | [`cart-and-order-domain-diagrams/cart-order-lld.drawio`](cart-and-order-domain-diagrams/cart-order-lld.drawio) |
| System overview | [`wallet-diagrams/wallet-overview.drawio`](wallet-diagrams/wallet-overview.drawio), rules in [`overview-guideline.md`](overview-guideline.md) |

### Diagram checks

- A third-party box carries its logo at 30×30, 16px from the left edge, embedded in the file.
- A Kafka consume ends in a green Ack pill after the last step.
- Export a PNG and read it. A line through a box, or a label sitting on a line, fails review.
