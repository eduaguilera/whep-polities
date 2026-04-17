# ==============================================================================
# pipelines/pre1961-matching/match.R
#
# Self-contained, reproducible pipeline that crosslinks the pre-1961
# agricultural/livestock dataset (`data/external/before_1961.csv`) with the
# WHEP polity database (`data/final/polities_database.csv`) and emits the
# inputs the web UI's "Data" tab consumes.
#
# Everything this pipeline needs is declared in-file. Run from the project root:
#
#   Rscript pipelines/pre1961-matching/match.R
#
# ------------------------------------------------------------------------------
# Inputs
#   data/external/before_1961.csv       pre-1961 raw data (~124k rows)
#   data/final/polities_database.csv    WHEP polity registry (~1.3k rows)
#
# Outputs
#   data/compiled/pre1961/
#     matched.csv                       Input rows annotated with
#                                       `whep_polity_code` and `match_status`.
#     summary_by_polity.json            Per-polity rollup (rows, years, items,
#                                       sources). Consumed by the site UI.
#     by_item/<slug>.json               Per-item pivot:
#                                         {item, unit, by_year: {year:
#                                           {polity_code: value, ...}, ...}}
#                                       One file per crop/commodity.
#     by_item_index.json                {items: [{slug, item, unit,
#                                         year_min, year_max, polities: N}, ...]}
#     report.md                         Human-readable match report.
#
# The site build (`site/build_wiki.sh`) copies these into
# `site/data/pre1961/` so the UI can fetch per-item files on demand.
# ==============================================================================

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tidyr)
  library(jsonlite)
})

# ---- paths -------------------------------------------------------------------
proj_root   <- normalizePath(".")
input_path  <- file.path(proj_root, "data", "external", "before_1961.csv")
whep_path   <- file.path(proj_root, "data", "final", "polities_database.csv")
out_dir     <- file.path(proj_root, "data", "compiled", "pre1961")
by_item_dir <- file.path(out_dir, "by_item")

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(by_item_dir, recursive = TRUE, showWarnings = FALSE)

stopifnot(file.exists(input_path))
stopifnot(file.exists(whep_path))

# ---- load --------------------------------------------------------------------
cat("[load] WHEP polities...\n")
whep <- read_csv(whep_path, show_col_types = FALSE) |>
  filter(!is.na(start_year), !is.na(end_year)) |>
  mutate(start_year = as.integer(start_year),
         end_year   = as.integer(end_year))

cat(sprintf("[load] pre-1961 input (%.1f MB)...\n",
            file.size(input_path) / 1024^2))
pre <- read_csv(input_path, show_col_types = FALSE) |>
  mutate(year = as.integer(year))

# ---- iso3c normalisation -----------------------------------------------------
# WHEP uses some non-ISO-3166 codes for composite / historical entities.
# Pre-independence years of modern ISO3 codes are also routed to the
# appropriate imperial/colonial WHEP chain. Edit this table when new
# mismatches surface.
normalise_iso <- function(iso, year, polity_name = NA_character_) {
  if (is.na(iso) || iso == "NA") return(NA_character_)
  y <- if (!is.na(year)) year else NA_integer_

  # --- Europe: pre-independence / composite entities -------------------------
  # PRINCIPLE: if the data reports a country separately, it gets its own polity.
  # We only rewrite ISOs when the input name is retroactive (e.g. "Yugoslav SFR"
  # for pre-1918) or the input uses a modern ISO for a genuinely different entity.

  # Serbia pre-1920 → Kingdom of Serbia (SER)
  if (iso == "SRB" && !is.na(y) && y < 1920) return("SER")

  # Finland, Ireland, Austria, Hungary, Baltics, Poland: data reports these
  # separately from their empires → they have their own WHEP polity entries
  # (FIN-1809-1917, IRL-1800-1921, AUT-1800-1918, HUN-1800-1918,
  # EST/LVA/LTU/POL-1800-1918, EST/LVA/LTU-1940-1991). No routing needed —
  # iso codes match directly.

  # Turkey pre-1913: data reports "Turkey" covering Anatolian territory
  # (~780k km2), NOT the full Ottoman Empire (~2.66M km2). Mitchell and
  # FAOSTAT use "Turkey" for the present-day borders retroactively (Pamuk
  # confirms). TUR-1800-1913 captures this; OTT captures the full empire.
  # No routing needed — TUR iso matches TUR-1800-1913 directly.
  # Israel/Palestine pre-1948 → British Mandate Palestine (PAL)
  if (iso %in% c("ISR", "PSE") && !is.na(y) && y < 1948) return("PAL")

  # Yugoslavia: pre-1918 → Serbia (continuity state); 1918+ → F248
  # ("Yugoslav SFR" is a retroactive name — the territory was Serbia)
  if (iso == "YUG") {
    if (!is.na(y) && y < 1918) return("SER") else return("F248")
  }
  # Czechoslovakia: pre-1918 → AUH (retroactive name for AH territory);
  #                 1918+ → F51 (Czechoslovakia). NOT F77 (East Germany).
  if (iso == "CSK") {
    if (!is.na(y) && y < 1918) return("AUH") else return("F51")
  }

  # Czech Republic pre-1993 → Czechoslovakia (F51)
  if (iso == "CZE" && !is.na(y) && y < 1993) return("F51")

  # Germany 1949-1990 stays as DEU (→ DEU-1949-1990, the combined
  # FRG+GDR statistical aggregate for datasets that report a single
  # 'Germany' stream). Separate FRG/GDR data (not present in the pre-1961
  # input) would use iso3c=FRG / DDR and normalise_iso passes those
  # through unchanged; downstream they match F78 / F77 as before.
  # 1945-1948 Allied occupation resolves directly to DEU → DEU-1945-1949.

  # Russia/USSR pre-1991 → Russian Empire/USSR chain (F228)
  if (iso == "RUS" && !is.na(y) && y < 1991) return("F228")

  # --- Africa: colonial-era routings -----------------------------------------

  # Tanzania pre-1964 → Tanganyika (TAN)
  if (iso == "TZA" && !is.na(y) && y < 1964) return("TAN")
  # Botswana pre-1966 → Bechuanaland Protectorate (BEC)
  if (iso == "BWA" && !is.na(y) && y < 1966) return("BEC")
  # Mauritania pre-1960 → colonial Mauritania (MAU)
  if (iso == "MRT" && !is.na(y) && y < 1960) return("MAU")
  # Somalia pre-1960 → Italian Somaliland (ITS)
  if (iso == "SOM" && !is.na(y) && y < 1960) return("ITS")
  # Sudan: WHEP uses SUD (not SDN) for pre-2011 unified Sudan
  if (iso == "SDN" && !is.na(y) && y < 2011) return("SUD")
  # Malawi/Zimbabwe/Zambia 1953-1964 → Federation of Rhodesia & Nyasaland (FRN)
  if (iso == "MWI" && !is.na(y) && y >= 1953 && y < 1964) return("FRN")
  if (iso == "ZWE" && !is.na(y) && y >= 1953 && y < 1964) return("FRN")
  if (iso == "ZMB" && !is.na(y) && y >= 1953 && y < 1964) return("FRN")
  # Libya pre-1912 → Ottoman Empire (OTT)
  if (iso == "LBY" && !is.na(y) && y < 1912) return("OTT")
  # Rwanda pre-1962 → Ruanda-Urundi (RWB)
  if (iso == "RWA" && !is.na(y) && y < 1962) return("RWB")

  # --- Asia: colonial/pre-independence routings ------------------------------

  # Malaysia: pre-1922 → Federated Malay States (FED); 1922-1946 → British Malaya (BMA)
  if (iso == "MYS" && !is.na(y) && y < 1922) return("FED")
  if (iso == "MYS" && !is.na(y) && y >= 1922 && y < 1946) return("BMA")
  # (PAK pre-1947 routing removed — PAK-1800-1947 now exists as own polity)
  # Pakistan pre-1947 and Bangladesh pre-1971: data reports these
  # separately from India/Pakistan → they have their own WHEP entries
  # (PAK-1800-1947, BGD-1947-1971). Same principle as Finland/Ireland.
  # No routing needed — iso codes match directly.
  # Vietnam 1954-1975 → South Vietnam (SVI)
  if (iso == "VNM" && !is.na(y) && y >= 1954 && y <= 1975) return("SVI")
  # North Korea pre-1948 → Korea (occupied) — pre-division
  if (iso == "PRK" && !is.na(y) && y < 1948) return("KOR")
  # Zambia pre-1911 → Northwestern Rhodesia (NWR)
  if (iso == "ZMB" && !is.na(y) && y < 1911) return("NWR")

  iso
}

