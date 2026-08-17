#!/usr/bin/env python3
"""Publish `pipelines/pre1961-matching/match.R`'s routing decisions as a committed table.

WHY (issue 16). `scripts/crosscheck_matchers.py` compares the repo's matchers against
each other, but it could only ever compare TWO of the three: the third,
`pipelines/pre1961-matching/match.R`, is R, its input (`data/external/before_1961.csv`,
18 MB) and its output (`data/compiled/pre1961/matched.csv`, 19 MB) are both outside what
CI can read — the second is gitignored — and CI has no R toolchain at all. The gate could
therefore only check the R matcher BY SOURCE TEXT, which is exactly the limitation
`scripts/validate_matcher_orphan_guard.py` records in prose: "two of the four code-bearing
outputs ... are gitignored, so no gate can ever read them".

This script closes that by writing what the gate actually needs: not 124,508 data rows,
but the DECISIONS behind them. Every row of matched.csv is one answer to the question the
three matchers all answer — "(label, iso3, year) -> which polity" — and the answers are
piecewise constant in the year, so the whole 124,508-row match collapses to 487 runs over
150 reporting entities. A run ENDS exactly where the R matcher changes its mind, so the
run boundaries ARE the transition years, which is the one place every recorded matcher
divergence has ever shown itself (issue 16 again, and the reason the FAOSTAT arm of the
crosscheck stopped probing midpoints only).

Requires the R pipeline to have been run first, because it reads its output:

    Rscript pipelines/pre1961-matching/match.R          # writes data/compiled/pre1961/
    python3 pipelines/pre1961-matching/write_r_crosswalk.py

Output: pipelines/pre1961-matching/state/r_crosswalk.csv  (tracked, read by the gate)

Unmatched input rows (`match_status == "none"`, 4,682 rows / 4.7% of the panel) are NOT
recorded. They are the R matcher declining to answer, and this table pins answers; the
gate's own "matchlib cannot resolve" arm covers the opposite direction.
"""
import csv
import os
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MATCHED = os.path.join(REPO, "data/compiled/pre1961/matched.csv")
OUT = os.path.join(REPO, "pipelines/pre1961-matching/state/r_crosswalk.csv")

# The identity the R matcher resolves on: raw iso3c plus the two label columns it falls
# back to (`resolve_iso` tries polity_name, then country, against its name_override table).
KEY = ("iso3c", "polity_name", "country")
FIELDS = (*KEY, "year_start", "year_end", "polity_code", "rows")


def main() -> int:
    if not os.path.exists(MATCHED):
        print(
            f"FAIL: {os.path.relpath(MATCHED, REPO)} is missing. This table is derived "
            f"from the R matcher's own output, so run it first:\n"
            f"  Rscript pipelines/pre1961-matching/match.R"
        )
        return 1

    answers = defaultdict(dict)   # entity -> {year: code}
    counts = defaultdict(int)     # (entity, year) -> data rows
    conflicts = []
    with open(MATCHED, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            code = (r.get("whep_polity_code") or "").strip()
            if code in ("", "NA"):
                continue          # match_status == "none": no decision to record
            ent = tuple(r[k] for k in KEY)
            year = int(r["year"])
            prev = answers[ent].get(year)
            if prev is not None and prev != code:
                conflicts.append((ent, year, prev, code))
            answers[ent][year] = code
            counts[(ent, year)] += 1

    if conflicts:
        # The R matcher resolves per (iso3c, polity_name, country, year), so one key
        # cannot hold two answers. If it ever does, this table's shape is wrong and
        # collapsing it to runs would silently drop one of the two.
        print(f"FAIL: {len(conflicts)} key(s) carry two different R answers, so the "
              f"crosswalk key is not the matcher's key")
        for ent, year, a, b in conflicts[:10]:
            print(f"  {ent} {year}: {a} vs {b}")
        return 1

    runs = []
    for ent, per_year in answers.items():
        years = sorted(per_year)
        start = prev_year = years[0]
        code = per_year[start]
        rows = counts[(ent, start)]
        for year in years[1:]:
            # Break the run on a changed answer OR on a gap in the data: a run must
            # describe a contiguous span the matcher actually saw, so the gate's
            # boundary probes land on years the R side really answered.
            if per_year[year] != code or year != prev_year + 1:
                runs.append((*ent, start, prev_year, code, rows))
                start, code, rows = year, per_year[year], 0
            rows += counts[(ent, year)]
            prev_year = year
        runs.append((*ent, start, prev_year, code, rows))

    runs.sort()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(FIELDS)
        w.writerows(runs)

    print(f"read   {os.path.relpath(MATCHED, REPO)}")
    print(f"  reporting entities            : {len(answers)}")
    print(f"  constant-answer runs          : {len(runs)}")
    print(f"  data rows behind them         : {sum(r[-1] for r in runs):,}")
    print(f"wrote  {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
