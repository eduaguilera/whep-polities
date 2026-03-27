# Gap Analysis Report (v2.1)

**Date**: 2026-03-27
**Database version**: 2.1 (data integrity fixes)
**Database file**: `data/final/polities_database.csv` (1,236 entries)
**Unified GeoPackage**: `data/final/polities_database.gpkg` (1,236 rows, 1,153 with geometry)

---

## Executive Summary

The WHEP polities database contains 1,236 entries covering 1800-2025 with 99.5%
polygon coverage. This report identifies remaining gaps with emphasis on the ~30
countries most important for historical trade and agricultural production analysis.

**Key metrics:**
| Metric | Value |
|--------|-------|
| Total polities | 1,236 |
| Non-region polities | 1,159 |
| With geometry | 1,153 / 1,159 (99.5%) |
| Verified | 843 / 1,236 (68.1%) |
| ISO3 coverage | 1,088 / 1,236 (88.0%) |
| COW coverage | 398 / 1,236 (32.2%) |
| Predecessor/successor linked | ~200 / 1,236 (16.2%) |
| Knowledge graph | 1,244 nodes, 2,383 edges |

---

## 1. Trade-Critical Country Coverage

### Countries ranked by weakness (most urgent first)

#### TIER 1 -- Critical Gaps

| Country | Temporal coverage | Entries | Key gap | Trade importance |
|---------|------------------|---------|---------|-----------------|
| **Nigeria** | 56.2% (1899-2025) | 8 | Missing 1800-1898 pre-colonial | Palm oil, groundnuts, cocoa |

**Resolved in v2.1:**
- ~~New Zealand~~ → Added `NZL-1840-1907` (colony entry with CShapes polygon)
- ~~China (PRC)~~ → Added `CHN-1950-2025` sovereign entry
- ~~Canada~~ → Added `CAN-1800-1866` pre-Confederation entry with CShapes polygon

#### TIER 2 -- Structural Weaknesses

| Country | Issue | Trade importance |
|---------|-------|-----------------|
| **Japan** | ~~No subnational~~ 47 prefectures added v2.2; still no Empire period differentiation | 4th-largest economy; major silk/tea exporter 19C |
| **United Kingdom** | ~~No subnational~~ 4 nations added v2.2; still no colonial links | Center of global trade 1800-1950 |
| **Mexico** | Single entry, 226 years; no territorial changes | Silver, oil, agriculture |
| **Cuba** | Single entry; no Spanish colonial differentiation | World's largest sugar exporter, 19C |
| **South Africa** | Missing 1800-1827; aggregate added in v2.1 | Gold, diamonds, wool |
| **Argentina** | 3 entries + aggregate added in v2.1; no subnational | Top-5 agricultural exporter c.1900 |

#### TIER 3 -- Adequate but Improvable

| Country | Issue |
|---------|-------|
| **Germany** | 3-year gap 1946-1948 (occupation); many UNVERIFIED |
| **India** | No subnational; many UNVERIFIED |
| **Egypt** | Overlapping entries need rationalization |
| **Indonesia** | No subnational (IND prefix collision resolved in v2.1 → IDN-) |
| **Australia** | Pre-1901 gap (colonial entries exist separately) |

#### TIER 4 -- Strong Coverage (model examples)

| Country | Entries | Subnational | Notes |
|---------|---------|-------------|-------|
| **United States** | 108 | 102 | 100% verified; best in database |
| **Russia/USSR** | 94 | 83 | 9 historical periods + federal subjects |
| **Spain** | 61 | 52 | Provinces from 1833 |
| **Brazil** | 65 | 53 | Historical + modern states |
| **China** | 71 | 57 | Qing provinces + modern provinces |
| **Italy** | 13 | 0 | Excellent pre-unification chain |
| **France** | 21 | 0 | Good colonial aggregates |
| **Netherlands** | 10 | 0 | Colonial aggregates (DEI) |
| **Thailand** | 5 | 0 | Perfectly clean, model example |
| **Iran** | 2 | 0 | Properly linked, Cliopatria polygon |

---

## 2. Missing Aggregate Entries

Aggregate entries enable continuous trade data linkage across the full 1800-2025
period, even when sovereign/historical entries split at boundary changes.

**Added in v2.1**: `GBR-1800-2025`, `ARG-1800-2025`, `RUS-1800-2025`,
`USA-1800-2025`, `ZAF-1800-2025`.

**Remaining trading nations without aggregates:**

| Country | Current entries | Recommended aggregate |
|---------|----------------|----------------------|
| **India** | Multiple IND entries | `IND-1800-2025` |
| **Japan** | JPN-1800-2025 (single entry) | Not needed (already continuous) |
| **Cuba** | CUB-1800-2025 (single entry) | Not needed (already continuous) |
| **Mexico** | MEX-1800-2025 (single entry) | Not needed (already continuous) |

