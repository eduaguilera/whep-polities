---
polity_code: MEX-TABASCO-1824-2025
polity_name: Tabasco
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
polygon_feature_id: null
polygon_feature_year: null
polygon_status: unassigned
predecessor: []
successor: []
container:
  - code: MEX-1800-1848
    start_year: 1824
    end_year: 1848
    basis: Tabasco was one of the original states named in the 1824 Constitution of the United Mexican States, within the First Federal Republic / subsequent centralist period before the 1848 Treaty of Guadalupe Hidalgo reorganization
  - code: MEX-1848-2025
    start_year: 1848
    end_year: 2025
    basis: Tabasco continued as a constituent state of Mexico through the post-1848 federation to the present
---

# Tabasco

## Summary

Tabasco is a state of Mexico on the Gulf coast, in the southeast of the country, bordering Veracruz to the west, Chiapas to the south, Campeche to the east, and Guatemala's border region to the southeast, with a short Gulf of Mexico coastline to the north. It was one of the states named directly in the 1824 Constitution of the United Mexican States, at the founding of the first Mexican federal republic, and has remained a constituent state continuously since — unlike Baja California, Baja California Sur, and Quintana Roo, which began as federal territories and only later converted to statehood. `type: subnational` is used because Tabasco never held sovereign statehood of its own; Mexico held sovereignty over this territory throughout 1824-2025, and this entry exists purely to carry state-level reporting data that the national MEX rows are too coarse to represent. The entry spans 1824-2025 because that is the state's full continuous existence as a named constituent unit, even though the ingested data series for Tabasco (mitchell and/or related agricultural/production tables referenced by this pipeline) only begins around 1900; per this repository's country-convention default for Mexican states, the polity's start_year reflects federation admission rather than data availability.

**Why this entry exists.** This entry captures Mexican state-level data for Tabasco that the routing pipeline found matched only to national-level MEX rows (MEX-1800-1848 and MEX-1848-2025), which are roughly 80 times larger in area than the state itself and therefore inappropriate reporting units for state-specific statistics. No candidate subnational polity existed for Tabasco prior to this decision — the routing_reasoning explicitly notes "candidates are only national-level Mexico rows." What confirms Tabasco is a genuinely distinct, long-standing administrative and statistical unit rather than an artifact of the ingested data's own labeling is its constitutional status: it was named directly as a state in Mexico's founding 1824 Constitution, not carved out or converted from a territory the way Quintana Roo or the two Baja California states were, and it has reported as a discrete administrative unit in Mexican federal statistics continuously since. This is the first Mexican subnational entry in the table (0 existing MEX subnational codes before this decision), so it also establishes the code and container-edge pattern that later Mexican state entries (e.g. Chiapas, Veracruz, Yucatan) should follow.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon feature is currently attached in the GeoPackage for this period. The routing decision resolved to `registered_source_unfetched`: GADM 4.1 adm1 is already a registered source in this repository (used for other ADM1-level state/province boundaries), and it is unambiguously the correct source type for a Mexican state, but the locally-subsetted `gadm-4.1-adm1` file bundled in this repo only carries an 81-country subset and Mexico was never included — confirmed zero features for MEX in the local file. `polygon_source` is therefore set to the slug `gadm-4.1-adm1` itself (per harness rules for this route, the slug IS the source even though unfetched), with `polygon_status: unassigned` and `polygon_feature_id: null` until the full GADM 4.1 adm1 release is fetched and Mexico's ADM1 rows (GID_1-keyed, including the Tabasco feature) are added to the local file.

**Territory description:** Tabasco covers roughly 24,700 km² of low-lying, heavily riverine coastal plain in southeastern Mexico — the delta region of the Grijalva and Usumacinta rivers, one of the wettest and most hydrologically dominant regions of the country. Its capital is Villahermosa. On a modern map it sits directly east of Veracruz state, north of Chiapas, and west of Campeche, with its northern edge on the Gulf of Mexico. State boundaries have been essentially stable since the 19th century, so a present-day GADM ADM1 boundary for Tabasco, once fetched, should serve as a reasonable proxy for the entire 1824-2025 span, though this treats a modern boundary as valid back to the 1824 founding and should be understood as an approximation rather than a period-accurate reconstruction. No area figure is stated here as measured, since no geometry is yet attached to this entry.

## Predecessors and successors

Tabasco has no predecessor or successor polity rows: it was named directly as a constituent state in the 1824 Constitution of the United Mexican States and has continued uninterrupted as a Mexican federal state ever since, with no territorial reorganization severe enough to warrant a split entry (unlike, e.g., Baja California/Baja California Sur, which were carved from a single earlier territory). The two container edges (MEX-1800-1848, then MEX-1848-2025) capture the national-level reorganization around the 1848 Treaty of Guadalupe Hidalgo, but Tabasco itself persists as the same subnational unit across that transition.

