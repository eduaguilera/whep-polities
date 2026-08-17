#!/usr/bin/env python3
"""The entrepot census issue 14 asked for, and the measured reason it promotes nothing.

WHAT #14 ASKED AND WHAT #291 DELIVERED
--------------------------------------
Issue 14 recorded ONE adjudicated case -- IIA green coffee under `djibouti` is Ethiopian
beans in transit, published as `data/final/source_flow_flags.csv` -- and said the class was
general, naming Singapore, Hong Kong, Beira/Lourenco Marques, Trieste and Rotterdam as
candidates. #291 then built `13_trade_entrepot_direction.py`, which classifies 5,839
reporter-item-years as entrepot flows (3,064 unsourceable, 2,775 re-export) from the FAOSTAT
bilateral and production pins. The census question left over is a join: cross that
classification against the flag file and PROMOTE the cases the evidence supports.

This script performs the cross and writes it down. The answer is ZERO promotions, and the
reason is structural rather than a matter of not having looked hard enough:

  1. THE CLASSIFICATION CANNOT NAME AN ORIGIN. A flag row's discriminating column is
     `origin_iso3` -- Djibouti's coffee is flagged because it is ETHIOPIAN. The entrepot
     table is keyed on (reporter, item, year) and summed over ALL partners: it carries no
     partner column at all, by construction, because "exports exceed availability" is a
     statement about a reporter's whole year. So it supplies the RATIO half of the
     discriminator and never the origin half. `12_`/`13_`'s bilateral direction table does
     carry partners, but only for flows already through the 1000x mirror screen.

  2. IT DOES NOT REACH THE ERA WHERE THE DOUBLE COUNT LIVES. The bilateral pin is 1986-2021
     and layer B is 1850-1960: zero overlapping years, as 13_ prints every run. #14's harm
     is a TRANSIT TONNAGE BOOKED IN A PRODUCTION SERIES, which is a property of the
     historical compilations layer B carries; FAOSTAT keeps production and trade in separate
     tables, so a `reexport` row there is correctly filed as trade and double-counts nothing.

  3. ON THE ONE TERRITORY ALREADY ADJUDICATED, IT MISSES THE ITEM. Djibouti IS in the
     entrepot table -- 6 rows, 2014-2021, molasses / dry beans / pears / green chillies /
     raw sugar -- and not one of them is coffee, while `coffee, green` is entrepot-classified
     for 24 OTHER reporters. The classification would not have found the case the flag file
     exists for. That is the same result the intensity screen gives from the other side
     (05_magnitude_screen ranks Djibouti's coffee 16th of 52 coffee outliers, behind Cape
     Verde and El Salvador, which really do grow coffee on very little land).

WHAT THE CENSUS TABLE IS FOR, GIVEN THAT
----------------------------------------
It is the candidate list, with both halves of the discriminator shown side by side, so the
next reader spends their time on origin research and not on re-deriving the join. One row
per layer-B production series whose SOURCE LABEL and ITEM are also entrepot-classified in
the modern pin, carrying:

  * the layer-B side: source, label, polity, median tonnage, span, measured km2, the
    intensity ratio against the item's cross-polity median, and `arealess` -- whether the
    source publishes a tonnage for this label and item WITHOUT any companion area. Djibouti's
    coffee is arealess, which is what a port statistic looks like; a real crop usually
    carries hectares. Measured here: it moves Djibouti from 16th to 20th of 70 on the same
    kind of list, so it is a NECESSARY condition and still not a positive ranker.
  * the modern side: the flow classes and the year range the classification assigns.
  * `already_flagged`, from data/final/source_flow_flags.csv.
  * `verdict`, one of `already_flagged`, `promote`, `no_origin_evidence`. `promote` requires
     a published flag row and the gate enforces that: a verdict is not allowed to be the
     only place a decision lives.

NOTHING HERE IS A REPAIR. No corrected tonnage, no reallocation to the origin polity. #14
asks for entrepot rows to be MARKED so aggregates can exclude them, and marking a row is
the whole intervention.

Usage:
  python3 pipelines/polity-autoimprove/14_entrepot_census.py
Reads layer B (WHEP_LAYERB), state/trade_entrepot_flags.csv, data/final/label_alias_map.csv,
data/final/source_flow_flags.csv and data/final/polities_database.gpkg. Writes
state/entrepot_census.csv. scripts/validate_trade_direction_tiebreak.py re-derives every
claim the table makes that does not need the layer-B parquet.
"""
import csv
import os
import re
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd

import extdata

warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
H = os.path.join(REPO, "pipelines/polity-autoimprove/state")
ENTREPOT = os.path.join(H, "trade_entrepot_flags.csv")
CENSUS = os.path.join(H, "entrepot_census.csv")
ALIASES = os.path.join(REPO, "data/final/label_alias_map.csv")
FLAGS = os.path.join(REPO, "data/final/source_flow_flags.csv")
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")

# The intensity yardstick's own guard, kept identical to 05_magnitude_screen.py: an item
# reported by too few polities has no reliable cross-polity median to compare against.
MIN_ITEM_LABELS = 6

CENSUS_COLUMNS = ["source", "label", "item", "polity_code", "n_rows", "year_min", "year_max",
                  "median_t", "area_km2", "intensity_ratio", "arealess", "modern_classes",
                  "modern_year_min", "modern_year_max", "modern_rows", "already_flagged",
                  "verdict", "reason"]

NO_ORIGIN = ("the entrepot classification is reporter-level and names no partner, so it "
             "cannot supply origin_iso3; and its years share none with layer B")


def norm(s) -> str:
    """Label/item normalisation, identical to 05_magnitude_screen.norm_item."""
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def measured_areas() -> dict:
    g = gpd.read_file(GPKG)
    g = g[g.geometry.notna() & ~g.geometry.is_empty].copy()
    g["km2"] = g.to_crs("ESRI:54034").geometry.area / 1e6
    return dict(zip(g.polity_code, g.km2))


