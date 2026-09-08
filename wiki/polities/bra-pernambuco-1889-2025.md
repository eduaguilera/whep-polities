---
polity_code: BRA-PERNAMBUCO-1889-2025
polity_name: Pernambuco
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
    basis: Empire of Brazil era per cshapes-2.0's BRA-1800-1903 segment; Pernambuco was an imperial province until the 1889 Proclamation of the Republic, which is captured within this container edge rather than as a boundary in this row
  - code: BRA-1903-1909
    start_year: 1903
    end_year: 1909
    basis: Early Republic era per cshapes-2.0's BRA-1903-1909 segment; no territorial change to Pernambuco itself, only the national container changes
  - code: BRA-1909-2025
    start_year: 1909
    end_year: 2025
    basis: Modern Brazil era per cshapes-2.0's BRA-1909-2025 segment, running to present; Pernambuco continues as a federative state under this container to the end of the row's span
---

# Pernambuco

## Summary

Pernambuco is a Brazilian state on the northeastern coast, one of the original Imperial provinces converted into a federative state by the 1889 Proclamation of the Republic. This entry is `type: subnational` because it is a first-order administrative division of a sovereign country (Brazil), not a sovereign state itself — it must sit below the national BRA row in the matcher's hierarchy while still being addressable as its own reporting unit. The 1889 start follows the same default rule already applied to sibling Brazilian state entries (Bahia, Ceará, Alagoas): Pernambuco is not one of the six documented departure cases (states created or split later than the general Republic conversion), so it gets the standard 1889 start rather than a bespoke one. The state has been continuously administered since, with no split or merger changing its territory, so the entry runs open-ended to the present (2025).

**Why this entry exists.** Input data: state-level agricultural/production statistics for Brazil's Pernambuco, sourced under the label "Pernambuco" / "Brazil, Pernambuco", covering 1900-2023 (data begins in 1900, within the 1889-2025 default span; the pre-1900 years 1889-1899 are simply not covered by any data row and are left un-evidenced rather than fabricated). Before this entry existed, these state-level rows had nowhere to go but the national polity BRA-1909-2025 (or its predecessor segments), which silently aggregated a single state's figures into all-Brazil totals — wrong because the source explicitly tabulates Pernambuco separately from other states and from the national total, so folding it into the country row both double-counts against other state-level entries and misrepresents the geographic scope of the number. What confirms Pernambuco is a distinct reporting/administrative entity: it is one of Brazil's 27 first-order federative units under the 1889 Republican constitution and all successors, with its own state government, and it already has sibling entries in this database (BRA-BAHIA, BRA-CE, BRA-ALAGOAS, etc.) built on the same routing logic — Pernambuco was simply missing from that set until now.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon available in the GeoPackage for this period. The registered source with the correct granularity for Brazilian ADM1 boundaries is `geobr-ibge` (id_column `abbrev_state`, state code "PE"), which is purpose-built for exactly this kind of unit, but its data file (`data/geodata/geobr-ibge/states.gpkg`) is not present locally and has not been fetched. `gadm-4.1-adm1` is present locally but does not include Brazil among its 81 covered countries. `cshapes-2.0` carries Brazil only at the whole-country level (BRA-1800-1903, BRA-1903-1909, BRA-1909-2025), with no subdivision into states, so no polygon can be constructed from currently-fetched registered sources. Once `geobr-ibge` is fetched, Pernambuco should be directly available as `registered_source_feature` with feature id `PE`.

**Territory description:** Pernambuco is a state on Brazil's northeastern Atlantic coast, bordered by Paraíba, Ceará, Piauí, Bahia, Alagoas, and Rio Grande do Norte, and including the offshore archipelago of Fernando de Noronha. Its capital is Recife. The modern state covers approximately 98,000 km2 — a figure drawn from published IBGE state-area statistics for the current boundary, not from any geometry attached to this entry (none is attached). The state's mainland boundaries have been broadly stable since the early Republic; the main documented change in this period is the incorporation of the Fernando de Noronha federal territory back into Pernambuco state in 1988 (it had been split off as a separate federal territory in 1942), which is small in area (~26 km2) relative to the mainland state and does not materially affect the ~98,000 km2 figure.

## Predecessors and successors

No predecessor: Pernambuco is created directly at the 1889 Republic conversion from the former Imperial province of the same name and same approximate territory, so no distinct pre-1889 polity row precedes it — the province-to-state transition is treated as a continuity, not a break, consistent with how the other Brazilian state entries handle 1889. No successor: the state remains current as of 2025 with no split, merger, or renaming, so `successor` is empty and `end_year` is open at 2025 pending any future data or administrative change.

## Sourced claims

- State-level agricultural/production data under the label "Pernambuco" / "Brazil, Pernambuco" spans 1900-2023, matching the pattern of sibling entries (BAHIA, CEARA, ALAGOAS) that were each split out from the national BRA row for the same reason: source-level state disaggregation that predates this database's polity table.
- IBGE (Instituto Brasileiro de Geografia e Estatística) reports Fernando de Noronha as reincorporated into Pernambuco state by federal law in 1988, after being a separate federal territory from 1942; this is a boundary event within the entry's span that is not reflected in any polygon here since none is yet attached.

## Decisions

### d-default-1889-start

**Used the default 1889 Republic-conversion start year rather than a bespoke span**

Pernambuco is not among the six documented departure cases for Brazilian states (later creation or split from an existing state) recorded in prior routing decisions for BAHIA, CEARA, ALAGOAS, etc. The 1889 Proclamation of the Republic converted the Imperial province of Pernambuco directly into a federative state with no territorial break, so the standard default-start rule applies and the code follows the dominant <ISO3>-<SUBUNIT>-<start>-<end> pattern (BRA-PERNAMBUCO-1889-2025) rather than a bespoke code, since Pernambuco is an ordinary first-order administrative unit and not a historical territory with an independent identity of its own (unlike ALK or HAW).

### d-three-container-edges

**Split the container into three edges to tile 1889-2025 against cshapes' own BRA segmentation**

The routing decision's proposed container_code was a single BRA-1909-2025 edge, which would leave 1889-1909 (20 years) uncontained and fail the containment-tiling gate. cshapes-2.0 segments Brazil itself into BRA-1800-1903, BRA-1903-1909, and BRA-1909-2025; since Pernambuco's own span starts in 1889, inside the first cshapes segment, the container list here uses all three of those national eras as separate edges so the full 1889-2025 span is covered with no gap, even though Pernambuco's own territory did not change across those national-container transitions.

## Open questions

### oq-fernando-de-noronha-boundary

**Does the eventual polygon need to account for Fernando de Noronha's 1942-1988 separation?**

Fernando de Noronha was split off from Pernambuco as a separate federal territory in 1942 and reincorporated in 1988. Once geobr-ibge is fetched and a polygon is assigned, the current-day feature will include the archipelago for the entire 1889-2025 span, which is a ~26 km2 over-inclusion for the 1942-1988 window relative to the state's actual administrative extent in that period. This is small enough that it may not warrant a separate sub-period polygon, but it should be evaluated once the source is actually available rather than assumed away here.

### oq-pre-1900-data-gap

**Is the 1889-1899 data gap real or a routing artifact of an unexamined source?**

The data driving this entry begins in 1900, leaving 1889-1899 within the polity's span but without any routed rows. It is not yet confirmed whether this is because no state-level Pernambuco data exists for that decade in any ingested source, or because such data exists under a different label (e.g., an alternate spelling, or nested under a regional aggregate) that has not yet been identified and routed here. If earlier data does surface, it falls within the existing 1889-2025 span and would not require re-spanning, only re-routing.
