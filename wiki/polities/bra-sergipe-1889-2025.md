---
polity_code: BRA-SERGIPE-1889-2025
polity_name: Sergipe
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
predecessor: [BRA-1889-1909]
successor: []
container:
  - code: BRA-1909-2025
    start_year: 1889
    end_year: 2025
    basis: Sergipe has been a constituent state of Brazil continuously since the 1889 Proclamation of the Republic converted the imperial province directly into a state; the container row BRA-1909-2025 is the national chain covering this whole span, and no intervening national-chain break (1903, 1909) changed Sergipe's status as a state.
---

# Sergipe

## Summary

Sergipe is the smallest state of Brazil by area, on the Atlantic coast of the Northeast region, wedged between Bahia to its south/west and Alagoas to its north. It was an imperial province under the Empire of Brazil and was converted directly into a state of the federation at the 1889 Proclamation of the Republic, along with the other existing provinces — it is not one of the 6 exceptions the routing decision refers to (states later carved out of federal territories, such as Rondônia in 1943 or Roraima in 1988). Its capital, Aracaju, was already the provincial capital from 1855 (moved there from São Cristóvão for port access), and remains the state capital today. `type: subnational` is used because Sergipe is a first-order administrative division of a sovereign state (Brazil), never itself sovereign, and this entry exists to carry state-level statistics that are finer-grained than the national BRA row and should not be matched to it.

**Why this entry exists.** This entry captures Brazilian state-level data for Sergipe (iso3 BRA, admin unit "Sergipe" / postal code SE) spanning 1900-2023 in the source rows that motivated this routing decision (the agent-harness routing pass, `pipelines/agent-harness/state/routing_verdicts.csv`). Before this page existed, rows keyed to the admin unit "Sergipe" had no dedicated polity and would otherwise have been matched to the national polity rows BRA-1800-1903/1903-1909/1909-2025, which are national totals for the whole of Brazil (currently ~8.5 million km², vs. Sergipe's ~22,000 km²) and would badly overstate the territory the Sergipe-labelled figures actually describe. No existing polity in the table represents the state of Sergipe itself. Historically, Sergipe's distinctness as a reporting/administrative unit is uncontroversial and long-standing: it was already a separate captaincy and then province under the Portuguese and Imperial administrations (split from Bahia in the colonial period), was one of the original signatory provinces at Brazilian independence and again at the 1889 Republic, and IBGE (Brazil's national statistics institute) has published state-level series for Sergipe under this same boundary continuously since the Republic's founding — it is a standard reporting geography in every Brazilian census and agricultural survey, not a synthetic construct for this database.

## Territorial extent

**Polygon:** `polygon_status: unassigned`, `polygon_source: geobr-ibge`. The route decided for this unit was `registered_source_unfetched`: `geobr-ibge` is already registered in `sources.yaml` (id_column `abbrev_state`, target file `data/geodata/geobr-ibge/states.gpkg`), and that layer is IBGE's own state-boundary product, which is the correct source for a Brazilian state — but the file is not present locally in this session, so no feature id can be asserted here. `gadm-4.1-adm1` is registered and present but is a curated 81-country subset that excludes Brazil, so it cannot serve as today's route despite being fetched. Once `geobr-ibge/states.gpkg` is fetched, the feature with `abbrev_state == "SE"` should be assigned; vintage risk is low because Sergipe's external boundary (unlike carved-out states such as Rondônia or Amapá) has not changed since 1889 — no territory has been added to or removed from it to form a newer state.

**Territory description:** Sergipe occupies the Atlantic coastal strip of Brazil's Northeast region between the São Francisco river (its northern border with Alagoas) and the border with Bahia to the south and west. Its capital and largest city is Aracaju, on the coast at the mouth of the Sergipe river. It is the smallest of Brazil's 26 states by area, at approximately **21,910 km²** (current IBGE figure) — a reader can locate it on a modern map as the small coastal state directly northeast of Bahia's Salvador metropolitan region and southeast of Alagoas's Maceió. This figure is the state's own officially surveyed area, not a measurement of any polygon attached to this entry, since no polygon is attached yet.

## Predecessors and successors

Predecessor: the imperial Province of Sergipe, which this table represents (for the pre-1889 span) as part of the national chain `BRA-1889-1909`/earlier BRA national rows, since Sergipe was not itself broken out as a separate polity before the Republic. No predecessor polity representing Sergipe specifically exists before 1889 in this table. Successor: none — Sergipe remains a current Brazilian state, hence the open `end_year: 2025` matching the table's convention for still-existing units, and no successor code is listed.

## Sourced claims

- IBGE (Instituto Brasileiro de Geografia e Estatística) publishes Sergipe's official land area as approximately 21,910.348 km² in its most recent territorial-area survey, making it the smallest of Brazil's 26 states.
- Aracaju became the capital of the Province of Sergipe in 1855, replacing São Cristóvão, and has remained the state capital continuously since, per Brazilian administrative-history sources on the province-to-state transition.

## Decisions

### d-follow-default-code-pattern

**Used the dominant <ISO3>-<SUBUNIT>-<start>-<end> code pattern**

Sergipe is an ordinary Brazilian state with no bespoke historical-territory identity distinct from its role as a state (unlike e.g. Alaska or Hawaii before statehood), so the code BRA-SERGIPE-1889-2025 follows the pattern used by 338 of 351 subnational rows and matches the sibling BRA codes already in the table (BRA-ACRE-1962-2025, BRA-ALAGOAS-1889-2025, etc.), rather than inventing a bespoke code.

### d-polygon-source-unfetched

**polygon_source set to the registered slug geobr-ibge, not the route name**

The routing decision's polygon_route was registered_source_unfetched with candidate source geobr-ibge already registered in sources.yaml but its file not present locally. Per the harness's explicit instruction, registered_source_unfetched means the slug itself is the polygon_source (with polygon_status: unassigned), not the literal route category — so polygon_source is geobr-ibge and polygon_feature_id is left null pending the fetch.

## Open questions

### oq-geobr-fetch-pending

**geobr-ibge/states.gpkg has not yet been fetched into data/geodata**

The route for this entry's polygon is registered_source_unfetched: geobr-ibge is registered in sources.yaml with id_column abbrev_state, which would map directly to Sergipe via abbrev_state == 'SE', but the actual file data/geodata/geobr-ibge/states.gpkg does not exist locally in this session. Until it is fetched, polygon_status must remain unassigned and no polygon_feature_id can be asserted. Whoever fetches this source should also verify its licence (unknown as of this routing decision, per polygon_detail.candidate_new_source.licence_known: false) before it is used to assign polygons across all BRA state entries, not just this one.

### oq-predecessor-not-modeled

**No pre-1889 provincial predecessor polity exists for Sergipe specifically**

This entry's predecessor is listed as the national chain BRA-1889-1909 rather than a dedicated pre-Republic Sergipe polity, because no such row exists in the table. If a future pass adds imperial-era Brazilian provinces as their own subnational entries (analogous to how this state-era entry was created), this predecessor link should be revisited and pointed at that new entry instead of the national chain.

### oq-container-span-review

**Container basis asserts continuity through the 1903 and 1909 national-chain breaks without checking what those breaks represent**

The container edge spans the entry's full 1889-2025 range under a single container code BRA-1909-2025 with a basis claiming no intervening national break affected Sergipe's status. This assumes the 1903 and 1909 breaks in the national BRA chain reflect changes to Brazil's national government/sovereignty status (e.g., federal reorganization) rather than any change to Sergipe as a state; this has not been independently verified against the polity table's own description of those national-chain rows and should be checked if the containment gate rejects this edge.
