#!/usr/bin/env python3
"""What does the consumer publish where several panel rows share one key?

`.prepare_historical_production()` in the WHEP R package reduces duplicate keys with
`mean(value, na.rm = TRUE)` over (year, area, item..., unit) -- no label column, no source column.
`pipelines/polity-autoimprove/30_consumer_key_collapse.py` enumerates every group that key produces from
the layer-B panel and writes `state/collapse_groups.csv`; the panel is gitignored and absent in CI, so this
gate reads the committed table. (The generator is deliberately NOT numbered 27: `27_series_collapses.py`
already uses "collapse" for a series dropping to zero over time, which is a different phenomenon from the
single-year aggregation measured here.) Same arrangement as `validate_same_polity_overlaps.py`.

WHY A SECOND TABLE ALONGSIDE `same_polity_overlaps.csv` (issue 451). That screen groups by
`(polity, source)` and reports LABEL PAIRS. This one drops both label and source from the key, because
that is what the consumer does, and the difference is not marginal:

    differing collapse groups                                     1,977
      one label only                                              1,436
      more than one label anywhere                                  541
      a SINGLE source contributing two labels -- i.e. reachable       60   = 3.0%

`germany` alone supplies TEN rows for population 1937 on DEU-1920-1938, so there is no pair to report.
A label-pair screen is therefore not a partial view of this defect; it is very nearly disjoint from it.

WHAT IS PINNED, AND WHAT DELIBERATELY IS NOT. The group counts above are a routine SCREENING total:
they move whenever the panel or the matcher legitimately moves, and a gate that pinned them would fail
ALL 5 ARMS WERE VERIFIED TO FIRE on 2026-08-20, by mutating this table to trigger each in turn.
An arm that cannot fire passes every run while asserting nothing, and this repo has shipped three of
those (issues 407, 412, 420), so "the gate is green" is only meaningful once each arm is known live.
Verified: an unknown verdict (A); a mean outside its group's range (B, permanent case); an anchor
rewritten as agreement (C, permanent case); a composition contradicting n_labels (D); a
duplicate_class contradicting n_indicators (E, permanent case).

on every honest regeneration. They are printed, not asserted. What IS pinned both ways is the handful of
CURATED anchors below -- the specific groups quoted in issues 411, 449 and 451 -- because those are
findings a human confirmed, and if one silently changes its value the issue text has gone stale.
Arithmetic and vocabulary invariants are pinned unconditionally: they cannot legitimately break.

Checks:
  A. VOCABULARY AND SHAPE -- the header, the two verdicts, the four compositions, n_rows >= 2.
  B. ARITHMETIC -- published_mean lies within [v_min, v_max]; `values_identical` holds exactly when
     v_min == v_max and n_distinct == 1; ratio_mean_max agrees with published_mean / v_max. This is the
     arm that catches a rewritten aggregation: a table claiming a mean outside its own range is
     describing an operation that is not a mean.
  C. THE CURATED ANCHORS still read as the issues say they do.
  D. CONSISTENCY WITH THE COMPOSITION FIELD -- `one_label` iff exactly one label is listed, and
     likewise for sources, so the counts printed in C cannot drift from the rows they summarise.
"""
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/collapse_groups.csv")

FIELDS = ["whep_code", "item", "unit", "year", "n_rows", "n_distinct", "n_labels", "n_sources",
          "n_indicators", "verdict", "composition", "duplicate_class", "v_min", "v_max",
          "published_mean", "ratio_mean_max", "labels", "sources"]
DUP_CLASSES = {"true_duplicate_key", "item_code_collision"}
VERDICTS = {"values_identical", "values_differ"}
COMPOSITIONS = {"one_label_one_source", "one_label_several_sources",
                "several_labels_one_source", "several_labels_several_sources"}