# iso3c is NA in the input — fall back to polity_name or country.
name_override <- c(
  "Korea"                        = "KOR",
  "Republic of Korea"            = "KOR",
  "Natal"                        = "NAT",
  "Cape Natal"                   = "NAT",
  "Rwanda and Burundi"           = "RWB",
  "Israel/Palestine"             = "PAL",
  "Indochina"                    = "FID",
  "China, Manchuria Province of" = "MAN",
  "Cape Province"                = "CAP",
  "Cape of Good Hope"            = "CAP"
)

resolve_iso <- function(iso3c, polity_name, year, country = NA_character_) {
  iso <- normalise_iso(iso3c, year, polity_name)
  if (is.na(iso) || iso == "NA") {
    # Try polity_name first, then country column
    if (!is.na(polity_name) && polity_name %in% names(name_override)) {
      iso <- unname(name_override[polity_name])
    } else if (!is.na(country) && country %in% names(name_override)) {
      iso <- unname(name_override[country])
    }
  }
  # Post-resolution time-dependent adjustments for name_override results
  if (!is.na(iso) && iso != "NA") {
    # Natal → South Africa after Union (1910)
    if (iso == "NAT" && !is.na(year) && year > 1910) iso <- "ZAF"
    # Cape Colony → South Africa after Union (1910)
    if (iso == "CAP" && !is.na(year) && year > 1910) iso <- "ZAF"
    # Manchuria: only Manchukuo (MAN) 1932-1945; otherwise China (CHN)
    if (iso == "MAN" && !is.na(year) && (year < 1932 || year > 1945)) iso <- "CHN"
    # Palestine → Israel after May 1948
    if (iso == "PAL" && !is.na(year) && year >= 1948) iso <- "ISR"
  }
  iso
}

# ---- matching ----------------------------------------------------------------
cat(sprintf("[match] %d rows against %d WHEP polities...\n",
            nrow(pre), nrow(whep)))

# Lookup key: prefer iso3_code; fall back to the three-letter prefix of
# polity_code (e.g. "F51" for F51-1918-1938, "OTT" for OTT-1800-1886, "TAN"
# for TAN-1891-1920). normalise_iso() above returns these WHEP-internal
# codes for dissolved/renamed entities (CSK → F51, RUS pre-1991 → F228,
# TZA pre-1964 → TAN, etc.); we need those codes to resolve into the
# `whep_by_iso` index too, not just real ISO3 codes.
whep$lookup_key <- ifelse(is.na(whep$iso3_code) | whep$iso3_code == "",
                          sub("-.*", "", whep$polity_code),
                          whep$iso3_code)
whep_by_iso <- split(whep, whep$lookup_key)

