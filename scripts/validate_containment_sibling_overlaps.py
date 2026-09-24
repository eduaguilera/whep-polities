#!/usr/bin/env python3
"""Two members of one container may not cover the same ground in the same years.

WHY THIS EXISTS. `data/final/polity_containment.csv` says what sits inside what, and the natural
use of it is to SUM a container's members: the regions of Italy add up to Italy. That sum is only
right if the members TILE the container -- if no two of them claim the same ground over the same
years. `validate_polity_containment.py` checks each edge on its own (real codes, inside both spans,
every subnational row covered), and nothing checked the edges against each other.

What that let through, measured on 2026-09-24 against the ESRI:54034 polygons: five reporting
AGGREGATES declared directly under the national row BESIDE their own parts, so a member sum counted
the parts' ground twice --

    ITA-1919-2025  ITA-PVA-1861-2025 (Piemonte with Valle d'Aosta)  with  ITA-PIE-1970-2025 (99.99%)
                                                                    and   ITA-VDA-1948-2025 (99.88%)
    ITA-1919-2025  ITA-ABM-1861-2025 (Abruzzi e Molise)             with  ITA-ABR-1970-2025 (99.86%)
                                                                    and   ITA-MOL-1963-2025 (99.93%)
    ITA-1919-2025  ITA-TAA-1919-2025 (Trentino-Alto Adige)          with  ITA-ITH1-1919-2025 (99.79%)
                                                                    and   ITA-ITH2-1919-2025 (99.80%)
    FRA-1919-2025  FRA-COR-1800-2025 (Corsica, whole island)        with  FRA-2A-1975-2025 (99.90%)
    FRA-1919-2025  FRA-SSO-1860-2025 (Seine-et-Oise + suburban Seine) with FRA-91-1968-2025 (99.35%)

(share = the smaller member's area inside the larger). Every one of those parts was re-edged onto
its aggregate for the overlapping years, so the chain is part -> aggregate -> country and the
country's direct members tile it again. That is the fix this gate protects.

Its first run found a ninth, which the audit had not: HYD-1724-1948 and INU-1937-1947 both inside
IND-1937-1947, 100.00% of Hyderabad's 211,298 km2 shared. INU is the future-Union territory on
present boundaries (fao1952's `India`), which includes Hyderabad, and it had been added the same day
beside the Hyderabad edge. Hyderabad now sits inside INU for 1937-1947.

THE CHECK. For every container, every pair of distinct members whose EDGE intervals overlap
(`end_year` exclusive, as everywhere in this repo: the edges [1861,1866) and [1866,1870) share no
year) is intersected, and the intersection is normalised by the SMALLER member's area. A pair above
--max-share fails unless it is

  * registered as whole/part in pipelines/polity-autoimprove/state/polity_composition.csv, which is
    the place for a relation an edge cannot state faithfully -- a unit that straddles its would-be
    aggregate's boundary, so neither is inside the other -- and which carries its own double-count
    accounting (`overlap_sources`, `disposition`); or
  * listed in BASELINE below with the measured share and the reason.

BASELINE is BIDIRECTIONAL: an entry whose pair no longer overlaps above the threshold fails too, so
the list stays a record of live decisions rather than of past ones.

WHY 2%. After the re-edging the largest sibling overlap anywhere is 0.74% (USA-CT-1800-2025 /
USA-RI-1790-2025, 21 km2 of the smaller state), then AUS-ACT-1911-2025 / AUS-NSW-1901-2025 at 0.71%
and JPN-KYOTO-1871-2025 / JPN-OSAKA-1871-2025 at 0.61% -- outline resolution along a shared border,
not territory. An aggregate beside its part scores ~99%, and a real straddle scores its straddle
share, so the threshold sits well clear of the noise and far below every defect of this shape.
The Portuguese districts that straddle NUTS II regions (PRT-AV-1835-2025 is 63% Centro) do NOT
appear: they are depth-split already -- under PRT-1800-2025 until 1986 and under their NUTS II
region from 1986 -- so a district and a region are never siblings in the same year.

WHAT IT DOES NOT CHECK. Only direct siblings. A grandchild overlapping its parent's sibling is
already a sibling overlap one level up, so it is caught where it is introduced. A member with no
geometry cannot be measured; such pairs are counted and printed, never silently dropped.

Usage:
  python3 scripts/validate_containment_sibling_overlaps.py [--max-share 0.02] [--list]
"""
from __future__ import annotations

import argparse
import csv
import itertools
import os
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDGES = os.path.join(REPO, "data/final/polity_containment.csv")
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")
REGISTRY = os.path.join(REPO, "pipelines/polity-autoimprove/state/polity_composition.csv")
EQUAL_AREA = "ESRI:54034"

# Minimum number of measured sibling pairs. The live table yields 24,034 pairs whose intervals
# overlap (2026-09-24); if a refactor stopped reading the edges, the gate would find no overlap and
# PASS by having measured nothing.
MIN_PAIRS_MEASURED = 5000

