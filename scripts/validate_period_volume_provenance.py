#!/usr/bin/env python3
"""Guard `period_volume_provenance.csv`: the period -> volume map is a FUNCTION, the late-volume
classification follows it, and the tobacco/hops screen stays scoped to tobacco and hops (issue 416).

WHAT THIS PROTECTS. The table's whole claim is that one period label names one yearbook volume, so
`period` can serve as the provenance column layer B lacks. If a re-extraction ever printed one period
in two volumes, every attribution in the table would silently become a guess -- so arm B re-derives
the map FROM THE TABLE and compares it to the recorded one, rather than trusting either alone.

THE SCREEN SCOPE IS THE ARM THAT MATTERS MOST (arm E). 500,000 t is implausible for tobacco against a
world total of 2-3 Mt and completely ordinary for wheat, so `implausible_tobacco_hops` must be blank
for every row outside tobacco/hops in tonnes. A screen that leaked to other items would report a
plausible-looking pile of "defects" that are simply large crops, and nothing in the row counts would
look wrong -- the count would just go up.

THE CONSTANTS ARE RESTATED, NOT IMPORTED, on purpose: an imported threshold moves with the tool that
produced the table, which is exactly what a gate must not allow.

Counts are pinned BIDIRECTIONALLY. A fall is as much a failure as a rise: the 38 unscreened
`1928-1932` rows are the recorded gap, and if that becomes 0 the era table has been widened and this
gate's arm H has to be re-recorded rather than quietly passing.
"""
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines", "polity-autoimprove", "state",
                     "period_volume_provenance.csv")

# Restated from 42_period_volume_provenance.py. Derived there from 42,587 multi-year raw rows.
PERIOD_VOLUME = {
    "1900-1913": "iia_1925_26",
    "1909-1913": "iia_1925_26",
    "1921-1925": "iia_1929_30",
    "1924-1928": "iia_1933_34",
    "1925-1929": "iia_1933_34",
    "1928-1932": "iia_1938_39",
    "1934-1938": "iia_1939_45",
}
LATE_VOLUMES = {"iia_1938_39", "iia_1939_45"}
SCREEN_ITEMS = {"tobacco, unmanufactured", "hops"}
SCREEN_UNIT = "tonnes"
SCREEN_T = 500_000.0

