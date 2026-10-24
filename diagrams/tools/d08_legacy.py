"""08 - Legacy bridge (3 pages)."""
from drawio_lib import Diagram, frame

REF = "docs/design/legacy-bridge.md; docs/architecture.md P-39"
QS = ["O-31: which capabilities run on legacy, per brand, in what order, and the rollback rule for each",
      "O-18: the cutover from Fleet Management, FAAS and Driver Management (already open)",
      "Build a legacy adapter only for a capability with a named brand and a date; delete it at done"]


def build():
    d = Diagram("08-legacy-bridge.drawio", "Legacy bridge")

    # ------------------------------------------------------------ page 1
    p = d.page("1 Same port, different adapter", 1760, 1000)
    frame(p, "A legacy system sits behind the same port, so legacy shapes never leak in", REF + " section 1 to 4", QS)
    p.box("bff", 24, 280, 160, 90, "BFF or consumer", ["a caller"], kind="enginew")
    p.lane("dom", 214, 100, 1190, 520, "One domain (Go, hexagonal): the rules and gRPC contract do not change", "engine")
    p.box("api", 234, 280, 170, 90, "Domain api", ["gRPC contract"], kind="enginew", parent="dom")
    p.box("uc", 444, 280, 160, 90, "Use case", ["the domain rules"], kind="enginew", parent="dom")
    p.box("port", 644, 280, 190, 90, "Port", ["example: Dispatcher"], kind="enginew", parent="dom")
    p.box("route", 864, 255, 220, 140, "Capability route", [], kind="grpc", parent="dom", shape="diamond", dashed=True)
    p.box("nat", 1124, 150, 260, 90, "Native adapter", ["adapters/out/native"], kind="enginew", parent="dom")
    p.box("sha", 1124, 290, 260, 110, "Shadow", ["call both, return the legacy answer,", "record the difference"], kind="enginew", parent="dom", dashed=True)
    p.box("leg", 1124, 450, 260, 110, "Legacy adapter (the ACL)", ["adapters/out/legacy/system", "translates to and from our model"], kind="enginew", parent="dom", dashed=True)
    p.box("db", 1470, 150, 250, 90, "Domain schema (Aurora)", ["the new system of record"], kind="data")
    p.box("old", 1470, 450, 250, 110, "Legacy system", ["Fleet Management, FAAS, SDM order flow, a", "brand's account system (to confirm)"], kind="neutral", dashed=True)
    p.edge("bff", "api", "grpc", None, sp="r", dp="l")
    p.edge("api", "uc", "grpc", None, sp="r", dp="l")
    p.edge("uc", "port", "grpc", None, sp="r", dp="l")
    p.edge("port", "route", "grpc", None, sp="r", dp="l")
    p.fan("route", ["nat", "sha", "leg"], "grpc", side="r", trunk=1104)
    p.edge("nat", "db", "data", None, sp="r", dp="l")
    p.edge("leg", "old", "http", None, sp="r", dp="l")
    p.text("n1", 214, 640, 1190, 60, "The route is a small table owned by the domain: (brand_id, capability) to a mode. "
           "<b>One source of truth at a time</b>: shadow writes native only to a scratch area no reader uses. Two live writers are never allowed.", size=12, color="#475569")
    p.box("acl", 24, 740, 1696, 90, "ACL rules (inside the legacy adapter)",
          ["No legacy field name, status code or id format in the domain or its protos  |  legacy id kept beside ours in a legacy_ref table  |  legacy errors mapped to gRPC codes, a timeout is UNAVAILABLE",
           "money to integer satang, times to UTC  |  no other domain reads a legacy database or calls a legacy API  |  no personal data on the bus"],
          kind="note", align="left", valign="top", size=12)
    p.nodes["acl"].dashed = False

    # ------------------------------------------------------------ page 2
    q = d.page("2 Moving one capability for one brand", 1760, 880)
    frame(q, "The strangler: one capability, one brand, one step at a time", REF + " section 3 and 7", QS)
    st = [("sl", "legacy", ["every call goes to legacy", "source of truth: legacy"], "neutral"),
          ("ss", "shadow", ["call legacy and native, return legacy", "differences are recorded", "source of truth: legacy"], "enginew"),
          ("sc", "canary", ["listed stores use native, the rest legacy", "(by store, not by percentage: assumption)", "source of truth: native for listed stores"], "enginew"),
          ("sn", "native", ["every call goes to native", "the legacy adapter is idle", "source of truth: native"], "enginew"),
          ("sd", "done", ["legacy adapter deleted"], "data")]
    for i, (id_, t, dd, k) in enumerate(st):
        q.box(id_, 24 + i * 352, 130, 240, 150, t, dd, kind=k, dashed=(id_ in ("ss", "sc")))
    fw = [("sl", "ss", "mappings checked"), ("ss", "sc", "diffs explained"), ("sc", "sn", "all stores pass"), ("sn", "sd", "idle 30 days")]
    for a, b, lbl in fw:
        q.edge(a, b, "grpc", lbl, sp="r", dp="l")
    q.edge("sc", "ss", "fail", "problem found", sp=("b", 0.6), dp=("b", 0.3), via=[(24 + 2 * 352 + 168, 330), (24 + 352 + 72, 330)])
    q.edge("sn", "sc", "fail", "rollback", sp=("b", 0.6), dp=("b", 0.9), via=[(24 + 3 * 352 + 144, 380), (24 + 2 * 352 + 216, 380)])
    q.box("tbl", 24, 430, 820, 150, "The capability route table (owned by the domain that has the legacy adapter)",
          ["brand_id, capability: what is routed", "mode: legacy, shadow, canary or native", "canary: a list of stores (assumption: by store, so one store behaves the same all day)",
           "version and audit: same rules as other brand configuration"], kind="data", align="left", valign="top", size=13)
    q.box("chk", 880, 430, 840, 150, "Check before moving on",
          ["legacy to shadow: the legacy adapter passes the same contract tests as the native one (assumption: one suite per port)",
           "shadow to canary: the recorded differences are explained, the owner accepts the rest",
           "canary to native: every store ran on native through a full trading day, including a peak",
           "native to done: no calls to legacy for the agreed period (assumption: 30 days)"], kind="enginew", align="left", valign="top", size=13)
    q.box("rb", 24, 620, 1696, 100, "Rollback has a cost: decide it before the canary step (O-31)",
          ["Going back is safe only while data written by native can still be read by legacy, or while no native-only data exists.",
           "Otherwise rollback means a reverse sync or a freeze window. Each capability must say which one it is."], kind="fail", align="left", valign="top", size=13)

    # ------------------------------------------------------------ page 3
    r = d.page("3 Facts, old clients and where legacy is likely", 1760, 1040)
    frame(r, "Legacy changes become normal facts, and old clients keep working", REF + " section 5, 6 and 8", QS)
    r.text("h1", 24, 84, 1600, 24, "<b>Facts that legacy does not publish</b>: a bridge worker publishes them through the normal outbox, on the existing topics (no new topic)", size=13, color="#0F172A")
    r.box("l1", 24, 130, 240, 130, "Legacy system", ["does not write to our outbox or Kafka"], kind="neutral", dashed=True)
    r.box("det", 330, 130, 330, 130, "How a change is found", ["a webhook, through partner-adapter", "polling an API or a table (simplest; interval is an assumption)", "CDC: needs a new-tool request to DevOps (to confirm)"], kind="enginew", dashed=True, align="left", valign="top", size=12)
    r.box("bw", 730, 130, 280, 130, "Bridge worker", ["domain run mode worker"], kind="enginew", dashed=True)
    r.box("ob", 1070, 130, 240, 130, "Outbox", ["one transaction, as always"], kind="enginew")
    r.box("tp", 1380, 130, 340, 130, "Existing topic", ["example: a legacy delivery status becomes", "provider_update on delivery.requested (P-18)"], kind="cmd")
    for a, b in (("l1", "det"), ("det", "bw"), ("bw", "ob"), ("ob", "tp")):
        r.edge(a, b, "plain" if a != "ob" else "cmd", "detected" if a == "l1" else None, sp="r", dp="l")
    r.text("h2", 24, 310, 1600, 24, "<b>Old clients</b>: some brand apps or partners call old APIs; a compat route keeps them working, with an end date", size=13, color="#0F172A")
    r.box("oc", 24, 350, 240, 100, "Old brand app or partner", ["calls an old path"], kind="http")
    r.box("kg", 330, 350, 240, 100, "Kong", ["routes the old paths to a", "compat/brand route group"], kind="http")
    r.box("cr", 640, 350, 400, 100, "compat route in the existing BFF", ["no new app (D-03: four BFFs, two adapters)", "translates the old request in the mapper layer"], kind="enginew", dashed=True)
    r.box("cg", 1110, 350, 280, 100, "Current gRPC call", ["the same call as a new client"], kind="grpc")
    r.box("ed", 1460, 350, 260, 100, "End date", ["listed in the brand's onboarding", "record; removed on migration"], kind="note")
    for a, b in (("oc", "kg"), ("kg", "cr"), ("cr", "cg")):
        r.edge(a, b, "http" if a != "cr" else "grpc", None, sp="r", dp="l")
    r.text("h3", 24, 500, 1600, 24, "<b>Where legacy is likely</b> (only what the docs and the owner said; everything else is to confirm)", size=13, color="#0F172A")
    rows = [("Delivery &amp; Dispatch", "Fleet Management, FAAS, Driver Management. O-18: cutover plan not written; per brand is possible"),
            ("Cart &amp; Order", "the SDM order flow, with the move to BSL for mfg-tpc-api. The BSL adapter is the native side. To confirm the legacy API and owner"),
            ("Identity &amp; Profile", "each brand's own account system. A Minor ID merges accounts: needs legacy_ref and a matching rule"),
            ("Loyalty &amp; MemberCard", "the existing loyalty platform. To confirm what exists today"),
            ("Catalog &amp; Menu", "the POS master feed. Already a worker (D-08), not a legacy system in this sense"),
            ("Payment, Wallet, Voucher, Notification, Admin, Brand &amp; Store", "unknown. To confirm; not assumed")]
    for i, (a, b) in enumerate(rows):
        y = 540 + i * 60
        r.box("g%d" % i, 24, y, 460, 48, a, [], kind="enginew", size=12)
        r.box("w%d" % i, 500, y, 1220, 48, "", [b], kind="note", shape="rect", align="left", size=12)
    return d
