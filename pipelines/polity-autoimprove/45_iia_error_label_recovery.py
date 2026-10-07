#!/usr/bin/env python3
"""Where would the IIA extract's 1,237 `[error]`-labelled rows go if their labels were repaired?
(issue 493)

WHY THIS IS A TABLE AND NOT A ROW IN source_label_ocr_corrections.csv. The repo's two label
correction mechanisms -- the OCR spelling table and the item-scoped table -- both rewrite labels
of LAYER B rows inside 01_match_and_findings.py. The `[error]` rows never reach layer B: the raw
extract (`harmonized_data.xlsx`) is produced by the upstream IIA project, whose cleaning table
deliberately rewrites each unreadable country cell to `[error] <text>` and leaves it without a
modern country, and layer B's iia block is then built from the rows that DO have one. Measured:
layer B carries 0 rows with an `[error]` label. A correction keyed on `[error] inde` would
therefore hit 0 rows in stage 01, pass every gate, and route nothing. The repair has to happen
where the label is lost -- upstream, in the extract's cleaning table -- and this repo's job is to
say, with evidence, what each label really is.

THE TABLE. `state/iia_error_label_crosswalk.csv` has one row per `[error]` label (all 93):

  status   certain               the territory is established from the raw extract itself --
                                 its slot in the document, the absence of the territory's own
                                 row there, and a cell or period-average identity with that
                                 territory's properly-labelled series. `correct_label` is the
                                 label in the EXTRACT's own vocabulary (`british india`, not
                                 `India`), so the upstream fix is a one-cell edit.
           uncertain_territory   a territory row, but the words that name it are lost (the
                                 French/British half of a mandate, a truncated sub-territory)
           component_not_total   a component printed under a territory that already has its
                                 own row (Nyasaland's native-grown tobacco, Spain's interplanted
                                 vines). Relabelling it would put two values on one cell, which
                                 the consumer AVERAGES; it needs summing, not relabelling.
           not_a_territory       a total line or a column heading
           trade_only            no production-side row at all; layer B's iia block is
                                 production/area only, so these have no destination there

THIS SCRIPT re-derives every label's row counts from the raw extract and refuses if they drift
(the table was adjudicated over those rows), then measures what the certain repairs would do:
which layer-B label each correct label feeds (by value fingerprint -- the extract's labels are
renamed on the way into layer B: `british india` -> `india`), which polity the matcher resolves
each row to, how many rows are of a product layer B carries at all, and how many duplicate a
value layer B already holds. It writes nothing.

NOT A GATE. The raw extract and layer B live outside the repository, so CI cannot run this; it
SKIPs when either is absent, like 15_label_provenance.py.

Usage:
  python3 pipelines/polity-autoimprove/45_iia_error_label_recovery.py
"""
from __future__ import annotations

import csv
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
TABLE = os.path.join(HERE, "state/iia_error_label_crosswalk.csv")
POLDB = os.path.join(REPO, "data/final/polities_database.csv")
ALIASES = os.path.join(HERE, "state/applied_aliases.csv")
DEFAULT_RAW = os.path.expanduser(os.environ.get(
    "WHEP_IIA_RAW",
    "~/3itkt6h41pb7jdan/2025-10-06_iia-dataframe/outputs/processed data/harmonized_data.xlsx"))
DEFAULT_PANEL = os.path.expanduser(
    os.environ.get("WHEP_LAYER_B") or os.environ.get("WHEP_LAYERB")
    or "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet")
COMMON_NAMES = os.environ.get(
    "WHEP_COMMON_NAMES",
    os.path.expanduser("~/Nextcloud/WHEP_ERC 2025/Sources/datasets/unclassified_datasets/"
                       "Other polities/data/whep-source/common_names.csv"))

# The same production-side set 15_label_provenance.py uses; everything else is trade.
PRODUCTION_VARIABLES = frozenset({
    "production", "area", "bearing area", "planted area", "dry production",
    "laying hens", "number", "production of cocoons", "eggs for incubation",
})
STATUSES = ("certain", "uncertain_territory", "component_not_total", "not_a_territory",
            "trade_only")
# A raw product counts as CARRIED by layer B when at least this share of its positive
# production-side cells reappear in layer B's iia block by (year, rounded value). Carried
# products sit far above it (cotton, tea, coffee) and dropped ones near zero.
CARRIED_SHARE = 0.5


def _key(year, value):
    return (str(year), round(float(value)))


