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

Twenty-five checks guard the database, and a twenty-sixth checks the checks. Most
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
python3 scripts/write_feature_index.py --check

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
python3 scripts/validate_cow_codes.py
python3 scripts/validate_cross_family_names.py
python3 scripts/validate_period_overlaps.py
python3 scripts/validate_period_gaps.py
python3 scripts/validate_reporting_areas.py
python3 scripts/validate_code_year_agreement.py
python3 scripts/validate_references.py
python3 scripts/validate_map_area_year.py
python3 scripts/validate_alias_year_coverage.py

# geometry
python3 scripts/validate_polygons.py
python3 scripts/validate_polygon_validity.py
python3 scripts/validate_polygon_period_fit.py
python3 scripts/validate_polygon_binding_determinism.py
python3 scripts/validate_spatial_containment.py
python3 scripts/validate_family_areas.py
python3 scripts/validate_succession_geography.py   # reads the committed .gpkg; runs in CI too
python3 scripts/validate_chain_integrity.py        # CSV + wiki only, no geometry

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
| constants | `DEAD_STATUS` is defined **five** times, and `CLAIMS_POLYGON` excluded four statuses that 11 rows with geometry were using |
| aliases | five aliases silently **inert** — two had the target sitting in the `confidence` column |
| alias chain overlaps | *(guard)* an alias `year_end` is INCLUSIVE while a polity `end_year` is EXCLUSIVE, so consecutive aliases for one label both cover the boundary year and match order decides which polity a value lands in. 18 chains do, down from 25: the seven cleared on 2026-08-05 were the ones whose earlier alias claimed a year its successor covers, clipped after checking against the observations that nothing would go unmatched (issue 90 group A -- 58 aliases, 1,544 rows). The rate depends on how they were written — 18 of 31 hand-entered any-source chains against **0 of 7** generated with `year_end = polity_end_year - 1` — so the convention demonstrably removes it. The safe half is now fixed rather than gated: 58 aliases whose boundary year a successor alias already covers were clipped (issue 90). 209 aliases still overclaim, of which 24 (label, year) pairs carrying 229 rows have NO covering successor and must not be clipped -- those need a target or a period boundary, not a range edit |
| unranged aliases | the `"Syria"` alias had no year range and pointed at `SYR-1946-1967`, so every year — including 2020 — resolved to a polity that ended in 1967, across 162 observed rows. Unlike an inert alias it worked; it just worked wrongly |
| crosscheck matchers | the two independent matchers disagreed on three FAOSTAT areas, including Serbia 2006-2008 existing **twice** |
| shadowing | Alaska outranking the USA and absorbing ~7,600 rows of mainland data |
| iso codes | `FRS-1977-2025` is modern Djibouti and carried `iso3: FRS`; DJI is the real code, so nothing holding a country code could reach it. Also Sudan as `SUD`, colonial Angola as `ANG` |
| cross-family names | `TAN-1922-1964` overlapping `TZA-1961-1964`, and `MAR-1911-1958` overlapping `MOR-1956-1958` — the earlier row's end year running past its successor's start. Invisible to the period-overlap gate, which only compares within one prefix. Latent rather than live: the inert twins are unmapped, so the consumer never sees both |
| cow codes | `ICN-1800-2025` (Canary Islands) carried COW code **20**, which is Canada. The Canaries are not a COW state — they are part of Spain, 230 — so the value was removed rather than corrected, which would have swapped one collision for another. Its `iso3` and polygon were both fine, so no other check could see it |
| iso collisions | *(guard)* 59 pairs already share a code over overlapping years **by design**, since `iso3` groups by modern territory. The gate is that the set must not grow |
| local iso codes | *(guard)* `iso3_code` is **not ISO-conformant and cannot be** — there is no ISO 3166 code for Austria-Hungary, so this database invents `AUH`. 56 of its 276 values are local like that, and a consumer joining against ISO-keyed data silently matches none of them; it is what stops four dissolved federations reaching WHEP's LUH2 land series. The vocabulary is therefore an interface, and the gate is that it does not change unreviewed. Publishing the local/ISO distinction machine-readably is [issue 55](../../issues/55) |
| period overlaps | four same-family pairs cover the same years, so a year-aware matcher must guess. `PER-1825-1909` duplicates two rows that already tile its span exactly |
| reporting areas | six GADM territories claimed by **two** aggregates each — Palau and the Northern Marianas sit in both Asia Other and Oceania Other. Hidden because the RoW union deduplicates |
| polygons A | 8 polities carrying **another country's** polygon — San Marino had Albania's (470× too large), Indonesia had India's |
| polygons C | 28 polities declaring a polygon the build never attached |
| polygons D | 13 pages claiming `status: reviewed` with zero source citations |
| family areas | *(guard)* check A needs a **recorded** area to compare against, and 76% of rows claiming a polygon have none. Comparing a period to its own family's median needs no reference and covers all of them. Two anomalies today, both legitimate |
| spatial containment | one polity's polygon swallowing a neighbour's; a family's consecutive periods overlapping by under half |
| code/year agreement | *(guard)* a polity code is documented as `PREFIX-start-end`, so consumers read years straight off the identifier rather than joining. Two codes disagree with their own columns — `TAN-1922-1964` ends 1961, `NNG-1949-1963` ends 1969 — and the consumer's aliases were written against the CODE, so two of them resolve 1962-1964 to a polity its columns say had ended. Both are historical judgement (independence vs union; transfer vs Act of Free Choice), so baselined pending a decision |
| live name ambiguity | *(guard)* a consumer resolving a label by the polity's own NAME can only answer when one polity of that name is live in the year asked about, so a rename that collides with a live sibling turns a resolving label into `NA` — and `NA` is what an unmapped label looks like too. 17 names are ambiguous today: fifteen are a coarse period listed beside its own sub-periods (issue 49), and two cross prefix families and are tracked as issues 52 and 43 |
| succession geography | `NWR-1900-1905` (Northwestern Rhodesia) listing its successor as Northern **Nigeria**, 4,000 km away. A wrong code looks exactly like a right one, so only the polygons reveal it |
| gate self-test | *(the checks, checked)* Gates that all pass are indistinguishable, from a green summary, from gates that **cannot** fail. Mutation settles it: ten are shown to fail on an injected defect and to name it — three geometry gates that mutate the GeoPackage, and seven that mutate the CSV, the alias map or the wiki. The tenth case earned its keep before it ever guarded anything: it declared the wrong file writable, so its mutation wrote through a symlink into the real database, and two OTHER gates caught that immediately. It also stopped a plausible "fix" — symmetrising the containment metric would have reported 26 real historical facts, the Alaska purchase and the Treaty of Trianon among them, as defects to close |

`.github/workflows/validate.yml` runs **all twenty-four, plus the self-test,** on push to `main` and on PRs.
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
| `faostat_area_map`, `label_alias_map` | path and sha256 of the two published CSVs |

Two columns in those CSVs measure the same thing under **transposed names**, and neither was
documented until a consumer-side sweep noticed:

| file | column | blanks | zeros |
|---|---|---|---|
| `label_alias_map.csv` | `observed_rows` | 456 | 29 |
| `faostat_area_polity_map.csv` | `rows_observed` | 0 | 18 |

Both derive from the same registry column with the same coercion, so the difference is word
order, not meaning. They are NOT renamed here: the names are part of a published contract that
a consumer already reads, and breaking that to tidy a word order would cost more than the wart.

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
and CI gates it. That field is **descriptive only** — how dissolved states *should* be coded is
still [issue 55](../../issues/55), where three approaches coexist in the data today.

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
