#!/usr/bin/env python3
"""Guard `data/final/source_item_withholds.csv` (issue 375).

WHAT THE TABLE IS. A layer-B item can be a different commodity from the one it is named for, with no
single re-labelling that recovers the right one. iia `wheat` is spelt and meslin, cell by cell: the raw
IIA extract has ZERO wheat production or area rows (wheat there is trade only), so the correct iia wheat
series is EMPTY, not small. iia `other sugar crops n.e.c.` is citrus: the extract's only sugar crops are
beet and cane. Layer B files both under an FAO item code (15 wheat, 161 other sugar crops), so the
harmonized build published them as that commodity -- and on the consumer's (polity, item, unit, year)
key iia `wheat` was AVERAGED with juan/mitchell's real wheat on 68 keys, halving it.

A WITHHOLD DOES NOT DELETE ANYTHING. matchlib.item_withheld flags the rows; 01_match_and_findings.py
writes the flag to matched_rows.parquet as `item_withheld`; the harmonized build
(pipelines/historical-production-harmonized/build.R) drops flagged rows. Layer B and every diagnostic
keep seeing them.

WHAT THIS GATE CHECKS, and which arms run where.

  Everywhere (CI included -- none of it needs layer B):
    A  shape: matchlib's loader (exact header, no blank cell, positive `observed_rows`, no duplicate
       (source, item, unit)).
    B  the ADJUDICATED rules, pinned bidirectionally and in full. A deleted rule silently republishes
       its item as the commodity it is not, and nothing else in CI would notice.
    C  the rules and the item registry agree, both ways. state/item_equivalences.csv records, per
       (iia item, raw product) pair, whether the mapping is a rename, an aggregation, a `defect` or
       `unresolved`. An item ALL of whose products are `defect` has no correct series in the source, so
       it must be withheld; and a withheld item must be one of those -- withholding an item that has
       an approved product would throw away real data, and one with an `unresolved` product would
       decide that question here instead of in the registry.

  Where layer B and matched_rows.parquet are present (a maintainer's machine; SKIPped by name in CI):
    D  scope: each rule selects exactly `observed_rows` layer-B rows, and every unit layer B carries
       for a withheld (source, item) has its own rule -- a third unit would leak the item through.
    E  the matcher's output agrees: matched_rows.parquet carries `item_withheld`, equal row for row to
       the flag the table implies.

Usage:
  python3 scripts/validate_item_withholds.py
"""
from __future__ import annotations

import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "data/final/source_item_withholds.csv")
REGISTRY = os.path.join(REPO, "pipelines/polity-autoimprove/state/item_equivalences.csv")
MATCHED = os.path.join(REPO, "pipelines/polity-autoimprove/state/matched_rows.parquet")

# Arm B. Every adjudicated rule, in full; raise deliberately, with the new rule's evidence in its row.
# 2026-10-07 (issue 375): iia `wheat` (spelt and meslin) and iia `other sugar crops n.e.c.` (citrus),
# each in both units layer B carries for it.
BASELINE = frozenset({
    ("iia", "wheat", "ha", 129),
    ("iia", "wheat", "tonnes", 124),
    ("iia", "other sugar crops n.e.c.", "ha", 33),
    ("iia", "other sugar crops n.e.c.", "tonnes", 45),
})
# The registry covers iia alone (22_item_equivalences.py reads the raw IIA extract).
REGISTRY_SOURCE = "iia"


