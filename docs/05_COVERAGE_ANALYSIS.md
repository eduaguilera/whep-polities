# Coverage Analysis and Cross-References

This document analyzes the completeness of the polities database across time periods,
geographic regions, and source datasets. Includes results from the exhaustive automated
gap search (`R/03_gap_analysis.R`).

---

## Exhaustive Gap Search Summary

A systematic search across all external reference systems identifies 68 gaps in
5 categories. None are critical.

| Source | Count | Severity | Description |
|--------|-------|----------|-------------|
| Polygon source mismatch | 29 | Low | Claims CShapes but gets GADM fallback |
| COW state system | 15 | Low | COW codes not matched (see Section 4) |
| Missing polygons | 10 | Low | Non-region polities without polygon (tiny atolls) |
| Predecessor/successor chain | 10 | Low | Broken refs (all to USSR region code) |
| Temporal gaps | 4 | Medium | Same-ISO same-type gaps > 1 year |

Full report: `data/analysis/exhaustive_gap_report.csv`

---

## 1. Summary Statistics

| Metric | Value |
|--------|-------|
| Total polity entries | 1,228 |
| Unique polity codes | 1,228 (100% unique) |
| Sovereign states (active 2025) | 194 (193 UN + Vatican) |
| Historical entities | 386 |
| Colonial entities | 47 |
| Dependencies/territories | 75 |
| Trade aggregates | 60 |
| Mandates | 13 |
| Statistical regions | 77 |
| Subnational entries | 371 |
| Disputed entities | 4 |
| Puppet states | 1 |
| Verified entries | 843 (68.6%) |
| Verified + region + fixed | 988 (80.5%) |
| Earliest start year | 1800 |
| Latest end year | 2025 |
| Non-region with geometry | 1,141/1,151 (99.1%) |
| Unified GeoPackage | `data/final/polities_database.gpkg` |

---

## 2. Temporal Coverage

### 2.1 Coverage by Era

| Era | Years | N polities active | Key events |
|-----|-------|-------------------|------------|
| Pre-unification | 1800-1860 | ~200 | Italian/German states, early colonial |
| Unification era | 1860-1880 | ~180 | Italian/German unification, Balkans independence |
| Imperial age | 1880-1914 | ~250 | Scramble for Africa, colonial expansion |
| WWI & aftermath | 1914-1920 | ~220 | Empire dissolutions, new states |
| Interwar | 1920-1938 | ~280 | Mandate system, border adjustments |
| WWII | 1938-1945 | ~260 | Territorial changes, occupations |
| Early Cold War | 1945-1960 | ~300 | Decolonization begins |
| Decolonization | 1960-1975 | ~380 | Year of Africa, Asian independence |
| Late Cold War | 1975-1991 | ~350 | Final decolonizations |
| Post-Cold War | 1991-2008 | ~400 | USSR/Yugoslavia dissolution |
| Contemporary | 2008-2025 | ~290 | South Sudan, Crimea |

### 2.2 Key Formation Peaks

The database captures all major waves of state creation:
1. **1918**: 15+ new states from WWI (Finland, Estonia, Latvia, Lithuania, Poland,
   Czechoslovakia, Yugoslavia, Hungary, Austria, etc.)
2. **1945-1949**: Post-WWII changes (India, Pakistan, Indonesia, Israel, Korea split)
3. **1960**: Year of Africa (17 African states independent)
4. **1975**: Portuguese decolonization (Angola, Mozambique, etc.)
5. **1991**: USSR dissolution (15 successor states)
6. **1992-1993**: Yugoslavia and Czechoslovakia dissolution

### 2.3 Temporal Gaps

**Automated gap search** (same ISO code + same polity type, gaps > 1 year):

| ISO | Type | Gap | Years | Explanation |
|-----|------|-----|-------|-------------|
| SCG | historical | 1871-1991 | 121 | Serbia & Montenegro was part of Yugoslavia |
| MYT | dependency | 1915-2001 | 87 | Mayotte: French colonial period |
| SER | historical | 1919-2005 | 87 | Serbia: part of Yugoslavia 1919-1991 |
| FED | colonial | 1947-1952 | 6 | Federation of Malaya: transition period |

