#!/usr/bin/env python3
"""
Analyze subnational polygon coverage for major countries.

Examines GADM admin-1 units for the world's largest countries and assesses
their suitability as WHEP polities. Generates comparison plots and reports.

Reads:
  - GADM admin-1 data (gadm36_levels.gpkg, level1)
  - WHEP polities database
  - Existing subnational report

Writes:
  - data/analysis/subnational_gadm_analysis.csv
  - data/analysis/plots/subnational_*.png
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

GADM_PATH = "/home/usuario/LandInG/gadm/gadm36_levels.gpkg"

# ── Load data ────────────────────────────────────────────────────────
print("Loading data...")
polities = pd.read_csv(f"{BASE}/data/final/polities_database.csv")
gadm1 = gpd.read_file(GADM_PATH, layer="level1")
gadm0 = gpd.read_file(GADM_PATH, layer="level0")

# Load existing subnational report
sub_report = pd.read_csv(f"{BASE}/data/analysis/subnational_report.csv")

print(f"  GADM admin-1: {len(gadm1)} units across {gadm1['GID_0'].nunique()} countries")
print(f"  Polities database: {len(polities)} entries")
print(f"  Existing subnational: {len(sub_report)} regions")

# ── Major countries to analyze ───────────────────────────────────────

COUNTRIES = {
    "USA": {"name": "United States", "n_expected": 50, "note": "50 states + DC"},
    "BRA": {"name": "Brazil", "n_expected": 27, "note": "26 states + DF"},
    "IND": {"name": "India", "n_expected": 36, "note": "28 states + 8 UTs"},
    "CHN": {"name": "China", "n_expected": 31, "note": "23 provinces + 4 muni + 5 AR"},
    "RUS": {"name": "Russia", "n_expected": 83, "note": "Federal subjects"},
    "AUS": {"name": "Australia", "n_expected": 8, "note": "6 states + 2 territories"},
    "CAN": {"name": "Canada", "n_expected": 13, "note": "10 provinces + 3 territories"},
    "MEX": {"name": "Mexico", "n_expected": 32, "note": "31 states + Mexico City"},
    "ARG": {"name": "Argentina", "n_expected": 24, "note": "23 provinces + CABA"},
    "IDN": {"name": "Indonesia", "n_expected": 33, "note": "34 provinces (pre-2022 GADM)"},
    "JPN": {"name": "Japan", "n_expected": 47, "note": "47 prefectures"},
    "DEU": {"name": "Germany", "n_expected": 16, "note": "16 Länder"},
    "FRA": {"name": "France", "n_expected": 13, "note": "13 regions (2016 reform)"},
    "GBR": {"name": "United Kingdom", "n_expected": 4, "note": "4 constituent countries"},
    "NGA": {"name": "Nigeria", "n_expected": 37, "note": "36 states + FCT"},
    "ZAF": {"name": "South Africa", "n_expected": 9, "note": "9 provinces"},
    "COL": {"name": "Colombia", "n_expected": 33, "note": "32 departments + DC"},
    "PER": {"name": "Peru", "n_expected": 25, "note": "25 regions"},
    "EGY": {"name": "Egypt", "n_expected": 27, "note": "27 governorates"},
}

# ── Analyze each country ─────────────────────────────────────────────

print("\n" + "=" * 70)
print("SUBNATIONAL ANALYSIS BY COUNTRY")
print("=" * 70)

analysis_rows = []

for iso, info in COUNTRIES.items():
    units = gadm1[gadm1["GID_0"] == iso].copy()
    n = len(units)

    if n == 0:
        print(f"\n  {iso} ({info['name']}): NO GADM DATA")
        continue

    # Calculate areas
    units["area_deg2"] = units.geometry.area
    units_proj = units.to_crs("EPSG:6933")  # equal area projection
    units["area_km2"] = units_proj.geometry.area / 1e6

    # Country total area
    country = gadm0[gadm0["GID_0"] == iso]
    if len(country) > 0:
        country_proj = country.to_crs("EPSG:6933")
        total_area = country_proj.geometry.area.sum() / 1e6
    else:
        total_area = units["area_km2"].sum()

    # Admin-1 types
    types = units["ENGTYPE_1"].value_counts()

    # Check what's already in polities database
    existing = polities[polities["iso3_code"] == iso]
    existing_names = set(existing["polity_name"].str.lower())

    print(f"\n  {iso} ({info['name']}): {n} admin-1 units (expected: {info['n_expected']})")
    print(f"    Types: {dict(types)}")
    print(f"    Total area: {total_area:,.0f} km²")
    print(f"    Area range: {units['area_km2'].min():,.0f} - {units['area_km2'].max():,.0f} km²")
    print(f"    Existing polity entries for {iso}: {len(existing)}")

    for _, u in units.iterrows():
        analysis_rows.append({
            "country_iso": iso,
            "country_name": info["name"],
            "admin1_name": u["NAME_1"],
            "admin1_type": u["ENGTYPE_1"],
            "area_km2": u["area_km2"],
            "pct_of_country": u["area_km2"] / total_area * 100 if total_area > 0 else 0,
            "gadm_gid": u["GID_1"],
            "varname": u.get("VARNAME_1", ""),
        })

# Save analysis
analysis_df = pd.DataFrame(analysis_rows)
analysis_df.to_csv(f"{BASE}/data/analysis/subnational_gadm_analysis.csv", index=False)
print(f"\nSaved {len(analysis_df)} admin-1 unit records to subnational_gadm_analysis.csv")


# =====================================================================
# PLOT 1: Admin-1 count by country (bar chart)
# =====================================================================
print("\n─── GENERATING PLOTS ───")

fig, ax = plt.subplots(figsize=(16, 8))
countries_sorted = sorted(COUNTRIES.keys(),
                          key=lambda x: len(gadm1[gadm1["GID_0"] == x]), reverse=True)
counts = [len(gadm1[gadm1["GID_0"] == iso]) for iso in countries_sorted]
expected = [COUNTRIES[iso]["n_expected"] for iso in countries_sorted]
names = [f"{iso}\n({COUNTRIES[iso]['name']})" for iso in countries_sorted]

x = np.arange(len(countries_sorted))
width = 0.35
bars1 = ax.bar(x - width/2, counts, width, label="GADM admin-1 units", color="#2196F3")
bars2 = ax.bar(x + width/2, expected, width, label="Expected units", color="#FF9800", alpha=0.7)

for bar, v in zip(bars1, counts):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            str(v), ha="center", fontsize=8, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(names, fontsize=8)
ax.set_ylabel("Number of Admin-1 Units")
ax.set_title("GADM Admin-1 Units vs Expected Subdivisions for Major Countries", fontweight="bold")
ax.legend()
ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/subnational_01_admin1_counts.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 1: admin-1 counts")


# =====================================================================
# PLOT 2: Area distribution of admin-1 units (box plots by country)
# =====================================================================
fig, ax = plt.subplots(figsize=(16, 8))

# Top 12 countries by subdivision count
top12 = sorted(COUNTRIES.keys(),
               key=lambda x: len(gadm1[gadm1["GID_0"] == x]), reverse=True)[:12]

data = []
labels = []
for iso in top12:
    units = analysis_df[analysis_df["country_iso"] == iso]["area_km2"]
    if len(units) > 0:
        data.append(units.values)
        labels.append(f"{iso}\n(n={len(units)})")

bp = ax.boxplot(data, labels=labels, patch_artist=True, showfliers=True)
colors = plt.cm.Set3(np.linspace(0, 1, len(data)))
for patch, color in zip(bp["boxes"], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

ax.set_ylabel("Area (km²)")
ax.set_title("Admin-1 Unit Area Distribution by Country", fontweight="bold")
ax.set_yscale("log")
ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/subnational_02_area_distribution.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 2: area distribution")


# =====================================================================
# PLOT 3: Map of admin-1 units for 6 key countries
# =====================================================================
fig, axes = plt.subplots(2, 3, figsize=(20, 14))
map_countries = ["USA", "BRA", "IND", "CHN", "RUS", "AUS"]

for ax, iso in zip(axes.flat, map_countries):
    units = gadm1[gadm1["GID_0"] == iso]
    if len(units) > 0:
        units.plot(ax=ax, color="lightblue", edgecolor="navy", linewidth=0.5)
        ax.set_title(f"{COUNTRIES[iso]['name']} ({len(units)} units)", fontweight="bold", fontsize=11)
        ax.set_aspect("equal")
        ax.tick_params(labelsize=7)
    else:
        ax.set_title(f"{iso}: No data")

fig.suptitle("GADM Admin-1 Units for Major Countries", fontsize=14, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/subnational_03_maps.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 3: admin-1 maps")


# =====================================================================
# PLOT 4: Existing vs potential polity entries
# =====================================================================
fig, ax = plt.subplots(figsize=(16, 8))

countries_ordered = sorted(COUNTRIES.keys(),
                           key=lambda x: len(gadm1[gadm1["GID_0"] == x]), reverse=True)

existing_counts = []
potential_new = []
labels = []

for iso in countries_ordered:
    n_gadm = len(gadm1[gadm1["GID_0"] == iso])
    n_existing = len(polities[polities["iso3_code"] == iso])
    existing_counts.append(n_existing)
    potential_new.append(n_gadm)
    labels.append(f"{iso}")

x = np.arange(len(labels))
width = 0.35
ax.bar(x - width/2, existing_counts, width, label="Existing polity entries", color="#4CAF50")
ax.bar(x + width/2, potential_new, width, label="GADM admin-1 units (potential)", color="#2196F3", alpha=0.7)

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9)
ax.set_ylabel("Count")
ax.set_title("Existing Polity Entries vs GADM Admin-1 Potential", fontweight="bold")
ax.legend()
ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/subnational_04_existing_vs_potential.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 4: existing vs potential")


# =====================================================================
# PLOT 5: Admin-1 type distribution across all countries
# =====================================================================
fig, ax = plt.subplots(figsize=(14, 8))

# Collect all admin-1 types
all_types = analysis_df["admin1_type"].value_counts().head(20)
colors_types = plt.cm.tab20(np.linspace(0, 1, len(all_types)))

ax.barh(range(len(all_types)), all_types.values, color=colors_types)
ax.set_yticks(range(len(all_types)))
ax.set_yticklabels(all_types.index, fontsize=9)
ax.set_xlabel("Number of Units")
ax.set_title("Admin-1 Unit Types Across Major Countries", fontweight="bold")
ax.invert_yaxis()

for i, v in enumerate(all_types.values):
    ax.text(v + 1, i, str(v), va="center", fontsize=9)

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/subnational_05_type_distribution.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 5: type distribution")


# =====================================================================
# PLOT 6: Comparative area treemap (showing relative sizes of largest admin-1 units)
# =====================================================================
fig, axes = plt.subplots(2, 3, figsize=(20, 14))
treemap_countries = ["USA", "BRA", "IND", "CHN", "RUS", "MEX"]

for ax, iso in zip(axes.flat, treemap_countries):
    df_c = analysis_df[analysis_df["country_iso"] == iso].sort_values("area_km2", ascending=True)
    if len(df_c) == 0:
        continue

    # Horizontal bar chart (largest first)
    top_n = min(20, len(df_c))
    df_top = df_c.tail(top_n)

    colors_bar = plt.cm.RdYlGn(np.linspace(0.2, 0.8, top_n))
    ax.barh(range(top_n), df_top["area_km2"].values / 1000, color=colors_bar)
    ax.set_yticks(range(top_n))
    ax.set_yticklabels(df_top["admin1_name"].values, fontsize=7)
    ax.set_xlabel("Area (1000 km²)", fontsize=9)
    ax.set_title(f"{COUNTRIES[iso]['name']} - Largest Admin-1 Units", fontsize=10, fontweight="bold")

fig.suptitle("Largest Admin-1 Units by Country (Top 20)", fontsize=14, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/subnational_06_largest_units.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 6: largest units")


# =====================================================================
# PLOT 7: Boundary stability assessment (qualitative)
# =====================================================================
# Known boundary stability data for major countries
stability_data = {
    "USA": {"stable_since": 1912, "rating": 5, "note": "Last state: AZ/NM 1912; AK/HI 1959"},
    "BRA": {"stable_since": 1988, "rating": 3, "note": "Tocantins created 1988; Mato Grosso split 1977"},
    "IND": {"stable_since": 2019, "rating": 2, "note": "Telangana 2014, J&K reorganized 2019; frequent changes"},
    "CHN": {"stable_since": 1997, "rating": 4, "note": "Chongqing 1997; Hainan 1988; mostly stable since Qing"},
    "RUS": {"stable_since": 2014, "rating": 2, "note": "Crimea 2014; many mergers 2003-2008"},
    "AUS": {"stable_since": 1911, "rating": 5, "note": "ACT 1911; very stable since federation"},
    "CAN": {"stable_since": 1999, "rating": 4, "note": "Nunavut 1999; Newfoundland 1949"},
    "MEX": {"stable_since": 1974, "rating": 4, "note": "BCS + Quintana Roo 1974; mostly stable"},
    "ARG": {"stable_since": 1991, "rating": 4, "note": "Tierra del Fuego province 1990"},
    "IDN": {"stable_since": 2022, "rating": 1, "note": "Constant splits; 27→34+ provinces since 1999"},
    "JPN": {"stable_since": 1972, "rating": 5, "note": "Okinawa returned 1972; prefectures stable since 1888"},
    "DEU": {"stable_since": 1990, "rating": 4, "note": "Reunification 1990; stable since"},
    "FRA": {"stable_since": 2016, "rating": 3, "note": "Region reform 2016; departments stable since 1860"},
    "GBR": {"stable_since": 1921, "rating": 5, "note": "N. Ireland 1921; countries stable for centuries"},
    "NGA": {"stable_since": 1996, "rating": 1, "note": "12→36 states 1963-1996; very unstable"},
    "ZAF": {"stable_since": 1994, "rating": 3, "note": "Provinces created 1994; different from historical"},
    "COL": {"stable_since": 1991, "rating": 4, "note": "Constitution 1991; mostly stable before"},
    "PER": {"stable_since": 2002, "rating": 3, "note": "Lima province created 2002"},
    "EGY": {"stable_since": 2011, "rating": 2, "note": "Governorates split frequently since 1950s"},
}

fig, axes = plt.subplots(1, 2, figsize=(16, 8))

# Rating bar chart
ax = axes[0]
countries_by_rating = sorted(stability_data.keys(), key=lambda x: stability_data[x]["rating"], reverse=True)
ratings = [stability_data[iso]["rating"] for iso in countries_by_rating]
colors_rating = [["#F44336", "#FF9800", "#FFC107", "#8BC34A", "#4CAF50"][r - 1] for r in ratings]

ax.barh(range(len(countries_by_rating)), ratings, color=colors_rating)
ax.set_yticks(range(len(countries_by_rating)))
ax.set_yticklabels([f"{iso} ({COUNTRIES[iso]['name']})" for iso in countries_by_rating], fontsize=9)
ax.set_xlabel("Boundary Stability Rating (1=Unstable, 5=Very Stable)")
ax.set_title("Admin-1 Boundary Stability Rating", fontweight="bold")
ax.set_xlim(0, 5.5)
for i, (iso, r) in enumerate(zip(countries_by_rating, ratings)):
    ax.text(r + 0.1, i, f"stable since {stability_data[iso]['stable_since']}", va="center", fontsize=8)

# Timeline of last boundary change
ax = axes[1]
years = [stability_data[iso]["stable_since"] for iso in countries_by_rating]
ax.barh(range(len(countries_by_rating)), [2025 - y for y in years],
        left=years, color=colors_rating, alpha=0.7)
ax.set_yticks(range(len(countries_by_rating)))
ax.set_yticklabels([f"{iso}" for iso in countries_by_rating], fontsize=9)
ax.set_xlabel("Year")
ax.set_title("Current Boundaries Stable Since...", fontweight="bold")
ax.axvline(1850, color="red", linestyle="--", alpha=0.5, label="WHEP start (1850)")
ax.axvline(1945, color="blue", linestyle="--", alpha=0.5, label="Post-WWII")
ax.legend(fontsize=9)
ax.set_xlim(1900, 2030)

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/subnational_07_boundary_stability.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 7: boundary stability")


# =====================================================================
# PLOT 8: Polity potential assessment matrix
# =====================================================================
fig, ax = plt.subplots(figsize=(14, 10))

# For each country, assess:
# x-axis: number of potential polity entries
# y-axis: boundary stability rating
# size: total area covered
# color: how many already exist in database

for iso in COUNTRIES:
    if iso not in stability_data:
        continue
    n_units = len(gadm1[gadm1["GID_0"] == iso])
    rating = stability_data[iso]["rating"]
    n_existing = len(polities[polities["iso3_code"] == iso])

    # Size proportional to country area
    c_area = analysis_df[analysis_df["country_iso"] == iso]["area_km2"].sum()
    size = max(50, min(500, c_area / 50))

    color = "green" if n_existing > 3 else "orange" if n_existing > 1 else "red"

    ax.scatter(n_units, rating, s=size, c=color, alpha=0.6, edgecolors="black", linewidth=1)
    ax.annotate(iso, (n_units, rating), textcoords="offset points",
                xytext=(8, 3), fontsize=9, fontweight="bold")

ax.set_xlabel("Number of GADM Admin-1 Units", fontsize=12)
ax.set_ylabel("Boundary Stability Rating", fontsize=12)
ax.set_title("Subnational Polity Potential Assessment\n(size=country area, color=existing entries)", fontsize=13, fontweight="bold")
ax.set_ylim(0.5, 5.5)
ax.set_yticks([1, 2, 3, 4, 5])
ax.set_yticklabels(["Very Unstable", "Unstable", "Moderate", "Stable", "Very Stable"])
ax.grid(alpha=0.3)

# Legend for colors
legend_elements = [
    mpatches.Patch(facecolor="green", label="3+ existing entries"),
    mpatches.Patch(facecolor="orange", label="1-2 existing entries"),
    mpatches.Patch(facecolor="red", label="0 existing entries"),
]
ax.legend(handles=legend_elements, loc="lower right", fontsize=10)

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/subnational_08_potential_matrix.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 8: potential matrix")


# =====================================================================
# Summary statistics
# =====================================================================
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

total_admin1 = len(analysis_df)
print(f"Total admin-1 units analyzed: {total_admin1}")
print(f"Countries analyzed: {len(COUNTRIES)}")
print()

# Priority recommendations
print("Priority recommendations for subnational polity additions:")
print()
recs = [
    ("USA", 5, "50 states + DC, boundaries stable since 1912, excellent GADM coverage"),
    ("JPN", 5, "47 prefectures, boundaries stable since 1888, excellent GADM coverage"),
    ("AUS", 5, "6 states already partially in database, fill gaps"),
    ("GBR", 5, "4 countries already in database as subnational regions"),
    ("CAN", 4, "13 provinces/territories, stable since 1999 (Nunavut)"),
    ("DEU", 4, "16 Länder, stable since reunification 1990"),
    ("MEX", 4, "32 states, stable since 1974"),
    ("ARG", 4, "24 provinces, stable since 1991"),
    ("CHN", 4, "31 province-level units, mostly stable"),
    ("BRA", 3, "27 states, but Tocantins only 1988"),
    ("COL", 4, "33 departments, stable since 1991"),
    ("FRA", 3, "Departments stable, but regions reformed 2016"),
    ("RUS", 2, "83 units, frequent mergers in 2000s"),
    ("IND", 2, "36 units, frequent reorganizations"),
    ("IDN", 1, "33+ provinces, constant splits since 1999"),
    ("NGA", 1, "37 states, created through many rounds 1963-1996"),
]

for iso, rating, note in recs:
    n = len(gadm1[gadm1["GID_0"] == iso])
    print(f"  {iso} (rating {rating}/5): {n} units — {note}")

print(f"\nTotal potential new polity entries (all countries): {total_admin1}")
print(f"High-confidence entries (rating 4-5): {sum(len(gadm1[gadm1['GID_0'] == iso]) for iso, r, _ in recs if r >= 4)}")
print(f"Medium-confidence entries (rating 3): {sum(len(gadm1[gadm1['GID_0'] == iso]) for iso, r, _ in recs if r == 3)}")