Countries with good aggregates: Germany (`GER-1800-2025`), China
(`CHN-1800-2025`), Netherlands (`DEI-1800-2025`), France (`FRA-1800-1982`),
Denmark (`DAN-1800-2025`), Indonesia (`DEI-1800-2025`), and (new) UK
(`GBR-1800-2025`), Argentina (`ARG-1800-2025`), Russia (`RUS-1800-2025`),
USA (`USA-1800-2025`), South Africa (`ZAF-1800-2025`).

---

## 3. Temporal Gaps by Continent

### Africa (260 entries)
- **1800-1830**: Thin coverage of interior West/Central/East African polities.
  43 pre-colonial kingdoms added via Paine et al. (2024) help, but major gaps
  remain (e.g., Hausa states, Lake region kingdoms pre-1850).
- **52.7% UNVERIFIED** (137/260) -- worst continent for verification.

### Asia (220 entries including subnational)
- **China 1949-2025**: ~~No `sovereign`-type entry for PRC~~ → Fixed in v2.1:
  `CHN-1950-2025` sovereign entry added.
- **India/Indonesia prefix collision**: ~~Pre-1949 entries for both use `IND-`~~
  → Fixed in v2.1: Indonesia entries renamed to `IDN-` prefix.
- **Japan**: No territorial changes reflected (Empire 1895-1945 with Korea,
  Taiwan, Manchuria not differentiated from home islands).

### Europe (321 entries including subnational)
- **Germany 1946-1948**: Allied occupation period not covered.
- **Pre-unification German states**: 12 entries (Bavaria, Saxony, Hanover, etc.)
  are mostly UNVERIFIED.
- Generally the best-covered continent.

### North America (179 entries including subnational)
- **Canada 1800-1865**: ~~No pre-Confederation entity~~ → Fixed in v2.1:
  `CAN-1800-1866` added.
- **Cuba, Mexico**: Single-entry coverage, no period differentiation.
- **USA**: Excellent -- 108 entries, 100% verified.

### South America (88 entries including subnational)
- **Argentina**: ~~No aggregate~~ → Fixed in v2.1: `ARG-1800-2025` added.
- **Brazil**: Excellent with 65 entries and historical subnational.
- **1800-1820**: Independence-era coverage is thin.

### Oceania (80 entries)
- **New Zealand 1800-1906**: ~~Major gap~~ → Fixed in v2.1: `NZL-1840-1907` added.
- **Australia pre-1901**: Federation gap (colonial entries exist separately).
- **Pacific island chieftaincies**: Largely absent before colonization.

---

## 4. Polygon/Geometry Gaps

### 6 Remaining Non-Region Polities Without Geometry

| Polity | Type | Region | Fillable? |
|--------|------|--------|-----------|
| DRO-1800-1982 Dronning Maud Land | dependency | Antarctica | YES -- Antarctic claim sector |
| DAN-1800-1845 Danish India | historical | Asia | MODERATE -- tiny trading posts |
| NEU-1800-1982 Neutral Zone | dependency | Asia | YES -- well-documented boundary |
| CAN-1800-1982 Canton & Enderbury | historical | Oceania | MODERATE -- tiny atolls |
| UNI-1800-1982 US Misc. Pacific Islands | dependency | Oceania | DIFFICULT -- scattered islets |
| USS-1859-2025 US Settlement Oceania | dependency | Oceania | DIFFICULT -- composite territory |

**Resolved in v2.1** (4 gaps filled):
- ~~MID-1859-1982 Midway Islands~~ → Natural Earth map_units polygon
- ~~WAK-1898-1982 Wake Island~~ → Natural Earth map_units polygon
- ~~JTN-1800-1982 Johnston Island~~ → Natural Earth map_units polygon
- ~~F285-2011-2023 Sark~~ → GADM admin-1 polygon (Guernsey subdivision)

All 6 remaining are minor territories. None affect trade data analysis for major countries.

### Polygon Source Distribution

| Source | Count | % |
|--------|-------|---|
| CShapes 2.0 | 425 | 34.6% |
| GADM 3.6 (subnational) | 216 | 17.6% |
| CShapes 2.0 + CShapes-Europe | 84 | 6.8% |
| CShapes 2.0 (dependencies=TRUE) | 84 | 6.8% |
| none (statistical aggregate) | 77 | 6.3% |
| GADM 4.1 | 75 | 6.1% |
| mapSpain/IGN (subnational) | 52 | 4.2% |
| USAboundaries/Newberry (subnational) | 51 | 4.2% |
| Paine et al. (2024) | 37 | 3.0% |
| GADM 4.1 or Natural Earth | 36 | 2.9% |
| CHGIS v6 (subnational) | 26 | 2.1% |
| geobr/IBGE (subnational) | 26 | 2.1% |
| CShapes-Europe | 22 | 1.8% |
| GADM 4.1 (subnational) | 7 | 0.6% |
| Paine et al. (2024) + Cliopatria | 6 | 0.5% |
| Cliopatria (Seshat) | 4 | 0.3% |

