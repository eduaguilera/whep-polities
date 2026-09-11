---
polity_code: ARG-LAPAMPA-1900-1951
polity_name: La Pampa (national territory of Argentina)
start_year: 1900
end_year: 1951
type: subnational
iso3: ARG
continent: South America
cow: NA
status: draft
last_ingest: 2026-09-11
sources: [juan-subnational]
polygon_source: gadm-4.1-adm1
polygon_feature_id: null
polygon_feature_year: null
polygon_status: unassigned
predecessor: []
successor: []
container:
  - code: ARG-1902-2025
    start_year: 1902
    end_year: 1951
    basis: La Pampa remained a national territory of Argentina under this boundary era, from the start of the extract's coverage in 1900 through to its 1951 provincialization.
---

# La Pampa (national territory of Argentina)

## Summary

This entry covers La Pampa, in the central Argentine pampas west of Buenos Aires province, during its era as a Territorio Nacional -- a national territory directly administered from Buenos Aires by an appointed governor, without provincial autonomy or full congressional representation -- from 1900 through its 1951 elevation to full provincial status. The type is `subnational` because sovereignty over this territory was always Argentina's; the row exists to carry the distinct pre-province reporting/administrative unit, which the routed statistical extract (juan-subnational, ARG La Pampa rows for 1900-1950) tabulates separately from both the national ARG total and from the later province. The 1951 end_year matches the pre-decided Argentina country convention's fixed provincialization date for La Pampa (an explicit, administratively-grounded departure from the convention's default 1853 provincial-start rule for other provinces); the 1900 start_year instead matches where the routed data begins, not the territorio's actual 1884 legal creation by Ley 1532 -- a gap from the Chaco sibling entry's convention that is flagged as an open question rather than resolved silently. Without this entry, the unit's 1900-1950 data would have no home: the routing decision found zero name candidates and zero boundary matches against any existing polity, and folding it into the already-existing province row (ARG-LAPAMPA-1951-2025, start_year 1951) would violate that row's own start_year rather than extend a genuinely continuous administrative unit across a status change that Argentine administrative law treats as a real break.

**Why this entry exists.** This entry was created by the agent-harness routing pipeline to carry Argentine subnational statistics tabulated under "La Pampa" for years before provincial status existed. Input data: the juan-subnational extract, ARG La Pampa rows spanning 1900-1950 (the pre-provincialization portion of the unit's full 1900-2023 coverage; the post-1950 portion is already routed to ARG-LAPAMPA-1951-2025). The routing decision found zero name-candidate matches and zero boundary matches against any existing polity for this unit, so match_existing was unavailable, and the pre-decided Argentina country convention's fixed 1951 provincial-start date for La Pampa meant the 1900-1950 data could not be folded into the existing province row without violating that row's own start_year -- so it would otherwise have been silently absorbed into the national ARG total, a container roughly ~90x the territory the figures actually measure. What confirms this entity was distinct: Ley 1532 (16 October 1884) established the Territorio Nacional de La Pampa as a legally and administratively distinct national territory, directly governed from Buenos Aires by an appointed governor rather than folded into an existing province, and the 1951 provincialization law marks a clean administrative break -- the same legal-record basis used for the sibling ARG-CHACO-1884-1951 entry.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is attached at this entry (`polygon_status: unassigned`, `polygon_feature_id: null`). The intended source is `gadm-4.1-adm1`, which is registered but whose locally-fetched extract is a curated 81-country subset that does not include Argentina -- so the slug is recorded as the intended registered source without a fetched feature (`registered_source_unfetched`), matching the route given in the routing decision and matching how the sibling ARG-CHACO-1884-1951 entry was authored, rather than `new_source_needed`/`none_available` with `polygon_source: none`.

**Territory description:** The Territorio Nacional de La Pampa corresponds closely to the modern Argentine province of La Pampa, in the central pampas region south of Córdoba and San Luis provinces, west of Buenos Aires province, and north of Río Negro -- a reader can locate it on a modern map as the roughly rectangular province directly west of Buenos Aires province's southern half. The modern province covers approximately 143,440 km². This is a stated figure about the present-day administrative unit, not a measurement of any geometry attached to this entry (none is attached), and the historical territorio nacional's internal boundaries relative to neighboring territories were subject to decree adjustments during 1884-1951 that have not been checked here -- so this figure should not be treated as validated for this entry's 1900-1951 span until a polygon is fetched and the boundary history is confirmed (see oq-boundary-vintage-proxy).

## Predecessors and successors

La Pampa was established as the Territorio Nacional de La Pampa by Ley 1532 of 16 October 1884, one of the national territories carved from land taken during the Conquista del Desierto campaigns, administered directly from Buenos Aires by an appointed territorial governor without provincial autonomy or full congressional representation. This entry covers the 1900-1951 portion of that era, matching the span of the routed statistical data rather than the 1884 legal creation date (see d-code-and-span and oq-start-year-1900-vs-1884-creation). No predecessor entry exists: 1900 is simply where the routed extract's La Pampa data begins, not a change of administrative status, so `predecessor` is left empty rather than pointing at a national ARG row that would represent sovereignty rather than the distinct territorio-nacional reporting unit. The successor is the Province of La Pampa, created by national law in 1951 elevating the territorio to full provincial status -- already represented by the existing row ARG-LAPAMPA-1951-2025. That page's own `predecessor` field is currently empty rather than pointing back here, which a prior version of this page tried to paper over with a one-directional `successor` claim that the chain-integrity gate correctly rejected; `successor` is now left empty here too, with the needed reciprocal edit recorded in oq-successor-edge-needs-reciprocal-edit instead of asserted unilaterally.

## Sourced claims

- Ley 1532 (16 October 1884) created the Territorio Nacional de La Pampa, together with Chaco, Formosa, Misiones, Neuquén, Río Negro, Chubut, Santa Cruz, Tierra del Fuego and Los Andes, under a unified national-territory administrative framework directly governed from Buenos Aires.
- National law promulgated in 1951 elevated the Territorio Nacional de La Pampa to full provincial status as the Province of La Pampa, ending its status as a directly-administered national territory -- the same 1951 date the pre-decided Argentina country convention uses to fix ARG-LAPAMPA-1951-2025's start_year.

## Decisions

### d-code-and-span

**Code ARG-LAPAMPA-1900-1951, span fixed by the extract's own coverage rather than the territorio's 1884 legal creation**

Following the ARG-CHACO-1884-1951 precedent, this page uses the dominant <ISO3>-<SUBUNIT>-<start>-<end> pattern rather than a bespoke code, since La Pampa is a standard Argentine national-territory/province unit, not a historical territory with a name of its own outside that administrative system. The start_year is set to 1900, not 1884 (the year Ley 1532 legally created the Territorio Nacional de La Pampa), because the routing decision's era_of_this_page explicitly scopes this page to the unit's data coverage of 1900-2023, and the pre-decided country convention only fixes 1951 as the provincialization end date -- it says nothing that would justify back-dating the row's start past where the data begins. Extending to 1884 without data to support it would misrepresent what this entry captures. This is flagged as an open question below rather than silently assumed correct, since Chaco's sibling entry did use its legal creation year (1884) as start_year with no data before it noted as a gap, and a future editor may want to reconcile the two conventions.

### d-no-successor-edge

**Dropped the successor claim to ARG-LAPAMPA-1951-2025 after the prior submission was rejected for asymmetry**

The previous version of this page declared `successor: [ARG-LAPAMPA-1951-2025]`, but that page (which already exists and cannot be edited from here) declares `predecessor: []`, so validate_chain_integrity rejected the one-directional edge. Rather than re-asserting an edge only this page claims, `successor` is left empty here, and the relationship is instead stated in prose in `predecessors_and_successors` plus recorded as an open question naming the exact edit the other page needs. This mirrors the ARG-CHACO precedent (d-container-era-split / oq-successor-code-unsettled), where an unconfirmed sibling edge was also left out of the typed field rather than guessed or forced.

## Open questions

### oq-successor-edge-needs-reciprocal-edit

**ARG-LAPAMPA-1951-2025 needs its `predecessor` field updated to point back at this entry**

This page's prose states that La Pampa's provincial era (1951-2025) is carried by the existing row ARG-LAPAMPA-1951-2025, but that row currently declares `predecessor: []`, not this code. validate_chain_integrity treats predecessor/successor as a two-directional relationship checked against a baseline in both directions, so a one-sided claim from this page alone would fail the gate -- which is exactly what happened to the previous submission of this page. The correct fix is on the OTHER page: ARG-LAPAMPA-1951-2025's `predecessor` field should be changed from `[]` to `[ARG-LAPAMPA-1900-1951]` in a future edit. Until that edit lands, `successor` here is deliberately left empty rather than re-asserting the rejected one-directional edge.

### oq-start-year-1900-vs-1884-creation

**Should this entry's start_year be 1884 (legal creation) instead of 1900 (data coverage start)?**

Ley 1532 of 16 October 1884 created the Territorio Nacional de La Pampa alongside Chaco, Formosa, Misiones, Neuquén, Río Negro, Chubut, Santa Cruz, Tierra del Fuego and Los Andes -- the same act the sibling ARG-CHACO-1884-1951 entry uses for its own 1884 start_year. This page instead starts at 1900, matching only where the routed data begins, per the routing decision's era_of_this_page framing. That leaves 1884-1900 administratively unaccounted for by any polity row, an inconsistency with the Chaco precedent that a future editor should resolve -- either by moving this entry's start_year to 1884 (if no data exists for 1884-1900, that is not itself disqualifying, since Chaco's entry also carries years before its own data begins) or by confirming 1900 is deliberate for some reason not stated in the routing decision.

### oq-boundary-vintage-proxy

**No polygon fetched yet for La Pampa's historical territorio nacional extent**

polygon_route was registered_source_unfetched against gadm-4.1-adm1, exactly as for the province-era sibling and for ARG-CHACO-1884-1951, but the locally-fetched GADM 4.1 admin-1 extract is a curated 81-country subset that excludes Argentina entirely, so no ARG.* feature (e.g. the ARG.11_1 feature the province-era page already cites) can be attached here even as a proxy. A future ingest step needs the global GADM 4.1 release or an IGN Argentina provincial shapefile fetched locally. Until then this entry carries no measured area, and the modern province's ~143,440 km² figure should not be treated as validated for the 1900-1951 territorio-nacional-era span, since national-territory limits were subject to decree adjustments relative to neighboring territories (Neuquén, Río Negro, Buenos Aires province, Córdoba, San Luis) that have not been checked.
