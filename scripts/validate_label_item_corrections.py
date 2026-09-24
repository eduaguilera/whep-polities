#!/usr/bin/env python3
"""Guard `data/final/source_label_item_corrections.csv` (issue 675).

WHAT THE TABLE IS. A source sometimes files ONE item of one territory under ANOTHER territory's
label. Mitchell prints Natal's pre-Union sugar cane under `south africa` -- the label every other
pre-1910 item routes to the Cape through -- and South Africa's national 1945-1957 horse count under
`natal`; fao1952 files two 1951 Netherlands New Guinea land-use rows under `New Guinea`. An alias
maps (label, source, years) to a polity and has no item dimension, so no alias can fix these: the
same label and years carry both territories. Each rule here re-labels the rows matching
(source, source_label, item, dated year in [year_start, year_end]) to `correct_label` BEFORE
matching (01_match_and_findings.py, via matchlib.apply_label_item_corrections), and the ordinary
machinery routes them. `polity_code` records where that lands, for a consumer that does not run
this repository's matcher.

WHAT THIS GATE CHECKS, and which arms run where.

  Everywhere (CI included -- none of it needs layer B):
    A  shape: the exact header, every key field filled, a bounded ordered year range, a
       positive `observed_rows`, a non-empty `issue` and `evidence`. Evidence is required
       because the whole point of a rule is a judgement the alias table could not record.
    B  no overlap: two rules on one (source, source_label, item) whose years intersect would
       be decided by file order, and a rule whose `correct_label` is another overlapping
       rule's `source_label` would mean different things to a consumer applying them in
       sequence than to the matcher, which never chains. Both are refused.
    C  targets live and agree: `polity_code` is a LIVE polity whose period covers every year
       of the rule, `correct_label` actually resolves to it in every one of those years, and
       `source_label` does NOT (a rule whose label already routes there is redundant and would
       hide whatever changed underneath it).
    D  ceiling: the number of rules and the rows they cover are pinned, bidirectionally. A
       deleted rule silently puts its rows back on the wrong territory, and nothing else in
       the repository would count that.

  Where layer B is present (a maintainer's machine; SKIPped by name in CI):
    E  scope: each rule selects exactly `observed_rows` non-aggregate rows, so a rebuild of
       layer B cannot quietly widen or narrow what was adjudicated; and the relabelled rows
       collide with no row the corrected label already carries in that source at the same
       (item, unit, year) -- a collision would be a double count, not a correction.
    F  routing: where state/matched_rows.parquet exists, every row it marks as relabelled
       (`country` differs from `source_label_raw` under a rule's key) sits on the rule's
       `polity_code`.

Usage:
  python3 scripts/validate_label_item_corrections.py
"""
from __future__ import annotations

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "data/final/source_label_item_corrections.csv")
POLDB = os.path.join(REPO, "data/final/polities_database.csv")
ALIASES = os.path.join(REPO, "pipelines/polity-autoimprove/state/applied_aliases.csv")
MATCHED = os.path.join(REPO, "pipelines/polity-autoimprove/state/matched_rows.parquet")

# Bidirectional. Raise deliberately, with the new rule's evidence in its row; a fall means a rule
# was deleted and its rows went back to the territory the source misfiled them under.
BASELINE_RULES = 6
BASELINE_ROWS = 100


