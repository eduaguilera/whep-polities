# ==============================================================================
# Gap Analysis & Data Quality Assessment
# ==============================================================================
# Identifies: timeline gaps, missing polities, source coverage,
# code prefix collisions, area data completeness
# ==============================================================================

source("R/00_setup.R")

master <- read_csv(
  file.path(compiled_dir, "polities_master.csv"),
  show_col_types = FALSE
)

entities <- master %>% filter(!polity_type %in% c("region"))

# ==============================================================================
# 1. Timeline Gap Analysis by Prefix
# ==============================================================================
# Group polities by prefix and check for gaps between periods

prefix_groups <- entities %>%
  filter(!is.na(start_year), !is.na(end_year)) %>%
  group_by(prefix) %>%
  filter(n() > 1) %>%
  arrange(prefix, start_year) %>%
  mutate(
    prev_end = lag(end_year),
    gap_years = start_year - prev_end,
    has_gap = !is.na(gap_years) & gap_years > 1,
    has_overlap = !is.na(gap_years) & gap_years < 0
  ) %>%
  ungroup()

gaps <- prefix_groups %>%
  filter(has_gap) %>%
  select(prefix, polity_name, start_year, prev_end, gap_years) %>%
  arrange(desc(gap_years))

overlaps <- prefix_groups %>%
  filter(has_overlap) %>%
  select(prefix, polity_name, start_year, prev_end, gap_years) %>%
  mutate(overlap_years = abs(gap_years)) %>%
  arrange(desc(overlap_years))

cat("=== Timeline Gaps (>1 year between periods for same prefix) ===\n")
cat("Found", nrow(gaps), "gaps\n\n")
if (nrow(gaps) > 0) {
  print(head(gaps, 20))
}

cat("\n=== Timeline Overlaps ===\n")
cat("Found", nrow(overlaps), "overlaps\n\n")
if (nrow(overlaps) > 0) {
  print(head(overlaps, 20))
}

# ==============================================================================
# 2. Source Coverage Analysis
# ==============================================================================

source_matrix <- master %>%
  filter(!is.na(sources)) %>%
  separate_rows(sources, sep = ";") %>%
  count(sources, polity_type) %>%
  pivot_wider(names_from = polity_type, values_from = n, values_fill = 0)

cat("\n=== Source Coverage by Polity Type ===\n")
print(source_matrix)

p_sources <- master %>%
  filter(!is.na(n_sources), !polity_type %in% c("region")) %>%
  ggplot(aes(x = factor(n_sources), fill = polity_type)) +
  geom_bar(alpha = 0.8) +
  scale_fill_brewer(palette = "Set2") +
  labs(
    title = "Number of Data Sources Per Polity",
    subtitle = "More sources = higher cross-reference confidence",
    x = "Number of sources",
    y = "Count",
    fill = "Type"
  ) +
  theme_minimal(base_size = 12) +
  theme(legend.position = "top")

ggsave(
  file.path(plot_dir, "08_source_coverage.png"),
  p_sources,
  width = 10,
  height = 7,
  dpi = 150
)

# ==============================================================================
# 3. Area Data Completeness
# ==============================================================================

area_stats <- entities %>%
  group_by(polity_type) %>%
  summarise(
    total = n(),
    has_area = sum(!is.na(area_km2)),
    pct_area = round(100 * has_area / total, 1),
    .groups = "drop"
  )

cat("\n=== Area Data Completeness ===\n")
print(area_stats)

# Area distribution for those that have it
p_area <- entities %>%
  filter(!is.na(area_km2), area_km2 > 0) %>%
  ggplot(aes(x = area_km2, fill = polity_type)) +
  geom_histogram(bins = 50, alpha = 0.8) +
  scale_x_log10(labels = label_comma()) +
  scale_fill_brewer(palette = "Set2") +
  labs(
    title = "Distribution of Polity Areas (log scale)",
    subtitle = paste(
      "Polities with area data:",
      sum(!is.na(entities$area_km2))
    ),
    x = "Area (km²)",
    y = "Count",
    fill = "Type"
  ) +
  theme_minimal(base_size = 12) +
  theme(legend.position = "top")

ggsave(
  file.path(plot_dir, "09_area_distribution.png"),
  p_area,
  width = 12,
  height = 7,
  dpi = 150
)

# ==============================================================================
# 4. Code Prefix Collision Analysis
# ==============================================================================

prefix_collision <- entities %>%
  group_by(prefix) %>%
  summarise(
    n_polities = n(),
    names = paste(unique(polity_name), collapse = " | "),
    .groups = "drop"
  ) %>%
  filter(n_polities > 1) %>%
  # Check if they refer to different base entities (not just time periods)
  mutate(
    unique_base = str_extract_all(names, "[^|]+") %>%
      map_int(~ n_distinct(str_trim(.x)))
  )

# True collisions: same prefix but genuinely different entities
true_collisions <- prefix_collision %>%
  filter(unique_base > 1, n_polities <= 5) %>%
  arrange(desc(unique_base))

