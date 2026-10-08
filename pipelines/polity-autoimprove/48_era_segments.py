#!/usr/bin/env python3
"""Cut every iia item series into the raw-label ERAS it is stitched from, and say where each era goes
(issue 443).

WHAT THIS GENERALISES. `20_item_provenance.py` grew a `split_candidate` status for a series that is two
raw labels in sequence -- `russia in europe` 1909-1916 then `ussr` 1930-1940 under one layer-B
`russian federation / sugar` series. That status is reachable only inside the `unattributable` branch
(no single label clears the 60% share floor), so a splice with a DOMINANT side is invisible to it: the
Syrian cotton series is 63% `french syria and lebanon`, therefore `attributable`, and its 1939-1945 era
from `french syria` alone never surfaces. `cell_attribution.csv` sees cells but, by design, only in the
`unattributable` series. Neither table says where an era's rows SHOULD go, which is the question the
issue asked.

This tool asks it of every iia (label, item, unit) series, whatever item_provenance called it.

HOW AN ERA IS FOUND -- the same three-axis identity the cell table uses, plus a floor per era.
  1. A dated layer-B cell is attributed to a raw label when EXACTLY ONE raw label prints that value
     for (product, variable, year), searching only the products `item_equivalences.csv` maps the item
     to (verdict not `defect`). Zero is excluded: a 0 matches every raw row printing 0.
  2. A raw label is a CANDIDATE for the series only when its uniquely attributed cells carry at least
     MIN_ERA_DISTINCT distinct values. This is item_provenance's distinctness filter applied per era:
     a label with two or three round values in a long series is how `jamaica cotton -> bulgaria` and
     `cyprus lemons -> union of south africa` look, and neither is an era.
  3. A series with two or more candidates is a SPLICE. A cell joins an era when exactly one CANDIDATE
     prints it (a round value another, non-candidate label also prints does not cut an era short).
     Those cells, ordered by year, are cut into RUNS of one label; each run is one row (an era).
  4. `shape` is `partition` when every candidate forms exactly one run (a dated succession that a year
     boundary separates), and `alternating` when a label returns after another (A-B-A): still
     separable by year, but each run must be dispositioned on its own.

WHY 4 AND NOT item_provenance's 6. The crosswalk restriction in (1) is what 20's distinctness floor
stands in for: 20 matches a series against all 403 raw labels on all products, so round values collide
across commodities, and only a high floor separates signal from that. Here a candidate must match on the
right product and variable AND be the only label doing so in that cell, which removes the
cross-commodity collisions outright. Measured 2026-10-07: at 4 every detected era is a real territory
for that commodity; the extra series admitted between 6 and 4 are `french lebanon` sesame 1922-1925
(four distinct values, 91 / 115 / 140 / 145 t) and the 1922-1925 `ussr in europe` / `ussr in asia`
eras, all of which the source prints as separate reporting units.

THE DISPOSITION is what the issue's remedy needs, and it is never inferred from magnitude. One of:
  `rerouted`   a rule in data/final/source_label_item_corrections.csv covers the era's years for this
               (label, item, unit), and `reference` is its polity. The era's rows sit there.
  `routed`     the era's raw label is the same territory as the polity its rows already reach through
               the year-scoped aliases -- a rename or a succession the alias map already models
               (`kingdom of serbs, croats and slovenes` -> `yugoslavia`; `british samoa` ->
               `new zealand western samoa`).
  `component`  the era publishes a PART of the routed territory and no polity for that part exists,
               so the rows stay and the understatement is recorded where `reference` points (a
               data_errors entry or a source convention).
  `open`       none of the above has been decided; `note` says why.
`routed`/`component`/`open` come from DISPOSITIONS below, keyed on (layer-B label, raw label) and a year
window, because they are judgements about what a label MEANS. `rerouted` is never curated: it is read
from the corrections table, so deleting a rule turns its eras back into `open` here and the gate fails.

WHAT A ROW DOES NOT CLAIM. That the cells in an era's span which are NOT uniquely attributed belong to the
era's label. They are counted (`n_unattributed_in_span`) because a corrections rule keyed on years moves
them with the era; a reader deciding a reroute must look at them.

Usage:
  python3 pipelines/polity-autoimprove/48_era_segments.py            # report
  python3 pipelines/polity-autoimprove/48_era_segments.py --write    # refresh state/era_segments.csv
  python3 pipelines/polity-autoimprove/48_era_segments.py --check    # fail if stale
"""
from __future__ import annotations

