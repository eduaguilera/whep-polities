# ==============================================================================
# Temporal Analysis of Polities
# ==============================================================================
# Analyzes: timelines, era distributions, formation/dissolution events,
# temporal coverage gaps, polity lifespans
# ==============================================================================

source("R/00_setup.R")

master <- read_csv(file.path(compiled_dir, "polities_master.csv"),
                   show_col_types = FALSE)

# Filter out regions for most analyses
entities <- master %>% filter(!polity_type %in% c("region"))

# ==============================================================================
# Plot 1: Formation and Dissolution Events Over Time
# ==============================================================================

formations <- entities %>%
  filter(!is.na(start_year), start_year > 1800) %>%
  count(start_year) %>%
  rename(year = start_year, formations = n)

dissolutions <- entities %>%
  filter(!is.na(end_year), end_year < 2025) %>%
  count(end_year) %>%
  rename(year = end_year, dissolutions = n)

events <- full_join(formations, dissolutions, by = "year") %>%
  replace_na(list(formations = 0, dissolutions = 0)) %>%
  pivot_longer(cols = c(formations, dissolutions),
               names_to = "event_type", values_to = "count") %>%
  filter(year >= 1800, year <= 2025)

p1 <- ggplot(events, aes(x = year, y = count, fill = event_type)) +
  geom_col(position = "dodge", width = 1.5) +
  scale_fill_manual(values = c("formations" = "#2196F3", "dissolutions" = "#F44336"),
                    labels = c("Formations", "Dissolutions")) +
  scale_x_continuous(breaks = seq(1800, 2025, 25)) +
  labs(
    title = "Polity Formation and Dissolution Events (1800-2025)",
    subtitle = "Peaks at major geopolitical transitions: 1918, 1945, 1960, 1991",
    x = "Year", y = "Number of events", fill = NULL
  ) +
  theme_minimal(base_size = 12) +
  theme(legend.position = "top",
        panel.grid.minor = element_blank())

ggsave(file.path(plot_dir, "01_formation_dissolution_events.png"), p1,
       width = 14, height = 7, dpi = 150)

# ==============================================================================
# Plot 2: Number of Active Polities Over Time
# ==============================================================================

years <- 1800:2025
active_counts <- tibble(year = years) %>%
  rowwise() %>%
  mutate(
    n_total     = sum(entities$start_year <= year & entities$end_year >= year, na.rm = TRUE),
    n_sovereign = sum(entities$start_year <= year & entities$end_year >= year &
                        entities$polity_type == "sovereign", na.rm = TRUE),
    n_historical = sum(entities$start_year <= year & entities$end_year >= year &
                         entities$polity_type == "historical", na.rm = TRUE),
    n_colonial  = sum(entities$start_year <= year & entities$end_year >= year &
                        entities$polity_type == "colonial", na.rm = TRUE),
    n_aggregate = sum(entities$start_year <= year & entities$end_year >= year &
                        entities$polity_type == "aggregate", na.rm = TRUE)
  ) %>%
  ungroup()

active_long <- active_counts %>%
  select(year, n_sovereign, n_historical, n_colonial, n_aggregate) %>%
  pivot_longer(-year, names_to = "type", values_to = "count") %>%
  mutate(type = str_remove(type, "^n_") %>%
           str_to_title() %>%
           factor(levels = c("Sovereign", "Historical", "Colonial", "Aggregate")))

p2 <- ggplot(active_long, aes(x = year, y = count, fill = type)) +
  geom_area(alpha = 0.7) +
  scale_fill_brewer(palette = "Set2") +
  scale_x_continuous(breaks = seq(1800, 2025, 25)) +
  geom_vline(xintercept = c(1871, 1918, 1945, 1960, 1991),
             linetype = "dashed", alpha = 0.5) +
  annotate("text", x = c(1871, 1918, 1945, 1960, 1991),
           y = max(active_counts$n_total) * 0.95,
           label = c("Unifications", "WWI end", "WWII end", "Decolonization", "USSR fall"),
           angle = 90, hjust = 1, size = 3, alpha = 0.6) +
  labs(
    title = "Active Polities in WHEP Database Over Time",
    subtitle = "Stacked by polity type",
    x = "Year", y = "Number of active polities", fill = "Type"
  ) +
  theme_minimal(base_size = 12) +
  theme(legend.position = "top",
        panel.grid.minor = element_blank())

ggsave(file.path(plot_dir, "02_active_polities_timeline.png"), p2,
       width = 14, height = 7, dpi = 150)

# ==============================================================================
# Plot 3: Polity Lifespan Distribution
# ==============================================================================

p3 <- entities %>%
  filter(!is.na(duration), duration > 0) %>%
  ggplot(aes(x = duration, fill = polity_type)) +
  geom_histogram(binwidth = 10, color = "white", alpha = 0.8) +
  scale_fill_brewer(palette = "Set2") +
  labs(
    title = "Distribution of Polity Lifespans",
    subtitle = paste("Median:", median(entities$duration, na.rm = TRUE), "years"),
    x = "Duration (years)", y = "Count", fill = "Type"
  ) +
  theme_minimal(base_size = 12) +
  theme(legend.position = "top")

ggsave(file.path(plot_dir, "03_polity_lifespan_distribution.png"), p3,
       width = 12, height = 7, dpi = 150)

# ==============================================================================
# Plot 4: Era Breakdown - How Many Polities Per Era
# ==============================================================================

eras <- tribble(
  ~era,                  ~era_start, ~era_end,
  "Pre-Unification\n(1800-1870)",  1800, 1870,
  "Imperial Age\n(1871-1918)",     1871, 1918,
  "Interwar\n(1919-1938)",         1919, 1938,
  "WWII\n(1939-1945)",            1939, 1945,
  "Cold War\n(1946-1991)",        1946, 1991,
  "Post-Cold War\n(1992-2025)",   1992, 2025,
)

