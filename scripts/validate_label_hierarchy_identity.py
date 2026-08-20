#!/usr/bin/env python3
"""Gate `state/label_hierarchy_identity.csv` (issues 411, 449, 450) -- CI cannot rebuild it.

The table is produced by `pipelines/polity-autoimprove/36_label_hierarchy_identity.py` from
`matched_rows.parquet`, which is not in the repository, so `--check` there cannot run in CI. This gate
checks what is checkable from the file alone, and the arms are chosen so that the two ways this table
can lie are both covered.

  A  schema: exactly the generator's columns, every one populated.
  B  internal arithmetic: MIN_CELLS <= cells, exact_cells <= cells, min <= median <= max,
     n_parts_present <= n_kids, and `parts_present` holds exactly n_parts_present labels.
  C  the verdict is RE-DERIVED by importing the generator's own classify() and re-running it on the
     numbers in the file. A hand-edited verdict -- the cheapest way to turn a `subset` into a
     `partition` -- fails here.
  D  THE LABEL TREE IS RE-VERIFIED. Every entry in `parts_present` must have `whole_label` as a proper
     prefix followed by a space or a colon. This is the arm that exists because the generator got it
     wrong: an earlier version accepted ANY non-alphanumeric separator and so filed `guinea-bissau` as
     a part of `guinea`, publishing a fabricated hierarchy at a plausible 0.89 ratio over 8 cells. No
     arithmetic arm could catch that -- the ratios were real, the relationship was not.
  E  the proven partitions stay proven. BASELINE pins the three identities the table rests on. It is
     BIDIRECTIONAL: if a rebuild legitimately changes one, update the baseline in the same commit.
"""
from __future__ import annotations

import csv
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TOOL = os.path.join(REPO, "pipelines/polity-autoimprove/36_label_hierarchy_identity.py")
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/label_hierarchy_identity.csv")

# (source, whole_label, parts_present) -> (cells, exact_cells, verdict)
# An exact identity printed by the source itself: these are the rows other issues cite.
BASELINE = {
    ("fao1952", "germany", "germany berlin | germany eastern | germany western"):
        (28, 28, "partition"),
    ("fao1952", "french north africa",
     "french north africa algeria | french north africa morocco | french north africa tunisia"):
        (4, 4, "partition"),
    ("iia", "ethiopia", "ethiopia pdr"): (3, 3, "duplicate"),
    # A SINGLE cell, admitted below the generator's floor because it is already proof: 108.9 = 98.9 +
    # 10.0, four significant digits, in the exact years two issues had left undecided (#355, #407).
    ("fao1952", "korea", "korea north | korea south"): (1, 1, "partition"),
    # Two cells, both exact three-term sums: 770 = 35 + 295 + 440 (1937) and 953 = 47 + 335 + 571
    # (1951). Also below the generator's floor, and also admitted as already proof.
    ("fao1952", "british borneo",
     "british borneo brunei | british borneo north borneo | british borneo sarawak"):
        (2, 2, "partition"),
}


