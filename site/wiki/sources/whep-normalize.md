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
  burma)`, `french morocco (former)`). They are part of the label: since 2026-10-02 the matcher keys
  a source label WITH its qualifier (`matchlib.label_key`), so such a label routes only by a rule
  written for the full label and never by its base label's rules or name (see "Qualified labels"
  below);
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

**1,415 pairs** at onboarding; labels the harmonize audit (2026-10-01) routed are removed from the table below. Kinds: `subunit` (a part of a polity that has no row of its own), `era` (a
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
| `indonesia: bali and lombok, other islands` | composite | 1 | 1952..1952 | Bali+Lombok plus the Outer Islands (1952): no polity |
| `libya: cyrenaica, fezzan` | composite | 1 | 1948-1952..1948-1952 | Cyrenaica plus Fezzan: no polity |
| `west indies federation: cayman islands, jamaica` | composite | 1 | 1960..1960 | Jamaica plus the Cayman Islands: no polity |
| `west indies federation: jamaica, turks and caicos islands` | composite | 1 | 1960..1960 | Jamaica plus Turks and Caicos: no polity |
| `british north nigeria` | dberror | 1 | 1913..1913 | 1913: the Northern Nigeria Protectorate lasted until amalgamation on 1 January 1914, but NNI-1904-1913's exclusive end_year stops coverage at 1912 |
| `british south nigeria` | dberror | 1 | 1913..1913 | 1913: the Southern Nigeria Protectorate lasted until 1 January 1914, but SNI-1906-1913's exclusive end_year stops at 1912 |
| `eritrea and ethiopia federation: eritrea` | era | 7 | 1952..1960 | Eritrea inside the federation (1952-1960): ERI-1889-1952 ends at federation; a row for Eritrea inside Ethiopia was tried and withdrawn, because the ERI and ETH families would both claim 1952-1993 (validate_period_overlaps) and ERI-1889-1952 would still win 1952 |
| `indonesia: java, madura` | era | 7 | 1951..1957 | Java and Madura after 1951: IDN-JVM-1949-1951 ends |
| `indonesia: other islands` | era | 7 | 1951..1957 | Outer Islands after 1951: IDN-OTH-1949-1951 ends |
| `union of south africa: cape province` | era | 7 | 1928-1932..1937 | Cape Province 1910-1994: no polity (CAP-1895-1910 ends at Union) |
| `british weihaiwei` | era | 5 | 1911..1929 | Weihaiwei leased territory (1898-1930): no polity |
| `french indochina: guangzhouwan` | era | 5 | 1913..1937 | Kwangchowan leased territory (1898-1945): no polity |
| `spanish ifni` | era | 5 | 1948-1952..1960 | Ifni: no polity |
| `saar basin` | era | 4 | 1957..1960 | the Saar after its 1957 return to Germany: SAA-1947-1957 ends and no row covers the Saarland |
| `state of alawis` | era | 4 | 1926..1929 | Alawite State (1920-1936): no polity |
| `china: manchuria` | era | 3 | 1915..1917 | Manchuria region before 1921 has no row (MAN-1921-1932 starts with CHN-1921-1932) |
| `german kiautschou bay` | era | 3 | 1911..1921 | Kiautschou leased territory: no polity |
| `greece: dodecanese` | era | 3 | 1947..1951 | the Dodecanese inside Greece from 1947: ITAEG-1912-1947 ends and no row covers the islands after |
| `libya` | era | 3 | 1909..1911 | Ottoman Tripolitania before the 1912 Italian row: no polity |
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
| `italian libya: cyrenaica` | subunit | 21 | 1913..1937 | Cyrenaica under Italy (before CYR-1943-1949): no polity |
| `italian libya: tripolitania` | subunit | 20 | 1913..1937 | Tripolitania under Italy (before TRP-1943-1951): no polity |
| `japanese palau` | subunit | 16 | 1921..1940 | Palau alone under the Japanese mandate: no polity (SSM-1914-1945 is the whole mandate; CAR-1920-1945's polygon is the FSM Carolines only) |
| `japanese palau: angaur` | subunit | 15 | 1915..1932 | Angaur island (phosphate): no polity |
| `libya: cyrenaica` | subunit | 15 | 1914..1960 | Cyrenaica outside 1943-1950 (Italian province / Libyan province): no polity |
| `libya: tripolitania` | subunit | 15 | 1914..1960 | Tripolitania outside the 1943-1950 British administration: no polity |
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
| `british nigeria: west` | subunit | 7 | 1947-1951..1959 | Western Region/Provinces of Nigeria: no polity |
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
| `sheikh said` | subunit | 5 | 1913..1937 | Sheikh Said peninsula: no polity |
| `spain: mainland` | subunit | 5 | 1934-1938..1954 | peninsular Spain alone: no polity |
| `british mauritius: rodrigues` | subunit | 4 | 1937..1957 | Rodrigues island: no polity |
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

## The harmonized dataset (2026-10-01)

The same colleague's harmonized dataset (`whep_data_harmonize`, **794,782 value rows**; columns
hemisphere, continent, polity, commodity, variable, unit, year, value, notes, yearbook, document;
IIA yearbooks 1921-1945 and FAO yearbooks 1949-1961; not committed) is built on this vocabulary.
Its `polity` column has **620 labels over 14,813 (label, year) pairs** (the year axis mixes dated
years and multi-year periods, as above); 113 of the labels are not in the label list, nearly all of
them compound `A; B` labels joining two or more territories. A polity audit of that column (Claude,
2026-10-01) re-checked how this source resolves every pair, and the routing was corrected where the
resolution was wrong or missing. **No layer-B row moves** -- every rule is scoped to
`source = whep-normalize` (stage 01 re-run: 0 of 190,529 matched rows change code).

| | pairs | value rows |
|---|---:|---:|
| routed before | 12,503 (84.4%) | 669,533 (84.2%) |
| **routed after** | **12,910 (87.2%)** | **680,221 (85.6%)** |
| ... newly routed | 407 | 10,688 |
| ... re-routed | 3 | 14 |

### New routes

Compound labels that name the members of a row that already exists (a combined reporting unit, an
aggregate, or a territory whose polygon holds all the members) route to it; the gaps are years the
harmonized dataset carries that the label list did not (`french reunion` 1946 and 1953-1960, `british
kenya` 1920, `french central african republic` 1959).

| label | polity | years | pairs | rows | was |
|---|---|---|---:|---:|---|
| `french lebanon; french syria` | SYL-1920-1944 | 1921-1925..1939 | 23 | 2,341 | unrouted |
| `british nigeria: north; british nigeria: south` | NGA-1914-1960 | 1914..1959 | 54 | 2,014 | unrouted |
| `british malaya federation; british singapore` | MASG-1946-1963 | 1946..1956 | 13 | 1,420 | unrouted |
| `british malaya federation` | MYS-1946-1957 | 1946..1956 | 14 | 579 | unrouted |
| `british singapore; malaya federation` | MASG-1946-1963 | 1957..1960 | 4 | 568 | unrouted |
| `french reunion` | REU-1946-2025 | 1946..1960 | 9 | 563 | unrouted |
| `british north cameroon; british south cameroon` | BCM-1916-1961 | 1909-1913..1960 | 45 | 533 | unrouted |
| `lebanon; syria` | SYL-1944-1953 | 1946..1952 | 9 | 470 | unrouted |
| `vietnam north; vietnam south` | F237-1954-1975 | 1954..1957 | 4 | 291 | unrouted |
| `korea north; korea south` | KORP-1948-1953 | 1947-1951..1952 | 8 | 227 | unrouted |
| `british gold coast; british togoland` | GCT-1919-1956 | 1934-1938..1954 | 12 | 183 | unrouted |
| `british india; british pakistan` | IND-1937-1947 | 1934-1938..1946 | 2 | 180 | unrouted |
| `portuguese kambing; portuguese timor` | TLS-1800-2025 | 1909-1913..1940 | 23 | 152 | unrouted |
| `japanese korea: south` | KRS-1910-1945 | 1934-1938..1939 | 5 | 117 | unrouted |
| `british north cameroon; british south cameroon; french cameroon` | BFCM-1920-1960 | 1909..1959 | 20 | 103 | unrouted |
| `british aden; british perim` | ADS-1839-1937 | 1909-1913..1936 | 21 | 95 | unrouted |
| `british north nigeria; british south nigeria` | NGA-1886-1914 | 1900-1913..1913 | 7 | 85 | unrouted |
| `british north rhodesia; british nyasaland; british south rhodesia` | FRN-1953-1964 | 1934-1938..1952 | 5 | 85 | unrouted |
| `french annam; french cochinchina; french tonkin` | VNM-1887-1954 | 1934-1938..1938 | 5 | 69 | unrouted |
| `french algeria; french morocco; french tunisia` | FNA-1912-1956 | 1934-1938..1954 | 14 | 64 | unrouted |
| `british nigeria: north; british nigeria: south` | NGA-1960-1961 | 1960 | 1 | 55 | unrouted |
| `french cambodia; french laos; french vietnam` | FID-1887-1954 | 1953 | 1 | 47 | unrouted |
| `british nigeria: north; british nigeria: south; british north cameroon; british south cameroon` | NGBC-1916-1960 | 1934-1938..1954 | 13 | 46 | unrouted |
| `us pacific islands` | SSM-1914-1945 | 1934..1937 | 4 | 40 | unrouted |
| `germany: west; saar basin` | WZO-1938-1949 | 1934-1938..1948 | 6 | 36 | unrouted |
| `korea north; korea south` | KOR-1945-1948 | 1946..1947 | 2 | 33 | unrouted |
| `spain: ceuta; spain: melilla` | CEM-1800-2025 | 1937..1960 | 10 | 33 | unrouted |
| `french central african republic` | CAF-1919-1960 | 1959 | 1 | 28 | unrouted |
| `australian papua; papua and new guinea` | PNG-1949-1975 | 1948-1952..1960 | 8 | 23 | unrouted |
| `british gozo; british malta` | MLT-1800-2025 | 1937..1957 | 10 | 22 | unrouted |
| `japanese caroline islands; japanese mariana islands; japanese marshall islands; japanese palau` | SSM-1914-1945 | 1921..1940 | 9 | 18 | unrouted |
| `british kenya` | KEN-1907-1924 | 1920 | 1 | 17 | unrouted |
| `belgian congo; belgian ruanda-urundi` | CODRU-1922-1960 | 1934-1938..1948 | 4 | 16 | unrouted |
| `british eritrea; ethiopia` | ETH-1952-1993 | 1934-1938..1948-1952 | 4 | 16 | unrouted |
| `british aden; british perim` | ADC-1937-1967 | 1937..1939 | 3 | 14 | unrouted |
| `dutch java; dutch madura` | IDN-JVM-1949-1951 | 1948-1950 | 1 | 13 | unrouted |
| `japan; us ryukyu` | JPN-1945-1952 | 1946..1948 | 3 | 12 | unrouted |
| `dutch bali; dutch lombok` | IDN-BLB-1949-1951 | 1948-1950 | 1 | 11 | unrouted |
| `japanese korea: south` | KRS-1945-1948 | 1945 | 1 | 10 | unrouted |
| `china; taiwan` | CHN-1947-1949 | 1947..1948 | 2 | 10 | TWN-1945-2025 |
| `british nigeria; british north cameroon; british south cameroon` | NGBC-1916-1960 | 1934-1939..1947-1951 | 2 | 7 | unrouted |
| `greece; greece: dodecanese` | GRC-1947-2025 | 1948 | 1 | 7 | unrouted |
| `british aden; british khuriya muriya` | ADC-1937-1967 | 1947 | 1 | 6 | unrouted |
| `british aden; british kuria; british perim` | ADC-1937-1967 | 1947 | 1 | 6 | unrouted |
| `ethiopia; italian eritrea; italian somaliland` | AOI-1936-1941 | 1928-1932..1937 | 6 | 6 | unrouted |
| `british malaya; british singapore` | MASG-1946-1963 | 1947..1948 | 2 | 6 | unrouted |
| `panama; us panama canal` | PAN-1903-1979 | 1934-1938..1954 | 5 | 5 | unrouted |
| `japan; japan: ryukyu` | JPN-1895-1945 | 1938 | 1 | 4 | unrouted |
| `china; taiwan` | CHN-1945-1947 | 1946 | 1 | 4 | TWN-1945-2025 |
| `dutch east indies; dutch new guinea` | IDN-1800-1945 | 1934-1938 | 1 | 4 | unrouted |
| `british burma; british india` | IND-1914-1937 | 1926-1936..1931 | 2 | 3 | unrouted |
| `japanese pescadores; japanese taiwan` | TWN-1895-1945 | 1933..1937 | 2 | 2 | unrouted |
| `french syria; lebanon` | SYL-1944-1953 | 1945 | 1 | 1 | unrouted |
| `french dakar; french senegal` | SEN-1886-1960 | 1929 | 1 | 1 | unrouted |
| `us pacific islands` | TTPI-1947-1994 | 1946 | 1 | 1 | unrouted |

**Every route was checked for two labels landing on one polity in one table cell** (same yearbook,
document, commodity, variable, unit, notes and year), the way a consumer collapsing on (polity, item,
unit, year) would average them: 67 such cells before the change, **67 after**. Four candidate routes
failed that check and are not made -- `dutch east indies: other islands; dutch java; dutch madura`,
`us caroline islands; us mariana islands; us marshall islands; us palau`, `spanish fernando po;
spanish rio muni` and the 1937 row of `british aden; british khuriya muriya` (reasons below).

`china; taiwan` used to reach **TWN-1945-2025, Taiwan alone**, through the blank-source `China,
Taiwan` alias, which put the mainland's figures on 36,000 km2. 1946-1948 now go to the China rows
whose polygons hold Taiwan (CHN-1945-1947, CHN-1947-1949; 0.999 of TWN inside each). From 1949 no
row was the mainland plus Taiwan, and an alias cannot route a label to nothing, so the second step
below adds the combined rows CHT-1949-1950 and CHT-1950-2025 for it (and for `china (incl
manchuria); taiwan` 1953, which shares the key).

### More not-a-territory labels

| label | pairs | rows | years | reason |
|---|---:|---:|---|---|
| `caribbean; latin america` | 26 | 4,595 | 1934..1960 | regional aggregate (the Caribbean plus Latin America), like `caribbean` and `latin america` on their own |
| `caribbean net; latin america net` | 5 | 45 | 1934-1938..1952 | regional aggregate (net trade), like `caribbean net` and `latin america net` |
| `british dependent territories in europe` | 4 | 10 | 1938..1948 | aggregate of the British dependencies in Europe |
| `united states; us dependent territories` | 13 | 120 | 1934-1938..1954 | the United States plus all its dependencies: an aggregate, like `us dependent territories` on its own |

### Compound and other labels left unresolved

Kinds as above. `era` rows are years of an otherwise routed label.

| label | kind | pairs | rows | years | why unresolved |
|---|---|---:|---:|---|---|
| `british kenya; british uganda` | composite | 27 | 1,362 | 1921-1925..1954 | Kenya plus Uganda (the customs union's joint reporting): no row is the pair |
| `egypt; syria` | composite | 11 | 388 | 1947..1960 | Egypt plus Syria, 1947-1960: no row is the pair (the United Arab Republic 1958-1961 has no row either) |
| `british federated malay states; british singapore` | composite | 3 | 320 | 1926-1938..1934-1938 | the Federated Malay States plus Singapore: no row |
| `french senegal; french sudan` | composite | 5 | 174 | 1934..1938 | Senegal plus French Sudan: no row |
| `korea north; korea south` | era | 8 | 132 | 1953..1960 | 1953-1960: KORP-1948-1953 ends and no row is the whole peninsula later |
| `french morocco; spanish morocco` | composite | 12 | 109 | 1909-1913..1955 | the French and Spanish zones together (Morocco without Tangier): no row is the pair |
| `bhutan; china: tibet; nepal; sikkim` | composite | 12 | 97 | 1934-1938..1960 | four Himalayan territories under three sovereigns: no row |
| `french chad; french ubangi shari` | composite | 15 | 74 | 1909-1913..1933 | Chad plus Ubangi-Shari: no row is the pair |
| `cambodia; laos; vietnam north; vietnam south` | composite | 2 | 56 | 1954..1955 | the former Indochina, 1954-1955: FID-1887-1954 ends at the Geneva settlement and no row is the four states |
| `french morocco: west` | subunit | 7 | 54 | 1915..1921 | western zone of French Morocco (1915-1921): no row |
| `british brunei; british north borneo; british sarawak` | composite | 13 | 44 | 1934-1938..1954 | British Borneo (Brunei, North Borneo, Sarawak): no row is the three |
| `british nauru; ocean island` | composite | 20 | 36 | 1915..1951 | Nauru plus Ocean Island (the phosphate islands): no row |
| `british india; british pakistan` | era | 1 | 30 | 1947 | 1947: the two dominions from 15 August have no single row |
| `china; japanese taiwan` | composite | 2 | 28 | 1934-1938..1938 | China with Japanese Taiwan: no row |
| `british somaliland; italian somaliland` | composite | 9 | 25 | 1913..1937 | the two Somalilands, 1913-1937: no row before the 1960 union |
| `british guernsey; british isle of man; british jersey` | composite | 10 | 25 | 1932..1960 | the three Crown dependencies: CHI-1800-2025 is the Channel Islands without Man |
| `india; pakistan` | composite | 4 | 23 | 1948..1950 | the two dominions after partition, 1948-1950: no row is both |
| `british christmas island; british singapore` | composite | 9 | 22 | 1934-1938..1951 | Singapore with Christmas Island: SGP-1946-1963 is Singapore alone |
| `french comoros; french madagascar` | composite | 9 | 18 | 1934-1938..1954 | Madagascar with the Comoros: MDG-1882-2025 is the island alone (COM-1946-1975's polygon is not inside it) |
| `dutch east indies: other islands; dutch java; dutch madura` | ambiguous | 9 | 18 | 1922..1944 | names the whole Dutch East Indies, but in the same IIA tables it is a fraction of 'dutch east indies' (coffee 1934-1938: 8,600 t against 123,600 t; cocoa 1922: 921 t against 1,260 t), so it is a sub-category of the colony's figures, not its territory |
| `canada; united states` | composite | 18 | 18 | 1909..1925 | Canada plus the United States: no row |
| `british christmas island; british cocos islands; british singapore` | composite | 3 | 18 | 1951..1954 | Singapore with Christmas and the Cocos Islands: no row |
| `us caroline islands; us mariana islands; us marshall islands; us palau` | ambiguous | 10 | 17 | 1946..1960 | names the whole US trust, but in the same FAO tables it differs from 'us pacific islands' (land area 1960: 10,000 ha against 178,000 ha; phosphate rock 1949: 211,000 t against 135,000 t), so it is not the territory TTPI-1947-1994 holds |
| `british saint helena; british saint helena: ascension; british tristan da cunha` | composite | 2 | 12 | 1946..1958 | St Helena with Ascension and Tristan: SHN-1834-1967 is the island alone (123 km2) |
| `british antigua; british saint kitts and nevis` | composite | 3 | 12 | 1949..1951 | two Leeward Islands presidencies: no row |
| `british jamaica; british turks and caicos islands` | composite | 9 | 11 | 1911..1937 | Jamaica with its Turks and Caicos dependency: JAM-1800-2025 is Jamaica alone |
| `german nauru; ocean island` | composite | 7 | 8 | 1909..1914 | Nauru plus Ocean Island: no row |
| `dutch java; dutch sumatra` | composite | 4 | 8 | 1922..1925 | Java plus Sumatra: no row |
| `british north cameroon; british south cameroon; french cameroon` | era | 1 | 8 | 1960 | 1960: French Cameroun was independent from 1 January and no row is it plus the British Cameroons |
| `japanese korea: north` | subunit | 4 | 7 | 1934-1938..1938 | Korea north of the 38th parallel under Japan: no row (KRS-1910-1945 is the south) |
| `dutch sint eustatius; dutch sint maarten` | composite | 7 | 7 | 1909-1913..1926 | two of the six Dutch Caribbean islands: no row |
| `indonesia: java, madura; indonesia: other islands` | composite | 3 | 6 | 1955..1957 | Java and Madura plus the Outer Islands after 1951 (= Indonesia without Bali and Lombok): no row |
| `french cochinchina; french tonkin` | composite | 6 | 6 | 1925..1937 | two of Vietnam's three ky: no row |
| `british zanzibar; union of south africa` | ambiguous | 3 | 6 | 1949..1951 | Zanzibar and South Africa in one label: not a territory any row can hold; a normalisation slip |
| `british north rhodesia; british south rhodesia` | composite | 5 | 6 | 1911..1929 | the two Rhodesias, 1911-1929: no row |
| `spanish fernando po; spanish rio muni` | composite | 4 | 5 | 1934-1938..1952 | Fernando Po plus Rio Muni: in the same FAO tables 'spanish guinea' reports the whole (cocoa 1934-1938: 12,300 t against 11,700 t), so routing the pair to GNQ-1886-1968 would put two figures on one cell |
| `french sahara` | subunit | 4 | 5 | 1911..1925 | the Southern Territories of Algeria: no row |
| `french chad; french middle congo; french ubangi shari` | composite | 1 | 5 | 1921-1925 | French Equatorial Africa without Gabon: no row |
| `french annam; french tonkin` | composite | 5 | 5 | 1925..1929 | two of Vietnam's three ky: no row |
| `french annam; french cochinchina` | composite | 5 | 5 | 1925..1929 | two of Vietnam's three ky: no row |
| `china; japanese manchukuo` | composite | 1 | 5 | 1934-1938 | China with Manchukuo, 1934-1938: no row (CHN-1932-1945 excludes Manchukuo) |
| `british east africa; british uganda` | composite | 1 | 5 | 1909-1913 | the East Africa Protectorate plus Uganda: no row |
| `french reunion: amsterdam, kerguelen, saint paul` | subunit | 4 | 4 | 1911..1925 | three of the French sub-Antarctic islands: ATF-1800-2025 is all of them with Crozet and the Scattered Islands |
| `french morocco: east` | subunit | 1 | 4 | 1916 | eastern zone of French Morocco (1916): no row |
| `french cameroon; french equatorial africa` | composite | 3 | 4 | 1934-1938..1954 | French Cameroun plus French Equatorial Africa: no row |
| `egypt; french syria` | composite | 1 | 4 | 1937 | Egypt plus Syria, 1937: no row is the pair |
| `german caroline islands; german mariana islands; german marshall islands; german palau` | composite | 2 | 3 | 1911..1913 | German Micronesia: no row is the four groups |
| `french gabon; french middle congo` | composite | 3 | 3 | 1915..1921-1925 | Gabon plus Middle Congo: no row |
| `british jamaica; british saint vincent` | composite | 3 | 3 | 1949..1951 | Jamaica plus Saint Vincent: no row |
| `british jamaica; british saint lucia` | composite | 3 | 3 | 1949..1951 | Jamaica plus Saint Lucia: no row |
| `british aden; british socotra` | composite | 3 | 3 | 1913..1937 | Aden plus Socotra: no row (Socotra is in the Aden Protectorate) |
| `lebanon; syria` | era | 2 | 2 | 1953..1954 | 1953-1954: SYL-1944-1953 ends and no row is the pair later |
| `dutch java; dutch madura; dutch sumatra` | composite | 1 | 2 | 1948 | Java, Madura and Sumatra: no row |
| `dutch east indies; dutch new guinea` | composite | 1 | 2 | 1948-1950 | 1948-1950: from 1949 Indonesia and Netherlands New Guinea are two rows |
| `burma; french cambodia; french laos; french vietnam` | composite | 2 | 2 | 1948-1950..1952 | Burma plus Indochina: no row |
| `british nigeria: lagos` | subunit | 1 | 2 | 1960 | Lagos alone (1960): no row |
| `british cayman islands; british jamaica` | composite | 2 | 2 | 1937..1948-1952 | Jamaica with its Cayman dependency: JAM-1800-2025 is Jamaica alone |
| `british burma; french indochina` | composite | 1 | 2 | 1934-1938 | Burma plus French Indochina: no row |
| `australian cocos islands; british christmas island` | composite | 1 | 2 | 1947 | the Cocos plus Christmas Island: no row |
| `japanese pescadores; us taiwan` | ambiguous | 1 | 1 | 1932 | a US prefix on Japanese Taiwan inside a compound (1932): the same slip as 'us taiwan' |
| `french reunion; rhodesia and nyasaland federation` | ambiguous | 1 | 1 | 1954 | Reunion and the Rhodesian federation in one label: a normalisation slip |
| `french morocco; french tunisia` | composite | 1 | 1 | 1951 | French Morocco plus Tunisia: no row is the pair |
| `british togoland; french togoland` | composite | 1 | 1 | 1921-1925 | the two Togoland mandates, 1921-1925: no row after GTO-1884-1920 |
| `british nigeria: north; british north cameroon` | composite | 1 | 1 | 1934-1938 | the Northern Provinces plus the Northern Cameroons: no row |
| `british montserrat; british saint kitts and nevis; british virgin islands` | composite | 1 | 1 | 1951 | three Leeward Islands presidencies: no row |
| `british aden; british khuriya muriya` | ambiguous | 1 | 1 | 1937 | 1937 only: IIA's 7,500 ha sits in the same table cell as 'british aden; british perim' (20,700 ha), so it is not the colony; 1947 routes to ADC-1937-1967 |

### New polities (2026-10-01, second step)

Twenty-six territories the harmonized dataset reports on their own got a row, each from a polygon
source already used here or fetched by an existing script (GADM 4.1 MYS and COD per-country files,
`FETCH_ONLY` in `scripts/sources/gadm-4.1/fetch.sh`); facts from
[wikipedia-harmonize-audit-2026-10-01](wikipedia-harmonize-audit-2026-10-01.md). Each page states
its polygon status, the km2 reasoning and why it exists.

| polity | labels | years | pairs | rows |
|---|---|---|---:|---:|
| [IDN-JVM-1800-1949](../polities/idn-jvm-1800-1949.md) | `dutch java; dutch madura` | 1909..1948 | 45 | 2,138 |
| [COD-LEO-1933-1962](../polities/cod-leo-1933-1962.md) | `belgian congo: leopoldville` | 1937..1960 | 11 | 577 |
| [KWA-1905-1945](../polities/kwa-1905-1945.md) | `japanese kwantung` | 1909..1939 | 31 | 498 |
| [MYS-PNG-1826-1946](../polities/mys-png-1826-1946.md) | `british penang` | 1909..1924 | 17 | 250 |
| [MYS-MLK-1826-1946](../polities/mys-mlk-1826-1946.md) | `british malacca` | 1909..1924 | 17 | 240 |
| [MYS-LBN-1907-1946](../polities/mys-lbn-1907-1946.md) | `british labuan` | 1909..1921 | 14 | 181 |
| [MYS-JHR-1909-1946](../polities/mys-jhr-1909-1946.md) | `british johor` | 1909-1913..1929 | 21 | 155 |
| [MYS-KTN-1909-1946](../polities/mys-ktn-1909-1946.md) | `british kelantan` | 1909-1913..1929 | 20 | 141 |
| [MYS-KDH-1909-1946](../polities/mys-kdh-1909-1946.md) | `british kedah` | 1909-1913..1929 | 18 | 89 |
| [MYS-TRG-1909-1946](../polities/mys-trg-1909-1946.md) | `british terengganu` | 1909-1913..1945 | 29 | 74 |
| [IDN-BLB-1800-1949](../polities/idn-blb-1800-1949.md) | `dutch bali; dutch lombok` | 1934-1938..1948 | 6 | 70 |
| [NGA-N-1914-1961](../polities/nga-n-1914-1961.md) | `british nigeria: north` | 1932..1960 | 14 | 64 |
| [MYS-PLS-1909-1946](../polities/mys-pls-1909-1946.md) | `british perlis` | 1909-1913..1939 | 26 | 63 |
| [GNG-1900-1920](../polities/gng-1900-1920.md) | `german new guinea` | 1909-1913..1917 | 9 | 36 |
| [NGA-S-1914-1967](../polities/nga-s-1914-1967.md) | `british nigeria: south` | 1932..1939 | 5 | 22 |
| [CHT-1950-2025](../polities/cht-1950-2025.md) | `china (incl manchuria); taiwan`, `china; taiwan` | 1948-1950..1954 | 6 | 21 |
| [CZE-CL-1938-1945](../polities/cze-cl-1938-1945.md) | `czechoslovakia: bohemia, moravia, silesia` | 1939..1944 | 6 | 18 |
| [GEI-1892-1916](../polities/gei-1892-1916.md) | `british gilbert and ellice islands` | 1909-1913..1915 | 4 | 6 |
| [MYS-NSN-1909-1946](../polities/mys-nsn-1909-1946.md) | `british negri sembilan` | 1911..1929 | 5 | 6 |
| [MYS-PHG-1909-1946](../polities/mys-phg-1909-1946.md) | `british pahang` | 1911..1929 | 5 | 6 |
| [MYS-PRK-1909-1946](../polities/mys-prk-1909-1946.md) | `british perak` | 1911..1929 | 5 | 6 |
| [MYS-SGR-1909-1946](../polities/mys-sgr-1909-1946.md) | `british selangor` | 1911..1929 | 5 | 6 |
| [CZE-CL-1945-1993](../polities/cze-cl-1945-1993.md) | `czechoslovakia: bohemia, moravia, silesia` | 1945 | 1 | 3 |
| [CZE-CL-1918-1938](../polities/cze-cl-1918-1938.md) | `czechoslovakia: bohemia, moravia, silesia` | 1934-1938 | 1 | 3 |
| [BIH-1878-1918](../polities/bih-1878-1918.md) | `bosnia and herzegovina` | 1911..1913 | 2 | 3 |
| [CHT-1949-1950](../polities/cht-1949-1950.md) | `china; taiwan` | 1949 | 1 | 2 |

Harmonized dataset after both steps: **13,227 of 14,813 pairs (89.3%) and
684,876 of 794,782 value rows (86.2%) routed**. The label list: 13,313 of
14,902 pairs route. `china; taiwan` 1949-1954 (and `china (incl manchuria); taiwan` 1953) leave Taiwan alone
(TWN-1945-2025) for the combined rows CHT-1949-1950 and CHT-1950-2025. The same-cell check of the
first step: 65 cells after, against 67 before (the two `china; taiwan` cells that shared TWN with
`taiwan`).

Re-edged so that sums count each part once: IDN-JAV-1800-1949 and IDN-MAD-1800-1949 now sit under
IDN-JVM-1800-1949, IDN-BAL-1800-1949 and IDN-LOM-1800-1949 under IDN-BLB-1800-1949.

Not created, and why:

- **German Alsace-Lorraine (1871-1918)**: no row routes there; `france: alsace` is Alsace alone
  (Bas-Rhin and Haut-Rhin), whose departement rows FRA-67/FRA-68 start in 1919 and would have to be
  re-edged under a new Alsace row. Left unrouted.
- **The Northern and Southern Cameroons apart, and the Eastern and Western Regions of Nigeria**: no
  fetched polygon draws the line between them (GADM NGA and CMR are not fetched); the harmonized
  dataset carries the Cameroons only together.
- **Kenya with Uganda** (`british kenya; british uganda`, 1,362 rows) and the other compound labels
  listed above: no row is the pair, and the audit's brief was to route or document them, not to build
  new aggregates for each.
- **Somaliland under British military administration** and **the US Pacific Islands 1945-1947**:
  see the first step (no change of territory; back_cast respectively).

### Conventions the audit questioned, re-checked

- **`british india` 1947 -> IND-1947-1949 stands.** The audit's rule gives a transition year to the
  polity valid for more of its days (British India held 226 of 1947's), but this repository gives a
  handover year to the INCOMING row (`wiki/README.md`, year convention; issue 74), and
  `british pakistan` 1947 goes to PAK-1947-1949 by the same rule. The label's 1947 rows are FAO
  1949-1950 columns, 33 of whose 80 (yearbook, table, variable, year) cells sit beside a separate
  `british pakistan` cell, so they are the Indian Union's territory on either reading. The alias basis
  now says so instead of "the successor convention".
- **`us philippines` 1947-1960 is a normalisation slip**, the class of `us taiwan`/`us karafuto`/`us
  kwantung`: the US prefix outlives independence (4 July 1946). The routing to PHL-1800-2025 stands --
  one row for the islands on both sides of 1946 -- and the alias is split at 1946/1947 so the 1947-1960
  half carries the caveat.
- **Estonia, Latvia and Lithuania switch to their SSR rows in 1940**, the year of the Soviet
  occupation (June) and annexation (August); the handover year belongs to the incoming row, so this
  is the convention applied, not an exception to it.
- **Guadeloupe and Martinique (one row each across the 1946 departmentalisation) against French Guiana
  and Reunion (split at 1946)**, and Greenland (one row across 1953): the year convention is applied
  consistently -- where a row splits, it splits at 1946 -- but whether a status change over the same
  territory makes a row at all is a polity-definition question the database answers both ways. It is
  recorded as a proposal in `wiki/log.md` (`proposal-status-change-splits`), not changed here.
- **Ex-Italian Somaliland under British military administration (1941-1950)** keeps the single row
  ITS-1908-1960. Libya's 1943-1951 rows exist because the country was administered as three
  territories (CYR, TRP, FEZ); Somaliland was administered whole, so it changed administrator, not
  territory, which the polity-definition rule does not split on.
- **`australia (excl victoria)` and `british india (excl burma)` no longer reach the whole
  country.** They used to share their base labels' key, because `matchlib.norm()` dropped
  parentheticals from source labels and the WHEP consumer built the same key. Fixed in both
  repositories at once on 2026-10-02: see "Qualified labels" below.

### Qualified labels (2026-10-02)

The matcher now keys a source label with its bracketed qualifier, and a qualified label may fall
back only to a polity name carrying the same qualifier, so a part or remainder cannot land on its
whole. Measured over all 14,813 pairs, resolved before and after the change with the same rules
(a period pair takes the polity covering most of its years): **37 pairs (972 rows of the harmonized
dataset) changed, all 12 labels carrying a qualifier and nothing else.** New rules re-route the
labels whose qualifier names the same territory as a polity; what is left:

| label | pairs (rows) | before | now |
|---|---:|---|---|
| `british india (excl burma)` 1926-1936 | 5 (19) | IND-1914-1937 (includes Burma, 13.6% of its area) | IND-1937-1947, `back_cast` (differs only by the Aden Settlement, 293 km2) |
| `british india (excl burma)` 1937 | 1 (4) | IND-1937-1947 | IND-1937-1947 |
| `french morocco (former)` 1956-1957 | 2 (365) | MAR-1911-1958 | MAR-1911-1958 |
| `french west africa (former)` 1959 | 1 (22) | AOF-1895-1960 | AOF-1895-1960 |
| `italian somaliland (former)` 1946-1959 | 15 (365) | ITS-1908-1960 | ITS-1908-1960 |
| `ussr (incl dagestan)` 1934, 1939 | 2 (2) | F228-1921-1940 | F228-1921-1940 (Dagestan is in the RSFSR) |
| `china (incl manchuria); taiwan` 1953 | 1 (1) | CHT-1950-2025 | CHT-1950-2025 |
| `australia (excl victoria)` 1934-1938 | 1 (1) | AUS-1901-2025 | unrouted: no polity is Australia without Victoria |
| `russia (excl far east, transcaucasia, turkestan)` 1909-1913 | 1 (22) | F228-1905-1914 | unrouted: no polity is that remainder |
| `ussr (excl far east, transcaucasia, turkestan)` 1922-1925 | 4 (82) | F228-1921-1940 | unrouted: likewise |
| `china (incl jehol, manchuria, sikang, sinkiang, taiwan, tibet)` 1947 | 1 (18) | CHN-1947-1949 | unrouted: CHN-1947-1949 excludes Tibet (TIB-1913-1950); no row is the union |
| `french west africa (former)` 1960, `italian somaliland (former)` 1960, `spanish morocco (former)` 1956 | 3 (71) | the outgoing polity, via the bare label's end-year fallback | unrouted: the polity ends exclusively that year and no alias may claim it (`validate_alias_year_coverage.py`) |

The unrouted ones need a polygon (a remainder or a union) and so a geodata change; they are left
for a follow-up rather than routed to a whole they are not.

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
