# One published row per consumer key, never a blend (whep-polities issues 451 and 367).
#
# WHY. `.prepare_historical_production()` in the WHEP R package reduces every
# (year, area, item, unit) key with `mean(value)`, and this build used to do the same over a
# finer key before handing the table over. A mean over rows that are not the same measurement of
# the same territory is a number from nowhere: fao1952 prints Yugoslavia's 1949 dry beans as two
# rows, 38,000 ha and 783,000 ha, whose SUM is the 821,000 ha juan reports, and the old build
# published their mean against juan's total -- 547,333 ha after the consumer's second mean. Where a
# total sits beside its own parts (Italy grapes 1950: 6,544 = 4,014 + 2,530 thousand t) a mean
# returns a third of the truth and a sum returns double. So the build now resolves every key to
# ONE candidate row it can name, and records how.
#
# THE RULES, applied per key, in order. A key is (year, polity_code, area_code, item_prod_code,
# item_cbs_code, live_anim_code, unit) -- the consumer's key plus the polity, which the consumer
# keeps apart through `area` (one area_code carries two polities in 1949).
#
#   1. Within ONE source, reduce its rows to one value:
#        single               one row.
#        identical            all rows carry the same number (one series under two spellings,
#                             e.g. iia `ethiopia` / `ethiopia pdr`): keep one.
#        total_beside_parts   three or more rows whose largest equals the sum of the rest to within
#                             TBP_TOLERANCE (issue 367's fingerprint): keep the total.
#        ambiguous            anything else -- siblings with no total, or two series sharing an item
#                             code. Nothing in the panel says whether to add them or pick one, so
#                             this source contributes NOTHING to the key rather than a guess.
#   2. Across the sources that survive step 1:
#        identical               every candidate row carries the same number.
#        one_source              one source survives.
#        source_precedence       several survive and agree to within CONTRADICTION_RATIO: publish
#                                the first in PRECEDENCE. Cross-source agreement has a median of
#                                1.0011 (state/cross_source_agreement.csv), so which one is
#                                published moves the value by revision noise, not by territory.
#        withheld_contradiction  several survive and the largest exceeds CONTRADICTION_RATIO times
#                                the smallest. They cannot both be this key's measurement, and the
#                                panel does not say which is: iia's `wheat` on F51-1918-1938 in
#                                1930 reads 311.9 t against juan's 1,377,280 t. Precedence would
#                                publish the 311.9; the mean published 688,796, right for neither.
#        withheld_ambiguous      no source survives step 1.
#   A withheld key is NOT published. Every one must be listed in state/withheld_keys_baseline.csv
#   with a reason, or scripts/validate_published_collapse.py fails: a NEW withheld key is a new
#   defect to document (data_errors.csv) or resolve upstream, never a silent loss.
#
# PRECEDENCE is WHEP's own `.prod_source_rank()`: every `historical_*` source ranks 3 and ties
# break alphabetically, so the consumer already LABELS each averaged key with the first of these.
# Publishing that source's value makes the label true instead of introducing a new ranking here.
# It is a convention, not a judgement of source quality; reorder it in one place if a historian
# ranks the sources, and `scripts/validate_published_collapse.py` re-derives every key from it.
PRECEDENCE <- c("fao1952", "iia", "juan", "mitchell", "sa_colonial")
TBP_TOLERANCE <- 0.02
CONTRADICTION_RATIO <- 2
IDENTICAL_TOLERANCE <- 1e-9

COLLAPSE_KEY <- c(
  "year",
  "polity_code",
  "area_code",
  "item_prod_code",
  "item_cbs_code",
  "live_anim_code",
  "unit"
)

.same_values <- function(v) {
  (max(v) - min(v)) <= IDENTICAL_TOLERANCE * max(1, abs(max(v)))
}

# The rule one source's rows fall under, and which of its rows carries the value.
.reduce_one_source <- function(v) {
  if (length(v) == 1L) {
    return(list(rule = "single", pick = 1L))
  }
  if (.same_values(v)) {
    return(list(rule = "identical", pick = 1L))
  }
  top <- which.max(v)
  if (length(v) >= 3L &&
    abs(v[[top]] - (sum(v) - v[[top]])) <= TBP_TOLERANCE * abs(v[[top]])) {
    return(list(rule = "total_beside_parts", pick = top))
  }
  list(rule = "ambiguous", pick = NA_integer_)
}

