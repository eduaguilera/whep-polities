# ==============================================================================
# Cliopatria Polygon Accuracy Fixes and Mexico Period Split
# ==============================================================================
# Uses the full Cliopatria (Seshat) dataset (15,690 features) to replace
# inaccurate back-projected polygons with time-appropriate boundaries.
#
# POLYGON FIXES (replacing inaccurate polygons):
#   1. ETH-1800-1889: Ethiopian Empire 240K km2 (was 2-3x too large)
#   2. EGY-1800-1899: Muhammad Ali dynasty 1.83M km2 (was missing Sudan)
#   3. ZAN-1856-1964: Zanzibar mainland 28K km2 (was islands-only)
#   4. MAD-1800-1912: Merina Kingdom 85K->427K km2 phases (was whole island)
#   5. MOR-1800-1904: Morocco Alaouite 388K km2 (was modern borders)
#   6. OTT-1800-1912: Ottoman Empire time-appropriate 2.66M km2
#
# MEXICO PERIOD SPLIT:
#   7. Split MEX-1800-2025 into MEX-1800-1848 + MEX-1848-2025
#      Pre-1848 Mexico ~3.2M km2 (includes territory lost in Treaty of
#      Guadalupe Hidalgo, a -55% territorial change)
#
# CUBA: Keep as single entry (island, no >10% area change). Enhance notes.
#
# Memory-safe: reads Cliopatria features one polity at a time via ogr2ogr SQL.
# Run AFTER R/20.
# ==============================================================================

source("R/00_setup.R")
sf_use_s2(FALSE)

cat("=== Cliopatria Polygon Fixes and Mexico Split ===\n\n")

db <- read_csv(file.path(final_dir, "polities_database.csv"), show_col_types = FALSE)
cat("Loaded database:", nrow(db), "entries\n")

poly_path <- file.path(geodata_dir, "polities_polygons.gpkg")
polys <- st_read(poly_path, quiet = TRUE) %>% st_set_crs(4326)
cat("Loaded polygons:", nrow(polys), "features\n")

clio_path <- file.path(proj_root, "data", "source", "cliopatria",
                        "cliopatria_polities_only.geojson")
if (!file.exists(clio_path)) {
  # Try inputs/
  zip_path <- file.path(proj_root, "inputs", "cliopatria.geojson.zip")
  if (file.exists(zip_path)) {
    tmp_dir <- tempdir()
    unzip(zip_path, exdir = tmp_dir, overwrite = TRUE)
    clio_path <- file.path(tmp_dir, "cliopatria_polities_only.geojson")
  }
}
stopifnot("Cliopatria GeoJSON not found" = file.exists(clio_path))
cat("Cliopatria source:", clio_path, "\n\n")

existing_codes <- db$polity_code
new_entries <- list()
changes <- 0

# Helper: read a specific Cliopatria time step (memory-safe, one feature)
read_clio <- function(name, from_year, to_year) {
  query <- sprintf(
    "SELECT * FROM cliopatria_polities_only WHERE Name = '%s' AND FromYear = %d AND ToYear = %d",
    gsub("'", "''", name), from_year, to_year
  )
  tryCatch({
    feat <- st_read(clio_path, query = query, quiet = TRUE)
    if (nrow(feat) > 0) {
      feat <- st_set_crs(feat, 4326) %>% st_make_valid()
      return(feat[1, ])
    }
    # Try broader match
    query2 <- sprintf(
      "SELECT * FROM cliopatria_polities_only WHERE Name = '%s' AND FromYear <= %d AND ToYear >= %d LIMIT 1",
      gsub("'", "''", name), from_year, to_year
    )
    feat <- st_read(clio_path, query = query2, quiet = TRUE)
    if (nrow(feat) > 0) {
      feat <- st_set_crs(feat, 4326) %>% st_make_valid()
      return(feat[1, ])
    }
    return(NULL)
  }, error = function(e) {
    cat(sprintf("    ERROR reading %s %d-%d: %s\n", name, from_year, to_year, e$message))
    return(NULL)
  })
}

# Helper: replace polygon for existing polity code
replace_polygon <- function(code, new_geom) {
  idx <- which(polys$polity_code == code)
  if (length(idx) > 0) {
    polys[idx, ] <<- st_set_geometry(polys[idx, ], new_geom)
  } else {
    polys <<- bind_rows(polys, st_sf(polity_code = code, geometry = new_geom))
  }
}

