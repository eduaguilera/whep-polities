---
polity_code: MEX-HIDALGO-1869-2025
polity_name: Hidalgo
start_year: 1869
end_year: 2025
type: subnational
iso3: MEX
continent: North America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: gadm-4.1-adm1
polygon_feature_id: MEX.13_1
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: MEX-1848-2025
    start_year: 1869
    end_year: 2025
    basis: Hidalgo has been one of the federal entities of the United Mexican States since its creation in 1869, throughout the entire span of the modern Mexican federation container row MEX-1848-2025.
---

# Hidalgo

## Summary

Hidalgo is one of the 32 federal entities (states) of the United Mexican States, located in central Mexico immediately north and northeast of Mexico City, bordering Mexico State, Queretaro, San Luis Potosi, Veracruz, Puebla and Tlaxcala. It was created by presidential decree in January 1869, split off from the State of Mexico -- one of several mid-19th-century subdivisions of that oversized original federation state, alongside Morelos (1869) and Guerrero (1849). This entry is typed `subnational` because Hidalgo has never held sovereignty of its own: it is, and has always been, a constituent state of the Mexican federation, first under the 1857 constitution's federal structure and continuously since. The row exists to carry statistical or administrative data reported specifically for Hidalgo state rather than for Mexico as a whole or for the State of Mexico from which it split, and its span (1869-2025, end exclusive) reflects the state's actual creation date rather than the 1824 founding of the Mexican federation, since asserting Hidalgo statehood back to 1824 would misrepresent nineteen-plus years during which the territory was part of the State of Mexico.

**Why this entry exists.** Input data: the routing decision for unit_id MEX-HIDALGO (admin_name "Hidalgo", country Mexico) identifies Hidalgo as a genuine Mexican federal state (admin-1 unit) present in the source's administrative unit list, though the specific row count and originating dataset are not given in the decision payload beyond the unit identifier itself -- that count should be confirmed against the ingest pipeline's staging table before this entry is finalized. Previously matched to: nothing specific -- only the national MEX rows (MEX-1800-1848 and MEX-1848-2025) existed in the polity table prior to this decision, so any Hidalgo-labelled data was either unmatched or folded into the national Mexico total, which is wrong because it discards the sub-national reporting granularity the source data actually carries and conflates Hidalgo's ~20,800 km2 with the full ~1.96 million km2 of Mexico. What confirms distinctness: Hidalgo is one of the 32 constitutionally enumerated federal entities of the United Mexican States under Article 43 of the Mexican Constitution, with its own state government, congress, and INEGI-published statistics reported separately from both the national total and its parent State of Mexico -- the same administrative-unit standard applied to the 57 other <ISO3>-<SUBUNIT> subnational rows already in this table (e.g. the Spanish provinces, Colombian departments).

## Territorial extent

**Polygon status:** Not yet assigned. No polygon available in the GeoPackage for this period. No registered, locally-present source carries a Mexican state-level (admin-1) boundary layer: `gadm-4.1-adm1` is registered and present locally but is a curated subset covering 81 other countries and structurally excludes Mexico (zero matching rows), and `gadm-3.6`, which would carry a global admin-1 layer including Mexico, is not present locally. No union or difference of already-registered, locally-present features can construct a Hidalgo polygon either, since no Mexican subnational polygon exists in any locally-present registered source to combine. `polygon_source` is therefore `none` and `polygon_status` is `unassigned`, per the harness's rule that `new_source_needed` routes must not name an unregistered slug. The candidate fix -- registering INEGI's Marco Geoestadistico Nacional or the full global GADM admin-1 layer -- is recorded as an open question rather than declared here.

