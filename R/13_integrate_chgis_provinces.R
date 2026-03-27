# ==============================================================================
# WHEP Polities - Integrate CHGIS v6 Qing Dynasty Province Polygons
# ==============================================================================
# Source: China Historical GIS (CHGIS) v6
#   Harvard University & Fudan University
#   Download: https://dataverse.harvard.edu/dataverse/chgis_v6
#   Dataset: "1820 Layers UTF8 Encoding" (doi:10.7910/DVN/ST5KKM)
#   File: v6_1820_prov_pgn_utf.zip (province-level polygons, 1820 snapshot)
#   License: Free for academic use, no commercial use or redistribution.
#   Citation: "CHGIS, Version: 6. (c) Fairbank Center for Chinese Studies,
#     Harvard University and Center for Historical Geographical Studies,
#     Fudan University, 2016."
#
# This script:
#   1. Reads v6_1820_prov_pgn_utf from inputs/chgis.zip
#   2. Maps Qing provinces to WHEP subnational polity codes
#   3. Excludes South China Sea island claims and treaty-disputed areas
#   4. Adds 26 subnational entries to polities_database.csv
#   5. Saves polygons to data/geodata/chgis_qing_provinces.gpkg
#   6. Generates a summary map
#
# The 1820 snapshot represents the stable Qing provincial structure.
# These provinces serve the same role as GADM admin-1 entries for modern
# China (1997-2025): subnational units for linking trade/production data.
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

cat("=== Integrating CHGIS v6 Qing Province Polygons ===\n\n")

# --- 1. Extract and read province shapefile from zip ---
zip_path <- file.path(proj_root, "inputs", "chgis.zip")
if (!file.exists(zip_path)) {
  stop(
    "inputs/chgis.zip not found.\n",
    "Download '1820 Layers UTF8 Encoding' from:\n",
    "  https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/ST5KKM\n",
    "Place the zip file as inputs/chgis.zip"
  )
}

tmp_dir <- tempdir()
# Extract inner zip from outer zip
inner_zip <- "v6_1820_prov_pgn_utf.zip"
unzip(zip_path, files = inner_zip, exdir = tmp_dir, overwrite = TRUE)
# Extract shapefile from inner zip
unzip(file.path(tmp_dir, inner_zip), exdir = file.path(tmp_dir, "prov"),
      overwrite = TRUE)

shp_path <- file.path(tmp_dir, "prov", "v6_1820_prov_pgn_utf.shp")
prov <- st_read(shp_path, quiet = TRUE)
cat("Read", nrow(prov), "province polygons from CHGIS v6 1820\n")
cat("CRS:", st_crs(prov)$input, "\n\n")

# --- 2. Map provinces to WHEP polity codes ---
# Exclude: South China Sea island claims (tiny, no trade data) and
# Nibuchu (treaty-disputed area with Russia, not an administered province)
#
# Code format: CN + 2-letter abbreviation + -1820-1912
# Matches modern subnational pattern (CNAH-1997-2025 etc.)
# Where Qing province maps to a modern province, same 2-letter code is reused.
# Qing-specific provinces get new codes.

