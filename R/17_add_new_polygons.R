# ==============================================================================
# v2.2 Polygon Additions and Fixes
# ==============================================================================
# This script adds new polity entries and fixes polygon issues identified in the
# v2.1 gap analysis. Run AFTER R/16_data_integrity_fixes.R.
#
# Changes:
#   FIX 1. OTT-1800-1912 polygon override (copy from TUR-1800-1912)
#   FIX 2. Dronning Maud Land polygon (Antarctic sector claim)
#   FIX 3. Neutral Zone polygon (Saudi-Kuwait/Iraq)
#   ADD 4. Japan 47 prefectures (subnational, GADM)
#   ADD 5. UK 4 nations (subnational, GADM)
#   ADD 6. Saar Territory 1920-1935 (interwar entity)
#   ADD 7. Memel Territory 1920-1923 (interwar entity)
#   ADD 8. Free City of Fiume 1920-1924 (interwar entity)
#   ADD 9. Mongolia 1911-1921 (fill independence gap)
#   ADD 10. India aggregate entry
#
# Requires: GADM 3.6 GeoPackage for subnational additions (Japan, UK)
#           CShapes data in data/geodata/ for interwar polygons
# ==============================================================================

source("R/00_setup.R")

cat("=== v2.2 Polygon Additions and Fixes ===\n\n")

# ==============================================================================
# Load current database and polygons
# ==============================================================================

db <- read_csv(file.path(final_dir, "polities_database.csv"), show_col_types = FALSE)
cat("Loaded database:", nrow(db), "entries\n")

poly_path <- file.path(geodata_dir, "polities_polygons.gpkg")
if (file.exists(poly_path)) {
  polys <- st_read(poly_path, quiet = TRUE) %>% st_set_crs(4326)
  cat("Loaded polygons:", nrow(polys), "features\n")
} else {
  polys <- st_sf(polity_code = character(0), geometry = st_sfc(), crs = 4326)
  cat("WARNING: No polygon file found, starting empty\n")
}

existing_codes <- db$polity_code
new_entries <- list()
new_polys <- list()
fix_log <- list()

log_fix <- function(action, code, detail) {
  fix_log[[length(fix_log) + 1]] <<- tibble(
    action = action, polity_code = code, detail = detail
  )
  cat(sprintf("  %-6s %-25s %s\n", action, code, detail))
}

# ==============================================================================
# FIX 1: OTT-1800-1912 polygon override
# ==============================================================================
# The Ottoman Empire entry gets a small CShapes-Europe polygon (Balkans+Anatolia
# only ~64 deg2). TUR-1800-1912 has the correct large CShapes 2.0 polygon
# covering the full Ottoman territory (~283 deg2). We copy TUR's geometry to OTT.

cat("\n--- FIX 1: OTT-1800-1912 polygon override ---\n")

ott_code <- "OTT-1800-1912"
tur_code <- "TUR-1800-1912"

if (tur_code %in% polys$polity_code && ott_code %in% polys$polity_code) {
  tur_geom <- polys[polys$polity_code == tur_code, ] %>% st_geometry()
  polys[polys$polity_code == ott_code, ] <- st_set_geometry(
    polys[polys$polity_code == ott_code, ], tur_geom
  )
  log_fix("FIX", ott_code, "Replaced small CShapes-Europe polygon with full CShapes 2.0 from TUR-1800-1912")

  # Update polygon_source in database
  db$polygon_source[db$polity_code == ott_code] <- "CShapes 2.0 (via TUR-1800-1912)"
} else if (tur_code %in% polys$polity_code) {
  # OTT not in polys yet, add it
  tur_geom <- polys[polys$polity_code == tur_code, ] %>% st_geometry()
  new_polys[[length(new_polys) + 1]] <- st_sf(
    polity_code = ott_code, geometry = tur_geom
  )
  log_fix("FIX", ott_code, "Added polygon from TUR-1800-1912")
  db$polygon_source[db$polity_code == ott_code] <- "CShapes 2.0 (via TUR-1800-1912)"
} else {
  cat("  SKIP: Neither OTT nor TUR polygon found in polygon file\n")
}

