"""15 - Multi-brand shared cart (3 pages). Proposal, 2026-10-28."""
from drawio_lib import Diagram, frame

DATE = "2026-10-28"
DOC = "docs/design/multi-brand-cart.md"


def fr(p, title, maps_to, qs):
    frame(p, title, maps_to, qs, date=DATE)


def build():
    d = Diagram("15-multi-brand-cart.drawio", "Multi-brand shared cart")
    c = [24, 344, 664, 984, 1304]
    W = 260

    # ================================================================== page 1: one cart, many brands
    p = d.page("1 One cart, many brands", 1700, 1060)
    fr(p, "One basket holds lines of several brands. Each brand's lines are priced and checked with that brand's own id",
       DOC + " sections 1 to 5; P-59, P-61, P-31",
       ["O-56: confirm the meaning. Read as 'share': one cart, split into one order per brand. A cart shared by several people is not designed",
        "O-59: which brands may share a basket, and which app hosts it (a brand app is proposed)",
        "O-60: may a voucher, a campaign, or points span brands? Not in the first draft"])
    p.lane("L1", 24, 100, 1652, 150, "What the shopper does, in the app of one brand (the entry brand)", "http")
    p.box("u1", 44, 140, 360, 90, "Customer app of Brand A", ["adds a dish from Brand A, then a dish", "from Brand B. One cart, one screen"], kind="http", parent="L1", step=1)
    p.box("u2", 464, 140, 360, 90, "customer-bff (Brand A)", ["x-brand-id = A for every call.", "The token is for Brand A only (P-40)"], kind="enginew", parent="L1")
    p.box("u3", 884, 140, 360, 90, "Cart &amp; Order: UpdateCart", ["one basket per (entry brand, customer).", "Replaces the whole basket, checks version"], kind="enginew", parent="L1", step=2)
    p.edge("u1", "u2", "http", None, sp="r", dp="l")
    p.edge("u2", "u3", "grpc", None, sp="r", dp="l")
    p.lane("L2", 24, 280, 1652, 230, "Inside the basket: one brand group per brand, each line has its own brand_id", "engine")
    p.box("g1", 44, 330, 380, 150, "Brand A group (entry brand)", ["lines of A", "store, delivery or pickup", "voucher codes of A", "its own quote"], kind="enginew", parent="L2", dashed=True, step=3)
    p.box("g2", 464, 330, 380, 150, "Brand B group", ["lines of B", "needs the switch on in A and B,", "an enabled membership, a live store", "its own store and fulfillment"], kind="enginew", parent="L2", dashed=True)
    p.box("g3", 884, 330, 380, 150, "Brand C group (optional)", ["the same rules as B.", "A table tab (postpaid) is never", "in a basket: one brand, one store", "(P-61)"], kind="enginew", parent="L2", dashed=True)
    p.box("gn", 1304, 330, 340, 150, "Guest basket", ["a guest cart stays on the device", "and is one brand only. A cross-brand", "basket needs a signed-in customer"], kind="note", parent="L2", align="left", valign="top")
    p.fan("u3", ["g1", "g2", "g3"], kind="plain", side="b", trunk=262)
    p.lane("L3", 24, 540, 1652, 190, "Priced and checked per group, in parallel, with that group's brand in x-brand-id (new, flagged)", "grpc")
    ks = [("k1", "Catalog", ["PriceLines per brand.", "No price is stored"]),
          ("k2", "Voucher &amp; Campaign", ["EvaluateBasket per brand.", "No deal spans brands"]),
          ("k3", "Brand &amp; Store", ["ResolveStore per brand and", "the cross_brand_basket switch"]),
          ("k4", "Identity &amp; Profile", ["GetMembership: is the customer", "enabled in this brand (P-40)"]),
          ("k5", "Delivery", ["GetQuote per delivery group.", "One fee per brand order"])]
    for i, (id_, t, dd) in enumerate(ks):
        p.box(id_, 44 + i * 322, 600, 290, 100, t, dd, kind="grpc", parent="L3", step=(4 if i == 0 else None))
    p.edge("g2", "k3", "grpc", "each group, in parallel", sp="b", dp="t", lab=0.55)
    p.lane("L4", 24, 760, 1652, 140, "Stays per brand, not shared (D-11)", "data")
    p.box("n1", 44, 810, 1600, 70, "Wallet, loyalty points, vouchers, the invoice and receipt, the delivery fee, the POS ticket, and the payment account", ["the grand total on the screen is the sum of the brand totals, for display only. It is not stored"], kind="data", parent="L4")

    # ================================================================== page 2: checkout and split
    q = d.page("2 Checkout: split into brand orders, one gate, partial failure", 1700, 1160)
    fr(q, "Checkout: one order per brand, one payment per brand order, and nothing is placed until every payment is authorized",
       DOC + " section 6; P-60, P-09, P-16, P-32, P-10",
       ["O-57: one combined payment instead of one per brand? Needs finance and legal. Reverses one provider per brand",
        "O-58: all-or-nothing before placing (proposed), or independent orders? What the shopper sees on a late rejection",
        "O-04: the payment window (an assumption: 15 minutes)"])
    q.box("a1", c[0], 125, W, 110, "PlaceBasket", ["idempotency_key, basket_version,", "expected total for each brand group"], kind="http", step=1)
    q.box("a2", c[1], 125, W, 110, "Order: check every group", ["in parallel: ResolveStore, PriceLines,", "GetQuote, EvaluateBasket"], kind="enginew", step=2)
    q.box("a3", c[2], 125, W, 110, "One transaction", ["basket order (gate: authorizing) + one", "child order per brand. Basket locked"], kind="enginew", step=3)
    q.box("a4", c[3], 125, W, 110, "Voucher holds", ["ReserveRedemptions for each", "child order, as in P-32"], kind="grpc")
    q.box("a5", c[4], 125, W, 110, "Payment per child", ["CreateTransaction, key", "basket_order_id:brand_id:attempt"], kind="grpc", step=4)
    for a, b in (("a1", "a2"), ("a2", "a3"), ("a3", "a4"), ("a4", "a5")):
        q.edge(a, b, "plain", None, sp="r", dp="l")
    q.box("b5", c[4], 285, W, 110, "Each brand's gateway", ["its own Omise account. One", "authorize_url for each child"], kind="http")
    q.box("b4", c[3], 285, W, 110, "Shopper pays each child", ["one pay step per brand, with 3DS.", "Retry one failed brand is allowed"], kind="http", step=5)
    q.box("b3", c[2], 285, W, 110, "Webhooks", ["payment.requested {webhook}, then", "payment.events {authorized | failed}"], kind="fact", step=6)
    q.box("b2", c[1], 285, W, 110, "Order marks each child", ["authorized, as its event arrives.", "Nothing is placed yet"], kind="enginew", step=7)
    q.box("b1", c[0], 285, W, 110, "GATE: all authorized", ["one commit: every child placed,", "basket deleted. Then step 9"], kind="enginew", step=8)
    q.edge("a5", "b5", "http", "charge", sp="b", dp="t")
    q.edge("b5", "b4", "http", "shopper", sp="l", dp="r")
    q.edge("b4", "b3", "fact", None, sp="l", dp="r")
    q.edge("b3", "b2", "fact", "consume", sp="l", dp="r")
    q.edge("b2", "b1", "plain", None, sp="l", dp="r")
    q.box("c1", c[0], 445, W, 110, "order.events {placed}", ["one per child, key brand_id:order_id,", "payload has basket_order_id"], kind="fact", step=9)
    q.box("c2", c[1], 445, W, 110, "Each child is an ordinary order", ["its own POS ticket, accept or reject,", "capture or void, delivery"], kind="enginew")
    q.box("c3", c[2], 445, W, 110, "Per brand after that", ["wallet, points, invoice, tracking", "and refund stay with each child"], kind="enginew")
    q.edge("b1", "c1", "fact", "publish", sp="b", dp="t")
    q.edge("c1", "c2", "plain", None, sp="r", dp="l")
    q.edge("c2", "c3", "plain", None, sp="r", dp="l")
    q.lane("F", 24, 600, 1652, 280, "When something fails", "fail")
    q.box("f1", 44, 650, 500, 210, "Before the gate: all or nothing", ["a payment fails, 3DS is abandoned, or the window ends.", "Void every authorized hold, cancel every unplaced child,", "release the voucher holds, unlock the basket.", "One clear message. The shopper may retry one", "failed payment inside the window first."], kind="fail", parent="F", align="left", valign="top", size=13)
    q.box("f2", 584, 650, 500, 210, "After the gate: each child alone", ["Brand B's POS rejects: only B is voided and refunded.", "Brand A keeps cooking. The kitchens cannot be recalled,", "so all-or-nothing after the gate is not offered.", "The shopper is told per child. A delivery failure follows", "Delivery's normal path for that child (O-14)."], kind="fail", parent="F", align="left", valign="top", size=13)
    q.box("f3", 1124, 650, 520, 210, "Crash or a repeat", ["PlaceBasket twice returns the same basket order and the", "same children. A crash resumes from the last committed", "status. The sweeper finds a basket with every child", "authorized and commits the gate (idempotent), or voids an", "expired one. A child pays only with its own key (P-01)."], kind="fail", parent="F", align="left", valign="top", size=13)
    q.text("n1", 24, 900, 1652, 40, "<b>Alternatives not taken:</b> independent orders with no gate (a shopper could pay brand A and fail on B), and one combined payment for all brands (needs a group merchant of record, a settlement split, and a tax invoice per brand: O-57).",
           size=12, color="#475569")

    # ================================================================== page 3: stays per brand
    r = d.page("3 What stays per brand, and the open questions", 1700, 1000)
    fr(r, "What stays per brand, what is only for the first draft, and what the owner still has to decide",
       DOC + " sections 7, 9, 11; P-59, P-60, P-61, D-11",
       ["O-56 to O-60: meaning, one payment or many, all-or-nothing, scope and host, deals",
        "Assumption (P-66): about 5 percent of orders come from a basket, 2.2 brands on average",
        "Order count is the same as separate checkouts. Downstream calls rise about 5 percent"])
    cells = [("Payment account", ["each child pays on its brand's own", "gateway account (one provider per brand)"]),
             ("Tender", ["one tender per child order (P-16).", "Brand A by wallet, brand B by card, is fine"]),
             ("Wallet", ["the child's brand wallet. No cross-brand", "balance (D-11, O-19)"]),
             ("Loyalty", ["points earned per child on completed", "(D-11, O-20)"]),
             ("Vouchers and campaigns", ["per brand. A code attaches to the group", "it is valid for, or invalid_for_brand"]),
             ("Delivery and fee", ["one delivery, one quote and one fee per", "child. A shared rider is Later (O-59)"]),
             ("Invoice and receipt", ["one per child, with that brand's invoice", "header. The legal seller: to confirm (O-57)"]),
             ("Tracking and messages", ["GetBasketOrder groups the children. Each", "child has its own status and message"]),
             ("Refund", ["per child, as today. The other children", "are untouched"]),
             ("Postpaid table tab", ["always one brand and one store.", "A basket never makes a postpaid order"]),
             ("AI assistant", ["writes only through UpdateCart (P-34),", "under the same brand checks. Cannot place"]),
             ("Legacy brands (P-39)", ["a child goes through the legacy adapter.", "The gate needs its authorization too"])]
    for i, (t, dd) in enumerate(cells):
        r.box("x%d" % i, 24 + (i % 4) * 415, 110 + (i // 4) * 130, 395, 110, t, dd, kind="enginew", dashed=(i in (9, 10, 11)))
    r.lane("LT", 24, 510, 1652, 200, "Later, not in the first draft", "neutral")
    later = [("One combined payment", ["a group merchant of record,", "a settlement split (O-57)"]),
             ("One rider for several stores", ["a shared quote and fee,", "with an allocation rule (O-59)"]),
             ("Cross-brand deals", ["a voucher, a campaign or points", "across brands (O-60, O-19, O-20)"]),
             ("A basket shared by people", ["a table or a group order: merge,", "owner, payer (O-56)"])]
    for i, (t, dd) in enumerate(later):
        r.box("l%d" % i, 44 + i * 405, 560, 380, 120, t, dd, kind="neutral", parent="LT", dashed=True)
    r.text("n1", 24, 730, 1652, 44, "<b>Flags:</b> principle 6 (a call's brand is set by Order for a basket group, not copied from Kong, after the switch and membership checks), P-31 and P-09 (amended and extended), and the two-hop rule (the fan-out is parallel, so the chain is not longer).",
           size=12, color="#475569")
    return d
