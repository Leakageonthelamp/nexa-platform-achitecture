#!/usr/bin/env python3
"""Validate generated diagrams: XML structure, ids, overlaps, lines through boxes, label clashes, text fit.

Used by gen_diagrams.py (the geometry comes from the generator's model) and also re-parses every written
.drawio file as a second, independent check of the XML (ids, edge source/target, mxfile structure).
"""
import re, sys, os
import xml.etree.ElementTree as ET
from drawio_lib import text_w, wrap_lines

DEC_RE = re.compile(r"\b([PDO]-\d\d)\b")


def load_decision_ids(arch_md):
    txt = open(arch_md, encoding="utf-8").read()
    ids = set()
    for line in txt.splitlines():
        m = re.match(r"\|\s*([PDO]-\d\d)\s*\|", line)
        if m:
            ids.add(m.group(1))
    return ids


def inter(a, b, eps=0.5):
    return a[0] < b[2] - eps and b[0] < a[2] - eps and a[1] < b[3] - eps and b[1] < a[3] - eps


def contains(outer, inner, eps=0.5):
    return outer[0] - eps <= inner[0] and outer[1] - eps <= inner[1] and inner[2] <= outer[2] + eps and inner[3] <= outer[3] + eps


def seg_hits_rect(p, q, r, pad=0.0):
    x0, y0, x1, y1 = r[0] - pad, r[1] - pad, r[2] + pad, r[3] + pad
    if abs(p[0] - q[0]) < 0.01:  # vertical
        x = p[0]
        lo, hi = sorted((p[1], q[1]))
        return x0 < x < x1 and lo < y1 and hi > y0
    if abs(p[1] - q[1]) < 0.01:
        y = p[1]
        lo, hi = sorted((p[0], q[0]))
        return y0 < y < y1 and lo < x1 and hi > x0
    return True  # diagonal: treat as hit


def seg_cross(s1, s2):
    (a, b), (c, d) = s1, s2
    v1, v2 = abs(a[0] - b[0]) < 0.01, abs(c[0] - d[0]) < 0.01
    if v1 == v2:
        return False
    if v2:
        (a, b), (c, d) = (c, d), (a, b)
    # now a-b vertical, c-d horizontal
    x = a[0]
    y = c[1]
    lo, hi = sorted((a[1], b[1]))
    l2, h2 = sorted((c[0], d[0]))
    return lo + 0.5 < y < hi - 0.5 and l2 + 0.5 < x < h2 - 0.5


