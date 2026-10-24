"""09 - AI assistant integration (2 pages)."""
from drawio_lib import Diagram, frame

REF = "docs/design/tech-stack.md (AI-ready edge); docs/platform-concept.md step 5; docs/architecture.md P-34, P-41"
QS = ["O-24: which model and vendor, which component hosts the assistant, and which data it may read under PDPA consent",
      "O-35: does it act as the customer with a scoped token, or as a service principal; which operations are allowed",
      "P-41: the edge is REST only for now; the assistant is added later"]


def build():
    d = Diagram("09-ai-assistant-integration.drawio", "AI assistant integration")

    # ------------------------------------------------------------ page 1
    p = d.page("1 What the assistant may read and write", 1700, 980)
    frame(p, "The AI assistant owns no state: it reads like the app and writes only through UpdateCart", REF, QS)
    p.box("app", 24, 330, 220, 110, "Customer app", ["the shopper taps or asks in words"], kind="http")
    p.box("ai", 24, 120, 260, 130, "AI assistant (later)", ["no menu, price, stock or cart of its own;", "its context window is not a data store", "home and vendor: open (O-24)"], kind="enginew", dashed=True)
    p.lane("edge", 360, 100, 640, 440, "Edge: REST only (P-41)", "http")
    p.box("kong", 390, 230, 150, 150, "Kong", ["the only policy", "enforcement point"], kind="http", parent="edge")
    p.box("bff", 640, 230, 330, 150, "customer-bff", ["OpenAPI per BFF, idempotency_key on writes", "separate rate bucket for assistant traffic", "audit row: came from the assistant, with prompt id"], kind="enginew", parent="edge", align="left", valign="top", size=12)
    p.edge("app", "kong", "http", "customer JWT", sp="r", dp=("l", 0.75))
    p.edge("ai", "kong", "http", "scoped token", sp="r", dp=("l", 0.25), via=[(330, 185), (330, 267), ])
    p.edge("kong", "bff", "http", None, sp="r", dp="l")
    p.lane("core", 1080, 100, 596, 520, "Core: gRPC behind the BFF", "engine")
    p.box("cat", 1110, 150, 536, 110, "Catalog", ["READ: GetMenu, availability, PriceLines", "live data the answer must be grounded in"], kind="enginew", parent="core")
    p.box("ord", 1110, 330, 536, 130, "Cart &amp; Order", ["READ: order history, GetCart", "WRITE: UpdateCart (the only write)", "one cart per (brand_id, customer_id), priced live"], kind="enginew", parent="core")
    p.box("idn", 1110, 510, 536, 80, "Identity &amp; Profile", ["PDPA consent decides what the assistant may read (O-24)"], kind="grpc", parent="core", dashed=True)
    p.edge("bff", "cat", "grpc", "reads", sp=("r", 0.2), dp="l")
    p.edge("bff", "ord", "grpc", "reads + UpdateCart", sp=("r", 0.8), dp="l")
    p.box("no", 360, 600, 640, 150, "What the assistant cannot do (proposed token scope)",
          ["It cannot place an order or pay: the shopper does that with the normal PlaceOrder.", "It cannot change a menu, a price, stock, a store or a deal.", "It carries a token that names the customer and the allowed operations, such as read menu, read order history, UpdateCart."],
          kind="fail", dashed=True, align="left", valign="top", size=12)
    p.text("n1", 24, 600, 300, 150, "Manual and AI orders share <b>one cart and one price</b> (P-34), so whatever the assistant adds, the shopper sees and edits like any other line.", size=12, color="#475569")
    p.text("n2", 1080, 650, 596, 100, "No new Kafka topic: every AI read is a gRPC read and the write is UpdateCart (P-35). The shopper is waiting, so none of it is a topic.", size=12, color="#475569")

    # ------------------------------------------------------------ page 2
    q = d.page("2 One AI order, and what the edge needs", 1700, 1000)
    frame(q, "An AI order in five steps, and the six things the edge needs to be AI-ready", REF, QS)
    steps = [("s1", "Shopper says what is needed", ["\"Dinner for 4, one of us does not eat spicy, under 1,000 baht\""], "http"),
             ("s2", "Assistant reads live data", ["menu, this customer's deals, live stock at the", "nearest store, past orders"], "enginew"),
             ("s3", "Assistant fills the cart", ["UpdateCart replaces the whole cart", "and checks its version"], "enginew"),
             ("s4", "Shopper reviews", ["adds 8 items, or refines: make it 800, add a dessert"], "http"),
             ("s5", "Shopper pays as usual", ["PlaceOrder and the checkout flow, unchanged"], "http")]
    for i, (id_, t, dd, k) in enumerate(steps):
        q.box(id_, 24 + i * 336, 130, 296, 130, t, dd, kind=k, step=i + 1, dashed=(id_ in ("s2", "s3")), size=12)
    for a, b in zip(["s1", "s2", "s3", "s4"], ["s2", "s3", "s4", "s5"]):
        q.edge(a, b, "flow", None, sp="r", dp="l")
    q.text("h", 24, 300, 1600, 24, "<b>The AI-ready edge</b>: keep the list short and build only what has a named user", size=13, color="#0F172A")
    needs = [("n1", "Stable contracts", "One OpenAPI document per BFF, versioned, with a CI diff that fails on a breaking change.", "Proposed"),
             ("n2", "Tool-friendly operations", "Small single-purpose operations, clear names, typed errors, an idempotency_key on every write (P-01).", "Proposed"),
             ("n3", "Scoped tokens", "A token that names the customer and the allowed operations. It cannot place an order or pay. Identity model: O-35.", "Proposed"),
             ("n4", "Audit", "Every AI write has an audit row that says it came from the assistant, with the prompt id, in the same transaction.", "Proposed"),
             ("n5", "No new state", "The AI keeps no cart, menu or price of its own (P-34). Its context window is not a data store.", "Decided (P-34)"),
             ("n6", "Rate limits", "A separate token bucket for assistant traffic at Kong, so it cannot starve the shopper path.", "Proposed")]
    for i, (id_, t, dd, st) in enumerate(needs):
        x = 24 + (i % 3) * 556
        y = 340 + (i // 3) * 200
        q.box(id_, x, y, 520, 170, t, [dd, "", "Status: " + st], kind="enginew", dashed=(st == "Proposed"), align="left", valign="top", size=13)
    return d
