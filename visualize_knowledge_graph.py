#!/usr/bin/env python3
"""
Visualize the WHEP polities knowledge graph.

Reads:
  - data/analysis/knowledge_graph_edges.csv
  - data/analysis/knowledge_graph_nodes.csv
  - data/final/polities_database.csv

Writes:
  - data/analysis/plots/kg_01_relation_type_distribution.png
  - data/analysis/plots/kg_02_degree_distribution.png
  - data/analysis/plots/kg_03_successor_chains.png
  - data/analysis/plots/kg_04_colonial_empires.png
  - data/analysis/plots/kg_05_subnational_hierarchy.png
  - data/analysis/plots/kg_06_graph_metrics_summary.png
"""

import os
import warnings

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

BASE = "/home/usuario/whep-polities"
PLOT_DIR = f"{BASE}/data/analysis/plots"
os.makedirs(PLOT_DIR, exist_ok=True)

# ── Colors ─────────────────────────────────────────────────────────────

RELATION_COLORS = {
    "located_in_continent": "#78909C",
    "region_contains": "#42A5F5",
    "subregion_of": "#66BB6A",
    "temporal_next": "#FFA726",
    "aggregate_covers": "#AB47BC",
    "colonial_ruler_of": "#EF5350",
    "same_territory": "#26C6DA",
    "successor_of": "#8D6E63",
    "predecessor_of": "#BDBDBD",
}

TYPE_COLORS = {
    "sovereign": "#2196F3",
    "historical": "#FF9800",
    "colonial": "#F44336",
    "dependency": "#9C27B0",
    "mandate": "#E91E63",
    "aggregate": "#607D8B",
    "region": "#795548",
    "subnational": "#4CAF50",
    "disputed": "#FF5722",
    "puppet": "#9E9E9E",
    "occupation": "#673AB7",
    "continent": "#FFC107",
}

CONTINENT_COLORS = {
    "Africa": "#E53935",
    "Asia": "#FF9800",
    "Europe": "#1E88E5",
    "North America": "#43A047",
    "South America": "#8E24AA",
    "Oceania": "#00ACC1",
    "Antarctica": "#546E7A",
    "Global": "#757575",
}

# ── Load data ──────────────────────────────────────────────────────────

print("Loading knowledge graph data...")
edges = pd.read_csv(f"{BASE}/data/analysis/knowledge_graph_edges.csv")
nodes = pd.read_csv(f"{BASE}/data/analysis/knowledge_graph_nodes.csv")
polities = pd.read_csv(f"{BASE}/data/final/polities_database.csv")

print(f"  Nodes: {len(nodes)}, Edges: {len(edges)}")

# Build NetworkX graph
G = nx.DiGraph()
for _, row in nodes.iterrows():
    G.add_node(row["polity_code"], **row.to_dict())
for _, row in edges.iterrows():
    G.add_edge(row["source"], row["target"], **row.to_dict())


# ── Plot 1: Relation Type Distribution ────────────────────────────────

print("\nPlot 1: Relation type distribution...")
fig, ax = plt.subplots(figsize=(12, 6))

rel_counts = edges["relation"].value_counts()
colors = [RELATION_COLORS.get(r, "#999") for r in rel_counts.index]

bars = ax.barh(range(len(rel_counts)), rel_counts.values, color=colors)
ax.set_yticks(range(len(rel_counts)))
ax.set_yticklabels(rel_counts.index, fontsize=11)
ax.set_xlabel("Number of edges", fontsize=12)
ax.set_title("Knowledge Graph: Edge Count by Relation Type", fontsize=14, fontweight="bold")
ax.invert_yaxis()

for bar, val in zip(bars, rel_counts.values):
    ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height() / 2,
            str(val), va="center", fontsize=10, fontweight="bold")

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/kg_01_relation_type_distribution.png", dpi=150)
plt.close()

# ── Plot 2: Degree Distribution ───────────────────────────────────────

print("Plot 2: Degree distribution...")
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Only polity nodes (exclude continent pseudo-nodes)
polity_nodes = nodes[nodes["node_type"] == "polity"]
degrees = polity_nodes["total_degree"].values

# Histogram
ax = axes[0]
ax.hist(degrees, bins=50, color="#2196F3", edgecolor="white", alpha=0.8)
ax.set_xlabel("Degree (total connections)", fontsize=12)
ax.set_ylabel("Number of polities", fontsize=12)
ax.set_title("Degree Distribution", fontsize=13, fontweight="bold")
ax.axvline(np.median(degrees), color="red", linestyle="--", label=f"Median: {np.median(degrees):.0f}")
ax.legend()