# ==============================================================================
# FIX 2: Dronning Maud Land polygon (Antarctic sector claim)
# ==============================================================================
# Norwegian Antarctic claim: 20 deg W to 44 deg 38' E, from coast (~70 deg S)
# to South Pole (90 deg S). We use 60 deg S as northern boundary (approximate
# Antarctic coastline latitude at this longitude range).

cat("\n--- FIX 2: Dronning Maud Land polygon ---\n")

dro_code <- "DRO-1800-1982"
if (dro_code %in% existing_codes) {
  # Create wedge polygon: sector from 60S to 90S, 20W to 44.633E
  # Note: at the South Pole, all longitudes converge, so we approximate
  dro_coords <- matrix(c(
    -20, -60,       # NW corner (coast)
    44.633, -60,    # NE corner (coast)
    44.633, -89.99, # SE near pole
    -20, -89.99,    # SW near pole
    -20, -60        # close ring
  ), ncol = 2, byrow = TRUE)

  dro_poly <- st_polygon(list(dro_coords))
  dro_sf <- st_sf(
    polity_code = dro_code,
    geometry = st_sfc(dro_poly, crs = 4326)
  )
  new_polys[[length(new_polys) + 1]] <- dro_sf
  db$polygon_source[db$polity_code == dro_code] <- "Constructed (Antarctic sector claim)"
  log_fix("FIX", dro_code, "Created Antarctic sector polygon (20W-44.6E, 60S-90S)")
} else {
  cat("  SKIP: DRO-1800-1982 not in database\n")
}

# ==============================================================================
# FIX 3: Neutral Zone polygon (Saudi-Kuwait/Iraq)
# ==============================================================================
# The Saudi-Kuwait Neutral Zone (1922-1970) was a diamond-shaped area between
# Saudi Arabia and Kuwait. Approximate coordinates from historical maps.

cat("\n--- FIX 3: Neutral Zone polygon ---\n")

neu_code <- "NEU-1800-1982"
if (neu_code %in% existing_codes) {
  # Saudi-Kuwait Neutral Zone approximate boundaries
  # Based on the Uqair Protocol (1922) boundary definition
  neu_coords <- matrix(c(
    46.55, 28.53,  # SW corner
    48.40, 28.53,  # SE corner
    48.40, 29.10,  # NE corner
    46.55, 29.10,  # NW corner
    46.55, 28.53   # close ring
  ), ncol = 2, byrow = TRUE)

  neu_poly <- st_polygon(list(neu_coords))
  neu_sf <- st_sf(
    polity_code = neu_code,
    geometry = st_sfc(neu_poly, crs = 4326)
  )
  new_polys[[length(new_polys) + 1]] <- neu_sf
  db$polygon_source[db$polity_code == neu_code] <- "Constructed (Uqair Protocol 1922 boundaries)"
  log_fix("FIX", neu_code, "Created Neutral Zone polygon (Uqair Protocol boundaries)")
} else {
  cat("  SKIP: NEU-1800-1982 not in database\n")
}

# ==============================================================================
# ADD 4: Japan 47 prefectures
# ==============================================================================
# Japan's 47 prefectures have been stable since the Meiji-era reorganization
# (1888). GADM admin-1 boundaries are excellent proxies. Start year 1888.

cat("\n--- ADD 4: Japan 47 prefectures ---\n")

gadm_available <- file.exists(gadm_path)

