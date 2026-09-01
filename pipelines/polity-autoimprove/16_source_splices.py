#!/usr/bin/env python3
"""Where a series switches SOURCE mid-stream, does the value stay on the same scale?

Layer B assigns every (country, year, item, unit) cell to exactly ONE source — measured: zero of
179,097 cells carry two. Sources are partitioned, never overlaid. That has a consequence nobody had
looked at: where a series is spliced from two sources, the join is a seam, and 30% of the seams are
not scale-consistent.

WHAT THIS FOUND ON THE RUN THAT ADDED IT (issue 360):

    series (country, item, unit)                    13,430
      containing more than one source                 574   (4%)
    adjacent-year source splices                    1,245
      value jumps by more than 30%                     373   (30%)
      by more than 3x                                  123   (10%)
      by more than 10x                                  66   (5%)
      by more than 100x                                 30   (2%)

A jump at exactly the year the source changes is not a harvest, a war or a border. The worst are
physically impossible: US flax fibre area x1655 at a `juan`->`mitchell` boundary, Canada x1231, Turkey
WHEAT area x41 at `iia`->`mitchell`.

IT IS NOT ONE BAD SOURCE. Splices jumping >3x are near-symmetric across every pairing —
`iia->mitchell` 26, `mitchell->iia` 25, `juan->iia` 20, `iia->juan` 19, `juan->mitchell` 19,
`mitchell->juan` 14 — so this is a property of the splicing, not of one source being wrong.

WHY A TRACKED TABLE RATHER THAN A LIVE CHECK. Layer B is gitignored and absent in CI, exactly like the
IIA raw extract behind `15_label_provenance.py`. So this script writes the seams it finds to
`state/source_splices.csv`, that file is committed, and `scripts/validate_source_splices.py` reads it
in CI. The gate can then refuse a NEW implausible seam without needing the panel.

WHAT THIS DOES NOT DECIDE. The cause of any individual splice. Candidates, probably all present: a
unit or thousands-multiplier mismatch (the 1000x+ cases look like exactly that), genuinely different
territorial coverage between the two sources' labels, different item definitions (seed cotton vs lint,
fibre vs tow), or a source-specific reporting basis. Separating them needs the sources, one seam at a
time. This measures the jump and the year it lands on.

Usage:
  python3 pipelines/polity-autoimprove/16_source_splices.py            # report only
  python3 pipelines/polity-autoimprove/16_source_splices.py --write    # refresh the tracked table
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
OUT = os.path.join(HERE, "state/source_splices.csv")
DEFAULT_PANEL = os.path.expanduser(
    os.environ.get("WHEP_LAYER_B") or os.environ.get("WHEP_LAYERB")
    # ONE PANEL, EITHER SPELLING (issue 629). Two names were in use -- WHEP_LAYERB in
    # 01_match_and_findings.py and extdata.py, WHEP_LAYER_B in the other 17 tools -- so
    # neither redirected the whole pipeline and setting one left stage 01 matching against
    # a different panel than the analysis stages measured.
    or "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet")

# A seam is worth recording once the value moves by more than this across it. 30% is the same
# threshold the abandoned territorial-step detector used, and it is well above ordinary
# year-on-year agricultural variation in AREA (output varies far more, which is why area is the
# better series to read a scale break from).
REPORT = 0.30


def norm(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def find_splices(panel_path):
    import pandas as pd
    d = pd.read_parquet(panel_path)
    d = d.dropna(subset=["year", "value"])
    d = d[d["value"] > 0]
    series = defaultdict(list)
    for r in d.itertuples():
        series[(norm(r.country), norm(r.item), str(r.unit))].append((int(r.year), r.source, float(r.value)))
    out, n_series, n_multi = [], 0, 0
    for (country, item, unit), vals in series.items():
        vals.sort()
        n_series += 1
        if len({s for _y, s, _v in vals}) > 1:
            n_multi += 1
        for i in range(len(vals) - 1):
            y1, s1, v1 = vals[i]
            y2, s2, v2 = vals[i + 1]
            if s2 == s1 or y2 != y1 + 1 or v1 <= 0:
                continue
            ratio = v2 / v1
            if 1 - REPORT <= ratio <= 1 / (1 - REPORT):
                continue
            out.append({"country": country, "item": item, "unit": unit,
                        "year_before": y1, "year_after": y2,
                        "source_before": s1, "source_after": s2,
                        "value_before": f"{v1:.3f}", "value_after": f"{v2:.3f}",
                        "ratio": f"{ratio:.4f}"})
    out.sort(key=lambda r: -abs(1 - float(r["ratio"])))
    return out, n_series, n_multi


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

    rows, n_series, n_multi = find_splices(args.layer_b)
    print(f"series (country, item, unit): {n_series:,}   containing >1 source: {n_multi:,} "
          f"({100 * n_multi / n_series:.0f}%)")
    print(f"seams where the value jumps by more than {REPORT:.0%}: {len(rows):,}")
    for thr, lab in ((3, ">3x"), (10, ">10x"), (100, ">100x")):
        n = sum(1 for r in rows if float(r["ratio"]) > thr or float(r["ratio"]) < 1 / thr)
        print(f"   of which {lab:6}: {n:>4}")
    print("\n   by source pair (>3x):",
          dict(Counter(f"{r['source_before']}->{r['source_after']}" for r in rows
                       if float(r["ratio"]) > 3 or float(r["ratio"]) < 1 / 3).most_common()))
    print("\nworst seams:")
    for r in rows[:12]:
        print(f"   {r['country'][:18]:20} {r['item'][:16]:18} {r['unit']:7} "
              f"{r['year_before']}->{r['year_after']} {r['source_before']:9}->{r['source_after']:9} "
              f"x{float(r['ratio']):.2f}")

    if args.write or args.check:
        cols = ["country", "item", "unit", "year_before", "year_after", "source_before",
                "source_after", "value_before", "value_after", "ratio"]
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
        print(f"\nwrote {len(rows)} seams to {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
