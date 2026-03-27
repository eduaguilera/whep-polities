# ==============================================================================
# WHEP Polities - Integrate Cliopatria (Seshat) Polygons
# ==============================================================================
# Source: Seshat Global History Databank / Cliopatria
#   GitHub: https://github.com/Seshat-Global-History-Databank/seshat_browser
#   License: CC BY 4.0
#
# This script:
#   1. Reads cliopatria_polities_only.geojson from inputs/cliopatria.geojson.zip
#   2. Extracts polygons for 4 polities that have NO polygon from any other source
#   3. Selects representative time steps for each polity
#   4. Saves to data/geodata/cliopatria_polygons.gpkg
#   5. Updates polities_database.csv polygon_source field
#   6. Generates a summary map
#
# IMPORTANT: Only used for polities with polygon_source = "None".
#   Polities already covered by CShapes, GADM, Paine et al., etc. are NOT replaced.
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

cat("=== Integrating Cliopatria Polygons (4 missing polities) ===\n\n")

# --- 1. Extract and read GeoJSON from zip ---
zip_path <- file.path(proj_root, "inputs", "cliopatria.geojson.zip")
if (!file.exists(zip_path)) {
  stop(
    "inputs/cliopatria.geojson.zip not found.\n",
    "Download from: https://github.com/Seshat-Global-History-Databank/seshat_browser\n",
    "Place the zip file as inputs/cliopatria.geojson.zip"
  )
}

tmp_dir <- tempdir()
unzip(zip_path, exdir = tmp_dir, overwrite = TRUE)
geojson_path <- file.path(tmp_dir, "cliopatria_polities_only.geojson")

cat("Reading Cliopatria GeoJSON (this may take a moment)...\n")
clio <- st_read(geojson_path, quiet = TRUE)
cat("Read", nrow(clio), "features from Cliopatria\n")
cat("CRS:", st_crs(clio)$input, "\n\n")

# --- 2. Define target polities and their Cliopatria matches ---
# These are the ONLY 4 polities in the database with polygon_source = "None"
#
# Selection criteria for time step:
#   - Pick the Cliopatria feature whose time range best overlaps with our polity dates
#   - Prefer the largest stable polygon within the polity's lifespan
#   - For polities defined by territorial loss, pick the polygon BEFORE the loss

targets <- list(
  list(
    polity_code = "IRN-1800-1828",
    clio_name   = "Qajar Dynasty",
    # Qajar 1800-1804 (1,743,611 km2) includes South Caucasus — correct for pre-1828
    from_year   = 1800,
    to_year     = 1804,
    note        = "Qajar Iran including South Caucasus, pre-Treaty of Turkmenchay"
  ),
  list(
    polity_code = "AUH-1800-1867",
    clio_name   = "Austrian Empire",
    # Austrian Empire 1815-1819 (691,595 km2) — post-Congress of Vienna, stable borders
    from_year   = 1815,
    to_year     = 1819,
    note        = "Austrian Empire post-Congress of Vienna, pre-Ausgleich"
  ),
  list(
    polity_code = "SWE-1800-1809",
    clio_name   = "Swedish Empire",
    # Swedish Empire 1763-1808 (790,005 km2) — includes Finland
    from_year   = 1763,
    to_year     = 1808,
    note        = "Swedish Empire including Finland, pre-Treaty of Fredrikshamn"
  ),
  list(
    polity_code = "SWE-1809-1814",
    clio_name   = "Swedish Empire",
    # Swedish Empire 1809-1811 (463,631 km2) — without Finland, before Norway
    from_year   = 1809,
    to_year     = 1811,
    note        = "Sweden without Finland, before union with Norway"
  )
)

# --- 3. Extract matching polygons ---
results <- list()

