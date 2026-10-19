# Brand & Store HLD — presenter script

Source: [`brand-store-hld.drawio`](brand-store-hld.drawio). About 15 minutes, then questions. Screen-share the diagram and leave it zoomed out until a section says to zoom.

The sentence on the title is the whole talk: **admin writes, Kafka facts, shopper only reads.**

---

## 0. Open (45 seconds)

Point at the title, then the grey subtitle under it.

> Two Go engines. Brand Engine owns tenant identity and whether that brand is live. Store Engine owns the store, its group, its hours, and its trade zone.
>
> Azure AD and the store-manager role live in Identity. Neither engine talks to Azure. Admin BFF is the only write door. There is no store portal and no Store BFF.
>
> Every hop carries `brand_id`. TPC, SW, BC, and the rest are rows in one stack. We do not stand up a stack per brand.

Pause. Four colored pills under the subtitle are the legend. Walk them left to right, once:

1. Orange — gRPC. Writes, and the two reads the client waits on: `ResolveStore` and `ListNearest`.
2. Teal — JWKS / HTTP. Kong is the only policy enforcement point. Identity owns the Azure AD call.
3. Purple — one Kafka command: `store.import.requested`, from BSL, Excel, or S3.
4. Green — Kafka facts. They leave only after a Postgres commit.

> If a line is not one of those four, it is not a path we support.

---

## 1. Edge — who is allowed in (3 minutes)

Zoom to the teal lane, **1. Edge**. Point at Kong.

> Cloudflare and Kong sit in front. Kong is the only PEP. PEP means policy enforcement point: the one place a request is allowed through or stopped.
>
> Kong does not decide who a person is. Azure AD did that at login, and Identity owns that call. Kong enforces the result on the way in: a request with a token Kong cannot verify never reaches a BFF. The store-manager role or the manage-store grant is still checked later, by Admin BFF, from the headers Kong injected.
>
> Nothing behind Kong is a second gate. Admin BFF, guest-bff, customer-bff, and both engines do not call Azure, and they do not validate the token again. If Kong admitted the request, they trust it.

Point at Azure AD (dashed box).

> Admin MFA happens here. Identity owns that call. Brand Engine and Store Engine never dial Azure.

Point at Kong again.

> Enforcement, on the wire: Kong checks the token with JWKS, strips `Authorization` so the raw token dies at the edge, and injects three headers: `X-Principal-Id`, `X-Roles`, `X-Brand-Id`. Downstream reads those headers. It does not re-read the JWT. A grant change shows up on the next token Kong accepts, not by an engine calling Azure.

Point at the three BFFs.

> **admin-bff** is the only write door. It needs a store-manager role or a manage-store grant. The writes are `PublishBrand`, `UpsertStore`, hours, and zone.
>
> **customer-bff** is read only. It has a JWT, `X-Minor-Id`, and `X-Brand-Id`. It calls `ResolveStore` and `ListNearest`. It never writes.
>
> **guest-bff** is also read only, and it is not logged in. No `minor_id`. The brand comes from the app. It only calls `ListNearest` with lat and lng.

Point at the grey note in the lane.

> No store portal. No Store BFF. Guest and customer only read.

---

## 2. The only command (2 minutes)

Zoom to the purple lane, **2. Kafka commands**.

> This lane is a feed. Catalog, Order, and Payment never publish here.

Point at Master feed, then the topic, then Import consumer.

> BSL from POS, or an Excel or CSV dropped through an S3 adapter. Every row has a `brand_id`.
>
> The topic is `store.import.requested`. Key is `brand_id:store_id`.
>
> The import consumer applies the row only if its version is newer. A bad row goes to the dead letter. It does not block the rest of the file.

> Admin writes and this feed are the only two ways a store changes. The feed is the only Kafka command in the domain.

---

## 3. Brand Engine (3 minutes)

Zoom to the green **Brand Engine** lane. Say the lane title.

> Source of truth for tenant identity and one flag: is this brand live?

Point at the note under the lane title.

> Identity owns Azure, the role, and the grant. Brand Engine reads the headers Kong already admitted. It never mints a session.

Point at the Brand box.

> A brand is identity, `live?`, and a version. No payment keys. No menu. Those belong to other domains. We will hit that box at the end.

Point at Tenancy, then the four pills TPC, SW, BC, ETC.

> Shared topics. The Kafka key is `brand_id`. Those names are rows, not deployments.

Point at Version.

> Version is monotonic per `brand_id`. Each `PublishBrand` commits `version + 1`, and `brand.published` carries that number. A consumer applies the fact only if it is newer. The same `(brand_id, version)` is a no-op.

Do not open Store Engine yet. One sentence to plant the dependency:

> Store Engine reads `live` from here. If the brand is not live, store writes reject and shopper reads omit that brand. The store rows stay.

---

## 4. Store Engine (4 minutes)

Zoom to the yellow **Store Engine** lane. Say the lane title.

> Source of truth for the store, its hours, and its zone. It is an API, a consumer, a worker, and a cron.

Point at Store.

> One store, one `brand_id`. A group is optional. We store address, lat/lng, and whether it does delivery, dine-in, and pickup.

Point at Store group.

