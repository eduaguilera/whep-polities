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
    "match_method"
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
    dplyr::select("whep_code", dplyr::any_of("match_method"))
) |>
  dplyr::mutate(
    item_code = normalise_item_code(.data$raw_item_code),
    item_alias = normalise_item_name(.data$raw_item),
    unit_in = stringr::str_squish(tolower(.data$raw_unit)),
    unit_multiplier = unit_multiplier(.data$unit_in),
    year = as.integer(.data$year),
    unit = output_unit(.data$unit_in),
    value = as.numeric(.data$value) * .data$unit_multiplier
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

harmonized <- dplyr::bind_rows(products, stocks) |>
  dplyr::left_join(polity_lookup(), by = "whep_code") |>
  dplyr::filter(
    !is.na(.data$item_prod_code),
    !is.na(.data$item_cbs_code),
    !is.na(.data$area_code)
  ) |>
  dplyr::mutate(
    source = paste0("historical_", .data$raw_source),
    item_prod_code = as.numeric(.data$item_prod_code),
    item_cbs_code = as.numeric(.data$item_cbs_code),
    live_anim_code = as.numeric(.data$live_anim_code)
  ) |>
  dplyr::summarise(
    value = mean(.data$value, na.rm = TRUE),
    .by = c(
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
      "match_method"
    )
  ) |>
  dplyr::filter(!is.nan(.data$value)) |>
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
