---
polity_code: MEX-JALISCO-1824-2025
polity_name: Jalisco
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
    basis: Jalisco was constituted as a free and sovereign state of the federation by the 1824 Constitution of the United Mexican States and remained one of the constituent states of Mexico through the country's early national period, which the polity table spans as MEX-1800-1848
  - code: MEX-1848-2025
    start_year: 1848
    end_year: 2025
    basis: Jalisco has continued as one of Mexico's 31 states without interruption from the post-1848 national era to the present, the span the polity table carries as MEX-1848-2025
---

# Jalisco

## Summary

Jalisco is one of the 31 states of the United Mexican States, located in west-central Mexico on the Pacific coast, with Guadalajara as its capital. It was created as a state of the federation by the Constitution of 1824, out of the former Nueva Galicia intendancy of New Spain, and is not one of the three federal territories (Baja California, Baja California Sur, Quintana Roo) whose statehood came decades later by conversion from territory status. This entry is `type: subnational` rather than `national`: Mexico's sovereignty is carried by the MEX national chain (MEX-1800-1848, MEX-1848-2025), and Jalisco exists here purely as a sub-national reporting and administrative unit whose boundaries and statistics differ from the national totals. The span 1824-2025 reflects Jalisco's full life as a constituent state: it starts at the 1824 Constitution rather than at the first year data happens to be available (1900 in the input dataset), because the state existed and was administratively distinct for three-quarters of a century before any of the routed data begins, and a polity's start year should reflect institutional origin, not first observation.

