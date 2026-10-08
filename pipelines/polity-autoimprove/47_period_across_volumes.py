#!/usr/bin/env python3
"""A series' 1934-1938 average must resemble its own 1928-1932 average -- the third member of the
42/43 family, and the one screen that needs neither a second source nor a dated year (issue 640).

WHAT IS NEW HERE. 42_period_volume_provenance.py shows each period label is printed by exactly ONE
iia volume; 43_period_vs_dated_consistency.py compares a period average with ITS OWN dated years.
Neither compares one volume's average with the PREVIOUS volume's average for the same series:
`1928-1932` is printed by iia_1938_39 and `1934-1938` by iia_1939_45. Six years apart the two should
be about equal, and that is testable for every (label, item, unit) present in both volumes -- 1,324
pairs -- including the series that have no dated years at all (which 43 cannot reach).

THE CONTROL IS BUILT IN. The median ratio over the 1,324 pairs is 1.093 (p10 0.54, p25 0.90,
p75 1.55, p90 3.0): a real series drifts a little between those windows, and a ratio of 30x in
either direction is therefore not drift. 17 pairs sit beyond 30x, running BOTH ways (12 high, 5
low), which is why a one-directional threshold would miss a third of them.

VALUE-SCALE DIVISORS (data/final/source_value_scale_corrections.csv, #416/#717). Those rules divide
DATED rows only (a period row cannot be assigned a volume by its years), so no period value is
divided here; the screen compares what the source printed. That is the right comparison for the
tobacco/hops blocks the rules cover, because BOTH period rows of such a series sit in the
x100 late volumes: `rule_covered` marks the pairs whose 1934-1938 span lies inside a rule and the
gate pins their median ratio near 1, which is the evidence that dividing one side only would break
the screen rather than repair it. A tobacco pair is a break here only when it disagrees with its own
previous average ON TOP of the shared unit change (czech republic 36x, dominican republic 636x).

THE BREAKS ARE A BASELINE, NOT A VERDICT. Each of the 17 is explained in
scripts/validate_period_across_volumes.py by a data_errors entry or by a documented reason, and a
new break fails the gate. What the ratio cannot say is WHICH SIDE moved or by what factor: bulgaria
beans is 925x the previous volume but the factor is x1000 (fixed by the yield identity), and china
groundnuts' LOW side is the earlier one. The table records the disagreement, never a culprit.

Excludes pairs whose 1928-1932 value is not positive (a zero satisfies no ratio; #414 owns zeros).
"""
import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "period_across_volumes.csv")
DEFAULT_PANEL = os.path.expanduser(
    os.environ.get("WHEP_LAYER_B") or os.environ.get("WHEP_LAYERB")
    or "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet")

EARLY, LATE = "1928-1932", "1934-1938"
LATE_SPAN = (1934, 1938)
BREAK = 30.0            # the issue's threshold: beyond 30x either way is not six years of drift
FIELDS = ["label", "item", "unit", "value_1928_1932", "value_1934_1938", "ratio", "rule_covered",
          "verdict"]


def classify(ratio):
    if ratio >= BREAK:
        return "break_higher"
    if ratio <= 1.0 / BREAK:
        return "break_lower"
    return "within_band"


def rule_covers(rules, item, unit, label):
    """True when a value-scale rule would divide DATED rows of this series across the late span."""
    for ru in rules:
        if (ru["source"] == "iia" and ru["item"] == item and ru["unit"] == unit
                and ru["y0"] <= LATE_SPAN[0] and ru["y1"] >= LATE_SPAN[1]
                and label not in ru["exempt"]):
            return True
    return False


def build(panel_path):
    import pandas as pd
    import extdata
    import matchlib
    rules = matchlib.load_value_scale_corrections(extdata.VALUE_SCALE_CORRECTIONS)
    lb = pd.read_parquet(panel_path)
    per = lb[(lb["source"] == "iia") & lb["value"].notna() & lb["year"].isna()
             & lb["period"].astype(str).isin([EARLY, LATE])]
    key = ["country", "item", "unit"]
    if per.duplicated(key + ["period"]).any():
        raise SystemExit("more than one iia row per (label, item, unit, period): the pair is "
                         "ambiguous, so this screen cannot choose a value")
    wide = per.pivot(index=key, columns="period", values="value").dropna()
    rows = []
    for (c, i, u), r in wide.iterrows():
        e, l = float(r[EARLY]), float(r[LATE])
        if e <= 0 or l <= 0:
            continue
        ratio = l / e
        rows.append({"label": c, "item": i, "unit": u, "value_1928_1932": round(e, 4),
                     "value_1934_1938": round(l, 4), "ratio": round(ratio, 6),
                     "rule_covered": str(rule_covers(rules, i, u, c)),
                     "verdict": classify(ratio)})
    rows.sort(key=lambda r: (r["item"], r["label"], r["unit"]))
    return rows


def report(rows):
    import collections
    import statistics
    rs = [r["ratio"] for r in rows]
    q = statistics.quantiles(rs, n=10)
    print(f"{len(rows)} comparable pairs; median ratio {statistics.median(rs):.4f} "
          f"(p10 {q[0]:.3f}, p90 {q[-1]:.3f})  <- the control")
    cov = [r["ratio"] for r in rows if r["rule_covered"] == "True"]
    if cov:
        print(f"{len(cov)} pairs sit under a value-scale rule; their median ratio is "
              f"{statistics.median(cov):.4f}")
    for v, n in sorted(collections.Counter(r["verdict"] for r in rows).items()):
        print(f"  {v:14s} {n:5d}")
    for r in sorted((r for r in rows if r["verdict"] != "within_band"), key=lambda r: r["ratio"]):
        print(f"  {r['label'][:24]:26s} {r['item'][:24]:26s} {r['unit']:7s} "
              f"{r['value_1928_1932']:>13,.1f} -> {r['value_1934_1938']:>15,.1f}  {r['ratio']:.4g}x")


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
