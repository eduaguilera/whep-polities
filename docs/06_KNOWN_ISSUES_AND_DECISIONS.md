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

---

## 2. Known Limitations (Unresolved)

### Denmark 1864 Period Split
- **Impact**: DNK-1800-1920 doesn't capture the loss of Schleswig-Holstein in 1864
- **Territory loss**: 33% (57,086 km2 to 38,483 km2)
- **Why not fixed**: Requires team discussion. Changes needed in common_names.csv,
  polity_codes.csv, and potentially rename_cshapes.csv. CShapes starts at 1886
  so it doesn't contain the 1864 change directly.
- **Recommendation**: Split into DNK-1800-1864 and DNK-1864-1920

### Afghanistan 1888-1919 Gap
- **Impact**: 31-year gap between AFG-1800-1888 and AFG-1919-2025
- **Why intentional**: No CShapes data for this period. Afghanistan was a British
  buffer state between 1888-1919 with limited sovereignty.
- **Recommendation**: Document, don't fix

### Sweden Semantic Inconsistency
- **Issue**: SWE-1800-2025 has post-1905 geometry (443,303 km2) but claims to cover
  1800-2025. Actual 1800-1905 territory included Norway (761,932 km2).
- **Why kept**: Breaking this would disrupt FAOSTAT data linkage
- **Recommendation**: Document the inconsistency for users

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
