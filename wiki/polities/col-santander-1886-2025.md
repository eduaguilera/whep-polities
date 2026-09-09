---
polity_code: COL-SANTANDER-1886-2025
polity_name: Santander (department of Colombia)
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
polygon_feature_id: COL.28_2
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: COL-1830-1903
    start_year: 1886
    end_year: 1903
    basis: Santander was constituted as a department of the unitary Republic of Colombia under the 1886 Constitution, which this row's container COL-1830-1903 (Colombia to 1903) still covers at its tail end
  - code: COL-1903-1922
    start_year: 1903
    end_year: 1922
    basis: Santander continued as a department of Colombia through the 1903-1922 national era, bounded by Panama's 1903 secession and the 1922 US-Colombia treaty ratification
  - code: COL-1922-2025
    start_year: 1922
    end_year: 2025
    basis: Santander remains a current department of Colombia within the modern national row, open-ended (end_year 2025) as the still-current polity
---

# Santander (department of Colombia)

## Summary

Santander is a department of the Republic of Colombia in the northeastern Andes, capital Bucaramanga, constituted under the centralizing 1886 Constitution that replaced the earlier federal Estados Unidos de Colombia (1863-1886), in which Santander had existed as a sovereign federal state (the Estado Soberano de Santander). This entry is `type: subnational` because Colombia held sovereignty throughout 1886-2025 — Santander was never itself a sovereign state in the period this row covers — but it is nonetheless a distinct administrative and statistical reporting unit that agricultural, trade, and population data are tabulated against separately from national Colombia totals. The row exists to carry that department-level reporting territory rather than to compete with the national COL-* chain for sovereignty ranking in the matcher. Santander is a current, unabolished department (unlike the territorios nacionales only elevated to departments from 1991), so its span runs continuously from 1886 to the open end_year 2025 used for still-current subnational units in this table, mirroring the resolution already applied to sibling departments Antioquia, Atlántico, Bolívar, Boyacá, Caldas, and Cauca in the same pipeline pass.

**Why this entry exists.** The pipeline's routing decision (unit_id COL-SANTANDER) identified rows labelled with a Santander-specific admin name in Colombian country data spanning 1915-2023, previously matched only to the national COL-* rows (COL-1903-1922 or COL-1922-2025 depending on year), which are national totals for the whole of Colombia and therefore roughly 37 times Santander's own area (Colombia ~1,141,748 km2; Santander ~30,537 km2). No existing polity in the table IS Santander specifically — the four COL-* rows are successive national eras (Gran Colombia to 1830, Colombia to 1903, 1903-1922, 1922-2025) and none represents the department alone. Santander's status as a distinct, continuously-existing administrative unit since 1886 is confirmed by Colombia's own constitutional history: the 1886 Constitution replaced the federal Estados Unidos de Colombia's sovereign states (including the Estado Soberano de Santander) with departments under a unitary republic, and Santander has remained one of Colombia's departments ever since (after shedding Norte de Santander in 1910), with continuous departmental government and its own statistical reporting (DANE tabulates department-level series for Santander through the 20th and 21st centuries). This mirrors sibling departments (Antioquia, Atlántico, Bolívar, Boyacá, Caldas, Cauca) this same pipeline pass resolved to create_new for the identical reason: a reporting unit smaller than the national total, with no existing polity representing it, and mostly interpolated_scaled/scaled data that nonetheless describes a territory that existed continuously across the full 1915-2023 data span, requiring no back_cast split.

## Territorial extent

**Polygon:** `polygon_status: unassigned`. The routing decision classified this as `registered_source_unfetched`: `gadm-4.1-adm1` is the registered source family already used for other countries' ADM1-level department/province polygons in this repository, but the locally cached `gadm-4.1-adm1.gpkg` is a subset covering only 81 countries and Colombia is not among them (0 features for COL in the current cache). The remedy is to fetch Colombia's ADM1 data from GADM (e.g. `gadm41_COL_1` from gadm.org, same CC-BY-NC licence already governing this source family) rather than construct a new source or borrow a polygon from elsewhere. No polygon is assigned by this page; `polygon_feature_id` is left null pending that fetch, and no `polygon_area_km2` is recorded since none is measured yet — nothing here should be read as evidence about size beyond the description below.

**Territory description:** Santander is a department in the northeastern Colombian Andes along the Magdalena valley's eastern flank, capital Bucaramanga. On a modern map it is bounded by Norte de Santander to the northeast, Cesar and Bolívar to the north, Antioquia and Boyacá to the south, and Boyacá again to the east, with the Magdalena River forming much of its western boundary against Antioquia and Bolívar. Its present-day area is approximately 30,537 km2, about 2.7% of Colombia's national total of ~1,141,748 km2. The department's boundary has been broadly stable since the 1910 separation of Norte de Santander, though this entry does not attempt to model minor subsequent municipal boundary adjustments with neighbouring departments across its 1886-2025 span.

