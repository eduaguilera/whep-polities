---
polity_code: MEX-VERACRUZ-1824-2025
polity_name: Veracruz
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
    basis: Veracruz was one of the original states of the federation established by the 1824 Constitution, and the pre-1848 Mexico row covers the country before the loss of its northern territories in the Mexican-American War.
  - code: MEX-1848-2025
    start_year: 1848
    end_year: 2025
    basis: Continuous state of the federation inside post-1848 Mexico, unaffected by the northern territorial losses that define the 1848 boundary between the two national rows.
---

# Veracruz

## Summary

Veracruz is a Gulf-coast state of Mexico, one of the 19 original states created as constituent members of the federal republic by the Constitution of 1824, when the former Spanish colonial intendancy of Veracruz was reorganized into a state of the new federation. Unlike Baja California, Baja California Sur and Quintana Roo — which began as federal territories and were only admitted as states in the 20th century — Veracruz was a state from the federation's founding, so its start year follows the default rule of dating a state entry to 1824 rather than to a later territory-to-state conversion. `type: subnational` is used because Veracruz never held sovereignty of its own: sovereignty sits with the national Mexico chain (MEX-1800-1848, then MEX-1848-2025), and this entry exists purely to carry state-level reporting territory, the same purpose subnational rows serve elsewhere in this table (e.g. Manchuria under China). The state has existed continuously under this name and roughly this territory since 1824, through the Mexican-American War, the Reform, the Porfiriato, the Revolution and the modern federal era, so the span runs uninterrupted from 1824 to the present (end_year 2025, exclusive, per the open-ended-entity convention).

