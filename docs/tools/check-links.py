#!/usr/bin/env python3
"""Check every relative Markdown link and #anchor in a repo.

Usage: python3 check-links.py [repo_root]
Exit code 1 when any link is broken.
Rules:
- Inline links [text](target) and reference-style definitions [id]: target are checked.
- Links inside fenced code blocks and inline code spans are ignored.
- http(s):, mailto: and data: targets are skipped (offline check).
- #anchor targets are checked against GitHub-style heading slugs of the target .md file.
"""
import os, re, sys
from urllib.parse import unquote

root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
FENCE = re.compile(r"^\s*(```|~~~)")
INLINE = re.compile(r"`+[^`\n]*`+")
LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)|!\[[^\]]*\]\(([^)\s]+)\)")
REFDEF = re.compile(r"^\s*\[[^\]]+\]:\s*(\S+)")
HEAD = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")

def slug(text, seen):
    t = re.sub(r"`", "", text)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = t.strip().lower()
    t = re.sub(r"[^\w\- ]", "", t, flags=re.UNICODE)
    t = t.replace(" ", "-")
    n = seen.get(t, 0)
    seen[t] = n + 1
    return t if n == 0 else f"{t}-{n}"

_anchor_cache = {}
def anchors(path):
    if path in _anchor_cache:
        return _anchor_cache[path]
    out, seen, fence = set(), {}, False
    with open(path, encoding="utf-8") as f:
        for line in f:
            if FENCE.match(line):
                fence = not fence
                continue
            if fence:
                continue
            m = HEAD.match(line)
            if m:
                out.add(slug(m.group(2), seen))
            for a in re.findall(r'<a\s+(?:name|id)="([^"]+)"', line):
                out.add(a)
    _anchor_cache[path] = out
    return out

broken, total, files = [], 0, 0
for dp, dn, fn in os.walk(root):
    dn[:] = [d for d in dn if d != ".git"]
    for name in fn:
        if not name.endswith(".md"):
            continue
        p = os.path.join(dp, name)
        files += 1
        fence = False
        with open(p, encoding="utf-8") as f:
            for ln, line in enumerate(f, 1):
                if FENCE.match(line):
                    fence = not fence
                    continue
                if fence:
                    continue
                clean = INLINE.sub("", line)
                targets = []
                for m in LINK.finditer(clean):
                    targets.append(m.group(1) or m.group(2))
                m = REFDEF.match(clean)
                if m:
                    targets.append(m.group(1))
                for t in targets:
                    t = t.strip("<>")
                    if re.match(r"^(https?:|mailto:|data:|tel:)", t):
                        continue
                    total += 1
                    path_part, _, frag = t.partition("#")
                    path_part = unquote(path_part)
                    tgt = p if path_part == "" else os.path.normpath(os.path.join(dp, path_part))
                    rel = os.path.relpath(p, root)
                    if not os.path.exists(tgt):
                        broken.append((rel, ln, t, "target missing"))
                        continue
                    if frag:
                        if os.path.isfile(tgt) and tgt.endswith(".md"):
                            if unquote(frag).lower() not in anchors(tgt):
                                broken.append((rel, ln, t, "anchor missing"))
                        elif os.path.isdir(tgt):
                            broken.append((rel, ln, t, "anchor on a directory"))

print(f"checked {files} md files, {total} relative links")
for b in broken:
    print(f"BROKEN {b[0]}:{b[1]} -> {b[2]} ({b[3]})")
print(f"broken: {len(broken)}")
sys.exit(1 if broken else 0)
