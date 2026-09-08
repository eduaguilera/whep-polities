---
polity_code: ARG-SANLUIS-1853-2025
polity_name: San Luis (province of Argentina)
start_year: 1853
end_year: 2025
type: subnational
iso3: ARG
continent: South America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: gadm-3.6
polygon_feature_id: null
polygon_feature_year: null
polygon_status: unassigned
predecessor: []
successor: []
container:
  - code: ARG-1800-1899
    start_year: 1853
    end_year: 1899
    basis: San Luis was one of the historic provinces that ratified the 1853 Constitution and entered the Argentine Confederation/Republic; ARG-1800-1899 is the containing sovereign national row for this era.
  - code: ARG-1899-1902
    start_year: 1899
    end_year: 1902
    basis: Short bridging national-era container row between the 1899 and 1902 national polity boundaries; San Luis's provincial territory and status did not change across this transition.
  - code: ARG-1902-2025
    start_year: 1902
    end_year: 2025
    basis: San Luis remains a province of the modern Argentine Republic, represented from 1902 onward by the national row ARG-1902-2025, through to the present day.
---

# San Luis (province of Argentina)

## Summary

San Luis is one of the fourteen original provinces that constituted the Argentine Confederation and ratified the 1853 Constitution, located in the west-central Cuyo region of Argentina, bordering Mendoza to the west, Córdoba to the east, La Pampa to the south and La Rioja/Córdoba to the north. It is not a former territorio nacional promoted to province status in the twentieth century (unlike Chaco, Formosa, La Pampa, Misiones, Neuquén or Río Negro) and not a special federal district (unlike CABA) — it has held province-level status continuously since 1853, which is why this entry starts there rather than at a later provincialization date. `type: subnational` is used because San Luis was never sovereign in its own right within this span; sovereignty sits with the successive national ARG rows this entry is containered under, but statistical sources report production data at the province level distinct from the national ARG total, which is the reporting-territory rationale for giving it its own row. San Luis's economy historically centred on livestock (goats, cattle) and, from the mid-20th century, on industrial promotion zones and mining (dolomite, granite, gold); more recently wind-power generation and light manufacturing have become significant.

**Why this entry exists.** This entry captures province-level production/statistical data reported for San Luis, Argentina, spanning 1900-2023 per the routing decision (well within the 1853-2025 span), sourced from juan-subnational. Before this entry, no subnational polity existed for any Argentine province in this table except the six other Argentine provincial rows created alongside it (e.g. ARG-CORDOBA-1853-2025, ARG-CORRIENTES-1853-2025) - the ARG chain otherwise contained only national-level rows (ARG-1800-1899, ARG-1899-1902, ARG-1902-2025). Any San Luis-labeled data was previously either left unmatched or folded into the national ARG total, which is wrong because it conflates one province's output with the whole country's and discards the sub-national resolution the source provides - the routing check found zero existing candidate matches for "San Luis" and confirmed it is not a national total or residual bucket. That San Luis is a distinct, long-standing statistical reporting unit is confirmed by its status as one of the signatory provinces of the 1853 Constitution and its continuous, unbroken existence as a first-order administrative division of Argentina ever since, with no merger, contested renaming, or territorio-nacional interlude.

## Territorial extent

Polygon status: Not yet assigned. No polygon is attached in this pass. The routing decision selected registered_source_unfetched for gadm-3.6: GADM 3.6's global admin-1 layer digitizes San Luis province (expected feature such as ARG.23_1), and gadm-3.6 is a registered source in this repository's sources.yaml, but it is marked present_locally=False - the file is not on disk, so no feature id can be verified. The newer gadm-4.1-adm1 is present locally but is an 81-country curated subset that excludes Argentina entirely, so it cannot serve as a registered_source_feature route here despite being on disk. polygon_status: unassigned rather than proxy or assigned, and polygon_feature_id is left null pending the gadm-3.6 fetch.

Territory description: San Luis province sits in the Cuyo region of west-central Argentina, bordered by Mendoza to the west, Córdoba to the east, La Pampa to the south, and San Juan/La Rioja/Córdoba to the north. Its modern area is approximately 76,700 km2 (general reference geography, not measured from any attached polygon in this repository, since none is attached). The provincial capital is the city of San Luis. Provincial boundaries have been essentially stable since the 19th century - San Luis was not carved up, merged into, or split off from a neighboring jurisdiction the way several Patagonian and Chaco-region territorios nacionales were - so a modern GADM adm1 boundary, once fetched, is expected to be a reasonable proxy for the entire 1853-2025 span, with the vintage-risk caveat noted below.

## Predecessors and successors

