---
polity_code: ARG-SANTAFE-1853-2025
polity_name: Santa Fe (province of Argentina)
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
polygon_feature_id: ARG.21_1
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: ARG-1800-1899
    start_year: 1853
    end_year: 1899
    basis: Santa Fe was one of the historic provinces that entered the Argentine Confederation/Republic under the 1853 Constitution; the national row ARG-1800-1899 is the containing sovereign polity for this era.
  - code: ARG-1899-1902
    start_year: 1899
    end_year: 1902
    basis: Short national-era container row bridging the 1899 and 1902 national polity boundaries; Santa Fe's provincial territory and status did not change across this transition.
  - code: ARG-1902-2025
    start_year: 1902
    end_year: 2025
    basis: Santa Fe remains a province of the modern Argentine Republic, represented from 1902 onward by the national row ARG-1902-2025, through to the present day.
---

# Santa Fe (province of Argentina)

## Summary

Santa Fe is a province of Argentina located in the east-central part of the country, along the Paraná River, and is one of the fourteen original provinces (together with Buenos Aires, Córdoba, Entre Ríos, Corrientes, and others) that constituted the Argentine Confederation and ratified the 1853 Constitution. It is not a former sovereign state and not one of the ex-territorios nacionales (such as Chaco, Chubut, or Formosa) that only reached province status in the 20th century, nor is it the City of Buenos Aires (CABA), the other departure case in this country's convention; it has held province-level status continuously since Argentina's constitutional organization, which is why this entry starts in 1853 rather than at a later provincialization date. `type: subnational` is used because Santa Fe was never sovereign in its own right within this span — sovereignty sits with the successive national ARG rows this entry is containered under — but statistical sources report production and demographic data at the province level distinct from national ARG totals, which is the reporting-territory rationale for giving it its own row. Santa Fe's capital is the city of Santa Fe, and its largest city, Rosario, is a major agro-industrial port; the province is one of Argentina's principal soybean, maize, wheat, and dairy-producing regions, and hosts significant grain-export infrastructure along the Paraná. End_year is set to the open convention value 2025 because Santa Fe remains a current, unchanged province of Argentina.

**Why this entry exists.** This entry captures production/statistical data reported for the Argentine province of Santa Fe over 1900-2023 (per the routing decision), comfortably inside the 1853-2025 span set by the country's default provincial-span convention. The routing pipeline identified rows keyed to an admin unit named "Santa Fe" within Argentina that needed a home; previously, no subnational polity existed for any Argentine province apart from the sibling entries created in this same pass (Córdoba, Corrientes, Buenos Aires, and others) — the ARG chain in the polities table otherwise contains only national-level rows (ARG-1800-1899, ARG-1899-1902, ARG-1902-2025) — so any Santa Fe-labeled data was previously either left unmatched or folded into the national ARG total, which is wrong because it conflates one province's output (Santa Fe alone accounts for a large share of national grain and dairy production) with the whole country's, discarding the sub-national resolution the source actually provides. That Santa Fe is a distinct, long-standing administrative and statistical reporting unit is confirmed by its status as one of the signatory provinces of the 1853 Constitution and its continuous, unbroken existence as a first-order administrative division of Argentina ever since — it is not a contested, renamed, or merged unit, unlike the territorios nacionales whose spans required more deliberation.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is attached in this pass. The route selected is `registered_source_unfetched`: GADM 4.1's global admin-1 layer does digitize Santa Fe province, but the GADM file present in this repository's geodata (`gadm-4.1-adm1.gpkg`) is an 81-country subset that excludes Argentina entirely (0 features for ARG), and the routing_concerns additionally note that no feature was found under the exact name "Santa Fe" — a check that needs to be repeated with name variants (e.g. "Santa Fé") once the full dataset is fetched. The source is therefore named (`gadm-4.1-adm1`) and registered, but not fetched here, so `polygon_status: unassigned` rather than `proxy` or `assigned`, and `polygon_feature_id` is left null pending that fetch.

**Territory description:** Santa Fe province occupies the east-central Pampas region of Argentina, bordered by Chaco and Santiago del Estero to the north, Córdoba to the west, Buenos Aires to the south, and Entre Ríos (across the Paraná River) to the east. Its modern area is approximately **133,000 km²** (a figure from general reference geography, not measured from any attached polygon in this repository, since none is attached). The provincial capital is the city of Santa Fe, and the largest city is Rosario, a major river port. Boundaries have been essentially stable since the 19th century — Santa Fe was not carved up, merged, or reassigned the way several Patagonian and Chaco-region territorios nacionales were — so a modern GADM adm1 boundary, once fetched, is expected to be a reasonable proxy for the entire 1853-2025 span, with the same vintage-risk caveat recorded for ARG-CORDOBA-1853-2025.

