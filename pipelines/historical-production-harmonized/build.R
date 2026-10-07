#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)

layer_b_path <- if (length(args) >= 1L) {
  path.expand(args[[1]])
} else {
  "/home/usuario/Nextcloud/whep/layer_b/consolidated_layer_b.parquet"
}
matches_path <- if (length(args) >= 2L) {
  path.expand(args[[2]])
} else {
  "/home/usuario/whep-polities/pipelines/polity-autoimprove/state/matched_rows.parquet"
}
out_dir <- if (length(args) >= 3L) {
  path.expand(args[[3]])
} else {
  "/home/usuario/Nextcloud/whep/historical_production_harmonized"
}

file_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
script_dir <- if (length(file_arg)) {
  dirname(normalizePath(sub("^--file=", "", file_arg[[1L]])))
} else {
  file.path(getwd(), "pipelines/historical-production-harmonized")
}
source(file.path(script_dir, "R", "resolve_collapse_groups.R"))
# The tracked resolution table describes the real panel; an explicit-argument run over another
# panel still writes its outputs but leaves the record alone unless asked.
write_tracked_state <- length(args) < 2L || nzchar(Sys.getenv("WHEP_WRITE_COLLAPSE_STATE"))

if (!requireNamespace("whep", quietly = TRUE)) {
  if (requireNamespace("pkgload", quietly = TRUE)) {
    pkgload::load_all("/home/usuario/WHEP-polities-reconcile", quiet = TRUE)
  } else {
    stop("Package `whep` is not available and `pkgload` is not installed.")
  }
}

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

normalise_item_code <- function(x) {
  out <- suppressWarnings(as.integer(as.numeric(x)))
  dplyr::if_else(is.na(out), NA_character_, as.character(out))
}

normalise_item_name <- function(x) {
  x <- tolower(trimws(as.character(x)))
  x <- stringr::str_replace_all(x, "[^a-z0-9]+", " ")
  stringr::str_squish(x)
}

output_unit <- function(unit) {
  dplyr::case_when(
    unit %in% c("tonnes", "tons", "1000 tonnes") ~ "tonnes",
    unit %in% c("ha", "1000 hectares", "1000000 hectares") ~ "ha",
    unit %in% c("heads", "1000 heads") ~ "heads",
    TRUE ~ NA_character_
  )
}

unit_multiplier <- function(unit) {
  dplyr::case_when(
    unit %in% c("1000 tonnes", "1000 hectares", "1000 heads") ~ 1000,
    unit == "1000000 hectares" ~ 1e6,
    TRUE ~ 1
  )
}

same_or_both_na <- function(x, y) {
  x <- as.character(x)
  y <- as.character(y)
  (is.na(x) & is.na(y)) | (!is.na(x) & !is.na(y) & x == y)
}

same_or_both_na_num <- function(x, y, tolerance = sqrt(.Machine$double.eps)) {
  x <- as.numeric(x)
  y <- as.numeric(y)
  (is.na(x) & is.na(y)) |
    (!is.na(x) & !is.na(y) & abs(x - y) <= tolerance)
}

require_cols <- function(df, cols, label) {
  missing <- setdiff(cols, names(df))
  if (length(missing) > 0L) {
    stop(label, " is missing required columns: ", paste(missing, collapse = ", "))
  }
}

validate_alignment <- function(layer_b, matches) {
  # `country` in matched_rows is the label a row was ROUTED under, after the OCR
  # spelling corrections (issue 552) and the item-scoped label corrections
  # (issue 675) rewrite it; layer B's own label travels as `source_label_raw`.
  # Comparing the routed label against layer B stopped this build on the 25 OCR
  # rows, so compare the raw one wherever the matcher wrote it.
  if ("source_label_raw" %in% names(matches)) {
    # A relabelled row also has its `iso3c` cleared, because the ISO code came with the
    # territory it was misfiled under (924 rows on 2026-10-07). Restore layer B's own code on
    # exactly those rows before comparing, so the check still catches a misaligned row
    # everywhere else instead of stopping on every relabelling.
    relabelled <- !same_or_both_na(matches$country, matches$source_label_raw)
    if ("iso3c" %in% names(matches) && "iso3c" %in% names(layer_b)) {
      matches$iso3c[relabelled] <- layer_b$iso3c[relabelled]
    }
    matches$country <- matches$source_label_raw
  }
  check_cols <- intersect(
    c("source", "country", "iso3c", "year", "item", "unit"),
    intersect(names(layer_b), names(matches))
  )
  bad_cols <- check_cols[
    vapply(
      check_cols,
      \(col) !all(same_or_both_na(layer_b[[col]], matches[[col]])),
      logical(1)
    )
  ]

  if ("value" %in% names(layer_b) && "value" %in% names(matches)) {
    if (!all(same_or_both_na_num(layer_b$value, matches$value))) {
      bad_cols <- c(bad_cols, "value")
    }
  }

  if (length(bad_cols) > 0L) {
    stop(
      "Layer B rows and WHEP match rows are not aligned for: ",
      paste(bad_cols, collapse = ", ")
    )
  }
  invisible(TRUE)
}

