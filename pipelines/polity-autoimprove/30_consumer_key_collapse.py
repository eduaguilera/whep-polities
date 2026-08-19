#!/usr/bin/env python3
"""Every group of panel rows that the consumer collapses into ONE published value.

NOT THE SAME THING AS `27_series_collapses.py`, despite both saying "collapse", and the two were
one filename apart before this was renamed. There, a collapse is a SERIES dropping to zero and
staying there (a level break within one series over time). Here, a collapse is the AGGREGATION the
consumer performs when several rows share its key in a single year -- nothing drops and nothing is
about time. A tool numbered 27 alongside 27_series_collapses.py invited exactly the wrong reading.

WHY THIS EXISTS, AND WHY 25_same_polity_overlaps.py IS NOT ENOUGH (issues 451, 367).
`.prepare_historical_production()` in the WHEP R package reduces duplicate keys with

    key_cols <- c("year","area","area_code","item_prod","item_prod_code",
                  "item_cbs","item_cbs_code","live_anim","live_anim_code","unit")
    out <- dt[, .(value = mean(value, na.rm = TRUE), ...), by = key_cols]

so the unit that becomes one number is (POLITY, ITEM, UNIT, YEAR) -- with NO label column and NO
source column in the key. `25_same_polity_overlaps.py` screens the same panel but groups by
(polity, source) and reports LABEL PAIRS, so two whole classes of collapse are outside what it can
see by construction:

  * duplicates under a SINGLE label. `germany` alone supplies TEN rows for population 1937 on
    DEU-1920-1938. There is no pair, so no pair-wise screen will ever report it.
  * duplicates spanning SEVERAL SOURCES, which its per-source grouping separates before comparing.

Measured on the panel, those two classes are nearly all of the problem: of 1,977 groups whose members
DISAGREE, 1,436 involve one label only. 541 do carry more than one label -- but in 481 of those the
labels come from DIFFERENT sources, which a per-source screen separates before it can compare them.
So the number a label-pair screen keyed on (polity, source) can reach at all is the groups where one
source contributes two distinct labels:

    differing collapse groups                                        1,977
      with more than one label anywhere                                541
      where a SINGLE source contributes two labels (reachable)          60   = 3.0%

That 3.0% is the reason this file exists, and it is why the key here deliberately drops `source` even
though every other screen in this pipeline keeps it. (I first reported the reachable share as 27% on
issue 451, reading it off the label count; the per-source grouping makes the true figure an order of
magnitude smaller.)

WHAT A ROW MEANS, AND WHAT IT DOES NOT. A row is a group the consumer WOULD average. It is not by
itself a defect:

  values_identical   every member is the same number, so `mean` returns it unchanged and nothing is
                     distorted today. Recorded anyway, because the harm is one aggregation change
                     away: under `sum` these become exact multiple-counts. The 9 shared
                     `ethiopia`/`ethiopia pdr` coffee cells are this class, and the claim on issue 451
                     that they "count Ethiopian coffee twice" was WITHDRAWN for exactly this reason.
  values_differ      the members disagree, so the published number is a blend of all of them and
                     equals none. This is the class worth reading. `KOR-1948-2025` population 1951
                     holds 29,300 (the whole peninsula) and 20,500 (South Korea) and publishes
                     24,900; `DEU-1920-1938` population 1937 publishes 13,854 against a Reich total
                     of 57,576.

`ratio_mean_max` is the published mean over the group's largest member -- a size for the distortion
that needs no outside information, since if the largest member is the total then the ratio is the
share of it that survives. It is a DESCRIPTION, not a verdict: for a group of genuine siblings with no
total present, a low ratio is expected and correct. Do not read it as an error rate.

THE ITEM AXIS IS WHERE THE SIGNAL IS. The dominant items are livestock and meat aggregates --
`horses mules asses`, `meat`, `poultry`, `other meat` -- not the FAO population table (12.4%), and for
4-row groups the ratio clusters tightly at 0.25, the signature of one total beside three small
components. That is issue 367's `total_beside_parts` class, here counted polity-keyed and across all
five sources instead of fao1952-only.

BOUND, STATED. This keys the panel the way the consumer keys it. Whether a given item survives the
upstream `item_cbs_code` mapping is a separate filter not evaluated here, so these are groups that
WOULD collapse, not a claim that each reaches a published table.

WHY A TRACKED TABLE. The routings come from the gitignored layer-B panel, absent in CI, so this
writes `state/collapse_groups.csv`, that file is committed, and `validate_collapse_groups.py` reads
it. Same arrangement as 25_same_polity_overlaps.py.

Usage:
  python3 pipelines/polity-autoimprove/30_consumer_key_collapse.py            # report only
  python3 pipelines/polity-autoimprove/30_consumer_key_collapse.py --write    # refresh the table
  python3 pipelines/polity-autoimprove/30_consumer_key_collapse.py --check    # fail if stale
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "collapse_groups.csv")
MATCHED = os.path.join(STATE, "matched_rows.parquet")

# Float noise from the panel's own round-trips, not a real difference. Same value as 25's EPS.
EPS = 1e-9

FIELDS = ("whep_code", "item", "unit", "year", "n_rows", "n_distinct", "n_labels", "n_sources",
          "verdict", "composition", "v_min", "v_max", "published_mean", "ratio_mean_max",
          "labels", "sources")


def _num(x) -> str:
    """render without exponent noise so the tracked table diffs cleanly"""
    f = float(x)
    return str(int(f)) if f == int(f) and abs(f) < 1e15 else repr(round(f, 6))


def build(matched: str) -> list[dict]:
    import pandas as pd

    d = pd.read_parquet(matched)
    # A group can only collapse if it HAS a key: an unrouted row, a null value and a null year each
    # mean there is nothing for the consumer to reduce. Excluding them is not a filter on the
    # finding -- rows with no year are issue 310 and rows with no code are the matcher's business.
    d = d[d.whep_code.notna() & d.value.notna() & d.year.notna()]
    rows = []
    for (code, item, unit, year), g in d.groupby(["whep_code", "item", "unit", "year"], sort=True):
        if len(g) < 2:
            continue
        vals = g.value.astype(float)
        vmin, vmax, vmean = float(vals.min()), float(vals.max()), float(vals.mean())
        labels = sorted({str(x).strip() for x in g.country})
        sources = sorted({str(x).strip() for x in g.source})
        identical = (vmax - vmin) <= EPS * max(1.0, abs(vmax))
        rows.append({
            "whep_code": code, "item": item, "unit": unit, "year": int(year),
            "n_rows": len(g),
            # distinctness is judged on the ROUNDED value for the same reason EPS exists: two
            # round-trips of one number through parquet must not read as two opinions.
            "n_distinct": int(vals.round(9).nunique()),
            "n_labels": len(labels), "n_sources": len(sources),
            "verdict": "values_identical" if identical else "values_differ",
            "composition": ("one_label" if len(labels) == 1 else "several_labels") + "_" +
                           ("one_source" if len(sources) == 1 else "several_sources"),
            "v_min": _num(vmin), "v_max": _num(vmax), "published_mean": _num(vmean),
            # DERIVED FROM THE VALUES AS WRITTEN, not from full precision, so the row is exactly
            # self-consistent and `validate_collapse_groups.py` check B can recompute it with a tight
            # tolerance. Taking it from the unrounded mean instead makes the table disagree with
            # itself by up to 2e-6 -- for Nyasaland `other meat` 1949 (0.1, 0.3, mean 0.2333...) the
            # stored mean is 0.233333 and 0.233333/0.3 is 0.777777, while the unrounded ratio rounds
            # to 0.777778. Four rows failed on exactly that, which is how this was found.
            "ratio_mean_max": (_num(float(_num(vmean)) / float(_num(vmax))) if vmax else ""),
            "labels": " | ".join(labels), "sources": " | ".join(sources),
        })
    rows.sort(key=lambda r: (r["whep_code"], r["item"], r["unit"], r["year"]))
    return rows


def write(rows: list[dict], path: str) -> None:
    # build fully, then replace: a truncating open() has cost this repo two tracked files mid-error.
    import tempfile
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--matched", default=MATCHED)
    ap.add_argument("--write", action="store_true", help=f"refresh {os.path.relpath(OUT, REPO)}")
    ap.add_argument("--check", action="store_true", help="exit 1 if the tracked table is stale")
    args = ap.parse_args()

    if not os.path.exists(args.matched):
        print(f"panel absent ({args.matched}); nothing to do", file=sys.stderr)
        return 0

    rows = build(args.matched)
    diff = [r for r in rows if r["verdict"] == "values_differ"]
    print(f"{len(rows)} collapse group(s) hold more than one row "
          f"({sum(int(r['n_rows']) for r in rows)} rows)")
    print(f"  values_identical {len(rows) - len(diff)}  (mean returns the value; a sum would multiply it)")
    print(f"  values_differ    {len(diff)}  (published value is a blend of all members)")
    comp: dict[str, int] = {}
    for r in diff:
        comp[r["composition"]] = comp.get(r["composition"], 0) + 1
    for k in sorted(comp):
        note = "  <- what a label-pair screen can reach" if k.startswith("several_labels") else ""
        print(f"    {k:32} {comp[k]}{note}")

    if args.check:
        if not os.path.exists(OUT):
            print(f"MISSING {os.path.relpath(OUT, REPO)}", file=sys.stderr)
            return 1
        with open(OUT, newline="") as fh:
            have = list(csv.DictReader(fh))
        want = [{k: str(v) for k, v in r.items()} for r in rows]
        if have != want:
            print(f"STALE {os.path.relpath(OUT, REPO)}: rerun with --write", file=sys.stderr)
            return 1
        print("table is current")
        return 0

    if args.write:
        write(rows, OUT)
        print(f"wrote {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
