# ==============================================================================
# USA and Russia Territorial Period Splits
# ==============================================================================
# USA: 4-period split (10x expansion 1800-1867)
#   USA-1800-1803  Original states + territories (~1.2M km2)
#   USA-1803-1848  Louisiana Purchase era (~3.0M km2 by 1845)
#   USA-1848-1867  Mexican Cession to pre-Alaska (~4.3M km2)
#   USA-1867-1959  Alaska onward (~9.4M km2, stable)
#   USA-1800-1959  reclassified as aggregate
#
# Russia: 2-period split (37% expansion)
#   F228-1800-1856  Pre-Crimean War Russian Empire (~17.6M km2)
#   F228-1856-1905  Post-Crimean + Central Asian expansion (~22M km2)
#   F228-1800-1905  reclassified as aggregate
#
# Polygons from Cliopatria time-stepped data (memory-safe SQL queries).
# ==============================================================================

source("R/00_setup.R")
sf_use_s2(FALSE)

cat("=== USA and Russia Territorial Splits ===\n\n")

db <- read_csv(file.path(final_dir, "polities_database.csv"), show_col_types = FALSE)
cat("Loaded database:", nrow(db), "entries\n")

poly_path <- file.path(geodata_dir, "polities_polygons.gpkg")
polys <- st_read(poly_path, quiet = TRUE) %>% st_set_crs(4326)

clio_path <- file.path(proj_root, "data", "source", "cliopatria",
                        "cliopatria_polities_only.geojson")
if (!file.exists(clio_path)) {
  tmp_dir <- tempdir()
  unzip(file.path(proj_root, "inputs", "cliopatria.geojson.zip"),
        exdir = tmp_dir, overwrite = TRUE)
  clio_path <- file.path(tmp_dir, "cliopatria_polities_only.geojson")
}

existing_codes <- db$polity_code
new_entries <- list()
changes <- 0

read_clio <- function(name, from_year, to_year) {
  query <- sprintf(
    "SELECT * FROM cliopatria_polities_only WHERE Name = '%s' AND FromYear <= %d AND ToYear >= %d LIMIT 1",
    gsub("'", "''", name), from_year, to_year)
  tryCatch({
    feat <- st_read(clio_path, query = query, quiet = TRUE)
    if (nrow(feat) > 0) return(st_set_crs(feat[1, ], 4326) %>% st_make_valid())
    NULL
  }, error = function(e) { cat(sprintf("    ERROR: %s\n", e$message)); NULL })
}

add_entry <- function(code, name, start, end, type, continent, iso3, polygon_src,
                       pred, succ, notes, clio_name, clio_yr) {
  if (code %in% existing_codes) { cat(sprintf("  SKIP: %s exists\n", code)); return() }

  new_entries[[length(new_entries) + 1]] <<- tibble(
    polity_code = code, polity_name = name,
    start_year = as.integer(start), end_year = as.integer(end),
    duration_years = as.integer(end - start + 1),
    polity_type = type, continent = continent, iso3_code = iso3,
    cow_code = NA_character_, polygon_source = polygon_src,
    predecessor = ifelse(is.null(pred), NA_character_, pred),
    successor = ifelse(is.null(succ), NA_character_, succ),
    data_sources = "CShapes; Cliopatria; research",
    verification_status = "VERIFIED", notes = notes
  )
  existing_codes <<- c(existing_codes, code)

  if (!is.null(clio_name)) {
    feat <- read_clio(clio_name, clio_yr[1], clio_yr[2])
    if (!is.null(feat)) {
      polys <<- bind_rows(polys, st_sf(polity_code = code, geometry = st_geometry(feat)))
      new_entries[[length(new_entries)]]$polygon_source <<-
        sprintf("Cliopatria (%s %d-%d)", clio_name, clio_yr[1], clio_yr[2])
      cat(sprintf("  ADD: %s with Cliopatria polygon\n", code))
    } else {
      cat(sprintf("  ADD: %s (no Cliopatria match)\n", code))
    }
  } else {
    cat(sprintf("  ADD: %s\n", code))
  }
  changes <<- changes + 1
}

# ==============================================================================
# PART 1: USA 4-period split
# ==============================================================================

cat("--- PART 1: USA territorial splits ---\n")

# Reclassify USA-1800-1959 as aggregate
usa_idx <- which(db$polity_code == "USA-1800-1959")
if (length(usa_idx) == 1) {
  db$polity_type[usa_idx] <- "national"
  db$notes[usa_idx] <- "Aggregate for continuous trade data linkage. Split into 4 territorial periods."
  cat("  USA-1800-1959 reclassified as aggregate\n")
  changes <- changes + 1
}

