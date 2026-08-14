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
#   Rscript --vanilla pipelines/faostat-era-matching/match.R [--no-apply] [--accept-diff]
#
# --accept-diff (or env WHEP_FAOSTAT_ACCEPT_DIFF=1): accept a merge that
# drops or retargets EXISTING faostat rows in applied_aliases.csv (only
# legitimate after an intentional match.R route change; the guard otherwise
# aborts so hand-edits are never silently wiped).
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

# A polity period is [start_year, end_year): `end_year` is EXCLUSIVE, while the
# alias `year_end` this script EMITS is INCLUSIVE, so a consistent pair has
# end_year == year_end + 1. Named rather than written as a bare `- 1L` because
# the two readings of one field, each plausible and neither erroring, is issue
# #131; scripts/validate_year_semantics.py fails if this file, matchlib.py or
# pipelines/pre1961-matching/match.R stops declaring and using it.
END_YEAR_EXCLUSIVE <- TRUE

# INCLUSIVE last year covered by a period whose exclusive bound is `end_year`.
last_covered_year <- function(end_year) {
  end_year - as.integer(END_YEAR_EXCLUSIVE)
}

# The OTHER half of the same conversion, and the one this script actually needs:
# the alias `year_end` it emits is INCLUSIVE, so it equals the last covered year.
# Named for the same reason END_YEAR_EXCLUSIVE is — the alias reading was left as
# an unnamed assumption when the polity reading was fixed, which is precisely the
# shape of issue #131 one field over. matchlib.py declares the same constant and
# scripts/validate_year_semantics.py fails if either file stops doing so.
ALIAS_YEAR_END_INCLUSIVE <- TRUE

# The alias `year_end` that means the same last covered year as `end_year`.
alias_year_end <- function(end_year) {
  last_covered_year(end_year) + (1L - as.integer(ALIAS_YEAR_END_INCLUSIVE))
}

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
  anti_join(aggregates, by = "area_code") |>
  mutate(has_data = TRUE)

# Registry completeness: WHEP's PROCESSED production imputes rows for
# reporting areas that carry no data in the RAW pins (micro-states like
# Andorra, dependent territories). The alias table must map those too, or a
# straight swap in WHEP's crosswalk would drop their polity. Add every
# crosswalk area we did NOT observe and that isn't an aggregate, excluding
# the 900+ WHEP-internal codes (999 RoW, 901-906 "X Other") which are
# FABIO-collapse TARGETS, not raw FAOSTAT reporting areas.
registry <- crosswalk_env$polity_area_crosswalk |>
  as_tibble() |>
  filter(!is.na(area_code), area_code < 900L) |>
  distinct(area_code, area_name, iso3 = area_iso3c)
nodata <- registry |>
  anti_join(inventory, by = "area_code") |>
  anti_join(aggregates, by = "area_code") |>
  mutate(
    year_first = NA_integer_,
    year_last = NA_integer_,
    n_rows = 0L,
    pins = "(no data in scanned pins)",
    has_data = FALSE
  )
inventory <- bind_rows(inventory, nodata)
message("  + ", nrow(nodata), " no-data registry areas for completeness")

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

# EXTEND routes: the manual prefix is added ON TOP of the ISO3 family, so
# post-independence periods still match via iso3. Pre-independence colonial
# chains (Portuguese Angola ANG, Bechuanaland BEC, French Somaliland FRS) and
# French overseas départements (GUF/REU, whose polity rows carry iso3_code=NA
# so an iso3 match alone misses them) sit here.
manual_prefix <- c(
  "7" = "ANG", # Angola (Portuguese, to 1975) + modern AGO via iso3
  "20" = "BEC", # Botswana (Bechuanaland Protectorate) + modern BWA via iso3
  "69" = "GUF", # French Guiana (iso3 NA on GUF polity rows)
  "72" = "FRS", # Djibouti (French Somaliland chain) + modern DJI via iso3
  "182" = "REU" # Réunion (iso3 NA on REU polity rows)
)