prov_mapping <- data.frame(
  NAME_PY = c(
    # Core provinces (18 provinces / shiba sheng)
    "Zhili",        # 直隶 → became Hebei after 1912
    "Shandong",     # 山东
    "Shanxi",       # 山西
    "Henan",        # 河南
    "Jiangsu",      # 江苏
    "Anhui",        # 安徽
    "Zhejiang",     # 浙江
    "Fujian",       # 福建
    "Jiangxi",      # 江西
    "Hubei",        # 湖北
    "Hunan",        # 湖南
    "Guangdong",    # 广东
    "Guangxi",      # 广西
    "Sichuan",      # 四川
    "Guizhou",      # 贵州
    "Yunnan",       # 云南
    "Shaanxi",      # 陕西
    "Gansu",        # 甘肃
    # Manchuria (3)
    "Shengjing",    # 盛京 → became Liaoning/Fengtian
    "Heilongjiang", # 黑龙江
    "Jinlin",       # 吉林 (spelled Jinlin in data, = Jilin)
    # Frontier regions (5)
    "Xinjiang",     # 新疆
    "Xizang",       # 西藏 (Tibet)
    "Neimenggu",    # 内蒙古 (Inner Mongolia)
    "Wuliyasutai",  # 乌里雅苏台 (Outer Mongolia / Khalkha)
    "Qinghai"       # 青海
  ),
  polity_code = c(
    # Core provinces — reuse modern 2-letter where possible
    "CNZL-1820-1912",  # Zhili (no modern equivalent, new code ZL)
    "CNSD-1820-1912",  # Shandong
    "CNSX-1820-1912",  # Shanxi
    "CNHE-1820-1912",  # Henan
    "CNJS-1820-1912",  # Jiangsu
    "CNAH-1820-1912",  # Anhui
    "CNZJ-1820-1912",  # Zhejiang
    "CNFJ-1820-1912",  # Fujian
    "CNJX-1820-1912",  # Jiangxi
    "CNHU-1820-1912",  # Hubei
    "CNHN-1820-1912",  # Hunan
    "CNGD-1820-1912",  # Guangdong
    "CNGX-1820-1912",  # Guangxi
    "CNSC-1820-1912",  # Sichuan
    "CNGZ-1820-1912",  # Guizhou
    "CNYN-1820-1912",  # Yunnan
    "CNSA-1820-1912",  # Shaanxi
    "CNGS-1820-1912",  # Gansu
    # Manchuria
    "CNSJ-1820-1912",  # Shengjing (new code SJ)
    "CNHL-1820-1912",  # Heilongjiang
    "CNJL-1820-1912",  # Jilin
    # Frontier regions
    "CNXJ-1820-1912",  # Xinjiang
    "CNXZ-1820-1912",  # Xizang (Tibet)
    "CNNM-1820-1912",  # Neimenggu (Inner Mongolia)
    "CNWL-1820-1912",  # Wuliyasutai (Outer Mongolia, new code WL)
    "CNQH-1820-1912"   # Qinghai
  ),
  polity_name = c(
    "Zhili (Province)",
    "Shandong (Province)",
    "Shanxi (Province)",
    "Henan (Province)",
    "Jiangsu (Province)",
    "Anhui (Province)",
    "Zhejiang (Province)",
    "Fujian (Province)",
    "Jiangxi (Province)",
    "Hubei (Province)",
    "Hunan (Province)",
    "Guangdong (Province)",
    "Guangxi (Province)",
    "Sichuan (Province)",
    "Guizhou (Province)",
    "Yunnan (Province)",
    "Shaanxi (Province)",
    "Gansu (Province)",
    "Shengjing (Manchuria)",
    "Heilongjiang (Manchuria)",
    "Jilin (Manchuria)",
    "Xinjiang (Province)",
    "Xizang (Tibet)",
    "Nei Mongol (Inner Mongolia)",
    "Wuliyasutai (Outer Mongolia)",
    "Qinghai (Province)"
  ),
  stringsAsFactors = FALSE
)

cat("Mapping", nrow(prov_mapping), "Qing provinces to WHEP codes\n")
cat("Excluding:", nrow(prov) - nrow(prov_mapping),
    "records (SCS island claims + treaty-disputed area)\n\n")

# --- 3. Join mapping to spatial data ---
matched <- prov |>
  inner_join(prov_mapping, by = "NAME_PY")

cat("Matched provinces:", nrow(matched), "\n")

# Check for unmatched
unmatched_data <- prov |>
  filter(!NAME_PY %in% prov_mapping$NAME_PY)
if (nrow(unmatched_data) > 0) {
  cat("Excluded:", paste(unmatched_data$NAME_PY, collapse = ", "), "\n")
}
cat("\n")

# --- 4. Compute areas ---
matched_ea <- st_transform(matched, "ESRI:102025")  # Asia North Albers Equal Area
matched$area_km2 <- as.numeric(st_area(matched_ea)) / 1e6

cat("=== Province areas (km2) ===\n")
area_summary <- matched |>
  st_drop_geometry() |>
  select(polity_code, NAME_PY, NAME_CH, area_km2) |>
  arrange(desc(area_km2))
print(as.data.frame(area_summary), row.names = FALSE)
cat("\nTotal Qing territory (excl. SCS):",
    format(sum(matched$area_km2), big.mark = ","), "km2\n\n")

# --- 5. Save GeoPackage ---
output_sf <- matched |>
  select(polity_code, polity_name, chgis_name_py = NAME_PY,
         chgis_name_ch = NAME_CH, area_km2)

gpkg_path <- file.path(geodata_dir, "chgis_qing_provinces.gpkg")
st_write(output_sf, gpkg_path, layer = "qing_provinces_1820",
         delete_layer = TRUE, quiet = TRUE)
cat("Saved", nrow(output_sf), "polygons to", gpkg_path, "\n")

# --- 6. Add entries to polities_database.csv ---
cat("\nAdding subnational entries to polities_database.csv...\n")

db <- read_csv(
  file.path(final_dir, "polities_database.csv"),
  show_col_types = FALSE
)

# Parent polity for Qing subnational entries
parent_code <- "CHN-1800-1895"