## Sourced claims

- Tabasco was named as one of the original states of the federation in the 1824 Constitution of the United Mexican States, distinguishing it from Baja California, Baja California Sur, and Quintana Roo, which began as federal territories and converted to statehood later (Baja California in 1952, Baja California Sur and Quintana Roo in 1974).
- The locally-subsetted `gadm-4.1-adm1` GeoPackage used by this repository contains zero features for Mexico (ISO3 MEX), confirmed by direct inspection of the source file, even though GADM 4.1's public release does carry Mexican ADM1 (state-level) boundaries including Tabasco.

## Decisions

### d-code-pattern-iso3-subunit-years

**Followed the dominant subnational code pattern <ISO3>-<SUBUNIT>-<start>-<end>**

57 of 66 subnational rows in the table use <ISO3>-<SUBUNIT>-<start>-<end>. Tabasco is a genuine federal state (not a historical territory with a name of its own like Alaska or Hyderabad), so the bespoke-code exception does not apply. Used MEX-TABASCO-1824-2025, taking the routing decision's own unit_id (MEX-TABASCO) as the subunit token since it is already a stable, unambiguous abbreviation for this state and no shorter conventional abbreviation (like AS for Asturias) is established elsewhere in the table for Mexican states. This is the first Mexican subnational row, so it sets precedent for siblings (e.g. a future Chiapas or Yucatan entry should follow MEX-CHIAPAS-<start>-<end>).

### d-start-year-1824-not-1900

**Set start_year to 1824 per country convention, overriding the data's 1900 start**

The routing decision explicitly instructs that Mexican states default to their federation admission year (1824 Constitution) rather than the year the ingested data happens to begin, unless the state is one of the three documented exceptions (Baja California, Baja California Sur, Quintana Roo), none of which apply to Tabasco. Tabasco was named as one of the original states in the 1824 Constitution of the United Mexican States. This required a container edge reaching back to MEX-1800-1848 (which spans 1800-1848) to tile the full 1824-2025 span, since MEX-1848-2025 alone only covers from 1848.

### d-polygon-registered-unfetched

**polygon_source set to gadm-4.1-adm1 with polygon_status unassigned, per registered_source_unfetched route**

The routing decision's polygon_route is registered_source_unfetched: gadm-4.1-adm1 is already a registered source in sources.yaml and is the correct source type (ADM1 state boundaries) for this entity, but the locally-subsetted gadm-4.1-adm1 file used by this repo only covers 81 countries and Mexico's rows were never included in that subset. Per the harness instructions, in this route the slug itself is the polygon_source (not 'none' and not a placeholder like 'new_source_needed'), and polygon_status is unassigned rather than assigned or proxy, since no feature has actually been attached yet. polygon_feature_id is left null until the full GADM 4.1 adm1 release is fetched and Mexico's rows are added to the local file.

## Open questions

### oq-1824-constitution-confirmation

**Confirm Tabasco's 1824 status as a state rather than a later-converted territory**

The routing_concerns explicitly flag this: it should be verified that Tabasco was indeed named as a state (not a territory that only later converted to statehood) in the 1824 Constitution of the United Mexican States, to confirm start_year=1824 is correct rather than some other admission date. If a primary or secondary historical source shows Tabasco entered the federation at a different point (e.g., during the brief 1836-1846 centralist Republic reorganization, when several states were temporarily redesignated as departments), start_year may need revision, and the container edge split at 1848 (currently MEX-1800-1848 / MEX-1848-2025) may need an additional edge to capture that intermediate reorganization.

### oq-gadm-mexico-fetch-needed

**GADM 4.1 adm1 full release must be fetched to attach Tabasco's polygon**

No polygon is attached to this entry at all, since the locally-subsetted gadm-4.1-adm1 GeoPackage excludes Mexico entirely (0 features for MEX, confirmed). Until the full GADM 4.1 adm1 release is fetched and Mexico's ADM1 rows are merged into the local source file, this entry will remain polygon_status: unassigned. This also blocks any area (km2) figure from being computed for Tabasco, and blocks the same fix for any other Mexican state entries created under this same routing precedent.

### oq-data-start-year-gap

**Data for Tabasco reportedly begins around 1900, leaving a 1824-1900 span with no observed data**

The routing_reasoning references "the data's 1900 start" as the reason a naive approach might have set start_year=1900; the polity's actual start_year is set to 1824 per country convention, but this means roughly three-quarters of this entry's span (1824-1900) currently has no data rows routed to it and exists purely to correctly delimit the polity's constitutional history. Whether any earlier (pre-1900) Tabasco-specific statistical series exist in other sources that should also be routed here is unconfirmed.
