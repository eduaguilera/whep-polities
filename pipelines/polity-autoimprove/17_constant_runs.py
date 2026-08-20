#!/usr/bin/env python3
"""Where a series repeats one value for years on end, is that agriculture or a filled-in gap?

Found while chasing the tobacco magnitudes in issue 360. A detector for implausibly LARGE cells kept
flagging `india / sesame seed / ha`, and the reason turned out to be the opposite of a spike: 1922-1933
carry 2.0-2.5M ha (which is India's real sesame area), and then 1934-1945 are all **exactly 1,000.0**.
The flag was right, the diagnosis was inverted. Nothing existing looks for this shape, because a flat
line breaks no magnitude bound, opens no year gap and crosses no source seam.

THE OBVIOUS INNOCENT EXPLANATION, AND WHY IT IS FALSE HERE. A long run of exactly 1,000 ha looks like
a source reporting in thousands, where every small producer rounds to "1". That would make the run a
resolution limit rather than a defect. It is testable, and it fails: these series resolve FINER than
their own constant. Iceland's potato series records 400, Malta's grapes 600, Norway's wheat 4,300 —
and `argentina / soybeans / ha` records **2 ha** and then sits at exactly 1,000 for eleven years. A
source that can express 2 is not rounding to 1,000. The cleanest proof is
`denmark / potatoes / ha`: exactly 54,000 for ten straight years, in a series that elsewhere
carries 54,100, so its grid resolves 100 ha and the decade of no change is not rounding.

So this script reports only runs that their OWN series refutes: a run of >= MIN_RUN identical values
where somewhere else in the same series sits a value that is not a multiple of the run value's own
power-of-ten grid. That test needs no external data and no judgement, which is why the table can be
gated.

WHAT THE RUN THAT ADDED IT MEASURED (issue filed alongside):

    constant runs of >=5 identical values                       827   (4,590 rows, 2.6% of valued)
      refuted as rounding by their own series                   253   (1,666 rows, 215 series)
        by source   juan 1,077   iia 522   mitchell 62   fao1952 5

WHY IT MATTERS, AND IT IS NOT THE SIZE OF THE NUMBER. These rows carry zero variance. Any trend,
growth rate, elasticity or level-shift analysis reads them as "this did not change", when what
happened is that nobody knew. The bias is not random either: it lands on small producers and on
colonial reporting units, so it systematically flattens exactly the series that are already weakest.
Fifteen consecutive years of literally unchanging Norwegian wheat area is not agriculture.

WHAT THIS DOES NOT DECIDE. Whether a given run was carried forward from one observation, interpolated,
or filled with a round placeholder for "not available" — those need the source page. It also cannot
rule out a genuinely unchanging series, which is why the refutation test is required rather than the
bare run: a real constant would not sit in a series that resolves finer than it.

A run is counted over consecutive OBSERVATIONS, not consecutive years, since the panel is not
gap-free; `year_first`/`year_last` give the real span and `n_values` the number of rows.

Usage:
  python3 pipelines/polity-autoimprove/17_constant_runs.py            # report only
  python3 pipelines/polity-autoimprove/17_constant_runs.py --write    # refresh the tracked table
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
OUT = os.path.join(HERE, "state/constant_runs.csv")
DEFAULT_PANEL = os.path.expanduser(
    os.environ.get("WHEP_LAYER_B", "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet"))

# Four identical values can happen; five in a row in a series that resolves finer is a filled gap.
MIN_RUN = 5
# Below this the "same series resolves finer" test has too little to draw on to mean anything.
MIN_SERIES = 6


def norm(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


SCALE = 10 ** 6          # the panel carries at most a few decimals; work in scaled integers


def grid_of(v: float) -> int:
    """The coarsest power-of-ten grid the value sits on, as a SCALE-ed integer.

    54,000 -> 1000, 54,100 -> 100, 2 -> 1, 0.8 -> 0.1. Computed on scaled integers because float
    modulo cannot be trusted here, and returning 1 (not 0.1) for a decimal constant would make the
    refutation test below trivially true — 0.8 is not a multiple of 1, so ANY other decimal in the
    series would "refute" a constant that was never on that grid in the first place.
    """
    n = int(round(v * SCALE))
    if n == 0:
        return 1
    g = 1
    while n % (g * 10) == 0 and g < SCALE * 10 ** 9:
        g *= 10
    return g


# IIA VOLUME WINDOWS, and why this column exists at all (issue 366).
#
# This table only ever contains runs that HAVE finer evidence somewhere in their series -- a run fully
# consistent with its grid is never emitted. So `n_finer_elsewhere` is positive by construction, and it
# cannot distinguish the two cases that matter:
#
#   * the finer value comes from a DIFFERENT yearbook volume, whose grid was finer. Then the run is a
#     resolution limit of its own volume and nothing is wrong with it. Issue 366's original headline was
#     withdrawn on exactly this ground.
#   * the finer value comes from the SAME volume. Then that volume demonstrably could express the finer
#     figure and chose a round number for the run's years, which the grid cannot explain.
#
# Reading `n_finer_elsewhere` without that split produces the withdrawn claim, which is what happened.
#
# LAYER B CARRIES NO VOLUME PROVENANCE, so "same volume" can only be inferred from the year, and the
# windows OVERLAP -- 1920, 1921, 1929, 1932 and 1933 each fall in two volumes, so a value there could
# have come from either and proves nothing. Those years are excluded, which is the difference between a
# defensible 18 and an inflated 39.
IIA_VOLUMES = ((1909, 1921), (1920, 1925), (1926, 1929), (1929, 1933), (1932, 1938), (1939, 1945))
IIA_AMBIGUOUS_YEARS = frozenset(
    y for y in range(1900, 1960)
    if sum(1 for a, b in IIA_VOLUMES if a <= y <= b) > 1
)


def _iia_volumes_covering(year: int) -> set:
    return {i for i, (a, b) in enumerate(IIA_VOLUMES) if a <= year <= b}


def find_runs(panel_path):
    import pandas as pd
    d = pd.read_parquet(panel_path)
    # Aggregates ("Total", "ASIA", ...) are already flagged in the panel and dropped by 00_intake;
    # leaving them in would flag world totals as if they were reporting units.
    if "is_aggregate" in d.columns:
        d = d[~d["is_aggregate"].astype(bool)]
    d = d.dropna(subset=["year", "value"])
    d = d[d["value"] > 0]

    series = defaultdict(list)
    for r in d.itertuples():
        series[(norm(r.country), norm(r.item), str(r.unit), r.source)].append(
            (int(r.year), float(r.value)))

    out, n_series, n_runs_all, n_rows_all = [], 0, 0, 0
    for (country, item, unit, source), vals in series.items():
        if len(vals) < MIN_SERIES:
            continue
        n_series += 1
        vals.sort()
        years = [y for y, _v in vals]
        v = [x for _y, x in vals]
        start = 0
        for k in range(1, len(v) + 1):
            if k == len(v) or v[k] != v[start]:
                n = k - start
                if n >= MIN_RUN:
                    n_runs_all += 1
                    n_rows_all += n
                    const = v[start]
                    g = grid_of(const)
                    finer = [x for j, x in enumerate(v)
                             if not (start <= j < k)
                             and int(round(x * SCALE)) % g != 0]
                    # The in-volume witness: the earliest finer value that sits in a volume window the
                    # run itself touches, at a year only ONE volume covers. Earliest rather than
                    # closest so the choice is deterministic when the panel is rebuilt.
                    wit_y, wit_v = "", ""
                    if finer and source == "iia":
                        run_vols = (_iia_volumes_covering(years[start])
                                    | _iia_volumes_covering(years[k - 1]))
                        for j, x in enumerate(v):
                            if start <= j < k or int(round(x * SCALE)) % g == 0:
                                continue
                            yr = years[j]
                            if yr in IIA_AMBIGUOUS_YEARS:
                                continue
                            if _iia_volumes_covering(yr) & run_vols:
                                wit_y, wit_v = str(yr), f"{x:.3f}"
                                break
                    if finer:
                        out.append({
                            "source": source, "country": country, "item": item, "unit": unit,
                            "constant": f"{const:.3f}", "n_values": n,
                            "year_first": years[start], "year_last": years[k - 1],
                            "series_n": len(v), "grid": f"{g / SCALE:g}",
                            "finest_elsewhere": f"{min(finer, key=abs):.3f}",
                            "n_finer_elsewhere": len(finer),
                            "finer_in_volume_year": wit_y,
                            "finer_in_volume_value": wit_v,
                        })
                start = k
    out.sort(key=lambda r: (-r["n_values"], r["source"], r["country"], r["item"]))
    return out, n_series, n_runs_all, n_rows_all


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

    rows, n_series, n_runs_all, n_rows_all = find_runs(args.layer_b)
    print(f"series (country, item, unit, source) with >={MIN_SERIES} values: {n_series:,}")
    print(f"constant runs of >={MIN_RUN} identical values: {n_runs_all:,} ({n_rows_all:,} rows)")
    print(f"  refuted as rounding by their own series: {len(rows):,} "
          f"({sum(r['n_values'] for r in rows):,} rows, "
          f"{len({(r['country'], r['item'], r['unit'], r['source']) for r in rows}):,} series)")
    print("  by source:",
          dict(Counter({s: sum(r["n_values"] for r in rows if r["source"] == s)
                        for s in {r["source"] for r in rows}}).most_common()))
    print("\nlongest refuted runs (the series resolves finer than the value it repeats):")
    for r in rows[:14]:
        print(f"   {r['source']:9} {r['country'][:17]:18} {r['item'][:21]:22} {r['unit']:7} "
              f"{float(r['constant']):>10,.0f} x{r['n_values']:>2} "
              f"{r['year_first']}-{r['year_last']}  grid {float(r['grid']):>7,.0f}  "
              f"elsewhere {float(r['finest_elsewhere']):>12,.1f}")

    if args.write or args.check:
        cols = ["source", "country", "item", "unit", "constant", "n_values", "year_first",
                "year_last", "series_n", "grid", "finest_elsewhere", "n_finer_elsewhere",
                "finer_in_volume_year", "finer_in_volume_value"]
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
        with open(tmp, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, OUT)
        print(f"\nwrote {len(rows)} runs to {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