# Known historical/modern name pairs — kept here so `match_one` can use them
# too (to avoid rejecting correct but renamed matches like Japan ↔ Japanese
# Empire or Ivory Coast ↔ Côte d'Ivoire).
name_equiv <- list(
  # Direct iso matches — historical/modern name pairs
  JPN = c("japanese empire"),
  TUR = c("t\u00fcrkiye", "ottoman"),
  DEU = c("german", "prussia", "north german confederation"),
  SWE = c("sweden-norway"),
  SYR = c("syria", "syria and lebanon"),
  CIV = c("c\u00f4te d'ivoire", "cote d'ivoire"),
  VNM = c("vietnam", "annam", "tonkin"),
  MMR = c("upper burma", "lower burma", "burma", "konbaung"),
  LAO = c("laos"),
  NGA = c("nigeria", "northern nigeria", "southern nigeria"),
  IRN = c("persia", "iran"),
  THA = c("siam"),
  IDN = c("dutch east indies", "indonesia"),
  ETH = c("abyssinia", "ethiopia"),
  ZAF = c("south africa", "natal", "cape"),
  EGY = c("egypt"),
  RUS = c("russian empire", "soviet"),
  KOR = c("korea"),
  COD = c("congo"),
  CMR = c("cameroon", "cameroun", "kamerun"),
  TGO = c("togo", "togoland"),
  # Rewrite-target codes — aliases that confirm the WHEP polity is valid
  GBR  = c("united kingdom", "great britain", "britain"),
  AUH  = c("austria", "hungary", "austrian", "austro"),
  F228 = c("russia", "russian", "soviet", "ussr", "rsfsr",
           "finland", "poland", "estonia", "latvia", "lithuania"),
  F248 = c("yugoslavia", "yugoslav", "serb", "croat", "slovene"),
  F51  = c("czech", "czechoslovakia", "slovaki"),
  F78  = c("germany", "west germany", "federal republic"),
  OTT  = c("ottoman", "turkey", "libya", "levant"),
  PAL  = c("palestine", "israel", "jordan"),
  TAN  = c("tanzania", "tanganyika"),
  BEC  = c("botswana", "bechuanaland", "tswana"),
  MAU  = c("mauritania"),
  BMA  = c("malaysia", "malaya", "malay"),
  ITS  = c("somali", "somalia"),
  FRN  = c("malawi", "nyasaland", "rhodesia", "zimbabwe", "zambia"),
  SUD  = c("sudan"),
  IND  = c("india", "pakistan", "bengal"),
  PAK  = c("pakistan", "bangladesh", "east pakistan"),
  RWB  = c("ruanda", "urundi", "rwanda", "burundi"),
  MAN  = c("manchuria", "manchukuo", "china"),
  FID  = c("indochina", "french indochina", "cochinchina"),
  CAP  = c("cape colony", "cape province", "cape of good hope"),
  SVI  = c("vietnam", "viet nam", "south vietnam"),
  FED  = c("malaysia", "malaya", "malay", "federated"),
  NWR  = c("zambia", "northern rhodesia", "northwestern rhodesia"),
  FCC  = c("indochina", "cochinchina"),
  LSO  = c("lesotho", "basutoland", "basotho"),
  SER  = c("serbia", "yugoslav", "serb"),
  # Direct-iso entries for pre-independence polities (guard: "Finland" ↔ "Grand Duchy of Finland")
  FIN  = c("finland", "grand duchy"),
  AUT  = c("austria", "cisleithania"),
  HUN  = c("hungary", "transleithania", "kingdom"),
  IRL  = c("ireland", "united kingdom"),
  EST  = c("estonia", "estonian", "governorate"),
  LVA  = c("latvia", "livonia", "courland", "latvian"),
  LTU  = c("lithuania", "lithuanian", "governorate"),
  POL  = c("poland", "congress", "kongresowka"),
  TUR  = c("turkey", "anatolia", "ottoman"),
  BGD  = c("bangladesh", "east pakistan", "east bengal")
)

known_equivalent <- function(iso, whep_name) {
  if (is.na(iso) || is.na(whep_name)) return(FALSE)
  aliases <- name_equiv[[iso]]
  if (is.null(aliases)) return(FALSE)
  any(vapply(aliases, function(a) grepl(a, tolower(whep_name), fixed = TRUE), logical(1)))
}

match_one <- function(iso_lookup, year, input_country = NA_character_) {
  if (is.na(iso_lookup) || is.na(year)) return(list(code = NA, status = "none"))
  pool <- whep_by_iso[[iso_lookup]]
  if (is.null(pool) || nrow(pool) == 0) return(list(code = NA, status = "none"))
  hits <- pool[pool$start_year <= year & pool$end_year >= year, ]
  if (nrow(hits) == 0) return(list(code = NA, status = "none"))
  nat <- hits[hits$polity_type == "national", ]
  if (nrow(nat) == 1) {
    # Single national candidate: reject if its name has no token overlap
    # with the input country and it's not a known historical equivalent.
    # Avoids matching NGA 1889-1897 to NUP-1800-1897 (Nupe Kingdom) just
    # because Nupe happens to carry iso3_code=NGA.
    if (!is.na(input_country) && nchar(input_country) > 0) {
      tokens_in <- tolower(strsplit(gsub("[^A-Za-z ]", " ", input_country), "\\s+")[[1]])
      tokens_in <- tokens_in[nchar(tokens_in) >= 4]
      wn <- tolower(nat$polity_name[[1]])
      overlap <- any(vapply(tokens_in, function(t) grepl(t, wn, fixed = TRUE), logical(1)))
      if (!overlap && !known_equivalent(iso_lookup, nat$polity_name[[1]])) {
        return(list(code = NA, status = "none"))
      }
    }
    return(list(code = nat$polity_code[[1]], status = "unique"))
  }
  # When several national candidates match, prefer one whose polity_name
  # token-overlaps the input country name (avoids, e.g., NGA rows hitting
  # the Nupe Kingdom row just because Nupe's iso3_code is also NGA).
  if (nrow(nat) > 1) {
    if (!is.na(input_country) && nchar(input_country) > 0) {
      tokens_in <- tolower(strsplit(gsub("[^A-Za-z ]", " ", input_country), "\\s+")[[1]])
      tokens_in <- tokens_in[nchar(tokens_in) >= 4]
      name_matches <- vapply(seq_len(nrow(nat)), function(k) {
        wn <- tolower(nat$polity_name[[k]])
        any(vapply(tokens_in, function(t) grepl(t, wn, fixed = TRUE), logical(1)))
      }, logical(1))
      if (any(name_matches)) {
        sub <- nat[name_matches, ]
        top <- sub[which.max(sub$end_year - sub$start_year), ]
        return(list(code = top$polity_code[[1]], status = "name-preferred"))
      }
    }
    top <- nat[which.max(nat$end_year - nat$start_year), ]
    return(list(code = top$polity_code[[1]], status = "national"))
  }
  if (nrow(hits) == 1) return(list(code = hits$polity_code[[1]], status = "unique"))
  top <- hits[which.max(hits$end_year - hits$start_year), ]
  list(code = top$polity_code[[1]], status = "subnational")
}

