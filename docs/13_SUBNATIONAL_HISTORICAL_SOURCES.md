# Historical Subnational Polygon Sources for Major Countries

Research compiled 2026-03-27. Comprehensive survey of freely available vector
boundary datasets for historical admin-1 (state/province/department) polygons
across the 11 priority countries identified by the WHEP project.

---

## Executive Summary

The WHEP polities database currently has subnational coverage for 6 countries
(Russia, USA, China, Brazil, Canada, Australia) plus 26 Qing China historical
provinces. This research identifies sources to extend historical subnational
coverage backward in time and to add subnational data for 5 additional countries
(India, Indonesia, France, Germany, Spain).

### Current Subnational Coverage

| Country | Current Source | Period | Units | Gap |
|---------|--------------|--------|-------|-----|
| China (modern) | GADM 3.6 | 1997-2025 | 31 | 1912-1997 |
| China (Qing) | CHGIS v6 | 1820-1912 | 26 | -- |
| USA | GADM 3.6 | 1959-2025 | 51 | 1800-1959 |
| Russia | GADM 3.6 | 1993-2025 | 83 | 1800-1993 |
| Brazil | GADM 3.6 | 1988-2025 | 27 | 1800-1988 |
| Canada | GADM 3.6 | 1999-2025 | 13 | 1800-1999 |
| Australia | GADM 3.6 | 1901-2025 | 11 | -- |
| India | -- | -- | -- | Full gap |
| Indonesia | -- | -- | -- | Full gap |
| France | -- | -- | -- | Full gap |
| Germany | -- | -- | -- | Full gap |
| Spain | -- | -- | -- | Full gap |

### Coverage Achievability Summary

| Country | Historical Coverage | Best Free Source | Effort | Assessment |
|---------|-------------------|-----------------|--------|------------|
| **USA** | 1783-2000 | USAboundaries R pkg | **Done** | **INTEGRATED** (51 entries) |
| **Brazil** | 1872-2020 | geobr R pkg | **Done** | **INTEGRATED** (26 entries) |
| **France** | 1790-1940 | TRF-GIS + French HGIS | **Low** | Near-complete |
| **Germany** | 1820-1914 | HGIS Germany (NYU) | **Low** | Good for 19th c. |
| **Russia** | 1820s, 1897, 1926 | Imperiia + RISTAT + Transcultural | **Medium** | Snapshots only |
| **Spain** | 1833-present | CNIG/mapSpain (stable since 1833) | **Done** | **INTEGRATED** (52 entries) |
| **Canada** | 1867-present | StatCan / ccensus boundaries | **Medium** | Good from Confederation |
| **Australia** | 1901-present | GADM (stable since federation) | **Low** | Already covered |
| **India** | 1872+ | Appraising Risk (contact needed) | **High** | Limited availability |
| **Indonesia** | 1990-2014 | FAO GAUL (Earth Engine) | **Medium** | Modern era only |
| **China** | 1820, 1911 | CHGIS v6 (already integrated) | **Done** | 1912-1997 gap remains |

---

## 1. UNITED STATES (1800-1959 gap)

The USA has the best historical subnational boundary ecosystem of any country.
Multiple high-quality, freely available sources provide complete coverage.

### 1.1 USAboundaries R Package (rOpenSci) -- RECOMMENDED

- **URL**: https://github.com/ropensci/USAboundaries
- **Coverage**: Historical boundaries **1629-2000** (state/territory + county)
- **Format**: Returns `sf` objects directly in R
- **Data source**: Newberry Library Atlas of Historical County Boundaries
- **License**: CC BY-NC-SA 2.5 (Newberry attribution required); code MIT
- **Programmatic**: `us_states(map_date = "1850-07-04")` returns boundaries for
  that exact date. Any date 1783-09-03 to 2000-12-31 is valid.
- **Key advantage**: One-liner in R to get any historical snapshot. Actively
  maintained (v0.5.1, 2025-11-08). Built on the gold-standard Newberry data.

### 1.2 Atlas of Historical County Boundaries (Newberry Library) -- RAW DATA

- **URL**: https://publications.newberry.org/ahcb/downloads/united_states.html
  (state/territory files); .../states.html (per-state county files)
- **Coverage**: US Historical States & Territories: **1783-2000**. Counties: 1629-2000.
- **Format**: Shapefile + KMZ. Five generalization levels (110 MB to 0.6 MB).
- **License**: Effectively **CC0** (public domain). Library of Congress catalogs as CC0.
- **Programmatic**: Direct HTTP download of ZIP archives. No registration.
- **Key advantage**: Every boundary change coded with start/end dates. Includes
  organized territories, unorganized territories, Indian Territory.

### 1.3 NHGIS (IPUMS) -- CENSUS-LINKED

- **URL**: https://www.nhgis.org/gis-files
- **Coverage**: States from **1790**, counties from 1790. One shapefile per census
  year (1790, 1800, ..., 2020). Includes territories.
