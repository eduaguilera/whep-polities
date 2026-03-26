# Polygon Accuracy Audit

---

## Purpose

This document records findings from a deep audit of polygon accuracy across the
database, focusing on areas where our polygon proxies may significantly misrepresent
historical territorial reality. Each entry includes the historical reality, our
current polygon, the magnitude of inaccuracy, and available sources for improvement.

Severity ratings:
- **CRITICAL**: Polygon territory differs by >50% from historical reality
- **MAJOR**: Polygon territory differs by 20-50%
- **MODERATE**: Polygon territory differs by 5-20%
- **MINOR**: Polygon territory differs by <5% or the issue is conceptual

---

## 1. Africa: Pre-Colonial and Early Colonial (pre-1886)

### 1.1 Ethiopia (ETH-1800-1889) — CRITICAL

**Historical reality**: Pre-1889 Ethiopia was dramatically smaller than post-Menelik
Ethiopia. During the Zemene Mesafint (Era of Princes, 1769-1855), the empire was
fragmented among rival warlords. Effective control was limited to the highland core:
Gondar, Gojjam, Shewa, parts of Tigray, and Wello (~250,000-350,000 km2).

Menelik II (1889-1913) tripled Ethiopian territory through conquest: Harar (1887),
Ogaden (1891), Arsi/Bale (1891), Wolayta (1894-95), Kaffa (1897), and western
borderlands. By 1898, Ethiopia had roughly its modern borders (1,100,000+ km2).

**Our polygon**: CShapes polygon dated 1898-1902 (post-expansion), back-projected
to 1800. This shows the full modern-sized Ethiopia for the entire 1800-1889 period.

**Magnitude of error**: The polygon is 2-3x too large for 1800-1855. Territory that
was NOT Ethiopian before 1889: Eritrea (Italian from 1882), Ogaden, Harar (independent
emirate until 1887), Kaffa, Wolayta, Sidamo, Illubabor, and the entire southern tier.

**Available sources**:
- Paine, Qiu & Ricart-Huguet (2024/2025), "Endogenous Colonial Borders" —
  APSR Dataverse replication data contains 46 digitized pre-colonial African state
  polygons including Ethiopia
- Territorial evolution well-documented in academic literature

### 1.2 Egypt (EGY-1800-1899) — CRITICAL

**Historical reality**: The Khedivate of Egypt's territory fluctuated enormously:
- 1800-1820: Egypt proper (Nile Delta to First Cataract, ~1 million km2)
- 1820-1882: Egypt + Sudan (conquered 1820-24) + Equatoria province (est. 1871).
  At maximum extent (c. 1875), Egyptian claims reached Lake Albert in modern Uganda.
  Total territory: ~3.5 million km2.
- 1882-1885: British occupation. Mahdist revolt destroyed Egyptian control of Sudan.
- 1885-1899: Egypt alone (without Sudan). Sudan fell to the Mahdists entirely.

**Our polygon**: CShapes 1886-1899 polygon (post-Mahdist revolt, Egypt without Sudan),
back-projected to 1800.

**Magnitude of error**: For 1820-1882, the polygon is missing ~60% of Khedivate
territory (Sudan = 1.86 million km2). For 1871-1882, it's also missing Equatoria.

**Note**: The Anglo-Egyptian Condominium (1899-1956) is captured separately in our
database as SUD-1882-2025, but there is no polygon linking Egypt to Sudan for the
1820-1882 period when Egypt actually controlled Sudan.

### 1.3 Zanzibar Sultanate (ZAN-1800-1964) — CRITICAL

**Historical reality**: Under Said bin Sultan (d. 1856), Zanzibar controlled a vast
mainland coastal strip from Cape Delgado (Mozambique) to Mogadishu (Somalia), roughly
1,500 km of coastline with 10-40 km depth inland. This was a major commercial empire
controlling ivory and slave trade routes into the African interior.

- 1856: Omani empire split; Zanzibar became separate sultanate
- 1886: Anglo-German commission defined Sultan's mainland territory as 10-nautical-mile
  coastal strip
