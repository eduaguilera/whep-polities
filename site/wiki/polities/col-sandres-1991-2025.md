---
polity_code: COL-SANDRES-1991-2025
polity_name: San Andrés y Providencia (department of Colombia)
start_year: 1991
end_year: 2025
type: subnational
iso3: COL
continent: South America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: gadm-4.1-adm1
polygon_feature_id: COL.27_1
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: COL-1922-2025
    start_year: 1991
    end_year: 2025
    basis: San Andrés y Providencia was a national intendencia/territory of Colombia before 1991; the 1991 Constitution elevated it to a full department while it remained part of the Colombian national territory throughout, so the containing national row is unchanged across the transition.
---

# San Andrés y Providencia (department of Colombia)

## Summary

San Andrés y Providencia is the Colombian department comprising the Caribbean islands of San Andrés, Providencia and Santa Catalina, together with a scatter of surrounding cays and reefs, located roughly 700-800 km northwest of mainland Colombia and much closer to the coasts of Nicaragua and Panama than to the Colombian coast. This entry is typed `subnational` rather than `national` because Colombia held sovereignty over the archipelago throughout the entry's span; the row exists to carry a reporting/administrative territory below the national level, not a competing claim to sovereignty. Before 1991 the archipelago was governed as a national intendencia (a territory administered directly by the central government rather than by an elected departmental government), a status it shared with several other peripheral Colombian territories such as Casanare, Guaviare, Vaupés, Vichada, Guainía, Amazonas, Putumayo and Arauca. Colombia's 1991 Constitution converted these national intendencias and comisarías into ordinary departments, giving each an elected governor and departmental assembly with the same institutional standing as the older, pre-existing departments. This entry begins in 1991 to mark that institutional promotion and runs to 2025 as the department remains current. It is contained by COL-1922-2025 (the modern Colombian national state) for its full span, since the department-level reorganization did not change Colombia's national boundaries or its identity as the containing sovereign state — only the internal administrative status of this particular unit changed.

**Why this entry exists.** This entry captures data for the unit identified in the routing pipeline as COL-SANANDRESYPROVIDEN ("San Andrés y Providencia", Colombia, iso3 COL), a department-level administrative reporting unit. Before this decision, rows for this unit spanning 1915-2023 risked being matched wholesale to the national container COL-1922-2025, which would have (a) duplicated claims already examined and rejected for sibling former-territorio-nacional units like Casanare and Guaviare on the same years, and (b) obscured that department-level (post-1991) reporting for this archipelago is a genuinely distinct administrative regime from the earlier national-intendencia era, during which the routing analysis found the associated data to be 98.7% non-observed (heavily interpolated, scaled, or fallback-derived rather than directly reported) — evidence that the pre-1991 figures for this territory are being reconstructed onto a department that did not yet exist in that form, rather than being genuine department-era observations. What confirms San Andrés y Providencia is a distinct reporting/administrative entity, separate from the pre-1991 national-intendencia era and from the national COL container, is Colombia's own enumerated departure list of the 1991 Constitution's conversions of national territories into departments (paralleling Casanare, Guaviare, Vaupés, Vichada, Guainía, Amazonas, Putumayo and Arauca, several of which already have their own polity rows in this same country following the identical institutional transition), which is the country-specific convention this pipeline's routing step applies. Only the 1991-2025 department-era span is created as `create_new` here; the pre-1991 intendencia-era rows for the same territory remain an open question (see oq-pre1991-data-routing) rather than being folded into this entry.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is currently available in the GeoPackage for this unit: the registered source `gadm-4.1-adm1` (GADM 4.1 admin-level-1 polygons, the standard first-order administrative boundary source used elsewhere in this database for department-level Colombian units) is the correct source in principle, but the copy of that layer present at `data/geodata/gadm-4.1/gadm41_adm1.gpkg` is a curated subset covering only 81 countries, and Colombia is not among them (a query for COL returns 0 features). Because the source is identified and registered, but simply not fetched for this country, `polygon_status` is `unassigned` and `polygon_source` is recorded as the registered slug `gadm-4.1-adm1` itself rather than `none` — per this pipeline's rule that `registered_source_unfetched` routes keep the slug as the declared source. No other registered source in this repository (cshapes-2.0, cliopatria, paine-2024, histogis-1860-habsburg, constructed, reporting-areas) operates at department level for Colombia or could be unioned/differenced to approximate this archipelago's boundary. `polygon_feature_id` and `polygon_area_km2` are therefore left null; no measured-geometry figure is attached to this entry.

**Territory description:** San Andrés y Providencia is Colombia's smallest department by land area, made up of the islands of San Andrés (the largest and most populous, roughly 26 km2), Providencia and Santa Catalina (together roughly 20 km2), plus a number of small, mostly uninhabited cays and reefs (Roncador, Serrana, Quitasueño, Serranilla, Bajo Nuevo, Alburquerque, East-Southeast Cays) scattered across a much larger stretch of the western Caribbean Sea. The islands sit roughly 700-800 km northwest of the Colombian mainland, and are considerably closer to the coasts of Nicaragua (about 230 km) and Panama than to continental Colombia — a geography that has made the department's maritime boundary the subject of the long-running Colombia-Nicaragua dispute before the International Court of Justice. Total emerged land area is on the order of 50-55 km2, small enough that any GADM department polygon obtained for this unit should be checked for whether it represents land area only or includes a much larger maritime/EEZ buffer, since a naive area reading of a "department" polygon here could be off by several orders of magnitude if it silently includes surrounding sea.