- **Format**: Shapefile (Albers Equal Area Conic projection)
- **License**: Free; redistribution requires IPUMS permission. Registration required.
- **Programmatic**: Via `ipumsr` R package and NHGIS API (free API key).
- **Key advantage**: Boundaries linked to census tabular data (population, etc.).
- **Limitation**: Decennial snapshots only, not arbitrary dates.

### 1.4 US History Maps (poezn) -- LIGHTWEIGHT

- **URL**: https://poezn.github.io/us-history-maps/
- **Coverage**: **1789-1959** (150+ dated snapshots, monthly during Civil War)
- **Format**: Shapefile + GeoJSON
- **License**: CC BY-SA 3.0
- **Programmatic**: Direct GitHub download.

### USA Recommendation

Use **USAboundaries** as the primary R integration. Install the package and call
`us_states(map_date = "YYYY-MM-DD")` for any date. This closes the 1800-1959
gap completely with zero manual work.

---

## 2. BRAZIL (1800-1988 gap)

Excellent coverage from 1872 (first census) onward. Pre-1872 gap is manageable
because provincial boundaries were stable.

### 2.1 geobr R Package (IPEA/IBGE) -- RECOMMENDED

- **URL**: https://ipeagit.github.io/geobr/ ; https://github.com/ipeaGIT/geobr
- **Coverage for states**: **1872, 1900, 1911, 1920, 1933, 1940, 1950, 1960,
  1970, 1980, 1991, 2000, 2001, 2010, 2013-2020** (22 snapshots over 148 years)
- **Format**: GeoPackage, returned as `sf` objects. CRS: SIRGAS2000 (EPSG:4674).
- **Admin levels**: States, municipalities, plus many other levels (regions,
  mesoregions, biomes, indigenous lands, etc.)
- **License**: Code MIT. Data from IBGE (public/open access).
- **Programmatic**: `geobr::read_state(year = 1872)`. Also available in Python.
- **Key advantage**: 22 temporal snapshots. Captures all major reorganizations:
  creation of territories (1943), Mato Grosso do Sul split (1977), Tocantins (1988).

### 2.2 IBGE FTP -- RAW DATA

- **URL**: https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/evolucao_da_divisao_territorial_do_brasil/evolucao_da_divisao_territorial_do_brasil_1872_2010/
- **Coverage**: Snapshots for **1872-2010** (13 time points)
- **Format**: Shapefiles (zipped). Custom World Polyconic Projection.
- **License**: Public domain (Brazilian government data).
- **Programmatic**: Direct FTP/HTTP download. No registration.
- **Key advantage**: Authoritative source that geobr wraps. Raw shapefiles with
  documentation (genealogy of municipalities, population data, etc.).

### 2.3 Stanford EarthWorks -- ALTERNATIVE MIRROR

- **URL**: https://earthworks.stanford.edu/catalog/stanford-tj392fk5522 (1872)
- **Coverage**: Multiple snapshots (1872, 1920, 1991, 2001, 2010, etc.)
- **License**: **Public domain**
- **Programmatic**: Stanford Stacks download service.

### Brazil Summary

| Period | Source | Quality |
|--------|--------|---------|
| 1800-1871 | **No GIS data** (back-project 1872) | Gap (manageable) |
| 1872-1988 | geobr / IBGE FTP | Excellent (13+ snapshots) |
| 1988-present | GADM (already in pipeline) | Good |

The pre-1872 gap is manageable because: (1) provincial boundaries inherited from
captaincies were largely stable; (2) main changes were Cisplatina/Uruguay lost
1828, Amazonas from Para 1850, Parana from Sao Paulo 1853 -- reconstructable by
merging/splitting 1872 polygons.

---

## 3. FRANCE (full gap)

Near-complete coverage achievable from freely available sources.

### 3.1 TRF-GIS: Third-Republic France (1870-1940) -- TOP PICK

- **URL**: https://dataverse.harvard.edu/dataverse/TRF-GIS
- **Paper**: Gay, V. (2021) "Mapping the Third Republic", Historical Methods, 54(4).
- **Coverage**: **1870-1940, annual** shapefiles
- **Admin levels**: Departements, arrondissements, cantons, communes; plus special
  constituencies (military, judicial, electoral, academic, ecclesiastical)
- **Format**: Shapefiles (830 files) + 901 nomenclature tables
- **CRS**: RGF93 Lambert-93 (IGN standard)
- **License**: CC BY 4.0
- **Programmatic**: Harvard Dataverse API (programmatic access via DOI).
- **Key strength**: Annual boundary changes for 70 years. Captures Alsace-Lorraine
  transfer (1871 loss, 1919 return), Territoire de Belfort creation.

### 3.2 French Historical GIS -- Departments c. 1790

- **URL**: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/HJISNR
- **Coverage**: c. 1790 (creation of the departement system, 83 original departments)
- **Format**: Shapefile
- **License**: Harvard Dataverse terms (free academic use)
- **Programmatic**: Yes, via Dataverse API with DOI `10.7910/DVN/HJISNR`
- **Related**: Region Boundaries c. 1790 at doi:10.7910/DVN/BU2SQZ

