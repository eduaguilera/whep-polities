---
polity_code: ARG-SANTACRUZ-1955-2025
polity_name: Santa Cruz (province of Argentina)
start_year: 1955
end_year: 2025
type: subnational
iso3: ARG
continent: South America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: gadm-4.1-adm1
polygon_feature_id: ARG.20_1
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: ARG-1902-2025
    start_year: 1955
    end_year: 2025
    basis: Santa Cruz was one of the national territories held directly under the Argentine national government; it was granted full provincial status by Law 14.408 in 1955 and has remained a province of Argentina within this national territory chain through the present.
---

# Santa Cruz (province of Argentina)

## Summary

Santa Cruz is a province of Argentina occupying the southern portion of Patagonia, bordered by Chile to the west and south, the Atlantic Ocean to the east, and the province of Chubut to the north. This entry captures Santa Cruz from 1955, when national Law 14.408 converted it from a directly-administered national territory (Territorio Nacional de Santa Cruz, held under a national-government-appointed governor since the 1880s) into a full province with its own elected government, through to the present (open end_year of 2025, following the convention used elsewhere in the table for still-current administrative units, e.g. ARG-CHUBUT-1884-2025). `type: subnational` reflects that this is a first-order administrative division of a sovereign state, not an independent polity — Argentina held sovereignty over this territory continuously before, during, and after this span; what changed in 1955 was Santa Cruz's internal administrative status within Argentina, from territorio nacional to provincia, alongside its sister territory Chubut in the same legislative act.

**Why this entry exists.** Input data: the routing decision for unit_id ARG-SANTACRUZ (admin_name "Santa Cruz", country Argentina) identifies this as one of the country's explicit departure cases requiring a new polity — a province created by provincialization law in 1955. The decision does not itemize a row count or specific source table in this pass; it establishes the routing/creation need based on Argentina's known administrative history (the 1955 provincialization wave alongside Chubut) rather than a specific dataset excerpt, so the row-count/source-label detail that would normally appear here is not available from this decision object and is flagged as a gap for whoever ingests actual Santa Cruz statistics into this row. Previously matched to: prior to this entry's creation, any Santa Cruz-labeled data for 1955 onward would have had no dedicated provincial row and would default to routing at the national ARG level, which conflates a specific province's statistics with all-Argentina totals — wrong because Santa Cruz from 1955 has its own distinct administrative and statistical identity as a province, separate from other provinces and from the national aggregate. Confirmation of distinctness: Argentine national law (Law 14.408, 1955) itself formally created Santa Cruz as a province distinct from its prior status as a national territory, and distinct from sibling provinces such as Chubut created in the same act — this is a legally and administratively documented act of creating a new first-order subnational unit, not merely a naming variant of an existing one.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is currently attached in the GeoPackage for this period; `polygon_status: unassigned` and `polygon_feature_id` is null. The intended source is `gadm-4.1-adm1` (GADM 4.1, administrative level 1), which is the registered source category this repository uses for exactly this kind of feature — a country's first-order administrative subdivision — but the locally fetched copy of that dataset (data/geodata/gadm-4.1/gadm41_adm1.gpkg) is a curated subset covering only 81 countries and does not include Argentina at all. This is a `registered_source_unfetched` case: the correct source is named and registered, it simply is not present on disk for this country yet, so no feature id can be supplied until the global GADM adm1 layer (or an Argentina-inclusive subset of it) is fetched. See open question oq-polygon-source-unfetched-gadm.

**Why this entry exists:** the routing decision names Santa Cruz as an explicit departure case — an ex-territorio nacional granted full provincial status in 1955 (Law 14.408), in the same wave as Chubut. No existing polity in the table IS this territory as a province; the only ARG rows available before this entry were national-level totals, which is the wrong container for provincial-level statistics collected on Santa Cruz specifically from 1955 onward. This entry gives that reporting unit its own row.

**Territory description:** a reader can locate Santa Cruz on a modern map as Argentina's southernmost mainland province, lying between roughly 46°S and 52°S, stretching from the Andes and the Chilean border in the west to the Atlantic coast in the east, with Chubut Province immediately to the north and the Strait of Magellan / Tierra del Fuego to the south. Its modern administrative area is approximately 243,943 km² (a widely cited official figure for the province, not a measurement derived from any geometry attached to this entry, since none is attached yet). The province's boundaries have been broadly stable since the 1880s definition of the national territory, with the main open question being whether any minor boundary adjustments occurred at or after the 1955 provincialization — not addressed here since no polygon is yet attached to check against.

## Predecessors and successors

This entry has no declared predecessor or successor edges. Territorially, its predecessor is the pre-1955 national-territory-era Santa Cruz, whose data is currently folded into ARG-1902-2025 rather than given its own row (see open question oq-pre1955-national-territory-granularity); that relationship cannot yet be declared as a formal predecessor edge because ARG-1902-2025 does not list this page as a successor (see oq-arg1902-successor-edge-missing). No successor exists because the province continues to the present day under the same administrative identity, matching the open end_year convention already used for its sibling ARG-CHUBUT-1884-2025.

