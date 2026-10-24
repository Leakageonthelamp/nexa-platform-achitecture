#!/usr/bin/env python3
"""Fail if a Markdown file still uses an old folder name.

Old names: the `*-diagrams/` domain folders, `_refs/`, and the bare `refs/` folder.
Allowed places: docs/CHANGELOG.md (it holds the old-to-new table) and anything under _archive/.
Usage: python3 lint-old-names.py [repo_root]
"""
import os, re, sys
root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
OLD = re.compile(r"[a-z-]+-diagrams/|<domain>-diagrams|\b_refs\b|(?<![\w_.-])refs/")
bad = 0
for dp, dn, fn in os.walk(root):
    dn[:] = [d for d in dn if d not in (".git", "_archive")]
    for f in fn:
        if not f.endswith(".md"):
            continue
        p = os.path.join(dp, f)
        rel = os.path.relpath(p, root)
        if rel == os.path.join("docs", "CHANGELOG.md"):
            continue
        for i, line in enumerate(open(p, encoding="utf-8"), 1):
            m = OLD.search(line)
            if m:
                bad += 1
                print(f"{rel}:{i}: old name '{m.group(0)}'")
print(f"old-name references: {bad}")
sys.exit(1 if bad else 0)
