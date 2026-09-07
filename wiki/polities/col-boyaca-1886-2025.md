---
polity_code: COL-BOYACA-1886-2025
polity_name: Boyacá (department of Colombia)
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
polygon_feature_id: null
polygon_feature_year: null
polygon_status: unassigned
predecessor: []
successor: []
container:
  - code: COL-1830-1903
    start_year: 1886
    end_year: 1903
    basis: Boyacá was constituted as a department of the unitary Republic of Colombia under the 1886 Constitution, which this row's container COL-1830-1903 (Colombia to 1903) still covers at its tail end
  - code: COL-1903-1922
    start_year: 1903
    end_year: 1922
    basis: Boyacá continued as a department of Colombia through the 1903-1922 national era (bounded by Panama's 1903 secession and the 1922 US-Colombia treaty ratification)
  - code: COL-1922-2025
    start_year: 1922
    end_year: 2025
    basis: Boyacá remains a current department of Colombia within the modern national row, open-ended (end_year 2025) as the still-current polity
---

# Boyacá (department of Colombia)

## Summary

Boyacá is one of the original departments of the Republic of Colombia, a department in the eastern Andean cordillera and adjoining llanos foothills whose capital is Tunja — historically significant as the site of the decisive 1819 Battle of Boyacá in the independence war. It was constituted as a department under the centralizing 1886 Constitution that replaced the earlier federal Estados Unidos de Colombia (in which Boyacá had existed as a sovereign federal state, the Estado Soberano de Boyacá, since 1857/1863). This entry is `type: subnational` because Boyacá was never a sovereign state in the period this row covers — Colombia held sovereignty throughout 1886-2025 — but Boyacá is nonetheless a distinct reporting and administrative unit that agricultural, trade, and population statistics are tabulated against separately from national Colombia totals. The row exists to carry that department-level reporting territory, not to compete with the national COL chain for sovereignty ranking. Boyacá is not among the country convention's departure list of territorios nacionales (Amazonas, Arauca, Casanare, Guainía, Guaviare, Putumayo, San Andrés) that were only elevated to departments later, so the default 1886 start rule applies and its span runs continuously to the open end_year (2025) used for still-current subnational units, mirroring sibling entries for Antioquia, Atlántico, and Bolívar resolved the same way. Unlike some siblings, however, Boyacá's own territorial extent is not simply "current department, unchanged since 1886": its eastern llanos frontier was carved off over the 20th century into the separate territorio nacional and later department of Casanare, so any polygon eventually assigned here needs to account for that shrinkage rather than treat the modern GADM boundary as valid for the whole span.

**Why this entry exists.** The pipeline's routing decision (unit_id COL-BOYACA) identified rows labelled with a Boyacá-specific admin name in Colombian country data (source: juan-subnational), previously matched only to the national COL-* rows (COL-1903-1922 or COL-1922-2025 depending on year), which are national totals for the whole of Colombia and therefore roughly 49 times Boyacá's own area (Colombia ~1,141,748 km2; Boyacá ~23,189 km2). No existing polity in the table IS Boyacá specifically — the four COL-* rows are successive national eras (Gran Colombia to 1830, Colombia to 1903, 1903-1922, 1922-2025) and none represents the department alone. Boyacá's status as a distinct, continuously-existing administrative unit since 1886 is confirmed by Colombia's own constitutional history: the 1886 Constitution replaced the federal Estados Unidos de Colombia's sovereign states (including the Estado Soberano de Boyacá) with departments under a unitary republic, and Boyacá has remained one of Colombia's departments ever since, with continuous departmental government and its own statistical reporting (DANE tabulates department-level series for Boyacá back through the 20th century). This mirrors sibling departments (Antioquia, Atlántico, Bolívar, Amazonas, Arauca) this same pipeline pass resolved to create_new for the identical reason: a reporting unit smaller than the national total, with no existing polity representing it, and not among the departure list (Amazonas, Arauca, Casanare, Guainía, Guaviare, Putumayo, San Andrés) of territorios nacionales elevated to departments later than 1886.

## Territorial extent

**Polygon:** `polygon_status: unassigned`. The routing decision classified this as `registered_source_unfetched`: `gadm-4.1-adm1` is already the registered source family this repository uses for other countries' ADM1-level department/province polygons, but the locally cached `gadm-4.1-adm1.gpkg` is a subset covering only 81 countries and Colombia is not among them (0 features for COL in the current cache). The remedy is to fetch Colombia's ADM1 data from GADM (e.g. `gadm41_COL_1` from gadm.org, same CC-BY-NC licence already governing this source family) rather than construct a new source or borrow a polygon from elsewhere. No polygon is assigned by this page; `polygon_feature_id` is left null pending that fetch, and no `polygon_area_km2` is recorded since none is measured yet — nothing here should be read as evidence about size beyond the description below.

**Territory description:** Boyacá is a department in the eastern Colombian Andes and adjoining llanos, capital Tunja. On a modern map it is bounded by Santander to the northwest, Arauca to the northeast, Casanare to the east and southeast, Cundinamarca to the south, and Caldas and Antioquia to the west. Its present-day area is approximately 23,189 km2, roughly 2% of Colombia's total ~1,141,748 km2. Unlike Antioquia, Boyacá's boundary has NOT been stable across the full 1886-2025 span: its eastern llanos territory was progressively organized as the separate national intendencia/comisaría of Casanare during the 20th century and made a full department in 1991, so a present-day GADM polygon for Boyacá understates the department's earlier, larger extent rather than merely approximating it with minor drift.

## Predecessors and successors

No predecessor or successor rows are set. Boyacá does not descend from a distinct prior polity in this table — its pre-1886 existence as the Estado Soberano de Boyacá under the 1863 federal constitution is administratively continuous with the post-1886 department (same core territory, same name, no rupture in the data being routed here), so no predecessor edge is drawn rather than inventing one without a data-backed reason. It has no successor because it remains a current department as of the 2025 end_year used across this table for still-open units. Note, however, that Boyacá's own territory was reduced in 1991 when Casanare — previously an intendencia carved partly from Boyacá's eastern llanos territory — was elevated to a full department in its own right; no successor edge is drawn for that split because Casanare is treated in this table's routing pass as its own distinct pre-1991 territorio nacional lineage, not as a fragment whose data continues to be filed under Boyacá after 1991.

## Sourced claims

- Colombia's 1886 Constitution replaced the federal Estados Unidos de Colombia (1863-1886), under which Boyacá held sovereign-state status as the Estado Soberano de Boyacá, with a unitary republic organized into departments, of which Boyacá was one from the outset.
- Boyacá's approximate present-day area is 23,189 km2 per standard departmental references (e.g. DANE/IGAC figures), versus Colombia's national total of approximately 1,141,748 km2 — the department is under 2.1% of the country, which is why routing its data to the national COL-* rows overstates its territory roughly 49-fold.
- Casanare, now a separate Colombian department bordering Boyacá to the southeast, was elevated to full department status in 1991 from territory that had previously been organized as a national intendencia/comisaría partly carved from Boyacá's eastern lowlands, meaning Boyacá's own boundary is not identical across the full 1886-2025 span this entry covers.

## Decisions

### d-follow-dominant-iso3-subunit-pattern

**Used <ISO3>-<SUBUNIT>-<start>-<end> rather than a bespoke code**

The polity code is COL-BOYACA-1886-2025, following the dominant 57-of-66 pattern for subnational rows (e.g. ESP-AS-1833-2025, DZA-CVD-1902-1919) rather than a bespoke name-only code. Boyacá is a standard department within Colombia's standing national administrative hierarchy, not a historical territory with a name and identity independent of its containing state the way Alaska Territory or Hyderabad State were before annexation/statehood, so the bespoke-code exception (3 of 66 rows) does not apply. The subunit token BOYACA is spelled out in full (without the accent, for ASCII safety in the code) rather than abbreviated, matching the sibling entry COL-ANTIOQUIA-1886-2025: this is among the first COL subnational rows and no short-code convention (like ESP's two-letter province codes) has been established for Colombian departments in this table, so the full name avoids inventing an arbitrary abbreviation this early in the country's subnational coverage.

