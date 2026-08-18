#!/usr/bin/env python3
"""Two labels of ONE source landing on ONE polity, over years that overlap.

`polity_composition.csv` records whole/part pairs as `(whole_code, part_code)` and
`validate_composition_sums.py` check C forbids an undeclared double count between them. Neither can
express the case where **both labels route to the SAME polity** -- there is only one code, so there
is no pair to register. Issue 355 named four such cases from a string test over label spellings and
said the model needed a second registry keyed on the labels rather than the codes.

This derives them from the matcher's ACTUAL routings instead of from label shape, which is what makes
the result trustworthy: issue 355's string test matched 39 polities of which 4 were real, because
`'Lao'` extends to `"Lao People's Democratic Republic"` and eight spellings of `'Trieste UK-US'`
extend to each other. Shape cannot tell a parent from a longer synonym. Shared cells can.

A pair is reported only when the two labels share at least one (item, unit, year) cell. Disjoint
labels on one polity are the normal, correct case -- a polity is supposed to collect its territory's
data from wherever the source files it -- and reporting those would bury the real finding under
hundreds of non-events.

THE RELATION IS DERIVED FROM THE SHARED CELLS, NOT ASSERTED:

  orthographic_variant  the two labels normalise to the same string, so they are one territory
                        reached twice. 30 such groups exist in fao1952 alone (`Ruanda Urundi` and
                        `Ruanda-Urundi`, `China Taiwan` and `China: Taiwan`, `*Madagascar` and
                        `Madagascar`, five `British West Indies  X` doubled-space pairs). These are
                        not a double count -- they are a reason every tool keying on the raw label
                        undercounts, this one included.
  containment           one side exceeds the other in at least 90% of shared cells, never falls
                        below, and does so over at least 5 cells. `Germany` over `Germany Western`,
                        `United Kingdom` over `United Kingdom Great Britain`.
  undetermined          too few shared cells to say anything. Most pairs land here and that is the
                        honest answer: on a single shared cell, "the larger side contains the other"
                        is a coin flip.
  identical             every shared cell is equal. Under a DISTINCTNESS FLOOR of 6 distinct values,
                        because a series of three round numbers matches anything.
  disagreement          shared cells run both directions. Neither contains the other, so at least
                        one routing is wrong.

WHY THIS IS NOT A DOUBLE-COUNT COUNT. The WHEP R package collapses duplicate keys with `mean(value)`,
not `sum` (`.prepare_historical_production()`, measured on issue 367), so a whole and its part landing
on one polity are AVERAGED. That understates rather than doubles. The defect these rows describe is
real either way -- one polity-year-item holding two incompatible numbers -- but the direction of the
error depends on a downstream operation this repo does not control, so the table records the relation
and leaves the arithmetic to whoever consumes it.

WHY A TRACKED TABLE. The routings come from the layer-B panel, which is gitignored and absent in CI,
so this writes `state/same_polity_overlaps.csv`, that file is committed, and the gate reads it. Same
arrangement as 16_source_splices.py, 17_constant_runs.py, 18_isolated_spikes.py, 19_composition_overlaps.py.

Usage:
  python3 pipelines/polity-autoimprove/25_same_polity_overlaps.py            # report only
  python3 pipelines/polity-autoimprove/25_same_polity_overlaps.py --write    # refresh the table
  python3 pipelines/polity-autoimprove/25_same_polity_overlaps.py --check    # fail if stale
"""
from __future__ import annotations

import argparse
import csv
import itertools
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "same_polity_overlaps.csv")
MATCHED = os.path.join(STATE, "matched_rows.parquet")

# A relative gap this small is float noise from the panel's own round-trips, not a real difference.
EPS = 1e-9
# Below this many DISTINCT values, an all-equal verdict means nothing: three round numbers match
# anything. Same floor the source-splice fingerprints use.
MIN_DISTINCT = 6
# One side must exceed the other this often, and never fall below, before calling it containment.
CONTAIN_FRAC = 0.90
# ...and over at least this many cells. NOT a fitted number: under a null where each shared cell
# falls either way at random, n cells agreeing in one direction has probability 2**-(n-1) two-sided,
# so n=5 is the smallest count that clears 0.05. On one cell "the bigger side contains the other" is
# a coin flip, and it was reached for 18 of the 26 pairs before this floor existed -- including
# `EI Salvador` over `El Salvador`, which is an OCR variant of ONE label (capital I for lowercase l)
# that norm() cannot collapse because the confusion is glyphic, not orthographic.
MIN_DIRECTIONAL = 5

