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

Within an iso3 family, a pair is AT RISK when it overlaps by more than one year (a
one-year overlap is the shared transition year, resolved by the successor
convention) and ties on the national/not-national preference. Every such pair has
its winner chosen by family order.

THE 3x RATIO FILTER WAS REMOVED (issue 115). It reported only pairs differing in
area by >=3x, on the premise that a component is much smaller than its parent —
true for HYD-1724-1948 inside British India at 20x, which is one of the three
cases that motivated this script. But it is INVERTED for the worst case: two rows
describing the SAME territory have a ratio of 1.0, which read as "not a
component" when it means "the same place", and that is where the arbitrary pick
matters most. Measured before the change: 0 pairs at >=3x, so this script PASSED,
while 15 pairs had their match decided by family order — including
MYS-1957-1963 against MASG-1946-1963 at 1.004x, which was resolving "Malaysia"
1961 to British North Borneo (issue 44).

So the ratio is now REPORTED rather than used to filter, in three bands:

  >= 3x        probable component inside a parent — the original concern
  <= 1.1x      comparable or identical territory — arbitrary AND high-impact
  in between   neither reading is clear; still arbitrary

WHAT NEAR-EQUAL DOES NOT MEAN, because it is the obvious wrong inference: it does
not mean same territory. Sarawak against Malaya (1.06x) and South against Western
Australia (1.09x) are different places of similar size. All these pairs share is
that family order decides the match, which is enough to report and is the only
claim made.

Usage:
  python3 scripts/audit_family_shadowing.py [--ratio 3.0]

`--ratio` now only sets the boundary of the "probable component" band in the
report. Exit 1 if any pair is not in BASELINE.
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
# Tied pairs judged and accepted, each with the reason. A pair here still has its winner
# chosen by family order — the entry says that is harmless because the two are genuinely
# different territories and no label should resolve between them by type alone.
# Bidirectional: a new pair fails, and one that stops tying must be removed.
BASELINE = {
    # Two distinct Australian-administered territories on one island, similar in size.
    # A label naming either should route by alias, not by rank.
    "TPAP-1906-1949 / TNGU-1920-1949": "Papua and New Guinea, different territories",
    # Sarawak is not Malaya. Different territories of comparable size, both correct rows.
    "BSW-1841-1963 / MASG-1946-1963": "Sarawak vs Malaya+Singapore, different territories",
    "BSW-1841-1963 / GBM-1895-1946": "Sarawak vs British Malaya, different territories",
    "BNB-1881-1963 / BSW-1841-1963": "North Borneo vs Sarawak, different territories",
    "BNB-1881-1963 / MASG-1946-1963": "North Borneo vs Malaya+Singapore, different",
    "BNB-1881-1963 / GBM-1895-1946": "North Borneo vs British Malaya, different",
    # Two separate Australian colonies before federation.
    "AUSA-1836-1900 / AUWA-1829-1900": "South vs Western Australia, different colonies",
}

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
            # No ratio filter: every tied pair has its winner chosen by family order.
            flagged.append((iso, ratio, small, big, int(lo), int(hi)))

flagged.sort(key=lambda x: -x[1])
unbaselined = [f for f in flagged
               if f"{f[2].polity_code} / {f[3].polity_code}" not in BASELINE
               and f"{f[3].polity_code} / {f[2].polity_code}" not in BASELINE]
print(f"{len(g)} live polities with geometry; {len(flagged)} tied pair(s) "
      f"(same iso3, >1y overlap, tied type rank), {len(unbaselined)} not baselined\n")
for iso, ratio, small, big, lo, hi in flagged:
    band = ("probable component in parent" if ratio >= A.ratio
            else "comparable or identical territory" if ratio <= 1.1
            else "neither reading clear")
    mark = "" if f"{small.polity_code} / {big.polity_code}" in BASELINE or \
                 f"{big.polity_code} / {small.polity_code}" in BASELINE else "  <-- NOT BASELINED"
    print(f"  [{band}]{mark}")
    # Label by BAND, not by size. Calling the smaller row "component?" is only a
    # reasonable guess in the >=ratio band; on a 1.06x pair it asserts a containment
    # that is usually false -- Sarawak is not a component of Malaya.
    la, lb = (("component?", "parent?   ") if ratio >= A.ratio
              else ("smaller:  ", "larger:   "))
    print(f"  {ratio:7.2f}x  iso {iso}  {lo}-{hi}")
    print(f"           {la} {small.polity_code:18s} {str(small.polity_name)[:34]:34s} "
          f"{small.area_km2:>12,.0f} km2  type={small.polity_type}")
    print(f"           {lb} {big.polity_code:18s} {str(big.polity_name)[:34]:34s} "
          f"{big.area_km2:>12,.0f} km2  type={big.polity_type}")

for pair in sorted(BASELINE):
    a, b = [x.strip() for x in pair.split("/")]
    live = {f"{f[2].polity_code} / {f[3].polity_code}" for f in flagged} | \
           {f"{f[3].polity_code} / {f[2].polity_code}" for f in flagged}
    if pair not in live:
        unbaselined.append(("stale", 0.0, None, None, 0, 0))
        print(f"\n  {pair} is baselined as a tied pair but no longer ties — remove it")

print(f"\n{'FAIL' if unbaselined else 'PASS'}: {len(flagged)} tied pair(s); "
      f"{len(unbaselined)} outside the baseline. Family ordering, not polity_type, "
      f"decides each of these.")
sys.exit(1 if unbaselined else 0)
