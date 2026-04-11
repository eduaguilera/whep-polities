# ==============================================================================
# WHEP Polities — Fetch CShapes 2.0 (COW version)
# ==============================================================================
# Regenerates data/geodata/cshapes2_full.gpkg from the `cshapes` R package.
#
# The file is the COW-based distribution with dependencies included, i.e.
#     cshapes::cshp(useGW = FALSE, dependencies = TRUE)
# not the package default (the package defaults to useGW = TRUE).
#
# Verified 2026-04-11 to produce a file bit-equivalent in content to the
# previously-committed cshapes2_full.gpkg (805 rows, identical column set,
# identical attribute tuples, all 805 geometries st_equals-identical).
# See wiki/sources/cshapes-2.0.md and
# wiki/log.md § 2026-04-11 cshapes-reproducibility-verified.
#
# Usage:
#   Rscript R/00b_fetch_cshapes.R
#
# Writes: data/geodata/cshapes2_full.gpkg (~21 MB)

# Locate and source the setup script (handles both source() and Rscript).
.this_script <- local({
  if (!is.null(sys.frame(1)$ofile)) {
    normalizePath(sys.frame(1)$ofile)
  } else {
    args <- commandArgs(trailingOnly = FALSE)
    file_arg <- grep("^--file=", args, value = TRUE)
    if (length(file_arg) > 0) {
      normalizePath(sub("^--file=", "", file_arg))
    } else {
      normalizePath("R/00b_fetch_cshapes.R")
    }
  }
})
source(file.path(dirname(.this_script), "00_setup.R"))

if (!requireNamespace("cshapes", quietly = TRUE)) {
  stop(
    "Package 'cshapes' is not installed. Install with:\n",
    "  install.packages('cshapes')\n",
    "or add it to renv via renv::install('cshapes')."
  )
}

library(cshapes)
library(sf)

out_path <- file.path(geodata_dir, "cshapes2_full.gpkg")

cat("Fetching CShapes 2.0 (COW, dependencies=TRUE) ...\n")
cs <- cshapes::cshp(useGW = FALSE, dependencies = TRUE)
cat("  rows:", nrow(cs), "\n")
cat("  cols:", paste(names(cs), collapse = ", "), "\n")

cat("Writing ", out_path, " ...\n", sep = "")
st_write(cs, out_path, delete_dsn = TRUE, quiet = TRUE)

cat("Done. Regeneration is deterministic; content should match prior file.\n")