def main() -> int:
    if not (os.path.exists(DEFAULT_RAW) and os.path.exists(DEFAULT_PANEL)):
        print("SKIP: raw IIA extract or layer B absent -- this measurement needs both")
        return 0
    import pandas as pd
    sys.path.insert(0, HERE)
    import matchlib

    with open(TABLE, newline="", encoding="utf-8") as fh:
        table = list(csv.DictReader(fh))
    problems = []
    for r in table:
        if r["status"] not in STATUSES:
            problems.append(f"{r['raw_label']!r}: unknown status {r['status']!r}")
        if (r["status"] == "certain") != bool(r["correct_label"].strip()):
            problems.append(f"{r['raw_label']!r}: a correct_label belongs on certain rows only")
        if not r["evidence"].strip():
            problems.append(f"{r['raw_label']!r}: no evidence")

    raw = pd.read_excel(DEFAULT_RAW, dtype=str)
    raw["v"] = pd.to_numeric(raw["value"], errors="coerce")
    raw["prod_side"] = raw["variable"].isin(PRODUCTION_VARIABLES)
    err = raw[raw["country"].fillna("").str.startswith("[error]")]

    # 1. The table must still describe the extract it was adjudicated over.
    observed = {lab: (len(g), int(g["prod_side"].sum())) for lab, g in err.groupby("country")}
    tabled = {r["raw_label"]: (int(r["rows"]), int(r["production_side_rows"])) for r in table}
    for lab in sorted(set(observed) | set(tabled)):
        if observed.get(lab) != tabled.get(lab):
            problems.append(f"{lab!r}: extract has {observed.get(lab)} (rows, production-side), "
                            f"table records {tabled.get(lab)}")
    print(f"[error] labels: {len(observed)} in the extract, {len(tabled)} tabled; "
          f"{sum(n for n, _ in observed.values()):,} rows")
    by_status = defaultdict(lambda: [0, 0, 0])
    for r in table:
        s = by_status[r["status"]]
        s[0] += 1
        s[1] += int(r["rows"])
        s[2] += int(r["production_side_rows"])
    for st in STATUSES:
        n, rows, ps = by_status[st]
        print(f"  {st:<20} {n:>3} labels  {rows:>5} rows  {ps:>4} production-side")
    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)")
        for p in problems:
            print("  " + p)
        return 1

    # 2. What the certain repairs would feed.
    import extdata
    lb = pd.read_parquet(DEFAULT_PANEL)
    # Layer B's `polity_code` holds lowercase ISO codes (issue 95); rename it so nothing here can
    # join it to a real polity code. Only `iso3c` is read below.
    lb = extdata.rename_layer_b_misnamed(
        lb, polity_codes=set(pd.read_csv(POLDB)["polity_code"]), where="layer B")
    iia = lb[(lb["source"] == "iia") & ~lb["is_aggregate"].astype(bool)].copy()
    iia["v"] = pd.to_numeric(iia["value"], errors="coerce")
    iia["yk"] = iia["year"].astype("string").fillna(iia["period"])
    iia = iia[iia["v"] > 0]
    where = defaultdict(Counter)                   # (year, value) -> layer-B labels holding it
    for yk, v, c in zip(iia["yk"], iia["v"], iia["country"]):
        where[_key(yk, v)][c] += 1
    iso_of = iia.dropna(subset=["iso3c"]).groupby("country")["iso3c"].agg(
        lambda s: s.mode().iat[0]).to_dict()

    ps = raw[raw["prod_side"] & (raw["v"] > 0)]
    carried = {}
    for prod, g in ps.groupby("product"):
        hits = sum(1 for y, v in zip(g["year"], g["v"]) if _key(y, v) in where)
        carried[prod] = hits / len(g) >= CARRIED_SHARE

    matcher = matchlib.Matcher(POLDB, applied_aliases_csv=ALIASES,
                               common_names_csv=COMMON_NAMES if os.path.exists(COMMON_NAMES)
                               else None, verbose=False)
    print("\nCERTAIN repairs -> layer-B label (by fingerprint of the correct label's own rows) "
          "-> polity")
    tot = Counter()
    per_polity = Counter()
    for r in (r for r in table if r["status"] == "certain"):
        own = ps[ps["country"] == r["correct_label"]]
        fp = Counter()
        for y, v in zip(own["year"], own["v"]):
            fp.update(where.get(_key(y, v), {}))
        lb_label = fp.most_common(1)[0][0] if fp else None
        rows = err[(err["country"] == r["raw_label"]) & err["prod_side"]]
        n_carried = int(rows["product"].map(carried).fillna(False).sum())
        dup = sum(1 for y, v in zip(rows["year"], rows["v"])
                  if pd.notna(v) and v > 0 and lb_label in where.get(_key(y, v), {}))
        codes = Counter()
        for y in rows["year"]:
            yr = matchlib.eff_year(pd.to_numeric(y, errors="coerce"), y)
            code = None
            if lb_label and yr is not None and not pd.isna(yr):
                code = matcher.assign(lb_label, iso_of.get(lb_label), "iia", int(yr))[0]
            codes[code or "(unresolved)"] += 1
        tot.update(rows=len(rows), carried=n_carried, dup=dup,
                   resolved=sum(n for c, n in codes.items() if c != "(unresolved)"))
        for c, n in codes.items():
            per_polity[c] += n
        print(f"  {r['raw_label']:<42} {len(rows):>4} rows -> {r['correct_label']:<32} -> "
              f"{lb_label or '(no layer-B label)':<22} carried {n_carried:>3}  dup {dup:>2}  "
              + ", ".join(f"{c} {n}" for c, n in codes.most_common()))
    print(f"\n  certain production-side rows      {tot['rows']:>5}")
    print(f"    resolve to a polity               {tot['resolved']:>5}")
    print(f"    of a product layer B carries      {tot['carried']:>5}")
    print(f"    value already in layer B there    {tot['dup']:>5}")
    print("  by polity: " + ", ".join(f"{c} {n}" for c, n in per_polity.most_common()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
