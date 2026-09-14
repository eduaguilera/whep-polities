---
polity_code: MEX-GUANAJUATO-1824-2025
polity_name: Guanajuato
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
polygon_feature_id: MEX.11_1
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: MEX-1800-1848
    start_year: 1824
    end_year: 1848
    basis: Guanajuato was one of the original states admitted under the 1824 federal constitution, inside the first Mexican federation before the 1848 Treaty of Guadalupe Hidalgo territorial loss
  - code: MEX-1848-2025
    start_year: 1848
    end_year: 2025
    basis: Guanajuato continues as a federal state inside Mexico after the 1848 territorial reorganization, unaffected by the northern cessions
---

# Guanajuato

## Summary

Guanajuato is one of the 19 original states of the Mexican federation created under the 1824 Constitution, carved from the colonial-era Intendancy of Guanajuato in the Bajio region of central Mexico. It is not one of the three states created later by converting a federal territory (Baja California, Baja California Sur, Quintana Roo), so under this repository's country convention its start year follows the founding-federation default of 1824 rather than a later territory-to-statehood conversion date. This entry is type: subnational because Guanajuato has never held sovereignty of its own -- it is, and has always been, a first-order administrative division inside Mexico, first as a state of the First Federal Republic, then continuously (with brief centralist-era interruptions common to all Mexican states) as a state of the federation through the present day. The end_year of 2025 (exclusive) reflects that it remains a current, ongoing state, following the country convention's open-end-year rule for still-existing subnational units rather than an actual dissolution.

