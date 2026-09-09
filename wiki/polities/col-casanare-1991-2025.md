---
polity_code: COL-CASANARE-1991-2025
polity_name: Casanare (department of Colombia)
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
polygon_feature_id: COL.10_2
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: COL-1922-2025
    start_year: 1991
    end_year: 2025
    basis: Casanare was elevated from a national territory (comisaría/intendencia administered directly from Bogotá) to a full department of Colombia under the 1991 Constitution, entirely within the modern national era bounded below by COL-1922-2025's own 1922 start; the department remains current, so end_year 2025 is the open end used across this table for still-active subnational units.
---

# Casanare (department of Colombia)

## Summary

Casanare is a department in the Orinoquía (eastern plains/Llanos) region of Colombia, whose capital is Yopal. Like Arauca, Guainía, Guaviare, Putumayo, San Andrés and (on an earlier legal basis) Caquetá, Casanare spent most of the 20th century as a national territory (comisaría/intendencia) administered directly from Bogotá rather than as a self-governing department, and was only elevated to full departmental status under Colombia's 1991 Constitution. This entry is type: subnational because Colombia held sovereignty throughout — the row exists to carry the department-level reporting territory that production/trade statistics tabulate separately from national Colombia totals (already carried by the national COL-1922-2025 chain), not to compete for sovereignty ranking. The start_year of 1991, rather than the extract's earliest data year of 1915, reflects that legal elevation: the routing decision found the pre-1991 data (1915-1990) is 98% scaled/interpolated, the signature of a series back-projected onto a boundary (a department) that did not yet exist as a distinct administrative or reporting unit at the time — a back_cast onto this proposed polity, not a genuinely separate historical entity requiring its own predecessor row.

**Why this entry exists.** The pipeline's routing decision (unit_id COL-CASANARE) identified rows labelled with a Casanare-specific admin name in Colombian country data, spanning a data window described as 1915-2023, previously matched only to the national COL-1922-2025 row — a whole-of-Colombia total roughly 25 times Casanare's own ~44,640 km2 and therefore incapable of preserving Casanare as a distinct reporting series once merged. No existing polity in the table represents Casanare specifically before this batch; Colombia had zero subnational rows prior to this pipeline pass, so there was no competing entry to route to. Casanare's distinctness as a reporting/administrative unit is confirmed by its documented administrative history: a national territory (comisaría/intendencia) for most of the 20th century, elevated to full department status by the 1991 Constitution alongside a cluster of sibling frontier territories (Arauca, Guainía, Guaviare, Putumayo, San Andrés) whose parallel 1991 departure from the default start rule is already recorded in the pipeline's country convention file, per the routing decision's own span_basis. The routing decision explicitly departs from the sibling verdicts' 'unroutable' treatment of the pre-1991 segment, instead classifying 1915-1990 as back_cast (98% scaled/interpolated) reasoning that these rows back-project onto Casanare's modern boundary rather than describing a genuinely separate unrouted entity — a reclassification the routing_concerns field itself flags as needing maintainer confirmation.

## Territorial extent

Polygon status: Not yet assigned. No polygon available in the GeoPackage for this period. The routing decision classifies this as registered_source_unfetched: gadm-4.1-adm1 is the source family this repository already uses for other countries' department/province polygons, but the locally cached gadm-4.1-adm1.gpkg covers only a curated 81-country subset and Colombia is not among them (0 features for COL in the current cache) — the identical gap already documented on sibling entries COL-CAQUETA-1981-2025, COL-ANTIOQUIA-1886-2025, COL-ATL-1910-2025 and COL-BOYACA-1886-2025. The remedy is to fetch Colombia's ADM1 layer (gadm41_COL_1) from gadm.org under the same licence family already governing gadm-4.1-adm1, not to construct a substitute polygon; no other registered source (CShapes, Cliopatria, Paine) carries Colombian department-level boundaries. No polygon_area_km2 is recorded since no geometry is attached.

Territory description: Casanare occupies the eastern plains (Llanos Orientales) of Colombia, east of the Andean cordillera and west of the Orinoco basin proper. On a modern map it is bounded by Boyacá to the north and northwest, Arauca to the northeast, Vichada to the east, Meta to the south, and Cundinamarca to the southwest. Its capital is Yopal. It is one of Colombia's larger departments by area, approximately 44,640 km2, drained by tributaries of the Meta and Casanare rivers and known for cattle ranching, oil production (notably around Yopal and the Cusiana/Cupiagua fields), and llanero cultural traditions. This description is drawn from general geographic reference, not from any polygon attached to this entry — no geometry has been assigned, so no measured km2 figure exists in this database for it yet.

## Predecessors and successors

No predecessor or successor rows are set. Casanare does not descend from a distinct prior polity in this table: before 1991 it was administered as a national territory (intendencia/comisaría) directly under the Colombian national government rather than as a separate department-level polity, and that pre-1991 span is staged elsewhere in the pipeline as a back_cast segment rather than assigned to a predecessor row here (see open questions). Casanare has no successor because it remains a current department of Colombia as of the 2025 end_year convention used across this table for still-open subnational units.

## Sourced claims

- Casanare was one of Colombia's frontier territorios nacionales (national territories administered directly from Bogotá rather than as self-governing departments) and was elevated to full departmental status under the 1991 Constitution, part of the same wave that converted Amazonas, Arauca, Guainía, Guaviare, Putumayo and San Andrés from national territories into departments (paralleling, though on a later legal basis than, Caquetá's 1981 elevation by Ley 78).
- The routing decision's own extract for this unit spans 1915-2023 (per its stated data window) with the pre-1991 segment (1915-1990) dominated by scaled and interpolated methods (98% combined), the signature of a source back-projecting totals onto the modern departmental boundary before Casanare existed as a first-order administrative/reporting unit.

