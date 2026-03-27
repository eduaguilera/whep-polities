# Gap Analysis Report (v2.0)

**Date**: 2026-03-27
**Database version**: 2.0 (unified GeoPackage)
**Database file**: `data/final/polities_database.csv` (1,228 entries)
**Unified GeoPackage**: `data/final/polities_database.gpkg` (1,228 rows, 1,141 with geometry)

---

## Executive Summary

The WHEP polities database contains 1,228 entries covering 1800-2025 with 99.1%
polygon coverage. This report identifies remaining gaps with emphasis on the ~30
countries most important for historical trade and agricultural production analysis.

**Key metrics:**
| Metric | Value |
|--------|-------|
| Total polities | 1,228 |
| Non-region polities | 1,151 |
| With geometry | 1,141 / 1,151 (99.1%) |
| Verified | 843 / 1,228 (68.6%) |
| ISO3 coverage | 1,080 / 1,228 (87.9%) |
| COW coverage | 398 / 1,228 (32.4%) |
| Predecessor/successor linked | 162 / 1,228 (13.2%) |
| Knowledge graph | 1,236 nodes, 2,188 edges |

---

## 1. Trade-Critical Country Coverage

### Countries ranked by weakness (most urgent first)

#### TIER 1 -- Critical Gaps

| Country | Temporal coverage | Entries | Key gap | Trade importance |
|---------|------------------|---------|---------|-----------------|
| **New Zealand** | 52.7% (1907-2025 only) | 1 | Missing 1800-1906 | Major wool/meat exporter from 1850s |
| **Nigeria** | 56.2% (1899-2025) | 8 | Missing 1800-1898 pre-colonial | Palm oil, groundnuts, cocoa |
| **China (PRC)** | No sovereign entry 1949-2025 | 71 total | Aggregate covers it, but no `sovereign` type entry for PRC | World's largest modern exporter |
| **Canada** | 70.8% (1866-2025) | 15 | Missing 1800-1865 pre-Confederation | Timber, furs, wheat |

#### TIER 2 -- Structural Weaknesses

| Country | Issue | Trade importance |
|---------|-------|-----------------|
| **Japan** | Only 1 entry for 226 years; no Empire period; no subnational | 4th-largest economy; major silk/tea exporter 19C |
| **United Kingdom** | Only 2 entries; no aggregate; no subnational; no colonial links | Center of global trade 1800-1950 |
| **Mexico** | Single entry, 226 years; no territorial changes | Silver, oil, agriculture |
| **Cuba** | Single entry; no Spanish colonial differentiation | World's largest sugar exporter, 19C |
| **South Africa** | Missing 1800-1827; colonial entries unlinked | Gold, diamonds, wool |
| **Argentina** | 3 entries; no aggregate; no subnational | Top-5 agricultural exporter c.1900 |

#### TIER 3 -- Adequate but Improvable

| Country | Issue |
|---------|-------|
| **Germany** | 3-year gap 1946-1948 (occupation); many UNVERIFIED |
| **India** | IND prefix collision with Indonesia; no subnational; many UNVERIFIED |
| **Egypt** | Overlapping entries need rationalization |
| **Indonesia** | IND prefix collision with India; no subnational |
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
period, even when sovereign/historical entries split at boundary changes. The
following important trading nations **lack aggregate entries**:

| Country | Current entries | Recommended aggregate |
|---------|----------------|----------------------|
| **United Kingdom** | GBR-1800-1921, GBR-1921-2025 | `GBR-1800-2025` |
| **Japan** | JPN-1800-2025 (single entry) | Not needed (already continuous) |
| **Argentina** | ARG-1800-1899, ARG-1899-1902, ARG-1902-2025 | `ARG-1800-2025` |
| **Russia/USSR** | 9 F228 periods + RUS entries | `RUS-1800-2025` |
| **United States** | USA-1800-1959, USA-1959-2025 | `USA-1800-2025` |
| **India** | Multiple IND entries | `IND-1800-2025` |
| **Cuba** | CUB-1800-2025 (single entry) | Not needed (already continuous) |
| **Mexico** | MEX-1800-2025 (single entry) | Not needed (already continuous) |
| **South Africa** | ZAF-1828-2025 | `ZAF-1800-2025` |

