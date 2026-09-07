---
polity_code: COL-MAGDALENA-1915-2025
polity_name: Magdalena (department of Colombia)
start_year: 1915
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
  - code: COL-1903-1922
    start_year: 1915
    end_year: 1922
    basis: Magdalena was already a constituted department of the unitary Republic of Colombia during the 1903-1922 national era (bounded by Panama's 1903 secession and the 1922 US-Colombia treaty ratification), and the data span begins in 1915 within that era
  - code: COL-1922-2025
    start_year: 1922
    end_year: 2025
    basis: Magdalena continues as a current department of Colombia within the modern national row, open-ended (end_year 2025) as the still-current polity, matching sibling entries such as COL-ANTIOQUIA-1886-2025 and COL-BOYACA-1886-2025
---

# Magdalena (department of Colombia)

## Summary

Magdalena is a Colombian department on the Caribbean coast, capital Santa Marta, constituted under the centralizing 1886 Constitution that replaced the earlier federal Estados Unidos de Colombia. This entry is `type: subnational` because Colombia held sovereignty throughout 1915-2025 — Magdalena never functioned as a sovereign state in this window — but it is nonetheless a distinct administrative and statistical reporting unit that trade and production series are tabulated against separately from national Colombia totals. The row exists to carry that department-level reporting territory rather than to compete with the national COL chain for sovereignty ranking. `start_year` is set to 1915 (the pipeline's proposed span) rather than 1886, since that is where the routed data begins and no evidence here narrows the department's own administrative history earlier than the country convention default; `end_year` uses the open convention (2025, exclusive) applied to still-current subnational units across this table, mirroring COL-ANTIOQUIA-1886-2025, COL-BOYACA-1886-2025, COL-ATL-1910-2025 and other Colombian department siblings created in the same pass.

**Why this entry exists.** Country data labelled with a Magdalena-specific admin name, spanning 1915-2023, was previously matched only to the national COL-* rows (COL-1903-1922 or COL-1922-2025 depending on year) — national totals for the whole of Colombia (~1,141,748 km2), roughly 49 times Magdalena's own present-day area (~23,188 km2). No existing polity in the table IS Magdalena specifically: the four COL-* rows are successive national eras (Gran Colombia to 1830, Colombia to 1903, 1903-1922, 1922-2025) and none represents the department alone, so match_existing was rejected in the routing decision. Magdalena's status as a distinct, long-standing administrative unit is confirmed by Colombia's own constitutional and administrative history: it is one of the historic departments (not one of the territorios nacionales only elevated to department status starting in 1991, per the country departure-list convention), with continuous departmental government and its own DANE statistical reporting distinct from national totals — the same reasoning already applied to sibling departments Antioquia, Atlántico, Bolívar, Boyacá, Caldas, Cauca and Cundinamarca resolved to create_new in the same pipeline pass for the identical reason: a reporting unit smaller than the national total, with no existing polity representing it.

## Territorial extent

**Polygon:** `polygon_status: unassigned`. The routing decision for this unit proposed `new_source_needed`, but that route is not a valid `polygon_source` value here — the correct registered slug for this class of unit is `gadm-4.1-adm1`, the same source family already used for Antioquia, Boyacá and other Colombian departments in this table. The locally cached `gadm-4.1-adm1.gpkg` is restricted to an 81-country subset that excludes Colombia entirely (0 features for COL), so this is a fetch gap rather than a genuinely unregistered source: GADM's global ADM1 layer (`gadm41_COL_1`) does publish Magdalena's department boundary and would need to be pulled into the cache, not constructed or substituted from elsewhere. `polygon_feature_id` is left null pending that fetch; no `polygon_area_km2` is recorded since no geometry is attached, and nothing below should be read as a measurement of any attached shape.

**Territory description:** Magdalena is a department on Colombia's Caribbean coast, capital Santa Marta, at the northern foot of the Sierra Nevada de Santa Marta. On a modern map it is bounded by the Caribbean Sea to the north and northwest, La Guajira and Cesar to the east, Bolívar to the south and southwest, and Atlántico across the mouth of the Magdalena River to the west. Its present-day area is approximately 23,188 km2 — about 2% of Colombia's national total of ~1,141,748 km2, which is why routing its data to the national COL-* rows overstates its territory roughly 49-fold. Magdalena's boundary has not been static across the 1915-2025 span: Cesar was split off as its own department in 1967 and La Guajira (already a national territory, promoted to department in 1965) drew further from adjoining land, so the present-day ~23,188 km2 boundary is materially smaller than whatever the department covered in 1915. No polygon is attached yet, so this vintage mismatch is a live open question rather than something a proxy figure needs to be defended against here.

## Predecessors and successors

No predecessor or successor rows are set. Magdalena does not descend from a distinct prior polity tracked in this table for the 1915-2025 span — its administrative existence as a department predates 1915 without a corresponding rupture in the routed data, so no predecessor edge is drawn rather than inventing one without evidence. It has no successor because it remains a current, unabolished Colombian department as of the 2025 open end_year convention used across this table's still-current subnational units. Cesar's 1967 separation and La Guajira's 1965 promotion to department status are administrative boundary changes to Magdalena's own territory, not a succession of the Magdalena polity itself, and are noted under territorial extent and open questions rather than modeled as predecessor/successor edges.

## Sourced claims

- Magdalena is one of Colombia's historic departments under the unitary 1886 Constitution, not one of the territorios nacionales first elevated to department status starting in 1991 (per this project's country-convention departure list), which is why the default pre-1991 start-year rule rather than a 1991-anchored one applies to it.
- Magdalena's approximate present-day area is 23,188 km2 against Colombia's national total of approximately 1,141,748 km2 — the department is roughly 2% of the country, so routing its data to the national COL-* rows overstates its territory on the order of 49-fold.
- Cesar department was separated from Magdalena territory in 1967, and La Guajira (a national territory since the 19th century) was promoted to department status in 1965 with land historically administered from Santa Marta, both of which shrank Magdalena's boundary within the 1915-2025 span this entry covers.

## Decisions

### d-follow-dominant-iso3-subunit-pattern

**Use the dominant <ISO3>-<SUBUNIT>-<start>-<end> code pattern, not a bespoke code**

Magdalena is an ordinary current administrative department, not a historical territory with its own proper name comparable to Alaska Territory, Hyderabad State, or the Ryukyu Islands under US administration — the three bespoke-code exceptions in this table's precedent. It is a standard ADM1 unit of a still-existing unitary state, so the dominant pattern observed in 57 of 66 subnational rows (<ISO3>-<SUBUNIT>-<start>-<end>) applies directly: COL-MAGDALENA-1915-2025. No existing Colombian subnational code precedent constrained this choice (0 prior COL subnational rows before this pipeline pass), so this entry and its siblings (COL-ANTIOQUIA-1886-2025, COL-ATL-1910-2025, COL-BOYACA-1886-2025, etc.) collectively set that precedent for Colombia going forward, all following the dominant pattern rather than diverging from it.

### d-use-1915-not-1886-start

**Start the span at 1915 (the routed data's start), not 1886 (department constitution)**

The routing decision's proposed span begins in 1915, matching where the country data this entry captures actually begins, rather than 1886 when Magdalena was constituted as a department under the unitary constitution (the date used for some sibling departments like Antioquia and Boyacá whose routed data reaches back that far). No data motivating this entry is known to exist for 1886-1915, and no independent evidence was gathered here to confirm Magdalena's administrative continuity across that earlier window specifically, so the span is kept conservative at 1915 rather than assumed to extend further back by analogy to siblings whose own data spans differ. This leaves 1886-1915 as a gap this entry deliberately does not claim to cover, flagged below as an open question.

## Open questions

### oq-magdalena-boundary-vintage-vs-cesar-guajira

**A present-day GADM polygon for Magdalena will not match its 1915-1965 extent**

Once gadm-4.1-adm1 is fetched for Colombia, the Magdalena feature it provides will reflect present-day boundaries (~23,188 km2), which post-date both the 1965 promotion of La Guajira to department status and the 1967 separation of Cesar — both of which drew territory away from what was administered as Magdalena earlier in this entry's 1915-2025 span. Data from the 1915-1964 portion of this span may therefore correspond to a larger reporting territory than any polygon eventually attached here would show, unless period-specific department boundaries are sourced (e.g. from IGAC historical cartography) rather than a single modern GADM snapshot reused across the whole span. This should be revisited when the polygon is actually fetched and assigned, since right now `polygon_status: unassigned` means no proxy decision has been made yet that this note could be checked against.

### oq-magdalena-pre-1915-department-history

**Whether Magdalena's administrative existence extends back before 1915 in a way that should extend this entry's start_year**

This entry starts at 1915 because that is where the routed data begins, not because 1915 is a documented administrative discontinuity for Magdalena — the department was already constituted well before that date under the 1886 Constitution, following the same default rule applied to sibling departments. If earlier country data (pre-1915) surfaces that should also route to Magdalena rather than the national COL-* rows, this entry's start_year would need to move earlier (with a corresponding container edge added against COL-1903-1922 or COL-1830-1903), rather than creating a second overlapping Magdalena entry, since the containment gate rejects edges that don't tile the full span and this repository disallows two pages for the same territory.
