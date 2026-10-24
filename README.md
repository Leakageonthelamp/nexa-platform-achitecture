# NEXA

[![Documentation](https://img.shields.io/badge/docs-draw.io%20%2B%20markdown-blue.svg)](https://www.diagrams.net/)

NEXA (next generation experience architecture) is the design record for the Minor Food multi-brand food-tech platform. It was called "MFG ePlatform" until baseline v2. One central platform serves every brand, and a new brand plugs in by configuration. This repository holds the rulebook, the topic registry, the design notes, and the draw.io diagrams. Service code lives in the mono-repo.

**Status: first draft, design phase (baseline v3, 2026-10-24).** It is built from best practice and is not yet refined by business requirements or brand limits. Nothing is final. Recommendations and assumptions are labelled as such.

<!-- ai:anchor:overview -->
## Overview

[`docs/architecture.md`](docs/architecture.md) is the rulebook. It wins over everything else in this repo: diagrams, presenter scripts, domain descriptions, and the 2029 concept. [`docs/kafka-topics.md`](docs/kafka-topics.md) is the complete list of Kafka topics.

The idea in short:

- **One shared stack, brands are rows.** `brand_id` is on every call, every Kafka key, and every table. There are no per-brand services, topics, or databases. What differs per brand is configuration ([`docs/design/brand-configuration.md`](docs/design/brand-configuration.md)).
- **One Minor ID** works across brands and can be enabled or disabled per brand. The profile is shared with consent. Loyalty and the e-wallet stay separate per brand ([`docs/design/identity-model.md`](docs/design/identity-model.md)).
- **The POS is the one layer we do not control.** The order system (OMS, the Cart & Order domain) talks to POS vendors through one port with an adapter per vendor ([`docs/design/pos-adapters.md`](docs/design/pos-adapters.md)).
- **Domains are Go** with a hexagonal structure. **BFFs and adapters are Bun and Elysia v2**, REST only. **Confluent Kafka** carries work that nobody is waiting on ([`docs/design/tech-stack.md`](docs/design/tech-stack.md)).
- **Postgres is the truth.** A MongoDB log keeps every raw and converted order payload beside it, best effort ([`docs/design/order-payload-log.md`](docs/design/order-payload-log.md)).
- **Some parts stay on legacy** for now, behind the same ports ([`docs/design/legacy-bridge.md`](docs/design/legacy-bridge.md)).

[`docs/platform-concept.md`](docs/platform-concept.md) is the 2029 direction. Accepted decisions in the rulebook stay in force until the decision register changes them.

### Architecture

```text
 Channels             Edge                 BFFs · adapters (Bun/Elysia v2)   Domains (Go, hexagonal)    Backbone
┌──────────────┐    ┌──────────────┐     ┌──────────────────┐          ┌────────────────────┐      ┌──────────────┐
│ Customer app │    │ Cloudflare   │     │ customer-bff     │          │ Cart & Order (OMS) │─pub─▶│ Confluent    │
│ Guest        │───▶│ WAF · TLS    │────▶│ guest-bff        │──gRPC───▶│ Catalog · Payment  │◀─sub─│ Kafka +      │
│ Admin · CSC  │    │      │       │     │ admin-bff        │          │ Brand & Store · …  │      │ Schema Reg.  │
│ Partner API  │    │      ▼       │     │ partner-bff      │          └──┬──────────┬──────┘      └──────▲───────┘
├──────────────┤    │ Kong (PEP)   │     ├──────────────────┤             │ commit   │ POS port           │
│ Aggregators  │───▶│ JWT routes   │────▶│ partner-adapter  │── command ──┼──────────┼────────────────────┘
│ POS vendors  │    │ signed hooks │     │ (vendor mappers) │             ▼          ▼
│ PSP · SES·SMS│    └──────────────┘     │ webhook-adapter  │    Aurora PostgreSQL · Valkey · S3 · Vault
│ LINE         │                         └──────────────────┘    + MongoDB payload log (order trace only)
└──────────────┘
```

The master map is [`domains/platform-overview/mfg-eplatform-hld.drawio`](domains/platform-overview/mfg-eplatform-hld.drawio) (the title inside the picture still says MFG ePlatform). Domain HLDs zoom into one box on that map. The system overview for a technical reader is [`domains/platform-overview/mfg-eplatform-overview.drawio`](domains/platform-overview/mfg-eplatform-overview.drawio). Some diagrams are behind the v3 text. The list is in [`docs/architecture.md` §14](docs/architecture.md#14-known-drift).

### Flow Summary

A shopper request stays synchronous. Kafka starts only after the answer has already been given.

1. The app, guest, admin console, partner, aggregator, POS, or gateway hits Cloudflare, then Kong. Kong is the only place a request is allowed through or stopped. It injects the principal, roles, and brand.
2. The matching BFF or adapter calls a domain. Client to BFF is HTTPS (REST). Everything behind the BFF is gRPC.
3. If someone is waiting, the call stays on gRPC. State and the outbox row commit in one Postgres transaction. The fact is published after that commit.
4. A consumer applies the record when `version` is newer, then Ack. A redelivery is a no-op.

Own-app checkout, the reference saga, is in [`docs/architecture.md` §7](docs/architecture.md#reference-flow-own-app-checkout). The shopper waits through `PlaceOrder` and the gateway hand-off. Capture or void happens after the POS accepts or rejects the ticket.

### Reading order

1. [`docs/architecture.md`](docs/architecture.md) — principles, components, transports, and the decision register.
2. [`docs/kafka-topics.md`](docs/kafka-topics.md) — the twelve registered topics, their keys, what was removed, and the growth policy.
3. [`docs/design/tech-stack.md`](docs/design/tech-stack.md) — what is fixed, what is open, and what is verified.
4. The other design notes in [`docs/design/`](docs/design/): [POS adapters](docs/design/pos-adapters.md), [brand configuration](docs/design/brand-configuration.md), [order payload log](docs/design/order-payload-log.md), [legacy bridge](docs/design/legacy-bridge.md), [identity model](docs/design/identity-model.md), [scale assumptions](docs/design/scale-assumptions.md).
5. [`domains/platform-overview/description.md`](domains/platform-overview/description.md) — the platform pictures.
6. The domain folder you work on. Each `description.md` says what the domain owns and which diagram files are current.
7. [`docs/platform-concept.md`](docs/platform-concept.md) — where the platform is heading, and where that picture still disagrees with the baseline.
8. [`docs/overview-guideline.md`](docs/overview-guideline.md) — before drawing a system overview page.
9. [`docs/CHANGELOG.md`](docs/CHANGELOG.md) — what changed in v3, where every file moved, and what to do next.

When those files disagree, `docs/architecture.md` wins, then `docs/kafka-topics.md`, then the design notes, then the domain `description.md`, then the HLD.

<!-- ai:anchor:features -->
## Features

- Binding architecture baseline: eight principles, component ownership, gRPC and Kafka rules, and a decision register (accepted, proposed, open).
- Twelve registered Kafka business topics, with producers, consumers, keys, retention, and partition counts, and a policy for adding more.
- Design notes for the POS adapter port, per-brand configuration, the MongoDB order payload log, the legacy bridge, the identity model, and recommended scale numbers (all assumptions).
- Domain diagrams in draw.io: a system overview, an HLD, and an LLD. Presenter scripts sit next to the HLDs that have one.
- A 2029 platform concept and a clickable demo at [`references/2029_Concept_Demo.html`](references/2029_Concept_Demo.html).
- Diagram rules for HLD layout, LLD page strips, colors, logos, and the Ack on a Kafka consume.

<!-- ai:anchor:installation -->
## Installation & Setup

### Prerequisites

- A draw.io editor: [diagrams.net](https://app.diagrams.net/) in the browser, or the draw.io desktop app.
- A Markdown preview for the rulebook. Any editor preview is enough. Mermaid diagrams in `docs/design/` render on GitHub and in most previews.
- Python 3 to run the checks in [`docs/tools/`](docs/tools/).

### Opening a diagram

1. Clone this repository.
2. Open the `.drawio` file in diagrams.net (File → Open From → Device) or in the desktop app.
3. Read the folder's `description.md` before the picture. It names which file is current. For a system overview, read `domain-overview.md` and do not open `*-overview.drawio` for the words.
4. Export a PNG with `draw.io -x -f png` only to check layout by eye. Leave the PNG uncommitted.

Files without a suffix are the baseline. Superseded `-v2` drafts, including the overview, live in [`_archive/`](_archive/).

<!-- ai:anchor:structure -->
## Project Structure

```text
.
├── README.md                       This file.
├── docs/
│   ├── architecture.md             Rulebook. Read this first. Baseline v3.
│   ├── kafka-topics.md             The only topic list, and the growth policy.
│   ├── platform-concept.md         2029 target picture.
│   ├── overview-guideline.md       How to draw a system overview page.
│   ├── CHANGELOG.md                Every change, and old path to new path.
│   ├── design/                     Design notes (v3). They explain and extend the rulebook.
│   │   ├── tech-stack.md           Edge, core, infrastructure: fixed, open, verified.
│   │   ├── pos-adapters.md         Multi-vendor POS port in OMS.
│   │   ├── brand-configuration.md  Per-brand configuration, capabilities, onboarding.
│   │   ├── order-payload-log.md    MongoDB parallel order payload log.
│   │   ├── legacy-bridge.md        Anti-corruption layer and strangler cutover.
│   │   ├── scale-assumptions.md    Recommended shape. All numbers are assumptions.
│   │   └── identity-model.md       Minor ID across brands.
│   └── tools/                      check-links.py, lint-old-names.py, scale-calc.py.
├── domains/
│   ├── platform-overview/          Platform overview and HLD.
│   ├── identity-and-customer/      Customer, login, OTP, addresses, PDPA consent.
│   ├── admin-and-partner/          Admin principal, grants, partner OAuth clients.
│   ├── brand-and-store/            Brand, store, hours, zone.
│   ├── catalog-and-menu/           SKUs, menu versions, sold-out, price book.
│   ├── cart-and-order/             Cart, order, POS ticket, checkout saga. This is the OMS.
│   ├── payment-and-billing/        Transactions, invoices, receipts.
│   ├── delivery-and-dispatch/      Quote, dispatch, rider, earnings ledger.
│   ├── wallet/                     Stored-value ledger and holds.
│   ├── loyalty-and-membercard/     Points, tier, and the member card.
│   ├── voucher-and-campaign/       Campaigns, vouchers, and the redemption book.
│   └── notification/               Templates, inbox, and outbound channels.
├── references/                     Source notes and the 2029 HTML demo.
└── _archive/                       Pre-EDA and v2 drafts. Historical. Not edited.
```

Loyalty & MemberCard is drawn from the [Loyalty target architecture](https://minordigital.atlassian.net/wiki/spaces/BackEnd/pages/3898146819/Loyalty+Domain+-+Target+Architecture). Topics follow [`docs/kafka-topics.md`](docs/kafka-topics.md): `order.events` in, `notification.requested` out.

| Domain | Diagrams |
| --- | --- |
| Platform | [platform-overview](domains/platform-overview/description.md) |
| Identity & Profile | [identity-and-customer](domains/identity-and-customer/description.md) |
| Admin & Partner | [admin-and-partner](domains/admin-and-partner/description.md) |
| Brand & Store | [brand-and-store](domains/brand-and-store/description.md) |
| Catalog & Menu | [catalog-and-menu](domains/catalog-and-menu/description.md) |
| Cart & Order (OMS) | [cart-and-order](domains/cart-and-order/description.md) |
| Payment & Billing | [payment-and-billing](domains/payment-and-billing/description.md) |
| Delivery & Dispatch | [delivery-and-dispatch](domains/delivery-and-dispatch/description.md) |
| Wallet | [wallet](domains/wallet/description.md) |
| Loyalty & MemberCard | [loyalty-and-membercard](domains/loyalty-and-membercard/description.md) |
| Voucher & Campaign | [voucher-and-campaign](domains/voucher-and-campaign/description.md) |
| Notification | [notification](domains/notification/description.md) |

<!-- ai:anchor:infrastructure -->
## Infrastructure / Integrations

The pictures name these contracts. The rules for each one are in [`docs/architecture.md`](docs/architecture.md). The core infrastructure is run by the DevOps team and stays on AWS as much as possible ([`docs/design/tech-stack.md`](docs/design/tech-stack.md)).

| Piece | Role |
| --- | --- |
| Cloudflare | Bots, WAF, TLS |
| Kong | The only policy enforcement point. JWT routes and signed webhook routes |
| Confluent Kafka + Schema Registry | Facts and commands. Protobuf, BACKWARD compatible |
| Aurora PostgreSQL | System of record per domain, including the transactional outbox |
| MongoDB (Atlas on AWS, to confirm with DevOps) | The order payload log in Cart & Order only. Never the truth |
| Valkey | The four cache uses in the rulebook. The truth stays in Postgres |
| S3 | Files such as a campaign audience. The command carries the key |
| Vault | Signing keys |
| Azure AD | Admin identity. Only Admin & Partner calls it |
| Omise | Card and QR gateway. One account per brand |
| TrueMoney | Rider payouts, called by Payment |
| SES, SMS, LINE | Message providers. Receipts enter through `webhook-adapter` |
| Grab, LINE MAN, Shopee Food | Aggregators, behind `partner-adapter` |
| ZEEK, Grab Express | Fleet providers, behind the Delivery port |
| POS vendors (BSL first; Promise and VIVI may follow) | Behind the `PosGateway` port in Cart & Order, one adapter per vendor |
| Legacy systems (Fleet Management, FAAS, Driver Management, SDM) | Behind the same domain ports, through the legacy bridge, during cutover |

<!-- ai:anchor:development -->
## Development

### Changing a fact

1. If the change breaks a rule, edit [`docs/architecture.md`](docs/architecture.md) first and write the reason in the decision register. If the change conflicts with a principle or an accepted decision, flag it in the text. Do not override it silently.
2. Add or remove a topic in [`docs/kafka-topics.md`](docs/kafka-topics.md) before it appears on a diagram. A new topic needs a producer, a consumer, and a reason a gRPC call or an existing topic does not already cover it ([growth policy](docs/kafka-topics.md#growth-policy)).
3. Update the design note that owns the idea (for example the POS adapters), then that domain's `description.md`, then the HLD, then the LLD. An LLD stays inside the topics, services, and owners the HLD already shows.
4. Copy styles from the reference file for that level. Do not invent a new look.
5. Run the checks below. Add a line to [`docs/CHANGELOG.md`](docs/CHANGELOG.md).

### Reference files

| Level | Copy from |
| --- | --- |
| HLD layout | [`domains/catalog-and-menu/catalog-menu-hld.drawio`](domains/catalog-and-menu/catalog-menu-hld.drawio) |
| HLD relation lines | [`domains/wallet/wallet-hld.drawio`](domains/wallet/wallet-hld.drawio) |
| LLD page | [`domains/cart-and-order/cart-order-lld.drawio`](domains/cart-and-order/cart-order-lld.drawio) |
| System overview | [`domains/wallet/wallet-overview.drawio`](domains/wallet/wallet-overview.drawio), rules in [`docs/overview-guideline.md`](docs/overview-guideline.md) |

### Diagram checks

- A third-party box carries its logo at 30×30, 16px from the left edge, embedded in the file.
- A Kafka consume ends in a green Ack pill after the last step.
- Export a PNG and read it. A line through a box, or a label sitting on a line, fails review.

### Document checks

```bash
python3 docs/tools/check-links.py .        # every relative Markdown link and #anchor must exist
python3 docs/tools/lint-old-names.py .     # no old folder names outside the changelog and _archive
python3 docs/tools/scale-calc.py           # recompute the scale tables from their assumptions
```

Do not edit a `.drawio` file by hand to rename things. Diagram titles still say "MFG ePlatform". That is a follow-up listed in [`docs/CHANGELOG.md`](docs/CHANGELOG.md).
