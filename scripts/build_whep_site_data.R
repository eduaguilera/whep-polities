#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = TRUE)

`%||%` <- function(x, y) {
  if (is.null(x) || length(x) == 0L) y else x
}

arg_value <- function(name, default = NULL) {
  prefix <- paste0("--", name, "=")
  hit <- grep(paste0("^", prefix), args, value = TRUE)
  if (length(hit)) {
    return(sub(prefix, "", hit[[1]], fixed = TRUE))
  }
  flag <- paste0("--", name)
  idx <- match(flag, args)
  if (!is.na(idx) && idx < length(args)) {
    return(args[[idx + 1L]])
  }
  env <- Sys.getenv(toupper(gsub("-", "_", name)), unset = NA_character_)
  if (!is.na(env) && nzchar(env)) {
    return(env)
  }
  default
}

default_whep_repo <- function() {
  candidates <- c(
    path.expand("~/refactor/polities-database"),
    path.expand("~/WHEP")
  )
  hit <- candidates[dir.exists(candidates)]
  if (!length(hit)) {
    stop("Could not find WHEP checkout. Pass --whep-repo=/path/to/WHEP.")
  }
  hit[[1]]
}

script_file <- grep("^--file=", commandArgs(FALSE), value = TRUE)
script_file <- if (length(script_file)) {
  sub("^--file=", "", script_file[[1]])
} else {
  "scripts/build_whep_site_data.R"
}
script_path <- normalizePath(script_file, mustWork = FALSE)
repo_root <- normalizePath(file.path(dirname(script_path), ".."), mustWork = TRUE)

slugify <- function(x) {
  x <- iconv(x, to = "ASCII//TRANSLIT")
  x <- tolower(x)
  x <- gsub("[^a-z0-9]+", "-", x)
  x <- gsub("(^-|-$)", "", x)
  ifelse(nzchar(x), x, "unknown")
}

as_int <- function(x, default) {
  out <- suppressWarnings(as.integer(x))
  ifelse(is.na(out), default, out)
}

repo_path <- function(path) {
  path <- path.expand(path)
  if (!grepl("^/", path)) {
    path <- file.path(repo_root, path)
  }
  normalizePath(path, mustWork = FALSE)
}

message_step <- function(...) {
  message("\n-- ", paste0(..., collapse = ""), " --")
}

whep_repo <- normalizePath(arg_value("whep-repo", default_whep_repo()), mustWork = TRUE)
out_dir <- repo_path(arg_value("out-dir", file.path(repo_root, "site", "whep")))
start_year <- as_int(arg_value("start-year", "1850"), 1850L)
end_year <- as_int(arg_value("end-year", "2023"), 2023L)
top_n <- as_int(arg_value("top-n", "10"), 10L)
datasets_arg <- strsplit(arg_value("datasets", "primary,cbs"), ",", fixed = TRUE)[[1]]
datasets_arg <- trimws(datasets_arg)

primary_units_arg <- arg_value("primary-units", "")
primary_units <- if (nzchar(primary_units_arg)) {
  trimws(strsplit(primary_units_arg, ",", fixed = TRUE)[[1]])
} else {
  NULL
}

cbs_elements_arg <- arg_value("cbs-elements", "")
cbs_elements <- if (nzchar(cbs_elements_arg)) {
  trimws(strsplit(cbs_elements_arg, ",", fixed = TRUE)[[1]])
} else {
  c(
    "domestic_supply",
    "production",
    "import",
    "export",
    "stock_variation",
    "food",
    "feed",
    "seed",
    "other_uses",
    "processing"
  )
}

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
primary_site_cache <- NULL
site_geometry_codes <- NULL

message_step("Loading WHEP from ", whep_repo)
if (file.exists(file.path(whep_repo, "renv", "activate.R"))) {
  source(file.path(whep_repo, "renv", "activate.R"))
  if (requireNamespace("renv", quietly = TRUE)) {
    renv::load(whep_repo, quiet = TRUE)
  }
}
setwd(whep_repo)
pkgload::load_all(whep_repo, quiet = TRUE)

suppressPackageStartupMessages({
  library(data.table)
  library(jsonlite)
})

round_values <- function(x) {
  signif(as.numeric(x), 8)
}

