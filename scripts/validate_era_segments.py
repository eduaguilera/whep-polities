#!/usr/bin/env python3
"""Every era of a spliced iia series has a disposition, and the disposition is backed by the file
that carries it out (issue 443).

`pipelines/polity-autoimprove/48_era_segments.py` cuts each iia (label, item, unit) series that is
stitched from two or more raw labels into eras, and records where each era's rows go. The generator
needs the layer-B panel and the raw extract, neither of which CI has, so this gate holds the TRACKED
table to its own claims and to the two tables a claim points at:

  A  shape. A series has >= 2 eras numbered 1..k in year order, consecutive eras do not overlap and
     carry different raw labels, `shape` is `partition` exactly when no label returns, and every
     raw label clears MIN_ERA_DISTINCT distinct values summed over its eras -- the floor that keeps
     a two-value coincidence from reading as an era.
  B  rerouted, both directions. A `rerouted` era is covered, every year, by rules in
     data/final/source_label_item_corrections.csv on (iia, label, item) whose polities are its
     `reference`, and its rows sit there (`routed_polities`). An era NOT marked `rerouted` that such
     rules fully cover is stale: deleting a rule must turn its eras back into something else, and
     adding one must not leave an era claiming its rows are still undecided.
  C  periods. A rerouted era's rules move no period-average row that belongs to ANOTHER raw label
     (`n_period_moved_other` = 0). Issue 443 was itself partly a period row misread as a dated one,
     and Syria's `1934-1938` row is `french syria` alone inside a Syria+Lebanon era: a single
     1922-1938 rule would have moved it.
  D  references resolve. `component` needs a reference; a `data_errors:` reference names an existing
     entry, a `source_conventions:` one an existing (source, label_pattern, item_pattern); a `routed`
     era's polities are all inside its reference.
  E  pinned, bidirectionally: series, eras and the count per disposition. An `open` era closing is
     progress and must be recorded by lowering the pin; one appearing is a new splice to look at.

Usage:
  python3 scripts/validate_era_segments.py
"""
from __future__ import annotations

import collections
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(REPO, "pipelines/polity-autoimprove/state")
TABLE = os.path.join(STATE, "era_segments.csv")
CORRECTIONS = os.path.join(REPO, "data/final/source_label_item_corrections.csv")
ERRORS = os.path.join(STATE, "data_errors.csv")
CONVENTIONS = os.path.join(STATE, "source_conventions.csv")

# Restated, not imported from the generator: relaxing the generator's floor and regenerating must fail
# here rather than move the bar silently.
MIN_ERA_DISTINCT = 4
DISPOSITIONS = frozenset({"rerouted", "routed", "component", "open"})

# Pinned 2026-10-08 (issue 443, Claude), after issue 372's rules landed. 59 series, 128 eras.
BASELINE_SERIES = 59
BASELINE_ERAS = 128
BASELINE_BY_DISPOSITION = {"routed": 78, "rerouted": 22, "component": 18, "open": 10}


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def covering(rules, label, item, unit, y0, y1):
    mine = [r for r in rules if r["source"] == "iia" and r["source_label"] == label
            and r["item"] == item and r.get("unit", "") in ("", unit) and not r.get("indicator", "")]
    pols = set()
    for y in range(y0, y1 + 1):
        hit = [r for r in mine if int(r["year_start"]) <= y <= int(r["year_end"])]
        if not hit:
            return None
        pols.update(r["polity_code"] for r in hit)
    return pols