pre <- pre |>
  mutate(iso_lookup = mapply(resolve_iso, iso3c, polity_name, year, country,
                             USE.NAMES = FALSE))

results <- vector("list", nrow(pre))
for (i in seq_len(nrow(pre))) {
  results[[i]] <- match_one(pre$iso_lookup[i], pre$year[i], pre$country[i])
}
pre$whep_polity_code <- vapply(results, function(r) {
  if (is.null(r$code) || (length(r$code) == 1 && is.na(r$code))) NA_character_
  else as.character(r$code)
}, character(1))
pre$match_status <- vapply(results, function(r) r$status, character(1))

# ---- false-positive audit ---------------------------------------------------
# A match is "trusted" when the input country is the same entity as the WHEP
# polity. We approximate "same entity" with token overlap between the input
# labels and the WHEP polity_name. A match that passes any of these is
# trusted:
#   - Input iso3c matches WHEP iso3_code exactly (no rewrite was applied).
#   - The first word of WHEP polity_name is a substring of the input country
#     or polity_name (case-insensitive), or vice versa.
#   - Explicit trust list for known-safe rewrites (IRL-pre-1921 -> GBR,
#     FIN-pre-1917 -> F228, etc.).
# Anything else is flagged as `suspect` in `match_confidence`. Reviewers
# should check those rows and extend the trust rules as needed.

whep_name_by_code <- setNames(whep$polity_name, whep$polity_code)
whep_iso_by_code  <- setNames(whep$iso3_code, whep$polity_code)

token_match <- function(input_str, whep_name) {
  if (is.na(input_str) || is.na(whep_name) || nchar(input_str) == 0) return(FALSE)
  a <- tolower(input_str); b <- tolower(whep_name)
  # Strip punctuation, take the first 1-3 words of each.
  toks_a <- head(strsplit(gsub("[^a-z ]", "", a), "\\s+")[[1]], 3)
  toks_b <- head(strsplit(gsub("[^a-z ]", "", b), "\\s+")[[1]], 3)
  toks_a <- toks_a[nchar(toks_a) >= 3]
  toks_b <- toks_b[nchar(toks_b) >= 3]
  if (length(toks_a) == 0 || length(toks_b) == 0) return(FALSE)
  length(intersect(toks_a, toks_b)) > 0
}

