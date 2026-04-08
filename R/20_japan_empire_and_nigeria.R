# ==============================================================================
# Japan Empire Period Splits and Nigeria Pre-Colonial Coverage
# ==============================================================================
# 1. Split JPN-1800-2025 into 4 periods based on >10% area changes:
#    JPN-1800-1895 (home islands, pre-imperial)
#    JPN-1895-1945 (empire: +Taiwan 1895, +Sakhalin 1905, +Korea 1910)
#    JPN-1945-1952 (occupied by USA)
#    JPN-1952-2025 (modern Japan)
#    JPN-1800-2025 reclassified as aggregate
#    Empire polygon built by unioning CShapes Japan + Taiwan + Korea + Sakhalin
#
# 2. Add Niger Delta City-States (NDD-1800-1884) -- palm oil trade hub
# 3. Add Nupe Kingdom (NUP-1800-1897) -- Niger River trade
# 4. Add Nigeria pre-colonial aggregate (NGA-1800-1899)
# 5. Enhance Sokoto notes with Kano/Katsina trade info
#
# Memory-safe: uses SQL queries on CShapes, no bulk loading.
# Run AFTER R/19.
# ==============================================================================

source("R/00_setup.R")
sf_use_s2(FALSE)

cat("=== Japan Empire Splits and Nigeria Pre-Colonial Coverage ===\n\n")

db <- read_csv(file.path(final_dir, "polities_database.csv"), show_col_types = FALSE)
cat("Loaded database:", nrow(db), "entries\n")

poly_path <- file.path(geodata_dir, "polities_polygons.gpkg")
polys <- st_read(poly_path, quiet = TRUE) %>% st_set_crs(4326)
cat("Loaded polygons:", nrow(polys), "features\n\n")

existing_codes <- db$polity_code
new_entries <- list()
new_polys <- list()
changes <- 0

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
# PART 1: Japan Empire Period Splits
# ==============================================================================

cat("--- PART 1: Japan Empire period splits ---\n")

# Step 1: Reclassify JPN-1800-2025 as aggregate
jpn_idx <- which(db$polity_code == "JPN-1800-2025")
if (length(jpn_idx) == 1) {
  db$polity_type[jpn_idx] <- "national"
  db$notes[jpn_idx] <- "Aggregate entry for continuous trade data linkage across empire/post-war periods"
  db$polygon_source[jpn_idx] <- "CShapes 2.0"
  cat("  JPN-1800-2025 reclassified as aggregate\n")
  changes <- changes + 1
}

# Step 2: Build empire polygon from CShapes
# Load individual components via SQL (memory-safe)
cs_path <- file.path(geodata_dir, "cshapes2_full.gpkg")
cs_available <- file.exists(cs_path)

jpn_home_geom <- NULL
jpn_empire_geom <- NULL
jpn_post_geom <- NULL