write_dataset_catalog <- function(site_root) {
  catalog_dir <- file.path(site_root, "data")
  dir.create(catalog_dir, recursive = TRUE, showWarnings = FALSE)
  catalog <- list(
    datasets = list(
      list(
        id = "pre1961",
        label = "Pre-1961 production test data",
        description = "Historical production test dataset already bundled with the site.",
        index = "pre1961/by_item_index.json",
        itemPath = "pre1961/by_item/{slug}.json",
        metricLabel = "Measure"
      ),
      list(
        id = "whep-primary",
        label = "WHEP primary production",
        description = "Top WHEP primary-production items by unit; positive values only.",
        index = "whep/primary/index.json",
        itemPath = "whep/primary/by_metric/{metric}/{slug}.json",
        metricLabel = "Unit"
      ),
      list(
        id = "whep-cbs",
        label = "WHEP commodity balance sheets",
        description = "Top WHEP CBS items by element; positive values only.",
        index = "whep/cbs/index.json",
        itemPath = "whep/cbs/by_metric/{metric}/{slug}.json",
        metricLabel = "Element"
      )
    )
  )
  write_json(
    catalog,
    file.path(catalog_dir, "catalog.json"),
    auto_unbox = TRUE,
    pretty = FALSE
  )
}

unit_for_cbs_item <- function(item_type) {
  ifelse(grepl("^livestock", item_type %||% ""), "heads", "tonnes")
}

current_site_geometry_codes <- function() {
  if (!is.null(site_geometry_codes)) {
    return(site_geometry_codes)
  }
  geojson_path <- file.path(repo_root, "site", "polities.geojson")
  if (!file.exists(geojson_path)) {
    site_geometry_codes <<- character()
    return(site_geometry_codes)
  }
  geo <- jsonlite::fromJSON(geojson_path, simplifyVector = FALSE)
  site_geometry_codes <<- vapply(
    geo$features,
    function(feature) feature$properties$polity_code %||% NA_character_,
    character(1)
  )
  site_geometry_codes <<- unique(site_geometry_codes[!is.na(site_geometry_codes)])
  site_geometry_codes
}

compact_by_year <- function(dt) {
  setorder(dt, year, polity_code)
  split(dt, by = "year", keep.by = FALSE) |>
    lapply(function(x) {
      vals <- as.list(round_values(x$value))
      names(vals) <- x$polity_code
      vals
    })
}

panel_rows_by_year <- function(dt, key_cols) {
  if (!nrow(dt)) {
    return(list())
  }
  setorder(dt, year, -value)
  split(dt, by = "year", keep.by = FALSE) |>
    lapply(function(x) {
      x <- head(x, 30L)
      rows <- lapply(seq_len(nrow(x)), function(i) {
        as.list(x[i, ..key_cols])
      })
      unname(rows)
    })
}

map_selected_values <- function(dt) {
  if (!nrow(dt)) {
    return(dt)
  }
  mapped <- whep::add_polity_code(
    tibble::as_tibble(dt),
    code_column = "area_code",
    year_column = "year"
  )
  mapped <- as.data.table(mapped)
  geometry_codes <- current_site_geometry_codes()
  if (length(geometry_codes)) {
    mapped[, has_geometry := polity_code %in% geometry_codes]
  }
  mapped
}

write_metric_item <- function(dt, out_file, meta) {
  dir.create(dirname(out_file), recursive = TRUE, showWarnings = FALSE)

  mapped <- map_selected_values(dt)
  mapped[, value := as.numeric(value)]
  if (!"area_name" %in% names(mapped)) {
    mapped[, area_name := NA_character_]
  }
  if (!"area_iso3c" %in% names(mapped)) {
    mapped[, area_iso3c := NA_character_]
  }
  mapped[
    ,
    area_label := fifelse(
      !is.na(area_name) & nzchar(area_name),
      area_name,
      paste0("Area ", area_code)
    )
  ]
  mapped[
    ,
    area_code_label := fifelse(
      !is.na(area_iso3c) & nzchar(area_iso3c),
      area_iso3c,
      as.character(area_code)
    )
  ]

  visible <- mapped[
    !is.na(polity_code) & has_geometry %in% TRUE & value > 0,
    .(value = sum(value, na.rm = TRUE)),
    by = .(year, polity_code)
  ]

  no_polygon <- mapped[
    !is.na(polity_code) & !(has_geometry %in% TRUE) & value > 0,
    .(
      value = sum(value, na.rm = TRUE),
      country = area_label[which.max(value)]
    ),
    by = .(year, polity_code)
  ][
    ,
    .(
      year,
      country,
      polity_code,
      value = round_values(value)
    )
  ]

  unmatched <- mapped[
    is.na(polity_code) & value > 0,
    .(
      value = sum(value, na.rm = TRUE),
      name = area_label[which.max(value)],
      iso3c = area_code_label[which.max(value)]
    ),
    by = .(year, area_code)
  ][
    ,
    .(
      year,
      area_code,
      name,
      iso3c,
      value = round_values(value)
    )
  ]

  payload <- c(
    meta,
    list(
      polity_count = uniqueN(visible$polity_code),
      rows = nrow(visible),
      by_year = compact_by_year(visible),
      unmatched_by_year = panel_rows_by_year(
        unmatched,
        c("area_code", "name", "iso3c", "value")
      ),
      no_polygon_by_year = panel_rows_by_year(
        no_polygon,
        c("country", "polity_code", "value")
      )
    )
  )

  write_json(
    payload,
    out_file,
    auto_unbox = TRUE,
    pretty = FALSE,
    digits = 8,
    null = "null"
  )
}

