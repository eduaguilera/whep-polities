#!/usr/bin/env python3
"""Where do two IIA yearbook VOLUMES disagree about the same cell, and where is one of them zero?

The raw IIA extract carries a `yearbook` column naming the volume each row came from -- six of them,
`iia_1909_21` through `iia_1939_45`. Nothing in this repo had used it, and it answers a question no
amount of internal consistency checking can: **the source disagrees with itself, and one volume can be
shown wrong by another.**

Every other check here compares the panel against a polity, an area, a sibling series or a second
source. This compares one edition of ONE source against another edition of the same source, which is
the only comparison that can convict an extraction of a specific cell.

WHAT THE FIRST RUN MEASURED (issue 414). Zero rates on production and area rows are not comparable
across volumes:

    iia_1909_21    8,635 rows   zeros  71 = 0.82%
    iia_1925_26    5,798 rows   zeros   7 = 0.12%
    iia_1929_30    8,297 rows   zeros   8 = 0.10%
    iia_1933_34   10,047 rows   zeros  11 = 0.11%
    iia_1938_39   14,565 rows   zeros 940 = 6.45%   <- 6x to 60x every other volume
    iia_1939_45   16,611 rows   zeros  65 = 0.39%

85% of the extract's production/area zeros come from one volume, and where a second volume covers the
same cell it is NON-ZERO 87 times out of 88. Austria's 1933 meslin area is 0 in `iia_1938_39` and
8,588 ha in `iia_1933_34`.

THE COVERAGE CAVEAT IS THE POINT, NOT A WEAKNESS. Only 88 of 770 zeros are testable, because most of
that volume's years are covered by no other volume -- 1933 is the only overlapping year. That is also
why the defect survives into layer B: for 1934-1938 there is no second opinion for the pipeline to
prefer, and the zeros pass through (149->119, 148->120), while for 1933 most are resolved (179->61).

WHY UNIT AND VARIABLE MUST BOTH BE IN THE KEY. An earlier pass at this compared `area` rows against
`production` rows because it keyed only on (label, product, year), and reported medians mixing
hectares with tonnes. The raw vocabulary separates them (`variable` in {production, area, ...},
`unit` in {tonnes, hectares, heads}) and so must the key.

WHY A TRACKED TABLE. Needs the raw extract, which lives outside the repo and is absent in CI, so this
writes `state/edition_conflicts.csv`, that file is committed, and the gate reads it -- the same
arrangement as 16_source_splices.py, 17_constant_runs.py and 25_same_polity_overlaps.py.

Usage:
  python3 pipelines/polity-autoimprove/26_edition_conflicts.py            # report only
  python3 pipelines/polity-autoimprove/26_edition_conflicts.py --write    # refresh the table
  python3 pipelines/polity-autoimprove/26_edition_conflicts.py --check    # fail if stale
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "edition_conflicts.csv")
DEFAULT_RAW = os.path.expanduser(os.environ.get(
    "WHEP_IIA_RAW",
    "~/3itkt6h41pb7jdan/2025-10-06_iia-dataframe/outputs/processed data/harmonized_data.xlsx"))

# Only the variables layer B actually carries. Trade rows are 74% of the extract and would swamp the
# zero rates with a different phenomenon -- an unreported import is genuinely zero far more often than
# an unreported harvest.
MEASURED = {"production", "area"}

# A relative gap this small is float noise from the extract's own round-trips.
EPS = 1e-9

# How close to a clean power of ten a ratio must sit to be called one. The same 5% window
# 07_yield_consistency.py uses for the identical question about yields, so the two cannot disagree
# about what "a dropped digit" means. NOT fitted: the observed x10 cases run 9.67 to 10.26 and the
# x100 cases cluster tightly, while ordinary revisions have a median ratio of 1.032.
POW10_WINDOW = 0.05

FIELDS = ["label", "product", "variable", "unit", "year", "kind",
          "volume_a", "value_a", "volume_b", "value_b", "ratio"]


def power_of_ten(ratio: float) -> int | None:
    """The exponent if `ratio` is within POW10_WINDOW of 10, 100 or 1000, else None.

    Exponent 0 is excluded on purpose: every ratio is "within 5% of 10**0" once it is close to 1,
    and calling those power-of-ten cases would swallow the whole `revised` class.
    """
    import math

    if ratio <= 0:
        return None
    p = round(math.log10(ratio))
    if p == 0 or abs(p) > 3:
        return None
    return p if abs(ratio / (10.0 ** p) - 1.0) <= POW10_WINDOW else None


def build(raw_path: str) -> tuple[list[dict], dict]:
    import pandas as pd

    d = pd.read_excel(raw_path)
    d["cl"] = d["country"].astype(str).str.strip().str.lower()
    d["vl"] = d["variable"].astype(str).str.strip().str.lower()
    d["ul"] = d["unit"].astype(str).str.strip().str.lower()
    d["pl"] = d["product"].astype(str).str.strip()
    d["y"] = pd.to_numeric(d["year"], errors="coerce")
    d = d[d["value"].notna() & d["y"].notna() & d["vl"].isin(MEASURED)]

    volumes = {}
    for vol, g in d.groupby("yearbook"):
        volumes[str(vol)] = {"rows": int(len(g)), "zeros": int((g["value"] == 0).sum())}

    key = ["cl", "pl", "vl", "ul", "y"]
    rows = []
    for k, g in d.groupby(key):
        per = g.groupby("yearbook")["value"].median()
        if len(per) < 2:
            continue
        items = sorted(per.items(), key=lambda kv: str(kv[0]))
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                (va, xa), (vb, xb) = items[i], items[j]
                xa, xb = float(xa), float(xb)
                if abs(xa - xb) <= max(abs(xa), abs(xb)) * EPS:
                    continue
                # THREE KINDS, because the evidence each supports is different.
                #
                # `zero_contradicted` -- one volume prints a value and the other prints 0. Provably
                # wrong whichever way, since a zero publishes as "produced none of this".
                #
                # `power_of_ten` -- the two differ by a clean factor of 10, 100 or 1000. A source
                # does not revise an estimate by exactly a hundredfold; that is a dropped digit or a
                # units column read as absolute. The DIRECTION is what makes this more than a
                # pattern: across all 1,032 revisions between iia_1933_34 and iia_1938_39 the
                # 1933-34 volume is the smaller side 55% of the time -- a coin flip -- but among the
                # power-of-ten cases it is smaller 98 times out of 99. The x100 cases are ENTIRELY
                # tobacco (52) and hops (13), which is issue 416 seen from the volume side; the x10
                # cases span twelve products and are issue 424.
                #
                # `revised` -- everything else. A source restating an estimate is normal, and the
                # ceiling on this class exists to catch a volume being double-loaded, not to convict
                # a cell.
                if xa == 0 or xb == 0:
                    kind = "zero_contradicted"
                elif power_of_ten(max(abs(xa), abs(xb)) / min(abs(xa), abs(xb))):
                    kind = "power_of_ten"
                else:
                    kind = "revised"
                hi, lo = max(abs(xa), abs(xb)), min(abs(xa), abs(xb))
                rows.append({
                    "label": k[0], "product": k[1], "variable": k[2], "unit": k[3],
                    "year": int(k[4]), "kind": kind,
                    # .12g, not .6g: the volumes differ by rounding as well as by revision --
                    # french algeria wine 1933 is 1,522,516.996 in iia_1933_34 and 1,522,521.0 in
                    # iia_1938_39 -- and at six significant figures both print identically, so the
                    # table recorded a conflict it could not display. The gate caught exactly that.
                    "volume_a": str(va), "value_a": f"{xa:.12g}",
                    "volume_b": str(vb), "value_b": f"{xb:.12g}",
                    "ratio": "inf" if lo == 0 else f"{hi / lo:.4f}",
                })
    rows.sort(key=lambda r: (r["kind"], r["label"], r["product"], r["variable"],
                             r["unit"], r["year"], r["volume_a"], r["volume_b"]))
    return rows, volumes


def write(rows: list[dict], path: str) -> None:
    """Build fully in memory then replace atomically -- a truncating open() has cost this repo two
    tracked state files mid-error."""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default=DEFAULT_RAW)
    ap.add_argument("--write", action="store_true", help=f"refresh {os.path.relpath(OUT, REPO)}")
    ap.add_argument("--check", action="store_true", help="exit 1 if the tracked table is stale")
    args = ap.parse_args()

    if not os.path.exists(args.raw):
        print(f"raw IIA extract absent ({args.raw}); nothing to do", file=sys.stderr)
        return 0

    rows, volumes = build(args.raw)
    print("production+area zero rate by yearbook volume:")
    for vol in sorted(volumes):
        v = volumes[vol]
        print(f"  {vol:14} {v['rows']:>6} rows   zeros {v['zeros']:>4} = {v['zeros']/v['rows']:.2%}")
    kinds = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print(f"\ncells carried by >1 volume that disagree: {len(rows)}")
    for k in sorted(kinds):
        print(f"  {k:20} {kinds[k]}")

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
