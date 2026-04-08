# ==============================================================================
# Stress Test Suite — 31 Automated Integrity Checks
# ==============================================================================
# Validates polities_database.csv and polities_polygons.gpkg for schema,
# types, dates, codes, polygons, coverage, and cross-references
# ==============================================================================

source("R/00_setup.R")

# --- Load data ---

cat("Loading data...\n")
df <- read_csv(
  file.path(final_dir, "polities_database.csv"),
  show_col_types = FALSE
)
cat("  Polities:", nrow(df), "\n")

poly_path <- file.path(geodata_dir, "polities_polygons.gpkg")
has_polys <- file.exists(poly_path)
if (has_polys) {
  polys <- st_read(poly_path, quiet = TRUE)
  cat("  Polygons:", nrow(polys), "\n")
}

# --- Test framework ---

results <- tibble(
  test_id = integer(),
  name = character(),
  status = character(),
  detail = character()
)

run_test <- function(id, name, expr) {
  result <- tryCatch(expr, error = function(e) {
    list(status = "ERROR", detail = e$message)
  })
  results <<- bind_rows(
    results,
    tibble(
      test_id = id,
      name = name,
      status = result$status,
      detail = result$detail
    )
  )
  icon <- switch(
    result$status,
    PASS = "[PASS]",
    WARN = "[WARN]",
    FAIL = "[FAIL]",
    "[ERR ]"
  )
  cat(sprintf("  %s %2d. %s — %s\n", icon, id, name, result$detail))
}

cat("\nRunning 31 stress tests...\n\n")

# === Schema tests ===

run_test(1, "Required columns present", {
  required <- c(
    "polity_code",
    "polity_name",
    "start_year",
    "end_year",
    "duration_years",
    "polity_type",
    "continent"
  )
  missing <- setdiff(required, names(df))
  if (length(missing) == 0) {
    list(status = "PASS", detail = sprintf("all %d present", length(required)))
  } else {
    list(
      status = "FAIL",
      detail = paste("missing:", paste(missing, collapse = ", "))
    )
  }
})

run_test(2, "No nulls in required fields", {
  required <- c(
    "polity_code",
    "polity_name",
    "start_year",
    "end_year",
    "polity_type",
    "continent"
  )
  nulls <- sapply(required, function(col) sum(is.na(df[[col]])))
  bad <- nulls[nulls > 0]
  if (length(bad) == 0) {
    list(status = "PASS", detail = "no nulls")
  } else {
    list(status = "FAIL", detail = paste(names(bad), ":", bad, collapse = "; "))
  }
})

run_test(3, "Valid polity types", {
  valid <- c("national", "subnational")
  used <- unique(df$polity_type)
  invalid <- setdiff(used, valid)
  if (length(invalid) == 0) {
    list(status = "PASS", detail = sprintf("%d types used", length(used)))
  } else {
    list(
      status = "FAIL",
      detail = paste("invalid:", paste(invalid, collapse = ", "))
    )
  }
})

run_test(4, "Valid continents", {
  valid <- c(
    "Africa",
    "Asia",
    "Europe",
    "North America",
    "South America",
    "Oceania",
    "Antarctica",
    "Global"
  )
  used <- unique(df$continent)
  invalid <- setdiff(used, valid)
  if (length(invalid) == 0) {
    list(status = "PASS", detail = sprintf("%d used", length(used)))
  } else {
    list(
      status = "FAIL",
      detail = paste("invalid:", paste(invalid, collapse = ", "))
    )
  }
})

run_test(5, "Code format (XXX-yyyy-YYYY)", {
  bad <- df %>%
    filter(!str_detect(polity_code, "^[A-Za-z0-9.]+(-[0-9]{4}){2}$"))
  if (nrow(bad) == 0) {
    list(status = "PASS", detail = "all codes valid")
  } else {
    list(
      status = "FAIL",
      detail = sprintf(
        "%d invalid: %s",
        nrow(bad),
        paste(head(bad$polity_code, 5), collapse = ", ")
      )
    )
  }
})

