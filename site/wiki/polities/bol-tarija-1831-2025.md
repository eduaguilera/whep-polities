---
polity_code: BOL-TARIJA-1831-2025
polity_name: Tarija (department of Bolivia)
start_year: 1831
end_year: 2025
type: subnational
iso3: BOL
continent: South America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: gadm-4.1-adm1
polygon_feature_id: BOL.9_1
polygon_feature_year: null
polygon_status: unassigned
predecessor: []
successor: []
container:
  - code: BOL-1825-1903
    start_year: 1831
    end_year: 1903
    basis: Tarija was incorporated into Bolivia and constituted as a department in 1831, per the country convention's documented departure from the default 1825/1826 start rule; from constitution until 1903 it sat inside the republic's first national era, BOL-1825-1903.
  - code: BOL-1903-1909
    start_year: 1903
    end_year: 1909
    basis: Tarija remained a department of Bolivia through the national-era boundary at 1903, which reflects a change recorded in the country row, not in Tarija's own department borders.
  - code: BOL-1909-1938
    start_year: 1909
    end_year: 1938
    basis: Tarija remained a department of Bolivia through the national-era boundary at 1909; the department's eastern and southern limits were still being contested through the Chaco War period that falls inside this era.
  - code: BOL-1938-2025
    start_year: 1938
    end_year: 2025
    basis: Tarija continues as a department inside Bolivia's current national era, BOL-1938-2025, which begins after the 1938 Chaco Peace settlement fixed Bolivia's eastern boundary with Paraguay.
---

# Tarija (department of Bolivia)

## Summary

Tarija is a department (admin-1 unit) of Bolivia in the country's far south, bordering Argentina and Paraguay, historically a contested borderland between Upper Peru/Bolivia, Argentina and the former Spanish intendancy of Salta before being formally incorporated and constituted as a Bolivian department in 1831 -- six years after the republic's own 1825 founding, which is why this entry's start_year departs from the default rule most other Bolivian departments use. The department capital is the city of Tarija, and the region is known for its wine- and singani-producing valleys as well as, since the mid-20th century, natural gas production in its eastern lowlands near the Chaco. This entry is `type: subnational` because Tarija has never been a sovereign polity: it is carried here as a first-level administrative reporting unit inside Bolivia, following the same convention already applied to Bolivia's other departments (e.g. BOL-BEN-1842-2025) and to Spain's and Argentina's provinces elsewhere in this table -- department-level units that appear as distinct reporting units in agricultural and trade statistics get their own polity row rather than being folded into the national BOL-* row, which would misrepresent the territory the underlying data actually describes.

**Why this entry exists.** This row is created directly from a routing decision (unit_id BOL-TARIJA) rather than from a specific data extract examined here: the routing stage identified Tarija, a Bolivian department, as a first-level administrative unit that the country's routing convention requires to have its own polity row, and found that none of the four existing BOL-* candidates (national totals, not departments) represented it -- a department is not its country, and folding Tarija's data into a national row would misattribute department-scale statistics to the whole of Bolivia. What confirms Tarija is a distinct, long-standing administrative entity rather than an artefact of the matcher is Bolivia's own department history: unlike most departments, which the country convention dates to the 1825/1826 republic founding, Tarija is explicitly documented there as incorporated and constituted separately in 1831, after resolution of its contested status as a borderland with Argentina and the former intendancy of Salta -- a distinctness the convention itself calls out rather than something inferred from the data alone.

## Territorial extent

Polygon status: Not yet assigned (polygon_status: unassigned). The routing decision identified gadm-4.1-adm1 as the correct eventual source -- already registered and used for this same kind of department-level feature elsewhere in the table, including on BOL-BEN-1842-2025 -- with the likely feature BOL.9_1 following GADM's standard Bolivia department numbering. This is unverified: the GeoPackage cached locally at data/geodata/gadm-4.1/gadm41_adm1.gpkg is a curated 81-country subset that excludes Bolivia entirely, so no feature can be fetched or confirmed from what is on disk today. No polygon is attached, and no area figure is given, because there is nothing to measure yet -- fetching the global GADM 4.1 adm1 layer (or a Bolivia-specific extract) is the open task recorded below.

Territory description: Tarija department occupies Bolivia's southernmost tip, a region of Andean valleys in the west transitioning to Chaco lowlands in the east, bordering Argentina to the south and Paraguay to the southeast. Its capital is the city of Tarija. On a modern map, present-day Tarija department covers roughly 37,600 km2 -- one of Bolivia's smaller departments by area, historically known for viticulture in its central valleys and, since the discovery of major natural gas fields in the Chaco lowlands in the latter 20th century, a significant hydrocarbon-producing region. No polygon (proxy or otherwise) is attached in this entry, so this km2 figure is drawn from general knowledge of the present-day department's extent, not measured from any geometry in this table; a source-backed figure should replace it once GADM 4.1 adm1 is fetched and BOL.9_1 (or the correct feature) is confirmed and attached.

## Predecessors and successors

No predecessor: Tarija is not carried forward from an earlier polity row in this table; its 1831 constitution as a department is the unit's own administrative origin, following disputed status as a borderland between Bolivia, Argentina and the former Spanish intendancy of Salta since independence, not a continuation of a differently-coded polity. No successor: Tarija continues to the present day as a department of Bolivia, so end_year: 2025 records the open/current bound rather than a dissolution, and no follow-on row is needed. The department's own internal boundary history -- an unsettled 19th-century frontier with Argentina, and a possible Chaco War-era eastern adjustment -- is handled inside this single row via the polygon-vintage caveats in the open questions below, rather than by splitting the row into separate pre/post-settlement entries, since no source available here ties a specific data series to either boundary configuration.

## Sourced claims

