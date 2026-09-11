---
polity_code: BRA-RIODEJANEIRO-1889-2025
polity_name: Rio de Janeiro
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
polygon_feature_id: 'RJ'
polygon_feature_year: 2020
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: BRA-1800-1903
    start_year: 1889
    end_year: 1903
    basis: Imperial Brazil until the Proclamation of the Republic reorganized the former provinces into states; Rio de Janeiro existed as a province of the Empire throughout this segment.
  - code: BRA-1903-1909
    start_year: 1903
    end_year: 1909
    basis: Short-lived national-boundary era in the polity table between the 1903 and 1909 Brazilian territorial revisions; Rio de Janeiro state's own boundary was unaffected.
  - code: BRA-1909-2025
    start_year: 1909
    end_year: 2025
    basis: Modern Brazilian national boundary era, current to present; Rio de Janeiro remains a constituent state throughout.
---

# Rio de Janeiro

## Summary

Rio de Janeiro is a state of Brazil in the country's Southeast Region, on the Atlantic coast between Espírito Santo to the northeast, Minas Gerais to the north and west, and São Paulo to the southwest. This entry is `type: subnational` because Rio de Janeiro has never itself been a sovereign state: it is a constituent unit of Brazil throughout, first as an Imperial province and then as a state of the Republic. The 1889 start_year marks the Proclamation of the Republic, which converted all Imperial provinces into states of the new federation -- the same default-case logic already applied to the other BRA subnational rows (Paraná, Alagoas, Bahia, Ceará, Espírito Santo, and others), none of which had an administrative status change later than 1889 that would justify a later start. This entry does not attempt to separately model the former Federal District / city of Rio de Janeiro (the national capital until 1960, later the state of Guanabara until its 1975 merger back into Rio de Janeiro state) -- that territory was administratively distinct from the surrounding state for nearly a century of this span, which is flagged as an open question below rather than resolved by splitting the entry. The entry is created to receive statistical rows reported at the Rio-de-Janeiro-state level rather than the Brazil-national level, which the national BRA rows cannot correctly represent since they are a large multiple of the state's territory.

**Why this entry exists.** Input data: statistical rows reported at the Rio de Janeiro state level for Brazil, spanning 1900-2023 per the routing decision (BRA-RIODEJANEIRO unit, exact row count not restated here beyond what the routing decision supplied). Previously matched to: the national BRA rows (BRA-1800-1903, BRA-1903-1909, BRA-1909-2025), which is wrong because those rows cover the whole of Brazil -- roughly an order of magnitude larger than Rio de Janeiro state's ~43,750 km² -- so any state-level series routed there is silently aggregated at national scale, both inflating national totals with a component already reported separately and losing the state-level resolution the source actually provides. Confirmation the entity is distinct: Rio de Janeiro is one of Brazil's 26 states plus the Federal District, an IBGE-recognized administrative and statistical reporting unit with its own state government since the 1889 Republic (and, before that, an Imperial province since colonial times); it is not a Federico-Tena trading polity (that dataset does not carve up Brazil internally), but IBGE itself publishes state-level series for Rio de Janeiro as a first-class reporting unit, which is the operative confirmation here, parallel to the geobr-ibge source already used for the other BRA-<SUBUNIT> rows.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon feature is attached yet because the registered source, geobr-ibge (IBGE's Brazilian state boundaries, id_column=abbrev_state, value 'RJ' for Rio de Janeiro), is registered in scripts/sources.yaml but not present locally -- data/geodata/geobr-ibge/states.gpkg does not exist on disk, so no feature can be selected or measured in this pass. `polygon_source` is set to the registered slug `geobr-ibge` itself (per the routing decision's `registered_source_unfetched` route) rather than `none`, since the correct source is known and only needs fetching; `polygon_status` is `unassigned` accordingly, and `polygon_feature_id` and `polygon_area_km2` are left blank rather than guessed.

**Territory a reader can locate today:** Rio de Janeiro state occupies the coast of southeastern Brazil, surrounding but administratively separate from the city and metropolitan area of Rio de Janeiro; it stretches from the Serra do Mar mountains and Paraíba do Sul valley in the interior to Atlantic beach resort towns such as Búzios and Angra dos Reis. Its capital is the city of Rio de Janeiro (also the state capital since the 1975 fusion; before that Niterói was capital while the city of Rio was the separate Federal District/Guanabara). The present-day IBGE-mapped state covers approximately 43,750 km², one of Brazil's smaller states by area -- this figure is IBGE's official published territory statistic, not one measured from any polygon attached to this entry, since no polygon is attached yet. Once geobr-ibge is fetched this can be cross-checked against the actual feature's measured area.