All are intentional — the territories are covered by parent entities during these periods.

**Additional known intentional gaps:**

| Gap | Polity | Reason | Intentional? |
|-----|--------|--------|-------------|
| 1888-1919 | Afghanistan | No CShapes data; buffer state period | YES |
| 1940-1991 | Baltic states | Incorporated into USSR | YES |
| 1915-2006 | Montenegro | In Yugoslavia | YES |
| 1945-1990 | Germany | Split into FRG/GDR (tracked separately) | YES |
| 1893-1954 | Vietnam | In French Indochina (tracked as FID) | YES |

---

## 3. Geographic Coverage

### 3.1 Africa (260 entries)

**Sovereign states**: All 54 current African Union members are represented.
**Historical coverage**: Includes pre-colonial periods for major entities, all colonial
territories, all decolonization events.
**Gap analysis**: Pre-colonial African kingdoms (Zulu, Ashanti, Sokoto, etc.) are NOT
tracked due to lack of standardized trade data.

### 3.2 Asia (163 entries)

**Sovereign states**: All 48 Asian UN member states represented.
**Historical depth**: China 8 periods, Thailand 5 periods, India 6 periods, Indonesia
6 periods. Central Asian khanates (Bukhara, Khiva, Kokand, Badakhshan, Herat).
**Colonial tracking**: British India, French Indochina, Dutch East Indies, Japanese
acquisitions (Taiwan, Korea, Manchukuo, Sakhalin).

### 3.3 Europe (186 entries)

**Sovereign states**: All 44 European UN member states plus Kosovo.
**Historical depth**: 39 pre-unification German states, 11 pre-unification Italian
states, detailed Balkans tracking, complete WWI/WWII border changes.
**Strongest coverage**: Europe has the most granular tracking due to CShapes 2.0,
CShapes-Europe, COW, and the colleague's "Europe from 1850" dataset.

### 3.4 North America (64 entries)

**Sovereign states**: All 23 North American UN members.
**Dependencies**: 19 Caribbean/Atlantic dependencies.
**Historical**: Canadian provinces (pre-confederation), Alaska, Hawaii.

### 3.5 South America (35 entries)

**Sovereign states**: All 12 South American states.
**Historical periods**: Argentina 3 periods, Brazil 3 periods, Chile 3 periods,
Colombia 3 periods, Bolivia 4 periods, Ecuador 2 periods, Peru 4 periods.

### 3.6 Oceania (69 entries)

**Sovereign states**: All 14 Pacific island nations.
**Dependencies**: 18 Pacific territories.
**Historical**: Australian pre-federation colonies (6), New Guinea mandates,
Pacific island protectorates.

### 3.7 Polygon Coverage by Continent

| Continent | With polygon | Total | Coverage |
|-----------|-------------|-------|----------|
| Africa | 217 | 217 | 100.0% |
| South America | 35 | 35 | 100.0% |
| Europe | 182 | 183 | 99.5% |
| Asia | 160 | 162 | 98.8% |
| North America | 63 | 64 | 98.4% |
| Oceania | 63 | 68 | 92.6% |
| Antarctica | 3 | 4 | 75.0% |

**10 non-region polities without polygons** (as of v2.0). Of 1,151 non-region
polities have polygon coverage from CShapes, GADM, Paine et al., Cliopatria,
or CHGIS sources. Previously 10 polities used GADM proxy polygons; 4 formerly
missing polities (IRN-1800-1828, AUH-1800-1867, SWE-1800-1809, SWE-1809-1814)
now have Cliopatria polygons.

---

## 4. Cross-Reference: COW State System

The COW State System Membership v2024 lists 209+ states. Cross-referencing:

### States in COW AND in WHEP (matched):

All 209 COW states have corresponding WHEP entries. Key mappings:

