#!/usr/bin/env python3
"""
Validate and visualize ISO code overlap patterns in the polities database.

ISO code collisions occur when different historical/geographic entities share
the same 3-letter prefix in their polity_code (e.g., NOR = Northern Nigeria,
Northeastern Rhodesia, Northwestern Rhodesia, and Norway).

This script:
1. Identifies all ISO code collision groups
2. Classifies overlap types (boundary transitions, dual entities, true collisions)
3. Generates diagnostic visualizations
4. Produces a detailed overlap report

Writes:
  - data/analysis/iso_overlap_report.csv
  - data/analysis/plots/overlap_*.png
"""

import warnings
warnings.filterwarnings("ignore")

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from collections import Counter, defaultdict

BASE = "/home/usuario/whep-polities"
PLOT_DIR = f"{BASE}/data/analysis/plots"
os.makedirs(PLOT_DIR, exist_ok=True)

polities = pd.read_csv(f"{BASE}/data/final/polities_database.csv")
non_region = polities[polities["polity_type"] != "region"]

print("=" * 70)
print("ISO CODE OVERLAP ANALYSIS")
print("=" * 70)


# ── Identify all ISO prefix groups ───────────────────────────────────

def get_prefix(code):
    parts = code.split("-")
    return parts[0] if len(parts) >= 3 else code

non_region["prefix"] = non_region["polity_code"].apply(get_prefix)

# Group by prefix
prefix_groups = non_region.groupby("prefix")
multi_name_prefixes = {}  # prefixes that map to genuinely different entities

for prefix, group in prefix_groups:
    # Get distinct base names (strip parenthetical dates)
    import re
    base_names = set()
    for name in group["polity_name"]:
        base = re.sub(r'\s*\(.*?\)\s*$', '', str(name)).strip()
        base_names.add(base)

    if len(base_names) > 1:
        multi_name_prefixes[prefix] = {
            "names": sorted(base_names),
            "count": len(group),
            "codes": group["polity_code"].tolist(),
            "types": group["polity_type"].unique().tolist(),
        }

print(f"\nTotal prefix groups: {len(prefix_groups)}")
print(f"Prefixes with multiple distinct entity names: {len(multi_name_prefixes)}")


# ── Classify overlaps ────────────────────────────────────────────────

overlap_rows = []
collision_map = defaultdict(list)

for prefix, info in sorted(multi_name_prefixes.items()):
    group = non_region[non_region["prefix"] == prefix].sort_values("start_year")

    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            ri = group.iloc[i]
            rj = group.iloc[j]

            # Only flag overlapping pairs
            if ri["end_year"] < rj["start_year"] or rj["end_year"] < ri["start_year"]:
                continue

            overlap = min(ri["end_year"], rj["end_year"]) - max(ri["start_year"], rj["start_year"]) + 1

            # Classify
            name_i = re.sub(r'\s*\(.*?\)\s*$', '', str(ri["polity_name"])).strip()
            name_j = re.sub(r'\s*\(.*?\)\s*$', '', str(rj["polity_name"])).strip()

            if name_i == name_j:
                category = "same_entity_period_split"
            elif ri["polity_type"] != rj["polity_type"]:
                category = "different_type_dual"
            elif overlap == 1:
                category = "boundary_transition"
            else:
                # True ISO collision - different entities sharing prefix
                category = "iso_collision"
                collision_map[prefix].append((ri["polity_code"], rj["polity_code"], overlap))

            overlap_rows.append({
                "prefix": prefix,
                "code1": ri["polity_code"],
                "name1": ri["polity_name"],
                "type1": ri["polity_type"],
                "code2": rj["polity_code"],
                "name2": rj["polity_name"],
                "type2": rj["polity_type"],
                "overlap_years": overlap,
                "category": category,
            })

overlap_df = pd.DataFrame(overlap_rows)

# Summarize categories
if len(overlap_df) > 0:
    print("\nOverlap categories:")
    for cat, count in overlap_df["category"].value_counts().items():
        print(f"  {cat}: {count}")

print(f"\nISO collision prefixes: {len(collision_map)}")
for prefix, collisions in sorted(collision_map.items()):
    info = multi_name_prefixes[prefix]
    print(f"  {prefix}: {info['names']}")
    for c1, c2, ov in collisions[:3]:
        print(f"    {c1} ↔ {c2} ({ov}yr overlap)")

# Save report
overlap_df.to_csv(f"{BASE}/data/analysis/iso_overlap_report.csv", index=False)


# =====================================================================
# PLOTS
# =====================================================================
print("\n─── GENERATING PLOTS ───")

# Plot 1: Timeline visualization of worst ISO collision groups
fig, axes = plt.subplots(len(collision_map) if len(collision_map) <= 12 else 12, 1,
                          figsize=(16, max(8, len(collision_map) * 1.5)))
if len(collision_map) <= 1:
    axes = [axes]
elif len(collision_map) > 12:
    axes = list(axes)[:12]

