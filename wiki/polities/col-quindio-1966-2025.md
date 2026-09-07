---
polity_code: COL-QUINDIO-1966-2025
polity_name: Quindío (department of Colombia)
start_year: 1966
end_year: 2025
type: subnational
iso3: COL
continent: South America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: none
polygon_feature_id: null
polygon_feature_year: null
polygon_status: unassigned
predecessor: [COL-CALDAS-1905-2025]
successor: []
container:
  - code: COL-1922-2025
    start_year: 1966
    end_year: 2025
    basis: Quindío was created as a department in 1966 within the modern national era (COL-1922-2025), a single era that already covers the whole 1966-2025 span with no gap; Colombia held sovereignty throughout and Quindío remains a current department
---

# Quindío (department of Colombia)

## Summary

Quindío is a department in west-central Colombia, in the heart of the country's Eje Cafetero (coffee axis), with its capital at Armenia. It was created by national law in 1966, carved from the territory of the department of Caldas, in the same administrative reform that also split off neighbouring Risaralda. This entry is `type: subnational` — Colombia held sovereignty throughout 1966-2025 and Quindío was never a sovereign state — but it is a distinct administrative and statistical reporting unit that agricultural and trade data are tabulated against separately from both the national COL total and its parent department, Caldas, which is why the row exists rather than folding this data into either of those. The department's start_year of 1966 reflects its legal creation date, not the earlier years for which back-cast/reconstructed data exists under its present-day boundary; its end_year of 2025 follows the open-ended convention used across this table for still-current, unabolished Colombian departments, matching sibling entries Caldas, Antioquia, Boyacá, Cesar and Chocó resolved in the same pipeline pass.

