#!/usr/bin/env python3
"""Does every verdict in the review ledger still describe something that exists?

`pipelines/polity-autoimprove/state/review_ledger.csv` is the banked memory of the assertion
pipeline: one row per unit that has been judged, carrying the verdict, the evidence hash it was
judged against, and the protocol version it was judged under. It is TRACKED, so it ships.

WHAT IT COULD NOT SEE. A polity-keyed row says "this polity was examined and found correct".
When a polity is RE-SPANNED its code changes -- SEN-1886-1959 became SEN-1886-1960 when issue 77
closed a one-year hole -- and the ledger keeps the old key. The row then asserts that something
which does not exist is correct, which is not a true statement or a false one; it is a statement
about nothing, and it silently exempts the row that REPLACED it from ever being examined.

Measured when this check was written (2026-08-17): 4 of 260 polity-keyed rows, all
`status=correct`, all naming codes retired by re-spans between 2026-06-29 and 2026-07-01 --
CHL-1810-1883, GNGU-1884-1914, LAO-1893-1953, SEN-1886-1959.

This is the same shape as issue 243 (matched_rows.parquet outliving a re-span) and the deployed
pre-1961 site (#300), and the third place it has appeared. The pattern is always: state keyed by
polity code, written before a rename, never re-derived.

WHY NOT JUST REPAIR THE FOUR. Because the next re-span does it again. A rename is a normal
event here -- five happened in one PR (#269) -- so the ledger needs a check, not a cleanup.

Two signals:
  A. DEAD KEY      a polity-keyed row whose code is absent from the database.
  B. RETIRED KEY   a polity-keyed row whose code exists but is retired or superseded. Weaker:
                   a verdict about a row that still exists but can never receive data is stale
                   rather than meaningless, so it is reported and counted, not failed, unless
                   it claims `correct`.

Usage:
  python3 scripts/validate_review_ledger.py
"""
from __future__ import annotations

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(REPO, "pipelines/polity-autoimprove/state/review_ledger.csv")
DB = os.path.join(REPO, "data/final/polities_database.csv")
DEAD = ("retired", "superseded")

# Rows recorded before this check existed and not yet re-derived. BIDIRECTIONAL: repair one and
# this gate fails until its entry is deleted, so the list can only shrink.
# EVERY BASELINE MUST BE A frozenset({...}), NOT A BARE {...}.
BASELINE_DEAD_KEYS = frozenset()

# Signal B is a CEILING, not a failure list. A polity judged `correct` and LATER superseded by a
# split was correctly judged at the time -- the verdict is stale, not wrong, and the row still
# exists. Pinning it stops the class growing while leaving the seven alone. Measured 2026-08-17.
BASELINE_RETIRED_CORRECT = 7


def main() -> int:
    for path in (LEDGER, DB):
        if not os.path.exists(path):
            print(f"SKIP: {os.path.relpath(path, REPO)} missing")
            return 0

    live, known = {}, set()
    with open(DB, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            known.add(r["polity_code"])
            live[r["polity_code"]] = (r.get("wiki_status") or "").strip()

    with open(LEDGER, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    pol = [r for r in rows if (r.get("unit_kind") or "") == "polity"]

    dead_key, retired_key = [], []
    for r in pol:
        key = (r.get("key") or "").strip()
        if not key:
            continue
        if key not in known:
            dead_key.append((key, r.get("status"), r.get("last_run")))
        elif live.get(key) in DEAD and (r.get("status") or "") == "correct":
            retired_key.append((key, r.get("status"), r.get("last_run")))

    print(f"ledger rows: {len(rows)} ({len(pol)} polity-keyed)")
    print(f"A. keys absent from the database: {len(dead_key)}")
    print(f"B. keys that are retired or superseded but judged `correct`: {len(retired_key)}")

    problems = []
    for key, status, last in sorted(dead_key):
        if key in BASELINE_DEAD_KEYS:
            continue
        problems.append(
            f"{key} is judged `{status}` (last run {last}) but no such polity exists. A re-span "
            f"renames the code and the ledger keeps the old one, so this verdict describes "
            f"nothing AND the row that replaced it inherits no judgement. Re-point it at the "
            f"successor and re-derive, or delete it"
        )
    if len(retired_key) > BASELINE_RETIRED_CORRECT:
        for key, status, last in sorted(retired_key):
            print(f"   retired-but-correct  {key:22} last run {last}")
        problems.append(
            f"{len(retired_key)} verdicts judge a retired or superseded polity `correct`, above "
            f"the pinned ceiling of {BASELINE_RETIRED_CORRECT}. Such a verdict was true when it "
            f"was made and is merely stale, so the ceiling exists to stop the class growing "
            f"rather than to condemn the ones already there"
        )
    for key in sorted(BASELINE_DEAD_KEYS - {k for k, _s, _l in dead_key}):
        problems.append(
            f"{key} is baselined here as a dead ledger key but is not one any more — remove its "
            f"entry, saying what was re-derived"
        )

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: every banked verdict names a polity that exists")
    return 0


if __name__ == "__main__":
    sys.exit(main())
