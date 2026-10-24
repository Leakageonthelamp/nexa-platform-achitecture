#!/usr/bin/env python3
"""Tiny helper library to generate native draw.io (mxfile, uncompressed) diagrams.

Boxes, lanes (containers), free text and orthogonal edges with explicit source and target ids.
The library keeps its own copy of the geometry, so validate_diagrams.py can check overlaps,
lines through boxes, label clashes and text fit without opening draw.io.

Nothing here is NEXA-specific except the colour legend, which follows docs/architecture.md section 11.
"""
import re
from xml.sax.saxutils import escape

# ---------------------------------------------------------------- colours (architecture.md section 11)
KIND = {
    #  stroke,    fill,      ink (darker text colour)
    "grpc":    ("#EA580C", "#FFF7ED", "#C2410C"),
    "http":    ("#2563EB", "#EFF6FF", "#1D4ED8"),
    "cmd":     ("#7C3AED", "#F5F3FF", "#6D28D9"),
    "fact":    ("#059669", "#ECFDF5", "#047857"),
    "engine":  ("#EAB308", "#FEF9C3", "#854D0E"),
    "enginew": ("#EAB308", "#FFFFFF", "#854D0E"),   # engine box on a white page
    "data":    ("#64748B", "#F8FAFC", "#475569"),
    "neutral": ("#94A3B8", "#F8FAFC", "#475569"),
    "fail":    ("#DC2626", "#FEF2F2", "#B91C1C"),
    "note":    ("#CBD5E1", "#FFFFFF", "#475569"),
    "plain":   ("none", "none", "#334155"),
}
LINE = {  # edge kind -> (colour, dash pattern or None, text ink)
    "grpc": ("#EA580C", None, "#C2410C"),
    "http": ("#2563EB", None, "#1D4ED8"),
    "cmd":  ("#7C3AED", "6 4", "#6D28D9"),
    "fact": ("#059669", "6 4", "#047857"),
    "data": ("#64748B", None, "#475569"),
    "log":  ("#64748B", "2 4", "#475569"),
    "fail": ("#DC2626", "6 4", "#B91C1C"),
    "plain": ("#94A3B8", None, "#475569"),
    "flow": ("#334155", None, "#334155"),
}
FONT = "Helvetica"

# ---------------------------------------------------------------- text measuring
try:
    from PIL import ImageFont
    _R = ImageFont.truetype("/usr/share/fonts/opentype/urw-base35/NimbusSans-Regular.otf", 100)
    _B = ImageFont.truetype("/usr/share/fonts/opentype/urw-base35/NimbusSans-Bold.otf", 100)
except Exception:  # pragma: no cover
    _R = _B = None


def text_w(s, size=11, bold=False):
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    if _R is None:
        return len(s) * size * (0.6 if bold else 0.55)
    return (_B if bold else _R).getlength(s) * size / 100.0


def wrap_lines(s, width, size=11, bold=False):
    """Greedy word wrap; returns the number of lines the browser would draw."""
    n = 0
    for para in re.split(r"<br\s*/?>|\n", s):
        words = para.split(" ")
        cur = ""
        lines = 1
        for w in words:
            t = (cur + " " + w).strip()
            if text_w(t, size, bold) <= width or not cur:
                cur = t
            else:
                lines += 1
                cur = w
        n += lines
    return n


def badge(n):
    return ('<b style="background-color:#0F172A;color:#FFFFFF;border-radius:9px;padding:0px 6px;">%s</b>&nbsp;' % n)


def badge_w(n):
    return text_w(str(n), 11, True) + 18


def h(s):
    return escape(s)


