#!/usr/bin/env python3
"""
Detailed polygon quality analysis for the WHEP polities database.

Examines polygon geometries for:
1. Area distribution and outliers
2. Complexity (vertex counts)
3. Topology (self-intersections, holes)
4. Multi-polygon fragmentation
5. Centroid validation against claimed continent
6. Boundary precision comparison (CShapes vs GADM)

Produces:
  - data/analysis/plots/polyqual_*.png (5 plots)
  - data/analysis/polygon_quality_report.csv
  - Console analysis
"""

import warnings
warnings.filterwarnings("ignore")

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import MultiPolygon, Polygon
from collections import Counter

BASE = "/home/usuario/whep-polities"
PLOT_DIR = f"{BASE}/data/analysis/plots"
os.makedirs(PLOT_DIR, exist_ok=True)

polities = pd.read_csv(f"{BASE}/data/final/polities_database.csv")
non_region = polities[polities["polity_type"] != "region"]
polygons = gpd.read_file(f"{BASE}/data/geodata/polities_polygons.gpkg")
poly_report = pd.read_csv(f"{BASE}/data/analysis/polygon_matching_report.csv")

TYPE_COLORS = {
    "sovereign": "#2196F3", "historical": "#9E9E9E", "colonial": "#F44336",
    "dependency": "#FF9800", "aggregate": "#9C27B0", "mandate": "#4CAF50",
    "disputed": "#FFEB3B", "puppet": "#795548"
}

print("=" * 70)
print("POLYGON QUALITY ANALYSIS")
print("=" * 70)
print(f"Polygons to analyze: {len(polygons)}")

# Merge metadata
poly_meta = polities[["polity_code", "polity_type", "continent", "polity_name"]].copy()
poly_meta.columns = ["polity_code", "p_type", "p_continent", "p_name"]
poly_all = polygons.merge(poly_meta, on="polity_code", how="left")


# ── Compute geometry properties ──────────────────────────────────────
print("\nComputing geometry properties...")

quality_rows = []
for idx, row in poly_all.iterrows():
    geom = row.geometry
    if geom is None or geom.is_empty:
        continue

    # Basic properties
    area_deg2 = geom.area
    centroid = geom.centroid
    is_valid = geom.is_valid
    bounds = geom.bounds  # minx, miny, maxx, maxy

    # Vertex count
    if isinstance(geom, MultiPolygon):
        n_parts = len(geom.geoms)
        n_vertices = sum(len(p.exterior.coords) for p in geom.geoms)
        n_holes = sum(len(p.interiors) for p in geom.geoms)
    elif isinstance(geom, Polygon):
        n_parts = 1
        n_vertices = len(geom.exterior.coords)
        n_holes = len(geom.interiors)
    else:
        n_parts = 0
        n_vertices = 0
        n_holes = 0

    # Compactness (Polsby-Popper): 4π * area / perimeter²
    if geom.length > 0:
        compactness = 4 * np.pi * area_deg2 / (geom.length ** 2)
    else:
        compactness = 0

    quality_rows.append({
        "polity_code": row["polity_code"],
        "polity_name": row["p_name"],
        "polity_type": row["p_type"],
        "continent": row["p_continent"],
        "area_deg2": area_deg2,
        "centroid_lon": centroid.x,
        "centroid_lat": centroid.y,
        "n_parts": n_parts,
        "n_vertices": n_vertices,
        "n_holes": n_holes,
        "compactness": compactness,
        "is_valid": is_valid,
        "span_lon": bounds[2] - bounds[0],
        "span_lat": bounds[3] - bounds[1],
    })

quality_df = pd.DataFrame(quality_rows)
print(f"Analyzed {len(quality_df)} polygons")


# ── Console summary ──────────────────────────────────────────────────
print("\n─── GEOMETRY SUMMARY ───")
print(f"Valid geometries: {quality_df['is_valid'].sum()}/{len(quality_df)}")
print(f"MultiPolygons: {(quality_df['n_parts'] > 1).sum()}")
print(f"Polygons with holes: {(quality_df['n_holes'] > 0).sum()}")
print(f"\nArea (deg²): median={quality_df['area_deg2'].median():.2f}, "
      f"min={quality_df['area_deg2'].min():.6f}, max={quality_df['area_deg2'].max():.1f}")
