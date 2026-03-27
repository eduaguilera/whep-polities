# Data Sources Reference

This document describes every data source consulted in building the WHEP polities
database, including what each source provides, its temporal coverage, and how it
contributed to the final database.

---

## 1. Primary Internal Sources

These are the datasets directly merged into the polities pipeline.

### 1.1 Federico-Tena Historical Trade Database

- **Entries**: 243 polities
- **Coverage**: 1800-1938
- **Content**: Historical trade entities with population estimates
- **Role**: Provides the earliest temporal coverage. Many polities have start_year
  derived from when they first appear in Federico-Tena trade data.
- **Key characteristics**:
  - Includes colonial trade groupings (French West Africa, British East Africa, etc.)
  - Includes pre-unification Italian states and the Germany/Zollverein aggregate
  - End years sometimes uncertain (NA defaults to 2025 -- source of Manchukuo bug)
  - Some entities use non-standard names ("CapoVerde", "Quatar", "Maldive")
  - Contains population estimates (in thousands) at the start year of data
- **Citation**: Federico, G. and Tena-Junguito, A. (2019). "World trade, 1800-1938:
  a new synthesis." Revista de Historia Economica / Journal of Iberian and Latin
  American Economic History, 37(1), 9-41.

### 1.2 FAOSTAT Country/Region Definitions

- **Entries**: 343 countries and regions
- **Coverage**: 1961-present
- **Content**: Modern country definitions with M49, ISO2, ISO3 codes
- **Role**: Provides standard codes (ISO, M49) for modern entities and defines
  aggregate statistical regions.
- **Key characteristics**:
  - ~250 actual countries/territories + ~93 aggregate regions
  - Regions use F-prefixed codes (e.g., F5300 for Asia, F5400 for Europe)
  - Includes start/end years for entities that appeared/dissolved within FAOSTAT coverage
  - Historical entities: USSR (F228), Yugoslav SFR (F248), Czechoslovakia (F51)
- **Source**: Food and Agriculture Organization of the United Nations

### 1.3 UN M49 Standard Country Codes

- **Entries**: 285 (historical) + 249 (current) = 534 total
- **Coverage**: 1970-present (historical), current (unstats)
- **Content**: UN standard country and area codes
- **Role**: Provides M49 numeric codes and validates country existence periods
- **Key characteristics**:
  - `historical_m49.csv`: 285 entries including dissolved states
  - `unstats_m49.csv`: 249 current standard entries
  - Geographic groupings (macro-regions, sub-regions)
- **Source**: United Nations Statistics Division

### 1.4 CShapes 2.0

- **Entries**: ~930 (with dependencies=TRUE), ~315 (without)
- **Coverage**: 1886-2019
- **Content**: Historical country boundaries with area, capital, status
- **Role**: Primary source for geographic boundaries and territorial change detection
- **Key characteristics**:
  - MULTIPOLYGON geometries in WGS84
  - Status field distinguishes sovereign states from colonies/dependencies
  - Owner field identifies colonial power (GW code)
  - Monthly precision internally (aggregated to yearly in pipeline)
  - Area calculated from polygons in km2
- **Citation**: Schvitz, G., Girardin, L., Ruegg, S., Weidmann, N.B., Cederman,
  L.-E., and Gleditsch, K.S. (2022). "Mapping the International System, 1886-2019:
  The CShapes 2.0 Dataset." Journal of Conflict Resolution, 66(1), 144-161.
- **R package**: `cshapes` (CRAN)

### 1.5 CShapes-Europe Historical Extension

- **Entries**: ~46 European entities
- **Coverage**: 1806-2023
- **Content**: Pre-1886 European state boundaries
- **Stored as**: `cshapes_europe_geometries.gpkg` (274 KB)
- **Role**: Fills the pre-1886 gap for European pre-unification states
- **Key characteristics**:
  - Italian pre-unification states (Kingdom of Naples, Piedmont, etc.)
  - German pre-unification states
  - Pre-1864 Denmark with Schleswig-Holstein
  - Ottoman European territories

### 1.6 GADM 4.1

