# Definitive Guide to Historical Polities Databases & Territorial Change Datasets

Compiled 2026-03-25 via extensive online research.

---

## 1. Correlates of War (COW) -- Territorial Change Dataset v6

### Overview
Identifies and codes **all territorial changes involving at least one nation-state** (as defined by COW) for 1816-2018. Covers peaceful and violent transfers of territory.

### Download
- **URL**: <https://correlatesofwar.org/data-sets/territorial-change/>
- **ZIP**: `terr-changes-v6.zip` (255 KB) containing:
  - `tc2018.csv` -- main data (CSV)
  - `tc2018.xls` -- Excel version
  - `tcmanual.pdf` -- coding manual
  - `Entities.pdf` -- list of political entities (colonies, dependencies, possessions)

### CSV Schema (`tc2018.csv`)
Confirmed by downloading and inspecting the header row:

| Column | Description |
|--------|-------------|
| `year` | Year of the territorial change |
| `month` | Month of the change (-9 if unknown) |
| `gainer` | COW code of the gaining state/entity |
| `gaintype` | Type of territory for gainer: 0=dependent, 1=homeland |
| `procedur` | Process: 1=Conquest, 2=Annexation, 3=Cession, 4=Secession, 5=Unification, 6=Mandated territory (-9 if N/A) |
| `entity` | COW code of the territory exchanged |
| `contgain` | Contiguity of exchanged unit to gaining state |
| `area` | Area of unit exchanged in square kilometers |
| `pop` | Population of unit exchanged |
| `portion` | 0=part of unit, 1=entire unit, -9=undetermined |
| `loser` | COW code of the losing state/entity |
| `losetype` | Type of territory for loser: 0=dependent, 1=homeland |
| `contlose` | Contiguity of exchanged unit to losing state |
| `entry` | System entry flag |
| `exit` | System exit flag |
| `number` | Unique territorial change number (arbitrary identifier) |
| `indep` | Independence flag: 1=independence, 0=other |
| `conflict` | Military conflict: 1=yes, 0=no |
| `version` | Data file version |

### Temporal Coverage
1816-2018

### Entities
All COW-coded nation-states plus political entities (colonies, dependencies, possessions). Missing data coded as `-9`.

### Licensing
Free for academic use. Citation required: Tir et al. (1998), "Territorial Changes, 1816-1996", *Conflict Management and Peace Science* 16:89-97.

### Contact
Steven V. Miller (Clemson University): svmille@clemson.edu

---

## 2. Correlates of War (COW) -- State System Membership (v2024)

### Overview
Identifies states in the international system, their standard COW country codes, abbreviations, and dates of membership as states and major powers.

### Download
- **URL**: <https://correlatesofwar.org/data-sets/state-system-membership/>
- **Files**:
  - `States2024.zip` -- state list (CSV + DTA)
  - `MajorPowers2024.zip` -- major powers list
  - `System2024.zip` -- country-year format
  - Non-directed and directed dyad-year datasets also available
- **Codebook PDF**: <https://correlatesofwar.org/wp-content/uploads/State-System-Membership-Codebook-V2024.pdf>

### CSV Schema (States file)
10 variables, 243+ observations:

| Column | Description |
|--------|-------------|
| `stateabb` | COW state abbreviation (character) |
| `ccode` | COW numeric country code |
| `statenme` | Primary state name |
| `styear` | Year state entered the system |
| `stmonth` | Month state entered the system |
| `stday` | Day state entered the system |
| `endyear` | Year state exited the system |
| `endmonth` | Month state exited the system |
| `endday` | Day state exited the system |
| `version` | Data file version number |

### Membership Criteria
- **Pre-1920**: Population > 500,000 AND diplomatic missions at/above charge d'affaires level with Britain and France
- **Post-1920**: Membership in League of Nations/UN, OR population > 500,000 AND diplomatic recognition from any two major powers

### Temporal Coverage
1816-2024

### Number of Entities
~243 states (varies by version)

### Licensing
Free for academic use. Citation required.

### Contact
Jeff Carter (Appalachian State): jtc475@gmail.com; Scott Wolford (UT Austin): swolford@austin.utexas.edu

---

## 3. CShapes 2.0

### Overview
GIS dataset providing historical maps of **independent states and dependent territories** from 1886 to 2019. Maps borders, capitals, and political status over time. Two coding variants: one based on Gleditsch & Ward, one on COW.