- 1888-1890: Germany and Britain leased/purchased the coastal strips
- 1890: Heligoland-Zanzibar Treaty. Sultan retained only the islands.

**Our polygon**: CShapes 1895-1963 — islands only (Zanzibar + Pemba).

**Magnitude of error**: For 1800-1886, the island-only polygon understates Zanzibari
territory by ~90%. The mainland coastal empire is completely missing.

### 1.4 Morocco (MOR-1800-1904) — MAJOR (conceptual)

**Historical reality**: Pre-colonial Morocco's sovereignty was fundamentally graduated:
- **Bled al-makhzen**: Territory under effective government control (fluctuated by
  reign and season)
- **Bled es-siba**: "Land of dissidence" — nominal religious allegiance but no taxation
  or administrative control (Rif, Atlas Mountains, parts of Sous at various times)
- Southern "border" was non-existent; the Sultan claimed suzerainty over Saharan nomads
  as far as Timbuktu, but this was administratively meaningless

**Our polygon**: CShapes 1886-1902, likely showing approximately modern borders.

**Magnitude of error**: The concept of fixed Moroccan borders is anachronistic. Modern
borders include Western Sahara territory that was never part of pre-colonial Morocco.
The Rif and Atlas were frequently in "siba." Any polygon with a clear southern line is
an anachronism.

### 1.5 Madagascar (MAD-1800-1912) — MODERATE

**Historical reality**: The Merina Kingdom expanded from the central highlands:
- 1800: Controlled only the central highlands (~10% of the island)
- 1810-1828: Radama I conquered most coastal peoples
- 1830s: Controlled ~2/3 to 3/4 of the island
- Never fully subjugated western Sakalava kingdoms of Menabe and Boina
- 1896: French colonization — full island becomes colonial territory

**Our polygon**: CShapes 1886-1896 — likely the whole island or most of it.

**Magnitude of error**: Whole-island polygon overstates Merina territory for 1800
(~90% too large), 1815 (~60% too large), 1830 (~25% too large). Becomes reasonable
approximation after 1830.

### 1.6 Eritrea (ERI-1800-1889) — MODERATE (conceptual)

**Historical reality**: There was no "Eritrea" before Italian colonization (1882-1889).
The territory was split between the Ethiopian Empire (highlands around Asmara), the
Ottoman Empire (coastal Massawa, 1557-1865), and Egypt (Massawa, 1865-1882). Italy
acquired coastal stations starting 1869 (Assab) and formally established the colony
on January 1, 1890.

**Our polygon**: CShapes 1886-1889 (likely Italian coastal possessions — tiny strips
around Massawa and Assab).

**Issue**: The entity "Eritrea (to 1889)" does not correspond to any historical polity.
This is a Federico-Tena artifact. The polygon is small but conceptually problematic.

---

## 2. Colonial Boundary Accuracy

### 2.1 French West Africa Internal Boundaries — MODERATE

Internal boundaries between AOF sub-colonies shifted frequently:
- 1919: Upper Volta carved from Upper Senegal and Niger
- **1932**: Upper Volta dissolved entirely (territory split between Ivory Coast,
  French Sudan, and Niger)
- **1947**: Upper Volta reconstituted with previous boundaries

CShapes 2.0 correctly captures these major reorganizations through period splits for
Mali, Niger, Ivory Coast, and Burkina Faso. However, pre-1904 internal boundaries were
extremely fluid and provisional. The boundary between Niger and Nigeria was not fully
demarcated until the 1906 Anglo-French Convention.

### 2.2 German Kamerun (1884-1919) — MINOR

CShapes correctly captures the dramatic **Neukamerun** expansion of 1911 (gaining
~275,000 km2 from French Equatorial Africa as compensation for Morocco/Agadir Crisis)
and its reversion after 1916. Our database correctly splits at KAM-1912-1919.

### 2.3 Zanzibar Mainland Territories — see 1.3 above

### 2.4 Congo Free State / French Congo Border — MINOR

The modern DRC/Republic of Congo border follows the colonial-era Congo River/Ubangi
River boundary established 1885-1895 with ~98% accuracy. Uti possidetis juris applies
well here.

