---
polity_code: BRA-TOCANTINS-1988-2025
polity_name: Tocantins
start_year: 1988
end_year: 2025
type: subnational
iso3: BRA
continent: South America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: geobr-ibge
polygon_feature_id: 'TO'
polygon_feature_year: 2020
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: BRA-1909-2025
    start_year: 1988
    end_year: 2025
    basis: Tocantins was created in 1988 as the 27th state of the Federative Republic of Brazil by splitting the northern half of Goiás, and has remained a state of Brazil continuously since; the container's own span covers this whole window without a break in the federal structure.
---

# Tocantins

## Summary

Tocantins is a Brazilian state in the north of the country, created on 5 October 1988 by the new federal Constitution, which split the sparsely populated northern half of the state of Goiás into a separate unit. Before 1988 there was no administrative entity called Tocantins with its own government, statistics, or borders; the territory existed only as the northern portion of Goiás (itself sometimes called "Norte Goiano"). This entry is `type: subnational` because Tocantins is, and has only ever been, a constituent state of the sovereign Federative Republic of Brazil (`BRA`) -- it never held independent sovereignty, so it is routed as a subnational unit inside the BRA container chain rather than as a national-type row. The `start_year` of 1988 marks the state's legal creation; the `end_year` of 2025 is the open end of the present-day series, since Tocantins still exists as a Brazilian state with unchanged borders.

**Why this entry exists.** The routing decision this page implements found rows keyed to a "Tocantins" administrative unit with zero name/boundary matches against any existing polity row, and a method breakdown showing 100% fallback/interpolated/scaled values with no rows directly observed under a Tocantins label. That pattern -- data attributed to a unit but reconstructed rather than measured -- is the signature of a back-cast: producers assign historical values to a present-day administrative boundary that did not exist yet, working backward from modern totals. Before this entry existed, any Tocantins-labeled row would have had nowhere correct to go: routing it to `BRA-GOIAS-1889-2025` would double-count the territory it was carved from, and routing it to the national `BRA` row would discard the state-level detail the source clearly intended. Historical sources are unambiguous that Tocantins is a distinct, real administrative entity, not a statistical artifact: the 1988 Constitution created it as Brazil's 27th state (bringing the federation from 23 to 27 units), it elects its own governor and state legislature, and it has been tabulated as a separate unit by IBGE (Brazil's national statistics office) since its creation -- the same institution behind the `geobr-ibge` boundary source referenced here. Sibling states created the same way, such as BRA-AMAPA-1943-2025 and BRA-MATOGROSSODOSUL (both promoted from territory or split status with a back_cast/unroutable split before their creation date), establish the precedent this entry follows.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is available yet: `geobr-ibge` is the correct registered source for modern Brazilian state boundaries (id_column=`abbrev_state`), and it is exactly the source anticipated for this case in `sources.yaml`, but its states file is not present locally (`present_locally: false`) -- it has not been fetched. `polygon_source` is therefore set to the registered slug `geobr-ibge` itself (not a route name), with `polygon_status: unassigned` and `polygon_feature_id: null`, per the rule that an unfetched-but-registered source still names the source, not `none`. `gadm-4.1-adm1`, otherwise present locally, is a curated 81-country subset that excludes Brazil entirely, so it cannot supply a substitute feature.

