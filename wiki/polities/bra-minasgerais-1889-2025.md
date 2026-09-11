---
polity_code: BRA-MINASGERAIS-1889-2025
polity_name: Minas Gerais
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
polygon_feature_id: 'MG'
polygon_feature_year: 2020
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: BRA-1800-1903
    start_year: 1889
    end_year: 1903
    basis: Minas Gerais as a province of the Empire of Brazil until the Republic's provinces-to-states conversion, within the national row that runs to 1903
  - code: BRA-1903-1909
    start_year: 1903
    end_year: 1909
    basis: Minas Gerais as a state of the Republic, within the national row covering this narrow 1903-1909 era
  - code: BRA-1909-2025
    start_year: 1909
    end_year: 2025
    basis: Minas Gerais as a state of the Republic, within the current national row spanning 1909 to the present
---

# Minas Gerais

## Summary

Minas Gerais is Brazil's second-most-populous state, an entirely landlocked territory in the southeastern highlands that was the historical center of Brazil's 18th-century gold and diamond rushes, with its capital Belo Horizonte (planned and founded in 1897 to replace the old colonial capital Ouro Preto). This entry covers Minas Gerais from 1889, when the Proclamation of the Republic converted the former Imperial province into a state of the federation, to the present. `type: subnational` is used because Minas Gerais has never been a sovereign polity in its own right: it was a captaincy and then a province under Portuguese and Imperial Brazilian rule, and has been a first-order administrative division (state) of the Brazilian federation continuously since 1889, with no territorial or sovereignty break of the kind that would justify a predecessor row (unlike BRA-ACRE, which passed through Bolivian sovereignty and federal-territory status before statehood, or BRA-MS, split from Mato Grosso only in 1977). Minas Gerais is not among the small set of listed BRA departures (Acre, Mato Grosso do Sul, Rondonia, Amapa, Roraima, Tocantins), so the country convention's default republic-founding start year of 1889 applies, with an open end_year of 2025 since the state remains current.

**Why this entry exists.** The routing decision this page implements (unit_id BRA-MINASGERAIS) found no existing polity in the database representing Minas Gerais itself: the only BRA rows are three national totals (BRA-1800-1903, BRA-1903-1909, BRA-1909-2025), none of which is state-scale. Source rows describing Minas Gerais specifically -- a state-level Brazilian subnational dataset, per the routing_reasoning spanning 1900-2023, following the same pattern as the sibling BRA-ALAGOAS and BRA-BAHIA verdicts -- had previously nowhere correct to route except the national BRA-1909-2025 row, a container many times Minas Gerais's own territory, which would misattribute state-level agricultural/production data to the whole country. What confirms Minas Gerais is a distinct reporting unit rather than folded into national Brazil figures is the same practice documented for the sibling entries: the source reports Minas Gerais as a named first-order administrative unit (a Brazilian state), consistent with IBGE's own state-level statistical reporting since the founding of the Republic. This entry is one of a batch of Brazilian state-level polities created under the same default start-year rule, with no departure listed for Minas Gerais in the country convention (unlike BRA-ACRE, BRA-MS, or the other departure states). The routing decision itself gives no exact row count for the underlying source data (see open question below), only the general 1900-2023 data span and the sibling-verdict pattern it follows.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon available in the GeoPackage for this period. The correct source is `geobr-ibge` (Brazilian state boundaries, id_column `abbrev_state`), which is registered in `scripts/sources.yaml` specifically to carry Brazilian ADM1 units but whose file (`data/geodata/geobr-ibge/states.gpkg`) is not present locally, per the routing decision's own polygon_reasoning. `gadm-4.1-adm1` is nominally present_locally=True but its local subset excludes Brazil entirely (0 features for BRA), and the only BRA source currently present, `cshapes-2.0`, digitises Brazil at whole-country scale only. Once `geobr-ibge` is fetched, this entry should match `abbrev_state='MG'`.

**Territory description:** modern Minas Gerais covers approximately 586,500 km2, the fourth-largest Brazilian state by area -- comparable in size to France -- occupying the mineral-rich highlands and plateaus of the country's southeast. It is entirely landlocked, bordering Bahia and Espirito Santo to the north/east, Rio de Janeiro and Sao Paulo to the south, Mato Grosso do Sul and Goias to the west, and a narrow contact with the Federal District at its western Triangulo Mineiro salient. Its capital, Belo Horizonte, was purpose-built starting in 1894-97 to replace Ouro Preto, seat of the 18th-century gold rush and the colonial captaincy administration. No `polygon_area_km2` is recorded here since no geometry is yet attached; the ~586,500 km2 figure is the commonly cited modern administrative area, not a measurement of any geometry attached to this entry.

## Predecessors and successors

No predecessor row is created by this decision: Minas Gerais's status as a first-order Brazilian administrative unit runs continuously back to 1889, when the Imperial province (established 1720) was converted into a Republic state, with no interruption of the kind that separates BRA-ACRE from its federal-territory and Bolivian-sovereignty predecessors -- so no separate pre-1889 provincial entry is proposed, and the pre-1889 Imperial province is left to the national BRA-1800-1903 row, consistent with the default convention. This entry has no successor: Minas Gerais remains a Brazilian state to the present, so the span runs to 2025 as still-current, matching the routing decision's proposed end_year and the treatment of sibling entries BRA-BAHIA and BRA-ALAGOAS.

## Sourced claims