# ---------------------------------------------------------------- model
class Node:
    def __init__(self, page, id, x, y, w, hgt, kind, title, details, dashed, parent, container, meta,
                 shape, size, step, align, style_extra, valign):
        self.page, self.id, self.x, self.y, self.w, self.h = page, id, x, y, w, hgt
        self.kind, self.title, self.details = kind, title, details or []
        self.dashed, self.parent, self.container, self.meta = dashed, parent, container, meta
        self.shape, self.size, self.step, self.align = shape, size, step, align
        self.style_extra, self.valign = style_extra, valign

    def rect(self):
        return (self.x, self.y, self.x + self.w, self.y + self.h)

    def port(self, side, frac=0.5):
        if side == "r":
            return (self.x + self.w, self.y + self.h * frac)
        if side == "l":
            return (self.x, self.y + self.h * frac)
        if side == "t":
            return (self.x + self.w * frac, self.y)
        if side == "b":
            return (self.x + self.w * frac, self.y + self.h)
        raise ValueError(side)

    # html label --------------------------------------------------------------
    def label_html(self):
        stroke, fill, ink = KIND[self.kind]
        t = ""
        if self.step is not None:
            t += badge(self.step)
        if self.title:
            t += "<b>%s</b>" % self.title_html()
        for k, d in enumerate(self.details):
            t += ("<br>" if (t or k) else "") + ("<font style=\"font-size:%dpx\" color=\"%s\">%s</font>" % (self.size - 1 if self.size > 11 else 11, ink, d))
        return t

    def title_html(self):
        return self.title  # callers pass already-escaped html-safe text (use h() for & < >)


class Edge:
    def __init__(self, page, id, src, dst, kind, label, step, pts, sp, dp, lab, loff, width, dashed, arrow):
        self.page, self.id, self.src, self.dst, self.kind = page, id, src, dst, kind
        self.label, self.step, self.pts, self.sp, self.dp = label, step, pts, sp, dp
        self.lab, self.loff, self.width, self.dashed, self.arrow = lab, loff, width, dashed, arrow

    def length(self):
        return sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(self.pts, self.pts[1:]))

    def point_at(self, t):
        total = self.length()
        d = total * t
        for a, b in zip(self.pts, self.pts[1:]):
            seg = abs(a[0] - b[0]) + abs(a[1] - b[1])
            if d <= seg or (a, b) == (self.pts[-2], self.pts[-1]):
                f = 0 if seg == 0 else min(1, d / seg)
                return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
            d -= seg
        return self.pts[-1]

    def label_text(self):
        t = ""
        if self.step is not None:
            t += badge(self.step)
        t += self.label or ""
        return t

    def label_box(self):
        if not (self.label or self.step is not None):
            return None
        cx, cy = self.point_at(self.lab)
        cx += self.loff[0]
        cy += self.loff[1]
        w = (text_w(self.label or "", 11) + 10) + (badge_w(self.step) if self.step is not None else 0)
        hh = 18
        return (cx - w / 2, cy - hh / 2, cx + w / 2, cy + hh / 2)