TYPE_COLORS = {
    "sovereign": "#2196F3", "historical": "#9E9E9E", "colonial": "#F44336",
    "dependency": "#FF9800", "aggregate": "#9C27B0", "mandate": "#4CAF50",
    "disputed": "#FFEB3B", "puppet": "#795548",
}

for ax, (prefix, collisions) in zip(axes, sorted(collision_map.items())):
    group = non_region[non_region["prefix"] == prefix].sort_values("start_year")

    for idx, (_, row) in enumerate(group.iterrows()):
        name = re.sub(r'\s*\(.*?\)\s*$', '', str(row["polity_name"])).strip()[:25]
        color = TYPE_COLORS.get(row["polity_type"], "#666666")
        ax.barh(idx, row["end_year"] - row["start_year"] + 1,
                left=row["start_year"], height=0.6, color=color, alpha=0.7,
                edgecolor="black", linewidth=0.5)
        ax.text(row["start_year"] - 2, idx, f"{name}", ha="right", va="center",
                fontsize=7)

    ax.set_title(f"Prefix: {prefix} ({', '.join(multi_name_prefixes[prefix]['names'][:3])})",
                 fontsize=9, fontweight="bold")
    ax.set_xlim(1790, 2030)
    ax.set_yticks([])
    ax.tick_params(labelsize=7)

fig.suptitle("ISO Code Collision Groups — Timeline View", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/overlap_01_collision_timelines.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 1: collision timelines")


# Plot 2: Overlap category distribution
if len(overlap_df) > 0:
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Pie chart
    ax = axes[0]
    cats = overlap_df["category"].value_counts()
    colors_cat = {"same_entity_period_split": "#4CAF50", "different_type_dual": "#2196F3",
                  "boundary_transition": "#FF9800", "iso_collision": "#F44336"}
    ax.pie(cats.values, labels=[c.replace("_", "\n") for c in cats.index],
           colors=[colors_cat.get(c, "#999") for c in cats.index],
           autopct="%1.0f%%", startangle=90)
    ax.set_title("Overlap Categories", fontweight="bold")

    # Duration distribution by category
    ax = axes[1]
    for cat in ["iso_collision", "same_entity_period_split", "different_type_dual"]:
        subset = overlap_df[overlap_df["category"] == cat]
        if len(subset) > 0:
            ax.hist(subset["overlap_years"], bins=30, alpha=0.5,
                    color=colors_cat.get(cat, "#999"), label=cat.replace("_", " "))
    ax.set_xlabel("Overlap Duration (years)")
    ax.set_ylabel("Count")
    ax.set_title("Overlap Duration by Category", fontweight="bold")
    ax.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/overlap_02_categories.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Plot 2: overlap categories")


# Plot 3: Full multi-name prefix landscape
fig, ax = plt.subplots(figsize=(16, 10))

prefixes_by_size = sorted(multi_name_prefixes.items(),
                           key=lambda x: len(x[1]["names"]), reverse=True)

y_positions = []
labels = []
for i, (prefix, info) in enumerate(prefixes_by_size[:40]):
    y_positions.append(i)
    label = f"{prefix}: {', '.join(n[:20] for n in info['names'][:3])}"
    if len(info["names"]) > 3:
        label += f" +{len(info['names'])-3}"
    labels.append(label)

    # Plot timeline bars
    group = non_region[non_region["prefix"] == prefix].sort_values("start_year")
    for j, (_, row) in enumerate(group.iterrows()):
        color = TYPE_COLORS.get(row["polity_type"], "#666666")
        ax.barh(i + j * 0.15, row["end_year"] - row["start_year"] + 1,
                left=row["start_year"], height=0.12, color=color, alpha=0.7)

ax.set_yticks(y_positions)
ax.set_yticklabels(labels, fontsize=7)
ax.set_xlabel("Year")
ax.set_title("Top 40 ISO Prefix Groups with Multiple Entity Names", fontweight="bold")
ax.set_xlim(1790, 2030)
ax.invert_yaxis()

# Legend
legend_elements = [mpatches.Patch(facecolor=c, label=t)
                   for t, c in TYPE_COLORS.items() if t != "puppet"]
ax.legend(handles=legend_elements, loc="lower right", fontsize=8, ncol=3)

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/overlap_03_prefix_landscape.png", dpi=150, bbox_inches="tight")
plt.close()
print("  Plot 3: prefix landscape")


# ── Summary ──────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Prefixes analyzed: {len(multi_name_prefixes)}")
print(f"True ISO collision prefixes: {len(collision_map)}")
print(f"Total overlapping pairs: {len(overlap_df)}")
if len(overlap_df) > 0:
    print(f"  ISO collisions: {len(overlap_df[overlap_df['category'] == 'iso_collision'])}")
    print(f"  Same entity splits: {len(overlap_df[overlap_df['category'] == 'same_entity_period_split'])}")
    print(f"  Different type duals: {len(overlap_df[overlap_df['category'] == 'different_type_dual'])}")
    print(f"  Boundary transitions: {len(overlap_df[overlap_df['category'] == 'boundary_transition'])}")
