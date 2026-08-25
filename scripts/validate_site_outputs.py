#!/usr/bin/env python3
"""Check that site/ still describes the database it is generated from.

`site/build_wiki.sh` trims and simplifies the master GeoPackage for in-browser display, and
`.github/workflows/pages.yml` DEPLOYS `site/**` whenever it changes. So `site/` is published
output -- and until this gate existed, nothing compared it to the database at all. The word
`site/` appeared in exactly one workflow, the one that publishes it.

WHAT THAT COST, measured on 2026-08-10 (issue 146):

    site/polities.geojson last regenerated   2026-06-11
    features it carried                      561
    live polities with geometry               681
    live codes missing from the site         194
    retired/superseded polities DRAWN          35

Two independent defects in one file, which is why one check is not enough:

  1. STALE. Two months of polygon work -- including every geometry repair, the s2 fixes, and
     four new polities -- never reached the site. A viewer looking at the map was reading June.

  2. WITHDRAWN ROWS WERE DRAWN. `build_wiki.sh` converted the whole GeoPackage, and the
     GeoPackage carries geometry for dead rows too. `index.html` reads `wiki_status` for the
     colour legend and the status badge but never FILTERS on it, so `ARG-1800-2025`
     (superseded) drew Argentina a second time over ARG's real periods, and three retired
     Canadas drew over Canada. The map claimed the same ground twice for a reason that has
     nothing to do with territory. Nobody would see this by reading either file: the CSV is
     correct, the GeoPackage is correct, and the defect is in what the converter chose to keep.

THE CONTRACT, asserted rather than described:

    A. site/polities.csv is byte-identical to data/final/polities_database.csv (it is a `cp`)
    B. site/polities.geojson holds EXACTLY the live rows carrying polygonal geometry
    C. no feature in site/polities.geojson is retired or superseded

B is an equality, not a subset in either direction, so it catches both directions of drift:
a stale site (missing live codes) and a site built from a newer database than the committed
one (codes the database no longer has).

Geometry is deliberately NOT compared. `build_wiki.sh` simplifies rings to 80 points, drops
parts under 0.1 square degrees and splits antimeridian polygons, all on purpose -- comparing
coordinates would fail on every run and teach people to ignore this. What must not drift is
WHICH polities the site claims to show.

Usage:
  python3 scripts/validate_site_outputs.py
"""
from __future__ import annotations

import csv
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_CSV = os.path.join(REPO, "data/final/polities_database.csv")
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")
SITE_CSV = os.path.join(REPO, "site/polities.csv")
SITE_GEOJSON = os.path.join(REPO, "site/polities.geojson")
SITE_PRE1961 = os.path.join(REPO, "site/pre1961")

DEAD = ("retired", "superseded")
REBUILD = "  rebuild: bash site/build_wiki.sh"


def live_with_geometry() -> set:
    """Codes the site is expected to draw: live rows whose GeoPackage geometry is polygonal."""
    import warnings

    warnings.filterwarnings("ignore")
    import geopandas as gpd

    g = gpd.read_file(GPKG)
    g = g[g.geometry.notna() & ~g.geometry.is_empty]
    g = g[~g.wiki_status.astype(str).str.strip().isin(DEAD)]
    return set(g.polity_code)


