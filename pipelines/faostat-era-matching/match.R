# faostat-era-matching/match.R
#
# Deterministic matcher: FAOSTAT-era (1961+) reporting areas -> WHEP polities.
#
# Scans the WHEP package's cached FAOSTAT pins for every reporting area that
# actually carries data (area_code, area name, observed year span, row count),
# matches each area to the WHEP polity period(s) covering its span, and emits
# year-ranged routing aliases. High-confidence rows are appended (idempotent)
# to pipelines/polity-autoimprove/state/applied_aliases.csv with
# source = "faostat", so the alias table knows about the FAOSTAT era without
# ever affecting other sources (rules are source- and year-scoped).
#
# Run from the repo root:
#   Rscript --vanilla pipelines/faostat-era-matching/match.R [--no-apply]
#
# Env:
#   WHEP_REPO  path to a WHEP checkout (pins cache + area registry).
#              Default /home/usuario/WHEP.

# Rscript --vanilla starts in the C locale; area names are UTF-8 (Türkiye,
# Côte d'Ivoire), so string handling needs a UTF-8 locale.
invisible(suppressWarnings(Sys.setlocale("LC_CTYPE", "C.UTF-8")))

suppressMessages({
  library(dplyr)
  library(readr)
  library(purrr)
  library(tidyr)
})

args <- commandArgs(trailingOnly = TRUE)
apply_aliases <- !("--no-apply" %in% args)

whep_repo <- Sys.getenv("WHEP_REPO", unset = "/home/usuario/WHEP")
pipe_dir <- file.path("pipelines", "faostat-era-matching")
state_dir <- file.path(pipe_dir, "state")
dir.create(state_dir, showWarnings = FALSE, recursive = TRUE)
applied_path <- file.path(
  "pipelines", "polity-autoimprove", "state", "applied_aliases.csv"
)

faostat_era_start <- 1961L

# Pins scanned for the observed reporting-area inventory. Column names vary
# slightly across dumps; resolved per file below.
pins <- c(
  "faostat-production",
  "faostat-fbs-new",
  "faostat-fbs-old",
  "faostat-cbs-old-crops",
  "faostat-cbs-old-animal",
  "faostat-cbs-new",
  "faostat-trade-totals"
)

# -- 1. Observed inventory from WHEP pins --------------------------------------

message("Loading WHEP from ", whep_repo)
suppressMessages(devtools::load_all(whep_repo, quiet = TRUE))

col_candidates <- list(
  area_code = c("Area Code", "AreaCode", "area_code"),
  area_name = c("Area", "AreaName", "area"),
  year = c("Year", "year")
)

scan_pin <- function(alias) {
  message("Scanning pin ", alias)
  paths <- tryCatch(
    getFromNamespace(".download_pin_paths", "whep")(alias),
    error = function(e) {
      message("  skipped (", conditionMessage(e), ")")
      NULL
    }
  )
  parquet <- grep("\\.parquet$", paths %||% character(), value = TRUE)
  if (length(parquet) == 0L) {
    return(NULL)
  }
  ds <- arrow::open_dataset(parquet, format = "parquet")
  resolved <- map_chr(col_candidates, function(cands) {
    hit <- intersect(cands, names(ds))
    if (length(hit) == 0L) NA_character_ else hit[[1L]]
  })
  if (anyNA(resolved)) {
    message("  skipped (columns not found)")
    return(NULL)
  }
  ds |>
    select(all_of(unname(resolved))) |>
    rename(
      area_code = all_of(resolved[["area_code"]]),
      area_name = all_of(resolved[["area_name"]]),
      year = all_of(resolved[["year"]])
    ) |>
    collect() |>
    mutate(
      area_code = as.integer(area_code),
      year = as.integer(year),
      pin = alias
    ) |>
    filter(!is.na(area_code), !is.na(year))
}

`%||%` <- function(a, b) if (is.null(a)) b else a

# Some pin dumps carry latin1-encoded names (e.g. C\xf4te d'Ivoire); force
# valid UTF-8 so names round-trip through the alias CSV.
.fix_utf8 <- function(x) {
  bad <- !validUTF8(x)
  x[bad] <- iconv(x[bad], "latin1", "UTF-8")
  x
}

