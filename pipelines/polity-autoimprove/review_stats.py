#!/usr/bin/env python3
"""Measure the blind review, from the banked verdict archive (issue #27).

The verification pipeline's quality claim rests on a blind second verifier
disagreeing when the first verdict is wrong. That claim was never MEASURED
against the archive: nothing reported how much of the population is actually
second-checked, and nothing recorded WHICH model or WHICH lens produced each
review, so "does disagreement rise when the reviewer is decorrelated from the
verifier?" could not be answered at all.

This script answers the measurable part, deterministically, from
state/verdicts_applied.jsonl:

  * review COVERAGE, overall and for the population that matters — confident
    confirms, the only class the sampler can skip;
  * AGREEMENT, sliced by (verify_model -> review_model) and by review lens, so
    the decorrelation introduced in verify_assertions.workflow.js can be
    compared against the correlated same-model baseline it replaced;
  * the disagreements themselves, with what each side concluded.

It deliberately does NOT report an error rate, because agreement is evidence of
CONSISTENCY, not of truth: two agents can be wrong the same way, which is the
whole point of issue #27. The only thing that yields a real error rate is a
human scoring a sample by hand — `--audit-sample N` writes exactly that sample
(deterministic, seeded by key hash, so the same N rows come back every run) with
blank columns for a human verdict.

Not a CI gate: the archive is an append-only history of decisions, so there is
no invariant here to enforce — a bad agreement rate is a finding to act on, not
a build to break.
"""
import argparse
import collections
import csv
import hashlib
import json
import os

H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")
ARCHIVE = os.path.join(H, "verdicts_applied.jsonl")
AUDIT_OUT = os.path.join(H, "audit_sample_banked.csv")

# Reviews banked before the reviewer returned a full VERDICT object used a
# flatter schema ({agree, own_verdict, own_polity_code, reason}); they are real
# reviews and are counted, but they carry no model/lens and their agreement was
# self-declared by the reviewer rather than compared in code.
LEGACY_KEYS = {"agree", "own_verdict"}


def load(path):
    if not os.path.exists(path):
        raise SystemExit(f"no archive at {path}")
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def is_legacy(review):
    return bool(review) and not review.get("verdict") and LEGACY_KEYS & set(review)


def agreed(rec):
    """True/False/None(=unknown) for one record's review outcome."""
    r = rec.get("review")
    if not r:
        return None
    if is_legacy(r):
        return bool(r.get("agree"))
    if "review_agrees" in rec:
        return bool(rec["review_agrees"])
    return None


def pct(n, d):
    return "n/a" if not d else f"{100.0 * n / d:.1f}%"