def main() -> int:
    sys.path.insert(0, os.path.join(REPO, "pipelines/polity-autoimprove"))
    import matchlib

    problems = []
    try:
        rules = matchlib.load_label_item_corrections(TABLE)
    except (FileNotFoundError, ValueError) as exc:
        print(f"FAIL: {exc}")
        return 1

    # --- A: shape -------------------------------------------------------------------------
    for i, r in enumerate(rules, start=2):
        where = f"row {i} {(r['source'], r['source_label'], r['item'])}"
        n = (r.get("observed_rows") or "").strip()
        if not n.isdigit() or int(n) <= 0:
            problems.append(f"{where}: observed_rows {n!r} is not a positive count")
        for col in ("issue", "evidence"):
            if not (r.get(col) or "").strip():
                problems.append(f"{where}: empty `{col}` -- a rule is a judgement the alias "
                                "table could not record, so the reasoning must travel with it")

    # --- B: no overlap, no chains ---------------------------------------------------------
    def intersects(a, b):
        return a["y0"] <= b["y1"] and b["y0"] <= a["y1"]

    for i, a in enumerate(rules):
        for b in rules[i + 1:]:
            if a["source"] != b["source"] or a["item"] != b["item"] or not intersects(a, b):
                continue
            if a["source_label"] == b["source_label"]:
                problems.append(
                    f"overlapping rules on {(a['source'], a['source_label'], a['item'])}: "
                    f"{a['y0']}-{a['y1']} and {b['y0']}-{b['y1']} -- file order would decide")
            if a["correct_label"] == b["source_label"] or b["correct_label"] == a["source_label"]:
                problems.append(
                    f"chained rules on {(a['source'], a['item'])}: "
                    f"{a['source_label']!r}->{a['correct_label']!r} and "
                    f"{b['source_label']!r}->{b['correct_label']!r} overlap in years; the matcher "
                    "never chains, a consumer applying them in order would")

    # --- C: targets live, relabel lands on the recorded polity ----------------------------
    matcher = matchlib.Matcher(POLDB, ALIASES, verbose=False)
    span = {}
    with open(POLDB, newline="", encoding="utf-8") as fh:
        for p in csv.DictReader(fh):
            span[p["polity_code"]] = (int(p["start_year"]), int(p["end_year"]))
    for r in rules:
        key = (r["source"], r["source_label"], r["item"], r["y0"], r["y1"])
        code = r["polity_code"]
        if code not in span:
            problems.append(f"{key}: polity_code {code} is not in the database")
            continue
        if code in matcher.dead_codes:
            problems.append(f"{key}: polity_code {code} is retired/superseded and receives no data")
            continue
        s, e = span[code]
        for y in range(r["y0"], r["y1"] + 1):
            if not matchlib.covers(s, e, y):
                problems.append(f"{key}: {code} ({s}-{e}) does not cover {y}")
                break
            got = matcher.assign(r["correct_label"], None, r["source"], y)[0]
            if got != code:
                problems.append(
                    f"{key}: `{r['correct_label']}` resolves to {got} at {y}, not the recorded "
                    f"{code} -- the relabel and the published polity_code disagree")
                break
            if matcher.assign(r["source_label"], None, r["source"], y)[0] == code:
                problems.append(
                    f"{key}: `{r['source_label']}` already resolves to {code} at {y}, so the rule "
                    "is redundant and hides whatever now routes the label there")
                break

    # --- D: ceiling -----------------------------------------------------------------------
    total = sum(int(r["observed_rows"]) for r in rules if str(r["observed_rows"]).isdigit())
    print(f"item-scoped label corrections: {len(rules)} rule(s) over {total} row(s) "
          f"(pinned {BASELINE_RULES} / {BASELINE_ROWS})")
    if len(rules) != BASELINE_RULES:
        problems.append(
            f"{len(rules)} rules against the pinned {BASELINE_RULES} -- "
            + ("a rule was deleted and its rows went back to the misfiled territory"
               if len(rules) < BASELINE_RULES else
               "raise BASELINE_RULES deliberately, with the new rule's evidence in its row"))
    if total != BASELINE_ROWS:
        problems.append(f"the rules cover {total} rows against the pinned {BASELINE_ROWS}; "
                        "update BASELINE_ROWS in the same change that moves them")

    # --- E/F: against layer B and the matcher's output, where present ----------------------
    import extdata
    if not os.path.exists(extdata.LAYER_B):
        print(f"SKIP arms E/F: layer B absent ({extdata.LAYER_B}); scope and routing are "
              "checked on a maintainer's machine, not here")
    else:
        import pandas as pd
        lb = extdata.load_layer_b()
        lb = lb[~lb["is_aggregate"]]
        try:
            _, hit, per_rule = matchlib.apply_label_item_corrections(lb, rules)
        except ValueError as exc:
            # The matcher refuses overlapping rules too; arm B has already named them, so report
            # and stop here rather than letting the refusal hide the rest of the findings.
            problems.append(f"arms E/F not run: the matcher refuses the table ({exc})")
            hit = None
    if os.path.exists(extdata.LAYER_B) and hit is not None:
        for k, r in enumerate(rules):
            key = (r["source"], r["source_label"], r["item"], r["y0"], r["y1"])
            if per_rule[k] != int(r["observed_rows"]):
                problems.append(f"{key}: selects {per_rule[k]} layer-B row(s), the table records "
                                f"{r['observed_rows']} -- re-verify against the rebuilt panel")
        moved = lb[hit]
        for k, r in enumerate(rules):
            mine = moved[(moved["source"] == r["source"]) & (moved["country"] == r["source_label"])
                         & (moved["item"] == r["item"])]
            if mine.empty:
                continue
            there = lb[(lb["source"] == r["source"]) & (lb["country"] == r["correct_label"])
                       & (lb["item"] == r["item"]) & ~hit]
            clash = mine.merge(there, on=["unit", "year"], how="inner")
            if len(clash):
                problems.append(
                    f"{(r['source'], r['source_label'], r['item'])}: {len(clash)} relabelled row(s) "
                    f"land on a (unit, year) cell `{r['correct_label']}` already carries, e.g. "
                    f"{clash[['unit', 'year']].iloc[0].tolist()} -- a double count")
        if os.path.exists(MATCHED):
            m = pd.read_parquet(MATCHED)
            if "source_label_raw" not in m.columns:
                problems.append("matched_rows.parquet has no `source_label_raw`; re-run "
                                "01_match_and_findings.py")
            else:
                routed = 0
                for r in rules:
                    sel = m[(m["source"] == r["source"]) & (m["source_label_raw"] == r["source_label"])
                            & (m["item"] == r["item"]) & (m["country"] == r["correct_label"])]
                    sel = sel[[matchlib.alias_covers(r["y0"], r["y1"], y)
                               for y in pd.to_numeric(sel["year"], errors="coerce")]]
                    routed += len(sel)
                    wrong = sel[sel["whep_code"] != r["polity_code"]]
                    if len(wrong):
                        problems.append(
                            f"{(r['source'], r['source_label'], r['item'])}: {len(wrong)} relabelled "
                            f"row(s) in matched_rows.parquet sit on "
                            f"{sorted(wrong['whep_code'].fillna('(none)').unique())}, not {r['polity_code']}")
                print(f"  matched_rows.parquet: {routed} relabelled row(s) found")
                if routed != total:
                    problems.append(f"matched_rows.parquet carries {routed} relabelled rows, the "
                                    f"table {total} -- stale; re-run 01_match_and_findings.py")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print("  " + p)
        return 1
    print("\nPASS: every item-scoped relabel is unambiguous, lands on a live polity, and is needed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
