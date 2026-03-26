# ==============================================================================
# Build Knowledge Graph Between Polities
# ==============================================================================
# Extracts 9 relation types: predecessor/successor, subregion_of,
# aggregate_covers, temporal_next, colonial_ruler_of, region_contains,
# located_in_continent, same_territory
# ==============================================================================

source("R/00_setup.R")

# --- Load data ---

cat("Loading data...\n")
df <- read_csv(
  file.path(final_dir, "polities_database.csv"),
  show_col_types = FALSE
)
m49 <- read_csv(file.path(whep_dir, "unstats_m49.csv"), show_col_types = FALSE)
fao <- read_csv(
  file.path(whep_dir, "faostat_regions.csv"),
  show_col_types = FALSE
)

all_codes <- df$polity_code
cat("  Polities:", nrow(df), "\n")

# --- Initialize graph ---

g <- make_empty_graph(directed = TRUE)
g <- add_vertices(
  g,
  nrow(df),
  name = df$polity_code,
  polity_name = df$polity_name,
  polity_type = df$polity_type,
  continent = df$continent,
  start_year = df$start_year,
  end_year = df$end_year,
  iso3_code = replace_na(df$iso3_code, ""),
  node_type = "polity"
)

# Add continent nodes
continents <- unique(na.omit(df$continent))
g <- add_vertices(
  g,
  length(continents),
  name = continents,
  polity_name = continents,
  polity_type = "continent",
  continent = continents,
  start_year = 1800L,
  end_year = 2025L,
  iso3_code = "",
  node_type = "continent"
)

edge_log <- tibble(
  source = character(),
  target = character(),
  relation = character(),
  evidence = character(),
  start_year = integer(),
  end_year = integer()
)

add_edge_logged <- function(
  src,
  tgt,
  rel,
  ev = "",
  sy = NA_integer_,
  ey = NA_integer_
) {
  g <<- add_edges(
    g,
    c(src, tgt),
    relation = rel,
    evidence = ev,
    start_year = sy %||% 0L,
    end_year = ey %||% 0L
  )
  edge_log <<- bind_rows(
    edge_log,
    tibble(
      source = src,
      target = tgt,
      relation = rel,
      evidence = ev,
      start_year = sy,
      end_year = ey
    )
  )
}

# === 1. Predecessor / Successor ===

cat("\n1. Extracting predecessor/successor relations...\n")
missing_refs <- character()

for (i in seq_len(nrow(df))) {
  code <- df$polity_code[i]

  # Predecessors
  pred <- df$predecessor[i]
  if (!is.na(pred) && nzchar(trimws(pred))) {
    refs <- trimws(unlist(str_split(pred, "[;,]")))
    for (ref in refs) {
      if (ref %in% all_codes) {
        add_edge_logged(
          ref,
          code,
          "predecessor_of",
          "predecessor column",
          df$start_year[i],
          df$end_year[i]
        )
      } else if (str_detect(ref, "^[A-Z0-9]+-\\d{4}-\\d{4}$")) {
        missing_refs <- c(missing_refs, sprintf("%s -> %s", code, ref))
      }
    }
  }

  # Successors
  succ <- df$successor[i]
  if (!is.na(succ) && nzchar(trimws(succ))) {
    refs <- trimws(unlist(str_split(succ, "[;,]")))
    for (ref in refs) {
      if (ref %in% all_codes) {
        add_edge_logged(
          code,
          ref,
          "successor_of",
          "successor column",
          df$start_year[i],
          df$end_year[i]
        )
      } else if (str_detect(ref, "^[A-Z0-9]+-\\d{4}-\\d{4}$")) {
        missing_refs <- c(missing_refs, sprintf("%s -> %s", code, ref))
      }
    }
  }
}

ps_count <- sum(edge_log$relation %in% c("predecessor_of", "successor_of"))
cat("  predecessor_of + successor_of edges:", ps_count, "\n")
if (length(missing_refs) > 0) {
  cat("  Missing references:", length(missing_refs), "\n")
  for (r in head(missing_refs, 5)) {
    cat("    ", r, "\n")
  }
}

# === 2. Subregion_of (subnational -> parent) ===

