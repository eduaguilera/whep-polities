---
polity_code: BRA-RONDONIA-1943-2025
polity_name: Rondônia
start_year: 1943
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
    start_year: 1943
    end_year: 2025
    basis: Rondônia (as the Federal Territory of Guaporé, renamed Rondônia in 1956, then a state from 1982) has been a first-order division of Brazil continuously since its creation in 1943, carved from Mato Grosso and Amazonas territory.
---

# Rondônia

## Summary

Rondônia is a state in Brazil's Amazonian northwest, carved out in 1943 as the Federal Territory of Guaporé from parts of Mato Grosso and Amazonas, renamed Rondônia in 1956 (after telegraph-line pioneer Cândido Rondon), and elevated to full statehood in 1982. This entry is `type: subnational` because Rondônia has never been sovereign — it has always been a first-order administrative division of Brazil, first as a federally-administered territory (1943-1982) and then as a constituent state (1982-present) — and it is created as a distinct polity row because the reporting territory itself, not sovereignty, is what a matcher needs: before 1943 no Rondônia-equivalent unit existed to report statistics against, so any source data naming "Rondônia" necessarily refers to years from 1943 onward. The span starts at territory creation (1943) rather than at statehood (1982) because the administrative boundary and identity are continuous across that transition — the same treatment already given to the accepted sibling entry BRA-AMAPA-1943-2025, another 1943-created federal territory that later became a state.

**Why this entry exists.** Input data: Brazilian state-level production/trade series (Mitchell-style historical compilations) naming Rondônia (or its predecessor name, Território Federal do Guaporé) as a distinct reporting unit, spanning candidate data years 1943-2025 out of a routing pass that examined 124 candidate years for this unit, of which 43 (35%) had been marked unroutable prior to this polity's creation. Previously, absent a Rondônia polity row, those data years had nowhere valid to route to: they could not go to `BRA-MATOGROSSO` or `BRA-AMAZONAS` (the source labels them as Rondônia specifically, a different reporting territory) and could not go to the bare national `BRA` row either, since that discards the sub-national detail the source actually provides. That left them `unroutable`, which is reserved for years nothing could ever carry — not for years before the modern classification existed but the underlying territory (as a federal territory) already did. What confirms this is a genuinely distinct entity rather than a fabricated one: Brazil's own 1943 decree-law creating the Federal Territory of Guaporé, its 1956 renaming to Rondônia, and its 1982 elevation to statehood are all matters of settled administrative record (via IBGE and Brazilian federal law), and the same three-stage creation-then-statehood pattern is already accepted in this database for the sibling entry BRA-AMAPA-1943-2025.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon has been fetched into this pipeline for this period; `polygon_status: unassigned`. The routing decision names `geobr-ibge` (IBGE's official Brazilian state-boundary GeoPackage, id_column `abbrev_state`, value `RO`) as the registered source that should resolve this — it is listed in `scripts/sources.yaml` but the corresponding file is not present under `data/geodata/geobr-ibge/`. A global release of `gadm-4.1-adm1` (which does include Rondônia as feature BRA.23_1) is a viable fallback, but the copy of GADM 4.1 currently vendored in this repository is a curated subset that excludes Brazil entirely, so neither source can be cited as resolved today. No area figure is attached to this page.

**Why this entry exists:** it captures Brazilian sub-national production/trade data years for Rondônia — the routing decision covers the 1943-2025 span sourced from Mitchell-style historical compilations reporting Brazilian states individually. That data was previously at risk of being left `unroutable` (43 of 124 candidate data years, 35%, were marked unroutable in an earlier pass) simply because no Rondônia polity row existed to receive it, even though the source clearly tabulates a "Rondônia" (or "Território Federal do Guaporé") reporting unit from 1943 onward. The Brazilian federal government's own creation of the territory in 1943, and its consistent appearance as a named administrative unit in national statistics and gazetteers from that date, confirms this is a genuinely distinct reporting entity, not a re-filed subset of Mato Grosso.

**Territory description:** modern Rondônia state, in Brazil's northwest bordering Bolivia, comprising roughly the middle Madeira and Guaporé/Mamoré river basins; its capital is Porto Velho. The current state covers approximately 237,590 km2 (IBGE's official 2022 figure) — this is cited as external reference for locating the territory, not as a measurement of any polygon attached to this page, since no polygon is attached yet. The original 1943 territorial carve-out from Mato Grosso and Amazonas is believed to closely match this modern extent, but that has not been verified against a primary boundary-history source (see open questions).

## Predecessors and successors

No predecessor entity: before 1943 no distinct Rondônia-equivalent administrative unit existed, so this polity has no predecessor code — the area's pre-1943 history belongs, if anywhere, to Mato Grosso's and Amazonas's own polity rows (see the open question on pre-1943 row disposition). No successor either: the Federal Territory of Guaporé (1943), renamed Rondônia in 1956, was elevated directly to statehood in 1982 without further territorial reorganization, and the state of Rondônia continues to the present day, so start_year=1943 and end_year=2025 cover the entity's entire continuous existence in one row.

## Sourced claims

