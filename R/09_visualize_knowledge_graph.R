# ==============================================================================
# Knowledge Graph Visualizations
# ==============================================================================
# Generates 6 plots from the knowledge graph edge/node data
# ==============================================================================

source("R/00_setup.R")

# --- Load data ---

cat("Loading knowledge graph data...\n")
edges <- read_csv(file.path(analysis_dir, "knowledge_graph_edges.csv"), show_col_types = FALSE)
nodes <- read_csv(file.path(analysis_dir, "knowledge_graph_nodes.csv"), show_col_types = FALSE)
polities <- read_csv(file.path(final_dir, "polities_database.csv"), show_col_types = FALSE)

cat("  Nodes:", nrow(nodes), "Edges:", nrow(edges), "\n")

# --- Plot 1: Relation type distribution ---

cat("\nPlot 1: Relation type distribution...\n")

rel_counts <- edges %>% count(relation, sort = TRUE)

p1 <- ggplot(rel_counts, aes(x = reorder(relation, n), y = n, fill = relation)) +
  geom_col(show.legend = FALSE) +
  geom_text(aes(label = n), hjust = -0.2, fontface = "bold", size = 3.5) +
  scale_fill_manual(values = RELATION_COLORS) +
  coord_flip() +
  labs(title = "Knowledge Graph: Edge Count by Relation Type",
       x = NULL, y = "Number of edges") +
  theme_minimal(base_size = 12) +
  theme(plot.title = element_text(face = "bold"))

ggsave(file.path(plot_dir, "kg_01_relation_type_distribution.png"), p1,
       width = 12, height = 6, dpi = 150)

# --- Plot 2: Degree distribution ---

cat("Plot 2: Degree distribution...\n")

polity_nodes <- nodes %>% filter(node_type == "polity")

p2a <- ggplot(polity_nodes, aes(x = total_degree)) +
  geom_histogram(bins = 50, fill = "#2196F3", color = "white", alpha = 0.8) +
  geom_vline(xintercept = median(polity_nodes$total_degree),
             color = "red", linetype = "dashed") +
  annotate("text", x = median(polity_nodes$total_degree) + 2,
           y = Inf, vjust = 2,
           label = sprintf("Median: %d", median(polity_nodes$total_degree)),
           color = "red") +
  labs(title = "Degree Distribution", x = "Degree (total connections)", y = "Count") +
  theme_minimal(base_size = 11) +
  theme(plot.title = element_text(face = "bold"))

top20 <- polity_nodes %>% slice_max(total_degree, n = 20)

p2b <- ggplot(top20, aes(x = reorder(str_trunc(polity_name, 30), total_degree),
                          y = total_degree, fill = polity_type)) +
  geom_col() +
  scale_fill_manual(values = TYPE_COLORS) +
  coord_flip() +
  labs(title = "Top 20 Most Connected Polities", x = NULL, y = "Degree") +
  theme_minimal(base_size = 11) +
  theme(plot.title = element_text(face = "bold"), legend.position = "bottom")

p2 <- gridExtra::grid.arrange(p2a, p2b, ncol = 2)
ggsave(file.path(plot_dir, "kg_02_degree_distribution.png"), p2,
       width = 14, height = 6, dpi = 150)

# --- Plot 3: Successor chains ---

cat("Plot 3: Successor chains...\n")

interesting_isos <- c("DEU", "CHN", "RUS", "ITA", "PAK", "SDN", "YUG", "ETH")

chain_data <- polities %>%
  filter(iso3_code %in% interesting_isos,
         polity_type %in% c("sovereign", "historical")) %>%
  arrange(iso3_code, start_year) %>%
  mutate(iso_label = iso3_code,
         label = sprintf("%s\n(%d-%d)", str_trunc(polity_name, 20), start_year, end_year))

p3 <- ggplot(chain_data, aes(x = start_year, y = fct_rev(iso_label), color = polity_type)) +
  geom_segment(aes(xend = end_year, yend = fct_rev(iso_label)), linewidth = 4, alpha = 0.7) +
  geom_point(size = 2) +
  geom_point(aes(x = end_year), size = 2) +
  scale_color_manual(values = TYPE_COLORS) +
  labs(title = "Temporal Successor Chains for Selected Countries",
       x = "Year", y = NULL, color = "Type") +
  theme_minimal(base_size = 12) +
  theme(plot.title = element_text(face = "bold"),
        legend.position = "bottom")

ggsave(file.path(plot_dir, "kg_03_successor_chains.png"), p3,
       width = 16, height = 8, dpi = 150)

# --- Plot 4: Colonial empires ---

cat("Plot 4: Colonial empires...\n")

col_edges <- edges %>% filter(relation == "colonial_ruler_of")

