# Subnational Polygons for Major Countries

---

## Overview

This document assesses GADM admin-1 subdivisions for 19 major countries as potential
WHEP polity entries. Each country is evaluated for:
- Number of admin-1 units available in GADM 3.6
- Historical boundary stability (can modern GADM boundaries represent historical territories?)
- Quality tier for using GADM as a proxy for historical subdivisions
- Recommended polity entries to add

**Key finding**: 552 admin-1 units are available across 19 countries. Of these,
261 have high-confidence stable boundaries (rating 4-5/5), making them strong
candidates for inclusion as WHEP polities.

---

## Boundary Stability Rating System

| Rating | Label | Criteria | Time depth |
|--------|-------|----------|------------|
| 5 | Very stable | Boundaries unchanged for 100+ years | Pre-1920 |
| 4 | Stable | Last change 30+ years ago | Pre-1995 |
| 3 | Moderate | Some recent changes, but majority stable | Mixed |
| 2 | Unstable | Frequent reorganizations | Post-2000 |
| 1 | Very unstable | Boundaries changing continuously | Ongoing |

---

## Country Assessments

### United States (USA) — Rating: 5/5

**GADM admin-1**: 51 units (50 states + District of Columbia)
**Total area**: 9,472,981 km²
**Admin-1 types**: State (50), Federal District (1)

**Boundary stability**: Excellent. US state boundaries are among the most stable
administrative boundaries in the world. The last continental state boundary change
was Arizona/New Mexico admission in 1912. Alaska (1959) and Hawaii (1959) were
the last states admitted. Internal boundaries have not changed since admission
for any state.

**Key dates**:
- 13 original states: 1788-1790
- Louisiana Purchase states: 1812-1845
- Western states: 1846-1912
- Alaska/Hawaii: 1959

**Recommendation**: Add all 50 states + DC as polities. Each state's start_year
should be its year of admission to the Union (or 1800 for original 13 states,
since our database starts at 1800). End_year = 2025. Polygon quality: **Tier 2**
(good modern proxy; boundaries stable since state admission).

**Potential entries**: 51

**Limitations**:
- Pre-statehood territorial boundaries differ (e.g., Dakota Territory → North/South Dakota)
- Some states had minor border adjustments early in their history
- GADM boundaries are modern — won't capture territorial phase boundaries

---

### Japan (JPN) — Rating: 5/5

**GADM admin-1**: 47 units (43 prefectures + 2 urban prefectures + 1 circuit + 1 metropolis)
**Total area**: 372,468 km²

**Boundary stability**: Excellent. Japan's prefectural system was established in
1871 (Meiji era) and the current 47 prefectures have been stable since 1888.
Okinawa was under US administration 1945-1972 but retained its prefecture identity.

**Key dates**:
- 1871: Abolition of han (domains), creation of prefecture system
- 1888: Consolidation to current 47 prefectures
- 1945-1972: Okinawa under US administration

**Recommendation**: Add all 47 prefectures. Start_year = 1888 (or 1871 for early
adopters). Polygon quality: **Tier 2** (boundaries stable for 135+ years).

**Potential entries**: 47

---

### Australia (AUS) — Rating: 5/5

**GADM admin-1**: 11 units (6 states + 5 territories)
**Total area**: 7,688,040 km²

**Boundary stability**: Excellent. The 6 state boundaries have been stable since
before Federation (1901). ACT created 1911. NT separated from South Australia 1911.

**Already in database**: 6 pre-Federation colonies (NSW, QLD, SA, WA, Victoria,
Tasmania) are already polities with end_year 1900. Need post-Federation entries.

**Recommendation**: Add modern state entries (1901-2025) and territory entries
(ACT from 1911, NT from 1911). Polygon quality: **Tier 2**.

**Potential new entries**: ~8 (post-Federation states + territories)

---

### United Kingdom (GBR) — Rating: 5/5

**GADM admin-1**: 4 units (England, Scotland, Wales, Northern Ireland)
**Total area**: 245,486 km²
**Admin-1 types**: Kingdom (2), Province (1), Principality (1)

**Boundary stability**: Excellent. England/Scotland boundary stable since Treaty
of York (1237). Wales boundary stable since Laws in Wales Acts (1535-1542).
Northern Ireland created 1921.

