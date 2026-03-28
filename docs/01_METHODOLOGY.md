# Polities Database: Methodology and Definitions

**Project**: Who Has Eaten the Planet (WHEP)
**Database version**: 1.0 (2026-03-27)
**Temporal scope**: 1800-2025 (optimized for 1850-present)
**Funded by**: European Research Council (ERC)

---

## 1. What Is a "Polity"?

A **polity** is a fixed territory over a continuous period of time. This definition is
specifically designed for linking historical trade data to geographic boundaries:

- **Territory change = new polity**, even if the country name stays the same.
  Example: Bulgaria in 1913 (96,345 km2) becomes a different polity from Bulgaria in
  1919 (103,146 km2) after the Treaty of Neuilly territorial adjustments.

- **Name change only (no territory change) = same polity.**
  Example: Siam renamed to Thailand in 1939 without territorial change: same polity.

- **Sovereignty change without territory change = same polity.**
  Example: Hong Kong (HKG-1841-2025) spans British colonial rule and Chinese sovereignty
  because the territory did not change in 1997.

- **Colonies are tracked separately** if they have individual trade data in the
  Federico-Tena or FAOSTAT databases.

## 2. Polity Code Format

Each polity is assigned a unique code in the format:

```
XXX-yyyy-YYYY
```

Where:
- `XXX` = ISO 3166-1 alpha-3 code (for modern/standard entities) or an artificial
  prefix (for historical entities, aggregates, or regions with no ISO code)
- `yyyy` = start year (inclusive) of the polity period
- `YYYY` = end year (inclusive); 2025 means "still exists"

### Examples:
| Code | Meaning |
|------|---------|
| `AFG-1919-2025` | Afghanistan from independence (1919) to present |
| `AFG-1800-1888` | Afghanistan historical period (pre-Durand Line) |
| `DEU-1938-1945` | Germany during Anschluss period (expanded territory) |
| `GER-1800-2025` | Germany/Zollverein trade aggregate (full history) |
| `X06-1800-2025` | Africa (FAOSTAT regional aggregate) |
| `TWO-1800-1860` | Kingdom of the Two Sicilies (historical Italian state) |

### Prefix collisions

Approximately 17 prefixes are shared by different polities. This is unavoidable given
the 3-letter constraint, but **full codes are always unique**:

| Prefix | Polities sharing it |
|--------|-------------------|
| `BEL` | Belgium (BEL-1831-2025), Belgian Congo (BEL-1885-2025) |
| `CAN` | Canada periods, Canary Islands, Canton-Enderbury Islands |
| `SAR` | Sardinia (SAR-1800-1860), Sarawak (SAR-1841-2025) |
| `PAL` | Palestine (PAL-1920-1948), Palmyra Island (PAL-1889-1912) |
| `DAN` | Danish India, Danish Virgin Islands, Danzig |
| `CON` | Congo periods, Democratic Republic of Congo periods |
| `NOR` | Norway, Northern Nigeria periods, Northwestern Rhodesia periods |
| `SOU` | South Australia, Southern Nigeria, Southern Sakhalin, Southern Morocco zone |
| `NEW` | New Guinea periods, New South Wales, Newfoundland |
| `IND` | India periods, Indonesia periods |
| `BRI` | British Bechuanaland, British Cameroon, British Somaliland, British Togoland |
| `FRE` | French Guiana periods, French West Africa periods |
| `VAN` | Van Diemen's Land (Tasmania), Vancouver's Island |
| `SPA` | Spanish Guinea, Spanish Morocco, Spanish North Africa, Spanish West Africa |
| `GER` | Germany/Zollverein, German Solomon Islands, German Togoland, German colonies |
| `WES` | West Irian (Dutch New Guinea), West Bank, Western Australia |
| `GAB` | Gabon, Gabon historical period |

## 3. Area Threshold for Period Splits

A new polity period is created when territorial change exceeds:
- **10% of total polity area** for mainland territories
- **100 km2** for island territories

Changes below these thresholds are documented but do not create new periods.

