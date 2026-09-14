---
polity_code: ARG-MENDOZA-1853-2025
polity_name: Mendoza (province of Argentina)
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
polygon_feature_id: ARG.13_1
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: ARG-1800-1899
    start_year: 1853
    end_year: 1899
    basis: Mendoza was one of the historic provinces that entered the Argentine Confederation/Republic under the 1853 Constitution; the national row ARG-1800-1899 is the containing sovereign polity for this era.
  - code: ARG-1899-1902
    start_year: 1899
    end_year: 1902
    basis: Short national-era container row bridging the 1899 and 1902 national polity boundaries; Mendoza's provincial territory and status did not change across this transition.
  - code: ARG-1902-2025
    start_year: 1902
    end_year: 2025
    basis: Mendoza remains a province of the modern Argentine Republic, represented from 1902 onward by the national row ARG-1902-2025, through to the present day.
---

# Mendoza (province of Argentina)

## Summary

Mendoza is a province in west-central Argentina, on the eastern flank of the Andes bordering Chile, one of the fourteen historic provinces that ratified the 1853 Constitution and constituted the Argentine Confederation/Republic. It is not a former territorio nacional promoted to province status in the 20th century (unlike Chaco, Formosa, La Pampa, or Chubut), nor a bespoke historical territory with a name of its own distinct from the present-day province (unlike Alaska Territory or the Kingdom of Hawaii). It has held continuous province-level status since 1853, which is why this entry's start_year follows the country's default founding-province convention rather than a later provincialization date. `type: subnational` is used because sovereignty over Mendoza sits with the successive national ARG rows this entry is containered under across the full span, not with the province itself; the entry exists purely as a reporting-territory row because statistical sources (agricultural production, viticulture output, demographic data) tabulate Mendoza separately from national ARG totals. Mendoza's economy is historically dominated by irrigated viticulture (it produces roughly two-thirds of Argentina's wine) made possible by snowmelt irrigation from the Andes, a distinguishing feature of this province's statistical footprint relative to the pampas provinces. End_year is fixed at the open-end convention value of 2025 because Mendoza remains a current, unchanged province of Argentina.

**Why this entry exists.** This entry captures production/statistical data reported for the Argentine province of Mendoza (per the routing decision for unit_id ARG-MENDOZA, admin_name "Mendoza", country Argentina) under the country convention's default provincial span rule. Previously, no subnational polity existed for any Argentine province in this table beyond the national ARG chain (ARG-1800-1899, ARG-1899-1902, ARG-1902-2025); any Mendoza-labeled data would have been left unmatched or folded into the national ARG total, which is wrong because it conflates one province's wine and agricultural output with the whole country's, discarding the sub-national resolution the source actually provides -- a distortion that matters especially for Mendoza, since its viticulture output is disproportionate to its share of national population or territory. That Mendoza is a distinct, long-standing administrative and statistical reporting unit is confirmed by its status as one of the signatory provinces of the 1853 Constitution and its continuous, unbroken existence as a first-order administrative division of Argentina ever since, unlike the ex-territorios nacionales whose provincial status and spans required separate deliberation (routing_reasoning explicitly excludes Mendoza from those four departure groups: Chaco/Formosa-type territorios nacionales, Chubut/Santa Cruz, Tierra del Fuego, and CABA).

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is attached in this pass. The route selected was `registered_source_unfetched`: GADM 4.1's global admin-1 layer does digitize Mendoza province (it would carry a GID_1 such as ARG.14_1), but the GADM file present in this repository's geodata (`gadm-4.1-adm1.gpkg`) is an 81-country subset that excludes Argentina entirely (0 features for ARG). The source is therefore named (`gadm-4.1-adm1`) and registered, but not fetched here, so `polygon_status: unassigned` rather than `proxy` or `assigned`, and `polygon_feature_id` is left null pending that fetch.

**Territory description:** Mendoza province occupies west-central Argentina against the Andes, bordered by San Juan to the north, San Luis and La Pampa to the east, Neuquén to the south, and the Chilean border (with Aconcagua, the highest peak in the Americas, on that frontier) to the west. Its modern area is approximately **148,800 km²** (a figure from general reference geography, not measured from any attached polygon in this repository, since none is attached). The provincial capital is the city of Mendoza. Boundaries have been broadly stable since the 19th century -- Mendoza was not carved up, merged, or reassigned the way several Patagonian and Chaco-region territorios nacionales were -- so a modern GADM adm1 boundary, once fetched, is expected to be a reasonable proxy for the entire 1853-2025 span, subject to the vintage-risk caveat below.

