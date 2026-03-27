# ==============================================================================
# Data Integrity Fixes (v2.1)
# ==============================================================================
# 1. Fix predecessor/successor links for trade-critical countries
# 2. Fix broken F228 USSR predecessor references (F228-1940-1991 → F228-1945-1991)
# 3. Add F228 chain links
# 4. Add missing aggregate entries (UK, Argentina, USA, Russia, South Africa)
# 5. Add missing temporal entries (New Zealand 1840-1907, Canada 1800-1866, PRC 1950-2025)
# 6. Rename IND- Indonesia entries to IDN- prefix
# 7. Fill 5 polygon gaps (Midway, Wake, Johnston, Sark, + NZ/Canada polygons)
# 8. Rebuild unified GeoPackage
# ==============================================================================

source("R/00_setup.R")

cat("=== Data Integrity Fixes ===\n\n")

db <- read_csv(file.path(final_dir, "polities_database.csv"), show_col_types = FALSE)
db$cow_code <- as.character(db$cow_code)
cat("Loaded:", nrow(db), "entries\n\n")

# Helper to set predecessor/successor
set_pred <- function(db, code, value) {
  idx <- which(db$polity_code == code)
  if (length(idx) == 1) {
    old <- db$predecessor[idx]
    db$predecessor[idx] <- value
    cat(sprintf("  %-25s predecessor: %s → %s\n", code,
                ifelse(is.na(old), "-", old), value))
  } else {
    cat(sprintf("  WARNING: %s not found\n", code))
  }
  db
}

set_succ <- function(db, code, value) {
  idx <- which(db$polity_code == code)
  if (length(idx) == 1) {
    old <- db$successor[idx]
    db$successor[idx] <- value
    cat(sprintf("  %-25s successor:   %s → %s\n", code,
                ifelse(is.na(old), "-", old), value))
  } else {
    cat(sprintf("  WARNING: %s not found\n", code))
  }
  db
}

# ==============================================================================
# 1. Fix predecessor/successor links for trade-critical countries
# ==============================================================================

cat("--- 1. Fixing predecessor/successor links ---\n")

# UK chain
db <- set_succ(db, "GBR-1800-1921", "GBR-1921-2025")
db <- set_pred(db, "GBR-1921-2025", "GBR-1800-1921")

# France chain
db <- set_succ(db, "FRA-1800-1919", "FRA-1919-2025")
db <- set_pred(db, "FRA-1919-2025", "FRA-1800-1919")

# Argentina chain
db <- set_succ(db, "ARG-1800-1899", "ARG-1899-1902")
db <- set_pred(db, "ARG-1899-1902", "ARG-1800-1899")
db <- set_succ(db, "ARG-1899-1902", "ARG-1902-2025")
db <- set_pred(db, "ARG-1902-2025", "ARG-1899-1902")

# Brazil chain
db <- set_succ(db, "BRA-1800-1903", "BRA-1903-1909")
db <- set_pred(db, "BRA-1903-1909", "BRA-1800-1903")
db <- set_succ(db, "BRA-1903-1909", "BRA-1909-2025")
db <- set_pred(db, "BRA-1909-2025", "BRA-1903-1909")

# Colombia chain
db <- set_succ(db, "COL-1800-1903", "COL-1903-1922")
db <- set_pred(db, "COL-1903-1922", "COL-1800-1903")
db <- set_succ(db, "COL-1903-1922", "COL-1922-2025")
db <- set_pred(db, "COL-1922-2025", "COL-1903-1922")

# Canada chain
db <- set_succ(db, "CAN-1866-1948", "CAN-1948-2025")
db <- set_pred(db, "CAN-1948-2025", "CAN-1866-1948")

cat("\n")

# ==============================================================================
# 2. Fix broken F228 predecessor references
# ==============================================================================

cat("--- 2. Fixing F228-1940-1991 → F228-1945-1991 ---\n")

