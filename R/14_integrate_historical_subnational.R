# ==============================================================================
# WHEP Polities - Integrate Historical Subnational Polygons
# ==============================================================================
# Sources:
#   1. USAboundaries R package (rOpenSci) — US states/territories 1800-1959
#      Data: Newberry Library Atlas of Historical County Boundaries
#      License: CC BY-NC-SA 2.5 (historical); CC0 per Newberry clarification
#      URL: https://github.com/ropensci/USAboundaries
#
#   2. geobr R package (IPEA/IBGE) — Brazilian states 1872-1988
#      Data: IBGE Evolucao da Divisao Territorial do Brasil
#      License: MIT (code); public domain (IBGE data)
#      URL: https://github.com/ipeaGIT/geobr
#
#   3. mapSpain R package (rOpenSpain) — Spanish provinces (current = 1833+)
#      Data: IGN CartoBase SIANE / Eurostat GISCO
#      License: CC BY 4.0
#      URL: https://ropenspain.github.io/mapSpain/
#
# This script:
#   1. Extracts US state/territory boundaries at key historical dates (1800-1959)
#      to extend USA subnational coverage backward from existing GADM 1959-2025
#   2. Extracts Brazilian state boundaries at historical census dates (1872-1980)
#      to extend Brazil subnational coverage backward from existing GADM 1988-2025
#   3. Extracts Spanish province boundaries as new subnational entries
#   4. Saves all polygons to GeoPackages
#   5. Adds entries to polities_database.csv
#   6. Updates knowledge graph
# ==============================================================================

# Source setup
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

library(USAboundaries)
library(geobr)
library(mapSpain)

cat("=== Integrating Historical Subnational Polygons ===\n\n")

# Load current database
db <- read_csv(
  file.path(final_dir, "polities_database.csv"),
  show_col_types = FALSE
)
cat("Current database:", nrow(db), "entries\n\n")

all_new_entries <- list()
all_new_polygons <- list()

# ==============================================================================
# PART 1: UNITED STATES (1800-1959)
# ==============================================================================
cat("--- PART 1: United States Historical States/Territories ---\n\n")

# Strategy: Use the 1800 snapshot to capture all states/territories at that date.
# Then 1959 is already covered by GADM. We need to pick an appropriate start date
# for each state. The USAboundaries data gives us the exact admission date.
#
# Approach: Extract US states at 1800-01-01. For each state, the boundary already
# encodes start/end dates. We create one entry per state covering its period from
# statehood (or 1800, whichever is later) until 1959 (where GADM picks up).
# For territories that became states before 1959, we create the territory entry.

# Get all states at 1959-01-03 (just before Alaska/Hawaii, last GADM start)
# to understand what we already have
existing_us <- db |>
  filter(grepl("^US", polity_code), polity_type == "subnational")
existing_us_names <- existing_us$polity_name
cat("Existing US subnational entries:", nrow(existing_us), "\n")

# Get state boundaries at key dates to understand temporal evolution
# Use 1800-01-01 as our starting point
us_1800 <- us_states(map_date = "1800-01-01")
cat("States/territories in 1800:", nrow(us_1800), "\n")

# Get the full state history: extract at a late date to get all states
# with their full metadata
us_all <- us_states(map_date = "1958-12-31")  # just before Alaska/Hawaii
cat("States/territories in 1958:", nrow(us_all), "\n")

# For the pre-1959 period, we want entries for states that existed.
# Each existing GADM entry starts at 1959. We need to create entries
# covering admission_date to 1958 (or 1800 to 1958 for original states).
#
# The polity code pattern for existing entries: US + 2-letter state code.
# For historical entries, we use the same prefix but with historical dates.

# Build mapping of state abbreviations to their admission years
# Using USAboundaries terr_type to distinguish states from territories
us_snapshots <- list()
for (yr in c(1800, 1820, 1850, 1870, 1900, 1912, 1920, 1945, 1958)) {
  date_str <- paste0(yr, "-07-04")
  s <- us_states(map_date = date_str)
  s$snapshot_year <- yr
  us_snapshots[[as.character(yr)]] <- s
}