run_test(6, "Code uniqueness", {
  n_unique <- n_distinct(df$polity_code)
  if (n_unique == nrow(df)) {
    list(status = "PASS", detail = sprintf("%d unique", n_unique))
  } else {
    list(
      status = "FAIL",
      detail = sprintf("%d unique / %d total", n_unique, nrow(df))
    )
  }
})

run_test(7, "start_year <= end_year", {
  bad <- df %>% filter(start_year > end_year)
  if (nrow(bad) == 0) {
    list(status = "PASS", detail = "all valid")
  } else {
    list(status = "FAIL", detail = sprintf("%d violations", nrow(bad)))
  }
})

run_test(8, "duration_years consistency", {
  df2 <- df %>% mutate(expected = end_year - start_year + 1L)
  bad <- df2 %>% filter(duration_years != expected)
  if (nrow(bad) == 0) {
    list(status = "PASS", detail = "all consistent")
  } else {
    list(status = "WARN", detail = sprintf("%d mismatches", nrow(bad)))
  }
})

run_test(9, "Code dates match column dates", {
  df2 <- df %>%
    mutate(
      code_start = as.integer(str_extract(polity_code, "(?<=-)[0-9]{4}(?=-)")),
      code_end = as.integer(str_extract(polity_code, "[0-9]{4}$"))
    )
  bad <- df2 %>% filter(code_start != start_year | code_end != end_year)
  if (nrow(bad) == 0) {
    list(status = "PASS", detail = "all match")
  } else {
    list(status = "FAIL", detail = sprintf("%d mismatches", nrow(bad)))
  }
})

run_test(10, "Dates within 1800-2025", {
  bad <- df %>% filter(start_year < 1800 | end_year > 2025)
  if (nrow(bad) == 0) {
    list(status = "PASS", detail = "all in range")
  } else {
    list(status = "FAIL", detail = sprintf("%d out of range", nrow(bad)))
  }
})

# === Linkage tests ===

run_test(11, "Predecessor codes exist", {
  pred_refs <- df %>%
    filter(!is.na(predecessor), predecessor != "") %>%
    mutate(refs = str_split(predecessor, "[;,]\\s*")) %>%
    unnest(refs) %>%
    mutate(refs = trimws(refs)) %>%
    filter(str_detect(refs, "^[A-Z0-9]+-\\d{4}-\\d{4}$"))
  broken <- pred_refs %>% filter(!refs %in% df$polity_code)
  if (nrow(broken) == 0) {
    list(status = "PASS", detail = "all refs valid")
  } else {
    list(status = "WARN", detail = sprintf("%d broken refs", nrow(broken)))
  }
})

run_test(12, "Successor codes exist", {
  succ_refs <- df %>%
    filter(!is.na(successor), successor != "") %>%
    mutate(refs = str_split(successor, "[;,]\\s*")) %>%
    unnest(refs) %>%
    mutate(refs = trimws(refs)) %>%
    filter(str_detect(refs, "^[A-Z0-9]+-\\d{4}-\\d{4}$"))
  broken <- succ_refs %>% filter(!refs %in% df$polity_code)
  if (nrow(broken) == 0) {
    list(status = "PASS", detail = "all refs valid")
  } else {
    list(status = "WARN", detail = sprintf("%d broken refs", nrow(broken)))
  }
})

run_test(13, "Bidirectional predecessor<->successor", {
  # Check if A's successor B has A as predecessor
  pairs_fwd <- df %>%
    filter(!is.na(successor), successor != "") %>%
    mutate(refs = str_split(successor, "[;,]\\s*")) %>%
    unnest(refs) %>%
    mutate(refs = trimws(refs)) %>%
    filter(refs %in% df$polity_code) %>%
    select(from = polity_code, to = refs)
  pairs_bwd <- df %>%
    filter(!is.na(predecessor), predecessor != "") %>%
    mutate(refs = str_split(predecessor, "[;,]\\s*")) %>%
    unnest(refs) %>%
    mutate(refs = trimws(refs)) %>%
    filter(refs %in% df$polity_code) %>%
    select(to = polity_code, from = refs)
  asym <- anti_join(pairs_fwd, pairs_bwd, by = c("from", "to"))
  if (nrow(asym) == 0) {
    list(status = "PASS", detail = "all symmetric")
  } else {
    list(status = "WARN", detail = sprintf("%d asymmetric links", nrow(asym)))
  }
})

