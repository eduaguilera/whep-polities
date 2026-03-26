# Knowledge Graph Documentation

---

## Overview

The WHEP polities knowledge graph models **relations between political entities** as a
directed graph. It captures temporal succession, territorial hierarchy, colonial control,
regional membership, and other structural relationships between the 1,026 polities in the
database.

### Graph Statistics

| Metric | Value |
|--------|-------|
| Nodes | 1,034 (1,026 polities + 8 continent nodes) |
| Edges | 1,900 |
| Relation types | 9 |
| Connected components | 53 |
| Largest component | 982 nodes |
| Isolated nodes | 52 (specialized FAOSTAT regions) |

---

## Relation Types

### 1. `predecessor_of` (13 edges)

**Direction**: predecessor → successor polity

**Source**: `predecessor` column in polities_database.csv

**Example**: `SUD-1956-2011` → `SDN-2011-2025` (Sudan splitting)

**Note**: 15 broken references to `F228-1940-1991` (USSR region code not in non-region
subset). These represent the post-Soviet successor states.

---

### 2. `successor_of` (14 edges)

**Direction**: polity → successor polity

**Source**: `successor` column in polities_database.csv

**Example**: `AUH-1908-1918` → `AUT-1918-2025` (Austria-Hungary → Austria)

---

### 3. `subregion_of` (237 edges)

**Direction**: child → parent

Two sources:
- **Subnational entries** (216 edges): Present-day admin-1 units → parent sovereign state.
  Extracted from the `notes` field `Parent: XXX-YYYY-ZZZZ`.
- **M49 region hierarchy** (21 edges): Region → parent region (e.g., Eastern Africa →
  Africa → World).

**Example**: `USCA-1959-2025` (California) → `USA-1959-2025` (United States)

---

### 4. `aggregate_covers` (50 edges)

**Direction**: aggregate entry → period-specific entry

An aggregate entry (e.g., `GER-1800-2025` for Germany) covers all period-specific entries
for the same ISO3 code whose date ranges fall within the aggregate's range.

**Example**: `GER-1800-2025` → `DEU-1990-2025` (aggregate Germany covers modern Germany)

---

### 5. `temporal_next` (163 edges)

**Direction**: earlier period → later period

Same ISO3 code, same or similar polity type, with a gap of ≤ 5 years between end of the
earlier entry and start of the later entry. Captures the temporal chain of a country's
political evolution.

**Example**: `CHN-1800-1895` → `CHN-1895-1912` (Qing China → late Qing)

---

### 6. `colonial_ruler_of` (36 edges)

**Direction**: metropole → colony/mandate/dependency

Inferred from polity name keywords: "British" → GBR, "French" → FRA, "German" → DEU,
"Spanish" → ESP, "Portuguese" → PRT, "Dutch" → NLD, "Italian" → ITA, "Belgian" → BEL,
"Japanese" → JPN, etc. The metropole is matched to the sovereign/historical polity active
in the same period.

**Example**: `GBR-1920-2025` → `BRI-1800-1966` (UK → British Bechuanaland)

---

### 7. `region_contains` (420 edges)

**Direction**: M49 region polity → country polity

Derived from the UN M49 hierarchy. Each country is linked to its M49 sub-region, region,
and macro-region polities (where those exist in the database as FAOSTAT region entries).

**Example**: `F5101-1800-2025` (Eastern Africa) → `KEN-1963-2025` (Kenya)

---

### 8. `located_in_continent` (949 edges)

**Direction**: polity → continent pseudo-node

Every non-region polity links to its `continent` value. The 8 continent pseudo-nodes
(Africa, Asia, Europe, North America, South America, Oceania, Antarctica, Global) serve as
geographic anchors in the graph.

---

### 9. `same_territory` (18 edges)

**Direction**: sovereign/historical → colonial/mandate/dependency

Identifies entries with the same ISO3 code and overlapping time periods but different
polity types, indicating that the same geographic territory was simultaneously claimed by
both a sovereign entity and a colonial/mandate entry.

**Example**: Two entities sharing the same ISO3 code and active in overlapping years,
one classified as sovereign and the other as colonial.

---

## Output Files

| File | Format | Content |
|------|--------|---------|
| `data/analysis/knowledge_graph_edges.csv` | CSV | All edges with source, target, relation, evidence, dates |
| `data/analysis/knowledge_graph_nodes.csv` | CSV | All nodes with attributes and degree metrics |
| `data/analysis/knowledge_graph.graphml` | GraphML | Full graph for Gephi/Cytoscape/igraph |

---

## Visualizations

| Plot | Description |
|------|-------------|
| `kg_01_relation_type_distribution.png` | Bar chart of edge counts by relation type |
| `kg_02_degree_distribution.png` | Degree histogram + top-20 most connected polities |
| `kg_03_successor_chains.png` | Temporal chains for 8 selected countries |
| `kg_04_colonial_empires.png` | Network of colonial metropoles and their territories |
| `kg_05_subnational_hierarchy.png` | Star graphs of 6 countries and their admin-1 units |
| `kg_06_graph_metrics_summary.png` | Dashboard: temporal edges, node types, components, degree scatter |

---

## Key Findings

1. **Russia is the most connected polity** (87 edges) due to its 83 subnational units
   plus sovereign/temporal edges.

2. **The largest connected component contains 982 of 1,034 nodes** (95%), showing that
   the polities database is highly interconnected through temporal, territorial, and
   hierarchical relations.

3. **52 isolated nodes** are specialized FAOSTAT statistical regions (fishing areas,
   economic groupings like "Annex I countries", "European Union") that don't participate
   in the M49 geographic hierarchy.

4. **163 temporal_next edges** trace the complete territorial evolution of countries
   through their period-specific entries.

5. **36 colonial relationships** were automatically inferred from polity naming patterns,
   capturing the major colonial empires (British, French, German, Spanish, Portuguese,
   Dutch, Italian, Belgian, Japanese).

---

## How to Use

### Load in R (igraph)

```r
library(igraph)
g <- read_graph("data/analysis/knowledge_graph.graphml", format = "graphml")

# Find all successors of the Ottoman Empire
ottoman <- "OTT-1800-1912"
edges_out <- E(g)[from(ottoman)]
successors <- ends(g, edges_out[edge_attr(g, "relation", edges_out) == "successor_of"])[, 2]

# Get all subnational units of the USA
edges_in <- E(g)[to("USA-1959-2025")]
usa_subs <- ends(g, edges_in[edge_attr(g, "relation", edges_in) == "subregion_of"])[, 1]

# Trace temporal chain for Germany
chain <- "DEU-1800-1919"
repeat {
  e_out <- E(g)[from(tail(chain, 1))]
  nexts <- ends(g, e_out[edge_attr(g, "relation", e_out) == "temporal_next"])[, 2]
  if (length(nexts) == 0) break
  chain <- c(chain, nexts[1])
}
```

### Load in Gephi

Open `knowledge_graph.graphml` directly in Gephi for interactive exploration.

---

## Scripts

| Script | Purpose |
|--------|---------|
| `R/07_build_knowledge_graph.R` | Extract all 9 relation types, build graph, export CSV + GraphML |
| `R/09_visualize_knowledge_graph.R` | Generate 6 visualization plots |