## Sourced claims

- Law 14.408, enacted in 1955, granted full provincial status to the national territories of Santa Cruz and Chubut, ending their administration as territorios nacionales governed by a national-government-appointed governor rather than an elected provincial government.
- Argentina's Territorio Nacional de Santa Cruz was created in 1878 (organized under Ley 1532 of 1884 alongside the other Patagonian territories) and existed as a directly-administered national territory until the 1955 provincialization, meaning this entry's 1955 start_year marks a change in administrative status, not the territory's first appearance in Argentine administration.

## Decisions

### d-code-argsantacruz-1955-2025

**Code chosen as ARG-SANTACRUZ-1955-2025, following the dominant <ISO3>-<SUBUNIT>-<start>-<end> pattern**

351 subnational rows in the table show 338 following <ISO3>-<SUBUNIT>-<start>-<end> (e.g. ARG-CHUBUT-1884-2025, ARG-CORDOBA-1853-2025), against only 5 bespoke codes reserved for territories whose historical identity is independent of any modern country subdivision naming (ALK, CAL, HAW). Santa Cruz is not such a case: it is a straightforward Argentine province, administratively parallel to Chubut, which already has the code ARG-CHUBUT-1884-2025 in the existing table. There is no reason to depart from the dominant convention, so ARG-SANTACRUZ-1955-2025 was chosen, matching the ISO3 prefix and start/end years required by the containment gate (1955 inclusive start, 2025 exclusive-as-open-end per the country's open end_year convention already used for ARG-CHUBUT and ARG-1884-1951's siblings).

### d-dropped-predecessor-claim

**Dropped the predecessor:[ARG-1902-2025] claim instead of asserting a one-directional edge**

The routing decision proposed treating ARG-1902-2025 as this polity's territorial predecessor (Santa Cruz's pre-1955 data, when it was administered as a national territory rather than a province, is folded into that national row). But ARG-1902-2025's own successor list does not name this page, and validate_chain_integrity rejects edges asserted from only one side. Since this page cannot edit ARG-1902-2025, the predecessor field is left empty here and the asymmetry is recorded instead as an open question naming the exact edit ARG-1902-2025 would need (adding ARG-SANTACRUZ-1955-2025 to its successor list) rather than silently dropping the historical relationship.

## Open questions

### oq-arg1902-successor-edge-missing

**ARG-1902-2025 does not list this page as a successor, so the predecessor relationship is asserted from only one side**

This page's territory was, before 1955, part of the national territory of Santa Cruz administered directly by the Argentine national government and reported inside the national-level data captured by ARG-1902-2025. That is a genuine predecessor relationship — the same land, before it acquired its own provincial administrative identity — but it cannot be declared here as `predecessor: [ARG-1902-2025]` because that page's `successor` list does not name ARG-SANTACRUZ-1955-2025, and validate_chain_integrity rejects any edge only one side asserts. The fix is an edit to ARG-1902-2025 (and likely its siblings for the other 1955-wave provincializations, e.g. Chubut) adding ARG-SANTACRUZ-1955-2025 to its successor array. Until that edit lands, this page's predecessor field stays empty, meaning any reader building the territorial lineage from this page alone would incorrectly conclude Santa Cruz appears from nothing in 1955.

### oq-polygon-source-unfetched-gadm

**No polygon is attached because GADM 4.1 admin-1 does not include Argentina in this repository's local copy**

The routing decision explains that the standard registered source for provincial boundaries, gadm-4.1-adm1, is listed in scripts/sources.yaml but the locally fetched file (data/geodata/gadm-4.1/gadm41_adm1.gpkg) is a curated subset of only 81 countries that excludes Argentina entirely — zero matching rows. This is a `registered_source_unfetched` situation, not a case where the boundary doesn't exist: GADM globally does digitise Santa Cruz province. Until either the global gadm41_adm1.gpkg is re-fetched or Argentina is added to the local subset, `polygon_status` stays `unassigned` and `polygon_feature_id` is null. Once fetched, the feature should also be checked for vintage risk: GADM 4.1 reflects present-day boundaries, and while Santa Cruz's borders have been broadly stable since 1955, this should be confirmed rather than assumed.

### oq-pre1955-national-territory-granularity

**Whether pre-1955 Santa Cruz data deserves its own national-territory-era polity is unresolved**

The routing decision itself flags this as a concern: data from 1900-1954, when Santa Cruz existed as a national territory (Territorio Nacional de Santa Cruz) rather than a province, is currently routed to the national-level ARG polity rather than to a distinct pre-1955 'Santa Cruz (national territory)' entry. This may undercount subnational granularity for that 55-year window, during which Santa Cruz already had its own territorial governor and administrative boundaries distinct from other national territories (e.g. Chubut, also provincialized in 1955). Whether this warrants a separate predecessor polity is a broader policy question about how the 1900-1954 national-territory era should be represented across all provinces created by the 1955 provincialization wave, not something this single page's creation should decide unilaterally.
