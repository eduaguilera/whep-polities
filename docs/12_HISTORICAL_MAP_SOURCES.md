# Historical Map Sources for Pre-1886 Boundary Digitization

Research compiled 2026-03-27. Focus: digitized historical atlases, academic GIS
projects, and vector boundary datasets that could fill the CShapes pre-1886 gap
for the WHEP polities database (1800-1886).

---

## Executive Summary

The pre-1886 period is the weakest part of the WHEP polygon pipeline. CShapes 2.0
starts at 1886; CShapes-Europe extends to 1816 but only for ~46 European entities.
For all other regions (Africa, Asia, Americas, Oceania), polygons before 1886 are
back-projected from the earliest CShapes snapshot, producing significant territorial
inaccuracies documented in `docs/08_POLYGON_ACCURACY_AUDIT.md`.

This research identifies **28 sources** across 5 categories that could provide or
help create accurate pre-1886 vector boundaries. The most actionable are marked with
priority ratings.

---

## 1. Scanned/Digitized Historical Atlases

### 1.1 David Rumsey Map Collection -- REFERENCE ONLY

- **URL**: https://www.davidrumsey.com/
- **Coverage**: 200,000+ maps, heavy focus on 16th-21st century. Includes:
  - Colton's General Atlas of the World (1865, 1870, 1875, 1880, 1886)
  - Mitchell's New General Atlas (1870, 1880, 1890)
  - Stieler's Handatlas (multiple editions)
  - Numerous 19th century political wall maps and school atlases
- **Georeferencing status**: All maps have been georeferenced using GIS control
  points (up to 200 per map). Georeferencer v4 is built into the site. Export
  available as GeoTIFF, KML, WMS tiles.
- **Format**: Raster (high-resolution scans). NOT vector data. Would require
  manual heads-up digitizing to create polygons.
- **License**: Free to browse. High-resolution downloads available. Educational
  use generally permitted. Commercial use requires permission.
- **Quality**: Very high-resolution scans with professional georeferencing.
  Excellent reference for verifying boundaries but substantial manual work
  needed to extract vector polygons.
- **Relevance to WHEP**: Best used as reference source for verifying boundaries
  digitized from other sources. Colton's 1865 and 1880 atlases show global
  political boundaries at key dates in our 1800-1886 gap. Not practical as a
  primary data source due to the labor required to vectorize.

### 1.2 Shepherd's Historical Atlas -- PUBLIC DOMAIN, REFERENCE ONLY

- **URL (UT Austin)**: https://maps.lib.utexas.edu/maps/historical/history_shepherd_1923.html
- **URL (Internet Archive)**: https://archive.org/details/HistoricalAtlasWilliamR.Shepherd
- **URL (Wikimedia)**: https://commons.wikimedia.org/wiki/Category:Historical_Atlas_by_William_R._Shepherd
- **Coverage**: World history from ancient to early 20th century. 1911, 1923, and
  1926 editions digitized. Includes 19th century political maps of Europe, Asia,
  Africa, and the Americas.
- **Format**: Raster scans (JPEG/PNG). NOT georeferenced. NOT vector.
- **License**: **Public domain** (published pre-1927). Can be freely used.
- **Quality**: Good scholarly atlas but maps are schematic, not precisely
  cartographic. Lower spatial accuracy than Rumsey collection maps.
- **Relevance to WHEP**: Public domain status is a major advantage. Maps of
  Europe after Congress of Vienna, Ottoman Empire, colonial Africa, and Latin
  American independence could be georeferenced and vectorized. However, the
  effort would be substantial and the spatial accuracy limited.

### 1.3 Putzger Historischer Weltatlas -- LIMITED ACCESS

- **URL (Internet Archive)**: https://archive.org/details/putzgerhistorisc0000unse
- **URL (Library of Congress)**: https://www.loc.gov/item/2013591295/
- **Coverage**: World history atlas, focus on Europe. First published 1877,
  continuously updated (now 105th edition). Excellent 19th century political
  maps of Europe, German states, and Central European territorial changes.
- **Format**: Raster scans of older editions available on Internet Archive.
  Current editions are commercial print. NOT vector.
- **License**: Pre-1927 editions are public domain. Modern editions copyrighted
  (Cornelsen Verlag).
- **Quality**: Extremely detailed for German and Central European boundaries.
  The standard German historical atlas for over a century.
- **Relevance to WHEP**: The early editions (pre-1927) could provide reference
  for German pre-unification states and Central European boundaries, but HGIS
  Germany (Section 2.3) already provides this as vector data.

### 1.4 Ajayi & Crowder, Historical Atlas of Africa (1985) -- KEY SOURCE

- **URL**: Not digitized online (print only, Cambridge University Press)
- **Coverage**: 7 detailed regional maps of 19th century Africa showing
  pre-colonial state boundaries, each produced by a leading regional scholar.
- **Format**: Print atlas. However, this atlas was the primary source used by
  Paine, Qiu & Ricart-Huguet (2024) to create their digitized pre-colonial
  African states dataset (see Section 2.1).
- **License**: Copyrighted, but the vectorized derivatives from Paine et al.
  are available under academic license.
- **Quality**: The definitive scholarly source for pre-colonial African political
  boundaries. CShapes itself cites Brownlie (1979) which is complementary.
- **Relevance to WHEP**: **HIGH**. Directly relevant to ETH-1800-1889,
  ZAN-1800-1964, MOR-1800-1904, MAD-1800-1912, EGY-1800-1899. The Paine et al.
  vectorization (Section 2.1) is the practical way to use this source.

---

## 2. Academic/Research Projects with Vector Boundaries

### 2.1 Paine, Qiu & Ricart-Huguet (2024) Pre-Colonial African States -- PRIORITY HIGH

- **URL**: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/9QJVJ1
- **Paper**: "Endogenous Colonial Borders: Precolonial States and Geography in
  the Partition of Africa", APSR Vol. 119(1), pp. 1-20.
- **Coverage**: 46 digitized pre-colonial African state polygons, derived from
  Ajayi & Crowder (1985). Covers states existing on the eve of European
  colonization (~1880s).
- **Format**: Shapefile (`PCS.shp`, 929 KB) in `Shapefiles/Precolonial states/`
  directory. 7 files total (.shp, .dbf, .shx, .prj, .cpg, .sbn, .sbx).
  Attributes: PCS (state name), Source (reference map), Index, Legend.
  No login required to download.
- **Coordinate system**: WGS 84
- **License**: Harvard Dataverse -- free download, no login required. Terms state
  "not to be distributed/posted outside of Harvard Dataverse" (downloads must
  come directly from Dataverse)
- **Quality**: Peer-reviewed (APSR is top-tier). Digitized by trained researchers
  from the most authoritative source (Ajayi & Crowder). Authors use 0.25-degree
  buffers (~25 km) around boundaries for robustness checks, acknowledging
  inherent uncertainty in pre-colonial boundary placement.
- **Complete list of 46 states**:
  - **Core states (all sources agree)**: Asante, Benin Kingdom, Borno, Buganda,
    Bunyoro, Burundi, Cayor, Dahomey, Darfur, Ethiopia, Futa Jalon, Jolof,
    Kazembe/Lunda East, Lesotho, Luba, Mwata Yamvo/Lunda West, Nkore (Ankole),
    Rwanda, Sokoto, Wadai, Walo, Zulu
  - **Additional**: Bemba, Bundu, Kasanje, Lozi, Ndebele, Porto Novo, Salum, Sine
  - **North African**: Egypt, Morocco, Tunis
  - **Case-by-case inclusion**: Borgu, Dagomba, Damagaram, Futa Toro, Gaza,
    Gobir, Igala, Mossi, Swazi, Egba, Ibadan, Ijebu, Oyo
