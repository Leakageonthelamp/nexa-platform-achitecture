# Catalog & Menu HLD — presenter script

Source: [`catalog-menu-hld.drawio`](catalog-menu-hld.drawio). About 12 minutes, then questions. Screen-share the diagram and leave it zoomed out until a section says to zoom.

The sentence on the title is the whole talk: **admin writes the draft, publish emits the facts, shoppers only read.**

This domain owns three topics: `catalog.requested`, `catalog.menu.published`, and `catalog.availability.changed`. The full list lives in [`kafka-topics.md`](../kafka-topics.md).

---

## 0. Open (45 seconds)

Point at the title, then the grey subtitle.

> One Go engine. Catalog owns the SKU, modifiers, the menu version, and the sold-out flag. The feed owns `pos_code` and the base price. Brand & Store owns brand, store, and hours.
>
> Catalog keeps only `brand_id` and `store_id`, checked live at create. Admin BFF is the only write door.

Walk the four pills once:

1. Orange — gRPC. Writes, `GetMenu`, `PriceLines`, and the brand lookup. The client waits.
2. Blue — JWKS and HTTP. Kong is the PEP. Admin & Partner owns the Azure AD call.
3. Purple — one command, `catalog.requested`.
4. Green — facts, only after the Postgres commit.

---

## 1. Callers (2 minutes)

Zoom to **1. Callers**.

> Cloudflare, then Kong. Kong checks JWKS and injects `X-Principal-Id` and `X-Roles`. Azure AD keeps MFA, and Catalog never calls it.
>
> **admin-bff** is the only write door. It needs menu-manager or manage-menu for draft, publish, and sold-out.
>
> **customer-bff** and **guest-bff** are read only. They call `GetMenu` and never write.
>
> The **partner-adapter** reads `GetMenu` for Grab, LINE MAN, and Shopee Food. It never writes.

> No menu portal. Guest and customer only read.

---

## 2. Kafka in (1 minute)

Zoom to **2. Kafka in**.

> One command: sold-out. The BSL POS webhook lands at the partner-adapter, which publishes `catalog.requested`, keyed `brand_id:store_id:sku_id`.
>
> The master feed (BSL, Excel, or S3) is a worker inside Catalog that writes the draft. Nobody else consumes the file, so it is not a topic.

---

## 3. The engine (4 minutes)

Zoom to **3. Catalog Engine**.

> **Lookup at create** asks Brand & Store over gRPC. The result is a foreign key on `brand_id` and `store_id`, not a copy. An unknown id is rejected.
>
> **Who may write**: Admin BFF checks the grant, and the engine trusts `X-Roles`.
>
> **SKU ownership is split.** The feed owns `pos_code`, the POS name, and the price. The admin owns name, image, and category. The worker writes the feed fields.

Point at Menu draft, Modifier group, Price book, and Menu version.

> A draft is one brand and one channel, private until publish. Modifier groups have min, max, required, and a price delta, checked at publish and at `PriceLines`. The price book (base, store, channel) is frozen into the version.
>
> A menu version is immutable once published: draft, scheduled, published, superseded. It is not an offline copy. It means shoppers and aggregators only ever see a complete, approved menu, a lunch menu can go live at 11:00, and the cache keyed by version is never stale.

Point at the outbox relay and the crons.

> State and outbox commit together, and the fact leaves after the commit. One cron runs every minute for scheduled publish, and one every five minutes restores sold-out items.

Point at **PriceLines** and **GetMenu**.

> Cart & Order calls `PriceLines` at checkout and stores the price lines it was given. That is the order's record of what the shopper paid, not a copy of the menu. `GetMenu` is read only.

Point at **Sold-out**.

> Sold-out is a flag per store and SKU, outside the menu version, with an optional auto-restore time. The consume ends in an Ack.

---

## 4. Facts out (1 minute)

Zoom to **4. Facts out**.

> `catalog.menu.published` is thin: the version only. The consumer calls `GetMenu`, because a menu can pass Kafka's 1 MB default.
>
> `catalog.availability.changed` is the sold-out fact. It does not republish the menu.

---

## 5. Consumers (1 minute)

Zoom to **5. Consumers**.

> The partner-adapter pushes the menu and toggles items. The cache projector fills Valkey, for Catalog only. The S3 data lake sinks both facts.
>
> Idempotent on version: apply only if newer, then Ack.

---

## 6. Data, decisions, not this domain (2 minutes)

> Aurora holds SKU, modifier, draft, version, sold-out, outbox, and audit. Valkey holds the menu JSON keyed by version, plus the current pointer and the sold-out set. Images are a presigned PUT to S3, served from the Cloudflare CDN.
>
> No OpenSearch. A store menu is under 1,000 items.

Read the bold words in **Decisions**, then **Not this domain**: Brand & Store, Order, Payment, Identity, Voucher (which calls `ListSkus`), Inventory (not built), and the aggregators behind the partner-adapter.

---

## 7. Close (30 seconds)

> Admin writes a draft. Publish freezes a version and sends a thin fact. Sold-out moves on its own topic. Shoppers only read.

Stop talking. Take questions.

---

## If they ask

**Why is the menu fact thin?**
A full menu can pass 1 MB. The version never changes, so `GetMenu(version)` is a cache hit.

**Why is sold-out a separate topic?**
It changes far more often than menus, and it must not republish the menu.

**What if the feed and the admin edit the same SKU?**
They own different fields. The feed's price waits for the next publish.

**Why not copy the store?**
One owner. Create waits on Brand & Store and fails if it is down. That is the written cost.

**Where is inventory?**
Not built. Sold-out is a flag until a stock count is needed.
