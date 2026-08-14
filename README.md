# WHEP Polities

Historical polities database for the [Who Has Eaten the Planet?](https://www.whep.eu/) (WHEP) project. Each polity is a territorial-economic unit with a defined extent over a continuous time period from 1800 to 2025.

## Architecture

**The wiki is the source of truth.** Every polity has a curated page at `wiki/polities/<code>.md` with YAML frontmatter that declares its identity, status, and the provenance of its polygon. Everything else is a derived artifact — rebuilt from the wiki and the polygon sources by a single command: `bash scripts/rebuild.sh`.

```
 wiki/polities/*.md          ← you edit this (source of truth)
       │
       ▼
 bash scripts/rebuild.sh
       │
       ├── scripts/sources/constructed/build.py   (dissolves/unions from cshapes, gadm, ...)
       ├── scripts/build_database.py              → data/final/polities_database.{csv,gpkg}
       ├── site/build_wiki.sh                     → site/polities.{csv,geojson} + site/wiki/
       ├── pipelines/pre1961-matching/match.R     → data/compiled/pre1961/*  (optional, needs R)
       └── site/build_wiki.sh (second pass)       → site/pre1961/*
```

`scripts/rebuild.sh` is the only command a human runs. The pieces it calls aren't separately user-facing.

## Rebuilding from scratch

Raw polygon inputs (CShapes, GADM, Cliopatria, …) live under `data/geodata/<slug>/` and are **gitignored**. Each source has a fetch script that re-downloads it from its original location:

```bash
# 1. Fetch the raw sources you need
bash scripts/sources/cshapes-2.0/fetch.sh
bash scripts/sources/cshapes-europe/fetch.sh
bash scripts/sources/cliopatria/fetch.sh
bash scripts/sources/paine-2024/fetch.sh
bash scripts/sources/histogis-1860-habsburg/fetch.sh
bash scripts/sources/gadm-4.1/fetch.sh

# 2. Rebuild every derived artifact in one command
bash scripts/rebuild.sh
```

If R isn't installed, step 1 skips the R-package sources (USAboundaries, mapSpain, geobr) and `rebuild.sh` skips the pre-1961 crosslink with a warning.

You don't have to run the fetches if you only want to consume the committed `data/final/polities_database.gpkg` — it's self-contained.

## Validation

Thirty-eight checks guard the database, and a thirty-ninth checks the checks -- the
count matches the `validate_*`/`crosscheck_*`/`audit_*` scripts under `scripts/`,
which is what `selftest_gates.py` enumerates, so it is checkable rather than prose.
(Counted on 2026-08-13 while adding `validate_year_semantics.py`: the prose said
thirty-five against a real thirty-six, so the sentence claiming to be checkable was
itself the stale one. It is words, and `selftest_gates` compares script names, not
numbers.) Most
exist because that class of error was **found in the data**, not hypothesised; the
few marked *(guard)* below hold a property that is true today and would be costly
to lose. All are worth keeping green:

```bash
# the published contract still matches the wiki
python3 scripts/build_database.py --check
python3 scripts/write_manifest.py --check
python3 scripts/write_faostat_area_map.py --check
python3 scripts/write_label_alias_map.py --check
python3 scripts/update_wiki_index.py --check
python3 pipelines/polity-autoimprove/04_territory_basis.py --check
python3 pipelines/polity-autoimprove/08_source_stated_areas.py --check
python3 scripts/write_feature_index.py --check
python3 scripts/write_iso3_successor_map.py --check
python3 scripts/write_iso3_successor_map.py

# provenance and internal consistency
python3 scripts/validate_schema_contract.py
python3 scripts/validate_citations.py
python3 scripts/validate_constants.py
python3 scripts/validate_aliases.py
python3 scripts/validate_unranged_aliases.py
python3 scripts/validate_alias_chain_overlaps.py
python3 scripts/validate_live_name_ambiguity.py
python3 scripts/validate_local_iso_codes.py
python3 scripts/crosscheck_matchers.py
python3 scripts/validate_order_decided_families.py
python3 scripts/audit_family_shadowing.py

# identity and periodisation
python3 scripts/validate_iso_codes.py
python3 scripts/validate_iso_collisions.py
python3 scripts/validate_dissolved_iso_codes.py    # the ISO 3166-3 coding rule, as a check
python3 scripts/validate_cow_codes.py
python3 scripts/validate_cross_family_names.py
python3 scripts/validate_period_overlaps.py
python3 scripts/validate_period_gaps.py
python3 scripts/validate_reporting_areas.py
python3 scripts/validate_code_year_agreement.py
python3 scripts/validate_year_semantics.py         # one reading of end_year, and one of alias year_end, in every component
python3 scripts/validate_references.py
python3 scripts/validate_map_area_year.py
python3 scripts/validate_alias_year_coverage.py

# geometry
python3 scripts/validate_polygons.py
python3 scripts/validate_polygon_validity.py
python3 scripts/validate_simplification_loss.py  # shipped geometry vs the source it was cut from
python3 scripts/validate_stated_areas.py
python3 scripts/validate_shared_polygons.py
python3 scripts/validate_polygon_period_fit.py
python3 scripts/validate_polygon_binding_determinism.py
python3 scripts/validate_spatial_containment.py
python3 scripts/validate_family_areas.py
python3 scripts/validate_source_change_steps.py   # a step is only suspicious WITH a source change
python3 scripts/validate_s2_polygons.py            # asks s2 itself, via spherely
python3 scripts/validate_spherical_edges.py
python3 scripts/validate_succession_geography.py   # reads the committed .gpkg; runs in CI too
python3 scripts/validate_chain_integrity.py        # CSV + wiki only, no geometry
python3 scripts/validate_site_outputs.py           # site/ is deployed output; nothing checked it
python3 scripts/validate_registry_unmapped.py      # 'no polity for this area' is a claim; check it

# and the one that asks whether the checks above can fail at all
python3 scripts/selftest_gates.py

# the external-data guards, whose self-test uses synthetic frames and so runs anywhere
python3 pipelines/polity-autoimprove/extdata.py
```

| check | what it caught when first run |
|---|---|
| `build_database.py --check` | a wiki edit never propagated to the CSV; later, `"NA"` text stored as a literal string |
| `write_manifest.py --check` | a stale alias-map fingerprint after aliases changed |
| citations | 17 citations pointing at source files that were never ingested |
| `validate_site_outputs.py` | site/polities.geojson two months stale — 194 live polities missing, 35 withdrawn ones drawn on the map |
| `validate_registry_unmapped.py` | 16 areas listed as having no polity while their polity existed, so their data still resolved to `ROW-1850-2025` |
| constants | `DEAD_STATUS` is defined **five** times, and `CLAIMS_POLYGON` excluded four statuses that 11 rows with geometry were using |
| schema contract | seven tables named the same four things six, five, three and two ways, and four analyses in one session read a wrong name and got an *answer* rather than an error — `csv.DictReader` returns `None` for a column that is not there. Issue 95 unified the pipeline-internal half: `original_name`/`area_name` → `source_label`, `rows`/`n_rows` → `observed_rows`, `target_polity_code` → `polity_code`, across seven state files, four of them newly pinned. The published half is deliberately untouched (`data/final/*` is read by name from the WHEP R package, so `observed_rows` and `rows_observed` remain transpositions of each other pending a deprecation release), and layer B's `polity_code` — which holds lowercase ISO codes, 0 of its 166 values matching any real polity code — is renamed to `iso3_lower` as this repo loads it, since the parquet is built elsewhere |
| aliases | five aliases silently **inert** — two had the target sitting in the `confidence` column |
| alias chain overlaps | *(guard)* an alias `year_end` is INCLUSIVE while a polity `end_year` is EXCLUSIVE, so consecutive aliases for one label both cover the boundary year and match order decides which polity a value lands in. 17 chains do, down from 25: the seven cleared on 2026-08-05 were the ones whose earlier alias claimed a year its successor covers, clipped after checking against the observations that nothing would go unmatched (issue 90 group A -- 58 aliases, 1,544 rows). The rate depends on how they were written — 18 of 31 hand-entered any-source chains against **0 of 7** generated with `year_end = polity_end_year - 1` — so the convention demonstrably removes it. The safe half is now fixed rather than gated: 58 aliases whose boundary year a successor alias already covers were clipped (issue 90). Re-measured 2026-08-13: **200** aliases still overclaim, of which **17** (label, source, year) pairs carrying **108** rows have NO covering target and must not be clipped -- those need a target or a period boundary, not a range edit. The 209/24/229 previously recorded here was the count on the day group B was fixed; intervening Libya, Papua and Trieste work moved it, and `italy` 1919 (73 rows, the largest single item and the only one whose own chain had already been clipped at its other two links) was fixed on 2026-08-13. The 17 that remain are periodisation decisions, largest first: greece 1913, libya 1949, libya tripolitania 1951, burkina faso 1932, indonesia java and madura 1951, czechoslovakia 1918 |
| alias year coverage | an alias claiming a year its own target polity does not cover, over **451,145 observed rows**. Re-measured 2026-08-13 (issue 79): 131 alias rows, not the 270 the issue reported — three of its mid-sized cases had already been clipped. Two thirds of what it flagged was not a defect: 67 rows pointed at a LIVE polity whose exclusive `end_year` is the 2025 ceiling, where `year_end == 2025` is the ceiling showing through, and are now excluded exactly as `validate_map_area_year.py` already excluded them. Two were real and are fixed — `"tanzania"`/`"tanganyika"` claiming to 1964 against `TAN-1922-1964`, whose span ends 1961 since `TZA-1961-1964` was split out, the only overshoot in the class larger than one year. The 101 that remain are dissolved entities' FINAL REPORTING YEAR (Belgium-Luxembourg 1999, Sudan 2011, USSR 1991, Netherlands Antilles 2010 = 450,335 rows), now **accepted as data with the convention written down**: that year belongs to the outgoing entity |
| unranged aliases | the `"Syria"` alias had no year range and pointed at `SYR-1946-1967`, so every year — including 2020 — resolved to a polity that ended in 1967, across 162 observed rows. Unlike an inert alias it worked; it just worked wrongly |
| crosscheck matchers | the two independent matchers disagreed on three FAOSTAT areas, including Serbia 2006-2008 existing **twice** |
| shadowing | Alaska outranking the USA and absorbing ~7,600 rows of mainland data |
| iso codes | `FRS-1977-2025` is modern Djibouti and carried `iso3: FRS`; DJI is the real code, so nothing holding a country code could reach it. Also Sudan as `SUD`, colonial Angola as `ANG` |
| cross-family names | `TAN-1922-1964` overlapping `TZA-1961-1964`, and `MAR-1911-1958` overlapping `MOR-1956-1958` — the earlier row's end year running past its successor's start. Invisible to the period-overlap gate, which only compares within one prefix. Latent rather than live: the inert twins are unmapped, so the consumer never sees both |
| cow codes | `ICN-1800-2025` (Canary Islands) carried COW code **20**, which is Canada. The Canaries are not a COW state — they are part of Spain, 230 — so the value was removed rather than corrected, which would have swapped one collision for another. Its `iso3` and polygon were both fine, so no other check could see it |
| iso collisions | *(guard)* 59 pairs already share a code over overlapping years **by design**, since `iso3` groups by modern territory. The gate is that the set must not grow |
| dissolved iso codes | the USSR's three rows carried **no** `iso3_code`, so a consumer holding `SUN` — which WHEP's own `regions_full` and `polity_area_crosswalk` both reference — reached nothing, even though the polity plainly existed. Fixed to `SUN` (ISO 3166-3 `SUHH`). The gate is the rule [issue 55](../../issues/55) asked to have written down: a dissolved entity whose polity family **continues into a live polity** carries that live polity's 3166-1 code (Zaire→`COD`, Burma→`MMR`, Southern Rhodesia→`ZWE`, Afars and Issas→`DJI`) and must NOT use its 3166-3 code; one whose family **terminates** carries its own 3166-3 code (`CSK`, `YUG`, `DDR`, `SUN`, `ANT`, `SCG`, `PCI`). Membership is listed, the verdict is derived, so the rule is tested rather than restated. 12 entities, 36 rows |
| local iso codes | *(guard)* `iso3_code` is **not ISO-conformant and cannot be** — there is no ISO 3166 code for Austria-Hungary, so this database invents `AUH`. 56 of its 276 values are local like that, and a consumer joining against ISO-keyed data silently matches none of them; it is what stops four dissolved federations reaching WHEP's LUH2 land series. The vocabulary is therefore an interface, and the gate is that it does not change unreviewed. The local/ISO distinction is now published in `polities_manifest.json` (`local_iso3_codes`), and how dissolved states are coded is gated by `validate_dissolved_iso_codes.py` |
| period overlaps | four same-family pairs cover the same years, so a year-aware matcher must guess. `PER-1825-1909` duplicates two rows that already tile its span exactly |
| period gaps | *(guard)* the complement — 11 families leave a year between consecutive periods, where a matcher gets NO answer. `LBY` 1949 was one and was sending 28 rows labelled `Libya` to Cyrenaica alone. Its coverage annotation answered "who else held this territory" by comparing `iso3_code`, which cannot cross a family: five gaps read "no cover found" while the published successor map named a holder for every year of them — `CZE` 1918-1992 to `F51`, `MNE` 1918-2005 to `F248`/`SCG`, `ERI` 1952-1992 to `ETH`, `SEN` 1959 to `AOF`, `LAO` 1953 to `FID` (issue 82). The annotation now reads that map. It is still advisory: the gate passes or fails only on the baseline |
| `validate_map_area_year.py` | the same question asked of the published FAOSTAT map, whose `year_start`/`year_end` are **INCLUSIVE** while a polity's `end_year` is **EXCLUSIVE**. Two areas gave a real handover year to both polities at once — area 205 in 1975 (the Madrid Accords) and area 240 in 1917 (the sale of the Danish West Indies) — and `validate_period_overlaps` could see neither, because read from the database `DWI-1800-1917` covers through 1916 and genuinely does not overlap `VIR-1917-2025`. The ambiguity existed only in the published ranges. Both are fixed, and both fixes chose the same rule, so it is now written down and asserted rather than argued: **a handover year belongs to the INCOMING polity** (issue 74). All 53 handover boundaries in the 43 multi-row areas obey it, with no baseline. The third arm catches one answer too FEW, which neither of the other two can: an outgoing row clipped a year short leaves a year no polity claims, and a year with zero answers looks exactly like a year nobody asked about. The four rows whose `year_end` overshoots their polity's coverage are a different question — a dissolved entity's final REPORTED year, accepted and pinned (issue 164) |
| reporting areas | six GADM territories claimed by **two** aggregates each — Palau and the Northern Marianas sit in both Asia Other and Oceania Other. Hidden because the RoW union deduplicates |
| polygons A | 8 polities carrying **another country's** polygon — San Marino had Albania's (470× too large), Indonesia had India's |
| polygons C | 28 polities declaring a polygon the build never attached |
| polygons D | 13 pages claiming `status: reviewed` with zero source citations |
| family areas | *(guard)* check A needs a **recorded** area to compare against, and 76% of rows claiming a polygon have none. Comparing a period to its own family's median needs no reference and covers all of them. Two anomalies today, both legitimate |
| source-change steps | `TUN-1800-1881 -> TUN-1881-2025` published a **3.55×** area step at 1881 — the largest in the database — and the Treaty of Bardo transferred authority over the Beylik, it did not quadruple it. The step was a source change: Paine et al. (2024) feature `Tunis` at 43,752 km² followed by CShapes 616@1886 at 155,471. Issue 159 read the difference as claimed-versus-effective territory with the Sahara between them; **re-measuring rejected that** — only 61,369 km² of the 111,741 lies south of 33.44°N and **42,728 km² is north-WESTERN Tunisia**, with Béja, Jendouba, Le Kef, Kasserine and Gafsa outside the Paine polygon while Kairouan, Siliana and Sfax are inside it. The Medjerda valley is the Beylik's grain belt, so the polygon was not a stricter convention but the wrong shape; of the 41 rows bound to `paine-2024` it was the only one outside the dataset's stated sub-Saharan coverage, and the page's own prose had described a CShapes back-projection all along. Rebound, step now **1.00×**. The gate then found a second, larger artefact the issue had not: `OTT-1800-1886 -> OTT-1886-1908` publishes a **34% expansion** of an empire that spent the century contracting — +881,968 km² of Ottoman Libya and +81,552 of Yemen/Asir that Cliopatria's 1800 polygon omits, against a real −171,358 km² in the Balkans, so 963,520 km² of convention outweighs a genuine loss and reverses its sign. *(guard)* Neither a big ratio nor a source change is a signal alone — the largest steps here are Trianon and Guadalupe Hidalgo, and 22 of 39 source changes move the area under 30%; the two together are, so each of the 17 qualifying steps carries a verdict of `EVENT`, `ARTEFACT` or `SCOPE` and prose naming what produced it |
| spatial containment | one polity's polygon swallowing a neighbour's; a family's consecutive periods overlapping by under half |
| binding determinism | 25 of 674 bindings were decided by **shapefile row order** rather than by the data, because `find_feature`'s tie-break cannot choose when two candidate time-steps start in the queried year. Asking only "could this binding have gone another way?" found live errors that three separate accidents had each found one at a time (issues 45, 92, 99): Russia carrying the USSR, Serbia carrying Kosovo, Vietnam pre-Laos-transfer. Nine more were pinned on 2026-08-13 and **four of those were already wrong** — Kenya on its pre-transfer extent against a page that says post-transfer, the **USA without Hawaii**, Türkiye pre-Mudros against a page asking for post-Mudros and wrongly asserting no such polygon existed, Czechoslovakia on a 33-day step for a 7-year row. Twelve remain: nine whose candidates are identical in area, and three single-year rows CShapes cuts into three-plus steps, which **no `polygon_feature_year` can pin** — one of them, `POL-1919-1920`, carries the polygon its own page rejects by name and is 44% short (issue 100) |
| shared polygons | *(consumer-found)* **twelve** cross-family pairs coexist on ONE polygon in WHEP's embedded copy, so the ground inside it is claimed twice: `GNQ-1968-2025` and `STP-1800-2025` were both bound to CShapes feature 411, which is mainland Rio Muni, and cell (10.25, 1.75) claimed **2.0000×** its own area — 451 of 67,691 cells over-claimed for 2015, 12.72 Mha in excess. All twelve are already resolved here, so this gate is the standing assertion rather than the repair, and each pair is pinned by name. The reason it is a separate check is that **all 27 other gates pass on it**, verified by injecting it back at the wiki, the CSV and the GeoPackage together: the area check had no recorded area to compare against, the containment check needs three swallowed neighbours and two identical polygons swallow one each, and the period-fit and determinism checks confirm `411@1900` resolves cleanly — it is simply the wrong country. Two signals, because a binding and a geometry can each be wrong alone: a shared `(source, feature_id, feature_year)` in the CSV, and an intersection-over-union above 0.9999 in the GeoPackage. It deliberately does **not** assert that a cell never over-claims: 188 coexisting pairs overlap by >1 km² in 2015 (331,429 km² total) and the large ones are dispute and nesting — `ESH`/`MAR` 267,078 km², `SAU`/`YEM` 29,918 km², `ESP`/`ICN` 7,027 km² — which is a territorial judgement, tracked separately |
| code/year agreement | *(guard)* a polity code is documented as `PREFIX-start-end`, so consumers read years straight off the identifier rather than joining. Two codes disagree with their own columns — `TAN-1922-1964` ends 1961, `NNG-1949-1963` ends 1969 — and the consumer's aliases were written against the CODE, so two of them resolve 1962-1964 to a polity its columns say had ended. Both are historical judgement (independence vs union; transfer vs Act of Free Choice), so baselined pending a decision |
| references | a page can assert something the database does not contain and nothing notices. `can-1948-2025` named a predecessor `CAN-1866-1948` that does not exist (17 more were dangling); six pages used CSV *column* names as frontmatter keys, so the builder silently dropped five statuses and two ISO codes. The newest signal is **title periods**, added for [issue 25](../../issues/25): a heading can contradict the row while naming no code at all. `blz-1800-2025`, a `superseded` 1800-2025 umbrella, was headed "Belize (to 1886)" — the name of the *separate* `BLZ-1800-1886` row that replaced part of it — and its whole body described the pre-1886 period. Eight more claimed a period their row does not have ("# Gambia (to 1889)" on 1800-2025, "# UAE (1913-1971)" on 1892-2025); all nine are the leftover title of a split that was planned and never applied. Bare prose mentions of absent codes stay WARNINGS — 249 of them are accurate history (deleted rows, rejected splits, hypothetical future rows) — so only an *asserted* code fails: one on a `Predecessor:`/`Successor:` line, or a link to a page that is not there |
| year semantics | `end_year` is **EXCLUSIVE** here and `matchlib` read it **INCLUSIVELY**, so at a transition year — where a predecessor's `end_year` equals its successor's `start_year` — the ENDED period competed for the year, and in any family with a third overlapping row it won on list position. 12 layer-B `(label, source, year)` tuples carrying **190 rows** resolved to a polity that had already ended, including every India transition (1886, 1893, 1914, 1937, 1947, 1949), Greece 1919, Indonesia 1949 and Malaysia 1957. Nothing errored, which is the whole defect: both readings return a live, plausibly-dated polity, so a measurement taken across the seam is wrong silently — issue #77's "four territory-years fall in no polity" was really **one**, the other three being artefacts of the convention, not of the data. The gate compares one NAMED constant, `END_YEAR_EXCLUSIVE`, across the three components that resolve a year (`matchlib.py` and both `match.R`), requires `wiki/README.md` to state it — the issue cited a sentence that file **did not contain** — and asks the matcher whether an ended period still wins its own boundary year. 12 boundaries where it does are baselined, none of them a convention defect: 9 because the successor is not reachable in the predecessor's family at all, 3 because the row starting there is a narrower `polity_type`. **The alias field reads the other way, on purpose, and that half was still unnamed:** alias `year_end` is INCLUSIVE, so a consistent pair is `end_year == year_end + 1`, and `matchlib.assign` honoured an alias over its target's own boundary year by testing `rec[3] <= year <= rec[4]` — the inclusive reading of the exclusive field — for **every** alias, including blanket ones carrying no year bound at all. Deferring to a written `year_end` is deliberate (`Libya Tripolitania ...-1951 -> TRP-1943-1951` asserts 1951 is Tripolitania's); deferring to an alias that claims **no** year is just the same misreading arriving through a second door. Measured: 219 of 903 rules can reach their target's `end_year`, 200 declare it and **19 did not**. Fixing it moved exactly one answer — blanket `belgian congo` at 1960, from `COD-1910-1960` (which ends that year) to `COD-1960-2025` — and **zero** of the 17,599 layer-B `(label, source, year, iso3)` tuples, which is what makes the change safe to make rather than to argue about. `ALIAS_YEAR_END_INCLUSIVE` is now declared by `matchlib.py` and `faostat-era-matching/match.R`, and `wiki/README.md` must state the pairing |
| live name ambiguity | *(guard)* a consumer resolving a label by the polity's own NAME can only answer when one polity of that name is live in the year asked about, so a rename that collides with a live sibling turns a resolving label into `NA` — and `NA` is what an unmapped label looks like too. 17 names are ambiguous today: fifteen are a coarse period listed beside its own sub-periods (issue 49), and two cross prefix families and are tracked as issues 52 and 43 |
| succession geography | `NWR-1900-1905` (Northwestern Rhodesia) listing its successor as Northern **Nigeria**, 4,000 km away. A wrong code looks exactly like a right one, so only the polygons reveal it |
| s2 polygons | ten of the 703 polygons could not be **loaded by s2 at all**, so `sf::st_area()` and `sf::st_intersection()` aborted on them rather than answering — and every other geometry check here reasons in the plane, so none could see it. Two were **GEOS-valid**: `DEU-1871-1919` and `SNW-1814-1905` each carry two non-adjacent edges of one ring 4e-10 m apart (about one ULP), which GEOS reads as no intersection and s2, converting lon/lat to unit vectors first, reads as a crossing. `make_valid()` had nothing to repair and returned them unchanged. The live cost was `FJI-1800-2025`, current today and carrying FAOSTAT area 66 across 203,519 observed rows: intersected with a 0.5° grid its polygon raised `Loop 82 edge 4 crosses loop 332 edge 2` and produced **no cells**, where live neighbour `TON-1800-2025` produced 20. Repaired at source by `scripts/repair_s2_polygons.py`, which exposes the two repairs that disagree — `buffer(0)` and `make_valid` differ by 12,845 km² on Qajar Iran, the very spread `validate_polygon_validity` declined to decide — and defaults to the one that **moves no published area**: measured in ESRI:54034 the repair changes seven of the ten by 0.00 km² and none by more than 21. Eight of the 41 rows in that gate's invalid baseline came valid as a by-product, which is why its pinned count is now 33 |
| simplification loss | *(issue 71)* `polygon_area_km2` was compared against the geometry this repo SHIPS, not the polygon the page names, and the two were not the same thing. `build_database.py`'s `SimplifyPreserveTopology(0.01)` — 1.1 km at the equator — deleted **42% of the Maldives** (299.68 km² at source, 172.62 shipped, 791 atolls almost all smaller than the tolerance) and 48% of the Vatican. So an archipelago could declare the truth about its territory and fail check A on a **correct** polygon, or declare what the rendering measures and understate the country by 42%; `MDV-1800-2025` took the second option and documented the first in prose. **No other gate here can see it**: the loss is planar and internally consistent — valid, s2-loadable, contained, right binding, right feature year, nothing newly overlapping — and check A, the only gate that compares an area to anything, skips every row where both figures are under `--min-km2 200`, which is every polity small enough for 1.1 km of thinning to matter, by construction. The geometry was repaired at source by the build's area budget (`SIMPLIFY_MAX_AREA_CHANGE`, 2026-08-10); this gate is the standing assertion that it stays repaired, and it needs no `data/geodata` because `polygon_feature_index.csv` already publishes each source feature's area from before the build touches it. Measured across all 735 shipped polygons: **max movement 2.1%**, nothing above 5%, the Maldives at 0.0% — and the movement is not all loss, since densification adds up to +1.9% by bowing straight edges onto the great circle a spherical consumer draws |
| gate self-test | *(the checks, checked)* Gates that all pass are indistinguishable, from a green summary, from gates that **cannot** fail. Mutation settles it: 33 cases are shown to fail on an injected defect and to name it, by mutating the GeoPackage, the CSV, the alias map, the wiki or a builder script's own literal. The s2 case is the only mutation here that no other gate could catch, because the injected geometry is planar-valid; it also had to use the real defect's coordinates, since a synthetic thin sliver built on a geodesic-sag theory is accepted by s2 at every latitude and would have read as "this gate cannot fail". One case earned its keep before it ever guarded anything: it declared the wrong file writable, so its mutation wrote through a symlink into the real database, and two OTHER gates caught that immediately. It also stopped a plausible "fix" — symmetrising the containment metric would have reported 26 real historical facts, the Alaska purchase and the Treaty of Trianon among them, as defects to close |
| spherical edges | the published 49th-parallel US/Canada border was **one segment 27.6 degrees of longitude wide**, and under s2 — which `sf` uses by default, and which any geodesic area requires — a segment is a GREAT CIRCLE that bulges poleward between two equal-latitude points. So it rendered as an arc reaching latitude 49.83, **92 km into Canada, booking 12.33 Mha of Canadian prairie to the United States** (eduaguilera/whep#529). 525 distinct edges were affected, displacing 292,481 km² of ground in total; Egypt's 22nd parallel contributed 235,890 ha over two edges. **No existing check could see any of it, by construction**: USA + CAN = 1.0000 in every cell, no overlap, no gap, planar area unchanged to the bit — a clean mutual displacement, and conservation checks detect non-conservation, not misattribution. Half of it was ours: CShapes stores that border with 124 vertices, and `build_database.py`'s own `SimplifyPreserveTopology(0.01)` deleted all 124, because Douglas-Peucker measures deviation from the chord in PLANAR degrees. The build now densifies **after** simplifying |

`.github/workflows/validate.yml` runs **all thirty-seven, plus the self-test,** on push to `main` and on PRs.
(Counted on 2026-08-13: 38 `validate_*`/`crosscheck_*`/`audit_*` scripts. The prose said
thirty-five while there were already thirty-six, which is the drift its own paragraph warns about —
`selftest_gates.py` checks that every gate is NAMED here, not that the number is right.)
The self-test also checks that claim: a gate script the workflow never mentions fails it, because a gate
absent from CI passes on its author's machine and never runs again — which is exactly what happened to the
live-name-ambiguity gate between writing it and registering it.
Every one of them needs only what the repo commits — the CSV, the GeoPackage, the
manifest and the wiki — so none requires the raw sources under `data/geodata`.

Baselines also report **reachability** — whether a consumer can reach the polities
involved through the published FAOSTAT area map. That is what separates a live defect
from a latent one, and it is not obvious: all seven baselined period overlaps are
latent, and none of the 13 polygon gaps is FAOSTAT-mapped. Two findings on this branch
were written up as live and downgraded after checking, which is why the gates now print
it rather than leaving it to be re-derived.

Several carry a baseline so they fail on *new* occurrences while a known backlog
stays tracked in the issues — `validate_polygons.py` has
`scripts/validate_polygons_baseline.txt`, and the matcher, period-overlap,
ISO-collision, reporting-area and succession checks each hold theirs inline.
**Every baseline is bidirectional**: a new case fails, and so does a baselined
case that has been fixed but not yet removed from the list. That second arm is
not decoration — it is what reported that correcting three `iso3` fields had made
two previously unresolvable FAOSTAT areas resolvable.

### Consuming this database

`data/final/polities_manifest.json` is the **contract for downstream consumers**
(regenerate with `scripts/write_manifest.py`, CI-checked). It carries the row
counts, an `identity_sha256` over the fields a consumer resolves against, the
list of live polity codes, and — critically — `dead_polity_codes`: rows with
`wiki_status` of `retired` or `superseded` that **must never receive data**.

Every published field, and who reads it. The manifest grew as the consumer stopped
inferring things it could not infer correctly, so each row here is a fact this repository
decided and a consumer used to get wrong:

| field | what it settles |
|---|---|
| `identity_fields`, `identity_sha256` | which columns a consumer resolves against, and one hash over them. Deliberately excludes polygon fields, so re-measuring an area does not invalidate every consumer while a changed date or status does |
| `counts`, `live_polity_codes`, `dead_polity_codes` | 740 rows, 713 live, 27 dead |
| `dead_status` | which `wiki_status` values mean "must never receive data" — `retired`, `superseded`. Defined **five** times in this repo, so `validate_constants.py` compares the copies; a consumer hardcoding a sixth is how it drifts |
| `claims_polygon_status` | which polygon statuses ASSERT a polygon exists. Not "anything except `unassigned`": that held only while the vocabulary had one non-claiming value, and three of the four legacy statuses asserted no polygon |
| `polygon_gap_polity_codes` | rows whose status claims a polygon the GeoPackage cannot carry, because the feature id was recorded as prose. A consumer asserting the strict invariant is red until this backlog clears; tolerating exactly this set keeps the check sharp for anything new |
| `faostat_unmapped_areas` | why an area maps to no polity, in three kinds a consumer cannot tell apart from the numbers — see below |
| `faostat_area_map`, `label_alias_map`, `iso3_successor_map` | path and sha256 of the three published CSVs |
| `territory_families`, `territory_families_why` | which OTHER families cover one territory — 80 relations over 74 modern codes, collapsed from the successor map's depth-1 rows. `iso3_code` cannot answer this and a consumer matching on it gets nothing: Czech territory in 1950 is held by `CSK`, Montenegrin by `YUG`, Moroccan before 1911 by the local code `MOR` |

Two columns in those CSVs measure the same thing under **transposed names**, and neither was
documented until a consumer-side sweep noticed:

| file | column | blanks | zeros |
|---|---|---|---|
| `label_alias_map.csv` | `observed_rows` | 456 | 29 |
| `faostat_area_polity_map.csv` | `rows_observed` | 0 | 18 |

Both derive from the same registry column with the same coercion, so the difference is word
order, not meaning. They are NOT renamed here: the names are part of a published contract that
a consumer already reads, and breaking that to tidy a word order would cost more than the wart.
Every table upstream of them now says `observed_rows` (issue 95); these two published spellings
are what a deprecation release would have to unify, and `scripts/validate_schema_contract.py`
pins both so a third spelling cannot appear.

The blank counts differ for a real reason rather than an accident. A blank means **not measured
here**, which is distinct from `0` meaning **measured, no rows** — the distinction that was lost
when an earlier version coerced empty to zero and made 456 aliases read as inert. Every row of
the FAOSTAT map is measured in this repository, so it has no blanks; the alias map covers
sources whose data lives in the consumer, so most of its rows cannot be measured here at all.

**`iso3_code` is not ISO-conformant, and a consumer cannot tell which values are.** Measured
on the published database: **56 of the 276** distinct `iso3_code` values are not ISO 3166-1
alpha-3 codes. That is by design and the design is sound — there is no ISO code for
Austria-Hungary, and inventing `AUH` beats leaving it blank — but it is nowhere written down,
and the consumer discovers it by getting no match.

The rule, which holds for **80 of the 81** rows carrying such a code: the local code is the
**polity family's prefix**. `AUH-1800-1859` carries `AUH`, `OTT-1800-1886` carries `OTT`,
`SUD-1899-1934` carries `SUD`. The single exception is consistent with the grouping rule rather
than a mistake: `FCC-1862-1887` French Cochinchina carries `FID`, French Indochina's code,
because it became part of it — the same "groups by modern territory" logic that makes 59 pairs
share a code deliberately.

The classes are: historical entities (`AUH`, `OTT`, `AOF`, `AEF`, `BWI`, `NFL`, `ZNZ`, `NAT`,
`SWA`, `TAN`, `ITS`), colonies of Australia and Canada (`NSW`, `VIC`, `QUE`, `TAS`, `SAA`),
this project's aggregates (`ROW`, `RAFR`, `RASI`, `REUR`, `RLAM`, `RNAM`, `ROCE`), real ISO
3166-3 former codes (`ANT`, `SCG`, `BLX`), and pseudo-codes for entities that also have a modern
one (`ANG` for colonial Angola beside `AGO`, `SUD`, `MOR`, `PAL`, `SER`).

**Distinguish these from the fixed defects listed in the validation table above.** `FRS` for
modern Djibouti was a real error and is gone — Djibouti has an ISO code and nothing holding a
country code could reach it. `SUD` and `ANG` look like the same thing and are not: those
entities have no ISO code, so the prefix is the answer rather than a bug awaiting a fix. Reading
them as unfixed defects is the wrong conclusion, and the table above invites it.

**Why it matters downstream.** A consumer joining `iso3_code` against an ISO-keyed external
dataset silently matches nothing for those 56. That is exactly what blocks the WHEP package's
LUH2 back-cast: the bridge to LUH2 land goes through ISO3, LUH2 is ISO-keyed, so four dissolved
federations carrying **11.88% of production value at 1961** cannot reach it. The data is not
missing; the identifier cannot be matched. Several separately-filed gaps are this one fact.
**The distinction is now published.** `polities_manifest.json` carries `local_iso3_codes` (the 56)
and `local_iso3_why`, so a consumer can tell a local code from an ISO one without discovering it
by getting no match. Read from the gate's baseline rather than restated, so there is one list
and CI gates it. That field is **descriptive only**.

**How dissolved states are coded is now a rule with a gate**, not three coexisting approaches
([issue 55](../../issues/55), `validate_dissolved_iso_codes.py`). An entity with an ISO 3166-3
former alpha-3 code takes **its successor's modern 3166-1 code when its own polity family
continues into a live polity** — the state still exists and only the name changed, so Zaire's
rows carry `COD`, Burma's `MMR`, Southern Rhodesia's `ZWE`, the Afars and Issas' `DJI`, and the
3166-3 code goes unused. It takes **its own 3166-3 code when the family terminates**: `CSK`,
`YUG`, `DDR`, `SUN`, `ANT`, `SCG`, `PCI`. Only the third apparent approach — carrying nothing —
was a defect, and the last of it (the USSR's three rows, fixed to `SUN` on 2026-08-13) is gone.
The gate lists which polities represent each entity, which is a judgement, but DERIVES the
verdict from whether they reach a live polity, so the rule is tested rather than restated.

**Knowing a code is local does not tell you which family holds its territory instead.** That is
the sharper version of the same problem, and it is [issue 82](../../issues/82). A consumer asking
"who held Czech territory in 1950" and matching on `iso3_code` gets nothing: the Czech family
carries `CZE` and Czechoslovakia carries `CSK`. The issue diagnosed this as the aggregates carrying
an EMPTY `iso3_code` — measured on the current database, `F51-1947-1993` carries `CSK` and
`F248-1947-1991` carries `YUG`, so the defect is a *different* code rather than a missing one, the
same shape as the local-versus-ISO case (`MOR-*` beside `MAR-*`) and not a second failure mode.

**The link is derived and published: `territory_families` in the manifest, and
`iso3_successor_map.csv` beside it.** The CSV resolves (modern code, year) → the polity that
actually held the territory, from the database's own predecessor and successor edges — 5,068
year-resolved relations over 76 codes; the manifest field is the family-level collapse of the
depth-1 rows, 80 relations over 74 codes, including every pair the issue named as unlinkable
(`CZE`→`F51`, `SVK`→`F51`, `MAR`→`MOR`, `SRB`→`SER`/`SCG`, `MNE`→`SCG`, `TZA`→`TAN`, `AGO`→`ANG`).
Depth 1 only in the manifest, because that is where the database *asserts* the relation with an
edge; deeper traversals stay in the year-resolved file where a consumer can see the depth it is
trusting. **Absence is not coverage** — `MAR` has no holder for 1904-1910, a real seven-year hole
that no per-family check can see because it falls *between* two families.

**`observed_rows` is not a licence to un-fold an area.** Worth stating because the consumer
tried it and it cost a 13.7x error. The WHEP package derived "areas with observed data" from
these columns and used it to promote areas that FABIO folds into its rest-of-world bucket
(`fabio_code` 999) onto their own numeric aggregation key — reasonable on its face, since an
area reporting thousands of rows of its own should not have them attributed to `ROW-1850-2023`.

Measured on a full-range build, promoting the 16 such areas inflated global `feed` **13.7x**
and `export` 13.2x, with the entire `feed` increase landing on one area (212 Syria, at twelve
times the world total). Something downstream scales on bucket membership, so an area promoted
out of a bucket takes bucket-level magnitudes with it. The promotion is withheld and tracked in
eduaguilera/whep#419.

So these columns answer **"does this label carry data?"** — which is what they were added for,
and what makes an alias inert or live. They do not answer **"can this area stand alone as an
aggregation unit?"**, which depends on the consumer's own aggregation scheme and cannot be
decided here. A consumer that reads the first as the second gets a plausible, large, silent
error.

`faostat_unmapped_areas` carries three distinct reasons an area is unmapped, and the
distinction matters because a consumer should report the first two and **warn** on
anything left over:

- `group_code_min` (5000) — at or above it, FAOSTAT's own regional groups: World, the
  continents, the income bands. Never territories.
- `deliberate_area_codes` (351) — a statistical aggregate published ALONGSIDE its own
  components. 351 "China" is mainland + Hong Kong + Macao + Taiwan, so routing it
  anywhere double-counts all four. This is a decision, not an absence, and inference
  cannot tell the two apart: a consumer that guessed "deliberate" from crosswalk
  membership reported China as *"an area code this project does not know"*.
- `subthreshold_group_codes` (261, 265, 266, 268, 269, 420) — aggregates whose code sits
  BELOW the threshold, so the rule of thumb misses them. 420 is Sub-Saharan Africa; the
  rest are the "(excluding intra-trade)" totals for China and the EU at 12, 15, 25 and 27
  members. Each was found by a real consumer build reporting it as an unknown code, then
  the class was enumerated by sweeping nine input pins rather than waiting for the next
  build to surface the next one.

Compare the hash against your embedded copy to detect drift in one step. The
hash deliberately excludes polygon fields, so re-measuring an area does not
invalidate every consumer, while a changed date or status does.

This exists because the WHEP R package's embedded copy had drifted to **603 rows
against 740** here, with **24 FAOSTAT area codes routing to withdrawn
polities** — and checking meant diffing whole tables across two repositories.

**`identity_sha256` deliberately excludes the polygon fields, so a geometry fix does
not announce itself to a consumer.** That is the right trade for re-measuring an area,
and it means a consumer holding a broken polygon has no way to learn from the hash that
it was repaired. Repairing the ten s2-unloadable polygons on 2026-08-05 left the
identity hash unchanged and `whep::polities` still carrying seven of them — the same ten
minus the three rows its 603-row copy does not have. Nothing downstream can consume that
fix without re-syncing the embedded copy from `polities_database.gpkg`, which is
eduaguilera/whep#530.

**Open work lives in the [issue tracker](../../issues)**, not in comments or state
files — anything recorded only in a CSV tends to be rediscovered by accident.
Useful labels: `decision-needed`, `blocked-on-source`, `guard`, `backlog`.

## Layout

| Path | What |
|------|------|
| `wiki/polities/` | One markdown page per polity (source of truth) |
| `wiki/sources/` | One page per external data source (immutable once ingested) |
| `wiki/README.md` | Wiki schema, link conventions, polygon frontmatter fields |
| `wiki/prompts/` | Agent workflow prompts (ingest, lint, query, autonomous-next) |
| `wiki/log.md` | Chronological record of decisions and open questions |
| `scripts/rebuild.sh` | **The** rebuild command. Orchestrates everything below. |
| `scripts/build_database.py` | Builds `data/final/polities_database.{csv,gpkg}` from wiki + `scripts/sources.yaml` |
| `scripts/repair_s2_polygons.py` | Makes polygons loadable by s2, which `make_valid()` cannot always do. Called by `build_database.py` on write, so a rebuild needs no separate step; run standalone (`--dry-run` to look first) to repair the committed GeoPackage without one |
| `scripts/sources.yaml` | Per-source registry: file path, id column, temporal columns |
| `scripts/sources/<slug>/fetch.{sh,R}` | Fetches the raw source |
| `scripts/sources/<slug>/build.py` | Optional per-source processing step for derived sources |
| `site/build_wiki.sh` | Simplifies the master GPKG for web display (called by `rebuild.sh`) |
| `pipelines/pre1961-matching/match.R` | Crosslinks pre-1961 agricultural data to polity codes (called by `rebuild.sh`) |
| `pipelines/polity-autoimprove/` | Assertion-level data→polity verification: `00_intake.py` (any dataset → evidence bundles), `verify_assertions.workflow.js` (agent verdicts), `apply_verdicts.py`, plus the shared matcher core `matchlib.py`. See its README. |
| `pipelines/faostat-era-matching/` | Matches FAOSTAT-era (1961+) reporting areas by numeric area code |
| `scripts/validate_*.py`, `scripts/audit_family_shadowing.py` | The validation suite (see above) |
| `data/final/` | Committed master database (CSV + GeoPackage) |
| `data/external/` | External reference datasets (COW state system, decolonization events, pre-1961 ag data) |
| `data/geodata/` | Raw polygon sources (gitignored; populated by fetch scripts) |
| `data/compiled/` | Pipeline intermediates (gitignored) |
| `site/` | MapLibre GL JS visualization + copy of the wiki for in-browser reading |

## Polygon sources

Declared in `scripts/sources.yaml`:

| Slug | Source | Native ID | Notes |
|------|--------|-----------|-------|
| `cshapes-2.0` | [ETH Zürich ICR](https://icr.ethz.ch/data/cshapes/) | `gwcode` + year | Primary source for 1886+ state boundaries |
| `cshapes-europe` | ETH Zürich ICR (pre-1886 extension) | `Id` + year | European pre-1886 |
| `gadm-4.1-adm0` / `gadm-4.1-adm1` | [GADM 4.1](https://gadm.org/) | `GID_0` / `GID_1` | Per-country fetch, two levels |
| `gadm-3.6` | GADM 3.6 (legacy subnational) | `GID_1` | Placeholder; no current wiki citations |
| `paine-2024` | [Paine, Qiu & Ricart-Huguet (APSR 2024)](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/9QJVJ1) | `PCS` | Pre-colonial African states |
| `cliopatria` | [Seshat Global History Databank](https://github.com/Seshat-Global-History-Databank/cliopatria) | `Name` + year | Broad historical coverage |
| `histogis-1860-habsburg` | [HistoGIS ACDH-CH](https://histogis.acdh.oeaw.ac.at/) (dissolved crownlands) | `polity_code` | Derived source (has `build.py`) |
| `chgis-v6` | [CHGIS v6](https://dataverse.harvard.edu/dataverse/chgis) Qing provinces | `NAME_PY` + year | Placeholder |
| `usaboundaries-newberry` | Newberry Atlas via R `USAboundaries` | `state_abbr` + year | Placeholder |
| `mapspain-ign` | IGN Spain via R `mapSpain` | `cpro` | Placeholder |
| `geobr-ibge` | IBGE via R `geobr` | `abbrev_state` + year | Placeholder |
| `constructed` | Union / difference / dissolve of features from other fetched sources | `polity_code` | Derived source (has `build.py`). 13 entries: `DEU-1945-1949`, `DEU-1949-1990`, `JPN-1895-1945`, `KOR-1800-1945`, `MAN-1932-1945`, `CHN-1932-1945`, `IRL-1800-1921`, `CODRU-1922-1960`, `BLX-1921-1999`, `MASG-1946-1963`, `AOF-1895-1960`, `CZE-1804-1918`, `EGYSUD-1934-1956` |

## Adding a new polygon source

1. Create `scripts/sources/<slug>/fetch.{sh,R}` — downloads raw file(s) into `data/geodata/<slug>/`.
2. Add an entry to `scripts/sources.yaml`: `file`, optional `layer`, `id_column`, `id_type`, optional `temporal`.
3. For polities where this source applies, set the wiki frontmatter:
   ```yaml
   polygon_source: <slug>
   polygon_feature_id: <value matching id_column>
   polygon_feature_year: <year, for temporal sources>
   polygon_status: assigned
   ```
4. Run `bash scripts/rebuild.sh`. Missing raw files are reported but don't abort the build.

## Adding a constructed (derived) polygon

For polities that have no single external-source match — unions of CShapes halves, dissolves of GADM provinces, etc. — edit `scripts/sources/constructed/build.py`:

1. Write a `build_<polity_code_lowercased>()` function that returns an `ogr.Geometry` in WGS84.
2. Register it in the `BUILDERS` list with a provenance note.
3. Set the wiki page's frontmatter: `polygon_source: constructed`, `polygon_feature_id: <THE-POLITY-CODE>`.
4. Run `bash scripts/rebuild.sh`. `build.py` is called early and writes `data/geodata/constructed/constructed.geojson`, which `build_database.py` then picks up.