### Download
- **Main page**: <https://icr.ethz.ch/data/cshapes/>
- **GeoJSON**: <https://icr.ethz.ch/data/cshapes/CShapes-2.0.geojson>
- **Codebook**: <https://icr.ethz.ch/data/cshapes/CShapes-2.0_Codebook.pdf>
- **Shapefile**: available at the main page
- **CSV**: available at the main page
- **R package**: `cshapes` on CRAN
- **API/OGC**: <https://demo.ldproxy.net/cshapes>

### Schema (Attributes per country-period row)
Confirmed from the codebook:

| Column | Description |
|--------|-------------|
| `gwcode` | Country identifier (Gleditsch & Ward coding for independent states; separate coding for dependencies) |
| `statename` | State name (aliases in brackets) |
| `startdate` | Start date of the country-period |
| `enddate` | End date of the country-period |
| `status` | Political status: 1=Independent state, 2=Colony, 3=Protectorate, 4=Leased territory, 5=Occupied |
| `ruledby` | For dependencies: gwcode of the sovereign state (e.g., 200 for British colonies) |
| `capname` | Name of the capital |
| `caplong` | Longitude of the capital (decimal degrees) |
| `caplat` | Latitude of the capital (decimal degrees) |
| `area_sqkm` | Size of territory in square kilometers |
| `b_def` | Border definition: 1=clearly defined, 0=partly undefined |
| `fid` | Feature ID (unique row identifier) |
| `geom_id` | Unique geometry identifier |

Also includes (in some distributions): `gwsdate`, `gwedate`, `gwsyear`, `gwsmonth`, `gwsday`, `gweyear`, `gwemonth`, `gweday`, `ISO1NUM`, `ISO1AL2`, `ISO1AL3`, `cowcode`.

### Data Structure
- Rows = country-periods (a new row for every change in borders or attributes)
- Geometry = polygons in EPSG:4326
- Two versions: GW-based and COW-based coding

### Temporal Coverage
1886-2019 (extends back from original CShapes 1.0 which started at 1946)

### Number of Entities
All independent states and dependent territories in the international system over this period.

### Licensing
Free for academic use. Citation: Schvitz et al. (2022), "Mapping The International System, 1886-2017", *Journal of Conflict Resolution* 66(1): 144-161.

### Border Change Sources
- Territorial Change Dataset (Tir et al., 1998)
- Encyclopedia of International Boundaries (Biger, 1995)
- Encyclopedia of African Boundaries (Brownlie, 1979)

---

## 4. Cliopatria

### Overview
Comprehensive open-source geospatial dataset of **worldwide polities from 3400 BCE to 2024 CE**. Part of the Seshat Global History Databank. Covers city-states through empires, centralized and decentralized.

### Download
- **GitHub**: <https://github.com/Seshat-Global-History-Databank/cliopatria>
- **Zenodo**: <https://zenodo.org/records/14714684> (DOI: 10.5281/zenodo.14714684)
- **Zenodo (data)**: <https://zenodo.org/records/13363121>
- **Interactive map**: <https://seshat-db.com/core/cliopatria/>

### Schema (GeoJSON features)
Confirmed from the Nature Scientific Data paper (2025) and GitHub README:

| Field | Description |
|-------|-------------|
| `Name` | Entity name (e.g., "Roman Empire", "Middle Kingdom of Egypt") |
| `FromYear` | Start year (negative = BCE, positive = CE) |
| `ToYear` | End year |
| `Area` | Territory in km^2 (calculated using EPSG:6933 equal-area projection) |
| `Type` | Classification (currently "POLITY") |
| `Wikipedia` | Associated Wikipedia page phrase (compose URL: `http://en.wikipedia.org/<phrase>`) |
| `SeshatID` | Reference to Seshat polity record (`http://seshat-db.org/core/polity/<id>`) |
| `MemberOf` | Composite/supra-polity membership |
| `Components` | Member entities for composite polities |
| `geometry` | Polygon/MultiPolygon in EPSG:4326 |

### Data Structure
- ~15,000 records total
- Multiple rows per entity (new row when spatial/temporal attributes change)
- Composite polities denoted with parentheses, e.g., "(British Empire)"

### Temporal Coverage
3400 BCE - 2024 CE (508 individual map images for specific years)

### Number of Entities
Over **1,600 political entities**

### Inclusion Criteria
With rare exceptions, polities must occupy at least 5,000 km^2 and have a duration of at least 50 years.

### Licensing
**Creative Commons Attribution 4.0 International (CC BY 4.0)**

### Citation
Published in Nature Scientific Data (2025): "Cliopatria - A geospatial database of world-wide political entities from 3400BCE to 2024CE"

---

## 5. Natural Earth -- Admin-0 Countries