cat("\n2. Extracting subregion_of relations...\n")
sub_count <- 0L
sub_rows <- df %>% filter(polity_type == "subnational")

for (i in seq_len(nrow(sub_rows))) {
  notes <- sub_rows$notes[i]
  m <- str_match(notes, "Parent:\\s*([A-Z0-9]+-\\d{4}-\\d{4})")
  if (!is.na(m[1, 2]) && m[1, 2] %in% all_codes) {
    add_edge_logged(
      sub_rows$polity_code[i],
      m[1, 2],
      "subregion_of",
      "notes field (Parent)",
      sub_rows$start_year[i],
      sub_rows$end_year[i]
    )
    sub_count <- sub_count + 1L
  }
}
cat("  subregion_of edges:", sub_count, "\n")

# === 3. Aggregate_covers ===

cat("\n3. Extracting aggregate_covers relations...\n")
agg_count <- 0L
aggregates <- df %>% filter(polity_type == "aggregate", !is.na(iso3_code))

for (i in seq_len(nrow(aggregates))) {
  agg <- aggregates[i, ]
  matches <- df %>%
    filter(
      iso3_code == agg$iso3_code,
      polity_type %in%
        c("sovereign", "historical", "colonial", "dependency", "mandate"),
      start_year >= agg$start_year,
      end_year <= agg$end_year
    )
  for (j in seq_len(nrow(matches))) {
    m <- matches[j, ]
    add_edge_logged(
      agg$polity_code,
      m$polity_code,
      "aggregate_covers",
      sprintf("same ISO3 (%s), date range contained", agg$iso3_code),
      m$start_year,
      m$end_year
    )
    agg_count <- agg_count + 1L
  }
}
cat("  aggregate_covers edges:", agg_count, "\n")

# === 4. Temporal_next ===

cat("\n4. Extracting temporal_next relations...\n")
temp_count <- 0L
core <- df %>%
  filter(
    polity_type %in%
      c("sovereign", "historical", "colonial", "dependency", "mandate")
  )

for (iso in unique(na.omit(core$iso3_code))) {
  grp <- core %>% filter(iso3_code == iso) %>% arrange(start_year)
  if (nrow(grp) < 2) {
    next
  }
  for (i in seq_len(nrow(grp) - 1)) {
    gap <- grp$start_year[i + 1] - grp$end_year[i]
    if (gap >= -2 && gap <= 5) {
      add_edge_logged(
        grp$polity_code[i],
        grp$polity_code[i + 1],
        "temporal_next",
        sprintf("same ISO3 (%s), gap=%dy", iso, gap),
        grp$end_year[i],
        grp$start_year[i + 1]
      )
      temp_count <- temp_count + 1L
    }
  }
}
cat("  temporal_next edges:", temp_count, "\n")

# === 5. Colonial_ruler_of ===

cat("\n5. Extracting colonial_ruler_of relations...\n")

colonial_powers <- c(
  British = "GBR",
  Britain = "GBR",
  French = "FRA",
  France = "FRA",
  German = "DEU",
  Germany = "DEU",
  Spanish = "ESP",
  Spain = "ESP",
  Portuguese = "PRT",
  Portugal = "PRT",
  Dutch = "NLD",
  Netherlands = "NLD",
  Italian = "ITA",
  Italy = "ITA",
  Belgian = "BEL",
  Belgium = "BEL",
  Japanese = "JPN",
  Japan = "JPN",
  American = "USA",
  Ottoman = "OTT",
  Turkish = "TUR",
  Soviet = "RUS",
  Russian = "RUS",
  Danish = "DNK",
  Denmark = "DNK"
)

colonial_entries <- df %>%
  filter(polity_type %in% c("colonial", "mandate", "dependency", "puppet"))
col_count <- 0L

