"""06 - Order payload log (MongoDB), 4 pages."""
from drawio_lib import Diagram, frame

REF = "docs/design/order-payload-log.md; docs/architecture.md P-38"


def build():
    d = Diagram("06-order-payload-log-mongo.drawio", "Order payload log (MongoDB)")

    # ================================================================ page 1
    p = d.page("1 A parallel log beside the order", 1700, 1060)
    frame(p, "The payload log runs beside the order, never on its critical path",
          REF + " section 1, 3, 6",
          ["P-38: a second database engine, with the written reason in order-payload-log.md section 2",
           "O-29: Atlas hosting, region, private link, backup, keys (DevOps)",
           "O-30: debugging aid or audit record? That decides completeness and who may write"])
    p.lane("src", 24, 100, 520, 640, "Capture points: at the boundary, not inside business logic", "engine")
    caps = [("c1", "partner-adapter", ["raw webhook or API body (no secrets),", "then the canonical command"]),
            ("c2", "partner-bff", ["order creation from a partner:", "raw request, then converted"]),
            ("c3", "POS adapter (in Order)", ["canonical ticket, vendor request,", "vendor response"]),
            ("c4", "POS status mapper", ["raw webhook, then the canonical", "PosUpdate (partner-adapter)"]),
            ("c5", "Order consumer", ["the outcome: applied, duplicate,", "stale or anomaly, with order_id"]),
            ("c6", "Reconciliation cron (Order)", ["the vendor read-back and the result"])]
    for i, (id_, t, dd) in enumerate(caps):
        p.box(id_, 44, 150 + i * 92, 480, 76, t, dd, kind="enginew", parent="src")
    p.lane("proc", 660, 100, 400, 640, "In the same process (Go goroutine or Bun task)", "neutral")
    p.box("q", 690, 160, 340, 100, "Bounded in-memory queue", ["capture is a non-blocking put", "full: drop the oldest, count it"], kind="enginew", parent="proc")
    p.box("w", 690, 330, 340, 110, "Async writer", ["masks the payload in-process,", "batches inserts, short timeout,", "circuit breaker while Mongo is down"], kind="enginew", parent="proc")
    p.box("drop", 690, 520, 340, 120, "Gap in the trace, never a failed order", ["a pod crash loses what is in the queue;", "Mongo downtime loses records after the queue fills.", "Metrics: depth, dropped, written, latency"], kind="fail", parent="proc")
    p.edge("src", "q", "log", "non-blocking put", sp=("r", 0.17), dp="l", lab=0.5)
    p.edge("q", "w", "log", None, sp="b", dp="t")
    p.edge("w", "drop", "fail", "queue full or Mongo down", sp="b", dp="t")
    p.lane("mg", 1180, 100, 496, 340, "MongoDB Atlas on AWS (to confirm with DevOps)", "data", dashed=True)
    p.box("coll", 1210, 160, 436, 240, "order_payload_log", ["one collection, append-only, insert-only role", "payload kept as received, after masking", "read by order_id or correlation id only", "each document expires on its own date (ttl_at)"],
          kind="data", parent="mg", dashed=True)
    p.edge("w", "mg", "log", "insertMany", sp=("r", 0.5), dp=("l", 0.5))
    p.lane("truth", 660, 790, 1016, 120, "The truth stays in Aurora", "engine")
    p.box("pg", 700, 830, 450, 60, "Postgres order + outbox", ["commit, then the fact (principle 4)"], kind="enginew", parent="truth")
    p.box("rd", 1190, 830, 450, 60, "Order: GetOrderPayloadTrace", ["proposed door, via admin-bff, grant order.payload.read"], kind="enginew", parent="truth", dashed=True)
    p.edge("rd", "mg", "grpc", None, sp=("t", 0.5), dp=("b", 0.5), via=[(1415, 560), (1415, 440)])
    p.text("n1", 24, 770, 600, 120, "The log is not on the shopper path and no other domain reads it. "
           "If Mongo is down, orders still work. No Kafka topic carries a payload (principle 8, 1 MB limit).", size=12, color="#475569")

    # ================================================================ page 2
    q = d.page("2 Linking the log to the order", 1700, 1000)
    frame(q, "Three ids tie the log to the order, read in two steps",
          REF + " section 4 and 5",
          ["O-30: whether several writers (adapters and Order) are acceptable",
           "seq is ordered within one process only; across processes captured_at can be skewed (assumption)",
           "The trace is for a person to read, not for exact replay"])
    q.box("pg", 560, 100, 320, 80, "Postgres order", ["order_id (system of record)"], kind="enginew")
    recs = [("r1", "1 Adapter record, before the order exists",
             ["stage: raw_request, then converted", "correlation_id = C1", "external_ref = E1", "order_id = empty"]),
            ("r2", "2 POS webhook record",
             ["stage: webhook", "external_ref = E1 (often the only id)", "correlation_id = may be empty", "order_id = empty"]),
            ("r3", "3 Order outcome record",
             ["stage: outcome (applied, duplicate, stale, anomaly)", "order_id = O1", "correlation_id = C1", "external_ref = E1"])]
    for i, (id_, t, dd) in enumerate(recs):
        q.box(id_, 40 + i * 540, 260, 500, 110, t, dd, kind="data", align="left")
    q.edge("pg", "r3", "data", "same order_id", sp=("r", 0.5), dp=("t", 0.5), via=[(1290, 140)])
    q.text("cap", 40, 420, 1600, 50, "Order's outcome record carries all three ids together. That is what links the adapter records, written before the order existed, to the order.", size=12, color="#475569")
    steps = [("s1", "Find the records with this order_id", ["index { order_id, seq }"]),
             ("s2", "Collect their correlation_id and external_ref", ["C1 and E1 in the example"]),
             ("s3", "Fetch every record with any of those values", ["indexes on correlation_id and external_ref"]),
             ("s4", "Read them in seq order", ["payloads already masked"])]
    for i, (id_, t, dd) in enumerate(steps):
        q.box(id_, 40 + i * 410, 520, 350, 100, t, dd, kind="enginew", step=i + 1)
    for a, b in (("s1", "s2"), ("s2", "s3"), ("s3", "s4")):
        q.edge(a, b, "flow", None, sp="r", dp="l")
    q.box("idx", 40, 700, 1600, 90, "Indexes (a starting set)",
          ["{ order_id, seq }: read an order's trace   |   { correlation_id, seq }: read the adapter side   |   { external_ref }: find by aggregator or POS reference",
           "{ brand_id, captured_at desc }: support and clean-up by brand   |   { ttl_at } with expireAfterSeconds 0: each document expires at its own date"],
          kind="data", align="left", valign="top")

    # ================================================================ page 3 options
    r = d.page("3 Write options and the choice", 1700, 800)
    frame(r, "How the log gets written: four options, option A recommended",
          REF + " section 6",
          ["O-30 decides: if the log must be complete (legal or dispute), move from A to B",
           "Option C would break principle 8 unless masked, and topic rule 1 (one consumer in the same domain)",
           "Honest alternative (P-38): Postgres JSONB with partition drops is simpler at Tier S"])
    opts = [("A", "A. In-process queue, async writer", "Complete? No: gaps on crash or outage",
             "Lowest cost. No change to checkout. Recommended for v3.", "enginew", False),
            ("B", "B. Capture row in Postgres in the same transaction, a worker ships it to Mongo", "Complete? Yes for Order-side records",
             "More Postgres writes; raw payloads sit in Aurora for a while, so masking must happen before the insert; a new purge job. Candidate if O-30 needs completeness.", "neutral", True),
            ("C", "C. A Kafka topic carries payloads to a log writer", "Complete? Mostly",
             "Payloads on the bus, the 1 MB limit, a topic with one consumer in the same domain. Not recommended; listed as a candidate, not a topic.", "fail", True),
            ("D", "D. Write to Mongo synchronously in the request", "Complete? Yes",
             "Mongo latency and downtime hit checkout. Rejected.", "fail", True)]
    for i, (k, t, c, v, kind, dash) in enumerate(opts):
        x = 24 + i * 415
        r.box("o" + k, x, 120, 385, 290, t, ["", c, "", v], kind=kind, dashed=dash, align="left", valign="top", size=13)
    r.text("n1", 24, 450, 1650, 140, "<b>Rules for option A</b> (all options): capture is a non-blocking put; the writer is async; a log failure never fails an order and never rolls anything back; "
           "no new Kafka topic; metrics on queue depth, dropped, written and write latency, with an alert on a sustained drop rate.<br><br>"
           "<b>Cost of A:</b> the trace can have gaps. For debugging and support that is accepted. <b>Several writers:</b> one shared writer library and one insert-only Mongo role; only Cart &amp; Order reads (principle 3 compromise, O-30).",
           size=12, color="#475569")

    # ================================================================ page 4 masking
    s = d.page("4 Masking, retention and access", 1700, 900)
    frame(s, "Before a payload is stored: mask it, hash it, cap it, give it an end date",
          REF + " section 7 to 9; docs/architecture.md principle 8",
          ["O-07: retention under PDPA; O-30: right to delete cannot find one customer's payloads (they are masked)",
           "90 days, the 256 KB cap and the break-glass role are assumptions",
           "To confirm with DevOps: Atlas encryption at rest and keys through AWS KMS; region; private link"])
    steps = [("m1", "Raw payload", ["as received from the outside party"], "http"),
             ("m2", "Hash", ["payload_hash = sha256 of the unmasked", "payload: proves a match without storing it"], "enginew"),
             ("m3", "Mask by key name", ["phone, email, name, address, coordinates,", "token, authorization, signature, card number"], "enginew"),
             ("m4", "Tokenize", ["HMAC token, key in Vault scoped by brand_id;", "headers with secrets are dropped, not tokenized"], "enginew"),
             ("m5", "Cap the size", ["over 256 KB: truncated flag, hash and", "original size kept (assumption)"], "enginew"),
             ("m6", "Insert with ttl_at", ["assumption: 90 days, shorter if PDPA says so"], "data")]
    for i, (id_, t, dd, kind) in enumerate(steps):
        s.box(id_, 24 + i * 278, 130, 250, 120, t, dd, kind=kind, step=i + 1, dashed=(id_ == "m6"))
    for a, b in zip([x[0] for x in steps[:-1]], [x[0] for x in steps[1:]]):
        s.edge(a, b, "flow", None, sp="r", dp="l")
    s.box("ttl", 1136, 330, 250, 100, "Expired by MongoDB", ["background task about every 60 s;", "deletion is not immediate"], kind="data")
    s.edge("m6", "ttl", "log", "at ttl_at", sp="b", dp="t", via=[(1149, 290), (1261, 290)])
    s.box("acc", 24, 330, 520, 130, "Access", ["writer role: insert only (adapters, Order)", "read role: used only by Cart &amp; Order, through admin-bff", "break-glass human access with an audit trail (assumption)", "BFFs never read Mongo directly"], kind="enginew", align="left", valign="top")
    s.box("new", 580, 330, 520, 130, "A new vendor adapter before go-live", ["lists its sensitive paths for masking", "unknown keys are kept, so the list is a gate", "rules are per party and schema_version"], kind="enginew", dashed=True, align="left", valign="top")
    s.box("del", 24, 520, 520, 130, "Right to delete (a known limit)", ["A customer's payloads cannot be found by name: masked.", "Tokens are HMACs under a brand-level key, so one", "customer's tokens cannot be removed alone.", "Records leave by TTL expiry. Confirm in O-30."], kind="fail", align="left", valign="top")
    s.box("host", 580, 520, 520, 130, "Hosting (to confirm with DevOps, O-29)", ["likely MongoDB Atlas on AWS", "Atlas lists ap-southeast-7 (Thailand) as supported", "private connectivity from EKS", "backup: part of O-30"], kind="data", dashed=True, align="left", valign="top")
    s.box("enc", 1136, 520, 520, 130, "Encryption", ["in transit and at rest", "Queryable Encryption exists; kept in reserve for", "any field we must store recoverable"], kind="data", dashed=True, align="left", valign="top")
    return d
