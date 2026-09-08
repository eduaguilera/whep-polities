---
polity_code: BRA-RIOGRANDEDOSUL-1889-2025
polity_name: Rio Grande do Sul
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
    basis: Imperial Brazil until the Proclamation of the Republic reorganized the former provinces into states; Rio Grande do Sul existed as a province of the Empire throughout this segment.
  - code: BRA-1903-1909
    start_year: 1903
    end_year: 1909
    basis: Short-lived national-boundary era in the polity table between the 1903 and 1909 Brazilian territorial revisions (Acre annexation); Rio Grande do Sul's own boundary in the far south was unaffected.
  - code: BRA-1909-2025
    start_year: 1909
    end_year: 2025
    basis: Modern Brazilian national boundary era, current to present; Rio Grande do Sul remains a constituent state throughout.
---

# Rio Grande do Sul

## Summary

Rio Grande do Sul is Brazil's southernmost state, bordering Uruguay and Argentina, and is one of the original Imperial provinces converted into a state of the federation at the 1889 Proclamation of the Republic. This entry is `type: subnational` because Rio Grande do Sul has never itself been a sovereign state within this span: it is a constituent unit of Brazil throughout, first as an Imperial province (since colonial times) and then as a state of the Republic from 1889. The 1889 start_year applies the same default-case logic already used for the other BRA subnational rows (Paraná, Rio de Janeiro, Bahia, Alagoas, and others): the province was converted to a state at the Proclamation and had no later administrative-status change (no split-off, no territory-to-statehood elevation) that would justify a later start_year. The entry is created to receive statistical rows reported at the Rio-Grande-do-Sul-state level rather than the Brazil-national level, since the national BRA rows are roughly twelve times the state's territory and cannot correctly represent state-scale series.

**Why this entry exists.** Input data: statistical rows reported at the Rio Grande do Sul state level for Brazil, per the routing decision's BRA-RIOGRANDEDOSUL unit, with data starting in 1900 (entirely within the proposed 1889-2025 span, so no back-cast segment is needed). Previously matched to: the national BRA rows (BRA-1800-1903, BRA-1903-1909, BRA-1909-2025), which is wrong because those rows cover the whole of Brazil -- roughly an order of magnitude larger than Rio Grande do Sul's ~281,730 km² -- so any state-level series routed there is silently aggregated at national scale, both inflating national totals with a component already reported separately and losing the state-level resolution the source actually provides. Confirmation the entity is distinct: Rio Grande do Sul is one of Brazil's 26 states plus the Federal District, an IBGE-recognized administrative and statistical reporting unit with its own state government since the 1889 Republic (and an Imperial province before that, since the late colonial period); it is not a Federico-Tena trading polity (that dataset does not carve up Brazil internally), but IBGE itself publishes state-level series for Rio Grande do Sul as a first-class reporting unit, which is the operative confirmation here, parallel to the geobr-ibge source already used for the other BRA-<SUBUNIT> rows such as Rio de Janeiro and Paraná.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon feature is attached yet because the registered source, geobr-ibge (IBGE's Brazilian state boundaries, id_column=abbrev_state, value 'RS' for Rio Grande do Sul), is registered in scripts/sources.yaml but not present locally -- data/geodata/geobr-ibge/states.gpkg does not exist on disk, so no feature can be selected or measured in this pass. `polygon_source` is set to the registered slug `geobr-ibge` itself (per the routing decision's `registered_source_unfetched` route) rather than `none`, since the correct source is known and only needs fetching; `polygon_status` is `unassigned` accordingly, and `polygon_feature_id` and `polygon_area_km2` are left blank rather than guessed.

**Territory a reader can locate today:** Rio Grande do Sul is Brazil's southernmost state, in the South Region, bordering Santa Catarina to the north, Argentina (Misiones and Corrientes provinces) to the west, and Uruguay to the south, with an Atlantic coastline to the east including the Lagoa dos Patos lagoon. Its capital is Porto Alegre. The present-day IBGE-mapped state covers approximately 281,730 km², one of Brazil's larger southern states -- this figure is IBGE's official published territory statistic, not one measured from any polygon attached to this entry, since no polygon is attached yet. Once geobr-ibge is fetched this can be cross-checked against the actual feature's measured area. No mid-span territorial changes to the state's own boundary are documented for 1889-2025 (unlike, e.g., Rio de Janeiro's 1960-1975 Guanabara split), so a single continuous polygon proxy across the full span is expected to be valid once fetched, subject to the open question below about pre-1889 border disputes potentially leaving a residual 19th-century vintage mismatch.