broken_f228 <- which(!is.na(db$predecessor) & db$predecessor == "F228-1940-1991")
cat(sprintf("  Found %d entries referencing F228-1940-1991\n", length(broken_f228)))
db$predecessor[broken_f228] <- "F228-1945-1991"
cat("  Updated all to F228-1945-1991\n\n")

# ==============================================================================
# 3. Add F228/RUS chain links
# ==============================================================================

cat("--- 3. Adding F228/RUS temporal chain ---\n")

f228_chain <- c(
  "F228-1800-1905", "F228-1905-1914", "F228-1914-1917", "F228-1917-1918",
  "F228-1918-1920", "F228-1920-1921", "F228-1921-1940", "F228-1940-1945",
  "F228-1945-1991", "RUS-1991-2014", "RUS-2014-2025"
)

for (i in seq_along(f228_chain)) {
  if (i > 1) {
    db <- set_pred(db, f228_chain[i], f228_chain[i - 1])
  }
  if (i < length(f228_chain)) {
    db <- set_succ(db, f228_chain[i], f228_chain[i + 1])
  }
}

# Also add successor link from F228-1945-1991 to post-Soviet states
db <- set_succ(db, "F228-1945-1991",
  "RUS-1991-2014; ARM-1991-2025; AZE-1991-2025; BLR-1991-2025; EST-1991-2025; GEO-1991-2025; KAZ-1991-2025; KGZ-1991-2025; LTU-1991-2025; LVA-1991-2025; MDA-1991-2025; TJK-1991-2025; TKM-1991-2025; UKR-1991-2014; UZB-1991-2025")

cat("\n")

# ==============================================================================
# 4. Rename IND- Indonesia entries to IDN- prefix
# ==============================================================================

cat("--- 4. Renaming IND- Indonesia entries to IDN- ---\n")

rename_map <- c(
  "IND-1800-1889" = "IDN-1800-1889",
  "IND-1889-1949" = "IDN-1889-1949"
)

for (old_code in names(rename_map)) {
  new_code <- rename_map[old_code]
  idx <- which(db$polity_code == old_code)
  if (length(idx) == 1) {
    db$polity_code[idx] <- new_code
    db$iso3_code[idx] <- "IDN"
    cat(sprintf("  Renamed %s → %s (iso3: IND → IDN)\n", old_code, new_code))

    # Update any predecessor/successor references in other entries
    pred_refs <- which(!is.na(db$predecessor) & grepl(old_code, db$predecessor, fixed = TRUE))
    if (length(pred_refs) > 0) {
      db$predecessor[pred_refs] <- gsub(old_code, new_code, db$predecessor[pred_refs], fixed = TRUE)
      cat(sprintf("    Updated %d predecessor references\n", length(pred_refs)))
    }
    succ_refs <- which(!is.na(db$successor) & grepl(old_code, db$successor, fixed = TRUE))
    if (length(succ_refs) > 0) {
      db$successor[succ_refs] <- gsub(old_code, new_code, db$successor[succ_refs], fixed = TRUE)
      cat(sprintf("    Updated %d successor references\n", length(succ_refs)))
    }
  }
}

# Add successor/predecessor links for Indonesia chain
db <- set_succ(db, "IDN-1800-1889", "IDN-1889-1949")
db <- set_pred(db, "IDN-1889-1949", "IDN-1800-1889")
db <- set_succ(db, "IDN-1889-1949", "IDN-1945-1949")
db <- set_pred(db, "IDN-1945-1949", "IDN-1889-1949")

cat("\n")

# ==============================================================================
# 5. Add missing aggregate entries
# ==============================================================================

cat("--- 5. Adding missing aggregate entries ---\n")