## Predecessors and successors

No predecessor or successor rows are set. Santander's pre-1886 existence as the Estado Soberano de Santander under the 1863 federal constitution is administratively continuous in name but not in territory with the post-1886 department, since the federal-era state's land was later split between this entry and Norte de Santander (separated 1910, present in the table as col-nortedesantander-1910-2025); rather than invent a predecessor edge that would misrepresent a 1:1 continuity that did not hold, none is drawn. Santander remains a current, unabolished department as of the table's 2025 end_year convention for still-open subnational units, so it has no successor.

## Sourced claims

- Colombia's 1886 Constitution replaced the federal Estados Unidos de Colombia (1863-1886), under which Santander held sovereign-state status as the Estado Soberano de Santander, with a unitary republic organized into departments, of which Santander was one from the outset.
- Norte de Santander was formally separated from Santander as its own department in 1910, meaning the pre-1886 federal-era Santander territory was materially larger than the department this entry represents; the split department is present in this table as col-nortedesantander-1910-2025.
- Santander's present-day area is approximately 30,537 km2 per standard Colombian departmental references (DANE/IGAC), versus Colombia's national total of approximately 1,141,748 km2 — the department is roughly 2.7% of the country, so routing its data to the national COL-* rows would overstate its territory by a factor of about 37.

## Decisions

### d-follow-dominant-iso3-subunit-pattern

**Code follows the dominant <ISO3>-<SUBUNIT>-<start>-<end> pattern**

COL-SANTANDER-1886-2025 follows the pattern used by 57 of 66 subnational rows in the table (e.g. ESP-AS-1833-2025, DZA-CVD-1902-1919) and matches the sibling Colombian department entries created in this same pass (COL-ANTIOQUIA, COL-BOYACA, COL-CAUCA, COL-ATL, COL-BOLIVAR, COL-CALDAS). Santander is a standing, unabolished department with no name of its own distinct from its administrative identity, so it does not qualify for a bespoke code the way ALK, HYD, or RYU do (historical territories whose names outlived or predated their administrative form). No existing COL subnational code precedent constrains this choice, since Colombia had zero subnational rows before this pipeline pass, so this entry and its siblings set that precedent together, consistently.

### d-start-year-default-rule

**start_year 1886 uses the default-constitution rule, not a confirmed founding date**

The routing decision's own routing_concerns flags that Santander's exact formal creation year as a department is not directly confirmed and is assumed at the 1886 floor per the default rule applied to all non-territorios-nacionales departments. This is the same assumption made for Antioquia, Boyacá, Cauca and other siblings resolved in this pass, so 1886 is used here for consistency with that established convention rather than as an independently verified date. If a more precise founding date surfaces (some Colombian departments trace formal boundaries to later 19th/20th-century legislation reorganizing the historical Estado Soberano de Santander), start_year should be revisited alongside the sibling rows, not this one in isolation.

## Open questions

### oq-santander-1857-federal-state-split

**Pre-1886 Santander was a federal sovereign state that later split into two departments**

Under the 1863 federal constitution, the Estado Soberano de Santander was one of the original nine sovereign states of the Estados Unidos de Colombia, covering territory that the 1886 unitary reorganization eventually split into two separate departments: Santander (this entry, capital Bucaramanga) and Norte de Santander (capital Cúcuta), the latter formally separated in 1910 and already present in this table as its own sibling row (col-nortedesantander-1910-2025). This means the pre-1886 federal-state territory was roughly double the area this entry represents from 1886 onward, and the exact year the two departments' administrative boundary was finalized (versus merely proposed) is not confirmed here. No predecessor edge is drawn from this row to the federal-era Estado Soberano de Santander because doing so would require deciding how to split that entity's data between two present-day departments, which this entry does not attempt.

### oq-santander-polygon-not-fetched

**GADM Colombia ADM1 data absent locally, no polygon feature assigned**

Same gap as every other Colombian department created in this pass: gadm-4.1-adm1 is the correct registered source family for department-level polygons, but the locally cached gadm41_adm1.gpkg subset covers only 81 countries and Colombia is not among them (0 COL features present). polygon_status is unassigned and polygon_feature_id is null pending an actual fetch of gadm41_COL_1 from gadm.org. Whether Santander's present-day GADM boundary reflects the post-1910 (post-Norte de Santander split) shape, or some earlier or later revision, is unverified until that fetch happens and the feature is inspected directly.
