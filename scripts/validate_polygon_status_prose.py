#!/usr/bin/env python3
"""A page's polygon-status headline must not contradict its own frontmatter.

WHY THIS EXISTS. On 2026-09-09 three bulk commits (00f8e72, 433a81a, af85272) bound real
boundaries to 392 subnational polities by editing ONLY their frontmatter. Each of those pages had
been written from one template whose Territorial extent section opened with a headline like

    **Polygon status:** Not yet assigned. No polygon is available in the GeoPackage ...

and every one of those headlines stayed. Measured on c514f8a (2026-09-24), this gate reports 323
live pages whose first statement about their polygon says the opposite of their
`polygon_status`; after that day's correction it reports 0, with an empty baseline. Nothing failed: build_database
reads only the frontmatter, and every other gate reads the database. The wiki is the evidence
the verification pipeline reads, so a page that says "no polygon" while shipping one is a false
statement in the source of truth.

WHAT IT CHECKS (only fixed phrasings, so it cannot drift into judgement):

  The HEADLINE is the first paragraph, inside a `## ` section whose title mentions territory or
  polygon, that opens with a polygon label: `**Polygon status:**`, `**Polygon:**`,
  `**Polygon source.**`, `Polygon status:` and their bold/list variants. A paragraph whose label
  itself says it is superseded, resolved or dated history -- e.g. `**Polygon status (superseded
  2026-09-24, kept as the record of what blocked it):**` -- is not the headline; the repo keeps
  such paragraphs on purpose.

  A. Frontmatter binds a polygon (`assigned`, `proxy`, `estimate`, `polygon_vintage_drift`) and
     the headline says it does not: "not yet assigned", "no polygon is attached/available/
     assigned", "no geometry is attached", "`polygon_status: unassigned`", "Polygon status:
     unassigned/none", "Polygon status is **unassigned**".
  B. Frontmatter is `unassigned` (or has no polygon) and the headline claims a binding:
     "Polygon status: `assigned`/`proxy`/`estimate`".

Retired and superseded pages are skipped: their banner is the live statement. Pages with no
polygon headline are not checked -- a missing headline is not a contradiction.

Known exceptions go in scripts/validate_polygon_status_prose_baseline.txt (`slug  # why`), which
is bidirectional: a baselined page that no longer fails is reported, so the list can only
shrink.

Usage:
  python3 scripts/validate_polygon_status_prose.py [--list]
Exit 1 on any new contradiction or stale baseline line.
"""
import argparse
import glob
import os
import re
import sys

import yaml

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLITIES = os.path.join(REPO, "wiki/polities")
BASELINE = os.path.join(REPO, "scripts/validate_polygon_status_prose_baseline.txt")

BOUND = {"assigned", "proxy", "estimate", "polygon_vintage_drift"}
DEAD = {"retired", "superseded"}

SECTION = re.compile(r"territor|polygon", re.I)
LABEL = re.compile(
    r"^\s*(?:[-*>]\s+)?(?:\*\*\s*)?(Polygon(?:[ _]status|[ _]source)?)\b([^\n]{0,80}?)(?:\*\*|:|\.)", re.I)
# a label that marks its own paragraph as history rather than the current statement
HISTORY_LABEL = re.compile(r"superseded|resolved|historical|record of|previous|former|until|20\d\d-\d\d-\d\d", re.I)
NEGATIVE = re.compile(
    r"not yet assigned"
    r"|no polygon (?:is |was )?(?:yet )?(?:attached|available|assigned)"
    r"|no geometry (?:is |was )?(?:yet )?attached"
    r"|`?polygon_status`?\s*(?::|=|is)\s*`?unassigned"
    r"|polygon status\s*(?::|is)?\s*\**\s*:?\s*\**\s*`?(?:unassigned|none)\b",
    re.I)
POSITIVE = re.compile(r"polygon status:?\**:?\s*\**\s*`(assigned|proxy|estimate)`", re.I)


def split_page(path):
    text = open(path, encoding="utf-8").read()
    if not text.startswith("---\n"):
        return {}, "", 0
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, "", 0
    try:
        fm = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError:
        fm = {}
    # the offset turns a body line number into the file line number an editor shows
    return fm, text[end + 5:], text[:end + 5].count("\n")


def headline(body):
    """(body line number, paragraph text) of the current polygon headline, or None."""
    section, fenced, para, start = "", False, [], 0
    lines = body.split("\n") + [""]
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        if not line.strip() or line.startswith("#"):
            if para and SECTION.search(section):
                text = "\n".join(para)
                m = LABEL.match(para[0])
                if m and not HISTORY_LABEL.search(m.group(2)):
                    return start, text
            para = []
            if line.startswith("## "):
                section = line[3:]
            continue
        if not para:
            start = i
        para.append(line)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="print every page's headline verdict")
    args = ap.parse_args()

    baseline = {}
    if os.path.exists(BASELINE):
        for line in open(BASELINE, encoding="utf-8"):
            slug = line.split("#")[0].strip()
            if slug:
                baseline[slug] = line.strip()

    checked, found = 0, []
    for path in sorted(glob.glob(os.path.join(POLITIES, "*.md"))):
        slug = os.path.basename(path)[:-3]
        if slug.startswith("_"):
            continue
        fm, body, offset = split_page(path)
        if str(fm.get("status")) in DEAD:
            continue
        hl = headline(body)
        if hl is None:
            continue
        checked += 1
        lineno, text = hl
        lineno += offset
        # a phrase the headline QUOTES is being reported, not asserted: syr-1920-1922 records that
        # 'the sentence previously here, "Polygon: Not yet assigned", was already stale'
        text = re.sub(r'"[^"\n]*"|“[^”\n]*”', '""', text)
        pst = str(fm.get("polygon_status") or "")
        src = str(fm.get("polygon_source") or "none")
        if pst in BOUND:
            m = NEGATIVE.search(text)
            if m:
                found.append((slug, lineno, f"frontmatter is `{pst}` ({src} {fm.get('polygon_feature_id')}) "
                                            f"but the headline says {m.group(0)!r}"))
        else:
            m = POSITIVE.search(text)
            if m:
                found.append((slug, lineno, f"frontmatter is `{pst or 'empty'}` but the headline claims "
                                            f"`{m.group(1)}`"))
        if args.list:
            print(f"   {slug:34s} L{lineno}: {pst:12s} {text[:90]!r}")

    new = [f for f in found if f[0] not in baseline]
    stale = sorted(set(baseline) - {f[0] for f in found})
    print(f"{checked} page(s) with a polygon headline checked against their frontmatter; "
          f"{len(found)} contradiction(s), {len(found) - len(new)} baselined")
    for slug, lineno, why in new:
        print(f"   FAIL {slug} L{lineno}: {why}. Put the current binding first and relabel the old "
              f"paragraph `(superseded YYYY-MM-DD, kept as the record of what blocked it)`.")
    for slug in stale:
        print(f"   FAIL baseline line for {slug} no longer matches anything -- delete it: {baseline[slug]}")
    ok = not new and not stale
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