- Tarija was incorporated into Bolivia and formally constituted as a department in 1831, later than the 1825/1826 republic founding that most other Bolivian departments default to, per the country convention's documented departure for this unit.
- The department's southern frontier with Argentina, running through the Bermejo and Pilcomayo river basins, was not settled by treaty until 1889 (ratified 1893), decades after the department's 1831 constitution -- meaning any modern GADM boundary is an approximation for the earlier portion of this span.
- Bolivia's national polity chain in this table divides at 1903, 1909 and 1938, and Tarija's own department status persisted unchanged across all three of those national-era boundaries, so its container edges track the national chain rather than any change internal to the department.

## Decisions

### d-start-year-1831-not-extract

**Used 1831 as start_year, per the country convention, rather than the extract's 1900 or the republic-founding 1825/1826 default**

The routing decision's span_basis cites the country convention's documented departure for Tarija: unlike most Bolivian departments that default to the 1825/1826 founding of the republic, Tarija was only incorporated into Bolivia and constituted as a department in 1831 -- it had been contested between Bolivia, Argentina and the former Spanish intendancy of Salta since independence, and the 1831 date is when the department was formally organized under La Paz rather than left as a disputed borderland. The source extract that surfaced this unit only carries data from 1900 onward (juan-subnational), but start_year records the territory's own administrative origin, not the first year data happens to exist for it -- the same convention followed on BOL-BEN-1842-2025, whose department-formation year (1842) predates its own earliest data. Using 1900 instead would misstate when Tarija became a department; using 1825 would ignore the country convention's explicit correction for this one department.

### d-container-four-eras

**Split the container into four edges tiling 1831-2025 across all four BOL national eras, instead of the single BOL-1825-1903 edge the routing decision proposed**

The routing decision's own routing_concerns flagged this: a single container_code for the whole 1831-2025 span would leave everything after 1903 uncontained, and the containment gate rejects an edge whose bounds fall outside the container's own span (BOL-1825-1903 only exists through 1903). Reading the polity table's four Bolivian national eras -- BOL-1825-1903, BOL-1903-1909, BOL-1909-1938, BOL-1938-2025, the same chain already used on BOL-BEN-1842-2025 -- and tiling one edge per era that overlaps Tarija's span (starting the first edge at 1831, not 1825, since Tarija did not exist as a department before then) covers the full 1831-2025 range with no gap, exactly as the Beni entry's precedent did for its own start year.

### d-polygon-source-not-new-needed

**Recorded polygon_source as the registered slug gadm-4.1-adm1 with polygon_status unassigned, not new_source_needed**

The routing decision's polygon_route is registered_source_unfetched: GADM 4.1 publishes an adm1 feature for Tarija department, and gadm-4.1-adm1 is already the registered source used for this same kind of department-level feature elsewhere in the table (including on BOL-BEN-1842-2025). The blocker is not that no boundary exists or that the source is unregistered -- it is that the locally cached extract at data/geodata/gadm-4.1/gadm41_adm1.gpkg is a curated 81-country subset that excludes Bolivia entirely (0 Bolivia features, per the routing decision's own polygon_reasoning). Per the harness instructions, registered_source_unfetched means the slug IS the source and polygon_status is unassigned, which is what this entry declares. polygon_feature_id BOL.9_1 is recorded as GADM's standard Bolivia numbering guess (following the same convention Beni's entry used for BOL.2_1) but is explicitly unverified, since it cannot be confirmed against the missing local extract.

## Open questions

### oq-gadm-bolivia-not-cached

**GADM 4.1 adm1 for Bolivia, including Tarija, is not present in the locally cached GeoPackage**

The same gap already recorded on BOL-BEN-1842-2025 applies here: data/geodata/gadm-4.1/gadm41_adm1.gpkg is an 81-country subset that does not include Bolivia, so the feature ID BOL.9_1 recorded above is an unverified guess following GADM's standard country-numbering pattern, not a confirmed match. Fetching the global GADM 4.1 adm1 layer (or a Bolivia-specific extract) and re-running the polygon assignment step would confirm or correct this feature ID and let polygon_status move from unassigned to assigned. Until then, no area figure can be measured or cited for this entry.

### oq-boundary-vintage-19th-century

**Tarija's 19th-century boundary with Argentina was not fixed until well after 1831 and GADM reflects only the present-day line**

Tarija's southern border was disputed with Argentina for decades after the department's 1831 constitution -- the frontier along the Bermejo and Pilcomayo river basins was not settled until the 1889 Bolivia-Argentina boundary treaty (ratified 1893), with further adjustments into the early 20th century. Any polygon eventually attached from gadm-4.1-adm1 will reflect the present-day department line, which is an approximation for the 1831-1893 portion of this span, in the same way BOL-BEN-1842-2025 flags its own pre-1938 boundary as smaller than what GADM digitises today. This should be noted as a vintage caveat once a polygon is actually assigned, rather than silently treating the modern GADM line as valid all the way back to 1831.

### oq-chaco-war-territory-loss

**Whether Tarija's own department boundary shifted as a result of the 1932-1935 Chaco War and 1938 peace settlement**

The Chaco War was fought largely over the Chaco Boreal, territory more commonly attributed to Bolivia's national claims and to the neighbouring department configuration than to Tarija specifically, but Tarija's eastern and southeastern limits run close to the disputed Chaco region and the 1938 Chaco Peace Treaty's final delimitation could plausibly have touched Tarija's own eastern boundary rather than only Bolivia's national frontier with Paraguay. This entry currently assumes Tarija's department-level boundary was unaffected and only the national container changes at 1938 (per the container edge basis above); this has not been separately verified against a Bolivian departmental-boundary history and should be checked before treating the post-1938 GADM shape as valid for the full 1938-2025 portion of this span.