# --- C. curated anchors: (code, item, unit, year) -> the facts the issues assert ------------------
# Each entry is quoted in an open issue. A change here is not necessarily a regression -- it may be a
# correct reroute -- but it MUST be noticed, because the issue text stops being true.
ANCHORS = {
    ("KOR-1948-2025", "r_fao_population_1952_10_18", "1000 people", "1951"): dict(
        verdict="values_differ", v_min="20500", v_max="29300", published_mean="24900",
        why="issue 451: 29,300 is the whole Korean peninsula in 1951 and 20,500 is South Korea "
            "alone. Both route to KOR-1948-2025, so the published figure is 24,900 -- a number for "
            "no territory. The two cannot both describe one territory, which makes this decidable "
            "without any external source"),
    ("DEU-1920-1938", "r_fao_population_1952_10_18", "1000 people", "1937"): dict(
        verdict="values_differ", n_rows="10", v_max="57576", published_mean="13854.5",
        why="issue 411: TEN rows for one polity-item-year, the 57,576 Reich total beside its "
            "post-war subdivisions, published as 13,854.5 -- 24% of the Reich. Four labels are "
            "involved but `germany` alone supplies five of the ten rows, which is why the "
            "label-pair screen reports one cell here and this table reports ten rows"),
    ("ETH-1941-1952", "coffee, green", "tonnes", "1945"): dict(
        verdict="values_identical", v_min="17000", v_max="17000", published_mean="17000",
        why="issue 451: `ethiopia` and `ethiopia pdr` agree to the digit, so `mean` returns the "
            "value and NOTHING is double-counted today. This anchor exists to keep that withdrawal "
            "honest -- if it ever reads values_differ, the tidy-up became a real correctness fix"),
}