# Period 1: Original states (1800-1803)
add_entry("USA-1800-1803", "United States (original)", 1800, 1803,
  "national", "North America", "USA",
  NA_character_, NULL, "USA-1803-1848",
  "Original 13 states + early territories (Ohio, Kentucky, Tennessee, Vermont). ~1.2M km2. Louisiana Purchase (1803) doubles territory.",
  "United States of America", c(1800, 1802))

# Period 2: Louisiana Purchase era (1803-1848)
add_entry("USA-1803-1848", "United States (1803-1848)", 1803, 1848,
  "national", "North America", "USA",
  NA_character_, "USA-1800-1803", "USA-1848-1867",
  "Post-Louisiana Purchase (1803, +2.1M km2). Florida (Adams-Onis 1819). Texas annexation (1845). Oregon Treaty (1846). ~3.5M km2 by 1845. Treaty of Guadalupe Hidalgo (1848) triggers next split.",
  "United States of America", c(1842, 1845))

# Period 3: Mexican Cession to pre-Alaska (1848-1867)
add_entry("USA-1848-1867", "United States (1848-1867)", 1848, 1867,
  "national", "North America", "USA",
  NA_character_, "USA-1803-1848", "USA-1867-1959",
  "Post-Mexican Cession (Guadalupe Hidalgo 1848, +1.4M km2). Gadsden Purchase (1854). Civil War (1861-1865). ~4.3M km2 pre-Alaska. Alaska Purchase (1867) triggers next split.",
  "United States of America", c(1859, 1860))

# Period 4: Alaska onward (1867-1959)
add_entry("USA-1867-1959", "United States (1867-1959)", 1867, 1959,
  "national", "North America", "USA",
  NA_character_, "USA-1848-1867", "USA-1959-2025",
  "Alaska Purchase (1867, +1.7M km2). Territory stable at ~9.4M km2. Hawaii Territory (1898). Admitted as 49th and 50th states 1959.",
  "United States of America", c(1877, 1879))

# Link to existing USA-1959-2025
set_pred_idx <- which(db$polity_code == "USA-1959-2025")
if (length(set_pred_idx) == 1 && (is.na(db$predecessor[set_pred_idx]) || db$predecessor[set_pred_idx] == "NA")) {
  db$predecessor[set_pred_idx] <- "USA-1867-1959"
}

# Update subnational parent references: keep pointing to USA-1800-2025 aggregate

# ==============================================================================
# PART 2: Russia 2-period split
# ==============================================================================

cat("\n--- PART 2: Russia territorial splits ---\n")

# Reclassify F228-1800-1905 as aggregate
rus_idx <- which(db$polity_code == "F228-1800-1905")
if (length(rus_idx) == 1) {
  db$polity_type[rus_idx] <- "national"
  db$notes[rus_idx] <- "Aggregate for continuous trade data linkage. Split into 2 territorial periods at Crimean War."
  cat("  F228-1800-1905 reclassified as aggregate\n")
  changes <- changes + 1
}

# Period 1: Pre-Crimean War (1800-1856)
add_entry("F228-1800-1856", "Russian Empire (to 1856)", 1800, 1856,
  "national", "Europe", "RUS",
  NA_character_, NULL, "F228-1856-1905",
  "Russian Empire pre-Crimean War. ~17.4M km2. Acquisitions: Georgia (1801), Finland (1809), Bessarabia (1812), Congress Poland (1815). Caucasus conquest ongoing. Crimean War (1853-56) ends this period.",
  "Russian Empire", c(1815, 1823))

# Period 2: Post-Crimean + Central Asian expansion (1856-1905)
add_entry("F228-1856-1905", "Russian Empire (1856-1905)", 1856, 1905,
  "national", "Europe", "RUS",
  NA_character_, "F228-1800-1856", "F228-1905-1914",
  "Russian Empire post-Crimean War. Massive Central Asian expansion: Tashkent (1865), Bukhara protectorate (1868), Khiva (1873), Kokand (1876), Merv (1884). Far East: Amur/Ussuri (1858-60), Sakhalin (1875). ~22M km2 by 1900. Russo-Japanese War (1904-05) triggers next period.",
  "Russian Empire", c(1885, 1894))

# Link to existing F228-1905-1914
f228_next <- which(db$polity_code == "F228-1905-1914")
if (length(f228_next) == 1 && (is.na(db$predecessor[f228_next]) || db$predecessor[f228_next] == "NA")) {
  db$predecessor[f228_next] <- "F228-1856-1905"
}

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
