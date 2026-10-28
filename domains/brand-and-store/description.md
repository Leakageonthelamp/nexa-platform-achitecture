# Brand & Store

Brand & Store is which brand, which store, and whether it is open. One Go engine owns the brand, the store, the group, the hours, and the trade zone. TPC, SW, BC, and the rest are rows in that stack, not separate deployments.

Admin writes. Shoppers only read. `admin-bff` is the only write door, and it needs a store-manager role or a manage-store grant. There is no store portal and no Store BFF. Azure AD and the grant live in Admin & Partner. This engine never calls Azure.

Open-now is not stored. A reader derives it from hours, status, and the current time. The zone is a PostGIS polygon that answers which store serves a point. Delivery fee and fleet are not part of that polygon.

| | |
| --- | --- |
| **Owns** | Brand identity and the live flag. Store, optional group, address, hours, status, and zone. |
| **Does not own** | The menu, the delivery fee, payment keys, or admin login. |
| **How it is called** | `PublishBrand` and store writes (`UpsertStore`, hours, zone) are gRPC. Shoppers call `ResolveStore` and `ListNearest`. Those reads publish nothing. |
| **Kafka** | Publishes `brand.changed` and `store.changed` (compacted, after the Postgres commit). No command topic. The master feed (BSL, Excel, S3) is a worker inside the engine. |

## v3 additions: brand configuration

Baseline v3 (2026-10-24) proposes that Brand & Store also owns each brand's **feature switches** (which capabilities the brand has turned on) and its **onboarding state** (draft, configured, ready, testing, live). It does not own other domains' settings: each domain owns its own per-brand slice. A new brand is mostly configuration, and a readiness check reads each owner before the live flag turns on. See [`brand-configuration.md`](../../docs/design/brand-configuration.md). The HLD does not show this yet (see [`architecture.md` §14](../../docs/architecture.md#14-known-drift)).
## v-next (2026-10-25): table registry for postpaid ordering (proposal)

Brand & Store would also own the **table registry** (`store_table`: table, label, active flag) and the **QR key version** for postpaid QR table ordering, plus the brand and store switch `postpaid_table_ordering`. It adds `ResolveTable` (verifies the signed QR and returns the table and store facts), `ListTables`, `UpsertTable`, and `RotateTableKey`. It does not own the table session or the tab: Cart & Order does, so the one-owner rule holds. Design: [`postpaid-table-ordering.md`](../../docs/design/postpaid-table-ordering.md) (P-44, P-45). The HLD does not show this yet.

## Diagrams

**Overview** — `brand-store-overview.drawio`

`domain-overview.md` is the plain reading of the HLD and the LLD. Read that instead of the overview page.

Writing a store, finding one that is open, telling Catalog and Delivery, and the import. A solid line is another domain asking. A dashed line is Kafka. Not a replacement for the SHLD. The rulebook is [`overview-guideline.md`](../../docs/overview-guideline.md).

**SHLD** — `brand-store-shld.drawio` *(not yet drawn: this file is not in the repo)*

Who writes and who only reads, what this domain keeps, and how a new store reaches menus and delivery.

**HLD** — `brand-store-hld.drawio`

One page: the write door, the two reads, the two facts, and who consumes them (Catalog and Delivery).

**LLD** — `brand-store-lld.drawio`

| Page | Flow |
| --- | --- |
| 1 | UpsertStore |
| 2 | ResolveStore |
| 3 | ListNearest |
| 4 | Import worker |
| 5 | PublishBrand |
