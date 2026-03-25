# ==============================================================================
# Map & Spatial Analysis
# ==============================================================================
# Creates world maps colored by WHEP coverage, era maps, polity density maps
# ==============================================================================

source("R/00_setup.R")

master <- read_csv(file.path(compiled_dir, "polities_master.csv"),
                   show_col_types = FALSE)

# --- Load world map ---
world <- ne_countries(scale = "medium", returnclass = "sf") %>%
  select(name, iso_a3, iso_a2, continent, pop_est, gdp_md, geometry)

# ==============================================================================
# Plot 1: WHEP Coverage Map - Which countries are in the database?
# ==============================================================================

# Match WHEP polities to Natural Earth by ISO3
whep_modern <- master %>%
  filter(end_year >= 2020, !polity_type %in% c("region", "aggregate")) %>%
  select(polity_name, iso3_code, polity_type, n_sources, start_year) %>%
  distinct(iso3_code, .keep_all = TRUE)

world_coverage <- world %>%
  left_join(whep_modern, by = c("iso_a3" = "iso3_code")) %>%
  mutate(
    in_whep = !is.na(polity_name),
    coverage_label = case_when(
      is.na(polity_name) ~ "Not in WHEP",
      n_sources >= 4     ~ "4+ sources",
      n_sources == 3     ~ "3 sources",
      n_sources == 2     ~ "2 sources",
      n_sources == 1     ~ "1 source",
      TRUE               ~ "In WHEP (sources unknown)"
    )
  )

p_map1 <- ggplot(world_coverage) +
  geom_sf(aes(fill = coverage_label), color = "grey40", linewidth = 0.1) +
  scale_fill_manual(values = c(
    "Not in WHEP"              = "#EEEEEE",
    "1 source"                 = "#BBDEFB",
    "2 sources"                = "#64B5F6",
    "3 sources"                = "#1976D2",
    "4+ sources"               = "#0D47A1",
    "In WHEP (sources unknown)" = "#90CAF9"
  )) +
  labs(
    title = "WHEP Polities Database: Modern Country Coverage",
    subtitle = "Colored by number of cross-referenced data sources",
    fill = "Coverage"
  ) +
  theme_void(base_size = 12) +
  theme(legend.position = "bottom",
        plot.title = element_text(hjust = 0.5),
        plot.subtitle = element_text(hjust = 0.5))

ggsave(file.path(plot_dir, "13_whep_world_coverage.png"), p_map1,
       width = 16, height = 9, dpi = 150)

# ==============================================================================
# Plot 2: Polity Start Year Map - When did each modern polity enter the DB?
# ==============================================================================

world_startyear <- world %>%
  left_join(
    master %>%
      filter(end_year >= 2020, !polity_type %in% c("region", "aggregate")) %>%
      group_by(iso3_code) %>%
      summarise(earliest_start = min(start_year, na.rm = TRUE), .groups = "drop"),
    by = c("iso_a3" = "iso3_code")
  )

p_map2 <- ggplot(world_startyear) +
  geom_sf(aes(fill = earliest_start), color = "grey40", linewidth = 0.1) +
  scale_fill_viridis_c(
    option = "plasma",
    na.value = "#EEEEEE",
    breaks = c(1800, 1850, 1900, 1950, 2000),
    labels = c("1800", "1850", "1900", "1950", "2000")
  ) +
  labs(
    title = "WHEP Database: Earliest Coverage Year Per Country",
    subtitle = "Earlier = longer historical trade data coverage",
    fill = "Earliest Year"
  ) +
  theme_void(base_size = 12) +
  theme(legend.position = "bottom",
        plot.title = element_text(hjust = 0.5),
        plot.subtitle = element_text(hjust = 0.5))

ggsave(file.path(plot_dir, "14_earliest_coverage_map.png"), p_map2,
       width = 16, height = 9, dpi = 150)

# ==============================================================================
# Plot 3: Number of Territorial Periods Per Country
# ==============================================================================

period_counts <- master %>%
  filter(!polity_type %in% c("region", "aggregate")) %>%
  count(prefix, name = "n_periods") %>%
  filter(n_periods > 1)

# Join with master to get ISO3 for each prefix
prefix_to_iso <- master %>%
  filter(!is.na(iso3_code)) %>%
  distinct(prefix, iso3_code)

period_map_data <- world %>%
  left_join(
    period_counts %>%
      left_join(prefix_to_iso, by = "prefix") %>%
      group_by(iso3_code) %>%
      summarise(total_periods = sum(n_periods), .groups = "drop"),
    by = c("iso_a3" = "iso3_code")
  ) %>%
  mutate(total_periods = replace_na(total_periods, 1))

p_map3 <- ggplot(period_map_data) +
  geom_sf(aes(fill = total_periods), color = "grey40", linewidth = 0.1) +
  scale_fill_viridis_c(
    option = "inferno",
    trans = "log1p",
    breaks = c(1, 2, 5, 10, 20),
    na.value = "#EEEEEE"
  ) +
  labs(
    title = "Territorial Period Complexity Per Country",
    subtitle = "More periods = more territorial changes tracked in WHEP",
    fill = "Number of\nPeriods"
  ) +
  theme_void(base_size = 12) +
  theme(legend.position = "bottom",
        plot.title = element_text(hjust = 0.5),
        plot.subtitle = element_text(hjust = 0.5))

ggsave(file.path(plot_dir, "15_territorial_complexity_map.png"), p_map3,
       width = 16, height = 9, dpi = 150)

# ==============================================================================
# Plot 4: Empire Affiliation Map (Historical)
# ==============================================================================

empire_map_data <- master %>%
  filter(!is.na(empire), !polity_type %in% c("region")) %>%
  distinct(iso3_code, empire) %>%
  filter(!is.na(iso3_code))

world_empire <- world %>%
  left_join(empire_map_data, by = c("iso_a3" = "iso3_code"))

p_map4 <- ggplot(world_empire) +
  geom_sf(aes(fill = empire), color = "grey40", linewidth = 0.1) +
  scale_fill_brewer(palette = "Set3", na.value = "#F5F5F5") +
  labs(
    title = "Historical Empire Affiliation of WHEP Polities",
    subtitle = "Shows which empires controlled territories in the database",
    fill = "Empire"
  ) +
  theme_void(base_size = 12) +
  theme(legend.position = "bottom",
        plot.title = element_text(hjust = 0.5),
        plot.subtitle = element_text(hjust = 0.5))

ggsave(file.path(plot_dir, "16_empire_affiliation_map.png"), p_map4,
       width = 16, height = 9, dpi = 150)

# ==============================================================================
# Plot 5: Continental Type Distribution (Stacked Bar)
# ==============================================================================

continent_type_data <- master %>%
  filter(!polity_type %in% c("region"), !is.na(continent)) %>%
  count(continent, polity_type)

p_cont_type <- ggplot(continent_type_data,
                      aes(x = reorder(continent, -n, sum),
                          y = n, fill = polity_type)) +
  geom_col(alpha = 0.8) +
  geom_text(aes(label = n), position = position_stack(vjust = 0.5), size = 3) +
  scale_fill_brewer(palette = "Set2") +
  labs(
    title = "WHEP Polities: Continent x Type Distribution",
    x = NULL, y = "Number of polities", fill = "Type"
  ) +
  theme_minimal(base_size = 12) +
  theme(legend.position = "top",
        plot.title = element_text(hjust = 0.5))

ggsave(file.path(plot_dir, "17_continent_type_distribution.png"), p_cont_type,
       width = 12, height = 7, dpi = 150)

cat("\nMap analysis complete. Plots saved to:", plot_dir, "\n")
