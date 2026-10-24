> **Note (v3, 2026-10-24).** This is a copy of reference notes from Confluence. It names `*-shld.drawio` files. Those SHLD diagrams are **not in this repo** (not yet drawn). The copy is kept unchanged below.

## Identity & Profile

Identity & Profile is the customer. One Go app holds the Minor ID: the login, the customer signing key, the one-time code, the profile, addresses, contacts, and PDPA consent. One account works in every brand. A brand sees another brand's rows only when the customer has opted in to that sharing.

Every caller is waiting, so every door is gRPC. Kong reads the public half of the customer signing key over HTTP. Notification and Delivery read contacts and the drop-off address live. Nobody keeps a copy, and nothing personal is put on the bus.

| | |
| --- | --- |
| Owns | The customer, the login, the customer signing key, OTP generate and verify, addresses, contacts, and PDPA consent. |
| Does not own | Admin or partner identity, message delivery, points, stored value, or saved cards. |
| How it is called | customer-bff signs in, joins a brand, and edits the profile. admin-bff does a support edit or a PDPA delete, after the grant in X-Roles. Notification calls BatchGetContacts. Delivery calls GetAddress. StartSignIn calls Notification SendOtp, because the shopper is waiting. |
| Kafka | None. Identity publishes nothing and consumes nothing. A join is not announced; Loyalty learns the customer from order.events. |

### Super high-level design

identity-customer-shld.drawio

Who holds a Minor ID, what this domain keeps, and how a customer signs up once and then joins a second brand.

### High-level design

identity-customer-hld.drawio

One page: the five doors, the one schema, the tokens, and why there is no command in and no fact out.

### Low-level design

identity-customer-lld.drawio

| Page | Flow |
| --- | --- |
| 1 | StartSignIn |
| 2 | VerifyOtp (sign in or register) |
| 3 | JoinBrand |
| 4 | UpdateProfile |
| 5 | DeleteCustomer |
| 6 | BatchGetContacts and GetAddress |

Address writes, consent writes, and RefreshToken follow the same commit as UpdateProfile. Their pages are still to add.

## Admin & Partner

Admin & Partner decides who may operate the platform, and which partner may call it. Admin owns the principal, the grant, and the session. Partner owns the OAuth client. Kong is the only place a request is allowed through or stopped. This domain is the only one that calls Azure AD.

Login is synchronous. The caller is always waiting, so nothing here is a Kafka topic. The bus never carries a token, a secret, or a client assertion. The audit row in Postgres is the record.

| | |
| --- | --- |
| Owns | Admin principal, role, grant, session, audit. Partner org, OAuth client, scopes, and the partner public key. Two Vault keys: admin-es512 and partner-es512. |
| Does not own | The customer, minor_id, social login, OTP, or the customer signing key. Those stay in Identity. |
| How it is called | Admin login is authorization code + PKCE. A partner token is client_credentials + private_key_jwt. Both are gRPC. A grant change does not rewrite a live JWT. |
| Kafka | None. |

### Super high-level design

admin-partner-shld.drawio

Who may sign in, what this domain grants them, and how a staff sign-in and a partner token work.

### High-level design

admin-partner-hld.drawio

One page: callers, the two engines, and why there is no command in and no fact out.

### Low-level design

admin-partner-lld.drawio

| Page | Flow |
| --- | --- |
| 1 | Admin login |
| 2 | Refresh and revoke |
| 3 | Partner token |
| 4 | Grant change |
| 5 | Register, rotate, or suspend a partner client |

## Brand & Store

Brand & Store is which brand, which store, and whether it is open. One Go engine owns the brand, the store, the group, the hours, and the trade zone. TPC, SW, BC, and the rest are rows in that stack, not separate deployments.

Admin writes. Shoppers only read. admin-bff is the only write door, and it needs a store-manager role or a manage-store grant. There is no store portal and no Store BFF. Azure AD and the grant live in Admin & Partner. This engine never calls Azure.

Open-now is not stored. A reader derives it from hours, status, and the current time. The zone is a PostGIS polygon that answers which store serves a point. Delivery fee and fleet are not part of that polygon.

| | |
| --- | --- |
| Owns | Brand identity and the live flag. Store, optional group, address, hours, status, and zone. |
| Does not own | The menu, the delivery fee, payment keys, or admin login. |
| How it is called | PublishBrand and store writes (UpsertStore, hours, zone) are gRPC. Shoppers call ResolveStore and ListNearest. Those reads publish nothing. |
| Kafka | Publishes brand.changed and store.changed (compacted, after the Postgres commit). No command topic. The master feed (BSL, Excel, S3) is a worker inside the engine. |