### 3.3 Guerry R Package -- c. 1830 Departments

- **URL**: https://www.datavis.ca/gallery/guerry/maps.html
- **Coverage**: c. 1830 (86 departments, Corsica merged)
- **Format**: Shapefile via R CRAN package `Guerry`
- **Programmatic**: `install.packages("Guerry")` in R

### 3.4 Eurostat GISCO NUTS (2003-2024)

- **URL**: https://ec.europa.eu/eurostat/web/gisco/geodata/statistical-units/territorial-units-statistics
- **Coverage**: 2003, 2006, 2010, 2013, 2016, 2021, 2024
- **France mapping**: NUTS 2 = regions, NUTS 3 = departements
- **Format**: SHP, GeoPackage, GeoJSON, TopoJSON, PBF, SVG
- **License**: Eurostat copyright (free reuse with attribution)
- **Programmatic**: GISCO API + R package `giscoR`

### 3.5 IGN ADMIN EXPRESS -- Current Official

- **URL**: https://geoservices.ign.fr/adminexpress
- **Coverage**: Current (updated regularly since 2017)
- **Format**: Shapefile, GeoPackage. CRS: RGF93 Lambert-93.
- **License**: Licence Ouverte 2.0 (free for all uses)
- **Programmatic**: WFS service and ATOM feed

### 3.6 Geo-Larhra (CNRS/Lyon) -- Pre-Revolution

- **URL**: http://geo-larhra.ish-lyon.cnrs.fr/
- **Coverage**: France 1660-1789 administrative boundaries
- **Format**: Vector data for GIS
- **License**: Some public, some restricted to LARHRA members
- **Note**: Pre-Revolution French administrative geography. Access partially restricted.

### 3.7 CAMPOP/INED COMMUNES Project (IN PROGRESS)

- **URL**: https://www.campop.geog.cam.ac.uk/research/projects/internationaloccupations/enchpopgos/france/boundaries.html
- **Coverage**: 1790-present (all changes since the Revolution)
- **Admin levels**: Communes (aggregatable to departements/arrondissements)
- **Status**: Ongoing research project. Contact project team for access.

### France Summary

| Period | Source | Quality |
|--------|--------|---------|
| 1660-1789 | Geo-Larhra | Partial access |
| c. 1790 | French Historical GIS (Harvard) | Good (single snapshot) |
| c. 1830 | Guerry R package | Good (single snapshot) |
| 1870-1940 | TRF-GIS (Harvard) | Excellent (annual) |
| 1940-2003 | FAO GAUL (1990-2014 only) | Partial |
| 2003-2024 | Eurostat GISCO NUTS | Good (7 snapshots) |
| Current | IGN ADMIN EXPRESS | Official |

**Coverage gap**: 1790-1870 only covered by the 1790 snapshot and c. 1830 Guerry.

---

## 4. GERMANY (full gap)

HGIS Germany provides excellent coverage for the 19th century (pre-unification
states through the Kaiserreich).

### 4.1 HGIS Germany (1820-1914) -- PRIMARY SOURCE

- **Main page**: http://www.digihist.de/html/hgisg/index.htm (interactive only)
- **Download (recommended)**: NYU Spatial Data Repository -- search for "ghgis"
  at https://geo.nyu.edu/. Pattern:
  - `harvard-ghgisYYYYcore` (state/Bundesstaaten boundaries)
  - `harvard-ghgisYYYYdistricts` (district boundaries)
  - `harvard-ghgisYYYYprovinces` (province boundaries)