new_entries <- matched |>
  st_drop_geometry() |>
  transmute(
    polity_code = polity_code,
    polity_name = polity_name,
    start_year = 1820L,
    end_year = 1912L,
    duration_years = 1912L - 1820L + 1L,
    polity_type = "subnational",
    continent = "Asia",
    iso3_code = "CHN",
    cow_code = NA_real_,
    polygon_source = "CHGIS v6 (subnational)",
    predecessor = NA_character_,
    successor = NA_character_,
    data_sources = "CHGIS",
    verification_status = "VERIFIED",
    notes = paste0("Parent: ", parent_code,
                    "; CHGIS v6 1820 province: ", NAME_PY,
                    " (", NAME_CH, ")",
                    "; Area: ", format(round(area_km2), big.mark = ","),
                    " km2")
  )

# Check for conflicts with existing codes
existing_codes <- db$polity_code
conflicts <- new_entries$polity_code[new_entries$polity_code %in% existing_codes]
if (length(conflicts) > 0) {
  cat("  WARNING: Conflicting codes (already exist):", paste(conflicts, collapse = ", "), "\n")
  cat("  These will NOT be added again.\n")
  new_entries <- new_entries |> filter(!polity_code %in% existing_codes)
}

db_updated <- bind_rows(db, new_entries)
write_csv(db_updated, file.path(final_dir, "polities_database.csv"))
cat("Added", nrow(new_entries), "new subnational entries\n")
cat("Database now has", nrow(db_updated), "entries\n")

# --- 7. Update knowledge graph ---
cat("\nUpdating knowledge graph...\n")

nodes_path <- file.path(analysis_dir, "knowledge_graph_nodes.csv")
edges_path <- file.path(analysis_dir, "knowledge_graph_edges.csv")

if (file.exists(nodes_path) && file.exists(edges_path)) {
  nodes <- read_csv(nodes_path, show_col_types = FALSE)
  edges <- read_csv(edges_path, show_col_types = FALSE)

  # Add new nodes
  new_nodes <- new_entries |>
    transmute(
      id = polity_code,
      label = polity_name,
      type = polity_type,
      continent = continent,
      start_year = start_year,
      end_year = end_year,
      degree = 1L  # at least continent edge
    )
  nodes <- bind_rows(nodes, new_nodes)

  # Add continent edges
  new_edges_continent <- new_entries |>
    transmute(
      source = polity_code,
      target = "Asia",
      relation = "located_in_continent",
      weight = 1L
    )
  edges <- bind_rows(edges, new_edges_continent)

  # Update degree counts for Asia node
  asia_idx <- which(nodes$id == "Asia")
  if (length(asia_idx) == 1) {
    nodes$degree[asia_idx] <- sum(edges$source == "Asia" | edges$target == "Asia")
  }

  write_csv(nodes, nodes_path)
  write_csv(edges, edges_path)
  cat("  Added", nrow(new_nodes), "nodes and", nrow(new_edges_continent), "edges\n")
  cat("  Knowledge graph:", nrow(nodes), "nodes,", nrow(edges), "edges\n")
}

# --- 8. Generate summary map ---
cat("\nGenerating map...\n")
world <- ne_countries(scale = "medium", returnclass = "sf") |>
  filter(continent == "Asia" | name %in% c("Russia", "Mongolia"))

p <- ggplot() +
  geom_sf(data = world, fill = "grey90", color = "grey60", linewidth = 0.2) +
  geom_sf(
    data = output_sf,
    aes(fill = polity_name),
    alpha = 0.5,
    color = "black",
    linewidth = 0.3
  ) +
  geom_sf_text(
    data = output_sf |> filter(area_km2 > 100000),
    aes(label = chgis_name_py),
    size = 2.0,
    fontface = "bold"
  ) +
  coord_sf(xlim = c(70, 145), ylim = c(15, 55)) +
  labs(
    title = "Qing Dynasty Provinces (CHGIS v6, 1820 Snapshot)",
    subtitle = paste0(nrow(output_sf), " subnational entries for WHEP polities database"),
    caption = paste0(
      "Source: CHGIS v6, Harvard University & Fudan University\n",
      "doi:10.7910/DVN/ST5KKM (1820 Layers UTF8 Encoding)"
    )
  ) +
  theme_minimal(base_size = 10) +
  theme(legend.position = "none")

plot_path <- file.path(analysis_dir, "chgis_qing_provinces_map.png")
ggsave(plot_path, p, width = 12, height = 8, dpi = 150)
cat("Saved map to", plot_path, "\n")

cat("\n=== Done ===\n")
cat("Total Qing province entries added:", nrow(new_entries), "\n")
cat("Polygon source: CHGIS v6 (doi:10.7910/DVN/ST5KKM)\n")
cat("Period: 1820-1912 (Qing dynasty, 1820 admin structure)\n")
cat("Parent polity:", parent_code, "\n")