new_aggregates <- tribble(
  ~polity_code, ~polity_name, ~start_year, ~end_year, ~continent, ~iso3_code, ~cow_code, ~polygon_source,
  "GBR-1800-2025", "United Kingdom (old)", 1800L, 2025L, "Europe", "GBR", NA_character_, "CShapes 2.0",
  "ARG-1800-2025", "Argentina (old)", 1800L, 2025L, "South America", "ARG", NA_character_, "CShapes 2.0",
  "USA-1800-2025", "United States (old)", 1800L, 2025L, "North America", "USA", NA_character_, "CShapes 2.0",
  "RUS-1800-2025", "Russia/USSR (old)", 1800L, 2025L, "Europe", "RUS", NA_character_, "CShapes 2.0",
  "ZAF-1800-2025", "South Africa (old)", 1800L, 2025L, "Africa", "ZAF", NA_character_, "CShapes 2.0"
)

new_aggregates <- new_aggregates %>%
  mutate(
    duration_years = end_year - start_year + 1L,
    polity_type = "aggregate",
    predecessor = NA_character_,
    successor = NA_character_,
    data_sources = "WHEP-fix",
    verification_status = "VERIFIED",
    notes = "Aggregate entry for continuous trade data linkage"
  )

# Check none already exist
existing <- new_aggregates$polity_code[new_aggregates$polity_code %in% db$polity_code]
if (length(existing) > 0) {
  cat(sprintf("  SKIPPING already existing: %s\n", paste(existing, collapse = ", ")))
  new_aggregates <- new_aggregates[!new_aggregates$polity_code %in% existing, ]
}

cat(sprintf("  Adding %d aggregate entries:\n", nrow(new_aggregates)))
for (i in seq_len(nrow(new_aggregates))) {
  cat(sprintf("    %s (%s)\n", new_aggregates$polity_code[i], new_aggregates$polity_name[i]))
}

db <- bind_rows(db, new_aggregates)
cat("\n")

# ==============================================================================
# 6. Add missing temporal entries
# ==============================================================================

cat("--- 6. Adding missing temporal entries ---\n")

new_entries <- tribble(
  ~polity_code, ~polity_name, ~start_year, ~end_year, ~polity_type, ~continent, ~iso3_code, ~cow_code, ~polygon_source, ~successor, ~predecessor, ~data_sources, ~verification_status, ~notes,
  "NZL-1840-1907", "New Zealand (colony)", 1840L, 1907L, "historical", "Oceania", "NZL", NA_character_, "CShapes 2.0", "NZL-1907-2025", NA_character_, "CShapes; WHEP-fix", "VERIFIED", "British crown colony 1840; dominion from 1907",
  "CAN-1800-1866", "Canada (pre-Confederation)", 1800L, 1866L, "historical", "North America", "CAN", NA_character_, "CShapes 2.0", "CAN-1866-1948", NA_character_, "CShapes; WHEP-fix", "VERIFIED", "British North America; Confederation 1867",
  "CHN-1950-2025", "China (PRC)", 1950L, 2025L, "sovereign", "Asia", "CHN", NA_character_, "CShapes 2.0", NA_character_, "CHN-1949-1950", "CShapes; FAOSTAT; M49; WHEP-fix", "VERIFIED", "People's Republic of China"
)

new_entries <- new_entries %>%
  mutate(duration_years = end_year - start_year + 1L)

cat(sprintf("  Adding %d entries:\n", nrow(new_entries)))
for (i in seq_len(nrow(new_entries))) {
  cat(sprintf("    %s (%s) %d-%d\n",
      new_entries$polity_code[i], new_entries$polity_name[i],
      new_entries$start_year[i], new_entries$end_year[i]))
}

# Update predecessor links for existing entries
db <- set_pred(db, "NZL-1907-2025", "NZL-1840-1907")
db <- set_pred(db, "CAN-1866-1948", "CAN-1800-1866")
db <- set_succ(db, "CHN-1949-1950", "CHN-1950-2025")

db <- bind_rows(db, new_entries)
cat("\n")

# ==============================================================================
# 7. Extract polygons for new + missing entries
# ==============================================================================

