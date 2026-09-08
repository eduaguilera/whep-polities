---
polity_code: COL-ANTIOQUIA-1886-2025
polity_name: Antioquia (department of Colombia)
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
    basis: Antioquia was constituted as a department of the unitary Republic of Colombia under the 1886 Constitution, which this row's container COL-1830-1903 (Colombia to 1903) still covers at its tail end
  - code: COL-1903-1922
    start_year: 1903
    end_year: 1922
    basis: Antioquia continued as a department of Colombia through the 1903-1922 national era (bounded by Panama's 1903 secession and the 1922 US-Colombia treaty ratification)
  - code: COL-1922-2025
    start_year: 1922
    end_year: 2025
    basis: Antioquia remains a current department of Colombia within the modern national row, open-ended (end_year 2025) as the still-current polity
---

# Antioquia (department of Colombia)

## Summary

Antioquia is one of the original departments of the Republic of Colombia, a mountainous region in the north-central Andes whose capital is Medellín. It was constituted as a department under the centralizing 1886 Constitution that replaced the earlier federal Estados Unidos de Colombia (in which Antioquia had existed as a sovereign federal state since 1863). This entry is `type: subnational` because Antioquia was never a sovereign state in the period this row covers — Colombia held sovereignty throughout 1886-2025 — but Antioquia is nonetheless a distinct reporting and administrative unit that agricultural, trade, and population statistics are tabulated against separately from national Colombia totals. The row exists to carry that department-level reporting territory, not to compete with the national COL chain for sovereignty ranking. Antioquia is a current, unabolished department (unlike the territorios nacionales only elevated to departments starting in 1991), so its span runs continuously from 1886 to the open end_year used for still-current subnational units, mirroring sibling entries for Atlántico, Bolívar, Boyacá, Caldas, and Cauca resolved the same way.

**Why this entry exists.** The pipeline's routing decision (unit_id COL-ANTIOQUIA) identified rows labelled with an Antioquia-specific admin name in Colombian country data, previously matched only to the national COL-* rows (COL-1903-1922 or COL-1922-2025 depending on year), which are national totals for the whole of Colombia and therefore roughly 18 times Antioquia's own area (Colombia ~1,141,748 km2; Antioquia ~63,612 km2). No existing polity in the table IS Antioquia specifically — the four COL-* rows are successive national eras (Gran Colombia to 1830, Colombia to 1903, 1903-1922, 1922-2025) and none represents the department alone. Antioquia's status as a distinct, continuously-existing administrative unit since 1886 is confirmed by Colombia's own constitutional history: the 1886 Constitution replaced the federal Estados Unidos de Colombia's sovereign states (including the Estado Soberano de Antioquia) with departments under a unitary republic, and Antioquia has remained one of Colombia's departments ever since, with continuous departmental government and its own statistical reporting (DANE tabulates department-level series for Antioquia back through the 20th century). This mirrors sibling departments (Atlántico, Bolívar, Boyacá, Caldas, Cauca) this same pipeline pass resolved to create_new for the identical reason: a reporting unit smaller than the national total, with no existing polity representing it.

## Territorial extent

**Polygon:** `polygon_status: unassigned`. The routing decision classified this as `registered_source_unfetched`: `gadm-4.1-adm1` is already the registered source family this repository uses for other countries' ADM1-level department/province polygons, but the locally cached `gadm-4.1-adm1.gpkg` is a subset covering only 81 countries and Colombia is not among them (0 features for COL in the current cache). The remedy is to fetch Colombia's ADM1 data from GADM (e.g. `gadm41_COL_1` from gadm.org, same CC-BY-NC licence already governing this source family) rather than construct a new source or borrow a polygon from elsewhere. No polygon is assigned by this page; `polygon_feature_id` is left null pending that fetch, and no `polygon_area_km2` is recorded since none is measured yet — nothing here should be read as evidence about size beyond the description below.

**Territory description:** Antioquia is a department in the north-central Colombian Andes, capital Medellín. On a modern map it is bounded by Córdoba and Sucre to the northwest, Bolívar to the north, Santander and Boyacá to the east, Caldas and Risaralda to the south, and Chocó to the west, with a short Caribbean coastline near the Gulf of Urabá. Its present-day area is approximately 63,612 km2 — larger than several South American countries but only about 5.6% of Colombia's total ~1,141,748 km2. Antioquia's boundary has been broadly stable since the department's formation, though minor municipal boundary adjustments with neighbouring departments have occurred across the 1886-2025 span that this entry does not attempt to model.

## Predecessors and successors

No predecessor or successor rows are set. Antioquia does not descend from a distinct prior polity in this table — its pre-1886 existence as the Estado Soberano de Antioquia under the 1863 federal constitution is administratively continuous with the post-1886 department (same core territory, same name, no rupture in the data being routed here), so no predecessor edge is drawn rather than inventing one without a data-backed reason. It has no successor because it remains a current department as of the 2025 end_year used across this table for still-open units.

## Sourced claims

- Colombia's 1886 Constitution replaced the federal Estados Unidos de Colombia (1863-1886), under which Antioquia held sovereign-state status as the Estado Soberano de Antioquia, with a unitary republic organized into departments, of which Antioquia was one from the outset.
- Antioquia's approximate present-day area is 63,612 km2 per standard departmental references (e.g. DANE/IGAC figures), versus Colombia's national total of approximately 1,141,748 km2 — the department is about 5.6% of the country, which is why routing its data to the national COL-* rows overstates its territory roughly 18-fold.

## Decisions

### d-follow-dominant-iso3-subunit-pattern

**Used <ISO3>-<SUBUNIT>-<start>-<end> rather than a bespoke code**

The polity code is COL-ANTIOQUIA-1886-2025, following the dominant 57-of-66 pattern for subnational rows (e.g. ESP-AS-1833-2025, DZA-CVD-1902-1919) rather than a bespoke name-only code. Antioquia is a standard department within a standing national administrative hierarchy, not a historical territory with a name and identity independent of its containing state the way Alaska Territory or Hyderabad State were before annexation/statehood, so the bespoke-code exception (3 of 66 rows) does not apply. The subunit token ANTIOQUIA is spelled out in full rather than abbreviated, since unlike the ESP-<province-code> siblings there is no existing short-code convention established for COL subunits in this table (this is the first COL subnational row), so the full name avoids inventing an arbitrary abbreviation.

### d-container-tiles-full-span

**Container chain covers 1886-2025 across three national eras with no gap**

Antioquia's 1886-2025 span crosses three successive national containers already in the polity table: COL-1830-1903 (covering 1886-1903), COL-1903-1922 (covering 1903-1922), and COL-1922-2025 (covering 1922-2025, still current). One container edge is recorded per era, together tiling the full span with no gap, per the containment gate's requirement that each edge fall within both parties' own spans. Panama's 1903 secession and the 1922 US-Colombia treaty ratification are the boundaries the existing COL national rows already use to segment Colombia's own history; Antioquia's containment simply follows those same era boundaries.

## Open questions

### oq-start-year-1886-vs-earlier

**Whether 1886 is the right start year versus an earlier federal-era date**

The proposed start_year of 1886 follows the country convention's default rule for Colombian departments (constitutional creation under the 1886 unitary reorganization), rather than treating Antioquia as continuous back through its 1863-1886 existence as a sovereign federal state (Estado Soberano de Antioquia) or further back to colonial-era provincial boundaries. If the underlying source data being routed to this entry contains Antioquia-labelled rows dated before 1886, either the start_year should move earlier (with a predecessor edge added, e.g. to a federal-era Antioquia row if later created) or those pre-1886 rows need a different routing decision entirely. This was flagged as an open concern in the routing decision itself and is not yet resolved against the actual data being matched.

### oq-gadm-col-fetch-pending

**GADM Colombia ADM1 data has not actually been fetched**

polygon_status is unassigned because gadm-4.1-adm1.gpkg's locally cached 81-country subset excludes Colombia entirely (0 features). Until someone fetches gadm41_COL_1 (shapefile or GeoJSON) from gadm.org and adds it to the local source cache, this entry and its sibling Colombian departments (Atlántico, Bolívar, Boyacá, Caldas, Cauca) have no polygon at all, not even a proxy. It is also unconfirmed whether GADM's current Antioquia boundary differs from the department's 1886-1930s extent — Colombian departmental boundaries have had minor adjustments (e.g. municipality transfers with neighbouring departments) that a present-day GADM polygon would silently paper over for the earliest decades of this span.
