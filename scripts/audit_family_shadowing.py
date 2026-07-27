#!/usr/bin/env python3
"""Find polities that can SHADOW a sibling in the matcher's family ranking.

The matcher resolves a label to an ISO family, then picks the period covering the
row's year, preferring polity_type == "national" (see
pipelines/polity-autoimprove/matchlib.py, pick_by_year). When two polities share
an iso3_code, overlap in time, and tie on that preference, the winner is decided
by family ORDERING — which is arbitrary. If one of them is a component of the
other (a territory, princely state, island group), national-scale data can land
on it silently.

This has bitten three times in one day:
  ALK-1867-1959  Territory of Alaska, typed `national`, iso3 USA, same span as
                 USA-1867-1959 — absorbed ~7,600 rows of mainland US data.
  HYD-1724-1948  Hyderabad State, typed `colonial`, iso3 IND, spanning
                 1724-1948 — took 36 rows of plainly "india" data the moment the
                 India chain was re-split.
  ARG-1800-2025  a retired collapsed row outranking its own live successors
                 (fixed separately by excluding dead statuses).

The fix in each case is the type field: a component should be `subnational`,
`territory` or `city-territory`, all of which rank below `national`. This script
flags the remaining candidates so the type field can be corrected before data
lands wrongly, rather than after.

Heuristic: within an iso3 family, report pairs that overlap by more than one year
(a one-year overlap is the shared transition year, resolved by the successor
convention), tie on the national/not-national preference, and differ in measured
area by at least --ratio — the smaller being a probable component of the larger.

Usage:
  python3 scripts/audit_family_shadowing.py [--ratio 3.0]
Exit 1 if any pair is flagged.
"""
import geopandas as gpd, pandas as pd, argparse, os, sys, warnings
warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")
DEAD = ("retired", "superseded")

ap = argparse.ArgumentParser()
ap.add_argument("--ratio", type=float, default=3.0,
                help="minimum area ratio for the smaller polity to count as a probable component")
A = ap.parse_args()

g = gpd.read_file(GPKG)
g = g[~g.wiki_status.astype(str).isin(DEAD)]                  # dead rows never match
g = g[g.geometry.notna() & ~g.geometry.is_empty].copy()
g["area_km2"] = g.to_crs("ESRI:54034").geometry.area / 1e6
g["s"] = pd.to_numeric(g.start_year, errors="coerce")
g["e"] = pd.to_numeric(g.end_year, errors="coerce")
g["is_nat"] = g.polity_type.astype(str) == "national"

# The matcher indexes a family only for a real iso3 string. Note pandas reads
# "NA" from the CSV as NaN, so those polities are NOT in any family — but the
# GeoPackage returns the same value as the TEXT "NA", which would create one
# bogus family containing every unrelated polity. Exclude the non-ISO values.
NON_ISO = {"NA", "NAN", "NONE", ""}
flagged = []
for iso, fam in g.groupby("iso3_code"):
    if not isinstance(iso, str) or iso.strip().upper() in NON_ISO: continue
    if len(fam) < 2: continue
    rows = list(fam.itertuples())
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            lo, hi = max(a.s, b.s), min(a.e, b.e)
            if pd.isna(lo) or pd.isna(hi) or hi - lo < 1: continue   # no real overlap
            if a.is_nat != b.is_nat: continue                        # rank breaks the tie
            big, small = (a, b) if a.area_km2 >= b.area_km2 else (b, a)
            if small.area_km2 <= 0: continue
            ratio = big.area_km2 / small.area_km2
            if ratio < A.ratio: continue
            flagged.append((iso, ratio, small, big, int(lo), int(hi)))

flagged.sort(key=lambda x: -x[1])
print(f"{len(g)} live polities with geometry; {len(flagged)} shadowing candidate(s) "
      f"(same iso3, >1y overlap, tied type rank, area ratio >= {A.ratio}x)\n")
for iso, ratio, small, big, lo, hi in flagged:
    print(f"  {ratio:7.1f}x  iso {iso}  {lo}-{hi}")
    print(f"           component?  {small.polity_code:18s} {str(small.polity_name)[:34]:34s} "
          f"{small.area_km2:>12,.0f} km2  type={small.polity_type}")
    print(f"           parent?     {big.polity_code:18s} {str(big.polity_name)[:34]:34s} "
          f"{big.area_km2:>12,.0f} km2  type={big.polity_type}")

print(f"\n{'FAIL' if flagged else 'PASS'}: {len(flagged)} pair(s) where family ordering, "
      f"not polity_type, decides the match")
sys.exit(1 if flagged else 0)
