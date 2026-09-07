---
polity_code: USA-SOUTHDAKOTA-1889-2025
polity_name: South Dakota (state of the United States)
start_year: 1889
end_year: 2025
type: subnational
iso3: USA
continent: North America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: gadm-4.1-adm1
polygon_feature_id: USA.42_1
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: USA-1867-1959
    start_year: 1889
    end_year: 1959
    basis: South Dakota as a state inside the United States, from admission in 1889 to the 1959 database-row boundary for the national USA chain
  - code: USA-1959-2025
    start_year: 1959
    end_year: 2025
    basis: South Dakota as a state inside the United States, continuing under the post-1959 national USA row through the end of the covered span
---

# South Dakota (state of the United States)

## Summary

This row tracks South Dakota as a constituent state of the United States, from its admission to the Union on 1889-11-02 (one of the "omnibus" pair admitted alongside North Dakota, itself split from Dakota Territory) through the end of the covered span in 2025. South Dakota was never a sovereign entity; sovereignty belongs to the United States throughout. `type: subnational` is used for the same reason it is used for ALK-1867-1959 and HAWI-1898-1959: the entry exists to carry a reporting territory distinct from the national aggregate, not to compete with the national USA chain in sovereignty ranking. Before 1889 the area was part of Dakota Territory (organized 1861), administered from Yankton and later Bismarck; some agricultural series back-cast Dakota Territory data onto the eventual state boundary, which is why the data's own start year (1879, per the routing decision) precedes statehood — the entry follows the country's default admission-year start rule rather than the data's earliest observed year, consistent with the sibling case USA-CALIFORNIA -> create_new.