# (container, member_a, member_b) with a and b sorted -> reason. Empty on 2026-09-24: every pair
# above the threshold was an aggregate declared beside its own part and was fixed by re-edging.
BASELINE: dict[tuple[str, str, str], str] = {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-share", type=float, default=0.02,
                    help="largest tolerated intersection as a share of the smaller member")
    ap.add_argument("--list", action="store_true", help="print the largest pairs below the threshold")
    args = ap.parse_args()

    try:
        import geopandas as gpd
    except ImportError as exc:
        print(f"FAIL: geopandas unavailable ({exc})")
        return 2
    for path in (EDGES, GPKG, REGISTRY):
        if not os.path.exists(path):
            print(f"FAIL: {os.path.relpath(path, REPO)} missing")
            return 2

    with open(EDGES, newline="", encoding="utf-8") as fh:
        edges = list(csv.DictReader(fh))
    with open(REGISTRY, newline="", encoding="utf-8") as fh:
        registered = set()
        for r in csv.DictReader(fh):
            w, p = (r.get("whole_code") or "").strip(), (r.get("part_code") or "").strip()
            if w and p:
                registered.add(frozenset((w, p)))

    g = gpd.read_file(GPKG)
    g = g[g.geometry.notna() & ~g.geometry.is_empty].to_crs(EQUAL_AREA)
    geo = dict(zip(g.polity_code, g.geometry.buffer(0)))

    by_container: dict[str, list[tuple[str, int, int]]] = defaultdict(list)
    for e in edges:
        by_container[e["container_code"].strip()].append(
            (e["member_code"].strip(), int(e["start_year"]), int(e["end_year"])))

    measured, no_geometry = 0, 0
    over: dict[tuple[str, str, str], tuple[float, float, int, int]] = {}
    below: list[tuple[float, str, str, str, int, int]] = []
    for container, members in sorted(by_container.items()):
        # One member may carry several edges to one container; merge nothing, but measure a pair
        # of MEMBERS once, over the union of the years in which any of their edges overlap.
        pairs: dict[tuple[str, str], list[int]] = {}
        for (a, sa, ta), (b, sb, tb) in itertools.combinations(members, 2):
            if a == b:
                continue
            s, t = max(sa, sb), min(ta, tb)
            if s >= t:
                continue
            key = tuple(sorted((a, b)))
            span = pairs.setdefault(key, [s, t])
            span[0], span[1] = min(span[0], s), max(span[1], t)
        for (a, b), (s, t) in sorted(pairs.items()):
            ga, gb = geo.get(a), geo.get(b)
            if ga is None or gb is None:
                no_geometry += 1
                continue
            measured += 1
            ax0, ay0, ax1, ay1 = ga.bounds
            bx0, by0, bx1, by1 = gb.bounds
            if ax1 < bx0 or bx1 < ax0 or ay1 < by0 or by1 < ay0:
                continue
            smaller = min(ga.area, gb.area)
            if smaller <= 0 or not ga.intersects(gb):
                continue
            inter = ga.intersection(gb).area
            share = inter / smaller
            if share > args.max_share:
                over[(container, a, b)] = (share, inter / 1e6, s, t)
            elif share > 0:
                below.append((share, container, a, b, s, t))

    problems: list[str] = []
    if measured < MIN_PAIRS_MEASURED:
        problems.append(
            f"LIVE: only {measured} sibling pair(s) were measured (expected >= "
            f"{MIN_PAIRS_MEASURED}); the gate cannot pass by having nothing to compare")

    exempt_registered = []
    for key, (share, km2, s, t) in sorted(over.items()):
        container, a, b = key
        if frozenset((a, b)) in registered:
            exempt_registered.append(key)
            continue
        if key in BASELINE:
            continue
        problems.append(
            f"OVERLAP: {a} and {b} are both declared inside {container} for {s}-{t} and share "
            f"{km2:,.0f} km2, {share:.2%} of the smaller -- summing {container}'s members counts "
            f"that ground twice. If one contains the other, re-edge the part onto the whole for "
            f"those years (container: block on its wiki page); if neither contains the other, "
            f"register the pair in polity_composition.csv.")
    for key, why in sorted(BASELINE.items()):
        if key not in over:
            problems.append(
                f"STALE BASELINE: {key[1]} / {key[2]} in {key[0]} no longer overlaps above "
                f"{args.max_share:.0%}; remove it from BASELINE ({why})")

    print(f"{len(edges)} containment edge(s) over {len(by_container)} container(s); "
          f"{measured} sibling pair(s) with overlapping years measured, {no_geometry} without "
          f"geometry on one side")
    print(f"  above {args.max_share:.0%} of the smaller member: {len(over)} "
          f"({len(exempt_registered)} registered in polity_composition.csv, "
          f"{len(set(over) & set(BASELINE))} baselined)")
    for key in exempt_registered:
        share, km2, s, t = over[key]
        print(f"    registered  {key[1]} / {key[2]} in {key[0]} {s}-{t}: {share:.2%}")
    top = sorted(below, reverse=True)[: (20 if args.list else 3)]
    if top:
        print("  largest pairs below the threshold (outline resolution along a shared border):")
        for share, container, a, b, s, t in top:
            print(f"    {share:.2%}  {a} / {b} in {container} {s}-{t}")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1
    print("\nPASS: no two members of one container cover the same ground in the same years")
    return 0


if __name__ == "__main__":
    sys.exit(main())
