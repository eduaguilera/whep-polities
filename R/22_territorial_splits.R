# ==============================================================================
# Territorial Splits for 1800-Start Entries with >10% Area Changes
# ==============================================================================
# Audit of all 227 entries starting at 1800 cross-referenced with Cliopatria
# time-stepped areas identified 4 entries where metropolitan territory changed
# >10% during the entry's span without being split.
#
# 1. NLD-1800-2025 -> NLD-1800-1830 + NLD-1830-2025 (-42%, Belgium secession)
# 2. NPL-1800-2025 -> NPL-1800-1816 + NPL-1816-2025 (-34%, Sugauli Treaty)
# 3. OMN-1800-2025 -> OMN-1800-1856 + OMN-1856-2025 (-50%+, Zanzibar split)
# 4. COL-1800-1903 -> COL-1800-1830 + COL-1830-1903 (-34%, Gran Colombia)
#
# USA and Russia deferred (continuous expansion, would need many splits).
# GBR/ESP/PRT: Cliopatria includes colonial empires; metropolitan territory
# was stable. Colonies tracked separately. No split needed.
#
# Memory-safe: Cliopatria reads via SQL, one polygon at a time.
# Run AFTER R/21.
# ==============================================================================

source("R/00_setup.R")
sf_use_s2(FALSE)

cat("=== Territorial Splits (1800-start audit) ===\n\n")

db <- read_csv(file.path(final_dir, "polities_database.csv"), show_col_types = FALSE)
cat("Loaded database:", nrow(db), "entries\n")

poly_path <- file.path(geodata_dir, "polities_polygons.gpkg")
polys <- st_read(poly_path, quiet = TRUE) %>% st_set_crs(4326)
cat("Loaded polygons:", nrow(polys), "features\n")

clio_path <- file.path(proj_root, "data", "source", "cliopatria",
                        "cliopatria_polities_only.geojson")
if (!file.exists(clio_path)) {
  tmp_dir <- tempdir()
  unzip(file.path(proj_root, "inputs", "cliopatria.geojson.zip"),
        exdir = tmp_dir, overwrite = TRUE)
  clio_path <- file.path(tmp_dir, "cliopatria_polities_only.geojson")
}
cat("Cliopatria:", clio_path, "\n\n")

existing_codes <- db$polity_code
new_entries <- list()
changes <- 0

read_clio <- function(name, from_year, to_year) {
  query <- sprintf(
    "SELECT * FROM cliopatria_polities_only WHERE Name = '%s' AND FromYear <= %d AND ToYear >= %d LIMIT 1",
    gsub("'", "''", name), from_year, to_year
  )
  tryCatch({
    feat <- st_read(clio_path, query = query, quiet = TRUE)
    if (nrow(feat) > 0) return(st_set_crs(feat[1, ], 4326) %>% st_make_valid())
    NULL
  }, error = function(e) NULL)
}

