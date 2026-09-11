---
polity_code: COL-CUNDINAMARCA-1886-2025
polity_name: Cundinamarca (department of Colombia)
start_year: 1886
end_year: 2025
type: subnational
iso3: COL
continent: South America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: gadm-4.1-adm1
polygon_feature_id: COL.15_2
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: COL-1830-1903
    start_year: 1886
    end_year: 1903
    basis: Cundinamarca was constituted as a department of the unitary Republic of Colombia under the 1886 Constitution, which the container row COL-1830-1903 (Colombia to 1903) still covers at its tail end
  - code: COL-1903-1922
    start_year: 1903
    end_year: 1922
    basis: Cundinamarca continued as a department of Colombia through the 1903-1922 national era, bounded by Panama's 1903 secession and the 1922 US-Colombia treaty ratification that the existing COL rows already use to segment this period
  - code: COL-1922-2025
    start_year: 1922
    end_year: 2025
    basis: Cundinamarca remains a current department of Colombia within the modern national row, open-ended (end_year 2025) as the still-current polity, per the routing decision's proposed container_code
---

# Cundinamarca (department of Colombia)

## Summary

Cundinamarca is one of the original departments of the Republic of Colombia, a central Andean region surrounding — but since 1991 administratively excluding — the national capital Bogotá. It was constituted as a department under the centralizing 1886 Constitution that replaced the earlier federal Estados Unidos de Colombia, in which Cundinamarca had existed as a sovereign federal state (Estado Soberano de Cundinamarca) since 1863. This entry is `type: subnational` because Colombia held sovereignty throughout 1886-2025 — Cundinamarca was never itself a sovereign state within this row's span — but it is nonetheless a distinct reporting and administrative unit that agricultural, trade, and population statistics are tabulated against separately from national Colombia totals. The row exists to carry that department-level reporting territory, not to compete with the national COL chain for sovereignty ranking. Cundinamarca is a current, unabolished department (unlike the territorios nacionales only elevated to departments starting in 1991, and unlike Bogotá, which was carved out of it), so its span runs continuously from 1886 to the open end_year (2025) used for still-current subnational units, mirroring the treatment already applied to sibling department COL-ANTIOQUIA-1886-2025 created in the same pipeline pass.

**Why this entry exists.** Input data: 66 rows of source `juan-subnational` labelled with a Cundinamarca-specific admin name, spanning data years 1915-2023, covering Colombian country statistics tabulated at department level. Previous match: all 66 rows were matched to the national COL-* rows (chiefly COL-1922-2025, with any pre-1922 rows falling to COL-1903-1922), which is wrong because those rows are whole-of-Colombia totals roughly 50 times Cundinamarca's own department-level area (~22,605 km2 vs Colombia's ~1,141,748 km2) — folding department-scale figures into a national total either double-counts them against the country aggregate or silently mislabels their territorial scope. Confirmation of distinctness: Colombia's own constitutional and administrative history confirms Cundinamarca as a continuously-existing, separately-governed department since the 1886 Constitution (having been the sovereign Estado Soberano de Cundinamarca 1863-1886 before that), with its own DANE statistical reporting distinct from national aggregates — the same evidentiary basis already accepted for sibling department COL-ANTIOQUIA-1886-2025 in this same pipeline pass, and none of the four listed departure exceptions in the routing decision (Sucre; 1991 new departments; Quindío/Risaralda split; Cesar) apply to disqualify Cundinamarca from the same default treatment.

## Territorial extent

