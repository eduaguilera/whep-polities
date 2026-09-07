---
polity_code: COL-VICHADA-1991-2025
polity_name: Vichada (department of Colombia)
start_year: 1991
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
  - code: COL-1922-2025
    start_year: 1991
    end_year: 2025
    basis: Vichada existed as a department inside the unitary Republic of Colombia from the 1991 Constitution onward, the same national era (COL-1922-2025) that has held since 1922; no national-level break occurs across this span.
---

# Vichada (department of Colombia)

## Summary

Vichada is a department in eastern Colombia, in the Orinoquia region bordering Venezuela along the Orinoco and Meta rivers. It was created as a full department by the 1991 Constitution, which converted several former national territories (intendencias and comisarías administered directly by Bogotá rather than through ordinary departmental government) into departments with the same status as the rest of the country -- Vichada was one of this group, alongside Arauca, Casanare, Guainía, Guaviare, Putumayo and Vaupés. Before 1991 Vichada was a comisaría/intendencia, a distinct administrative tier with weaker self-government and direct national administration; that status is not represented by any existing polity in this database, so the pre-1991 portion of the historical data series for Vichada (which runs back to 1915) is not routed to this entry. `type: subnational` reflects that Colombia held sovereignty throughout and this row exists to carry the post-1991 department-level reporting unit, not a separate sovereign claim. `polygon_status: unassigned` because the department-level source that would supply this boundary, gadm-4.1-adm1, is registered in sources.yaml (with GID_1 as its id column, matching this exact administrative tier) but the locally fetched file is a curated 81-country subset that excludes Colombia entirely -- the source is named and vetted, it is simply not present in the local data yet, which is the registered_source_unfetched case rather than new_source_needed.

**Why this entry exists.** This entry captures the department-level administrative existence of Vichada from 1991, when the Constitution converted the former national intendencia/comisaría of Vichada into a full department with the same constitutional status as long-established departments like Antioquia or Boyacá. Before this entry was created, any statistical series reporting "Vichada" at department granularity had nowhere to go except the national row COL-1922-2025, which spans the whole country (roughly 1,142,000 km2) and so silently discards the fact that the data describes one department (~100,000 km2, under 9% of national territory). Routing department-level Vichada data to the national row would be wrong in the same way routing a province's data to its country row is wrong elsewhere in this database: it inflates the implied denominator by more than 10x. The 1991 Constitution itself is the historical source confirming this entity's distinctness -- it names Vichada in Article 309's list of former intendencias and comisarías elevated to departmental status, a legal and administrative change (new departmental assembly, governor, budget line) rather than a mere statistical relabeling. Colombia's own national statistics agency (DANE) has reported Vichada as a department-level unit in its territorial series since that date, which is the country's own primary confirmation that the unit is treated as distinct in official reporting, not just in this project's judgment.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon available in the GeoPackage for this period. The natural source is `gadm-4.1-adm1`, already registered for exactly this tier of unit (department/province boundaries, keyed on GID_1), but the locally fetched GADM 4.1 ADM1 file is a curated 81-country subset that does not include Colombia (0 features for COL in the local data). The source is registered and appropriate; it is simply unfetched for this country, so `polygon_source` is set to the slug itself (`gadm-4.1-adm1`) with `polygon_status: unassigned` rather than `none`, per the routing decision's `registered_source_unfetched` route. No other registered source in this project (cshapes-2.0, cliopatria) carries subnational Colombian units -- both are country-level only -- so no proxy or constructed polygon is available either.

**Territory description:** Vichada occupies the eastern plains (Llanos Orientales) of Colombia, bordering Venezuela to the east along the Orinoco River, with the Meta River forming part of its northern boundary and the Vichada River crossing the department. Its capital is Puerto Carreño. Vichada is one of Colombia's largest departments by area but among its most sparsely populated, consisting mostly of savanna and gallery forest. Its modern administrative area is approximately 100,242 km2 (about 8.8% of Colombia's roughly 1,142,000 km2 national territory) per DANE's official department-area figures -- this is a published administrative-boundary figure, not a measurement from any geometry attached to this entry, since none is attached yet.

## Predecessors and successors

No predecessor is set: the pre-1991 data for the same geographic area (Vichada as a national territory/intendencia/comisaría back to 1915) is deliberately left unrouted rather than linked as a predecessor, because that earlier administrative status -- direct national administration without departmental self-government -- is a distinct category this database does not yet model as its own polity type. No successor is set: Vichada remains a department of Colombia today, so this entry's `end_year: 2025` matches the open end of the current national era (COL-1922-2025) rather than marking any real institutional change.

## Sourced claims

- Article 309 of the 1991 Political Constitution of Colombia converts the intendencias and comisarías, including Vichada, into departments, effective with the Constitution's promulgation in 1991.
- DANE (Departamento Administrativo Nacional de Estadística), Colombia's national statistics agency, reports Vichada's departmental area as approximately 100,242 km2 in its official división político-administrativa (DIVIPOLA) territorial reference data.

## Decisions

### d-follow-dominant-pattern

**Used <ISO3>-<SUBUNIT>-<start>-<end> per the 57/66 dominant pattern**

Vichada is an ordinary first-order administrative department created by constitutional reorganization, not a historical territory with an identity of its own outside the modern Colombian administrative system (unlike the three bespoke-code cases such as Hyderabad or the Ryukyus). It therefore follows the dominant COL-VICHADA-1991-2025 pattern rather than a bespoke code, consistent with the other Colombian department rows being created in this same pipeline run (e.g. col-atl, col-cau, col-tolima).

### d-no-predecessor-link

**Left pre-1991 intendencia/comisaría period unlinked rather than assigning a predecessor**

The routing decision explicitly notes the pre-1991 data (back to 1915) cannot be routed to this department-level entry because the intendencia/comisaría administrative status is not represented by any existing polity. Rather than force a predecessor link to a national-territory-era row that does not exist, this entry leaves `predecessor` empty and records the gap as an open question, since inventing a predecessor row is a broader country-convention decision (whether to model intendencia-era territories at all) that this single-unit page should not resolve unilaterally.

## Open questions

### oq-pre1991-intendencia-unrouted

**Should the 1915-1991 intendencia/comisaría-era Vichada data get its own polity row?**

The data series for Vichada runs back to 1915, but from 1915-1991 Vichada held intendencia/comisaría status -- direct national administration, not full departmental self-government -- and no existing polity in this database represents that administrative tier for any of the seven former national territories (Vichada, Arauca, Casanare, Guainía, Guaviare, Putumayo, Vaupés). Currently that 76-year span of data for all seven units is left unrouted rather than assigned to either COL-1922-2025 (which would misattribute department-scale reporting to the whole country) or this entry (whose start_year excludes it by construction). This is a country-convention question broader than Vichada alone: if the project decides to model the intendencia/comisaría era as its own polity type, this entry's `predecessor` field and possibly its `start_year` should be revisited, and six sibling entries would need the same treatment.

### oq-gadm-fetch-needed

**GADM 4.1 ADM1 full/global release has not been fetched to supply Colombia**

The locally fetched GADM 4.1 ADM1 file is an 81-country curated subset that excludes Colombia, so no polygon can be assigned to this entry until the global GADM 4.1 ADM1 release (or a Colombia-specific extract) is fetched into the project's source data. Once fetched, the correct GID_1 feature for Vichada should be attached; vintage risk is believed low since Vichada's boundary has been stable since 1991, but this is unconfirmed until the actual feature is inspected against, e.g., any documented boundary adjustments with neighboring Meta or Guainía departments.
