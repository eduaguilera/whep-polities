#!/usr/bin/env python3
"""
Analyze coverage between the Excel region list and the polities database.
Generates comparison reports, gap analysis, and maps.
"""

import csv
import os
import warnings
from collections import Counter

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

warnings.filterwarnings("ignore")

BASE = "/home/usuario/whep-polities"


def load_data():
    """Load all data sources."""
    polities = pd.read_csv(f"{BASE}/data/final/polities_database.csv")
    matching = pd.read_csv(f"{BASE}/data/analysis/region_matching.csv")
    polygons = gpd.read_file(f"{BASE}/data/geodata/polities_polygons.gpkg")
    poly_report = pd.read_csv(f"{BASE}/data/analysis/polygon_matching_report.csv")
    return polities, matching, polygons, poly_report


def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def analyze_region_coverage(polities, matching):
    """Analyze how well the Excel regions map to polities."""
    print_section("REGION-TO-POLITY COVERAGE")

    total = len(matching)
    by_status = Counter(matching["match_status"])
    print(f"\nTotal unique Excel regions: {total}")
    for status, count in sorted(by_status.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        print(f"  {status:15s}: {count:4d} ({pct:5.1f}%)")

    # Matched regions: do they have polygons?
    matched = matching[matching["match_status"] == "matched"]
    matched_codes = set(matched["matched_polity_code"].dropna())
    poly_report = pd.read_csv(f"{BASE}/data/analysis/polygon_matching_report.csv")
    with_poly = poly_report[poly_report["polity_code"].isin(matched_codes) & poly_report["has_geometry"]]

    print(f"\nMatched regions with polygons: {len(with_poly)}/{len(matched_codes)}")
    without = matched_codes - set(with_poly["polity_code"])
    if without:
        print("  Missing polygons for matched regions:")
        for code in sorted(without):
            name = polities[polities["polity_code"] == code]["polity_name"].values
            print(f"    {code}: {name[0] if len(name) > 0 else '?'}")


def analyze_subnational_needs(matching):
    """Analyze subnational regions that need polygons."""
    print_section("SUBNATIONAL REGIONS NEEDING POLYGONS")

    sub = matching[matching["match_status"] == "subnational"]
    # Group by parent
    parents = Counter(sub["parent_polity_code"])
    print(f"\nTotal subnational regions: {len(sub)}")
    print(f"Unique parent polities: {len(parents)}")
    print(f"\nBy parent (needing subnational polygon extraction):")
    for parent, count in sorted(parents.items(), key=lambda x: -x[1]):
        names = sub[sub["parent_polity_code"] == parent]["cleaned_name"].tolist()
        print(f"\n  {parent} ({count} sub-regions):")
        for n in sorted(names):
            print(f"    - {n}")


def analyze_polygon_coverage(polities, poly_report):
    """Analyze polygon coverage by type and continent."""
    print_section("POLYGON COVERAGE BY TYPE AND CONTINENT")

    merged = polities.merge(poly_report[["polity_code", "has_geometry", "source_used"]],
                           on="polity_code", how="left")
    merged["has_geometry"] = merged["has_geometry"].fillna(False)

    # By type
    print("\nBy polity type:")
    for ptype in sorted(merged["polity_type"].unique()):
        subset = merged[merged["polity_type"] == ptype]
        with_geo = subset["has_geometry"].sum()
        total = len(subset)
        pct = with_geo / total * 100 if total > 0 else 0
        print(f"  {ptype:15s}: {with_geo:4d}/{total:4d} ({pct:5.1f}%)")

    # By continent
    print("\nBy continent:")
    for cont in sorted(merged["continent"].unique()):
        subset = merged[(merged["continent"] == cont) & (merged["polity_type"] != "region")]
        with_geo = subset["has_geometry"].sum()
        total = len(subset)
        pct = with_geo / total * 100 if total > 0 else 0
        print(f"  {cont:20s}: {with_geo:4d}/{total:4d} ({pct:5.1f}%)")


def analyze_temporal_coverage(polities, poly_report):
    """Check polygon availability by decade."""
    print_section("TEMPORAL POLYGON COVERAGE")

    merged = polities.merge(poly_report[["polity_code", "has_geometry"]],
                           on="polity_code", how="left")
    merged["has_geometry"] = merged["has_geometry"].fillna(False)
    non_region = merged[merged["polity_type"] != "region"]

    print("\nActive polities with polygons by decade:")
    print(f"{'Decade':>8s}  {'Total':>6s}  {'With poly':>9s}  {'Coverage':>8s}")
    for decade in range(1850, 2030, 10):
        active = non_region[
            (non_region["start_year"] <= decade) &
            (non_region["end_year"] >= decade)
        ]
        with_geo = active["has_geometry"].sum()
        total = len(active)
        pct = with_geo / total * 100 if total > 0 else 0
        print(f"  {decade:6d}  {total:6d}  {with_geo:9d}  {pct:7.1f}%")


def generate_map(polygons, polities):
    """Generate a world map of polity coverage."""
    print_section("GENERATING MAP")

    fig, axes = plt.subplots(2, 2, figsize=(20, 14))

    # 1. All polities colored by type
    ax = axes[0, 0]
    type_colors = {
        "sovereign": "#2196F3",
        "historical": "#9E9E9E",
        "colonial": "#F44336",
        "dependency": "#FF9800",
        "aggregate": "#9C27B0",
        "mandate": "#4CAF50",
        "disputed": "#FFEB3B",
        "puppet": "#795548",
    }
    # polity_type is already in the polygons gpkg; if not, merge it
    if "polity_type" not in polygons.columns:
        merged = polygons.merge(polities[["polity_code", "polity_type"]], on="polity_code")
    else:
        merged = polygons.copy()
    for ptype, color in type_colors.items():
        subset = merged[merged["polity_type"] == ptype]
        if len(subset) > 0:
            subset.plot(ax=ax, color=color, edgecolor="black", linewidth=0.2,
                       alpha=0.7, label=ptype)
    ax.set_title("All Polities by Type", fontsize=12, fontweight="bold")
    ax.legend(loc="lower left", fontsize=7)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 85)

    # 2. Polities active around 1920
    ax = axes[0, 1]
    active_1920 = merged[
        (merged["start_year"] <= 1920) & (merged["end_year"] >= 1920)
    ]
    for ptype, color in type_colors.items():
        subset = active_1920[active_1920["polity_type"] == ptype]
        if len(subset) > 0:
            subset.plot(ax=ax, color=color, edgecolor="black", linewidth=0.2,
                       alpha=0.7, label=ptype)
    ax.set_title("Polities Active in 1920", fontsize=12, fontweight="bold")
    ax.legend(loc="lower left", fontsize=7)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 85)

    # 3. Colonial entities
    ax = axes[1, 0]
    colonial = merged[merged["polity_type"].isin(["colonial", "mandate", "puppet"])]
    colonial.plot(ax=ax, color="#F44336", edgecolor="black", linewidth=0.2, alpha=0.6)
    ax.set_title(f"Colonial/Mandate/Puppet Entities ({len(colonial)})", fontsize=12, fontweight="bold")
    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 85)

    # 4. Sovereign states active 2025
    ax = axes[1, 1]
    sovereign_2025 = merged[
        (merged["polity_type"] == "sovereign") & (merged["end_year"] == 2025)
    ]
    sovereign_2025.plot(ax=ax, color="#2196F3", edgecolor="black", linewidth=0.3, alpha=0.7)
    ax.set_title(f"Current Sovereign States ({len(sovereign_2025)})", fontsize=12, fontweight="bold")
    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 85)

    plt.suptitle("WHEP Polities Database - Polygon Coverage", fontsize=14, fontweight="bold")
    plt.tight_layout()

    os.makedirs(f"{BASE}/data/analysis", exist_ok=True)
    plt.savefig(f"{BASE}/data/analysis/polities_map.png", dpi=150, bbox_inches="tight")
    print(f"  Map saved to data/analysis/polities_map.png")
    plt.close()


