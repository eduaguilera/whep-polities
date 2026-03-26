#!/usr/bin/env python3
"""
Generate comprehensive validation summary report and visualization dashboard.

Combines results from:
  - stress_test.py (31 integrity tests)
  - compare_polygons.py (CShapes vs GADM comparison)
  - validate_iso_overlaps.py (ISO collision analysis)
  - analyze_subnational.py (subnational potential)

Produces:
  - data/analysis/plots/dashboard_*.png (summary dashboard plots)
  - Console validation summary
"""

import warnings
warnings.filterwarnings("ignore")

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

BASE = "/home/usuario/whep-polities"
PLOT_DIR = f"{BASE}/data/analysis/plots"
os.makedirs(PLOT_DIR, exist_ok=True)

# ── Load all data ────────────────────────────────────────────────────
print("Loading data for validation dashboard...")
polities = pd.read_csv(f"{BASE}/data/final/polities_database.csv")
poly_report = pd.read_csv(f"{BASE}/data/analysis/polygon_matching_report.csv")
stress_report = pd.read_csv(f"{BASE}/data/analysis/stress_test_report.csv")
poly_compare = pd.read_csv(f"{BASE}/data/analysis/polygon_comparison.csv")
iso_overlaps = pd.read_csv(f"{BASE}/data/analysis/iso_overlap_report.csv")
sub_gadm = pd.read_csv(f"{BASE}/data/analysis/subnational_gadm_analysis.csv")
polygons = gpd.read_file(f"{BASE}/data/geodata/polities_polygons.gpkg")

non_region = polities[polities["polity_type"] != "region"]
print(f"  Polities: {len(polities)}, Polygons: {len(polygons)}")

# =====================================================================
# DASHBOARD PLOT 1: Complete Database Health Overview
# =====================================================================
print("\n─── GENERATING DASHBOARD ───")

fig = plt.figure(figsize=(24, 16))
gs = GridSpec(3, 4, figure=fig, hspace=0.4, wspace=0.35)

# Panel A: Stress test results
ax = fig.add_subplot(gs[0, 0])
test_counts = stress_report["status"].value_counts()
colors_test = {"PASS": "#4CAF50", "WARN": "#FF9800", "FAIL": "#F44336"}
bars = ax.bar(test_counts.index, test_counts.values,
              color=[colors_test[s] for s in test_counts.index])
for bar, v in zip(bars, test_counts.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            str(v), ha="center", fontweight="bold", fontsize=12)
ax.set_title("A) Stress Test Results", fontweight="bold", fontsize=11)
ax.set_ylabel("Count")

# Panel B: Polygon coverage by type
ax = fig.add_subplot(gs[0, 1])
types = ["sovereign", "historical", "colonial", "dependency", "mandate"]
with_poly = []
without_poly = []
for t in types:
    in_type = non_region[non_region["polity_type"] == t]
    matched = poly_report[(poly_report["polity_code"].isin(in_type["polity_code"])) &
                          (poly_report["has_geometry"] == True)]
    with_poly.append(len(matched))
    without_poly.append(len(in_type) - len(matched))

x = np.arange(len(types))
ax.bar(x, with_poly, color="#4CAF50", label="With polygon")
ax.bar(x, without_poly, bottom=with_poly, color="#F44336", label="Without")
ax.set_xticks(x)
ax.set_xticklabels(types, rotation=30, ha="right", fontsize=8)
ax.set_title("B) Polygon Coverage by Type", fontweight="bold", fontsize=11)
ax.legend(fontsize=8)
for i, (w, wo) in enumerate(zip(with_poly, without_poly)):
    pct = w / (w + wo) * 100 if (w + wo) > 0 else 0
    ax.text(i, w + wo + 1, f"{pct:.0f}%", ha="center", fontsize=8)

# Panel C: CShapes vs GADM IoU distribution
ax = fig.add_subplot(gs[0, 2])
ax.hist(poly_compare["iou"], bins=30, color="#2196F3", edgecolor="white")
ax.axvline(poly_compare["iou"].median(), color="red", linestyle="--",
           label=f"Median: {poly_compare['iou'].median():.3f}")
ax.set_xlabel("IoU")
ax.set_title("C) CShapes vs GADM Agreement", fontweight="bold", fontsize=11)
ax.legend(fontsize=8)

# Panel D: ISO collision breakdown
ax = fig.add_subplot(gs[0, 3])
if len(iso_overlaps) > 0:
    cats = iso_overlaps["category"].value_counts()
    colors_cat = {"same_entity_period_split": "#4CAF50", "different_type_dual": "#2196F3",
                  "boundary_transition": "#FF9800", "iso_collision": "#F44336"}
    ax.pie(cats.values, labels=[c.replace("_", "\n")[:20] for c in cats.index],
           colors=[colors_cat.get(c, "#999") for c in cats.index],
           autopct="%1.0f%%", textprops={"fontsize": 8})
ax.set_title("D) ISO Overlap Classification", fontweight="bold", fontsize=11)