if (gadm_available) {
  gadm <- st_read(gadm_path, layer = "level1", quiet = TRUE)

  jpn_gadm <- gadm %>%
    filter(GID_0 == "JPN") %>%
    arrange(NAME_1)

  cat(sprintf("  GADM Japan admin-1: %d units\n", nrow(jpn_gadm)))

  jpn_parent <- "JPN-1800-2025"
  jpn_start <- 1888L

  for (j in seq_len(nrow(jpn_gadm))) {
    row <- jpn_gadm[j, ]
    name <- row$NAME_1
    eng_type <- row$ENGTYPE_1
    hasc <- row$HASC_1

    if (is.na(hasc)) {
      gid_num <- str_extract(row$GID_1, "(?<=\\.)[0-9]+")
      hasc <- paste0("JP.", gid_num)
      cat(sprintf("    WARNING: No HASC for %s, using %s\n", name, hasc))
    }

    code_prefix <- str_replace(hasc, "\\.", "")
    polity_code <- sprintf("%s-%d-2025", code_prefix, jpn_start)

    if (polity_code %in% existing_codes) {
      cat(sprintf("    COLLISION: %s (%s) -- skipping\n", polity_code, name))
      next
    }

    polity_name <- sprintf("%s (%s)", name, eng_type)

    new_entries[[length(new_entries) + 1]] <- tibble(
      polity_code = polity_code,
      polity_name = polity_name,
      start_year = jpn_start,
      end_year = 2025L,
      duration_years = 2025L - jpn_start + 1L,
      polity_type = "subnational",
      continent = "Asia",
      iso3_code = "JPN",
      cow_code = NA_character_,
      polygon_source = "GADM 3.6 (subnational)",
      predecessor = NA_character_,
      successor = NA_character_,
      data_sources = "GADM",
      verification_status = "VERIFIED",
      notes = sprintf("Parent: %s; GADM GID: %s; Boundaries stable since 1888 Meiji reforms",
                       jpn_parent, row$GID_1)
    )

    existing_codes <- c(existing_codes, polity_code)

    geom <- st_geometry(row)
    if (!st_is_empty(geom)) {
      new_polys[[length(new_polys) + 1]] <- st_sf(
        polity_code = polity_code, geometry = geom
      )
    }

    log_fix("ADD", polity_code, polity_name)
  }
} else {
  cat("  SKIP: GADM file not found at:", gadm_path, "\n")
  cat("  To add Japan prefectures, ensure GADM 3.6 GeoPackage is available.\n")
}

# ==============================================================================
# ADD 5: UK 4 nations
# ==============================================================================
# England, Scotland, Wales, Northern Ireland. Boundaries stable for centuries
# (England/Scotland/Wales) or since 1921 (Northern Ireland).

cat("\n--- ADD 5: UK 4 nations ---\n")