**Why this entry exists.** This entry gives Veracruz a subnational row distinct from the two existing national Mexico rows (MEX-1800-1848, MEX-1848-2025), the only Mexico-related rows in the polity table before this page. No prior entry represented any Mexican state individually, so any state-level Veracruz series in the source data would previously have had nowhere to route except the national rows, which are roughly 30 times Veracruz's area (Mexico ~1.96 million km2; Veracruz ~71,800 km2) and would badly overstate the territory a Veracruz-specific figure describes. The historical source confirming Veracruz as a distinct constituent entity is the Constitución Federal de los Estados Unidos Mexicanos of 1824 itself, which lists Veracruz among the original states of the federation, distinct from territories such as Alta California, Baja California, Colima, New Mexico and Tlaxcala. This entry was proposed by the agent-harness routing pipeline (unit_id MEX-VERACRUZ) ahead of any specific dataset already staged in this repository; no row count or source label is yet attached, so the immediate purpose is to register the polity and its territory ahead of any Veracruz-labelled series being routed to it.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is available in the GeoPackage for this period. The routing decision names gadm-4.1-adm1 (GADM 4.1 global admin-1 boundaries) as the correct source — Veracruz is a standard adm1 unit and GADM's schema (GID_1 id column) is the right shape of source — but the locally cached copy of gadm-4.1-adm1 only covers an 81-country subset that excludes Mexico entirely, so no feature id can be assigned yet. polygon_source: gadm-4.1-adm1 is recorded as the target source with polygon_status: unassigned rather than polygon_source: none, because the source is registered and known to model this territory correctly — it is simply not fetched for this country. Re-fetching the full/global GADM adm1 layer (or Mexico's country-specific GADM package) would supply the Veracruz feature directly.

**Territory description:** Veracruz (officially Veracruz de Ignacio de la Llave) is a narrow state running roughly 700 km along Mexico's Gulf coast, from the Pánuco river in the north (bordering Tamaulipas) to the Tonalá river in the south (bordering Tabasco), and inland to the eastern slopes of the Sierra Madre Oriental and the Cofre de Perote / Pico de Orizaba volcanic massif, bordering San Luis Potosí, Hidalgo, Puebla, and Oaxaca. Its capital is Xalapa; its largest port city is the city of Veracruz. The modern state covers approximately 71,800 km2. A reader can locate it on a modern map as the coastal strip directly east of Mexico City and Puebla, containing the port of Veracruz where Hernán Cortés first landed in 1519.

Boundary changes since 1824 are believed to be minor internal adjustments (e.g. 19th-century district reorganizations, and boundary disputes with Puebla and Oaxaca resolved in the 20th century) rather than large-scale territorial gain or loss, unlike Mexico's national boundary, which changed dramatically in 1848. A present-day GADM polygon for Veracruz is therefore expected to be a reasonable, though unverified, proxy for most of the 1824-2025 span once fetched — this is a vintage-risk judgment, not a confirmed proxy decision, and is flagged as an open question below.

## Predecessors and successors

No predecessor or successor rows exist: Veracruz has not been split off from, nor merged with, another entity in this table's period of coverage. It was not, itself, a colonial-era intendancy under a different code — the Spanish Intendencia de Veracruz that preceded the 1824 state is not separately represented here — so this entry's start year is anchored to the 1824 Constitution rather than to any earlier polity it replaces. It remains current, so it has no successor; end_year 2025 reflects the open-ended-entity convention rather than a dissolution.

## Sourced claims

- The Constitución Federal de los Estados Unidos Mexicanos of 1824 (Acta Constitutiva de la Federación, 31 January 1824, and the Constitución, 4 October 1824) lists Veracruz among the founding states of the federal republic, distinct from federal territories such as Alta California, Baja California, Colima, New Mexico and Tlaxcala.
- GADM 4.1 (gadm.org) publishes a global admin-1 layer with Mexican states identified by GID_1; the locally cached gadm-4.1-adm1 file in this repository (data/geodata/gadm-4.1/gadm41_adm1.gpkg) covers only 81 countries and does not include Mexico, per the routing decision's polygon_detail.

## Decisions

### d-code-with-subunit-suffix

**Used the dominant <ISO3>-<SUBUNIT>-<start>-<end> pattern rather than a bespoke code**

57 of 66 subnational rows in the table use <ISO3>-<SUBUNIT>-<start>-<end> (e.g. ESP-AS-1833-2025), and Veracruz is an ordinary administrative state with no separate historical identity as a polity (unlike bespoke cases such as Hyderabad or Ryukyu, which were distinct polities before incorporation). No existing subnational code exists for MEX, so this entry sets the country's precedent: MEX-VERACRUZ-1824-2025, using the full subunit name rather than an abbreviation since no other MEX rows exist yet to establish an abbreviation convention.

### d-start-year-1824-not-1848

**Start year is 1824, not 1848, requiring two container edges**

The routing decision's proposed span (1824-2025) and its proposed container_code (MEX-1848-2025) are inconsistent on their own: MEX-1848-2025 only begins in 1848, which would leave 1824-1848 uncontained if it were the sole container edge. The polity table shows a predecessor national row, MEX-1800-1848, covering exactly that gap. This entry therefore uses two container edges — MEX-1800-1848 for 1824-1848 and MEX-1848-2025 for 1848-2025 — so the full 1824-2025 span is tiled with no gap, as the containment gate requires.

## Open questions

### oq-gadm-mexico-fetch

**GADM 4.1 admin-1 data for Mexico has not been fetched into this repository**

The registered source gadm-4.1-adm1 is the right schema for this territory (Mexican states are standard GADM adm1 units, keyed by GID_1), but the cached local file only covers an 81-country subset that excludes Mexico. Until the full GADM adm1 layer or a Mexico-specific GADM package is fetched and added to data/geodata, this entry has polygon_status: unassigned and no polygon_feature_id. Whoever fetches it should also check GADM's licence terms (not verified in this session, per the routing decision's polygon_reasoning) before the polygon is relied upon downstream.

### oq-1824-boundary-precision

**Whether Veracruz's 1824 boundary matches the modern state, and by how much a GADM proxy would overstate or understate it**

The routing decision itself flags this as unconfirmed: whether Veracruz was named explicitly among the states in the 1824 Constitution (as opposed to being formed or admitted slightly later) has not been verified against the constitutional text directly, only inferred from general accounts of the 1824 federation. Separately, even if 1824 is correct, no source has been checked for whether Veracruz's internal boundaries (with Puebla, Oaxaca, Tabasco, San Luis Potosí) have shifted since 1824 in ways that would make a present-day GADM polygon a poor proxy for the earlier period — unlike Finland 1809-1917 where the territory is documented as essentially unchanged. This should be checked once a GADM feature is actually fetched and before the proxy is treated as valid rather than merely plausible.

### oq-no-data-routed-yet

**No dataset rows have actually been routed to this entry yet**

This page was created ahead of any specific Veracruz-labelled data series being matched to it (unlike the Manchuria exemplar, which cites specific mitchell/fao1952 row counts). It is not yet known which source(s) in this repository's data pipeline, if any, carry a Veracruz-specific label that should route here rather than to the national MEX rows. Until such rows are identified, sources in the frontmatter is empty and this entry's practical value is unproven; the next step is to check whether any staged dataset (e.g. a Mexican state-level agricultural or population series) actually needs this row.
