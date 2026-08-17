#!/usr/bin/env python3
"""Validate the land-containment table's claims against its own arithmetic.

`pipelines/polity-autoimprove/state/land_containment.csv` (issue #29's last identity) records every
FAO-1952 land-use block whose ARABLE cell is smaller than something that must fit inside it: the
sum of the crop areas the same yearbook reports, or its irrigated-arable area. For each breach it
says WHICH of three things that means, and only one of the three is safe to act on:

  replace_value  the arable cell is short, and the value is recoverable: the block's own deficit
                 against `use total` puts the cell above its floor, and the restored figure is the
                 recorded one with a leading digit put back (43 -> 1,043).
  review_cell    the cell is located but no value is safe.
  review         the breach may not be a defect at all. Harvested area counts a double-cropped
                 field twice, so a crop-area floor above arable can be real agronomy.

The distinction between the last two and the first is the whole substance of the table, and it
rests on which bound binds. **A crop-area breach has a cropping-intensity escape; an
irrigated-area breach does not** -- irrigated arable land is arable land by definition. So the one
mistake that would make this table dangerous is dismissing an IRRIGATED breach as multiple
cropping, which is how Peru 1950 (arable 600, irrigated 750, block 1,000 short of its total)
would go back to looking fine. That is the defect this gate exists to name.

Every claim is re-derived from the row's own numbers, so nothing here needs the gitignored
`matched_rows.parquet`:

  bounds          `floor` must equal the LARGER of the two bounds present, and `binding_bound`
                  must name a bound whose value is that floor. A floor read off the weaker bound
                  understates every ratio in the file.
  ratio           must equal floor / arable_recorded, to four decimals.
  real breach     floor must exceed arable_recorded by more than the generator's window
                  (max(0.5, 1% of arable)). A non-breach sitting in a breach table sends someone
                  to repair a cell that is fine -- the same defect scripts/validate_subnational_
                  sums.py forbids in the other direction.
  crops           crop_area_floor and n_crops must be present together, and n_crops >= 1.
  review          may only be claimed where `crop_area_floor` is the binding bound: a breach of a
                  subset relation has no multiple-cropping explanation.
  replace_value   implied_correct - arable_recorded must equal block_deficit (the recovery must be
                  the block's OWN missing amount, not an invented number); implied_correct must
                  reach the floor, or the "correction" still violates the containment it claims to
                  fix; and its decimal string must end with the recorded one's, which is the
                  digits-dropped story the diagnosis asserts.
  no re-proposal  a replace_value row whose `landuse_block_status` says 06_landuse_consistency.py
                  already localised the SAME cell would give a consumer two different values for
                  one cell.
  no value        review and review_cell must propose none.

Usage:
  python3 scripts/validate_land_containment.py
Exit 1 if any claim disagrees with the arithmetic it describes.
"""
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/land_containment.csv")

COLUMNS = ["polity_code", "year", "arable_recorded", "crop_area_floor", "n_crops",
           "irrigated_arable", "binding_bound", "floor", "ratio", "use_total", "block_deficit",
           "implied_correct", "action", "diagnosis", "landuse_block_status"]
ACTIONS = {"replace_value", "review_cell", "review"}
BOUNDS = {"crop_area_floor", "irrigated_arable"}
# the generator's breach window, --tolerance, and its floor of half a printed unit
TOLERANCE = 0.01
# 06 verdicts that already name a value for the arable cell itself
LOCALISED = ("replace_value:", "review_cell:")


