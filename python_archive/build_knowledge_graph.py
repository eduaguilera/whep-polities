#!/usr/bin/env python3
"""
Build a knowledge graph of relations between WHEP polities.

Relations extracted:
  1. predecessor_of / successor_of  (from predecessor/successor columns)
  2. subregion_of                   (subnational -> parent polity)
  3. aggregate_covers               (aggregate -> period-specific entries)
  4. temporal_next                  (same ISO, adjacent time periods)
  5. colonial_ruler_of              (metropole -> colony, inferred from names)
  6. region_contains                (M49 region -> country polity)
  7. located_in_continent           (polity -> continent node)
  8. same_territory                 (sovereign + colonial overlap on same land)

Reads:
  - data/final/polities_database.csv
  - data/whep-source/unstats_m49.csv
  - data/whep-source/faostat_regions.csv

Writes:
  - data/analysis/knowledge_graph_edges.csv
  - data/analysis/knowledge_graph_nodes.csv
  - data/analysis/knowledge_graph.graphml
"""

import os
import re
import warnings

import networkx as nx
import pandas as pd

warnings.filterwarnings("ignore")

BASE = "/home/usuario/whep-polities"

# ── Load data ──────────────────────────────────────────────────────────

print("Loading data...")
df = pd.read_csv(f"{BASE}/data/final/polities_database.csv")
m49 = pd.read_csv(f"{BASE}/data/whep-source/unstats_m49.csv")
fao = pd.read_csv(f"{BASE}/data/whep-source/faostat_regions.csv")

all_codes = set(df["polity_code"].values)
print(f"  Polities: {len(df)}")

# ── Build graph ────────────────────────────────────────────────────────

G = nx.DiGraph()

# Add polity nodes
for _, row in df.iterrows():
    G.add_node(
        row["polity_code"],
        polity_name=str(row["polity_name"]),
        polity_type=str(row["polity_type"]),
        continent=str(row["continent"]),
        start_year=int(row["start_year"]),
        end_year=int(row["end_year"]),
        iso3_code=str(row["iso3_code"]) if pd.notna(row["iso3_code"]) else "",
        node_type="polity",
    )

# Add continent nodes
continents = [c for c in df["continent"].unique() if pd.notna(c)]
for c in continents:
    G.add_node(c, polity_name=c, polity_type="continent", continent=c,
               start_year=1800, end_year=2025, iso3_code="", node_type="continent")

edge_log = []  # Collect all edges for CSV export


def add_edge(source, target, relation, evidence="", start_year=None, end_year=None):
    """Add edge to graph and log."""
    G.add_edge(source, target, relation=relation, evidence=evidence,
               start_year=start_year or 0, end_year=end_year or 0)
    edge_log.append({
        "source": source, "target": target, "relation": relation,
        "evidence": evidence, "start_year": start_year or "", "end_year": end_year or "",
    })


# ── 1. Predecessor / Successor ────────────────────────────────────────

print("\n1. Extracting predecessor/successor relations...")
missing_refs = []

for _, row in df.iterrows():
    code = row["polity_code"]

    # Predecessors
    pred = row["predecessor"]
    if pd.notna(pred) and pred.strip():
        for ref in re.split(r"[;,]\s*", str(pred)):
            ref = ref.strip()
            if ref in all_codes:
                add_edge(ref, code, "predecessor_of",
                         evidence="predecessor column",
                         start_year=row["start_year"], end_year=row["end_year"])
            elif re.match(r"^[A-Z0-9]+-\d{4}-\d{4}$", ref):
                missing_refs.append((code, "predecessor", ref))

    # Successors
    succ = row["successor"]
    if pd.notna(succ) and succ.strip():
        for ref in re.split(r"[;,]\s*", str(succ)):
            ref = ref.strip()
            if ref in all_codes:
                add_edge(code, ref, "successor_of",
                         evidence="successor column",
                         start_year=row["start_year"], end_year=row["end_year"])
            elif re.match(r"^[A-Z0-9]+-\d{4}-\d{4}$", ref):
                missing_refs.append((code, "successor", ref))

pred_succ_count = sum(1 for e in edge_log if e["relation"] in ("predecessor_of", "successor_of"))
print(f"  predecessor_of + successor_of edges: {pred_succ_count}")
if missing_refs:
    print(f"  Missing references: {len(missing_refs)}")
    for code, field, ref in missing_refs[:5]:
        print(f"    {code} -> {field}={ref}")