### d-container-tiles-full-span

**Container chain covers 1886-2025 across three national eras with no gap**

Boyacá's 1886-2025 span crosses three successive national containers already in the polity table: COL-1830-1903 (covering 1886-1903), COL-1903-1922 (covering 1903-1922), and COL-1922-2025 (covering 1922-2025, still current). One container edge is recorded per era, together tiling the full span with no gap, per the containment gate's requirement that each edge fall within both parties' own spans. Panama's 1903 secession and the 1922 US-Colombia treaty ratification are the boundaries the existing COL national rows already use to segment Colombia's own history; Boyacá's containment simply follows those same era boundaries, identical in structure to sibling department COL-ANTIOQUIA-1886-2025.

## Open questions

### oq-start-year-1886-vs-earlier

**Whether 1886 is the right start year versus an earlier federal-era date**

The proposed start_year of 1886 follows the country convention's default rule for Colombian departments (constitutional creation under the 1886 unitary reorganization), rather than treating Boyacá as continuous back through its 1857-1886 existence as a sovereign federal state (Estado Soberano de Boyacá) under the earlier Estados Unidos de Colombia, or further back to its brief role as the seat of the 1863-1886 federal capital arrangements and colonial-era provincial boundaries around Tunja. If the underlying source data being routed to this entry contains Boyacá-labelled rows dated before 1886, either the start_year should move earlier (with a predecessor edge added to a federal-era Boyacá row if one is later created) or those pre-1886 rows need a different routing decision entirely. The routing decision's own routing_concerns field flags that Boyacá's administrative history was not independently verified beyond applying the country default rule, so this is not yet resolved against the actual data being matched.

### oq-gadm-col-fetch-pending

**GADM Colombia ADM1 data has not actually been fetched**

polygon_status is unassigned because gadm-4.1-adm1.gpkg's locally cached 81-country subset excludes Colombia entirely (0 features for COL in the current cache), exactly as documented in the routing decision's polygon_detail. Until someone fetches gadm41_COL_1 (shapefile or GeoJSON) from gadm.org and adds it to the local source cache, this entry and its sibling Colombian departments (Antioquia, Atlántico, Bolívar, Amazonas, Arauca, etc.) have no polygon at all, not even a proxy. It is also unconfirmed whether GADM's current Boyacá boundary differs from the department's 1886-era extent — Boyacá's territory has seen at least one significant loss, the 1991 constitutional creation of Casanare as a separate department from what had been Boyacá's eastern lowlands (Casanare intendencia/comisaría territory), meaning a present-day GADM polygon for Boyacá would understate the department's own 19th- and early-20th-century extent, not merely approximate it.
