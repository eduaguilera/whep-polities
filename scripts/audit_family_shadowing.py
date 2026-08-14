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
    # An aggregate over its own constituents, added 2026-08-05 with PAPNG-1920-1949. Unlike the
    # pairs above these are NOT different territories -- the larger CONTAINS the smaller, by
    # construction: PAPNG is the union of exactly these two. The ratios (2.06x and 1.94x) are
    # therefore expected rather than suspicious, and the coexistence is describable because
    # PAPNG is typed `aggregate` while both constituents are `colonial`.
    #
    # Compare GCT-1919-1956, whose polygon is STILL unattached because it and BTL-1920-1957 are
    # both typed `colonial` and overlap at 9x (issue 47). The type is what makes the difference
    # between a reporting unit and a collision, which is why `aggregate` was chosen here.
    "TPAP-1906-1949 / PAPNG-1920-1949": "Papua inside the Papua+New Guinea reporting unit (2.06x, by construction)",
    # British Togoland inside the Gold Coast + British Togoland reporting unit, added 2026-08-06
    # when GCT-1919-1956's polygon was finally attached. 9.00x, and by construction: GCT is the
    # union of the Gold Coast (212,416 km2) and exactly this mandate (26,630).
    #
    # THIS PAIR IS WHY GCT SAT UNATTACHED FOR A WEEK. Both rows were typed `colonial` on iso3 GHA,
    # so this audit read them as two colonies of wildly different size overlapping 1920-1956 and
    # reported "neither reading clear" -- correctly, because nothing in the data said which was the
    # container. Retyping GCT `aggregate` (the MASG/CODRU/PAPNG pattern for a combined reporting
    # unit) changed the audit's own verdict to "probable component in parent", which is the
    # relationship that actually holds. The type field was carrying the information all along; it
    # was just set to the wrong value.
    "BTL-1920-1957 / GCT-1919-1956": "British Togoland inside the Gold Coast + Br Togoland reporting unit (9.00x, by construction)",
    # Java and Netherlands New Guinea, added 2026-08-07 when IDN-JVM's polygon was attached.
    #
    # THE AUDIT LABELS THIS "probable component in parent" AND THAT LABEL IS WRONG HERE. Measured:
    # Java spans 105.1-116.3E, Netherlands New Guinea 129.7-141.0E, their intersection is 0.000 km2
    # and they are 14.4 degrees apart. Neither contains the other; they are opposite ends of the
    # archipelago.
    #
    # They share iso3 IDN because both are parts of Indonesia, and they overlap in TIME (1949-1951)
    # while being disjoint in SPACE -- which is the one combination this audit's heuristic cannot
    # read, because it infers containment from an area ratio and a shared code. A 3.09x ratio
    # between two disjoint islands looks identical to a 3.09x ratio between a province and its
    # country. Recorded so the label is not mistaken for a finding.
    "IDN-JVM-1949-1951 / NNG-1949-1963": "Java and Netherlands New Guinea: DISJOINT (0.000 km2 intersection, 14.4 degrees apart), sharing iso3 IDN only",
    # The three-way 1949-1951 Indonesian partition, added 2026-08-07 when IDN-BLB and IDN-OTH were
    # attached. Java, Bali/Lombok and "other islands" are MUTUALLY DISJOINT BY CONSTRUCTION --
    # IDN-OTH is literally the complement of the other two -- so every ratio below is a partition
    # and not a containment, however large. Measured intersections are 0.0 km2 for all of them.
    #
    # The audit cannot tell a partition from a containment, because both look like one large row
    # and one small row sharing an iso3 and a span. 171x between Bali/Lombok and the other islands
    # is the most extreme instance and the most obviously benign.
    "IDN-BLB-1949-1951 / IDN-OTH-1949-1951": "partition, disjoint by construction (171x, 0.0 km2 intersection)",
    "IDN-JVM-1949-1951 / IDN-OTH-1949-1951": "partition, disjoint by construction (13.1x, 0.0 km2 intersection)",
    "IDN-BLB-1949-1951 / IDN-JVM-1949-1951": "partition, disjoint by construction (13.1x, 0.0 km2 intersection)",
    "IDN-BLB-1949-1951 / NNG-1949-1963": "Bali/Lombok and West Papua: disjoint (0.0 km2 intersection)",
    # AND ONE THAT WAS NOT BENIGN, now fixed -- kept here with both numbers, because the pair still
    # TIES on area ratio (3.3x) even though it no longer overlaps, and PINNED_DISJOINT below is what
    # holds the fix in place:
    #
    #   IDN-OTH-1949-1951 n NNG-1949-1963 = 405,513 km2 -> 0 km2   (98.8% of NNG, claimed twice)
    #
    # Netherlands New Guinea stayed Dutch until 1962, so West Papua was NOT part of Indonesia in
    # 1949-1951 -- yet IDN-OTH's declared area of 1,757,495 km2 INCLUDED it, so the double claim was
    # in the two pages' definitions rather than in the geometry implementing them. Any area-weighted
    # use over 1949-1951 counted West Papua twice: the class eduaguilera/whep#514 reports, for a
    # different pair than the one that issue names.
    #
    # FIXED 2026-08-07: build_idn_oth_1949_1951 now subtracts the same CShapes feature NNG binds to,
    # and the declared area drops to 1,349,065 -- FAO 1952 lists Indonesia (1947, 1,904,350) and New
    # Guinea (1951, 412,780) as SEPARATE reporting units, so the old figure was a whole-Dutch-East-
    # Indies total less Java and Bali. The old 0.6% agreement between declared and measured was two
    # errors cancelling, which is why the geometry alone never looked wrong.
    "NNG-1949-1963 / IDN-OTH-1949-1951": "was a 405,513 km2 real overlap (98.8% of NNG); fixed 2026-08-07, now disjoint and pinned so",
    # Surfaced by moving FRIN-1816-1954 from iso3 FRA to IND on 2026-08-07. Under FRA nothing
    # compared French India with anything Indian; under IND it ties with Hyderabad State, because
    # both are non-national and the rank cannot break it. They are 1.155 degrees apart and the
    # intersection measures 0.000 km2 -- Pondicherry and the other establishments are coastal, and
    # Hyderabad was the Deccan interior. PINNED_DISJOINT asserts that zero rather than describing it.
    "FRIN-1816-1954 / HYD-1724-1948": "French India vs Hyderabad State: disjoint (0.000 km2, 1.155 degrees apart), sharing iso3 IND only",
    "TNGU-1920-1949 / PAPNG-1920-1949": "New Guinea inside the Papua+New Guinea reporting unit (1.94x, by construction)",
    "BSW-1841-1963 / GBM-1895-1946": "Sarawak vs British Malaya, different territories",
    "BNB-1881-1963 / BSW-1841-1963": "North Borneo vs Sarawak, different territories",
    "BNB-1881-1963 / MASG-1946-1963": "North Borneo vs Malaya+Singapore, different",
    "BNB-1881-1963 / GBM-1895-1946": "North Borneo vs British Malaya, different",
    # OCCUPIED LIBYA 1943-1951: the three territories, and each against the all-Libya rows.
    # Added 2026-08-10 with their polygons (issue 156). Eight pairs appear at once and every one
    # is the partition working as intended rather than a defect:
    #
    #   TRP / CYR / FEZ against LBY-1943-1949 and LBY-1949-1951 -- a part inside its own whole,
    #   which is what "component in parent" is supposed to look like. Ratios 5.14x, 3.49x, 1.93x.
    #
    #   TRP / CYR / FEZ against each other -- same iso3 LBY, same polity_type national, spans
    #   overlapping, so the type rank cannot break the tie. They are pairwise disjoint (0.0000
    #   km2 unsimplified) and PINNED_DISJOINT asserts it every run.
    #
    # The pairs are unavoidable given the model: iso3 LBY carries both the whole and its parts,
    # and all four are `national` because the occupation territories were not subordinate units
    # of a Libyan state -- there was no Libyan state between 1943 and 1951.
    "TRP-1943-1951 / LBY-1943-1949": "Tripolitania inside all-Libya, by construction (5.14x)",
    "TRP-1943-1951 / LBY-1949-1951": "Tripolitania inside all-Libya, by construction (5.14x)",
    "FEZ-1943-1951 / LBY-1943-1949": "Fezzan inside all-Libya, by construction (3.49x)",
    "FEZ-1943-1951 / LBY-1949-1951": "Fezzan inside all-Libya, by construction (3.49x)",
    "CYR-1949-1951 / LBY-1949-1951": "Cyrenaica inside all-Libya, by construction (1.93x)",
    "TRP-1943-1951 / CYR-1949-1951": "two thirds of the same partition: disjoint, 0.0000 km2",
    "FEZ-1943-1951 / CYR-1949-1951": "two thirds of the same partition: disjoint, 0.0000 km2",
    "TRP-1943-1951 / FEZ-1943-1951": "two thirds of the same partition: disjoint, 0.0000 km2",
    # CYR-1943-1949 added 2026-08-13 (issue 198): the British military administration of Cyrenaica,
    # which had no row while TRP and FEZ covered 1943-1951 in full. It carries CYR-1949-1951's
    # constructed feature UNCHANGED -- same 837,876 km2 of ground, earlier administration -- so
    # these three pairs are the same three the emirate already had, one window earlier. It does NOT
    # pair with CYR-1949-1951 itself: end_year is exclusive, so the two never coexist.
    "CYR-1943-1949 / LBY-1943-1949": "Cyrenaica inside all-Libya, by construction (1.93x)",
    "TRP-1943-1951 / CYR-1943-1949": "two thirds of the same partition: disjoint, 0.0000 km2",
    "FEZ-1943-1951 / CYR-1943-1949": "two thirds of the same partition: disjoint, 0.0000 km2",
    # Two separate Australian colonies before federation.
    "AUSA-1836-1900 / AUWA-1829-1900": "South vs Western Australia, different colonies",
}