No predecessor or successor polity is listed. San Luis does not succeed any prior distinct polity tracked in this table - it enters at 1853 as an original constitutional province with no earlier separate administrative existence recorded here - and it does not hand off to any successor, since it remains a current province with end_year fixed at the open convention value of 2025. It is contained, era by era, under the three successive national ARG rows (ARG-1800-1899, ARG-1899-1902, ARG-1902-2025), which together tile the full 1853-2025 span with no gap.

## Sourced claims

- San Luis was one of the provinces of the Argentine Confederation that ratified the Constitution of 1853, establishing it as a founding province rather than a later territorio nacional promoted to province status.
- San Luis's provincial borders have remained essentially unchanged since the 19th century, unlike Patagonian and Chaco-region territorios nacionales, which were only granted provincial status in the 20th century (e.g. Chaco and Formosa in 1951, La Pampa and Chubut in the same wave).

## Decisions

### d-code-follows-dominant-pattern

**Used the dominant ISO3-SUBUNIT-start-end code pattern**

San Luis is an ordinary, unbroken Argentine province with no bespoke historical name of its own (unlike Alaska Territory or Manchuria), so the bespoke-code exception does not apply. Following the pattern used by 338 of 351 subnational rows, including the six other Argentine provincial rows already created in this same pass (ARG-BA, ARG-CAT, ARG-CF, ARG-CHUBUT, ARG-CORDOBA, ARG-CORRIENTES), the code is ARG-SANLUIS-1853-2025. Uses an uppercase, diacritic-free subunit token (SANLUIS, no space or hyphen) for ASCII-safety, and the start/end years match the frontmatter exactly as the gate requires.

### d-three-container-edges

**Split the container into three edges to tile 1853-2025 with no gap**

The routing decision proposed only a single container reference (ARG-1902-2025, spanning 1902-2025), which would leave 1853-1902 uncontained and fail the containment gate, since an edge cannot fall outside either party's own span. Following the precedent set by the sibling Argentine provincial entries created in the same pass, three edges were declared instead: ARG-1800-1899 for 1853-1899, ARG-1899-1902 for the short bridging era 1899-1902, and ARG-1902-2025 for 1902-2025, each edge basis explaining that San Luis's provincial status and territory did not change across these national-era transitions - only the identity of the sovereign national row containing it changed.

### d-polygon-source-registered-unfetched

**Recorded polygon_source as the registered slug gadm-3.6, not the route name**

The routing decision's polygon_route was registered_source_unfetched, and polygon_detail confirms the candidate is gadm-3.6, a source already registered in sources.yaml but not present on disk (present_locally=False). Per the authoring rule for this route, the slug itself is the source, so polygon_source is set to gadm-3.6 (not to the route name or to a placeholder like 'new_source_needed'), with polygon_status left at unassigned pending the actual fetch.

## Open questions

### oq-gadm36-argentina-fetch-needed

**GADM 3.6 admin-1 polygon for Argentina still needs to be fetched**

gadm-3.6 is registered but not present locally in this repository's geodata, so no polygon can be attached to this entry yet despite GADM 3.6 digitizing San Luis (expected feature ID pattern ARG.23_1 or similar, per the routing decision's polygon_reasoning). Fetching the gadm-3.6 dataset (or confirming a suitable Argentina-specific provincial source, e.g. IGN/INDEC boundaries, as an alternative) is required before polygon_status can move from unassigned to assigned. Until then, any area or shape claims about this province rest on general reference geography rather than a verifiable attached polygon.

### oq-boundary-vintage-risk

**Modern GADM boundary would be used as a proxy across a 172-year span**

Once fetched, gadm-3.6 reflects present-day provincial boundaries, which would then be used as a proxy for the entire 1853-2025 span. San Luis's provincial territory is described as stable since 1853 with no known internal boundary revision, but this claim has not been independently corroborated against a historical source (e.g. a 19th-century Argentine provincial boundary atlas or Federico-Tena) the way the four departure provinces (Chaco/Formosa/La Pampa/Misiones/Neuquen/Rio Negro) were checked against their territorio-nacional histories. If San Luis lost or gained territory to a neighboring province at any point (a boundary dispute with Cordoba or Mendoza, for instance), the modern-boundary proxy would misstate the historical territory and this should be checked before polygon_status is upgraded past proxy.

### oq-data-coverage-gap

**Routed data years (1900-2023) leave the 1853-1900 and 2023-2025 tails uncovered**

The routing decision states juan-subnational data for San Luis runs 1900-2023, comfortably inside the 1853-2025 span but not covering it entirely. It is unclear whether the 1853-1900 gap reflects a genuine absence of province-level statistics for this period (plausible, given Argentina's national statistical apparatus was still maturing) or an artefact of the source's own coverage window that a different source might fill. Similarly, 2024-2025 is open per the end-year convention but has no data behind it yet.
