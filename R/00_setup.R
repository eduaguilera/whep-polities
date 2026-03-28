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
library(igraph)
library(gridExtra)
library(RColorBrewer)

# Project paths
# Support both source() and Rscript invocation
if (!is.null(sys.frame(1)$ofile)) {
  proj_root <- normalizePath(file.path(dirname(sys.frame(1)$ofile), ".."))
} else {
  # Called via Rscript — use commandArgs to find script location
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  if (length(file_arg) > 0) {
    proj_root <- normalizePath(file.path(dirname(sub("^--file=", "", file_arg)), ".."))
  } else {
    proj_root <- normalizePath(".")
  }
}

data_dir <- file.path(proj_root, "data")
final_dir <- file.path(data_dir, "final")
whep_dir <- file.path(data_dir, "whep-source")
geodata_dir <- file.path(data_dir, "geodata")
analysis_dir <- file.path(data_dir, "analysis")
ext_dir <- file.path(data_dir, "external")
compiled_dir <- file.path(data_dir, "compiled")
output_dir <- file.path(proj_root, "output")
plot_dir <- file.path(analysis_dir, "plots")
report_dir <- file.path(output_dir, "reports")

gadm_path <- "/home/usuario/LandInG/gadm/gadm36_levels.gpkg"
gadm41_path <- file.path(proj_root, "inputs", "gadm_410.gpkg")

for (d in c(
  compiled_dir,
  final_dir,
  geodata_dir,
  analysis_dir,
  plot_dir,
  report_dir,
  output_dir
)) {
  dir.create(d, recursive = TRUE, showWarnings = FALSE)
}

# Common color palettes
TYPE_COLORS <- c(
  sovereign = "#2196F3",
  historical = "#FF9800",
  colonial = "#F44336",
  dependency = "#9C27B0",
  mandate = "#E91E63",
  occupation = "#673AB7",
  aggregate = "#607D8B",
  region = "#795548",
  disputed = "#FF5722",
  puppet = "#9E9E9E",
  subnational = "#4CAF50",
  continent = "#FFC107"
)

CONTINENT_COLORS <- c(
  Africa = "#E53935",
  Asia = "#FF9800",
  Europe = "#1E88E5",
  `North America` = "#43A047",
  `South America` = "#8E24AA",
  Oceania = "#00ACC1",
  Antarctica = "#546E7A",
  Global = "#757575"
)

RELATION_COLORS <- c(
  located_in_continent = "#78909C",
  region_contains = "#42A5F5",
  subregion_of = "#66BB6A",
  temporal_next = "#FFA726",
  aggregate_covers = "#AB47BC",
  colonial_ruler_of = "#EF5350",
  same_territory = "#26C6DA",
  successor_of = "#8D6E63",
  predecessor_of = "#BDBDBD"
)

cat("Setup complete. Project root:", proj_root, "\n")
