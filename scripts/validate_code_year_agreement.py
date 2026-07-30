#!/usr/bin/env python3
"""Check that a polity code's embedded years match its own start_year and end_year.

A polity code is documented as `PREFIX-startyear-endyear`, which makes the years
readable straight off the identifier — and consumers do read them, because parsing a
string is cheaper than joining a table. When the code disagrees with the columns, both
answers are in circulation and nothing says which is right.

FOUND VIA A DOWNSTREAM SYMPTOM, not by looking here. The consumer swept its 869 label
aliases for ranges extending past their target polity's span. 268 overshot by exactly one
year, which is the convention — an alias `year_end` is inclusive while a polity
`end_year` is exclusive. Two overshot by four:

    tanganyika  1922-1964  ->  TAN-1922-1964
    tanzania    1922-1964  ->  TAN-1922-1964

The aliases were written against the years in the CODE. The polity's `end_year` is 1961.
So the aliases resolve 1962, 1963 and 1964 to a polity its own columns say had ended, and
they do it because the identifier advertised a different span.

Both cases are historical judgement rather than typos, which is why they are baselined
rather than corrected here:

  TAN-1922-1964  Tanganyika. Independence 1961; the union with Zanzibar forming Tanzania
                 was 1964. Either year is defensible for the end of the polity, but the
                 code and the columns must agree on which was chosen.
  NNG-1949-1963  Netherlands New Guinea. Transferred to Indonesian administration 1963;
                 the Act of Free Choice was 1969. `end_year` says 1969, the code says
                 1963.

Fixing either means editing the wiki page — the source of truth — and deciding which year
the polity ends. Until then the pair is tracked so a THIRD cannot appear unnoticed, and so
that resolving one forces its removal from the baseline.

Usage:
  python3 scripts/validate_code_year_agreement.py
"""
import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(REPO, "data/final/polities_database.csv")

# Codes whose embedded years knowingly disagree with their columns, each awaiting a
# decision about which year is right. Bidirectional: a new one fails, and a resolved one
# must be removed or this fails too.
BASELINE = {
    "NNG-1949-1963": "end_year 1969; Act of Free Choice vs 1963 transfer",
    "TAN-1922-1964": "end_year 1961; independence vs the 1964 union with Zanzibar",
}

CODE_RE = re.compile(r"^([A-Z0-9]+)-(\d{4})-(\d{4})$")


def main() -> int:
    if not os.path.exists(CSV_PATH):
        print(f"FAIL: {CSV_PATH} missing; run scripts/build_database.py first")
        return 2

    parseable = 0
    disagreeing = {}
    with open(CSV_PATH, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            code = (row.get("polity_code") or "").strip()
            m = CODE_RE.match(code)
            if not m:
                # Aggregates and a handful of others do not encode years. Not an error:
                # the format applies to periodized territorial rows.
                continue
            parseable += 1
            try:
                start = int(row["start_year"])
                end = int(row["end_year"])
            except (KeyError, TypeError, ValueError):
                disagreeing[code] = "start_year or end_year is not an integer"
                continue
            if int(m.group(2)) != start or int(m.group(3)) != end:
                disagreeing[code] = (
                    f"code says {m.group(2)}-{m.group(3)}, columns say {start}-{end}"
                )

    print(f"polity codes encoding a year range: {parseable}")
    print(f"codes disagreeing with their own columns: {len(disagreeing)}")
    for code, why in sorted(disagreeing.items()):
        mark = "baselined" if code in BASELINE else "NEW"
        print(f"   {code:<18}{why}   [{mark}]")

    problems = []
    new = sorted(set(disagreeing) - set(BASELINE))
    if new:
        problems.append(
            f"codes whose embedded years disagree with their columns and are not "
            f"baselined: {new}. A consumer reading years off the identifier gets a "
            f"different span from one reading the columns."
        )
    fixed = sorted(set(BASELINE) - set(disagreeing))
    if fixed:
        problems.append(
            f"baselined codes that now agree — remove them from BASELINE: {fixed}"
        )

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print(
        "\nPASS: every code's embedded years match its columns, except the "
        f"{len(BASELINE)} awaiting a decision"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
