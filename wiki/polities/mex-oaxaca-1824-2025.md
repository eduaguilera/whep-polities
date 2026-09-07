---
polity_code: MEX-OAXACA-1824-2025
polity_name: Oaxaca
start_year: 1824
end_year: 2025
type: subnational
iso3: MEX
continent: North America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: none
polygon_feature_id: null
polygon_feature_year: null
polygon_status: unassigned
predecessor: []
successor: []
container:
  - code: MEX-1800-1848
    start_year: 1824
    end_year: 1848
    basis: Oaxaca as a state of the federated Mexican Republic falls within the pre-1848 Mexico row, which itself runs 1800-1848 and covers the era before the Mexican-American War territorial losses
  - code: MEX-1848-2025
    start_year: 1848
    end_year: 2025
    basis: Oaxaca remains a constituent state of Mexico through the post-1848 national row, which runs to the present (open end_year 2025)
---

# Oaxaca

## Summary

Oaxaca is one of the original states of the Mexican federation, a mountainous region on Mexico's Pacific side in the south of the country, home to a large indigenous population (chiefly Zapotec and Mixtec) that has shaped its distinct political and cultural profile since independence. This entry is `type: subnational`: Mexico held sovereignty over the territory throughout, and Oaxaca never existed as an independent state; the row exists to carry a sub-national reporting/administrative unit, not to compete with the national MEX chain for sovereignty ranking in the matcher. Oaxaca was constituted as a state under the Constitution of 1824, the founding document of the first Mexican federal republic, alongside the other original nineteen states, and has kept essentially the same name and identity (with boundary adjustments, not dissolution) through the Reform era, the Porfiriato, the Revolution, and to the present day. Unlike Baja California, Baja California Sur, and Quintana Roo, territories carved out later and only granted statehood in the 20th century, Oaxaca required no such promotion, which is why its span opens at the federation's founding rather than at a later admission date.

**Why this entry exists.** This entry captures Mexican state-level data for "Oaxaca" that had no home in the existing polity table: no prior polity is named Oaxaca, and the only candidates that mention Mexico at all are the two national-level rows MEX-1800-1848 and MEX-1848-2025, both of which merely CONTAIN Oaxaca rather than being it. Routing the data to either would understate the scale mismatch between a national total and a single state. The routing decision this page implements identifies Oaxaca-labelled rows spanning 1900-2023 with no existing target; per the country convention for MEX, Oaxaca is not one of the three enumerated late-admission departures (Baja California, Baja California Sur, Quintana Roo), so the default rule applies and the entry is backdated to the 1824 constitutional founding of the federated states rather than to the first year data happens to appear. State-level Mexican statistical yearbooks tabulate Oaxaca as a distinct reporting unit across the 20th century, which is the independent confirmation that this is a genuine sub-national reporting entity and not an artifact of one source's labelling.

## Territorial extent

Polygon status: Not yet assigned. No polygon available in the GeoPackage for this period. The routing decision names gadm-4.1-adm1 as the correct source type (ADM1-level state boundary, expected feature id pattern MEX.20_1 for Oaxaca) and identifies the concrete gap: the GADM 4.1 file present in this repository's data/geodata/gadm-4.1/ is a curated 81-country subset that does not include Mexico at all, so no feature can be looked up or verified yet. Since the missing dataset is a registered source not yet fetched, polygon_source here is "none" and the fetch requirement is recorded as an open question rather than asserted as fact.

Territory description: Oaxaca is a Mexican state occupying the southern Pacific coast and adjoining highlands, bordered by Guerrero to the west, Puebla to the north, Veracruz to the northeast, and Chiapas to the east, with a long Pacific shoreline including the resort area around Huatulco and Puerto Escondido. Its modern state area is approximately 93,800 km2 (INEGI figure for the present-day state), one of Mexico's larger states. Oaxaca's state boundaries have been essentially stable since the 19th century, unlike some Mexican states that were split or merged, so a present-day ADM1 polygon, once fetched, would carry low vintage risk as a proxy for the full 1824-2025 span.

## Predecessors and successors

No predecessor or successor polity rows: Oaxaca has had no prior distinct administrative existence recorded in this table (it enters directly at federation) and, as a current Mexican state, has no successor. The span is left open at 2025 to match the convention used for MEX-1848-2025 and other still-existing polities.

## Sourced claims

- State-level Mexican statistical yearbooks and INEGI historical series report agricultural and demographic data for Oaxaca as a distinct reporting unit across the 20th century, distinguishing it from national Mexican totals.
- The Constitution of 1824 (Acta Constitutiva de la Federacion / Constitucion Federal de los Estados Unidos Mexicanos) lists Oaxaca among the original states of the first Mexican federal republic, unlike Baja California, Baja California Sur, and Quintana Roo, which entered as federal territories and only gained statehood in 1931/1952 and 1974 respectively.

## Decisions

### d-start-year-1824-federation

**Start year set to 1824 federation founding, not first data year**

The routed source data for Oaxaca begins around 1900, but the polity's start_year is set to 1824, the year of the founding federal constitution, following the country convention's default rule for states not among the documented late-admission departures (Baja California, Baja California Sur, Quintana Roo). This mirrors the treatment of MEX-1800-1848/MEX-1848-2025, which are not truncated to their first data year either. The risk flagged in routing_concerns is real: this assumes Oaxaca was one of the original 1824 federation states rather than promoted later; if archival research shows otherwise the start_year should shift to the true admission year and the container edge boundary at 1824 would need to move with it.

## Open questions

### oq-gadm-mexico-fetch

**GADM 4.1 ADM1 layer for Mexico has not been fetched into this repository**

The local data/geodata/gadm-4.1/gadm41_adm1.gpkg is a curated 81-country subset that excludes Mexico entirely, so no feature_id for Oaxaca (expected pattern MEX.20_1 in the full GADM 4.1 release, but unconfirmed) can be looked up or declared yet. Until the full Mexico ADM1 layer is fetched and the correct GID_1 code for Oaxaca is verified against the actual file, polygon_status must remain unassigned. This blocks not just this entry but any other Mexican state-level polity this pipeline creates, since they all depend on the same missing dataset.

### oq-1824-founding-state-confirmation

**Whether Oaxaca was actually an original 1824 federation state needs primary-source confirmation**

This entry assumes, per the country convention's default rule, that Oaxaca was admitted at the 1824 constitutional founding rather than later, since it is not one of the three documented departure states (Baja California, Baja California Sur, Quintana Roo). This has not been independently verified against the 1824 Acta Constitutiva's actual list of constituent states or against a Mexican constitutional history source. If Oaxaca in fact entered later (e.g., after an intervening territorial reorganization), both start_year and the 1824 container edge boundary against MEX-1800-1848 would need correction.

### oq-oaxaca-boundary-stability-unverified

**Oaxaca's boundary stability since 1824 is asserted, not checked against a historical boundary source**

The territorial_extent section claims Oaxaca's state boundaries have been essentially stable since the 19th century, which is why a present-day GADM polygon would be a low-risk proxy for the full span once fetched. This claim is plausible but has not been checked against a historical Mexican administrative-boundary source, such as changes during the Reform era's district reorganizations, or any 19th-century territorial exchanges with neighboring states like Guerrero or Chiapas, both of which were themselves reorganized in this period. If a dramatic boundary change is found, the modern GADM polygon would need to be treated as a rejected proxy per the polygon proxy rules rather than a low-risk stand-in.
