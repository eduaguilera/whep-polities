---
polity_code: BRA-PARANA-1889-2025
polity_name: Paraná
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
polygon_feature_id: 'PR'
polygon_feature_year: 2020
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: BRA-1800-1903
    start_year: 1889
    end_year: 1903
    basis: Imperial Brazil until the Proclamation of the Republic reorganized the former provinces into states; Paraná existed as a province of the Empire throughout this segment.
  - code: BRA-1903-1909
    start_year: 1903
    end_year: 1909
    basis: Short-lived national-boundary era in the polity table between the 1903 and 1909 Brazilian territorial revisions; Paraná's own boundary was unaffected.
  - code: BRA-1909-2025
    start_year: 1909
    end_year: 2025
    basis: Modern Brazilian national boundary era, current to present; Paraná remains a constituent state throughout.
---

# Paraná

## Summary

Paraná is a state of Brazil in the country's South Region, on the southern plateau between São Paulo to the north, Santa Catarina to the south, Mato Grosso do Sul and Paraguay to the west, and Argentina to the southwest along the Iguaçu/Paraná rivers. This entry is `type: subnational` because Paraná has never been a sovereign state: it is a constituent unit of Brazil throughout, first as an Imperial province (from 1853, well before this entry's 1889 start) and then as a state of the Republic. The 1889 start_year marks the Proclamation of the Republic, which converted all Imperial provinces into states of the new federation -- the same default-case logic already applied to the other 14 non-departure-case BRA subnational rows (Alagoas, Amazonas, Bahia, Ceará, Espírito Santo, Goiás, Maranhão, Mato Grosso, Minas Gerais, Pará, Paraíba, and others), none of which had an administrative status change later than 1889 that would justify a later start. The entry is created to receive statistical rows reported at the Paraná-state level rather than the Brazil-national level, which the national BRA rows cannot correctly represent since they are roughly 15-20x Paraná's territory.

