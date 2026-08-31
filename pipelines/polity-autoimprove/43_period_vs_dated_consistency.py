#!/usr/bin/env python3
"""A multi-year average must equal the mean of the years it covers, and 1,655 IIA pairs let us check
it -- a detector with its own built-in control (issues 424, 416).

WHAT IS NEW HERE. Every existing IIA magnitude test compares a cell to something OUTSIDE it: another
volume (26_edition_conflicts.py), another source (39_cross_source_agreement.py), the label's own
pre-1934 history (29_era_shift_verdicts.py), or an absolute threshold. Each needs a second opinion to
exist, and #424 exists precisely because its x10 class sits under the 20x floor that the collapse and
spike screens share.

This test needs no second opinion. A period row and the dated rows inside its span are the SAME
series, so their relationship is fixed by arithmetic rather than by judgement: `1934-1938` must be
about the mean of 1934..1938. Where both sides exist the ratio is a self-contained measurement.

THE CONTROL IS BUILT IN, AND IT IS WHAT MAKES THE TAILS MEAN ANYTHING. Over 1,655 comparable pairs the
median ratio is 1.000 in EVERY volume:

    iia_1925_26   n= 224   median 1.000     (the 1909-1913 average)
    iia_1938_39   n= 642   median 1.005     (1928-1932)
    iia_1939_45   n= 789   median 1.000     (1934-1938)

So the source computes its own averages correctly as a rule, and a ratio near a power of ten is a
defect rather than a modelling artefact. Contrast a threshold test, which has no way to say what
normal looks like.

WHAT IT FINDS. 20 pairs sit within 15% of 100x and 11 within 15% of a tenth.

  - 18 of the 20 at ~100x are tobacco (16) or hops (2), all in `1928-1932`, i.e. #416's inflation
    arriving through the period rows. That is independent corroboration at the SERIES level: #416's
    published scope screens on an absolute 500,000 t, which cannot distinguish a big producer from an
    inflated one, whereas a series compared against itself can.
  - 4 of the 11 low cases are hops AREA, the second fault already recorded in `iia-hops-x100`. This
    test reaches it on a slice that entry does not use -- the entry measures the 1933 overlap between
    two volumes, this measures 1934-1938 inside one.
  - TWO x100 CELLS FALL OUTSIDE EVERY RECORDED ITEM SCOPE. `israel / olives / 1934-1938` reads
    3,075,400 t against a dated mean of 30,660 and against its OWN sibling period rows of 15,751
    (1925-1929) and 12,300 (1928-1932) -- 3 Mt is more olives than the Mediterranean produced, so the
    cell is impossible on three independent comparisons. `indonesia / cotton lint / 1909-1913` reads
    3,990 t against a dated mean of 39, and exceeds every value the series ever reaches; it sits in
    `iia_1925_26`, a volume otherwise clean.
  - The remaining 7 low cases are items in no existing entry: hempseed, oranges, sugar raw
    centrifugal, sesame seed, flax fibre and tow, cotton lint, grapes.

WHICH SIDE IS WRONG IS NOT DECIDED HERE, and the table does not pretend otherwise. The ratio says the
two disagree by a factor of ten; it cannot say which one moved. Both directions occur in the low set:
for `czech republic / hops / ha` the period figure (11,300) is the historically plausible one and the
dated mean (112,800) exceeds world hops area, while for `bulgaria / sugar raw centrifugal` the dated
mean (16,140) is plausible and the period figure (1,600) is the low one. `verdict` therefore records
the DISAGREEMENT and its factor, never a culprit.

Requires at least 3 dated years inside the span, and excludes zero on either side -- a zero satisfies
no ratio and #414 is a separate defect. `1925-1929` yields no comparable pair at all: layer B has no
series with 3+ dated years in that window, which is itself worth knowing.
"""
import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "period_vs_dated_consistency.csv")
DEFAULT_PANEL = os.path.expanduser(
    os.environ.get("WHEP_LAYER_B", "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet"))

# Restated from 42_period_volume_provenance.py: each period label is printed by exactly one volume.
VOL = {"1900-1913": "iia_1925_26", "1909-1913": "iia_1925_26", "1921-1925": "iia_1929_30",
       "1924-1928": "iia_1933_34", "1925-1929": "iia_1933_34", "1928-1932": "iia_1938_39",
       "1934-1938": "iia_1939_45"}
SPAN = {p: (int(p[:4]), int(p[5:])) for p in VOL}
MIN_DATED = 3          # two years is not a mean worth testing
TOL = 0.15             # "within 15% of a clean power of ten"
FIELDS = ["source", "label", "item", "unit", "period", "volume", "period_value", "dated_mean",
          "dated_n", "dated_first", "dated_last", "ratio", "verdict"]


