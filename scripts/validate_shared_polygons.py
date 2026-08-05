#!/usr/bin/env python3
"""No two polities that COEXIST in time may be bound to the same polygon.

Two live rows carrying one polygon means the ground inside it is claimed twice.
Any area-weighted use then double-counts: intersect the polity set against a grid
and the cell is handed to both in full, so a per-hectare rate applied to claimed
territory delivers the cell's quantity twice, and re-aggregating back to a polity
inflates whichever one holds the duplicate.

MEASURED IN THE CONSUMER, which is where it surfaced (eduaguilera/whep#514). The
WHEP R package's embedded copy of this database holds 579 live rows with geometry
and 470 distinct polygons, and TWELVE cross-family pairs coexist while sharing a
polygon. Intersecting its 205 live real polities for 2015 against the 0.5 degree
grid, 451 of 67,691 cells claim more territory than they contain, 12.72 Mha in
excess, worst ratio 2.0000x. The named instance is cell (10.25, 1.75), inside
mainland Rio Muni: GNQ-1968-2025 and STP-1800-2025 were both bound to CShapes 2.0
feature 411, so Equatorial Guinea's polygon was handed to Sao Tome and Principe as
well and each claimed the cell in full.

WHY THIS GATE IS NEW WORK RATHER THAN A DUPLICATE. The defect was injected back
into a copy of this repository at the wiki, the CSV and the GeoPackage together --
STP-1800-2025 rebound to cshapes-2.0/411@1900 with polygon_area_km2 blanked, which
is exactly the state the row shipped in -- and then all 27 validate/crosscheck/
audit gates were run against it. Every one exited 0 and not one named
STP-1800-2025. So did build_database.py --check, write_manifest.py --check and
write_faostat_area_map.py --check. The suite is blind to this, for reasons that are
individually defensible:

  validate_polygons          compares MEASURED against RECORDED area, and the row
                             recorded none. That is the 76% blind spot its own
                             docstring names.
  validate_spatial_containment reports a polity holding >=3 contemporaneous
                             polities of other families. Two identical polygons
                             contain each other and nothing else, so the pair sits
                             two below the threshold -- the single-swallow blind
                             spot that gate documents, in its extreme form.
  validate_family_areas      compares a period against its own FAMILY median, and
                             STP has one row, so there is no median to be out of
                             scale with.
  validate_polygon_period_fit / _binding_determinism
                             ask whether a binding resolves to the right STEP of
                             the source it names. 411@1900 resolves cleanly and
                             deterministically; it is simply the wrong country.
  build_database --check      compares the artefacts against the wiki. When the
                             wiki is what is wrong, they agree.

Nothing asked the one question that settles it: does any OTHER live polity already
hold this polygon?

TWO SIGNALS, because a binding and a geometry can each be wrong without the other:

  A  BINDING   two coexisting live rows declaring the same (polygon_source,
               polygon_feature_id, polygon_feature_year). Reads the CSV only, so it
               fires on a wiki edit before any polygon is fetched or attached, and
               names the field to change.
  B  GEOMETRY  two coexisting live rows whose polygons are geometrically the same,
               measured as intersection-over-union above --identical. Catches what A
               cannot: the same territory reached through two different sources, or
               through `constructed`, where the declared bindings differ and the
               ground does not.

WHAT IS LEGITIMATE AND DELIBERATELY NOT REPORTED. Sharing a polygon is normal when
the rows do NOT coexist: successive periods of one territory that saw no boundary
change are bound to the same feature on purpose, and there are 173 such pairs today.
A further 19 shared-polygon pairs are cross-family and sequential -- a successor
reusing its predecessor's step -- which is a real error class, and the one
validate_polygon_period_fit exists for; it is not re-litigated here. This gate asks
only about rows whose spans OVERLAP, where no reading makes two claims on one piece
of ground correct.

BOUNDARY OF WHAT THIS GATE FIXES. It does not assert that a cell's claimed
territory never exceeds the cell. It cannot, and pretending otherwise would be the
same silent renormalisation that hid this defect: 188 coexisting live pairs overlap
by more than 1 km2 in 2015, totalling 331,429 km2, and the large ones are history
and dispute rather than mis-binding -- ESH-1975-2025 / MAR-1979-2025 267,078 km2
(Western Sahara), SAU-1924-2025 / YEM-1990-2025 29,918 km2 (the Rub al Khali
frontier), ESP-1800-2025 / ICN-1800-2025 7,027 km2 and CHN-1950-2025 /
HKG-1842-2025 889 km2 (a sub-polity inside its parent's polygon). Deciding which
row owns that ground is a territorial judgement and belongs in an issue, not in a
threshold here.

Usage:
  python3 scripts/validate_shared_polygons.py [--identical 0.9999]
"""
import argparse
import csv
import hashlib
import os
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(REPO, "data/final/polities_database.csv")
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")
FAOSTAT_MAP = os.path.join(REPO, "data/final/faostat_area_polity_map.csv")
EQUAL_AREA = "ESRI:54034"
DEAD_STATUS = ("retired", "superseded")

