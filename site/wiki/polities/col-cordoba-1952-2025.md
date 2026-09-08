---
polity_code: COL-CORDOBA-1952-2025
polity_name: Córdoba (department of Colombia)
start_year: 1952
end_year: 2025
type: subnational
iso3: COL
continent: South America
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
  - code: COL-1922-2025
    start_year: 1952
    end_year: 2025
    basis: Córdoba was created as a department of Colombia in 1952, split off from the department of Bolívar, entirely within the modern national era bounded below by COL-1922-2025's own 1922 start; the department remains current, so end_year 2025 is the open end used across this table for still-active subnational units.
---

# Córdoba (department of Colombia)

## Summary

Córdoba is a department in northwestern Colombia's Caribbean region, created in 1952 by splitting territory off from the department of Bolívar. This entry is `type: subnational` because Colombia held sovereignty throughout the full span — the row exists to carry the department-level reporting territory that production/trade statistics tabulate separately from whole-of-Colombia totals (already carried by the national COL-1922-2025 chain), not to compete for sovereignty ranking against that national chain. The start_year of 1952, rather than the routing extract's earliest data year of 1915, reflects Córdoba's formal constitution as a department: the routing decision found the pre-1952 data (1915-1951) to be 98.3% scaled/interpolated, the signature of a series back-projected onto a departmental boundary that did not yet exist as a distinct administrative or reporting unit at the time it was recorded — treated as a back_cast onto this proposed polity rather than as a genuinely separate historical entity requiring its own predecessor row, matching the treatment already given to sibling entries COL-CAQUETA-1981-2025 and COL-CASANARE-1991-2025 in this same pipeline pass.

**Why this entry exists.** The pipeline's routing decision (unit_id COL-CORDOBA) identified rows labelled with a Córdoba-specific admin name in Colombian country data, spanning a stated data window of 1915-2023, previously matched only to the national COL-1922-2025 row — a whole-of-Colombia total roughly 45 times Córdoba's own ~25,000 km2 and therefore incapable of preserving Córdoba as a distinct reporting series once merged into it. No existing polity in the table represents Córdoba specifically before this batch; the four COL-national rows (COL-1800-1830, COL-1830-1903, COL-1903-1922, COL-1922-2025) only contain it, and Colombia had zero subnational rows in the table prior to this pipeline pass, so there was no competing entry to route these rows to. Córdoba's distinctness as an administrative/reporting unit is confirmed by its documented administrative history: formally created as a department of Colombia in 1952 by splitting territory off from the department of Bolívar (Decree 1029 of 1952), a discrete legal event rather than a gradual reporting convention, paralleling how sibling entries in this same batch (COL-CAQUETA-1981-2025 by Ley 78 of 1981, COL-CASANARE-1991-2025 under the 1991 Constitution) each rest on their own dated departmental-creation act.

## Territorial extent

Polygon status: Not yet assigned. No polygon available in the GeoPackage for this period. The routing decision's polygon_route field is labelled new_source_needed, but its own polygon_reasoning acknowledges this is really a registered_source_unfetched case: gadm-4.1 is already a registered source family in this repository (site/wiki/sources/gadm-4.1.md), used for other countries' department/province polygons, but the locally cached data/geodata/gadm-4.1/ directory holds only a curated country subset and no Colombia file (gadm41_COL_*.gpkg) is present — the identical gap already documented on sibling entries COL-CAQUETA-1981-2025, COL-CASANARE-1991-2025, COL-ANTIOQUIA-1886-2025, COL-ATL-1910-2025 and COL-BOYACA-1886-2025 created in this same pipeline pass. The remedy is to fetch Colombia's ADM1 layer from gadm.org under the same licence family, not to construct a substitute polygon; no other registered source in this repository (CShapes 2.0, Cliopatria, Paine et al.) carries Colombian department-level boundaries. polygon_source is accordingly set to gadm-4.1-adm1 (the registered slug), polygon_status to unassigned, and no polygon_area_km2 is recorded since no geometry is attached.

Territory description: Córdoba occupies part of Colombia's Caribbean coastal lowlands and the lower Sinú river valley, in the country's northwest. On a modern map it is bounded by the Caribbean Sea to the north, Antioquia to the south and southeast, Sucre to the west, and Bolívar to the east. Its capital is Montería. It covers approximately 25,000 km2 (a commonly cited reference figure for the department, not a figure measured from any attached geometry — no polygon is attached to this entry) and its economy is historically dominated by cattle ranching and, along the Sinú valley, agriculture. This description is drawn from general geographic reference, not from any polygon attached to this entry.

## Predecessors and successors

No predecessor or successor rows are set. Córdoba does not descend from a distinct prior polity in this table: before 1952 its territory was part of the department of Bolívar, and that pre-1952 span is staged elsewhere in the pipeline as a back_cast segment rather than assigned to a predecessor row here (see open questions, given the unresolved risk that some of that segment may in fact belong to COL-BOLIVAR-1886-2025 rather than to this entry). Córdoba has no successor because it remains a current department of Colombia as of the 2025 end_year convention used across this table for still-open subnational units.

## Sourced claims

- Córdoba was created as a department of Colombia in 1952, split off from the department of Bolívar (Decree 1029 of 1952), rather than descending from one of the frontier territorios nacionales (Amazonas, Arauca, Casanare, Guainía, Guaviare, Putumayo, San Andrés, and Caquetá on an earlier legal basis) whose later 1980s/1990s elevation from national-territory to departmental status is recorded separately in this pipeline's country conventions.
- The routing decision's extract for unit_id COL-CORDOBA spans a stated data window of 1915-2023, with the pre-1952 segment (1915-1951) dominated by reconstructed methods: 74.9% interpolated plus 23.4% scaled (98.3% combined), the signature of a source back-projecting totals onto a departmental boundary that did not yet exist as a first-order administrative or reporting unit before 1952.