---

## 3. Central Asian Khanates (pre-1886) — MODERATE

### 3.1 Khiva Khanate (KHI-1800-1873)

**Historical reality**: The Khanate of Khiva occupied the Amu Darya delta region
(modern Karakalpakstan + Khorezm regions of Uzbekistan + parts of Turkmenistan).
The khanate's borders fluctuated with nomadic Turkmen tribal allegiances. Conquered
by Russia in 1873, became a protectorate, formally abolished 1920.

**Our polygon**: CShapes has a "Khiva" entry. The polygon source is noted as
"GADM 4.1 or Natural Earth" (weakest tier) in our metadata.

**Magnitude of error**: Uncertain without comparing actual geometry. The main risk
is that modern administrative boundaries don't capture the fluid nomadic frontier.
The oasis core (Khiva city and irrigated Amu Darya lands) is well-defined, but
the desert periphery was never demarcated.

### 3.2 Kokand Khanate (KOK-1800-1876)

**Historical reality**: Occupied the Fergana Valley and surrounding areas (modern
Fergana, Andijan, Namangan regions of Uzbekistan + parts of Kyrgyzstan and
Tajikistan). The khanate expanded significantly under Alim Khan (1799-1810) to
include Tashkent and parts of the steppe, but lost territory to Bukhara and Russia.
Conquered and annexed by Russia in 1876.

**Our polygon**: Matched to CShapes "Kokand" entry via name mapping.

### 3.3 Bukhara Emirate (BUK-1800-1920)

**Historical reality**: The largest Central Asian state, covering most of modern
Uzbekistan (except Khiva and Kokand territories) plus parts of Tajikistan and
Turkmenistan. Became a Russian protectorate in 1868. The emirate included the
important cities of Bukhara and Samarkand. Abolished in 1920 when the Bolsheviks
established the Bukharan People's Soviet Republic.

**Our polygon**: Matched to CShapes "Bokhara" entry. CShapes uses the older
transliteration.

### 3.4 Chechnya (CHE-1816-1857) — BUG FIXED

**Historical reality**: The Chechen resistance under Imam Shamil (Caucasian
Imamate) controlled highland areas of the northeastern Caucasus, not a well-defined
state but a zone of guerrilla resistance to Russian conquest. The entity represents
the period before final Russian conquest (1857).

**Our polygon**: Previously **WRONG** — matched to Switzerland's polygon due to
ISO code collision (CHE = Switzerland in ISO 3166-1). Now correctly matched to
CShapes-Europe "Chechnya" entry.

**Bug details**: The polity code prefix "CHE" collided with Switzerland's ISO 3166-1
code. The COW code (225 = Switzerland) was also erroneously assigned. Fixed by
removing the COW code for this entity and adding explicit name mapping.

---

## 4. German Pre-Unification States (pre-1871)

### 4.1 Overview — MODERATE

Our database contains ~15 German pre-unification states (1800-1871). Most use
"GADM 4.1 or Natural Earth" or "CShapes-Europe" as polygon sources. Key issues:

**Historical complexity**: Pre-unification German states often had non-contiguous
territories (exclaves, enclaves). For example:
- Prussia had territories from the Rhineland to East Prussia
- Bavaria included the Palatinate (left bank of Rhine), detached from main territory
- Hesse was split between Hesse-Kassel (north) and Hesse-Darmstadt (south)
- Mecklenburg was split between Mecklenburg-Schwerin and Mecklenburg-Strelitz

**GADM proxy accuracy**: Modern German Länder boundaries do NOT correspond to
pre-unification states. For example:
- Modern Baden-Württemberg ≠ historical Baden + Württemberg (different boundaries)
- Modern Hessen ≠ Hesse-Kassel + Hesse-Darmstadt (Rheinhessen now in Rhineland-Palatinate)
- Modern Thuringia ≠ any single historical state (composed of ~20 Thuringian states)

### 4.2 Saxe-Weimar (SWE-1816-1870) — BUG FIXED