def analyze_subnational_coverage():
    """Analyze subnational polygon extraction results."""
    print_section("SUBNATIONAL POLYGON COVERAGE")

    sub_report_path = f"{BASE}/data/analysis/subnational_report.csv"
    if not os.path.exists(sub_report_path):
        print("  No subnational report found. Run build_subnational_polygons.py first.")
        return

    sub = pd.read_csv(sub_report_path)
    print(f"\nTotal subnational regions: {len(sub)}")
    print(f"  With geometry: {sub['has_geometry'].sum()}")
    print(f"  Without geometry: {(~sub['has_geometry']).sum()}")

    print(f"\nBy quality tier:")
    for tier in sorted(sub["quality_tier"].unique()):
        count = (sub["quality_tier"] == tier).sum()
        with_g = sub[sub["quality_tier"] == tier]["has_geometry"].sum()
        labels = {0: "No rule", 1: "Historical boundary", 2: "Good proxy",
                  3: "Acceptable proxy", 4: "No good proxy"}
        print(f"  Tier {tier} ({labels.get(tier, '?'):20s}): {count:3d} ({with_g} with geometry)")

    # By parent polity
    print(f"\nBy parent polity:")
    for parent in sorted(sub["parent_code"].unique()):
        subset = sub[sub["parent_code"] == parent]
        with_g = subset["has_geometry"].sum()
        total = len(subset)
        print(f"  {parent:25s}: {with_g}/{total}")