manual_product_aliases <- function(items) {
  aliases <- tibble::tribble(
    ~item_alias, ~item_prod_code,
    "rice paddy", "27",
    "dry beans", "176",
    "dry peas", "187",
    "broad beans", "181",
    "broad beans horse beans dry", "181",
    "chick peas", "191",
    "cacao", "661",
    "cacao beans", "661",
    "cottonseed", "329",
    "cotton seed", "329",
    "groundnuts", "242",
    "funflower seed", "267",
    "flax fiber", "773",
    "flax fibre", "773",
    "jute allied fibres", "780",
    "jute allied fibers", "780",
    "hemp fiber", "777",
    "hemp fibre", "777",
    "abaca", "809",
    "manila fibre abaca", "809",
    "manila fiber abaca", "809"
  )

  aliases |>
    dplyr::left_join(
      items |>
        dplyr::select(
          "item_prod_code",
          "item_prod",
          "item_cbs",
          "item_cbs_code",
          "group",
          "live_anim",
          "live_anim_code"
        ),
      by = "item_prod_code"
    ) |>
    dplyr::filter(!is.na(.data$item_prod)) |>
    dplyr::mutate(
      item_code = NA_character_,
      item_alias = normalise_item_name(.data$item_alias)
    ) |>
    dplyr::select(
      "item_code",
      "item_alias",
      "item_prod",
      "item_prod_code",
      "item_cbs",
      "item_cbs_code",
      "group",
      "live_anim",
      "live_anim_code"
    )
}

product_lookup <- function() {
  item_cols <- c(
    "item_prod",
    "item_prod_code",
    "item_cbs",
    "item_cbs_code",
    "group",
    "live_anim",
    "live_anim_code"
  )
  items <- whep::items_prod_full |>
    dplyr::filter(
      .data$group %in% c("Primary crops", "Crop products", "Livestock products"),
      !is.na(.data$item_prod_code),
      !is.na(.data$item_cbs_code)
    )

  by_code <- items |>
    dplyr::mutate(
      item_code = normalise_item_code(.data$item_prod_code),
      item_alias = NA_character_
    ) |>
    dplyr::filter(!is.na(.data$item_code)) |>
    dplyr::select(
      "item_code",
      "item_alias",
      dplyr::all_of(item_cols)
    )

  alias_cols <- intersect(
    c("item_prod", "Name", "Name_biomass", "Name_Eurostat"),
    names(items)
  )
  by_alias <- purrr::map_dfr(
    alias_cols,
    \(col) {
      items |>
        dplyr::mutate(
          item_code = NA_character_,
          item_alias = normalise_item_name(.data[[col]])
        ) |>
        dplyr::select(
          "item_code",
          "item_alias",
          dplyr::all_of(item_cols)
        )
    }
  ) |>
    dplyr::bind_rows(manual_product_aliases(items)) |>
    dplyr::filter(!is.na(.data$item_alias), .data$item_alias != "") |>
    dplyr::distinct(.data$item_alias, .data$item_prod_code, .keep_all = TRUE) |>
    dplyr::add_count(.data$item_alias, name = ".n_alias") |>
    dplyr::filter(.data$.n_alias == 1L) |>
    dplyr::select(-dplyr::all_of(".n_alias"))

  dplyr::bind_rows(by_code, by_alias)
}