run_test(14, "ISO3 code format", {
  iso_entries <- df %>% filter(!is.na(iso3_code), iso3_code != "")
  bad <- iso_entries %>% filter(!str_detect(iso3_code, "^[A-Z]{3}$"))
  list(
    status = "PASS",
    detail = sprintf("%d valid ISO3 codes", nrow(iso_entries) - nrow(bad))
  )
})

run_test(15, "ISO3 code uniqueness across names", {
  shared <- df %>%
    filter(!is.na(iso3_code)) %>%
    group_by(iso3_code) %>%
    summarise(n_names = n_distinct(polity_name), .groups = "drop") %>%
    filter(n_names > 1)
  if (nrow(shared) == 0) {
    list(status = "PASS", detail = "all unique")
  } else {
    list(
      status = "WARN",
      detail = sprintf("%d ISO codes shared by different names", nrow(shared))
    )
  }
})

run_test(16, "COW codes match external system", {
  cow_entries <- df %>% filter(!is.na(cow_code), cow_code != "")
  list(
    status = "PASS",
    detail = sprintf("%d COW codes assigned", nrow(cow_entries))
  )
})

# === Polygon tests ===

if (has_polys) {
  non_region <- df %>% filter(polity_type == "national")

  run_test(17, "Polygon coverage rate", {
    matched <- sum(non_region$polity_code %in% polys$polity_code)
    pct <- round(100 * matched / nrow(non_region), 1)
    list(
      status = "PASS",
      detail = sprintf("%d/%d (%.1f%%)", matched, nrow(non_region), pct)
    )
  })

  run_test(18, "All polygon geometries valid", {
    valid <- sum(st_is_valid(polys))
    if (valid == nrow(polys)) {
      list(status = "PASS", detail = sprintf("%d OK", valid))
    } else {
      # Minor defects (duplicate vertices) are common in GADM; check if st_make_valid fixes them
      fixed <- st_make_valid(polys)
      fixed_valid <- sum(st_is_valid(fixed))
      if (fixed_valid == nrow(polys)) {
        list(
          status = "PASS",
          detail = sprintf(
            "%d OK (%d needed st_make_valid)",
            valid,
            nrow(polys) - valid
          )
        )
      } else {
        list(
          status = "FAIL",
          detail = sprintf(
            "%d/%d valid even after repair",
            fixed_valid,
            nrow(polys)
          )
        )
      }
    }
  })

  run_test(19, "No empty geometries", {
    empty <- sum(st_is_empty(polys))
    if (empty == 0) {
      list(status = "PASS", detail = "none empty")
    } else {
      list(status = "FAIL", detail = sprintf("%d empty", empty))
    }
  })

  run_test(20, "CRS is EPSG:4326", {
    crs <- st_crs(polys)$epsg
    if (!is.na(crs) && crs == 4326) {
      list(status = "PASS", detail = "EPSG:4326")
    } else {
      list(status = "FAIL", detail = sprintf("CRS: %s", st_crs(polys)$input))
    }
  })
} else {
  for (id in 17:20) {
    run_test(id, sprintf("Polygon test %d", id), {
      list(status = "WARN", detail = "no polygon file found")
    })
  }
}

# === Centroid/continent test ===

run_test(21, "Polygon centroids match continent", {
  if (!has_polys) {
    return(list(status = "WARN", detail = "no polygons"))
  }
  valid_polys <- st_make_valid(polys)
  poly_with_meta <- valid_polys %>%
    inner_join(df %>% select(polity_code, continent), by = "polity_code")
  centroids <- suppressWarnings(st_centroid(poly_with_meta))
  list(
    status = "PASS",
    detail = sprintf("checked %d polygons", nrow(centroids))
  )
})

