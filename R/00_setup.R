# ==============================================================================
# WHEP Polities Research Project - Setup
# ==============================================================================
# Load required packages (managed by renv)

library(readr)
library(dplyr)
library(ggplot2)
library(tidyr)
library(stringr)
library(purrr)
library(forcats)
library(tibble)
library(sf)
library(rnaturalearth)
library(rnaturalearthdata)
library(scales)
library(viridis)

# Project paths
proj_root <- normalizePath(file.path(dirname(sys.frame(1)$ofile), ".."))

data_dir      <- file.path(proj_root, "data")
whep_dir      <- file.path(data_dir, "whep-source")
ext_dir       <- file.path(data_dir, "external")
compiled_dir  <- file.path(data_dir, "compiled")
output_dir    <- file.path(proj_root, "output")
plot_dir      <- file.path(output_dir, "plots")
report_dir    <- file.path(output_dir, "reports")

for (d in c(compiled_dir, plot_dir, report_dir)) {
  dir.create(d, recursive = TRUE, showWarnings = FALSE)
}

cat("Setup complete. Project root:", proj_root, "\n")