**Why this entry exists.** Input data: statistical rows reported at the Paraná-state level for Brazil, spanning 1900-2023 per the routing reasoning (exact row count not restated here beyond what the routing decision supplied). Previously matched to: the national BRA rows (BRA-1800-1903, BRA-1903-1909, BRA-1909-2025), which is wrong because those rows cover the whole of Brazil -- roughly 15-20x Paraná's ~199,300 km² -- so any state-level series routed there is silently aggregated at national scale, both inflating national totals with a component that was already reported separately and losing the state-level resolution the source actually provides. Confirmation the entity is distinct: Paraná is one of Brazil's 26 states plus the Federal District, each an IBGE-recognized administrative and statistical reporting unit with its own state government since the 1889 Republic; it is not a Federico-Tena trading polity (that dataset does not carve up Brazil internally), but IBGE itself -- Brazil's national statistics agency -- publishes state-level series for Paraná as a first-class reporting unit, which is the operative confirmation here, parallel to the geobr-ibge source already used for the other 14 BRA-<SUBUNIT> rows.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon feature is attached yet because the registered source, geobr-ibge (IBGE's Brazilian state boundaries, id_column=abbrev_state, value 'PR' for Paraná), is registered in scripts/sources.yaml but not present locally -- data/geodata/geobr-ibge/states.gpkg does not exist on disk, so no feature can be selected or measured in this pass. `polygon_source` is set to the registered slug `geobr-ibge` itself (per the routing decision's `registered_source_unfetched` route) rather than `none`, since the correct source is known and only needs fetching; `polygon_status` is `unassigned` accordingly, and `polygon_feature_id` and `polygon_area_km2` are left blank rather than guessed.

**Territory a reader can locate today:** Paraná is bordered by the Atlantic Ocean at its small southeastern coastline (around the ports of Paranaguá and Antonina), and its inland extent runs roughly 600 km west to the Paraná and Iguaçu river borders with Paraguay and Argentina, including the Brazilian side of the Iguaçu Falls and the Itaipu Dam reservoir on the Paraná River. Its capital is Curitiba. The present-day IBGE-mapped state covers approximately 199,300 km², Brazil's 15th-largest state by area -- this figure is IBGE's official published territory statistic, not one measured from any polygon attached to this entry, since no polygon is attached yet. Once geobr-ibge is fetched this can be cross-checked against the actual feature's measured area.

Because the western boundary shifted after the 1912-1916 Contestado War settlement with Santa Catarina, the present-day IBGE shape is a boundary as it has stood since roughly 1916-1920, not necessarily since 1889; see the open question on boundary vintage above.

## Predecessors and successors

No predecessor or successor polity rows exist. Paraná has no earlier polity entry: prior to 1889 it was a province of the Empire of Brazil, captured by the national BRA-1800-1903 row rather than any dedicated provincial entry, and no colonial-era (captaincy) polity for this territory has been created. It has no successor: Paraná remains a current Brazilian state, so end_year is the open convention value 2025 and the row simply continues.

## Sourced claims

- Paraná became a province of the Empire of Brazil in 1853, separated from São Paulo province; it was converted into a state of the newly proclaimed Republic on 15 November 1889, the event this entry's start_year encodes.
- Paraná's western boundary with Santa Catarina was set by a 1916 agreement following the Contestado War (1912-1916), a border dispute over the timber- and yerba-mate-rich Contestado region that both states had claimed since the 1853 separation; the modern IBGE administrative boundary reflects this post-1916 line, not the boundary claimed by Paraná before the settlement.

## Decisions

### d-code-pattern-parana

**Followed the dominant BRA subnational code pattern**

Used ISO3-SUBUNIT-start-end (BRA-PARANA-1889-2025) rather than a bespoke code, since Paraná is not a historical territory with an identity separate from its status as a Brazilian federative unit -- it is one of the original Imperial provinces converted to a state at the 1889 Proclamation of the Republic, exactly the case the routing decision describes as the default. This matches the other 15 existing BRA-<SUBUNIT> rows (BRA-ACRE-1962-2025, BRA-ALAGOAS-1889-2025, BRA-BAHIA-1889-2025, etc.), all of which share the same 1889 start convention for provinces not among the six documented departure cases (Acre, Amapá, DF, Mato Grosso do Sul, and two others with later administrative starts).

### d-container-three-edges

**Split the container into three national-era edges instead of one**

The routing decision's proposed container_code was BRA-1909-2025 alone, but Paraná's proposed start_year is 1889, and the polity table shows the national BRA chain segmented into BRA-1800-1903, BRA-1903-1909, and BRA-1909-2025 for exactly this window (rows 100-103 in data/final/polities_database.csv). A single container edge of 1909-2025 would leave 1889-1909 -- twenty years, including the entire First Republic founding period -- outside any container span, which the containment gate rejects. Three edges, one per national era, tile 1889-2025 with no gap; Paraná's own province/state boundary is not documented as having moved at either 1903 or 1909, so all three edges share the same practical territory, only the containing national polygon era differs.

## Open questions

### oq-geobr-ibge-not-fetched

**geobr-ibge is registered but not present locally, so no polygon feature ID exists yet**

polygon_status is unassigned because data/geodata/geobr-ibge/states.gpkg does not exist on disk (present_locally: False in scripts/sources.yaml), per the routing decision. Once fetched, the feature for Paraná should be selectable via id_column=abbrev_state, value 'PR'. Until then this entry has no polygon_feature_id and no measured area; polygon_area_km2 is left blank rather than guessed.

### oq-boundary-vintage-1889

**geobr-ibge is a present-day boundary standing in for an 1889-2025 span**

Paraná's western boundary was not stable across this whole span: the state ceded territory in the Contestado region to Santa Catarina following the 1916 Argentina-Brazil arbitration outcome and the subsequent 1912-1916 Contestado War settlement, and the modern IBGE polygon reflects the post-settlement, present-day boundary. Whether this is close enough to treat as a proxy for 1889-1916 (pre-cession) data, or whether pre-1916 Paraná was meaningfully larger, is not resolved here -- no km² figure for the pre-cession province has been located yet. Flagged for whoever assigns the polygon once geobr-ibge is fetched.

### oq-data-span-vs-polity-span

**Confirm no rows before 1900 or after 2023 need a different container edge**

The routing reasoning states the data span is 1900-2023, entirely inside 1889-2025, so no back-cast segment was thought necessary. This has not been independently re-verified against the actual routed rows for BRA-PARANA in this pass -- if a later data refresh adds rows outside 1900-2023 (e.g., colonial-era captaincy records), the container tiling and start_year should be rechecked, since the 1889 start assumes the province/state transition is the correct origin and does not account for any pre-Republic captaincy-era territory that might use a different name or boundary.
