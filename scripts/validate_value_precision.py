#!/usr/bin/env python3
"""Gate `state/source_value_precision.csv` (issue 446) -- CI cannot rebuild it.

The table is derived from the layer-B panel, which is not in the repository, so the generator's
`--check` cannot run in CI. This gate checks what the file supports alone, and one arm reaches outside
it:

  A  schema: exactly the generator's columns, every field populated.
  B  arithmetic: shares in [0, 1]; the 1000-grid share cannot exceed the 100-grid share (every multiple
     of 1000 is a multiple of 100); n_nonzero at least MIN_ROWS.
  C  the verdict is RE-DERIVED by importing the generator's own classify(). A hand-edited verdict is the
     cheapest way to turn a `mixed` source into a `fine` one, and prose elsewhere cites these verdicts.
  D  CROSS-CHECK AGAINST THE CONVENTIONS REGISTRY, which is the arm that matters. `source_conventions.csv`
     records the reporting grids of `mitchell`, `iia` and `juan` as conventions with their own mechanical
     re-tests. This table is the machine-readable form of the same facts, so the two must not drift: a
     source with a registered grid convention must show at least one `coarse_*` row here, and a source
     showing `coarse_*` here must have a convention there. Without this arm the table could quietly
     contradict the registry that justifies it.
  E  BASELINE pins the extreme rows the issue's argument rests on. BIDIRECTIONAL: if a rebuild
     legitimately moves one, update the baseline in the same commit.
"""
from __future__ import annotations

import csv
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TOOL = os.path.join(REPO, "pipelines/polity-autoimprove/37_value_precision.py")
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/source_value_precision.csv")
CONVENTIONS = os.path.join(REPO, "pipelines/polity-autoimprove/state/source_conventions.csv")

# Sources whose reporting grid is registered as a convention. Keys are the `source` column there.
GRID_CONVENTION_SOURCES = frozenset({"mitchell", "iia", "juan"})

# (source, unit, era) -> verdict. The rows issue 446's exposure argument is built on.
BASELINE = {
    ("mitchell", "ha", "all"): "coarse_1000",
    ("mitchell", "heads", "all"): "coarse_1000",
    ("mitchell", "tonnes", "all"): "coarse_100",
    ("iia", "ha", "1934+"): "coarse_1000",
    ("iia", "tonnes", "1934+"): "coarse_100",
    ("juan", "heads", "all"): "coarse_1000",
}


def load_tool():
    spec = importlib.util.spec_from_file_location("value_precision", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    for p in (TABLE, CONVENTIONS):
        if not os.path.exists(p):
            print(f"MISSING {p}", file=sys.stderr)
            return 1
    tool = load_tool()
    with open(TABLE, newline="") as fh:
        rdr = csv.DictReader(fh)
        cols = tuple(rdr.fieldnames or ())
        rows = list(rdr)

    fails = []
    if cols != tool.FIELDS:
        print(f"FAIL columns {cols} != generator FIELDS {tool.FIELDS}", file=sys.stderr)
        return 1

    seen = set()
    coarse_sources = set()
    for i, r in enumerate(rows, 2):
        who = f"row {i} ({r['source']}/{r['unit']}/{r['era']})"
        for c in tool.FIELDS:
            if not str(r[c]).strip():
                fails.append(f"{who}: empty {c}")
        key = (r["source"], r["unit"], r["era"])
        if key in seen:
            fails.append(f"{who}: duplicate key {key}")
        seen.add(key)
        try:
            n = int(r["n_nonzero"])
            g1000, g100 = float(r["share_grid_1000"]), float(r["share_grid_100"])
            sub = float(r["share_subunit"])
        except ValueError as e:
            fails.append(f"{who}: unparseable numeric ({e})")
            continue
        # --- B ---
        if n < tool.MIN_ROWS:
            fails.append(f"{who}: n_nonzero {n} below MIN_ROWS {tool.MIN_ROWS}")
        for name, v in (("share_grid_1000", g1000), ("share_grid_100", g100),
                        ("share_subunit", sub)):
            if not 0.0 <= v <= 1.0:
                fails.append(f"{who}: {name} {v} outside [0, 1]")
        if g1000 > g100 + 1e-9:
            fails.append(f"{who}: 1000-grid share {g1000} exceeds the 100-grid share {g100}, which is "
                         f"impossible -- every multiple of 1000 is a multiple of 100")
        # --- C ---
        want = tool.classify(g1000, g100)
        if r["verdict"] != want:
            fails.append(f"{who}: verdict {r['verdict']!r}, but classify() on this row's own shares "
                         f"(1000={g1000}, 100={g100}) gives {want!r}")
        if r["verdict"].startswith("coarse"):
            coarse_sources.add(r["source"])

    # --- D: cross-check against the conventions registry ---
    with open(CONVENTIONS, newline="") as fh:
        conv_sources = {r["source"] for r in csv.DictReader(fh)}
    for src in sorted(GRID_CONVENTION_SOURCES):
        if src not in conv_sources:
            fails.append(f"{src} is listed in GRID_CONVENTION_SOURCES but has no entry in "
                         f"source_conventions.csv -- the registry this table mirrors has changed")
        elif src not in coarse_sources:
            fails.append(f"{src} has a registered reporting-grid convention but NO `coarse_*` row in "
                         f"this table; the table and the registry now disagree")
    for src in sorted(coarse_sources - GRID_CONVENTION_SOURCES):
        fails.append(f"{src} is recorded `coarse_*` here but has no registered grid convention. Register "
                     f"it (with a re-test) or explain the row -- an unregistered coarse verdict is a "
                     f"claim about a source with nothing standing behind it")

    # --- E: baseline ---
    have = {(r["source"], r["unit"], r["era"]): r["verdict"] for r in rows}
    for k, want in sorted(BASELINE.items()):
        if k not in have:
            fails.append(f"BASELINE {k} is absent from the table")
        elif have[k] != want:
            fails.append(f"BASELINE {k}: table says {have[k]!r}, baseline says {want!r}. If the rebuild "
                         f"is right, update BASELINE in the same commit (it is bidirectional)")

    if fails:
        print(f"FAIL {len(fails)} problem(s) in source_value_precision.csv:", file=sys.stderr)
        for f in fails:
            print(f"  {f}", file=sys.stderr)
        return 1
    print(f"OK source_value_precision.csv: {len(rows)} group(s), "
          f"{len(coarse_sources)} source(s) with a coarse grid, {len(BASELINE)} baselined")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