## Predecessors and successors

No predecessor or successor polity rows exist. Rio Grande do Sul has no earlier polity entry: prior to 1889 it was a province of the Empire of Brazil (and, briefly during 1836-1845, the breakaway Rio-Grandense Republic during the Farroupilha Revolution, never internationally recognized and reincorporated at war's end), captured by the national BRA-1800-1903 row rather than any dedicated provincial or rebel-state entry. It has no successor: Rio Grande do Sul remains a current Brazilian state, so end_year is the open convention value 2025 and the row simply continues.

## Sourced claims

- Rio Grande do Sul province of the Empire of Brazil was converted into a state of the newly proclaimed Republic on 15 November 1889, the event this entry's start_year encodes.
- The Farroupilha Revolution (1835-1845) saw the province briefly declare itself the independent Rio-Grandense Republic before being militarily reincorporated into the Empire of Brazil; this predates and does not affect this entry's 1889-2025 span.

## Decisions

### d-code-pattern-riograndedosul

**Followed the dominant BRA subnational code pattern**

Used ISO3-SUBUNIT-start-end (BRA-RIOGRANDEDOSUL-1889-2025) rather than a bespoke code, since Rio Grande do Sul is one of the original Imperial provinces converted to a state at the 1889 Proclamation of the Republic -- exactly the routing decision's default case -- and is not among the documented departure cases (Acre, Amapá, DF, Mato Grosso do Sul, and others with later administrative starts from splits or elevations). This matches the existing BRA-<SUBUNIT> rows (BRA-PARANA-1889-2025, BRA-RIODEJANEIRO-1889-2025, BRA-BAHIA-1889-2025, etc.), all sharing the 1889 start convention. The subunit token RIOGRANDEDOSUL (no hyphens/spaces/accents) follows the same flattening convention visible in the existing codes.

### d-container-three-edges

**Split the container into three national-era edges instead of one**

The routing decision's proposed container_code was BRA-1909-2025 alone, but Rio Grande do Sul's proposed start_year is 1889, and the polity table shows the national BRA chain segmented into BRA-1800-1903, BRA-1903-1909, and BRA-1909-2025 for this window. A single container edge of 1909-2025 would leave 1889-1909 (twenty years, including the entire First Republic founding period and the 1903 Acre annexation) outside any container span, which the containment gate rejects. Three edges, one per national era, tile 1889-2025 with no gap; Rio Grande do Sul's own state boundary in Brazil's far south was not affected by the 1903 Acre acquisition in the country's far north, so all three edges share the same practical state territory -- only the containing national polygon era differs. This mirrors the identical fix already applied on BRA-PARANA-1889-2025 and BRA-RIODEJANEIRO-1889-2025.

## Open questions

### oq-geobr-ibge-not-fetched

**geobr-ibge is registered but not present locally, so no polygon feature ID exists yet**

polygon_status is unassigned because data/geodata/geobr-ibge/states.gpkg does not exist on disk (present_locally: False in scripts/sources.yaml), per the routing decision, which found gadm-4.1-adm1's local subset excludes Brazil entirely and cshapes-2.0 (already used for the national BRA rows) carries no subnational Brazilian boundaries. Once geobr-ibge is fetched, the feature for Rio Grande do Sul should be selectable via id_column=abbrev_state, value 'RS'. Until then this entry has no polygon_feature_id and no measured area; polygon_area_km2 is left blank rather than guessed.

### oq-farroupilha-and-border-disputes

**Does the modern geobr-ibge shape correctly represent Rio Grande do Sul across the full 1889-2025 span, given the province's history of border wars and the Farroupilha secession?**

Rio Grande do Sul's southern and western borders with Uruguay and Argentina were shaped by a long sequence of colonial and imperial-era conflicts (the Guaranitic War, the Cisplatine War that split off Uruguay, the Ragamuffin War/Farroupilha Revolution of 1835-1845 during which the province briefly declared itself the independent Rio-Grandense Republic before being reincorporated). All of that predates this entry's 1889 start_year, so it should not affect the polygon proxy, but no check has been done to confirm the state's international boundary was fully settled and unchanged for the entire 1889-2025 span -- a residual border adjustment with Argentina or Santa Catarina in this period, if any, has not been ruled out. This should be checked once the geobr-ibge feature is fetched and its vintage compared against 19th-century boundary sources.