def num(value):
    text = str(value).replace(",", "").strip()
    if text == "":
        return None
    try:
        return float(text)
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
    where = f"{r.get('polity_code')} {r.get('year')}"
    action = r.get("action", "")
    arable, floor, ratio = num(r.get("arable_recorded")), num(r.get("floor")), num(r.get("ratio"))
    crop, irrig = num(r.get("crop_area_floor")), num(r.get("irrigated_arable"))
    n_crops, deficit = num(r.get("n_crops")), num(r.get("block_deficit"))
    implied, binding = num(r.get("implied_correct")), r.get("binding_bound", "")

    if action not in ACTIONS:
        problems.append(f"{where}: action {action!r} is not one of {sorted(ACTIONS)}")
    if binding not in BOUNDS:
        problems.append(f"{where}: binding_bound {binding!r} is not one of {sorted(BOUNDS)}")
    if None in (arable, floor, ratio) or arable <= 0:
        problems.append(f"{where}: arable_recorded/floor/ratio must be positive numbers, got "
                        f"{r.get('arable_recorded')!r}/{r.get('floor')!r}/{r.get('ratio')!r}")
        continue

    present = {"crop_area_floor": crop, "irrigated_arable": irrig}
    have = {k: v for k, v in present.items() if v is not None}
    if not have:
        problems.append(f"{where}: neither bound is populated, so nothing says what the floor "
                        f"{floor:,.1f} was measured from")
    else:
        if abs(max(have.values()) - floor) > 0.05:
            problems.append(
                f"{where}: floor is {floor:,.1f} but the LARGER bound present is "
                f"{max(have.values()):,.1f} ({max(have, key=have.get)}) — a floor read off the "
                f"weaker bound understates the breach"
            )
        if binding in have and abs(have[binding] - floor) > 0.05:
            problems.append(f"{where}: binding_bound says {binding} but that bound is "
                            f"{have[binding]:,.1f}, not the floor {floor:,.1f}")
        elif binding not in have:
            problems.append(f"{where}: binding_bound says {binding} but that column is empty")

    if abs(ratio - floor / arable) > 5e-4:
        problems.append(f"{where}: ratio is {ratio:.4f} but floor / arable_recorded is "
                        f"{floor / arable:.4f} — the row's own three numbers disagree")

    window = max(0.5, TOLERANCE * arable)
    if floor - arable <= window:
        problems.append(
            f"{where}: floor {floor:,.1f} does not exceed arable {arable:,.1f} by more than the "
            f"generator's window ({window:,.1f}), so this is not a containment breach and a "
            f"consumer would repair a cell that is fine"
        )

    if (crop is None) != (n_crops in (None, 0.0)):
        problems.append(f"{where}: crop_area_floor is {r.get('crop_area_floor')!r} and n_crops is "
                        f"{r.get('n_crops')!r}; a floor with no crops behind it, or crops with no "
                        f"floor, means the bound cannot be re-derived")

    if action == "review":
        if binding != "crop_area_floor":
            problems.append(
                f"{where}: dismissed as possible multiple cropping while the binding bound is "
                f"{binding}. Irrigated arable land IS arable land, so that breach has no "
                f"cropping-intensity explanation and may not be waved through as one"
            )
        if implied is not None:
            problems.append(f"{where}: review proposes no value, but implied_correct is "
                            f"{r['implied_correct']!r}")
    elif action == "review_cell":
        if implied is not None:
            problems.append(f"{where}: review_cell proposes no value, but implied_correct is "
                            f"{r['implied_correct']!r}")
    elif action == "replace_value":
        if implied is None:
            problems.append(f"{where}: replace_value with an empty implied_correct, so nothing "
                            f"says what the arable cell should have been")
            continue
        if deficit is None:
            problems.append(f"{where}: replace_value with no block_deficit, so the recovery rests "
                            f"on nothing the block itself says")
        elif abs((implied - arable) - deficit) > 0.5:
            problems.append(
                f"{where}: proposes {implied:,.1f} for {arable:,.1f}, a change of "
                f"{implied - arable:,.1f}, while the block is {deficit:,.1f} short of use total — "
                f"the recovery is not the block's own missing amount"
            )
        if implied < floor - 0.05:
            problems.append(
                f"{where}: proposes {implied:,.1f} for an arable cell that must hold at least "
                f"{floor:,.1f}, so the correction still breaches the containment it claims to fix"
            )
        if not str(int(round(implied))).endswith(str(int(round(arable)))):
            problems.append(
                f"{where}: diagnosed as digits dropped, but {implied:,.0f} does not end with the "
                f"recorded {arable:,.0f} — a value with no digit story is not safe to apply"
            )
        if str(r.get("landuse_block_status", "")).startswith(LOCALISED):
            problems.append(
                f"{where}: 06_landuse_consistency.py already names a value for this same cell "
                f"({r['landuse_block_status']}), so a consumer would have two different "
                f"corrections for it"
            )

by_action = {a: sum(1 for r in rows if r.get("action") == a) for a in sorted(ACTIONS)}
print(f"{len(rows)} row(s) in {os.path.relpath(TABLE, REPO)}")
print("  " + "   ".join(f"{a}={n}" for a, n in by_action.items()))

print(f"\nCLAIMS DISAGREEING WITH THEIR ARITHMETIC: {len(problems)}")
for p in problems[:40]:
    print(f"   FAIL {p}")

print(f"\n{'FAIL' if problems else 'PASS'}: {len(problems)} problem(s) in {len(rows)} row(s)")
sys.exit(1 if problems else 0)