- **Entries**: 166 downloaded territories (level 0 and level 1)
- **Coverage**: Current snapshot
- **Content**: Administrative boundaries at multiple levels
- **Stored as**: `gadm_geometries.gpkg` (22.3 MB) + 166 GeoJSON cache files
- **Role**: Provides modern boundaries for territories not in CShapes
- **Key characteristics**:
  - 6 administrative levels (L0 = country, L1-L5 = subdivisions)
  - Higher resolution (~1:100K) than CShapes (~1:1M)
  - Simplified to ~1 km tolerance for sysdata.rda storage
- **Source**: https://gadm.org/

### 1.7 WHEP Manual Fixes

- **Entries**: 116 corrections
- **Content**: Manual overrides for dates, boundaries, and special cases
- **Role**: Highest-priority corrections applied after automated processing
- **Categories**:
  - Date corrections (Manchukuo end year, Ionian Islands, Kokand)
  - Backward compatibility entries for CShapes dependencies=TRUE
  - Independence year standardizations
  - German/Italian pre-unification state entries
  - Other historical entity entries (Ottoman Empire, Cracow, etc.)

### 1.8 Common Names Mapping

- **Entries**: 1,687 mappings
- **Content**: Maps source-specific names to canonical WHEP common names
- **Role**: Name harmonization across all 7 data sources
- **Structure**: `original_name, source, common_name`
- **Sources mapped**: cshapes (472), faostat (343), m49 (285), federico_tena (243),
  gadm (182), whep (116), cshapes_europe (46)

---

## 2. External Reference Sources

These sources were consulted for cross-referencing, validation, and gap-filling but
are not directly merged into the pipeline.

### 2.1 Correlates of War (COW) State System Membership v2024

- **Entries**: 209+ states
- **Coverage**: 1816-2024
- **Content**: States recognized as members of the international system
- **Role**: Primary validation reference for sovereign state existence periods
- **Key characteristics**:
  - Uses COW numeric codes (2-digit for Americas, 200-395 for Europe, etc.)
  - Includes start/end dates for system membership
  - Membership criteria: population > 500,000 (post-1920) or diplomatic recognition
- **Source**: https://correlatesofwar.org/data-sets/state-system-membership/

### 2.2 COW Territorial Change Dataset v6

- **Entries**: 381 territorial transfers
- **Coverage**: 1816-2018
- **Content**: Every territorial transfer with gainer/loser/area/process
- **Role**: Validated territorial boundaries and change dates
- **Key characteristics**:
  - Area data in km2 for each transfer
  - Process codes: conquest, cession, secession, unification, mandate, etc.
  - Used to verify that WHEP captures all major territorial changes
- **Coverage of COW by WHEP**: 96% of sovereign formations, 94% of major transfers,
  85% of colonial acquisitions, 13% of sub-threshold changes
- **Source**: https://correlatesofwar.org/data-sets/territorial-change/

### 2.3 Gleditsch & Ward State List

- **Coverage**: 1816-present
- **Content**: Revised COW state list with microstate flagging
- **Role**: Cross-reference for state existence periods
- **Key difference from COW**: Lower population threshold, includes more microstates
- **Source**: https://ksgleditsch.com/statelist.html

### 2.4 Cliopatria

- **Entries**: 2,905 (2,694 from 1860+)
- **Coverage**: 3400 BCE-2024 CE
- **Content**: Historical polities with areas and basic geographic data
- **Role**: Supplementary cross-reference, especially for pre-1886 entities
- **Key limitations**: Date precision issues, no ISO codes, empire-level polygons
- **Source**: Seshat Global History Databank

### 2.5 V-Dem (Varieties of Democracy)

- **Entries**: 202 countries
- **Coverage**: 1789-2025
- **Content**: 531 indicators on democracy and governance
- **Version**: v16
- **Role**: Cross-reference for state existence periods (regime data, not territorial)
- **Source**: https://v-dem.net/

### 2.6 Polity5

- **Coverage**: 1800-2018
- **Content**: Democracy/autocracy scale (-10 to +10) with regime change events
- **Role**: Cross-reference for state existence periods
- **Key limitation**: Regime characteristics only, no territorial data
- **Source**: Center for Systemic Peace (systemicpeace.org)

### 2.7 Natural Earth

- **Entries**: 258 countries (Admin 0)
- **Coverage**: Current snapshot
- **Content**: Country boundaries at 3 scales (10m, 50m, 110m)
- **Role**: Fallback polygon source, validation
- **License**: Public domain
- **Source**: https://www.naturalearthdata.com/

### 2.8 Maddison Project Database 2023