# ── 2. Subregion_of (subnational -> parent) ───────────────────────────

print("\n2. Extracting subregion_of relations...")
sub_count = 0
for _, row in df[df["polity_type"] == "subnational"].iterrows():
    notes = str(row["notes"])
    match = re.search(r"Parent:\s*([A-Z0-9]+-\d{4}-\d{4})", notes)
    if match:
        parent = match.group(1)
        if parent in all_codes:
            add_edge(row["polity_code"], parent, "subregion_of",
                     evidence="notes field (Parent)",
                     start_year=row["start_year"], end_year=row["end_year"])
            sub_count += 1

print(f"  subregion_of edges: {sub_count}")

# ── 3. Aggregate_covers ───────────────────────────────────────────────

print("\n3. Extracting aggregate_covers relations...")
agg_count = 0
aggregates = df[df["polity_type"] == "aggregate"]

for _, agg in aggregates.iterrows():
    iso = agg["iso3_code"]
    if pd.isna(iso) or iso == "":
        continue

    # Find non-aggregate, non-region, non-subnational entries with same ISO
    matches = df[
        (df["iso3_code"] == iso)
        & (df["polity_type"].isin(["sovereign", "historical", "colonial", "dependency", "mandate"]))
        & (df["start_year"] >= agg["start_year"])
        & (df["end_year"] <= agg["end_year"])
    ]
    for _, m in matches.iterrows():
        add_edge(agg["polity_code"], m["polity_code"], "aggregate_covers",
                 evidence=f"same ISO3 ({iso}), date range contained",
                 start_year=m["start_year"], end_year=m["end_year"])
        agg_count += 1

print(f"  aggregate_covers edges: {agg_count}")

# ── 4. Temporal_next (same ISO, consecutive periods) ──────────────────

print("\n4. Extracting temporal_next relations...")
temp_count = 0
core_types = ["sovereign", "historical", "colonial", "dependency", "mandate"]
core = df[df["polity_type"].isin(core_types)].copy()

for iso, group in core.groupby("iso3_code"):
    if pd.isna(iso) or iso == "":
        continue
    sorted_g = group.sort_values("start_year")
    codes = sorted_g["polity_code"].tolist()
    starts = sorted_g["start_year"].tolist()
    ends = sorted_g["end_year"].tolist()

    for i in range(len(codes) - 1):
        gap = starts[i + 1] - ends[i]
        if -2 <= gap <= 5:  # Allow 1-year overlap (boundary) to 5-year gap
            add_edge(codes[i], codes[i + 1], "temporal_next",
                     evidence=f"same ISO3 ({iso}), gap={gap}y",
                     start_year=ends[i], end_year=starts[i + 1])
            temp_count += 1

print(f"  temporal_next edges: {temp_count}")

# ── 5. Colonial_ruler_of ──────────────────────────────────────────────

print("\n5. Extracting colonial_ruler_of relations...")

# Map colonial name keywords to the ISO3 of the metropole
COLONIAL_POWERS = {
    "British": "GBR", "Britain": "GBR", "Anglo-": "GBR",
    "French": "FRA", "France": "FRA",
    "German": "DEU", "Germany": "DEU",
    "Spanish": "ESP", "Spain": "ESP",
    "Portuguese": "PRT", "Portugal": "PRT",
    "Dutch": "NLD", "Netherlands": "NLD",
    "Italian": "ITA", "Italy": "ITA",
    "Belgian": "BEL", "Belgium": "BEL",
    "Japanese": "JPN", "Japan": "JPN",
    "American": "USA",
    "Ottoman": "OTT", "Turkish": "TUR",
    "Soviet": "RUS", "Russian": "RUS",
    "Danish": "DNK", "Denmark": "DNK",
}

colonial_types = ["colonial", "mandate", "dependency", "puppet"]
colonial_entries = df[df["polity_type"].isin(colonial_types)]
col_count = 0

