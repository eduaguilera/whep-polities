---
polity_code: BRA-AMAZONAS-1889-2025
polity_name: Amazonas
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
  - code: BRA-1909-2025
    start_year: 1909
    end_year: 2025
    basis: Amazonas has been a state of the Brazilian federation continuously since the 1889 Proclamation of the Republic; the container row BRA-1909-2025 spans this entry's full 1889-2025 range at its own start (1909), so a single edge tiles the whole span with no gap.
---

# Amazonas

## Summary

Amazonas is the largest state of Brazil by area, occupying most of the western Brazilian Amazon basin, capital Manaus. It was one of the original provinces converted into a state of the federation at the 1889 Proclamation of the Republic, and unlike Acre, Rondônia, Mato Grosso do Sul, Amapá, Roraima or Tocantins it was not later carved out of, or split off from, another unit -- it has held state status without interruption since 1889. `type: subnational` reflects that Amazonas is an administrative division of a sovereign country (Brazil), not an independent state; sovereignty over the territory has always sat with Brazil (empire, then republic), and this row exists only to carry the state-level reporting territory that Brazilian statistical sources (e.g. IBGE-derived series) tabulate separately from national totals.

**Why this entry exists.** This entry is created under the general country-level routing pass for Brazilian subnational units (BRA-ALAGOAS, BRA-BAHIA, BRA-CEARA, BRA-ESPIRITO-SANTO, BRA-GOIAS, BRA-MARANHAO, BRA-MATO-GROSSO, etc.), all resolved the same way: a genuine Brazilian state identifier ('Amazonas') with no name match among the existing polities table and no boundary-features candidate already registered for it, so create_new was chosen over match_existing. Before this pass, any Amazonas-labelled rows in ingested data would have fallen through to the national row BRA-1909-2025 (or its 1800-1903/1903-1909 predecessors), which is roughly 9-10x the area of the state itself and mixes Amazonas's figures into all-Brazil totals. Federico-Tena-style state-level trade/administrative treatments and Brazilian federal census/IBGE practice both confirm Amazonas has been tabulated as a distinct first-level administrative unit since 1889, which is the historical-source basis for giving it its own row rather than leaving it folded into the national series.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is attached in the GeoPackage for this period. The routing decision names `geobr-ibge` (Brazilian state boundaries sourced from IBGE, keyed on `abbrev_state`) as the correct registered source -- it is registered in sources.yaml and specifically covers Brazilian states -- but it is not yet fetched locally (`present_locally=False`), so no `polygon_feature_id` can be assigned from what's on disk today. `gadm-4.1-adm1` is also registered and present locally but its local copy is a curated subset that carries zero Brazil features, so it cannot supply a feature either. `polygon_source: geobr-ibge` records the intended registered source per the routing decision; `polygon_status: unassigned` reflects that the source is not yet fetched, not that no source exists.

**Territory description:** Amazonas is Brazil's largest state (roughly 1,559,000 km2, larger than Mongolia), located in the northwestern Amazon basin, bordered by Colombia, Peru and Venezuela to the west/north and by the Brazilian states of Roraima, Pará, Mato Grosso, Rondônia and Acre. Its capital and dominant population center is Manaus, at the confluence of the Rio Negro and the Amazon (Solimões) river. The 1,559,159 km2 figure above is a reader-oriented estimate of the modern state's area from public reference figures (e.g. IBGE), not a measurement of any polygon attached to this entry -- no polygon is attached yet. Amazonas's external state boundaries have been essentially stable since 1889; it was not among the six units (Acre, Mato Grosso do Sul, Rondônia, Amapá, Roraima, Tocantins) later carved out of neighboring territory, so once `geobr-ibge` is fetched, current IBGE boundaries should be a reasonable proxy back to 1889, modulo the open question below about internal municipal/administrative reorganizations that don't affect the state's outer boundary.

## Predecessors and successors

No predecessor: Amazonas province existed before 1889 (as Provincia do Amazonas, split from Grão-Pará in 1850), but this entry's span begins at the 1889 Proclamation of the Republic per the country-wide default start rule for BRA subnational units, and no pre-1889 provincial entry is being created in this pass. No successor: the state is still current as of 2025, so `end_year` is the open convention value and `successor` is empty.

## Sourced claims

- IBGE (Instituto Brasileiro de Geografia e Estatística) tabulates Amazonas as one of Brazil's 26 states plus the Federal District, with continuous state-level statistical reporting (population, production, area) distinct from national Brazil totals.
- Amazonas was not one of the six BRA subnational units flagged as later territorial departures from the 1889 baseline (Acre 1962, Mato Grosso do Sul 1979, Rondônia 1943/1981, Amapá 1943, Roraima 1943, Tocantins 1989) -- it retained its 1889 provincial boundary as its state boundary without a documented split-off.

## Decisions

### d-code-follows-dominant-pattern

**Used <ISO3>-<SUBUNIT>-<start>-<end> per the dominant subnational pattern**

Chose BRA-AMAZONAS-1889-2025 rather than a bespoke code because Amazonas is a standard first-level administrative division (a Brazilian state) with no independent historical identity of its own comparable to Alaska Territory, Hyderabad or Ryukyu -- it has been a constituent state of Brazil under one name throughout its span. This matches 57 of 66 existing subnational rows in the table, including the pattern already used for sibling BRA states in this same routing pass (e.g. BRA-ALAGOAS, BRA-ACRE, BRA-AMAPA already present as untracked wiki files in this branch).

### d-polygon-source-unfetched-not-none

**Declared geobr-ibge as unfetched source rather than none**

The routing decision's polygon_route is registered_source_unfetched with polygon_source geobr-ibge. Per the harness rules, when the route is registered_source_unfetched the slug IS the source and polygon_status must be unassigned, not none -- so geobr-ibge is recorded as the polygon_source here even though no local feature file currently backs it, rather than falling back to polygon_source: none, which is reserved for new_source_needed/none_available routes.

## Open questions

### oq-geobr-ibge-fetch-and-vintage

**geobr-ibge needs to be fetched, and its vintage risk for pre-2000 years is unconfirmed**

geobr-ibge is registered but not present locally; once fetched, the Amazonas feature (keyed by abbrev_state = 'AM' or similar) needs to be identified and assigned to polygon_feature_id, and polygon_status should move from unassigned to assigned or proxy. Separately, geobr-ibge boundaries reflect the present-day IBGE administrative layer: while Amazonas has not undergone an external boundary split since 1889, internal municipal boundary changes and any minor 20th-century adjustments along the Peru/Colombia/Venezuela frontier (several Brazilian border treaties were signed in the early-to-mid 20th century) have not been checked against this entry's full 1889-2025 span. Using a modern boundary for the full span should be flagged as an approximation until that stability is independently confirmed, similar to the vintage caveat already noted for other geobr-ibge-routed BRA states in this pass.

### oq-no-input-data-rows-cited

**No specific ingested data rows for Amazonas were named in the routing decision**

Unlike some create_new verdicts that cite a specific count of rows and source labels that were previously mismatched, the routing decision for BRA-AMAZONAS gives only the general reasoning (no name match, no boundary-features candidate) without naming which dataset(s) or how many rows currently carry an 'Amazonas' label that this entry is meant to capture. Before this page is treated as fully grounded, it would help to confirm from the ingest ledger which specific source(s) and row counts motivated creating this row now, rather than as part of the general Brazilian-states sweep, and whether those rows were previously silently absorbed into BRA-1909-2025 totals.
