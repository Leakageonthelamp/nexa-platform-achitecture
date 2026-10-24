"""12 - Deployment and infrastructure (3 pages)."""
from drawio_lib import Diagram, frame

REF = "docs/design/tech-stack.md section 1; docs/architecture.md section 6 and 9; docs/design/scale-assumptions.md"
QS = ["O-29: MongoDB Atlas hosting: region, private connectivity, backup, keys, owner (DevOps)",
      "O-36: who creates Kafka topics and Schema Registry subjects (DevOps or the domain teams)",
      "O-01, O-02, O-03: the real load, latency and recovery targets; the numbers on page 3 are assumptions (P-43)"]


def build():
    d = Diagram("12-deployment-and-infra.drawio", "Deployment and infrastructure")

    # ------------------------------------------------------------ page 1
    p = d.page("1 Where everything runs", 1700, 1060)
    frame(p, "Where NEXA runs: Cloudflare in front, EKS in the middle, managed data and vendors around it", REF, QS)
    p.box("ext", 24, 150, 190, 330, "Outside", ["shoppers and the brand apps", "admin console and CSC", "partners and aggregators", "POS vendors", "payment gateway, SES, SMS, LINE"], kind="http", size=11)
    p.box("cf", 254, 255, 170, 120, "Cloudflare", ["CDN, WAF, TLS", "run by DevOps"], kind="http")
    p.lane("aws", 470, 100, 780, 770, "AWS (run by DevOps)", "neutral")
    p.lane("eks", 490, 140, 740, 330, "EKS: every mode is its own workload from one image", "engine", parent="aws")
    p.box("kong", 510, 260, 110, 110, "Kong", ["the only policy", "point"], kind="http", parent="eks")
    p.box("edge", 670, 190, 240, 250, "Edge apps (Bun, Elysia v2 RC)", ["customer-bff, guest-bff,", "admin-bff, partner-bff", "partner-adapter, webhook-adapter", "REST only (P-41, O-34)"], kind="enginew", parent="eks")
    p.box("core", 960, 190, 250, 250, "Domain apps (Go)", ["11 domains, hexagonal", "modes: api, consumer,", "worker, cron", "gRPC behind the BFFs"], kind="enginew", parent="eks")
    p.lane("data", 490, 520, 740, 170, "Data and secrets", "data", parent="aws")
    p.box("aur", 510, 570, 160, 100, "Aurora PostgreSQL", ["schema and role per domain", "system of record (P-08)"], kind="data", parent="data", size=11)
    p.box("val", 690, 570, 160, 100, "ElastiCache Valkey", ["4 uses only (D-04)", "never the truth"], kind="data", parent="data", size=11)
    p.box("s3", 870, 570, 160, 100, "S3", ["images, imports, audiences,", "invoices, data lake"], kind="data", parent="data", size=11)
    p.box("vault", 1050, 570, 160, 100, "Vault", ["signing keys and", "provider secrets"], kind="data", parent="data", size=11)
    p.box("obs", 490, 730, 740, 110, "CloudWatch and OpenTelemetry", ["logs, metrics, traces; traceparent travels in gRPC metadata and Kafka headers", "Lambda only for headless scheduled glue with no domain state"], kind="enginew", parent="aws")
    p.lane("ven", 1320, 100, 356, 770, "Vendor services", "neutral")
    p.box("conf", 1340, 190, 316, 100, "Confluent Cloud", ["Kafka: 12 topics (P-42)", "Schema Registry, Protobuf, BACKWARD"], kind="fact", parent="ven")
    p.box("atlas", 1340, 302, 316, 100, "MongoDB Atlas on AWS", ["order payload log only (P-38)", "to confirm with DevOps (O-29)"], kind="data", parent="ven", dashed=True)
    p.box("prov", 1340, 520, 316, 190, "Providers the apps call", ["Omise, TrueMoney", "FCM, SES, SMS, LINE", "ZEEK, Grab Express, Google Maps", "POS vendors (BSL first)"], kind="http", parent="ven", size=11)
    p.edge("ext", "cf", "http", None, sp="r", dp="l")
    p.edge("cf", "kong", "http", None, sp="r", dp="l")
    p.edge("kong", "edge", "http", None, sp="r", dp="l")
    p.edge("edge", "core", "grpc", "gRPC", sp="r", dp="l")
    p.edge("core", "data", "data", "SQL, cache, files, keys", sp="b", dp=("t", (1085 - 490) / 740.0))
    p.edge("core", "conf", "cmd", "Kafka", sp=("r", 0.2), dp="l")
    p.edge("core", "atlas", "log", "log, best effort", sp=("r", 0.648), dp="l")
    p.text("n1", 24, 520, 420, 190, "Core infrastructure is fixed by DevOps and DevOps builds it. A new tool needs a decision row with a reason, a cost and a named DevOps owner; it may be non-AWS when clearly better.",
           size=12, color="#475569")
    p.text("n2", 24, 730, 420, 110, "To confirm with DevOps: how topics are created, the Atlas project with private connectivity and an insert-only role.", size=12, color="#475569")

    # ------------------------------------------------------------ page 2
    q = d.page("2 One domain app, four run modes", 1700, 1060)
    frame(q, "One image per domain, four modes, each its own Kubernetes workload", REF.replace("section 1", "section 3") + " (hexagonal)", QS)
    modes = [("api", "api", ["gRPC server (adapters/in/grpc)", "serves grpc.health.v1", "shopper and admin calls"], "grpc"),
             ("cons", "consumer", ["Kafka consumer (adapters/in/kafka)", "dedupe, apply, Ack", "3 retries, then the service dlq"], "cmd"),
             ("work", "worker", ["outbox relay and background loops", "one active relay per domain", "(advisory lock, P-05)"], "enginew"),
             ("cron", "cron", ["Kubernetes CronJob (adapters/in/cron)", "Forbid, Asia/Bangkok, safe to run twice", "sweepers and nightly jobs (P-07)"], "enginew")]
    for i, (id_, t, dd, k) in enumerate(modes):
        q.box(id_, 24 + i * 420, 130, 380, 130, "mode: " + t, dd, kind=k, size=12)
    q.lane("hex", 24, 340, 1650, 260, "The core: use cases and ports know no gRPC, Kafka, Postgres or vendor", "engine")
    q.box("uc", 60, 390, 420, 170, "Domain and use cases", ["the rules of this domain", "the only writer of its own state", "transaction: state change + outbox row"], kind="enginew", parent="hex")
    q.box("ports", 600, 390, 420, 170, "Ports", ["repository, event publisher, clock,", "and a port per outside system", "(PosGateway, FleetProvider, a legacy port)"], kind="enginew", parent="hex")
    q.box("adp", 1140, 390, 500, 170, "Out adapters", ["adapters/out: Postgres, Kafka outbox, vendor adapters,", "legacy adapters (adapters/out/legacy/system),", "S3, Valkey"], kind="enginew", parent="hex")
    for id_ in ("api", "cons", "work", "cron"):
        q.edge(id_, "hex", "plain", None, sp="b", dp=("t", (q.nodes[id_].x + q.nodes[id_].w / 2 - 24) / 1650.0))
    q.edge("uc", "ports", "plain", None, sp="r", dp="l")
    q.edge("ports", "adp", "plain", None, sp="r", dp="l")
    q.box("hl", 24, 660, 800, 110, "Health", ["every mode serves HTTP /healthz (liveness) and /readyz", "readiness checks Postgres and, for consumer and worker, Kafka"], kind="enginew", align="left", valign="top")
    q.box("mg", 880, 660, 794, 110, "Migrations", ["live with the domain app, run as a pre-deploy job", "expand, then contract: the previous release keeps working"], kind="enginew", align="left", valign="top")
    q.text("n1", 24, 790, 1650, 60, "The layout is proposed. Align with the owner's boilerplate repos when they are shared. Statement is a mode of the Payment app, and Brand and Store are one app.", size=12, color="#475569")

    # ------------------------------------------------------------ page 3
    r = d.page("3 Scale assumptions by tier", 1700, 860)
    frame(r, "How big it might get: three tiers, all assumptions until the business answers",
          "docs/design/scale-assumptions.md sections 2 to 6; docs/architecture.md P-43", QS)
    tiers = [("S", "Tier S: a pilot, one or two brands live", ["peak 200 orders per minute (total)", "busiest brand 80 orders per minute", "5 orders per second with burst", "200 edge requests per second", "85 Kafka records per second", "125 Postgres write transactions per second",
                                                                 "", "shopper path 99.5% available (assumption)", "recovery: RPO 5 minutes, RTO 60 minutes", "shape: multi-AZ only"]),
             ("M", "Tier M: several brands live", ["peak 1,000 orders per minute (total)", "busiest brand 400 orders per minute", "25 orders per second with burst", "1,000 edge requests per second", "425 Kafka records per second", "625 Postgres write transactions per second",
                                                    "", "shopper path 99.9% available (assumption)", "recovery: RPO 1 minute, RTO 30 minutes", "shape: multi-AZ, tested restore"]),
             ("L", "Tier L: most brands live, at the lunch peak", ["peak 5,000 orders per minute (total)", "busiest brand 2,000 orders per minute", "125 orders per second with burst", "5,000 edge requests per second", "2,125 Kafka records per second", "3,125 Postgres write transactions per second",
                                                                    "", "shopper path 99.95% available (assumption)", "recovery: RPO 1 minute, RTO 15 minutes", "shape: multi-AZ plus a second region (to confirm cost)"])]
    for i, (k, t, dd) in enumerate(tiers):
        r.box("t" + k, 24 + i * 556, 120, 530, 330, t, dd, kind="enginew", dashed=True, align="left", valign="top", size=13)
    r.text("n1", 24, 490, 1650, 130, "All numbers are recommended shapes with example values, not business facts (P-43). They let the design size partitions, Aurora and replicas. "
           "Partitions: 6 by default, 12 for order.* and payment.* (the registry also gives delivery.* 12). The admin console is 99.5% in every tier. The payload log is best effort with no recovery target. "
           "At Tier L the risk is the hot brand, the lunch peak, per-key ordering and the sync chain on PlaceOrder, not raw volume (to verify with DevOps and a load test).", size=12, color="#475569")
    return d
