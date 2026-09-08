---
polity_code: COL-BOLIVAR-1886-2025
polity_name: Bolívar (department of Colombia)
start_year: 1886
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
  - code: COL-1830-1903
    start_year: 1886
    end_year: 1903
    basis: Bolívar was constituted as a department of the unitary Republic of Colombia under the 1886 Constitution, which container COL-1830-1903 (Colombia to 1903) still covers at its tail end
  - code: COL-1903-1922
    start_year: 1903
    end_year: 1922
    basis: Bolívar continued as a department of Colombia through the 1903-1922 national era, bounded by Panama's 1903 secession and the 1922 US-Colombia treaty ratification, the same era boundaries the existing COL national rows already use
  - code: COL-1922-2025
    start_year: 1922
    end_year: 2025
    basis: Bolívar remains a current department of Colombia within the modern national row, open-ended (end_year 2025) as the still-current polity
---

# Bolívar (department of Colombia)

## Summary

Bolívar is one of Colombia's original departments, on the Caribbean coast around Cartagena de Indias, the historic Province of Cartagena and later Estado Soberano de Bolívar under the 1863 federal constitution. It was reconstituted as a department under the centralizing 1886 Constitution that replaced the federal Estados Unidos de Colombia. This entry is `type: subnational` because Colombia held sovereignty throughout 1886-2025 -- the national COL chain already carries that -- while Bolívar is tracked separately because production/trade data sources report statistics at department level under a Bolívar-specific label, a reporting unit both smaller than, and administratively distinct from, the national totals COL-1922-2025 would otherwise absorb them into. Unlike Antioquia, whose boundary has been stable since 1886, Bolívar's territory has repeatedly shrunk: Atlántico split off in 1910, Córdoba in 1952, and Sucre in 1966, so "Bolívar" in the data can refer to substantially different areas depending on the year, a distinction this entry's single continuous span does not resolve.

**Why this entry exists.** This entry captures production/trade data rows reporting under a Colombian department-level label for "Bolívar", identified by the pipeline's routing decision (unit_id COL-BOLIVAR) as having no existing polity match. Previously, in the absence of any COL subnational entry, these rows would have matched only the national polity COL-1922-2025 (or its predecessor eras), conflating department-level reporting with all-Colombia totals roughly 18-35x larger depending on period, and making Bolívar's own data invisible once merged into the national figure. No existing polity in this database -- national or subnational -- carries any name match or administrative boundary feature for Bolívar specifically; the four COL-* rows are successive national eras and none represents the department alone. Bolívar's distinctness as a reporting/administrative unit is confirmed by its continuous, if territorially shrinking, existence as a Colombian department since 1886 (predated by its 1863-1886 status as the Estado Soberano de Bolívar), independently attested by standard treatments of Colombian administrative history (e.g. DANE's departmental gazetteer), which is why it is treated here as a stable subnational unit rather than folded into the national total. This mirrors sibling departments (Antioquia, Atlántico, Boyacá, Caldas, Cauca) this same pipeline pass resolved to create_new for the identical reason.

## Territorial extent

Polygon status: Not yet assigned. No polygon available in the GeoPackage for this period. GADM 4.1 admin-1 is the intended registered source -- the same source family used for other countries' ADM1-level department polygons -- but the locally cached gadm-4.1-adm1.gpkg is an 81-country subset that excludes Colombia entirely (0 features for COL), so no adm1 feature for Bolívar can be fetched today (registered_source_unfetched, not a missing-source case). No other registered source (CShapes, Cliopatria, Paine) carries Colombian department-level boundaries -- they hold only a single country-level COL feature -- so no proxy copy is possible either.

Territory description: Present-day Bolívar department covers roughly 25,900 km2 on Colombia's Caribbean coast, with Cartagena de Indias as its capital, bordered by Atlántico and the Caribbean Sea to the north, Sucre and Córdoba to the west and southwest, Antioquia and Santander to the south, and Cesar and Magdalena to the east across the Magdalena River. This present-day extent, however, is the post-1966 residual department after three successive splits: Atlántico (1910), Córdoba (1952), and Sucre (1966) were all carved from the original, much larger Bolívar. The 1886 department, before any of these splits, would have covered on the order of 51,000-52,000 km2 (present-day Bolívar plus Atlántico, Córdoba, and Sucre combined) -- roughly double the modern figure. No polygon is attached to this entry, so no measured km2 figure exists in this database for it yet; the ranges above are drawn from general geographic reference, not from any GeoPackage feature.

## Predecessors and successors

No predecessor or successor rows are set. Bolívar does not descend from a distinct prior polity in this table -- its pre-1886 existence as the Estado Soberano de Bolívar under the 1863 federal constitution is treated as administratively continuous with the post-1886 department (same core territory at that point, same name, no rupture in the data being routed here), so no predecessor edge is drawn rather than inventing one without a data-backed reason. It has no successor because it remains a current department as of the 2025 end_year used across this table for still-open units, despite having repeatedly shed territory to Atlántico (1910), Córdoba (1952), and Sucre (1966) -- none of those splits is modelled as a predecessor/successor edge on this page, since Bolívar itself was not abolished or renamed by any of them, only reduced in area.

## Sourced claims