**Already in database**: UK countries are already tracked as subnational regions
in the Excel data matching (see doc 07_SUBNATIONAL_POLYGONS.md).

**Recommendation**: Already covered. No new entries needed.

---

### Canada (CAN) — Rating: 4/5

**GADM admin-1**: 13 units (10 provinces + 3 territories)
**Total area**: 9,955,230 km²

**Boundary stability**: Good. Most provinces stable since Confederation (1867)
or shortly after. Last change: Nunavut created from NWT in 1999.

**Key dates**:
- 1867: Ontario, Quebec, Nova Scotia, New Brunswick (Confederation)
- 1870: Manitoba, NWT (tiny initial Manitoba expanded later)
- 1871: British Columbia
- 1873: Prince Edward Island
- 1905: Alberta, Saskatchewan
- 1949: Newfoundland and Labrador
- 1999: Nunavut

**Recommendation**: Add all 13 provinces/territories with appropriate start dates.
Polygon quality: **Tier 2** for most, **Tier 3** for Manitoba (boundaries
changed significantly from tiny 1870 province to current extent in 1912).

**Potential entries**: 13

**Limitations**:
- Manitoba's 1870 boundaries were much smaller than today
- NWT boundaries changed dramatically (lost Alberta, Saskatchewan, parts to Ontario/Quebec)
- Modern GADM boundaries only represent current state

---

### Germany (DEU) — Rating: 4/5

**GADM admin-1**: 16 units (16 Länder/States)
**Total area**: 357,839 km²

**Boundary stability**: Good since reunification (1990). The 16 Länder have been
stable since then. However, these modern Länder have NO historical continuity with
pre-1945 German states (Prussia, Bavaria, etc.) — the post-war Allied zones and
subsequent reorganization created entirely new boundaries.

**Key dates**:
- 1949: West German Länder created by Allied occupation zones
- 1952: Baden, Württemberg-Baden, Württemberg-Hohenzollern → Baden-Württemberg
- 1957: Saarland rejoins West Germany
- 1990: 5 new Länder from East Germany

**Already in database**: Some historical German states (Bavaria, Saxony, Hanover,
Baden, Bremen, etc.) exist via CShapes-Europe.

**Recommendation**: Add 16 modern Länder as polities (1990-2025 for reunified
Germany context). Polygon quality: **Tier 2** for post-1990, but **NOT** usable
as historical proxies for pre-1945 German states.

**Potential entries**: 16

**Limitations**:
- Modern Länder ≠ historical German states
- CShapes-Europe has 30+ historical German states that are better for pre-1871
- Post-1945 boundaries were arbitrarily drawn by Allied powers

---

### Mexico (MEX) — Rating: 4/5

**GADM admin-1**: 32 units (31 states + Federal District/Mexico City)
**Total area**: 1,952,023 km²

**Boundary stability**: Good. Most state boundaries date to the 19th century.
Last new states: Baja California Sur and Quintana Roo (elevated from territories
to states in 1974).

**Key dates**:
- 1824: First federal constitution, original states
- 1863: Campeche separated from Yucatán
- 1869: Hidalgo and Morelos separated from México state
- 1974: BCS and Quintana Roo become states

**Recommendation**: Add all 32 states. Start dates vary (1824 for original states,
later for split-offs). Polygon quality: **Tier 2**.

**Potential entries**: 32

---

### Argentina (ARG) — Rating: 4/5

**GADM admin-1**: 24 units (23 provinces + Ciudad de Buenos Aires)
**Total area**: 2,780,097 km²

**Boundary stability**: Good. Most provincial boundaries date to the 19th century.
Tierra del Fuego was the last territory elevated to province status (1990).

**Recommendation**: Add all 24 provinces. Polygon quality: **Tier 2**.
**Potential entries**: 24

---

### China (CHN) — Rating: 4/5

**GADM admin-1**: 31 units (22 provinces + 5 autonomous regions + 4 municipalities)
**Total area**: 9,382,250 km²

**Boundary stability**: Mostly good. Provincial boundaries are largely inherited
from the Qing dynasty, with some modern adjustments:
- 1988: Hainan Province separated from Guangdong
- 1997: Chongqing Municipality separated from Sichuan

