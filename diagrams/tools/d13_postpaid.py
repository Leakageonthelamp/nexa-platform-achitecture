"""13 - Postpaid QR table ordering (6 pages). Proposal added 2026-10-25, regenerated 2026-10-28 for fire and forget (P-53 to P-55): no POS callback."""
from drawio_lib import Diagram, frame

DATE = "2026-10-28"
DOC = "docs/design/postpaid-table-ordering.md"


def fr(p, title, maps_to, qs):
    frame(p, title, maps_to, qs, date=DATE)


def build():
    d = Diagram("13-postpaid-table-ordering.drawio", "Postpaid QR table ordering")

    # ================================================================== page 1: the idea at a glance
    p = d.page("1 The idea at a glance", 1700, 1000)
    fr(p, "Postpaid table ordering: scan, order, eat, pay at the end",
       DOC + " sections 1, 5, 6; P-44, P-46, P-47, P-53",
       ["O-37: which brands, stores and formats; which store is the pilot?",
        "O-39: which QR guard level, and how much staff effort at seating?",
        "O-49: what the POS learns about a payment made in NEXA (marker, report, nothing)",
        "Amended 2026-10-28: the POS takes no action and sends no callback. NEXA keeps the whole tab"])
    X = [44, 464, 884, 1304]
    W = 360
    p.lane("l1", 24, 100, 1652, 240, "What the diner does (guest, or signed in with Minor ID)", "http")
    p.lane("l2", 24, 380, 1652, 190, "What NEXA keeps: the whole tab, with no POS callback (Cart & Order)", "engine")
    p.lane("l3", 24, 610, 1652, 220, "What the store does (staff and kitchen)", "http", dashed=False)
    dn = [("Scan the table QR", ["The sticker holds the brand, store and table.", "No personal data. No login needed."], 1),
          ("Order from the phone", ["Pick dishes and send them as a round.", "The kitchen gets it at once. No payment yet."], 2),
          ("Eat, and order more", ["Send more rounds any time.", "Everyone at the table sees the same tab."], 3),
          ("Ask for the bill and pay", ["Tip, voucher, card or PromptPay QR.", "Pay the whole bill. Receipt on screen."], 4)]
    for i, (t, dd, st) in enumerate(dn):
        p.box("d%d" % (i + 1), X[i], 150, W, 160, t, dd, kind="http", parent="l1", step=st)
    tb = [("Table session opens", ["One open session per table.", "Guests and members can join."]),
          ("Each round is fired and forgotten", ["Its own ticket to the POS, again and again.", "NEXA marks it sent. Staff tap served."]),
          ("The session bill adds up", ["Rounds add to one bill in NEXA. Rejected or", "voided rounds are left out of the bill."]),
          ("Paid, then NEXA closes the tab", ["Money first, then NEXA closes the tab", "and the session. The POS is not asked."])]
    for i, (t, dd) in enumerate(tb):
        p.box("t%d" % (i + 1), X[i], 420, W, 130, t, dd, kind="enginew", parent="l2")
    st_ = [("Table board shows the tab", ["Staff see open tabs, rounds that need", "staff, and how long each has been open."]),
           ("Kitchen gets each ticket", ["Through the POS, with the table and", "pay-later on it. Nothing comes back."]),
           ("Staff serve and tap served", ["Food is carried to the table by staff.", "This is not the Delivery domain."]),
           ("Staff see the bill request", ["Or settle at the till: staff enter it in", "NEXA, which closes the tab."])]
    for i, (t, dd) in enumerate(st_):
        p.box("s%d" % (i + 1), X[i], 660, W, 130, t, dd, kind="http", parent="l3")
    labs = ["start", "send round", "more rounds", "bill, pay"]
    labs2 = ["table board", "ticket", "served tap", "settle in NEXA"]
    for i in range(4):
        p.edge("d%d" % (i + 1), "t%d" % (i + 1), "plain", labs[i], sp="b", dp="t")
        p.edge("t%d" % (i + 1), "s%d" % (i + 1), "plain", labs2[i], sp="b", dp="t")
    for i in range(3):
        p.edge("d%d" % (i + 1), "d%d" % (i + 2), "flow", None, sp="r", dp="l")
    p.text("n1", 24, 840, 1652, 24, "<b>Not in this picture:</b> a POS callback or an open check (dropped, P-53), the Delivery domain (no rider, no fee), a new Kafka topic, and a new service.",
           size=12, color="#475569")

    # ================================================================== page 2: states
    q = d.page("2 Table session and tab states", 1700, 1000)
    fr(q, "The tab moves through seven states, and NEXA moves it alone; each round has its own", DOC + " section 5; P-46, P-53, P-55",
       ["O-48: who confirms served, and how a bill or a never-arrived dispute is settled?",
        "O-50: what counts as 'the kitchen has it' when the POS answers nothing?",
        "No timer ever sets closed or abandoned_unpaid. No POS update sets any state (P-53)"])
    xs = [24, 364, 704, 1044, 1384]
    y, h, w = 170, 90, 200
    names = [("open", "tab exists, no round fired yet"), ("active", "at least one round fired; more can come"),
             ("bill_requested", "diner asked; ordering more goes back"), ("payment_pending", "tab locked while a payment runs"),
             ("closed", "app, counter or staff_override")]
    kinds = ["enginew", "enginew", "enginew", "enginew", "fact"]
    for i, (n, dd) in enumerate(names):
        q.box("s." + n, xs[i], y, w, h, n, [dd], kind=kinds[i])
    chain = [("s.open", "s.active", "round 1 fired"), ("s.active", "s.bill_requested", "asks bill"),
             ("s.bill_requested", "s.payment_pending", "PayBill"), ("s.payment_pending", "s.closed", "captured: NEXA closes")]
    for a, b, lab in chain:
        q.edge(a, b, "flow", lab, sp="r", dp="l")
    ab, bb = q.nodes["s.active"], q.nodes["s.bill_requested"]
    q.edge("s.bill_requested", "s.active", "fail", "orders more", sp=("b", 0.25), dp=("b", 0.75),
           via=[(bb.x + 50, y + h + 40), (ab.x + 150, y + h + 40)], lab=0.5)
    pb = q.nodes["s.payment_pending"]
    q.edge("s.payment_pending", "s.bill_requested", "fail", "payment failed or expired", sp=("b", 0.25), dp=("b", 0.75),
           via=[(pb.x + 50, y + h + 80), (bb.x + 150, y + h + 80)], lab=0.5)
    ac, cl = q.nodes["s.active"], q.nodes["s.closed"]
    q.edge("s.active", "s.closed", "http", "staff settle at the counter in NEXA, or staff close", sp=("t", 0.5), dp=("t", 0.5),
           via=[(ac.x + 100, 128), (cl.x + 100, 128)], lab=0.5)
    q.box("s.cancelled", 24, 400, 500, 90, "cancelled", ["no round was fired, or every line was rejected or voided"], kind="fail")
    q.box("s.abandoned", 704, 400, 640, 90, "abandoned_unpaid", ["staff flagged a walk-out. Never set by a timer"], kind="fail")
    q.edge("s.open", "s.cancelled", "fail", "nothing fired", sp="b", dp=("t", (124 - 24) / 500.0), lab=0.5)
    q.edge("s.active", "s.cancelled", "fail", "all rejected", sp=("b", 0.25), dp=("t", (ab.x + 50 - 24) / 500.0), lab=0.5, loff=(40, 0))
    q.edge("s.bill_requested", "s.abandoned", "fail", "staff flag", sp=("b", 0.5), dp=("t", (bb.x + 100 - 704) / 640.0), lab=0.55)
    q.edge("s.payment_pending", "s.abandoned", "fail", "staff flag", sp=("b", 0.5), dp=("t", (pb.x + 100 - 704) / 640.0), lab=0.55)
    q.lane("rl", 24, 540, 1652, 270, "Every round has its own states, kept by NEXA (the POS reports none of them)", "engine")
    rs = [("fired", "committed in NEXA, being sent", "enginew"), ("sent", "the POS call succeeded (not 'printed')", "enginew"),
          ("served", "a staff tap on the table board", "fact")]
    rx = [44, 444, 844]
    for i, (n, dd, k) in enumerate(rs):
        q.box("r." + n, rx[i], 590, 300, 80, n, [dd], kind=k, parent="rl")
    for i in range(2):
        q.edge("r." + rs[i][0], "r." + rs[i + 1][0], "flow", None, sp="r", dp="l")
    q.box("r.rejected", 44, 710, 300, 80, "rejected", ["the POS refused the call, or staff. Not billed"], kind="fail", parent="rl")
    q.box("r.needs", 444, 710, 300, 80, "needs_staff (a flag)", ["send failed or unclear: staff decide"], kind="fail", parent="rl", dashed=True)
    q.box("r.voided", 844, 710, 300, 80, "voided", ["staff voided it, with a reason. Not billed"], kind="fail", parent="rl")
    q.edge("r.fired", "r.rejected", "fail", "refused", sp=("b", 0.25), dp=("t", 0.5), lab=0.5)
    q.edge("r.fired", "r.needs", "fail", "unclear", sp=("b", 0.75), dp=("t", 0.25), lab=0.5)
    q.edge("r.sent", "r.voided", "fail", "VoidRound", sp=("b", 0.75), dp=("t", 0.5), lab=0.5)
    q.text("n1", 1180, 590, 470, 200, "<b>No status comes back from the POS.</b> 'sent' only means the call was accepted. Rejected, voided and served are decided in NEXA by the send result and by staff. A status that a vendor pushes anyway is logged and not applied (P-53).",
           size=12, color="#475569", parent="rl")
    q.text("n2", 24, 822, 1652, 22, "Served is derived: the tab is fully served when no round is waiting. The bill does not wait for it. A session is open until its tab ends, or it expires with no round.",
           size=12, color="#475569")


    # ================================================================== page 3: round to kitchen
    r = d.page("3 A round goes to the POS and the kitchen", 1700, 1060)
    fr(r, "One ordering round: price it live, commit, fire it to the POS and forget it; only the send result comes back",
       DOC + " sections 5, 6, 8; docs/design/pos-adapters.md section 14; P-36, P-46, P-53, P-54",
       ["O-42: which POS vendors accept a dine-in ticket with a pay-later marker and an idempotent send? BSL flags are unknown",
        "O-50: what counts as 'the kitchen has it' when the POS answers nothing?",
        "O-44: how do staff learn of new rounds and bill requests?"])
    cx = [24, 304, 584, 864, 1144, 1424]
    r.box("a1", cx[0], 130, 240, 110, "Diner sends a round", ["REST POST /v1/dine-in/rounds", "with an Idempotency-Key"], kind="http", step=1)
    r.box("a2", cx[1], 130, 240, 110, "guest-bff or customer-bff", ["token carries only the session", "and member, not the table"], kind="enginew")
    r.box("a3", cx[2], 130, 240, 110, "Cart &amp; Order: PlaceRound", ["session open, caps, dine-in on,", "live total equals expected"], kind="enginew", step=2)
    r.box("a4", cx[3], 130, 240, 110, "Live checks", ["Brand &amp; Store ResolveStore,", "Catalog PriceLines (dine_in)"], kind="grpc")
    r.edge("a1", "a2", "http", None, sp="r", dp="l")
    r.edge("a2", "a3", "grpc", None, sp="r", dp="l")
    r.edge("a3", "a4", "grpc", None, sp="r", dp="l")
    r.box("b1", cx[2], 300, 240, 100, "Commit the round", ["state fired, price lines + outbox", "row, one transaction. Tab: active"], kind="enginew", step=3)
    r.box("b2", cx[1], 300, 240, 100, "order.events", ["{placed} for round 1 only", "no payment gate"], kind="fact")
    r.edge("a3", "b1", "plain", "commit", sp="b", dp="t")
    r.edge("b1", "b2", "fact", None, sp="l", dp="r")
    r.box("c1", cx[2], 470, 240, 110, "POS worker", ["registry picks the adapter.", "mode fire_only (P-54)"], kind="enginew", step=4)
    r.box("c2", cx[3], 470, 240, 110, "PosGateway.Submit", ["one dine-in ticket per round: table,", "round, pay-later. Key order_id:round_no"], kind="enginew", step=5)
    r.box("pos", cx[4], 470, 240, 110, "POS vendor", ["kitchen screen or printer gets the", "ticket. It sends no status back"], kind="http")
    r.edge("b1", "c1", "plain", "outbox", sp="b", dp="t")
    r.edge("c1", "c2", "plain", None, sp="r", dp="l")
    r.edge("c2", "pos", "http", "ticket", sp="r", dp="l")
    r.box("r1", cx[3], 640, 240, 110, "The call result", ["the only answer. On success the", "round is sent (step 7)"], kind="enginew", step=6)
    r.box("r2", cx[2], 640, 240, 110, "Round marked sent", ["Order commits the state and", "publishes round_updated"], kind="enginew", step=7)
    r.box("r3", cx[1], 640, 240, 110, "order.events", ["fact {round_updated}", "fired, sent, served, rejected"], kind="fact")
    r.box("r4", cx[0], 640, 240, 110, "Diner and staff", ["status on the phone and the board;", "staff tap served"], kind="http", step=8)
    r.edge("c2", "r1", "plain", "returns", sp="b", dp="t")
    r.edge("r1", "r2", "plain", None, sp="l", dp="r")
    r.edge("r2", "r3", "fact", None, sp="l", dp="r")
    r.edge("r3", "r4", "fact", "read", sp="l", dp="r")
    r.box("f1", cx[3], 810, 240, 110, "Refused, or unclear", ["after the retry window.", "NEXA never resends by itself"], kind="fail")
    r.box("f2", cx[2], 810, 240, 110, "needs_staff, board raised", ["rejected if refused. For an", "unclear send staff must decide"], kind="fail")
    r.box("f3", cx[1], 810, 240, 110, "Staff act in NEXA", ["resend, confirm, or void.", "Each with a reason and an audit row"], kind="http")
    r.edge("r1", "f1", "fail", "else", sp="b", dp="t")
    r.edge("f1", "f2", "fail", None, sp="l", dp="r")
    r.edge("f2", "f3", "fail", None, sp="l", dp="r")
    r.box("f4", cx[4], 640, 240, 110, "A status pushed anyway", ["logged in the payload log,", "never applied (P-53)"], kind="data", dashed=True)
    r.edge("pos", "f4", "log", "if it does", sp="b", dp="t")


    # ================================================================== page 4: bill and pay
    s = d.page("4 Ask for the bill and pay at the end", 1700, 1100)
    fr(s, "The bill: built from agreed lines, paid first, then NEXA closes the tab (or staff settle at the counter)",
       DOC + " section 7; P-47, P-48, P-53, P-55, D-09, P-17",
       ["O-41: service charge, tip, VAT display and the guest tax invoice need finance and legal",
        "O-49: what the POS learns about the payment, and who issues the tax invoice for a table bill",
        "O-51: counter settlement by staff in NEXA: tenders, who may press it, how cash is counted"])
    c = [24, 344, 664, 984, 1304]
    W = 260
    s.box("a1", c[0], 125, W, 100, "Diner asks for the bill", ["REST via guest-bff or customer-bff"], kind="http", step=1)
    s.box("a2", c[1], 125, W, 100, "Order: RequestBill", ["tab: bill_requested. Bill from the", "agreed lines, service charge, tip"], kind="enginew", step=2)
    s.box("a3", c[2], 125, W, 100, "Voucher &amp; Campaign", ["EvaluateBasket on the whole tab", "channel dine_in"], kind="grpc")
    s.box("a4", c[3], 125, W, 100, "Staff table board", ["shows 'bill requested' with", "the age and the amount"], kind="http")
    s.edge("a1", "a2", "http", None, sp="r", dp="l")
    s.edge("a2", "a3", "grpc", "deals", sp="r", dp="l")
    s.edge("a2", "a4", "plain", "board", sp=("t", 0.5), dp=("t", 0.5), via=[(c[1] + 130, 104), (c[3] + 130, 104)], lab=0.5)
    s.box("b1", c[0], 285, W, 100, "Diner chooses how to pay", ["tip, voucher code, sign in for points,", "method: card, PromptPay QR, wallet"], kind="http", step=3)
    s.box("b2", c[1], 285, W, 100, "Order: PayBill", ["locks the tab, then asks Payment", "key + bill_version + expected total"], kind="enginew", step=4)
    s.box("b3", c[2], 285, W, 100, "Payment &amp; Billing", ["purpose = table_bill,", "charge and capture at once"], kind="enginew", step=5)
    s.box("b4", c[3], 285, W, 100, "Gateway or Wallet", ["Omise card, PromptPay QR, or", "wallet Hold and Capture"], kind="http", step=6)
    s.edge("a1", "b1", "plain", "sees the bill", sp="b", dp="t")
    s.edge("b1", "b2", "http", "PayBill", sp="r", dp="l")
    s.edge("b2", "b3", "grpc", None, sp="r", dp="l")
    s.edge("b3", "b4", "http", "charge", sp="r", dp="l")
    s.edge("b2", "a3", "grpc", "ReserveRedemptions", sp="t", dp="b", via=[(c[1] + 130, 255), (c[2] + 130, 255)], lab=0.5)
    s.text("t1", 24, 398, 500, 22, "<b>Nobody waits from here</b>", size=12, color="#6D28D9")
    s.box("c4", c[3], 445, W, 100, "webhook-adapter", ["checks the gateway signature"], kind="enginew", step=7)
    s.box("c3", c[2], 445, W, 100, "payment.requested", ["command {webhook}"], kind="cmd")
    s.box("c2", c[1], 445, W, 100, "Payment commits captured", ["Statement writes the receipt", "and the invoice (to confirm)"], kind="enginew")
    s.box("c1", c[0], 445, W, 100, "payment.events", ["fact {captured}", "purpose = table_bill"], kind="fact")
    s.edge("b4", "c4", "http", "signed webhook", sp="b", dp="t")
    s.edge("c4", "c3", "cmd", "publish", sp="l", dp="r")
    s.edge("c3", "c2", "cmd", "consume", sp="l", dp="r")
    s.edge("c2", "c1", "fact", "publish", sp="l", dp="r")
    s.box("d1", c[0], 605, W, 100, "Order: payment captured", ["consumes captured. The diner", "already sees 'paid'"], kind="enginew", step=8)
    s.box("d2", c[1], 605, W, 100, "NEXA closes the tab", ["tab and session closed in one commit.", "settlement = app. No POS call"], kind="enginew", step=9)
    s.box("d3", c[2], 605, W, 100, "order.events", ["fact {completed}", "totals, settlement"], kind="fact", step=10)
    s.box("d4", c[3], 605, W, 100, "Consumers", ["Voucher commits the hold, Loyalty", "earns, Notification tells, receipt"], kind="fact")
    s.edge("c1", "d1", "fact", "consume, Ack", sp="b", dp="t")
    s.edge("d1", "d2", "plain", "then", sp="r", dp="l")
    s.edge("d2", "d3", "fact", "publish", sp="r", dp="l")
    s.edge("d3", "d4", "fact", "consume", sp="r", dp="l")
    s.box("d5", c[4], 605, W, 100, "Optional, one way", ["tell the POS (marker or report).", "A failure never reopens the tab"], kind="http", dashed=True)
    s.edge("d4", "d5", "plain", "O-49", sp="r", dp="l", dashed=True)
    s.text("t2", 24, 722, 900, 22, "<b>Other way to finish: pay at the counter.</b> No POS update closes a tab. Staff settle in NEXA.", size=12, color="#1D4ED8")
    s.box("e1", c[0], 765, W, 100, "Diner pays at the till", ["staff take the money as usual", "and also enter it in NEXA"], kind="http")
    s.box("e2", c[1], 765, W, 100, "SettleTabAtCounter", ["admin console. Grant tab.settle,", "tender, amount, reference, reason"], kind="enginew")
    s.box("e3", c[2], 765, W, 100, "Order: tab closed", ["settlement = counter, audit row.", "Then as step 10"], kind="fact")
    s.box("e4", c[3], 765, W, 100, "Collision with an app payment", ["the first commit wins. The other", "is refunded by CSC (P-55)"], kind="fail")
    s.edge("e1", "e2", "http", "settle", sp="r", dp="l")
    s.edge("e2", "e3", "grpc", None, sp="r", dp="l")
    s.edge("e3", "e4", "fail", "if both", sp="r", dp="l")
    s.text("n1", 1304, 125, 360, 100,
           "<b>Split bill.</b> First draft: one person pays the whole bill. Next: equal split, one payment per share, the tab closes when all are paid. Later: by item (O-40).",
           size=11, color="#475569")
    s.text("n2", 24, 885, 1650, 40,
           "Unpaid tabs: staff flag a walk-out (MarkTabUnpaid). With a card hold (P-48) it may be captured only under the terms the diner saw. No timer closes a tab.",
           size=12, color="#475569")


    # ================================================================== page 5: failures
    t = d.page("5 Failures and edge cases", 1700, 760)
    fr(t, "What happens when it goes wrong: nine cases, all ending with staff or a retry, never a silent close",
       DOC + " section 12; P-47, P-53, P-54, P-55",
       ["O-38: walk-out policy, who bears the loss, and the hold terms",
        "O-49, O-50: what the POS learns, and what counts as the kitchen having it",
        "O-48: the served signal and disputes need a business answer"])
    cases = [
        ("1 The customer leaves without paying", ["Staff flag the tab: MarkTabUnpaid with a reason (grant tab.override).", "It becomes abandoned_unpaid. A card hold may be captured only", "under the terms shown at the hold. No timer closes it."]),
        ("2 The POS is offline when a round is sent", ["Submit fails as unavailable. The worker retries from the outbox.", "After the send window the round gets needs_staff and the table", "board is raised. Staff resend or void it. The tab stays open."]),
        ("3 Payment fails at the end", ["payment.events {failed} puts the tab back to bill_requested", "and unlocks it. The diner retries or picks another method.", "The voucher hold stays for the retry."]),
        ("4 Paid, but the POS never learns of it", ["NEXA closed the tab at capture. The POS has the pay-later", "marker and maybe a report (O-49). A failed report is an info", "entry, not an error. The daily comparison finds a mismatch."]),
        ("5 The kitchen cannot make an item", ["The POS sends nothing back. Staff VoidRound or mark kitchen", "cannot make it, with a reason. The bill leaves it out and", "bill_version rises, so a stale PayBill is rejected."]),
        ("6 App payment and counter settlement collide", ["The first one to commit wins. If staff settled first, the later", "captured meets a closed tab: a CSC refund task is raised.", "If the app was first, staff see the tab is already closed."]),
        ("7 Someone orders from a photo of the QR", ["Guard levels: rate limit and caps always (G1), a table code (G2,", "proposed default), staff confirm of the first round (G3).", "A round to an empty table shows on the table board."]),
        ("8 The store closes with tabs still open", ["The sweeper puts every open tab on the staff queue. It never", "marks them paid or unpaid. New sessions are refused by the", "store hours. A tab past the maximum time is queued too."]),
        ("9 The bill is disputed, or the POS total differs", ["Staff VoidRound before payment, which raises bill_version so a", "stale PayBill is rejected. The diner pays what the app showed.", "A POS total gap is found in the daily comparison, not a price change."]),
    ]
    for i, (tt, dd) in enumerate(cases):
        col, row = i % 3, i // 3
        t.box("f%d" % (i + 1), 24 + col * 560, 110 + row * 150, 520, 130, tt, dd, kind="fail", align="left", valign="top", size=13)
    t.text("n1", 24, 570, 1650, 22, "All 23 edge cases are in docs/design/postpaid-table-ordering.md section 12, including an unclear send, a kitchen that never got a round, and a status the vendor pushes anyway.",
           size=12, color="#475569")

    # ================================================================== page 6: where it plugs in
    u = d.page("6 Where it plugs into NEXA", 1700, 1270)
    fr(u, "Where postpaid plugs in: no new service, no new topic, new tables and calls in existing domains",
       DOC + " sections 2, 9; P-44, P-45, P-53, P-54, P-51, P-52; docs/kafka-topics.md",
       ["O-37: which brands and stores switch it on? Every switch is off until set",
        "O-49: what the POS learns about a payment. No POS callback in this flow",
        "O-36: who creates new event schemas and ACLs (DevOps or the domain teams)"])
    u.lane("L1", 24, 100, 1652, 170, "Edge: Bun and Elysia v2, REST only (P-41)", "http")
    u.box("bffg", 44, 150, 300, 100, "guest-bff and customer-bff", ["/v1/dine-in/sessions, rounds, bill/pay", "diners: guests and Minor ID"], kind="enginew", parent="L1")
    u.box("adm", 404, 150, 300, 100, "admin-bff", ["/v1/admin/.../tabs and tables", "store staff (new grants, P-50)"], kind="enginew", parent="L1")
    u.box("par", 764, 150, 300, 100, "partner-adapter", ["not used for postpaid status.", "A pushed status is only logged"], kind="enginew", parent="L1")
    u.box("pos", 1304, 150, 250, 100, "POS vendor", ["takes a dine-in ticket only", "(O-42, O-49)"], kind="http", parent="L1", dashed=True)
    u.lane("L2", 24, 300, 1652, 230, "Domains (Go, gRPC): new tables and calls in existing owners", "engine")
    u.box("ident", 44, 360, 300, 110, "Identity &amp; Profile", ["IssueGuestToken, scope dine_in", "no guest state kept (P-45)"], kind="enginew", parent="L2")
    u.box("order", 404, 350, 660, 130, "Cart &amp; Order (the OMS)", ["owns the table session, the tab, rounds and the bill (P-44)", "POS worker: Submit one ticket per round, no callback", "sweeper: idle sessions, stale payment, stuck send, store closing"], kind="enginew", parent="L2")
    u.box("brand", 1204, 360, 300, 110, "Brand &amp; Store", ["store_table, QR key version,", "postpaid switch. ResolveTable"], kind="enginew", parent="L2")
    u.edge("bffg", "ident", "grpc", "guest token", sp=("b", 0.4), dp=("t", 0.4))
    u.edge("bffg", "order", "grpc", "StartTableSession, PlaceRound", sp=("b", 0.85), dp=("t", 0.15), via=[(299, 285), (503, 285)], lab=0.5)
    u.edge("adm", "order", "grpc", "tab operations", sp=("b", 0.5), dp=("t", 0.45))
    u.edge("order", "brand", "grpc", "ResolveTable", sp="r", dp="l")
    u.lane("L3", 24, 560, 1652, 190, "Called live by Cart &amp; Order, and consumers of its facts", "grpc")
    u.box("cat", 404, 620, 200, 100, "Catalog", ["PriceLines, GetMenu", "channel dine_in"], kind="grpc", parent="L3")
    u.box("pay", 644, 620, 200, 100, "Payment &amp; Billing", ["table_bill, table_preauth", "Statement: receipt"], kind="grpc", parent="L3")
    u.box("vou", 884, 620, 200, 100, "Voucher &amp; Campaign", ["EvaluateBasket,", "ReserveRedemptions"], kind="grpc", parent="L3")
    u.box("con", 1204, 620, 300, 100, "Loyalty, Notification, Voucher", ["read order.events: earn, message,", "commit or release the hold"], kind="fact", parent="L3")
    u.edge("order", "cat", "grpc", "PriceLines", sp=("b", 0.15), dp="t")
    u.edge("order", "pay", "grpc", "CreateTransaction", sp=("b", 0.5), dp="t")
    u.edge("order", "vou", "grpc", "EvaluateBasket", sp=("b", 0.85), dp="t")
    u.lane("L4", 24, 780, 1652, 160, "Kafka: the existing topics, with new event types only (P-51)", "cmd")
    u.box("t1", 44, 830, 380, 90, "order.events", ["placed (round 1), round_updated (new),", "completed, cancelled. No accepted"], kind="fact", parent="L4")
    u.box("t2", 464, 830, 380, 90, "order.requested", ["not used for postpaid:", "no POS status to carry (P-53)"], kind="cmd", parent="L4", dashed=True)
    u.box("t3", 884, 830, 380, 90, "payment.events", ["captured, failed, voided with", "purpose = table_bill or table_preauth"], kind="fact", parent="L4")
    u.box("t4", 1304, 830, 340, 90, "payment.requested", ["webhook, and capture or void", "for a card hold"], kind="cmd", parent="L4")
    u.lane("L5", 24, 970, 1652, 160, "Data, log and settings", "data")
    dd = [("aur", "Aurora PostgreSQL", ["table_session, table_session_member,", "order_round, tab_bill, store_table"], False),
          ("mon", "MongoDB payload log", ["Submit traffic, with round_no,", "and any status pushed anyway"], False),
          ("val", "ElastiCache Valkey", ["tab status cache keyed by version,", "rate limits on session start"], False),
          ("vlt", "Vault", ["QR signing keys per brand,", "guest token key (Identity)"], False),
          ("cfg", "Settings (one owner each)", ["postpaid switch, qr_guard, fire_only,", "pos_payment_report, send window, caps"], True)]
    for i, (id_, tt, det, dsh) in enumerate(dd):
        u.box(id_, 44 + i * 328, 1020, 300, 90, tt, det, kind="data", parent="L5", dashed=dsh)
    return d
