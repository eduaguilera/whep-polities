---
polity_code: ARG-CORRIENTES-1853-2025
polity_name: Corrientes (province of Argentina)
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
polygon_feature_id: ARG.7_1
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: ARG-1800-1899
    start_year: 1853
    end_year: 1899
    basis: Corrientes was one of the historic provinces that entered the Argentine Confederation/Republic under the 1853 Constitution; the national row ARG-1800-1899 is the containing sovereign polity for this era.
  - code: ARG-1899-1902
    start_year: 1899
    end_year: 1902
    basis: Short national-era container row bridging the 1899 and 1902 national polity boundaries; Corrientes's provincial territory and status did not change across this transition.
  - code: ARG-1902-2025
    start_year: 1902
    end_year: 2025
    basis: Corrientes remains a province of the modern Argentine Republic, represented from 1902 onward by the national row ARG-1902-2025, through to the present day.
---

# Corrientes (province of Argentina)

## Summary

Corrientes is a province in the northeastern Mesopotamia region of Argentina, bounded by the Parana river to the west and south (facing Chaco and Santa Fe) and the Uruguay river to the east (facing Uruguay and Brazil), with Misiones to the north and Entre Rios to the south. It is one of the original signatory provinces of the Argentine Confederation that ratified the 1853 Constitution, and unlike several other Argentine subnational units in this table (Chaco, Formosa, La Pampa, Misiones, Neuquen, Rio Negro, Chubut, Santa Cruz, Tierra del Fuego, or the City of Buenos Aires) it was never administered as a national territorio nacional later promoted to provincial status -- it has held province-level status continuously since 1853, which fixes this entry's start year under the country's default provincial span convention. `type: subnational` is used because Corrientes was never sovereign in its own right within this span -- national sovereignty sits with the successive ARG rows this entry is containered under (ARG-1800-1899, ARG-1899-1902, ARG-1902-2025) -- but the routing decision identifies statistical data reported at the province level distinct from national ARG totals, which is the reporting-territory rationale for giving Corrientes its own row rather than folding its figures into the national aggregate. End_year is set to the open convention value of 2025 because Corrientes remains a current, unchanged province of Argentina.

**Why this entry exists.** This entry captures production/statistical data reported for the Argentine province of Corrientes, per the routing decision keyed to unit_id ARG-CORRIENTES with a data window of 1900-2023, comfortably inside the declared 1853-2025 span. Previously, no subnational polity existed for any Argentine province -- the ARG chain in the polities table held only national-level rows (ARG-1800-1899, ARG-1899-1902, ARG-1902-2025) -- so any Corrientes-labeled data was either left unmatched or folded into the national ARG total, which is wrong because it conflates one province's output with the whole country's and discards the sub-national resolution the source actually provides. That Corrientes is a distinct, long-standing administrative and statistical reporting unit is confirmed by its status as one of the founding provinces of the 1853 Constitution and its continuous, unbroken existence as a first-order administrative division of Argentina since -- unlike the ex-territorios nacionales (Chaco, Formosa, La Pampa, Misiones, Neuquen, Rio Negro, Chubut, Santa Cruz, Tierra del Fuego) or the City of Buenos Aires, whose provincial/autonomous status arrived much later and required more deliberation over span endpoints.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is attached in this pass. The route selected was `registered_source_unfetched`: GADM 4.1's global admin-1 layer does digitize Corrientes province (expected to carry a GID_1 such as ARG.7_1, exact value to be confirmed), but the GADM file present in this repository's geodata (`gadm-4.1-adm1.gpkg`) is an 81-country subset that excludes Argentina entirely. The source is therefore named (`gadm-4.1-adm1`) and registered, but not fetched here, so `polygon_status: unassigned` rather than `proxy` or `assigned`, and `polygon_feature_id` is left null pending that fetch.

**Territory description:** Corrientes province occupies Argentina's Mesopotamia region in the northeast, between the Parana river (border with Chaco and Santa Fe provinces, and with Paraguay near its northern tip) and the Uruguay river (border with Uruguay and, via Misiones, Brazil), with Misiones province to the north and Entre Rios province to the south. Its modern area is approximately **88,200 km²** (a figure from general reference geography, not measured from any attached polygon in this repository, since none is attached). The provincial capital is the city of Corrientes, on the Parana river. Boundaries have been broadly stable since the province's founding-era existence, though the 19th-century river frontier with Paraguay was contested during and after the War of the Triple Alliance (1865-1870) -- a caveat noted below since a modern GADM boundary, once fetched, would need to stand in as a proxy for the entire 1853-2025 span.

## Predecessors and successors

