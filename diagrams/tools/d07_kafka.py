"""07 - Kafka topic map (6 pages)."""
from drawio_lib import Diagram, frame

REF = "docs/kafka-topics.md; docs/architecture.md section 4 (topics), P-06, P-42"
QS = ["P-42: the list of 12 may grow, only through the three-answers rule; candidates are not topics",
      "O-36: who creates a topic and its Schema Registry subject (DevOps or the domain team)",
      "A topic needs a named producer and consumer outside the owner; no personal data rides on it (principle 8)"]


def strips(pg, items, y0=104, topic_w=520):
    y = y0
    for k, (name, kind, prod, tl, cons) in enumerate(items):
        n = max(len(prod), len(tl) + 1, len(cons))
        h = max(100, 52 + 20 * n)
        pg.box("p%d" % k, 24, y, 440, h, "Producers", prod, kind="enginew", align="left", valign="top", size=13)
        pg.box("t%d" % k, 560, y, topic_w, h, name, tl, kind=kind, align="left", valign="top", size=13)
        pg.box("c%d" % k, 1250 - (520 - topic_w), y, 426 + (520 - topic_w), h, "Consumers", cons, kind="enginew", align="left", valign="top", size=13)
        ek = "cmd" if kind == "cmd" else "fact"
        pg.edge("p%d" % k, "t%d" % k, ek, "publish", sp="r", dp="l")
        pg.edge("t%d" % k, "c%d" % k, ek, "consume", sp="r", dp="l")
        y += h + 22
    return y


def strip_page(d, name, title, items):
    pg = d.page(name, 1700, 900)
    y = strips(pg, items)
    pg.h = y + 150
    frame(pg, title, REF + " (Registry)", QS)
    return pg