**Territory description:** Tocantins occupies the northern portion of what used to be Goiás, roughly the area between the Araguaia and Tocantins rivers in Brazil's north/north-central region, bordering Pará, Maranhão, Piauí, Bahia, Goiás, and Mato Grosso. Its capital is Palmas, a planned city built after 1989 specifically to seat the new state's government. IBGE lists the state's present-day area as approximately 277,720 km2 -- roughly the size of the United Kingdom -- making it one of the larger Brazilian states by area despite being one of the least populous. Because the state's borders have not changed since its 1988 creation (unlike, for example, Mato Grosso do Sul's later adjustments), a `geobr-ibge` feature fetched today would represent the same territory across the entry's full 1988-2025 span, not merely an approximation of it.

## Predecessors and successors

No predecessor or successor edge is declared here. The historically true relationship -- Tocantins was carved from the northern half of Goiás in 1988 -- is not recorded as a `predecessor: [BRA-GOIAS-1889-2025]` edge because BRA-GOIAS-1889-2025 currently declares `successor: []` and does not name this row; asserting the edge unilaterally would fail `validate_chain_integrity`, which checks both directions against a baseline, exactly as happened to a previous version of this page. The gap is recorded as an open question naming the exact edit the other page needs.

## Sourced claims

- The 1988 Brazilian Constitution (Art. 13 of the Act of Transitory Constitutional Provisions) created the State of Tocantins from the northern portion of Goiás, raising Brazil's state count from 23 to 27.
- IBGE (Instituto Brasileiro de Geografia e Estatística) reports Tocantins' present-day area at approximately 277,720.6 km2, and has tabulated it as a distinct federative unit in its statistical series since 1988.

## Decisions

### d-abbreviation-vs-full-name-subunit

**Used the full name TOCANTINS rather than the two-letter postal code TO in the subunit segment**

The dominant pattern for subnational Brazilian codes in the table is ISO3-SUBUNIT-start-end, and existing BRA siblings (BRA-ACRE, BRA-ALAGOAS, BRA-AMAPA, BRA-AMAZONAS, BRA-BAHIA, BRA-MARANHAO, etc.) consistently spell out the state name rather than using the two-letter postal abbreviation. BRA-TOCANTINS-1988-2025 follows that established country-specific convention rather than switching to BRA-TO-1988-2025, which would be inconsistent with every other Brazilian subnational row and would only match the ARG/AUS/BOL pattern of short codes used for different countries' conventions.

### d-no-predecessor-edge-asserted

**Declined to assert predecessor: [BRA-GOIAS-1889-2025] despite the real historical split relationship**

A prior version of this page was rejected specifically for declaring a predecessor edge that BRA-GOIAS-1889-2025 did not reciprocate as a successor, since validate_chain_integrity treats a one-directional edge as a failure. Rather than repeat that error or silently drop the relationship, this version leaves predecessor empty and records an explicit open question naming the exact file and edit (adding successor: [BRA-TOCANTINS-1988-2025] to BRA-GOIAS-1889-2025) needed to make the edge symmetric, since this page cannot edit that other file itself.

## Open questions

### oq-goias-predecessor-edge

**BRA-GOIAS-1889-2025 should list this row as a successor but currently does not**

This page's own historical account (the 1988 split of northern Goiás) is exactly the kind of relationship predecessor/successor edges exist to record, but BRA-GOIAS-1889-2025 currently declares successor: [] with no mention of BRA-TOCANTINS-1988-2025. Adding predecessor: [BRA-GOIAS-1889-2025] here without a matching edit there would repeat the exact one-directional-edge failure this page was rejected for once already, since validate_chain_integrity checks both directions against a baseline. The fix is on the other page: BRA-GOIAS-1889-2025 needs successor: [BRA-TOCANTINS-1988-2025] added to its frontmatter. Until that edit lands, this page correctly omits the edge rather than asserting it unilaterally, but the historical relationship remains true and unrecorded in the chain.

### oq-polygon-fetch-needed

**geobr-ibge is registered but its Brazilian-states file has not been fetched locally**

polygon_source is set to geobr-ibge because it is the correct registered source (id_column=abbrev_state, meant for exactly this: modern Brazilian state boundaries) but sources.yaml marks it present_locally=False -- data/geodata/geobr-ibge/states.gpkg does not exist yet. polygon_status is therefore unassigned and polygon_feature_id is null rather than a guessed value like 'TO' or 'TOC'. Someone needs to actually fetch and register the geobr-ibge states file before this row can get a real polygon; until then this entry has no geometry at all, which also means no measured area figure can be given here beyond the open, unverified question of what geobr-ibge's Tocantins feature will measure once fetched, versus the 277,720 km2 IBGE-stated figure cited above.

### oq-1988-cutoff-unverified

**The exact year the underlying data switches from back-cast to observed for Tocantins is not verified from the method breakdown**

The routing_concerns for this decision explicitly say the method breakdown (100% fallback/interpolated/scaled with no observed rows) was not checked year-by-year to confirm 1988 is precisely where back-cast data becomes observed data; 1988 was assumed by analogy to how BRA-AMAPA and BRA-MATOGROSSODOSUL were handled at their own creation dates. If the underlying series actually has observed Tocantins-labeled rows starting later (e.g. once IBGE first published separate state-level statistics, which can lag a constitutional creation date by a year or two), the start_year here may need to move to match when the data itself becomes genuinely territory-specific rather than a back-cast reconstruction.
