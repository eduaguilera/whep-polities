#!/usr/bin/env python3
"""When re-spanning renames a queue key, what carries the verdict already banked under the old one?

Assertion keys are `label|source|first-last`. Re-deriving the queue re-splits spans, so a verdict
banked under `algeria|iia|1920-1945` no longer matches anything when the queue starts carrying
`algeria|iia|1919-1945`. Measured today: 52 of 460 banked verdicts are orphaned this way, and every
single one is span drift -- `label|source gone entirely` is ZERO. The evidence did not change and the
judgement did not become wrong; only the name it was filed under did.

Issue 308 diagnosed exactly why that matters, and this script is the answer to its last sentence:

    "So quarantines have a carrier. Confirms do not. 48 of the 51 orphans are ordinary banked
     verdicts with no tracked artifact keyed to find them by, and those are simply redone."

`quarantine.csv` is tracked and keyed independently, so a later verifier finds prior quarantine work
and cites it -- that is how the India rice-paddy break survived a re-split. An ordinary `confirm` has
no such file, so re-spanning silently sends it back to the queue as `pending` and it is paid for twice.

WHAT THIS DOES AND DELIBERATELY DOES NOT DO. It writes the mapping from each orphaned banked key to the
queue keys that overlap it, with the overlap measured. It does NOT re-bank anything. A re-split is
sometimes a response to a finding -- issue 308's India case re-split `india|mitchell|1915-1937` into
seven spans while the new `1914-1936` still contains the 1928/29 break that got the original
quarantined -- so auto-carrying a confirm across a re-span would launder a judgement onto a span nobody
judged. The table is evidence for the next verifier, not a verdict.

OVERLAP IS PER PAIR, NOT PER KEY. `brazil|mitchell|1879-1960` was banked as one span; the queue now
carries `1909-1960`, `1903-1908` and `1879-1902`. All three inherit the same prior verdict as evidence
and each is a separate row, because the prior judgement covered all three and none of them individually.
A queue key with NO overlap is not emitted: `algeria|iia|1909-1918` shares a label and source with the
banked `1920-1945` and shares not one year, so prior work on it says nothing.

Usage:
  python3 pipelines/polity-autoimprove/23_verdict_carryover.py            # report only
  python3 pipelines/polity-autoimprove/23_verdict_carryover.py --write    # refresh the table
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import tempfile
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "verdict_carryover.csv")
APPLIED = os.path.join(STATE, "verdicts_applied.jsonl")
QUEUE = os.path.join(STATE, "assertions.json")

# ONE ROW PER BANKED VERDICT, not per carry pair. The queue (`assertions.json`) is GITIGNORED, so a
# gate cannot recompute which verdicts are orphaned -- it can only read this table and the tracked
# applied log. So the table must state the outcome for EVERY banked key, and the carries are folded
# into one column. The first version emitted only orphan->queue pairs and its gate silently SKIPPED in
# CI for want of the queue, which the selftest reported as the gate failing to catch its own defect.
COLS = ["banked_key", "label", "source", "banked_span", "queue_state", "n_carries",
        "carries", "banked_verdict"]


def parse_key(k):
    """`label|source|first-last` -> (label, source, first, last). Spans can be absent or None-None."""
    parts = str(k).split("|")
    if len(parts) < 3:
        return None
    label, source, span = parts[0], parts[1], "|".join(parts[2:])
    yy = re.findall(r"\d{4}", span)
    if len(yy) < 2:
        return (label, source, None, None)
    return (label, source, int(yy[0]), int(yy[-1]))


def applied_keys():
    """key -> verdict string, from the applied log. The key is NESTED under `verdict`."""
    out = {}
    if not os.path.exists(APPLIED):
        return out
    with open(APPLIED, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            v = rec.get("verdict")
            if isinstance(v, str):
                try:
                    v = json.loads(v)
                except Exception:
                    continue
            if isinstance(v, dict) and v.get("key"):
                out[v["key"]] = str(v.get("verdict") or v.get("confirm_kind") or "").strip()
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help=f"refresh {os.path.relpath(OUT, REPO)}")
    args = ap.parse_args()

    if not os.path.exists(QUEUE):
        print(f"SKIP: {os.path.relpath(QUEUE, REPO)} missing — run 00_intake.py")
        return 0
    banked = applied_keys()
    q = json.load(open(QUEUE, encoding="utf-8"))
    q = q if isinstance(q, list) else q.get("assertions", [])
    # A dict keyed on `key` DROPS one entry of every colliding pair, which is not hypothetical:
    # `ethiopia|iia|None-None` shipped twice with different candidates (ETH-1907-1936 and
    # ETH-1936-1941) and this line silently discarded one of them on every run. 00_intake.py now
    # disambiguates collisions and raises if any survive, so reaching this branch means the queue
    # was produced by an intake predating that fix -- refuse it rather than quietly halving it.
    _keys = [a["key"] for a in q if a.get("key")]
    _dupes = sorted(k for k, n in Counter(_keys).items() if n > 1)
    if _dupes:
        print(f"FAIL: {len(_dupes)} assertion key(s) appear more than once in "
              f"{os.path.relpath(QUEUE, REPO)}: {_dupes[:5]}. A key maps to one ledger row and one "
              f"evidence bundle; carrying verdicts across a non-unique key drops one of each pair "
              f"(issue 308). Re-run 00_intake.py, which disambiguates them.", file=sys.stderr)
        return 1
    qstatus = {a["key"]: str(a.get("status") or "") for a in q if a.get("key")}

    by_ls = defaultdict(list)
    for k in qstatus:
        p = parse_key(k)
        if p:
            by_ls[(p[0], p[1])].append((k, p[2], p[3]))

    orphans = [k for k in banked if k not in qstatus]
    rows, no_overlap = [], []
    for bk in sorted(orphans):
        p = parse_key(bk)
        if not p:
            continue
        label, source, b0, b1 = p
        cands = by_ls.get((label, source), [])
        if not cands:
            no_overlap.append((bk, "label|source gone from the queue"))
            continue
        span_years = set(range(b0, b1 + 1)) if b0 is not None else set()
        emitted = 0
        for qk, q0, q1 in sorted(cands):
            if q0 is None or not span_years:
                continue
            ov = len(span_years & set(range(q0, q1 + 1)))
            if ov == 0:
                continue          # shares a label and source but not one year -- says nothing
            emitted += 1
            rows.append({
                "banked_key": bk, "queue_key": qk, "label": label, "source": source,
                "banked_span": f"{b0}-{b1}", "queue_span": f"{q0}-{q1}",
                "overlap_years": ov, "banked_years": len(span_years),
                "overlap_share": f"{ov / len(span_years):.4f}",
                "banked_verdict": banked[bk], "queue_status": qstatus.get(qk, ""),
            })
        if not emitted:
            no_overlap.append((bk, "same label|source in the queue but no shared year"))

    per_key = defaultdict(list)
    for r in rows:
        per_key[r["banked_key"]].append(r)

    out = []
    for bk in sorted(banked):
        p = parse_key(bk)
        if not p:
            continue
        label, source, b0, b1 = p
        if bk in qstatus:
            state, carries = "matched", []
        elif bk in per_key:
            state = "carried"
            carries = [f"{r['queue_key']}@{r['overlap_share']}"
                       for r in sorted(per_key[bk], key=lambda x: -float(x["overlap_share"]))]
        else:
            state, carries = "uncarried", []
        out.append({
            "banked_key": bk, "label": label, "source": source,
            "banked_span": f"{b0}-{b1}" if b0 is not None else "",
            "queue_state": state, "n_carries": len(carries),
            "carries": ";".join(carries), "banked_verdict": banked[bk],
        })
    rows = out
    from collections import Counter as _C
    print("\n  per-verdict outcome:", dict(_C(r["queue_state"] for r in rows)))

    if args.write:
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(OUT), suffix=".tmp")
        os.close(fd)
        with open(tmp, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS)
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, OUT)
        print(f"\nwrote {len(rows)} carry rows to {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
