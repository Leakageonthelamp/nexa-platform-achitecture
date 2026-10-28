"""13 - Postpaid QR table ordering (6 pages). Proposal, added 2026-10-25."""
from drawio_lib import Diagram, frame

DATE = "2026-10-25"
DOC = "docs/design/postpaid-table-ordering.md"


def fr(p, title, maps_to, qs):
    frame(p, title, maps_to, qs, date=DATE)


def build():
    d = Diagram("13-postpaid-table-ordering.drawio", "Postpaid QR table ordering")

    # ================================================================== page 1: the idea at a glance
    p = d.page("1 The idea at a glance", 1700, 1000)
    fr(p, "Postpaid table ordering: scan, order, eat, pay at the end",
       DOC + " sections 1, 5, 6; P-44, P-46, P-47",
       ["O-37: which brands, stores and formats; which store is the pilot?",
        "O-39: which QR guard level, and how much staff effort at seating?",
        "O-40: split bill - which kind, in which release?",
        "All of this is a proposal. The order goes to the kitchen first, the money moves at the end"])
    X = [44, 464, 884, 1304]
    W = 360
    p.lane("l1", 24, 100, 1652, 240, "What the diner does (guest, or signed in with Minor ID)", "http")
    p.lane("l2", 24, 380, 1652, 190, "What NEXA keeps: one open tab on the table (Cart & Order)", "engine")
    p.lane("l3", 24, 610, 1652, 220, "What the store does (staff and kitchen)", "http", dashed=False)
    dn = [("Scan the table QR", ["The sticker holds the brand, store and table.", "No personal data. No login needed."], 1),
          ("Order from the phone", ["Pick dishes and send them as a round.", "The kitchen gets it at once. No payment yet."], 2),
          ("Eat, and order more", ["Send more rounds any time.", "Everyone at the table sees the same tab."], 3),
          ("Ask for the bill and pay", ["Tip, voucher, card or PromptPay QR.", "Pay the whole bill. Receipt on screen."], 4)]
    for i, (t, dd, st) in enumerate(dn):
        p.box("d%d" % (i + 1), X[i], 150, W, 160, t, dd, kind="http", parent="l1", step=st)
    tb = [("Table session opens", ["One open session per table.", "Guests and members can join."]),
          ("Each round is a new add-on", ["Sent to the POS as part of the same check.", "Status: sent, accepted, ready, served."]),
          ("The tab stays open", ["It stays until it is paid. Rounds that are", "rejected are left out of the bill."]),
          ("Paid, check closed, tab closed", ["Money first, then the POS check closes.", "Points and vouchers settle at the close."])]
    for i, (t, dd) in enumerate(tb):
        p.box("t%d" % (i + 1), X[i], 420, W, 130, t, dd, kind="enginew", parent="l2")
    st_ = [("Table board shows a new tab", ["Staff see open tabs, rounds waiting,", "and how long each has been open."]),
           ("Kitchen gets each ticket", ["Through the POS, with the table on it.", "The kitchen works as for any order."]),
           ("Staff serve and tap served", ["Food is carried to the table by staff.", "This is not the Delivery domain."]),
           ("Staff see the bill request", ["Or settle at the till: the POS update", "closes the tab. Staff can also close it."])]
    for i, (t, dd) in enumerate(st_):
        p.box("s%d" % (i + 1), X[i], 660, W, 130, t, dd, kind="http", parent="l3")
    labs = ["start", "send round", "status feed", "bill, pay"]
    labs2 = ["table board", "ticket", "served tap", "close"]
    for i in range(4):
        p.edge("d%d" % (i + 1), "t%d" % (i + 1), "plain", labs[i], sp="b", dp="t")
        p.edge("t%d" % (i + 1), "s%d" % (i + 1), "plain", labs2[i], sp="b", dp="t")
    for i in range(3):
        p.edge("d%d" % (i + 1), "d%d" % (i + 2), "flow", None, sp="r", dp="l")
    p.text("n1", 24, 840, 1652, 24, "<b>Not in this picture:</b> the Delivery domain (no rider, no fee), a new Kafka topic (none is added), and a new service (none is added).",
           size=12, color="#475569")

    # ================================================================== page 2: states
    q = d.page("2 Table session and tab states", 1700, 1000)
    fr(q, "The tab moves through eight states; each round has its own", DOC + " section 5; P-46, P-50",
       ["O-48: who confirms served, and how a bill or a never-arrived dispute is settled?",
        "O-46: idle and maximum session time, and the payment window, are assumptions",
        "No timer ever sets closed, paid or abandoned_unpaid: a sweeper only queues staff"])
    xs = [24, 304, 584, 864, 1144, 1424]
    y, h, w = 170, 90, 200
    names = [("open", "tab exists, no round fired yet"), ("active", "at least one round fired; more can come"),
             ("bill_requested", "diner asked; ordering more goes back"), ("payment_pending", "tab locked while a payment runs"),
             ("paid", "payment captured; check closing"), ("closed", "app, counter or staff_override")]
    kinds = ["enginew", "enginew", "enginew", "enginew", "fact", "fact"]
    for i, (n, dd) in enumerate(names):
        q.box("s." + n, xs[i], y, w, h, n, [dd], kind=kinds[i])
    chain = [("s.open", "s.active", "round 1 fired"), ("s.active", "s.bill_requested", "asks bill"),
             ("s.bill_requested", "s.payment_pending", "PayBill"), ("s.payment_pending", "s.paid", "captured"),
             ("s.paid", "s.closed", "check closed")]
    for a, b, lab in chain:
        q.edge(a, b, "flow", lab, sp="r", dp="l")
    # reverse edges below the row
    ab, bb = q.nodes["s.active"], q.nodes["s.bill_requested"]
    q.edge("s.bill_requested", "s.active", "fail", "orders more", sp=("b", 0.25), dp=("b", 0.75),
           via=[(bb.x + 50, y + h + 40), (ab.x + 150, y + h + 40)], lab=0.5)
    pb = q.nodes["s.payment_pending"]
    q.edge("s.payment_pending", "s.bill_requested", "fail", "payment failed or expired", sp=("b", 0.25), dp=("b", 0.75),
           via=[(pb.x + 50, y + h + 80), (bb.x + 150, y + h + 80)], lab=0.5)
    # counter or staff close, over the top
    ac, cl = q.nodes["s.active"], q.nodes["s.closed"]
    q.edge("s.active", "s.closed", "http", "counter settlement or staff close", sp=("t", 0.5), dp=("t", 0.5),
           via=[(ac.x + 100, 128), (cl.x + 100, 128)], lab=0.5)
    # terminal boxes
    q.box("s.cancelled", 24, 400, 420, 90, "cancelled", ["no round was fired, or every line was rejected or voided"], kind="fail")
    q.box("s.abandoned", 584, 400, 480, 90, "abandoned_unpaid", ["staff flagged a walk-out. Never set by a timer"], kind="fail")
    q.edge("s.open", "s.cancelled", "fail", "nothing fired", sp="b", dp=("t", (124 - 24) / 420.0), lab=0.5)
    q.edge("s.active", "s.cancelled", "fail", "all rejected", sp=("b", 0.25), dp=("t", (354 - 24) / 420.0), lab=0.5, loff=(40, 0))
    q.edge("s.bill_requested", "s.abandoned", "fail", "staff flag", sp=("b", 0.5), dp=("t", (684 - 584) / 480.0), lab=0.55)
    q.edge("s.payment_pending", "s.abandoned", "fail", "staff flag", sp=("b", 0.5), dp=("t", (964 - 584) / 480.0), lab=0.55)
    # round states
    q.lane("rl", 24, 540, 1652, 270, "Every round has its own states (the POS ticket ranks, renamed for table service)", "engine")
    rs = [("fired", "sent, no answer yet", "enginew"), ("accepted", "the kitchen has it", "enginew"),
          ("preparing", "if the vendor says so", "enginew"), ("ready", "to carry to the table", "enginew"),
          ("served", "staff tap, or the POS", "fact")]
    rx = [44, 364, 684, 1004, 1324]
    for i, (n, dd, k) in enumerate(rs):
        q.box("r." + n, rx[i], 590, 300, 80, n, [dd], kind=k, parent="rl")
    for i in range(4):
        q.edge("r." + rs[i][0], "r." + rs[i + 1][0], "flow", None, sp="r", dp="l")
    q.box("r.rejected", 44, 710, 300, 80, "rejected", ["the kitchen refused it. Not billed"], kind="fail", parent="rl")
    q.box("r.voided", 1004, 710, 300, 80, "voided", ["staff voided it, with a reason. Not billed"], kind="fail", parent="rl")
    q.edge("r.fired", "r.rejected", "fail", "kitchen refuses", sp="b", dp="t", lab=0.5)
    q.edge("r.ready", "r.voided", "fail", "VoidRound", sp="b", dp="t", lab=0.5)
    q.text("n1", 24, 822, 1652, 22, "Served is derived: the tab is fully served when no round is waiting. The bill does not wait for it. A session is open until its tab ends, or it expires with no round.",
           size=12, color="#475569")

    # ================================================================== page 3: round to kitchen
    r = d.page("3 A round goes to the POS and the kitchen", 1700, 1060)
    fr(r, "One ordering round: price it live, commit, add it to the POS check, watch the status come back",
       DOC + " sections 5, 6, 8; docs/design/pos-adapters.md section 14; P-36, P-46, P-49",
       ["O-42: which POS vendors can keep a check open and add items? BSL flags are unknown",
        "O-44: how do staff learn of new rounds and bill requests?",
        "P-36 rules R1 to R7 still decide every POS update; the bill never takes a POS total"])
    cx = [24, 304, 584, 864, 1144, 1424]
    # row 1
    r.box("a1", cx[0], 130, 240, 110, "Diner sends a round", ["REST POST /v1/dine-in/rounds", "with an Idempotency-Key"], kind="http", step=1)
    r.box("a2", cx[1], 130, 240, 110, "guest-bff or customer-bff", ["token carries only the session", "and member, not the table"], kind="enginew")
    r.box("a3", cx[2], 130, 240, 110, "Cart &amp; Order: PlaceRound", ["session open, caps, dine-in on,", "live total equals expected"], kind="enginew", step=2)
    r.box("a4", cx[3], 130, 240, 110, "Live checks", ["Brand &amp; Store ResolveStore,", "Catalog PriceLines (dine_in)"], kind="grpc")
    r.edge("a1", "a2", "http", None, sp="r", dp="l")
    r.edge("a2", "a3", "grpc", None, sp="r", dp="l")
    r.edge("a3", "a4", "grpc", None, sp="r", dp="l")
    # row 2
    r.box("b1", cx[2], 300, 240, 100, "Commit the round", ["price lines + outbox row,", "one transaction. Tab: active"], kind="enginew", step=3)
    r.box("b2", cx[1], 300, 240, 100, "order.events", ["{placed} for round 1 only", "no payment gate"], kind="fact")
    r.edge("a3", "b1", "plain", "commit", sp="b", dp="t")
    r.edge("b1", "b2", "fact", None, sp="l", dp="r")
    # row 3
    r.box("c1", cx[2], 470, 240, 110, "POS worker", ["registry picks the adapter and", "flags from pos_connection"], kind="enginew", step=4)
    r.box("c2", cx[3], 470, 240, 110, "postpaid_pos_mode?", [], kind="enginew", shape="diamond", dashed=True)
    r.edge("b1", "c1", "plain", "outbox", sp="b", dp="t")
    r.edge("c1", "c2", "plain", None, sp="r", dp="l")
    r.box("m1", 1204, 325, 230, 100, "open_check", ["OpenCheck once, then AddItems", "per round. Needs vendor flags"], kind="enginew", step=5, dashed=True)
    r.box("m3", 1204, 475, 230, 100, "staff_settle", ["rounds go as tickets.", "Payment is at the counter"], kind="enginew", dashed=True)
    r.box("m2", 1204, 625, 230, 100, "ticket_per_round", ["one ticket per round with table", "and 'pay later' on it"], kind="enginew", dashed=True)
    r.box("pos", 1494, 325, 182, 400, "POS vendor", ["BSL first, Promise, VIVI later", "", "kitchen screen or printer", "gets the ticket", "", "to confirm per vendor:", "open check, add items,", "outside payment (O-42)"], kind="http")
    r.edge("c2", "m1", "plain", "supports_open_check", sp="t", dp="l", via=[(984, 375)], lab=0.5)
    r.edge("c2", "m3", "plain", "else", sp="r", dp="l")
    r.edge("c2", "m2", "plain", "no append", sp="b", dp="l", via=[(984, 675)], lab=0.6)
    for k in ("m1", "m3", "m2"):
        r.edge(k, "pos", "http", None, sp="r", dp=("l", (r.nodes[k].y + 50 - 325) / 400.0))
    # row 4 (flows leftwards)
    r.box("e1", 1424, 800, 200, 100, "partner-adapter", ["vendor mapper builds a", "canonical PosUpdate"], kind="enginew", step=6)
    r.box("e2", 1144, 800, 200, 100, "order.requested", ["command {pos_status}", "round, check, state"], kind="cmd")
    r.box("e3", 864, 800, 200, 100, "Order: consumer", ["R1 to R7, then commit", "state + outbox, Ack"], kind="enginew", step=7)
    r.box("e4", 584, 800, 200, 100, "order.events", ["fact {round_updated}", "fired ... served"], kind="fact", step=8)
    r.box("e5", 304, 800, 200, 100, "Status feed", ["GET sessions/current,", "cached by tab version"], kind="enginew")
    r.box("e6", 24, 800, 200, 100, "Diner and staff", ["status on the phone;", "staff tap served"], kind="http", step=9)
    r.edge("pos", "e1", "http", "signed webhook", sp=("b", (1524 - 1494) / 182.0), dp=("t", 0.5), lab=0.5)
    r.edge("e1", "e2", "cmd", "publish", sp="l", dp="r")
    r.edge("e2", "e3", "cmd", "consume", sp="l", dp="r")
    r.edge("e3", "e4", "fact", "publish", sp="l", dp="r")
    r.edge("e4", "e5", "fact", "read", sp="l", dp="r")
    r.edge("e5", "e6", "http", "poll", sp="l", dp="r")

    # ================================================================== page 4: bill and pay
    s = d.page("4 Ask for the bill and pay at the end", 1700, 1100)
    fr(s, "The bill: built from agreed lines, paid first, then the POS check closes (or pay at the counter)",
       DOC + " section 7; P-47, P-48, P-50, D-09, P-17",
       ["O-41: service charge, tip, VAT display and the guest tax invoice need finance and legal",
        "O-43: card hold and partial capture on MFG's gateway accounts are to confirm",
        "O-40: whole bill only in the first draft; equal split next, by item later (flag against P-16)"])
    c = [24, 344, 664, 984, 1304]
    W = 260
    # row 1
    s.box("a1", c[0], 125, W, 100, "Diner asks for the bill", ["REST via guest-bff or customer-bff"], kind="http", step=1)
    s.box("a2", c[1], 125, W, 100, "Order: RequestBill", ["tab: bill_requested. Bill from the", "agreed lines, service charge, tip"], kind="enginew", step=2)
    s.box("a3", c[2], 125, W, 100, "Voucher &amp; Campaign", ["EvaluateBasket on the whole tab", "channel dine_in"], kind="grpc")
    s.box("a4", c[3], 125, W, 100, "Staff table board", ["shows 'bill requested' with", "the age and the amount"], kind="http")
    s.edge("a1", "a2", "http", None, sp="r", dp="l")
    s.edge("a2", "a3", "grpc", "deals", sp="r", dp="l")
    s.edge("a2", "a4", "plain", "board", sp=("t", 0.5), dp=("t", 0.5), via=[(c[1] + 130, 104), (c[3] + 130, 104)], lab=0.5)
    # row 2
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
    # row 3 (leftwards)
    s.box("c4", c[3], 445, W, 100, "webhook-adapter", ["checks the gateway signature"], kind="enginew", step=7)
    s.box("c3", c[2], 445, W, 100, "payment.requested", ["command {webhook}"], kind="cmd")
    s.box("c2", c[1], 445, W, 100, "Payment commits captured", ["Statement writes the receipt", "and the invoice (to confirm)"], kind="enginew")
    s.box("c1", c[0], 445, W, 100, "payment.events", ["fact {captured}", "purpose = table_bill"], kind="fact")
    s.edge("b4", "c4", "http", "signed webhook", sp="b", dp="t")
    s.edge("c4", "c3", "cmd", "publish", sp="l", dp="r")
    s.edge("c3", "c2", "cmd", "consume", sp="l", dp="r")
    s.edge("c2", "c1", "fact", "publish", sp="l", dp="r")
    # row 4
    s.box("d1", c[0], 605, W, 100, "Order: tab paid", ["consumes captured, Ack.", "The diner already sees 'paid'"], kind="enginew", step=8)
    s.box("d2", c[1], 605, W, 100, "POS worker", ["ApplyPayment, then CloseCheck", "idempotency key order_id:close"], kind="enginew", step=9)
    s.box("d3", c[2], 605, W, 100, "POS check closed", ["answer or webhook. If it fails: retry,", "then staff queue. No refund"], kind="http")
    s.box("d4", c[3], 605, W, 100, "Order: tab closed", ["order.events {completed}", "settlement = app"], kind="fact", step=10)
    s.box("d5", c[4], 605, W, 100, "Consumers", ["Voucher commits the hold,", "Loyalty earns, Notification tells"], kind="fact")
    s.edge("c1", "d1", "fact", "consume, Ack", sp="b", dp="t")
    s.edge("d1", "d2", "plain", "then", sp="r", dp="l")
    s.edge("d2", "d3", "http", "close", sp="r", dp="l")
    s.edge("d3", "d4", "http", "confirmed", sp="r", dp="l")
    s.edge("d4", "d5", "fact", "publish", sp="r", dp="l")
    s.text("t2", 24, 722, 700, 22, "<b>Other way to finish: pay at the counter</b> (the universal fallback)", size=12, color="#1D4ED8")
    # row 5
    s.box("e1", c[0], 765, W, 100, "Diner pays at the till", ["staff settle in the POS with", "any POS tender"], kind="http")
    s.box("e2", c[1], 765, W, 100, "POS check paid or closed", ["webhook, or a GetCheck poll"], kind="http")
    s.box("e3", c[2], 765, W, 100, "partner-adapter", ["maps it to a PosUpdate with", "check_state"], kind="enginew")
    s.box("e4", c[3], 765, W, 100, "order.requested", ["command {pos_status}"], kind="cmd")
    s.box("e5", c[4], 765, W, 100, "Order: tab closed", ["settlement = counter, then as", "step 10. Or staff ForceCloseTab"], kind="fact")
    s.edge("e1", "e2", "http", "settle", sp="r", dp="l")
    s.edge("e2", "e3", "http", "webhook", sp="r", dp="l")
    s.edge("e3", "e4", "cmd", "publish", sp="r", dp="l")
    s.edge("e4", "e5", "cmd", "consume", sp="r", dp="l")
    s.text("n1", 1304, 125, 360, 100,
           "<b>Split bill.</b> First draft: one person pays the whole bill. Next: equal split, one payment per share, the tab closes when all are paid. Later: by item (O-40).",
           size=11, color="#475569")
    s.text("n2", 24, 885, 1650, 40,
           "Unpaid tabs: staff flag a walk-out (MarkTabUnpaid). With a card hold (P-48) it may be captured only under the terms the diner saw. No timer closes a tab.",
           size=12, color="#475569")

    # ================================================================== page 5: failures
    t = d.page("5 Failures and edge cases", 1700, 760)
    fr(t, "What happens when it goes wrong: nine cases, all ending with staff or a retry, never a silent close",
       DOC + " section 12; P-47, P-49, P-50; R1 to R7 in docs/design/pos-adapters.md",
       ["O-38: walk-out policy, who bears the loss, and the hold terms",
        "O-32: when the POS total differs from the bill, what is the rule?",
        "O-45, O-48: POS-added lines, disputes and the served signal need business answers"])
    cases = [
        ("1 The customer leaves without paying", ["Staff flag the tab: MarkTabUnpaid with a reason (grant tab.override).", "It becomes abandoned_unpaid. A card hold may be captured only", "under the terms shown at the hold. No timer closes it."]),
        ("2 The POS is offline when a round is sent", ["The POS worker retries from the outbox. The round stays fired.", "After the POS window the sweeper rejects the round and the", "diner is told to ask staff. Nothing is billed. The tab stays open."]),
        ("3 Payment fails at the end", ["payment.events {failed} puts the tab back to bill_requested", "and unlocks it. The diner retries or picks another method.", "The voucher hold stays for the retry."]),
        ("4 Paid, but the POS check will not close", ["The tab stays paid. CloseCheck is retried, then a staff queue", "entry carries the payment reference. No second charge and no", "automatic refund. Staff close the check in the POS."]),
        ("5 The kitchen rejects or voids after the fire", ["rejected is applied from the POS and left out of the bill.", "A void after ready is not applied from the POS: only staff can", "VoidRound, with a reason. The agreed lines are never rewritten."]),
        ("6 App payment and counter settlement collide", ["The first one to commit wins. If the POS settled first, the later", "captured meets a closed tab: a CSC refund task is raised.", "If the app was first, the POS update goes to reconciliation."]),
        ("7 Someone orders from a photo of the QR", ["Guard levels: rate limit and caps always (G1), a table code (G2,", "proposed default), staff confirm of the first round (G3).", "A round to an empty table shows on the table board."]),
        ("8 The store closes with tabs still open", ["The sweeper puts every open tab on the staff queue. It never", "marks them paid or unpaid. New sessions are refused by the", "store hours. A tab past the maximum time is queued too."]),
        ("9 The bill is disputed, or the POS total differs", ["Staff VoidRound before payment, which raises bill_version so a", "stale PayBill is rejected. The diner pays what the app showed.", "A POS total gap is a reconciliation row, not a price change."]),
    ]
    for i, (tt, dd) in enumerate(cases):
        col, row = i % 3, i // 3
        t.box("f%d" % (i + 1), 24 + col * 560, 110 + row * 150, 520, 130, tt, dd, kind="fail", align="left", valign="top", size=13)
    t.text("n1", 24, 570, 1650, 22, "All 20 edge cases are in docs/design/postpaid-table-ordering.md section 12, including a changed price, a moved table, a partial payment and a voucher that is not valid.",
           size=12, color="#475569")

    # ================================================================== page 6: where it plugs in
    u = d.page("6 Where it plugs into NEXA", 1700, 1270)
    fr(u, "Where postpaid plugs in: no new service, no new topic, new tables and calls in existing domains",
       DOC + " sections 2, 9; P-44, P-45, P-49, P-51, P-52; docs/kafka-topics.md",
       ["O-37: which brands and stores switch it on? Every switch is off until set",
        "O-46: the limits, time values and polling are assumptions (P-52)",
        "O-36: who creates new event schemas and ACLs (DevOps or the domain teams)"])
    u.lane("L1", 24, 100, 1652, 170, "Edge: Bun and Elysia v2, REST only (P-41)", "http")
    u.box("bffg", 44, 150, 300, 100, "guest-bff and customer-bff", ["/v1/dine-in/sessions, rounds, bill/pay", "diners: guests and Minor ID"], kind="enginew", parent="L1")
    u.box("adm", 404, 150, 300, 100, "admin-bff", ["/v1/admin/.../tabs and tables", "store staff (new grants, P-50)"], kind="enginew", parent="L1")
    u.box("par", 764, 150, 300, 100, "partner-adapter", ["POS vendor mapper: round, check", "reference and check state"], kind="enginew", parent="L1")
    u.box("pos", 1304, 150, 250, 100, "POS vendor", ["open check, add items,", "outside payment (O-42)"], kind="http", parent="L1", dashed=True)
    u.edge("pos", "par", "http", "signed webhook", sp="l", dp="r")
    u.lane("L2", 24, 300, 1652, 230, "Domains (Go, gRPC): new tables and calls in existing owners", "engine")
    u.box("ident", 44, 360, 300, 110, "Identity &amp; Profile", ["IssueGuestToken, scope dine_in", "no guest state kept (P-45)"], kind="enginew", parent="L2")
    u.box("order", 404, 350, 660, 130, "Cart &amp; Order (the OMS)", ["owns the table session, the tab, rounds and the bill (P-44)", "POS worker: OpenCheck, AddItems, ApplyPayment, CloseCheck", "sweeper: idle sessions, stale payment, close retry, store closing"], kind="enginew", parent="L2")
    u.box("brand", 1204, 360, 300, 110, "Brand &amp; Store", ["store_table, QR key version,", "postpaid switch. ResolveTable"], kind="enginew", parent="L2")
    u.edge("bffg", "ident", "grpc", "guest token", sp=("b", 0.4), dp=("t", 0.4))
    u.edge("bffg", "order", "grpc", "StartTableSession, PlaceRound", sp=("b", 0.85), dp=("t", 0.15), via=[(299, 285), (503, 285)], lab=0.5)
    u.edge("adm", "order", "grpc", "tab operations", sp=("b", 0.5), dp=("t", 0.45))
    u.edge("par", "order", "cmd", "order.requested", sp=("b", 0.5), dp=("t", 0.7))
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
    u.box("t1", 44, 830, 380, 90, "order.events", ["placed (round 1), accepted, round_updated (new),", "completed, cancelled"], kind="fact", parent="L4")
    u.box("t2", 464, 830, 380, 90, "order.requested", ["pos_status with round, check and", "check_state"], kind="cmd", parent="L4")
    u.box("t3", 884, 830, 380, 90, "payment.events", ["captured, failed, voided with", "purpose = table_bill or table_preauth"], kind="fact", parent="L4")
    u.box("t4", 1304, 830, 340, 90, "payment.requested", ["webhook, and capture or void", "for a card hold"], kind="cmd", parent="L4")
    u.lane("L5", 24, 970, 1652, 160, "Data, log and settings", "data")
    dd = [("aur", "Aurora PostgreSQL", ["table_session, table_session_member,", "order_round, tab_bill, store_table"], False),
          ("mon", "MongoDB payload log", ["OpenCheck, AddItems, ApplyPayment,", "CloseCheck traffic, with round_no"], False),
          ("val", "ElastiCache Valkey", ["tab status cache keyed by version,", "rate limits on session start"], False),
          ("vlt", "Vault", ["QR signing keys per brand,", "guest token key (Identity)"], False),
          ("cfg", "Settings (one owner each)", ["postpaid switch, qr_guard, POS mode,", "caps, TTLs, tip, split, card hold"], True)]
    for i, (id_, tt, det, dsh) in enumerate(dd):
        u.box(id_, 44 + i * 328, 1020, 300, 90, tt, det, kind="data", parent="L5", dashed=dsh)
    return d
