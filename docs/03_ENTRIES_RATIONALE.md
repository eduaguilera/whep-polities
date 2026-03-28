# Polities Database: Entry-by-Entry Rationale

This document explains **why each polity is in the database**, what historical events
define its temporal boundaries, and which sources confirm its existence. Entries are
organized by era and region.

---

## Table of Contents

1. [Pre-Unification European States (pre-1871)](#1-pre-unification-european-states)
2. [Italian Unification (1859-1871)](#2-italian-unification)
3. [German Unification (1864-1871)](#3-german-unification)
4. [Balkans and Ottoman Decline (1878-1922)](#4-balkans-and-ottoman-decline)
5. [Scramble for Africa (1884-1914)](#5-scramble-for-africa)
6. [Asian States and Colonialism (1800-1920)](#6-asian-states-and-colonialism)
7. [WWI Aftermath (1918-1920)](#7-wwi-aftermath)
8. [Interwar Period (1920-1938)](#8-interwar-period)
9. [WWII Territorial Changes (1938-1945)](#9-wwii-territorial-changes)
10. [Decolonization Wave (1945-1975)](#10-decolonization-wave)
11. [Cold War Divisions (1945-1991)](#11-cold-war-divisions)
12. [Post-Cold War (1991-2008)](#12-post-cold-war)
13. [Recent Changes (2008-2025)](#13-recent-changes)
14. [Trade Aggregates](#14-trade-aggregates)
15. [Colonial Entities](#15-colonial-entities)
16. [Dependencies and Territories](#16-dependencies-and-territories)
17. [Statistical Regions](#17-statistical-regions)

---

## 1. Pre-Unification European States

### Italian Pre-Unification States

| Code | Name | Dates | Rationale |
|------|------|-------|-----------|
| SAR-1800-1860 | Sardinia (Kingdom of Sardinia) | 1800-1860 | Core of Italian unification under House of Savoy. Separate trade entity in FT. COW #325. CShapes-Europe has polygon. Annexes Lombardy (1859) then leads unification. |
| TWO-1800-1860 | Two Sicilies | 1800-1860 | Largest Italian pre-unification state (southern Italy + Sicily). COW #329. FT has trade data. Conquered by Garibaldi 1860. Note: duplicate "Kingdom Two sicilies" was merged (FIX applied). |
| PAP-1800-1870 | Papal States | 1800-1870 | Central Italian territory under Papal sovereignty. COW #327. Last to join unified Italy (1870 capture of Rome). FT trade data. |
| TUS-1800-1860 | Tuscany | 1800-1860 | Grand Duchy of Tuscany. COW #337. Plebiscite for Italian union 1860. FT trade data. 22,163 km2. |
| DMO-1800-1860 | Duchy of Modena | 1800-1860 | COW #332. Small duchy (6,031 km2) annexed to Sardinia 1860. FT trade data. |
| DPA-1800-1860 | Duchy of Parma | 1800-1860 | COW #335. Small duchy (6,221 km2) annexed to Sardinia 1860. FT trade data. |
| PIE-1816-1861 | Piedmont | 1816-1861 | Core territory of Kingdom of Sardinia. CShapes-Europe polygon. Overlaps with SAR-1800-1860 (Piedmont IS Sardinia in CShapes terminology). |
| LUC-1816-1847 | Lucca | 1816-1847 | Duchy of Lucca. Absorbed by Tuscany 1847. CShapes-Europe data. |
| MAS-1816-1829 | Massa | 1816-1829 | Duchy of Massa and Carrara. Absorbed by Modena 1829. CShapes-Europe data. |
| NAP-1816-1861 | Kingdom of Naples | 1816-1861 | Mainland portion of Two Sicilies. CShapes-Europe differentiates from full Two Sicilies. |
| ITA-1861-1919 | Italy (to 1919) | 1861-1919 | Unified Italy from proclamation to post-WWI border changes (+Trentino, Trieste, Istria). CShapes polygon. |
| ITA-1919-2025 | Italy | 1919-2025 | Modern Italy. Post-WWI borders (minor WWII changes reversed). CShapes + FAOSTAT. |

### German Pre-Unification States

These are tracked because they appear in CShapes-Europe and COW data, even though
Federico-Tena aggregates German trade under "Germany/Zollverein":

| Code | Name | Dates | Rationale |
|------|------|-------|-----------|
| BAV-1800-1871 | Bavaria | 1800-1871 | Largest German state after Prussia. COW #245. 76,000 km2. CShapes-Europe polygon. GADM DEU L1 "Bayern" as modern proxy. |
| SAX-1800-1871 | Saxony | 1800-1871 | Kingdom of Saxony. COW #269. CShapes-Europe. GADM DEU L1 "Sachsen". |
| HAN-1800-1866 | Hanover | 1800-1866 | Kingdom of Hanover. COW #240. Annexed by Prussia 1866. 38,474 km2. |
| WUR-1800-1871 | Wurttemberg | 1800-1871 | Kingdom of Wurttemberg. COW #271. Joined German Empire 1871. |
| BAD-1800-1871 | Baden | 1800-1871 | Grand Duchy. COW #267. CShapes-Europe polygon. |
| HES-1800-1871 | Hesse | 1800-1871 | Represents Hesse-Darmstadt (Grand Duchy). COW #275. |
| MEK-1800-1871 | Mecklenburg | 1800-1871 | Mecklenburg-Schwerin. COW #280. |
| THU-1800-1871 | Thuringia | 1800-1871 | Aggregate of Thuringian states. Multiple Saxe-* duchies. |
| SHL-1800-1866 | Schleswig-Holstein | 1800-1866 | Fought over in 1864 wars. Annexed by Prussia. Key territorial change for Denmark. |
| BRE-1800-1871 | Bremen (city-state) | 1800-1871 | Free Hanseatic City. Joined German Empire. |
| OLD-1800-1871 | Oldenburg | 1800-1871 | Grand Duchy. Joined German Empire. |
| NAS-1816-1866 | Nassau | 1816-1866 | Duchy. Annexed by Prussia 1866. |
| FFK-1816-1866 | Frankfurt (Free City) | 1816-1866 | Free City. Annexed by Prussia 1866. COW Frankfurt. |
| CRA-1816-1846 | Cracow (Free City) | 1816-1846 | Free city under joint Austrian/Prussian/Russian control. Annexed by Austria 1846. |

**Additional small German states** (all CShapes-Europe, ended 1866-1871):
ANH-1864-1870 (Anhalt), ANB-1816-1864 (Anhalt-Bernburg), ANH-1816-1863 (Anhalt-Dessau),
LIP-1816-1870 (Lippe-Detmold), RSU-1816-1870 (Reuss), SAL-1827-1870 (Saxe-Altenburg),
SCK-1827-1870 (Saxe-Coburg-Gotha), SCS-1816-1826 (Saxe-Coburg-Saalfeld),
SGA-1816-1826 (Saxe-Gotha-Altenberg), SHI-1816-1826 (Saxe-Hildburghausen),
SME-1816-1870 (Saxe-Meiningen), SWM-1816-1870 (Saxe-Weimar), SCL-1816-1870 (Schaumburg-Lippe),
WAL-1816-1870 (Waldeck), WOL-1816-1870 (Wolfenbuttel), HHE-1816-1850 (Hohenzollern-Hechingen),
HSI-1816-1850 (Hohenzollern-Sigmaringen), HOG-1816-1818 (Hohengeroldseck),
HHO-1816-1866 (Hesse-Homburg).

### Other Pre-1871 European Entities

| Code | Name | Dates | Rationale |
|------|------|-------|-----------|
| ION-1815-1864 | Ionian Islands | 1815-1864 | British protectorate, ceded to Greece by Treaty of London 1864. FT trade data. FIX: end year corrected from 1862 to 1864. |
| OTT-1800-1912 | Ottoman Empire | 1800-1912 | Major empire controlling SE Europe, Middle East, North Africa. COW #640. Tracked to 1912 (Balkan Wars begin). FT trade data. WHEP-fix entry. |

---

## 2. Italian Unification (1859-1871)

The unification process is captured by having each pre-unification state end when
absorbed, with unified Italy (ITA-1861-1919) beginning at proclamation.

**Key territorial changes per COW Territorial Change v6:**
- 1859: Lombardy from Austria to Sardinia (23,728 km2)
- 1860: Modena, Parma, Tuscany, Two Sicilies all to Sardinia/Italy
- 1860: Nice/Savoy from Sardinia to France (8,261 km2)
- 1866: Venetia from Austria to Italy (25,397 km2)
- 1870: Rome/Papal States to Italy (11,790 km2)
- 1919: Trentino/South Tyrol, Trieste, Istria from Austria (= ITA-1919-2025)

---

## 3. German Unification (1864-1871)

Germany is tracked at two levels:
- **GER-1800-2025** (aggregate): "Germany/Zollverein" covering all German trade
  throughout the period, used for FT trade data continuity.
- **DEU-period codes**: Specific territorial configurations of the German state.

| Code | Dates | Territory |
|------|-------|-----------|
| DEU-1800-1919 | 1800-1919 | German states -> Empire (1871) -> loss of Alsace-Lorraine (1919) |
| DEU-1919-1920 | 1919-1920 | Weimar Republic initial borders |
| DEU-1920-1938 | 1920-1938 | After plebiscites (Upper Silesia, etc.) |
| DEU-1938-1945 | 1938-1945 | Greater Germany (Anschluss + Sudetenland) |
| F78-1949-1990 | 1949-1990 | West Germany (FRG) |
| F77-1949-1990 | 1949-1990 | East Germany (GDR) |
| DEU-1990-2025 | 1990-2025 | Reunified Germany |

---

## 4. Balkans and Ottoman Decline (1878-1922)

### Balkans

| Code | Name | Dates | Rationale |
|------|------|-------|-----------|
| BGR-1878-1913 | Bulgaria (to 1913) | 1878-1913 | Principality/Kingdom from Congress of Berlin. 96,345 km2 (incl. Eastern Rumelia 1885). |
| BGR-1913-1918 | Bulgaria (1913-1918) | 1913-1918 | After Balkan Wars: gained Thrace, lost S. Dobruja. |
| BGR-1918-1919 | Bulgaria (1918-1919) | 1918-1919 | Post-WWI interim. |
| BGR-1919-1940 | Bulgaria (1919-1940) | 1919-1940 | Treaty of Neuilly borders. Lost Thrace, W. Macedonia. |
| BGR-1940-2025 | Bulgaria | 1940-2025 | Regained S. Dobruja from Romania (1940 Craiova Treaty). |
| SER-1816-1913 | Serbia (to 1913) | 1816-1913 | From autonomy to kingdom. Multiple COW periods. |
| SER-1913-1918 | Serbia (1913-1918) | 1913-1918 | Post-Balkan Wars: expanded into Macedonia, Kosovo. |
| MNE-1878-1913 | Montenegro (to 1913) | 1878-1913 | Recognized at Congress of Berlin. 4,584 km2. |
| MNE-1913-1915 | Montenegro (1913-1915) | 1913-1915 | Expanded after Balkan Wars. Then occupied 1916. |
| ROU-1859-1913 | Romania (to 1913) | 1859-1913 | From union of Moldavia/Wallachia. COW #360. |
| ROU-1913-1918 | Romania (1913-1918) | 1913-1918 | Gained S. Dobruja in Second Balkan War. |
| ROU-1918-1919 | Romania (1918-1919) | 1918-1919 | Post-WWI interim. |
| ROU-1919-1940 | Romania (1919-1940) | 1919-1940 | "Greater Romania" with Transylvania, Bukovina, Bessarabia. |
| ROU-1940-2025 | Romania | 1940-2025 | Lost Bessarabia, N. Bukovina (to USSR), S. Dobruja (to Bulgaria). |
| GRC-1800-1913 | Greece (to 1913) | 1800-1913 | From independence (1830) through early expansions. |
| GRC-1913-1919 | Greece (1913-1919) | 1913-1919 | Major Balkan Wars gains: Crete, Epirus, Macedonia. |
| GRC-1919-2025 | Greece | 1919-2025 | Post-WWI borders (gained W. Thrace 1920, Dodecanese 1947). |
| CRE-1898-1913 | Crete | 1898-1913 | Autonomous Cretan State before Greek union. COW/CShapes data. |
| ALB-1913-2025 | Albania | 1913-2025 | Independent from 1912 (COW: 1913). 28,748 km2. |
| BOS-1800-1908 | Bosnia (to 1908) | 1800-1908 | Ottoman territory, occupied by A-H 1878, annexed 1908. |
| HER-1800-1908 | Herzegovina (to 1908) | 1800-1908 | Ottoman territory, part of Bosnia occupation/annexation. |

### Austria-Hungary

| Code | Name | Dates | Rationale |
|------|------|-------|-----------|
| AUH-1800-1908 | Austria-Hungary (to 1908) | 1800-1908 | Dual monarchy. Bosnia annexation = new polity period. COW #300. FT trade data. |
| AUH-1908-1918 | Austria-Hungary (1908-1918) | 1908-1918 | With annexed Bosnia. Dissolved November 1918. |

### Turkey and Ottoman Successor States

| Code | Name | Dates | Rationale |
|------|------|-------|-----------|
| TUR-1800-1912 | Turkey (to 1912) | 1800-1912 | Ottoman Empire period (same as OTT). |
| TUR-1913-1914 | Turkey (1913-1914) | 1913-1914 | Post-Balkan Wars Ottoman rump. |
| TUR-1914-1920 | Turkey (1914-1920) | 1914-1920 | WWI period to Treaty of Sevres. |
| TUR-1920-2025 | Turkey | 1920-2025 | Republic of Turkey from Treaty of Lausanne. |
| SYR-1918-2025 | Syria and Lebanon | 1918-2025 | French mandate territory aggregate. |
| SYR-1920-1967 | Syrian Arab Republic (1920-1967) | 1920-1967 | French mandate -> independence (1946) -> UAR -> pre-Six Day War. |
| SYR-1946-1967 | Syrian Arab Republic (1946-1967) | 1946-1967 | Post-independence, pre-Golan Heights loss. |
| SYR-1967-2025 | Syrian Arab Republic | 1967-2025 | After Six-Day War (lost Golan Heights). |
| LBN-1944-2025 | Lebanon | 1944-2025 | Independent from French mandate. FAOSTAT/CShapes. |
| IRQ-1921-2025 | Iraq | 1921-2025 | British mandate -> kingdom -> republic. CShapes/FAOSTAT. |
| JOR-1918-2025 | Jordan | 1918-2025 | Transjordan mandate -> independence. |
| JOR-1920-1923 | Jordan (1920-1923) | 1920-1923 | Initial mandate period. |
| PAL-1920-1948 | Palestine (1920-1948) | 1920-1948 | British Mandate Palestine. CShapes mandate polygon. |

---

## 5. Scramble for Africa (1884-1914)

### British Colonial Africa

| Code | Name | Dates | Rationale |
|------|------|-------|-----------|
| BEA-1895-2025 | British East Africa | 1895-2025 | Kenya-Uganda protectorate aggregate. FT trade data. |
| BCA-1914-2025 | British Cameroon | 1914-2025 | Former German Kamerun territory administered by Britain. |
| BSO-1884-2025 | British Somaliland | 1884-2025 | Protectorate. FT data. Became part of Somalia 1960. |
| GOL-1843-2025 | Gold Coast | 1843-2025 | British colony. FT trade data. Became Ghana 1957. |
| BAS-1884-2025 | Basutoland | 1884-2025 | British protectorate. Became Lesotho 1966. |
| BEC-1885-2025 | Bechuanaland Protectorate | 1885-2025 | British protectorate. Became Botswana 1966. |
| BBE-1885-1895 | British Bechuanaland | 1885-1895 | Southern portion, annexed to Cape Colony 1895. |
| NYA-1891-2025 | Nyasaland (Malawi) | 1891-2025 | British protectorate. Became Malawi 1964. |
| GIL-1892-2025 | Gilbert and Ellice Islands | 1892-2025 | Pacific colony. Split into Kiribati/Tuvalu 1979. |
| ZAN-1800-1964 | Zanzibar | 1800-1964 | Sultanate -> British protectorate -> merged with Tanganyika 1964. FT data. |

### French Colonial Africa

| Code | Name | Dates | Rationale |
|------|------|-------|-----------|
| FWA-1895-2025 | French West Africa | 1895-2025 | Federation of 8 territories. FT trade aggregate. |
| FEA-1910-2025 | French Equatorial Africa | 1910-2025 | Federation of 4 territories (Gabon, Congo, CAR, Chad). FT data. |
| FRS-1887-2025 | French Somaliland | 1887-2025 | Became Djibouti 1977. |
| FRS-1884-1977 | French Somalia | 1884-1977 | Alternate tracking for French Somaliland. |

### German Colonial Africa

| Code | Name | Dates | Rationale |
|------|------|-------|-----------|
| GEA-1884-2025 | German East Africa (Tanganyika) | 1884-2025 | Present-day mainland Tanzania. FT data. |
| GWA-1884-1914 | German West Africa | 1884-1914 | German South-West Africa (present Namibia). |
| NAM-1884-2025 | Namibia | 1884-2025 | German SWA -> SA mandate -> independence 1990. |

### Belgian Colonial Africa

| Code | Name | Dates | Rationale |
|------|------|-------|-----------|
| BCG-1885-2025 | Belgian Congo | 1885-2025 | Congo Free State (1885-1908) -> Belgian Congo -> DRC. FT aggregate. |

### South Africa

| Code | Name | Dates | Rationale |
|------|------|-------|-----------|
| ZAF-1828-2025 | South Africa | 1828-2025 | Cape Colony -> Union (1910) -> Republic (1961). |
| CAP-1800-1895 | Cape Colony (to 1895) | 1800-1895 | Pre-expansion Cape Colony. |
| CAP-1895-1910 | Cape Colony (1895-1910) | 1895-1910 | Expanded Cape Colony (incl. British Bechuanaland). |
| NAT-1800-1895 | Natal (to 1895) | 1800-1895 | British colony of Natal. |
| NAT-1895-1910 | Natal (1895-1910) | 1895-1910 | Natal with Zululand annexed. |
| TRA-1856-1910 | Transvaal (to 1910) | 1856-1910 | South African Republic/Transvaal. Joined Union 1910. |
| ORA-1848-1910 | Orange Free State (to 1910) | 1848-1910 | Independent Boer republic. FIX: merged duplicate, start corrected to 1848. |
| ZWE-1890-2025 | Zimbabwe | 1890-2025 | From BSAC administration -> Southern Rhodesia -> Zimbabwe 1980. |

---

## 6. Asian States and Colonialism (1800-1920)

### China

China has 8 meticulous territorial periods reflecting treaty port cessions, Manchuria
changes, and civil war/Communist victory:

| Code | Dates | Event defining period |
|------|-------|----------------------|
| CHN-1800-1895 | 1800-1895 | Qing dynasty, pre-Sino-Japanese War |
| CHN-1895-1912 | 1895-1912 | Post-Shimonoseki (lost Taiwan, Liaodong) |
| CHN-1913-1914 | 1913-1914 | Early Republic |
| CHN-1914-1921 | 1914-1921 | WWI period, Japanese 21 Demands |
| CHN-1921-1945 | 1921-1945 | Warlord era -> WWII (lost Manchuria to Manchukuo) |
| CHN-1945-1947 | 1945-1947 | Post-WWII recovery |
| CHN-1947-1949 | 1947-1949 | Civil war |
| CHN-1949-1950 | 1949-1950 | PRC proclamation, Taiwan separation |

Plus: **CHN-1800-2025** ("China, mainland") as FT/FAOSTAT aggregate.

### Thailand (Siam)

Thailand is one of the best-tracked polities with 5 periods reflecting each French/
British cession:

| Code | Dates | Event |
|------|-------|-------|
| THA-1800-1893 | 1800-1893 | Pre-colonial Siam |
| THA-1893-1904 | 1893-1904 | Lost Laos to France (1893) |
| THA-1904-1907 | 1904-1907 | Further French cessions |
| THA-1907-1909 | 1907-1909 | Lost Battambang to France |
| THA-1909-2025 | 1909-2025 | Lost Malay states to Britain (1909). Modern borders. |

### India

| Code | Dates | Rationale |
|------|-------|-----------|
| IND-1800-1893 | 1800-1893 | British India early period |
| IND-1893-1914 | 1893-1914 | Durand Line drawn (1893) |
| IND-1914-1937 | 1914-1937 | WWI-era changes |
| IND-1937-1947 | 1937-1947 | Burma separated from India (1937) |
| IND-1947-1949 | 1947-1949 | Independence, partition with Pakistan |
| IND-1949-2025 | 1949-2025 | Post-accession of princely states. Modern India. |

### Central Asian Khanates

| Code | Name | Dates | Rationale |
|------|------|-------|-----------|
| BKH-1800-1873 | Badakhshan | 1800-1873 | Central Asian khanate, conquered by Afghanistan. |
| BUK-1800-1920 | Bukhara | 1800-1920 | Emirate of Bukhara. Russian protectorate 1868. Dissolved 1920. FT data. |
| KHI-1800-1873 | Khiva | 1800-1873 | Khanate of Khiva. Russian protectorate 1873. |
| KOK-1800-1876 | Kokand | 1800-1876 | Khanate of Kokand. Conquered by Russia Feb 1876. FIX: end corrected from 1883 to 1876. |
| HRT-1800-1862 | Herat | 1800-1862 | Semi-independent khanate. Conquered by Afghanistan 1863. |

### Other Asian Entries

| Code | Name | Dates | Rationale |
|------|------|-------|-----------|
| OKO-1800-1910 | Korea (to 1910) | 1800-1910 | Korean Empire. Annexed by Japan 1910. FT/COW data. |
| TWN-1896-2025 | Taiwan | 1896-2025 | Japanese colony (1895) -> ROC (1945) -> current status. |
| MNG-1911-2025 | Mongolia | 1911-2025 | Independence from Qing dynasty 1911. |
| JPN-1800-2025 | Japan | 1800-2025 | Single period because colonial acquisitions tracked separately. |
| AFG-1800-1888 | Afghanistan (to 1888) | 1800-1888 | Pre-Durand Line Afghanistan. |
| AFG-1800-1893 | Afghanistan (to 1893) | 1800-1893 | Before Durand Line agreement with British India. |
| AFG-1919-2025 | Afghanistan | 1919-2025 | Full independence from British influence. |
| MAN-1932-1945 | Manchukuo | 1932-1945 | Japanese puppet state in Manchuria. FIX: end corrected from 2025 to 1945. |

---

## 7. WWI Aftermath (1918-1920)

| Code | Name | Dates | Rationale |
|------|------|-------|-----------|
| POL-1918-1919 | Poland (1918-1919) | 1918-1919 | Re-established. Initial borders. |
| POL-1919-1920 | Poland (1919-1920) | 1919-1920 | Versailles borders. |
| POL-1920-1938 | Poland (1920-1938) | 1920-1938 | Post-Riga Treaty (gained eastern territories from Russia). |
| POL-1938-1945 | Poland (1938-1945) | 1938-1945 | Gained Teschen from Czechoslovakia. |
| POL-1945-2025 | Poland | 1945-2025 | Shifted westward (Oder-Neisse line). Modern borders. |
| F51-1918-1938 | Czechoslovakia (1918-1938) | 1918-1938 | Created from Austria-Hungary. 140,968 km2. |
| F51-1938-1945 | Czechoslovakia (1938-1945) | 1938-1945 | After Munich (lost Sudetenland) and Vienna Award (lost south Slovakia). |
| F51-1945-1947 | Czechoslovakia (1945-1947) | 1945-1947 | Restored, lost Subcarpathian Ruthenia to USSR. |
| EST-1918-1940 | Estonia (1918-1940) | 1918-1940 | Independent republic. Annexed by USSR 1940. |
| LVA-1918-1940 | Latvia (1918-1940) | 1918-1940 | Independent republic. Annexed by USSR 1940. |
| LTU-1918-1920 | Lithuania (1918-1920) | 1918-1920 | Initial independence, large borders (154,491 km2). |
| LTU-1920-1940 | Lithuania (1920-1940) | 1920-1940 | After Vilnius loss to Poland (55,600 km2). |
| FIN-1917-1940 | Finland (1917-1940) | 1917-1940 | Independence from Russia. 325,534 km2. |
| FIN-1940-2025 | Finland | 1940-2025 | Lost Karelia to USSR (Winter War). ~290,000 km2. |
| IRL-1921-2025 | Ireland | 1921-2025 | Irish Free State -> Republic. 68,891 km2. |
| F248-1918-1919 | Yugoslavia (1918-1919) | 1918-1919 | Kingdom of Serbs, Croats, Slovenes proclaimed. |
| F248-1919-1920 | Yugoslavia (1919-1920) | 1919-1920 | Treaty borders being defined. |
| F248-1920-1991 | Yugoslavia (1920-1991) | 1920-1991 | Kingdom -> Socialist Federal Republic. |

---

## 8. Interwar Period (1920-1938)

### Hungary (Treaty of Trianon and reversals)

| Code | Dates | Area | Event |
|------|-------|------|-------|
| HUN-1918-1919 | 1918-1919 | ~282,000 km2 | Post-empire, pre-Trianon |
| HUN-1919-1920 | 1919-1920 | Transitional | Soviet Republic period |
| HUN-1920-1938 | 1920-1938 | 91,075 km2 | Trianon borders (lost 67% territory) |
| HUN-1938-1947 | 1938-1947 | ~172,000 km2 | Vienna Awards: regained S. Slovakia, N. Transylvania |
| HUN-1947-2025 | 1947-2025 | 93,030 km2 | Paris Treaty restored Trianon borders |

### Saudi Arabia

| Code | Dates | Rationale |
|------|-------|-----------|
| SAU-1924-1932 | 1924-1932 | Hejaz-Nejd unification process. FT data. |
| SAU-1932-2000 | 1932-2000 | Kingdom proclaimed 1932. CShapes boundary. |
| SAU-2000-2025 | 2000-2025 | Border settlement with Yemen (Treaty of Jeddah 2000). |

---

## 9. WWII Territorial Changes (1938-1945)

| Code | Name | Dates | Rationale |
|------|------|-------|-----------|
| DEU-1938-1945 | Germany (1938-1945) | 1938-1945 | Anschluss (Austria 83,869 km2) + Sudetenland (28,674 km2). |
| F228-1940-1991 | USSR (1940-1991) | 1940-1991 | Expanded: Baltic states, Bessarabia, Karelia, E. Poland. |
| HUN-1938-1947 | Hungary (1938-1947) | 1938-1947 | Vienna Awards expansion. |
| BGR-1940-2025 | Bulgaria (1940-) | 1940-2025 | Regained S. Dobruja. |
| ROU-1940-2025 | Romania (1940-) | 1940-2025 | Lost Bessarabia, N. Bukovina, S. Dobruja. |

---

## 10. Decolonization Wave (1945-1975)

All 96 decolonization events from 1946-2011 are represented. Major entries:

### Asia
- IND-1947-1949, IND-1949-2025: India (independence 1947, princely states accession 1949)
- PAK-1947-1949, PAK-1949-1971, PAK-1971-2025: Pakistan (independence, pre/post-Bangladesh)
- BGD-1971-2025: Bangladesh (split from Pakistan 1971)
- IDN-1945-1949 through IDN-2002-2025: Indonesia (4 territorial periods)
- VNM-1975-2025: Reunified Vietnam
- KHM-1953-2025: Cambodia (independence from France)
- LAO-1954-2025: Laos (independence from France)
- MYS-1957-1963, MYS-1963-1965, MYS-1965-2025: Malaysia formation

### Africa (Year of Africa 1960 and beyond)
- 17+ countries gained independence in 1960 alone (Senegal, Mali, Niger, Chad, CAR,
  Congo, DRC, Gabon, Benin, Burkina Faso, Cote d'Ivoire, Mauritania, Togo, Cameroon,
  Nigeria, Madagascar, Somalia)
- GHA-1957-2025: Ghana (first sub-Saharan independence)
- KEN-1963-2025: Kenya
- TZA-1961-1964, TZA-1964-2025: Tanzania (Tanganyika + Zanzibar union)
- AGO-1816-2025: Angola
- MOZ-1816-2025: Mozambique

### Caribbean/Americas
- JAM-1800-2025: Jamaica
- TTO-1800-2025: Trinidad and Tobago
- GUY-1800-2025: Guyana
- SUR-1975-2025: Suriname

---

## 11. Cold War Divisions (1945-1991)

| Code | Name | Dates | Rationale |
|------|------|-------|-----------|
| F78-1949-1990 | West Germany | 1949-1990 | Federal Republic of Germany. COW #260. |
| F77-1949-1990 | East Germany | 1949-1990 | German Democratic Republic. COW #265. |
| PRK-1948-2025 | North Korea | 1948-2025 | DPRK. COW #731. |
| KOR-1948-2025 | South Korea | 1948-2025 | ROK. COW #732. |
| NVI-1954-1975 | North Vietnam | 1954-1975 | DRV. COW #816. |
| SVI-1954-1975 | South Vietnam | 1954-1975 | Republic of Vietnam. COW #817. |
| F246-1918-1990 | North Yemen | 1918-1990 | Yemen Arab Republic. |
| F247-1967-1990 | South Yemen | 1967-1990 | People's Democratic Republic of Yemen. |

### USSR Periods
| Code | Dates | Event |
|------|-------|-------|
| F228-1800-1886 | 1800-1886 | Russian Empire pre-CShapes |
| F228-1886-1919 | 1886-1919 | Russian Empire (CShapes coverage) |
| F228-1919-1920 | 1919-1920 | Post-WWI border changes |
| F228-1920-1924 | 1920-1924 | Soviet Russia formation period |
| F228-1924-1926 | 1924-1926 | Early USSR |
| F228-1926-1939 | 1926-1939 | Interwar USSR |
| F228-1939-1940 | 1939-1940 | Molotov-Ribbentrop expansion |
| F228-1940-1945 | 1940-1945 | Full WWII expansion (Baltic, Bessarabia, Karelia) |
| F228-1945-1991 | 1945-1991 | Cold War USSR borders |

---

## 12. Post-Cold War (1991-2008)

### USSR Dissolution (1991) -> 15 successor states

All successor states tracked: ARM-1991-2025, AZE-1991-2025, BLR-1991-2025,
EST-1991-2025, GEO-1991-2025, KAZ-1991-2025, KGZ-1991-2025, LTU-1991-2025,
LVA-1991-2025, MDA-1991-2025, RUS-1991-2014, TJK-1991-2025, TKM-1991-2025,
UKR-1991-2014, UZB-1991-2025.

### Yugoslavia Dissolution (1991-2008)

| Code | Name | Dates | Rationale |
|------|------|-------|-----------|
| F248-1991-1992 | Yugoslavia (1991-1992) | 1991-1992 | Rump federation during breakup |
| SVN-1992-2025 | Slovenia | 1992-2025 | Independence 1991/92. 20,256 km2. |
| HRV-1992-2025 | Croatia | 1992-2025 | Independence 1991/92. 56,410 km2. |
| BIH-1992-2025 | Bosnia and Herzegovina | 1992-2025 | Independence 1992. 51,107 km2. |
| MKD-1991-2025 | North Macedonia | 1991-2025 | Independence 1991. |
| SCG-1992-2006 | Serbia and Montenegro | 1992-2006 | Federal Republic -> State Union. |
| SER-2006-2008 | Serbia (2006-2008) | 2006-2008 | Post-Montenegro independence, pre-Kosovo. |
| MNE-2006-2025 | Montenegro | 2006-2025 | Independence referendum 2006. |
| SRB-2008-2025 | Serbia | 2008-2025 | After Kosovo declaration. 77,026 km2. |
| KOS-2008-2025 | Kosovo | 2008-2025 | Declared independence 2008. 104 UN recognitions. 10,887 km2. |

### Czechoslovakia Dissolution (1993)

| Code | Name | Dates | Rationale |
|------|------|-------|-----------|
| CZE-1993-2025 | Czechia | 1993-2025 | Velvet Divorce. 78,866 km2. |
| SVK-1993-2025 | Slovakia | 1993-2025 | Velvet Divorce. 49,035 km2. |

### Other 1990s-2000s

| Code | Name | Dates | Rationale |
|------|------|-------|-----------|
| ERI-1882-2025 | Eritrea | 1882-2025 | Italian colony -> British admin -> Ethiopian federation -> independence 1993. |
| ETH-1993-2025 | Ethiopia | 1993-2025 | Post-Eritrea separation borders. |
| TLS-1800-2025 | Timor-Leste | 1800-2025 | Portuguese colony -> Indonesian annexation 1976 -> independence 2002. |
| YEM-1990-2000 | Yemen (1990-2000) | 1990-2000 | Unified North+South Yemen. |
| YEM-2000-2025 | Yemen | 2000-2025 | Post-Saudi border settlement. |

---

## 13. Recent Changes (2008-2025)

| Code | Name | Dates | Rationale |
|------|------|-------|-----------|
| SSD-2011-2025 | South Sudan | 2011-2025 | Independence referendum 2011. 619,745 km2. |
| SDN-2011-2025 | Sudan | 2011-2025 | Post-South Sudan separation. |
| RUS-2014-2025 | Russia | 2014-2025 | Post-Crimea annexation (+25,777 km2). |
| UKR-2014-2025 | Ukraine | 2014-2025 | Post-Crimea loss (-25,777 km2). |

**Not tracked (by design)**: Post-2022 Russian invasion territorial changes (front lines
fluid, internationally disputed, CShapes has no post-2019 data).

---

## 14. Trade Aggregates

These entities span long periods for trade data continuity, coexisting with period-
specific entries:

| Code | Name | Rationale |
|------|------|-----------|
| GER-1800-2025 | Germany/Zollverein | FT trade aggregate for all German trade 1800-2025. Encompasses pre-unification states, Empire, Weimar, Nazi, divided, reunified. |
| CHN-1800-2025 | China, mainland | FT/FAOSTAT aggregate for Chinese trade data continuity. |
| ETH-1800-2025 | Ethiopia (old) | FT aggregate spanning all Ethiopian territorial configurations. |
| KOR-1800-1945 | Korea (old) | FT aggregate for Korean trade before division. |
| F206-1800-2011 | Sudan (old) | FAOSTAT aggregate for undivided Sudan. |
| NET-1800-2025 | Netherlands (old) | FAOSTAT aggregate including former colonies/territories. |
| LUO-1800-2025 | Luxembourg (old) | FAOSTAT aggregate. Belgium-Luxembourg customs union. |

---

## 15. Colonial Entities

67 colonial entities are tracked. These represent territories administered by colonial
powers that had separate trade data in Federico-Tena or other sources.

### Why colonial entities are in the database:
1. **Trade data exists**: FT records separate trade for British India, French West Africa, etc.
2. **Territory is distinct**: Colonial boundaries differ from modern successor states.
3. **Temporal tracking**: Colonial period start/end dates differ from modern states.

### Polygon source for colonial entities:
- **CShapes 2.0 (dependencies=TRUE)**: Primary source for colonial polygons 1886-2019.
  Status codes: 2=colony, 3=protectorate, 4=leased, 5=occupied.
- **GADM modern borders**: Approximation via uti possidetis principle (colonial borders
  became modern borders at independence in most cases).

---

## 16. Dependencies and Territories

60 dependency entries track non-sovereign territories with distinct identities:
- Overseas territories (Bermuda, Guam, etc.)
- Crown dependencies (Isle of Man, Jersey, Guernsey)
- Autonomous regions (Greenland, Faroe Islands)
- Associated states (Cook Islands, Niue)
- Special administrative regions (Hong Kong, Macao)

### Why dependencies are in the database:
1. **FAOSTAT tracks them separately**: FAO reports data for many dependencies individually.
2. **Distinct trade patterns**: Many have their own customs/trade regimes.
3. **ISO codes exist**: Most have their own ISO 3166-1 alpha-3 codes.

---

## 17. Statistical Regions

146 region entries from FAOSTAT/UN M49 statistical classifications:

### Categories:
- **Geographic regions**: Africa, Asia, Europe, Americas, Oceania and sub-regions
- **Economic groupings**: OECD, EU, LDCs, SIDS, income groups
- **FAO-specific**: Fishing areas, food security groups
- **Cross-regional**: "Latin America and the Caribbean", "Sub-Saharan Africa", etc.

### Why regions are in the database:
FAOSTAT publishes aggregate trade data for these regions. They enable analysis at
regional levels without requiring per-country data assembly.

**Regions do not have polygon geometry.** They are statistical aggregates, not
geographic entities.
