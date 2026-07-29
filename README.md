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

Eighteen checks guard the database. Each exists because that class of error was
**found in the data**, not hypothesised, so they are worth keeping green:

```bash
# the published contract still matches the wiki
python3 scripts/build_database.py --check
python3 scripts/write_manifest.py --check
python3 scripts/write_faostat_area_map.py --check
python3 scripts/write_label_alias_map.py --check
python3 scripts/update_wiki_index.py --check

# provenance and internal consistency
python3 scripts/validate_citations.py
python3 scripts/validate_constants.py
python3 scripts/validate_aliases.py
python3 scripts/validate_unranged_aliases.py
python3 scripts/crosscheck_matchers.py
python3 scripts/audit_family_shadowing.py

# identity and periodisation
python3 scripts/validate_iso_codes.py
python3 scripts/validate_iso_collisions.py
python3 scripts/validate_period_overlaps.py
python3 scripts/validate_reporting_areas.py

# geometry
python3 scripts/validate_polygons.py
python3 scripts/validate_spatial_containment.py
python3 scripts/validate_succession_geography.py   # needs the built .gpkg, so local only
```

| check | what it caught when first run |
|---|---|
| `build_database.py --check` | a wiki edit never propagated to the CSV; later, `"NA"` text stored as a literal string |
| `write_manifest.py --check` | a stale alias-map fingerprint after aliases changed |
| citations | 17 citations pointing at source files that were never ingested |
| constants | `DEAD_STATUS` is defined **five** times, and `CLAIMS_POLYGON` excluded four statuses that 11 rows with geometry were using |
| aliases | five aliases silently **inert** — two had the target sitting in the `confidence` column |
| unranged aliases | the `"Syria"` alias had no year range and pointed at `SYR-1946-1967`, so every year — including 2020 — resolved to a polity that ended in 1967, across 162 observed rows. Unlike an inert alias it worked; it just worked wrongly |
| crosscheck matchers | the two independent matchers disagreed on three FAOSTAT areas, including Serbia 2006-2008 existing **twice** |
| shadowing | Alaska outranking the USA and absorbing ~7,600 rows of mainland data |
| iso codes | `FRS-1977-2025` is modern Djibouti and carried `iso3: FRS`; DJI is the real code, so nothing holding a country code could reach it. Also Sudan as `SUD`, colonial Angola as `ANG` |
| iso collisions | *(guard)* 59 pairs already share a code over overlapping years **by design**, since `iso3` groups by modern territory. The gate is that the set must not grow |
| period overlaps | four same-family pairs cover the same years, so a year-aware matcher must guess. `PER-1825-1909` duplicates two rows that already tile its span exactly |
| reporting areas | six GADM territories claimed by **two** aggregates each — Palau and the Northern Marianas sit in both Asia Other and Oceania Other. Hidden because the RoW union deduplicates |
| polygons A | 8 polities carrying **another country's** polygon — San Marino had Albania's (470× too large), Indonesia had India's |
| polygons C | 28 polities declaring a polygon the build never attached |
| polygons D | 13 pages claiming `status: reviewed` with zero source citations |
| spatial containment | one polity's polygon swallowing a neighbour's; a family's consecutive periods overlapping by under half |
| succession geography | `NWR-1900-1905` (Northwestern Rhodesia) listing its successor as Northern **Nigeria**, 4,000 km away. A wrong code looks exactly like a right one, so only the polygons reveal it |

`.github/workflows/validate.yml` runs all of them on push to `main` and on PRs,
except `validate_succession_geography.py`, which needs the built GeoPackage.
The rest need only what the repo commits, so they work without `data/geodata`.

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
