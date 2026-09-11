---
polity_code: ARG-LAPAMPA-1951-2025
polity_name: La Pampa (province of Argentina)
start_year: 1951
end_year: 2025
type: subnational
iso3: ARG
continent: South America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: gadm-4.1-adm1
polygon_feature_id: ARG.11_1
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: ARG-1902-2025
    start_year: 1951
    end_year: 2025
    basis: Provincia de La Pampa, created by national law in 1951 elevating the former Territorio Nacional de La Pampa to full provincial status, inside Argentina's 1902-2025 national chain through to the present
---

# La Pampa (province of Argentina)

## Summary

This page covers La Pampa, an Argentine province in the central pampas, from its 1951 elevation to full provincial status to the present day. The type is `subnational` because La Pampa has never held sovereignty of its own — it is an internal administrative division of Argentina, first governed (before this entry's start) as a national territory under an appointed governor, then from 1951 as a self-governing province with its own constitution and elected officials within the Argentine federal system. Unlike the sibling Chubut entry, which spans both its Territorio Nacional and provincial eras in a single row (1884-2025), this entry's start_year is fixed at 1951 by the pre-decided Argentina country convention, which explicitly lists La Pampa as one of the departures from the default 1853 provincial-start rule, precisely because 1951 is the administratively grounded date of provincialization rather than an artifact of when the extract's data happens to begin. That choice necessarily leaves the unit's earlier 1900-1950 Territorio Nacional-era data unrouted by this entry (see the open question below), a gap the routing decision itself flags rather than papers over.

**Why this entry exists.** This entry captures the 'La Pampa' panel unit from the Argentine subnational data source, whose reported coverage spans 1900-2023 — but per the pre-decided country convention, only the 1951-2023 portion of that run belongs to this polity, since 1951 is La Pampa's administratively justified start_year (the year of provincialization) rather than the data's own 1900 start. Before this decision, La Pampa had no representing polity at all (0 name candidates, 0 boundary matches in gadm-4.1-adm1), so match_existing was unavailable and create_new was the only option. What confirms La Pampa is a distinct administrative entity, separate from any other ARG row, is its unbroken legal existence as a named jurisdiction: organized as a Territorio Nacional in 1884 during Argentina's pampean/Patagonian territorial expansion, then elevated by national law to the Provincia de La Pampa in 1951 — a jurisdiction Argentina's own provincial system continues to recognize as one of its 23 current provinces, and the same unit the country convention names explicitly as a departure case requiring its own start_year rather than the 1853 default applied to the original historic provinces.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is present in the GeoPackage for this unit at any period. `polygon_source: gadm-4.1-adm1` with `polygon_status: unassigned` reflects the registered_source_unfetched route: GADM 4.1's global admin-1 layer does digitize Argentine provincial boundaries and the source family is already registered in sources.yaml, but the locally fetched GADM 4.1 adm1 subset used by this repository is curated to 81 countries and currently excludes Argentina (0 ARG features). No other registered source can substitute — cshapes carries only national-level ARG polygons, and none of the other registered sources (paine-2024, cliopatria, constructed, reporting-areas, histogis-1860-habsburg) cover Argentine provincial subdivisions.

**Territory description:** La Pampa occupies the central pampas of Argentina, bordered by Buenos Aires province to the east, Córdoba and San Luis to the north, Mendoza and Neuquén to the west, and Río Negro to the south — a reader can locate it as the roughly rectangular province lying directly west of Buenos Aires province, centered near 37°S, 65°W, with its capital at Santa Rosa. The modern province covers approximately 143,440 km2, roughly the size of Nepal or Greece. Its external boundaries were fixed largely by the 1884 territorial organization of the pampean frontier and by subsequent boundary agreements with neighboring provinces, and have been stable since the 1951 provincialization; no measured-from-geometry figure is available here since no polygon is yet attached.

## Predecessors and successors

La Pampa has no predecessor entry in this database: its earlier existence as the Territorio Nacional de La Pampa (from 1884) is not currently captured by any polity row (see open question oq-territorio-nacional-lapampa-1900-1950), so this entry begins directly at provincialization in 1951 rather than continuing from an existing predecessor row, unlike Chubut's single-row treatment of the same kind of transition. It has no successor either: La Pampa remains one of Argentina's 23 current provinces, and end_year 2025 reflects the country convention's open-ended present-day cutoff (capped at the containing national row ARG-1902-2025's own end_year), not any dissolution, renaming, or absorption event.

