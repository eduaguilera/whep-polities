#!/usr/bin/env python3
"""Cross-block containment check for the FAO 1952 land-use block: what must fit INSIDE arable land.

Issue 29's list of self-checking arithmetic is now down to its last identity, the inequality
chain **crop area <= arable land <= total land**. 06_landuse_consistency.py already exploits the
land-use block's own arithmetic (components sum to `use total`, `use total` equals the territory's
area). This stage is the CROSS-BLOCK half: it holds the arable-land cell against numbers that live
in a DIFFERENT block of the same yearbook and must fit inside it.

MEASURED FIRST, as the issue asks, because two thirds of the chain turned out not to be worth a
stage:

  * `arable <= use total` finds 6 blocks (Brazil 1947, Jamaica 1948, Costa Rica 1950, Israel 1951,
    New Caledonia 1949, Reunion 1951) and ALL SIX ALREADY CARRY a 06 correction row. Arable
    exceeding the block's own total is a special case of the components exceeding it, so the
    within-block sum sees every instance. That half of the chain is not checked here; it would only
    restate 06.
  * `crop area <= arable` is where the cross-block information is, because the crop-area block is
    one 06 never reads. Of 169 land-use blocks carrying an arable cell, 99 also carry crop areas
    and 4 of those breach it; 54 carry an irrigated area and 1 of those breaches it.

WHAT BOUNDS ARABLE FROM BELOW. Two independent floors, both from the same yearbook:

  crop_area_floor   the sum of the 32 crops fao1952 reports an area for. A LOWER bound, and a
                    loose one: the source reports no area at all for wheat, maize, barley or
                    potatoes, so the floor omits the largest arable crops in most countries. A
                    breach of a floor this loose is strong evidence.
  irrigated_arable  `irrigation arable land orchards vineyards`. Irrigated arable land is arable
                    land BY DEFINITION, so this bound has no escape (see below). Egypt 1951 sits
                    exactly on it -- 2,451 against 2,451 -- which is correct and not a breach.

Overlapping crop families are collapsed to their MINIMUM, not summed: `cottonseed` and
`cotton lint` are two products of one field, and so are `linseed` and `flax fiber` in this source
(Netherlands 1951 reports 30 for both, West Germany 8 for both, Peru 1 for both). Summing them
would inflate a bound whose whole value is that it is a floor. Taking the minimum can only weaken
the check, never manufacture a breach.

WHY THE CHECK IS ONE-SIDED AND NEEDS AN ESCAPE. `crop area <= arable` is NOT an identity that
always holds: harvested area counts a double-cropped field twice, so a cropping intensity above 1
is real agronomy, not a defect. That is why a breach of the crop floor alone is reported and never
corrected. The two bounds therefore carry different weight, and the table says which one binds:

  irrigated_arable  a breach cannot be cropping intensity. Irrigated arable is a SUBSET.
  crop_area_floor   a breach may be cropping intensity, and is only corrected when a SECOND,
                    independent fact says the arable cell is short.

THE SECOND FACT, AND THE THREE RECOVERIES. Where the block is short of its own `use total`, the
deficit is a candidate for the arable cell -- but 06 cannot tell a short arable cell from a MISSING
CATEGORY ROW, and its docstring says so: it flags the round deficits (1,000 / 2,000 / 6,000 /
10,000) and deliberately does not correct them, reading them as a missing row. The containment
floor is what decides between the two, because a missing row says nothing about arable while a
floor above arable proves arable itself is too small. Where both point at the same cell and the
restored value is the recorded one with a leading digit put back, all three of these agree:

  NLD-1830-2025 1951  arable 43, crop floor 409      block short by 1,000  ->  1,043
  F78-1949-1990 1951  arable 539, crop floor 2,867   block short by 8,000  ->  8,539
  PER-1942-2025 1950  arable 600, irrigated 750      block short by 1,000  ->  1,600

The third action the table can carry, `review_cell` -- an irrigated-area breach the block deficit
does NOT restore, so the cell is located but no value is safe -- has no instance on this run. It is
kept because it is the only honest verdict for that combination, and the gate validates it if a
re-run of the source ever produces one.

"1043" ends with "43", "8539" with "539", "1600" with "600": digits DROPPED, the mirror of 06's
`digits prepended`. Each restored value also makes the block sum to `use total` exactly, and each
is the figure the historical record carries (Netherlands ~1.0m ha arable, West Germany ~8.5m
against the 5,583 of grassland in the same block, Peru ~1.6m).

Peru is the one none of the existing guards can see. Its deficit is 1,000 on a `use total` of
124,905, and 06's consistency window is 2% of the total -- 2,498 -- so the block passes as
consistent and never reaches 06's table at all. It takes the irrigated-area bound, from another
block, to show that the arable cell is 1,000 short.

NOT CORRECTED, deliberately:

  HKG-1842-2025 1951  crop floor 16 against arable 10, block sums to `use total` exactly. Rice
                      paddy alone is 13. Hong Kong's paddy was double-cropped, so an intensity of
                      1.6 is plausible and there is no second fact.
  THA-1909-2025 1949  crop floor 5,144 against arable 4,750 (rice paddy alone 4,963), block sums
                      exactly. An intensity of 1.08 is well inside what Thai paddy could give.

Like 06 and 07, this does NOT modify the source parquet (it lives outside the repo, in the
maintainer's own store). It writes a correction table so the fix lands upstream in the
consolidation step. scripts/validate_land_containment.py re-derives every claim in it.

Usage:
  python3 pipelines/polity-autoimprove/13_land_containment.py [--tolerance 0.01]
Writes state/land_containment.csv
"""
import argparse
import os
import warnings

