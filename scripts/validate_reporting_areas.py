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

Six such claims existed when this was written. MNP and PLW were resolved on 2026-08-17
(issue 48) and four remain, of two kinds:

  BES, CUW, SXM   ANT-1961-2010 and RLAM-1850-2025. Arguably intentional temporal
                  succession — the Netherlands Antilles dissolved in 2010 and its parts
                  fall to Latin America Other afterwards — except the two spans OVERLAP
                  for 1961-2010, so during those years both claim the same islands.
                  Unfixable without per-year aggregate geometry, which this builder emits
                  one feature per aggregate and therefore does not have.
  UMI             RNAM-1850-2025 (North America Other) and ROCE-1850-2025. US Minor
                  Outlying Islands genuinely straddle both regions (Navassa in the
                  Caribbean, Johnston/Midway/Wake in the Pacific), but the GADM polygon
                  is one indivisible feature, so it cannot sit in both without
                  double-claiming.

RESOLVED 2026-08-17 (issue 48), so removed from the baseline: MNP and PLW were in
RASI-1850-2025 (Asia Other) as two of four proxies for the Pacific Islands Trust
Territory, while ROCE-1850-2025 (Oceania Other) claims them as members in their own
right. WHEP's `inst/extdata/harmonization/regions_full.csv` settles it: its `polity_code`
column gives RASI exactly two members, IOT and PCI (Pacific Islands Trust Territory), and
files MNP and PLW under ROCE. So the Asia Other claim was an artefact of the proxy, not a
membership the source asserts. The PCI proxy is now FSM + MHL alone, which no other
aggregate claims; RASI's polygon falls 2,128 -> 1,140 km2 as a result, and the proxy now
covers about half of PCI's former land area. ROW's union is unchanged, because MNP and PLW
still enter it through ROCE.

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
    "BES": ("ANT-1961-2010", "RLAM-1850-2025"),
    "CUW": ("ANT-1961-2010", "RLAM-1850-2025"),
    "SXM": ("ANT-1961-2010", "RLAM-1850-2025"),
    # MNP and PLW were here until 2026-08-17. Removed from RASI-1850-2025's components
    # (issue 48): regions_full.csv gives RASI only IOT and PCI, and files both islands
    # under ROCE, so the Asia Other claim was a Pacific-Islands-Trust-Territory proxy
    # artefact. Neither is claimed twice any more.
    "UMI": ("RNAM-1850-2025", "ROCE-1850-2025"),
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