top_keys <- function(dt, by_cols, value_col = "value", top_n = 10L) {
  totals <- dt[
    get(value_col) > 0,
    .(total = sum(get(value_col), na.rm = TRUE), rows = .N),
    by = by_cols
  ]
  setorderv(totals, c(by_cols[1], "total"), c(1L, -1L))
  if (top_n > 0L) {
    totals <- totals[, head(.SD, top_n), by = c(by_cols[1])]
  }
  totals[]
}

get_primary_for_site <- function() {
  if (is.null(primary_site_cache)) {
    message_step("Building WHEP primary production ", start_year, "-", end_year)
    primary_site_cache <<- as.data.table(whep::build_primary_production(
      start_year = start_year,
      end_year = end_year
    ))
  }
  copy(primary_site_cache)
}

build_primary_site_data <- function() {
  primary <- get_primary_for_site()
  primary <- primary[!is.na(value) & value > 0]
  primary[, item_prod_code := as.numeric(item_prod_code)]
  primary[, item_cbs_code := as.numeric(item_cbs_code)]

  items_prod <- as.data.table(whep::items_prod)
  items_prod[, item_prod_code := as.numeric(item_prod_code)]
  items_prod_full <- unique(
    as.data.table(whep::items_prod_full)[
      ,
      .(
        item_prod_code = as.numeric(item_prod_code),
        item_prod
      )
    ],
    by = "item_prod_code"
  )
  items_cbs <- as.data.table(whep::items_cbs)
  items_cbs[, item_cbs_code := as.numeric(item_cbs_code)]

  primary <- merge(primary, items_prod, by = "item_prod_code", all.x = TRUE)
  primary <- merge(primary, items_prod_full, by = "item_prod_code", all.x = TRUE)
  primary <- merge(primary, items_cbs, by = "item_cbs_code", all.x = TRUE)
  primary[, item_label := fifelse(
    !is.na(item_prod_name),
    item_prod_name,
    fifelse(
      !is.na(item_prod),
      item_prod,
      fifelse(!is.na(item_cbs_name), item_cbs_name, paste0("Item ", item_prod_code))
    )
  )]

  if (!is.null(primary_units)) {
    primary <- primary[unit %in% primary_units]
  }

  keys <- top_keys(
    primary,
    c("unit", "item_prod_code", "item_label"),
    top_n = top_n
  )
  setorder(keys, unit, -total)

  index <- list(
    dataset = "whep-primary",
    label = "WHEP primary production",
    description = sprintf(
      "Top %s positive-value primary-production items per unit, %s-%s.",
      ifelse(top_n > 0L, top_n, "all"),
      start_year,
      end_year
    ),
    generated_at = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
    start_year = start_year,
    end_year = end_year,
    top_n = top_n,
    rows_available = nrow(primary),
    metrics = list()
  )

  metric_ids <- unique(keys$unit)
  for (metric in metric_ids) {
    metric_slug <- slugify(metric)
    metric_keys <- keys[unit == metric]
    metric_items <- vector("list", nrow(metric_keys))
    for (i in seq_len(nrow(metric_keys))) {
      key <- metric_keys[i]
      item_slug <- paste0(slugify(key$item_label), "-", as.integer(key$item_prod_code))
      rel_path <- file.path("whep", "primary", "by_metric", metric_slug, paste0(item_slug, ".json"))
      out_file <- file.path(dirname(out_dir), rel_path)
      item_dt <- primary[
        unit == key$unit &
          item_prod_code == key$item_prod_code,
        .(year, area_code, value)
      ]
      meta <- list(
        dataset = "whep-primary",
        dataset_label = "WHEP primary production",
        item = key$item_label,
        item_code = as.integer(key$item_prod_code),
        metric = metric,
        metric_label = metric,
        unit = metric,
        year_min = min(item_dt$year, na.rm = TRUE),
        year_max = max(item_dt$year, na.rm = TRUE),
        positive_values_only = TRUE
      )
      write_metric_item(item_dt, out_file, meta)
      metric_items[[i]] <- list(
        slug = item_slug,
        item = key$item_label,
        item_code = as.integer(key$item_prod_code),
        unit = metric,
        year_min = min(item_dt$year, na.rm = TRUE),
        year_max = max(item_dt$year, na.rm = TRUE),
        rows = nrow(item_dt),
        path = rel_path,
        total = round_values(key$total)
      )
      message("  primary/", metric_slug, "/", item_slug)
    }
    index$metrics[[length(index$metrics) + 1L]] <- list(
      id = metric_slug,
      label = metric,
      unit = metric,
      items = metric_items
    )
  }

  dir.create(file.path(out_dir, "primary"), recursive = TRUE, showWarnings = FALSE)
  write_json(
    index,
    file.path(out_dir, "primary", "index.json"),
    auto_unbox = TRUE,
    pretty = FALSE,
    digits = 8
  )
}

