"""11 - One context page per remaining domain (8 pages), same layout on every page.

Left: who calls it (gRPC, someone is waiting) and what it consumes (Kafka in).
Middle: the domain engine. Right: what it publishes, calls and reaches outside.
Content is read from docs/architecture.md, docs/kafka-topics.md and, where the v3 text is silent, the
domain's HLD (original draw.io); where they differ the v3 text wins (see the report).
"""
from drawio_lib import Diagram, frame

REF = "docs/architecture.md section 3 and 13; docs/kafka-topics.md; domains/%s"


def domain_page(d, name, title, hld, spec, qs):
    callers, ins, engine, outs, notes = spec["callers"], spec["ins"], spec["engine"], spec["outs"], spec["notes"]
    nleft = len(callers) + len(ins)
    rows = max(nleft, len(outs), len(engine))
    pitch = 100 if rows > 6 else 124
    bh = pitch - 24
    top = 130
    lane_h = rows * pitch + 20
    pg = d.page(name, 1700, 100 + 16 + lane_h + 60 + 28 * len(notes) + 160)
    pg.text("hl", 24, 84, 320, 20, "<b>Calls it, someone waits (gRPC)</b>", size=12, color="#C2410C")
    pg.text("hm", 1186, 84, 490, 20, "<b>Goes out</b>", size=12, color="#0F172A")
    pg.lane("eng", 470, 100, 640, lane_h, spec["engine_title"], "engine")
    # engine boxes spread evenly
    n = len(engine)
    eh = (lane_h - 60 - 14 * (n - 1)) / n
    eh = max(eh, 60)
    for i, (t, dd, k) in enumerate(engine):
        pg.box("e%d" % i, 490, 140 + i * (eh + 14), 600, eh, t, dd, kind=k, parent="eng", align="left", valign="top", size=11)
    ly = lambda cy: min(0.97, max(0.03, (cy - 100) / float(lane_h)))
    y = top
    for i, (t, dd, k) in enumerate(callers):
        pg.box("c%d" % i, 24, y, 330, bh, t, dd, kind=k, size=11)
        pg.edge("c%d" % i, "eng", "grpc", None, sp="r", dp=("l", ly(y + bh / 2.0)))
        y += pitch
    for i, (t, dd, ek) in enumerate(ins):
        pg.box("k%d" % i, 24, y, 330, bh, t, dd, kind=ek, size=11)
        pg.edge("k%d" % i, "eng", ek, "consume", sp="r", dp=("l", ly(y + bh / 2.0)))
        y += pitch
    y = top
    for i, (t, dd, boxk, ek) in enumerate(outs):
        pg.box("o%d" % i, 1186, y, 490, bh, t, dd, kind=boxk, size=11, dashed=False)
        pg.edge("eng", "o%d" % i, ek, None, sp=("r", ly(y + bh / 2.0)), dp="l")
        y += pitch
    ny = 100 + lane_h + 20
    for i, (t, line) in enumerate(notes):
        pg.text("nt%d" % i, 24, ny + i * 28, 1650, 26, "<b>%s</b> %s" % (t, line), size=12, color="#475569")
    frame(pg, title, REF % hld, qs)
    return pg


