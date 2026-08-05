#!/usr/bin/env python3
"""Compare each polygon against the area the SOURCE stated for that reporting unit.

Every other area check in this repo compares our polygon to another GIS product, or to a
family median. Both can be consistently wrong in the same direction, because GIS products share
conventions. This one compares against `data/final/source_stated_areas.csv` -- 2,002 statements
from six IIA yearbook editions (1909-1938) in which each reporting unit is given its own area in
km2 by the statistical authority that published the data.

WHY THAT IS A DIFFERENT QUESTION. Polities exist to carry data rows, so the territorial basis
that matters is the one the source used. Issue 159 asks whether polygons should follow CLAIMED
territory (CShapes) or EFFECTIVE CONTROL (Cliopatria, paine-2024) -- a question with no answer
in the abstract, and 29 families where the two conventions meet and publish the difference as a
territorial event. The source's own figure decides it, per row, with evidence.

Tunisia is the case that made this worth building:

    IIA stated                    125,130 km2      six editions 1911-1937, unchanged
    TUN-1800-1881  paine-2024      43,752 km2      0.35x
    TUN-1881-2025  cshapes-2.0    155,482 km2      1.24x

Both wrong, in opposite directions, and the 3.55x step between them at 1881 is entirely the two
conventions meeting -- the stated area does not move across the protectorate boundary, because
the territory did not.

WHAT THIS CHECK IS NOT FOR. The yearbooks are not more accurate than modern GIS about
coastlines, and they carry their own errors: IIA gives Monaco as 21 km2 in five editions and 149
in two, against an actual ~2 km2. What a stated area IS authoritative about is SCOPE -- whether
the Sahara was in Tunisia, whether Patagonia was in Chile -- which is exactly what a per-km2
denominator has to match. So the threshold is deliberately loose (25%): this is a scope
detector, not a precision check. `validate_polygons` owns precision.

On the first run, of 228 (polity, year) pairs that resolve to a stated area:

    within 10%                                 177
    within 25%                                 210
    polygon more than 25% LARGER than stated     0
    polygon more than 25% SMALLER than stated   18

Zero overstatements is itself worth recording: whatever else is wrong with these polygons, they
are not systematically bigger than the territories the sources were describing.

Comparison is against the RANGE of everything the source ever stated for a polity, not a single
figure, because the source revises itself: 61 of 159 repeated (label, year) pairs disagree across
editions, up to 5.45x. See the comment in main().

Bidirectional: a new divergence fails, and a baselined one that comes back inside the range must
be removed.
"""
from __future__ import annotations

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATED_PATH = os.path.join(REPO, "data/final/source_stated_areas.csv")
GPKG_PATH = os.path.join(REPO, "data/final/polities_database.gpkg")
CSV_PATH = os.path.join(REPO, "data/final/polities_database.csv")

TOLERANCE = 0.25  # scope detector, not a precision check

# (polity_code, source) -> why the polygon and the stated area disagree by more than 25%.
# Being here means the divergence is understood, NOT that it is acceptable.
BASELINE = {
    ("MCO-1800-2025", "iia"):
        "THE SOURCE IS WRONG, not the polygon. IIA states 21 km2 in five editions and 149 in "
        "two others for a territory that has never exceeded ~2 km2. Monaco is the control case "
        "for this whole check: a stated area can be a transcription or unit error, so a "
        "divergence is a question rather than a verdict.",
    ("PRY-1870-1932", "iia"):
        "IIA states 450,000 km2 for 1913 against our 293,549 (0.65x). Modern Paraguay is "
        "406,752, so OUR POLYGON IS 28% BELOW even the present-day country, which makes this "
        "ours rather than the source's. Pre-Chaco-War Paraguay also claimed territory it did "
        "not hold, so part of the gap is the claimed-versus-controlled question of issue 159. "
        "Tracked with the long-single-vintage rows in issue 22, which names Paraguay.",
    ("PRY-1932-1938", "iia"):
        "same polygon as PRY-1870-1932 (293,549) against a stated 457,872 for 1932/1933/1937. "
        "The Chaco War is fought across this row's span, so the stated figure is a claim under "
        "active dispute -- but the polygon does not move at all, which is the issue 22 problem.",
}


