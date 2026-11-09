"""14 - Catalog source of truth and sync in both directions (4 pages). Proposal, 2026-10-28."""
from drawio_lib import Diagram, frame

DATE = "2026-10-28"
DOC = "docs/design/catalog-sync-and-sot.md"


def fr(p, title, maps_to, qs):
    frame(p, title, maps_to, qs, date=DATE)


def build():
    d = Diagram("14-catalog-sync-and-source-of-truth.drawio", "Catalog source of truth and sync")
    c = [24, 364, 704, 1044, 1384]
    W = 260

    # ================================================================== page 1: two modes at a glance
    p = d.page("1 Two modes at a glance", 1700, 1000)
    fr(p, "Menu and catalog: the NEXA admin is the source, or the POS is, and both end in one structure",
       DOC + " sections 1 to 3; P-56, P-57, P-58",
       ["O-52: which brands and stores run in which mode, and who approves a switch?",
        "O-53: what each POS vendor can export, accept, and push is unknown. BSL: only the master feed and sold-out",
        "A proposal. Exactly one writer for each field group, per brand and store (P-56)"])
    p.lane("A", 24, 100, 1652, 200, "Mode service: the NEXA admin is the source of truth (outbound sync)", "engine")
    p.box("a1", c[0] + 20, 150, W, 120, "Brand admin edits", ["menu, price, content, schedule", "in the admin console (admin-bff)"], kind="http", parent="A", step=1)
    p.box("a2", c[1] + 20, 150, W, 120, "Catalog: draft, then publish", ["a published version, as today (D-08)", "the mapping check runs first"], kind="enginew", parent="A", step=2)
    p.box("a3", c[2] + 20, 150, W, 120, "Sync run per store", ["Catalog's own outbox worker.", "No Kafka topic is added (P-65)"], kind="enginew", parent="A", step=3, dashed=True)
    p.box("a4", c[3] + 20, 150, W, 120, "POS vendor menu", ["pushed by a vendor mapper.", "What it accepts: to confirm (O-53)"], kind="http", parent="A", dashed=True, step=4)
    p.box("a5", c[4] + 20, 150, 250, 120, "Channels", ["own apps and aggregators read", "the published version"], kind="http", parent="A")
    p.edge("a1", "a2", "http", None, sp="r", dp="l")
    p.edge("a2", "a3", "plain", None, sp="r", dp="l")
    p.edge("a3", "a4", "http", None, sp="r", dp="l")
    p.edge("a4", "a5", "plain", None, sp="r", dp="l", dashed=True)
    p.lane("B", 24, 330, 1652, 200, "Mode pos: the POS is the source of truth (inbound sync)", "http")
    p.box("b1", c[0] + 20, 380, W, 120, "POS vendor menu", ["the source. Items, modifiers,", "combos, prices, availability"], kind="http", parent="B", dashed=True, step=1)
    p.box("b2", c[1] + 20, 380, W, 120, "Import", ["a webhook, a poll or a file.", "Raw payload kept in S3"], kind="enginew", parent="B", step=2, dashed=True)
    p.box("b3", c[2] + 20, 380, W, 120, "Stage, diff, guard", ["mapped to the canonical menu.", "Nothing goes live from here"], kind="enginew", parent="B", step=3, dashed=True)
    p.box("b4", c[3] + 20, 380, W, 120, "Catalog draft, then publish", ["review (default) or auto inside", "guard limits. The normal publish"], kind="enginew", parent="B", step=4)
    p.box("b5", c[4] + 20, 380, 250, 120, "Channels", ["same as above: they never see", "which side was the source"], kind="http", parent="B")
    for a, b in (("b1", "b2"), ("b2", "b3"), ("b3", "b4"), ("b4", "b5")):
        p.edge(a, b, "plain", None, sp="r", dp="l")
    p.box("m1", 44, 570, 520, 120, "The setting: catalog_sync_mode", ["per brand, with an optional store override.", "service, pos, or mixed with one owner per field group.", "A switch needs a dry run and an audit row"], kind="enginew", dashed=True)
    p.box("m2", 604, 570, 520, 120, "The canonical menu", ["menu, category, item, modifier group and option,", "combo, price, availability, content, schedule.", "One structure, whichever side wrote it (P-57)"], kind="enginew")
    p.box("m3", 1164, 570, 480, 120, "The id mapping: pos_item_map", ["NEXA SKU id to the vendor's item reference,", "per brand, vendor and store. Anything that", "cannot be mapped is reported, never dropped"], kind="data", dashed=True)
    p.text("n1", 24, 720, 1652, 44, "<b>Not in this picture:</b> a new service, a new Kafka topic, or a second place that writes the live menu. A POS price change waits for a publish (D-08). The POS-owned sold-out flag is never auto-restored by NEXA.",
           size=12, color="#475569")

    # ================================================================== page 2: outbound path
    q = d.page("2 Outbound path: service is the source", 1700, 1000)
    fr(q, "Outbound: publish once, push to every store's POS, confirm per store, and never show a menu the POS does not have",
       DOC + " section 5; P-57, P-58, D-08",
       ["O-53: can each vendor take a menu from us? Until it answers, nothing is pushed to it",
        "O-54: where vendor connection data and secrets live (Catalog's row or a Vault reference)",
        "A new item stays hidden at a store until that store's sync is confirmed (P-58)"])
    q.box("a1", c[0], 125, W, 110, "Admin edits the draft", ["admin-bff, grant catalog.menu.edit", "one writer per field group"], kind="http", step=1)
    q.box("a2", c[1], 125, W, 110, "Catalog: PublishMenu", ["mapping check: every item has a", "vendor ref for each POS store"], kind="enginew", step=2)
    q.box("a3", c[2], 125, W, 110, "One commit", ["new menu version + sync_run rows", "+ outbox row, one transaction"], kind="enginew", step=3)
    q.box("a4", c[3], 125, W, 110, "catalog.menu.published", ["thin fact: version, effective_at", "apps and channels read it"], kind="fact")
    q.edge("a1", "a2", "http", None, sp="r", dp="l")
    q.edge("a2", "a3", "plain", None, sp="r", dp="l")
    q.edge("a3", "a4", "fact", "publish", sp="r", dp="l")
    q.box("b1", c[2], 285, W, 110, "Sync worker", ["reads the outbox, one run per", "store, in order, with rate limits"], kind="enginew", step=4, dashed=True)
    q.box("b2", c[1], 285, W, 110, "PosMenuGateway", ["PushMenu(version). Idempotent by", "version. The vendor mapper converts"], kind="enginew", step=5, dashed=True)
    q.box("b3", c[0], 285, W, 110, "POS vendor", ["takes or refuses the menu.", "Capability flags: all unknown (O-53)"], kind="http", dashed=True)
    q.edge("a3", "b1", "plain", "outbox", sp="b", dp="t")
    q.edge("b1", "b2", "plain", None, sp="l", dp="r")
    q.edge("b2", "b3", "http", "push", sp="l", dp="r")
    q.box("c1", c[0], 445, W, 110, "Result per item", ["sync_run_item: ok, failed, or", "unmapped, with a reason"], kind="enginew", step=6)
    q.box("c2", c[1], 445, W, 110, "Store confirmed", ["the new items become visible", "at that store (P-58)"], kind="enginew", step=7)
    q.box("c3", c[2], 445, W, 110, "Retry, then alert", ["retry for the sync window.", "Then an alert and the admin sees it"], kind="fail")
    q.edge("b3", "c1", "http", "answer", sp="b", dp="t")
    q.edge("c1", "c2", "plain", "ok", sp="r", dp="l")
    q.edge("c1", "c3", "fail", None, sp=("b", 0.5), dp=("b", 0.5), via=[(c[0] + 130, 580), (c[2] + 130, 580)], lab=0.5)
    q.lane("D", 24, 640, 1652, 150, "Every night, and never destructive", "neutral")
    q.box("d1", 44, 690, 500, 80, "Drift check", ["ReadMenu where the vendor allows it, compared with", "the published version. It reports and never overwrites"], kind="enginew", parent="D", dashed=True)
    q.box("d2", 584, 690, 500, 80, "Availability, both ways", ["a sold-out flag from the POS is never auto-restored", "by NEXA. A NEXA sold-out is pushed to the POS"], kind="enginew", parent="D", dashed=True)
    q.box("d3", 1124, 690, 520, 80, "A change of mode", ["dry run first, a diff to review, an audit row.", "Never a silent switch (P-56)"], kind="enginew", parent="D", dashed=True)

    # ================================================================== page 3: inbound path
    s = d.page("3 Inbound path: the POS is the source", 1700, 1160)
    fr(s, "Inbound: keep the raw payload, map it, stage it, diff it, and publish only through the normal publish",
       DOC + " section 6; P-57, P-58, D-08",
       ["O-55: review or auto-publish, the guard limits, and how fast a POS price may reach shoppers",
        "O-54: raw vendor payloads go to S3 with a Postgres pointer. MongoDB would need P-38 amended",
        "An unmapped or invalid row is reported and not published. A delete retires an item, never history"])
    s.box("a1", c[0], 125, W, 110, "A change in the POS menu", ["a menu change, a new item,", "a price or a sold-out change"], kind="http", step=1, dashed=True)
    s.box("a2", c[1], 125, W, 110, "partner-adapter", ["checks the vendor signature.", "Only for a vendor with a webhook"], kind="enginew", step=2, dashed=True)
    s.box("a3", c[2], 125, W, 110, "catalog.requested", ["command {pos_menu_changed}", "thin: vendor, store, S3 key"], kind="cmd", dashed=True)
    s.box("a4", c[3], 125, W, 110, "Catalog scheduler", ["polls a vendor with no webhook", "or reads a file. No record needed"], kind="enginew", dashed=True)
    s.edge("a1", "a2", "http", "webhook", sp="r", dp="l")
    s.edge("a2", "a3", "cmd", "publish", sp="r", dp="l")
    s.box("b1", c[2], 285, W, 110, "Catalog import worker", ["consumes the command, or the", "scheduler. Reads the vendor menu"], kind="enginew", step=3)
    s.box("b2", c[1], 285, W, 110, "Keep the raw payload", ["S3, with a pointer in Postgres.", "Masked. Expires by policy"], kind="data", step=4)
    s.box("b3", c[0], 285, W, 110, "Map to the canonical menu", ["PosMenuGateway.ReadMenu and the", "vendor mapper, then pos_item_map"], kind="enginew", step=5, dashed=True)
    s.edge("a3", "b1", "cmd", "consume", sp="b", dp="t")
    s.edge("a4", "b1", "plain", "scheduled", sp="b", dp=("t", 0.85), via=[(c[3] + 130, 260), (c[2] + 221, 260)], lab=0.5)
    s.edge("b1", "b2", "plain", None, sp="l", dp="r")
    s.edge("b2", "b3", "plain", None, sp="l", dp="r")
    s.box("c1", c[0], 445, W, 110, "Stage and diff", ["compare with the published menu:", "added, changed, retired items"], kind="enginew", step=6)
    s.box("c2", c[1], 445, W, 110, "Guard limits", ["share of items changed or deleted,", "price jumps, empty menu: stop"], kind="enginew", step=7, dashed=True)
    s.box("c3", c[2], 445, W, 110, "Review or auto", ["review (default): staff approve.", "auto: only inside the guard limits"], kind="enginew", step=8, dashed=True)
    s.edge("b3", "c1", "plain", None, sp="b", dp="t")
    s.edge("c1", "c2", "plain", None, sp="r", dp="l")
    s.edge("c2", "c3", "plain", "pass", sp="r", dp="l")
    s.box("d1", c[3], 445, W, 110, "Report, do not publish", ["unmapped, invalid, or over the", "guard. Shown in the admin console"], kind="fail")
    s.edge("c2", "d1", "fail", None, sp=("t", 0.5), dp=("t", 0.5), via=[(c[1] + 130, 420), (c[3] + 130, 420)], lab=0.5)
    s.box("e1", c[2], 605, W, 110, "Catalog draft", ["written by the import, as a", "second way in beside the admin"], kind="enginew", step=9)
    s.box("e2", c[3], 605, W, 110, "The normal publish", ["a new menu version (D-08). A POS", "price waits for it. No live write"], kind="enginew", step=10)
    s.box("e3", c[4], 605, W, 110, "catalog.menu.published", ["thin fact. Apps, aggregators and", "the cart read the new version"], kind="fact")
    s.edge("c3", "e1", "plain", "approved", sp="b", dp="t")
    s.edge("e1", "e2", "plain", None, sp="r", dp="l")
    s.edge("e2", "e3", "fact", "publish", sp="r", dp="l")
    s.lane("F", 24, 770, 1652, 150, "Rules that do not bend", "neutral")
    s.box("f1", 44, 820, 380, 80, "A delete from the POS", ["retires the item. History and old", "menu versions stay"], kind="enginew", parent="F")
    s.box("f2", 464, 820, 380, 80, "A sold-out flag from the POS", ["goes through the existing sold-out path.", "NEXA never restores it by itself"], kind="enginew", parent="F")
    s.box("f3", 884, 820, 380, 80, "A first import", ["always reviewed, whatever the", "setting. It is the baseline"], kind="enginew", parent="F", dashed=True)
    s.box("f4", 1304, 820, 340, 80, "A failed run", ["leaves the live menu as it was", "and raises an alert"], kind="fail", parent="F")

    # ================================================================== page 4: config, mapping, edge cases
    t = d.page("4 Per-brand setup, mapping tables and edge cases", 1700, 1060)
    fr(t, "What is stored, per brand and per store, and what happens when a mapping or a mode goes wrong",
       DOC + " sections 3, 4, 9, 11; P-56, P-57, P-58",
       ["O-52: which field groups the POS owns when a brand mixes the two modes",
        "O-53, O-28: vendor menu limits, ids, modifiers and combos, and rate limits",
        "O-54: connection data and secrets for the menu port"])
    t.lane("L1", 24, 100, 820, 440, "Stored in Catalog (Postgres). Names are proposals", "data")
    tb = [("sync_setting", ["brand, store override, mode,", "field owner per group, version"]),
          ("pos_item_map", ["brand, vendor, store scope,", "NEXA SKU id, vendor item ref"]),
          ("sync_run", ["store, menu version, status,", "counts, S3 key, times"]),
          ("sync_run_item", ["run, entity, result,", "reason (ok, failed, unmapped)"]),
          ("menu_import", ["store, external version or hash,", "status, S3 key, diff, guard result"]),
          ("pos_menu_connection", ["vendor, a Vault reference,", "routing values (O-54)"])]
    for i, (n, dd) in enumerate(tb):
        t.box("t%d" % i, 44 + (i % 2) * 400, 150 + (i // 2) * 120, 380, 100, n, dd, kind="data", parent="L1", dashed=True)
    t.text("tn", 44, 500, 780, 30, "Raw vendor payloads are in S3, with a pointer here. Credentials stay in Vault.", size=11, color="#475569", parent="L1")
    t.lane("L2", 864, 100, 812, 440, "One writer for each field group (the two presets)", "engine")
    hd = ["structure, content", "price", "availability", "schedule"]
    t.box("g0", 884, 150, 380, 70, "Field group", ["mode service: owner / mode pos: owner"], kind="note", parent="L2")
    rows = [("Structure and content", "NEXA admin / POS"), ("Price", "NEXA admin / POS"), ("Availability (sold out)", "both ways, POS flag wins / POS"), ("Schedule (dayparts)", "NEXA admin / POS")]
    for i, (a, b) in enumerate(rows):
        t.box("g%d" % (i + 1), 884, 235 + i * 70, 380, 60, a, [b], kind="enginew", parent="L2", dashed=True)
    t.box("gn", 1284, 150, 372, 360, "Mixed mode is an advanced option", ["For example prices from the POS and content", "from NEXA. It doubles the rules to test.", "", "A write to a field the other side owns is", "rejected, so there is never a tug of war.", "", "The preset names are only shortcuts for", "the owner of each group (P-56)."], kind="note", parent="L2", align="left", valign="top")
    t.lane("L3", 24, 570, 1652, 330, "What happens when something goes wrong", "fail")
    cases = [("Item missing in the vendor menu", ["Outbound: the item is unmapped and not", "pushed. The admin console lists it."]),
             ("A combo does not map one to one", ["Reported as unmapped. Never flattened", "into a wrong item. Staff map it by hand."]),
             ("POS price differs at checkout", ["The cart uses the published price (D-08).", "The POS total differs: O-32 decides."]),
             ("A new item before its store syncs", ["Hidden at that store until the sync is", "confirmed, so no order the POS cannot take."]),
             ("A mode switch with a different menu", ["Dry run and a diff to review first.", "An audit row. Never applied silently."]),
             ("Vendor rate limit or outage", ["The worker retries inside the window, then", "alerts. The live menu is not changed."])]
    for i, (a, b) in enumerate(cases):
        t.box("c%d" % i, 44 + (i % 3) * 540, 620 + (i // 3) * 130, 500, 110, a, b, kind="fail", parent="L3", align="left", valign="top", size=13)
    return d
