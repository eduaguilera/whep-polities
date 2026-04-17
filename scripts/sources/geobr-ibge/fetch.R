#!/usr/bin/env Rscript
# Fetch Brazil historical state boundaries from the geobr R package.
# geobr wraps IBGE's territorial division snapshots (1872, 1900, 1911, 1920,
# 1933, 1940, 1950, 1960, 1970, 1980, 1991, 2000, 2010, ...).
#
# This script reads needed (state, year) pairs from wiki frontmatter where
# polygon_source == 'geobr-ibge' and writes one GPKG with features keyed
# by (abbrev_state, year).

suppressPackageStartupMessages({
  library(sf)
  library(geobr)
})

proj_root <- normalizePath(file.path(dirname(sys.frame(1)$ofile), "../../.."))
out_dir   <- file.path(proj_root, "data/geodata/geobr-ibge")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

wiki_dir <- file.path(proj_root, "wiki/polities")
pages    <- list.files(wiki_dir, pattern = "\\.md$", full.names = TRUE)

parse_fm <- function(path) {
  lines <- readLines(path, warn = FALSE)
  if (length(lines) < 2 || lines[1] != "---") return(NULL)
  end <- which(lines[-1] == "---")[1]
  if (is.na(end)) return(NULL)
  fm <- list()
  for (l in lines[2:end]) {
    m <- regmatches(l, regexec("^([a-z_]+): *(.*)$", l))[[1]]
    if (length(m) == 3) fm[[m[2]]] <- trimws(gsub('"', '', m[3]))
  }
  fm
}

years_needed <- c()
for (p in pages) {
  fm <- parse_fm(p)
  if (isTRUE(fm$polygon_source == "geobr-ibge")) {
    y <- suppressWarnings(as.integer(fm$polygon_feature_year %||% fm$start_year))
    if (!is.na(y)) years_needed <- union(years_needed, y)
  }
}

if (length(years_needed) == 0) {
  message("No wiki pages cite geobr-ibge. Nothing to fetch.")
  quit(save = "no", status = 0)
}

parts <- list()
for (y in sort(years_needed)) {
  s <- tryCatch(read_state(year = y, showProgress = FALSE), error = function(e) NULL)
  if (is.null(s)) next
  s$year <- y
  parts[[length(parts) + 1]] <- s[, c("abbrev_state", "name_state", "year", "geom")]
}
out <- do.call(rbind, parts)
st_write(out, file.path(out_dir, "states.gpkg"), delete_dsn = TRUE, quiet = TRUE)
message("Wrote: ", file.path(out_dir, "states.gpkg"), " (", nrow(out), " features)")
