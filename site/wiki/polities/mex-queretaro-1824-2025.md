---
polity_code: MEX-QUERETARO-1824-2025
polity_name: Querétaro
start_year: 1824
end_year: 2025
type: subnational
iso3: MEX
continent: North America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: gadm-4.1-adm1
polygon_feature_id: MEX.22_1
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: MEX-1800-1848
    start_year: 1824
    end_year: 1848
    basis: Querétaro was one of the original states named in the federal pact of the 1824 Constitution of the United Mexican States, and remained part of Mexico's territory through the loss of the northern territories in 1848.
  - code: MEX-1848-2025
    start_year: 1848
    end_year: 2025
    basis: Querétaro continues as a constituent state of the United Mexican States, unaffected by the 1848 cession of the northern territories to the United States, through to the present.
---

# Querétaro

## Summary

Querétaro is one of the 31 states of the United Mexican States, located on the central Mexican plateau north of Mexico City, bordered by Guanajuato, San Luis Potosí, Hidalgo and Mexico State. This entry captures it as a federal constituent state (`type: subnational`) rather than a sovereign polity, so it does not compete with the national MEX chain for sovereignty-ranked matching. It was one of the original states named in the pact of union in the 1824 Constitution of the United Mexican States that created the federal republic out of the former Provincias Internas and intendancies of New Spain; Querétaro is not among the three states (Baja California, Baja California Sur, Quintana Roo) that entered the federation later as territories promoted to statehood, so the country convention's default rule applies: start_year is set to 1824, the year of the federation's founding, rather than derived from the extent of any single dataset. The state's own political history includes brief interruptions common to all Mexican states in this period (the centralist Siete Leyes of 1836-1846, the French intervention of 1863-1867), but none of these episodes removed Querétaro from Mexican sovereignty or redrew it as a separate reporting unit, so a single span from 1824 to the present (end_year 2025, open) is used rather than segmenting the entry.

**Why this entry exists.** No existing polity in the database represents Querétaro; the candidate list for this unit was empty, and the only prior match available was the national aggregate MEX-1848-2025 (and, for the earlier span, MEX-1800-1848), which is roughly 165 times the area of this one state and would blend Querétaro-specific statistics into a nationwide total. Federico-Tena and comparable historical-statistics compilations treat Mexican federal states as distinct sub-national reporting units from the 19th century onward, consistent with Querétaro appearing as a named unit in Mexican census and agricultural-production series (e.g. INEGI historical censuses) separately from national totals. No production/trade rows have yet been routed to this code in the current ingest; the entry is created ahead of that routing, per the country convention that all 1824-founding states receive rows before data matching proceeds, so that when Querétaro-labeled data is encountered it has a home other than the national total.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon feature is currently matched in the GeoPackage for this state. The intended source is `gadm-4.1-adm1` (GID_1 `MEX.15_1` in the global GADM 4.1 dataset), which is registered in `scripts/sources.yaml` with `present_locally=True`, but the local file at `data/geodata/gadm-4.1/gadm41_adm1.gpkg` is a partial extract covering only 81 countries and does not include Mexico (0 rows for MEX). The source is therefore registered but unfetched for this country, not missing from the registry — `polygon_source: gadm-4.1-adm1` records the intended source and `polygon_status: unassigned` records that it has not actually been attached. Fetching the full global GADM 4.1 admin-1 dataset (or the Mexico-specific subset) would resolve this.

**Territory description:** Querétaro is a small central Mexican state on the Bajío/central plateau, roughly 200 km northwest of Mexico City. Its capital is Santiago de Querétaro. The modern state covers approximately 11,700 km², one of the smaller Mexican states by area, bounded by Guanajuato to the northwest, San Luis Potosí to the north, Hidalgo to the east and México State to the south. No area figure is measured from an attached geometry here since none is attached; the ~11,700 km² figure is the state's present-day administrative area as commonly reported (e.g. INEGI), not a polygon measurement.