def main() -> int:
    problems = []
    if not os.path.exists(TABLE):
        print(f"FAIL: missing {os.path.relpath(TABLE, REPO)}", file=sys.stderr)
        return 1
    with open(TABLE, newline="") as fh:
        rd = csv.DictReader(fh)
        if rd.fieldnames != FIELDS:
            print(f"FAIL: {os.path.relpath(TABLE, REPO)} header is {rd.fieldnames}, expected {FIELDS}",
                  file=sys.stderr)
            return 1
        rows = list(rd)

    for i, r in enumerate(rows, start=2):
        where = f"line {i} {r['whep_code']}/{r['item']}/{r['year']}"
        # --- A. vocabulary and shape ---
        if r["verdict"] not in VERDICTS:
            problems.append(f"A {where}: verdict {r['verdict']!r} not in {sorted(VERDICTS)}")
        if r["composition"] not in COMPOSITIONS:
            problems.append(f"A {where}: composition {r['composition']!r} not in {sorted(COMPOSITIONS)}")
        try:
            n_rows, n_dist = int(r["n_rows"]), int(r["n_distinct"])
            n_lab, n_src = int(r["n_labels"]), int(r["n_sources"])
            vmin, vmax, mean = float(r["v_min"]), float(r["v_max"]), float(r["published_mean"])
        except ValueError:
            problems.append(f"A {where}: a numeric field is not numeric")
            continue
        if n_rows < 2:
            problems.append(f"A {where}: n_rows={n_rows}; a group of one collapses to itself and "
                            f"must not be listed at all")
        # --- B. arithmetic ---
        if vmin > vmax:
            problems.append(f"B {where}: v_min {vmin} > v_max {vmax}")
        elif not (vmin - 1e-6 <= mean <= vmax + 1e-6):
            problems.append(f"B {where}: published_mean {mean} lies outside [{vmin}, {vmax}] -- a "
                            f"mean cannot; the aggregation being described is not mean(value)")
        ident = r["verdict"] == "values_identical"
        if ident != (abs(vmax - vmin) <= 1e-9 * max(1.0, abs(vmax))):
            problems.append(f"B {where}: verdict {r['verdict']} disagrees with v_min/v_max "
                            f"({vmin}, {vmax})")
        if ident and n_dist != 1:
            problems.append(f"B {where}: values_identical but n_distinct={n_dist}")
        if not ident and n_dist < 2:
            problems.append(f"B {where}: values_differ but n_distinct={n_dist}")
        if r["ratio_mean_max"] and vmax:
            want = mean / vmax
            if abs(float(r["ratio_mean_max"]) - want) > 1e-6:
                problems.append(f"B {where}: ratio_mean_max {r['ratio_mean_max']} != "
                                f"published_mean/v_max ({want:.6f})")
        # --- E. duplicate_class must follow n_indicators ---
        # The consumer's key excludes `indicator`, which names the MEASURE within an item code, so a
        # group holding several indicators is several distinct statistics being averaged -- a real
        # defect, but issue 13's, not a whole/part collision, and no routing change would touch it.
        # Counting the two together overstates duplicate reporting by about a fifth (1,995 -> 1,577).
        # This arm stops the classification drifting from the column it rests on.
        try:
            n_ind = int(r["n_indicators"])
        except (KeyError, ValueError):
            problems.append(f"E {where}: n_indicators {r.get('n_indicators')!r} is not an integer")
            n_ind = None
        if r["duplicate_class"] not in DUP_CLASSES:
            problems.append(f"E {where}: duplicate_class {r['duplicate_class']!r} not in "
                            f"{sorted(DUP_CLASSES)}")
        elif n_ind is not None:
            want = "true_duplicate_key" if n_ind == 1 else "item_code_collision"
            if r["duplicate_class"] != want:
                problems.append(
                    f"E {where}: {n_ind} distinct indicator(s) but duplicate_class is "
                    f"{r['duplicate_class']!r}, expected {want!r}. With >1 indicator the spread is "
                    f"partly distinct MEASURES sharing an item code (issue 13), which routing cannot "
                    f"fix; calling it a duplicate key sends the reader at the wrong remedy")
        if n_ind is not None and not (1 <= n_ind <= n_rows):
            problems.append(f"E {where}: n_indicators {n_ind} outside [1, n_rows={n_rows}]")

        # --- D. composition agrees with the listed labels/sources ---
        labs = [x for x in r["labels"].split(" | ") if x]
        srcs = [x for x in r["sources"].split(" | ") if x]
        if len(labs) != n_lab:
            problems.append(f"D {where}: n_labels={n_lab} but {len(labs)} label(s) listed")
        if len(srcs) != n_src:
            problems.append(f"D {where}: n_sources={n_src} but {len(srcs)} source(s) listed")
        want_comp = ("one_label" if n_lab == 1 else "several_labels") + "_" + \
                    ("one_source" if n_src == 1 else "several_sources")
        if r["composition"] != want_comp:
            problems.append(f"D {where}: composition {r['composition']!r} but {n_lab} label(s) and "
                            f"{n_src} source(s) say {want_comp!r}")

    # --- C. curated anchors ---
    by_key = {(r["whep_code"], r["item"], r["unit"], r["year"]): r for r in rows}
    for key, want in ANCHORS.items():
        r = by_key.get(key)
        if r is None:
            problems.append(f"C {'/'.join(key)}: anchor group is GONE from the table. It is quoted "
                            f"in an open issue: {want['why']}")
            continue
        for f, v in want.items():
            if f == "why":
                continue
            if r[f] != v:
                problems.append(f"C {'/'.join(key)}: {f} is {r[f]!r}, expected {v!r}. {want['why']}")

    # --- report ---
    diff = [r for r in rows if r["verdict"] == "values_differ"]
    comp: dict[str, int] = {}
    for r in diff:
        comp[r["composition"]] = comp.get(r["composition"], 0) + 1
    print(f"{len(rows)} collapse group(s) hold >1 row: {len(rows) - len(diff)} values_identical, "
          f"{len(diff)} values_differ")
    for k in sorted(comp):
        print(f"  {k:32} {comp[k]}")
    dc: dict[str, int] = {}
    for r in diff:
        dc[r["duplicate_class"]] = dc.get(r["duplicate_class"], 0) + 1
    for k in ("true_duplicate_key", "item_code_collision"):
        print(f"  {k:24} {dc.get(k, 0)}")
    reach = comp.get("several_labels_one_source", 0)
    if diff:
        print(f"  reachable by a per-source label-pair screen: {reach} "
              f"({100.0 * reach / len(diff):.1f}% of differing groups)")
    print(f"curated anchors checked: {len(ANCHORS)}")

    if problems:
        print(f"FAIL: {len(problems)} collapse-group problem(s)", file=sys.stderr)
        for p in problems[:40]:
            print("  - " + p, file=sys.stderr)
        return 1
    print("PASS: the table the consumer's collapse key produces is arithmetically consistent and "
          "its curated anchors still read as the issues describe")
    return 0


if __name__ == "__main__":
    sys.exit(main())