Countries that already have good aggregates: Germany (`GER-1800-2025`), China
(`CHN-1800-2025`), Netherlands (`DEI-1800-2025`), France (`FRA-1800-1982`),
Denmark (`DAN-1800-2025`), Indonesia (`DEI-1800-2025`).

---

## 3. Temporal Gaps by Continent

### Africa (260 entries)
- **1800-1830**: Thin coverage of interior West/Central/East African polities.
  43 pre-colonial kingdoms added via Paine et al. (2024) help, but major gaps
  remain (e.g., Hausa states, Lake region kingdoms pre-1850).
- **52.7% UNVERIFIED** (137/260) -- worst continent for verification.

### Asia (220 entries including subnational)
- **China 1949-2025**: No `sovereign`-type entry for PRC. Covered by aggregate
  `F351-1950-2025` and `CHN-1800-2025` for trade linkage.
- **India/Indonesia prefix collision**: Pre-1949 entries for both use `IND-`
  prefix, creating data linkage confusion.
- **Japan**: No territorial changes reflected (Empire 1895-1945 with Korea,
  Taiwan, Manchuria not differentiated from home islands).

### Europe (321 entries including subnational)
- **Germany 1946-1948**: Allied occupation period not covered.
- **Pre-unification German states**: 12 entries (Bavaria, Saxony, Hanover, etc.)
  are mostly UNVERIFIED.
- Generally the best-covered continent.

### North America (179 entries including subnational)
- **Canada 1800-1865**: No pre-Confederation entity.
- **Cuba, Mexico**: Single-entry coverage, no period differentiation.
- **USA**: Excellent -- 108 entries, 100% verified.

### South America (88 entries including subnational)
- **Argentina**: No aggregate despite 3 period entries.
- **Brazil**: Excellent with 65 entries and historical subnational.
- **1800-1820**: Independence-era coverage is thin.

### Oceania (80 entries)
- **New Zealand 1800-1906**: Major gap. No colonial-period entry.
- **Australia pre-1901**: Federation gap (colonial entries exist separately).
- **Pacific island chieftaincies**: Largely absent before colonization.

---

## 4. Polygon/Geometry Gaps

### 10 Remaining Non-Region Polities Without Geometry

| Polity | Type | Region | Fillable? |
|--------|------|--------|-----------|
| DRO-1800-1982 Dronning Maud Land | dependency | Antarctica | YES -- Antarctic claim sector |
| NEU-1800-1982 Neutral Zone | dependency | Asia | YES -- well-documented boundary |
| F285-2011-2023 Sark | dependency | Europe | YES -- sub-admin of Guernsey |
| MID-1859-1982 Midway Islands | dependency | Oceania | YES -- well-known atoll |
| WAK-1898-1982 Wake Island | dependency | Oceania | YES -- well-known atoll |
| DAN-1800-1845 Danish India | historical | Asia | MODERATE -- tiny trading posts |
| CAN-1800-1982 Canton & Enderbury | historical | Oceania | MODERATE -- tiny atolls |
| JTN-1800-1982 Johnston Island | dependency | Oceania | MODERATE -- tiny atoll |
| UNI-1800-1982 US Misc. Pacific Islands | dependency | Oceania | DIFFICULT -- scattered islets |
| USS-1859-2025 US Settlement Oceania | dependency | Oceania | DIFFICULT -- composite territory |

All 10 are minor territories. None affect trade data analysis for major countries.

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
| Nodes | 1,236 (1,228 polities + 8 continents) |
| Edges | 2,188 |
| Edge types | 9 |
| Connected components | 56 |
| Largest component | 1,027 nodes |
| Isolated nodes | 55 (all statistical regions) |

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
3. **Broken predecessor references**: 28 entries reference non-existent codes,
   primarily `F228-1940-1991` (USSR region code) used by 12 post-Soviet states.
4. **Sparse predecessor/successor links**: 86.8% of polities have neither.

---

## 7. Predecessor/Successor Chain Gaps

### Overall coverage
| Status | Count | % |
|--------|-------|---|
| Has predecessor | 52 | 4.2% |
| Has successor | 116 | 9.4% |
| Has both | 6 | 0.5% |
| Has neither | 1,066 | 86.8% |

### Important missing links for trade-critical countries