# Intentionally-trusted cross-name rewrites (input label != WHEP name but we
# know the mapping is correct).
trusted_rewrite <- function(input_iso, input_name, year, whep_code, whep_iso) {
  if (is.na(whep_code)) return(FALSE)
  y <- if (!is.na(year)) year else NA_integer_

  # --- ISO-based rewrites (input_iso not NA) ---
  if (!is.na(input_iso)) {

  # --- Europe ---
  # (IRL→GBR, FIN→F228, AUT/HUN→AUH, Baltics→F228 REMOVED: these countries
  # now have their own pre-independence WHEP entries and match directly via iso.)
  # (TUR→OTT removed — TUR-1800-1913 now exists as own polity)
  if (input_iso %in% c("ISR", "PSE") && !is.na(y) && y < 1948 && grepl("^PAL", whep_code)) return(TRUE)
  if (input_iso == "SRB" && !is.na(y) && y < 1920 && grepl("^SER", whep_code)) return(TRUE)
  if (input_iso == "YUG" && grepl("^F248", whep_code)) return(TRUE)
  if (input_iso == "CSK" && grepl("^F51", whep_code)) return(TRUE)
  if (input_iso == "CSK" && !is.na(y) && y < 1918 && grepl("^AUH", whep_code)) return(TRUE)
  if (input_iso == "CZE" && !is.na(y) && y < 1993 && grepl("^F51", whep_code)) return(TRUE)
  if (input_iso == "DEU" && !is.na(y) && y >= 1949 && y < 1990 && grepl("^F78", whep_code)) return(TRUE)
  if (input_iso == "RUS" && !is.na(y) && y < 1991 && grepl("^F228", whep_code)) return(TRUE)

  # --- Africa ---
  if (input_iso == "TZA" && !is.na(y) && y < 1964 && grepl("^TAN", whep_code)) return(TRUE)
  if (input_iso == "BWA" && !is.na(y) && y < 1966 && grepl("^BEC", whep_code)) return(TRUE)
  if (input_iso == "MRT" && !is.na(y) && y < 1960 && grepl("^MAU", whep_code)) return(TRUE)
  if (input_iso == "SOM" && !is.na(y) && y < 1960 && grepl("^ITS", whep_code)) return(TRUE)
  if (input_iso == "SDN" && !is.na(y) && y < 2011 && grepl("^SUD", whep_code)) return(TRUE)
  if (input_iso %in% c("MWI", "ZWE", "ZMB") && !is.na(y) && y >= 1953 && y < 1964 && grepl("^FRN", whep_code)) return(TRUE)
  if (input_iso == "LBY" && !is.na(y) && y < 1912 && grepl("^OTT", whep_code)) return(TRUE)
  if (input_iso == "RWA" && !is.na(y) && y < 1962 && grepl("^RWB", whep_code)) return(TRUE)
  if (input_iso == "CSK" && !is.na(y) && y < 1918 && grepl("^AUH", whep_code)) return(TRUE)

  # --- Asia ---
  if (input_iso == "MYS" && !is.na(y) && y < 1946 && grepl("^BMA", whep_code)) return(TRUE)
  # (PAK→IND and BGD→PAK removed — these now have own polities)
  if (input_iso == "VNM" && !is.na(y) && y >= 1954 && y <= 1975 && grepl("^SVI", whep_code)) return(TRUE)
  if (input_iso == "PRK" && !is.na(y) && y < 1948 && grepl("^KOR", whep_code)) return(TRUE)
  if (input_iso == "ZMB" && !is.na(y) && y < 1911 && grepl("^NWR", whep_code)) return(TRUE)
  if (input_iso == "YUG" && !is.na(y) && y < 1918 && grepl("^SER", whep_code)) return(TRUE)
  if (input_iso == "MYS" && !is.na(y) && y < 1922 && grepl("^FED", whep_code)) return(TRUE)

  } # end !is.na(input_iso)

  # --- Name-override resolved codes (input iso is NA) ---
  # Natal/Cape → ZAF post-1910
  if (is.na(input_iso) && grepl("^ZAF", whep_code) &&
      !is.na(input_name) && grepl("natal|cape", tolower(input_name))) return(TRUE)
  # Manchuria → MAN or CHN
  if (is.na(input_iso) && !is.na(input_name) && grepl("manchuria", tolower(input_name)) &&
      (grepl("^MAN", whep_code) || grepl("^CHN", whep_code))) return(TRUE)
  # Indochina → FID or FCC (pre-1887 Cochinchina)
  if (is.na(input_iso) && !is.na(input_name) && grepl("indochina", tolower(input_name)) &&
      (grepl("^FID", whep_code) || grepl("^FCC", whep_code))) return(TRUE)
  # Korea → KOR
  if (is.na(input_iso) && !is.na(input_name) && grepl("korea", tolower(input_name)) &&
      (grepl("^KOR", whep_code) || grepl("^OKO", whep_code))) return(TRUE)
  # Rwanda and Burundi → RWB
  if (is.na(input_iso) && !is.na(input_name) && grepl("rwanda|burundi", tolower(input_name)) &&
      grepl("^RWB", whep_code)) return(TRUE)
  # Israel/Palestine → PAL or ISR (post-1948 rerouted to ISR)
  if (is.na(input_iso) && !is.na(input_name) && grepl("israel|palestine", tolower(input_name)) &&
      (grepl("^PAL", whep_code) || grepl("^ISR", whep_code))) return(TRUE)

  FALSE
}

cat("[audit] scoring match confidence...\n")
whep_name_of <- whep_name_by_code[pre$whep_polity_code]
whep_iso_of  <- whep_iso_by_code[pre$whep_polity_code]

confidence <- rep("suspect", nrow(pre))
confidence[is.na(pre$whep_polity_code)] <- "none"
# Trust by iso equality + name overlap
iso_equal <- !is.na(pre$whep_polity_code) &
             !is.na(whep_iso_of) & whep_iso_of != "NA" &
             pre$iso3c == whep_iso_of
for (i in which(iso_equal)) {
  if (token_match(pre$country[i], whep_name_of[i]) ||
      token_match(pre$polity_name[i], whep_name_of[i])) {
    confidence[i] <- "iso-equal"
  } else if (known_equivalent(pre$iso3c[i], whep_name_of[i])) {
    confidence[i] <- "known-equivalent"
  } else {
    confidence[i] <- "iso-equal-name-mismatch"
  }
}
# Non-iso-equal rows: rewrites + name fallbacks.
for (i in which(confidence == "suspect" & !is.na(pre$whep_polity_code))) {
  tr_name <- if (!is.na(pre$polity_name[i])) pre$polity_name[i] else pre$country[i]
  if (trusted_rewrite(pre$iso3c[i], tr_name,
                       pre$year[i], pre$whep_polity_code[i],
                       whep_iso_of[i])) {
    confidence[i] <- "trusted-rewrite"
  } else if (token_match(pre$country[i], whep_name_of[i]) ||
             token_match(pre$polity_name[i], whep_name_of[i])) {
    confidence[i] <- "name-overlap"
  }
}
pre$match_confidence <- confidence

# Stats
conf_tbl <- pre |> count(match_confidence, sort = TRUE)
cat("[audit] confidence breakdown:\n")
print(conf_tbl)

# Build the top suspect buckets — grouped by (input iso3c, polity_name,
# assigned polity_code, WHEP polity name) so reviewers can triage.
suspects <- pre |>
  filter(match_confidence %in% c("suspect", "iso-equal-name-mismatch")) |>
  mutate(whep_name = whep_name_of[match(whep_polity_code, names(whep_name_of))]) |>
  group_by(iso3c, country, polity_name, whep_polity_code, whep_name, match_confidence) |>
  summarise(rows = n(),
            year_min = min(year, na.rm = TRUE),
            year_max = max(year, na.rm = TRUE),
            .groups = "drop") |>
  arrange(desc(rows))