era_counts <- eras %>%
  rowwise() %>%
  mutate(
    n_active = sum(entities$start_year <= era_end &
                     entities$end_year >= era_start, na.rm = TRUE),
    n_formed = sum(entities$start_year >= era_start &
                     entities$start_year <= era_end, na.rm = TRUE),
    n_dissolved = sum(entities$end_year >= era_start &
                        entities$end_year <= era_end &
                        entities$end_year < 2025, na.rm = TRUE)
  ) %>%
  ungroup()

era_long <- era_counts %>%
  select(era, n_active, n_formed, n_dissolved) %>%
  pivot_longer(-era, names_to = "metric", values_to = "count") %>%
  mutate(
    era = factor(era, levels = eras$era),
    metric = factor(metric,
                    levels = c("n_active", "n_formed", "n_dissolved"),
                    labels = c("Active", "Formed", "Dissolved"))
  )

p4 <- ggplot(era_long, aes(x = era, y = count, fill = metric)) +
  geom_col(position = "dodge") +
  scale_fill_manual(values = c("#4CAF50", "#2196F3", "#F44336")) +
  labs(
    title = "Polity Activity by Historical Era",
    x = NULL, y = "Count", fill = NULL
  ) +
  theme_minimal(base_size = 12) +
  theme(legend.position = "top",
        axis.text.x = element_text(size = 9))

ggsave(file.path(plot_dir, "04_era_breakdown.png"), p4,
       width = 12, height = 7, dpi = 150)

# ==============================================================================
# Plot 5: Timeline of Major Empire Dissolutions
# ==============================================================================

empire_events <- tribble(
  ~empire,              ~year, ~n_successors, ~event,
  "Holy Roman Empire",  1806,  30,            "dissolution",
  "Italian States",     1861,  7,             "unification",
  "German States",      1871,  25,            "unification",
  "Ottoman Empire",     1918,  15,            "dissolution",
  "Austria-Hungary",    1918,  7,             "dissolution",
  "Russian Empire",     1917,  1,             "revolution",
  "Colonial Empires",   1960,  40,            "decolonization",
  "USSR",               1991,  15,            "dissolution",
  "Yugoslavia",         1992,  7,             "dissolution",
  "Czechoslovakia",     1993,  2,             "dissolution",
)

p5 <- ggplot(empire_events, aes(x = year, y = reorder(empire, year))) +
  geom_point(aes(size = n_successors, color = event), alpha = 0.8) +
  geom_text(aes(label = n_successors), size = 3, fontface = "bold") +
  scale_size_continuous(range = c(4, 15), guide = "none") +
  scale_color_manual(values = c(
    "dissolution" = "#F44336", "unification" = "#4CAF50",
    "revolution" = "#FF9800", "decolonization" = "#9C27B0"
  )) +
  scale_x_continuous(breaks = seq(1800, 2000, 20)) +
  labs(
    title = "Major Geopolitical Transitions (1800-2000)",
    subtitle = "Number shows successor/predecessor states involved",
    x = "Year", y = NULL, color = "Event Type"
  ) +
  theme_minimal(base_size = 12) +
  theme(legend.position = "top",
        panel.grid.minor = element_blank())

ggsave(file.path(plot_dir, "05_empire_dissolutions.png"), p5,
       width = 12, height = 7, dpi = 150)

# ==============================================================================
# Plot 6: Top 30 Longest-Lived Sovereign Polities
# ==============================================================================

top_long <- entities %>%
  filter(polity_type == "sovereign", !is.na(duration)) %>%
  slice_max(duration, n = 30) %>%
  mutate(polity_name = fct_reorder(polity_name, duration))

p6 <- ggplot(top_long, aes(x = duration, y = polity_name)) +
  geom_col(aes(fill = continent), alpha = 0.8) +
  geom_text(aes(label = paste0(start_year, "-", end_year)),
            hjust = -0.1, size = 2.5) +
  scale_fill_brewer(palette = "Set2") +
  labs(
    title = "Top 30 Longest-Lived Sovereign Polities in WHEP",
    x = "Duration (years)", y = NULL, fill = "Continent"
  ) +
  theme_minimal(base_size = 11) +
  theme(legend.position = "top")

ggsave(file.path(plot_dir, "06_longest_sovereign_polities.png"), p6,
       width = 12, height = 10, dpi = 150)

# ==============================================================================
# Plot 7: Short-lived polities (< 25 years)
# ==============================================================================

short_lived <- entities %>%
  filter(!is.na(duration), duration > 0, duration <= 25,
         polity_type != "aggregate") %>%
  arrange(duration) %>%
  mutate(polity_label = paste0(polity_name, " (", start_year, "-", end_year, ")"))

p7 <- short_lived %>%
  slice_head(n = 40) %>%
  mutate(polity_label = fct_reorder(polity_label, duration)) %>%
  ggplot(aes(x = duration, y = polity_label, fill = polity_type)) +
  geom_col(alpha = 0.8) +
  scale_fill_brewer(palette = "Set2") +
  labs(
    title = "Short-Lived Polities (< 25 years)",
    subtitle = paste("Total:", nrow(short_lived), "polities with duration <= 25 years"),
    x = "Duration (years)", y = NULL, fill = "Type"
  ) +
  theme_minimal(base_size = 10) +
  theme(legend.position = "top")

ggsave(file.path(plot_dir, "07_short_lived_polities.png"), p7,
       width = 12, height = 12, dpi = 150)

cat("\nTemporal analysis complete. Plots saved to:", plot_dir, "\n")
