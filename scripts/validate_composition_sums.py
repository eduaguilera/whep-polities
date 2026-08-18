#!/usr/bin/env python3
"""Cross-check banked part/whole relations against each other: sums, containment, double counts.

Every other guard here checks ONE row, ONE alias or ONE polygon in isolation. Issue 10 asks for
the missing class: checks that compare banked conclusions **against each other**, because two
sessions can be wrong the same way but they cannot both be right if their conclusions contradict
each other arithmetically. The highest-yield such identity in this database is *parts sum to the
whole* -- a federation's colonies against the federation, an island group's islands against the
group, a combined reporting row against the two states it combines.

The relations live in `pipelines/polity-autoimprove/state/polity_composition.csv`, one row per
(whole, part) pair, each carrying the wiki page that grounds the membership. Areas are MEASURED
from the GeoPackage, never read from `polygon_area_km2` -- 520 of the live rows with geometry have
no recorded area at all, so a check that needed one would skip most of the database.

Four checks:

  R  Registry integrity. Both codes exist, are live, have geometry, their spans overlap, and the
     evidence page exists. A registry that has quietly stopped referring to real rows would make
     every other check here vacuous.

  A  Partition sums. Where the parts are declared to exhaust the whole, sum(parts) must equal the
     whole within --tolerance. This is what independently verifies a composed_union recipe: the
     union's area is one number and the enumerated members' areas are another, and the repo has
     been bitten three times by a recipe that named the wrong features while declaring the right
     area (IDN-JVM-1949-1951 attached North Sulawesi and dropped Jawa Barat; SER-1918-1945 and
     CAN-1800-1866 the same shape). Ten of the eleven partitions land inside 0.9917-1.0059.

  B  Containment. Every part must lie inside its whole. A part that sums correctly but sits
     somewhere else is a mis-binding that check A cannot see.

  C  Data double counts. For each pair, the sources that route labels to BOTH the whole and the
     part over overlapping years are computed from `label_alias_map.csv` and must match the
     `overlap_sources` column exactly. Summing such a pair double-counts, which is the shape of
     issue 14 (Djibouti coffee) and issue 143's class 2. The check does not decide the accounting
     -- it forbids an overlap from going UNRECORDED, so a new alias that creates one fails here.
     `disposition` says what is known: `separate_series` where the source demonstrably reports the
     two as distinct areas, `sum_risk` where it does not and the item sets cannot be compared from
     committed data (item is not a column of the alias map; that comparison needs layer B, which
     is gitignored and so cannot run in CI).

What check A found on the run that added it: **the AOF federation's parts exceed the federation
by 272,441 km2** (4,895,509 against 4,623,068, 1.0589x). The member set is right -- the union of
the eight member polygons equals the AOF polygon to 70 km2, 0.0015% -- so the excess is a genuine
double count inside the members: MLI-1890-1960 carries CShapes cowcode 432 at the **1905 vintage**,
which predates Upper Volta's creation in 1919, and 272,319 of BFA-1947-1960's 272,322 km2 (99.999%)
lies inside it. mli-1890-1960.md already documents the vintage choice and says the 1947 snapshot
(1,252,292 km2) is the better fit for post-1947 data; this check is what turns that caveat into a
number. Fixing it is a vintage/span decision for MLI-1890-1960 rather than a registry edit, so the
pair is baselined with its measurement.

Usage:
  python3 scripts/validate_composition_sums.py [--tolerance 0.02] [--containment 0.95]
"""
import argparse
import csv
import os
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLITIES_CSV = os.path.join(REPO, "data/final/polities_database.csv")
POLITIES_GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")
ALIAS_MAP = os.path.join(REPO, "data/final/label_alias_map.csv")
REGISTRY = os.path.join(
    REPO, "pipelines/polity-autoimprove/state/polity_composition.csv"
)
OVERLAP_TABLE = os.path.join(
    REPO, "pipelines/polity-autoimprove/state/composition_overlaps.csv"
)

DEAD_STATUS = ("retired", "superseded")
RELATIONS = ("partition", "nested")
DISPOSITIONS = ("none", "separate_series", "sum_risk")

# Wholes whose parts do not sum to them, with the reason. See the docstring.
#
# AOF-1895-1960  sum 4,895,509 km2 against 4,623,068 (1.0589x, +272,441). Not a wrong member
#                set -- the eight members' UNION equals the AOF polygon to 70 km2. The excess is
#                MLI-1890-1960's 1905-vintage polygon still containing Upper Volta, which
#                BFA-1947-1960 also claims: 272,319 km2, 99.999% of BFA. Removing this baseline
#                requires MLI-1890-1960 to be re-bound or split at 1919/1947, not a registry edit.
SUM_BASELINE = frozenset({"AOF-1895-1960"})