for _, row in colonial_entries.iterrows():
    name = str(row["polity_name"])
    for keyword, metro_iso in COLONIAL_POWERS.items():
        if keyword in name:
            # Find the metropole sovereign polity active at the same time
            metro_candidates = df[
                (df["iso3_code"] == metro_iso)
                & (df["polity_type"].isin(["sovereign", "historical"]))
                & (df["start_year"] <= row["end_year"])
                & (df["end_year"] >= row["start_year"])
            ]
            if len(metro_candidates) > 0:
                # Use the longest-active candidate
                best = metro_candidates.loc[metro_candidates["duration_years"].idxmax()]
                add_edge(best["polity_code"], row["polity_code"], "colonial_ruler_of",
                         evidence=f"name contains '{keyword}'",
                         start_year=max(int(row["start_year"]), int(best["start_year"])),
                         end_year=min(int(row["end_year"]), int(best["end_year"])))
                col_count += 1
            break  # Only match the first keyword

print(f"  colonial_ruler_of edges: {col_count}")

# ── 6. Region_contains (M49 hierarchy) ────────────────────────────────

print("\n6. Extracting region_contains relations (M49 hierarchy)...")

# Build M49 code -> polity_code mapping for regions
# FAOSTAT regions have country_code matching F-prefixed polity codes
fao_region_map = {}
for _, row in fao.iterrows():
    fao_code = row["country_code"]
    iso3 = row["iso3_code"]
    if pd.notna(iso3):
        # Check if there's a region polity with matching code
        candidate = f"F{int(fao_code)}-1800-2025"
        if candidate in all_codes:
            fao_region_map[int(row["m49_code"])] = candidate
        # Also check X-prefixed codes
        if str(iso3).startswith("X"):
            candidates = df[df["iso3_code"] == iso3]
            if len(candidates) > 0:
                fao_region_map[int(row["m49_code"])] = candidates.iloc[0]["polity_code"]

# Also map continent-level M49 codes
m49_continent_map = {
    2: "X06-1800-2025",     # Africa
    19: "X21-1800-2025",    # Americas
    142: "F5300-1800-2025", # Asia
    150: "F5400-1800-2025", # Europe
    9: "F5500-1800-2025",   # Oceania
}
fao_region_map.update(m49_continent_map)

# Now link countries to their M49 regions
region_count = 0
for _, row in m49.iterrows():
    country_iso3 = row["iso3_code"]
    if pd.isna(country_iso3):
        continue

    # Find polities with this ISO3
    country_polities = df[
        (df["iso3_code"] == country_iso3)
        & (df["polity_type"].isin(["sovereign", "historical"]))
    ]
    if len(country_polities) == 0:
        continue

    # Use the most recent sovereign entry
    latest = country_polities.loc[country_polities["end_year"].idxmax()]

    # Link to each M49 region level
    for region_col in ["region1_code", "region2_code", "region3_code"]:
        r_code = row[region_col]
        if pd.notna(r_code):
            r_code = int(r_code)
            if r_code in fao_region_map:
                region_polity = fao_region_map[r_code]
                if region_polity in all_codes:
                    add_edge(region_polity, latest["polity_code"], "region_contains",
                             evidence=f"M49 code {r_code}",
                             start_year=latest["start_year"], end_year=latest["end_year"])
                    region_count += 1

print(f"  region_contains edges: {region_count}")

# ── 6b. Region hierarchy (region subregion_of region) ─────────────────

print("  Extracting M49 region hierarchy...")
region_hier_count = 0
seen_region_pairs = set()

for _, row in m49.iterrows():
    levels = []
    for code_col, name_col in [
        ("region1_code", "region1_name"),
        ("region2_code", "region2_name"),
        ("region3_code", "region3_name"),
        ("region4_code", "region4_name"),
    ]:
        code = row[code_col]
        if pd.notna(code):
            code = int(code)
            if code in fao_region_map:
                levels.append(fao_region_map[code])

    # Link child -> parent for consecutive levels
    for i in range(len(levels) - 1):
        child, parent = levels[i], levels[i + 1]
        pair = (child, parent)
        if pair not in seen_region_pairs and child in all_codes and parent in all_codes:
            add_edge(child, parent, "subregion_of",
                     evidence="M49 hierarchy",
                     start_year=1800, end_year=2025)
            seen_region_pairs.add(pair)
            region_hier_count += 1

print(f"  Region hierarchy edges: {region_hier_count}")

# ── 7. Located_in_continent ───────────────────────────────────────────

print("\n7. Extracting located_in_continent relations...")
cont_count = 0
for _, row in df[df["polity_type"] != "region"].iterrows():
    cont = row["continent"]
    if pd.notna(cont) and cont in G.nodes:
        add_edge(row["polity_code"], cont, "located_in_continent",
                 evidence="continent column",
                 start_year=row["start_year"], end_year=row["end_year"])
        cont_count += 1

