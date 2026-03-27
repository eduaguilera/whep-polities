# Known Issues, Decisions, and Changelog

---

## 1. Issues Found and Resolved

### FIXED: Manchukuo End Year
- **Code**: MAN-1932-2025 -> MAN-1932-1945
- **Severity**: IMPORTANT
- **Root cause**: Federico-Tena has `NA` for end_year, which defaults to 2025
- **Historical fact**: Manchukuo (Japanese puppet state in Manchuria) dissolved when
  Japan surrendered on August 15, 1945
- **Fix applied**: Added to whep_fixes.csv with forced end_year = 1945
- **Sources confirming**: COW, CShapes, all historical references

### FIXED: Ionian Islands End Year
- **Code**: ION-1815-1862 -> ION-1815-1864
- **Severity**: MINOR
- **Root cause**: Federico-Tena has end_year=1862 but its own notes say "1864-1938 Greece"
- **Historical fact**: Treaty of London signed November 14, 1863. Handover completed
  May 28, 1864. The 1862 date corresponds to King Otto's deposition, not the cession.
- **Fix applied**: whep_fixes.csv with forced end_year = 1864
- **Sources confirming**: COW, Treaty of London (1863), multiple historical references

### FIXED: Kokand End Year
- **Code**: KOK-1800-1883 -> KOK-1800-1876
- **Severity**: IMPORTANT
- **Root cause**: Federico-Tena had end_year=1883, 7 years after actual dissolution
- **Historical fact**: Khanate of Kokand formally dissolved by Russia on February 19, 1876.
  COW records conquest at 92,463 km2.
- **Fix applied**: whep_fixes.csv with forced end_year = 1876
- **Sources confirming**: COW Territorial Change, Russian historical records

### FIXED: Two Sicilies Duplicate
- **Codes**: KIN-1800-1860 ("Kingdom Two sicilies") removed; TWO-1800-1860 ("Two Sicilies") kept
- **Severity**: IMPORTANT
- **Root cause**: Federico-Tena CSV contained two separate entries for the same entity
  with identical dates and notes: "Kingdom Two sicilies" and "Two Sicilies"
- **Historical fact**: "Kingdom of the Two Sicilies" is the full name; "Two Sicilies" is
  the common short form. COW codes it as single entry #329.
- **Fix applied**: Remapped FT "Kingdom Two sicilies" to common_name "Two Sicilies"

### FIXED: Orange Free State Duplicate
- **Codes**: ORA-1848-1900 removed; ORA-1800-1910 updated to ORA-1848-1910
- **Severity**: MINOR
- **Root cause**: Two entries from different sources (FT: 1848-1900 trade period,
  CShapes: to 1910 territorial period). Overlap was genuine.
- **Fix applied**: Merged into single entry ORA-1848-1910. Start year corrected
  from 1800 to 1848 (actual founding of Orange Free State).

### FIXED: Austria-Hungary 1800 Placeholder Split
- **Code**: AUH-1800-1908 -> AUH-1800-1867 + AUH-1867-1908
- **Severity**: IMPORTANT
- **Root cause**: "Austria-Hungary" didn't exist until the Ausgleich (Compromise)
  of 1867. The entry labelled 1800-1908 conflated the Austrian Empire (Habsburg
  Monarchy) with the later Austro-Hungarian dual monarchy.
- **Historical fact**: The Austrian Empire was proclaimed in 1804. The dual monarchy
  of Austria-Hungary was created by the Austro-Hungarian Compromise of 1867.
- **Fix applied**: Split into AUH-1800-1867 "Austrian Empire" and AUH-1867-1908
  "Austria-Hungary". Updated predecessor/successor chains and knowledge graph.
- **Polygon note**: AUH-1800-1867 lacks a dedicated polygon (CShapes starts 1886).
  Potential sources: Cliopatria (Seshat), HistoGIS (Austrian Empire Crownlands 1848).

### FIXED: Greece 1800 Placeholder
- **Code**: GRC-1800-1913 -> GRC-1830-1913
- **Severity**: IMPORTANT
- **Root cause**: Greece was Ottoman territory in 1800. Greek independence was 1830.
- **Fix applied**: Start year corrected from 1800 to 1830.
- **Polygon note**: CShapes polygon (63,711 km2 from 1886) overestimates early
  Greece (~47,000 km2 in 1830). Cliopatria has more accurate boundaries.

### FIXED: Serbia 1800 Duplicate Removed
- **Code**: SER-1800-1913 deleted (superseded by SER-1816-1913)
- **Severity**: MINOR
- **Root cause**: SER-1816-1913 (VERIFIED, WHEP-fix) already corrected the start
  date. SER-1800-1913 (UNVERIFIED) was a duplicate legacy entry.