class Page:
    def __init__(self, diagram, key, name, w, hgt):
        self.diagram, self.key, self.name, self.w, self.h = diagram, key, name, w, hgt
        self.nodes, self.edges = {}, {}
        self.order = []  # emission order
        self.notes = []  # (decision ids used) strings for validation
        self.refs = set()

    # --- creation --------------------------------------------------------------
    def _add_node(self, n):
        if n.id in self.nodes or n.id in self.edges:
            raise ValueError("duplicate id %s on page %s" % (n.id, self.name))
        self.nodes[n.id] = n
        self.order.append(("n", n.id))
        for t in [n.title] + n.details:
            self.refs.update(re.findall(r"\b([PDO]-\d\d)\b", t or ""))
        return n

    def lane(self, id, x, y, w, hgt, title, kind="neutral", dashed=False, sub=None, parent=None, size=12):
        n = Node(self, id, x, y, w, hgt, kind, title, [sub] if sub else [], dashed, parent, True, False,
                 "lane", size, None, "left", "", "top")
        return self._add_node(n)

    def box(self, id, x, y, w, hgt, title, details=None, kind="engine", dashed=False, parent=None,
            shape="rounded", size=12, step=None, align="center", meta=False, valign="middle", extra=""):
        n = Node(self, id, x, y, w, hgt, kind, title, details, dashed, parent, False, meta,
                 shape, size, step, align, extra, valign)
        return self._add_node(n)

    def text(self, id, x, y, w, hgt, html_text, size=11, color="#334155", align="left", bold=False,
             meta=False, valign="top", parent=None):
        n = Node(self, id, x, y, w, hgt, "plain", "", [], False, parent, False, meta, "text", size, None,
                 align, "", valign)
        n.raw = html_text
        n.color = color
        n.bold = bold
        return self._add_node(n)

    def pill(self, id, x, y, w, hgt, text, kind="neutral", dashed=False, parent=None, size=11):
        n = Node(self, id, x, y, w, hgt, kind, text, [], dashed, parent, False, True, "pill", size, None,
                 "center", "", "middle")
        return self._add_node(n)

    def swatch_line(self, id, x, y, w, kind, parent=None):
        n = Node(self, id, x, y, w, 8, "plain", "", [], False, parent, False, True, "line:" + kind, 11, None,
                 "center", "", "middle")
        return self._add_node(n)

    # --- edges -----------------------------------------------------------------
    def edge(self, src, dst, kind="grpc", label=None, step=None, sp="r", dp="l", via=None, lab=0.5,
             loff=(0, 0), width=2, dashed=None, arrow="block", id=None):
        a, b = self.nodes[src], self.nodes[dst]
        sps = sp if isinstance(sp, tuple) else (sp, 0.5)
        dps = dp if isinstance(dp, tuple) else (dp, 0.5)
        p0 = a.port(*sps)
        p1 = b.port(*dps)
        pts = _route(p0, sps[0], p1, dps[0], via or [])
        eid = id or "e.%s.%s" % (src, dst)
        k = 2
        base = eid
        while eid in self.edges or eid in self.nodes:
            eid = "%s.%d" % (base, k)
            k += 1
        e = Edge(self, eid, src, dst, kind, label, step, pts, (sps), (dps), lab, loff, width, dashed, arrow)
        self.edges[eid] = e
        self.order.append(("e", eid))
        if label:
            self.refs.update(re.findall(r"\b([PDO]-\d\d)\b", label))
        return e

    def fan(self, src, dsts, kind="grpc", side="b", trunk=None, labels=None, **kw):
        """One trunk from src to several targets (targets above, below, left or right)."""
        a = self.nodes[src]
        out = []
        for i, d in enumerate(dsts):
            b = self.nodes[d]
            if side in ("b", "t"):
                ty = trunk if trunk is not None else ((a.y + a.h + b.y) / 2 if side == "b" else (b.y + b.h + a.y) / 2)
                sp = (side, 0.5)
                dp = ("t" if side == "b" else "b", 0.5)
                sx, _ = a.port(*sp)
                dx, _ = b.port(*dp)
                via = [(sx, ty), (dx, ty)] if abs(sx - dx) > 0.5 else []
            else:
                tx = trunk if trunk is not None else ((a.x + a.w + b.x) / 2 if side == "r" else (b.x + b.w + a.x) / 2)
                sp = (side, 0.5)
                dp = ("l" if side == "r" else "r", 0.5)
                _, sy = a.port(*sp)
                _, dy = b.port(*dp)
                via = [(tx, sy), (tx, dy)] if abs(sy - dy) > 0.5 else []
            lab = (labels or {}).get(d)
            out.append(self.edge(src, d, kind=kind, label=lab, sp=sp, dp=dp, via=via, **kw))
        return out

    # --- helpers ---------------------------------------------------------------
    def abs_rect(self, n):
        return n.rect()

    def ancestors(self, n):
        out = []
        p = n.parent
        while p:
            out.append(p)
            p = self.nodes[p].parent
        return out


def _dedupe(pts):
    out = []
    for p in pts:
        p = (round(p[0], 1), round(p[1], 1))
        if not out or out[-1] != p:
            out.append(p)
    # drop collinear middle points
    changed = True
    while changed and len(out) > 2:
        changed = False
        for i in range(1, len(out) - 1):
            a, b, c = out[i - 1], out[i], out[i + 1]
            if (a[0] == b[0] == c[0]) or (a[1] == b[1] == c[1]):
                del out[i]
                changed = True
                break
    return out