- **Specific relevance**:
  - **ETH-1800-1889**: Includes pre-Menelik Ethiopia (CRITICAL fix, 2-3x oversize)
  - **ZAN-1800-1890**: May include Zanzibar Sultanate mainland (CRITICAL fix)
  - **MOR-1800-1904**: May include Morocco (MAJOR fix, bled al-makhzen)
  - **MAD-1800-1912**: May include Merina Kingdom (MODERATE fix)
  - Also relevant to EGY, various West African entities
  - Paine et al. explicitly demonstrate that the Murdock ethnographic map (843
    ethnic groups) should NOT be used as a proxy for state boundaries

### 2.2 HGIS Germany (1820-1914) -- PRIORITY HIGH, NOT YET INTEGRATED

- **Main page**: http://www.digihist.de/html/hgisg/index.htm (interactive maps only,
  no direct downloads; HTTPS certificate broken, use HTTP)
- **Download (recommended)**: NYU Spatial Data Repository — search for "ghgis" at
  https://geo.nyu.edu/. Individual datasets follow the pattern:
  `https://geo.nyu.edu/catalog/harvard-ghgisYYYYcore` (state boundaries)
  `https://geo.nyu.edu/catalog/harvard-ghgisYYYYdistricts` (districts)
  `https://geo.nyu.edu/catalog/harvard-ghgisYYYYprovinces` (provinces)
