---
polity_code: COL-CALDAS-1905-2025
polity_name: Caldas (department of Colombia)
start_year: 1905
end_year: 2025
type: subnational
iso3: COL
continent: South America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: gadm-4.1-adm1
polygon_feature_id: COL.8_2
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: COL-1903-1922
    start_year: 1905
    end_year: 1922
    basis: Caldas was created as a department in 1905 by Colombian law from territory of Antioquia, Tolima and Cauca, within the national era bounded by Panama's 1903 secession and the 1922 US-Colombia treaty ratification
  - code: COL-1922-2025
    start_year: 1922
    end_year: 2025
    basis: Caldas remains a current department of Colombia within the modern national row, open-ended (end_year 2025) as the still-current polity
---

# Caldas (department of Colombia)

## Summary

Caldas is a department in west-central Colombia, in the heart of the country's coffee-growing region, whose capital is Manizales. It was created in 1905 by Colombian law, carved from territory previously belonging to the departments of Antioquia, Tolima and Cauca, as part of the early-20th-century wave of new department creations under the 1886 unitary constitution. This entry is `type: subnational` because Caldas was never a sovereign state — Colombia held sovereignty throughout 1905-2025 — but Caldas is nonetheless a distinct reporting and administrative unit that agricultural, trade, and population statistics are tabulated against separately from national Colombia totals, particularly given its central role in Colombian coffee production. The row exists to carry that department-level reporting territory, not to compete with the national COL chain for sovereignty ranking. Caldas's start_year of 1905 reflects its legal creation date rather than an earlier date, since the department did not exist as an administrative unit before then; its end_year of 2025 is the open convention value used across this table for still-current, unabolished subnational units, mirroring sibling department entries for Antioquia, Boyacá, Atlántico and Bolívar resolved the same way in this pipeline pass.

**Why this entry exists.** The pipeline's routing decision (unit_id COL-CALDAS) identified rows labelled with a Caldas-specific admin name in Colombian country data, dated 1915-2023, previously matched only to the national COL-1922-2025 row, which is a national total for the whole of Colombia and therefore roughly 145 times Caldas's present-day area (Colombia ~1,141,748 km2; Caldas ~7,888 km2). No existing polity in the table IS Caldas specifically — the four COL-* national-era rows (Gran Colombia to 1830, Colombia to 1903, 1903-1922, 1922-2025) are successive national totals and none represents the department alone. Caldas's status as a distinct, continuously-existing administrative unit since 1905 is confirmed by Colombian administrative history: it was created by national law from territory of Antioquia, Tolima and Cauca as part of the early-20th-century department-creation wave, and has remained a department (with its own statistical reporting by DANE) ever since, notwithstanding the 1966 split-off of Quindío and Risaralda from its original territory. This mirrors sibling departments (Antioquia, Boyacá, Atlántico, Bolívar) this same pipeline pass resolved to create_new for the identical reason: a reporting unit far smaller than the national total, with no existing polity representing it.

## Territorial extent

**Polygon:** `polygon_status: unassigned`. The routing decision classified this as `registered_source_unfetched`: `gadm-4.1-adm1` is already the registered source family this repository uses for other countries' ADM1-level department/province polygons, but the locally cached `gadm-4.1-adm1.gpkg` is a subset covering only 81 countries and Colombia is not among them (0 features for COL in the current cache). The remedy is to fetch Colombia's ADM1 data from GADM (e.g. `gadm41_COL_1` from gadm.org, same CC-BY-NC licence already governing this source family) rather than construct a new source or borrow a polygon from elsewhere, matching the same unresolved gap already documented on sibling entries COL-ANTIOQUIA-1886-2025 and COL-BOYACA-1886-2025. No polygon is assigned by this page; `polygon_feature_id` is left null pending that fetch, and no `polygon_area_km2` is recorded since none is measured yet.

**Territory description:** Caldas is a department in west-central Colombia, part of the country's central coffee-growing axis, with capital Manizales. On a modern map it is bounded by Antioquia to the north, Boyacá and Cundinamarca to the east, Tolima to the southeast, Risaralda and Quindío to the south, and the Cauca River valley to the west. Its present-day area is approximately 7,888 km2, one of Colombia's smaller departments by area but among the most agriculturally significant given its coffee production. This present-day figure describes a substantially smaller territory than the department held between its 1905 creation and 1966, when Quindío and Risaralda were split off as separate departments — a mid-span territorial reduction this single-row entry does not model, and which is flagged as an open question below.

## Predecessors and successors

