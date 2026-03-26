#!/usr/bin/env python3
"""
Cross-comparison of polygon sources for the same territories.

Compares CShapes 2.0, CShapes-Europe, and GADM polygons where they overlap,
measuring area differences, boundary deviations, and centroid offsets.

This helps identify:
1. How much CShapes and GADM differ for the same country
2. Where CShapes-Europe differs from CShapes 2.0 for European states
3. Temporal polygon changes within CShapes (territory changes over time)
4. Potential accuracy issues in our polygon assignments

Writes:
  - data/analysis/polygon_comparison.csv
  - data/analysis/plots/compare_*.png
"""

import warnings
warnings.filterwarnings("ignore")

import os
import re
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import shape
from shapely.ops import unary_union

BASE = "/home/usuario/whep-polities"
REF = "/home/usuario/WHEP.worktrees/lbm364dl-refactor-polities/data-raw/polities_inputs"
PLOT_DIR = f"{BASE}/data/analysis/plots"
os.makedirs(PLOT_DIR, exist_ok=True)

# ── Load data ────────────────────────────────────────────────────────
print("Loading polygon sources...")
polities = pd.read_csv(f"{BASE}/data/final/polities_database.csv")
our_polys = gpd.read_file(f"{BASE}/data/geodata/polities_polygons.gpkg")
cshapes = gpd.read_file(f"{BASE}/data/geodata/cshapes2_full.gpkg")
cshapes_sov = gpd.read_file(f"{BASE}/data/geodata/cshapes2_sovereign.gpkg")
cshapes_eu = gpd.read_file(f"{REF}/cshapes_europe_geometries.gpkg")
gadm = gpd.read_file("/home/usuario/LandInG/gadm/gadm36_levels.gpkg", layer="level0")

print(f"  Our polygons: {len(our_polys)}")
print(f"  CShapes full: {len(cshapes)}")
print(f"  CShapes sovereign: {len(cshapes_sov)}")
print(f"  CShapes-Europe: {len(cshapes_eu)}")
print(f"  GADM admin-0: {len(gadm)}")


# ── Comparison 1: CShapes vs GADM for modern countries ───────────────
print("\n=== COMPARISON 1: CShapes 2.0 vs GADM (modern countries) ===")

# Get latest CShapes entry per country
cshapes["start_dt"] = pd.to_datetime(cshapes["start"])
cshapes["end_dt"] = pd.to_datetime(cshapes["end"])
latest_cs = cshapes.sort_values("end_dt").groupby("country_name").last().reset_index()

# Build COW→ISO lookup from our polities database
cow_to_iso = {}
for _, p in polities.iterrows():
    if pd.notna(p["cow_code"]) and pd.notna(p["iso3_code"]):
        try:
            cow_to_iso[str(int(float(p["cow_code"])))] = p["iso3_code"]
        except (ValueError, TypeError):
            pass

# Add ISO to CShapes via COW code
latest_cs["iso3"] = latest_cs["cowcode"].apply(
    lambda x: cow_to_iso.get(str(int(x)) if pd.notna(x) and x != 0 else "", ""))

comparison_rows = []

for _, g in gadm.iterrows():
    iso = g["GID_0"]
    gadm_geom = g.geometry

    # Find CShapes match by ISO (via COW lookup)
    cs_match = latest_cs[latest_cs["iso3"] == iso]
    if len(cs_match) == 0:
        continue

    cs_geom = cs_match.iloc[0].geometry

    # Both in equal-area projection
    try:
        from shapely.ops import transform
        import pyproj

        project = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True).transform
        gadm_proj = transform(project, gadm_geom)
        cs_proj = transform(project, cs_geom)

        area_gadm = gadm_proj.area / 1e6  # km²
        area_cs = cs_proj.area / 1e6

        # Intersection area
        try:
            inter = gadm_proj.intersection(cs_proj)
            area_inter = inter.area / 1e6
        except Exception:
            area_inter = 0

        # IoU (Intersection over Union)
        area_union = area_gadm + area_cs - area_inter
        iou = area_inter / area_union if area_union > 0 else 0

        # Area ratio
        area_ratio = area_cs / area_gadm if area_gadm > 0 else 0

        # Centroid offset (in degrees for simplicity)
        gadm_c = gadm_geom.centroid
        cs_c = cs_geom.centroid
        centroid_offset_deg = ((gadm_c.x - cs_c.x)**2 + (gadm_c.y - cs_c.y)**2)**0.5

        comparison_rows.append({
            "iso3": iso,
            "name": g["NAME_0"],
            "cs_name": cs_match.iloc[0]["country_name"],
            "area_gadm_km2": area_gadm,
            "area_cshapes_km2": area_cs,
            "area_ratio": area_ratio,
            "iou": iou,
            "centroid_offset_deg": centroid_offset_deg,
        })
    except Exception as e:
        pass

