"""02 - brand onboarding and configuration (3 pages)."""
from drawio_lib import Diagram, frame


def build():
    d = Diagram("02-brand-onboarding-and-config.drawio", "Brand onboarding and configuration")

    # ------------------------------------------------------------------ page 1: the 13 steps
    p = d.page("1 Onboarding steps", 1720, 900)
    frame(p, "Onboarding a new brand: 13 steps, mostly configuration",
          "docs/design/brand-configuration.md section 4; docs/architecture.md P-37",
          ["P-37: a new brand needs code only for a new kind of outside system",
           "O-27: who owns brand configuration and approves risky changes?",
           "O-28: real POS capability matrix per vendor still unknown",
           "O-31: which capabilities still run on legacy, per brand"])
    states = [("s.draft", "draft"), ("s.conf", "configured"), ("s.ready", "ready"), ("s.test", "testing"),
              ("s.live", "live"), ("s.hidden", "hidden")]
    for i, (id_, t) in enumerate(states):
        p.box(id_, 24 + i * 240, 90, 130, 44, t, kind="grpc" if t == "live" else "neutral")
    labels = ["all slices written", "readiness passes", "test orders", "owner approves", "flag off"]
    for i in range(5):
        p.edge(states[i][0], states[i + 1][0], "plain" if i < 3 else "flow", labels[i], sp="r", dp="l", lab=0.5)
    p.edge("s.hidden", "s.live", "flow", "back to live", sp="b", dp="b",
           via=[(24 + 5 * 240 + 65, 164), (24 + 4 * 240 + 65, 164)], lab=0.5)
    steps = [
        ("Create the brand: brand_id, name, owned or franchised, live flag off", "Brand &amp; Store", "no"),
        ("Create stores: address, hours, zone, group", "Brand &amp; Store", "no"),
        ("Choose the POS vendor, write a pos_connection per store (credentials stay in Vault)", "Cart &amp; Order", "yes, only if the vendor has no adapter yet"),
        ("Load the menu through the master feed or a file, then publish", "Catalog", "no"),
        ("Set up the payment account and keys", "Payment &amp; Billing", "yes, only for a new provider"),
        ("Turn on aggregators per store, with their mapping", "Cart &amp; Order", "yes, only for a new aggregator"),
        ("Set the delivery provider list per store, or leave delivery off", "Delivery &amp; Dispatch", "no"),
        ("Set notification channels and templates", "Notification", "no"),
        ("Set loyalty rules, wallet limits, first campaigns", "Loyalty, Wallet, Voucher &amp; Campaign", "no"),
        ("Enable the brand for Minor ID and set the consent wording", "Identity &amp; Profile", "no"),
        ("Run the readiness check (one read-only question to each owner)", "admin-bff reads each owner", "no"),
        ("Place test orders on a test store, through every enabled channel", "Owner and QA", "no"),
        ("Turn the live flag on", "Brand &amp; Store", "no"),
    ]
    ids = []
    for i, (t, owner, code) in enumerate(steps):
        col, row = (0, i) if i < 7 else (1, i - 7)
        x = 24 + col * 842
        y = 190 + row * 76
        sid = "st%02d" % (i + 1)
        ids.append(sid)
        p.box(sid, x, y, 810, 58, t, ["Owner: %s &#183; Needs code: %s" % (owner, code)], kind="enginew",
              step=i + 1, align="left")
    for i in range(12):
        a, b = ids[i], ids[i + 1]
        if i == 6:
            p.edge(a, b, "flow", None, sp="r", dp="l", via=[(850, 190 + 6 * 76 + 29), (850, 190 + 29)])
        else:
            p.edge(a, b, "flow", None, sp="b", dp="t")
    p.box("readiness", 866, 190 + 6 * 76, 810, 120, "Readiness check (proposed)",
          ["admin-bff asks each owning domain one read-only question, 'is this brand ready?', and shows all answers on one page.",
           "Examples: every store has a valid pos_connection; a menu version exists; a gateway key exists.",
           "A set of gRPC reads. No topic and no new service. The name CheckBrandReadiness is a placeholder."],
          kind="note", dashed=True, shape="rect", size=12, align="left")

    # ------------------------------------------------------------------ page 2: capability AND feature AND store
    q = d.page("2 Capability, feature and store setup", 1600, 1040)
    frame(q, "What decides if a brand can offer something: three yes answers",
          "docs/design/brand-configuration.md section 3 and 5; docs/design/pos-adapters.md section 6",
          ["P-37: unset means off; the most specific setting wins",
           "O-28: the real capability list per POS vendor is still to learn",
           "GetFulfillmentOptions is a proposed name, not drawn in any HLD yet"])
    q.box("vendor", 40, 110, 360, 110, "Vendor capability", ["What the POS vendor can do", "Example: the POS supports delivery tickets",
                                                          "Set by the vendor profile, store override on top"], kind="enginew", step=1)
    q.box("feature", 40, 250, 360, 110, "Brand feature", ["What the brand has switched on", "Example: the brand offers delivery",
                                                          "Brand &amp; Store feature switch (proposed)"], kind="enginew", step=2)
    q.box("store", 40, 390, 360, 110, "Store setup", ["What this store has configured", "Example: a fleet provider is listed for the store",
                                                       "Valid pos_connection, hours, zone"], kind="enginew", step=3)
    q.box("and", 560, 220, 220, 160, "AND", ["all three say yes", "= effective capability"], kind="grpc", shape="diamond")
    q.box("yes", 960, 150, 360, 100, "Offer the option in the app", ["GetFulfillmentOptions(brand, store) says yes"], kind="fact")
    q.box("no", 960, 350, 360, 110, "Hide the option", ["PlaceOrder returns FAILED_PRECONDITION", "for example fulfillment_not_supported"],
          kind="fail")
    for nid, y in (("vendor", 165), ("feature", 305), ("store", 445)):
        q.edge(nid, "and", "flow", None, sp="r", dp=("l", 0.5), via=[(480, y), (480, 300)])
    q.edge("and", "yes", "fact", "yes", sp=("t", 0.5), dp="l", via=[(670, 200)], lab=0.45)
    q.edge("and", "no", "fail", "no", sp=("b", 0.5), dp="l", via=[(670, 405)], lab=0.45)
    q.box("rules", 40, 540, 760, 200, "Four rules (proposed)",
          ["Default is off: a capability or feature that is not set is false. A new brand starts with nothing on.",
           "Most specific wins: store override, then brand, then vendor profile. Never the other way.",
           "A flag has a behaviour for false. A flag whose false case nobody handles is not added.",
           "The app asks the owning domain what to show. It never guesses from a brand name."],
          kind="note", shape="rect", size=12, align="left", valign="top")
    q.box("data", 830, 540, 360, 330, "Data (a row, changed by an admin)",
          ["which POS vendor a store uses, and its routing values", "capability overrides, feature switches",
           "gateway account per brand", "aggregator on or off, SKU mapping", "earn rules, tiers, deal parameters",
           "templates, channel settings", "provider order per store", "which capability runs on a legacy system"],
          kind="data", shape="rect", size=12, align="left", valign="top")
    q.box("code", 1230, 540, 330, 330, "Code (a deploy)",
          ["a new POS adapter and mapper", "a new capability flag and its behaviour", "a new payment provider",
           "a new aggregator mapper", "a new type of rule in the deal engine", "a new channel type", "a new fleet provider",
           "a new legacy adapter"], kind="engine", shape="rect", size=12, align="left", valign="top")
    q.box("tip", 40, 760, 760, 110, "Before you write code for 'brand X behaves differently'",
          ["Check first whether the difference can be a typed setting that existing code reads."], kind="note", shape="rect",
          size=12, align="left", valign="top")

    # ------------------------------------------------------------------ page 3: hub and owners
    r = d.page("3 Who owns which setting", 1700, 1020)
    frame(r, "Brands are rows: each domain owns its own slice, keyed by brand_id",
          "docs/design/brand-configuration.md section 2 and 6; docs/architecture.md principle 6, D-07",
          ["P-37: no central config service and no shared config table",
           "O-27: who owns brand configuration as a whole, and who approves a change?",
           "Every slice is versioned and audited, holds a Vault path, never a secret"])
    r.box("hub", 640, 430, 420, 130, "One brand = one row of brand_id", ["There are no per-brand services, topics or databases",
                                                                          "brand_id is on every gRPC call, Kafka key and table"],
          kind="neutral", shape="rect", size=13)
    r.box("adm", 60, 440, 200, 110, "admin-bff", ["every configuration write goes", "through here, with a grant"], kind="enginew")
    r.box("ready", 1440, 440, 200, 110, "Readiness check", ["proposed: reads each owner", "before the live flag"], kind="enginew",
          dashed=True)
    r.edge("adm", "hub", "grpc", "writes (versioned, audited)", sp="r", dp="l")
    r.edge("ready", "hub", "grpc", "reads each owner", sp="l", dp="r")
    top = [("o.bs", "Brand &amp; Store", ["brand, live flag, feature switches,", "onboarding state; store hours, zone"], True),
           ("o.cat", "Catalog", ["menu, price book,", "channel prices"], False),
           ("o.oms", "Cart &amp; Order", ["POS connection and capability", "overrides; aggregator mapping per store"], False),
           ("o.pay", "Payment &amp; Billing", ["gateway keys and", "provider choice"], False),
           ("o.del", "Delivery &amp; Dispatch", ["provider list per store,", "quote scheme"], False)]
    bot = [("o.not", "Notification", ["channel config", "and templates"], False),
           ("o.loy", "Loyalty &amp; MemberCard", ["earn rules, tiers,", "reward prices"], False),
           ("o.wal", "Wallet", ["wallet limits"], False),
           ("o.vou", "Voucher &amp; Campaign", ["campaign rules"], False),
           ("o.idn", "Identity &amp; Profile", ["brand membership, consent,", "brand app client, consent wording"], False)]
    for i, (id_, t, dd, dash) in enumerate(top):
        r.box(id_, 60 + i * 320, 150, 300, 130, t, dd, kind="enginew", dashed=dash)
    for i, (id_, t, dd, dash) in enumerate(bot):
        r.box(id_, 60 + i * 320, 700, 300, 130, t, dd, kind="enginew")
    r.fan("hub", [x[0] for x in top], "plain", side="t", trunk=350, arrow="none")
    r.fan("hub", [x[0] for x in bot], "plain", side="b", trunk=630, arrow="none")
    r.text("t2", 60, 846, 1500, 20,
           "Legacy routing per capability (brand_id and capability) is owned by the domain that has the legacy adapter. See 08-legacy-bridge.",
           size=11, color="#64748B")
    return d