import argparse
import collections
import csv
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "era_segments.csv")
EQUIV = os.path.join(STATE, "item_equivalences.csv")
MATCHED = os.path.join(STATE, "matched_rows.parquet")
CORRECTIONS = os.path.join(REPO, "data/final/source_label_item_corrections.csv")
PANEL_DEFAULT = os.path.expanduser(
    os.environ.get("WHEP_LAYER_B") or os.environ.get("WHEP_LAYERB")
    or "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet")
RAW_DEFAULT = os.path.expanduser(os.environ.get(
    "WHEP_IIA_RAW",
    "~/3itkt6h41pb7jdan/2025-10-06_iia-dataframe/outputs/processed data/harmonized_data.xlsx"))

UNIT_VARIABLE = {"ha": "area", "tonnes": "production"}
MIN_ERA_DISTINCT = 4

FIELDS = ("layer_b_label", "item", "unit", "shape", "era", "raw_label", "raw_products",
          "year_start", "year_end", "n_cells", "n_distinct", "n_unattributed_in_span",
          "n_period_same_label", "n_period_other_label", "n_period_moved_other",
          "routed_polities", "disposition",
          "reference", "note")

_SER_PREWAR = ("the label's pre-1918 cells (routed by year to Serbia) have no settled territory: "
               "layerb-nested-reporting-levels-one-polity records that they are neither pre-war "
               "Serbia's figures nor the future federation's, and magnitude cannot name it")
_RUS_HALVES = "source_conventions:iia|russian federation|*"
_USA_SUGAR = "data_errors:iia-item-series-switch-raw-products"

# (layer-B label, raw label, first year, last year) -> (disposition, reference, note). An era matches
# when its span lies inside the window. Only `routed`, `component` and `open` live here; `rerouted` is
# read from the corrections table so it cannot be asserted without the rule that does it.
DISPOSITIONS = {
    ("russian federation", "ussr", 1921, 1945):
        ("routed", "F228-1921-1940/F228-1940-1945", "whole-USSR series on the USSR-scope polity"),
    ("russian federation", "russia in europe", 1909, 1920):
        ("component", _RUS_HALVES,
         "European half of the Empire; no continental-half polity exists, so the rows stay as a "
         "documented understatement (tobacco's Asian half is recorded dropped in "
         "iia-russia-asian-component-dropped)"),
    ("russian federation", "russia in asia", 1909, 1920):
        ("component", _RUS_HALVES,
         "Asian half of the Empire; for cotton it is nearly the whole crop, but no half polity exists"),
    ("russian federation", "ussr in europe", 1921, 1925):
        ("component", _RUS_HALVES,
         "the 1925-26 volume prints the European half as its own reporting unit for 1922-1925"),
    ("russian federation", "ussr in asia", 1921, 1925):
        ("component", _RUS_HALVES,
         "the 1925-26 volume prints the Asian half as its own reporting unit for 1922-1925"),
    ("serbia", "kingdom of serbs, croats and slovenes", 1918, 1929):
        ("routed", "F248-1920-1947", "the Kingdom's own name until 1929; same territory as `yugoslavia`"),
    ("serbia", "kingdom of serbs, croats and slovenes", 1909, 1929):
        ("open", "data_errors:layerb-nested-reporting-levels-one-polity", _SER_PREWAR),
    ("serbia", "yugoslavia", 1929, 1945):
        ("routed", "F248-1920-1947", "Yugoslavia under its post-1929 name"),
    ("united states of america", "usa", 1909, 1945, "sugar raw centrifugal"):
        ("component", _USA_SUGAR,
         "`usa` / sugar: BEET only -- the mainland beet crop, all cane missing (39-81% of US sugar)"),
    ("united states of america", "usa: louisiana and florida", 1909, 1945, "sugar raw centrifugal"):
        ("component", _USA_SUGAR,
         "two cane states published under the national label (4-21% of US sugar); no polity for them "
         "exists, and the 1930-1938 cells between the two eras are a cane sum over usa + puerto rico "
         "+ hawaii that matches no single raw label"),
    ("indonesia", "dutch java and madura", 1900, 1945):
        ("open", "data_errors:iia-indonesia-is-java-and-madura",
         "a single 1941 tobacco-area cell (6,000 ha) that `french annam` also prints, so it is not "
         "uniquely Java's; issue 372 and 443's rules move the Java eras that are"),
    ("indonesia", "dutch east indies", 1900, 1945):
        ("routed", "IDN-1800-1945", "the whole archipelago, on the Dutch East Indies polity"),
    ("syrian arab republic", "french syria", 1922, 1945):
        ("routed", "SYR-1922-1946", "Syria alone, on the Syrian mandate polity"),
    ("niger", "french niger", 1922, 1945):
        ("routed", "NER-1922-1947", "the colony itself"),
    ("guadeloupe", "french guadeloupe and dependencies", 1900, 1945):
        ("routed", "GLP-1816-2025", "Guadeloupe's polity includes its dependencies; a label rename"),
    ("guadeloupe", "french guadeloupe", 1900, 1945):
        ("routed", "GLP-1816-2025", "Guadeloupe"),
    ("samoa", "british samoa", 1909, 1921):
        ("routed", "WSM-1900-2025",
         "Western Samoa under its occupation-era name; same islands as `new zealand western samoa`"),
    ("samoa", "new zealand western samoa", 1920, 1945):
        ("routed", "WSM-1900-2025", "the New Zealand mandate over Western Samoa"),
    ("ethiopia pdr", "ethiopian empire", 1936, 1945):
        ("routed", "ETH-1936-1941/ETH-1941-1952", "Ethiopia"),
    ("ethiopia pdr", "italian east africa", 1928, 1937):
        ("open", "",
         "a persistent column header: the label names the 1936-1941 federation but supplies "
         "1933-1935 too (cell_attribution.py docstring; issue 372). Eritrea and Italian Somaliland "
         "print no coffee of their own in this extract, which is consistent with Ethiopia's crop, "
         "but availability is not identity and no reroute is asserted"),
    ("australia", "australia", 1900, 1945):
        ("routed", "AUS-1901-2025", "the Commonwealth"),
    ("australia", "australia: queensland", 1900, 1945):
        ("open", "",
         "the state's figure alternates with the Commonwealth's inside one series (issue 443's "
         "interleaved class); a year-keyed rule cannot separate a whole from its part"),
    ("united states of america", "usa and canada", 1909, 1945, "n"):
        ("open", "",
         "a two-country total under the US label (issue 372); no polity for the pair exists, and "
         "whether to unroute it or keep it as a recorded overstatement is undecided"),
    ("united states of america", "usa", 1909, 1945, "n"):
        ("routed", "USA-1867-1959", "the United States"),
    ("austria", "austria", 1919, 1945):
        ("routed", "AUT-1919-2025", "the First Republic"),
}


