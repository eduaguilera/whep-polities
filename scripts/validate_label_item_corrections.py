#!/usr/bin/env python3
"""Guard `data/final/source_label_item_corrections.csv` (issue 675).

WHAT THE TABLE IS. A source sometimes files ONE item of one territory under ANOTHER territory's
label. Mitchell prints Natal's pre-Union sugar cane under `south africa` -- the label every other
pre-1910 item routes to the Cape through -- and South Africa's national 1945-1957 horse count under
`natal`; fao1952 files two 1951 Netherlands New Guinea land-use rows under `New Guinea`. An alias
maps (label, source, years) to a polity and has no item dimension, so no alias can fix these: the
same label and years carry both territories. Each rule here re-labels the rows matching
(source, source_label, item, dated year in [year_start, year_end], or a period average lying wholly
inside it) to `correct_label` BEFORE
matching (01_match_and_findings.py, via matchlib.apply_label_item_corrections), and the ordinary
machinery routes them. `polity_code` records where that lands, for a consumer that does not run
this repository's matcher.

UNIT / INDICATOR SCOPE (2026-09-25, issue 688). Two optional columns, `unit` and `indicator`,
narrow a rule to rows whose layer-B `unit` / `indicator` equal the value exactly; BLANK MEANS ANY,
so a rule without them selects what it always did. They exist because some sources file one
item's rows under two territories that only the TABLE separates: Mitchell's `viet nam` 1955-1960
rice and maize output (tonnes) is North plus South, the same label's area (ha) South only.

WHAT THIS GATE CHECKS, and which arms run where.

  Everywhere (CI included -- none of it needs layer B):
    A  shape: the exact header, every key field filled, a bounded ordered year range, a
       positive `observed_rows`, a non-empty `issue` and `evidence`. Evidence is required
       because the whole point of a rule is a judgement the alias table could not record.
    B  no overlap: two rules on one (source, source_label, item) whose years intersect would
       be decided by file order, and a rule whose `correct_label` is another overlapping
       rule's `source_label` would mean different things to a consumer applying them in
       sequence than to the matcher, which never chains. Both are refused. Two rules whose
       unit/indicator scopes are DISJOINT (a column set on both, to different values) select
       no common row and do not overlap; a scoped and an unscoped rule on one key still do.
       A scope value must be a known layer-B unit (SCOPE_UNITS below), so a typo that would
       select nothing fails here, in CI, and not only where layer B is present.
    C' unrouting: a rule whose `polity_code` is the sentinel `UNROUTED`
       (matchlib.LABEL_ITEM_UNROUTED, added 2026-09-24) takes its rows OFF the panel -- for a
       row that is the wrong territory with no right one to land on (iia `jamaica` cotton
       1934-1945, the doubled British West Indies total). Its `correct_label` must resolve to
       NO polity in every year of the rule, and its `source_label` must still resolve to one
       (else the rule is redundant); arm F then requires every such row to be unrouted.
    C  targets live and agree: `polity_code` is a LIVE polity whose period covers every year
       of the rule (or, for a year before it begins, is reached through a `back_cast` alias), `correct_label` actually resolves to it in every one of those years, and
       `source_label` does NOT (a rule whose label already routes there is redundant and would
       hide whatever changed underneath it).
    D  ceiling: the number of rules and the rows they cover are pinned, bidirectionally. A
       deleted rule silently puts its rows back on the wrong territory, and nothing else in
       the repository would count that. So is the number of SCOPED rules: blanking a scope
       leaves every count above unchanged in CI while widening the rule onto the rows the scope
       exists to leave alone (Vietnam's South-only area onto the North+South aggregate).

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
# 6/100 -> 8/106 on 2026-09-24: fao1952 `USSR` rye (2 period rows) and 1937 population (4 rows) are
# on post-war boundaries while the label's other pre-war items are not (source_conventions.csv).
# 8/106 -> 15/155 on 2026-09-24 (issue 687, the iia raw-extract fingerprint audit): iia `france` eggs
# that are Saint-Pierre-et-Miquelon's (2 rules, 9 rows), `greece` grapes that are the Dodecanese's
# (2 rules, 4 rows), `egypt` dry beans that are the Sudan's (1 rule, 4 rows), and the first two
# UNROUTED rules -- `jamaica` cotton lint and seed 1934-1945, the doubled British West Indies total
# (16 rows each).
# 15/155 -> 23/205 on 2026-09-24 (issue 688, Mitchell footnotes): mitchell `ghana` livestock 1939-1952 (21 rows)
# and crop area/output 1919-1955 (22) are Gold Coast plus British Togoland by Mitchell's own notes, and mitchell
# `syrian arab republic` tobacco 1945-1951 (7) includes Lebanon; the label's other tables do not.
# 23/205 -> 49/785 on 2026-09-24 (issues 687 and 688, the polities those two issues asked for): iia `viet nam`
# items that are raw `french tonkin` (10 rules, 258 rows -> VNM-TON-1887-1945), iia `cameroon` items that are raw
# `british-french cameroon` (6 rules, 124 -> BFCM-1920-1960), Mitchell `nigeria` cacao 1945-1959 and livestock to
# 1950, footnoted as including British Cameroons (7 rules, 148 -> NGBC-1916-1960), and Mitchell `syrian arab
# republic` olive oil, sheep and goats footnoted as including Lebanon (3 rules, 50 -> SYL-1920-1944).
# 49/785 -> 55/838 on 2026-09-25 (cross-source routing audit): iia `india` sesame, groundnuts, eggs, cotton
# lint 1934-1945 and cotton seed 1937-1945 are French India's (5 rules, 51 rows, issue 372), and fao1952
# `USSR` oats 1934-1938 closes on post-war boundaries as rye does (1 rule, 2 rows, issue 681).
# 55/838 -> 59/892 on 2026-09-25 (issue 688, the unit scope): mitchell `viet nam` rice and maize OUTPUT
# 1955-1960 (tonnes, 12 rows -> F237-1954-1975; C2 prints North and South apart, layer B holds the sum) and
# mitchell `syrian arab republic` wheat and barley OUTPUT 1920-1940 (tonnes, 42 rows -> SYL-1920-1944; C2
# note 17 'Including Lebanon to 1940'). All four are scoped `unit=tonnes`: the same keys' area rows stay.
# 59/892 -> 60/900 on 2026-09-25 (unrouted-rows audit, Claude): fao1952 `French Morocco & Br Gold Coast` dry
# peas 1934-1951 (8 rows) are French Morocco's; the label carries nothing else and the Gold Coast grows no dry
# peas. Unscoped (unit and indicator blank), so BASELINE_SCOPED_RULES is unchanged.
BASELINE_RULES = 60
BASELINE_ROWS = 900
BASELINE_SCOPED_RULES = 4

# Units a scope may name, per source: layer B's own `unit` vocabulary, measured 2026-09-25 over
# consolidated_layer_b.parquet (every non-null value of the column, by source). A scope outside it
# selects nothing, and a rule that selects nothing leaves its rows on the wrong territory, so it is
# refused here where CI can see it. Arm E re-measures the vocabulary where layer B is present, so a
# rebuild that adds or renames a unit fails there rather than leaving this list quietly stale.
SCOPE_UNITS = {
    "fao1952": {"1000 tonnes", "1000 hectares", "1000 heads", "kilograms", "number", "tonnes",
                "hectoliters", "1000000 hectares", "1000 people"},
    "iia": {"ha", "tonnes"},
    "juan": {"tonnes", "ha", "heads"},
    "mitchell": {"ha", "heads", "tonnes", "tons"},
    "sa_colonial": {"Bushels", "Tons", "Gallons"},
}


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
        unit = r.get("unit") or ""
        if unit and unit not in SCOPE_UNITS.get(r["source"], set()):
            problems.append(f"{where}: unit scope {unit!r} is not a layer-B unit of "
                            f"{r['source']} ({sorted(SCOPE_UNITS.get(r['source'], set()))}) -- the "
                            "rule would select no row")

    # --- B: no overlap, no chains ---------------------------------------------------------
    def intersects(a, b):
        return a["y0"] <= b["y1"] and b["y0"] <= a["y1"]

    for i, a in enumerate(rules):
        for b in rules[i + 1:]:
            if a["source"] != b["source"] or a["item"] != b["item"] or not intersects(a, b):
                continue
            if matchlib.label_item_scopes_disjoint(a, b):
                continue   # e.g. tonnes vs ha: no row can satisfy both, so neither can decide it
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
        if code == matchlib.LABEL_ITEM_UNROUTED:
            for y in range(r["y0"], r["y1"] + 1):
                got = matcher.assign(r["correct_label"], None, r["source"], y)[0]
                if got is not None:
                    problems.append(
                        f"{key}: an UNROUTED rule's `{r['correct_label']}` resolves to {got} at "
                        f"{y} -- the rows would land there instead of leaving the panel")
                    break
                if matcher.assign(r["source_label"], None, r["source"], y)[0] is None:
                    problems.append(
                        f"{key}: `{r['source_label']}` already resolves to nothing at {y}, so "
                        "the UNROUTED rule is redundant")
                    break
            continue
        if code not in span:
            problems.append(f"{key}: polity_code {code} is not in the database")
            continue
        if code in matcher.dead_codes:
            problems.append(f"{key}: polity_code {code} is retired/superseded and receives no data")
            continue
        s, e = span[code]
        for y in range(r["y0"], r["y1"] + 1):
            got, _, how = matcher.assign(r["correct_label"], None, r["source"], y)
            # A year before the target begins is allowed ONLY when the corrected label reaches the
            # target through a `back_cast` alias -- the source reconstructs those years onto a
            # boundary drawn later (fao1952's USSR rye and 1937 population, 2026-09-24). Any other
            # uncovered year is still refused.
            if not matchlib.covers(s, e, y) and not (
                    got == code and how == "applied_alias_back_cast" and y < s):
                problems.append(f"{key}: {code} ({s}-{e}) does not cover {y}")
                break
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
    scoped = sum(1 for r in rules if matchlib.label_item_rule_scope(r))
    print(f"  of which scoped on unit/indicator: {scoped} (pinned {BASELINE_SCOPED_RULES})")
    if scoped != BASELINE_SCOPED_RULES:
        problems.append(
            f"{scoped} unit/indicator-scoped rules against the pinned {BASELINE_SCOPED_RULES} -- "
            + ("a scope was blanked, so its rule now also relabels the rows the scope left alone "
               "(the rule and row counts cannot see this in CI)" if scoped < BASELINE_SCOPED_RULES
               else "raise BASELINE_SCOPED_RULES deliberately, with the scope's reason in `evidence`"))

    # --- E/F: against layer B and the matcher's output, where present ----------------------
    import extdata
    if not os.path.exists(extdata.LAYER_B):
        print(f"SKIP arms E/F: layer B absent ({extdata.LAYER_B}); scope and routing are "
              "checked on a maintainer's machine, not here")
    else:
        import pandas as pd
        lb = extdata.load_layer_b()
        # Vocabulary over EVERY row, aggregates included (fao1952's `1000000 hectares` is on
        # aggregate rows only), since that is the whole set a scope could ever be compared with.
        for src in sorted({r["source"] for r in rules}):
            got = set(lb.loc[lb["source"] == src, "unit"].dropna())
            if got != SCOPE_UNITS.get(src, set()):
                problems.append(
                    f"layer B's `unit` vocabulary for {src} is {sorted(got)}, SCOPE_UNITS pins "
                    f"{sorted(SCOPE_UNITS.get(src, set()))} -- re-measure it")
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
            # `period` is part of the cell: a 1934-1938 average and a dated row are different cells
            # (pandas matches NaN to NaN on a merge key, so two dated rows still pair on year alone).
            clash = mine.merge(there, on=["unit", "year", "period"], how="inner")
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
                    for col, val in matchlib.label_item_rule_scope(r).items():
                        sel = sel[sel[col] == val]
                    # A boolean SERIES, not a list: an empty list would select no COLUMNS.
                    sel = sel[pd.Series([matchlib.label_item_rule_covers(r, y, pp) for y, pp in
                                         zip(pd.to_numeric(sel["year"], errors="coerce"),
                                             sel["period"])], index=sel.index, dtype=bool)]
                    routed += len(sel)
                    if r["polity_code"] == matchlib.LABEL_ITEM_UNROUTED:
                        wrong = sel[sel["whep_code"].notna()]
                    else:
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
