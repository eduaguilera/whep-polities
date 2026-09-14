---
polity_code: ARG-FORMOSA-1955-2025
polity_name: Formosa (province of Argentina)
start_year: 1955
end_year: 2025
type: subnational
iso3: ARG
continent: South America
cow: NA
status: draft
last_ingest: 2026-09-11
sources: [juan-subnational]
polygon_source: gadm-4.1-adm1
polygon_feature_id: null
polygon_feature_year: null
polygon_status: unassigned
predecessor: []
successor: []
container:
  - code: ARG-1902-2025
    start_year: 1955
    end_year: 2025
    basis: Formosa remained a constituent unit of Argentina under the 1902-2025 national polity era after Ley 14408 (1955) elevated it from Territorio Nacional to province; no national-era boundary falls within this span
---

# Formosa (province of Argentina)

## Summary

This entry covers Formosa as a full Argentine province, from Ley 14408's 1955 provincialization -- which converted the federally-administered Territorio Nacional de Formosa into a self-governing province with its own elected governor, constitution, and legislature -- to the present. type is subnational because Formosa has never held sovereignty of its own: it has always been a constituent unit of Argentina, and this row exists to carry the province-era reporting territory as distinct from both the pre-1955 national-territory era and the national ARG chain, the same reasoning already applied to sibling entries such as ARG-CHUBUT-1884-2025 and ARG-NEUQUEN-1884-2025 (whose own 1955 provincializations they treat as continuous with their pre-1955 territorial phase, choosing a single row). Formosa is coded here as a two-era split rather than one continuous row because the sibling page ARG-FORMOSA-1900-1955 already exists covering the pre-1955 Territorio Nacional phase under that convention, and this page's own predecessor task explicitly reserved the 1955-2025 continuation as a follow-on entry rather than retroactively merging the two -- a choice recorded as an open question below, since ARG-CHUBUT and ARG-NEUQUEN show the single-row alternative was available and arguably more consistent.

**Why this entry exists.** This entry captures the post-1955 continuation of Argentine subnational time-series data (source juan-subnational, per the routing decision that also produced ARG-FORMOSA-1900-1955) for the province of Formosa. The routing verdict that authored the earlier, pre-1955 page explicitly flagged that a second proposed polity for the 1955-2025 province stage was required but could not be included in that single-object schema submission; this page is that follow-on entry, closing the gap the earlier page's own open question (oq-province-stage-successor) named. Before this split, data for province-era Formosa (1955 onward) would otherwise have had nowhere distinct to route except the national ARG-1902-2025 row, which is roughly fifteen times the territory these figures actually describe -- the same over-broad-container problem the pre-1955 page was created to fix for the earlier era. What confirms Formosa is a distinct entity worth its own row, separate from a generic Argentina-wide bucket, is that it is one of Argentina's 23 formally constituted provinces, each maintained as a distinct unit in INDEC's provincial statistical reporting with its own government since 1955 -- not a contested or ambiguous administrative unit, and the same country convention already applied to every other Argentine province split out in this batch.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is attached in the GeoPackage for this period. The polygon route is registered_source_unfetched: gadm-4.1-adm1 (GADM 4.1 admin-1 boundaries) is the correct registered source class for a first-level Argentine administrative division like the modern province of Formosa, but the local extract at data/geodata/gadm-4.1/gadm41_adm1.gpkg is a curated 81-country subset that does not currently include Argentina at all (0 ARG features present, matching the state already documented on the predecessor page). Per the harness's rule for this route, polygon_source is set to the registered slug gadm-4.1-adm1 itself, and polygon_status is unassigned since no feature can be cited yet, not proxy or assigned.

**Territory description:** The province of Formosa occupies Argentina's far north, in the Gran Chaco region, bounded by the Pilcomayo River (Paraguay) to the north, the Paraguay River (Paraguay) to the northeast, Chaco province to the south, and Salta province to the west. Its capital is the city of Formosa on the Paraguay River. The province covers approximately 72,000 km2 on modern maps. Because no polygon is attached to this entry, that figure describes where a reader can locate the unit on a present-day map, not a measurement of any geometry held by this page. Since this entry's span begins at the 1955 provincialization itself, the modern province boundary is a closer match in principle than for the pre-1955 Territorio Nacional era, but that assumed continuity is unconfirmed against a primary source (see open questions).

## Predecessors and successors