## Decisions

### d-follow-dominant-subunit-pattern

**Used <ISO3>-<SUBUNIT>-<start>-<end> rather than a bespoke code**

The polity code is COL-CORDOBA-1952-2025, following the dominant 57-of-66 subnational pattern (e.g. ESP-AS-1833-2025, DZA-CVD-1902-1919) rather than a bespoke name-only code, and matching sibling Colombian department entries created in this same pipeline pass (COL-CAQUETA-1981-2025, COL-CASANARE-1991-2025, COL-ANTIOQUIA-1886-2025, COL-ATL-1910-2025, COL-BOYACA-1886-2025, COL-CALDAS-1905-2025, COL-CAU-1886-2025, COL-CESAR-1967-2025, COL-CHO-1947-2025, COL-CUNDINAMARCA-1886-2025). Córdoba is a standard department within Colombia's standing administrative hierarchy, not a historical territory with an identity independent of that role, so the bespoke-code exception (3 of 66 rows: ALK, HYD, RYU) does not apply. The subunit token CORDOBA is spelled in full, unaccented ASCII, matching sibling department entries in this same batch (CAQUETA, CASANARE) rather than an abbreviation.

### d-start-year-is-creation-not-data-start

**start_year set to 1952 (formal creation as a department), not the extract's 1915 data start**

Córdoba was constituted as a department of Colombia in 1952 by Decree 1029 of 1952, splitting it off from the department of Bolívar. The routing decision's extract spans 1915-2023, but the pre-1952 segment (1915-1951) is dominated by reconstructed methods (74.9% interpolated + 23.4% scaled = 98.3%), the signature of a source back-projecting totals onto Córdoba's modern departmental boundary before the department existed as a distinct administrative or reporting unit. This is the same treatment already applied to sibling entries COL-CAQUETA-1981-2025 and COL-CASANARE-1991-2025: start_year is set at legal creation, and the pre-creation back_cast segment is left staged in the pipeline rather than assigned a predecessor row here. The routing_concerns field flags the 1952 date as drawn from general historical knowledge rather than a primary source verified in this repo; this is carried forward as an open question below rather than silently resolved.

### d-polygon-route-is-unfetched-not-new

**polygon_source is gadm-4.1-adm1 (registered_source_unfetched), overriding the decision's new_source_needed label**

The routing decision's polygon_route field says new_source_needed and its polygon_reasoning field explicitly hedges that this is really a registered_source_unfetched case forced into the wrong enum bucket: gadm-4.1 IS a registered source in this repository (site/wiki/sources/gadm-4.1.md, scripts/sources.yaml), already used for other countries' department/province polygons, but the locally cached data/geodata/gadm-4.1/ directory holds only a curated subset of country .gpkg files and no gadm41_COL_*.gpkg is present (0 features for COL in the current cache) — the identical gap already documented on sibling entries COL-CAQUETA-1981-2025, COL-CASANARE-1991-2025, COL-ANTIOQUIA-1886-2025, COL-ATL-1910-2025 and COL-BOYACA-1886-2025. Per the harness instructions, new_source_needed and registered_source_unfetched both map polygon_source to a real registered slug when the slug itself already exists in the registry and only the fetch is missing, so polygon_source is set to gadm-4.1-adm1 with polygon_status: unassigned and polygon_feature_id: null, not 'none'.

## Open questions

### oq-1952-creation-date-unverified

**1952 creation date for Córdoba is not yet verified against a primary Colombian legal source**

The routing decision's own routing_concerns field states the 1952 date is drawn from general historical knowledge, not corroborated against a primary source in this repository (e.g. the text of Decree 1029 of 1952, or a Colombian government/DANE administrative-history reference). If a primary source instead gives a different effective date (creation decrees and effective installation of departmental government sometimes differ by months or a year), start_year and this entry's container edge start_year would both need revision, since the code embeds the start year directly. This should be corroborated before the span_basis is treated as settled, following the same caution already flagged on sibling entries in this batch.

### oq-back-cast-parent-unconfirmed

**Whether 1915-1951 data correctly back-casts onto Córdoba rather than onto Bolívar**

The routing decision classifies the 1915-1951 segment (98.3% combined interpolated/scaled) as a back_cast onto Córdoba's modern boundary, consistent with the sibling COL-CAQUETA and COL-CASANARE treatments. But the routing_concerns field flags an unresolved risk: if the underlying source's allocation method actually implies the pre-1952 rows describe the parent department (Bolívar) rather than being reconstructed specifically onto Córdoba's post-1952 boundary, then those rows may need re-routing to COL-BOLIVAR-1886-2025 (already created in this same pipeline pass) instead of being staged as a back_cast segment under this entry. This has not been checked against the source's own stated allocation method.

### oq-no-polygon-cached-for-col

**No GADM ADM1 geometry is cached for Colombia; fetching it is unscheduled**

This entry has no polygon assigned because data/geodata/gadm-4.1/ does not include a Colombia file in its cached subset. Fetching gadm41_COL_1.gpkg from gadm.org (same licence family as gadm-4.1) would resolve this for Córdoba and for the five other Colombian department entries created in this same pipeline pass that share the identical gap. Until that fetch happens, polygon_area_km2 is unset and the ~25,000 km2 approximate figure given in territorial_extent is descriptive only, not a measured geometry.
