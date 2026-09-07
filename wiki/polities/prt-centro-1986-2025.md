---
polity_code: PRT-CENTRO-1986-2025
polity_name: Centro (NUTS II region of Portugal)
start_year: 1986
end_year: 2025
type: subnational
iso3: PRT
continent: Europe
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: none
polygon_feature_id: null
polygon_feature_year: null
polygon_status: unassigned
predecessor: []
successor: []
container:
  - code: PRT-1800-2025
    start_year: 1986
    end_year: 2025
    basis: Centro is a NUTS II statistical region inside the sovereign Portuguese state throughout its existence; no change of sovereign container occurs across the span.
---

# Centro (NUTS II region of Portugal)

## Summary

Centro is one of Portugal's NUTS II statistical regions, covering the west-central strip of mainland Portugal between the Lisbon Metropolitan Area to the south and the Norte region to the north — districts and sub-regions including Coimbra, Aveiro (partly), Leiria, Viseu, Guarda, Castelo Branco and the Beira interior. It is a `type: subnational` entry, not a sovereign polity: Portugal held (and holds) sovereignty over this territory throughout, and the entry exists purely to carry statistical reporting for a unit that Eurostat and national statistics tabulate separately from both the national total and from sibling NUTS II regions (PT_FA/Algarve, PT11/Norte, PT17/Lisboa, PT18/Alentejo). The NUTS classification for Portugal was introduced in 1986, coinciding with EU accession, so the region as a defined statistical unit — and therefore as a reporting territory that can be matched to data — does not exist before that year. start_year 1986 reflects that floor rather than any change in the underlying territory's population or economy, which of course existed long before. end_year 2025 (exclusive) is an open end, following the country convention applied to all still-current Portuguese NUTS entries: the region remains active and unresolved to a closing year.