# PAIRS THAT MUST MEASURE ZERO INTERSECTION, asserted rather than described.
#
# eduaguilera/whep#514 asked for "a regression check pinning the GNQ/STP pair" -- but GNQ and STP
# were never the defect (different sources, 26x size difference, empty intersection), so pinning
# them would pass vacuously forever. The pair that DID double-claim ground is IDN-OTH / NNG, so
# that is what is pinned here.
#
# WHY THE BASELINE ABOVE IS NOT ENOUGH. That baseline records pairs by NAME with a prose reason;
# nothing in it re-measures anything. IDN-OTH/NNG sat in it for a day carrying the string
# "REAL OVERLAP: 405,513 km2" and the gate passed on every run, because a described defect is
# still a baselined pair. A named pair with a measured assertion cannot rot that way: if the
# builder stops subtracting West Papua, this fails with the km2 it came back as.
PINNED_DISJOINT = {
    ("IDN-OTH-1949-1951", "NNG-1949-1963"):
        "West Papua was Dutch until 1962; IDN-OTH is a complement and must exclude it (whep#514)",
    ("IDN-JVM-1949-1951", "IDN-OTH-1949-1951"):
        "partition by construction -- OTH is defined as Indonesia minus JVM and BLB",
    ("IDN-BLB-1949-1951", "IDN-OTH-1949-1951"):
        "partition by construction -- OTH is defined as Indonesia minus JVM and BLB",
    ("FRIN-1816-1954", "HYD-1724-1948"):
        "coastal establishments vs the Deccan interior; ties on iso3 IND only",
    # Occupied Libya's three territories, added 2026-08-10 with their polygons (issue 156).
    # They are built as unions of disjoint GADM shabiyat, so disjointness is by construction --
    # which is exactly why it is worth ASSERTING: the whole value of the partition is that
    # per-territory data sums to the national total, and a future edit to any of the three
    # shabiya lists could break that silently. The union also equals GADM's Libya to 0.0000 km2.
    ("TRP-1943-1951", "CYR-1949-1951"):
        "Tripolitania vs Cyrenaica; adjacent across the Sirte basin, disjoint by construction",
    ("TRP-1943-1951", "FEZ-1943-1951"):
        "Tripolitania vs Fezzan; adjacent, disjoint by construction",
    ("CYR-1949-1951", "FEZ-1943-1951"):
        "Cyrenaica vs Fezzan; adjacent, disjoint by construction",
    # The 1943-1948 half of the same partition, added 2026-08-13 with CYR-1943-1949 (issue 198).
    # Worth asserting separately even though CYR-1943-1949 shares the emirate's feature: the two
    # rows are simplified INDEPENDENTLY by build_database, so these are genuinely different
    # measurements, and if a future edit rebinds either row the pin fails with the km2 it came
    # back as instead of going quietly inert.
    ("TRP-1943-1951", "CYR-1943-1949"):
        "Tripolitania vs British-administered Cyrenaica; disjoint by construction",
    ("CYR-1943-1949", "FEZ-1943-1951"):
        "British-administered Cyrenaica vs Fezzan; disjoint by construction",
}
PIN_TOLERANCE_KM2 = 1.0   # simplify+densify leaves sliver-scale disagreement on shared edges

