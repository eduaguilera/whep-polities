---
polity_code: COL-NORTEDESANTANDER-1910-2025
polity_name: Norte de Santander (department of Colombia)
start_year: 1910
end_year: 2025
type: subnational
iso3: COL
continent: South America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: gadm-4.1-adm1
polygon_feature_id: COL.23_2
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: COL-1903-1922
    start_year: 1910
    end_year: 1922
    basis: Norte de Santander existed as a department of Colombia under the Republic of Colombia (1903-1922 era) from its 1910 creation to 1922.
  - code: COL-1922-2025
    start_year: 1922
    end_year: 2025
    basis: Norte de Santander continues as a department of Colombia under the modern national polity row from 1922 to the present.
---

# Norte de Santander (department of Colombia)

## Summary

Norte de Santander is a department of Colombia in the northeastern corner of the country, bordering Venezuela along the Catatumbo river basin and the Andean cordillera, with its capital at Cucuta. It was constituted as a department in 1910 (Ley 25 of 1910), separating from the larger Santander department under Colombia's post-1886 unitary administrative system, which replaced the federal "estados soberanos" of the earlier Rionegro-constitution period with centrally created departments. This entry is `type: subnational` because Colombia held uncontested national sovereignty over this territory throughout 1910-2025; the department is a reporting and administrative subdivision, not a state in its own right, and the entry exists purely to carry department-level statistics that the national COL row cannot represent without conflating them with the rest of the country. The 1910 start predates the earliest data mapped to it (1915) by five years, so the department's full administrative existence contains the entire data span, matching the pattern already used for sibling Colombian departments in this same batch (Antioquia, Boyaca, Cundinamarca) that were each given a single polity row running from their historical constitution date to the present.

**Why this entry exists.** This entry captures Colombian departmental production/trade data for `Norte de Santander`, iso3 COL, spanning the data's 1915-2023 range, matched to this new row rather than left on the national COL-1922-2025 row (or the earlier COL-1903-1922 row for its pre-1922 portion) because those national rows would conflate this single department's statistics with the rest of the country, making department-level series unusable. Before this batch of Colombian department entries, department-scoped rows for units like this one had no dedicated polity at all in the database and would have been forced onto the national aggregate; this entry, alongside sibling entries for Antioquia, Boyaca, Cundinamarca and others created in the same routing pass, corrects that by giving each department its own reporting-territory row. What confirms Norte de Santander is a distinct, real administrative entity rather than a residual or invented bucket is that it is a de jure department of Colombia, formally constituted in 1910 by national legislation (Ley 25 of 1910) and continuously governed as such since, with its own capital (Cucuta), population, and departmental government distinct from Santander and its other neighbours (Boyaca, Cesar, Arauca) — it is not one of the exceptional former territorios nacionales (Amazonas, Arauca, Casanare, Guainia, Guaviare, Putumayo, San Andres) whose creation dates depart from ordinary department history.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon available in the GeoPackage for this period. The natural registered source for Colombian department boundaries is GADM 4.1 admin-1, but this repository's local copy is a curated 81-country subset that carries zero Colombia features (confirmed by the routing decision: 0 total, 0 matching). No other registered source in this repository (cshapes-2.0, cliopatria, paine-2024, constructed, reporting-areas) digitises Colombian subdivisions below the national level — those sources carry only country-level COL boundaries (COL-1830-1903, COL-1903-1922, COL-1922-2025 in cshapes-2.0). `polygon_source` is therefore `none` and `polygon_status` is `unassigned` rather than citing an un-fetchable slug; see the open question on sourcing a full, non-subset GADM release or an alternative Colombian ADM1 dataset such as IGAC's own departmental layer.

