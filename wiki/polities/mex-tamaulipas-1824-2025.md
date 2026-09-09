---
polity_code: MEX-TAMAULIPAS-1824-2025
polity_name: Tamaulipas
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
polygon_feature_id: MEX.28_1
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: MEX-1800-1848
    start_year: 1824
    end_year: 1848
    basis: Tamaulipas (as the pre-1824 colonial province of Nuevo Santander, renamed) was one of the founding states of the Federated Republic of Mexico under the 1824 Constitution, so its statehood begins inside the span of the pre-1848 Mexico row.
  - code: MEX-1848-2025
    start_year: 1848
    end_year: 2025
    basis: Continuous Mexican state, contained in the post-1848 national row (post-Mexican-American War territory) through the present; no change to Tamaulipas' own statehood or boundaries at this transition.
---

# Tamaulipas

## Summary

Tamaulipas is a state of Mexico on the Gulf coast in the northeast of the country, bordering Texas (USA) along the Rio Grande to the north, the Gulf of Mexico to the east, and the Mexican states of Nuevo Leon, San Luis Potosi and Veracruz. It was created as one of the founding states of the Federated Republic of Mexico under the 1824 Constitution, out of the former Spanish colonial province of Nuevo Santander (renamed Tamaulipas in 1824 after Mexican independence). Unlike Baja California, Baja California Sur and Quintana Roo, territories that were only later converted into full states, Tamaulipas held statehood from the federation's founding and is not one of the country convention's enumerated late-admission departures. type: subnational because Mexico held sovereignty throughout; this row exists only to carry the state-level administrative unit, distinct from the national MEX chain, so it does not compete with it in matching. The entry spans two eras of the national container (MEX-1800-1848, then MEX-1848-2025) because Tamaulipas' own continuous existence as a state straddles the 1848 national boundary/territory change (the loss of the northern territories in the Mexican-American War), even though Tamaulipas itself was not among the ceded territory and its own boundaries were not affected by that war.

**Why this entry exists.** This entry is created directly by the country-convention default-start-rule decision for MEX subnational units, not by a specific data-matching case documented in a prior open question. No existing polity row represents Tamaulipas specifically: only the two national MEX rows (MEX-1800-1848, MEX-1848-2025) exist, and both are the country-level container, not the state. Any source data keyed to Mexico/Tamaulipas at state granularity would previously have had nowhere to route except the national row, which is roughly 60x Tamaulipas' area and would misrepresent state-level statistics as national ones. Historical confirmation of distinctness: Tamaulipas appears as one of the original signatory states in the 1824 Federal Constitution's enumeration of the states of the federation, with continuous existence as a first-order administrative division of Mexico since then, unlike the three departures the country convention enumerates (Baja California, Baja California Sur, Quintana Roo), which were upgraded from territories later.

## Territorial extent

Polygon status: Not yet assigned. No polygon available in the GeoPackage for this period. The routing decision identified gadm-4.1-adm1 as the correct registered source for Mexican state boundaries, but the GADM 4.1 file currently on disk (gadm-4.1-adm1.gpkg) is a curated subset covering only 81 countries, and Mexico is not among them, so zero Tamaulipas features exist in the locally fetched data. This is a registered_source_unfetched case: the source is registered in scripts/sources.yaml, but obtaining the feature requires fetching the full/global GADM 4.1 admin-1 download (or a Mexico-specific GADM extract) rather than constructing from any polygon already on disk. No national or other subnational MEX polygon can substitute or be unioned to produce this shape, since GADM adm1 boundaries for Tamaulipas are not derivable from the national cshapes/cliopatria polygons already registered.

Territory description: Tamaulipas occupies Mexico's northeastern Gulf coast, roughly the area between the Rio Grande/Rio Bravo (the US-Mexico border with Texas) in the north, the Gulf of Mexico to the east, and the Sierra Madre Oriental foothills to the west, with its capital at Ciudad Victoria and major cities including Reynosa, Matamoros, Nuevo Laredo and Tampico. Its modern area is approximately 80,175 km2. The state's borders have been essentially stable since the 19th century; unlike the country's northern territories lost in 1848, Tamaulipas' own extent was not affected by that war, so a single modern-boundary polygon (once fetched) would reasonably proxy the entire 1824-2025 span, with the caveat standard to GADM-derived proxies that municipal-level adjustments over two centuries are not reflected.

