# ==============================================================================
# Consolidated Analysis Plots
# ==============================================================================
# Covers: polygon quality, temporal evolution, ISO collision analysis,
# subnational assessment, and coverage summary
# Produces plots in data/analysis/plots/
# ==============================================================================

source("R/00_setup.R")

# --- Load data ---

cat("Loading data...\n")
df <- read_csv(file.path(final_dir, "polities_database.csv"), show_col_types = FALSE)
cat("  Polities:", nrow(df), "\n")

poly_path <- file.path(geodata_dir, "polities_polygons.gpkg")
has_polys <- file.exists(poly_path)
if (has_polys) {
  polys <- st_read(poly_path, quiet = TRUE) %>% st_make_valid()
  cat("  Polygons:", nrow(polys), "\n")
}

# ==============================================================================
# 1. Temporal Evolution
# ==============================================================================

cat("\n--- Temporal Evolution ---\n")

# Active polities per year
years <- 1800:2025
non_sub <- df %>% filter(!polity_type %in% c("region", "subnational"))

active_counts <- tibble(year = years) %>%
  rowwise() %>%
  mutate(count = sum(non_sub$start_year <= year & non_sub$end_year >= year)) %>%
  ungroup()

p_temporal <- ggplot(active_counts, aes(x = year, y = count)) +
  geom_line(color = "#2196F3", linewidth = 1) +
  geom_vline(xintercept = c(1886, 1914, 1945, 1991), linetype = "dashed", alpha = 0.4) +
  annotate("text", x = c(1886, 1914, 1945, 1991), y = max(active_counts$count),
           label = c("CShapes\nstart", "WWI", "WWII", "USSR\nfall"),
           vjust = -0.2, size = 3) +
  labs(title = "Active Polities Over Time (excl. regions & subnational)",
       x = "Year", y = "Active polities") +
  theme_minimal(base_size = 12) +
  theme(plot.title = element_text(face = "bold"))

ggsave(file.path(plot_dir, "temporal_01_active_polities.png"), p_temporal,
       width = 14, height = 6, dpi = 150)

# Formation/dissolution rates
events <- bind_rows(
  non_sub %>% transmute(year = start_year, event = "formation", type = polity_type),
  non_sub %>% filter(end_year < 2025) %>%
    transmute(year = end_year, event = "dissolution", type = polity_type)
)

p_events <- ggplot(events, aes(x = year, fill = event)) +
  geom_histogram(bins = 45, position = "dodge", alpha = 0.8) +
  scale_fill_manual(values = c(formation = "#4CAF50", dissolution = "#F44336")) +
  labs(title = "Formation and Dissolution Events",
       x = "Year", y = "Count", fill = NULL) +
  theme_minimal(base_size = 12) +
  theme(plot.title = element_text(face = "bold"))

ggsave(file.path(plot_dir, "temporal_02_events.png"), p_events,
       width = 14, height = 6, dpi = 150)

# Lifespan distribution by type
p_lifespan <- ggplot(non_sub, aes(x = duration_years, fill = polity_type)) +
  geom_histogram(bins = 50, alpha = 0.7) +
  scale_fill_manual(values = TYPE_COLORS) +
  labs(title = "Polity Lifespan Distribution",
       x = "Duration (years)", y = "Count", fill = "Type") +
  theme_minimal(base_size = 12) +
  theme(plot.title = element_text(face = "bold"))

ggsave(file.path(plot_dir, "temporal_03_lifespan.png"), p_lifespan,
       width = 12, height = 6, dpi = 150)

# Type distribution over time
decades <- tibble(decade = seq(1800, 2020, 10))
decade_type <- tidyr::crossing(non_sub, decades) %>%
  filter(start_year <= decade, end_year >= decade) %>%
  count(decade, polity_type)

p_type_time <- ggplot(decade_type, aes(x = decade, y = n, fill = polity_type)) +
  geom_area(alpha = 0.8) +
  scale_fill_manual(values = TYPE_COLORS) +
  labs(title = "Polity Types Over Time", x = "Year", y = "Active count", fill = "Type") +
  theme_minimal(base_size = 12) +
  theme(plot.title = element_text(face = "bold"))

