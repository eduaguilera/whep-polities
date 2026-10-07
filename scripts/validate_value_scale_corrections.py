#!/usr/bin/env python3
"""Guard `data/final/source_value_scale_corrections.csv` (issues 416, 424).

WHAT THE TABLE IS. A yearbook edition can print a whole column in a different unit from the editions
before it. The IIA's two late volumes (iia_1938_39, iia_1939_45) print tobacco and hops PRODUCTION in
a unit 100x smaller than the earlier ones, and iia_1938_39 alone prints hops AREA 10x smaller. Layer B
carries those cells as printed, so the panel's iia tobacco jumps 100x at 1934 and stays there. The
defect belongs to a volume's column, not to a cell, so it is recorded as one rule per (source, item,
unit, years) block with a power-of-ten `divisor`, not as 339 hand rows.

CELL RULES (issue 424). The same table carries single cells one volume printed ten times too small
while another volume prints the same cell right: iia_1933_34's 1933 japan soybean area is 32,367 ha
where iia_1938_39 prints 324,000. A cell rule names its layer-B label in `labels`, spans one year and
carries a divisor below 1 (0.1 multiplies by ten). Cells are convicted by
pipelines/polity-autoimprove/46_volume_scale_conflicts.py, which pairs every printing of a layer-B
cell across IIA volumes and judges a power-of-ten disagreement against the series' own neighbours;
its tracked output, state/volume_scale_conflicts.csv, is what arm G reads.

A RULE DOES NOT REWRITE `value`. matchlib.value_scale_divisors yields a per-row divisor that
01_match_and_findings.py writes to matched_rows.parquet as `value_divisor`, and the harmonized build
(pipelines/historical-production-harmonized/build.R) divides by it. Every diagnostic that convicts the
printed number (29_era_shift_verdicts.py, 41_era_volume_attribution.py, the edition tables) keeps
seeing it.

WHAT THIS GATE CHECKS, and which arms run where.

  Everywhere (CI included -- none of it needs layer B):
    A  shape: matchlib's loader (exact header, bounded years, a power-of-ten divisor other than 1,
       not both `labels` and `exempt_labels`), a positive `observed_rows`, a non-empty `issue`,
       `evidence` and `volume`.
    B  no overlap: two rules on one (source, item, unit) whose years AND label scopes intersect would
       be decided by file order.
    C  the ADJUDICATED rules, pinned bidirectionally and in full: (source, item, unit, years,
       divisor, exemptions, labels, volume, observed_rows). A count alone cannot see a widened year
       range -- hops area stretched from 1938 to 1945 keeps every count in CI and divides eight cells
       that are already right -- and a deleted rule silently puts its block back at 100x.
    G  cell rules against the volume comparison that convicted them (state/volume_scale_conflicts.csv),
       BOTH WAYS: every cell rule is a `carried_convicted` row of its label, item, unit and year, with
       the rule's `volume` the one layer B carries and its divisor the inverse of the factor between
       the volumes; every `carried_convicted` row has such a rule; no `carried_consistent` row --
       where the series supports the printed value, as for the 1933 hops areas iia_1938_39 prints in
       its 10x unit -- is touched by any rule. Verdict counts are pinned.

  Where layer B and matched_rows.parquet are present (a maintainer's machine; SKIPped by name in CI):
    D  scope: each rule selects exactly `observed_rows` layer-B rows, and a cell rule's row prints the
       value state/volume_scale_conflicts.csv says layer B carries.
    E  the matcher's output agrees: matched_rows.parquet carries `value_divisor`, equal row for row to
       the divisor the table implies on the label layer B prints.
    F  SIBLING SOURCES, per series -- the evidence the rules rest on, re-measured. For every divided
       row with a same-polity, same-year juan/mitchell value of the same item and unit: before the
       division it disagrees by more than 2x, after it agrees within 2x, except the pinned residual
       cells. And the CONTROL that fixes each rule's edges: rows of the same key that a rule leaves
       alone (the exempt label, hops area after 1938) must already agree with their sibling. fao1952's
       1934-1938 average is compared with the mean of the divided 1934-1938 dated rows the same way.
       Block rules only: a cell rule's evidence is the volume comparison, re-checked by arm G.

Usage:
  python3 scripts/validate_value_scale_corrections.py
"""
from __future__ import annotations

