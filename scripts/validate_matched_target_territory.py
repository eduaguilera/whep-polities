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

Threshold is 3.0x. Everything above it is baselined below, because the right disposition for those
years is a modelling decision (`back_cast`, or a polity for the era that does not exist yet) rather
than something this gate can pick -- see issue 657. Bidirectional: a NEW one fails, and a resolved
one must be removed from the baseline or this fails too.

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

# (unit_id, start_year, end_year, target) knowingly matched to a container. The right
# disposition is a modelling decision (issue 657), not this gate's call.
BASELINE = frozenset({
    ("AUS-TASMANIA", 1900, 1900, "AUS-1800-1901"),  # 112.8x
    ("CHL-LI", 1902, 1975, "CHL-1902-2025"),  # 45.4x
    ("CHL-LI", 1900, 1901, "CHL-1899-1902"),  # 42.6x
    ("ITA-ITH4", 1919, 1969, "ITA-1919-2025"),  # 38.7x
    ("ITA-ITI2", 1919, 1969, "ITA-1919-2025"),  # 35.5x
    ("ITA-ITI2", 1870, 1918, "ITA-1870-1919"),  # 33.7x
    ("ITA-ITI2", 1866, 1869, "ITA-1866-1870"),  # 32.3x
    ("ITA-ITI2", 1861, 1865, "ITA-1861-1866"),  # 29.3x
    ("MEX-BAJACALIFORNIA", 1900, 1951, "MEX-1848-2025"),  # 26.8x
    ("COL-GUAVIARE", 1922, 1990, "COL-1922-2025"),  # 20.5x
    ("COL-GUAVIARE", 1915, 1921, "COL-1903-1922"),  # 19.7x
    ("ITA-ITI4", 1919, 1969, "ITA-1919-2025"),  # 17.4x
    ("ITA-ITI4", 1870, 1918, "ITA-1870-1919"),  # 16.5x
    ("ITA-ITI4", 1866, 1869, "ITA-1866-1870"),  # 15.8x
    ("ITA-ITI4", 1861, 1865, "ITA-1861-1866"),  # 14.3x
    ("ITA-ITH5", 1919, 1969, "ITA-1919-2025"),  # 13.6x
    ("ITA-ITH5", 1870, 1918, "ITA-1870-1919"),  # 12.9x
    ("ITA-ITH5", 1866, 1869, "ITA-1866-1870"),  # 12.3x
    ("ITA-ITC1", 1919, 1969, "ITA-1919-2025"),  # 11.9x
    ("ARG-SANTACRUZ", 1900, 1901, "ARG-1899-1902"),  # 11.6x
    ("ARG-SANTACRUZ", 1902, 1954, "ARG-1902-2025"),  # 11.4x
    ("ITA-ITC1", 1880, 1918, "ITA-1870-1919"),  # 11.3x
    ("ITA-ITH5", 1861, 1865, "ITA-1861-1866"),  # 11.2x
    ("AUS-SOUTHAUSTRALIA", 1900, 1900, "AUS-1800-1901"),  # 7.8x
    ("AUS-NORTHERNTERRITORY", 1900, 1900, "AUS-1800-1901"),  # 5.7x
})


def main() -> int:
    if not os.path.exists(LEDGER):
        print(f"SKIP: {os.path.relpath(LEDGER, REPO)} absent")
        return 0
    try:
        import geopandas as gpd
    except ImportError:
        print("SKIP: geopandas unavailable")
        return 0
    if not os.path.exists(GPKG):
        print(f"SKIP: {os.path.relpath(GPKG, REPO)} absent")
        return 0

    csv.field_size_limit(sys.maxsize)
    with open(POLDB, encoding="utf-8") as fh:
        pol = {r["polity_code"]: r for r in csv.DictReader(fh)}

    g = gpd.read_file(GPKG).to_crs("ESRI:54034")
    area = {r["polity_code"]: r.geometry.area / 1e6 for _, r in g.iterrows()
            if r.geometry is not None and not r.geometry.is_empty}

    found = {}
    with open(LEDGER, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            raw = (r.get("coverage_json") or "").strip()
            if not raw:
                continue
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                continue
            segs = parsed.get("segments", []) if isinstance(parsed, dict) else parsed
            page = (r.get("page_polity_code") or r.get("matched_polity_code") or "").strip()
            if pol.get(page, {}).get("polity_type") != "subnational":
                continue
            mine = area.get(page)
            if not mine:
                continue
            for s in segs:
                if s.get("disposition") != "matched":
                    continue
                target = (s.get("polity_code") or "").strip()
                theirs = area.get(target)
                if not theirs:
                    continue
                ratio = theirs / mine
                if ratio <= MAX_RATIO:
                    continue
                try:
                    key = (r["unit_id"], int(s["start_year"]), int(s["end_year"]), target)
                except (KeyError, TypeError, ValueError):
                    continue
                found[key] = (ratio, r["country"], page)

    stale = sorted(set(BASELINE) - set(found))
    if stale:
        print(f"FAIL: {len(stale)} baseline entr(ies) no longer match a container -- remove them:")
        for k in stale:
            print(f"  {k[0]} {k[1]}-{k[2]} -> {k[3]}")
        return 1

    new = {k: v for k, v in found.items() if k not in BASELINE}
    if new:
        print(f"FAIL: {len(new)} `matched` segment(s) name a polity far larger than the "
              f"territory the source reported\n")
        for (unit, lo, hi, target), (ratio, country, page) in sorted(
                new.items(), key=lambda kv: -kv[1][0]):
            print(f"  {unit} ({country}) {lo}-{hi} -> {target}")
            print(f"      {ratio:.1f}x the area of {page}, this unit's own polity. `matched` "
                  f"asserts the source OBSERVED that territory; at this ratio it observed a "
                  f"part of it, and routing the data there attributes a region's values to its "
                  f"container -- which already receives its own national labels.")
        print("\nUse `back_cast` if the values are a reconstruction onto a boundary that did not "
              "exist yet, or create the polity for the era. See issue 657.")
        return 1

    print(f"PASS: every `matched` segment names a polity within {MAX_RATIO}x the reporting "
          f"unit's own territory ({len(BASELINE)} baselined)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