def _route(p0, sside, p1, dside, via):
    pts = [p0] + [tuple(v) for v in via] + [p1]
    out = [pts[0]]
    head = "h" if sside in ("l", "r") else "v"
    arr = "h" if dside in ("l", "r") else "v"
    for i in range(1, len(pts)):
        p, q = out[-1], pts[i]
        last = i == len(pts) - 1
        if abs(p[0] - q[0]) < 0.01 or abs(p[1] - q[1]) < 0.01:
            out.append(q)
            head = "h" if abs(p[1] - q[1]) < 0.01 else "v"
            if abs(p[0] - q[0]) < 0.01 and abs(p[1] - q[1]) < 0.01:
                pass
            continue
        # need an elbow
        if last and i == 1:
            if head == "h" and arr == "h":
                mx = (p[0] + q[0]) / 2
                out += [(mx, p[1]), (mx, q[1]), q]
                head = "h"
            elif head == "v" and arr == "v":
                my = (p[1] + q[1]) / 2
                out += [(p[0], my), (q[0], my), q]
                head = "v"
            elif head == "h":
                out += [(q[0], p[1]), q]
                head = "v"
            else:
                out += [(p[0], q[1]), q]
                head = "h"
            continue
        if head == "h":
            e = (q[0], p[1])
            newhead = "v"
        else:
            e = (p[0], q[1])
            newhead = "h"
        if last and newhead != arr:
            e = (p[0], q[1]) if head == "h" else (q[0], p[1])
            newhead = "h" if head == "h" else "v"
        out += [e, q]
        head = newhead
    return _dedupe(out)