- **Coverage**: 1 CE-2022
- **Content**: Historical GDP per capita and population
- **Role**: Economic context for polity significance
- **Source**: https://www.rug.nl/ggdc/historicaldevelopment/maddison/

### 2.9 Penn World Table 11.0

- **Coverage**: 1950-2023
- **Content**: Real GDP, labor productivity, capital stock
- **Role**: Modern economic validation
- **Source**: https://www.rug.nl/ggdc/productivity/pwt/

### 2.10 Colleague's Working Database

- **Source**: `/home/catalin/Downloads/polities data full.xlsx`
- **Content**: 8+ worksheets cross-referencing COW, CShapes, Federico-Tena, Cliopatria
- **Role**: Primary validation reference, especially for area data and period splits
- **Key sheets**:
  - `whep_equivalences` (1,226 rows, 179 unique polities)
  - `COWs full entities changes` (381 territorial transfers)
  - `Europe from 1850` (~240 polity-periods with areas)
  - `Cliopatria` (2,905 entries)
  - `Colonies_ft_cshapes` (~1,000 colonial period mappings)
  - British/French/Ottoman empire-specific sheets

### 2.11 Paine, Qiu & Ricart-Huguet (2024) -- Pre-Colonial African States

- **Entries**: 46 pre-colonial African polities
- **Coverage**: Pre-1885 (pre-Scramble for Africa)
- **Content**: Vector boundaries (Shapefile) for African states, digitized from
  Murdock (1959), Herbst (2000), and other historical sources
- **Role**: Only systematic source of pre-colonial African state boundaries with
  consistent methodology and replication data
- **Key characteristics**:
  - Published in American Political Science Review (APSR 2024)
  - Replication data on Harvard Dataverse (doi:10.7910/DVN/9QJVJ1)
  - Uses 0.25-degree buffers (~25 km) for robustness checks, acknowledging
    boundary uncertainty
  - Core states include: Asante, Benin Kingdom, Borno, Buganda, Bunyoro,
    Burundi, Cayor, Dahomey, Darfur, Ethiopia, Futa Jalon, Jolof, Kazembe,
    Lesotho, Luba, Lunda, Nkore, Rwanda, Sokoto, Wadai, Walo, Zulu, Egypt,
    Morocco, Tunis, and ~20 others
  - Explicitly demonstrates that Murdock ethnographic map should NOT be used
    as proxy for state boundaries
- **License**: Free (Harvard Dataverse)
- **Citation**: Paine, J., Qiu, Y., & Ricart-Huguet, J. (2024). "Endogenous
  Colonial Borders: Precolonial States and Geography in the Partition of
  Africa." American Political Science Review, 119(1), 1-20.
- **Key file**: `PCS.shp` (929 KB) in `Shapefiles/Precolonial states/` directory

### 2.12 Cliopatria (Seshat Global History Databank)

- **Entries**: 1,600+ polities worldwide (15,690 GeoJSON features)
- **Coverage**: 3400 BCE to 2024 CE
- **Content**: Polygons for historical polities, hand-traced from reference atlases
- **Role**: Best single source for pre-1886 global polygon coverage
- **Key characteristics**:
  - For 1800-1886: 1,945 features covering 290+ polities
  - Variable temporal resolution (Ottoman: 33 records, Russian Empire: 34,
    Qing China: 31, Qajar Iran: 12, Ashanti: 20 time-steps)
  - African polities: Ashanti Empire, Sokoto Caliphate, Ethiopian Empire,
    Merina Kingdom, Bornu Empire, Zululand, Morocco, Zanzibar, Regency of
    Algiers, Khedivate of Egypt, Sultanate of Darfur, Wadai Empire, and others
  - Moderate spatial precision (~hundreds of vertices per polygon, ~25-100 km
    uncertainty)
  - Limitation: treats some empires as monolithic (e.g., "British Africa")
- **License**: CC BY 4.0
- **Source**: https://seshatdatabank.info/
- **WHEP integration**: 4 polygons extracted for polities that had no polygon from
  any other source (IRN-1800-1828 Qajar Dynasty, AUH-1800-1867 Austrian Empire,
  SWE-1800-1809 Swedish Empire incl. Finland, SWE-1809-1814 Sweden post-Finland).
  Script: `R/12_integrate_cliopatria_polygons.R`.
  Output: `data/geodata/cliopatria_polygons.gpkg`.
  Data file: `inputs/cliopatria.geojson.zip` (not committed; download from GitHub).

