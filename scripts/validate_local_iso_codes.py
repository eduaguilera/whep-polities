#!/usr/bin/env python3
"""Baseline the `iso3_code` vocabulary, so a change to territory identity is reviewed.

WHY THIS REPOSITORY OWES THE PROPERTY. `iso3_code` is not ISO-conformant and cannot be:
there is no ISO 3166 code for Austria-Hungary, so this database invents `AUH`. That is a
sound design, but it makes the column two things at once -- real ISO codes for entities
that have them, local codes for entities that do not -- and a consumer joining against an
ISO-keyed dataset silently matches nothing for the local ones. It is what stops four
dissolved federations reaching WHEP's LUH2 land series, and they carry 11.88% of
production value at 1961.

So the vocabulary itself is a published interface. This baselines it: the set of distinct
`iso3_code` values must not change without the change being reviewed. Adding a value means
a consumer's join gains or loses rows; changing one silently re-points every row carrying
it.

WHAT THIS DELIBERATELY DOES NOT DO, because the first version of it was vacuous.

I first tried to identify the LOCAL codes by testing `iso3_code == polity family prefix`,
on the observation that `AUH-1800-1859` carries `AUH`. That is not a discriminator at all:
`FRA-1958-2025` carries `FRA` too, because for most polities the prefix simply IS the ISO
code. The check reported 276 "local" codes over 607 rows when there are 56 local ones --
it was measuring the norm, not the exception. Caught only because 276 was implausible.

Separating local from real ISO needs an authoritative ISO 3166 list, which is not
available here: `requirements-ci.txt` is deliberately minimal, and vendoring 249 codes to
police a documentation claim is a poor trade. So this checks the weaker property that can
be checked honestly -- the vocabulary is stable -- and the README carries the local/ISO
distinction as prose, with the count and the rule stated there.

FAILS ON:
  - a new `iso3_code` value that is not baselined
  - a baselined value that no longer appears anywhere
  - a documented grouping exception that no longer holds
"""

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(REPO, "data/final/polities_database.csv")
BASELINE_PATH = os.path.join(REPO, "scripts/validate_local_iso_codes_baseline.txt")

# Polities whose `iso3_code` is deliberately another family's, because the entity was
# folded into it. Asserted by identity so the grouping cannot drift unnoticed.
EXCEPTIONS = {
    # French Cochinchina became part of French Indochina, so it carries FID, not FCC.
    # The same "groups by modern territory" rule that makes 59 pairs share a code.
    "FCC-1862-1887": "FID",
}


def load_baseline() -> set:
    if not os.path.exists(BASELINE_PATH):
        return set()
    codes = set()
    with open(BASELINE_PATH, encoding="utf-8") as fh:
        for line in fh:
            # Inline comments carry which values are local rather than ISO, which is the
            # useful part of this file, so they must be stripped rather than banned. The
            # first version of this loader only handled whole-line comments and read
            # "AUH  # local" as a code, so every entry mismatched at once.
            text = line.split("#", 1)[0].strip()
            if text:
                codes.add(text)
    return codes


def main() -> int:
    if not os.path.exists(CSV_PATH):
        print(f"FAIL: {CSV_PATH} not found")
        return 1

    with open(CSV_PATH, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    if not rows:
        print("FAIL: polities database is empty")
        return 1
    for col in ("iso3_code", "polity_code"):
        if col not in rows[0]:
            print(f"FAIL: expected a {col} column")
            return 1

    seen = {}
    problems = []

    for row in rows:
        code = (row.get("iso3_code") or "").strip()
        polity = (row.get("polity_code") or "").strip()
        if not code:
            continue
        seen.setdefault(code, []).append(polity)

        expected = EXCEPTIONS.get(polity)
        if expected is not None and code != expected:
            problems.append(
                f"{polity} is baselined as carrying {expected} but carries {code!r}"
            )

    for polity in EXCEPTIONS:
        if not any(polity in v for v in seen.values()):
            problems.append(
                f"{polity} is a baselined grouping exception but carries no iso3_code"
            )

    baseline = load_baseline()
    # Non-vacuous: an empty baseline would make the comparisons below assert nothing.
    if len(baseline) < 100:
        problems.append(
            f"baseline holds only {len(baseline)} codes, which cannot be right for "
            f"{len(seen)} observed -- regenerate it deliberately"
        )

    added = sorted(set(seen) - baseline)
    if added:
        problems.append(
            f"{len(added)} iso3_code value(s) are not baselined. Each one changes what an "
            f"ISO-keyed join matches, so it is a decision, not a detail: "
            f"{', '.join(added)}"
        )

    removed = sorted(baseline - set(seen))
    if removed:
        problems.append(
            f"{len(removed)} baselined iso3_code value(s) no longer appear. If a polity "
            f"was given a better code that is progress, but drop these from the baseline: "
            f"{', '.join(removed)}"
        )

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1

    rows_covered = sum(len(v) for v in seen.values())
    print(
        f"\nPASS: {len(seen)} distinct iso3_code value(s) over {rows_covered} row(s) match "
        f"the baseline exactly, and {len(EXCEPTIONS)} grouping exception(s) hold"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