n_total <- nrow(pre)
n_match <- sum(pre$match_status %in% c("unique", "national", "subnational"))
cat(sprintf("[match] %d/%d matched (%.1f%%)\n",
            n_match, n_total, 100 * n_match / n_total))
print(pre |> count(match_status, sort = TRUE))

# ---- output: matched CSV -----------------------------------------------------
matched_path <- file.path(out_dir, "matched.csv")
write_csv(pre |> select(-iso_lookup), matched_path)
cat("[out] ", matched_path, "\n")

# ---- output: suspects summary (per-bucket, for quick review) ---------------
suspects_path <- file.path(out_dir, "suspects.json")
suspects_obj <- lapply(seq_len(nrow(suspects)), function(i) list(
  iso3c     = suspects$iso3c[[i]],
  country   = suspects$country[[i]],
  polity_name_input = suspects$polity_name[[i]],
  whep_polity_code  = suspects$whep_polity_code[[i]],
  whep_polity_name  = suspects$whep_name[[i]],
  confidence = suspects$match_confidence[[i]],
  rows      = suspects$rows[[i]],
  year_min  = suspects$year_min[[i]],
  year_max  = suspects$year_max[[i]]
))
write(toJSON(suspects_obj, auto_unbox = TRUE, pretty = FALSE), suspects_path)
cat("[out] ", suspects_path, "\n")

# ---- output: per-polity summary JSON -----------------------------------------
by_polity <- pre |>
  filter(!is.na(whep_polity_code)) |>
  group_by(whep_polity_code) |>
  summarise(
    rows     = n(),
    year_min = min(year, na.rm = TRUE),
    year_max = max(year, na.rm = TRUE),
    items    = list(sort(unique(item))),
    sources  = list(sort(unique(Source))),
    .groups  = "drop"
  )

summary_list <- setNames(
  lapply(seq_len(nrow(by_polity)), function(i) list(
    rows     = by_polity$rows[[i]],
    year_min = by_polity$year_min[[i]],
    year_max = by_polity$year_max[[i]],
    items    = by_polity$items[[i]],
    sources  = by_polity$sources[[i]]
  )),
  by_polity$whep_polity_code
)

summary_path <- file.path(out_dir, "summary_by_polity.json")
write(toJSON(summary_list, auto_unbox = TRUE, pretty = FALSE), summary_path)
cat("[out] ", summary_path, "\n")

# ---- output: per-item JSON (for the map-with-data UI) ------------------------
slugify <- function(s) {
  s <- tolower(s)
  s <- gsub("[^a-z0-9]+", "-", s)
  s <- gsub("^-+|-+$", "", s)
  s
}

matched_only <- pre |> filter(!is.na(whep_polity_code))
items <- matched_only |>
  group_by(item) |>
  summarise(
    unit     = paste(sort(unique(unit)), collapse = ", "),
    year_min = min(year, na.rm = TRUE),
    year_max = max(year, na.rm = TRUE),
    polities = n_distinct(whep_polity_code),
    rows     = n(),
    .groups  = "drop"
  ) |>
  arrange(desc(rows))
items$slug <- vapply(items$item, slugify, character(1))

# ---- no-polygon detection ---------------------------------------------------
`%||%` <- function(a, b) if (is.null(a) || length(a) == 0) b else a
# Check which matched polity codes lack a polygon in the site GeoJSON.
geojson_path <- file.path(proj_root, "site", "polities.geojson")
has_polygon <- character(0)
if (file.exists(geojson_path)) {
  gj <- fromJSON(geojson_path, simplifyVector = FALSE)
  has_polygon <- unique(vapply(gj$features, function(f)
    f$properties$polity_code %||% "", character(1)))
  has_polygon <- has_polygon[nchar(has_polygon) > 0]
  cat(sprintf("[polygon] %d polity codes have geometry in site GeoJSON\n",
              length(has_polygon)))
}

matched_codes <- unique(matched_only$whep_polity_code)
no_poly_codes <- setdiff(matched_codes, has_polygon)
if (length(no_poly_codes) > 0 && length(has_polygon) > 0) {
  cat(sprintf("[polygon] %d matched polity codes have NO polygon\n",
              length(no_poly_codes)))
  # Emit per-polity summary
  np_summary <- matched_only |>
    filter(whep_polity_code %in% no_poly_codes) |>
    group_by(whep_polity_code) |>
    summarise(rows = n(),
              year_min = min(year, na.rm = TRUE),
              year_max = max(year, na.rm = TRUE),
              items = n_distinct(item),
              .groups = "drop") |>
    mutate(whep_name = whep_name_by_code[whep_polity_code]) |>
    arrange(desc(rows))
  np_obj <- lapply(seq_len(nrow(np_summary)), function(i) list(
    whep_polity_code = np_summary$whep_polity_code[[i]],
    whep_polity_name = np_summary$whep_name[[i]],
    rows = np_summary$rows[[i]],
    year_min = np_summary$year_min[[i]],
    year_max = np_summary$year_max[[i]],
    items = np_summary$items[[i]]
  ))
  np_path <- file.path(out_dir, "no_polygon.json")
  write(toJSON(np_obj, auto_unbox = TRUE, pretty = FALSE), np_path)
  cat("[out] ", np_path, "\n")
} else {
  np_path <- file.path(out_dir, "no_polygon.json")
  write("[]", np_path)
}