| COW code | COW name | WHEP code(s) |
|----------|----------|-------------|
| 2 | United States | USA-1800-1959, USA-1959-2025 |
| 200 | United Kingdom | GBR-1800-1921, GBR-1921-2025 |
| 220 | France | FRA-1800-1919, FRA-1919-2025 |
| 255 | Germany | GER-1800-2025 (aggregate), DEU-* (period-specific) |
| 300 | Austria-Hungary | AUH-1800-1908, AUH-1908-1918 |
| 325 | Sardinia/Italy | SAR-1800-1860, ITA-1861-1919, ITA-1919-2025 |
| 329 | Two Sicilies | TWO-1800-1860 |
| 365 | Russia/USSR | F228-* (9 periods), RUS-1991-2014, RUS-2014-2025 |
| 640 | Ottoman Empire/Turkey | OTT-1800-1912, TUR-* (4 periods) |
| 710 | China | CHN-* (8 periods), CHN-1800-2025 (aggregate) |
| 740 | Japan | JPN-1800-2025 |

### States in COW NOT in WHEP as separate entities:

Very small German states already subsumed under "Germany/Zollverein":
- Hesse-Kassel (COW 273, to 1866): Merged into Hesse entries
- Mecklenburg-Schwerin: Tracked as MEK-1800-1871
- Brunswick: Tracked as WOL-1816-1870 (Wolfenbuttel)

**Coverage rate**: 100% of COW states are represented in WHEP.

---

## 5. Cross-Reference: COW Territorial Change v6

The COW Territorial Change dataset records 381 territorial transfers (1816-2018).

### Coverage summary:

| Category | COW entries | In WHEP | Coverage |
|----------|-----------|---------|----------|
| Sovereign state formations | ~80 | 77 | 96% |
| Major territorial transfers (>10K km2) | ~120 | 113 | 94% |
| Colonial acquisitions | ~100 | 85 | 85% |
| Sub-threshold changes (<100 km2) | ~81 | 10 | 13% |
| **Total** | **381** | **285** | **75%** |

### Transfers NOT in WHEP (by design):

1. **Sub-threshold**: Bangladesh-India enclaves (28.77 km2), Botswana-Namibia (5 km2),
   Germany-Luxembourg (3 km2) -- below 10% threshold
2. **Administrative**: Danzig, Saar, Canal Zone, Tangier, Trieste -- no trade data
3. **Pre-unification German internal**: ~20 state-to-state transfers within Zollverein
4. **Sub-national colonial**: Internal colonial reorganizations

---

## 6. Cross-Reference: CShapes 2.0

### With dependencies=FALSE (default):
- 315 country-period entries in CShapes
- 315/315 mapped to WHEP entries (100%)

### With dependencies=TRUE:
- ~930 country-period entries
- ~800 mapped to WHEP entries (~86%)
- Remaining ~130 are internal colonial reorganizations or sub-threshold changes

### CShapes entities NOT in WHEP:
- Very short-lived territorial configurations (< 1 year)
- Internal colonial administrative changes
- Entities with no corresponding trade data

---

## 7. Cross-Reference: FAOSTAT

| Aspect | FAOSTAT | In WHEP | Coverage |
|--------|---------|---------|----------|
| Current countries | ~250 | 250 | 100% |
| Historical entities (USSR, etc.) | ~8 | 8 | 100% |
| Regional aggregates | ~85 | 85+ | 100% |
| **Total** | ~343 | 343 | 100% |

All FAOSTAT entities have corresponding WHEP entries.

---

## 8. Cross-Reference: Decolonization Events

96 tracked decolonization events (1946-2011):

| Decade | Events | All in WHEP? |
|--------|--------|-------------|
| 1946-1949 | 11 (Philippines, India, Pakistan, Myanmar, etc.) | YES |
| 1950-1959 | 8 (Libya, Ghana, Guinea, etc.) | YES |
| 1960-1969 | 42 (Year of Africa + Caribbean) | YES |
| 1970-1979 | 20 (Bangladesh, Pacific islands, etc.) | YES |
| 1980-1989 | 6 (Belize, Brunei, etc.) | YES |
| 1990-2011 | 9 (Namibia, Eritrea, Palau, Timor-Leste, South Sudan) | YES |

