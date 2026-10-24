"""05 - OMS multi-vendor POS adapters (4 pages)."""
from drawio_lib import Diagram, frame

REF = "docs/design/pos-adapters.md; docs/architecture.md P-36"


def build():
    d = Diagram("05-oms-pos-adapters.drawio", "OMS POS adapters")

    # ================================================================== page 1: structure
    p = d.page("1 Port, registry and adapters", 1560, 1040)
    frame(p, "OMS and the POS: one port, one adapter per vendor, BSL is the first",
          REF + "; docs/design/tech-stack.md section 3",
          ["P-36: reverses the old guardrail 'several POS proxies from day one'",
           "O-28: real vendor limits and capability matrix still unknown",
           "To verify: should the BSL adapter later call BSL directly, not via the proxy?"])
    p.lane("oms", 24, 100, 1100, 620, "Cart &amp; Order (the OMS): Go, hexagonal", "engine")
    p.box("uc", 44, 150, 190, 100, "Use cases", ["PlaceOrder, the POS worker,", "apply a POS update"], kind="enginew", parent="oms")
    p.box("port", 284, 150, 190, 100, "PosGateway port", ["Submit, Cancel, Status,", "ReadBack, Capabilities"], kind="enginew", parent="oms", dashed=True)
    p.box("reg", 524, 150, 190, 100, "Registry", ["(brand_id, store_id) to", "adapter + capability flags"], kind="enginew", parent="oms", dashed=True)
    p.box("conn", 524, 300, 190, 130, "pos_connection", ["one row per brand and store:", "vendor, routing, credentials_ref", "(Vault path), flags, promo_mode"], kind="data", parent="oms", dashed=True)
    adapters = [("ad.bsl", "adapter pos/bsl", ["first adapter; BSL proxy is its transport"], False),
                ("ad.prom", "adapter pos/promise", ["written when a brand needs it"], True),
                ("ad.vivi", "adapter pos/vivi", ["written when a brand needs it"], True),
                ("ad.next", "next vendor adapter", ["one Go package per vendor"], True)]
    for i, (id_, t, dd, dash) in enumerate(adapters):
        p.box(id_, 790, 150 + i * 100, 310, 80, t, dd, kind="enginew", parent="oms", dashed=dash)
    p.box("cons", 44, 540, 300, 110, "Order consumer", ["applies a POS update by rank and version", "rules R1 to R7, then Ack"], kind="enginew", parent="oms")
    p.edge("uc", "port", "grpc", "calls", sp="r", dp="l")
    p.edge("port", "reg", "grpc", "asks", sp="r", dp="l")
    p.edge("reg", "conn", "data", "reads", sp="b", dp="t")
    p.fan("reg", [a[0] for a in adapters], "grpc", side="r", trunk=752)
    p.lane("ven", 1230, 100, 290, 450, "POS vendor systems", "http")
    vens = [("v.bsl", "BSL POS", False), ("v.prom", "Promise POS (may come)", True), ("v.vivi", "VIVI POS (may come)", True),
            ("v.next", "other POS", True)]
    for i, (id_, t, dash) in enumerate(vens):
        p.box(id_, 1250, 150 + i * 100, 250, 80, t, [], kind="http", parent="ven", dashed=dash)
        p.edge(adapters[i][0], id_, "http", "vendor request" if i == 0 else None, sp="r", dp="l", lab=0.3)
    p.box("pa", 1250, 770, 250, 100, "partner-adapter", ["the only webhook entry", "vendor mapper (Bun) per POS"], kind="enginew")
    p.box("topic", 44, 770, 300, 100, "order.requested", ["command {pos_status}", "one canonical PosUpdate"], kind="cmd")
    p.edge("ven", "pa", "http", "signed webhooks", sp=("b", (1375 - 1230) / 290.0), dp=("t", 0.5), )
    p.edge("pa", "topic", "cmd", "publish", sp="l", dp="r")
    p.edge("topic", "cons", "cmd", "consume", sp=("t", 0.5), dp=("b", 0.5))
    p.text("n1", 790, 590, 330, 110, "Adding a vendor = one Go adapter package + one Bun mapper. Checkout rules do not change. "
           "Differences between vendors are declared as capability flags (page 4).", size=11, color="#475569", parent="oms")
    p.text("n2", 400, 868, 800, 44, "<b>Out</b>: use case, port, registry, vendor adapter, POS vendor.<br><b>In</b>: POS vendor, partner-adapter, "
           "order.requested, Order consumer. A BFF never calls a POS. A domain never exposes a webhook.", size=11, color="#475569")

    # ================================================================== page 2: rules R1 to R7
    q = d.page("2 Applying a POS update (R1 to R7)", 1700, 1160)
    frame(q, "A POS update is untrusted input: seven rules decide what it may change",
          REF + " section 5 and 9; docs/kafka-topics.md (order.requested)",
          ["P-06: facts dedupe on version, commands on event_id",
           "O-32: what to do when the POS total disagrees with the priced order is open",
           "The 2 minute settle delay is an assumption"])
    q.box("in", 24, 130, 210, 90, "order.requested", ["command {pos_status}", "one canonical PosUpdate"], kind="cmd")
    q.box("r1", 284, 115, 210, 120, "R1: event_id already seen?", [], kind="grpc", shape="diamond")
    q.box("r2", 534, 115, 290, 120, "R2, R3: rank higher, not terminal?", [], kind="grpc", shape="diamond")
    q.box("apply", 864, 130, 240, 90, "Apply the status", ["one transaction: state + outbox row", "(R4: skipped ranks are fine)"], kind="enginew")
    q.box("eff", 1164, 130, 290, 90, "What it moves in the saga", ["received = accepted, then capture", "rejected = void; ready, completed"], kind="enginew")
    q.edge("in", "r1", "cmd", None, sp="r", dp="l")
    q.edge("r1", "r2", "grpc", "no", sp="r", dp="l")
    q.edge("r2", "apply", "grpc", "yes", sp="r", dp="l")
    q.edge("apply", "eff", "grpc", "then", sp="r", dp="l")
    q.box("d1", 284, 330, 210, 80, "Duplicate", ["no-op, Ack", "outcome: duplicate"], kind="neutral")
    q.box("d2", 554, 330, 250, 80, "Stale or terminal", ["recorded, not applied; Ack", "outcome: stale"], kind="neutral")
    q.edge("r1", "d1", "grpc", "yes", sp="b", dp="t")
    q.edge("r2", "d2", "grpc", "no", sp="b", dp="t")
    q.box("r5", 864, 510, 240, 100, "R5: reported totals", ["written to reported_* on pos_ticket,", "never to the order's price lines"], kind="enginew")
    q.edge("apply", "r5", "grpc", "same transaction", sp=("b", 0.5), dp=("t", 0.5), via=[(984, 300), (984, 510)], lab=0.5)
    q.box("r6", 544, 495, 230, 130, "R6: vendor_version newer?", [], kind="grpc", shape="diamond")
    q.box("r7", 264, 495, 230, 130, "R7: zero total after a good one?", [], kind="grpc", shape="diamond")
    q.box("ow", 24, 520, 190, 80, "Overwrite reported_*", ["latest good total"], kind="enginew")
    q.edge("r5", "r6", "grpc", "newer", sp="l", dp="r")
    q.edge("r6", "r7", "grpc", "yes", sp="l", dp="r")
    q.edge("r7", "ow", "grpc", "no", sp="l", dp="r")
    q.box("d3", 544, 720, 230, 80, "Older update", ["keep the stored total", "outcome: stale"], kind="neutral")
    q.box("d4", 264, 720, 230, 100, "Anomaly", ["not applied; flag the ticket for", "reconciliation. outcome: anomaly"], kind="fail")
    q.edge("r6", "d3", "grpc", "no", sp="b", dp="t")
    q.edge("r7", "d4", "fail", "yes", sp="b", dp="t")
    q.box("out", 1164, 330, 290, 130, "Every update gets an outcome",
          ["applied, duplicate, stale or anomaly:", "written to the ticket history and, best effort,", "to the MongoDB payload log (payload_ref)"], kind="data", dashed=True)
    q.box("rec", 24, 880, 1430, 120, "Reconciliation cron in Order (same sweeper pattern as P-10)",
          ["When: a ticket reaches received plus a settle delay (assumption: 2 minutes), again at completed, and for every ticket flagged by R7.",
           "Compares: agreed total against reported total, the set of SKUs, and whether the discount total is present (ReadBack when the vendor supports it).",
           "Result: match, mismatch_total, mismatch_lines, promo_dropped or unknown, into a pos_reconciliation row, a metric and the CSC queue. It is not a Kafka topic.",
           "It never changes price lines, never changes the capture amount and never messages the shopper (rule for a mismatch: O-32)."],
          kind="enginew", align="left", valign="top")
    q.text("note", 1164, 520, 400, 100, "Rules run in this order inside one transaction. A lower rank never moves a ticket backward. "
           "Terminal states (rejected, cancelled, completed) never change.", size=11, color="#475569")

    # ================================================================== page 3: what the adapter absorbs
    r = d.page("3 What the adapter has to absorb", 1700, 1100)
    frame(r, "What BSL taught us: behaviours any POS adapter has to absorb",
          REF + " section 10",
          ["O-28: all BSL values are the owner's UAT observations (October 2026), not vendor documentation",
           "O-32: the rule for a total that disagrees is open",
           "Nothing is hardcoded as 'BSL logic': it is vendor profile data and generic rules"])
    r.text("h1", 24, 84, 760, 24, "<b>Observed with BSL (UAT, October 2026)</b>", size=13, color="#0F172A")
    r.text("h2", 924, 84, 752, 24, "<b>How the design absorbs it</b>", size=13, color="#0F172A")
    pairs = [
        ("Status webhooks arrive within about a second, and some are duplicated", "R1: dedupe on a deterministic event_id (UUIDv5 of vendor, vendor_ref, status, version)"),
        ("Updates can arrive out of order", "R2, R3, R4: rank, terminal states, skipped ranks are fine. status_updates_ordered = false"),
        ("A late update can overwrite the total, and an empty check can reset the net total to 0 (the till bill stayed correct)", "R5, R6, R7: reported totals kept apart from price lines, applied by version, regression guard; reconciliation"),
        ("Some promotions are silently dropped, so the POS total can differ from our priced order", "promo_mode (passthrough, flatten, discount_line) and the reconciliation result promo_dropped"),
        ("The vendor needs per-store routing values (an enterprise unit and an organization); a wrong default unit never reached the POS", "pos_connection.routing, validated against the vendor schema; a missing value never falls back to a default unit"),
        ("Pickup works. Delivery is not available yet", "supports_pickup = true, supports_delivery = false in the BSL profile; flip the flag when the vendor ships delivery"),
        ("Status names run OrderPlaced, ReceivedForFulfillment, InFulfillment, ReadyForPickup", "The BSL mapper table to canonical submitted, received, in_progress, ready"),
        ("A short reference on the till slip matches the vendor's reference", "Stored as vendor_ref and shown to CSC"),
    ]
    for i, (a, b) in enumerate(pairs):
        y = 118 + i * 88
        r.box("o%d" % i, 24, y, 760, 72, "", [a], kind="http", align="left", size=12, step=i + 1)
        r.box("m%d" % i, 924, y, 752, 72, "", [b], kind="enginew", align="left", size=12)
        r.edge("o%d" % i, "m%d" % i, "grpc", "absorbed by", sp="r", dp="l")
    r.text("n1", 24, 830, 1650, 60, "A new vendor gets its own row of observations like this one. The list is the checklist for a new adapter: "
           "list its sensitive paths for masking, its status table, its routing values, its capability flags.", size=12, color="#475569")

    # ================================================================== page 4: per-brand selection and capabilities
    s = d.page("4 Per-brand selection and capability flags", 1700, 1000)
    frame(s, "Each store picks its POS vendor by data; capability flags say what that vendor can do",
          REF + " section 6, 7 and 10; docs/design/brand-configuration.md section 3",
          ["O-28: flag values for BSL are assumptions until the vendor confirms",
           "P-37: a shopper action is allowed when vendor, brand feature and store setup all say yes",
           "The three stores below are illustrative, not real stores"])
    rows = [("Brand A, store 1", "vendor = bsl", "routing: enterprise unit, organization (request headers); credentials_ref: Vault path; promo_mode: flatten", "adapter pos/bsl", "BSL POS", False),
            ("Brand B, store 7", "vendor = promise (illustrative, may come)", "routing and credentials as the vendor needs; capability_overrides per store", "adapter pos/promise", "Promise POS", True),
            ("Brand C, store 3", "vendor = vivi (illustrative, may come)", "its own routing schema, validated on write", "adapter pos/vivi", "VIVI POS", True)]
    for i, (st, ven, rest, ad, pos, dash) in enumerate(rows):
        y = 120 + i * 130
        s.box("st%d" % i, 24, y, 220, 90, st, ["a store (brand_id, store_id)"], kind="enginew")
        s.box("pc%d" % i, 324, y, 540, 90, "pos_connection row: " + ven, [rest], kind="data", dashed=dash, align="left")
        s.box("ad%d" % i, 944, y, 230, 90, ad, ["picked by the registry"], kind="enginew", dashed=dash)
        s.box("vp%d" % i, 1254, y, 200, 90, pos, ["vendor system"], kind="http", dashed=dash)
        s.edge("st%d" % i, "pc%d" % i, "data", "has one", sp="r", dp="l")
        s.edge("pc%d" % i, "ad%d" % i, "grpc", "registry reads", sp="r", dp="l")
        s.edge("ad%d" % i, "vp%d" % i, "http", None, sp="r", dp="l")
    s.box("nopos", 1494, 120, 182, 350, "No valid pos_connection",
          ["the store cannot take orders: ResolveStore still says open, but checkout fails with FAILED_PRECONDITION and the brand readiness check fails",
           "A missing routing value never sends a ticket to a default unit."], kind="fail", size=12, align="left", valign="top")
    s.box("flags", 24, 520, 840, 330, "Capability flags (data, not code; a flag needs a behaviour for false)",
          ["supports_pickup: false means no pickup on this POS",
           "supports_delivery: false means PlaceOrder returns FAILED_PRECONDITION (fulfillment_not_supported) and the app hides it",
           "supports_promotions_passthrough: false means OMS uses promo_mode instead",
           "supports_modify: false means a replace is cancel then submit",
           "supports_cancel_after_accept: false means a late cancel goes to CSC",
           "supports_status_webhooks: false means OMS polls Status on a schedule",
           "status_updates_ordered: not set by default, so R2 and R6 always run",
           "supports_idempotent_submit: false means read Status before any re-send",
           "supports_bill_readback: false means reconciliation reports unknown",
           "supports_sold_out_push: false means sold-out comes from the master feed only",
           "promo_mode: passthrough, flatten (default), or discount_line (to verify per vendor)"],
          kind="enginew", align="left", valign="top", size=12)
    s.box("bsl", 900, 520, 440, 250, "BSL starting profile (all assumptions)",
          ["supports_pickup = true", "supports_delivery = false", "supports_promotions_passthrough = false", "supports_modify = false",
           "supports_status_webhooks = true", "status_updates_ordered = false", "supports_idempotent_submit = unknown (treat as false)",
           "supports_bill_readback = unknown (treat as false)", "guard_total_regression = true"], kind="enginew", dashed=True, align="left", valign="top", size=12)
    s.box("eff", 1380, 520, 296, 250, "Effective capability",
          ["= vendor supports it", "AND the store's POS setup allows it", "AND the brand has the feature on", "", "Delivery also needs a fleet provider for the store (P-19)."],
          kind="grpc", align="left", valign="top", size=12)
    s.text("n1", 900, 800, 776, 50, "Flags live on the vendor profile and can be overridden per store in pos_connection (capability_overrides). "
           "A flag is only added when a vendor needs it and it has a behaviour for false.", size=11, color="#475569")
    return d
