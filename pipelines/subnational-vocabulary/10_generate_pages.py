#!/usr/bin/env python3
"""Generate polity wiki pages for the subnational admin units a source actually reports.

SUPERSEDED BY pipelines/agent-harness/. Kept as the record of how Japan's 46 prefectures were
generated; do NOT add a country to COUNTRIES below. The dict is the problem: a human decided Japan
needed prefectures and then configured a generator for it, which does not scale past the country in
front of you and learns nothing from the data. In the harness, "we need provinces here" is an
OUTPUT -- stage 0 decides the country's span and container convention once, stage 1 decides per unit
whether an existing polity already IS that territory, and stage 3 authors the page. Run that instead.

WHY A GENERATOR. The subnational compilation carries 431 real admin units across 26 countries
(whep#1000), and the polity table is built FROM the wiki -- one row per page. Hand-writing 431 pages
would take longer than the data took to compile and would drift; generating them keeps the vocabulary
a function of the panel, which is what issue 400's policy says it should be: a reporting unit gets a
row when statistics were collected on it.

THE RAW PANEL IS NEVER COMMITTED. It is read from WHEP_SUBNATIONAL (or the Nextcloud default below),
outside this repo, exactly as the layer-B tools read WHEP_LAYER_B. What lands in git is vocabulary --
pages, containment edges, counts -- never a data row.

WHAT IT REFUSES TO CREATE, which is the part that matters:

  * RESIDUAL BUCKETS. `USA-RESID` ("Other States") is an aggregation bucket, not a territory. A
    container code is an identity; conflating the two silently misattributes data, so any unit whose
    id or name marks it as a residual is skipped and reported.
  * NATIONAL ROWS WEARING A SUBNATIONAL LABEL. Thirteen "countries" in the panel have exactly one
    admin unit, each id'd `<ISO>-NATIONAL` -- Cuba, Peru, Uruguay and ten more. Those are national
    figures sitting in a subnational table; creating polities for them would manufacture thirteen
    fake provinces.
  * ANYTHING WITHOUT A POLYGON FEATURE. A page claiming a boundary it cannot resolve is worse than
    no page.

CONTAINMENT IS EMITTED AS EDGES, one per era of the parent, because a unit outlives any single
national row: a Japanese prefecture spanning 1871-2025 sits inside four successive JPN polities. That
is the whep#51 edge set, and it is why the interval lives on the edge rather than on the unit.

Usage:
  python3 pipelines/subnational-vocabulary/10_generate_pages.py --country Japan [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
WIKI = REPO / "wiki" / "polities"
DB = REPO / "data" / "final" / "polities_database.csv"
GADM = REPO / "data" / "geodata" / "gadm-4.1" / "gadm41_adm1.gpkg"
PANEL = Path(os.environ.get(
    "WHEP_SUBNATIONAL",
    os.path.expanduser("~/Nextcloud/WHEP_ERC 2025/Sources/data_raw/sources_juan/"
                       "whep_production_subnational.parquet")))

# Per-country configuration. Kept explicit rather than inferred: the span of an admin unit is a fact
# about its administration, not about how far the data happens to run, and getting it from the data
# would force a re-span every time an extract grows (issue 308's cost).
COUNTRIES = {
    "Japan": {
        "iso": "JPN",
        "code_prefix": "JPN",
        "unit_noun": "prefecture",
        # The modern prefecture system dates from the 1871 abolition of the han; the 47-prefecture
        # configuration settled in 1888. 1871 is used so the span covers the data (from 1883)
        # without being defined by it.
        "start_year": 1871,
        "end_year": 2025,
        "system_note": ("the modern prefecture system established by the 1871 abolition of the han "
                        "(haihan-chiken), with the present configuration settled in 1888"),
        # GADM spellings that differ from the panel's. Recorded rather than fuzzy-matched so each
        # one is a decision someone can check.
        "name_fixes": {
            "Gumma": "Gunma",        # alternative romanisation of the same prefecture
            "Hyogo": "Hyōgo",        # macron in GADM
            "Nagasaki": "Naoasaki",  # GADM DEFECT: gadm41_adm1 misspells Nagasaki
        },
    },
}

RESIDUAL_MARKERS = ("RESID", "OTHER", "NATIONAL", "UNKNOWN", "TOTAL")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    return re.sub(r"[^a-z]", "", s.encode("ascii", "ignore").decode().lower())


def container_eras(iso: str, lo: int, hi: int) -> list[tuple[str, int, int]]:
    """The successive national rows a unit sits inside, clipped to its own span."""
    import csv as _csv

    with open(DB, newline="", encoding="utf-8") as fh:
        rows = [r for r in _csv.DictReader(fh)
                if r["polity_code"].startswith(iso + "-")
                and r["polity_type"] == "national"
                and r["wiki_status"] not in ("retired", "superseded")]
    out = []
    for r in sorted(rows, key=lambda x: int(x["start_year"])):
        s, t = int(r["start_year"]), int(r["end_year"])
        a, b = max(s, lo), min(t, hi)
        if a < b:
            out.append((r["polity_code"], a, b))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", required=True)
    ap.add_argument("--dry-run", action="store_true")
    A = ap.parse_args()
    cfg = COUNTRIES.get(A.country)
    if not cfg:
        print(f"FAIL: no configuration for {A.country!r}; add one to COUNTRIES")
        return 1
    if not PANEL.exists():
        print(f"SKIP: subnational panel not present at {PANEL}\n"
              f"  set WHEP_SUBNATIONAL to its location (it is never committed to this repo)")
        return 0

    import pandas as pd
    import geopandas as gpd

    df = pd.read_parquet(PANEL, columns=["country_clean", "admin_unit_id", "admin_name_clean",
                                         "admin_level", "year", "indicator"])
    df = df[df.country_clean == A.country]
    if df.empty:
        print(f"FAIL: no rows for {A.country!r} in the panel")
        return 1

    g = gpd.read_file(GADM, columns=["GID_0", "GID_1", "NAME_1"])
    g = g[g.GID_0 == cfg["iso"]].copy()
    # Measured from the attached feature in an equal-area projection, and the centroid in WGS84 so a
    # reader can place the unit on a modern map. Both are required by the "Wiki page requirements"
    # spec in pipelines/pre1961-matching/README.md, which asks for a territory a reader can locate
    # and an approximate km2. They are stated as MEASUREMENTS OF THE POLYGON, never as evidence
    # about the territory -- that distinction is issue 195, and it is why polygon_area_km2 stays
    # undeclared in the frontmatter while the figure appears in the prose.
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # NO leading underscores: itertuples() renames such columns positionally and
        # r._area raises AttributeError -- a trap this repo has hit repeatedly.
        g["featarea"] = g.to_crs("ESRI:54034").area / 1e6
        pt = g.geometry.representative_point()
        g["featlat"], g["featlon"] = pt.y, pt.x
    by_name = {norm(r.NAME_1): (r.GID_1, r.NAME_1, r.featarea, r.featlat, r.featlon)
               for r in g.itertuples()}

    units = (df.groupby("admin_unit_id")
               .agg(name=("admin_name_clean", "first"), y0=("year", "min"),
                    y1=("year", "max"), rows=("year", "size"),
                    inds=("indicator", lambda s: ";".join(sorted(set(s)))))
               .sort_index())

    eras = container_eras(cfg["iso"], cfg["start_year"], cfg["end_year"])
    if not eras:
        print(f"FAIL: no national {cfg['iso']} rows cover {cfg['start_year']}-{cfg['end_year']}")
        return 1

    made, skipped = [], []
    for uid, r in units.iterrows():
        tail = uid.split("-", 1)[1] if "-" in uid else uid
        if any(m in tail.upper() for m in RESIDUAL_MARKERS):
            skipped.append((uid, "residual or national bucket, not a territory"))
            continue
        panel_name = str(r["name"])
        lookup = cfg["name_fixes"].get(panel_name, panel_name)
        hit = by_name.get(norm(lookup))
        if not hit:
            skipped.append((uid, f"no GADM feature matches {panel_name!r}"))
            continue
        gid, gadm_name, feat_area, feat_lat, feat_lon = hit
        code = f"{cfg['code_prefix']}-{tail}-{cfg['start_year']}-{cfg['end_year']}"
        slug = code.lower()
        made.append((code, slug, uid, panel_name, gadm_name, gid, r,
                     feat_area, feat_lat, feat_lon))

    print(f"{A.country}: {len(units)} panel unit(s) -> {len(made)} page(s), {len(skipped)} skipped")
    for uid, why in skipped:
        print(f"  SKIP {uid}: {why}")
    print(f"container eras: " + ", ".join(f"{c}({a}-{b})" for c, a, b in eras))
    if A.dry_run:
        print("\n(dry run: no pages written)")
        return 0

    for code, slug, uid, panel_name, gadm_name, gid, r, feat_area, feat_lat, feat_lon in made:
        note = ""
        if panel_name != gadm_name:
            note = (f"\n\n**Name note.** The panel spells this unit `{panel_name}` and GADM 4.1 "
                    f"spells it `{gadm_name}`."
                    + (" GADM's spelling is a defect, not a variant."
                       if norm(panel_name) != norm(cfg['name_fixes'].get(panel_name, panel_name))
                       else " Both refer to the same unit."))
        cont = "\ncontainer:\n" + "".join(
            f"  - code: {c}\n    start_year: {a}\n    end_year: {b}\n"
            f"    basis: {cfg['unit_noun']} inside {c} for those years\n" for c, a, b in eras)
        page = f"""---