observed <- pins |>
  map(scan_pin) |>
  compact() |>
  bind_rows() |>
  mutate(area_name = .fix_utf8(area_name))

inventory <- observed |>
  summarise(
    year_first = min(year),
    year_last = max(year),
    n_rows = n(),
    pins = paste(sort(unique(pin)), collapse = ";"),
    .by = c(area_code, area_name)
  ) |>
  # One name per code: keep the name carrying the most rows (current label).
  arrange(area_code, desc(n_rows)) |>
  mutate(
    n_rows = sum(n_rows),
    year_first = min(year_first),
    year_last = max(year_last),
    pins = paste(sort(unique(unlist(strsplit(pins, ";")))), collapse = ";"),
    .by = area_code
  ) |>
  distinct(area_code, .keep_all = TRUE)

message("Observed reporting areas: ", nrow(inventory))

# -- 2. ISO3 attribution (FAOSTAT registry metadata via WHEP crosswalk) --------

crosswalk_env <- new.env()
load(
  file.path(whep_repo, "data", "polity_area_crosswalk.rda"),
  envir = crosswalk_env
)
area_iso3 <- crosswalk_env$polity_area_crosswalk |>
  as_tibble() |>
  filter(!is.na(area_code)) |>
  distinct(area_code, iso3 = area_iso3c)

inventory <- inventory |> left_join(area_iso3, by = "area_code")

# FAOSTAT statistical aggregates are intentionally unrouted: their rows sum
# other reporting areas, so routing them to a polity would double-count.
# Codes >= 5000 are FAOSTAT group codes (World, continents, income groups);
# 351 "China" is the mainland+HKG+MAC+TWN aggregate reported alongside its
# components (see pipelines/pre1961-matching and the WHEP crosswalk).
aggregate_codes <- c(351L)
aggregates <- inventory |>
  filter(
    area_code >= 5000L |
      area_code %in% aggregate_codes |
      # Trade-reporter groups (EU-N, China incl. components).
      grepl("excluding intra-trade", area_name, fixed = TRUE)
  )
inventory <- inventory |>
  anti_join(aggregates, by = "area_code")

# -- 3. Polity families --------------------------------------------------------

polities <- suppressWarnings(read_csv(
  file.path("data", "final", "polities_database.csv"),
  show_col_types = FALSE
)) |>
  mutate(
    start_year = suppressWarnings(as.integer(start_year)),
    end_year = suppressWarnings(as.integer(end_year))
  )

malformed_polities <- polities |>
  filter(is.na(start_year) | is.na(end_year))
if (nrow(malformed_polities) > 0L) {
  warning(
    "Skipping polity rows with unparseable years (malformed CSV?): ",
    paste(malformed_polities$polity_code, collapse = ", ")
  )
  polities <- polities |> anti_join(malformed_polities, by = "polity_code")
}

# FAOSTAT composite reporting areas whose family is not their ISO3 family:
# dissolved-state reporting areas route to the WHEP composite polities, and
# "Sudan (former)" (206, iso3 SDN) reports the pre-2011 undivided Sudan (SUD),
# not the post-2011 rump state.
manual_prefix <- c(
  "51" = "F51", # Czechoslovakia
  "206" = "SUD", # Sudan (former)
  "228" = "F228", # USSR
  "248" = "F248" # Yugoslav SFR
)

polity_prefix <- sub("-.*", "", polities$polity_code)

family_for <- function(area_code, iso3) {
  key <- as.character(area_code)
  if (key %in% names(manual_prefix)) {
    fam <- polities[polity_prefix == manual_prefix[[key]], ]
    return(list(fam = fam, route = "manual-route"))
  }
  if (!is.na(iso3) && iso3 %in% polities$iso3_code) {
    fam <- polities[!is.na(polities$iso3_code) & polities$iso3_code == iso3, ]
    return(list(fam = fam, route = "iso-equal"))
  }
  list(fam = polities[0, ], route = "no-family")
}

# -- 4. Match each area's observed span to polity periods ----------------------

