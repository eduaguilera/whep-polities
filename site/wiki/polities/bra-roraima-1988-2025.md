---
polity_code: BRA-RORAIMA-1988-2025
polity_name: Roraima (state, 1988-2025)
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
polygon_feature_id: null
polygon_feature_year: null
polygon_status: unassigned
predecessor: []
successor: []
container:
  - code: BRA-1909-2025
    start_year: 1988
    end_year: 2025
    basis: Roraima is a state of the Federative Republic of Brazil from its 1988 constitutional elevation to statehood through the present; no change of national container occurs across this span.
---

# Roraima (state, 1988-2025)

## Summary

Roraima is Brazil's northernmost state, in the far north of the Amazon region bordering Venezuela and Guyana. Before 1943 the area was administered as part of the state of Amazonas. In 1943 the federal government carved out the Federal Territory of Rio Branco (renamed Território Federal de Roraima in 1962) as one of several frontier territories placed under direct federal administration rather than state government — a status driven by defense and settlement policy for the sparsely populated northern border, not by any prior distinct polity. The 1988 Constitution elevated Roraima (along with Amapá) from federal territory to full statehood, giving it its own elected government and legislature. This entry covers the state era, 1988 to the present. `type: subnational` because Roraima has never been sovereign — it is and was a first-order administrative division of Brazil throughout, first as a federally-administered territory and then as a constituent state, and the entry's purpose is to carry the correct sub-national reporting territory rather than to represent statehood itself.

**Why this entry exists.** This entry receives the Roraima-specific portion of a Brazilian subnational data reconstruction spanning 1900-2023, in which totals are allocated onto the modern Roraima state boundary for every year, including years before Roraima existed as a distinct administrative unit at all (pre-1943 it was simply part of Amazonas). 89% of the routed rows are scaled/interpolated/fallback reconstruction rather than direct period reporting, so those pre-1988 years back_cast onto this polity's modern boundary rather than being left unrouted. Previously there was no polity row for Roraima at all: the data would otherwise have had to be folded into a general BRA national total or force-matched to Amazonas, both of which misrepresent a reporting unit that Brazilian federal and state statistical agencies (IBGE) have published separately since the Federal Territory was created in 1943. The 1988 Constitution is the confirming source that Roraima became a distinct constituent unit of the federation, distinguishing it from both its Amazonas-administered past and its federal-territory interim status.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is attached in this repository yet, but a source has been identified: `geobr-ibge` (IBGE's official Brazilian state boundaries, keyed by `abbrev_state`), registered in `scripts/sources.yaml` but not present locally (0 features fetched as of this writing) — hence `polygon_route: registered_source_unfetched` and `polygon_status: unassigned` rather than `assigned`. The alternative candidate `gadm-4.1-adm1` was rejected because the locally-held GADM adm1 subset only curates 81 countries and Brazil is not among them.

**Territory description:** Roraima occupies Brazil's extreme north, bordering Venezuela to the north and Guyana to the east, with Amazonas state to its south and west and Pará to the southeast. Its capital is Boa Vista. The state covers approximately 224,300 km² (IBGE's published figure for the modern state), dominated by Amazon rainforest in the south and the Guiana Highlands/savanna (the Rupununi-adjacent "lavrado") in the north, including part of the Raposa Serra do Sol indigenous territory. This is a stated figure from IBGE, not a measurement from an attached geometry — no polygon is attached to this entry yet.

**Boundary stability caveat:** The federal-territory-to-state boundary (1943→1988) is believed to have remained essentially unchanged through statehood, but that continuity has not been verified against historical maps in this session, and a modern IBGE state boundary is being proposed as a proxy for the 1988 date without that check.

## Predecessors and successors

No predecessor polity is declared. Pre-1943 Roraima was part of Amazonas with no distinct administrative or statistical identity of its own, and 1943-1987 (the Federal Territory of Roraima/Rio Branco era) is not modeled as a separate polity segment here — both spans back_cast onto this entry's modern boundary rather than routing to a distinct predecessor. No successor is declared; Roraima remains a current Brazilian state with open end_year 2025.

## Sourced claims

- The Federal Territory of Rio Branco was created by Decree-Law 5,812 of 13 September 1943, detaching the area from Amazonas state; it was renamed Território Federal de Roraima in 1962 (Law 4,182).
- Article 14 of the Transitional Constitutional Provisions Act (ADCT) of the 1988 Brazilian Constitution transformed the federal territories of Roraima and Amapá into states of the Federation, effective 1 January 1989 (Roraima's state government installed in 1988's transition).

## Decisions

### d-back-cast-vs-federal-territory-split

**Back-cast 1900-1987 onto the state polity rather than creating a separate federal-territory segment**

The routing decision explicitly raises the alternative of modeling 1943-1987 as its own 'Federal Territory of Roraima' polity, distinct from the post-1988 state. I chose not to split it: 89% of the routed rows are already reconstructions (scaled/interpolated/fallback) allocating national or regional totals onto the modern Roraima boundary, so the value these rows carry is geographic (which land area the numbers describe) rather than administrative-status-specific. Splitting into a federal-territory segment would require sourcing federal-territory-era boundaries and administrative detail that the routing decision does not supply, for a period where almost none of the underlying data reflects territory-specific reporting anyway. This should be revisited if a source is found that reports the Federal Territory of Roraima specifically and separately from Amazonas/national totals for 1943-1987.

### d-polygon-source-unfetched

**Named geobr-ibge as the polygon source despite it being unfetched**

Per the harness's own instruction, when polygon_route is registered_source_unfetched the slug itself is the correct polygon_source value (not 'none' and not a placeholder), with polygon_status set to unassigned rather than assigned. I followed that literally: polygon_source is geobr-ibge, polygon_feature_id is null pending fetch, and the open question below records what remains to be verified once it is fetched (correct abbrev_state key, and boundary-vintage stability back to 1943).

## Open questions

### oq-geobr-ibge-fetch-and-vintage

**geobr-ibge has not been fetched, and its boundary vintage against pre-1988 Roraima is unverified**

The proposed polygon source geobr-ibge is registered in scripts/sources.yaml but has 0 features present locally, so no polygon_feature_id could be assigned in this entry. Once fetched, two things need checking: (1) that the abbrev_state key for Roraima ('RR') resolves to exactly one feature with no ambiguity against neighboring states; (2) whether IBGE's current state boundary is actually stable back to the 1943 federal-territory creation, or whether any adjustments occurred at statehood in 1988 or since (e.g., demarcation of the Raposa Serra do Sol indigenous territory in 2005, which affects internal administration but should not affect the external state boundary — this has not been confirmed).

### oq-pre1988-routing-revisit

**Whether 1900-1987 data should instead route to Amazonas or a separate federal-territory polity**

The routing_concerns explicitly flag that 1900-1942 predates even the 1943 federal territory (the area was then administratively part of Amazonas), and no distinct predecessor polity is proposed here for either 1900-1942 or the 1943-1987 federal-territory era. If a source surfaces that reports the pre-1943 area as part of Amazonas's own statistics, or reports the 1943-1987 Federal Territory of Roraima distinctly from both Amazonas and the modern state, those years should be re-routed away from this back_cast rather than continuing to be folded onto BRA-RORAIMA-1988-2025's modern boundary. This has not been checked against Amazonas's own data coverage in this session.
