---
polity_code: ARG-RIONEGRO-1884-2025
polity_name: Río Negro (province of Argentina)
start_year: 1884
end_year: 2025
type: subnational
iso3: ARG
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
  - code: ARG-1800-1899
    start_year: 1884
    end_year: 1899
    basis: Río Negro was a Territorio Nacional (Ley 1532, 1884) administered directly by the Argentine national government, so it sat inside the national row for this era. Split across the national chain because the previous single edge named ARG-1884-1951, a code that no longer exists after that page was renamed ARG-CHACO-1884-1951.
  - code: ARG-1899-1902
    start_year: 1899
    end_year: 1902
    basis: Río Negro was a Territorio Nacional (Ley 1532, 1884) administered directly by the Argentine national government, so it sat inside the national row for this era. Split across the national chain because the previous single edge named ARG-1884-1951, a code that no longer exists after that page was renamed ARG-CHACO-1884-1951.
  - code: ARG-1902-2025
    start_year: 1902
    end_year: 2025
    basis: From the 1902 reorganisation of the national territories through provincehood (1955) to the present, Río Negro remained one administrative unit inside the Argentine Republic as represented by this container code.
---

# Río Negro (province of Argentina)

## Summary

Río Negro is a province of Argentina in northern Patagonia, created as a Territorio Nacional in 1884 (Ley 1532) and elevated to provincial status in 1955 (Ley 14408). This entry treats it as one continuous administrative territory from its 1884 creation to the present, spanning both its territorio-nacional era and its provincial era, because the change in 1955 was a change of legal status (representation in Congress, self-government) rather than a redrawing of its boundaries or a break in administrative continuity. `type: subnational` reflects that Río Negro was never a sovereign polity in its own right -- it was always a first-order division of Argentina, first as a centrally administered national territory and later as a province with its own government -- and the entry exists purely to carry statistical data reported at this sub-national scale rather than to represent an independent state.

**Why this entry exists.** This entry captures production/statistical data for the unit "Río Negro" (Argentina) spanning roughly 1900-2023, currently unrouted to any existing polity code. That data was at risk of being matched to the national row ARG-1902-2025 (or a similar all-Argentina code), which would have folded a single Patagonian province's output into a series covering the entire country -- a large territorial mismatch by area (Argentina is roughly 2.78 million km2; Río Negro is roughly 203,000 km2) and a serious distortion for any per-area or per-capita figure derived from the series. The unit is confirmed as a distinct, continuously governed administrative entity by Argentina's own legal record: Ley 1532 (1884) created the Territorio Nacional de Río Negro with its own boundaries and administration separate from other territorios nacionales (Chubut, Neuquén, La Pampa), and Ley 14408 (1955) elevated it to a province without merging or splitting it. That two-law history of a single named, bounded jurisdiction is the same kind of source-confirmed administrative distinctness that justifies other territorio-nacional-to-province entries already in the table (e.g. ARG-CHUBUT-1884-2025).

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is available in the GeoPackage for this period. The intended source is `gadm-4.1-adm1` (registered in scripts/sources.yaml, id column GID_1), which digitises Río Negro as a present-day first-order Argentine administrative division, but the locally cached copy of that source only covers 81 countries and returns zero Argentina features -- the global GADM 4.1 GeoPackage (or an Argentina-specific extract) still needs to be fetched before a GID_1 feature (expected code pattern ARG.20_1 or similar) can be queried and assigned. Because the route is `registered_source_unfetched`, `polygon_source` is recorded as the slug itself (`gadm-4.1-adm1`) and `polygon_status` as `unassigned`, rather than left as `none`.

**Territory description:** Río Negro is a province in northern Argentine Patagonia, bordered by Neuquén to the west, La Pampa and Buenos Aires province to the north/northeast, Chubut to the south, and the Atlantic Ocean to the east; its capital is Viedma, at the mouth of the Río Negro river that gives the province its name. On a modern map it occupies the region between roughly 38°S and 42°S latitude, stretching from the Andean foothills near Bariloche in the west to the Atlantic coast in the east. Its present-day area is approximately 203,013 km² (a figure from published Argentine provincial statistics, not a measurement from any polygon attached to this entry, since none is attached). No polygon-derived area figure is reported here, consistent with `polygon_status: unassigned` -- an area measurement will only be added once a GADM feature is actually fetched and attached.