def build():
    d = Diagram("07-kafka-topic-map.drawio", "Kafka topic map")

    # ---------------------------------------------------------------- page 1: all 12
    p = d.page("1 All 12 topics", 1700, 840)
    frame(p, "Twelve Kafka topics: five commands, seven facts, nothing else",
          REF, QS)
    p.text("h1", 24, 84, 1650, 24, "<b>Commands</b> (purple): one per domain, named domain.requested. A command asks the owner to do something; the owner consumes it.", size=13, color="#6D28D9")
    cmds = [("catalog.requested", "Catalog", "brand_id:store_id:sku_id", "7 days, 6 partitions", "POS sold-out webhook"),
            ("order.requested", "Order", "brand_id:order_id", "7 days, 12 partitions", "create, replace, cancel, POS status"),
            ("payment.requested", "Payment", "brand_id:transaction_id", "7 days, 12 partitions", "capture, void, webhook, payout"),
            ("delivery.requested", "Delivery", "brand_id:delivery_id (rider: mfg:rider_ref)", "7 days, 12 partitions", "provider_update, rider_sync, roster_sync"),
            ("notification.requested", "Notification", "brand_id:notification_id", "7 days, 6 partitions", "send, broadcast, receipt")]
    for i, (n, o, k, r, v) in enumerate(cmds):
        p.box("c%d" % i, 24 + i * 332, 116, 316, 150, n, ["owner: " + o, "key: " + k, r, "carries: " + v], kind="cmd", align="left", valign="top", size=13)
    p.text("h2", 24, 300, 1650, 24, "<b>Facts</b> (green): what already happened. The owner publishes; everyone else reacts. Compacted state keeps the latest value; lifecycle keeps 7 days.", size=13, color="#047857")
    facts = [("brand.changed", "Brand &amp; Store", "brand_id", "compacted, 6 partitions", "latest brand"),
             ("store.changed", "Brand &amp; Store", "brand_id:store_id", "compacted, 6 partitions", "hours, status, zone, group_id"),
             ("catalog.menu.published", "Catalog", "brand_id:menu_id:channel", "compacted, 6 partitions", "thin: version and effective_at"),
             ("catalog.availability.changed", "Catalog", "brand_id:store_id:sku_id", "compacted, 6 partitions", "sold out or back"),
             ("order.events", "Order", "brand_id:order_id", "7 days, 12 partitions", "placed, accepted, rejected, ready, completed, cancelled"),
             ("payment.events", "Payment", "brand_id:transaction_id", "7 days, 12 partitions", "authorized, captured, failed, voided, refunded, paid_out, payout_failed"),
             ("delivery.events", "Delivery", "brand_id:delivery_id", "7 days, 12 partitions", "dispatched, rider_assigned, picked_up, delivered, failed, cancelled")]
    for i, (n, o, k, r, v) in enumerate(facts):
        p.box("f%d" % i, 24 + i * 236, 332, 224, 230, n, ["owner: " + o, "key: " + k, r, "carries: " + v], kind="fact", align="left", valign="top", size=12)
    p.text("n1", 24, 600, 1650, 80, "Not topics: <b>&lt;service&gt;.dlq</b> (one per consuming service, operations only). A wallet spend, a charge, a refund, OTP and every read are gRPC because someone is waiting (D-09). "
           "Candidates such as customer.changed, order.payload.captured and audit.events are not registered and are never drawn as topics (page 6).", size=12, color="#475569")

    # ---------------------------------------------------------------- page 2: brand and catalog
    strip_page(d, "2 Brand, store and catalog topics", "Who writes and who reads: brand, store and catalog topics", [
        ("brand.changed", "fact", ["Brand &amp; Store"], ["fact, compacted, key brand_id", "latest brand: status, features"], ["Catalog"]),
        ("store.changed", "fact", ["Brand &amp; Store"], ["fact, compacted, key brand_id:store_id", "hours, status, zone, group_id; open-now is derived"],
         ["Catalog", "Delivery (syncs the store to the fleet provider)", "Order does not consume it: ResolveStore is live"]),
        ("catalog.requested", "cmd", ["partner-adapter (POS sold-out webhook)"], ["command, key brand_id:store_id:sku_id", "7 days"], ["Catalog"]),
        ("catalog.menu.published", "fact", ["Catalog"], ["fact, compacted, thin, key brand_id:menu_id:channel", "version and effective_at only; the reader calls GetMenu(version)"],
         ["partner-adapter", "Catalog cache"]),
        ("catalog.availability.changed", "fact", ["Catalog"], ["fact, compacted, key brand_id:store_id:sku_id", "sold out is its own topic because its rate differs"],
         ["partner-adapter", "Catalog cache"]),
    ])

    # ---------------------------------------------------------------- page 3: order and payment
    strip_page(d, "3 Order and payment topics", "Who writes and who reads: order and payment topics", [
        ("order.requested", "cmd", ["partner-adapter (aggregator create, replace, cancel;", "POS status from the vendor mapper)"],
         ["command, key brand_id:order_id, 12 partitions", "one oneof: create, replace, cancel, POS status"], ["Order"]),
        ("order.events", "fact", ["Order"], ["lifecycle, key brand_id:order_id, 7 days", "placed, accepted, rejected, ready, completed, cancelled"],
         ["Delivery (acts on accepted and cancelled)", "Notification", "Loyalty", "Voucher", "partner-adapter"]),
        ("payment.requested", "cmd", ["Order (capture, void)", "webhook-adapter (verified gateway webhook)", "Delivery (payout)"],
         ["command, key brand_id:transaction_id, 12 partitions", "capture, void, webhook, payout; charge and refund are gRPC"], ["Payment"]),
        ("payment.events", "fact", ["Payment"], ["lifecycle, key brand_id:transaction_id, 7 days", "authorized, captured, failed, voided, refunded, paid_out, payout_failed"],
         ["Order", "Wallet (captured with purpose=top_up only)", "Notification (refunded only)", "Delivery (paid_out, payout_failed only)"]),
    ])

    # ---------------------------------------------------------------- page 4: delivery and notification
    strip_page(d, "4 Delivery and notification topics", "Who writes and who reads: delivery and notification topics", [
        ("delivery.requested", "cmd", ["partner-adapter (verified provider webhook)"],
         ["command, 12 partitions", "provider_update: key brand_id:delivery_id", "rider_sync, roster_sync: key mfg:rider_ref, thin pointers"], ["Delivery"]),
        ("delivery.events", "fact", ["Delivery"], ["lifecycle, key brand_id:delivery_id, 7 days", "dispatched, rider_assigned, picked_up, delivered, failed, cancelled"],
         ["Order (delivered, failed, cancelled)", "Notification", "partner-adapter (FAAS brand callback)", "Payment (Statement invoices a FAAS brand)"]),
        ("notification.requested", "cmd", ["Voucher &amp; Campaign (broadcast, send)", "Loyalty", "Wallet", "webhook-adapter (receipt after signature check)"],
         ["command, key brand_id:notification_id, 6 partitions", "send, broadcast (thin: an S3 key), receipt", "never a phone, email or LINE id"], ["Notification"]),
    ])

    # ---------------------------------------------------------------- page 5: envelope
    t = d.page("5 One record, from commit to Ack", 1700, 1060)
    frame(t, "Every record has the same envelope and the same delivery path",
          REF + " (Rules 5, 6, 7; Envelope)", ["P-06: facts dedupe on version, commands on event_id",
                                          "Three retries and the <service>.dlq are the documented design; backoff timings are not set",
                                          "O-36: who creates topics and subjects"])
    t.box("app", 24, 130, 300, 120, "Producer: domain app", ["one Postgres transaction:", "state change + outbox row"], kind="enginew", step=1)
    t.box("relay", 394, 130, 300, 120, "Outbox relay", ["same app, mode worker", "no Debezium, no Connect cluster"], kind="enginew", step=2)
    t.box("topic", 764, 130, 360, 120, "Kafka topic", ["Confluent Cloud, Schema Registry,", "Protobuf, BACKWARD compatible"], kind="fact", step=3)
    t.box("cons", 1194, 130, 300, 120, "Consumer: domain app", ["run mode consumer"], kind="enginew", step=4)
    t.edge("app", "relay", "plain", "outbox row", sp="r", dp="l")
    t.edge("relay", "topic", "fact", "produce", sp="r", dp="l")
    t.edge("topic", "cons", "fact", "consume", sp="r", dp="l")
    t.box("dd", 1194, 330, 300, 100, "Dedupe", ["event_id for a command,", "version for a fact"], kind="grpc", step=5)
    t.box("ap", 1194, 510, 300, 100, "Apply", ["only when the version is newer"], kind="grpc", step=6)
    t.box("ack", 1194, 690, 300, 80, "Ack", ["no work for this variant is also an Ack"], kind="fact", step=7)
    t.edge("cons", "dd", "grpc", None, sp="b", dp="t")
    t.edge("dd", "ap", "grpc", "new", sp="b", dp="t")
    t.edge("ap", "ack", "grpc", "done", sp="b", dp="t")
    t.box("retry", 764, 510, 360, 100, "Retry inside the app", ["three tries with backoff", "no per-topic retry topic"], kind="fail")
    t.box("dlq", 764, 690, 360, 80, "&lt;service&gt;.dlq", ["one per consuming service; operations only"], kind="fail")
    t.edge("ap", "retry", "fail", "apply fails", sp="l", dp="r")
    t.edge("retry", "dlq", "fail", "still failing", sp="b", dp="t")
    t.box("env", 24, 330, 640, 230, "Envelope (same on every topic)",
          ["key: brand_id:aggregate id", "(rider variants: mfg:rider_ref)", "",
           "headers: event_id, event_type, brand_id,", "occurred_at, version, traceparent", "",
           "value: Protobuf, one oneof per topic",
           "no personal data on the bus (principle 8)"], kind="note", align="left", valign="top", size=13)
    t.text("n1", 24, 600, 700, 80, "A duplicate delivery changes nothing: the consumer sees the same event_id or version, does nothing, then Acks. "
           "Partitions: rule 9 says 6, except order.* and payment.* with 12; the registry also gives the delivery topics 12 (text to reconcile).", size=12, color="#475569")

    # ---------------------------------------------------------------- page 6: is it a topic?
    u = d.page("6 Is it a topic? The growth rule", 1700, 1180)
    frame(u, "Before adding a thirteenth topic, ask four questions in this order",
          REF + " (Growth policy; Candidates, not registered)", QS)
    qs = [("k1", "1. Is someone waiting?", "gRPC, not a topic", "grpc"),
          ("k2", "2. Can an existing topic carry it as one more oneof variant?", "Add the variant", "fact"),
          ("k3", "3. Is it only this service's own background work?", "Outbox table and a worker in the same app", "fact"),
          ("k4", "4. Crosses a boundary, with a named outside consumer?", "Write a proposal", "cmd")]
    for i, (id_, qt, ans, kind) in enumerate(qs):
        y = 120 + i * 200
        u.box(id_, 24, y, 460, 140, qt, [], kind="grpc", shape="diamond")
        u.box("a" + id_, 600, y + 30, 360, 80, ans, [], kind=kind, step=None)
        u.edge(id_, "a" + id_, "plain", "yes", sp="r", dp="l")
    for i in range(3):
        u.edge(qs[i][0], qs[i + 1][0], "plain", "no", sp="b", dp="t")
    u.box("nt", 600, 920, 360, 80, "Not a topic", ["no named consumer, so it is not built"], kind="fail")
    u.edge("k4", "nt", "fail", "no", sp=("b", 0.5), dp=("t", 0.5), via=[(254, 880), (780, 880)])
    u.box("prop", 1040, 120, 636, 220, "A proposal must contain",
          ["owner and kind (.requested, .changed, .published, .events)", "key, retention, partitions (sized with the scale assumptions)",
           "producers and consumers, by name", "the Protobuf value", "one line saying no personal data rides on it",
           "", "It changes, in order: the registry, the topics table in architecture.md section 3, the decision register, then the diagram.",
           "O-36: DevOps creates the topic and subject; who asks is open."], kind="note", align="left", valign="top", size=12)
    u.box("cand", 1040, 380, 636, 250, "Candidates, not registered: never draw them as topics",
          ["customer.changed (Identity): needs a second domain that reacts within seconds", "order.payload.captured (payload log): only if O-30 needs completeness and a Postgres capture row is rejected",
           "audit.events: when a SIEM or fraud consumer is chosen", "loyalty.events, wallet.events: nobody reacts today (D-11)", "",
           "Considered and covered: a topic per POS vendor (order.requested pos_status), a reconciliation topic (Order's table and CSC queue), brand feature switches (brand.changed)."],
          kind="fail", dashed=True, align="left", valign="top", size=12)
    u.text("n1", 1040, 660, 636, 70, "Signal to remove a topic: no consumer for a full release. v3 added none: every topic that came up failed one of the three answers.", size=12, color="#475569")
    return d