import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "data/final/source_value_scale_corrections.csv")
MATCHED = os.path.join(REPO, "pipelines/polity-autoimprove/state/matched_rows.parquet")
CONFLICTS = os.path.join(REPO, "pipelines/polity-autoimprove/state/volume_scale_conflicts.csv")

# Arm C. Every adjudicated rule, in full; raise deliberately, with the new rule's evidence in its row.
# 2026-10-07 (issue 416): the three iia rules -- tobacco and hops production 1934-1945 /100 (ivory
# coast exempt: its own overlap factor is 9.88x and its printed yields are plausible), hops area
# 1934-1938 /10 (iia_1939_45 prints it in plain hectares).
# 2026-10-07 (issue 424): eight 1933 cells iia_1933_34 printed ten times too small, each convicted by
# state/volume_scale_conflicts.csv. Tuple: (source, item, unit, y0, y1, divisor, exempt, labels,
# volume, observed_rows).
_T, _H = "iia_1938_39;iia_1939_45", "iia_1938_39"
_C = "iia_1933_34"
BASELINE = frozenset({
    ("iia", "tobacco, unmanufactured", "tonnes", 1934, 1945, 100, ("ivory coast",), (), _T, 292),
    ("iia", "hops", "tonnes", 1934, 1945, 100, (), (), _T, 27),
    ("iia", "hops", "ha", 1934, 1938, 10, (), (), _H, 20),
    ("iia", "sugar raw centrifugal", "tonnes", 1933, 1933, 0.1, (), ("antigua and barbuda",), _C, 1),
    ("iia", "sugar raw centrifugal", "tonnes", 1933, 1933, 0.1, (), ("australia",), _C, 1),
    ("iia", "sesame seed", "ha", 1933, 1933, 0.1, (), ("indonesia",), _C, 1),
    ("iia", "soybeans", "ha", 1933, 1933, 0.1, (), ("japan",), _C, 1),
    ("iia", "cotton seed", "ha", 1933, 1933, 0.1, (), ("peru",), _C, 1),
    ("iia", "cotton lint", "ha", 1933, 1933, 0.1, (), ("syrian arab republic",), _C, 1),
    ("iia", "cotton seed", "ha", 1933, 1933, 0.1, (), ("syrian arab republic",), _C, 1),
    ("iia", "tea", "ha", 1933, 1933, 0.1, (), ("viet nam",), _C, 1),
})
# Arm G. Verdict counts in state/volume_scale_conflicts.csv, measured 2026-10-07 by
# 46_volume_scale_conflicts.py. `carried_consistent` is 21 because the 1933 tobacco/hops x100 pairs
# (18) and the three hops-area x10 pairs read RIGHT once issue 416's rules divide their 1934
# neighbours; `undecided` (7) are benin cacao and eggs, ivory coast, cyprus, israel and namibia
# tobacco, and jamaica cacao area -- a neighbour missing or on neither side.
VERDICT_PINS = {"carried_convicted": 8, "carried_consistent": 21, "undecided": 7,
                "not_in_layer_b": 99}

# Arm F. Same-polity same-year sibling comparisons (juan + mitchell), per rule key, pinned as
# (compared, agree within 2x after division). Measured 2026-10-07 on matched_rows.parquet.
SIBLING_PINS = {
    ("iia", "tobacco, unmanufactured", "tonnes"): (25, 25),
    ("iia", "hops", "tonnes"): (17, 16),
    ("iia", "hops", "ha"): (10, 10),
}
# Divided cells that agree with no sibling either way, each for a recorded second reason.
RESIDUAL = frozenset({
    # prints 46,100 where juan's 3,461 implies 346,100: a dropped leading digit on top of the unit
    ("iia", "czech republic", "hops", "tonnes", 1944),
})
# The control: same key, left alone by the rule, compared with a sibling -- all must agree as printed.
CONTROL_PINS = {
    ("iia", "tobacco, unmanufactured", "tonnes"): 0,     # ivory coast has no sibling
    ("iia", "hops", "tonnes"): 0,
    ("iia", "hops", "ha"): 8,                            # czech republic 1939-1945, serbia 1939
}
# fao1952 1934-1938 average vs the mean of the divided dated 1934-1938 rows: (polities, within 2x).
# Joined on polity: fao1952's `Czechoslovakia` average closes on F51-1947-1993, so czech republic's
# 1934-1938 iia rows (F51-1918-1938) have no partner here and are compared through juan in arm F.
FAO_PINS = {
    ("iia", "tobacco, unmanufactured", "tonnes"): (20, 20),
    ("iia", "hops", "tonnes"): (2, 2),
    ("iia", "hops", "ha"): (3, 3),
}
FAO_ITEM = {"tobacco, unmanufactured": "tobacco", "hops": "hops"}
FAO_UNIT = {"tonnes": "1000 tonnes", "ha": "1000 hectares"}
BAND = 2.0