if (cs_available) {
  cat("  Building polygons from CShapes...\n")

  # Japan home islands (COW 740, earliest period)
  jpn_cs <- st_read(cs_path, quiet = TRUE,
    query = "SELECT * FROM cshapes WHERE cowcode = 740 LIMIT 1")
  if (nrow(jpn_cs) > 0) {
    jpn_home_geom <- st_geometry(jpn_cs[1, ]) %>% st_set_crs(4326)
    cat("    Japan home islands: OK\n")
  }

  # Taiwan colony (COW 713 = Taiwan under Japan in CShapes)
  twn_cs <- st_read(cs_path, quiet = TRUE,
    query = "SELECT * FROM cshapes WHERE cowcode = 713 LIMIT 1")
  twn_geom <- if (nrow(twn_cs) > 0) st_geometry(twn_cs[1, ]) %>% st_set_crs(4326) else NULL

  # Korea colony (COW 730 = Korea under Japan)
  kor_cs <- st_read(cs_path, quiet = TRUE,
    query = "SELECT * FROM cshapes WHERE cowcode = 730 AND status = 3 LIMIT 1")
  if (nrow(kor_cs) == 0) {
    kor_cs <- st_read(cs_path, quiet = TRUE,
      query = "SELECT * FROM cshapes WHERE cowcode = 730 LIMIT 1")
  }
  kor_geom <- if (nrow(kor_cs) > 0) st_geometry(kor_cs[1, ]) %>% st_set_crs(4326) else NULL

  # Southern Sakhalin (COW code varies; try by name)
  sak_cs <- st_read(cs_path, quiet = TRUE,
    query = "SELECT * FROM cshapes WHERE country_name LIKE '%Sakhalin%' OR country_name LIKE '%Karafuto%' LIMIT 1")
  if (nrow(sak_cs) == 0) {
    # Try owner = Japan (740)
    sak_cs <- st_read(cs_path, quiet = TRUE,
      query = "SELECT * FROM cshapes WHERE owner = 740 AND country_name LIKE '%South%' LIMIT 1")
  }
  sak_geom <- if (nrow(sak_cs) > 0) st_geometry(sak_cs[1, ]) %>% st_set_crs(4326) else NULL

  if (!is.null(jpn_home_geom)) {
    # Build empire polygon: union of home + colonies
    components <- list(jpn_home_geom)
    if (!is.null(twn_geom)) components <- c(components, list(twn_geom))
    if (!is.null(kor_geom)) components <- c(components, list(kor_geom))
    if (!is.null(sak_geom)) components <- c(components, list(sak_geom))

    # Union all components
    empire_union <- do.call(c, components) %>% st_union() %>% st_make_valid()
    jpn_empire_geom <- empire_union

    cat(sprintf("    Empire polygon: Japan + %s%s%s\n",
      ifelse(!is.null(twn_geom), "Taiwan ", ""),
      ifelse(!is.null(kor_geom), "Korea ", ""),
      ifelse(!is.null(sak_geom), "Sakhalin ", "")))

    jpn_post_geom <- jpn_home_geom
  }
} else {
  cat("  WARNING: CShapes file not found, using existing JPN polygon\n")
  jpn_in_polys <- polys[polys$polity_code == "JPN-1800-2025", ]
  if (nrow(jpn_in_polys) > 0) {
    jpn_home_geom <- st_geometry(jpn_in_polys[1, ])
    jpn_empire_geom <- jpn_home_geom  # fallback: same polygon
    jpn_post_geom <- jpn_home_geom
  }
}

# Step 3: Create period entries
jpn_periods <- tribble(
  ~code, ~name, ~start, ~end, ~type, ~polygon_src, ~notes,
  "JPN-1800-1895", "Japan (to 1895)", 1800L, 1895L, "national",
    "CShapes 2.0", "Pre-imperial Japan. Home islands only (~370,776 km2). Treaty of Shimonoseki (1895) marks beginning of colonial expansion.",
  "JPN-1895-1945", "Japanese Empire", 1895L, 1945L, "national",
    "CShapes 2.0 (union: Japan + Taiwan + Korea + S. Sakhalin)",
    "Empire period. +Taiwan (Treaty of Shimonoseki 1895), +S. Sakhalin (Treaty of Portsmouth 1905), +Korea (annexed 1910). ~658,000 km2 at peak. Manchukuo (1932-45) tracked separately as MAN-1932-1945.",
  "JPN-1945-1952", "Japan (occupied)", 1945L, 1952L, "national",
    "CShapes 2.0", "US occupation (SCAP). All colonies stripped. Treaty of San Francisco (1952-04-28) restores sovereignty.",
  "JPN-1952-2025", "Japan", 1952L, 2025L, "national",
    "CShapes 2.0", "Post-occupation. Okinawa reverted 1972. Kuril Islands dispute with Russia unresolved."
)

