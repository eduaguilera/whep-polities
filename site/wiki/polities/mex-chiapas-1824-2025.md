---
polity_code: MEX-CHIAPAS-1824-2025
polity_name: Chiapas
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
    basis: Chiapas joined the Mexican federation in 1824 following the plebiscite that separated it from the former Kingdom of Guatemala/Central America; MEX-1800-1848 is the polity row covering Mexico for this earlier era, up to the 1848 Treaty of Guadalupe Hidalgo boundary.
  - code: MEX-1848-2025
    start_year: 1848
    end_year: 2025
    basis: Continuous Mexican federal sovereignty over Chiapas from the post-1848 national territory through the present; MEX-1848-2025 is the polity row covering this later era.
---

# Chiapas

## Summary

Chiapas is a Mexican federal state in the country's far south, bordering Guatemala. This entry covers it as a subnational reporting/administrative unit of the Mexican federation from its 1824 admission as a state to the present. `type: subnational` because Chiapas is a constituent unit contained by Mexico's national sovereignty throughout, not a claim to statehood of its own -- exactly the same rationale that keeps subnational entries out of competition with a country's national polity chain in the matcher's family/sovereignty ranking. There is no predecessor row and no successor row: nothing in this table currently represents Chiapas before 1824 (it was part of the Kingdom of Guatemala/Central American federation, not tracked here as a MEX-lineage polity) or after 2025 (2025 is the open-ended-present convention date, not a real discontinuity). The entry was created because Chiapas is a real administrative unit with its own government, statistics, and identity that has no existing row, boundary feature, or name-matching candidate in the table -- it did not arise from routing any specific dataset, but from filling a gap in Mexico's state-level coverage identified by this pipeline's country/subunit sweep.

**Why this entry exists.** This entry does not capture any specific dataset rows -- unlike the Manchuria exemplar, it originates from this pipeline's country/subunit coverage sweep for Mexico rather than from a routing conflict against existing data. What it captures is the gap itself: Mexico has zero existing subnational rows in the polity table (the routing decision notes "Existing subnational codes for MEX (0): none -- this country sets its own precedent"), so no candidate row, name match, or boundary feature previously existed for Chiapas to be matched against, correctly or incorrectly. What confirms Chiapas is a distinct administrative entity deserving its own row is straightforward and not contested: it is one of Mexico's 31 constituent states, with continuous existence as a federal subdivision since its 1824 admission, its own state government, and its own economic/agricultural statistics reported by Mexican national sources (e.g., INEGI, SIAP) separately from national totals -- the same reporting-unit logic (a distinct entity that gets tabulated on its own) that the Manchuria exemplar cites via issue 400, applied here prospectively rather than in response to an existing mismatched dataset.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon available in the GeoPackage for this period. GADM 4.1's admin-1 layer is the natural source -- it does digitise Mexican states -- but the copy of that source present in this repository (data/geodata/gadm-4.1/gadm41_adm1.gpkg) is a curated 81-country subset that does not include Mexico at all, so zero candidate features exist locally today. This is a registered-source-unfetched situation, not a missing-source one: fetching the full global (or Mexico-inclusive) GADM 4.1 admin-1 layer is what would unblock assignment, tracked in open question oq-gadm-mexico-fetch.

**Territory description:** Chiapas is Mexico's southernmost state, bordering Guatemala to the east and south, Tabasco to the north, Veracruz and Oaxaca to the west, and the Pacific Ocean along its southwestern Soconusco coast. Its capital is Tuxtla Gutiérrez; the state also contains the historic town of San Cristóbal de las Casas and the Lacandon Jungle along the Guatemalan border. Modern Chiapas covers approximately 73,900 km2 (INEGI's official figure for the state). No polygon-derived area is available for this entry (see polygon status above), so this figure is the conventional modern administrative area, not a measurement of any geometry attached to this record. The state's boundary has not been perfectly stable across the 1824-2025 span: the Soconusco coastal strip was disputed between Mexico and Central America/Guatemala until its formal incorporation into Chiapas in 1842, so a modern-boundary polygon would slightly overstate Chiapas's actual administered territory for roughly the first two decades of this entry's span (open question oq-modern-vs-historical-boundary).

## Predecessors and successors

No predecessor row exists: before 1824 Chiapas was part of the Kingdom of Guatemala and then briefly the Federal Republic of Central America, neither of which is represented in this table's MEX lineage, so the predecessor list is empty rather than pointing to an untracked entity. No successor row exists either: Chiapas remains a Mexican state today, and end_year 2025 reflects this table's open-ended-present convention rather than any real discontinuity, so the successor list is also empty. Containment carries the actual continuity instead, via two edges: MEX-1800-1848 for 1824-1848 and MEX-1848-2025 for 1848-2025, jointly tiling the whole span with the split falling exactly at the boundary between those two container rows.

## Sourced claims