if (nrow(col_edges) > 0) {
  col_nodes <- bind_rows(
    nodes %>% filter(polity_code %in% col_edges$source) %>% mutate(role = "metropole"),
    nodes %>% filter(polity_code %in% col_edges$target) %>% mutate(role = "colony")
  ) %>% distinct(polity_code, .keep_all = TRUE)

  # Count colonies per metropole
  metro_counts <- col_edges %>%
    count(source, name = "n_colonies") %>%
    inner_join(nodes %>% select(polity_code, polity_name), by = c("source" = "polity_code"))

  col_plot_data <- col_edges %>%
    inner_join(nodes %>% select(polity_code, polity_name, continent),
               by = c("target" = "polity_code")) %>%
    inner_join(nodes %>% select(polity_code, polity_name),
               by = c("source" = "polity_code"), suffix = c("_colony", "_metro"))

  p4 <- ggplot(col_plot_data,
               aes(x = reorder(str_trunc(polity_name_metro, 20), -table(source)[source]),
                   fill = continent)) +
    geom_bar() +
    scale_fill_manual(values = CONTINENT_COLORS) +
    labs(title = "Colonial Empire Networks",
         x = "Metropole", y = "Number of colonies/dependencies",
         fill = "Colony continent") +
    theme_minimal(base_size = 12) +
    theme(plot.title = element_text(face = "bold"),
          axis.text.x = element_text(angle = 45, hjust = 1))
} else {
  p4 <- ggplot() + annotate("text", x = 0.5, y = 0.5, label = "No colonial edges") + theme_void()
}

ggsave(file.path(plot_dir, "kg_04_colonial_empires.png"), p4,
       width = 14, height = 8, dpi = 150)

# --- Plot 5: Subnational hierarchy ---

cat("Plot 5: Subnational hierarchy...\n")

countries <- tribble(
  ~iso3, ~parent_code,        ~label,
  "USA", "USA-1959-2025",     "United States",
  "CAN", "CAN-1948-2025",     "Canada",
  "BRA", "BRA-1909-2025",     "Brazil",
  "AUS", "AUS-1901-2025",     "Australia",
  "CHN", "F351-1950-2025",    "China",
  "RUS", "RUS-2014-2025",     "Russia"
)

sub_data <- edges %>%
  filter(relation == "subregion_of", evidence == "notes field (Parent)") %>%
  inner_join(polities %>% select(polity_code, polity_name, iso3_code),
             by = c("source" = "polity_code")) %>%
  inner_join(countries, by = c("target" = "parent_code"))

p5 <- ggplot(sub_data %>% count(label, name = "n_regions"),
             aes(x = reorder(label, -n_regions), y = n_regions)) +
  geom_col(fill = "#4CAF50", alpha = 0.8) +
  geom_text(aes(label = n_regions), vjust = -0.5, fontface = "bold") +
  labs(title = "Subnational Hierarchy: Admin-1 Units per Country",
       x = NULL, y = "Number of admin-1 units") +
  theme_minimal(base_size = 12) +
  theme(plot.title = element_text(face = "bold"))

ggsave(file.path(plot_dir, "kg_05_subnational_hierarchy.png"), p5,
       width = 10, height = 6, dpi = 150)

# --- Plot 6: Graph metrics summary ---

cat("Plot 6: Graph metrics summary...\n")

# 6a: Node type distribution
p6a <- ggplot(polity_nodes %>% count(polity_type),
              aes(x = reorder(polity_type, n), y = n, fill = polity_type)) +
  geom_col(show.legend = FALSE) +
  scale_fill_manual(values = TYPE_COLORS) +
  coord_flip() +
  labs(title = "Node Distribution by Type", x = NULL, y = "Count") +
  theme_minimal(base_size = 10) +
  theme(plot.title = element_text(face = "bold"))

# 6b: In-degree vs out-degree
p6b <- ggplot(polity_nodes, aes(x = in_degree, y = out_degree, color = polity_type)) +
  geom_point(alpha = 0.5, size = 1.5) +
  geom_abline(slope = 1, intercept = 0, linetype = "dashed", alpha = 0.3) +
  scale_color_manual(values = TYPE_COLORS) +
  labs(title = "In-degree vs Out-degree", x = "In-degree", y = "Out-degree") +
  theme_minimal(base_size = 10) +
  theme(plot.title = element_text(face = "bold"), legend.position = "none")

# 6c: Edges by period
temporal_edges <- edges %>%
  filter(!is.na(start_year), relation != "located_in_continent") %>%
  mutate(period = cut(start_year, breaks = seq(1800, 2025, 25), include.lowest = TRUE))

p6c <- ggplot(temporal_edges %>% filter(!is.na(period)),
              aes(x = period, fill = relation)) +
  geom_bar() +
  scale_fill_manual(values = RELATION_COLORS) +
  labs(title = "Edges by Period (excl. continent)", x = "Period", y = "Count") +
  theme_minimal(base_size = 10) +
  theme(plot.title = element_text(face = "bold"),
        axis.text.x = element_text(angle = 45, hjust = 1, size = 7),
        legend.text = element_text(size = 7))

# 6d: Degree histogram by type
p6d <- ggplot(polity_nodes, aes(x = total_degree, fill = polity_type)) +
  geom_histogram(bins = 40, alpha = 0.7) +
  scale_fill_manual(values = TYPE_COLORS) +
  labs(title = "Degree Distribution by Type", x = "Total degree", y = "Count") +
  theme_minimal(base_size = 10) +
  theme(plot.title = element_text(face = "bold"), legend.position = "none")

p6 <- gridExtra::grid.arrange(p6a, p6b, p6c, p6d, ncol = 2,
                                top = grid::textGrob("Knowledge Graph Metrics",
                                                      gp = grid::gpar(fontsize = 15, fontface = "bold")))

ggsave(file.path(plot_dir, "kg_06_graph_metrics_summary.png"), p6,
       width = 14, height = 12, dpi = 150)

cat(sprintf("\nAll plots saved to %s/kg_*.png\n", plot_dir))
cat("Done!\n")
