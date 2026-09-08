---
polity_code: BRA-MATOGROSSO-1889-2025
polity_name: Mato Grosso
start_year: 1889
end_year: 2025
type: subnational
iso3: BRA
continent: South America
cow: NA
status: draft
last_ingest: 2026-09-07
sources: [juan-subnational]
polygon_source: geobr-ibge
polygon_feature_id: null
polygon_feature_year: null
polygon_status: unassigned
predecessor: []
successor: []
container:
  - code: BRA-1800-1903
    start_year: 1889
    end_year: 1903
    basis: Mato Grosso as a province of the Empire of Brazil until the Republic's provinces-to-states conversion, within the national row that runs to 1903
  - code: BRA-1903-1909
    start_year: 1903
    end_year: 1909
    basis: Mato Grosso as a state of the Republic, within the national row covering this narrow 1903-1909 era
  - code: BRA-1909-2025
    start_year: 1909
    end_year: 2025
    basis: Mato Grosso as a state of the Republic, within the current national row spanning 1909 to the present
---

# Mato Grosso

## Summary

Mato Grosso is a landlocked Brazilian state straddling the southern Amazon basin, the Pantanal wetlands, and the Cerrado savanna of the central-western plateau. It descends from one of Portuguese Brazil's original captaincies, formalized as a province in the colonial era and centered on 18th-century gold-mining settlements around Cuiabá (still the capital). This entry covers Mato Grosso from 1889, when the Proclamation of the Republic converted the Imperial province into a state of the federation, to the present. `type: subnational` is used because Mato Grosso has never been a sovereign polity: it was a captaincy and then a province under Portuguese and Imperial rule, and has been a first-order administrative division (state) of the Brazilian federation continuously since 1889. Mato Grosso itself is not among the six listed BRA departures from the default rule — it is instead the PARENT from which Mato Grosso do Sul later departed, splitting off in 1977/1979 — so the default republic-founding start year of 1889 applies to this entry, with an open end_year of 2025 since Mato Grosso remains a current state under its own (now smaller) name.

**Why this entry exists.** The routing decision this page implements (unit_id BRA-MATOGROSSO) found no existing polity in the database representing Mato Grosso itself: the only BRA rows are three national totals (BRA-1800-1903, BRA-1903-1909, BRA-1909-2025), none of which is state-scale, and no boundary or name candidates matched. Source rows describing Mato Grosso specifically — a state-level Brazilian subnational dataset, following the same pattern already established for sibling verdicts BRA-BAHIA, BRA-GOIAS, BRA-ALAGOAS and BRA-AMAZONAS — previously had nowhere correct to route except the national BRA-1909-2025 row, a container many times Mato Grosso's own territory, which would misattribute state-level agricultural/production data to the whole country. What confirms Mato Grosso is a distinct reporting unit rather than folded into national Brazil figures is the practice documented for the sibling entries: the source reports Mato Grosso as a named first-order administrative unit (a Brazilian state), consistent with IBGE's own state-level statistical reporting since the founding of the Republic, and consistent with the routing decision's explicit framing of Mato Grosso as the historical parent unit from which Mato Grosso do Sul later split — itself proof that contemporary statistical and administrative practice treated (and treats) Mato Grosso as its own distinct territory, not a subset folded into a larger reporting unit. This entry is one of a batch of Brazilian state-level polities created under the same default start-year rule, with no departure listed for Mato Grosso in the country convention (unlike Mato Grosso do Sul, Acre, Rondônia, Amapá, Roraima and Tocantins, which are the six enumerated departures).

## Territorial extent

**Polygon status:** Not yet assigned. No polygon available in the GeoPackage for this period. The correct source is `geobr-ibge` (Brazilian state boundaries, id_column `abbrev_state`), registered in scripts/sources.yaml specifically to carry Brazilian ADM1 units, but its file (data/geodata/geobr-ibge/states.gpkg) is not present locally, per the routing decision's own polygon_reasoning. `gadm-4.1-adm1` excludes Brazil from its locally curated subset, and the only BRA source currently present, `cshapes-2.0`, digitises Brazil at whole-country scale only. Once geobr-ibge is fetched, this entry should match abbrev_state='MT'. **The modern boundary is a materially incomplete proxy for most of this span**: present-day Mato Grosso covers approximately 903,400 km2 (one of Brazil's largest states, still larger than France), but until 1977 its territory also included what became Mato Grosso do Sul (roughly 358,000 km2), so pre-1977 Mato Grosso was closer to 1,260,000 km2 combined — about 40% larger than the modern state's area. Modern Mato Grosso is bordered by Amazonas, Pará and Tocantins to the north, Goiás to the east, Mato Grosso do Sul to the south, and Rondônia and Bolivia to the west; its capital is Cuiabá, founded in 1719 during the gold rush that first drew Portuguese settlement to the region. No polygon_area_km2 is recorded here since no geometry is yet attached.

## Predecessors and successors

No predecessor row is created by this decision: Mato Grosso's status as a first-order Brazilian administrative unit runs continuously back to 1889 with no sovereignty break, so no separate pre-1889 provincial entry is proposed (the pre-1889 Imperial province is left to the national BRA-1800-1903 row, consistent with the default convention). This entry has no successor row of its own — Mato Grosso remains a Brazilian state to the present, so the span runs to 2025 as still-current — but Mato Grosso do Sul (split off 1977/1979) is a territorial descendant of undivided Mato Grosso that, once created as its own polity, will need a predecessor/successor or container link back to this entry; this page does not create that link since the routing decision provides no basis for it.