**Previous bug**: Matched to **Sweden's polygon** due to ISO code collision
(SWE = Sweden in ISO 3166-1). The Grand Duchy of Saxe-Weimar-Eisenach was a
small Thuringian state (~3,600 km2), not Scandinavia.

**Fix**: Removed COW code, added to SKIP_COW_MATCHING set. Now correctly matches
via CShapes-Europe "Saxe-Weimar" entry.

### 4.3 Available source: HGIS Germany

The HGIS Germany project (hgis-germany.de) provides historical GIS data for German
states from 1820-1914 at three levels: state, province, and district. Data is available
through Harvard Geospatial Library. This would significantly improve polygon accuracy
for all German pre-unification entries.

---

## 5. Caribbean and Small Island States

### 5.1 Caribbean Island COW Code Cascade — BUG FIXED

**Bug**: Three Caribbean islands had wrong polygons due to a discrepancy between
the COW State System numbering and CShapes' internal COW codes:

| Entity | Our COW | CShapes COW | Matched to |
|--------|---------|-------------|------------|
| Dominica (DMA) | 56 | 54 | St. Lucia (CShapes COW 56) |
| Saint Lucia (LCA) | 57 | 56 | St. Vincent (CShapes COW 57) |
| St. Vincent (VCT) | 58 | 57 | Antigua (CShapes COW 58) |

The COW State System assigns COW 56 = Dominica, but CShapes assigns COW 56 =
St. Lucia. This one-off discrepancy cascaded through three islands.

**Fix**: Added explicit CSHAPES_NAME_MAP entries for all Caribbean islands,
bypassing the COW code matching step entirely.

### 5.2 Other ISO Code Collisions — BUGS FIXED

| Polity code | Entity | Previously matched to | Root cause |
|-------------|--------|----------------------|------------|
| NOR-1900-1911 | Northeastern Rhodesia | Norway | NOR = Norway ISO |
| NOR-1900-1905 | Northwestern Rhodesia | Norway | NOR = Norway ISO |
| NOR-1905-1911 | Northwestern Rhodesia | Norway | NOR = Norway ISO |
| PER-1800-1896 | Perak (Malay State) | Peru | PER = Peru ISO |
| CHE-1816-1857 | Chechnya | Switzerland | CHE = Switzerland ISO |
| SWE-1816-1870 | Saxe-Weimar | Sweden | SWE = Sweden ISO |
| JAM-1947-1949 | Jammu & Kashmir | Jamaica | JAM = Jamaica ISO |
| CAN-1800-1982 | Canton & Enderbury Is. | Canada | CAN = Canada ISO |
| SAR-1800-1860 | Sardinia | Malta | COW 338 = Malta in CShapes |
| GER-1800-1899 | German Solomon Is. | Germany (Prussia) | GER = Germany code |
| GER-1884-2025 | German colonies Oceania | Germany (Prussia) | GER = Germany code |

**Root cause**: The `build_database.py` script assigned COW codes based on ISO3
prefix lookup. When a historical entity's polity code prefix (e.g., "NOR" for
Northeastern Rhodesia) matches a modern country's ISO 3166-1 code (NOR = Norway),
the wrong COW code was assigned. The polygon builder then matched via COW code,
producing a wrong-continent match.

**Fixes applied**:
1. Added ISO collision exclusion logic in `build_database.py` — historical entities
   with colliding prefixes no longer get the modern country's COW code
2. Added explicit CSHAPES_NAME_MAP entries in `build_polygons.py` for all affected entities
3. Added SKIP_COW_MATCHING set to prevent COW code matching for collision entries
4. Extended the guard to the GADM ISO fallback matching step

**Impact**: 13 polygon assignments corrected (11 wrong-continent fixes, 2 wrong-island
fixes within the Caribbean).

---

## 6. Pre-1886 European States

### 6.1 CShapes Pre-1886 Gap

CShapes 2.0 coverage starts at 1886. Our database extends to 1800. The gap is filled
by CShapes-Europe (46 entities, 1806-2023) and backward projection of earliest CShapes
polygons. This is fundamentally problematic for entities whose territory changed
significantly between 1800-1886.

