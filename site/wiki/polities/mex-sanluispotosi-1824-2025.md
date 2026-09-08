---
polity_code: MEX-SANLUISPOTOSI-1824-2025
polity_name: San Luis Potosí (state of Mexico)
start_year: 1824
end_year: 2025
type: subnational
iso3: MEX
continent: North America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: gadm-4.1-adm1
polygon_feature_id: null
polygon_feature_year: null
polygon_status: unassigned
predecessor: []
successor: []
container:
  - code: MEX-1800-1848
    start_year: 1824
    end_year: 1848
    basis: San Luis Potosí was admitted as a state under the 1824 federal constitution, within the national era this table represents as MEX-1800-1848 (Mexico to the Treaty of Guadalupe Hidalgo)
  - code: MEX-1848-2025
    start_year: 1848
    end_year: 2025
    basis: San Luis Potosí continues as a state through the post-1848 national era, open-ended to the still-current MEX-1848-2025 row
---

# San Luis Potosí (state of Mexico)

## Summary

San Luis Potosí is one of the constituent states of the Mexican federation, established under the 1824 Constitution and never one of the three later territorial conversions (Baja California, Baja California Sur, Quintana Roo) that would justify a later start date under this table's default rule. This entry is `type: subnational` because Mexico held sovereignty over this territory throughout 1824-2025 — the row exists to carry a state-level reporting territory that agricultural and trade statistics are tabulated against separately from national Mexico totals, not to compete with the national MEX chain for sovereignty ranking in the matcher. No existing polity in the table represents San Luis Potosí specifically; only the two successive national-era rows (MEX-1800-1848 and MEX-1848-2025) exist, and routing state-level data to either overstates the reporting territory by roughly the ratio of Mexico's ~1,964,375 km2 national area to the state's own ~60,983 km2.

**Why this entry exists.** Input data: rows labelled with a San Luis Potosí-specific admin name (unit_id MEX-SANLUISPOTOSI) in a Mexican country data extract, with a data span described in the routing decision as 1900-2023, country MEX. Previously matched to: only the national-level MEX-* rows (MEX-1800-1848 or MEX-1848-2025 depending on year), which are national totals for the whole of Mexico and therefore roughly 32 times San Luis Potosí's own area (Mexico ~1,964,375 km2 vs San Luis Potosí ~60,983 km2), since no existing polity in the table represents the state alone. Confirmation of distinctness: San Luis Potosí is one of the original states admitted under the 1824 federal Constitution — it is not listed among the documented departures (Baja California, Baja California Sur, Quintana Roo) that were territories converted to statehood later, so the country's default start rule applies. Its status as a continuously existing, distinct first-order administrative and statistical reporting unit of Mexico (with its own state government, capital at the city of San Luis Potosí, and state-level agricultural/economic statistics tabulated by INEGI and predecessor Mexican statistical agencies) is what confirms this is a genuine reporting territory distinct from the national totals, following the same reasoning already applied to sibling state/department-analogue entries in other countries in this table (e.g. the Colombian department entries).

## Territorial extent

Polygon status: `polygon_status: unassigned`. The routing decision classified this as `registered_source_unfetched`: `gadm-4.1-adm1` is the registered source family this repository already uses for other countries' ADM1-level state/province polygons, but the locally cached `gadm-4.1-adm1.gpkg` is a curated subset of only 81 countries and Mexico has 0 matching features in it — the country is entirely absent locally, not lacking a source in principle. The remedy is to fetch Mexico's ADM1 layer (e.g. `gadm41_MEX_1`) from GADM under the same source registration, not to construct a new polygon or borrow one from elsewhere. `polygon_feature_id` is left null pending that fetch, and no `polygon_area_km2` is recorded since none is measured yet.

Territory description: San Luis Potosí is a state in north-central Mexico. On a modern map it is bounded by Nuevo León and Tamaulipas to the north, Veracruz to the east, Hidalgo and Querétaro to the south, Guanajuato and Zacatecas to the southwest and west, and a short border with Coahuila to the northwest; its capital and largest city is San Luis Potosí. Its present-day area is approximately 60,983 km2 — about 3.1% of Mexico's total national area of roughly 1,964,375 km2. The state's boundary has not been perfectly stable since 1824: portions of the original Intendencia de San Luis Potosí territory were later apportioned in the 19th century to help constitute Nuevo León, and neighboring state boundaries were adjusted more than once during the federal republic's early decades. This entry does not attempt to model those changes; the eventual GADM-derived polygon will represent the present-day boundary only, an approximation flagged in the open questions below.

