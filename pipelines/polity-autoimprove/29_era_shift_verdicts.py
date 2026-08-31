#!/usr/bin/env python3
"""Per-row verdicts on iia tobacco/hops production from 1934, the era issue 416 sized.

WHAT THIS SETTLES. Issue 416 established the scope -- 328 production rows from 1934 across 56 labels,
against a pre-1934 median yield of 0.92 t/ha and a 1934+ median of 76.00 -- and said the remedy needs a
PER-ROW test, because a blanket division is not supportable: the yield medians move ~65x, not 100x, and
some 1934+ rows are fine. The test was then done in a comment and never persisted, so the verdicts were
one re-derivation away from being lost. This writes them to tracked state.

THE ZERO-AREA CLASS, AND WHY IT IS FIRST. 50 of the 241 rows that HAVE a paired area row have an area of
exactly 0 against production of 200 to 85,000 tonnes. Their implied yield is INFINITE -- the strongest
evidence any row here carries -- and the obvious way to write this screen loses every one of them:

    if area > 0:  test the yield          # 50 rows fall through to the weaker no-area test

That guard is why the earlier count of "160 impossible_yield" was low. This repo has paid for the same
shape before (issue 420 filtered `area_ha > 0` before a division and dropped 177 infinite-yield cells --
the most impossible cases -- from the tool built to find impossible yields). So zero area is a verdict
here, not a skip.

Those zeros are almost certainly issue 414's defect appearing in the AREA series: `iia_1938_39` reads
blank cells as 0, and its window is exactly this era. That is an interaction between two open defects
rather than a coincidence -- a false-zero area disables the yield test for the production row beside it --
and it is recorded per row so the two remedies can be sequenced (issue 433 maps them).

THE CLASSES, strongest evidence first:

  impossible_yield_zero_area  production > 0 on an area of exactly 0. Infinite yield.
  impossible_yield            paired area > 0 and implied yield > 20 t/ha. Tobacco leaf runs 1-3 t/ha
                              and hops similar, so 20 is an order of magnitude above the crop's ceiling
                              rather than a fitted threshold.
  no_area_level_shift         no paired area, but the row is >= 30x the label's OWN pre-1934 median for
                              that item. Weaker than a yield test -- it assumes the label's own history
                              is the right baseline -- but it needs no area, which is what makes the 87
                              unpaired rows reachable at all.
  no_area_level_drop          the SAME 30x against the same baseline, on the other side: <= 1/30 of the
                              label's own pre-1934 median. See "THE RATIO TEST WAS ONE-SIDED" below.
  high_yield_3to20            elevated and not impossible. NOT convicted: a 5 t/ha tobacco yield is
                              wrong for a field but not arithmetically impossible, and calling it a
                              defect would be the magnitude argument this repo has been burned by.
  plausible_yield             <= 3 t/ha. The row is fine.
  no_area_level_consistent    no area, has a pre-1934 baseline, and sits within it.
  untestable                  no area and no pre-1934 baseline for the label+item. Counted, never
                              convicted -- an untestable row is not an innocent one, and saying so is
                              the difference between this table and a correction list.

THE RATIO TEST WAS ONE-SIDED, AND A VALUE COULD NOT BE TOO SMALL TO FAIL. The level arm convicted at
`ratio >= 30` and filed EVERYTHING else `no_area_level_consistent`. There was no filter to grep for --
the exoneration was the `else` branch -- so the shape only shows up in what the table says about a
particular row:

    germany / tobacco, unmanufactured / 1945    production 0    baseline 25,833.9    ratio 0.0
    verdict: no_area_level_consistent

A production of ZERO filed as consistent with a 25,834 t baseline. Nothing about the row was mislabelled;
the classifier simply had no way to say "too small", so the maximal disagreement a ratio can express fell
into the class reserved for agreement. `no_area_level_drop` is that missing arm, at the same 30x, and
`LEVEL_DROP = 1 / LEVEL_SHIFT` rather than a second tunable so the two sides cannot drift apart.

THE BOUND IS NOT FITTED, and the way to show that is that it does not matter. Measured over all 393 era
rows that carry a ratio:

    ratio <= 1/100    1 row        ratio <= 1/10     1 row
    ratio <= 1/30     1 row        ratio <= 1/3      3 rows

and the two extra rows at 1/3 (micronesia 1936 and 1937, at 0.296 and 0.148) are ALREADY convicted by the
zero-area arm, which runs first. So every bound from 1/100 to 1/3 convicts the same single row today. A
threshold whose live population is invariant across a 33x range of the threshold is not tuned to its
population.

WHY THAT ROW IS CONVICTED AND NOT MERELY FLAGGED, on evidence outside this table. In the raw extract
germany's tobacco production series in `iia_1939_45` runs 1939-1943 and then jumps to a 1945 cell of 0,
skipping 1944 -- while the AREA series beside it runs 1939-1944 with no gap and no 1945 cell at all. And
germany has exactly ONE cell at 1945 in that entire volume, against 20 to 36 cells in every other year
from 1939 to 1944. A country that reported nothing else in 1945 did not report a tobacco harvest of
precisely zero; the cell sits at the table's edge, and it is the edge rather than a harvest. What is
convicted is therefore the CELL, not a claim about German output.

The 1945 zeros are NOT a general blank-as-zero artefact of that volume, and the check that would have
made them one fails: 1945 carries 7 zeros in 973 production cells (0.72%), no higher than 1939-1944
(0.22%-0.57%), so "the last year was read as blank" is refuted at the volume level. The association is
with a THIN year-block, not with the year: among labels holding exactly one 1945 cell, 3 of 30 are zero;
among labels with a populated 1945 block, 10 of 1,607. That is n=3 and stated as an association.

TWO THINGS THIS ARM DOES NOT REACH. `netherlands / tobacco / 1945` is also a zero, sits in a POPULATED
1945 block (20 cells), and is the only netherlands tobacco cell in the whole corpus -- so it has no
pre-era baseline, no ratio, and stays `untestable`. And a row with area EXACTLY 0 and production 0 would
escape the zero-area arm, whose guard is `production > 0`; with this arm it now lands on the ratio test
instead of on `no_area_level_consistent`, though the live population of that shape is 0 rows today.

The falsy-zero rule matters here and is not decoration: `ratio` for the germany row is 0.0, so any
`if ratio:` or `ratio or default` writes it out of existence. It is tested with `is not None`
throughout, and this repo has already turned a real 0.0 into 1.0 in exactly this measurement.

WHAT THIS DOES NOT DO. It does not write corrections and it does not name a factor per row. The implied
factors run 21x to 293x with a median of 68x, so no single divisor fits, and `yield_series_corrections.csv`
remains the place a repair is proposed with its anchor. This is the evidence a repair would rest on. The
per-row VOLUME attribution -- which yearbook edition each era cell came from, and the 100x/10x factor
measured from that label's own volume overlap -- is `41_era_volume_attribution.py`, which needs the raw
extract and therefore cannot live here.

Usage:
  python3 pipelines/polity-autoimprove/29_era_shift_verdicts.py            # report only
  python3 pipelines/polity-autoimprove/29_era_shift_verdicts.py --write    # refresh the table
  python3 pipelines/polity-autoimprove/29_era_shift_verdicts.py --check    # fail if stale
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "era_shift_verdicts.csv")
MATCHED = os.path.join(STATE, "matched_rows.parquet")

SOURCE = "iia"
ITEMS = ("hops", "tobacco, unmanufactured")
ERA_FROM = 1934                 # the boundary issue 414 explains: the last year two volumes cover is 1933
IMPOSSIBLE_YIELD = 20.0         # t/ha; an order of magnitude above the crop's ceiling, not a fitted value
HIGH_YIELD = 3.0
LEVEL_SHIFT = 30.0              # x the label's own pre-era median
# THE OTHER SIDE OF THE SAME TEST, derived rather than tuned. A second free constant could be edited
# to 0.0 and the low arm would silently stop firing while the high arm kept working.
LEVEL_DROP = 1.0 / LEVEL_SHIFT

FIELDS = ("source", "label", "whep_code", "item", "year", "period", "unit", "production", "area_ha",
          "implied_yield", "own_pre_era_median", "ratio_to_own", "verdict", "convicted")

CONVICTING = {"impossible_yield_zero_area", "impossible_yield", "no_area_level_shift",
              "no_area_level_drop"}


def _n(x, nd=6):
    if x is None:
        return ""
    f = float(x)
    return str(int(f)) if f == int(f) and abs(f) < 1e15 else repr(round(f, nd))


def build(matched: str) -> list[dict]:
    import pandas as pd

    d = pd.read_parquet(matched)
    t = d[d.source.eq(SOURCE) & d.item.isin(ITEMS)]
    prod = t[t.unit.eq("tonnes")]
    area = t[t.unit.eq("ha")]
    def _period_end(p):
        yy = re.findall(r"\d{4}", str(p or ""))
        return int(yy[-1]) if yy else None

    key = ["country", "item", "year"]
    # median where a group holds several rows: this screen is about the ERA, not about within-group
    # duplication, which state/collapse_groups.csv covers separately.
    a = area.dropna(subset=["year"]).groupby(key).value.median()
    # PERIOD ROWS PAIR ON THEIR PERIOD: an area average matches a production average of the same span.
    a_per = area[area.year.isna() & area.period.notna()].groupby(
        ["country", "item", "period"]).value.median()
    # THE BASELINE COUNTS PRE-ERA PERIOD ROWS TOO, and leaving them out was the same exclusion as the
    # scope bug one block below: `prod.year <= ERA_FROM - 1` is False for NaN. Measured, 50 (label, item)
    # pairs have ONLY a period baseline -- no dated pre-1934 production at all -- so their era rows had
    # nothing to compare against and fell to `untestable`, which is the class this screen is least able
    # to act on. A five-year mean is a legitimate level baseline and arguably a better one than a single
    # year, being smoother; what it cannot do is date a defect, and it is not asked to.
    pre_dated = prod[prod.year <= ERA_FROM - 1]
    pre_per = prod[prod.year.isna() & prod.period.notna()]
    pre_per = pre_per[pre_per.period.map(lambda p: (_period_end(p) or 9999) < ERA_FROM)]
    base = pd.concat([pre_dated, pre_per]).groupby(["country", "item"]).value.median()

    # PERIOD ROWS ARE IN THE ERA TOO, and the first version of this screen dropped them silently.
    # 341 of the 1,037 production rows carry a period label instead of a year, and 99 of those are
    # `1934-1938` -- squarely inside the era. `prod.year >= ERA_FROM` is False for NaN, so they left no
    # trace and the era read as 328 rows when its true scope is 427. This is the same blindness that
    # made #456's diff miss a reroute -- measuring on the raw `year` column while the pipeline reasons
    # over a period's span -- found the same day, which is why it is stated here rather than just fixed.
    #
    # A period is included when it ENDS in the era: 1934-1938 is entirely inside, 1928-1932 entirely
    # before, and nothing in this source straddles the boundary. The row keeps an EMPTY `year` and
    # carries its `period`, so a five-year mean can never be read as an observation of one year. Note
    # these rows are excluded from publication anyway (issue 310, #460), so they are evidence about the
    # era's EXTENT, not about published figures.
    per = prod[prod.year.isna() & prod.period.notna()]
    per = per[per.period.map(lambda p: (_period_end(p) or 0) >= ERA_FROM)]

    rows = []
    for r in pd.concat([prod[prod.year >= ERA_FROM], per]).itertuples():
        dated = not pd.isna(r.year)
        k = (r.country, r.item, r.year) if dated else (r.country, r.item, r.period)
        ar = (a.get(k) if dated else a_per.get(k))
        bs = base.get((r.country, r.item))
        yld = None
        if ar is not None and float(ar) > 0:
            yld = float(r.value) / float(ar)
        ratio = (float(r.value) / float(bs)) if bs is not None and float(bs) > 0 else None

        if ar is not None and float(ar) == 0.0 and float(r.value) > 0:
            v = "impossible_yield_zero_area"
        elif yld is not None and yld > IMPOSSIBLE_YIELD:
            v = "impossible_yield"
        elif yld is not None and yld > HIGH_YIELD:
            v = "high_yield_3to20"
        elif yld is not None:
            v = "plausible_yield"
        elif ratio is not None and ratio >= LEVEL_SHIFT:
            v = "no_area_level_shift"
        # `ratio is not None`, never `if ratio`: the one row this arm convicts has ratio 0.0, and a
        # truthiness test here reinstates exactly the exoneration the arm exists to remove.
        elif ratio is not None and ratio <= LEVEL_DROP:
            v = "no_area_level_drop"
        elif ratio is not None:
            v = "no_area_level_consistent"
        else:
            v = "untestable"

        rows.append({
            "source": SOURCE, "label": r.country, "whep_code": r.whep_code, "item": r.item,
            "year": (int(r.year) if dated else ""), "period": ("" if dated else str(r.period)),
            "unit": r.unit, "production": _n(r.value),
            "area_ha": ("" if ar is None else _n(ar)),
            "implied_yield": ("" if yld is None else _n(yld)),
            "own_pre_era_median": ("" if bs is None else _n(bs)),
            "ratio_to_own": ("" if ratio is None else _n(ratio)),
            "verdict": v, "convicted": str(v in CONVICTING),
        })
    rows.sort(key=lambda r: (r["verdict"], r["label"], r["item"], str(r["year"]), r["period"]))
    return rows


def write(rows: list[dict], path: str) -> None:
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
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.matched):
        print(f"panel absent ({args.matched}); nothing to do", file=sys.stderr)
        return 0

    rows = build(args.matched)
    order = ("impossible_yield_zero_area", "impossible_yield", "no_area_level_shift",
             "no_area_level_drop", "high_yield_3to20", "plausible_yield",
             "no_area_level_consistent", "untestable")
    vc = {k: sum(1 for r in rows if r["verdict"] == k) for k in order}
    conv = sum(1 for r in rows if r["convicted"] == "True")
    print(f"{len(rows)} {SOURCE} tobacco/hops production row(s) from {ERA_FROM}, "
          f"{len({r['label'] for r in rows})} label(s)")
    for k in order:
        mark = "  <- convicted" if k in CONVICTING else ""
        print(f"  {k:28} {vc[k]:4}{mark}")
    print(f"convicted on the row's own evidence: {conv} of {len(rows)} "
          f"({100.0 * conv / len(rows):.0f}%)")

    if args.check:
        if not os.path.exists(OUT):
            print(f"MISSING {os.path.relpath(OUT, REPO)}", file=sys.stderr)
            return 1
        with open(OUT, newline="") as fh:
            have = list(csv.DictReader(fh))
        if have != [{k: str(v) for k, v in r.items()} for r in rows]:
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