for (i in seq_len(nrow(colonial_entries))) {
  row <- colonial_entries[i, ]
  matched <- FALSE
  for (kw in names(colonial_powers)) {
    if (matched) {
      break
    }
    if (str_detect(row$polity_name, fixed(kw))) {
      metro_iso <- colonial_powers[[kw]]
      candidates <- df %>%
        filter(
          iso3_code == metro_iso,
          polity_type %in% c("sovereign", "historical"),
          start_year <= row$end_year,
          end_year >= row$start_year
        )
      if (nrow(candidates) > 0) {
        best <- candidates %>%
          slice_max(duration_years, n = 1, with_ties = FALSE)
        add_edge_logged(
          best$polity_code,
          row$polity_code,
          "colonial_ruler_of",
          sprintf("name contains '%s'", kw),
          max(row$start_year, best$start_year),
          min(row$end_year, best$end_year)
        )
        col_count <- col_count + 1L
        matched <- TRUE
      }
    }
  }
}
cat("  colonial_ruler_of edges:", col_count, "\n")

# === 6. Region_contains (M49 hierarchy) ===

cat("\n6. Extracting region_contains relations...\n")

# Build M49 code -> polity_code mapping
fao_region_map <- list()
for (i in seq_len(nrow(fao))) {
  fao_code <- fao$country_code[i]
  iso3 <- fao$iso3_code[i]
  m49_code <- as.character(fao$m49_code[i])
  if (is.na(iso3)) {
    next
  }

  candidate <- sprintf("F%d-1800-2025", as.integer(fao_code))
  if (candidate %in% all_codes) {
    fao_region_map[[m49_code]] <- candidate
  }
  if (str_starts(as.character(iso3), "X")) {
    match_row <- df %>% filter(iso3_code == iso3) %>% slice(1)
    if (nrow(match_row) > 0) fao_region_map[[m49_code]] <- match_row$polity_code
  }
}

# Continent-level M49 codes
fao_region_map[["2"]] <- "X06-1800-2025"
fao_region_map[["19"]] <- "X21-1800-2025"
fao_region_map[["142"]] <- "F5300-1800-2025"
fao_region_map[["150"]] <- "F5400-1800-2025"
fao_region_map[["9"]] <- "F5500-1800-2025"

region_count <- 0L
for (i in seq_len(nrow(m49))) {
  country_iso3 <- m49$iso3_code[i]
  if (is.na(country_iso3)) {
    next
  }

  country_polities <- df %>%
    filter(
      iso3_code == country_iso3,
      polity_type %in% c("sovereign", "historical")
    )
  if (nrow(country_polities) == 0) {
    next
  }

  latest <- country_polities %>% slice_max(end_year, n = 1, with_ties = FALSE)

  for (col in c("region1_code", "region2_code", "region3_code")) {
    r_code <- as.character(m49[[col]][i])
    if (is.na(r_code)) {
      next
    }
    region_polity <- fao_region_map[[r_code]]
    if (!is.null(region_polity) && region_polity %in% all_codes) {
      add_edge_logged(
        region_polity,
        latest$polity_code,
        "region_contains",
        sprintf("M49 code %s", r_code),
        latest$start_year,
        latest$end_year
      )
      region_count <- region_count + 1L
    }
  }
}
cat("  region_contains edges:", region_count, "\n")

# Region hierarchy
cat("  Extracting M49 region hierarchy...\n")
seen_pairs <- character()
hier_count <- 0L
level_cols <- list(
  c("region1_code", "region1_name"),
  c("region2_code", "region2_name"),
  c("region3_code", "region3_name"),
  c("region4_code", "region4_name")
)

for (i in seq_len(nrow(m49))) {
  levels <- character()
  for (lc in level_cols) {
    code_val <- as.character(m49[[lc[1]]][i])
    if (!is.na(code_val) && code_val %in% names(fao_region_map)) {
      levels <- c(levels, fao_region_map[[code_val]])
    }
  }
  if (length(levels) < 2) {
    next
  }
  for (k in seq_len(length(levels) - 1)) {
    child <- levels[k]
    parent <- levels[k + 1]
    pair_key <- paste(child, parent)
    if (
      !(pair_key %in% seen_pairs) &&
        child %in% all_codes &&
        parent %in% all_codes
    ) {
      add_edge_logged(
        child,
        parent,
        "subregion_of",
        "M49 hierarchy",
        1800L,
        2025L
      )
      seen_pairs <- c(seen_pairs, pair_key)
      hier_count <- hier_count + 1L
    }
  }
}
cat("  Region hierarchy edges:", hier_count, "\n")

# === 7. Located_in_continent ===

