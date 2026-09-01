#!/usr/bin/env python3
"""Every defect-registry entry is covered by a re-test, and every re-test names a live entry.

WHY THIS EXISTS (issue 631). `state/data_errors.csv` is where this repo's per-cell adjudications
live, and the sentence they are trusted on is "42 entries / 404 claims still reproduce". That
sentence comes from `pipelines/polity-autoimprove/35_retest_data_errors.py`, which needs the
gitignored layer-B panel and therefore CANNOT run in CI. Until this gate, nothing else did either:
a fabricated entry covered by no re-test left all 90 gates green, and only the hand-run suite
noticed, and only when somebody ran it.

The parallel registry already had this. `validate_source_conventions.py` arm G asserts every
`source_conventions.csv` row has a check in `11_retest_conventions.py`, and states the principle
this gate reuses verbatim: whether a row is COVERED by a re-test is checkable from tracked files
even when whether it is TRUE is not. The two registries are the same kind of object and only one
of them was gated.

WHAT THIS DELIBERATELY DOES NOT CHECK: whether an entry is true, or whether its claims still
reproduce. That needs the panel and stays in the hand-run suite. This gate is about coverage, and
coverage is BIDIRECTIONAL -- an entry with no check is unverified, and a check for an entry that no
longer exists is dead code that reads as coverage.

Importing the re-test module is safe here: verified with the panel absent it imports in 0.26s,
because the panel is only read inside `main()`. If that ever stops being true this gate fails loudly
on the import rather than skipping, since a coverage check that skips when it cannot import is a
coverage check that passes when the thing it measures is broken.

Five checks:
  A. WELL-FORMED. Non-empty, unique `issue_id`; every row carries the registry's columns.
  B. COVERAGE. Every entry has a key in the re-test's CHECKS dict.
  C. NO ORPHAN CHECKS. Every CHECKS key names an entry that still exists.
  D. LIVENESS, both sides. Neither the registry nor CHECKS may be empty -- an empty either side
     makes A-C pass by having nothing to say, which is the failure this repo has paid for before.
  E. THE SUITE IS REACHABLE. The re-test file exists and exposes CHECKS as a dict.
"""
import csv
import importlib.util
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(REPO, "pipelines/polity-autoimprove/state/data_errors.csv")
RETEST = os.path.join(REPO, "pipelines/polity-autoimprove/35_retest_data_errors.py")

# Restated rather than imported: a gate that imports the column list it checks agrees with the
# file by construction. These are the columns an entry needs for the retest and the registry
# readers to work; a row missing one is malformed regardless of what the current file happens to
# have.
REQUIRED_COLUMNS = ("issue_id", "source", "label", "commodity", "summary")


def retest_checks():
    """The CHECKS dict of the re-test suite, or a reason it could not be read."""
    if not os.path.exists(RETEST):
        return None, f"{os.path.relpath(RETEST, REPO)} is missing, so no entry can be covered"
    spec = importlib.util.spec_from_file_location("retest_data_errors", RETEST)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:                                  # noqa: BLE001 - reported, not raised
        return None, (f"{os.path.relpath(RETEST, REPO)} could not be imported "
                      f"({type(exc).__name__}: {exc}), so coverage cannot be established. This is a "
                      f"failure, not a skip: a coverage check that skips on a broken import passes "
                      f"exactly when the thing it measures is broken.")
    checks = getattr(mod, "CHECKS", None)
    if not isinstance(checks, dict):
        return None, (f"{os.path.relpath(RETEST, REPO)} exposes no CHECKS dict, so this gate has no "
                      f"way to tell which entries are re-tested")
    return checks, None


def main():
    problems = []
    if not os.path.exists(REGISTRY):
        print(f"FAIL: {os.path.relpath(REGISTRY, REPO)} not found")
        return 1

    with open(REGISTRY, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    # --- A: well-formed ---
    seen = {}
    for i, r in enumerate(rows, start=2):                     # +2: header, 1-based
        eid = (r.get("issue_id") or "").strip()
        if not eid:
            problems.append(f"A: row {i} has an empty issue_id, so nothing can key a re-test to it")
            continue
        if eid in seen:
            problems.append(f"A: issue_id {eid!r} appears on rows {seen[eid]} and {i}; a duplicate "
                            f"key means one entry's re-test silently stands in for the other's")
        seen[eid] = i
        missing = [c for c in REQUIRED_COLUMNS if c not in r]
        if missing:
            problems.append(f"A: row {i} ({eid}) is missing column(s) {missing} -- a short row "
                            f"appended by a script that knows fewer columns")

    entries = set(seen)
    checks, why = retest_checks()

    # --- E: the suite is reachable ---
    if checks is None:
        problems.append(f"E: {why}")
        checks = {}

    # --- D: liveness, both sides ---
    if not entries:
        problems.append("D: the registry holds no entries. Checks B and C would pass by having no "
                        "subject, so this is reported instead of a clean bill of health.")
    if not checks and why is None:
        problems.append("D: the re-test exposes an EMPTY CHECKS dict, so every entry is uncovered "
                        "while check B has nothing to iterate.")

    # --- B: coverage ---
    if entries and checks:
        for eid in sorted(entries - set(checks)):
            problems.append(
                f"B: {eid} has no check in {os.path.relpath(RETEST, REPO)}, so nothing re-measures "
                f"it. The registry is what this repo's adjudications rest on, and an entry no "
                f"re-test covers is a claim with nothing behind it. Add a CHECKS entry keyed on "
                f"this issue_id.")

        # --- C: no orphan checks ---
        for key in sorted(set(checks) - entries):
            problems.append(
                f"C: {os.path.relpath(RETEST, REPO)} has a check keyed {key!r} but no registry "
                f"entry has that issue_id. A check for a deleted or renamed entry never runs and "
                f"reads as coverage.")

    print(f"registry entries: {len(entries)}   re-test checks: {len(checks)}   "
          f"covered: {len(entries & set(checks))}")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1
    print("\nPASS: every defect-registry entry is covered by a re-test, and every re-test names a "
          "live entry")
    return 0


if __name__ == "__main__":
    sys.exit(main())