**Polygon:** `polygon_status: unassigned`. The routing decision classified this as `registered_source_unfetched`: `gadm-4.1-adm1` is the registered source family this repository already uses for other countries' ADM1-level department/province polygons, but the locally cached `gadm-4.1-adm1.gpkg` is an 81-country subset that does not include Colombia (0 features for COL). The remedy is to fetch Colombia's ADM1 data (e.g. `gadm41_COL_1` from gadm.org, under the same source family's licence) rather than construct a new source or borrow a polygon from elsewhere — exactly the remedy recorded for sibling entry COL-ANTIOQUIA-1886-2025. No polygon is assigned by this page; `polygon_feature_id` is left null and no `polygon_area_km2` is recorded since none is measured, so nothing here should be read as evidence about size beyond the description below.

**Why this entry exists:** The pipeline's routing decision (unit_id COL-CUNDINAMARCA) identified 66 rows spanning 1915-2023 labelled with a Cundinamarca-specific admin name in Colombian country data (source: juan-subnational), previously matched only to the national COL-1922-2025 row (or COL-1903-1922 for any rows falling before 1922), which is a national total for the whole of Colombia and therefore roughly 50 times Cundinamarca's own area (Colombia ~1,141,748 km2; Cundinamarca ~22,605 km2). No existing polity in the table IS Cundinamarca specifically — the four COL-* rows are successive national eras (Gran Colombia to 1830, Colombia to 1903, 1903-1922, 1922-2025) and none represents the department alone. Cundinamarca's status as a distinct, continuously-existing administrative unit since 1886 is confirmed by the same constitutional history documented for Antioquia: the 1886 Constitution replaced the federal Estados Unidos de Colombia's sovereign states (including the Estado Soberano de Cundinamarca) with departments under a unitary republic, and Cundinamarca has remained one of Colombia's departments ever since, with continuous departmental government and its own DANE statistical reporting. This mirrors sibling departments (Antioquia, Atlántico, Bolívar, Boyacá, Caldas, Cauca) this same pipeline pass resolved to create_new for the identical reason: a reporting unit smaller than the national total, with no existing polity representing it, and — per the routing decision — none of the four listed departure patterns (Sucre; the 1991 new departments; Quindío/Risaralda; Cesar) apply to Cundinamarca either.

**Territory description:** Cundinamarca is a department in the central Colombian Andes surrounding the national capital, Bogotá (though Bogotá itself has been a separate Capital District, not part of the department, since 1991). On a modern map it is bounded by Boyacá to the northeast, Meta to the southeast, Tolima and Huila to the southwest, Caldas to the west, and Antioquia and Santander to the north/northwest. Its present-day departmental area (excluding Bogotá D.C.) is approximately 22,605 km2, roughly 2% of Colombia's total ~1,141,748 km2. Unlike Antioquia's broadly stable boundary, Cundinamarca's territory is complicated by Bogotá's staged administrative separation — first as a special district in 1954, then as a fully autonomous Capital District under the 1991 Constitution — a boundary change this entry does not attempt to model against the 1915-2023 data span it receives (see the open questions below).

## Predecessors and successors

No predecessor or successor rows are set. Cundinamarca does not descend from a distinct prior polity in this table — like Antioquia, its pre-1886 existence as a sovereign federal state (Estado Soberano de Cundinamarca under the 1863 Estados Unidos de Colombia constitution) is administratively continuous with the post-1886 department, so no predecessor edge is drawn. It has no successor because it remains a current department as of the 2025 end_year convention used across this table for still-open subnational units. Note that Bogotá's administrative separation from the department (special district in 1954, full Capital District in 1991) is not modelled as a predecessor/successor split here — see the open question on whether Bogotá-labelled source data needs its own row.

## Sourced claims

- Colombia's 1886 Constitution replaced the federal Estados Unidos de Colombia (1863-1886), under which Cundinamarca held sovereign-state status as the Estado Soberano de Cundinamarca, with a unitary republic organized into departments, of which Cundinamarca was one from the outset.
- Cundinamarca's approximate present-day area is 22,605 km2 per standard Colombian departmental references (DANE/IGAC), versus Colombia's national total of approximately 1,141,748 km2 — the department is about 2% of the country, meaning routing its data to the national COL-* rows overstates its territory roughly 50-fold.
- Bogotá, Cundinamarca's capital and largest city, was carved into a special administrative district (Distrito Especial) in 1954 and became a fully autonomous Capital District (Distrito Capital) no longer part of the department under the 1991 Constitution, per Colombian constitutional and administrative history.

## Decisions

### d-follow-dominant-iso3-subunit-pattern

**Used <ISO3>-<SUBUNIT>-<start>-<end> rather than a bespoke code**

The polity code is COL-CUNDINAMARCA-1886-2025, following the dominant 57-of-66 pattern for subnational rows (e.g. ESP-AS-1833-2025, DZA-CVD-1902-1919, and the sibling COL-ANTIOQUIA-1886-2025 created in this same pipeline pass) rather than a bespoke name-only code. Cundinamarca is a standard department within Colombia's standing national administrative hierarchy, not a historical territory with a name and identity independent of the containing state the way Alaska Territory or Hyderabad State were, so the bespoke-code exception (3 of 66 rows) does not apply. The subunit token CUNDINAMARCA is spelled out in full rather than abbreviated, matching the choice already made for COL-ANTIOQUIA, since no short-code convention exists yet for COL subunits in this table.

### d-container-tiles-full-span

**Container chain covers 1886-2025 across three national eras with no gap**

Cundinamarca's 1886-2025 span crosses three successive national containers already present in the polity table: COL-1830-1903 (covering 1886-1903), COL-1903-1922 (covering 1903-1922), and COL-1922-2025 (covering 1922-2025, still current). One container edge is recorded per era, together tiling the full span with no gap, matching the treatment of sibling entry COL-ANTIOQUIA-1886-2025 and following the same national-era boundaries (Panama's 1903 secession, the 1922 US-Colombia treaty ratification) the existing COL rows already use to segment Colombia's own history. The routing decision's proposed container_code (COL-1922-2025) alone would leave 1886-1922 uncontained, which is why the two earlier eras were added here rather than following the proposal literally.

