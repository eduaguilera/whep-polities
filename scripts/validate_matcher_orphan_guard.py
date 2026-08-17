#!/usr/bin/env python3
"""Every matcher crosswalk names a polity code data can actually be routed to.

WHY THIS EXISTS (issue 17). A matcher is a crosswalk: source labels in, polity codes out.
Its codes are resolved against the database, so they are right ON THE DAY IT RUNS — and the
database then MOVES. A period re-spanned, a row renamed, a row retired, and last run's codes
point at nothing. Nobody downstream notices, because every consumer resolves a code by
LOOKING IT UP, and a lookup that finds nothing returns nothing rather than raising. That is
the #244 failure: five codes carrying 799 rows sat in the layer-B match while
`territory_basis.csv` published 0 rows for their successors, and a polity had to be removed
from another gate's baseline because committed state said it received no data.

Measured on this repo 2026-08-17: one published FAOSTAT mapping row retargeted to a
fabricated `ZZZ-1800-1900` passes NINE of the TEN gates that read
`data/final/faostat_area_polity_map.csv`. `validate_map_area_year`, the only one that joins
on the code, drops rows whose code is not live (`if code not in live: continue`) — so an
orphan is invisible to exactly the check that would catch a wrong code.

WHAT IS AND IS NOT NEW HERE, measured rather than assumed. The tenth gate,
`crosscheck_matchers.py`, DOES catch that mutation: it re-resolves all 297 published areas
through matchlib and reports the disagreement (and it still catches it when the upstream
`faostat_aliases.csv` is mutated in step, so the published map is not in fact unguarded).
`scripts/validate_aliases.py` likewise already rejects a retired/superseded target in
`applied_aliases.csv`. So check A below is a cheap consolidation, asserted to zero across all
three committed crosswalks, and NOT the load-bearing half of this fix. The load-bearing half
is the refusal at each matcher's write, because two of the four code-bearing outputs are
gitignored and therefore invisible to every gate in CI, for ever:
`pipelines/polity-autoimprove/state/matched_rows.parquet` (issue 243's five orphan codes,
799 rows, lived exactly there) and `data/compiled/pre1961/matched.csv`. Stage 04's existing
guard is two stages downstream of where the bad parquet is authored; these refuse at
authorship.

WHY A GATE AND A GUARD, not one or the other. Issue 17's subject is that the matchers cannot
run in CI at all: `pipelines/polity-autoimprove/01_match_and_findings.py` needs layer B
(`WHEP_LAYERB`, not redistributable), `pipelines/faostat-era-matching/match.R` needs a WHEP
checkout's FAOSTAT pins cache (`WHEP_REPO`), and no R dependency is installed in the
workflow. So neither half suffices alone:

  * The REFUSAL has to live at the write, in the matcher, where the bad crosswalk is
    authored — that is the only place the defect can be introduced, and it runs wherever the
    matcher runs. `extdata.refuse_orphan_codes` (Python) and `pipelines/lib/orphan_guard.R`
    (base R, so it loads without the matchers' tidyverse) do that.
  * But CI cannot run the matchers, so CI cannot observe those guards firing, and a guard
    nothing checks is a guard that can be deleted or bypassed silently. THIS gate is what CI
    can see: it checks the committed crosswalks against the current database (check A) and
    checks that each matcher still routes its output through a guard before writing it
    (check B).

Check A is the part that answers the issue's "nothing validates matching in CI": it needs
only the repository, and it is a real check on matcher OUTPUT rather than on matcher logic.
It does not verify the 189,694-row match count — that still needs layer B — and it does not
claim to.

Asserted to zero, no baseline: measured 2026-08-17, all 1,540 code references across the
three committed crosswalks name live polities.

Usage:
  python3 scripts/validate_matcher_orphan_guard.py
"""
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Rows kept for provenance that must never receive data. Spelled here rather than imported
# so this gate fails if the policy is quietly widened elsewhere; scripts/validate_constants.py
# is what keeps the repo's copies of it in agreement.
DEAD_STATUS = ("retired", "superseded")

# CHECK A. Committed crosswalks a matcher wrote, and the column holding the target code.
# `applied_aliases.csv` is also covered by scripts/validate_aliases.py check 1 -- kept here
# anyway, because that gate reads the alias REGISTRY as a hand-maintained file while this one
# reads it as matcher output, and the overlap costs one set difference.
CROSSWALKS = (
    ("pipelines/faostat-era-matching/state/faostat_aliases.csv", "polity_code"),
    ("data/final/faostat_area_polity_map.csv", "polity_code"),
    ("pipelines/polity-autoimprove/state/applied_aliases.csv", "polity_code"),
)