**Key considerations**:
- Inner Mongolia's boundaries changed significantly (expanded in 1947, contracted
  during Cultural Revolution, restored 1979)
- Tibet's modern boundaries differ from historical Tibet
- Manchuria's three provinces (Heilongjiang, Jilin, Liaoning) are relatively stable

**Recommendation**: Add major provinces with stable boundaries. Start dates need
careful research per province. Polygon quality: **Tier 2** for core provinces,
**Tier 3** for border regions with historical boundary changes.

**Potential entries**: 31

---

### Colombia (COL) — Rating: 4/5

**GADM admin-1**: 32 units (23 departments + 5 commissaries + 4 intendancies)
**Total area**: 1,136,759 km²

**Boundary stability**: Good since 1991 Constitution. Most departments date to
19th century. Southeastern departments (Guainía, Guaviare, Vaupés, Vichada)
were intendancies/commissariats until 1991.

**Recommendation**: Add all departments. Polygon quality: **Tier 2**.
**Potential entries**: 32

---

### Brazil (BRA) — Rating: 3/5

**GADM admin-1**: 27 units (26 states + Federal District)
**Total area**: 8,500,365 km²

**Boundary stability**: Moderate. Most states are long-established, but several
changes occurred in the 20th century:
- 1943: Amapá, Roraima, Rondônia, Fernando de Noronha territories created
- 1977: Mato Grosso do Sul split from Mato Grosso
- 1988: Tocantins split from Goiás

**Key consideration**: The "captaincy" system (1500s) → "province" system (1822) →
"state" system (1889) means historical continuity varies. Coastal states (São Paulo,
Rio de Janeiro, Bahia, Pernambuco, Minas Gerais) have relatively stable boundaries.

**Recommendation**: Add core states with stable boundaries (start_year = 1889 for
Republic era). Recently split states should have later start dates.
Polygon quality: **Tier 2** for historic states, **Tier 3** for recently split ones.

**Potential entries**: 27

---

### France (FRA) — Rating: 3/5

**GADM admin-1**: 13 regions (post-2016 reform)
**Total area**: 549,516 km²

**Boundary stability**: Moderate for regions (reformed in 2016 from 22 to 13),
but **departments** (admin-2) have been very stable since their creation in 1790.
For historical analysis, departments are more useful than regions.

**Recommendation**: Use departments (96 metropolitan) rather than regions for
historical proxy. GADM admin-2 has all departments. Regions only useful for
post-2016 analysis.

**Potential entries**: 13 (regions) or ~96 (departments, admin-2)

---

### South Africa (ZAF) — Rating: 3/5

**GADM admin-1**: 9 provinces
**Total area**: 1,219,710 km²

**Boundary stability**: The 9 provinces were created in 1994 for the post-apartheid
era. They have NO continuity with the historical 4-province system (Cape Colony,
Natal, OFS, Transvaal) which is already in our database.

**Already in database**: Cape Colony, Natal, Transvaal, Orange Free State.

**Recommendation**: Add 9 modern provinces (1994-2025) but note they cannot serve
as historical proxies. Polygon quality: **Tier 2** (post-1994 only).

**Potential entries**: 9

---

### Peru (PER) — Rating: 3/5

**GADM admin-1**: 26 units (24 regions + 2 provinces)
**Recommendation**: Add regions. Polygon quality: **Tier 2** for most.
**Potential entries**: 26

---

### Russia (RUS) — Rating: 2/5

**GADM admin-1**: 83 units (46 regions + 21 republics + 9 territories + 4 autonomous provinces + 2 cities + 1 autonomous region)
**Total area**: 16,925,825 km²

**Boundary stability**: Poor. Frequent changes:
- Soviet era: Numerous creations, mergers, transfers
- 2003-2008: Several mergers (e.g., Perm Krai absorbed Komi-Permyak)
- 2014: Crimea and Sevastopol annexed (internationally disputed)

**Key consideration**: The sheer number of federal subjects (83) and frequent
changes make individual tracking very complex. Major historical oblasts
(Moscow, St. Petersburg/Leningrad, Novosibirsk, Sverdlovsk) have relatively
stable boundaries.

