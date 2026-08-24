#!/usr/bin/env python3
"""Guard `data/final/source_label_ocr_corrections.csv` (issue 552).

A dozen fao1952 source labels are misreadings of a label the SAME source also prints correctly
-- `Afghaniscan`, `Crechoslovakia`, `Madagascar 4`. `01_match_and_findings.py` rewrites them to
the correct spelling before matching, which routes 25 otherwise-unresolved rows.

WHY A RENAME AND NOT TWELVE ALIASES. `Czechoslovakia` routes per year across F51-1918-1938,
F51-1938-1945 and F51-1947-1993. An alias maps a label to ONE polity, so aliasing `Crechoslovakia`
would hard-code a span decision that year resolution already makes correctly -- and the modal
destination of the correct spelling (F51-1918-1938, which ends in 1938) is the WRONG one for its
1947-1948 rows. Correcting the spelling defers the decision instead of duplicating it.

WHAT THIS GATE CAN AND CANNOT SEE. Layer B is not redistributable and is absent in CI, so the
arms that need it degrade rather than vanish -- and the arms that do NOT need it are the ones
that catch the failure that matters: a correction that has become redundant, or a table that has
silently shrunk. Both are checkable from the polities database alone.
"""
from __future__ import annotations

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "data/final/source_label_ocr_corrections.csv")
POLDB = os.path.join(REPO, "data/final/polities_database.csv")
ALIASES = os.path.join(REPO, "pipelines/polity-autoimprove/state/applied_aliases.csv")

# Bidirectional, like every other ceiling here: the count dropping means a correction was deleted
# and 25 rows quietly stopped resolving, which no other number in this repo would show.
BASELINE_CORRECTIONS = 12

# `British Guiana` resolves only when the matcher is built with `common_names_csv`, which the
# pipeline passes and this gate cannot -- that file lives outside the repo. So one entry is
# expected to look unresolvable from here. Pinning the count keeps that honest instead of letting
# it hide a second one.
BASELINE_UNRESOLVABLE_WITHOUT_COMMON_NAMES = 1


def main() -> int:
    problems = []
    if not os.path.exists(TABLE):
        print(f"FAIL: {os.path.relpath(TABLE, REPO)} is missing")
        return 1
    with open(TABLE, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    seen = set()
    for r in rows:
        key = (r["source"], r["ocr_label"])
        if key in seen:
            problems.append(f"duplicate correction key {key}")
        seen.add(key)
        if not r["source"].strip():
            problems.append(f"{r['ocr_label']!r}: empty source -- a correction must name the source "
                            "it applies to, or it rewrites labels in tables that spell them correctly")
        if r["ocr_label"] == r["correct_label"]:
            problems.append(f"{key}: correction is a no-op")
        if not r.get("note", "").strip():
            problems.append(f"{key}: no note -- the note is where the OCR mechanism is named")

    print(f"OCR spelling corrections: {len(rows)} (ceiling {BASELINE_CORRECTIONS})")
    if len(rows) > BASELINE_CORRECTIONS:
        problems.append(f"{len(rows)} corrections, above the ceiling of {BASELINE_CORRECTIONS} -- "
                        "raise it deliberately, with the new pair's evidence in its note")
    elif len(rows) < BASELINE_CORRECTIONS:
        problems.append(f"only {len(rows)} corrections, below the ceiling of {BASELINE_CORRECTIONS} "
                        "-- an entry was deleted and its rows have stopped resolving")

    sys.path.insert(0, os.path.join(REPO, "pipelines/polity-autoimprove"))
    try:
        import matchlib
    except ImportError:
        print("SKIP: matchlib unavailable -- structural arms only")
        for p in problems:
            print("  " + p)
        return 1 if problems else 0

    matcher = matchlib.Matcher(POLDB, ALIASES, verbose=False)

    def resolves(label, source):
        for year in (1937, 1948, 1949, 1950, 1951):
            try:
                if matcher.assign(label, None, source, year)[0]:
                    return True
            except Exception:
                pass
        return False

    redundant = [r for r in rows if resolves(r["ocr_label"], r["source"])]
    if redundant:
        problems.append(
            f"{len(redundant)} OCR label(s) already resolve WITHOUT correction, so the entry is "
            f"redundant and hides whatever now routes them: "
            + ", ".join(f"{r['ocr_label']!r}" for r in redundant[:5])
        )

    unresolvable = [r for r in rows if not resolves(r["correct_label"], r["source"])]
    print(f"  correct spellings that do not resolve from here: {len(unresolvable)} "
          f"(expected {BASELINE_UNRESOLVABLE_WITHOUT_COMMON_NAMES}, the common_names case)")
    if len(unresolvable) > BASELINE_UNRESOLVABLE_WITHOUT_COMMON_NAMES:
        problems.append(
            f"{len(unresolvable)} correct spelling(s) resolve to no polity: "
            + ", ".join(f"{r['correct_label']!r}" for r in unresolvable[:5])
            + f". Above the expected {BASELINE_UNRESOLVABLE_WITHOUT_COMMON_NAMES} -- a correction "
            "whose target routes nowhere moves a row from one unresolved label to another"
        )
    elif len(unresolvable) < BASELINE_UNRESOLVABLE_WITHOUT_COMMON_NAMES:
        problems.append(
            f"only {len(unresolvable)} correct spelling(s) fail to resolve, below the expected "
            f"{BASELINE_UNRESOLVABLE_WITHOUT_COMMON_NAMES} -- lower it so the improvement is held"
        )

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print("  " + p)
        return 1
    print("\nPASS: every tabled OCR correction is needed, and its target routes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
