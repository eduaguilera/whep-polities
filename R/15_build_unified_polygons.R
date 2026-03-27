# ==============================================================================
# Build Unified Polities GeoPackage
# ==============================================================================
# Merges ALL polygon sources into a single SF object joined with the polities
# database CSV. Produces data/final/polities_database.gpkg — one file with
# every polity row, geometry attached where available.
#
# Polygon sources (in priority order):
#   1. precolonial_polygons.gpkg      (46 Paine et al. pre-colonial kingdoms)
#   2. cliopatria_polygons.gpkg       (4 Seshat/Cliopatria polities)
#   3. chgis_qing_provinces.gpkg      (26 Qing China provinces)
#   4. us_historical_states.gpkg      (51 US states/territories 1800-1958)
#   5. brazil_historical_states.gpkg  (26 Brazil states 1872-1987)
#   6. spain_provinces.gpkg           (52 Spain provinces 1833-2025)
#   7. polities_polygons.gpkg         (939 main build: CShapes + GADM admin-1)
#   8. CShapes recovery               (missing polities recovered from raw CShapes)
#   9. GADM recovery                   (missing polities recovered from GADM 3.6)
#
# Output: data/final/polities_database.gpkg
# ==============================================================================

source("R/00_setup.R")

# ==============================================================================
# 1. Load polities database
# ==============================================================================

cat("=== Building Unified Polities GeoPackage ===\n\n")

db <- read_csv(file.path(final_dir, "polities_database.csv"), show_col_types = FALSE)
cat("Loaded polities database:", nrow(db), "entries\n")
cat("  Non-region:", sum(db$polity_type != "region"), "\n")
cat("  Regions:", sum(db$polity_type == "region"), "\n\n")

# ==============================================================================
# 2. Load all existing polygon sources
# ==============================================================================

cat("--- Loading polygon sources ---\n")

load_gpkg <- function(filename, label) {
  path <- file.path(geodata_dir, filename)
  if (!file.exists(path)) {
    cat(sprintf("  SKIP: %s (file not found)\n", filename))
    return(NULL)
  }
  sf <- st_read(path, quiet = TRUE)
  sf <- sf[, "polity_code"] # keep only polity_code + geometry
  # Standardize geometry column name to "geometry"
  sf <- st_set_geometry(sf, "geometry")
  sf <- st_set_crs(sf, 4326)
  cat(sprintf("  %s: %d polygons (%s)\n", label, nrow(sf), filename))
  sf
}

sources <- list(
  load_gpkg("precolonial_polygons.gpkg", "Pre-colonial"),
  load_gpkg("cliopatria_polygons.gpkg", "Cliopatria"),
  load_gpkg("chgis_qing_provinces.gpkg", "CHGIS Qing"),
  load_gpkg("us_historical_states.gpkg", "US historical"),
  load_gpkg("brazil_historical_states.gpkg", "Brazil historical"),
  load_gpkg("spain_provinces.gpkg", "Spain provinces"),
  load_gpkg("polities_polygons.gpkg", "Main build")
)

sources <- Filter(Negate(is.null), sources)

# Combine, keeping first occurrence (priority order above)
all_polys <- bind_rows(sources)
all_polys <- all_polys[!duplicated(all_polys$polity_code), ]
cat(sprintf("\nCombined: %d unique polygons from existing sources\n", nrow(all_polys)))

# ==============================================================================
# 3. Identify missing polities
# ==============================================================================

non_region <- db[db$polity_type != "region", ]
missing <- non_region[!non_region$polity_code %in% all_polys$polity_code, ]
cat(sprintf("Missing polygons: %d of %d non-region polities\n\n",
            nrow(missing), nrow(non_region)))

if (nrow(missing) > 0) {
  cat("Missing polities:\n")
  for (i in seq_len(nrow(missing))) {
    cat(sprintf("  %-25s %-15s %s\n",
                missing$polity_code[i],
                missing$polity_type[i],
                ifelse(is.na(missing$polygon_source[i]), "NA",
                       missing$polygon_source[i])))
  }
  cat("\n")
}

# ==============================================================================
# 4. Recover missing polygons from CShapes raw data
# ==============================================================================

cat("--- Attempting CShapes recovery ---\n")

