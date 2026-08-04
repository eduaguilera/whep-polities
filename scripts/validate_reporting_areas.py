#!/usr/bin/env python3
"""Check the reporting-area aggregate polygons for territory claimed twice.

`scripts/sources/reporting-areas/build.py` builds the aggregate reporting polygons
(Belgium-Luxembourg, the regional "Other" buckets, Rest of World) as reproducible
unions of GADM 4.1 adm0 territories, listed per aggregate as `components`.

Nothing checked that a territory belongs to only ONE aggregate. It matters because
these aggregates are polities in their own right that receive data: if two of them
claim the same ground, allocating their data spatially puts two different aggregates'
values on the same territory. The ROW union itself is unaffected — unary_union
deduplicates — so the problem is invisible in the one geometry most likely to be
eyeballed.

Six such claims exist today, and they are not all the same kind of thing, which is why
this reports rather than fixes:

  BES, CUW, SXM   ANT-1961-2010 and RLAM-1850-2013. Arguably intentional temporal
                  succession — the Netherlands Antilles dissolved in 2010 and its parts
                  fall to Latin America Other afterwards — except the two spans OVERLAP
                  for 1961-2010, so during those years both claim the same islands.
  MNP, PLW        RASI-1850-2021 (Asia Other) and ROCE-1850-2021 (Oceania Other).
                  Northern Mariana Islands and Palau are in Oceania; membership of Asia
                  Other looks simply wrong.
  UMI             RNAM-1850-2021 (North America Other) and ROCE-1850-2021. US Minor
                  Outlying Islands genuinely straddle both regions (Navassa in the
                  Caribbean, Johnston/Midway/Wake in the Pacific), but the GADM polygon
                  is one indivisible feature, so it cannot sit in both without
                  double-claiming.

Baselined bidirectionally: a NEW double claim fails, and a baselined one that is
resolved fails until it is removed from the baseline.

Usage:
  python3 scripts/validate_reporting_areas.py
"""
import ast
import os
import re
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILDER = os.path.join(REPO, "scripts/sources/reporting-areas/build.py")

# component -> the aggregates that claim it, as (sorted) tuples.
BASELINE = {
    "BES": ("ANT-1961-2010", "RLAM-1850-2013"),
    "CUW": ("ANT-1961-2010", "RLAM-1850-2013"),
    "SXM": ("ANT-1961-2010", "RLAM-1850-2013"),
    "MNP": ("RASI-1850-2021", "ROCE-1850-2021"),
    "PLW": ("RASI-1850-2021", "ROCE-1850-2021"),
    "UMI": ("RNAM-1850-2021", "ROCE-1850-2021"),
}


def component_owners() -> dict:
    """Parse the builder's REPORTING_AREAS literal rather than importing it: the module
    needs geopandas and a 1 GB GADM file at import time, and neither is needed to read
    a list of ISO3 codes."""
    with open(BUILDER, encoding="utf-8") as fh:
        src = fh.read()
    start = src.index("REPORTING_AREAS = {")
    block = src[start : src.index("ROW_COMPONENTS")]
    owners = defaultdict(list)
    for m in re.finditer(r'"([A-Z0-9]+-\d{4}-\d{4})":\s*\{(.*?)\n    \}', block, re.S):
        code, body = m.group(1), m.group(2)
        cm = re.search(r'"components":\s*(\[.*?\])', body, re.S)
        if not cm:
            continue
        for comp in ast.literal_eval(cm.group(1)):
            owners[comp].append(code)
    return owners


def main() -> int:
    owners = component_owners()
    if not owners:
        print("FAIL: parsed no components from the builder", file=sys.stderr)
        return 2

    observed = {
        comp: tuple(sorted(set(aggs)))
        for comp, aggs in owners.items()
        if len(set(aggs)) > 1
    }

    print(f"aggregate reporting areas parsed: {len({a for v in owners.values() for a in v})}")
    print(f"distinct GADM components:         {len(owners)}")
    print(f"claimed by more than one:         {len(observed)}")
    for comp, aggs in sorted(observed.items()):
        print(f"   {comp:<5} -> {', '.join(aggs)}")

    problems = []
    for comp in sorted(set(observed) - set(BASELINE)):
        problems.append(
            f"NEW double claim: {comp} is in {', '.join(observed[comp])} — a territory "
            f"may belong to only one aggregate, or their data lands on the same ground"
        )
    for comp in sorted(set(BASELINE) - set(observed)):
        problems.append(
            f"{comp} is baselined as double-claimed but no longer is — remove it from "
            f"the baseline"
        )
    for comp in sorted(set(observed) & set(BASELINE)):
        if observed[comp] != BASELINE[comp]:
            problems.append(
                f"{comp} is still double-claimed but by different aggregates: "
                f"baseline {BASELINE[comp]}, now {observed[comp]}"
            )

    if problems:
        print(f"\nFAIL: {len(problems)} change(s) against the baseline\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: double-claimed components match the baseline exactly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
