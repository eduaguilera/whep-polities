---
polity_code: BRA-PARAIBA-1889-2025
polity_name: Paraíba
start_year: 1889
end_year: 2025
type: subnational
iso3: BRA
continent: South America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: geobr-ibge
polygon_feature_id: 'PB'
polygon_feature_year: 2020
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: BRA-1800-1903
    start_year: 1889
    end_year: 1903
    basis: Paraíba as a province of the Empire of Brazil until the Republic's provinces-to-states conversion, within the national row that runs to 1903
  - code: BRA-1903-1909
    start_year: 1903
    end_year: 1909
    basis: Paraíba as a state of the Republic, within the national row covering this narrow 1903-1909 era
  - code: BRA-1909-2025
    start_year: 1909
    end_year: 2025
    basis: Paraíba as a state of the Republic, within the current national row spanning 1909 to the present
---

# Paraíba

## Summary

Paraíba is a Brazilian state on the Atlantic coast of the Nordeste (Northeast) region, one of Brazil's original captaincies, with João Pessoa (formerly Parahyba) as its capital -- notable as the easternmost point of the Americas at Ponta do Seixas. This entry covers Paraíba from 1889, when the Proclamation of the Republic converted the former Imperial province into a state of the federation, to the present. `type: subnational` is used because Paraíba has never been a sovereign polity in its own right: it was a captaincy and then a province under Portuguese and Imperial Brazilian rule, and has been a first-order administrative division (state) of the Brazilian federation continuously since 1889, with no territorial or sovereignty break of the kind that would justify a predecessor row (unlike BRA-ACRE, which passed through Bolivian sovereignty and federal-territory status before statehood). Paraíba is not among the small set of listed BRA departures (Acre, Mato Grosso do Sul, Rondônia, Amapá, Roraima, Tocantins), so the country convention's default republic-founding start year of 1889 applies, with an open end_year of 2025 since Paraíba remains a current state.

**Why this entry exists.** The routing decision this page implements (unit_id BRA-PARAIBA) found no existing polity in the database representing Paraíba itself: the only BRA rows are three national totals (BRA-1800-1903, BRA-1903-1909, BRA-1909-2025), none of which is state-scale. Source rows describing Paraíba specifically -- a state-level Brazilian subnational dataset spanning 1900-2023 -- had previously nowhere correct to route except the national BRA-1909-2025 row, a container many times Paraíba's own territory, which would misattribute state-level agricultural/production data to the whole country. What confirms Paraíba is a distinct reporting unit rather than folded into national Brazil figures is the same practice documented for sibling entries: the source reports Paraíba as a named first-order administrative unit (a Brazilian state), consistent with IBGE's own state-level statistical reporting since the founding of the Republic. This entry is one of a batch of Brazilian state-level polities created under the same default start-year rule, with no departure listed for Paraíba in the country convention.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon available in the GeoPackage for this period. The correct source is `geobr-ibge` (Brazilian state boundaries, id_column `abbrev_state`), which is registered in `scripts/sources.yaml` specifically to carry Brazilian ADM1 units but whose file (`data/geodata/geobr-ibge/states.gpkg`) is not present locally, per the routing decision's own polygon_reasoning. `gadm-4.1-adm1` excludes Brazil entirely from its locally curated subset, and the only BRA source currently present, `cshapes-2.0`, digitises Brazil at whole-country scale only. Once `geobr-ibge` is fetched, this entry should match `abbrev_state='PB'`.

**Territory description:** modern Paraíba covers approximately 56,469 km2, one of the smaller Brazilian states, occupying a narrow coastal-to-sertão strip of the Nordeste roughly between Rio Grande do Norte to the north, Ceará to the west, and Pernambuco to the south. Its capital, João Pessoa, sits at the coast near Ponta do Seixas, the easternmost point of continental South America. Interior boundaries with Ceará and Pernambuco run through the semi-arid sertão and were subject to municipal-level adjustment into the 20th century, so the modern administrative boundary carries some vintage risk as a proxy across the full 1889-2025 span. No `polygon_area_km2` is recorded here since no geometry is yet attached.

## Predecessors and successors

No predecessor row is created by this decision: Paraíba's status as a first-order Brazilian administrative unit runs continuously back to 1889 with no interruption of the kind that separates BRA-ACRE from its federal-territory and Bolivian-sovereignty predecessors, so no separate pre-1889 provincial entry is proposed (the pre-1889 Imperial province is left to the national BRA-1800-1903 row, consistent with the default convention). This entry has no successor -- Paraíba remains a Brazilian state to the present, so the span runs to 2025 as still-current.