# Find earliest appearance of each state/territory
state_first_seen <- list()
for (snap_name in names(us_snapshots)) {
  s <- us_snapshots[[snap_name]]
  for (i in seq_len(nrow(s))) {
    nm <- s$name[i]
    yr <- s$snapshot_year[i]
    if (is.null(state_first_seen[[nm]]) || yr < state_first_seen[[nm]]$year) {
      state_first_seen[[nm]] <- list(year = yr, type = s$terr_type[i])
    }
  }
}

# Use the 1958 snapshot as our polygon source (most current pre-GADM boundaries)
us_final <- us_snapshots[["1958"]]
# Ensure WGS84
us_final <- st_transform(us_final, 4326)

# Make valid geometries
us_final <- st_make_valid(us_final)

# Create polity entries for each state in the 1958 snapshot
# These cover from their admission (or 1800) to 1958
us_entries <- data.frame(stringsAsFactors = FALSE)
us_polys <- list()

# Standard US state abbreviations (from USAboundaries data)
for (i in seq_len(nrow(us_final))) {
  state_name <- us_final$name[i]
  state_abbr <- us_final$state_abbr[i]
  terr_type  <- us_final$terr_type[i]

  if (is.na(state_abbr) || state_abbr == "") next

  # Determine start year
  # The start_date field gives us when this specific boundary configuration began
  # For our purposes, we want the statehood/territory start
  first_info <- state_first_seen[[state_name]]
  start_yr <- if (!is.null(first_info)) first_info$year else 1800L

  # Build polity code: US + 2-letter abbreviation + dates
  code <- paste0("US", state_abbr, "-", start_yr, "-1958")

  # Check this doesn't conflict with existing entries
  if (code %in% db$polity_code) next

  # Determine polity name suffix
  name_suffix <- if (terr_type == "State") "(State)" else "(Territory)"
  pname <- paste0(state_name, " ", name_suffix)

  entry <- data.frame(
    polity_code = code,
    polity_name = pname,
    start_year = as.integer(start_yr),
    end_year = 1958L,
    duration_years = 1958L - as.integer(start_yr) + 1L,
    polity_type = "subnational",
    continent = "North America",
    iso3_code = "USA",
    cow_code = NA_real_,
    polygon_source = "USAboundaries/Newberry (subnational)",
    predecessor = NA_character_,
    successor = paste0("US", state_abbr, "-1959-2025"),
    data_sources = "USAboundaries",
    verification_status = "VERIFIED",
    notes = paste0(
      "Parent: USA-1800-1959; ",
      "Source: Newberry Library Atlas of Historical County Boundaries; ",
      "Snapshot: 1958-07-04; ",
      "Type: ", terr_type
    ),
    stringsAsFactors = FALSE
  )

  us_entries <- rbind(us_entries, entry)
  us_polys[[code]] <- us_final[i, ]
}

# Also update the existing GADM entries to add predecessor references
# (we'll do this after all entries are collected)

cat("Created", nrow(us_entries), "US historical subnational entries\n")

# Save US polygons to GeoPackage
if (nrow(us_entries) > 0) {
  us_sf <- do.call(rbind, lapply(names(us_polys), function(code) {
    p <- us_polys[[code]]
    st_sf(
      polity_code = code,
      polity_name = us_entries$polity_name[us_entries$polity_code == code],
      geometry = st_geometry(p)
    )
  }))
  us_sf <- st_set_crs(us_sf, 4326)

  gpkg_path <- file.path(geodata_dir, "us_historical_states.gpkg")
  st_write(us_sf, gpkg_path, layer = "us_states_1800_1958",
           delete_layer = TRUE, quiet = TRUE)
  cat("Saved US polygons to", gpkg_path, "\n")
  all_new_polygons[["us"]] <- us_sf
}

all_new_entries[["us"]] <- us_entries
cat("\n")

# ==============================================================================
# PART 2: BRAZIL (1872-1988)
# ==============================================================================
cat("--- PART 2: Brazil Historical States/Provinces ---\n\n")