**Why this entry exists.** Input data: United States, South Dakota-labelled agricultural rows, reported under an admin_name of "SOUTH DAKOTA" spanning approximately 1879-2025 (per the routing decision's proposed span basis, back-cast Dakota Territory data before 1889 and continuous state-level reporting after). Exact row counts by source were not enumerated in the routing decision available to this page; that omission is flagged as an open question below. Previously, this data had no dedicated polity: the six existing USA-iso3 rows (USA-1800-1803 through USA-1959-2025, plus ALK-1867-1959) are either national totals for the whole country or the Alaska territory specifically, none of which IS South Dakota — routing South Dakota-specific series to a national row would merge a ~199,729 km2 state's figures into a ~9.4M km2 aggregate, the same sub-territory double-counting risk documented for Alaska and Hawaii. What confirms this is a distinct reporting unit: US state-level agricultural census and USDA statistics have tabulated South Dakota separately since territorial days, and the existing WHEP precedent for US states with dedicated data (ALK-1867-1959 for Alaska, and the sibling USA-CALIFORNIA decision referenced in the routing reasoning) establishes that state-level US reporting units get their own polity row rather than being absorbed into the national chain.

## Territorial extent

**Polygon status.** `Copied from` the registered GADM 4.1 admin-1 source, feature `USA.42_1` — South Dakota's modern state boundary. This is the `assigned` route (not a proxy): gadm-4.1-adm1 is already a registered source in `scripts/sources.yaml`, is present locally, and has exactly one matching feature for South Dakota, so the boundary is taken directly with no construction step, following the same source used for ALK-1867-1959 (feature USA.2_1).

**Territory description.** South Dakota occupies the north-central United States, bordered by North Dakota to the north, Minnesota and Iowa to the east, Nebraska to the south, and Montana and Wyoming to the west. It is bisected by the Missouri River and includes the Black Hills in the southwest. The state's boundaries have been fixed and unchanged since admission in 1889 — this is a case where a modern administrative polygon is an exact match for the historical territory, not merely a proxy, because US state lines are legally stable once set. Approximate area: **199,729 km2** (commonly cited land+water area of South Dakota), which the attached GADM geometry should reproduce closely; any measured figure from the attached polygon (`polygon_area_km2` in the frontmatter) is a measurement of that geometry and is not independent evidence of the state's legal area — it will simply confirm the well-known figure. South Dakota is roughly 1/47th the area of the USA-1867-1959 parent's ~9.4M km2 span, which is the scale relationship this entry exists to keep separate from the national aggregate.

## Predecessors and successors

No predecessor or successor polity row is set. Before 1889, South Dakota's territory was part of Dakota Territory (organized 1861, split into North and South Dakota Territory administratively well before the 1889 omnibus admission), for which no dedicated WHEP polity currently exists — pre-statehood data referencing "South Dakota" is back-cast onto this row's start year per the routing decision's span_basis rather than routed to a Dakota Territory predecessor, mirroring how ALK-1867-1959 leaves its Russian-America predecessor as the nearest existing row rather than inventing a territorial entity for a gap. After 2025 (the end of the covered span), South Dakota continues as a state; no successor row is needed since this entry's end_year is the database's own horizon, not a change of status.

## Sourced claims

- South Dakota was admitted to the Union on 1889-11-02 as the 40th state, in the same executive proclamation batch as North Dakota (the exact order of the two proclamations was deliberately concealed so neither could claim precedence). [Presidential Proclamation, 1889-11-02; US National Archives]
- GADM 4.1 admin-1 feature USA.42_1 delineates the present-day South Dakota state boundary, which has been unchanged since the 1889 admission act fixed the state's borders along the 43rd/45th parallels and the Missouri River/Big Sioux River lines. [GADM 4.1 release, 2022]

## Decisions

### d-code-pattern

**Polity code follows the <ISO3>-<SUBUNIT>-<start>-<end> minority pattern, not the dominant <ISO3>-<SUBUNIT>-2letter form**

Of the 66 subnational rows surveyed, 57 use a two-letter or short subunit abbreviation (ESP-AS, DZA-CVD). This entry instead spells out SOUTHDAKOTA in full, because United States states do not have an established short WHEP-internal abbreviation precedent the way Spanish provinces or Algerian departments do, and USPS-style two-letter postal codes (SD) risk collision with unrelated ISO or WHEP codes elsewhere in the table. The existing USA subnational precedent, ALK-1867-1959, is bespoke (not iso3-prefixed at all) because Alaska has a name of its own as a historical territory; South Dakota does not carry that kind of independent historical identity distinct from being 'the state of South Dakota', so the bespoke pattern was rejected in favor of keeping the ISO3 prefix and USA-SOUTHDAKOTA was chosen as the clearest non-colliding subunit token.

### d-container-tiling

**Two container edges are required to tile 1889-2025, not one**

The full span (1889-2025) crosses the boundary between the two national USA rows USA-1867-1959 (ends 1959) and USA-1959-2025 (starts 1959). A single container edge citing only one of these rows would leave the other half of the span uncontained and would be rejected by the containment gate for falling outside that party's own span. Two edges are therefore declared: USA-1867-1959 for 1889-1959, and USA-1959-2025 for 1959-2025, together covering the entry's full start_year to end_year with no gap, matching how the routing decision's proposed container_code (USA-1867-1959) only covers the first era and needed extending for the row to validate against the full 2025 end_year.

### d-start-year-vs-data

**start_year set to the 1889 admission year, not the data's 1879 start**

The routing decision explicitly flags that the data available for this unit begins in 1879, ten years before statehood, reflecting Dakota Territory-era data back-cast onto the eventual state boundary. Per the routing_reasoning and the country's documented default state-start rule (apply admission year unless enumerated as a departure like Alaska or Hawaii), South Dakota is not one of the enumerated departures, so the default rule applies and start_year is 1889 rather than 1879. The pre-1889 data years are therefore covered by this row's data ingestion but fall technically before its formal start_year -- this mismatch is called out explicitly as an open question rather than silently resolved, since back-cast administrative data predating the entity's assigned start is a recurring source of confusion in this database.

## Open questions

### oq-pre1889-data-gap

**Data years 1879-1888 predate this row's start_year but are attributed to South Dakota in the source**

The routing decision's span_basis states that the underlying data begins in 1879, reflecting Dakota Territory-era observations back-cast onto the eventual South Dakota state boundary, but this entry's start_year is set to 1889 (the admission year) per the default state-start rule. It is unresolved whether those 1879-1888 rows should instead be routed to a not-yet-created Dakota Territory polity (which would also need to cover North Dakota's identical pre-1889 data), left attached to this row despite predating its formal start_year, or dropped as out of scope. This mirrors the open question left unresolved on ALK-1867-1959 about its Russian-America predecessor gap, and should be resolved the same way once a Dakota Territory precedent (if any) is decided.

### oq-row-counts-unknown

**Exact source row counts and years for South Dakota-labelled data were not available to this page**

The page-requirements spec calls for stating the source, label, year range, and row count of the input data this polity captures. The routing decision supplied only the admin_name ("SOUTH DAKOTA"), country, and a proposed start_year/span_basis, without naming the underlying data source(s), specific labels used, or a row count. This page states the span (approximately 1879-2025) inferred from the span_basis text, but the actual source name, label text, and row count should be confirmed against the ingestion pipeline's routing_verdicts.csv or equivalent state file before this page is treated as fully sourced.

### oq-gadm-polygon-boundary-history

**GADM USA.42_1 has not been checked against any pre-1889 territorial boundary dispute**

South Dakota's borders were fixed at admission in 1889 and are treated here as unchanged since, but this has not been independently verified against a historical map of the 1889 admission act's described boundaries (e.g., the exact course along the Missouri River, Big Sioux River, and the 43rd parallel). Minor surveying adjustments or river-course changes between 1889 and the present (rivers can shift meander over a century) could introduce small discrepancies between the modern GADM polygon and the historical legal boundary; this is assumed negligible by analogy with ALK-1867-1959's treatment of its own post-1903 boundary but has not been separately confirmed for South Dakota.