### FIXED: Bosnia and Herzegovina 1800 Placeholder
- **Codes**: BOS-1800-1908 -> BOS-1878-1908; HER-1800-1908 -> HER-1878-1908
- **Severity**: IMPORTANT
- **Root cause**: Bosnia and Herzegovina were Ottoman vilayets until the Congress
  of Berlin (1878) assigned them to Austro-Hungarian occupation.
- **Fix applied**: Start dates corrected from 1800 to 1878.

### FIXED: Denmark 1864 Schleswig-Holstein Split
- **Code**: DNK-1800-1920 -> DNK-1800-1864 + DNK-1864-1920
- **Severity**: IMPORTANT
- **Root cause**: Previously documented as known limitation. Denmark lost
  Schleswig-Holstein in the Second Schleswig War (1864), a -33% territory loss.
- **Fix applied**: Split into DNK-1800-1864 "Denmark (with Schleswig-Holstein)"
  and DNK-1864-1920 "Denmark (to 1920)". CShapes-Europe has pre-1864 polygon.

### FIXED: Iran 1800-2025 Single Entry Split
- **Code**: IRN-1800-2025 -> IRN-1800-1828 + IRN-1828-2025
- **Severity**: IMPORTANT
- **Root cause**: Qajar Iran lost the South Caucasus (modern Azerbaijan, Armenia,
  eastern Georgia) to Russia via Treaty of Gulistan (1813) and Treaty of
  Turkmenchay (1828), totalling ~170,000+ km2 (~10% of territory).
- **Fix applied**: Split at 1828. IRN-1800-1828 "Persia (Qajar)" lacks polygon;
  Cliopatria has Qajar boundaries.

### FIXED: Sweden 1800-1905 Single Entry Split
- **Code**: SWE-1800-1905 -> SWE-1800-1809 + SWE-1809-1814 + SWE-1814-1905
- **Severity**: IMPORTANT
- **Root cause**: Sweden lost Finland to Russia (Treaty of Fredrikshamn 1809,
  -42% territory ~338,000 km2) and gained Norway (Treaty of Kiel 1814,
  personal union +318,000 km2). These massive changes were not reflected.
- **Fix applied**: Split into three periods. SWE-1800-1809 and SWE-1809-1814
  lack dedicated polygons; Cliopatria and histmaps R package have boundaries.
  SWE-1814-1905 uses CShapes 2.0 polygon (valid for 1886-1905).