# The twelve cross-family pairs that DO coexist while sharing a polygon in the
# consumer's embedded copy, measured on WHEP's data/polities.rda at 603 rows. Every
# one is resolved in this repository already -- by rebinding one side, or by retiring
# it so it can never receive data -- and each is pinned by name so a regression is
# reported as a named historical instance rather than as an anonymous new finding.
#
# Pinned as pairs rather than as expected resolutions on purpose. Retiring a row is a
# legitimate resolution and un-retiring it is a legitimate change, and either way
# signals A and B decide whether the pair is a defect TODAY; the pin's job is to name
# it when it is. What the pin does assert unconditionally is that both codes still
# exist, so a pin cannot go quietly inert by referring to a row that has been renamed
# away.
REGRESSION_PAIRS = frozenset({
    # The pair issue 514 was filed for: Equatorial Guinea's CShapes feature 411 handed
    # to Sao Tome and Principe, 250 km offshore, for the whole 1800-2025 span. Fixed
    # here on 2026-07-24 by binding STP to GADM 4.1 adm0 `STP` (1,002 km2) as a proxy.
    ("GNQ-1968-2025", "STP-1800-2025"),
    ("GNQ-1886-1968", "STP-1800-2025"),
    # San Marino carrying Albania's polygon, 470x too large -- validate_polygons check A
    # found this one, because SMR happened to record an area.
    ("ALB-1913-2025", "SMR-1800-2025"),
    # Modern Djibouti duplicated as DJI-1886-2025 and FRS-1977-2025 on one polygon.
    ("DJI-1886-2025", "FRS-1977-2025"),
    # Colonial Angola on the same feature as the modern row that outlives it.
    ("AGO-1816-2025", "ANG-1905-1975"),
    # Indonesia carrying India's polygon, in two period pairs.
    ("IDN-1800-1889", "IND-1800-1893"),
    ("IDN-1889-1945", "IND-1914-1937"),
    # Iran bound to Cliopatria's "United States of America" -- a mis-binding of
    # plausible SIZE (1,586,287 km2 against 1,621,564), so no area check could see it.
    ("IRN-1800-1828", "USA-1803-1848"),
    # Two prefixes for Morocco, overlapping 1956-1958 on one polygon.
    ("MAR-1911-1958", "MOR-1956-1958"),
    # Northern Nigeria on Norway's feature -- the same 4,000 km error the succession
    # gate found from the other direction.
    ("NNI-1904-1913", "NOR-1800-2025"),
    # Ottoman Empire and Turkey, two prefixes for one state, on one CShapes feature.
    ("OTT-1886-1908", "TUR-1800-1913"),
    ("OTT-1908-1912", "TUR-1800-1913"),
})

# Coexisting pairs that share a polygon ON PURPOSE. Empty, and there is currently no
# case for one: two live rows on one polygon double-count by construction, so an
# entry here would have to argue that the double count is wanted. frozenset rather
# than a bare literal because `{}` is a DICT and set arithmetic on it raises
# TypeError -- see the note in selftest_gates.check_every_gate_runs_in_ci.
BASELINE_SHARED = frozenset()