cs_full <- st_read(file.path(geodata_dir, "cshapes2_full.gpkg"), quiet = TRUE) %>%
  st_set_crs(4326)
cat(sprintf("  CShapes full: %d rows\n", nrow(cs_full)))

# Build a lookup: for each missing polity with a COW code, find best CShapes match
recovered <- list()

for (i in seq_len(nrow(missing))) {
  pc <- missing$polity_code[i]
  cow <- missing$cow_code[i]
  src <- missing$polygon_source[i]
  sy <- missing$start_year[i]
  ey <- missing$end_year[i]
  pname <- missing$polity_name[i]

  # Skip non-CShapes sources
  if (is.na(src) || !grepl("CShapes", src)) next

  if (!is.na(cow)) {
    cow_num <- as.integer(cow)
    candidates <- cs_full[cs_full$cowcode == cow_num, ]
  } else {
    # Try matching by name fragments
    name_clean <- str_replace_all(pname, "\\s*\\(.*\\)\\s*", "")
    candidates <- cs_full[grepl(name_clean, cs_full$country_name, ignore.case = TRUE), ]

    if (nrow(candidates) == 0) {
      # Try first word
      first_word <- word(pname, 1)
      if (nchar(first_word) >= 4) {
        candidates <- cs_full[grepl(first_word, cs_full$country_name, ignore.case = TRUE), ]
      }
    }
  }

  if (nrow(candidates) == 0) {
    cat(sprintf("  MISS: %-25s no CShapes match\n", pc))
    next
  }

  # Pick the candidate whose date range best overlaps with the polity
  candidates$cs_start <- as.integer(format(candidates$start, "%Y"))
  candidates$cs_end <- as.integer(format(candidates$end, "%Y"))

  # Prefer: (1) overlap with polity period, (2) closest start date
  candidates$overlap <- pmax(0,
    pmin(candidates$cs_end, ey) - pmax(candidates$cs_start, sy))
  candidates$date_dist <- abs(candidates$cs_start - sy)

  best <- candidates[order(-candidates$overlap, candidates$date_dist), ][1, ]

  rec_sf <- st_sf(
    polity_code = pc,
    geometry = st_geometry(best)
  )
  rec_sf <- st_set_geometry(rec_sf, "geometry")
  recovered[[length(recovered) + 1]] <- rec_sf
  cat(sprintf("  OK:   %-25s ← CShapes cow=%s (%s to %s)\n",
              pc, best$cowcode,
              format(best$start, "%Y"), format(best$end, "%Y")))
}

if (length(recovered) > 0) {
  recovered_sf <- bind_rows(recovered) %>% st_set_crs(4326)
  cat(sprintf("\n  Recovered %d polities from CShapes\n\n", nrow(recovered_sf)))
  all_polys <- bind_rows(all_polys, recovered_sf)
} else {
  cat("\n  No recoveries from CShapes\n\n")
}

# ==============================================================================
# 5. Recover missing polygons from GADM
# ==============================================================================

cat("--- Attempting GADM recovery ---\n")

# Update missing list
missing2 <- non_region[!non_region$polity_code %in% all_polys$polity_code, ]

gadm_missing <- missing2[!is.na(missing2$polygon_source) &
                          grepl("GADM", missing2$polygon_source), ]

