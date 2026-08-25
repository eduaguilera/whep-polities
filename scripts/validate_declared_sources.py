#!/usr/bin/env python3
"""Ratchet the OTHER citation channel: the `sources:` list in a polity page's frontmatter.

WHY THIS EXISTS, AND WHY IT IS NOT validate_citations OR validate_page_depth.
`validate_citations.py` proves that every INLINE `](../sources/x.md#anchor)` link resolves to
a real file and a real heading, on the stated ground that "a citation pointing at a file that
does not exist is worse than no citation: it looks like evidence and is not".
`validate_page_depth.py` (issue 19) proves that a data-receiving page is not a CSV-derived
stub. Neither reads the frontmatter key `sources:`, which is the other place a page names its
evidence -- `validate_references.py` merely permits the key -- and NOTHING in the repo reads
it at all. So it was a channel in which a page could name any string it liked and no check
would notice.

MEASURED, 2026-08-17, on main. Issue 19's follow-up asks whether citation-PRESENCE deserves
its own ratchet after FCC-1862-1887 graduated out of the stub ratchet while still carrying
zero `../sources/` citations. The naive form of that ratchet -- "a data-receiving page must
carry an inline citation" -- would have flagged 115 of the 460 data-receiving polities,
14,348 of 189,839 layer-B rows (7.56%), fourteen times the stub ratchet's exposure. It would
also have been almost entirely a false alarm: 113 of those 115 pages DO name sources, in
frontmatter, and the real defect underneath was different and sharper --

  * 146 of the 775 polity pages declared a slug that resolves to NO file under
    `wiki/sources/`. 38 distinct slugs, headed by `gadm-4.1` (46 pages),
    `CShapes` (22, a case variant of the registered `cshapes-2.0`),
    `gadm-4.1-adm0` (23) and `database` (18, which names this database itself).
  * only 3 pages -- and only 2 of the data-receiving ones, NRH-1911-1953 and
    PTIND-1816-1961 -- carried no source evidence of any kind.

The root cause is that two vocabularies collided. `scripts/sources.yaml` registers MACHINE
slugs for polygon binding (`gadm-4.1-adm0`, `cliopatria`, `paine-2024`), `wiki/sources/`
holds READABLE source records under different names (`gadm-4.1.md`, `cliopatria-v0.1.3.md`,
`paine-et-al-2024.md`), and nothing said which vocabulary `sources:` takes. It takes the
readable one -- a citation has to be readable to be checkable -- and wiki/README.md now says
so.

WHAT THIS CHECKS

  A  every slug in a page's `sources:` frontmatter resolves to `wiki/sources/<slug>.md`.
     Unresolvable slugs are baselined BY SLUG, not by page, in
     scripts/validate_declared_sources_baseline.txt: one unregistered source is one piece
     of work (register the page, or correct the slug on the pages naming it), and a
     per-slug baseline is a worklist ordered by exposure rather than 146 lines of noise.
  B  a polity that RECEIVES layer-B data must name evidence SOMEWHERE -- at least one
     inline `../sources/` citation, or at least one declared slug. This arm has NO
     baseline: it was brought to zero in the commit that added this gate (NRH-1911-1953
     and PTIND-1816-1961 were the two), and a page that receives data while naming no
     evidence at all should not be accepted quietly.

     Arm B accepts a declared slug even when that slug is unregistered, on purpose. Eight
     data-receiving pages name ONLY unregistered slugs today -- SER-1918-1945 (573 rows),
     TRS-1947-1954, TTPI-1947-1994, ALK-1867-1959, CZE-1804-1918, BWI-1833-1962,
     SAC-1935-1947, CXR-1946-1958 -- and arm A already reports every one of them through
     the slug they name. Failing them twice, under two baselines, would make the
     unregistered-source worklist harder to read without covering anything more: a page
     that invents a slug is still caught, by arm A.

Row counts for the exposure ordering come from `layerb_data_rows` in
`pipelines/polity-autoimprove/state/territory_basis.csv`, which is derived from the
gitignored, STALE `state/matched_rows.parquet` (issue 243 -- it undercounts SEN/LAO/TCD/
CHL/LBY). As in validate_page_depth, staleness is permissive and never strict: an
undercounted polity reads as 0 rows and drops out of arm B, so it can hide a defect but
never invent one. Arm A does not use row counts at all.

FAILS ON:
  - a page declaring a slug that resolves to nothing and is not baselined
  - a baselined slug that now resolves, or that no page declares any more (delete the
    line -- the whole point is that this list shrinks, and a stale entry silently accepts
    the next page that mistypes that slug)
  - a data-receiving polity whose page names no source at all

ARM D, ADDED 2026-08-25: `polygon_source` must name a slug registered in `scripts/sources.yaml`,
or be exactly `none`. wiki/README.md already states that contract ("slug of a source registered
in scripts/sources.yaml") and `write_feature_index.py` already MEASURES the violations -- and only
prints them. Five pages were outside it: `pry-1811-1870` wrote `polygon_source: ESTIMATE`, a status
word duplicating what its own `polygon_status: unassigned` already said, and four others spelled
"no source" as ``, `null` and `""` against the `none` that eight pages and the template use.

That is a narrower check than the one below, and it is the part of it that IS mechanical: this gate
cannot tell whether a page cites the source it really used, but it can tell that the field naming
the polygon's source names nothing at all.

DELIBERATELY NOT CHECKED: whether the source SUPPORTS the page's claims, and whether the
page cites the source it actually used. `sources: [cshapes-2.0]` on a page whose polygon
came from GADM is a lie this gate cannot see -- arm D only rules out the field being
meaningless, not its being wrong. Nor does it require an inline citation:
requiring one would have flagged 115 pages of which 113 do cite something, and a gate that
is 98% false alarm gets ignored.

Usage:
  python3 scripts/validate_declared_sources.py [--list]
Exit 1 on any of the above.
"""