ggsave(file.path(plot_dir, "temporal_04_types_over_time.png"), p_type_time,
       width = 14, height = 6, dpi = 150)

cat("  Saved 4 temporal plots\n")

# ==============================================================================
# 2. Continent/Type Distribution
# ==============================================================================

cat("\n--- Distribution Analysis ---\n")

# By continent and type
p_cont_type <- ggplot(non_sub, aes(x = fct_infreq(continent), fill = polity_type)) +
  geom_bar() +
  scale_fill_manual(values = TYPE_COLORS) +
  labs(title = "Polity Distribution by Continent and Type",
       x = NULL, y = "Count", fill = "Type") +
  theme_minimal(base_size = 12) +
  theme(plot.title = element_text(face = "bold"),
        axis.text.x = element_text(angle = 30, hjust = 1))

ggsave(file.path(plot_dir, "dist_01_continent_type.png"), p_cont_type,
       width = 12, height = 6, dpi = 150)

# Verification status
p_verif <- ggplot(df, aes(x = fct_infreq(str_trunc(verification_status, 15)))) +
  geom_bar(fill = "#42A5F5", alpha = 0.8) +
  geom_text(stat = "count", aes(label = after_stat(count)), vjust = -0.5) +
  labs(title = "Verification Status Distribution", x = NULL, y = "Count") +
  theme_minimal(base_size = 12) +
  theme(plot.title = element_text(face = "bold"))

ggsave(file.path(plot_dir, "dist_02_verification.png"), p_verif,
       width = 10, height = 6, dpi = 150)

cat("  Saved 2 distribution plots\n")

# ==============================================================================
# 3. Polygon Quality Analysis
# ==============================================================================

if (has_polys) {
  cat("\n--- Polygon Quality ---\n")

  poly_meta <- polys %>%
    mutate(
      geom_type = st_geometry_type(.),
      n_parts   = lengths(st_cast(st_geometry(.), "POLYGON", group_or_split = FALSE)),
      area_deg2 = as.numeric(st_area(.)) / 1e10  # approx deg^2
    ) %>%
    st_drop_geometry() %>%
    left_join(df %>% select(polity_code, polity_type, continent, polygon_source),
              by = "polity_code")

  # Area distribution by source
  p_area <- ggplot(poly_meta %>% filter(!is.na(polygon_source)),
                   aes(x = area_deg2, fill = str_trunc(polygon_source, 20))) +
    geom_histogram(bins = 50, alpha = 0.7) +
    scale_x_log10() +
    labs(title = "Polygon Area Distribution by Source",
         x = "Area (approx deg^2, log scale)", y = "Count", fill = "Source") +
    theme_minimal(base_size = 11) +
    theme(plot.title = element_text(face = "bold"), legend.position = "bottom")

  ggsave(file.path(plot_dir, "polyqual_01_area_dist.png"), p_area,
         width = 12, height = 6, dpi = 150)

  # Fragmentation (number of parts)
  p_frag <- ggplot(poly_meta, aes(x = n_parts)) +
    geom_histogram(bins = 50, fill = "#FF9800", alpha = 0.8) +
    scale_x_log10() +
    labs(title = "Polygon Fragmentation (number of parts)",
         x = "Parts (log scale)", y = "Count") +
    theme_minimal(base_size = 12) +
    theme(plot.title = element_text(face = "bold"))

  ggsave(file.path(plot_dir, "polyqual_02_fragmentation.png"), p_frag,
         width = 10, height = 6, dpi = 150)

  cat("  Saved 2 polygon quality plots\n")
}

# ==============================================================================
# 4. ISO Collision Analysis
# ==============================================================================

cat("\n--- ISO Collision Analysis ---\n")

iso_shared <- df %>%
  filter(!is.na(iso3_code), !polity_type %in% c("region", "subnational")) %>%
  group_by(iso3_code) %>%
  summarise(
    n_entries = n(),
    n_names = n_distinct(polity_name),
    names = paste(unique(polity_name), collapse = " | "),
    types = paste(unique(polity_type), collapse = ", "),
    .groups = "drop"
  ) %>%
  filter(n_entries > 1)

