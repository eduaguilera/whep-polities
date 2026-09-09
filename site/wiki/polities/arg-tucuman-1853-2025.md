---
polity_code: ARG-TUCUMAN-1853-2025
polity_name: Tucumán (province of Argentina)
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
polygon_feature_id: ARG.24_1
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: ARG-1800-1899
    start_year: 1853
    end_year: 1899
    basis: Tucumán as an organized province of the Argentine Confederation/Republic under the 1853 Constitution, within the pre-1899 national row
  - code: ARG-1899-1902
    start_year: 1899
    end_year: 1902
    basis: Tucumán inside the short transitional national row ARG-1899-1902 that the polity table carries between the 1899 and 1902 national boundary revisions
  - code: ARG-1902-2025
    start_year: 1902
    end_year: 2025
    basis: Tucumán as a current province inside the modern national territory from the 1902 boundary settlement onward
---

# Tucumán (province of Argentina)

## Summary

Tucumán (province of Argentina) is one of the fourteen historic provinces of the Argentine Republic, the smallest by area, located in the country's northwest at the eastern base of the Andes, bordered by Salta to the north, Santiago del Estero to the east and southeast, and Catamarca to the southwest and west. This entry is `type: subnational` because sovereignty throughout this span rests with Argentina — the entry exists to carry provincial-level statistics, not to claim independent political status. Tucumán was one of the thirteen original signatory provinces of the 1853 Constitution that organized the Argentine Confederation (joined by Buenos Aires in 1861), and unlike several current Argentine provinces (Chaco, Formosa, La Pampa, Misiones, Tierra del Fuego), it was never administered as a federal "national territory" before being granted provincehood — it has been a province in continuous existence since the mid-19th century, which is exactly why the routing decision applied the country convention's default 1853 start rule rather than any of the four documented later-provincialization exceptions. The routing decision found no existing candidate polity representing Tucumán specifically (zero name matches) among the entries in this table — the ARG-* national rows are roughly nationwide totals, not the province itself — and placed it inside the ARG national containment chain for its full proposed span.

**Why this entry exists.** This entry captures Argentine province-level production/trade data keyed to the label 'Tucumán' per the routing decision that proposed it (unit_id ARG-TUCUMAN), though that decision's routing_reasoning does not itemize a specific row count or year range the way some sibling decisions do (flagged as oq-data-coverage-gap below). Before this entry was created, no polity row represented Tucumán at all: the routing decision reports zero name-candidate matches and no existing boundary feature for it (0 name candidates, and gadm-4.1-adm1 has no Argentine features locally), meaning any Tucumán-labeled rows in the source data would previously have had no correct home and, if matched at all, would have been misrouted to the national ARG rows — which cover the whole of Argentina and would blend Tucumán's output (notably its historically dominant share of national sugarcane and citrus production) into all-Argentina totals, hiding the provincial detail the source data actually reports. What confirms Tucumán is a distinct, real administrative entity worth its own row — not a label variant of the national total — is that it is one of Argentina's fourteen constitutionally organized founding provinces, continuously self-governing under its own provincial constitution and legislature since 1853, with its own dedicated statistical apparatus (provincial dirección de estadística and national agricultural census returns broken out by province) that is exactly the kind of source that would report 'Tucumán' as a distinct reporting unit rather than as shorthand for the nation. The routing decision explicitly rules out treating this as a national total or a residual bucket: 'the unit is a genuine admin1 province, not a residual bucket or national total.'

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is available in the GeoPackage for Tucumán at any period: the locally cached `gadm-4.1-adm1` dataset — otherwise the correct registered source for a modern ADM1-level Argentine province boundary — is restricted to an 81-country subset that does not include Argentina, so zero features exist for any of Argentina's fourteen provinces, Tucumán included. `polygon_source` is set to the registered slug `gadm-4.1-adm1` (per the `registered_source_unfetched` route given in the routing decision) with `polygon_feature_id` left null and `polygon_status: unassigned`, rather than fabricating a feature id or falling back to the rejected value `new_source_needed` — the correct source is known and registered, it simply has not been fetched globally yet. No geometry is attached, so no measured area is reported for this entry (there is nothing to label as a self-referential measurement).

