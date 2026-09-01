#!/usr/bin/env python3
"""A fallback route may report on a quarantined series; it may not close one.

WHY THIS EXISTS (issue 627). `reconcile_quarantine.py` decides which quarantined series are
resolved and drops them from `quarantine.csv`. Its authoritative route source, `assertions.json`,
is GITIGNORED per-run state — absent on any fresh checkout — and the tool then falls back to
re-deriving routes through the shared deterministic matcher.

That matcher cannot reproduce an ADJUDICATED routing. Reproducing it is precisely what the
adjudication exists to record. So a row whose candidate was decided rather than derived looks
"route_changed" to the fallback and is dropped and archived as resolved.

Measured 2026-09-01: 10 of 43 quarantine rows carry a candidate the matcher cannot re-derive,
SEVEN of them with a bundle that agrees the route is unchanged. Toggling only that file's presence
moves `rwanda|mitchell|1953-1960` from KEEP to DROP — recorded verdict `uncertain`, basis "the
label is the Rwanda half of the Belgian trust territory", matcher returning `RWA-1922-1962`
against the recorded `RWB-1922-1962` (Ruanda-Urundi, both halves). The archived row would have
carried the reason "the recorded disagreement ... no longer applies" — a statement produced by a
missing file rather than by anything about the data.

Seven of the ten are shielded only because the matcher returns NOTHING for them, which the tool
already treats as "not resolvable — kept". The exposed class is the narrower one where it returns
something DIFFERENT, and which rows those are moves with the alias and span tables — so the count
is a property of today's routing, not a fixed bound.

`quarantine_resolved.csv` is append-only, so a dropped row is recoverable; the damage is that an
open, explicitly uncertain adjudication leaves the queue a human reads, marked resolved, for a
reason that is an artefact. #431 made this write atomic because `quarantine.csv` is not
re-derivable — but atomicity protects against a truncated write, not against a complete write of
the wrong row set.

Read with `ast`, not grep, so a guard that is present but unreachable fails. Four arms:
  A. ONE destructive write of the quarantine file, so there is a single path to guard.
  B. A module-level guard on the authoritative input's absence, exiting NON-ZERO, before it.
  C. The guard sits AFTER the --dry-run exit. Reporting on fallback routes is legitimate and must
     stay possible; only RESOLVING on them is not. A guard placed before the dry-run exit would
     make the tool unable to explain itself, which is a different bug, not a stricter one.
  D. An explicit opt-out exists, so the refusal is a default rather than a wall.
"""
import ast
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "pipelines", "polity-autoimprove", "reconcile_quarantine.py")

# Restated, not imported: a gate that imports the names it checks agrees by construction.
AUTHORITATIVE = "ASSERTIONS"
DEST = "QUARANTINE"
OPT_OUT = "--allow-fallback-routes"
DRY_FLAG = "DRY"


def _seg(src, node):
    return ast.get_source_segment(src, node) or ""


def main():
    if not os.path.exists(TOOL):
        print(f"FAIL: {TOOL} not found")
        return 1
    src = open(TOOL, encoding="utf-8").read()
    tree = ast.parse(src)
    problems = []

    # A. one destructive write
    writes = [n.lineno for n in ast.walk(tree)
              if isinstance(n, ast.Call)
              and isinstance(n.func, ast.Name) and n.func.id == "write_csv_atomic"
              and n.args and isinstance(n.args[0], ast.Name) and n.args[0].id == DEST]
    if len(writes) != 1:
        problems.append(
            f"A: expected exactly ONE write_csv_atomic({DEST}, ...), found {len(writes)} at "
            f"{writes}. Each destructive path needs its own guard, so this gate's single-path "
            f"assumption no longer holds.")
    write_line = writes[0] if writes else None

    # the --dry-run exit, which the guard must follow
    dry_exits = [n.lineno for n in tree.body
                 if isinstance(n, ast.If) and DRY_FLAG in _seg(src, n.test)
                 and "exit" in _seg(src, n).lower()]

    # B + C + D. the refusal
    guards = []
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        test = _seg(src, node.test)
        if AUTHORITATIVE not in test or "os.path.exists" not in test:
            continue
        body = _seg(src, node)
        if "exit" not in body.lower():
            continue
        if "sys.exit(0)" in body or "SystemExit(0)" in body:
            problems.append(
                f"B: the refusal at line {node.lineno} exits ZERO, so a caller cannot tell it "
                f"refused — as invisible as the silent resolution it replaced.")
            continue
        if OPT_OUT not in test and OPT_OUT not in body:
            problems.append(
                f"D: the refusal at line {node.lineno} names no opt-out. Without one the tool "
                f"cannot be run deliberately on fallback routes, which turns a default into a "
                f"wall and invites the guard being deleted rather than passed.")
        guards.append(node.lineno)

    if not guards:
        problems.append(
            f"B: no module-level guard found testing `os.path.exists({AUTHORITATIVE})` and "
            f"exiting non-zero. Without it, running the tool while assertions.json is absent "
            f"resolves quarantined series on re-derived routes the deterministic matcher cannot "
            f"produce for an adjudicated routing — 10 of 43 rows were exposed on the 2026-09-01 "
            f"measurement, 7 with a bundle agreeing the route was unchanged. See issue 627.")
    else:
        g = min(guards)
        if write_line is not None and g > write_line:
            problems.append(
                f"C: the guard is at line {g} but the destructive write is at line {write_line}. "
                f"A refusal after the write refuses nothing.")
        if dry_exits and g < min(dry_exits):
            problems.append(
                f"C: the guard at line {g} precedes the --dry-run exit at line {min(dry_exits)}, "
                f"so --dry-run can no longer report on fallback routes. Reporting is legitimate; "
                f"only resolving on them is not.")
        if not dry_exits:
            problems.append(
                "C: no --dry-run exit found, so the guard cannot be positioned relative to it. "
                "Inspection without writing is what makes the refusal actionable.")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1
    print("\nPASS: reconcile_quarantine.py refuses to resolve on fallback routes when "
          "assertions.json is absent, and --dry-run still reports")
    return 0


if __name__ == "__main__":
    sys.exit(main())
