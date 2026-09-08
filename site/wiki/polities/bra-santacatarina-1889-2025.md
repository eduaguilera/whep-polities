---
polity_code: BRA-SANTACATARINA-1889-2025
polity_name: Santa Catarina
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
    basis: Imperial Brazil until the Proclamation of the Republic reorganized the former provinces into states; Santa Catarina existed as a province of the Empire throughout this segment.
  - code: BRA-1903-1909
    start_year: 1903
    end_year: 1909
    basis: Short-lived national-boundary era in the polity table between the 1903 and 1909 Brazilian territorial revisions; Santa Catarina's own boundary was unaffected by this national-level segmentation.
  - code: BRA-1909-2025
    start_year: 1909
    end_year: 2025
    basis: Modern Brazilian national boundary era, current to present; Santa Catarina remains a constituent state throughout.
---

# Santa Catarina

## Summary

Santa Catarina is a state of Brazil in the country's South Region, on the Atlantic coast between Paraná to the north and Rio Grande do Sul to the south, with Argentina along part of its western border. This entry is `type: subnational` because Santa Catarina has never been a sovereign state: it is a constituent unit of Brazil throughout, first as an Imperial captaincy/province (from the 18th/early 19th century, well before this entry's 1889 start) and then as a state of the Republic. The 1889 start_year marks the Proclamation of the Republic, which converted all Imperial provinces into states of the new federation -- the same default-case logic already applied to the other BRA subnational rows not among the six documented departure cases (Acre, Amapá, DF, Mato Grosso do Sul, Rondônia, Roraima), including its immediate neighbor Paraná (BRA-PARANA-1889-2025), which shares the identical rationale and container structure. The entry is created to receive statistical rows reported at the Santa Catarina-state level rather than the Brazil-national level, which the national BRA rows cannot correctly represent since they cover roughly 13-14x Santa Catarina's own territory.