### Super high-level design

brand-store-shld.drawio

Who writes and who only reads, what this domain keeps, and how a new store reaches menus and delivery.

### High-level design

brand-store-hld.drawio

One page: the write door, the two reads, the two facts, and who consumes them (Catalog and Delivery).

### Low-level design

brand-store-lld.drawio

| Page | Flow |
| --- | --- |
| 1 | UpsertStore |
| 2 | ResolveStore |
| 3 | ListNearest |
| 4 | Import worker |
| 5 | PublishBrand |

## Catalog & Menu

Catalog & Menu is what a store sells. One Go engine owns the SKU, modifiers, the menu version, and the sold-out flag. The master feed owns pos_code and the base price. Brand & Store owns the brand, the store, and the hours. Catalog keeps only brand_id and store_id, checked live when a row is created.

Admin writes the draft. Publish emits the facts. Shoppers and aggregators only read a published menu. A menu version is immutable once published, so a half-edited draft never reaches a shopper, and a lunch menu can go live at a set time. Sold-out sits outside the version: it is a flag per store and SKU, and it can restore itself.

| | |
| --- | --- |
| Owns | SKU, modifier groups, price book, menu draft and published version, sold-out flag. |
| Does not own | The store, the order, or the price on an order. Cart & Order calls PriceLines at checkout and stores the lines it was given. |
| How it is called | admin-bff is the only write door (draft, publish, sold-out). customer-bff, guest-bff, and partner-adapter call GetMenu. Cart & Order calls PriceLines. |
| Kafka | Consumes catalog.requested (sold-out from the BSL POS, via partner-adapter), brand.changed, and store.changed. Publishes catalog.menu.published and catalog.availability.changed. The master feed is a worker, not a topic. |

### Super high-level design

catalog-menu-shld.drawio

Who reads and writes the menu, how a menu goes live and an item sells out, and the choices to publish prices together and not copy the store.

### High-level design

catalog-menu-hld.drawio

One page: the draft and publish path, sold-out, GetMenu, PriceLines, and the facts that leave after commit. This is the layout the other domain HLDs copy.

### Low-level design

catalog-menu-lld.drawio

| Page | Flow |
| --- | --- |
| 1 | PublishMenu |
| 2 | Sold-out |
| 3 | GetMenu |
| 4 | PriceLines |
| 5 | brand.changed and store.changed |

## Cart & Order

Cart & Order is the checkout. One Go engine owns the cart, the order, and the POS ticket. It runs the saga: price the basket, authorize the payment, send the ticket to the store, then capture after the POS accepts or void if the kitchen rejects.

The shopper waits on gRPC. The bus carries what already happened. Own-app checkout does not enter through Kafka. PlaceOrder takes an idempotency_key, so a double tap never makes two orders. A wallet order runs the same saga: Payment holds the balance at once, so there is no authorize_url. Aggregator orders (Grab, LINE MAN, Shopee Food) skip payment: the partner has already collected the money, and partner-adapter publishes order.requested.

Order does not recompute the price or the delivery fee, and does not keep a copy of the store. At checkout it asks Brand & Store for ResolveStore, Catalog for PriceLines, and Delivery for GetQuote, live.

The cart is lines, not prices. There is one open cart per brand and customer, and GetCart and UpdateCart price it live with PriceLines on every read. PlaceOrder checks out that cart by cart_version and the total the shopper saw. If the live total differs, it returns price_changed, so the shopper never pays a total they did not see. The cart is deleted when its order is placed. A guest cart stays on the device, and aggregator orders have no cart.

| | |
| --- | --- |
| Owns | The cart, the order, the price lines and the delivery fee agreed at checkout, the POS ticket, and the checkout saga. |
| Does not own | The menu price (Catalog), the charge (Payment), the store (Brand & Store), or the quote and the delivery (Delivery). |
| How it is called | customer-bff calls GetCart and UpdateCart, then PlaceOrder with a quote_id for a delivery order. Order calls Brand & Store, Catalog, Delivery, and Payment over gRPC while the shopper waits. Capture and void leave as a command after the POS answers. |
| Kafka | Publishes order.events and payment.requested (capture or void). Consumes order.requested (aggregator create, replace, cancel, POS status), payment.events, and delivery.events (delivered, failed, cancelled). The cart has no topic. |