---

## 5. Verification Gaps

### By polity type (worst first)

| Type | UNVERIFIED | Total | % Unverified |
|------|-----------|-------|-------------|
| mandate | 9 | 13 | 69.2% |
| colonial | 32 | 47 | 68.1% |
| historical | 189 | 386 | 48.9% |
| dependency | 7 | 75 | 9.3% |
| sovereign | 0 | 194 | 0% |
| subnational | 0 | 371 | 0% |

### By continent (worst first)

| Continent | UNVERIFIED | Total | % |
|-----------|-----------|-------|---|
| Africa | 137 | 260 | 52.7% |
| Asia | 38 | 220 | 17.3% |
| Oceania | 13 | 80 | 16.3% |
| Europe | 42 | 321 | 13.1% |
| South America | 3 | 88 | 3.4% |
| North America | 2 | 179 | 1.1% |

**235 polities remain UNVERIFIED**, primarily African historical/colonial
entries (137), European pre-unification states (42), and Asian colonial
mandates (38).

---

## 6. Knowledge Graph Issues

### Statistics
| Metric | Value |
|--------|-------|
| Nodes | 1,244 (1,236 polities + 8 continents) |
| Edges | 2,383 |
| Edge types | 9 |
| Connected components | 55 |
| Largest component | ~1,190 nodes |
| Isolated nodes | 54 (specialized FAOSTAT regions) |

### Edge type distribution (current)
| Relation | Edges |
|----------|-------|
| located_in_continent | 1,151 |
| subregion_of | 359 |
| region_contains | 328 |
| temporal_next | 174 |
| aggregate_covers | 50 |
| predecessor_of | 45 |
| colonial_ruler_of | 38 |
| successor_of | 25 |
| same_territory | 18 |

### Known issues
1. **BRA-1822-2025 referential error**: 26 Brazilian state `subregion_of` edges
   point to `BRA-1822-2025`, but the database entry is `BRA-1909-2025`.
2. **Node CSV format bug**: 155 subnational nodes have data in alternative
   columns (`id`, `label`, `type`, `degree`) instead of primary columns.

**Resolved in v2.1:**
- ~~Broken F228 predecessor references~~ → 15 entries corrected from
  `F228-1940-1991` to `F228-1945-1991`
- ~~Sparse predecessor/successor links~~ → ~40 new links added for UK, France,
  Argentina, Brazil, Colombia, Canada, Russia/F228 chain

---

## 7. Predecessor/Successor Chain Gaps

### Overall coverage (improved in v2.1)

~40 new predecessor/successor links were added in v2.1 for trade-critical
countries: UK, France, Argentina, Brazil, Colombia, Canada, and the full
Russia/F228 chain (11 entries linked).

### Remaining missing links

| Country | Missing link |
|---------|-------------|
| South Africa | Cape Colony → ZAF (not linked as predecessor) |

### Remaining broken references
- **Italy (to 1919)** → 6 predecessor codes (SAR, TWO, PAP, TUS, DMO, DPA)
  that use shorter formats than actual polity codes
- **F77/F78** (East/West Germany) → referenced by unified Germany but codes
  don't exist in database as formatted

**Resolved in v2.1:**
- ~~UK~~ → GBR-1800-1921 ↔ GBR-1921-2025 now linked
- ~~France~~ → FRA-1800-1919 ↔ FRA-1919-2025 now linked
- ~~Argentina~~ → Full chain ARG-1800-1899 → ARG-1899-1902 → ARG-1902-2025 linked
- ~~Colombia~~ → Full chain COL-1800-1903 → COL-1903-1922 → COL-1922-2025 linked
- ~~Brazil~~ → Full chain BRA-1800-1903 → BRA-1903-1909 → BRA-1909-2025 linked
- ~~Russia~~ → Complete F228/RUS chain (11 entries) mutually linked
- ~~F228 broken references~~ → 15 post-Soviet states corrected to F228-1945-1991

---

## 8. Cross-Cutting Data Quality Issues

### IND Prefix Collision — RESOLVED in v2.1
~~Pre-1949 entries for both India and Indonesia used the `IND-` prefix.~~
Fixed: Indonesia entries renamed from `IND-1800-1889` / `IND-1889-1949` to
`IDN-1800-1889` / `IDN-1889-1949`. All `IND-` entries now refer to India only.

