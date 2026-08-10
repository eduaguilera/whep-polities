#!/usr/bin/env python3
"""Two spatial checks that need no reference data and no hand-entered value.

  CONTAINMENT   a polygon that geometrically swallows other contemporaneous
                polities, which double-counts their territory
  CONTINUITY    successive periods of one family whose polygons do not overlap,
                which means one of them is bound to the wrong feature

Why this is a distinct check: `validate_polygons.py` compares a polygon against
its recorded `polygon_area_km2`, so it is opt-in via a hand-entered field. Roughly
590 of 740 rows carry no area and are therefore never compared, and the worst
polygon error in the database sits in that blind spot:

  RUS-1991-2014 uses CShapes feature 365 — the same feature as every F228 (Russian
  Empire / USSR) row — and measures 21,824,142 km2 against Russia's 17,098,242. It
  geometrically contains Kazakhstan, Ukraine, Uzbekistan, Turkmenistan, the
  Baltics, Georgia and Azerbaijan. It has no recorded area, so nothing compared it
  to anything (issue 45).

This check needs no reference data and no hand-entered value. It asks only whether
two polities that COEXIST in time overlap in space, which for two separate
territories is a contradiction the geometry itself reveals.

Containment is frequently legitimate, so the check reports CONTAINERS rather than
pairs: a polity whose polygon holds three or more contemporaneous polities of other
families. Empires and federations do exactly that — and `polity_type` cannot
distinguish them, since French West Africa and its member colonies are all
`national` — so the legitimate ones are enumerated below rather than inferred.

Usage:
  python3 scripts/validate_spatial_containment.py [--min-contained 3]
"""
import argparse
import os
import sys
from collections import defaultdict

import geopandas as gpd
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")
EQUAL_AREA = "ESRI:54034"
DEAD_STATUS = ("retired", "superseded")