## Predecessors and successors

No predecessor or successor rows are set. San Luis Potosí does not descend from a distinct prior polity in this table — its colonial-era predecessor, the Intendencia de San Luis Potosí (established 1786 under the Bourbon intendancy system), is administratively continuous with the post-1824 state (same core territory and name, no rupture in the data being routed here), so no predecessor edge is drawn rather than inventing one without a data-backed reason. It has no successor because it remains a current, unabolished Mexican state as of the 2025 end_year used across this table for still-open subnational units.

## Sourced claims

- Mexico's 1824 Federal Constitution (Constitución Federal de los Estados Unidos Mexicanos) established San Luis Potosí as one of the original constituent states of the federation, distinct from the later territorial conversions of Baja California, Baja California Sur, and Quintana Roo.
- San Luis Potosí's approximate present-day area is 60,983 km2 per standard state-level references (e.g. INEGI), versus Mexico's national total of approximately 1,964,375 km2 — the state is about 3.1% of the country, meaning routing its data to the national MEX-* rows overstates its territory roughly 32-fold.

## Decisions

### d-follow-dominant-iso3-start-end-pattern

**Followed the dominant <ISO3>-<SUBUNIT>-<start>-<end> code pattern rather than a bespoke code**

The table's dominant subnational pattern (57 of 66 rows) is <ISO3>-<SUBUNIT>-<start>-<end>, e.g. COL-ANTIOQUIA-1886-2025. San Luis Potosí has no existing subnational MEX precedent (0 rows), so this entry sets the country's own convention. I chose MEX-SANLUISPOTOSI-1824-2025 to match the dominant pattern rather than a bespoke code, because San Luis Potosí is an ordinary constituent state under the 1824 federation, not a historical territory with a name and identity independent of Mexico's administrative structure (unlike ALK or HYD). Using the subunit-in-code form also keeps it consistent with how future MEX state entries (there will likely be many, since MEX has 32 states) should be coded, avoiding a mixed convention within one country.

### d-two-container-eras-not-one

**Split the container into two edges (MEX-1800-1848 and MEX-1848-2025) rather than only citing the modern national row**

The routing decision proposed only container_code MEX-1848-2025 with start_year 1824, but the polity table shows a MEX-1800-1848 row (Mexico to 1848) covering the 1824-1848 span. Citing only MEX-1848-2025 for a 1824-2025 span would leave 1824-1848 uncontained by an edge that starts before its own container's own span, which the containment gate rejects. I added the MEX-1800-1848 edge for 1824-1848 and kept MEX-1848-2025 for 1848-2025, so the two edges together tile the full 1824-2025 span with no gap.

## Open questions

### oq-admission-year-unverified

**Exact admission year of San Luis Potosí to the federation is assumed, not sourced**

The 1824 start_year comes from the country's default rule (any state not listed among the three departures — Baja California, Baja California Sur, Quintana Roo — starts in 1824), not from a primary source confirming San Luis Potosí specifically appears in the 1824 Acta Constitutiva or the 1824 Constitution's list of founding states. Mexican federal history includes states whose territorial definition was still being negotiated through the 1820s-1830s (e.g. disputes with the former Provincias Internas partition), so it is possible San Luis Potosí's boundaries or even its formal state status were not fully settled until slightly later. This should be checked against a primary constitutional history source before treating 1824 as more than a default.

### oq-gadm-boundary-vintage

**GADM adm1 boundary is a present-day snapshot; no historical boundary is modeled for 1824-2025**

Once gadm-4.1-adm1 is fetched for Mexico, the polygon assigned will reflect San Luis Potosí's current boundary, not necessarily its boundary at any specific point across a 201-year span. San Luis Potosí's territory was reduced when parts were used to help form the state of Nuevo León, and in the colonial-to-independence transition the intendancy that preceded it had a somewhat different extent. This entry does not attempt to model those boundary changes, and the eventual polygon assignment should note in its own commit whether pre-20th-century boundary drift materially affects the ~3.1% national-territory-share claim above.

### oq-row-count-and-source-unstated

**Underlying row count and exact data source for the SANLUISPOTOSI unit were not stated in the routing decision**

The routing decision names the unit_id and admin_name but gives no row count and only mentions 'the data extract's 1900-2023 range' in passing, without naming the dataset. Before this page is treated as fully grounded, the ingest pipeline should confirm how many rows and which years of San Luis Potosí-labeled data are being re-routed here from the national MEX-* rows, so the 'why this entry exists' claim can cite a concrete count rather than an inferred one.
