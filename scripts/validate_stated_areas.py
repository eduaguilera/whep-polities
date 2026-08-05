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

Tunisia is the case that made this worth building, AND THE CASE THAT SHOWS WHY ONE SOURCE IS NOT
ENOUGH. On IIA alone the reading was "both polygons are wrong":

    IIA stated                    125,130 km2      six editions 1911-1937, unchanged
    TUN-1800-1881  paine-2024      43,752 km2      0.35x of IIA
    TUN-1881-2025  cshapes-2.0    155,482 km2      1.24x of IIA

Adding FAO reversed half of that conclusion. FAO states 155,830 km2, which matches CShapes to
0.2%, and across every polity where both sources speak they agree closely -- Chile 741,770 vs
741,767, Libya 1,759,500 vs 1,759,540, Yugoslavia 1.03x, French Togoland 1.06x. Tunisia is the
ONLY 20%+ disagreement between them.

So TUN-1881-2025 is right and IIA is the outlier; only paine-2024's 43,752 is wrong. The 3.55x
step at 1881 is still an artifact, but of ONE bad polygon rather than of two conventions meeting.
Two sources agreeing to four digits while a third differs by a quarter is how you tell an outlier
from a convention -- and with IIA alone I drew the wrong conclusion and wrote it into a merged PR.

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
    # MCO-1800-2025 was baselined here and the gate REMOVED IT, which is the design working.
    # IIA states Monaco as 21 km2 in seven editions and 149 in two, for a territory that has
    # never exceeded ~2 -- and FAO states the correct 2. Once each source got ONE VOTE instead of
    # one per edition, FAO's value survived, the accepted band became 2-21, and our 2 km2 polygon
    # stopped diverging. Keep the reasoning: Monaco is the control case for this whole check.
    # A stated area can be a transcription or unit error, so a divergence is a question, not a
    # verdict -- and a majority of editions agreeing proves nothing, because yearbooks reprint
    # each other's area tables.
    ("PRY-1870-1932", "iia"):
        "IIA states 450,000 km2 for 1913 against our 293,549 (0.65x). Modern Paraguay is "
        "406,752, so OUR POLYGON IS 28% BELOW even the present-day country, which makes this "
        "ours rather than the source's. Pre-Chaco-War Paraguay also claimed territory it did "
        "not hold, so part of the gap is the claimed-versus-controlled question of issue 159. "
        "Tracked with the long-single-vintage rows in issue 22, which names Paraguay.",
    # --- FAO additions, 2026-08-05. Each says WHICH SIDE is wrong, because the answer differs.
    ("F249-1918-1990", "fao"):
        "SCOPE MISMATCH, not an error. FAO's `Yemen` for 1947 is 195,000 km2 -- NORTH Yemen "
        "alone -- while F249-1918-1990 is the combined YAR + PDR reporting unit at 423,668. The "
        "routing question (should a pre-1990 `Yemen` label reach the combined row or a "
        "North-Yemen one?) is the pre-1990 Yemen gap already known from the production/trade "
        "review; it is not answerable by area.",
    ("RYU-1945-1972", "fao"):
        "SCOPE MISMATCH, explained. FAO states 3,410 km2 against our 2,270. The US-administered "
        "Ryukyus included Amami Oshima (~1,200 km2) until it returned to Japan in 1953, and "
        "2,270 + 1,200 = 3,470, within 2% of the stated figure. Our polygon is Okinawa "
        "Prefecture, so the gap is Amami and the divergence is real rather than wrong.",
    ("SAU-1924-2025", "fao"):
        "GENUINE HISTORICAL UNCERTAINTY. FAO states 1,546,000 km2 against our 1,954,454 and a "
        "modern 2,149,690. Saudi Arabia's southern and eastern desert boundaries were not "
        "settled until the 1990s, so contemporary figures varied by hundreds of thousands of "
        "km2. Neither side is wrong; the territory was not agreed.",
    ("QAT-1800-2025", "fao"):
        "GENUINE HISTORICAL UNCERTAINTY, same shape. FAO states 22,000 km2 against our 11,062 "
        "and a modern 11,586. Pre-settlement figures for Qatar commonly included disputed zones.",
    ("VNM-1887-1954", "fao"):
        "OUR POLYGON IS CORROBORATED BY THE OTHER SOURCE, so FAO is the narrow one here. FAO "
        "states 225,000 km2 for `Indochina Viet Nam` in 1951 against our 324,094. But IIA lists "
        "the three constituent protectorates separately -- Tonkin 115,700 + Annam 147,600 + "
        "Cochinchine 64,700 = 328,000 -- which is within 1.2% of our polygon. 1951 sits in the "
        "middle of the First Indochina War, with the State of Vietnam administering part of the "
        "territory and the Viet Minh the rest, so a survey covering 225,000 km2 is plausible as "
        "the area actually enumerated. Cross-checking two sources is what makes this readable as "
        "a coverage difference rather than a polygon error.",
    ("SLV-1821-2025", "fao"):
        "EXTRACTION DAMAGE, visible in the label itself: the row is `EI Salvador`, an OCR misread "
        "of `El`. The stated 34,130 km2 is 62% above El Salvador's 21,041, so the number is as "
        "suspect as the name. Belongs to the digitisation review, not to this repo.",
    ("JAM-1800-2025", "fao"):
        "THE LABEL IS NOT THE POLITY. `British West Indies Jamaica` states 1,420 km2 against "
        "Jamaica's 10,991, and IIA's equivalent sub-label states 231-271 km2 -- BOTH sources "
        "give a small figure, so this is a sub-unit inside a BWI section rather than the island. "
        "The alias routing it to JAM-1800-2025 is what needs revisiting, not the polygon.",
    ("NFK-1914-2025", "fao"):
        "A UNIT ERROR IN THE SOURCE. FAO states 350 km2 for Norfolk Island, which is 35 km2 -- "
        "exactly 10x, i.e. a figure in km2 recorded under the `1000 hectares` heading. Our 37 is "
        "right.",
    ("SMR-1800-2025", "fao"):
        "ROUNDING AT LOW MAGNITUDE. FAO's smallest unit is 1,000 hectares = 10 km2, so San "
        "Marino's 61 km2 can only be recorded as 6 or 10 -- it is recorded as 10, giving 100. "
        "Our 66 is right. Anything under a few hundred km2 cannot be checked at this resolution.",
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
    # CONSENSUS, NOT RANGE -- because the NUMBERS have OCR errors too, not just the labels.
    #
    # The first version accepted anything inside the full span of what the source ever stated.
    # That is unsafe, and Cote des Somalis shows why:
    #
    #     iia ed1909, ed1925        120,000 km2      wrong
    #     iia ed1929, 32, 33, 38     22,000 / 21,963  correct
    #     fao ed1952                 23,000          independent confirmation
    #     French Somaliland actual   ~23,200
    #
    # That is not the source revising its scope. It is a BAD NUMBER, corrected in 1929, and it
    # looks like a spurious leading digit on 20,000. Accepting the full range would let a 5x
    # wrong polygon pass for Djibouti. Monaco is the same shape (21 in five editions, 149 in two,
    # against FAO's correct 2) and so is Norfolk Island (FAO 350 against an actual 35 -- exactly
    # 10x, a figure in km2 filed under a `1000 hectares` heading).
    #
    # So: take the MEDIAN of everything stated for a polity, drop statements that sit at roughly
    # 10x or 1/10 of it -- the signature of a lost or gained digit -- and compare the polygon
    # against what survives. The dropped statements are reported separately, because a list of
    # probable digit errors is useful feedback for the digitisation pipeline rather than noise.
    #
    # Tunisia deliberately does NOT get dropped by this rule: IIA states 125,130 and FAO 155,830,
    # a 0.76x ratio that is nothing like a digit error, and IIA repeats it identically across six
    # editions, which OCR would not. That one is a definitional difference -- most likely whether
    # the southern military territories were counted -- and it should stay visible.
    import statistics

    pairs, allstated = {}, {}
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
        allstated.setdefault(code, []).append((stated, row["source"], row["edition"], row["label"]))

    # ONE VOTE PER SOURCE, NOT PER EDITION -- because editions are not independent.
    #
    # A count-based median is fooled whenever the majority is wrong, and Monaco proves it: IIA
    # states 21 km2 in seven editions and 149 in two, FAO states the correct 2. Median by count
    # is 21, so the first version of this screen discarded FAO'S CORRECT VALUE as the outlier.
    # Yearbooks reprint each other's area tables, so seven IIA editions are close to one
    # observation repeated, not seven observations agreeing.
    #
    # So: collapse each source to its own median first, then take the consensus across sources.
    # Monaco becomes IIA 21 vs FAO 2, and neither is discarded -- the band is simply wide, which
    # is the honest description of two sources disagreeing tenfold about a 2 km2 country.
    DIGIT_LO, DIGIT_HI = 7.0, 13.0  # a lost or gained decimal digit, with room for rounding
    suspect, worst = [], {}
    for code, obs in allstated.items():
        by_source = {}
        for stated, src, edition, label in obs:
            by_source.setdefault(src, []).append((stated, edition, label))
        source_value = {
            src: statistics.median(v for v, *_ in vals) for src, vals in by_source.items()
        }
        consensus = statistics.median(source_value.values())
        kept = {}
        for src, val in source_value.items():
            r = val / consensus if val > consensus else consensus / val
            # only drop a source whose whole median looks like a digit error AND where another
            # source survives to compare against -- never leave the polity with no evidence
            if DIGIT_LO <= r <= DIGIT_HI and len(source_value) > 1:
                worst_ed = max(by_source[src], key=lambda t: abs(t[0] - consensus))
                suspect.append((code, val, consensus, src, worst_ed[1], worst_ed[2]))
            else:
                kept[src] = val
        if not kept:
            continue
        lo, hi = min(kept.values()), max(kept.values())
        mine = ours[code]
        key = (code, "/".join(sorted(kept)))
        if mine < lo * (1 - TOLERANCE):
            worst[key] = (mine / lo, lo, hi, mine, list(kept.items()))
        elif mine > hi * (1 + TOLERANCE):
            worst[key] = (mine / hi, lo, hi, mine, list(kept.items()))

    diverged = worst

    problems = []
    baselined = {k[0] for k in BASELINE}
    for key in sorted(diverged):
        if key[0] in baselined:
            continue
        ratio, lo, hi, mine, ev = diverged[key]
        rng = f"{lo:,.0f}" if lo == hi else f"{lo:,.0f}-{hi:,.0f}"
        problems.append(
            f"{key[0]} polygon {mine:,.0f} km2 is outside every area {key[1]} states for it "
            f"({rng} km2 across {len(ev)} statement(s), {ratio:.2f}x the nearest)"
        )
    seen = {k[0] for k in diverged}
    for key in sorted(BASELINE):
        if key[0] in ours and key[0] not in seen:
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
    revised = sum(
        1 for obs in allstated.values() if len({round(v) for v, *_ in obs}) > 1
    )
    print(f"  polities whose stated area is REVISED between editions for one data year: {revised}")
    print(f"  polities outside every stated figure: {len(diverged)} ({len(BASELINE)} baselined)")
    if suspect:
        print(f"\n  statements dropped as probable DIGIT ERRORS (~10x the median for that polity): {len(suspect)}")
        for code, stated, med, src, edition, label in sorted(suspect)[:10]:
            print(f"    {code:18s} {src} ed{edition} states {stated:>11,.0f} vs median {med:>11,.0f}  [{label[:26]}]")

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