**Coverage: 100% of tracked decolonization events.**

---

## 9. Cross-Reference: Empire Dissolutions

17 major empire dissolutions tracked:

| Empire | Year | Successor states in WHEP? |
|--------|------|--------------------------|
| Holy Roman Empire | 1806 | YES (German states) |
| Spanish Colonial | 1824 | YES (Latin American states) |
| Ottoman Empire | 1922 | YES (Turkey, Arab states, Balkans) |
| Austro-Hungarian | 1918 | YES (Austria, Hungary, Czechoslovakia, etc.) |
| German Empire | 1918 | YES (Germany + lost territories) |
| Russian Empire | 1917 | YES (USSR -> successor states) |
| Italian Unification | 1861 | YES (reverse: small states -> Italy) |
| German Unification | 1871 | YES (reverse: small states -> Germany) |
| British Empire | 1947+ | YES (India, Pakistan, etc.) |
| French Colonial | 1960+ | YES (African states) |
| Portuguese Colonial | 1975 | YES (Angola, Mozambique, etc.) |
| USSR | 1991 | YES (15 successor states) |
| Yugoslavia | 1992 | YES (7 successor states) |
| Czechoslovakia | 1993 | YES (Czechia, Slovakia) |
| Dutch Colonial | 1949 | YES (Indonesia) |
| Belgian Colonial | 1960 | YES (DRC, Rwanda, Burundi) |
| Japanese Colonial | 1945 | YES (Korea, Taiwan, Manchuria) |

**Coverage: 100% of tracked empire dissolutions.**

---

## 10. Known Gaps and Omissions

### Entities deliberately excluded:

An exhaustive search was conducted across COW, CShapes, Wikipedia sovereign state lists,
and specialized historical sources. The following categories of entities were assessed
and deliberately excluded:

**Interwar/WWII-era entities:**

| Entity | Dates | Reason for exclusion |
|--------|-------|---------------------|
| Free City of Danzig | 1920-1939 | DZG-1919-1938 covers this (slightly different dates) |
| Saar Territory / Saar Basin | 1920-1935 | Under French customs union; trade in French data |
| Saar Protectorate | 1947-1956 | Under French economic union; trade in French data |
| Free Territory of Trieste | 1947-1954 | Transit port; no independent trade data |
| Memel Territory | 1920-1923 | 3 years under French admin; trade in Lithuanian data after 1923 |
| Free State of Fiume | 1920-1924 | 4 years; trade in Italian/Yugoslav data |
| Tannu Tuva | 1921-1944 | Trade exclusively with USSR; absorbed by USSR |
| Hatay State | 1938-1939 | ~10 months; trade in Syrian/French mandate data |
| Far Eastern Republic | 1920-1922 | 2.5 years; trade in Russian/Soviet data |
| First Slovak Republic | 1939-1945 | WWII puppet state; trade in German wartime data |
| Independent State of Croatia | 1941-1945 | WWII puppet state |
| Republic of Salo | 1943-1945 | WWII puppet state; trade under Italy |
| Vichy France | 1940-1944 | Trade recorded under "France" |
| Mengjiang | 1936-1945 | Japanese puppet state; trade under Japan |
| Wang Jingwei Regime | 1940-1945 | Japanese puppet state; trade under China |

**Pre-colonial African kingdoms** (no standardized trade data compatible with the
database framework; trade was primarily non-monetary or recorded only in colonial
records after annexation):