print(f"Vertices: median={quality_df['n_vertices'].median():.0f}, "
      f"min={quality_df['n_vertices'].min()}, max={quality_df['n_vertices'].max()}")
print(f"Parts: median={quality_df['n_parts'].median():.0f}, max={quality_df['n_parts'].max()}")
print(f"Compactness: median={quality_df['compactness'].median():.3f}")

# Most fragmented
print("\nMost fragmented (by # parts):")
frag = quality_df.nlargest(10, "n_parts")
for _, row in frag.iterrows():
    print(f"  {row['polity_code']:25s} {row['polity_name'][:30]:30s} {row['n_parts']:5d} parts")

# Most complex
print("\nMost complex (by vertex count):")
complex_poly = quality_df.nlargest(10, "n_vertices")
for _, row in complex_poly.iterrows():
    print(f"  {row['polity_code']:25s} {row['polity_name'][:30]:30s} {row['n_vertices']:7d} vertices")

# Tiniest
print("\nSmallest polygons (by area):")
tiny = quality_df.nsmallest(10, "area_deg2")
for _, row in tiny.iterrows():
    print(f"  {row['polity_code']:25s} {row['polity_name'][:30]:30s} {row['area_deg2']:.6f} deg²")

# Largest
print("\nLargest polygons (by area):")
big = quality_df.nlargest(10, "area_deg2")
for _, row in big.iterrows():
    print(f"  {row['polity_code']:25s} {row['polity_name'][:30]:30s} {row['area_deg2']:.1f} deg²")


# ── Centroid-continent validation ────────────────────────────────────
print("\n─── CENTROID-CONTINENT VALIDATION ───")

# Approximate continent bounding boxes
continent_bounds = {
    "Africa": (-25, -35, 55, 40),
    "Asia": (25, -15, 180, 80),
    "Europe": (-25, 35, 65, 75),
    "North America": (-170, 5, -50, 85),
    "South America": (-85, -60, -30, 15),
    "Oceania": (90, -55, 180, 25),
    "Antarctica": (-180, -90, 180, -60),
}

mismatches = []
for _, row in quality_df.iterrows():
    cont = row["continent"]
    if cont not in continent_bounds or cont == "Global":
        continue
    minx, miny, maxx, maxy = continent_bounds[cont]
    lon, lat = row["centroid_lon"], row["centroid_lat"]
    if not (minx <= lon <= maxx and miny <= lat <= maxy):
        mismatches.append(row)

print(f"Centroid outside claimed continent bounds: {len(mismatches)}")
for row in mismatches[:15]:
    print(f"  {row['polity_code']:25s} {row['polity_name'][:25]:25s} "
          f"({row['centroid_lon']:.1f}, {row['centroid_lat']:.1f}) claimed: {row['continent']}")


# =====================================================================
# PLOTS
# =====================================================================
print("\n─── GENERATING PLOTS ───")

# Plot 1: Area distribution analysis
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# A: Area histogram by type
ax = axes[0, 0]
for ptype in ["sovereign", "historical", "colonial", "dependency"]:
    subset = quality_df[quality_df["polity_type"] == ptype]
    areas = subset["area_deg2"]
    areas = areas[areas > 0]
    if len(areas) > 0:
        ax.hist(np.log10(areas), bins=30, alpha=0.5,
                color=TYPE_COLORS.get(ptype, "#999"), label=f"{ptype} (n={len(areas)})")
ax.set_xlabel("log₁₀(area in deg²)")
ax.set_ylabel("Count")
ax.set_title("A) Polygon Area Distribution by Type", fontweight="bold")
ax.legend(fontsize=8)

# B: Vertex count histogram
ax = axes[0, 1]
for ptype in ["sovereign", "historical", "colonial", "dependency"]:
    subset = quality_df[quality_df["polity_type"] == ptype]
    ax.hist(np.log10(subset["n_vertices"].clip(lower=1)), bins=30, alpha=0.5,
            color=TYPE_COLORS.get(ptype, "#999"), label=ptype)
ax.set_xlabel("log₁₀(vertex count)")
ax.set_ylabel("Count")
ax.set_title("B) Polygon Complexity by Type", fontweight="bold")
ax.legend(fontsize=8)