## Predecessors and successors

No predecessor: this entry begins at the territory's own legal creation as the Territorio Nacional de Río Negro under Ley 1532 in 1884, so there is no prior polity whose territory or population it inherited. No successor: the province persists to the present day (`end_year: 2025` under the open-ended convention for still-current subnational units), with no further change of administrative status or boundary since the 1955 provincehood (Ley 14408) that occurs within this same entry's span rather than at its edge.

## Sourced claims

- Ley 1532 (16 October 1884, Argentina) created the Territorio Nacional de Río Negro along with the other Patagonian and Chaco territorios nacionales, fixing its administrative boundaries separate from Neuquén, Chubut and La Pampa.
- Ley 14408 (1955, Argentina) elevated the Territorio Nacional de Río Negro to provincial status as the Province of Río Negro, one of several former territorios nacionales converted to provinces that year alongside Chubut, La Pampa, Neuquén and Santa Cruz.

## Decisions

### d-span-from-1884-creation

**Span the polity from the 1884 territorial creation, not from 1900 data or 1955 provincehood**

The unit's routed data (production series, roughly 1900-2023) only begins in 1900, and Río Negro was not elevated to a province until 1955 (Ley 14408). Two narrower choices were rejected: starting the code at 1900 would tie the polity's identity to a modern data source's coverage rather than to when the territory itself came into being, and starting at 1955 would orphan decades of data (1900-1955) describing the same continuously administered territory under its earlier Territorio Nacional status. Ley 1532 (1884) created Río Negro as a fixed-boundary Territorio Nacional under the national government, and Ley 14408 (1955) changed its legal status to province without altering its territory or administrative continuity -- the same land and population, governed continuously, just re-labelled. Following the sibling precedent already in the table (an ARG-1884-1951 national-era code with an 1884 start), a single 1884-2025 span for Río Negro keeps the polity's start year tied to the act that created the entity.

### d-code-follows-iso3-subunit-pattern

**Use the dominant ISO3-SUBUNIT-start-end code pattern**

Río Negro is an ordinary first-order administrative division of a country, not a historical territory with a name and identity independent of the modern state (unlike ALK or HAW). It therefore follows the dominant 338-of-351 pattern, ARG-RIONEGRO-1884-2025, matching the existing ARG-CHUBUT-1884-2025 and ARG-CORDOBA-1853-2025 entries in form and in the country convention's treatment of other Argentine territorios nacionales that predate provincehood.

## Open questions

### oq-gadm-boundary-vintage-risk

**GADM adm1 present-day boundary is assumed, not confirmed, for the 1884-1955 Territorio Nacional period**

polygon_source is set to gadm-4.1-adm1 with polygon_status unassigned because the source is registered in scripts/sources.yaml but the locally cached GADM 4.1 file only covers 81 countries and yields zero Argentina features -- the global GeoPackage (or an Argentina-specific slice) still needs to be fetched and queried on GID_1 for Río Negro (expected pattern ARG.20_1 or similar) before a feature can be assigned. Separately, once fetched, using today's provincial boundary as a proxy for the 1884-1955 Territorio Nacional silently assumes the territory's original limits matched the present-day province. Ley 1532 (1884) set the territorio's boundaries against the neighbouring Chubut, Neuquén and La Pampa territorios, and at least one adjustment is known to have occurred before 1955 (transfers of land between territorios nacionales during the early 20th century administrative reorganisations, including the 1902 restructuring recorded in the container basis above). Whether that adjustment changed Río Negro's specific extent, and by how much, has not been checked here and should be verified against a historical-boundary source (e.g. Argentina's own IGN historical maps) before the pre-1955 portion of this span is treated as boundary-accurate.

### oq-1884-1902-container-basis-unverified

**Whether ARG-1884-1951 actually represents the pre-1902 Argentine national government distinctly from ARG-1902-2025**

The container edges assume ARG-1884-1951 and ARG-1902-2025 are two genuinely distinct national-era rows in the polity table with a clean 1902 boundary between them, based only on the code names supplied in this task's precedent list -- their own start/end years and the historical basis for a break specifically at 1902 have not been read from the polity table itself. If ARG-1884-1951's span does not actually end at 1902, or if the table records a different transition year for Argentina's own administrative eras, these container edges will fail the containment gate (an edge outside either party's span) and need to be re-cut to whatever boundary the ARG national rows actually use.
