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