## Decisions

### d-follow-dominant-iso3-subunit-pattern

**Used <ISO3>-<SUBUNIT>-<start>-<end> rather than a bespoke code**

The polity code is COL-CASANARE-1991-2025, following the dominant 57-of-66 subnational pattern (e.g. ESP-AS-1833-2025, DZA-CVD-1902-1919) rather than a bespoke name-only code, and matching sibling Colombian department entries created in this same pipeline pass (COL-CAQUETA-1981-2025, COL-ANTIOQUIA-1886-2025, COL-ATL-1910-2025). Casanare is a standard department within Colombia's standing administrative hierarchy — it has no identity independent of its role as a Colombian department the way Alaska Territory or Hyderabad State did as historical polities with names of their own — so the bespoke-code exception (3 of 66 rows) does not apply. The subunit token CASANARE is spelled in full (unaccented ASCII), matching the pattern already used for CAQUETA rather than an abbreviation, since Colombian department names in this batch are being written out in full.

### d-start-year-is-1991-constitution-not-data-start

**start_year set to 1991 (constitutional departmental status), not the routing decision's earlier data years**

The routing decision documents the pre-1991 data (1915-1990) as 98% scaled/interpolated, the signature of a source back-projecting totals onto the modern Casanare boundary before it existed as a department, rather than of a genuinely distinct reporting unit existing that early. Casanare was one of the intendencias/comisarías (national territories administered directly from Bogotá, not self-governing departments) that the 1991 Constitution elevated to full departmental status, alongside Arauca, Guainía, Guaviare, Putumayo, San Andrés and — per the sibling entry created in this same pass — Caquetá (elevated earlier, in 1981, by ordinary law rather than by the constitutional reform). Following the same reasoning already applied to COL-CAQUETA-1981-2025 (whose start_year is its own 1981 legal elevation, not its extract's 1915 data floor), this entry's span starts at 1991 rather than at 1915, and the pre-1991 back-cast segment is left uncaptured by this page (see open questions) rather than folded into its span.

### d-single-container-edge-suffices

**Single container edge to COL-1922-2025 tiles the whole 1991-2025 span**

Casanare's 1991 start falls entirely inside the COL-1922-2025 national era (1922-2025), so one container edge covering 1991-2025 is sufficient and no gap is left; no edge into COL-1903-1922 or earlier eras is needed or valid, since 1991 postdates them by decades. This mirrors the single-edge treatment already used for COL-CAQUETA-1981-2025 and differs from COL-CALDAS-1905-2025, which required two edges because its start year fell inside an earlier national era.

## Open questions

### oq-1991-elevation-not-independently-verified

**1991 elevation to department status not verified against a primary Colombian legal source**

The routing decision's proposed span_basis cites 'the documented departure from the default start rule for former territorios nacionales' and asserts 1991 as Casanare's elevation year, following the pattern already established for the cluster of frontier territorios nacionales (Amazonas, Arauca, Guainía, Guaviare, Putumayo, San Andrés) that the 1991 Constitution converted into departments. This has not been checked here against the constitutional text itself or against DANE's departmental gazetteer for Casanare specifically. If Casanare's actual elevation happened under a different provision or year than the general 1991 constitutional cluster (as Caquetá's did, by separate 1981 ordinary law rather than the 1991 reform), both start_year and the polity code would need to change together, since the code-year gate requires them to match exactly.

### oq-pre1991-data-not-covered-by-this-entry

**1915-1990 rows for this unit are not represented by any polity row yet**

The routing decision's own reasoning notes the pre-1991 segment (1915-1990) is 98% scaled/interpolated — a back_cast of modern-boundary totals onto a period when Casanare was not yet a department — and the routing_concerns explicitly flag that 'back_cast is used here instead of the unroutable label the sibling verdicts used for the pre-1991 segment', asking a maintainer to confirm this reclassification is consistent with policy going forward. Whether that pre-1991 span should eventually become a second row (a national-territory-era predecessor entry, paralleling how comisaría-era predecessors are sometimes modelled for other frontier departments) or should simply remain routed to the national COL chain is unresolved and is not decided by this page.

### oq-country-convention-departure-list-status

**Casanare's presence in the country convention's departure list for national-territory-to-department cases has not been checked**

pipelines/agent-harness/state/country_conventions.json is stated by the routing decision to already document the 1991 departure convention for former territorios nacionales, but whether Casanare is explicitly named there (as opposed to Caquetá, which the sibling entry flagged as missing and requiring an explicit add) was not independently verified while authoring this page. If Casanare is absent from that list, the convention file should be updated so future routing passes do not have to re-derive this reasoning from scratch.

### oq-gadm-col-fetch-pending

**GADM Colombia ADM1 data has not been fetched, so no polygon exists**

polygon_status is unassigned for the same reason as every other Colombian department entry created in this pipeline pass (COL-CAQUETA-1981-2025, COL-ANTIOQUIA-1886-2025, COL-ATL-1910-2025, COL-BOYACA-1886-2025): the locally cached gadm-4.1-adm1.gpkg subset covers only a curated 81-country set and excludes Colombia entirely (0 features for COL). The routing decision's polygon_route of registered_source_unfetched and polygon_detail confirm gadm-4.1-adm1 is the correct eventual source family, via the candidate full/global GADM 4.1 release (gadm41_COL_1) rather than any construction from other registered sources, since no other registered source (CShapes, Cliopatria, Paine) carries Colombian department-level boundaries. Until that fetch happens, no polygon_area_km2 is recorded here.