cat("--- 7. Extracting polygons ---\n")

cs_full <- st_read(file.path(geodata_dir, "cshapes2_full.gpkg"), quiet = TRUE) %>%
  st_set_crs(4326)

# Extract by COW code + best date match
extract_cshapes <- function(cow_num, target_start, target_end, label) {
  candidates <- cs_full[cs_full$cowcode == cow_num, ]
  if (nrow(candidates) == 0) {
    cat(sprintf("  MISS: %s (cow=%d not found)\n", label, cow_num))
    return(NULL)
  }
  candidates$cs_start <- as.integer(format(candidates$start, "%Y"))
  candidates$cs_end <- as.integer(format(candidates$end, "%Y"))
  candidates$overlap <- pmax(0,
    pmin(candidates$cs_end, target_end) - pmax(candidates$cs_start, target_start))
  best <- candidates[order(-candidates$overlap), ][1, ]
  cat(sprintf("  OK:   %s ← CShapes cow=%d (%s to %s)\n", label, cow_num,
      format(best$start, "%Y"), format(best$end, "%Y")))
  st_geometry(best)
}

new_polys <- list()

# New Zealand colony
geom <- extract_cshapes(920, 1840, 1907, "NZL-1840-1907")
if (!is.null(geom)) new_polys[["NZL-1840-1907"]] <- geom

# Canada pre-Confederation (use COW 20 = Canada)
geom <- extract_cshapes(20, 1800, 1866, "CAN-1800-1866")
if (!is.null(geom)) new_polys[["CAN-1800-1866"]] <- geom

# PRC (COW 710)
geom <- extract_cshapes(710, 1950, 2025, "CHN-1950-2025")
if (!is.null(geom)) new_polys[["CHN-1950-2025"]] <- geom

# Aggregate polygons — use the modern sovereign polygon
# Load existing unified gpkg to grab modern polygons
unified <- st_read(file.path(final_dir, "polities_database.gpkg"), quiet = TRUE)

for (agg_code in c("GBR-1800-2025", "ARG-1800-2025", "USA-1800-2025",
                    "RUS-1800-2025", "ZAF-1800-2025")) {
  iso <- sub("-.*", "", agg_code)
  # Find modern sovereign entry polygon
  modern_codes <- db$polity_code[db$iso3_code == iso & db$polity_type == "sovereign" &
                                   db$end_year == 2025 & !is.na(db$iso3_code)]
  matched <- unified[unified$polity_code %in% modern_codes & !st_is_empty(unified), ]
  if (nrow(matched) > 0) {
    new_polys[[agg_code]] <- st_geometry(matched[1, ])
    cat(sprintf("  OK:   %s ← polygon from %s\n", agg_code, matched$polity_code[1]))
  } else {
    # Fallback to CShapes
    cow <- db$cow_code[db$polity_code == agg_code]
    if (!is.na(cow)) {
      geom <- extract_cshapes(as.integer(cow), 1950, 2025, agg_code)
      if (!is.null(geom)) new_polys[[agg_code]] <- geom
    } else {
      cat(sprintf("  MISS: %s (no modern polygon found)\n", agg_code))
    }
  }
}

# Tiny islands from Natural Earth map_units
ne_mu <- ne_download(scale = 10, type = "admin_0_map_units", category = "cultural",
                     returnclass = "sf")

ne_map <- c(
  "MID-1859-1982" = "Midway Is.",
  "WAK-1898-1982" = "Wake Atoll",
  "JTN-1800-1982" = "Johnston Atoll"
)

for (pc in names(ne_map)) {
  ne_name <- ne_map[pc]
  m <- ne_mu[ne_mu$NAME == ne_name, ]
  if (nrow(m) > 0) {
    new_polys[[pc]] <- st_geometry(m[1, ]) %>% st_set_crs(4326)
    cat(sprintf("  OK:   %s ← Natural Earth '%s'\n", pc, ne_name))
  } else {
    cat(sprintf("  MISS: %s (Natural Earth '%s' not found)\n", pc, ne_name))
  }
}

