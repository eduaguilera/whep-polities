# Reproducibility Guide

This document explains how to reproduce the WHEP polities database from scratch,
what external datasets are required, and where to obtain them.

---

## Quick start (using the release)

The simplest way to use the database is to download the pre-built files from the
[GitHub Release](https://github.com/lbm364dl/whep-polities/releases/tag/v2.5):

- `polities_database.csv` -- the full database (1,420 entries, 15 columns)
- `polities_database.gpkg` -- GeoPackage with polygon geometries for all entries

The CSV is also included in the git repository at `data/final/polities_database.csv`.
The GeoPackage is too large for git (196 MB) and is distributed as a release asset.

---

## Rebuilding from scratch

### Prerequisites

**Software**:
- R >= 4.5
- System libraries: `libgdal-dev libgeos-dev libproj-dev libudunits2-dev` (Ubuntu/Debian)
- R packages managed by `renv` (run `renv::restore()` to install)

**External datasets** (not redistributable, must be downloaded by the user):

| Dataset | Size | Source | License | Used by |
|---------|------|--------|---------|---------|
| GADM 4.1 | 1.4 GB (zip) | [gadm.org](https://gadm.org/download_world.html) -- download "GeoPackage" format | Free for academic use | R/17 (Japan, UK, Saar, Memel subnational) |
| Paine et al. (2024) | ~1 MB | [Harvard Dataverse doi:10.7910/DVN/9QJVJ1](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/9QJVJ1) | Academic use | R/11 (46 pre-colonial African states) |
| CHGIS v6 | ~50 MB | [Harvard Dataverse doi:10.7910/DVN/ST5KKM](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/ST5KKM) -- download "1820 Layers UTF8 Encoding" | Academic use | R/13 (26 Qing Dynasty provinces) |
| CShapes 2.0 | ~20 MB | Downloaded automatically by the `cshapes` R package from ETH Zurich | CC BY 4.0 | R/01 (main polygon source) |

The Cliopatria (Seshat) dataset is included in the repository at
`data/source/cliopatria/cliopatria.geojson.zip` (52 MB, CC BY 4.0).

### Setup

```bash
# Clone the repository
git clone https://github.com/lbm364dl/whep-polities.git
cd whep-polities

# Install system dependencies (Ubuntu/Debian)
sudo apt install libgdal-dev libgeos-dev libproj-dev libudunits2-dev

# Install R packages
Rscript -e 'renv::restore()'

# Download and place external datasets
# 1. GADM: download gadm_410-gpkg.zip from gadm.org, extract to inputs/gadm_410.gpkg
# 2. Paine et al.: download from Harvard Dataverse, save as inputs/paine_et_al.zip
# 3. CHGIS: download "1820 Layers" from Harvard Dataverse, save as inputs/chgis.zip
```

Update `R/00_setup.R` if your GADM path differs from the default.

### Build pipeline

The pipeline has two phases: base build (R/01-R/16) and enrichment (R/17-R/24).

**Phase 1: Base build** (generates intermediate geodata files):

```bash
Rscript R/00b_fetch_cshapes.R             # Fetch CShapes 2.0 (COW, deps=TRUE) -> cshapes2_full.gpkg
Rscript R/01_build_master_db.R            # Build enriched base database
Rscript R/06_add_subnational.R            # Add GADM admin-1 subnational entries
Rscript R/11_integrate_precolonial_polygons.R  # Paine et al. African states
Rscript R/12_integrate_cliopatria_polygons.R   # 4 Cliopatria polities
Rscript R/13_integrate_chgis_provinces.R       # Qing Dynasty provinces
Rscript R/14_integrate_historical_subnational.R # US, Brazil, Spain historical
Rscript R/15_build_unified_polygons.R     # Merge all polygon sources
Rscript R/16_data_integrity_fixes.R       # Fixes, aggregates, IND->IDN rename
```

**Phase 2: Enrichment** (adds entries and improves polygons):

```bash
Rscript R/17_add_new_polygons.R           # Japan/UK subnational, interwar, polygon fixes
Rscript R/18_improve_african_coverage.R   # Verify African entries, add chains
Rscript R/19_verify_remaining_and_fix_chains.R  # Global verification, chain fixes
Rscript R/20_japan_empire_and_nigeria.R   # Japan 4-period split, Nigeria pre-colonial
Rscript R/21_cliopatria_polygon_fixes_and_mexico.R  # 6 polygon accuracy fixes, Mexico split
Rscript R/22_territorial_splits.R         # NLD, NPL, OMN, COL territorial splits
Rscript R/23_usa_russia_splits.R          # USA 4-period, Russia 2-period splits
Rscript R/24_cliopatria_broad_pass.R      # 12 Italian/German pre-1886 polygon fixes
```

**Phase 3: Rebuild outputs** (after enrichment):

```bash
Rscript R/15_build_unified_polygons.R     # Rebuild unified GeoPackage
Rscript R/07_build_knowledge_graph.R      # Build knowledge graph
Rscript R/08_stress_test.R               # Validate (31 automated tests)
```

**Analysis and visualization** (optional):

```bash
Rscript R/02_temporal_analysis.R
Rscript R/03_gap_analysis.R
Rscript R/04_map_analysis.R
Rscript R/05_cross_reference.R
Rscript R/09_visualize_knowledge_graph.R
Rscript R/10_analysis_plots.R
```

### Important notes on reproducibility

1. **The CSV in git is the final state.** Scripts R/17-R/24 are idempotent: they
   check for existing entries before adding and skip duplicates. Running them on
   the already-complete CSV will not corrupt it.

2. **CShapes data is fetched by** `R/00b_fetch_cshapes.R`, which calls
   `cshapes::cshp(useGW = FALSE, dependencies = TRUE)` (v2.0, Schvitz et al.
   2022) and writes `data/geodata/cshapes2_full.gpkg`. Note that WHEP uses the
   **COW-based** distribution (the R package defaults to `useGW = TRUE`, which
   is *not* what WHEP loads) — the choice is load-bearing because COW and GW
   differ on pre-1945 independence dates (see
   `wiki/log.md § 2026-04-11 decision-cshapes-is-cow-based` for the evidence
   and `wiki/sources/cshapes-2.0.md` for the reproducibility proof). If the
   ETH Zurich server or package changes, results may differ; the file in
   `data/geodata/` captures the exact version used.

3. **GADM path**: R/00_setup.R defines two GADM paths. Update `gadm41_path` to
   point to your local GADM 4.1 GeoPackage. If GADM is unavailable, R/17 will
   skip Japan/UK subnational entries (all other operations work without GADM).

4. **Cliopatria extraction**: Scripts R/21-R/24 read the extracted GeoJSON file.
   If only the zip is present, the scripts extract it to a temporary directory
   automatically.

---

## File inventory

### In the git repository

| Path | Description |
|------|-------------|
| `data/whep-source/*.csv` | 11 source CSVs from the WHEP R package |
| `data/external/*.csv` | 5 manually compiled reference datasets |
| `data/final/polities_database.csv` | Final database (1,420 entries) |
| `data/analysis/*.csv` | 16 analysis and validation reports |
| `data/source/cliopatria/cliopatria.geojson.zip` | Cliopatria v0.1.3 (52 MB) |
| `R/*.R` | 24 R scripts (full pipeline) |
| `docs/*.md` | 15 documentation files |
| `renv.lock` | R package version lock file |
| `inputs/README.md` | Instructions for obtaining external datasets |

### In the GitHub Release (v2.5)

| File | Size | Description |
|------|------|-------------|
| `polities_database.gpkg` | ~196 MB | Unified GeoPackage (CSV + polygons) |
| `polities_database.csv` | ~218 KB | Database CSV (also in git) |

### Generated locally (not distributed)

| Path | Size | Generated by |
|------|------|-------------|
| `data/geodata/polities_polygons.gpkg` | 191 MB | R/01 + R/06 + R/11-14 + R/17 |
| `data/geodata/subnational_polygons.gpkg` | 164 MB | R/06 |
| `data/geodata/cshapes2_full.gpkg` | 21 MB | R/00b_fetch_cshapes.R (cshapes::cshp useGW=FALSE deps=TRUE) |
| `data/geodata/cshapes2_sovereign.gpkg` | 17 MB | R/01 |
| `data/geodata/precolonial_polygons.gpkg` | 2 MB | R/11 |
| `data/geodata/cliopatria_polygons.gpkg` | 116 KB | R/12 |
| `data/geodata/chgis_qing_provinces.gpkg` | 2.5 MB | R/13 |
| `data/geodata/us_historical_states.gpkg` | 376 KB | R/14 |
| `data/geodata/brazil_historical_states.gpkg` | 748 KB | R/14 |
| `data/geodata/spain_provinces.gpkg` | 608 KB | R/14 |
| `data/compiled/polities_master.csv` | ~100 KB | R/01 |

---

## Data sources and citations

| Source | Citation | Used for |
|--------|----------|----------|
| CShapes 2.0 | Schvitz, G. et al. (2022). "Mapping the International System, 1886-2019." *Journal of Conflict Resolution* 66(1), 144-179. | Primary polygon source (1886-2019) |
| GADM 4.1 | Global Administrative Areas (2022). University of California, Davis. gadm.org | Modern boundaries, subnational |
| Paine et al. (2024) | Paine, J., Qiu, Y., & Ricart-Huguet, J. (2024). "Endogenous Colonial Borders." *American Political Science Review* 119(1), 1-20. doi:10.7910/DVN/9QJVJ1 | 46 pre-colonial African states |
| CHGIS v6 | Fairbank Center for Chinese Studies, Harvard & Center for Historical Geographical Studies, Fudan University (2016). doi:10.7910/DVN/ST5KKM | Qing Dynasty provinces |
| Cliopatria (Seshat) | Seshat Global History Databank (2025). github.com/Seshat-Global-History-Databank/cliopatria. CC BY 4.0. | Time-stepped historical polygons |
| Federico-Tena | Federico, G. & Tena-Junguito, A. (2019). "World Trade, 1800-1938." *Journal of World Trade* | Historical trade polities |
| CShapes-Europe | Modifications of CShapes for European states pre-1886 | Pre-1886 European boundaries |
| Natural Earth | naturalearthdata.com. Public domain. | Fallback boundaries |
| COW | Correlates of War Project. correlatesofwar.org | State system cross-reference |
| UN M49 | United Nations Statistics Division. unstats.un.org | Standard country codes |
| FAOSTAT | Food and Agriculture Organization. fao.org/faostat | Agricultural production regions |

---

## License

Research use. WHEP project funded by the European Research Council (ERC).

External datasets retain their original licenses (see table above). The WHEP
polities database itself (the CSV, documentation, and R scripts) is provided
for academic research purposes.