# A PAIR SHARING A LONG LAND BOUNDARY NEEDS MORE HEADROOM THAN AN ISLAND PAIR, and 1.0 km2 was
# calibrated on island pairs. The IDN entries above are separated by open sea, so their shared
# edge has no length and any intersection at all is a defect. Tripolitania and Cyrenaica are
# built from adjacent GADM shabiyat and share roughly 500 km of land boundary through the Sirte
# basin: unsimplified they intersect at 0.0000 km2, but build_database simplifies each row
# INDEPENDENTLY at 0.01 degrees (~1.1 km), so the shared edge no longer matches and 1.2 km2 of
# sliver appears in the published GeoPackage. That is the same mechanism that put 341 km2 back
# between IDN-OTH and NNG (PR 182) -- there it was fatal because the rim was 6,140 km2 wide;
# here the whole boundary contributes 1.2.
#
# 5 km2 against territories of 315,000 and 838,000 km2 is 0.0006%, and a genuine re-assignment
# error would be a whole shabiya -- 78,659 km2 for Surt, 111,245 for Al Jufrah. So this cannot
# hide the defect it is here to catch.
PIN_TOLERANCE_OVERRIDE = {
    ("TRP-1943-1951", "CYR-1949-1951"): 5.0,
    ("TRP-1943-1951", "FEZ-1943-1951"): 5.0,
    ("CYR-1949-1951", "FEZ-1943-1951"): 5.0,
    # Same shared land boundaries, one window earlier (issue 198).
    ("TRP-1943-1951", "CYR-1943-1949"): 5.0,
    ("CYR-1943-1949", "FEZ-1943-1951"): 5.0,
}

