#!/usr/bin/env python3
"""Does every banked verdict orphaned by re-spanning still have something pointing at it?

Assertion keys are `label|source|first-last`, so re-deriving the queue re-splits spans and renames
keys. A verdict banked under `algeria|iia|1920-1945` then matches nothing when the queue starts
carrying `algeria|iia|1919-1945`. Issue 308 measured the cost and named the asymmetry:

    "So quarantines have a carrier. Confirms do not."

`quarantine.csv` is tracked and independently keyed, so a later verifier finds prior quarantine work
and cites it. An ordinary `confirm` had no such file, so re-spanning silently returned it to the queue
as `pending` and it was paid for twice. `23_verdict_carryover.py` writes that carrier and this gate
keeps it honest.

Measured on the run that added it: 52 of 460 banked verdicts are orphaned, ALL of them span drift --
`label|source gone entirely` is ZERO -- and 75 carry rows recover 50 of them onto 69 queue keys.

THE TABLE IS EVIDENCE, NOT A VERDICT, and that is a deliberate limit. A re-split is sometimes a
RESPONSE to a finding: issue 308's India case re-split `india|mitchell|1915-1937` into seven spans
while the new `1914-1936` still contained the 1928/29 break that got the original quarantined. Auto
-carrying a confirm across a re-span would launder a judgement onto a span nobody judged. So nothing
here re-banks; the gate only refuses to let prior work vanish unnoticed.

Three signals:
  A. NOTHING LOST      every orphaned banked key must appear in the table, or be one the generator
                       reports as having nothing to carry to. Silent disappearance is the defect.
  B. OVERLAP DERIVED   `overlap_years`, `banked_years` and `overlap_share` are re-derived from the two
                       spans in the row. The share is what a verifier would weigh prior work by.
  C. NO ZERO CARRIES   a row with zero overlap must not exist: sharing a label and source while
                       sharing no year says nothing, and `algeria|iia|1909-1918` beside a banked
                       `1920-1945` is exactly that case.

Usage:
  python3 scripts/validate_verdict_carryover.py
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(REPO, "pipelines/polity-autoimprove/state")
TABLE = os.path.join(STATE, "verdict_carryover.csv")
APPLIED = os.path.join(STATE, "verdicts_applied.jsonl")
QUEUE = os.path.join(STATE, "assertions.json")

# Orphans with no overlapping queue key at all. Both are single-year spans whose label|source was
# re-split into ranges that exclude them, so there is genuinely nothing to carry prior work onto.
BASELINE_UNCARRIED = frozenset({
    "ethiopia|iia|1938-1938",
    "malaysia|iia|1945-1945",
})


def span_of(k):
    yy = re.findall(r"\d{4}", "|".join(str(k).split("|")[2:]))
    return (int(yy[0]), int(yy[-1])) if len(yy) >= 2 else None


def main() -> int:
    for p in (TABLE, APPLIED, QUEUE):
        if not os.path.exists(p):
            print(f"SKIP: {os.path.relpath(p, REPO)} missing — run 23_verdict_carryover.py --write")
            return 0
    with open(TABLE, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    banked = set()
    with open(APPLIED, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            v = json.loads(line).get("verdict")
            if isinstance(v, str):
                try:
                    v = json.loads(v)
                except Exception:
                    continue
            if isinstance(v, dict) and v.get("key"):
                banked.add(v["key"])
    q = json.load(open(QUEUE, encoding="utf-8"))
    q = q if isinstance(q, list) else q.get("assertions", [])
    qkeys = {a.get("key") for a in q if a.get("key")}

    problems = []
    orphans = banked - qkeys
    carried = {r["banked_key"] for r in rows}
    print(f"banked verdicts {len(banked)}   orphaned by re-spanning {len(orphans)}   "
          f"carry rows {len(rows)}")
    print(f"  orphans carried: {len(carried)}   uncarried baseline: {len(BASELINE_UNCARRIED)}")

    # --- A ---
    for k in sorted(orphans - carried - BASELINE_UNCARRIED):
        problems.append(
            f"A banked verdict {k!r} matches no queue key and no carry row — the judgement is lost "
            f"and the assertion will be decided again from scratch. Re-run "
            f"23_verdict_carryover.py --write, or baseline it if nothing overlaps")
    for k in sorted(BASELINE_UNCARRIED & carried):
        problems.append(
            f"A {k!r} is baselined as having nothing to carry to but now has a carry row — remove it "
            f"from BASELINE_UNCARRIED")
    for k in sorted(carried - orphans):
        problems.append(
            f"A carry row for {k!r}, which is NOT orphaned — it matches a queue key directly, so the "
            f"row is stale. Re-run 23_verdict_carryover.py --write")

    for r in rows:
        tag = f"{r['banked_key']} -> {r['queue_key']}"
        # --- B ---
        bs, qs = span_of(r["banked_key"]), span_of(r["queue_key"])
        if not bs or not qs:
            problems.append(f"B {tag}: a key carries no parseable span")
            continue
        byears = set(range(bs[0], bs[1] + 1))
        ov = len(byears & set(range(qs[0], qs[1] + 1)))
        if ov != int(r["overlap_years"]):
            problems.append(
                f"B {tag}: overlap_years is {r['overlap_years']} but the two spans share {ov}")
        if len(byears) != int(r["banked_years"]):
            problems.append(
                f"B {tag}: banked_years is {r['banked_years']} but {bs[0]}-{bs[1]} is {len(byears)}")
        want = ov / len(byears) if byears else 0.0
        if abs(want - float(r["overlap_share"])) > 5e-4:
            problems.append(
                f"B {tag}: overlap_share is {r['overlap_share']} but the spans give {want:.4f}")
        # --- C ---
        if ov == 0:
            problems.append(
                f"C {tag}: zero shared years. Sharing a label and source while sharing no year says "
                f"nothing about the assertion, and such a row would carry prior work onto an "
                f"unrelated span")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1
    print("\nPASS: every orphaned verdict is accounted for, every overlap re-derives, no empty carries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
