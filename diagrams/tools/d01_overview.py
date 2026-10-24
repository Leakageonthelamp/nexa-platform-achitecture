"""01 - platform overview (2 pages): the big picture, and the components in plain words."""
from drawio_lib import Diagram, frame, h


def build():
    d = Diagram("01-platform-overview.drawio", "Platform overview")

    # ------------------------------------------------------------------ page 1: big picture
    p = d.page("1 Big picture", 1700, 1180)
    frame(p, "Platform overview: many brands, one platform",
          "docs/architecture.md section 1, 3, 4; docs/design/tech-stack.md",
          ["O-01 to O-03: scale and uptime numbers are assumptions (P-43)",
           "O-29: MongoDB Atlas hosting is to confirm with DevOps (P-38)",
           "O-31: which domains run on legacy, per brand (P-39)",
           "O-34: Elysia 2 is a release candidate, pin the version (P-41)"])
    p.box("banner", 24, 84, 1652, 46, "One platform, many brands",
          ["Bonchon &#183; The Pizza Company &#183; Swensen's &#183; Sizzler &#183; Dairy Queen &#183; Burger King &#183; "
           "The Coffee Club &#183; GAGA. A brand is a row (brand_id on every call, topic key and table), not a separate deployment."],
          kind="neutral", shape="rect", meta=True, size=12)

    # lanes
    p.lane("ch", 24, 170, 226, 540, "Channels and outside parties", "neutral")
    p.lane("edge", 290, 170, 190, 540, "Edge (DevOps)", "http")
    p.lane("apps", 520, 170, 260, 540, "Edge apps: Bun, Elysia v2", "engine")
    p.lane("dom", 840, 170, 440, 540, "Core: 11 domains, Go, hexagonal", "engine")
    p.lane("kafka", 1370, 170, 130, 540, "Confluent Kafka", "neutral")
    p.lane("data", 840, 750, 440, 210, "Data and secrets (DevOps)", "data")

    chans = [("ch.shop", "Shoppers", ["Customer app, one per brand", "Guest browsing, no login"]),
             ("ch.staff", "Staff and partners", ["Admin console and CSC", "Partner API clients"]),
             ("ch.agg", "Aggregators", ["Grab, LINE MAN, Shopee Food"]),
             ("ch.pos", "POS vendors and fleets", ["POS: BSL first, then Promise, VIVI...", "Fleet: ZEEK, Grab Express"]),
             ("ch.psp", "Payment and messaging", ["Omise gateway", "SES, SMS, LINE"])]
    for i, (id_, t, dd) in enumerate(chans):
        p.box(id_, 34, 206 + i * 100, 206, 86, t, dd, kind="http", parent="ch")

    p.box("cf", 300, 206, 170, 110, "Cloudflare", ["WAF, bots, TLS, CDN"], kind="http", parent="edge")
    p.box("kong", 300, 400, 170, 170, "Kong", ["The only policy point (PEP)", "Checks the JWT, signs hooks",
                                                  "Injects X-Principal-Id, X-Roles, X-Brand-Id"], kind="http", parent="edge")

    apps = [("a.cust", "customer-bff", ["customer app, REST"]), ("a.guest", "guest-bff", ["no login, menu only"]),
            ("a.admin", "admin-bff", ["admin console, CSC"]), ("a.partner", "partner-bff", ["partner API"])]
    for i, (id_, t, dd) in enumerate(apps):
        p.box(id_, 530, 206 + i * 68, 240, 58, t, dd, kind="enginew", parent="apps")
    p.box("a.padapter", 530, 498, 240, 80, "partner-adapter", ["aggregators, POS vendors, fleets", "one mapper per vendor"],
          kind="enginew", parent="apps")
    p.box("a.wadapter", 530, 588, 240, 80, "webhook-adapter", ["payment gateway, message providers"],
          kind="enginew", parent="apps")

    tiles = [("t.journey", "Shopper journey", ["Identity (Minor ID) &#183; Brand &amp; Store &#183; Catalog", "Cart &amp; Order (the OMS)"]),
             ("t.money", "Money and deals", ["Payment &#183; Wallet &#183; Loyalty", "Voucher &amp; Campaign"]),
             ("t.fulfil", "Fulfilment and messages", ["Delivery &amp; Dispatch &#183; Notification"]),
             ("t.control", "Control", ["Admin &amp; Partner (the only caller of Azure AD)"])]
    for i, (id_, t, dd) in enumerate(tiles):
        p.box(id_, 855, 206 + i * 116, 410, 100, t, dd, kind="enginew", parent="dom")

    p.box("k.cmd", 1380, 216, 110, 190, "Commands", ["5 topics named", "&lt;domain&gt;.requested", "one inbound door per domain", "Schema Registry on all"],
          kind="cmd", parent="kafka")
    p.box("k.fact", 1380, 440, 110, 240, "Facts", ["7 topics:", ".changed, .published, .events", "what already happened"],
          kind="fact", parent="kafka")

    p.box("d.pg", 855, 790, 200, 70, "Aurora PostgreSQL", ["one schema per domain, the truth"], kind="data", parent="data")
    p.box("d.valkey", 1065, 790, 200, 70, "ElastiCache Valkey", ["cache, auth state, rate limits"], kind="data", parent="data")
    p.box("d.s3", 855, 870, 130, 70, "S3", ["files, imports"], kind="data", parent="data")
    p.box("d.vault", 995, 870, 130, 70, "Vault", ["keys and secrets"], kind="data", parent="data")
    p.box("d.mongo", 1135, 870, 130, 70, "MongoDB", ["order payload log (P-38)"], kind="data", dashed=True, parent="data")
    p.box("legacy", 1540, 750, 136, 120, "Legacy systems", ["some brands, for now", "behind the same ports (P-39)"],
          kind="neutral", dashed=True)

    # edges
    p.edge("ch", "cf", "http", "HTTPS", sp=("r", 0.1), dp="l", lab=0.5)
    p.edge("cf", "kong", "http", "all traffic", sp="b", dp="t")
    p.edge("kong", "apps", "http", "routes", sp="r", dp=("l", (485 - 170) / 540.0))
    p.edge("apps", "dom", "grpc", "gRPC", sp=("r", 0.3), dp=("l", 0.3))
    p.edge("dom", "kafka", "fact", "publish", sp=("r", 0.3), dp=("l", 0.3))
    p.edge("kafka", "dom", "cmd", "consume", sp=("l", 0.62), dp=("r", 0.62))
    p.edge("apps", "kafka", "cmd", "adapters: commands", sp=("t", 0.5), dp=("t", 0.5), via=[(650, 148), (1435, 148)], lab=0.52)
    p.edge("dom", "data", "data", "commit, read", sp=("b", 0.5), dp=("t", 0.5))
    p.edge("dom", "legacy", "plain", "legacy bridge", sp=("b", 0.92), dp=("t", 0.5), via=[(1244, 730), (1608, 730)], lab=0.62)

    # ------------------------------------------------------------------ page 2: components in plain words
    q = d.page("2 Components in plain words", 1700, 1040)
    frame(q, "Platform overview: what each box does",
          "docs/architecture.md section 3 (components), D-03, D-01",
          ["D-03: four BFFs and two adapters, no more (a payment webhook never queues behind an aggregator)",
           "P-36: vendor mappers sit in partner-adapter, one per POS vendor",
           "Domains never call each other's tables (D-07); they call over gRPC, live"])
    q.lane("apps", 24, 84, 560, 700, "Edge apps (Bun, Elysia v2 RC, REST only)", "engine")
    edge_tiles = [
        ("customer-bff", "the customer app, with a customer JWT", ["Shopper reads, the cart, PlaceOrder,", "wallet top-up, inbox, WebSocket"]),
        ("guest-bff", "the app with no login", ["ListNearest and GetMenu only", "never anything that needs a principal"]),
        ("admin-bff", "the admin console and CSC (admin JWT)", ["Every admin write, after the", "grant check in X-Roles"]),
        ("partner-bff", "partners (partner JWT, client_credentials)", ["The partner API and the partner", "token endpoint"]),
        ("partner-adapter", "aggregators, POS vendors, fleet providers", ["Checks the signature, runs the vendor", "mapper, publishes one canonical command"]),
        ("webhook-adapter", "payment gateway, message providers", ["Checks the signature, publishes", "payment.requested or notification.requested"]),
    ]
    for i, (name, who, dd) in enumerate(edge_tiles):
        r, c = divmod(i, 2)
        q.box("ea." + name, 36 + c * 270, 124 + r * 210, 258, 196, name, [who] + dd, kind="enginew", parent="apps")
    q.lane("dom", 614, 84, 1062, 700, "Core domains (Go, hexagonal; one owner per piece of state)", "engine")
    doms = [
        ("Identity &amp; Profile", ["The Minor ID: login, shared profile,", "brand membership, PDPA consent"]),
        ("Brand &amp; Store", ["Brand, stores, hours, zone;", "feature switches and onboarding (proposed)"]),
        ("Catalog", ["SKUs, modifiers, menu versions,", "sold-out flag, price book"]),
        ("Cart &amp; Order (the OMS)", ["Cart, order, POS ticket, POS adapter port,", "checkout saga, payload log (proposed)"]),
        ("Payment &amp; Billing", ["Transaction, gateway keys per brand,", "invoices and receipts"]),
        ("Wallet", ["One wallet per brand and customer,", "stored-value ledger, holds"]),
        ("Loyalty &amp; MemberCard", ["Points, tier and the card you scan,", "per brand"]),
        ("Voucher &amp; Campaign", ["Vouchers, campaigns, holds,", "redemption book, audiences"]),
        ("Delivery &amp; Dispatch", ["Delivery, quote, fee, provider job,", "rider, roster, earnings ledger"]),
        ("Notification", ["Templates, message log, inbox,", "device tokens, reachability"]),
        ("Admin &amp; Partner", ["Admin principal, grants, sessions,", "partner OAuth client; only Azure AD caller"]),
    ]
    for i, (name, dd) in enumerate(doms):
        r, c = divmod(i, 3)
        q.box("dm.%d" % i, 626 + c * 346, 124 + r * 164, 332, 148, name, dd,
              kind="enginew", dashed=(i in (1, 3)), parent="dom")
    q.box("infra", 24, 810, 1652, 58, "Infrastructure, run by DevOps (fixed for the core)",
          ["Cloudflare &#183; Kong &#183; EKS &#183; Aurora PostgreSQL &#183; ElastiCache Valkey &#183; S3 &#183; Vault &#183; "
           "Confluent Cloud (Kafka + Schema Registry) &#183; CloudWatch and OpenTelemetry. MongoDB Atlas for the payload log: to confirm (O-29)."],
          kind="data", shape="rect", size=12)
    q.text("note.dashed", 24, 874, 1652, 20,
           "Dashed outline = new in v3 (feature switches in Brand &amp; Store, POS port and payload log in Cart &amp; Order): the original draw.io files do not show them yet.",
           size=11, color="#64748B")
    return d