**Why this entry exists.** The routing input identifies unit_id MEX-JALISCO, admin_name "Jalisco", country Mexico, with source data beginning around 1900 (per the routing agent's data window) that had previously been folded into the national Mexico rows (MEX-1800-1848 / MEX-1848-2025) for lack of any Jalisco-specific polity. That routing is wrong because Jalisco is a real, persistent administrative unit with its own boundaries, population, and (for many series) its own reported statistics distinct from national Mexican totals -- collapsing it into the national row silently mixes a sub-national reporting geography into a national one. Jalisco's distinctness as an administrative and statistical unit is confirmed by its continuous existence as a first-order constituent state of the Mexican federation since 1824 (one of the original states named in the 1824 Constitution, not one of the later territory-to-state conversions), by its status today as one of Mexico's 31 states with its own state government, congress, and INEGI-published state-level statistics, and by the fact that GADM digitizes Jalisco as a distinct admin-1 feature (GID_1 codes such as MEX.14_1) precisely because it is a real administrative boundary, not an artifact of the data source.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is attached in this entry (`polygon_status: unassigned`), but the source is registered: `polygon_source: gadm-4.1-adm1`. GADM 4.1 does digitize Jalisco globally (GID_1 codes such as `MEX.14_1`), but the `gadm-4.1-adm1` file currently staged in this repository's geodata is a curated subset covering only 81 countries, and Mexico is entirely absent from that subset (0 features). This is a fetch gap, not a source-availability gap: the correct source exists and is registered, it simply has not been extended to include Mexico yet. Until that fetch happens, `polygon_feature_id` stays null and no area figure is attached to this entry -- there is no `polygon_area_km2` measurement to report here, and none should be inferred from other Mexican states' proxies.

**Territory description:** Jalisco is a state in west-central Mexico on the Pacific coast, bordered by Nayarit, Zacatecas, Aguascalientes, Guanajuato, Michoacán, Colima, and the Pacific Ocean. Its capital is Guadalajara, Mexico's second-largest metropolitan area. The modern state covers approximately 78,600 km², making it Mexico's sixth-largest state by area. Nineteenth-century Jalisco was somewhat larger than the modern state: portions of its original territory were detached to help form the neighboring state of Colima (fully separated by 1857) and adjustments were made with Nayarit and Zacatecas over the 19th century, so applying the modern GADM boundary back to 1824 is an approximation that overstates precision for the earliest decades of this span.

## Predecessors and successors

No predecessor or successor polities are declared. Jalisco has no predecessor entry because, prior to 1824, its territory was administered as part of the Spanish colonial intendancy of Nueva Galicia, which is not separately represented in this polity table (it is absorbed into whatever pre-1824 Mexico/New Spain rows exist, none of which this entry claims to continue). It has no successor because it remains an active, current state of Mexico through the open end_year of 2025, alongside its containing national rows MEX-1800-1848 and MEX-1848-2025.

## Sourced claims

- The 1824 Constitution of the United Mexican States (Constitución Federal de los Estados Unidos Mexicanos) named Jalisco as one of the original constituent states of the federation, formed from the former Nueva Galicia intendancy.
- GADM 4.1 digitizes Jalisco as admin-1 feature(s) under GID_1 codes beginning MEX.14 (e.g. MEX.14_1), confirming it as a distinct, mapped administrative boundary rather than a data artifact.
- Modern Jalisco covers approximately 78,588 km² per INEGI (Mexico's national statistics/geography institute), ranking it among Mexico's largest states by area.

## Decisions

### d-start-year-1824-not-1900

**Start year set to 1824 (constitutional founding) rather than 1900 (first data year)**

The routing input's data window for MEX-JALISCO begins around 1900, but the proposed span in the routing decision correctly uses 1824 as start_year, on the basis that Jalisco was one of the original states named in the 1824 Constitution and is not one of the three later territory-to-state conversions (Baja California, Baja California Sur, Quintana Roo) that would justify a later admission-based start. This entry follows that reasoning: a polity's start_year should reflect when the administrative unit came into being, not when the first routed dataset happens to begin observing it. The risk flagged by the routing agent -- that precise confirmation of Jalisco's exact founding date among the 1824 states has not been separately verified against a specialized source on Mexican federal admission history -- is carried forward as an open question below rather than silently resolved.

### d-polygon-source-registered-unfetched

**polygon_source set to the registered slug gadm-4.1-adm1, not "none" or "new_source_needed"**

The routing decision's polygon_route is registered_source_unfetched, meaning the correct source (GADM 4.1 admin-1) is a real, registered source in this pipeline's vocabulary, but the specific on-disk file has not been fetched to include Mexico. Per this page's authoring instructions, that route requires the slug itself in polygon_source (not "none" and not the route name), with polygon_status set to unassigned rather than proxy or estimate. This distinguishes Jalisco's situation from a true none_available case: no new source needs to be found or invented, an existing fetch job just needs to be extended to cover Mexico.

## Open questions

### oq-jalisco-1824-founding-date

**Was Jalisco founded precisely in 1824, or admitted at a slightly different date?**

The routing agent explicitly flagged this as unconfirmed: the reasoning assumes Jalisco was one of the original founding states named directly in the 1824 Constitution rather than admitted in a subsequent year, based only on the fact that it is not one of the three well-documented territory-to-state conversions (Baja California, Baja California Sur, Quintana Roo). A dedicated source on Mexican federal state admission history (e.g. a constitutional history of the 1824 federation, or INEGI's own state histories) should be checked to confirm 1824 exactly, since some accounts describe Jalisco's territory being reorganized out of the short-lived 1823 Estado Libre de Xalisco slightly before the federal Constitution was ratified, which could push the defensible start_year a year earlier or later.

### oq-jalisco-19th-century-boundary-changes

**How much of Jalisco's modern territory differs from its 1824-1857 extent, given the Colima separation?**

Colima was detached from Jalisco's original territory and became a separate territory/state over the 19th century (formalized by 1857), and there were also boundary adjustments with Nayarit (itself carved out of Jalisco's Pacific coastal district, the Séptimo Cantón, as the Military Canton of Tepic in 1867 and later a full state in 1917) and with Zacatecas. This means the modern ~78,600 km² GADM boundary is almost certainly larger than 1824-1857 Jalisco and larger still than 1824-1917 Jalisco, but no specific historical-boundary source has been checked to quantify by how much. This should be resolved before any polygon is actually assigned to this entry, since applying the modern boundary uncritically across the full 1824-2025 span would overstate early Jalisco's territory, particularly for the pre-1917 portion of the span.

### oq-jalisco-mexico-source-gap

**When will gadm-4.1-adm1 be fetched/extended to cover Mexico, and is there an interim registered alternative?**

This entry cannot receive a polygon until the gadm-4.1-adm1 file staged in this repository's geodata is extended beyond its current 81-country subset to include Mexico. It is unclear from this routing pass whether that fetch is already scheduled, or whether an interim source (e.g. a Mexico-specific INEGI state-boundary shapefile, if one is already registered elsewhere in this pipeline's source list) could serve as a stopgap for gadm-4.1-adm1 specifically for Mexican states. This should be checked against the pipeline's source-fetch backlog rather than assumed to be pending indefinitely.
