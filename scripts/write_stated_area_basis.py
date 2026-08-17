#!/usr/bin/env python3
"""Publish, per (polity, source), the territorial basis the SOURCE's numbers were collected on.

WHY THIS FILE EXISTS (issue 166). `data/final/source_stated_areas.csv` already carries what each
statistical authority said its own reporting units measured -- but keyed by the source's RAW
LABEL (`ALGERIE`, `royaume uni`, `British West Indies Jamaica`), in French, with OCR damage, and
across nine editions that disagree with each other. A consumer holding production rows for a
polity cannot join to it: resolving a label to a polity needs the matcher, the French lexicon and
the digit screen that `scripts/validate_stated_areas.py` runs. So the one fact a per-km2 consumer
needs -- WHICH TERRITORY THE NUMERATOR WAS COLLECTED OVER -- existed only inside a gate, as prose
in a Python dict.

THE PROBLEM IS NOT AN ERROR, WHICH IS EXACTLY WHY IT NEEDS PUBLISHING. Measured today:

    DZA-1902-1919  our polygon 2,442,683 km2   IIA states   575,511 km2   4.24x
    SMO-1912-1956  our polygon    52,792 km2   IIA states    21,800 km2   2.42x
    MAN-1932-1945  our polygon   791,708 km2   IIA states 1,303,143 km2   0.61x

Algeria is the one to worry about. IIA counted the three CIVIL DEPARTMENTS of northern Algeria;
our polygon is the colony including the Southern Territories. The production figure is right, the
polygon is right, the join is right, and a yield computed as one over the other understates by a
factor of four with nothing to flag it. Only the BASIS mismatches, and basis is invisible to every
other check in this repo: `04_territory_basis.py` classifies whether a polygon's VINTAGE fits its
span, and the vintage here is fine.

WHAT THIS PUBLISHES, AND WHAT IT DOES NOT DO. It does not overwrite a polygon or pick a winner.
Both figures are correct for their purpose, so both are carried and the consumer chooses:
`build_constant_territory_series()` in the WHEP R package can use the basis the numerator was
collected on rather than the one the GeoPackage happens to hold. `basis_flag` marks the rows where
that choice changes the answer materially -- ratio at or beyond 1.5x in either direction.

An empty `note` on a `review` row is NOT reassurance. It means the gate accepts the polity because
some OTHER source's figure keeps it inside the accepted band, so no reason was ever recorded for
THIS source's basis. Per-source is the granularity a denominator needs: FAO and IIA disagree about
Tunisia by a quarter, and the row you are dividing came from one of them, not from their median.

Notes come from TWO dicts in `validate_stated_areas`, and the second exists because of that
sentence. `BASELINE` is bidirectional -- an entry for a polity now inside the band is itself a gate
failure -- so a polity accepted on IIA's figure while FAO's is 7.7x wrong (JAM-1800-2025, issue
111) could not keep its explanation there. `SOURCE_NOTES` holds those, and this table publishes
either, so a per-km2 consumer reading one source's row is still told the figure is bad.

The comparison itself is NOT reimplemented here -- it is `validate_stated_areas.analyse()`, so the
published table and the gate that guards it cannot drift apart.

Usage:
  python3 scripts/write_stated_area_basis.py            # rewrite the CSV
  python3 scripts/write_stated_area_basis.py --check     # verify the committed copy is current
"""
from __future__ import annotations

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(REPO, "data/final/source_stated_area_basis.csv")

sys.path.insert(0, os.path.join(REPO, "scripts"))

import validate_stated_areas as V  # noqa: E402  (path set above)

# A ratio this far from 1 means a per-km2 use has to decide which basis it wants. Deliberately
# LOOSER than the gate's 25% scope threshold: the gate asks "is a polygon defensible at all",
# this asks "would using the wrong one of two defensible territories change the answer".
REVIEW_RATIO = 1.5

COLUMNS = [
    "polity_code", "polity_name", "source", "stated_area_km2", "statements", "editions",
    "source_labels", "polygon_area_km2", "ratio_polygon_over_stated", "basis_flag", "note",
]

# Columns whose values are FLOATING-POINT GEODESY, compared with a tolerance by --check rather
# than as strings. Polygon areas come out of PROJ (ESRI:54034), and PROJ's last digits move
# between releases; an exact compare would turn main red on a dependency bump rather than on a
# data change, which is the failure mode this repo has already hit once with `air`.
NUMERIC = {"stated_area_km2", "polygon_area_km2", "ratio_polygon_over_stated"}
NUMERIC_TOLERANCE = 0.005  # 0.5%