## Sourced claims

- The Proclamation of the Republic (15 November 1889) converted the Imperial provinces, including Paraíba -- one of Brazil's original captaincies/provinces dating to the earliest Portuguese colonial administration -- into states of the new federation, the event that fixes this entry's 1889 start under the country convention's default rule.
- IBGE (Brazil's national statistics institute) reports agricultural and demographic data at the state level for Paraíba continuously since the early Republic, the same reporting practice cited for sibling entries BRA-BAHIA and BRA-ALAGOAS as evidence the unit is a distinct, statistically tracked reporting territory rather than a component folded into national totals.

## Decisions

### d-code-iso3-subunit-start-end-pattern

**Code follows the dominant <ISO3>-<SUBUNIT>-<start>-<end> pattern**

Used BRA-PARAIBA-1889-2025 rather than a bespoke code, matching the pattern established for sibling Brazilian state entries (BRA-ALAGOAS, BRA-BAHIA, BRA-AMAZONAS). Paraíba is a first-order administrative division with no historical identity distinct from that administrative role: it was an Imperial province before 1889 and has been a Republic state continuously since, the same continuity pattern as Bahia and Alagoas rather than the discontinuous federal-territory history of Acre. This places it in the 57/66 dominant subnational pattern, not among the three bespoke historical-territory codes. SUBUNIT is the plain state name 'PARAIBA' (ASCII, no diacritic) rather than an IBGE abbreviation, for the same reason given on sibling entries: Brazilian states lack a universally recognized postal-style short code, so the full name is self-documenting and consistent with sibling pages.

### d-container-three-edges-tile-full-span

**Three container edges are needed, not one, because the national row itself changes across 1889-2025**

The routing decision's proposed container_code is BRA-1909-2025 alone, with its own span_basis text citing 1889 as the start year -- an internal inconsistency in the decision object, since BRA-1909-2025 only begins in 1909. Used alone it would leave 1889-1909 uncontained, which the containment gate rejects as falling outside the container's own span. The polity table shows three successive national BRA rows: BRA-1800-1903 (to 1903), BRA-1903-1909, and BRA-1909-2025. This entry's container list therefore has three edges, one per national era, tiling the full 1889-2025 span with no gap: 1889-1903 under BRA-1800-1903, 1903-1909 under BRA-1903-1909, and 1909-2025 under BRA-1909-2025 (the routing decision's own proposed container, used correctly only for its own portion of the span). This mirrors the identical fix already made on BRA-BAHIA and BRA-ALAGOAS.

## Open questions

### oq-geobr-ibge-not-fetched

**geobr-ibge is registered but its file has never been pulled to disk**

polygon_status is 'unassigned' because geobr-ibge is named in scripts/sources.yaml as the correct source for Brazilian state boundaries (id_column abbrev_state) but present_locally=False per the routing decision's polygon_detail -- the file data/geodata/geobr-ibge/states.gpkg does not exist locally, so no feature_id can be matched yet. This is the same blocking task recorded on the sibling BRA-BAHIA, BRA-ALAGOAS and BRA-ACRE entries. Once fetched, this entry should match abbrev_state='PB' and polygon_status should move to 'assigned', with the resulting measured area cross-checked against IBGE's own published figure for Paraíba (commonly cited near 56,469 km2, not independently verified against a specific IBGE table in this pass).

### oq-1889-vs-1903-provincial-boundary-continuity

**Was the province-to-state boundary literally unchanged in 1889, or is this an assumed continuity?**

This entry treats the 1889 Imperial province of Paraíba and the 1889-onward Republican state of Paraíba as territorially identical, the standard assumption for the provinces-to-states conversion but unchecked here against any 19th-century boundary source. Paraíba's western sertão boundary with Ceará, Pernambuco and Rio Grande do Norte was subject to municipal-level adjustments into the 20th century, similar to the risk already flagged for Bahia's interior frontiers, so this continuity assumption carries some risk. If a future source documents a specific boundary change, the geobr-ibge proxy (a present-day boundary) would need the same vintage-risk caveat already flagged on sibling entries.

### oq-source-row-count-and-span-not-in-decision-object

**The routing decision gives no exact row count for the source data this entry receives**

The routing decision implemented here states the data spans 1900-2023 and fits within the proposed 1889-2025 span, but gives no row count. The page-requirements spec asks for the input data's row count explicitly; that detail should be pulled from the underlying routing_verdicts.csv / assertion ledger and added here once available, rather than asserted from memory.