# REPLACE routes: a FORMER-entity reporting code whose successor(s) report
# under their OWN code. Its data ALWAYS represents the former polity's
# territory, so the ISO3 family is REPLACED (not extended) — otherwise a
# successor whose iso3 the former code happens to carry leaks into the
# candidate set. Critical for 206 "Sudan (former)", whose crosswalk iso3 is
# SDN (the rump successor): without this, undivided-Sudan data at the shared
# 2011 boundary year is mis-assigned to rump SDN (a ~25%-smaller territory,
# dropping South Sudan's share) and collides with area 276. The dissolved
# states (51/228/248) map to their WHEP composite F-polities the same way.
manual_prefix_replace <- c(
  "51" = "F51", # Czechoslovakia (successors CZE 167 / SVK 199)
  "206" = "SUD", # undivided Sudan (rump Sudan reports under 276)
  "228" = "F228", # USSR (successor republics have own codes)
  "248" = "F248" # Yugoslav SFR (successor republics have own codes)
)

polity_prefix <- sub("-.*", "", polities$polity_code)

family_for <- function(area_code, iso3) {
  key <- as.character(area_code)
  if (key %in% names(manual_prefix_replace)) {
    return(list(
      fam = polities[polity_prefix == manual_prefix_replace[[key]], ],
      route = "manual-replace"
    ))
  }
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
  res <- family_for(row$area_code, row$iso3)
  fam <- res$fam

  # No-data registry areas: no observed span to split. Emit the family's
  # periods so WHEP can map the area at any year; if there is no family it
  # is a genuine non-country (Antarctica, "Unspecified", uninhabited isle)
  # and stays unmapped WITHOUT becoming an actionable finding.
  if (!isTRUE(row$has_data)) {
    return(.match_registry(row, fam, res$route))
  }

  span0 <- max(row$year_first, faostat_era_start)
  span1 <- row$year_last

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

# No-data registry area -> one alias row per family period (best type rank),
# clamped to WHEP's [1850, 2025] range. No observed data, so never a
# coverage gap or ambiguity finding; areas with no family are marked
# 'registry_unmapped' (informational, not an actionable finding).
.match_registry <- function(row, fam, route) {
  base <- tibble(
    area_code = row$area_code,
    area_name = row$area_name,
    iso3 = row$iso3
  )
  if (nrow(fam) == 0L) {
    return(base |>
      mutate(
        year_start = 1850L,
        year_end = 2025L,
        target_polity_code = NA_character_,
        common_name = NA_character_,
        match_route = "registry",
        match_status = "registry_unmapped",
        note = "registry area with no polity family (non-country/aggregate)"
      ))
  }
  fam |>
    filter(
      .polity_type_rank(polity_type) == min(.polity_type_rank(fam$polity_type))
    ) |>
    transmute(
      area_code = row$area_code,
      area_name = row$area_name,
      iso3 = row$iso3,
      year_start = pmax(start_year, 1850L),
      # end_year is EXCLUSIVE in the polities database and year_end here is INCLUSIVE, so
      # alias_year_end() is the convention conversion, and it names BOTH readings rather
      # than only the polity-side one (issue 131). Without it this route wrote the polity
      # code's end year verbatim and claimed one year past the polity's coverage: 16 of the 18
      # registry rows sat at `end_year - year_end == 0` while 243 of 249 iso-equal rows sat at
      # 1. Three were material -- ESH-1958-1975, SHN-1834-1967, CXR-1946-1958 -- and the ESH
      # one was ALSO the single baselined (area, year) ambiguity in validate_map_area_year,
      # because area 205's two rows both claimed 1975. See `+ 1L` at the segment splitter
      # below, which already had this right.
      year_end = pmin(alias_year_end(end_year), 2025L),
      target_polity_code = polity_code,
      common_name = polity_name,
      match_route = "registry",
      match_status = "matched",
      note = NA_character_
    ) |>
    filter(year_start <= year_end)
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
    basis = if_else(
      match_route == "registry",
      sprintf(
        "FAOSTAT area code %d; no data in scanned pins; registry map to %s (%d-%d)",
        area_code, target_polity_code, year_start, year_end
      ),
      sprintf(
        "FAOSTAT area code %d; observed %d-%d in pins %s; %s period match%s",
        area_code, year_start, year_end, pins, match_route,
        if_else(is.na(note), "", paste0("; ", note))
      )
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

# Data-bearing areas with no polity family are ACTIONABLE (create a polity);
# no-data registry areas with no family are genuine non-countries and only
# informational.
unmatched <- matches |>
  filter(is.na(target_polity_code), match_status == "unmatched") |>
  select(area_code, area_name, iso3, year_start, year_end, note, n_rows, pins)
registry_unmapped <- matches |>
  filter(match_status == "registry_unmapped") |>
  select(area_code, area_name, iso3, note) |>
  arrange(area_code)

registry_matched <- aliases |> filter(match_route == "registry")
write_csv(select(aliases, -note), file.path(state_dir, "faostat_aliases.csv"))
write_csv(ambiguous, file.path(state_dir, "ambiguous.csv"))
write_csv(unmatched, file.path(state_dir, "unmatched.csv"))
write_csv(registry_unmapped, file.path(state_dir, "registry_unmapped.csv"))
write_csv(aggregates, file.path(state_dir, "aggregates.csv"))

.report_lines <- function(df, fmt_fn) {
  if (nrow(df) == 0L) "(none)" else fmt_fn(df)
}

report <- c(
  "# faostat-era-matching report",
  "",
  sprintf(
    "- Observed reporting areas (1961+): %d (+%d statistical aggregates, intentionally unrouted)",
    sum(inventory$has_data), nrow(aggregates)
  ),
  sprintf(
    "- No-data registry areas (for WHEP crosswalk completeness): %d matched, %d unmapped non-countries",
    n_distinct(registry_matched$area_code), nrow(registry_unmapped)
  ),
  sprintf("- Alias rows emitted: %d (of which %d registry/no-data)",
    nrow(aliases), nrow(registry_matched)),
  sprintf("- Areas with coverage gaps (early years without a polity period): %d", nrow(gaps)),
  sprintf("- Ambiguous areas (overlapping polity periods, not applied): %d", n_distinct(ambiguous$area_code)),
  sprintf("- Data-bearing unmatched areas: %d", nrow(unmatched)),
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
  "## Data-bearing unmatched areas (autoimprove queue)",
  "",
  .report_lines(unmatched, \(df) sprintf(
    "- %s (%d) %d-%d: %s [%d rows]",
    df$area_name, df$area_code, df$year_start, df$year_end, df$note, df$n_rows
  )),
  "",
  "## No-data registry areas with no polity family (informational, not a finding)",
  "",
  .report_lines(registry_unmapped, \(df) sprintf(
    "- %s (%d): %s", df$area_name, df$area_code, df$note
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

  # Guard against silently wiping decisions: every faostat row in the CSV is
  # machine-generated by THIS script, so an existing faostat row the fresh run
  # does not regenerate (dropped key, or same key routed to a different
  # polity) is either (a) a hand-edit about to be lost — encode it as a route
  # in match.R instead — or (b) an intentional match.R change, which must be
  # accepted explicitly. Purely NEW rows never trigger the guard, so steady-
  # state re-runs need no flag.
  accept_diff <- ("--accept-diff" %in% args) ||
    nzchar(Sys.getenv("WHEP_FAOSTAT_ACCEPT_DIFF"))
  existing_fao <- suppressWarnings(read_csv(
    applied_path,
    col_types = cols(.default = "c"),
    progress = FALSE
  )) |>
    filter(source == "faostat")
  if (nrow(existing_fao) > 0 && !accept_diff) {
    new_chr <- canonical |>
      mutate(across(everything(), as.character)) |>
      mutate(key = paste(original_name, year_start, year_end, sep = " | "))
    old_chr <- existing_fao |>
      mutate(key = paste(original_name, year_start, year_end, sep = " | "))
    lost <- anti_join(old_chr, new_chr, by = "key")
    changed <- inner_join(
      old_chr |> select(key, old_target = target_polity_code),
      new_chr |> select(key, new_target = target_polity_code),
      by = "key"
    ) |>
      filter(old_target != new_target)
    if (nrow(lost) > 0 || nrow(changed) > 0) {
      stop(paste(c(
        "REFUSING to rewrite faostat rows in applied_aliases.csv:",
        if (nrow(lost) > 0) c(
          sprintf("  %d existing row(s) would be DROPPED:", nrow(lost)),
          head(sprintf("    %s -> %s", lost$key, lost$target_polity_code), 20)
        ),
        if (nrow(changed) > 0) c(
          sprintf("  %d existing row(s) would change TARGET:", nrow(changed)),
          head(
            sprintf(
              "    %s: %s -> %s",
              changed$key, changed$old_target, changed$new_target
            ),
            20
          )
        ),
        "faostat rows are machine-generated: hand decisions belong in match.R",
        "(manual_prefix / manual_prefix_replace / manual_span_routes), never",
        "in the CSV (the merge is replace-by-source and would wipe them).",
        "If this diff comes from an intentional match.R change, re-run with",
        "--accept-diff (or WHEP_FAOSTAT_ACCEPT_DIFF=1) to accept it."
      ), collapse = "\n"), call. = FALSE)
    }
  }

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
