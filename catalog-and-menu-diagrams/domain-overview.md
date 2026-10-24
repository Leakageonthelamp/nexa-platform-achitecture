# Catalog & Menu — system overview

Plain reading of [`catalog-menu-hld.drawio`](catalog-menu-hld.drawio) and [`catalog-menu-lld.drawio`](catalog-menu-lld.drawio).
Ownership stays in [`description.md`](description.md).

<!-- ai:anchor:sentence -->
## Sentence

The menu, the price, and the sold-out flag. Staff publish and wait. Shoppers only read. A published menu and a sold-out change leave as messages after the commit.

<!-- ai:anchor:features -->
## Features

### Publish
- **Contact:** Staff ask
- **Technology:** gRPC
- **From:** HLD Menu version · LLD PublishMenu
- A draft becomes a menu that never changes
- The message carries the version, not the whole menu
- A reader asks for that version
- A price from the store feed waits for the next publish

### Sold out
- **Contact:** Kafka from the store
- **Technology:** Kafka
- **From:** HLD Sold-out · LLD Sold-out, brand.changed and store.changed
- The point of sale marks an item sold out
- The flag sits outside the menu version
- A brand or store change only hides or shows this domain’s own menus
- It does not keep a copy of the store

### Read
- **Contact:** Customers read
- **Technology:** gRPC
- **From:** HLD GetMenu · LLD GetMenu
- Shoppers, guests, and partners read the same menu
- The menu for a version never changes, so it can be cached
- Sold-out is added on top at read time
- Nobody writes through this door

### Price
- **Contact:** Orders ask
- **Technology:** gRPC
- **From:** HLD PriceLines · LLD PriceLines
- Checkout asks for the price of each line
- A sold-out line is rejected
- Orders store the prices they were given
- This domain does not own the order

<!-- ai:anchor:shared -->
## Shared

**The menu version** — published once, then never edited

On the bar: the item, the modifiers, the price book, and the sold-out flag. A draft is private. The feed owns the store code and the base price. Staff own the name, the picture, and the category.

<!-- ai:anchor:neighbours -->
## Neighbours

- **Staff** — solid, both ends, `asks`. Publish a menu, or mark sold out by hand.
- **Customers** — solid, both ends, `asks`. Read a menu. Guests and partners use the same read.
- **Orders** — solid, both ends, `asks`. The price of each line at checkout.
- **Voucher** — solid, one way, `asks`. The item list, only when a rule names items.
- **Brand & Store** — solid, both ends, `asks`. A live check that the brand and the store exist, at create time.
- **The store** — dashed into this domain, `Kafka`. Sold out, and a brand or store change.
- **Partners** — dashed out, `Kafka`. A new menu version, and a sold-out change.
- **Nightly check** — solid, `inside Catalog`. Technology: Daily job. A scheduled menu goes live every minute. Sold-out flags restore every five minutes.

<!-- ai:anchor:infrastructure -->
## Infrastructure

- **Aurora PostgreSQL** — The menu, the price book, and the sold-out flag.
- **Valkey** — The menu for a version, and the sold-out set. A miss reads the database.
- **S3** — Item pictures. The browser uploads them. This domain stores the key.
- **Kafka** — The dashed lines run on this.

No search engine. A store menu is small enough to read as it is.

<!-- ai:anchor:not-here -->
## Not here

The store’s hours and zone, the cart, the charge, and who may sign in.
