#!/usr/bin/env python3
"""
Temporal evolution analysis of the WHEP polities database.

Generates detailed visualizations showing how the political world changes
over time, focusing on key transition periods and decolonization waves.

Produces:
  - data/analysis/plots/temporal_*.png (6 plots)
  - Console analysis
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

polities = pd.read_csv(f"{BASE}/data/final/polities_database.csv")
non_region = polities[polities["polity_type"] != "region"]
polygons = gpd.read_file(f"{BASE}/data/geodata/polities_polygons.gpkg")

TYPE_COLORS = {
    "sovereign": "#2196F3", "historical": "#9E9E9E", "colonial": "#F44336",
    "dependency": "#FF9800", "aggregate": "#9C27B0", "mandate": "#4CAF50",
    "disputed": "#FFEB3B", "puppet": "#795548"
}

print("=" * 70)
print("TEMPORAL EVOLUTION ANALYSIS")
print("=" * 70)

# Merge type info into polygons
poly_meta = polities[["polity_code", "polity_type", "continent", "polity_name"]].copy()
poly_meta.columns = ["polity_code", "p_type", "p_continent", "p_name"]
poly_merged = polygons.merge(poly_meta, on="polity_code", how="left")

# =====================================================================
# PLOT 1: World Maps at Key Historical Moments (6 snapshots)
# =====================================================================
print("\n─── Plot 1: World maps at key moments ───")

snapshot_years = [1800, 1880, 1914, 1945, 1970, 2025]
snapshot_labels = [
    "1800: Napoleonic Era",
    "1880: Age of Empire",
    "1914: Eve of WWI",
    "1945: Post-WWII",
    "1970: Decolonization Peak",
    "2025: Modern World"
]

fig, axes = plt.subplots(2, 3, figsize=(24, 14))

for ax, year, label in zip(axes.flat, snapshot_years, snapshot_labels):
    active = poly_merged[
        (poly_merged["start_year"] <= year) & (poly_merged["end_year"] >= year)
    ]

    # Plot by type
    for ptype in ["colonial", "mandate", "puppet", "dependency", "historical",
                  "disputed", "sovereign", "aggregate"]:
        subset = active[active["p_type"] == ptype]
        if len(subset) > 0:
            subset.plot(ax=ax, color=TYPE_COLORS.get(ptype, "#999"),
                       alpha=0.6, edgecolor="black", linewidth=0.2)

    # Count stats
    n_sov = (active["p_type"] == "sovereign").sum()
    n_col = (active["p_type"].isin(["colonial", "mandate", "puppet"])).sum()
    n_hist = (active["p_type"] == "historical").sum()

    ax.set_title(f"{label}\n({n_sov} sov, {n_col} col, {n_hist} hist)",
                 fontsize=10, fontweight="bold")
    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 85)
    ax.set_xticks([])
    ax.set_yticks([])

# Legend
legend_elements = [mpatches.Patch(facecolor=c, label=t)
                   for t, c in TYPE_COLORS.items() if t not in ("puppet", "disputed")]
fig.legend(handles=legend_elements, loc="lower center", fontsize=9, ncol=6,
           bbox_to_anchor=(0.5, -0.02))

fig.suptitle("WHEP Polities Database — Political World at Key Moments",
             fontsize=16, fontweight="bold")
plt.tight_layout(rect=[0, 0.03, 1, 0.97])
plt.savefig(f"{PLOT_DIR}/temporal_01_world_snapshots.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 1 saved")


# =====================================================================
# PLOT 2: State Formation and Dissolution Rates
# =====================================================================
print("\n─── Plot 2: Formation/dissolution rates ───")

fig, axes = plt.subplots(2, 1, figsize=(20, 10), sharex=True)

years = np.arange(1800, 2026)

# Formations (start_year)
formations = non_region.groupby("start_year").size()
# Dissolutions (end_year, excluding 2025 = still active)
dissolutions = non_region[non_region["end_year"] < 2025].groupby("end_year").size()

# Smooth with 5-year rolling window
form_series = pd.Series(0, index=years)
for yr, count in formations.items():
    if yr in form_series.index:
        form_series[yr] = count
diss_series = pd.Series(0, index=years)
for yr, count in dissolutions.items():
    if yr in diss_series.index:
        diss_series[yr] = count

form_smooth = form_series.rolling(5, center=True, min_periods=1).mean()
diss_smooth = diss_series.rolling(5, center=True, min_periods=1).mean()

# By type
ax = axes[0]
for ptype in ["sovereign", "historical", "colonial", "dependency", "mandate"]:
    subset = non_region[non_region["polity_type"] == ptype]
    type_form = subset.groupby("start_year").size()
    type_series = pd.Series(0.0, index=years)
    for yr, count in type_form.items():
        if yr in type_series.index:
            type_series[yr] = count
    smoothed = type_series.rolling(5, center=True, min_periods=1).mean()
    ax.plot(years, smoothed, color=TYPE_COLORS[ptype], label=ptype, linewidth=1.5)

ax.fill_between(years, form_smooth, alpha=0.1, color="blue")
ax.set_ylabel("New Polities (5yr avg)")
ax.set_title("A) Polity Formation Rate by Type", fontweight="bold")
ax.legend(fontsize=8, ncol=5)

# Key events
events = [(1861, "Italy"), (1871, "Germany"), (1918, "WWI end"),
          (1945, "WWII end"), (1960, "Year of\nAfrica"), (1991, "USSR")]
for yr, label in events:
    ax.axvline(yr, color="gray", linestyle=":", alpha=0.5)
    ax.text(yr, ax.get_ylim()[1] * 0.95, label, fontsize=7, ha="center", va="top")

# Net change
ax = axes[1]
net = form_series - diss_series
net_smooth = net.rolling(5, center=True, min_periods=1).mean()
colors = ["#4CAF50" if v >= 0 else "#F44336" for v in net_smooth]
ax.bar(years, net_smooth, color=colors, alpha=0.7, width=1)
ax.axhline(0, color="black", linewidth=0.5)
ax.set_ylabel("Net Change (5yr avg)")
ax.set_xlabel("Year")
ax.set_title("B) Net Polity Change (formations - dissolutions)", fontweight="bold")

for yr, label in events:
    ax.axvline(yr, color="gray", linestyle=":", alpha=0.5)

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/temporal_02_formation_rates.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 2 saved")


# =====================================================================
# PLOT 3: Decolonization Wave Analysis
# =====================================================================
print("\n─── Plot 3: Decolonization waves ───")

colonial_types = non_region[non_region["polity_type"].isin(["colonial", "mandate"])]
sovereign_born = non_region[(non_region["polity_type"] == "sovereign") &
                            (non_region["start_year"] > 1945)]

fig, axes = plt.subplots(1, 3, figsize=(20, 7))

# A: Colonial entities ending by decade
ax = axes[0]
colonial_ends = colonial_types[colonial_types["end_year"] < 2025]
decades = list(range(1940, 2020, 10))
by_continent = {}
for cont in ["Africa", "Asia", "Oceania", "North America", "South America"]:
    by_continent[cont] = []
    subset = colonial_ends[colonial_ends["continent"] == cont]
    for d in decades:
        count = ((subset["end_year"] >= d) & (subset["end_year"] < d + 10)).sum()
        by_continent[cont].append(count)

x = np.arange(len(decades))
bottom = np.zeros(len(decades))
cont_colors = {"Africa": "#F44336", "Asia": "#FF9800", "Oceania": "#2196F3",
               "North America": "#4CAF50", "South America": "#9C27B0"}
for cont, counts in by_continent.items():
    ax.bar(x, counts, bottom=bottom, color=cont_colors.get(cont, "#999"),
           label=cont, alpha=0.7)
    bottom += np.array(counts)

ax.set_xticks(x)
ax.set_xticklabels([str(d) + "s" for d in decades], fontsize=9)
ax.set_ylabel("Colonial Entities Ending")
ax.set_title("A) Colonial Entity Dissolution by Decade", fontweight="bold")
ax.legend(fontsize=7)

# B: New sovereign states by decade (post-1945)
ax = axes[1]
sov_decades = list(range(1940, 2030, 10))
by_continent_sov = {}
for cont in ["Africa", "Asia", "Europe", "Oceania", "North America", "South America"]:
    by_continent_sov[cont] = []
    subset = sovereign_born[sovereign_born["continent"] == cont]
    for d in sov_decades:
        count = ((subset["start_year"] >= d) & (subset["start_year"] < d + 10)).sum()
        by_continent_sov[cont].append(count)

x = np.arange(len(sov_decades))
bottom = np.zeros(len(sov_decades))
cont_colors["Europe"] = "#9E9E9E"
for cont, counts in by_continent_sov.items():
    if sum(counts) > 0:
        ax.bar(x, counts, bottom=bottom, color=cont_colors.get(cont, "#999"),
               label=cont, alpha=0.7)
        bottom += np.array(counts)

ax.set_xticks(x)
ax.set_xticklabels([str(d) + "s" for d in sov_decades], fontsize=9)
ax.set_ylabel("New Sovereign States")
ax.set_title("B) New Sovereign States by Decade", fontweight="bold")
ax.legend(fontsize=7)

# C: Timeline of decolonization (cumulative)
ax = axes[2]
years_range = np.arange(1945, 2026)
for cont in ["Africa", "Asia", "Oceania", "North America"]:
    sov_cont = sovereign_born[sovereign_born["continent"] == cont]
    cum = np.array([((sov_cont["start_year"] <= yr)).sum() for yr in years_range])
    ax.plot(years_range, cum, color=cont_colors.get(cont, "#999"), label=cont,
            linewidth=2)

ax.set_xlabel("Year")
ax.set_ylabel("Cumulative New States")
ax.set_title("C) Cumulative Post-WWII State Formation", fontweight="bold")
ax.legend(fontsize=8)

plt.suptitle("Decolonization Wave Analysis", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/temporal_03_decolonization.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 3 saved")


# =====================================================================
# PLOT 4: Continental Polity Count Trends
# =====================================================================
print("\n─── Plot 4: Continental trends ───")

fig, axes = plt.subplots(2, 3, figsize=(20, 12))
continents = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania"]

for ax, cont in zip(axes.flat, continents):
    cont_polities = non_region[non_region["continent"] == cont]
    years_range = np.arange(1800, 2026)

    for ptype in ["sovereign", "historical", "colonial", "dependency", "mandate"]:
        subset = cont_polities[cont_polities["polity_type"] == ptype]
        counts = np.array([((subset["start_year"] <= yr) &
                            (subset["end_year"] >= yr)).sum()
                           for yr in years_range])
        if counts.max() > 0:
            ax.plot(years_range, counts, color=TYPE_COLORS[ptype], label=ptype,
                    linewidth=1.5, alpha=0.8)

    ax.set_title(f"{cont} ({len(cont_polities)} total)", fontweight="bold")
    ax.set_xlim(1800, 2025)
    ax.set_ylabel("Active Count")
    ax.legend(fontsize=7, loc="upper left")

plt.suptitle("Active Polity Count by Continent and Type", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/temporal_04_continental_trends.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 4 saved")


# =====================================================================
# PLOT 5: Polity Lifespan Analysis
# =====================================================================
print("\n─── Plot 5: Lifespan analysis ───")

fig = plt.figure(figsize=(20, 12))
gs = GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.3)

# A: Longest-lived polities
ax = fig.add_subplot(gs[0, 0])
longest = non_region.nlargest(25, "duration_years")
y = np.arange(len(longest))
colors = [TYPE_COLORS.get(t, "#999") for t in longest["polity_type"]]
ax.barh(y, longest["duration_years"], color=colors, alpha=0.7)
ax.set_yticks(y)
ax.set_yticklabels([f"{row['polity_name'][:25]}" for _, row in longest.iterrows()],
                   fontsize=7)
ax.set_xlabel("Duration (years)")
ax.set_title("A) 25 Longest-Lived Polities", fontweight="bold")
ax.invert_yaxis()

# B: Shortest-lived polities (> 0 years)
ax = fig.add_subplot(gs[0, 1])
shortest = non_region[non_region["duration_years"] > 0].nsmallest(25, "duration_years")
y = np.arange(len(shortest))
colors = [TYPE_COLORS.get(t, "#999") for t in shortest["polity_type"]]
ax.barh(y, shortest["duration_years"], color=colors, alpha=0.7)
ax.set_yticks(y)
ax.set_yticklabels([f"{row['polity_name'][:25]}" for _, row in shortest.iterrows()],
                   fontsize=7)
ax.set_xlabel("Duration (years)")
ax.set_title("B) 25 Shortest-Lived Polities", fontweight="bold")
ax.invert_yaxis()

# C: Duration CDF by type
ax = fig.add_subplot(gs[0, 2])
for ptype in ["sovereign", "historical", "colonial", "dependency"]:
    subset = non_region[non_region["polity_type"] == ptype]
    sorted_dur = np.sort(subset["duration_years"])
    cdf = np.arange(1, len(sorted_dur) + 1) / len(sorted_dur)
    ax.plot(sorted_dur, cdf, color=TYPE_COLORS[ptype], label=ptype, linewidth=2)
ax.set_xlabel("Duration (years)")
ax.set_ylabel("Cumulative Fraction")
ax.set_title("C) Duration CDF by Type", fontweight="bold")
ax.legend(fontsize=8)
ax.grid(alpha=0.3)

# D: Start year vs duration scatter
ax = fig.add_subplot(gs[1, :2])
for ptype in ["sovereign", "historical", "colonial", "dependency"]:
    subset = non_region[non_region["polity_type"] == ptype]
    ax.scatter(subset["start_year"], subset["duration_years"],
              color=TYPE_COLORS[ptype], alpha=0.4, s=20, label=ptype)
ax.set_xlabel("Start Year")
ax.set_ylabel("Duration (years)")
ax.set_title("D) Polity Start Year vs Duration", fontweight="bold")
ax.legend(fontsize=8)
ax.set_xlim(1795, 2030)

# E: Active polity count over time (stacked by continent)
ax = fig.add_subplot(gs[1, 2])
years_range = np.arange(1800, 2026)
cont_order = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania"]
cont_colors_line = {"Africa": "#F44336", "Asia": "#FF9800", "Europe": "#2196F3",
                    "North America": "#4CAF50", "South America": "#9C27B0",
                    "Oceania": "#00BCD4"}

bottom = np.zeros(len(years_range))
for cont in cont_order:
    subset = non_region[non_region["continent"] == cont]
    counts = np.array([((subset["start_year"] <= yr) &
                        (subset["end_year"] >= yr)).sum()
                       for yr in years_range])
    ax.fill_between(years_range, bottom, bottom + counts,
                    color=cont_colors_line.get(cont, "#999"), alpha=0.6, label=cont)
    bottom += counts

ax.set_xlabel("Year")
ax.set_ylabel("Active Count")
ax.set_title("E) Total Active by Continent", fontweight="bold")
ax.legend(fontsize=7, loc="upper left")
ax.set_xlim(1800, 2025)

plt.suptitle("Polity Lifespan Analysis", fontsize=16, fontweight="bold")
plt.savefig(f"{PLOT_DIR}/temporal_05_lifespan.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 5 saved")


# =====================================================================
# PLOT 6: European Political Fragmentation/Consolidation
# =====================================================================
print("\n─── Plot 6: European state changes ───")

europe = non_region[non_region["continent"] == "Europe"]
fig, axes = plt.subplots(1, 3, figsize=(20, 7))

# A: Active European polities over time
ax = axes[0]
years_range = np.arange(1800, 2026)
for ptype in ["sovereign", "historical"]:
    subset = europe[europe["polity_type"] == ptype]
    counts = np.array([((subset["start_year"] <= yr) &
                        (subset["end_year"] >= yr)).sum()
                       for yr in years_range])
    ax.plot(years_range, counts, color=TYPE_COLORS[ptype], label=ptype, linewidth=2)

# Total
total = np.array([((europe["start_year"] <= yr) & (europe["end_year"] >= yr)).sum()
                  for yr in years_range])
ax.plot(years_range, total, color="black", label="total", linewidth=1, linestyle="--")

events = [(1815, "Vienna"), (1861, "Italy"), (1871, "Germany"), (1918, "WWI"),
          (1938, "Munich"), (1945, "WWII"), (1991, "USSR"), (1993, "Czech/Slovak")]
for yr, label in events:
    ax.axvline(yr, color="gray", linestyle=":", alpha=0.4)
    ax.text(yr, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 100,
            label, fontsize=6, ha="center", va="bottom", rotation=45)

ax.set_title("A) European Polities Over Time", fontweight="bold")
ax.set_ylabel("Count")
ax.legend(fontsize=8)

# B: German states detail
ax = axes[1]
german_keywords = ["German", "Prussia", "Bavaria", "Saxony", "Württemberg", "Baden",
                   "Hanover", "Hesse", "Mecklenburg", "Oldenburg", "Brunswick",
                   "Nassau", "Frankfurt", "Hamburg", "Bremen", "Lübeck",
                   "Saxe", "Anhalt", "Schwarzburg", "Reuss", "Lippe",
                   "Waldeck", "Schaumburg", "Hohenzollern", "Wolfenbuttel"]
german = europe[europe["polity_name"].apply(
    lambda x: any(kw.lower() in str(x).lower() for kw in german_keywords))]
german_count = np.array([((german["start_year"] <= yr) &
                           (german["end_year"] >= yr)).sum()
                          for yr in years_range])
ax.plot(years_range, german_count, color="#F44336", linewidth=2, label="German states")
ax.axvline(1871, color="black", linestyle="--", label="Unification 1871")
ax.fill_between(years_range, german_count, alpha=0.2, color="#F44336")
ax.set_title("B) German State Consolidation", fontweight="bold")
ax.set_ylabel("Active German Polities")
ax.legend(fontsize=8)

# C: Italian states detail
ax = axes[2]
italian_keywords = ["Italian", "Italy", "Sardinia", "Two Sicilies", "Papal",
                    "Tuscany", "Modena", "Parma", "Lucca", "Lombard", "Venice",
                    "San Marino", "Vatican"]
italian = europe[europe["polity_name"].apply(
    lambda x: any(kw.lower() in str(x).lower() for kw in italian_keywords))]
italian_count = np.array([((italian["start_year"] <= yr) &
                            (italian["end_year"] >= yr)).sum()
                           for yr in years_range])
ax.plot(years_range, italian_count, color="#4CAF50", linewidth=2, label="Italian states")
ax.axvline(1861, color="black", linestyle="--", label="Unification 1861")
ax.fill_between(years_range, italian_count, alpha=0.2, color="#4CAF50")
ax.set_title("C) Italian State Consolidation", fontweight="bold")
ax.set_ylabel("Active Italian Polities")
ax.legend(fontsize=8)

plt.suptitle("European Political Evolution", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/temporal_06_europe.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 6 saved")


# ── Console summary ──────────────────────────────────────────────────
print("\n" + "=" * 70)
print("TEMPORAL EVOLUTION SUMMARY")
print("=" * 70)

# Key stats
peak_year = years[np.argmax([((non_region["start_year"] <= yr) &
                               (non_region["end_year"] >= yr)).sum()
                              for yr in years])]
peak_count = max([((non_region["start_year"] <= yr) &
                    (non_region["end_year"] >= yr)).sum()
                   for yr in years])

print(f"Peak active polities: {peak_count} in {peak_year}")
print(f"Currently active (2025): {((non_region['start_year'] <= 2025) & (non_region['end_year'] >= 2025)).sum()}")
print(f"Formations: {len(non_region)} total")
print(f"  1800: {(non_region['start_year'] == 1800).sum()} (starting entities)")
print(f"  Peak formation year: {formations.idxmax()} ({formations.max()} new)")
print(f"  Post-1945 sovereign states: {len(sovereign_born)}")
print(f"Dissolutions: {len(non_region[non_region['end_year'] < 2025])}")

# Colonial analysis
n_colonial = len(non_region[non_region["polity_type"].isin(["colonial", "mandate"])])
n_colonial_ended = len(non_region[non_region["polity_type"].isin(["colonial", "mandate"]) &
                                   (non_region["end_year"] < 2025)])
print(f"\nColonial/mandate entities: {n_colonial}")
print(f"  Ended (decolonized): {n_colonial_ended}")
print(f"  Remaining: {n_colonial - n_colonial_ended}")

print("\n✓ Temporal evolution analysis complete")
print(f"  6 plots saved to {PLOT_DIR}/temporal_*.png")