- Chiapas was admitted as a state of the Mexican federation in 1824, following a plebiscite that separated the former Provincia de Chiapas from the Kingdom of Guatemala/Federal Republic of Central America (per the routing decision's span_basis, corroboration against a primary administrative-history source pending -- see open question oq-1824-admission-year-corroboration).
- GADM 4.1's global admin-1 layer digitises Mexican states, including Chiapas (expected GID_1 code in the MEX.* series), but the copy present in data/geodata/gadm-4.1/gadm41_adm1.gpkg in this repository is a curated 81-country subset that returns zero rows for Mexico, confirmed by the routing decision's polygon_reasoning field.

## Decisions

### d-code-pattern-iso3-subunit

**Coded as MEX-CHIAPAS-1824-2025, following the dominant 57-of-66 pattern**

Chiapas is a Mexican federal state with no existing name-matching candidate or boundary feature, and no historical-territory identity distinct from its administrative role (unlike ALK or HYD, which carry names independent of any modern ISO subdivision code). The dominant subnational pattern, <ISO3>-<SUBUNIT>-<start>-<end>, applies directly: ISO3 is MEX, SUBUNIT is CHIAPAS (there is no shorter conventional abbreviation analogous to ESP's two-letter province codes, so the full state name is used to avoid collision with any other Mexican state that might later be coded with a truncated form), giving MEX-CHIAPAS-1824-2025. No departure from the dominant pattern was needed.

### d-container-split-two-eras

**Container split across MEX-1800-1848 and MEX-1848-2025 to tile the full 1824-2025 span**

The polity table holds only two MEX national rows: MEX-1800-1848 (1800-1848) and MEX-1848-2025 (1848-2025), together spanning 1800-2025 with no gap. Chiapas's own span, 1824-2025, starts inside the first era and runs through the second, so a single container edge citing only MEX-1848-2025 would leave 1824-1848 uncontained -- the exact failure mode the harness's containment gate is built to reject. Two edges were used instead, split exactly at the 1848 boundary shared by the two container rows, so the pair jointly covers 1824-2025 with no gap and no edge extending past either container row's own span.

### d-polygon-status-unassigned

**polygon_status set to unassigned, not proxy or estimate**

The routing decision this page implements found GADM's admin-1 layer is the natural source for Chiapas's boundary, but the copy of gadm-4.1-adm1 present in this repository (data/geodata/gadm-4.1/gadm41_adm1.gpkg) is an 81-country curated subset that excludes Mexico entirely -- zero matching rows. No feature_id can therefore be identified today, which is the 'registered_source_unfetched' situation described in the routing decision: the source is known and registered but not locally usable for this country. Of the schema's polygon_status values (assigned, proxy, estimate, unassigned, polygon_vintage_drift), unassigned is the only one that does not assert a specific geometry or an approximation of one; proxy and polygon_vintage_drift both presuppose an actual attached feature, which does not exist here.

## Open questions

### oq-gadm-mexico-fetch

**GADM Mexico admin-1 data needs to be fetched before a polygon can be attached**

The repository's local gadm-4.1-adm1 GeoPackage is an 81-country curated subset that does not include Mexico, so no GID_1 feature for Chiapas (expected to be something like MEX.7_1 in GADM's numbering) can currently be identified. Fetching the full global GADM 4.1 admin-1 layer, or another Mexico-specific state boundary source, is a prerequisite for moving polygon_status from unassigned to assigned. Until then this entry carries no territory geometry and no measured area, and any downstream user relying on polygon_area_km2 for Chiapas will find it null.

### oq-1824-admission-year-corroboration

**The 1824 admission year is the routing decision's stated default, not independently verified against a primary source**

The upstream routing decision cites 1824 -- the year of the plebiscite separating Chiapas from the former Kingdom of Guatemala/Central America and its formal incorporation as a state of the Mexican federation -- as the default start_year under the admission-year convention, explicitly flagging that this date 'should be corroborated against a primary administrative-history source rather than general knowledge.' That corroboration has not been done in authoring this page. If a primary source places the plebiscite or the federal admission in a different year (some accounts distinguish the 1824 plebiscite from a later formal annexation date), start_year and the code itself would need to change together, since the code must equal the frontmatter years.

### oq-modern-vs-historical-boundary

**Any polygon eventually attached will be a modern-boundary approximation for the entire 1824-2025 span, including the 19th century**

GADM's admin-1 layer reflects present-day (c. 2018-2022) state boundaries. Chiapas's own boundary has not been static since 1824: most notably, the Soconusco region (the Pacific coastal strip bordering Guatemala) was disputed between Mexico and the Central American federation/Guatemala until it was formally incorporated into Chiapas in 1842, and there have been smaller municipal-boundary adjustments since. A GADM-derived polygon used as-is for the full 1824-2025 span would silently include Soconusco for the roughly two decades before 1842 when it was not administratively part of Chiapas. Whether this should be handled as a documented approximation or a separate pre-1842 sub-period is unresolved and depends on whether any data actually keyed to this polity falls in that window.