# Polities that legitimately contain others, because they WERE the larger entity:
# empires containing their possessions, colonial federations containing their
# member colonies, and the statistical aggregates that exist to hold small
# territories. Enumerated because the database cannot express it — AOF-1895-1960
# and every colony inside it are all typed `national`.
LEGITIMATE_CONTAINERS = frozenset({
    # Statistical / reporting aggregates
    "ROW-1850-2025", "RAFR-1850-2025", "RASI-1850-2025", "REUR-1850-2025",
    "RLAM-1850-2025", "ROCE-1850-2025",
    # Empires
    "F228-1800-1856", "F228-1856-1905", "F228-1905-1914", "F228-1914-1917",
    "F228-1917-1918", "F228-1918-1920", "F228-1945-1991",
    "AUH-1800-1859", "AUH-1859-1866", "AUH-1866-1908", "AUH-1908-1918",
    "OTT-1800-1886", "JPN-1895-1945",
    # Colonial federations and their groupings
    "AOF-1895-1960", "AEF-1910-1960", "CODRU-1922-1960", "FRN-1953-1964",
    "MASG-1946-1963",
    "MLI-1890-1960", "SEN-1854-1886", "SEN-1886-1959", "KEN-1891-1894",
    "NGA-1886-1914", "ZWE-1891-1900",
    # AEF-1910-1960 added when its polygon was first built: French Equatorial Africa
    # is the union of Gabon, Ubangi-Shari, Chad and Middle Congo, so it necessarily
    # contains the 13 period-polities of those four families. Flagged as a NEW
    # container the moment the builder landed, which is the third time this check has
    # made a newly built polygon justify itself.
    # A federation over its pre-1901 colonies
    "AUS-1800-1901",
    # TTPI-1947-1994 WAS HERE AND IS NOT ANY MORE, which is worth explaining rather than
    # silently deleting: it did not stop containing anything, the measurement got sharper.
    #
    # It was added on 2026-07-29 as a UN trust territory over the four territories that became
    # its successors — the union of GADM FSM, MHL, MNP and PLW necessarily contains those
    # polities, whose spans overlap TTPI's 1947-1994.
    #
    # On 2026-08-10 build_database gained a per-feature simplification budget, so archipelagos
    # are no longer thinned at 1.1 km. Re-measured against TTPI's 2,026 km2:
    #
    #     PLW-1991-2025   480.5 km2   100.0% inside
    #     FSM-1991-2025   762.8 km2    99.3% inside
    #     MHL-1874-2025   300.0 km2    85.6% inside   <-- below the 90% --overlap threshold
    #
    # Two contained rows, not three, so TTPI no longer meets this gate's >=3 definition of a
    # container. Both remaining containments are as real as they ever were.
    #
    # MHL's 85.6% is the finding hiding in here, and it is NOT a simplification artefact: about
    # 43 km2 of the Marshall Islands sits outside the polygon of the trust territory that
    # administered them, because TTPI is a union of modern GADM outlines and MHL's own GADM
    # outline reaches atolls the union does not. Coarse simplification had blurred both until
    # they agreed. Left recorded rather than fixed -- it is a question about TTPI's recipe in
    # scripts/sources/constructed/build.py, not about the simplification change.
    # French Indochina over Vietnam, Cambodia and Laos -- it held all three as
    # constituent protectorates, so containment is the historical fact.
    #
    # WORTH READING BEFORE TRUSTING THIS GATE'S SILENCE ELSEWHERE: this container appeared
    # only on 2026-08-05, when FID-1887-1954's polygon was rebuilt. Not because the polygon
    # moved into Indochina -- the previous one already covered Hanoi and Saigon -- but because
    # the previous one was INVALID, and `contains` on an invalid geometry is unreliable. A
    # containment relationship involving six polities was invisible for as long as the
    # geometry was broken, and nothing reported that this check was degraded. That is the
    # concrete harm validate_polygon_validity exists to bound.
    #
    # The double-count risk here is REAL and not hypothetical: in 22 years (1930-1951) layer B
    # carries data against both the whole and its parts, because Mitchell publishes an
    # Indochina aggregate alongside per-territory series. Both are kept -- dropping either
    # would discard published data -- so any spatial or area-weighted use must pick one level.
    # Fixing the routing found 99 rows labelled `Indochina Viet Nam` that were landing on the
    # WHOLE rather than on Vietnam, which would have summed a part into its own aggregate.
    "FID-1887-1954",
    # British India over the European enclaves, added 2026-08-07 when FRIN-1816-1954's polygon was
    # attached. Pondicherry, Karikal, Mahe and Yanam sit inside India by definition, as Goa and
    # Daman-and-Diu already did for PTIND-1816-1961. Hyderabad and Kashmir likewise.
    "IND-1947-1949",
    "IND-1949-2025",
    # Occupied and divided Germany over its occupation zones AND the Saar. Both became
    # containers on 2026-08-05 only because SAA-1947-1957's polygon was attached, which pushed
    # each from two contained polities to three -- the zones were already inside them.
    #
    # The zone containment is by construction: build_deu_1945_1949() and build_deu_1949_1990()
    # are unions of exactly those territories.
    #
    # THE SAAR IS DIFFERENT AND THE DOUBLE-COUNT IS REAL. Between 1947 and 1957 the Saar was
    # detached from Germany -- a French protectorate with its own currency and customs frontier --
    # so it sits geographically inside these polygons while being administratively outside them.
    # Any spatial or area-weighted use that sums Germany and the Saar for those years
    # double-counts 2,571 km2. That is 0.7% of Germany, so it is small rather than negligible,
    # and it is a property of the history rather than of the polygons: the Saar really was inside
    # Germany's outline and outside its administration.
    "DEU-1945-1949",
    "DEU-1949-1990",
    # Occupied Libya over its three territories, added 2026-08-10 with their polygons (issue
    # 156). This is the most literal container in the list: TRP + CYR + FEZ are built as unions of
    # disjoint GADM shabiyat whose union reproduces GADM's Libya to 0.0000 km2, so LBY-1949-1951
    # containing all three is the partition property itself, not a swallow.
    #
    # THE DOUBLE-COUNT RISK IS REAL AND IS THE REASON THE PARTS EXIST. FAO 1952 publishes an
    # all-Libya series AND per-territory series for the same years, and both are kept -- dropping
    # either would discard published data -- so any spatial or area-weighted use must pick one
    # level. That is the same shape as FID-1887-1954 over Indochina above.
    #
    # LBY-1943-1949 does NOT appear here, and the reason is worth knowing: it holds only TRP and
    # FEZ, because CYR-1949-1951 is the EMIRATE of Cyrenaica and starts in 1949. The British
    # military administration of Cyrenaica, 1943-1949, has no row at all -- so this container
    # sits one below the >=3 threshold for a coverage gap rather than for a territorial reason.
    "LBY-1949-1951",
    # A joint reporting unit over the two states it combines. Added when its polygon
    # was first built: SYL-1944-1953 is Syria + Lebanon, so it necessarily contains
    # the SYR and LBN period-polities.
    "SYL-1944-1953",
    # British India over its provinces and princely states. These four crossed the
    # >=3 threshold the moment PTIND-1816-1961's polygon was built (2026-08-04), which
    # is the fifth time this check has made a newly built polygon justify itself. Each
    # content was checked individually rather than accepted as a group:
    #
    #   HYD-1724-1948   211,298 km2  100.0%  Hyderabad, a princely state under British
    #                                        suzerainty and inside British India.
    #   MMR-1885-2025   675,971 km2   96.9%  Burma, annexed 1886 and administered AS A
    #                                        PROVINCE of British India until it was
    #                                        separated on 1937-04-01.
    #   PAK-1937-1947   932,574 km2  100.0%  The territory that became Pakistan, which
    #                                        its own polity_name states was within
    #                                        British India.
    #
    # The polygons encode the Burma separation correctly, which is the evidence that
    # these are history and not mis-bindings: IND-1937-1947 does NOT contain
    # MMR-1885-2025, while the three earlier periods do.
    #
    # ONE CONTENT IS NOT LEGITIMATE, and a container-level exemption necessarily hides
    # it: PTIND-1816-1961 (Portuguese India -- Goa, Daman, Diu) sits 98.4% inside every
    # British India period, and Portuguese India was never British India. It is a real
    # 3,779 km2 double-count and it survives into IND-1949-2025, since independent India
    # did not annex Goa until December 1961. The same measurement also found
    # IND-1800-1886 holding LKA-1800-2025 (Ceylon, 65,955 km2, 99.5%), a separate Crown
    # Colony that was likewise never British India -- invisible here only because that
    # period holds two. Both are filed as issue 84 rather than left implied by this
    # exemption.
    "IND-1886-1893", "IND-1893-1914", "IND-1914-1937", "IND-1937-1947",
})

