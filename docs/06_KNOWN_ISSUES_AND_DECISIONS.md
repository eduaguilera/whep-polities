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
- **Polygon note**: AUH-1800-1867 now has a Cliopatria (Seshat) polygon: "Austrian
  Empire" 1815-1819 time step (691,595 km2). Integrated via R/12_integrate_cliopatria_polygons.R.

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
- **Codes**: BOS-1800-1908 -> BOS-1878-1908; HER-1800-1908 -> HZG-1878-1908
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
- **Fix applied**: Split at 1828. IRN-1800-1828 "Persia (Qajar)" now has a Cliopatria
  polygon: "Qajar Dynasty" 1800-1804 time step (1,743,611 km2, including South Caucasus).
  Integrated via R/12_integrate_cliopatria_polygons.R.

### FIXED: Sweden 1800-1905 Single Entry Split
- **Code**: SWE-1800-1905 -> SWE-1800-1809 + SWE-1809-1814 + SWE-1814-1905
- **Severity**: IMPORTANT
- **Root cause**: Sweden lost Finland to Russia (Treaty of Fredrikshamn 1809,
  -42% territory ~338,000 km2) and gained Norway (Treaty of Kiel 1814,
  personal union +318,000 km2). These massive changes were not reflected.
- **Fix applied**: Split into three periods. SWE-1800-1809 now has Cliopatria polygon
  "Swedish Empire" 1763-1808 (790,005 km2, incl. Finland). SWE-1809-1814 has Cliopatria
  polygon "Swedish Empire" 1809-1811 (463,631 km2, without Finland).
  SWE-1814-1905 uses CShapes 2.0 polygon (valid for 1886-1905).
  All integrated via R/12_integrate_cliopatria_polygons.R.