def main() -> int:
    for p in (TABLE, CORRECTIONS, ERRORS, CONVENTIONS):
        if not os.path.exists(p):
            print(f"FAIL: {os.path.relpath(p, REPO)} missing")
            return 1
    with open(TABLE, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    with open(CORRECTIONS, newline="", encoding="utf-8") as fh:
        rules = list(csv.DictReader(fh))
    with open(ERRORS, newline="", encoding="utf-8") as fh:
        error_ids = {r["issue_id"] for r in csv.DictReader(fh)}
    with open(CONVENTIONS, newline="", encoding="utf-8") as fh:
        conv_keys = {f"{r['source']}|{r['label_pattern']}|{r['item_pattern']}"
                     for r in csv.DictReader(fh)}

    problems = []
    series = collections.defaultdict(list)
    for r in rows:
        y0, y1 = _int(r["year_start"]), _int(r["year_end"])
        era = _int(r["era"])
        if y0 is None or y1 is None or era is None or y0 > y1:
            problems.append(f"{r['layer_b_label']}/{r['item']}/{r['unit']}: unreadable era or years "
                            f"({r['era']!r}, {r['year_start']!r}-{r['year_end']!r})")
            continue
        r["_y0"], r["_y1"], r["_era"] = y0, y1, era
        series[(r["layer_b_label"], r["item"], r["unit"])].append(r)
        if r["disposition"] not in DISPOSITIONS:
            problems.append(f"{r['layer_b_label']}/{r['item']}: disposition {r['disposition']!r} "
                            f"is not one of {sorted(DISPOSITIONS)}")

    # A  shape
    for key, eras in sorted(series.items()):
        eras.sort(key=lambda r: r["_era"])
        name = "/".join(key)
        if [r["_era"] for r in eras] != list(range(1, len(eras) + 1)):
            problems.append(f"{name}: eras are not numbered 1..{len(eras)}")
        labels = [r["raw_label"] for r in eras]
        if len(set(labels)) < 2:
            problems.append(f"{name}: a splice needs two raw labels, has {sorted(set(labels))}")
        for a, b in zip(eras, eras[1:]):
            if not a["_y1"] < b["_y0"]:
                problems.append(f"{name}: era {a['_era']} ({a['raw_label']} {a['_y0']}-{a['_y1']}) "
                                f"does not end before era {b['_era']} ({b['raw_label']} "
                                f"{b['_y0']}-{b['_y1']}) begins -- eras must be in year order")
            if a["raw_label"] == b["raw_label"]:
                problems.append(f"{name}: eras {a['_era']} and {b['_era']} share raw label "
                                f"{a['raw_label']!r}; consecutive runs of one label are one era")
        want = "partition" if len(set(labels)) == len(labels) else "alternating"
        if any(r["shape"] != want for r in eras):
            problems.append(f"{name}: shape {sorted({r['shape'] for r in eras})} but its eras say "
                            f"{want!r}")
        per = collections.Counter()
        for r in eras:
            per[r["raw_label"]] += _int(r["n_distinct"]) or 0
            if (_int(r["n_distinct"]) or 0) > (_int(r["n_cells"]) or 0):
                problems.append(f"{name}: era {r['_era']} has more distinct values than cells")
        for lab, n in per.items():
            if n < MIN_ERA_DISTINCT:
                problems.append(f"{name}: raw label {lab!r} carries {n} distinct value(s) over its eras, "
                                f"under the floor of {MIN_ERA_DISTINCT} -- a coincidence, not an era")

    # B, C, D
    for key, eras in sorted(series.items()):
        name = "/".join(key)
        for r in eras:
            tag = f"{name} era {r['_era']} ({r['raw_label']} {r['_y0']}-{r['_y1']})"
            cover = covering(rules, key[0], key[1], key[2], r["_y0"], r["_y1"])
            ref = set(filter(None, r["reference"].split("/")))
            routed = set(filter(None, r["routed_polities"].split("/")))
            if r["disposition"] == "rerouted":
                if cover is None:
                    problems.append(f"{tag}: marked `rerouted` but no rule in "
                                    f"source_label_item_corrections.csv covers every year of it")
                elif cover != ref:
                    problems.append(f"{tag}: reference {sorted(ref)} but the covering rules send it "
                                    f"to {sorted(cover)}")
                if routed != ref:
                    problems.append(f"{tag}: rerouted to {sorted(ref)} but its rows sit on "
                                    f"{sorted(routed)}")
                if (_int(r["n_period_moved_other"]) or 0) != 0:
                    problems.append(f"{tag}: its rules move {r['n_period_moved_other']} period row(s) "
                                    f"that another raw label prints -- a period is a second time axis, "
                                    f"split the rule so neither half covers it")
            elif cover is not None:
                problems.append(f"{tag}: rules send every year of it to {sorted(cover)}, yet it is "
                                f"marked `{r['disposition']}` -- regenerate 48_era_segments.py")
            if r["disposition"] == "component" and not r["reference"]:
                problems.append(f"{tag}: a `component` era must point at the record of its "
                                f"understatement")
            if r["reference"].startswith("data_errors:"):
                if r["reference"].split(":", 1)[1] not in error_ids:
                    problems.append(f"{tag}: reference {r['reference']!r} is not in data_errors.csv")
            elif r["reference"].startswith("source_conventions:"):
                if r["reference"].split(":", 1)[1] not in conv_keys:
                    problems.append(f"{tag}: reference {r['reference']!r} is not a "
                                    f"source_conventions.csv key")
            if r["disposition"] == "routed":
                if not ref:
                    problems.append(f"{tag}: `routed` needs the polity it is routed to")
                elif not routed <= ref:
                    problems.append(f"{tag}: `routed` to {sorted(ref)} but its rows sit on "
                                    f"{sorted(routed - ref)} too")

    # E  pins
    by = collections.Counter(r["disposition"] for r in rows)
    print(f"era segments: {len(series)} series, {len(rows)} eras; {dict(sorted(by.items()))}")
    if len(series) != BASELINE_SERIES or len(rows) != BASELINE_ERAS:
        problems.append(f"{len(series)} series / {len(rows)} eras against the pinned "
                        f"{BASELINE_SERIES} / {BASELINE_ERAS}")
    for k in sorted(DISPOSITIONS):
        if by.get(k, 0) != BASELINE_BY_DISPOSITION.get(k, 0):
            problems.append(f"{by.get(k, 0)} `{k}` era(s) against the pinned "
                            f"{BASELINE_BY_DISPOSITION.get(k, 0)}")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("PASS: every era of a spliced series is dispositioned, and each disposition is backed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
