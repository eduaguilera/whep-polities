---
polity_code: FRA-CANTAL-1800-2025
polity_name: Cantal (département)
start_year: 1800
end_year: 2025
type: subnational
iso3: FRA
continent: Europe
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: gadm-4.1-adm2
polygon_feature_id: FRA.1.4_1
polygon_feature_year: null
polygon_status: assigned
predecessor: []
successor: []
container:
  - code: FRA-1800-1871
    start_year: 1800
    end_year: 1871
    basis: Cantal was one of the original ~83 départements created in the 1790 Revolutionary reform and sat inside metropolitan France, incl. Alsace-Lorraine, through this era
  - code: FRA-1871-1919
    start_year: 1871
    end_year: 1919
    basis: Cantal is landlocked in the Massif Central, unaffected by the 1871 loss of Alsace-Lorraine; it remained inside the reduced French national territory
  - code: FRA-1919-2025
    start_year: 1919
    end_year: 2025
    basis: Cantal continued inside reunified France after Alsace-Lorraine's return, through to the present
---

# Cantal (département)

## Summary

Cantal is a French département in the Massif Central, in the modern Auvergne-Rhône-Alpes region, with its préfecture at Aurillac. It was created by the National Constituent Assembly's decree of 26 February-4 March 1790 as one of the original roughly 83 départements that replaced the pre-Revolutionary provinces (Cantal was carved mainly from Haute-Auvergne, part of the former province of Auvergne). Unlike Belfort, the Alsace-Lorraine départements, Corsica or the overseas départements, Cantal was never split, annexed, or reconstituted after its creation, so its boundary has been essentially continuous for over two centuries. `type: subnational` is used because Cantal never held sovereignty of its own; it is being entered here purely as a reporting/administrative unit inside the French state, distinct from the national FRA rows which cover all of metropolitan France (and, for FRA-1800-1871, Alsace-Lorraine as well) rather than this one département specifically.

**Why this entry exists.** This entry implements the routing pipeline's verdict for unit_id FRA-FRK12 ("FRK12"), an administrative-unit code for Cantal that appears in an upstream data extract with a stated year range of 1862-2023. The routing_reasoning explains what this data was previously matched to and why that was wrong: the only existing FRA candidates in the polity table are the three national-total rows (FRA-1800-1871, FRA-1871-1919, FRA-1919-2025), which contain Cantal geographically but are not Cantal -- routing Cantal-level figures to a whole-of-France row would conflate a single département's statistics with roughly 90 other départements' worth of national totals, per the "contains vs is" rule the pipeline applies. No existing FRA polity row represents any single département, so a new subnational polity was required rather than a match to an existing one. What confirms this is a historically distinct administrative entity, rather than an arbitrary statistical partition, is Cantal's status as one of the original 1790 Revolutionary départements -- a formal unit of French local government with its own préfecture, conseil départemental, and INSEE code (15), continuously since creation. The specific dataset behind FRA-FRK12 (its publisher, exact row count, and the variable measured) was not supplied with the routing decision and is flagged as an open question below; this page documents the routing verdict, not yet a verified trace to the source series.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon available in the GeoPackage for this period. The routing decision found that gadm-4.1-adm1 is registered as a source and its id_column (GID_1) is designed to carry French département-level features, but the copy of that dataset held locally is a curated 81-country subset that excludes France entirely (0 rows for FRA). Fetching the full global GADM ADM1 layer, or IGN's ADMIN-EXPRESS as a national-agency alternative, would unlock a feature; until then `polygon_feature_id` is null and `polygon_status` is `unassigned`, per the rule that `registered_source_unfetched` keeps the registered slug (gadm-4.1-adm1) as `polygon_source` rather than `none`.

**Territory description:** Cantal occupies the southern/central part of the Massif Central in south-central France, roughly between Aurillac (the préfecture) in the west and the volcanic Cantal massif and Monts du Cantal in the east, bordered by the départements of Puy-de-Dôme, Haute-Loire, Lozère, Aveyron, Lot and Corrèze. It is a rural, mountainous, sparsely populated département in modern terms -- one of metropolitan France's least populous -- with an area of approximately **5,726 km2**, per INSEE's current published figure for the département, not a measurement of any polygon attached to this entry (since none is attached yet). Its boundary has been stable since the 1790 creation, so a present-day GADM/IGN feature, once fetched, should be a faithful proxy for the entire 1800-2025 span rather than an approximation limited to the modern era.

## Predecessors and successors