### FIXED: 15 African Colonial Entries with Placeholder 1800 Start Dates
- **Severity**: IMPORTANT (batch fix)
- **Root cause**: CShapes uses `NA` for start_year (meaning "existed at dataset
  start, 1886"), which was converted to 1800 in the polities database. For most
  African colonial entries, the colonial entity did not exist in 1800 — the
  territory was controlled by pre-colonial African kingdoms and polities.
- **Entries corrected** (old start → new start):
  - ALG-1830-1902: 1800→1830 (French invasion; was Regency of Algiers/Ottoman)
  - BOT-1885-1890: 1800→1885 (Bechuanaland Protectorate; was Tswana kingdoms)
  - BBE-1885-1895: 1800→1885 (British Bechuanaland Crown Colony)
  - BSO-1884-1960: 1800→1884 (British Somaliland; was Somali clan societies)
  - COD-1885-1891: 1800→1885 (Congo Free State; was Luba/Lunda/Kongo kingdoms)
  - COG-1882-1898: 1800→1882 (French Congo; was Loango/Teke kingdoms)
  - ERI-1882-1889: 1800→1882 (Italian Eritrea; was Ethiopian highlands/Ottoman coast)
  - GAB-1839-1912: 1800→1839 (French Gabon; was Mpongwe coastal polities)
  - GHA-1821-1888: 1800→1821 (British Gold Coast; Ashanti Empire dominated in 1800)
  - KAM-1884-1912: 1800→1884 (German Kamerun; was Bamoun/Fulani/Duala polities)
  - LAG-1861-1906: 1800→1861 (Lagos Colony; was Yoruba kingdom of Lagos)
  - NAT-1843-1895: 1800→1843 (Natal Colony; was Nguni peoples/Zulu Kingdom)
  - OIL-1884-1898: 1800→1884 (Oil Rivers Protectorate; was Niger Delta city-states)
  - SWA-1884-1912: 1800→1884 (Spanish West Africa; was Sahrawi tribal territories)
  - ZAN-1856-1964: 1800→1856 (Sultanate of Zanzibar; was part of Oman before 1856)
- **Polygon sources for pre-colonial entities**: Paine, Qiu & Ricart-Huguet (2024)
  has 46 pre-colonial African state polygons (Harvard Dataverse). Cliopatria (Seshat)
  has 28+ African polities with temporal variation. See docs/12_HISTORICAL_MAP_SOURCES.md.
- **Note**: Pre-colonial African boundaries represent zones of influence rather
  than hard borders. Any polygon is a scholarly approximation with ~25-100 km
  uncertainty (Paine et al. use 0.25° buffers for robustness checks).

### ADDED: 43 Pre-Colonial African State Entries
- **Severity**: ENHANCEMENT
- **Rationale**: The database had no entries for pre-colonial African states that
  controlled territory before European colonization. All African "historical" entries
  were colonial constructs. This left a systematic gap in coverage, especially for
  the pre-1886 period where trade data exists but no polity entries represented the
  actual political entities.
- **Selection criteria**: All 46 states in the Paine et al. (2024) PCS.shp dataset,
  plus the Beylik of Tunis (predecessor of TUN-1881-2025). Three PCS states
  (Ethiopia, Egypt, Morocco) already existed in the database and received updated
  polygon sources instead of new entries.
- **Data source**: Paine, Qiu & Ricart-Huguet (2024), "Endogenous Colonial Borders:
  Precolonial States and Geography in the Partition of Africa", APSR 119(1), 1-20.
  Replication data: Harvard Dataverse doi:10.7910/DVN/9QJVJ1. File: `PCS.shp`
  (929 KB, 46 polygons, WGS 84). Free download, no login required.
- **Entries added (43 new)**:
  Major states (20, first batch):
  - ASH-1800-1896: Ashanti Empire (modern Ghana, ~194,003 km²)
  - SOK-1804-1903: Sokoto Caliphate (N. Nigeria/Niger, ~644,005 km²)
  - DHY-1800-1894: Kingdom of Dahomey (modern Benin, ~39,129 km²)
  - ZUL-1816-1879: Zulu Kingdom (KwaZulu-Natal, ~34,659 km²)
  - BNU-1800-1893: Bornu Empire (NE Nigeria/Chad, ~85,026 km²)
  - WAD-1800-1912: Wadai Empire (E. Chad, ~362,754 km²)
  - DFR-1800-1874: Sultanate of Darfur (W. Sudan, ~507,894 km²)
  - BGA-1800-1894: Kingdom of Buganda (central Uganda, ~38,776 km²)
  - BNY-1800-1899: Kingdom of Bunyoro (western Uganda, ~16,298 km²)
  - BKN-1800-1897: Kingdom of Benin (Edo State, Nigeria, ~9,582 km²)
  - LBA-1800-1885: Luba Empire (Katanga, DRC, ~26,898 km²)
  - LND-1800-1887: Lunda Empire (DRC/Angola/Zambia, ~67,656 km²)
  - FTJ-1800-1896: Imamate of Futa Jallon (Guinea, ~47,565 km²)
  - NDB-1823-1894: Ndebele Kingdom (Matabeleland, Zimbabwe, ~33,343 km²)
  - GZE-1824-1895: Gaza Empire (S. Mozambique, ~128,362 km²)
  - OYO-1800-1836: Oyo Empire (SW Nigeria, ~17,851 km²)
  - RWK-1800-1890: Kingdom of Rwanda (~25,159 km²)
  - BDK-1800-1890: Kingdom of Burundi (~21,575 km²)
  - LST-1822-1868: Basotho Kingdom (Lesotho, ~39,224 km²)
  - SWK-1800-1894: Swazi Kingdom (Eswatini, ~22,450 km²)
  Additional states (23, second batch — completing all 46 PCS states):
  - LZI-1800-1890: Lozi Kingdom/Barotseland (W. Zambia)
  - BRG-1800-1897: Borgu Confederacy (Nigeria/Benin border)
  - DGM-1800-1899: Kingdom of Dagbon/Dagomba (N. Ghana)
  - MOS-1800-1897: Mossi Kingdoms (Burkina Faso)
  - DMG-1800-1899: Sultanate of Damagaram (Niger/Zinder)
  - GOB-1800-1808: Kingdom of Gobir (N. Nigeria, conquered by Sokoto)
  - PNV-1800-1882: Kingdom of Porto-Novo (Benin coast)
  - BND-1800-1887: Kingdom of Bundu (Senegal-Mali border)
  - FTT-1800-1862: Imamate of Futa Toro (Senegal River)
  - IGL-1800-1901: Igala Kingdom (Niger-Benue confluence, Nigeria)
  - WLO-1800-1855: Kingdom of Waalo (Senegal River mouth)
  - CAY-1800-1886: Kingdom of Cayor (W. Senegal)
  - SNE-1800-1887: Kingdom of Sine (Sine-Saloum, Senegal)
  - JOL-1800-1890: Kingdom of Jolof (interior Senegal)
  - SLM-1800-1887: Kingdom of Saloum (Sine-Saloum, Senegal)
  - NKR-1800-1901: Kingdom of Nkore/Ankole (SW Uganda)
  - KSJ-1800-1911: Kingdom of Kasanje (Kwango valley, Angola)
  - TUN-1800-1881: Beylik of Tunis (predecessor of Tunisia)
  - BMB-1800-1899: Bemba Kingdom (N. Zambia)
  - IBD-1829-1893: Ibadan City-State (Yoruba, Nigeria)
  - EGB-1830-1914: Egba United Government/Abeokuta (Yoruba, Nigeria)
  - IJB-1800-1892: Ijebu Kingdom (Yoruba, Nigeria)
  - KZM-1800-1899: Kingdom of Kazembe (Zambia/DRC border)
- **Existing polities updated** (3): ETH-1800-1889, EGY-1800-1899, MOR-1800-1904
  received Paine et al. polygons and enriched notes.
- **Predecessor/successor links created**: Successor colonial entries updated with
  predecessor references (e.g., UGA-1894-1902 ← BGA + BNY + NKR,
  NAT-1843-1895 ← ZUL, TUN-1881-2025 ← TUN-1800-1881)
- **Polygon integration**: All 46 PCS polygons saved to
  `data/geodata/precolonial_polygons.gpkg` via `R/11_integrate_precolonial_polygons.R`.
  Areas computed using Africa Albers Equal Area projection.
- **Polygon sources**: Paine et al. (2024) for all 43; Cliopatria as co-source for
  6 entries (Ashanti, Sokoto, Zulu, Bornu, Wadai, Darfur with time-stepped boundaries)
- **Note**: Pre-colonial boundary uncertainty ~25-100 km. See docs/12 Section 3.8
  for full discussion of fundamental challenges with African historical boundaries.
- **Database count**: 1,026 → 1,073 entries

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

### Version 2.4 (2026-03-28)
- Comprehensive data integrity audit and fixes:
  - **Australian colonies**: 4 duplicate colony entries (TAS-1828-1900, AUSA-1838-1900,
    AUWA-1838-1900, VIC-1853-1900) linked to AUS-1901-2025 as successors; AUS
    predecessor list updated. Fixed 4-char iso3_codes (AUSA/AUWA → AUS).
  - **Portuguese colonies**: AGO, MOZ, GNB, CPV, STP long-spanning "sovereign" entries
    reclassified as aggregate (these span colonial + independent periods). ANG chain
    (3 entries) retyped colonial with corrected polygon_source. Chain linked ANG→AGO,
    MOZ historical→MOZ aggregate.
  - **US states**: 51 post-1959 entries gained predecessor back-links to pre-1959 entries.
  - **Brazilian states**: 26 post-1988 entries gained predecessor back-links.
  - **Asymmetric links**: 35 missing predecessor/successor back-links added across
    the database (African kingdoms, Yugoslav successors, etc.).
  - **Type reclassifications**: 48 entries spanning colonial periods reclassified from
    sovereign/historical/colonial → aggregate (Gambia, Mauritius, Philippines, Jamaica,
    Fiji, Myanmar, and 42 others). 14 overlapping entries reclassified as aggregate
    (EGY-1800-1922, PAN-1800-1979, AFG-1800-1893, IND-1800-1947, etc.).
  - **Mandates**: GEA-1884-2025 and PAL-1918-2025 reclassified mandate → aggregate.
  - **Ottoman**: Fixed free-text successor to valid code TUR-1800-1912.
  - **Madagascar**: Added polygon mismatch caveat to MAD-1800-1912 notes (Merina Kingdom
    1840 polygon applied to 1800-1912 entry; 2-5x overstatement before 1840).
- Remaining known polygon-date mismatches documented but unfixable with current sources:
  Ottoman (2% coverage), Egypt (16%), Zanzibar (26%), Russian Empire (14-18%),
  Mexico (21%), Gran Colombia (3%), USA 1803-1848 (7%), Konbaung Burma (8%).

### Version 2.3 (2026-03-28)
- Revised polity code prefixes to resolve 39 collision groups where unrelated
  polities shared the same 3-letter prefix. ISO 3166-1 alpha-3 codes take
  priority in all conflicts; non-ISO entities receive new unique prefixes.
- 100 polity codes renamed, 2 true duplicates removed (BRI-1885-1895, ST.-1800-2025)
- All predecessor/successor references, iso3_code fields, R scripts, GeoPackages,
  and documentation updated to reflect new codes.
- Key prefix resolutions (39 conflict groups):
  - **ISO holders keep prefix**: BEL (Belgium not Belgian Congo→BCG),
    CAN (Canada not Canary Islands→ICN), CHE (Switzerland not Chechnya→CCH),
    FRA (France not Frankfurt→FFK), FSM (Micronesia not French Somaliland→FRS),
    ITA (Italy not Italian Somaliland→ISM), JAM (Jamaica not J&K→JKS),
    NOR (Norway not Northern Nigeria→NNI), PER (Peru not Perak→PEK),
    PRI (Puerto Rico not Prince Edward Island→PEI), REU (Réunion not Reuss→RSU),
    SCG (Serbia-Montenegro not Saxe-Coburg-Gotha→SCK), SWE (Sweden not Saxe-Weimar→SWM)
  - **Moved to real ISO codes**: Cambodia CAM→KHM, Chad CHA→TCD, Congo CON→COG/COD,
    Mali MAL→MLI, Malaysia MAL→MYS, Niger NIG→NER, Nigeria NIG→NGA,
    Western Sahara SPA→ESH, Netherlands Antilles NET→ANT
  - **Split multi-entity prefixes**: BRI (4 British colonies→BSO/BCA/BTO),
    CON (Congo vs DRC→COG/COD), DAN (3 entities→DNI/DVI/DZG),
    DUT (2→DWI/DNG), FED (3 federations→FED/FRN/FSA), FRE (2→GUF/FWA),
    FSO (2→FOC/FRS), GER (Zollverein vs colonies→GCO/GSI/GTO),
    HER (Herat/Herzegovina→HRT/HZG), NEW (3→NSW/NFL/NGN),
    SOU (4→AUSA/SNI/SKH/SZM), SPA (5 Spanish colonies→SNA/SGN/SWA/SMO/ESH),
    ST. (3→VCT/LCA removed), VAN (2→TAS/VCI), WES (3→AUWA/WBK/DNG)
  - **Other**: Alaska ALA→ALK, Anhalt-Dessau AND→ANH, Badakhshan BAD→BKH,
    Papal States keeps PAP (Papua→PUA), Sardinia keeps SAR (Sarawak→SRW)
- Database: 1,320 → 1,318 entries (2 duplicates removed)

### Version 2.0 (2026-03-27)
- Built unified GeoPackage (`data/final/polities_database.gpkg`) combining all
  polygon sources into a single SF object joined with the polities database CSV
- Merged 7 polygon source files + recovered 23 previously missing polygons from
  CShapes raw data (COW code matching + name matching)
- Script: R/15_build_unified_polygons.R
- Polygon coverage: 1,141/1,151 non-region polities (99.1%); 10 remaining gaps
  are tiny Pacific atolls and minor historical territories
- Comprehensive gap analysis report: docs/14_GAP_ANALYSIS_REPORT.md
- Updated all documentation to reflect current state (v2.0)
- Identified trade-critical country gaps: New Zealand (missing 1800-1906),
  Nigeria (missing 1800-1898), Canada (missing 1800-1865), China (no PRC
  sovereign entry), UK/Japan/Mexico/Cuba (single-entry coverage)
- Knowledge graph: edge counts updated (located_in_continent 1,151,
  subregion_of 359, temporal_next 174, colonial_ruler_of 38,
  predecessor_of 45, successor_of 25, region_contains 328)

### Version 1.9 (2026-03-27)
- Integrated historical subnational polygons for 3 countries:
  - USA: 51 states/territories (1800-1958) from USAboundaries/Newberry Library
  - Brazil: 26 states/provinces (1872-1987) from geobr/IBGE
  - Spain: 52 provinces (1833-2025) from mapSpain/IGN
- Script: R/14_integrate_historical_subnational.R
- Database expanded from 1,099 to 1,228 entries; subnational 242 → 371
- Knowledge graph: 1,236 nodes, 2,188 edges
- GeoPackages: us_historical_states.gpkg, brazil_historical_states.gpkg,
  spain_provinces.gpkg

### Version 1.8 (2026-03-27)
- Comprehensive research survey of historical subnational polygon sources for
  11 major countries: China, USA, India, Brazil, Russia, Indonesia, France,
  Germany, Canada, Australia, Spain
- Identified freely available datasets for USA (1783-2000), Brazil (1872-2020),
  France (1790-1940), Germany (1820-1914), Russia (1820s/1897/1926/~1998),
  Spain (stable since 1833)
- Key R packages identified: USAboundaries (USA), geobr (Brazil), mapSpain (Spain)
- Documented remaining gaps: Russia 1927-1989, Indonesia 1945-1990, China 1912-1997,
  India 1800-1941 (partial), Germany 1914-1990
- Added docs/13_SUBNATIONAL_HISTORICAL_SOURCES.md (comprehensive research report)

### Version 1.7 (2026-03-27)
- Added 26 Qing Dynasty province subnational entries (1820-1912)
  from CHGIS v6 (doi:10.7910/DVN/ST5KKM, Harvard/Fudan University)
- Provinces include 18 core provinces, 3 Manchuria, 5 frontier regions
  (Xinjiang, Tibet, Inner Mongolia, Outer Mongolia, Qinghai)
- Excluded 5 South China Sea island claims and 1 treaty-disputed area (Nibuchu)
- Parent polity: CHN-1800-1895; polygon source: CHGIS v6 (subnational)
- Script: R/13_integrate_chgis_provinces.R
- Database expanded from 1,073 to 1,099 entries; subnational 216 → 242
- Knowledge graph: 1,107 nodes, 1,930 edges

### Version 1.6 (2026-03-27)
- Integrated Cliopatria (Seshat) polygons for 4 polities with no prior polygon:
  IRN-1800-1828 (Qajar), AUH-1800-1867 (Austrian Empire),
  SWE-1800-1809 (Swedish Empire + Finland), SWE-1809-1814 (Sweden post-Finland)
- Non-region polygon coverage: 996/996 (100%)
- Script: R/12_integrate_cliopatria_polygons.R

### Version 1.5 (2026-03-27)
- Fixed 8 European/Asian polities with placeholder 1800 start dates
- Corrected 15 African colonial entries with placeholder 1800 start dates
- Added 43 pre-colonial African kingdom entries from Paine et al. (2024)
  (Harvard Dataverse doi:10.7910/DVN/9QJVJ1, 46 PCS polygons)
- Script: R/11_integrate_precolonial_polygons.R
- Database expanded from 1,026 to 1,073 entries; historical 339 → 386

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