# Survivors that cannot be one measurement: a ratio beyond CONTRADICTION_RATIO, or a zero beside
# a non-zero (a ratio of infinity). Two zeros are identical and never reach here.
.contradicts <- function(v) {
  lo <- min(v)
  hi <- max(v)
  if (lo <= 0) {
    return(hi > 0)
  }
  hi / lo > CONTRADICTION_RATIO
}

.source_rank <- function(source) {
  r <- match(source, PRECEDENCE)
  ifelse(is.na(r), length(PRECEDENCE) + 1L, r)
}

# Render a number so the tracked table diffs cleanly and Python re-reads it exactly.
.fmt_value <- function(x) {
  sprintf("%.15g", x)
}

# `rows` carries COLLAPSE_KEY, `raw_source`, `value` and whatever provenance columns the build
# keeps. Returns list(published = one row per key, resolutions = the tracked audit table).
resolve_collapse_groups <- function(rows) {
  rows <- rows |>
    dplyr::mutate(
      .row = dplyr::row_number(),
      .rank = .source_rank(.data$raw_source)
    ) |>
    dplyr::arrange(.data$.rank, .data$raw_source, .data$.row)

  rows <- rows |>
    dplyr::mutate(.key = dplyr::cur_group_id(), .by = dplyr::all_of(COLLAPSE_KEY))
  n_by_key <- tabulate(rows$.key)
  single <- rows[n_by_key[rows$.key] == 1L, , drop = FALSE]
  multi <- rows[n_by_key[rows$.key] > 1L, , drop = FALSE]

  picked <- integer(0)
  audit <- vector("list", 0L)
  for (part in split(seq_len(nrow(multi)), multi$.key)) {
    g <- multi[part, , drop = FALSE]
    by_src <- split(seq_len(nrow(g)), factor(g$raw_source, levels = unique(g$raw_source)))
    rules <- character(0)
    survivors <- integer(0)
    for (s in names(by_src)) {
      idx <- by_src[[s]]
      red <- .reduce_one_source(g$value[idx])
      rules[[s]] <- red$rule
      if (!is.na(red$pick)) {
        survivors[[s]] <- part[idx[[red$pick]]]
      }
    }
    all_same <- .same_values(g$value)
    sv <- multi$value[survivors]
    resolution <- if (length(survivors) == 0L) {
      "withheld_ambiguous"
    } else if (all_same) {
      "identical"
    } else if (length(survivors) == 1L) {
      "one_source"
    } else if (.contradicts(sv)) {
      "withheld_contradiction"
    } else {
      "source_precedence"
    }
    # `by_src` is in PRECEDENCE order already, so the first survivor is the winner.
    chosen <- if (length(survivors) && !startsWith(resolution, "withheld")) {
      survivors[[1L]]
    } else {
      NA_integer_
    }
    if (!is.na(chosen)) {
      picked <- c(picked, chosen)
    }
    one_source_dups <- any(lengths(by_src) > 1L)
    if (all_same && !one_source_dups) {
      # Two publishers agreeing to the digit: corroboration, not a collapse. Published as one row
      # and not listed, or the table would be 2,500 rows of agreement burying the decisions.
      next
    }
    audit[[length(audit) + 1L]] <- tibble::tibble(
      year = g$year[[1L]],
      polity_code = g$polity_code[[1L]],
      item_prod_code = .fmt_value(g$item_prod_code[[1L]]),
      item_prod_name = g$item_prod[[1L]],
      unit = g$unit[[1L]],
      n_candidates = nrow(g),
      candidates = paste(
        vapply(
          names(by_src),
          \(s) paste0(s, "=", paste(.fmt_value(sort(g$value[by_src[[s]]])), collapse = ";")),
          character(1)
        ),
        collapse = "|"
      ),
      labels = paste(sort(unique(g$raw_country)), collapse = " | "),
      raw_items = paste(sort(unique(g$raw_item)), collapse = " | "),
      source_rules = paste0(names(rules), "=", rules, collapse = "|"),
      resolution = resolution,
      published_source = if (is.na(chosen)) "" else multi$raw_source[[chosen]],
      published_value = if (is.na(chosen)) "" else .fmt_value(multi$value[[chosen]])
    )
  }

  published <- dplyr::bind_rows(single, multi[picked, , drop = FALSE]) |>
    dplyr::arrange(.data$.row) |>
    dplyr::select(-dplyr::all_of(c(".row", ".rank", ".key")))
  resolutions <- dplyr::bind_rows(audit)
  if (nrow(resolutions)) {
    resolutions <- resolutions |>
      dplyr::arrange(.data$polity_code, .data$item_prod_code, .data$unit, .data$year)
  }
  list(published = published, resolutions = resolutions)
}
