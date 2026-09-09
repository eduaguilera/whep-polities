---
polity_code: MEX-MICHOACAN-1824-2025
polity_name: Michoacán
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
polygon_feature_id: MEX.16_1
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: MEX-1848-2025
    start_year: 1848
    end_year: 2025
    basis: Michoacán has been a constituent state of the Mexican federation continuously since 1824, and the national polity MEX-1848-2025 covers the post-Mexican-American-War national territory that Michoacán has sat inside from 1848 onward.
  - code: MEX-1800-1848
    start_year: 1824
    end_year: 1848
    basis: From its 1824 admission to the federation under the 1824 Constitution until the 1848 territorial reorganization following the Mexican-American War, Michoacán sat inside the earlier national polity MEX-1800-1848.
---

# Michoacán

## Summary

This entry represents the Mexican state of Michoacán, one of the original 19 states admitted to the United Mexican States under the 1824 Constitution, and continuously a first-order administrative division of Mexico since. `type: subnational` is used because Michoacán has never held sovereign status of its own -- it sits inside the sovereign national Mexico chain (MEX-1800-1848, then MEX-1848-2025) throughout its existence -- and this row exists purely to carry state-level statistics that were previously only routable to the much larger national MEX rows. No MEX subnational row existed before this entry (0 of the table's 66 subnational rows carry a MEX iso3), so this page and its code choice (MEX-MICHOACAN-1824-2025) set the precedent other Mexican states will likely follow. The span 1824-2025 follows the state's continuous existence under the federation rather than the narrower range of any single data extract, per the routing decision's `span_basis`, and end_year 2025 is open/current (exclusive) rather than marking any dissolution.

**Why this entry exists.** **Input data captured:** This entry is created to carry Mexican state-level statistics for Michoacán that the routing pipeline found had no existing home. Per the routing decision (unit_id MEX-MICHOACAN, admin_name "Michoacán", country Mexico), Michoacán contains subnational statistics collected specifically for this state, distinct from country-wide MEX totals.

**Previous matching and why it was wrong:** Before this entry, the only MEX polities in the database were the two national rows MEX-1800-1848 and MEX-1848-2025 -- there were zero subnational MEX rows. Any Michoacán-specific statistics would previously have had to be routed to one of those national rows, which cover the whole of Mexico (roughly 2 million km²) rather than the ~58,600 km² state the data actually describes -- a mismatch of more than 30x in territorial scope, which silently misattributes state-level figures as national ones.

**Confirmation the entity is distinct:** Michoacán's status as a distinct, continuously-existing political-administrative entity is not in serious doubt -- it is one of the 19 original states named in the 1824 Constitution creating the Mexican federation, and has remained a first-order constituent state since (unlike Baja California, Baja California Sur, and Quintana Roo, which the routing reasoning notes were federal territories converted to statehood later, and so follow a different start-date rule). Its founding date and continuous existence are attested by Mexican constitutional history rather than by a single data source, which is why this entry's start_year (1824) is derived from that constitutional history rather than from the data extract's own range.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon feature could be attached at creation time, though the correct registered source is identified: `gadm-4.1-adm1` publishes Mexican state boundaries under `GID_1` codes (Michoacán would be `MEX.16_1`), but the repository's local copy of that GeoPackage under data/geodata/gadm-4.1/ is a curated subset covering 81 countries that excludes Mexico entirely (0 features for MEX). This is the `registered_source_unfetched` case: the source is correctly identified and registered, it just has not been fetched/added locally for this country. `polygon_source` is set to `gadm-4.1-adm1` (the slug, not the route name) with `polygon_feature_id` left null and `polygon_status: unassigned` until that local gap is closed.

**Territory description:** Michoacán is a Mexican state on the Pacific coast of west-central Mexico, bordered by Jalisco, Guanajuato, Querétaro, México State, and Guerrero, with a Pacific coastline in the south. Its capital is Morelia. The modern state covers approximately 58,600 km², making it one of Mexico's mid-sized states (roughly the area of Croatia). This figure is drawn from present-day state statistics, not measured from any polygon attached to this entry (none is attached yet), and is offered only so a reader can locate and size the territory on a modern map. The state's historical boundaries have shifted somewhat since 1824 -- portions of its original territory were involved in 19th-century adjustments with neighboring states such as Colima, Guerrero, and Jalisco -- so the modern ~58,600 km² figure should not be assumed to hold exactly for the earliest years of this entry's span; see the open question on boundary vintage.

## Predecessors and successors

Michoacán has no predecessor polity in this table: it is a founding state of the Mexican federation from 1824, not a successor to any prior distinct entity captured here (colonial-era New Spain intendancies are not separately modeled). It has no successor either, since end_year 2025 is open-ended (exclusive) and the state remains current as of this writing -- it is simply Mexico's ongoing constituent state of Michoacán, with no annexation, split, or renaming event recorded in this database's span.

## Sourced claims

- Michoacán was one of the original 19 states named in the Constitution of 1824, which established the United Mexican States as a federal republic (Acta Constitutiva de la Federación Mexicana, 1824).
- GADM 4.1's admin-1 layer for Mexico assigns Michoacán the GID_1 code MEX.16_1, but the repository's local extract of that dataset at data/geodata/gadm-4.1/ currently contains zero MEX features (confirmed by the routing decision's polygon_reasoning field, which reports the local file is an 81-country curated subset excluding MEX).

## Decisions

### d-code-follows-subunit-pattern

**Code follows the dominant <ISO3>-<SUBUNIT>-<start>-<end> pattern**

57 of 66 subnational rows in the polity table use <ISO3>-<SUBUNIT>-<start>-<end>, e.g. ESP-AS-1833-2025, DZA-CVD-1902-1919. Michoacán has no existing subnational precedent for MEX (0 rows), so this entry sets it. It is not a historical territory with a name independent of the modern state the way ALK or HYD are -- it is simply a Mexican state -- so the bespoke-code pattern does not apply, and the dominant pattern is followed: MEX-MICHOACAN-1824-2025. A short abbreviation (MICH) was considered but the full name was kept since no other MEX subnational codes exist yet to establish an abbreviation convention, and 'MICH' risks colliding with a future different state's initials.

### d-container-split-at-1848

**Container edges split at the 1848 national reorganization**

The polity table has two national MEX rows: MEX-1800-1848 (Mexico to 1848) and MEX-1848-2025 (Mexico from 1848). Michoacán's span (1824-2025) crosses that boundary, so a single container edge citing only MEX-1848-2025 would leave 1824-1848 uncontained and fail the containment gate's full-tiling requirement. Two edges are declared instead, one per containing national era, together tiling 1824-2025 with no gap: MEX-1800-1848 for 1824-1848, and MEX-1848-2025 for 1848-2025.

### d-polygon-status-unassigned

**polygon_status is unassigned, not proxy or estimate, because the source is registered but unfetched**

The routing decision's polygon_route is registered_source_unfetched: gadm-4.1-adm1 is a registered source and does publish Mexican state boundaries under GID_1 codes (e.g. MEX.16_1 for Michoacán), but the local copy at data/geodata/gadm-4.1/ is a curated 81-country subset that excludes MEX entirely (0 features for that country). Per the routing instructions, when the route is registered_source_unfetched the slug IS the polygon_source (gadm-4.1-adm1), polygon_feature_id is left null since no feature can be identified from what's on disk, and polygon_status is unassigned rather than new_source_needed or none, which were both explicitly rejected by validate_declared_sources for this exact situation.

## Open questions

### oq-gadm-mex-not-fetched

**Local GADM 4.1 admin-1 file excludes Mexico entirely**

The repository's copy of gadm-4.1-adm1.gpkg under data/geodata/gadm-4.1/ is a curated 81-country subset and has zero features for MEX, even though GADM 4.1 globally does publish Mexican state boundaries (GID_1 codes like MEX.16_1 for Michoacán). Until MEX is added to that local extract, or the full global GADM 4.1 admin-1 layer is fetched, no polygon_feature_id can be assigned here and polygon_status must stay unassigned. This blocks not just Michoacán but any other Mexican state entries this pipeline creates later -- worth fetching the MEX slice once rather than re-discovering this gap per state.

### oq-boundary-changes-since-1824

**Whether Michoacán's modern GADM boundary matches its historical extent back to 1824**

Even once a GADM 4.1 feature for Michoacán is available, it will be a present-day snapshot. Michoacán's territory has not been static since 1824: parts of its original extent were reassigned during 19th-century state formations (e.g. the creation/adjustment of neighboring states such as Colima, Guerrero, and territorial disputes with Jalisco and México state over the following decades). No check has been done here on how large that discrepancy is, or whether an intermediate boundary vintage would be more appropriate for the pre-1857 portion of this span; this should be assessed once a feature is actually fetched.

### oq-1848-container-split-precedent

**Is splitting a subnational container edge at a national reorganization year the right general pattern?**

This is likely one of the first MEX subnational entries whose span crosses the 1848 MEX-1800-1848/MEX-1848-2025 national boundary. The two-edge container solution used here (splitting at 1848) satisfies the tiling gate, but if other founding states (e.g. Jalisco, Guanajuato, also founded 1824) are added later, this convention should be checked for consistency rather than re-derived each time, and recorded in country_conventions.json for MEX if not already.
