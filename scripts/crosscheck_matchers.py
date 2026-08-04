#!/usr/bin/env python3
"""Check this repo's two matchers against each other.

There are two independent implementations of "which polity does this source's
label mean in this year":

  pipelines/faostat-era-matching/match.R   scans the FAOSTAT pins and emits
                                           year-ranged routing aliases
  pipelines/polity-autoimprove/matchlib.py resolves labels by alias, then by
                                           ISO/name family + year containment

`matchlib.pick_by_year` carries a comment saying it was written to agree with
match.R on the shared-transition-year rule, so agreement is the intent. Nothing
verified it. Comparing them found three real defects on the first run:

  Serbia 2006-2008 exists TWICE, as SER-2006-2008 and SRB-2006-2008 (issue 43)
  "Malaysia" 1961 resolves to British North Borneo, because four same-iso3
    candidates are all typed `national` so the tie-break cannot discriminate
    (issue 44)
  "Viet Nam" 1967 routes to RVN (South Vietnam alone) by one alias and to
    F237 (combined DRV+RVN) by the other

The comparison must avoid circularity: matchlib READS the aliases match.R writes,
so asking it about a FAOSTAT label would just return match.R's own answer. This
loads matchlib with the `faostat`-sourced rules REMOVED, forcing it to resolve by
its own deterministic routes, and compares that against the published map.

Disagreements are baselined rather than asserted to zero — the three above are
real and open. A NEW one fails, and a baselined one that starts agreeing fails
too, so the list shrinks as the defects are fixed.

Usage:
  python3 scripts/crosscheck_matchers.py
"""
import csv
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipelines/polity-autoimprove"))

ALIASES = os.path.join(REPO, "pipelines/polity-autoimprove/state/applied_aliases.csv")
POLITIES = os.path.join(REPO, "data/final/polities_database.csv")
PUBLISHED = os.path.join(REPO, "data/final/faostat_area_polity_map.csv")

# Known disagreements, by FAOSTAT area code. Each is an open defect, not an
# accepted difference — see the issues named above.
BASELINE_DIFFERENT = {131, 237, 272}

# Labels matchlib cannot resolve without the faostat alias, so an explicit route is
# REQUIRED. One area, and it is genuinely nominal: the Yugoslav SFR chain sits under
# F248-*, a combined-reporting prefix, and the label "Yugoslav SFR" with iso3 YUG leads
# nowhere at all — status `unresolved`, not `year_uncovered`.
#
# This set used to be {7, 72, 248}, and the two that left are worth recording because the
# stated reason for all three was wrong. The comment claimed each was "a prefix the label
# does not lead to". For Angola and Djibouti the obstacle was TEMPORAL: both areas have two
# published mappings, the modern one resolved fine, and the COLONIAL row returned
# `year_uncovered` because the ISO code attached only to the post-independence polity.
# Correcting three `iso3` fields to name the TERRITORY rather than the era —
# ANG-1905-1975 to AGO, FRS-1884-1977 and FRS-1977-2025 to DJI, SUD-1956-2011 to SDN —
# made both colonial rows resolve, and this baseline's bidirectional arm is what reported
# it. The prefixes were never the problem and are unchanged.
#
# I also first guessed this set would be the four China components, assuming an aggregate
# with no ISO3 would be the hard case. Those resolve fine.
BASELINE_UNRESOLVED = {248}


def main() -> int:
    import matchlib

    rows = list(csv.DictReader(open(ALIASES, encoding="utf-8")))
    cols = list(rows[0].keys())
    tmp = tempfile.NamedTemporaryFile(
        "w", suffix=".csv", delete=False, newline="", encoding="utf-8"
    )
    w = csv.DictWriter(tmp, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        if r.get("source") != "faostat":
            w.writerow({c: r.get(c, "") for c in cols})
    tmp.close()

    try:
        m = matchlib.Matcher(POLITIES, applied_aliases_csv=tmp.name, verbose=False)
        published = list(csv.DictReader(open(PUBLISHED, encoding="utf-8")))

        agree, different, unresolved = 0, {}, {}
        for r in published:
            area = int(float(r["area_code"]))
            y0, y1 = int(r["year_start"]), int(r["year_end"])
            code, _status, how = m.assign(
                r["source_label"], r["iso3"] or None, "faostat", (y0 + y1) // 2
            )
            if code == r["polity_code"]:
                agree += 1
            elif code is None:
                unresolved[area] = (r["source_label"], r["polity_code"], how)
            else:
                different[area] = (r["source_label"], r["polity_code"], code, how)
    finally:
        os.unlink(tmp.name)

    problems = []
    for label, observed, baseline in (
        ("disagreement", set(different), BASELINE_DIFFERENT),
        ("unresolved", set(unresolved), BASELINE_UNRESOLVED),
    ):
        for area in sorted(observed - baseline):
            problems.append(f"NEW {label} at area {area}")
        for area in sorted(baseline - observed):
            problems.append(
                f"area {area} is baselined as a {label} but now agrees — "
                f"remove it from the baseline"
            )

    print(f"published FAOSTAT mappings: {len(published)}")
    print(f"  the two matchers agree     : {agree}")
    print(f"  different target           : {len(different)}")
    print(f"  matchlib cannot resolve    : {len(unresolved)}")
    if different:
        print("\n  different target:")
        for area, (lbl, a, b, how) in sorted(different.items()):
            print(
                f"    area {area:>4} {lbl[:26]:<28} match.R={a:<16} "
                f"matchlib={b:<16} ({how})"
            )

    if problems:
        print(f"\nFAIL: {len(problems)} change(s) against the baseline\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: agreement matches the baseline exactly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
