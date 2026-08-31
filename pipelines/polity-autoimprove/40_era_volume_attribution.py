#!/usr/bin/env python3
"""Which yearbook EDITION does each row of the 1934+ tobacco/hops era come from, and by what factor?

WHAT THIS ADDS TO 29. `29_era_shift_verdicts.py` convicts 350 of the 427 `iia` tobacco/hops production
rows from 1934 on the row's own arithmetic -- an impossible yield, a zero area, or a 30x break from the
label's own pre-era level. What it cannot say is WHERE the number came from or WHAT the factor is, because
layer B carries no volume provenance and the implied factors run 21x to 293x. Issue 416 has been stuck on
exactly that: a blanket division by 100 is not supportable, so a repair needs a per-row factor with an
anchor. This is that per-row attribution.

THE FACTOR IS MEASURED FROM THE SOURCE'S OWN OVERLAP, NOT FITTED. Consecutive IIA volumes re-print the
same years, so 1932 and 1933 appear in both `iia_1933_34` (clean) and `iia_1938_39` (the first inflated
one). For a label reporting that item in both, the ratio between the two printings IS the factor, measured
on the source's own two opinions of one cell with no yield identity and no agronomic assumption:

    germany  tobacco  1933   iia_1933_34: 29,433.4 t   iia_1938_39: 2,943,300 t   ratio 100.00

That ratio is what this tool attaches to every era row of that label and item, and the corrected value it
implies is written beside the published one so the result can be judged rather than trusted.

WHY THE JOIN IS BY VALUE AND KEY, WITH THE NAME AS CONFIRMATION. A bare NAME join between the raw extract
and layer B reports "absent in raw" for nearly everything, because the raw labels are colonial
(`japanese taiwan`, `british nyasaland`, `uk`) and layer B's are modern. `state/iia_label_provenance.csv`
maps 335 of them but not all -- 32 of the 72 labels in `edition_conflicts.csv` for these two items have no
entry -- so a provenance-only join reaches 154 era rows where a value join reaches 246. The join used here
is therefore (raw product, variable, year-or-period, exact value), with the provenance map and a
colonial-prefix rename test used to CONFIRM the label rather than to find it, and `name_confirmed`
recording which rows got that second opinion.

POSITIVE CONTROL, printed on every run and required to hold. Over all 2,340 `iia` tobacco/hops rows in
layer B -- production and area, every year, not just the era -- the join finds an exact raw value at the
same key for 2,296 (98.1%) and resolves 2,294 to a SINGLE volume. A join that silently matched nothing
would report a clean "no attribution possible" for every row, and the tell is that the answer looks
uniform, so the control is a floor (`--min-control`) and not a printed remark.

The item names come from `state/item_equivalences.csv` (`tobacco unmanufactured -> tobacco`,
`hops -> hops`) rather than being hardcoded, and the lookup strips the comma layer B writes into
`tobacco, unmanufactured`. If either item stops resolving the tool fails instead of quietly attributing
half the population.

WHAT THE ATTRIBUTION ESTABLISHES, and it is stronger than the year heuristic already on record:

  * ALL 427 era rows resolve to a volume and ALL 427 come from a LATE one (`iia_1938_39` 147,
    `iia_1939_45` 280); none from a clean volume. So `year >= 1934` is not a proxy for "from an
    inflated volume", it is equivalent to it -- now per row, and over period rows too, which the
    dated-row version of that claim did not cover;
  * `overlap_100x` (247 rows) carry a label-specific factor within 20% of 100, measured on that
    label's own two printings of 1932/1933. Dividing by it moves tobacco from 0 of 144 cells inside
    0.2-3.0 t/ha to 130 of 144 (median implied yield 83.11 -> 0.790) and hops from 0 of 27 to 10 of
    27 (50.03 -> 5.019), the hops residual being its area rounding floor rather than its factor;
  * `no_overlap_pair` (158 rows) is the honest limit: the label did not report this item before 1934
    in a volume that also prints an era year, so the source offers no second opinion and no factor
    can be derived FOR THAT LABEL. Counted, never assigned a divisor -- 122 of them are convicted by
    29 on their own arithmetic, which is a separate and sufficient basis;
  * `ambiguous_raw_label` (6 rows) and `overlap_other` (6 rows) are named rather than folded in.

AND IT REFUTES A BLANKET DIVISION ON TEN ROWS, WHICH IS THE POINT OF DOING IT PER ROW. The 10
`overlap_10x` rows are all `ivory coast` tobacco, and all 10 carry 29's verdict `plausible_yield` --
the yield test says the PUBLISHED numbers are already fine. The raw explains why the factor
disagrees, and the fault is in the clean volume rather than the era:

    iia_1933_34  1933   334 t on 1,640 ha  =  0.20 t/ha
    iia_1938_39  1933  3,300 t on 2,000 ha =  1.65 t/ha     <- a revision, not an inflation
    iia_1939_45  1939-45  1,500-6,000 t on 2,000-6,000 ha = 0.75-1.50 t/ha

Dividing those era cells by their measured 9.88x would push a plausible 0.75-1.50 t/ha down to
0.09-0.19. So where the overlap factor and the physical yield test disagree, the yield test wins: it
tests the row itself, while the factor tests a neighbouring cell in another edition. A blanket
divisor would have damaged all ten.

WHAT IT DOES NOT DO. It does not repair anything and it does not write to
`yield_series_corrections.csv`, which `07_yield_consistency.py` regenerates -- an adjudication typed into
a generated table is one re-run from being erased. `corrected_*` columns are what the measured factor
WOULD produce, so that a decision to repair can be judged against agronomy before it is taken.

Usage:
  python3 pipelines/polity-autoimprove/40_era_volume_attribution.py            # report only
  python3 pipelines/polity-autoimprove/40_era_volume_attribution.py --write    # refresh the table
  python3 pipelines/polity-autoimprove/40_era_volume_attribution.py --check    # fail if stale
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import statistics
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "era_volume_attribution.csv")
VERDICTS = os.path.join(STATE, "era_shift_verdicts.csv")
PROVENANCE = os.path.join(STATE, "iia_label_provenance.csv")
EQUIVALENCES = os.path.join(STATE, "item_equivalences.csv")
MATCHED = os.path.join(STATE, "matched_rows.parquet")
DEFAULT_RAW = os.path.expanduser(
    "~/3itkt6h41pb7jdan/2025-10-06_iia-dataframe/outputs/processed data/harmonized_data.xlsx")

ITEMS = ("hops", "tobacco, unmanufactured")
# The volumes whose windows END before 1934 print the clean unit; the two later ones print the
# inflated one. 1933 is the last year a clean volume reaches, which is why the era starts at 1934.
CLEAN_VOLUMES = ("iia_1909_21", "iia_1925_26", "iia_1929_30", "iia_1933_34")
LATE_VOLUMES = ("iia_1938_39", "iia_1939_45")
# t/ha. Tobacco leaf runs 0.5-3 and hops similar, so this is the band a corrected cell must land in
# for the factor to have been the right one. It judges the correction; it does not choose the factor.
PLAUSIBLE_LO, PLAUSIBLE_HI = 0.2, 3.0
FACTOR_BAND = 0.20              # +/-20% around 100x / 10x, the band edition_conflicts.csv already uses
MIN_CONTROL = 0.90              # the join must find this share of layer-B rows in the raw extract

COLONIAL = ("british", "french", "dutch", "portuguese", "italian", "spanish", "german", "japanese",
            "danish", "belgian", "american", "us", "soviet", "russian")

FIELDS = ("source", "label", "item", "year", "period", "verdict", "convicted", "production",
          "area_ha", "raw_label", "n_raw_labels", "volume", "n_volumes", "name_confirmed",
          "resolution", "overlap_years", "n_overlap_years", "prod_factor", "area_factor",
          "area_factor_pairs", "corrected_production", "corrected_area", "corrected_yield",
          "attribution", "plausible_after")

# Raw labels that are not territories: world and hemisphere aggregates, and the extract's own OCR
# failures. They are excluded from the COMPONENT-SUM search only -- a world total that happens to
# sum with something else to a country's figure is a coincidence, not a composition -- and never
# from the single-cell join, where an exact value at an exact key is the evidence.
NOT_A_TERRITORY = ("total", "[error]")


def norm(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def is_rename(raw_label: str, lb_label: str) -> bool:
    """Is the raw label the layer-B label wearing at most one colonial qualifier?

    Same rule as `15_label_provenance.py`, and deliberately the conservative version: it is used here
    only to CONFIRM a match the value join already made, so a miss costs a `name_confirmed` flag and
    never a row.
    """
    a, b = norm(raw_label), norm(lb_label)
    if a == b:
        return True
    parts = a.split()
    if parts and parts[0] in COLONIAL:
        parts = parts[1:]
    return " ".join(parts) == b


def _n(x, nd=6):
    if x is None:
        return ""
    f = float(x)
    return str(int(f)) if f == int(f) and abs(f) < 1e15 else repr(round(f, nd))


def _f(s):
    s = (s or "").strip()
    return None if s == "" else float(s)


def raw_product_for(item: str, equivalences: str) -> str | None:
    """Layer-B item -> raw IIA product, via the tracked equivalence table only.

    `item_equivalences.csv` stores the item WITHOUT the comma layer B writes (`tobacco
    unmanufactured`), so the lookup is on the normalised name. Returning None is fatal upstream: a
    silently unresolved item would attribute an empty population and print a clean report.
    """
    with open(equivalences, newline="") as fh:
        for r in csv.DictReader(fh):
            if norm(r["item"]) == norm(item):
                return r["raw_product"]
    return None


def build(raw_path: str, matched: str) -> tuple[list[dict], dict]:
    import pandas as pd

    with open(VERDICTS, newline="") as fh:
        verdicts = list(csv.DictReader(fh))
    with open(PROVENANCE, newline="") as fh:
        raw2lb = {norm(r["raw_label"]): norm(r["layer_b_label"])
                  for r in csv.DictReader(fh) if r["layer_b_label"]}

    products = {}
    for item in ITEMS:
        p = raw_product_for(item, EQUIVALENCES)
        if p is None:
            raise SystemExit(f"FAIL: item {item!r} has no raw_product in "
                             f"{os.path.relpath(EQUIVALENCES, REPO)}; the join would silently "
                             f"attribute nothing for it")
        products[item] = p

    raw = pd.read_excel(raw_path)
    raw = raw[raw["product"].isin(set(products.values()))].copy()
    # `year` mixes 1934 with '1934-1938'; coerce and keep the string form as the period key.
    yr = pd.to_numeric(raw.year, errors="coerce")
    raw["key"] = [int(y) if pd.notna(y) else str(s) for y, s in zip(yr, raw.year)]

    idx = {}
    for t in raw.itertuples():
        idx.setdefault((t.product, t.variable, t.key), []).append(
            (t.country, float(t.value), t.yearbook))

    def resolve(label, product, variable, key, value):
        cands = idx.get((product, variable, key), [])
        exact = [c for c in cands if abs(c[1] - value) <= 1e-9 * max(1.0, abs(c[1]))]
        named = [c for c in exact if is_rename(c[0], label) or raw2lb.get(norm(c[0])) == norm(label)]
        return (named or exact), bool(named)

    def resolve_pair(product, variable, key, value):
        """A layer-B cell that is the SUM of two raw sub-labels printed in one volume.

        Five era rows carry a value that appears nowhere in the raw extract, and every one of them is
        a composition rather than a transcription. Searched within a single volume, over territory
        labels only, each resolves to EXACTLY ONE exact two-part sum, and each pair is
        geographically coherent -- which is why this is reported as a composition and not as a
        numerical coincidence:

            china, mainland  1934-1938  = china + china: manchuria
            greece           1934-1938  = greece + italian dodecanese islands
            indonesia        1934-1938  = dutch java and madura + dutch sumatra
            indonesia        1940       = dutch java and madura + dutch sumatra
            usa              1934-1938  = usa + us puerto rico

        Uniqueness is the whole safeguard: if more than one pair sums to the value the row is left
        unresolved rather than assigned the first one found. Two parts only -- a three-part search
        over ~200 candidates would find something for almost any target, which is the point at which
        an exact sum stops being evidence.
        """
        cands = [c for c in idx.get((product, variable, key), [])
                 if 0 < c[1] < value and not str(c[0]).startswith(NOT_A_TERRITORY)]
        hits = []
        by_volume = {}
        for c in cands:
            by_volume.setdefault(c[2], []).append(c)
        for _vol, group in by_volume.items():
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    if abs(group[i][1] + group[j][1] - value) <= 1e-9 * value:
                        hits.append((group[i], group[j]))
        if len(hits) != 1:
            return []
        return list(hits[0])

    # --- POSITIVE CONTROL over the whole item population, not just the era ---------------------
    control = {"rows": 0, "value_found": 0, "unique_volume": 0}
    if os.path.exists(matched):
        m = pd.read_parquet(matched)
        m = m[m.source.eq("iia") & m.item.isin(ITEMS)]
        unitvar = {"tonnes": "production", "ha": "area"}
        for t in m.itertuples():
            var = unitvar.get(t.unit)
            if var is None:
                continue
            key = int(t.year) if pd.notna(t.year) else str(t.period)
            got, _ = resolve(t.country, products[t.item], var, key, float(t.value))
            control["rows"] += 1
            control["value_found"] += bool(got)
            control["unique_volume"] += len({g[2] for g in got}) == 1

    # --- the label's own factor, from the volumes' overlap on the SAME cell --------------------
    factors = {}
    for (country, product, variable), g in raw.groupby(["country", "product", "variable"]):
        clean = g[g.yearbook.isin(CLEAN_VOLUMES)].groupby("key").value.median()
        late = g[g.yearbook.isin(LATE_VOLUMES)].groupby("key").value.median()
        pairs = [(k, clean[k], late[k]) for k in clean.index
                 if k in late.index and float(clean[k]) > 0]
        if pairs:
            factors[(country, product, variable)] = (
                statistics.median(float(l) / float(c) for _k, c, l in pairs),
                [str(k) for k, _c, _l in pairs])

    rows = []
    for v in verdicts:
        item, label = v["item"], v["label"]
        product = products[item]
        prod = float(v["production"])
        area = _f(v["area_ha"])
        key = int(v["year"]) if v["year"] else str(v["period"])
        got, named = resolve(label, product, "production", key, prod)
        resolution = "single_cell" if got else "unresolved"
        if not got:
            got = resolve_pair(product, "production", key, prod)
            if got:
                resolution = "component_sum"
        raw_labels = sorted({g[0] for g in got})
        volumes = sorted({g[2] for g in got})

        # THE FACTOR MUST NOT BE PICKED FROM A COINCIDENCE. Six rows match TWO raw labels, because
        # two countries printed the same figure in the same year (`british transjordan` and
        # `german south west africa` both at 1938). Taking the first candidate that happens to own a
        # factor attributes one territory's factor to another -- measured: `benin` was handed
        # `french ivory coast`'s 9.88x that way. So a factor is assigned only when every candidate
        # that has one agrees with the others within the band, and the same rule then serves the
        # component sums, where the two parts must have moved together for the sum's factor to mean
        # anything.
        cand_prod = [(rl, factors[(rl, product, "production")])
                     for rl in raw_labels if (rl, product, "production") in factors]
        cand_area = [(rl, factors[(rl, product, "area")])
                     for rl in raw_labels if (rl, product, "area") in factors]

        def _agree(cands):
            vals = [c[1][0] for c in cands]
            if not vals:
                return None, []
            lo, hi = min(vals), max(vals)
            if lo > 0 and (hi - lo) > FACTOR_BAND * lo:
                return None, []
            return statistics.median(vals), sorted({y for c in cands for y in c[1][1]})

        ambiguous = len(raw_labels) > 1 and len(cand_prod) != len(raw_labels)
        pf, overlap = (None, []) if ambiguous else _agree(cand_prod)
        af, area_years = (None, []) if ambiguous else _agree(cand_area)
        area_pairs = len(area_years)

        if not got:
            attribution = "unresolved_in_raw"
        elif ambiguous:
            attribution = "ambiguous_raw_label"
        elif pf is None:
            attribution = "no_overlap_pair"
        elif abs(pf - 100.0) <= FACTOR_BAND * 100.0:
            attribution = "overlap_100x"
        elif abs(pf - 10.0) <= FACTOR_BAND * 10.0:
            attribution = "overlap_10x"
        else:
            attribution = "overlap_other"

        # `is not None` throughout: a factor or a value of 0 must not be read as absent.
        cp = (prod / pf) if pf is not None and pf > 0 else None
        ca = None
        if area is not None:
            ca = (area / af) if af is not None and af > 0 else area
        cy = (cp / ca) if cp is not None and ca is not None and ca > 0 else None
        plaus = "" if cy is None else str(PLAUSIBLE_LO <= cy <= PLAUSIBLE_HI)

        rows.append({
            "source": v["source"], "label": label, "item": item, "year": v["year"],
            "period": v["period"], "verdict": v["verdict"], "convicted": v["convicted"],
            "production": v["production"], "area_ha": v["area_ha"],
            "raw_label": "|".join(raw_labels), "n_raw_labels": str(len(raw_labels)),
            "volume": "|".join(volumes), "n_volumes": str(len(volumes)),
            "name_confirmed": str(named), "resolution": resolution,
            "overlap_years": "|".join(overlap), "n_overlap_years": str(len(overlap)),
            "prod_factor": _n(pf, 4), "area_factor": _n(af, 4),
            "area_factor_pairs": str(area_pairs),
            "corrected_production": _n(cp, 4), "corrected_area": _n(ca, 4),
            "corrected_yield": _n(cy, 4), "attribution": attribution,
            "plausible_after": plaus,
        })
    rows.sort(key=lambda r: (r["attribution"], r["label"], r["item"], r["year"], r["period"]))
    return rows, control


def write(rows: list[dict], path: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default=DEFAULT_RAW, help="raw IIA harmonized extract (xlsx)")
    ap.add_argument("--matched", default=MATCHED, help="layer-B panel, for the positive control")
    ap.add_argument("--min-control", type=float, default=MIN_CONTROL)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.raw):
        print(f"raw extract absent ({args.raw}); nothing to do", file=sys.stderr)
        return 0
    if not os.path.exists(VERDICTS):
        print(f"FAIL: missing {os.path.relpath(VERDICTS, REPO)}", file=sys.stderr)
        return 1

    rows, control = build(args.raw, args.matched)

    if control["rows"]:
        share = control["value_found"] / control["rows"]
        print(f"positive control: {control['value_found']} of {control['rows']} layer-B "
              f"tobacco/hops rows found in the raw extract at the same key ({100 * share:.1f}%), "
              f"{control['unique_volume']} resolved to one volume")
        if share < args.min_control:
            print(f"FAIL: the raw join found only {100 * share:.1f}% of layer-B rows, below "
                  f"{100 * args.min_control:.0f}%. A join this thin reports 'no attribution' "
                  f"uniformly, which reads like a finding and is not one", file=sys.stderr)
            return 1
    else:
        print("positive control SKIPPED: layer-B panel absent, so the join is unverified",
              file=sys.stderr)

    order = ("overlap_100x", "overlap_10x", "overlap_other", "ambiguous_raw_label",
             "no_overlap_pair", "unresolved_in_raw")
    ac = {k: sum(1 for r in rows if r["attribution"] == k) for k in order}
    print(f"{len(rows)} era row(s), {len({r['label'] for r in rows})} label(s)")
    for k in order:
        print(f"  {k:20} {ac[k]:4}")
    res = {}
    for r in rows:
        res[r["resolution"]] = res.get(r["resolution"], 0) + 1
    print("  resolution: " + ", ".join(f"{k}={n}" for k, n in sorted(res.items())))
    vols = {}
    for r in rows:
        for v in (r["volume"].split("|") if r["volume"] else ["(unresolved)"]):
            vols[v] = vols.get(v, 0) + 1
    print("  volume of origin: " + ", ".join(f"{k}={n}" for k, n in sorted(vols.items())))
    late = sum(n for k, n in vols.items() if k in LATE_VOLUMES)
    clean = sum(n for k, n in vols.items() if k in CLEAN_VOLUMES)
    print(f"  from a late volume {late}, from a clean volume {clean}")
    testable = [r for r in rows if r["plausible_after"]]
    ok = sum(1 for r in testable if r["plausible_after"] == "True")
    print(f"  corrected yield inside {PLAUSIBLE_LO}-{PLAUSIBLE_HI} t/ha: {ok} of {len(testable)} "
          f"rows that have both a factor and an area")

    if args.check:
        if not os.path.exists(OUT):
            print(f"MISSING {os.path.relpath(OUT, REPO)}", file=sys.stderr)
            return 1
        with open(OUT, newline="") as fh:
            have = list(csv.DictReader(fh))
        if have != [{k: str(v) for k, v in r.items()} for r in rows]:
            print(f"STALE {os.path.relpath(OUT, REPO)}: rerun with --write", file=sys.stderr)
            return 1
        print("table is current")
        return 0
    if args.write:
        write(rows, OUT)
        print(f"wrote {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