def generate_excel_match_summary(matching, polities, poly_report):
    """Generate a summary of which Excel regions have polygons (including subnational)."""
    print_section("EXCEL REGION → POLYGON SUMMARY")

    # Load subnational report if available
    sub_report_path = f"{BASE}/data/analysis/subnational_report.csv"
    sub_lookup = {}
    if os.path.exists(sub_report_path):
        sub_df = pd.read_csv(sub_report_path)
        for _, sr in sub_df.iterrows():
            sub_lookup[sr["excel_region"]] = {
                "has_geometry": sr["has_geometry"],
                "source": sr["source"],
                "quality_tier": sr["quality_tier"],
            }

    # For each non-aggregate, non-total region in Excel
    regions = matching[matching["match_status"].isin(["matched", "subnational"])]

    summary = []
    for _, r in regions.iterrows():
        has_poly = False
        poly_src = ""
        quality_tier = None

        if r["match_status"] == "matched" and pd.notna(r["matched_polity_code"]):
            pr = poly_report[poly_report["polity_code"] == r["matched_polity_code"]]
            if len(pr) > 0 and pr.iloc[0]["has_geometry"]:
                has_poly = True
                poly_src = pr.iloc[0]["source_used"]
        elif r["match_status"] == "subnational":
            name = r["cleaned_name"].strip()
            sub_info = sub_lookup.get(name)
            if sub_info and sub_info["has_geometry"]:
                has_poly = True
                poly_src = sub_info["source"]
                quality_tier = sub_info["quality_tier"]

        summary.append({
            "excel_region": r["cleaned_name"],
            "match_status": r["match_status"],
            "polity_code": r.get("matched_polity_code", ""),
            "parent_code": r.get("parent_polity_code", ""),
            "has_polygon": has_poly,
            "polygon_source": poly_src,
            "quality_tier": quality_tier if quality_tier else ("" if not has_poly else "1"),
            "needs_subnational": r["match_status"] == "subnational",
        })

    df = pd.DataFrame(summary)
    with_poly = df["has_polygon"].sum()
    sub_with_poly = df[df["needs_subnational"]]["has_polygon"].sum()
    sub_without = df["needs_subnational"].sum() - sub_with_poly
    no_poly = len(df) - with_poly

    print(f"\nExcel regions (matched + subnational): {len(df)}")
    print(f"  With polygon (direct match):       {with_poly - sub_with_poly}")
    print(f"  With polygon (subnational):        {sub_with_poly}")
    print(f"  Subnational without polygon:       {sub_without}")
    print(f"  Total with polygon:                {with_poly}")
    print(f"  Total without polygon:             {no_poly}")
    print(f"  Coverage:                          {with_poly/len(df)*100:.1f}%")

    df.to_csv(f"{BASE}/data/analysis/excel_polygon_coverage.csv", index=False)
    print(f"\n  Saved to data/analysis/excel_polygon_coverage.csv")


def main():
    polities, matching, polygons, poly_report = load_data()

    analyze_region_coverage(polities, matching)
    analyze_subnational_needs(matching)
    analyze_subnational_coverage()
    analyze_polygon_coverage(polities, poly_report)
    analyze_temporal_coverage(polities, poly_report)
    generate_excel_match_summary(matching, polities, poly_report)
    generate_map(polygons, polities)

    print_section("DONE")
    print("\nGenerated files:")
    print("  data/analysis/polities_map.png")
    print("  data/analysis/excel_polygon_coverage.csv")


if __name__ == "__main__":
    main()
