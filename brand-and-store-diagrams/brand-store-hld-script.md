# Brand & Store HLD — presenter script

Source: [`brand-store-hld.drawio`](brand-store-hld.drawio). About 12 minutes, then questions. Screen-share the diagram and leave it zoomed out until a section says to zoom.

The sentence on the title is the whole talk: **admin writes, Kafka facts, shopper only reads.**

Topic names on this page are the only two this domain publishes: `brand.changed` and `store.changed`. The full list lives in [`kafka-topics.md`](../kafka-topics.md).

---

## 0. Open (45 seconds)

Point at the title, then the grey subtitle under it.

> One Go engine. It owns the brand, the store, the group, the hours, and the zone.
>
> Azure AD and the store-manager grant live in Admin & Partner. Admin BFF is the only write door. There is no store portal and no Store BFF.
>
> Every hop carries `brand_id`. TPC, SW, BC, and the rest are rows in one stack. We do not stand up a stack per brand.

Pause. Four colored pills under the subtitle. Walk them left to right, once:

1. Orange — gRPC. Writes, and the two reads the client waits on: `ResolveStore` and `ListNearest`.
2. Blue — JWKS and HTTP. Kong is the only policy enforcement point. Admin & Partner owns the Azure AD call.
3. Purple — no Kafka command. The master feed is a worker inside the engine, not a topic.
4. Green — Kafka facts. They leave only after a Postgres commit.

> If a line is not one of those, it is not a path we support.

---

## 1. Edge — who is allowed in (3 minutes)

Zoom to lane **1. Callers**. Point at Kong.

> Cloudflare and Kong sit in front. Kong is the only PEP. PEP means policy enforcement point: the one place a request is allowed through or stopped.
>
> Kong does not decide who a person is. Azure AD did that at login, and Admin & Partner owns that call. Kong checks the token, strips `Authorization`, and injects `X-Principal-Id`, `X-Roles`, and `X-Brand-Id`. Downstream reads those headers. It does not re-read the JWT.

Point at Azure AD (dashed box).

> Admin MFA happens here. This engine never dials Azure.

Point at the three BFFs.

> **admin-bff** is the only write door. It needs a store-manager role or a manage-store grant. The writes are `PublishBrand`, `UpsertStore`, hours, and zone.
>
> **customer-bff** is read only. It calls `ResolveStore` and `ListNearest`.
>
> **guest-bff** is also read only, and it is not logged in. The brand comes from the app. It only calls `ListNearest` with lat and lng.

Point at the note in the lane.

> No store portal. No Store BFF. Guest and customer only read.

---

## 2. No command topic (1 minute)

Zoom to the purple lane, **2. Kafka in**.

> This lane is empty on purpose. An admin is waiting on every write, so the write is gRPC.
>
> The master feed — BSL, Excel, or a file on S3 — is a worker inside this engine. It reads the file. Nothing else consumes that file, so a topic would be a queue with one reader.
>
> A feed row older than the admin version is dropped. A bad row is dead-lettered inside the worker and does not blank a live store.

---

## 3. The engine (4 minutes)

Zoom to the yellow lane, **3. Brand & Store**.

> One service. Brand is identity, `live?`, and a version. No payment keys and no menu. Store is one `brand_id`, an optional group, the address, the hours, and the zone.

Point at Store group, then Hours, then Zone.

> Many stores, still one brand. A store joins at most one group. Site is a field on the store, not a stack.
>
> Hours are a weekly schedule plus a temporary close. Open-now is not a column and not a topic. A reader derives it from hours, status, and now.
>
> The zone is a PostGIS polygon. It answers which store serves a point. Delivery fee, fleet, and hub are not this polygon.

Point at Version, then the two orange write boxes.

> Version is monotonic. `PublishBrand` bumps it for the brand. A store write bumps it for `(brand_id, store_id)`. A consumer applies the fact only if it is newer. The same version is a no-op.
>
> Both writes are gRPC, on Admin BFF. The shopper reads are also gRPC, and they publish nothing.

Point at the note under the boxes.

> Valkey is filled in-process after the commit. This service does not consume its own facts.

---

## 4. Facts out (2 minutes)

Zoom to the green lane, **4. Facts out**.

> Two topics. Both compacted.
>
> `brand.changed`. Key is `brand_id`. It carries `live?` and the version.
>
> `store.changed`. Key is `brand_id:store_id`. Hours, status, zone, and `group_id` ride on this one fact. There is no snapshot topic beside it. A new consumer reads the latest value per key, then Ack.

---

## 5. Who listens (2 minutes)

Zoom to **5. Consumers**.

> Each box reads the topic itself, then Ack. Apply only if the version is newer.
>
> **Catalog** takes both facts. A brand that is not live is hidden. The store rows stay.
>
> **Delivery** takes `store.changed` for the catchment. It does not take fee, fleet, or hub from us.

---

## 6. Where the bytes land (1 minute)

Point at **6. Data**, then **Decisions**.

> Commit happens in Postgres before any fact. PostGIS holds the polygon. Valkey is the hot path for `ResolveStore` and `ListNearest`. Postgres is the source of truth.
>
> One engine, not two. Two topics, not nine. No open-now cron. The import is a worker. The outbox is in the app: no Debezium and no Kafka Connect cluster.

---

## 7. What this diagram refuses (1 minute)

Point at **Not this domain**.

> Catalog owns menu and SKU. Order owns the cart and the POS ticket. Delivery owns fee, fleet, and hub. Admin & Partner owns Azure, the role, and the grant. Payment owns gateway keys.
>
> We are not carrying forward Redbook’s Laravel reads, Mongo trade zones, or RabbitMQ.

---

## 8. Close (30 seconds)

Zoom back to the title.

> Admin writes through one door. The feed is a worker, and a newer version wins. Postgres commits, then two facts go out. Shoppers only read.
>
> One stack. `brand_id` on every hop. Brands are rows.

Stop talking. Take questions.

---

## If they ask

Answer from the diagram. If it is not on the page, say it is not decided here.

**Why no Store BFF?**
Admin BFF is the only write door. Guest and customer already have BFFs, and both are read only. A store portal would be a second writer.

**Who checks the store-manager role?**
Admin BFF, against the headers Kong injected. The engine trusts `X-Roles`. It does not call Azure, and it does not mint a session.

**What if the feed and an admin edit race?**
Version. The admin bumps `(brand_id, store_id)`. The worker applies a feed row only when its version is newer, so an older file loses.

**What if a consumer crashes?**
Same rule. Re-delivery of the same version is a no-op, then Ack. A new consumer does not replay history. It reads the latest compacted value per key.

**What is open-now?**
Derived. Hours plus status plus now. It is not stored and it is not a fact we publish.

**What happens when we turn a brand off?**
A newer `brand.changed` with live false. Catalog hides the brand. Store writes reject. Shopper reads omit it. Store rows stay in Postgres.

**Can a guest resolve a specific store?**
No. Guest calls `ListNearest` with lat and lng. `ResolveStore` is on the customer path, and Order calls it at checkout.

**Where do payment keys and the menu live?**
Not here. Payment owns gateway keys. Catalog owns menu and SKU.