| Country | Missing link |
|---------|-------------|
| UK | GBR-1800-1921 ↔ GBR-1921-2025 (no pred/succ) |
| France | FRA-1800-1919 ↔ FRA-1919-2025 (no pred/succ) |
| Argentina | ARG-1800-1899 → ARG-1899-1902 → ARG-1902-2025 (no chain) |
| Colombia | COL-1800-1903 → COL-1903-1922 → COL-1922-2025 (no chain) |
| Brazil | BRA-1800-1903 → BRA-1903-1909 → BRA-1909-2025 (no chain) |
| Russia | F228 chain entries lack mutual links |
| South Africa | Cape Colony → ZAF (not linked as predecessor) |

### Broken references (28 total)
- **12 post-Soviet states** → `F228-1940-1991` (code not in non-region subset)
- **Italy (to 1919)** → 6 predecessor codes (SAR, TWO, PAP, TUS, DMO, DPA)
  that use shorter formats than actual polity codes
- **F77/F78** (East/West Germany) → referenced by unified Germany but codes
  don't exist in database as formatted

---

## 8. Cross-Cutting Data Quality Issues

### IND Prefix Collision
Pre-1949 entries for both India and Indonesia use the `IND-` prefix:
- `IND-1800-1893`, `IND-1893-1914`, etc. → India
- `IND-1800-1889`, `IND-1889-1949` → Indonesia

This creates confusion in code-based lookups. Modern entries correctly
differentiate: India uses `IND-1947-2025`, Indonesia uses `IDN-1945-2025`.

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
| **UK** | **0** | -- |
| **France** | **0** | -- |
| **Germany** | **0** | -- |
| **India** | **0** | -- |
| **Japan** | **0** | -- |
| **Argentina** | **0** | -- |

---

## 9. Recommended Priority Actions

### HIGH PRIORITY (for trade data analysis)

1. **Add New Zealand colonial entry** (`NZL-1840-1907` or similar) to fill the
   1800-1906 gap. Critical for 19th-century wool/meat trade data.

2. **Add Canada pre-Confederation entry** (`CAN-1800-1866` or similar) to fill
   the 1800-1865 gap. Critical for timber/fur trade data.

3. **Add PRC sovereign entry** (`CHN-1949-2025` or `CHN-1950-2025` sovereign).
   The aggregate exists but a sovereign-type entry is structurally expected.

4. **Add missing aggregate entries** for UK (`GBR-1800-2025`), Argentina
   (`ARG-1800-2025`), Russia (`RUS-1800-2025`), USA (`USA-1800-2025`).

5. **Fix BRA-1822-2025 KG reference** to point to `BRA-1909-2025`.

### MEDIUM PRIORITY (data quality)

6. **Verify African entries**: 137 UNVERIFIED African polities, mostly
   historical/colonial. Prioritize trade-relevant: Nigeria, Egypt, South Africa.

7. **Fix broken predecessor/successor references** (28 entries), particularly
   the F228 (USSR) and Italian pre-unification chain.

8. **Add predecessor/successor links** for trade-critical countries (UK, France,
   Argentina, Brazil, Colombia, Russia).

9. **Resolve IND prefix collision**: Consider renaming pre-1949 Indonesia
   entries from `IND-` to `IDN-` prefix for consistency.

### LOW PRIORITY (nice to have)

10. **Fill 5 easy polygon gaps**: Dronning Maud Land, Neutral Zone, Sark,
    Midway, Wake Island (all well-documented territories).

11. **Add Japan Empire period differentiation** (1895-1945 with colonial
    territories vs. home islands).

12. **Add subnational for UK, France, Germany, India** -- but these primarily
    serve geographic analysis rather than trade data linkage (per
    `cleaning_geography.xlsx` analysis, few subnational trade mentions exist).

13. **Fix KG node CSV format** for 155 subnational entries with misaligned
    columns.

---

## 10. Scripts

| Script | Purpose |
|--------|---------|
| `R/15_build_unified_polygons.R` | Build unified GeoPackage from all sources |
| `R/08_stress_test.R` | 31 automated integrity checks |
| `R/07_build_knowledge_graph.R` | Build knowledge graph (9 relation types) |
| `R/10_analysis_plots.R` | Generate analysis visualizations |