def build():
    d = Diagram("11-other-domains.drawio", "Other domains")

    domain_page(d, "1 Payment and Billing", "Payment &amp; Billing: charge is gRPC, capture and webhook are commands, results are facts",
                "payment-and-billing/payment-billing-hld.drawio", dict(
        callers=[("Order", ["CreateTransaction at checkout, with an idempotency_key (D-02)"], "enginew"),
                 ("customer-bff", ["wallet top-up: 3DS, QR, PromptPay"], "enginew"),
                 ("admin-bff", ["Refund (partial allowed); the admin is waiting"], "enginew")],
        ins=[("payment.requested", ["capture, void, webhook, payout. Producers: Order, webhook-adapter, Delivery"], "cmd"),
             ("delivery.events", ["delivered: Statement invoices a FAAS brand, then Ack"], "fact")],
        engine_title="Payment &amp; Billing: one Go app (modes api, consumer, worker, cron; Statement is a mode)",
        engine=[("Checkout", ["CreateTransaction: Omise charge and authorize_url,", "or Wallet Hold with no page for a wallet order"], "enginew"),
                ("Capture, void, payout, webhook", ["one command, same key, so they stay in order; match the ref, then the outbox"], "enginew"),
                ("Gateway worker and refund", ["calls Omise or TrueMoney after the commit; 2C2P is a port, not shipped"], "enginew"),
                ("Statement mode", ["tax invoice and receipt after capture; FAAS invoice from delivered"], "enginew"),
                ("Data", ["Aurora: one transactions table (brand_id is a column), attempts, brand config with gateway keys,", "outbox, processed_event, audit. S3: invoices and receipts"], "data")],
        outs=[("payment.events", ["authorized, captured, failed, voided, refunded, paid_out, payout_failed"], "fact", "fact"),
              ("Wallet (gRPC)", ["Hold, Capture, Release, Refund (D-09)"], "enginew", "grpc"),
              ("Omise gateway (HTTPS)", ["one account per brand (O-22 asks about more)"], "http", "http"),
              ("TrueMoney (HTTPS)", ["rider payout only, brand_id = mfg (P-25)"], "http", "http")],
        notes=[("Rule:", "food is authorized first and captured only after the POS accepts the ticket; a refund is gRPC because an admin waits."),
               ("Not this domain:", "the order status (Order), the balance (Wallet), the price (Catalog), the rider and the trip (Delivery).")]),
        ["O-05: if capture fails after the kitchen accepted, is the order kept, retried or sent to CSC?",
         "O-11: is the tax invoice issued at top-up or when the balance is spent?  O-22: more than one payment partner per brand?",
         "O-16: the TrueMoney merchant account for rider payout"])

    domain_page(d, "2 Delivery and Dispatch", "Delivery &amp; Dispatch: one port for every fleet, one ledger for the rider",
                "delivery-and-dispatch/delivery-dispatch-hld.drawio", dict(
        callers=[("customer-bff", ["Quote, GetDelivery (read)"], "enginew"),
                 ("Order", ["GetQuote at PlaceOrder; quote_id on the order (P-22)"], "enginew"),
                 ("partner-bff (FAAS)", ["Quote, CreateDelivery (P-26)"], "enginew"),
                 ("admin-bff", ["assign, cancel, redispatch, mark delivered, rider admin"], "enginew")],
        ins=[("order.events", ["accepted starts dispatch, cancelled cancels the job (P-21)"], "fact"),
             ("delivery.requested", ["provider_update, rider_sync, roster_sync"], "cmd"),
             ("store.changed", ["syncs the store to the fleet provider as a merchant"], "fact"),
             ("payment.events", ["paid_out, payout_failed settle the trip row"], "fact")],
        engine_title="Delivery &amp; Dispatch: one Go app, one schema for dispatch and the rider workforce",
        engine=[("Quote and CreateDelivery", ["fee, distance, eta; no provider call; Delivery owns the quote (P-22, P-29)"], "enginew"),
                ("Deliveries and status log", ["seven states, an update applies only at a higher rank (P-20)"], "enginew"),
                ("Dispatch worker and sweeper", ["FleetProvider port (P-18); ordered provider list per store (P-19);", "next provider when create fails or the no-rider wait ends (O-13)"], "enginew"),
                ("Rider workforce (brand_id = mfg, P-23)", ["rider registry, roster and shifts, earnings ledger; payout status on the trip row"], "enginew"),
                ("Data", ["Aurora: deliveries, quotes, provider config, earnings, outbox, audit. S3: shift file"], "data")],
        outs=[("delivery.events", ["dispatched, rider_assigned, picked_up, delivered, failed, cancelled"], "fact", "fact"),
              ("payment.requested {payout}", ["same commit as delivered, one per delivery (P-25)"], "cmd", "cmd"),
              ("Fleet providers (HTTPS)", ["ZEEK, Grab Express, behind one port"], "http", "http"),
              ("Google Maps (HTTPS)", ["road distance only above a threshold"], "http", "http"),
              ("Brand &amp; Store, Identity (gRPC)", ["zone and address read live, never copied (P-24)"], "enginew", "grpc")],
        notes=[("Rule:", "no rider or customer contact on the bus; a rider sync carries only the provider ref (P-24)."),
               ("Not this domain:", "the store zone (Brand &amp; Store), the order (Order), a real-money payout (Payment).")]),
        ["O-13: no-rider timeout, maximum attempts, scheduled-order lead time",
         "O-14: when every provider fails, auto-cancel and refund, or wait for CSC?  O-15: quote TTL, distance, fee scheme",
         "O-16: TrueMoney account and rider pay;  O-17: rider document retention;  O-18: cutover from Fleet Management, FAAS, Driver Management"])

    domain_page(d, "3 Wallet", "Wallet: stored value with its own ledger, paid through Payment",
                "wallet/wallet-hld.drawio", dict(
        callers=[("Payment", ["Hold at authorize, Capture or Release later, Refund (D-09)"], "enginew"),
                 ("admin-bff", ["Adjust: credit or debit, wallet.adjust grant (P-15)"], "enginew"),
                 ("customer-bff", ["GetWallet, ListEntries: own wallet, read only"], "enginew")],
        ins=[("payment.events", ["captured with purpose = top_up only; other variants Ack"], "fact")],
        engine_title="Wallet: one Go app, one wallet per (brand_id, customer_id)",
        engine=[("Payment port", ["Hold, Release, Capture, Refund; idempotent on Payment's ids"], "enginew"),
                ("Admin adjust", ["reason code and the grant's amount limit; audit row in the same commit; no maker-checker (P-15)"], "enginew"),
                ("Wallet and ledger", ["wallet_entries append-only; available = balance minus held; a hold moves held only"], "enginew"),
                ("Holds and reconciliation cron", ["no hold timer: Payment closes every hold, Order's sweeper voids (P-14);", "daily check of entries against balance, old holds flagged, no auto-fix"], "enginew"),
                ("Data", ["Aurora schema wallet: wallets, holds, wallet_entries, outbox, audit. No Valkey: a balance is never cached (D-04)"], "data")],
        outs=[("notification.requested {send}", ["topped up, adjusted, refunded; customer_id only"], "cmd", "cmd")],
        notes=[("Rules:", "one tender per order, no split between wallet and card (P-16); a top-up is captured at authorize and cannot be refunded to the card in v1 (P-17); real money never lands here (D-10)."),
               ("Not this domain:", "Omise and the top-up charge (Payment), points and the loyalty profile (Loyalty). No wallet topic: a spend is gRPC (D-09).")]),
        ["O-10: balance cap, top-up limits, expiry, and which BOT e-money rules apply",
         "O-12: the amount limit on the wallet.adjust grant",
         "O-19: one Minor Wallet across brands is deferred (D-11: one wallet per brand)"])

    domain_page(d, "4 Loyalty and MemberCard", "Loyalty &amp; MemberCard: points, the level and the card you scan",
                "loyalty-and-membercard/loyalty-membercard-hld.drawio", dict(
        callers=[("customer-bff", ["RedeemPoints; reads: GetMember, GetBalance, ListPostings, GetCard"], "enginew"),
                 ("admin-bff", ["AdjustPoints, publish rules, replace a card (loyalty.adjust grant)"], "enginew")],
        ins=[("order.events", ["completed earns, cancelled reverses; other variants Ack"], "fact")],
        engine_title="Loyalty &amp; MemberCard: one Go app, one profile per (brand_id, customer_id)",
        engine=[("Earn consumer", ["enrols the member on the first completed order; a guest earns nothing"], "enginew"),
                ("Redeem", ["debits oldest points first, then Voucher.IssueReward and waits; same redemption id on a retry"], "enginew"),
                ("Member, card and points ledger", ["card and QR, level on the member row; append-only postings, balance = sum of postings, expiry buckets"], "enginew"),
                ("Nightly crons", ["expire points 01:00, recompute tier 02:00 (Asia/Bangkok), Forbid"], "enginew"),
                ("Data", ["Aurora schema loyalty: members, cards, postings, buckets, rewards, redemptions, outbox, audit. No Valkey (D-04)"], "data")],
        outs=[("Voucher &amp; Campaign (gRPC)", ["IssueReward; Loyalty waits for the reply"], "enginew", "grpc"),
              ("notification.requested {send}", ["earned, reversed, expiring, expired, tier changed, voucher issued"], "cmd", "cmd")],
        notes=[("Rules:", "points are not stored value and not a tender; a posting is never edited, a reversal is a new posting the other way. No loyalty fact topic (nobody reacts)."),
               ("Not this domain:", "voucher codes and the redemption book (Voucher), stored value (Wallet), the person and consent (Identity).")]),
        ["O-20: points and level across brands is deferred (D-11: one profile per brand)",
         "Enrolment happens on the first completed order, so there is no member or birthday voucher before it (HLD cost)",
         "A refund does not reverse points (HLD decision; payment.events is not consumed)"])

    domain_page(d, "5 Voucher and Campaign", "Voucher &amp; Campaign: deals and vouchers, settled when the order is placed",
                "voucher-and-campaign/voucher-campaign-hld.drawio", dict(
        callers=[("Order", ["EvaluateBasket (nothing spent); ReserveRedemptions keyed by order_id at PlaceOrder"], "enginew"),
                 ("Loyalty", ["IssueReward; Loyalty waits"], "enginew"),
                 ("admin-bff", ["campaigns and vouchers, IssueVoucher for staff"], "enginew"),
                 ("customer-bff", ["own vouchers, read only"], "enginew")],
        ins=[("order.events", ["placed spends the hold; cancelled or rejected returns it"], "fact")],
        engine_title="Voucher &amp; Campaign: one Go app",
        engine=[("Basket", ["EvaluateBasket applies rules in a fixed order; no best-stack search and no margin floor yet (O-21)"], "enginew"),
                ("Hold", ["ReserveRedemptions: unique on order_id, re-checks the cap"], "enginew"),
                ("Settle on the fact", ["order.events spends or returns the hold; a hold whose order never committed waits for the cron"], "enginew"),
                ("Schedule cron", ["every 5 minutes: open, close and expire campaigns; purge the outbox"], "enginew"),
                ("Data", ["Aurora schema voucher: rules, vouchers, holds, redemptions, outbox. S3: broadcast audience file, customer ids only"], "data")],
        outs=[("notification.requested {send, broadcast}", ["send carries customer_id; broadcast carries an S3 key only"], "cmd", "cmd"),
              ("Catalog (gRPC)", ["ListSkus only when a rule names items"], "enginew", "grpc")],
        notes=[("Rules:", "no campaign topic and no Valkey: a hold is a Postgres row so a cache miss cannot double-spend it."),
               ("Not this domain:", "the cart and total (Order), menu price (Catalog), points and the card (Loyalty), the charge (Payment).")]),
        ["O-21: where do member price and deal stacking run, and who sets the margin floor per campaign?",
         "Voucher does not consume payment.events, so a payment does not issue a voucher",
         "D-11: loyalty stays per brand, so IssueReward is per brand"])

    domain_page(d, "6 Notification", "Notification: facts and commands in, one message log, every channel out",
                "notification/notification-hld.drawio", dict(
        callers=[("Identity", ["SendOtp: the shopper waits, SMS inline"], "enginew"),
                 ("customer-bff", ["RegisterDevice, inbox, preferences; holds the WebSocket"], "enginew"),
                 ("admin-bff", ["templates, brand channel config, CSC resend"], "enginew")],
        ins=[("order.events and delivery.events", ["the shopper hears both"], "fact"),
             ("payment.events", ["refunded only; other variants Ack"], "fact"),
             ("notification.requested", ["send, broadcast, receipt"], "cmd")],
        engine_title="Notification: one Go app; owns templates, message log, inbox, devices, reachability",
        engine=[("Intake consumers", ["one handler per topic; apply a new event_id once, then Ack"], "enginew"),
                ("Recipient resolve", ["BatchGetContacts on Identity at send time: consent, locale, reachability (no personal data on the bus, D-05)"], "enginew"),
                ("Message log and rules", ["one row per recipient and channel, unique on event_id; event type to template per brand"], "enginew"),
                ("Send and broadcast workers", ["by priority: OTP, transactional, marketing; three retries with backoff, then failed;", "broadcast reads the S3 audience in pages, throttled; marketing keeps quiet hours"], "enginew"),
                ("Data", ["Aurora: templates, message log, inbox, devices, preferences, audit. Valkey: token buckets, pub/sub. S3: audiences. Vault: channel secrets"], "data")],
        outs=[("FCM, SES, SMS, LINE (HTTPS)", ["one sender, identity or OA per brand; receipts return through webhook-adapter"], "http", "http"),
              ("Valkey pub/sub to customer-bff", ["WebSocket frames, at-most-once; the app re-reads on reconnect"], "data", "log"),
              ("Identity (gRPC)", ["BatchGetContacts"], "enginew", "grpc")],
        notes=[("Rules:", "no fact topic goes out (nobody downstream acts on a delivery status); OTP is gRPC because Identity waits; aggregator orders are skipped by the rules."),
               ("Not this domain:", "the contact, LINE id, consent and OTP code (Identity); moving an order or payment status (Order, Payment).")]),
        ["O-07: retention under PDPA for the message log, audit and order history",
         "D-05: no personal data on the bus; Notification reads contacts live",
         "Delivery of a message is at-least-once to providers; a crash after the provider reply can send one duplicate (HLD cost)"])

    domain_page(d, "7 Catalog and Menu", "Catalog &amp; Menu: admin writes the draft, publish emits the facts, shoppers only read",
                "catalog-and-menu/catalog-menu-hld.drawio", dict(
        callers=[("admin-bff", ["draft, publish, sold-out; the only write door"], "enginew"),
                 ("customer-bff, guest-bff", ["GetMenu, read only"], "enginew"),
                 ("partner-adapter and Order", ["GetMenu for aggregators; PriceLines at checkout"], "enginew")],
        ins=[("catalog.requested", ["sold-out from the POS webhook, via partner-adapter"], "cmd"),
             ("brand.changed and store.changed", ["v3 registry: Catalog consumes both"], "fact")],
        engine_title="Catalog &amp; Menu: one Go app; menu and product share one database",
        engine=[("Menu draft", ["private until publish; one brand and one channel; modifiers checked at publish and in PriceLines"], "enginew"),
                ("Menu version", ["immutable once published: draft, scheduled, published, superseded; price book frozen into it (D-08)"], "enginew"),
                ("Sold-out flag", ["per store and SKU, outside the menu version; optional auto-restore"], "enginew"),
                ("Import worker", ["reads the master feed (BSL, Excel, S3) into the draft; not a topic; cron publish every minute"], "enginew"),
                ("Data", ["Aurora: SKU, modifier, menu, sold-out, outbox, audit. Valkey: menu JSON keyed by version. S3 and CDN: images"], "data")],
        outs=[("catalog.menu.published", ["thin: version and effective_at; the reader calls GetMenu(version)"], "fact", "fact"),
              ("catalog.availability.changed", ["sold-out changes, separate topic because the rate differs"], "fact", "fact"),
              ("Brand &amp; Store (gRPC)", ["live brand and store lookup when a record is created"], "enginew", "grpc")],
        notes=[("Rules:", "a price change from the BSL feed reaches shoppers at the next publish (D-08); no copy of the store (D-07); no OpenSearch for under 1,000 items per store."),
               ("Not this domain:", "tenant, hours and zone (Brand &amp; Store), the order price lines (Order), the role and grant (Admin &amp; Partner).")]),
        ["O-21: member price and deal stacking may need to run beside or inside the price book",
         "D-08: a POS price change waits for a publish",
         "To reconcile: the HLD keeps no copy and checks Brand & Store live, while the v3 registry lists brand.changed and store.changed as Catalog inputs"])

    domain_page(d, "8 Admin and Partner", "Admin &amp; Partner: login is synchronous, and the bus is not involved",
                "admin-and-partner/admin-partner-hld.drawio", dict(
        callers=[("admin-bff", ["auth code with PKCE, grant, revoke, session"], "enginew"),
                 ("partner-bff", ["client_credentials with private_key_jwt"], "enginew")],
        ins=[],
        engine_title="Admin &amp; Partner: one Go domain, two engines; zero topics",
        engine=[("Admin engine", ["principal (IdP subject, email, name), grant, session; Admin JWT iss=admin, ES512, short TTL, roles fixed until the next token"], "enginew"),
                ("Partner engine", ["OAuth client with a public key only; Partner JWT 5 minutes, no refresh token; register, rotate, suspend"], "enginew"),
                ("Azure adapter", ["the only call to Azure AD (D-01); the port stays, only Azure is shipped"], "enginew"),
                ("Audit", ["audit_log in the same transaction as the write; the data lake reads Postgres, not the bus"], "enginew"),
                ("Data", ["Aurora schemas admin and partner. Valkey: refresh family, one-time code, PKCE verifier. Vault: admin-es512, partner-es512"], "data")],
        outs=[("Azure AD (HTTPS)", ["token endpoint; MFA stays in Azure"], "http", "http"),
              ("Kong JWKS", ["public halves of the admin and partner keys; Kong never calls Azure"], "http", "http")],
        notes=[("Rules:", "a token on the bus would be a secret to redact, so a grant, revoke, rotate or login is gRPC and the audit row is the record. A revoked session lives until its access token expires (5 minutes)."),
               ("Not this domain:", "the customer, the Minor ID and the customer key (Identity), headers downstream (Kong injects them).")]),
        ["O-09: which partners call partner-bff with a token rather than integrating through partner-adapter webhooks?",
         "D-01: Azure AD is called only by Admin &amp; Partner",
         "No fraud worker and no denylist projector (HLD decisions)"])

    return d
