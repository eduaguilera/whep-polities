#!/usr/bin/env python3
"""Validate the FAO-1952 land-use correction table's diagnoses against its own arithmetic.

`pipelines/polity-autoimprove/state/landuse_corrections.csv` (issue #4) is a
repair table: for each bad cell in the self-checking FAO land-use block it records
what was recorded, what the block's arithmetic implies, and WHY the recorded value
is wrong. The last of those three is the only one a machine cannot re-derive, and
it is the one a consumer acts on — a row labelled `decimal point dropped (x100)`
invites an upstream fixer to divide by 100, which is a different number from the
value in `implied_correct` unless the label is true.

That is not hypothetical. Until 2026-08-14 the generator tested the ratio
`recorded / implied` against 100 with a 2% window, so Brazil 1947 (arable 1,918,835
for an implied 18,835, ratio 101.9) shipped labelled `decimal point dropped (x100)`
— while 18,835 x 100 is 1,883,500, not 1,918,835. The real defect was two digits
prepended. Dividing by 100 would have "fixed" Brazil's arable land to 19,188.35.

So this gate re-derives every label from `recorded` and `implied_correct`:

  decimal point dropped (xK)  recorded == implied x K to within one unit. Exactly:
                              a decimal shift is not an approximation, and treating
                              it as one is the defect above.
  digits prepended            the decimal string of recorded ends with that of
                              implied, and recorded is the larger.
  spurious row                action must be drop_row with no implied value: the
                              cell is an extra row, not a corrupted number.
  value too large (basis      the arithmetic forces a value but no digit story
  unclear)                    explains it, so action must be review_cell — never
                              replace_value, which would invite an unattended
                              rewrite of a cell nobody has explained.
  components sum to X but     action must be review, and X / total must match the
  total is Y                  row's own recorded / implied_correct.

It also checks the columns a consumer reads by name, and that every `action` is one
of the four the table defines.

Usage:
  python3 scripts/validate_landuse_corrections.py
Exit 1 if any label disagrees with the arithmetic it describes.
"""
import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/landuse_corrections.csv")

COLUMNS = ["polity_code", "year", "item", "recorded", "implied_correct", "action",
           "diagnosis", "use_total", "territory_1000ha", "components_present"]
ACTIONS = {"replace_value", "drop_row", "review_cell", "review"}

SHIFT = re.compile(r"^decimal point dropped \(x(10|100|1000)\)")
SUMS = re.compile(r"^components sum to ([\d,]+) but total is ([\d,]+)$")


def num(s):
    try:
        return float(str(s).replace(",", ""))
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
    where = f"{r.get('polity_code')} {r.get('year')} {str(r.get('item'))[:40]}"
    action, diag = r.get("action", ""), r.get("diagnosis", "")
    rec, imp = num(r.get("recorded")), num(r.get("implied_correct"))

    if action not in ACTIONS:
        problems.append(f"{where}: action {action!r} is not one of {sorted(ACTIONS)}")

    m = SHIFT.match(diag)
    if m:
        k = int(m.group(1))
        if rec is None or imp is None:
            problems.append(f"{where}: labelled a decimal shift but has no numbers")
        elif abs(rec - imp * k) > 1.0:
            problems.append(
                f"{where}: labelled 'decimal point dropped (x{k})' but "
                f"{imp:,.3f} x {k} = {imp * k:,.3f}, not the recorded {rec:,.3f} "
                f"(off by {abs(rec - imp * k):,.3f}) — a decimal shift is exact, so "
                f"this label is wrong and dividing by {k} would not recover the cell"
            )
        if action != "replace_value":
            problems.append(f"{where}: a recoverable decimal shift must be "
                            f"action=replace_value, not {action!r}")
        continue

    if diag == "digits prepended":
        if rec is None or imp is None:
            problems.append(f"{where}: labelled 'digits prepended' but has no numbers")
        elif not (rec > imp and str(int(round(rec))).endswith(str(int(round(imp))))):
            problems.append(
                f"{where}: labelled 'digits prepended' but {rec:,.0f} does not end "
                f"with {imp:,.0f}"
            )
        if action != "replace_value":
            problems.append(f"{where}: a recoverable prepend must be "
                            f"action=replace_value, not {action!r}")
        continue

    if diag.startswith("spurious row"):
        if action != "drop_row":
            problems.append(f"{where}: a spurious row must be action=drop_row, "
                            f"not {action!r}")
        if str(r.get("implied_correct", "")).strip():
            problems.append(f"{where}: a spurious row has no corrected value, but "
                            f"implied_correct is {r['implied_correct']!r}")
        continue

    if diag.startswith("value too large"):
        if action != "review_cell":
            problems.append(
                f"{where}: the arithmetic locates this cell but no digit story "
                f"explains it, so it must be action=review_cell, not {action!r} — "
                f"replace_value would invite an unattended rewrite"
            )
        continue

    m = SUMS.match(diag)
    if m:
        said_sum, said_total = num(m.group(1)), num(m.group(2))
        if action != "review":
            problems.append(f"{where}: a block with no single-cell story must be "
                            f"action=review, not {action!r}")
        if rec is None or abs(said_sum - rec) > 0.5:
            problems.append(f"{where}: text says components sum to {said_sum:,.0f} "
                            f"but `recorded` is {rec}")
        if imp is None or abs(said_total - imp) > 0.5:
            problems.append(f"{where}: text says total is {said_total:,.0f} but "
                            f"`implied_correct` is {imp}")
        continue

    problems.append(f"{where}: diagnosis {diag!r} matches none of this gate's "
                    f"known shapes, so nothing verified it")

by_action = {a: sum(1 for r in rows if r.get("action") == a) for a in sorted(ACTIONS)}
print(f"{len(rows)} correction row(s) in {os.path.relpath(TABLE, REPO)}")
print("  " + "   ".join(f"{a}={n}" for a, n in by_action.items()))
print(f"\nLABELS DISAGREEING WITH THEIR ARITHMETIC: {len(problems)}")
for p in problems[:40]:
    print(f"   FAIL {p}")

print(f"\n{'FAIL' if problems else 'PASS'}: {len(problems)} problem(s) in "
      f"{len(rows)} correction row(s)")
sys.exit(1 if problems else 0)
