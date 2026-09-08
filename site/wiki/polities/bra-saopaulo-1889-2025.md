---
polity_code: BRA-SAOPAULO-1889-2025
polity_name: São Paulo
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
polygon_feature_id: null
polygon_feature_year: null
polygon_status: unassigned
predecessor: []
successor: []
container:
  - code: BRA-1800-1903
    start_year: 1889
    end_year: 1903
    basis: Imperial Brazil until the Proclamation of the Republic reorganized the former provinces into states; São Paulo existed as a province of the Empire throughout this segment.
  - code: BRA-1903-1909
    start_year: 1903
    end_year: 1909
    basis: Short-lived national-boundary era in the polity table between the 1903 and 1909 Brazilian territorial revisions; São Paulo's own boundary was unaffected.
  - code: BRA-1909-2025
    start_year: 1909
    end_year: 2025
    basis: Modern Brazilian national boundary era, current to present; São Paulo remains a constituent state throughout.
---

# São Paulo

## Summary

São Paulo is a state of Brazil in the country's Southeast Region, bordered by Minas Gerais to the north and northeast, Rio de Janeiro to the east, Paraná to the south, and Mato Grosso do Sul to the west, with an Atlantic coastline including the port of Santos. This entry is `type: subnational` because São Paulo has never been a sovereign state: it is a constituent unit of Brazil throughout, first as an Imperial province and then as a state of the Republic. The 1889 start_year marks the Proclamation of the Republic, which converted all Imperial provinces into states of the new federation -- the same default-case logic already applied to the other BRA subnational rows (Paraná, Bahia, Alagoas, Amazonas, Ceará, Espírito Santo, Goiás, Maranhão, and others), none of which had an administrative status change later than 1889 that would justify a later start. The entry is created to receive statistical rows reported at the São Paulo-state level rather than the Brazil-national level, which the national BRA rows cannot correctly represent since they are roughly 34x São Paulo's territory (8,472,100 km² national vs. ~248,200 km² for the state).