No predecessor or successor rows are set. Caldas does not descend from a distinct prior polity in this table — it was created directly by law in 1905 out of territory previously part of Antioquia, Tolima and Cauca departments, but those departments continue to exist as their own ongoing polities rather than being superseded, so no predecessor edge is drawn. Caldas has no successor because it remains a current department of Colombia as of the 2025 end_year used across this table for still-open subnational units, notwithstanding the 1966 territorial split described in the open questions below.

## Sourced claims

- Colombia's Department of Caldas was created in 1905 by national law from territory previously belonging to the departments of Antioquia, Tolima and Cauca, as part of a wave of new department creations in the early 20th century under the 1886 unitary constitutional framework.
- In 1966, the departments of Quindío and Risaralda were split off from Caldas's original territory, substantially reducing the department's area from its 1905-1966 extent to its present-day boundaries — a change this entry's single 1905-2025 span does not model as a territory break.

## Decisions

### d-follow-dominant-iso3-subunit-pattern

**Used <ISO3>-<SUBUNIT>-<start>-<end> rather than a bespoke code**

The polity code is COL-CALDAS-1905-2025, following the dominant 57-of-66 pattern for subnational rows (e.g. ESP-AS-1833-2025, DZA-CVD-1902-1919) rather than a bespoke name-only code, and matching the pattern already used for sibling entries COL-ANTIOQUIA-1886-2025 and COL-BOYACA-1886-2025 created in this same pass. Caldas is a standard department within Colombia's standing administrative hierarchy, not a historical territory with a name and identity independent of its containing state the way Alaska Territory or Hyderabad State were, so the bespoke-code exception (3 of 66 rows) does not apply. The subunit token CALDAS is spelled out in full, matching the full-name convention already established by the COL-ANTIOQUIA and COL-BOYACA sibling rows created in this same pipeline pass, rather than inventing an abbreviation.

### d-container-tiles-full-span

**Container chain covers 1905-2025 across two national eras with no gap**

Caldas's 1905-2025 span crosses two successive national containers already in the polity table: COL-1903-1922 (covering 1905-1922, since Caldas's 1905 creation postdates that era's own 1903 start) and COL-1922-2025 (covering 1922-2025, still current). One container edge is recorded per era, together tiling the full span with no gap, per the containment gate's requirement that each edge fall within both parties' own spans. Caldas was created in 1905, inside the 1903-1922 national era, so no earlier container edge (e.g. to COL-1830-1903) is needed or valid — unlike Antioquia and Boyacá, which predate 1903 and so require a third container edge into COL-1830-1903.

## Open questions

### oq-founding-law-not-verified

**1905 founding year and source law not verified against a primary Colombian source**

The proposed start_year of 1905 for Caldas's creation from parts of Antioquia, Tolima and Cauca is drawn from general historical knowledge of Colombian administrative history (the routing decision itself flags this as unverified), not from a primary source in this repository such as the founding law's number and date or a Colombian government gazetteer entry. If the precise founding date differs from 1905, or if the department was constituted in stages (e.g. an intermediate territorial status before full departmental status), the start_year and the polity code that encodes it would both need to change, and the code-year gate would need to be re-satisfied.

### oq-1966-split-territory-not-modelled

**1966 split-off of Quindío and Risaralda not reflected in this entry's territory or span**

Caldas's original 1905 boundaries included territory that was split off in 1966 to form the separate departments of Quindío and Risaralda (a significant reduction, not a minor municipal adjustment). This entry spans 1905-2025 as a single continuous row without a mid-span territory break, meaning any data routed here from before 1966 corresponds to a substantially larger area than a present-day GADM polygon for Caldas would show once fetched. Whether this warrants splitting the entry at 1966, or whether the underlying data being routed here is entirely post-1966 (making the question moot), is unresolved and should be checked against the actual rows once GADM Colombia ADM1 is fetched.

### oq-gadm-col-fetch-pending

**GADM Colombia ADM1 data has not actually been fetched**

polygon_status is unassigned because gadm-4.1-adm1.gpkg's locally cached 81-country subset excludes Colombia entirely (0 features), the same gap already documented on sibling entries COL-ANTIOQUIA-1886-2025 and COL-BOYACA-1886-2025. Until someone fetches gadm41_COL_1 from gadm.org and adds it to the local source cache, this entry has no polygon at all, not even a proxy. Even once fetched, GADM's current Caldas boundary reflects the post-1966 department (after Quindío and Risaralda split off), which would not correctly represent the department's larger 1905-1966 extent — see oq-1966-split-territory-not-modelled above.