match_area <- function(row) {
  span0 <- max(row$year_first, faostat_era_start)
  span1 <- row$year_last
  res <- family_for(row$area_code, row$iso3)
  fam <- res$fam

  if (nrow(fam) == 0L) {
    return(tibble(
      area_code = row$area_code,
      area_name = row$area_name,
      iso3 = row$iso3,
      year_start = span0,
      year_end = span1,
      target_polity_code = NA_character_,
      common_name = NA_character_,
      match_route = res$route,
      match_status = "unmatched",
      note = "no polity family for this reporting area"
    ))
  }

  national <- fam[fam$polity_type == "national", ]
  if (nrow(national) > 0L) {
    fam <- national
  }
  fam <- fam |>
    filter(start_year <= span1, end_year >= span0) |>
    arrange(start_year)

  if (nrow(fam) == 0L) {
    return(tibble(
      area_code = row$area_code,
      area_name = row$area_name,
      iso3 = row$iso3,
      year_start = span0,
      year_end = span1,
      target_polity_code = NA_character_,
      common_name = NA_character_,
      match_route = res$route,
      match_status = "unmatched",
      note = "family exists but no period intersects the observed span"
    ))
  }

  pieces <- fam |>
    mutate(
      year_start = pmax(start_year, span0),
      year_end = pmin(end_year, span1)
    )
  # Adjacent WHEP periods share their boundary year (ESP-1800-2025 style
  # spans); a shared endpoint is not an ambiguity. Real overlaps are.
  overlapping <- nrow(pieces) > 1L &&
    any(pieces$year_start[-1L] < pieces$year_end[-nrow(pieces)])
  covered_years <- unique(unlist(
    Map(seq.int, pieces$year_start, pieces$year_end)
  ))
  uncovered <- setdiff(seq.int(span0, span1), covered_years)
  gap_note <- if (length(uncovered) > 0L) {
    sprintf(
      "no covering polity period for observed years %s",
      .format_year_ranges(uncovered)
    )
  } else {
    NA_character_
  }

  pieces |>
    transmute(
      area_code = row$area_code,
      area_name = row$area_name,
      iso3 = row$iso3,
      year_start,
      year_end,
      target_polity_code = polity_code,
      common_name = polity_name,
      match_route = res$route,
      match_status = if_else(overlapping, "ambiguous", "matched"),
      note = if_else(
        overlapping,
        "overlapping polity periods for this span",
        gap_note
      )
    )
}

.format_year_ranges <- function(years) {
  years <- sort(years)
  breaks <- c(0L, which(diff(years) > 1L), length(years))
  ranges <- map_chr(seq_len(length(breaks) - 1L), function(i) {
    lo <- years[breaks[i] + 1L]
    hi <- years[breaks[i + 1L]]
    if (lo == hi) as.character(lo) else sprintf("%d-%d", lo, hi)
  })
  paste(ranges, collapse = ", ")
}

matches <- inventory |>
  group_split(area_code) |>
  map(\(g) match_area(as.list(g[1, ]))) |>
  bind_rows() |>
  left_join(
    inventory |> select(area_code, n_rows, pins),
    by = "area_code"
  )

# -- 5. Write pipeline state ---------------------------------------------------

alias_base <- matches |>
  filter(!is.na(target_polity_code)) |>
  mutate(
    source = "faostat",
    confidence = "high",
    basis = sprintf(
      paste0(
        "FAOSTAT area code %d; observed %d-%d in pins %s; %s period match%s"
      ),
      area_code, year_start, year_end, pins, match_route,
      if_else(is.na(note), "", paste0("; ", note))
    )
  ) |>
  select(
    original_name = area_name,
    source,
    year_start,
    year_end,
    common_name,
    target_polity_code,
    confidence,
    basis,
    rows = n_rows,
    area_code,
    iso3,
    match_route,
    match_status,
    note
  )

aliases <- alias_base |> filter(match_status == "matched")
ambiguous <- alias_base |> filter(match_status == "ambiguous")
gaps <- aliases |> filter(!is.na(note)) |> distinct(area_code, .keep_all = TRUE)

