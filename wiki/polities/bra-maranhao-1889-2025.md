---
polity_code: BRA-MARANHAO-1889-2025
polity_name: Maranhão
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
polygon_feature_id: 'MA'
polygon_feature_year: 2020
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: BRA-1800-1903
    start_year: 1889
    end_year: 1903
    basis: Maranhão as a province of the Empire of Brazil until the Republic's provinces-to-states conversion, within the national row that runs to 1903
  - code: BRA-1903-1909
    start_year: 1903
    end_year: 1909
    basis: Maranhão as a state of the Republic, within the national row covering this narrow 1903-1909 era
  - code: BRA-1909-2025
    start_year: 1909
    end_year: 2025
    basis: Maranhão as a state of the Republic, within the current national row spanning 1909 to the present
---

# Maranhão

## Summary

Maranhão is a Brazilian state occupying the northeastern coast where the Nordeste meets the Amazon, bordered by Pará to the west, Piauí to the east, Tocantins to the south, and the Atlantic to the north. This entry covers Maranhão from 1889, when the Proclamation of the Republic converted the former Imperial province of Maranhão into a state of the federation, to the present. `type: subnational` is used because Maranhão has never been a sovereign polity: it was a captaincy and then Imperial province under Portuguese and Brazilian rule, and has been a first-order administrative division of the Brazilian federation continuously since 1889. It is not among the six BRA units whose start year departs from the default rule (Acre, Mato Grosso do Sul, Rondônia, Amapá, Roraima, Tocantins) — those departed because of later territorial elevation, splits, or contested sovereignty; Maranhão was a direct province-to-state conversion with no such interruption, so the default 1889 start applies. The 2025 end reflects that Maranhão remains a current Brazilian state.

