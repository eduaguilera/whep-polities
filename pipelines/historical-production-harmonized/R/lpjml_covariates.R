lpjml_grid_cell_area_ha <- function(lat, lon_res, lat_res) {
  radius_m <- 6371008.8
  dlon <- lon_res * pi / 180
  lat1 <- (lat - lat_res / 2) * pi / 180
  lat2 <- (lat + lat_res / 2) * pi / 180
  abs(radius_m^2 * dlon * (sin(lat2) - sin(lat1))) / 10000
}

lpjml_nearest_grid_index <- function(x, min_value, max_value, resolution) {
  value <- pmin(max_value, pmax(min_value, x))
  as.integer(round((value - min_value) / resolution))
}

make_lpjml_surface_covariate <- function(surface, value_col, label = value_col) {
  stopifnot(all(c("lon", "lat", "year", value_col) %in% names(surface)))

  surface <- as.data.frame(surface)
  surface <- surface[!is.na(surface[[value_col]]) & surface[[value_col]] > 0, ]
  if (nrow(surface) == 0) {
    stop("No positive rows available for LPJmL covariate: ", label)
  }

  lon_vals <- sort(unique(surface$lon))
  lat_vals <- sort(unique(surface$lat))
  lon_res <- min(diff(lon_vals))
  lat_res <- min(diff(lat_vals))
  lon_min <- min(lon_vals)
  lat_min <- min(lat_vals)
  lon_max <- max(lon_vals)
  lat_max <- max(lat_vals)
  available_years <- sort(unique(surface$year))

  surface$lon_i <- lpjml_nearest_grid_index(
    surface$lon, lon_min, lon_max, lon_res
  )
  surface$lat_i <- lpjml_nearest_grid_index(
    surface$lat, lat_min, lat_max, lat_res
  )
  surface$density <- pmax(
    surface[[value_col]] /
      lpjml_grid_cell_area_ha(surface$lat, lon_res, lat_res),
    0
  )

  dt <- data.table::as.data.table(surface[, c(
    "year", "lon_i", "lat_i", "density"
  )])
  dt <- dt[, .(density = sum(density, na.rm = TRUE)), by = .(year, lon_i, lat_i)]
  data.table::setkey(dt, year, lon_i, lat_i)

  fn <- function(centroids_sf, year) {
    coords <- sf::st_coordinates(sf::st_transform(centroids_sf, 4326))
    nearest_year <- available_years[which.min(abs(available_years - year))]
    query <- data.table::data.table(
      year = as.integer(nearest_year),
      lon_i = lpjml_nearest_grid_index(coords[, "X"], lon_min, lon_max, lon_res),
      lat_i = lpjml_nearest_grid_index(coords[, "Y"], lat_min, lat_max, lat_res)
    )
    values <- dt[query, on = .(year, lon_i, lat_i)]$density
    values[is.na(values)] <- 0
    values
  }
  attr(fn, "label") <- label
  fn
}

make_lpjml_total_cropland_covariate <- function(input_dir, years) {
  years <- as.integer(years)
  cropland <- arrow::open_dataset(
    file.path(input_dir, "gridded_cropland.parquet")
  ) |>
    dplyr::filter(year %in% years) |>
    dplyr::select("lon", "lat", "year", "cropland_ha") |>
    dplyr::collect()

  make_lpjml_surface_covariate(
    cropland,
    value_col = "cropland_ha",
    label = "lpjml_total_cropland"
  )
}

make_lpjml_crop_pattern_covariate <- function(
  input_dir,
  years,
  item_prod_code,
  cft_mapping = whep::cft_mapping
) {
  years <- as.integer(years)
  item_prod_code <- as.integer(item_prod_code)

  item_map <- cft_mapping[cft_mapping$item_prod_code == item_prod_code, ]
  if (nrow(item_map) != 1) {
    stop(
      "Expected exactly one cft_mapping row for item_prod_code ",
      item_prod_code,
      "; found ",
      nrow(item_map),
      "."
    )
  }
  luh2_type <- item_map$luh2_type[[1]]

  type_cropland <- arrow::open_dataset(
    file.path(input_dir, "type_cropland.parquet")
  ) |>
    dplyr::filter(year %in% years, luh2_type == !!luh2_type) |>
    dplyr::select("lon", "lat", "year", "type_ha") |>
    dplyr::collect()

  crop_pattern <- arrow::open_dataset(
    file.path(input_dir, "crop_patterns.parquet")
  ) |>
    dplyr::filter(item_prod_code == !!item_prod_code) |>
    dplyr::select("lon", "lat", "harvest_fraction") |>
    dplyr::collect()

  if (nrow(crop_pattern) == 0) {
    stop("No crop pattern rows found for item_prod_code ", item_prod_code, ".")
  }

  dt <- data.table::as.data.table(type_cropland)
  pattern <- data.table::as.data.table(crop_pattern)
  dt[pattern, harvest_fraction := i.harvest_fraction, on = .(lon, lat)]
  dt[is.na(harvest_fraction), harvest_fraction := 0]
  dt[, crop_pattern_ha := type_ha * harvest_fraction]

  make_lpjml_surface_covariate(
    dt[, .(lon, lat, year, crop_pattern_ha)],
    value_col = "crop_pattern_ha",
    label = paste0(
      "lpjml_",
      item_map$item_prod_name[[1]],
      "_",
      luh2_type,
      "_crop_pattern"
    )
  )
}
