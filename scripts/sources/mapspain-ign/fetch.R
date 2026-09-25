#!/usr/bin/env Rscript
# Fetch Spanish province boundaries from the mapSpain R package.
# Source: Instituto Geográfico Nacional (IGN). Provinces have been stable
# since 1833.

suppressPackageStartupMessages({
  library(sf)
  library(mapSpain)
})

# Resolve the project root whether this file is run with Rscript or source()d.
# `sys.frame(1)$ofile` is only set by source(), so the documented invocation
# (Rscript scripts/sources/<slug>/fetch.R) died with "not that many frames on the stack".
script_path <- local({
  a <- commandArgs(trailingOnly = FALSE)
  m <- grep("^--file=", a, value = TRUE)
  if (length(m)) sub("^--file=", "", m[1]) else sys.frame(1)$ofile
})
proj_root <- normalizePath(file.path(dirname(script_path), "../../.."))
out_dir   <- file.path(proj_root, "data/geodata/mapspain-ign")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

# moveCAN = FALSE: mapSpain by default shifts the Canary Islands next to the Peninsula as a
# map inset (lon -13..-8.5, lat 34.7..36.3), which placed Las Palmas and Santa Cruz de Tenerife
# in the ocean off Morocco instead of at their true position (lon -18.2..-13.3, lat 27.6..29.5).
provinces <- esp_get_prov(resolution = 3, moveCAN = FALSE)
# mapSpain uses `cpro` as the 2-digit province code.
keep <- c("cpro", "ine.prov.name", "iso2.prov.code", "geometry")
keep <- intersect(keep, names(provinces))
provinces <- provinces[, keep]
st_write(provinces, file.path(out_dir, "provinces.gpkg"), delete_dsn = TRUE, quiet = TRUE)
message("Wrote: ", file.path(out_dir, "provinces.gpkg"), " (", nrow(provinces), " provinces)")