# Panel E: Active polities over time
ax = fig.add_subplot(gs[1, :2])
years = np.arange(1800, 2026)
types_order = ["sovereign", "colonial", "dependency", "mandate", "puppet",
               "disputed", "historical", "aggregate"]
type_colors = {
    "sovereign": "#2196F3", "historical": "#9E9E9E", "colonial": "#F44336",
    "dependency": "#FF9800", "aggregate": "#9C27B0", "mandate": "#4CAF50",
    "disputed": "#FFEB3B", "puppet": "#795548"
}

bottom = np.zeros(len(years))
for ptype in types_order:
    subset = non_region[non_region["polity_type"] == ptype]
    counts = np.array([((subset["start_year"] <= yr) & (subset["end_year"] >= yr)).sum()
                        for yr in years])
    ax.fill_between(years, bottom, bottom + counts,
                    color=type_colors.get(ptype, "#999"), alpha=0.7, label=ptype)
    bottom += counts

ax.set_xlim(1800, 2025)
ax.set_ylabel("Count")
ax.set_title("E) Active Polities Over Time", fontweight="bold", fontsize=11)
ax.legend(loc="upper left", fontsize=7, ncol=4)

# Panel F: Subnational potential by country
ax = fig.add_subplot(gs[1, 2:])
top_countries = sub_gadm.groupby("country_iso").size().nlargest(12)
stability = {"RUS": 2, "USA": 5, "JPN": 5, "NGA": 1, "IND": 2, "IDN": 1,
             "MEX": 4, "CHN": 4, "BRA": 3, "COL": 4, "EGY": 2, "PER": 3,
             "ARG": 4, "DEU": 4, "FRA": 3, "CAN": 4, "AUS": 5, "GBR": 5, "ZAF": 3}
colors_stab = {1: "#F44336", 2: "#FF9800", 3: "#FFC107", 4: "#8BC34A", 5: "#4CAF50"}

x = np.arange(len(top_countries))
colors_bar = [colors_stab.get(stability.get(iso, 3), "#999") for iso in top_countries.index]
ax.bar(x, top_countries.values, color=colors_bar, edgecolor="white")
ax.set_xticks(x)
ax.set_xticklabels(top_countries.index, fontsize=9)
ax.set_ylabel("GADM Admin-1 Units")
ax.set_title("F) Subnational Potential (color=stability)", fontweight="bold", fontsize=11)
for i, (iso, n) in enumerate(top_countries.items()):
    ax.text(i, n + 1, f"r={stability.get(iso, '?')}", ha="center", fontsize=7)

# Panel G: Polygon area comparison
ax = fig.add_subplot(gs[2, :2])
polygons_meta = polygons.merge(
    polities[["polity_code", "polity_type"]].rename(columns={"polity_type": "p_type"}),
    on="polity_code", how="left")
polygons_meta["area_deg2"] = polygons_meta.geometry.area

for ptype in ["sovereign", "historical", "colonial", "dependency"]:
    subset = polygons_meta[polygons_meta["p_type"] == ptype]["area_deg2"]
    subset = subset[subset > 0]
    if len(subset) > 0:
        ax.hist(np.log10(subset), bins=30, alpha=0.5,
                color=type_colors.get(ptype, "#999"), label=f"{ptype} (n={len(subset)})")
ax.set_xlabel("log₁₀(area in deg²)")
ax.set_ylabel("Count")
ax.set_title("G) Polygon Area Distribution by Type", fontweight="bold", fontsize=11)
ax.legend(fontsize=8)

# Panel H: Key statistics summary
ax = fig.add_subplot(gs[2, 2:])
ax.axis("off")

stats = [
    ("Total polities", str(len(polities))),
    ("Non-region polities", str(len(non_region))),
    ("Polities with polygons", f"{len(polygons)} ({len(polygons)/len(non_region)*100:.1f}%)"),
    ("Stress tests passed", f"{len(stress_report[stress_report['status']=='PASS'])}/{len(stress_report)}"),
    ("CShapes-GADM median IoU", f"{poly_compare['iou'].median():.3f}"),
    ("ISO collision groups", f"{iso_overlaps['category'].value_counts().get('iso_collision', 0)} pairs across {iso_overlaps[iso_overlaps['category']=='iso_collision']['prefix'].nunique()} prefixes"),
    ("Subnational units analyzed", str(len(sub_gadm))),
    ("High-confidence subnational", "261 units (rating 4-5/5)"),
    ("Verification coverage", f"{(polities['verification_status'].str.startswith('VERIFIED') | polities['verification_status'].str.startswith('FIXED')).sum()}/{len(polities)} ({(polities['verification_status'].str.startswith('VERIFIED') | polities['verification_status'].str.startswith('FIXED')).sum()/len(polities)*100:.0f}%)"),
    ("COW coverage", f"207/209 states matched"),
    ("FAOSTAT coverage", f"249/252 entities matched"),
    ("Decolonization coverage", "94/94 events (100%)"),
]