## Predecessors and successors

No predecessor or successor polity is listed. Mendoza does not succeed any prior distinct polity in this table -- it enters at 1853 as an original constitutional province with no earlier separate administrative existence tracked here -- and it does not hand off to any successor, since it is a still-current province with end_year fixed at the open convention value of 2025. It is contained, era by era, under the three successive national ARG rows (ARG-1800-1899, ARG-1899-1902, ARG-1902-2025), which together tile the full 1853-2025 span with no gap.

## Sourced claims

- Mendoza was one of the provinces of the Argentine Confederation that ratified the Constitution of 1853, establishing it as a founding province rather than a later territorio nacional promoted to province status.
- Mendoza province accounts for roughly two-thirds of Argentina's wine production, made possible by Andean snowmelt irrigation systems (e.g. the historic acequia network), a distinguishing feature of its statistical reporting relative to other provinces.

## Decisions

### d-code-follows-dominant-pattern

**Used the dominant <ISO3>-<SUBUNIT>-<start>-<end> code pattern**

Mendoza is an ordinary, unbroken Argentine province with no bespoke historical name of its own distinct from the present-day province (unlike Alaska Territory or Hyderabad), so the bespoke-code exception does not apply. Following the dominant pattern used by 338 of 351 subnational rows, and consistent with the precedent already set for other Argentine provinces in this table (ARG-BA-1853-2025, ARG-CORDOBA-1853-2025, ARG-CORRIENTES-1853-2025), the code chosen is ARG-MENDOZA-1853-2025: ISO3, then an uppercase ASCII subunit token (MENDOZA, no diacritics), then the start and end years, matching the frontmatter years exactly as the code/containment gate requires.

### d-three-container-edges

**Split the container into three edges to tile 1853-2025 with no gap**

The routing_concerns and the country's national ARG chain (ARG-1800-1899, ARG-1899-1902, ARG-1902-2025) mean a 1853-2025 span crosses three national-era container polities. A single container edge referencing only ARG-1902-2025 would leave 1853-1902 uncontained and fail the containment gate, since an edge cannot fall outside either party's own span. Instead three edges were declared, matching the pattern already used for ARG-CORDOBA-1853-2025: ARG-1800-1899 for 1853-1899, ARG-1899-1902 for 1899-1902, and ARG-1902-2025 for 1902-2025, each basis explaining that Mendoza's provincial status and territory did not change across these national-era transitions -- only the identity of the sovereign national row containing it changed.

## Open questions

### oq-gadm-argentina-fetch-needed

**GADM 4.1 adm1 polygon for Argentina still needs to be fetched**

The locally available gadm-4.1-adm1.gpkg is restricted to an 81-country subset that does not include Argentina, so no polygon can be attached to this entry yet despite GADM digitizing Mendoza (expected feature ID pattern ARG.14_1 or similar). Fetching the full global GADM 4.1 admin-1 dataset (or an Argentina-specific extract) is required before polygon_status can move from unassigned to assigned. Until then, any area or shape claims about this province rest on general reference geography rather than a verifiable attached polygon.

### oq-boundary-vintage-risk

**Modern GADM boundary would be used as a proxy for the full 1853-2025 span**

Once fetched, a present-day GADM admin-1 polygon for Mendoza would need to stand in for the entire 1853-2025 period. While Mendoza's boundaries are believed to have been broadly stable since the 19th century, this has not been verified against a period-accurate historical source (e.g. confirming no border adjustments with San Juan, San Luis, or Neuquén occurred during 19th- or early-20th-century territorial reorganizations, including Neuquén's own territorio-nacional-to-province transition). This should be checked before treating a modern polygon as a safe proxy for the earliest decades of this span.

### oq-data-coverage-start-date

**Actual start year of Mendoza-specific data is unconfirmed against the 1853 structural start**

The routing decision gives no explicit data start year for this unit, only the structural 1853 constitutional-organization convention. It is worth confirming what year Mendoza-specific statistics (viticulture, agricultural production) actually begin in the ingested sources, and whether any gap between 1853 and the first data year is purely a structural/administrative-history choice with no corresponding routed data, as was found to be the case for Córdoba (1853-1900 gap).