# Containers that are DEFECTS, tracked so the gate stays useful while they are
# open. Bidirectional: one that stops containing must be removed from this set, so
# the list shrinks as the polygons are fixed.
# Empty: issue 45 is FIXED. RUS-1991-2014 carried the USSR polygon because
# `polygon_feature_year: 1991` matched six CShapes time-steps and the winner was
# decided by shapefile order; 1992 selects the durable 1991-2014 step and the row now
# measures 16,882,058 km2 instead of 21,824,142. Kept as an empty frozenset rather
# than deleted so a regression names the container.
TRACKED_DEFECTS = frozenset()

# Family pairs whose consecutive polygons do not overlap. Tracked, not accepted.
# frozenset(...) rather than a bare {...}: when the last entry is removed — which
# is the goal, once issue 46 is fixed — a bare literal becomes an empty DICT, and
# `dict - set` raises TypeError. The gate would crash precisely when the data became
# correct. Found by actually emptying it rather than assuming.
# Empty: issue 46 is FIXED. IRN-1800-1828 was bound to Cliopatria's "United States
# of America" and is now bound to "Qajar Dynasty" at 1800, so the two Iran periods
# overlap as they should. Kept as an empty frozenset rather than deleted so a
# regression names the pair.
KNOWN_DISCONTINUOUS = frozenset({
    # NOT defects, and not discontinuities either -- this check has mis-read its own input.
    #
    # It groups families by CODE PREFIX and sorts by start_year, so IDN-BLB, IDN-JVM and IDN-OTH
    # all become the "IDN family" and, because all three start in 1949, an arbitrary sort order
    # turns them into "consecutive periods". They are not consecutive; they are a SIMULTANEOUS
    # PARTITION of Indonesia for 1949-1951 -- Java, Bali/Lombok, and everything else -- and 0%
    # overlap is the correct and required outcome for a partition, the exact opposite of the
    # mis-binding this check exists to catch.
    #
    # Tracked rather than fixing the grouping, because the prefix heuristic is right for every
    # ordinary family and a partition is rare. If a second one appears, teach the check about
    # polity_type instead of adding two more lines here.
    "IDN-BLB-1949-1951 / IDN-JVM-1949-1951",
    "IDN-JVM-1949-1951 / IDN-OTH-1949-1951",
})

