---
polity_code: COL-RISARALDA-1966-2025
polity_name: Risaralda (department of Colombia)
start_year: 1966
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
    start_year: 1966
    end_year: 2025
    basis: Risaralda has existed as a department inside the national Republic of Colombia continuously since its creation in 1966; the containing national polity's own span (1922-2025) fully covers this interval.
---

# Risaralda (department of Colombia)

## Summary

Risaralda is a department of Colombia located in the west-central part of the country, in the Coffee Axis (Eje Cafetero) region, bordered by Caldas, Quindío, Valle del Cauca, and Chocó, with its capital at Pereira. It was created on 1 December 1966 when the historical department of Caldas (sometimes called "Gran Caldas") was split into three: Caldas, Quindío, and Risaralda. This entry is typed `subnational` because Colombia has held continuous national sovereignty over this territory throughout; the department is a sub-national administrative and statistical reporting unit within the Colombian state, not an independent polity, and the entry exists to carry department-level data series distinct from Colombia's national totals — mirroring how other Colombian departments (e.g. Casanare, Cundinamarca, Nariño) are modeled in this database. The span starts in 1966, the year of the department's formal creation, and runs open-ended to 2025 since Risaralda remains an active, unchanged department of Colombia today. Data for years before 1966 that is nonetheless keyed to Risaralda's territory is a back-cast allocation of pre-existing national or Caldas-era totals onto the modern departmental boundary, not a record of an administratively distinct Risaralda, and is routed here as `back_cast` per the same convention used for COL-CASANARE's pre-1991 years.

**Why this entry exists.** Input data: a Colombia-labeled series keyed to the modern department of Risaralda, spanning at minimum 1966-2025 for the department's active period, plus back-cast years 1915-1965 (composition reported as 73.9% interpolated_scaled + 24.1% scaled) allocating earlier national/Caldas totals onto Risaralda's boundary; exact row counts were not stated in the routing decision and should be confirmed directly against the source table (see oq-back-cast-share-not-verified). This data was previously unrouted (matched_polity_code: null) and would otherwise have fallen through to the national COL-1922-2025 row, which is wrong because it conflates a department covering roughly 4,140 km2 with the whole of Colombia (over 1.1 million km2), destroying the sub-national resolution the source data actually carries. What confirms Risaralda is a distinct reporting entity rather than an artefact of this pipeline: Colombia's DANE administrative structure and departmental statistical yearbooks report Risaralda separately from Caldas and from national totals from 1967 onward, consistent with its formal creation as a department on 1 December 1966 (a date taken from general historical knowledge per the routing decision and still needing corroboration against a repository source, per oq-1966-creation-date-uncorroborated).

## Territorial extent

**Polygon status:** Not yet assigned. No polygon available in the GeoPackage for this period. The registered `gadm-4.1-adm1` source family is the correct one for a Colombian department boundary, but the GADM adm1 extract present in this repository's local geodata is restricted to a subset of 81 countries that does not include Colombia. `polygon_source` is therefore set to the registered slug `gadm-4.1-adm1` (not "none" and not a route name) with `polygon_status: unassigned`, following the `registered_source_unfetched` route: the source is registered and almost certainly holds a Risaralda feature, it simply has not been fetched into this repository yet. Fetching the full global `gadm41_adm1.gpkg` (or a Colombia-specific DANE/DIVIPOLA admin-1 dataset) is required before a `polygon_feature_id` can be populated — see open question oq-gadm-col-extract-needed, including a licence check on GADM's redistribution terms.

**Why this entry exists.** No existing polity in this database represents Risaralda or its Caldas-era predecessor territory. The department was created in 1966, and prior to that its territory was part of the department of Caldas, which itself has no dedicated polity row here — so time series keyed to Risaralda (whether reporting the modern department directly, or a back-cast allocation onto its boundary for years before 1966) had nowhere correct to route and would otherwise have been mismatched onto the whole-of-Colombia national row (COL-1922-2025), overstating the reporting territory by roughly two orders of magnitude. Colombia's own DANE administrative gazetteer and departmental statistical yearbooks treat Risaralda as a distinct reporting department from 1967 onward (the first full year after its December 1966 creation), which is the historical confirmation that this is a genuinely separate administrative and statistical entity, not merely a subset of Caldas continuing under a new name.

**Territory description.** Risaralda occupies roughly 4,140 km2 in the Coffee Axis region of west-central Colombia, in the Central and Western Cordilleras of the Andes, with Pereira as its capital and other notable towns including Dosquebradas and Santa Rosa de Cabal. On a modern map it sits between Caldas to the north/east, Quindío and Valle del Cauca to the south, and Chocó to the west, and is one of Colombia's smallest departments by area but among its more densely populated due to the coffee economy. No polygon is yet attached to this entry (see above), so the ~4,140 km2 figure is a reference figure drawn from modern Colombian administrative statistics (DANE), not a measurement of any geometry in this database.

## Predecessors and successors