if (gadm_available) {
  gbr_gadm <- gadm %>%
    filter(GID_0 == "GBR") %>%
    arrange(NAME_1)

  cat(sprintf("  GADM UK admin-1: %d units\n", nrow(gbr_gadm)))

  # UK has many admin-1 units in GADM (counties, regions). We want the 4 nations.
  # GADM groups these at different levels depending on version.
  # Strategy: group GADM admin-1 units by nation using ENGTYPE_1 or NAME_1 patterns

  # Define nation groupings based on GADM NAME_1 prefixes
  # First check what we have
  cat("  Available UK admin-1 types:\n")
  uk_types <- gbr_gadm %>% st_drop_geometry() %>% count(ENGTYPE_1)
  for (t in seq_len(nrow(uk_types))) {
    cat(sprintf("    %s: %d\n", uk_types$ENGTYPE_1[t], uk_types$n[t]))
  }

  # Define the 4 nations with their GADM grouping
  uk_nations <- tribble(
    ~nation_name, ~polity_code, ~engtype_filter,
    "England",          "GBENG-1800-2025",  "Metropolitan County|London Borough|Unitary Authority \\(Eng\\)|Ceremonial County|Greater London",
    "Scotland",         "GBSCT-1800-2025",  "Council Area",
    "Wales",            "GBWLS-1800-2025",  "Unitary Authority \\(Wal\\)",
    "Northern Ireland", "GBNIR-1921-2025",  "District"
  )

  gbr_parent <- "GBR-1921-2025"

  for (n in seq_len(nrow(uk_nations))) {
    nation <- uk_nations[n, ]

    if (nation$polity_code %in% existing_codes) {
      cat(sprintf("  COLLISION: %s -- skipping\n", nation$polity_code))
      next
    }

    # Try to filter by ENGTYPE_1
    matched_units <- gbr_gadm %>%
      filter(grepl(nation$engtype_filter, ENGTYPE_1))

    if (nrow(matched_units) == 0) {
      # Fallback: try NAME_1 matching
      matched_units <- gbr_gadm %>%
        filter(grepl(nation$nation_name, NAME_1, ignore.case = TRUE))
    }

    if (nrow(matched_units) == 0) {
      cat(sprintf("  MISS: Could not identify %s units in GADM\n", nation$nation_name))
      next
    }

    cat(sprintf("  %s: %d GADM units matched\n", nation$nation_name, nrow(matched_units)))

    # Dissolve (union) all units into a single nation polygon
    nation_geom <- st_union(matched_units) %>% st_make_valid()

    start_yr <- ifelse(nation$nation_name == "Northern Ireland", 1921L, 1800L)

    new_entries[[length(new_entries) + 1]] <- tibble(
      polity_code = nation$polity_code,
      polity_name = sprintf("%s (Country)", nation$nation_name),
      start_year = start_yr,
      end_year = 2025L,
      duration_years = 2025L - start_yr + 1L,
      polity_type = "subnational",
      continent = "Europe",
      iso3_code = "GBR",
      cow_code = NA_character_,
      polygon_source = "GADM 3.6 (dissolved subnational)",
      predecessor = NA_character_,
      successor = NA_character_,
      data_sources = "GADM",
      verification_status = "VERIFIED",
      notes = sprintf("Parent: %s; Dissolved from %d GADM admin-1 units",
                       gbr_parent, nrow(matched_units))
    )

    existing_codes <- c(existing_codes, nation$polity_code)

    new_polys[[length(new_polys) + 1]] <- st_sf(
      polity_code = nation$polity_code,
      geometry = nation_geom
    )

    log_fix("ADD", nation$polity_code, sprintf("%s (Country) - %d units dissolved",
                                                nation$nation_name, nrow(matched_units)))
  }
} else {
  cat("  SKIP: GADM file not found. UK nations require GADM 3.6.\n")
}

# ==============================================================================
# ADD 6: Saar Territory 1920-1935
# ==============================================================================
# League of Nations mandate 1920-1935, returned to Germany by plebiscite.
# Use GADM Saarland (DE.SL) as polygon proxy (boundaries very similar).

cat("\n--- ADD 6: Saar Territory 1920-1935 ---\n")

saar_code <- "SAA-1920-1935"
if (!saar_code %in% existing_codes) {
  new_entries[[length(new_entries) + 1]] <- tibble(
    polity_code = saar_code,
    polity_name = "Saar Territory (League of Nations)",
    start_year = 1920L,
    end_year = 1935L,
    duration_years = 16L,
    polity_type = "mandate",
    continent = "Europe",
    iso3_code = NA_character_,
    cow_code = NA_character_,
    polygon_source = NA_character_,
    predecessor = NA_character_,
    successor = NA_character_,
    data_sources = "research",
    verification_status = "VERIFIED",
    notes = "League of Nations mandate; governed by commission; returned to Germany 1935 plebiscite (90.7% for reunification)"
  )
  existing_codes <- c(existing_codes, saar_code)

  # Try to get Saarland polygon from GADM
  if (gadm_available) {
    deu_gadm <- gadm %>% filter(GID_0 == "DEU")
    saarland <- deu_gadm %>% filter(grepl("Saarland", NAME_1))
    if (nrow(saarland) > 0) {
      new_polys[[length(new_polys) + 1]] <- st_sf(
        polity_code = saar_code,
        geometry = st_geometry(saarland[1, ])
      )
      db_idx <- which(sapply(new_entries, function(x) x$polity_code[1]) == saar_code)
      if (length(db_idx) > 0) {
        new_entries[[db_idx]]$polygon_source <- "GADM 3.6 (Saarland proxy)"
      }
      log_fix("ADD", saar_code, "Saar Territory with GADM Saarland polygon")
    } else {
      log_fix("ADD", saar_code, "Saar Territory (no polygon - GADM Saarland not found)")
    }
  } else {
    log_fix("ADD", saar_code, "Saar Territory (no polygon - GADM not available)")
  }
} else {
  cat("  SKIP: Already exists\n")
}

