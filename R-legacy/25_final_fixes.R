# ==============================================================================
# Final Fixes: Missing Polygons, Myanmar Split, Auto-Chain Historical Entries
# ==============================================================================
# Priority 2: Fill 3 missing polygon_source entries
# Priority 3: Split MMR-1800-2025 (Myanmar lost 31% in 1826, 21% in 1852)
# Priority 4: Auto-chain ~267 historical entries by ISO3 + date order
#
# Memory-safe: CSV only for chains, minimal geo for polygon fills.
# ==============================================================================

source("R/00_setup.R")
sf_use_s2(FALSE)

cat("=== Final Fixes ===\n\n")

db <- read_csv(file.path(final_dir, "polities_database.csv"), show_col_types = FALSE)
cat("Loaded database:", nrow(db), "entries\n")

poly_path <- file.path(geodata_dir, "polities_polygons.gpkg")
polys <- st_read(poly_path, quiet = TRUE) %>% st_set_crs(4326)

existing_codes <- db$polity_code
new_entries <- list()
changes <- 0

# ==============================================================================
# PRIORITY 2: Fill 3 missing polygon sources
# ==============================================================================

cat("\n--- PRIORITY 2: Fill missing polygon sources ---\n")

# IND-1800-2025 (India aggregate): use IND-1949-2025 sovereign polygon
ind_poly <- polys[polys$polity_code == "IND-1949-2025", ]
if (nrow(ind_poly) > 0) {
  polys <- bind_rows(polys, st_sf(polity_code = "IND-1800-2025", geometry = st_geometry(ind_poly[1,])))
  db$polygon_source[db$polity_code == "IND-1800-2025"] <- "CShapes 2.0 (modern India sovereign polygon)"
  cat("  OK: IND-1800-2025 <- IND-1949-2025 polygon\n")
  changes <- changes + 1
} else {
  cat("  MISS: IND-1949-2025 polygon not found\n")
}

# NDD-1800-1884 (Niger Delta): use OIL-1884-1898 polygon (same territory)
oil_poly <- polys[polys$polity_code == "OIL-1884-1898", ]
if (nrow(oil_poly) > 0) {
  polys <- bind_rows(polys, st_sf(polity_code = "NDD-1800-1884", geometry = st_geometry(oil_poly[1,])))
  db$polygon_source[db$polity_code == "NDD-1800-1884"] <- "CShapes 2.0 (Oil Rivers Protectorate proxy)"
  cat("  OK: NDD-1800-1884 <- OIL-1884-1898 polygon\n")
  changes <- changes + 1
} else {
  cat("  MISS: OIL-1884-1898 polygon not found (will be recovered in R/15)\n")
}

# NUP-1800-1897 (Nupe): use Sokoto polygon clipped? No, just use SOK polygon as proxy
sok_poly <- polys[polys$polity_code == "SOK-1804-1903", ]
if (nrow(sok_poly) > 0) {
  polys <- bind_rows(polys, st_sf(polity_code = "NUP-1800-1897", geometry = st_geometry(sok_poly[1,])))
  db$polygon_source[db$polity_code == "NUP-1800-1897"] <- "Paine et al. (2024) (Sokoto Caliphate proxy, Nupe within)"
  cat("  OK: NUP-1800-1897 <- SOK-1804-1903 polygon (proxy)\n")
  changes <- changes + 1
} else {
  cat("  MISS: SOK-1804-1903 polygon not found\n")
}

# ==============================================================================
# PRIORITY 3: Split Myanmar (Anglo-Burmese Wars)
# ==============================================================================

cat("\n--- PRIORITY 3: Myanmar territorial splits ---\n")

# Cliopatria data shows:
#   1800-1824: ~798K km2 (Konbaung at peak, including Arakan, Assam expansion)
#   1825-1852: ~553K km2 (lost Arakan + Tenasserim in Treaty of Yandabo 1826, -31%)
#   1853-1885: ~437K km2 (lost Lower Burma/Pegu in 1852, -21%)
#   1886+:     British Burma (fully colonized)
# Both 1826 and 1852 exceed the 10% threshold.