# Pairs where the part is genuinely inside the whole historically but the polygons do not agree.
#
# JPN-1895-1945 / RYU-1937-1945  1,613 of the Ryukyus' 2,337 km2 lies inside the Japanese Empire
#                polygon (69.0%), leaving 724 km2 outside it. Okinawa Prefecture was Japanese from
#                1879, so the relation is right; the shortfall is GADM island outlines against a
#                CShapes national outline at a different resolution. Small in absolute terms and
#                not a binding error, so recorded rather than chased.
CONTAINMENT_BASELINE = frozenset({("JPN-1895-1945", "RYU-1937-1945")})


def year(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tolerance", type=float, default=0.02)
    ap.add_argument("--containment", type=float, default=0.95)
    args = ap.parse_args()

    try:
        import geopandas as gpd
        from shapely.validation import make_valid
    except ImportError as exc:
        print(f"FAIL: geopandas/shapely unavailable ({exc})")
        return 2
    for path in (POLITIES_CSV, POLITIES_GPKG, ALIAS_MAP, REGISTRY):
        if not os.path.exists(path):
            print(f"FAIL: {path} missing; run scripts/build_database.py first")
            return 2

    with open(REGISTRY, encoding="utf-8") as fh:
        registry = [r for r in csv.DictReader(fh) if (r.get("whole_code") or "").strip()]
    if not registry:
        print(f"FAIL: {REGISTRY} declares no part/whole relation, so nothing is cross-checked")
        return 2

    with open(POLITIES_CSV, encoding="utf-8") as fh:
        rows = {r["polity_code"]: r for r in csv.DictReader(fh)}

    problems = []

    # --- check R: the registry refers to real, live, contemporaneous rows -----------------
    for r in registry:
        whole, part = r["whole_code"].strip(), (r.get("part_code") or "").strip()
        tag = f"{whole} <- {part}"
        if (r.get("relation") or "").strip() not in RELATIONS:
            problems.append(f"R {tag}: relation must be one of {RELATIONS}")
        if (r.get("disposition") or "").strip() not in DISPOSITIONS:
            problems.append(f"R {tag}: disposition must be one of {DISPOSITIONS}")
        evidence = (r.get("evidence") or "").strip()
        if not evidence or not os.path.exists(os.path.join(REPO, evidence)):
            problems.append(f"R {tag}: evidence page {evidence!r} does not exist")
        for code in (whole, part):
            row = rows.get(code)
            if row is None:
                problems.append(f"R {tag}: {code} is not a row of the database")
            elif (row.get("wiki_status") or "").strip() in DEAD_STATUS:
                problems.append(
                    f"R {tag}: {code} is {row['wiki_status']}, so the relation is stale"
                )
        wr, pr = rows.get(whole), rows.get(part)
        if wr and pr:
            lo = max(year(wr["start_year"]), year(pr["start_year"]))
            hi = min(year(wr["end_year"]), year(pr["end_year"]))
            if lo >= hi:
                problems.append(
                    f"R {tag}: spans {wr['start_year']}-{wr['end_year']} and "
                    f"{pr['start_year']}-{pr['end_year']} do not overlap, so no part/whole "
                    f"relation can hold between these two rows"
                )

    codes = {c for r in registry for c in (r["whole_code"].strip(), (r.get("part_code") or "").strip())}
    frame = gpd.read_file(POLITIES_GPKG)
    frame = frame[frame["polity_code"].isin(codes)].copy()
    frame = frame[~frame.geometry.isna() & ~frame.geometry.is_empty]
    # Reproject FIRST and validate after: make_valid on the lon/lat geometry still left
    # side-location conflicts that made .intersection() raise in the equal-area CRS.
    frame = frame.to_crs("ESRI:54034")
    frame["geometry"] = frame.geometry.map(make_valid).buffer(0)
    geom = dict(zip(frame["polity_code"], frame.geometry))
    area = {c: g.area / 1e6 for c, g in geom.items()}
    for code in sorted(codes):
        if code not in geom and code in rows:
            problems.append(
                f"R {code}: registered in a composition but carries no geometry, so neither "
                f"its sum nor its containment can be checked"
            )

    # --- check A: partitions must sum to their whole ---------------------------------------
    parts_of = defaultdict(list)
    for r in registry:
        if (r.get("relation") or "").strip() == "partition":
            parts_of[r["whole_code"].strip()].append((r.get("part_code") or "").strip())

    print(f"part/whole relations registered: {len(registry)}")
    print(f"partitions checked for the sum identity: {len(parts_of)}\n")
    off = set()
    for whole in sorted(parts_of):
        members = parts_of[whole]
        if whole not in area or any(m not in area for m in members):
            continue
        total = sum(area[m] for m in members)
        ratio = total / area[whole] if area[whole] else 0.0
        flag = "" if abs(ratio - 1.0) <= args.tolerance else "  <-- off"
        if flag:
            off.add(whole)
        print(
            f"   {whole:<18}{area[whole]:>12,.0f} km2   parts {total:>12,.0f}"
            f"   ratio {ratio:.4f}  ({len(members)} parts){flag}"
        )
        if flag:
            worst = max(members, key=lambda m: area[m])
            print(
                f"      largest part {worst} {area[worst]:,.0f} km2; difference "
                f"{total - area[whole]:+,.0f} km2"
            )

    for whole in sorted(off - SUM_BASELINE):
        members = parts_of[whole]
        total = sum(area[m] for m in members)
        problems.append(
            f"A {whole}: its {len(members)} declared parts sum to {total:,.0f} km2 against the "
            f"whole's {area[whole]:,.0f} ({total / area[whole]:.4f}x, {total - area[whole]:+,.0f}). "
            f"Either a part is bound to the wrong feature, two parts claim the same ground, or a "
            f"member is missing from the registry"
        )
    for whole in sorted(SUM_BASELINE - off):
        problems.append(
            f"A {whole} is baselined as not summing to its parts but now does — remove it from "
            f"SUM_BASELINE and say what was fixed"
        )

    # --- check B: every part must lie inside its whole -------------------------------------
    outside = set()
    for r in registry:
        whole, part = r["whole_code"].strip(), (r.get("part_code") or "").strip()
        if whole not in geom or part not in geom or not area.get(part):
            continue
        inside = geom[whole].intersection(geom[part]).area / 1e6
        share = inside / area[part]
        if share < args.containment:
            outside.add((whole, part))
            print(
                f"\n   only {share * 100:.1f}% of {part} lies inside {whole} "
                f"({area[part] - inside:,.0f} km2 outside)"
            )
    for pair in sorted(outside - CONTAINMENT_BASELINE):
        whole, part = pair
        inside = geom[whole].intersection(geom[part]).area / 1e6
        problems.append(
            f"B {whole} <- {part}: only {inside / area[part] * 100:.1f}% of the part lies inside "
            f"the whole. A part that is declared inside a whole and is not there is a polygon "
            f"binding error, whatever its area says"
        )
    for pair in sorted(CONTAINMENT_BASELINE - outside):
        problems.append(
            f"B {pair[0]} <- {pair[1]} is baselined as not contained but now is — remove it from "
            f"CONTAINMENT_BASELINE"
        )

    # --- check C: data reaching both sides of a pair must be recorded ----------------------
    alias = defaultdict(list)
    with open(ALIAS_MAP, encoding="utf-8") as fh:
        for a in csv.DictReader(fh):
            src = (a.get("source") or "").strip()
            ys, ye = year(a.get("year_start")), year(a.get("year_end"))
            # A BLANK `source` IS A WILDCARD, NOT AN ABSENCE. Such an alias routes its label from
            # ANY source, which is exactly how the matchers apply it. Skipping those rows made this
            # check blind to 188 of the alias map's 992 rows (19%), and to 62 polities reachable
            # ONLY that way -- among them AOF-1895-1960, which is itself a registered whole here.
            # Nine real overlaps were invisible as a result, including SYL-1944-1953 <- SYR-1946-1967
            # (fao1952 routes 'Syria and Lebanon' to the whole and 'Syria' to the part) and
            # JPN-1895-1945 <- RYU-1937-1945. Check C exists to stop a double count going
            # unrecorded; a fifth of the routing was exempt from it.
            if ys is not None and ye is not None:
                alias[a["polity_code"]].append((src, ys, ye, a.get("source_label") or ""))

    # The alias map is not the whole routing. Of the 832 label->polity routings the matcher made,
    # only 205 came from an alias; 627 (75%) resolved by iso/name/tokenset, and a part reached that
    # way was invisible here -- so a whole and its own part could both receive data undeclared. Those
    # routings are computed from the layer-B panel, which is gitignored and absent in CI, so
    # 19_composition_overlaps.py writes them to a tracked table and this reads it. 13 real overlaps
    # were hidden, among them AOI-1936-1941 <- ERI-1889-1952 with 66 shared cells.
    table = {}
    if os.path.exists(OVERLAP_TABLE):
        with open(OVERLAP_TABLE, encoding="utf-8") as fh:
            for t in csv.DictReader(fh):
                table[(t["whole_code"], t["part_code"], t["source"])] = t

    overlaps = 0
    narrowable = []
    for r in registry:
        whole, part = r["whole_code"].strip(), (r.get("part_code") or "").strip()
        found = {}
        for wsrc, wys, wye, wlab in alias.get(whole, []):
            for psrc, pys, pye, plab in alias.get(part, []):
                # Wildcard on either side matches; two named sources must be equal. A pair matched
                # only through two wildcards is recorded as `(any)` -- it says data can reach both
                # sides without naming which source does it, which still has to be declared.
                if wsrc and psrc and wsrc != psrc:
                    continue
                lo, hi = max(wys, pys), min(wye, pye)
                if lo <= hi:
                    found.setdefault(wsrc or psrc or "(any)", (lo, hi, wlab, plab))
        # Overlaps the alias map cannot express, from the tracked table.
        for (tw, tp, tsrc), t in table.items():
            if tw == whole and tp == part and tsrc not in found:
                found[tsrc] = (t["year_first"], t["year_last"],
                               t["whole_labels"], t["part_labels"])

        declared = {
            s.strip()
            for s in (r.get("overlap_sources") or "").split(";")
            if s.strip()
        }
        if found:
            overlaps += 1
            for src, (lo, hi, wlab, plab) in sorted(found.items()):
                print(
                    f"   overlap {src:<26} {whole} <- {part}  {lo}-{hi}"
                    f"  {wlab!r} / {plab!r}"
                )
        tag = f"{whole} <- {part}"
        for src in sorted(set(found) - declared):
            lo, hi, wlab, plab = found[src]
            problems.append(
                f"C {tag}: {src} routes {wlab!r} to the whole and {plab!r} to the part over "
                f"{lo}-{hi}, so summing the two double-counts, and this is not recorded in "
                f"overlap_sources"
            )
        for src in sorted(declared - set(found)):
            problems.append(
                f"C {tag}: overlap_sources claims {src} feeds both sides but neither an "
                f"overlapping alias pair nor a row in composition_overlaps.csv says so — remove "
                f"it, or re-run 19_composition_overlaps.py --write if the routing changed"
            )
        disposition = (r.get("disposition") or "").strip()
        if found and disposition == "none":
            problems.append(
                f"C {tag}: data reaches both sides but disposition is `none`; say whether the "
                f"source reports them separately (`separate_series`) or a sum would double-count "
                f"(`sum_risk`)"
            )
        if not found and disposition != "none":
            problems.append(
                f"C {tag}: disposition is {disposition!r} but no source feeds both sides"
            )

        # `separate_series` vs `sum_risk` is not a matter of opinion: it turns on whether the two
        # sides carry the same (item, unit, year) cells, which 19_composition_overlaps.py counts
        # from the panel. This is the one part of check C that used to rest on trust -- and the
        # counts disagree with the intuitive reading in both directions. JPN-1895-1945 <-
        # RYU-1937-1945 shares ZERO cells in iia and mitchell, so Ryukyu really is reported apart
        # from Japan; AOI-1936-1941 <- ERI-1889-1952 shares 66.
        # NOTE ON WHAT ZERO SHARED CELLS DOES AND DOES NOT MEAN. It means no (item, unit, year)
        # cell appears on both sides, so a per-cell SUM cannot double-count. It does NOT mean the
        # territories are disjoint: fao1952 publishes `british west indies windward islands` with
        # sugar and population and `british west indies dominica` with limes only, and the Windward
        # sugar figure still contains Dominica's ground. Safe to add up; not safe to read as "these
        # are different territories".
        measured = [t for (tw, tp, _s), t in table.items() if tw == whole and tp == part
                    and t["shared_cells"] != ""]
        if measured and disposition in ("separate_series", "sum_risk"):
            worst = max(int(t["shared_cells"]) for t in measured)
            if worst > 0 and disposition == "separate_series":
                problems.append(
                    f"C {tag}: disposition is `separate_series` but {worst} (item, unit, year) "
                    f"cells are present on BOTH sides, so a sum double-counts them"
                )
            if worst == 0 and disposition == "sum_risk":
                # NOT a failure, deliberately. `sum_risk` was the documented default for "could not
                # verify disjointness in CI", so an entry carrying it while measuring zero shared
                # cells is over-cautious, not wrong, and forcing the flip would silently weaken ten
                # entries that were set that way on purpose. The asymmetry is the point: the gate
                # exists to catch an UNDERSTATED risk, not to punish an overstated one.
                narrowable.append(
                    f"{tag}: `sum_risk` could be narrowed to `separate_series` — 0 shared cells"
                )

    print(f"\npairs whose data overlaps in at least one source: {overlaps}")
    if narrowable:
        print(f"over-cautious dispositions ({len(narrowable)}, not failures):")
        for n in narrowable:
            print(f"   {n}")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: every registered composition sums, contains and declares its data overlaps")
    return 0


if __name__ == "__main__":
    sys.exit(main())
