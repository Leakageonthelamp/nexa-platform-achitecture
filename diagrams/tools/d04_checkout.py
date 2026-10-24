"""04 - OMS checkout flow, own-app saga (6 pages)."""
from drawio_lib import Diagram, frame, badge

REF = "docs/architecture.md section 7 (reference flow)"


def build():
    d = Diagram("04-oms-checkout-flow.drawio", "OMS checkout flow")

    # ================================================================== page 1: at a glance
    p = d.page("1 Saga at a glance", 1760, 820)
    frame(p, "Own-app checkout at a glance: the shopper waits for 5 steps, then nobody waits",
          REF + "; P-09, P-10, P-32",
          ["O-04: the payment window and the POS answer window are still open",
           "O-05: capture fails after the kitchen accepted - keep, retry or CSC?",
           "O-32: POS total differs from the priced order - what is the rule?"])
    p.lane("wait", 24, 100, 4 * 176 + 3 * 40 + 24, 300, "The shopper waits: steps 0 to 5, all gRPC", "grpc")
    x2 = 24 + 4 * 176 + 3 * 40 + 24 + 40
    p.lane("nowait", x2 - 20, 100, 4 * 176 + 3 * 40 + 24, 300, "Nobody waits: steps 6 to 12, Kafka and workers", "cmd")
    boxes = [
        ("g1", "0", "Cart priced live", ["customer-bff calls GetCart and UpdateCart.", "Order prices it with Catalog, deals with Voucher."], "wait"),
        ("g2", "1-2", "PlaceOrder", ["idempotency_key, cart_version, expected total.", "Order checks store, price, quote and deals live."], "wait"),
        ("g3", "3", "Hold deals, commit", ["ReserveRedemptions holds the deals.", "Order commits the order, not placed yet."], "wait"),
        ("g4", "4-5", "Authorize payment", ["CreateTransaction to Payment and the gateway.", "authorize_url back to the app: 3DS or QR."], "wait"),
        ("g5", "6-8", "Payment confirmed", ["Gateway webhook becomes payment.events.", "Order commits placed and publishes order.events."], "nowait"),
        ("g6", "9-10", "POS ticket", ["POS worker sends the ticket through the", "PosGateway port; POS status comes back."], "nowait"),
        ("g7", "11", "Accept or reject", ["accepted: capture is requested.", "rejected: void is requested."], "nowait"),
        ("g8", "12", "Money moves", ["Payment captures or voids.", "Order closes the step."], "nowait"),
    ]
    for i, (id_, st, t, dd, lane) in enumerate(boxes):
        base = 24 + 12 if lane == "wait" else x2 - 20 + 12
        j = i if lane == "wait" else i - 4
        kind = "grpc" if lane == "wait" else ("cmd" if i in (4, 6) else "fact" if i in (5, 7) else "cmd")
        kind = "enginew"
        p.box(id_, base + j * 216, 160, 176, 200, t, dd, kind=kind, parent=lane, step=st)
    for i in range(7):
        kind = "grpc" if i < 3 else ("cmd" if i == 3 else "plain")
        lab = None
        p.edge("g%d" % (i + 1), "g%d" % (i + 2), "grpc" if i < 3 else "cmd" if i == 3 else "plain",
               "payment window" if False else None, sp="r", dp="l")
    p.box("sweep", 780, 460, 620, 100, "Sweeper cron in Order (P-10)",
          ["Closes checkouts that never got authorized and POS tickets the POS never answered,", "then sends payment.requested{void}. A crash resumes from the last committed status."],
          kind="engine")
    p.edge("sweep", "g4", "fail", "payment window", sp=("t", 0.12), dp="b", via=[], lab=0.5)
    p.edge("sweep", "g6", "fail", "POS window", sp=("t", 0.55), dp="b", lab=0.5)
    p.edge("sweep", "g8", "fail", "void", sp=("t", 0.88), dp="b", lab=0.5)
    p.text("n1", 24, 470, 720, 100,
           "<b>Three promises.</b> 1) Commit, then the fact: state and the outbox row commit together, the fact leaves after. "
           "2) Every consumer is idempotent: a redelivery does nothing. 3) Food is authorized first and captured only after the POS accepts the ticket.",
           size=12, color="#334155")
    p.text("n2", 24, 600, 1700, 60,
           "<b>Variants:</b> aggregator orders skip steps 1 to 7 (the aggregator already took the money). Wallet orders use the same steps, "
           "Payment holds the wallet balance instead of calling the gateway. See page 6.",
           size=12, color="#334155")

    # ================================================================== page 2: shopper waits
    q = d.page("2 Shopper waits (steps 1 to 5)", 1760, 1000)
    frame(q, "Own-app checkout, part 1: the shopper waits (steps 1 to 5)", REF + "; P-01, P-02, P-22, P-31, P-32, D-02, D-07, D-09",
          ["P-32: a different live total is price_changed; the app re-reads the cart",
           "P-16: wallet short of balance means the whole order goes to card",
           "O-02: p99 and deadline budget for PlaceOrder are still open"])
    q.lane("app", 24, 110, 120, 700, "Customer app", "http")
    q.lane("bff", 244, 110, 140, 700, "customer-bff", "engine")
    q.lane("ord", 544, 110, 180, 700, "Cart &amp; Order", "engine")
    q.box("ord.commit", 554, 624, 160, 64, "Commit the order", ["price lines and quoted fee, not placed yet"],
          kind="enginew", parent="ord", step=3, size=11)
    q.box("bs", 864, 348, 220, 44, "Brand &amp; Store", [], kind="grpc")
    q.box("cat", 864, 404, 220, 44, "Catalog", [], kind="grpc")
    q.box("del", 864, 460, 220, 44, "Delivery &amp; Dispatch", [], kind="grpc")
    q.box("vou", 864, 516, 220, 88, "Voucher &amp; Campaign", [], kind="grpc")
    q.box("pay", 864, 648, 220, 90, "Payment &amp; Billing", ["one Omise account per brand"], kind="grpc")
    q.box("omise", 1224, 648, 180, 40, "Omise (gateway)", [], kind="http")
    q.box("wal", 1224, 706, 180, 60, "Wallet", ["only for a wallet order"], kind="grpc", dashed=False)
    # step 1
    q.edge("app", "bff", "http", "HTTPS", sp=("r", (330 - 110) / 700.0), dp=("l", (330 - 110) / 700.0))
    q.edge("bff", "ord", "grpc", "PlaceOrder", step=1, sp=("r", (330 - 110) / 700.0), dp=("l", (330 - 110) / 700.0))
    ys = {"bs": 370, "cat": 426, "del": 482}
    q.edge("ord", "bs", "grpc", "ResolveStore", step=2, sp=("r", (370 - 110) / 700.0), dp="l")
    q.edge("ord", "cat", "grpc", "PriceLines", sp=("r", (426 - 110) / 700.0), dp="l")
    q.edge("ord", "del", "grpc", "GetQuote", sp=("r", (482 - 110) / 700.0), dp="l")
    q.edge("ord", "vou", "grpc", "EvaluateBasket", sp=("r", (538 - 110) / 700.0), dp=("l", (538 - 516) / 88.0))
    q.edge("ord", "vou", "grpc", "ReserveRedemptions", step=3, sp=("r", (582 - 110) / 700.0), dp=("l", (582 - 516) / 88.0))
    q.edge("ord", "pay", "grpc", "CreateTransaction", step=4, sp=("r", (670 - 110) / 700.0), dp=("l", (670 - 648) / 90.0))
    q.edge("pay", "omise", "http", "HTTP charge", sp=("r", (668 - 648) / 90.0), dp=("l", 0.5))
    q.edge("pay", "wal", "grpc", "Hold (wallet)", sp=("r", 0.8), dp=("l", 0.5), dashed="6 4")
    # step 5: return path
    q.edge("pay", "ord", "grpc", "authorize_url", step=5, sp=("l", (722 - 648) / 90.0), dp=("r", (722 - 110) / 700.0))
    q.edge("ord", "bff", "grpc", "authorize_url", sp=("l", (722 - 110) / 700.0), dp=("r", (722 - 110) / 700.0))
    q.edge("bff", "app", "http", "authorize_url", sp=("l", (722 - 110) / 700.0), dp=("r", (722 - 110) / 700.0))
    q.box("panel", 1440, 110, 296, 430, "What happens",
          ["0  Before checkout the cart is read and priced live: GetCart and UpdateCart, then Catalog PriceLines and Voucher EvaluateBasket.",
           "1  The shopper taps Pay. PlaceOrder carries idempotency_key, cart_version and the total the shopper saw.",
           "2  Order checks live: the store is open, the price, the delivery quote, the deals. Any failure here commits nothing.",
           "3  Order holds the deals (ReserveRedemptions) and commits the order with its price lines. It is not placed yet.",
           "4  Order asks Payment for an authorization. Payment calls the gateway. A wallet order calls Wallet Hold instead.",
           "5  authorize_url goes back to the app. The shopper finishes 3DS or QR at the gateway. From here nobody waits."],
          kind="note", shape="rect", size=12, align="left", valign="top")
    q.text("n1", 24, 830, 1400, 40, "Every call carries x-brand-id, x-principal-id, x-roles, traceparent and a deadline that is passed down and never reset. "
           "No chain of sync calls is longer than two hops on the shopper's path.", size=11, color="#475569")

    # ================================================================== page 3: payment confirmed
    r = d.page("3 Payment confirmed (steps 6 to 8)", 1700, 900)
    frame(r, "Own-app checkout, part 2: payment is confirmed, the order becomes placed (steps 6 to 8)",
          REF + "; P-06, P-09, D-05",
          ["P-09: placed means the kitchen may see it: after authorized for own-app orders",
           "O-04: how long to wait for the shopper (abandoned 3DS or QR)?"])
    xs = [24, 394, 764, 1134]
    W = 270
    r.box("omise", xs[0], 130, W, 100, "Omise (gateway)", ["shopper finished 3DS or QR"], kind="http")
    r.box("wh", xs[1], 130, W, 100, "webhook-adapter", ["checks the gateway signature", "bad signature stops here"], kind="enginew", step=6)
    r.box("t.req", xs[2], 130, W, 100, "payment.requested", ["command {webhook}", "key brand_id:transaction_id"], kind="cmd")
    r.box("pay", xs[3], 130, 340, 100, "Payment &amp; Billing", ["consumes, commits the transaction", "and the outbox row"], kind="enginew", step=7)
    r.edge("omise", "wh", "http", "signed webhook", sp="r", dp="l")
    r.edge("wh", "t.req", "cmd", "publish", sp="r", dp="l")
    r.edge("t.req", "pay", "cmd", "consume", sp="r", dp="l")
    r.box("t.auth", xs[3], 330, 340, 100, "payment.events", ["fact {authorized}", "key brand_id:transaction_id"], kind="fact")
    r.edge("pay", "t.auth", "fact", "publish after commit", sp="b", dp="t")
    r.box("ord", xs[2], 330, W, 100, "Cart &amp; Order", ["commits placed, deletes the cart"], kind="enginew", step=8)
    r.edge("t.auth", "ord", "fact", "consume, Ack", sp="l", dp="r")
    r.box("t.ord", xs[1], 330, W, 100, "order.events", ["fact {placed}", "key brand_id:order_id"], kind="fact")
    r.edge("ord", "t.ord", "fact", "publish", sp="l", dp="r")
    r.box("vou", xs[0], 330, W, 100, "Voucher &amp; Campaign", ["spends the deal hold on placed"], kind="fact")
    r.edge("t.ord", "vou", "fact", "consume, Ack", sp="l", dp="r")
    r.box("not", xs[1], 540, W, 100, "Notification", ["messages the shopper from the fact", "contacts read from Identity, live"], kind="fact")
    r.edge("t.ord", "not", "fact", "consume, Ack", sp="b", dp="t")
    r.box("pos", xs[2], 540, W, 100, "POS worker (step 9)", ["next page: the ticket goes to the POS"], kind="enginew")
    r.edge("ord", "pos", "grpc", "then", sp="b", dp="t", dashed="6 4")
    r.box("fail", xs[3], 540, 340, 100, "payment.events {failed}", ["Order commits cancelled, reason payment_failed,", "and publishes order.events {cancelled}"],
          kind="fail")
    r.edge("t.auth", "fail", "fail", "or failed", sp=("b", 0.5), dp="t", dashed="6 4")
    r.text("n1", 24, 680, 1640, 60,
           "A shopper who abandons 3DS never produces an authorized fact. The sweeper in Order closes the order after the payment window and sends payment.requested {void}. "
           "A redelivered record is a no-op: facts are deduplicated on version, commands on event_id (P-06).",
           size=12, color="#334155")

    # ================================================================== page 4: POS ticket (9 and 10)
    s = d.page("4 POS ticket and answer (steps 9 and 10)", 1700, 1000)
    frame(s, "Own-app checkout, part 3: the POS ticket goes out, the POS answer comes back (steps 9 and 10)",
          REF + "; docs/design/pos-adapters.md section 8; docs/design/order-payload-log.md",
          ["P-36: one PosGateway port, one adapter per vendor; BSL is the first adapter",
           "P-38 and O-30: payload log is best effort; is it a debugging aid or an audit record?",
           "O-28: real BSL capabilities need vendor confirmation"])
    s.box("w", 24, 130, 250, 100, "Order: POS worker", ["takes the placed order from the outbox", "and builds a canonical ticket"], kind="enginew", step=9)
    s.box("port", 394, 130, 250, 100, "PosGateway port and registry", ["picks the adapter from pos_connection", "(brand_id, store_id)"], kind="enginew")
    s.box("adp", 764, 130, 250, 100, "Vendor adapter (Go)", ["pos/bsl first, others later", "the BSL proxy is its transport"], kind="enginew")
    s.box("pos", 1400, 130, 276, 338, "POS vendor", ["BSL first, Promise, VIVI later", "", "receives the ticket", "sends status webhooks", "", "behaviour is untrusted input:", "duplicates, late, out of order"],
          kind="http")
    s.edge("w", "port", "grpc", "Submit", sp="r", dp="l")
    s.edge("port", "adp", "grpc", "adapter + flags", sp="r", dp="l")
    s.edge("adp", "pos", "http", "vendor request, routing from pos_connection", sp="r", dp=("l", (170 - 130) / 338.0))
    s.box("mongo", 24, 274, 990, 70, "MongoDB: order_payload_log (parallel, best effort, never blocks an order)",
          ["raw request and response before and after conversion, webhooks, outcomes; masked, expires by TTL; linked by order_id"],
          kind="data", dashed=True)
    s.box("pa", 764, 388, 250, 100, "partner-adapter", ["vendor mapper: checks signature,", "builds one canonical PosUpdate"], kind="enginew", step=10)
    s.box("t.req", 394, 388, 250, 100, "order.requested", ["command {pos_status}", "event_id is deterministic"], kind="cmd")
    s.box("cons", 24, 388, 250, 100, "Order: consumer", ["applies by rank and version (R1 to R7)", "commit state and outbox, then Ack"], kind="enginew")
    s.edge("pos", "pa", "http", "signed webhook (status)", sp=("l", (428 - 130) / 338.0), dp="r")
    s.edge("pa", "t.req", "cmd", "publish", sp="l", dp="r")
    s.edge("t.req", "cons", "cmd", "consume", sp="l", dp="r")
    s.edge("adp", "mongo", "log", "ticket, vendor request and response", sp=("b", 0.5), dp=("t", (889 - 24) / 990.0), lab=0.5, loff=(0, 0))
    s.edge("pa", "mongo", "log", "raw webhook, canonical PosUpdate", sp=("t", 0.2), dp=("b", (814 - 24) / 990.0), lab=0.5)
    s.edge("cons", "mongo", "log", "outcome", sp=("t", 0.5), dp=("b", (149 - 24) / 990.0), lab=0.5)
    s.box("f1", 24, 560, 400, 110, "Submit fails or the POS never answers",
          ["The POS worker retries from the outbox. After the POS window the", "sweeper rejects the ticket and sends a void (P-10, O-04)."], kind="fail", align="left")
    s.box("f2", 450, 560, 400, 110, "Duplicate, late or lower-rank update",
          ["Dropped or recorded as stale. A lower rank never moves", "a ticket backward. A zero total after a good one is an anomaly."], kind="fail", align="left")
    s.box("f3", 876, 560, 400, 110, "POS total differs from the priced order",
          ["Price lines never change. A reconciliation row and a CSC", "queue entry are written. The fix rule is open (O-32)."], kind="fail", align="left")
    s.text("n1", 24, 700, 1640, 60,
           "The shopper is not waiting here. The payload log is not a step: adapters and Order capture payloads in memory and a writer sends them to MongoDB later. "
           "A log failure never touches the order. Details: 05-oms-pos-adapters and 06-order-payload-log-mongo.", size=12, color="#334155")

    # ================================================================== page 5: accept or reject
    t = d.page("5 Accept or reject (steps 11 and 12)", 1700, 1080)
    frame(t, "Own-app checkout, part 4: accepted means capture, rejected means void (steps 11 and 12)",
          REF + "; P-10, P-14, D-09",
          ["O-05: if capture fails after the kitchen accepted, is the order kept, retried or sent to CSC?",
           "O-14: when every delivery provider fails, auto-cancel and refund or wait for CSC?",
           "Delivery starts dispatch on accepted (P-21)"])
    t.lane("la", 24, 100, 1652, 290, "Accepted", "fact")
    t.lane("lr", 24, 440, 1652, 290, "Rejected", "fail")
    t.box("sa", 44, 150, 220, 220, "Order commits accepted", ["state + capture request in one transaction", "(POS status received)"], kind="enginew", step=11, parent="la")
    t.box("a1", 384, 150, 270, 90, "payment.requested", ["command {capture}"], kind="cmd", parent="la")
    t.box("a2", 764, 150, 250, 90, "Payment &amp; Billing", ["captures with the gateway", "(wallet order: Wallet Capture)"], kind="enginew", parent="la", step=12)
    t.box("a3", 1124, 150, 220, 90, "payment.events", ["fact {captured}"], kind="fact", parent="la")
    t.box("a4", 1424, 150, 232, 90, "Order", ["closes the step"], kind="fact", parent="la")
    t.box("b1", 384, 280, 270, 90, "order.events", ["fact {accepted}"], kind="fact", parent="la")
    t.box("b2", 764, 280, 250, 90, "Delivery &amp; Dispatch", ["starts dispatch (P-21)"], kind="fact", parent="la")
    t.edge("sa", "a1", "cmd", "publish", sp=("r", 0.2045), dp="l")
    t.edge("sa", "b1", "fact", "publish", sp=("r", 0.795), dp="l")
    t.edge("a1", "a2", "cmd", "consume", sp="r", dp="l")
    t.edge("a2", "a3", "fact", "publish", sp="r", dp="l")
    t.edge("a3", "a4", "fact", "consume", sp="r", dp="l")
    t.edge("b1", "b2", "fact", "consume", sp="r", dp="l")
    t.box("sr", 44, 490, 220, 220, "Order commits rejected", ["state + void request in one transaction", "(POS refused, or POS window passed)"], kind="enginew", step=11, parent="lr")
    t.box("r1", 384, 490, 270, 90, "payment.requested", ["command {void}"], kind="cmd", parent="lr")
    t.box("r2", 764, 490, 250, 90, "Payment &amp; Billing", ["voids the hold", "(wallet order: Wallet Release)"], kind="enginew", parent="lr", step=12)
    t.box("r3", 1124, 490, 220, 90, "payment.events", ["fact {voided}"], kind="fact", parent="lr")
    t.box("r4", 1424, 490, 232, 90, "Order", ["closes the step"], kind="fact", parent="lr")
    t.box("q1", 384, 620, 270, 90, "order.events", ["fact {rejected}"], kind="fact", parent="lr")
    t.box("q2", 764, 620, 250, 90, "Voucher &amp; Campaign", ["releases the deal hold"], kind="fact", parent="lr")
    t.edge("sr", "r1", "cmd", "publish", sp=("r", 0.2045), dp="l")
    t.edge("sr", "q1", "fact", "publish", sp=("r", 0.795), dp="l")
    t.edge("r1", "r2", "cmd", "consume", sp="r", dp="l")
    t.edge("r2", "r3", "fact", "publish", sp="r", dp="l")
    t.edge("r3", "r4", "fact", "consume", sp="r", dp="l")
    t.edge("q1", "q2", "fact", "consume", sp="r", dp="l")
    t.box("sw", 44, 770, 400, 80, "Sweeper cron in Order", ["POS never answered within the POS window:", "it rejects the ticket, then sends the void"], kind="engine", align="left")
    t.edge("sw", "lr", "fail", "reject and void", sp=("t", 0.5), dp=("b", (244 - 24) / 1652.0))
    t.text("n1", 480, 770, 1190, 100,
           "Capture happens only after the POS accepts the ticket. Notification, Loyalty and Voucher react to the same order facts; every other variant of a topic is an Ack with no work. "
           "Delivery acts on accepted (start dispatch) and cancelled (cancel the provider job).", size=12, color="#334155")

    # ================================================================== page 6: variants and failures
    u = d.page("6 Variants and failures", 1700, 1340)
    frame(u, "Checkout variants (aggregator, wallet) and what happens when something fails",
          REF + "; P-09, P-16, P-32, P-36; D-09",
          ["O-04, O-05, O-14, O-32: the failure rules marked open in the register",
           "P-16: one tender per order, no split between wallet and card"])
    u.lane("agg", 24, 90, 1652, 250, "Aggregator order: skips steps 1 to 7 (the aggregator already collected the money)", "neutral")
    ax = [40, 360, 680, 1000, 1330]
    u.box("ag1", ax[0], 140, 250, 100, "Aggregator", ["Grab, LINE MAN, Shopee Food"], kind="http", parent="agg")
    u.box("ag2", ax[1], 140, 250, 100, "partner-adapter", ["checks signature, vendor mapper", "one canonical command"], kind="enginew", parent="agg")
    u.box("ag3", ax[2], 140, 250, 100, "order.requested", ["command {create, replace, cancel}"], kind="cmd", parent="agg")
    u.box("ag4", ax[3], 140, 250, 100, "Order", ["commits placed straight away", "no cart, no payment"], kind="enginew", parent="agg")
    u.box("ag5", ax[4], 140, 316, 100, "Steps 9 to 11 as before", ["POS ticket, status back, accepted or rejected", "no capture and no void"], kind="enginew", parent="agg")
    u.edge("ag1", "ag2", "http", "webhook", sp="r", dp="l")
    u.edge("ag2", "ag3", "cmd", "publish", sp="r", dp="l")
    u.edge("ag3", "ag4", "cmd", "consume", sp="r", dp="l")
    u.edge("ag4", "ag5", "grpc", "then", sp="r", dp="l")
    u.text("agn", 40, 258, 1500, 40, "partner-adapter writes the raw webhook and the canonical command to the payload log (best effort). Steps 9 to 11 are the same as the own-app flow.", size=11, color="#475569", parent="agg")
    u.lane("wal", 24, 370, 1652, 230, "Wallet order: same steps, method = wallet", "neutral")
    u.box("w1", 40, 420, 250, 100, "Cart &amp; Order", ["CreateTransaction, method = wallet"], kind="grpc", parent="wal")
    u.box("w2", 360, 420, 250, 100, "Payment &amp; Billing", ["calls Wallet instead of the gateway"], kind="grpc", parent="wal")
    u.box("w3", 680, 420, 250, 100, "Wallet", ["Hold at step 4, Capture or", "Release at step 12"], kind="grpc", parent="wal")
    u.box("w4", 1000, 420, 330, 100, "Authorized at once", ["no authorize_url, step 6 is skipped"], kind="enginew", parent="wal")
    u.box("w5", 1360, 420, 296, 100, "Short balance", ["FAILED_PRECONDITION; the app offers", "a card for the whole order (P-16)"], kind="fail", parent="wal")
    u.edge("w1", "w2", "grpc", "gRPC", sp="r", dp="l")
    u.edge("w2", "w3", "grpc", "Hold", sp="r", dp="l")
    u.edge("w3", "w4", "grpc", "ok", sp="r", dp="l")
    u.edge("w3", "w5", "fail", "short", sp=("b", 0.5), dp=("b", 0.5), via=[(805, 560), (1508, 560)], lab=0.5)
    # failure table
    rows = [
        ("Store hidden, not live or closed at step 2", "PlaceOrder returns FAILED_PRECONDITION. Nothing is committed."),
        ("Live total differs from the total the shopper saw", "FAILED_PRECONDITION (price_changed). Nothing is committed. The app re-reads the cart."),
        ("Brand and Store, Catalog, Delivery or Voucher down at step 2 or 3", "UNAVAILABLE. Nothing is committed. The app retries with the same idempotency_key."),
        ("Quote expired, used, or for another brand", "FAILED_PRECONDITION. Nothing is committed."),
        ("Payment down at step 4", "The order stays unplaced. A retry with the same key returns the same order and calls CreateTransaction again."),
        ("Shopper abandons 3DS", "No authorized arrives. The sweeper closes the order after the payment window and sends void."),
        ("payment.events {failed}", "Order commits cancelled (payment_failed) and publishes order.events {cancelled}."),
        ("POS never answers", "The sweeper rejects the ticket after the POS window and sends a void."),
        ("POS update is a duplicate, late or out of order", "Dropped or recorded as stale. A lower rank never moves a ticket backward."),
        ("POS total differs from the priced order", "Price lines never change. Reconciliation row and CSC queue entry. The rule is open (O-32)."),
        ("The store's POS cannot take this fulfillment", "FAILED_PRECONDITION (fulfillment_not_supported). Nothing is committed."),
        ("Crash anywhere", "The step resumes from the last committed status. A redelivered record is a no-op."),
    ]
    u.text("ft", 24, 624, 800, 24, "<b>What goes wrong, and what happens</b> (docs/architecture.md section 7)", size=13, color="#0F172A")
    for i, (a, b) in enumerate(rows):
        y = 654 + i * 46
        u.box("fa%d" % i, 24, y, 520, 38, a, [], kind="fail", align="left", size=11)
        u.box("fb%d" % i, 556, y, 1120, 38, "", [b], kind="note", shape="rect", align="left", size=11)
    return d