build_cbs_site_data <- function() {
  message_step("Building WHEP CBS ", start_year, "-", end_year)
  primary <- get_primary_for_site()
  cbs <- as.data.table(whep::build_commodity_balances(
    primary,
    start_year = start_year,
    end_year = end_year
  ))
  cbs <- cbs[!is.na(value) & value > 0 & element %in% cbs_elements]
  cbs[, item_cbs_code := as.numeric(item_cbs_code)]
  items <- as.data.table(whep::items_cbs)
  items[, item_cbs_code := as.numeric(item_cbs_code)]
  cbs <- merge(cbs, items, by = "item_cbs_code", all.x = TRUE)
  cbs[is.na(item_cbs_name), item_cbs_name := paste0("Item ", item_cbs_code)]
  cbs[, unit := unit_for_cbs_item(item_type)]

  keys <- top_keys(
    cbs,
    c("element", "item_cbs_code", "item_cbs_name", "unit"),
    top_n = top_n
  )
  setorder(keys, element, -total)

  index <- list(
    dataset = "whep-cbs",
    label = "WHEP commodity balance sheets",
    description = sprintf(
      "Top %s positive-value CBS items per element, %s-%s.",
      ifelse(top_n > 0L, top_n, "all"),
      start_year,
      end_year
    ),
    generated_at = format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC"),
    start_year = start_year,
    end_year = end_year,
    top_n = top_n,
    rows_available = nrow(cbs),
    metrics = list()
  )

  metric_ids <- unique(keys$element)
  for (metric in metric_ids) {
    metric_slug <- slugify(metric)
    metric_keys <- keys[element == metric]
    metric_items <- vector("list", nrow(metric_keys))
    for (i in seq_len(nrow(metric_keys))) {
      key <- metric_keys[i]
      item_slug <- paste0(slugify(key$item_cbs_name), "-", as.integer(key$item_cbs_code))
      rel_path <- file.path("whep", "cbs", "by_metric", metric_slug, paste0(item_slug, ".json"))
      out_file <- file.path(dirname(out_dir), rel_path)
      item_dt <- cbs[
        element == key$element &
          item_cbs_code == key$item_cbs_code,
        .(year, area_code, value)
      ]
      meta <- list(
        dataset = "whep-cbs",
        dataset_label = "WHEP commodity balance sheets",
        item = key$item_cbs_name,
        item_code = as.integer(key$item_cbs_code),
        metric = metric,
        metric_label = gsub("_", " ", metric),
        unit = key$unit,
        year_min = min(item_dt$year, na.rm = TRUE),
        year_max = max(item_dt$year, na.rm = TRUE),
        positive_values_only = TRUE
      )
      write_metric_item(item_dt, out_file, meta)
      metric_items[[i]] <- list(
        slug = item_slug,
        item = key$item_cbs_name,
        item_code = as.integer(key$item_cbs_code),
        unit = key$unit,
        year_min = min(item_dt$year, na.rm = TRUE),
        year_max = max(item_dt$year, na.rm = TRUE),
        rows = nrow(item_dt),
        path = rel_path,
        total = round_values(key$total)
      )
      message("  cbs/", metric_slug, "/", item_slug)
    }
    index$metrics[[length(index$metrics) + 1L]] <- list(
      id = metric_slug,
      label = gsub("_", " ", metric),
      element = metric,
      items = metric_items
    )
  }

  dir.create(file.path(out_dir, "cbs"), recursive = TRUE, showWarnings = FALSE)
  write_json(
    index,
    file.path(out_dir, "cbs", "index.json"),
    auto_unbox = TRUE,
    pretty = FALSE,
    digits = 8
  )
}

write_dataset_catalog(file.path(repo_root, "site"))

if ("primary" %in% datasets_arg || "all" %in% datasets_arg) {
  build_primary_site_data()
}
if ("cbs" %in% datasets_arg || "all" %in% datasets_arg) {
  build_cbs_site_data()
}

message("\nWrote WHEP site data to: ", out_dir)
