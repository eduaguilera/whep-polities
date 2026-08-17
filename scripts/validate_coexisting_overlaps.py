#!/usr/bin/env python3
"""Two coexisting polities may overlap only by a pinned amount of ground.

WHAT THIS IS FOR. Intersect the live polity set for one year against a grid and each
cell is handed to every polity whose polygon covers it. Where two coexisting polygons
cover the SAME ground, the cell is claimed twice, so a per-hectare rate applied to
claimed territory delivers that cell's quantity twice. `validate_shared_polygons.py`
forbids the extreme case -- two live rows on ONE polygon -- and cannot see partial
overlap, which is where nearly all of the remaining over-claim lives: measured on the
2015 slice, 544 of 68,549 half-degree cells claim more than they contain, 30.73 Mha in
excess (issue 143).

THE ISSUE THIS CLOSES HALF OF. Issue 143 separated that residual into three classes and
argued that a tolerance written before the largest class is decided has to be wide enough
to swallow 267,078 km2 of Western Sahara, at which point it means nothing. PR 247 decided
class 2 -- a polity's polygon is GROSS of the sub-polities that are themselves rows, see
`wiki/log.md` under `decision-nested-subpolity-polygons-are-gross` -- and left class 1
(disputed sovereignty) explicitly open, because netting, splitting or leaving the ESH/MAR
and ISR/PSE overlaps explicit is a territorial judgement this database will not invent.
This gate is the OTHER half: it pins the long tail so it cannot grow, and it does so
WITHOUT deciding class 1, by naming every substantial overlap individually with the class
it belongs to.

THE SEPARATION THAT MAKES THAT POSSIBLE, measured rather than assumed. Expressed as a
share OF THE SMALLER polity, the classes do not touch: the sliver tail reaches at most
1.07% (`MMR-1885-2025`/`THA-1909-2025`), the Saudi-Yemen frontier is 6.58% of Yemen, and
every disputed or nested pair is 14.1% or more -- most of them above 79%. Anything from
about 1.1% to 6.5% therefore splits "two sources disagreeing about where a border runs"
from "two rows claiming the same territory on purpose". This gate uses 10%: above it, a
pair must be NAMED and CLASSIFIED below; at or below it, the pair is a resolution
artefact and only its size is gated.

  A  SUBSTANTIAL   a coexisting pair overlapping >= --substantive of the smaller polity
                   must appear in DECIDED_OVERLAPS with its class. A new one is a real
                   finding -- either a mis-binding of a whole territory (the class
                   `validate_shared_polygons` catches only when the polygon is literally
                   shared) or a new coding of contested ground that needs a decision.
                   Bidirectional: an entry that stops overlapping substantially in every
                   checked year is reported too, so a resolved pair cannot leave a pin
                   behind that quietly protects nothing.
  B  LARGE SLIVER  a sub-threshold pair above --max-sliver km2 must be pinned with its
                   measured size (+-5%). Five exist, and pinning the SIZE rather than
                   just the name is what makes a border drifting further apart visible.
  C  TAIL BUDGET   the total of every remaining sliver pair, per checked year, must not
                   exceed its pinned budget. This is the "tolerance for the long tail"
                   issue 143 asked for, and it is a BUDGET rather than a per-pair
                   tolerance on purpose: ~180 pairs of 0.006% each are individually
                   uninteresting and collectively 5,000 km2 that a consumer double-counts.

WHY YEARS >= 1990 ONLY. The checked years are 1990, 2000, 2010, 2015 and 2020. Earlier
slices are dominated by the class-2 convention at colonial scale -- measured, 1925 has 50
substantial pairs totalling 11.46 Mha (`AOF`/`MLI`, `AEF`/`TCD`, `ALK`/`USA` and so on),
every one of them the gross-polygon decision working as decided -- and enumerating 50
federation/member pairs per year here would restate `validate_spatial_containment.py`'s
container list in a second place, where it would rot. The consequence is a real gap and it
is named rather than hidden: a NEW pre-1990 whole-territory mis-binding is not caught by
this gate. It is caught by `validate_shared_polygons` if the polygon is shared, by
`validate_composition_sums` if the pair sits inside a documented federation, and by
`validate_polygons` if the area is recorded.

WHAT IS NOT ASSERTED. That no cell over-claims. It still does, by 30.73 Mha, and the
first acceptance criterion of eduaguilera/whep#514 is not satisfiable until class 1 is
decided. What is asserted is that the part of the over-claim which is nobody's decision
cannot grow silently, and that the part which IS a decision is enumerated with its class.

Usage:
  python3 scripts/validate_coexisting_overlaps.py [--substantive 0.10] [--max-sliver 2000]
"""
import argparse
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(REPO, "data/final/polities_database.csv")
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")
EQUAL_AREA = "ESRI:54034"
DEAD_STATUS = ("retired", "superseded")
MIN_OVERLAP_KM2 = 1.0