ap = argparse.ArgumentParser()
# KNOWN LIMITATION, measured 2026-07-29. The default of 3 was chosen to keep the
# baseline reviewable — at >=1 there are 95 containers, at >=2 there are 58, at >=3
# there are 33 — but it means a polygon that swallows exactly ONE coexisting polity is
# never reported, and that is arguably the commonest real error: a polygon one neighbour
# too large.
#
# The instance that used to be cited here is FIXED (issue 21, closed 2026-08-05):
# ITS-1908-1960 used CShapes 520, all of Somalia at 635,888 km2, and contained
# BSS-1884-1960 (British Somaliland, 171,633 km2) at 100%. It is now a `constructed`
# 520 MINUS 521 at 464,286 km2 and the two no longer intersect at all.
#
# THE LIMITATION IS UNCHANGED, which is why this note stays. That pair was found by
# reading the data, not by this check -- a single swallow is invisible at the default
# threshold however wrong it is, and the fix removed the instance rather than the blind
# spot. Another single-swallow error of the same shape would be equally unreported.
#
# Lowering the default to 1 would require judging all 37 single-swallow cases, and most
# ARE legitimate history — GBR-1800-1921 contains IRL-1800-1921, ESP-1800-2025 contains
# ICN-1800-2025, IND-1947-1949 contains HYD-1724-1948, SRB-2008-2025 contains
# KOS-2008-2025, and SLE-1886-1889 contains GMB-1800-2025 because CShapes 451 for
# 1886-1889 is the British West African Settlements, which included Gambia until 1888.
# Enumerating those as legitimate without verifying each would be the guessing this
# check exists to prevent, so the threshold is left at 3 and the gap recorded here
# rather than papered over.
ap.add_argument("--min-contained", type=int, default=3,
                help="report a polity that contains at least this many others; see the "
                     "KNOWN LIMITATION note above about single-swallow cases")
ap.add_argument("--overlap", type=float, default=0.90,
                help="fraction of the smaller polity that must lie inside")
ap.add_argument("--continuity", type=float, default=0.50,
                help="minimum overlap between consecutive periods of one family")
A = ap.parse_args()

g = gpd.read_file(GPKG)
g = g[g.geometry.notna() & ~g.geometry.is_empty]
g = g[~g["wiki_status"].isin(DEAD_STATUS)].copy()
for col in ("start_year", "end_year"):
    g[col] = pd.to_numeric(g[col], errors="coerce")

eq = g.to_crs(EQUAL_AREA).copy()
# buffer(0) heals self-intersections that would otherwise make .area unreliable.
eq["geometry"] = eq.geometry.buffer(0)
eq["area_km2"] = eq.geometry.area / 1e6

pairs = gpd.sjoin(
    eq[["polity_code", "geometry"]], eq[["polity_code", "geometry"]],
    how="inner", predicate="intersects",
)
pairs = pairs[pairs.polity_code_left != pairs.polity_code_right]

meta = eq.set_index("polity_code")[["start_year", "end_year", "area_km2"]]
geo = eq.set_index("polity_code")["geometry"]

contains = defaultdict(list)
for outer, inner in zip(pairs.polity_code_left, pairs.polity_code_right):
    # Same prefix = successive periods of one territory, not two places.
    if outer.split("-")[0] == inner.split("-")[0]:
        continue
    mo, mi = meta.loc[outer], meta.loc[inner]
    # A shared transition year (one ends where the other starts) is not coexistence.
    if not (mo.start_year < mi.end_year and mi.start_year < mo.end_year):
        continue
    if mi.area_km2 <= 0 or mi.area_km2 >= mo.area_km2:
        continue
    if geo.loc[inner].intersection(geo.loc[outer]).area / geo.loc[inner].area > A.overlap:
        contains[outer].append(inner)

