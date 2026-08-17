## Refuse to write a matcher output that names a polity code data cannot be routed to.
##
## THE #244 PATTERN, for the R matchers (issue 17). Both matchers in this repo read inputs
## that live OUTSIDE it -- `pipelines/faostat-era-matching/match.R` needs a WHEP checkout's
## FAOSTAT pins cache (`WHEP_REPO`), and neither R matcher's dependencies are installed in
## CI -- so nothing in `.github/workflows/validate.yml` can run them, and a gate expressing
## this invariant would skip in the only place gates run automatically. The refusal
## therefore lives at the WRITE, where the bad crosswalk is authored, and runs wherever the
## matcher runs.
##
## Why it is needed even though the matchers resolve against the database they emit codes
## for: the database MOVES under them. A polity re-spanned, renamed or retired between two
## runs leaves the previous run's codes pointing at nothing, and downstream nothing
## complains -- measured 2026-08-17, one row of `data/final/faostat_area_polity_map.csv`
## pointing at a fabricated `ZZZ-1800-1900` passes NINE of the TEN gates that read that file,
## because the only gate that joins on the code (`validate_map_area_year`) SKIPS rows whose
## code is not live. An orphan is invisible to the check that would catch a wrong code. (The
## tenth, `crosscheck_matchers.py`, does catch it, by re-resolving every published FAOSTAT
## area through matchlib. `data/compiled/pre1961/matched.csv`, which this guard protects, is
## gitignored and has NO reader in CI at all.)
##
## Base R only, and deliberately: the matchers' tidyverse dependencies are not installed
## everywhere, and a guard that cannot load is not a guard.

whep_live_polity_codes <- function(polities_csv) {
  if (!file.exists(polities_csv)) {
    return(character(0))
  }
  db <- utils::read.csv(polities_csv, stringsAsFactors = FALSE, colClasses = "character")
  codes <- trimws(db$polity_code)
  status <- if ("wiki_status" %in% names(db)) trimws(db$wiki_status) else rep("", length(codes))
  ## Retired/superseded rows stay in the database for provenance but must never receive
  ## data; scripts/validate_aliases.py already rejects a hand-written alias naming one.
  codes[nzchar(codes) & !(status %in% c("retired", "superseded"))]
}

refuse_orphan_codes <- function(codes, what, fix, polities_csv) {
  live <- whep_live_polity_codes(polities_csv)
  if (length(live) == 0L) {
    message("WARNING: ", what, ": no polity database at ", polities_csv,
            "; orphan-code guard skipped")
    return(invisible(0L))
  }
  codes <- trimws(as.character(codes))
  codes <- codes[!is.na(codes) & nzchar(codes)]
  bad <- codes[!(codes %in% live)]
  if (length(bad) == 0L) {
    return(invisible(0L))
  }
  counts <- sort(table(bad), decreasing = TRUE)
  message("FAIL: ", what, " names ", length(counts),
          " polity code(s) the database cannot route data to, carrying ",
          length(bad), " row(s). Every consumer looks these codes up and finds ",
          "nothing, silently:")
  present <- utils::read.csv(polities_csv, stringsAsFactors = FALSE,
                             colClasses = "character")$polity_code
  for (code in names(counts)) {
    why <- if (code %in% trimws(present)) "retired/superseded" else "absent"
    message("  ", code, "  ", counts[[code]], " row(s)  [", why, "]")
  }
  message("  refusing to write. ", fix)
  quit(status = 1L, save = "no")
}
