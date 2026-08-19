#!/usr/bin/env python3
"""No tool may TRUNCATE a tracked state file that holds work nobody can re-derive.

`open(path, "w")` and `pandas.to_csv(path)` both truncate on open, so a failure between the truncate
and the last row leaves a tracked file half-written. That has already cost this repository two state
files. Every tool from `16_source_splices.py` onward builds its output in memory and replaces it
atomically; issue 431 found the lesson had never reached the older tools and named the four sites
where it mattered, `pipelines/polity-autoimprove/atomic.py` closed them, and this gate is what stops
a fifth from appearing.

WHY A GATE AND NOT JUST THE FIX (issue 431). The four sites were found by grepping for
`open(x, "w")`. That detector is a floor, not a census, and the issue said so: it cannot see
`pandas.to_csv`, `pathlib.write_text`, or a `json.dump` whose `open` sits on another line. Re-swept
with an AST instead of a regex, the repository has **48 write sites, not 16** -- the regex missed
about forty, nearly all of them `to_csv`. Every one of those forty writes a REGENERABLE output, so
nothing was actually exposed, but the margin was luck rather than design: a `to_csv(LEDGER)` added
tomorrow would have been invisible to the check that found the original four.

WHAT IS PROTECTED, AND WHY EACH. Only files whose content cannot be rebuilt by re-running a tool.
A truncated measurement table (`magnitude_outliers.csv`, `yield_corrections.csv`, and the other
regenerable tables issue 431 lists) is repaired by regenerating it, and `atomic.py`'s own docstring
declines to cover them on exactly that ground -- so this gate does not either. Overreaching here
would make the gate a nuisance that gets weakened, which is worse than a narrow one that holds.

HOW "ATOMIC" IS RECOGNISED, and why the rule is phrased negatively. An atomic writer never names the
destination in its truncating call -- it truncates a temp file in the same directory and then
`os.replace`s it onto the target. So the check does not try to prove a write is safe; it looks for a
truncating call whose target RESOLVES to a protected path, which an atomic writer cannot produce.
`write_csv_atomic(LEDGER, ...)` therefore passes without being special-cased, and a hand-rolled
mkstemp/replace pair passes too.

APPEND IS NOT TRUNCATION. `verdicts_applied.jsonl` is opened `"a"`, which cannot lose the existing
record, and issue 431's first pass wrongly listed it as exposed. Append modes are allowed, and the
gate asserts that file is never opened `"w"` rather than that it is never opened at all.

Checks:
  A. no truncating write resolves to a protected path.
  B. the protected registry still matches `atomic.py`'s docstring claim about which files hold
     adjudications, so the two cannot drift apart silently.
  C. the AST sweep still finds every write site it found when this gate was written -- a floor on
     coverage, so that a rewrite which stops parsing (and therefore stops checking) is visible.
"""
import ast
import glob
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Files holding banked judgements that no re-run can reproduce. The reason is recorded per file
# because a future maintainer must be able to tell whether a new file belongs in here.
PROTECTED = {
    "review_ledger.csv": "every verification decision ever banked; three separate tools write it, "
                         "and two of them read it, edit it in memory and write it back over itself",
    "quarantine.csv": "quarantined series and the reason each was quarantined",
    "quarantine_resolved.csv": "the record of quarantines that were lifted",
    "applied_aliases.csv": "routing decisions confirmed by prior runs; the matcher reads this, not "
                           "the derived data/final/label_alias_map.csv",
    "source_conventions.csv": "verified source conventions with the evidence that established each",
    "suspect_wiki_pages.csv": "outstanding wiki review findings",
    "wiki_notes_queue.csv": "outstanding wiki notes",
    "wiki_findings_resolved.csv": "wiki findings already adjudicated",
    "data_errors.csv": "confirmed source-data defects with their diagnosis",
    "verdicts_applied.jsonl": "the applied-verdict record issue 308 treats as the authority; "
                              "APPEND-only, never truncated",
}

# Calls that truncate their destination on open.
TRUNCATING_SINKS = {"to_csv", "to_parquet", "to_json", "write_text", "write_bytes"}
# A target expression mentioning any of these is a temp handle, i.e. the atomic pattern.
TEMP_HINTS = ("tmp", "fd", "tempfile", "TMP", "StringIO", "buf")