> Many stores, still one `brand_id`. A store joins at most one group. The group key is `brand_id:group_id`. Site is a field on the store. Site is not a stack.

Point at Hours + status, then Lifecycle.

> Weekly hours plus a temporary close. Lifecycle is Draft, Open, Paused, Hidden, Closed.
>
> Open-now is not a column. A cron derives it from hours and status, then emits `store.availability.changed`.

Point at Trade zone.

> A PostGIS polygon. It answers which store serves a point. That is the zone. Delivery fee, fleet, and hub are not this polygon.

Point at Who may write, then Contract.

> The engine trusts headers. Admin BFF is the one that checks the Identity snapshot: store-manager role or manage-store grant.
>
> Contract, in one line: Admin BFF writes. Guest and customer BFFs read `ResolveStore` and `ListNearest`. Facts go out after the commit. Import is the only command.

Point at the store Version box.

> Same rule as brand, scoped to `(brand_id, store_id)`. Every write bumps the version. Facts and `store.snapshot` carry it. Apply only if newer. An admin version beats an older feed row.

Point at the `brand.published` effects note.

> A newer `brand.published` is the only brand fact Store Engine acts on.
>
> Live: Catalog shows the brand, store writes are accepted, shopper reads turn on.
>
> Not live: Catalog hides it, writes reject, reads omit it. We do not delete the store rows.

---

## 5. Where the bytes land (2 minutes)

Stay zoomed out enough to see Postgres, Redis, and the two Kafka boxes under the engines.

Point at PostgreSQL · PostGIS.

> Commit happens here before any fact. Brand Engine stores brand, version, and `live?`. Store Engine stores store, version, hours, and the zone polygon.

Point at Redis.

> Hot path only: `ResolveStore`, `ListNearest`, open-now, and a zone hit. Redis is a cache. Postgres is the source of truth.

Point at Kafka facts out.

> Brand fact: `brand.published`. Key is `brand_id`, and it carries version.
>
> Store facts, after the commit: `store.upserted`, group, hours, status, zone, availability. Store key is `brand_id:store_id`. Group key is `brand_id:group_id`. Each fact carries version.

Point at `store.snapshot`.

> Compacted. Latest value per key. A new consumer rebuilds from this topic, then Ack. It does not replay `store.upserted`.

---

## 6. Who listens (2 minutes)

Zoom to the dashed lane, **Who consumes**.

> Every consumer is idempotent on version. Apply only if newer.

Point at each box:

> **Catalog** takes `brand.published`, `store.upserted`, and `store.status.changed`. Menu and SKU stay in Catalog. It only learns that the brand and the store exist and whether the store is in a state it should show.
>
> **Order** takes `store.upserted`, `store.status.changed`, and `store.availability.changed`. It needs to know the store is there and whether it can take an order right now.
>
> **Delivery** takes `store.zone.updated` and `store.upserted`. It does not take fee, fleet, or hub from us.
>
> **Our own cache projector** takes every fact and writes Redis, so `ResolveStore` stays hot.

---

## 7. What this diagram refuses (1 minute)

Point at the three grey boxes: Not this domain, Identity & Access, Left behind.

> Catalog owns menu and SKU. Delivery owns fee, fleet, and hub. Identity owns Azure, the role, and the grant. Payment owns gateway keys.
>
> The `roles[]` inside a JWT is a snapshot. Neither engine refreshes it. If the grant changes, that shows up on the next token, not by us calling Azure.
>
> We are not carrying forward Redbook’s Laravel reads, Mongo trade zones, or RabbitMQ.

---

## 8. Close (30 seconds)

Zoom back to the title.

> Admin writes through one door. A feed is the only command, and a newer version wins. Postgres commits, then a fact goes out. Shoppers only read, and they read a cache that was built from those facts.
>
> One stack. `brand_id` on every hop. Brands are rows.

Stop talking. Take questions.

---

## If they ask

Answer from the diagram. If it is not on the page, say it is not decided here.

**Why no Store BFF?**
Admin BFF is the only write door. Guest and customer already have BFFs, and both are read only. A store portal would be a second writer.

**Who checks the store-manager role?**
Admin BFF, against the Identity snapshot in the headers. Store Engine trusts `X-Roles`. It does not call Azure, and it does not mint a session.

**What if the feed and an admin edit race?**
Version. Admin bumps `(brand_id, store_id)`. The import applies only if its version is newer, so an older feed row loses to the admin write.

**What if a consumer crashes?**
Same rule. Re-delivery of the same `(id, version)` is a no-op. A brand-new consumer does not replay history. It reads compacted `store.snapshot`, latest per key, then Ack.

**What is open-now?**
Derived. Hours plus status plus the cron. It is not a stored flag. The cron emits `store.availability.changed`.

**What happens when we turn a brand off?**
A newer `brand.published` with live false. Catalog hides the brand. Store writes reject. Shopper reads omit it. Store rows stay in Postgres.

**Can guest resolve a specific store?**
No. Guest calls `ListNearest` with lat and lng. `ResolveStore` is on the customer path.

**Where do payment keys and the menu live?**
Not here. Payment owns gateway keys. Catalog owns menu and SKU.