**Recommendation**: Only add the most stable and significant subjects.
Polygon quality: **Tier 3** for stable subjects, **Tier 4** for recently merged.

**Potential entries**: ~20 (most stable subjects only)

---

### India (IND) — Rating: 2/5

**GADM admin-1**: 36 units (28 states + 8 union territories)
**Total area**: 3,152,800 km²

**Boundary stability**: Poor. Frequent reorganizations:
- 1947: Partition (British India → India + Pakistan)
- 1956: States Reorganisation Act (complete restructuring on linguistic lines)
- 1960: Bombay State → Maharashtra + Gujarat
- 1966: Punjab → Punjab + Haryana
- 2000: Chhattisgarh, Jharkhand, Uttarakhand created
- 2014: Telangana split from Andhra Pradesh
- 2019: Jammu & Kashmir reorganized into 2 UTs

**Key consideration**: Very few Indian states have stable boundaries across
the full 1947-2025 period. States reorganized in 1956 mostly retained their
post-1956 boundaries, but 7 more states were created 2000-2019.

**Recommendation**: Only add states stable since 1956 (Tamil Nadu, Kerala,
Karnataka, West Bengal, Rajasthan, etc.). Exclude recently split states
unless using post-split dates.

**Potential entries**: ~25 (stable post-1956 states)

---

### Egypt (EGY) — Rating: 2/5

**GADM admin-1**: 27 governorates
**Total area**: 983,765 km²

**Boundary stability**: Poor. Governorates have been split frequently since
the 1950s. Many current governorates were created in the 2000s.

**Recommendation**: Not recommended for individual polity entries due to
frequent boundary changes.

**Potential entries**: 0 recommended

---

### Indonesia (IDN) — Rating: 1/5

**GADM admin-1**: 33 provinces
**Total area**: 1,890,245 km²

**Boundary stability**: Very poor. Indonesia went from 27 provinces in 1999
to 34+ provinces by 2022, with constant splits. Many current province
boundaries are less than 20 years old.

**Already in database**: Island-based subnational regions (Java, Sumatra, etc.)
are already tracked for Dutch East Indies data.

**Recommendation**: Not recommended for individual province entries. Use
island-level groupings instead (already in doc 07).

**Potential entries**: 0 recommended (use existing island groupings)

---

### Nigeria (NGA) — Rating: 1/5

**GADM admin-1**: 37 units (36 states + FCT Abuja)
**Total area**: 908,410 km²

**Boundary stability**: Very poor. Nigeria went from 3 regions (1960) →
4 regions (1963) → 12 states (1967) → 19 states (1976) → 21 states (1987)
→ 30 states (1991) → 36 states (1996). Almost every boundary changed
during these reorganizations.

**Already in database**: Northern Nigeria and Southern Nigeria (pre-1914)
are already polities.

**Recommendation**: Not recommended. Modern state boundaries have no
historical continuity with any pre-1967 administrative division.

**Potential entries**: 0 recommended

---

## Summary Table

| Country | GADM Units | Rating | Recommended | Tier | Notes |
|---------|-----------|--------|-------------|------|-------|
| USA | 51 | 5 | 51 | 2 | Stable since 1912 |
| JPN | 47 | 5 | 47 | 2 | Stable since 1888 |
| AUS | 11 | 5 | 8 | 2 | Some already in DB |
| GBR | 4 | 5 | 0 | - | Already covered |
| CAN | 13 | 4 | 13 | 2-3 | Manitoba boundary issue |
| DEU | 16 | 4 | 16 | 2 | Post-1990 only |
| MEX | 32 | 4 | 32 | 2 | Stable since 1974 |
| ARG | 24 | 4 | 24 | 2 | Stable since 1991 |
| CHN | 31 | 4 | 31 | 2-3 | Mostly stable |
| COL | 32 | 4 | 32 | 2 | Stable since 1991 |
| BRA | 27 | 3 | 27 | 2-3 | Tocantins 1988 |
| FRA | 13 | 3 | 13 | 2 | Regions post-2016 |
| ZAF | 9 | 3 | 9 | 2 | Post-1994 only |
| PER | 26 | 3 | 26 | 2 | Mostly stable |
| RUS | 83 | 2 | ~20 | 3 | Only stable subjects |
| IND | 36 | 2 | ~25 | 3 | Post-1956 states |
| EGY | 27 | 2 | 0 | - | Too unstable |
| IDN | 33 | 1 | 0 | - | Constant splits |
| NGA | 37 | 1 | 0 | - | No historical continuity |

