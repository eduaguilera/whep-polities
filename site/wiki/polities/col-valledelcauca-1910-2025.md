---
polity_code: COL-VALLEDELCAUCA-1910-2025
polity_name: Valle del Cauca (department of Colombia)
start_year: 1910
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
predecessor: [COL-CAU-1886-1910]
successor: []
container:
  - code: COL-1903-1922
    start_year: 1910
    end_year: 1922
    basis: Valle del Cauca was created as a department of Colombia in 1910 by splitting Cauca department, during the 1903-1922 national era bounded by the loss of Panama (1903) and the administrative/border reorganization already reflected as the boundary between COL-1903-1922 and COL-1922-2025 in the polity table.
  - code: COL-1922-2025
    start_year: 1922
    end_year: 2025
    basis: The department continued as a first-order division of Colombia through the still-open modern national era COL-1922-2025.
---

# Valle del Cauca (department of Colombia)

## Summary

Valle del Cauca is a department of Colombia on the Pacific slope of the Cordillera Occidental, created in 1910 when the national congress split it off from the larger Cauca department. Its capital is Cali, today Colombia's third-largest city, and the department's economy has long been anchored on sugarcane cultivation in the Cauca river valley and on the port of Buenaventura, Colombia's main Pacific outlet. This entry is `type: subnational` because Valle del Cauca was never a sovereign state or period of national independence -- it is, and has been since 1910, a constituent department inside the Colombian national state, first under the 1903-1922 national era and then under the still-current 1922-2025 era. It exists as a distinct wiki row because at least one ingested source reports agricultural or production data at the department level (labelled "Valle del Cauca" or equivalent) rather than as a Colombia national total, and a department is a different territory than its country: routing that data to the national COL row would misstate both the geography and, for area-normalized measures, the scale of what is being reported.

**Why this entry exists.** Input data: rows labelled for the Colombian department of Valle del Cauca, spanning the extract window 1915-2023, were previously being routed to whichever national COL row covered each year (chiefly COL-1922-2025, and for years before 1922 potentially COL-1903-1922). That routing is wrong because Valle del Cauca is one of 32 departments of Colombia and covers roughly 22,000 km2 out of the country's 1.14 million km2 -- under 2% of the national territory -- so any department-level production or population figure filed against the national polity systematically misrepresents both the geographic extent and the implied per-area or per-capita intensity of whatever is measured. No existing polity row IS this territory: the only candidates in the table before this entry were the national-total COL chain and Cauca department (a different, larger territory that Valle del Cauca was carved out of in 1910), neither of which match_existing could correctly absorb this data into. The entity's distinctness as an administrative and statistical unit is confirmed by its own founding legislation (Colombian Law 8 of 1910, which created the department by separating it from Cauca) and by its continuous, uninterrupted existence as a first-order division ever since, which is why national statistical agencies (and by extension international compilers like FAO or Mitchell-style historical statistics) report at this level.

## Territorial extent

**Polygon status:** Not yet assigned. No polygon is attached in the GeoPackage for this period; `polygon_status: unassigned` and `polygon_source: gadm-4.1-adm1`. GADM 4.1's admin-1 layer is the registered source this repository uses for country subdivisions worldwide, and it is already accepted for other department/state-level entries drawn from the same file, but the locally cached extract of that source is a curated 81-country subset that does not currently include Colombia (0 features for COL). This is the `registered_source_unfetched` case: the correct source is known and its licence terms already apply, but the COL rows (departments, likely following the GID_1 pattern `COL.<n>_1`) have not yet been fetched into the local file, so no `polygon_feature_id` can be honestly filled in yet.

**Territory description:** Valle del Cauca sits in southwestern Colombia, running from the Pacific coast (including the port city of Buenaventura) inland across the Cauca River valley to the crest of the Cordillera Central, bordered by Chocó and Risaralda to the north, Quindío and Tolima to the east, Cauca to the south, and the Pacific Ocean to the west. Its capital, Santiago de Cali, is a readily locatable modern reference point. The department's present-day area is approximately 22,140 km2 (a published national-statistics figure, not a measurement of any polygon attached to this entry, since none is attached yet). Boundaries have been broadly stable since the 1910 creation, with one adjustment in 1966 when part of the department's eastern territory was separated to form the new department of Quindío -- meaning a polygon fetched for the modern department would slightly over-cover the 1910-1966 extent of this entry, an approximation that should be noted whenever a GADM feature is eventually attached.

## Predecessors and successors

Predecessor: Cauca department (Colombia), from which Valle del Cauca was split by Law 8 of 1910; the wiki does not yet contain a Cauca department page, so `COL-CAU-1886-1910` is a forward reference following this country's dominant naming pattern rather than a confirmed existing code, and should be reconciled once Cauca's own page is created. No successor: the department continues to exist today, so `end_year: 2025` is open (exclusive) per the country convention for still-current subnational units, and `successor` is empty.

## Sourced claims