if (nrow(gadm_missing) > 0 && file.exists(gadm_path)) {
  gadm0 <- st_read(gadm_path, layer = "level0", quiet = TRUE) %>% st_set_crs(4326)
  cat(sprintf("  GADM level0: %d countries\n", nrow(gadm0)))

  # Manual mapping for special GADM cases
  gadm_map <- c(
    "DRO-1800-1982" = NA_character_,      # Dronning Maud Land — no GADM entry
    "NEU-1800-1982" = NA_character_,       # Neutral Zone — dissolved
    "F285-2011-2023" = NA_character_,      # Sark — part of Guernsey in GADM
    "JTN-1800-1982" = NA_character_,       # Johnston Island — tiny atoll
    "UNI-1800-1982" = NA_character_,       # US misc Pacific — scattered
    "MID-1859-1982" = NA_character_,       # Midway — tiny atoll
    "USS-1859-2025" = NA_character_,       # US settlement Oceania — no GADM
    "WAK-1898-1982" = NA_character_,       # Wake Island — tiny atoll
    "DAN-1800-1845" = NA_character_        # Danish India — tiny trading posts
  )

  for (i in seq_len(nrow(gadm_missing))) {
    pc <- gadm_missing$polity_code[i]
    iso <- gadm_missing$iso3_code[i]

    if (pc %in% names(gadm_map)) {
      if (is.na(gadm_map[pc])) {
        cat(sprintf("  SKIP: %-25s (no GADM equivalent)\n", pc))
        next
      }
      iso <- gadm_map[pc]
    }

    if (is.na(iso)) {
      cat(sprintf("  MISS: %-25s no ISO3 code\n", pc))
      next
    }

    gm <- gadm0[gadm0$GID_0 == iso, ]
    if (nrow(gm) > 0) {
      gadm_sf <- st_sf(
        polity_code = pc,
        geometry = st_geometry(gm[1, ])
      )
      gadm_sf <- st_set_geometry(gadm_sf, "geometry")
      gadm_sf <- st_set_crs(gadm_sf, 4326)
      all_polys <- bind_rows(all_polys, gadm_sf)
      cat(sprintf("  OK:   %-25s ← GADM %s\n", pc, iso))
    } else {
      cat(sprintf("  MISS: %-25s GADM has no %s\n", pc, iso))
    }
  }
} else if (nrow(gadm_missing) > 0) {
  cat("  GADM file not found at:", gadm_path, "\n")
} else {
  cat("  No GADM-sourced polities missing\n")
}

cat("\n")

# ==============================================================================
# 6. Final coverage report
# ==============================================================================

all_polys <- all_polys[!duplicated(all_polys$polity_code), ]

final_missing <- non_region[!non_region$polity_code %in% all_polys$polity_code, ]

cat(sprintf("=== Final Coverage ===\n"))
cat(sprintf("  Polygons available: %d / %d non-region polities (%.1f%%)\n",
            nrow(all_polys), nrow(non_region),
            100 * nrow(all_polys) / nrow(non_region)))
cat(sprintf("  Still missing: %d\n", nrow(final_missing)))

if (nrow(final_missing) > 0) {
  cat("\n  Remaining gaps:\n")
  for (i in seq_len(nrow(final_missing))) {
    cat(sprintf("    %-25s %-40s %s\n",
                final_missing$polity_code[i],
                final_missing$polity_name[i],
                ifelse(is.na(final_missing$polygon_source[i]), "no source",
                       final_missing$polygon_source[i])))
  }
}

# ==============================================================================
# 7. Build unified SF object
# ==============================================================================

cat("\n--- Building unified SF object ---\n")

# Make all polygon geometries valid
all_polys <- st_make_valid(all_polys)

# Left-join: database ← polygons (regions get empty geometry)
unified <- db %>%
  left_join(
    all_polys %>% select(polity_code),
    by = "polity_code"
  )

# Convert to sf — rows without polygon get EMPTY geometry
unified <- st_as_sf(unified)
unified <- st_set_crs(unified, 4326)

has_geom <- !st_is_empty(unified)
cat(sprintf("  Total rows: %d\n", nrow(unified)))
cat(sprintf("  With geometry: %d\n", sum(has_geom)))
cat(sprintf("  Empty geometry: %d (regions + missing)\n", sum(!has_geom)))

# ==============================================================================
# 8. Save unified GeoPackage
# ==============================================================================

out_path <- file.path(final_dir, "polities_database.gpkg")

if (file.exists(out_path)) file.remove(out_path)

st_write(unified, out_path, layer = "polities", quiet = TRUE)
cat(sprintf("\nSaved: %s\n", out_path))
cat(sprintf("  Size: %.1f MB\n", file.size(out_path) / 1e6))

# Quick verification
check <- st_read(out_path, quiet = TRUE)
cat(sprintf("  Verification: %d rows, %d columns\n", nrow(check), ncol(check)))
cat(sprintf("  Geometry types: %s\n",
            paste(unique(st_geometry_type(check)), collapse = ", ")))

cat("\n=== Done ===\n")
cat("Load in R with:\n")
cat('  library(sf)\n')
cat('  polities <- st_read("data/final/polities_database.gpkg")\n')
cat('  plot(polities[polities$polity_type == "sovereign" & polities$end_year == 2025, "continent"])\n')