**Why this entry exists.** Input data: statistical rows reported at the Santa Catarina-state level for Brazil, spanning 1900-2023 per the routing reasoning (exact row count not restated here beyond what the routing decision supplied). Previously matched to: the national BRA rows (BRA-1800-1903, BRA-1903-1909, BRA-1909-2025), which is wrong because those rows cover the whole of Brazil -- roughly 13-14x Santa Catarina's ~95,730 km² -- so any state-level series routed there is silently aggregated at national scale, both inflating national totals with a component already reported separately and losing the state-level resolution the source actually provides. Confirmation the entity is distinct: Santa Catarina is one of Brazil's 26 states plus the Federal District, an IBGE-recognized administrative and statistical reporting unit with its own state government since the 1889 Republic; it is not a Federico-Tena trading polity (that dataset does not carve up Brazil internally), but IBGE itself -- Brazil's national statistics agency -- publishes state-level series for Santa Catarina as a first-class reporting unit, which is the operative confirmation here, parallel to the geobr-ibge source already used for the other BRA-<SUBUNIT> rows, including the neighboring Paraná entry created in the same pass.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon feature is attached yet because the registered source, geobr-ibge (IBGE's Brazilian state boundaries, id_column=abbrev_state, value 'SC' for Santa Catarina), is registered in scripts/sources.yaml but not present locally -- data/geodata/geobr-ibge/states.gpkg does not exist on disk, so no feature can be selected or measured in this pass. `polygon_source` is set to the registered slug `geobr-ibge` itself (per the routing decision's `registered_source_unfetched` route) rather than `none`, since the correct source is known and only needs fetching; `polygon_status` is `unassigned` accordingly, and `polygon_feature_id` and `polygon_area_km2` are left blank rather than guessed. This mirrors the treatment already given to the sibling Paraná entry and the other 14 BRA-<SUBUNIT> rows using this same unfetched source.

**Territory a reader can locate today:** Santa Catarina occupies a coastal strip and interior plateau on Brazil's South Atlantic coast, bordered by Paraná to the north, Rio Grande do Sul to the south, and Argentina along part of its western edge. Its coastline runs roughly 500 km, including the state capital Florianópolis (on Ilha de Santa Catarina) and the port/industrial cities of Joinville, Blumenau, and Itajaí to the north, and Criciúma to the south. The present-day IBGE-mapped state covers approximately 95,730 km², making it one of Brazil's smaller states by area -- this figure is IBGE's official published territory statistic, not one measured from any polygon attached to this entry, since no polygon is attached yet. Once geobr-ibge is fetched this can be cross-checked against the actual feature's measured area.

Because the state's western boundary with Paraná shifted after the 1912-1916 Contestado War settlement (Santa Catarina ceding the disputed Contestado plateau), the present-day IBGE shape reflects a boundary settled by 1916-1920, not necessarily the boundary as it stood at the 1889 start of this entry's span; see the open question on Contestado boundary vintage below.

## Predecessors and successors

No predecessor or successor polity rows exist. Santa Catarina has no earlier polity entry: prior to 1889 it was a province of the Empire of Brazil (a captaincy since 1738, a province since 1738/1821), captured by the national BRA-1800-1903 row rather than any dedicated provincial entry, and no colonial-era captaincy polity for this territory has been created. It has no successor: Santa Catarina remains a current Brazilian state, so end_year is the open convention value 2025 and the row simply continues, exactly as for its sibling Paraná entry.

## Sourced claims

- Santa Catarina was elevated from captaincy to province of the Empire of Brazil in the early 19th century and was converted into a state of the newly proclaimed Republic on 15 November 1889, the event this entry's start_year encodes.
- Santa Catarina's western boundary with Paraná was contested from the 1853 provincial separation through the 1912-1916 Contestado War, a conflict over the timber- and yerba-mate-rich Contestado plateau that both provinces/states claimed; the 1916 settlement fixed the boundary largely as it stands in the present-day IBGE administrative map, which is why any polygon assigned to this entry from a modern source is a post-1916 proxy for the earlier years.

## Decisions

### d-code-pattern-santacatarina

**Followed the dominant BRA subnational code pattern**

Used ISO3-SUBUNIT-start-end (BRA-SANTACATARINA-1889-2025) rather than a bespoke code, since Santa Catarina is not a historical territory with an identity separate from its status as a Brazilian federative unit -- it is one of the original Imperial provinces converted to a state at the 1889 Proclamation of the Republic, the default case the routing decision describes (Santa Catarina is not among the 6 documented departure cases: Acre, Amapá, DF, Mato Grosso do Sul, Rondônia, Roraima). This matches the 16 existing BRA-<SUBUNIT> rows already in the table, including the immediately preceding Paraná entry (BRA-PARANA-1889-2025), which shares the identical 1889 start rationale and container structure.

### d-container-three-edges

**Split the container into three national-era edges instead of one, per the same fix already applied for Paraná**

The routing decision's proposed container_code was BRA-1909-2025 alone with proposed start_year 1889, which would leave 1889-1909 -- twenty years -- outside any container span; the containment gate rejects that gap. The polity table segments the national BRA chain as BRA-1800-1903, BRA-1903-1909, and BRA-1909-2025 for exactly this window, so three edges are used here, tiling 1889-2025 with no gap. Santa Catarina's own boundary was not documented as changing at either 1903 or 1909, so all three edges share the same practical territory; only the containing national polygon era differs. This is the identical remedy already applied to the sibling Paraná entry (BRA-PARANA-1889-2025), which cites the same three-edge tiling for the same reason.

## Open questions

### oq-geobr-ibge-not-fetched

**geobr-ibge is registered but not present locally, so no polygon feature ID exists yet**

polygon_status is unassigned because data/geodata/geobr-ibge/states.gpkg does not exist on disk (present_locally: False in scripts/sources.yaml), per the routing decision's registered_source_unfetched route. Once fetched, the feature for Santa Catarina should be selectable via id_column=abbrev_state, value 'SC'. Until then this entry has no polygon_feature_id and no measured area; polygon_area_km2 is left blank rather than guessed, matching the treatment already given to BRA-PARANA-1889-2025 and the other 14 BRA-<SUBUNIT> rows sharing this same unfetched source.

### oq-contestado-boundary-vintage

**geobr-ibge is a present-day boundary standing in for an 1889-2025 span, and the Contestado War changed exactly this state's western border**

Santa Catarina's western boundary with Paraná was disputed from the 1853 provincial separation onward and was only resolved by the 1916 settlement following the 1912-1916 Contestado War, in which Santa Catarina lost the contested Contestado region (the same territory whose award is recorded as an open question on the Paraná entry, BRA-PARANA-1889-2025#oq-boundary-vintage-1889). Whether the present-day IBGE polygon -- which reflects the post-1916 line -- is an adequate proxy for 1889-1916 Santa Catarina data, or whether the pre-settlement province was meaningfully larger, is unresolved here; no km² figure for the pre-cession province has been located. Flagged for whoever assigns the polygon once geobr-ibge is fetched.

### oq-data-span-vs-polity-span

**Confirm no rows before 1900 or after 2023 need a different container edge**

The routing reasoning states the data span is 1900-2023, entirely inside 1889-2025, so no back-cast segment was thought necessary. This has not been independently re-verified against the actual routed rows for BRA-SANTACATARINA in this pass -- if a later data refresh adds rows outside 1900-2023 (e.g., colonial-era captaincy records predating the 1889 Republic), the container tiling and start_year should be rechecked, since the 1889 start assumes the province-to-state transition is the correct origin and does not account for any pre-Republic captaincy-era territory (Santa Catarina was a captaincy/province since 1738) that might use a different name or boundary.
