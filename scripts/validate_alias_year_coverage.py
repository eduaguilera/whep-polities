#!/usr/bin/env python3
"""Check that an alias does not claim a year its target polity cannot cover.

A polity code's `end_year` is EXCLUSIVE: `BLX-1850-1999` covers 1850-1998. An alias
row's `year_end` is INCLUSIVE. So whenever an alias's `year_end` equals its target's
`end_year`, the alias claims one year the polity does not hold.

Measured when this was written: 265 alias rows do that, carrying 461,445 observed
rows between them. RE-MEASURED 2026-08-13 against 907 published aliases (issue 79):
201 rows, 451,933 observed rows -- the class had already shrunk, because the mid-sized
cases issue 79 listed ("united states of america" [juan] 6,076 rows, "czech republic"
603, "serbia" 568) were clipped in the meantime and the issue's figures went stale.

OPEN-ENDED ALIASES ARE NOT IN THE CLASS, decided 2026-08-13. 67 of those 201 pointed at
a LIVE polity whose exclusive `end_year` is the 2025 ceiling, where `year_end == 2025` is
the ceiling showing through rather than an overshoot: a live polity has no real last year,
so there is nothing for the alias to overclaim. `validate_map_area_year.py` already
excluded exactly this case for the FAOSTAT map -- "13 registry rows sat there for that
reason alone" -- and the two gates asking the same question now answer it the same way.
Those 67 carried 788 observed rows and every one of them is `year_end == 2025`; none
overshot a ceiling polity by more than the ceiling itself. Removed from the baseline
rather than exempted quietly: see the header of validate_alias_year_baseline.txt.

WHAT REMAINS, 133 alias rows over 132 keys ("Indonesia Bali and Lombok" [fao1952] appears
twice, which is why the printed count is 132 and the row counts below sum to 133), splits
three ways and only one part is a defect:

  * 101 rows, 450,348 observed, name a DISSOLVED entity's final reporting year that no
    successor alias claims. ACCEPTED AS DATA, which is issue 79's third option and the
    decision already taken for the same four entities on the FAOSTAT map side (issue 164,
    see BASELINE_YEAR_END_PAST_COVERAGE in validate_map_area_year.py). The convention, now
    written down because a consumer resolving by strict year containment needs it: an
    alias's inclusive `year_end` MAY name the final year an entity reported as a unit even
    though the polity code's exclusive `end_year` stops before it, and that year's data
    belongs to the OUTGOING entity. Belgium-Luxembourg reported as a unit for 1999, Sudan
    for 2011, the USSR for 1991, the Netherlands Antilles for 2010 -- those four are
    450,335 of the 450,348 rows. The alternatives are worse: moving the polity end years
    embeds a new year in every polity_code and collides with successors that already start
    in the current end_year, and clipping the alias sends a genuine reported year to a
    polity that no alias names, which for an `aggregate` target WHEP's nearest-period
    fallback deliberately skips -- so the row goes to NA rather than being relabelled.
  * 32 rows, 813 observed, DO have a successor alias covering the boundary year, so the
    year has two answers and match order decides. These are clippable by the issue 90
    group A recipe (`year_end = polity end_year - 1`) and are deliberately NOT clipped
    here: 6 of them move measured data (Syria 1967, "united states of america" 1803 and
    1848 on two sources, "china 22 provinces" 1945); 7 point at a successor in a DIFFERENT
    polity family (sudan 2011, serbia 2006, serbia 1992, serbia 1918, czech republic 1993,
    botswana 1966, china manchuria 1945), which is the class validate_alias_chain_overlaps.py
    says needs a historical decision rather than a range edit; and Cape Verde 1975 is a
    deliberate curation choice documented in that gate. Still open.
  * 0 rows overshoot by MORE than one year. There were 2 on 2026-08-13 ("tanzania" and
    "tanganyika" claiming to 1964 against TAN-1922-1964, whose span was narrowed to
    end_year=1961 when TZA-1961-1964 was split out, leaving 1964 in the CODE only). Both
    were fixed rather than baselined, by the group B pattern: clipped to 1960 and the
    1961-1963 and 1964 claims re-pointed at TZA-1961-1964 and TZA-1964-2025.

The failure is silent, which is the reason to gate it: a matcher that falls back to
the nearest period lands these rows on the ADJACENT polity rather than dropping them,
so 451k rows can be misattributed without anything looking broken.

Usage:
  python3 scripts/validate_alias_year_coverage.py [--list]
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALIAS = os.path.join(REPO, "data/final/label_alias_map.csv")
DB = os.path.join(REPO, "data/final/polities_database.csv")
BASELINE = os.path.join(REPO, "scripts/validate_alias_year_baseline.txt")

# A live polity whose exclusive end_year IS this ceiling has no real last year, so an alias
# ending at the ceiling is not overclaiming anything. Same constant and same reason as
# validate_map_area_year.py's CEILING. See the module docstring.
CEILING = 2025


def load_baseline() -> set:
    if not os.path.exists(BASELINE):
        return set()
    out = set()
    with open(BASELINE, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) == 3:
                out.add(tuple(parts))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="print every offender, not just new ones")
    args = ap.parse_args()

    with open(DB, encoding="utf-8") as fh:
        db = {r["polity_code"]: r for r in csv.DictReader(fh)}
    with open(ALIAS, encoding="utf-8") as fh:
        aliases = list(csv.DictReader(fh))

    observed = {}
    rows_at_risk = 0
    unknown_target = 0
    open_ended = 0
    for r in aliases:
        code = (r.get("polity_code") or "").strip()
        target = db.get(code)
        if target is None:
            unknown_target += 1
            continue
        try:
            year_end = int(r["year_end"])
            polity_end = int(target["end_year"])
        except (KeyError, TypeError, ValueError):
            continue
        if year_end < polity_end:
            continue
        if polity_end >= CEILING and year_end <= CEILING:
            # Open-ended target: the ceiling showing through, not an overshoot. Counted so
            # the number is visible rather than silently dropped.
            #
            # `year_end <= CEILING` deliberately narrows the exclusion: an alias reaching
            # BEYOND the ceiling (year_end 2026 against AND-1800-2025) is a real overclaim
            # and must not disappear into it. All 67 rows excluded when this was written had
            # year_end == 2025 exactly, so the guard costs nothing today and closes the hole
            # a bare `polity_end >= CEILING` would leave open.
            open_ended += 1
            continue
        key = ((r.get("source_label") or ""), (r.get("source") or ""), code)
        try:
            n = int(r.get("observed_rows") or 0)
        except ValueError:
            n = 0
        if key not in observed:
            rows_at_risk += n
        observed[key] = (year_end, polity_end, n)

    baseline = load_baseline()
    print(f"{len(aliases)} alias rows, {unknown_target} pointing at no known polity")
    print(f"claiming a year past their polity's coverage: {len(observed)}")
    print(f"observed rows on those aliases: {rows_at_risk:,}")
    print(
        f"excluded: {open_ended} alias rows ending at the {CEILING} ceiling of a live "
        f"polity, which has no last year to overclaim"
    )

    if args.list:
        for key, (ye, pe, n) in sorted(observed.items(), key=lambda kv: -kv[1][2]):
            print(f'   rows={n:>6}  "{key[0][:34]:34}" [{key[1][:12]:12}] to {ye} -> {key[2]} (covers to {pe - 1})')

    problems = []
    for key in sorted(set(observed) - baseline):
        ye, pe, n = observed[key]
        problems.append(
            f'NEW: "{key[0]}" [{key[1]}] claims to {ye} but {key[2]} covers only to '
            f"{pe - 1} ({n} observed rows)"
        )
    for key in sorted(baseline - set(observed)):
        problems.append(
            f'"{key[0]}" [{key[1]}] -> {key[2]} is baselined but no longer overclaims — '
            f"remove its line from scripts/validate_alias_year_baseline.txt"
        )

    if problems:
        print(f"\nFAIL: {len(problems)} change(s) against the baseline\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: alias year coverage matches the baseline exactly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
