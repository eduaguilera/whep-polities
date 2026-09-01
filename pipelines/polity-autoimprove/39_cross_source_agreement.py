#!/usr/bin/env python3
"""Two independent sources on ONE polity: the free validation surface from issue 375.

Issue 360 recorded, correctly, that cross-source validation is impossible here because zero cells
carry two sources -- keyed on the LABEL. Keyed on the POLITY it is a different number, because
different labels routing to the same polity make independent publishers directly comparable. Issue
375 measured 786 such cells and called it "a free validation surface that has never been used".

This publishes it, so it can be used. Every (polity, item, unit, year) cell carrying more than one
source, with the ratio between the extreme values and -- for the large disagreements -- which
`data_errors.csv` entry already explains it.

WHY THE COVERAGE COLUMN IS THE POINT. Median agreement is 1.0011, so the surface is mostly two
publishers confirming each other to four figures. The tail is what matters, and today every cell of
it is a defect this repo has already recorded: wheat is spelt and meslin, tobacco and hops are the
1934 scale break, `czech republic` and `serbia` are layer-B labels fed by several raw labels at
different territorial levels. A cell in the tail with NO entry behind it would be new, and there is
currently no such cell -- which is what makes zero a usable ceiling rather than an aspiration.

THE KEY DELIBERATELY EXCLUDES `indicator`, and that is not an oversight. The column carries a
different KIND of value per source: fao1952 and iia use a measurement type (`crops:production`,
`livestock:production`), while mitchell uses a page reference (`page_12_table_1`). Adding it to the
key separates iia from mitchell on a field that does not mean the same thing in each, which destroys
exactly the comparisons this table exists for -- 53 of the 804 cells pair a null indicator against a
mitchell page string. `unit` already separates production from area, which is what the column would
otherwise be protecting against.

Two things make that easy to get wrong. 126,631 of 189,578 rows have a NULL indicator, so
`groupby(..., dropna=True)` -- the default -- silently drops two thirds of the panel and returns ZERO
multi-source cells, which reads as "the key needs no fixing" for the wrong reason. And `nunique()`
excludes nulls too, so a check for "does this cell mix indicators" answers 0 when half its rows have
none. Arm E in the gate tests the thing that WOULD invalidate a comparison -- both sides annotated and
disagreeing -- rather than the presence of the column.

NO --check MODE, DELIBERATELY. This reads layer B, which is not redistributable and is absent in CI,
so a check comparing the committed table against a regeneration could only ever run on a developer
machine -- and would report OK in CI by comparing nothing. That is the failure issue 573 describes.
The gate reads the committed table instead, and this script is how the table is refreshed.
"""
from __future__ import annotations

import csv
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MATCHED = os.path.join(HERE, "state/matched_rows.parquet")
ERRORS = os.path.join(HERE, "state/data_errors.csv")
OUT = os.path.join(HERE, "state/cross_source_agreement.csv")

# `>=`, not `>`. A ratio of EXACTLY 10 is the single most diagnostic value here -- it is what a
# dropped or added zero produces -- and a strict `>` excluded a whole cluster of hops and rye cells
# sitting on 10.0000, which then printed an empty `known_defect` that reads as "nothing explains
# this" when it means "never tested". Same shape as the one-sided thresholds recorded in the
# retest registry: the excluded tail was the interesting one.
BIG_RATIO = 10.0
COLUMNS = ("polity_code", "item", "unit", "year", "sources", "labels", "indicators",
           "value_min", "value_max", "ratio", "known_defect")


