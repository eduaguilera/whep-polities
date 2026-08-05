#!/usr/bin/env python3
"""Check that a live polity's own name identifies it, given a year.

WHY THIS REPOSITORY OWES THE PROPERTY. WHEP's `resolve_polity_label()` now resolves a
label by alias first and then by the polity's own name, mirroring
`matchlib.Matcher`'s name family. Both sides can only answer when EXACTLY ONE polity
of that name is live in the year asked about; otherwise they return nothing, because
picking by row order would invent an answer. That makes "one live polity per
(normalised name, year)" a property the consumer depends on and nothing here guarded.

The failure mode is silent on the consumer's side. Renaming a polity so its
normalised name collides with a live sibling does not break a join or raise a
warning — it makes a label that used to resolve return NA, and NA is what an
unmapped label looks like too.

MEASURED: 732 live polities, 110 normalised names shared by more than one, and 17 of
those have holders whose years OVERLAP. Sharing a name is fine — Greece 1830-1881 and
Greece 1947-2025 are the same country in two eras, and a year separates them. Sharing
a name AND a year is what cannot be resolved.

FIFTEEN of the 17 are one shape, and I first wrote that all of them were, which running
this disproved. The fifteen are a COARSE period listed alongside its own finer
sub-periods, so the coarse row overlaps each of them — same prefix throughout:

    belize      BLZ-1800-2025 spans BLZ-1800-1886, BLZ-1970-1981, BLZ-1981-2025
    greece      GRC-1830-1913 spans GRC-1830-1881 and GRC-1881-1913

The other TWO cross prefix families, which makes them different problems wearing the
same symptom, and both are already open:

    morocco     MAR-1911-1958 against MOR-1956-1958  (issue 52: runs past its
                successor's start year)
    serbia      SER-2006-2008 against SRB-2006-2008  (issue 43: two live polities for
                one territory and period — a duplicate, not a periodisation)

So the fifteen are the consumer's view of issue 49 (same-family pairs covering the same
years), and the two are views of 52 and 43. Baselined rather than forbidden because
resolving the fifteen means deciding whether a coarse period should exist at all, which
is a curation decision per family — and because the two are tracked elsewhere and will
leave this list when they are fixed there.

Bidirectional: a NEW ambiguous name fails, and a baselined one that stops overlapping
must be removed from the file, so the list can only shrink deliberately.

Usage:
  python3 scripts/validate_live_name_ambiguity.py
"""
import collections
import csv
import os
import re
import sys
import unicodedata

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(REPO, "data/final/polities_database.csv")

# Matches the six other gates that already agree on this: validate_cow_codes,
# validate_family_areas, validate_iso_collisions, validate_cross_family_names,
# audit_family_shadowing and structural_change_check all define exactly this tuple.
# This gate tested `== "retired"` alone until 2026-08-05, so it counted the 20
# `superseded` rows as LIVE -- 728 against the repo convention's 708 -- and any
# name it flagged where one member was superseded was an artifact of that, not an
# ambiguity a data source could ever hit.
DEAD_STATUS = ("retired", "superseded")
BASELINE_PATH = os.path.join(
    REPO, "scripts/validate_live_name_ambiguity_baseline.txt"
)


def norm(s: str) -> str:
    """Mirror matchlib.norm and resolve_polity_label()'s normalisation exactly.

    Both sides fold accents, DROP parenthesised qualifiers, strip a leading "the" and
    map punctuation to spaces. The parenthetical rule is what makes this check
    necessary at all: "Greece (1830-1881)" and "Greece" both reduce to "greece", so
    period qualifiers written into the NAME do not separate two rows the way the year
    columns do.
    """
    s = (s or "").strip().lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"\s*\(.*?\)\s*", " ", s)
    s = re.sub(r"^the\s+", "", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load_baseline() -> set:
    if not os.path.exists(BASELINE_PATH):
        return set()
    with open(BASELINE_PATH, encoding="utf-8") as fh:
        return {
            line.strip()
            for line in fh
            if line.strip() and not line.startswith("#")
        }


def main() -> int:
    if not os.path.exists(CSV_PATH):
        print(f"FAIL: {CSV_PATH} missing; run scripts/build_database.py first")
        return 2

    live = []
    with open(CSV_PATH, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if (row.get("wiki_status") or "").strip() in DEAD_STATUS:
                continue
            try:
                start = int(row["start_year"])
                end = int(row["end_year"])
            except (KeyError, TypeError, ValueError):
                # A row without parseable years cannot be placed in time; the
                # code/column gate owns that complaint, not this one.
                continue
            live.append((norm(row["polity_name"]), row["polity_code"], start, end))

    by_name = collections.defaultdict(list)
    for key, code, start, end in live:
        if key:
            by_name[key].append((start, end, code))

    shared = {k: v for k, v in by_name.items() if len(v) > 1}
    ambiguous = {}
    for key, rows in shared.items():
        rows.sort()
        codes = set()
        for i, (s1, e1, c1) in enumerate(rows):
            for s2, e2, c2 in rows[i + 1 :]:
                # end_year is EXCLUSIVE, so touching periods do not overlap.
                if s1 < e2 and s2 < e1:
                    codes.update((c1, c2))
        if codes:
            ambiguous[key] = sorted(codes)

    print(f"live polities: {len(live)}")
    print(f"normalised names held by more than one: {len(shared)}")
    print(f"names whose holders overlap in years: {len(ambiguous)}")

    baseline = load_baseline()
    problems = []
    new = sorted(set(ambiguous) - baseline)
    for key in new:
        print(f"   NEW  {key:<26}{ambiguous[key]}")
    if new:
        problems.append(
            f"{len(new)} name(s) held by two polities live in the same year, and not "
            f"baselined: {new}. A consumer resolving a label by name gets NA for "
            f"those years, which is indistinguishable from an unmapped label."
        )
    fixed = sorted(baseline - set(ambiguous))
    if fixed:
        problems.append(
            f"baselined names that no longer overlap — remove them: {fixed}"
        )

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print(
        f"\nPASS: name ambiguity among live polities matches the baseline exactly "
        f"({len(baseline)} tracked)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