class Diagram:
    def __init__(self, fname, title):
        self.fname, self.title = fname, title
        self.pages = []

    def page(self, name, w=1600, h=1000):
        key = "p%d" % (len(self.pages) + 1)
        p = Page(self, key, name, w, h)
        self.pages.append(p)
        return p

    # --- XML ---------------------------------------------------------------------
    def to_xml(self):
        out = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<mxfile host="app.diagrams.net" agent="NEXA diagram generator" version="24.0.0" type="device">']
        for pg in self.pages:
            out.append(' <diagram id="%s" name="%s">' % (pg.key, h(pg.name)))
            out.append('  <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" '
                       'arrows="1" fold="1" page="1" pageScale="1" pageWidth="%d" pageHeight="%d" math="0" shadow="0">'
                       % (pg.w, pg.h))
            out.append("   <root>")
            out.append('    <mxCell id="0"/>')
            out.append('    <mxCell id="1" parent="0"/>')
            for kind, i in pg.order:
                if kind == "n":
                    out.append(self._node_xml(pg, pg.nodes[i]))
                else:
                    out.append(self._edge_xml(pg, pg.edges[i]))
            out.append("   </root>")
            out.append("  </mxGraphModel>")
            out.append(" </diagram>")
        out.append("</mxfile>")
        return "\n".join(out) + "\n"

    def _node_xml(self, pg, n):
        stroke, fill, ink = KIND[n.kind]
        par = "1"
        x, y = n.x, n.y
        if n.parent:
            pn = pg.nodes[n.parent]
            par = pn.id
            x, y = n.x - pn.x, n.y - pn.y
        common = "html=1;whiteSpace=wrap;fontFamily=%s;" % FONT
        if n.shape == "lane":
            style = (common + "rounded=1;arcSize=2;container=1;collapsible=0;recursiveResize=0;verticalAlign=top;align=left;"
                     "spacingLeft=10;spacingTop=4;fontSize=%d;fontStyle=1;fontColor=%s;strokeColor=%s;fillColor=%s;strokeWidth=1.5;"
                     % (n.size, ink, stroke, fill))
            if n.dashed:
                style += "dashed=1;dashPattern=8 4;"
            val = "<b>%s</b>" % n.title
            if n.details:
                val += "<br><font style=\"font-size:11px;font-weight:normal\" color=\"%s\">%s</font>" % (ink, n.details[0])
            # sub-title inside lane keeps lane header readable
            return self._cell(n.id, val, style, par, x, y, n.w, n.h)
        if n.shape == "text":
            style = (common + "text;strokeColor=none;fillColor=none;align=%s;verticalAlign=%s;fontSize=%d;fontColor=%s;"
                     "spacingLeft=2;spacingRight=2;spacingTop=0;spacingBottom=0;%s" %
                     (n.align, n.valign, n.size, n.color, "fontStyle=1;" if n.bold else ""))
            return self._cell(n.id, n.raw, style, par, x, y, n.w, n.h)
        if n.shape.startswith("line:"):
            lk = n.shape[5:]
            col, dash, _ = LINE[lk]
            style = "shape=line;strokeWidth=2;strokeColor=%s;html=1;" % col
            if dash:
                style += "dashed=1;dashPattern=%s;" % dash
            return self._cell(n.id, "", style, par, x, y, n.w, n.h)
        if n.shape == "pill":
            style = (common + "rounded=1;arcSize=50;fontSize=%d;fontColor=%s;strokeColor=%s;fillColor=%s;strokeWidth=1.5;"
                     "spacingLeft=4;spacingRight=4;spacingTop=0;spacingBottom=0;" % (n.size, ink, stroke, fill))
            if n.dashed:
                style += "dashed=1;dashPattern=6 3;"
            return self._cell(n.id, "<b>%s</b>" % n.title, style, par, x, y, n.w, n.h)
        # rounded box / rect / cylinder / diamond / hex
        shp = {"rounded": "rounded=1;arcSize=10;",
               "rect": "rounded=0;",
               "cylinder": "shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=10;",
               "diamond": "rhombus;",
               "hex": "shape=hexagon;perimeter=hexagonPerimeter2;size=0.12;fixedSize=0;",
               "ellipse": "ellipse;",
               }[n.shape]
        style = (common + shp + "fontSize=%d;fontColor=%s;strokeColor=%s;fillColor=%s;strokeWidth=1.5;align=%s;verticalAlign=%s;"
                 "spacingLeft=6;spacingRight=6;spacingTop=2;spacingBottom=2;" % (n.size, "#0F172A", stroke, fill, n.align, n.valign))
        if n.dashed:
            style += "dashed=1;dashPattern=6 3;"
        if n.style_extra:
            style += n.style_extra
        return self._cell(n.id, n.label_html(), style, par, x, y, n.w, n.h)

    def _cell(self, id, value, style, parent, x, y, w, hgt):
        return ('    <mxCell id="%s" value="%s" style="%s" vertex="1" parent="%s">\n'
                '     <mxGeometry x="%g" y="%g" width="%g" height="%g" as="geometry"/>\n    </mxCell>'
                % (id, escape(value, {'"': "&quot;"}), style, parent, x, y, w, hgt))

    def _edge_xml(self, pg, e):
        col, dash, ink = LINE[e.kind]
        a, b = pg.nodes[e.src], pg.nodes[e.dst]
        sx = (e.pts[0][0] - a.x) / a.w if a.w else 0.5
        sy = (e.pts[0][1] - a.y) / a.h if a.h else 0.5
        dx = (e.pts[-1][0] - b.x) / b.w if b.w else 0.5
        dy = (e.pts[-1][1] - b.y) / b.h if b.h else 0.5
        style = ("edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;html=1;fontFamily=%s;fontSize=11;fontColor=%s;"
                 "strokeColor=%s;strokeWidth=%g;endArrow=%s;endFill=1;endSize=6;labelBackgroundColor=#FFFFFF;"
                 "exitX=%.4f;exitY=%.4f;exitDx=0;exitDy=0;entryX=%.4f;entryY=%.4f;entryDx=0;entryDy=0;jettySize=auto;"
                 % (FONT, ink, col, e.width, e.arrow, sx, sy, dx, dy))
        dsh = dash if e.dashed is None else e.dashed
        if dsh:
            style += "dashed=1;dashPattern=%s;" % dsh
        interior = e.pts[1:-1]
        geo = '     <mxGeometry relative="1" as="geometry"'
        lab = e.label_text()
        x = 2 * e.lab - 1
        geo += ' x="%.4f"' % x if lab else ""
        geo += ">"
        if lab and (e.loff[0] or e.loff[1]):
            geo += '\n      <mxPoint x="%g" y="%g" as="offset"/>' % (e.loff[0], e.loff[1])
        if interior:
            geo += "\n      <Array as=\"points\">"
            for p in interior:
                geo += '\n       <mxPoint x="%g" y="%g"/>' % p
            geo += "\n      </Array>"
        geo += "\n     </mxGeometry>"
        return ('    <mxCell id="%s" value="%s" style="%s" edge="1" parent="1" source="%s" target="%s">\n%s\n    </mxCell>'
                % (e.id, escape(lab, {'"': "&quot;"}), style, e.src, e.dst, geo))

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_xml())


