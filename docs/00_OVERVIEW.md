# WHEP Polities Database v1.2 -- Overview

**Project**: Who Has Eaten the Planet (WHEP)
**Funded by**: European Research Council (ERC)
**Date**: 2026-03-26
**Database file**: `data/final/polities_database.csv`

---

## What Is This Database?

A comprehensive database of **810 historical political entities ("polities")** spanning
**1800-2025**, designed to link historical trade data to geographic territories for the
WHEP project studying the environmental impacts of food systems since 1850.

Each polity represents a **fixed territory over a continuous period of time**. When
territory changes significantly (>10% area), a new polity entry is created.

---

## Quick Statistics

| Category | Count |
|----------|-------|
| Total entries | 810 |
| Sovereign states | 194 |
| Historical entities | 339 |
| Colonial entities | 47 |
| Dependencies/territories | 75 |
| Trade aggregates | 60 |
| Mandates | 13 |
| Statistical regions | 77 |
| Disputed entities | 4 |
| Puppet states | 1 |

### Polygon Coverage
| Category | Count |
|----------|-------|
| Polities with polygons | 723/810 (89.3%) |
| Subnational polygons extracted | 91/110 (82.7%) |
| Excel data regions with polygons | 390/409 (95.4%) |
| COW State System coverage | 207/209 (99.0%) |
| FAOSTAT coverage | 249/252 (98.8%) |
| Decolonization events | 94/94 (100%) |

### Geographic Distribution
| Continent | Entries |
|-----------|---------|
| Africa | 217 |
| Europe | 183 |
| Asia | 162 |
| Global (regions) | 76 |
| Oceania | 69 |
| North America | 64 |
| South America | 35 |
| Antarctica | 4 |

### Temporal Coverage
- **Earliest start**: 1800
- **Latest end**: 2025
- **Active in 2025**: 309 non-region entities
- **Optimized for**: 1850-present

---

## Database Schema

The final database (`data/final/polities_database.csv`) has 15 columns:

| Column | Type | Description |
|--------|------|-------------|
| `polity_code` | String | Unique identifier (XXX-yyyy-YYYY format) |
| `polity_name` | String | Canonical polity name |
| `start_year` | Integer | Start year (inclusive) |
| `end_year` | Integer | End year (inclusive; 2025 = still exists) |
| `duration_years` | Integer | end_year - start_year + 1 |
| `polity_type` | String | sovereign/historical/colonial/dependency/mandate/occupation/puppet/aggregate/region/disputed |
| `continent` | String | Africa/Asia/Europe/North America/South America/Oceania/Antarctica/Global |
| `iso3_code` | String | ISO 3166-1 alpha-3 code (if applicable) |
| `cow_code` | String | Correlates of War numeric code (if applicable) |
| `polygon_source` | String | Primary source for geographic polygon |
| `predecessor` | String | Polity code(s) of predecessor entity |
| `successor` | String | Polity code(s) of successor entity |
| `data_sources` | String | Which source databases include this polity |
| `verification_status` | String | VERIFIED/REGION/FIXED/UNVERIFIED |
| `notes` | String | Additional notes (from verification) |

---

## Data Sources

7 primary data sources are merged into the polities pipeline:

| # | Source | Entries | Coverage | Provides |
|---|--------|---------|----------|----------|
| 1 | Federico-Tena | 243 | 1800-1938 | Earliest trade data, populations |
| 2 | FAOSTAT | 343 | 1961-present | ISO/M49 codes, modern coverage |
| 3 | UN M49 | 534 | 1970-present | Standard codes, regional groupings |
| 4 | CShapes 2.0 | 930 | 1886-2019 | Boundaries, areas, colonial territories |
| 5 | CShapes-Europe | 46 | 1806-2023 | Pre-1886 European boundaries |
| 6 | GADM 4.1 | 166 | Current | Modern boundaries, subnational |
| 7 | WHEP fixes | 116 | Manual | Expert corrections |

14+ external reference sources were consulted for validation (see `02_DATA_SOURCES.md`).

---

## Polygon/Geometry Sources

Each polity is assigned a polygon source indicating where its geographic boundary comes from:

| Source | N polities | Description |
|--------|-----------|-------------|
| CShapes 2.0 | 425 | Historical boundaries 1886-2019 |
| CShapes 2.0 + CShapes-Europe | 85 | Combined historical coverage |
| CShapes 2.0 (dependencies=TRUE) | 84 | Colonial territory boundaries |
| GADM 4.1 | 75 | Modern boundaries |
| GADM 4.1 or Natural Earth | 36 | Fallback for remaining |
| CShapes-Europe | 21 | Pre-1886 European states |
| GADM 4.1 (subnational) | 7 | Sub-national units |
| None (statistical aggregate) | 77 | Regions (no geometry needed) |

