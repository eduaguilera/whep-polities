# Subnational Polygon Extraction

---

## Overview

The cleaning_geography.xlsx Excel file contains 2,948 OCR'd historical region names
from production data (circa 1900-1945). After harmonization and matching, **110 of
these regions are subnational**: they refer to subdivisions of polities in our database
rather than whole polities.

This document describes how we extracted polygon geometries for these subnational
regions, including the quality tier system, sources used, and detailed limitations.

**Results**: 91 of 110 subnational regions received polygon geometries (82.7%).
Combined with 299 direct polity matches, **390 of 409 data-bearing Excel regions
have polygons (95.4%)**.

---

## Quality Tier System

Each subnational polygon is assigned a quality tier indicating how well the
modern/available geometry represents the historical territory.

| Tier | Label               | Count | Description                                    |
|------|---------------------|-------|------------------------------------------------|
| 1    | Historical boundary | 19    | Actual colonial-era boundary from CShapes 2.0   |
| 2    | Good modern proxy   | 50    | Modern boundary that closely matches historical  |
| 3    | Acceptable proxy    | 22    | Approximation with documented caveats            |
| 4    | No good proxy       | 19    | No available geometry; needs historical GIS      |

### Tier 1 — Historical boundary (CShapes 2.0)

These use CShapes 2.0 polygons that represent the actual colonial-era boundaries.
The principle of *uti possidetis juris* (colonial borders become national borders at
independence) means African colonial sub-territories in CShapes directly correspond
to the historical production regions.

**Examples**: French Senegal, French Guinea, French Dahomey (Benin), French Gabon,
French Chad, French Cambodia, French Laos, Northern Nigeria, Southern Nigeria,
Karafuto Prefecture (Southern Sakhalin).

### Tier 2 — Good modern proxy (GADM admin-1/0)

These use modern GADM boundaries where:
- The region is island-based (boundaries inherently stable): Tasmania, Faroe Islands,
  Greenland, Singapore, Labuan, Cook Islands
- The boundaries have been stable for centuries: UK constituent countries, Malaysian
  states (Johor, Kedah, Kelantan, Perlis, Terengganu), Australian states, Alsace
- The region corresponds to a whole modern country (GADM admin-0): Palau, Greenland

### Tier 3 — Acceptable proxy with caveats

These are approximations where the modern boundary doesn't perfectly match the
historical territory but is the best available without dedicated historical GIS.

**Methods used**:
- GADM province groupings (e.g., Dutch East Indies islands → Indonesian provinces)
- CShapes polygon merging (e.g., Upper Senegal and Niger → Mali + Niger + Burkina Faso)
- Country-minus-subregion subtraction (e.g., China excluding Manchuria, Turkey in Asia)

### Tier 4 — No good proxy (19 regions)

These regions have no acceptable modern equivalent. Common reasons:
- Internal administrative divisions with no modern spatial counterpart
  (British India Crown provinces vs Princely states)
- Regions that cross modern boundaries (French Indochina: Tonkin, Annam, Cochinchina)
- Tiny islands or localities (Angaur, Marie-Galante, Juan de Nova, Makatea, Khibiny)
- Continental subdivisions requiring Ural Mountain classification (Russia/USSR in Europe/Asia)
- Historical protectorate zones without standard modern equivalent (French East/West Morocco)

---

## Extraction Methods

### 1. CShapes direct (`cshapes`)
Find the CShapes 2.0 polygon matching a colonial entity name, preferring the
period around 1920 (center of our 1900-1945 data window).

### 2. CShapes merge (`cshapes_merge`)
Union multiple CShapes polygons to reconstruct aggregate territories
(e.g., Transcaucasian SFSR = Georgia + Armenia + Azerbaijan).

### 3. CShapes subtraction (`cshapes_subtract`)
Base CShapes polygon minus other CShapes polygons
(e.g., British India excluding Burma = India - Myanmar).

### 4. GADM admin-0 (`gadm0`)
Modern country-level polygon from GADM 3.6.

### 5. GADM admin-1 (`gadm1` / `gadm1_merge`)
Modern first-level administrative division(s) from GADM 3.6. Single region
or union of multiple regions.

### 6. GADM subtraction (`subtract_gadm1`)
Country-level GADM polygon minus specific admin-1 regions
(e.g., USA minus Alaska/California/Louisiana/Florida).

---

## Detailed Limitations by Region Group