### 2.13 Additional Databases Surveyed

| Database | Coverage | Content | Used? |
|----------|----------|---------|-------|
| Clio-Infra | 1500-2018 | 86 socioeconomic datasets | No (modern boundaries only) |
| World Historical Gazetteer | All history | 2M+ place records | No (gazetteer, not borders) |
| IPE Data Resource | 1800-2018 | 951 variables, concordance table | Consulted for code mapping |
| Wimmer & Min | 1816-2001 | State formation data | Consulted for dates |
| IBAD | 1816-2001 | Border agreement records | Consulted for border change dates |
| HGIS Germany | 1820-1914 | German state boundaries (vector) | Potential pre-1886 source |
| CHGIS v6 | Qing dynasty | 3,830 prefecture-level (rank 3) polygons | Assessed: too granular (subnational admin, not sovereign boundaries). CHN entries already covered by CShapes. |
| HistoGIS | Austrian Empire 1848 | Crownland boundaries (vector) | Potential pre-1886 source |
| Imperiia Project | Russian Empire 1820s | Provincial boundaries (vector) | Potential pre-1886 source |
| Centennia CRE | 1000-2003 | Europe+ME boundaries (commercial) | Not used ($3,125 license) |
| Euratlas | 1 CE-2000 | Historical shapefiles | Not used (€150/century license) |
| Thenmap API | 1945-present | GeoJSON via REST | Consulted for post-WWII |
| MPIDR Census Mosaic | Europe 1860-2003 | Census boundary shapefiles | Potential pre-1886 source |
| Aourednik | 800 BCE-2010 | GeoJSON snapshots | Consulted (empire-level polygons only) |
| COLDAT | Colonial dates | Tabular | Consulted for colonial period dates |
| Geo-Larhra | Italy 1815-1866 | Shapefiles | Potential for Italian states |
| geoBoundaries | Global current | Open-source boundaries | Fallback option |
| FEWS NET | Food-insecure regions | Admin boundaries | Not relevant |

See `docs/12_HISTORICAL_MAP_SOURCES.md` for a comprehensive catalog of 28+
historical polygon sources with detailed assessments and priority ratings.

---

## 3. Source Concordance

How polities can be linked across sources:

| Link type | Sources connected | Reliability |
|-----------|------------------|-------------|
| ISO 3166-1 alpha-3 | FAOSTAT, M49, GADM, Natural Earth, V-Dem | High (modern states) |
| ISO 3166-1 alpha-2 | FAOSTAT, M49, Natural Earth | High (modern states) |
| M49 numeric code | FAOSTAT, M49, UN datasets | High (UN members) |
| COW numeric code | COW state system, COW territorial change, CShapes | High (1816-2018) |
| Gleditsch-Ward code | CShapes, G&W state list | High (1816-present) |
| Country name | All sources (requires harmonization) | Medium (name variations) |

**Recommended R package for concordance**: `countrycode` (CRAN) provides mappings
between COW, ISO, M49, G&W, and other coding systems.

---

## 4. Source Quality Assessment

| Source | Strengths | Weaknesses |
|--------|-----------|------------|
| Federico-Tena | Earliest coverage (1800+), trade-specific | End years uncertain, NA defaults |
| CShapes 2.0 | Geometry, precise areas, colonial coverage | Ends 2019, pre-1886 Europe only |
| FAOSTAT | Modern coverage, standard codes, regions | No historical data pre-1961 |
| UN M49 | Standard codes, UN recognition basis | No geometry, starts 1970 |
| COW | Detailed transfers, area data | Different naming, 1816 start |
| Cliopatria | Deepest historical coverage (3400 BCE+), 290+ polities 1800-1886 | ~25-100 km boundary uncertainty, no ISO codes |
| Paine et al. | Only systematic pre-colonial African state polygons (46 states) | Single time snapshot, ~25 km uncertainty |
| GADM | Very detailed geometry, all admin levels | Current snapshot only |
| Natural Earth | Public domain, good disputed areas | Current only, coarser resolution |
| V-Dem | Longest coverage (1789+), rich indicators | Regime data only, no territory |
| Colleague's Excel | Cross-references everything | Working document, not final |