def build() -> list:
    result = V.analyse()
    if isinstance(result, str):
        return result
    ours, names, per_source = result["ours"], result["names"], result["per_source"]
    rows = []
    for (code, source), info in sorted(per_source.items()):
        mine = ours[code]
        stated = info["stated"]
        ratio = mine / stated if stated else 0.0
        if info["digit_error_suspect"]:
            flag = "source_figure_suspect"
        elif ratio >= REVIEW_RATIO or ratio <= 1 / REVIEW_RATIO:
            flag = "review"
        else:
            flag = "agrees"
        note = V.BASELINE.get((code, source)) or V.SOURCE_NOTES.get((code, source), "")
        rows.append({
            "polity_code": code,
            "polity_name": names.get(code, ""),
            "source": source,
            "stated_area_km2": f"{stated:.0f}",
            "statements": info["statements"],
            "editions": ";".join(info["editions"]),
            "source_labels": ";".join(info["labels"]),
            "polygon_area_km2": f"{mine:.0f}",
            "ratio_polygon_over_stated": f"{ratio:.3f}",
            "basis_flag": flag,
            "note": " ".join(note.split()),
        })
    return rows


def _same(committed: list, fresh: list) -> list:
    if len(committed) != len(fresh):
        return [f"{len(committed)} committed rows vs {len(fresh)} regenerated"]
    diffs = []
    for c, f in zip(committed, fresh):
        for col in COLUMNS:
            cv, fv = c.get(col, ""), str(f[col])
            if col in NUMERIC:
                try:
                    a, b = float(cv), float(fv)
                except ValueError:
                    diffs.append(f"{c.get('polity_code')}/{c.get('source')}: {col} unparseable")
                    continue
                scale = max(abs(a), abs(b), 1e-9)
                if abs(a - b) / scale > NUMERIC_TOLERANCE:
                    diffs.append(f"{c.get('polity_code')}/{c.get('source')}: {col} {cv} -> {fv}")
            elif cv != fv:
                diffs.append(f"{c.get('polity_code')}/{c.get('source')}: {col} {cv!r} -> {fv!r}")
    return diffs


def main() -> int:
    check = "--check" in sys.argv
    rows = build()
    if isinstance(rows, str):
        print(rows)
        return 0

    if check:
        if not os.path.exists(DEST):
            print(f"FAIL: {os.path.relpath(DEST, REPO)} missing; run without --check")
            return 1
        with open(DEST, encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames != COLUMNS:
                print(f"FAIL: {os.path.basename(DEST)} columns are "
                      f"{reader.fieldnames} not {COLUMNS}")
                return 1
            committed = list(reader)
        diffs = _same(committed, rows)
        if diffs:
            print(f"FAIL: {os.path.basename(DEST)} is stale ({len(diffs)} difference(s))")
            for d in diffs[:10]:
                print(f"  {d}")
            print("\n  Fix: run scripts/write_stated_area_basis.py and commit data/final/.")
            return 1
        print(f"OK: {os.path.basename(DEST)} matches the sources ({len(rows)} (polity, source) "
              f"bases, {sum(1 for r in rows if r['basis_flag'] == 'review')} flagged for review)")
        return 0

    with open(DEST, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    review = [r for r in rows if r["basis_flag"] == "review"]
    print(f"wrote {len(rows)} (polity, source) territorial bases -> {os.path.relpath(DEST, REPO)}")
    print(f"  polities: {len({r['polity_code'] for r in rows})}   "
          f"sources: {sorted({r['source'] for r in rows})}")
    print(f"  flagged for review (>= {REVIEW_RATIO}x either way): {len(review)}   "
          f"with a recorded reason: {sum(1 for r in review if r['note'])}")
    for r in sorted(review, key=lambda r: -abs(float(r["ratio_polygon_over_stated"]) - 1))[:12]:
        print(f"    {r['polity_code']:18s} {r['source']:4s} ours {float(r['polygon_area_km2']):>12,.0f}"
              f"  stated {float(r['stated_area_km2']):>12,.0f}  "
              f"{float(r['ratio_polygon_over_stated']):>6.2f}x"
              f"{'' if r['note'] else '   [no recorded reason]'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