def within(a: float, b: float) -> bool:
    return b > 0 and a > 0 and 1 / BAND <= a / b <= BAND


def main() -> int:
    sys.path.insert(0, os.path.join(REPO, "pipelines/polity-autoimprove"))
    import matchlib

    problems = []
    try:
        rules = matchlib.load_value_scale_corrections(TABLE)
    except (FileNotFoundError, ValueError) as exc:
        print(f"FAIL: {exc}")
        return 1

    # --- A: shape ---------------------------------------------------------------------------
    for i, r in enumerate(rules, start=2):
        n = (r.get("observed_rows") or "").strip()
        if not n.isdigit() or int(n) <= 0:
            problems.append(f"row {i}: observed_rows {n!r} is not a positive count")

    for i, r in enumerate(rules, start=2):
        if r["labels"] and r["y0"] != r["y1"]:
            problems.append(f"row {i}: a cell rule (`labels` set) must span one year, got "
                            f"{r['y0']}-{r['y1']}")

    # --- B: no overlap ----------------------------------------------------------------------
    def scopes_meet(x, y):
        if x["labels"] and y["labels"]:
            return bool(set(x["labels"]) & set(y["labels"]))
        if x["labels"]:
            return not set(x["labels"]) <= set(y["exempt"])
        if y["labels"]:
            return not set(y["labels"]) <= set(x["exempt"])
        return True

    for a in range(len(rules)):
        for b in range(a + 1, len(rules)):
            x, y = rules[a], rules[b]
            if ((x["source"], x["item"], x["unit"]) == (y["source"], y["item"], y["unit"])
                    and x["y0"] <= y["y1"] and y["y0"] <= x["y1"] and scopes_meet(x, y)):
                problems.append(f"rules {a + 2} and {b + 2} on {(x['source'], x['item'], x['unit'])} "
                                "overlap in years and labels -- file order would decide the factor")

    # --- C: the adjudicated rules, in full ---------------------------------------------------
    got = {(r["source"], r["item"], r["unit"], r["y0"], r["y1"], r["div"], tuple(sorted(r["exempt"])),
            tuple(sorted(r["labels"])), r["volume"].strip(), int(r["observed_rows"])) for r in rules}
    for k in sorted(got - BASELINE, key=str):
        problems.append(f"rule {k} differs from the adjudicated set -- a new or edited rule; add it to "
                        "BASELINE deliberately, with its sibling evidence")
    for k in sorted(BASELINE - got, key=str):
        problems.append(f"adjudicated rule {k} is missing or was edited -- its block would be published "
                        "at the wrong power of ten")
    print(f"  {len(rules)} rule(s), {sum(int(r['observed_rows']) for r in rules)} row(s) adjudicated")

    # --- G: cell rules against the volume comparison, both ways ------------------------------
    conflicts = conflict_arm(rules, problems)

    # --- D/E/F: against layer B and the matcher's output, where present ---------------------
    import extdata
    if not os.path.exists(extdata.LAYER_B) or not os.path.exists(MATCHED):
        print(f"SKIP arms D/E/F: layer B or matched_rows.parquet absent; scope, matcher agreement and "
              "the sibling re-measurement run on a maintainer's machine, not here")
    else:
        import pandas as pd
        lb = extdata.load_layer_b()
        lb = lb[~lb["is_aggregate"]]
        _, per_rule = matchlib.value_scale_divisors(lb, rules)
        for k, r in enumerate(rules):
            if per_rule[k] != int(r["observed_rows"]):
                problems.append(f"{(r['source'], r['item'], r['unit'], r['y0'], r['y1'])}: selects "
                                f"{per_rule[k]} layer-B row(s), the table records {r['observed_rows']}")
            if r["labels"]:
                sel = lb[(lb["source"] == r["source"]) & (lb["item"] == r["item"])
                         & (lb["unit"] == r["unit"]) & lb["country"].isin(r["labels"])
                         & (pd.to_numeric(lb["year"], errors="coerce") == r["y0"])]
                want = {round(float(c["carried_value"]), 6) for c in conflicts
                        if c["verdict"] == "carried_convicted" and c["layer_b_label"] in r["labels"]
                        and c["item"] == r["item"] and c["unit"] == r["unit"]
                        and int(c["year"]) == r["y0"]}
                have = {round(float(v), 6) for v in sel["value"]}
                if have != want:
                    problems.append(f"{(r['source'], r['labels'], r['item'], r['unit'], r['y0'])}: layer B "
                                    f"prints {sorted(have)}, the volume comparison convicted {sorted(want)}")
        m = pd.read_parquet(MATCHED)
        if "value_divisor" not in m.columns or "source_label_raw" not in m.columns:
            problems.append("matched_rows.parquet has no `value_divisor`; re-run 01_match_and_findings.py")
        else:
            want, _ = matchlib.value_scale_divisors(m, rules, label_col="source_label_raw")
            bad = int((want.values != m["value_divisor"].values).sum())
            if bad:
                problems.append(f"matched_rows.parquet: {bad} row(s) carry a value_divisor the table does "
                                "not imply -- stale; re-run 01_match_and_findings.py")
            problems += sibling_arm(m, rules, pd)
    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print("  " + p)
        return 1
    print("\nPASS: every value-scale rule is the adjudicated one, and its siblings still agree")
    return 0