def coexist(a: dict, b: dict) -> bool:
    """Spans that overlap. `end_year` is EXCLUSIVE, so a shared transition year --
    one row ending where the next begins -- is not coexistence."""
    return (
        a["start_year"] < b["end_year"] and b["start_year"] < a["end_year"]
    )


def read_rows() -> list:
    with open(CSV, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    live = []
    for r in rows:
        if (r.get("wiki_status") or "") in DEAD_STATUS:
            continue
        try:
            r["start_year"] = int(r["start_year"])
            r["end_year"] = int(r["end_year"])
        except (TypeError, ValueError):
            continue
        live.append(r)
    return live


def faostat_reach() -> dict:
    """Which FAOSTAT area codes reach each polity, so a finding says whether a
    consumer can actually see it. A latent defect and a live one need different
    urgency and the numbers do not distinguish them."""
    reach = defaultdict(set)
    if not os.path.exists(FAOSTAT_MAP):
        return reach
    with open(FAOSTAT_MAP, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            code = (r.get("polity_code") or "").strip()
            if code:
                reach[code].add((r.get("area_code") or "").strip())
    return reach


def describe(pair: tuple, reach: dict) -> str:
    tags = []
    for code in pair:
        n = len(reach.get(code, ()))
        how = f"FAOSTAT-mapped via {n} area code(s)" if n else "not FAOSTAT-mapped"
        tags.append(f"{code} ({how})")
    return " and ".join(tags)


def signal_binding(live: list) -> set:
    """Two coexisting live rows declaring the same source, feature and year."""
    by_key = defaultdict(list)
    for r in live:
        fid = (r.get("polygon_feature_id") or "").strip()
        if not fid:
            continue
        key = (
            (r.get("polygon_source") or "").strip(),
            fid,
            (r.get("polygon_feature_year") or "").strip(),
        )
        by_key[key].append(r)
    found = {}
    for key, rs in by_key.items():
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                if coexist(rs[i], rs[j]):
                    pair = tuple(sorted((rs[i]["polity_code"], rs[j]["polity_code"])))
                    found[pair] = key
    return found


def signal_geometry(live: list, threshold: float) -> dict:
    """Two coexisting live rows whose polygons are the same ground.

    Exact duplicates are found by hashing the WKB, which costs nothing and is what a
    feature copied onto two rows produces. Near-duplicates -- the same territory
    reached through two sources, so the vertices differ but the ground does not --
    need a measurement, so intersecting candidate pairs are scored by
    intersection-over-union in an equal-area projection.
    """
    import geopandas as gpd

    g = gpd.read_file(GPKG)
    g = g[~g.geometry.isna() & ~g.geometry.is_empty].copy()
    spans = {
        r["polity_code"]: {"start_year": r["start_year"], "end_year": r["end_year"]}
        for r in live
    }
    g = g[g.polity_code.isin(spans)].copy()

    found = {}
    # Exact: identical serialised geometry.
    by_hash = defaultdict(list)
    for code, geom in zip(g.polity_code, g.geometry):
        by_hash[hashlib.sha256(geom.wkb).hexdigest()].append(code)
    for codes in by_hash.values():
        for i in range(len(codes)):
            for j in range(i + 1, len(codes)):
                if coexist(spans[codes[i]], spans[codes[j]]):
                    found[tuple(sorted((codes[i], codes[j])))] = 1.0

    # Near: same ground, different vertices. buffer(0) heals self-intersections that
    # would otherwise make .area unreliable, as in validate_spatial_containment.
    eq = g.to_crs(EQUAL_AREA).copy()
    eq["geometry"] = eq.geometry.buffer(0)
    eq["area_km2"] = eq.geometry.area / 1e6
    area = dict(zip(eq.polity_code, eq.area_km2))
    geo = dict(zip(eq.polity_code, eq.geometry))
    pairs = gpd.sjoin(
        eq[["polity_code", "geometry"]],
        eq[["polity_code", "geometry"]],
        how="inner",
        predicate="intersects",
    )
    for a, b in zip(pairs.polity_code_left, pairs.polity_code_right):
        if a >= b:
            continue
        key = (a, b)
        if key in found:
            continue
        if not coexist(spans[a], spans[b]):
            continue
        smaller = min(area[a], area[b])
        if smaller <= 0 or max(area[a], area[b]) / smaller > 1.01:
            continue  # too different in size to be the same ground
        union = geo[a].union(geo[b]).area
        if union <= 0:
            continue
        iou = geo[a].intersection(geo[b]).area / union
        if iou >= threshold:
            found[key] = iou
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--identical",
        type=float,
        default=0.9999,
        help="intersection-over-union above which two polygons are the same ground",
    )
    args = ap.parse_args()

    live = read_rows()
    reach = faostat_reach()
    codes = {r["polity_code"] for r in live}
    all_codes = set()
    with open(CSV, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            all_codes.add(r["polity_code"])

    problems = []

    binding = signal_binding(live)
    print(f"{len(live)} live polities; {len(binding)} coexisting pair(s) declaring "
          f"one polygon binding")
    for pair, key in sorted(binding.items()):
        if pair in BASELINE_SHARED:
            print(f"  BASELINED {pair[0]} / {pair[1]} both declare {key}")
            continue
        problems.append(
            f"SHARED BINDING {pair[0]} / {pair[1]} both declare "
            f"polygon_source={key[0]!r} polygon_feature_id={key[1]!r} "
            f"polygon_feature_year={key[2]!r}, and their spans overlap — "
            f"{describe(pair, reach)}"
        )

    geometry = {}
    if os.path.exists(GPKG):
        try:
            geometry = signal_geometry(live, args.identical)
        except ImportError as exc:
            problems.append(
                f"geopandas unavailable ({exc}), so signal B did not run — a shared "
                f"polygon reached through two different sources would go unreported"
            )
    else:
        problems.append(f"{GPKG} missing, so signal B did not run")
    print(f"{len(geometry)} coexisting pair(s) whose polygons are the same ground "
          f"(IoU >= {args.identical})")
    for pair, iou in sorted(geometry.items()):
        if pair in BASELINE_SHARED:
            print(f"  BASELINED {pair[0]} / {pair[1]} IoU {iou:.6f}")
            continue
        problems.append(
            f"SHARED POLYGON {pair[0]} / {pair[1]} occupy the same ground "
            f"(IoU {iou:.6f}) while their spans overlap — {describe(pair, reach)}"
        )

    # Bidirectional arm: a baselined pair that no longer shares must be removed, or
    # the baseline drifts into a licence nobody re-checks.
    observed = set(binding) | set(geometry)
    for pair in sorted(BASELINE_SHARED - observed):
        problems.append(
            f"{pair[0]} / {pair[1]} is baselined as a deliberate shared polygon but no "
            f"longer shares one — remove it from BASELINE_SHARED"
        )

    # ---------- the regression pins ----------
    print(f"\nregression pins: {len(REGRESSION_PAIRS)} pair(s) that shared a polygon "
          f"in the consumer's embedded copy")
    for pair in sorted(REGRESSION_PAIRS):
        missing = [c for c in pair if c not in all_codes]
        if missing:
            problems.append(
                f"pinned pair {pair[0]} / {pair[1]} names {missing}, which is not in "
                f"the database — the pin cannot fail, so update it deliberately "
                f"rather than leaving it inert"
            )
            continue
        if pair in observed:
            problems.append(
                f"REGRESSION {pair[0]} / {pair[1]} shares a polygon again — this is a "
                f"pinned historical defect (whep#514)"
            )
            continue
        dead = [c for c in pair if c not in codes]
        verb = "receives" if len(dead) == 1 else "receive"
        how = f"resolved: {', '.join(dead)} no longer {verb} data" if dead \
            else "resolved: distinct polygons"
        print(f"  {pair[0]} / {pair[1]} — {how}")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        print("\n  Two live rows on one polygon claim the same ground twice, and a "
              "crosswalk that renormalises each cell to sum to 1 absorbs it into a "
              "plausible-looking split rather than surfacing it.")
        return 1

    print("\nPASS: no two coexisting live polities share a polygon, and every pinned "
          "historical pair is still resolved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
