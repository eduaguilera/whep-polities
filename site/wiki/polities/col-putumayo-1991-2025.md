---
polity_code: COL-PUTUMAYO-1991-2025
polity_name: Putumayo (department of Colombia)
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
    basis: Putumayo was constituted as a department of Colombia in 1991 (Constitution of 1991, converting the former territorio nacional), and remains a department within the Republic of Colombia through the present; the container edge covers exactly the span this entry claims, since no earlier COL container era applies before the department existed.
---

# Putumayo (department of Colombia)

## Summary

Putumayo is a department in southwestern Colombia, in the Amazonian piedmont bordering Ecuador and Peru, with its capital at Mocoa. Before 1991 it held the status of territorio nacional (national territory), a category of sparsely populated frontier regions administered directly by Bogotá rather than through the ordinary departmental structure that covered the more populous core of the country. The 1991 Constitution of Colombia abolished the territorio nacional category and converted its remaining units, including Putumayo, into full departments with their own elected governor and assembly. This entry is typed `subnational` because Putumayo is, and has always been, a constituent unit of the sovereign Republic of Colombia (COL) rather than an independent state — the type records administrative-tier status, not statehood, and keeps this row from competing with the national COL polity in matching. The span (1991-2025) covers the period during which Putumayo has existed as a department in its modern institutional sense; the territorio nacional period before 1991 is administratively distinct and is treated separately (see predecessors/successors and open questions).

**Why this entry exists.** This entry captures Colombian departmental data for the modern department of Putumayo. Prior to this routing decision, no polity row existed for Putumayo specifically: the routing search found 0 name candidates and 0 matching GADM adm1 features among the already-registered/matched polities, meaning any data keyed to "Putumayo" would previously have fallen back to matching against the national total `COL-1922-2025`. That fallback was rejected as the wrong target because it repeats a known error pattern (rejected-coverage) in which every one of Colombia's ~32 departments would equally and indistinguishably claim the single national polygon and the national container, destroying the ability to attribute department-level statistics to their actual territory. What confirms Putumayo is a distinct, trackable reporting/administrative unit rather than an artifact of this pipeline is the country convention file itself, which explicitly names Putumayo among the departments with a non-default founding date (1991, as a former territorio nacional) — i.e., a maintained, pre-existing record already treats Putumayo as administratively distinct and dates its transition, independent of this specific ingest. The entry is created following the same precedent already established for sibling former territorios nacionales COL-CASANARE-1991-2025 and COL-CAQUETA-1981-2025.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon available in the GeoPackage for this period. The routing decision identified `gadm-4.1-adm1` as the correct registered source type (GID_1-keyed modern department boundaries, the same source type used for sibling departments), but the locally present gadm-4.1-adm1 file only covers a subset of 81 countries and excludes Colombia entirely (0 matching features). This is a `registered_source_unfetched` situation: the source slug and schema are right, but Colombia's GID_1 features (from the global GADM 4.1 release, or a COL-specific extract) have not yet been fetched into the local dataset, so no feature_id can be assigned and `polygon_status` is `unassigned` rather than `assigned` or `proxy`. No polygon area is reported here because none is attached to this entry.

**Territory a reader can locate:** Putumayo department occupies Colombia's southwestern Amazonian piedmont, stretching from the eastern slopes of the Andes (around Sibundoy and Mocoa) down into the Amazon lowlands, bordering Ecuador to the south and Peru to the southeast, and the Colombian departments of Nariño, Cauca, Caqueta, and Amazonas along its other edges. Its capital is Mocoa. The modern department covers approximately 24,900 km2 (a commonly cited official figure for present-day Putumayo; this figure is not derived from any polygon attached to this entry, since none exists yet, and should be verified against the GADM feature once fetched).

## Predecessors and successors

Putumayo has no predecessor or successor polity row in this database. Before 1991 it was governed as a territorio nacional (national territory) directly administered by the central government rather than as a self-governing department, and no separate WHEP entry currently exists for that earlier administrative status — the pre-1991 data for this area is a back-cast reconstruction discussed in the open questions, not a distinct predecessor polity. Since its 1991 creation as a department, Putumayo has continued without interruption to the present (2025), so this entry has no successor either; end_year 2025 marks the present, not a dissolution.

## Sourced claims

- The country convention file (pipelines/agent-harness/state/country_conventions.json) explicitly lists Putumayo among Colombian departments that departed from the default polity-start rule, dating its department status to 1991 as a former territorio nacional.
- Colombia's 1991 Constitution eliminated the territorio nacional category, converting the remaining national territories (including Putumayo, Casanare, Caqueta, Guainia, Guaviare, Vaupes, Vichada and Amazonas) into departments with elected governors, replacing the prior model of direct central-government administration.

## Decisions

### d-code-pattern-iso3-subunit

**Followed the dominant ISO3-SUBUNIT-start-end pattern, matching sibling territorios nacionales**

Putumayo has no prior WHEP polity row (0 name candidates, 0 GADM adm1 matches at ingest time), so this country sets no precedent of its own beyond the general convention. The code COL-PUTUMAYO-1991-2025 follows the dominant 57-of-66 pattern (<ISO3>-<SUBUNIT>-<start>-<end>) used for its direct siblings COL-CASANARE-1991-2025 and COL-CAQUETA-1981-2025, which are the same category of former territorio nacional promoted to department. Putumayo is an ordinary Colombian administrative department, not a bespoke historical territory with a name of its own outside the modern administrative hierarchy, so the bespoke-code pattern (used for entities like Alaska Territory or Hyderabad State) does not apply here.

## Open questions

### oq-putumayo-founding-date

**Confirm the exact 1991 founding date and constitutional article for Putumayo as a department**

The routing decision that created this entry notes the founding year (1991) is taken from the country convention's explicit departure list for territorios nacionales promoted to departments, consistent with the 1991 Colombian Constitution's abolition of the territorio nacional category, but no primary constitutional citation (article number, exact promulgation date) has been checked in this pipeline run. If a more precise date within 1991 or a different year emerges from a primary source, start_year and the polity_code must be updated together, since the years in the code must equal the years in the frontmatter.

### oq-putumayo-polygon-fetch

**GADM 4.1 ADM1 Colombia features are not yet fetched into the registered source**

polygon_source is set to gadm-4.1-adm1 with polygon_status unassigned because the locally registered gadm-4.1-adm1 file covers only a subset of 81 countries and does not include Colombia (0 matching features at routing time). The slug is registered and its schema (GID_1 as id_column) is appropriate for a modern department like Putumayo, but the actual Colombia GID_1 features (global GADM 4.1 release or a COL-specific extract) must be fetched before polygon_feature_id can be assigned and polygon_status can move to assigned. Licence terms for GADM 4.1 (free for non-commercial/academic use, redistribution restrictions) have also not been verified in this session.

### oq-putumayo-pre1991-data-coverage

**Pre-1991 back-cast data allocated onto the future department boundary is not covered by this entry's span**

Per the routing decision, roughly 74% interpolated_scaled + 24% scaled + 1% fallback of the source data for this territory predates 1991 and represents a back-cast reconstruction allocated onto Putumayo's future department boundary before the department formally existed (matching the pattern used for sibling territorios nacionales COL-CASANARE and COL-CAQUETA). Because start_year is fixed at 1991 to reflect the department's actual founding, this entry does not itself cover that pre-1991 back-cast period; whether that data should attach to a distinct territorio-nacional-era predecessor polity, or remain implicitly folded into the national COL container, is unresolved and not decided by this page.
