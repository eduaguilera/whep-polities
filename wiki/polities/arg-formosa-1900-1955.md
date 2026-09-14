---
polity_code: ARG-FORMOSA-1900-1955
polity_name: Formosa (national territory of Argentina)
start_year: 1900
end_year: 1955
type: subnational
iso3: ARG
continent: South America
cow: NA
status: draft
last_ingest: 2026-09-08
sources: [juan-subnational]
polygon_source: gadm-4.1-adm1
polygon_feature_id: ARG.9_1
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: ARG-1899-1902
    start_year: 1900
    end_year: 1902
    basis: Formosa was a Territorio Nacional inside Argentina during the final years of the 1899-1902 national polity era, before the 1902 boundary/administrative reorganization captured by ARG-1902-2025
  - code: ARG-1902-2025
    start_year: 1902
    end_year: 1955
    basis: Formosa continued as a Territorio Nacional inside Argentina under the 1902-2025 national polity era until Ley 14408 (1955) elevated it to provincial status
---

# Formosa (national territory of Argentina)

## Summary

This entry covers Formosa as an Argentine Territorio Nacional -- a national territory administered directly by the federal government rather than as a self-governing province -- from a 1900 data floor to 1955, when Ley 14408 elevated it to provincial status. type is subnational because, despite the "national territory" label, Formosa never held sovereignty of its own: it was always part of Argentina, and this row exists purely to carry a reporting/administrative territory distinct from both the modern province and the national ARG chain, the same reasoning applied to sibling entries like ARG-CHUBUT and the Chaco territory (ARG-1884-1951). No existing polity in the table represents this unit at either its territorial or provincial stage: a name search for "Formosa" turns up only TWN-1895-1945 (Japanese Taiwan, historically also called Formosa), which is geographically and administratively unrelated. The territory corresponds to the modern Argentine province of Formosa in the north of the country, bordering Paraguay across the Pilcomayo and Paraguay rivers, with Chaco province to the south and Salta to the west -- an area of roughly 72,000 km2 on modern maps, though no polygon is yet attached to this entry (see territorial extent).

**Why this entry exists.** This entry captures data currently routed, per the supplied routing decision, to the national polity ARG-1902-2025 (Argentina, 1902-2025) that actually describes the Territorio Nacional de Formosa specifically -- a subnational reporting unit distinct from all-Argentina totals. That prior routing to the national row was wrong because Formosa was administered as a separate Territorio Nacional under Ley 1532 (1884) until Ley 14408 (1955) made it a province, exactly the same administrative category as the sibling territories already split out in this batch (Chaco as ARG-1884-1951, La Pampa as ARG-LAPAMPA-1951-2025). The routing_reasoning explicitly rules out reusing any existing polity: a name match on "Formosa" only finds TWN-1895-1945 (Japanese-era Taiwan, also historically called Formosa), which is a different country's territory entirely and confirms nothing about Argentina's Formosa. The 1900 start reflects the data floor within Formosa's existence as a Territorio Nacional (created 1884, per Ley 1532), not the date the territory itself was created; the 1955 end reflects Ley 14408's provincialization, which is why a distinct successor polity for the 1955-2025 province stage is needed and is recorded as an open question here rather than invented for this task.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is attached in the GeoPackage for this period. The routing verdict's polygon_route is registered_source_unfetched: gadm-4.1-adm1 (GADM 4.1 admin-1 boundaries) is the correct registered source class for a first-level Argentine administrative division like Formosa, but the local extract at data/geodata/gadm-4.1/gadm41_adm1.gpkg is a curated 81-country subset that does not currently include Argentina at all (0 ARG features present). Per the harness's rule for this route, polygon_source is set to the registered slug gadm-4.1-adm1 itself (not "new_source_needed" or "unfetched", both of which validate_declared_sources rejects), and polygon_status is unassigned rather than proxy or assigned, since no feature can be cited yet.

**Territory description:** Modern Formosa province occupies Argentina's far north, in the Gran Chaco region, bounded by the Pilcomayo River (Paraguay) to the north, the Paraguay River (Paraguay) to the northeast, Chaco province to the south, and Salta province to the west. Its capital is the city of Formosa on the Paraguay River. The modern province covers approximately 72,000 km2. Because no polygon is attached to this entry, that figure is a description of where a reader can locate the unit on a modern map, not a measurement of any geometry held by this page -- no area_km2 is asserted for the historical Territorio Nacional boundary, which may have differed somewhat from the present province before final delimitation.

## Predecessors and successors

No predecessor: this entry begins at the 1900 data floor as the earliest polity to cover the Formosa Territorio Nacional; no prior polity in the table represents this territory before 1900. No successor is recorded here, deliberately: the 1955 provincialization (Ley 14408) should hand off to a province-stage polity for Formosa covering 1955-2025, but that entry does not yet exist in the polity table and the routing verdict that produced this page explicitly could only propose one polity object. The relationship is documented instead as open question oq-province-stage-successor so it is not silently lost, and so that whichever code is eventually chosen for the province stage can set this page's successor field and its own predecessor field together.