### Super high-level design

cart-order-shld.drawio

Own-app checkout from the delivery fee and the payment hold through the kitchen ticket and capture, with aggregator orders joining at the kitchen.

### High-level design

cart-order-hld.drawio

One page: the cart, PlaceOrder, the authorize-then-capture saga, the POS worker, and the three consumes.

### Low-level design

cart-order-lld.drawio

| Page | Flow |
| --- | --- |
| 1 | PlaceOrder |
| 2 | payment.events consumer |
| 3 | POS dispatch and status |
| 4 | Checkout sweeper cron |
| 5 | Aggregator create |
| 6 | delivery.events consumer |
| 7 | Cart: GetCart and UpdateCart |

Page 1 is the reference layout for every other LLD page.

## Payment & Billing

Payment & Billing moves the money and writes the paper. One Go engine owns the transaction. Checkout returns authorize_url on the gRPC. Capture, void, and the gateway webhook travel on the bus. A rider payout calls TrueMoney. Statement is a mode of this app, not a second service: after capture it writes the Thai tax invoice and receipt, and it never talks to a gateway.

Food payments are authorized first and captured later. The hold is placed at authorize. Money moves at capture, and only after Order has accepted the POS ticket. A rejection becomes a void. There is one transactions table, one Omise account per brand, and no automatic second gateway.

| | |
| --- | --- |
| Owns | The transaction, the attempt, gateway keys per brand, the invoice, and the receipt. |
| Does not own | The order status, the wallet balance, or the price. Order runs the saga. Wallet owns the stored-value ledger. |
| How it is called | Order calls CreateTransaction at checkout. customer-bff calls it only for a wallet top-up. admin-bff calls refund. Omise and TrueMoney are reached by this engine. They never call it. Webhooks land at webhook-adapter. |
| Kafka | Publishes payment.events (authorized, captured, failed, voided, refunded, paid_out, payout_failed). Consumes payment.requested (capture, void, webhook, payout). Charge and refund stay gRPC, because someone is waiting. |

### Super high-level design

payment-billing-shld.drawio

One page: hold, then capture or release, a refund, and the Thai tax invoice. A wallet spend is a tender behind the payment, a top-up is taken at once, and a partner brand is invoiced when the order is delivered.

### High-level design

payment-billing-hld.drawio

One page: checkout, the command in, the transaction, statement mode, and who consumes payment.events (Order, Wallet, Delivery, Notification).

### Low-level design

payment-billing-lld.drawio

| Page | Flow |
| --- | --- |
| 1 | CreateTransaction |
| 2 | Gateway webhook |
| 3 | Capture and void |
| 4 | Refund |
| 5 | Statement mode |
| 6 | Rider payout |

## Delivery & Dispatch

Delivery & Dispatch is the trip and the rider. One Go app covers dispatch and the rider workforce. One port talks to every fleet: our own riders, the shared pool, ZEEK, and Grab Express. Swapping a provider later is a new package behind that port. One ledger records rider earnings. A payout is real money, so it leaves as a command to Payment, which calls TrueMoney.

Dispatch starts when the kitchen accepts, not when the order is placed. A shopper can ask for a quote while they wait. The quote uses straight-line distance, and Google Maps only when the distance is above a threshold. It does not call the fleet. FAAS brands have no kitchen accept, so partner-bff starts the delivery on CreateDelivery.

Riders use brand_id = mfg, because one pool serves every brand. The delivery itself stays on the order's brand.

| | |
| --- | --- |
| Owns | The delivery, the quote, the fee, the provider job, the rider, the roster, and the earnings ledger. |
| Does not own | The store zone (Brand & Store), the order (Cart & Order), or a real-money payout (Payment). |
| How it is called | customer-bff calls Quote. Order calls GetQuote at PlaceOrder and stores that fee. admin-bff assigns, cancels, redispatches, and approves a rider. Fleet webhooks arrive as delivery.requested through partner-adapter. |
| Kafka | Publishes delivery.events and payment.requested (payout). Consumes order.events, delivery.requested, store.changed, and payment.events. |

### Super high-level design

delivery-dispatch-shld.drawio

Quote, dispatch, tracking, and rider pay: the kitchen accepts, a rider is sent, the trip is delivered, and the rider is paid.

### High-level design

delivery-dispatch-hld.drawio

One page: quote and create, the seven delivery states, the fleet port, and the rider workforce under the same schema.

### Low-level design

delivery-dispatch-lld.drawio

