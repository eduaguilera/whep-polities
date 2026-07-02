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

# Retired/superseded rows are kept in the DB for provenance but must never
# receive data (e.g. DJI-1886-2025 is retired in favour of the FRS chain).
polities <- polities |>
  filter(!wiki_status %in% c("retired", "superseded"))

# FAOSTAT reporting areas whose polity chain is not (only) their ISO3
# family: dissolved-state reporting areas route to WHEP composite polities,
# "Sudan (former)" (206, iso3 SDN) reports the pre-2011 undivided Sudan
# (SUD), and pre-independence chains carry their own prefixes (Portuguese
# Angola ANG, Bechuanaland BEC, French Somaliland FRS). The manual prefix
# EXTENDS the ISO3 family, so post-independence periods still match.
manual_prefix <- c(
  "7" = "ANG", # Angola (Portuguese, to 1975)
  "20" = "BEC", # Botswana (Bechuanaland Protectorate, to 1966)
  "51" = "F51", # Czechoslovakia
  "72" = "FRS", # Djibouti (French Somaliland chain)
  "206" = "SUD", # Sudan (former)
  "228" = "F228", # USSR
  "248" = "F248" # Yugoslav SFR
)

polity_prefix <- sub("-.*", "", polities$polity_code)

family_for <- function(area_code, iso3) {
  key <- as.character(area_code)
  fam <- polities[0, ]
  route <- "no-family"
  if (!is.na(iso3) && iso3 %in% polities$iso3_code) {
    fam <- polities[!is.na(polities$iso3_code) & polities$iso3_code == iso3, ]
    route <- "iso-equal"
  }
  if (key %in% names(manual_prefix)) {
    fam <- bind_rows(
      fam,
      polities[polity_prefix == manual_prefix[[key]], ]
    ) |>
      distinct(polity_code, .keep_all = TRUE)
    route <- "manual-route"
  }
  list(fam = fam, route = route)
}

# Preference order when several polity periods cover the same years.
.polity_type_rank <- function(type) {
  rank <- c(
    national = 1,
    colonial = 2,
    territory = 3,
    "city-territory" = 3,
    disputed = 4,
    aggregate = 5,
    statistical = 6
  )
  out <- unname(rank[type])
  out[is.na(out)] <- 7
  out
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

  pieces <- .match_span(fam, span0, span1)
  uncovered <- pieces |> filter(is.na(target_polity_code))
  gap_note <- if (nrow(uncovered) > 0L) {
    sprintf(
      "no covering polity period for observed years %s",
      .format_year_ranges(unlist(
        Map(seq.int, uncovered$year_start, uncovered$year_end)
      ))
    )
  } else {
    NA_character_
  }

  pieces |>
    filter(!is.na(target_polity_code)) |>
    transmute(
      area_code = row$area_code,
      area_name = row$area_name,
      iso3 = row$iso3,
      year_start,
      year_end,
      target_polity_code,
      common_name,
      match_route = res$route,
      match_status,
      note = if_else(
        match_status == "ambiguous",
        "overlapping polity periods for this span",
        gap_note
      )
    )
}