# Top-20 most connected polities
ax = axes[1]
top = polity_nodes.nlargest(20, "total_degree")
colors = [TYPE_COLORS.get(t, "#999") for t in top["polity_type"]]
ax.barh(range(len(top)), top["total_degree"].values, color=colors)
ax.set_yticks(range(len(top)))
labels = [f"{row['polity_name'][:30]}" for _, row in top.iterrows()]
ax.set_yticklabels(labels, fontsize=9)
ax.set_xlabel("Degree", fontsize=12)
ax.set_title("Top 20 Most Connected Polities", fontsize=13, fontweight="bold")
ax.invert_yaxis()

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/kg_02_degree_distribution.png", dpi=150)
plt.close()

# ── Plot 3: Successor Chains ─────────────────────────────────────────

print("Plot 3: Successor chains...")

# Build chains from temporal_next + predecessor/successor edges
chain_edges = edges[edges["relation"].isin(["temporal_next", "predecessor_of", "successor_of"])]

# Find interesting chains by tracing from specific start polities
interesting_isos = ["DEU", "CHN", "RUS", "ITA", "PAK", "SDN", "YUG", "ETH"]
chain_graph = nx.DiGraph()

for iso in interesting_isos:
    iso_entries = polities[
        (polities["iso3_code"] == iso)
        & (polities["polity_type"].isin(["sovereign", "historical"]))
    ].sort_values("start_year")

    if len(iso_entries) == 0:
        continue

    for _, row in iso_entries.iterrows():
        chain_graph.add_node(
            row["polity_code"],
            label=f"{row['polity_name']}\n({row['start_year']}-{row['end_year']})",
            polity_type=row["polity_type"],
            start_year=row["start_year"],
            iso3=iso,
        )

    codes = iso_entries["polity_code"].tolist()
    for i in range(len(codes) - 1):
        chain_graph.add_edge(codes[i], codes[i + 1])

# Also add explicit predecessor/successor links
for _, row in chain_edges.iterrows():
    if row["source"] in chain_graph.nodes and row["target"] in chain_graph.nodes:
        chain_graph.add_edge(row["source"], row["target"])

fig, ax = plt.subplots(figsize=(18, 10))

if len(chain_graph.nodes) > 0:
    # Position nodes by start_year (x) and ISO group (y)
    iso_list = list(dict.fromkeys(
        nx.get_node_attributes(chain_graph, "iso3").values()
    ))
    pos = {}
    for node in chain_graph.nodes:
        data = chain_graph.nodes[node]
        x = data.get("start_year", 1900)
        y = iso_list.index(data.get("iso3", "")) if data.get("iso3", "") in iso_list else 0
        # Slight jitter to avoid overlap
        pos[node] = (x, -y * 2)

    node_colors = [TYPE_COLORS.get(chain_graph.nodes[n].get("polity_type", ""), "#999")
                   for n in chain_graph.nodes]
    labels = {n: chain_graph.nodes[n].get("label", n)[:25] for n in chain_graph.nodes}

    nx.draw_networkx_nodes(chain_graph, pos, ax=ax, node_size=200,
                           node_color=node_colors, alpha=0.9)
    nx.draw_networkx_edges(chain_graph, pos, ax=ax, arrows=True,
                           arrowsize=12, edge_color="#666", alpha=0.6)
    nx.draw_networkx_labels(chain_graph, pos, labels=labels, ax=ax,
                            font_size=6, font_weight="bold")

    # Add ISO labels on the left
    for iso in iso_list:
        y = -iso_list.index(iso) * 2
        ax.text(1790, y, iso, fontsize=12, fontweight="bold", ha="right", va="center")

ax.set_title("Temporal Successor Chains for Selected Countries", fontsize=14, fontweight="bold")
ax.set_xlabel("Start Year", fontsize=12)
ax.margins(0.15)
ax.grid(True, axis="x", alpha=0.3)

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/kg_03_successor_chains.png", dpi=150)
plt.close()

# ── Plot 4: Colonial Empires ─────────────────────────────────────────

print("Plot 4: Colonial empires...")

colonial_edges = edges[edges["relation"] == "colonial_ruler_of"]
col_graph = nx.DiGraph()