### 6.2 Pre-Confederation Canadian Colonies

Our database includes 6 Canadian pre-Confederation entities (1800-1866/1867):
Lower Quebec, New Brunswick, Nova Scotia, Ontario, Prince Edward Island, British
Columbia. These use "GADM 4.1 (subnational)" — modern Canadian province boundaries.

**Accuracy**: Modern Canadian province boundaries are good proxies because they were
largely established during the colonial period. Ontario's 1867 boundary is close to
the modern boundary (expanded northward in 1912). Quebec's 1867 boundary extended to
Hudson Bay only in 1912. Overall: acceptable proxy with caveat about northern expansions.

---

## 7. Ottoman Empire — MODERATE (with caveat)

**Historical reality**: At its zenith in 1800, the Ottoman Empire controlled Anatolia,
the Balkans, the Levant, Mesopotamia, the Arabian Peninsula (varying control), Egypt
(nominal suzerainty), and North Africa (Libya, Tunisia). Total: ~5-6 million km2.
The empire contracted dramatically during the 19th century.

**Our polygons**: The database has TWO overlapping entries for the pre-1912 period:

| Entry | Polygon source | Area (deg²) | Bounds |
|-------|---------------|-------------|--------|
| **TUR-1800-1912** (Türkiye) | CShapes 2.0 (1886-1908) | 283 | 9-51°E, 13-44°N |
| **OTT-1800-1912** (Ottoman Empire) | CShapes-Europe | 64 | 16-42°E, 35-48°N |

The **TUR entry** has the correct large polygon from CShapes 2.0, covering Anatolia,
the Levant, Mesopotamia, Arabia (down to 13°N including Yemen), and North Africa. This
is comprehensive and reasonably accurate for the 1886-1908 Ottoman territory.

The **OTT entry** has only the small CShapes-Europe polygon (Balkans/Anatolia subset).
This is because the matching logic tries CShapes-Europe first (the polygon_source says
"CShapes 2.0 + CShapes-Europe"), and CShapes-Europe has a match for "Ottoman Empire."

CShapes also correctly captures the Ottoman territorial contraction through 5 period
splits from 1886-1923 (282→81 deg²), tracking the Balkan Wars, WWI losses, and the
establishment of the Republic of Turkey.

**Assessment**: For practical use, TUR-1800-1912 provides accurate Ottoman territorial
representation. The OTT-1800-1912 entry's smaller polygon is a matching priority issue
(CShapes-Europe found first). If users need Ottoman Empire territory, they should use
the TUR entry.

---

## 8. Qing China (CHN-1800-1912) — MAJOR

**Historical reality**: The Qing Empire at its maximum extent (c. 1820) included:
- China proper (18 provinces)
- Manchuria (homeland of the Qing dynasty)
- Inner Mongolia
- Outer Mongolia (tributary, 1.5+ million km2)
- Xinjiang (conquered 1757-59, reconquered 1876-78 after Dungan Revolt)
- Tibet (varying degrees of control, amban system)
- Taiwan

Total area: approximately 13-14 million km2 at maximum.

**Our polygon**: CShapes "China" (73-135°E, 18-54°N). This represents roughly modern
PRC borders including Manchuria, Inner Mongolia, Xinjiang, and Tibet.