def load_tool():
    spec = importlib.util.spec_from_file_location("hier_identity", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"MISSING {TABLE}", file=sys.stderr)
        return 1
    tool = load_tool()
    with open(TABLE, newline="") as fh:
        rdr = csv.DictReader(fh)
        cols = tuple(rdr.fieldnames or ())
        rows = list(rdr)

    fails = []
    # --- A: schema ---
    if cols != tool.FIELDS:
        fails.append(f"columns {cols} != generator FIELDS {tool.FIELDS}")
        print("\n".join(f"  {f}" for f in fails), file=sys.stderr)
        return 1
    seen = set()
    for i, r in enumerate(rows, 2):
        who = f"row {i} ({r['source']}/{r['whole_label']})"
        for c in tool.FIELDS:
            if c != "items" and not str(r[c]).strip():
                fails.append(f"{who}: empty {c}")
        key = (r["source"], r["whole_label"], r["parts_present"])
        if key in seen:
            fails.append(f"{who}: duplicate key {key}")
        seen.add(key)

        # --- B: internal arithmetic ---
        try:
            cells, exact = int(r["cells"]), int(r["exact_cells"])
            nk, npp = int(r["n_kids"]), int(r["n_parts_present"])
            lo, mid, hi = (float(r["min_ratio"]), float(r["median_ratio"]), float(r["max_ratio"]))
        except ValueError as e:
            fails.append(f"{who}: unparseable numeric ({e})")
            continue
        if cells < tool.MIN_CELLS:
            # The generator admits ONE narrow exemption to its own floor: a single cell that is
            # already proof -- every named child present, at least two of them, the sum exact, and the
            # whole not a round number (issue 355's `Korea` = `Korea South` + `Korea North`,
            # 108.9 = 98.9 + 10.0). Re-derived here rather than trusted, so a hand-added sub-floor row
            # cannot borrow the exemption without meeting it.
            ok = (npp == nk >= 2 and exact == cells
                  and abs(mid - 1.0) <= tool.TOL and r["verdict"] == "partition")
            if not ok:
                fails.append(f"{who}: cells {cells} below MIN_CELLS {tool.MIN_CELLS} and this row does "
                             f"not meet the exact-full-partition exemption (all {nk} kids present, "
                             f"every cell exact, verdict `partition`)")
        if not 0 <= exact <= cells:
            fails.append(f"{who}: exact_cells {exact} outside 0..{cells}")
        if not lo <= mid <= hi:
            fails.append(f"{who}: median {mid} outside [{lo}, {hi}]")
        if not 1 <= npp <= nk:
            fails.append(f"{who}: n_parts_present {npp} outside 1..{nk}")
        parts = [p.strip() for p in r["parts_present"].split("|") if p.strip()]
        if len(parts) != npp:
            fails.append(f"{who}: parts_present holds {len(parts)} labels, n_parts_present is {npp}")

        # --- C: re-derive the verdict ---
        want = tool.classify(nk, npp, mid, exact / cells if cells else 0.0)
        if r["verdict"] != want:
            fails.append(f"{who}: verdict {r['verdict']!r}, but classify() on this row's own numbers "
                         f"(n_kids={nk}, present={npp}, median={mid}, exact={exact}/{cells}) "
                         f"gives {want!r}")

        # --- D: re-verify the tree ---
        for p in parts:
            w = r["whole_label"]
            if not (p.startswith(w) and len(p) > len(w) and p[len(w)] in " :"):
                fails.append(f"{who}: {p!r} is filed as a part of {w!r}, but {w!r} is not a "
                             f"space-or-colon-separated prefix of it -- a fabricated hierarchy")

    # --- E: baseline ---
    have = {(r["source"], r["whole_label"], r["parts_present"]):
            (int(r["cells"]), int(r["exact_cells"]), r["verdict"]) for r in rows}
    for k, want in sorted(BASELINE.items()):
        if k not in have:
            fails.append(f"BASELINE {k} is absent from the table -- a proven source identity vanished")
        elif have[k] != want:
            fails.append(f"BASELINE {k}: table says {have[k]}, baseline says {want}. If the rebuild is "
                         f"right, update BASELINE in the same commit (it is bidirectional)")
    for k in sorted(have):
        if k in BASELINE:
            continue
        if have[k][2] == "partition" and have[k][1] == have[k][0]:
            fails.append(f"{k}: a new all-cells-exact partition is not in BASELINE. Add it, so that "
                         f"the identity other issues cite cannot silently disappear")

    if fails:
        print(f"FAIL {len(fails)} problem(s) in label_hierarchy_identity.csv:", file=sys.stderr)
        for f in fails:
            print(f"  {f}", file=sys.stderr)
        return 1
    print(f"OK label_hierarchy_identity.csv: {len(rows)} group(s), "
          f"{sum(1 for r in rows if r['verdict'].startswith('partition'))} partition, "
          f"{len(BASELINE)} baselined identity(ies) intact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
