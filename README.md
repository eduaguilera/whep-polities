# WHEP Polities

Historical polities database for the [Who Has Eaten the Planet?](https://www.whep.eu/) (WHEP) project. Each polity is a territorial-economic unit with a defined extent over a continuous time period from 1800 to 2025.

## Architecture

**The wiki is the source of truth.** Every polity has a curated page at `wiki/polities/<code>.md` with YAML frontmatter that declares its identity, status, and the provenance of its polygon. The CSV and GeoPackage under `data/final/` are derived artifacts, rebuilt by `scripts/build_database.py`.

```
 wiki/polities/*.md          ← you edit this (source of truth)
       │
       ▼
 scripts/build_database.py   ← joins wiki + raw polygon sources
       │
       ▼
 data/final/
   polities_database.csv     ← committed (~60 KB)
   polities_database.gpkg    ← committed (~7 MB, 500+ polygons)
       │
       ▼
 site/build_wiki.sh          ← simplifies for web
       │
       ▼
 site/polities.{csv, geojson}   +   site/wiki/ (rendered markdown)
```

## Rebuilding from scratch

Raw polygon inputs (CShapes, GADM, Cliopatria, …) live under `data/geodata/<slug>/` and are **gitignored**. Each source has a fetch script that re-downloads it from its original location:

```bash
# 1. Fetch raw polygons (pick the sources you need)
bash scripts/sources/cshapes-2.0/fetch.sh
bash scripts/sources/cshapes-europe/fetch.sh
bash scripts/sources/cliopatria/fetch.sh
bash scripts/sources/paine-2024/fetch.sh
bash scripts/sources/histogis-1860-habsburg/fetch.sh
bash scripts/sources/gadm-4.1/fetch.sh

# 2. Rebuild every derived artifact in one command:
#    - data/final/polities_database.{csv,gpkg}
#    - site/polities.{csv,geojson}
#    - site/wiki/ (markdown copy for the in-browser reader)
bash scripts/rebuild.sh
```

`scripts/rebuild.sh` is a thin wrapper that runs
`python3 scripts/build_database.py` then `bash site/build_wiki.sh`.
You don't have to run the fetches if you only want to consume the committed `data/final/polities_database.gpkg` — it's self-contained.

## Layout

| Path | What |
|------|------|
| `wiki/polities/` | One markdown page per polity (source of truth) |
| `wiki/sources/` | One page per external data source (immutable once ingested) |
| `wiki/README.md` | Wiki schema, link conventions, polygon frontmatter fields |
| `wiki/prompts/` | Agent workflow prompts (ingest, lint, query, autonomous-next) |
| `wiki/log.md` | Chronological record of decisions and open questions |
| `scripts/rebuild.sh` | One-shot rebuild of every derived artifact (runs `build_database.py` + `site/build_wiki.sh`) |
| `scripts/build_database.py` | Builds `data/final/polities_database.{csv,gpkg}` from wiki + `scripts/sources.yaml` |
| `scripts/sources.yaml` | Per-source registry: file path, id column, temporal columns |
| `scripts/sources/<slug>/fetch.{sh,R}` | Fetches the raw source |
| `scripts/histogis_habsburg.py` | Ad-hoc derived-source builder (dissolves HistoGIS crownlands into Cisleithania/Transleithania) |
| `data/final/` | Committed master database (CSV + GeoPackage) |
| `data/external/` | External reference datasets (COW state system, decolonization events, pre-1961 ag data) |
| `data/geodata/` | Raw polygon sources (gitignored; populated by fetch scripts) |
| `pipelines/pre1961-matching/` | R pipeline that crosslinks pre-1961 agricultural data against the polity database |
| `site/` | MapLibre GL JS visualization |

## Polygon sources

Declared in `scripts/sources.yaml`:

| Slug | Source | Native ID |
|------|--------|-----------|
| `cshapes-2.0` | [ETH Zürich ICR](https://icr.ethz.ch/data/cshapes/) | `gwcode` + year |
| `cshapes-europe` | ETH Zürich ICR (pre-1886 extension) | `Id` + year |
| `gadm-4.1-adm0` / `gadm-4.1-adm1` | [GADM 4.1](https://gadm.org/) | `GID_0` / `GID_1` |
| `gadm-3.6` | GADM 3.6 (legacy subnational) | `GID_1` |
| `paine-2024` | [Paine, Qiu & Ricart-Huguet (APSR 2024)](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/9QJVJ1) | `PCS` |
| `cliopatria` | [Seshat Global History Databank](https://github.com/Seshat-Global-History-Databank/cliopatria) | `Name` + year |
| `histogis-1860-habsburg` | [HistoGIS ACDH-CH](https://histogis.acdh.oeaw.ac.at/) (dissolved crownlands) | `polity_code` |
| `chgis-v6` | [CHGIS v6](https://dataverse.harvard.edu/dataverse/chgis) Qing provinces | `NAME_PY` + year |
| `usaboundaries-newberry` | Newberry Atlas via R `USAboundaries` | `state_abbr` + year |
| `mapspain-ign` | IGN Spain via R `mapSpain` | `cpro` |
| `geobr-ibge` | IBGE via R `geobr` | `abbrev_state` + year |
| `constructed` | Hand-authored (Antarctic sector, Uqair, point buffers) | `polity_code` |

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
