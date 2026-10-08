#!/usr/bin/env python3
"""Guard `data/final/source_value_null_corrections.csv` (issue 414).

WHAT THE TABLE IS. Layer B carries some IIA cells as 0 where the printed yearbook gives NO FIGURE: a
dash, `...`, or the volume's see-notes marker `-o)`, which the transcription typed as 0. A 0 is then
averaged into the panel as an observation of "none". The repair withholds the value -- it does not
estimate one -- so the table is one row per (source, label, item, unit, year) cell, keyed on the
label layer B prints, DATED rows only (the harmonized build drops period averages anyway).

A ROW DOES NOT REWRITE `value`. matchlib.value_null_mask yields a per-row flag that
01_match_and_findings.py writes to matched_rows.parquet as `value_is_null`, and the harmonized build
(pipelines/historical-production-harmonized/build.R) turns it into NA. Every diagnostic that convicts
the printed 0 (40_zero_grid_floor.py, 07_yield_consistency.py, the edition tables) keeps seeing it.

WHAT A ROW NEEDS. A 0 is a value unless something shows otherwise, and in the IIA's coarse volumes a
printed `0` is the grid's way of writing "under half a unit" (issue 446): iia_1938_39 prints the
digit in its own tables, so its 940 production/area zeros are NOT blanks and are not in this table.
`evidence_rule` names what refutes the 0:

  scan_no_figure                the scanned page prints a non-figure glyph in the cell
                                (`printed_glyph`, `evidence_ref` names the pdf and page)
  refuted_by_paired_axis        state/zero_grid_floor.csv refutes it: no sub-grid value fits the
                                tonnage (or area) printed beside it
  contradicted_by_other_volume  state/edition_conflicts.csv: another edition prints a value the
                                volume's grid cannot round to 0 (`grid_cannot_explain`)

WHAT THIS GATE CHECKS, and which arms run where.

  Everywhere (CI included -- none of it needs layer B):
    A  shape: matchlib's loader (exact header, one cell per row, a dated year, a known evidence rule,
       a non-figure glyph), printed_value 0, a positive observed_rows, a non-empty issue/evidence.
    B  the ADJUDICATED cells, pinned bidirectionally and in full. A deleted row silently puts a
       false zero back in the panel; an added one withholds a value nobody adjudicated.
    C  the evidence still stands in tracked state: a refuted_by_paired_axis row names a
       `refuted_by_paired_axis` row of state/zero_grid_floor.csv; a contradicted_by_other_volume row
       names a `zero_contradicted` / `grid_cannot_explain` row of state/edition_conflicts.csv; a
       scan_no_figure row names a pdf page.

  Where layer B and matched_rows.parquet are present (a maintainer's machine; SKIPped by name in CI):
    D  scope: each cell selects exactly `observed_rows` non-aggregate layer-B rows, all of them 0.
    E  the matcher's output agrees: matched_rows.parquet carries `value_is_null`, equal row for row
       to the mask the table implies on the label layer B prints.

Usage:
  python3 scripts/validate_value_null_corrections.py
"""
from __future__ import annotations

import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "data/final/source_value_null_corrections.csv")
STATE = os.path.join(REPO, "pipelines/polity-autoimprove/state")
MATCHED = os.path.join(STATE, "matched_rows.parquet")