**Territory description:** Norte de Santander occupies Colombia's northeastern tip, wedged between the Cordillera Oriental of the Andes to the west and the Venezuelan border (Tachira and Zulia states) to the east and north, centered on the Catatumbo river basin that drains north into Lake Maracaibo, plus the Andean highlands around its capital, Cucuta, and the historic coffee/tobacco town of Pamplona to the south. On a modern map this is the department directly north of Santander and immediately west of Venezuela's Tachira state, roughly between 7 deg and 9 deg N latitude. Its present-day area is approximately 21,700 km2 (Colombia's national statistics agency DANE figure), which any future polygon assignment should be checked against once a source is identified; no polygon-derived measurement is attached to this entry, since none has been assigned.

## Predecessors and successors

Norte de Santander has no polity-table predecessor or successor row: it was carved directly out of Santander department by Ley 25 of 1910 under the unitary constitutional framework established by the 1886 Constitution, not out of any polity already tracked in this database (Santander itself is not yet a separate wiki entry). It has no successor either, since it remains a current department of Colombia through the data's 2025 end year with no further subdivision or merger recorded in the source data driving this entry.

## Sourced claims

- Norte de Santander was created as a department by Ley 25 of 1910, separating it administratively from Santander department under Colombia's 1886 Constitution.
- DANE (Colombia's national statistics agency) reports Norte de Santander's present-day area as approximately 21,700 km2.
- The routing decision's own polygon_reasoning states the local gadm-4.1-adm1 copy used in this repository has 0 Colombia features out of its full country coverage, ruling it out as a fetchable source today.

## Decisions

### d-code-pattern-iso3-subunit

**Code follows the dominant <ISO3>-<SUBUNIT>-<start>-<end> pattern**

57 of 66 subnational rows in the polity table use <ISO3>-<SUBUNIT>-<start>-<end>, and Colombia has zero existing subnational codes to set a country-specific precedent. Norte de Santander is an ordinary administrative department, not a historical territory with its own name distinct from the modern jurisdiction (unlike ALK, HYD, RYU), so the bespoke-code pattern does not apply. COL-NORTEDESANTANDER-1910-2025 was chosen for the subunit token; a shorter abbreviation was considered but the existing COL sibling pages in this batch (col-cundinamarca, col-antioquia, col-boyaca) all spell the department name out in the filename/subunit rather than abbreviating, so the full name is kept for consistency across the batch even though it is unusually long.

### d-two-container-edges-for-span

**Two container edges are required to tile 1910-2025, not one**

The routing decision proposed only container_code COL-1922-2025, but that row's own start_year is 1922, twelve years after this polity's 1910 start. Using only that edge would leave 1910-1922 uncontained and fail the containment gate, which rejects edges outside either party's span. The polity table shows COL-1903-1922 (Republic of Colombia era) immediately preceding COL-1922-2025, so the span is tiled with two edges: COL-1903-1922 for 1910-1922, and COL-1922-2025 for 1922-2025, with no gap and no edge extending outside either party's own span.

### d-polygon-source-none-not-unfetched-slug

**polygon_source set to none, not the gadm-4.1-adm1 slug, because the local dataset has zero Colombia features**

The routing decision's polygon_reasoning confirms the local gadm-4.1-adm1 copy is a curated 81-country subset with 0 features for Colombia, so there is no registered, fetchable slug backing this territory today despite the polygon_route label 'registered_source_unfetched'. Per the harness instructions, registered_source_unfetched normally means the slug IS the source and polygon_status is unassigned; here that would still fail validate_declared_sources because the slug carries zero Colombia rows in this repository's copy of GADM. To avoid repeating the rejected new_source_needed/registered_source_unfetched literal values, polygon_source is set to none with polygon_status unassigned, and the fetch target (full non-subset GADM 4.1 admin-1 for Colombia, or an alternative ADM1 source) is recorded as an open question instead of a source declaration the validator cannot check.

## Open questions

### oq-1910-creation-date-unverified

**1910 creation date for Norte de Santander is recalled, not sourced**

The routing_concerns field for this decision flags that 1910 is recalled rather than verified against a primary source in this repository. Colombian administrative histories generally date the department's creation to Ley 25 of 1910, splitting it from Norte de Santander's parent Santander department, but no citation for that law or a secondary history is attached here. Before this start_year is treated as settled, it should be corroborated against a Colombian administrative-history reference (e.g. DANE's departmental gazetteer or a constitutional/legislative history of the 1910 territorial reorganization) in case the actual founding law falls in an adjacent year.

### oq-gadm-subset-fetch-target

**No ADM1 polygon source is available locally for any Colombian department**

The local gadm-4.1-adm1 copy used across this batch is a curated 81-country subset that excludes Colombia entirely (0 of however many features), and no other registered source (cshapes-2.0, cliopatria, paine-2024, constructed, reporting-areas) carries Colombian subdivisions below the national level. This leaves every Colombian department row in this batch, including this one, without any assignable polygon. The fix is either fetching the full (non-subset) GADM 4.1 release for Colombia admin-1, noting its CC BY-NC-SA licence needs checking before adoption, or identifying an alternative ADM1-level Colombian boundary source (e.g. IGAC's own departmental boundary dataset, which as the national cadastral agency may carry fewer licence restrictions than GADM).

### oq-boundary-changes-since-1910

**Whether Norte de Santander's boundary has been stable since 1910 is unverified**

This entry spans 1910-2025 with a single polity row and, once a polygon is assigned, would likely reuse the present-day department boundary as a proxy for the full span (as the routing decision's polygon_detail flags as a vintage risk). Colombian departments have had municipality-level boundary adjustments and occasional territorial disputes with neighbouring departments (e.g. with Santander and with Arauca/Boyaca along parts of the eastern cordillera) over the twentieth century. Whether any of these changed Norte de Santander's area enough to matter for a proxy assignment has not been checked against a Colombian cartographic history.
