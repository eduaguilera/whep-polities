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
from collections import defaultdict

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


STATES = ("matched", "carried", "uncarried")


def main() -> int:
    # NOTE: assertions.json (the queue) is GITIGNORED and absent in CI, so this gate reads ONLY the
    # tracked table and the tracked applied log. That is why the table carries a `queue_state` per
    # banked verdict instead of just orphan->queue pairs: the outcome has to be stated, because it
    # cannot be recomputed here. The first version of this gate did depend on the queue and SKIPPED in
    # CI, which the selftest correctly reported as the gate failing to catch its own injected defect.
    for p in (TABLE, APPLIED):
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

    problems = []
    listed = {r["banked_key"] for r in rows}
    by_state = defaultdict(set)
    for r in rows:
        by_state[r["queue_state"]].add(r["banked_key"])
    print(f"banked verdicts in the applied log: {len(banked)}   rows in the table: {len(rows)}")
    print("  " + "  ".join(f"{k}={len(v)}" for k, v in sorted(by_state.items())))

    # --- A: nothing lost ---
    for k in sorted(banked - listed):
        problems.append(
            f"A banked verdict {k!r} has no row in the table, so nothing records whether re-spanning "
            f"orphaned it. That is how a judgement silently returns to the queue as `pending` and is "
            f"paid for twice — re-run 23_verdict_carryover.py --write")
    for k in sorted(listed - banked):
        problems.append(
            f"A the table lists {k!r}, which is not in the applied log — a stale row; re-run the "
            f"generator")
    uncarried = by_state.get("uncarried", set())
    for k in sorted(uncarried - BASELINE_UNCARRIED):
        problems.append(
            f"A {k!r} is orphaned with NOTHING to carry its verdict to and is not baselined. Either a "
            f"queue key overlapping it exists and the table is stale, or the judgement is genuinely "
            f"unreachable and must be recorded as such")
    for k in sorted(BASELINE_UNCARRIED - uncarried):
        problems.append(
            f"A {k!r} is baselined as uncarried but is not any more — remove it from "
            f"BASELINE_UNCARRIED, saying what it now carries to")

    for r in rows:
        bk = r["banked_key"]
        if r["queue_state"] not in STATES:
            problems.append(f"B {bk}: unknown queue_state {r['queue_state']!r}, not in {STATES}")
            continue
        n = int(r["n_carries"])
        parts = [c for c in (r["carries"] or "").split(";") if c]
        if n != len(parts):
            problems.append(f"B {bk}: n_carries={n} but the carries column names {len(parts)}")
        if r["queue_state"] != "carried" and parts:
            problems.append(
                f"B {bk}: state is `{r['queue_state']}` but it carries {len(parts)} queue key(s)")
        if r["queue_state"] == "carried" and not parts:
            problems.append(f"B {bk}: state is `carried` with no carries listed")
        # --- C: every carry must share years, and the share must re-derive from the two spans ---
        bs = span_of(bk)
        for c in parts:
            qk, _, sh = c.rpartition("@")
            qs = span_of(qk)
            if not bs or not qs:
                problems.append(f"C {bk} -> {qk}: a key carries no parseable span")
                continue
            byears = set(range(bs[0], bs[1] + 1))
            ov = len(byears & set(range(qs[0], qs[1] + 1)))
            if ov == 0:
                problems.append(
                    f"C {bk} -> {qk}: zero shared years. Sharing a label and source while sharing no "
                    f"year says nothing about the assertion, and such a carry would put prior work "
                    f"onto an unrelated span")
                continue
            want = ov / len(byears)
            try:
                got = float(sh)
            except ValueError:
                problems.append(f"C {bk} -> {qk}: overlap share {sh!r} is not a number")
                continue
            if abs(want - got) > 5e-4:
                problems.append(
                    f"C {bk} -> {qk}: recorded overlap {got:.4f} but the two spans give {want:.4f}")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1
    print("\nPASS: every banked verdict is accounted for, every carry shares years and re-derives")
    return 0


if __name__ == "__main__":
    sys.exit(main())