**Total recommended new polity entries**: ~374

---

## Polygon Comparison: CShapes vs GADM

Cross-comparison of CShapes 2.0 and GADM polygons for 183 countries shows:

| Metric | Value |
|--------|-------|
| Median IoU (Intersection over Union) | 0.975 |
| Mean IoU | 0.881 |
| Countries with IoU ≥ 0.8 (good) | 157 (86%) |
| Countries with IoU 0.5-0.8 (moderate) | 12 (7%) |
| Countries with IoU < 0.5 (poor) | 14 (8%) |

**Poor agreement countries** are almost all small island nations where CShapes
and GADM use different polygon resolutions or island selections:
Comoros, Cape Verde, Dominica, Israel, Saint Lucia, San Marino, São Tomé,
Saint Vincent, Tuvalu, Maldives, Marshall Islands, Seychelles, Kiribati, Tonga.

**Implication**: For subnational polygons, GADM admin-1 boundaries are fully
compatible with our CShapes-based national polygons. The subnational units
will nest correctly within the national boundaries.

---

## CShapes Temporal Polygon Evolution

For key countries, CShapes 2.0 tracks territory changes over time:

| Country | CShapes periods | Area ratio (max/min) | Key change |
|---------|----------------|---------------------|------------|
| Turkey/Ottoman | 11 | 3.5× | Ottoman dissolution |
| Poland | 9 | 3.0× | Partitions, WWI, WWII |
| Austria | 4 | 2.5× | Austria-Hungary dissolution |
| India | 8 | 1.6× | British India → modern India |
| China | 10 | 1.5× | Qing → Republic → PRC |
| USA | 3 | 1.3× | Territorial expansion |
| Russia | 25 | 1.2× | Soviet era changes |
| France | 4 | 1.0× | Very stable |
| Japan | 3 | 1.0× | Very stable |

---

## CShapes-Europe Unique Entries

41 of 46 CShapes-Europe entries have NO equivalent in CShapes 2.0. These are
primarily pre-unification German and Italian states:

**German states (30+)**: Bavaria, Saxony, Hanover, Baden, Württemberg, Bremen,
Oldenburg, Mecklenburg, Thuringia, Hesse, Frankfurt, Nassau, Hesse-Homburg,
Anhalt (3 variants), Lippe-Detmold, Waldeck, Wolfenbüttel, Hohenzollern (2),
Saxe-Weimar, Saxe-Altenburg, Saxe-Coburg-Gotha, Saxe-Meiningen, etc.

**Italian states**: Papal States, Duchy Modena, Duchy Parma, Kingdom of Naples,
Piedmont, Lucca, Massa

**Other**: Cracow (Free City), Chechnya, Circassia

These are valuable for pre-1871 (Germany) and pre-1861 (Italy) analysis and
are NOT replaceable by GADM modern boundaries.

---

## Data Sources and Methods

| Source | Data | Usage |
|--------|------|-------|
| GADM 3.6 (level1) | 3,610 admin-1 units, 228 countries | Subnational polygons |
| GADM 3.6 (level0) | 256 countries | Country-level comparison |
| CShapes 2.0 | 805 historical state periods | Temporal polygon comparison |
| CShapes-Europe | 46 pre-1886 European states | Historical European boundaries |
| polities_database.csv | 810 entries | Current polity inventory |

---

## Files

| File | Description |
|------|-------------|
| `analyze_subnational.py` | Analysis script generating all plots and CSV |
| `compare_polygons.py` | CShapes vs GADM cross-comparison script |
| `data/analysis/subnational_gadm_analysis.csv` | 552 admin-1 units with areas |
| `data/analysis/polygon_comparison.csv` | 183 country IoU comparisons |
| `data/analysis/plots/subnational_*.png` | 8 subnational analysis plots |
| `data/analysis/plots/compare_*.png` | 5 polygon comparison plots |