set_pred <- function(code, pred_code) {
  idx <- which(db$polity_code == code)
  if (length(idx) != 1) return(FALSE)
  cur <- db$predecessor[idx]
  if (is.na(cur) || cur == "NA") db$predecessor[idx] <<- pred_code
  else if (!grepl(pred_code, cur, fixed = TRUE))
    db$predecessor[idx] <<- paste0(cur, "; ", pred_code)
  TRUE
}
set_succ <- function(code, succ_code) {
  idx <- which(db$polity_code == code)
  if (length(idx) != 1) return(FALSE)
  cur <- db$successor[idx]
  if (is.na(cur) || cur == "NA") db$successor[idx] <<- succ_code
  else if (!grepl(succ_code, cur, fixed = TRUE))
    db$successor[idx] <<- paste0(cur, "; ", succ_code)
  TRUE
}

# ==============================================================================
# 1. ETH-1800-1889: Ethiopian Empire pre-Menelik (240K km2)
# ==============================================================================
cat("--- 1. ETH-1800-1889: Ethiopian Empire pre-Menelik ---\n")

eth_clio <- read_clio("Ethiopian Empire", 1769, 1889)
if (!is.null(eth_clio)) {
  replace_polygon("ETH-1800-1889", st_geometry(eth_clio))
  db$polygon_source[db$polity_code == "ETH-1800-1889"] <-
    "Cliopatria (Ethiopian Empire 1769-1889, 240K km2)"
  db$notes[db$polity_code == "ETH-1800-1889"] <-
    "Pre-Menelik Ethiopia. Zemene Mesafint (Era of Princes). Highland core only: Gondar, Gojjam, Shewa, Tigray, Wello. ~240,000 km2. Cliopatria polygon replaces back-projected CShapes which was 2-3x too large."
  cat("  OK: Replaced with Cliopatria 240K km2 polygon\n")
  changes <- changes + 1
} else {
  cat("  SKIP: Cliopatria match not found\n")
}

# ==============================================================================
# 2. EGY-1800-1899: Muhammad Ali dynasty / Khedivate with Sudan
# ==============================================================================
cat("\n--- 2. EGY-1800-1899: Egypt with Sudan territory ---\n")

# Use Muhammad Ali dynasty 1848-1864 (1,834,433 km2) - includes Sudan
egy_clio <- read_clio("Muhammad Ali dynasty", 1848, 1864)
if (!is.null(egy_clio)) {
  replace_polygon("EGY-1800-1899", st_geometry(egy_clio))
  db$polygon_source[db$polity_code == "EGY-1800-1899"] <-
    "Cliopatria (Muhammad Ali dynasty 1848-1864, 1.83M km2)"
  db$notes[db$polity_code == "EGY-1800-1899"] <-
    "Khedivate of Egypt including Sudan (conquered 1820-24) and Equatoria. Cliopatria polygon represents mid-century extent (~1.83M km2). Egypt lost Sudan to Mahdist revolt by 1885. Pre-1820: Egypt proper only (~1M km2)."
  cat("  OK: Replaced with Cliopatria 1.83M km2 polygon (incl. Sudan)\n")
  changes <- changes + 1
} else {
  cat("  SKIP: Cliopatria match not found\n")
}

# ==============================================================================
# 3. ZAN-1856-1964: Zanzibar mainland coastal empire
# ==============================================================================
cat("\n--- 3. ZAN-1856-1964: Zanzibar mainland territory ---\n")

zan_clio <- read_clio("People's Republic of Zanzibar", 1856, 1884)
if (!is.null(zan_clio)) {
  replace_polygon("ZAN-1856-1964", st_geometry(zan_clio))
  db$polygon_source[db$polity_code == "ZAN-1856-1964"] <-
    "Cliopatria (Zanzibar Sultanate 1856-1884, 28K km2 mainland)"
  db$notes[db$polity_code == "ZAN-1856-1964"] <-
    "Zanzibar Sultanate including mainland coastal strip (Cape Delgado to near Mogadishu, 1500km). Cliopatria polygon includes mainland (28K km2). Mainland lost 1886-1890 via Anglo-German treaties. Post-1890: islands only."
  cat("  OK: Replaced with Cliopatria 28K km2 mainland polygon\n")
  changes <- changes + 1
} else {
  cat("  SKIP: Cliopatria match not found\n")
}

