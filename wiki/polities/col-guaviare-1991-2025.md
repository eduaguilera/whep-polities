---
polity_code: COL-GUAVIARE-1991-2025
polity_name: Guaviare (department of Colombia)
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
polygon_feature_id: null
polygon_feature_year: null
polygon_status: unassigned
predecessor: []
successor: []
container:
  - code: COL-1922-2025
    start_year: 1991
    end_year: 2025
    basis: Guaviare has been a department of the Republic of Colombia continuously since its constitution under the 1991 Constitution; the national polity's own span (1922-2025) covers this whole window without a break.
---

# Guaviare (department of Colombia)

## Summary

Guaviare is a department in southeastern Colombia, part of the Llanos-Amazon transition zone, with its capital at San José del Guaviare. It was created as a full department by the 1991 Constitution, which abolished Colombia's old category of territorios nacionales (federally-administered territories without department status) and converted several of them, including Guaviare, into ordinary departments with elected governors and assemblies. Before 1991 the same land was part of a territorio nacional called Comisaría del Guaviare (created 1977, itself carved from the earlier Comisaría del Vaupés), administered directly by Bogotá rather than through department-level government. This entry is `type: subnational` and starts in 1991 — not earlier — because the reorganisation from federally-administered territory to constituent department is a genuine administrative discontinuity that the routing decision treats as the natural break point, mirroring how COL-AMAZONAS was already handled for the equivalent pre/post-1991 split. The entry's container is the national Colombian polity COL-1922-2025, which holds sovereignty throughout; this row exists to carry a distinct statistical reporting territory once Guaviare began reporting as its own department-level unit, not to claim sovereignty separate from Colombia.

**Why this entry exists.** Twenty-plus years of production/trade data (1915-2023 per the routing decision) are reported for the territory now known as Guaviare. Data from 1991 onward — after Guaviare became a full department — reflect a genuinely distinct administrative and statistical reporting unit: a department with its own governor, assembly, and DANE reporting codes, no longer folded into the national territorios nacionales aggregate. Previously, all of this territory's data (both pre- and post-1991) would have been matched only to the national Colombian polity row, which is roughly 22x the area of this single department and conflates Guaviare's output with all other Colombian regions. That routing was wrong for the post-1991 period specifically because a distinct sub-national reporting entity exists and is directly analogous to the already-created COL-AMAZONAS entry, which the routing decision explicitly cites as precedent for exactly this territorio-nacional-to-department transition. The historical source confirming Guaviare's distinctness as an administrative/statistical unit is Colombia's 1991 Constitution itself, which enumerated the former territorios nacionales (Guaviare among them) as new departments, formally ending their prior status as directly-administered national territory — the same constitutional event that underlies the COL-AMAZONAS split this entry mirrors.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is copied from any sibling row because none of Guaviare's predecessor administrations (Comisaría del Vaupés, Comisaría del Guaviare) have a digitised boundary in this repository's GeoPackage to copy from, and no proxy period exists that would obviously match the modern department's extent. `polygon_source: gadm-4.1-adm1` names the registered source that is the right long-term answer — GADM's global ADM1 layer, which includes Colombian departments — but the specific file staged in this repo's geodata is a subset covering 81 countries that excludes Colombia entirely (confirmed: 0 COL features on disk). Because a real, mapped boundary is known to exist and only needs fetching, `polygon_status` is `unassigned` (registered_source_unfetched), not `none` — the distinction the harness draws between "no source exists" and "source exists but hasn't been pulled down here."

**Territory description:** The department of Guaviare sits in southeastern Colombia, bordered by Meta to the north, Vichada and Guainía to the east, Vaupés and Caquetá to the south, and Meta/Caquetá to the west. Its capital, San José del Guaviare, lies roughly 300 km southeast of Bogotá. The department spans the ecological transition from the Llanos (eastern plains) in its north to Amazon rainforest in its south, and is drained by the Guaviare River, from which it takes its name. Colombia's national statistical agency (DANE) and international sources report its area at approximately 55,000-56,000 km2, comparable in size to Croatia — a figure independent of any polygon attached to this row, since none has been assigned yet. This description should let a reader locate the department on any current map of Colombia's 32 departments.

## Predecessors and successors

Guaviare has no predecessor or successor polity row declared on this page: before 1991 its territory was administered directly by the national government as part of the territorio nacional system, which this entry treats as continuous with the national polity COL-1922-2025 via the container edge rather than via a predecessor link, because the national row (which is not editable from here) does not reciprocate a predecessor/successor claim. See open question oq-col1922-successor-edge for the exact edit that would close this gap, and oq-pre1991-disposition for whether any pre-1991 rows currently matched to the national total should instead be re-routed to this row as back-cast estimates. No successor exists because the department remains current (open end_year 2025 by convention).