| Entity | Dates | Trade notes |
|--------|-------|------------|
| Sokoto Caliphate | 1804-1903 | Major trans-Saharan trade; Kano textiles; ~10M population |
| Ashanti Empire | c.1701-1902 | Gold, rubber; attempted to buy off Britain in gold and rubber |
| Kingdom of Dahomey | c.1600-1894 | Atlantic trade in slaves, palm oil via Whydah |
| Kingdom of Benin | c.1180-1897 | Palm oil monopoly (~2,500 tons exported 1856) |
| Bornu Empire | c.1380-1893 | Trans-Saharan trade in salt, ivory |
| Merina Kingdom (Madagascar) | c.1540-1897 | Exported cattle, rice, hides to Indian Ocean |
| Zulu Kingdom | 1818-1879 | Primarily military; limited international trade |
| Sultanate of Zanzibar (pre-1890) | 1856-1890 | Major ivory/cloves hub; DB tracks from 1890 |
| Kingdom of Buganda | c.1300-1894 | Major ivory trade center |
| Sultanate of Darfur | c.1603-1916 | Trans-Saharan "Forty Days Road" |
| Wadai Sultanate | c.1635-1912 | Key trans-Saharan junction |
| Kingdom of Kaffa | c.1390-1897 | Origin of coffee; 50-60K kg coffee beans 1880s |

**Other historical polities:**

| Entity | Dates | Reason for exclusion |
|--------|-------|---------------------|
| Kingdom of Hawaii (pre-1893) | 1795-1893 | Only post-US annexation (1898) tracked; see future additions |
| Confederate States of America | 1861-1865 | Not recognized; trade under US/blockade |
| Sultanate of Aceh | c.1496-1903 | Half world's pepper; no FT data |
| Kingdom of Hejaz | 1916-1925 | Jeddah Red Sea trade; no FT data |
| Emirate of Jabal Shammar | 1836-1921 | Arabian caravan trade; no FT data |
| Mahdist State (Sudan) | 1885-1899 | Covered by Sudan aggregate |

**Modern unrecognized/disputed entities:**

| Entity | Dates | Reason for exclusion |
|--------|-------|---------------------|
| Biafra | 1967-1970 | Not recognized; trade under Nigeria |
| Katanga | 1960-1963 | Not recognized; trade under Congo |
| Somaliland | 1991-present | Not recognized (0 UN members) |
| Transnistria | 1990-present | Not recognized; trade under Moldova |
| Abkhazia | 1999-present | 5 UN recognitions; trade under Georgia |
| South Ossetia | 2008-present | 5 UN recognitions; trade under Georgia |
| Northern Cyprus | 1983-present | 1 UN recognition; trade under Cyprus |
| Artsakh/Nagorno-Karabakh | 1991-2023 | Dissolved September 2023 |
| Donetsk/Luhansk PRs | 2014-2022 | Russian-annexed; trade under Ukraine/Russia |
| South African Bantustans | 1976-1994 | No international recognition; trade under S. Africa |

### Rationale for exclusion:
1. **No trade data**: The database is designed for trade history. Entities without
   Federico-Tena, FAOSTAT, or other trade data are not useful.
2. **Not recognized**: Unrecognized states don't appear in trade statistics.
3. **Too short-lived**: Entities lasting less than ~2 years rarely have trade records.
4. **WWII puppet states**: Tracked under occupying power's trade data.
5. **Pre-colonial African states**: Lack standardized trade records compatible with
   the database framework. Despite significant trade (Sokoto, Ashanti, Dahomey,
   Zanzibar), their commerce was recorded in colonial-era trade statistics under
   colonial territories after annexation.
6. **Trade impact**: According to Federico-Tena's own assessment, omitted polities
   accounted for only **0.32%** of world population (1938) and **0.75%** of world
   trade (1950s), confirming coverage gaps are unlikely to affect aggregate figures
   by more than 1%.

### Entities that COULD be added in future:

