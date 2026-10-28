#!/usr/bin/env python3
"""Regenerate every NEXA diagram in diagrams/ from the content modules d*.py.

Usage (from the repo root):  python3 diagrams/tools/gen_diagrams.py [--render]
  - writes diagrams/NN-name.drawio (uncompressed mxfile XML, one page per view)
  - validates every page (overlaps, lines through boxes, label clashes, text fit, decision ids)
  - with --render: exports each page to diagrams/previews/*.png with the draw.io desktop CLI

Hand-edits in draw.io are fine. Re-running this script overwrites the .drawio files, so either
change the generator, or stop using it for a file you now maintain by hand.
"""
import importlib, os, sys, subprocess, shutil, re

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "diagrams")

import validate_diagrams as V

MODULES = ["d01_overview", "d02_brand", "d03_identity", "d04_checkout", "d05_pos", "d06_paylog", "d07_kafka",
           "d08_legacy", "d09_ai", "d10_domainmap", "d11_domains", "d12_infra", "d13_postpaid"]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main():
    decisions = V.load_decision_ids(os.path.join(ROOT, "docs", "architecture.md"))
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    render = "--render" in sys.argv
    total_err = 0
    stats = []
    for m in MODULES:
        if only and not any(o in m for o in only):
            continue
        mod = importlib.import_module(m)
        d = mod.build()
        path = os.path.join(OUT, d.fname)
        d.save(path)
        ferr, cells, edges = V.check_file(path)
        for e in ferr:
            print("  FILE ERROR %s: %s" % (d.fname, e))
        total_err += len(ferr)
        for i, pg in enumerate(d.pages, 1):
            errs, warns, count = V.check_page(pg, decisions)
            tag = "%s p%d %-34s nodes=%2d edges=%2d" % (d.fname, i, pg.name[:34], count, len(pg.edges))
            print(tag + ("  ERRORS=%d" % len(errs) if errs else "  ok") + ("  warns=%d" % len(warns) if warns else ""))
            for e in errs:
                print("    ERR  " + e)
            for w in warns:
                print("    warn " + w)
            total_err += len(errs)
            stats.append((d.fname, i, pg.name, count, len(pg.edges), len(errs), len(warns)))
        if render:
            render_file(d)
    print("TOTAL errors:", total_err)
    return 1 if total_err else 0


def render_file(d):
    drawio = os.environ.get("DRAWIO", "/workspace/drawio-cli/ext/opt/drawio/drawio")
    prev = os.path.join(OUT, "previews")
    os.makedirs(prev, exist_ok=True)
    src = os.path.join(OUT, d.fname)
    base = d.fname[:-len(".drawio")]
    for i, pg in enumerate(d.pages, 1):
        outp = os.path.join(prev, "%s-p%d-%s.png" % (base, i, slug(pg.name)))
        cmd = ["xvfb-run", "-a", drawio, "--no-sandbox", "-x", "-f", "png", "--size", "page", "-p", str(i), "-s", "1",
               "-o", outp, src]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
        if not os.path.exists(outp):
            print("  render failed:", outp, r.stderr[-300:])


if __name__ == "__main__":
    sys.exit(main())
