# ==============================================================================
# Add Present-Day Subnational Polity Entries
# ==============================================================================
# Adds GADM 3.6 admin-1 entries for the 6 largest countries by area:
# Russia (83), USA (51), China (31), Brazil (27), Canada (13), Australia (11)
# Total: 216 new subnational entries
# ==============================================================================

source("R/00_setup.R")

# --- Configuration ---

country_config <- tribble(
  ~iso3,
  ~start_year,
  ~continent,
  ~parent_polity,
  "USA",
  1959L,
  "North America",
  "USA-1959-2025",
  "CAN",
  1999L,
  "North America",
  "CAN-1948-2025",
  "BRA",
  1988L,
  "South America",
  "BRA-1909-2025",
  "AUS",
  1901L,
  "Oceania",
  "AUS-1901-2025",
  "CHN",
  1997L,
  "Asia",
  "F351-1950-2025",
  "RUS",
  1993L,
  "Europe",
  "RUS-2014-2025"
)

hasc_fixes <- c("Moscow City" = "RU.MW")

# --- Load data ---

cat("Loading data...\n")
polities <- read_csv(
  file.path(final_dir, "polities_database.csv"),
  show_col_types = FALSE
)
gadm <- st_read(gadm_path, layer = "level1", quiet = TRUE)

cat("  Existing polities:", nrow(polities), "\n")
cat("  GADM admin-1 units:", nrow(gadm), "\n")

existing_codes <- polities$polity_code

# --- Load existing polygons ---

poly_path <- file.path(geodata_dir, "polities_polygons.gpkg")
if (file.exists(poly_path)) {
  existing_polys <- st_read(poly_path, quiet = TRUE)
  cat("  Existing polygons:", nrow(existing_polys), "\n")
} else {
  existing_polys <- NULL
  cat("  No existing polygon file found\n")
}

# --- Generate subnational entries ---

cat("\nGenerating subnational entries...\n")
new_entries <- list()
new_polys <- list()

for (i in seq_len(nrow(country_config))) {
  cfg <- country_config[i, ]
  country_gadm <- gadm %>%
    filter(GID_0 == cfg$iso3) %>%
    arrange(NAME_1)

  cat(sprintf("\n  %s: %d admin-1 units\n", cfg$iso3, nrow(country_gadm)))

  for (j in seq_len(nrow(country_gadm))) {
    row <- country_gadm[j, ]
    name <- row$NAME_1
    eng_type <- row$ENGTYPE_1
    gid <- row$GID_1
    hasc <- row$HASC_1

    # Fix missing HASC codes
    if (is.na(hasc)) {
      if (name %in% names(hasc_fixes)) {
        hasc <- hasc_fixes[[name]]
      } else {
        gid_num <- str_extract(gid, "(?<=\\.)[0-9]+")
        hasc <- paste0(substr(cfg$iso3, 1, 2), ".", gid_num)
        cat(sprintf("    WARNING: No HASC for %s, using %s\n", name, hasc))
      }
    }

    code_prefix <- str_replace(hasc, "\\.", "")
    polity_code <- sprintf("%s-%d-2025", code_prefix, cfg$start_year)

    if (polity_code %in% existing_codes) {
      cat(sprintf("    COLLISION: %s (%s) -- skipping\n", polity_code, name))
      next
    }

    polity_name <- sprintf("%s (%s)", name, eng_type)

    new_entries[[length(new_entries) + 1]] <- tibble(
      polity_code = polity_code,
      polity_name = polity_name,
      start_year = cfg$start_year,
      end_year = 2025L,
      duration_years = 2025L - cfg$start_year + 1L,
      polity_type = "subnational",
      continent = cfg$continent,
      iso3_code = cfg$iso3,
      cow_code = NA_character_,
      polygon_source = "GADM 3.6 (subnational)",
      predecessor = NA_character_,
      successor = NA_character_,
      data_sources = "GADM",
      verification_status = "VERIFIED",
      notes = sprintf("Parent: %s; GADM GID: %s", cfg$parent_polity, gid)
    )

    existing_codes <- c(existing_codes, polity_code)

    geom <- st_geometry(row)
    if (!is.na(st_is_empty(geom)) && !st_is_empty(geom)) {
      new_polys[[length(new_polys) + 1]] <- st_sf(
        polity_code = polity_code,
        polity_name = polity_name,
        geometry = geom
      )
    }

    cat(sprintf("    %-20s %s\n", polity_code, polity_name))
  }
}

# --- Summary ---

new_df <- bind_rows(new_entries)
new_poly_sf <- bind_rows(new_polys) %>% st_set_crs(4326)

cat(sprintf(
  "\n%s\nTotal new entries: %d\nTotal new polygons: %d\n",
  strrep("=", 60),
  nrow(new_df),
  nrow(new_poly_sf)
))

iso_summary <- new_df %>% count(iso3_code)
walk2(
  iso_summary$iso3_code,
  iso_summary$n,
  ~ cat(sprintf("  %s: %d\n", .x, .y))
)

# --- Save updated CSV ---

updated <- bind_rows(polities, new_df)
write_csv(updated, file.path(final_dir, "polities_database.csv"))
cat(sprintf(
  "\nUpdated polities_database.csv: %d -> %d entries\n",
  nrow(polities),
  nrow(updated)
))

# --- Save updated polygons ---

if (nrow(new_poly_sf) > 0) {
  if (!is.null(existing_polys)) {
    cols <- intersect(names(existing_polys), names(new_poly_sf))
    combined <- bind_rows(existing_polys[, cols], new_poly_sf[, cols])
  } else {
    combined <- new_poly_sf
  }
  if (file.exists(poly_path)) {
    file.remove(poly_path)
  }
  st_write(combined, poly_path, layer = "polities", quiet = TRUE)
  cat(sprintf(
    "Updated polities_polygons.gpkg: %d total polygons\n",
    nrow(combined)
  ))
}

# --- Save report ---

write_csv(new_df, file.path(analysis_dir, "subnational_additions_report.csv"))
cat("Saved report: data/analysis/subnational_additions_report.csv\n\nDone!\n")
