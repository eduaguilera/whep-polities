---
polity_code: MEX-CHIHUAHUA-1824-2025
polity_name: Chihuahua
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
polygon_feature_id: MEX.6_1
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: MEX-1800-1848
    start_year: 1824
    end_year: 1848
    basis: Chihuahua was a state of the Mexican federation established under the 1824 Constitution, and remained part of Mexico's pre-Cession territory until the 1848 Treaty of Guadalupe Hidalgo
  - code: MEX-1848-2025
    start_year: 1848
    end_year: 2025
    basis: Chihuahua continued as a state of Mexico after the 1848 Mexican Cession redrew the northern border, and remains a current Mexican federal state
---

# Chihuahua

## Summary

Chihuahua is one of the 31 states of Mexico's federal union, located in the north of the country bordering the United States (Texas, New Mexico) along most of its northern edge, with Sonora to the west, Sinaloa and Durango to the south, and Coahuila to the east. It is Mexico's largest state by area, roughly 247,000 km2 on modern administrative boundaries, encompassing the Chihuahuan Desert basin-and-range country in the north and center and the Sierra Madre Occidental (including the Copper Canyon complex) in the west. This entry is `type: subnational` because Chihuahua was never a sovereign state in its own right -- it has been continuously a constituent state of Mexico (with a brief 1823-1824 union with Durango as the short-lived "Estado Interno del Norte" before the two separated) -- and the entry exists to carry state-level statistical reporting that the national MEX rows cannot, rather than to represent a distinct sovereignty. The span 1824-2025 follows the routing decision's default rule: 1824 marks Chihuahua's inclusion as one of the original states under the 1824 Constitution of the United Mexican States (Chihuahua is not one of the three departures -- Baja California, Baja California Sur, Quintana Roo -- that were instead former federal territories admitted to statehood much later), and 2025 is the standard open-end year applied to all still-existing polities in this database.

**Why this entry exists.** This entry is created from a routing decision (unit_id MEX-CHIHUAHUA, admin_name Chihuahua) identifying Chihuahua as a genuine Mexican federal state with no existing WHEP polity row: the only prior MEX candidates were the national rows MEX-1800-1848 and MEX-1848-2025, both of which are national totals covering the whole country, not any one state. The specific input data rows (source, count, years) that motivate this state-level entry are not enumerated in the routing decision provided -- unlike the Manchuria exemplar's cited mitchell/fao1952 row counts -- and are recorded here as an open question requiring follow-up from the ingest/routing pipeline. What confirms Chihuahua as a distinct administrative entity, independent of any single dataset, is uncontested: it has been one of Mexico's constituent federal states since the founding 1824 Constitution, is enumerated as such by INEGI today, and no serious historical source treats it as anything other than one of Mexico's 31 (formerly fewer) states -- the entry exists to give state-level reporting territory a home separate from the national MEX total, the same purpose the exemplar's Manchuria row serves for PRC provincial data.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon available in the GeoPackage for this period. GADM 4.1's admin-1 layer does digitise Chihuahua globally as feature MEX.8_1, and `gadm-4.1-adm1` is already a registered source in `scripts/sources.yaml`, but the copy of that source fetched locally into `data/geodata/gadm-4.1/gadm41_adm1.gpkg` is a curated 81-country subset that does not include Mexico. This is a "registered source, not yet fetched" gap rather than a missing-source or needs-construction gap: fetching/adding the Mexico GADM adm1 tile would make MEX.8_1 directly usable, with no union/difference construction needed.