# Existing entries cover 1988-2025 with codes like BRAC-1988-2025
# We extend backward using geobr snapshots

# Available years in geobr for states:
# 1872, 1900, 1911, 1920, 1933, 1940, 1950, 1960, 1970, 1980, 1991, 2000, ...
# We want 1872 to 1980 (1991 and later overlap with or are close to our 1988 GADM)

# Strategy: Use the 1872 snapshot as the earliest, then pick a snapshot close to
# our GADM start (1988). We'll use 1980 as the end date since 1988 GADM picks up.
# The 1872 snapshot gives us the provinces as they existed for the first census.

# For simplicity, use a single period per state: from when it first appears in
# geobr to 1987 (one year before GADM 1988).

# First, let's check what provinces/states existed at each key date
br_years <- c(1872, 1900, 1920, 1940, 1960, 1980)
br_all_states <- list()

for (yr in br_years) {
  b <- tryCatch(
    read_state(year = yr, showProgress = FALSE),
    error = function(e) NULL
  )
  if (!is.null(b)) {
    b$snapshot_year <- yr
    br_all_states[[as.character(yr)]] <- b
    cat("  geobr", yr, ":", nrow(b), "states\n")
  }
}

# Use 1872 as the start for most provinces (they existed since then)
# Use the 1980 snapshot as our polygon source (closest to GADM 1988)
br_1980 <- br_all_states[["1980"]]
br_1980 <- st_transform(br_1980, 4326)
br_1980 <- st_make_valid(br_1980)

# Find which states existed in 1872
br_1872 <- br_all_states[["1872"]]
br_1872_names <- br_1872$name_state

# Existing Brazil subnational entries
existing_br <- db |>
  filter(grepl("^BR", polity_code), polity_type == "subnational")
cat("\nExisting Brazil subnational entries:", nrow(existing_br), "\n")

# Extract 2-letter state abbreviation from existing codes (e.g., BRAC -> AC)
existing_br_abbrs <- substr(existing_br$polity_code, 3, 4)

# Build mapping from geobr state names to 2-letter codes
# We need to match geobr names to our existing GADM-based abbreviations
# Let's get the 2020 geobr data which has abbrev_state
br_modern <- read_state(year = 2020, showProgress = FALSE)

# Create a name-to-abbrev mapping with case-normalized matching
# geobr names vary across years (e.g., "do" vs "Do", "de" vs "De",
# "Território de X" vs "X", "Brasília" vs "Distrito Federal")
br_name_abbrev <- setNames(br_modern$abbrev_state, br_modern$name_state)

# Add normalized-case fallback mapping
br_name_lower <- setNames(br_modern$abbrev_state, tolower(br_modern$name_state))

# Manual overrides for known name differences between 1980 and 2020 geobr
br_name_override <- c(
  "Amazonas"                     = "AM",
  "Brasília"                     = "DF",
  "Mato Grosso do Sul"           = "MS",
  "Rio de Janeiro"               = "RJ",
  "Rio Grande do Norte"          = "RN",
  "Rio Grande do Sul"            = "RS",
  "Território de Rondônia"       = "RO",
  "Território de Roraima"        = "RR",
  "Território do Amapá"          = "AP",
  "Território de Fernando de Noronha" = NA_character_,  # Skip: tiny island, absorbed into PE
  "Litígio PI/CE"                = NA_character_  # Skip: disputed area, not a state
)

# Also check 1872 names that may differ
# 1872 used province names that mostly match modern state names
cat("\n1872 province names:\n")
cat(paste(sort(br_1872_names), collapse = "\n"), "\n\n")

# For historical entries, we use the 1980 snapshot boundaries
br_entries <- data.frame(stringsAsFactors = FALSE)
br_polys <- list()

# Determine first appearance year for each state
state_first_year <- list()
for (yr_name in names(br_all_states)) {
  s <- br_all_states[[yr_name]]
  yr <- as.integer(yr_name)
  for (nm in s$name_state) {
    if (is.null(state_first_year[[nm]]) || yr < state_first_year[[nm]]) {
      state_first_year[[nm]] <- yr
    }
  }
}