## Sourced claims

- The Proclamation of the Republic (15 November 1889) converted the Imperial provinces, including Mato Grosso — one of Brazil's original captaincies/provinces dating to 18th-century Portuguese colonial administration and gold-mining settlement — into states of the new federation, the event that fixes this entry's 1889 start under the country convention's default rule.
- Complementary Law 31 of 11 October 1977 split the state of Mato Grosso do Sul from the southern portion of undivided Mato Grosso, with the new state formally installed on 1 January 1979, reducing modern Mato Grosso to roughly its northern half — a fact relevant to reading any pre-1977 territorial figures against this entry's proxy polygon.

## Decisions

### d-code-iso3-subunit-start-end-pattern

**Use the dominant <ISO3>-<SUBUNIT>-<start>-<end> code pattern, not a bespoke code**

Mato Grosso is a first-order Brazilian state, structurally identical to the 57 of 66 subnational rows in the table that follow <ISO3>-<SUBUNIT>-<start>-<end> (e.g. ESP-AS-1833-2025, DZA-CVD-1902-1919), including the sibling BRA states already created this session (BRA-BAHIA-1889-2025, BRA-GOIAS-1889-2025, BRA-ALAGOAS-1889-2025, BRA-AMAZONAS-1889-2025, BRA-CE-1889-2025, BRA-ES-1889-2025, BRA-MARANHAO-1889-2025). It is not a historical territory with a name and identity distinct from its status as an administrative division, so it does not qualify for bespoke-code treatment like ALK-1867-1959 or HYD-1724-1948. BRA-1909-2025 is the container across almost the entire span, consistent with all sibling BRA-state entries, and BRA-1800-1903/BRA-1903-1909 tile the remainder with no gap.

### d-single-span-despite-1977-partition

**One unbroken 1889-2025 span, not split at the 1977 Mato Grosso do Sul partition**

Mato Grosso lost roughly half its undivided territory when Mato Grosso do Sul was split off in 1977 (Complementary Law 31/1977, effective 1979). Despite that, this entry does not split into pre-1977/post-1977 rows, because: (1) the routing decision explicitly identifies Mato Grosso as the parent from which Mato Grosso do Sul later split, but gives no basis for a mid-span split of this entry itself and treats the default 1889 start as applying to the whole span; (2) the sibling verdicts (BRA-GOIAS, which underwent the structurally identical 1988 Tocantins split) establish an unbroken single-span pattern for BRA states even where boundaries changed dramatically; (3) Mato Grosso do Sul is one of the six enumerated departures from the default BRA start rule and will receive its own polity row with its own start year (1977 or 1979), at which point the territorial transfer can be handled via that entry's own predecessor/successor or container links rather than by fragmenting this one. The territorial discontinuity is documented plainly in Territorial extent so a future polygon-fetch step does not treat the modern geobr-ibge boundary as valid back to 1889 without qualification.

## Open questions

### oq-pre1977-boundary-proxy-validity

**Is the modern geobr-ibge Mato Grosso boundary a valid proxy before 1977, or does it need a constructed pre-partition polygon?**

Once geobr-ibge is fetched, the default action would be to match abbrev_state='MT' for the whole 1889-2025 span. But that modern boundary excludes the roughly 358,000 km2 that became Mato Grosso do Sul in 1977/1979, so for 1889-1977 (nearly ninety of this entry's 136 years) it under-covers Mato Grosso's actual historical territory by close to half. A constructed union polygon (modern Mato Grosso + modern Mato Grosso do Sul, analogous to how MAN-1932-1945 unions three modern Chinese provinces, and to the same open question raised on BRA-GOIAS for its 1988 Tocantins split) may be more correct for the pre-1977 portion, via constructed/build.py. This needs a decision before any pre-1977 data routed here is treated as territorially accurate, and before polygon_status is upgraded from unassigned.

### oq-underlying-source-row-count-unknown

**Exact row count and year coverage of the source data routed to this entry is not stated in the routing decision**

The routing decision's proposed span (1889-2025) is stated but the routing_reasoning gives no row count or explicit year range for Mato Grosso-labeled subnational data, unlike some sibling verdicts. Before this entry's last_ingest/sources metadata is finalized, the actual source file and row count for Mato Grosso should be confirmed against the ingest pipeline (likely the same juan-subnational dataset used for BRA-BAHIA, BRA-GOIAS and other BRA-state siblings), since a wiki page asserting specific coverage without checking the source risks the kind of unverified pin flagged elsewhere in this project's history.

### oq-mato-grosso-do-sul-link-not-modeled

**Does the 1977/1979 Mato Grosso do Sul split need an explicit predecessor/successor link once that entry exists?**

Mato Grosso do Sul is one of the six enumerated BRA departure cases and, per the routing_reasoning for this entry, is expected to receive its own polity row with a 1977 or 1979 start. This entry's single container chain (BRA-1800-1903 / BRA-1903-1909 / BRA-1909-2025) does not distinguish the pre-split undivided territory from the post-split smaller one. Once BRA-MATOGROSSODOSUL (or similar code) is created, it may be worth adding an explicit link (predecessor/successor or a note) between the two entries so a reader does not assume Mato Grosso's reporting territory was constant 1889-2025 without the 1977 excision. Left unresolved here since it depends on how that future entry itself frames the split.
