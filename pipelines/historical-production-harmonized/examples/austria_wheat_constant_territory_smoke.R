#!/usr/bin/env Rscript

# Smoke run: compare old WHEP pre-1961 production backcast with a
# constant-territory estimate from harmonized historical source rows.
#
# Example:
#   present-day Austria wheat tonnes, selected years.
#
# Old series:
#   WHEP build_primary_production() for area_code 11.  Pre-1961 rows are
#   LUH2-based backcasts labelled to the 1961/current-ish reporting territory.
#
# Adapted series:
#   Start from harmonized historical rows reported under each source year's
#   historical Austria polity, then reallocate to the present-day Austria
#   boundary with build_constant_territory_series().
#
# This is a smoke run, not a final estimate. It compares:
# - plain area weighting
# - total cropland weighting from the prepared WHEP/LPJmL inputs
# - wheat-specific weighting from LUH2 c3ann cropland times WHEP crop patterns

if (!requireNamespace("whep", quietly = TRUE)) {
  if (requireNamespace("pkgload", quietly = TRUE)) {
    pkgload::load_all("/home/usuario/WHEP-polities-reconcile", quiet = TRUE)
  } else {
    stop("Package `whep` is not available and `pkgload` is not installed.")
  }
}

harmonized_path <- "/home/usuario/Nextcloud/whep/historical_production_harmonized/historical_production_harmonized.parquet"
lpjml_input_dir <- "/home/usuario/WHEP/LPJmL_inputs/whep/inputs"
out_dir <- "/home/usuario/Nextcloud/whep/historical_production_harmonized/smoke_runs"
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

out_csv <- file.path(out_dir, "austria_wheat_constant_territory_smoke.csv")

years_keep <- c(1851L, 1860L, 1880L, 1900L, 1910L, 1920L, 1950L, 1960L)

source("pipelines/historical-production-harmonized/R/lpjml_covariates.R")

historical <- arrow::read_parquet(harmonized_path) |>
  dplyr::filter(
    .data$item_prod_code == 15,
    .data$unit == "tonnes",
    grepl("^AUT-", .data$polity_code),
    .data$year %in% years_keep
  ) |>
  dplyr::transmute(
    year = as.integer(.data$year),
    polity_code = .data$polity_code,
    value = .data$value
  )

polities <- whep::get_polity_geometries()
# Current get_polity_geometries() can return an sf data frame whose geometry
# column lost the sfc class in this environment. Re-wrap it for sf operations.
polities$geom <- sf::st_sfc(polities$geom, crs = 4326)
polities <- sf::st_as_sf(polities, sf_column_name = "geom", crs = 4326)
polities <- polities[grepl("^AUT-", polities$polity_code), ]

build_adapted <- function(covariate, prefix) {
  whep::build_constant_territory_series(
    historical,
    ref_year = 2020,
    polities = polities,
    covariate = covariate,
    resolution = 100000,
    donor = "regional",
    max_cells = 2e5,
    verbose = FALSE
  ) |>
    dplyr::filter(.data$target_polity_code == "AUT-1919-2025") |>
    dplyr::transmute(
      year = .data$year,
      "{prefix}_present_border_tonnes" := .data$value,
      "{prefix}_imputed_share" := .data$imputed_share,
      "{prefix}_n_sources" := .data$n_sources
    )
}

adapted_uniform <- build_adapted(NULL, "adapted_uniform")
adapted_total_cropland <- build_adapted(
  make_lpjml_total_cropland_covariate(lpjml_input_dir, years_keep),
  "adapted_total_cropland"
)
adapted_wheat_pattern <- build_adapted(
  make_lpjml_crop_pattern_covariate(
    lpjml_input_dir,
    years_keep,
    item_prod_code = 15
  ),
  "adapted_wheat_pattern"
)

old <- whep::build_primary_production(
  start_year = min(years_keep),
  end_year = max(years_keep)
) |>
  dplyr::filter(
    .data$year %in% years_keep,
    .data$area_code == 11,
    .data$item_prod_code == 15,
    .data$unit == "tonnes"
  ) |>
  dplyr::transmute(
    year = as.integer(.data$year),
    old_1961_border_tonnes = .data$value,
    old_source = .data$source,
    old_reporting_polity_code = .data$reporting_polity_code
  )

comparison <- old |>
  dplyr::full_join(adapted_uniform, by = "year") |>
  dplyr::full_join(adapted_total_cropland, by = "year") |>
  dplyr::full_join(adapted_wheat_pattern, by = "year") |>
  dplyr::mutate(
    ratio_uniform_to_old =
      .data$adapted_uniform_present_border_tonnes / .data$old_1961_border_tonnes,
    ratio_total_cropland_to_old =
      .data$adapted_total_cropland_present_border_tonnes / .data$old_1961_border_tonnes,
    ratio_wheat_pattern_to_old =
      .data$adapted_wheat_pattern_present_border_tonnes / .data$old_1961_border_tonnes,
    diff_uniform_minus_old =
      .data$adapted_uniform_present_border_tonnes - .data$old_1961_border_tonnes,
    diff_total_cropland_minus_old =
      .data$adapted_total_cropland_present_border_tonnes - .data$old_1961_border_tonnes,
    diff_wheat_pattern_minus_old =
      .data$adapted_wheat_pattern_present_border_tonnes - .data$old_1961_border_tonnes
  ) |>
  dplyr::arrange(.data$year)

readr::write_csv(comparison, out_csv)
print(comparison, n = Inf)
message("Wrote: ", out_csv)
