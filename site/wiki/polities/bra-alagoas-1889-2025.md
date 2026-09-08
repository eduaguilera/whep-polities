---
polity_code: BRA-ALAGOAS-1889-2025
polity_name: Alagoas
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
    basis: Alagoas as a province of the Empire of Brazil until the Republic's provinces-to-states conversion, within the national row that runs to 1903
  - code: BRA-1903-1909
    start_year: 1903
    end_year: 1909
    basis: Alagoas as a state of the Republic, within the national row covering this narrow 1903-1909 era
  - code: BRA-1909-2025
    start_year: 1909
    end_year: 2025
    basis: Alagoas as a state of the Republic, within the current national row spanning 1909 to the present
---

# Alagoas

## Summary

Alagoas is a Brazilian state on the Atlantic coast of the Nordeste (Northeast) region, between Pernambuco to the north and Sergipe/Bahia to the south. This entry covers Alagoas from 1889, when the Proclamation of the Republic converted the former Imperial province of Alagoas into a state of the federation, to the present. `type: subnational` is used because Alagoas has never been a sovereign polity in its own right: it was a captaincy/province under Portuguese and then Imperial Brazilian rule, and has been a first-order administrative division (state) of the Brazilian federation continuously since 1889, with no territorial or status break of the kind that would justify a predecessor row (unlike BRA-ACRE, which passed through Bolivian sovereignty and federal-territory status before statehood). The 1889 start follows the country convention's default rule: Alagoas is not among the small set of listed BRA departures (Acre, and other units whose Brazilian-administered history begins later or was interrupted), so the default republic-founding start applies.

**Why this entry exists.** The routing decision this page implements (unit_id BRA-ALAGOAS) found no existing polity in the database representing Alagoas itself: the only BRA rows are three national totals (BRA-1800-1903, BRA-1903-1909, BRA-1909-2025), none of which is state-scale. Source rows describing Alagoas specifically — under the sibling BRA-BAHIA/BRA-CEARA verdicts' pattern, a state-level Brazilian subnational dataset spanning the full republican era — had previously nowhere correct to route except the national BRA-1909-2025 row, a container more than thirty times Alagoas's own territory, which would misattribute state-level agricultural/production data to the whole country. What confirms Alagoas is a distinct reporting unit rather than folded into national Brazil figures is the same practice documented for BRA-BAHIA and BRA-CEARA: the source reports Alagoas as a named first-order administrative unit (a Brazilian state), consistent with IBGE's own state-level statistical reporting since the founding of the Republic. This entry is one of a batch of Brazilian state-level polities created under the same default start-year rule, with no departure listed for Alagoas in the country convention.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon available in the GeoPackage for this period. The correct source is `geobr-ibge` (Brazilian state boundaries, id_column `abbrev_state`), which is registered in `scripts/sources.yaml` specifically to carry Brazilian ADM1 units but whose file (`data/geodata/geobr-ibge/states.gpkg`) is not present locally, per the routing decision's own polygon_reasoning. `gadm-4.1-adm1` excludes Brazil entirely from its locally curated 81-country subset, and the only BRA source currently present, `cshapes-2.0`, digitises Brazil at whole-country scale only. Once `geobr-ibge` is fetched, this entry should match `abbrev_state='AL'`.

**Territory description:** modern Alagoas covers approximately 27,800 km2, one of Brazil's smaller states, on the Atlantic coast of the Nordeste region — bordered by Pernambuco to the north, Sergipe to the south, Bahia to the southwest, and the Atlantic Ocean to the east. Its capital and largest city is Maceió. The state occupies a narrow coastal strip and the lower São Francisco river basin along its southern border. Its boundary has been administratively stable since the Republic converted the imperial province directly into a state in 1889, without the territorial disputes or later admission that some other Brazilian states experienced, so the modern administrative boundary should be a low-risk proxy across the full 1889-2025 span once `geobr-ibge` is fetched. No `polygon_area_km2` is recorded here since no geometry is yet attached.

## Predecessors and successors

No predecessor row is created by this decision: Alagoas's status as a first-order Brazilian administrative unit runs continuously back to 1889 with no interruption of the kind that separates BRA-ACRE from its federal-territory and Bolivian-sovereignty predecessors, so there is no separate pre-1889 provincial entry proposed here (the pre-1889 Imperial province is left to the national BRA-1800-1903 row, consistent with the default convention). This entry has no successor — Alagoas remains a Brazilian state to the present, so the span runs to 2025 as still-current.