unmatched <- matches |>
  filter(is.na(target_polity_code)) |>
  select(area_code, area_name, iso3, year_start, year_end, note, n_rows, pins)

write_csv(select(aliases, -note), file.path(state_dir, "faostat_aliases.csv"))
write_csv(ambiguous, file.path(state_dir, "ambiguous.csv"))
write_csv(unmatched, file.path(state_dir, "unmatched.csv"))
write_csv(aggregates, file.path(state_dir, "aggregates.csv"))

.report_lines <- function(df, fmt_fn) {
  if (nrow(df) == 0L) "(none)" else fmt_fn(df)
}

report <- c(
  "# faostat-era-matching report",
  "",
  sprintf(
    "- Observed reporting areas (1961+): %d (+%d statistical aggregates, intentionally unrouted)",
    nrow(inventory), nrow(aggregates)
  ),
  sprintf("- Alias rows emitted: %d", nrow(aliases)),
  sprintf("- Areas with coverage gaps (early years without a polity period): %d", nrow(gaps)),
  sprintf("- Ambiguous areas (overlapping polity periods, not applied): %d", n_distinct(ambiguous$area_code)),
  sprintf("- Unmatched areas: %d", nrow(unmatched)),
  "",
  "## Coverage gaps (autoimprove queue)",
  "",
  .report_lines(gaps, \(df) sprintf(
    "- %s (%d): %s", df$original_name, df$area_code, df$note
  )),
  "",
  "## Ambiguous areas (autoimprove queue)",
  "",
  .report_lines(ambiguous, \(df) sprintf(
    "- %s (%d) %d-%d -> candidate %s",
    df$original_name, df$area_code, df$year_start, df$year_end,
    df$target_polity_code
  )),
  "",
  "## Unmatched areas (autoimprove queue)",
  "",
  .report_lines(unmatched, \(df) sprintf(
    "- %s (%d) %d-%d: %s [%d rows]",
    df$area_name, df$area_code, df$year_start, df$year_end, df$note, df$n_rows
  ))
)
writeLines(report, file.path(state_dir, "report.md"))
message("Wrote state files under ", state_dir)

# -- 6. Merge into applied_aliases.csv (idempotent) ----------------------------

if (apply_aliases) {
  # The alias file is curated by hand and by agents; a few historical rows
  # are malformed (extra/short columns) and the python matcher reads them
  # leniently. Never rewrite existing lines — append only.
  applied_keys <- suppressWarnings(read_csv(
    applied_path,
    col_types = cols(.default = col_character())
  )) |>
    select(original_name, source, year_start, year_end)
  canonical <- aliases |>
    select(
      original_name,
      source,
      year_start,
      year_end,
      common_name,
      target_polity_code,
      confidence,
      basis,
      rows
    )
  new_rows <- canonical |>
    mutate(
      year_start_chr = as.character(year_start),
      year_end_chr = as.character(year_end)
    ) |>
    anti_join(
      applied_keys,
      by = c(
        "original_name",
        "source",
        "year_start_chr" = "year_start",
        "year_end_chr" = "year_end"
      )
    ) |>
    select(-year_start_chr, -year_end_chr)
  if (nrow(new_rows) > 0L) {
    existing <- readBin(
      applied_path,
      what = "raw",
      n = file.size(applied_path)
    )
    needs_newline <- length(existing) > 0L &&
      existing[length(existing)] != as.raw(10L)
    lines <- format_csv(new_rows)
    lines <- sub("^[^\n]*\n", "", lines, useBytes = TRUE) # drop header
    # Byte-level append: keeps existing lines untouched and sidesteps any
    # locale translation of non-ASCII area names (e.g. Türkiye).
    con <- file(applied_path, open = "ab")
    if (needs_newline) {
      writeBin(charToRaw("\n"), con)
    }
    writeBin(charToRaw(enc2utf8(lines)), con)
    close(con)
  }
  message(
    "Appended ", nrow(new_rows), " new rows to ", applied_path,
    " (", nrow(canonical) - nrow(new_rows), " already present)"
  )
} else {
  message("--no-apply: skipped merge into ", applied_path)
}