# Helper: split an existing entry into two periods
split_entry <- function(old_code, split_year, pre_name, post_name, pre_type, post_type,
                         pre_notes, post_notes, pre_clio_name, pre_clio_year,
                         post_clio_name, post_clio_year) {

  old_idx <- which(db$polity_code == old_code)
  if (length(old_idx) != 1) { cat(sprintf("  SKIP: %s not found\n", old_code)); return() }

  old_row <- db[old_idx, ]
  prefix <- strsplit(old_code, "-")[[1]][1]
  end_year <- as.integer(old_row$end_year)

  pre_code <- sprintf("%s-1800-%d", prefix, split_year)
  post_code <- sprintf("%s-%d-%d", prefix, split_year, end_year)

  # Reclassify old entry as aggregate
  db$polity_type[old_idx] <<- "aggregate"
  db$notes[old_idx] <<- sprintf("Aggregate for continuous trade data linkage. Split at %d.", split_year)

  # Create pre-split entry
  if (!pre_code %in% existing_codes) {
    new_entries[[length(new_entries) + 1]] <<- tibble(
      polity_code = pre_code,
      polity_name = pre_name,
      start_year = 1800L, end_year = as.integer(split_year),
      duration_years = as.integer(split_year) - 1800L + 1L,
      polity_type = pre_type,
      continent = old_row$continent,
      iso3_code = old_row$iso3_code,
      cow_code = NA_character_,
      polygon_source = NA_character_,
      predecessor = NA_character_,
      successor = post_code,
      data_sources = "CShapes; Cliopatria; research",
      verification_status = "VERIFIED",
      notes = pre_notes
    )
    existing_codes <<- c(existing_codes, pre_code)

    # Get Cliopatria polygon
    clio_feat <- read_clio(pre_clio_name, pre_clio_year[1], pre_clio_year[2])
    if (!is.null(clio_feat)) {
      polys <<- bind_rows(polys, st_sf(polity_code = pre_code, geometry = st_geometry(clio_feat)))
      new_entries[[length(new_entries)]]$polygon_source <<-
        sprintf("Cliopatria (%s %d-%d)", pre_clio_name, pre_clio_year[1], pre_clio_year[2])
      cat(sprintf("  ADD: %s with Cliopatria polygon\n", pre_code))
    } else {
      # Fallback: use existing polygon
      old_poly <- polys[polys$polity_code == old_code, ]
      if (nrow(old_poly) > 0) {
        polys <<- bind_rows(polys, st_sf(polity_code = pre_code, geometry = st_geometry(old_poly[1,])))
        new_entries[[length(new_entries)]]$polygon_source <<- old_row$polygon_source
      }
      cat(sprintf("  ADD: %s (Cliopatria not found, using fallback)\n", pre_code))
    }
    changes <<- changes + 1
  }

  # Create post-split entry
  if (!post_code %in% existing_codes) {
    new_entries[[length(new_entries) + 1]] <<- tibble(
      polity_code = post_code,
      polity_name = post_name,
      start_year = as.integer(split_year), end_year = end_year,
      duration_years = end_year - as.integer(split_year) + 1L,
      polity_type = post_type,
      continent = old_row$continent,
      iso3_code = old_row$iso3_code,
      cow_code = NA_character_,
      polygon_source = NA_character_,
      predecessor = pre_code,
      successor = NA_character_,
      data_sources = "CShapes; Cliopatria; research",
      verification_status = "VERIFIED",
      notes = post_notes
    )
    existing_codes <<- c(existing_codes, post_code)

    clio_feat <- read_clio(post_clio_name, post_clio_year[1], post_clio_year[2])
    if (!is.null(clio_feat)) {
      polys <<- bind_rows(polys, st_sf(polity_code = post_code, geometry = st_geometry(clio_feat)))
      new_entries[[length(new_entries)]]$polygon_source <<-
        sprintf("Cliopatria (%s %d-%d)", post_clio_name, post_clio_year[1], post_clio_year[2])
      cat(sprintf("  ADD: %s with Cliopatria polygon\n", post_code))
    } else {
      old_poly <- polys[polys$polity_code == old_code, ]
      if (nrow(old_poly) > 0) {
        polys <<- bind_rows(polys, st_sf(polity_code = post_code, geometry = st_geometry(old_poly[1,])))
        new_entries[[length(new_entries)]]$polygon_source <<- old_row$polygon_source
      }
      cat(sprintf("  ADD: %s (Cliopatria not found, using fallback)\n", post_code))
    }
    changes <<- changes + 1
  }

  # Update any existing successor references to old_code
  for (i in seq_len(nrow(db))) {
    if (!is.na(db$successor[i]) && db$successor[i] != "NA" && grepl(old_code, db$successor[i], fixed = TRUE)) {
      db$successor[i] <<- gsub(old_code, pre_code, db$successor[i], fixed = TRUE)
    }
    if (!is.na(db$predecessor[i]) && db$predecessor[i] != "NA" && grepl(old_code, db$predecessor[i], fixed = TRUE)) {
      db$predecessor[i] <<- gsub(old_code, post_code, db$predecessor[i], fixed = TRUE)
    }
  }

  cat(sprintf("  %s reclassified as aggregate, split at %d\n", old_code, split_year))
  changes <<- changes + 1
}