# Sark from GADM
gadm1 <- st_read(gadm_path, layer = "level1", quiet = TRUE)
sark <- gadm1[grepl("Sark", gadm1$NAME_1, ignore.case = TRUE) &
                grepl("Guernsey", gadm1$NAME_0, ignore.case = TRUE), ]
if (nrow(sark) > 0) {
  new_polys[["F285-2011-2023"]] <- st_geometry(sark[1, ]) %>% st_set_crs(4326)
  cat(sprintf("  OK:   F285-2011-2023 ← GADM Sark (Guernsey admin-1)\n"))
}

cat(sprintf("\n  Total new polygons: %d\n\n", length(new_polys)))

# ==============================================================================
# 8. Update polygon files for renamed entries
# ==============================================================================

cat("--- 8. Updating polygon files for IND→IDN rename ---\n")

# Update polities_polygons.gpkg
poly_path <- file.path(geodata_dir, "polities_polygons.gpkg")
polys <- st_read(poly_path, quiet = TRUE)

for (old_code in names(rename_map)) {
  new_code <- rename_map[old_code]
  idx <- which(polys$polity_code == old_code)
  if (length(idx) > 0) {
    polys$polity_code[idx] <- new_code
    cat(sprintf("  Renamed %s → %s in polities_polygons.gpkg\n", old_code, new_code))
  }
}

if (file.exists(poly_path)) file.remove(poly_path)
st_write(polys, poly_path, layer = "polities", quiet = TRUE)
cat("  Saved updated polities_polygons.gpkg\n\n")

# ==============================================================================
# 9. Save updated CSV
# ==============================================================================

cat("--- 9. Saving updated database ---\n")
cat(sprintf("  Entries: %d (was 1,228)\n", nrow(db)))

write_csv(db, file.path(final_dir, "polities_database.csv"))
cat("  Saved polities_database.csv\n\n")

# ==============================================================================
# 10. Rebuild unified GeoPackage
# ==============================================================================

cat("--- 10. Rebuilding unified GeoPackage ---\n")

# Reload all polygon sources (R/15 logic inlined)
load_gpkg <- function(filename) {
  path <- file.path(geodata_dir, filename)
  if (!file.exists(path)) return(NULL)
  sf <- st_read(path, quiet = TRUE)
  sf <- sf[, "polity_code"]
  sf <- st_set_geometry(sf, "geometry")
  st_set_crs(sf, 4326)
}

all_polys <- bind_rows(
  load_gpkg("precolonial_polygons.gpkg"),
  load_gpkg("cliopatria_polygons.gpkg"),
  load_gpkg("chgis_qing_provinces.gpkg"),
  load_gpkg("us_historical_states.gpkg"),
  load_gpkg("brazil_historical_states.gpkg"),
  load_gpkg("spain_provinces.gpkg"),
  load_gpkg("polities_polygons.gpkg")
)

all_polys <- all_polys[!duplicated(all_polys$polity_code), ]
cat(sprintf("  Base polygons: %d\n", nrow(all_polys)))

# CShapes recovery for polities still missing (same logic as R/15)
non_region <- db[db$polity_type != "region", ]
still_missing <- non_region[!non_region$polity_code %in% all_polys$polity_code &
                              !is.na(non_region$polygon_source) &
                              grepl("CShapes", non_region$polygon_source), ]
cat(sprintf("  CShapes recovery candidates: %d\n", nrow(still_missing)))

