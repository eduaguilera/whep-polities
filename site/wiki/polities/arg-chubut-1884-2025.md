---
polity_code: ARG-CHUBUT-1884-2025
polity_name: Chubut (territory/province of Argentina)
start_year: 1884
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
    start_year: 1884
    end_year: 1899
    basis: Territorio Nacional del Chubut, created by Ley 1532 (1884), administered as a national territory of Argentina under the pre-1899 national chain
  - code: ARG-1899-1902
    start_year: 1899
    end_year: 1902
    basis: continuation of Territorio Nacional del Chubut inside Argentina during the short 1899-1902 national-chain segment
  - code: ARG-1902-2025
    start_year: 1902
    end_year: 2025
    basis: Territorio Nacional del Chubut (to 1955) and then Provincia del Chubut (from Ley 14408, 1955) inside Argentina's 1902-2025 national chain, through to the present
---

# Chubut (territory/province of Argentina)

## Summary

This page covers Chubut, an Argentine administrative division in central Patagonia, from its creation as a Territorio Nacional in 1884 through its 1955 elevation to full provincial status and up to the present. The type is `subnational` because Chubut has never held sovereignty of its own: it was and remains an internal administrative unit of Argentina, first as a national territory governed by an appointed governor reporting to Buenos Aires, then (from 1955) as a self-governing province with its own constitution, legislature, and elected governor within the Argentine federal system. The entry exists to give a single, continuous polity row to statistics that were collected at the Chubut level well before 1955 — the earlier "unroutable" treatment (recorded in sibling verdicts for Chaco and Formosa, and implicitly for Chubut before this decision) wrongly assumed that pre-provincial data belonged to no clearly identified administration, when in fact the Territorio Nacional del Chubut was the same continuously governed territory, merely under a different constitutional status, as the later province. Spanning 1884-2025 in one row (rather than splitting at 1955) avoids leaving 1900-1954 data unrouted and avoids creating an artificial predecessor/successor break at a status change that did not alter the territory's boundaries or its identity as a single administered unit.

