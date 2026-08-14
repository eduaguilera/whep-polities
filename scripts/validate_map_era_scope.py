#!/usr/bin/env python3
"""Check that the FAOSTAT area map stays inside the era it declares, and that the era is declared.

WHY THIS EXISTS (issue 200, filed from the consumer side). `data/final/faostat_area_polity_map.csv`
is built from what FAOSTAT actually REPORTS, which begins in 1961. The WHEP R package publishes
1850-2023, so for 111 years it has data and no map row: its pre-1961 series is the 1961 anchor grown
backwards by LUH2 land, and LUH2 is keyed on PRESENT-DAY ISO3. Having no upstream answer for those
years, it manufactured one -- 262 crosswalk rows matched by ISO3 PREFIX -- and a prefix rule cannot
express `TUR < 1913 -> OTT` or `PAK < 1947 -> IND` at all, because the stems differ. That is the
downstream defect. The upstream half of it is that THE MAP NEVER SAID WHERE IT STOPPED, so a
consumer could not tell "no row" (out of scope) from "no polity" (a gap to fill).

THE SCOPE DECISION, taken 2026-08-14 for issue 200, option (b) of the two the issue offered:

    The FAOSTAT area -> polity map describes the REPORTING ERA ONLY. It does not state, and will
    not state, which polity an area's back-cast pre-reporting years belong to.

Not because (a) -- publishing pre-1961 rows per area_code -- is more work, but because it is not
answerable on this key. Measured on the current map:

  * 36 of the 244 areas are not covered until AFTER 1961 at all (Armenia 1992, Czechia 1993,
    Palau 2000, Serbia 2006, South Sudan 2012, Belgium and Luxembourg 2000). There is no 1961
    anchor row to extend backwards for any of them, so "the area's pre-1961 polity" has no
    referent; and 38 areas have no row covering 1961 in the first place.
  * Where a pre-1961 answer DOES exist it lives on a different key. `label_alias_map.csv` resolves
    source LABELS ("Abyssinia" 1800-1889 -> `ETH-1800-1889`) and `pipelines/pre1961-matching`
    routes real historical observations to real historical polities. An area code is a modern
    reporting slot; a back-cast built on modern borders is not an observation of the entity that
    held that ground in 1850, and stamping a polity code on it would assert more than the data has.

So the pre-reporting era is declared OUT OF SCOPE, machine-readably, in
`polities_manifest.json -> faostat_area_map.coverage`, together with the rule that replaces the
prefix logic downstream: for years before an area's earliest row, use that area's ANCHOR row -- its
earliest -- and label the result a reconstruction, never a dated observation. That rule is only
total if every area has exactly one anchor, which is what arm B asserts.

WHAT THE 30 PRE-1961 ROWS IN THE MAP ARE, since they look like a contradiction and are not: every
one is a `registry` route with `rows_observed = 0` -- a no-data reporting area (Andorra, Greenland,
San Marino, the Falklands) whose span comes from its POLITY's period rather than from observed
FAOSTAT years, because there are no observed years. They assert an identity for a year in which the
polity demonstrably existed, and they carry no data. That is a different act from asserting a
pre-1961 identity for an area whose 1961+ data is being extrapolated, which is what arm A forbids.

THREE ARMS, all zero today, no baseline:

  A. OBSERVED ROW BEFORE THE REPORTING ERA  a row with `rows_observed > 0` whose `year_start` is
     earlier than 1961. The map would then be claiming a territorial identity for years FAOSTAT
     does not report -- option (a) arriving by accident, e.g. a matcher change that widens an
     observed span to its polity's period the way the registry branch legitimately does.
  B. AMBIGUOUS ANCHOR                       an area whose earliest `year_start` is shared by more
     than one row. The documented back-cast rule then has two answers and picks by row order,
     which is the same failure the prefix rule had.
  C. YEAR_START BEFORE THE POLITY EXISTS    a row starting before its own polity's `start_year`.
     `validate_map_area_year.py` compares the map's rows against EACH OTHER and against coverage at
     the `year_end` end (where four overshoots are pinned as final REPORTED years, issue 164);
     nothing asked the same question at the `year_start` end, which is the end this issue is about.

  D. THE DECLARATION ITSELF                 `faostat_area_map.coverage` must be present in the
     manifest and must say `pre_reporting_era: out-of-scope` with the same
     `reporting_era_first_year` this gate uses. A scope that is documented in one file and enforced
     against a different number is not documented. Skipped, not failed, if the manifest is absent.

Usage:
  python3 scripts/validate_map_era_scope.py
"""
from __future__ import annotations

import csv
import json
import os
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(REPO, "data/final/faostat_area_polity_map.csv")
DB = os.path.join(REPO, "data/final/polities_database.csv")
MANIFEST = os.path.join(REPO, "data/final/polities_manifest.json")

# The first year FAOSTAT reports. Declared here and republished by scripts/write_manifest.py into
# `faostat_area_map.coverage.reporting_era_first_year`; arm D compares the two so the published
# scope and the enforced scope cannot drift apart.
REPORTING_ERA_FIRST_YEAR = 1961


def _int(value: str, default: int | None = None) -> int | None:
    try:
        return int(float((value or "").strip()))
    except (TypeError, ValueError):
        return default


