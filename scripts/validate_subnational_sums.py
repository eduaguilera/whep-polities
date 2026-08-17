#!/usr/bin/env python3
"""Validate the sub-national sums table's claims against its own arithmetic.

`pipelines/polity-autoimprove/state/subnational_sums.csv` (issue #29) records, for every
(table, item, indicator, unit, period) key where fao1952 reports a whole and at least two of
its parts, what the whole says, what the parts sum to, and WHICH OF THREE THINGS that means.
The third is the only one a machine cannot re-derive from the file, and it is the one a
consumer acts on:

  mark_aggregate  the whole IS the sum of its parts, so the row is an aggregate layer B
                  leaves unmarked -- a consumer must drop the whole or drop the parts.
  relabel_rows    the parts sum to MORE than the whole, which is impossible, and the reason
                  is that they are not its parts: `proposed` gives the relabelling that
                  makes the identity hold.
  review          the parts sum to more than the whole and no relabelling explains it, so
                  the offending cell is the whole's and no value is proposed.

The three are distinguished by the SIGN AND SIZE of one number, `residual`, so a row whose
action does not match its own residual is telling a consumer to do the opposite of what the
data says. Two ways that goes wrong, and both are cheap to make:

  * an aggregate row with a residual -- "these parts sum to the whole" asserted about a block
    that is 18 units short of it, which is what a PERCENTAGE tolerance produced while the
    generator was being written: four keys with residuals of 6, 12, 18 and 31 passed as exact
    aggregate relations. A consumer that drops the whole then loses the difference silently.
  * a `review` row whose parts are SHORT of the whole -- a deficit, which is the expected
    state of a partly extracted family and not a defect at all. The table's own rule is that
    no deficit is reported; a deficit sitting in it as a defect sends someone to repair a
    cell that is fine.

So this gate re-derives every claim from `whole`, `parts_sum` and `residual`:

  residual        must equal parts_sum - whole, to a tenth. The row's own three numbers.
  mark_aggregate  |residual| <= 0.5, i.e. within half a printed unit.
  relabel_rows    residual > 0.5 (a surplus), and `proposed` must hold at least n_parts
                  mappings of the form `old -> new`, each actually changing the label.
  review          residual > 0.5, and no value proposed.
  no deficits     no row at all with residual < -0.5, whatever its action.
  part_labels     must list exactly n_parts labels, and n_parts must be at least 2: a sum
                  over one part is a deficit test, not an identity test.

It also checks the columns a consumer reads by name.

Usage:
  python3 scripts/validate_subnational_sums.py
Exit 1 if any claim disagrees with the arithmetic it describes.
"""
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/subnational_sums.csv")

COLUMNS = ["source", "source_detail", "whole_label", "part_labels", "n_parts", "item",
           "indicator", "unit", "year", "period", "whole", "parts_sum", "residual",
           "action", "proposed", "diagnosis"]
ACTIONS = {"mark_aggregate", "relabel_rows", "review"}

# Half a printed unit. The generator's own window; see its `tolerance`.
TOL = 0.5


def num(value):
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


if not os.path.exists(TABLE):
    print(f"FAIL: {os.path.relpath(TABLE, REPO)} is missing")
    sys.exit(1)

with open(TABLE, encoding="utf-8") as fh:
    rows = list(csv.DictReader(fh))
header = list(rows[0].keys()) if rows else []

problems = []
missing = [c for c in COLUMNS if c not in header]
if missing:
    problems.append(f"columns a consumer reads by name are absent: {missing}")

