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

ALREADY-ADJUDICATED FLOWS (issue 14). `data/final/source_flow_flags.csv` records the
(source, label, item) combinations a human already ruled NON-production — Ethiopian
coffee under `djibouti` is the standing case. This screen reads that file and joins it
onto the outliers on (source, polity, item), for two reasons that pull in opposite
directions:
  * an outlier already carrying a flag needs no further investigation, and reporting it
    again spends an agent's time re-deriving a settled verdict;
  * a flagged combination the screen does NOT rank as an outlier is proof the screen is
    not a census of entrepots. Both directions are printed, and `known_flow` /
    `flow_origin_iso3` land in state/magnitude_outliers.csv so the next reader sees the
    verdict beside the ratio. Until this join existed nothing in the repository consumed
    the published flag file at all.

Usage:
  python3 pipelines/polity-autoimprove/05_magnitude_screen.py [--top 40] [--min-ratio 8]
Writes state/magnitude_outliers.csv and prints the ranked list.
"""
import csv
import re
import pandas as pd, numpy as np, geopandas as gpd, json, os, argparse, warnings
warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
H = os.path.join(REPO, "pipelines/polity-autoimprove/state")
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")
FLAGS = os.path.join(REPO, "data/final/source_flow_flags.csv")

ap = argparse.ArgumentParser()
ap.add_argument("--top", type=int, default=40)
ap.add_argument("--min-ratio", type=float, default=8.0,
                help="flag a polity-item when its intensity exceeds the item's cross-polity median by this factor")
ap.add_argument("--min-polities", type=int, default=6,
                help="skip items reported by fewer polities than this (no reliable median)")
A = ap.parse_args()


def norm_item(s) -> str:
    """Item normalisation shared with the flag join — the two sides must agree."""
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def load_flow_flags():
    """The published non-production flows, keyed the way this screen keys its rows.

    The flag file is written on (source, source LABEL, item); this screen works in
    (source, POLITY, item), so the join uses the flag's `polity_code` column — which the
    writer resolves from the published alias map, so the two cannot drift. Two flag
    shapes cannot be joined and are returned separately rather than silently dropped:
      * `polity_code` empty (a `label_pattern` of `*`, i.e. every label of a source) —
        not one polity, so not attachable to one polity's outlier row;
      * `item_pattern` of `*` — every item, handled as a per-(source, polity) wildcard.
    """
    exact, wildcard, unjoinable = {}, {}, []
    if not os.path.exists(FLAGS):
        return exact, wildcard, unjoinable
    with open(FLAGS, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            codes = [c for c in (r.get("polity_code") or "").split(";") if c]
            payload = (r.get("flow_type", ""), r.get("origin_iso3", ""))
            if not codes:
                unjoinable.append(r)
                continue
            for code in codes:
                if r.get("item_pattern", "*").strip() == "*":
                    wildcard[(r["source"], code)] = payload
                else:
                    exact[(r["source"], code, norm_item(r["item_pattern"]))] = payload
    return exact, wildcard, unjoinable


FLAG_EXACT, FLAG_WILDCARD, FLAG_UNJOINABLE = load_flow_flags()
print(f"{len(FLAG_EXACT) + len(FLAG_WILDCARD)} published non-production flow flag(s) "
      f"joinable to a polity; {len(FLAG_UNJOINABLE)} not attachable to one polity")


def flag_for(source, code, item):
    """(flow_type, origin_iso3) already recorded for this combination, or ("", "")."""
    return FLAG_EXACT.get((source, code, norm_item(item))) \
        or FLAG_WILDCARD.get((source, code)) or ("", "")


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

# ---------- already-adjudicated flows (issue 14) ----------
flagged = [flag_for(r.source, r.whep_code, r.item) for r in out.itertuples()]
out["known_flow"] = [f[0] for f in flagged]
out["flow_origin_iso3"] = [f[1] for f in flagged]
known = out[out.known_flow != ""]
print(f"already carrying a verdict in data/final/source_flow_flags.csv, and so needing no "
      f"further investigation: {len(known)}")
for r in known.itertuples():
    print(f"  SETTLED {r.ratio:8.1f}x  {r.item[:26]:26s} {r.whep_code:16s} {r.source:9s} "
          f"{r.known_flow} (origin {r.flow_origin_iso3 or 'unrecorded'})")

# The reverse direction, and the more important one: a flagged combination this screen
# does NOT rank as an outlier. Those are the cases intensity cannot find, so their
# number is the measured argument against treating this screen as a census.
seen = {(r.source, r.whep_code, norm_item(r.item)) for r in grp.itertuples()}
ranked = {(r.source, r.whep_code, norm_item(r.item)) for r in out.itertuples()}
missed = sorted(k for k in seen - ranked if flag_for(*k)[0])
for s, c, i in missed:
    print(f"  MISSED BY THIS SCREEN  {i[:26]:26s} {c:16s} {s:9s} — flagged "
          f"{flag_for(s, c, i)[0]} but below {A.min_ratio}x, so intensity would never "
          f"have found it")

cols = ["ratio", "item", "unit", "whep_code", "polity_name", "source", "median_value",
        "area", "n", "item_median_intensity", "assertion_keys", "known_flow",
        "flow_origin_iso3"]
out[cols].to_csv(os.path.join(H, "magnitude_outliers.csv"), index=False)

show = out.head(A.top)
for r in show.itertuples():
    print(f"{r.ratio:8.1f}x  {r.item[:26]:26s} {r.whep_code:16s} ({r.area:>9,.0f} km2) "
          f"{r.source:9s} median={r.median_value:>12,.0f} {r.unit[:12]:12s} n={r.n}"
          + (f"  [SETTLED: {r.known_flow}]" if r.known_flow else ""))
    print(f"           -> {r.assertion_keys[:110]}")
print(f"\nwrote {os.path.join(H,'magnitude_outliers.csv')} ({len(out)} rows)")