# Arm B. Every adjudicated cell: (source, label, item, unit, year, evidence_rule, glyph, observed_rows).
# Raise deliberately, with the new cell's evidence in its row.
# 2026-10-07 (issue 414): every dated iia 0 in layer B outside iia_1938_39 was read on the scanned page
# (iia_1938_39 prints the digit 0 as its grid floor: 24 of a 25-cell random sample are a printed 0).
# These 44 are the cells whose page shows no zero; the printed zeros (fertilizers 1909-1920, sugar
# 1909-1933, french guiana eggs 1942-1944 `0,0`) stay as values.
BASELINE = frozenset({
    ('iia', 'nigeria', 'cotton lint', 'ha', 1939, 'refuted_by_paired_axis', '—', 1),
    ('iia', 'nigeria', 'cotton lint', 'ha', 1940, 'refuted_by_paired_axis', '—', 1),
    ('iia', 'nigeria', 'cotton lint', 'ha', 1941, 'refuted_by_paired_axis', '—', 1),
    ('iia', 'nigeria', 'cotton lint', 'ha', 1942, 'refuted_by_paired_axis', '—', 1),
    ('iia', 'nigeria', 'cotton lint', 'ha', 1943, 'refuted_by_paired_axis', '—', 1),
    ('iia', 'nigeria', 'cotton lint', 'ha', 1944, 'refuted_by_paired_axis', '—', 1),
    ('iia', 'nigeria', 'cotton lint', 'ha', 1945, 'scan_no_figure', '—', 1),
    ('iia', 'congo', 'cotton lint', 'ha', 1939, 'refuted_by_paired_axis', '-', 1),
    ('iia', 'dominican republic', 'tobacco, unmanufactured', 'ha', 1939, 'refuted_by_paired_axis', '—', 1),
    ('iia', 'germany', 'tobacco, unmanufactured', 'tonnes', 1945, 'scan_no_figure', '-o)', 1),
    ('iia', 'guyana', 'cacao, beans', 'tonnes', 1939, 'scan_no_figure', '—', 1),
    ('iia', 'guyana', 'cacao, beans', 'tonnes', 1940, 'scan_no_figure', '—', 1),
    ('iia', 'guyana', 'cacao, beans', 'tonnes', 1941, 'scan_no_figure', '—', 1),
    ('iia', 'netherlands', 'tobacco, unmanufactured', 'tonnes', 1945, 'scan_no_figure', '—', 1),
    ('iia', 'poland', 'hops', 'ha', 1945, 'scan_no_figure', '-o)', 1),
    ('iia', 'myanmar', 'sesame seed', 'ha', 1944, 'scan_no_figure', '-o)', 1),
    ('iia', 'estonia', 'milk, whole fresh cow', 'tonnes', 1944, 'scan_no_figure', '—', 1),
    ('iia', 'estonia', 'cheese, processed', 'tonnes', 1940, 'scan_no_figure', '—', 1),
    ('iia', 'latvia', 'cheese, processed', 'tonnes', 1940, 'scan_no_figure', '—', 1),
    ('iia', 'malta', 'eggs, hen, in shell', 'tonnes', 1939, 'scan_no_figure', '—', 1),
    ('iia', 'faroe islands', 'eggs, hen, in shell', 'tonnes', 1939, 'scan_no_figure', '—', 1),
    ('iia', 'kenya', 'beans, dry', 'tonnes', 1942, 'scan_no_figure', '—', 1),
    ('iia', 'kenya', 'beans, dry', 'tonnes', 1943, 'scan_no_figure', '—', 1),
    ('iia', 'latvia', 'sugar raw centrifugal', 'tonnes', 1940, 'scan_no_figure', '—', 1),
    ('iia', 'latvia', 'sugar raw centrifugal', 'tonnes', 1941, 'scan_no_figure', '—', 1),
    ('iia', 'latvia', 'sugar raw centrifugal', 'tonnes', 1942, 'scan_no_figure', '—', 1),
    ('iia', 'latvia', 'sugar raw centrifugal', 'tonnes', 1943, 'scan_no_figure', '—', 1),
    ('iia', 'latvia', 'sugar raw centrifugal', 'tonnes', 1944, 'scan_no_figure', '—', 1),
    ('iia', 'latvia', 'sugar raw centrifugal', 'tonnes', 1945, 'scan_no_figure', '—', 1),
    ('iia', 'lithuania', 'sugar raw centrifugal', 'tonnes', 1940, 'scan_no_figure', '—', 1),
    ('iia', 'lithuania', 'sugar raw centrifugal', 'tonnes', 1941, 'scan_no_figure', '—', 1),
    ('iia', 'lithuania', 'sugar raw centrifugal', 'tonnes', 1942, 'scan_no_figure', '—', 1),
    ('iia', 'lithuania', 'sugar raw centrifugal', 'tonnes', 1943, 'scan_no_figure', '—', 1),
    ('iia', 'lithuania', 'sugar raw centrifugal', 'tonnes', 1944, 'scan_no_figure', '—', 1),
    ('iia', 'lithuania', 'sugar raw centrifugal', 'tonnes', 1945, 'scan_no_figure', '—', 1),
    ('iia', 'jordan', 'grapes', 'ha', 1943, 'scan_no_figure', '—', 1),
    ('iia', 'greece', 'grapes', 'tonnes', 1941, 'scan_no_figure', '—', 1),
    ('iia', 'greece', 'grapes', 'tonnes', 1944, 'scan_no_figure', '—', 1),
    ('iia', 'greece', 'grapes', 'tonnes', 1945, 'scan_no_figure', '—', 1),
    ('iia', 'argentina', 'wine', 'tonnes', 1945, 'scan_no_figure', '...', 1),
    ('iia', 'morocco', 'cotton lint', 'tonnes', 1940, 'scan_no_figure', 'figure', 1),
    ('iia', 'egypt', 'flax fibre and tow', 'ha', 1913, 'scan_no_figure', 'figure', 1),
    ('iia', 'palau', 'p', 'tonnes', 1913, 'scan_no_figure', 'figure', 1),
    ('iia', 'new caledonia', 'cotton lint', 'tonnes', 1938, 'scan_no_figure', '...', 1),
})