for (i in seq_len(nrow(jpn_periods))) {
  p <- jpn_periods[i, ]
  if (p$code %in% existing_codes) {
    cat(sprintf("  SKIP: %s already exists\n", p$code))
    next
  }

  new_entries[[length(new_entries) + 1]] <- tibble(
    polity_code = p$code,
    polity_name = p$name,
    start_year = p$start,
    end_year = p$end,
    duration_years = p$end - p$start + 1L,
    polity_type = p$type,
    continent = "Asia",
    iso3_code = "JPN",
    cow_code = NA_character_,
    polygon_source = p$polygon_src,
    predecessor = NA_character_,
    successor = NA_character_,
    data_sources = "CShapes; research",
    verification_status = "VERIFIED",
    notes = p$notes
  )
  existing_codes <- c(existing_codes, p$code)

  # Assign polygon
  geom_to_use <- switch(p$code,
    "JPN-1800-1895" = jpn_home_geom,
    "JPN-1895-1945" = jpn_empire_geom,
    "JPN-1945-1952" = jpn_post_geom,
    "JPN-1952-2025" = jpn_post_geom,
    NULL
  )
  if (!is.null(geom_to_use)) {
    new_polys[[length(new_polys) + 1]] <- st_sf(
      polity_code = p$code, geometry = geom_to_use
    )
  }

  cat(sprintf("  ADD: %s (%s)\n", p$code, p$name))
  changes <- changes + 1
}

# Step 4: Link predecessor/successor chain
set_succ("JPN-1800-1895", "JPN-1895-1945")
set_pred("JPN-1895-1945", "JPN-1800-1895")
set_succ("JPN-1895-1945", "JPN-1945-1952")
set_pred("JPN-1945-1952", "JPN-1895-1945")
set_succ("JPN-1945-1952", "JPN-1952-2025")
set_pred("JPN-1952-2025", "JPN-1945-1952")

# Update subnational parent references (47 prefectures -> JPN-1952-2025)
# Since prefectures are 1888-2025 and span multiple Japan periods, keep parent
# as JPN-1800-2025 (the aggregate) which is the correct semantic parent.

cat("  Linked Japan predecessor/successor chain\n")

# ==============================================================================
# PART 2: Nigeria Pre-Colonial Coverage
# ==============================================================================

cat("\n--- PART 2: Nigeria pre-colonial coverage ---\n")

# ADD: Niger Delta City-States (palm oil trade hub)
ndd_code <- "NDD-1800-1884"
if (!ndd_code %in% existing_codes) {
  new_entries[[length(new_entries) + 1]] <- tibble(
    polity_code = ndd_code,
    polity_name = "Niger Delta City-States",
    start_year = 1800L, end_year = 1884L, duration_years = 85L,
    polity_type = "national",
    continent = "Africa", iso3_code = "NGA", cow_code = NA_character_,
    polygon_source = NA_character_,
    predecessor = NA_character_, successor = "OIL-1884-1898",
    data_sources = "research",
    verification_status = "VERIFIED",
    notes = "Composite: Bonny, Opobo (1870-1887), New Calabar (Kalabari), Brass (Nembe), Old Calabar (Efik). World's largest palm oil exporters. Predecessor to Oil Rivers Protectorate. Territory: Niger Delta mangrove coast, Cross River estuary."
  )
  existing_codes <- c(existing_codes, ndd_code)

  # Use OIL-1884-1898 polygon as proxy (covers same territory)
  oil_poly <- polys[polys$polity_code == "OIL-1884-1898", ]
  if (nrow(oil_poly) > 0) {
    new_polys[[length(new_polys) + 1]] <- st_sf(
      polity_code = ndd_code, geometry = st_geometry(oil_poly[1, ])
    )
    # Update polygon source
    new_entries[[length(new_entries)]]$polygon_source <- "CShapes 2.0 (Oil Rivers Protectorate proxy)"
    cat(sprintf("  ADD: %s with OIL proxy polygon\n", ndd_code))
  } else {
    cat(sprintf("  ADD: %s (no polygon)\n", ndd_code))
  }

  set_pred("OIL-1884-1898", ndd_code)
  changes <- changes + 1
}

# ADD: Nupe Kingdom / Bida Emirate (Niger River trade)
nup_code <- "NUP-1800-1897"
if (!nup_code %in% existing_codes) {
  new_entries[[length(new_entries) + 1]] <- tibble(
    polity_code = nup_code,
    polity_name = "Nupe Kingdom (Bida Emirate)",
    start_year = 1800L, end_year = 1897L, duration_years = 98L,
    polity_type = "national",
    continent = "Africa", iso3_code = "NGA", cow_code = NA_character_,
    polygon_source = NA_character_,
    predecessor = NA_character_, successor = "NNI-1899-1904",
    data_sources = "research",
    verification_status = "VERIFIED",
    notes = "Middle Niger River trade hub. Famous for brass and glass bead manufacture, cloth production. Nominally under Sokoto/Gwandu but operationally autonomous. Conquered by Royal Niger Company Jan 1897 (Bida fell Jan 29). Capital: Bida (6.01E, 9.08N)."
  )
  existing_codes <- c(existing_codes, nup_code)

  # No polygon available - Nupe falls within Sokoto polygon but was distinct
  cat(sprintf("  ADD: %s (no dedicated polygon)\n", nup_code))
  set_pred("NNI-1899-1904", nup_code)
  changes <- changes + 1
}