The modern state boundary reflects the 1975 fusion of the state of Guanabara (the former Federal District, i.e. the city of Rio de Janeiro, made a state in its own right when the capital moved to Brasília in 1960) back into the surrounding state of Rio de Janeiro. For 1960-1975 the 'state of Rio de Janeiro' as an administrative unit therefore excluded the city itself, and any statistical series from that window that reports 'Rio de Janeiro' state-level figures needs to be checked against whether it means the pre-1975 rump state or the post-1975 merged state; see the open question below.

## Predecessors and successors

No predecessor or successor polity rows exist. Rio de Janeiro has no earlier polity entry: prior to 1889 it was a province of the Empire of Brazil, captured by the national BRA-1800-1903 row rather than any dedicated provincial entry, and no colonial-era (captaincy) polity for this territory has been created. It has no successor: Rio de Janeiro remains a current Brazilian state, so end_year is the open convention value 2025 and the row simply continues.

## Sourced claims

- Rio de Janeiro province of the Empire of Brazil was converted into a state of the newly proclaimed Republic on 15 November 1889, the event this entry's start_year encodes.
- The Federal District (the city of Rio de Janeiro) was separated from the surrounding province/state from the Empire's founding until 1960, when the national capital moved to Brasília and the former Federal District became the state of Guanabara; Guanabara was merged back into the state of Rio de Janeiro in 1975, restoring the current single-state configuration.

## Decisions

### d-code-pattern-riodejaneiro

**Followed the dominant BRA subnational code pattern**

Used ISO3-SUBUNIT-start-end (BRA-RIODEJANEIRO-1889-2025) rather than a bespoke code, since Rio de Janeiro state is not a historical territory with an identity separate from its status as a Brazilian federative unit -- it is one of the original Imperial provinces converted to a state at the 1889 Proclamation of the Republic, exactly the case the routing decision describes as the default. This matches the existing BRA-<SUBUNIT> rows (BRA-PARANA-1889-2025, BRA-ALAGOAS-1889-2025, BRA-BAHIA-1889-2025, etc.), all of which share the same 1889 start convention for provinces not among the documented departure cases (Acre, Amapá, DF, and others with later administrative starts). The subunit token RIODEJANEIRO (no hyphen/spaces) follows the same flattening convention visible in the existing codes.

### d-container-three-edges

**Split the container into three national-era edges instead of one**

The routing decision's proposed container_code was BRA-1909-2025 alone, but Rio de Janeiro's proposed start_year is 1889, and the polity table shows the national BRA chain segmented into BRA-1800-1903, BRA-1903-1909, and BRA-1909-2025 for exactly this window. A single container edge of 1909-2025 would leave 1889-1909 -- twenty years, including the entire First Republic founding period -- outside any container span, which the containment gate rejects. Three edges, one per national era, tile 1889-2025 with no gap; Rio de Janeiro's own province/state boundary is not documented as having moved at either 1903 or 1909, so all three edges share the same practical territory, only the containing national polygon era differs. This mirrors the identical fix already applied on BRA-PARANA-1889-2025.

### d-no-guanabara-merge

**Did not attempt to model the 1960-1975 Guanabara split within this entry**

Rather than creating a separate Guanabara polity row for 1960-1975 or trying to encode a mid-span territorial change inside this entry's single polygon assignment, this entry simply spans 1889-2025 continuously as 'Rio de Janeiro state' and flags the Guanabara period as an open question. A dedicated Guanabara/Federal-District row is out of scope for this pass since the routing decision only proposed one new BRA-RIODEJANEIRO polity and no input data was flagged as specifically Guanabara-era; if such data surfaces later it would need its own subnational entry rather than being folded here.

## Open questions

### oq-geobr-ibge-not-fetched

**geobr-ibge is registered but not present locally, so no polygon feature ID exists yet**

polygon_status is unassigned because data/geodata/geobr-ibge/states.gpkg does not exist on disk (present_locally: False in scripts/sources.yaml), per the routing decision. Once fetched, the feature for Rio de Janeiro should be selectable via id_column=abbrev_state, value 'RJ'. Until then this entry has no polygon_feature_id and no measured area; polygon_area_km2 is left blank rather than guessed.

### oq-guanabara-1960-1975-boundary

**Does the modern geobr-ibge shape, or any routed data series, actually cover 1960-1975 correctly?**

For 1960-1975 the city of Rio de Janeiro was the separate state of Guanabara, not part of the state of Rio de Janeiro; the modern IBGE polygon (post-1975 merged shape) will be a poor proxy for 'Rio de Janeiro state' data reported during that fifteen-year window, since it includes territory (the city) that was administratively excluded at the time. Any data rows from 1960-1975 labelled 'Rio de Janeiro' need to be checked for whether they mean the rump state or already include Guanabara before being trusted against a geobr-ibge-derived area figure. This also raises whether a distinct BRA-GUANABARA polity should exist for that window if such data is found.