# ENCLAVE PAIRS THAT COEXIST BEFORE 1990 (issue 197). The YEARS grid below starts at 1990
# for the reason in the docstring, which leaves three named double claims unwatched: a
# national row spanning an enclave's absorption date overlaps that enclave for part of its
# span, and all three windows closed before 1990.
#
# Measured 2026-08-18 in ESRI:54034, each at a year inside the overlap:
#
#     IND-1949-2025 / PTIND-1816-1961   3,719.08 km2   98% of Portuguese India
#     IND-1949-2025 / FRIN-1816-1954      520.25 km2   95% of French India
#     ITA-1919-2025 / VAT-1929-2025         0.53 km2  100% of the Holy See
#
# These are pinned as CEILINGS, not classified and not decided. Issue 197 asks whether to
# split the national rows at the absorption dates, subtract the enclaves, or record the
# overlap as intended, and that is a periodisation judgement about live national rows. What
# this arm does is make sure the ground does not grow while it is open.
#
# ITA-1919-2025 / SMR-1800-2025 is deliberately NOT here. The issue lists San Marino at
# "~61 km2", which is the country's own area; the actual intersection is 8.60 km2, 14% of
# it, so Italy's polygon already excludes 86% of San Marino and what remains is border
# imprecision of the same size as the sliver tail this gate budgets. Adding it would spend a
# ceiling on vintage noise.
ENCLAVE_PINS = {
    ("IND-1949-2025", "PTIND-1816-1961", 1955): 3719.08,
    ("IND-1949-2025", "FRIN-1816-1954", 1950): 520.25,
    ("ITA-1919-2025", "VAT-1929-2025", 1950): 0.53,
}
ENCLAVE_TOLERANCE = 0.02      # 2%: simplification and CRS noise, not a territorial change


# The years measured. Modern slices only, for the reason in the docstring. 2015 is the
# year issue 143 and eduaguilera/whep#514 both measured, so it is kept even though 2010
# and 2020 bracket it; 2025 is deliberately absent because `end_year` is EXCLUSIVE and
# every open-ended row ends AT 2025, so the 2025 slice is empty and would pin nothing.
YEARS = (1990, 2000, 2010, 2015, 2020)

