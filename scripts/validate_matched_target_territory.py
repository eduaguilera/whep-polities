#!/usr/bin/env python3
"""A `matched` coverage segment must name a polity of comparable territory.

`matched` is the strongest disposition the harness has. The schema defines it as:

    matched: an existing polity covers these years and the source OBSERVED the territory then.

So it asserts two things, and the second is about identity: the polity IS the territory the source
was reporting. When a reporting unit's years are matched to its CONTAINER instead, the assertion is
false and the consequence is not cosmetic -- the data lands on the container.

WHAT THAT COSTS, measured. `ITA-1919-2025` already receives Italy's own national labels ('italy',
'Italy' from faostat, 'ltaly' from fao1952). Five Italian NUTS regions -- ITC1, ITH4, ITH5, ITI2,
ITI4 -- each carry a `matched` segment for 1919-1969 naming that same row. Executing those as
aliases would put five regions' values and the country's own value on one polity for the same years,
and `.prepare_historical_production()` in the WHEP R package collapses duplicate keys with
`mean(value)`. The published number would be the average of Italy and five of its parts.

I nearly did exactly that. Having found 22 segments whose target existed and had no alias, the
obvious move was to write the aliases and recover ~250,000 rows. Checking what already routed to
those targets is what stopped it.

`polity_type` IS NOT THE DISCRIMINATOR, which is why this gate measures area instead.
`NSW-1800-1901` is typed `national` and is exactly New South Wales; Australia's pre-federation
colonies are all typed that way because they were self-governing. Matching AUS-NEWSOUTHWALES to it
is correct. The ratio of the target's polygon to the reporting unit's own separates the cases
cleanly:

    1.00 - 1.05x   the same territory -- Japan's 47 prefectures, Spain's provinces, and each
                   Australian colony matched to its own colonial row. Legitimate.
    1.72 - 2.35x   the Northern Territory inside South Australia, which administered it until
                   1911. A container, but a recorded decision, and below the threshold.
    5.70 - 112.8x  a province or region matched to its whole country.

Threshold is 3.0x. The 25 cases above it that this gate found when it landed were resolved in
issue 657 -- `back_cast` to the unit's own modern polity, or `matched` to an era polity of the same
territory -- so nothing is baselined. Bidirectional: a NEW one fails, and a resolved
one must be removed from the baseline or this fails too.

`back_cast` AND `proposed` SEGMENTS ARE HELD TO THE SAME TEST. The first version measured only
`matched`, and 12 `back_cast` segments over five units (CHL-AP, CHL-AR, COL-AMAZONAS,
COL-GUAINIA, ITA-ITF6) named the national row at 10-44x the unit's area while the alias registry
routed the unit's own polity. A back_cast is a reconstruction FOR the reporting unit's territory;
its target is that territory's polity, not the country that held it. Re-recorded 2026-09-24.

SKIPS ARE COUNTED AND PINNED. A segment this cannot measure -- unparseable coverage, a page or a
target with no polygon, years that are not integers -- used to be skipped silently, so a gate that
measured nothing would still print PASS. Each kind is now printed, and the counts are pinned in
EXPECTED_SKIPS: a new skip fails, and so does a pinned one that went away.

MISSING PREREQUISITES FAIL. The ledger and the GeoPackage are committed, so their absence is a
broken checkout, not an environment to tolerate. geopandas may be absent on a laptop (SKIP, loudly)
but not in CI, which installs it: there a missing import fails instead of printing SKIP and exit 0.

Reads only committed files plus the committed GeoPackage, so it runs anywhere.

Usage:
  python3 scripts/validate_matched_target_territory.py
"""
import csv
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(REPO, "pipelines/agent-harness/state/routing_verdicts.csv")
POLDB = os.path.join(REPO, "data/final/polities_database.csv")
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")

# Above this, the target is a container rather than the territory the source observed.
MAX_RATIO = 3.0

# (unit_id, start_year, end_year, target) knowingly matched to a container. Empty since issue
# 657 was resolved: the 25 segments baselined here (Italian NUTS regions, CHL-LI, COL-GUAVIARE,
# MEX-BAJACALIFORNIA, ARG-SANTACRUZ, and three Australian colonies' 1900) were re-recorded --
# as `back_cast` to the unit's own modern polity where no era polity of the same territory
# exists, and as `matched` to the colony itself for the Australian 1900s, whose colonial rows
# (end_year exclusive, 1901) already covered that year. Keep it empty: a new entry needs a
# reason the rule above cannot express.
BASELINE = frozenset()

# The dispositions whose target must be the reporting unit's own territory.
DISPOSITIONS = ("matched", "back_cast", "proposed")

# Segments this gate could NOT measure, by reason, pinned at their measured counts (2026-09-24).
# Bidirectional: a new skip fails (something stopped being checkable) and a count that drops fails
# too (lower the pin so the coverage is held). Informational counts -- rows outside this gate's
# scope -- are printed but not pinned; see SCOPE below.
EXPECTED_SKIPS = {
    "coverage_json does not parse": 0,
    "page polity has no polygon": 0,
    "segment target has no polygon": 0,
    "segment years are not integers": 0,
}


