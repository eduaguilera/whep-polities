---
polity_code: COL-CAQUETA-1981-2025
polity_name: Caquetá (department of Colombia)
start_year: 1981
end_year: 2025
type: subnational
iso3: COL
continent: South America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: gadm-4.1-adm1
polygon_feature_id: COL.9_2
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: COL-1922-2025
    start_year: 1981
    end_year: 2025
    basis: Caquetá was elevated from national territory (comisaría/intendencia) to a full department of Colombia in 1981 by Ley 78 de 1981, entirely within the modern national era bounded below by COL-1922-2025's own 1922 start; still current so end_year 2025 is open-ended
---

# Caquetá (department of Colombia)

## Summary

Caquetá is a department in southern Colombia, in the Amazon piedmont region, whose capital is Florencia. Unlike the older 19th-century Andean departments (Antioquia, Boyacá, Caldas), Caquetá spent most of the 20th century as a national territory — a comisaría/intendencia administered directly from Bogotá rather than as a self-governing department — and was only elevated to full departmental status in 1981 by Ley 78 de 1981, alongside a cluster of other Colombian frontier territories (Arauca, Casanare, Guainía, Guaviare, Putumayo) that followed the same path. This entry is `type: subnational` because Colombia held sovereignty throughout; the row exists to carry the department-level reporting territory that agricultural and population statistics are tabulated against separately from national Colombia totals, not to compete with the national COL chain for sovereignty ranking. The start_year of 1981, rather than the extract's earliest data year of 1915, reflects that legal elevation: the pre-1981 data for this unit is dominated by interpolated and back-cast methods (98.1% combined), the signature of a series being reconstructed onto a boundary (a full department) that did not yet exist as a first-order administrative or reporting unit at the time.

**Why this entry exists.** The pipeline's routing decision (unit_id COL-CAQUETA) identified rows labelled with a Caquetá-specific admin name in Colombian country data, spanning 1915-2023, previously matched only to the national COL-1922-2025 row — a total for the whole of Colombia and therefore vastly larger than Caquetá's own ~88,965 km2. No existing polity in the table represents Caquetá specifically; the national COL-* rows are successive whole-country totals. Caquetá's status as a distinct administrative and statistical reporting unit is confirmed by its documented history: administered as a national territory (comisaría/intendencia) for most of the 20th century, then elevated to full department status in 1981 by Ley 78 de 1981 — following the same path as sibling frontier departments Arauca, Casanare, Guainía, Guaviare and Putumayo, whose departures from the "national territory" default are already recorded in the country convention file (Caquetá itself is not yet named there, which is flagged as an open question). This mirrors sibling entries this same pipeline pass resolved to create_new for the identical reason: a reporting unit far smaller than the national total, with no existing polity representing it, and with a sibling verdict for this exact unit already recording the identical 1981 routing split.

## Territorial extent

**Polygon:** `polygon_status: unassigned`. The routing decision classifies this as `registered_source_unfetched`: `gadm-4.1-adm1` is the source family this repository already uses for other countries' department/province polygons, but the locally cached `gadm-4.1-adm1.gpkg` covers only a curated 81-country subset and Colombia is not among them (0 features for COL in the current cache) — the identical gap already documented on sibling entries COL-ANTIOQUIA-1886-2025, COL-CALDAS-1905-2025 and COL-BOYACA-1886-2025. The remedy is to fetch Colombia's ADM1 layer (`gadm41_COL_1`) from gadm.org under the same CC-BY-NC licence already governing this source family, not to construct a substitute polygon. No `polygon_area_km2` is recorded since no geometry is attached.

**Territory description:** Caquetá occupies the transition zone between the Andes and the Colombian Amazon in the south of the country, with capital Florencia. On a modern map it is bounded by Cauca and Huila to the north/northwest, Meta and Guaviare to the northeast/east, Amazonas to the southeast, Putumayo to the south, and Nariño and Cauca to the west. It is one of Colombia's larger departments by area, approximately 88,965 km2 (a figure drawn from general geographic reference, not from any polygon attached to this entry, since none exists yet — see polygon status above). Its territorial boundaries have been comparatively stable since the 1981 departmental elevation, unlike Caldas's 1966 split into three departments, though this has not been independently verified against a primary Colombian administrative-boundary source.

## Predecessors and successors

No predecessor or successor rows are set. Caquetá does not descend from a distinct prior polity in this table: before 1981 it was administered as a national territory (intendencia/comisaría) directly under the Colombian national government rather than as a separate department-level polity, and that pre-1981 span is staged elsewhere in the pipeline as unroutable/back_cast rather than assigned to a predecessor row (see open questions). Caquetá has no successor because it remains a current department of Colombia as of the 2025 end_year convention used across this table for still-open subnational units.

## Sourced claims

- Colombia's Department of Caquetá was created by Ley 78 de 1981, elevating the former national territory (intendencia/comisaría) of Caquetá to full department status — part of the same late-20th-century wave of national-territory-to-department elevations that produced Arauca, Casanare, Guainía, Guaviare and Putumayo.
- The routing decision's own extract for this unit spans 1915-2023 with method shares of 75.4% interpolated and 22.7% back_cast dominating, indicating the pre-1981 portion of the series is a reconstruction onto administrative boundaries (a full department) that did not yet exist in that period.

