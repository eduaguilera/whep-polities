#!/usr/bin/env Rscript
# Fetch Spanish province boundaries from the mapSpain R package.
# Source: Instituto Geográfico Nacional (IGN). Provinces have been stable
# since 1833.

suppressPackageStartupMessages({
  library(sf)
  library(mapSpain)
})

proj_root <- normalizePath(file.path(dirname(sys.frame(1)$ofile), "../../.."))
out_dir   <- file.path(proj_root, "data/geodata/mapspain-ign")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

provinces <- esp_get_prov(resolution = 3)
# mapSpain uses `cpro` as the 2-digit province code.
keep <- c("cpro", "ine.prov.name", "iso2.prov.code", "geometry")
keep <- intersect(keep, names(provinces))
provinces <- provinces[, keep]
st_write(provinces, file.path(out_dir, "provinces.gpkg"), delete_dsn = TRUE, quiet = TRUE)
message("Wrote: ", file.path(out_dir, "provinces.gpkg"), " (", nrow(provinces), " provinces)")