**Why this entry exists.** The routing decision (unit_id COL-QUINDIO) identified Colombian source data labelled with a Quindío-specific administrative name, previously matched only to the national COL-1922-2025 row — Colombia's whole-country total (~1,141,748 km2), roughly 620 times Quindío's present-day area of ~1,845 km2. No existing polity in the table represents Quindío specifically: the four COL-* national-era rows are successive whole-country totals, and while Caldas (COL-CALDAS-1905-2025, created in this same pipeline pass) is the department Quindío split off from, Caldas's own row covers only its own post-split administrative continuation, not the Quindío territory carved away from it in 1966. Quindío's distinctness as an administrative unit is confirmed by Colombian administrative history: it was formally created as a department by national law in 1966 out of Caldas territory (the same reform documented in Caldas's own sourced claims), and has been continuously governed and statistically reported (via DANE) as its own department since. The source data's own method composition — dominated by interpolated_scaled and scaled (back-cast) methods rather than raw observed figures — is itself evidence that the underlying dataset is reconstructing a Quindío-shaped series across years before 1966, which is exactly the pattern this pipeline treats as requiring a distinct polity row rather than silent absorption into either Caldas or the national total.

## Territorial extent

**Polygon:** `polygon_status: unassigned`, `polygon_source: none`. The routing decision classified this as `new_source_needed`: the locally registered `gadm-4.1-adm1` cache is an 81-country subset that excludes Colombia entirely (0 features), and neither Cliopatria nor cshapes-2.0 digitise Colombia below whole-country granularity, so no registered source — fetched or otherwise — can currently supply a Quindío-specific boundary, ruling out both `registered_source_unfetched` and `construct_from_registered`. The routing decision names GADM's global ADM1 layer (fetchable as `gadm41_COL_1` from gadm.org) as the likely candidate once someone verifies its licence terms, which this session did not do; that remedy is recorded as an open question rather than declared here, per the rule that `new_source_needed` pages point to `none` and leave the wanted source as an open question rather than writing an unregistered slug into `polygon_source`. No `polygon_area_km2` is recorded, since no geometry is attached to this entry to measure.

**Territory description:** On a modern map, Quindío sits in west-central Colombia, bordered by Caldas and Risaralda to the north, Tolima to the east across the Cordillera Central, and Valle del Cauca to the south and west. Its capital, Armenia, lies in the coffee-growing hills of the Cordillera Central's western slope. Quindío is one of Colombia's smallest departments by area, at approximately 1,845 km2 (a widely cited figure for the modern department, distinct from and much smaller than parent department Caldas's present-day ~7,888 km2), but is agriculturally and touristically significant as part of the UNESCO-recognised Coffee Cultural Landscape of Colombia.

## Predecessors and successors

No successor row is set: Quindío remains a current, unabolished department of Colombia, so its span runs open-ended to the 2025 end_year convention used across this table for still-current subnational units. Predecessor is set to COL-CALDAS-1905-2025: Quindío's entire territory was carved directly out of Caldas department in 1966, the same reform that also split off Risaralda (not yet a row in this table — see open questions). This is a genuine predecessor edge rather than a no-op, because Caldas itself continues to exist afterward as a smaller, ongoing department rather than being superseded or dissolved — mirroring how COL-CALDAS-1905-2025 itself declined to draw predecessor edges to Antioquia/Tolima/Cauca (those departments continued rather than being superseded) but is different here because Quindío is entirely new territory-wise, splitting cleanly away from a single parent rather than being assembled from multiple continuing donors.

## Sourced claims

- Quindío was created as a department of Colombia in 1966, split off from the department of Caldas as part of the same administrative reform that also carved off Risaralda — a fact already recorded on sibling entry COL-CALDAS-1905-2025's sourced claims regarding the 1966 reduction of Caldas's territory.
- The pipeline's routing decision for unit_id COL-QUINDIO found the source data dominated by interpolated_scaled (74.6%) and scaled (23.7%) methods, the back_cast signature of values reconstructed onto Quindío's present-day department boundary for years before 1966, when the department did not yet exist as an administrative or statistical reporting unit.
- Colombia's registered local GADM ADM1 cache (gadm-4.1-adm1.gpkg) contains zero features for Colombia (COL), out of a stated 81-country subset, meaning no department-level polygon for Quindío — or any other Colombian department — is currently available from a registered, already-fetched local source.

## Decisions

### d-follow-dominant-iso3-subunit-pattern

**Used <ISO3>-<SUBUNIT>-<start>-<end> rather than a bespoke code**

The polity code is COL-QUINDIO-1966-2025, following the dominant 57-of-66 subnational pattern (e.g. ESP-AS-1833-2025, DZA-CVD-1902-1919) rather than a bespoke name-only code, and matching sibling Colombian department entries already created in this same pipeline pass — COL-CALDAS-1905-2025, COL-ANTIOQUIA-1886-2025, COL-BOYACA-1886-2025, COL-CESAR-1967-2025, COL-CHOCO-1947-2025. Quindío is a standard department within Colombia's standing administrative hierarchy, not a historical territory with an identity independent of the containing state the way Alaska Territory or Hyderabad State were, so the 3-of-66 bespoke-code exception does not apply. The subunit token QUINDIO is spelled out in full (accent dropped, matching the ASCII-only convention already used for NORTEDESANTANDER and other sibling codes in this pass), rather than inventing an abbreviation.

### d-start-year-1966-not-extract-start

**start_year set to 1966 (legal creation), not the extract's earlier data years**

The routing decision reports the source data uses interpolated_scaled and scaled methods for 74.6% and 23.7% of rows respectively, which is the back_cast signature: values reconstructed onto Quindío's present-day boundary for years before the department existed. Per the country's default rule already applied to sibling departments (COL-CESAR starts 1967, COL-CHOCO starts 1947) that depart from their extract's start year, this entry's start_year is pinned to the department's actual legal creation year, 1966, when it was split off from Caldas. Pre-1966 back-cast rows route to this polity under `back_cast` but do not extend its nominal span — the same treatment given to Cesar and Chocó, so the pattern is not novel to this entry.

## Open questions

### oq-polygon-source-unfetched

**No department-level polygon exists locally for Quindío; GADM ADM1 fetch needed**

The routing decision found that the locally cached gadm-4.1-adm1.gpkg is a subset covering only 81 countries, and Colombia has zero features in that cache, so no registered local source can currently supply Quindío's boundary. Cliopatria and cshapes-2.0 both cover COL only at whole-country granularity (the four national-era rows), never at department level, so construct_from_registered is not available either. GADM's global ADM1 layer is documented to include Colombian departments (commonly cited as feature COL.21_1 or similar for Quindío), and would be the natural fetch target — e.g. `gadm41_COL_1` from gadm.org — but this session did not verify GADM's current licence terms, so the routing decision correctly withheld a definite polygon_source and this page leaves `polygon_source: none` / `polygon_status: unassigned` pending that fetch. This mirrors the identical open item already recorded on sibling entries COL-CALDAS-1905-2025, COL-ANTIOQUIA-1886-2025 and COL-BOYACA-1886-2025.

### oq-confirm-1966-creation-year

**Confirm 1966 as Quindío's exact department-creation year against an authoritative Colombian legal source**

The routing decision's own routing_concerns flag this: 1966 is the commonly cited year for Quindío's creation as a department (Decree/Law separating it from Caldas), but this session has not checked the exact enabling legislation (date and law number) against a primary Colombian government or DANE source. If the true legal creation date differs — for instance if it fell in late 1966 or 1965 depending on the source consulted — both this entry's start_year and the back_cast/observed split point for the underlying data would need to move accordingly, and the polity_code itself would need to change to match, since the code's years are gated against the frontmatter.

### oq-fallback-rows-unclassified

**1.0% of source rows are flagged fallback (unspecified method) and could predate or postdate the 1966 split ambiguously**

The routing decision reports that roughly 1% of rows use an unspecified 'fallback' method rather than the dominant interpolated_scaled/scaled back-cast methods. It is not established whether these fallback rows are genuine post-1966 observed records for Quindío, pre-1966 records under some other territorial label that were force-matched here, or something else entirely. Until someone inspects these rows directly, there is a small chance a handful of them are misrouted either into or out of this polity, which would not be visible from the aggregate method-share statistics alone.

### oq-risaralda-same-1966-split-not-yet-created

**Risaralda, split from Caldas in the same 1966 reform, is not yet a row in this table**

Colombian administrative history records that both Quindío and Risaralda were carved out of Caldas's original territory in 1966 (per the sourced claim already on COL-CALDAS-1905-2025). This pass creates Quindío but Risaralda does not yet have a corresponding COL-RISARALDA-* entry. If Risaralda-labelled data exists in the same source and is currently still routed to COL-CALDAS-1905-2025 or to the national COL-1922-2025 row, it is misassigned in the same way Quindío's data was, and a parallel routing decision for Risaralda should be expected in a future pipeline pass.