# Signal A. Every coexisting pair overlapping >= 10% of the smaller polity, in at least
# one checked year, with the class it belongs to. Measured 2026-08-17 against
# data/final/polities_database.gpkg. `disputed` and `occupation` are class 1 of issue 143
# and are OPEN -- listed here so the gate can stay quiet about them without pretending
# they are resolved. `nested` is class 2, decided in wiki/log.md under
# `decision-nested-subpolity-polygons-are-gross`: the parent's polygon is gross of its
# sub-polities, so the overlap is the convention rather than a defect.
DECIDED_OVERLAPS = {
    # ---- class 1, disputed sovereignty: UNDECIDED, see wiki/log.md and issue 143 ----
    # 267,078 km2, 99.8% of Western Sahara. Both rows live, both polygons the same ground:
    # this database codes the claimant as well as the de facto controller where CShapes
    # codes only the controller. 81% of the whole residual on its own.
    ("ESH-1975-2025", "MAR-1979-2025"): "disputed",
    # 6,150 km2, 99.1% of Palestine. Same shape of problem, different territory.
    ("ISR-1979-2025", "PSE-1948-2025"): "disputed",
    # 14,951 km2, 99.8% of Timor-Leste, and only in the 1990/1995 slices: TLS-1800-2025
    # runs through the Indonesian annexation, which IDN-1976-2002 also covers. An
    # occupation coded from both sides, so class 1 rather than class 2.
    ("IDN-1976-2002", "TLS-1800-2025"): "occupation",
    # ---- class 2, nested sub-polity: DECIDED, polygons are gross ----
    # 7,027 km2, 93.2% of the Canaries, inside Spain's polygon.
    ("ESP-1800-2025", "ICN-1800-2025"): "nested",
    # 893 km2, 79.2% of Hong Kong, inside China's.
    ("CHN-1950-2025", "HKG-1842-2025"): "nested",
    # 6 km2, 19.2% of Macau, inside China's. Small in area, large in share, which is why
    # the threshold is a share and not a size.
    ("CHN-1950-2025", "MAC-1800-2025"): "nested",
    # 9 km2, 14.1% of San Marino. The enclave case: Italy's polygon does not cut San
    # Marino out cleanly at source resolution. Reported as nested because the convention
    # is the same -- the container's polygon includes ground the enclave also claims.
    ("ITA-1919-2025", "SMR-1800-2025"): "nested",
    # ---- class 2 in the 1990 slice only: the USSR and the Pacific trust territory ----
    # F228-1945-1991 is the Soviet Union; its polygon is gross of the republics that are
    # rows in their own right. 86,011 km2 (Azerbaijan SSR), 65,965 (Latvia), 55,886
    # (Lithuania), 49,289 (Estonia), each 100.0% of the republic.
    ("AZE-SSR-1920-1991", "F228-1945-1991"): "nested",
    ("F228-1945-1991", "LVA-1940-1991"): "nested",
    ("F228-1945-1991", "LTU-1940-1991"): "nested",
    ("EST-1940-1991", "F228-1945-1991"): "nested",
    # TTPI-1947-1994 is the Trust Territory of the Pacific Islands, gross of the entities
    # that emerged from it: 503 km2 (99.9% of the Northern Marianas), 257 km2 (85.6% of
    # the Marshall Islands).
    ("MNP-1986-2025", "TTPI-1947-1994"): "nested",
    ("MHL-1874-2025", "TTPI-1947-1994"): "nested",
}

# Signal B. Sliver pairs above --max-sliver km2, with the size measured 2026-08-17. Each
# is below the 10% share threshold, so none of them is a territory coded twice; they are
# two polygon sources disagreeing about where one border runs. Pinned by SIZE so that a
# rebinding which moves a border further apart is reported even though the pair is already
# known.
LARGE_SLIVERS = {
    # 6.58% of Yemen. Its own class in issue 143's accounting and still open: the
    # Saudi-Yemen frontier through the Rub al Khali was undefined until the 2000 Treaty of
    # Jeddah, and the two sources simply place it differently. Needs a source decision,
    # not a tolerance -- but its SIZE is pinned here so it cannot drift unnoticed.
    ("SAU-1924-2025", "YEM-1990-2025"): 29828.3,
    # 1.07% of Thailand -- the largest genuine resolution artefact in the set, and the
    # number that sets the top of class 3.
    ("MMR-1885-2025", "THA-1909-2025"): 5458.7,
    # 0.72% of Myanmar, along the Chinese border.
    ("CHN-1950-2025", "MMR-1885-2025"): 4845.5,
    # 1.70% and 1.57% of Nepal: the Himalayan border drawn from two sources.
    ("IND-1949-2025", "NPL-1816-2025"): 2529.3,
    ("CHN-1950-2025", "NPL-1816-2025"): 2332.8,
}
SLIVER_PIN_TOLERANCE = 0.05