## Sourced claims

- National law in 1951 elevated the Territorio Nacional de La Pampa (established 1884 as part of Argentina's late-19th-century organization of the pampean and Patagonian frontier territories) to full provincial status as the Provincia de La Pampa, giving it its own elected governor and legislature for the first time.
- The routing verdict for this unit (ARG-LAPAMPA in routing_verdicts.csv) reports a single panel unit ('La Pampa') with data coverage spanning 1900-2023, of which only 1951-2023 falls within this polity's declared 1951-2025 span; the 1900-1950 portion is explicitly noted as uncaptured by any existing polity.

## Decisions

### d-span-starts-1951-not-1900

**Span fixed at 1951-2025 per country convention, leaving 1900-1950 unrouted here**

The pre-decided Argentina country convention explicitly lists La Pampa as a departure from the default 1853 provincial-organization start rule: its administratively justified start_year is 1951, the year national law granted La Pampa full provincial status (ending its status as a Territorio Nacional, itself established in 1884). This entry therefore covers only 1951-2025. The routing verdict's own data run for this unit spans 1900-2023, so 51 years of pre-provincial Territorio Nacional data (1900-1950) are NOT captured by this row and are explicitly flagged in the routing_concerns as needing a separate 'Territorio Nacional de La Pampa' polity, which was outside the scope of this pre-decided convention and is raised here as an open question rather than silently folded in or silently dropped.

### d-single-container-era-not-three

**Container is a single ARG-1902-2025 edge, not the three-era Argentine national chain**

Sibling ARG subnational pages (e.g. arg-chubut-1884-2025.md) that start before 1899 must tile across ARG-1800-1899, ARG-1899-1902, and ARG-1902-2025 to cover their full span without a gap. La Pampa's provincial span begins in 1951, entirely inside the ARG-1902-2025 national-chain segment (1902-2025), so a single container edge fully tiles 1951-2025 with no gap; the earlier national-chain segments are irrelevant here precisely because this row does not reach back before 1902 (see d-span-starts-1951-not-1900).

## Open questions

### oq-territorio-nacional-lapampa-1900-1950

**Where does the 1900-1950 Territorio Nacional de La Pampa data belong?**

The routing verdict for ARG-LAPAMPA reports data coverage of 1900-2023 for this unit, but the country convention fixes this provincial polity's start_year at 1951 (the year of provincialization), so the 1900-1950 portion — when La Pampa was a Territorio Nacional (established 1884) — is not covered by ARG-LAPAMPA-1951-2025 and is not covered by any other existing polity either. The routing_concerns explicitly flag this as needing a separate polity, analogous to how Chubut's page (arg-chubut-1884-2025.md) instead chose to span both the Territorio Nacional and provincial eras in one row rather than split at the status-change year. Whether La Pampa should follow the Chubut precedent (one row, 1884-2025) or keep the two eras separate as this convention currently implies is unresolved and should be decided before or alongside creating a companion 'Territorio Nacional de La Pampa' polity, since as written the pre-1951 data has no home.

### oq-gadm-argentina-unfetched

**gadm-4.1-adm1 does not yet include Argentina locally**

polygon_source is set to gadm-4.1-adm1 with polygon_status unassigned (registered_source_unfetched) because GADM 4.1's global admin-1 release does digitize Argentine provinces and the source family is already registered in sources.yaml, but the locally fetched subset used by this repository is curated to 81 countries and currently excludes Argentina entirely (0 ARG features). Until Argentina's layer is fetched into the local GADM 4.1 adm1 dataset, no polygon can be attached to this or any other Argentine province row, and the modern boundary (essentially stable since 1951, per the routing's vintage_risk note) would in any case only be a low-risk proxy for the full 1951-2025 span, not an exact contemporaneous boundary.
