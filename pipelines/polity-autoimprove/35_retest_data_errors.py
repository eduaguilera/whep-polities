#!/usr/bin/env python3
"""Re-test the QUANTITATIVE claims in state/data_errors.csv against the current data (issue 431).

WHY THIS EXISTS, AND WHY IT IS NOT A DUPLICATE OF 11_retest_conventions.py. The two curated registries in
`state/` are policed very differently, and the asymmetry has a cost:

    source_conventions.csv    validate_source_conventions.py (its own gate)
                              11_retest_conventions.py (26 mechanical re-tests)
                              a registration rule: two corroborators, and a re-test per entry

    data_errors.csv           read by SIX gates as input -- baselines, exclusions, ceilings --
                              no gate of its own, no re-test, no registration rule

The pipeline README justifies the conventions re-test on the ground that "a wrong one propagates further
than any single verdict". That argument applies here too: six gates consume this file. But nothing
re-measured whether an entry still describes reality, and on 2026-08-20 that cost showed twice.
`iia-layerb-magnitude-scale-inconsistent` sat as pending_audit with a diagnosis whose EVERY leg turned out
refutable -- its magnitude evidence cited `wheat`, which in this source is spelt and meslin -- and nothing
flagged it; it took re-deriving the entry by hand. `iia-reunion-tobacco-baseline-contaminated`, written the
same day, had its stated condition refuted within the hour by the one row not checked.

WHAT THIS COVERS, AND WHAT IT DELIBERATELY DOES NOT. Only entries resting on a REPRODUCIBLE FIGURE -- a row
count, a label count, an absence -- can be re-tested mechanically. Most of this file is single attributable
cells with no measurement behind them (`nru-1933-phosphate-transposed-with-australia`,
`cze-1910-rye-area-orphan-3ha`), and several are explicitly unrepairable, so there is nothing to re-run.
Those are out of scope by design rather than by omission, and this script says so rather than implying
coverage it does not have.

A FIGURE MISMATCH IS NOT AUTOMATICALLY AN ERROR, the same distinction 11_retest_conventions.py draws: a
count can move because the panel was reconsolidated while the diagnosis stays true. The check reports what
it now finds; whether that is drift to correct in the entry or a conclusion to withdraw is a reading.

Usage:
  python3 pipelines/polity-autoimprove/35_retest_data_errors.py [--raw PATH] [--layer-b PATH]

Exit 1 if a claim no longer reproduces; 0 on pass, or on SKIP when the inputs are absent.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(HERE, "state")
ERRORS = os.path.join(STATE, "data_errors.csv")
MATCHED = os.path.join(STATE, "matched_rows.parquet")
DEFAULT_RAW = os.path.expanduser(os.environ.get(
    "WHEP_IIA_RAW",
    "~/3itkt6h41pb7jdan/2025-10-06_iia-dataframe/outputs/processed data/harmonized_data.xlsx"))
DEFAULT_PANEL = os.path.expanduser(
    os.environ.get("WHEP_LAYER_B", "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet"))


def check_corrupted_country_labels(ctx):
    """1,237 rows carry a country label beginning `[error]`, across 93 distinct labels, and the PRODUCT
    column is clean. The product-side zero is the load-bearing half: it is what makes the corruption
    specific to the country axis rather than a general extraction failure."""
    raw = ctx["raw"]
    e = raw[raw["_c"].str.startswith("[error]")]
    prod_broken = int(raw["_p"].str.startswith("[error]").sum())
    return ([("rows", len(e), 1237), ("distinct labels", e["_c"].nunique(), 93),
             ("broken product labels", prod_broken, 0)],
            "the country axis is corrupted and the product axis is not")


def check_wheat_is_spelt_and_meslin(ctx):
    """The source carries ZERO `wheat` production or area rows -- only trade -- so layer B's iia `wheat`
    cannot have come from a wheat production series. An absence is the strongest form this file records,
    and also the easiest to falsify if a re-extraction adds one."""
    raw = ctx["raw"]
    w = raw[(raw["_p"] == "wheat") & raw["_v"].isin(["production", "area"])]
    trade = raw[(raw["_p"] == "wheat") & raw["_v"].isin(["imports", "exports", "reexports"])]
    return ([("wheat production/area rows", len(w), 0)],
            f"and {len(trade)} wheat rows remain, all trade")


def check_tobacco_era_scope(ctx):
    """The era table holds 427 rows across 93 labels. Both numbers are quoted in
    iia-tobacco-implausible-magnitudes and in issue 416's own scope, and the label count is the one that
    matters: it is what says the defect is source-wide rather than a few series."""
    v = ctx["era"]
    return ([("era rows", len(v), 427), ("labels", len({r["label"] for r in v}), 93)],
            "scope unchanged")


def check_fao1952_china_label(ctx):
    """The `China` label carries 33 rows. The entry's argument is that the label is a correct national
    total with six broken livestock cells inside it, and the row count is the denominator of that claim."""
    lb = ctx["panel"]
    ch = lb[(lb["source"] == "fao1952") & (lb["country"] == "China")]
    return ([("`China` rows", len(ch), 33)], "denominator unchanged")


# Only entries with a reproducible figure appear here. See the docstring on why the rest cannot.
CHECKS = {
    "iia-corrupted-country-labels": check_corrupted_country_labels,
    "iia-wheat-is-spelt-and-meslin": check_wheat_is_spelt_and_meslin,
    "iia-tobacco-implausible-magnitudes": check_tobacco_era_scope,
    "fao1952-china-livestock-cells-implausible": check_fao1952_china_label,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default=DEFAULT_RAW)
    ap.add_argument("--layer-b", default=DEFAULT_PANEL)
    a = ap.parse_args()

    for p in (a.raw, a.layer_b, MATCHED, ERRORS):
        if not os.path.exists(p):
            print(f"SKIP: {p} not present on this machine", file=sys.stderr)
            return 0

    import pandas as pd
    raw = pd.read_excel(a.raw)
    raw = raw.assign(_c=raw["country"].astype(str).str.strip().str.lower(),
                     _p=raw["product"].astype(str).str.strip().str.lower(),
                     _v=raw["variable"].astype(str).str.lower())
    with open(os.path.join(STATE, "era_shift_verdicts.csv"), newline="", encoding="utf-8") as fh:
        era = list(csv.DictReader(fh))
    ctx = {"raw": raw, "panel": pd.read_parquet(a.layer_b), "era": era}

    with open(ERRORS, newline="", encoding="utf-8") as fh:
        entries = list(csv.DictReader(fh))
    ids = {r["issue_id"] for r in entries}

    problems, tested = [], 0
    for eid, fn in sorted(CHECKS.items()):
        if eid not in ids:
            problems.append(f"{eid}: has a re-test here but no longer exists in data_errors.csv")
            continue
        claims, note = fn(ctx)
        for label, now, stated in claims:
            tested += 1
            ok = now == stated
            print(f"  {'ok  ' if ok else 'FAIL'} {eid[:42]:44}{label[:26]:28}{now:>9} (stated {stated})")
            if not ok:
                problems.append(f"{eid}: {label} is now {now}, the entry states {stated}")
        print(f"       -> {note}")

    print(f"\n{len(CHECKS)} entr(ies) re-tested over {tested} claim(s); "
          f"{len(ids) - len(CHECKS)} of {len(ids)} entries carry no reproducible figure and are out of "
          f"scope by design")
    if problems:
        print(f"\nFAIL: {len(problems)} claim(s) no longer reproduce", file=sys.stderr)
        for p in problems:
            print("  - " + p, file=sys.stderr)
        return 1
    print("PASS: every re-testable claim in data_errors.csv still reproduces")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
