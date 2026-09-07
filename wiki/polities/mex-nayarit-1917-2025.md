---
polity_code: MEX-NAYARIT-1917-2025
polity_name: Nayarit
start_year: 1917
end_year: 2025
type: subnational
iso3: MEX
continent: North America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: gadm-4.1-adm1
polygon_feature_id: null
polygon_feature_year: null
polygon_status: unassigned
predecessor: []
successor: []
container:
  - code: MEX-1848-2025
    start_year: 1917
    end_year: 2025
    basis: Nayarit has been a constituent state of the Mexican federation since its 1917 admission, and the federation's own row spans 1848-2025 without interruption across that period.
---

# Nayarit

## Summary

Nayarit is a constituent state of the Mexican federation on the Pacific coast of northwestern Mexico, bordered by Sinaloa to the northwest, Durango and Zacatecas to the northeast, Jalisco to the southeast, and the Pacific Ocean to the west and south (its territory also includes the Marías Islands archipelago). This entry is typed subnational rather than national because Mexico's sovereignty and national-level reporting are already carried by the MEX-1800-1848 and MEX-1848-2025 rows; this row exists purely to give a distinct polity code to the state-level administrative and statistical unit, mirroring the treatment given to other first-order Mexican, Spanish, and Colombian subnational divisions already in the table. The area now called Nayarit was administered as part of Jalisco until 1884, when it was separated out as the Territorio de Tepic, a federal territory under direct national administration rather than a self-governing state. It remained a territory for over three decades before the Constitution of 1917 admitted it to the federation as the State of Nayarit, the boundary and status change that fixes this entry's start_year at 1917. It continues to exist as a Mexican state today, so end_year is left open at 2025 per this project's convention for ongoing polities.