## Predecessors and successors

No predecessor or successor polity is recorded: Querétaro has been a continuous constituent state of Mexico since the 1824 federation and, unlike Baja California, Baja California Sur or Quintana Roo, was never a federal territory later promoted to statehood, so there is no earlier territorial-status entry to chain from. It remains current (end_year 2025, open), so no successor entry exists either.

## Sourced claims

- Querétaro was one of the original constituent states named in the pact of union of the 1824 Constitution of the United Mexican States, distinguishing it from Baja California, Baja California Sur and Quintana Roo, which entered the federation later as territories converted to statehood (the last, Quintana Roo, only in 1974).
- The `gadm-4.1-adm1` source is listed in `scripts/sources.yaml` with `present_locally=True`, but the local file `data/geodata/gadm-4.1/gadm41_adm1.gpkg` contains admin-1 features for only 81 countries and has zero rows with ISO3 `MEX`, confirming the source is registered but not yet fetched for this country.

## Decisions

### d-code-follows-dominant-pattern

**Code follows the dominant <ISO3>-<SUBUNIT>-<start>-<end> pattern**

Chose `MEX-QUERETARO-1824-2025` rather than a bespoke code, since Querétaro is an ordinary federal constituent state with no independent identity outside the Mexican federation — it is not a historical territory with a name of its own in the way Alaska Territory or Hyderabad State are. The subunit token `QUERETARO` (rather than a postal abbreviation like `QRO`) was used because no existing MEX subnational row exists to set a precedent, and the full name avoids ambiguity with other Mexican states whose two-letter abbreviations might collide.

### d-two-container-eras-for-1848-cession

**Container split into two eras at the 1848 US-Mexico cession**

The proposed decision only supplied `MEX-1848-2025` as the container, but that row's own span starts in 1848 while this entry's span starts in 1824 (per the country convention's federation-founding rule), leaving 1824-1848 uncontained. The polity table has a separate national row `MEX-1800-1848` ("Mexico (to 1848)") covering exactly that earlier era, so a second container edge was added for 1824-1848 against that row to tile the full span with no gap, as required by the containment gate.

## Open questions

### oq-polygon-fetch-needed

**GADM 4.1 admin-1 data for Mexico needs to be fetched**

The registered source `gadm-4.1-adm1` is the correct polygon source for this state (GID_1 `MEX.15_1`), but the locally cached GeoPackage only covers 81 countries and Mexico is not among them. Until the full global GADM 4.1 admin-1 dataset (or a Mexico-specific extract) is fetched and loaded, this entry has `polygon_status: unassigned` and no geometry. Resolving this is a data-fetch task, not a routing or boundary-identification task — the feature ID to use once fetched should be `MEX.15_1`.

### oq-boundary-vintage-since-1824

**Whether Querétaro's boundaries have been stable since 1824**

This entry spans 1824-2025 using a single (future) GADM present-day boundary as its eventual polygon, which assumes the state's borders have been effectively stable for two centuries. Mexican state boundaries have in fact seen minor adjustments and disputes with neighboring states over this period (e.g. periodic disputes with Guanajuato and San Luis Potosí over municipal boundary lines), though none is known to have substantially resized the state. This has not been verified against a historical-boundary source and should be checked before treating a present-day GADM polygon as valid for the full 1824-2025 span; if a dramatic resize is found, the span should be split rather than proxied.

### oq-no-rows-yet-routed

**No production/trade data rows are yet routed to this code**

This entry is created ahead of any confirmed data routing, per the country convention that establishes all original 1824 federation states before matching proceeds. It is not yet known which source rows (if any) labeled "Querétaro" or "Queretaro" exist in the ingested data and should be routed here instead of to the national MEX total; a follow-up pass should search `mitchell`, `fao1952`, and INEGI-derived sources for state-level Querétaro rows and route them to this code.
