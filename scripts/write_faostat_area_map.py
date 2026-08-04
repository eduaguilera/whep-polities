#!/usr/bin/env python3
"""Publish the FAOSTAT area -> polity mapping as a consumer contract.

Why: the WHEP R package builds its own FAOSTAT area -> polity mapping, by joining
area codes to polity families on an ISO3-shaped prefix. This repository already
knows the answer — `pipelines/faostat-era-matching` resolves it per area and year
range — so there were two authorities for one question and no way to compare
them. Cross-checking them found a real defect: the prefix join could not reach a
colonial-era polity whose prefix differs from the modern one, so 118 area-years
of FAOSTAT data were attributed to a polity that did not exist yet, including 50
years of Sudan routed to the post-2011 row that excludes South Sudan
(eduaguilera/whep#387).

The comparison should not depend on a consumer reading a pipeline's internal
state directory. `pipelines/faostat-era-matching/state/faostat_aliases.csv` is
working state: its columns exist to serve the matcher, it carries verbose `basis`
prose, and nothing promises its shape. This script republishes the resolved
mapping under data/final/ with a stable, documented column set, so consumers have
a contract to read instead of an implementation detail to reach into.

Only `matched` rows are published. An unresolved label is not a mapping, and
emitting it with an empty target invites a consumer to treat the absence as a
polity.

Usage:
  python3 scripts/write_faostat_area_map.py [--check]

`--check` verifies the committed map matches the pipeline state without writing,
exiting 1 on drift, for CI.
"""
import argparse
import csv
import io
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(
    REPO, "pipelines/faostat-era-matching/state/faostat_aliases.csv"
)
OUT = os.path.join(REPO, "data/final/faostat_area_polity_map.csv")

# The published column set. Deliberately excludes `basis` (multi-line prose
# naming the pins an observation came from — useful to the matcher, noise to a
# consumer) and `source`/`common_name` (constant and redundant respectively).
COLUMNS = (
    "area_code",       # FAOSTAT numeric reporting area
    "year_start",      # first year this area reports as this polity (inclusive)
    "year_end",        # last year (inclusive)
    "polity_code",     # the resolved WHEP polity
    "source_label",    # the label FAOSTAT uses for the area, verbatim
    "iso3",            # ISO3 the source carries, where it has one
    "match_route",     # how it was resolved: iso-equal, registry, manual-*
    "confidence",      # matcher confidence
    "rows_observed",   # data rows behind the assertion, for weighting review
)

ap = argparse.ArgumentParser()
ap.add_argument(
    "--check",
    action="store_true",
    help="verify the committed map matches the pipeline state; exit 1 on drift",
)
A = ap.parse_args()

if not os.path.exists(STATE):
    print(f"pipeline state not found: {STATE}", file=sys.stderr)
    sys.exit(2)

state = list(csv.DictReader(open(STATE, encoding="utf-8")))
matched = [r for r in state if r.get("match_status") == "matched"]

rows = []
for r in matched:
    area = (r.get("area_code") or "").strip()
    if not area:
        # A matched label with no area code is a polity assertion about a source
        # label, not about a FAOSTAT reporting area, so it is out of scope here.
        continue
    rows.append(
        {
            "area_code": int(float(area)),
            "year_start": r["year_start"].strip(),
            "year_end": r["year_end"].strip(),
            "polity_code": r["target_polity_code"].strip(),
            "source_label": r["original_name"].strip(),
            "iso3": (r.get("iso3") or "").strip(),
            "match_route": (r.get("match_route") or "").strip(),
            "confidence": (r.get("confidence") or "").strip(),
            "rows_observed": (r.get("rows") or "").strip(),
        }
    )

# Sorted so the file is a stable diff: an area's segments read in time order.
rows.sort(key=lambda r: (r["area_code"], r["year_start"], r["polity_code"]))

# Written with csv.writer rather than by hand, so labels containing commas
# ("Bolivia (Plurinational State of)") are quoted correctly.
sio = io.StringIO()
w = csv.DictWriter(sio, fieldnames=list(COLUMNS), lineterminator="\n")
w.writeheader()
for r in rows:
    w.writerow(r)
new = sio.getvalue()

areas = sorted({r["area_code"] for r in rows})

if A.check:
    old = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
    if old == new:
        print(
            f"--check: PASS — faostat_area_polity_map.csv matches the pipeline "
            f"state ({len(rows)} mappings over {len(areas)} areas)"
        )
        sys.exit(0)
    print("--check: FAIL — data/final/faostat_area_polity_map.csv is stale")
    if old:
        old_lines = old.splitlines()
        new_lines = new.splitlines()
        old_rows, new_rows = len(old_lines) - 1, len(new_lines) - 1
        if old_rows != new_rows:
            print(f"  committed map has {old_rows} mappings; state yields {new_rows}")
        else:
            # Equal counts, different content — say so explicitly and name a
            # differing line. Reporting the counts alone here reads as "the
            # counts are the problem" when they are not, which sends the reader
            # looking in the wrong place.
            print(f"  same number of mappings ({new_rows}), but the content differs")
            for k, (o, n) in enumerate(zip(old_lines, new_lines)):
                if o != n:
                    print(f"  first difference on line {k + 1}:")
                    print(f"    committed: {o}")
                    print(f"    expected:  {n}")
                    break
    print("\n  Fix: run scripts/write_faostat_area_map.py and commit data/final/.")
    sys.exit(1)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(new)
print(
    f"wrote {os.path.relpath(OUT, REPO)}: {len(rows)} mappings over "
    f"{len(areas)} FAOSTAT areas"
)