**Why this entry exists.** The routing decision (unit_id BRA-MARANHAO) found no existing BRA polity representing Maranhão specifically: the only BRA rows in the database are three national totals (BRA-1800-1903, BRA-1903-1909, BRA-1909-2025), none at state scale. Source data attributed to Maranhão was drawn from a Brazilian state-level panel (source key juan-subnational, per the routing decision's `sources` field) spanning roughly 1900-2023, entirely contained within the proposed 1889-2025 span with no unroutable years, consistent with sibling verdicts BRA-ALAGOAS, BRA-AMAZONAS, BRA-BAHIA, BRA-ES, BRA-GOIAS and others created in the same batch. Previously, any state-level row for Maranhão had nowhere correct to route except the national BRA-1909-2025 container — a unit roughly forty times Maranhão's own area — which would misattribute state-scale production/demographic figures to the whole country. What confirms Maranhão as a distinct reporting unit rather than a component folded into national totals is the same evidence cited for the sibling entries: IBGE and its predecessor statistical bodies have reported Maranhão as a named first-order administrative unit continuously since the Republic's founding, the standard practice for Brazilian state-level agricultural and demographic statistics.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon available in the GeoPackage for this period. The routing decision names `geobr-ibge` (Brazilian state boundaries, id_column `abbrev_state`) as the correct registered source — it is registered in `scripts/sources.yaml` specifically for Brazilian ADM1 units — but its file (`data/geodata/geobr-ibge/states.gpkg`) is not present locally, which is why `polygon_route` came back `registered_source_unfetched` rather than an assignable feature. `gadm-4.1-adm1`'s local copy excludes Brazil from its curated 81-country subset, and the only BRA source present locally, `cshapes-2.0`, digitises Brazil at whole-country scale only, with no state-level disaggregation to construct from. Once `geobr-ibge` is fetched, this entry should match `abbrev_state='MA'`.

**Territory description:** modern Maranhão covers approximately 331,900 km2, Brazil's eighth-largest state by area, occupying the northeastern coastal strip where the Amazon rainforest transitions into the semi-arid Nordeste. It is bordered by Pará to the west, Piauí to the east, Tocantins to the south, and the Atlantic Ocean along its northern coast, including the São Marcos and São José bays near its capital, São Luís (itself on an island). Unlike Alagoas, whose borders have been administratively stable since 1889, the routing decision explicitly flags that Maranhão's boundaries with Pará and Piauí were adjusted more than once through the early-to-mid 20th century, so a modern boundary proxy carries more vintage risk here than for the more stable Nordeste states in this batch. No `polygon_area_km2` is recorded here since no geometry is yet attached; the 331,900 km2 figure above is the modern state's commonly cited area, not a measurement of any geometry attached to this entry.

## Predecessors and successors

No predecessor row is created by this decision: Maranhão's status as a first-order Brazilian administrative unit runs continuously back to 1889 with no interruption of the kind that separates BRA-ACRE (Bolivian sovereignty, federal-territory status) from a direct province-to-state conversion. The pre-1889 Imperial province of Maranhão is left to the national BRA-1800-1903 row, consistent with the default convention applied across this batch. This entry has no successor — Maranhão remains a Brazilian state to the present, so the span runs to 2025 as still-current, matching the open end_year pattern used for every other still-existing BRA state entry in this batch.

## Sourced claims

- The Proclamation of the Republic (15 November 1889) converted the Imperial provinces, including Maranhão, into states of the new federation, the event that fixes this entry's 1889 start under the country convention's default rule.
- IBGE (Brazil's national statistics institute) and its predecessor bodies report agricultural and demographic data at the state level for Maranhão continuously since the early Republic, the same reporting practice cited for sibling entries BRA-ALAGOAS and BRA-BAHIA as evidence the unit is a distinct, statistically tracked reporting territory.
- Maranhão's borders with Pará and Piauí were adjusted more than once during the early-to-mid 20th century, per the routing decision's polygon_reasoning, meaning the modern administrative boundary is a less certain proxy for the earliest decades of this span than for Nordeste states with stable post-1889 borders.

## Decisions

### d-code-iso3-subunit-start-end-pattern

**Code follows the dominant ISO3-SUBUNIT-start-end pattern**

BRA-MARANHAO-1889-2025 follows the 57-of-66 dominant subnational pattern (<ISO3>-<SUBUNIT>-<start>-<end>), matching the sibling BRA state entries created in this same batch (BRA-ALAGOAS, BRA-BAHIA, BRA-AMAZONAS, BRA-CE, etc.). Maranhão is not a historical territory with a name distinct from its modern administrative identity in the way that would call for a bespoke code like ALK or HYD — it is simply the continuously-existing Brazilian state — so the bespoke-code pattern does not apply here. No existing BRA subnational codes precede this batch, so this batch itself sets the country's precedent, and internal consistency across the batch is the primary reason to follow the dominant pattern rather than inventing a one-off form for Maranhão specifically.

### d-three-container-edges-tile-span

**Three container edges tile the full 1889-2025 span with no gap**

The container list has three edges — BRA-1800-1903 (1889-1903), BRA-1903-1909 (1903-1909), and BRA-1909-2025 (1909-2025) — because the containing national chain itself changes rows at 1903 and 1909, and the containment gate rejects an edge whose interval falls outside either party's own span. A single edge citing only BRA-1909-2025 across 1889-2025 would leave 1889-1909 uncontained by that row, since Maranhão's state-level existence begins at the 1889 Proclamation of the Republic, twenty years before the national row's own 1909 start. This mirrors the sibling BRA-ALAGOAS/BRA-BAHIA entries created in the same batch.

## Open questions

### oq-geobr-ibge-not-fetched

**geobr-ibge is registered but not fetched, so the polygon is unassigned**

polygon_source is set to geobr-ibge (registered in scripts/sources.yaml for Brazilian state boundaries, id_column abbrev_state) per the routing decision's polygon_route of registered_source_unfetched, but the file data/geodata/geobr-ibge/states.gpkg does not exist locally, so polygon_status is unassigned and no polygon_feature_id can be set. Once fetched, this entry should match abbrev_state='MA'. Until then this page carries no geometry and no area figure.

### oq-boundary-vintage-para-piaui-disputes

**Modern IBGE boundary would be a vintage-risk proxy for the pre-1930s span**

The routing decision explicitly flags that Maranhão's borders with Pará and Piauí were adjusted multiple times after the 1889 state creation, through the early-to-mid 20th century. A fetched geobr-ibge feature reflects the present-day (post-2000s) boundary, so using it as a proxy for the full 1889-2025 span is an approximation whose error margin for the early-20th-century territory is currently unknown. This should be re-examined once the source is fetched and the historical boundary-change record for the Pará/Maranhão and Piauí/Maranhão frontiers can be checked against the modern shape.

### oq-juan-subnational-row-count-unspecified

**Source row count and exact source label for Maranhão not stated in the routing decision**

The routing decision references sibling verdicts (BRA-ALAGOAS, BRA-AMAZONAS, BRA-BAHIA) and a juan-subnational-style dataset but does not itself give Maranhão's specific row count, source label text, or exact year range within 1900-2023. This page states the data is entirely contained within the 1889-2025 span per the routing_reasoning field, but the underlying source table should be checked directly (the juan-subnational panel) to confirm the row count and years actually attributed to Maranhão before this entry is treated as fully verified against its source data.