# C: Area vs vertex count scatter
ax = axes[1, 0]
for ptype in ["sovereign", "historical", "colonial", "dependency"]:
    subset = quality_df[quality_df["polity_type"] == ptype]
    ax.scatter(np.log10(subset["area_deg2"].clip(lower=1e-6)),
              np.log10(subset["n_vertices"].clip(lower=1)),
              color=TYPE_COLORS.get(ptype, "#999"), alpha=0.4, s=15, label=ptype)
ax.set_xlabel("log₁₀(area)")
ax.set_ylabel("log₁₀(vertices)")
ax.set_title("C) Area vs Complexity", fontweight="bold")
ax.legend(fontsize=8)

# D: Compactness by type
ax = axes[1, 1]
types = ["sovereign", "historical", "colonial", "dependency"]
data = [quality_df[quality_df["polity_type"] == t]["compactness"].values for t in types]
bp = ax.boxplot(data, labels=types, patch_artist=True)
for patch, ptype in zip(bp["boxes"], types):
    patch.set_facecolor(TYPE_COLORS.get(ptype, "#999"))
    patch.set_alpha(0.6)
ax.set_ylabel("Compactness (Polsby-Popper)")
ax.set_title("D) Shape Compactness by Type", fontweight="bold")

plt.suptitle("Polygon Geometry Quality Analysis", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/polyqual_01_area_complexity.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 1: area & complexity analysis")


# Plot 2: Fragmentation analysis
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# A: Parts distribution
ax = axes[0]
parts_hist = quality_df["n_parts"].value_counts().sort_index()
parts_hist_top = parts_hist[parts_hist.index <= 20]
ax.bar(parts_hist_top.index, parts_hist_top.values, color="#2196F3", alpha=0.7)
ax.set_xlabel("Number of polygon parts")
ax.set_ylabel("Count")
ax.set_title("A) Polygon Part Count Distribution", fontweight="bold")
ax.text(0.7, 0.9, f"Max: {quality_df['n_parts'].max()} parts",
        transform=ax.transAxes, fontsize=9)

# B: Holes distribution
ax = axes[1]
holes_hist = quality_df["n_holes"].value_counts().sort_index()
holes_hist_top = holes_hist[holes_hist.index <= 10]
ax.bar(holes_hist_top.index, holes_hist_top.values, color="#FF9800", alpha=0.7)
ax.set_xlabel("Number of holes")
ax.set_ylabel("Count")
ax.set_title("B) Polygon Hole Count Distribution", fontweight="bold")
holes_gt0 = (quality_df["n_holes"] > 0).sum()
ax.text(0.5, 0.9, f"{holes_gt0} polygons with holes",
        transform=ax.transAxes, fontsize=9)

# C: Most fragmented polities
ax = axes[2]
top_frag = quality_df.nlargest(15, "n_parts")
y = np.arange(len(top_frag))
colors = [TYPE_COLORS.get(t, "#999") for t in top_frag["polity_type"]]
ax.barh(y, top_frag["n_parts"], color=colors, alpha=0.7)
ax.set_yticks(y)
ax.set_yticklabels([f"{row['polity_name'][:25]}" for _, row in top_frag.iterrows()],
                   fontsize=8)
ax.set_xlabel("Number of polygon parts")
ax.set_title("C) Most Fragmented Polities", fontweight="bold")
ax.invert_yaxis()

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/polyqual_02_fragmentation.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 2: fragmentation analysis")


# Plot 3: Geographic extent analysis
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# A: Centroid scatter colored by type
ax = axes[0]
for ptype in ["sovereign", "historical", "colonial", "dependency", "mandate"]:
    subset = quality_df[quality_df["polity_type"] == ptype]
    ax.scatter(subset["centroid_lon"], subset["centroid_lat"],
              color=TYPE_COLORS.get(ptype, "#999"), alpha=0.5, s=15, label=ptype)
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_title("A) Polity Centroids by Type", fontweight="bold")
ax.legend(fontsize=7, loc="lower left")
ax.set_xlim(-180, 180)
ax.set_ylim(-60, 85)
ax.axhline(0, color="gray", linewidth=0.5)
ax.axvline(0, color="gray", linewidth=0.5)

# B: Centroid scatter colored by start year
ax = axes[1]
sc = ax.scatter(quality_df["centroid_lon"], quality_df["centroid_lat"],
               c=quality_df.merge(non_region[["polity_code", "start_year"]],
                                   on="polity_code", how="left")["start_year"],
               cmap="viridis", alpha=0.5, s=15)
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_title("B) Polity Centroids by Start Year", fontweight="bold")
plt.colorbar(sc, ax=ax, shrink=0.7, label="Start Year")
ax.set_xlim(-180, 180)
ax.set_ylim(-60, 85)

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/polyqual_03_centroids.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 3: centroid analysis")


# Plot 4: Polygon source quality comparison
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Merge source info
src_info = poly_report[["polity_code", "source_used"]].copy()
src_info.columns = ["polity_code", "src_used"]
quality_with_src = quality_df.merge(src_info, on="polity_code", how="left")

def simplify_source(src):
    if pd.isna(src):
        return "Unknown"
    if "CShapes 2.0" in str(src) and "fallback" not in str(src):
        return "CShapes 2.0"
    elif "CShapes-Europe" in str(src):
        return "CShapes-Europe"
    elif "GADM" in str(src):
        return "GADM"
    else:
        return "Other"

quality_with_src["src_simple"] = quality_with_src["src_used"].apply(simplify_source)

source_colors = {"CShapes 2.0": "#2196F3", "CShapes-Europe": "#9C27B0",
                 "GADM": "#FF9800", "Other": "#9E9E9E", "Unknown": "#E0E0E0"}

# A: Vertex count by source
ax = axes[0, 0]
sources = ["CShapes 2.0", "CShapes-Europe", "GADM"]
data = [quality_with_src[quality_with_src["src_simple"] == s]["n_vertices"].values
        for s in sources]
bp = ax.boxplot(data, labels=sources, patch_artist=True)
for patch, src in zip(bp["boxes"], sources):
    patch.set_facecolor(source_colors.get(src, "#999"))
    patch.set_alpha(0.6)
ax.set_ylabel("Vertex Count")
ax.set_title("A) Polygon Complexity by Source", fontweight="bold")
ax.set_yscale("log")

# B: Compactness by source
ax = axes[0, 1]
data = [quality_with_src[quality_with_src["src_simple"] == s]["compactness"].values
        for s in sources]
bp = ax.boxplot(data, labels=sources, patch_artist=True)
for patch, src in zip(bp["boxes"], sources):
    patch.set_facecolor(source_colors.get(src, "#999"))
    patch.set_alpha(0.6)
ax.set_ylabel("Compactness")
ax.set_title("B) Shape Compactness by Source", fontweight="bold")

# C: Parts count by source
ax = axes[1, 0]
data = [quality_with_src[quality_with_src["src_simple"] == s]["n_parts"].values
        for s in sources]
bp = ax.boxplot(data, labels=sources, patch_artist=True)
for patch, src in zip(bp["boxes"], sources):
    patch.set_facecolor(source_colors.get(src, "#999"))
    patch.set_alpha(0.6)
ax.set_ylabel("Parts Count")
ax.set_title("C) Fragmentation by Source", fontweight="bold")

# D: Area by source
ax = axes[1, 1]
for src in sources:
    subset = quality_with_src[quality_with_src["src_simple"] == src]
    areas = subset["area_deg2"]
    areas = areas[areas > 0]
    if len(areas) > 0:
        ax.hist(np.log10(areas), bins=25, alpha=0.5,
                color=source_colors.get(src, "#999"), label=f"{src} (n={len(areas)})")
ax.set_xlabel("log₁₀(area in deg²)")
ax.set_ylabel("Count")
ax.set_title("D) Area Distribution by Source", fontweight="bold")
ax.legend(fontsize=8)

plt.suptitle("Polygon Quality by Source Dataset", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/polyqual_04_by_source.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 4: source quality comparison")


# Plot 5: Polygon quality summary dashboard
fig = plt.figure(figsize=(20, 10))

# Summary statistics panel
ax = fig.add_subplot(121)
ax.axis("off")

stats = [
    ("Total polygons", str(len(quality_df))),
    ("Valid geometries", f"{quality_df['is_valid'].sum()}/{len(quality_df)} ({quality_df['is_valid'].mean()*100:.1f}%)"),
    ("", ""),
    ("Area (deg²)", ""),
    ("  Median", f"{quality_df['area_deg2'].median():.2f}"),
    ("  Min", f"{quality_df['area_deg2'].min():.6f}"),
    ("  Max", f"{quality_df['area_deg2'].max():.1f}"),
    ("", ""),
    ("Vertices", ""),
    ("  Median", f"{quality_df['n_vertices'].median():.0f}"),
    ("  Max", f"{quality_df['n_vertices'].max():,}"),
    ("", ""),
    ("MultiPolygons (>1 part)", f"{(quality_df['n_parts'] > 1).sum()} ({(quality_df['n_parts'] > 1).mean()*100:.1f}%)"),
    ("With holes", f"{(quality_df['n_holes'] > 0).sum()} ({(quality_df['n_holes'] > 0).mean()*100:.1f}%)"),
    ("", ""),
    ("Compactness (Polsby-Popper)", ""),
    ("  Median", f"{quality_df['compactness'].median():.3f}"),
    ("  Most compact", f"{quality_df.loc[quality_df['compactness'].idxmax(), 'polity_name'][:25]}"),
    ("  Least compact", f"{quality_df.loc[quality_df['compactness'].idxmin(), 'polity_name'][:25]}"),
    ("", ""),
    ("Centroid mismatches", f"{len(mismatches)} outside continent bounds"),
    ("", ""),
    ("By source:", ""),
    ("  CShapes 2.0", f"{(quality_with_src['src_simple'] == 'CShapes 2.0').sum()}"),
    ("  CShapes-Europe", f"{(quality_with_src['src_simple'] == 'CShapes-Europe').sum()}"),
    ("  GADM", f"{(quality_with_src['src_simple'] == 'GADM').sum()}"),
]

for i, (label, value) in enumerate(stats):
    y = 0.98 - i * 0.035
    if label:
        ax.text(0.05, y, label, fontsize=10, fontweight="bold" if not label.startswith("  ") else "normal",
                transform=ax.transAxes)
        ax.text(0.6, y, value, fontsize=10, transform=ax.transAxes)

ax.set_title("Polygon Quality Summary", fontweight="bold", fontsize=13)

# Quality score by continent
ax = fig.add_subplot(122)
cont_stats = []
for cont in ["Africa", "Asia", "Europe", "North America", "South America", "Oceania"]:
    subset = quality_df[quality_df["continent"] == cont]
    if len(subset) > 0:
        cont_stats.append({
            "continent": cont,
            "count": len(subset),
            "median_area": subset["area_deg2"].median(),
            "median_vertices": subset["n_vertices"].median(),
            "median_compactness": subset["compactness"].median(),
            "pct_multi": (subset["n_parts"] > 1).mean() * 100,
        })

cont_df = pd.DataFrame(cont_stats)
x = np.arange(len(cont_df))
width = 0.3

ax2 = ax.twinx()
bars1 = ax.bar(x - width/2, cont_df["median_vertices"], width,
               color="#2196F3", alpha=0.7, label="Median vertices")
bars2 = ax2.bar(x + width/2, cont_df["pct_multi"], width,
                color="#FF9800", alpha=0.7, label="% MultiPolygon")

ax.set_xticks(x)
ax.set_xticklabels(cont_df["continent"], rotation=30, ha="right", fontsize=9)
ax.set_ylabel("Median Vertices", color="#2196F3")
ax2.set_ylabel("% MultiPolygon", color="#FF9800")
ax.set_title("Polygon Quality by Continent", fontweight="bold")

# Combined legend
lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc="upper left")

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/polyqual_05_summary.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 5: quality summary dashboard")


# ── Save report ──────────────────────────────────────────────────────
quality_df.to_csv(f"{BASE}/data/analysis/polygon_quality_report.csv", index=False)
print(f"\nSaved: data/analysis/polygon_quality_report.csv")

print("\n✓ Polygon quality analysis complete")
print(f"  5 plots saved to {PLOT_DIR}/polyqual_*.png")
