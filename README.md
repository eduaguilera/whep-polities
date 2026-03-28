# WHEP Polities Research (v1.0)

Research-level database of historical polities for the [Who Has Eaten the Planet?](https://www.whep.eu/) (WHEP) project. Covers political entities from 1800 to 2025 with territorial boundaries, cross-referenced against multiple external datasets.

## Key statistics

| Metric | Value |
|--------|-------|
| Total polities | 1,317 |
| Non-region polities | 1,240 |
| With polygon geometry | 1,139 / 1,240 (91.9%) |
| Subnational entries | 422 |
| Verified entries | 1,317 / 1,317 (100%) |
| Knowledge graph | 1,325 nodes, 2,696 edges (9 relation types) |
| Temporal coverage | 1800-2025 |
| Trade data coverage | 331 / 331 geographies matched (100%) |

## What's here

### Data

```
data/
  whep-source/            # Raw CSVs from WHEP refactor/polities branch
    polity_codes.csv        811 polity code definitions (XXX-yyyy-YYYY format)
    polities_database_verified.csv   602 verified entries with status
    common_names.csv        1,687 source-to-common-name mappings
    cshapes.csv             472 territorial boundaries with areas (1886-2019)
    faostat_regions.csv     343 FAO country/region definitions
    federico_tena_polities.csv   243 historical trade polities (1800-1938)
    historical_m49.csv      285 UN M49 historical codes
    whep_fixes.csv          116 manual overrides
    unstats_m49.csv         248 current UN M49 codes
    polities.csv            412-row output from get_polities()
  external/               # Manually compiled reference datasets
    decolonization_events.csv   96 independence events with exact dates
    empire_dissolutions.csv     17 major geopolitical transitions
    disputed_states.csv         10 disputed/unrecognized entities
    microstates.csv             10 micro-states with sovereignty dates
    cow_state_system.csv        209 COW state system entries
  compiled/               # Intermediate (gitignored)
    polities_master.csv         Enriched base database (811 entries, run 01)
  final/                  # Main output
    polities_database.csv       Final database (1,236 entries, 15 columns)
    polities_database.gpkg      Unified GeoPackage with all geometries
  geodata/                # Polygon source files (gitignored, large)
    polities_polygons.gpkg      Main polygon collection (~939 polities)
    subnational_polygons.gpkg   Admin-1 boundaries (371 entries)
    precolonial_polygons.gpkg   Paine et al. (2024) 46 African states
    cliopatria_polygons.gpkg    Seshat/Cliopatria 4 historical polities
    chgis_qing_provinces.gpkg   CHGIS v6 Qing provinces (26 entries)
    us_historical_states.gpkg   US states 1800-1958 (51 entries)
    brazil_historical_states.gpkg  Brazil states 1872-1987 (26 entries)
    spain_provinces.gpkg        Spain provinces 1833-2025 (52 entries)
    cshapes2_full.gpkg          CShapes 2.0 complete (1886-2019)
    cshapes2_sovereign.gpkg     CShapes 2.0 sovereign only
  analysis/               # Reports and plots
    knowledge_graph_edges.csv   2,383 edges (9 relation types)
    knowledge_graph_nodes.csv   1,244 nodes
    knowledge_graph.graphml     GraphML for Gephi/Cytoscape
    polygon_quality_report.csv  Geometry validation results
    stress_test_results.csv     31 automated integrity checks
    plots/                      72 PNG analysis visualizations
```

### R scripts

Run sequentially. Each script sources `00_setup.R` for paths and packages.

| Script | Purpose | Key outputs |
|--------|---------|-------------|
| `00_setup.R` | Load packages, define project paths | - |
| `01_build_master_db.R` | Enrich 811 polities with type, continent, empire, ISO codes, areas, predecessor/successor | `data/compiled/polities_master.csv` |
| `02_temporal_analysis.R` | Formation/dissolution events, active polities over time, lifespan distribution | 7 plots |
| `03_gap_analysis.R` | Timeline gaps/overlaps, source coverage, area completeness | 5 plots + report |
| `04_map_analysis.R` | World maps: coverage, earliest year, territorial complexity, empires | 5 maps |
| `05_cross_reference.R` | COW state system comparison, Natural Earth cross-reference | 1 plot + report |
| `06_add_subnational.R` | Add GADM admin-1 entries for 6 countries (USA, CAN, BRA, AUS, CHN, RUS) | Updated CSV + GeoPackage |
| `07_build_knowledge_graph.R` | Build 9-relation knowledge graph (1,244 nodes, 2,383 edges) | CSV + GraphML |
| `08_stress_test.R` | 31 automated integrity checks | `stress_test_results.csv` |
| `09_visualize_knowledge_graph.R` | Knowledge graph visualizations | 6 plots |
| `10_analysis_plots.R` | Consolidated analysis: temporal, quality, coverage | 12 plots |
| `11_integrate_precolonial_polygons.R` | Integrate 46 Paine et al. (2024) pre-colonial African states | `precolonial_polygons.gpkg` |
| `12_integrate_cliopatria_polygons.R` | Integrate 4 Cliopatria (Seshat) historical polities | `cliopatria_polygons.gpkg` |
| `13_integrate_chgis_provinces.R` | Integrate 26 Qing Dynasty province boundaries (CHGIS v6) | `chgis_qing_provinces.gpkg` |
| `14_integrate_historical_subnational.R` | Add 129 historical subnational (US, Brazil, Spain) | 3 GeoPackage files |
| `15_build_unified_polygons.R` | Merge all polygon sources into unified GeoPackage | `polities_database.gpkg` |
| `16_data_integrity_fixes.R` | Fix pred/succ links, add aggregates, fill temporal gaps, rename IDN | Updated CSV + GeoPackage |
| `17_add_new_polygons.R` | Add Japan/UK subnational, interwar entities, easy polygon fills | Updated CSV + GeoPackage |
| `18_improve_african_coverage.R` | Verify Paine/CShapes entries, add predecessor/successor chains, polygon warnings | Updated CSV |

### External data (not redistributable)

Download into `inputs/` before running scripts 11-13:

| File | Source | Used by |
|------|--------|---------|
| `paine_et_al.zip` | [Harvard Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/9QJVJ1) | Script 11 |
| `cliopatria.geojson.zip` | Seshat GitHub / Cliopatria GeoJSON | Script 12 |
| `chgis.zip` | [Harvard Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/ST5KKM) | Script 13 |

### Documentation

See `docs/` for 15 comprehensive documents covering methodology, data sources, polygon accuracy, known issues, gap analysis, and knowledge graph design.

## Setup

Requires R >= 4.5. Package management via [renv](https://rstudio.github.io/renv/).

```bash
# System dependencies for sf (Ubuntu/Debian)
sudo apt install libgdal-dev libgeos-dev libproj-dev libudunits2-dev

# Install R packages
cd whep-polities
Rscript -e 'renv::restore()'
```

## Run

```bash
# Core pipeline (build from source data)
Rscript R/01_build_master_db.R
Rscript R/02_temporal_analysis.R
Rscript R/03_gap_analysis.R
Rscript R/04_map_analysis.R
Rscript R/05_cross_reference.R

# Subnational and polygon integration
Rscript R/06_add_subnational.R
Rscript R/11_integrate_precolonial_polygons.R
Rscript R/12_integrate_cliopatria_polygons.R
Rscript R/13_integrate_chgis_provinces.R
Rscript R/14_integrate_historical_subnational.R

# Build unified output and apply fixes
Rscript R/15_build_unified_polygons.R
Rscript R/16_data_integrity_fixes.R
Rscript R/17_add_new_polygons.R

# Analysis and validation
Rscript R/07_build_knowledge_graph.R
Rscript R/08_stress_test.R
Rscript R/09_visualize_knowledge_graph.R
Rscript R/10_analysis_plots.R
```

Plots go to `data/analysis/plots/`, reports to `output/reports/`.

## Data sources

The WHEP polities pipeline integrates 7 primary sources: Federico-Tena (1800-1938), FAOSTAT, UN M49, CShapes 2.0 (1886-2019), CShapes-Europe (1806-2023), GADM 4.1, and manual WHEP fixes. Additional polygon sources: Paine et al. (2024) pre-colonial African states, Cliopatria/Seshat historical polities, CHGIS v6 Qing provinces, USAboundaries/Newberry, geobr/IBGE, and mapSpain/IGN.

Cross-referenced against COW, Natural Earth, Gleditsch-Ward, V-Dem, Polity5, Maddison, and Penn World Tables.

## Known issues

- Afghanistan 1888-1919 gap (intentional, no CShapes data for this period)
- ~17 prefix collisions (e.g. SAR = Sardinia + Sarawak); full polity codes are unique
- 235 entries UNVERIFIED (primarily African historical/colonial)
- Pre-1886 polygon accuracy limitations (CShapes starts at 1886; earlier polygons are back-projected)
- See `docs/06_KNOWN_ISSUES_AND_DECISIONS.md` and `docs/08_POLYGON_ACCURACY_AUDIT.md` for details

## License

Research use. WHEP project funded by the European Research Council.
