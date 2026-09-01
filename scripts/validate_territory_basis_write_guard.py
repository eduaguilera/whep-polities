#!/usr/bin/env python3
"""`04_territory_basis.py` cannot publish a column the run was unable to compute.

WHY THIS EXISTS (issue 573). Two of that script's inputs are untracked -- `matched_rows.parquet`
(layer B, outside the repo) and `territorial_flagged.json` (per-run, written by stage 02 and
gitignored). When one is absent the column it feeds does not go missing, it COLLAPSES to a
constant: `priority_review` to False, `layerb_data_rows` to 0. The write then publishes that
collapse over real values and exits 0.

Measured on 2026-09-01 with `territorial_flagged.json` absent: `priority_review` went from 116
True to 27 True -- 89 flags deleted, silently -- and those flags are read by
`pipelines/footnote-territory-extraction/validate_proposals.py`. Issue 573 records that exactly
this regeneration was run and nearly committed while investigating something else. The file's
own `--check` cannot catch it, because the same missing input makes the check SKIP that column:
it is green precisely where it cannot see.

The asymmetry the guard encodes, and what this gate protects: a CHECK may safely degrade on a
missing input, since comparing fewer columns is only weaker. A WRITE may not -- publishing fewer
columns' worth of truth is wrong rather than weak, and it overwrites the only copy. So the same
condition that makes `--check` skip a column must make the write refuse.

This gate is static because a dynamic one would have to attempt the destructive write to observe
it being refused, and a test that can leave a collapsed file behind on interruption is a poor
trade for what it adds. It reads the module with `ast` rather than by grep, so a guard that is
present but UNREACHABLE -- nested inside a function, or placed after the write -- fails here.

Four checks:
  A. ONE WRITE. Exactly one module-level write of the destination, so there is one path to guard.
  B. THE VOLATILE MAP is declared at module level and names both untracked inputs.
  C. THE GUARD EXISTS, at module level, testing the missing-input set and raising a NON-ZERO exit.
  D. THE GUARD PRECEDES THE WRITE. A refusal after the write refuses nothing.
"""
import ast
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(REPO, "pipelines", "polity-autoimprove", "04_territory_basis.py")

# Restated here rather than imported: a gate that imports the constant it checks agrees with the
# tool by construction. If either name is renamed, this gate must be updated deliberately.
VOLATILE_COLUMNS = {"layerb_data_rows", "priority_review"}
VOLATILE_INPUTS = {"matched_rows.parquet", "territorial_flagged.json"}
MISSING_NAME = "_missing"
DEST_NAME = "_DEST"


def _seg(src, node):
    return ast.get_source_segment(src, node) or ""


def main():
    if not os.path.exists(TOOL):
        print(f"FAIL: {TOOL} not found")
        return 1

    src = open(TOOL, encoding="utf-8").read()
    tree = ast.parse(src)
    problems = []

    # A. exactly one module-level write of the destination
    writes = []
    for node in tree.body:
        for sub in ast.walk(node):
            if (isinstance(sub, ast.Call)
                    and isinstance(sub.func, ast.Attribute)
                    and sub.func.attr == "to_csv"
                    and sub.args
                    and isinstance(sub.args[0], ast.Name)
                    and sub.args[0].id == DEST_NAME):
                writes.append((node, sub.lineno))
    if len(writes) != 1:
        problems.append(
            f"A: expected exactly ONE write of {DEST_NAME} at module level, found {len(writes)} "
            f"at line(s) {[ln for _, ln in writes]}. Each write needs its own guard, so this "
            f"gate's single-path assumption no longer holds -- guard the new write and update "
            f"this check.")
    write_line = writes[0][1] if writes else None

    # B. the volatile map, at module level, naming both untracked inputs
    vol = [n for n in tree.body
           if isinstance(n, ast.Assign)
           and any(getattr(t, "id", None) == "_VOLATILE" for t in n.targets)]
    if not vol:
        problems.append(
            "B: no module-level `_VOLATILE` assignment. It names which columns depend on "
            "untracked inputs; without it neither the check's skip list nor the write's refusal "
            "has a source of truth.")
    else:
        text = _seg(src, vol[0])
        for col in sorted(VOLATILE_COLUMNS):
            if col not in text:
                problems.append(f"B: `_VOLATILE` no longer names the column `{col}`.")
        for inp in sorted(VOLATILE_INPUTS):
            if inp not in text:
                problems.append(
                    f"B: `_VOLATILE` no longer names the untracked input `{inp}`. If the input "
                    f"became tracked, this gate and issue 573 both need updating.")

    # C + D. a module-level refusal, testing the missing set, exiting non-zero, before the write
    guards = []
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        if MISSING_NAME not in _seg(src, node.test):
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.Raise) and "SystemExit" in _seg(src, sub):
                code = _seg(src, sub)
                if "SystemExit(0)" in code:
                    problems.append(
                        f"C: the refusal at line {node.lineno} exits ZERO, so a caller cannot "
                        f"tell it refused. A silent refusal and a silent overwrite are equally "
                        f"invisible to a script that checks the exit status.")
                else:
                    guards.append(node.lineno)
                break
    if not guards:
        problems.append(
            f"C: no module-level guard found that tests `{MISSING_NAME}` and raises SystemExit. "
            f"Without it, running the tool while an untracked input is absent overwrites the "
            f"committed column with its collapsed value and exits 0 -- 89 `priority_review` "
            f"flags on the 2026-09-01 measurement. See issue 573.")
    elif write_line is not None and min(guards) > write_line:
        problems.append(
            f"D: the guard is at line {min(guards)} but the write is at line {write_line}. "
            f"A refusal that runs after the write refuses nothing -- the file is already "
            f"overwritten.")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: 04_territory_basis.py refuses to write when an untracked input is absent, "
          "and the refusal is reachable and precedes the write")
    return 0


if __name__ == "__main__":
    sys.exit(main())