stock_lookup <- function() {
  animals <- whep::animals_codes |>
    dplyr::add_count(.data$Item_Code, name = ".n_item_code") |>
    dplyr::filter(.data$.n_item_code == 1L) |>
    dplyr::transmute(
      item_code = as.character(.data$Item_Code),
      item_alias = normalise_item_name(.data$item_cbs),
      item_prod = .data$item_cbs,
      item_prod_code = as.character(.data$item_cbs_code),
      item_cbs = .data$item_cbs,
      item_cbs_code = as.numeric(.data$item_cbs_code)
    )

  manual <- tibble::tribble(
    ~item_alias, ~item_prod_code,
    "buffaloes", "946",
    "rabbits and hares", "1140",
    "beehives", "1181"
  ) |>
    dplyr::left_join(
      animals |>
        dplyr::select(
          item_prod_code,
          item_prod,
          item_cbs,
          item_cbs_code
        ),
      by = "item_prod_code"
    ) |>
    dplyr::mutate(
      item_code = NA_character_,
      item_alias = normalise_item_name(.data$item_alias)
    ) |>
    dplyr::select(
      "item_code",
      "item_alias",
      "item_prod",
      "item_prod_code",
      "item_cbs",
      "item_cbs_code"
    )

  dplyr::bind_rows(animals, manual) |>
    dplyr::distinct(.data$item_code, .data$item_alias, .keep_all = TRUE)
}

polity_lookup <- function() {
  whep::polity_area_crosswalk |>
    dplyr::filter(!is.na(.data$polity_code)) |>
    dplyr::mutate(
      area_code = dplyr::coalesce(.data$area_code, .data$polity_area_code),
      has_area_code = !is.na(.data$area_code),
      has_polity_area_code = !is.na(.data$polity_area_code),
      is_matched = .data$mapping_status == "matched"
    ) |>
    dplyr::arrange(
      .data$polity_code,
      dplyr::desc(.data$has_area_code),
      dplyr::desc(.data$has_polity_area_code),
      dplyr::desc(.data$is_matched)
    ) |>
    dplyr::distinct(.data$polity_code, .keep_all = TRUE) |>
    dplyr::transmute(
      whep_code = .data$polity_code,
      area_code = as.numeric(.data$area_code),
      polity_area_code = as.numeric(.data$polity_area_code),
      polity_code = .data$polity_code,
      reporting_polity_code = .data$polity_code,
      reporting_polity_name = .data$polity_name,
      reporting_polity_has_geometry = .data$has_geometry
    )
}

base_cols <- function() {
  c(
    "raw_source",
    "source_detail",
    "raw_country",
    "iso3c",
    "raw_item",
    "raw_item_code",
    "year",
    "value",
    "unit",
    "raw_unit",
    "whep_code",
    "match_method",
    "value_grid",
    "source_grid_verdict"
  )
}

prepare_products <- function(base, lookup) {
  code_lookup <- lookup |>
    dplyr::filter(!is.na(.data$item_code)) |>
    dplyr::distinct(.data$item_code, .keep_all = TRUE)
  alias_lookup <- lookup |>
    dplyr::filter(!is.na(.data$item_alias)) |>
    dplyr::distinct(.data$item_alias, .keep_all = TRUE)

  base |>
    dplyr::filter(.data$unit %in% c("ha", "tonnes")) |>
    dplyr::left_join(code_lookup, by = "item_code", suffix = c("", "_code")) |>
    dplyr::left_join(alias_lookup, by = "item_alias", suffix = c("", "_alias")) |>
    dplyr::mutate(
      item_prod = dplyr::coalesce(.data$item_prod, .data$item_prod_alias),
      item_prod_code = dplyr::coalesce(.data$item_prod_code, .data$item_prod_code_alias),
      item_cbs = dplyr::coalesce(.data$item_cbs, .data$item_cbs_alias),
      item_cbs_code = dplyr::coalesce(.data$item_cbs_code, .data$item_cbs_code_alias),
      group = dplyr::coalesce(.data$group, .data$group_alias),
      live_anim = dplyr::coalesce(.data$live_anim, .data$live_anim_alias),
      live_anim_code = as.character(dplyr::coalesce(.data$live_anim_code, .data$live_anim_code_alias))
    ) |>
    dplyr::filter(
      !is.na(.data$item_prod_code),
      !is.na(.data$item_cbs_code),
      .data$group %in% c("Primary crops", "Crop products", "Livestock products"),
      .data$unit != "ha" | .data$group == "Primary crops"
    ) |>
    dplyr::select(
      dplyr::any_of(base_cols()),
      "item_prod",
      "item_prod_code",
      "item_cbs",
      "item_cbs_code",
      "live_anim",
      "live_anim_code"
    )
}