### Overview
Public domain map dataset at three scales (1:10m, 1:50m, 1:110m). Admin-0 Countries contains **258 countries** (current, de facto boundaries). Shows who controls territory, not de jure claims.

### Download
- **10m Countries**: <https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_admin_0_countries.zip> (4.7 MB)
- **10m Countries (without lakes)**: `ne_10m_admin_0_countries_lakes.zip` (4.87 MB)
- **50m Countries**: <https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/50m/cultural/ne_50m_admin_0_countries.zip>
- **110m Countries**: <https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/110m/cultural/ne_110m_admin_0_countries.zip>
- **GitHub (GeoJSON)**: <https://github.com/nvkelso/natural-earth-vector/tree/master/geojson>
- **Main page**: <https://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/>

### Formats
Shapefile, GeoJSON (via GitHub), GeoDB, SQLite

### Key Attribute Fields
Over 90 attributes. Key ones include:

**Identity/Codes:**
| Field | Description |
|-------|-------------|
| `SOVEREIGNT` | Sovereign state name |
| `SOV_A3` | 3-letter sovereign state code |
| `ADMIN` | Admin-0 name |
| `ADM0_A3` | Admin-0 3-letter code |
| `NAME` | Country name |
| `NAME_LONG` | Long-form name |
| `FORMAL_EN` | Formal English name |
| `ISO_A2` | ISO 3166-1 alpha-2 code |
| `ISO_A3` | ISO 3166-1 alpha-3 code |
| `ISO_N3` | ISO 3166-1 numeric code |
| `UN_A3` | United Nations code |
| `WB_A2` | World Bank 2-letter code |
| `WB_A3` | World Bank 3-letter code |
| `FIPS_10_` | FIPS country code |

**Geography/Classification:**
| Field | Description |
|-------|-------------|
| `CONTINENT` | Continent name |
| `REGION_UN` | UN region |
| `SUBREGION` | UN subregion |
| `REGION_WB` | World Bank region |

**Hierarchy:**
| Field | Description |
|-------|-------------|
| `TYPE` | Entity type |
| `ADM0_DIF` | Flag: admin-0 differs from sovereign |
| `GEOU_DIF` | Flag: geo unit differs from admin |
| `GU_A3` | Geo unit 3-letter code |
| `SU_A3` | Subunit 3-letter code |
| `BRK_A3` | Breakaway/disputed 3-letter code |
| `BRK_NAME` | Breakaway name |

**Thematic:**
| Field | Description |
|-------|-------------|
| `POP_EST` | Population estimate |
| `POP_RANK` | Population rank |
| `GDP_MD` | GDP in millions of dollars |
| `ECONOMY` | Economic classification |
| `INCOME_GRP` | Income group |
| `MAPCOLOR7/8/9/13` | Map coloring values |
| `LABELRANK` | Label display priority |
| `SCALERANK` | Scale rank |
| `TINY` | Small country flag |

### Number of Entities
- **Countries**: 258 (distinguishes metropolitan and semi-independent portions)
- **Sovereign states**: 209 (199 issuing passports)

### POV Variants
Point-of-view variants available for several dozen countries (e.g., `ADM0_A3_US`, `ADM0_A3_UN`, `ADM0_A3_WB`)

### Temporal Coverage
Current boundaries only (no historical data). Version 5.1.1.

### Licensing
**Public domain** (no restrictions)

---

## 6. GADM (Global Administrative Areas) v4.1

### Overview
Spatial database of the world's administrative boundaries at **6 levels** (country down to commune/municipality). Current version: 4.1. Delimits **400,276 administrative areas**.

### Download
- **Main page**: <https://gadm.org/data.html>
- **Whole world (GeoPackage)**: <https://geodata.ucdavis.edu/gadm/gadm4.1/gadm_410-gpkg.zip>
- **Whole world (Geodatabase)**: <https://geodata.ucdavis.edu/gadm/gadm4.1/gadm_410-gdb.zip>
- **Six separate layers (GeoPackage)**: <https://geodata.ucdavis.edu/gadm/gadm4.1/gadm_410-levels.zip>
- **By country**: <https://gadm.org/download_country.html>
- **Metadata**: <https://gadm.org/metadata.html>

### Formats
GeoPackage (standard), Geodatabase, Shapefile, KMZ, R spatial objects

### Administrative Levels
| Level | Description |
|-------|-------------|
| 0 | Country |
| 1 | State/province/equivalent |
| 2 | County/district/equivalent |
| 3 | Commune/municipality/equivalent |
| 4 | Smaller subdivision |
| 5 | Smallest subdivision |