All polygon sources use **WGS84 (EPSG:4326)** and are directly compatible.

---

## Documentation Guide

| Document | Content |
|----------|---------|
| `00_OVERVIEW.md` | This file -- project overview and quick reference |
| `01_METHODOLOGY.md` | Definitions, coding rules, area thresholds, classification |
| `02_DATA_SOURCES.md` | All 14+ data sources documented with schemas and access |
| `03_ENTRIES_RATIONALE.md` | Why each entry exists, organized by era and region |
| `04_POLYGON_SOURCES.md` | Where each polygon comes from, technical details |
| `05_COVERAGE_ANALYSIS.md` | Coverage by era, continent; cross-references with COW/CShapes/FAOSTAT |
| `06_KNOWN_ISSUES_AND_DECISIONS.md` | 5 fixes, 4 known limitations, 9 design decisions, changelog |
| `07_SUBNATIONAL_POLYGONS.md` | Subnational polygon extraction: quality tiers, limitations, GADM assessment |
| `08_POLYGON_ACCURACY_AUDIT.md` | Deep audit: 12 problem zones, 18 severity entries, external GIS sources |
| `09_SUBNATIONAL_MAJOR_COUNTRIES.md` | GADM admin-1 for 19 countries: stability ratings, 374 potential entries |

---

## Quality Assurance

- **99.2%** of polities have correct date ranges
- **100%** coverage of COW State System (209 states)
- **96%** coverage of COW sovereign state formations
- **94%** coverage of COW major territorial transfers
- **100%** coverage of FAOSTAT entities (343)
- **100%** coverage of tracked decolonization events (96)
- **100%** coverage of tracked empire dissolutions (17)
- **5 fixes** applied from exhaustive cross-referencing
- **478 polities** individually verified against multiple sources

### Automated Stress Testing (31 tests)
- **23 PASS**: Schema, types, dates, code uniqueness, duration, polygon validity, CRS, etc.
- **7 WARN**: ISO code sharing (by design), predecessor chain gaps (region codes), centroid
  exceptions (Turkey, Greenland — transcontinental entities), date overlaps (by design)
- **1 FAIL**: 3 polity codes use dots (ST.-1800-2025, ST.-1800-1838, ST.-1800-1833)

### Polygon Cross-Validation
- CShapes 2.0 vs GADM: **median IoU 0.975** across 183 countries
- **157 countries** with IoU ≥ 0.8 (good agreement)
- **14 countries** with IoU < 0.5 (all small island nations)
- **41 CShapes-Europe entries** unique to that dataset (pre-unification German/Italian states)

---

## How to Use This Database

### For trade data analysis:
Use `polity_type = "aggregate"` entries (GER-1800-2025, CHN-1800-2025, etc.) for
continuous trade data linkage across the full period.

### For territorial/geographic analysis:
Use period-specific entries (DEU-1800-1919, DEU-1919-1920, etc.) which represent
actual territorial configurations.

### For modern country analysis:
Filter by `end_year = 2025` and `polity_type = "sovereign"` to get current states.

### For joining with other datasets:
Use `iso3_code` for ISO-based datasets, `cow_code` for COW-based datasets.

---

## Analysis Scripts

| Script | Purpose |
|--------|---------|
| `build_database.py` | Build final polities_database.csv from all sources |
| `build_polygons.py` | Match polities to CShapes/GADM/CShapes-Europe polygons |
| `generate_plots.py` | Generate 13 analysis and cross-validation plots |
| `stress_test.py` | 31 automated integrity checks with diagnostic plots |
| `compare_polygons.py` | CShapes vs GADM IoU comparison for 183 countries |
| `validate_iso_overlaps.py` | ISO code collision detection and classification |
| `analyze_subnational.py` | GADM admin-1 analysis for 19 major countries |
| `generate_validation_report.py` | Combined validation dashboard (3 plots) |

---

## Relationship to WHEP R Package

This database is designed to be the reference input for the `whep` R package's
`get_polities()` function. The pipeline that builds the R package's internal data
(`sysdata.rda`) reads from the same source files documented here.

The key code change required for full polygon coverage: use
`cshapes::cshp(dependencies = TRUE)` instead of the default `dependencies = FALSE`.