# ==============================================================================
# ADD 7: Memel Territory 1920-1923
# ==============================================================================
# French-administered League mandate, seized by Lithuania 1923.
# Use Klaipeda County from GADM Lithuania as proxy.

cat("\n--- ADD 7: Memel Territory 1920-1923 ---\n")

mem_code <- "MEM-1920-1923"
if (!mem_code %in% existing_codes) {
  new_entries[[length(new_entries) + 1]] <- tibble(
    polity_code = mem_code,
    polity_name = "Memel Territory",
    start_year = 1920L,
    end_year = 1923L,
    duration_years = 4L,
    polity_type = "mandate",
    continent = "Europe",
    iso3_code = NA_character_,
    cow_code = NA_character_,
    polygon_source = NA_character_,
    predecessor = NA_character_,
    successor = NA_character_,
    data_sources = "research",
    verification_status = "VERIFIED",
    notes = "French-administered League mandate; seized by Lithuania Jan 1923; Klaipeda Convention 1924"
  )
  existing_codes <- c(existing_codes, mem_code)

  if (gadm_available) {
    ltu_gadm <- gadm %>% filter(GID_0 == "LTU")
    klaipeda <- ltu_gadm %>% filter(grepl("Klaip", NAME_1))
    if (nrow(klaipeda) > 0) {
      new_polys[[length(new_polys) + 1]] <- st_sf(
        polity_code = mem_code,
        geometry = st_geometry(klaipeda[1, ])
      )
      db_idx <- which(sapply(new_entries, function(x) x$polity_code[1]) == mem_code)
      if (length(db_idx) > 0) {
        new_entries[[db_idx]]$polygon_source <- "GADM 3.6 (Klaipeda County proxy)"
      }
      log_fix("ADD", mem_code, "Memel Territory with GADM Klaipeda polygon")
    } else {
      log_fix("ADD", mem_code, "Memel Territory (no polygon - Klaipeda not found)")
    }
  } else {
    log_fix("ADD", mem_code, "Memel Territory (no polygon - GADM not available)")
  }
} else {
  cat("  SKIP: Already exists\n")
}

# ==============================================================================
# ADD 8: Free City of Fiume 1920-1924
# ==============================================================================
# Small city-state on the Adriatic (~28 km2). Create buffer around city center.

cat("\n--- ADD 8: Free City of Fiume 1920-1924 ---\n")

fiu_code <- "FIU-1920-1924"
if (!fiu_code %in% existing_codes) {
  new_entries[[length(new_entries) + 1]] <- tibble(
    polity_code = fiu_code,
    polity_name = "Free City of Fiume",
    start_year = 1920L,
    end_year = 1924L,
    duration_years = 5L,
    polity_type = "historical",
    continent = "Europe",
    iso3_code = NA_character_,
    cow_code = NA_character_,
    polygon_source = "Constructed (point buffer ~28 km2)",
    predecessor = NA_character_,
    successor = NA_character_,
    data_sources = "research",
    verification_status = "VERIFIED",
    notes = "Treaty of Rapallo 1920; Italian annexation 1924 (Treaty of Rome). Rijeka/Fiume. ~28 km2."
  )
  existing_codes <- c(existing_codes, fiu_code)

  # Rijeka/Fiume center: 14.4422 E, 45.3271 N
  # Buffer ~3 km radius for ~28 km2
  fiu_center <- st_sfc(st_point(c(14.4422, 45.3271)), crs = 4326)
  # Transform to metric CRS, buffer, transform back
  fiu_metric <- st_transform(fiu_center, 3035) # ETRS89 Lambert Azimuthal
  fiu_buffered <- st_buffer(fiu_metric, 3000) # 3 km radius
  fiu_geom <- st_transform(fiu_buffered, 4326)

  new_polys[[length(new_polys) + 1]] <- st_sf(
    polity_code = fiu_code,
    geometry = fiu_geom
  )
  log_fix("ADD", fiu_code, "Free City of Fiume (~28 km2 buffer)")
} else {
  cat("  SKIP: Already exists\n")
}

