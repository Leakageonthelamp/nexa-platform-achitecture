# Changelog

Changes to the NEXA documentation repo. This file records the v3 restructure (2026-10-24): what changed, why, where every file moved, and what is left to do.

Baseline v2 (2026-10-05) is superseded by baseline v3 (2026-10-24). v2 content is kept. Where something became superseded the text says so.

---

## Addendum 2026-10-25: postpaid QR table ordering (proposal)

A new requirement was added to the first draft: a customer scans a QR code at the table, orders from the phone, and pays after eating. The order stays on the table until it is paid, and the food is served to the table. Everything below is a **proposal in the design phase**. Nothing is fixed.

| Area | Change |
| --- | --- |
| New note | [`design/postpaid-table-ordering.md`](design/postpaid-table-ordering.md): the open tab in Cart & Order, table and QR, lifecycle, flow, payment at the end, POS add-on, data and contracts, edge cases, decisions, open questions |
| Rulebook | `architecture.md`: new decisions **P-44 to P-52** and open items **O-37 to O-48** in section 13. A postpaid flow in section 7. The component rows (section 3), the OMS capabilities, section 10, two drift rows (section 14) and three glossary terms were extended. The text of section 2, 5 and 8 is unchanged |
| POS | `design/pos-adapters.md`: new section 14 (open checks and table service) and a BSL postpaid paragraph. BSL flags for the new operations are recorded as unknown |
| Config | `design/brand-configuration.md`: a postpaid switch row in the axis and ownership tables, and a new section 7 with the switches. The open items moved to section 8 |
| Kafka | `kafka-topics.md`: **no new topic**. `order.events` gains `round_updated`. `payment` records carry a `purpose`. The `tab.events` idea is listed as already covered |
| Domains | `description.md` of Cart & Order, Brand & Store, Payment & Billing, Notification, Identity & Customer, Delivery & Dispatch (not used) and Voucher & Campaign got a "v-next (2026-10-25)" section |
| Diagrams | New `diagrams/13-postpaid-table-ordering.drawio` (6 pages) with previews and the generator module `diagrams/tools/d13_postpaid.py`. `drawio_lib.py` `frame()` gained an optional `date` argument whose default is unchanged. The other 12 files were not regenerated and are unchanged |

Decisions I made for this addendum (each is also a P- row):

| # | Point | Choice | Why |
| --- | --- | --- | --- |
| 1 | Who owns the table session and tab | Cart & Order (P-44). Rejected: Brand & Store, a new Dining domain, the Delivery domain | Principle 3 and 5: one write path per aggregate and no new service |
| 2 | Guest identity | A guest token: a customer-family JWT with scope `dine_in`, signed by Identity, 5 minutes (P-45). A fourth token family is written down as an alternative. The text of section 8 is unchanged and flagged | Do not change an accepted rule without the owner |
| 3 | When an order is "placed" | At the first round, with no payment gate. This changes the cost line of P-09 and is flagged | A tab has no payment before the meal |
| 4 | Payment | Pay first, then close the POS check. Capture at authorize as in P-17. A card hold (P-48) is optional per brand | A POS close can be retried safely, a split authorize and capture cannot be done with QR |
| 5 | POS without open check | Degrade modes `ticket_per_round` and `staff_settle`. No vendor capability is asserted | O-42 is open for every vendor |
| 6 | Kafka | No new topic (P-51) | A `tab.events` topic fails the third answer of the growth rule |
| 7 | Split bill | Whole bill only in the first draft. Equal split next, by item later, flagged against P-16 | Conservative scope |
| 8 | "Deliver to table" | Table service by staff, from POS or kitchen signals plus a staff tap. Not the Delivery domain | No rider, no fee, no zone |

Diagrams to update next (they do not yet show postpaid): 03 identity (guest token), 04 checkout (postpaid variant), 05 POS adapters (open check and flags), 07 Kafka map (`round_updated`, `purpose`), 10 domain map and 11 other domains (new calls). Public facts about the card hold were read on the Omise pages named in the note on 2026-10-25. MFG's own account settings are to confirm (O-43).

---

## 1. Summary