**Why this entry exists.** This entry captures rows keyed to the Eurostat/PRT-Centro NUTS II reporting unit — a Portuguese sub-national statistical territory (admin_name PT16) with routed years spanning up to 1870-2020 in the source data, though only the 1986-2020 portion (32 years) is a genuine match to the region as defined; the pre-1986 portion (119 of 151 years, ~79%) was flagged by the harness as `unroutable` under the prior verdict, which was wrong: `unroutable` should mean no territory could ever carry the data, not that the classification naming the region postdates it. The pre-1986 years were previously left unmatched entirely, and before that (in an earlier, rejected proposal) had been routed to the national polity PRT-1800-2025 — which was wrong because a second, distinct NUTS II sibling unit (PT_FA/Algarve) also reports data against PRT-1800-2025 for overlapping years, and two distinct subnational territories cannot both be represented by the same national total for the same span without double-counting. Eurostat's own NUTS classification, in continuous use as the EU's statistical geography since 1986 and applied by Portugal's national statistics institute (INE) to organize regional accounts, confirms Centro as a distinct, persistently-tracked reporting unit distinct from its NUTS II siblings and from the national aggregate — this is the historical source establishing it as a separate entity for the routing decision. The pre-1986 years remain a genuinely open problem, noted below, rather than silently dropped or misrouted.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon available in the GeoPackage for this period. The polygon route selected by the pipeline was `new_source_needed`: the only sub-national boundary source currently present in this repository, `gadm-4.1-adm1`, is a curated 81-country subset that does not include Portugal at all, and no other registered source (cshapes, paine, cliopatria, histogis, reporting-areas, constructed) models Portuguese NUTS regions or offers province/district features that could be unioned to approximate one. `polygon_source` is therefore `none` and `polygon_status` is `unassigned`, per the routing rule that `new_source_needed` cases carry no source field value (not the route name itself, which is not a registered slug). A genuine boundary for Centro does exist outside this repository: Eurostat/GISCO publishes official NUTS statistical unit shapefiles (https://ec.europa.eu/eurostat/web/gisco/geodata/statistical-units/territorial-units-statistics), including Portugal's NUTS II regions back to the 1986 classification, and that is the candidate source recorded as an open question below rather than adopted here, since its licence has not yet been verified for use in this repository and its boundary vintage has shifted (notably a 2013/2015 revision affecting Centro's own extent, when Médio Tejo sub-region moved between Centro and Lisboa classifications).

**Territory description:** Centro occupies the west-central part of mainland Portugal, running from the Atlantic coast around Aveiro and Figueira da Foz inland to the Spanish border districts of Guarda and Castelo Branco, bounded by Norte to the north and the Lisbon Metropolitan Area/Alentejo to the south. It includes the cities of Coimbra, Aveiro, Leiria, Viseu, Covilhã and Castelo Branco. Under the NUTS 2013 revision (the vintage covering most of this entry's span) Centro's area is approximately 23,700 km², a reader can locate it on a modern map as the districts of Aveiro (partial), Coimbra, Leiria, Viseu, Guarda and Castelo Branco. No polygon is attached to this entry, so no geometry-measured figure is reported here — the ~23,700 km² figure above is a description of the modern statistical territory from published Eurostat/INE regional profiles, not a measurement of any attached shape.

## Predecessors and successors

No predecessor entry: the pre-1986 span for this territory is not currently covered by any polity in this database (see open question on the unrouted pre-1986 years). No successor entry: the region remains current as of the data horizon, so `end_year` is an open 2025 per the country convention, and no dissolution or reorganisation into a successor unit has occurred.

## Sourced claims

- Eurostat introduced the NUTS (Nomenclature of Territorial Units for Statistics) classification for Portugal in 1986, coinciding with Portugal's accession to the European Economic Community, establishing Centro as one of Portugal's NUTS II regions.
- The NUTS 2013 revision moved the Médio Tejo sub-region's classification, changing Centro's boundary and area relative to earlier NUTS vintages — meaning a single present-day Eurostat/GISCO shapefile vintage would not correctly represent Centro's extent across the full 1986-2025 span if adopted without noting the vintage.

## Decisions

### d-code-not-iso3-subunit-pattern

**Used PRT-CENTRO-<years> instead of the dominant PRT-<2-letter>-<years> pattern**

The dominant subnational pattern observed in the table (57 of 66 rows) is <ISO3>-<SUBUNIT>-<start>-<end> with a short subunit code, e.g. ESP-AS-1833-2025. Since PRT has no existing subnational precedent to match (0 existing rows), I chose CENTRO as the subunit token rather than inventing an opaque 2-letter abbreviation, because Eurostat's own NUTS code for this region is PT16 / PT2 (not a memorable short string) and 'Centro' is the name actually used in every English-language source describing the region. This keeps the code human-legible while still following the <ISO3>-<SUBUNIT>-<start>-<end> shape overall, so no bespoke break from the dominant pattern was needed.

## Open questions

### oq-precentro-1870-1985-unrouted

**119 of 151 data years (1870-1985) for this unit remain unrouted**

The routing decision reports that the source data for unit PT16/Centro spans 1870-2020, but only 1986-2020 (32 years) is captured by this entry, matching the NUTS classification floor. The remaining 119 years (1870-1985, ~79% of the unit's data) were marked `unroutable` by a prior verdict, which the harness flagged as likely wrong: the source measured something in those years, so either an earlier Portuguese administrative territory (a historic district grouping such as Coimbra/Aveiro/Leiria/Viseu/Guarda/Castelo Branco districts, which existed well before 1986) should be identified and given its own polity row or an earlier start_year, or the pre-1986 data belongs to a different, currently unidentified reporting unit. This entry deliberately does not attempt that resolution — no district-level historic predecessor was proposed in the routing decision — so the pre-1986 span is left as unrouted, undropped data pending a future investigation into what territory (if any) reported it.

### oq-polygon-vintage-and-licence

**No verified, licensed boundary source for Centro is registered in this repository**

Eurostat/GISCO NUTS shapefiles are the obvious real-world boundary source for this exact territory, but they are not yet registered in this repository, and their licence for redistribution/use here has not been checked. Separately, Centro's own boundary shifted under the NUTS 2013 revision (the Médio Tejo sub-region moved), so even once a source is registered, a decision is needed on which vintage (pre- or post-2013) best represents the 1986-2025 span, or whether two period-specific features are needed.
