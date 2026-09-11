---
polity_code: ARG-LARIOJA-1853-2025
polity_name: La Rioja (province of Argentina)
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
polygon_feature_id: ARG.12_1
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: ARG-1800-1899
    start_year: 1853
    end_year: 1899
    basis: La Rioja was one of the historic provinces that entered the Argentine Confederation/Republic under the 1853 Constitution; ARG-1800-1899 is the containing sovereign polity for this era.
  - code: ARG-1899-1902
    start_year: 1899
    end_year: 1902
    basis: Short national-era container row bridging the 1899 and 1902 national polity boundaries; La Rioja's provincial territory and status did not change across this transition.
  - code: ARG-1902-2025
    start_year: 1902
    end_year: 2025
    basis: La Rioja remains a province of the modern Argentine Republic, represented from 1902 onward by the national row ARG-1902-2025, through to the present day.
---

# La Rioja (province of Argentina)

## Summary

La Rioja is a province in the northwest of Argentina, one of the fourteen historic provinces (alongside Buenos Aires, Córdoba, Corrientes, Entre Ríos, and others) that entered the Argentine Confederation and ratified the 1853 Constitution. It is not a former territorio nacional promoted to province status in the 20th century -- unlike Chaco, Formosa, La Pampa, or Chubut, which departed from the country's default span rule and were created with later start years tied to their legal provincialization dates -- so La Rioja carries the default convention span of 1853-2025. `type: subnational` is used because La Rioja was never sovereign in its own right within this span; sovereignty sits with the successive national ARG rows (ARG-1800-1899, ARG-1899-1902, ARG-1902-2025) under which this entry is containered. The reporting-territory rationale for giving it its own row is that statistical sources (per the routing decision, Juan's subnational admin-1 panel, covering roughly 1900-2023) report data keyed to "La Rioja" as a distinct Argentine administrative unit, separate from national ARG totals. The province is known for viticulture (a major wine-producing region within the larger Cuyo/Northwest wine belt), mining, and a arid, mountainous Andean-foothill terrain. End_year is fixed at the open convention value of 2025 because La Rioja remains a current, unchanged province of Argentina.

**Why this entry exists.** This entry captures production/statistical data reported for the Argentine province of La Rioja beginning around 1900 (per the routing decision, unit_id ARG-LARIOJA, data spans roughly 1900-2023) and continuing to the present. Previously, no subnational polity existed for any Argentine province in this table -- the ARG chain contained only national-level rows (ARG-1800-1899, ARG-1899-1902, ARG-1902-2025) -- so any La Rioja-labeled data was either left unmatched or folded into the national ARG total, which is wrong because it conflates one province's output (a province of roughly 89,680 km2) with the whole country's (roughly 2,780,000 km2), a mismatch of more than an order of magnitude that discards the sub-national resolution the source actually provides. The routing decision itself states that no existing polity matches La Rioja by name and that the three ARG national-total polities are containers, not this province itself, so `match_existing` was inapplicable and creation was the only option. What confirms La Rioja was administratively distinct throughout this period: it is one of the provinces that ratified the 1853 Constitution as a founding member of the Argentine Confederation/Republic, and it has held continuous, unbroken province-level status since -- it is not a contested, renamed, split, or merged unit, unlike the ex-territorios nacionales (Chaco, Formosa, La Pampa, Chubut, Santa Cruz, Tierra del Fuego) or the City of Buenos Aires (CABA), all of which the country convention explicitly lists as departures from the default 1853 start rule.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is attached in this pass. The route selected was `registered_source_unfetched`: GADM 4.1's global admin-1 layer does digitize La Rioja province (expected to carry a GID_1 such as ARG.11_1), but the GADM file present in this repository's geodata (`gadm-4.1-adm1.gpkg`) is a curated 81-country subset that excludes Argentina entirely (0 features for ARG), per the routing decision's own polygon_detail. The source is therefore named (`gadm-4.1-adm1`) and registered, but not fetched here, so `polygon_status: unassigned` rather than `proxy` or `assigned`, and `polygon_feature_id` is left null pending that fetch -- the same situation already documented for ARG-CORDOBA-1853-2025 and ARG-1884-1951 (Chaco).

**Territory description:** La Rioja province occupies the northwest of Argentina, in the Cuyo/Norte Grande border region, bordered by Catamarca to the north, Córdoba to the east, San Luis and San Juan to the south and southwest, and the Andes mountains (Chilean border) to the west. Its modern area is approximately **89,680 km2** (a figure from general reference geography, not measured from any attached polygon in this repository, since none is attached). The provincial capital is the city of La Rioja. The province's terrain is arid and mountainous, part of the Sierras Pampeanas and pre-Andean ranges, with the economy historically centered on viticulture (a wine-producing zone extending from the Cuyo region), olives, and mining. Boundaries have been essentially stable since the 19th century -- unlike the Patagonian and Chaco-region territorios nacionales, La Rioja was never carved up or reassigned -- so a modern GADM adm1 boundary, once fetched, is expected to be a reasonable proxy for the entire 1853-2025 span, with the vintage-risk caveat recorded below.

## Predecessors and successors