| Area | Change |
| --- | --- |
| Name | Prose and titles say NEXA (next generation experience architecture). "MFG ePlatform" appears as the former name in the README, rulebook, and platform concept, and where a note says a diagram title still carries it. `mfg.<domain>.v1` proto packages, the tenant `mfg`, and Kafka topic names are unchanged |
| Status | Marked a first draft in the design phase, not yet refined by business requirements or brand limits. "MVP1" in an old commit message means nothing |
| Layout | Four root docs moved to `docs/`, the twelve `*-diagrams` folders became `domains/<name>/`, `_refs/` became `references/`, `_archive/` stayed. 16 draw.io lock files removed |
| Rulebook | `docs/architecture.md` is baseline v3: central platform and per-brand configuration, POS adapter port, MongoDB payload log, hexagonal Go and Elysia v2, legacy bridge, Minor ID per brand. New decisions P-36 to P-43 and open items O-27 to O-36. D-11 confirmed. O-19 and O-20 deferred |
| Design notes | Seven new files in `docs/design/` |
| Topics | `docs/kafka-topics.md` keeps the 12 registered topics. **No topic was added.** A growth policy and a list of candidates were added |
| Drift | Known drift was fixed in the text. Diagrams that now lag the text are listed in section 6 |
| Checks | `docs/tools/check-links.py` (zero broken links), `lint-old-names.py`, `scale-calc.py` |
| Diagrams | **No `.drawio` file was edited.** All 52 are byte-identical to the originals at their new paths (see the mapping table) |

---

## 2. Decisions I made

The task asked that an ambiguous point take the most conservative option and be written down here.

| # | Point | Choice | Why |
| --- | --- | --- | --- |
| 1 | Up to 3 new Kafka topics if strongly justified | **None registered.** Four candidates listed, plus four ideas shown to be covered by existing topics | Each failed the three-answers rule today. The owner called 12 low, so this is flagged for review in the Kafka file, not hidden |
| 2 | Elysia v2 status | Documented as a **release candidate (19 Oct 2026)**, not a final release. Only facts read on the official Elysia pages are stated, with the URL. Everything else is "To verify" | The official RC post says "RC". An npm page read the same day showed 1.4.30 as the default tag, possibly cached |
| 3 | Elysia 2 defaults to RFC 9457 error bodies (per the beta post) while §4 sets our own error body | Our own `{ code, message, trace_id }` stays the rule. Mapping is a "To verify" item (O-34) | Do not weaken an accepted rule because a framework default differs |
| 4 | Where per-brand config lives | Each domain owns its own slice. Brand & Store owns only brand feature switches and the onboarding state, as a **proposal** | Principle 3 (one owner) and D-07 (no copies). A central config service would be a new component |
| 5 | Mongo write path | Recommended: in-process capture, async best-effort writer. Options B (Postgres capture row) and C (topic) are written down as alternatives | The owner said best effort, async, never blocking checkout. Completeness is raised as O-30 |
| 6 | Several writers into the Mongo log vs principle 3 | Flagged in the doc and in P-38, limited to insert-only writers and one reader | Not silently overridden |
| 7 | POS proxies guardrail in §10 | Row struck through and marked "Reversed in v3 (P-36)" with the reason and cost. Row text kept | Do not delete information |
| 8 | SHLD references | Dangling links removed. Each name is kept as text and marked "not yet drawn". No SHLD file was invented | Instruction |
| 9 | Delivery LLD page count | The file has 16 pages (14 entry points, 15 end to end, 16 payout reconcile). Text in P-13 and §3 was fixed to 16 | Counted from the `<diagram` elements |
| 10 | Catalog HLD file has 2 pages (second is "Page-2") | Reported in §14 as something to check. Not changed | A `.drawio` file must not be edited |
| 11 | Correlation id for the payload log | The trace id from `traceparent`. No change to the Kafka record envelope | Smallest change |
| 12 | Ids for new items | Decisions P-36 to P-43. Open items O-27 to O-36. The original O-08 was never used and stays unused | Continue the existing numbering without reusing a gap |
| 13 | Scripts | `docs/tools/` holds the three document checks. The one-off move scripts are not in the repo | The target layout has no tools folder, so only the scripts a maintainer would rerun were added |
| 14 | BSL profile values in the POS note | Every flag value is an Assumption, taken from the owner's UAT testing, until the vendor confirms (O-28) | Not vendor documentation |
| 15 | `domain-overview.md` files (plain readings of the HLD) | Appended a short "v3 changes not yet in the diagrams" section to the Cart & Order and Brand & Store ones. Other domains' overview files were not edited | The HLD is the source of those files and was not redrawn |
| 16 | `references/confluence-domains.md` | A note was added at the top. The body is unchanged | It is a copy of reference notes |
| 17 | `_archive/` | Not edited. Its contents moved nowhere | Instruction |
| 18 | `Ready for development` gate in §12 | Left as is. Several §14 rows are open on purpose, so Order, Brand & Store, and Identity should not start coding until their rows close | The rule says so. It is stated in the text |