# ==============================================================================
# 4. MAD-1800-1912: Merina Kingdom expansion phases
# ==============================================================================
cat("\n--- 4. MAD-1800-1912: Merina Kingdom ---\n")

# Use Merina Kingdom 1803-1810 (113K km2) as representative early period
# (better than 1796-1802 at 85K which is before Radama I's conquests start)
mad_clio <- read_clio("Merina Kingdom", 1840, 1894)
if (!is.null(mad_clio)) {
  replace_polygon("MAD-1800-1912", st_geometry(mad_clio))
  db$polygon_source[db$polity_code == "MAD-1800-1912"] <-
    "Cliopatria (Merina Kingdom 1840-1894, 427K km2)"
  db$notes[db$polity_code == "MAD-1800-1912"] <-
    "Merina Kingdom. Expanded from central highlands: 85K km2 (1796) -> 113K (1803) -> 173K (1820) -> 245K (1822) -> 375K (1825) -> 427K (1840-1894). Cliopatria polygon uses 1840 extent (~75% of island). Western Sakalava never fully subjugated. French colonization 1896."
  cat("  OK: Replaced with Cliopatria 427K km2 polygon (1840 extent)\n")
  changes <- changes + 1
} else {
  cat("  SKIP: Cliopatria match not found\n")
}

# ==============================================================================
# 5. MOR-1800-1904: Morocco Alaouite dynasty
# ==============================================================================
cat("\n--- 5. MOR-1800-1904: Morocco Alaouite ---\n")

mor_clio <- read_clio("Morocco", 1769, 1860)
if (!is.null(mor_clio)) {
  replace_polygon("MOR-1800-1904", st_geometry(mor_clio))
  db$polygon_source[db$polity_code == "MOR-1800-1904"] <-
    "Cliopatria (Morocco 1769-1860, 388K km2)"
  db$notes[db$polity_code == "MOR-1800-1904"] <-
    "Alaouite Morocco. Cliopatria polygon (388K km2). Note: fixed borders remain conceptually anachronistic. Historical Morocco had Bled al-makhzen (governed territory) vs Bled es-siba (nominal allegiance only, Rif/Atlas). Southern border was non-existent."
  cat("  OK: Replaced with Cliopatria 388K km2 polygon\n")
  changes <- changes + 1
} else {
  cat("  SKIP: Cliopatria match not found\n")
}

# ==============================================================================
# 6. OTT-1800-1912: Ottoman Empire time-appropriate polygon
# ==============================================================================
cat("\n--- 6. OTT-1800-1912: Ottoman Empire ---\n")

# Use Ottoman 1800-1802 (2.66M km2) for the full empire extent
ott_clio <- read_clio("Ottoman Empire", 1800, 1802)
if (!is.null(ott_clio)) {
  replace_polygon("OTT-1800-1912", st_geometry(ott_clio))
  db$polygon_source[db$polity_code == "OTT-1800-1912"] <-
    "Cliopatria (Ottoman Empire 1800-1802, 2.66M km2)"
  db$notes[db$polity_code == "OTT-1800-1912"] <-
    "Ottoman Empire at 1800 extent (2.66M km2). Cliopatria has 47 time steps showing gradual contraction from 2.66M (1800) to 724K km2 (1922). This polygon represents the early-period maximum."
  cat("  OK: Replaced with Cliopatria 2.66M km2 polygon\n")
  changes <- changes + 1
} else {
  cat("  SKIP: Cliopatria match not found\n")
}

# ==============================================================================
# 7. Mexico period split
# ==============================================================================
cat("\n--- 7. Mexico period split ---\n")