cat(sprintf("[out] writing %d per-item JSON files...\n", nrow(items)))
unmatched_all <- pre |> filter(match_status == "none", !is.na(value))
for (i in seq_len(nrow(items))) {
  it_name <- items$item[[i]]
  sub <- matched_only |>
    filter(item == it_name, !is.na(value)) |>
    select(year, whep_polity_code, value, country, iso3c)
  # Collapse duplicates (e.g., juan + mitchell for same polity/year): mean.
  # Keep original country/iso for provenance.
  sub <- sub |>
    group_by(year, whep_polity_code, country, iso3c) |>
    summarise(value = mean(value, na.rm = TRUE), .groups = "drop")
  # If multiple input countries map to the same polity/year, pick one and sum.
  sub_agg <- sub |>
    group_by(year, whep_polity_code) |>
    summarise(value = sum(value, na.rm = TRUE),
              country = paste(unique(country), collapse = "; "),
              iso3c = paste(unique(na.omit(iso3c)), collapse = "; "),
              .groups = "drop")
  by_year <- split(sub_agg, sub_agg$year)
  by_year_obj <- lapply(by_year, function(df) {
    setNames(
      lapply(seq_len(nrow(df)), function(k) list(
        v = df$value[[k]],
        c = df$country[[k]],
        i = if (nchar(df$iso3c[[k]]) > 0) df$iso3c[[k]] else NULL
      )),
      df$whep_polity_code
    )
  })

  # Unmatched rows for this item, by year, listing (iso3c, country, value).
  um_sub <- unmatched_all |>
    filter(item == it_name) |>
    select(year, iso3c, country, polity_name, value) |>
    group_by(year, iso3c, country, polity_name) |>
    summarise(value = mean(value, na.rm = TRUE), .groups = "drop")
  um_by_year <- split(um_sub, um_sub$year)
  um_by_year_obj <- lapply(um_by_year, function(df) {
    lapply(seq_len(nrow(df)), function(k) list(
      iso3c   = df$iso3c[[k]],
      country = df$country[[k]],
      name    = df$polity_name[[k]],
      value   = df$value[[k]]
    ))
  })

  # No-polygon rows: matched but polity has no geometry on the map.
  np_sub_data <- matched_only |>
    filter(item == it_name, !is.na(value),
           whep_polity_code %in% no_poly_codes) |>
    select(year, whep_polity_code, country, value) |>
    group_by(year, whep_polity_code, country) |>
    summarise(value = mean(value, na.rm = TRUE), .groups = "drop")
  np_by_year <- split(np_sub_data, np_sub_data$year)
  np_by_year_obj <- lapply(np_by_year, function(df) {
    lapply(seq_len(nrow(df)), function(k) list(
      polity_code = df$whep_polity_code[[k]],
      country     = df$country[[k]],
      value       = df$value[[k]]
    ))
  })

  obj <- list(
    item = it_name,
    unit = items$unit[[i]],
    year_min = items$year_min[[i]],
    year_max = items$year_max[[i]],
    polity_count = items$polities[[i]],
    by_year = by_year_obj,
    unmatched_by_year = um_by_year_obj,
    no_polygon_by_year = np_by_year_obj
  )
  write(toJSON(obj, auto_unbox = TRUE, pretty = FALSE),
        file.path(by_item_dir, paste0(items$slug[[i]], ".json")))
}

# Per-item index.
index_obj <- list(items = lapply(seq_len(nrow(items)), function(i) list(
  slug     = items$slug[[i]],
  item     = items$item[[i]],
  unit     = items$unit[[i]],
  year_min = items$year_min[[i]],
  year_max = items$year_max[[i]],
  polities = items$polities[[i]],
  rows     = items$rows[[i]]
)))
index_path <- file.path(out_dir, "by_item_index.json")
write(toJSON(index_obj, auto_unbox = TRUE, pretty = FALSE), index_path)
cat("[out] ", index_path, "\n")

# ---- output: markdown report --------------------------------------------------
unmatched <- pre |>
  filter(match_status == "none") |>
  count(iso3c, country, polity_name, sort = TRUE) |>
  slice_head(n = 60)

unmatched_yrs <- pre |>
  filter(match_status == "none") |>
  group_by(iso3c, country, polity_name) |>
  summarise(mn = min(year, na.rm = TRUE),
            mx = max(year, na.rm = TRUE),
            .groups = "drop")

unmatched <- unmatched |> left_join(unmatched_yrs,
                                     by = c("iso3c", "country", "polity_name"))

status_tbl <- pre |> count(match_status, sort = TRUE)