## Sourced claims

- The Proclamation of the Republic (15 November 1889) converted the Imperial provinces, including Alagoas, into states of the new federation, the event that fixes this entry's 1889 start under the country convention's default rule.
- IBGE (Brazil's national statistics institute) reports agricultural and demographic data at the state level for Alagoas continuously since the early Republic, the same reporting practice cited for sibling entries BRA-BAHIA and BRA-CEARA as evidence the unit is a distinct, statistically tracked reporting territory rather than a component folded into national totals.

## Decisions

### d-code-iso3-subunit-start-end-pattern

**Code follows the dominant <ISO3>-<SUBUNIT>-<start>-<end> pattern**

Used BRA-ALAGOAS-1889-2025 rather than a bespoke code, matching the pattern already established for sibling Brazilian state entries (e.g. BRA-BAHIA, BRA-CEARA, BRA-ACRE) created under the same batch of routing verdicts. Alagoas is a first-order administrative division (a Brazilian state) with no historical identity as a polity distinct from that administrative role — unlike a bespoke case such as Alaska-as-territory or Hyderabad, it does not predate or outlive its container's administrative scheme. That matches the 57/66 dominant subnational pattern, not the three bespoke cases. SUBUNIT is the plain state name 'ALAGOAS' rather than the IBGE two-letter code 'AL', for consistency with the sibling BRA-ACRE entry's stated reasoning: Brazilian states lack a universally recognized postal-style abbreviation the way US states or Spanish provinces do, so the full name is used and is self-documenting.

### d-container-three-edges-tile-full-span

**Three container edges are needed, not one, because the national row itself changes across 1889-2025**

The routing decision's proposed container_code is BRA-1909-2025 alone, but that row only starts in 1909 — leaving 1889-1909 uncontained if a single edge were used, which the containment gate would reject as falling outside the container's own span. The polity table shows three successive national BRA rows: BRA-1800-1903 (to 1903), BRA-1903-1909, and BRA-1909-2025. This entry's container list therefore has three edges, one per national era, together tiling the full 1889-2025 span with no gap: 1889-1903 under BRA-1800-1903, 1903-1909 under BRA-1903-1909, and 1909-2025 under BRA-1909-2025 (the routing decision's own proposed container, correctly used for its own portion of the span).

## Open questions

### oq-geobr-ibge-not-fetched

**geobr-ibge is registered but its file has never been pulled to disk**

polygon_status is 'unassigned' because geobr-ibge is named in scripts/sources.yaml as the correct source for Brazilian state boundaries (id_column abbrev_state) but present_locally=False per the routing decision's polygon_detail — the file data/geodata/geobr-ibge/states.gpkg does not exist locally, so no feature_id can be matched yet. This is the same blocking task recorded on the sibling BRA-ACRE entry. Once fetched, this entry should match abbrev_state='AL' and polygon_status should move to 'assigned', with the resulting measured area cross-checked against IBGE's own published figure for Alagoas (commonly cited near 27,800 km2, not independently verified against a specific IBGE table in this pass).

### oq-1889-vs-1903-provincial-boundary-continuity

**Was the province-to-state boundary literally unchanged in 1889, or is this an assumed continuity?**

This entry treats the 1889 Imperial province of Alagoas and the 1889-onward Republican state of Alagoas as territorially identical, which is the standard assumption for Brazilian provinces-to-states conversion but has not been checked here against any 19th-century boundary source (e.g. whether municipal-boundary adjustments with neighbouring Pernambuco or Sergipe occurred in the transition years). If a future source shows a boundary change in this window, the geobr-ibge proxy (a present-day boundary) would need the same kind of vintage-risk caveat already flagged for BRA-ACRE's federal-territory predecessor.

### oq-source-row-count-and-span-not-in-decision-object

**The routing decision gives no row count or exact year range for the source data this entry receives**

Unlike the BRA-ACRE decision, which quoted a specific method-breakdown and row count for its source, the decision implemented here gives only a qualitative description ('this matches sibling verdicts already recorded') without stating how many rows or which exact years of Alagoas data are being routed to this new polity. The page-requirements spec asks for the input data's row count and year range explicitly; that detail should be pulled from the underlying routing_verdicts.csv / assertion ledger and added here once available, rather than asserted from memory.