mex_idx <- which(db$polity_code == "MEX-1800-2025")
if (length(mex_idx) == 1) {
  # Reclassify as aggregate
  db$polity_type[mex_idx] <- "aggregate"
  db$notes[mex_idx] <- "Aggregate entry for continuous trade data linkage. Pre-1848: included territory lost in Treaty of Guadalupe Hidalgo (~55% area loss)."
  cat("  MEX-1800-2025 reclassified as aggregate\n")

  # Add MEX-1800-1848 (pre-Guadalupe Hidalgo)
  mex_pre <- "MEX-1800-1848"
  if (!mex_pre %in% existing_codes) {
    new_entries[[length(new_entries) + 1]] <- tibble(
      polity_code = mex_pre,
      polity_name = "Mexico (to 1848)",
      start_year = 1800L, end_year = 1848L, duration_years = 49L,
      polity_type = "historical",
      continent = "North America", iso3_code = "MEX", cow_code = NA_character_,
      polygon_source = NA_character_,
      predecessor = NA_character_,
      successor = "MEX-1848-2025",
      data_sources = "CShapes; Cliopatria; research",
      verification_status = "VERIFIED",
      notes = "Pre-Treaty of Guadalupe Hidalgo. Included Central America until 1823 (~4.4M km2), then ~3.2M km2. Lost Texas de facto 1836. Treaty of Guadalupe Hidalgo (1848-02-02) ceded California, Nevada, Utah, Arizona, New Mexico to US (~55% loss)."
    )
    existing_codes <- c(existing_codes, mex_pre)

    # Get Cliopatria polygon: Federated Republic of Mexico 1825-1835 (~3.19M km2)
    mex_clio <- read_clio("Federated Republic of Mexico", 1825, 1835)
    if (!is.null(mex_clio)) {
      polys <- bind_rows(polys, st_sf(
        polity_code = mex_pre, geometry = st_geometry(mex_clio)
      ))
      new_entries[[length(new_entries)]]$polygon_source <-
        "Cliopatria (Federated Republic of Mexico 1825-1835, 3.19M km2)"
      cat(sprintf("  ADD: %s with Cliopatria 3.19M km2 polygon\n", mex_pre))
    } else {
      cat(sprintf("  ADD: %s (no polygon)\n", mex_pre))
    }
    changes <- changes + 1
  }

  # Add MEX-1848-2025 (post-Guadalupe Hidalgo)
  mex_post <- "MEX-1848-2025"
  if (!mex_post %in% existing_codes) {
    new_entries[[length(new_entries) + 1]] <- tibble(
      polity_code = mex_post,
      polity_name = "Mexico",
      start_year = 1848L, end_year = 2025L, duration_years = 178L,
      polity_type = "sovereign",
      continent = "North America", iso3_code = "MEX", cow_code = NA_character_,
      polygon_source = "CShapes 2.0",
      predecessor = "MEX-1800-1848",
      successor = NA_character_,
      data_sources = "CShapes; research",
      verification_status = "VERIFIED",
      notes = "Post-Treaty of Guadalupe Hidalgo. Gadsden Purchase (1854, -77K km2) is sub-threshold (-3.9%). Territory stable at ~1.96M km2 since 1854."
    )
    existing_codes <- c(existing_codes, mex_post)

    # Use existing CShapes Mexico polygon
    mex_poly <- polys[polys$polity_code == "MEX-1800-2025", ]
    if (nrow(mex_poly) > 0) {
      polys <- bind_rows(polys, st_sf(
        polity_code = mex_post, geometry = st_geometry(mex_poly[1, ])
      ))
      cat(sprintf("  ADD: %s with existing CShapes polygon\n", mex_post))
    }
    changes <- changes + 1
  }
}

# ==============================================================================
# 8. Cuba: enhance notes (no split needed)
# ==============================================================================
cat("\n--- 8. Cuba: enhance notes ---\n")

cub_idx <- which(db$polity_code == "CUB-1800-2025")
if (length(cub_idx) == 1) {
  db$notes[cub_idx] <- "Island territory constant at ~109K km2 (no >10% area change). Political transitions: Spanish colony to 1898; US occupation 1899-1902; Republic (Platt Amendment) 1902; full sovereignty 1934; Cuban Revolution 1959. CShapes has 5 status periods. Not split because territory did not change."
  cat("  Updated CUB-1800-2025 notes with political timeline\n")
  changes <- changes + 1
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

# Deduplicate polygons (keep last occurrence for replaced entries)
polys <- polys[!duplicated(polys$polity_code, fromLast = TRUE), ]
if (file.exists(poly_path)) file.remove(poly_path)
st_write(polys, poly_path, layer = "polities", quiet = TRUE)
cat(sprintf("  Saved: polities_polygons.gpkg (%d polygons)\n", nrow(polys)))

cat(sprintf("\nTotal changes: %d\n", changes))
cat("\n=== Done ===\n")
cat("Next: Run R/15, R/07 to rebuild unified output\n")