cat("\n=== Prefix Collisions (same prefix, different entities) ===\n")
cat("Found", nrow(true_collisions), "potential collisions\n\n")
if (nrow(true_collisions) > 0) {
  print(head(true_collisions %>% select(prefix, n_polities, names), 20))
}

# ==============================================================================
# 5. ISO Code Coverage
# ==============================================================================

iso_stats <- master %>%
  group_by(polity_type) %>%
  summarise(
    total = n(),
    has_iso3 = sum(!is.na(iso3_code)),
    has_m49 = sum(!is.na(m49_code)),
    has_iso2 = sum(!is.na(iso2_code)),
    .groups = "drop"
  )

cat("\n=== ISO Code Coverage ===\n")
print(iso_stats)

# ==============================================================================
# 6. Verification Status Distribution
# ==============================================================================

verif_stats <- master %>%
  count(polity_type, verified_status) %>%
  pivot_wider(names_from = verified_status, values_from = n, values_fill = 0)

cat("\n=== Verification Status ===\n")
print(verif_stats)

p_verif <- master %>%
  filter(!is.na(verified_status)) %>%
  ggplot(aes(x = verified_status, fill = polity_type)) +
  geom_bar(alpha = 0.8) +
  scale_fill_brewer(palette = "Set2") +
  labs(
    title = "Verification Status of Polities",
    x = "Status",
    y = "Count",
    fill = "Type"
  ) +
  theme_minimal(base_size = 12) +
  theme(legend.position = "top")

ggsave(
  file.path(plot_dir, "10_verification_status.png"),
  p_verif,
  width = 10,
  height = 7,
  dpi = 150
)

# ==============================================================================
# 7. Missing Polities Assessment
# ==============================================================================
# Key polities that should exist but might be missing

expected_modern <- c(
  "Afghanistan",
  "Albania",
  "Algeria",
  "Andorra",
  "Angola",
  "Argentina",
  "Armenia",
  "Australia",
  "Austria",
  "Azerbaijan",
  "Bahamas",
  "Bahrain",
  "Bangladesh",
  "Barbados",
  "Belarus",
  "Belgium",
  "Belize",
  "Benin",
  "Bhutan",
  "Bolivia",
  "Bosnia and Herzegovina",
  "Botswana",
  "Brazil",
  "Brunei Darussalam",
  "Bulgaria",
  "Burkina Faso",
  "Burundi",
  "Cabo Verde",
  "Cambodia",
  "Cameroon",
  "Canada",
  "Central African Republic",
  "Chad",
  "Chile",
  "Colombia",
  "Comoros",
  "Congo",
  "Costa Rica",
  "Croatia",
  "Cuba",
  "Cyprus",
  "Czechia",
  "Denmark",
  "Djibouti",
  "Dominica",
  "Dominican Republic",
  "Ecuador",
  "Egypt",
  "El Salvador",
  "Equatorial Guinea",
  "Eritrea",
  "Estonia",
  "Eswatini",
  "Ethiopia",
  "Fiji",
  "Finland",
  "France",
  "Gabon",
  "Gambia",
  "Georgia",
  "Germany",
  "Ghana",
  "Greece",
  "Guatemala",
  "Guinea",
  "Guinea-Bissau",
  "Guyana",
  "Haiti",
  "Honduras",
  "Hungary",
  "Iceland",
  "India",
  "Indonesia",
  "Iran",
  "Iraq",
  "Ireland",
  "Israel",
  "Italy",
  "Jamaica",
  "Japan",
  "Jordan",
  "Kazakhstan",
  "Kenya",
  "Kiribati",
  "Kosovo",
  "Kuwait",
  "Kyrgyzstan",
  "Laos",
  "Latvia",
  "Lebanon",
  "Lesotho",
  "Liberia",
  "Libya",
  "Liechtenstein",
  "Lithuania",
  "Luxembourg",
  "Madagascar",
  "Malawi",
  "Malaysia",
  "Maldives",
  "Mali",
  "Malta",
  "Mauritania",
  "Mauritius",
  "Mexico",
  "Moldova",
  "Monaco",
  "Mongolia",
  "Montenegro",
  "Morocco",
  "Mozambique",
  "Myanmar",
  "Namibia",
  "Nepal",
  "Netherlands",
  "New Zealand",
  "Nicaragua",
  "Niger",
  "Nigeria",
  "North Korea",
  "North Macedonia",
  "Norway",
  "Oman",
  "Pakistan",
  "Palau",
  "Panama",
  "Papua New Guinea",
  "Paraguay",
  "Peru",
  "Philippines",
  "Poland",
  "Portugal",
  "Qatar",
  "Romania",
  "Russia",
  "Rwanda",
  "Samoa",
  "San Marino",
  "Saudi Arabia",
  "Senegal",
  "Serbia",
  "Seychelles",
  "Sierra Leone",
  "Singapore",
  "Slovakia",
  "Slovenia",
  "Solomon Islands",
  "Somalia",
  "South Africa",
  "South Korea",
  "South Sudan",
  "Spain",
  "Sri Lanka",
  "Sudan",
  "Suriname",
  "Sweden",
  "Switzerland",
  "Taiwan",
  "Tajikistan",
  "Tanzania",
  "Thailand",
  "Timor-Leste",
  "Togo",
  "Tonga",
  "Trinidad and Tobago",
  "Tunisia",
  "Türkiye",
  "Turkmenistan",
  "Tuvalu",
  "Uganda",
  "Ukraine",
  "United Arab Emirates",
  "United Kingdom",
  "United States of America",
  "Uruguay",
  "Uzbekistan",
  "Vanuatu",
  "Venezuela",
  "Vietnam",
  "Yemen",
  "Zambia",
  "Zimbabwe"
)