- **Alternative mirrors**: Stanford EarthWorks (https://earthworks.stanford.edu/?q=hgis+germany),
  Harvard Geospatial Library (https://hgl.harvard.edu, may have WAF challenge)
- **Available time slices** (state boundaries): 1820, 1826, 1830, 1834, 1839,
  1848, 1850, 1867, 1871, 1890, 1914 (11 snapshots)
- **Also available**: Provincial + district boundaries, capitals, railways 1835-1885
- **Format**: Shapefile and GeoJSON, EPSG:4326 (WGS 84)
- **License**: Free for non-commercial academic research
- **Quality**: Created by Andreas Kunz and Leonhard Dietze (IEG Mainz).
  Professional-grade historical GIS.
- **NOTE**: Early period (1648-1812) and 20th century (1921-1993) available as
  interactive web maps only, NOT downloadable shapefiles.
- **Download status**: Harvard GeoServer proxy (`geodata-proxy.lib.harvard.edu`)
  appears to be decommissioned (no DNS A record). NYU mirrors require email-based
  request. User should request download from NYU or try Stanford EarthWorks.

### 4.2 Eurostat GISCO NUTS (2003-2024)

- **Germany mapping**: NUTS 1 = Lander, NUTS 2 = Regierungsbezirke, NUTS 3 = Kreise
- Same details as France Section 3.4.

### Germany Summary

| Period | Source | Quality |
|--------|--------|---------|
| 1820-1914 | HGIS Germany (NYU/Stanford) | Excellent (11 snapshots) |
| 1914-1945 | No freely available source | Gap |
| 1945-1990 | No unified source (FRG+DDR separate) | Gap |
| 1990-present | GADM / Eurostat GISCO | Good |

**Key note**: HGIS Germany covers the critical pre-unification period (38+ states
in the German Confederation). The 1914-1990 gap (WWI, Weimar, Nazi, occupation,
divided Germany) lacks freely available subnational boundary GIS data.

---

## 5. RUSSIA (1800-1993 gap)

The most challenging country due to constant administrative reorganization across
four regimes (Imperial, Soviet, post-Soviet transition). Multiple partial sources
must be stitched together.

### 5.1 Imperiia Project (Harvard) -- 1820s GUBERNIYA

- **URL**: https://dataverse.harvard.edu/dataverse/ImperiiaGIS
- **Dataset**: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/SKVR2L
- **Coverage**: **1820s** (from Military-Topographical Depot atlas, 1820-1827).
  49 gubernii plus Kingdom of Poland and Grand Duchy of Finland.
- **Format**: Zipped shapefiles
- **License**: Harvard Dataverse terms (open access for academic use)
- **Programmatic**: Harvard Dataverse API. Direct ZIP downloads.

### 5.2 RISTAT -- 1897 GUBERNIYA/DISTRICT

- **URL**: https://datasets.iisg.amsterdam/dataset.xhtml?persistentId=hdl:10622/DN9QDM
- **Maps**: https://ristat.org/maps
- **Coverage**: **1897** (First Russian Imperial Census). Provinces + districts (uyezdy).
- **Format**: **GeoPackage** (`provinces_1897.gpkg` 1.2 MB, `districts_1897.gpkg` 3.2 MB)
- **License**: **CC0** with citation to "Electronic Repository of Russian Historical Statistics"
- **Programmatic**: Direct ZIP download via IISG Amsterdam dataverse.
- **Key advantage**: CC0 license, GeoPackage format. Covers entire Russian Empire
  including Finland, Poland, Baltic states, Caucasus, Central Asia.
- **Created by**: Rombert Stapel (IISH)

### 5.3 Transcultural Empire GIS (Heidelberg/HSE) -- 1897 + 1926

- **URL**: https://heidata.uni-heidelberg.de/dataset.xhtml?persistentId=doi:10.11588/data/10064
- **B2FIND**: https://b2find.eudat.eu/dataset/64f5d7d2-acfd-55fc-933d-dd3f2b900c37
- **Coverage**: **1897** (Russian Empire census) AND **1926** (First All-Union Soviet Census)
- **Format**: Shapefiles + QGIS project files + PDF documentation (~2.3 MB total)
- **License**: Open access. Created by Ivan Sablin (HSE St. Petersburg) at Heidelberg.
- **Key advantage**: The ONLY freely available source providing **Soviet-era (1926)
  administrative boundaries** as vector data. Includes census attribute data.
- **Limitation**: Only two snapshots. Does not cover 1930s-1980s reorganizations.

### 5.4 ORNL DAAC (NASA) -- LATE SOVIET/POST-SOVIET (~1998)

- **URL**: https://doi.org/10.3334/ORNLDAAC/699
- **Access**: https://www.earthdata.nasa.gov/
- **Coverage**: ~1998 boundaries. 162 administrative regions across the entire
  Former Soviet Union (all 15 successor states).
- **Format**: ArcView shapefile (~4 MB, 2 granules)
- **License**: Open access, no restrictions (EOSDIS Data Use Guidance)
- **Programmatic**: Via NASA Earthdata.
- **Key advantage**: Covers all 15 successor states at oblast level. Useful proxy
  for late Soviet configuration.

### 5.5 Russian-GIStory Project (GitHub) -- IN PROGRESS / STALLED

- **URL**: https://github.com/Emelieh21/russian-gistory
- **Target years**: 1950, 1959, 1990 (USSR oblasts/krai)
- **Status**: **INCOMPLETE / stalled** since 2018. "Premature drafts" only.
- **Note**: If completed would fill the Soviet-era gap. Worth monitoring.

### Russia Summary

| Period | Source | Quality |
|--------|--------|---------|
| 1820s | Imperiia Project (Harvard) | Good (49 gubernii) |
| 1897 | RISTAT + Transcultural Empire | Excellent (full Empire, CC0) |
| 1926 | Transcultural Empire | Good (Soviet oblasts) |
| **1927-1989** | **NO FREELY AVAILABLE SOURCE** | **Major gap** |
| ~1990-1998 | ORNL DAAC (NASA) | Adequate (162 FSU regions) |
| 1993-present | GADM (already in pipeline) | Good |

**Strategy**: Use RISTAT 1897 as the baseline for 1800-1917 (guberniya boundaries
were relatively stable in the late Imperial period). Use Transcultural Empire 1926
for early Soviet. For 1927-1993, the ORNL DAAC ~1998 boundaries serve as a rough
proxy for the late Soviet configuration.

---

## 6. SPAIN (full gap)

Spain's provinces have been essentially unchanged since the 1833 Javier de Burgos
reform, making current boundaries a valid historical proxy for 1833-present.

### 6.1 CNIG/IGN Spain -- Official Boundaries

- **URL**: https://centrodedescargas.cnig.es/CentroDescargas/busquedaSerie.do?codSerie=LILIM
- **datos.gob.es**: https://datos.gob.es/en/catalogo/e00125901-spaignllm
- **Coverage**: Current boundaries (no historical versions)
- **Admin levels**: Municipalities, 50 provinces, 17 autonomous communities + 2 cities
- **Format**: Shapefile, GML. CRS: ETRS89 (mainland), REGCAN95/WGS84 (Canaries).
- **Scale**: 1:25,000
- **License**: IGN open use license (free with attribution, including commercial)
- **Programmatic**: WFS at https://www.ign.es/wfs-inspire/unidades-administrativas,
  WMS, ATOM feed, CNIG Download Center

### 6.2 mapSpain R Package

- **URL**: https://ropenspain.github.io/mapSpain/
- **CRAN**: https://cran.r-project.org/web/packages/mapSpain/
- **DOI**: 10.5281/zenodo.5366622
- **Coverage**: Current (CartoBase SIANE data spanning 2006-2024)
- **License**: CC BY 4.0 (for CartoBase SIANE data)
- **Programmatic**: `esp_get_ccaa()`, `esp_get_prov_siane()`, `esp_get_munic_siane()`

### 6.3 HGIS de las Indias -- Colonial Spanish America (1701-1808)

- **URL**: https://dataverse.harvard.edu/dataverse/hgis-indias
- **Coverage**: 1701-1808 (Spanish colonial America, NOT metropolitan Spain).
  11 hierarchical admin levels. CC BY 4.0.
- **Key datasets**:
  - Territorial gazetteer: doi:10.7910/DVN/YPEU5E (1,000+ admin units with dates)
  - Basemaps: doi:10.7910/DVN/HZJGKA (7 dates: 1701, 1725, 1750, 1775, 1787, 1800, 1808)
- **Note**: Covers colonies, not Spain itself. Relevant to loss of American colonies.

### 6.4 Eurostat GISCO NUTS (2003-2024)

- **Spain mapping**: NUTS 1 = groups of CCAA; NUTS 2 = autonomous communities;
  NUTS 3 = provinces. Spain's NUTS 3 = provinces stable since 1833.

### Spain Summary

| Period | Source | Quality |
|--------|--------|---------|
| 1800-1833 | **No GIS data** (pre-Burgos reform) | Gap |
| **1833-present** | CNIG/mapSpain (proxy: current = historical) | **Good** |
| 1701-1808 (colonies) | HGIS de las Indias | Excellent |
| 2003-2024 | Eurostat GISCO NUTS | Good |

**Key finding**: Since Spain's 50 provinces have been unchanged since 1833, the
current CNIG/IGN boundaries serve as a valid proxy for the entire 1833-2025 period.
Only the 1800-1833 window (pre-Burgos reform, historic kingdoms/regions system)
lacks coverage, and no ready-made GIS dataset exists for it.

---

## 7. INDIA (full gap)

India is one of the most challenging countries due to the complexity of British
India's administrative geography (directly-ruled provinces + hundreds of Princely
States) and frequent post-independence state reorganizations.

### 7.1 Appraising Risk -- Census Districts 1872-1891

- **URL**: https://www.appraisingrisk.com/2020/10/23/digitization-of-indian-census-districts-1872-to-present/
- **Coverage**: Administrative district boundaries of British India from 1872.
  Shapefiles for 1872, 1881, 1891 (being finalized).
- **Format**: Shapefiles
- **License**: Academic (check project site)
- **Access**: Contact project team (Indian Ocean World Centre)
- **Key strength**: "The only known shapefiles yet produced of the administrative
  boundaries of late 19th century and early 20th century India."

### 7.2 India State Stories -- State Boundaries 1941-2024

- **URL**: Not publicly downloadable
- **Coverage**: Indian state boundaries from 1941 through 2024
- **Access**: Email request required
- **Key events covered**: States Reorganisation Act 1956, creation of new states
  (Jharkhand, Uttarakhand, Chhattisgarh 2000; Telangana 2014)

### 7.3 IPUMS International -- Census Boundaries

- **URL**: https://international.ipums.org/international/
- **Coverage**: Indian census boundaries for available census years
- **Format**: Shapefile
- **License**: Free registration required; redistribution restricted

### 7.4 SOI (Survey of India) -- Current Official

- **URL**: https://onlinemaps.surveyofindia.gov.in/
- **Coverage**: Current administrative boundaries
- **Note**: Official source but limited historical coverage

### India Summary

| Period | Source | Quality |
|--------|--------|---------|
| 1800-1871 | **No GIS data** | Gap |
| 1872-1891 | Appraising Risk (contact required) | Limited |
| 1891-1941 | **No freely available source** | Gap |
| 1941-2024 | India State Stories (email request) | Unknown |
| Current | SOI / GADM | Good |

**Strategy**: Contact Appraising Risk for 1872 shapefiles. For 1947-present,
the States Reorganisation Commission report (1955) and subsequent acts provide
the textual basis for reconstructing boundaries, but no comprehensive vector
dataset is freely available.

---

## 8. INDONESIA (full gap)

Indonesia is the most challenging of the 11 countries. No comprehensive historical
vector boundary dataset exists. The frequent *pemekaran* (administrative splits)
created 38 provinces from an original 10.

### 8.1 FAO GAUL 2015 -- Annual Layers 1990-2014

- **URL**: https://data.apps.fao.org/catalog/dataset/global-administrative-unit-layers-gaul-2015
- **Google Earth Engine**: FAO_GAUL_2015_level1
- **Coverage**: **1990-2014** (annual layers). Captures the critical pemekaran wave.
- **Format**: Shapefile (FAO), FeatureCollection (Earth Engine)
- **License**: Non-commercial use; restricted distribution (authorized institutions)
- **Programmatic**: Via Google Earth Engine (free for research)
- **Key strength**: The ONLY readily available dataset tracking Indonesian provincial
  boundary changes over time.

### 8.2 GADM 4.1 -- Current

- **URL**: https://gadm.org/download_country.html
- **Coverage**: Current snapshot (~2020, 34 provinces). Does NOT include 2022 Papua splits.
- **Programmatic**: R package `geodata::gadm()`

### 8.3 BIG (Badan Informasi Geospasial) -- Official

- **URL**: https://tanahair.indonesia.go.id/portal-web/
- **Coverage**: Current official (38 provinces including 2022 Papua splits)
- **Format**: Shapefile, web services
- **License**: Indonesian government open data
- **REST**: https://geoservices.big.go.id/rbi/rest/services/BATASWILAYAH/

### 8.4 HDX (Humanitarian Data Exchange)

- **URL**: https://data.humdata.org/dataset/cod-ab-idn
- **Coverage**: Current (2020 boundaries, reviewed Oct 2024)
- **Format**: Shapefile, GeoJSON. License: Humanitarian use.

### 8.5 GitHub: batas-administrasi-indonesia

- **URL**: https://github.com/Alf-Anas/batas-administrasi-indonesia
- **Coverage**: Current (38 provinces, updated June 2023 with Papua splits)
- **Format**: Shapefile, KML, GeoJSON, GeoPackage

### 8.6 Historical Reference (Raster Only)

- **Yale-NUS Digital Historical Maps of SE Asia**: https://historicalmaps.yale-nus.edu.sg/
  (1,400+ digitized maps, includes Dutch colonial maps. Raster only.)
- **KITLV/KIT Dutch Colonial Map Collection** (Leiden University):
  https://digitalcollections.universiteitleiden.nl/dutchcolonialmapskit
  (~11,500 map sheets. Raster only.)

### Indonesian Provincial Timeline

| Year | Provinces | Key Changes |
|------|-----------|-------------|
| 1950 | 10 | Original at independence |
| 1957-58 | ~20 | Major splits (Kalimantan x3, Sumatra splits) |
| 1963 | ~25 | West Papua incorporated |
| 1976 | 27 | East Timor annexed |
| 1999 | 26 | East Timor independence |
| 1999-2004 | 33 | Pemekaran: Banten, Gorontalo, West Papua, etc. |
| 2012 | 34 | North Kalimantan |
| 2022 | 38 | Papua split into 4 new + Southwest Papua |

### Indonesia Summary

| Period | Source | Quality |
|--------|--------|---------|
| Pre-1945 | **No vector data** (raster colonial maps only) | Not feasible |
| 1945-1990 | **No source** (reconstruct by merging current) | Manual work |
| **1990-2014** | FAO GAUL (annual layers) | Adequate |
| Current | BIG / HDX / GitHub | Good |

**Strategy**: Use FAO GAUL for 1990-2014. For 1945-1990, reconstruct by merging
current province polygons back together following the documented split timeline.
For the Dutch colonial period, no vector datasets exist.

---

## 9. CANADA (1800-1999 gap)

### 9.1 Statistics Canada -- Census Boundary Files

- **URL**: https://www12.statcan.gc.ca/census-recensement/2021/geo/sip-pis/boundary-limites/index-eng.cfm
- **Coverage**: Census years from 1991 (digital). Earlier boundaries from cartographic files.
- **Format**: Shapefile, GML
- **License**: Statistics Canada Open Licence

### 9.2 Natural Resources Canada -- Historical Provinces

- Canada's provinces have been relatively stable since Confederation (1867).
  Major changes: Manitoba expansion (1912), Alberta/Saskatchewan created (1905),
  Newfoundland joined (1949), Nunavut created (1999).
- Historical maps available through Natural Resources Canada / Library and Archives.
- No comprehensive historical boundary GIS dataset identified.

### Canada Summary

| Period | Source | Quality |
|--------|--------|---------|
| 1867-1999 | Reconstruct from known dates | Manual (few changes) |
| 1999-present | GADM (already in pipeline) | Good |

**Note**: Canada's provincial boundary changes are few and well-documented enough
to reconstruct manually from modern GADM polygons.

---

## 10. AUSTRALIA (1800-1901 gap)

### 10.1 Already Covered

Australia's state/territory boundaries have been essentially fixed since federation
(1901). GADM 3.6 covers 1901-2025 with 11 units. The main pre-1901 change was
the separation of Queensland from New South Wales (1859) and the various colonial
boundary adjustments, but these can be reconstructed from the current shapes.

---

## 11. CHINA (1912-1997 gap)

### 11.1 CHGIS v6 -- Already Integrated (1820-1912)

26 Qing province polygons added as subnational entries. See doc 12, Section 2.3.

### 11.2 Gap: Republic of China + PRC (1912-1997)

No freely available comprehensive historical GIS dataset covers Chinese provincial
boundaries for the Republic of China (1912-1949) or early PRC (1949-1997) periods.
The CHGIS project focuses on the imperial period (pre-1912).

For the ROC period (1912-1949), the 35-province system was relatively similar to
the late Qing structure. For the early PRC, major changes include: creation of
autonomous regions (Inner Mongolia 1947, Xinjiang 1955, Guangxi/Ningxia 1958,
Tibet 1965), creation and dissolution of various provinces, and the Hainan
separation from Guangdong (1988) and Chongqing from Sichuan (1997).

---

## 12. Cross-Cutting Sources

### 12.1 FAO GAUL 2015

- **Coverage**: Global, 1990-2014 (annual layers at admin-1 and admin-2)
- **Access**: Google Earth Engine (free for research); FAO direct download (authorization)
- Useful for: France, Spain, Indonesia, and any other country where 1990-2014
  changes matter.

### 12.2 Eurostat GISCO NUTS

- **Coverage**: EU/EFTA countries, 2003-2024 (7 snapshots, NUTS 0-3)
- Useful for: France (NUTS 3 = departements), Spain (NUTS 3 = provinces),
  Germany (NUTS 1 = Lander)

### 12.3 geoBoundaries

- **URL**: https://www.geoboundaries.org/
- **Coverage**: All UN member states, current boundaries only
- **License**: CC BY 4.0 / ODbL
- Useful as a modern reference baseline for all countries.

### 12.4 IPUMS International

- **URL**: https://international.ipums.org/international/
- Census boundary files for many countries at various census years.
- Registration required.

---

## 13. Consolidated Actionability Matrix

### Tier 1: Immediate Integration (R package, one-liner)

| Country | Source | Period | Programmatic | License | Effort |
|---------|--------|--------|-------------|---------|--------|
| **USA** | USAboundaries | 1783-2000 | `us_states(map_date=...)` | CC BY-NC-SA 2.5 | **DONE** |
| **Brazil** | geobr | 1872-2020 | `read_state(year=...)` | MIT/public | **DONE** |
| **Spain** | mapSpain | Current (= 1833+) | `esp_get_prov_siane()` | CC BY 4.0 | **DONE** |

### Tier 2: Download and Process (free, moderate effort)

| Country | Source | Period | Format | License | Effort |
|---------|--------|--------|--------|---------|--------|
| **France** | TRF-GIS | 1870-1940 | SHP | CC BY 4.0 | **Low** |
| **France** | French HGIS | c. 1790 | SHP | Academic | **Low** |
| **Germany** | HGIS Germany (NYU) | 1820-1914 | SHP/GeoJSON | Academic free | **Low** |
| **Russia** | RISTAT | 1897 | GeoPackage | CC0 | **Low** |
| **Russia** | Imperiia (Harvard) | 1820s | SHP | Academic | **Low** |
| **Russia** | Transcultural Empire | 1897+1926 | SHP | Open access | **Low** |
| **Russia** | ORNL DAAC (NASA) | ~1998 | SHP | Open | **Low** |

### Tier 3: Contact Required or Restricted

| Country | Source | Period | Access | Effort |
|---------|--------|--------|--------|--------|
| **India** | Appraising Risk | 1872-1891 | Contact project | **Medium** |
| **India** | India State Stories | 1941-2024 | Email request | **Medium** |
| **Indonesia** | FAO GAUL | 1990-2014 | Earth Engine (free) | **Medium** |

### Tier 4: Not Currently Feasible

| Country | Gap | Reason |
|---------|-----|--------|
| **Russia** | 1927-1989 | No completed dataset exists |
| **Indonesia** | 1945-1990 | Must reconstruct manually |
| **China** | 1912-1997 | No freely available dataset |
| **India** | 1800-1871, 1891-1941 | No freely available dataset |
| **Germany** | 1914-1990 | No freely available subnational GIS |

---

## 14. Recommended Next Steps

### Phase 1: Immediate (R package integration) -- COMPLETED

1. **DONE**: Extracted US state/territory boundaries (1800-1958) via USAboundaries.
   51 entries added. Script: `R/14_integrate_historical_subnational.R`.
   Output: `data/geodata/us_historical_states.gpkg`.
2. **DONE**: Extracted Brazilian state boundaries (1872-1987) via geobr (1980 snapshot).
   26 entries added. Output: `data/geodata/brazil_historical_states.gpkg`.
3. **DONE**: Extracted Spanish province boundaries (1833-2025) via mapSpain.
   52 entries added. Output: `data/geodata/spain_provinces.gpkg`.

### Phase 2: Download and Process

4. Download TRF-GIS departement boundaries (1870 snapshot) and French HGIS (1790
   snapshot) from Harvard Dataverse for French subnational coverage.
5. Download HGIS Germany 1820 state boundaries from NYU/Stanford for German
   subnational coverage of the pre-unification period.
6. Download RISTAT 1897 GeoPackage and Imperiia 1820s shapefiles for Russian
   Imperial subnational coverage.
7. Download Transcultural Empire 1926 shapefiles for early Soviet coverage.

### Phase 3: Contact and Restricted Access

8. Contact Appraising Risk project for Indian 1872 census district shapefiles.
9. Access FAO GAUL via Google Earth Engine for Indonesian 1990-2014 provinces.
10. Request India State Stories dataset for 1941-2024 state boundaries.

---

## 15. Sources Consulted

### R Packages
- USAboundaries: https://github.com/ropensci/USAboundaries
- geobr: https://github.com/ipeaGIT/geobr
- mapSpain: https://ropenspain.github.io/mapSpain/
- giscoR: https://ropengov.github.io/giscoR/
- Guerry: https://cran.r-project.org/web/packages/Guerry/

### Academic Vector Datasets
- Newberry Library AHCB: https://publications.newberry.org/ahcb/
- NHGIS (IPUMS): https://www.nhgis.org/gis-files
- US History Maps (poezn): https://poezn.github.io/us-history-maps/
- IBGE Territorial Division: https://geoftp.ibge.gov.br/organizacao_do_territorio/
- Stanford EarthWorks (Brazil): https://earthworks.stanford.edu/catalog/stanford-tj392fk5522
- TRF-GIS France: https://dataverse.harvard.edu/dataverse/TRF-GIS
- French Historical GIS: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/HJISNR
- Geo-Larhra: http://geo-larhra.ish-lyon.cnrs.fr/
- HGIS Germany at NYU: https://geo.nyu.edu/ (search "ghgis")
- HGIS Germany at Stanford: https://earthworks.stanford.edu/?q=hgis+germany
- Imperiia Project: https://dataverse.harvard.edu/dataverse/ImperiiaGIS
- RISTAT: https://datasets.iisg.amsterdam/dataset.xhtml?persistentId=hdl:10622/DN9QDM
- Transcultural Empire GIS: https://heidata.uni-heidelberg.de/dataset.xhtml?persistentId=doi:10.11588/data/10064
- ORNL DAAC FSU: https://doi.org/10.3334/ORNLDAAC/699
- HGIS de las Indias: https://dataverse.harvard.edu/dataverse/hgis-indias
- Appraising Risk India: https://www.appraisingrisk.com/2020/10/23/digitization-of-indian-census-districts-1872-to-present/

### Official Boundary Sources
- IGN France (ADMIN EXPRESS): https://geoservices.ign.fr/adminexpress
- CNIG/IGN Spain: https://centrodedescargas.cnig.es/
- BIG Indonesia: https://tanahair.indonesia.go.id/portal-web/
- Survey of India: https://onlinemaps.surveyofindia.gov.in/
- Statistics Canada: https://www12.statcan.gc.ca/census-recensement/2021/geo/

### Global/Multi-Country
- FAO GAUL 2015: https://data.apps.fao.org/catalog/dataset/global-administrative-unit-layers-gaul-2015
- Eurostat GISCO NUTS: https://ec.europa.eu/eurostat/web/gisco/geodata/statistical-units/territorial-units-statistics
- geoBoundaries: https://www.geoboundaries.org/
- HDX Indonesia: https://data.humdata.org/dataset/cod-ab-idn
- IPUMS International: https://international.ipums.org/international/

### Community / GitHub
- france-geojson: https://github.com/gregoiredavid/france-geojson
- batas-administrasi-indonesia: https://github.com/Alf-Anas/batas-administrasi-indonesia
- Russian-GIStory: https://github.com/Emelieh21/russian-gistory
- Yale-NUS Historical Maps of SE Asia: https://historicalmaps.yale-nus.edu.sg/
- KITLV/KIT Colonial Maps: https://digitalcollections.universiteitleiden.nl/dutchcolonialmapskit
