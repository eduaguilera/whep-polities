---
polity_code: ARG-CORDOBA-1853-2025
polity_name: Córdoba (province of Argentina)
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
    basis: Córdoba was one of the historic provinces that entered the Argentine Confederation/Republic under the 1853 Constitution; the national row ARG-1800-1899 is the containing sovereign polity for this era.
  - code: ARG-1899-1902
    start_year: 1899
    end_year: 1902
    basis: Short national-era container row bridging the 1899 and 1902 national polity boundaries; Córdoba's provincial territory and status did not change across this transition.
  - code: ARG-1902-2025
    start_year: 1902
    end_year: 2025
    basis: Córdoba remains a province of the modern Argentine Republic, represented from 1902 onward by the national row ARG-1902-2025, through to the present day.
---

# Córdoba (province of Argentina)

## Summary

Córdoba is a province of Argentina located in the center of the country, one of the fourteen original provinces (together with Buenos Aires, Santa Fe, Entre Ríos, Corrientes, and others) that constituted the Argentine Confederation and ratified the 1853 Constitution. It is not a former sovereign state or a territorio nacional that was later provincialized; it has held province-level status continuously since Argentina's constitutional organization, which is why this entry starts in 1853 rather than at a later provincialization date, unlike the ex-territorios nacionales (e.g. Chaco, Chubut, Formosa) that only became provinces in the 20th century. `type: subnational` is used because Córdoba was never sovereign in its own right within this span — sovereignty sits with the successive national ARG rows that this entry is containered under — but statistical sources report production and demographic data at the province level distinct from national ARG totals, which is the reporting-territory rationale for giving it its own row. The province's capital, also named Córdoba, is Argentina's second-largest city, and the province is a major agricultural region (grain, especially maize and soybeans) and industrial center (automotive manufacturing in the capital). End_year is set to the open convention value 2025 because Córdoba remains a current, unchanged province of Argentina.

**Why this entry exists.** This entry captures production/statistical data reported for the Argentine province of Córdoba beginning around 1900 (per the routing decision, data begins in 1900, comfortably inside the 1853-2025 span) and continuing to the present; the routing pipeline identified rows keyed to an admin unit named "Córdoba" within Argentina that needed a home. Previously, no subnational polity existed for any Argentine province — the ARG chain in the polities table only contains national-level rows (ARG-1800-1899, ARG-1899-1902, ARG-1902-2025) — so any Córdoba-labeled data was either left unmatched or folded into the national ARG total, which is wrong because it conflates one province's output with the whole country's, discarding the sub-national resolution the source actually provides. That Córdoba is a distinct, long-standing administrative and statistical reporting unit is confirmed by its status as one of the signatory provinces of the 1853 Constitution and its continuous, unbroken existence as a first-order administrative division of Argentina ever since — it is not a contested, renamed, or merged unit, unlike several other Argentine provinces (e.g. the territorios nacionales) whose spans required more deliberation.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is attached in this pass. The route selected was `registered_source_unfetched`: GADM 4.1's global admin-1 layer does digitize Córdoba province (it would carry a GID_1 such as ARG.7_1), but the GADM file present in this repository's geodata (`gadm-4.1-adm1.gpkg`) is an 81-country subset that excludes Argentina entirely (0 features for ARG). The source is therefore named (`gadm-4.1-adm1`) and registered, but not fetched here, so `polygon_status: unassigned` rather than `proxy` or `assigned`, and `polygon_feature_id` is left null pending that fetch.

**Territory description:** Córdoba province occupies the center of Argentina, bordered by Santiago del Estero and Catamarca to the north, La Rioja and San Luis to the west, La Pampa to the south, and Santa Fe and Buenos Aires provinces to the east. Its modern area is approximately **165,300 km²** (a figure from general reference geography, not measured from any attached polygon in this repository, since none is attached). The provincial capital is the city of Córdoba. Boundaries have been essentially stable since the 19th century — Córdoba was not carved up, merged, or reassigned to a neighboring jurisdiction the way several Patagonian and Chaco-region territorios nacionales were — so a modern GADM adm1 boundary, once fetched, is expected to be a reasonable proxy for the entire 1853-2025 span, with the caveat below about vintage risk.