**Why this entry exists.** This entry captures Argentine national-level statistical series (e.g., Mitchell's International Historical Statistics-style agricultural/livestock series, per the routing decision) reported at the Chubut administrative level from approximately 1900 through the present (the routing decision cites a 1900-2023 data run). Those pre-1955 rows were previously left unrouted ("unroutable" segment 1900-1954) under a prior verdict that assumed provincial-level statistics could only be attributed to an administration once Chubut attained formal provincial status in 1955, incorrectly treating the earlier Territorio Nacional period as belonging to no identifiable sub-national administration even though it was the same continuously governed territory reporting the same kind of data. What confirms Chubut was a distinct, continuously identifiable administrative entity across this full span is its unbroken legal existence: created as Territorio Nacional del Chubut by Ley 1532 in 1884 and continued without interruption (only a change of constitutional status, not of territory or identity) as Provincia del Chubut under Ley 14408 in 1955 — the same jurisdiction is referenced by both its national-territory-era statistics and its post-1955 provincial statistics, which is why a single polity row spanning 1884-2025 is the correct match rather than two separate rows split at the 1955 status change.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is present in the GeoPackage for this unit at any period. The intended source is GADM 4.1's admin-1 layer, which does publish Argentine provincial boundaries globally, but the locally fetched subset of GADM 4.1 adm1 used by this repository is curated to 81 countries and does not currently include Argentina (0 features for ARG). This is recorded as `polygon_source: gadm-4.1-adm1` with `polygon_status: unassigned` (registered_source_unfetched route) rather than `none`, because the source family is registered in sources.yaml and the fix is to fetch Argentina's layer, not to find a different source. No construction from other registered sources is possible in the meantime: cshapes, the other Argentina-relevant registered source, carries only national-level ARG polygons and cannot be subdivided into provinces.

**Territory description:** Chubut occupies central Argentine Patagonia, bordered by the Atlantic Ocean to the east, Chile to the west, Río Negro province to the north, and Santa Cruz province to the south — a reader can locate it as the province directly north of the Santa Cruz/Chubut provincial line at roughly 44°S to 46°S latitude, containing the cities of Rawson (provincial capital), Comodoro Rivadavia, Trelew, and Puerto Madryn. The modern province covers approximately 224,686 km2, comparable in size to the United Kingdom. Chubut's external boundaries were substantially set by the original Ley 1532 partition of Patagonia and have been largely stable since, though the exact 1884 limits versus the 1955 provincial boundary used in Ley 14408 have not been checked against a primary source here (see open questions) — no measured-from-geometry figure is available since no polygon is yet attached.

## Predecessors and successors

Chubut has no predecessor entry: it was created directly by Ley 1532 in 1884 as a national territory carved from previously unorganized Patagonian land claimed by Argentina following the 1878-1885 "Conquista del Desierto" campaigns, not by splitting or merging with another polity already in the database. It has no successor entry either, since the entity persists to the present day as Provincia del Chubut, one of Argentina's 23 provinces; end_year 2025 reflects the country convention's open-ended present-day cutoff rather than any dissolution or absorption event. The 1955 transition from Territorio Nacional to Provincia (Ley 14408) is treated as an internal status change within this single polity row, not a predecessor/successor boundary, consistent with how the exemplar MAN-1950-1955 treats an administrative-tier change without creating a new row.

## Sourced claims

- Ley 1532 (16 October 1884) organized the Patagonian territories recently brought under effective Argentine administration into several Territorios Nacionales, including Chubut, with a capital eventually fixed at Rawson.
- Ley 14408 (1955) elevated the Territorio Nacional del Chubut to full provincial status as the Provincia del Chubut, giving it its own constitution and elected governor for the first time.
- Mitchell's International Historical Statistics and related Argentine national-territory production series report Chubut-level agricultural and livestock figures from at least 1900 onward, prior to its 1955 provincial elevation, which is the data this polity row is created to capture.

## Decisions

### d-code-follows-iso3-subunit-pattern

**Code follows the ISO3-SUBUNIT-start-end pattern despite ARG having no prior subnational rows**

ARG currently has zero subnational rows, so there is no country-specific precedent to follow, but the dominant pattern across the table (57 of 66 subnational rows, e.g. ESP-AS-1833-2025, DZA-CVD-1902-1919) is <ISO3>-<SUBUNIT>-<start>-<end>. Chubut is an ordinary Argentine administrative division with no separate historical identity outside Argentina's administrative hierarchy (unlike bespoke cases such as Hyderabad or the Ryukyus, which were distinct polities before incorporation), so the bespoke-code pattern does not apply. The chosen code is ARG-CHUBUT-1884-2025, matching the dominant pattern and setting the convention other Argentine provincial pages (Chaco, Formosa, etc.) should follow for consistency.

### d-span-starts-at-1884-not-1955

**Span starts at the 1884 creation of the Territorio Nacional, not at 1955 provincial elevation**

The routing decision explicitly argues that the country convention's start rule (fixing on provincial status, 1955 for Chubut) is too narrow: the governing policy is that a statistics-collection territory qualifies for a polity row regardless of whether it held provincial or national-territory status, and Chubut was one continuously administered unit from Ley 1532 (1884) through Ley 14408 (1955, provincial elevation) to the present. Starting the span at 1884 instead of 1955 is what allows the full 1900-2023 data run cited in routing_reasoning to be captured under one polity row rather than leaving 1900-1954 unrouted, which is the defect the routing decision was created to fix. This deliberately departs from the (as yet unrevised) ARG-CHACO and ARG-FORMOSA verdicts, which the routing_concerns field flags as inconsistent and likely needing the same fix.

## Open questions

### oq-ley-1532-creation-date

**Confirm the exact 1884 creation date and boundaries of Ley 1532 against a primary legal source**

The routing decision itself flags this as unconfirmed: 'Confirm the exact creation date of Territorio Nacional del Chubut (1884, Ley 1532) against a primary source before finalizing the span.' Ley 1532 (October 1884) created several Argentine national territories at once (Chubut, Río Negro, Neuquén, Santa Cruz, Chaco, Formosa, Misiones, La Pampa), and while secondary sources consistently cite 1884, the exact promulgation date and the original territorial boundaries assigned to Chubut specifically (which may differ from later adjustments, e.g. the 1955 Ley 14408 boundary used for provincial status) have not been checked against the law's text or against INDEC/IGN historical boundary records here.

### oq-sibling-verdicts-need-revision

**ARG-CHACO and ARG-FORMOSA verdicts likely need the same start-year correction**

routing_concerns notes that sibling verdicts already recorded for ARG-CHACO and ARG-FORMOSA treated their pre-elevation years (pre-1951 and pre-1955 respectively) as unroutable, which is the same defect this entry corrects for Chubut. If those verdicts are not revised to start at each territory's own Ley 1532 (or later, e.g. Ley 14294 for Chaco/Formosa in 1951) creation date, the pipeline will leave those provinces' early data unrouted while Chubut's is fully covered, producing an inconsistent treatment across otherwise-identical Argentine national-territory-to-province histories.

### oq-gadm-argentina-not-fetched

**No Argentine provincial boundary is actually present locally; gadm-4.1-adm1 excludes ARG**

polygon_route is registered_source_unfetched: the source family (GADM 4.1 admin-1) is registered in sources.yaml, but the locally fetched subset covers only 81 countries and does not include Argentina at all (0 features). Until Argentina's GADM adm1 layer (or an IGN Argentina provincial-boundaries source) is actually fetched and registered, this page carries no usable polygon feature, and polygon_status is unassigned rather than proxy or assigned. Fetching GADM's Argentina adm1 layer, or registering IGN's official provincial limits as a named source, would resolve this.

### oq-boundary-stability-1884-1955

**Whether Chubut's external limits before 1955 match the modern province is unverified**

Even once a modern provincial boundary is fetched, using it as a proxy for the 1884-1955 Territorio Nacional period is an approximation flagged in polygon_detail as carrying moderate vintage risk: Argentine national-territory boundaries were adjusted several times before their provinces were formally constituted (boundary disputes with Río Negro and Santa Cruz, and the definition used in Ley 14408 in 1955), and it is not yet confirmed whether the 1884 original limits differ materially from the present-day province's ~224,686 km2 extent.
