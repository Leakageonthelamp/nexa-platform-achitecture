# Platform — system overview

Plain reading of [`mfg-eplatform-hld.drawio`](mfg-eplatform-hld.drawio). There is no platform LLD.
The picture names the four edges, the two adapters, one Aurora schema per domain, and the twelve topics in [`kafka-topics.md`](../../docs/kafka-topics.md).

<!-- ai:anchor:sentence -->
## Sentence

One shared platform for every brand. A caller who is waiting uses a direct call. Kafka carries only what already happened, and only the topics in the registry.

<!-- ai:anchor:features -->
## Features

### Shoppers
- **Contact:** Customers ask
- **Technology:** gRPC
- **From:** HLD Customer BFF and Guest BFF, corrected by the rulebook
- The customer app and the guest app each have their own edge
- They call the domain that owns the answer
- A guest is not signed in
- The customer edge also pushes a live frame, which can be dropped

### Staff and partners
- **Contact:** Staff and partners ask
- **Technology:** gRPC
- **From:** HLD Admin BFF, corrected: no store portal and no store edge
- Staff use one admin edge
- A partner with a token uses the partner edge
- There is no store portal
- The grant is checked before the domain is called

### Signed webhooks
- **Contact:** The edge receives them
- **Technology:** HTTP
- **From:** HLD adapters, corrected: two adapters, not one
- Aggregators, the kitchen, and the gateway hit an adapter
- The adapter checks the signature
- It publishes one command
- A domain never takes the webhook itself

### Domains
- **Contact:** A domain asks another, and waits
- **Technology:** gRPC
- **From:** HLD domain row, corrected against the domain HLDs
- Each domain owns one kind of truth
- Go for the domains, Bun for the edges
- A wallet is one ledger per brand and customer, not “digital wallets”
- Loyalty is points and the card. Voucher is the deal

<!-- ai:anchor:shared -->
## Shared

**One brand on every hop** — shared services, not a stack per brand

On the bar: `brand_id` on the call and on the message key. A rider’s pay and a group-wide exception use the reserved group tenant.

<!-- ai:anchor:neighbours -->
## Neighbours

- **Shoppers, staff, and partners** — solid, `asks`. Through the four edges.
- **The domains** — solid, `asks`. Direct calls when someone is waiting.
- **The bus** — dashed, `Kafka`. The registry only: brand, store, catalog, order, payment, delivery, and notification. There is no customer topic, no loyalty topic, and no wallet topic.

<!-- ai:anchor:infrastructure -->
## Infrastructure

- **Aurora PostgreSQL** — One cluster per environment, one schema and one role per domain. Not a database product per service.
- **Kafka** — The dashed lines run on this. Twelve business topics, not a family per domain name.
- **Valkey** — A read cache, short-lived sign-in state, rate limits, and the live frame. Never the order, the payment, or a balance.
- **S3** — Files and the analytics sink. The sink reads facts that already exist.
- **Vault** — Secrets.

<!-- ai:anchor:not-here -->
## Not here

A store portal, a second admin edge for stores, one adapter for every outsider, a search engine for the menu, and topic families named delivery, customer, or loyalty.