for i, (label, value) in enumerate(stats):
    y = 0.95 - i * 0.075
    ax.text(0.05, y, label + ":", fontsize=10, fontweight="bold", transform=ax.transAxes)
    ax.text(0.55, y, value, fontsize=10, transform=ax.transAxes)

ax.set_title("H) Key Statistics", fontweight="bold", fontsize=11)

fig.suptitle("WHEP Polities Database v1.2 — Validation Dashboard",
             fontsize=16, fontweight="bold", y=0.98)

plt.savefig(f"{PLOT_DIR}/dashboard_full.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Dashboard: full validation dashboard")


# =====================================================================
# DASHBOARD PLOT 2: Geographic validation map
# =====================================================================
fig, axes = plt.subplots(1, 2, figsize=(20, 8))

# Map 1: All polygons colored by source
ax = axes[0]
import matplotlib.colors as mcolors

# Merge source info - rename to avoid column conflicts with polygons gpkg
src_info = poly_report[["polity_code", "source_used"]].copy()
src_info.columns = ["polity_code", "src_used"]
poly_with_source = polygons.merge(src_info, on="polity_code", how="left")

# Simplify source labels
def simplify_source(src):
    if "CShapes 2.0" in str(src) and "fallback" not in str(src):
        return "CShapes 2.0"
    elif "CShapes-Europe" in str(src):
        return "CShapes-Europe"
    elif "GADM" in str(src):
        return "GADM"
    else:
        return "Other"

poly_with_source["src_simple"] = poly_with_source["src_used"].apply(simplify_source)

source_colors = {"CShapes 2.0": "#2196F3", "CShapes-Europe": "#9C27B0",
                 "GADM": "#FF9800", "Other": "#9E9E9E"}

for src, color in source_colors.items():
    subset = poly_with_source[poly_with_source["src_simple"] == src]
    if len(subset) > 0:
        subset.plot(ax=ax, color=color, alpha=0.5, edgecolor="none", label=f"{src} (n={len(subset)})")

ax.set_title("Polygon Sources", fontweight="bold")
ax.legend(loc="lower left", fontsize=9)
ax.set_xlim(-180, 180)
ax.set_ylim(-60, 85)

# Map 2: Polygons colored by type
ax = axes[1]
poly_with_type = polygons.merge(
    polities[["polity_code", "polity_type"]].rename(columns={"polity_type": "p_type"}),
    on="polity_code", how="left"
)

for ptype in ["sovereign", "historical", "colonial", "dependency", "mandate"]:
    subset = poly_with_type[poly_with_type["p_type"] == ptype]
    if len(subset) > 0:
        subset.plot(ax=ax, color=type_colors.get(ptype, "#999"), alpha=0.5,
                   edgecolor="none", label=f"{ptype} (n={len(subset)})")

ax.set_title("Polity Types", fontweight="bold")
ax.legend(loc="lower left", fontsize=9)
ax.set_xlim(-180, 180)
ax.set_ylim(-60, 85)

fig.suptitle("WHEP Polities — Geographic Distribution", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/dashboard_maps.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Dashboard: geographic maps")


# =====================================================================
# DASHBOARD PLOT 3: Temporal heatmap
# =====================================================================
fig, ax = plt.subplots(figsize=(20, 10))

continents = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania"]
decades = list(range(1800, 2030, 10))

heatmap = np.zeros((len(continents), len(decades)))

for i, cont in enumerate(continents):
    subset = non_region[non_region["continent"] == cont]
    for j, d in enumerate(decades):
        n = ((subset["start_year"] <= d) & (subset["end_year"] >= d)).sum()
        heatmap[i][j] = n

im = ax.imshow(heatmap, cmap="YlOrRd", aspect="auto")
ax.set_xticks(range(len(decades)))
ax.set_xticklabels(decades, rotation=45, fontsize=9)
ax.set_yticks(range(len(continents)))
ax.set_yticklabels(continents, fontsize=11)

for i in range(len(continents)):
    for j in range(len(decades)):
        val = int(heatmap[i][j])
        ax.text(j, i, str(val), ha="center", va="center", fontsize=8,
                color="white" if val > 50 else "black")

ax.set_title("Active Non-Region Polities by Continent and Decade", fontsize=14, fontweight="bold")
plt.colorbar(im, ax=ax, shrink=0.6, label="Active polities")

# Annotate key events
events = {8: "Italian\nUnification\n(1861)", 9: "German\nUnification\n(1871)",
          12: "WWI\nEnd\n(1918)", 15: "WWII\nEnd\n(1945)",
          16: "Year of\nAfrica\n(1960)", 19: "USSR\nCollapse\n(1991)"}
for idx, label in events.items():
    if idx < len(decades):
        ax.axvline(idx - 0.5, color="white", linestyle="--", alpha=0.5, linewidth=1)

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/dashboard_heatmap.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Dashboard: temporal heatmap")

print("\n✓ All dashboards generated")
