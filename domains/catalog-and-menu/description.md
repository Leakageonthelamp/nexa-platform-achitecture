# Catalog & Menu

Catalog & Menu is what a store sells. One Go engine owns the SKU, modifiers, the menu version, and the sold-out flag. The master feed owns `pos_code` and the base price. Brand & Store owns the brand, the store, and the hours. Catalog keeps only `brand_id` and `store_id`, checked live when a row is created.

Admin writes the draft. Publish emits the facts. Shoppers and aggregators only read a published menu. A menu version is immutable once published, so a half-edited draft never reaches a shopper, and a lunch menu can go live at a set time. Sold-out sits outside the version: it is a flag per store and SKU, and it can restore itself.

| | |
| --- | --- |
| **Owns** | SKU, modifier groups, price book, menu draft and published version, sold-out flag. |
| **Does not own** | The store, the order, or the price on an order. Cart & Order calls `PriceLines` at checkout and stores the lines it was given. |
| **How it is called** | `admin-bff` is the only write door (draft, publish, sold-out). `customer-bff`, `guest-bff`, and `partner-adapter` call `GetMenu`. Cart & Order calls `PriceLines`. Voucher calls `ListSkus` when a rule names items. |
| **Kafka** | Consumes `catalog.requested` (sold-out from the BSL POS, via `partner-adapter`), `brand.changed`, and `store.changed`. Publishes `catalog.menu.published` and `catalog.availability.changed`. The master feed is a worker, not a topic. |

## Diagrams

**Overview** — `catalog-overview.drawio`

`domain-overview.md` is the plain reading of the HLD and the LLD. Read that instead of the overview page.

Draft, publish, sold out, and reading the menu. A solid line is another domain asking. A dashed line is Kafka. Not a replacement for the SHLD. The rulebook is [`overview-guideline.md`](../../docs/overview-guideline.md).

**SHLD** — `catalog-menu-shld.drawio` *(not yet drawn: this file is not in the repo)*

Who reads and writes the menu, how a menu goes live and an item sells out, and the choices to publish prices together and not copy the store.

**HLD** — `catalog-menu-hld.drawio`

One page: the draft and publish path, sold-out, `GetMenu`, `PriceLines`, `ListSkus`, and the facts that leave after commit. This is the layout the other domain HLDs copy.

**LLD** — `catalog-menu-lld.drawio`

| Page | Flow |
| --- | --- |
| 1 | PublishMenu |
| 2 | Sold-out |
| 3 | GetMenu |
| 4 | PriceLines |
| 5 | `brand.changed` and `store.changed` |
| 6 | ListSkus |