## Predecessors and successors

No predecessor or successor polities: Tamaulipas has existed continuously as a Mexican state since 1824 with no territorial merger, split, or renaming event recorded in this database. It is not preceded by a separate colonial-era row (the Spanish province of Nuevo Santander, which it replaced, is not itself represented as a polity here) and has no open end; end_year 2025 uses the open-end convention for a currently existing polity, not an actual dissolution.

## Sourced claims

- Tamaulipas was among the states enumerated in the Mexican Federal Constitution of 1824, formed from the former colonial Provincia de Nuevo Santander (renamed Tamaulipas at Mexican independence).
- The three departures from the MEX subnational default-start convention, Baja California, Baja California Sur, and Quintana Roo, were admitted as full states later (1952, 1974, and 1974 respectively) after periods as federal territories; Tamaulipas has no such territorial-to-state conversion and dates its statehood to 1824.

## Decisions

### d-two-container-eras

**Split the container into two edges across the 1848 national boundary change**

Tamaulipas' 1824-2025 span crosses the point where the national MEX chain splits into MEX-1800-1848 and MEX-1848-2025 (the Mexican-American War territorial loss). Since Tamaulipas itself was not part of the ceded territory and its own borders and statehood were continuous across 1848, a single container edge covering only one national era would leave the other era's portion of this entry's span uncontained, which the containment gate rejects. Two edges were used instead: MEX-1800-1848 for 1824-1848 and MEX-1848-2025 for 1848-2025, tiling the full span with no gap and matching each edge to the container row that actually existed in that era.

### d-no-polygon-assigned

**Left polygon_status as unassigned rather than guessing a proxy or constructing one**

The routing decision proposed polygon_source: gadm-4.1-adm1 directly, but the schema requires a source that is actually usable now, and the local GADM 4.1 file excludes Mexico entirely (curated 81-country subset). Following the routing spec's instruction that registered_source_unfetched cases should still name the registered slug as polygon_source while marking polygon_status as unassigned (not assigned or proxy), this entry does that rather than inventing a constructed union (no other registered source carries Mexican state-level detail to build from) or leaving polygon_source as none (which would lose the information that the correct source is already identified, just not fetched).

## Open questions

### oq-gadm-mexico-fetch

**GADM 4.1 admin-1 data for Mexico has not been fetched**

The registered source gadm-4.1-adm1 is the correct boundary source for Tamaulipas (and every other Mexican state entry created under this same routing decision), but the file on disk only covers 81 countries and Mexico is not one of them. Until a global or Mexico-specific GADM 4.1 admin-1 download is added to the pipeline, every Mexican subnational entry created from this batch of routing decisions will sit at polygon_status: unassigned. This should be resolved once, centrally, rather than per-state, since it affects all Mexican state-level pages simultaneously.

### oq-1824-admission-year

**Exact admission year to the federation not verified against a primary source**

The routing decision flagged this itself: start_year=1824 follows the country convention's default rule (the year of the 1824 Constitution) rather than a confirmed date of Tamaulipas' specific admission or the seating of its first state congress, which in some Mexican states occurred in 1824 or 1825 depending on when the state constitution was ratified. No evidence was found suggesting Tamaulipas was a late admission like the three enumerated departures, but the precise year (1824 vs 1825) has not been checked against a primary legislative source and could shift start_year by one year if verified.

### oq-nuevo-santander-predecessor

**Whether the colonial province of Nuevo Santander should be a predecessor row**

Tamaulipas was formed by renaming the Spanish colonial Provincia de Nuevo Santander at independence. No polity row represents Nuevo Santander in this database, so predecessor is left empty rather than pointing to a nonexistent code. If a colonial-era Mexican provinces layer is ever added to this database, Nuevo Santander should be added as a predecessor here, but 1824 stands as this territory's origin as a state.
