---
polity_code: ARG-SANJUAN-1853-2025
polity_name: San Juan (province of Argentina)
start_year: 1853
end_year: 2025
type: subnational
iso3: ARG
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
  - code: ARG-1800-1899
    start_year: 1853
    end_year: 1899
    basis: San Juan was one of the historic provinces that entered the Argentine Confederation/Republic under the 1853 Constitution; the national row ARG-1800-1899 is the containing sovereign polity for this era.
  - code: ARG-1899-1902
    start_year: 1899
    end_year: 1902
    basis: Short national-era container row bridging the 1899 and 1902 national polity boundaries; San Juan's provincial territory and status did not change across this transition.
  - code: ARG-1902-2025
    start_year: 1902
    end_year: 2025
    basis: San Juan remains a province of the modern Argentine Republic, represented from 1902 onward by the national row ARG-1902-2025, through to the present day.
---

# San Juan (province of Argentina)

## Summary

San Juan is a province of Argentina in the west of the country, in the Cuyo region, one of the fourteen original provinces (together with Buenos Aires, Córdoba, Mendoza, and others) that constituted the Argentine Confederation and ratified the 1853 Constitution. It is not a former territorio nacional that was later provincialized, and it has held province-level status continuously since Argentina's constitutional organization, which is why this entry starts in 1853 rather than at a later provincialization date, unlike the ex-territorios nacionales (e.g. Chaco, Chubut, La Pampa) that only became provinces in the 20th century. `type: subnational` is used because San Juan was never sovereign in its own right within this span — sovereignty sits with the successive national ARG rows that this entry is containered under — but statistical sources report production and demographic data at the province level distinct from national ARG totals, which is the reporting-territory rationale for giving it its own row. San Juan's capital, also named San Juan, is a wine-producing center; the province is known for viticulture (especially in the Tulum, Ullum, and Zonda valleys) and mining, and lies in an arid, seismically active zone at the base of the Andes. End_year is set to the open convention value 2025 because San Juan remains a current, unchanged province of Argentina.

**Why this entry exists.** This entry captures production/statistical data reported for the Argentine province of San Juan (per the routing decision, data spans roughly 1900-2023, comfortably inside the 1853-2025 span); the routing pipeline identified rows keyed to an admin unit named "San Juan" within Argentina that needed a home. Previously, no subnational polity existed for any Argentine province in this table beyond the small set already created in this same pipeline run (e.g. ARG-BA, ARG-CORDOBA, ARG-CORRIENTES) — the ARG chain otherwise contains only national-level rows (ARG-1800-1899, ARG-1899-1902, ARG-1902-2025) — so any San Juan-labeled data was previously either left unmatched or folded into the national ARG total, which is wrong because it conflates one province's output (notably its wine and mineral production, both regionally concentrated) with the whole country's, discarding the sub-national resolution the source actually provides. That San Juan is a distinct, long-standing administrative and statistical reporting unit is confirmed by its status as one of the signatory provinces of the 1853 Constitution and its continuous, unbroken existence as a first-order administrative division of Argentina ever since — it is not a contested, renamed, or merged unit, unlike several other Argentine provinces (the territorios nacionales) whose spans required more deliberation in this same pipeline pass.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is attached in this pass. The route selected was `registered_source_unfetched`: GADM 4.1's global admin-1 layer does digitize San Juan province (it would carry a GID_1 such as ARG.22_1), but the GADM file present in this repository's geodata (`gadm-4.1-adm1.gpkg`) is an 81-country subset that excludes Argentina entirely (0 features for ARG). The source is therefore named (`gadm-4.1-adm1`) and registered, but not fetched here, so `polygon_status: unassigned` rather than `proxy` or `assigned`, and `polygon_feature_id` is left null pending that fetch.

**Territory description:** San Juan province lies in western Argentina's Cuyo region, bordered by La Rioja to the east/northeast, Catamarca to the north, San Luis to the southeast, Mendoza to the south, and Chile (across the Andes) to the west. Its modern area is approximately **89,650 km²** (a figure from general reference geography, not measured from any attached polygon in this repository, since none is attached). The provincial capital is the city of San Juan. Boundaries have been essentially stable since the 19th century — San Juan was not carved up, merged, or reassigned to a neighboring jurisdiction the way several Patagonian and Chaco-region territorios nacionales were — so a modern GADM adm1 boundary, once fetched, is expected to be a reasonable proxy for the entire 1853-2025 span, with the caveat below about vintage risk.