def sibling_arm(m, rules, pd):
    problems = []
    m = m.copy()
    m["yr_"] = pd.to_numeric(m["year"], errors="coerce")
    sib = m[m["source"].isin(["juan", "mitchell"]) & m["yr_"].notna() & m["whep_code"].notna()]
    for r in rules:
        if r["labels"]:
            continue     # a cell rule's evidence is the volume comparison (arm G), not a sibling
        key = (r["source"], r["item"], r["unit"])
        block = m[(m["source"] == r["source"]) & (m["item"] == r["item"]) & (m["unit"] == r["unit"])
                  & m["yr_"].notna() & m["whep_code"].notna()]
        s = (sib[(sib["item"] == r["item"]) & (sib["unit"] == r["unit"])]
             .groupby(["whep_code", "yr_"])["value"].median().rename("sib").reset_index())
        j = block.merge(s, on=["whep_code", "yr_"], how="inner")
        j = j[j["sib"] > 0]
        div = j[j["value_divisor"] != 1]
        n, ok = 0, 0
        for row in div.itertuples():
            cell = (r["source"], row.source_label_raw, r["item"], r["unit"], int(row.yr_))
            n += 1
            after = within(row.value / row.value_divisor, row.sib)
            ok += after
            if within(row.value, row.sib):
                problems.append(f"{cell}: printed {row.value:,.0f} already agrees with the sibling "
                                f"{row.sib:,.0f}, so the rule DAMAGES it")
            elif not after and cell not in RESIDUAL:
                problems.append(f"{cell}: {row.value / row.value_divisor:,.1f} after division still "
                                f"disagrees with the sibling {row.sib:,.0f} and is not a recorded residual")
        if (n, ok) != SIBLING_PINS[key]:
            problems.append(f"{key}: {n} sibling comparisons, {ok} agree after division; pinned "
                            f"{SIBLING_PINS[key]}")
        # The control: rows of this key in the rule's own sources and era that the rule leaves alone.
        ctl = j[(j["value_divisor"] == 1) & (j["yr_"] >= r["y0"]) & (j["yr_"] <= 1945)]
        for row in ctl.itertuples():
            if not within(row.value, row.sib):
                problems.append(f"{(r['source'], row.source_label_raw, r['item'], r['unit'], int(row.yr_))}: "
                                f"left undivided at {row.value:,.0f} but the sibling reads {row.sib:,.0f} "
                                "-- the rule's edge or exemption is wrong")
        if len(ctl) != CONTROL_PINS[key]:
            problems.append(f"{key}: {len(ctl)} undivided control row(s) with a sibling; pinned "
                            f"{CONTROL_PINS[key]}")
        # fao1952's 1934-1938 average against the mean of the divided dated 1934-1938 rows.
        f = m[(m["source"] == "fao1952") & (m["item"] == FAO_ITEM[r["item"]])
              & (m["unit"] == FAO_UNIT[r["unit"]]) & (m["period"].astype(str) == "1934-1938")
              & m["whep_code"].notna()]
        f = (f.groupby("whep_code")["value"].median() * 1000).rename("fao")
        e = block[(block["yr_"] >= 1934) & (block["yr_"] <= 1938) & (block["value_divisor"] != 1)]
        e = e.assign(c=e["value"] / e["value_divisor"]).groupby("whep_code").agg(
            raw=("value", "mean"), c=("c", "mean"))
        g = e.join(f, how="inner")
        g = g[g["fao"] > 0]
        agree = sum(within(c, fv) for c, fv in zip(g["c"], g["fao"]))
        raw_agree = sum(within(v, fv) for v, fv in zip(g["raw"], g["fao"]))
        if (len(g), agree) != FAO_PINS[key] or raw_agree:
            problems.append(f"{key}: fao1952 1934-1938 -- {len(g)} polities, {agree} within 2x after "
                            f"division, {raw_agree} as printed; pinned {FAO_PINS[key]} and 0")
        print(f"  {key}: siblings {n} compared / {ok} agree after; control {len(ctl)}; "
              f"fao1952 {len(g)} / {agree}")
    return problems