| Page | Flow |
| --- | --- |
| 1 | Quote and GetQuote |
| 2 | Kitchen accepted to dispatch |
| 3 | Provider update |
| 4 | No-rider sweeper |
| 5 | Scheduled dispatch |
| 6 | Cancel |
| 7 | Ops |
| 8 | FAAS create |
| 9 | Store sync |
| 10 | Rider sync |
| 11 | Roster |
| 12 | Earnings |
| 13 | Payout |
| 14 | Workforce admin |
| 15 | End to end |
| 16 | Payout reconcile |

## Wallet

Wallet is stored value. One Go engine holds one wallet per brand per customer, plus an append-only ledger. Available balance is balance minus held. It is not a column. Only a ledger entry moves the balance.

A spend looks like any other tender. Payment calls Hold, Capture, Release, and Refund, the same way it calls Omise. Order, Voucher, and MemberCard never call Wallet. Top-up money stays in Payment: the shopper pays Omise, and Wallet credits the ledger when payment.events says that top-up was captured. Real money never lands here.

| | |
| --- | --- |
| Owns | The wallet per brand and customer, the stored-value ledger, and holds. |
| Does not own | The charge, the card, the order, or loyalty points. |
| How it is called | Payment is the only writer on the checkout path. admin-bff calls Adjust (CSC credit or a correcting debit) with the wallet.adjust grant, a reason, and a limit. customer-bff reads GetWallet and ListEntries. A shopper never writes. |
| Kafka | No wallet topic. Consumes payment.events, and only a captured top-up. Sends notification.requested so Notification can tell the customer. |

### Super high-level design

wallet-shld.drawio

Who uses the stored-value balance, what Wallet does, and how a wallet payment and a top-up run.

### High-level design

wallet-hld.drawio

One page: the four doors (Payment, admin adjust, reads, top-up credit), the ledger, and why nothing is published except a notification. This is the reference for the relation lines on every HLD.

### Low-level design

wallet-lld.drawio

| Page | Flow |
| --- | --- |
| 1 | Hold |
| 2 | Capture and release |
| 3 | Top-up credit |
| 4 | Adjust |
| 5 | Refund to wallet |
| 6 | GetWallet and ListEntries |
| 7 | Reconciliation cron |
| 8 | Pay with wallet, end to end |

## Notification

Notification delivers the message. One Go engine owns the templates, the message log, the in-app inbox, device tokens, and whether a channel can reach that customer. Six channels leave from here: push, SMS, email, LINE, WebSocket, and the inbox.

It does not own the person. Identity owns the phone, the email, the LINE user id, and PDPA consent. Notification reads them over gRPC at send time, so no personal data rides the bus. A domain that already publishes a fact (Order, Payment) is not also asked to send a command. Notification turns those facts into messages. Loyalty, Wallet, and Voucher send notification.requested until they have a fact topic of their own.

Aggregator orders are skipped. Grab, LINE MAN, and Shopee Food already notify their own customer.

| | |
| --- | --- |
| Owns | Templates, the message log, the inbox, device tokens, channel reachability, and brand channel config. |
| Does not own | The contact, the consent, or the OTP code. Identity generates the OTP and calls SendOtp because the shopper is waiting on that screen. |
| How it is called | customer-bff registers devices, reads the inbox, and holds the WebSocket. admin-bff writes templates and channel config, and CSC reads the log and resends. Provider receipts (SES, SMS, LINE) arrive at webhook-adapter and become a command. |
| Kafka | Publishes nothing. Consumes order.events, payment.events (refunded only), and notification.requested (send, broadcast, receipt). |

### Super high-level design

notification-shld.drawio

One page: who asks for a message, delivery status told by Delivery rather than a second send, and the channels that reach the customer.

### High-level design

notification-hld.drawio

One page: the three consumes, the path from event to message log to channel, and the call to Identity for contacts.

### Low-level design

notification-lld.drawio

| Page | Flow |
| --- | --- |
| 1 | order.events consumer |
| 2 | SendOtp |
| 3 | Broadcast |
| 4 | Provider receipt |
| 5 | RegisterDevice |
| 6 | payment.events refunded |
| 7 | Send command |
| 8 | Inbox |
| 9 | Preferences |
| 10 | Templates |
| 11 | Brand channel config |
| 12 | CSC log and resend |
| 13 | Campaign stats |
| 14 | WebSocket fanout |
| 15 | Channel sender |
| 16 | UnregisterDevice |
