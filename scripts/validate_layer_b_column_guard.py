#!/usr/bin/env python3
"""Every layer-B read renames the column whose NAME lies about its contents.

WHY THIS EXISTS. The consolidated layer-B parquet
(`~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet`, `WHEP_LAYERB`) has a column
literally named `polity_code` that does NOT hold polity codes. It holds lowercase ISO
codes. Measured on the current file, 2026-08-17:

    192,670 rows; 165,581 non-null `polity_code`; 166 distinct values;
    99.37% of them exactly `lower(iso3c)`; 0 of the 166 equal to ANY polity_code in
    data/final/polities_database.csv.

So the join a reader naturally writes --

    layer_b.merge(polities, on="polity_code")

-- returns an empty frame, and raises nothing. That is issue 95, option 4, and it cost a
table of zeros nearly published as evidence that no data existed in those years.

The parquet is built OUTSIDE this repository, so its header cannot be fixed here. What can
be fixed here is that no frame held by a script in this repo carries the misleading name:
`extdata.rename_layer_b_misnamed()` renames it to `iso3_lower` on the way in, and refuses
if the column ever starts holding real codes.

WHAT THIS GATE DOES. It is a SOURCE check, not a data check -- deliberately, because layer
B is not redistributable and CI cannot read it, so the property has to be enforced where CI
can see it. It finds every file that reads a layer-B parquet and asserts that the same file
renames the column, and it asserts that the rename and its reverse guard are still declared
in extdata.py. It needs no external data and runs anywhere.

Why source-scanning rather than trusting the loader: the loader already existed when this
was written, and two of its three callers passed no `polity_codes`, so the reverse guard
compared against an empty set and passed for that reason. A guard is only live if something
checks that it is wired up.

WHAT IT DELIBERATELY DOES NOT DO. It does not try to find every wrong join in the repo --
that needs the semantics of a whole script. It checks the one mechanical precondition that
makes the wrong join unwritable: the name is not there to join on.

Usage:
  python3 scripts/validate_layer_b_column_guard.py
"""
import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The misnamed column, and what every reader in this repo must call it instead. Kept here as
# well as in extdata.py on purpose: this gate must fail if extdata stops declaring it, and a
# gate that imports its own expectation from the thing it checks checks nothing.
MISNAMED = "polity_code"
RENAMED_TO = "iso3_lower"

# How a file says "this path is layer B". The env var name, the file's own basename, and the
# module-level constants that hold them.
PANEL_ENV_NAMES = ("WHEP_LAYERB", "WHEP_LAYER_B")
LAYER_B_MARKERS = ("WHEP_LAYERB", "consolidated_layer_b")

# Any ONE of these in the same file counts as passing the column through the guard:
# the Python helpers, or an explicit rename in R, which has no import of them.
GUARD_TOKENS = (
    "rename_layer_b_misnamed",
    "load_layer_b",
    f'{RENAMED_TO} = "{MISNAMED}"',      # R: dplyr::rename(iso3_lower = "polity_code")
    f"{RENAMED_TO} = '{MISNAMED}'",
    f'"{MISNAMED}": "{RENAMED_TO}"',     # Python: an explicit rename mapping
)

# Files whose only mention of layer B is documentation -- they read a DERIVED table, not the
# parquet. Listed so the scan's variable resolution is checkable rather than implicit.
SKIP = {
    "scripts/validate_layer_b_column_guard.py",   # this file
    "scripts/validate_schema_contract.py",        # documents the schema, reads no parquet
}

READ_CALL = re.compile(r"read_parquet\(\s*([A-Za-z_][\w.$]*|['\"][^'\"]+['\"])")
ASSIGN = re.compile(r"^\s*([A-Za-z_][\w.]*)\s*(?:=|<-)\s*(.+)$")


def source_files() -> list:
    out = []
    for base, dirs, names in os.walk(REPO):
        dirs[:] = [d for d in dirs
                   if d not in {".git", ".claude", "node_modules", "renv", "site", "__pycache__"}]
        for name in names:
            if name.endswith((".py", ".R", ".r")):
                out.append(os.path.relpath(os.path.join(base, name), REPO))
    return sorted(out)