### French West Africa (11 regions, all with polygons)
- **Tier 1** (8 regions): Individual colonies became modern nations at independence.
  CShapes polygons are authoritative. Minor caveat: Upper Volta was dissolved 1932-1947
  (territory split between French Sudan, Côte d'Ivoire, and Niger), then reconstituted.
- **Tier 2-3** (3 regions): Composite territories (Senegal+Sudan, Upper Senegal+Niger)
  created by merging individual colony polygons. The merged boundaries are approximate;
  internal colonial administrative boundaries shifted multiple times between 1895-1958.
- **Dakar**: City-commune, not a territory. GADM admin-1 "Dakar" region is significantly
  larger than the historical municipality.

### French Equatorial Africa (9 regions, all with polygons)
- **Tier 1** (4 regions): Gabon, Middle Congo (Congo-Brazzaville), Oubangui-Chari (CAR),
  Chad. Colonial borders became modern national borders.
- **Tier 2** (5 regions): Merged colony polygons for combined administrative periods.

### French Indochina (5 regions, 2 with polygons)
- **Tier 1**: Cambodia and Laos — CShapes polygons from French protectorate era.
  Boundaries largely stable.
- **Tier 4** (3 regions): Tonkin, Annam, and Cochinchina (the three Vietnamese divisions)
  have NO modern equivalent. The 1954 North/South Vietnam partition roughly follows the
  old Tonkin/Annam boundary, but Annam's southern extent doesn't match any modern
  administrative unit. These would require digitizing French colonial maps.

### British India (5 regions, 1 with polygon)
- **Tier 3**: "British India excluding Burma" — CShapes India minus Myanmar. Gives the
  correct outer boundary but cannot represent the Crown/Princely internal distinction.
- **Tier 4** (4 regions): Crown provinces, Princely states, and South provinces have
  no modern equivalent. The 1947 Partition (India/Pakistan/Bangladesh) and 1956 States
  Reorganisation Act completely restructured administrative boundaries. There were ~584
  Princely states forming an intricate patchwork. Would require the Imperial Gazetteer
  maps or specialized historical GIS datasets.

### Dutch East Indies (13 regions, all with polygons)
- **Tier 2** (9 regions): Island-based divisions (Java, Sumatra) map well to modern
  Indonesian provinces. Islands have inherently stable geographic boundaries.
- **Tier 3** (4 regions): Bali and Lombok approximated by Bali + Nusa Tenggara Barat
  (includes Sumbawa, which wasn't part of the historical "Bali and Lombok" category).
  East Outer Provinces (Groote Oost) approximated by NTT + Sulawesi + Maluku + Papua.
- **Cultivation variants**: "European cultivation", "indigenous cultivation", "native
  cultivations" are data categories, not geographic subdivisions. They share the same
  polygon as the base territory.

### UK Sub-regions (4 regions, all with polygons)
- **Tier 2**: England/Wales boundary stable since Laws in Wales Acts (1535-1542).
  Scotland/England boundary stable since Treaty of York (1237). Northern Ireland
  created 1921 with 6 counties of Ulster; boundary stable since.

### Unfederated Malay States (5 regions, all with polygons)
- **Tier 2**: Johor, Kedah, Kelantan, Perlis, Terengganu. These were never federated
  (unlike the FMS: Perak, Selangor, Negeri Sembilan, Pahang). Their boundaries have
  been stable since the colonial era and map directly to modern Malaysian states.

### British Nigeria (4 regions, all with polygons)
- **Tier 1**: CShapes has separate Northern Nigeria and Southern Nigeria protectorate
  polygons (1899-1913). After 1914 amalgamation, the north/south provincial division
  roughly followed the same boundary (Niger and Benue rivers). British Cameroons
  administered as part of Nigerian provinces until 1961 plebiscite.

### Mozambique Concession Companies (3 regions, all with polygons)
- **Tier 3**: Mozambique Company territory ≈ Manica + Sofala provinces. Niassa Company ≈
  Cabo Delgado + Niassa provinces. Boundaries followed rivers (Save, Zambezi, Lurio)
  which don't precisely align with modern provincial boundaries.

### Italian Libya (2 regions, both with polygons)
- **Tier 3**: Tripolitania and Cyrenaica approximated by groups of modern Libyan
  districts. Libya used the tripartite division (Tripolitania/Cyrenaica/Fezzan)
  officially until 1963. Modern districts are much finer-grained.

### China: Manchuria (2 regions, both with polygons)
- **Tier 3**: Manchuria ≈ Heilongjiang + Jilin + Liaoning (Three Northeastern Provinces).
  Manchukuo (1932-1945) also included parts of Inner Mongolia (Hulunbuir, Hinggan) and
  Hebei (Chengde). "China excluding Manchuria" is the country GADM polygon minus these
  three provinces.

### USSR/Russia Continental Divisions (6 regions, 1 with polygon)
- **Tier 2**: Transcaucasian SFSR = merged Georgia + Armenia + Azerbaijan CShapes.
- **Tier 4** (5 regions): Europe/Asia divisions require classifying federal subjects by
  continent. Several subjects straddle the Ural boundary (Chelyabinsk, Sverdlovsk,
  Orenburg, Bashkortostan). Khibiny is a mining locality (point, not territory).

---

## Files

| File | Description |
|------|-------------|
| `data/geodata/subnational_polygons.gpkg` | 91 subnational polygon geometries (EPSG:4326) |
| `data/analysis/subnational_report.csv` | All 110 regions with tier, source, limitations, geometry flag |
| `R/06_add_subnational.R` | Extraction script with all rules and methods |

---

## Key Research Finding: GADM as Historical Proxy

**Question**: Is GADM a good proxy for historical subnational boundaries?

**Answer**: It depends on the region.

- **Yes, for island-based divisions**: Java, Sumatra, Tasmania, Singapore, etc.
  Islands have inherently stable boundaries.
- **Yes, for long-stable internal borders**: UK constituent countries, Malaysian
  states, Australian states, US states. These boundaries predate our study period.
- **Yes, for African colonial territories** (at country level): The *uti possidetis
  juris* principle means colonial borders became national borders. CShapes (preferred)
  or GADM admin-0 gives the correct boundaries.
- **Partially, for GADM admin-1 groupings**: Dutch East Indies islands, Mozambique
  concession territories, Italian Libya regions. These approximate the historical
  divisions but boundaries don't precisely align.
- **No, for cross-boundary divisions**: Tonkin/Annam/Cochinchina, British India
  Crown/Princely, French Morocco East/West. These historical divisions cut across
  all modern administrative units.
- **No, for continental splits**: Russia/USSR Europe/Asia requires Ural classification.
- **No, for point/small localities**: Khibiny, Angaur, Marie-Galante, Makatea.

Overall, GADM provides useful polygons for **83% of our subnational regions** (91/110),
but each usage must be documented with its specific limitations.