import argparse
import csv
import glob
import os
import re
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLITIES = os.path.join(REPO, "wiki/polities")
SOURCES = os.path.join(REPO, "wiki/sources")
BASIS = os.path.join(REPO, "pipelines/polity-autoimprove/state/territory_basis.csv")
BASELINE_PATH = os.path.join(REPO, "scripts/validate_declared_sources_baseline.txt")

# The same inline-citation shape validate_citations.py and 00_intake.py's page_stats() use.
CITE = re.compile(r"\]\(\.\./sources/")
# `sources: [a, b]` on one line, which is the form all 772 pages carrying the key use, plus
# the YAML block form, so a page written in the other style is screened rather than skipped.
SOURCES_INLINE = re.compile(r"^sources:\s*\[(.*?)\]\s*$", re.M)
SOURCES_BLOCK = re.compile(r"^sources:\s*$\n((?:\s*-\s*\S+\s*$\n?)+)", re.M)


def load_baseline() -> set:
    """Slugs accepted as unregistered today. Inline comments carry the exposure and the
    diagnosis, which is the useful part of the file, so they are stripped not parsed."""
    if not os.path.exists(BASELINE_PATH):
        return set()
    out = set()
    with open(BASELINE_PATH, encoding="utf-8") as fh:
        for line in fh:
            text = line.split("#", 1)[0].strip()
            if text:
                out.add(text)
    return out