# ---------------------------------------------------------------- shared frame: title, legend, questions
LEG_W = 880
LEG_H = 104


def frame(pg, title, maps_to, questions=None, q_title="Open questions and assumptions", legend=True, notes_h=None):
    """Title, subtitle, legend and the 'open questions' sticky. Content area: y from 84 to pg.h - LEG_H - 36."""
    pg.text("title", 24, 12, pg.w - 48, 32, "NEXA &#8211; %s" % title, size=22, color="#0F172A", bold=True, meta=True)
    pg.text("subtitle", 24, 46, pg.w - 48, 22,
            "NEXA - first draft, 2026-10-24 &#183; design phase, nothing is fixed &#183; maps to: %s" % maps_to,
            size=12, color="#64748B", meta=True)
    y0 = pg.h - LEG_H - 16
    if legend:
        legend_box(pg, 24, y0)
    qx = 24 + LEG_W + 24
    qw = pg.w - qx - 24
    if questions:
        body = "<br>".join("&#8226; " + q for q in questions)
        n = pg.box("questions", qx, y0, qw, LEG_H, q_title, [body], kind="note", align="left", valign="top",
                   meta=True, shape="rect", size=11)
        n.style_extra = "dashed=1;dashPattern=4 3;fillColor=#FFFBEB;strokeColor=#D97706;"


def legend_box(pg, x, y):
    pg.lane("legend", x, y, LEG_W, LEG_H, "Legend", kind="note", size=11).meta = True
    items = [
        ("box", "engine", "NEXA service (Go, Bun)"),
        ("box", "http", "Edge or outside party"),
        ("box", "grpc", "Sync call (gRPC)"),
        ("box", "cmd", "Kafka command topic"),
        ("box", "fact", "Kafka fact topic"),
        ("box", "data", "Data store"),
        ("box", "fail", "Failure or stop"),
        ("dash", "neutral", "Dashed: new or proposed"),
        ("line", "grpc", "gRPC, a caller waits"),
        ("line", "http", "HTTPS"),
        ("line", "cmd", "Kafka command"),
        ("line", "fact", "Kafka fact"),
        ("line", "log", "Log write, best effort"),
    ]
    colw = 172
    for i, (k, kind, label) in enumerate(items):
        r, c = divmod(i, 5)
        ix = x + 10 + c * colw + (4 if c else 0)
        iy = y + 26 + r * 25
        if k in ("box", "dash"):
            sw = pg.pill("lg.sw%d" % i, ix, iy + 2, 20, 12, "", kind=kind, dashed=(k == "dash"), parent="legend")
            sw.shape = "rect"
            sw.title = ""
        else:
            pg.swatch_line("lg.sw%d" % i, ix, iy + 4, 22, kind, parent="legend")
        t = pg.text("lg.t%d" % i, ix + 24, iy, colw - 28, 20, label, size=10, color="#334155", meta=True, valign="middle", parent="legend")