- Colombia's 1886 Constitution replaced the federal Estados Unidos de Colombia (1863-1886), under which Bolívar held sovereign-state status as the Estado Soberano de Bolívar, with a unitary republic organized into departments, of which Bolívar was one from the outset.
- Bolívar's territory was reduced three times in the 20th century by the creation of new departments from its former area: Atlántico in 1910, Córdoba in 1952, and Sucre in 1966, each confirmed by Colombian administrative history and by the existence of the sibling entry COL-ATL-1910-2025 for the first of these splits.
- Present-day Bolívar's approximate area is 25,900 km2 per standard departmental references, versus an estimated pre-1910 extent on the order of 51,000-52,000 km2 including the territory later ceded to Atlántico, Córdoba, and Sucre -- meaning a single present-day GADM polygon, once fetched, would understate the department's early-span extent by roughly half.

## Decisions

### d-follow-dominant-iso3-subunit-pattern

**Used <ISO3>-<SUBUNIT>-<start>-<end> rather than a bespoke code**

The polity code is COL-BOLIVAR-1886-2025, following the dominant 57-of-66 pattern for subnational rows (e.g. ESP-AS-1833-2025, DZA-CVD-1902-1919) rather than a bespoke name-only code. Bolívar is a standard department within Colombia's standing administrative hierarchy, not a historical territory with an identity independent of its containing state the way Alaska Territory or Hyderabad State were, so the bespoke-code exception (3 of 66 rows) does not apply. The subunit token BOLIVAR is spelled out in full (no diacritic, ASCII-safe) rather than abbreviated, following the precedent set by the sibling row COL-ANTIOQUIA-1886-2025 authored in this same pipeline pass -- since this is only the second COL subnational row, the full-name convention from that sibling is followed rather than inventing a 2-3 letter abbreviation that would create an inconsistent mix within the same country.

### d-start-year-1886-not-1908-placeholder

**Used 1886 (constitutional default), rejecting the routing decision's 1908 placeholder**

The routing decision proposed start_year 1908, explicitly flagged in its own text as 'a placeholder pending confirmation of the precise creation year, not derived from the data's extract range,' and its routing_concerns asked whether siblings like Antioquia used the data's start year or a historically justified one. Antioquia's page (authored in this same pass) resolved that question by using 1886 -- the year the unitary Constitution replaced Colombia's federal sovereign states with departments -- as the country-wide default start rule for original departments. Bolívar was, like Antioquia, one of the historic Estados Soberanos under the 1863 federal constitution and became one of the original departments when the 1886 Constitution took effect, so the same default applies and 1886 replaces the unverified 1908 figure. This is left as an open question below rather than treated as settled, since no primary Colombian legal text was consulted directly.

### d-container-tiles-full-span

**Container chain covers 1886-2025 across three national eras with no gap**

Bolívar's 1886-2025 span crosses three successive national containers already in the polity table: COL-1830-1903 (covering 1886-1903), COL-1903-1922 (covering 1903-1922), and COL-1922-2025 (covering 1922-2025, still current). One container edge is recorded per era, together tiling the full span with no gap, per the containment gate's requirement that each edge fall within both parties' own spans. This mirrors the identical three-era tiling used on the sibling Antioquia entry, since both units cross the same national-era boundaries (Panama's 1903 secession, the 1922 US-Colombia treaty ratification).

## Open questions

### oq-start-year-1886-vs-federal-era

**Whether 1886 is the right start year versus Bolívar's earlier federal/colonial existence**

The proposed start_year of 1886 follows the country convention's default rule (constitutional creation of departments under the 1886 unitary reorganization) rather than treating Bolívar as continuous back through its 1863-1886 existence as the Estado Soberano de Bolívar, or further back to the colonial Province of Cartagena, which is the territory's much older historical identity. This entry does not attempt to model Bolívar under the earlier Cartagena provincial boundary. If Bolívar-labelled data rows exist before 1886, either the start_year should move earlier with a predecessor edge, or those rows need separate routing. This mirrors the identical unresolved question left open on the sibling Antioquia page and is not yet checked against the actual data being matched.

### oq-bolivar-territory-fragmentation-history

**Modern Bolívar's boundary reflects large 20th-century territorial losses this entry does not model**

Unlike Antioquia, whose boundary has been broadly stable since 1886, Bolívar has repeatedly lost territory to newly created neighbouring departments across this span: Atlántico separated in 1910 (see sibling entry COL-ATL-1910-2025), Córdoba separated in 1952, and Sucre separated in 1966. A single present-day GADM polygon, once fetched, would represent only the post-1966 residual Bolívar (~25,900 km2), silently misrepresenting the much larger 1886-1910 extent (~51,000-52,000 km2) if ever used as a proxy for those earlier decades without adjustment. This entry does not construct any period-specific polygon to address that, since no polygon is assigned at all yet; whoever eventually fetches or assigns a GADM feature for Bolívar must treat any use of it for pre-1966 years as a documented approximation, not a silent one.

### oq-gadm-col-fetch-pending

**GADM Colombia ADM1 data has not actually been fetched**

polygon_status is unassigned because gadm-4.1-adm1.gpkg's locally cached 81-country subset excludes Colombia entirely (0 features for COL). Until someone fetches gadm41_COL_1 from gadm.org and adds it to the local source cache, this entry and its sibling Colombian departments (Antioquia, Atlántico, Boyacá, Caldas, Cauca) have no polygon at all, not even a proxy. Given Bolívar's territorial losses noted above, whoever performs that fetch will also need to decide whether the present-day GADM Bolívar boundary is usable at all for the pre-1966 portion of this span, or whether a constructed union polygon (post-1966 Bolívar plus Atlántico, Córdoba, and Sucre) is needed to approximate the 1886-1910 extent.