cat("\n7. Extracting located_in_continent relations...\n")
cont_count <- 0L
non_region <- df %>% filter(polity_type != "region")

for (i in seq_len(nrow(non_region))) {
  cont <- non_region$continent[i]
  if (!is.na(cont) && cont %in% V(g)$name) {
    add_edge_logged(
      non_region$polity_code[i],
      cont,
      "located_in_continent",
      "continent column",
      non_region$start_year[i],
      non_region$end_year[i]
    )
    cont_count <- cont_count + 1L
  }
}
cat("  located_in_continent edges:", cont_count, "\n")

# === 8. Same_territory ===

cat("\n8. Extracting same_territory relations...\n")
same_count <- 0L
sov_types <- c("sovereign", "historical")
col_types <- c("colonial", "mandate", "dependency", "puppet", "occupation")

for (iso in unique(na.omit(df$iso3_code))) {
  grp <- df %>% filter(iso3_code == iso)
  sov <- grp %>% filter(polity_type %in% sov_types)
  col <- grp %>% filter(polity_type %in% col_types)
  if (nrow(sov) == 0 || nrow(col) == 0) {
    next
  }

  for (si in seq_len(nrow(sov))) {
    for (ci in seq_len(nrow(col))) {
      overlap_start <- max(sov$start_year[si], col$start_year[ci])
      overlap_end <- min(sov$end_year[si], col$end_year[ci])
      if (overlap_start <= overlap_end) {
        add_edge_logged(
          sov$polity_code[si],
          col$polity_code[ci],
          "same_territory",
          sprintf("same ISO3 (%s), temporal overlap", iso),
          overlap_start,
          overlap_end
        )
        same_count <- same_count + 1L
      }
    }
  }
}
cat("  same_territory edges:", same_count, "\n")

# === Summary ===

cat(sprintf(
  "\n%s\nKnowledge Graph Summary\n%s\n",
  strrep("=", 60),
  strrep("=", 60)
))
cat("Nodes:", vcount(g), "\n")
cat("Edges:", ecount(g), "\n\n")

cat("Edges by relation type:\n")
rel_summary <- edge_log %>% count(relation, sort = TRUE)
walk2(
  rel_summary$relation,
  rel_summary$n,
  ~ cat(sprintf("  %-25s %5d\n", .x, .y))
)

cat(sprintf("\nTop 15 most connected nodes:\n"))
deg <- degree(g, mode = "all")
top15 <- sort(deg, decreasing = TRUE)[1:15]
for (nm in names(top15)) {
  idx <- which(V(g)$name == nm)
  pname <- V(g)$polity_name[idx]
  ptype <- V(g)$polity_type[idx]
  cat(sprintf("  %-25s %-40s %-12s degree=%d\n", nm, pname, ptype, top15[[nm]]))
}

# Connected components
comps <- components(as_undirected(g))
cat(sprintf("\nConnected components: %d\n", comps$no))
cat(sprintf("  Largest: %d\n", max(comps$csize)))
orphans <- V(g)$name[degree(g) == 0]
cat(sprintf("  Orphan nodes: %d\n", length(orphans)))

# === Export ===

write_csv(edge_log, file.path(analysis_dir, "knowledge_graph_edges.csv"))
cat(sprintf("\nSaved: knowledge_graph_edges.csv (%d edges)\n", nrow(edge_log)))

node_df <- tibble(
  polity_code = V(g)$name,
  polity_name = V(g)$polity_name,
  polity_type = V(g)$polity_type,
  continent = V(g)$continent,
  start_year = V(g)$start_year,
  end_year = V(g)$end_year,
  iso3_code = V(g)$iso3_code,
  node_type = V(g)$node_type,
  in_degree = degree(g, mode = "in"),
  out_degree = degree(g, mode = "out"),
  total_degree = degree(g, mode = "all")
)
write_csv(node_df, file.path(analysis_dir, "knowledge_graph_nodes.csv"))
cat(sprintf("Saved: knowledge_graph_nodes.csv (%d nodes)\n", nrow(node_df)))

write_graph(
  g,
  file.path(analysis_dir, "knowledge_graph.graphml"),
  format = "graphml"
)
cat("Saved: knowledge_graph.graphml\n\nDone!\n")