# CHECK B. Each matcher/generator that writes a code-bearing crosswalk, the token proving its
# guard is present, and the write it must come BEFORE. Order matters: a guard placed after the
# write refuses nothing that has not already been published.
GUARDED_WRITERS = (
    ("pipelines/polity-autoimprove/01_match_and_findings.py",
     "refuse_orphan_codes(", 'to_parquet(f"{OUT}/matched_rows.parquet"'),
    ("pipelines/polity-autoimprove/04_territory_basis.py",
     "matched_rows.parquet attributes", "def classify("),
    ("pipelines/faostat-era-matching/match.R",
     "refuse_orphan_codes(", 'file.path(state_dir, "faostat_aliases.csv")'),
    ("pipelines/pre1961-matching/match.R",
     "refuse_orphan_codes(", "matched_path <- file.path(out_dir"),
)

# The guards themselves. Without these declarations the calls above are name errors, and a
# matcher that cannot load its guard is a matcher with no guard.
GUARD_DECLARATIONS = (
    ("pipelines/polity-autoimprove/extdata.py", "def refuse_orphan_codes("),
    ("pipelines/polity-autoimprove/extdata.py", "def live_polity_codes("),
    ("pipelines/lib/orphan_guard.R", "refuse_orphan_codes <- function("),
    ("pipelines/lib/orphan_guard.R", "whep_live_polity_codes <- function("),
)


def read_rows(rel: str) -> list:
    path = os.path.join(REPO, rel)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    problems = []

    polities = read_rows("data/final/polities_database.csv")
    if not polities:
        print("FAIL: data/final/polities_database.csv is missing or empty")
        return 1
    present = {r["polity_code"] for r in polities if r.get("polity_code")}
    live = {r["polity_code"] for r in polities
            if r.get("polity_code")
            and (r.get("wiki_status") or "").strip() not in DEAD_STATUS}
    print(f"polities: {len(present):,} present, {len(live):,} live "
          f"({len(present) - len(live)} retired/superseded)")

    # --- A. committed crosswalks name live polities -----------------------------------
    checked = 0
    for rel, column in CROSSWALKS:
        rows = read_rows(rel)
        if not rows:
            problems.append(f"{rel}: missing or empty -- this gate has stopped checking it")
            continue
        if column not in rows[0]:
            problems.append(f"{rel}: no {column!r} column (renamed?); nothing was checked")
            continue
        codes = [(r.get(column) or "").strip() for r in rows]
        codes = [c for c in codes if c]
        checked += len(codes)
        bad = {}
        for code in codes:
            if code not in live:
                bad.setdefault(code, [0, "absent" if code not in present
                                         else "retired/superseded"])[0] += 1
        print(f"  {rel}: {len(codes):,} code reference(s), {len(bad)} unroutable")
        for code, (n, why) in sorted(bad.items(), key=lambda t: (-t[1][0], t[0])):
            problems.append(
                f"{rel}: {n} row(s) target {code}, which is {why}. Consumers resolve this "
                f"code by lookup, so the rows route NOWHERE and nothing raises "
                f"(validate_map_area_year skips them outright)."
            )

    # --- B. each matcher still refuses to write an unroutable crosswalk ---------------
    for rel, token, write_token in GUARDED_WRITERS:
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            problems.append(f"{rel}: missing -- a guarded writer disappeared")
            continue
        text = open(path, encoding="utf-8").read()
        gpos, wpos = text.find(token), text.find(write_token)
        if wpos < 0:
            problems.append(
                f"{rel}: cannot find its write ({write_token!r}); this check is looking at "
                f"the wrong place and is no longer verifying anything"
            )
            continue
        if gpos < 0:
            problems.append(
                f"{rel}: writes a code-bearing crosswalk but never calls the orphan guard "
                f"({token!r}). CI cannot run this matcher, so a crosswalk it writes against "
                f"a moved database is caught here or nowhere."
            )
        elif gpos > wpos:
            problems.append(
                f"{rel}: calls the orphan guard AFTER its write ({token!r} at {gpos}, write "
                f"at {wpos}); the bad file is already on disk by then"
            )

    for rel, token in GUARD_DECLARATIONS:
        path = os.path.join(REPO, rel)
        text = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        if token not in text:
            problems.append(
                f"{rel}: no longer declares {token!r} -- every call above is a name error, "
                f"and an R matcher that cannot source its guard fails only when someone runs it"
            )

    print(f"guarded writers: {len(GUARDED_WRITERS)}; code references checked: {checked:,}")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: every committed crosswalk names a live polity, and every matcher "
          "refuses to write one that does not")
    return 0


if __name__ == "__main__":
    sys.exit(main())