polity_code: {code}
polity_name: {panel_name} ({cfg['unit_noun']} of {A.country})
start_year: {cfg['start_year']}
end_year: {cfg['end_year']}
type: subnational
iso3: {cfg['iso']}
continent: Asia
cow: NA
status: draft
last_ingest: 2026-09-01
sources: [juan-subnational]
polygon_source: gadm-4.1-adm1
polygon_feature_id: {gid}
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []{cont.rstrip()}
---

# {panel_name} ({cfg['unit_noun']} of {A.country})

## Summary

{panel_name}, a {cfg['unit_noun']} of {A.country}. This is a **subnational reporting unit, not a
sovereign state**: `type: subnational` keeps it out of the matcher's family/sovereignty ranking, so
it cannot compete with the national {cfg['iso']} chain.

**Why this entry exists.** The harmonized subnational compilation reports
{cfg['unit_noun']} figures for this unit as `{uid}` — **{int(r['rows']):,} valued rows**,
{int(r['y0'])}–{int(r['y1'])}, covering {r['inds'].replace(';', ', ')}. Under the policy decided on
[issue 400](https://github.com/eduaguilera/whep-polities/issues/400), a reporting unit qualifies for
a polity row when statistics were collected on it. Without this row those figures can only attach to
the national row, which is roughly forty times the territory they measure.{note}

## Territorial extent

**Polygon status:** assigned from `gadm-4.1-adm1` feature `{gid}` ({gadm_name}). GADM 4.1 admin-1
is the present-day boundary; the {cfg['unit_noun']} system has been stable in outline since 1888,
which is why a modern feature is used without an ESTIMATE flag. This is neither a copied proxy nor an
absence — the two cases the wiki-page spec enumerates — so it is stated as a fourth form: a boundary
taken directly from a registered source at this unit's own level.

**Territory description.** {panel_name} covers roughly **{feat_area:,.0f} km2**, centred near
{feat_lat:.2f}°N {feat_lon:.2f}°E, which places it on a modern map of {A.country}. For scale, that is
about {feat_area / 377975 * 100:.1f}% of {A.country}'s land area, and the figure is a **measurement of
the attached polygon**, not an independent statement about the territory.

`polygon_area_km2` is deliberately **left undeclared in the frontmatter**. Declaring it there would
put a number in the column that check A compares against the geometry it was read from, which is
self-referential and cannot be evidence (issue 195). No independently stated area for this unit
exists in this repository, so the measurement appears here in prose, labelled as such.

## Predecessors and successors

None. This unit neither succeeds nor is succeeded by another polity — its relation to the national
row is **containment**, not succession, which is precisely the distinction whep#51 exists to record.

## Sourced claims

- {A.country} is divided into {cfg['unit_noun']}s under {cfg['system_note']}.
- The compilation reports this unit continuously across {int(r['y0'])}–{int(r['y1'])}.

## Decisions

### d-span-follows-the-administration

`{cfg['start_year']}`–`{cfg['end_year']}` follows {cfg['system_note']}, not the data's
{int(r['y0'])}–{int(r['y1'])} extent. A data-driven span would have to be re-spanned every time an
extract grows, and issue 308 records what re-spanning costs: banked verdicts orphaned by span drift.

### d-containment-not-succession

The national relation is expressed as {len(eras)} containment edge(s), one per era of the national
chain, rather than as a `predecessor`. A single parent field could not express it: this unit outlives
every individual national row.
"""
        (WIKI / f"{slug}.md").write_text(page, encoding="utf-8")
    print(f"\nwrote {len(made)} page(s) to {WIKI.relative_to(REPO)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
