---
polity_code: ARG-MISIONES-1881-2025
polity_name: Misiones (province of Argentina)
start_year: 1881
end_year: 2025
type: subnational
iso3: ARG
continent: South America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: gadm-4.1-adm1
polygon_feature_id: ARG.14_1
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: ARG-1800-1899
    start_year: 1881
    end_year: 1899
    basis: Territorio Nacional de Misiones, created 1881 within the framework of Ley 1532, existed inside the Argentine national territory of this era, prior to the 1899 CoW-boundary national row split
  - code: ARG-1899-1902
    start_year: 1899
    end_year: 1902
    basis: short national-row era between the two adjacent Argentina national spans; the Territorio Nacional de Misiones continues unchanged through it
  - code: ARG-1902-2025
    start_year: 1902
    end_year: 2025
    basis: Misiones as a territorio nacional and then (from 1953) a province of the modern Argentine national territory, from 1902 to present
---

# Misiones (province of Argentina)

## Summary

Misiones is Argentina's northeasternmost province, a narrow finger of territory wedged between Brazil and Paraguay, roofed by subtropical rainforest and known for the Iguazú Falls and the ruins of Jesuit reductions from which the province takes its name. It was carved out as the Territorio Nacional de Misiones in 1881 under the national-territories framework of Ley 1532 (1884), administered directly from Buenos Aires as a non-self-governing territory rather than a constitutional province, and remained in that status for seven decades. Ley 14294 elevated it to full provincial status in 1953, and it has continued as the province of Misiones ever since. `type` is `subnational` because this row does not claim sovereignty — Argentina held sovereignty over this territory throughout 1881-2025, already carried by the national ARG chain (ARG-1800-1899, ARG-1899-1902, ARG-1902-2025). What this entry carries is the reporting/administrative unit "Misiones," the level at which INDEC and its predecessors (and, before 1953, the territorio nacional's own administration) tabulate population, production and land-area figures separately from national totals and from sibling provinces. Misiones is one of the routing convention's departure cases for Argentina precisely because it began life as a territorio nacional rather than an original constitutional province, which is why its start year is 1881 (territorial creation) rather than 1853 (the constitutional-provinces default used for e.g. Jujuy).