for _, row in colonial_edges.iterrows():
    src = row["source"]
    tgt = row["target"]
    if src in G.nodes and tgt in G.nodes:
        col_graph.add_node(src, **{k: v for k, v in G.nodes[src].items() if isinstance(v, (str, int, float))})
        col_graph.add_node(tgt, **{k: v for k, v in G.nodes[tgt].items() if isinstance(v, (str, int, float))})
        col_graph.add_edge(src, tgt)

fig, ax = plt.subplots(figsize=(18, 14))

if len(col_graph.nodes) > 0:
    # Use spring layout with metropoles pinned
    metropoles = set(colonial_edges["source"].unique())
    pos = nx.spring_layout(col_graph, k=2.5, iterations=80, seed=42)

    # Color by continent of the colony
    node_colors = []
    node_sizes = []
    for n in col_graph.nodes:
        cont = col_graph.nodes[n].get("continent", "")
        node_colors.append(CONTINENT_COLORS.get(cont, "#999"))
        if n in metropoles:
            node_sizes.append(600)
        else:
            node_sizes.append(150)

    nx.draw_networkx_nodes(col_graph, pos, ax=ax, node_size=node_sizes,
                           node_color=node_colors, alpha=0.8, edgecolors="black", linewidths=0.5)
    nx.draw_networkx_edges(col_graph, pos, ax=ax, arrows=True,
                           arrowsize=8, edge_color="#AAA", alpha=0.5)

    # Label metropoles prominently
    metro_labels = {n: G.nodes[n].get("polity_name", n)[:20] for n in metropoles if n in col_graph.nodes}
    nx.draw_networkx_labels(col_graph, pos, labels=metro_labels, ax=ax,
                            font_size=9, font_weight="bold", font_color="black")

    # Label colonies smaller
    colony_labels = {n: G.nodes[n].get("polity_name", n)[:20]
                     for n in col_graph.nodes if n not in metropoles}
    nx.draw_networkx_labels(col_graph, pos, labels=colony_labels, ax=ax,
                            font_size=5, font_color="#333")

    # Legend
    handles = [plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=c,
               markersize=8, label=cont)
               for cont, c in CONTINENT_COLORS.items() if cont != "Global"]
    ax.legend(handles=handles, loc="lower left", fontsize=9, title="Colony continent")