comp_df = pd.DataFrame(comparison_rows)
comp_df.to_csv(f"{BASE}/data/analysis/polygon_comparison.csv", index=False)

print(f"  Compared {len(comp_df)} countries")
print(f"  Mean IoU: {comp_df['iou'].mean():.3f}")
print(f"  Median IoU: {comp_df['iou'].median():.3f}")
print(f"  Countries with IoU < 0.8: {len(comp_df[comp_df['iou'] < 0.8])}")
print(f"  Countries with IoU < 0.5: {len(comp_df[comp_df['iou'] < 0.5])}")

# Show worst matches
worst = comp_df.nsmallest(20, "iou")
print("\n  Worst IoU matches (CShapes vs GADM):")
for _, r in worst.iterrows():
    print(f"    {r['iso3']:4s} {r['name']:30s} IoU={r['iou']:.3f} "
          f"area_ratio={r['area_ratio']:.2f} centroid_off={r['centroid_offset_deg']:.2f}°")


# ── Comparison 2: CShapes temporal evolution ─────────────────────────
print("\n=== COMPARISON 2: Temporal polygon evolution in CShapes ===")

# For key countries, show how their CShapes polygon changes over time
temporal_countries = ["Germany", "France", "Russia", "Turkey", "China", "India",
                      "United States of America", "United Kingdom", "Italy",
                      "Austria", "Poland", "Japan"]

temporal_results = []
for country_key in temporal_countries:
    # Find in CShapes
    matches = cshapes[cshapes["country_name"].str.contains(country_key, case=False, na=False)]
    if len(matches) == 0:
        continue

    # Get unique country_name entries
    for cname in matches["country_name"].unique():
        entries = matches[matches["country_name"] == cname].sort_values("start_dt")
        if len(entries) < 2:
            continue

        areas = []
        for _, e in entries.iterrows():
            area_deg2 = e.geometry.area
            areas.append({
                "country": cname,
                "start": e["start"],
                "end": e["end"],
                "area_deg2": area_deg2,
                "centroid_lat": e.geometry.centroid.y,
                "centroid_lon": e.geometry.centroid.x,
            })

        temporal_results.extend(areas)
        if len(areas) > 1:
            max_area = max(a["area_deg2"] for a in areas)
            min_area = min(a["area_deg2"] for a in areas)
            ratio = max_area / min_area if min_area > 0 else float('inf')
            print(f"  {cname}: {len(areas)} periods, area range {min_area:.1f}-{max_area:.1f} deg² (ratio {ratio:.1f}x)")

temporal_df = pd.DataFrame(temporal_results)


# ── Comparison 3: CShapes-Europe vs CShapes 2.0 overlap ─────────────
print("\n=== COMPARISON 3: CShapes-Europe vs CShapes 2.0 overlap ===")

eu_names = set(cshapes_eu["polity_name"].unique())
cs_names = set(cshapes["country_name"].unique())

# Find European states present in both
overlap_count = 0
eu_only_count = 0
eu_comparison = []