**Key issue**: Outer Mongolia (~1.5 million km2). CShapes creates the Mongolia entry
starting 1921 (Soviet-backed independence), but Mongolia was already effectively
independent from 1911 (Bogd Khan's declaration after the Xinhai Revolution). For the
period 1800-1911, the Qing's sovereignty over Outer Mongolia is not reflected — the
China polygon likely uses modern borders that exclude Mongolia.

**Magnitude of error**: ~10-15% of Qing territory missing for 1800-1911 period
(Outer Mongolia). The actual CShapes China polygon may include Tibet and Xinjiang
(modern PRC extent), which is reasonable for the Qing period.

---

## 9. Interwar European Entities (1918-1939)

### 9.1 Missing Entities

Several interwar League of Nations mandated territories have no entry in our database:

| Entity | Period | Area | Status |
|--------|--------|------|--------|
| **Saar Territory** | 1920-1935 | ~2,570 km2 | NOT IN DATABASE |
| **Memel Territory** | 1920-1923 | ~2,600 km2 | NOT IN DATABASE |
| **Free City of Fiume** | 1920-1924 | ~28 km2 | NOT IN DATABASE |

The Saar Territory (administered by League of Nations 1920-1935, returned to Germany
by plebiscite) is the most significant omission. The Memel Territory (administered
by France/League 1920-1923, then seized by Lithuania) is also notable.

### 9.2 Mongolia 1911-1921 Gap

Mongolia declared independence from China in 1911 (Bogd Khan), but CShapes starts
Mongolia at 1921 (Soviet-backed). This creates a 10-year gap where Mongolia exists
as a de facto independent state but has no polygon in our database.

### 9.3 Baltic States Pre-1940 vs Post-1991 Borders

Estonia, Latvia, and Lithuania have slightly different borders in their pre-1940
incarnations compared to post-1991:
- Estonia: Lost the Petseri (Pechory) district to Russia (1944)
- Latvia: Lost Abrene (Pytalovo) district to Russia (1944)
- Lithuania: Gained Vilnius region (from Poland 1939, confirmed 1945) and Klaipėda
  (Memel, from Germany 1923/1945)

CShapes captures these changes through period splits. The magnitude of difference
is small (~5% of territory) for Estonia and Latvia, larger for Lithuania.

### 9.4 Danzig Free City (DAN-1919-1938)

CShapes has a Danzig entry. The polygon correctly represents the Free City territory
(~1,966 km2 including the city and surrounding rural districts). This is well-captured.

---

## 10. Available Historical GIS Sources

### 10.1 High Priority

| Dataset | Coverage | Format | Access |
|---------|----------|--------|--------|
| **Paine, Qiu & Ricart-Huguet (2024)** | 46 pre-colonial African states | Shapefiles | APSR Dataverse |
| **CShapes 2.0** (already used) | 1886-2019, global | GeoPackage | ETH Zurich |
| **Murdock (1959) digitized** | 825 African ethnic groups, ~1890-1910 | Shapefiles | Harvard Dataverse / R package |
| **HGIS Germany** | German states 1820-1914 | Shapefiles | Harvard Geospatial Library |

### 10.2 Reference Sources (not GIS-ready)

| Source | Coverage | Notes |
|--------|----------|-------|
| **Brownlie (1979)** African Boundaries | Treaty-by-treaty documentation for all African colonial borders | The reference CShapes itself uses |
| **Ajayi & Crowder (1985)** Historical Atlas of Africa | Definitive historical atlas, 7 regional maps for 19th century | Digitized in part by Paine et al. |
| **Omniatlas** | Interactive global historical atlas | omniatlas.com — visual reference, not downloadable GIS |
| **Centennia Historical Atlas** | European borders 1000-2000 CE | Commercial software |

### 10.3 Institutional Portals

| Portal | URL | Content |
|--------|-----|---------|
| **geoBoundaries** | geoboundaries.org | Modern admin boundaries, some historical |
| **openAFRICA** | open.africa | Current African boundaries |
| **COLDAT** | beckerbastian.net/data | Colonial dates dataset (temporal, not spatial) |
| **Hiribarren Borno Maps** | vincenthiribarren.com/borno | Digitized Bornu boundary evolution |

---

## 11. Polygon Matching Bugs Found and Fixed

### 11.1 Summary

A comprehensive audit of the polygon matching pipeline discovered **13 wrong polygon
assignments** across two categories:

1. **ISO code collisions** (11 entities): Historical entity polity code prefixes
   collided with modern ISO 3166-1 country codes, causing the COW code lookup to
   assign the wrong country's code, which then matched the wrong polygon.

2. **COW/CShapes numbering discrepancy** (3 entities): The COW State System and
   CShapes use different numeric codes for small Caribbean islands, producing a
   cascade of off-by-one polygon mismatches.

### 11.2 Detection Method

We compared polity names against their matched CShapes names, flagging entries where
no meaningful word overlap existed between the polity name and the matched polygon
source name (after filtering known colonial→modern name changes).

### 11.3 All Fixes

| File | Change | Entities fixed |
|------|--------|---------------|
| `build_database.py` | Added `iso_collision_exclude` to `get_cow_code()` | 7 entities |
| `build_polygons.py` | Added 15+ entries to `CSHAPES_NAME_MAP` | 13 entities |
| `build_polygons.py` | Added `SKIP_COW_MATCHING` set with guard logic | 9 entities |
| `build_polygons.py` | Extended guard to GADM ISO fallback | 2 entities |

### 11.4 Post-Fix Polygon Count

| Metric | Before fix | After fix |
|--------|-----------|-----------|
| Total polygons matched | 724 | 723 |
| Correctly matched | 711 | 723 |
| Wrong polygon (wrong country/continent) | 13 | 0 |
| Truly unmatched (tiny islands, aggregates) | 9 | 10 |

The net polygon count decreased by 1 because Canton & Enderbury Islands (a tiny
uninhabited Pacific atoll) was previously incorrectly getting Canada's polygon
and is now correctly reported as unmatched.

---

## 12. Summary of Severity

| Entity | Period | Severity | Error magnitude | Root cause | Status |
|--------|--------|----------|-----------------|------------|--------|
| **Polygon matching bugs** | | | | | |
| NOR/PER/CHE/SWE/JAM/CAN/SAR/GER | Various | CRITICAL | Wrong continent | ISO code collision | **FIXED** |
| DMA/LCA/VCT | Caribbean | CRITICAL | Wrong island | COW/CShapes discrepancy | **FIXED** |
| **Historical territory inaccuracies** | | | | | |
| OTT-1800-1912 | Ottoman Empire | MODERATE | OTT=small polygon, TUR=correct | CShapes-Europe matched first for OTT | Known |
| ETH-1800-1889 | Pre-Menelik Ethiopia | CRITICAL | 2-3x too large | Post-expansion polygon back-projected | Known |
| EGY-1800-1899 | Egypt without Sudan | CRITICAL | Missing 60% territory (1820-1882) | Post-Mahdist polygon back-projected | Known |
| ZAN-1800-1890 | Zanzibar islands only | CRITICAL | Missing ~90% territory | Mainland coastal empire not captured | Known |
| CHN-1800-1912 | Qing China | MAJOR | ~10-15% (Outer Mongolia missing) | Qing tributary not in polygon | Known |
| MOR-1800-1904 | Morocco fixed borders | MAJOR | Conceptual — fixed borders anachronistic | Bled al-makhzen/es-siba distinction | Known |
| MAD-1800-1830 | Madagascar whole-island | MODERATE | 25-90% too large (decreasing) | Merina Kingdom was smaller | Known |
| ERI-1800-1889 | Pre-colonial "Eritrea" | MODERATE | Conceptual — entity anachronistic | No "Eritrea" before Italy | Known |
| KHI/KOK/BUK | Central Asian khanates | MODERATE | Polygon source weak; nomadic borders fluid | Need specialized GIS | Known |
| German states | Pre-1871 | MODERATE | Modern Länder ≠ historical states | Territorial fragmentation | Known |
| FWA internal | French West Africa | MODERATE | Pre-1904 boundaries unreliable | Colonial admin boundaries fluid | Known |
| MNG 1911-1921 | Mongolia independence gap | MODERATE | No polygon for 10-year period | CShapes starts Mongolia at 1921 | Known |
| Baltic states | Pre-1940 vs post-1991 | MINOR | ~5% boundary shifts | Petseri/Abrene/Vilnius transfers | Known |
| German Kamerun | Neukamerun 1911-1916 | MINOR | Well-captured by CShapes | | Known |
| Congo Free State | DRC/Congo border | MINOR | ~98% accuracy | Uti possidetis applies well | Known |
| **Missing interwar entities** | | | | | |
| Saar Territory | 1920-1935 | MODERATE | Not in database | League of Nations mandate | Missing |
| Memel Territory | 1920-1923 | MINOR | Not in database | League/French administration | Missing |