import pandas as pd

warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
H = os.path.join(REPO, "pipelines/polity-autoimprove/state")

ARABLE = "use agricultural area arable land orchards"
TOTAL = "use total"
IRRIGATED = "irrigation arable land orchards vineyards"
# `use land` is a sub-aggregate of `use total` whose exclusions are undocumented (see 06), so the
# deficit is measured against `use total` and these five components only.
COMPONENTS = [ARABLE,
              "use agricultural area permanent peadows pastures",
              "use builton wasteland",
              "use forests woodlands",
              "use unused productive land"]
# Two products of one field. Collapsed to their MINIMUM so the floor stays a floor.
OVERLAP_FAMILIES = [{"cottonseed", "cotton lint"}, {"linseed", "flax fiber"}]

COLS = ["polity_code", "year", "arable_recorded", "crop_area_floor", "n_crops",
        "irrigated_arable", "binding_bound", "floor", "ratio", "use_total", "block_deficit",
        "implied_correct", "action", "diagnosis", "landuse_block_status"]

ap = argparse.ArgumentParser()
ap.add_argument("--tolerance", type=float, default=0.01,
                help="breach window as a fraction of the arable cell (default 0.01)")
args = ap.parse_args()


def crop_floor(items):
    """Lower bound on cropped area from a block's per-crop areas, families collapsed to min."""
    used = dict(items)
    total, n = 0.0, 0
    for fam in OVERLAP_FAMILIES:
        present = [k for k in fam if k in used]
        if present:
            total += min(used[k] for k in present)
            n += 1
            for k in present:
                del used[k]
    return total + sum(used.values()), n + len(used)


m = pd.read_parquet(os.path.join(H, "matched_rows.parquet"))
f = m[m["source"] == "fao1952"].copy()
f["v"] = pd.to_numeric(f["value"], errors="coerce")
f["item"] = f["item"].astype(str)
f = f[f["v"].notna() & f["year"].notna()]

lu = f[f["item"].str.startswith("use ")]
# crop areas: the 1000 ha rows that are neither a land-use category nor an irrigation aggregate
ca = f[(f["unit"] == "1000 hectares") & ~f["item"].str.startswith(("use ", "irrigation "))]
# Per (code, year, item) the MAXIMUM over the source's country labels, never their sum. Two labels
# can route to one polity because one is an OCR variant of the other (fao1952 carries both
# "Netherlands" and "Necherlands", and "Germany Western" and "Germany  Western"), and because a
# source can report a whole and one of its parts. Summing would double-count the second case and
# inflate a bound whose whole value is that it is a floor.
irr = f[f["item"] == IRRIGATED].groupby(["whep_code", "year"])["v"].max()

# what 06 already says about each block, so a cell is never proposed twice
lc_path = os.path.join(H, "landuse_corrections.csv")
lc = pd.read_csv(lc_path) if os.path.exists(lc_path) else pd.DataFrame(
    columns=["polity_code", "year", "item", "action"])