# Signal C. The total of every sliver pair NOT in LARGE_SLIVERS, per year, in km2,
# measured 2026-08-17. Around 150-180 pairs per year, each a few km2 to a few hundred, and
# collectively the part of the cell over-claim that is nobody's decision.
#
# BIDIRECTIONAL, like every baseline here. Growth above 1% fails: adding a polity whose
# polygon disagrees with its neighbours' is legitimate work, and the pin's job is to make
# that show up as a number to re-record rather than as nothing at all. Falling more than
# 10% below fails too, because a tail that has been reduced must be re-pinned at its new
# size or the gate goes on protecting territory that is no longer there.
TAIL_BUDGET_KM2 = {
    1990: 4870.3,
    2000: 5105.0,
    2010: 5134.7,
    2015: 5160.5,
    2020: 5160.5,
}
TAIL_GROWTH_TOLERANCE = 0.01
TAIL_SHRINK_TOLERANCE = 0.10


def read_live() -> dict:
    """Live REAL polities and their spans. Aggregates are excluded because an aggregate's
    polygon is a union of its members BY DEFINITION -- reporting it as an overlap would be
    reporting the definition. Retired and superseded rows are excluded because they can
    never receive data, so ground they claim is claimed by nobody."""
    live = {}
    with open(CSV, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if (r.get("wiki_status") or "") in DEAD_STATUS:
                continue
            if (r.get("polity_type") or "") == "aggregate":
                continue
            try:
                live[r["polity_code"]] = (int(r["start_year"]), int(r["end_year"]))
            except (TypeError, ValueError):
                continue
    return live


def all_codes() -> set:
    with open(CSV, encoding="utf-8") as fh:
        return {r["polity_code"] for r in csv.DictReader(fh)}


def overlaps_by_year(live: dict) -> dict:
    """{year: [(km2, code_a, code_b, share_of_smaller), ...]} for every coexisting pair
    overlapping more than MIN_OVERLAP_KM2, measured in an equal-area projection.

    buffer(0) heals self-intersections before any area is taken, as in
    validate_spatial_containment and validate_shared_polygons: on an invalid ring
    `.area` is not trustworthy and the whole gate is areas."""
    import geopandas as gpd

    g = gpd.read_file(GPKG)
    g = g[~g.geometry.isna() & ~g.geometry.is_empty]
    g = g[g.polity_code.isin(live)].to_crs(EQUAL_AREA).copy()
    g["geometry"] = g.geometry.buffer(0)

    out = {}
    for year in YEARS:
        sel = g[[live[c][0] <= year < live[c][1] for c in g.polity_code]]
        geo = dict(zip(sel.polity_code, sel.geometry))
        area = {c: v.area / 1e6 for c, v in geo.items()}
        hits = gpd.sjoin(
            sel[["polity_code", "geometry"]],
            sel[["polity_code", "geometry"]],
            how="inner",
            predicate="intersects",
        )
        found = []
        seen = set()
        for a, b in zip(hits.polity_code_left, hits.polity_code_right):
            if a >= b or (a, b) in seen:
                continue
            seen.add((a, b))
            km2 = geo[a].intersection(geo[b]).area / 1e6
            if km2 <= MIN_OVERLAP_KM2:
                continue
            smaller = min(area[a], area[b])
            found.append((km2, a, b, km2 / smaller if smaller > 0 else 1.0))
        found.sort(reverse=True)
        out[year] = found
    return out


def enclave_pin_problems(live: dict) -> list:
    """Check the pre-1990 enclave pairs pinned for issue 197, at the year each is pinned at.

    Independent of the YEARS grid on purpose: adding a pre-1990 slice there would pull in the
    whole colonial-era gross-polygon class (the 1925 slice alone has 50 substantial pairs over
    11.46 Mha), which needs the convention decision this gate deliberately does not make.
    Same CRS and the same buffer(0) as overlaps_by_year, so the numbers are comparable.
    """
    import geopandas as gpd

    out = []
    g = gpd.read_file(GPKG)
    g = g[~g.geometry.isna() & ~g.geometry.is_empty].to_crs(EQUAL_AREA).copy()
    g["geometry"] = g.geometry.buffer(0)
    geo = dict(zip(g.polity_code, g.geometry))
    for (outer, inner, year), pinned in sorted(ENCLAVE_PINS.items()):
        for code in (outer, inner):
            if code not in geo:
                out.append(
                    f"ENCLAVE PIN {outer} / {inner} cannot be measured: {code} carries no "
                    f"geometry. If the row was re-spanned or retired, update the pin"
                )
                break
        else:
            for code in (outer, inner):
                s, e = live.get(code, (None, None))
                if s is None or not (s <= year < e):
                    out.append(
                        f"ENCLAVE PIN {outer} / {inner} is pinned at {year}, which is outside "
                        f"{code}'s span {s}-{e} — issue 197's window moved, so re-measure and "
                        f"re-pin rather than deleting"
                    )
                    break
            else:
                km2 = geo[outer].intersection(geo[inner]).area / 1e6
                drift = abs(km2 - pinned) / pinned if pinned > 0 else 0.0
                print(f"   enclave pin {outer} / {inner} @{year}: {km2:,.2f} km2 "
                      f"(pinned {pinned:,.2f}, {drift:+.1%})")
                if drift > ENCLAVE_TOLERANCE:
                    out.append(
                        f"ENCLAVE PIN {outer} / {inner} @{year} now measures {km2:,.2f} km2 "
                        f"against a pinned {pinned:,.2f} ({drift:.1%} drift, tolerance "
                        f"{ENCLAVE_TOLERANCE:.0%}). A national row's overlap with an enclave it "
                        f"later absorbed has CHANGED — either a polygon moved or the row was "
                        f"re-spanned. Issue 197 decides what to do about the overlap; this only "
                        f"says it must not drift while that is open"
                    )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--substantive",
        type=float,
        default=0.10,
        help="share of the SMALLER polity above which an overlap must be named and classified",
    )
    ap.add_argument(
        "--max-sliver",
        type=float,
        default=2000.0,
        help="a sub-threshold pair above this many km2 must be pinned by size",
    )
    args = ap.parse_args()

    if not os.path.exists(GPKG):
        print(f"FAIL: {GPKG} is missing, so no overlap can be measured")
        return 1
    try:
        import geopandas  # noqa: F401
    except ImportError as exc:
        print(f"SKIP: geopandas unavailable ({exc}); signal A/B/C need geometry")
        return 0

    live = read_live()
    per_year = overlaps_by_year(live)
    codes = all_codes()
    problems = []

    # Every pinned pair must still refer to rows that exist, so a pin cannot go inert by
    # naming a row that was renamed away.
    for pair in list(DECIDED_OVERLAPS) + list(LARGE_SLIVERS):
        for code in pair:
            if code not in codes:
                problems.append(
                    f"PIN NAMES A MISSING ROW {code} (in pin {pair[0]} / {pair[1]}) — the "
                    f"row was renamed or removed, so the pin protects nothing; update it"
                )

    seen_substantial = set()
    seen_large_sliver = {}

    for year in YEARS:
        pairs = per_year[year]
        substantial = [p for p in pairs if p[3] >= args.substantive]
        slivers = [p for p in pairs if p[3] < args.substantive]
        big = [p for p in slivers if (p[1], p[2]) in LARGE_SLIVERS]
        tail = [p for p in slivers if (p[1], p[2]) not in LARGE_SLIVERS]
        tail_total = sum(p[0] for p in tail)

        print(
            f"{year}: {len(pairs)} coexisting pair(s) overlapping >{MIN_OVERLAP_KM2:g} km2, "
            f"{sum(p[0] for p in pairs):,.0f} km2 total — {len(substantial)} substantial, "
            f"{len(big)} pinned sliver(s), {len(tail)} tail pair(s) {tail_total:,.1f} km2"
        )

        for km2, a, b, share in substantial:
            key = (a, b)
            seen_substantial.add(key)
            cls = DECIDED_OVERLAPS.get(key)
            if cls is None:
                problems.append(
                    f"UNCLASSIFIED SUBSTANTIAL OVERLAP {a} / {b} at {year}: {km2:,.0f} km2, "
                    f"{share:.1%} of the smaller — two coexisting live rows claim the same "
                    f"territory. Either one is bound to the wrong polygon, or this is "
                    f"contested ground that needs a class in DECIDED_OVERLAPS "
                    f"(disputed / occupation / nested; see wiki/log.md "
                    f"`decision-nested-subpolity-polygons-are-gross`)"
                )
            else:
                print(f"  {cls.upper():10} {a} / {b}: {km2:,.0f} km2, {share:.1%} of the smaller")

        for km2, a, b, share in slivers:
            key = (a, b)
            if key in LARGE_SLIVERS:
                pin = LARGE_SLIVERS[key]
                seen_large_sliver[key] = max(seen_large_sliver.get(key, 0.0), km2)
                if abs(km2 - pin) > pin * SLIVER_PIN_TOLERANCE:
                    problems.append(
                        f"PINNED SLIVER MOVED {a} / {b} at {year}: {km2:,.1f} km2 against a "
                        f"pin of {pin:,.1f} km2 ({(km2 / pin - 1):+.1%}, tolerance "
                        f"{SLIVER_PIN_TOLERANCE:.0%}) — the two sources now place this border "
                        f"differently; re-measure and re-pin"
                    )
            elif km2 > args.max_sliver:
                problems.append(
                    f"NEW LARGE SLIVER {a} / {b} at {year}: {km2:,.1f} km2, {share:.2%} of the "
                    f"smaller — below the substantial-overlap share, so it is a border "
                    f"disagreement rather than a doubled territory, but larger than "
                    f"{args.max_sliver:,.0f} km2; pin it in LARGE_SLIVERS with its measured size"
                )

        budget = TAIL_BUDGET_KM2.get(year)
        if budget is None:
            problems.append(
                f"NO TAIL BUDGET for {year}, which YEARS asks to be checked — add the measured "
                f"total {tail_total:,.1f} km2 to TAIL_BUDGET_KM2"
            )
            continue
        if tail_total > budget * (1 + TAIL_GROWTH_TOLERANCE):
            worst = ", ".join(f"{a}/{b} {km2:,.0f}" for km2, a, b, _s in tail[:5])
            problems.append(
                f"TAIL GREW at {year}: {tail_total:,.1f} km2 across {len(tail)} pair(s) against "
                f"a budget of {budget:,.1f} km2 ({(tail_total / budget - 1):+.1%}, tolerance "
                f"{TAIL_GROWTH_TOLERANCE:.0%}) — more ground is claimed twice than when this "
                f"was pinned. Largest: {worst}. If the growth is a polity legitimately added, "
                f"re-pin TAIL_BUDGET_KM2[{year}] at the measured total and say so"
            )
        elif tail_total < budget * (1 - TAIL_SHRINK_TOLERANCE):
            problems.append(
                f"TAIL SHRANK at {year}: {tail_total:,.1f} km2 against a budget of "
                f"{budget:,.1f} km2 ({(tail_total / budget - 1):+.1%}) — the double-claimed "
                f"ground was reduced, which is the outcome this pin exists to protect. Re-pin "
                f"TAIL_BUDGET_KM2[{year}] at the new total so the gate guards the improvement"
            )

    # Bidirectional: a pin that no longer describes anything.
    for pair, cls in sorted(DECIDED_OVERLAPS.items()):
        if pair not in seen_substantial:
            problems.append(
                f"STALE PIN {pair[0]} / {pair[1]} is recorded as {cls} but overlaps below "
                f"{args.substantive:.0%} of the smaller in every checked year — if the overlap "
                f"was resolved, delete the entry and record what changed"
            )
    for pair in sorted(LARGE_SLIVERS):
        if pair not in seen_large_sliver:
            problems.append(
                f"STALE SLIVER PIN {pair[0]} / {pair[1]} no longer overlaps above "
                f"{MIN_OVERLAP_KM2:g} km2 as a sliver in any checked year — delete the entry "
                f"and record what changed"
            )

    problems.extend(enclave_pin_problems(live))

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(
        f"\nPASS: {len(DECIDED_OVERLAPS)} substantial overlap(s) classified, "
        f"{len(LARGE_SLIVERS)} sliver(s) pinned by size, {len(ENCLAVE_PINS)} pre-1990 "
        f"enclave pin(s) steady, tail within budget in all {len(YEARS)} checked year(s)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