No predecessor or successor polity is listed. Corrientes does not succeed any prior distinct polity tracked in this table -- it enters at 1853 as one of the founding constitutional provinces of the Argentine Confederation/Republic, with no earlier separate administrative existence recorded here -- and it does not hand off to any successor, since it is a still-current province with end_year fixed at the open convention value of 2025. It is contained, era by era, under the three successive national ARG rows (ARG-1800-1899, ARG-1899-1902, ARG-1902-2025), which together tile the full 1853-2025 span with no gap, exactly as the sibling entry for Cordoba does.

## Sourced claims

- Corrientes was one of the provinces of the Argentine Confederation that ratified the Constitution of 1853, establishing it as a founding province rather than a later territorio nacional promoted to province status (unlike Chaco and Formosa, provincialized only in 1951, or Chubut, provincialized in 1955).
- Corrientes fought on the Allied side against Paraguay in the War of the Triple Alliance (1865-1870), a conflict fought largely along its own northeastern river frontier -- a period during which its exact boundary with Paraguay across the Parana river was still being settled, bearing on how safely a modern boundary can proxy for the 19th-century territory.

## Decisions

### d-code-follows-dominant-pattern

**Used the dominant <ISO3>-<SUBUNIT>-<start>-<end> code pattern**

Corrientes is one of Argentina's original historic provinces with no bespoke historical name distinct from the modern province itself (unlike Alaska Territory or Hyderabad), so the bespoke-code exception does not apply. Following the pattern used by 57 of 66 subnational rows (e.g. ESP-AS-1833-2025, DZA-CVD-1902-1919, and the sibling entry ARG-CORDOBA-1853-2025 created in this same pass), the code chosen is ARG-CORRIENTES-1853-2025: ISO3, an uppercase ASCII subunit token, then start and end years matching the frontmatter exactly. ARG has no pre-existing subnational rows, so together with Cordoba this entry helps set the country's precedent rather than depart from one.

### d-three-container-edges

**Split the container into three edges to tile 1853-2025 with no gap**

The routing_concerns and the polity table show the ARG national chain crosses three eras in this span: ARG-1800-1899, ARG-1899-1902, and ARG-1902-2025 (the proposed container_code of ARG-1902-2025 alone only covers 1902-2025, leaving 1853-1902 uncontained). A single edge referencing only ARG-1902-2025 would fail the containment gate for falling outside that party's own span at the 1853 end. Instead three edges are declared, matching exactly the pattern used for ARG-CORDOBA-1853-2025: ARG-1800-1899 for 1853-1899, ARG-1899-1902 for 1899-1902, and ARG-1902-2025 for 1902-2025, each basis noting that Corrientes's provincial status and territory did not change across these national-era transitions -- only the identity of the containing sovereign row changed.

## Open questions

### oq-gadm-argentina-fetch-needed

**GADM 4.1 adm1 polygon for Argentina still needs to be fetched**

The locally available gadm-4.1-adm1.gpkg is restricted to an 81-country subset that does not include Argentina, so no polygon can be attached to this entry yet despite GADM digitizing Corrientes (expected feature ID pattern ARG.7_1-style, exact GID_1 to be confirmed once fetched). Fetching the full global GADM 4.1 admin-1 dataset, or an Argentina-specific extract, is required before polygon_status can move from unassigned to assigned. Until then, any area or shape claims about this province rest on general reference geography rather than a verifiable attached polygon in this repository.

### oq-boundary-vintage-risk

**Modern GADM boundary would be used as a proxy for the full 1853-2025 span**

Once fetched, a present-day GADM admin-1 polygon for Corrientes would need to stand in for the entire 1853-2025 period. Corrientes's boundaries are believed to have been broadly stable since the 19th century -- it was one of the original signatory provinces and was never a territorio nacional later carved into provincial form -- but this has not been verified against a period-accurate historical source, particularly regarding the Parana and Uruguay river frontiers with Entre Rios, Misiones, Chaco and (across the border) Paraguay, which shifted somewhat over the 19th century including after the War of the Triple Alliance. This should be checked before treating a modern polygon as a safe proxy for the earliest decades of this span.

### oq-data-coverage-gap-pre-1900

**Data coverage before the year 1900 is unconfirmed**

The routing decision states the unit's data window runs 1900-2023, entirely inside the declared 1853-2025 span, but does not confirm whether any Corrientes-specific statistics exist for 1853-1900. This leaves roughly 47 years where the polity exists in this table but is not known to be backed by any routed data row, mirroring the same open question raised on the sibling entry ARG-CORDOBA-1853-2025. It is worth confirming whether earlier Corrientes-specific statistics exist in any ingested source, or whether the 1853 start is purely a structural/administrative-history choice under the country's default provincial span convention with no corresponding data in this window.