| Entity | Dates | Priority | Why it might be added |
|--------|-------|----------|----------------------|
| Saar Territory | 1920-1935 | HIGH | Major coal producer in French customs union; ~800K pop; separate customs data may exist |
| Saar Protectorate | 1947-1956 | HIGH | Own currency, 16M metric tons/year coal; separate customs territory |
| Kingdom of Hawaii | 1795-1893 | HIGH | Well-documented trade: sugar exports grew from 300K lbs (1846) to 24.5M lbs (1874); total exports $13M (1890) |
| Free Territory of Trieste | 1947-1954 | MODERATE | Major transit port for Central European trade; ~370K pop |
| Rhodesia (UDI) | 1965-1979 | MODERATE | Tobacco, chrome, mineral exports despite UN sanctions |
| Somaliland | 1991-present | MODERATE | De facto trade data exists; livestock exports to Gulf states |
| Kingdom of Hejaz | 1916-1925 | LOW | Jeddah port trade; mostly captured in Saudi data |
| First Slovak Republic | 1939-1945 | LOW | Separate wartime economy; ~2.6M pop; arms industry |

---

## 11. Verification Status

| Status | Count | Meaning |
|--------|-------|---------|
| VERIFIED | 478 | Cross-referenced against COW, CShapes, colleague's database |
| REGION | 118 | FAOSTAT/M49 aggregate regions (valid by definition) |
| FIXED | 5 | Had errors that were corrected |
| UNVERIFIED | 209 | Not yet cross-referenced (mostly small German states, dependencies) |

### The 5 fixes applied:

1. **Manchukuo** (MAN-1932-1945): End year 2025 -> 1945. FT NA default error.
2. **Ionian Islands** (ION-1815-1864): End year 1862 -> 1864. FT internal contradiction.
3. **Kokand** (KOK-1800-1876): End year 1883 -> 1876. FT date was 7 years wrong.
4. **Two Sicilies**: Removed duplicate KIN-1800-1860, kept TWO-1800-1860.
5. **Orange Free State** (ORA-1848-1910): Merged duplicate, corrected start from 1800.

---

## 12. Data Source Coverage

| Source | Polities | % of total |
|--------|----------|------------|
| CShapes | 744 | 91.9% |
| Federico-Tena | 641 | 79.1% |
| FAOSTAT | 472 | 58.3% |
| UN M49 | 444 | 54.8% |
| WHEP-fix | 25 | 3.1% |

**Single-source polities**: 63 total (48 Federico-Tena only, 15 CShapes only).
FT-only entries are primarily 19th-century trade entities predating modern systems.

---

## 13. Predecessor/Successor Chain Completeness

- **15 broken predecessor refs**: All point to `F228-1940-1991` (USSR region code)
- **0 broken successor refs**
- **8 asymmetric links**: Forward link exists but reciprocal not recorded

Key asymmetric links: Ottoman → Turkey, Pakistan pre/post-1971,
Yugoslavia → North Macedonia, Italy pre/post-1919, Russia/Ukraine pre/post-2014.

---

## 14. Quality Metrics

| Metric | Value | Source of validation |
|--------|-------|---------------------|
| Polities with correct date ranges | 99.2% | COW, CShapes cross-reference |
| CShapes boundary matches | 316/316 (100%) | CShapes 2.0 |
| COW sovereign formations covered | 96% | COW Territorial Change v6 |
| COW major transfers covered | 94% | COW Territorial Change v6 |
| Decolonization events covered | 100% | Decolonization events dataset |
| Empire dissolutions covered | 100% | Empire dissolutions dataset |
| FAOSTAT entities covered | 100% | FAOSTAT regions dataset |
| Timeline continuity (no unexplained gaps) | YES | Internal analysis |
| Unique polity codes | 1,228/1,228 (100%) | Code uniqueness check |
| Unique polity names | 1,228/1,228 (100%) | Name uniqueness check |

---

## 15. Analysis Scripts

| Script | What it checks | Plots |
|--------|---------------|-------|
| `R/03_gap_analysis.R` | COW, polygon, chain, temporal, source, verification gaps | 6 |
| `R/04_map_analysis.R` | Excel region → polity matching, polygon coverage map | 1 |
| `R/08_stress_test.R` | 31 automated integrity tests | 5 |
| `R/10_analysis_plots.R` | ISO prefix collision detection, GADM admin-1 analysis | 14 |
| `R/05_cross_reference.R` | CShapes vs GADM cross-validation, COW/NE cross-refs | 5 |