## Predecessors and successors

No predecessor or successor polity is listed. Córdoba does not succeed any prior distinct polity in this table — it enters at 1853 as an original constitutional province with no earlier separate administrative existence tracked here — and it does not hand off to any successor, since it is a still-current province with end_year fixed at the open convention value of 2025. It is contained, era by era, under the three successive national ARG rows (ARG-1800-1899, ARG-1899-1902, ARG-1902-2025), which together tile the full 1853-2025 span with no gap.

## Sourced claims

- Córdoba was one of the provinces of the Argentine Confederation that ratified the Constitution of 1853, establishing it as a founding province rather than a later territorio nacional promoted to province status.
- The province of Córdoba's borders have remained essentially unchanged since the 19th century, unlike Patagonian and Chaco-region territorios nacionales, which were only granted provincial status in the 20th century (e.g. Chaco and Formosa in 1951, La Pampa and Chubut in 1951).

## Decisions

### d-code-follows-dominant-pattern

**Used the dominant <ISO3>-<SUBUNIT>-<start>-<end> code pattern**

Córdoba is an ordinary, unbroken Argentine province with no bespoke historical name of its own (unlike Alaska Territory or Hyderabad), so the bespoke-code exception does not apply. Following the pattern used by 57 of 66 subnational rows (e.g. ESP-AS-1833-2025, ESP-CA-1833-2025, DZA-CVD-1902-1919), the code is ARG-CORDOBA-1853-2025. Since ARG has zero existing subnational rows, this entry sets the precedent for the country: ISO3, then an uppercase subunit token (CORDOBA, without diacritics, to keep the code ASCII-safe), then the start and end years, matching the years declared in the frontmatter exactly as the gate requires.

### d-three-container-edges

**Split the container into three edges to tile 1853-2025 with no gap**

The routing_concerns flagged that a 1853-2025 span crosses three national-era ARG container polities. A single container edge referencing only ARG-1902-2025 would leave 1853-1902 uncontained and fail the containment gate, since an edge cannot fall outside either party's own span. Instead three edges were declared: ARG-1800-1899 for 1853-1899, ARG-1899-1902 for 1899-1902, and ARG-1902-2025 for 1902-2025, each edge basis explaining that Córdoba's provincial status and territory did not change across these national-era transitions — only the identity of the sovereign national row containing it changed.

## Open questions

### oq-gadm-argentina-fetch-needed

**GADM 4.1 adm1 polygon for Argentina still needs to be fetched**

The locally available gadm-4.1-adm1.gpkg is restricted to an 81-country subset that does not include Argentina, so no polygon can be attached to this entry yet despite GADM digitizing Córdoba (expected feature ID pattern ARG.7_1 or similar). Fetching the full global GADM 4.1 admin-1 dataset (or an Argentina-specific extract) is required before polygon_status can move from unassigned to assigned. Until then, any area or shape claims about this province rest on general reference geography rather than a verifiable attached polygon.

### oq-boundary-vintage-risk

**Modern GADM boundary would be used as a proxy for the full 1853-2025 span**

Once fetched, a present-day GADM admin-1 polygon for Córdoba would need to stand in for the entire 1853-2025 period. While Córdoba's boundaries are believed to have been broadly stable since the 19th century, this has not been verified against a period-accurate historical source (e.g. confirming no border adjustments with La Pampa, Santiago del Estero, or San Luis occurred during 19th- or early-20th-century territorial reorganizations). This should be checked before treating a modern polygon as a safe proxy for the earliest decades of this span, rather than assumed.

### oq-data-coverage-gap-1853-1900

**No data identified for Córdoba between 1853 and 1900**

The routing decision states that the underlying data for this unit begins around 1900, but the entry's start_year is set to 1853 per the country's default provincial span convention. This leaves roughly 47 years (1853-1900) where the polity exists in this table but is not known to be backed by any routed data row. It is worth confirming whether earlier Córdoba-specific statistics exist in any ingested source and, if so, whether they were missed by the routing pass, or whether the 1853 start is purely a structural/administrative-history choice with no corresponding data in this window.