### Overlapping Same-ISO Entries
282 pairs of entries share the same ISO3 code with overlapping date ranges:
- 173 boundary transitions (1-year overlap at era boundaries -- by design)
- 72 different-type dual entries (colonial + sovereign -- by design)
- 58 same-entity period splits
- 53 ISO prefix collisions (different entities sharing code prefix)

### Subnational Coverage Asymmetry
| Country | Subnational entries | Historical coverage |
|---------|--------------------|--------------------|
| USA | 102 | 1800-2025 (via USAboundaries + GADM) |
| Russia | 83 | 1993-2025 only |
| Spain | 52 | 1833-2025 |
| China | 57 | 1820-1912 (Qing) + 1997-2025 (modern) |
| Brazil | 53 | 1872-2025 (via geobr + GADM) |
| Canada | 13 | 1999-2025 only |
| Australia | 11 | 1901-2025 only |
| **UK** | **4** | **1800-2025 (4 nations, added v2.2)** |
| **France** | **0** | -- |
| **Germany** | **0** | -- |
| **India** | **0** | -- |
| **Japan** | **47** | **1888-2025 (prefectures, added v2.2)** |
| **Argentina** | **0** | -- |

---

## 9. Recommended Priority Actions

### Completed in v2.1
- ~~Add NZ colonial entry~~ → `NZL-1840-1907` added
- ~~Add Canada pre-Confederation~~ → `CAN-1800-1866` added
- ~~Add PRC sovereign~~ → `CHN-1950-2025` added
- ~~Add missing aggregates~~ → GBR, ARG, RUS, USA, ZAF -1800-2025 added
- ~~Fix F228 predecessor references~~ → 15 entries corrected
- ~~Add pred/succ links~~ → ~40 links for UK, France, Argentina, Brazil, Colombia, Canada, Russia
- ~~Resolve IND prefix collision~~ → Indonesia renamed to IDN-
- ~~Fill 4 easy polygon gaps~~ → Midway, Wake, Johnston, Sark

### Completed in v2.2
- ~~Fill 2 easy polygon gaps~~ → DRO-1800-1982, NEU-1800-1982 polygons created
- ~~Fix OTT-1800-1912 polygon~~ → Replaced with full CShapes 2.0 via TUR-1800-1912
- ~~Add Japan subnational~~ → 47 prefectures (1888-2025) added
- ~~Add UK subnational~~ → 4 nations (England, Scotland, Wales, NI) added
- ~~Add interwar entities~~ → Saar (1920-35), Memel (1920-23), Fiume (1920-24) added
- ~~Fill Mongolia 1911-1921 gap~~ → MNG-1911-1921 Bogd Khanate added
- ~~Add India aggregate~~ → IND-1800-2025 added
- ~~Fix Italian predecessor codes~~ → VERIFIED: already correct (full format)
- ~~Fix BRA-1822-2025 KG reference~~ → VERIFIED: does not exist (false positive)
- ~~Fix KG node CSV misalignment~~ → VERIFIED: no misalignment (false positive)

### HIGH PRIORITY (remaining)

1. **Verify African entries**: 137 UNVERIFIED African polities, mostly
   historical/colonial. Prioritize trade-relevant: Nigeria, Egypt, South Africa.

2. **Integrate HGIS Germany** for ~15 pre-unification German states (1820-1914).
   Currently use inaccurate GADM modern Lander proxies. Requires manual download
   from NYU (geo.nyu.edu, search "ghgis") or email Harvard.

### MEDIUM PRIORITY

3. **Add Japan Empire period differentiation** (1895-1945 with colonial
   territories vs. home islands).

4. **Add France, Germany, India subnational** -- primarily for geographic
   analysis rather than trade data linkage.

5. **Nigeria pre-1899 coverage** -- biggest trade-critical temporal gap
   (palm oil, groundnuts, cocoa).

### LOW PRIORITY (nice to have)

6. **Fill 4 difficult polygon gaps**: Danish India, Canton & Enderbury, US Misc.
   Pacific Islands, US Settlement Oceania.

---

## 10. Scripts

| Script | Purpose |
|--------|---------|
| `R/15_build_unified_polygons.R` | Build unified GeoPackage from all sources |
| `R/16_data_integrity_fixes.R` | Fix pred/succ links, add aggregates, fill temporal gaps, resolve IND collision |
| `R/17_add_new_polygons.R` | v2.2: Japan/UK subnational, interwar entities, OTT/DRO/NEU polygon fixes |
| `R/08_stress_test.R` | 31 automated integrity checks |
| `R/07_build_knowledge_graph.R` | Build knowledge graph (9 relation types) |
| `R/10_analysis_plots.R` | Generate analysis visualizations |