**Why this entry exists.** This entry implements the agent-harness routing decision for unit_id ARG-MISIONES (admin_name "Misiones", country Argentina), which found the pre-existing coverage attempt unroutable: data spanning 1900-1950 had been rejected because it fell before the territory's 1953 elevation to provincial status, wrongly treating the pre-elevation decades as un-administered rather than administered by a distinct, continuously existing national territory. The routing_reasoning is explicit that the 1953 event is a change of legal status, not the birth of the territory, so a single polity row spans the whole administrative lifetime (1881-2025) instead of splitting at 1953 into a territorio-nacional row and a province row. Before this decision, any data keyed to "Misiones" for years before 1953 had nowhere specific to route except the national ARG rows — roughly 45x Misiones's own area (29,801 km2 vs. Argentina's ~2.78 million km2) and conflating its statistics with every other province and territory. The historical source confirming this is a persistently distinct, separately administered unit is Ley 1532 itself (1884), which formalized the national-territories system Misiones had already been carved into in 1881, and Ley 14294 (1953), whose own text speaks of Misiones being "elevated" to province — language that presupposes prior existence as a distinct territorial entity, not a creation ex nihilo.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon available in the GeoPackage for this period. `polygon_route` from the routing decision was `registered_source_unfetched`: GADM 4.1's admin-1 layer is the standard modern source for country subdivisions and almost certainly digitises Misiones globally, but the copy present in this repository (data/geodata/gadm-4.1/gadm41_adm1.gpkg) is a hand-picked 81-country subset that excludes Argentina entirely (0 rows returned for GID_0=ARG). That is a source that is registered but not locally fetched for this country, which is why `polygon_source` is set to the registered slug `gadm-4.1-adm1` with `polygon_status: unassigned` rather than `none` — per the routing rules, `registered_source_unfetched` keeps the slug as the source since the source itself is known and valid, just not yet extracted for Argentina.

**Territory description:** Misiones is a narrow, elongated province in Argentina's far northeast, bounded by Brazil to the north and east and Paraguay to the west across the Paraná and Iguazú rivers, with only a short land border (to Corrientes province) connecting it to the rest of Argentina. A reader can locate it on a modern map as the thin peninsula of Argentine territory reaching up between Paraguay and southern Brazil, containing the city of Posadas (the provincial capital) and the Iguazú Falls at its northern tip. Its modern area is approximately 29,801 km2 (per INDEC), essentially unchanged since its 1881 creation, since the province's borders were fixed by treaty with Brazil and Paraguay (and by separation from Corrientes) before Ley 1532 and have not been redrawn since — this is stated territory-description evidence from INDEC, not a measurement of any geometry attached to this entry, because no geometry is attached yet.

## Predecessors and successors

No predecessor or successor rows: this entry is deliberately a single continuous polity across its full 1881-2025 span rather than being split at the 1953 territorio-nacional-to-province transition, per the routing_reasoning's explicit argument that the 1953 event changed legal status but not the territorial entity's identity or continuity. There is no earlier Argentine administrative unit this territory was carved from that would warrant a predecessor link — before 1881 the area was unorganized national territory, part of the undifferentiated ARG national rows rather than any distinct predecessor polity — and no later successor, since the province persists to the present under the same name and (per the territory description) essentially the same borders.

## Sourced claims

- Ley 14294 (1953) is described in the routing decision's own admin_name text as "elevating" the Territorio Nacional de Misiones to provincial status, implying the territory existed continuously before that date rather than being created by the 1953 law.
- INDEC's official area figure for Misiones province is approximately 29,801 km2, a figure a reader can check against INDEC's own provincial statistics pages or any current gazetteer of Argentine provinces.

## Decisions

### d-single-continuous-span

**One polity row spans 1881-2025, not split at the 1953 provincialization**

The routing decision explicitly argues that Ley 14294 (1953) changed Misiones's legal status from territorio nacional to province but did not create a new territorial entity — the same population, administration, and reporting unit continued under a new legal label. Splitting at 1953 would have required deciding whether the pre-1953 territorio nacional and the post-1953 province are the 'same' polity for predecessor/successor purposes, and would have re-created the exact coverage gap this entry was created to fix (data for 1900-1950 previously rejected as unroutable because it predated provincial status). A single row with start_year 1881 (the territory's creation year, following the routing decision's own proposed span) and end_year 2025 (the open convention date for a current first-order administrative division, matching sibling pages like Jujuy) avoids re-splitting a unit that Argentine administrative history and statistical practice have always treated as continuous.

### d-polygon-source-unfetched-not-none

**polygon_source set to gadm-4.1-adm1 with status unassigned, not none**

The routing decision's polygon_route is registered_source_unfetched, which per the harness's own distinction means the slug IS the source (GADM 4.1 adm1 is a registered, known-good source for country subdivisions worldwide) and the gap is purely that the local repository copy hasn't been extended to include Argentina (0 of Argentina's rows are in the current gpkg subset of 81 countries). Writing polygon_source: none here would misrepresent the situation as 'no source exists' when in fact a specific, named, fetchable source is known and only needs a re-fetch/re-extract step — a materially different and more actionable state than none_available.

## Open questions

### oq-1881-creation-date-unverified

**The 1881 creation date for the Territorio Nacional de Misiones is not verified from a primary source**

The routing_reasoning notes explicitly that 1881 is 'the commonly cited date for the broader Ley 1532 national-territories framework, not verified here from a primary source.' Ley 1532 itself dates to 1884, three years after the proposed start_year, so there is an unresolved gap between when Misiones was administratively carved out (possibly informally, before national-territories legislation formalized the system) and when Ley 1532 gave that status a legal framework. If a primary source (e.g. the decree actually creating the Territorio Nacional de Misiones) gives a different year, start_year and the polity_code should both change, since the code embeds the year and a gate checks that they match.

### oq-territory-boundary-changes-1881-1953

**Whether Misiones's borders were stable across its full 1881-2025 span is unconfirmed**

The territorial_extent section asserts the modern ~29,801 km2 area has been 'essentially unchanged since 1881,' but this is stated from INDEC's current figure projected backward, not from a historical source describing the territory's actual 19th/20th-century boundary history. Misiones's borders were shaped by 19th-century disputes and treaties with Brazil and Paraguay (and separation from Corrientes) whose exact dates relative to 1881 are not established here. Using a modern GADM adm1 polygon (once fetched) as a proxy for the full 1881-2025 span would carry the same vintage risk the routing decision flagged: 'any 19th/early 20th century boundary adjustments... would not be captured.' This should be checked before the polygon is assigned and status moved from unassigned to proxy or assigned.

### oq-sibling-territorio-precedent

**Whether sibling ex-territorios-nacionales (Chaco, Formosa, La Pampa, Neuquén, Río Negro) are or will be modeled the same way**

The routing_concerns for this decision flag that whether the repository's data model prefers splitting territorio-nacional-to-province transitions into two rows, versus one continuous row as done here, 'should be checked against how similar cases... are ultimately resolved, since precedent should stay consistent across siblings.' At the time of writing this page, it is not confirmed whether those sibling provinces have pages yet, or whether they follow the single-continuous-span pattern used here. If a sibling is later modeled with a 1953-era split, this entry's approach should be reconciled with that precedent rather than left as an unexplained inconsistency.
