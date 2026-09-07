---
polity_code: COL-TOLIMA-1886-2025
polity_name: Tolima (department of Colombia)
start_year: 1886
end_year: 2025
type: subnational
iso3: COL
continent: South America
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
  - code: COL-1830-1903
    start_year: 1886
    end_year: 1903
    basis: Tolima was constituted as a sovereign federal state (Estado Soberano del Tolima) under the United States of Colombia and remained part of that national polity through the 1886 constitutional reorganisation into a unitary republic
  - code: COL-1903-1922
    start_year: 1903
    end_year: 1922
    basis: Tolima continued as a department of the Republic of Colombia through the period following the 1903 secession of Panama, which did not affect Tolima's own boundaries
  - code: COL-1922-2025
    start_year: 1922
    end_year: 2025
    basis: Tolima remains a department of the Republic of Colombia under its current national administration to the present
---

# Tolima (department of Colombia)

## Summary

Tolima is a department of central Colombia, located in the upper Magdalena River valley between the Cordillera Central and Cordillera Oriental, with its capital at Ibagué. This entry captures it as a `subnational` administrative unit of Colombia rather than a sovereign or quasi-sovereign polity: Colombia has held continuous national sovereignty over the territory throughout the entry's span, and the department exists in this database only because Colombia's national-level rows (COL-1830-1903, COL-1903-1922, COL-1922-2025) do not carry department-level detail that some other WHEP data sources report at. The entry begins in 1886, when the 1886 Constitution dissolved the federal-era Estado Soberano del Tolima and reconstituted it as a department of the newly unitary Republic of Colombia; it runs to the present (end_year 2025 per this batch's open-ended convention for departments that have not been abolished, split, or renamed). Tolima is one of Colombia's original 1886-vintage departments — it is not among the departments created later by subdivision of a larger unit (such as several eastern-plains departments carved out much more recently) — so the default start-year rule of "start at the 1886 Constitution" applies rather than a later founding date tied to a specific creation law.

**Why this entry exists.** This entry was created to give Colombia's department of Tolima its own subnational polity row, distinct from the national COL chain (COL-1830-1903, COL-1903-1922, COL-1922-2025). The routing decision reports no existing WHEP polity currently represents Tolima at department granularity; data referencing Tolima by name would previously have had nowhere to route except the national COL rows, which cover the entire country and would silently blend department-level statistics into a territory roughly 55 times larger. The routing decision itself does not cite a specific input dataset (row count, source name) that motivated this particular creation — it argues from general administrative-history knowledge that Tolima is one of Colombia's original 1886 departments and therefore should exist as its own row under the country's default `start_year = founding constitution` rule, applied here in a batch alongside many other Colombian departments (col-antioquia, col-cesar, col-cundinamarca, etc., visible as sibling untracked files in this same batch). What confirms Tolima as a distinct administrative entity, rather than an artefact of this batch process, is straightforward constitutional history: Tolima was one of the nine sovereign states of the federal 1863-1886 United States of Colombia (Estado Soberano del Tolima) and was carried forward as a named department by the 1886 Constitution's Título XVIII, a status it retains without interruption or renaming to the present day — the same kind of long, unbroken, separately-named administrative existence that justifies the other Colombian department entries in this batch.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is attached in the GeoPackage for this entry (`polygon_status: unassigned`). The routing decision identified `gadm-4.1-adm1` as the correct registered source — GADM's global admin-1 layer already digitises Colombian departments — but the copy of that source fetched into this repository's local GeoPackage is a curated 81-country subset that does not include Colombia, so no specific feature ID can be attached today. `polygon_source` is therefore set to the registered slug `gadm-4.1-adm1` itself (this is a `registered_source_unfetched` situation: the source exists and is named, it simply has not been pulled for this country), not to a placeholder or route-name value. Re-fetching GADM 4.1 adm1 for Colombia (or fetching the global release rather than the 81-country subset) would supply the missing feature directly.

**Territory description:** Tolima department covers roughly 23,600 km² of central Colombia in the upper and middle Magdalena valley, bounded by the Cordillera Central to the west (including the Nevado del Tolima volcano) and the Cordillera Oriental to the east, with the Magdalena River running through its length. Its capital, Ibagué, sits roughly 200 km southwest of Bogotá. This ~23,600 km² figure comes from present-day published department-area references (e.g. DANE/general reference works on Colombian departments), not from any polygon attached to this entry — no geometry has been measured for this record, since none is yet attached. The department's boundaries have been broadly stable since the 1886 reorganisation, though this has not been independently verified against 19th-century state boundaries for the Estado Soberano del Tolima, which is noted as an open question below.

## Predecessors and successors

Tolima has no predecessor or successor polity row in this database: it is not a split, merger, or renaming of another entry, but the direct continuation of a pre-existing territorial unit (the Estado Soberano del Tolima) into department status. Under the federal 1863 Rionegro constitution Tolima was one of the nine sovereign states of the United States of Colombia; the 1886 Constitution abolished the federal states and reorganised the country into centrally-administered departments, converting the former state directly into the Department of Tolima with essentially the same territory. No prior WHEP polity row represents the federal-era Estado Soberano del Tolima, so this entry's start_year of 1886 marks the department's formal constitutional status rather than the territory's first appearance as a distinct administrative unit; that federal-era gap is noted as an open question below. Tolima has not been dissolved, split, or renamed since 1886 and remains a functioning department of Colombia today, so end_year is left open at 2025 per the country convention used for all currently-existing COL departments in this batch.

## Sourced claims

- Tolima was created as a department of Colombia directly by the 1886 Constitution, which abolished the federal Estados Soberanos (including the Estado Soberano del Tolima) and reorganised the country into a unitary republic with centrally-administered departments (Constitución Política de Colombia, 1886, Título XVIII).
- GADM 4.1's administrative level 1 (adm1) layer digitises Colombia's current departments, including Tolima, as polygon features; the locally-fetched WHEP copy of gadm-4.1-adm1 is a curated 81-country subset that excludes Colombia, so the Tolima feature exists in the upstream GADM release but has not yet been fetched into this repository's GeoPackage.

## Decisions

### d-country-precedent

**No existing COL subnational precedent, so ISO3-SUBUNIT pattern chosen by analogy**

COL has zero existing subnational rows, so there is no in-country precedent to follow. Tolima is an ordinary first-order administrative department with no distinct historical name of its own (unlike ALK, HYD, RYU), so the dominant cross-country pattern <ISO3>-<SUBUNIT>-<start>-<end> applies rather than a bespoke code. SUBUNIT is set to 'tolima' (matching the informal abbreviation style already used for other Latin American department codes such as col-antioquia, col-cesar elsewhere in this batch) to keep the code readable and collision-free with the national COL codes.

### d-container-tiling

**Three container edges needed to tile 1886-2025, not one**

The routing decision proposed only container_code COL-1922-2025 with start_year 1886, which would leave 1886-1922 uncontained and violate the containment gate (an edge cannot fall outside either party's span). The polity table shows COL was COL-1830-1903 (national), COL-1903-1922 (national), and COL-1922-2025 (national) across this range. Tolima's span therefore needed three container edges, one per containing era: COL-1830-1903 for 1886-1903, COL-1903-1922 for 1903-1922, and COL-1922-2025 for 1922-2025, each with its own basis referencing the department's continuous existence under the successive national administrations.

### d-polygon-source-slug

**polygon_source set to the registered slug, not the route name**

The routing decision's polygon_route is registered_source_unfetched with polygon_source already correctly given as the registered slug gadm-4.1-adm1 (not a route name like 'new_source_needed'). Per the task instructions, when the route is registered_source_unfetched the slug IS the polygon_source and polygon_status must be 'unassigned' (not 'proxy' or 'assigned'), since no feature has actually been fetched or attached yet. polygon_feature_id is left null because no specific GADM feature has been identified for Tolima locally.

## Open questions

### oq-federal-era-gap

**Should Tolima's start year reach back before 1886 to the federal-era Estado Soberano del Tolima?**

This entry starts at 1886 (formal department status under the unitary Constitution), but Tolima existed as a sovereign federal state (Estado Soberano del Tolima) from at least 1861/1863 under the Confederación Granadina / United States of Colombia. If any WHEP data source reports statistics for 'Tolima' or the broader federal state it was drawn from (it was itself formed by merging earlier provinces) before 1886, those rows have no home in this database: the national COL-1830-1903 row exists but a pre-1886 Tolima-labelled row does not. Confirming whether any routed data actually needs a pre-1886 Tolima entry, and if so what its exact predecessor state and territory were, is unresolved.

### oq-gadm-fetch

**When will gadm-4.1-adm1 actually be fetched for Colombia, and does the modern boundary match the historical one?**

polygon_status is unassigned because the local GADM 4.1 adm1 copy excludes Colombia entirely. Beyond simply fetching the missing country, it is unverified whether Tolima's current department boundary (used once fetched) matches its historical extent across the full 1886-2025 span — Colombian departments have had minor boundary adjustments and Tolima itself lost territory in some 20th-century administrative reorganisations of neighbouring departments (e.g. the creation/adjustment of Huila and Quindío, which bordered Tolima). Whether a single modern GADM feature is an adequate proxy for the whole span or whether an earlier-vintage boundary is needed is not yet assessed.
