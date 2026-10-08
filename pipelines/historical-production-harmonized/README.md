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

## Value-Scale Corrections

`matched_rows.parquet` carries a per-row `value_divisor` (whep-polities issue 416), 1 except where
`data/final/source_value_scale_corrections.csv` says the source printed a block in another unit --
iia tobacco and hops production 1934-1945 (/100) and hops area 1934-1938 (/10) -- or a single cell
ten times too small (divisor 0.1, issue 424: eight 1933 iia cells that another yearbook volume prints
right, e.g. japan soybean area). The build divides `value` by it (multiplying by the exact inverse
when the divisor is below 1) and refuses a matches file without the column, which would otherwise publish those
cells at 100x. Re-run `pipelines/polity-autoimprove/01_match_and_findings.py` after changing the
table.

## One Row Per Consumer Key (issues 451, 367)

WHEP's `.prepare_historical_production()` reduces every `(year, area, item, unit)` key with
`mean(value)`, and this build used to do the same before handing the table over. Where a key's
candidate rows disagree the consumer then publishes a number equal to none of them: fao1952 prints
Yugoslavia's 1949 dry beans as two rows (38,000 and 783,000 ha) that sum to juan's 821,000, and the
three were averaged. Measured 2026-10-07, **1,706 published keys** were blends like that.

The build now publishes **exactly one row per key** (`year`, `polity_code`, `area_code`,
`item_prod_code`, `item_cbs_code`, `live_anim_code`, `unit`) and refuses to write a table that does
not. `R/resolve_collapse_groups.R` picks the row:

1. within one source: one row; identical rows (one series under two spellings) deduped; a total
   beside its own parts (largest = sum of the rest within 2%, issue 367) keeps the total; anything
   else is `ambiguous` and that source contributes nothing to the key;
2. across the surviving sources: agreement within 2x publishes the first in `PRECEDENCE`
   (WHEP's own `.prod_source_rank()` order, so the source the consumer already labels the key with
   is now the source of its value); a wider disagreement, or no survivor, **withholds** the key.

Every decision that was not a lone row or plain cross-source agreement goes to the tracked
`state/collapse_resolutions.csv`; every withheld key must be listed, with a reason and its
`data_errors.csv` id where one exists, in `state/withheld_keys_baseline.csv`.
`scripts/validate_published_collapse.py` re-derives each decision in CI and fails on a withheld key
the baseline does not document. The tracked table is rewritten only by a default-input run (or with
`WHEP_WRITE_COLLAPSE_STATE=1`), so a run over a test panel leaves the record alone.

Effect on the consumer-collapsed totals, 2026-10-07 panel, before -> after:

```
          before             after              change     withheld keys carried
ha        33,084,288,112     33,033,610,621     -0.153%    52,678,607
tonnes    67,684,626,039     67,629,287,398     -0.082%    58,183,573
heads     84,928,919,271     84,820,666,637     -0.127%    94,805,500

keys 141,974 -> 141,718: 256 withheld (251 cross-source contradictions, 5 unreadable
single-source groups); 1,451 retained keys change value, median ratio 1.001
```

136 of the 256 withheld keys already have a `data_errors.csv` explanation (iia wheat that is spelt
and meslin, Czechoslovak beans that are one component, Mitchell's Japanese "rye", ...). The other
120 are recorded only in the baseline and are open defects.

## Item Withholds

`matched_rows.parquet` also carries `item_withheld` (whep-polities issue 375), TRUE where
`data/final/source_item_withholds.csv` says a source's item is not the commodity it is named for and
no single relabel recovers it: iia `wheat` is spelt and meslin (the IIA extract has no wheat
production or area at all), iia `other sugar crops n.e.c.` is citrus. The build drops those rows and
refuses a matches file without the column.

The item withhold runs BEFORE the resolver above, and it changes what that resolver sees. iia `wheat`
used to contest 68 keys with juan's real wheat at a median 100x below it, so all 68 were withheld as
contradictions (they were 68 of the 256 above); 9 more keys had iia alone and published spelt and
meslin as wheat. Measured on the 2026-10-07 panel, with only `item_withheld` toggled:

```
keys 141,718 -> 141,721: 65 leave (9 iia wheat, 56 iia other sugar crops), 68 return with juan's
wheat; no other key changes value. Withheld keys 256 -> 188.
          before             after
ha        33,034,033,576     33,077,110,552     +43,076,976 = +43,995,600 juan wheat - 918,624 iia rows
tonnes    67,629,892,455     67,686,662,269     +56,769,814 = +57,321,350 juan wheat - 551,536 iia rows
```

## Value-Null Corrections

`matched_rows.parquet` also carries a per-row `value_is_null` (whep-polities issue 414): TRUE on the
cells `data/final/source_value_null_corrections.csv` withholds -- iia zeros whose scanned page prints
a dash, `...`, the see-notes marker `-o)`, or a non-zero figure, or whose own other axis refutes
them. The build sets their value to NA, so the `!is.na(value)` filter drops them instead of
averaging a 0 into the polity-year, and refuses a matches file without the column.

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
- `value_grid`
- `source_grid_verdict`

## Value Precision

`value` is a printed number, and a large part of the panel was printed coarsely: 47% of the non-zero
layer-B values sit on a 1000-grid (whep-polities #446), so `1,000` is often "somewhere in 500-1,500",
not an exact point. Two columns carry that, derived by `matchlib.value_precision` in stage 01 and
documented for consumers in `data/final/polities_manifest.json` under `value_precision`:

- `value_grid` -- the step the value cannot be assumed finer than, **in the row's output unit**. Treat
  it as a `+/- value_grid/2` interval around `value`, never as a shift of it. It is the coarser of
  (a) the largest power of ten (0.001 to 1,000,000) that every non-zero value of the row's own series
  `(source, label, item, unit, indicator[, era])` is a multiple of -- needs 5 non-zero values, and a
  series that is not on any grid above the 0.001 floor reads 0.001, meaning "that fine or finer" -- and
  (b) 1000 / 100 where the source's verdict is `coarse_1000` / `coarse_100`. It follows the value's own
  rescaling: the printed grid is multiplied by the `1000 tonnes` style unit multiplier and divided by
  the #416 value-scale divisor. The published row (one per consumer key, `R/resolve_collapse_groups.R`) carries the grid of
  the candidate row it was chosen from; where several rows carrying the SAME number were merged it
  keeps the COARSEST of their grids, because a number is no more precise than its least precise printing. **NULL means
  unknown, not exact**: 3.4% of the harmonized rows (short series from a source without a coarse
verdict).
- `source_grid_verdict` -- `coarse_1000`, `coarse_100`, `mixed` or `fine`, the (source, unit, era)
  verdict of `pipelines/polity-autoimprove/state/source_value_precision.csv`. `mixed` (the majority of
  the panel: `juan` crops, `iia` overall) means the source prints both coarse and fine values there, so
  the verdict cannot say whether THIS value is rounded -- read `value_grid` for that. Only `iia` is
  split by era (the 1934 volume boundary; a period row takes its end year).

Neither column is proof that one value was rounded: a grid is a fact about a series or a source. A
published `0` in a series on a coarse grid may be a value below half a step; the 201 such zeros are
enumerated in `state/grid_ambiguous_zeros.csv`. The build refuses a matches file without the columns,
which would otherwise publish the panel as exact again. Gate: `scripts/validate_value_grid_channel.py`.

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
