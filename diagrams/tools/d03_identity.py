"""03 - Identity: Minor ID across brands (2 pages)."""
from drawio_lib import Diagram, frame


def build():
    d = Diagram("03-identity-minor-id.drawio", "Identity and Minor ID")

    # ------------------------------------------------------------------ page 1: the model
    p = d.page("1 One person, many brands", 1700, 1060)
    frame(p, "Minor ID: one account, shared profile, loyalty and wallet stay per brand",
          "docs/design/identity-model.md section 1 to 4; docs/architecture.md P-33, P-40, D-11",
          ["O-06: how Kong sets X-Brand-Id for a customer in more than one brand",
           "O-33: default consent, sign-in minimum, what happens to a balance when a brand is disabled",
           "O-26: what a franchisor sees; O-19 and O-20: cross-brand wallet and points are deferred"])
    p.lane("idn", 24, 84, 1652, 216, "Identity &amp; Profile: one record per person, for all brands", "engine")
    p.box("minor", 300, 124, 330, 110, "Minor ID account", ["login identifier, sign-in methods, status", "one per person, all brands"],
          kind="enginew", parent="idn")
    p.box("profile", 800, 124, 330, 110, "Shared profile", ["name, birthday, preferences, addresses", "origin_brand_id on every row"],
          kind="enginew", parent="idn")
    p.box("gate", 1230, 124, 290, 110, "PDPA consent gate", ["checked in Identity on every", "cross-brand read; withdraw any time"],
          kind="grpc", parent="idn")
    p.edge("minor", "profile", "plain", "one profile", sp="r", dp="l")
    p.edge("profile", "gate", "grpc", "every read", sp="r", dp="l")

    p.lane("brands", 24, 340, 1652, 540, "Per brand: membership, loyalty, wallet, carts and orders (D-11: nothing crosses brands)", "neutral")
    cfg = [("A", 40, "Brand A (example: Bonchon)", True), ("B", 590, "Brand B (example: The Pizza Company)", True),
           ("C", 1140, "Brand C (a brand where this customer is disabled)", False)]
    for k, x, title, enabled in cfg:
        p.lane("br" + k, x, 380, 520, 480, title, "engine" if enabled else "neutral", parent="brands", dashed=not enabled)
        p.box("m" + k, x + 10, 430, 500, 90,
              "Membership: enabled" if enabled else "Membership: disabled",
              ["customer_id + brand_id; the customer can sign in and use this brand"] if enabled else
              ["the customer cannot sign in to this brand; the data is kept, not usable"],
              kind="enginew" if enabled else "fail", parent="br" + k)
        names = [("loy", "Loyalty profile", ["points, tier, card", "Loyalty &amp; MemberCard"]),
                 ("wal", "E-wallet", ["balance and ledger", "Wallet"]),
                 ("ord", "Cart and orders", ["one open cart per brand", "Cart &amp; Order"])]
        for i, (nid, t, dd) in enumerate(names):
            p.box("%s%s" % (nid, k), x + 10 + i * 172, 600, 156, 120, t, dd,
                  kind="enginew" if enabled else "neutral", dashed=not enabled, parent="br" + k)
        p.fan("m" + k, ["%s%s" % (n[0], k) for n in names], "plain", side="b", trunk=560, arrow="none")
    # Minor ID to each membership: trunk in the gap between the Identity lane and the brand lanes
    for k, x, _, _ in cfg:
        ex = x + 10 + 100
        p.edge("minor", "m" + k, "plain", None, sp=("b", 0.5), dp=("t", 100 / 500.0), via=[(465, 322), (ex, 322)], arrow="block")
    p.edge("gate", "brands", "grpc", "a brand reads shared rows only if the customer agreed", sp=("b", 0.5), dp=("t", (1375 - 24) / 1652.0),
           lab=0.55, loff=(-190, 0))
    p.text("n1", 24, 890, 1652, 36,
           "D-11 (confirmed 2026-10-24): one customer across brands means many loyalty profiles and many wallets. Nothing moves a balance "
           "between brands. One wallet or points balance across brands is a later option (O-19, O-20: deferred).",
           size=11, color="#475569")

    # ------------------------------------------------------------------ page 2: sign in, enable, disable
    q = d.page("2 Sign-in and disable per brand", 1700, 1000)
    frame(q, "Minor ID: sign in to one brand, and what happens when a brand is disabled",
          "docs/design/identity-model.md section 2; docs/architecture.md P-40, section 8",
          ["O-06: Kong setting X-Brand-Id from the brand app is a proposal, not yet confirmed",
           "O-33: what happens to wallet, points and notifications of a disabled brand",
           "P-40: a disable takes effect at the next token refresh, up to 5 minutes"])
    q.box("app", 40, 130, 230, 100, "Brand B app", ["the customer opens it", "client id of Brand B"], kind="http", step=1)
    q.box("kong", 340, 130, 230, 100, "Kong", ["sets X-Brand-Id from the brand app", "(host or client id) - proposed"], kind="http", step=2)
    q.box("bff", 640, 130, 230, 100, "customer-bff", ["StartSignIn, VerifyOtp,", "JoinBrand for a new brand"], kind="enginew", step=3)
    q.box("idn", 940, 130, 330, 100, "Identity &amp; Profile", ["checks the membership of this customer", "in this brand (customer_id, brand_id)"],
          kind="engine", step=4)
    q.edge("app", "kong", "http", "HTTPS", sp="r", dp="l")
    q.edge("kong", "bff", "http", "route", sp="r", dp="l")
    q.edge("bff", "idn", "grpc", "gRPC", sp="r", dp="l")
    q.box("dec", 960, 300, 290, 150, "Membership enabled for this brand?", [], kind="grpc", shape="diamond")
    q.edge("idn", "dec", "data", "read membership", sp="b", dp="t")
    q.box("tok", 520, 315, 330, 120, "Issue a token for this brand only",
          ["brand_id claim, access token 5 minutes,", "refresh checks the membership again", "returned to the app"], kind="engine", step=5)
    q.box("deny", 1330, 315, 300, 120, "No token", ["sign-in refused for this brand", "the data is kept, not usable"], kind="fail")
    q.edge("dec", "tok", "grpc", "yes", sp="l", dp="r")
    q.edge("dec", "deny", "fail", "no, disabled", sp="r", dp="l")
    q.box("kcheck", 340, 540, 330, 110, "Kong checks every later request",
          ["rejects a token whose brand_id differs", "from the route the request is for"], kind="http", step=6)
    q.edge("app", "kcheck", "http", "later requests", sp=("b", 0.5), dp="l", via=[(155, 595)], lab=0.55)
    q.edge("tok", "kcheck", "plain", "token is used", sp=("b", 0.5), dp="r", via=[(685, 595)], lab=0.3)
    q.box("dis1", 40, 740, 340, 110, "The customer disables Brand B",
          ["customer-bff for the customer, or", "admin-bff with a grant for support"], kind="enginew", step=7)
    q.box("dis2", 440, 740, 300, 110, "Membership becomes disabled", ["Identity writes the status", "no event is published"], kind="engine")
    q.box("dis3", 800, 740, 330, 110, "Takes effect at the next RefreshToken",
          ["the access token lives 5 minutes, so", "the lag is up to 5 minutes"], kind="engine")
    q.edge("dis1", "dis2", "grpc", "gRPC", sp="r", dp="l")
    q.edge("dis2", "dis3", "plain", "at refresh", sp="r", dp="l")
    q.edge("dis3", "dec", "grpc", "re-check", sp=("t", (1060 - 800) / 330.0), dp="b", lab=0.5, loff=(40, 0))
    q.text("n1", 1180, 560, 450, 150,
           "<b>Same person, other brands:</b> disabling Brand B does not touch the Minor ID or the memberships in other brands. "
           "A customer who stays in one brand is a Minor ID with one enabled membership.",
           size=12, color="#475569")
    return d