def _in_ci() -> bool:
    return bool(os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"))


def main() -> int:
    # Both files are COMMITTED: their absence is a broken checkout, never a reason to pass.
    for path in (LEDGER, GPKG):
        if not os.path.exists(path):
            print(f"FAIL: {os.path.relpath(path, REPO)} absent -- it is committed, so this "
                  f"checkout is broken; the gate cannot run and must not pass")
            return 1
    try:
        import geopandas as gpd
    except ImportError:
        if _in_ci():
            print("FAIL: geopandas unavailable in CI, which installs it -- the gate would "
                  "measure nothing")
            return 1
        print("SKIP: geopandas unavailable (outside CI only; CI fails here instead)")
        return 0

    csv.field_size_limit(sys.maxsize)
    with open(POLDB, encoding="utf-8") as fh:
        pol = {r["polity_code"]: r for r in csv.DictReader(fh)}

    g = gpd.read_file(GPKG).to_crs("ESRI:54034")
    area = {r["polity_code"]: r.geometry.area / 1e6 for _, r in g.iterrows()
            if r.geometry is not None and not r.geometry.is_empty}

    skips = {k: [] for k in EXPECTED_SKIPS}
    scope = {"no coverage_json": 0, "page polity not subnational": 0,
             "segment names no polity (proposed, authored on the page)": 0}
    measured = {d: 0 for d in DISPOSITIONS}
    found = {}
    with open(LEDGER, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            raw = (r.get("coverage_json") or "").strip()
            if not raw:
                scope["no coverage_json"] += 1
                continue
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                skips["coverage_json does not parse"].append(r["unit_id"])
                continue
            segs = parsed.get("segments", []) if isinstance(parsed, dict) else parsed
            page = (r.get("page_polity_code") or r.get("matched_polity_code") or "").strip()
            if pol.get(page, {}).get("polity_type") != "subnational":
                scope["page polity not subnational"] += 1
                continue
            mine = area.get(page)
            if not mine:
                skips["page polity has no polygon"].append(f"{r['unit_id']} ({page})")
                continue
            for s in segs:
                disp = s.get("disposition")
                if disp not in DISPOSITIONS:
                    continue
                target = (s.get("polity_code") or "").strip()
                if not target:
                    if disp == "proposed":
                        scope["segment names no polity (proposed, authored on the page)"] += 1
                    else:
                        skips["segment target has no polygon"].append(
                            f"{r['unit_id']} {disp} (no polity_code)")
                    continue
                theirs = area.get(target)
                if not theirs:
                    skips["segment target has no polygon"].append(
                        f"{r['unit_id']} {disp} -> {target}")
                    continue
                try:
                    key = (r["unit_id"], int(s["start_year"]), int(s["end_year"]), target)
                except (KeyError, TypeError, ValueError):
                    skips["segment years are not integers"].append(f"{r['unit_id']} {disp}")
                    continue
                measured[disp] += 1
                ratio = theirs / mine
                if ratio <= MAX_RATIO:
                    continue
                found[key] = (ratio, r["country"], page, disp)

    print("segments measured: " + ", ".join(f"{d} {n}" for d, n in measured.items()))
    print("out of scope (not pinned): " + ", ".join(f"{k} {n}" for k, n in scope.items()))
    print("skipped, unmeasurable (pinned): "
          + ", ".join(f"{k} {len(v)}" for k, v in skips.items()))
    drift = {k: (len(v), EXPECTED_SKIPS[k]) for k, v in skips.items()
             if len(v) != EXPECTED_SKIPS[k]}
    if drift:
        print(f"FAIL: skip count(s) moved off their pin -- a segment this gate cannot measure is "
              f"one it silently passes:")
        for k, (have, pin) in drift.items():
            print(f"  {k}: {have}, pinned {pin}")
            for item in skips[k][:10]:
                print(f"      {item}")
        print("Fix what became unmeasurable, or update EXPECTED_SKIPS (both directions).")
        return 1

    stale = sorted(set(BASELINE) - set(found))
    if stale:
        print(f"FAIL: {len(stale)} baseline entr(ies) no longer match a container -- remove them:")
        for k in stale:
            print(f"  {k[0]} {k[1]}-{k[2]} -> {k[3]}")
        return 1

    new = {k: v for k, v in found.items() if k not in BASELINE}
    if new:
        kinds = sorted({v[3] for v in new.values()})
        print(f"FAIL: {len(new)} {'/'.join(f'`{d}`' for d in kinds)} segment(s) name a polity far "
              f"larger than the territory the source reported\n")
        for (unit, lo, hi, target), (ratio, country, page, disp) in sorted(
                new.items(), key=lambda kv: -kv[1][0]):
            print(f"  {unit} ({country}) {lo}-{hi} {disp} -> {target}")
            print(f"      {ratio:.1f}x the area of {page}, this unit's own polity. The segment "
                  f"asserts the data is FOR that territory; at this ratio it is a part of it, and "
                  f"routing the data there attributes a region's values to its container -- "
                  f"which already receives its own national labels.")
        print("\nUse `back_cast` to the unit's OWN polity if the values are a reconstruction onto "
              "a boundary that did not exist yet, or create the polity for the era. See issue 657.")
        return 1

    print(f"PASS: every {'/'.join(DISPOSITIONS)} segment names a polity within {MAX_RATIO}x "
          f"the reporting unit's own territory ({len(BASELINE)} baselined)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