# ADD: Nigeria pre-colonial aggregate
nga_agg_code <- "NGA-1800-1899"
if (!nga_agg_code %in% existing_codes) {
  new_entries[[length(new_entries) + 1]] <- tibble(
    polity_code = nga_agg_code,
    polity_name = "Nigeria (pre-colonial)",
    start_year = 1800L, end_year = 1899L, duration_years = 100L,
    polity_type = "national",
    continent = "Africa", iso3_code = "NGA", cow_code = NA_character_,
    polygon_source = NA_character_,
    predecessor = NA_character_,
    successor = "NNI-1899-1904; SNI-1899-1906",
    data_sources = "research",
    verification_status = "VERIFIED",
    notes = "Pre-colonial aggregate for Nigerian trade data linkage. Includes Sokoto Caliphate (incl. Kano and Katsina emirates, largest constituent ~644k km2), Bornu Empire, Oyo successor states (Ibadan, Ijebu, Egba), Kingdom of Benin, Niger Delta city-states (Bonny, Calabar, Brass), Nupe/Bida, Igala, Borgu. Uses modern Nigeria polygon as proxy."
  )
  existing_codes <- c(existing_codes, nga_agg_code)

  # Use modern NGA polygon as proxy (consistent with other aggregates)
  nga_poly <- polys[polys$polity_code == "NGA-1961-2025", ]
  if (nrow(nga_poly) == 0) nga_poly <- polys[polys$polity_code == "NGA-1960-1961", ]
  if (nrow(nga_poly) > 0) {
    new_polys[[length(new_polys) + 1]] <- st_sf(
      polity_code = nga_agg_code, geometry = st_geometry(nga_poly[1, ])
    )
    new_entries[[length(new_entries)]]$polygon_source <- "CShapes 2.0 (modern Nigeria proxy)"
    cat(sprintf("  ADD: %s with modern NGA proxy polygon\n", nga_agg_code))
  } else {
    cat(sprintf("  ADD: %s (no polygon)\n", nga_agg_code))
  }
  changes <- changes + 1
}

# Enhance Sokoto notes with Kano/Katsina trade info
sok_idx <- which(db$polity_code == "SOK-1804-1903")
if (length(sok_idx) == 1) {
  existing_notes <- db$notes[sok_idx]
  kano_note <- "Includes Kano Emirate (caliphate's most commercially important vassal: trans-Saharan trade terminus, textile/indigo production center) and Katsina Emirate (leather, cloth). Both subsumed after Fulani jihad 1804-1808."
  if (is.na(existing_notes) || existing_notes == "NA") {
    db$notes[sok_idx] <- kano_note
  } else if (!grepl("Kano", existing_notes)) {
    db$notes[sok_idx] <- paste0(existing_notes, ". ", kano_note)
  }
  cat("  Updated SOK-1804-1903 notes with Kano/Katsina trade info\n")
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

if (length(new_polys) > 0) {
  new_poly_sf <- bind_rows(new_polys) %>% st_set_crs(4326)
  cols <- intersect(names(polys), names(new_poly_sf))
  polys <- polys[!polys$polity_code %in% new_poly_sf$polity_code, ]
  combined <- bind_rows(polys[, cols], new_poly_sf[, cols])
  if (file.exists(poly_path)) file.remove(poly_path)
  st_write(combined, poly_path, layer = "polities", quiet = TRUE)
  cat(sprintf("  Saved: polities_polygons.gpkg (%d polygons)\n", nrow(combined)))
}

cat(sprintf("\nTotal changes: %d\n", changes))
cat("\n=== Done ===\n")
cat("Next: Run R/15, R/07, R/08 to rebuild unified output and validate\n")