def report(rows):
    v = [r for r in rows if r.get("verdict")]
    reviewed = [r for r in v if r.get("review")]
    legacy = [r for r in reviewed if is_legacy(r["review"])]
    print(f"banked verdicts:            {len(v)}")
    print(f"  carrying a review:        {len(reviewed)}  ({pct(len(reviewed), len(v))})"
          f"   [{len(legacy)} in the pre-VERDICT reviewer schema]")

    by_verdict = collections.Counter(r["verdict"].get("verdict") for r in v)
    print("  by verdict:               " + ", ".join(f"{k}={n}" for k, n in by_verdict.most_common()))

    # the population the sampler can skip: confident confirms
    cc = [r for r in v if r["verdict"].get("verdict") == "confirm"
          and r["verdict"].get("confidence") != "low"]
    ccr = [r for r in cc if r.get("review")]
    print(f"\nconfident confirms:         {len(cc)}")
    print(f"  second-checked:           {len(ccr)}  ({pct(len(ccr), len(cc))})")
    print(f"  NEVER second-checked:     {len(cc) - len(ccr)}  ({pct(len(cc) - len(ccr), len(cc))})"
          "   <- the confident-wrong-confirm exposure")

    ok = sum(1 for r in reviewed if agreed(r) is True)
    no = sum(1 for r in reviewed if agreed(r) is False)
    unk = len(reviewed) - ok - no
    print(f"\nagreement among reviewed:   {ok} agree / {no} disagree"
          f"{f' / {unk} unknown' if unk else ''}   ({pct(ok, ok + no)} agree)")
    print("  agreement measures CONSISTENCY, not truth (issue #27):"
          " a correlated pair agrees when both are wrong.")

    def slice_by(name, keyfn):
        buckets = collections.defaultdict(lambda: [0, 0])
        for r in reviewed:
            a = agreed(r)
            if a is None:
                continue
            buckets[keyfn(r)][0 if a else 1] += 1
        print(f"\nby {name}:")
        if not buckets:
            print("  (nothing recorded)")
        for k in sorted(buckets, key=str):
            a, d = buckets[k]
            print(f"  {str(k):34} {a} agree / {d} disagree   ({pct(d, a + d)} disagreement)")

    slice_by("verifier -> reviewer model",
             lambda r: f"{r.get('verify_model') or '?'} -> {r.get('review_model') or '?'}")
    slice_by("reviewer lens", lambda r: r.get("review_lens") or "(none: same instructions)")

    dis = [r for r in reviewed if agreed(r) is False]
    if dis:
        print(f"\ndisagreements ({len(dis)}) — each went to quarantine:")
        for r in dis:
            a, b = r["verdict"], r["review"]
            bv = b.get("verdict") or b.get("own_verdict") or "?"
            bp = b.get("polity_code") or b.get("own_polity_code") or ""
            print(f"  {a['key'][:46]:46} {a.get('verdict')} {a.get('polity_code') or '':16}"
                  f" vs {bv} {bp}")

    unmeasurable = sum(1 for r in reviewed if agreed(r) is not None and not r.get("review_model"))
    if unmeasurable:
        print(f"\nNOTE: {unmeasurable} reviewed verdicts predate model/lens recording, so their"
              "\n      correlation cannot be assessed retrospectively. Re-verification stamps"
              "\n      verify_model/review_model/review_lens from now on.")


def audit_sample(rows, n):
    """Deterministic human-audit sample of BANKED CONFIRMS (option 4 of #27).

    Seeded by md5 of the assertion key, so the same rows are drawn every run and
    a partially scored file can be re-generated without losing its place.
    """
    cand = [r for r in rows
            if r.get("verdict", {}).get("verdict") == "confirm" and r["verdict"].get("key")]
    cand.sort(key=lambda r: hashlib.md5(r["verdict"]["key"].encode()).hexdigest())
    pick = cand[:n]
    cols = ["key", "polity_code", "confidence", "confirm_kind", "second_checked",
            "evidence_used", "basis", "human_verdict", "human_reason"]
    with open(AUDIT_OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in pick:
            v = r["verdict"]
            w.writerow({
                "key": v["key"], "polity_code": v.get("polity_code") or "",
                "confidence": v.get("confidence") or "",
                "confirm_kind": v.get("confirm_kind") or "",
                "second_checked": "yes" if r.get("review") else "no",
                "evidence_used": "|".join(v.get("evidence_used") or []),
                "basis": (v.get("basis") or "")[:1200],
                "human_verdict": "", "human_reason": "",
            })
    print(f"\nhuman-audit sample: {len(pick)} banked confirms -> {AUDIT_OUT}"
          "\n  fill human_verdict (correct/wrong/uncertain) BY HAND; an agent scoring it"
          "\n  reintroduces exactly the correlated error this sample exists to measure.")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--archive", default=ARCHIVE)
    ap.add_argument("--audit-sample", type=int, metavar="N",
                    help="also write a deterministic N-row human-audit sample of banked confirms")
    a = ap.parse_args()
    rows = load(a.archive)
    report(rows)
    if a.audit_sample:
        audit_sample(rows, a.audit_sample)


if __name__ == "__main__":
    main()