def _statements(text: str):
    """(name, whole right-hand side) for each assignment, continuations included.

    The right-hand side has to be read across lines or the scan misses the real ones: both
    `LAYER_B = os.environ.get(\\n "WHEP_LAYERB", ...)` in extdata.py and build.R's
    `layer_b_path <- if (...) {...}` put the marker on a LATER line than the `=`. A version
    of this that matched single lines only found 1 of the 3 readers and printed PASS.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = ASSIGN.match(line)
        if not m:
            continue
        rhs = [m.group(2)]
        depth = sum(m.group(2).count(c) for c in "([{") - sum(m.group(2).count(c) for c in ")]}")
        j = i + 1
        while depth > 0 and j < len(lines) and j - i < 40:
            rhs.append(lines[j])
            depth += sum(lines[j].count(c) for c in "([{") - sum(lines[j].count(c) for c in ")]}")
            j += 1
        yield m.group(1), "\n".join(rhs)


def layer_b_variables(text: str) -> set:
    """Names assigned an expression that mentions layer B -- LB, LAYER_B, layer_b_path."""
    names = {n for n, _ in _statements(text) if re.search(r"layer_?b", n, re.I)}
    for name, rhs in _statements(text):
        if any(k in rhs for k in LAYER_B_MARKERS):
            names.add(name)
    # A second pass, so `LB = os.environ.get("WHEP_LAYERB", DEFAULT)` followed by
    # `p = path or LB` is still recognised as layer B.
    for _ in range(2):
        for name, rhs in _statements(text):
            if any(re.search(rf"\b{re.escape(n)}\b", rhs) for n in names):
                names.add(name)
    return names


def reads_layer_b(text: str) -> list:
    """The read_parquet arguments in `text` that resolve to layer B."""
    variables = layer_b_variables(text)
    hits = []
    for m in READ_CALL.finditer(text):
        arg = m.group(1)
        literal = arg.strip("'\"")
        if arg in variables or any(k in literal for k in LAYER_B_MARKERS):
            hits.append(arg)
    return hits


def main() -> int:
    problems = []
    readers = []

    for rel in source_files():
        if rel in SKIP:
            continue
        try:
            text = open(os.path.join(REPO, rel), encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        if not any(k in text for k in LAYER_B_MARKERS):
            continue
        hits = reads_layer_b(text)
        if not hits:
            continue                      # mentions layer B, reads something else
        readers.append((rel, hits))
        if not any(tok in text for tok in GUARD_TOKENS):
            problems.append(
                f"{rel}: reads layer B ({', '.join(sorted(set(hits)))}) but never renames "
                f"{MISNAMED!r} to {RENAMED_TO!r}.\n"
                f"      Layer B's {MISNAMED!r} holds LOWERCASE ISO CODES; joining it to this\n"
                f"      repo's polity_code matches NOTHING and raises NOTHING. Call\n"
                f"      extdata.rename_layer_b_misnamed(df, polity_codes=...) (Python) or\n"
                f"      dplyr::rename({RENAMED_TO} = \"{MISNAMED}\") (R) at the read."
            )

    if not readers:
        problems.append(
            "no layer-B reader found at all -- the scan is looking for "
            f"read_parquet of a name assigned from {LAYER_B_MARKERS}; if the readers moved, "
            "this gate has stopped checking anything"
        )

    # The guard itself must still be declared, with the reverse check that stops a FIXED
    # upstream being relabelled into a wrong name.
    ext = os.path.join(REPO, "pipelines/polity-autoimprove/extdata.py")
    if not os.path.exists(ext):
        problems.append("pipelines/polity-autoimprove/extdata.py: missing -- the rename lives there")
    else:
        etext = open(ext, encoding="utf-8").read()
        if f'LAYER_B_MISNAMED = {{"{MISNAMED}": "{RENAMED_TO}"}}' not in etext:
            problems.append(
                f"extdata.py no longer declares LAYER_B_MISNAMED = "
                f'{{"{MISNAMED}": "{RENAMED_TO}"}} -- the rename every reader relies on'
            )
        # Looked for INSIDE load_layer_b, not anywhere in the file: the first version of this
        # check searched the whole text and passed on a copy where the default had been
        # removed from the loader but the helper was still called in the module's selftest.
        loader = etext.split("def load_layer_b(", 1)[-1].split("\ndef ", 1)[0]
        if "polity_codes_from_database()" not in loader:
            problems.append(
                "extdata.load_layer_b no longer defaults `polity_codes` to the published "
                "codes, so its reverse guard compares against an empty set and passes for "
                "that reason rather than because the column is still misnamed"
            )

    # And the codes it compares against must exist, or the same guard is inert.
    csvp = os.path.join(REPO, "data/final/polities_database.csv")
    codes = set()
    if os.path.exists(csvp):
        with open(csvp, newline="", encoding="utf-8") as fh:
            codes = {r["polity_code"] for r in csv.DictReader(fh) if r.get("polity_code")}
        if not codes:
            problems.append("data/final/polities_database.csv holds no polity codes")

    print(f"layer-B readers found: {len(readers)}")
    for rel, hits in readers:
        print(f"  {rel}  <- {', '.join(sorted(set(hits)))}")
    print(f"polity codes available to the reverse guard: {len(codes):,}")

    # ONE PANEL, EITHER SPELLING (issue 629). The panel's location is read from an environment
    # variable, and for a long time there were TWO of them: WHEP_LAYERB in 01_match_and_findings.py
    # and extdata.py, WHEP_LAYER_B in the other 17 tools. Neither redirected the whole pipeline, so
    # pointing it at a different panel left stage 01 -- which produces matched_rows.parquet that
    # everything downstream consumes -- matching against one panel while the analysis stages
    # measured another, silently, whenever both paths happened to exist.
    #
    # THIS ARM ENUMERATES THE SITES ITSELF rather than reusing `readers` above. It has to: `readers`
    # finds 3 files (build.R, 01_match_and_findings.py, extdata.py) because it looks for the RENAME
    # pattern this gate's other arms are about, and 17 of the 19 environment reads are not in it.
    # The first version of this arm did reuse `readers`, reported "3 of 3", and could not have seen
    # a regression in any of the 17 -- a check scoped to the wrong population passes for the wrong
    # reason. build.R is excluded on purpose: it takes the panel path as argv[1], not from the
    # environment, so it is not part of this split.
    #
    # Source text only -- no existence check on the panel, which is outside the repo and absent in
    # CI. A tool may read either spelling; it may not read only one, because that is the split.
    import ast as _ast

    def _env_names(tree):
        found = set()
        for n in _ast.walk(tree):
            if (isinstance(n, _ast.Call) and isinstance(n.func, _ast.Attribute)
                    and n.func.attr == "get"
                    and isinstance(n.func.value, _ast.Attribute)
                    and n.func.value.attr == "environ"
                    and n.args and isinstance(n.args[0], _ast.Constant)
                    and n.args[0].value in PANEL_ENV_NAMES):
                found.add(n.args[0].value)
        return found

    split, total = [], 0
    for sub in ("pipelines", "scripts"):
        base = os.path.join(REPO, sub)
        for dirpath, _dirs, files in os.walk(base):
            for fn in sorted(files):
                if not fn.endswith(".py"):
                    continue
                full = os.path.join(dirpath, fn)
                try:
                    names = _env_names(_ast.parse(open(full, encoding="utf-8").read()))
                except (SyntaxError, UnicodeDecodeError):
                    continue
                if not names:
                    continue
                total += 1
                if len(names) == 1:
                    split.append((os.path.relpath(full, REPO), names.pop()))
    if not total:
        problems.append(
            "no module reads the panel path from the environment at all, which cannot be right -- "
            "this arm has lost its subject and would pass forever. Check PANEL_ENV_NAMES.")
    for rel, only in sorted(split):
        other = [n for n in PANEL_ENV_NAMES if n != only][0]
        problems.append(
            f"{rel}: reads only {only} and not {other}, so setting {other} redirects the rest of "
            f"the pipeline and not this tool. Both spellings must resolve the panel -- "
            f"`os.environ.get(\"WHEP_LAYER_B\") or os.environ.get(\"WHEP_LAYERB\") or <default>` "
            f"-- or stage 01 and the analysis stages can read different panels with nothing to show "
            f"for it. See issue 629.")
    print(f"panel-path readers honouring both spellings: {total - len(split)} of {total}")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print(f"\nPASS: every layer-B read renames {MISNAMED!r} to {RENAMED_TO!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