### Schema (per level)

**Level 0 (Country):**

| Field | Type | Description |
|-------|------|-------------|
| `UID` | Integer | Unique ID across all geometries |
| `GID_0` | String | ISO 3166-1 alpha-3 country code |
| `NAME_0` | String | Country name in English |

**Levels 1-5 (where i = level number):**

| Field | Type | Description |
|-------|------|-------------|
| `GID_i` | String | Hierarchical unique ID (e.g., AFG.1.2) |
| `NAME_i` | String | Official name in Latin script |
| `VARNAME_i` | String | Alternate names (pipe-separated) |
| `NL_NAME_i` | String | Non-Latin script names |
| `HASC_i` | String | Statoids hierarchical code |
| `CC_i` | String | Within-country unique code |
| `TYPE_i` | String | Administrative type (local language) |
| `ENGTYPE_i` | String | Administrative type (English) |
| `VALIDFR_i` | String | Valid-from date (YYYY-MM-DD) |
| `VALIDTO_i` | String | Valid-to date (YYYY-MM-DD) |
| `REMARKS_i` | String | Historical notes |

### GID Coding System
ISO alpha-3 country code + dot-delimited hierarchical numbers: `AFG.1`, `AFG.1.1`, `AFG.1.1.1`, with version suffix (e.g., `AFG.3_1`).

### Comparison with Natural Earth
| Feature | GADM 4.1 | Natural Earth |
|---------|-----------|---------------|
| Resolution | Very high (400K+ areas) | Three scales (10m/50m/110m) |
| Levels | 6 (country to commune) | Country + states/provinces |
| Licensing | Academic/non-commercial only | Public domain |
| Temporal | Current boundaries only | Current boundaries only |
| Formats | GeoPackage, GDB, SHP, KMZ, R | SHP, GeoJSON, GeoDB |
| Thematic data | Names, codes only | Population, GDP, economy, etc. |
| Use case | Detailed admin boundaries | Cartographic visualization |

### Licensing
**Free for academic and non-commercial use.** Redistribution or commercial use prohibited without permission.

### Number of Entities
400,276 administrative areas across all levels. Version 5 scheduled for January 2026.

---

## 7. Gleditsch & Ward (G&W) State List

### Overview
A revised list of independent states since 1816, correcting perceived shortcomings in the COW state system list. Published in Gleditsch & Ward (1999), "Interstate System Membership: A Revised List of the Independent States since 1816", *International Interactions* 25: 393-413.

### Download
- **Main page**: <http://ksgleditsch.com/statelist.html>
- **Data page**: <http://ksgleditsch.com/data-4.html>
- **Format**: Tab-delimited text files
- **R packages**: `states` (CRAN), `peacesciencer` (CRAN)

### Schema
6 variables:

| Column | Description |
|--------|-------------|
| `gwcode` | G&W numeric country code |
| `gwc` | G&W character country code (derived from COW codes) |
| `country_name` | Full country name |
| `start` | Independence start date (YYYY-MM-DD) |
| `end` | Independence end date (9999-12-31 = ongoing) |
| `microstate` | Boolean: TRUE if population < 250,000 |

### Key Differences from COW
| Aspect | COW | Gleditsch & Ward |
|--------|-----|-----------------|
| Pre-1920 states | Requires diplomatic missions with Britain AND France | More inclusive; recognizes more states as independent |
| State count | Fewer pre-1920 states | Substantially more pre-1920 states |
| Code range | 2-990 | 2-990 (same range, substantial overlap) |
| Microstates | Not separately flagged | Includes microstate flag (<250K pop) |
| Independence criteria | Stricter diplomatic recognition | Broader functional sovereignty test |
| Soviet succession | Russia (365) = predecessor/successor of USSR | Same treatment: Russia (365) = predecessor/successor |
| Germany | Some differences in coding East/West | Slightly different handling |

### Temporal Coverage
1816-present (regularly updated)

### Number of Entities
Substantially more than COW for the pre-1920 period. Includes both independent states and a separate microstate list.

### Licensing
Free for academic use. Citation: Gleditsch & Ward (1999).

---

## 8. V-Dem (Varieties of Democracy)

### Overview
World's most comprehensive democracy measurement dataset. Rates countries on 531 indicators and 95+ indices across 5 principles: electoral, liberal, participatory, deliberative, egalitarian.

### Download
- **Main page**: <https://www.v-dem.net/data/the-v-dem-dataset/>
- **Current version**: v16 (March 2026)
- **Formats**: STATA, CSV, R, SPSS
- **R package**: `vdemdata` (GitHub)

