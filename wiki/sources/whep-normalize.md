---
source_slug: whep-normalize
title: "A colleague's normalized IIA/FAO-yearbook country-label list (whep_data_normalize)"
author: WHEP project (in-house normalisation by a colleague)
publisher: Unpublished project working file
year: 2026
license: Project-internal. NOT committed to this repository.
access_date: 2026-09-30
type: dataset
coverage: 14,902 (year or period, label) pairs over 595 distinct labels, 1897-1960, plus multi-year periods (1900-1913, 1909-1913, 1934-1938, 1948-1952 ...)
---

# A colleague's normalized IIA/FAO-yearbook country-label list

## What it is

A two-column working sheet (`whep_data_normalize`, no header): a year or period, and a country label,
**14,902 distinct (year, label) pairs over 595 labels**. It carries no values and no source column.
The labels are a normalized vocabulary over International Institute of Agriculture (IIA) and FAO
yearbook country names:

- a **sovereign prefix** names the territory's ruler in that year: `british burma`, `french dahomey`,
  `japanese karafuto`, `us guam`, `dutch java`, `portuguese kambing`;
- **`country: subunit`** names a part: `british perim: socotra`, `germany: bizone, french`,
  `rhodesia and nyasaland federation: north rhodesia`, `united kingdom: england, wales`;
- **parenthetical qualifiers** mark coverage (`total (excl china, ussr)`, `british india (excl
  burma)`, `french morocco (former)`); `matchlib.norm()` drops them, so each such label shares the
  alias rows of its base label;
- **aggregates and residuals**: `total ...`, `other countries in ...`, regional totals.

Only 143 of the labels coincide (case-insensitively) with a layer-B `country` string, so it is a
separate normalisation of the same kind of yearbook data, and it is onboarded here as a source of its
own: slug `whep-normalize`. The sheet itself is **not committed**; what this repository stores is the
vocabulary -- alias rows, labels and year spans.

## How it is routed

Every alias row is scoped to `source = whep-normalize`, so no other source's routing moves. Rows were
written only for labels where the existing rules (blank-source aliases, name, token-set and spelling
matches) gave a wrong or no answer in some year; the other labels route through those rules and were
checked. Year spans are compressed into ranges that stay inside the target's own span
(`year_end = end_year - 1`), except `back_cast` rows, which end before their target begins. A period
pair (`1934-1938`) resolves as layer-B period rows do: to the polity covering most of its years.

| | pairs | share |
|---|---:|---:|
| resolved by the pre-existing rules (before this change) | 5,632 | 37.8% |
| ... of which to the wrong polity | 70 | |
| **routed after this change** | **12,929** | **86.8%** |
| ... by a new `whep-normalize` alias | 8,326 | |
| ... by a new `back_cast` alias | 53 | |
| ... by the existing rules, checked | 4,550 | |
| not a territory (documented below) | 558 | 3.7% |
| unresolved: no polity is that territory in that year (below) | 1,415 | 9.5% |

The 70 wrong answers the existing rules gave: `austria-hungary: austria` and `: hungary` (22 pairs)
reached the whole Dual Monarchy by token-set matching; `yemen` (20) reached the Yemen YAR+PDRY
aggregate, which would sum in the separately-listed Aden colony and protectorate; `ethiopia` 1936-1940
(6) reached Italian East Africa through the blank-source `Ethiopia` alias, where iia, fao1952 and
mitchell all route to Ethiopia proper; the rest are transition years a successor now takes.

## New polities

Thirty-three territories the list reports on their own had no row. Each was created from a polygon
source already on hand -- GADM 4.1, CShapes 2.0, or an existing row's feature
([wikipedia-whep-normalize-2026-09-30](wikipedia-whep-normalize-2026-09-30.md) for the facts):

- **parts of states**: Scotland (GBR-SCT-1800-2025), England and Wales (GBR-EW-1800-2025), Northern
  Ireland (GBR-NIR-1921-2025), Madeira (PRT-MAD-1800-2025), the Azores (PRT-AZO-1800-2025), mainland
  Portugal (PRT-CON-1800-2025, an aggregate of the districts), Ceuta (ESP-CE-1800-2025), Melilla
  (ESP-ML-1800-2025), the Andaman and Nicobar Islands (IND-AN-1868-2025), Sikkim (IND-SK-1890-2025),
  Tibet within the PRC (CHN-XZ-1951-2025);
- **Crown dependencies and islands**: Jersey (JEY-1800-2025), Guernsey (GGY-1800-2025), the Cocos
  (Keeling) Islands (CCK-1857-2025), Ascension (ASC-1815-2025), Tristan da Cunha (TDC-1816-2025),
  Christmas Island before and after Singapore (CXR-1888-1946, CXR-1958-2025);