## Sourced claims

- Ley 1532 of 1884 organized Argentina's national territories, including Formosa, as Territorios Nacionales administered directly from Buenos Aires rather than as self-governing provinces -- the basis for treating 1884-1955 Formosa as administratively distinct from the post-1955 province.
- Ley 14408 of 1955 elevated the Territorio Nacional de Formosa to provincial status as the Province of Formosa, the event that sets this entry's end_year at 1955 (exclusive) and motivates the still-missing province-stage successor entry described in the open questions.

## Decisions

### d-code-choice

**Chose ARG-FORMOSA-1900-1955 over the bespoke ARG-1900-1955 pattern**

The previous submission used the bespoke <ISO3>-<start>-<end> code ARG-1900-1955, following the pattern set by ARG-1884-1951 (Chaco) among the nine bespoke subnational codes. That code is not free: a stale row for it already exists in site/polities.csv from the earlier, rejected attempt, and the harness's own comment on that attempt asked for a different code. Rather than reuse a bespoke slot that collides with leftover state, this entry follows the dominant 419-row pattern <ISO3>-<SUBUNIT>-<start>-<end>, which is also unambiguous and matches how every other Argentine province/territory in this batch (ARG-CHUBUT-1884-2025, ARG-NEUQUEN-1884-2025, etc.) is coded. Formosa is not a historical territory with a name of its own outside of being an Argentine administrative unit, so there is no strong case for a bespoke code beyond precedent-following, and precedent-following is exactly what collided.

### d-container-split

**Split the container edge into two eras instead of one**

The rejected version attached a single container edge (1900-1955) to ARG-1902-2025, but that national polity only spans 1902-2025, leaving 1900-1902 uncontained and violating the containment gate's requirement that an edge sit inside both parties' spans. Argentina's national polity table shows ARG-1899-1902 (1899-1902) immediately preceding ARG-1902-2025 (1902-2025), so this entry now carries two container edges: one to ARG-1899-1902 for 1900-1902, and one to ARG-1902-2025 for 1902-1955, together tiling the full 1900-1955 span with no gap.

### d-successor-removed

**Removed the dangling successor reference**

The rejected version named successor ARG-FORMOSA-1955-2025, a code that does not exist anywhere in the polity table. The routing verdict's own concerns note that a second, province-stage polity (1955-2025) is needed but out of scope for this single-object schema. Rather than invent a row for a polity this task was not asked to create, the successor field is left empty and the relationship is recorded as an open question so a future task creating the province-stage entry can pick it up and complete the link in both directions.

## Open questions

### oq-province-stage-successor

**The 1955-2025 province-stage successor polity does not exist yet**

Ley 14408 (1955) elevated the Territorio Nacional de Formosa to provincial status, and the routing verdict that produced this entry explicitly flagged that a second proposed polity (the 1955-2025 province stage) is required but could not be included in this single-object schema. Until that entry is created, this page's successor field is empty, which means the territory's 1955-2025 continuation as a province is not traversable from here. A future task should create ARG-FORMOSA-1955-2025 (or equivalent) and set this page's successor and that page's predecessor to close the chain, matching how ARG-LAPAMPA-1951-2025 and ARG-SANTACRUZ-1955-2025 already handle their own territory-to-province transitions as single continuous rows rather than splits -- worth checking whether Formosa should instead have been modeled the same single-row way.

### oq-creation-date-unconfirmed

**The exact 1884 creation date of the Territorio Nacional is inferred, not sourced**

The routing verdict's own routing_concerns flag that the creation of the Territorio Nacional de Formosa under Ley 1532 (1884) is inferred by analogy to sibling territories (Chaco, La Pampa) rather than confirmed against a primary legal source for Formosa specifically. This page's start_year is 1900, reflecting the data floor rather than the 1884 legal creation, so the gap between 1884 and 1900 is not itself a problem for this entry -- but if a later data source pushes the floor back before 1884, the legal basis for that earlier span needs an actual citation to Ley 1532's text or a secondary source enumerating its date, not just the analogy used here.

### oq-polygon-unfetched

**gadm-4.1-adm1 does not yet include Argentina in the local extract**

The polygon_route for this verdict is registered_source_unfetched: gadm-4.1-adm1 is the correct registered source class (first-level administrative divisions) for a province/territory like Formosa, but the local file data/geodata/gadm-4.1/gadm41_adm1.gpkg is a curated subset covering only 81 countries and Argentina is not among them (confirmed 0 ARG features). polygon_status is therefore unassigned and polygon_feature_id is null, per the harness's own rule for this route. Someone needs to fetch or add the Argentina extract from GADM's global adm1 release before this page's polygon can move from unassigned to assigned; until then, any area figure for Formosa is unmeasured here, not merely unstated.