### Dataset Variants
1. **Coder-Level**: 273 indicators with coder-reliability scores
2. **Country-Date**: 531 indicators, 95 indices
3. **Country-Year Core**: 5 high-level indices, 93 sub-indices, 179 indicators
4. **Country-Year Full+Others**: All 531 indicators + 251 indices + 62 external indicators

### Polity Definition
"A V-Dem country is a political unit enjoying at least some degree of functional and/or formal sovereignty." Includes:
- Fully sovereign states
- Entities with intermediate sovereignty (e.g., Hungarian part of Austro-Hungarian Empire, Norway under Personal Union with Sweden)
- Major colonies (British India, Dutch East Indies, Spanish South American colonies)

### Key Cross-Reference Fields
| Column | Description |
|--------|-------------|
| `country_name` | Country name |
| `country_text_id` | 3-letter country code |
| `country_id` | V-Dem numeric ID |
| `year` | Year |
| `v2x_polyarchy` | Electoral democracy index (0-1) |
| `v2x_libdem` | Liberal democracy index (0-1) |
| `v2x_partipdem` | Participatory democracy index |
| `v2x_delibdem` | Deliberative democracy index |
| `v2x_egaldem` | Egalitarian democracy index |

### Temporal Coverage
1789-2025 (or from first functional/formal sovereignty for each country)

### Number of Entities
**202 distinct countries/entities** (v16)

### Documentation
- Country Coding Units document: <https://v-dem.net/documents/40/v-dem_countryunit_v14.pdf>
- Full codebook: <https://v-dem.net/documents/55/codebook.pdf>

### Licensing
Free to download. Citation required.

---

## 9. Polity5 / Polity IV

### Overview
Annual cross-national time-series coding democratic and autocratic "patterns of authority" and regime changes. Uses a **21-point scale** from -10 (hereditary monarchy) to +10 (consolidated democracy).

### Download
- **INSCR Data Page**: <https://www.systemicpeace.org/inscrdata.html>
- **Project page**: <https://www.systemicpeace.org/polityproject.html>
- **Manual**: <https://www.systemicpeace.org/inscr/p5manualv2018.pdf>

### File Formats
1. **Annual Time-Series (1946-2018)**: `p5v2018.sav` (SPSS), `p5v2018.xls` (Excel)
2. **Polity-Case Format (1800-2018)**: `p5v2018d.sav` (SPSS), `p5v2018d.xls` (Excel)

### Key Variables
| Variable | Description |
|----------|-------------|
| `ccode` | COW numeric country code (2016 version) |
| `scode` | Alphabetic country code |
| `country` | Country name |
| `year` | Year |
| `democ` | Institutionalized democracy (0-10) |
| `autoc` | Institutionalized autocracy (0-10) |
| `polity` | Combined polity score (democ - autoc), range -10 to +10 |
| `polity2` | Modified polity score (converts -66, -77, -88 to conventional range) |
| `xrreg` | Regulation of Chief Executive Recruitment |
| `xrcomp` | Competitiveness of Executive Recruitment |
| `xropen` | Openness of Executive Recruitment |
| `xconst` | Executive Constraints (Decision Rules) |
| `parreg` | Regulation of Participation |
| `parcomp` | Competitiveness of Participation |

### Regime Categories
- **Autocracies**: -10 to -6
- **Anocracies**: -5 to +5 (plus special codes -66, -77, -88)
- **Democracies**: +6 to +10

### Special Codes
- `-66`: Interruption
- `-77`: Interregnum (no functioning central authority)
- `-88`: Transition period

### Polity Definition
All **independent countries** with total population > 500,000 (in 2018). The dataset codes only institutions of the central government and political groups acting within that authority. Excludes separatist territories.

### Temporal Coverage
1800-2018

### Number of Entities
**167 countries** (in 2018)

### Licensing
**Copyrighted** by Center for Systemic Peace. Published use requires citation. Reproduction/redistribution prohibited without permission.

---

## 10. GeoNames

### Overview
Geographical database covering all countries, containing **over 11 million placenames**. Useful for historical polity identification through its alternative names system with temporal flags.

### Download
- **Main dump**: <https://download.geonames.org/export/dump/>
- **Country info**: <https://download.geonames.org/export/dump/countryInfo.txt>
- **All countries**: `allCountries.zip` (398 MB)
- **Alternate names**: `alternateNamesV2.zip` (190 MB)
- **Individual countries**: by ISO 2-letter code (e.g., `US.zip`, `FR.zip`)

