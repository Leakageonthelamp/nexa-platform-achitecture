"""10 - Domain map (3 pages)."""
from drawio_lib import Diagram, frame

REF = "docs/architecture.md section 3 and 4; docs/kafka-topics.md (Registry)"
QS = ["D-07: no copies of another domain's data unless a written decision says why",
      "D-11: loyalty and wallet stay per brand; O-19 and O-20 (cross-brand wallet and points) are deferred",
      "The sync-call list shows the calls named in the reference flows and topic rules; each domain's own diagrams hold the rest"]


def build():
    d = Diagram("10-domain-map.diagrams".replace(".diagrams", ".drawio"), "Domain map")

    # ------------------------------------------------------------ page 1
    p = d.page("1 Eleven domains by role", 1700, 1010)
    frame(p, "Eleven Go domains, each the only owner of its data", REF + " (Domains)", QS)
    groups = [
        ("g1", "People and access", 24, 100, 540, 250, [("identity", "Identity &amp; Profile", "owns the Minor ID, brand membership, login, profile, consent, OTP"),
                                                       ("admin", "Admin &amp; Partner", "owns admin principals, grants, sessions, partner OAuth clients; the only call to Azure AD")]),
        ("g2", "Brands, stores and menus", 584, 100, 540, 250, [("brand", "Brand &amp; Store", "owns brand, store, group, hours, zone, feature switches, onboarding state"),
                                                              ("catalog", "Catalog", "owns SKUs, modifiers, menu versions, sold-out flag, price book")]),
        ("g3", "Order and delivery", 1144, 100, 532, 250, [("order", "Cart &amp; Order (OMS)", "owns cart, order, POS ticket, pos_connection, checkout saga, payload log"),
                                                         ("delivery", "Delivery &amp; Dispatch", "owns delivery, quote, fee, provider job, rider, roster, earnings ledger")]),
        ("g4", "Money", 24, 380, 540, 250, [("payment", "Payment &amp; Billing", "owns transaction, gateway keys per brand, invoices and receipts"),
                                           ("wallet", "Wallet", "owns the wallet per brand and customer, stored-value ledger, holds")]),
        ("g5", "Customer value", 584, 380, 540, 250, [("loyalty", "Loyalty &amp; MemberCard", "owns points, tier, the card you scan"),
                                                    ("voucher", "Voucher &amp; Campaign", "owns vouchers, campaigns, holds, redemption book, audiences")]),
        ("g6", "Messaging", 1144, 380, 532, 250, [("notif", "Notification", "owns templates, message log, inbox, device tokens, reachability")]),
    ]
    for gid, title, x, y, w, h, boxes in groups:
        p.lane(gid, x, y, w, h, title, "neutral")
        for i, (bid, bt, bd) in enumerate(boxes):
            p.box(bid, x + 20 + i * 255, y + 50, 235, 180 if len(boxes) > 1 else 180, bt, [bd], kind="enginew", parent=gid, size=12)
    p.box("never", 1419, 430, 235, 180, "Never owns", ["the contact, the consent or the OTP code (they stay in Identity)", "or any other domain's data (D-07)"], kind="note", size=12, parent="g6")
    p.text("n1", 24, 660, 1650, 100, "Every domain app runs in modes from one image: <b>api</b> (gRPC), <b>consumer</b> (Kafka), <b>worker</b> (outbox relay and background jobs) and <b>cron</b>. "
           "Each mode is its own Kubernetes workload. Statement is a mode of the Payment app, and Brand and Store are one app. A second domain that needs data calls the owner over gRPC, live.",
           size=12, color="#475569")

    # ------------------------------------------------------------ page 2
    q = d.page("2 Who calls whom, live (gRPC)", 1700, 1080)
    frame(q, "Synchronous calls between domains: someone is waiting, so it is gRPC", REF + "; reference flow section 7", QS)
    q.box("bff", 640, 110, 260, 90, "customer-bff", ["GetCart, UpdateCart, PlaceOrder"], kind="enginew")
    q.box("order", 640, 330, 260, 130, "Cart &amp; Order", ["the checkout saga lives here"], kind="enginew")
    q.edge("bff", "order", "grpc", "PlaceOrder", sp="b", dp="t")
    left = [("bs", "Brand &amp; Store", "owns the store"), ("cat", "Catalog", "owns price and menu"), ("del", "Delivery &amp; Dispatch", "owns the delivery fee"), ("vou", "Voucher &amp; Campaign", "also ReserveRedemptions")]
    for i, (id_, t, dd) in enumerate(left):
        q.box(id_, 100, 140 + i * 150, 250, 100, t, [dd], kind="enginew")
    q.fan("order", ["bs", "cat", "del", "vou"], "grpc", side="l", trunk=500, lab=0.75,
          labels={"bs": "ResolveStore", "cat": "PriceLines", "del": "GetQuote", "vou": "EvaluateBasket"})
    q.edge("vou", "cat", "grpc", "ListSkus", sp="l", dp="l", via=[(60, 640), (60, 340)], lab=0.5)
    q.box("pay", 1080, 330, 240, 130, "Payment &amp; Billing", ["one Omise account per brand"], kind="enginew")
    q.box("omise", 1440, 330, 220, 130, "Omise (gateway)", ["card, QR, 3DS"], kind="http")
    q.box("wal", 1080, 600, 240, 110, "Wallet", ["balance, ledger, holds"], kind="enginew")
    q.edge("order", "pay", "grpc", "CreateTransaction", sp="r", dp="l")
    q.edge("pay", "omise", "http", "HTTPS charge", sp="r", dp="l")
    q.edge("pay", "wal", "grpc", "Hold, Capture, Release, Refund", sp="b", dp="t")
    q.box("idn", 560, 820, 240, 100, "Identity &amp; Profile", ["contacts, consent, OTP"], kind="enginew")
    q.box("not", 1000, 820, 240, 100, "Notification", ["templates, message log"], kind="enginew")
    q.edge("idn", "not", "grpc", "SendOtp", sp=("r", 0.3), dp=("l", 0.3))
    q.edge("not", "idn", "grpc", "reads contacts live", sp=("l", 0.7), dp=("r", 0.7))
    q.text("n1", 24, 800, 480, 130, "Rules: no chain of sync calls longer than two hops on the shopper's path; every call carries x-brand-id, x-principal-id, x-roles, traceparent and a deadline that is passed on, never reset.",
           size=12, color="#475569")
    q.text("n2", 1300, 780, 380, 150, "Wallet is gRPC, not a topic: Payment is waiting for the hold, so a command could not return it (D-09). Notification reads contacts from Identity at send time, so no phone number or email rides on the bus.",
           size=12, color="#475569")

    # ------------------------------------------------------------ page 3
    r = d.page("3 Who publishes and who consumes (Kafka)", 1700, 1260)
    frame(r, "Asynchronous map: what each domain publishes and consumes", REF + "; docs/architecture.md (Topics and diagram status)", QS)
    hdr_y = 84
    r.box("hd1", 24, hdr_y, 300, 34, "Domain or adapter", [], kind="enginew", shape="rect", size=12)
    r.box("hd2", 340, hdr_y, 640, 34, "Publishes", [], kind="cmd", shape="rect", size=12)
    r.box("hd3", 996, hdr_y, 680, 34, "Consumes", [], kind="fact", shape="rect", size=12)
    rows = [("Identity &amp; Profile", "none (every door is gRPC)", "none"),
            ("Admin &amp; Partner", "none (an admin is waiting)", "none"),
            ("Brand &amp; Store", "brand.changed, store.changed", "none"),
            ("Catalog", "catalog.menu.published, catalog.availability.changed", "catalog.requested, brand.changed, store.changed"),
            ("Cart &amp; Order", "order.events, payment.requested (capture, void)", "order.requested, payment.events, delivery.events"),
            ("Payment &amp; Billing", "payment.events", "payment.requested, delivery.events (FAAS invoice on delivered)"),
            ("Delivery &amp; Dispatch", "delivery.events, payment.requested (payout)", "order.events, store.changed, delivery.requested, payment.events"),
            ("Loyalty &amp; MemberCard", "notification.requested", "order.events"),
            ("Voucher &amp; Campaign", "notification.requested", "order.events"),
            ("Wallet", "notification.requested", "payment.events (top_up only)"),
            ("Notification", "none", "order.events, payment.events (refunded), delivery.events, notification.requested"),
            ("partner-adapter (edge)", "order.requested, catalog.requested, delivery.requested", "order.events, delivery.events, catalog.menu.published, catalog.availability.changed"),
            ("webhook-adapter (edge)", "payment.requested, notification.requested", "none")]
    for i, (a, b, c) in enumerate(rows):
        y = 130 + i * 74
        r.box("a%d" % i, 24, y, 300, 62, a, [], kind="enginew" if i < 11 else "http", size=12)
        r.box("b%d" % i, 340, y, 640, 62, "", [b], kind="note", shape="rect", align="left", size=12)
        r.box("c%d" % i, 996, y, 680, 62, "", [c], kind="note", shape="rect", align="left", size=12)
    return d