# Prefix collision groups
prefix_groups <- df %>%
  filter(!is.na(iso3_code), !polity_type %in% c("region", "subnational")) %>%
  mutate(prefix = str_extract(polity_code, "^[^-]+")) %>%
  group_by(prefix) %>%
  summarise(
    n_isos = n_distinct(iso3_code),
    n_entries = n(),
    iso_codes = paste(unique(iso3_code), collapse = ", "),
    .groups = "drop"
  ) %>%
  filter(n_isos > 1)

p_iso <- ggplot(iso_shared %>% slice_max(n_entries, n = 30),
                aes(x = reorder(iso3_code, n_entries), y = n_entries)) +
  geom_col(fill = "#AB47BC", alpha = 0.8) +
  coord_flip() +
  labs(title = sprintf("Top 30 Most-Shared ISO3 Codes (%d codes shared total)",
                       nrow(iso_shared)),
       x = "ISO3 code", y = "Number of entries") +
  theme_minimal(base_size = 11) +
  theme(plot.title = element_text(face = "bold"))

ggsave(file.path(plot_dir, "iso_01_shared_codes.png"), p_iso,
       width = 10, height = 8, dpi = 150)

p_prefix <- ggplot(prefix_groups, aes(x = reorder(prefix, n_isos), y = n_isos)) +
  geom_col(fill = "#EF5350", alpha = 0.8) +
  coord_flip() +
  labs(title = sprintf("Prefix Collision Groups (%d groups)", nrow(prefix_groups)),
       x = "Code prefix", y = "Number of distinct ISO3 codes") +
  theme_minimal(base_size = 11) +
  theme(plot.title = element_text(face = "bold"))

ggsave(file.path(plot_dir, "iso_02_prefix_collisions.png"), p_prefix,
       width = 10, height = 8, dpi = 150)

cat("  Saved 2 ISO analysis plots\n")

# ==============================================================================
# 5. Coverage Summary
# ==============================================================================

cat("\n--- Coverage Summary ---\n")

# Coverage by data source
source_coverage <- df %>%
  filter(!is.na(data_sources)) %>%
  mutate(sources = str_split(data_sources, ";\\s*")) %>%
  unnest(sources) %>%
  mutate(sources = trimws(sources)) %>%
  count(sources, sort = TRUE)

p_sources <- ggplot(source_coverage, aes(x = reorder(sources, n), y = n)) +
  geom_col(fill = "#26A69A", alpha = 0.8) +
  geom_text(aes(label = n), hjust = -0.2, size = 3.5) +
  coord_flip() +
  labs(title = "Polity Coverage by Data Source",
       x = NULL, y = "Number of entries") +
  theme_minimal(base_size = 12) +
  theme(plot.title = element_text(face = "bold"))

ggsave(file.path(plot_dir, "coverage_01_by_source.png"), p_sources,
       width = 10, height = 6, dpi = 150)

# Polygon source distribution
poly_sources <- df %>%
  filter(!polity_type %in% c("region")) %>%
  count(polygon_source = str_trunc(replace_na(polygon_source, "None"), 30), sort = TRUE)

p_poly_src <- ggplot(poly_sources, aes(x = reorder(polygon_source, n), y = n)) +
  geom_col(fill = "#7E57C2", alpha = 0.8) +
  geom_text(aes(label = n), hjust = -0.2, size = 3.5) +
  coord_flip() +
  labs(title = "Polygon Source Distribution",
       x = NULL, y = "Number of entries") +
  theme_minimal(base_size = 12) +
  theme(plot.title = element_text(face = "bold"))

ggsave(file.path(plot_dir, "coverage_02_polygon_sources.png"), p_poly_src,
       width = 12, height = 6, dpi = 150)

cat("  Saved 2 coverage plots\n")

# ==============================================================================

cat(sprintf("\nAll analysis plots saved to %s/\n", plot_dir))
cat("Done!\n")
