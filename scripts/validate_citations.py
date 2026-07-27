#!/usr/bin/env python3
"""Validate every wiki source citation resolves to a real source and heading.

The wiki is the database's source of truth, and its authority rests on
citations of the form

    [biger-1995 §ghana](../sources/biger-1995.md#ghana)

A citation pointing at a file that does not exist, or an anchor that no heading
produces, is worse than no citation: it looks like evidence and is not. That
risk is highest when pages are documented at scale — by a person or an agent —
so this check is deterministic and gates CI.

Anchors follow the repo's GitHub+Obsidian rule (wiki/README.md): the anchor is
the heading text lowercased with non-alphanumerics collapsed to hyphens, so a
heading `## Key dates` yields `#key-dates`.

Usage:
  python3 scripts/validate_citations.py [--fix-report]
Exit 1 if any citation is unresolvable.
"""
import os, re, sys, glob, argparse, collections

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(REPO, "wiki/sources")
POLITIES = os.path.join(REPO, "wiki/polities")

ap = argparse.ArgumentParser()
ap.add_argument("--fix-report", action="store_true",
                help="group failures by target so they can be fixed in batches")
A = ap.parse_args()


def anchors_for(path):
    """Anchors a markdown file's headings produce, per the repo's convention."""
    out = set()
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^#{1,6}\s+(.*?)\s*$", line)
        if not m: continue
        text = m.group(1)
        text = re.sub(r"[`*_\[\]()]", "", text)            # strip inline markup
        slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
        if slug: out.add(slug)
    return out


# every source file and the anchors it offers
source_anchors = {}
for f in glob.glob(os.path.join(SOURCES, "*.md")):
    source_anchors[os.path.basename(f)] = anchors_for(f)

CITE = re.compile(r"\]\(\.\./sources/([^)#]+\.md)(?:#([^)]+))?\)")
bad_file, bad_anchor, total = [], [], 0
pages = [f for f in sorted(glob.glob(os.path.join(POLITIES, "*.md")))
         if not os.path.basename(f).startswith("_")]   # _template.md holds deliberate placeholders
for page in pages:
    txt = open(page, encoding="utf-8").read()
    for m in CITE.finditer(txt):
        total += 1
        fname, anchor = m.group(1), m.group(2)
        rel = os.path.relpath(page, REPO)
        if fname not in source_anchors:
            bad_file.append((rel, fname, anchor))
        elif anchor and anchor not in source_anchors[fname]:
            bad_anchor.append((rel, fname, anchor))

print(f"{len(source_anchors)} source files; {total:,} citations across "
      f"{len(pages)} polity pages")
print(f"\nUNRESOLVABLE SOURCE FILE: {len(bad_file)}")
for rel, f, a in bad_file[:25]:
    print(f"   FAIL {rel:44s} -> {f}{'#'+a if a else ''}  (no such source)")
print(f"\nUNRESOLVABLE ANCHOR: {len(bad_anchor)}")
if A.fix_report:
    by = collections.Counter((f, a) for _, f, a in bad_anchor)
    for (f, a), n in by.most_common(30):
        print(f"   FAIL {f}#{a}  ({n} page(s))")
else:
    for rel, f, a in bad_anchor[:25]:
        print(f"   FAIL {rel:44s} -> {f}#{a}  (no heading produces this anchor)")

fail = bool(bad_file or bad_anchor)
print(f"\n{'FAIL' if fail else 'PASS'}: {len(bad_file)} missing source(s), "
      f"{len(bad_anchor)} missing anchor(s)")
sys.exit(1 if fail else 0)