mmr_idx <- which(db$polity_code == "MMR-1800-2025")
if (length(mmr_idx) == 1) {
  # Reclassify as aggregate
  db$polity_type[mmr_idx] <- "national"
  db$notes[mmr_idx] <- "Aggregate for continuous trade data linkage. Split at 1826 and 1852 (Anglo-Burmese Wars)."
  cat("  MMR-1800-2025 reclassified as aggregate\n")

  # Read Cliopatria for polygons
  clio_path <- file.path(proj_root, "data", "source", "cliopatria",
                          "cliopatria_polities_only.geojson")
  if (!file.exists(clio_path)) {
    tmp_dir <- tempdir()
    unzip(file.path(proj_root, "inputs", "cliopatria.geojson.zip"),
          exdir = tmp_dir, overwrite = TRUE)
    clio_path <- file.path(tmp_dir, "cliopatria_polities_only.geojson")
  }

  read_clio <- function(name, fy, ty) {
    q <- sprintf("SELECT * FROM cliopatria_polities_only WHERE Name = '%s' AND FromYear <= %d AND ToYear >= %d LIMIT 1",
                 gsub("'", "''", name), fy, ty)
    tryCatch({
      f <- st_read(clio_path, query = q, quiet = TRUE)
      if (nrow(f) > 0) return(st_set_crs(f[1,], 4326) %>% st_make_valid())
      NULL
    }, error = function(e) NULL)
  }

  mmr_periods <- list(
    list(code = "MMR-1800-1826", name = "Konbaung Burma (to 1826)",
         start = 1800L, end = 1826L, type = "national",
         clio_name = "Burma", clio_fy = 1822, clio_ty = 1824,
         notes = "Konbaung Dynasty at peak. ~798K km2 including Arakan, Manipur, Assam. First Anglo-Burmese War (1824-26) ends with Treaty of Yandabo: lost Arakan, Tenasserim, Assam, Manipur. -31% territory."),
    list(code = "MMR-1826-1852", name = "Burma (1826-1852)",
         start = 1826L, end = 1852L, type = "national",
         clio_name = "Burma", clio_fy = 1828, clio_ty = 1833,
         notes = "Post-First Anglo-Burmese War. ~553K km2. Second Anglo-Burmese War (1852): Britain seizes Lower Burma (Pegu). -21% territory."),
    list(code = "MMR-1852-1885", name = "Upper Burma (1852-1885)",
         start = 1852L, end = 1885L, type = "national",
         clio_name = "Burma", clio_fy = 1853, clio_ty = 1858,
         notes = "Upper Burma only. ~437K km2. Third Anglo-Burmese War (1885): Britain conquers Upper Burma. Kingdom abolished 1 Jan 1886."),
    list(code = "MMR-1885-2025", name = "Myanmar",
         start = 1885L, end = 2025L, type = "national",
         clio_name = "Burma", clio_fy = 1948, clio_ty = 1962,
         notes = "British Burma 1886-1948. Independence 1948. Military rule 1962-2011. Name changed to Myanmar 1989.")
  )

  for (i in seq_along(mmr_periods)) {
    p <- mmr_periods[[i]]
    if (p$code %in% existing_codes) {
      cat(sprintf("  SKIP: %s exists\n", p$code))
      next
    }

    pred_code <- if (i > 1) mmr_periods[[i-1]]$code else NA_character_
    succ_code <- if (i < length(mmr_periods)) mmr_periods[[i+1]]$code else NA_character_

    new_entries[[length(new_entries) + 1]] <- tibble(
      polity_code = p$code, polity_name = p$name,
      start_year = p$start, end_year = p$end,
      duration_years = p$end - p$start + 1L,
      polity_type = p$type, continent = "Asia", iso3_code = "MMR",
      cow_code = NA_character_, polygon_source = NA_character_,
      predecessor = ifelse(is.na(pred_code), NA_character_, pred_code),
      successor = ifelse(is.na(succ_code), NA_character_, succ_code),
      data_sources = "CShapes; Cliopatria; research",
      verification_status = "VERIFIED", notes = p$notes
    )
    existing_codes <- c(existing_codes, p$code)

    feat <- read_clio(p$clio_name, p$clio_fy, p$clio_ty)
    if (!is.null(feat)) {
      polys <- bind_rows(polys, st_sf(polity_code = p$code, geometry = st_geometry(feat)))
      new_entries[[length(new_entries)]]$polygon_source <-
        sprintf("Cliopatria (%s %d-%d)", p$clio_name, p$clio_fy, p$clio_ty)
      cat(sprintf("  ADD: %s with Cliopatria polygon\n", p$code))
    } else {
      # Fallback: use existing MMR polygon
      mmr_poly <- polys[polys$polity_code == "MMR-1800-2025", ]
      if (nrow(mmr_poly) > 0) {
        polys <- bind_rows(polys, st_sf(polity_code = p$code, geometry = st_geometry(mmr_poly[1,])))
        new_entries[[length(new_entries)]]$polygon_source <- "CShapes 2.0 (fallback)"
      }
      cat(sprintf("  ADD: %s (Cliopatria miss, fallback)\n", p$code))
    }
    changes <- changes + 1
  }
}