def main() -> int:
    for path in (MAP, DB):
        if not os.path.exists(path):
            print(f"SKIP: {os.path.relpath(path, REPO)} missing")
            return 0

    with open(MAP, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    with open(DB, encoding="utf-8") as fh:
        spans = {r["polity_code"]: r for r in csv.DictReader(fh)}

    by_area = defaultdict(list)
    for r in rows:
        by_area[_int(r.get("area_code"), -1)].append(r)

    observed_pre, ambiguous_anchor, before_polity = [], [], []

    for r in rows:
        ys = _int(r.get("year_start"))
        obs = _int(r.get("rows_observed"), 0) or 0
        if ys is None:
            continue
        if obs > 0 and ys < REPORTING_ERA_FIRST_YEAR:
            observed_pre.append((r["area_code"], r["source_label"], ys, r["polity_code"], obs))
        p = spans.get((r.get("polity_code") or "").strip())
        if p is not None:
            start = _int(p.get("start_year"))
            if start is not None and ys < start:
                before_polity.append((r["area_code"], r["polity_code"], ys, start))

    for area, group in sorted(by_area.items()):
        first = min(_int(r.get("year_start"), 9999) for r in group)
        heads = [r for r in group if _int(r.get("year_start"), 9999) == first]
        if len(heads) > 1:
            ambiguous_anchor.append(
                (area, first, sorted(r["polity_code"] for r in heads))
            )

    anchors = {
        a: min(_int(r.get("year_start"), 9999) for r in g) for a, g in by_area.items()
    }
    late = sum(1 for y in anchors.values() if y > REPORTING_ERA_FIRST_YEAR)
    early = sum(1 for y in anchors.values() if y < REPORTING_ERA_FIRST_YEAR)

    print(f"published mappings: {len(rows)} over {len(by_area)} FAOSTAT areas")
    print(f"reporting era declared to begin: {REPORTING_ERA_FIRST_YEAR}")
    print(
        f"areas whose anchor row starts before {REPORTING_ERA_FIRST_YEAR}: {early} "
        f"(no-data registry areas); after it: {late} (no anchor at the era's start)"
    )
    print(f"A. observed rows starting before the reporting era: {len(observed_pre)}")
    print(f"B. areas whose earliest year_start has more than one row: {len(ambiguous_anchor)}")
    print(f"C. rows starting before their own polity's start_year: {len(before_polity)}")

    problems = []
    for area, label, ys, code, obs in observed_pre:
        problems.append(
            f"area {area} ({label}) -> {code} starts {ys}, before the reporting era "
            f"({REPORTING_ERA_FIRST_YEAR}), while carrying {obs} observed rows. The map states the "
            f"reporting era only: a pre-{REPORTING_ERA_FIRST_YEAR} year of an area whose data is "
            f"back-cast has no stated polity, by the issue 200 decision. Either the span is wrong "
            f"or the scope declaration in polities_manifest.json has to change first"
        )
    for area, first, codes in ambiguous_anchor:
        problems.append(
            f"area {area} has {len(codes)} rows starting in {first} ({', '.join(codes)}), so its "
            f"ANCHOR is ambiguous and the documented pre-coverage rule -- use the earliest row -- "
            f"would pick by row order"
        )
    for area, code, ys, start in before_polity:
        problems.append(
            f"area {area} -> {code} starts {ys} but that polity starts {start}, so the map claims "
            f"the area was this polity before the polity existed"
        )

    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as fh:
            manifest = json.load(fh)
        cov = (manifest.get("faostat_area_map") or {}).get("coverage")
        if not cov:
            problems.append(
                "polities_manifest.json -> faostat_area_map has no `coverage` block, so the map "
                "publishes no scope at all and a consumer cannot tell 'out of scope' from 'gap' "
                "-- which is the defect issue 200 reported"
            )
        else:
            if cov.get("reporting_era_first_year") != REPORTING_ERA_FIRST_YEAR:
                problems.append(
                    f"the manifest declares the reporting era begins "
                    f"{cov.get('reporting_era_first_year')} while this gate enforces "
                    f"{REPORTING_ERA_FIRST_YEAR}: the published scope and the enforced scope have "
                    f"drifted apart"
                )
            if cov.get("pre_reporting_era") != "out-of-scope":
                problems.append(
                    "the manifest no longer declares `pre_reporting_era: out-of-scope`. That is "
                    "the issue 200 decision this gate enforces; changing it is a modelling change "
                    "and needs arm A revisited with it"
                )
            if not (cov.get("pre_coverage_rule") or "").strip():
                problems.append(
                    "`faostat_area_map.coverage.pre_coverage_rule` is empty, so the manifest "
                    "declares the pre-reporting era out of scope without saying what a consumer "
                    "should do instead -- which is how the 262 prefix-matched rows appeared"
                )
    else:
        print("D. SKIP: polities_manifest.json missing, scope declaration not checked")

    if problems:
        print(f"\nFAIL: {len(problems)} scope violation(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print(
        "\nPASS: every observed mapping stays inside the reporting era, every area has one "
        "anchor, no row predates its polity, and the scope is declared in the manifest"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