def norm(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def _disposition(label, raw_label, item, y0, y1):
    """The curated entry whose window contains [y0, y1]; the NARROWEST wins, so a specific window
    (1918-1929) overrides a wider fallback (1909-1929) for the same pair. A key may carry a fifth
    element, the layer-B item, when the judgement is about one commodity only (`usa` is beet sugar
    in the sugar series and something else entirely in `n`)."""
    best = None
    for key, val in DISPOSITIONS.items():
        lab, raw, a, b = key[:4]
        if len(key) > 4 and key[4] != item:
            continue
        if lab == label and raw == raw_label and a <= y0 and y1 <= b:
            if best is None or (b - a) < best[0]:
                best = (b - a, val)
    return best[1] if best else None


def _rules():
    with open(CORRECTIONS, newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if r["source"] == "iia"]


def _mine(rules, label, item, unit):
    return [r for r in rules if r["source_label"] == label and r["item"] == item
            and r.get("unit", "") in ("", unit) and not r.get("indicator", "")]


def period_moved(rules, label, item, unit, period):
    """Does some rule move this period-average row? The matcher's reading: BOTH ends inside one
    rule's years (matchlib.label_item_rule_covers)."""
    b = re.findall(r"\d{4}", period)
    if len(b) < 2:
        return False
    return any(int(r["year_start"]) <= int(b[0]) and int(b[-1]) <= int(r["year_end"])
               for r in _mine(rules, label, item, unit))


def rules_covering(rules, label, item, unit, y0, y1):
    """Rules on (iia, label, item) whose unit scope admits `unit` and which together cover every year
    of [y0, y1]. Returns the sorted polity codes, or None when some year is uncovered."""
    mine = _mine(rules, label, item, unit)
    pols = set()
    for y in range(y0, y1 + 1):
        hit = [r for r in mine if int(r["year_start"]) <= y <= int(r["year_end"])]
        if not hit:
            return None
        pols.update(r["polity_code"] for r in hit)
    return sorted(pols)


def build(panel_path, raw_path):
    import pandas as pd

    equiv = collections.defaultdict(set)
    with open(EQUIV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["verdict"] != "defect":
                equiv[r["item"]].add(str(r["raw_product"]).strip().lower())

    raw = pd.read_excel(raw_path)
    raw.columns = [c.strip().lower() for c in raw.columns]
    raw = raw[raw["value"].notna()]
    idx = collections.defaultdict(list)       # (product, variable, when) -> [(label, value)]
    for c, p, var, y, v in zip(raw["country"].astype(str).str.strip().str.lower(),
                               raw["product"].astype(str).str.strip().str.lower(),
                               raw["variable"], raw["year"].astype(str).str.strip(), raw["value"]):
        try:
            idx[(p, var, y)].append((c, float(v)))
        except (TypeError, ValueError):
            pass

    d = pd.read_parquet(panel_path)
    if "is_aggregate" in d.columns:
        d = d[~d["is_aggregate"].astype(bool)]
    d = d[(d["source"] == "iia") & d["value"].notna() & (d["value"] != 0)]

    def attribute(item_n, unit, when, value):
        var = UNIT_VARIABLE.get(unit)
        prods = equiv.get(item_n, ())
        if var is None or not prods:
            return None, ()
        hits = set()
        for p in sorted(prods):
            for lab, val in idx.get((p, var, when), ()):
                if abs(val - value) <= 1e-6 * max(abs(value), 1.0):
                    hits.add((lab, p))
        labs = {lab for lab, _p in hits}
        return (next(iter(labs)) if len(labs) == 1 else None), hits

    routed = None
    if os.path.exists(MATCHED):
        m = pd.read_parquet(MATCHED, columns=["source", "source_label_raw", "item", "unit",
                                              "year", "whep_code"])
        m = m[(m["source"] == "iia") & m["year"].notna()]
        routed = collections.defaultdict(set)
        for lab, it, un, y, w in zip(m["source_label_raw"], m["item"], m["unit"], m["year"],
                                     m["whep_code"]):
            routed[(lab, it, un, int(y))].add(str(w))

    rules = _rules()
    out = []
    for (label, item, unit), g in d.groupby(["country", "item", "unit"], sort=True):
        item_n = norm(item)
        cells, periods = [], []
        for t in g.itertuples():
            if pd.notna(t.year):
                lab, hits = attribute(item_n, unit, str(int(t.year)), float(t.value))
                cells.append((int(t.year), round(float(t.value), 1), lab, hits))
            elif isinstance(t.period, str):
                lab, _h = attribute(item_n, unit, t.period.strip(), float(t.value))
                periods.append((t.period.strip(), lab))
        distinct = collections.defaultdict(set)
        for y, v, lab, _h in cells:
            if lab:
                distinct[lab].add(v)
        cands = {lab for lab, vs in distinct.items() if len(vs) >= MIN_ERA_DISTINCT}
        if len(cands) < 2:
            continue
        # ASSIGNMENT IS AMONG CANDIDATES. Candidacy needs cells no OTHER raw label prints; once the
        # candidates are known, a cell joins an era when exactly one CANDIDATE prints it. A round
        # 7,000 ha that `dutch guiana` coffee also prints cannot make `dutch guiana` an era (it has no
        # unique cells), so it must not cut `british malaya`'s era short either -- which it did when
        # assignment required global uniqueness, ending that era at 1934 instead of 1944.
        seq = []
        for y, v, _lab, hits in cells:
            mine = {lab for lab, _p in hits} & cands
            if len(mine) == 1:
                seq.append((y, v, next(iter(mine)), hits))
        seq.sort(key=lambda c: (c[0], c[1], c[2]))
        runs = []
        for y, v, lab, hits in seq:
            if runs and runs[-1]["raw_label"] == lab:
                runs[-1]["cells"].append((y, v, hits))
            else:
                runs.append({"raw_label": lab, "cells": [(y, v, hits)]})
        shape = "partition" if len(runs) == len(cands) else "alternating"
        for i, run in enumerate(runs, start=1):
            ys = [y for y, _v, _h in run["cells"]]
            y0, y1 = min(ys), max(ys)
            in_span = [c for c in cells if y0 <= c[0] <= y1]
            prods = sorted({p for _y, _v, hits in run["cells"] for lab, p in hits
                            if lab == run["raw_label"]})
            same = other = 0
            for per, lab in periods:
                b = re.findall(r"\d{4}", per)
                if len(b) >= 2 and y0 <= int(b[0]) and int(b[-1]) <= y1:
                    if lab == run["raw_label"]:
                        same += 1
                    elif lab is not None:
                        other += 1
            pols = ""
            if routed is not None:
                pols = "/".join(sorted({w for y in ys for w in routed.get((label, item, unit, y), ())}))
            rec = {"layer_b_label": label, "item": item, "unit": unit, "shape": shape, "era": i,
                   "raw_label": run["raw_label"], "raw_products": "; ".join(prods),
                   "year_start": y0, "year_end": y1, "n_cells": len(ys),
                   "n_distinct": len({v for _y, v, _h in run["cells"]}),
                   "n_unattributed_in_span": len(in_span) - len(ys),
                   "n_period_same_label": same, "n_period_other_label": other,
                   "routed_polities": pols}
            cover = rules_covering(rules, label, item, unit, y0, y1)
            # A PERIOD ROW IS A SECOND TIME AXIS (issue 443's own retraction: a `1934-1938` row read
            # as a dated 1938). A year-keyed rule moves every period row inside it, and the late
            # volumes restate `1934-1938` for a narrower territory than the dated cells around it
            # (Syria's combined-unit eras), so count the rows a rule would drag across that belong
            # to ANOTHER label. The gate requires zero for a rerouted era.
            rec["n_period_moved_other"] = sum(
                1 for per, lab in periods
                if lab is not None and lab != run["raw_label"]
                and period_moved(rules, label, item, unit, per)
                and y0 <= int(re.findall(r"\d{4}", per)[0]) <= y1) if cover else 0
            if cover:
                rec.update(disposition="rerouted", reference="/".join(cover),
                           note="source_label_item_corrections.csv moves this era's years")
            else:
                cur = _disposition(label, run["raw_label"], item, y0, y1)
                if cur:
                    rec.update(disposition=cur[0], reference=cur[1], note=cur[2])
                else:
                    rec.update(disposition="open", reference="",
                               note="no disposition recorded for this era")
            out.append(rec)
    return out


def write(rows, path):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as fh:
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
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--layer-b", default=PANEL_DEFAULT)
    ap.add_argument("--raw", default=RAW_DEFAULT)
    a = ap.parse_args()
    for p in (a.layer_b, a.raw, MATCHED):
        if not os.path.exists(p):
            print(f"SKIP: input absent ({p})")
            return 0
    rows = build(a.layer_b, a.raw)
    series = {(r["layer_b_label"], r["item"], r["unit"]) for r in rows}
    disp = collections.Counter(r["disposition"] for r in rows)
    shapes = collections.Counter(r["shape"] for r in {(r["layer_b_label"], r["item"], r["unit"]):
                                                      r for r in rows}.values())
    print(f"{len(series)} iia series are spliced from two or more raw labels "
          f"({dict(sorted(shapes.items()))}); {len(rows)} eras")
    print(f"  dispositions: {dict(sorted(disp.items()))}")
    for r in rows:
        print(f"  {r['layer_b_label'][:22]:22} {r['item'][:22]:22} {r['unit']:6} "
              f"#{r['era']} {r['raw_label'][:36]:36} {r['year_start']}-{r['year_end']} "
              f"n={r['n_cells']:<3} {r['routed_polities'][:30]:30} {r['disposition']} {r['reference']}")
    if a.check:
        if not os.path.exists(OUT):
            print(f"MISSING {OUT}; run with --write", file=sys.stderr)
            return 1
        with open(OUT, newline="", encoding="utf-8") as fh:
            have = list(csv.DictReader(fh))
        want = [{k: str(r[k]) for k in FIELDS} for r in rows]
        if have != want:
            print(f"STALE {OUT}: {len(have)} row(s) on disk, {len(want)} rebuilt; rerun with --write "
                  "(after re-running 01_match_and_findings.py if routing changed)", file=sys.stderr)
            return 1
        print(f"OK {os.path.basename(OUT)} matches a fresh rebuild ({len(have)} rows)")
    if a.write:
        write(rows, OUT)
        print(f"wrote {OUT} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
