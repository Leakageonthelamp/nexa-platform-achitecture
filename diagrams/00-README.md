# NEXA diagrams (first draft, 2026-10-24)

A new set of easy-to-read diagrams of the NEXA design, drawn as native draw.io files. They follow the v3 text in [`docs/`](../docs/). **Where a diagram and the text disagree, the text wins** ([`docs/architecture.md`](../docs/architecture.md) is the rulebook). The older diagrams under [`domains/`](../domains/) and [`references/`](../references/) are untouched.

Status: first draft, design phase. Nothing is fixed. Every diagram says so in its subtitle, and every one has an "Open questions and assumptions" sticky that links real decision ids (D-, P- and O-) from the decision register in [`docs/architecture.md`](../docs/architecture.md#13-decision-register).

## The diagrams

Each file is one subject. Each page inside a file is one picture you can read in about a minute. The PNG previews are rendered from the files by the generator and are kept in [`previews/`](previews/).

| File | What it shows | Maps to | Previews |
| --- | --- | --- | --- |
| [`01-platform-overview.drawio`](01-platform-overview.drawio) | Big picture: who calls what, from the edge to the data, and what each box does in plain words | 1 (system map), 3 (components), 9 (runtime) in [architecture.md](../docs/architecture.md); [tech-stack.md](../docs/design/tech-stack.md) | [page 1](previews/01-platform-overview-p1-1-big-picture.png), [page 2](previews/01-platform-overview-p2-2-components-in-plain-words.png) |
| [`02-brand-onboarding-and-config.drawio`](02-brand-onboarding-and-config.drawio) | How a new brand is onboarded in 13 steps, what decides if a brand can offer something (vendor, brand feature, store setup), and who owns which setting | [brand-configuration.md](../docs/design/brand-configuration.md); P-37 | [page 1](previews/02-brand-onboarding-and-config-p1-1-onboarding-steps.png), [page 2](previews/02-brand-onboarding-and-config-p2-2-capability-feature-and-store-setup.png), [page 3](previews/02-brand-onboarding-and-config-p3-3-who-owns-which-setting.png) |
| [`03-identity-minor-id.drawio`](03-identity-minor-id.drawio) | One Minor ID across brands, shared profile with PDPA consent, loyalty and wallet separate per brand; sign-in and what happens when a brand is disabled | [identity-model.md](../docs/design/identity-model.md); P-33, P-40, D-11 | [page 1](previews/03-identity-minor-id-p1-1-one-person-many-brands.png), [page 2](previews/03-identity-minor-id-p2-2-sign-in-and-disable-per-brand.png) |
| [`04-oms-checkout-flow.drawio`](04-oms-checkout-flow.drawio) | The own-app checkout saga, step 0 to 12, in five pages, plus aggregator and wallet variants and a failure table | [architecture.md section 7](../docs/architecture.md#reference-flow-own-app-checkout); P-09, P-10, P-32 | [page 1](previews/04-oms-checkout-flow-p1-1-saga-at-a-glance.png), [page 2](previews/04-oms-checkout-flow-p2-2-shopper-waits-steps-1-to-5.png), [page 3](previews/04-oms-checkout-flow-p3-3-payment-confirmed-steps-6-to-8.png), [page 4](previews/04-oms-checkout-flow-p4-4-pos-ticket-and-answer-steps-9-and-10.png), [page 5](previews/04-oms-checkout-flow-p5-5-accept-or-reject-steps-11-and-12.png), [page 6](previews/04-oms-checkout-flow-p6-6-variants-and-failures.png) |
| [`05-oms-pos-adapters.drawio`](05-oms-pos-adapters.drawio) | The OMS POS port, registry and one adapter per vendor; the seven rules for applying a POS update; what BSL taught us; capability flags per store | [pos-adapters.md](../docs/design/pos-adapters.md); P-36 | [page 1](previews/05-oms-pos-adapters-p1-1-port-registry-and-adapters.png), [page 2](previews/05-oms-pos-adapters-p2-2-applying-a-pos-update-r1-to-r7.png), [page 3](previews/05-oms-pos-adapters-p3-3-what-the-adapter-has-to-absorb.png), [page 4](previews/05-oms-pos-adapters-p4-4-per-brand-selection-and-capability-flags.png) |
| [`06-order-payload-log-mongo.drawio`](06-order-payload-log-mongo.drawio) | The parallel MongoDB payload log: where it sits, how it links to the order, the write options, masking and retention | [order-payload-log.md](../docs/design/order-payload-log.md); P-38 | [page 1](previews/06-order-payload-log-mongo-p1-1-a-parallel-log-beside-the-order.png), [page 2](previews/06-order-payload-log-mongo-p2-2-linking-the-log-to-the-order.png), [page 3](previews/06-order-payload-log-mongo-p3-3-write-options-and-the-choice.png), [page 4](previews/06-order-payload-log-mongo-p4-4-masking-retention-and-access.png) |
| [`07-kafka-topic-map.drawio`](07-kafka-topic-map.drawio) | The twelve topics, who publishes and who consumes each, the envelope and delivery path, and the rule for adding a thirteenth | [kafka-topics.md](../docs/kafka-topics.md); P-06, P-42 | [page 1](previews/07-kafka-topic-map-p1-1-all-12-topics.png), [page 2](previews/07-kafka-topic-map-p2-2-brand-store-and-catalog-topics.png), [page 3](previews/07-kafka-topic-map-p3-3-order-and-payment-topics.png), [page 4](previews/07-kafka-topic-map-p4-4-delivery-and-notification-topics.png), [page 5](previews/07-kafka-topic-map-p5-5-one-record-from-commit-to-ack.png), [page 6](previews/07-kafka-topic-map-p6-6-is-it-a-topic-the-growth-rule.png) |
| [`08-legacy-bridge.drawio`](08-legacy-bridge.drawio) | A legacy system behind the same port, the strangler steps per capability and brand, bridge worker, old clients, where legacy is likely | [legacy-bridge.md](../docs/design/legacy-bridge.md); P-39 | [page 1](previews/08-legacy-bridge-p1-1-same-port-different-adapter.png), [page 2](previews/08-legacy-bridge-p2-2-moving-one-capability-for-one-brand.png), [page 3](previews/08-legacy-bridge-p3-3-facts-old-clients-and-where-legacy-is-likely.png) |
| [`09-ai-assistant-integration.drawio`](09-ai-assistant-integration.drawio) | What the AI assistant may read and write (UpdateCart only), one AI order in five steps, the six needs of an AI-ready edge | [tech-stack.md](../docs/design/tech-stack.md) (AI-ready edge); [platform-concept.md](../docs/platform-concept.md); P-34, P-41 | [page 1](previews/09-ai-assistant-integration-p1-1-what-the-assistant-may-read-and-write.png), [page 2](previews/09-ai-assistant-integration-p2-2-one-ai-order-and-what-the-edge-needs.png) |
| [`10-domain-map.drawio`](10-domain-map.drawio) | Eleven domains by role, who calls whom live over gRPC, and who publishes and consumes on Kafka | [architecture.md section 3 and 4](../docs/architecture.md#3-components); [kafka-topics.md](../docs/kafka-topics.md) | [page 1](previews/10-domain-map-p1-1-eleven-domains-by-role.png), [page 2](previews/10-domain-map-p2-2-who-calls-whom-live-grpc.png), [page 3](previews/10-domain-map-p3-3-who-publishes-and-who-consumes-kafka.png) |
| [`11-other-domains.drawio`](11-other-domains.drawio) | One context page each for Payment, Delivery, Wallet, Loyalty, Voucher and Campaign, Notification, Catalog and Admin and Partner (Brand and Store is in file 02, Identity in file 03) | [architecture.md](../docs/architecture.md); the domain HLDs under [domains/](../domains/) | [page 1](previews/11-other-domains-p1-1-payment-and-billing.png), [page 2](previews/11-other-domains-p2-2-delivery-and-dispatch.png), [page 3](previews/11-other-domains-p3-3-wallet.png), [page 4](previews/11-other-domains-p4-4-loyalty-and-membercard.png), [page 5](previews/11-other-domains-p5-5-voucher-and-campaign.png), [page 6](previews/11-other-domains-p6-6-notification.png), [page 7](previews/11-other-domains-p7-7-catalog-and-menu.png), [page 8](previews/11-other-domains-p8-8-admin-and-partner.png) |
| [`12-deployment-and-infra.drawio`](12-deployment-and-infra.drawio) | Where everything runs (Cloudflare, EKS, Aurora, Valkey, S3, Vault, Confluent, MongoDB Atlas), one domain app with four run modes, scale assumptions by tier | [tech-stack.md](../docs/design/tech-stack.md); [scale-assumptions.md](../docs/design/scale-assumptions.md); P-43 | [page 1](previews/12-deployment-and-infra-p1-1-where-everything-runs.png), [page 2](previews/12-deployment-and-infra-p2-2-one-domain-app-four-run-modes.png), [page 3](previews/12-deployment-and-infra-p3-3-scale-assumptions-by-tier.png) |
| [`13-postpaid-table-ordering.drawio`](13-postpaid-table-ordering.drawio) | Proposal added 2026-10-25: QR table ordering with pay at the end. The idea at a glance, tab and round states, one round to the POS and the kitchen, the bill and payment (with pay at the counter), failures, and where it plugs into NEXA | [postpaid-table-ordering.md](../docs/design/postpaid-table-ordering.md); P-44 to P-52 | [page 1](previews/13-postpaid-table-ordering-p1-1-the-idea-at-a-glance.png), [page 2](previews/13-postpaid-table-ordering-p2-2-table-session-and-tab-states.png), [page 3](previews/13-postpaid-table-ordering-p3-3-a-round-goes-to-the-pos-and-the-kitchen.png), [page 4](previews/13-postpaid-table-ordering-p4-4-ask-for-the-bill-and-pay-at-the-end.png), [page 5](previews/13-postpaid-table-ordering-p5-5-failures-and-edge-cases.png), [page 6](previews/13-postpaid-table-ordering-p6-6-where-it-plugs-into-nexa.png) |

Page counts: 01 has 2, 02 has 3, 03 has 2, 04 has 6, 05 has 4, 06 has 4, 07 has 6, 08 has 3, 09 has 2, 10 has 3, 11 has 8, 12 has 3, 13 has 6: 52 pages in 13 files.

Two pages are tables on purpose and go past the soft limit of about 25 boxes: the failure table in 04 (page 6) and the publish and consume matrix in 10 (page 3).

## How to open and edit

- **draw.io desktop** (any recent version): File, Open, pick a `.drawio` file. Pages are tabs at the bottom.
- **diagrams.net** in a browser: File, Open from, Device.
- **VS Code**: the "Draw.io Integration" extension opens `.drawio` files in the editor.
- The files are uncompressed XML (`mxfile`), so a change shows up as a normal text diff in git. Ids are stable and meaningful (for example `e.order.pay` is the edge from Order to Payment).
- **Hand edits are fine.** Move a box, rewrite a label, add a note. If you edit by hand, keep the legend and the question sticky, and keep the dashed outline for anything proposed.
- **The generator** is [`tools/gen_diagrams.py`](tools/gen_diagrams.py), with the shared library `tools/drawio_lib.py`. It writes the `.drawio` files, checks them (valid XML, every edge end exists, no duplicate ids, no overlapping boxes, no line through a box, labels clear of boxes, decision ids exist in the register) and can render the previews with the draw.io desktop CLI: `python3 diagrams/tools/gen_diagrams.py --render`. Rerunning it overwrites hand edits in the generated files, so choose one way to maintain each file: hand edit, or change the generator.

## How to read them

| Style | Meaning |
| --- | --- |
| Orange line | synchronous call (gRPC): someone is waiting |
| Blue line | HTTPS at the edge, or an outside party |
| Purple dashed line, purple box | Kafka command topic (`domain.requested`) |
| Green dashed line, green box | Kafka fact topic (what already happened) |
| Yellow box | a NEXA service (Go or Bun) or an engine |
| Grey box or line | data store, or a best-effort log write |
| Red box or line | failure or stop |
| Dashed outline | new in v3, proposed, or an assumption |
| Numbered black badge | a step on a flow, in order |

Every page has the title "NEXA - first draft" with its date (2026-10-24, or 2026-10-25 for file 13), a legend, a "maps to" line naming the document it comes from, and a short numbered flow where there is a flow. Boxes use plain words first and the technical name second. Swimlanes, orthogonal lines, at most about 25 boxes per page.

## How to discuss and change them

1. Find the page. The subtitle says which document and section it comes from.
2. Read the numbered steps and the sticky at the bottom right. The sticky lists the open questions (O-xx) and assumptions behind the page, with their ids.
3. Say which step or box you want changed. A change that touches a rule goes into the decision register first ([`docs/architecture.md`](../docs/architecture.md#13-decision-register)), then into the diagram.
4. A new topic never appears on a diagram before it is in [`docs/kafka-topics.md`](../docs/kafka-topics.md).

## Where the older diagrams differ

[`docs/architecture.md` section 14](../docs/architecture.md#14-known-drift) lists the older files that the v3 text has moved ahead of. These new diagrams follow the text, so they show the POS adapter port, the MongoDB payload log, brand feature switches, the enabled or disabled membership and the legacy bridge that the older files do not.