No predecessor or successor polities are listed. Cantal has had no predecessor as a distinct administrative unit -- it was created directly by the 1790 reform from parts of the pre-Revolutionary province of Auvergne, and provinces are not represented as polities in this table. It has had no successor: Cantal remains an active French département today, so `end_year: 2025` reflects the open/current convention used for still-existing subnational units, not a dissolution.

## Sourced claims

- Cantal was created by the French National Constituent Assembly's decree of 26 February-4 March 1790, carved chiefly from Haute-Auvergne within the former province of Auvergne, as one of the original set of roughly 83 départements.
- INSEE lists Cantal (department code 15) with a current land area of approximately 5,726 km2, and its préfecture is Aurillac.
- Cantal has not been subject to any of the four documented departures from the default 1790 département start-year convention (the 1871-1922 Territoire de Belfort split, the Alsace-Lorraine annexation/return départements, the 1975 Corsican split, or the overseas départements created in 1946), so its full administrative history runs 1790-present without a boundary-driven break.

## Decisions

### d-code-and-start-year-1800-not-1790

**Chose polity_code FRA-CANTAL-1800-2025 and start_year 1800, departing from the routing decision's proposed 1790**

The routing decision's `proposed.start_year` is 1790, matching Cantal's actual 1790 creation date, and its own `routing_concerns` field flags exactly this tension: '1790 predates the earliest container FRA-1800-1871 ... confirm whether the container chain should be extended back to 1790 or whether 1800 is the intended practical floor.' I checked the polity table directly and confirmed FRA-1800-1871 is in fact the earliest FRA row available -- there is no FRA container spanning any part of 1790-1800. The containment gate rejects an edge that falls outside either party's own span, so a container edge of {code: FRA-1800-1871, start_year: 1790, end_year: 1871} would fail immediately (1790 < the container's own start of 1800). Rather than leave a page that cannot pass the containment gate, I set this entry's start_year to 1800 -- the practical floor implied by the current table -- and used the dominant <ISO3>-<SUBUNIT>-<start>-<end> subnational naming pattern (57 of 66 subnational precedents) rather than a bespoke code, since Cantal is an ordinary département, not a historical territory with a name of its own like Alaska Territory or Hyderabad. This is recorded as open question oq-pre-1800-span-uncontained so that whoever eventually back-extends the FRA container chain to 1790 can also correct this entry's start_year and code.

## Open questions

### oq-pre-1800-span-uncontained

**Cantal existed as a département from 1790, ten years before this entry's container chain begins**

Cantal was created in the March 1790 Revolutionary reform along with the other original départements, so its true administrative start is 1790, not 1800. This page starts at 1800 only because the earliest FRA national row currently in the polity table, FRA-1800-1871, does not reach back further, and the containment gate requires every edge to fall inside its container's own span -- a 1790 start would produce an edge outside FRA-1800-1871's own 1800-1871 range and fail the gate. If a FRA container row covering 1790-1800 is ever added to the table, this entry's start_year, its container edge, and its polity_code should all be revisited and pulled back to 1790 (FRA-CANTAL-1790-2025) to match Cantal's actual founding date, with the frontmatter years updated to match per the gate that checks code years against frontmatter years.

### oq-no-polygon-fetched

**No GADM ADM1 feature is available on disk for any French département, including Cantal**

The routing decision found that the locally cached gadm-4.1-adm1 file is a curated subset covering only 81 countries and excludes France entirely (0 rows), even though gadm-4.1-adm1 is registered as a source and its id_column (GID_1) is designed to carry département-level features. Until the full global GADM ADM1 layer (or IGN's ADMIN-EXPRESS, proposed in the routing decision as a national-agency alternative) is fetched and loaded, this polity has no geometry -- polygon_status is unassigned and polygon_feature_id is null. Whoever ingests full GADM ADM1 coverage for France should populate GID_1 for Cantal here rather than constructing a bespoke polygon, since the boundary has been essentially stable since 1790 and a present-day admin-1 feature should be a faithful match for the whole 1800-2025 span, not just an approximation limited to the modern era.

### oq-cantal-source-not-traced

**The underlying dataset behind unit FRA-FRK12 was never named in the routing decision handed to this page**

The routing decision gives a unit_id (FRA-FRK12) and a stated data year range of 1862-2023, but neither the publisher, the exact row count, nor the variable(s) measured were included in the fields available to author this page. Before this entry's `sources` field or summary can honestly describe what dataset motivated its creation, the ingest pipeline should be traced back to identify: which source table produced unit FRA-FRK12 (likely INSEE or a French agricultural/administrative statistics series, given the 1862-2023 span), how many rows it contributes, and what indicator(s) it reports for Cantal specifically. Until then this page documents the routing verdict's reasoning but cannot cite the actual data it is meant to carry.