## Predecessors and successors

No predecessor polity code is set: the routing decision explicitly treats 1915-1990 territorio-nacional-era data for this unit as belonging elsewhere (back-cast rather than matched to a distinct pre-1991 polity of this same archipelago), so linking a predecessor here would be presumptive pending resolution of open question oq-pre1991-data-routing. No successor is set because the department is current (end_year 2025, matching the container's own open end date) and has not been superseded.

## Sourced claims

- San Andrés, Providencia and Santa Catalina were governed as the Intendencia Nacional de San Andrés y Providencia (a national territory administered directly from Bogotá, not by an elected departmental government) prior to the 1991 Constitution.
- The Political Constitution of Colombia of 1991 (Constitución Política de Colombia, 1991) converted the former national intendencias and comisarías, including San Andrés y Providencia, Casanare, Arauca, Putumayo, Guainía, Guaviare, Vaupés, Vichada and Amazonas, into full departments with elected governors and departmental assemblies.
- San Andrés y Providencia is Colombia's smallest department by land area, consisting of the islands of San Andrés, Providencia and Santa Catalina plus surrounding cays in the western Caribbean Sea, roughly 700-800 km northwest of the Colombian mainland and closer to the coasts of Nicaragua and Panama.

## Decisions

### d-code-pattern

**Followed the dominant COL subnational naming pattern**

Colombia has no existing subnational rows, so this entry sets the country's precedent. I used <ISO3>-<SUBUNIT>-<start>-<end>, matching the pattern used by 57 of 66 existing subnational rows (e.g. ESP-AS-1833-2025, DZA-CVD-1902-1919), rather than a bespoke code. San Andrés y Providencia is a standard department created by administrative reorganization under a constitution, not a historical territory with a name of its own comparable to Alaska Territory or Hyderabad, so the bespoke pattern (3 of 66 rows) does not apply. I abbreviated the subunit to SANDRES to keep the code compact and unambiguous against other Colombian departments, since 'SANANDRESYPROVIDENCIA' would be unwieldy and no gate specifies subunit-code length.

### d-start-year-1991

**Start year set to 1991, matching the routing decision's proposed span**

The routing decision specifies start_year 1991 based on the 1991 Constitution elevating San Andrés y Providencia from national intendencia/territory to department. I did not independently re-verify the exact constitutional date beyond the routing decision's own stated concern that this should be checked against a primary source; I flag that unresolved as an open question rather than silently asserting certainty the routing reasoning itself disclaimed.

### d-polygon-source-slug

**polygon_source set to the registered slug gadm-4.1-adm1, not the route name**

The routing decision's polygon_route is registered_source_unfetched with polygon_source already stated as gadm-4.1-adm1 and polygon_feature_id empty. Per the authoring instructions, when the route is registered_source_unfetched the slug itself is the valid polygon_source and polygon_status must be 'unassigned' (not 'assigned' or 'proxy'), since the GADM 4.1 ADM1 layer at data/geodata/gadm-4.1/gadm41_adm1.gpkg does not currently include Colombia (0 features returned for COL per the routing_reasoning).

## Open questions

### oq-1991-date-verification

**Exact date San Andrés y Providencia became a department needs primary-source confirmation**

The routing decision itself flagged this as unverified: the 1991 start_year rests on general historical recollection that the 1991 Political Constitution of Colombia elevated San Andrés y Providencia from intendencia/national territory status to department status, alongside other former territorios nacionales such as Casanare, Guaviare, Vaupés, Vichada, Guainía, Amazonas, Putumayo and Arauca. A primary source (the constitutional text, Colombia's Registraduría, or DANE's administrative history) should be checked for the exact article and effective date, since some of these transitions took effect at Constitution promulgation (July 1991) while others were phased through subsequent organic law. If the actual date differs from 1991, both this entry's start_year and the years embedded in its polity code would need to change together, per the gate that checks code years against frontmatter years.

### oq-pre1991-data-routing

**Where the 98.7% non-observed pre-1991 data for this unit actually lands is not documented here**

The routing_reasoning states that COL-SANANDRESYPROVIDEN data for 1915-1990 is heavily interpolated/scaled/fallback (98.7% non-observed) and should NOT be matched to the national container to avoid duplicating claims already rejected for sibling units on the same years, implying it should instead back-cast onto this new department polity despite this polity's own start_year being 1991. This page does not itself resolve whether that back-cast is implemented via predecessor/successor linkage, an imputed_share flag, or a separate constant-territory reallocation step, since no predecessor code exists for San Andrés y Providencia before 1991 (predecessor is empty here). Whether pre-1991 rows should attach to this code with an imputed flag, or whether a distinct pre-1991 territorio-nacional-era polity should be created to hold them, is unresolved and should be checked against how the sibling units (Casanare, Guaviare) handled the same situation.

### oq-gadm-fetch-status

**GADM 4.1 ADM1 Colombia layer is not yet fetched; polygon remains unassigned**

data/geodata/gadm-4.1/gadm41_adm1.gpkg is a curated 81-country subset that does not include Colombia, so this entry has no polygon_feature_id and polygon_status is 'unassigned' rather than 'assigned'. Whoever fetches the full or Colombia-specific GADM 4.1 ADM1 layer should look up the GID_1 for San Andrés y Providencia (expected to be a small archipelago polygon of roughly 52 km2 of land, though GADM department boundaries for island territories sometimes include large maritime/EEZ buffers that would inflate a naive area reading) and populate polygon_feature_id, moving the route to registered_source_feature.
