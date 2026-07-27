#!/usr/bin/env python3
"""Deterministic implausible-magnitude screen: find assertions whose reported
output is impossible for the territory it is matched to.

Motivation: agent probes keep finding territorial mis-attribution — a
sub-territory's output folded up into its parent, or entrepot/transit volumes
recorded under the port that handled them (Ethiopian coffee under French
Somaliland). Both look identical in the data: an intensity (output per km2)
far outside what the commodity plausibly achieves anywhere.

Method, with no hardcoded agronomy: for each (item, unit) compute every
polity's intensity = median value / area_km2, then compare each polity against
the MEDIAN INTENSITY of the same item across all polities. A polity reporting
30x the typical per-km2 intensity for a crop is either mis-matched, an
entrepot, or a sub-territory folded into a parent — all worth an agent's time.
Ratios are computed in log space and reported as multiples.

Areas come from the polygon geometry (equal-area projection), not the
frontmatter field, so they are measured rather than asserted.

Usage:
  python3 pipelines/polity-autoimprove/05_magnitude_screen.py [--top 40] [--min-ratio 8]
Writes state/magnitude_outliers.csv and prints the ranked list.
"""
import pandas as pd, numpy as np, geopandas as gpd, json, os, argparse, warnings
warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
H = os.path.join(REPO, "pipelines/polity-autoimprove/state")
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")

ap = argparse.ArgumentParser()
ap.add_argument("--top", type=int, default=40)
ap.add_argument("--min-ratio", type=float, default=8.0,
                help="flag a polity-item when its intensity exceeds the item's cross-polity median by this factor")
ap.add_argument("--min-polities", type=int, default=6,
                help="skip items reported by fewer polities than this (no reliable median)")
A = ap.parse_args()

# ---------- measured areas (equal-area projection, not the frontmatter field) ----------
g = gpd.read_file(GPKG)
g = g[g.geometry.notna() & ~g.geometry.is_empty]
g["area_km2"] = g.to_crs("ESRI:54034").geometry.area / 1e6
area = dict(zip(g.polity_code, g.area_km2))
print(f"measured areas for {len(area)} polities with geometry")

m = pd.read_parquet(os.path.join(H, "matched_rows.parquet"))
m = m[m.whep_code.notna()].copy()
m["v"] = pd.to_numeric(m["value"], errors="coerce")
m = m[m.v > 0]
m["area"] = m.whep_code.map(area)
m = m[m.area.notna() & (m.area > 0)]
print(f"{len(m):,} matched rows with a positive value and a measured polygon")

# ---------- CHECK A: hard physical bound (no distributional assumption) ----------
# An area-denominated figure cannot exceed the territory's own land area. This is
# the highest-precision check available: a violation is an impossible number, not
# an unusual one, so it is a DATA error (unit/scale/parse) or a routing error.
HA_UNITS = {"ha": 1.0, "hectare": 1.0, "hectares": 1.0,
            "1000 ha": 1e3, "1000 hectare": 1e3, "1000 hectares": 1e3}
u = m["unit"].fillna("").astype(str).str.strip().str.lower()
mult = u.map(HA_UNITS)
areal = m[mult.notna()].copy()
areal["ha_reported"] = areal.v * mult[mult.notna()]
areal["ha_territory"] = areal.area * 100.0            # 1 km2 = 100 ha
impossible = (areal.groupby([areal["item"].astype(str), "whep_code", "source", "unit"])
              .agg(max_ha=("ha_reported", "max"), median_ha=("ha_reported", "median"),
                   ha_territory=("ha_territory", "first"), n=("ha_reported", "size"))
              .reset_index())
impossible.columns = ["item", "whep_code", "source", "unit", "max_ha", "median_ha", "ha_territory", "n"]
impossible["times_over"] = impossible.median_ha / impossible.ha_territory
impossible = impossible[impossible.times_over > 1.0].sort_values("times_over", ascending=False)
print(f"\nCHECK A — area-denominated values exceeding the territory's own land area: "
      f"{len(impossible)} (item, polity, source) combinations")
for r in impossible.head(15).itertuples():
    print(f"  {r.times_over:9.1f}x territory  {r.item[:26]:26s} {r.whep_code:16s} {r.source:9s} "
          f"median={r.median_ha:>14,.0f} ha vs territory {r.ha_territory:>12,.0f} ha (n={r.n}, unit={r.unit})")
impossible.to_csv(os.path.join(H, "magnitude_impossible_area.csv"), index=False)

# ---------- CHECK B: intensity outliers ----------
# Exclude RATE-like units: a per-animal carcass weight or a price is not a
# quantity, so dividing it by territory area is meaningless (it produced
# false positives for Liechtenstein/Malta "carcass weights ... kilograms").
RATE_UNIT_HINTS = ("kilogram", "kg", "per ", "/", "percent", "%", "index",
                   "price", "value", "currency", "usd", "capita")
is_rate = u.str.contains("|".join(RATE_UNIT_HINTS), regex=True, na=False)
n_rate = int(is_rate.sum())
m = m[~is_rate]
print(f"\nCHECK B — intensity outliers (excluded {n_rate:,} rows with rate-like units)")

# ---------- per (item, unit, polity) intensity ----------
grp = (m.groupby([m["item"].astype(str), m["unit"].fillna("").astype(str), "whep_code", "source"])
        .agg(median_value=("v", "median"), n=("v", "size"), area=("area", "first"))
        .reset_index()
        .rename(columns={"level_0": "item", "level_1": "unit"}))
grp.columns = ["item", "unit", "whep_code", "source", "median_value", "n", "area"]
grp["intensity"] = grp.median_value / grp.area

# cross-polity median intensity per (item, unit) — the yardstick
yard = (grp.groupby(["item", "unit"])
           .agg(item_median_intensity=("intensity", "median"),
                n_polities=("whep_code", "nunique")).reset_index())
grp = grp.merge(yard, on=["item", "unit"])
grp = grp[grp.n_polities >= A.min_polities]
grp["ratio"] = grp.intensity / grp.item_median_intensity

out = grp[grp.ratio >= A.min_ratio].sort_values("ratio", ascending=False)
print(f"\n{len(out)} (item, polity, source) combinations exceed {A.min_ratio}x the item's typical intensity\n")

# ---------- attach the assertion key each outlier belongs to ----------
ap_path = os.path.join(H, "assertions.json")
assertions = json.load(open(ap_path))["assertions"] if os.path.exists(ap_path) else []
by_code_src = {}
for a in assertions:
    by_code_src.setdefault((a["candidate"], a["source"]), []).append(a)
def keys_for(code, src):
    return "; ".join(x["key"] for x in by_code_src.get((code, src), [])[:3]) or "(no assertion)"
out = out.copy()
out["assertion_keys"] = [keys_for(r.whep_code, r.source) for r in out.itertuples()]
out["polity_name"] = out.whep_code.map(dict(zip(g.polity_code, g.polity_name)))

cols = ["ratio", "item", "unit", "whep_code", "polity_name", "source", "median_value",
        "area", "n", "item_median_intensity", "assertion_keys"]
out[cols].to_csv(os.path.join(H, "magnitude_outliers.csv"), index=False)

show = out.head(A.top)
for r in show.itertuples():
    print(f"{r.ratio:8.1f}x  {r.item[:26]:26s} {r.whep_code:16s} ({r.area:>9,.0f} km2) "
          f"{r.source:9s} median={r.median_value:>12,.0f} {r.unit[:12]:12s} n={r.n}")
    print(f"           -> {r.assertion_keys[:110]}")
print(f"\nwrote {os.path.join(H,'magnitude_outliers.csv')} ({len(out)} rows)")