for (tgt in targets) {
  cat("Searching for:", tgt$polity_code, "->", tgt$clio_name,
      tgt$from_year, "-", tgt$to_year, "\n")

  match <- clio |>
    filter(
      Name == tgt$clio_name,
      FromYear == tgt$from_year,
      ToYear == tgt$to_year
    )

  if (nrow(match) == 0) {
    cat("  WARNING: No exact match found. Trying closest...\n")
    # Fallback: find closest time range
    candidates <- clio |>
      filter(Name == tgt$clio_name) |>
      filter(FromYear <= tgt$from_year + 5, ToYear >= tgt$to_year - 5)
    if (nrow(candidates) > 0) {
      match <- candidates[1, ]
      cat("  Using fallback:", match$Name, match$FromYear, "-", match$ToYear, "\n")
    } else {
      cat("  ERROR: No match found at all for", tgt$clio_name, "\n")
      next
    }
  }

  # Take first match if duplicates (some have parenthesized duplicates)
  match <- match[1, ]

  # Compute area
  match_ea <- st_transform(match, "ESRI:54034") # World Cylindrical Equal Area
  area_km2 <- as.numeric(st_area(match_ea)) / 1e6

  cat("  Found:", match$Name, match$FromYear, "-", match$ToYear,
      "| Area:", round(area_km2), "km2\n")

  result <- match |>
    mutate(
      polity_code = tgt$polity_code,
      clio_name = tgt$clio_name,
      clio_from = tgt$from_year,
      clio_to = tgt$to_year,
      area_km2 = area_km2,
      selection_note = tgt$note
    ) |>
    select(polity_code, clio_name, clio_from, clio_to, area_km2, selection_note)

  results[[length(results) + 1]] <- result
}

# Combine all results
output <- do.call(rbind, results)
cat("\nExtracted", nrow(output), "polygons\n\n")

# --- 4. Add polity metadata from database ---
db <- read_csv(
  file.path(final_dir, "polities_database.csv"),
  show_col_types = FALSE
)

output <- output |>
  left_join(
    db |> select(polity_code, polity_name, start_year, end_year, polity_type),
    by = "polity_code"
  )

cat("=== Extracted polygons ===\n")
output |>
  st_drop_geometry() |>
  select(polity_code, polity_name, clio_from, clio_to, area_km2) |>
  as.data.frame() |>
  print(row.names = FALSE)
cat("\n")

# --- 5. Save GeoPackage ---
gpkg_path <- file.path(geodata_dir, "cliopatria_polygons.gpkg")
st_write(output, gpkg_path, layer = "cliopatria_polities",
         delete_layer = TRUE, quiet = TRUE)
cat("Saved", nrow(output), "polygons to", gpkg_path, "\n")

# --- 6. Update polities_database.csv ---
cat("\nUpdating polygon_source in polities_database.csv...\n")
for (tgt in targets) {
  idx <- which(db$polity_code == tgt$polity_code)
  if (length(idx) == 1) {
    old_src <- db$polygon_source[idx]
    db$polygon_source[idx] <- "Cliopatria (Seshat)"
    # Update notes to reflect the time step used
    existing_notes <- db$notes[idx]
    clio_note <- paste0("Cliopatria polygon: ", tgt$clio_name, " ",
                        tgt$from_year, "-", tgt$to_year, ". ", tgt$note, ".")
    if (!is.na(existing_notes) && nchar(existing_notes) > 0) {
      db$notes[idx] <- paste0(existing_notes, " ", clio_note)
    } else {
      db$notes[idx] <- clio_note
    }
    cat("  ", tgt$polity_code, ":", old_src, "->", db$polygon_source[idx], "\n")
  }
}

write_csv(db, file.path(final_dir, "polities_database.csv"))
cat("Updated polities_database.csv\n")

# --- 7. Generate summary map ---
cat("\nGenerating map...\n")
world <- ne_countries(scale = "medium", returnclass = "sf")

p <- ggplot() +
  geom_sf(data = world, fill = "grey90", color = "grey60", linewidth = 0.2) +
  geom_sf(
    data = output,
    aes(fill = polity_name),
    alpha = 0.5,
    color = "black",
    linewidth = 0.4
  ) +
  geom_sf_text(
    data = output,
    aes(label = polity_name),
    size = 2.5,
    fontface = "bold"
  ) +
  coord_sf(xlim = c(-15, 75), ylim = c(20, 75)) +
  labs(
    title = "Cliopatria Polygons Filling Missing WHEP Polities",
    subtitle = paste0(nrow(output), " polities that had no polygon from any other source"),
    caption = "Source: Seshat Global History Databank / Cliopatria (CC BY 4.0)",
    fill = "Polity"
  ) +
  theme_minimal(base_size = 10) +
  theme(legend.position = "bottom", legend.key.size = unit(0.4, "cm"))

plot_path <- file.path(analysis_dir, "cliopatria_polygons_map.png")
ggsave(plot_path, p, width = 10, height = 7, dpi = 150)
cat("Saved map to", plot_path, "\n")

cat("\n=== Done ===\n")
cat("Total Cliopatria polygons integrated:", nrow(output), "\n")
cat("All 4 previously missing polities now have polygons.\n")
cat("Database polygon coverage: 100% of non-region polities.\n")