- Mitchell's International Historical Statistics and comparable compilations report Brazilian production/trade data by state; Rondônia does not appear as a distinct reporting unit before 1943, consistent with it having no separate administrative existence until the Federal Territory of Guaporé was created that year.
- IBGE (Instituto Brasileiro de Geografia e Estatística), Brazil's official statistics and cartography agency, is the authoritative source for the state's administrative boundary and history; its geobr-ibge dataset (abbrev_state='RO') is the natural polygon source for this unit but has not yet been fetched into this pipeline's data/geodata directory.
- The country convention's departure-list note documents the Federal Territory of Guaporé's creation in 1943, its 1956 renaming to Rondônia, and its 1982 elevation to statehood — the same three-stage lineage already applied to the accepted sibling entry BRA-AMAPA-1943-2025.

## Decisions

### d-code-follows-bra-amapa-pattern

**Span starts at territory creation (1943), not statehood (1982), following the BRA-AMAPA precedent**

Rondônia was created in 1943 as the Federal Territory of Guaporé (renamed Rondônia in 1956) and only became a state in 1982. The routing decision explicitly matches this to the accepted sibling pattern for BRA-AMAPA, another federal territory created in 1943 and elevated to statehood in 1988, whose polity span likewise starts at territory creation rather than statehood. Using 1943 rather than 1982 keeps the entity continuous across the territory-to-state transition, since the administrative boundary and name lineage (Guaporé -> Rondônia) did not break at statehood, only the constitutional status changed. Code follows the dominant <ISO3>-<SUBUNIT>-<start>-<end> pattern used for 338 of 351 subnational rows, consistent with sibling BRA codes like BRA-ACRE-1962-2025 and BRA-AMAPA-1943-2025.

### d-polygon-route-unfetched-not-none

**polygon_source is the registered geobr-ibge slug, not a placeholder, because the route is registered_source_unfetched**

The routing decision's polygon_route is registered_source_unfetched: geobr-ibge is a real, registered source in scripts/sources.yaml (id_column=abbrev_state, would resolve abbrev_state='RO') that is simply not present on disk yet. Per the harness rules, when the route is registered_source_unfetched the slug IS the source and polygon_status is unassigned, in contrast to new_source_needed/none_available where polygon_source must be 'none'. gadm-4.1-adm1 is a registered fallback candidate globally (BRA.23_1) but its local curated file excludes Brazil, so it cannot be cited as the resolved source here; it is left as an open question instead.

### d-pre1943-not-included

**Pre-1943 years are out of scope for this entry by design**

No distinct Rondônia-equivalent administrative unit existed before 1943; the area was reported as part of Mato Grosso (and Amazonas). This page therefore only covers 1943-2025. Whether pre-1943 source rows for this area should be routed to BRA-MATOGROSSO/BRA-AMAZONAS as back-cast data, rather than left unroutable, is a separate question raised in the routing_concerns and recorded below as an open question.

## Open questions

### oq-geobr-ibge-not-fetched

**geobr-ibge polygon has not actually been fetched or licence-checked**

polygon_status is unassigned because the geobr-ibge Brazilian states GeoPackage (data/geodata/geobr-ibge/states.gpkg) is registered in scripts/sources.yaml but not present on disk for this pipeline run. Someone needs to fetch it (or fetch GADM 4.1 admin-1 globally, which does include BRA.23_1 Rondônia, as a fallback since the locally curated GADM subset excludes Brazil) and confirm the licence is compatible with this project's open-data mandate before polygon_status can move to assigned. Until then no area estimate is attached to this page at all.

### oq-pre1943-guapore-boundary-vintage

**Does the modern Rondônia state boundary match the original 1943 Federal Territory of Guaporé carve-out?**

geobr-ibge/GADM would supply Rondônia's current (post-1982, arguably post-2025) state boundary. Using that for the 1943-1982 Federal Territory of Guaporé/Rondônia span is an approximation: minor boundary adjustments between the original 1943 carve-out from Mato Grosso/Amazonas and the present state limits are plausible but unverified here. This should be checked against a primary Brazilian administrative-history source (e.g. IBGE historical boundary records) before the polygon is assigned as anything stronger than a proxy for the earliest years.

### oq-pre1943-rows-disposition

**Should pre-1943 source rows for this area be reallocated to Mato Grosso/Amazonas rather than left unroutable?**

The routing_concerns flagged that if the source's pre-1943 Rondônia-area values were originally filed under Mato Grosso and merely reallocated via GIS/dasymetric methods (a high fallback_interpolated/scaled share), a back_cast disposition to Mato Grosso's or Amazonas's own polity rows may be more correct than marking those data-years unroutable. This requires checking whether Mato Grosso's/Amazonas's recorded 1900-1942 data already includes or double-counts this area — not resolved by this page, which only creates the 1943-2025 entity.

### oq-exact-creation-date

**Exact 1943 creation date and administrative continuity through 1956 rename not verified against a primary source**

The 1943 federal-territory creation year and the 1956 Guaporé-to-Rondônia rename are taken from the country convention's departure note, not cross-checked against a primary Brazilian legal/administrative source (e.g. the creating decree-law). If the primary source gives a different year or shows a genuine administrative break at the 1956 rename, this page's start_year and predecessor/successor chain would need revision.