for (i in seq_len(nrow(br_1980))) {
  state_name <- br_1980$name_state[i]

  # Try direct match, then override, then case-insensitive
  abbrev <- br_name_abbrev[state_name]
  if (is.na(abbrev) && state_name %in% names(br_name_override)) {
    abbrev <- br_name_override[state_name]
  }
  if (is.na(abbrev)) {
    abbrev <- br_name_lower[tolower(state_name)]
  }

  if (is.na(abbrev)) {
    cat("  Skipping:", state_name, "(no match or excluded)\n")
    next
  }

  # Determine start year (first appearance in geobr)
  start_yr <- state_first_year[[state_name]]
  if (is.null(start_yr)) start_yr <- 1872L
  start_yr <- as.integer(start_yr)

  # End year is 1987 (year before GADM 1988)
  end_yr <- 1987L

  # Build polity code
  code <- paste0("BR", abbrev, "-", start_yr, "-", end_yr)

  # Check for conflicts
  if (code %in% db$polity_code) next

  # Polity name
  suffix <- if (start_yr <= 1889) "(Province)" else "(State)"
  pname <- paste(state_name, suffix)

  # Determine parent polity
  # Brazil 1822-1988: BRA-1822-2025 or similar
  parent <- "BRA-1822-2025"

  entry <- data.frame(
    polity_code = code,
    polity_name = pname,
    start_year = start_yr,
    end_year = end_yr,
    duration_years = end_yr - start_yr + 1L,
    polity_type = "subnational",
    continent = "South America",
    iso3_code = "BRA",
    cow_code = NA_real_,
    polygon_source = "geobr/IBGE (subnational)",
    predecessor = NA_character_,
    successor = paste0("BR", abbrev, "-1988-2025"),
    data_sources = "geobr",
    verification_status = "VERIFIED",
    notes = paste0(
      "Parent: ", parent, "; ",
      "Source: IBGE Evolucao da Divisao Territorial; ",
      "Snapshot: 1980; ",
      "First census appearance: ", start_yr
    ),
    stringsAsFactors = FALSE
  )

  br_entries <- rbind(br_entries, entry)
  br_polys[[code]] <- br_1980[i, ]
}

cat("Created", nrow(br_entries), "Brazil historical subnational entries\n")

# Save Brazil polygons
if (nrow(br_entries) > 0) {
  br_sf <- do.call(rbind, lapply(names(br_polys), function(code) {
    p <- br_polys[[code]]
    st_sf(
      polity_code = code,
      polity_name = br_entries$polity_name[br_entries$polity_code == code],
      geometry = st_geometry(p)
    )
  }))
  br_sf <- st_set_crs(br_sf, 4326)

  gpkg_path <- file.path(geodata_dir, "brazil_historical_states.gpkg")
  st_write(br_sf, gpkg_path, layer = "brazil_states_1872_1987",
           delete_layer = TRUE, quiet = TRUE)
  cat("Saved Brazil polygons to", gpkg_path, "\n")
  all_new_polygons[["br"]] <- br_sf
}

all_new_entries[["br"]] <- br_entries
cat("\n")

# ==============================================================================
# PART 3: SPAIN (provinces, stable since 1833)
# ==============================================================================
cat("--- PART 3: Spain Provinces ---\n\n")

# Spain's 50 provinces have been unchanged since the 1833 Javier de Burgos reform.
# Current boundaries serve as a valid proxy for 1833-present.
# We create subnational entries with start_year = 1833 covering to 2025.

# Get province boundaries from mapSpain
esp_prov <- esp_get_prov_siane()
esp_prov <- st_transform(esp_prov, 4326)
esp_prov <- st_make_valid(esp_prov)
cat("Spain provinces from mapSpain:", nrow(esp_prov), "\n")

# Map provinces to WHEP codes: ES + 2-letter province code
# Use ISO 3166-2:ES codes (cpro is the INE 2-digit code)
# We'll use a 2-letter abbreviation derived from the province name