report_lines <- c(
  "# before_1961.csv crosslink report",
  "",
  sprintf("- Source: `data/external/before_1961.csv` (%.1f MB, %d rows)",
          file.size(input_path) / 1024^2, n_total),
  sprintf("- Years %d-%d, %d distinct items",
          min(pre$year, na.rm = TRUE), max(pre$year, na.rm = TRUE),
          length(unique(pre$item))),
  "- Pipeline: `pipelines/pre1961-matching/match.R`",
  "- Regenerate: `Rscript pipelines/pre1961-matching/match.R`",
  "",
  "## Match results",
  "",
  "| status | rows | % |",
  "|--------|-----:|----:|",
  paste(sprintf("| %s | %s | %.1f%% |",
                status_tbl$match_status,
                format(status_tbl$n, big.mark = ","),
                100 * status_tbl$n / n_total),
        collapse = "\n"),
  "",
  sprintf("**Matched total:** %s / %s (%.1f%%)",
          format(n_match, big.mark = ","),
          format(n_total, big.mark = ","),
          100 * n_match / n_total),
  "",
  "Preference rule: when multiple WHEP polities cover the input year under the same iso3c, pick the `polity_type == 'national'` one (this collapses the subnational ES01-ES52 / US-state / BR-state rows). The `normalise_iso()` helper rewrites ~30 modern ISO3 codes to their historical WHEP equivalents: YUG\u2192F248, CSK\u2192F51, AUT/HUN<1918\u2192AUH, DEU 1949-1990\u2192F78, TZA<1964\u2192TAN, BWA<1966\u2192BEC, etc. The `name_override` table resolves entries with missing ISO codes (Korea, Natal, Cape, Indochina, Manchuria, Rwanda-Burundi). Extend these rules in `pipelines/pre1961-matching/match.R` when new mismatches surface.",
  "",
  "## Unmatched, top 60",
  "",
  "| iso3c | country | polity_name | years | rows |",
  "|-------|---------|-------------|-------|-----:|",
  paste(sprintf("| `%s` | %s | %s | %d-%d | %s |",
                unmatched$iso3c, unmatched$country, unmatched$polity_name,
                unmatched$mn, unmatched$mx,
                format(unmatched$n, big.mark = ",")),
        collapse = "\n"),
  "",
  "## Confidence audit",
  "",
  "A match isn't automatically correct — `normalise_iso()` may have routed the input to the wrong WHEP polity (silent false positive). For each matched row the pipeline now records `match_confidence`:",
  "",
  "- `iso-equal` — iso3c matches AND input country name shares a 3+-char token with the WHEP polity_name.
- `known-equivalent` — iso3c matches, name differs, but the difference is a known historical/modern pair (Japan ↔ Japanese Empire, Turkey ↔ Türkiye, Ivory Coast ↔ Côte d'Ivoire, etc.). Extend the `name_equiv` table in `match.R`.
- `iso-equal-name-mismatch` — iso3c matches but the WHEP polity_name shares no tokens with the input and isn't in the known-equivalents list. **These are the rows most likely to be silent false positives** (e.g., NGA being matched to the Nupe Kingdom because Nupe's WHEP row also carries iso=NGA).",
  "- `name-overlap` — input country / polity_name shares a 3+-char token with the WHEP polity_name.",
  "- `trusted-rewrite` — the input was rewritten by an explicit rule (YUG\u2192F248, CSK\u2192F51/AUH, DEU 1949-1990\u2192F78, TZA<1964\u2192TAN, BWA<1966\u2192BEC, SDN<2011\u2192SUD, etc.); listed in `trusted_rewrite()` in `match.R`. Note: many former rewrites (IRL\u2192GBR, FIN\u2192F228, AUT/HUN\u2192AUH, TUR\u2192OTT, PAK\u2192IND) were replaced with direct-match polities following the principle that separately-reported data gets its own polity.",
  "- `suspect` — matched but none of the above trust rules fired. These are the false-positive candidates you should audit.",
  "- `none` — unmatched (the panel already shows these).",
  "",
  "| confidence | rows | % |",
  "|-----------|-----:|----:|",
  paste(sprintf("| %s | %s | %.1f%% |",
                conf_tbl$match_confidence,
                format(conf_tbl$n, big.mark = ","),
                100 * conf_tbl$n / n_total),
        collapse = "\n"),
  "",
  sprintf("Top suspect buckets (out of %d total) — review to either add a `trusted_rewrite` rule or fix `normalise_iso()`:",
          sum(conf_tbl$n[conf_tbl$match_confidence == "suspect"])),
  "",
  "| kind | iso3c | input country | assigned polity_code | WHEP polity_name | years | rows |",
  "|------|-------|---------------|----------------------|------------------|-------|-----:|",
  if (nrow(suspects) == 0) "| (none) | | | | | | |" else
  paste(sprintf("| %s | `%s` | %s | `%s` | %s | %d-%d | %s |",
                head(suspects$match_confidence, 30),
                head(suspects$iso3c, 30),
                head(suspects$country, 30),
                head(suspects$whep_polity_code, 30),
                head(suspects$whep_name, 30),
                head(suspects$year_min, 30),
                head(suspects$year_max, 30),
                format(head(suspects$rows, 30), big.mark = ",")),
        collapse = "\n"),
  "",
  "## Data caveats",
  "",
  "Known limitations of the matching identified by audit (2026-04-16):",
  "",
  "- **India/Pakistan overlap 1940-1946:** Both 'India' (undivided British India) and 'Pakistan' have data rows for the same years and commodities. The 'India' rows for 1940-1946 likely include the Pakistan territory. Risk of double-counting when aggregating.",
  "- **Japan empire polygon 1895-1945:** Data matched to JPN-1895-1945 represents metropolitan Japan only (~370k km\u00b2), but the WHEP polygon covers the full Japanese Empire (~658k km\u00b2 including Korea, Taiwan, S. Sakhalin). Korea and Taiwan are tracked separately — no double-counting, but the polygon overstates geographic coverage.",
  "- **Russia/F228 1896-1960:** Data labeled 'Russian Federation' covers European Russia / RSFSR, not the full Russian Empire/USSR. The F228 polygon includes all Soviet republics. This is a known territorial overstatement.",
  "- **South Africa pre-1910:** Data labeled 'South Africa' for 1852-1910 coexists with separate 'Cape Province' and 'Natal' entries. The 'South Africa' rows may be aggregates that include Cape/Natal — risk of double-counting when summing.",
  "",
  "## Outputs",
  "",
  "- `data/compiled/pre1961/matched.csv` - per-row matched file (includes `match_confidence`)",
  "- `data/compiled/pre1961/summary_by_polity.json` - per-polity rollup",
  "- `data/compiled/pre1961/suspects.json` - per-bucket suspect list",
  sprintf("- `data/compiled/pre1961/by_item/<slug>.json` - per-item pivot (%d files)", nrow(items)),
  "- `data/compiled/pre1961/by_item_index.json` - index of item slugs + units + year spans"
)

report_path <- file.path(out_dir, "report.md")
writeLines(report_lines, report_path)
cat("[out] ", report_path, "\n")
cat("[done]\n")