for _, eu_row in cshapes_eu.iterrows():
    eu_name = eu_row["polity_name"]
    eu_geom = eu_row.geometry
    eu_area = eu_geom.area

    # Try to find in CShapes 2.0
    cs_match = cshapes[cshapes["country_name"].str.contains(eu_name, case=False, na=False)]
    if len(cs_match) > 0:
        overlap_count += 1
        # Compare areas
        cs_area = cs_match.iloc[0].geometry.area
        eu_comparison.append({
            "eu_name": eu_name,
            "cs_name": cs_match.iloc[0]["country_name"],
            "eu_area_deg2": eu_area,
            "cs_area_deg2": cs_area,
            "area_ratio": cs_area / eu_area if eu_area > 0 else 0,
        })
    else:
        eu_only_count += 1
        eu_comparison.append({
            "eu_name": eu_name,
            "cs_name": "",
            "eu_area_deg2": eu_area,
            "cs_area_deg2": 0,
            "area_ratio": 0,
        })

print(f"  CShapes-Europe entries: {len(cshapes_eu)}")
print(f"  Also in CShapes 2.0: {overlap_count}")
print(f"  Only in CShapes-Europe: {eu_only_count}")

eu_comp_df = pd.DataFrame(eu_comparison)
eu_only = eu_comp_df[eu_comp_df["cs_name"] == ""]
if len(eu_only) > 0:
    print(f"\n  CShapes-Europe only (not in CShapes 2.0):")
    for _, r in eu_only.iterrows():
        print(f"    {r['eu_name']:35s} area={r['eu_area_deg2']:.2f} deg²")


# =====================================================================
# PLOTS
# =====================================================================
print("\n─── GENERATING COMPARISON PLOTS ───")

# Plot 1: IoU distribution (CShapes vs GADM)
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

ax = axes[0]
ax.hist(comp_df["iou"], bins=50, color="#2196F3", edgecolor="white")
ax.axvline(comp_df["iou"].median(), color="red", linestyle="--", label=f"Median: {comp_df['iou'].median():.3f}")
ax.axvline(0.8, color="orange", linestyle="--", label="Good threshold (0.8)")
ax.set_xlabel("IoU (Intersection over Union)")
ax.set_ylabel("Count")
ax.set_title("CShapes 2.0 vs GADM: Polygon Agreement", fontweight="bold")
ax.legend()

ax = axes[1]
ax.scatter(comp_df["area_gadm_km2"] / 1000, comp_df["area_cshapes_km2"] / 1000,
           c=comp_df["iou"], cmap="RdYlGn", s=20, alpha=0.7)
ax.plot([0, 20000], [0, 20000], "k--", alpha=0.3, label="1:1 line")
ax.set_xlabel("GADM Area (×1000 km²)")
ax.set_ylabel("CShapes Area (×1000 km²)")
ax.set_title("Area Comparison: CShapes vs GADM", fontweight="bold")
ax.set_xscale("log")
ax.set_yscale("log")
plt.colorbar(ax.collections[0], ax=ax, label="IoU", shrink=0.8)

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/compare_01_cshapes_vs_gadm.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 1: CShapes vs GADM IoU")


# Plot 2: Temporal evolution for key countries
fig, axes = plt.subplots(3, 4, figsize=(20, 14))
axes_flat = axes.flat

for i, country_key in enumerate(temporal_countries):
    if i >= 12:
        break
    ax = axes_flat[i]

    matches = temporal_df[temporal_df["country"].str.contains(country_key, case=False, na=False)]
    if len(matches) == 0:
        ax.set_title(country_key)
        continue

    for cname in matches["country"].unique():
        entries = matches[matches["country"] == cname].sort_values("start")
        starts = pd.to_datetime(entries["start"]).dt.year
        areas = entries["area_deg2"]
        ax.plot(starts, areas, "o-", label=cname[:25], markersize=4)

    ax.set_title(country_key, fontweight="bold", fontsize=10)
    ax.set_xlabel("Year", fontsize=8)
    ax.set_ylabel("Area (deg²)", fontsize=8)
    ax.tick_params(labelsize=7)
    if len(matches["country"].unique()) <= 3:
        ax.legend(fontsize=6)

