# Historical Production Harmonized

Build a WHEP-compatible historical production table from the raw historical
printed-statistics union currently stored at:

`/home/usuario/Nextcloud/whep/layer_b/consolidated_layer_b.parquet`

The output is intentionally **not** named "Layer B".  "Layer B" is only the
current raw-staging nickname for the consolidated printed-statistics sources
before WHEP item/unit/polity harmonization.  The harmonized artifact is named:

- `historical_production_harmonized.parquet`
- `historical_production_harmonized.csv`

Default output directory:

`/home/usuario/Nextcloud/whep/historical_production_harmonized/`

## Build

Use the WHEP renv:

```bash
RENV_PROJECT=/home/usuario/WHEP Rscript --vanilla pipelines/historical-production-harmonized/build.R
```

Optional arguments:

```bash
Rscript build.R <raw_layer_b_parquet> <matched_rows_parquet> <output_dir>
```

## Constant-Territory Smoke Runs

The example in `examples/austria_wheat_constant_territory_smoke.R` compares
three ways to adapt historical wheat production rows to present-day Austria:

- uniform area weighting
- total cropland weighting from prepared WHEP/LPJmL inputs
- wheat-pattern weighting using `type_cropland` for the crop's LUH2 type and
  `crop_patterns` for the WHEP item

It currently assumes the prepared inputs exist locally at:

`/home/usuario/WHEP/LPJmL_inputs/whep/inputs`

Run it with the WHEP renv:

```bash
RENV_PROJECT=/home/usuario/WHEP Rscript --vanilla -e 'source("/home/usuario/WHEP/renv/activate.R"); source("pipelines/historical-production-harmonized/examples/austria_wheat_constant_territory_smoke.R")'
```

The output is written to:

`/home/usuario/Nextcloud/whep/historical_production_harmonized/smoke_runs/austria_wheat_constant_territory_smoke.csv`

## Output Schema

The main table is close to WHEP `build_primary_production()` output, with extra
provenance:

- `year`
- `area_code`
- `polity_area_code`
- `polity_code`
- `reporting_polity_code`
- `reporting_polity_name`
- `reporting_polity_has_geometry`
- `item_prod_code`
- `item_prod_name`
- `item_cbs_code`
- `item_cbs_name`
- `live_anim_code`
- `unit`
- `value`
- `source`
- `raw_source`
- `raw_country`
- `raw_item`
- `raw_item_code`
- `raw_unit`
- `source_detail`
- `match_method`

## Included

The build includes rows that can be mapped without source-specific split
assumptions:

- crop/product `tonnes`, `tons`/`Tons`, `1000 tonnes`
- crop area `ha`, `1000 hectares`
- unambiguous livestock stock `heads`, `1000 heads`
- sources `juan`, `mitchell`, `iia`, `fao1952`, `sa_colonial`

The build excludes rows needing stronger assumptions:

- bushels/gallons and other units requiring commodity-specific conversions
- people, tractors, pesticides, fertilizers, carcass weights
- ambiguous animal aggregates like cattle, pigs, chickens/poultry unless split
  rules are explicitly added
- aggregate regional rows
- **period averages — rows carrying a period label instead of a year.** This is
  the largest single exclusion and it was previously implicit, visible only as a
  `!is.na(year)` filter, so a coverage measurement read the gap as missing
  sources rather than as a deliberate exclusion (whep-polities #310):

  ```
  layer B rows                          192,670
  valued rows with NO year                9,865   5.12%   iia 6,163 | fao1952 3,702
     ...carrying a period label           9,865   100%    none is genuinely undated
  distinct periods                           21
     1934-1938 5,629 | 1925-1929 1,649 | 1928-1932 1,600 | 1909-1913 845
  series affected (label, item)           3,589   over 100 items and 401 labels
  ```

  These are the printed sources' five-year-mean convention, not sparse residue.
  They are excluded because a period average is not an observation of a year and
  placing it on one would invent a datum — but note the asymmetry with the
  assertion pipeline, which does reason about them: `matchlib.eff_year` reads the
  period's end year, `01_match_and_findings.py` routes a period average to the
  polity covering the MOST of its span (the midpoint was rejected on
  measurement), and `00_intake.py` refuses to run without `--period-col` (#437).
  None of that reaches here, because this build has no `period` column at all.

  If they are ever to be published, the option that needs no semantic decision is
  a separate table keyed on `(period_start, period_end)` rather than a flag on a
  chosen year — choosing the year is what #434's four lifetime-overlap failures
  ran into.
