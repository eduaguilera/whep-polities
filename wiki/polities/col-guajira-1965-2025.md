---
polity_code: COL-GUAJIRA-1965-2025
polity_name: Guajira (department of Colombia)
start_year: 1965
end_year: 2025
type: subnational
iso3: COL
continent: South America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: gadm-4.1-adm1
polygon_feature_id: COL.19_2
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: COL-1922-2025
    start_year: 1965
    end_year: 2025
    basis: La Guajira is a department of the Republic of Colombia throughout this span; the department was carved out of national territory (comisaría/intendencia status) and elevated to full department in 1965, remaining part of the unitary Colombian state to the present.
---

# Guajira (department of Colombia)

## Summary

This entry captures La Guajira, the department occupying the arid Guajira Peninsula in Colombia's extreme northeast, on the Caribbean coast bordering Venezuela. It is coded `type: subnational` because Colombia has held unbroken national sovereignty over this territory throughout; what this row exists to carry is the reporting/administrative unit, not a claim of statehood. The department was formally constituted in 1965, after decades as a Comisaría/Intendencia (a lower-tier "territorio nacional" administered more directly from Bogotá than a full department). No existing COL-* row in this table represents La Guajira specifically — the national Colombia rows (e.g. COL-1922-2025) are containers spanning the whole country, not this territory — so this is a genuinely new entry rather than a re-route of an existing one. The 1965 start_year marks the year the unit acquired full departmental status and its own elected departmental government, which is the natural break-point the country's default routing rule uses for post-1886 unitary-system departments. The vast majority of the statistical data now routed to this polity (about 98%) predates 1965 and is scaled/interpolated rather than directly reported, reflecting that the lower-tier territorio nacional was already being measured as a distinct reporting unit well before its 1965 elevation — hence it is back-cast to this polity rather than left unroutable.

**Why this entry exists.** This entry captures Colombian production/trade data tabulated under a "La Guajira" or equivalent department-level label, spanning back well before 1965 (the great majority of rows, ~98%, are scaled/interpolated reconstructions rather than directly reported figures) through to the present. Before this entry was created, that data had no department-specific polity to route to: the only existing COL-* rows are national containers (e.g. COL-1922-2025) representing the sovereign Colombian state as a whole, which is roughly 60 times larger in area than this one department and would badly misrepresent the geographic scope of any Guajira-specific statistic if used as the routing target. Historically, this entity's distinctness is confirmed by Colombia's own administrative law: La Guajira existed first as a Comisaría/Intendencia (territorio nacional), a recognized distinct administrative and statistical reporting unit under the national government, before its 1965 elevation to full department — meaning it was being tracked as a discrete unit in national statistics and administrative records well before it had a governor and departmental assembly of its own. This entry does not yet cross-reference a specific historical trading-polity source (e.g. Federico-Tena) confirming pre-1965 separate reporting; that remains to be checked (see open questions).

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is currently available in the GeoPackage for this territory. The registered source that should eventually supply it is GADM 4.1 ADM1 (`polygon_source: gadm-4.1-adm1`), which digitises Colombia's current departmental boundaries and is expected to carry La Guajira under a GID_1 code following the pattern `COL.xx_1`. However, the GADM 4.1 ADM1 file cached locally in this repository (`gadm-4.1-adm1.gpkg`) is a curated 81-country subset that does not include Colombia at all — the full global GADM ADM1 download does cover Colombia, but that full download has not been fetched into this repository, and GADM's licence terms have not yet been reviewed here. Because of this, `polygon_feature_id` is left null and `polygon_status` is `unassigned` rather than `assigned` or even `proxy`: there is no other polity's geometry in this table (Colombian or otherwise) that plausibly approximates a Guajira-shaped peninsula, so no proxy is offered either.

**Territory description:** La Guajira occupies the Guajira Peninsula, Colombia's northeasternmost department, projecting into the Caribbean Sea and sharing a land border with Venezuela's Zulia state to the east. Its capital is Riohacha on the Caribbean coast. The department is mostly semi-arid to desert terrain (La Guajira Desert) inhabited substantially by the Wayuu indigenous people, contrasting with the Sierra Nevada de Santa Marta foothills that form its southwestern edge. The modern department's area is approximately 20,850 km2 (a figure drawn from standard present-day references for the Colombian department, not measured from any polygon attached to this entry, since none is attached). A reader can locate it on a modern map as the tip of the peninsula separating the Caribbean Sea from the Gulf of Venezuela, north of Cesar and Magdalena departments.

## Predecessors and successors

No predecessor polity code is recorded: this entry begins cleanly at 1965, the year La Guajira was elevated from Comisaría/Intendencia (territorio nacional) status to a full department, and no earlier row in this table currently represents that pre-1965 national-territory phase as a distinct polity (see open question on this). There is no successor: La Guajira remains a current department of Colombia, so the span is left open through 2025 per this country's convention for still-existing subnational units, and end_year is exclusive of any future re-division.