def norm(s) -> str:
    """The registry's own item normalisation (22_item_equivalences.py): punctuation to spaces."""
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def main() -> int:
    sys.path.insert(0, os.path.join(REPO, "pipelines/polity-autoimprove"))
    import matchlib

    problems = []
    try:
        rules = matchlib.load_item_withholds(TABLE)
    except (FileNotFoundError, ValueError) as exc:
        print(f"FAIL: {exc}")
        return 1

    # --- B: the adjudicated rules, in full ---------------------------------------------------
    got = {(r["source"], r["item"], r["unit"], int(r["observed_rows"])) for r in rules}
    for k in sorted(got - BASELINE, key=str):
        problems.append(f"rule {k} differs from the adjudicated set -- a new or edited withhold; add "
                        "it to BASELINE deliberately, with its evidence")
    for k in sorted(BASELINE - got, key=str):
        problems.append(f"adjudicated rule {k} is missing or was edited -- its rows would be published "
                        "as a commodity they are not")
    print(f"  {len(rules)} rule(s), {sum(int(r['observed_rows']) for r in rules)} row(s) withheld")

    # --- C: rules and the item registry agree, both ways --------------------------------------
    verdicts: dict[str, set] = {}
    with open(REGISTRY, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            verdicts.setdefault(r["item"], set()).add(r["verdict"])
    all_defect = {i for i, v in verdicts.items() if v == {"defect"}}
    withheld = {norm(r["item"]) for r in rules if r["source"] == REGISTRY_SOURCE}
    for r in rules:
        if r["source"] != REGISTRY_SOURCE:
            problems.append(f"rule {(r['source'], r['item'], r['unit'])}: no item registry covers "
                            f"source {r['source']!r}, so nothing establishes the item is a defect")
            continue
        v = verdicts.get(norm(r["item"]))
        if v is None:
            problems.append(f"rule {(r['source'], r['item'], r['unit'])}: item absent from "
                            "item_equivalences.csv -- nothing records which raw product it carries")
        elif v != {"defect"}:
            problems.append(f"rule {(r['source'], r['item'], r['unit'])}: the registry's verdicts for "
                            f"this item are {sorted(v)}, not only `defect` -- withholding it discards "
                            "rows the registry approves or has not decided")
    for i in sorted(all_defect - withheld):
        problems.append(f"registry item {i!r}: every raw product it carries is a `defect`, so its "
                        "correct series in iia is empty -- but no withhold rule covers it, and the "
                        "harmonized build publishes it as the commodity it is named for")
    print(f"  registry: {len(all_defect)} item(s) whose every product is a defect, "
          f"{len(withheld)} withheld")

    # --- D/E: against layer B and the matcher's output, where present ------------------------
    import extdata
    if not os.path.exists(extdata.LAYER_B) or not os.path.exists(MATCHED):
        print("SKIP arms D/E: layer B or matched_rows.parquet absent; scope and matcher agreement run "
              "on a maintainer's machine, not here")
    else:
        import pandas as pd
        lb = extdata.load_layer_b()
        lb = lb[~lb["is_aggregate"]]
        _, per_rule = matchlib.item_withheld(lb, rules)
        for k, r in enumerate(rules):
            if per_rule[k] != int(r["observed_rows"]):
                problems.append(f"{(r['source'], r['item'], r['unit'])}: selects {per_rule[k]} layer-B "
                                f"row(s), the table records {r['observed_rows']}")
        keys = {(r["source"], r["item"]) for r in rules}
        ruled = {(r["source"], r["item"], r["unit"]) for r in rules}
        for (s, i) in sorted(keys):
            for u in sorted(lb.loc[(lb["source"] == s) & (lb["item"] == i), "unit"].dropna().unique()):
                if (s, i, u) not in ruled:
                    problems.append(f"{(s, i)}: layer B carries unit {u!r} for a withheld item and no "
                                    "rule covers it -- those rows are still published")
        m = pd.read_parquet(MATCHED)
        if "item_withheld" not in m.columns:
            problems.append("matched_rows.parquet has no `item_withheld`; re-run 01_match_and_findings.py")
        else:
            want, _ = matchlib.item_withheld(m, rules)
            bad = int((want.values != m["item_withheld"].astype(bool).values).sum())
            if bad:
                problems.append(f"matched_rows.parquet: {bad} row(s) carry an item_withheld flag the "
                                "table does not imply -- stale; re-run 01_match_and_findings.py")
            print(f"  matched_rows.parquet: {int(m['item_withheld'].sum())} row(s) flagged")
    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print("  " + p)
        return 1
    print("\nPASS: every withhold is adjudicated, and every all-defect registry item is withheld")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
