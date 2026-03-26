#!/usr/bin/env python3
"""
Comprehensive analysis, cross-validation, and visualization for the WHEP polities database.

Generates:
  1. Temporal analysis (formation/dissolution timelines, active counts by decade)
  2. Type distribution and data source coverage
  3. Cross-validation against COW, FAOSTAT, decolonization events
  4. Polygon coverage analysis (by type, continent, decade)
  5. Subnational polygon quality tier analysis
  6. Excel region matching sankey-style breakdown
  7. Geographic maps (polity density, temporal snapshots, subnational tiers)
  8. Duration distributions
  9. Data quality diagnostics (gaps, overlaps, consistency)

All plots saved to data/analysis/plots/
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
from collections import Counter

BASE = "/home/usuario/whep-polities"
PLOT_DIR = f"{BASE}/data/analysis/plots"
os.makedirs(PLOT_DIR, exist_ok=True)

# ── Load all data ────────────────────────────────────────────────────
print("Loading data...")
polities = pd.read_csv(f"{BASE}/data/final/polities_database.csv")
matching = pd.read_csv(f"{BASE}/data/analysis/region_matching.csv")
poly_report = pd.read_csv(f"{BASE}/data/analysis/polygon_matching_report.csv")
sub_report = pd.read_csv(f"{BASE}/data/analysis/subnational_report.csv")
excel_cov = pd.read_csv(f"{BASE}/data/analysis/excel_polygon_coverage.csv")
cow = pd.read_csv(f"{BASE}/data/external/cow_state_system.csv")
decol = pd.read_csv(f"{BASE}/data/external/decolonization_events.csv")
empire = pd.read_csv(f"{BASE}/data/external/empire_dissolutions.csv")

# Load polygons
polygons = gpd.read_file(f"{BASE}/data/geodata/polities_polygons.gpkg")
subnational_gdf = gpd.read_file(f"{BASE}/data/geodata/subnational_polygons.gpkg")

non_region = polities[polities["polity_type"] != "region"]

print(f"  Polities: {len(polities)}, Polygons: {len(polygons)}, Subnational: {len(subnational_gdf)}")
print(f"  COW: {len(cow)}, Decolonization: {len(decol)}, Empires: {len(empire)}")

# ── Color schemes ────────────────────────────────────────────────────
TYPE_COLORS = {
    "sovereign": "#2196F3",
    "historical": "#9E9E9E",
    "colonial": "#F44336",
    "dependency": "#FF9800",
    "aggregate": "#9C27B0",
    "mandate": "#4CAF50",
    "disputed": "#FFEB3B",
    "puppet": "#795548",
    "region": "#E0E0E0",
}
CONTINENT_COLORS = {
    "Africa": "#F44336",
    "Asia": "#FF9800",
    "Europe": "#2196F3",
    "North America": "#4CAF50",
    "South America": "#8BC34A",
    "Oceania": "#00BCD4",
    "Antarctica": "#B0BEC5",
    "Global": "#9E9E9E",
}
TIER_COLORS = {1: "#4CAF50", 2: "#2196F3", 3: "#FF9800", 4: "#F44336", 0: "#9E9E9E"}


# =====================================================================
# PLOT 1: Formation and Dissolution Timeline
# =====================================================================
def plot_formation_dissolution():
    print("  Plot 1: Formation/dissolution timeline...")
    fig, axes = plt.subplots(2, 1, figsize=(16, 10), sharex=True)

    years = range(1800, 2026)

    # Formations by decade
    ax = axes[0]
    formations = non_region["start_year"].values
    bins = np.arange(1800, 2030, 5)
    for ptype in ["sovereign", "historical", "colonial", "dependency", "mandate", "aggregate", "puppet", "disputed"]:
        subset = non_region[non_region["polity_type"] == ptype]["start_year"]
        ax.hist(subset, bins=bins, alpha=0.7, color=TYPE_COLORS[ptype], label=ptype, stacked=False)

    # Stacked histogram
    ax.clear()
    types_order = ["sovereign", "historical", "colonial", "dependency", "mandate", "aggregate", "puppet", "disputed"]
    data = [non_region[non_region["polity_type"] == t]["start_year"].values for t in types_order]
    colors = [TYPE_COLORS[t] for t in types_order]
    ax.hist(data, bins=bins, stacked=True, color=colors, label=types_order, edgecolor="white", linewidth=0.3)
    ax.set_ylabel("New polities (5-year bins)", fontsize=11)
    ax.set_title("Polity Formations Over Time", fontsize=13, fontweight="bold")
    ax.legend(loc="upper left", fontsize=8, ncol=4)

    # Key events
    events = {1861: "Italian\nunification", 1871: "German\nunification",
              1918: "WWI\nend", 1945: "WWII\nend", 1960: "Year of\nAfrica",
              1991: "USSR\ndissolution"}
    for yr, label in events.items():
        ax.axvline(yr, color="black", linestyle="--", alpha=0.4, linewidth=0.8)
        ax.text(yr, ax.get_ylim()[1] * 0.85, label, ha="center", fontsize=7, alpha=0.7)

    # Dissolutions by decade
    ax = axes[1]
    ended = non_region[non_region["end_year"] < 2025]
    data_end = [ended[ended["polity_type"] == t]["end_year"].values for t in types_order]
    ax.hist(data_end, bins=bins, stacked=True, color=colors, label=types_order, edgecolor="white", linewidth=0.3)
    ax.set_ylabel("Dissolved polities (5-year bins)", fontsize=11)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_title("Polity Dissolutions Over Time", fontsize=13, fontweight="bold")
    for yr, label in events.items():
        ax.axvline(yr, color="black", linestyle="--", alpha=0.4, linewidth=0.8)

    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/01_formation_dissolution_timeline.png", dpi=150, bbox_inches="tight")
    plt.close()


# =====================================================================
# PLOT 2: Active Polities Over Time (stacked area)
# =====================================================================
def plot_active_polities():
    print("  Plot 2: Active polities over time...")
    fig, ax = plt.subplots(figsize=(16, 8))

    years = np.arange(1800, 2026)
    types_order = ["sovereign", "colonial", "dependency", "mandate", "puppet", "disputed", "historical", "aggregate"]

    stacked = {}
    for ptype in types_order:
        subset = non_region[non_region["polity_type"] == ptype]
        counts = []
        for yr in years:
            n = ((subset["start_year"] <= yr) & (subset["end_year"] >= yr)).sum()
            counts.append(n)
        stacked[ptype] = np.array(counts)

    # Stacked area chart
    bottom = np.zeros(len(years))
    for ptype in types_order:
        ax.fill_between(years, bottom, bottom + stacked[ptype],
                        color=TYPE_COLORS[ptype], alpha=0.7, label=ptype)
        bottom += stacked[ptype]

    ax.set_xlim(1800, 2025)
    ax.set_ylabel("Number of Active Polities", fontsize=12)
    ax.set_xlabel("Year", fontsize=12)
    ax.set_title("Active Polities Over Time (Excluding Statistical Regions)", fontsize=14, fontweight="bold")
    ax.legend(loc="upper left", fontsize=9, ncol=2)

    # Annotate key totals
    for yr in [1850, 1900, 1920, 1945, 1960, 1990, 2025]:
        total = sum(stacked[t][yr - 1800] for t in types_order)
        ax.annotate(f"{total}", (yr, total), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=8, fontweight="bold")

    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/02_active_polities_stacked.png", dpi=150, bbox_inches="tight")
    plt.close()


# =====================================================================
# PLOT 3: Type Distribution (pie + bar)
# =====================================================================
def plot_type_distribution():
    print("  Plot 3: Type distribution...")
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Pie chart (non-region)
    ax = axes[0]
    type_counts = non_region["polity_type"].value_counts()
    colors = [TYPE_COLORS[t] for t in type_counts.index]
    wedges, texts, autotexts = ax.pie(type_counts.values, labels=type_counts.index,
                                       colors=colors, autopct="%1.1f%%",
                                       pctdistance=0.85, startangle=90)
    for t in autotexts:
        t.set_fontsize(9)
    ax.set_title(f"Polity Type Distribution (n={len(non_region)})", fontsize=13, fontweight="bold")

    # Bar by continent (stacked by type)
    ax = axes[1]
    types_order = ["sovereign", "historical", "colonial", "dependency", "mandate", "aggregate", "puppet", "disputed"]
    continents = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania", "Antarctica"]
    cont_data = {}
    for cont in continents:
        cont_data[cont] = {}
        for ptype in types_order:
            cont_data[cont][ptype] = len(non_region[(non_region["continent"] == cont) &
                                                     (non_region["polity_type"] == ptype)])

    x = np.arange(len(continents))
    width = 0.7
    bottom = np.zeros(len(continents))
    for ptype in types_order:
        vals = [cont_data[c][ptype] for c in continents]
        ax.bar(x, vals, width, bottom=bottom, color=TYPE_COLORS[ptype], label=ptype, edgecolor="white", linewidth=0.3)
        bottom += np.array(vals)

    ax.set_xticks(x)
    ax.set_xticklabels(continents, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("Number of Polities", fontsize=11)
    ax.set_title("Polities by Continent and Type", fontsize=13, fontweight="bold")
    ax.legend(loc="upper right", fontsize=8)

    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/03_type_distribution.png", dpi=150, bbox_inches="tight")
    plt.close()


# =====================================================================
# PLOT 4: Duration Distribution
# =====================================================================
def plot_duration_distribution():
    print("  Plot 4: Duration distributions...")
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Histogram of durations by type
    ax = axes[0]
    for ptype in ["sovereign", "historical", "colonial", "dependency"]:
        subset = non_region[non_region["polity_type"] == ptype]
        ax.hist(subset["duration_years"], bins=30, alpha=0.5, color=TYPE_COLORS[ptype],
                label=f"{ptype} (n={len(subset)}, med={subset['duration_years'].median():.0f}yr)")
    ax.set_xlabel("Duration (years)", fontsize=11)
    ax.set_ylabel("Count", fontsize=11)
    ax.set_title("Polity Duration Distribution by Type", fontsize=13, fontweight="bold")
    ax.legend(fontsize=9)
    ax.set_xlim(0, 230)

    # Box plot by continent
    ax = axes[1]
    continents = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania"]
    data_by_cont = [non_region[non_region["continent"] == c]["duration_years"].values for c in continents]
    bp = ax.boxplot(data_by_cont, labels=continents, patch_artist=True)
    for patch, cont in zip(bp["boxes"], continents):
        patch.set_facecolor(CONTINENT_COLORS[cont])
        patch.set_alpha(0.6)
    ax.set_ylabel("Duration (years)", fontsize=11)
    ax.set_title("Polity Duration by Continent", fontsize=13, fontweight="bold")
    ax.tick_params(axis="x", rotation=30)

    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/04_duration_distribution.png", dpi=150, bbox_inches="tight")
    plt.close()


# =====================================================================
# PLOT 5: Data Source Coverage Matrix
# =====================================================================
def plot_data_source_coverage():
    print("  Plot 5: Data source coverage...")
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Source combinations
    sources = ["FT", "FAOSTAT", "M49", "CShapes", "WHEP-fix"]
    source_matrix = np.zeros((len(sources), len(sources)))
    for _, row in polities.iterrows():
        ds = str(row["data_sources"])
        present = [s for s in sources if s in ds]
        for i, s1 in enumerate(sources):
            for j, s2 in enumerate(sources):
                if s1 in present and s2 in present:
                    source_matrix[i][j] += 1

    ax = axes[0]
    im = ax.imshow(source_matrix, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(sources)))
    ax.set_yticks(range(len(sources)))
    ax.set_xticklabels(sources, fontsize=10)
    ax.set_yticklabels(sources, fontsize=10)
    for i in range(len(sources)):
        for j in range(len(sources)):
            ax.text(j, i, f"{int(source_matrix[i][j])}", ha="center", va="center",
                    fontsize=10, fontweight="bold",
                    color="white" if source_matrix[i][j] > 400 else "black")
    ax.set_title("Data Source Co-occurrence Matrix", fontsize=13, fontweight="bold")
    plt.colorbar(im, ax=ax, shrink=0.8)

    # Source coverage by polity type
    ax = axes[1]
    types_order = ["sovereign", "historical", "colonial", "dependency", "aggregate", "mandate"]
    x = np.arange(len(types_order))
    width = 0.15
    for i, src in enumerate(sources):
        counts = []
        for ptype in types_order:
            subset = polities[polities["polity_type"] == ptype]
            n = subset["data_sources"].str.contains(src, na=False).sum()
            counts.append(n)
        ax.bar(x + i * width - 2 * width, counts, width, label=src, alpha=0.8)

    ax.set_xticks(x)
    ax.set_xticklabels(types_order, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("Number of Polities", fontsize=11)
    ax.set_title("Data Source Coverage by Polity Type", fontsize=13, fontweight="bold")
    ax.legend(fontsize=9)

    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/05_data_source_coverage.png", dpi=150, bbox_inches="tight")
    plt.close()


# =====================================================================
# PLOT 6: Cross-Validation with COW
# =====================================================================
def plot_cow_crossvalidation():
    print("  Plot 6: COW cross-validation...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Match COW to our database (numeric comparison)
    our_cow_codes = set(int(float(c)) for c in polities["cow_code"].dropna())
    cow_codes_set = set(int(c) for c in cow["cow_code"])
    cow_matched = len(our_cow_codes & cow_codes_set)
    cow_only = len(cow_codes_set - our_cow_codes)
    whep_no_cow = len(non_region[non_region["cow_code"].isna()])

    # Venn-style summary
    ax = axes[0]
    labels = ["Matched\n(in both)", "COW only\n(missing)", "WHEP only\n(no COW code)"]
    values = [cow_matched, cow_only, whep_no_cow]
    colors_v = ["#4CAF50", "#F44336", "#2196F3"]
    bars = ax.bar(labels, values, color=colors_v, edgecolor="white", linewidth=1.5)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3,
                str(v), ha="center", fontweight="bold", fontsize=12)
    ax.set_ylabel("Count", fontsize=11)
    ax.set_title(f"COW State System Cross-Validation\n(COW: {len(cow)} states)", fontsize=12, fontweight="bold")

    # Temporal overlap
    ax = axes[1]
    decades = range(1820, 2030, 10)
    cow_active = []
    whep_active = []
    sovereign_only = non_region[non_region["polity_type"] == "sovereign"]
    for d in decades:
        cow_n = ((cow["cow_start"] <= d) & (cow["cow_end"] >= d)).sum()
        whep_n = ((sovereign_only["start_year"] <= d) & (sovereign_only["end_year"] >= d)).sum()
        cow_active.append(cow_n)
        whep_active.append(whep_n)

    ax.plot(list(decades), cow_active, "o-", color="#F44336", label=f"COW ({len(cow)})", linewidth=2)
    ax.plot(list(decades), whep_active, "s-", color="#2196F3", label=f"WHEP sovereign ({len(sovereign_only)})", linewidth=2)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Active States", fontsize=11)
    ax.set_title("Active Sovereign States: COW vs WHEP", fontsize=12, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)

    # Decolonization coverage
    ax = axes[2]
    decol_matched = 0
    decol_iso_set = set(decol["iso3"].dropna().astype(str))
    our_iso_set = set(polities["iso3_code"].dropna().astype(str))
    matched_iso = decol_iso_set & our_iso_set
    decol_only = decol_iso_set - our_iso_set
    by_decade = Counter()
    for _, d in decol.iterrows():
        decade = (d["independence_year"] // 10) * 10
        by_decade[decade] += 1

    decades_d = sorted(by_decade.keys())
    matched_by_decade = []
    for dec in decades_d:
        sub = decol[(decol["independence_year"] >= dec) & (decol["independence_year"] < dec + 10)]
        n_matched = sum(1 for _, r in sub.iterrows() if str(r["iso3"]) in our_iso_set)
        matched_by_decade.append(n_matched)

    totals_d = [by_decade[d] for d in decades_d]
    ax.bar(decades_d, totals_d, width=8, color="#FFB74D", label="Total events", edgecolor="white")
    ax.bar(decades_d, matched_by_decade, width=8, color="#4CAF50", label="Matched in WHEP", edgecolor="white")
    ax.set_xlabel("Decade", fontsize=11)
    ax.set_ylabel("Decolonization Events", fontsize=11)
    ax.set_title(f"Decolonization Coverage\n({len(matched_iso)}/{len(decol_iso_set)} matched)", fontsize=12, fontweight="bold")
    ax.legend(fontsize=10)

    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/06_cross_validation.png", dpi=150, bbox_inches="tight")
    plt.close()


# =====================================================================
# PLOT 7: Polygon Coverage Analysis
# =====================================================================
def plot_polygon_coverage():
    print("  Plot 7: Polygon coverage...")
    fig = plt.figure(figsize=(18, 12))
    gs = GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.3)

    merged = polities.merge(poly_report[["polity_code", "has_geometry", "source_used"]],
                            on="polity_code", how="left")
    merged["has_geometry"] = merged["has_geometry"].fillna(False)

    # 7a: By type
    ax = fig.add_subplot(gs[0, 0])
    types_order = ["sovereign", "historical", "colonial", "dependency", "mandate", "aggregate", "puppet", "disputed"]
    with_g = []
    without_g = []
    for ptype in types_order:
        sub = merged[merged["polity_type"] == ptype]
        with_g.append(sub["has_geometry"].sum())
        without_g.append(len(sub) - sub["has_geometry"].sum())

    x = np.arange(len(types_order))
    ax.barh(x, with_g, color="#4CAF50", label="With polygon", edgecolor="white")
    ax.barh(x, without_g, left=with_g, color="#F44336", label="Without polygon", edgecolor="white")
    ax.set_yticks(x)
    ax.set_yticklabels(types_order, fontsize=9)
    ax.set_xlabel("Count", fontsize=10)
    ax.set_title("Polygon Coverage by Type", fontsize=12, fontweight="bold")
    ax.legend(fontsize=8)
    for i, (w, wo) in enumerate(zip(with_g, without_g)):
        if w + wo > 0:
            pct = w / (w + wo) * 100
            ax.text(w + wo + 2, i, f"{pct:.0f}%", va="center", fontsize=9, fontweight="bold")

    # 7b: By continent
    ax = fig.add_subplot(gs[0, 1])
    continents = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania", "Antarctica"]
    cont_with = []
    cont_without = []
    for cont in continents:
        sub = merged[(merged["continent"] == cont) & (merged["polity_type"] != "region")]
        cont_with.append(sub["has_geometry"].sum())
        cont_without.append(len(sub) - sub["has_geometry"].sum())

    x = np.arange(len(continents))
    ax.barh(x, cont_with, color="#4CAF50", edgecolor="white")
    ax.barh(x, cont_without, left=cont_with, color="#F44336", edgecolor="white")
    ax.set_yticks(x)
    ax.set_yticklabels(continents, fontsize=9)
    ax.set_xlabel("Count", fontsize=10)
    ax.set_title("Polygon Coverage by Continent", fontsize=12, fontweight="bold")
    for i, (w, wo) in enumerate(zip(cont_with, cont_without)):
        if w + wo > 0:
            pct = w / (w + wo) * 100
            ax.text(w + wo + 1, i, f"{pct:.0f}%", va="center", fontsize=9, fontweight="bold")

    # 7c: By decade
    ax = fig.add_subplot(gs[0, 2])
    decades = range(1850, 2030, 10)
    dec_total = []
    dec_with = []
    nr_merged = merged[merged["polity_type"] != "region"]
    for d in decades:
        active = nr_merged[(nr_merged["start_year"] <= d) & (nr_merged["end_year"] >= d)]
        dec_total.append(len(active))
        dec_with.append(active["has_geometry"].sum())

    ax.fill_between(list(decades), dec_total, color="#E0E0E0", label="Total active")
    ax.fill_between(list(decades), dec_with, color="#4CAF50", alpha=0.7, label="With polygon")
    ax.set_xlabel("Year", fontsize=10)
    ax.set_ylabel("Active Polities", fontsize=10)
    ax.set_title("Polygon Coverage Over Time", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)

    # 7d: Polygon source breakdown
    ax = fig.add_subplot(gs[1, 0])
    source_counts = polities["polygon_source"].value_counts()
    colors_src = plt.cm.Set3(np.linspace(0, 1, len(source_counts)))
    wedges, texts = ax.pie(source_counts.values, colors=colors_src, startangle=90)
    ax.legend(wedges, [f"{s} ({c})" for s, c in zip(source_counts.index, source_counts.values)],
              loc="center left", bbox_to_anchor=(-0.3, 0.5), fontsize=7)
    ax.set_title("Polygon Source Distribution", fontsize=12, fontweight="bold")

    # 7e: Subnational tier distribution
    ax = fig.add_subplot(gs[1, 1])
    tier_counts = sub_report["quality_tier"].value_counts().sort_index()
    tier_labels = {1: "Tier 1\nHistorical", 2: "Tier 2\nGood proxy", 3: "Tier 3\nAcceptable", 4: "Tier 4\nNo proxy"}
    bars = ax.bar([tier_labels.get(t, str(t)) for t in tier_counts.index],
                  tier_counts.values,
                  color=[TIER_COLORS.get(t, "#9E9E9E") for t in tier_counts.index],
                  edgecolor="white", linewidth=1.5)
    for bar, v in zip(bars, tier_counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                str(v), ha="center", fontweight="bold", fontsize=11)
    ax.set_ylabel("Subnational Regions", fontsize=10)
    ax.set_title("Subnational Polygon Quality Tiers", fontsize=12, fontweight="bold")

    # 7f: Excel region coverage funnel
    ax = fig.add_subplot(gs[1, 2])
    total_excel = 442  # total unique regions
    matched_direct = 299
    matched_sub = 110
    aggregate = 33
    with_poly_direct = 298
    with_poly_sub = 91
    no_poly = 20

    categories = ["Total Excel\nregions", "Matched\n(direct)", "Subnational", "Aggregate\n(no poly needed)",
                  "With polygon\n(direct)", "With polygon\n(subnational)", "Missing\npolygon"]
    values = [total_excel, matched_direct, matched_sub, aggregate,
              with_poly_direct, with_poly_sub, no_poly]
    colors_f = ["#90CAF9", "#4CAF50", "#FF9800", "#CE93D8", "#2E7D32", "#E65100", "#F44336"]
    bars = ax.barh(range(len(categories)), values, color=colors_f, edgecolor="white")
    ax.set_yticks(range(len(categories)))
    ax.set_yticklabels(categories, fontsize=9)
    ax.invert_yaxis()
    for bar, v in zip(bars, values):
        ax.text(bar.get_width() + 3, bar.get_y() + bar.get_height() / 2,
                str(v), va="center", fontweight="bold", fontsize=10)
    ax.set_xlabel("Count", fontsize=10)
    ax.set_title("Excel Region Coverage Pipeline", fontsize=12, fontweight="bold")

    plt.suptitle("WHEP Polities Database — Polygon Coverage Analysis", fontsize=15, fontweight="bold", y=1.02)
    plt.savefig(f"{PLOT_DIR}/07_polygon_coverage.png", dpi=150, bbox_inches="tight")
    plt.close()


# =====================================================================
# PLOT 8: World Maps — Temporal Snapshots
# =====================================================================
def plot_world_maps():
    print("  Plot 8: World maps (temporal snapshots)...")
    fig, axes = plt.subplots(2, 3, figsize=(24, 14))

    snapshot_years = [1850, 1900, 1920, 1945, 1970, 2025]

    for idx, (yr, ax) in enumerate(zip(snapshot_years, axes.flat)):
        # Filter active polities
        active = polygons[
            (polygons["start_year"] <= yr) & (polygons["end_year"] >= yr)
        ]

        # Draw by type
        drawn = False
        for ptype in ["colonial", "mandate", "puppet", "dependency", "historical", "sovereign", "disputed", "aggregate"]:
            subset = active[active["polity_type"] == ptype]
            if len(subset) > 0:
                subset.plot(ax=ax, color=TYPE_COLORS[ptype], edgecolor="black",
                            linewidth=0.15, alpha=0.7)
                drawn = True

        ax.set_xlim(-180, 180)
        ax.set_ylim(-60, 85)
        n_active = len(active)
        ax.set_title(f"{yr}  ({n_active} polities)", fontsize=12, fontweight="bold")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_facecolor("#F0F8FF")

    # Legend
    patches = [mpatches.Patch(color=TYPE_COLORS[t], label=t) for t in
               ["sovereign", "colonial", "dependency", "mandate", "historical", "puppet", "disputed", "aggregate"]]
    fig.legend(handles=patches, loc="lower center", ncol=8, fontsize=10,
               bbox_to_anchor=(0.5, -0.02))

    plt.suptitle("WHEP Polities — World Map Snapshots by Year", fontsize=16, fontweight="bold")
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    plt.savefig(f"{PLOT_DIR}/08_world_map_snapshots.png", dpi=150, bbox_inches="tight")
    plt.close()


# =====================================================================
# PLOT 9: Subnational Polygons Map
# =====================================================================
def plot_subnational_map():
    print("  Plot 9: Subnational polygon map...")
    fig, axes = plt.subplots(1, 2, figsize=(20, 8))

    # Left: all subnational polygons colored by tier
    ax = axes[0]
    for tier in [1, 2, 3]:
        subset = subnational_gdf[subnational_gdf["quality_tier"] == tier]
        if len(subset) > 0:
            subset.plot(ax=ax, color=TIER_COLORS[tier], edgecolor="black",
                        linewidth=0.3, alpha=0.7, label=f"Tier {tier}")
    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 85)
    ax.set_title(f"Subnational Polygons by Quality Tier (n={len(subnational_gdf)})",
                 fontsize=12, fontweight="bold")
    ax.legend(loc="lower left", fontsize=10)
    ax.set_facecolor("#F0F8FF")
    ax.set_xticks([])
    ax.set_yticks([])

    # Right: zoom into key regions
    ax = axes[1]
    # Show West Africa and SE Asia zooms
    for tier in [1, 2, 3]:
        subset = subnational_gdf[subnational_gdf["quality_tier"] == tier]
        if len(subset) > 0:
            subset.plot(ax=ax, color=TIER_COLORS[tier], edgecolor="black",
                        linewidth=0.5, alpha=0.7, label=f"Tier {tier}")

    # Focus on Africa
    ax.set_xlim(-20, 55)
    ax.set_ylim(-35, 40)
    ax.set_title("Subnational Polygons — Africa Detail", fontsize=12, fontweight="bold")
    ax.legend(loc="lower left", fontsize=10)
    ax.set_facecolor("#F0F8FF")

    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/09_subnational_map.png", dpi=150, bbox_inches="tight")
    plt.close()


# =====================================================================
# PLOT 10: Data Quality Diagnostics
# =====================================================================
def plot_data_quality():
    print("  Plot 10: Data quality diagnostics...")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # 10a: Verification status
    ax = axes[0, 0]
    vstatus = polities["verification_status"].apply(
        lambda x: "FIXED" if str(x).startswith("FIXED") else str(x)
    ).value_counts()
    colors_v = {"VERIFIED": "#4CAF50", "UNVERIFIED": "#FF9800", "REGION": "#9E9E9E", "FIXED": "#2196F3"}
    bars = ax.bar(vstatus.index, vstatus.values,
                  color=[colors_v.get(s, "#9E9E9E") for s in vstatus.index],
                  edgecolor="white", linewidth=1.5)
    for bar, v in zip(bars, vstatus.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3,
                str(v), ha="center", fontweight="bold", fontsize=11)
    ax.set_ylabel("Count", fontsize=11)
    ax.set_title("Verification Status", fontsize=13, fontweight="bold")

    # 10b: ISO code coverage by type
    ax = axes[0, 1]
    types_order = ["sovereign", "historical", "colonial", "dependency", "mandate", "aggregate"]
    iso_have = []
    iso_miss = []
    for ptype in types_order:
        sub = polities[polities["polity_type"] == ptype]
        have = sub["iso3_code"].notna().sum()
        iso_have.append(have)
        iso_miss.append(len(sub) - have)
    x = np.arange(len(types_order))
    ax.bar(x, iso_have, color="#4CAF50", label="Has ISO3", edgecolor="white")
    ax.bar(x, iso_miss, bottom=iso_have, color="#FF9800", label="No ISO3", edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels(types_order, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("Count", fontsize=11)
    ax.set_title("ISO3 Code Coverage by Type", fontsize=13, fontweight="bold")
    ax.legend(fontsize=9)

    # 10c: Temporal gap check — look for same-prefix overlaps
    ax = axes[1, 0]
    prefixes = polities["polity_code"].str.split("-").str[0]
    polities_with_prefix = polities.copy()
    polities_with_prefix["prefix"] = prefixes

    overlap_count = 0
    gap_count = 0
    gap_years_total = 0
    for prefix, group in polities_with_prefix.groupby("prefix"):
        if len(group) < 2:
            continue
        sorted_g = group.sort_values("start_year")
        for i in range(len(sorted_g) - 1):
            end_i = sorted_g.iloc[i]["end_year"]
            start_next = sorted_g.iloc[i + 1]["start_year"]
            if end_i >= start_next:
                overlap_count += 1
            elif end_i + 1 < start_next:
                gap_count += 1
                gap_years_total += (start_next - end_i - 1)

    categories = ["Clean\nsuccessions", "Overlapping\nperiods", "Temporal\ngaps"]
    total_pairs = sum(max(0, len(g) - 1) for _, g in polities_with_prefix.groupby("prefix") if len(g) > 1)
    clean = total_pairs - overlap_count - gap_count
    values = [clean, overlap_count, gap_count]
    colors_q = ["#4CAF50", "#F44336", "#FF9800"]
    bars = ax.bar(categories, values, color=colors_q, edgecolor="white", linewidth=1.5)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                str(v), ha="center", fontweight="bold", fontsize=11)
    ax.set_ylabel("Count", fontsize=11)
    ax.set_title(f"Temporal Continuity Check\n(same-prefix pairs: {total_pairs})", fontsize=12, fontweight="bold")

    # 10d: COW code coverage
    ax = axes[1, 1]
    cow_have = non_region["cow_code"].notna().sum()
    cow_miss = len(non_region) - cow_have
    iso_have_nr = non_region["iso3_code"].notna().sum()
    iso_miss_nr = len(non_region) - iso_have_nr
    both = ((non_region["cow_code"].notna()) & (non_region["iso3_code"].notna())).sum()
    neither = ((non_region["cow_code"].isna()) & (non_region["iso3_code"].isna())).sum()

    labels = ["Has both\nCOW+ISO", "COW only", "ISO only", "Neither"]
    cow_only = cow_have - both
    iso_only = iso_have_nr - both
    vals = [both, cow_only, iso_only, neither]
    colors_c = ["#4CAF50", "#2196F3", "#FF9800", "#F44336"]
    bars = ax.bar(labels, vals, color=colors_c, edgecolor="white", linewidth=1.5)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                str(v), ha="center", fontweight="bold", fontsize=11)
    ax.set_ylabel("Count", fontsize=11)
    ax.set_title(f"Code Coverage (n={len(non_region)} non-region polities)", fontsize=12, fontweight="bold")

    plt.suptitle("WHEP Polities Database — Data Quality Diagnostics", fontsize=15, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(f"{PLOT_DIR}/10_data_quality.png", dpi=150, bbox_inches="tight")
    plt.close()


# =====================================================================
# PLOT 11: Colonial Empires Timeline
# =====================================================================
def plot_colonial_empires():
    print("  Plot 11: Colonial empires timeline...")
    fig, ax = plt.subplots(figsize=(18, 10))

    # Identify colonial powers from prefix patterns in colonial/dependency entries
    colonial_entries = non_region[non_region["polity_type"].isin(["colonial", "dependency", "mandate"])]

    # Group by colonial power (based on polity name prefix)
    power_keywords = {
        "British": ["British", "UK:", "Anglo"],
        "French": ["French"],
        "Dutch": ["Dutch", "Netherlands"],
        "Portuguese": ["Portuguese"],
        "Spanish": ["Spanish"],
        "Italian": ["Italian"],
        "German": ["German"],
        "Belgian": ["Belgian"],
        "Japanese": ["Japanese", "Japan:"],
        "American": ["USA:", "American"],
        "Danish": ["Danish", "Denmark:"],
    }

    power_colors = {
        "British": "#F44336", "French": "#2196F3", "Dutch": "#FF9800",
        "Portuguese": "#4CAF50", "Spanish": "#FFEB3B", "Italian": "#9C27B0",
        "German": "#795548", "Belgian": "#607D8B", "Japanese": "#E91E63",
        "American": "#3F51B5", "Danish": "#009688",
    }

    y_offset = 0
    yticks = []
    ylabels = []

    for power, keywords in power_keywords.items():
        entries = colonial_entries[colonial_entries["polity_name"].apply(
            lambda n: any(k.lower() in str(n).lower() for k in keywords)
        )]
        if len(entries) == 0:
            continue

        entries = entries.sort_values("start_year")
        for _, row in entries.iterrows():
            ax.barh(y_offset, row["end_year"] - row["start_year"],
                    left=row["start_year"], height=0.7,
                    color=power_colors.get(power, "#9E9E9E"), alpha=0.7,
                    edgecolor="white", linewidth=0.3)
            y_offset += 1

        # Power label
        mid_y = y_offset - len(entries) / 2
        yticks.append(mid_y)
        ylabels.append(f"{power} ({len(entries)})")
        y_offset += 1  # gap

    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels, fontsize=10)
    ax.set_xlabel("Year", fontsize=12)
    ax.set_xlim(1800, 2030)
    ax.invert_yaxis()
    ax.set_title("Colonial/Dependency/Mandate Entities by Imperial Power", fontsize=14, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)

    # Mark key events
    for yr, label in {1884: "Berlin\nConference", 1918: "WWI end", 1945: "WWII end", 1960: "Year of\nAfrica"}.items():
        ax.axvline(yr, color="black", linestyle="--", alpha=0.5)
        ax.text(yr, -1.5, label, ha="center", fontsize=8, alpha=0.7)

    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/11_colonial_empires.png", dpi=150, bbox_inches="tight")
    plt.close()


# =====================================================================
# PLOT 12: Verification & Consistency Deep Dive
# =====================================================================
def plot_consistency_checks():
    print("  Plot 12: Consistency checks...")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # 12a: Start year distribution by continent
    ax = axes[0, 0]
    continents = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania"]
    for cont in continents:
        subset = non_region[non_region["continent"] == cont]
        ax.hist(subset["start_year"], bins=30, alpha=0.4, color=CONTINENT_COLORS[cont], label=cont)
    ax.set_xlabel("Start Year", fontsize=11)
    ax.set_ylabel("Count", fontsize=11)
    ax.set_title("Polity Start Year Distribution by Continent", fontsize=12, fontweight="bold")
    ax.legend(fontsize=8)

    # 12b: Predecessor/successor chain completeness
    ax = axes[0, 1]
    has_pred = non_region["predecessor"].notna().sum()
    has_succ = non_region["successor"].notna().sum()
    has_both = ((non_region["predecessor"].notna()) & (non_region["successor"].notna())).sum()
    has_neither = ((non_region["predecessor"].isna()) & (non_region["successor"].isna())).sum()

    labels = ["Has\npredecessor", "Has\nsuccessor", "Has both", "Has neither"]
    vals = [has_pred, has_succ, has_both, has_neither]
    colors_ps = ["#2196F3", "#FF9800", "#4CAF50", "#9E9E9E"]
    bars = ax.bar(labels, vals, color=colors_ps, edgecolor="white", linewidth=1.5)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                str(v), ha="center", fontweight="bold", fontsize=11)
    ax.set_ylabel("Count", fontsize=11)
    ax.set_title("Predecessor/Successor Chain Coverage", fontsize=12, fontweight="bold")

    # 12c: Polity code prefix reuse (same prefix = continuity chain)
    ax = axes[1, 0]
    prefixes = non_region["polity_code"].str.split("-").str[0]
    prefix_counts = Counter(prefixes)
    reuse_dist = Counter(prefix_counts.values())
    x_vals = sorted(reuse_dist.keys())
    y_vals = [reuse_dist[x] for x in x_vals]
    ax.bar(x_vals, y_vals, color="#2196F3", edgecolor="white")
    ax.set_xlabel("Entries per prefix", fontsize=11)
    ax.set_ylabel("Number of prefixes", fontsize=11)
    ax.set_title("Polity Code Prefix Reuse\n(>1 = territorial change chain)", fontsize=12, fontweight="bold")
    for x, y in zip(x_vals, y_vals):
        ax.text(x, y + 1, str(y), ha="center", fontsize=9)

    # 12d: Polygon vs no-polygon by start year
    ax = axes[1, 1]
    merged = polities.merge(poly_report[["polity_code", "has_geometry"]], on="polity_code", how="left")
    merged["has_geometry"] = merged["has_geometry"].fillna(False)
    nr_merged = merged[merged["polity_type"] != "region"]

    bins = np.arange(1800, 2030, 10)
    with_geo = nr_merged[nr_merged["has_geometry"]]["start_year"]
    without_geo = nr_merged[~nr_merged["has_geometry"]]["start_year"]
    ax.hist([with_geo, without_geo], bins=bins, stacked=True,
            color=["#4CAF50", "#F44336"], label=["With polygon", "Without polygon"],
            edgecolor="white", linewidth=0.3)
    ax.set_xlabel("Start Year", fontsize=11)
    ax.set_ylabel("Count", fontsize=11)
    ax.set_title("Polygon Availability by Start Year", fontsize=12, fontweight="bold")
    ax.legend(fontsize=10)

    plt.suptitle("WHEP Polities Database — Consistency & Completeness", fontsize=15, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(f"{PLOT_DIR}/12_consistency_checks.png", dpi=150, bbox_inches="tight")
    plt.close()


# =====================================================================
# PLOT 13: Excel Region Matching Detail
# =====================================================================
def plot_excel_matching():
    print("  Plot 13: Excel region matching...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 7))

    # 13a: Match status breakdown
    ax = axes[0]
    status_counts = matching["match_status"].value_counts()
    colors_m = {"matched": "#4CAF50", "subnational": "#FF9800", "aggregate": "#9C27B0", "unmatched": "#F44336"}
    ax.pie(status_counts.values, labels=status_counts.index, autopct="%1.1f%%",
           colors=[colors_m.get(s, "#9E9E9E") for s in status_counts.index],
           startangle=90, pctdistance=0.85)
    ax.set_title(f"Excel Region Match Status\n(n={len(matching)})", fontsize=12, fontweight="bold")

    # 13b: Subnational by parent polity (top 15)
    ax = axes[1]
    sub_parents = matching[matching["match_status"] == "subnational"]["parent_polity_code"].value_counts().head(15)
    ax.barh(range(len(sub_parents)), sub_parents.values, color="#FF9800", edgecolor="white")
    ax.set_yticks(range(len(sub_parents)))
    ax.set_yticklabels(sub_parents.index, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Sub-regions", fontsize=11)
    ax.set_title("Top 15 Parent Polities\n(subnational regions)", fontsize=12, fontweight="bold")

    # 13c: Polygon coverage by match status
    ax = axes[2]
    for status in ["matched", "subnational"]:
        sub = excel_cov[excel_cov["match_status"] == status]
        has = sub["has_polygon"].sum()
        no = len(sub) - has
        ax.bar(status, has, color="#4CAF50", label="With polygon" if status == "matched" else "")
        ax.bar(status, no, bottom=has, color="#F44336", label="Without polygon" if status == "matched" else "")
        ax.text(status, has + no + 2, f"{has}/{has+no}\n({has/(has+no)*100:.0f}%)",
                ha="center", fontsize=10, fontweight="bold")

    ax.set_ylabel("Regions", fontsize=11)
    ax.set_title("Polygon Coverage by Match Type", fontsize=12, fontweight="bold")
    ax.legend(fontsize=10)

    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/13_excel_matching.png", dpi=150, bbox_inches="tight")
    plt.close()


# =====================================================================
# RUN ALL VALIDATIONS
# =====================================================================
def run_validations():
    """Run data quality validations and print results."""
    print("\n" + "=" * 70)
    print("  DATA QUALITY VALIDATION REPORT")
    print("=" * 70)

    issues = []

    # 1. Check for duplicate polity codes
    dupes = polities[polities["polity_code"].duplicated()]
    if len(dupes) > 0:
        issues.append(f"CRITICAL: {len(dupes)} duplicate polity codes found")
        for _, d in dupes.iterrows():
            print(f"  DUPE: {d['polity_code']} - {d['polity_name']}")
    else:
        print("  [PASS] No duplicate polity codes")

    # 2. Check for duplicate ISO codes (same ISO, overlapping time, DIFFERENT prefix)
    iso_polities = non_region[non_region["iso3_code"].notna()].copy()
    iso_polities["prefix"] = iso_polities["polity_code"].str.split("-").str[0]
    iso_overlaps_same_prefix = 0
    iso_overlaps_diff_prefix = []
    for iso, group in iso_polities.groupby("iso3_code"):
        if len(group) < 2:
            continue
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a = group.iloc[i]
                b = group.iloc[j]
                if a["start_year"] <= b["end_year"] and b["start_year"] <= a["end_year"]:
                    if a["prefix"] == b["prefix"]:
                        iso_overlaps_same_prefix += 1
                    else:
                        iso_overlaps_diff_prefix.append(
                            (iso, a["polity_code"], b["polity_code"],
                             max(a["start_year"], b["start_year"]),
                             min(a["end_year"], b["end_year"])))

    print(f"  [INFO] {iso_overlaps_same_prefix} same-prefix ISO3 temporal overlaps (expected: territorial period chains)")
    if iso_overlaps_diff_prefix:
        print(f"  [WARN] {len(iso_overlaps_diff_prefix)} cross-prefix ISO3 temporal overlaps:")
        for iso, a, b, s, e in iso_overlaps_diff_prefix[:15]:
            print(f"    {iso}: {a} <-> {b} ({s}-{e})")
    else:
        print("  [PASS] No cross-prefix ISO3 temporal overlaps")

    # 3. Check year consistency
    bad_years = polities[polities["start_year"] > polities["end_year"]]
    if len(bad_years) > 0:
        issues.append(f"CRITICAL: {len(bad_years)} polities with start_year > end_year")
    else:
        print("  [PASS] All start_year <= end_year")

    bad_duration = polities[polities["duration_years"] != (polities["end_year"] - polities["start_year"] + 1)]
    if len(bad_duration) > 0:
        issues.append(f"WARN: {len(bad_duration)} polities with incorrect duration_years")
    else:
        print("  [PASS] All duration_years are consistent")

    # 4. Check polygon report matches polities
    poly_codes = set(poly_report["polity_code"])
    pol_codes = set(polities["polity_code"])
    missing_in_poly = pol_codes - poly_codes
    extra_in_poly = poly_codes - pol_codes
    if missing_in_poly:
        print(f"  [WARN] {len(missing_in_poly)} polities missing from polygon report")
    else:
        print("  [PASS] All polities present in polygon report")
    if extra_in_poly:
        print(f"  [WARN] {len(extra_in_poly)} extra entries in polygon report")

    # 5. Check subnational parent codes exist
    sub_parents = set(sub_report["parent_code"].dropna())
    missing_parents = sub_parents - pol_codes
    if missing_parents:
        print(f"  [WARN] {len(missing_parents)} subnational parent codes not in database: {missing_parents}")
    else:
        print("  [PASS] All subnational parent codes exist in database")

    # 6. Check COW coverage
    cow_code_set = set(int(c) for c in cow["cow_code"])
    our_cow = set(int(float(c)) for c in polities["cow_code"].dropna())
    cow_missing = cow_code_set - our_cow
    if cow_missing:
        cow_names = [cow[cow["cow_code"] == c]["cow_name"].values[0]
                     for c in sorted(list(cow_missing))[:5]]
        print(f"  [INFO] {len(cow_missing)} COW codes not in database (sample: {cow_names})")
    else:
        print("  [PASS] All COW state system codes covered")

    # 7. Check for polities ending at 2025 that shouldn't
    suspect_2025 = non_region[
        (non_region["end_year"] == 2025) &
        (non_region["polity_type"] == "historical")
    ]
    if len(suspect_2025) > 0:
        print(f"  [WARN] {len(suspect_2025)} historical polities ending at 2025 (should have dissolved):")
        for _, s in suspect_2025.head(5).iterrows():
            print(f"    {s['polity_code']}: {s['polity_name']}")
    else:
        print("  [PASS] No historical polities ending at 2025")

    # 8. Check decolonization events coverage
    decol_iso = set(str(i) for i in decol["iso3"].dropna())
    our_iso = set(str(i) for i in polities["iso3_code"].dropna())
    decol_covered = len(decol_iso & our_iso)
    print(f"  [INFO] Decolonization events covered: {decol_covered}/{len(decol_iso)} ({decol_covered/len(decol_iso)*100:.1f}%)")

    # Summary
    print(f"\n{'=' * 70}")
    print(f"  SUMMARY: {len(issues)} critical issues, {len(polities)} total polities")
    if not issues:
        print("  All critical checks passed.")
    else:
        for issue in issues:
            print(f"  {issue}")
    print(f"{'=' * 70}")


# =====================================================================
# MAIN
# =====================================================================
def main():
    print("\nGenerating plots...")

    plot_formation_dissolution()
    plot_active_polities()
    plot_type_distribution()
    plot_duration_distribution()
    plot_data_source_coverage()
    plot_cow_crossvalidation()
    plot_polygon_coverage()
    plot_world_maps()
    plot_subnational_map()
    plot_data_quality()
    plot_colonial_empires()
    plot_consistency_checks()
    plot_excel_matching()

    run_validations()

    print(f"\nAll plots saved to {PLOT_DIR}/")
    print("Files generated:")
    for f in sorted(os.listdir(PLOT_DIR)):
        if f.endswith(".png"):
            size = os.path.getsize(f"{PLOT_DIR}/{f}") / 1024
            print(f"  {f:50s} {size:7.1f} KB")


if __name__ == "__main__":
    main()
