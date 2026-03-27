# ==============================================================================
# WHEP Polities - Integrate Pre-Colonial African State Polygons
# ==============================================================================
# Source: Paine, Qiu & Ricart-Huguet (2024), "Endogenous Colonial Borders:
#   Precolonial States and Geography in the Partition of Africa", APSR 119(1).
# Data: Harvard Dataverse doi:10.7910/DVN/9QJVJ1
#   File: PCS.shp in Shapefiles/Precolonial states/
# License: Free download from Harvard Dataverse (do not redistribute).
#
# This script:
#   1. Reads PCS.shp from the inputs/paine_et_al.zip archive
#   2. Maps each polygon to a WHEP polity code
#   3. Computes areas in km2
#   4. Saves to data/geodata/precolonial_polygons.gpkg
#   5. Generates a summary map
# ==============================================================================

# Source setup (works with both source() and Rscript)
tryCatch(
  source(file.path(dirname(sys.frame(1)$ofile), "00_setup.R")),
  error = function(e) {
    args <- commandArgs(trailingOnly = FALSE)
    fa <- grep("^--file=", args, value = TRUE)
    if (length(fa) > 0) {
      source(file.path(dirname(sub("^--file=", "", fa)), "00_setup.R"))
    } else {
      source("R/00_setup.R")
    }
  }
)

cat("=== Integrating Pre-Colonial African State Polygons ===\n\n")

# --- 1. Extract and read PCS.shp from zip ---
zip_path <- file.path(proj_root, "inputs", "paine_et_al.zip")
if (!file.exists(zip_path)) {
  stop(
    "inputs/paine_et_al.zip not found.\n",
    "Download from: https://dataverse.harvard.edu/dataset.xhtml?",
    "persistentId=doi:10.7910/DVN/9QJVJ1\n",
    "Place the zip file as inputs/paine_et_al.zip"
  )
}

# Extract to temp directory
tmp_dir <- tempdir()
shp_pattern <- "Precolonial states/PCS\\."
zip_contents <- unzip(zip_path, list = TRUE)$Name
pcs_files <- zip_contents[grepl(shp_pattern, zip_contents)]
cat("Extracting", length(pcs_files), "PCS shapefile components...\n")
unzip(zip_path, files = pcs_files, exdir = tmp_dir, overwrite = TRUE)

shp_path <- file.path(
  tmp_dir,
  "AfricanBordersReplication/Shapefiles/Precolonial states/PCS.shp"
)
pcs <- st_read(shp_path, quiet = TRUE)
cat("Read", nrow(pcs), "pre-colonial state polygons from PCS.shp\n")
cat("CRS:", st_crs(pcs)$input, "\n\n")

# --- 2. Map PCS names to WHEP polity codes ---
pcs_to_whep <- c(
  # --- 20 new kingdoms (first batch) ---
  "Asante"     = "ASH-1800-1896",
  "Sokoto"     = "SOK-1804-1903",
  "Dahomey"    = "DHY-1800-1894",
  "Zulu"       = "ZUL-1816-1879",
  "Borno"      = "BNU-1800-1893",
  "Wadai"      = "WAD-1800-1912",
  "Darfur"     = "DFR-1800-1874",
  "Buganda"    = "BGA-1800-1894",
  "Bunyoro"    = "BNY-1800-1899",
  "Benin"      = "BKN-1800-1897",
  "Luba"       = "LBA-1800-1885",
  "Lunda"      = "LND-1800-1887",
  "Futa Jalon" = "FTJ-1800-1896",
  "Ndebele"    = "NDB-1823-1894",
  "Gaza"       = "GZE-1824-1895",
  "Oyo"        = "OYO-1800-1836",
  "Rwanda"     = "RWK-1800-1890",
  "Burundi"    = "BDK-1800-1890",
  "Lesotho"    = "LST-1822-1868",
  "Swazi"      = "SWK-1800-1894",
  # --- 23 remaining PCS states ---
  "Lozi"       = "LZI-1800-1890",
  "Borgu"      = "BRG-1800-1897",
  "Dagomba"    = "DGM-1800-1899",
  "Mossi"      = "MOS-1800-1897",
  "Damagaram"  = "DMG-1800-1899",
  "Gobir"      = "GOB-1800-1808",
  "Porto Novo" = "PNV-1800-1882",
  "Bundu"      = "BND-1800-1887",
  "Futa Toro"  = "FTT-1800-1862",
  "Igala"      = "IGL-1800-1901",
  "Walo"       = "WLO-1800-1855",
  "Cayor"      = "CAY-1800-1886",
  "Sine"       = "SNE-1800-1887",
  "Jolof"      = "JOL-1800-1890",
  "Salum"      = "SLM-1800-1887",
  "Nkore"      = "NKR-1800-1901",
  "Kasanje"    = "KSJ-1800-1911",
  "Tunis"      = "TUN-1800-1881",
  "Bemba"      = "BMB-1800-1899",
  "Ibadan"     = "IBD-1829-1893",
  "Egba"       = "EGB-1830-1914",
  "Ijebu"      = "IJB-1800-1892",
  "Kazembe"    = "KZM-1800-1899",
  # --- Existing polities that also get Paine polygons ---
  "Ethiopia"   = "ETH-1800-1889",
  "Egypt"      = "EGY-1800-1899",
  "Morocco"    = "MOR-1800-1904"
)

