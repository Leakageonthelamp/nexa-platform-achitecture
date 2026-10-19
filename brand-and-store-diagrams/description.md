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

## Diagrams

**Overview** — `brand-store-overview.drawio`

`domain-overview.md` is the plain reading of the HLD and the LLD. Read that instead of the overview page.

Writing a store, finding one that is open, telling Catalog and Delivery, and the import. A solid line is another domain asking. A dashed line is Kafka. Not a replacement for the SHLD. The rulebook is [`overview-guideline.md`](../overview-guideline.md).

**SHLD** — `brand-store-shld.drawio`

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