- **colonial units**: the Aden Settlement within British India (ADS-1839-1937), Singapore within the
  Straits Settlements (SGP-1824-1946), the Straits Settlements (STS-1826-1946), the Federated and
  Unfederated Malay States (FMS-1909-1946, UMS-1909-1946), Karafuto (KAR-1905-1945), the Free City
  of Danzig (DNZ-1920-1939), and Java, Madura, Sumatra, Bali, Lombok and the Outer Provinces of the
  Dutch East Indies (IDN-JAV/-MAD/-SUM/-BAL/-LOM/-OUT, all 1800-1949);
- **combined reporting units**: Svalbard and Jan Mayen (SJM-1930-2025), Louisiana and Florida
  (USA-FLLA-1845-2025).

IIA's stated areas, which the lexicon could not place before, now reach five of them and agree with
their polygons: the Federated Malay States (polygon/stated 1.003), the Unfederated (0.936), the
Straits Settlements (0.862), Karafuto (0.889) and the Andaman and Nicobar Islands (0.934).

## Not a territory

Totals, regional sums and residual buckets are left unrouted on purpose: a polity code is an
identity, not an aggregation bucket. **558 pairs over 40 labels.**

| label | pairs | years | reason |
|---|---:|---|---|
| `arabian peninsula` | 24 | 1913..1960 | regional aggregate of several sovereign territories |
| `arabian peninsula: other countries` | 7 | 1948-1952..1960 | residual 'other countries/islands' bucket: the complement of listed siblings, not a territory |
| `australian administered territories` | 5 | 1909-1913..1925 | aggregate of Australia's external territories (Papua, New Guinea, Norfolk, Nauru...) taken together |
| `british dependent territories` | 4 | 1938..1948 | aggregate of all British dependent territories |
| `british dependent territories in africa` | 10 | 1934-1938..1954 | aggregate of British dependencies in Africa |
| `british dependent territories in asia` | 10 | 1934-1938..1954 | aggregate of British dependencies in Asia |
| `british dependent territories in oceania` | 8 | 1948-1950..1954 | aggregate of British dependencies in Oceania |
| `british pacific islands: other islands` | 8 | 1911..1937 | residual 'other countries/islands' bucket: the complement of listed siblings, not a territory |
| `british west indies: other islands` | 15 | 1934-1938..1957 | residual 'other countries/islands' bucket: the complement of listed siblings, not a territory |
| `caribbean` | 26 | 1934..1960 | regional aggregate of several sovereign territories |
| `caribbean net` | 5 | 1934-1938..1952 | regional aggregate of several sovereign territories |
| `eastern europe` | 5 | 1934-1938..1954 | regional aggregate of several sovereign territories |
| `latin america` | 26 | 1934..1960 | regional aggregate of several sovereign territories |
| `latin america net` | 5 | 1934-1938..1952 | regional aggregate of several sovereign territories |
| `nam` | 5 | 1934-1938..1954 | unrecognised token 'nam' |
| `north america` | 8 | 1934..1954 | regional aggregate of several sovereign territories |
| `other central american republics` | 7 | 1948-1950..1953 | residual 'other countries/islands' bucket: the complement of listed siblings, not a territory |
| `other countries in africa` | 4 | 1948-1950..1954 | residual 'other countries/islands' bucket: the complement of listed siblings, not a territory |
| `other countries in america: north, central` | 4 | 1948-1950..1954 | residual 'other countries/islands' bucket: the complement of listed siblings, not a territory |
| `other countries in america: south` | 1 | 1952..1952 | residual 'other countries/islands' bucket: the complement of listed siblings, not a territory |
| `other countries in asia (excl china)` | 4 | 1948-1950..1954 | residual 'other countries/islands' bucket: the complement of listed siblings, not a territory |
| `total` | 73 | 1909-1913..1960 | world/regional TOTAL row (sum over reporting countries, with or without the USSR/China/Turkey/Hawaii/Mexico qualifier) |
| `total (excl china)` | 5 | 1925-1929..1933 | world/regional TOTAL row (sum over reporting countries, with or without the USSR/China/Turkey/Hawaii/Mexico qualifier) |
| `total (excl china, incl ussr)` | 5 | 1925-1929..1933 | world/regional TOTAL row (sum over reporting countries, with or without the USSR/China/Turkey/Hawaii/Mexico qualifier) |
| `total (excl china, ussr)` | 22 | 1925-1929..1960 | world/regional TOTAL row (sum over reporting countries, with or without the USSR/China/Turkey/Hawaii/Mexico qualifier) |
| `total (excl hawaii)` | 2 | 1937..1950 | world/regional TOTAL row (sum over reporting countries, with or without the USSR/China/Turkey/Hawaii/Mexico qualifier) |
| `total (excl turkey, ussr)` | 9 | 1909-1913..1948 | world/regional TOTAL row (sum over reporting countries, with or without the USSR/China/Turkey/Hawaii/Mexico qualifier) |
| `total (excl ussr)` | 66 | 1909-1913..1960 | world/regional TOTAL row (sum over reporting countries, with or without the USSR/China/Turkey/Hawaii/Mexico qualifier) |
| `total (excl ussr, incl china)` | 4 | 1948-1952..1957 | world/regional TOTAL row (sum over reporting countries, with or without the USSR/China/Turkey/Hawaii/Mexico qualifier) |
| `total (excl ussr, incl turkey)` | 5 | 1921-1925..1929 | world/regional TOTAL row (sum over reporting countries, with or without the USSR/China/Turkey/Hawaii/Mexico qualifier) |
| `total (incl china, ussr)` | 2 | 1937..1950 | world/regional TOTAL row (sum over reporting countries, with or without the USSR/China/Turkey/Hawaii/Mexico qualifier) |
| `total (incl hawaii)` | 2 | 1937..1950 | world/regional TOTAL row (sum over reporting countries, with or without the USSR/China/Turkey/Hawaii/Mexico qualifier) |
| `total (incl mexico)` | 7 | 1934-1938..1944 | world/regional TOTAL row (sum over reporting countries, with or without the USSR/China/Turkey/Hawaii/Mexico qualifier) |
| `total (incl ussr)` | 51 | 1909-1913..1960 | world/regional TOTAL row (sum over reporting countries, with or without the USSR/China/Turkey/Hawaii/Mexico qualifier) |
| `total net` | 26 | 1921-1925..1952 | world/regional TOTAL row (sum over reporting countries, with or without the USSR/China/Turkey/Hawaii/Mexico qualifier) |
| `total net (excl ussr)` | 23 | 1921-1925..1952 | world/regional TOTAL row (sum over reporting countries, with or without the USSR/China/Turkey/Hawaii/Mexico qualifier) |
| `total net (incl ussr)` | 19 | 1921-1925..1952 | world/regional TOTAL row (sum over reporting countries, with or without the USSR/China/Turkey/Hawaii/Mexico qualifier) |
| `united states: other states` | 30 | 1928-1932..1960 | residual 'other countries/islands' bucket: the complement of listed siblings, not a territory |
| `us dependent territories` | 13 | 1934-1938..1954 | aggregate of US dependencies |
| `west indies federation: other islands` | 3 | 1958..1960 | residual 'other countries/islands' bucket: the complement of listed siblings, not a territory |