No predecessor or successor polity is listed. La Rioja does not succeed any prior distinct polity in this table -- it enters at 1853 as one of the provinces that ratified the Argentine Constitution, with no earlier separate administrative existence tracked here -- and it does not hand off to any successor, since it is a still-current province with end_year fixed at the open convention value of 2025. It is contained, era by era, under the three successive national ARG rows (ARG-1800-1899, ARG-1899-1902, ARG-1902-2025), which together tile the full 1853-2025 span with no gap, exactly as for the sibling province entries ARG-CORDOBA-1853-2025, ARG-CORRIENTES-1853-2025, and ARG-JUJUY-1853-2025.

## Sourced claims

- La Rioja was one of the fourteen original provinces that entered the Argentine Confederation and ratified the Constitution of 1853, giving it founding-province status rather than the later territorio-nacional-to-province promotion undergone by Chaco (1951), Formosa (1955), La Pampa (1951), or Chubut (1955).
- Modern La Rioja province covers approximately 89,680 km2 and is bordered by Catamarca to the north, Córdoba to the east, San Luis and San Juan to the south and southwest, and the Chilean border along the Andes to the west; its capital is the city of La Rioja.

## Decisions

### d-code-follows-dominant-pattern

**Used the dominant <ISO3>-<SUBUNIT>-<start>-<end> code pattern**

La Rioja is an ordinary, unbroken Argentine province with no bespoke historical name of its own (unlike Alaska Territory, or the Territorio Nacional del Chaco, which was a genuinely distinct pre-1951 administrative classification and earned its own <ISO3>-<start>-<end> code, ARG-1884-1951). La Rioja was never a territorio nacional and never changed legal status the way Chaco, Formosa, La Pampa, or Chubut did -- the routing decision explicitly confirms it is not among the listed departures from the default span rule -- so it follows the same pattern already established for the sibling ARG provinces ARG-CORDOBA-1853-2025, ARG-CORRIENTES-1853-2025, ARG-ER-1853-2025, ARG-JUJUY-1853-2025, and ARG-CAT-1853-2025: ARG-LARIOJA-1853-2025. The subunit token is the province name uppercased with spaces and diacritics stripped (LARIOJA), matching the routing decision's own admin_name "La Rioja" and keeping the code ASCII-safe, following the same convention Corrientes and Catamarca already set.

### d-three-container-edges

**Split the container into three edges to tile 1853-2025 with no gap**

A 1853-2025 span crosses three successive national-era ARG container polities (ARG-1800-1899, ARG-1899-1902, ARG-1902-2025). A single container edge referencing only ARG-1902-2025 would leave 1853-1902 uncontained and fail the containment gate, since an edge cannot fall outside either party's own declared span. Instead three edges were declared, exactly mirroring the pattern already used on ARG-CORDOBA-1853-2025: ARG-1800-1899 for 1853-1899, ARG-1899-1902 for 1899-1902, and ARG-1902-2025 for 1902-2025, each edge basis explaining that La Rioja's provincial status and territory did not change across these national-era transitions -- only the identity of the sovereign national row containing it changed.

## Open questions

### oq-gadm-argentina-fetch-needed

**GADM 4.1 adm1 polygon for Argentina still needs to be fetched**

The locally available gadm-4.1-adm1.gpkg is restricted to an 81-country subset that does not include Argentina, so no polygon can be attached to this entry yet despite GADM digitizing La Rioja province (expected feature ID pattern ARG.11_1 or similar). Fetching the full global GADM 4.1 admin-1 dataset (or an Argentina-specific extract) is required before polygon_status can move from unassigned to assigned. This is the same blocking gap already logged against ARG-CORDOBA-1853-2025 and ARG-1884-1951 (Chaco); once resolved for one Argentine province it should be resolved for all of them in a single fetch, which is worth flagging so it isn't repeated province-by-province.

### oq-boundary-vintage-risk

**Modern GADM boundary would be used as a proxy for the full 1853-2025 span**

Once fetched, a present-day GADM admin-1 polygon for La Rioja would need to stand in for the entire 1853-2025 period. While La Rioja's boundaries are believed to have been broadly stable since the 19th century (it was never a territorio nacional subject to the kind of 20th-century boundary carve-outs that affected Chaco/Formosa or the Patagonian territories), this has not been verified against a period-accurate historical source confirming no border adjustments occurred with neighboring Catamarca, Córdoba, San Juan, or San Luis during 19th- or early-20th-century territorial reorganizations. This should be checked before treating a modern polygon as a safe proxy for the earliest decades of this span, rather than assumed.

### oq-data-coverage-gap-1853-1900

**No data identified for La Rioja between 1853 and 1900**

The routing decision's proposed span is anchored to the 1853 constitutional default, but the underlying Juan's subnational panel data for this unit is understood to begin around 1900 (consistent with the sibling province entries). This leaves roughly 47 years (1853-1900) where the polity exists in this table but is not known to be backed by any routed data row. It is worth confirming whether earlier La Rioja-specific statistics exist in any ingested source and, if so, whether they were missed by the routing pass, or whether the 1853 start is purely a structural/administrative-history choice with no corresponding data in this window.