blocks = lu.pivot_table(index=["whep_code", "year"], columns="item", values="v", aggfunc="sum")
n_checked_crop = n_checked_irr = 0
rows = []
for (code, year), b in blocks.iterrows():
    arable = b.get(ARABLE)
    if pd.isna(arable) or arable <= 0:
        continue
    grp = ca[(ca["whep_code"] == code) & (ca["year"] == year)]
    floor_crop, n_crops = crop_floor(grp.groupby("item")["v"].max().to_dict())
    floor_irr = irr.get((code, year), float("nan"))
    if n_crops:
        n_checked_crop += 1
    if not pd.isna(floor_irr):
        n_checked_irr += 1

    # the binding bound is the larger floor; irrigated wins ties because it has no escape
    cands = []
    if not pd.isna(floor_irr):
        cands.append((floor_irr, "irrigated_arable"))
    if n_crops:
        cands.append((floor_crop, "crop_area_floor"))
    if not cands:
        continue
    floor, binding = max(cands)

    window = max(0.5, args.tolerance * arable)
    if floor - arable <= window:
        continue

    present = [c for c in COMPONENTS if c in b.index and not pd.isna(b.get(c))]
    total = b.get(TOTAL)
    deficit = (float(total) - sum(float(b[c]) for c in present)
               if not pd.isna(total) and len(present) >= 2 else float("nan"))

    # 06's verdict on this block, if any
    same = lc[(lc["polity_code"] == code) & (lc["year"] == int(year))]
    if len(same) == 0:
        status = "absent"
    else:
        cell = same[same["item"] == ARABLE]
        status = (f"{cell.iloc[0]['action']}:{ARABLE.split()[-1]}" if len(cell)
                  else f"{same.iloc[0]['action']}:block")

    restored = (arable + deficit) if not pd.isna(deficit) else float("nan")
    digits_dropped = (not pd.isna(restored) and restored > arable
                      and str(int(round(restored))).endswith(str(int(round(arable)))))
    # Correct only when the block's OWN deficit lands the arable cell above its floor AND the
    # restored value is the recorded one with a leading digit put back. Either fact alone is
    # a guess; a cell 06 already localised is never re-proposed here.
    if digits_dropped and restored >= floor and not status.startswith(
            ("replace_value:", "review_cell:")):
        action = "replace_value"
        diag = (f"digits dropped: {binding} {floor:,.0f} exceeds arable {arable:,.0f}, and the "
                f"block is {deficit:,.0f} short of use total — restoring the leading digit(s) "
                f"satisfies both")
        implied = round(float(restored), 3)
    elif binding == "irrigated_arable":
        action = "review_cell"
        diag = (f"irrigated arable {floor:,.0f} exceeds arable {arable:,.0f}, which is "
                f"impossible by definition, but the block deficit does not restore it")
        implied = ""
    else:
        action = "review"
        diag = (f"crop area floor {floor:,.0f} over {n_crops} crop(s) exceeds arable "
                f"{arable:,.0f} (intensity {floor / arable:.2f}x); the block is consistent, so "
                f"multiple cropping is not excluded and no value is proposed")
        implied = ""

    rows.append({"polity_code": code, "year": int(year), "arable_recorded": float(arable),
                 "crop_area_floor": round(float(floor_crop), 3) if n_crops else "",
                 "n_crops": n_crops,
                 "irrigated_arable": ("" if pd.isna(floor_irr) else float(floor_irr)),
                 "binding_bound": binding, "floor": round(float(floor), 3),
                 "ratio": round(float(floor) / float(arable), 4),
                 "use_total": ("" if pd.isna(total) else float(total)),
                 "block_deficit": ("" if pd.isna(deficit) else round(float(deficit), 3)),
                 "implied_correct": implied, "action": action, "diagnosis": diag,
                 "landuse_block_status": status})

out = pd.DataFrame(rows, columns=COLS)
if len(out):
    out = out.sort_values("ratio", ascending=False)
out.to_csv(os.path.join(H, "land_containment.csv"), index=False)

# the other half of issue 29's chain, measured and reported rather than checked (see docstring)
over = blocks[blocks[ARABLE].notna() & blocks[TOTAL].notna()
              & (blocks[ARABLE] > blocks[TOTAL])]
covered = sum(1 for (code, year) in over.index
              if len(lc[(lc["polity_code"] == code) & (lc["year"] == int(year))]))

print(f"land-use blocks with an arable cell: {int(blocks[ARABLE].notna().sum())}")
print(f"  bounded by crop areas: {n_checked_crop}   bounded by irrigated area: {n_checked_irr}")
print(f"breaches: {len(out)}")
for a in ("replace_value", "review_cell", "review"):
    print(f"  {a}: {int((out['action'] == a).sum()) if len(out) else 0}")
print(f"\narable > use total: {len(over)} block(s), {covered} already in "
      f"landuse_corrections.csv (this stage does not restate them)")
for r in out.itertuples():
    good = f"{r.implied_correct:>10,.0f}" if r.implied_correct != "" else "   (no value)"
    print(f"  {r.polity_code:16s} {r.year}  arable {r.arable_recorded:>10,.0f} vs "
          f"{r.binding_bound:16s} {r.floor:>10,.0f}  ({r.ratio:.2f}x) -> {good}  [{r.action}]")
print(f"\nwrote {os.path.join(H, 'land_containment.csv')}")