def alias_index() -> dict:
    """(source, normalised label) -> [(year_start, year_end, polity_code), ...]."""
    idx = {}
    with open(ALIASES, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        idx.setdefault((r["source"], norm(r["source_label"])), []).append(
            (r["year_start"], r["year_end"], r["polity_code"]))
    print(f"alias map: {len(rows):,} rows, {len(idx):,} (source, label) keys")
    return idx


def resolve(idx, source, label, year):
    """The polity a source label resolves to in a given year, or None.

    Falls back to the label's sole polity when the year is absent (layer B has undated rows)
    or outside every alias span, and refuses to guess when the label is ambiguous -- which is
    why the census carries `polity_code` blank rather than a plausible wrong code.
    """
    spans = idx.get((source, label))
    if not spans:
        return None
    if year is not None:
        for ys, ye, code in spans:
            lo = int(ys) if str(ys).strip() not in ("", "nan") else None
            hi = int(ye) if str(ye).strip() not in ("", "nan") else None
            if (lo is None or year >= lo) and (hi is None or year <= hi):
                return code
    codes = {c for _, _, c in spans}
    return codes.pop() if len(codes) == 1 else None


def entrepot_side():
    """The classification, keyed the way the census joins it: normalised label and item."""
    with open(ENTREPOT, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if "partner" in (rows[0].keys() if rows else ()):
        raise SystemExit(
            "trade_entrepot_flags.csv now carries a partner column. That changes this "
            "script's central claim -- reread the docstring: a partner-level table CAN name "
            "an origin, so the census becomes answerable and the promotions must be redone.")
    by = {}
    for r in rows:
        by.setdefault((norm(r["reporter"]), norm(r["item"])), []).append(r)
    print(f"entrepot classification: {len(rows):,} rows, {len(by):,} (reporter, item) pairs, "
          f"{len({norm(r['reporter']) for r in rows})} reporters")
    return by


def flag_side():
    """The published flags, keyed on (source, normalised label, normalised item)."""
    out = {}
    with open(FLAGS, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if (r.get("flow_type") or "production") == "production":
                continue
            out[(r["source"], norm(r["label_pattern"]), norm(r["item_pattern"]))] = r
    print(f"published non-production flows: {len(out)}")
    return out


def main() -> int:
    areas = measured_areas()
    idx = alias_index()
    modern = entrepot_side()
    flags = flag_side()

    b = extdata.load_layer_b()
    b["nl"], b["ni"] = b["country"].map(norm), b["item"].map(norm)
    unit = b["unit"].fillna("").astype(str).str.strip().str.lower()
    tonnes = unit.map(extdata.PROD_UNITS)
    hectares = unit.map(extdata.AREA_UNITS)
    prod = b[tonnes.notna()].copy()
    prod["t"] = pd.to_numeric(prod["value"], errors="coerce") * tonnes[tonnes.notna()]
    prod = prod[prod["t"] > 0]
    has_area = set(zip(b.loc[hectares.notna(), "source"], b.loc[hectares.notna(), "nl"],
                       b.loc[hectares.notna(), "ni"]))
    print(f"layer B: {len(b):,} rows, {len(prod):,} positive tonnage rows, "
          f"{len(has_area):,} (source, label, item) keys with a companion area")

    # --- every layer-B production series, with its intensity ratio ---------------------
    series = []
    for (source, label, item), s in prod.groupby(["source", "nl", "ni"]):
        years = sorted(int(y) for y in s["year"].dropna().unique())
        mid = years[len(years) // 2] if years else None
        code = resolve(idx, source, label, mid)
        km2 = areas.get(code)
        med = float(s["t"].median())
        series.append(dict(source=source, label=label, item=item, polity_code=code or "",
                           n_rows=len(s), year_min=years[0] if years else "",
                           year_max=years[-1] if years else "", median_t=med,
                           area_km2=km2, intensity=(med / km2) if km2 else None,
                           arealess=(source, label, item) not in has_area))
    S = pd.DataFrame(series)
    yard = S.dropna(subset=["intensity"]).groupby("item").agg(
        med_int=("intensity", "median"), labels=("label", "nunique"))
    S = S.join(yard, on="item")
    S["intensity_ratio"] = np.where(S["labels"] >= MIN_ITEM_LABELS,
                                    S["intensity"] / S["med_int"], np.nan)
    print(f"layer-B production series: {len(S):,}; with a measured polygon: "
          f"{int(S.area_km2.notna().sum()):,}; with an intensity ratio: "
          f"{int(S.intensity_ratio.notna().sum()):,}")

    # --- the cross --------------------------------------------------------------------
    rows = []
    for r in S.itertuples():
        hits = modern.get((r.label, r.item))
        if not hits:
            continue
        classes = sorted({h["flow_class"] for h in hits})
        years = [int(h["year"]) for h in hits]
        key = (r.source, r.label, r.item)
        flag = flags.get(key)
        verdict = ("already_flagged" if flag else "no_origin_evidence")
        reason = (f"published flag: {flag['flow_type']} from {flag['origin_iso3'] or '?'}"
                  if flag else NO_ORIGIN)
        rows.append(dict(
            source=r.source, label=r.label, item=r.item, polity_code=r.polity_code,
            n_rows=r.n_rows, year_min=r.year_min, year_max=r.year_max,
            median_t=round(r.median_t, 1),
            area_km2=("" if r.area_km2 is None or pd.isna(r.area_km2)
                      else round(r.area_km2, 1)),
            intensity_ratio=("" if pd.isna(r.intensity_ratio)
                             else round(r.intensity_ratio, 2)),
            arealess=str(bool(r.arealess)).lower(), modern_classes="|".join(classes),
            modern_year_min=min(years), modern_year_max=max(years), modern_rows=len(hits),
            already_flagged=str(bool(flag)).lower(), verdict=verdict, reason=reason))
    C = pd.DataFrame(rows, columns=CENSUS_COLUMNS)
    C = C.sort_values(["intensity_ratio", "median_t"], ascending=False, key=lambda s:
                      pd.to_numeric(s, errors="coerce") if s.name in
                      ("intensity_ratio", "median_t") else s)
    C.to_csv(CENSUS, index=False)

    n_flagged = int((C.verdict == "already_flagged").sum())
    n_promote = int((C.verdict == "promote").sum())
    print(f"\ncensus: {len(C)} layer-B production series share a label AND an item with the "
          f"entrepot classification\n"
          f"  arealess (no companion area in the same source): "
          f"{int((C.arealess == 'true').sum())}\n"
          f"  intensity ratio >= 8x: "
          f"{int((pd.to_numeric(C.intensity_ratio, errors='coerce') >= 8).sum())}\n"
          f"  already carrying a published flag: {n_flagged}\n"
          f"  promoted to a flag by this run: {n_promote}")
    if n_flagged == 0:
        print("  -- and the one settled case is NOT among them: the classification puts "
              "Djibouti in 5 other items and never in coffee, so it is not a census of "
              "entrepots either")
    print(f"\nwrote {CENSUS} ({len(C)} rows)")
    print(C.head(15).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