Risaralda has no predecessor polity code in this database: it was created in 1966 by splitting the historical department of Caldas (with Quindío) into three, and Caldas is not currently modeled as its own polity row here, so the split leaves no entity on this side of the boundary to link backward to. It has no successor: Risaralda remains a current department of Colombia with unchanged status through 2025, the open end_year reflecting that it is still active. Should a COL-CALDAS entry be created later to carry Caldas's pre-1966 and residual post-1966 history, this page's predecessor field would be updated to point to it, and the 1915-1965 back-cast years discussed below might move there instead.

## Sourced claims

- Risaralda was constituted as a department of Colombia on 1 December 1966, split off from the former department of Caldas (per the routing decision's span_basis, based on general historical knowledge of Colombian administrative history, not yet corroborated against a document in this repository — see open question oq-1966-creation-date-uncorroborated).
- The pre-1966 years (1915-1965) of data routed to this polity code are a back-cast reconstruction, composed of 73.9% interpolated_scaled and 24.1% scaled values, allocating national or regional totals onto Risaralda's later administrative boundary rather than observing an administratively distinct Risaralda that did not yet exist.

## Decisions

### d-code-follows-dominant-pattern

**Code follows the ISO3-SUBUNIT-start-end pattern, not a bespoke name**

Risaralda is an ordinary Colombian department created by a routine 1966 territorial split from Caldas, not a historical territory with its own name recognized independently of the modern country (unlike ALK or HYD). With zero existing COL subnational rows to set precedent, the dominant table pattern (57 of 66 subnational rows use <ISO3>-<SUBUNIT>-<start>-<end>) applies directly: COL-RISARALDA-1966-2025. No departure from convention is warranted here.

### d-no-predecessor-polity

**No predecessor code recorded despite pre-1966 back-cast data**

The routing decision assigns 1915-1965 back-cast rows (allocations of national/regional totals onto Risaralda's later boundary) to this same polity code, matching how COL-CASANARE handled its pre-1991 back-cast years. Since Caldas itself (the department Risaralda split from) is not currently modeled as its own polity row in this database, there is no polity code to list as a predecessor. If a Caldas entry is created later, this page's predecessor field and the routing of the back-cast years should be revisited, as the routing_concerns note flags.

### d-polygon-route-unassigned

**polygon_source set to the registered slug gadm-4.1-adm1 with status unassigned**

The routing decision's polygon_route is registered_source_unfetched: GADM 4.1 adm1 is a registered source family and almost certainly carries a Risaralda department feature, but the locally present GADM extract is restricted to 81 countries and Colombia is not among them. Per the harness rule for this route, the slug itself is the polygon_source (not 'none' and not a route name), and polygon_status is set to unassigned rather than proxy or assigned, since no feature_id can be populated until the full global adm1 layer (or a Colombia-specific extract) is fetched.

## Open questions

### oq-gadm-col-extract-needed

**Full GADM 4.1 adm1 layer (or a Colombia-specific DANE/DIVIPOLA source) must be fetched to assign a polygon**

The locally present gadm-4.1-adm1 file is a subset covering only 81 countries, and Colombia is not one of them, so no polygon_feature_id can be populated today even though GADM almost certainly publishes Risaralda's department boundary. Fetching the full global gadm41_adm1.gpkg, or sourcing a DANE/DIVIPOLA Colombia admin-1 dataset instead, is required before this page can move from polygon_status: unassigned to assigned. GADM's data licence (which restricts redistribution and commercial use) should be checked for compatibility before it is adopted, per the routing_concerns note in the underlying decision.

### oq-1966-creation-date-uncorroborated

**The 1 December 1966 creation date is not yet corroborated against a document in this repository**

The span_basis for start_year=1966 relies on general historical knowledge that Risaralda was constituted as a department by splitting from Caldas on 1 December 1966, but the routing decision explicitly flags this as taken from background knowledge rather than a source document held in this repo. A Colombian administrative-history source (e.g. DANE's departmental gazetteer, or Colombia's Ley 70 de 1966 creating the department) should be located and cited to confirm both the exact date and that no earlier or later effective date applies.

### oq-caldas-predecessor-not-modeled

**Caldas (Gran Caldas), the department Risaralda split from, has no polity row of its own**

Risaralda was carved out of the historical 'Gran Caldas' department along with Quindío, both created in 1966. If a COL-CALDAS polity is created later to carry Caldas's own pre-split and post-split history, the pre-1966 back-cast years currently routed onto this page (1915-1965, per the routing decision) may belong on that Caldas entry instead, and this page's container/predecessor fields would need updating. This mirrors the same open question already live for Quindío's sibling department if it exists as a page.

### oq-back-cast-share-not-verified

**The reported back-cast composition (73.9% interpolated_scaled + 24.1% scaled) has not been independently re-derived for this entry**

The routing decision states the pre-1966 data for this territory is 73.9% interpolated_scaled and 24.1% scaled, but per the project's own methodology (never pin a figure from memory or from an upstream decision without recomputing it), this composition should be verified directly against the source data tables before it is treated as settled, since the remaining ~2% and the exact row count are not stated anywhere in the decision.