def coverage(row, errors):
    """Which recorded defect entries could explain this cell.

    An entry with commodity `(all)` or a placeholder label covers by SOURCE and YEAR alone -- that is
    how `layerb-nested-reporting-levels-one-polity` covers the `czech republic` beans cells, and
    excluding those entries is a live way to manufacture false findings: it reported 6 uncovered
    cells that are all explained by exactly that entry.
    """
    hits = []
    for e in errors:
        if e["source"] and not any(s in e["source"].split(";") for s in row["sources"].split(";")):
            continue
        # POLITY SCOPE (issue 635). An entry that names polity codes concerns THOSE polities, and
        # this filter is what makes that true of the matching as well as of the entry. Without it
        # `layerb-nested-reporting-levels-one-polity` -- 17 declared codes, `commodity = (all)`, a
        # placeholder label, all four sources, 1909-1960 -- matched 804 of 804 cells, so
        # BASELINE_UNEXPLAINED = 0 could never be exceeded and the gate's headline arm was dead.
        # It also attributed 8 real disagreements to itself: czech `beans, dry` x7 (two raw series,
        # layer B keeps one) and yugoslav `sunflower seed` (production x10), on polities absent from
        # its own list and commodities its summary never mentions. Both are now registered in their
        # own right (#636), which is why this filter does not turn the gate red.
        #
        # An entry that legitimately covers broadly leaves `polity_code` BLANK; declaring codes is
        # what opts an entry into being scoped.
        codes = [c for c in (e.get("polity_code") or "").split(";") if c.strip()]
        if codes and row["polity_code"] not in [c.strip() for c in codes]:
            continue
        try:
            if e["year_min"] and e["year_max"] and not (
                    int(e["year_min"]) <= int(row["year"]) <= int(e["year_max"])):
                continue
        except ValueError:
            pass
        com = (e["commodity"] or "").lower()
        if com and com != "(all)" and row["item"].lower().split(",")[0] not in com:
            continue
        lab = (e["label"] or "").lower()
        if lab and not lab.startswith("("):
            if not any(l in lab or lab in l for l in row["labels"].split(";")):
                continue
        hits.append(e["issue_id"])
    return ";".join(sorted(set(hits)))


def main() -> int:
    if not os.path.exists(MATCHED):
        print(f"SKIP: {os.path.relpath(MATCHED, REPO)} absent -- run 01_match_and_findings.py first")
        return 0
    frame = pd.read_parquet(MATCHED)
    frame = frame[frame.whep_code.notna() & frame.value.notna()].copy()
    frame["yr"] = frame["year"].astype(str)
    key = ["whep_code", "item", "unit", "yr"]
    multi = frame[frame.groupby(key)["source"].transform("nunique") > 1]
    # dropna=False on every groupby whose key can hold a null. `indicator` is not in this key, but
    # `unit` and `item` can be blank, and the default would drop those rows without saying so.
    agg = multi.groupby(key, dropna=False).agg(
        value_min=("value", "min"),
        value_max=("value", "max"),
        sources=("source", lambda s: ";".join(sorted(set(s)))),
        labels=("country", lambda s: ";".join(sorted({str(x).lower() for x in s}))),
        # Nulls counted as their own value -- see the docstring on why nunique() would not do.
        indicators=("indicator", lambda s: ";".join(sorted({
            "" if pd.isna(x) else str(x) for x in s}))),
    ).reset_index()
    agg = agg[agg.value_min > 0].copy()
    agg["ratio"] = agg.value_max / agg.value_min

    with open(ERRORS, newline="", encoding="utf-8") as fh:
        errors = [e for e in csv.DictReader(fh) if e["status"] in ("confirmed", "pending_audit")]

    rows = []
    for r in agg.itertuples():
        row = {"polity_code": r.whep_code, "item": r.item, "unit": r.unit, "year": r.yr,
               "sources": r.sources, "labels": r.labels, "indicators": r.indicators,
               "value_min": f"{r.value_min:.4g}", "value_max": f"{r.value_max:.4g}",
               "ratio": f"{r.ratio:.4f}", "known_defect": ""}
        # Coverage is computed for EVERY cell, not only the large ones, so an empty column always
        # means "no recorded entry explains this" rather than "not looked at".
        row["known_defect"] = coverage(row, errors)
        rows.append(row)
    rows.sort(key=lambda r: (-float(r["ratio"]), r["polity_code"], r["item"], r["year"]))

    tmp = OUT + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, OUT)

    big = [r for r in rows if float(r["ratio"]) >= BIG_RATIO]
    unexplained = [r for r in big if not r["known_defect"]]
    print(f"wrote {os.path.relpath(OUT, REPO)}: {len(rows):,} cells across "
          f"{len({r['polity_code'] for r in rows})} polities")
    print(f"  median ratio {agg.ratio.median():.4f}   >={BIG_RATIO:g}x: {len(big)}   "
          f"of those with NO recorded defect: {len(unexplained)}")
    for r in unexplained[:10]:
        print(f"   UNEXPLAINED  {r['polity_code']:16}{r['item'][:22]:24}{r['unit'][:8]:10}"
              f"{r['year']:6}{r['ratio']:>12}x  {r['sources']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
