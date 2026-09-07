---
polity_code: COL-NARINO-1904-2025
polity_name: Nariño (department of Colombia)
start_year: 1904
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
  - code: COL-1903-1922
    start_year: 1904
    end_year: 1922
    basis: Nariño was separated from Cauca department in 1904, within the national era covered by COL-1903-1922 (Panama's 1903 secession to the 1922 US-Colombia treaty ratification)
  - code: COL-1922-2025
    start_year: 1922
    end_year: 2025
    basis: Nariño remains a current department of Colombia within the modern national row, open-ended (end_year 2025) as still-current
---

# Nariño (department of Colombia)

## Summary

Nariño is a department in the far southwest of Colombia, on the border with Ecuador and fronting the Pacific Ocean, whose capital is Pasto. It was constituted as a separate department in 1904 by separation from the larger Cauca department, well before this unit's 1915-2023 statistical data span and well before Colombia's 1991 constitutional reorganization that elevated several former national territories (intendencias/comisarías) to department status. This entry is `type: subnational` because Colombia held sovereignty throughout 1904-2025 — Nariño was never itself a sovereign state — but it is nonetheless a distinct administrative and statistical reporting unit that agricultural, trade, and population data are tabulated against separately from national Colombia totals. No existing polity in the table IS the department itself: the national COL-* rows (successive national eras from 1830 through 2025) contain Nariño but are roughly thirty times its area, and none of them represents the department alone. This mirrors the resolution already applied to sibling Colombian departments (Antioquia, Atlántico, Bolívar, Boyacá, Caldas, Cauca) created in the same pipeline pass for the identical reason: a reporting unit smaller than the national total, with no existing polity representing it, and long predating the 1991 departures that reset the country convention's default start-year rule for newer departments.

**Why this entry exists.** The pipeline's routing decision (unit_id COL-NARINO) identified rows labelled with a Nariño-specific admin name in Colombian country data spanning 1915-2023, previously matched only to the national COL-* rows (COL-1903-1922 or COL-1922-2025 depending on year), which are national totals for the whole of Colombia and therefore roughly thirty times Nariño's own area (Colombia ~1,141,748 km2; Nariño ~33,268 km2). No existing polity in the table IS Nariño specifically — the national COL-* rows are successive national eras and none represents this department alone, and none of the sibling department rows created in this same pass (Antioquia, Atlántico, Bolívar, Boyacá, Caldas, Cauca) covers this territory either. Nariño's status as a distinct, long-standing administrative unit is supported by its 1904 creation via separation from Cauca department, well before this unit's 1915-2023 data window begins and well before the 1991 constitutional reorganization that created a distinct, later cohort of Colombian departments (the country convention's stated "1991 departures") — Nariño is explicitly not among that later cohort. This follows the same create_new resolution the pipeline applied to the sibling departments in the same pass: a reporting unit smaller than the national total, predating its own data window, with no existing polity representing it.

## Territorial extent

**Polygon:** `polygon_status: unassigned`. The routing decision classified this as `registered_source_unfetched`: `gadm-4.1-adm1` is the registered source family this repository already uses for other countries' ADM1-level department/province polygons, but the locally cached `gadm-4.1-adm1.gpkg` covers only an 81-country subset that excludes Colombia (0 features for COL currently). The remedy is to fetch Colombia's ADM1 data from GADM (e.g. `gadm41_COL_1`) rather than construct a new source or borrow a polygon from elsewhere in the table. No polygon is assigned by this page; `polygon_feature_id` is left null pending that fetch, and no area is recorded since none has been measured — nothing here should be read as a measurement, only as a description.

**Territory description:** Nariño occupies Colombia's far southwest, bordering Ecuador to the south, Cauca department to the north and east, Putumayo to the east, and the Pacific Ocean to the west, with its capital Pasto in the eastern Andean portion of the department. Its present-day area is approximately 33,268 km2 — about 2.9% of Colombia's national total of approximately 1,141,748 km2. The department's boundary has seen adjustments since its 1904 creation, particularly on its eastern edge where later administrative divisions and disputed jurisdiction with what is now Putumayo have affected the exact line; this entry does not attempt to model any such change across the 1904-2025 span, and the eventual GADM proxy will reflect only the present-day boundary.

## Predecessors and successors

No predecessor or successor rows are set. Nariño does not descend from a distinct prior polity in this table in the sense of a rupture requiring a predecessor edge: before 1904 its territory was part of the larger Cauca department (itself represented elsewhere in this table by its own department-level row), and the 1904 separation is treated as Nariño's founding rather than a continuation warranting a predecessor link to COL-CAUCA. It has no successor because it remains a current Colombian department as of the 2025 end_year used across this table for still-open subnational units.

## Sourced claims

- Nariño department was created in 1904 by separation from Cauca department, per the routing decision's stated administrative-history reasoning (unverified against a specific primary source, see open questions).
- Nariño's present-day area is approximately 33,268 km2 (IGAC/DANE department-area figures), located in southwestern Colombia bordering Ecuador and the Pacific Ocean, versus Colombia's national total of approximately 1,141,748 km2 — the department is roughly 2.9% of the country, which is why routing its data to the national COL-* rows would overstate its territory more than thirty-fold.

## Decisions

### d-follow-dominant-iso3-subunit-pattern

**Used <ISO3>-<SUBUNIT>-<start>-<end> rather than a bespoke code**

The polity code is COL-NARINO-1904-2025, following the dominant 57-of-66 pattern for subnational rows (e.g. ESP-AS-1833-2025, DZA-CVD-1902-1919, and the sibling COL-ANTIOQUIA-1886-2025) rather than a bespoke name-only code. Nariño is a standard department within Colombia's standing administrative hierarchy, not a historical territory with an identity independent of its containing state the way Alaska Territory or Hyderabad State were, so the bespoke-code exception (3 of 66 rows) does not apply. The subunit token NARINO is spelled without the tilde/diacritic, matching the ASCII-only convention already used for COL-ANTIOQUIA and other Colombian department siblings created in this same pipeline pass, since no other short-code convention has been established for COL subunits beyond that precedent.

### d-container-tiles-full-span

**Container chain covers 1904-2025 across two national eras with no gap**

Nariño's 1904-2025 span crosses two successive national containers already in the polity table: COL-1903-1922 (covering 1904-1922, since Nariño's 1904 creation falls inside this era's own 1903-1922 span) and COL-1922-2025 (covering 1922-2025, still current). One container edge is recorded per era, together tiling the full span with no gap, per the containment gate's requirement that each edge fall within both parties' own spans. The 1922 US-Colombia treaty ratification is the boundary the existing COL national rows already use to segment Colombia's own history at that point; Nariño's containment simply follows that same era boundary rather than inventing a new one.

### d-start-year-1904-not-1915

**Used the department's 1904 creation year, not the 1915 start of the routed data**

The routing decision's data span for this unit is 1915-2023, but the proposed start_year (and this page's start_year) is 1904, the year Nariño was constitutionally separated from Cauca department — matching the sibling convention (e.g. COL-ANTIOQUIA uses 1886, its constitutional founding year, not the earliest year of routed data) of dating a department polity to its administrative creation rather than to whenever the first surviving data row happens to begin. This keeps the code's year range describing the polity's actual existence, not an artefact of which years a particular dataset happened to sample.

## Open questions

### oq-1904-creation-year-unverified

**1904 creation date for Nariño rests on general historical knowledge, not a cited source**

The routing decision itself flags that the 1904 separation of Nariño from Cauca is based on general historical knowledge of Colombian administrative history, not a source document in the evidence packet reviewed for this routing pass. Colombian government references (e.g. DANE, DNP administrative-division histories) should be checked to confirm 1904 as the exact founding date and to rule out an earlier or later year before this is treated as settled. If a different year is confirmed, both the polity_code and the start_year/container basis in this page need to change together, since the code's years must match the frontmatter exactly.

### oq-gadm-col-fetch-pending

**GADM Colombia ADM1 data has not actually been fetched**

polygon_status is unassigned because gadm-4.1-adm1.gpkg's locally cached subset (81 countries) excludes Colombia entirely (0 features for COL). Until gadm41_COL_1 is fetched from gadm.org and added to the local source cache, this entry and its sibling Colombian departments (Antioquia, Atlántico, Bolívar, Boyacá, Caldas, Cauca) have no polygon at all, not even a proxy. It is also unconfirmed whether GADM's present-day Nariño boundary differs from its historical extent — Nariño's western border area has seen territorial disputes and adjustments (e.g. with Putumayo and Cauca) across the 1904-2025 span that a present-day GADM polygon would silently paper over for the earliest decades.

### oq-territory-loss-to-putumayo

**Whether Nariño's territory has shrunk since 1904 due to later department creations, unmodelled here**

Colombia created Putumayo as an intendencia/department later in the 20th century, and some sources describe parts of what is now Putumayo as having been administered from or disputed with Nariño earlier in the century. This page does not attempt to model any territorial reduction of Nariño across its 1904-2025 span; a single unassigned polygon proxy (once fetched) will represent only the present-day boundary, which may overstate or misdescribe Nariño's actual 1904-1920s extent. This mirrors the same class of caveat already recorded for COL-ANTIOQUIA and should be checked against a Colombian administrative-boundary-history source if precision for the earliest decades is ever required.