### countryInfo.txt Schema
| Field | Description |
|-------|-------------|
| `ISO` | ISO 3166-1 alpha-2 code |
| `ISO3` | ISO 3166-1 alpha-3 code |
| `ISONumeric` | ISO 3166-1 numeric code |
| `FIPS` | FIPS country code |
| `Country` | Country name |
| `Capital` | Capital city name |
| `Area` | Area in km^2 |
| `Population` | Population |
| `Continent` | Continent code |
| `TLD` | Top-level domain |
| `CurrencyCode` | Currency code |
| `CurrencyName` | Currency name |
| `Phone` | Phone prefix |
| `PostalCodeFormat` | Postal code format |
| `PostalCodeRegex` | Postal code regex |
| `Languages` | Spoken languages (comma-separated) |
| `geonameId` | GeoNames ID |
| `neighbours` | Neighboring country codes |
| `EquivalentFipsCode` | Equivalent FIPS code |

### Geoname Table Schema (main records)
| Field | Description |
|-------|-------------|
| `geonameId` | Unique integer ID |
| `name` | Name of feature |
| `asciiname` | ASCII-safe name |
| `alternatenames` | Comma-separated alternates |
| `latitude` | Latitude (WGS84) |
| `longitude` | Longitude (WGS84) |
| `feature_class` | Feature class (A=country, P=populated place, etc.) |
| `feature_code` | Feature code (PCL*=political entity codes) |
| `country_code` | ISO alpha-2 |
| `admin1_code` through `admin4_code` | Administrative division codes |
| `population` | Population |
| `elevation` | Elevation (meters) |
| `timezone` | IANA timezone |
| `modification_date` | Last modified date |

### Historical Name Support
The `alternateNamesV2` table includes:
- `isHistoric` flag (1 = name was used in the past)
- `from` and `to` date fields for when names were valid
- All language variants

### Usefulness for Historical Polity Identification
- Feature codes `PCLI` (independent political entity), `PCLD` (dependent), `PCLF` (freely associated), `PCLH` (historical political entity), `PCLS` (semi-independent)
- Historical names with temporal ranges
- Cross-references via ISO codes to other datasets

### Licensing
**Creative Commons Attribution 4.0 (CC BY 4.0)**

---

## 11. Wikidata / Wikipedia

### Overview
Wikidata contains structured data about sovereign states including temporal information, predecessor/successor chains, ISO codes, and more. Queryable via SPARQL endpoint.

### Access
- **SPARQL endpoint**: <https://query.wikidata.org/>
- **Query GUI**: <https://query.wikidata.org/sparql>

### Key Properties for Polity Research

| Property | Name | Description |
|----------|------|-------------|
| `P31` | instance of | Use with `Q3624078` (sovereign state) or `Q3024240` (historical country) |
| `P571` | inception | Date entity came into existence |
| `P576` | dissolved/abolished | Date entity ceased to exist |
| `P1365` | replaces | Predecessor entity |
| `P1366` | replaced by | Successor entity |
| `P297` | ISO 3166-1 alpha-2 code | 2-letter ISO code |
| `P298` | ISO 3166-1 alpha-3 code | 3-letter ISO code (note: not all sources agree -- some use P297 for alpha-2) |
| `P122` | basic form of government | Government type |
| `P47` | shares border with | Neighboring states |
| `P1549` | demonym | Name for inhabitants |
| `P17` | country | Associated country |
| `P36` | capital | Capital city |
| `P30` | continent | Continent |

### Key Entity Classes
| QID | Label | Count (approx.) |
|-----|-------|-----------------|
| `Q3624078` | sovereign state | ~200 current |
| `Q3024240` | historical country | ~3,025 |
| `Q6256` | country | broader concept |

### Example SPARQL: All Sovereign States with Timelines
```sparql
SELECT ?state ?stateLabel ?inception ?dissolved ?isoCode ?replacedBy ?replacedByLabel
WHERE {
  ?state wdt:P31/wdt:P279* wd:Q3624078 .
  OPTIONAL { ?state wdt:P571 ?inception . }
  OPTIONAL { ?state wdt:P576 ?dissolved . }
  OPTIONAL { ?state wdt:P297 ?isoCode . }
  OPTIONAL { ?state wdt:P1366 ?replacedBy . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
}
ORDER BY ?inception
```