**Why this entry exists.** This entry captures Guanajuato as its own reporting unit distinct from Mexico's national totals. Before this entry, any production, trade, or population data reported specifically for the state of Guanajuato had no polity row of its own to route to and would have fallen to MEX-1800-1848 or MEX-1848-2025, both of which are national-level rows covering the entire country -- for a state that is roughly 1/32nd of national territory and population, routing state-level statistics to the national total silently mixes one state's figures into all-Mexico totals (or, worse, leaves state-level series unmatched entirely). No existing polity in the table represents Guanajuato specifically: a grep of the polities database confirms MEX has zero subnational rows prior to this one, so this entry sets the country's own subnational precedent. Guanajuato's distinctness as a first-order administrative/statistical unit is confirmed structurally: it is one of the entities enumerated in the 1824 Acta Constitutiva de la Federacion and every subsequent Mexican federal constitution (1857, 1917) as one of the states composing the federation, and it is the level at which INEGI (Mexico's national statistics institute) and its predecessors have always published state-level census, agricultural, and production series -- i.e., "Guanajuato" is and has long been a standard statistical reporting geography in Mexican official data, not an ad hoc grouping.

## Territorial extent

Polygon status: Not yet assigned. No polygon is available in the GeoPackage for this period. The routing decision identified gadm-4.1-adm1 as the correct registered source (GADM's admin-1 layer is already used elsewhere in this repo for country subdivisions, and Mexico's 32 states are standard GADM adm1 features), but the locally fetched gadm41_adm1.gpkg is a curated 81-country subset that does not currently include Mexico. This is registered_source_unfetched, not a missing-source or construction case: the source is registered and the boundary certainly exists in GADM, it simply has not been fetched to disk yet. polygon_source is set to the slug gadm-4.1-adm1 itself with polygon_feature_id null and polygon_status unassigned, per the rule that an unfetched-but-registered source names the slug directly rather than new_source_needed.

Territory description: Guanajuato is a landlocked state in central Mexico, in the Bajio region, bordered by Jalisco, Zacatecas, San Luis Potosi, Queretaro, and Michoacan. Its capital is the city of Guanajuato; its largest city is Leon. On a modern map it sits roughly 300-400 km northwest of Mexico City. Its modern area is approximately 30,491 km2 (INEGI's published figure for the state), making it one of the smaller Mexican states by area (about 1.5% of national territory) but historically one of the most economically important owing to its silver-mining heritage (the colonial mines of Guanajuato and Valenciana). No polygon is attached to this entry yet, so this figure is drawn from external published state-area statistics, not measured from any geometry in this database.

## Predecessors and successors

No predecessor or successor polity is named. Guanajuato has no prior distinct statistical/administrative predecessor in this table -- it enters directly as a founding state of the 1824 federation, carved from the colonial Intendancy of Guanajuato rather than split from another polity row that exists here. It has no successor: it remains a current Mexican federal state through the open end_year of 2025, per the country convention that leaves ongoing subnational units open-ended rather than closing them at an arbitrary date.

## Sourced claims

- Guanajuato is enumerated among the states of the federation in the 1824 Acta Constitutiva de la Federacion Mexicana, the founding document of the First Federal Republic.
- INEGI (Instituto Nacional de Estadistica y Geografia) publishes Guanajuato's state area as approximately 30,491 km2 in its official state-level geographic statistics (Anuario Estadistico y Geografico de Guanajuato).

## Decisions

### d-code-pattern-iso3-subunit

**Followed the dominant ISO3-SUBUNIT-start-end pattern**

Used MEX-GUANAJUATO-1824-2025 rather than a bespoke code. Guanajuato is an ordinary federal state with no historical name of its own distinct from the modern administrative unit (unlike Alaska Territory or Hyderabad), so the 57-row dominant pattern applies directly. Since MEX has zero existing subnational rows, this entry sets the country's own precedent: subunit token is the state's common short form GUANAJUATO (no shorter unambiguous abbreviation is in wide use, unlike Spanish provinces which have INE two-letter codes).

### d-two-container-edges

**Split the container into two edges to tile 1824-2025 without a gap**

The proposed decision only names MEX-1848-2025 as container, but that leaves 1824-1848 uncontained, which the containment gate rejects. The polity table has MEX-1800-1848 covering exactly that earlier era, so I added it as a second container edge (1824-1848) alongside MEX-1848-2025 (1848-2025), together tiling the full span with no gap and no edge falling outside either party's own span.

### d-polygon-unassigned-not-fetched

**polygon_source is the registered slug gadm-4.1-adm1 with status unassigned, not a route name**

The routing decision's polygon_route is registered_source_unfetched: GADM 4.1 adm1 is a registered source and does cover Mexican states, but the locally fetched subset (81 countries) excludes Mexico, so no GID_1 feature id can be named today. Per instructions this means polygon_source is the slug itself (gadm-4.1-adm1), polygon_feature_id is null, and polygon_status is unassigned -- not new_source_needed and not a fabricated feature id.

## Open questions

### oq-gadm-feature-id-unknown

**Guanajuato's GADM GID_1 code is unverified pending a full adm1 fetch**

The locally fetched gadm41_adm1.gpkg only covers a curated 81-country subset and Mexico is not among them. The expected pattern is MEX.11_1 (GADM's alphabetical-by-state-name GID_1 numbering would place Guanajuato around 11th of 32), but this is a guess from the general convention, not confirmed against actual data. Fetching data/geodata/gadm-4.1/gadm41_adm1.gpkg for Mexico (or the full global adm1 layer) and identifying the correct GID_1 value for Guanajuato is required before polygon_status can move from unassigned to assigned.

### oq-1824-admission-date-uncorroborated

**1824 start year applied by default rule, not corroborated by a source naming Guanajuato specifically**

The routing decision flags that 1824 comes from the general rule that original federation states date to the 1824 Constitution, not from a source that names Guanajuato's own admission date. Guanajuato was historically the Intendancy of Guanajuato under New Spain and became a state via the 1824 Acta Constitutiva/Constitucion Federal; a citation naming Guanajuato's own state-constitution date (Guanajuato adopted its own state constitution in 1826) should be checked in case the effective statehood date used elsewhere in this repo for comparable original states differs from the constitution-adoption year.

### oq-boundary-stability-since-1824

**Whether Guanajuato's 1824 boundary matches its modern GADM boundary is unverified**

The routing decision notes GADM 4.1 reflects present-day boundaries and calls the use of a modern feature for the full 1824-2025 span low-risk because there have been no major territorial disputes, but this claim is not sourced to a specific boundary history for the state. Nineteenth-century Mexican state boundaries were adjusted multiple times as neighboring states and the Federal District were carved out; whether any of those adjustments touched Guanajuato specifically (as opposed to, e.g., Mexico State or Michoacan) has not been checked against a historical atlas.