by_code = {r.polity_code: r.geometry for r in g.itertuples()}
pin_failures = []
for (a, b), why in sorted(PINNED_DISJOINT.items()):
    if a not in by_code or b not in by_code:
        pin_failures.append(f"{a} / {b}: one side has no live geometry -- cannot verify ({why})")
        continue
    inter = by_code[a].intersection(by_code[b])
    km2 = 0.0 if inter.is_empty else (
        gpd.GeoSeries([inter], crs=g.crs).to_crs("ESRI:54034").iloc[0].area / 1e6)
    tol = PIN_TOLERANCE_OVERRIDE.get((a, b), PIN_TOLERANCE_OVERRIDE.get((b, a),
                                                                          PIN_TOLERANCE_KM2))
    if km2 > tol:
        pin_failures.append(f"{a} / {b}: intersect {km2:,.1f} km2, must be <= {tol} -- {why}")
print(f"pinned-disjoint pairs: {len(PINNED_DISJOINT)} checked, {len(pin_failures)} failing")
for f in pin_failures:
    print(f"  FAIL  {f}")
print()

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

bad = bool(unbaselined) or bool(pin_failures)
print(f"\n{'FAIL' if bad else 'PASS'}: {len(flagged)} tied pair(s); "
      f"{len(unbaselined)} outside the baseline; {len(pin_failures)} pinned-disjoint "
      f"pair(s) overlapping. Family ordering, not polity_type, decides each of these.")
sys.exit(1 if bad else 0)