# Add polity_code column
pcs$polity_code <- pcs_to_whep[pcs$PCS]

# Split into matched and unmatched
matched <- pcs[!is.na(pcs$polity_code), ]
unmatched <- pcs[is.na(pcs$polity_code), ]

cat("Matched to WHEP polity codes:", nrow(matched), "\n")
cat("Unmatched (not in WHEP DB):", nrow(unmatched), "\n")
cat("  Unmatched states:", paste(unmatched$PCS, collapse = ", "), "\n\n")

# --- 3. Compute areas ---
# Transform to equal-area projection for area calculation
matched_ea <- st_transform(matched, "ESRI:102022") # Africa Albers Equal Area
matched$area_km2 <- as.numeric(st_area(matched_ea)) / 1e6

cat("=== Area summary (km2) ===\n")
area_summary <- matched |>
  st_drop_geometry() |>
  select(polity_code, PCS, area_km2) |>
  arrange(desc(area_km2))
print(as.data.frame(area_summary), row.names = FALSE)
cat("\n")

# --- 4. Read polities database for metadata ---
db <- read_csv(
  file.path(final_dir, "polities_database.csv"),
  show_col_types = FALSE
)

# Build output sf with full metadata
output <- matched |>
  select(polity_code, pcs_name = PCS, pcs_source = Source, area_km2) |>
  left_join(
    db |> select(polity_code, polity_name, start_year, end_year, polity_type),
    by = "polity_code"
  )

# --- 5. Save GeoPackage ---
gpkg_path <- file.path(geodata_dir, "precolonial_polygons.gpkg")
st_write(output, gpkg_path, layer = "precolonial_states", delete_layer = TRUE, quiet = TRUE)
cat("Saved", nrow(output), "polygons to", gpkg_path, "\n")

# Also save the full PCS (all 46) as a reference layer
st_write(pcs, gpkg_path, layer = "pcs_all_46", delete_layer = TRUE, quiet = TRUE)
cat("Saved all 46 PCS polygons as reference layer\n\n")

# --- 6. Generate summary map ---
cat("Generating map...\n")
world <- ne_countries(scale = "medium", returnclass = "sf") |>
  filter(continent == "Africa")

p <- ggplot() +
  geom_sf(data = world, fill = "grey90", color = "grey60", linewidth = 0.2) +
  geom_sf(
    data = output,
    aes(fill = polity_type),
    alpha = 0.6,
    color = "black",
    linewidth = 0.3
  ) +
  geom_sf_text(
    data = output |> filter(area_km2 > 50000),
    aes(label = pcs_name),
    size = 2.2,
    fontface = "bold"
  ) +
  scale_fill_manual(values = c("historical" = "#E74C3C")) +
  coord_sf(xlim = c(-20, 55), ylim = c(-37, 38)) +
  labs(
    title = "Pre-Colonial African States with Paine et al. (2024) Polygons",
    subtitle = paste0(nrow(output), " states matched to WHEP polity codes"),
    caption = "Source: Paine, Qiu & Ricart-Huguet (2024), Harvard Dataverse doi:10.7910/DVN/9QJVJ1",
    fill = "Polity type"
  ) +
  theme_minimal(base_size = 10) +
  theme(legend.position = "none")

plot_path <- file.path(analysis_dir, "precolonial_states_map.png")
ggsave(plot_path, p, width = 8, height = 10, dpi = 150)
cat("Saved map to", plot_path, "\n")

cat("\n=== Done ===\n")
cat("Total pre-colonial polygons integrated:", nrow(output), "\n")
cat("  New polities (no previous polygon):", sum(output$polity_code %in%
  c("ASH-1800-1896", "SOK-1804-1903", "DHY-1800-1894", "ZUL-1816-1879",
    "BNU-1800-1893", "WAD-1800-1912", "DFR-1800-1874", "BGA-1800-1894",
    "BNY-1800-1899", "BKN-1800-1897", "LBA-1800-1885", "LND-1800-1887",
    "FTJ-1800-1896", "NDB-1823-1894", "GZE-1824-1895", "OYO-1800-1836",
    "RWK-1800-1890", "BDK-1800-1890", "LST-1822-1868", "SWK-1800-1894")), "\n")
cat("  Existing polities (updated polygon):", sum(output$polity_code %in%
  c("ETH-1800-1889", "EGY-1800-1899", "MOR-1800-1904")), "\n")