# C. floor on the sweep's coverage, so a parse regression cannot quietly disable this gate.
MIN_WRITE_SITES = 40


def _consts(tree) -> dict:
    out = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            try:
                out[n.targets[0].id] = ast.unparse(n.value)
            except Exception:
                pass
    return out


def _resolve(expr: str, consts: dict, depth: int = 0) -> str:
    """follow NAME -> its assigned expression, a few levels, so `to_csv(LEDGER)` becomes the path"""
    e = expr.strip()
    if depth > 4:
        return e
    if e in consts:
        return _resolve(consts[e], consts, depth + 1)
    return e


def _write_sites(path: str):
    """(lineno, kind, target_expression) for every call that truncates its destination"""
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except (SyntaxError, UnicodeDecodeError):
        return None, []
    sites = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else None)
        target = None
        if name == "open":
            mode = None
            if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                mode = n.args[1].value
            for kw in n.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = kw.value.value
            # APPEND IS NOT TRUNCATION -- see the docstring. Only "w"/"x" destroy what is there.
            if mode and ("w" in mode or "x" in mode) and n.args:
                target = ast.unparse(n.args[0])
        elif name in TRUNCATING_SINKS:
            if n.args:
                target = ast.unparse(n.args[0])
            else:
                for kw in n.keywords:
                    if kw.arg in ("path_or_buf", "path"):
                        target = ast.unparse(kw.value)
        if target is None:
            continue
        sites.append((n.lineno, name, target))
    return tree, sites


def main() -> int:
    problems = []
    files = sorted(glob.glob(os.path.join(REPO, "pipelines/**/*.py"), recursive=True) +
                   glob.glob(os.path.join(REPO, "scripts/*.py")))
    n_sites = 0
    n_scanned = 0
    for p in files:
        # selftest_gates.py writes ~80 files into its own temp scratch tree by design.
        if os.path.basename(p) == "selftest_gates.py":
            continue
        tree, sites = _write_sites(p)
        if tree is None:
            problems.append(f"C {os.path.relpath(p, REPO)}: does not parse, so its write sites are "
                            f"unchecked")
            continue
        n_scanned += 1
        consts = _consts(tree)
        for lineno, kind, target in sites:
            if any(h in target for h in TEMP_HINTS):      # the atomic pattern
                continue
            n_sites += 1
            resolved = _resolve(target, consts)
            for base, why in PROTECTED.items():
                if base in resolved:
                    problems.append(
                        f"A {os.path.relpath(p, REPO)}:{lineno}: {kind}({target}) truncates "
                        f"{base}, which holds {why}. Build the rows fully and replace atomically "
                        f"(pipelines/polity-autoimprove/atomic.py::write_csv_atomic); a failure "
                        f"part-way through this write loses the file rather than corrupting it")
    # --- B. the registry must not drift from atomic.py's own account ---
    doc = os.path.join(REPO, "pipelines/polity-autoimprove/atomic.py")
    if not os.path.exists(doc):
        problems.append("B pipelines/polity-autoimprove/atomic.py is gone, so the shared atomic "
                        "writer these tools depend on no longer exists")
    else:
        text = open(doc, encoding="utf-8").read()
        for base in ("review_ledger.csv", "quarantine.csv"):
            if base not in text:
                problems.append(f"B atomic.py no longer mentions {base}, so its docstring and this "
                                f"gate's registry have drifted apart")
    # --- C. coverage floor ---
    if n_sites < MIN_WRITE_SITES:
        problems.append(f"C the AST sweep found only {n_sites} truncating write site(s), below the "
                        f"floor of {MIN_WRITE_SITES} recorded when this gate was written. Either a "
                        f"lot of code was deleted or the sweep stopped seeing a whole call form -- "
                        f"and a sweep that sees nothing passes this gate for the wrong reason")

    print(f"{n_sites} truncating write site(s) across {n_scanned} module(s); "
          f"{len(PROTECTED)} protected file(s)")
    if problems:
        print(f"FAIL: {len(problems)} non-atomic state-write problem(s)", file=sys.stderr)
        for pr in problems[:30]:
            print("  - " + pr, file=sys.stderr)
        return 1
    print("PASS: no tool truncates a tracked state file that holds unregenerable adjudications")
    return 0


if __name__ == "__main__":
    sys.exit(main())