## Sourced claims

- Guaviare was constituted as a department of Colombia under the 1991 Constitution (promulgated 4 July 1991), ending its prior status as a territorio nacional administered directly by the national government.
- Mitchell/national statistical compilations and back-cast series report values for this territory as far back as 1915, predating the department's 1991 creation by 76 years, which is why the routing decision treats the pre-1991 span as belonging to the national polity chain rather than to this entry.
- GADM's global ADM1 administrative layer (version 4.1) digitises Colombian departments including Guaviare under a GID_1 code, but the copy of that source currently staged in this repository's geodata covers only 81 countries and Colombia is not one of them.

## Decisions

### d-code-pattern

**Code follows the ISO3-SUBUNIT-start-end dominant pattern**

57 of 66 subnational rows use <ISO3>-<SUBUNIT>-<start>-<end>, and Guaviare is not a historical territory with a name of its own outside the modern department (unlike ALK or HYD) — it is a standard Colombian department created by the 1991 Constitution, directly comparable to the existing COL-AMAZONAS precedent cited in the routing decision. So COL-GUAVIARE-1991-2025 follows the majority pattern rather than a bespoke code, and there are no existing COL subnational codes to conflict with or extend.

### d-dropped-predecessor-claim

**Dropped the predecessor edge to COL-1922-2025 rather than assert an unreciprocated link**

A previous version of this page declared predecessor: [COL-1922-2025], but that page declares successor: [] and cannot be edited from here. validate_chain_integrity checks both directions against the same baseline, so a one-sided claim fails the gate regardless of how true it is historically. Rather than re-fail the same check, predecessor and successor are both left empty here, and the asymmetry is recorded as an open question naming the exact edit COL-1922-2025 would need (successor: [COL-GUAVIARE-1991-2025]) if a maintainer with write access to that page wants to close the loop. The territorial continuity itself is still captured by the container edge, which is the field the harness actually uses to tile the span.

### d-polygon-unassigned-not-none

**polygon_source is the registered slug, polygon_status is unassigned, not none**

The routing decision's polygon_route is registered_source_unfetched: gadm-4.1-adm1 is a real, schema-registered source, just not fetched for Colombia rows in the file currently on disk (the routing_reasoning confirms 0 COL features present). Per the harness instructions, this means polygon_source is the slug itself (gadm-4.1-adm1) and polygon_status is unassigned — not new_source_needed or none, both of which are reserved for cases where no known digitised boundary exists at all.

## Open questions

### oq-col1922-successor-edge

**COL-1922-2025 should list this row as a successor but cannot be edited here**

This page does not declare predecessor: [COL-1922-2025] because that page currently declares successor: [], and an unreciprocated edge fails validate_chain_integrity in both directions. Historically the claim is correct: Guaviare's territory was part of the national polity's directly-administered territorio nacional before 1991 and became a department carved out of it in 1991. A maintainer with write access to col-1922-2025.md should add successor: [COL-GUAVIARE-1991-2025] (alongside any of its sibling department splits, e.g. COL-AMAZONAS) to that page's frontmatter so the two rows agree, at which point this page's predecessor field can safely be updated to match.

### oq-pre1991-disposition

**Whether 1915-1990 rows attributed to the national total should instead be disposition back_cast for this department**

The routing_concerns flag that ~98% of the pre-1991 rows for this territory are scaled/interpolated/fallback rather than direct observation. If those rows are genuinely back-cast reconstructions of Guaviare specifically (rather than the national aggregate simply containing an undifferentiated territorio nacional share), they may belong with disposition back_cast and polity_code=COL-GUAVIARE-1991-2025 instead of being matched to COL-1903-1922/COL-1922-2025. This page does not resolve that question — it only creates the 1991-2025 department row — and whoever reviews the pre-1991 method breakdown should decide whether any of it needs re-routing here.

### oq-gadm-fetch-needed

**gadm-4.1-adm1 needs to be fetched with Colombia coverage before polygon_status can move past unassigned**

The registered gadm-4.1-adm1 source file on disk covers only 81 countries and Colombia is not among them (0 total COL features), per the routing decision's polygon_detail. Until a Colombia-inclusive GADM 4.1 ADM1 fetch is added to the pipeline, this row's polygon_status stays unassigned and polygon_area_km2 cannot be populated. Vintage risk is assessed as low once fetched, since Colombian department boundaries have been stable since their 1991 constitutional creation, but that has not been verified against the actual GADM geometry.