def main() -> int:
    sys.path.insert(0, os.path.join(REPO, "pipelines/polity-autoimprove"))
    import matchlib

    problems = []
    try:
        rules = matchlib.load_value_null_corrections(TABLE)
    except (FileNotFoundError, ValueError) as exc:
        print(f"FAIL: {exc}")
        return 1

    # --- A: shape ---------------------------------------------------------------------------
    for i, r in enumerate(rules, start=2):
        n = (r.get("observed_rows") or "").strip()
        if not n.isdigit() or int(n) <= 0:
            problems.append(f"row {i}: observed_rows {n!r} is not a positive count")
        if r["pv"] != 0:
            problems.append(f"row {i}: printed_value {r['printed_value']!r} -- the table withholds "
                            "false ZEROS; a non-zero figure is a value, and its repair belongs elsewhere")

    # --- B: the adjudicated cells, in full ---------------------------------------------------
    got = {(r["source"], r["source_label"], r["item"], r["unit"], r["y"], r["evidence_rule"],
            r["glyph"], int(r["observed_rows"]) if str(r["observed_rows"]).isdigit() else -1)
           for r in rules}
    for k in sorted(got - BASELINE, key=str):
        problems.append(f"cell {k} differs from the adjudicated set -- a new or edited cell; add it to "
                        "BASELINE deliberately, with its evidence")
    for k in sorted(BASELINE - got, key=str):
        problems.append(f"adjudicated cell {k} is missing or was edited -- its false zero would be "
                        "published again")

    # --- C: the evidence still stands in tracked state ---------------------------------------
    with open(os.path.join(STATE, "zero_grid_floor.csv"), newline="", encoding="utf-8") as fh:
        floor = {"|".join((r["volume"], r["country"], r["product"], r["variable"], r["year"])): r
                 for r in csv.DictReader(fh)}
    with open(os.path.join(STATE, "edition_conflicts.csv"), newline="", encoding="utf-8") as fh:
        conflicts = {"|".join((r["volume_b"], r["label"], r["product"], r["variable"], r["year"])): r
                     for r in csv.DictReader(fh) if r["kind"] == "zero_contradicted"}
    for r in rules:
        ref = r["evidence_ref"]
        cell = r["key"]
        keys = re.findall(r"\[([^\]]+)\]", ref)
        if r["evidence_rule"] == "refuted_by_paired_axis":
            hit = [floor.get(k) for k in keys if "zero_grid_floor.csv" in ref]
            if not hit or any(h is None or h["verdict"] != "refuted_by_paired_axis" for h in hit):
                problems.append(f"{cell}: evidence_ref {ref!r} names no `refuted_by_paired_axis` row "
                                "of state/zero_grid_floor.csv")
            elif any(h["year"] != str(r["y"]) for h in hit):
                problems.append(f"{cell}: the zero_grid_floor row it cites is for another year")
        elif r["evidence_rule"] == "contradicted_by_other_volume":
            hit = [conflicts.get(k) for k in keys if "edition_conflicts.csv" in ref]
            if not hit or any(h is None or h["zero_grid_verdict"] != "grid_cannot_explain" for h in hit):
                problems.append(f"{cell}: evidence_ref {ref!r} names no zero_contradicted / "
                                "grid_cannot_explain row of state/edition_conflicts.csv")
        elif not re.search(r"\.pdf p\.\d+", ref):
            problems.append(f"{cell}: scan_no_figure needs `<file>.pdf p.<n>` in evidence_ref, got {ref!r}")
    print(f"  {len(rules)} cell(s), {sum(int(r['observed_rows']) for r in rules if str(r['observed_rows']).isdigit())}"
          f" layer-B row(s) withheld; by rule: "
          + ", ".join(f"{e} {sum(r['evidence_rule'] == e for r in rules)}"
                      for e in matchlib.VALUE_NULL_EVIDENCE_RULES))

    # --- D/E: against layer B and the matcher's output, where present ------------------------
    import extdata
    if not os.path.exists(extdata.LAYER_B) or not os.path.exists(MATCHED):
        print("SKIP arms D/E: layer B or matched_rows.parquet absent; scope and matcher agreement run "
              "on a maintainer's machine, not here")
    else:
        import pandas as pd
        lb = extdata.load_layer_b()
        lb = lb[~lb["is_aggregate"].fillna(False).astype(bool)]
        try:
            _, per_rule = matchlib.value_null_mask(lb, rules)
        except ValueError as exc:
            problems.append(str(exc))
            per_rule = {}
        for k, r in enumerate(rules):
            if k in per_rule and per_rule[k] != int(r["observed_rows"]):
                problems.append(f"{r['key']}: selects {per_rule[k]} layer-B row(s), the table records "
                                f"{r['observed_rows']}")
        m = pd.read_parquet(MATCHED)
        if "value_is_null" not in m.columns or "source_label_raw" not in m.columns:
            problems.append("matched_rows.parquet has no `value_is_null`; re-run 01_match_and_findings.py")
        else:
            want, _ = matchlib.value_null_mask(m, rules, label_col="source_label_raw")
            bad = int((want.values != m["value_is_null"].astype(bool).values).sum())
            if bad:
                problems.append(f"matched_rows.parquet: {bad} row(s) carry a value_is_null the table does "
                                "not imply -- stale; re-run 01_match_and_findings.py")
    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print("  " + p)
        return 1
    print("\nPASS: every withheld zero is an adjudicated cell, and its evidence still stands")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