- The Proclamation of the Republic (15 November 1889) converted the Imperial provinces, including Minas Gerais -- created as a captaincy/province in 1720 out of the gold-mining interior of the earlier Captaincy of Sao Paulo e Minas do Ouro -- into states of the new federation, the event that fixes this entry's 1889 start under the country convention's default rule.
- IBGE (Brazil's national statistics institute) reports agricultural and demographic data at the state level for Minas Gerais continuously since the early Republic, the same reporting practice cited for sibling entries BRA-BAHIA and BRA-ALAGOAS as evidence the unit is a distinct, statistically tracked reporting territory rather than a component folded into national totals.

## Decisions

### d-code-iso3-subunit-start-end-pattern

**Code follows the dominant <ISO3>-<SUBUNIT>-<start>-<end> pattern**

Used BRA-MINASGERAIS-1889-2025 rather than a bespoke code, matching the pattern already established for sibling Brazilian state entries (BRA-ALAGOAS, BRA-BAHIA, BRA-AMAZONAS, BRA-ACRE) created under the same batch of routing verdicts. Minas Gerais is a first-order administrative division (a Brazilian state) with no historical identity as a polity distinct from that administrative role: it was an Imperial province before 1889 (created 1720 from the Captaincy of Sao Paulo e Minas do Ouro) and has been a Republic state continuously since, with none of the discontinuous federal-territory-then-state history that would justify a bespoke code (as with Acre) or a predecessor row. That places it in the 57/66 dominant subnational pattern rather than the three bespoke historical-territory codes. SUBUNIT is the plain state name 'MINASGERAIS' (no space, following the sibling convention) rather than an IBGE abbreviation, since Brazilian states lack a universally recognized postal-style short code the way US states do; the full name is self-documenting and consistent with sibling pages.

### d-container-three-edges-tile-full-span

**Three container edges are needed, not one, because the national row itself changes across 1889-2025**

The routing decision's proposed container_code is BRA-1909-2025 alone (and its own span_basis text cites 1889 as the start, an internal inconsistency in the decision object, exactly as flagged on the BRA-BAHIA and BRA-ALAGOAS entries), but BRA-1909-2025 only begins in 1909 -- leaving 1889-1909 uncontained if a single edge were used, which the containment gate would reject as falling outside the container's own span. The polity table shows three successive national BRA rows: BRA-1800-1903 (to 1903), BRA-1903-1909, and BRA-1909-2025. This entry's container list therefore has three edges, one per national era, together tiling the full 1889-2025 span with no gap: 1889-1903 under BRA-1800-1903, 1903-1909 under BRA-1903-1909, and 1909-2025 under BRA-1909-2025 (the routing decision's own proposed container, correctly used only for its own portion of the span). This mirrors the identical fix already made on BRA-BAHIA and BRA-ALAGOAS.

## Open questions

### oq-geobr-ibge-not-fetched

**geobr-ibge is registered but its file has never been pulled to disk**

polygon_status is 'unassigned' because geobr-ibge is named in scripts/sources.yaml as the correct source for Brazilian state boundaries (id_column abbrev_state) but present_locally=False per the routing decision's polygon_detail -- the file data/geodata/geobr-ibge/states.gpkg does not exist locally, so no feature_id can be matched yet. gadm-4.1-adm1 is nominally registered as present_locally=True overall but its local subset excludes Brazil entirely (0 features for BRA), so it cannot execute this route despite the surface-level flag. This is the same blocking task recorded on the sibling BRA-BAHIA, BRA-ALAGOAS and BRA-ACRE entries. Once fetched, this entry should match abbrev_state='MG' and polygon_status should move to 'assigned', with the resulting measured area cross-checked against IBGE's own published figure for Minas Gerais (commonly cited near 586,500 km2, not independently verified against a specific IBGE table in this pass).

### oq-triangulo-mineiro-boundary-history

**Was the modern Minas Gerais boundary, including the Triangulo Mineiro, stable across the whole 1889-2025 span?**

Minas Gerais's western salient, the Triangulo Mineiro (bordering Goias/Mato Grosso and cut off from the rest of the state by the Rio Grande), was the subject of 19th-century jurisdictional disputes before being confirmed as Minas territory, and the state's borders with Goias, Bahia, Espirito Santo and Rio de Janeiro saw municipal-level adjustments into the early 20th century. This entry assumes, without independent verification, that the province-to-state conversion in 1889 carried the same territory the modern geobr-ibge boundary will show. If a future source documents a specific 19th- or early-20th-century boundary change (e.g. disputes with Goias over the Triangulo, or the transfer of areas near the Rio de Janeiro border), the geobr-ibge proxy -- a present-day boundary -- would need the same vintage-risk caveat already flagged on BRA-BAHIA and BRA-ACRE.

### oq-source-row-count-and-span-not-in-decision-object

**The routing decision gives no row count or exact year range for the source data this entry receives**

The routing decision implemented here (unit_id BRA-MINASGERAIS) gives only the qualitative description that Minas Gerais 'is a Brazilian state with no sibling departure listed' and that data is 'back_cast/matched... depending on method', without stating how many rows or which exact years of Minas Gerais data are being routed to this new polity, beyond a general span of 1900-2023 mentioned in the routing_reasoning. The page-requirements spec asks for the input data's row count and year range explicitly; that detail should be pulled from the underlying routing_verdicts.csv / assertion ledger and added here once available, rather than asserted from memory.