ax.set_title("Colonial Empire Networks", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/kg_04_colonial_empires.png", dpi=150)
plt.close()

# ── Plot 5: Subnational Hierarchy ────────────────────────────────────

print("Plot 5: Subnational hierarchy...")

sub_edges = edges[edges["relation"] == "subregion_of"]
# Only polity-to-polity (not M49 regions)
sub_polity = sub_edges[sub_edges["evidence"].str.contains("notes field", na=False)]

fig, axes = plt.subplots(2, 3, figsize=(20, 14))
countries = [
    ("USA", "USA-1959-2025", "United States"),
    ("CAN", "CAN-1948-2025", "Canada"),
    ("BRA", "BRA-1909-2025", "Brazil"),
    ("AUS", "AUS-1901-2025", "Australia"),
    ("CHN", "F351-1950-2025", "China"),
    ("RUS", "RUS-2014-2025", "Russia"),
]

for idx, (iso, parent_code, label) in enumerate(countries):
    ax = axes[idx // 3][idx % 3]

    # Build subgraph
    sub_g = nx.DiGraph()
    country_sub = sub_polity[sub_polity["target"] == parent_code]

    if len(country_sub) == 0:
        ax.text(0.5, 0.5, f"No subnational links for {label}", ha="center", va="center",
                transform=ax.transAxes)
        ax.set_title(label, fontsize=13, fontweight="bold")
        continue

    sub_g.add_node(parent_code, label=label)
    for _, row in country_sub.iterrows():
        src = row["source"]
        name_row = polities[polities["polity_code"] == src]
        name = name_row.iloc[0]["polity_name"][:20] if len(name_row) > 0 else src
        sub_g.add_node(src, label=name)
        sub_g.add_edge(src, parent_code)

    # Star layout
    pos = nx.spring_layout(sub_g, k=1.5, iterations=50, seed=42)

    # Draw
    colors = ["#E53935" if n == parent_code else "#4CAF50" for n in sub_g.nodes]
    sizes = [500 if n == parent_code else 100 for n in sub_g.nodes]
    nx.draw_networkx_nodes(sub_g, pos, ax=ax, node_size=sizes, node_color=colors, alpha=0.8)
    nx.draw_networkx_edges(sub_g, pos, ax=ax, arrows=True, arrowsize=8, edge_color="#AAA", alpha=0.5)

    # Labels
    labels_dict = nx.get_node_attributes(sub_g, "label")
    nx.draw_networkx_labels(sub_g, pos, labels=labels_dict, ax=ax, font_size=5)

    ax.set_title(f"{label} ({len(country_sub)} regions)", fontsize=13, fontweight="bold")

plt.suptitle("Subnational Hierarchy: Admin-1 Units → Parent Country",
             fontsize=15, fontweight="bold", y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig(f"{PLOT_DIR}/kg_05_subnational_hierarchy.png", dpi=150)
plt.close()

# ── Plot 6: Graph Metrics Summary ────────────────────────────────────

print("Plot 6: Graph metrics summary...")

fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# 6a: Edges over time (by start_year)
ax = axes[0][0]
temporal_edges = edges[edges["start_year"].notna() & (edges["start_year"] != "")]
temporal_edges = temporal_edges.copy()
temporal_edges["start_year"] = pd.to_numeric(temporal_edges["start_year"], errors="coerce")
valid_years = temporal_edges[temporal_edges["start_year"] > 1700]

year_counts = valid_years.groupby([pd.cut(valid_years["start_year"], bins=range(1800, 2030, 25)), "relation"]).size()
year_counts = year_counts.unstack(fill_value=0)

# Stacked bar chart by relation type (excluding located_in_continent for clarity)
plot_rels = [r for r in year_counts.columns if r != "located_in_continent"]
bottoms = np.zeros(len(year_counts))
for rel in plot_rels:
    if rel in year_counts.columns:
        vals = year_counts[rel].values
        color = RELATION_COLORS.get(rel, "#999")
        ax.bar(range(len(year_counts)), vals, bottom=bottoms, color=color, label=rel, alpha=0.8)
        bottoms += vals

ax.set_xticks(range(len(year_counts)))
ax.set_xticklabels([str(i.left) for i in year_counts.index], rotation=45, fontsize=8)
ax.set_ylabel("Edge count")
ax.set_title("Edge Count by Period (excl. continent links)", fontsize=12, fontweight="bold")
ax.legend(fontsize=7, loc="upper left")

# 6b: Node type distribution
ax = axes[0][1]
type_counts = nodes[nodes["node_type"] == "polity"]["polity_type"].value_counts()
colors = [TYPE_COLORS.get(t, "#999") for t in type_counts.index]
wedges, texts, autotexts = ax.pie(type_counts.values, labels=type_counts.index,
                                   colors=colors, autopct="%1.0f%%", pctdistance=0.8)
for t in autotexts:
    t.set_fontsize(8)
for t in texts:
    t.set_fontsize(9)
ax.set_title("Node Distribution by Polity Type", fontsize=12, fontweight="bold")

# 6c: Component size distribution
ax = axes[1][0]
ug = G.to_undirected()
comp_sizes = [len(c) for c in nx.connected_components(ug)]
ax.hist(comp_sizes, bins=30, color="#42A5F5", edgecolor="white")
ax.set_xlabel("Component size")
ax.set_ylabel("Count")
ax.set_title(f"Connected Component Sizes ({len(comp_sizes)} components)", fontsize=12, fontweight="bold")
ax.set_yscale("log")
ax.axvline(max(comp_sizes), color="red", linestyle="--",
           label=f"Largest: {max(comp_sizes)}")
ax.legend()

# 6d: In-degree vs out-degree scatter
ax = axes[1][1]
polity_only = nodes[nodes["node_type"] == "polity"]
colors_scatter = [TYPE_COLORS.get(t, "#999") for t in polity_only["polity_type"]]
ax.scatter(polity_only["in_degree"], polity_only["out_degree"],
           c=colors_scatter, alpha=0.5, s=20, edgecolors="none")
ax.set_xlabel("In-degree")
ax.set_ylabel("Out-degree")
ax.set_title("In-degree vs Out-degree by Polity Type", fontsize=12, fontweight="bold")
ax.plot([0, ax.get_xlim()[1]], [0, ax.get_xlim()[1]], "k--", alpha=0.3)

# Add legend for polity types
handles = [plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=c,
           markersize=6, label=t)
           for t, c in TYPE_COLORS.items() if t in polity_only["polity_type"].values]
ax.legend(handles=handles, fontsize=7, loc="upper right")

plt.suptitle("Knowledge Graph Metrics", fontsize=15, fontweight="bold", y=1.01)
plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/kg_06_graph_metrics_summary.png", dpi=150, bbox_inches="tight")
plt.close()

print(f"\nAll plots saved to {PLOT_DIR}/kg_*.png")
print("Done!")