for r in rows:
    where = (f"{r.get('whole_label')} {str(r.get('item'))[:28]} "
             f"{r.get('year') or r.get('period')}")
    action = r.get("action", "")
    whole, parts, residual = num(r.get("whole")), num(r.get("parts_sum")), num(r.get("residual"))
    n_parts, labels = num(r.get("n_parts")), str(r.get("part_labels", ""))

    if action not in ACTIONS:
        problems.append(f"{where}: action {action!r} is not one of {sorted(ACTIONS)}")
    if None in (whole, parts, residual):
        problems.append(f"{where}: whole/parts_sum/residual must all be numbers, got "
                        f"{r.get('whole')!r}/{r.get('parts_sum')!r}/{r.get('residual')!r}")
        continue

    if abs((parts - whole) - residual) > 0.1:
        problems.append(f"{where}: residual is {residual:,.3f} but parts_sum - whole is "
                        f"{parts - whole:,.3f} — the row's own three numbers disagree")

    listed = [p for p in (x.strip() for x in labels.split(";")) if p]
    if n_parts is None or n_parts < 2:
        problems.append(f"{where}: n_parts is {r.get('n_parts')!r}; an identity needs at "
                        f"least 2 parts, one part against its whole is only a deficit test")
    elif len(listed) != int(n_parts):
        problems.append(f"{where}: n_parts says {int(n_parts)} but part_labels lists "
                        f"{len(listed)}: {listed}")

    # Checked BEFORE the deficit rule below, because a mark_aggregate row with a deficit is
    # the specific defect a percentage tolerance produces, and it deserves to be reported as
    # the false aggregate claim it is rather than as a stray deficit row.
    if action == "mark_aggregate":
        if abs(residual) > TOL:
            problems.append(
                f"{where}: claims the whole ({whole:,.1f}) IS the sum of its parts "
                f"({parts:,.1f}) while they differ by {abs(residual):,.1f}, more than half a "
                f"printed unit — a consumer dropping the whole as a duplicate of its parts "
                f"loses that difference silently"
            )
        if str(r.get("proposed", "")).strip():
            problems.append(f"{where}: mark_aggregate proposes no relabelling, but "
                            f"`proposed` is {r['proposed']!r}")
        continue

    if residual < -TOL:
        problems.append(
            f"{where}: parts are {-residual:,.1f} SHORT of the whole. A deficit means the "
            f"extraction carries only some of the parts, which is not a defect, and this "
            f"table's rule is that none is reported — so a consumer would repair a cell "
            f"that is fine"
        )
        continue

    # relabel_rows and review both assert the impossible direction: parts exceed the whole.
    if residual <= TOL:
        problems.append(f"{where}: action {action!r} asserts the parts EXCEED the whole, "
                        f"but the residual is {residual:,.1f}")

    if action == "relabel_rows":
        mappings = [m.strip() for m in str(r.get("proposed", "")).split(";") if m.strip()]
        if not mappings:
            problems.append(f"{where}: relabel_rows with an empty `proposed`, so nothing "
                            f"says what the parts should have been called")
        if n_parts is not None and len(mappings) < int(n_parts):
            problems.append(f"{where}: relabel_rows proposes {len(mappings)} relabelling(s) "
                            f"for {int(n_parts)} part(s): every part must be renamed or the "
                            f"identity it is claimed to satisfy cannot hold")
        for m in mappings:
            if " -> " not in m:
                problems.append(f"{where}: {m!r} is not an `old -> new` mapping")
                continue
            old, new = (s.strip() for s in m.split(" -> ", 1))
            if not old or not new or old == new:
                problems.append(f"{where}: mapping {m!r} renames nothing")
    elif action == "review" and str(r.get("proposed", "")).strip():
        problems.append(f"{where}: review proposes no value, but `proposed` is "
                        f"{r['proposed']!r}")

by_action = {a: sum(1 for r in rows if r.get("action") == a) for a in sorted(ACTIONS)}
print(f"{len(rows)} row(s) in {os.path.relpath(TABLE, REPO)}")
print("  " + "   ".join(f"{a}={n}" for a, n in by_action.items()))
print(f"\nCLAIMS DISAGREEING WITH THEIR ARITHMETIC: {len(problems)}")
for p in problems[:40]:
    print(f"   FAIL {p}")

print(f"\n{'FAIL' if problems else 'PASS'}: {len(problems)} problem(s) in {len(rows)} row(s)")
sys.exit(1 if problems else 0)