def check_page(pg, decisions, max_nodes=25, verbose=True):
    errs, warns = [], []
    N = pg.nodes
    # ids and parents
    for n in N.values():
        if n.parent and n.parent not in N:
            errs.append("node %s: parent %s missing" % (n.id, n.parent))
    # children inside parents
    for n in N.values():
        if n.parent and n.parent in N:
            if not contains(N[n.parent].rect(), n.rect()):
                errs.append("node %s is not inside its container %s" % (n.id, n.parent))
    # overlaps
    ids = list(N)
    for i in range(len(ids)):
        a = N[ids[i]]
        for j in range(i + 1, len(ids)):
            b = N[ids[j]]
            if a.id in pg.ancestors(b) or b.id in pg.ancestors(a):
                continue
            if inter(a.rect(), b.rect()):
                # a container may contain a node that was not declared as child -> flag too
                errs.append("overlap: %s and %s" % (a.id, b.id))
    # text fit
    for n in N.values():
        if n.shape in ("text",):
            raw = n.raw
            wid = n.w - 4
            lines = wrap_lines(raw, wid, n.size, n.bold)
            need = lines * n.size * 1.25 + 2
            if need > n.h + 1:
                errs.append("text %s does not fit: needs %.0fpx, has %.0f" % (n.id, need, n.h))
            continue
        if n.shape.startswith("line:"):
            continue
        if n.container:
            # lane header must fit on one line
            if text_w(n.title, n.size, True) > n.w - 20:
                errs.append("lane title %s too wide" % n.id)
            continue
        wid = n.w - 14 - (2 if n.shape == "pill" else 0)
        if n.shape == "diamond":
            wid = n.w * 0.55
        if n.shape == "cylinder":
            wid = n.w - 14
        pre = 0
        need = 0
        t = n.title or ""
        if n.step is not None:
            pre = text_w(str(n.step), 11, True) + 20
        # title lines
        tl = wrap_lines(t, wid - pre, n.size, True) if t else 0
        need += tl * n.size * 1.25
        for d in n.details:
            sz = n.size - 1 if n.size > 11 else 11
            need += wrap_lines(d, wid, sz, False) * sz * 1.25
        if need > n.h - 4 + 0.5:
            errs.append("box %s text does not fit: needs %.0fpx, has %.0f (w=%d) '%s'" % (n.id, need, n.h - 4, n.w, (n.title or '')[:30]))
    # edges
    segs = []
    lboxes = []
    for e in pg.edges.values():
        if e.src not in N or e.dst not in N:
            errs.append("edge %s: bad endpoint" % e.id)
            continue
        for p, q in zip(e.pts, e.pts[1:]):
            if abs(p[0] - q[0]) > 0.01 and abs(p[1] - q[1]) > 0.01:
                errs.append("edge %s: diagonal segment %s-%s" % (e.id, p, q))
        skip = {e.src, e.dst}
        for n in N.values():
            if n.id in skip or n.container or n.shape in ("text",) or n.meta:
                continue
            for p, q in zip(e.pts, e.pts[1:]):
                if seg_hits_rect(p, q, n.rect()):
                    errs.append("edge %s passes through node %s" % (e.id, n.id))
                    break
        # a segment must not run back through its own endpoints
        for nid in (e.src, e.dst):
            n = N[nid]
            if n.container:
                continue
            inner = (n.x + 2, n.y + 2, n.x + n.w - 2, n.y + n.h - 2)
            for k, (p, q) in enumerate(zip(e.pts, e.pts[1:])):
                if seg_hits_rect(p, q, inner):
                    errs.append("edge %s runs through its own endpoint %s" % (e.id, nid))
                    break
        # edges also must not cut note/meta boxes (legend, questions)
        for n in N.values():
            if n.meta and n.id in ("legend", "questions"):
                for p, q in zip(e.pts, e.pts[1:]):
                    if seg_hits_rect(p, q, n.rect()):
                        errs.append("edge %s passes through %s" % (e.id, n.id))
                        break
        for p, q in zip(e.pts, e.pts[1:]):
            segs.append((e.id, (p, q)))
        lb = e.label_box()
        if lb:
            lboxes.append((e.id, lb))
    # label clashes
    for eid, lb in lboxes:
        for n in N.values():
            if n.container or n.shape == "text" and n.meta is False and False:
                continue
            if n.container:
                continue
            if n.shape.startswith("line:"):
                continue
            if inter(lb, n.rect(), eps=0):
                errs.append("label of %s overlaps node %s" % (eid, n.id))
        for eid2, lb2 in lboxes:
            if eid2 > eid and inter(lb, lb2, eps=0):
                errs.append("labels of %s and %s overlap" % (eid, eid2))
        # label over other edges' segments
        for sid, (p, q) in segs:
            if sid == eid:
                continue
            if seg_hits_rect(p, q, lb):
                warns.append("label of %s sits on edge %s" % (eid, sid))
        # label inside the page
        if lb[0] < 0 or lb[1] < 0 or lb[2] > pg.w or lb[3] > pg.h:
            errs.append("label of %s outside page" % eid)
    # crossings
    cross = 0
    seen = set()
    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            if segs[i][0] == segs[j][0]:
                continue
            if seg_cross(segs[i][1], segs[j][1]):
                key = tuple(sorted((segs[i][0], segs[j][0])))
                cross += 1
                seen.add(key)
    if cross:
        warns.append("%d line crossing(s): %s" % (cross, ", ".join("%s x %s" % k for k in sorted(seen)[:8])))
    # nodes inside page
    for n in N.values():
        if n.x < 0 or n.y < 0 or n.x + n.w > pg.w or n.y + n.h > pg.h:
            errs.append("node %s outside the page" % n.id)
    # node count
    count = sum(1 for n in N.values() if not n.container and not n.meta and n.shape != "text" and not n.shape.startswith("line:"))
    if count > max_nodes:
        warns.append("%d nodes (limit ~%d)" % (count, max_nodes))
    # decision ids exist
    for r in sorted(pg.refs):
        if r not in decisions:
            errs.append("decision id %s not found in architecture.md" % r)
    return errs, warns, count


def check_file(path):
    """Independent check of the written .drawio file."""
    errs = []
    try:
        root = ET.parse(path).getroot()
    except Exception as ex:
        return ["XML parse error: %s" % ex], 0, 0
    if root.tag != "mxfile":
        errs.append("root is not mxfile")
    pages = root.findall("diagram")
    if not pages:
        errs.append("no diagram pages")
    cells_total = edges_total = 0
    for d in pages:
        model = d.find("mxGraphModel")
        if model is None:
            errs.append("page %s: no mxGraphModel (compressed?)" % d.get("name"))
            continue
        ids = {}
        for c in model.iter("mxCell"):
            i = c.get("id")
            if i in ids:
                errs.append("page %s: duplicate id %s" % (d.get("name"), i))
            ids[i] = c
        for i, c in ids.items():
            cells_total += 1
            if c.get("edge") == "1":
                edges_total += 1
                s, t = c.get("source"), c.get("target")
                if not s or not t:
                    errs.append("page %s: edge %s has no source/target" % (d.get("name"), i))
                elif s not in ids or t not in ids:
                    errs.append("page %s: edge %s points to a missing id" % (d.get("name"), i))
            p = c.get("parent")
            if p and p not in ids:
                errs.append("page %s: cell %s parent %s missing" % (d.get("name"), i, p))
    return errs, cells_total, edges_total