### d-start-year-1886-not-1922

**Used 1886, not the routing decision's own start_year proposal, verbatim**

The routing decision's span_basis argues for a 1886 start (Cundinamarca as an original 1886-Constitution department, like Antioquia, with no departure event) and its proposed.start_year field is indeed 1886 — this page follows that proposal exactly. It is noted here only because the proposed.container_code field (COL-1922-2025) names just the final era; treating that single container as the whole containment chain would have left 1886-1922 uncontained, which the containment gate rejects. The chosen fix was to keep the proposed start_year and end_year but expand the container list to the three-era chain described above, exactly as was done for the Antioquia entry with an identical proposal shape.

## Open questions

### oq-gadm-col-fetch-pending

**GADM Colombia ADM1 data has not actually been fetched**

polygon_status is unassigned because gadm-4.1-adm1.gpkg's locally cached subset covers only 81 countries and Colombia is not among them (0 features for COL in the current cache), exactly the situation documented for sibling entry COL-ANTIOQUIA-1886-2025. Until gadm41_COL_1 is fetched from gadm.org and added to the local source cache, this entry and its Colombian department siblings (Antioquia, Atlántico, Bolívar, Boyacá, Caldas, Cauca) have no polygon at all, not even a proxy. It is also unconfirmed whether GADM's present-day Cundinamarca boundary differs from the department's 1886-1954 extent, given that Bogotá D.C. was administratively separated from the department in stages (a Distrito Especial from 1954, made a fully independent Capital District, Bogotá D.C., under the 1991 Constitution) — a modern GADM Cundinamarca polygon may well exclude Bogotá while historical data before 1954 or before 1991 may have reported Bogotá as part of Cundinamarca's territory.

### oq-bogota-separation-affects-data-routing

**Whether Bogotá-labelled rows in the 1915-2023 source data should route here or to a separate Bogotá D.C. entry**

Cundinamarca's capital, Bogotá, was progressively separated from the department administratively: given special-district status in 1954 (absorbing several surrounding municipalities) and made a fully autonomous Capital District under the 1991 Constitution, no longer part of Cundinamarca for departmental-government purposes even though it remains geographically enclosed by it. The data span this entry captures (1915-2023, 66 rows per the routing decision) predates and postdates that separation. If any of the underlying rows are labelled distinctly as Bogotá/Bogotá D.C. rather than Cundinamarca, they may need their own polity row rather than being folded into this one, and conversely, pre-1954 Cundinamarca-labelled data likely includes Bogotá's territory and statistics in a way that post-1991 Cundinamarca data does not, which this entry does not attempt to segment.