- **Alternative mirrors**: Stanford EarthWorks (https://earthworks.stanford.edu/?q=hgis+germany),
  Harvard Geospatial Library (https://hgl.harvard.edu, has WAF challenge in browser)
- **Available time slices** (state boundaries / Bundesstaaten): 1820, 1826, 1830,
  1834, 1839, 1848, 1850, 1867, 1871, 1890, 1914
- **Also available**: Provincial boundaries (1820-1914), district boundaries (1820-1914),
  state capitals, German Empire boundary 1871, railways (1835-1885), canals and roads
- **NOTE**: The early period (1648-1812 Imperial States) and 20th century (1921-1993)
  appear available only as interactive web maps on digihist.de, NOT as downloadable shapefiles.
- **Format**: Shapefile and GeoJSON, EPSG:4326 (WGS 84)
- **License**: Free for non-commercial academic research. No authentication required.
- **Quality**: Created by Andreas Kunz and Leonhard Dietze at Institut fuer
  Europaeische Geschichte (IEG), Mainz. Professional-grade historical GIS.
- **Specific relevance**:
  - **ALL pre-1871 German states**: BAV, SAX, HAN, WUR, BAD, HES, OLD, MEK,
    THU, BRE, SHL, and all the micro-states (Anhalt, Nassau, Reuss, Waldeck,
    Lippe, Schaumburg-Lippe, Saxe-Weimar, Saxe-Meiningen, etc.)
  - Currently these use GADM 4.1 (modern Laender) or CShapes-Europe -- both
    are known to be inaccurate proxies (see Section 4 of polygon audit)
  - HGIS Germany would replace ALL of these with accurate historical polygons
  - **38 of 41 German Confederation states in 1820 are included**
- **WHEP integration status**: Not yet integrated. German states currently use
  GADM/CShapes proxies. Downloading the 1820 state boundary shapefile from NYU
  would be the next step if replacing these proxies is desired.
- **Download status (2026-03-27)**: Harvard GeoServer proxy (`geodata-proxy.lib.harvard.edu`)
  is decommissioned (no DNS A record). All programmatic download attempts fail.
  NYU requires email-based request. Harvard HGL behind AWS WAF bot protection.
  Manual browser download or email request to Harvard (`hgl_ref@hulmail.harvard.edu`)
  or NYU is required.

### 2.3 CHGIS -- China Historical GIS (Harvard/Fudan) -- INTEGRATED (provinces)

- **URL**: https://chgis.fas.harvard.edu/
- **Download**: https://dataverse.harvard.edu/dataverse/chgis_v6
- **Coverage**: Administrative boundaries for all Chinese dynasties. Key datasets:
  - **1820 time-slice** (Qing Dynasty): ~9,000 placenames, provinces, circuits,
    prefectures, and counties
  - **1911 time-slice** (late Qing / early Republic)
  - **Time series** (221 BCE to 1911 CE): county and prefecture changes over time
- **Format**: Shapefiles
- **Coordinate system**: WGS 84
- **License**: Free for academic use, no commercial use or redistribution.
  Citation: "CHGIS, Version: 6. (c) Fairbank Center for Chinese Studies,
  Harvard University and Center for Historical Geographical Studies, Fudan
  University, 2016."
- **Quality**: Premier scholarly resource for Chinese historical geography.
  Joint Harvard-Fudan project. Provinces, prefectures, counties all digitized.
- **Assessment (2026-03-27)**: Downloaded and examined v6 data (`inputs/chgis.zip`).
  Contains two useful levels:
  - **Province polygons (`v6_1820_prov_pgn_utf`)**: 32 records, 26 administered
    provinces (excl. 5 SCS island claims + 1 treaty-disputed area). Total area
    13.1M km2. **INTEGRATED** as subnational entries (1820-1912).
  - **Prefecture polygons (`v6_time_pref_pgn`)**: 3,830 records, too granular for
    polity-level analysis.
  No top-level "Qing Empire" outer boundary polygon; sovereign CHN entries already
  covered by CShapes. Cliopatria has Qing outer boundary (31 time-steps, ~12.5M km2).
- **WHEP integration (2026-03-27)**: 26 Qing province polygons added as subnational
  entries. Script: `R/13_integrate_chgis_provinces.R`.
  Output: `data/geodata/chgis_qing_provinces.gpkg`.
  Data file: `inputs/chgis.zip` (not committed; download doi:10.7910/DVN/ST5KKM).

### 2.4 HGIS de las Indias -- Colonial Spanish America -- MODERATE PRIORITY

- **URL**: https://hgis-indias.net/
- **Download**: https://dataverse.harvard.edu/dataverse/hgis-indias
- **Coverage**: Territorial organization of the Spanish Empire in the Americas,
  1701-1808. 11 administrative levels including audiencias, intendencias,
  provinces, jurisdictions, dioceses, and frontier areas. 13,000+ place records,
  1,400+ territory records.
- **Format**: GeoPackage and shapefiles
- **Coordinate system**: WGS 84
- **License**: **Creative Commons 4.0** (open access)
- **Quality**: Funded by Austrian Science Fund (FWF), created by Dr. Werner
  Stangl (Universitaet Graz). Published academic project.
- **Specific relevance**:
  - Time range (1701-1808) partially overlaps our 1800-1886 window
  - Relevant to early independence-era South American boundaries, though the
    post-independence period (1810-1886) is NOT covered
  - Could help establish 1800-1810 baselines for ARG, BRA, COL, ECU, CHL,
    PER, BOL, PRY, VEN before independence reshuffled boundaries
  - The CC 4.0 license is highly favorable

### 2.5 TRF-GIS -- Third Republic France (1870-1940) -- MODERATE PRIORITY

- **URL**: https://dataverse.harvard.edu/dataverse/TRF-GIS
- **Paper**: Gay, V. (2021) "Mapping the Third Republic", Historical Methods,
  54(4).
- **Coverage**: Annual administrative boundaries of metropolitan France
  1870-1940: departements, arrondissements, cantons. Also special constituencies
  (military, judicial, electoral, academic, etc.). 830 shapefiles total.
- **Format**: Shapefiles
- **License**: Academic (Harvard Dataverse)
- **Quality**: Published in peer-reviewed journal. Comprehensive annual coverage.
- **Specific relevance**:
  - FRA-1800-1919: Would provide accurate French departement boundaries from
    1870 onward (overlapping our gap period)
  - French internal administrative boundaries are stable but the
    Alsace-Lorraine loss (1871) is a significant territorial change that this
    dataset captures annually

### 2.6 French Historical GIS Dataverse (1790-) -- MODERATE PRIORITY

- **URL**: https://dataverse.harvard.edu/dataverse/french-historical-gis
- **Coverage**: French regions and departement boundaries from c. 1790 onward.
  Extends earlier than TRF-GIS.
- **Format**: Shapefiles
- **License**: Academic
- **Specific relevance**: Extends French coverage back to 1790, covering the
  full 1800-1870 gap that TRF-GIS does not reach.

### 2.7 Appraising Risk -- Indian Census Districts (1872-present) -- PRIORITY HIGH

- **URL**: https://www.appraisingrisk.com/2020/10/23/digitization-of-indian-census-districts-1872-to-present/
- **Coverage**: Administrative district boundaries of British India from 1872
  onward, including both British districts and Princely States. Shapefiles for
  1872, 1881, 1891 (still being finalized as of last report).
- **Format**: Shapefiles
- **License**: Academic (check project site for current terms)
- **Quality**: Uses automated processing and tracing algorithms developed at
  the Indian Ocean World Centre. "The only known shapefiles yet produced of
  the administrative boundaries of late 19th century and early 20th century
  India."
- **Specific relevance**:
  - **IND-1800-1893**: Would provide actual 1872/1881 boundaries of British
    India including Princely States, rather than back-projecting modern India.
  - Critical for understanding the patchwork of British directly-ruled
    territories vs. hundreds of Princely States.
  - The 1872 boundary shows India BEFORE the Second Afghan War and BEFORE
    the annexation of Upper Burma (1886).

### 2.8 HistoGIS (ACDH-CH Austria) -- **INTEGRATED (2026-04-17)**

- **URL**: https://histogis.acdh.oeaw.ac.at/
- **Direct download (1860 crownlands)**: https://shared.acdh.oeaw.ac.at/histogis/austrian_empire_adm2_crownlands_1860.zip
- **Coverage**: Habsburg Empire / Austria-Hungary administrative boundaries.
  Includes:
  - Austrian Empire Crownlands 1860 (directly downloaded and integrated)
  - Austro-Hungarian Empire court districts 1910
  - Albania municipal level 1918
  - Serbia districts
- **Format**: Shapefiles (GeoDjango-based platform)
- **License**: Open access (ACDH-CH, Austrian Academy of Sciences)
- **Quality**: Institutional academic project. Good for Habsburg internal
  boundaries. Digitized from Floder 1835 + multiple Rumsey Collection maps.
- **Status**: **INTEGRATED** for AUT-1800-1918 and HUN-1800-1918.
  - Downloaded: `data/geodata/histogis/austrian_empire_adm2_crownlands_1860.zip`
  - Script: `R-legacy/25_integrate_histogis_habsburg.py`
  - Output: `data/geodata/histogis/habsburg_cisleithania_transleithania.gpkg`
  - Cisleithania polygon (AUT-1800-1918): 14 crownlands dissolved (excl. Venetia)
  - Transleithania polygon (HUN-1800-1918): 5 crownlands dissolved (Hungary,
    Transylvania, Croatia-Slavonia, Banat, Military Frontier)
- **Specific relevance**:
  - **AUT-1800-1918** (Cisleithania): Polygon now assigned from this source.
  - **HUN-1800-1918** (Transleithania): Polygon now assigned from this source.
  - The 1910 court-district dataset gives the finest-grained Habsburg
    boundaries ever produced (not yet integrated).

### 2.9 CensusMosaic / MPIDR Population History GIS -- MODERATE PRIORITY

- **URL**: https://censusmosaic.demog.berkeley.edu/data/historical-gis-files
  and https://mosaic.ipums.org/historical-gis-datafiles
- **Coverage**: European state boundaries at 30-year intervals (1900, 1930,
  1960, 1990, 2003). Also includes the Austro-Hungarian Empire 1910 dataset
  (from MPIDR, same as HistoGIS source).
- **Format**: Shapefiles
- **License**: Free for non-commercial scientific purposes with registration
- **Quality**: Max Planck Institute for Demographic Research (MPIDR) collection.
  High institutional quality.
- **Specific relevance**: The 1900 snapshot provides European boundaries very
  close to the end of our gap period. Registration required.

### 2.10 Great Britain Historical GIS (GBHGIS) -- LOW PRIORITY

- **URL**: https://www.visionofbritain.org.uk/data/ (A Vision of Britain
  through Time)
- **Additional**: Cambridge Group boundaries at
  https://www.campop.geog.cam.ac.uk/research/occupations/datasets/catalogues/boundaries/
- **Coverage**: Registration districts, poor law unions (c.1840-1911), local
  government districts (1911-1974), parishes (1870s-1974). County boundaries
  from 1831 and 1851 censuses.
- **Format**: Shapefiles
- **License**: County data free. Parish data commercially licensed (main income
  source). Non-commercial academic requests considered (email gbhgis@port.ac.uk).
- **Quality**: University of Portsmouth. Definitive source for British internal
  boundaries.
- **Specific relevance**: Low for WHEP because GBR-1800-1921 uses CShapes which
  already captures UK's external borders accurately. Internal boundaries not
  needed for this project.

### 2.11 Japan Historical GIS (Harvard) -- MODERATE PRIORITY

- **URL**: https://chgis.fas.harvard.edu/data/japan/
- **Download**: https://dataverse.harvard.edu/dataverse/japan_hgis
- **Coverage**: Tokugawa period (c. 1664, 1820) and Meiji period. Includes
  kuni (province) boundaries and daimyo domains (han).
- **Format**: Shapefiles
- **License**: Free for academic use
- **Quality**: Created by Lex Berman (Harvard CGA). Part of the CHGIS family.
- **Specific relevance**:
  - **JPN-1800-2025**: The 1820 Tokugawa boundaries would show Japan before
    the Meiji Restoration (1868) and the Hokkaido colonization. CShapes
    back-projects modern Japan to 1886, which includes Hokkaido (only fully
    incorporated post-1869) and Okinawa (annexed 1879).
  - Not a critical fix for external boundaries, but useful for internal
    accuracy.

### 2.12 Imperiia Project -- Russian Empire 1820s -- PRIORITY HIGH

- **URL**: https://dataverse.harvard.edu/dataverse/ImperiiaGIS
- **Coverage**: Russian Empire administrative boundaries, **1820s**, digitized from
  the Geographical Atlas of the Russian Empire (Military-Topographical Depot,
  1820-1827). Kingdom and Grand Duchy boundaries.
- **Format**: Shapefiles / GeoPackage
- **License**: Academic (Harvard Dataverse)
- **Quality**: Careful digitization from primary military cartographic sources.
- **Specific relevance**: Provides pre-CShapes Russian Empire boundaries for
  F228-1800-1905. Shows Russia near the start of the 19th century expansion
  into the Caucasus and Central Asia.

### 2.13 RISTAT -- Russian Empire 1897 -- MODERATE PRIORITY

- **URL**: https://ristat.org/ and
  https://datasets.iisg.amsterdam/dataset.xhtml?persistentId=hdl:10622/DN9QDM
- **Coverage**: Russian Empire 1897 at province (guberniya) and district (uezd) level.
  Based on the 1897 Imperial Census. Cleaned by Rombert Stapel (IISH).
- **Format**: GeoPackage, Shapefile
- **License**: Free
- **Specific relevance**: Combined with Imperiia (1820s), brackets the full
  1800-1886 period for the Russian Empire.

### 2.14 GISta Hungarorum -- Hungarian Kingdom 1720s-1910 -- MODERATE PRIORITY

- **URL**: https://www.gistory.hu/g/en/gistory/index
- **Coverage**: Hungarian Kingdom within Austria-Hungary, 1720s-1910. Settlement-level
  boundaries from 1884 (1:350,000 scale). ~7.3 million data entries.
- **Format**: Shapefile, KMZ
- **License**: Free
- **Specific relevance**: Settlement-level detail for the Hungarian portion of
  Austria-Hungary. Useful for AUH-1800-1867 and AUH-1867-1908.

### 2.15 Geo-Larhra -- Italy 1815-1866 -- MODERATE PRIORITY

- **URL**: http://geo-larhra.ish-lyon.cnrs.fr/
- **Geocatalogue**: http://geo-larhra.ish-lyon.cnrs.fr/?q=geocatalogue/vectors
- **Coverage**: Italian state boundaries 1815-1866 (pre-unification). Kingdom of
  Sardinia, Two Sicilies, Papal States, Tuscany, etc.
- **Format**: Shapefiles and raster
- **License**: Open access (CNRS/University of Lyon)
- **Specific relevance**: Directly covers Italian pre-unification states from
  Congress of Vienna to unification. Complements CShapes-Europe Italian entries.

### 2.16 Austrian Silesia and Galicia Datasets -- MODERATE PRIORITY

- **Austrian Silesia**: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/K7YPAF
  (Ostafin et al. 2020, Scientific Data 7:208). Commune/district level 1837-1910.
- **Galicia**: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/PXDP41
  5,944 cadastral communes from 413 map sheets (1:28,800), 1857-1910.
- **Format**: Shapefiles
- **License**: Open
- **Specific relevance**: Sub-national detail for two crownlands of the Austrian Empire.

### 2.17 Cliopatria (Seshat Global History Databank) -- PRIORITY HIGH

- **URL**: https://github.com/Seshat-Global-History-Databank/cliopatria
- **Zenodo**: https://zenodo.org/records/14714684
- **Paper**: Bennett et al. (2025), Nature Scientific Data
- **Coverage**: **3400 BCE to 2024 CE**, worldwide. 15,690 GeoJSON features
  covering 1,600+ polities. For 1800-1886: 1,945 features covering 290+
  polities.
- **Format**: GeoJSON (single file ~198 MB), EPSG:4326 (WGS 84)
- **License**: **CC BY 4.0** (open)
- **Temporal resolution**: Variable. 19th century: often yearly for major polities
  (Ottoman Empire: 33 records; Russian Empire: 34; Qing Dynasty: 31; Qajar Iran: 12).
- **Spatial accuracy**: Hand-traced from reference atlases. Moderate precision
  (~hundreds of vertices per polygon). R-squared ~0.90 vs Taagepera area
  measurements. The project acknowledges "currently unquantified uncertainty"
  in all boundary placements.
- **African polities specifically covered** (with time-steps and approximate areas):
  - **Ashanti Empire**: 1797-1894, 20 time-steps, ~154,508 km2
  - **Sokoto Caliphate**: 1805-1894, 6 time-steps, ~792,706 km2
  - **Ethiopian Empire**: 1769-1894, 2 time-steps, ~240,357 km2
  - **Merina Kingdom** (Madagascar): 1796-1894, 10 time-steps, ~426,715 km2
  - **Bornu Empire**: 1636-1894, 8 time-steps, ~227,106 km2
  - **Zululand**: 1820-1894, 5 time-steps, ~25,464 km2
  - **Morocco**: 1769-1904, 5 time-steps, ~386,205 km2
  - **Zanzibar**: 1856-1889, 2 time-steps, ~28,255 km2
  - **Regency of Algiers**: 1792-1845, 6 time-steps, ~163,203 km2
  - **Khedivate of Egypt / Muhammad Ali dynasty**: multiple entries
  - **Sultanate of Darfur**: 1636-1876, 3 time-steps
  - **Wadai Empire**: 1636-1894, 2 time-steps
  - **Also present**: Majeerteen Sultanate, Sultanate of Hobyo, Mahdist State,
    and others
  - **NOT found by name**: Dahomey and Buganda are not present as named entries
    in the dataset
- **Limitation**: Treats some empires as monolithic aggregates (e.g., "British
  Africa") -- these aggregate entries are unsuitable for per-territory analysis
  of individual colonial possessions.
- **Specific relevance**: **The most comprehensive open-source global polygon source
  for the pre-1886 gap.** Covers Ottoman Empire, Qing Dynasty, Russian Empire,
  Qajar Iran, African kingdoms (Ashanti, Sokoto, Merina, Zululand, etc.),
  Southeast Asian states, and many more.
- **WHEP integration status**: **INTEGRATED** (2026-03-27). 4 polygons extracted for
  polities that had no polygon from any other source:
  - IRN-1800-1828: Qajar Dynasty 1800-1804 (1,743,611 km2)
  - AUH-1800-1867: Austrian Empire 1815-1819 (691,595 km2)
  - SWE-1800-1809: Swedish Empire 1763-1808 (790,005 km2, incl. Finland)
  - SWE-1809-1814: Swedish Empire 1809-1811 (463,631 km2, without Finland)
  Script: `R/12_integrate_cliopatria_polygons.R`. Output: `data/geodata/cliopatria_polygons.gpkg`.
  Additional Cliopatria polygons were NOT extracted for polities already covered by
  CShapes, GADM, or other sources, per project policy.

### 2.18 Historical Atlas of the Low Countries (1350-1800) -- LOW PRIORITY

- **URL**: https://datasets.iisg.amsterdam/dataset.xhtml?persistentId=hdl:10622/PGFYTM
- **Paper**: Stapel, R.J. (2023), Research Data Journal for the Humanities
  and Social Sciences, 8(1), 1-33.
- **Coverage**: Locality-level boundaries for Netherlands, Belgium, Luxembourg,
  adjacent France/Germany. Cross-sections at 1350, 1500, 1650, 1800.
  ~18,000 units per cross-section (~5-10 km2 each).
- **Format**: GIS dataset (check repository for exact format)
- **License**: **Creative Commons** (open access, IISH Data Collection)
- **Quality**: Published academic dataset, CoreTrustSeal-certified repository.
- **Specific relevance**: Low for WHEP. The Netherlands external borders are
  already well-captured by CShapes. Internal boundaries not needed.

---

## 3. Regional GIS Projects

### 3.1 Ottoman Empire -- NO READY-MADE VECTOR DATA

- **Digital Ottoman Studies**: https://www.digitalottomanstudies.com/gis
  (hub for Ottoman GIS projects, but no downloadable boundary shapefiles)
- **SDSU GIS Tool**: https://edoras.sdsu.edu/~eckberg/Ottoman/Ottoman.html
  (educational interactive tool, not downloadable data)
- **OpenGulf Ottoman Map**: https://github.com/opengulf/ottoman-map
  (GeoJSON for c. 1910 map only, limited coverage)
- **University of Chicago holdings**: Heinrich Kiepert maps of Ottoman Empire
  (1850-1890 visits) -- catalog record only, no shapefiles
- **Digital Orientalist tutorial**: https://digitalorientalist.com/2020/11/06/
  social-scientific-applications-of-historical-gis-part-1/ (methodology for
  creating Ottoman district polygons from scratch)
- **Status**: **No publicly available comprehensive vector boundary files exist
  for the Ottoman Empire.** Researchers must create their own by georeferencing
  and digitizing historical maps.
- **Specific relevance**: OTT-1800-1912 and TUR-1800-1912 currently rely on
  CShapes which starts at 1886. The 1800-1886 Ottoman territory (especially
  pre-Balkan-independence boundaries showing control of Greece, Serbia,
  Romania, Bulgaria) would need to be manually created.
- **Best available approach**: Use Centennia Research Edition (Section 5.2)
  which has Ottoman boundaries at 0.1-year resolution, or georeference
  Kiepert maps from Rumsey collection.

### 3.2 Qing Dynasty / China -- CHGIS INTEGRATED (provinces)

CHGIS v6 was downloaded and assessed (2026-03-27). Contains province-level
polygons (26 administered provinces from 1820 snapshot) integrated as subnational
entries (1820-1912). Also contains 3,830 prefecture-level polygons (too granular).
CHN sovereign entries already covered by CShapes. See Section 2.3.
Cliopatria provides Qing outer boundary data (31 time-steps, ~12.5M km2 at peak).
For the 1912-1997 gap in Chinese subnational coverage, see doc 13 Section 11.

### 3.3 Japanese Historical GIS -- SEE Section 2.11

Harvard Japan HGIS covers Tokugawa and Meiji periods.

### 3.4 Africa -- Pre-Colonial Boundaries

**Primary vector source**: Paine et al. (2024) -- see Section 2.1.

**Additional reference sources**:
- **Murdock (1959) Ethnolinguistic Map**: 835 ethnic group boundaries digitized
  by Nathan Nunn (Harvard). Available as shapefile via Nunn's website and the
  `sboysel/murdock` R package on GitHub. These are ethnic/linguistic boundaries,
  NOT political, but overlap significantly with pre-colonial states.
  - **URL**: https://github.com/sboysel/murdock
  - **License**: Academic
  - **Quality**: Standard dataset in African political economy research
- **Vincent Hiribarren Borno Maps**: https://vincenthiribarren.com/borno
  (Bornu boundary evolution specifically)

### 3.5 South/Southeast Asia -- LIMITED

- **ESOC Princeton**: Administrative boundaries for SE Asia as of 1966 (too
  late for our period). URL: https://esoc.princeton.edu/data/
- **Leiden University**: Digitized historical maps of Dutch colonies (Indonesia).
  Raster only, not vectorized.
- **Appraising Risk**: Indian census districts 1872+ (see Section 2.7) -- the
  only available vector source for 19th century South Asia.
- **No comprehensive Southeast Asian historical boundary GIS exists** for the
  pre-colonial period. French Indochina, Siam, Burma boundaries would need
  manual digitization.

### 3.6 Iran/Persia (Qajar Dynasty) -- NO VECTOR DATA

- **UNESCO Qajar Maps Collection**: ~500 hand-drawn/lithographic maps from the
  Qajar period (1789-1925) held at National Library of Iran.
  URL: https://en.unesco.org/silkroad/silk-road-themes/documentary-heritage/
- **Academic GIS study**: Published in Journal of the Iranian Association of
  Geography (2024), digitized territorial losses during Qajar dynasty using
  GIS, showing 1.8-2.1 million km2 lost. But the actual shapefiles are not
  publicly released.
- **Status**: No publicly available vector boundaries for Qajar Iran exist.
  IRN-1800-2025 uses CShapes which back-projects modern Iran boundaries.
- **Specific relevance**: Iran's boundaries were significantly different in
  1800 (included parts of Afghanistan, Caucasus, Herat) vs. modern borders.
  Qajar territorial losses to Russia (Treaty of Turkmenchay 1828), Britain
  (Herat crisis 1856), and Afghanistan make the back-projection inaccurate.

### 3.7 Latin America -- Post-Independence

- **HGIS de las Indias**: Covers 1701-1808 (see Section 2.4). Does NOT cover
  the post-independence period.
- **No comprehensive Latin American historical boundary GIS exists** for the
  1810-1886 period specifically. This is a significant gap given the War of
  the Pacific (Chile vs. Bolivia/Peru, 1879-1884), Gran Colombia dissolution
  (1830), and Argentine territorial expansion.
- **Specific relevance**: ARG, BRA, COL, ECU, CHL, PER, BOL, PRY all have
  1800-era entries using CShapes back-projection. The War of the Pacific
  boundaries (Bolivia losing its coast) are a notable inaccuracy for
  BOL-1825-1903 and CHL-1810-1899.

### 3.8 Pre-Colonial African Boundaries -- Fundamental Challenges

The digitization of pre-colonial African polity boundaries faces challenges
qualitatively different from those of European or East Asian historical GIS
work. These must be understood when using sources like Paine et al. (2024) or
Cliopatria.

- **Zones of influence vs. hard borders**: Pre-colonial African polities
  typically exercised graduated sovereignty radiating outward from a core,
  rather than maintaining fixed linear borders. Peripheral areas were zones of
  shared or contested influence, not demarcated frontiers.
- **Scale of political fragmentation**: Circa 1880, Africa contained an
  estimated ~45,000 independent polities, of which only ~46 were organized as
  centralized states (those captured by Paine et al.). The vast majority were
  acephalous societies, chieftaincies, or segmentary lineage systems that did
  not map onto the Westphalian state model.
- **Overlapping sovereignty**: Tribute systems created hierarchies of
  overlapping claims. A polity paying tribute to Sokoto, for example, might
  simultaneously owe allegiance to a local Hausa emir and conduct independent
  diplomacy. Drawing a single polygon boundary necessarily simplifies these
  layered relationships.
- **Temporal instability**: Many pre-colonial African state boundaries shifted
  rapidly with military campaigns, succession crises, and seasonal patterns of
  raiding. A polygon valid for one decade may be seriously wrong for the next.
- **Boundaries not recorded by the polities themselves**: Unlike European or
  Chinese states, pre-colonial African polities generally did not produce
  boundary maps or treaty-delimited borders. All boundary reconstructions rely
  on European travelers' accounts, oral traditions collected later, or
  inference from archaeological and linguistic evidence.
- **Robustness strategies**:
  - Paine et al. (2024) use 0.25-degree buffers (~25 km) around all digitized
    boundaries for robustness checks, demonstrating that their results hold
    regardless of exact boundary placement within this margin.
  - Cliopatria acknowledges "currently unquantified uncertainty" in all its
    historical boundary data.
- **Practical implication for WHEP**: Any polygon representing a pre-colonial
  African polity is a scholarly approximation carrying ~25-100 km uncertainty
  at the boundary. This uncertainty should be documented in polygon metadata,
  and analysis should avoid relying on precise boundary placement.
- **Murdock ethnographic map**: The Murdock (1959) map of 843 ethnic groups is
  widely available as a shapefile and is sometimes used as a proxy for
  pre-colonial political boundaries. This is methodologically incorrect.
  Paine et al. (2024) demonstrate explicitly that ethnic group territories do
  not correspond to state boundaries -- many states spanned multiple ethnic
  groups, and many ethnic groups were split across states. The Murdock map
  should NOT be used as a substitute for state boundary data.

---

## 4. Crowdsourced and Community Projects

### 4.1 Aourednik Historical Basemaps -- PRIORITY MODERATE (quick wins)

- **URL**: https://github.com/aourednik/historical-basemaps
- **Coverage**: 36 world GeoJSON files for CE dates including:
  - **world_1800.geojson** -- directly relevant
  - **world_1815.geojson** -- Congress of Vienna
  - **world_1880.geojson** -- near end of our gap
  - Also: 1900, 1914, 1920, 1930, 1938, 1945, 1960, 1994, 2000, 2010
- **Format**: GeoJSON, WGS 84 (EPSG:4326)
- **License**: **GPL-3.0** (open source)
- **Quality**: Work in progress. Includes BORDERPRECISION field with ordinal
  values 1 (approximate), 2 (moderately precise), 3 (determined by
  international law). Author warns: "historical boundaries are even more
  disputed than contemporary ones" -- verify against other sources.
- **Specific relevance**:
  - The 1800 and 1880 GeoJSON files could be directly compared against our
    current polygons to identify discrepancies
  - Global coverage means ALL our problem polities could be checked
  - Quality varies: likely good for major powers, weaker for peripheral states
  - **Quick check**: Download world_1800.geojson and world_1880.geojson,
    overlay with our CShapes back-projections, and flag major differences

### 4.2 OpenHistoricalMap -- EMERGING, NOT YET RELIABLE

- **URL**: https://www.openhistoricalmap.org/
- **API**: Overpass API at https://overpass-api.openhistoricalmap.org/api/
- **Data export**: Weekly database dumps in PBF format on Amazon S3. Overpass
  turbo can export query results as GeoJSON.
- **Example query** (country boundaries on a specific date):
  ```
  relation(35,-12,60,40)["admin_level"="2"](if:
    t["start_date"] <= "1850-01-01" &&
    (!is_tag("end_date") || t["end_date"] > "1850-01-01"));
  out geom;
  ```
- **Coverage**: Very sparse for 19th century. US states/counties are best
  covered (imported from Atlas of Historical County Boundaries). France road
  network 1820-1866 mapped. Most other areas have minimal coverage.
- **License**: ODbL (Open Database License) -- same as OpenStreetMap
- **Quality**: Crowdsourced, highly variable. "In a very early state of
  development." Has a boundary viewer showing gaps (gray areas on map).
- **Specific relevance**: Not yet useful for systematic boundary extraction.
  The Overpass API could become valuable as coverage improves. Monitor for
  future use rather than rely on currently.

### 4.3 idris-maps/world-historical-gis-data -- LOW QUALITY

- **URL**: https://github.com/idris-maps/world-historical-gis-data
- **Coverage**: World boundaries 2000 BCE to 1994 CE (from defunct Oracle
  Thinkquest.org educational site, archived via Wayback Machine)
- **Format**: Shapefiles and TopoJSON
- **License**: Educational
- **Quality**: **Poor. "+/- 40 miles spatial error."** Created by students.
  "Should be used with caution and only for small scale projects."
- **Specific relevance**: NOT suitable for academic use. Too inaccurate.

### 4.4 ioggstream/europe-historical-geojson -- LOW QUALITY

- **URL**: https://github.com/ioggstream/europe-historical-geojson
- **Coverage**: Europe, Congress of Vienna to WWI (~1815-1918). Includes
  germany-1914-boundaries.geojson and some 1915 data.
- **Format**: GeoJSON
- **License**: BSD-3-Clause
- **Quality**: Created to "teach my kids history" -- game-board level accuracy.
  Based on EU GISCO dataset adapted for historical periods. NOT suitable for
  rigorous academic work.
- **Specific relevance**: NOT suitable. Use HGIS Germany and CShapes-Europe
  instead.

### 4.5 Wikidata / Wikimedia Commons Historical Geoshapes -- EXPERIMENTAL

- **URL**: https://www.wikidata.org/wiki/Wikidata:Map_data
- **Coverage**: Some historical entities have geoshape (P3896) property linking
  to map data on Wikimedia Commons. Coverage is patchy.
- **Format**: GeoJSON stored on Wikimedia Commons
- **License**: CC-BY-SA (typical Wikimedia license)
- **Quality**: Variable. Some contributed by knowledgeable editors, some
  approximate. Properties for tracking boundary changes exist (P7903/P7904).
- **Specific relevance**: Worth checking for specific entities (Ottoman Empire,
  Qing China, etc.) but not a systematic source. The WikiProject Historical
  Place tracks these efforts: https://www.wikidata.org/wiki/Wikidata:WikiProject_Historical_Place

### 4.6 Omniatlas -- VISUAL REFERENCE ONLY

- **URL**: https://omniatlas.com/
- **Coverage**: Interactive step-by-step world history atlas. Global coverage
  across centuries with event-by-event boundary changes.
- **Format**: Web application only. No data download or API.
- **License**: Proprietary (Patreon-supported)
- **Specific relevance**: Useful as visual reference only. Cannot extract
  vector data.

### 4.7 Ostellus Atlas -- VISUAL REFERENCE ONLY

- **URL**: https://atlas.ostellus.com/
- **Coverage**: Interactive world history visualization
- **Format**: Web application only. No evidence of data download capability.
- **Specific relevance**: Visual reference only.

---

## 5. Commercial / Licensable Sources

### 5.1 Euratlas -- PRIORITY MODERATE (if budget allows)

- **URL**: https://www.euratlas.net/shop/maps_gis/
- **Coverage**: Political boundaries of Europe at each century mark (1 CE to
  2000 CE). Coverage area: 15 deg W to 50 deg E, 20 deg N to 60 deg N.
  Data available for: years 1, 100, 200, 300, 400, 500, 600, 700, 800,
  900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, **1800**, **1900**, 2000.
- **Format**: Shapefiles (platform independent). Text encoding: Latin-1 and
  UTF-8. SLD styling files included.
- **Layers per century**: Sovereign countries, Holder countries, Provinces,
  Autonomous peoples, Cities (with name and size), Dioceses, plus physical
  features (rivers, seas, mountain contours).
- **Coordinate system**: Geographic (likely WGS 84)
- **Pricing**:
  - Single century (1800 or 1900): **150 EUR** (simple license)
  - Extended license: 600 EUR per century
  - Site license: from 600 EUR
- **License**: Three tiers (simple, extended, site). Details in license PDFs
  on their site.
- **Quality**: Long-established commercial product. Used by Duke University
  Libraries and Stanford among others. Professional quality.
- **Limitations**: **Only century marks** -- no data for intermediate years
  (e.g., 1830, 1860, 1886). Only covers Europe (not global).
- **Specific relevance**:
  - The **1800 snapshot** would provide European boundaries at the start of
    our gap period (Napoleonic era)
  - The **1900 snapshot** captures post-Congress-of-Berlin Europe
  - **Does NOT help with 1815-1886 intermediate changes** (Italian unification
    1860, German unification 1871, Balkan independence, etc.)
  - **Does NOT cover Asia, Africa, Americas, Oceania**
  - At 150 EUR per century, buying 1800+1900 = 300 EUR total. Reasonable for
    two reference snapshots but limited utility given the century-only resolution.

### 5.2 Centennia Research Edition (CRE) -- PRIORITY HIGH (if budget allows)

- **URL**: http://historicalatlas.com/CRE/
- **Developer**: Clockwork Mapping
- **Coverage**: Europe and the Middle East, 1000 CE to 2003 CE. Includes
  Ottoman Empire, North Africa, Levant, Mesopotamia, Arabia.
- **Format**: **KML** (standard, compatible with all modern GIS)
- **Time resolution**: **Every 0.1 year** (i.e., boundaries at ~36-day
  intervals). This is by far the finest temporal resolution of any historical
  boundary dataset.
- **Data size**: 4.5 GB compressed, 18 GB uncompressed
- **Content**: Complete internal database of all Centennia Historical Atlas
  entities. Polygons with identifiers at all dates. Political polygons extend
  past coastlines (for overlay with separate water datasets).
- **Pricing**:
  - **CRE Single-date**: $75 for KML data for any single year (requires signed
    contract)
  - **CRE 1789-1939**: $3,125 (requires signed contract)
  - **CRE Complete** (1000-2003): $12,500 (requires signed license)
- **License**: Requires signed licensing contract. Limitations on publication,
  display, and redistribution. Samples available for analysis before licensing.
- **Quality**: The Centennia atlas is well-known and was actually used as a
  source by CShapes-Europe for the pre-1886 European extension. Contains
  9,000+ border changes.
- **Specific relevance**:
  - **The single most comprehensive source** for European and Middle Eastern
    boundaries in the 1800-1886 period
  - Would provide exact boundaries for ALL European problem polities at any
    date: pre-unification German/Italian states, Ottoman territorial
    contraction, Balkan independence, Austrian-Hungarian internal changes
  - The 1789-1939 package ($3,125) covers our entire gap period plus WWI/
    interwar
  - A single-date purchase ($75) for, say, 1860 or 1870 would be a cost-
    effective way to evaluate quality before committing to the full package
  - **Key limitation**: Europe and Middle East only. Does not cover Africa,
    Asia (beyond Middle East), Americas, or Oceania.
  - **Note**: CShapes-Europe already used Centennia as a source, so the CRE
    data may be partially redundant with what CShapes-Europe provides. But
    CRE has much finer temporal resolution and includes entities that
    CShapes-Europe does not.

### 5.3 Mapire -- Habsburg Military Survey Maps -- REFERENCE ONLY

- **URL**: https://maps.arcanum.com/ (Arcanum Maps)
- **Coverage**: Three Habsburg Military Surveys georeferenced:
  - First Military Survey (1764-1784), scale 1:28,800
  - Second Military Survey (1806-1869), scale 1:28,800
  - Third Military Survey (1869-1887), scale 1:25,000 (Hungary) /
    1:75,000 (full empire)
- **Format**: Georeferenced raster (web viewer). High-resolution copies
  purchasable.
- **License**: Free to browse. Paid for high-res downloads. Created by
  Arcanum (Hungary) in partnership with archives in Hungary, Austria, Croatia.
- **Quality**: Extraordinarily detailed topographic maps. Possibly the most
  detailed historical maps of Central Europe ever produced.
- **Specific relevance**: These are topographic maps, not political boundary
  maps, but they show administrative divisions at extreme detail. Could be
  used to trace and verify boundaries for AUH-1800-1908 and all Habsburg
  successor entities. However, the work to extract political boundaries
  would be very labor-intensive.

---

## 6. Consolidated Priority Matrix

### Tier 1: Highest Impact, Ready to Use

| Source | Region | Gap it fills | Format | Cost | Effort |
|--------|--------|-------------|--------|------|--------|
| **HGIS Germany** | German states | 38 pre-1871 states, 1820-1914 | SHP | Free | Low (direct use) |
| **CHGIS v6** | China/Qing | CHN-1800-1895 + Outer Mongolia | SHP | Free | Low-Medium |
| **Paine et al. (2024)** | Africa | 46 pre-colonial states | SHP | Free | Medium |
| **Cliopatria** | Global (incl. Africa) | 290+ polities 1800-1886; African kingdoms (Ashanti, Sokoto, Merina, Bornu, Zululand, Ethiopia, Morocco, Zanzibar, etc.) | GeoJSON | Free (CC BY 4.0) | Low-Medium |
| **Aourednik basemaps** | Global | Quick validation of 1800 & 1880 | GeoJSON | Free | Low |

### Tier 2: High Value, Moderate Effort or Cost

| Source | Region | Gap it fills | Format | Cost | Effort |
|--------|--------|-------------|--------|------|--------|
| **Centennia CRE** | Europe+ME | All European+Ottoman 1800-1886 | KML | $75-$3,125 | Low |
| **Appraising Risk** | India | British India+Princely States 1872+ | SHP | Free | Medium |
| **HistoGIS/MPIDR** | Habsburg | AUH crownlands 1860 **INTEGRATED** for AUT-1800-1918 + HUN-1800-1918; districts 1910 available | SHP | Free | **DONE** |
| **HGIS de las Indias** | Lat. America | Spanish America baselines 1800-1808 | GPKG | Free | Medium |
| **TRF-GIS / French HGIS** | France | French admin boundaries 1790-1940 | SHP | Free | Medium |
| **Euratlas 1800** | Europe | European snapshot at 1800 | SHP | 150 EUR | Low |

### Tier 3: Reference / Supplementary

| Source | Region | Use case | Format | Cost |
|--------|--------|----------|--------|------|
| **David Rumsey** | Global | Reference/verification of digitized polys | GeoTIFF | Free |
| **Shepherd's Atlas** | Global | Public domain reference maps | JPEG | Free |
| **Japan HGIS** | Japan | Tokugawa/Meiji boundaries | SHP | Free |
| **OpenHistoricalMap** | Global | Emerging; monitor for future use | GeoJSON via API | Free |
| **Murdock map** | Africa | Ethnic group boundaries as context | SHP | Free |
| **Mapire** | Habsburg | Ultra-detailed topo reference | Raster | Free browse |

### Tier 4: Not Recommended

| Source | Reason |
|--------|--------|
| **idris-maps/world-historical-gis-data** | +/- 40 mile error; student-created |
| **ioggstream/europe-historical-geojson** | Game-board accuracy; "teach my kids" |
| **Omniatlas / Ostellus** | Visual only; no data export |

---

## 7. Mapping Sources to Problem Polities

Cross-referencing against the polygon accuracy audit (doc 08):

| Problem Polity | Severity | Best Source(s) | Status |
|----------------|----------|---------------|--------|
| ETH-1800-1889 (pre-Menelik Ethiopia) | CRITICAL | Paine et al. (2024) + Cliopatria (2 time-steps, ~240,357 km2) | Available now |
| EGY-1800-1899 (Egypt without Sudan) | CRITICAL | Paine et al. + Cliopatria (Khedivate, multiple entries) + Centennia CRE | Available now |
| ZAN-1800-1890 (Zanzibar islands only) | CRITICAL | Paine et al. + Cliopatria (2 time-steps, ~28,255 km2) | Available now |
| CHN-1800-1895 (Qing + Outer Mongolia) | ~~MAJOR~~ | CHGIS v6 province polygons | **DONE**: 26 Qing provinces added as subnational entries (1820-1912). Sovereign polygon unchanged (CShapes). |
| MOR-1800-1904 (Morocco fixed borders) | MAJOR | Paine et al. + Cliopatria (5 time-steps, ~386,205 km2) | Available now |
| MAD-1800-1912 (Madagascar whole island) | MODERATE | Paine et al. + Cliopatria (Merina, 10 time-steps, ~426,715 km2) | Available now |
| Ashanti Empire (1797-1894) | MODERATE | Cliopatria (20 time-steps, ~154,508 km2) | Available now |
| Sokoto Caliphate (1805-1894) | MODERATE | Paine et al. + Cliopatria (6 time-steps, ~792,706 km2) | Available now |
| Bornu Empire (1636-1894) | MODERATE | Paine et al. + Cliopatria (8 time-steps, ~227,106 km2) | Available now |
| Zululand (1820-1894) | MODERATE | Paine et al. + Cliopatria (5 time-steps, ~25,464 km2) | Available now |
| Regency of Algiers (1792-1845) | MODERATE | Cliopatria (6 time-steps, ~163,203 km2) | Available now |
| Darfur / Wadai | MODERATE | Paine et al. + Cliopatria (Darfur: 3 time-steps; Wadai: 2 time-steps) | Available now |
| German states (38 entities pre-1871) | MODERATE | HGIS Germany (1820-1914) | Available now |
| KHI/KOK/BUK (Central Asian khanates) | MODERATE | No vector source found | Manual work needed |
| OTT-1800-1886 (Ottoman pre-contraction) | MODERATE | Cliopatria (33 records) + Centennia CRE ($75+) | Available now / Commercial |
| IND-1800-1893 (British India) | MODERATE | Appraising Risk (1872+) | In progress |
| IRN-1800-1828 (Qajar Persia) | ~~MODERATE~~ | ~~Cliopatria~~ | **DONE** (Cliopatria polygon integrated) |
| Lat. American states (1800-1886) | MODERATE | HGIS de las Indias (to 1808) | Partial |
| FRA-1800-1919 (France Alsace-Lorraine) | MINOR | TRF-GIS + French HGIS | Available now |
| AUH-1800-1867 (Austrian Empire) | ~~MINOR~~ | ~~Cliopatria/HistoGIS~~ | **DONE** (Cliopatria polygon integrated) |
| Dahomey, Buganda | MINOR | Paine et al. only (NOT in Cliopatria by name) | Partial |

---

## 8. Recommended Action Plan

### Phase 1: Quick wins (free, immediate)

1. ~~Download **Paine et al. (2024)** replication data from Harvard Dataverse
   and extract pre-colonial African state polygons.~~ **DONE** (2026-03-27).
   43 new polity entries + 3 updated. Script: R/11_integrate_precolonial_polygons.R.
2. ~~Download **Cliopatria** from Seshat GitHub and fill polities with no
   polygon from any other source.~~ **DONE** (2026-03-27). 4 polities filled
   (IRN-1800-1828, AUH-1800-1867, SWE-1800-1809, SWE-1809-1814).
   Script: R/12_integrate_cliopatria_polygons.R.
3. ~~Download **CHGIS v6** and integrate Qing China provinces.~~
   **DONE** (2026-03-27). 26 Qing province polygons (1820 snapshot) added as
   subnational entries (1820-1912). Script: R/13_integrate_chgis_provinces.R.
   Sovereign CHN polygon unchanged (CShapes already covers it).
4. Download **HGIS Germany** shapefiles from NYU Spatial Data Repository
   (https://geo.nyu.edu/, search "ghgis") and replace GADM-proxied German states.
   Available as Shapefile and GeoJSON, no authentication required.
   Key dataset: `harvard-ghgis1820core` (1820 state boundaries).
5. Download **Aourednik world_1800.geojson and world_1880.geojson** and overlay
   with current WHEP polygons to identify the biggest discrepancies globally.

### Phase 2: Medium effort (free, requires processing)

5. Download **HGIS de las Indias** and extract 1800-1808 Spanish American
   territorial baselines.
6. Download **TRF-GIS / French HGIS** and create proper pre/post-1871 French
   boundaries.
7. ~~Download **HistoGIS** Austrian Empire Crownlands 1848 and match to
   AUH-1800-1908.~~ **DONE (2026-04-17)**: Downloaded 1860 crownlands shapefile,
   dissolved into Cisleithania (AUT-1800-1918) and Transleithania (HUN-1800-1918).
   Script: `R-legacy/25_integrate_histogis_habsburg.py`. Output:
   `data/geodata/histogis/habsburg_cisleithania_transleithania.gpkg`.
8. Contact **Appraising Risk** project about availability of 1872/1881 Indian
   census district shapefiles.
9. Download **Japan HGIS** Tokugawa data for JPN-1800 baseline.

### Phase 3: Commercial sources (if budget available)

10. Purchase **Centennia CRE single-date** for 1850 ($75) to evaluate quality
    and coverage for European/Ottoman boundaries.
11. If CRE quality is good, consider the 1789-1939 package ($3,125) for
    comprehensive European coverage.
12. Purchase **Euratlas 1800** (150 EUR) as an additional reference snapshot.

### Phase 4: Manual digitization (highest effort)

13. For Central Asian khanates (KHI, KOK, BUK): georeference Rumsey Collection
    19th century maps and manually digitize boundaries.
14. For Qajar Iran: georeference UNESCO Qajar maps collection or published
    academic GIS results.
15. For Ottoman Empire (if CRE not purchased): georeference Kiepert maps from
    Rumsey Collection.
16. For Southeast Asia (Siam, Burma, Vietnam pre-French): georeference
    Shepherd's Atlas or Rumsey maps.

---

## 9. Sources Consulted

### Digitized Atlas Collections
- David Rumsey Map Collection: https://www.davidrumsey.com/
- Shepherd's Historical Atlas (UT Austin): https://maps.lib.utexas.edu/maps/historical/history_shepherd_1923.html
- Shepherd's Historical Atlas (Internet Archive): https://archive.org/details/HistoricalAtlasWilliamR.Shepherd
- Putzger Historischer Weltatlas (Internet Archive): https://archive.org/details/putzgerhistorisc0000unse

### Academic Vector Datasets
- Paine et al. (2024) APSR Dataverse: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/9QJVJ1
- HGIS Germany (main page): http://www.digihist.de/html/hgisg/index.htm
- HGIS Germany at NYU (recommended download): https://geo.nyu.edu/catalog/harvard-ghgis1820core
- HGIS Germany at Stanford: https://earthworks.stanford.edu/?q=hgis+germany
- HGIS Germany at Harvard: https://hgl.harvard.edu/catalog/harvard-ghgis1820core
- CHGIS: https://chgis.fas.harvard.edu/
- CHGIS v6 Dataverse: https://dataverse.harvard.edu/dataverse/chgis_v6
- HGIS de las Indias: https://dataverse.harvard.edu/dataverse/hgis-indias
- TRF-GIS France: https://dataverse.harvard.edu/dataverse/TRF-GIS
- French Historical GIS: https://dataverse.harvard.edu/dataverse/french-historical-gis
- HistoGIS Austria: https://histogis.acdh.oeaw.ac.at/
- CensusMosaic/MPIDR: https://censusmosaic.demog.berkeley.edu/data/historical-gis-files
- GB Historical GIS: https://www.visionofbritain.org.uk/data/
- Japan HGIS: https://dataverse.harvard.edu/dataverse/japan_hgis
- Historical Atlas of the Low Countries: https://datasets.iisg.amsterdam/dataset.xhtml?persistentId=hdl:10622/PGFYTM
- Appraising Risk India: https://www.appraisingrisk.com/2020/10/23/digitization-of-indian-census-districts-1872-to-present/
- Cliopatria (Seshat): https://github.com/Seshat-Global-History-Databank/cliopatria
- Cliopatria Zenodo: https://zenodo.org/records/14714684
- Murdock ethnic map R package: https://github.com/sboysel/murdock

### Community/Open Source
- Aourednik historical-basemaps: https://github.com/aourednik/historical-basemaps
- OpenHistoricalMap: https://www.openhistoricalmap.org/
- OHM Overpass API: https://overpass-api.openhistoricalmap.org/api/
- OSHistory histgeodata: https://github.com/OSHistory/histgeodata
- idris-maps world-historical-gis-data: https://github.com/idris-maps/world-historical-gis-data
- ioggstream europe-historical-geojson: https://github.com/ioggstream/europe-historical-geojson
- awesome-historical-maps: https://github.com/stark1tty/awesome-historical-maps

### Commercial
- Euratlas: https://www.euratlas.net/shop/maps_gis/
- Centennia Research Edition: http://historicalatlas.com/CRE/
- Clockwork Mapping: https://www.clockwk.com/
- Mapire/Arcanum: https://maps.arcanum.com/

### Subnational Historical Sources (see also doc 13)
- USAboundaries R package (USA 1783-2000): https://github.com/ropensci/USAboundaries
- Newberry Library AHCB (USA 1783-2000): https://publications.newberry.org/ahcb/
- NHGIS (USA 1790-present): https://www.nhgis.org/gis-files
- geobr R package (Brazil 1872-2020): https://github.com/ipeaGIT/geobr
- IBGE FTP (Brazil 1872-2010): https://geoftp.ibge.gov.br/organizacao_do_territorio/
- Transcultural Empire GIS (Russia 1897+1926): https://heidata.uni-heidelberg.de/dataset.xhtml?persistentId=doi:10.11588/data/10064
- ORNL DAAC FSU (Russia ~1998): https://doi.org/10.3334/ORNLDAAC/699
- mapSpain R package (Spain provinces): https://ropenspain.github.io/mapSpain/
- CNIG/IGN Spain: https://centrodedescargas.cnig.es/
- FAO GAUL 2015 (global 1990-2014): https://data.apps.fao.org/catalog/dataset/global-administrative-unit-layers-gaul-2015

### Regional Projects
- Digital Ottoman Studies: https://www.digitalottomanstudies.com/gis
- OpenGulf Ottoman Map: https://github.com/opengulf/ottoman-map
- UNESCO Qajar Maps: https://en.unesco.org/silkroad/silk-road-themes/documentary-heritage/
- Wikidata Map Data: https://www.wikidata.org/wiki/Wikidata:Map_data

### Reference Guides
- Geography Realm: https://www.geographyrealm.com/find-gis-data-historical-country-boundaries/
- Duke GIS Data Sources: https://guides.library.duke.edu/gisdata/gisdata_historical
- GMU Humanities GIS: https://infoguides.gmu.edu/geohumanities/data
- alternatehistory.com GIS Resources Thread: https://www.alternatehistory.com/forum/threads/historical-gis-resources-thread.516971/

### CShapes (already in use)
- CShapes 2.0: https://icr.ethz.ch/data/cshapes/
- CShapes paper: Schvitz et al. (2022), Journal of Conflict Resolution, 66(1), 144-161.