def dead_codes_in_pre1961() -> list:
    """site/pre1961/** is TRACKED and deployed, and is copied wholesale from
    data/compiled/pre1961, which is GITIGNORED and produced by pipelines/pre1961-matching.

    That combination is how a fixed matcher fails to reach the published site: the R matcher
    gained its dead-status filter in issue 16, but nothing regenerates the compiled directory,
    so the deployed files kept attributing pre-1961 production to polities that had been
    retired or superseded. Measured on 2026-08-18 before this check existed: 23 dead codes
    across 138 files, e.g. ARG-1800-2025 in 76 of them, BRA-1800-2025 in 67.

    A reader of the site cannot tell -- the codes look like any other, and every gate that
    knows about dead rows was looking at polities.geojson, which is built from a different
    path and was clean throughout.
    """
    if not os.path.isdir(SITE_PRE1961):
        return []
    dead = set()
    with open(DB_CSV, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if (r.get("wiki_status") or "") in DEAD:
                dead.add(r["polity_code"])
    if not dead:
        return []
    found = {}
    for root, _dirs, files in os.walk(SITE_PRE1961):
        for name in files:
            path = os.path.join(root, name)
            try:
                text = open(path, encoding="utf-8").read()
            except (OSError, UnicodeDecodeError):
                continue
            for code in dead:
                if code in text:
                    found.setdefault(code, set()).add(name)
    # The mirror-image failure: build_wiki.sh does `rm -rf site/pre1961` and THEN copies, with
    # `|| true` on every cp. If data/compiled/pre1961 exists but is empty or partial -- a failed
    # or interrupted match.R run -- the tracked directory is emptied and the copies silently do
    # nothing, and a dead-code scan of an empty directory passes. So assert the deployed set is
    # still there. 138 files are tracked today; the two index files plus a non-empty by_item/ is
    # the shape, and checking the shape rather than the count leaves room for the item list to
    # change legitimately.
    out = []
    for name in ("summary_by_polity.json", "by_item_index.json"):
        if not os.path.exists(os.path.join(SITE_PRE1961, name)):
            out.append(
                f"site/pre1961/{name} is missing while the directory exists. build_wiki.sh "
                f"deletes this directory before copying and ignores copy failures, so an empty "
                f"or partial data/compiled/pre1961 silently empties the deployed set. "
                f"Regenerate it (Rscript pipelines/pre1961-matching/match.R) before rebuilding"
            )
    by_item = os.path.join(SITE_PRE1961, "by_item")
    if os.path.isdir(by_item) and not [f for f in os.listdir(by_item) if f.endswith(".json")]:
        out.append(
            "site/pre1961/by_item is empty while the directory exists — the deployed per-item "
            "files were removed without being replaced (same cause as above)"
        )
    for code in sorted(found):
        files = found[code]
        out.append(
            f"site/pre1961 attributes data to {code}, which is retired or superseded — "
            f"{len(files)} file(s), e.g. {sorted(files)[0]}. The compiled directory it is "
            f"copied from is gitignored, so regenerate it "
            f"(Rscript pipelines/pre1961-matching/match.R) and rerun site/build_wiki.sh"
        )
    return out


def main() -> int:
    for path in (DB_CSV, GPKG, SITE_CSV, SITE_GEOJSON):
        if not os.path.exists(path):
            print(f"FAIL: {os.path.relpath(path, REPO)} missing")
            return 2

    problems = []
    problems.extend(dead_codes_in_pre1961())

    # A ------------------------------------------------------------------------------------
    with open(DB_CSV, encoding="utf-8") as fh:
        master = fh.read()
    with open(SITE_CSV, encoding="utf-8") as fh:
        shipped = fh.read()
    if master.replace("\r\n", "\n") != shipped.replace("\r\n", "\n"):
        m, s = len(master.splitlines()), len(shipped.splitlines())
        problems.append(
            f"site/polities.csv differs from the master CSV ({s} lines vs {m}) -- it is a "
            f"straight copy, so any difference means the site was built from another database"
        )

    # B and C -----------------------------------------------------------------------------
    with open(SITE_GEOJSON, encoding="utf-8") as fh:
        geo = json.load(fh)
    feats = geo.get("features", [])
    shown, withdrawn = set(), []
    for f in feats:
        props = f.get("properties") or {}
        code = props.get("polity_code")
        if code:
            shown.add(code)
        if (props.get("wiki_status") or "").strip() in DEAD:
            withdrawn.append(code)

    expected = live_with_geometry()
    missing = sorted(expected - shown)
    extra = sorted(shown - expected)

    print(f"site/polities.geojson features: {len(feats)}")
    print(f"live polities with geometry:     {len(expected)}")
    print(f"missing from the site:           {len(missing)}")
    print(f"present but not expected:        {len(extra)}")
    print(f"retired/superseded drawn:        {len(withdrawn)}")

    if missing:
        problems.append(
            f"{len(missing)} live polities with geometry are not in site/polities.geojson, "
            f"e.g. {', '.join(missing[:5])} -- the site is behind the database"
        )
    if extra:
        problems.append(
            f"{len(extra)} features are not live polities with geometry, e.g. "
            f"{', '.join(extra[:5])} -- the site is ahead of, or diverged from, the database"
        )
    if withdrawn:
        problems.append(
            f"{len(withdrawn)} retired/superseded polities are drawn on the map, e.g. "
            f"{', '.join(sorted(c for c in withdrawn if c)[:5])} -- index.html colours by "
            f"wiki_status but does not filter on it, so each one is rendered over the rows "
            f"that replaced it"
        )

    # D ------------------------------------------------------------------------------------
    # THE PAGE COPIES DRIFTED FOR SIX DAYS WITHOUT THIS ARM (added 2026-08-24, issue 554).
    # `site/build_wiki.sh` copies `wiki/polities/*.md` and `wiki/sources/*.md` into `site/wiki/`
    # verbatim, and `pages.yml` publishes `site/**`. So the copies are published output and the
    # same argument as arm A applies to them: a straight copy that differs means the site is
    # describing a different wiki.
    #
    # Arms A-C compared the CSV and the geojson and nothing looked at the pages, so when
    # 9dc37c0 (2026-08-18) added prose to 45 polity pages, the site kept serving the old text
    # and every gate stayed green. It surfaced only because adding two polities forced a site
    # rebuild, which then showed 45 unrelated files changing.
    #
    # Byte comparison rather than mtime: the copy is `cp`, so equality is the whole contract,
    # and an mtime check would fire on any checkout.
    # `wiki/README.md` is copied too and was NOT covered by the loop below, which walks only the
    # two subdirectories. Found on 2026-08-25: a PR edited `wiki/README.md` to state the area
    # convention (issue 569), every gate stayed green, and `site/wiki/README.md` kept serving the
    # old text -- the same failure this arm was written for, one directory up. It surfaced the same
    # way too, when an unrelated rebuild showed the file changing.
    _src_readme = os.path.join(REPO, "wiki/README.md")
    _dst_readme = os.path.join(REPO, "site/wiki/README.md")
    if os.path.exists(_src_readme):
        if not os.path.exists(_dst_readme):
            problems.append("site/wiki/README.md is missing -- run bash site/build_wiki.sh")
        else:
            with open(_src_readme, "rb") as fh_a, open(_dst_readme, "rb") as fh_b:
                same = fh_a.read() == fh_b.read()
            print(f"site/wiki/README.md: {'matches' if same else 'STALE'}")
            if not same:
                problems.append(
                    "site/wiki/README.md differs from wiki/README.md. It is the page that documents "
                    "the schema every other page is written against, so a stale copy misdescribes "
                    "all of them" + REBUILD)

    for sub in ("polities", "sources"):
        src_dir = os.path.join(REPO, "wiki", sub)
        dst_dir = os.path.join(REPO, "site", "wiki", sub)
        if not os.path.isdir(src_dir):
            continue
        if not os.path.isdir(dst_dir):
            problems.append(f"site/wiki/{sub}/ is missing entirely -- run bash site/build_wiki.sh")
            continue
        src = {n for n in os.listdir(src_dir) if n.endswith(".md")}
        dst = {n for n in os.listdir(dst_dir) if n.endswith(".md")}
        for n in sorted(src - dst):
            problems.append(f"wiki/{sub}/{n} has no copy in site/wiki/{sub}/ -- the site is behind")
        for n in sorted(dst - src):
            problems.append(f"site/wiki/{sub}/{n} has no source page -- the site is ahead, or a "
                            f"page was renamed and the old copy left behind")
        stale = []
        for n in sorted(src & dst):
            with open(os.path.join(src_dir, n), encoding="utf-8") as fh:
                a = fh.read().replace("\r\n", "\n")
            with open(os.path.join(dst_dir, n), encoding="utf-8") as fh:
                b = fh.read().replace("\r\n", "\n")
            if a != b:
                stale.append(n)
        if stale:
            problems.append(
                f"{len(stale)} page(s) in site/wiki/{sub}/ differ from wiki/{sub}/, e.g. "
                f"{', '.join(stale[:5])} -- the copies are `cp`d verbatim, so any difference "
                f"means the published page is not the one in the repository"
            )
        print(f"site/wiki/{sub}: {len(src & dst)} copies compared, {len(stale)} stale, "
              f"{len(src - dst)} missing, {len(dst - src)} orphaned")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        print(f"\n{REBUILD}")
        return 1

    print("\nPASS: site/ shows exactly the live polities that carry geometry")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