observed = {k for k, v in contains.items() if len(v) >= A.min_contained}
print(f"{len(eq)} live polities with geometry")
print(f"containers holding >={A.min_contained} contemporaneous polities of other "
      f"families: {len(observed)}")

for code in sorted(observed & TRACKED_DEFECTS):
    inside = sorted(contains[code])
    print(f"\n  TRACKED DEFECT {code} contains {len(inside)}: "
          f"{', '.join(inside[:6])}{' ...' if len(inside) > 6 else ''}")

problems = []
for code in sorted(observed - LEGITIMATE_CONTAINERS - TRACKED_DEFECTS):
    inside = sorted(contains[code])
    problems.append(
        f"NEW container {code} holds {len(inside)} contemporaneous polities of "
        f"other families: {', '.join(inside[:6])}"
        + (" ..." if len(inside) > 6 else "")
    )
for code in sorted((LEGITIMATE_CONTAINERS | TRACKED_DEFECTS) - observed):
    problems.append(
        f"{code} is listed as a container but no longer contains "
        f">={A.min_contained} others — remove it from the list"
    )

# ---------- CONTINUITY ----------
# A family's consecutive periods describe the same territory at different times, so
# their polygons must overlap heavily. When they do not, one is bound to the wrong
# feature. This is the only check that finds a mis-binding of PLAUSIBLE SIZE:
# IRN-1800-1828 carries Cliopatria's "United States of America" (its
# polygon_feature_id says so literally) and sits in North America, but the USA in
# 1815 measured ~1,586,287 km2 against Iran's ~1,621,564 — a ratio of 0.98, so
# every area-based check passes it. Magnitude cannot detect position.
eq["prefix"] = eq.polity_code.str.split("-").str[0]
discontinuous = []
for _prefix, fam in eq.groupby("prefix"):
    if len(fam) < 2:
        continue
    # Sort on (start_year, polity_code), NOT start_year alone. A tie makes the order arbitrary,
    # and arbitrary order changes which rows are ADJACENT -- so the pairs this check reports differ
    # between machines and any baseline of them is unpinnable. That is not hypothetical: the three
    # IDN-*-1949-1951 rows all start in 1949, and on 2026-08-07 this gate passed locally while
    # failing in CI with the SAME data, reporting IDN-JVM/IDN-BLB and IDN-BLB/IDN-OTH where the
    # local run had reported IDN-BLB/IDN-JVM and IDN-JVM/IDN-OTH. Same three rows, two pairings.
    fam = fam.sort_values(["start_year", "polity_code"])
    codes, geos, areas = list(fam.polity_code), list(fam.geometry), list(fam.area_km2)
    for i in range(len(fam) - 1):
        smaller = min(areas[i], areas[i + 1])
        if smaller <= 0:
            continue
        frac = geos[i].intersection(geos[i + 1]).area / (smaller * 1e6)
        if frac < A.continuity:
            discontinuous.append((codes[i], codes[i + 1], frac))

print(f"\nconsecutive same-family periods overlapping <{A.continuity:.0%}: "
      f"{len(discontinuous)}")
for a, b, frac in sorted(discontinuous, key=lambda r: r[2]):
    pair = f"{a} / {b}"
    if pair in KNOWN_DISCONTINUOUS:
        print(f"  TRACKED DEFECT {pair}  overlap {frac:.0%}")
    else:
        problems.append(
            f"NEW discontinuity {pair}: consecutive periods of one family overlap "
            f"only {frac:.0%} — one polygon is probably bound to the wrong feature"
        )
observed_pairs = {f"{a} / {b}" for a, b, _ in discontinuous}
for pair in sorted(KNOWN_DISCONTINUOUS - observed_pairs):
    problems.append(
        f"{pair} is tracked as discontinuous but now overlaps — remove it from "
        f"KNOWN_DISCONTINUOUS"
    )

if problems:
    print(f"\nFAIL: {len(problems)} change(s)\n")
    for p in problems:
        print(f"  {p}")
    print("\n  A polygon that swallows a coexisting polity double-counts its "
          "territory in any spatial or area-weighted use.")
    sys.exit(1)

print("\nPASS: every container is either documented history or a tracked defect")