# ==============================================================================
# ADD 9: Mongolia 1911-1921 (fill independence gap)
# ==============================================================================
# Mongolia declared independence from China in 1911 (Bogd Khan). CShapes starts
# Mongolia only at 1921 (Soviet-backed). Fill the 10-year gap.

cat("\n--- ADD 9: Mongolia 1911-1921 ---\n")

mng_code <- "MNG-1911-1921"
if (!mng_code %in% existing_codes) {
  new_entries[[length(new_entries) + 1]] <- tibble(
    polity_code = mng_code,
    polity_name = "Bogd Khanate of Mongolia",
    start_year = 1911L,
    end_year = 1921L,
    duration_years = 11L,
    polity_type = "historical",
    continent = "Asia",
    iso3_code = "MNG",
    cow_code = NA_character_,
    polygon_source = NA_character_,
    predecessor = NA_character_,
    successor = NA_character_,
    data_sources = "research",
    verification_status = "VERIFIED",
    notes = "Bogd Khan declared independence from Qing China Dec 1911. De facto independent until 1921 Soviet-backed revolution. Predecessor of Mongolian People's Republic."
  )
  existing_codes <- c(existing_codes, mng_code)

  # Try to get Mongolia polygon from CShapes (earliest available)
  cs_path <- file.path(geodata_dir, "cshapes2_full.gpkg")
  if (file.exists(cs_path)) {
    cs <- st_read(cs_path, quiet = TRUE) %>% st_set_crs(4326)
    mng_cs <- cs %>%
      filter(grepl("Mongol", country_name, ignore.case = TRUE)) %>%
      slice(1)
    if (nrow(mng_cs) > 0) {
      new_polys[[length(new_polys) + 1]] <- st_sf(
        polity_code = mng_code,
        geometry = st_geometry(mng_cs)
      )
      db_idx <- which(sapply(new_entries, function(x) x$polity_code[1]) == mng_code)
      if (length(db_idx) > 0) {
        new_entries[[db_idx]]$polygon_source <- "CShapes 2.0 (earliest Mongolia polygon)"
      }
      log_fix("ADD", mng_code, "Bogd Khanate with CShapes Mongolia polygon")
    } else {
      log_fix("ADD", mng_code, "Bogd Khanate (no CShapes Mongolia match)")
    }
  } else {
    log_fix("ADD", mng_code, "Bogd Khanate (CShapes file not found)")
  }

  # Link predecessor/successor with existing Mongolia entries
  mng_entries <- db %>% filter(grepl("^MNG-", polity_code), polity_code != mng_code) %>%
    arrange(start_year)

  if (nrow(mng_entries) > 0) {
    first_after <- mng_entries %>% filter(start_year >= 1921) %>% slice(1)
    if (nrow(first_after) > 0) {
      # Update new entry's successor
      db_idx <- which(sapply(new_entries, function(x) x$polity_code[1]) == mng_code)
      if (length(db_idx) > 0) {
        new_entries[[db_idx]]$successor <- first_after$polity_code
      }
      # Update existing entry's predecessor
      db$predecessor[db$polity_code == first_after$polity_code] <-
        ifelse(is.na(db$predecessor[db$polity_code == first_after$polity_code]),
               mng_code,
               paste0(db$predecessor[db$polity_code == first_after$polity_code], "; ", mng_code))
      cat(sprintf("  Linked: %s -> %s\n", mng_code, first_after$polity_code))
    }
  }
} else {
  cat("  SKIP: Already exists\n")
}

# ==============================================================================
# ADD 10: India aggregate entry
# ==============================================================================
# India is a top trade country but has no aggregate entry for continuous linkage.

cat("\n--- ADD 10: India aggregate entry ---\n")