## Decisions

### d-follow-dominant-iso3-subunit-pattern

**Used <ISO3>-<SUBUNIT>-<start>-<end> rather than a bespoke code**

The polity code is COL-CAQUETA-1981-2025, following the dominant 57-of-66 subnational pattern (e.g. ESP-AS-1833-2025, DZA-CVD-1902-1919) rather than a bespoke name-only code, and matching sibling Colombian department entries created in this same pipeline pass (COL-ANTIOQUIA-1886-2025, COL-CALDAS-1905-2025, COL-BOYACA-1886-2025). Caquetá is a standard department within Colombia's standing administrative hierarchy, not a historical territory with an identity independent of its containing state the way Alaska Territory or Hyderabad State were, so the bespoke-code exception (3 of 66 rows) does not apply. The subunit token CAQUETA is spelled in full (unaccented, matching filesystem-safe ASCII already used for other accented Colombian department names such as CALDAS's siblings), rather than an abbreviation.

### d-start-year-is-departmental-elevation-not-data-start

**start_year set to 1981 (departmental elevation), not 1915 (earliest data)**

The routing decision's own extract for this unit runs 1915-2023, with the interpolated/back_cast methods dominating (75.4%+22.7%) — a signal that the pre-1981 rows are reconstructions onto a boundary (a full department) that did not yet exist, since before 1981 Caquetá was administered as a national territory (intendencia/comisaría), not a department, and was not a first-order reporting unit in the same administrative sense. Following the sibling verdict already recorded for this exact unit (1915-1980 staged separately as unroutable/back_cast, 1981-2023 as the proposed department), this entry's span starts at the 1981 legal elevation (Ley 78 de 1981) rather than at the data's earliest year, consistent with how COL-CALDAS-1905-2025 dates its own start to legal creation rather than to any earlier proto-territory.

### d-single-container-edge-suffices

**Single container edge to COL-1922-2025 tiles the whole 1981-2025 span**

Unlike COL-CALDAS-1905-2025 (which needed two container edges because its 1905 start falls inside the COL-1903-1922 era), Caquetá's 1981 start falls entirely inside the COL-1922-2025 national era (1922-2025), so one container edge covering 1981-2025 is sufficient and no gap is left. No edge into COL-1903-1922 or earlier eras is needed or valid, since 1981 postdates them.

## Open questions

### oq-1981-law-not-independently-verified

**1981 elevation year and Ley 78 citation not verified against a primary Colombian source**

The routing decision's own routing_concerns explicitly flag this: the 1981 date and 'Ley 78 de 1981' citation are carried over from the sibling verdict pattern for this exact unit, not independently checked against a primary source such as DANE's departmental gazetteer or the Colombian Diario Oficial text of the law. If the actual elevation date or law number differs, both start_year and the polity code (which encodes the year) would need to change, and the code-year gate would need re-satisfying. Unlike COL-CALDAS, where the founding-year uncertainty was flagged as general historical knowledge, here there is a specific law citation asserted that has not been checked at all.

### oq-pre1981-data-not-covered-by-this-entry

**1915-1980 rows for this unit are not represented by any polity row yet**

The routing decision stages 1915-1980 as 'unroutable/back_cast' rather than assigning it to this entry or to any other row — meaning a majority of the unit's own extract (75.4% interpolated + 22.7% back_cast method share, per the routing reasoning) falls in a span this page does not cover at all. Whether that pre-1981 span should eventually become a second row (e.g. a COL-CAQUETA-<territory>-1915-1981 national-territory entry, paralleling how comisaría-era predecessors are sometimes modelled elsewhere) or should simply remain routed to the national COL chain is unresolved, and is not decided by this page.

### oq-country-convention-departure-list-incomplete

**Caquetá is missing from the country convention's departure list for national-territory-to-department cases**

The routing_concerns note that Caquetá is not explicitly named among the departures (Amazonas, Arauca, Casanare, Guainía, Guaviare, Putumayo, San Andrés) recorded in the country convention file, even though its administrative history (comisaría/intendencia elevated to department) parallels those cases. `pipelines/agent-harness/state/country_conventions.json` should be checked and, if this pattern holds, updated to add Caquetá explicitly rather than relying on inferred parallelism, so future routing passes do not have to re-derive this reasoning from scratch.

### oq-gadm-col-fetch-pending

**GADM Colombia ADM1 data has not been fetched, so no polygon exists**

polygon_status is unassigned for the same reason as COL-CALDAS-1905-2025, COL-ANTIOQUIA-1886-2025 and COL-BOYACA-1886-2025: the locally cached gadm-4.1-adm1.gpkg subset covers only 81 countries and excludes Colombia (0 features for COL). Until gadm41_COL_1 is fetched from gadm.org and added to the local cache, this entry has no polygon at all, not even a proxy, and no polygon_area_km2 is recorded. Once fetched, Caquetá's GADM boundary should reflect its post-1981 department extent, which — unlike Caldas's 1966 split — has been comparatively stable since 1981, though minor municipal-level adjustments since then are not independently checked here.