### Example SPARQL: Historical Countries with Predecessor/Successor Chains
```sparql
SELECT ?state ?stateLabel ?inception ?dissolved ?predecessorLabel ?successorLabel
WHERE {
  ?state wdt:P31 wd:Q3024240 .
  OPTIONAL { ?state wdt:P571 ?inception . }
  OPTIONAL { ?state wdt:P576 ?dissolved . }
  OPTIONAL { ?state wdt:P1365 ?predecessor . }
  OPTIONAL { ?state wdt:P1366 ?successor . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
}
ORDER BY ?inception
```

### Temporal Coverage
All of recorded history (wherever Wikidata contributors have entered data)

### Number of Entities
~200 current sovereign states + ~3,025 historical countries

### Licensing
**CC0 (public domain)**

---

## 12. Maddison Project Database 2023

### Overview
Historical GDP and population data, providing information on comparative economic growth and income levels over the very long run. Maintained by the Groningen Growth and Development Centre (GGDC).

### Download
- **Official page**: <https://www.rug.nl/ggdc/historicaldevelopment/maddison/releases/maddison-project-database-2023>
- **Dataverse**: <https://dataverse.nl/dataset.xhtml?persistentId=doi:10.34894/INZBF2>
  - Excel: <https://dataverse.nl/api/access/datafile/421302>
  - Stata: <https://dataverse.nl/api/access/datafile/421303>
- **R package**: `MaddisonData` on CRAN
- **Kaggle mirror**: <https://www.kaggle.com/datasets/willianoliveiragibin/maddison-project-database-2023>

### Schema
| Column | Description |
|--------|-------------|
| `countrycode` | 3-letter country code |
| `country` | Country name |
| `year` | Year |
| `cgdppc` | GDP per capita (current PPPs, 2011 USD) |
| `rgdpnapc` | Real GDP per capita (national accounts, 2011 USD) |
| `pop` | Population (thousands) |
| `i_cig` | Interpolation/extrapolation indicator for GDP |
| `i_bm` | Benchmark indicator |

### Temporal Coverage
**1 CE - 2022** (with ~2,800 data points for pre-1820 period; original Maddison had only 158)

### Number of Entities
**169 countries** plus aggregate regions

### Licensing
**Creative Commons Attribution 4.0 (CC BY 4.0)**. Attribution required in published work.

### Citation
Bolt, Jutta and Jan Luiten van Zanden (2024), "Maddison style estimates of the evolution of the world economy: A new 2023 update", *Journal of Economic Surveys*, DOI: 10.1111/joes.12618

---

## 13. Penn World Table (PWT)

### Overview
Database with information on relative levels of income, output, input, and productivity. Current version: **11.0** (October 2025), upgrading from 10.01.

### Download
- **PWT 11.0**: <https://www.rug.nl/ggdc/productivity/pwt/?lang=en>
- **PWT 10.01 (Dataverse)**: <https://dataverse.nl/dataset.xhtml?persistentId=doi:10.34894/QT5BCC>
- **FRED (St. Louis Fed)**: <https://fred.stlouisfed.org/release?rid=285>
- **R package**: `pwt10` on CRAN (v10.01)
- **Formats**: Excel, Stata, online data access tool (CSV export)

### Schema (PWT 10.01 -- 52 variables, 12,810 observations)
Key variables:

| Variable | Description |
|----------|-------------|
| `country` | Country name |
| `isocode` | ISO 3166-1 alpha-3 code |
| `year` | Year |
| `currency` | National currency unit |
| `rgdpe` | Expenditure-side real GDP at chained PPPs (million 2017 USD) |
| `rgdpo` | Output-side real GDP at chained PPPs (million 2017 USD) |
| `pop` | Population (millions) |
| `emp` | Number of persons engaged (millions) |
| `avh` | Average annual hours worked |
| `hc` | Human capital index (schooling + returns) |
| `cgdpe` | Expenditure-side real GDP at current PPPs |
| `cgdpo` | Output-side real GDP at current PPPs |
| `cn` | Capital stock at current PPPs |
| `rgdpna` | Real GDP at constant 2017 national prices |
| `labsh` | Share of labour compensation in GDP |
| `xr` | Exchange rate (national currency / USD) |
| `pl_con` | Price level of consumption |
| `pl_gdpo` | Price level of output-side GDP |
| `csh_c` | Share of household consumption |
| `csh_i` | Share of gross capital formation |
| `csh_g` | Share of government consumption |
| `csh_x` | Share of merchandise exports |
| `csh_m` | Share of merchandise imports |
| `i_cig` | Relative price data source indicator |

(Full 52-variable list available in R package documentation)

### Country Definitions
PWT uses ISO 3166-1 alpha-3 codes. Countries are treated as their modern boundaries; historical states that no longer exist (e.g., USSR) have separate entries.