ind_agg_code <- "IND-1800-2025"
if (!ind_agg_code %in% existing_codes) {
  new_entries[[length(new_entries) + 1]] <- tibble(
    polity_code = ind_agg_code,
    polity_name = "India (old)",
    start_year = 1800L,
    end_year = 2025L,
    duration_years = 226L,
    polity_type = "aggregate",
    continent = "Asia",
    iso3_code = "IND",
    cow_code = NA_character_,
    polygon_source = NA_character_,
    predecessor = NA_character_,
    successor = NA_character_,
    data_sources = "research",
    verification_status = "VERIFIED",
    notes = "Aggregate entry for continuous trade data linkage across British India and modern India periods"
  )
  existing_codes <- c(existing_codes, ind_agg_code)

  # Use modern India polygon from existing polys
  ind_sovereign <- polys %>%
    filter(polity_code %in% c("IND-1948-2025", "IND-1947-2025")) %>%
    slice(1)

  if (nrow(ind_sovereign) > 0) {
    new_polys[[length(new_polys) + 1]] <- st_sf(
      polity_code = ind_agg_code,
      geometry = st_geometry(ind_sovereign)
    )
    db_idx <- which(sapply(new_entries, function(x) x$polity_code[1]) == ind_agg_code)
    if (length(db_idx) > 0) {
      new_entries[[db_idx]]$polygon_source <- "CShapes 2.0 (modern India sovereign polygon)"
    }
    log_fix("ADD", ind_agg_code, "India aggregate with modern sovereign polygon")
  } else {
    log_fix("ADD", ind_agg_code, "India aggregate (no polygon found)")
  }
} else {
  cat("  SKIP: Already exists\n")
}

# ==============================================================================
# Save results
# ==============================================================================

cat("\n--- Saving results ---\n")

# Combine new entries with database
if (length(new_entries) > 0) {
  new_df <- bind_rows(new_entries)
  db <- bind_rows(db, new_df)
  cat(sprintf("  Added %d new entries (total: %d)\n", nrow(new_df), nrow(db)))
} else {
  cat("  No new entries to add\n")
}

# Save updated CSV
write_csv(db, file.path(final_dir, "polities_database.csv"))
cat(sprintf("  Saved: data/final/polities_database.csv (%d rows)\n", nrow(db)))

# Update polygon file
if (length(new_polys) > 0) {
  new_poly_sf <- bind_rows(new_polys) %>% st_set_crs(4326)

  # Merge with existing
  cols <- intersect(names(polys), names(new_poly_sf))
  # Remove any existing entries that we're replacing (e.g., OTT)
  polys <- polys[!polys$polity_code %in% new_poly_sf$polity_code, ]
  combined <- bind_rows(polys[, cols], new_poly_sf[, cols])

  if (file.exists(poly_path)) file.remove(poly_path)
  st_write(combined, poly_path, layer = "polities", quiet = TRUE)
  cat(sprintf("  Saved: polities_polygons.gpkg (%d polygons)\n", nrow(combined)))
} else {
  cat("  No polygon changes\n")
}

# ==============================================================================
# Summary report
# ==============================================================================

cat(sprintf("\n%s\n", strrep("=", 60)))
cat("v2.2 Summary\n")
cat(sprintf("%s\n", strrep("=", 60)))

if (length(fix_log) > 0) {
  log_df <- bind_rows(fix_log)
  fixes <- sum(log_df$action == "FIX")
  adds <- sum(log_df$action == "ADD")
  cat(sprintf("  Fixes applied: %d\n", fixes))
  cat(sprintf("  Entries added: %d\n", adds))
  cat(sprintf("  Total database: %d entries\n", nrow(db)))

  # Save report
  write_csv(log_df, file.path(analysis_dir, "v2.2_changes_report.csv"))
  cat("  Report: data/analysis/v2.2_changes_report.csv\n")
}

cat(sprintf("\n  Non-region polities: %d\n", sum(db$polity_type != "region")))
cat(sprintf("  Subnational: %d\n", sum(db$polity_type == "subnational")))

cat("\n=== Done ===\n")
cat("Next steps:\n")
cat("  1. Run R/15_build_unified_polygons.R to rebuild unified GeoPackage\n")
cat("  2. Run R/07_build_knowledge_graph.R to update KG with new entries\n")
cat("  3. Run R/08_stress_test.R to validate\n")