print(f"  located_in_continent edges: {cont_count}")

# ── 8. Same_territory (sovereign + colonial overlap) ──────────────────

print("\n8. Extracting same_territory relations...")
same_count = 0
sovereign_types = {"sovereign", "historical"}
colonial_types_set = {"colonial", "mandate", "dependency", "puppet", "occupation"}

for iso, group in df.groupby("iso3_code"):
    if pd.isna(iso) or iso == "":
        continue
    sov = group[group["polity_type"].isin(sovereign_types)]
    col = group[group["polity_type"].isin(colonial_types_set)]

    for _, s in sov.iterrows():
        for _, c in col.iterrows():
            # Check temporal overlap
            overlap_start = max(s["start_year"], c["start_year"])
            overlap_end = min(s["end_year"], c["end_year"])
            if overlap_start <= overlap_end:
                add_edge(s["polity_code"], c["polity_code"], "same_territory",
                         evidence=f"same ISO3 ({iso}), temporal overlap",
                         start_year=overlap_start, end_year=overlap_end)
                same_count += 1

print(f"  same_territory edges: {same_count}")

# ── Summary ────────────────────────────────────────────────────────────

print(f"\n{'='*60}")
print(f"Knowledge Graph Summary")
print(f"{'='*60}")
print(f"Nodes: {G.number_of_nodes()}")
print(f"Edges: {G.number_of_edges()}")
print()

# Count by relation type
edge_counts = {}
for _, _, data in G.edges(data=True):
    rel = data.get("relation", "unknown")
    edge_counts[rel] = edge_counts.get(rel, 0) + 1

print("Edges by relation type:")
for rel, count in sorted(edge_counts.items(), key=lambda x: -x[1]):
    print(f"  {rel:25s} {count:5d}")

# Top degree nodes
print(f"\nTop 15 most connected nodes:")
degrees = sorted(G.degree(), key=lambda x: x[1], reverse=True)
for node, deg in degrees[:15]:
    name = G.nodes[node].get("polity_name", node)
    ntype = G.nodes[node].get("polity_type", "?")
    print(f"  {node:25s} {name:40s} {ntype:12s} degree={deg}")

# Connected components (undirected)
ug = G.to_undirected()
components = list(nx.connected_components(ug))
print(f"\nConnected components: {len(components)}")
sizes = sorted([len(c) for c in components], reverse=True)
print(f"  Largest: {sizes[0]}")
print(f"  Isolated nodes: {sum(1 for s in sizes if s == 1)}")

# Orphan polities (no edges at all)
orphans = [n for n in G.nodes if G.degree(n) == 0]
print(f"  Orphan nodes (no edges): {len(orphans)}")
if orphans:
    for o in orphans[:10]:
        print(f"    {o}: {G.nodes[o].get('polity_name', '?')}")

# ── Export ─────────────────────────────────────────────────────────────

os.makedirs(f"{BASE}/data/analysis", exist_ok=True)

# Edge list CSV
edges_df = pd.DataFrame(edge_log)
edges_df.to_csv(f"{BASE}/data/analysis/knowledge_graph_edges.csv", index=False)
print(f"\nSaved: data/analysis/knowledge_graph_edges.csv ({len(edges_df)} edges)")

# Node list CSV
node_records = []
for node, data in G.nodes(data=True):
    node_records.append({
        "polity_code": node,
        "polity_name": data.get("polity_name", ""),
        "polity_type": data.get("polity_type", ""),
        "continent": data.get("continent", ""),
        "start_year": data.get("start_year", ""),
        "end_year": data.get("end_year", ""),
        "iso3_code": data.get("iso3_code", ""),
        "node_type": data.get("node_type", "polity"),
        "in_degree": G.in_degree(node),
        "out_degree": G.out_degree(node),
        "total_degree": G.degree(node),
    })
nodes_df = pd.DataFrame(node_records)
nodes_df.to_csv(f"{BASE}/data/analysis/knowledge_graph_nodes.csv", index=False)
print(f"Saved: data/analysis/knowledge_graph_nodes.csv ({len(nodes_df)} nodes)")

# GraphML
nx.write_graphml(G, f"{BASE}/data/analysis/knowledge_graph.graphml")
print(f"Saved: data/analysis/knowledge_graph.graphml")

print("\nDone!")
