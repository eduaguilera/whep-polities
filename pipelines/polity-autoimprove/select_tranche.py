#!/usr/bin/env python3
"""Pick the next verification tranche: the highest-exposure assertions not yet judged.

WHY THIS IS A SCRIPT AND NOT A ONE-LINER. Selecting the next batch looks like `filter
status == pending, sort by rows, take 12`, and that is wrong in two independent ways. Both
were hit for real, and the second one silently re-selected a batch that had just been
verified -- twelve agents' worth of work about to be spent re-deciding settled questions.

  1. assertions.json GOES STALE THE MOMENT VERDICTS ARE APPLIED. apply_verdicts.py writes
     the ledger; only a re-run of 00_intake.py re-reads the ledger and re-labels the queue.
     Between those two events every just-verified assertion still reads `pending`. So
     `status` is necessary but nowhere near sufficient, and the authority on what has been
     judged is verdicts_applied.jsonl.

  2. THE APPLIED-VERDICT KEY IS NESTED. Records are
     {applied, verdict:{key, verdict, confidence, polity_code, checks, basis}, review,
     quarantined}. A top-level `rec.get("key")` returns None for every record, so the
     dedup set comes out EMPTY and nothing is excluded -- and an empty exclusion set looks
     exactly like a clean queue. That is the failure that re-selected a finished batch.

  3. A CANDIDATE CAN BE RETIRED OUT FROM UNDER THE QUEUE. Re-spans rename polity codes
     (SEN-1886-1959 -> SEN-1886-1960 when issue 77 closed a one-year hole), and an assertion
     derived before the rename still names the old code. Verifying a route to a polity that
     does not exist cannot produce a usable verdict. Those are reported separately, because
     a nonzero count is the signal to re-run 00_intake.py rather than something to ignore.

Both failure modes are silent and both bias the SAME way -- toward looking like there is
work to do when there is not -- which is why this prints its arithmetic rather than just
emitting a list.

Usage:
  python3 pipelines/polity-autoimprove/select_tranche.py             # next 12
  python3 pipelines/polity-autoimprove/select_tranche.py --limit 20
  python3 pipelines/polity-autoimprove/select_tranche.py --json      # bare JSON array

Feed the JSON array to the verification workflow as its `keys` argument.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(REPO, "pipelines/polity-autoimprove/state")
ASSERTIONS = os.path.join(STATE, "assertions.json")
APPLIED = os.path.join(STATE, "verdicts_applied.jsonl")
DB = os.path.join(REPO, "data/final/polities_database.csv")

PENDING = ("pending", "reopened")


def judged_keys(path: str) -> set[str]:
    """Keys with a banked verdict. The key is at record["verdict"]["key"], NOT top level."""
    keys: set[str] = set()
    if not os.path.exists(path):
        return keys
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            verdict = rec.get("verdict")
            if isinstance(verdict, str):  # tolerated: an older writer stored it repr()'d
                try:
                    verdict = json.loads(verdict)
                except json.JSONDecodeError:
                    continue
            if isinstance(verdict, dict) and verdict.get("key"):
                keys.add(verdict["key"])
    return keys


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=12, help="how many to select (default 12)")
    ap.add_argument("--json", action="store_true", help="print only the JSON array")
    args = ap.parse_args()

    for path in (ASSERTIONS, APPLIED, DB):
        if not os.path.exists(path):
            print(f"MISSING: {os.path.relpath(path, REPO)}", file=sys.stderr)
            if path is ASSERTIONS:
                print("run 00_intake.py first -- see README, 'Intake from layer B'", file=sys.stderr)
            return 2

    with open(DB, encoding="utf-8") as fh:
        known = {r["polity_code"] for r in csv.DictReader(fh)}

    done = judged_keys(APPLIED)

    with open(ASSERTIONS, encoding="utf-8") as fh:
        blob = json.load(fh)
    items = blob["assertions"] if isinstance(blob, dict) and "assertions" in blob else blob

    unjudged = [a for a in items if a.get("status") in PENDING and a.get("key") not in done]
    stale = [a for a in unjudged if a.get("candidate") not in known]
    live = [a for a in unjudged if a.get("candidate") in known]
    live.sort(key=lambda a: -(a.get("rows") or 0))
    picked = live[: args.limit]

    if args.json:
        print(json.dumps([a["key"] for a in picked]))
        return 0

    print(f"assertions        {len(items)}")
    print(f"  banked verdicts {len(done)}")
    print(f"  still pending   {len(live)}")
    if stale:
        rows = sum(a.get("rows") or 0 for a in stale)
        print(
            f"  SKIPPED (stale) {len(stale)} carrying {rows:,} rows name a candidate that no "
            f"longer exists -- re-run 00_intake.py to re-derive them"
        )
        for a in sorted(stale, key=lambda a: -(a.get("rows") or 0))[:5]:
            print(f"      {a.get('rows'):>5}  {a['key'][:44]:46} -> {a.get('candidate')} (gone)")

    print(f"\nnext {len(picked)} by exposure:")
    for a in picked:
        print(f"  {a.get('rows'):>5}  {a['key'][:44]:46} -> {a.get('candidate')}")
    print()
    print(json.dumps([a["key"] for a in picked]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