**Territory description:** Hidalgo state covers approximately 20,800 km2 of central Mexico (INEGI's official figure is 20,813 km2), making it one of the smaller Mexican states by area (roughly the size of El Salvador). Its terrain spans the eastern edge of the Mesa Central plateau, the Sierra Madre Oriental foothills, and the Huasteca lowlands toward Veracruz. The state capital is Pachuca de Soto. A reader can locate it on a modern map as the wedge of territory directly north of Mexico City and Mexico State, south of the Sierra Madre Oriental range shared with San Luis Potosi and Puebla's northern sierra. Its boundaries have been essentially stable since the 1869 creation decree, with only minor municipal-level adjustments since, which is why a modern INEGI or GADM admin-1 boundary -- once obtained -- would be a reasonably faithful proxy for the entire 1869-2025 span, an approximation that should be stated explicitly if such a source is adopted later.

## Predecessors and successors

No predecessor entry exists: Hidalgo was carved out of the State of Mexico by decree in January 1869 rather than splitting from any polity already represented as its own row in this table, so predecessor is left empty pending confirmation of what, if anything, reported data for the pre-1869 military district (see open question oq-1862-military-district-precursor). No successor: Hidalgo remains a current, unchanged federal entity of Mexico through 2025, the exclusive end_year matching the container row MEX-1848-2025's own end_year, so successor is left empty rather than pointing at a placeholder future entry.

## Sourced claims

- Hidalgo was created as a state of the Mexican federation by presidential decree on 16 January 1869, split off from the territory of the State of Mexico -- a claim from general historical knowledge of Mexican federal administrative history, flagged in the routing decision as not yet corroborated against a source file in this repository and repeated here as open question oq-1862-military-district-precursor.
- INEGI (Instituto Nacional de Estadistica y Geografia) states Hidalgo's official land area as 20,813 km2 in its Marco Geoestadistico Nacional and state quick-facts publications -- the authoritative modern figure for the state, distinct from and not sourced from the missing polygon geometry this entry currently lacks.

## Decisions

### d-code-follows-dominant-pattern

**Code follows the dominant <ISO3>-<SUBUNIT>-<start>-<end> pattern, not a bespoke name**

Chose MEX-HIDALGO-1869-2025 over a bespoke code like the three precedent exceptions (ALK, HYD, RYU). Hidalgo is an ordinary Mexican federal state, structurally identical to the other admin-1 subnational rows in this table (Spanish provinces ESP-AS-..., Colombian departments COL-CAU-...), not a historical territory with its own name distinct from its administrative role -- it has never been anything other than a Mexican state. The bespoke pattern in the precedent table is reserved for entities like Alaska-as-a-territory-before-statehood or Hyderabad, whose identity and borders predate or diverge from their eventual administrative container. Hidalgo has no such prior identity: it was created in 1869 specifically as a federal state and named for Miguel Hidalgo, so the dominant ISO3-SUBUNIT pattern is the correct one, following MEX's own lack of existing subnational precedent by falling back on the 57-row majority pattern used across other countries in the table.

## Open questions

### oq-no-polygon-source-registered

**No registered, locally-present source can supply a Hidalgo state polygon**

gadm-4.1-adm1 is registered and present locally, but the local file is a curated 81-country subset that structurally excludes Mexico entirely (0 matching rows for any MEX admin-1 unit), so it cannot be fetched further to fill this gap -- the exclusion is by design, not by missing coverage. gadm-3.6 would carry a global ADM1 layer including Mexico but is not present locally in this repo. The best real candidate is INEGI's Marco Geoestadistico Nacional, Mexico's own national statistical/geographic institute's authoritative state-boundary shapefiles, but it is not currently registered in scripts/sources.yaml and its licence terms have not been checked. Until either the full global GADM adm1 layer or an INEGI source is registered and fetched, polygon_status stays unassigned and polygon_area_km2 is left null rather than approximated from a neighbouring state or a national total divided by area share.

### oq-1862-military-district-precursor

**Whether an 1862-1869 military-district precursor should be a separate predecessor entry**

Hidalgo existed as a military district / territory carved from the State of Mexico from 1862, several years before the 1869 decree that granted full federal statehood. This entry starts at 1869 on the assumption that statistical and administrative data before that date, if any exists, was still reported under the State of Mexico rather than separately for the district -- but that assumption has not been verified against any source file in this repository (the routing decision itself flags the 1869 date as coming from general knowledge, not a corroborated reference). If a source is later found reporting data for the pre-1869 military district specifically, a predecessor row (e.g. MEX-HIDALGO-DIST-1862-1869) may be needed, and this entry's predecessor field would then need to be populated rather than left empty.