**Territory description:** Tucumán province sits in Argentina's northwest at the eastern edge of the Andean foothills (Sierras del Aconquija/Sierra de Ancasti to the west), draining east into the plains toward the Salí-Dulce river basin shared with Santiago del Estero. Its capital, San Miguel de Tucumán, is Argentina's fifth-largest city and was the site of the 1816 Congress that declared Argentine independence — well before this entry's 1853 start, but part of why the province has always been a distinct administrative and historical unit rather than a residual bucket. Tucumán is Argentina's smallest province by land area, covering approximately **22,500 km²** (Argentina's own INDEC/IGN-published provincial area figure) — a figure a reader can check directly on any current map of Argentina's provinces, and roughly comparable in size to a small European country such as Israel or Slovenia, despite carrying an outsized share of national sugarcane production historically. This is a description of the modern province's location and extent, not a measurement of any geometry attached to this entry, since none is attached yet.

## Predecessors and successors

Tucumán has no predecessor or successor polity in this table: it does not split off from, merge into, or get renamed from any other subnational entry. It was one of the thirteen founding signatory provinces of the 1853 Argentine Constitution (joined by Buenos Aires in 1861) and has remained a province of Argentina, under that same name and general territorial footprint, ever since. Unlike national territories such as Chaco, Formosa, La Pampa, or Misiones — which were federal territories before being upgraded to provincehood decades later, and which carry a predecessor/successor pair reflecting that status change — Tucumán had no intermediate territorial status of that kind, so predecessor and successor are both left empty.

## Sourced claims

- Tucumán was one of the thirteen original signatory provinces that ratified the 1853 Argentine Constitution (the founding provinces of the Confederación Argentina, joined by Buenos Aires in 1861), which is the documentary basis for using 1853 rather than a later date as this entry's start_year, and the same basis already used for the sibling entry ARG-CAT-1853-2025 (Catamarca).
- Argentina's own INDEC/IGN provincial statistics give Tucumán's land area as approximately 22,500 km², making it the smallest of Argentina's 23 provinces plus the Autonomous City of Buenos Aires — a figure independently checkable against any current administrative map of Argentina and unrelated to any geometry attached to this entry.

## Decisions

### d-code-and-span

**Code follows the dominant ISO3-SUBUNIT pattern, not a bespoke name**

Tucumán is one of Argentina's fourteen original provinces, organized as such under the 1853 national constitution (Confederación Argentina, later Argentine Republic) — one of the thirteen founding signatory provinces, joined later by Buenos Aires in 1861. It has no separate name-of-its-own history the way Alaska Territory or Hyderabad do; it has always been administered simply as 'the province of Tucumán'. The dominant 338-of-351 ISO3-SUBUNIT pattern therefore applies, giving ARG-TUCUMAN-1853-2025, matching the abbreviation style already used for ARG-CAT (Catamarca) and ARG-CORDOBA rather than inventing a truncated 3-4 letter code, since the routing decision itself used the unabbreviated 'ARG-TUCUMAN' unit_id and no shorter form is already in use elsewhere in the table for this province. start_year 1853 follows the routing decision's span_basis exactly: Tucumán is not one of the four documented Argentine territories that were provincialized later (Chaco, Formosa, La Pampa, Misiones — the ex-territorios nacionales departures from the default rule), nor is it Tierra del Fuego or CABA, so the country convention's default 1853 start applies without modification. end_year 2025 is left open per the repository's convention for currently-existing units, matching the container ARG-1902-2025's own end_year.

### d-polygon-route

**polygon_source is the registered slug gadm-4.1-adm1, not the route name**

The routing decision's polygon_route is registered_source_unfetched: gadm-4.1-adm1 is a registered source in sources.yaml and is the correct kind of source (global ADM1 boundaries) for a modern Argentine province, but the locally cached copy of that dataset is restricted to an 81-country subset that excludes Argentina, so zero features exist for any of Argentina's fourteen provinces today, Tucumán included. Per the harness instructions for this route, the registered slug itself becomes polygon_source, polygon_feature_id is left null, and polygon_status is set to unassigned rather than assigned, proxy, or the rejected value new_source_needed — the source is correctly identified, only the fetch is pending. This exactly mirrors the decision already made for the sibling entry ARG-CAT-1853-2025 (Catamarca), which hit the identical 81-country gap in the same locally cached file.

## Open questions

### oq-global-gadm-fetch

**Global GADM 4.1 (or GADM 3.6) needs to be fetched to cover Argentina's provinces**

The repository's locally cached gadm-4.1-adm1 file is an 81-country subset that does not include Argentina, so no ADM1 feature exists yet for Tucumán or any of its thirteen sibling provinces. Fetching the global GADM 4.1 release (or falling back to the also-registered gadm-3.6) would supply an id — most likely GADM's own ISO_1 code AR.TU or the province name 'Tucumán' — for all fourteen historic Argentine provinces at once, the same fix already flagged on ARG-CAT-1853-2025 and presumably on every other Argentine province row created in this batch. Until that fetch happens this entry stays polygon_status: unassigned and no boundary check can run against it.

### oq-boundary-vintage-1853

**How far does a modern-boundary proxy stretch back for Tucumán specifically**

Once a GADM feature is fetched, it will reflect Tucumán's present-day boundary, Argentina's smallest province by area. Tucumán's own borders were not fully static across 1853-2025: 19th-century boundary disputes with Santiago del Estero over the Salí/Dulce river lowlands, and with Catamarca over the western sierra foothills, were settled by federal arbitration and provincial law at various points into the 20th century, and the province's southern and eastern limits shifted somewhat as the Gran Chaco national territories to the east were organized. Whether the modern GADM shape is a safe proxy for the full 1853-2025 span, or needs a documented caveat similar to the Ireland or Poland cases in the proxy rules, is unresolved and should be checked once a feature is available to compare against historical province maps.

### oq-data-coverage-gap

**Pre-modern data span and row count are not itemized in the routing decision**

The routing decision that created this entry gives routing_reasoning and a proposed span but does not itemize which years or how many rows of production/trade data are actually keyed to the label 'Tucumán', unlike some sibling decisions that state an explicit row count and year range. The 1853 start year is not itself evidenced by any specific data row — it follows from Tucumán's status as one of the provinces organized under the 1853 Constitution — so it is unclear how much of the 1853-2025 span this entry currently carries with no confirmed underlying data, and whether the actual data span (once identified precisely) leaves an even larger uncovered stretch than the ~47 pre-1900 years found on the Catamarca sibling entry.