# mapSpain provides iso2.prov.code which is like "ES-A", "ES-AB" etc.
# We need a consistent 2-letter code. Let's use the INE code (cpro, 2-digit numeric)
# padded to create unique identifiers

esp_entries <- data.frame(stringsAsFactors = FALSE)
esp_polys <- list()

# Determine parent polity
# Spain sovereign entries - find the one active in 1833-2025
esp_parent <- db |>
  filter(iso3_code == "ESP", polity_type == "sovereign", end_year == 2025) |>
  pull(polity_code) |>
  first()
if (is.na(esp_parent) || length(esp_parent) == 0) {
  esp_parent <- "ESP-1975-2025"
}
cat("Spain parent polity:", esp_parent, "\n")

for (i in seq_len(nrow(esp_prov))) {
  prov_name <- esp_prov$prov.shortname.es[i]
  prov_ine  <- esp_prov$cpro[i]  # 2-digit INE code (01-52)

  # Build polity code: ES + INE code (2 digits)
  code <- paste0("ES", prov_ine, "-1833-2025")

  # Check for conflicts
  if (code %in% db$polity_code) next

  pname <- paste0(prov_name, " (Province)")

  # Get English name if available
  en_name <- esp_prov$prov.shortname.en[i]

  # Get autonomous community
  ccaa <- esp_prov$nuts2.name[i]

  entry <- data.frame(
    polity_code = code,
    polity_name = pname,
    start_year = 1833L,
    end_year = 2025L,
    duration_years = 2025L - 1833L + 1L,
    polity_type = "subnational",
    continent = "Europe",
    iso3_code = "ESP",
    cow_code = NA_real_,
    polygon_source = "mapSpain/IGN (subnational)",
    predecessor = NA_character_,
    successor = NA_character_,
    data_sources = "mapSpain",
    verification_status = "VERIFIED",
    notes = paste0(
      "Parent: ", esp_parent, "; ",
      "Source: IGN SIANE via mapSpain; ",
      "INE code: ", prov_ine, "; ",
      "CCAA: ", ccaa, "; ",
      "Provinces stable since 1833 Burgos reform",
      if (!is.na(en_name) && en_name != prov_name) paste0("; EN: ", en_name) else ""
    ),
    stringsAsFactors = FALSE
  )

  esp_entries <- rbind(esp_entries, entry)
  esp_polys[[code]] <- esp_prov[i, ]
}

cat("Created", nrow(esp_entries), "Spain province subnational entries\n")

# Save Spain polygons
if (nrow(esp_entries) > 0) {
  esp_sf <- do.call(rbind, lapply(names(esp_polys), function(code) {
    p <- esp_polys[[code]]
    st_sf(
      polity_code = code,
      polity_name = esp_entries$polity_name[esp_entries$polity_code == code],
      geometry = st_geometry(p)
    )
  }))
  esp_sf <- st_set_crs(esp_sf, 4326)

  gpkg_path <- file.path(geodata_dir, "spain_provinces.gpkg")
  st_write(esp_sf, gpkg_path, layer = "spain_provinces_1833_2025",
           delete_layer = TRUE, quiet = TRUE)
  cat("Saved Spain polygons to", gpkg_path, "\n")
  all_new_polygons[["esp"]] <- esp_sf
}

all_new_entries[["esp"]] <- esp_entries
cat("\n")

# ==============================================================================
# PART 4: Add all entries to database
# ==============================================================================
cat("--- PART 4: Updating Database ---\n\n")

new_entries <- do.call(rbind, all_new_entries)
cat("Total new entries:", nrow(new_entries), "\n")
cat("  USA:", nrow(all_new_entries[["us"]]), "\n")
cat("  Brazil:", nrow(all_new_entries[["br"]]), "\n")
cat("  Spain:", nrow(all_new_entries[["esp"]]), "\n")

# Remove any duplicates with existing codes
conflicts <- new_entries$polity_code[new_entries$polity_code %in% db$polity_code]
if (length(conflicts) > 0) {
  cat("  WARNING: Removing", length(conflicts), "conflicting codes\n")
  new_entries <- new_entries[!new_entries$polity_code %in% db$polity_code, ]
}