### Examples of sub-threshold changes (NOT creating new periods):
| Event | Area change | % of total | Decision |
|-------|-----------|------------|----------|
| India acquires Goa (1961) | +3,702 km2 | 0.1% | Same polity |
| Bangladesh-India enclave swap (2015) | 28.77 km2 | <0.01% | Same polity |
| Germany-Luxembourg border (various) | 3 km2 | <0.01% | Same polity |
| Botswana-Namibia island (1999) | 5 km2 | <0.01% | Same polity |

### Examples of supra-threshold changes (CREATING new periods):
| Event | Area change | % of total | New polity |
|-------|-----------|------------|------------|
| Denmark loses Schleswig-Holstein (1864) | -18,603 km2 | 33% | DNK-1800-1864 / DNK-1864-1920 (FIXED in v2.1) |
| Bulgaria after Balkan Wars (1913) | +34,775 km2 | 56% | BGR-1913-1918 |
| Finland loses Karelia (1940) | -40,000 km2 | 12% | FIN-1940-2025 |
| Hungary loses 2/3 territory (1920) | -189,000 km2 | 67% | HUN-1920-1938 |
| Lithuania loses Vilnius (1920) | -27,901 km2 | 33% | LTU-1920-1940 |

## 4. Temporal Boundaries

### Start year (1800)
The database begins at 1800 to capture the earliest Federico-Tena trade data, which
starts at 1800 for many polities. However, the **primary optimization is for 1850-present**.

### End year (2025)
All currently existing polities have end_year = 2025. This is the "current" marker
and should be updated as the project progresses.

### Cut-off for tracking changes
- **Pre-2019**: All major territorial changes tracked (source: CShapes 2.0 ends 2019)
- **2019-2025**: Only internationally recognized changes tracked (South Sudan 2011,
  Crimea 2014 via whep_fixes)
- **Post-2022**: Ukraine-Russia territorial changes NOT tracked (front lines fluid,
  internationally disputed, CShapes has no data)

## 5. Polity Type Classification

Each polity is classified into one of these types:

| Type | Definition | Examples |
|------|-----------|----------|
| `sovereign` | Independent state recognized by international community | France, Japan, Brazil |
| `historical` | Sovereign state that no longer exists | Ottoman Empire, Two Sicilies, Papal States |
| `colonial` | Territory administered by a colonial power | Belgian Congo, British East Africa |
| `dependency` | Non-sovereign territory with distinct administration | Hong Kong, Bermuda, Greenland |
| `mandate` | League of Nations or UN mandate/trust territory | Palestine mandate, Tanganyika trust |
| `occupation` | Territory under military occupation | Southern Sakhalin (Japan, 1905-1945) |
| `aggregate` | Multi-state entity tracked for trade data continuity | Germany/Zollverein, China mainland |
| `region` | FAOSTAT/UN statistical aggregate | Africa, Eastern Europe, OECD |
| `disputed` | Entity with contested sovereignty | Kosovo, Taiwan, Western Sahara |
| `puppet` | Client/puppet state of another power | Manchukuo (1932-1945) |
| `subnational` | Present-day admin-1 subdivision of a large country | California, São Paulo, Guangdong |

## 6. Continent Assignment

Polities are assigned to continents following UN M49 geographic regions:
- **Africa**: All African states and colonial entities on the continent
- **Asia**: Including Middle East, Central Asia, South/Southeast/East Asia
- **Europe**: Including Russia west of Urals, Caucasus states
- **North America**: Including Caribbean, Central America
- **South America**: All South American states
- **Oceania**: Australia, New Zealand, Pacific Islands
- **Antarctica**: Antarctic claims
- **Global**: For aggregate regions spanning multiple continents

## 7. Data Sources and Precedence

When multiple sources disagree on dates, the following precedence applies:

1. **WHEP manual fixes** (highest priority): Expert corrections
2. **CShapes 2.0**: Precise territorial data with area measurements
3. **COW Territorial Change v6**: Detailed transfer records with areas
4. **Federico-Tena**: Earliest trade data, but end years sometimes uncertain
5. **FAOSTAT**: Modern coverage, standard codes
6. **UN M49**: Standard country/region classification
7. **Cliopatria/Other**: Supplementary references

### Source-specific notes:
- **Federico-Tena** entries with `NA` for end_year default to 2025. This caused the
  Manchukuo bug (end year 2025 instead of 1945) and requires vigilance.
