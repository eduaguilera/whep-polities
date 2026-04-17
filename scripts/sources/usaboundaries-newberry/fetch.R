#!/usr/bin/env Rscript
# Fetch US historical state boundaries from the USAboundaries R package.
# Data: Newberry Library Atlas of Historical County Boundaries.
#
# We snapshot one polygon per WHEP polity (state, start-year). The script
# reads the list of needed (state, start_year) pairs from the wiki frontmatter
# of pages whose polygon_source == 'usaboundaries-newberry', and writes one
# GPKG keyed by (state_abbr, start_year) matching sources.yaml's id_column /
# temporal config.

suppressPackageStartupMessages({
  library(sf)
  library(USAboundaries)
  library(jsonlite)
})

proj_root <- normalizePath(file.path(dirname(sys.frame(1)$ofile), "../../.."))
out_dir   <- file.path(proj_root, "data/geodata/usaboundaries-newberry")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

wiki_dir <- file.path(proj_root, "wiki/polities")
pages    <- list.files(wiki_dir, pattern = "\\.md$", full.names = TRUE)

# Very small frontmatter parser: grab polygon_source and polygon_feature_* fields.
parse_fm <- function(path) {
  lines <- readLines(path, warn = FALSE)
  if (length(lines) < 2 || lines[1] != "---") return(NULL)
  end <- which(lines[-1] == "---")[1]
  if (is.na(end)) return(NULL)
  block <- lines[2:end]
  fm <- list()
  for (l in block) {
    m <- regmatches(l, regexec("^([a-z_]+): *(.*)$", l))[[1]]
    if (length(m) == 3) fm[[m[2]]] <- trimws(gsub('"', '', m[3]))
  }
  fm
}

needed <- list()
for (p in pages) {
  fm <- parse_fm(p)
  if (is.null(fm)) next
  if (isTRUE(fm$polygon_source == "usaboundaries-newberry")) {
    needed[[length(needed) + 1]] <- list(
      state = fm$polygon_feature_id,
      year  = as.integer(fm$polygon_feature_year %||% fm$start_year)
    )
  }
}

if (length(needed) == 0) {
  message("No wiki pages cite usaboundaries-newberry. Nothing to fetch.")
  quit(save = "no", status = 0)
}

# For each (state, year) snapshot, fetch the state boundary on Jan 1 of that year.
features <- list()
for (n in needed) {
  d <- sprintf("%d-01-01", n$year)
  sf0 <- tryCatch(
    us_states(map_date = d, resolution = "low"),
    error = function(e) NULL
  )
  if (is.null(sf0)) next
  hit <- sf0[toupper(sf0$state_abbr) == toupper(n$state), ]
  if (nrow(hit) == 0) next
  hit$start_year <- n$year
  hit$end_year   <- n$year
  features[[length(features) + 1]] <- hit[, c("state_abbr", "start_year", "end_year", "geometry")]
}

if (length(features) == 0) {
  stop("No USAboundaries matches resolved from wiki frontmatter.")
}

out <- do.call(rbind, features)
st_write(out, file.path(out_dir, "states.gpkg"), delete_dsn = TRUE, quiet = TRUE)
message("Wrote: ", file.path(out_dir, "states.gpkg"), " (", nrow(out), " features)")