def conflict_arm(rules, problems):
    """Arm G: cell rules and state/volume_scale_conflicts.csv must agree in both directions."""
    import csv
    if not os.path.exists(CONFLICTS):
        problems.append(f"{os.path.relpath(CONFLICTS, REPO)} missing -- run "
                        "46_volume_scale_conflicts.py --write")
        return []
    with open(CONFLICTS, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    counts = {}
    for c in rows:
        counts[c["verdict"]] = counts.get(c["verdict"], 0) + 1
    if counts != VERDICT_PINS:
        problems.append(f"volume_scale_conflicts.csv verdicts {dict(sorted(counts.items()))}, pinned "
                        f"{dict(sorted(VERDICT_PINS.items()))}")

    def cell(c):
        return (c["layer_b_label"], c["item"], c["unit"], int(c["year"]))

    convicted = {}
    for c in rows:
        if c["verdict"] == "carried_convicted":
            convicted.setdefault(cell(c), []).append(c)
    consistent = {cell(c) for c in rows if c["verdict"] == "carried_consistent"}
    ruled = {}
    for r in rules:
        if r["source"] != "iia":
            continue
        for lab in r["labels"]:
            ruled[(lab, r["item"], r["unit"], r["y0"])] = r
        if r["labels"]:
            k = (r["labels"][0], r["item"], r["unit"], r["y0"])
            hits = [c for lab in r["labels"]
                    for c in convicted.get((lab, r["item"], r["unit"], r["y0"]), [])]
            if not hits:
                problems.append(f"cell rule {k} has no carried_convicted row in "
                                "volume_scale_conflicts.csv -- nothing convicts the printed value")
            for c in hits:
                if c["carried_volume"] not in r["volume"].split(";"):
                    problems.append(f"cell rule {k}: volume {r['volume']!r}, but layer B carries "
                                    f"{c['carried_volume']}'s printing")
                if abs(float(r["div"]) * float(c["factor"]) - 1) > 1e-9:
                    problems.append(f"cell rule {k}: divisor {r['div']} does not undo the factor "
                                    f"{c['factor']} between the volumes")
    for k in sorted(convicted):
        if k not in ruled:
            problems.append(f"{k}: convicted by the volume comparison (carried "
                            f"{convicted[k][0]['carried_value']}, other volume "
                            f"{convicted[k][0]['other_value']}) but no cell rule corrects it")
    for r in rules:
        for k in sorted(consistent):
            if (r["source"] == "iia" and (r["item"], r["unit"]) == k[1:3] and r["y0"] <= k[3] <= r["y1"]
                    and (k[0] in r["labels"] if r["labels"] else k[0] not in r["exempt"])):
                problems.append(f"{k}: the series supports the printed value (carried_consistent), "
                                f"yet a rule scales it by 1/{r['div']}")
    print(f"  volume comparison: {counts.get('carried_convicted', 0)} convicted, "
          f"{counts.get('carried_consistent', 0)} consistent, {len(ruled)} cell rule label(s)")
    return rows


if __name__ == "__main__":
    raise SystemExit(main())