---

## 3. Edited files

| File | What changed |
| --- | --- |
| `README.md` | Rewritten for NEXA: purpose, picture, reading order, repo map, how to change a fact |
| `docs/architecture.md` | Baseline v3. See section 4 |
| `docs/kafka-topics.md` | Intro, `order.requested` note, a note under the removed list, deferred note for O-19 and O-20, growth policy, candidates |
| `docs/platform-concept.md` | Renamed, demo link fixed, owner decision note in §7 |
| `docs/overview-guideline.md` | Paths updated, SHLD guideline links removed |
| `domains/*/description.md` | `SHLD` entries marked "not yet drawn". Cart & Order, Brand & Store, Identity, and Delivery got a short v3 section |
| `domains/cart-and-order/domain-overview.md`, `domains/brand-and-store/domain-overview.md` | Short v3 section |
| `domains/cart-and-order/cart-order-hld-script.md` | A note at the top that it is a v2 script |
| `references/confluence-domains.md` | A note at the top |
| Other domain `*.md` files | Relative links rewritten for the new paths. No wording changed |

## 4. `architecture.md` in detail

| Section | Change |
| --- | --- |
| Header | v3 · 2026-10-24, first-draft status, "wins over everything else", NEXA name |
| Links | SHLD links removed, design notes linked, 2029 deferral noted |
| §1 | Central platform and configuration, tech stack summary, legacy note |
| §2 | **Unchanged.** Principles were not weakened |
| §3 | `partner-adapter` vendor mappers, Identity row (membership), Brand & Store row (switches), Cart & Order row (OMS, POS port, payload log), a new "OMS and the POS adapter port" section, Delivery page count |
| §4 | POS vendor rules |
| §5 | Unchanged |
| §6 | MongoDB for the order payload log only, with the written reason |
| §7 | Steps 9 and 10 use the POS port. Three new failure rows. Note on the payload log |
| §8 | Unchanged |
| §9 | Elysia v2, REST only, hexagonal Go and the mode mapping, infra ownership |
| §10 | The POS proxy guardrail reversed with reason and cost. A line on what v3 added |
| §11 | Unchanged |
| §12 | Two checklist items. A note on the ready gate |
| §13 | D-11 confirmed. P-13 fixed. P-36 to P-43 added. O-01 to O-03, O-06, O-18 updated. O-19 and O-20 deferred. O-27 to O-36 added |
| §14 | Open rows for diagrams that lag. Fixed drift. LLD page counts as drawn |
| §15 | New terms |

---

## 5. New files

- `docs/CHANGELOG.md`
- `docs/design/brand-configuration.md`
- `docs/design/identity-model.md`
- `docs/design/legacy-bridge.md`
- `docs/design/order-payload-log.md`
- `docs/design/pos-adapters.md`
- `docs/design/scale-assumptions.md`
- `docs/design/tech-stack.md`
- `docs/tools/check-links.py`
- `docs/tools/lint-old-names.py`
- `docs/tools/scale-calc.py`

---

## 6. Diagrams to update next