prepare_stocks <- function(base, lookup) {
  code_lookup <- lookup |>
    dplyr::filter(!is.na(.data$item_code)) |>
    dplyr::distinct(.data$item_code, .keep_all = TRUE)
  alias_lookup <- lookup |>
    dplyr::filter(!is.na(.data$item_alias)) |>
    dplyr::distinct(.data$item_alias, .keep_all = TRUE)

  base |>
    dplyr::filter(.data$unit == "heads") |>
    dplyr::left_join(code_lookup, by = "item_code", suffix = c("", "_code")) |>
    dplyr::left_join(alias_lookup, by = "item_alias", suffix = c("", "_alias")) |>
    dplyr::mutate(
      item_prod = dplyr::coalesce(.data$item_prod, .data$item_prod_alias),
      item_prod_code = dplyr::coalesce(.data$item_prod_code, .data$item_prod_code_alias),
      item_cbs = dplyr::coalesce(.data$item_cbs, .data$item_cbs_alias),
      item_cbs_code = dplyr::coalesce(.data$item_cbs_code, .data$item_cbs_code_alias)
    ) |>
    dplyr::filter(!is.na(.data$item_prod_code), !is.na(.data$item_cbs_code)) |>
    dplyr::mutate(
      live_anim = NA_character_,
      live_anim_code = NA_character_
    ) |>
    dplyr::select(
      dplyr::any_of(base_cols()),
      "item_prod",
      "item_prod_code",
      "item_cbs",
      "item_cbs_code",
      "live_anim",
      "live_anim_code"
    )
}

message("Reading raw historical printed-statistics union: ", layer_b_path)
layer_b <- arrow::read_parquet(layer_b_path) |>
  tibble::as_tibble()
# Layer B's column NAMED `polity_code` holds LOWERCASE ISO CODES ("fra", "deu"), not WHEP
# polity codes: measured 2026-08-17 on the 192,670-row parquet, 166 distinct values, 99.4%
# exactly tolower(iso3c), and 0 of them equal to any polity_code in
# data/final/polities_database.csv. Joining on it returns nothing and errors on nothing
# (issue 95, option 4). It is renamed here for the same reason extdata.py renames it on the
# Python side: the misleading name never exists in a frame this script holds. Nothing below
# reads it -- prepare_products()/prepare_stocks() narrow to base_cols(), which excludes it,
# and the real polity_code arrives later from polity_lookup() -- so this rename changes no
# output value; it removes the chance that a future edit joins on the wrong column.
if ("polity_code" %in% names(layer_b)) {
  layer_b <- dplyr::rename(layer_b, iso3_lower = "polity_code")
}
message("Reading WHEP polity matches: ", matches_path)
matches <- arrow::read_parquet(matches_path) |>
  tibble::as_tibble()

require_cols(
  layer_b,
  c("source", "source_detail", "country", "iso3c", "item", "item_code", "year", "value", "unit"),
  "raw historical table"
)
require_cols(
  matches,
  c("source", "country", "iso3c", "year", "item", "value", "unit", "whep_code"),
  "matched rows"
)

if ("is_aggregate" %in% names(layer_b)) {
  layer_b <- layer_b |>
    dplyr::filter(is.na(.data$is_aggregate) | !.data$is_aggregate)
}
if (nrow(layer_b) != nrow(matches)) {
  stop(
    "Raw non-aggregate rows (", nrow(layer_b),
    ") do not match match rows (", nrow(matches), ")."
  )
}
validate_alignment(layer_b, matches)