def classify(ratio):
    """Name the disagreement and its factor. Never names a culprit -- see the module docstring."""
    for factor, lo, hi in ((100.0, 100 * (1 - TOL), 100 * (1 + TOL)),
                           (10.0, 10 * (1 - TOL), 10 * (1 + TOL))):
        if lo <= ratio <= hi:
            return f"disagree_x{int(factor)}_period_higher"
    for factor, lo, hi in ((100.0, 1 / (100 * (1 + TOL)), 1 / (100 * (1 - TOL))),
                           (10.0, 1 / (10 * (1 + TOL)), 1 / (10 * (1 - TOL)))):
        if lo <= ratio <= hi:
            return f"disagree_x{int(factor)}_dated_higher"
    if 0.5 <= ratio <= 2.0:
        return "consistent"
    return "unexplained_period_higher" if ratio > 2.0 else "unexplained_dated_higher"


def build(panel_path):
    import pandas as pd
    lb = pd.read_parquet(panel_path)
    iia = lb[(lb["source"] == "iia") & lb["value"].notna()]
    dated = iia[iia["year"].notna()]
    per = iia[iia["year"].isna() & iia["period"].astype(str).isin(VOL)]
    # dropna=False is deliberate: `indicator` is null on all 26,175 iia rows, and the default would
    # drop every group if it were ever added to this key. It is not in the key for that reason.
    idx = {k: v for k, v in dated.groupby(["country", "item", "unit"], dropna=False)}
    rows = []
    for _, r in per.iterrows():
        d = idx.get((r["country"], r["item"], r["unit"]))
        if d is None:
            continue
        lo, hi = SPAN[str(r["period"])]
        w = d[(d["year"] >= lo) & (d["year"] <= hi)]
        if len(w) < MIN_DATED:
            continue
        m = float(w["value"].mean())
        pv = float(r["value"])
        if m <= 0 or pv <= 0:
            continue
        rows.append({
            "source": "iia", "label": r["country"], "item": r["item"], "unit": r["unit"],
            "period": str(r["period"]), "volume": VOL[str(r["period"])],
            "period_value": round(pv, 4), "dated_mean": round(m, 4), "dated_n": len(w),
            "dated_first": int(w["year"].min()), "dated_last": int(w["year"].max()),
            "ratio": round(pv / m, 6), "verdict": classify(pv / m),
        })
    rows.sort(key=lambda r: (r["period"], r["item"], r["label"], r["unit"]))
    return rows


def report(rows):
    import collections
    import statistics
    print(f"{len(rows)} comparable pairs (>= {MIN_DATED} dated years inside the span, both sides "
          f"non-zero)")
    print("\nTHE CONTROL -- a period average normally equals the mean of its own years:")
    for vol in sorted({r["volume"] for r in rows}):
        d = [r["ratio"] for r in rows if r["volume"] == vol]
        print(f"  {vol:12s} n={len(d):4d}  median {statistics.median(d):6.3f}")
    print("\nverdicts:")
    for v, n in sorted(collections.Counter(r["verdict"] for r in rows).items(),
                       key=lambda kv: -kv[1]):
        print(f"  {v:34s} {n:5d}")
    for v in ("disagree_x100_period_higher", "disagree_x10_dated_higher"):
        d = [r for r in rows if r["verdict"] == v]
        if not d:
            continue
        print(f"\n{v} ({len(d)}):")
        for r in sorted(d, key=lambda r: r["ratio"]):
            print(f"  {r['label'][:24]:26s} {r['item'][:22]:24s} {r['unit']:7s} {r['period']:10s} "
                  f"{r['volume']:12s} {r['period_value']:>12,.1f} vs {r['dated_mean']:>11,.1f} "
                  f"= {r['ratio']:.3f}x")
        print(f"  items: {dict(collections.Counter(r['item'] for r in d))}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--layer-b", default=DEFAULT_PANEL)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(a.layer_b):
        print(f"SKIP: layer B panel not present on this machine ({a.layer_b})", file=sys.stderr)
        return 0
    rows = build(a.layer_b)
    report(rows)
    if a.check:
        if not os.path.exists(OUT):
            print(f"MISSING {OUT}; run with --write", file=sys.stderr)
            return 1
        with open(OUT, newline="", encoding="utf-8") as fh:
            have = list(csv.DictReader(fh))
        want = [{k: str(v) for k, v in r.items()} for r in rows]
        if have != want:
            print(f"STALE {OUT}: {len(have)} on disk, {len(want)} rebuilt", file=sys.stderr)
            for h, w in zip(have, want):
                if h != w:
                    print(f"  first difference:\n    disk  {h}\n    built {w}", file=sys.stderr)
                    break
            return 1
        print(f"\nOK {os.path.basename(OUT)} matches a fresh rebuild ({len(have)} rows)")
    if a.write:
        from atomic import write_csv_atomic
        write_csv_atomic(OUT, FIELDS, rows)
        print(f"\nwrote {OUT} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    raise SystemExit(main())