for (i in seq_len(nrow(still_missing))) {
  pc <- still_missing$polity_code[i]
  cow <- still_missing$cow_code[i]
  sy <- still_missing$start_year[i]
  ey <- still_missing$end_year[i]
  pname <- still_missing$polity_name[i]

  if (!is.na(cow)) {
    candidates <- cs_full[cs_full$cowcode == as.integer(cow), ]
  } else {
    name_clean <- str_replace_all(pname, "\\s*\\(.*\\)\\s*", "")
    candidates <- cs_full[grepl(name_clean, cs_full$country_name, ignore.case = TRUE), ]
    if (nrow(candidates) == 0) {
      first_word <- word(pname, 1)
      if (nchar(first_word) >= 4) {
        candidates <- cs_full[grepl(first_word, cs_full$country_name, ignore.case = TRUE), ]
      }
    }
  }

  if (nrow(candidates) == 0) next

  candidates$cs_start <- as.integer(format(candidates$start, "%Y"))
  candidates$cs_end <- as.integer(format(candidates$end, "%Y"))
  candidates$overlap <- pmax(0, pmin(candidates$cs_end, ey) - pmax(candidates$cs_start, sy))
  best <- candidates[order(-candidates$overlap), ][1, ]

  rec_sf <- st_sf(polity_code = pc, geometry = st_geometry(best))
  rec_sf <- st_set_geometry(rec_sf, "geometry")
  rec_sf <- st_set_crs(rec_sf, 4326)
  all_polys <- bind_rows(all_polys, rec_sf)
}
all_polys <- all_polys[!duplicated(all_polys$polity_code), ]
cat(sprintf("  After CShapes recovery: %d\n", nrow(all_polys)))

# Add new polygons
for (pc in names(new_polys)) {
  if (!pc %in% all_polys$polity_code) {
    new_sf <- st_sf(
      polity_code = pc,
      geometry = new_polys[[pc]]
    )
    new_sf <- st_set_geometry(new_sf, "geometry")
    new_sf <- st_set_crs(new_sf, 4326)
    all_polys <- bind_rows(all_polys, new_sf)
  }
}

all_polys <- all_polys[!duplicated(all_polys$polity_code), ]
all_polys <- st_make_valid(all_polys)
cat(sprintf("  With new polygons: %d\n", nrow(all_polys)))

# Join with database
non_region <- db[db$polity_type != "region", ]
has_poly <- sum(non_region$polity_code %in% all_polys$polity_code)
cat(sprintf("  Non-region with polygon: %d / %d (%.1f%%)\n",
            has_poly, nrow(non_region), 100 * has_poly / nrow(non_region)))

unified <- db %>%
  left_join(all_polys %>% select(polity_code), by = "polity_code")

unified <- st_as_sf(unified)
unified <- st_set_crs(unified, 4326)

has_geom <- !st_is_empty(unified)
cat(sprintf("  With geometry: %d / %d\n", sum(has_geom), nrow(unified)))

out_path <- file.path(final_dir, "polities_database.gpkg")
if (file.exists(out_path)) file.remove(out_path)
st_write(unified, out_path, layer = "polities", quiet = TRUE)
cat(sprintf("  Saved: %s (%.1f MB)\n", out_path, file.size(out_path) / 1e6))

# ==============================================================================
# Summary
# ==============================================================================

cat("\n=== Summary ===\n")
cat(sprintf("  Total entries: %d\n", nrow(db)))
cat(sprintf("  New aggregates: 5 (GBR, ARG, USA, RUS, ZAF)\n"))
cat(sprintf("  New temporal: 3 (NZL colony, CAN pre-Confed, PRC sovereign)\n"))
cat(sprintf("  Renamed: 2 (IND-Indonesia → IDN-Indonesia)\n"))
cat(sprintf("  Pred/succ links fixed: ~40\n"))
cat(sprintf("  F228 references fixed: %d\n", length(broken_f228)))
cat(sprintf("  New polygons extracted: %d\n", length(new_polys)))
cat(sprintf("  Non-region with geometry: %d / %d (%.1f%%)\n",
            has_poly, nrow(non_region), 100 * has_poly / nrow(non_region)))
cat("\nDone!\n")