db_updated <- bind_rows(db, new_entries)
write_csv(db_updated, file.path(final_dir, "polities_database.csv"))
cat("\nDatabase updated:", nrow(db), "->", nrow(db_updated), "entries\n")

# Count subnational
n_sub <- sum(db_updated$polity_type == "subnational")
cat("Total subnational entries:", n_sub, "\n")

# ==============================================================================
# PART 5: Update knowledge graph
# ==============================================================================
cat("\n--- PART 5: Updating Knowledge Graph ---\n\n")

nodes_path <- file.path(analysis_dir, "knowledge_graph_nodes.csv")
edges_path <- file.path(analysis_dir, "knowledge_graph_edges.csv")

if (file.exists(nodes_path) && file.exists(edges_path)) {
  nodes <- read_csv(nodes_path, show_col_types = FALSE)
  edges <- read_csv(edges_path, show_col_types = FALSE)

  # Add new nodes
  new_nodes <- new_entries |>
    transmute(
      id = polity_code,
      label = polity_name,
      type = polity_type,
      continent = continent,
      start_year = start_year,
      end_year = end_year,
      degree = 2L  # continent + subregion_of edges
    )
  nodes <- bind_rows(nodes, new_nodes)

  # Add continent edges
  new_edges_continent <- new_entries |>
    transmute(
      source = polity_code,
      target = continent,
      relation = "located_in_continent",
      weight = 1L
    )

  # Add subregion_of edges (child -> parent)
  parent_map <- c(
    "USA" = "USA-1959-2025",
    "BRA" = "BRA-1822-2025",
    "ESP" = esp_parent
  )

  # Determine parent for each entry based on iso3_code
  new_edges_subregion <- new_entries |>
    mutate(
      parent = case_when(
        iso3_code == "USA" ~ "USA-1959-2025",
        iso3_code == "BRA" ~ "BRA-1822-2025",
        iso3_code == "ESP" ~ esp_parent,
        TRUE ~ NA_character_
      )
    ) |>
    filter(!is.na(parent)) |>
    transmute(
      source = polity_code,
      target = parent,
      relation = "subregion_of",
      weight = 1L
    )

  edges <- bind_rows(edges, new_edges_continent, new_edges_subregion)

  # Update continent degree counts
  for (cont in unique(new_entries$continent)) {
    cont_idx <- which(nodes$id == cont)
    if (length(cont_idx) == 1) {
      nodes$degree[cont_idx] <- sum(edges$source == cont | edges$target == cont)
    }
  }

  write_csv(nodes, nodes_path)
  write_csv(edges, edges_path)
  cat("Added", nrow(new_nodes), "nodes and",
      nrow(new_edges_continent) + nrow(new_edges_subregion), "edges\n")
  cat("Knowledge graph:", nrow(nodes), "nodes,", nrow(edges), "edges\n")
}

# ==============================================================================
# PART 6: Summary
# ==============================================================================
cat("\n=== Summary ===\n")
cat("USA: Added", nrow(all_new_entries[["us"]]),
    "historical subnational entries (1800-1958)\n")
cat("  Source: Newberry Library via USAboundaries R package\n")
cat("  Polygons: data/geodata/us_historical_states.gpkg\n\n")

cat("Brazil: Added", nrow(all_new_entries[["br"]]),
    "historical subnational entries (1872-1987)\n")
cat("  Source: IBGE via geobr R package\n")
cat("  Polygons: data/geodata/brazil_historical_states.gpkg\n\n")

cat("Spain: Added", nrow(all_new_entries[["esp"]]),
    "province subnational entries (1833-2025)\n")
cat("  Source: IGN SIANE via mapSpain R package\n")
cat("  Polygons: data/geodata/spain_provinces.gpkg\n\n")

cat("Database:", nrow(db_updated), "total entries,", n_sub, "subnational\n")
cat("\n=== Done ===\n")