## Predecessors and successors

No predecessor or successor polity is listed. San Juan does not succeed any prior distinct polity in this table — it enters at 1853 as an original constitutional province with no earlier separate administrative existence tracked here — and it does not hand off to any successor, since it is a still-current province with end_year fixed at the open convention value of 2025. It is contained, era by era, under the three successive national ARG rows (ARG-1800-1899, ARG-1899-1902, ARG-1902-2025), which together tile the full 1853-2025 span with no gap.

## Sourced claims

- San Juan was one of the provinces of the Argentine Confederation that ratified the Constitution of 1853, establishing it as a founding province rather than a later territorio nacional promoted to province status.
- The province of San Juan's borders have remained essentially unchanged since the 19th century, unlike Patagonian and Chaco-region territorios nacionales, which were only granted provincial status in the 20th century (e.g. La Pampa and Chubut in 1951).

## Decisions

### d-code-follows-dominant-pattern

**Used the dominant <ISO3>-<SUBUNIT>-<start>-<end> code pattern**

San Juan is an ordinary, unbroken Argentine province with no bespoke historical name of its own (unlike Alaska Territory or Hyderabad), so the bespoke-code exception does not apply. Following the pattern used by 338 of 351 subnational rows (e.g. ARG-BA-1853-2025, ARG-CORDOBA-1853-2025, ARG-CORRIENTES-1853-2025), the code is ARG-SANJUAN-1853-2025. Since ARG already has seven existing subnational rows created in this same pipeline pass, this entry follows their established precedent: ISO3, then an uppercase subunit token (SANJUAN, without spaces or diacritics, to keep the code ASCII-safe), then the start and end years, matching the years declared in the frontmatter exactly as the gate requires.

### d-three-container-edges

**Split the container into three edges to tile 1853-2025 with no gap**

The proposed decision only named a single container_code (ARG-1902-2025) despite a span_basis text describing a 1853 start, which would leave 1853-1902 uncontained and fail the containment gate, since an edge cannot fall outside either party's own span. Following the precedent set by the other ARG province entries created in this pass, three edges were declared instead: ARG-1800-1899 for 1853-1899, ARG-1899-1902 for 1899-1902, and ARG-1902-2025 for 1902-2025, each edge basis explaining that San Juan's provincial status and territory did not change across these national-era transitions — only the identity of the sovereign national row containing it changed.

## Open questions

### oq-gadm-argentina-fetch-needed

**GADM 4.1 adm1 polygon for Argentina still needs to be fetched**

The locally available gadm-4.1-adm1.gpkg is restricted to an 81-country subset that does not include Argentina, so no polygon can be attached to this entry yet despite GADM digitizing San Juan (expected feature ID pattern ARG.22_1 or similar). Fetching the full global GADM 4.1 admin-1 dataset (or an Argentina-specific extract) is required before polygon_status can move from unassigned to assigned. Until then, any area or shape claims about this province rest on general reference geography rather than a verifiable attached polygon.

### oq-boundary-vintage-risk

**Modern GADM boundary would be used as a proxy for the full 1853-2025 span**

Once fetched, a present-day GADM admin-1 polygon for San Juan would need to stand in for the entire 1853-2025 period. While San Juan's boundaries are believed to have been broadly stable since the 19th century, this has not been verified against a period-accurate historical source (e.g. confirming no border adjustments with La Rioja, Catamarca, or Mendoza occurred during 19th- or early-20th-century territorial reorganizations, or across the Chile/Argentina Andean boundary settlements). This should be checked before treating a modern polygon as a safe proxy for the earliest decades of this span, rather than assumed.

### oq-data-coverage-gap-1853-1900

**No data identified for San Juan between 1853 and 1900**

The routing decision states that the underlying data for this unit spans roughly 1900-2023, but the entry's start_year is set to 1853 per the country's default provincial span convention. This leaves roughly 47 years (1853-1900) where the polity exists in this table but is not known to be backed by any routed data row. It is worth confirming whether earlier San Juan-specific statistics (e.g. on the pre-phylloxera wine trade, or the 1894 provincial census) exist in any ingested source and, if so, whether they were missed by the routing pass, or whether the 1853 start is purely a structural/administrative-history choice with no corresponding data in this window.