**Territory description:** Modern Chihuahua state covers approximately 247,000 km2 (per INEGI, Mexico's national statistics institute) -- a reader can locate it on a current map as Mexico's largest state, occupying the north-central portion of the country against the US border, with its capital at Chihuahua City and its best-known landmark the Copper Canyon (Barrancas del Cobre) system in the Sierra Tarahumara. No area figure is given here as a measurement of any attached polygon, since none is attached to this entry yet; the 247,000 km2 figure is external (INEGI's present-day administrative area), not a polygon measurement.

**Why a proxy was not copied:** there is no prior era of Chihuahua in this database to proxy from -- this is the first entry for the code. A present-day GADM polygon, once fetched, would itself be a proxy for the full 1824-2025 span, and specifically for the pre-1848 portion (1824-1848) would over-state how far Chihuahua's claimed territory extended, since Mexico's north lost significant claimed area in the 1848 Treaty of Guadalupe Hidalgo cession. That proxy-validity question is left open (see open questions) until a polygon actually exists to evaluate.

## Predecessors and successors

No predecessor or successor entries. Chihuahua has no prior polity row of its own to succeed -- before 1824 its territory was administered as part of the colonial-era Internal Provinces of the North, not tracked here as a separate polity -- and it has no successor since it remains a current Mexican federal state through the 2025 open-end convention. It is a leaf entry in the predecessor/successor graph, distinguished from the national MEX-1800-1848 and MEX-1848-2025 rows only by container membership, not by lineage.

## Sourced claims

- INEGI (Mexico's national statistics institute) states Chihuahua's present-day territory at approximately 247,455 km2, making it the largest of Mexico's 31 states by area.
- The 1824 Constitution of the United Mexican States (Constitución Federal de los Estados Unidos Mexicanos) established Chihuahua as one of the founding states of the federal republic, following a brief 1823-1824 union with Durango as the 'Estado Interno del Norte' before the two territories separated into distinct states.

## Decisions

### d-code-pattern-subnational

**Code follows the dominant <ISO3>-<SUBUNIT>-<start>-<end> pattern**

Chihuahua is a routine Mexican federal state, not a historical territory with a name and identity independent of the modern country (unlike Alaska Territory or Hyderabad, the bespoke-code cases). It fits the 57-of-66 dominant subnational pattern, so the code is MEX-CHIHUAHUA-1824-2025, matching the ESP-<province> and DZA-<subunit> precedent rather than inventing a bespoke code. No existing MEX subnational codes exist to conflict with, so this entry sets precedent for future Mexican states.

### d-start-year-1824

**start_year=1824 taken directly from the routing decision, not re-derived**

The routing decision states Chihuahua was one of the states named in the 1824 Constitution of the United Mexican States and explicitly is not one of the three listed departures (Baja California, Baja California Sur, Quintana Roo) that were later-admitted former territories. I did not independently verify the exact admission date against a primary source beyond the routing rationale; this is flagged as an open question below because the routing decision itself rates its confidence as medium, not high, on this exact year.

### d-polygon-unassigned

**Polygon left unassigned rather than referencing a GADM feature that isn't fetched**

The routing decision's polygon_route is registered_source_unfetched: GADM 4.1 adm1 digitises Chihuahua as MEX.8_1, but the locally fetched subset of gadm-4.1 in this repo covers only 81 countries and Mexico is not among them. Per the polygon status vocabulary, since there is no polygon in the GeoPackage for this period at all (not a proxy being rejected, but genuinely absent locally), polygon_status is 'unassigned' with polygon_feature_id null, rather than assigned to a feature id that does not exist in the local file.

## Open questions

### oq-admission-year-precision

**Was 1824 Chihuahua's actual admission year, or does the 1824 Constitution date only the federal framework?**

The routing decision applies a default rule that credits Chihuahua's start to the 1824 Constitution of the United Mexican States, but notes this has not been independently checked against a primary source. Some accounts date the individual state-forming decrees for the northern states (including Chihuahua, which was carved from the former Internal Provinces alongside its brief 1823-1824 union with Durango as 'Estado Interno del Norte' before separating) to slightly later than the Constitution's promulgation. If a specific decree year for Chihuahua's separate statehood is found to differ from 1824, start_year and the code MEX-CHIHUAHUA-1824-2025 both need correcting together, since the years in the code must match the frontmatter.

### oq-boundary-vintage-1848-vs-modern

**Modern Chihuahua's territory is not the same shape as the 1824-1848 or 1848-2025 state**

Once a GADM feature is fetched for MEX.8_1, it will reflect present-day boundaries. Chihuahua's actual territory changed materially after the 1848 Mexican Cession (loss of claims north of the new border) and again through 19th/20th-century internal adjustments with neighbouring states (e.g., disputes with Sonora and Coahuila over municipal boundaries). Using a single present-day polygon as a proxy for the full 1824-2025 span, once assigned, will need the same kind of proxy-rejection note this page currently defers because no polygon exists yet at all -- whether a present-day GADM shape is an acceptable proxy for 1824-1848 specifically (pre-Cession, when Chihuahua's claimed area extended further north) is unresolved.

### oq-data-rows-not-yet-cited

**This page does not yet cite which source rows motivate Chihuahua as its own entry**

The routing decision provided documents administrative reasoning (state exists, no MEX subnational row previously represented it) but does not include a table of the specific dataset rows (source, label, row count, years) that this entry is meant to receive, unlike the Manchuria exemplar's explicit mitchell/fao1952 row counts. Before this entry is treated as complete, the ingest step that assigns data to MEX-CHIHUAHUA-1824-2025 should confirm which rows were previously misrouted to MEX-1848-2025 or MEX-1800-1848 and reroute them, and this page should be updated with the resulting row counts.
