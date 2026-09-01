#!/usr/bin/env python3
"""One year in a smooth series reading 10,000x its own neighbours.

`05_magnitude_screen.py` screens series MEDIANS against the polity's area, and that is the right test
for a series carried on the wrong scale throughout. It cannot see a single-year spike, by construction:
`iia cameroon / groundnuts, with shell / ha` runs 61,000 (1931), **620,004,098** (1932), 62,000 (1933),
and its median is 71,000 -- entirely plausible. The screen does carry that series, flagged at ratio 9.3
for intensity, so the row is present and the spike is invisible in it. Cameroon's whole land area is
about 47.5M ha, so the 1932 figure is thirteen times the country.

Nor can `16_source_splices.py` see these: the spike and both neighbours come from ONE source, so there
is no seam to measure. And `17_constant_runs.py` looks for the opposite shape.

WHAT THIS FOUND ON THE RUN THAT ADDED IT:

    isolated single-year spikes >=20x BOTH neighbours      21
      >=50x  11      >=100x  8      >=1000x  4
      by source   iia 16   juan 3   mitchell 1   sa_colonial 1

    iia   cameroon    groundnuts, with shell  ha      1932      620,004,098   (61,000 / 62,000)
    iia   guadeloupe  cotton seed             tonnes  1934        3,884,800   (30 / 100)
    iia   france      eggs, hen, in shell     tonnes  1937          334,180   (8 / 5)
    mitch czech rep.  beer of barley          tonnes  1937       66,528,960   (604,960 / 502,640)
    iia   spain       wine                    tonnes  1920       51,096,793   (1,990,897 / 1,862,817)

TWO TRAPS THIS HAD TO AVOID, AND THE FIRST ONE BIT.

1. `indicator` MUST be in the series key. Run without it, the detector returns 110 hits and 89 are
   `fao1952` -- and their "neighbours" print with the SAME YEAR as the spike, because that source packs
   several indicators under one item code (the convention is already recorded in
   `state/source_conventions.csv` for its population code). Those are not spikes; they are two
   different indicators being compared to each other. Keying on `indicator` removes all 89.
2. Even keyed on `indicator`, 342 series still carry more than one row for a single year with NOTHING
   in the panel to order them (issue 367). A series that cannot be ordered cannot have neighbours, so
   those are SKIPPED and counted, never guessed at.

WHAT IT MISSES, ON PURPOSE. Adjacent spikes mask each other: the Czech beer series spikes in 1937,
1944 AND 1945, and only 1937 is reported, because 1944's neighbour is 1945 (also spiked) and the ratio
collapses. A run of bad years is the source-splice and constant-run detectors' territory, not this
one's. Series endpoints have only one neighbour and are not tested either.

WHAT THIS DOES NOT DECIDE. Which digit went wrong. A dropped decimal, two prepended digits, a
misaligned column, a footnote read as a value -- all produce this shape, and separating them needs the
yearbook page. This reports the year and the factor against its own neighbours.

Usage:
  python3 pipelines/polity-autoimprove/18_isolated_spikes.py            # report only
  python3 pipelines/polity-autoimprove/18_isolated_spikes.py --write    # refresh the tracked table
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import tempfile
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "state/isolated_spikes.csv")
DEFAULT_PANEL = os.path.expanduser(
    os.environ.get("WHEP_LAYER_B") or os.environ.get("WHEP_LAYERB")
    # ONE PANEL, EITHER SPELLING (issue 629). Two names were in use -- WHEP_LAYERB in
    # 01_match_and_findings.py and extdata.py, WHEP_LAYER_B in the other 17 tools -- so
    # neither redirected the whole pipeline and setting one left stage 01 matching against
    # a different panel than the analysis stages measured.
    or "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet")

# Against the LARGER neighbour, so a spike must clear both. Agricultural output moves by factors of
# two or three in a bad year; twenty is not a harvest.
SPIKE = 20.0
MIN_SERIES = 5


def norm(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def find_spikes(panel_path):
    import pandas as pd
    d = pd.read_parquet(panel_path)
    if "is_aggregate" in d.columns:
        d = d[~d["is_aggregate"].astype(bool)]
    d = d.dropna(subset=["year", "value"])
    d = d[d["value"] > 0]

    series = defaultdict(list)
    for r in d.itertuples():
        # `indicator` is part of the key: without it, fao1952's several indicators under one item code
        # are compared to EACH OTHER and 89 of 110 "spikes" are that artefact.
        series[(norm(r.country), norm(r.item), str(r.unit), r.source, str(r.indicator))].append(
            (int(r.year), float(r.value)))

    out, n_series, n_unorderable = [], 0, 0
    for (country, item, unit, source, indicator), vals in series.items():
        if len(vals) < MIN_SERIES:
            continue
        years = [y for y, _v in vals]
        if len(set(years)) != len(years):
            # Two rows for one year, indistinguishable in the panel (issue 367). A series that cannot
            # be ordered has no neighbours; skipping is the only honest answer.
            n_unorderable += 1
            continue
        n_series += 1
        vals.sort()
        for i in range(1, len(vals) - 1):
            year, value = vals[i]
            prev_y, prev_v = vals[i - 1]
            next_y, next_v = vals[i + 1]
            bound = max(prev_v, next_v)
            if bound <= 0 or value / bound < SPIKE:
                continue
            out.append({
                "source": source, "country": country, "item": item, "unit": unit,
                "indicator": "" if indicator == "None" else indicator,
                "year": year, "value": f"{value:.3f}",
                "year_prev": prev_y, "value_prev": f"{prev_v:.3f}",
                "year_next": next_y, "value_next": f"{next_v:.3f}",
                "factor_vs_larger_neighbour": f"{value / bound:.2f}",
            })
    out.sort(key=lambda r: -float(r["factor_vs_larger_neighbour"]))
    return out, n_series, n_unorderable


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--layer-b", default=DEFAULT_PANEL)
    # Every tool from 25 up carries --check; these eight did not, so their tracked tables could drift
    # undetected. That is not hypothetical: 04's --check caught territory_basis.csv drifting after a
    # routing fix, and 23's absence let verdict_carryover.csv go stale (issues 308, 472). Safe here
    # because all eight were verified to regenerate byte-identically with default arguments -- the
    # precondition 15_label_provenance did NOT meet, where a check would have invited data loss.
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the tracked table is not what this run produces")
    ap.add_argument("--write", action="store_true", help=f"refresh {os.path.relpath(OUT, REPO)}")
    args = ap.parse_args()

    if not os.path.exists(args.layer_b):
        print(f"SKIP: layer-B panel not present at {args.layer_b}")
        return 0

    rows, n_series, n_unorderable = find_spikes(args.layer_b)
    print(f"orderable series with >={MIN_SERIES} values: {n_series:,}")
    print(f"series skipped as unorderable (two rows for one year, issue 367): {n_unorderable:,}")
    print(f"isolated single-year spikes >={SPIKE:.0f}x BOTH neighbours: {len(rows)}")
    for t in (50, 100, 1000):
        print(f"   >={t:>5}x: {sum(1 for r in rows if float(r['factor_vs_larger_neighbour']) >= t):>4}")
    print("   by source:", dict(Counter(r["source"] for r in rows).most_common()))
    print(f"\n{'factor':>10}  {'source':11} {'country':18} {'item':24} {'unit':7} {'yr':>4}"
          f"  {'value':>15}  neighbours")
    for r in rows:
        print(f"{float(r['factor_vs_larger_neighbour']):>9,.0f}x  {r['source']:11} "
              f"{r['country'][:17]:18} {r['item'][:23]:24} {r['unit'][:6]:7} {r['year']:>4}  "
              f"{float(r['value']):>15,.0f}  {r['year_prev']}:{float(r['value_prev']):,.0f} "
              f"{r['year_next']}:{float(r['value_next']):,.0f}")

    if args.write or args.check:
        cols = ["source", "country", "item", "unit", "indicator", "year", "value", "year_prev",
                "value_prev", "year_next", "value_next", "factor_vs_larger_neighbour"]
        if args.check:
            if not os.path.exists(OUT):
                print(f"MISSING {os.path.relpath(OUT, REPO)}", file=sys.stderr)
                return 1
            with open(OUT, newline="", encoding="utf-8") as fh:
                have = list(csv.DictReader(fh))
            want = [{k: ("" if v is None else str(v)) for k, v in dict(r).items()} for r in rows]
            if [{k: r.get(k, "") for k in cols} for r in have] != \
                    [{k: r.get(k, "") for k in cols} for r in want]:
                print(f"STALE {os.path.relpath(OUT, REPO)}: committed {len(have)} row(s), this run "
                      f"produces {len(want)}; rerun with --write", file=sys.stderr)
                return 1
            print(f"table is current ({len(have)} rows)")
            return 0
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(OUT), suffix=".tmp")
        os.close(fd)
        # The unlink matters: a DictWriter raises on an unexpected key, and without this the
        # half-written .tmp is left behind in a TRACKED state directory where `git add -A`
        # can commit it. That happened on 2026-08-20 when a column was added to the rows but
        # not to the fieldnames.
        try:
            with open(tmp, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=cols)
                w.writeheader()
                w.writerows(rows)
            os.replace(tmp, OUT)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
        print(f"\nwrote {len(rows)} spikes to {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