## Predecessors and successors

No predecessor or successor polity is listed. Santa Fe does not succeed any prior distinct polity in this table — it enters at 1853 as an original constitutional province with no earlier separate administrative existence tracked here — and it does not hand off to any successor, since it is a still-current province with end_year fixed at the open convention value of 2025. It is contained, era by era, under the three successive national ARG rows (ARG-1800-1899, ARG-1899-1902, ARG-1902-2025), which together tile the full 1853-2025 span with no gap, mirroring the container chain used for ARG-CORDOBA-1853-2025 and ARG-CORRIENTES-1853-2025.

## Sourced claims

- Santa Fe was one of the provinces of the Argentine Confederation that ratified the Constitution of 1853, establishing it as a founding province of the 1853 Confederation rather than a later territorio nacional promoted to province status.
- Santa Fe's borders have remained essentially stable since the 19th century organization of the Argentine provinces, unlike Patagonian and Chaco-region territorios nacionales (e.g. Chaco and Formosa, provincialized in 1951; La Pampa and Chubut, provincialized in 1951), which only reached provincial status in the 20th century.

## Decisions

### d-code-follows-dominant-pattern

**Used the dominant <ISO3>-<SUBUNIT>-<start>-<end> code pattern**

Santa Fe is an ordinary, unbroken Argentine province with no bespoke historical name of its own (unlike Alaska Territory or Hyderabad), so the bespoke-code exception does not apply. Following the pattern used for the great majority of subnational rows, including the sibling ARG entries already created (ARG-CORDOBA-1853-2025, ARG-CORRIENTES-1853-2025, ARG-BA-1853-2025), the code is ARG-SANTAFE-1853-2025. The subunit token SANTAFE (uppercase, no diacritics, no space) keeps the code ASCII-safe, and the start/end years match the frontmatter exactly as the gate requires.

### d-three-container-edges

**Split the container into three edges to tile 1853-2025 with no gap**

The routing_concerns and the country's national ARG chain (ARG-1800-1899, ARG-1899-1902, ARG-1902-2025) mean a single container edge referencing only ARG-1902-2025 (as literally proposed) would leave 1853-1902 uncontained and fail the containment gate, since an edge cannot fall outside either party's own span. Instead, following the precedent set by ARG-CORDOBA-1853-2025 and other founding-province entries, three edges were declared: ARG-1800-1899 for 1853-1899, ARG-1899-1902 for 1899-1902, and ARG-1902-2025 for 1902-2025, each basis explaining that Santa Fe's provincial status and territory did not change across these national-era transitions — only the identity of the sovereign national row containing it changed.

## Open questions

### oq-gadm-argentina-fetch-needed

**GADM 4.1 adm1 polygon for Argentina still needs to be fetched**

The locally available gadm-4.1-adm1.gpkg is restricted to an 81-country subset that does not include Argentina at all (0 features), so no polygon can be attached to this entry yet, despite GADM's global admin-1 layer digitizing Santa Fe (expected feature ID pattern ARG.22_1 or similar, alongside Córdoba's ARG.7_1). Fetching the full global GADM 4.1 admin-1 dataset, or an Argentina-specific extract, is required before polygon_status can move from unassigned to assigned. Until then, any area or shape claims about this province rest on general reference geography rather than a verifiable attached polygon.

### oq-name-variant-geometry-check

**Geometry match should be re-checked against name variants (Santa Fe vs Santa Fé)**

The routing_concerns explicitly flag that no boundary feature was found for Santa Fe in gadm-4.1-adm1 under this exact name, and that alternate spellings such as 'Santa Fé' (with the accented e) should be checked once the full GADM dataset is available, before concluding the unit is simply absent from the source rather than present under a different label string. This is separate from the dataset-coverage gap above: even after Argentina is fetched, a naive exact-string lookup could still miss the feature.

### oq-data-coverage-gap-1853-1900

**No data identified for Santa Fe between 1853 and 1900**

The routing decision states that the underlying data for this unit runs 1900-2023, but the entry's start_year is set to 1853 per the country's default provincial span convention (Santa Fe being one of the original 1853 constitutional provinces). This leaves roughly 47 years (1853-1900) where the polity exists in this table but is not known to be backed by any routed data row. It is worth confirming whether earlier Santa Fe-specific statistics exist in any ingested source and, if so, whether they were missed by the routing pass, or whether the 1853 start is purely a structural/administrative-history choice with no corresponding data in this window — the same open question already recorded for ARG-CORDOBA-1853-2025.