### Temporal Coverage
- **PWT 11.0**: 1950-2023, 185 countries
- **PWT 10.01**: 1950-2019, 183 countries

### Licensing
**Creative Commons Attribution 4.0 International (CC BY 4.0)**

### Citation
Feenstra, Robert C., Robert Inklaar and Marcel P. Timmer (2015), "The Next Generation of the Penn World Table", *American Economic Review*, 105(10): 3150-3182.

---

## 14. Additional Datasets Discovered

### geoBoundaries
- **URL**: <https://www.geoboundaries.org/>
- **Global downloads**: <https://www.geoboundaries.org/globalDownloads.html>
- Coverage: ~1 million boundaries, 200+ entities, all UN member states
- Levels: ADM0, ADM1, ADM2
- Products: HPSC (high precision), SSC (simplified), CGAZ (global composite)
- Formats: Shapefile, GeoJSON
- **License**: CC BY 4.0 / ODbL
- Harvard Dataverse archive also available

### World Bank Official Boundaries
- **URL**: <https://datacatalog.worldbank.org/search/dataset/0038272/world-bank-official-boundaries>
- Current admin-0 boundaries per World Bank definitions

### FEWS NET Geographic Boundaries
- Historical and current subnational administrative boundaries
- Formats: Shapefile, GeoJSON, KML

---

## Cross-Reference Summary Table

| Dataset | Temporal | Entities | Geospatial? | Historical? | License | Key IDs |
|---------|----------|----------|-------------|-------------|---------|---------|
| COW Territorial Change v6 | 1816-2018 | All COW states + entities | No | Yes | Academic | COW code |
| COW State System v2024 | 1816-2024 | ~243 states | No | Yes | Academic | COW ccode |
| CShapes 2.0 | 1886-2019 | States + dependencies | Yes (polygons) | Yes | Academic | gwcode, cowcode |
| Cliopatria | 3400 BCE-2024 CE | 1,600+ polities | Yes (polygons) | Yes | CC BY 4.0 | Name, SeshatID |
| Natural Earth | Current | 258 countries | Yes (polygons) | No | Public domain | ISO_A3, SOV_A3, ADM0_A3 |
| GADM 4.1 | Current | 400,276 areas | Yes (polygons) | No | Non-commercial | GID_0, ISO alpha-3 |
| Gleditsch & Ward | 1816-present | States + microstates | No | Yes | Academic | gwcode |
| V-Dem v16 | 1789-2025 | 202 entities | No | Yes | Free | country_id, country_text_id |
| Polity5 | 1800-2018 | 167 countries | No | Yes | Copyrighted | COW ccode |
| GeoNames | Current + historical names | 11M+ placenames | Point coords | Partial (names) | CC BY 4.0 | geonameId, ISO |
| Wikidata | All history | ~200 current + ~3,025 historical | No (but coords) | Yes | CC0 | QID, ISO codes |
| Maddison 2023 | 1 CE-2022 | 169 countries | No | Yes | CC BY 4.0 | countrycode (ISO) |
| PWT 11.0 | 1950-2023 | 185 countries | No | No | CC BY 4.0 | isocode (ISO) |
| geoBoundaries | Current | 200+ entities | Yes (polygons) | No | CC BY 4.0 | ISO codes |

---

## Linkage Strategy: Connecting Datasets

### Primary Join Keys
1. **COW ccode** <-> Polity5, COW Territorial Change, CShapes (cowcode field)
2. **Gleditsch & Ward gwcode** <-> CShapes (gwcode field), V-Dem (via concordance)
3. **ISO 3166-1 alpha-3** <-> Natural Earth (ISO_A3), GADM (GID_0), PWT (isocode), Maddison (countrycode), GeoNames (ISO3), Wikidata (P298)
4. **Country name** <-> Cliopatria (Name), cross-reference with Wikipedia field

### Recommended Cross-Walk Package
The R package `countrycode` provides concordance tables mapping between COW codes, G&W codes, ISO codes, and many other classification systems. Highly recommended for linking these datasets.

### For Historical Polities (pre-1816)
- Cliopatria is the primary source (3400 BCE onward)
- Wikidata's ~3,025 historical countries can supplement
- Maddison extends back to 1 CE for economic data

### For Modern State System (1816-present)
- COW State System as the backbone
- CShapes 2.0 for geospatial boundaries (1886-2019)
- G&W list for broader pre-1920 coverage
- V-Dem from 1789 for regime characteristics
- Polity5 from 1800 for regime scoring