## Sourced claims

- La Guajira was elevated to full department status in 1965, having previously held Comisaría/Intendencia (territorio nacional) status under Colombia's unitary administrative system — the routing decision's stated basis for this entry's start_year, pending primary legislative verification (see open question oq-guajira-elevation-year-verification).
- GADM 4.1 ADM1 digitises Colombia's current departments, including La Guajira, under an id_column GID_1 code expected to follow the pattern COL.xx_1, but the locally cached gadm-4.1-adm1.gpkg subset (81 countries) omits Colombia entirely, which is why this entry cannot yet cite a polygon_feature_id despite naming gadm-4.1-adm1 as its eventual source.

## Decisions

### d-code-guajira-not-gua

**Subunit code GUAJIRA chosen over the standard two/three-letter abbreviation GUA**

The dominant pattern in this table is <ISO3>-<SUBUNIT>-<start>-<end> with a short subunit abbreviation (e.g. ESP-AS, ESP-CA). The natural abbreviation for La Guajira is GUA, but wiki/polities/col-gua-1991-2025.md already exists in this repository for a different Colombian department (Guainía, elevated 1991), so GUA is taken. Rather than pick an arbitrary three-letter code that could be confused with either department, I used the full name GUAJIRA, following the same repository's precedent of falling back to longer names when abbreviations collide or are ambiguous (col-antioquia, col-cundinamarca, col-cordoba all use full names rather than forcing a two-letter code). Polity code: COL-GUAJIRA-1965-2025.

### d-polygon-unassigned-not-proxy

**No proxy polygon copied despite GADM being the obvious eventual source**

The routing decision's polygon_route is registered_source_unfetched: GADM 4.1 ADM1 is a registered source in scripts/sources.yaml but the locally cached gadm-4.1-adm1.gpkg only covers 81 countries and Colombia is not among them, so no feature_id can be assigned yet. Per the harness rule for this route, polygon_source is set to the slug itself (gadm-4.1-adm1) rather than 'none' or 'new_source_needed', and polygon_status is 'unassigned' rather than 'proxy', since there is no other polity's geometry in this table that would be a defensible stand-in for a Colombian department boundary.

## Open questions

### oq-guajira-elevation-year-verification

**1965 elevation-to-department date needs primary Colombian legal-source verification**

The start_year of 1965 rests on general historical recollection that La Guajira was elevated from Comisaría/Intendencia (territorio nacional) status to a full department of Colombia in that year, as flagged in the routing decision's own routing_concerns. Colombian departmental creation dates are set by specific national laws (e.g. Decreto/Ley numbered acts), and I have not verified the exact statute or its effective date against a primary legislative source such as the Colombian Congress's own gaceta or a standard reference like DANE's division político-administrativa history. If the correct year differs from 1965, both start_year in the frontmatter and the years embedded in the polity_code (COL-GUAJIRA-1965-2025) would need to change together, since a gate checks that those match.

### oq-guajira-boundary-stability-pre1965

**Whether the pre-1965 comisaría/intendencia territory had the same boundaries as today's department**

98% of the data being back-cast to this polity predates 1965 and is scaled/interpolated, per the routing decision's reasoning. Applying back_cast assumes the territory measured before 1965 (as a lower-tier national territory) had approximately the same extent as the modern department that GADM will eventually supply a polygon for. Colombian intendencias and comisarías were occasionally redrawn before conversion to departments, and I have not checked whether La Guajira's boundaries as a comisaría/intendencia in, say, the 1915-1930s differed materially from its 1965-onward departmental boundaries. If they differed, the earliest back-cast years would be measuring a different shape than the polygon eventually assigned here will represent.

### oq-guajira-predecessor-code

**No predecessor polity code recorded for the pre-1965 territorio nacional**

This entry has an empty predecessor list even though the routing decision explicitly treats pre-1965 data as a back-cast reconstruction of a territory that existed as a comisaría/intendencia before 1965. If a separate polity row for the pre-1965 territorio nacional phase is ever created (paralleling how other Colombian departments in this table sometimes get pre-elevation predecessor rows), this page's predecessor field and the container chain above should be revisited to link them rather than leaving this as a clean start in 1965.

### oq-guajira-gadm-fetch-pending

**GADM 4.1 ADM1 Colombia data has not actually been fetched or licence-checked**

polygon_source is set to gadm-4.1-adm1 under the registered_source_unfetched route, but as of this page's creation the full global GADM 4.1 ADM1 download (which does include Colombia, unlike the locally cached 81-country subset) has not been fetched into the repository, and the GADM licence terms have not been reviewed (licence_known: false in the routing decision's polygon_detail). Until that fetch happens and a GID_1 feature id for La Guajira (expected pattern COL.xx_1) is assigned, polygon_status must remain unassigned and no area figure can be computed for this territory from the repository's own geometry.