fig.suptitle("CShapes Polygon Area Evolution Over Time", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/compare_02_temporal_evolution.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 2: temporal evolution")


# Plot 3: Worst IoU countries — bar chart
fig, ax = plt.subplots(figsize=(14, 8))
worst30 = comp_df.nsmallest(30, "iou")
colors = ["#F44336" if x < 0.5 else "#FF9800" if x < 0.8 else "#4CAF50" for x in worst30["iou"]]
ax.barh(range(len(worst30)), worst30["iou"], color=colors)
ax.set_yticks(range(len(worst30)))
ax.set_yticklabels([f"{r['iso3']} ({r['name'][:20]})" for _, r in worst30.iterrows()], fontsize=8)
ax.set_xlabel("IoU")
ax.set_title("30 Countries with Lowest CShapes-GADM Agreement", fontweight="bold")
ax.axvline(0.8, color="green", linestyle="--", alpha=0.5, label="Good (0.8)")
ax.axvline(0.5, color="red", linestyle="--", alpha=0.5, label="Poor (0.5)")
ax.legend()
ax.invert_yaxis()

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/compare_03_worst_iou.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 3: worst IoU")


# Plot 4: Area ratio distribution
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

ax = axes[0]
ratios = comp_df["area_ratio"]
ratios_clipped = ratios.clip(0.1, 10)
ax.hist(ratios_clipped, bins=50, color="#4CAF50", edgecolor="white")
ax.axvline(1.0, color="red", linestyle="--", label="Equal area")
ax.set_xlabel("Area Ratio (CShapes / GADM)")
ax.set_ylabel("Count")
ax.set_title("CShapes vs GADM Area Ratio Distribution", fontweight="bold")
ax.legend()

# Centroid offset
ax = axes[1]
offsets = comp_df["centroid_offset_deg"]
ax.hist(offsets, bins=50, color="#FF9800", edgecolor="white")
ax.axvline(offsets.median(), color="red", linestyle="--",
           label=f"Median: {offsets.median():.3f}°")
ax.set_xlabel("Centroid Offset (degrees)")
ax.set_ylabel("Count")
ax.set_title("CShapes vs GADM Centroid Offset", fontweight="bold")
ax.legend()

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/compare_04_area_ratios.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 4: area ratios & centroid offsets")


# Plot 5: CShapes-Europe overlap comparison
if len(eu_comp_df[eu_comp_df["cs_name"] != ""]) > 0:
    fig, ax = plt.subplots(figsize=(14, 8))
    both = eu_comp_df[eu_comp_df["cs_name"] != ""].copy()
    both = both.sort_values("area_ratio")

    x = range(len(both))
    colors = ["#F44336" if abs(r - 1) > 0.5 else "#FF9800" if abs(r - 1) > 0.2 else "#4CAF50"
              for r in both["area_ratio"]]
    ax.barh(list(x), both["area_ratio"].values, color=colors)
    ax.set_yticks(list(x))
    ax.set_yticklabels(both["eu_name"].values, fontsize=7)
    ax.axvline(1.0, color="black", linestyle="--", alpha=0.5)
    ax.set_xlabel("Area Ratio (CShapes 2.0 / CShapes-Europe)")
    ax.set_title("CShapes 2.0 vs CShapes-Europe: Area Comparison", fontweight="bold")

    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/compare_05_cshapes_vs_europe.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Plot 5: CShapes vs CShapes-Europe")


# ── Summary ──────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("POLYGON COMPARISON SUMMARY")
print("=" * 70)
print(f"Countries compared (CShapes vs GADM): {len(comp_df)}")
print(f"Mean IoU: {comp_df['iou'].mean():.3f}")
print(f"Median IoU: {comp_df['iou'].median():.3f}")
print(f"Countries with poor agreement (IoU < 0.5): {len(comp_df[comp_df['iou'] < 0.5])}")
print(f"Countries with moderate agreement (0.5-0.8): {len(comp_df[(comp_df['iou'] >= 0.5) & (comp_df['iou'] < 0.8)])}")
print(f"Countries with good agreement (IoU >= 0.8): {len(comp_df[comp_df['iou'] >= 0.8])}")
print(f"\nCShapes-Europe entries: {len(cshapes_eu)}")
print(f"  Overlapping with CShapes 2.0: {overlap_count}")
print(f"  Unique to CShapes-Europe: {eu_only_count}")