## Unresolved territories

**1,415 pairs.** Kinds: `subunit` (a part of a polity that has no row of its own), `era` (a
territory whose row does not reach that year), `composite` (a combination of territories no row is),
`ambiguous` (the label cannot be read with confidence) and `dberror` (a polity row's own years are
wrong).

| label | kind | pairs | years | why unresolved |
|---|---|---:|---|---|
| `french southern reunion` | ambiguous | 8 | 1934-1938..1945 | 'southern Reunion' (IIA 'Reunion (Sud)'): a part of Reunion island or its southern dependencies; no polity either way |
| `rhodesia and nyasaland federation: belgian ruanda urundi` | ambiguous | 4 | 1948-1952..1960 | a Belgian mandate filed under the Rhodesian federation (1948-1952..1960); a normalisation slip -- the territory is Ruanda-Urundi, but a label that names the wrong parent cannot be routed with confidence |
| `aegean economic zone` | ambiguous | 3 | 1930..1932 | 'Aegean economic zone' 1930-1932 has no sovereign prefix; the colleague lists Italy's and Greece's Aegean islands separately ('italy: aegean', 'greece: aegean'), so this is most plausibly Turkey's Aegean agricultural region (Ege bolgesi) of the 1930s regional statistics. No subnational Turkish polity exists, and the reading is not certain enough to route |
| `us karafuto` | ambiguous | 2 | 1931..1932 | a US prefix on Japanese Karafuto (1931-1932): a normalisation slip, and Karafuto has no polity anyway |
| `us korea` | ambiguous | 2 | 1931..1932 | a US prefix on Japanese Korea in 1931-1932: a normalisation slip; routing it to KOR-1800-1945 beside 'japanese korea' would duplicate |
| `us kwantung` | ambiguous | 2 | 1931..1932 | a US prefix on Japanese Kwantung (1931-1932): normalisation slip; no polity |
| `us manchukuo` | ambiguous | 2 | 1931..1932 | a US prefix on Manchukuo (1931-1932): normalisation slip; routing beside 'japanese manchukuo' would duplicate |
| `us taiwan` | ambiguous | 2 | 1931..1932 | a US prefix on Japanese Taiwan (1931-1932): normalisation slip; routing beside 'japanese taiwan' would duplicate |
| `us pescadores` | ambiguous | 1 | 1932..1932 | a US prefix on the Japanese Pescadores (1932): normalisation slip; no polity |
| `ussr: transcaucasia` | composite | 19 | 1921-1925..1940 | Transcaucasia (Georgia + Armenia + Azerbaijan; the Transcaucasian SFSR 1922-1936): no polity; AZE-SSR-1920-1991 is Azerbaijan alone |
| `libya: cyrenaica, tripolitania` | composite | 10 | 1934-1938..1960 | Cyrenaica plus Tripolitania: no polity |
| `spain: mainland, canary islands` | composite | 10 | 1934-1938..1960 | peninsular Spain plus the Canaries (no Balearics): no polity |
| `spanish north africa` | composite | 8 | 1911..1937 | Spanish North Africa (plazas plus zone?) 1911-1937: no polity whose scope is certain |
| `british protected malay states` | composite | 7 | 1911..1925 | the Malay protected states (FMS + UMS) together: no polity |
| `new zealand: cook islands, tokelau` | composite | 4 | 1947-1951..1954 | Cook Islands plus Tokelau: no polity |
| `spain: mainland, balearic islands, canary islands` | composite | 3 | 1945..1954 | Spain excluding the plazas de soberania: no polity (differs from ESP by ~30 km2 but is not stated to include them) |
| `west indies federation` | composite | 3 | 1958..1960 | the West Indies Federation (1958-1962): no polity (BWI-1833-1962 also includes non-member Bahamas etc.) |
| `french antilles` | composite | 2 | 1911..1913 | Guadeloupe plus Martinique together: no polity |
| `china: mainland, pescadores, taiwan` | composite | 1 | 1951..1951 | mainland China plus Taiwan and the Pescadores in 1951: no polity (same gap as fao1952 'China 22 provinces & Taiwan') |
| `indonesia: bali and lombok, other islands` | composite | 1 | 1952..1952 | Bali+Lombok plus the Outer Islands (1952): no polity |
| `libya: cyrenaica, fezzan` | composite | 1 | 1948-1952..1948-1952 | Cyrenaica plus Fezzan: no polity |
| `west indies federation: cayman islands, jamaica` | composite | 1 | 1960..1960 | Jamaica plus the Cayman Islands: no polity |
| `west indies federation: jamaica, turks and caicos islands` | composite | 1 | 1960..1960 | Jamaica plus Turks and Caicos: no polity |
| `british north nigeria` | dberror | 1 | 1913..1913 | 1913: the Northern Nigeria Protectorate lasted until amalgamation on 1 January 1914, but NNI-1904-1913's exclusive end_year stops coverage at 1912 |
| `british south nigeria` | dberror | 1 | 1913..1913 | 1913: the Southern Nigeria Protectorate lasted until 1 January 1914, but SNI-1906-1913's exclusive end_year stops at 1912 |
| `japanese kwantung` | era | 31 | 1909..1939 | Kwantung Leased Territory: no polity |
| `german new guinea` | era | 9 | 1909-1913..1917 | German New Guinea before the 1920 mandate: no polity (the family-extension route to Papua TPAP was wrong) |
| `eritrea and ethiopia federation: eritrea` | era | 7 | 1952..1960 | Eritrea inside the federation (1952-1960): ERI-1889-1952 ends at federation; a row for Eritrea inside Ethiopia was tried and withdrawn, because the ERI and ETH families would both claim 1952-1993 (validate_period_overlaps) and ERI-1889-1952 would still win 1952 |
| `indonesia: java, madura` | era | 7 | 1951..1957 | Java and Madura after 1951: IDN-JVM-1949-1951 ends |
| `indonesia: other islands` | era | 7 | 1951..1957 | Outer Islands after 1951: IDN-OTH-1949-1951 ends |
| `union of south africa: cape province` | era | 7 | 1928-1932..1937 | Cape Province 1910-1994: no polity (CAP-1895-1910 ends at Union) |
| `british weihaiwei` | era | 5 | 1911..1929 | Weihaiwei leased territory (1898-1930): no polity |
| `french indochina: guangzhouwan` | era | 5 | 1913..1937 | Kwangchowan leased territory (1898-1945): no polity |
| `spanish ifni` | era | 5 | 1948-1952..1960 | Ifni: no polity |
| `us pacific islands` | era | 5 | 1934..1946 | the US Pacific islands before the 1947 trusteeship: no polity |
| `british gilbert and ellice islands` | era | 4 | 1909-1913..1915 | Gilbert and Ellice Islands Protectorate 1892-1915: GEI-1916-1976 starts at the Crown colony and no row covers the protectorate |
| `saar basin` | era | 4 | 1957..1960 | the Saar after its 1957 return to Germany: SAA-1947-1957 ends and no row covers the Saarland |
| `state of alawis` | era | 4 | 1926..1929 | Alawite State (1920-1936): no polity |
| `china: manchuria` | era | 3 | 1915..1917 | Manchuria region before 1921 has no row (MAN-1921-1932 starts with CHN-1921-1932) |
| `german kiautschou bay` | era | 3 | 1911..1921 | Kiautschou leased territory: no polity |
| `greece: dodecanese` | era | 3 | 1947..1951 | the Dodecanese inside Greece from 1947: ITAEG-1912-1947 ends and no row covers the islands after |
| `libya` | era | 3 | 1909..1911 | Ottoman Tripolitania before the 1912 Italian row: no polity |
| `bosnia and herzegovina` | era | 2 | 1911..1913 | Bosnia-Herzegovina 1911-1913 (Austro-Hungarian condominium) has no polity |
| `french comoros` | era | 2 | 1934-1938..1937 | the Comoros before 1946 were administered as part of Madagascar: no polity |
| `german mariana islands` | era | 2 | 1911..1913 | German Northern Mariana Islands: no polity |
| `indonesia: bali and lombok` | era | 2 | 1951..1952 | Bali and Lombok after 1951: IDN-BLB-1949-1951 ends |
| `korea north` | era | 2 | 1946..1947 | the Soviet zone of Korea 1945-1947: no polity (KRS-1945-1948 is the US zone) |
| `morocco: tangier` | era | 2 | 1956..1957 | Tangier inside independent Morocco from 1956: no polity |
| `us johnston island` | era | 2 | 1957..1960 | Johnston Atoll: no polity |
| `us midway islands` | era | 2 | 1957..1960 | Midway: no polity |
| `us wake island` | era | 2 | 1957..1960 | Wake Island: no polity |
| `british somaliland` | era | 1 | 1960..1960 | 1960: the protectorate became the State of Somaliland on 26 June and joined the Somali Republic on 1 July; BSS-1884-1960 ends and SOM-1960-2025 is the whole republic, so no row is the ex-protectorate in 1960 |
| `fiume` | era | 1 | 1921..1921 | Free State of Fiume (1920-1924): no polity |
| `french equatorial africa` | era | 1 | 1909..1909 | 1909: the colony of French Congo before AEF's creation in January 1910: no polity |
| `french morocco: tangier` | era | 1 | 1911..1911 | Tangier 1911 (before the 1912 zone): no polity |
| `french tonkin` | era | 1 | 1953..1953 | Tonkin after 1945: VNM-TON-1887-1945 ends and no row covers it |
| `germany: berlin` | era | 1 | 1937..1937 | Greater Berlin before 1938 (created 1920) has no row: BRL-1938-1945 starts 1938 |
| `italy: aegean` | era | 1 | 1947..1947 | 1947: the islands passed to Greece by the 1947 Paris treaty; ITAEG-1912-1947 ends and no row covers them after |
| `memel territory` | era | 1 | 1921..1921 | Memel Territory (1920-1923): no polity |
| `norway: spitsbergen` | era | 1 | 1913..1913 | Spitsbergen before the 1925 Svalbard Treaty came into force (terra nullius): no polity |
| `ryukyu islands` | era | 1 | 1934..1934 | Okinawa prefecture in 1934: RYU-1937-1945 starts 1937 |
| `british nigeria: north` | subunit | 56 | 1914..1960 | Northern Provinces/Region of Nigeria after amalgamation (1914-1960): no polity; NNI-1904-1913 stops at amalgamation |
| `british nigeria: south` | subunit | 56 | 1914..1960 | Southern Provinces of Nigeria after amalgamation: no polity |
| `british north cameroon` | subunit | 46 | 1909-1913..1960 | Northern Cameroons (the part of the British mandate administered with Northern Nigeria): no polity; BCM-1916-1961 is both parts |
| `british south cameroon` | subunit | 46 | 1909-1913..1960 | Southern Cameroons: no polity; BCM-1916-1961 is both parts |
| `spanish fernando po` | subunit | 44 | 1909-1913..1959 | Fernando Po (Bioko) alone: no polity (GNQ-1886-1968 is all Spanish Guinea) |
| `french oceania: makatea` | subunit | 41 | 1909..1951 | Makatea island alone: no polity |
| `british india: princely states` | subunit | 33 | 1909..1939 | the princely states of British India taken together: no polity (only Hyderabad has a row) |
| `british india: british provinces` | subunit | 32 | 1909..1939 | the British (governors') provinces of British India, excluding princely states: no polity |
| `french cochinchina` | subunit | 30 | 1913..1953 | Cochinchina colony: no polity |
| `french annam` | subunit | 29 | 1913..1944 | Annam protectorate: no polity |
| `ocean island` | subunit | 27 | 1909..1951 | Ocean Island (Banaba) alone, ~6 km2: no polity; iia `banaba island` reaches KIR-1800-2025 in layer B through its iso code |
| `el salvador: san salvador` | subunit | 26 | 1909..1937 | San Salvador department: no polity (name route to all El Salvador was wrong) |
| `british perim` | subunit | 25 | 1909-1913..1947 | Perim island (Aden dependency; part of ADC-1937-1967 from 1937): no polity |
| `portuguese kambing` | subunit | 23 | 1909-1913..1940 | Kambing (Atauro) island: no polity |
| `portuguese mozambique: colony` | subunit | 23 | 1909-1913..1938 | the directly-administered part of Mozambique: no polity |
| `portuguese mozambique: mozambique company` | subunit | 22 | 1909-1913..1938 | Mozambique Company territory (Manica and Sofala): no polity |
| `british johor` | subunit | 21 | 1909-1913..1929 | Johor (Unfederated Malay State): no polity |
| `italian libya: cyrenaica` | subunit | 21 | 1913..1937 | Cyrenaica under Italy (before CYR-1943-1949): no polity |
| `british kelantan` | subunit | 20 | 1909-1913..1929 | Kelantan (Unfederated Malay State): no polity |
| `british perlis` | subunit | 20 | 1909-1913..1928 | Perlis (Unfederated Malay State): no polity |
| `italian libya: tripolitania` | subunit | 20 | 1913..1937 | Tripolitania under Italy (before TRP-1943-1951): no polity |
| `british kedah` | subunit | 17 | 1909-1913..1928 | Kedah (Unfederated Malay State): no polity |
| `british straits settlements: malacca` | subunit | 17 | 1909..1924 | Malacca: no polity |
| `british straits settlements: penang` | subunit | 17 | 1909..1924 | Penang: no polity |
| `british terengganu` | subunit | 17 | 1909-1913..1929 | Terengganu (Unfederated Malay State): no polity |
| `british unfederated malay states: terengganu` | subunit | 16 | 1913..1945 | Terengganu: no polity |
| `japanese palau` | subunit | 16 | 1921..1940 | Palau alone under the Japanese mandate: no polity (SSM-1914-1945 is the whole mandate; CAR-1920-1945's polygon is the FSM Carolines only) |
| `japanese palau: angaur` | subunit | 15 | 1915..1932 | Angaur island (phosphate): no polity |
| `libya: cyrenaica` | subunit | 15 | 1914..1960 | Cyrenaica outside 1943-1950 (Italian province / Libyan province): no polity |
| `libya: tripolitania` | subunit | 15 | 1914..1960 | Tripolitania outside the 1943-1950 British administration: no polity |
| `british straits settlements: labuan` | subunit | 14 | 1909..1921 | Labuan: no polity |
| `belgian congo: leopoldville` | subunit | 13 | 1937..1960 | Leopoldville province of the Belgian Congo has no polity (the name route to French Congo COG was wrong) |
| `french dakar` | subunit | 13 | 1925-1929..1944 | Dakar and dependencies: no polity |
| `dutch sumatra: east` | subunit | 11 | 1909..1919 | East Coast of Sumatra residency: no polity |
| `british gozo` | subunit | 10 | 1937..1957 | Gozo is part of Malta (MLT-1800-2025); no polity for the island alone |
| `british nigeria: east` | subunit | 10 | 1947-1951..1960 | Eastern Region/Provinces of Nigeria: no polity |
| `france: alsace` | subunit | 10 | 1909-1913..1933 | Alsace (Bas-Rhin + Haut-Rhin): no polity for the pair |
| `russia: 9 provinces` | subunit | 10 | 1909..1920 | the nine Siberian governments reported by IIA: no polity |
| `us caroline islands` | subunit | 10 | 1946..1960 | Carolines under the US trust: no polity (TTPI-1947-1994 is the whole trust territory) |
| `us mariana islands` | subunit | 10 | 1946..1960 | Northern Marianas under the US trust: no polity |
| `us palau` | subunit | 10 | 1946..1960 | Palau under the US trust: no polity |
| `british newfoundland: labrador` | subunit | 9 | 1911..1947 | Labrador alone: no polity (NFL-1907-1949 is island plus Labrador) |
| `eritrea and ethiopia federation: ethiopia` | subunit | 9 | 1952..1960 | Ethiopia proper (excluding Eritrea) inside the federation 1952-1960: no polity |
| `germany: bizone` | subunit | 9 | 1926-1936..1949 | the US-British Bizone: no polity (WZO-1938-1949 is all three western zones) |
| `japanese mariana islands` | subunit | 9 | 1921..1940 | Northern Marianas under the Japanese mandate: no polity (SSM-1914-1945 is the whole mandate) |
| `russia: other provinces` | subunit | 9 | 1909..1917 | the remaining Asiatic governments: no polity |
| `spanish rio de oro` | subunit | 9 | 1911..1947 | Rio de Oro: no polity (SWA is all Spanish West Africa) |
| `czechoslovakia: bohemia, moravia, silesia` | subunit | 8 | 1934-1938..1945 | the Czech lands inside Czechoslovakia/the Protectorate 1934-1945: CZE-1804-1918 ends 1918 and no later row exists |
| `british nigeria: west` | subunit | 7 | 1947-1951..1959 | Western Region/Provinces of Nigeria: no polity |
| `british unfederated malay states: kedah` | subunit | 7 | 1912..1929 | Kedah: no polity |
| `british unfederated malay states: perlis` | subunit | 7 | 1913..1939 | Perlis: no polity |
| `dutch sint eustatius` | subunit | 7 | 1909-1913..1926 | Sint Eustatius: no polity (part of ANT) |
| `dutch sint maarten` | subunit | 7 | 1909-1913..1926 | Dutch Sint Maarten: no polity (part of ANT) |
| `french morocco: western zone` | subunit | 7 | 1915..1921 | western zone of French Morocco: no polity |
| `german palau: angaur` | subunit | 7 | 1909..1914 | Angaur island (phosphate): no polity |
| `japanese pescadores` | subunit | 7 | 1911..1937 | Pescadores (Penghu): no polity |
| `british socotra` | subunit | 6 | 1911..1933 | Socotra: no polity |
| `germany: french` | subunit | 6 | 1934-1938..1949 | the French occupation zone alone: no polity |
| `libya: fezzan` | subunit | 6 | 1951..1960 | Fezzan as a Libyan province from 1951: no polity |
| `tianjin foreign concessions` | subunit | 6 | 1911..1932 | Tianjin foreign concessions: no polity |
| `british india (excl burma): british provinces` | subunit | 5 | 1932..1936 | the British (governors') provinces of British India, excluding princely states: no polity |
| `british negri sembilan` | subunit | 5 | 1911..1929 | Negri Sembilan (Federated Malay State): no polity |
| `british pahang` | subunit | 5 | 1911..1929 | Pahang (Federated Malay State): no polity |
| `british perak` | subunit | 5 | 1911..1929 | Perak (Federated Malay State): no polity |
| `british selangor` | subunit | 5 | 1911..1929 | Selangor (Federated Malay State): no polity |
| `sheikh said` | subunit | 5 | 1913..1937 | Sheikh Said peninsula: no polity |
| `spain: mainland` | subunit | 5 | 1934-1938..1954 | peninsular Spain alone: no polity |
| `british mauritius: rodrigues` | subunit | 4 | 1937..1957 | Rodrigues island: no polity |
| `british unfederated malay states: kelantan` | subunit | 4 | 1913..1929 | Kelantan: no polity |
| `french amsterdam` | subunit | 4 | 1911..1925 | Amsterdam Island alone: no polity (ATF-1800-2025 is all French sub-Antarctic lands) |
| `french guadeloupe: saint vincent, marie galante` | subunit | 4 | 1934-1938..1941 | dependencies of Guadeloupe (Marie-Galante etc.): no polity |
| `french juan de nova` | subunit | 4 | 1926..1929 | Juan de Nova island: no polity |
| `french kerguelen` | subunit | 4 | 1911..1925 | Kerguelen alone: no polity (ATF is all French sub-Antarctic lands) |
| `french saint paul` | subunit | 4 | 1911..1925 | Saint-Paul island alone: no polity |
| `spanish morocco (former)` | subunit | 4 | 1957..1960 | 1957-1960 '(former)': the former Spanish zone inside independent Morocco has no polity after SMO-1912-1956 |
| `spanish rio muni` | subunit | 4 | 1934-1938..1952 | Rio Muni: no polity |
| `british mauritius: other islands` | subunit | 3 | 1937..1954 | the dependencies of Mauritius (Rodrigues, Agalega, Chagos, St Brandon...) other than the main island: no polity |
| `british perim: socotra` | subunit | 3 | 1913..1937 | Socotra: no polity |
| `french morocco (former)` | subunit | 3 | 1958..1960 | 1958-1960 '(former)': the former French zone inside independent Morocco has no polity after MAR-1911-1958 ends |
| `portuguese mozambique: nyassa company` | subunit | 3 | 1921-1925..1927 | Nyassa Company territory: no polity |
| `british mauritius: other islands (excl rodrigues)` | subunit | 2 | 1937..1957 | the dependencies of Mauritius (Rodrigues, Agalega, Chagos, St Brandon...) other than the main island: no polity |
| `british perim: khuriya muriya` | subunit | 2 | 1937..1947 | Kuria Muria islands: no polity |
| `british unfederated malay states: johor` | subunit | 2 | 1913..1929 | Johor: no polity |
| `dutch new guinea` | subunit | 2 | 1934-1938..1937 | western New Guinea before 1949 was a residency of the Dutch East Indies: no polity (the name route to Australian TNGU was wrong) |
| `germany: berlin east` | subunit | 2 | 1957..1960 | East Berlin: no polity (BRL-1949-1990 is the whole city) |
| `greece: aegean` | subunit | 2 | 1913..1925 | Greek Aegean islands: no polity |
| `british india: kashmir` | subunit | 1 | 1938..1938 | Jammu and Kashmir princely state 1938: no polity before KJM-1947-1972 |
| `british kuria` | subunit | 1 | 1947..1947 | Kuria Muria islands (Aden dependency): no polity |
| `british north cameroon: adamawa, bornu` | subunit | 1 | 1934-1938..1934-1938 | Adamawa and Bornu divisions of the Northern Cameroons: no polity |
| `china: jehol` | subunit | 1 | 1947..1947 | Jehol province: no polity |
| `china: sikang` | subunit | 1 | 1947..1947 | Sikang province: no polity |
| `french morocco: eastern zone` | subunit | 1 | 1916..1916 | eastern zone of French Morocco: no polity |
| `new zealand: campbell islands` | subunit | 1 | 1947..1947 | Campbell Island: no polity |
| `nigeria: lagos` | subunit | 1 | 1960..1960 | Lagos: no polity |
| `palestine: gaza strip` | subunit | 1 | 1960..1960 | Gaza Strip alone: no polity (PSE-1948-2025 is West Bank and Gaza) |
| `phoenix islands` | subunit | 1 | 1960..1960 | Phoenix Islands: no polity |
| `spanish morocco: north` | subunit | 1 | 1954..1954 | northern (Rif) zone: no polity |
| `spanish morocco: south` | subunit | 1 | 1953..1953 | southern zone (Tarfaya strip): no polity |

## Cross-check against layer B

3,247 (label, year) pairs coincide with a layer-B `country` string (case-insensitively, 136 labels).
Before the fix below, 3,220 resolved to the same polity as layer B and 27 did not; after it, 3,221 and 26:

- **fao1952 pre-war columns (24 pairs)**: `bulgaria`, `canada`, `czechoslovakia`, `finland`,
  `germany`, `japan`, `poland`, `romania` in 1934-1938, 1937, 1938 and 1939. fao1952 states those
  columns on post-war boundaries and layer B back-casts them; this list resolves them to the polity of
  the time, as iia's rows for the same labels and years do. The list has no source column, and its
  1934-1938 set demonstrably mixes IIA-type rows (it carries Estonia, Latvia and Lithuania, which FAO
  1952 does not report) with FAO-type ones (`british pakistan`, `germany: west`). Neither side is
  wrong; which one a pair needs depends on a source the sheet does not record.
- **Transition years (2 pairs)**: fao1952 `Libya` 1949 and `Libya: Cyrenaica` 1951 reach the ending
  polity through aliases whose inclusive `year_end` names that year (baselined by
  validate_alias_year_coverage); a new alias may not do that, so here `libya` 1949 goes to the
  successor LBY-1949-1951 and `libya: cyrenaica` 1951 stays unresolved.
- **iia `poland` 1909-1913 (1 pair, 13 layer-B rows) -- layer B was wrong, and is fixed.** It reached
  Congress Poland (POL-1815-1918, 130,180 km2) by its iso code. Its rye area is 5,087,178 ha against
  5,672,154 ha for 1925-1929; Congress Poland would need 39% of its whole area under rye. It is the
  interwar territory stated backwards, and an `iia` `back_cast` alias now sends it to POL-1921-1945.

## Findings about the database

- **NNI-1904-1913 and SNI-1906-1913 end a year early.** Northern and Southern Nigeria lasted until
  amalgamation on 1 January 1914 (both pages say so), but an exclusive `end_year` of 1913 stops their
  coverage at 1912; `british north nigeria` 1913 and `british south nigeria` 1913 resolve to nothing.
- **Layer-B iia `malaysia` 1909-1944 (116 rows) reaches British North Borneo** (BNB-1881-1963)
  through the `MYS` iso family, where colonial rows tie and family order decides. The label is a mix
  of Straits Settlements, Malay States and Borneo raw labels (iia_label_provenance: `mixed`), so no
  single row is right; British Malaya is closer than North Borneo.
- **iia `singapore` routes to all of British Malaya** (GBM-1895-1946) as a sub-territory, while the
  same source's British Malaya rows also route there. Now that SGP-1824-1946 and STS-1826-1946 exist,
  the layer-B label (a mix of `straits settlements` and `straits settlements: singapore` raw labels)
  can be split.
- **Normalisation slips in the list itself**: `us karafuto`, `us korea`, `us kwantung`, `us
  manchukuo`, `us pescadores`, `us taiwan` (1931-1932) put a US prefix on Japanese territories;
  `rhodesia and nyasaland federation: belgian ruanda urundi` files a Belgian mandate under the
  Rhodesian federation; `us virgin islands` 1909-1916 names the Danish West Indies by their later
  sovereign (routed to DWI-1800-1917, as iia does). The US-prefixed Japanese labels are left
  unresolved rather than routed beside their `japanese ...` twins.
- **Territories and eras the database lacks** (the `era` and `subunit` rows above): Kwantung,
  Kiautschou, Weihaiwei, Kwangchowan, Fiume, Memel, the Alawite State, Bosnia-Herzegovina 1908-1918,
  the Cocos Islands, Sikkim, Ifni, the Nigerian regions and the two Cameroons after 1914, Eritrea and
  Ethiopia proper inside the 1952 federation, Annam and Cochinchina, Tonkin after 1945, the Comoros
  before 1946, Okinawa before 1937, Greater Berlin before 1938, Manchuria before 1921, the Saar after
  1957, and the Malay states, Straits settlements and Dutch East Indies islands individually.
