# WHEP Polities Research

Research-level database of historical polities for the [Who Has Eaten the Planet?](https://www.whep.eu/) (WHEP) project. Covers political entities from 1800 to 2025 with territorial boundaries, cross-referenced against multiple external datasets.

## What's here

**811 polity codes** from the WHEP R package (branch `refactor/polities`), enriched with metadata from online research and cross-referenced against COW, CShapes, Natural Earth, Cliopatria, and others.

### Data

```
data/
  whep-source/          # Raw CSVs from WHEP refactor/polities branch
    polity_codes.csv      811 polity code definitions (XXX-yyyy-YYYY format)
    polities_database_verified.csv   602 verified entries with status
    common_names.csv      1687 source-to-common-name mappings
    cshapes.csv           472 territorial boundaries with areas (1886-2019)
    faostat_regions.csv   343 FAO country/region definitions
    federico_tena_polities.csv   243 historical trade polities (1800-1938)
    historical_m49.csv    285 UN M49 historical codes
    whep_fixes.csv        116 manual overrides
    unstats_m49.csv       248 current UN M49 codes
    polities.csv          412-row output from get_polities()
  external/             # Manually compiled reference datasets
    decolonization_events.csv   96 independence events with exact dates
    empire_dissolutions.csv     17 major geopolitical transitions
    disputed_states.csv         10 disputed/unrecognized entities
    microstates.csv             10 micro-states with sovereignty dates
  compiled/             # Generated (gitignored)
    polities_master.csv         Enriched master database (run 01 to generate)
```

### R scripts

Run sequentially. Each script sources `00_setup.R` for paths and packages.

| Script | Purpose | Outputs |
|--------|---------|---------|
| `00_setup.R` | Load packages, define project paths | - |
| `01_build_master_db.R` | Enrich 811 polities with type, continent, empire, ISO codes, areas, predecessor/successor, source counts | `data/compiled/polities_master.csv` |
| `02_temporal_analysis.R` | Formation/dissolution events, active polities over time, lifespan distribution, era breakdown | 7 plots |
| `03_gap_analysis.R` | Timeline gaps/overlaps, source coverage, area completeness, prefix collisions, missing modern states | 5 plots + text report |
| `04_map_analysis.R` | World maps: coverage, earliest year, territorial complexity, empire affiliation | 5 maps |
| `05_cross_reference.R` | COW state system comparison, Natural Earth cross-reference, WHEP vs COW timeline | 1 plot + text report |

### Reference

`POLITIES_DATA_SOURCES.md` documents 14 external datasets with download URLs, schemas, temporal coverage, and licensing.

## Setup

Requires R >= 4.5. Package management via [renv](https://rstudio.github.io/renv/).

```bash
# System dependencies for sf (Ubuntu/Debian)
sudo apt install libgdal-dev libgeos-dev libproj-dev libudunits2-dev

# Install R packages
cd whep-polities
Rscript -e 'renv::restore()'
# or if no lockfile yet:
Rscript -e 'renv::install(c("readr","dplyr","ggplot2","tidyr","stringr","purrr","forcats","tibble","sf","rnaturalearth","rnaturalearthdata","scales","viridis"), prompt=FALSE)'
Rscript -e 'renv::snapshot(prompt=FALSE)'
```

## Run

```bash
Rscript R/01_build_master_db.R    # build enriched database
Rscript R/02_temporal_analysis.R  # timeline plots
Rscript R/03_gap_analysis.R       # gap analysis + report
Rscript R/04_map_analysis.R       # world maps
Rscript R/05_cross_reference.R    # COW/NE cross-reference
```

Plots go to `output/plots/`, reports to `output/reports/`.

## Data sources

The WHEP polities pipeline integrates 7 sources: Federico-Tena (1800-1938), FAOSTAT, UN M49, CShapes 2.0 (1886-2019), CShapes-Europe (1806-2023), GADM 4.1, and manual WHEP fixes. This project cross-references those against COW, Cliopatria, Natural Earth, Gleditsch-Ward, V-Dem, Polity5, Maddison, and Penn World Tables.

## Known issues

From the WHEP verified database (99.2% accuracy):

- Manchukuo end year corrected (1945, not 2025) via whep_fixes
- Denmark missing 1864 Schleswig-Holstein split (deferred)
- Two Sicilies / Kingdom Two Sicilies possible duplicate (under investigation)
- Afghanistan 1888-1919 gap (intentional, no CShapes data)
- ~17 prefix collisions (e.g. SAR = Sardinia + Sarawak); full codes are unique

## License

Research use. WHEP project funded by the European Research Council.