FIELDS = ["whep_code", "source", "label_a", "label_b", "relation", "shared_cells",
          "n_equal", "n_a_gt_b", "n_b_gt_a", "distinct_values", "years", "rows_a", "rows_b"]


def norm(s: str) -> str:
    """Collapse spelling: case, punctuation, runs of whitespace, leading footnote asterisks."""
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def classify(eq: int, agt: int, bgt: int, n: int, distinct: int, same_norm: bool) -> str:
    if same_norm:
        return "orthographic_variant"
    if eq == n:
        return "identical" if distinct >= MIN_DISTINCT else "identical_indistinct"
    if n < MIN_DIRECTIONAL:
        return "undetermined"
    if bgt == 0 and agt >= CONTAIN_FRAC * n:
        return "containment"
    if agt == 0 and bgt >= CONTAIN_FRAC * n:
        return "containment"
    return "disagreement"


def build(matched: str) -> list[dict]:
    import pandas as pd

    df = pd.read_parquet(matched)
    df = df[df.value.notna() & df.whep_code.notna()]
    out = []
    for (code, src), g in df.groupby(["whep_code", "source"]):
        labels = sorted(g.country.dropna().unique())
        if len(labels) < 2:
            continue
        for a, b in itertools.combinations(labels, 2):
            ga, gb = g[g.country == a], g[g.country == b]
            ka = ga.set_index(["item", "unit", "year"]).value
            kb = gb.set_index(["item", "unit", "year"]).value
            ka, kb = ka[~ka.index.duplicated()], kb[~kb.index.duplicated()]
            shared = ka.index.intersection(kb.index)
            if len(shared) == 0:
                continue
            va, vb = ka.loc[shared], kb.loc[shared]
            tol = va.abs() * EPS
            eq = int(((va - vb).abs() <= tol).sum())
            agt = int((va - vb > tol).sum())
            bgt = int((vb - va > tol).sum())
            distinct = len(set(va.round(9)) | set(vb.round(9)))
            years = sorted({int(y) for _, _, y in shared if not pd.isna(y)})
            out.append({
                "whep_code": code, "source": src, "label_a": a, "label_b": b,
                "relation": classify(eq, agt, bgt, len(shared), distinct, norm(a) == norm(b)),
                "shared_cells": len(shared), "n_equal": eq, "n_a_gt_b": agt, "n_b_gt_a": bgt,
                "distinct_values": distinct,
                "years": f"{years[0]}-{years[-1]}" if years else "",
                "rows_a": len(ga), "rows_b": len(gb),
            })
    out.sort(key=lambda r: (r["whep_code"], r["source"], r["label_a"], r["label_b"]))
    return out


def write(rows: list[dict], path: str) -> None:
    """Build the whole file in memory, then replace atomically -- a truncating open() has cost this
    repo two tracked state files mid-error."""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--matched", default=MATCHED)
    ap.add_argument("--write", action="store_true", help=f"refresh {os.path.relpath(OUT, REPO)}")
    ap.add_argument("--check", action="store_true", help="exit 1 if the tracked table is stale")
    args = ap.parse_args()

    if not os.path.exists(args.matched):
        print(f"panel absent ({args.matched}); nothing to do", file=sys.stderr)
        return 0

    rows = build(args.matched)
    by_rel: dict[str, int] = {}
    for r in rows:
        by_rel[r["relation"]] = by_rel.get(r["relation"], 0) + 1
    print(f"{len(rows)} label pairs share cells on one polity within one source")
    for rel in sorted(by_rel):
        print(f"  {rel:24} {by_rel[rel]}")

    if args.check:
        if not os.path.exists(OUT):
            print(f"MISSING {os.path.relpath(OUT, REPO)}", file=sys.stderr)
            return 1
        with open(OUT, newline="") as fh:
            have = list(csv.DictReader(fh))
        want = [{k: str(v) for k, v in r.items()} for r in rows]
        if have != want:
            print(f"STALE {os.path.relpath(OUT, REPO)}: rerun with --write", file=sys.stderr)
            return 1
        print("table is current")
        return 0

    if args.write:
        write(rows, OUT)
        print(f"wrote {os.path.relpath(OUT, REPO)}")
    else:
        for r in rows:
            print(f"  {r['whep_code']:16} {r['source']:9} {r['relation']:22} "
                  f"{r['label_a']!r} / {r['label_b']!r}  {r['shared_cells']} cells")
    return 0


if __name__ == "__main__":
    sys.exit(main())