sovereign_names <- entities %>%
  filter(end_year == 2025 | end_year >= 2020) %>%
  pull(polity_name) %>%
  unique()

# Fuzzy check
missing_modern <- expected_modern[!expected_modern %in% master$polity_name]

cat("\n=== Potentially Missing Modern States ===\n")
cat("Expected:", length(expected_modern), "\n")
cat("Missing from exact name match:", length(missing_modern), "\n")
if (length(missing_modern) > 0) {
  cat(paste(missing_modern, collapse = ", "), "\n")
}

# ==============================================================================
# 8. Continent Coverage Summary Plot
# ==============================================================================

continent_summary <- entities %>%
  filter(!is.na(continent)) %>%
  group_by(continent, polity_type) %>%
  summarise(n = n(), .groups = "drop")

p_continent <- ggplot(
  continent_summary,
  aes(x = reorder(continent, -n, sum), y = n, fill = polity_type)
) +
  geom_col(alpha = 0.8) +
  scale_fill_brewer(palette = "Set2") +
  labs(
    title = "Polity Count by Continent and Type",
    x = NULL,
    y = "Number of polities",
    fill = "Type"
  ) +
  theme_minimal(base_size = 12) +
  theme(legend.position = "top")

ggsave(
  file.path(plot_dir, "11_continent_coverage.png"),
  p_continent,
  width = 10,
  height = 7,
  dpi = 150
)

# ==============================================================================
# 9. Gap timeline visualization for key prefix groups
# ==============================================================================

key_prefixes <- c(
  "AFG",
  "CHN",
  "DEU",
  "ETH",
  "FRA",
  "GBR",
  "IND",
  "ROU",
  "TUR",
  "USA",
  "RUS",
  "BRA",
  "EGY"
)

timeline_data <- entities %>%
  filter(prefix %in% key_prefixes) %>%
  mutate(polity_label = paste0(polity_name, "\n(", polity_code, ")"))

p_timeline <- ggplot(
  timeline_data,
  aes(
    xmin = start_year,
    xmax = end_year,
    y = reorder(polity_label, -start_year),
    fill = polity_type
  )
) +
  geom_rect(
    aes(
      ymin = as.numeric(reorder(polity_label, -start_year)) - 0.4,
      ymax = as.numeric(reorder(polity_label, -start_year)) + 0.4
    ),
    alpha = 0.7
  ) +
  scale_fill_brewer(palette = "Set2") +
  scale_x_continuous(breaks = seq(1800, 2025, 25)) +
  facet_wrap(~prefix, scales = "free_y", ncol = 2) +
  labs(
    title = "Timeline View: Key Polity Prefix Groups",
    subtitle = "Shows territorial period splits for selected countries",
    x = "Year",
    y = NULL,
    fill = "Type"
  ) +
  theme_minimal(base_size = 9) +
  theme(
    legend.position = "top",
    strip.text = element_text(face = "bold"),
    axis.text.y = element_text(size = 6)
  )

ggsave(
  file.path(plot_dir, "12_key_prefix_timelines.png"),
  p_timeline,
  width = 16,
  height = 20,
  dpi = 150
)

# ==============================================================================
# Save gap analysis report
# ==============================================================================

sink(file.path(report_dir, "gap_analysis_report.txt"))
cat("WHEP Polities Gap Analysis Report\n")
cat("==================================\n")
cat("Generated:", as.character(Sys.time()), "\n\n")

cat("1. Timeline Gaps:\n")
cat("   Found", nrow(gaps), "gaps between periods (same prefix)\n")
if (nrow(gaps) > 0) {
  cat("   Top 10 largest gaps:\n")
  print(head(gaps, 10))
}

cat("\n2. Timeline Overlaps:\n")
cat("   Found", nrow(overlaps), "overlaps\n")

cat("\n3. Source Coverage:\n")
print(source_matrix)

cat("\n4. Area Data Completeness:\n")
print(area_stats)

cat("\n5. Prefix Collisions:\n")
cat("   Found", nrow(true_collisions), "true collisions\n")

cat("\n6. ISO Code Coverage:\n")
print(iso_stats)

cat("\n7. Missing Modern States:\n")
cat("   ", paste(missing_modern, collapse = ", "), "\n")

sink()

cat("\nGap analysis complete. Report saved to:", report_dir, "\n")