# Split [span0, span1] at every period boundary; per segment pick the
# covering period, preferring national > colonial > territory. Several
# best-ranked candidates from the SAME polity prefix mean blanket +
# periodized modelling of one chain: the most specific (shortest) period
# wins. Candidates from DIFFERENT prefixes are genuinely simultaneous
# entities (e.g. Malaya vs Sarawak vs North Borneo for FAOSTAT "Malaysia"
# 1961-1963): all are emitted as ambiguous, never silently picked.
# Uncovered segments come back with NA target so the caller can flag them.
.match_span <- function(fam, span0, span1) {
  bounds <- sort(unique(c(
    span0,
    span1 + 1L,
    pmax(fam$start_year, span0),
    pmin(fam$end_year, span1) + 1L
  )))
  segments <- tibble(
    seg_start = bounds[-length(bounds)],
    seg_end = bounds[-1L] - 1L
  ) |>
    filter(seg_start <= seg_end)

  pieces <- segments |>
    pmap(function(seg_start, seg_end) {
      covering <- fam |>
        filter(start_year <= seg_start, end_year >= seg_end)
      if (nrow(covering) == 0L) {
        return(tibble(
          year_start = seg_start,
          year_end = seg_end,
          target_polity_code = NA_character_,
          common_name = NA_character_,
          match_status = "uncovered"
        ))
      }
      if (seg_start == seg_end && nrow(covering) > 1L) {
        # Adjacent WHEP periods share their transition year (predecessor
        # ends the year the successor starts). Mirror the pre-1961 rules
        # ("SDN < 2011 -> SUD"): the shared boundary year routes to the
        # successor, before any type or specificity preference. Only
        # applies when every candidate either starts or ends exactly on
        # this year — anything else is real ambiguity.
        starters <- covering |> filter(start_year == seg_start)
        enders <- covering |>
          filter(end_year == seg_end, start_year < seg_start)
        if (
          nrow(starters) > 0L &&
            nrow(starters) + nrow(enders) == nrow(covering)
        ) {
          covering <- starters
        }
      }
      best <- covering |>
        filter(
          .polity_type_rank(polity_type) ==
            min(.polity_type_rank(covering$polity_type))
        )
      prefixes <- unique(sub("-.*", "", best$polity_code))
      if (length(prefixes) == 1L) {
        best <- best |>
          arrange(end_year - start_year) |>
          slice(1L)
      }
      best |>
        transmute(
          year_start = seg_start,
          year_end = seg_end,
          target_polity_code = polity_code,
          common_name = polity_name,
          match_status = if_else(
            length(prefixes) == 1L,
            "matched",
            "ambiguous"
          )
        )
    }) |>
    bind_rows()

  # Merge runs of adjacent segments resolved to the same polity (a blanket
  # period can win several consecutive segments). Ambiguous rows are kept
  # as-is: one row per candidate.
  resolved <- pieces |>
    filter(match_status != "ambiguous") |>
    arrange(year_start) |>
    mutate(
      run_key = coalesce(target_polity_code, "<uncovered>"),
      run = cumsum(coalesce(
        run_key != lag(run_key) | year_start != lag(year_end) + 1L,
        TRUE
      ))
    ) |>
    summarise(
      year_start = min(year_start),
      year_end = max(year_end),
      target_polity_code = target_polity_code[1L],
      common_name = common_name[1L],
      match_status = match_status[1L],
      .by = run
    ) |>
    select(-run)

  bind_rows(resolved, filter(pieces, match_status == "ambiguous")) |>
    arrange(year_start)
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

# Curated routes for spans the deterministic matcher must leave ambiguous,
# each resolved from data magnitudes (recorded in the basis). Kept here —
# not as hand rows in applied_aliases.csv — because the faostat merge is
# replace-by-source and would wipe hand rows on the next run.
manual_span_routes <- tibble::tribble(
  ~area_code,
  ~year_start,
  ~year_end,
  ~target_polity_code,
  ~route_basis,
  131L,
  1961L,
  1962L,
  "MYS-1957-1963",
  paste(
    "FAOSTAT Malaysia pre-1963 is the Federation of Malaya (peninsula):",
    "natural-rubber production jumps ~23% between 1962 and 1963 when",
    "Sabah and Sarawak accede - a territorial step, not organic growth",
    "for a tree crop"
  )
)

.apply_span_routes <- function(matches, routes, polities) {
  for (i in seq_len(nrow(routes))) {
    r <- routes[i, ]
    hit <- matches$area_code == r$area_code &
      matches$match_status == "ambiguous" &
      matches$year_start >= r$year_start &
      matches$year_end <= r$year_end
    if (!any(hit)) {
      next
    }
    resolved <- matches[which(hit)[1L], ] |>
      mutate(
        year_start = r$year_start,
        year_end = r$year_end,
        target_polity_code = r$target_polity_code,
        common_name = polities$polity_name[
          polities$polity_code == r$target_polity_code
        ][1L],
        match_route = "manual-span",
        match_status = "matched",
        note = r$route_basis
      )
    matches <- bind_rows(matches[!hit, ], resolved)
  }
  matches
}

matches <- inventory |>
  group_split(area_code) |>
  map(\(g) match_area(as.list(g[1, ]))) |>
  bind_rows() |>
  .apply_span_routes(manual_span_routes, polities) |>
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
gaps <- aliases |>
  filter(!is.na(note), match_route != "manual-span") |>
  distinct(area_code, .keep_all = TRUE)

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
  # source = "faostat" rows are wholly machine-generated by this pipeline,
  # so the merge is replace-by-source: drop every existing faostat row and
  # append the fresh set. Rows from other sources are kept byte-identical
  # (a few historical hand-appended rows are malformed and must never be
  # re-serialised through a CSV parser).
  existing_lines <- readLines(applied_path, encoding = "UTF-8", warn = FALSE)
  kept <- existing_lines[
    !grepl(",faostat,", existing_lines, fixed = TRUE, useBytes = TRUE)
  ]
  dropped <- length(existing_lines) - length(kept)

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
  new_lines <- format_csv(canonical)
  new_lines <- sub("^[^\n]*\n", "", new_lines, useBytes = TRUE) # drop header

  con <- file(applied_path, open = "wb")
  writeBin(charToRaw(enc2utf8(paste0(
    paste(kept, collapse = "\n"),
    "\n",
    new_lines
  ))), con)
  close(con)
  message(
    "Replaced ", dropped, " faostat rows with ", nrow(canonical),
    " in ", applied_path
  )
} else {
  message("--no-apply: skipped merge into ", applied_path)
}