# ==============================================================================
# 1. Netherlands: lost Belgium 1830 (-42%)
# ==============================================================================
cat("--- 1. Netherlands: Belgium secession 1830 ---\n")
split_entry(
  "NLD-1800-2025", 1830,
  "United Kingdom of the Netherlands", "Netherlands",
  "historical", "sovereign",
  "United Kingdom of Netherlands (1815-1830) including Belgium and Luxembourg. ~71K km2. Belgian Revolution 1830 led to -42% territory loss.",
  "Netherlands after Belgian secession. ~41K km2. Luxembourg personal union until 1890.",
  "Netherlands", c(1815, 1819),
  "Netherlands", c(1834, 1839)
)

# ==============================================================================
# 2. Nepal: Sugauli Treaty 1816 (-34%)
# ==============================================================================
cat("\n--- 2. Nepal: Sugauli Treaty 1816 ---\n")
split_entry(
  "NPL-1800-2025", 1816,
  "Greater Nepal", "Nepal",
  "historical", "sovereign",
  "Greater Nepal under Prithvi Narayan Shah's successors. ~227K km2 at peak (1814). Treaty of Sugauli (1816) ceded Sikkim, Kumaon, Garhwal, western Terai to British India. -34% territory loss.",
  "Nepal post-Sugauli Treaty. ~149K km2. Borders largely stable since 1816.",
  "Nepal", c(1800, 1802),
  "Nepal", c(1820, 1835)
)

# ==============================================================================
# 3. Oman: Zanzibar separation 1856 (-50%+)
# ==============================================================================
cat("\n--- 3. Oman: Zanzibar separation 1856 ---\n")
split_entry(
  "OMN-1800-2025", 1856,
  "Omani Empire", "Sultanate of Oman",
  "historical", "sovereign",
  "Omani Empire including East African coast (Zanzibar, Pemba, mainland strip). Said bin Sultan ruled from Zanzibar (moved capital 1840). ~176K km2 at peak. Split on his death 1856: Zanzibar and Oman became separate sultanates.",
  "Sultanate of Oman (Muscat) after separation from Zanzibar 1856. ~80-310K km2 (varying with interior tribal control). Zanzibar tracked separately as ZAN-1856-1964.",
  "Sultanate of Oman", c(1840, 1855),
  "Sultanate of Oman", c(1856, 1858)
)

# ==============================================================================
# 4. Colombia: Gran Colombia dissolution 1830 (-34%)
# ==============================================================================
cat("\n--- 4. Colombia: Gran Colombia dissolution 1830 ---\n")
split_entry(
  "COL-1800-1903", 1830,
  "Gran Colombia", "Colombia (to 1903)",
  "historical", "historical",
  "Includes Gran Colombia period (1819-1830): Colombia + Venezuela + Ecuador + Panama. ~4.3M km2 at peak. Dissolved 1830: Venezuela and Ecuador seceded. -34% loss.",
  "Republic of New Granada / Colombia after Gran Colombia. ~2.8M km2. Lost Panama 1903.",
  "Gran Colombia", c(1822, 1823),
  "Gran Colombia", c(1830, 1833)
)

# ==============================================================================
# Save results
# ==============================================================================

cat("\n--- Saving results ---\n")

if (length(new_entries) > 0) {
  new_df <- bind_rows(new_entries)
  new_df$cow_code <- as.numeric(new_df$cow_code)
  new_df$start_year <- as.integer(new_df$start_year)
  new_df$end_year <- as.integer(new_df$end_year)
  new_df$duration_years <- as.integer(new_df$duration_years)
  db <- bind_rows(db, new_df)
  cat(sprintf("  Added %d new entries (total: %d)\n", nrow(new_df), nrow(db)))
}

write_csv(db, file.path(final_dir, "polities_database.csv"))
cat(sprintf("  Saved: polities_database.csv (%d rows)\n", nrow(db)))

polys <- polys[!duplicated(polys$polity_code, fromLast = TRUE), ]
if (file.exists(poly_path)) file.remove(poly_path)
st_write(polys, poly_path, layer = "polities", quiet = TRUE)
cat(sprintf("  Saved: polities_polygons.gpkg (%d polygons)\n", nrow(polys)))

cat(sprintf("\nTotal changes: %d\n", changes))
cat("\n=== Done ===\n")
cat("Deferred: USA (continuous expansion, 10x), Russia (gradual expansion, 1.4x)\n")
cat("Next: Run R/15, R/07 to rebuild\n")