### FIXED: 15 African Colonial Entries with Placeholder 1800 Start Dates
- **Severity**: IMPORTANT (batch fix)
- **Root cause**: CShapes uses `NA` for start_year (meaning "existed at dataset
  start, 1886"), which was converted to 1800 in the polities database. For most
  African colonial entries, the colonial entity did not exist in 1800 — the
  territory was controlled by pre-colonial African kingdoms and polities.
- **Entries corrected** (old start → new start):
  - ALG-1830-1902: 1800→1830 (French invasion; was Regency of Algiers/Ottoman)
  - BOT-1885-1890: 1800→1885 (Bechuanaland Protectorate; was Tswana kingdoms)
  - BRI-1885-1895: 1800→1885 (British Bechuanaland Crown Colony)
  - BRI-1884-1960: 1800→1884 (British Somaliland; was Somali clan societies)
  - CON-1885-1891: 1800→1885 (Congo Free State; was Luba/Lunda/Kongo kingdoms)
  - CON-1882-1898: 1800→1882 (French Congo; was Loango/Teke kingdoms)
  - ERI-1882-1889: 1800→1882 (Italian Eritrea; was Ethiopian highlands/Ottoman coast)
  - GAB-1839-1912: 1800→1839 (French Gabon; was Mpongwe coastal polities)
  - GHA-1821-1888: 1800→1821 (British Gold Coast; Ashanti Empire dominated in 1800)
  - KAM-1884-1912: 1800→1884 (German Kamerun; was Bamoun/Fulani/Duala polities)
  - LAG-1861-1906: 1800→1861 (Lagos Colony; was Yoruba kingdom of Lagos)
  - NAT-1843-1895: 1800→1843 (Natal Colony; was Nguni peoples/Zulu Kingdom)
  - OIL-1884-1898: 1800→1884 (Oil Rivers Protectorate; was Niger Delta city-states)
  - SPA-1884-1912: 1800→1884 (Spanish West Africa; was Sahrawi tribal territories)
  - ZAN-1856-1964: 1800→1856 (Sultanate of Zanzibar; was part of Oman before 1856)
- **Polygon sources for pre-colonial entities**: Paine, Qiu & Ricart-Huguet (2024)
  has 46 pre-colonial African state polygons (Harvard Dataverse). Cliopatria (Seshat)
  has 28+ African polities with temporal variation. See docs/12_HISTORICAL_MAP_SOURCES.md.
- **Note**: Pre-colonial African boundaries represent zones of influence rather
  than hard borders. Any polygon is a scholarly approximation with ~25-100 km
  uncertainty (Paine et al. use 0.25° buffers for robustness checks).

---

## 2. Known Limitations (Unresolved)

### ~~Denmark 1864 Period Split~~ (RESOLVED)
- **Status**: FIXED — see Section 1 above. Split into DNK-1800-1864 and DNK-1864-1920.

### Afghanistan 1888-1919 Gap
- **Impact**: 31-year gap between AFG-1800-1888 and AFG-1919-2025
- **Why intentional**: No CShapes data for this period. Afghanistan was a British
  buffer state between 1888-1919 with limited sovereignty.
- **Recommendation**: Document, don't fix

### Sweden Semantic Inconsistency (Partially Resolved)
- **Issue**: SWE-1800-2025 (aggregate) still has post-1905 geometry but claims 1800-2025.
- **Resolved**: The period-specific entries are now correctly split:
  SWE-1800-1809 (with Finland), SWE-1809-1814, SWE-1814-1905 (with Norway).
- **Remaining**: SWE-1800-2025 aggregate kept for FAOSTAT data linkage (uses wrong polygon)

### Post-2019 CShapes Gap
- **Issue**: CShapes 2.0 ends in 2019. All post-2019 changes are from whep_fixes only.
- **Impact**: Post-2019 territorial changes may be missed
- **Covered**: Crimea 2014 (via whep_fixes), South Sudan 2011
- **Not covered**: 2022 Ukraine-Russia changes (intentional)

---

## 3. Design Decisions

### Decision 1: FT Trade Aggregates Span Full Periods
- **What**: 60 entities classified as "aggregate" span full or extended periods.
  These include:
  - Trade accounting aggregates (GER-1800-2025 Germany/Zollverein, CHN-1800-2025 China)
  - Dissolved colonial territories with FT end_year=NA→2025 (Belgian Congo, British
    East Africa, French Indochina, etc.)
  - Historical sub-national entities (UAE emirates, Newfoundland, Sikkim, etc.)
  - FT reporting entities (Syria and Lebanon, Nigeria (old), Tibet (old))
- **Why**: FT trade data uses these as continuous entities for trade accounting.
  Colonial-era aggregates have end_year=2025 because FT uses NA for end dates.
- **Trade-off**: These coexist with period-specific entries, which may confuse users.
  No colonial entities actually exist in 2025 — the end date is an FT artifact.
- **Recommendation**: Users should use period-specific entries for territorial analysis
  and aggregate entries for trade data linkage

### Decision 2: Pre-Unification German States Are Minimal
- **What**: Individual German states are tracked but FT aggregates all under Zollverein
- **Why**: FT doesn't have separate trade data for Bavaria vs Saxony etc.
- **Trade-off**: CShapes and COW have detailed state-level data that's not fully used
- **Recommendation**: Use GER-1800-2025 for trade; individual states for geographic analysis

### Decision 3: Colonial Periods Merged When Territory Unchanged
- **What**: DZA-1831-2025 (Algeria) spans colonial + independence
- **Why**: CShapes shows no significant territorial change at the 1962 independence
- **Trade-off**: Doesn't distinguish colonial from post-colonial governance
- **Recommendation**: Users needing colonial/post-colonial distinction should use
  the start_year + historical context

### Decision 4: 10% Area Threshold
- **What**: Territorial changes < 10% don't create new polity periods
- **Why**: Prevents proliferation of near-identical polity periods
- **Trade-off**: Some meaningful changes (India-Goa 1961) are not captured as splits
- **Recommendation**: Threshold is appropriate for trade data purposes

### Decision 5: Administrative Territories Excluded
- **What**: Danzig, Saar, Canal Zone, Trieste not tracked
- **Why**: No independent trade data exists for these
- **Trade-off**: Users studying these specific entities won't find them
- **Recommendation**: Could be added if trade data is discovered

### Decision 6: Post-2022 Ukraine-Russia Not Tracked
- **What**: Russian-claimed territories in Ukraine (Crimea already tracked for 2014)
- **Why**: War ongoing, front lines fluid, internationally disputed, CShapes has no data
- **Trade-off**: Contemporary analysis won't reflect current territorial reality
- **Recommendation**: Revisit when conflict stabilizes and CShapes updates

### Decision 7: Sovereignty Changes Don't Create New Periods
- **What**: Hong Kong 1997, Macau 1999 kept as single continuous entries
- **Why**: Territory didn't change, only sovereignty
- **Consistent with**: Polity definition (territory-based, not sovereignty-based)

### Decision 8: FAOSTAT Aggregate Regions Preserved
- **What**: 146 regional aggregates (Africa, OECD, LDCs, etc.)
- **Why**: FAOSTAT publishes aggregate data for these
- **Trade-off**: Inflates total polity count; regions don't have geometry

### Decision 9: Sub-National Entities When Historically Significant
- **What**: Australian colonies, Canadian provinces, UAE emirates, etc.
- **Why**: Had separate trade/political identities before federation/unification
- **Consistent with**: FT tracking pre-federation trade data separately

---

## 4. Changelog

### Version 1.1 (2026-03-26)
- Reclassified polity types for accuracy:
  - Marshall Islands: colonial → sovereign (independent since 1986)
  - Caroline Island, Mariana Island: colonial → aggregate (FT trade aggregates)
  - 36 dissolved colonial entities with end_year=2025: colonial → aggregate (FT artifacts)
  - UAE emirates (Fujairah, Sharjah, Ras al Khaimah, Umm al Qawain): sovereign → aggregate
  - Newfoundland, Danish Virgin Islands, Sikkim, New Guinea: sovereign → aggregate
  - Nigeria (old), Tibet (old): sovereign → aggregate (FT "(old)" entities)
  - Syria and Lebanon, China (F351): sovereign → aggregate
  - France, Metropolitan: sovereign → aggregate
  - Åland Islands: sovereign → dependency (Finnish autonomous region)
  - Réunion: sovereign → dependency (French overseas department)
  - French Guiana, French Polynesia, British Indian Ocean Territory: added to dependencies
- Fixed polygon source assignment for reclassified colonial→aggregate entities
  (colonial-era entities still use CShapes 2.0 dependencies=TRUE)
- Final type distribution: sovereign 194, historical 339, aggregate 60, dependency 75,
  colonial 47, region 77, mandate 13, disputed 4, puppet 1

### Version 1.4 (2026-03-26)
- Added 216 present-day subnational entries for top 6 countries by area:
  Russia (83), USA (51), China (31), Brazil (27), Canada (13), Australia (11)
- New polity_type "subnational" with HASC-derived codes (e.g. USCA-1959-2025)
- All 216 subnational polygons extracted from GADM 3.6 admin-1
- Database expanded from 810 to 1,026 entries; polygons from 723 to 939
- Built polity knowledge graph: 1,034 nodes, 1,900 edges, 9 relation types
  (predecessor/successor, subregion_of, aggregate_covers, temporal_next,
  colonial_ruler_of, region_contains, located_in_continent, same_territory)
- Exports: CSV edge/node lists + GraphML (for Gephi/Cytoscape/igraph)
- Added 6 knowledge graph visualization plots
- Added docs 11 (knowledge graph documentation)
- Updated type distribution: sovereign 194, historical 339, subnational 216,
  aggregate 60, dependency 75, colonial 47, region 77, mandate 13, disputed 4, puppet 1

### Version 1.3 (2026-03-26)
- Added 31-test automated stress test suite (`R/08_stress_test.R`)
- Added CShapes vs GADM polygon cross-validation (median IoU 0.975) (`R/05_cross_reference.R`)
- Added ISO prefix collision analysis (20 collision groups) (`R/10_analysis_plots.R`)
- Added exhaustive coverage gap search (68 gaps, none critical) (`R/03_gap_analysis.R`)
- Added GADM admin-1 subnational assessment for 19 major countries (`R/10_analysis_plots.R`)
- Fixed 4 polygon source assignments via improved CShapes-Europe name mapping
- Updated docs 00, 05 with new analysis results
- Added docs 08 (polygon accuracy audit), 09 (subnational major countries), 10 (validation summary)
- Generated 37 diagnostic/analysis plots total

### Version 1.2 (2026-03-26)
- Extracted 91 subnational polygons from 110 subnational regions using 4-tier quality system
- Implemented 6 extraction methods: cshapes, cshapes_merge, cshapes_subtract, gadm0, gadm1/gadm1_merge, subtract_gadm1
- Added subtraction-based polygons for China excl. Manchuria, Turkey in Asia, USA residual, British India excl. Burma
- 19 tier-4 regions documented as requiring historical GIS (no acceptable modern proxy)
- Excel data region polygon coverage: 389/409 (95.1%)
- Added comprehensive subnational polygon documentation (docs/07_SUBNATIONAL_POLYGONS.md)
- Updated analysis pipeline to include subnational coverage statistics

### Version 1.0 (2026-03-26)
- Initial release with 810 polity entries
- Applied 5 fixes from prior research (Manchukuo, Ionian Islands, Kokand,
  Two Sicilies, Orange Free State)
- Cross-referenced against: COW State System v2024 (209 states), COW Territorial
  Change v6 (381 transfers), CShapes 2.0 (930 entries), FAOSTAT (343 entities),
  UN M49 (534 entries), colleague's 24-worksheet database
- Created comprehensive documentation (6 documents)
- Database covers 1800-2025, optimized for 1850-present
- 478 polities verified, 118 regions confirmed, 5 fixes applied