def declared_slugs(text: str) -> list:
    """Source slugs a page's frontmatter names, in order, deduplicated."""
    found = []
    m = SOURCES_INLINE.search(text)
    if m:
        found = [s.strip().strip("\"'") for s in m.group(1).split(",")]
    else:
        m = SOURCES_BLOCK.search(text)
        if m:
            found = [ln.strip().lstrip("-").strip().strip("\"'")
                     for ln in m.group(1).splitlines()]
    out = []
    for s in found:
        if s and s not in out:
            out.append(s)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true",
                    help="print every unregistered slug with its exposure, worst first")
    args = ap.parse_args()

    registered = {os.path.basename(f)[:-3] for f in glob.glob(os.path.join(SOURCES, "*.md"))
                  if not os.path.basename(f).startswith("_")}
    if not registered:
        print(f"FAIL: no source records found under {SOURCES}")
        return 1

    rows_for = {}
    if os.path.exists(BASIS):
        with open(BASIS, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                code = (row.get("polity_code") or "").strip()
                try:
                    n = int((row.get("layerb_data_rows") or "0").strip() or 0)
                except ValueError:
                    n = 0
                if code and n > 0:
                    rows_for[code] = n
    else:
        print(f"FAIL: {BASIS} not found "
              f"(run pipelines/polity-autoimprove/04_territory_basis.py)")
        return 1

    pages = [f for f in sorted(glob.glob(os.path.join(POLITIES, "*.md")))
             if not os.path.basename(f).startswith("_")]   # _template.md is a placeholder
    if not pages:
        print(f"FAIL: no polity pages found under {POLITIES}")
        return 1

    # ---------- D: polygon_source names a registered slug, or exactly `none` ----------
    import re as _re
    import yaml as _yaml
    with open(os.path.join(REPO, "scripts/sources.yaml"), encoding="utf-8") as fh:
        _y = _yaml.safe_load(fh)["sources"]
    poly_slugs = set(_y) if isinstance(_y, dict) else {
        x if isinstance(x, str) else (x.get("slug") or x.get("id")) for x in _y}
    bad_poly = []
    for page in pages:
        fm = open(page, encoding="utf-8").read().split("---", 2)
        if len(fm) < 3:
            continue
        # `[ \t]*`, NOT `\s*`: `\s` matches newlines, so on a page whose field is empty the
        # pattern happily captures the NEXT line and reports it as the value. That produced two
        # phantom violations reading `polygon_feature_id:` before I anchored it.
        m = _re.search(r"^polygon_source:[ \t]*(.*)$", fm[1], _re.M)
        if not m:
            continue
        val = m.group(1).strip()
        if val == "none" or val in poly_slugs:
            continue
        bad_poly.append((os.path.basename(page), val))
    print(f"D. polygon_source vocabulary: {len(pages)} page(s) checked against "
          f"{len(poly_slugs)} registered slug(s) plus `none`; {len(bad_poly)} outside it")
    for name, val in bad_poly[:8]:
        print(f"   FAIL {name}: polygon_source {val!r} names no source in scripts/sources.yaml "
              f"and is not `none`")

    # slug -> [pages, data-receiving pages, layer-B rows]
    unregistered = defaultdict(lambda: [0, 0, 0])
    no_evidence = {}
    for page in pages:
        code = os.path.basename(page)[:-3].upper()
        text = open(page, encoding="utf-8").read()
        slugs = declared_slugs(text)
        for slug in slugs:
            if slug in registered:
                continue
            entry = unregistered[slug]
            entry[0] += 1
            if code in rows_for:
                entry[1] += 1
                entry[2] += rows_for[code]
        if code in rows_for and not slugs and not CITE.search(text):
            no_evidence[code] = (rows_for[code], len(text))

    baseline = load_baseline()
    affected = sum(v[0] for v in unregistered.values())
    print(f"{len(pages)} polity pages, {len(registered)} registered source records, "
          f"{len(rows_for)} data-receiving polities")
    print(f"A. unregistered declared slugs: {len(unregistered)} slug(s) on "
          f"{affected} page reference(s); baseline accepts {len(baseline)}")

    if args.list:
        for slug, (np_, nr, nrows) in sorted(unregistered.items(),
                                             key=lambda kv: (-kv[1][2], -kv[1][0])):
            mark = " " if slug in baseline else "N"
            print(f"  {mark} {slug:50s} pages={np_:4d} data-receiving={nr:4d} "
                  f"rows={nrows:6d}")

    new = sorted(set(unregistered) - baseline)
    print(f"\nUNBASELINED UNREGISTERED SLUGS: {len(new)}")
    for slug in new:
        np_, nr, nrows = unregistered[slug]
        print(f"   FAIL {slug:50s} declared by {np_} page(s) ({nr} data-receiving, "
              f"{nrows:,} layer-B rows) but wiki/sources/{slug}.md does not exist -- "
              f"register the source, or correct the slug on those pages; if it must wait, "
              f"add it to scripts/validate_declared_sources_baseline.txt with the reason")

    gone = sorted(s for s in baseline if s not in unregistered)
    print(f"\nBASELINED SLUGS THAT ARE NO LONGER UNREGISTERED: {len(gone)}")
    for slug in gone:
        why = ("wiki/sources/%s.md now exists" % slug if slug in registered
               else "no page declares it any more")
        print(f"   FAIL {slug:50s} {why} -- delete its line from "
              f"scripts/validate_declared_sources_baseline.txt and say in the commit what "
              f"was registered or corrected")

    print(f"\nB. DATA-RECEIVING PAGES NAMING NO SOURCE AT ALL: {len(no_evidence)}")
    for code, (nrows, nbytes) in sorted(no_evidence.items(), key=lambda kv: -kv[1][0]):
        print(f"   FAIL {code:18s} receives {nrows:,} layer-B rows, {nbytes} bytes, no "
              f"inline ../sources/ citation and no `sources:` frontmatter -- the "
              f"verification pipeline reads this page as evidence and it names none")

    fail = bool(new or gone or no_evidence or bad_poly)
    print(f"\n{'FAIL' if fail else 'PASS'}: {len(new)} unbaselined unregistered slug(s), "
          f"{len(gone)} stale baseline entry(ies), {len(no_evidence)} page(s) naming no "
          f"source at all, {len(bad_poly)} polygon_source value(s) naming nothing")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