def main() -> int:
    for path in (STATED_PATH, CSV_PATH, GPKG_PATH):
        if not os.path.exists(path):
            print(f"SKIP: {os.path.relpath(path, REPO)} missing")
            return 0
    try:
        import geopandas as gpd
    except ImportError:
        print("SKIP: geopandas unavailable")
        return 0
    sys.path.insert(0, os.path.join(REPO, "pipelines/polity-autoimprove"))
    try:
        import matchlib
    except ImportError:
        print("SKIP: matchlib unavailable")
        return 0

    import warnings
    warnings.filterwarnings("ignore")

    frame = gpd.read_file(GPKG_PATH)
    frame = frame[frame.geometry.notna() & ~frame.geometry.is_empty].to_crs("ESRI:54034")
    ours = {r["polity_code"]: r.geometry.area / 1e6 for _, r in frame.iterrows()}

    matcher = matchlib.Matcher(
        CSV_PATH,
        os.path.join(REPO, "pipelines/polity-autoimprove/state/applied_aliases.csv"),
        verbose=False,
    )

    with open(STATED_PATH, encoding="utf-8") as fh:
        statements = list(csv.DictReader(fh))

    # COMPARE AGAINST THE RANGE OF STATED AREAS, NOT A SINGLE FIGURE.
    #
    # The first version of this gate took the most divergent single statement per polity and
    # failed on it. That was wrong, and measuring showed why: THE SOURCE DISAGREES WITH ITSELF.
    # Of 159 (label, data_year) pairs stated in more than one IIA edition, 61 -- 38% -- give
    # different areas for the SAME data year, 11 of them by over 25%:
    #
    #     cote des somalis  1913     22,000 -> 120,000   5.45x
    #     inde britannique  1911  2,012,967 -> 4,659,226 2.31x
    #     equateur          1913    307,243 ->   451,180 1.47x
    #     mozambique        1913    760,014 -> 1,105,475 1.45x
    #     bolivie           1913  1,332,808 -> 1,834,225 1.38x
    #
    # These are not territorial changes -- Mozambique's borders were settled in 1891 and the
    # 1929 edition simply revised a bad earlier survey downward by 335,000 km2. So "what the
    # source thought the territory was" depends on WHICH EDITION you read, not only on which
    # year it describes. A gate that picks one statement picks an edition, arbitrarily.
    #
    # So a polygon is only flagged when it falls outside the FULL RANGE of what any edition
    # ever stated for that polity, by more than the tolerance. That is the claim worth making:
    # not "our polygon disagrees with the source" but "our polygon disagrees with EVERY figure
    # the source ever published". Mozambique passes on this logic and should -- 786,369 sits
    # inside 760,014-1,108,875, agreeing with the four later editions and not the two earlier.
    pairs, span = {}, {}
    for row in statements:
        try:
            year = int(row["data_year"])
            stated = float(row["stated_area_km2"])
        except (KeyError, TypeError, ValueError):
            continue
        try:
            code = matcher.assign(row["label"], None, row["source"], year)[0]
        except Exception:
            code = None
        if not code or code not in ours or stated <= 0:
            continue
        pairs[(code, row["source"], year)] = ours[code] / stated
        key = (code, row["source"])
        lo, hi, ev = span.get(key, (stated, stated, []))
        span[key] = (min(lo, stated), max(hi, stated), ev + [(year, stated, row["label"])])

    worst = {}
    for key, (lo, hi, ev) in span.items():
        mine = ours[key[0]]
        if mine < lo * (1 - TOLERANCE):
            worst[key] = (mine / lo, lo, hi, mine, ev)
        elif mine > hi * (1 + TOLERANCE):
            worst[key] = (mine / hi, lo, hi, mine, ev)

    diverged = worst

    problems = []
    for key in sorted(diverged):
        if key in BASELINE:
            continue
        ratio, lo, hi, mine, ev = diverged[key]
        rng = f"{lo:,.0f}" if lo == hi else f"{lo:,.0f}-{hi:,.0f}"
        problems.append(
            f"{key[0]} polygon {mine:,.0f} km2 is outside EVERY area {key[1]} states for it "
            f"({rng} km2 across {len(ev)} statement(s), {ratio:.2f}x the nearest)"
        )
    for key in sorted(set(BASELINE) - set(diverged)):
        if key[0] in ours:
            problems.append(
                f"{key[0]} / {key[1]} is baselined as diverging but is now within "
                f"{TOLERANCE:.0%} -- remove its entry"
            )

    within10 = sum(1 for r in pairs.values() if abs(r - 1) <= 0.10)
    print(f"stated-area statements: {len(statements):,}")
    print(f"(polity, source, year) pairs resolved: {len(pairs)}   polities: {len({k[0] for k in pairs})}")
    print(f"  within 10%: {within10}   within {TOLERANCE:.0%}: "
          f"{sum(1 for r in pairs.values() if abs(r - 1) <= TOLERANCE)}")
    print(f"  polygon >{TOLERANCE:.0%} LARGER than stated:  {sum(1 for r in pairs.values() if r > 1 + TOLERANCE)}")
    print(f"  polygon >{TOLERANCE:.0%} SMALLER than stated: {sum(1 for r in pairs.values() if r < 1 - TOLERANCE)}")
    revised = 0
    for key, (lo, hi, ev) in span.items():
        byyear = {}
        for year, stated, _ in ev:
            byyear.setdefault(year, set()).add(round(stated))
        if any(len(v) > 1 for v in byyear.values()):
            revised += 1
    print(f"  polities whose stated area is REVISED between editions for one data year: {revised}")
    print(f"  polities outside every stated figure: {len(diverged)} ({len(BASELINE)} baselined)")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        print(
            "\n  A stated area is evidence about SCOPE -- what the publisher counted as inside\n"
            "  the territory -- which is what a per-km2 denominator must match. Check which side\n"
            "  is wrong before changing anything: IIA states Monaco as 21 km2, so the source can\n"
            "  be the error. If the divergence is real and understood, baseline it with the\n"
            "  reason; if the polygon is wrong, fix the polygon."
        )
        return 1

    print("\nPASS: every polygon agrees with its source's stated area, or diverges for a recorded reason")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
