#!/usr/bin/env python3
"""Internal-consistency check and repair table for the FAO 1952 land-use series.

The land-use block is self-checking: for a given (polity, year) the component
categories must sum to `use total`, and `use total` must equal the territory's
own land area. That makes bad cells both DETECTABLE and RECOVERABLE — the
correct value of a single bad component is total minus the sum of the others.

Found this way (all confirmed against the polity's measured polygon):
  Guam 1951        builton 8361 and unused 12118 should be 8.361 / 12.118
                   (the parse dropped decimal points; components then sum to 54
                   = use total = Guam's actual 53,768 ha)
  New Zealand 1951 forests 477897 should be 7897 (digits prepended)
  Mozambique 1948  forests 1019400 should be 19400 (digits prepended)
  Ireland 1951     `use land` 26889 is spurious — the five components already
                   sum exactly to use total (7028)

This script does NOT modify the source parquet (it lives outside the repo, in
the maintainer's own store). It writes a correction table so the fix can be
applied upstream in the consolidation step, where it belongs.

Usage:
  python3 pipelines/polity-autoimprove/06_landuse_consistency.py
Writes state/landuse_corrections.csv
"""
import pandas as pd, geopandas as gpd, os, warnings
warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
H = os.path.join(REPO, "pipelines/polity-autoimprove/state")

# component categories that should sum to `use total`
COMPONENTS = ["use agricultural area arable land orchards",
              "use agricultural area permanent peadows pastures",
              "use builton wasteland",
              "use forests woodlands",
              "use unused productive land"]
TOTAL = "use total"

m = pd.read_parquet(os.path.join(H, "matched_rows.parquet"))
lu = m[m["item"].astype(str).str.startswith("use ")].copy()
lu["v"] = pd.to_numeric(lu["value"], errors="coerce")

g = gpd.read_file(os.path.join(REPO, "data/final/polities_database.gpkg"))
g = g[g.geometry.notna() & ~g.geometry.is_empty]
g["terr_1000ha"] = (g.to_crs("ESRI:54034").geometry.area / 1e6) * 100 / 1000  # km2 -> 1000 ha
terr = dict(zip(g.polity_code, g.terr_1000ha))

rows = []
for (code, year), grp in lu.groupby(["whep_code", "year"]):
    vals = dict(zip(grp["item"].astype(str), grp.v))
    total = vals.get(TOTAL)
    present = [c for c in COMPONENTS if c in vals]
    if total is None or len(present) < 2: continue
    comp_sum = sum(vals[c] for c in present)
    resid = comp_sum - total
    if abs(resid) <= max(1.0, 0.02 * total):     # consistent within 2%
        continue
    # a single component is bad if replacing it with (total - others) makes the
    # set consistent AND the replacement is a plausible digit/decimal variant
    for c in present:
        others = comp_sum - vals[c]
        implied = total - others
        if implied < 0: continue
        bad, good = vals[c], implied
        if good == 0 or bad == 0: continue
        ratio = bad / good
        kind = None
        if abs(ratio - 1000) / 1000 < 0.02: kind = "decimal point dropped (x1000)"
        elif abs(ratio - 100) / 100 < 0.02: kind = "decimal point dropped (x100)"
        elif str(int(round(bad))).endswith(str(int(round(good)))): kind = "digits prepended"
        elif ratio > 2: kind = "value too large (basis unclear)"
        if kind:
            rows.append({"polity_code": code, "year": int(year), "item": c,
                         "recorded": bad, "implied_correct": round(good, 3),
                         "diagnosis": kind, "use_total": total,
                         "territory_1000ha": round(terr.get(code, float("nan")), 1),
                         "components_present": len(present)})
            break
    else:
        # no single-cell explanation: report the inconsistency itself
        rows.append({"polity_code": code, "year": int(year), "item": "(multiple)",
                     "recorded": comp_sum, "implied_correct": total,
                     "diagnosis": f"components sum to {comp_sum:,.0f} but total is {total:,.0f}",
                     "use_total": total, "territory_1000ha": round(terr.get(code, float("nan")), 1),
                     "components_present": len(present)})

out = pd.DataFrame(rows)
if len(out):
    out = out.sort_values("recorded", ascending=False)
    out.to_csv(os.path.join(H, "landuse_corrections.csv"), index=False)
print(f"land-use (polity, year) blocks checked: {lu.groupby(['whep_code','year']).ngroups}")
print(f"inconsistent blocks with a diagnosis: {len(out)}\n")
if len(out):
    for r in out.itertuples():
        print(f"  {r.polity_code:16s} {r.year}  {r.item[:44]:44s} "
              f"{r.recorded:>12,.0f} -> {r.implied_correct:>10,.3f}   [{r.diagnosis}]")
    print(f"\nwrote {os.path.join(H,'landuse_corrections.csv')}")
