#!/usr/bin/env python3
"""Which registered whole/part pairs actually receive data on BOTH sides, by any routing?

`validate_composition_sums.py` check C forbids an undeclared double count, and it reads the ALIAS MAP
to find them. That misses most of the routing. Of the 832 label->polity routings the matcher actually
made, only 205 came from an alias; the other 627 (75%) resolved by `iso`, `name` or `tokenset`, and a
part reached that way is invisible to the check -- so a whole and its own part can both receive data
with nothing recorded.

Measured on the run that added this: 13 such pairs, none of them declared. Not edge cases:

    AOI-1936-1941  <- ERI-1889-1952      fao1952, iia   'Africa Orientale Italiana' + 'eritrea'
    IDN-1949-1963  <- IDN-JVM/BLB/OTH    fao1952        'indonesia' + its three island groups
    JPN-1895-1945  <- RYU-1937-1945      iia, mitchell  'japan' + 'Ryukyu Islands'
    MASG-1946-1963 <- SGP-1946-1963      fao1952        'Malaya ... and Singapore' + 'singapore'
    SYL-1944-1953  <- LBN-1944-2025      fao1952        'Syria and Lebanon' + 'lebanon'
    AEF-1910-1960  <- GAB/CAF/TCD        iia, mitchell  'congo' (the FEA total) + each territory

The Syria/Lebanon pair is issue 315's Levant double count arriving from a completely different
direction, and the Indonesia pairs are issue 312's.

WHY A TRACKED TABLE. The routings live in `state/match_confidence.csv`, which is GITIGNORED because it
is derived from the layer-B panel, itself gitignored and absent in CI. So this script writes what it
finds to `state/composition_overlaps.csv`, that file is committed, and the gate reads it -- the same
arrangement as `16_source_splices.py`, `17_constant_runs.py` and `18_isolated_spikes.py`.

THE DISPOSITION IS DERIVED, NOT ASSERTED. `separate_series` versus `sum_risk` turns on whether the two
sides carry the same items, so this counts the (item, unit, year) cells present on BOTH sides from the
panel. Zero shared cells means the source really does report them separately; anything above zero means
a sum double-counts, and the count says by how much. That is the one part of check C that previously
had to be taken on trust.

WHAT THIS DOES NOT DECIDE. Which side to keep. A whole-plus-parts publication is a real editorial
choice by the source, and the fix differs per case -- drop the whole, drop the parts, or keep both and
never sum them. This records that the choice exists and has not been made.

Usage:
  python3 pipelines/polity-autoimprove/19_composition_overlaps.py            # report only
  python3 pipelines/polity-autoimprove/19_composition_overlaps.py --write    # refresh the table
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import tempfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "composition_overlaps.csv")
REGISTRY = os.path.join(STATE, "polity_composition.csv")
ALIASES = os.path.join(STATE, "applied_aliases.csv")
ROUTINGS = os.path.join(STATE, "match_confidence.csv")
DEFAULT_PANEL = os.path.expanduser(
    os.environ.get("WHEP_LAYER_B", "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet"))


def norm(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def year(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def routing_table():
    """(source, y0, y1, label, method) per polity, from the alias map AND the matcher's own output.

    A BLANK alias `source` is a wildcard, matching any source -- the same reading the matchers use.
    """
    out = defaultdict(list)
    with open(ALIASES, encoding="utf-8") as fh:
        for a in csv.DictReader(fh):
            y0, y1 = year(a.get("year_start")), year(a.get("year_end"))
            if y0 is not None and y1 is not None:
                out[a["polity_code"]].append(
                    ((a.get("source") or "").strip(), y0, y1, a.get("source_label") or "", "alias"))
    if os.path.exists(ROUTINGS):
        with open(ROUTINGS, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                y0, y1 = year(r.get("year_min")), year(r.get("year_max"))
                if y0 is not None and y1 is not None:
                    out[r["polity_code"]].append(
                        (r["source"], y0, y1, r.get("source_label") or "", r.get("method") or "?"))
    return out


def shared_cells(panel, source, whole_labels, part_labels):
    """(item, unit, year) cells present under BOTH sides' labels in one source.

    This is what separates `separate_series` from `sum_risk`, and it is the reason to read the panel
    rather than only the registry.
    """
    if panel is None:
        return None, None
    d = panel[panel["source"] == source]
    w = d[d["country"].map(norm).isin({norm(x) for x in whole_labels})]
    p = d[d["country"].map(norm).isin({norm(x) for x in part_labels})]
    key = lambda g: {(norm(r.item), str(r.unit), int(r.year))
                     for r in g.dropna(subset=["year"]).itertuples()}
    kw, kp = key(w), key(p)
    items_w = {(i, u) for i, u, _y in kw}
    items_p = {(i, u) for i, u, _y in kp}
    return len(kw & kp), len(items_w & items_p)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--layer-b", default=DEFAULT_PANEL)
    # Every tool from 25 up carries --check; these eight did not, so their tracked tables could drift
    # undetected. That is not hypothetical: 04's --check caught territory_basis.csv drifting after a
    # routing fix, and 23's absence let verdict_carryover.csv go stale (issues 308, 472). Safe here
    # because all eight were verified to regenerate byte-identically with default arguments -- the
    # precondition 15_label_provenance did NOT meet, where a check would have invited data loss.
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the tracked table is not what this run produces")
    ap.add_argument("--write", action="store_true", help=f"refresh {os.path.relpath(OUT, REPO)}")
    args = ap.parse_args()

    panel = None
    if os.path.exists(args.layer_b):
        import pandas as pd
        panel = pd.read_parquet(args.layer_b)
        if "is_aggregate" in panel.columns:
            panel = panel[~panel["is_aggregate"].astype(bool)]
        panel = panel.dropna(subset=["value"])
    else:
        print(f"NOTE: panel absent at {args.layer_b}; shared-cell counts will be blank")

    routes = routing_table()
    with open(REGISTRY, encoding="utf-8") as fh:
        registry = list(csv.DictReader(fh))

    rows = []
    for r in registry:
        whole = r["whole_code"].strip()
        part = (r.get("part_code") or "").strip()
        if not part:
            continue
        pairs = defaultdict(lambda: {"y0": None, "y1": None, "w": set(), "p": set(),
                                     "wm": set(), "pm": set()})
        for wsrc, wy0, wy1, wlab, wm in routes.get(whole, []):
            for psrc, py0, py1, plab, pm in routes.get(part, []):
                if wsrc and psrc and wsrc != psrc:
                    continue
                lo, hi = max(wy0, py0), min(wy1, py1)
                if lo > hi:
                    continue
                e = pairs[wsrc or psrc or "(any)"]
                e["y0"] = lo if e["y0"] is None else min(e["y0"], lo)
                e["y1"] = hi if e["y1"] is None else max(e["y1"], hi)
                e["w"].add(wlab); e["p"].add(plab)
                e["wm"].add(wm); e["pm"].add(pm)
        for src, e in sorted(pairs.items()):
            cells, items = (None, None)
            if src != "(any)":
                cells, items = shared_cells(panel, src, e["w"], e["p"])
            rows.append({
                "whole_code": whole, "part_code": part, "source": src,
                "year_first": e["y0"], "year_last": e["y1"],
                "whole_labels": ";".join(sorted(e["w"])[:4]),
                "part_labels": ";".join(sorted(e["p"])[:4]),
                "whole_method": ";".join(sorted(e["wm"])),
                "part_method": ";".join(sorted(e["pm"])),
                "shared_item_units": "" if items is None else items,
                "shared_cells": "" if cells is None else cells,
                "alias_visible": "yes" if ("alias" in e["wm"] and "alias" in e["pm"]) else "no",
            })

    rows.sort(key=lambda r: (r["alias_visible"], r["whole_code"], r["part_code"], r["source"]))
    hidden = [r for r in rows if r["alias_visible"] == "no"]
    print(f"registered pairs with a part: "
          f"{sum(1 for r in registry if (r.get('part_code') or '').strip())}")
    print(f"(pair, source) overlaps found: {len(rows)}")
    print(f"  reachable through an alias on BOTH sides (the CI gate can see these): "
          f"{len(rows) - len(hidden)}")
    print(f"  needing at least one non-alias routing (INVISIBLE to the CI gate today): {len(hidden)}")
    print(f"\n{'whole':17} {'part':19} {'source':9} {'years':11} {'cells':>6} "
          f"{'items':>6}  whole via / part via")
    for r in hidden:
        print(f"  {r['whole_code'][:16]:17} {r['part_code'][:18]:19} {r['source']:9} "
              f"{str(r['year_first'])+'-'+str(r['year_last']):11} "
              f"{str(r['shared_cells']):>6} {str(r['shared_item_units']):>6}  "
              f"{r['whole_method']} / {r['part_method']}")

    if args.write or args.check:
        cols = ["whole_code", "part_code", "source", "year_first", "year_last", "whole_labels",
                "part_labels", "whole_method", "part_method", "shared_item_units", "shared_cells",
                "alias_visible"]
        if args.check:
            if not os.path.exists(OUT):
                print(f"MISSING {os.path.relpath(OUT, REPO)}", file=sys.stderr)
                return 1
            with open(OUT, newline="", encoding="utf-8") as fh:
                have = list(csv.DictReader(fh))
            want = [{k: ("" if v is None else str(v)) for k, v in dict(r).items()} for r in rows]
            if [{k: r.get(k, "") for k in cols} for r in have] != \
                    [{k: r.get(k, "") for k in cols} for r in want]:
                print(f"STALE {os.path.relpath(OUT, REPO)}: committed {len(have)} row(s), this run "
                      f"produces {len(want)}; rerun with --write", file=sys.stderr)
                return 1
            print(f"table is current ({len(have)} rows)")
            return 0
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(OUT), suffix=".tmp")
        os.close(fd)
        # The unlink matters: a DictWriter raises on an unexpected key, and without this the
        # half-written .tmp is left behind in a TRACKED state directory where `git add -A`
        # can commit it. That happened on 2026-08-20 when a column was added to the rows but
        # not to the fieldnames.
        try:
            with open(tmp, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=cols)
                w.writeheader()
                w.writerows(rows)
            os.replace(tmp, OUT)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
        print(f"\nwrote {len(rows)} overlaps to {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