ROWS = 6163
LATE_ROWS = 3602
SCREENED = 341
# (period, above 500 kt, screened rows in that period). The clean volumes hold 0 and 2; both of the
# two are correct figures, so the real contrast is 0 in 145 clean against 79 in 196 late.
SCREEN_BY_PERIOD = {
    "1909-1913": (0, 55),
    "1925-1929": (2, 90),
    "1928-1932": (38, 97),
    "1934-1938": (41, 99),
}
# The two clean-volume hits are `india` and the `united states of america`, and both values are RIGHT
# -- the USA was the world's largest tobacco producer at roughly 600 kt. Pinned as an exoneration: a
# third clean-volume hit is a new finding and must not land silently, and losing these two means the
# screen or the extract moved.
CLEAN_HITS = {("india", "612500.0"), ("united states of america", "630805.5")}
# The scope gap this table exists to make countable: every implausible 1934-1938 row has an era
# verdict, and no 1928-1932 row has one at all.
ERA_COVERED_1934 = 41
ERA_GAP_1928 = 38


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"FAIL: {os.path.relpath(TABLE, REPO)} missing — "
              f"run 42_period_volume_provenance.py --write", file=sys.stderr)
        return 1
    with open(TABLE, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    problems = []

    # A. shape
    if len(rows) != ROWS:
        problems.append(f"A: {len(rows)} rows, recorded {ROWS}. A change in either direction needs "
                        f"the pins below re-recorded, not adjusted.")
    for i, r in enumerate(rows):
        if not r["period"] or not r["volume"]:
            problems.append(f"A: row {i} has an empty period or volume, so it is unattributed")
            break

    # B. the map is a function, and it is the recorded one
    seen = {}
    for r in rows:
        seen.setdefault(r["period"], set()).add(r["volume"])
    for per in sorted(seen):
        if len(seen[per]) > 1:
            problems.append(f"B: period {per} is attributed to {sorted(seen[per])} — the table's "
                            f"core claim is that one period names ONE volume, so attribution by "
                            f"period label is no longer sound")
        elif per not in PERIOD_VOLUME:
            problems.append(f"B: period {per} is not in the recorded map")
        elif PERIOD_VOLUME[per] != next(iter(seen[per])):
            problems.append(f"B: period {per} attributed to {next(iter(seen[per]))}, "
                            f"recorded {PERIOD_VOLUME[per]}")

    # C. the late flag follows the restated set, not the table's own opinion
    for r in rows:
        want = "yes" if r["volume"] in LATE_VOLUMES else "no"
        if r["volume_is_late"] != want:
            problems.append(f"C: {r['volume']} flagged volume_is_late={r['volume_is_late']}, "
                            f"the restated set says {want}")
            break

    # D. late total, bidirectional
    late = sum(1 for r in rows if r["volume_is_late"] == "yes")
    if late != LATE_ROWS:
        problems.append(f"D: {late} rows from a late volume, recorded {LATE_ROWS}")

    # E. the screen stays scoped to tobacco/hops in tonnes -- the wheat trap
    scr = [r for r in rows if r["implausible_tobacco_hops"]]
    for r in rows:
        in_scope = r["item"] in SCREEN_ITEMS and r["unit"] == SCREEN_UNIT
        has = bool(r["implausible_tobacco_hops"])
        if has and not in_scope:
            problems.append(f"E: the 500,000 t screen reached {r['item']!r} ({r['unit']}), which is "
                            f"outside tobacco/hops — 500 kt is ordinary for most crops, so this "
                            f"would publish large harvests as defects")
            break
        if in_scope and not has:
            problems.append(f"E: {r['item']!r} ({r['unit']}) is in scope but unscreened")
            break
    if len(scr) != SCREENED:
        problems.append(f"E: {len(scr)} screened rows, recorded {SCREENED}")
    for r in scr:
        want = "yes" if float(r["value"]) > SCREEN_T else "no"
        if r["implausible_tobacco_hops"] != want:
            problems.append(f"E: {r['country']}/{r['period']} value {r['value']} flagged "
                            f"{r['implausible_tobacco_hops']}, threshold says {want}")
            break

    # F. the per-period contamination table -- the evidence that the defect follows the EDITION
    for per, (want_big, want_n) in SCREEN_BY_PERIOD.items():
        d = [r for r in scr if r["period"] == per]
        big = [r for r in d if r["implausible_tobacco_hops"] == "yes"]
        if (len(big), len(d)) != (want_big, want_n):
            problems.append(f"F: {per} screens {len(big)}/{len(d)}, recorded {want_big}/{want_n}. "
                            f"This table is the evidence that a late volume, not a late YEAR, "
                            f"carries the defect — 1928-1932 is pre-1934 and printed by "
                            f"iia_1938_39.")

    # G. the clean-volume exoneration
    got = {(r["country"], r["value"]) for r in scr
           if r["implausible_tobacco_hops"] == "yes" and r["volume_is_late"] == "no"}
    if got != CLEAN_HITS:
        problems.append(f"G: clean-volume hits are {sorted(got)}, recorded {sorted(CLEAN_HITS)}. "
                        f"Both recorded values are CORRECT figures over-flagged by a crude 500 kt "
                        f"threshold; a different set is a real finding either way.")

    # H. the era-table scope gap, pinned in both directions
    p34 = [r for r in scr if r["period"] == "1934-1938" and r["implausible_tobacco_hops"] == "yes"]
    cov = sum(1 for r in p34 if r["era_screened"] == "yes")
    if cov != ERA_COVERED_1934:
        problems.append(f"H: {cov} of {len(p34)} implausible 1934-1938 rows carry an era verdict, "
                        f"recorded {ERA_COVERED_1934}")
    p28 = [r for r in scr if r["period"] == "1928-1932" and r["implausible_tobacco_hops"] == "yes"]
    gap = sum(1 for r in p28 if r["era_screened"] == "no")
    if gap != ERA_GAP_1928:
        problems.append(f"H: {gap} implausible 1928-1932 rows lack an era verdict, recorded "
                        f"{ERA_GAP_1928}. If this fell, era_shift_verdicts was widened to reach "
                        f"them and this pin must be re-recorded, not left passing.")
    if any(r["era_screened"] == "yes" for r in rows if r["period"] == "1928-1932"):
        problems.append("H: a 1928-1932 row now carries an era verdict; the era table's period "
                        "scope has changed and arm H's premise no longer holds")

    # I. cross-arm on scope: fao1952 uses the SAME `1934-1938` label, and a row of it here would be
    # attributed to an IIA volume that never printed it.
    bad_src = sorted({r["source"] for r in rows if r["source"] != "iia"})
    if bad_src:
        problems.append(f"I: non-iia sources present ({bad_src}); fao1952 shares the 1934-1938 "
                        f"period label, and the period -> volume map is an IIA fact only")

    if problems:
        print(f"FAIL {os.path.relpath(TABLE, REPO)}", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"OK period_volume_provenance.csv: {len(rows)} iia period rows, {late} from a late volume; "
          f"{len(scr)} tobacco/hops rows screened; {ERA_GAP_1928} implausible 1928-1932 rows still "
          f"carry no era verdict")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