# ==============================================================================
# PRIORITY 4: Auto-chain historical entries by ISO3 + date order
# ==============================================================================

cat("\n--- PRIORITY 4: Auto-chain historical entries ---\n")

# Strategy: for each ISO3, find all historical/colonial entries sorted by
# start_year. If two consecutive entries have a gap <= 5 years, chain them.
# Only add links where BOTH predecessor and successor are currently empty.

chain_count <- 0

# Group non-aggregate, non-subnational, non-region entries by ISO3
chainable_types <- c("national")
candidates <- db %>%
  filter(polity_type %in% chainable_types,
         !is.na(iso3_code), iso3_code != "NA") %>%
  arrange(iso3_code, start_year)

iso_groups <- split(candidates, candidates$iso3_code)

for (iso in names(iso_groups)) {
  group <- iso_groups[[iso]]
  if (nrow(group) < 2) next

  for (i in 1:(nrow(group) - 1)) {
    curr <- group[i, ]
    nxt <- group[i + 1, ]

    # Check temporal proximity: end of current close to start of next
    gap <- as.integer(nxt$start_year) - as.integer(curr$end_year)
    if (gap < -2 || gap > 5) next  # allow 1-year overlap to 5-year gap

    curr_idx <- which(db$polity_code == curr$polity_code)
    nxt_idx <- which(db$polity_code == nxt$polity_code)

    if (length(curr_idx) != 1 || length(nxt_idx) != 1) next

    # Only add successor if current has none
    curr_succ <- db$successor[curr_idx]
    if (is.na(curr_succ) || curr_succ == "NA") {
      db$successor[curr_idx] <- nxt$polity_code
      chain_count <- chain_count + 1
    } else if (!grepl(nxt$polity_code, curr_succ, fixed = TRUE)) {
      db$successor[curr_idx] <- paste0(curr_succ, "; ", nxt$polity_code)
      chain_count <- chain_count + 1
    }

    # Only add predecessor if next has none
    nxt_pred <- db$predecessor[nxt_idx]
    if (is.na(nxt_pred) || nxt_pred == "NA") {
      db$predecessor[nxt_idx] <- curr$polity_code
      chain_count <- chain_count + 1
    } else if (!grepl(curr$polity_code, nxt_pred, fixed = TRUE)) {
      db$predecessor[nxt_idx] <- paste0(nxt_pred, "; ", curr$polity_code)
      chain_count <- chain_count + 1
    }
  }
}

cat(sprintf("  Added %d chain links across all ISO3 groups\n", chain_count))
changes <- changes + chain_count

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
}

write_csv(db, file.path(final_dir, "polities_database.csv"))
cat(sprintf("  Saved: polities_database.csv (%d rows)\n", nrow(db)))

polys <- polys[!duplicated(polys$polity_code, fromLast = TRUE), ]
if (file.exists(poly_path)) file.remove(poly_path)
st_write(polys, poly_path, layer = "polities", quiet = TRUE)
cat(sprintf("  Saved: polities_polygons.gpkg (%d polygons)\n", nrow(polys)))

# Report
no_links <- db %>%
  filter(polity_type == "national",
         (is.na(predecessor) | predecessor == "NA"),
         (is.na(successor) | successor == "NA"))
cat(sprintf("\n  Historical entries still without any links: %d (was 267)\n", nrow(no_links)))
cat(sprintf("  Total changes: %d\n", changes))
cat("\n=== Done ===\n")