# VALUE-SCALE CORRECTIONS (whep-polities issues 416, 424). matched_rows.parquet carries a per-row
# `value_divisor`: 1 except where data/final/source_value_scale_corrections.csv says a source printed
# a block in a different unit (iia tobacco and hops production 1934-1945 at 100x, hops area 1934-1938
# at 10x), or a single cell ten times too small (0.1: eight 1933 iia cells another volume prints
# right). The matcher leaves `value` as printed, so the division happens here. A matches file
# without the column predates the table, and publishing from it would put the 100x cells back, so
# it is refused rather than read as "no corrections".
if (!"value_divisor" %in% names(matches)) {
  stop(
    "matched rows carry no `value_divisor`; re-run ",
    "pipelines/polity-autoimprove/01_match_and_findings.py"
  )
}

# VALUE PRECISION (whep-polities issue 446). matched_rows.parquet carries `value_grid` (the step a
# value cannot be assumed finer than, in the unit layer B printed it), `source_grid_verdict` and the
# two series columns. A matches file without them predates the channel; publishing from it would
# put 47% of the panel's non-zero values back as exact points, so it is refused.
if (!all(c("value_grid", "source_grid_verdict") %in% names(matches))) {
  stop(
    "matched rows carry no `value_grid`/`source_grid_verdict`; re-run ",
    "pipelines/polity-autoimprove/01_match_and_findings.py"
  )
}

base <- dplyr::bind_cols(
  layer_b |>
    dplyr::rename(
      raw_source = "source",
      raw_country = "country",
      raw_item = "item",
      raw_item_code = "item_code",
      raw_unit = "unit"
    ),
  matches |>
    dplyr::select(
      "whep_code", "value_divisor", "value_grid", "source_grid_verdict",
      dplyr::any_of("match_method")
    )
) |>
  dplyr::mutate(
    item_code = normalise_item_code(.data$raw_item_code),
    item_alias = normalise_item_name(.data$raw_item),
    unit_in = stringr::str_squish(tolower(.data$raw_unit)),
    unit_multiplier = unit_multiplier(.data$unit_in),
    year = as.integer(.data$year),
    unit = output_unit(.data$unit_in),
    # A divisor below 1 (issue 424: single cells printed 10x too small) multiplies by its exact
    # inverse; dividing by 0.1 would carry 0.1's binary rounding into the published value.
    value = dplyr::if_else(
      .data$value_divisor < 1,
      as.numeric(.data$value) * .data$unit_multiplier * round(1 / .data$value_divisor),
      as.numeric(.data$value) * .data$unit_multiplier / .data$value_divisor
    ),
    # The grid is a step in the PRINTED unit, so it rescales exactly as the value does: a
    # `1000 tonnes` row on a 0.1 grid is a 100 t step, a /100 value-scale correction divides the
    # step by 100 as well, and a x10 cell correction (divisor 0.1) multiplies it by 10.
    value_grid = dplyr::if_else(
      .data$value_divisor < 1,
      as.numeric(.data$value_grid) * .data$unit_multiplier * round(1 / .data$value_divisor),
      as.numeric(.data$value_grid) * .data$unit_multiplier / .data$value_divisor
    )
  ) |>
  dplyr::filter(
    !is.na(.data$unit),
    !is.na(.data$whep_code),
    !is.na(.data$value),
    # PERIOD AVERAGES ARE EXCLUDED HERE, and this is the largest single exclusion
    # the build makes: 9,865 valued layer-B rows (5.12%) carry a period label
    # like `1934-1938` instead of a year -- iia 6,163, fao1952 3,702, across
    # 3,589 (label, item) series, 100 items and 401 labels. Every one of them has
    # a period, so none is genuinely undated; they are the printed sources'
    # five-year-mean convention.
    #
    # A period average is not an observation of a year, so placing it on one
    # would invent a datum. But the exclusion used to be INVISIBLE -- just this
    # predicate -- and a coverage measurement then reads the gap as missing
    # sources (whep-polities #310). `period` is not even carried into this
    # pipeline, so there is no path by which the label could supply a year, and
    # `.prepare_historical_production()` would drop them again anyway via
    # `year %in% years` (NA %in% years is FALSE in R).
    !is.na(.data$year)
  )

products <- prepare_products(base, product_lookup())
stocks <- prepare_stocks(base, stock_lookup())