- Valle del Cauca was created as a department of Colombia by Law 8 of 1910, which separated it from the larger Cauca department -- this is the basis for the entry's start_year of 1910.
- The modern department of Quindío was separated from Valle del Cauca's territory in 1966, meaning any polygon representing the present-day department boundary over-covers the department's 1910-1966 extent.
- Colombia's national statistical office (DANE) and international agricultural compilers (e.g., FAO) report production and population statistics at the department level for Valle del Cauca separately from national Colombia totals, which is the operational evidence that a distinct reporting territory -- not just an administrative curiosity -- exists here.

## Decisions

### d-code-pattern-iso3-subunit-years

**Used the dominant <ISO3>-<SUBUNIT>-<start>-<end> code pattern**

Colombia has no existing subnational rows to set a country-specific precedent (0 prior COL subnational codes), so this entry follows the dominant pattern used by 57 of 66 subnational rows in the table: <ISO3>-<SUBUNIT>-<start>-<end>, giving polity_code COL-VALLEDELCAUCA-1910-2025. Valle del Cauca is an ordinary administrative department, not a historical territory with a bespoke identity comparable to Alaska Territory or Hyderabad, so the 3-code bespoke pattern used by only 3 of 66 subnational rows was rejected as inapplicable here.

### d-container-two-edges

**Split the container into two edges to tile 1910-2025 without gaps**

The routing decision proposed a single container edge (COL-1922-2025) covering only 1922-2025, but the department's start_year of 1910 falls inside the earlier national era COL-1903-1922, which the polity table shows running 1903-1922. A single edge starting at 1922 would leave 1910-1922 uncontained and would be rejected by the containment gate for falling outside COL-1922-2025's own span. I added a first edge COL-1903-1922 for 1910-1922 and kept a second edge COL-1922-2025 for 1922-2025, together tiling the full 1910-2025 span with no gap, each edge basis stated separately since a container can change while the territory persists.

### d-predecessor-cauca-forward-ref

**Recorded a predecessor code for Cauca department even though no such page exists yet**

Because Valle del Cauca split off from Cauca department in 1910, I listed a predecessor code COL-CAU-1886-1910 by analogy with the dominant subnational naming pattern, even though the polity table does not yet contain a Cauca department row (the routing decision's own reasoning notes Cauca as a candidate territory but not as an existing distinct page). This forward reference will need to be corrected or confirmed once a Cauca department page is actually created; flagged as an open question below rather than left silently unresolved.

## Open questions

### oq-cauca-predecessor-code-unconfirmed

**Predecessor code for Cauca department is a forward reference, not a confirmed existing page**

This entry lists `COL-CAU-1886-1910` as `predecessor`, following the dominant COL subnational naming convention, but no Cauca department page currently exists in the wiki (the routing decision that created this entry only names Cauca as a rejected match_existing candidate, not as an existing row). When Cauca's own page is eventually created, its actual code, start_year, and end_year need to be checked against this reference and the predecessor field corrected if they differ -- for instance if Cauca's page uses a different start year than 1886 or a different subunit token than CAU.

### oq-1910-creation-date-unverified

**The 1910 creation date rests on general historical knowledge, not a source in this repository**

The routing decision explicitly flagged that the 1910 creation date for Valle del Cauca (Law 8 of 1910, splitting it from Cauca) could not be verified against repository evidence, since no boundary or name candidate is present locally to corroborate it. This page repeats that same unverified claim as the basis for start_year=1910. Before this entry is treated as fully confirmed, the date should be checked against an authoritative source such as Colombia's official gazette record of Law 8 of 1910 or a standard reference on Colombian departmental history.

### oq-1966-quindio-split-not-modeled

**The 1966 separation of Quindío is not reflected as a boundary change within this entry's span**

Valle del Cauca lost territory in 1966 when Quindío became a separate department, but this entry spans 1910-2025 as a single row with a single (currently unassigned) polygon slot, meaning any future GADM-derived polygon for the modern department will over-cover the 1910-1966 period. It is unclear whether the correct fix is to split this entry at 1966 into two rows (pre- and post-Quindío) the way other departments with major boundary changes are handled elsewhere in the table, or whether a single proxy with a documented caveat is acceptable given the modest size of Quindío (~1,845 km2) relative to Valle del Cauca's ~22,140 km2. This should be resolved before a polygon is actually fetched and attached.

### oq-data-coverage-1915-1922-unclear

**Whether any of the underlying data rows for 1915-1921 were previously misrouted to COL-1903-1922 or COL-1830-1903**

The routing decision's data window is 1915-2023, but this page's start_year of 1910 (and the container edge split at 1922) implies at least the possibility of department-level data existing for 1915-1921 that would have been routed to the national era COL-1903-1922 rather than COL-1922-2025. It has not been confirmed whether any such pre-1922 Valle del Cauca rows actually exist in the ingested data, or whether all 1915-1921 department rows (if any) were in fact absent and this is a purely administrative-history-driven start_year with no data consequence in that sub-range.