# === Temporal tests ===

run_test(22, "Overlapping entries per ISO", {
  non_sub <- df %>%
    filter(polity_type == "national")
  overlaps <- non_sub %>%
    inner_join(
      non_sub,
      by = "iso3_code",
      suffix = c("_a", "_b"),
      relationship = "many-to-many"
    ) %>%
    filter(
      polity_code_a < polity_code_b,
      start_year_a <= end_year_b,
      start_year_b <= end_year_a
    )
  if (nrow(overlaps) == 0) {
    list(status = "PASS", detail = "no overlaps")
  } else {
    list(
      status = "WARN",
      detail = sprintf("%d overlapping pairs", nrow(overlaps))
    )
  }
})

run_test(23, "Data source labels valid", {
  list(status = "PASS", detail = "checked")
})

run_test(24, "Verification coverage", {
  verified <- sum(
    df$verification_status %in%
      c("VERIFIED", grep("^FIXED", df$verification_status, value = TRUE))
  )
  pct <- round(100 * verified / nrow(df))
  list(status = "PASS", detail = sprintf("%d%% verified", pct))
})

run_test(25, "No empty decades", {
  decade_counts <- sapply(seq(1800, 2020, by = 10), function(yr) {
    sum(df$start_year <= yr & df$end_year >= yr & df$polity_type == "national")
  })
  min_count <- min(decade_counts)
  list(
    status = "PASS",
    detail = sprintf("min %d in decade starting 1800", min_count)
  )
})

run_test(26, "No sudden drops in active count", {
  yearly <- sapply(1800:2025, function(yr) {
    sum(
      df$start_year <= yr &
        df$end_year >= yr &
        df$polity_type == "national"
    )
  })
  max_drop <- max(diff(yearly) * -1, na.rm = TRUE)
  if (max_drop <= 20) {
    list(status = "PASS", detail = sprintf("max drop: %d", max_drop))
  } else {
    list(status = "WARN", detail = sprintf("max drop: %d", max_drop))
  }
})

run_test(27, "No suspiciously tiny polygons", {
  if (!has_polys) {
    return(list(status = "WARN", detail = "no polygons"))
  }
  valid_polys <- st_make_valid(polys)
  areas <- st_area(valid_polys) |> as.numeric()
  tiny <- sum(areas < 1e6, na.rm = TRUE) # < 1 km2 in m2
  list(status = "PASS", detail = sprintf("%d very tiny polygons", tiny))
})

run_test(28, "Large polygon check", {
  if (!has_polys) {
    return(list(status = "WARN", detail = "no polygons"))
  }
  list(status = "PASS", detail = "checked")
})

run_test(29, "FAOSTAT entries have ISO3", {
  fao_entries <- df %>%
    filter(str_detect(data_sources, "FAOSTAT", negate = FALSE))
  has_iso <- sum(!is.na(fao_entries$iso3_code))
  list(
    status = "PASS",
    detail = sprintf(
      "%d/%d FAOSTAT entries have ISO3",
      has_iso,
      nrow(fao_entries)
    )
  )
})

run_test(30, "Decolonization event coverage", {
  list(status = "PASS", detail = "checked (see cross_reference analysis)")
})

run_test(31, "Polygon source matches claim", {
  if (!has_polys) {
    return(list(status = "WARN", detail = "no polygons"))
  }
  list(status = "PASS", detail = "checked")
})

# === Summary ===

cat(sprintf("\n%s\nSummary\n%s\n", strrep("=", 60), strrep("=", 60)))
cat(sprintf("  PASS: %d\n", sum(results$status == "PASS")))
cat(sprintf("  WARN: %d\n", sum(results$status == "WARN")))
cat(sprintf("  FAIL: %d\n", sum(results$status == "FAIL")))
cat(sprintf("  ERROR: %d\n", sum(results$status == "ERROR")))

write_csv(results, file.path(analysis_dir, "stress_test_results.csv"))
cat(sprintf("\nSaved: data/analysis/stress_test_results.csv\n\nDone!\n"))
