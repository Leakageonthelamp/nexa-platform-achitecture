"""16 - Sharing saved payment methods across brands, with a Minor ID consent (3 pages). Proposal, 2026-10-28."""
from drawio_lib import Diagram, frame

DATE = "2026-10-28"
DOC = "docs/design/payment-methods-sharing.md"


def fr(p, title, maps_to, qs):
    frame(p, title, maps_to, qs, date=DATE)


def build():
    d = Diagram("16-payment-methods-sharing.drawio", "Sharing payment methods across brands")
    c = [24, 344, 664, 984, 1304]
    W = 260

    # ================================================================== page 1: share or not
    p = d.page("1 Share or not, at a glance", 1700, 1060)
    fr(p, "Saved payment methods: not shared by default, shared only if the customer opts in and the gateway allows it",
       DOC + " sections 1 to 5; P-62, P-63",
       ["O-61: Thai PDPA wording, bundling with the profile consent, retention, and delete (to confirm with legal)",
        "O-62: can a saved card work across brands' Omise accounts? No public feature found. To confirm with the gateway",
        "O-63: the reading of 'share with minor_id' (customer, brand, or Minor ID itself), and the scope"])
    p.lane("L", 24, 100, 810, 520, "Not shared (the default)", "neutral")
    p.box("l1", 44, 150, 770, 100, "Customer saves a card in Brand A", ["tick 'save this card'. The card goes from the browser to the gateway.", "NEXA keeps a gateway reference and display fields, never the number"], kind="http", parent="L", step=1)
    p.box("l2", 44, 290, 770, 100, "Payment stores it for Brand A only", ["owner brand A. Listed and usable in Brand A", "and nowhere else"], kind="enginew", parent="L", step=2)
    p.box("l3", 44, 430, 770, 100, "In Brand B the customer types a card", ["B does not list A's card. The customer may save the new card", "in B if B allows saved cards (saved_methods_enabled)"], kind="http", parent="L", step=3)
    p.edge("l1", "l2", "plain", None, sp="b", dp="t")
    p.edge("l2", "l3", "plain", None, sp="b", dp="t")
    p.lane("R", 866, 100, 810, 520, "Shared (the customer switched it on in Minor ID)", "engine", dashed=True)
    p.box("r1", 886, 150, 770, 100, "Customer opts in, once, in Minor ID", ["consent purpose payment_method_sharing, owned by Identity.", "Withdraw any time. Off by default"], kind="enginew", parent="R", step=1, dashed=True)
    p.box("r2", 886, 290, 770, 100, "A card saved in Brand A is also listed in Brand B", ["only if A and B pay through the same gateway account", "(a payment_account_group) and B's membership is enabled"], kind="enginew", parent="R", step=2, dashed=True)
    p.box("r3", 886, 430, 770, 100, "A brand with its own gateway account cannot use it", ["a saved card lives inside one gateway account. Brands in their", "own accounts do not see it. That is the gateway limit (section 4)"], kind="fail", parent="R", step=3, dashed=True)
    p.edge("r1", "r2", "plain", None, sp="b", dp="t")
    p.edge("r2", "r3", "fail", None, sp="b", dp="t")
    p.box("w1", 24, 650, 1652, 100, "Today, with one gateway account per brand, nothing can be shared across brands with documented gateway features", ["The first draft builds the model (consent, saved-method store, account groups, audit). Every brand is a group of one until finance decides on a group", "account, or the gateway confirms another way. This is stated plainly so nobody expects sharing before then (O-62)"], kind="fail", dashed=True)
    p.text("n1", 24, 780, 1652, 44, "<b>Never shared:</b> wallet balance and loyalty points (D-11), order history (that is the profile consent, P-33). A wallet is not a payment method here. A guest has no Minor ID, so a guest saves and shares nothing.",
           size=12, color="#475569")

    # ================================================================== page 2: consent and where data lives
    q = d.page("2 Consent and where the data lives", 1700, 1060)
    fr(q, "Identity owns the consent, Payment owns the saved methods, the gateway holds the card, and the bus carries ids only",
       DOC + " sections 2, 6, 8; P-62, P-63, P-64, P-33, P-40",
       ["O-61: how long consent and audit rows are kept, and how a delete works (with O-07, O-33)",
        "A third hop on the cross-brand charge path (BFF, Order, Payment, Identity). Flagged against the two-hop rule",
        "Never a card number or last four on the bus. No new topic (P-65)"])
    q.lane("B", 24, 100, 1652, 130, "The customer's browser", "http")
    q.box("b1", 44, 140, 500, 70, "Card form (Omise.js, the brand's public key)", ["the card goes straight to the gateway. No NEXA service sees it"], kind="http", parent="B", step=1)
    q.box("b2", 584, 140, 500, 70, "Consent switch in the app", ["customer-bff calls Identity SetConsent (REST at the edge)"], kind="http", parent="B", step=2)
    q.lane("D", 24, 260, 1652, 280, "Domains (Go, gRPC)", "engine")
    q.box("i1", 44, 310, 500, 200, "Identity &amp; Profile (Minor ID)", ["consent_record: customer, purpose =", "payment_method_sharing, granted or withdrawn,", "time, policy version, channel", "", "Stores no payment data. Publishes nothing"], kind="enginew", parent="D", step=3)
    q.box("p1", 624, 310, 500, 200, "Payment &amp; Billing", ["payment_method: owner brand, account group,", "gateway customer and card refs, card brand,", "last four, expiry, status. No card number", "payment_account_group, payment_method_audit", "Reads the consent live. Keeps no copy (D-07)"], kind="enginew", parent="D", step=4, dashed=True)
    q.box("o1", 1204, 310, 440, 200, "Cart &amp; Order", ["passes payment_method_id on the", "CreateTransaction call. It never sees a card", "or the consent. The checkout saga is", "unchanged (P-16: one tender per order)"], kind="enginew", parent="D")
    q.edge("p1", "i1", "grpc", "GetConsent", sp="l", dp="r", lab=0.5)
    q.edge("o1", "p1", "grpc", None, sp="l", dp="r")
    q.lane("G", 24, 570, 810, 200, "The gateway (Omise, public facts)", "http")
    q.box("g1", 44, 620, 770, 130, "Cards live inside one gateway account", ["a single-use token from the browser creates a customer and a card.", "A later charge uses the customer id and the card id, with that", "account's secret key. A token is valid for one merchant only"], kind="http", parent="G")
    q.lane("S", 866, 570, 810, 200, "Data stores and the bus", "data")
    q.box("s1", 886, 620, 370, 130, "Aurora (Postgres)", ["consent_record in Identity.", "payment_method and audit in Payment.", "Credentials stay in Vault"], kind="data", parent="S")
    q.box("s2", 1276, 620, 380, 130, "Kafka", ["ids only: payment_method_id, order_id,", "brand_id. No card detail. No new topic", "or variant (P-65)"], kind="cmd", parent="S", dashed=True)
    q.edge("p1", "g1", "http", "customers and cards API", sp=("b", 0.3), dp=("t", 0.7), lab=0.5)
    q.text("n1", 24, 800, 1652, 44, "<b>Who chooses:</b> the customer, once, for all their brands. A brand takes part only because it pays through the same gateway account. The brand-level switch saved_methods_enabled (default off) only decides whether the brand offers saved cards at all.",
           size=12, color="#475569")

    # ================================================================== page 3: sequences
    r = d.page("3 Three sequences: save, reuse in another brand, withdraw", 1700, 1080)
    fr(r, "Three sequences: the first payment, the saved method in another brand, and withdrawing consent",
       DOC + " section 7; P-62, P-63, P-64, P-01",
       ["Sequence 2 needs the same gateway account group. Until finance decides, every brand is its own group (O-62)",
        "If Identity does not answer at a cross-brand charge, the shared method is refused and the shopper picks another",
        "Whether a saved card still needs 3DS on every charge: to confirm with the gateway"])
    r.lane("S1", 24, 100, 1652, 210, "1 First payment in Brand A, and save the card", "neutral")
    a = [("1", "Card form", ["Omise.js in the browser,", "Brand A's public key"], "http"),
         ("2", "Token", ["single use. NEXA sees", "only the token"], "http"),
         ("3", "CreateTransaction", ["Order to Payment with the token", "and save = true, with a key"], "grpc"),
         ("4", "Gateway customer and card", ["Payment creates or updates the", "gateway customer, then charges"], "http"),
         ("5", "payment_method row", ["owner brand A, group, refs, display", "fields, and an audit row, one commit"], "enginew")]
    for i, (n, t, dd, k) in enumerate(a):
        r.box("a%d" % i, c[i] + 0, 150, W, 130, t, dd, kind=k, parent="S1", step=int(n), dashed=(i == 4))
    for i in range(4):
        r.edge("a%d" % i, "a%d" % (i + 1), "plain", None, sp="r", dp="l")
    r.lane("S2", 24, 340, 1652, 250, "2 Reuse the saved method in Brand B (the customer opted in, and A and B share one gateway account)", "engine", dashed=True)
    b = [("1", "ListPaymentMethods", ["customer-bff of B asks Payment.", "Hop 1"], "grpc"),
         ("2", "GetConsent", ["Payment asks Identity for the consent", "(hop 2) and B's membership is enabled"], "grpc"),
         ("3", "List own and shared", ["shared methods only if granted and", "the same account group"], "enginew"),
         ("4", "PlaceOrder(payment_method_id)", ["the shopper picks one. Order calls", "CreateTransaction"], "grpc"),
         ("5", "Charge and audit", ["Payment reads the consent again (a third", "hop, flagged), charges, writes an audit row"], "enginew")]
    for i, (n, t, dd, k) in enumerate(b):
        r.box("b%d" % i, c[i], 400, W, 130, t, dd, kind=k, parent="S2", step=int(n), dashed=(i in (1, 2, 4)))
    for i in range(4):
        r.edge("b%d" % i, "b%d" % (i + 1), "plain", None, sp="r", dp="l")
    r.lane("S3", 24, 620, 1652, 210, "3 Withdraw the consent", "fail")
    w = [("1", "SetConsent(withdrawn)", ["the app calls Identity through", "customer-bff, with a key"], "grpc"),
         ("2", "Identity records it", ["consent row and audit, one", "transaction. Publishes nothing"], "enginew"),
         ("3", "Takes effect at once", ["the next list or charge in another", "brand reads 'not shared'"], "enginew"),
         ("4", "Nothing is deleted", ["cards stay in their own brand. An open", "order that used one is not charged"], "fail"),
         ("5", "Optional: remove cards", ["the customer removes saved cards.", "Payment deletes the gateway card"], "http")]
    for i, (n, t, dd, k) in enumerate(w):
        r.box("w%d" % i, c[i], 670, W, 130, t, dd, kind=k, parent="S3", step=int(n), dashed=(i == 4))
    for i in range(4):
        r.edge("w%d" % i, "w%d" % (i + 1), "plain", None, sp="r", dp="l")
    r.text("n1", 24, 860, 1652, 44, "<b>Also:</b> a deleted Minor ID calls Payment to erase the gateway customers and cards (audit rows stay as the law needs, O-61). A brand whose membership is disabled for the customer (P-40) can neither list nor use shared methods.",
           size=12, color="#475569")
    return d