candidates <- dplyr::bind_rows(products, stocks) |>
  dplyr::left_join(polity_lookup(), by = "whep_code") |>
  dplyr::filter(
    !is.na(.data$item_prod_code),
    !is.na(.data$item_cbs_code),
    !is.na(.data$area_code),
    !is.nan(.data$value)
  ) |>
  dplyr::mutate(
    source = paste0("historical_", .data$raw_source),
    item_prod_code = as.numeric(.data$item_prod_code),
    item_cbs_code = as.numeric(.data$item_cbs_code),
    live_anim_code = as.numeric(.data$live_anim_code)
  )

# ONE ROW PER CONSUMER KEY (whep-polities issues 451, 367). This used to be
# `summarise(value = mean(value))` over a key that kept the raw label, item and source apart, so
# several rows reached WHEP for one (year, area, item, unit) and WHEP averaged them: 1,706 keys of
# the published table carried candidates that disagree, and their published value equalled none of
# them. R/resolve_collapse_groups.R now picks one candidate per key by stated rules -- dedupe
# identical rows, keep a total over its own parts, drop a source whose rows cannot be told apart,
# then source precedence -- and writes every non-trivial decision to the tracked
# state/collapse_resolutions.csv, which scripts/validate_published_collapse.py re-derives in CI.
resolved <- resolve_collapse_groups(candidates)

harmonized <- resolved$published |>
  dplyr::select(
    "year",
    "area_code",
    "polity_area_code",
    "polity_code",
    "reporting_polity_code",
    "reporting_polity_name",
    "reporting_polity_has_geometry",
    "item_prod_code",
    "item_prod",
    "item_cbs_code",
    "item_cbs",
    "live_anim_code",
    "unit",
    "source",
    "raw_source",
    "raw_country",
    "raw_item",
    "raw_item_code",
    "raw_unit",
    "source_detail",
    "match_method",
    "value",
    "value_grid",
    "source_grid_verdict"
  ) |>
  dplyr::arrange(
    .data$year,
    .data$reporting_polity_code,
    .data$item_prod_code,
    .data$unit,
    .data$source
  ) |>
  dplyr::rename(
    item_prod_name = "item_prod",
    item_cbs_name = "item_cbs"
  )

dup_keys <- harmonized |>
  dplyr::count(dplyr::across(dplyr::all_of(COLLAPSE_KEY))) |>
  dplyr::filter(.data$n > 1L)
if (nrow(dup_keys) > 0L) {
  stop(nrow(dup_keys), " published keys still carry more than one row; the consumer would blend them")
}

# Tracked, so the CI gate can re-derive each decision without the (non-redistributable) panel.
# Written only for the default inputs: a run over a test panel must not overwrite the record.
resolutions_path <- file.path(script_dir, "state", "collapse_resolutions.csv")
if (write_tracked_state) {
  dir.create(dirname(resolutions_path), showWarnings = FALSE)
  tmp <- paste0(resolutions_path, ".tmp")
  readr::write_csv(resolved$resolutions, tmp, na = "")
  file.rename(tmp, resolutions_path)
  message("Wrote: ", resolutions_path)
}
message(
  "Collapse resolution: ", nrow(candidates), " candidate rows -> ", nrow(harmonized),
  " published keys; ",
  paste(names(table(resolved$resolutions$resolution)), table(resolved$resolutions$resolution),
    sep = " ", collapse = ", "
  )
)

out_parquet <- file.path(out_dir, "historical_production_harmonized.parquet")
out_csv <- file.path(out_dir, "historical_production_harmonized.csv")
out_summary <- file.path(out_dir, "historical_production_harmonized_summary.csv")

arrow::write_parquet(harmonized, out_parquet)
readr::write_csv(harmonized, out_csv)

summary <- harmonized |>
  dplyr::summarise(
    rows = dplyr::n(),
    year_min = min(.data$year, na.rm = TRUE),
    year_max = max(.data$year, na.rm = TRUE),
    polities = dplyr::n_distinct(.data$reporting_polity_code),
    .by = c("source", "unit")
  ) |>
  dplyr::arrange(.data$source, .data$unit)
readr::write_csv(summary, out_summary)

message("Wrote: ", out_parquet)
message("Wrote: ", out_csv)
message("Wrote: ", out_summary)
print(summary, n = Inf)
