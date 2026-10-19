# Brand & Store — system overview

Plain reading of [`brand-store-hld.drawio`](brand-store-hld.drawio) and [`brand-store-lld.drawio`](brand-store-lld.drawio).
Ownership stays in [`description.md`](description.md).

<!-- ai:anchor:sentence -->
## Sentence

The brand, the store, the hours, and the zone. Staff write and wait. Shoppers and checkout only read. A change leaves as a message after the commit.

<!-- ai:anchor:features -->
## Features

### Write
- **Contact:** Staff ask
- **Technology:** gRPC
- **From:** HLD PublishBrand and UpsertStore · LLD UpsertStore, PublishBrand, Import worker
- Create or hide a brand
- Edit a store: address, hours, status, zone, or group
- A file of stores is read inside this service, row by row
- A bad row does not blank a live store

### One store
- **Contact:** Orders and customers ask
- **Technology:** gRPC
- **From:** HLD Reads · LLD ResolveStore
- Whether this store can take an order right now
- Open-now is worked out at read time
- Checkout keeps no copy
- A hidden, closed, or not-live store is a reject

### Nearest
- **Contact:** Customers and guests read
- **Technology:** gRPC
- **From:** HLD Reads · LLD ListNearest
- Which stores serve this point
- A guest needs no account
- A short cache absorbs the lunch peak
- The zone, not a stored “open now” flag, decides

<!-- ai:anchor:shared -->
## Shared

**The store book** — one brand, many stores, each store in at most one group

On the bar: the brand, the store, hours, status, and the zone. Open-now is hours plus status plus the current time. It is not stored.

<!-- ai:anchor:neighbours -->
## Neighbours

- **Staff** — solid, both ends, `asks`. Publish a brand, or edit a store.
- **Orders** — solid, both ends, `asks`. One store, live, at checkout.
- **Customers** — solid, both ends, `asks`. One store, or the nearest stores.
- **Catalog** — dashed out, `Kafka`. A brand change and a store change.
- **Delivery** — dashed out, `Kafka`. A store change, for the catchment only.

No message comes in. The file import is a worker inside this service.

<!-- ai:anchor:infrastructure -->
## Infrastructure

- **Aurora PostgreSQL** — The brand, the store, the hours, and the zone.
- **Valkey** — A hot read of one store and of the nearest stores. Filled after the commit. Not the truth.
- **Kafka** — The dashed lines run on this.

A file of stores is applied inside this service. It is not a message, and it is not a second copy of the store.

<!-- ai:anchor:not-here -->
## Not here

The menu, the price, the order, the delivery fee, and who may sign in. There is no store portal.