**Why this entry exists.** Input data: statistical rows reported at the São Paulo-state level for Brazil, spanning 1900-2023 per the routing reasoning (exact row count not restated here beyond what the routing decision supplied). Previously matched to: the national BRA rows (BRA-1800-1903, BRA-1903-1909, BRA-1909-2025), which is wrong because those rows cover the whole of Brazil -- roughly 34x São Paulo's territory -- so any state-level series routed there is silently aggregated at national scale, both inflating national totals with a component already reported separately and losing the state-level resolution the source actually provides. Confirmation the entity is distinct: São Paulo is one of Brazil's 26 states plus the Federal District, each an IBGE-recognized administrative and statistical reporting unit with its own state government since the 1889 Republic; IBGE, Brazil's national statistics agency, publishes state-level series for São Paulo as a first-class reporting unit, parallel to the geobr-ibge source already used for the other BRA-<SUBUNIT> rows.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon feature is attached yet because the registered source, geobr-ibge (IBGE's Brazilian state boundaries, id_column=abbrev_state, value 'SP' for São Paulo), is registered in scripts/sources.yaml but not present locally -- data/geodata/geobr-ibge/states.gpkg does not exist on disk, so no feature can be selected or measured in this pass. `polygon_source` is set to the registered slug `geobr-ibge` itself (per the routing decision's `registered_source_unfetched` route) rather than `none`, since the correct source is known and only needs fetching; `polygon_status` is `unassigned` accordingly, and `polygon_feature_id` and `polygon_area_km2` are left blank rather than guessed.

**Territory a reader can locate today:** São Paulo state occupies Brazil's southeast, running from its Atlantic coastline at Santos and the port complex around it, inland roughly 600 km to its borders with Minas Gerais, Paraná, and Mato Grosso do Sul. Its capital, the city of São Paulo, is the largest metropolitan area in South America. The present-day IBGE-mapped state covers approximately 248,200 km², Brazil's 12th-largest state by area -- this figure is IBGE's official published territory statistic, not one measured from any polygon attached to this entry, since no polygon is attached yet. Once geobr-ibge is fetched this can be cross-checked against the actual feature's measured area. No dramatic territorial change is documented for São Paulo since 1889, unlike states carved out later (Mato Grosso do Sul from Mato Grosso in 1977, for instance), so a present-day proxy is expected to be reasonably close, though the precise boundary history across 1889-2025 has not been independently verified here (see open questions).

## Predecessors and successors

No predecessor or successor polity rows exist. São Paulo has no earlier polity entry: prior to 1889 it was a province of the Empire of Brazil, captured by the national BRA-1800-1903 row rather than any dedicated provincial entry, and no colonial-era (captaincy) polity for this territory has been created. It has no successor: São Paulo remains a current Brazilian state, so end_year is the open convention value 2025 and the row simply continues.

## Sourced claims

- São Paulo became a province of the Empire of Brazil in 1821 (as São Paulo captaincy/province) and was converted into a state of the newly proclaimed Republic on 15 November 1889, the event this entry's start_year encodes.
- São Paulo is Brazil's most populous state and its economic center, home to the city of São Paulo, and its modern IBGE-administered territory covers approximately 248,200 km², the state's officially published area figure -- not a figure measured from any polygon attached to this entry, since none is attached yet.

## Decisions

### d-code-pattern-saopaulo

**Followed the dominant BRA subnational code pattern**

Used ISO3-SUBUNIT-start-end (BRA-SAOPAULO-1889-2025) rather than a bespoke code, since São Paulo is not a historical territory with an identity separate from its status as a Brazilian federative unit -- it is one of the original Imperial provinces converted to a state at the 1889 Proclamation of the Republic, the default case the routing decision describes. This matches the 15 existing BRA-<SUBUNIT> rows (BRA-PARANA-1889-2025, BRA-BAHIA-1889-2025, BRA-ALAGOAS-1889-2025, etc.), all sharing the same 1889 start convention for provinces not among the documented departure cases (Acre, Amapá, DF, Mato Grosso do Sul, Rondônia, Roraima).

### d-container-three-edges-saopaulo

**Split the container into three national-era edges instead of one**

The routing decision's proposed container_code was BRA-1909-2025 alone, but São Paulo's proposed start_year is 1889. The polity table segments the national BRA chain into BRA-1800-1903, BRA-1903-1909, and BRA-1909-2025 for exactly this window. A single container edge of 1909-2025 would leave 1889-1909 -- twenty years, including the entire First Republic founding period -- outside any container span, which the containment gate rejects. Three edges, one per national era, tile 1889-2025 with no gap; São Paulo's own province/state boundary is not documented as having moved at either transition, so all three edges share the same practical territory, only the containing national polygon era differs. This mirrors the identical fix already made on BRA-PARANA-1889-2025.

## Open questions

### oq-geobr-ibge-not-fetched-saopaulo

**geobr-ibge is registered but not present locally, so no polygon feature ID exists yet**

polygon_status is unassigned because data/geodata/geobr-ibge/states.gpkg does not exist on disk (present_locally: False in scripts/sources.yaml), per the routing decision. Once fetched, the feature for São Paulo should be selectable via id_column=abbrev_state, value 'SP'. Until then this entry has no polygon_feature_id and no measured area; polygon_area_km2 is left blank rather than guessed. This is the same open item recorded on every other BRA-<SUBUNIT> row awaiting the same fetch.

### oq-boundary-vintage-1889-saopaulo

**geobr-ibge is a present-day boundary standing in for an 1889-2025 span**

São Paulo's borders were not entirely static across this span: the state's northern boundary with Minas Gerais and its western boundary toward Mato Grosso/Paraná were subject to early-20th-century adjustments (including disputes resolved by federal arbitration), and the loss of territory that became parts of neighboring states during the First Republic period is not fully documented here. Whether the modern IBGE polygon is close enough to treat as a proxy for the full 1889-2025 span, or whether pre-1900 São Paulo differed meaningfully in extent, is unresolved -- no km² figure for the earlier boundary has been located yet. Flagged for whoever assigns the polygon once geobr-ibge is fetched.

### oq-data-span-vs-polity-span-saopaulo

**Confirm no rows before 1900 or after 2023 need a different container edge**

The routing reasoning states the data span is 1900-2023, entirely inside 1889-2025, so no back-cast segment was thought necessary. This has not been independently re-verified against the actual routed rows for BRA-SAOPAULO in this pass -- if a later data refresh adds rows outside 1900-2023 (e.g., colonial-era captaincy records, or the Constitutionalist Revolution period of 1932 which briefly disrupted state administration but not its territory), the container tiling and start_year should be rechecked.