Predecessor: this row should link to ARG-FORMOSA-1900-1955, the Territorio Nacional era that Ley 14408 (1955) converted into the province this entry covers, but that field is left empty here. The predecessor page's own successor field is empty (it could not name a province-stage code that did not yet exist when it was authored), and validate_chain_integrity rejects an edge asserted by only one side. Setting predecessor here without first editing the other page to add successor: [ARG-FORMOSA-1955-2025] would recreate exactly the one-directional-edge failure a previous submission of this page was rejected for. No successor: this entry runs to the present (end_year 2025) as the current province.

## Sourced claims

- Ley 14408 of 1955 elevated the Territorio Nacional de Formosa to provincial status as the Province of Formosa, the event that sets this entry's start_year at 1955 -- the same law cited as the end_year basis on the sibling predecessor page ARG-FORMOSA-1900-1955.
- Formosa is one of Argentina's 23 provinces (plus the Autonomous City of Buenos Aires), each with its own constitution, elected governor, and legislature, and each reported as a distinct unit in INDEC's national statistical system -- the basis for treating post-1955 Formosa as a reporting territory distinct from the national ARG chain.

## Decisions

### d-predecessor-left-empty

**Left predecessor empty rather than declaring an asymmetric edge to ARG-FORMOSA-1900-1955**

A previous submission of this page declared predecessor: [ARG-FORMOSA-1900-1955], but that page declares successor: [] rather than pointing back here, and validate_chain_integrity counts an edge against a baseline in both directions -- an edge only one page asserts fails the gate. Since this task cannot edit the other page, the correct fix is not to guess or force the claim but to drop it and record the exact two-sided edit a future task needs to make (see oq-predecessor-edge-missing): first add successor: [ARG-FORMOSA-1955-2025] to wiki/polities/arg-formosa-1900-1955.md, then add predecessor: [ARG-FORMOSA-1900-1955] here, in the same change so neither side is ever asserted alone.

### d-code-choice

**Followed the dominant <ISO3>-<SUBUNIT>-<start>-<end> pattern, matching the predecessor page's own reasoning**

Formosa is a standard Argentine province, not a historical territory with a name of its own outside being an Argentine administrative unit, so it follows the 428-row dominant pattern rather than a bespoke code. ARG-FORMOSA-1955-2025 was checked against the current wiki/polities and pipelines/agent-harness state directories and is free; ARG-FORMOSA-1900-1955 already exists for the pre-1955 era, so this code is the natural pairing rather than a reused bespoke slot.

## Open questions

### oq-predecessor-edge-missing

**The 1900-1955 predecessor page does not yet assert its successor edge back to this row**

ARG-FORMOSA-1900-1955 covers the Territorio Nacional era ending in 1955 when Ley 14408 provincialized Formosa, exactly where this page's span begins, but that page's successor field was deliberately left empty at authoring time (recorded there as oq-province-stage-successor) because the province-stage code did not exist yet. Now that ARG-FORMOSA-1955-2025 exists, a future task needs to edit wiki/polities/arg-formosa-1900-1955.md to set successor: [ARG-FORMOSA-1955-2025], and only then can this page's predecessor field be set to [ARG-FORMOSA-1900-1955] in the same change -- doing only one side would recreate the exact one-directional-edge failure that got a previous version of this page rejected.

### oq-polygon-unfetched

**gadm-4.1-adm1 still does not include Argentina in the local extract**

Same underlying gap already documented on the predecessor page: gadm-4.1-adm1 is the correct registered source class for a first-level Argentine administrative division like the modern province of Formosa, but the local file data/geodata/gadm-4.1/gadm41_adm1.gpkg is a curated 81-country subset that does not currently include Argentina (0 ARG features). Since this page covers 1955-2025, the modern province boundary GADM would supply is an even closer match than for the pre-1955 territory, making it worth prioritizing the Argentina fetch specifically to unblock this row and its sibling once someone adds the country to the extract.

### oq-1955-boundary-continuity

**Whether provincialization in 1955 changed Formosa's boundaries at all is unconfirmed**

This page assumes territorial continuity across the 1955 Ley 14408 event -- that provincialization was a change of constitutional status (appointed territorial governor to elected provincial governor with a legislature) rather than a boundary change, mirroring how ARG-CHUBUT-1884-2025 and ARG-NEUQUEN-1884-2025 treat their own 1955 elevations as non-territorial. That assumption is not sourced here to a primary legal text for Formosa specifically, only inferred by analogy to those sibling provinces. If Ley 14408 or a later delimitation act moved Formosa's border with Chaco or Salta, the 72,000 km2 modern-map description in this page would not describe the 1955 boundary as delimited, only the present one.