The `.drawio` files were not edited. These need work so the diagrams match the text. The same list is in [`architecture.md` §14](architecture.md#14-known-drift).

| Diagram | Update |
| --- | --- |
| `domains/cart-and-order/cart-order-hld.drawio` | POS adapter port, registry and vendor adapters in place of "BSL proxy"; MongoDB box in the Data lane; written reason for the second engine in Decisions; a `ponytail:` note for the payload log writer |
| `domains/cart-and-order/cart-order-lld.drawio` page 3 | Rank, dedupe, reported-total rules (R1 to R7) and the reconcile cron |
| `domains/brand-and-store/brand-store-hld.drawio` | Brand feature switches and onboarding state |
| `domains/identity-and-customer/identity-customer-hld.drawio`, `identity-customer-lld.drawio` page 3 | Membership status, brand-scoped token |
| `domains/platform-overview/mfg-eplatform-hld.drawio`, `mfg-eplatform-overview.drawio` | NEXA title, MongoDB box, POS vendors in the adapter lane |
| `domains/cart-and-order/cart-order-overview.drawio` | MongoDB infrastructure card (copy the logo from a diagram that has it) |
| Cart & Order HLD script | Rewrite after the HLD is redrawn |

---

## 7. Follow-ups

| Item | Note |
| --- | --- |
| Diagram titles | Every `.drawio` title and label that says "MFG ePlatform" still does. Rename when each diagram is next opened. Do not rename `mfg.<domain>.v1`, the tenant `mfg`, or topic names |
| File names | `mfg-eplatform-hld.drawio` and `mfg-eplatform-overview.drawio` keep their names (names stay for now) |
| SHLD | `SHLD-guideline.md` and the `*-shld.drawio` files were never in this repo. Draw them or drop the idea |
| Catalog HLD | The file has a second page named "Page-2". Check what it holds |
| Boilerplates | Align `docs/design/tech-stack.md` section 3 with the owner's Go and Bun boilerplates when shared |
| Elysia | Re-check `docs/design/tech-stack.md` section 2 at the final Elysia 2 release |
| Mermaid | The diagrams in `docs/design/` were parse-checked, not rendered |

---

## 8. Removed noise

draw.io editor lock and autosave files (`.$*.bkp`). They hold no information that is not in the `.drawio` file of the same name. 16 files:

- `_refs/.$customer-lld.drawio.bkp`
- `admin-and-partner-diagrams/.$admin-partner-hld-v2.drawio.bkp`
- `admin-and-partner-diagrams/.$admin-partner-hld.drawio.bkp`
- `admin-and-partner-diagrams/.$admin-partner-lld.drawio.bkp`
- `brand-and-store-diagrams/.$brand-store-hld-v2.drawio.bkp`
- `brand-and-store-diagrams/.$brand-store-hld.drawio.bkp`
- `cart-and-order-domain-diagrams/.$cart-order-hld.drawio.bkp`
- `cart-and-order-domain-diagrams/.$cart-order-lld.drawio.bkp`
- `catalog-and-menu-diagrams/.$catalog-menu-hld.drawio.bkp`
- `delivery-and-dispatch-diagrams/.$delivery-dispatch-hld.drawio.bkp`
- `delivery-and-dispatch-diagrams/.$delivery-dispatch-lld.drawio.bkp`
- `notification-diagrams/.$notification-hld.drawio.bkp`
- `overview-diagrams/.$mfg-eplatform-hld.drawio.bkp`
- `overview-diagrams/.$mfg-eplatform-shld.drawio.bkp`
- `payment-domain-diagrams/.$payment-billing-hld.drawio.bkp`
- `wallet-diagrams/.$wallet-hld.drawio.bkp`

The working copy the restructure started from had no `.DS_Store`, `__MACOSX`, or `._*` files. (The tar of the original folder carries 136 `._*` AppleDouble entries. These are tar metadata, not repo files, and were left out of the 108.)

---

## 9. Old path to new path

Every one of the 108 files in the original copy is below, either at its new path or listed as removed. Old folder names appear here only, and in `_archive/` content.

| Old path | New path | Note |
| --- | --- | --- |
| `README.md` | `README.md` | moved, content edited |
| `_archive/2026-10-01-pre-eda/admin-and-partner-diagrams/admin-partner-hld.drawio` | `_archive/2026-10-01-pre-eda/admin-and-partner-diagrams/admin-partner-hld.drawio` | byte-identical (sha256 a44a578cd8e8) |
| `_archive/2026-10-01-pre-eda/brand-and-store-diagrams/brand-store-hld-script.md` | `_archive/2026-10-01-pre-eda/brand-and-store-diagrams/brand-store-hld-script.md` | unchanged |
| `_archive/2026-10-01-pre-eda/brand-and-store-diagrams/brand-store-hld.drawio` | `_archive/2026-10-01-pre-eda/brand-and-store-diagrams/brand-store-hld.drawio` | byte-identical (sha256 a137416014ac) |
| `_archive/2026-10-01-pre-eda/catalog-and-menu-diagrams/catalog-menu-hld.drawio` | `_archive/2026-10-01-pre-eda/catalog-and-menu-diagrams/catalog-menu-hld.drawio` | byte-identical (sha256 a27dfe1a64a2) |
| `_archive/2026-10-01-pre-eda/mfg-eplatform-hld.drawio` | `_archive/2026-10-01-pre-eda/mfg-eplatform-hld.drawio` | byte-identical (sha256 26d72b5feb73) |
| `_archive/2026-10-01-pre-eda/order-domain-diagrams/unity-order-service-order-engine-hld.drawio` | `_archive/2026-10-01-pre-eda/order-domain-diagrams/unity-order-service-order-engine-hld.drawio` | byte-identical (sha256 559c4c0b6b02) |
| `_archive/2026-10-01-pre-eda/payment-domain-diagrams/payment-billing-hld.drawio` | `_archive/2026-10-01-pre-eda/payment-domain-diagrams/payment-billing-hld.drawio` | byte-identical (sha256 ddaae520bd56) |
| `_archive/2026-10-05-v2-drafts/admin-and-partner-diagrams/admin-partner-hld-v2.drawio` | `_archive/2026-10-05-v2-drafts/admin-and-partner-diagrams/admin-partner-hld-v2.drawio` | byte-identical (sha256 0c33334a8301) |
| `_archive/2026-10-05-v2-drafts/brand-and-store-diagrams/brand-store-hld-v2.drawio` | `_archive/2026-10-05-v2-drafts/brand-and-store-diagrams/brand-store-hld-v2.drawio` | byte-identical (sha256 3560ddfdcdce) |
| `_archive/2026-10-05-v2-drafts/catalog-and-menu-diagrams/catalog-menu-hld-v2.drawio` | `_archive/2026-10-05-v2-drafts/catalog-and-menu-diagrams/catalog-menu-hld-v2.drawio` | byte-identical (sha256 f7fc5836b014) |
| `_archive/2026-10-05-v2-drafts/order-domain-diagrams/unity-order-service-order-engine-v2.drawio` | `_archive/2026-10-05-v2-drafts/order-domain-diagrams/unity-order-service-order-engine-v2.drawio` | byte-identical (sha256 772bc9c9fcdf) |
| `_archive/2026-10-05-v2-drafts/overview-diagrams/mfg-eplatform-hld-v2.drawio` | `_archive/2026-10-05-v2-drafts/overview-diagrams/mfg-eplatform-hld-v2.drawio` | byte-identical (sha256 8410f961297e) |
| `_archive/2026-10-05-v2-drafts/payment-domain-diagrams/payment-billing-hld-v2.drawio` | `_archive/2026-10-05-v2-drafts/payment-domain-diagrams/payment-billing-hld-v2.drawio` | byte-identical (sha256 70ab68aee983) |
| `_refs/.$customer-lld.drawio.bkp` | — | REMOVED (draw.io lock/autosave file) |
| `_refs/2029_Concept_Demo.html` | `references/2029_Concept_Demo.html` | moved, unchanged |
| `_refs/campaign-1.drawio` | `references/campaign-1.drawio` | byte-identical (sha256 4fabc6cfcb4d) |
| `_refs/campaign-2.drawio` | `references/campaign-2.drawio` | byte-identical (sha256 58fc94ab1864) |
| `_refs/campaign-3.drawio` | `references/campaign-3.drawio` | byte-identical (sha256 950b48dd54c3) |
| `_refs/confluence-domains.md` | `references/confluence-domains.md` | moved, content edited |
| `_refs/customer-hld.drawio` | `references/customer-hld.drawio` | byte-identical (sha256 32bbf0ebf565) |
| `_refs/customer-lld.drawio` | `references/customer-lld.drawio` | byte-identical (sha256 f6b9c15e5354) |
| `admin-and-partner-diagrams/.$admin-partner-hld-v2.drawio.bkp` | — | REMOVED (draw.io lock/autosave file) |
| `admin-and-partner-diagrams/.$admin-partner-hld.drawio.bkp` | — | REMOVED (draw.io lock/autosave file) |
| `admin-and-partner-diagrams/.$admin-partner-lld.drawio.bkp` | — | REMOVED (draw.io lock/autosave file) |
| `admin-and-partner-diagrams/admin-partner-hld-script.md` | `domains/admin-and-partner/admin-partner-hld-script.md` | moved, links rewritten |
| `admin-and-partner-diagrams/admin-partner-hld.drawio` | `domains/admin-and-partner/admin-partner-hld.drawio` | byte-identical (sha256 36b47a1cbbba) |
| `admin-and-partner-diagrams/admin-partner-lld.drawio` | `domains/admin-and-partner/admin-partner-lld.drawio` | byte-identical (sha256 f348ff77df0b) |
| `admin-and-partner-diagrams/admin-partner-overview.drawio` | `domains/admin-and-partner/admin-partner-overview.drawio` | byte-identical (sha256 ecd559a8913a) |
| `admin-and-partner-diagrams/description.md` | `domains/admin-and-partner/description.md` | moved, content edited |
| `admin-and-partner-diagrams/domain-overview.md` | `domains/admin-and-partner/domain-overview.md` | moved, unchanged |
| `architecture.md` | `docs/architecture.md` | moved, content edited |
| `brand-and-store-diagrams/.$brand-store-hld-v2.drawio.bkp` | — | REMOVED (draw.io lock/autosave file) |
| `brand-and-store-diagrams/.$brand-store-hld.drawio.bkp` | — | REMOVED (draw.io lock/autosave file) |
| `brand-and-store-diagrams/brand-store-hld-script.md` | `domains/brand-and-store/brand-store-hld-script.md` | moved, links rewritten |
| `brand-and-store-diagrams/brand-store-hld.drawio` | `domains/brand-and-store/brand-store-hld.drawio` | byte-identical (sha256 1df5f93078c1) |
| `brand-and-store-diagrams/brand-store-lld.drawio` | `domains/brand-and-store/brand-store-lld.drawio` | byte-identical (sha256 f5b7bb1883c8) |
| `brand-and-store-diagrams/brand-store-overview.drawio` | `domains/brand-and-store/brand-store-overview.drawio` | byte-identical (sha256 7d4c4617833b) |
| `brand-and-store-diagrams/description.md` | `domains/brand-and-store/description.md` | moved, content edited |
| `brand-and-store-diagrams/domain-overview.md` | `domains/brand-and-store/domain-overview.md` | moved, content edited |
| `cart-and-order-domain-diagrams/.$cart-order-hld.drawio.bkp` | — | REMOVED (draw.io lock/autosave file) |
| `cart-and-order-domain-diagrams/.$cart-order-lld.drawio.bkp` | — | REMOVED (draw.io lock/autosave file) |
| `cart-and-order-domain-diagrams/cart-order-hld-script.md` | `domains/cart-and-order/cart-order-hld-script.md` | moved, content edited |
| `cart-and-order-domain-diagrams/cart-order-hld.drawio` | `domains/cart-and-order/cart-order-hld.drawio` | byte-identical (sha256 6300d840160b) |
| `cart-and-order-domain-diagrams/cart-order-lld.drawio` | `domains/cart-and-order/cart-order-lld.drawio` | byte-identical (sha256 6eca00400a50) |
| `cart-and-order-domain-diagrams/cart-order-overview.drawio` | `domains/cart-and-order/cart-order-overview.drawio` | byte-identical (sha256 8edd1ff64310) |
| `cart-and-order-domain-diagrams/description.md` | `domains/cart-and-order/description.md` | moved, content edited |
| `cart-and-order-domain-diagrams/domain-overview.md` | `domains/cart-and-order/domain-overview.md` | moved, content edited |
| `catalog-and-menu-diagrams/.$catalog-menu-hld.drawio.bkp` | — | REMOVED (draw.io lock/autosave file) |
| `catalog-and-menu-diagrams/catalog-menu-hld-script.md` | `domains/catalog-and-menu/catalog-menu-hld-script.md` | moved, links rewritten |
| `catalog-and-menu-diagrams/catalog-menu-hld.drawio` | `domains/catalog-and-menu/catalog-menu-hld.drawio` | byte-identical (sha256 37d98f1ce229) |
| `catalog-and-menu-diagrams/catalog-menu-lld.drawio` | `domains/catalog-and-menu/catalog-menu-lld.drawio` | byte-identical (sha256 b7d798175d27) |
| `catalog-and-menu-diagrams/catalog-overview.drawio` | `domains/catalog-and-menu/catalog-overview.drawio` | byte-identical (sha256 c321819921fa) |
| `catalog-and-menu-diagrams/description.md` | `domains/catalog-and-menu/description.md` | moved, content edited |
| `catalog-and-menu-diagrams/domain-overview.md` | `domains/catalog-and-menu/domain-overview.md` | moved, unchanged |
| `delivery-and-dispatch-diagrams/.$delivery-dispatch-hld.drawio.bkp` | — | REMOVED (draw.io lock/autosave file) |
| `delivery-and-dispatch-diagrams/.$delivery-dispatch-lld.drawio.bkp` | — | REMOVED (draw.io lock/autosave file) |
| `delivery-and-dispatch-diagrams/delivery-dispatch-hld-script.md` | `domains/delivery-and-dispatch/delivery-dispatch-hld-script.md` | moved, links rewritten |
| `delivery-and-dispatch-diagrams/delivery-dispatch-hld.drawio` | `domains/delivery-and-dispatch/delivery-dispatch-hld.drawio` | byte-identical (sha256 118e361036bb) |
| `delivery-and-dispatch-diagrams/delivery-dispatch-lld.drawio` | `domains/delivery-and-dispatch/delivery-dispatch-lld.drawio` | byte-identical (sha256 a262ab55afae) |
| `delivery-and-dispatch-diagrams/delivery-overview.drawio` | `domains/delivery-and-dispatch/delivery-overview.drawio` | byte-identical (sha256 2b388e43e44f) |
| `delivery-and-dispatch-diagrams/description.md` | `domains/delivery-and-dispatch/description.md` | moved, content edited |
| `delivery-and-dispatch-diagrams/domain-overview.md` | `domains/delivery-and-dispatch/domain-overview.md` | moved, unchanged |
| `identity-and-customer-diagrams/description.md` | `domains/identity-and-customer/description.md` | moved, content edited |
| `identity-and-customer-diagrams/domain-overview.md` | `domains/identity-and-customer/domain-overview.md` | moved, unchanged |
| `identity-and-customer-diagrams/identity-customer-hld.drawio` | `domains/identity-and-customer/identity-customer-hld.drawio` | byte-identical (sha256 12d5276fc27b) |
| `identity-and-customer-diagrams/identity-customer-lld.drawio` | `domains/identity-and-customer/identity-customer-lld.drawio` | byte-identical (sha256 52ca8945c28c) |
| `identity-and-customer-diagrams/identity-customer-overview.drawio` | `domains/identity-and-customer/identity-customer-overview.drawio` | byte-identical (sha256 b12cdf7aab6c) |
| `kafka-topics.md` | `docs/kafka-topics.md` | moved, content edited |
| `loyalty-and-membercard-diagrams/description.md` | `domains/loyalty-and-membercard/description.md` | moved, content edited |
| `loyalty-and-membercard-diagrams/domain-overview.md` | `domains/loyalty-and-membercard/domain-overview.md` | moved, unchanged |
| `loyalty-and-membercard-diagrams/loyalty-membercard-hld.drawio` | `domains/loyalty-and-membercard/loyalty-membercard-hld.drawio` | byte-identical (sha256 16b6c5f6bde0) |
| `loyalty-and-membercard-diagrams/loyalty-membercard-lld.drawio` | `domains/loyalty-and-membercard/loyalty-membercard-lld.drawio` | byte-identical (sha256 f654772269eb) |
| `loyalty-and-membercard-diagrams/loyalty-membercard-overview.drawio` | `domains/loyalty-and-membercard/loyalty-membercard-overview.drawio` | byte-identical (sha256 ac5ed7cfef40) |
| `notification-diagrams/.$notification-hld.drawio.bkp` | — | REMOVED (draw.io lock/autosave file) |
| `notification-diagrams/description.md` | `domains/notification/description.md` | moved, content edited |
| `notification-diagrams/domain-overview.md` | `domains/notification/domain-overview.md` | moved, unchanged |
| `notification-diagrams/notification-hld-script.md` | `domains/notification/notification-hld-script.md` | moved, links rewritten |
| `notification-diagrams/notification-hld.drawio` | `domains/notification/notification-hld.drawio` | byte-identical (sha256 abeb7605f5e7) |
| `notification-diagrams/notification-lld.drawio` | `domains/notification/notification-lld.drawio` | byte-identical (sha256 ebbe355f610f) |
| `notification-diagrams/notification-overview.drawio` | `domains/notification/notification-overview.drawio` | byte-identical (sha256 1ca2925ac6e6) |
| `overview-diagrams/.$mfg-eplatform-hld.drawio.bkp` | — | REMOVED (draw.io lock/autosave file) |
| `overview-diagrams/.$mfg-eplatform-shld.drawio.bkp` | — | REMOVED (draw.io lock/autosave file) |
| `overview-diagrams/description.md` | `domains/platform-overview/description.md` | moved, content edited |
| `overview-diagrams/domain-overview.md` | `domains/platform-overview/domain-overview.md` | moved, links rewritten |
| `overview-diagrams/mfg-eplatform-hld.drawio` | `domains/platform-overview/mfg-eplatform-hld.drawio` | byte-identical (sha256 f0a42936ac25) |
| `overview-diagrams/mfg-eplatform-overview.drawio` | `domains/platform-overview/mfg-eplatform-overview.drawio` | byte-identical (sha256 c1e28aaacaa0) |
| `overview-guideline.md` | `docs/overview-guideline.md` | moved, content edited |
| `payment-domain-diagrams/.$payment-billing-hld.drawio.bkp` | — | REMOVED (draw.io lock/autosave file) |
| `payment-domain-diagrams/description.md` | `domains/payment-and-billing/description.md` | moved, content edited |
| `payment-domain-diagrams/domain-overview.md` | `domains/payment-and-billing/domain-overview.md` | moved, unchanged |
| `payment-domain-diagrams/payment-billing-hld-script.md` | `domains/payment-and-billing/payment-billing-hld-script.md` | moved, links rewritten |
| `payment-domain-diagrams/payment-billing-hld.drawio` | `domains/payment-and-billing/payment-billing-hld.drawio` | byte-identical (sha256 65878d7a430a) |
| `payment-domain-diagrams/payment-billing-lld.drawio` | `domains/payment-and-billing/payment-billing-lld.drawio` | byte-identical (sha256 7d94a34f3a8e) |
| `payment-domain-diagrams/payment-overview.drawio` | `domains/payment-and-billing/payment-overview.drawio` | byte-identical (sha256 94e76ae9dca5) |
| `platform-concept.md` | `docs/platform-concept.md` | moved, content edited |
| `voucher-and-campaign-diagrams/description.md` | `domains/voucher-and-campaign/description.md` | moved, content edited |
| `voucher-and-campaign-diagrams/domain-overview.md` | `domains/voucher-and-campaign/domain-overview.md` | moved, unchanged |
| `voucher-and-campaign-diagrams/voucher-campaign-hld.drawio` | `domains/voucher-and-campaign/voucher-campaign-hld.drawio` | byte-identical (sha256 7750c974da83) |
| `voucher-and-campaign-diagrams/voucher-campaign-lld.drawio` | `domains/voucher-and-campaign/voucher-campaign-lld.drawio` | byte-identical (sha256 eaf895fb230e) |
| `voucher-and-campaign-diagrams/voucher-campaign-overview.drawio` | `domains/voucher-and-campaign/voucher-campaign-overview.drawio` | byte-identical (sha256 ee05046c1595) |
| `wallet-diagrams/.$wallet-hld.drawio.bkp` | — | REMOVED (draw.io lock/autosave file) |
| `wallet-diagrams/description.md` | `domains/wallet/description.md` | moved, content edited |
| `wallet-diagrams/domain-overview.md` | `domains/wallet/domain-overview.md` | moved, unchanged |
| `wallet-diagrams/wallet-hld-script.md` | `domains/wallet/wallet-hld-script.md` | moved, links rewritten |
| `wallet-diagrams/wallet-hld.drawio` | `domains/wallet/wallet-hld.drawio` | byte-identical (sha256 1a3a3aa4a68f) |
| `wallet-diagrams/wallet-lld.drawio` | `domains/wallet/wallet-lld.drawio` | byte-identical (sha256 96bbf9b6716d) |
| `wallet-diagrams/wallet-overview.drawio` | `domains/wallet/wallet-overview.drawio` | byte-identical (sha256 0528cc9e6faa) |