- **CShapes 2.0** ends in 2019. Post-2019 boundaries extrapolated from last known state.
- **FAOSTAT** starts in 1961. Pre-1961 entities rely on FT/CShapes/COW.
- **CShapes dependencies=TRUE** unlocks colonial territory polygons (930+ entries vs 315
  with dependencies=FALSE).

## 8. Predecessor/Successor Relationships

Major state transitions are tracked via predecessor/successor codes:

### Empire dissolutions:
| Empire | Year | N successors | Key successors |
|--------|------|-------------|----------------|
| Ottoman Empire | 1918-1922 | 15+ | Turkey, Syria, Iraq, Lebanon, Jordan, Palestine, Saudi Arabia, Yemen |
| Austro-Hungarian Empire | 1918 | 7 | Austria, Hungary, Czechoslovakia, parts of Yugoslavia/Romania/Poland/Italy |
| Russian Empire / USSR | 1991 | 15 | Russia, Ukraine, Belarus, Kazakhstan, Georgia, etc. |
| Yugoslavia | 1992 | 7 | Slovenia, Croatia, Bosnia, Serbia, Montenegro, Kosovo, North Macedonia |
| Czechoslovakia | 1993 | 2 | Czechia, Slovakia |

### Unifications:
| Unification | Year | Predecessor states |
|------------|------|-------------------|
| Italy | 1861 | Sardinia/Piedmont, Two Sicilies, Papal States, Tuscany, Modena, Parma, Lombardy-Venetia |
| Germany | 1871 | Prussia, Bavaria, Saxony, Hanover, Wurttemberg, Baden, Hesse, + 20 smaller states |

## 9. Design Decisions

The following deliberate choices shape the database:

1. **Trade aggregates preserved**: Entities like "Germany/Zollverein" (GER-1800-2025)
   span the entire period for trade data continuity, even though the territory changed
   many times. These coexist with period-specific entries (DEU-1800-1919, DEU-1919-1920, etc.).

2. **Pre-unification German states included but minimal**: Individual German states
   (Bavaria, Saxony, etc.) are tracked because they appear in CShapes and COW data,
   but Federico-Tena aggregates them under "Germany/Zollverein."

3. **Colonial periods merged when territory unchanged**: Algeria (DZA-1831-2025) spans
   French colonial rule and independence because there was no significant territorial
   change at the 1962 independence.

4. **Administrative territories generally excluded**: Free City of Danzig, Saar Territory,
   Panama Canal Zone, Free Territory of Trieste, etc. are excluded unless they appear as
   separate entities in trade datasets.

5. **FAOSTAT regional aggregates preserved**: Entries like "Africa" (X06-1800-2025),
   "Eastern Europe" (F5401-1800-2025), "OECD" (F5873-1800-2025) are kept because
   FAOSTAT reports aggregate data for these regions.

6. **Sub-national entities included when historically significant**: Australian colonies
   (pre-1901 federation), Canadian provinces (pre-1867 confederation), Gulf emirates
   (pre-1971 UAE), and similar sub-national entities that had separate trade identities.

## 10. Known Limitations

1. **Denmark 1864**: The loss of Schleswig-Holstein (33% of territory) is not reflected
   as a period split. DNK-1800-1920 should ideally be split into DNK-1800-1864 and
   DNK-1864-1920.

2. **Afghanistan gap**: 31-year gap between AFG-1800-1888 and AFG-1919-2025 is
   intentional (no CShapes data; Afghanistan was a buffer state).

3. **Sweden semantic inconsistency**: SWE-1800-2025 has post-1905 geometry (443,303 km2)
   but claims to cover 1800-2025. The actual 1800-1905 territory included Norway
   (761,932 km2). Kept for FAOSTAT data linkage.

4. **Post-2019 boundaries**: CShapes 2.0 ends in 2019. Post-2019 boundaries are
   extrapolated from the last known CShapes state.

5. **Pre-colonial African states**: 43 pre-colonial African kingdoms (Zulu, Ashanti,
   Sokoto, etc.) were added in v1.5 from Paine et al. (2024) with polygons.
   They lack standardized trade data but provide territorial context.

6. **WWII puppet states**: First Slovak Republic (1939-1945), Independent State of
   Croatia (1941-1945), and Italian Social Republic (1943-1945) are not tracked
   because they lack separate trade data entries.