**Why this entry exists.** This entry captures data reported under a Nayarit/Tepic label for Mexico that was previously routed to the national MEX-1848-2025 row, which spans the entire federation across 177 years and roughly 30 times Nayarit's own area -- too coarse to preserve state-level detail carried by whatever series (agricultural, demographic, or trade statistics keyed to Mexican federal states) motivated this routing decision. The routing verdict that generated this page treated Nayarit as a genuine, statistically distinct reporting unit: it is one of Mexico's 32 current federal entities, each separately enumerated in national censuses and agricultural statistics since well before 1917, and its pre-1917 predecessor unit (Territorio de Tepic) was itself a distinct federal administrative division from 1884, confirming this was never merely an undifferentiated part of Jalisco or of Mexico-at-large during the period this data covers. No source in this pipeline's decision materials was cited by name/row-count for Nayarit specifically beyond the routing verdict's own reasoning, which is why the open questions above flag that the pre-1917 segment of whatever series prompted this entry still needs to be traced and matched to source row counts before the picture is complete.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon has been fetched for this period; `polygon_source: gadm-4.1-adm1` names the registered source that should eventually supply it (GADM 4.1's admin-1 layer, the standard modern first-order administrative boundary dataset), but the locally cached GADM 4.1 subset in this repository's `data/geodata/gadm-4.1/gadm41_adm1.gpkg` covers only 81 countries and Mexico is not one of them. `polygon_feature_id` is left null and `polygon_status` is `unassigned` (registered_source_unfetched) rather than `assigned`, pending that fetch and the confirmation of which GID_1 feature is Nayarit.

**Territory description:** Nayarit occupies Mexico's Pacific coast in the country's west, immediately northwest of Jalisco and Guadalajara, south of Sinaloa and Durango, and west of Zacatecas. Its terrain runs from coastal lowlands and the Marías Islands (Islas Marías) offshore in the Pacific up through the Sierra Madre Occidental foothills inland. The modern state covers approximately 27,800 km2 (INEGI's official figure for Nayarit is 27,857 km2), making it one of Mexico's smaller states by area. No polygon-derived measurement is attached to this entry yet, so this km2 figure is drawn from the modern administrative boundary as published by Mexico's national statistics institute (INEGI), not measured from any geometry in this repository. Nayarit's state boundary has been essentially stable since the 1917 admission aside from minor municipal-level adjustments, so a GADM adm1 feature fetched for the present day should serve as a low-risk proxy across the full 1917-2025 span once fetched.

## Predecessors and successors

No predecessor or successor polity codes exist yet in this table. The pre-1917 Territorio de Tepic administration that occupied the same approximate area from 1884-1917 has no corresponding row here (see open question oq-tepic-pre1917-gap); if one is created later, it should be added as this entry's `predecessor`. As a currently-existing Mexican state, this entry has no successor and its `end_year` of 2025 is the open-ended convention for ongoing polities rather than a real termination.

## Sourced claims

- Nayarit was created as the Territorio de Tepic in 1884, carved from the state of Jalisco, and existed as a federal territory (not a state) until the Constitution of 1917 elevated it to full statehood as Nayarit on 26 January 1917.
- GADM's global admin-1 layer (version 4.1) digitises Mexico's 32 federal entities including Nayarit as first-order administrative divisions, but the locally cached subset of that dataset in this repository covers only 81 countries and Mexico is not among them, so no feature has yet been fetched for this polity.

## Decisions

### d-code-form-subunit-not-iso-numeric

**Used MEX-NAYARIT-1917-2025 rather than a numeric subunit abbreviation**

The dominant pattern for subnational rows is <ISO3>-<SUBUNIT>-<start>-<end> with SUBUNIT typically a short postal/ISO-3166-2 code (e.g. ESP-AS, ESP-CA). Mexico has no existing subnational rows to set a local abbreviation convention, and Nayarit's ISO 3166-2 code is MX-NAY. I chose the fuller token NAYARIT over the two/three-letter NAY to avoid collision risk with other Mexican states in this session's batch (several are being created in parallel) and because the source decision object itself used unit_id MEX-NAYARIT. This still follows the <ISO3>-<SUBUNIT>-<start>-<end> shape; it is not a bespoke-code departure, just a longer subunit token than the Spanish/Algerian exemplars use.

### d-start-year-1917-admission

**Start year set to 1917 (statehood), not 1900 (data start) or 1824**

Nayarit was the Territorio de Tepic, a federal territory carved from Jalisco in 1884, until it was admitted as a full state of the Mexican federation on 26 January 1917 under the Constitution of 1917. The routing decision's default rule for this country is admission year as state start. Pre-1917 rows (1900-1916 in the source data) attach instead to the Tepic territorial administration or to MEX-1848-2025 depending on how that gap is eventually resolved -- left as an open question below since no Tepic polity exists yet to receive them.

### d-polygon-status-unassigned

**polygon_source is the registered slug gadm-4.1-adm1 with polygon_status unassigned, not new_source_needed**

The routing decision's polygon_route is registered_source_unfetched: GADM 4.1 adm1 is registered in scripts/sources.yaml but the local subset file (data/geodata/gadm-4.1/gadm41_adm1.gpkg) covers only 81 countries and Mexico is not among them. Per the harness rule for this route, the slug itself is the source and polygon_status is unassigned (not new_source_needed, which would misstate that GADM isn't registered at all, and not assigned, since no feature has actually been fetched). polygon_feature_id is left null pending that fetch.

## Open questions

### oq-tepic-pre1917-gap

**1900-1916 Tepic-territory data has no polity row to attach to**

The data underlying this entry likely includes rows for Nayarit/Tepic before 1917 that this polity's start_year now excludes, since Territorio de Tepic (a federal territory, not a state) governed the same approximate area from 1884 until the 1917 admission. If pre-1917 rows exist in mitchell, fao1952, or similar sources under a Tepic or Nayarit label, they currently have nowhere valid to route: attaching them to MEX-1848-2025 would blend territorial-era data into the national total, and no MEX-TEPIC-*-1917 polity has been created. Whether the pre-statehood segment needs its own row, analogous to how Manchuria's pre/post-1949 administrations were split into MAN-1945-1950 and this pattern's successor, should be checked against whatever source rows actually exist for Nayarit/Tepic before 1917.

### oq-gadm-mexico-fetch-needed

**GADM 4.1 adm1 boundary for Nayarit has not actually been fetched or verified**

polygon_status is unassigned because the local GADM 4.1 adm1 subset (data/geodata/gadm-4.1/gadm41_adm1.gpkg) does not include Mexico at all (0 of the 81 covered countries). Fetching Mexico's adm1 layer and confirming which GID_1 feature corresponds to Nayarit (expected around GID_1 'MEX.18_1' by alphabetical convention in GADM 3.6/4.1, but this must be verified against the actual attribute table once fetched, not assumed) is required before polygon_status can move to assigned. Separately, the exact 1917 admission date (26 January per secondary sources consulted) has not been checked against a primary Diario Oficial or Mexican constitutional-history source in this session, so start_year could in principle need a one-year adjustment if that date is wrong.
