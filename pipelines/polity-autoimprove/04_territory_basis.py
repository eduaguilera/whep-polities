#!/usr/bin/env python3
"""Stage 4 (deterministic): classify each polity's TERRITORY_BASIS — does its
polygon faithfully represent the territory of the period it serves, or is it an
ASSUMPTION (a later/modern border projected back, a single vintage held constant
across a long span, or no polygon at all)?

This operationalises the concern: "WHEP may carry 1860-1961 country data on
expected-same-territory borders that were not the real territory." For each
polity we compare the polygon's vintage (polygon_feature_year) to the polity's
own period [start_year, end_year] and emit a graded basis:

  measured            polygon vintage falls inside the period AND the span is
                      short enough that one vintage is defensible (faithful).
  assumed_constant    vintage inside the period but the span is long (>= SPAN_LONG):
                      one polygon is held constant across years whose borders
                      may have changed (e.g. a 1886 polygon for an 1850-1910 span).
  back_projected      vintage is OUTSIDE the period — a later (usually modern)
                      or earlier border applied to this period. The clearest
                      "not the real territory" case.
  unassigned          no polygon (polygon_status=unassigned / no geometry):
                      an HONEST gap, never a false territory.

A polity is "territory_assumed" (needs review) when basis != measured.
The report focuses on polities overlapping the WINDOW (default 1860-1961).
Data magnitude per polity is attached from the layer-B matched_rows when present.
"""
import pandas as pd, numpy as np, json, os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
H = os.path.join(REPO, "pipelines/polity-autoimprove/state")
POLDB = os.path.join(REPO, "data/final/polities_database.csv")
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")
CONSTRUCTED = os.path.join(REPO, "data/geodata/constructed/constructed.geojson")

WIN_LO, WIN_HI = 1860, 1961   # the concern window
SPAN_LONG = 25                # a span this long can't be one fixed border
DRIFT_TOL = 15                # vintage this far from period edge = real drift

pol = pd.read_csv(POLDB)

# has_geometry from the master gpkg (authoritative on what actually carries a polygon)
import geopandas as gpd, warnings
warnings.filterwarnings("ignore")
g = gpd.read_file(GPKG)
has_geom = {r.polity_code: (r.geometry is not None and not r.geometry.is_empty)
            for _, r in g.iterrows()}

# polygon_method (faithfulness label) for constructed/composed polygons
method = {}
if os.path.exists(CONSTRUCTED):
    cg = gpd.read_file(CONSTRUCTED)
    if "polygon_method" in cg.columns:
        method = {r.polity_code: str(r.polygon_method) for _, r in cg.iterrows()}

# priority signal: polities the territorial-evidence step (02) independently
# flagged (data magnitude step-change vs sibling period, README-known mismatch,
# polygon-vintage drift, or aggregate-contains-concurrent-data). An assumed_constant
# polity that ALSO trips 02 is a HIGH-PRIORITY review (real evidence its single
# polygon misrepresents the territory), vs a long-span border that was actually stable.
flagged_02 = set()
tf = os.path.join(H, "territorial_flagged.json")
if os.path.exists(tf):
    flagged_02 = {f["polity_code"] for f in json.load(open(tf))}

# layer-B data magnitude per polity (optional hint)
rows_by_code = {}
mp = os.path.join(H, "matched_rows.parquet")
if os.path.exists(mp):
    m = pd.read_parquet(mp)
    rows_by_code = m[m.whep_code.notna()].groupby("whep_code").size().to_dict()

def classify(r):
    code = r.polity_code
    s, e = int(r.start_year), int(r.end_year)
    status = str(r.get("polygon_status") or "").strip().lower()
    src = str(r.get("polygon_source") or "").strip().lower()
    fy = r.get("polygon_feature_year")
    geo = has_geom.get(code, False)
    if status == "unassigned" or not geo or src in ("none", "", "nan"):
        return "unassigned", "no polygon (honest gap; never a false territory)"
    if pd.isna(fy):
        return "assumed_constant", "polygon present but no recorded vintage year"
    fy = int(fy)
    span = e - s
    meth = method.get(code, "")
    if meth in ("modern_proxy", "constructed_estimate"):
        return "back_projected", f"polygon_method={meth} (not a faithful-vintage border)"
    if fy > e:
        return "back_projected", f"polygon vintage {fy} is AFTER the period ends ({e}) — later/modern border applied back"
    if fy < s:
        return "back_projected", f"polygon vintage {fy} is BEFORE the period starts ({s})"
    # vintage inside [s, e]
    drift = max(fy - s, e - fy)
    if span >= SPAN_LONG and drift >= DRIFT_TOL:
        return "assumed_constant", f"single {fy} polygon held across a {span}y span ({s}-{e}); borders may have changed"
    return "measured", f"vintage {fy} faithful to period {s}-{e}"

recs = []
for _, r in pol.iterrows():
    s, e = int(r.start_year), int(r.end_year)
    overlaps = (s <= WIN_HI) and (e >= WIN_LO)
    basis, reason = classify(r)
    recs.append({
        "polity_code": r.polity_code, "polity_name": r.polity_name,
        "start_year": s, "end_year": e,
        "polygon_source": r.get("polygon_source"),
        "polygon_feature_year": (int(r.polygon_feature_year) if pd.notna(r.get("polygon_feature_year")) else None),
        "polygon_status": r.get("polygon_status"),
        "overlaps_1860_1961": overlaps,
        "territory_basis": basis, "territory_assumed": basis != "measured",
        "priority_review": (basis in ("assumed_constant", "back_projected")) and (r.polity_code in flagged_02),
        "basis_reason": reason, "layerb_data_rows": int(rows_by_code.get(r.polity_code, 0)),
    })

out = pd.DataFrame(recs)
out.to_csv(os.path.join(H, "territory_basis.csv"), index=False)

ORDER = ["measured", "assumed_constant", "back_projected", "unassigned"]
print(f"classified {len(out)} polities -> state/territory_basis.csv\n")
print("ALL polities by territory_basis:")
for b in ORDER:
    sub = out[out.territory_basis == b]
    print(f"  {b:18s} {len(sub):>4} polities")

win = out[out.overlaps_1860_1961]
print(f"\n=== WINDOW {WIN_LO}-{WIN_HI}: {len(win)} polities overlap ===")
for b in ORDER:
    sub = win[win.territory_basis == b]
    print(f"  {b:18s} {len(sub):>4} polities  {int(sub.layerb_data_rows.sum()):>8,} layer-B rows")

prio = win[win.priority_review].sort_values("layerb_data_rows", ascending=False)
print(f"\n=== {len(prio)} window polities are PRIORITY_REVIEW "
      f"(assumed/back-projected AND independently flagged by stage 02) ===")
for _, r in prio.head(30).iterrows():
    print(f"  {r.polity_code:18s} {r.territory_basis:16s} {r.basis_reason[:60]:60s} [{r.layerb_data_rows}r]")
