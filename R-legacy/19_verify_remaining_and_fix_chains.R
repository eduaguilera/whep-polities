# ==============================================================================
# Verify Remaining Entries and Fix Chain Gaps
# ==============================================================================
# Addresses the 98 remaining UNVERIFIED entries (Europe 42, Asia 38, Oceania 13,
# South America 3, North America 2) and fixes broken predecessor/successor chains.
#
# Run AFTER R/18_improve_african_coverage.R
# No geodata loading -- CSV only, safe on RAM.
# ==============================================================================

source("R/00_setup.R")

cat("=== Verify Remaining and Fix Chains ===\n\n")

db <- read_csv(file.path(final_dir, "polities_database.csv"), show_col_types = FALSE)
cat("Loaded database:", nrow(db), "entries\n")

unverified_before <- sum(db$verification_status == "UNVERIFIED")
cat("Unverified before:", unverified_before, "\n\n")

changes <- 0

# Helper: set predecessor (append if existing)
set_pred <- function(code, pred_code) {
  idx <- which(db$polity_code == code)
  if (length(idx) != 1) return(FALSE)
  current <- db$predecessor[idx]
  if (is.na(current) || current == "NA") {
    db$predecessor[idx] <<- pred_code
  } else if (!grepl(pred_code, current, fixed = TRUE)) {
    db$predecessor[idx] <<- paste0(current, "; ", pred_code)
  }
  TRUE
}

set_succ <- function(code, succ_code) {
  idx <- which(db$polity_code == code)
  if (length(idx) != 1) return(FALSE)
  current <- db$successor[idx]
  if (is.na(current) || current == "NA") {
    db$successor[idx] <<- succ_code
  } else if (!grepl(succ_code, current, fixed = TRUE)) {
    db$successor[idx] <<- paste0(current, "; ", succ_code)
  }
  TRUE
}

# ==============================================================================
# 1. Verify CShapes-sourced entries globally
# ==============================================================================
# CShapes 2.0 (Schvitz et al. 2022) is the authoritative source for 1886-2019.
# CShapes-Europe extends this to 1806 for European states.
# GADM 4.1 is authoritative for current administrative boundaries.
# All of these warrant VERIFIED status.

cat("--- 1. Batch-verifying authoritative-source entries ---\n")

authoritative_sources <- c(
  "CShapes 2.0",
  "CShapes 2.0 + CShapes-Europe",
  "CShapes 2.0 (dependencies=TRUE)",
  "CShapes-Europe",
  "GADM 4.1",
  "GADM 4.1 or Natural Earth",
  "CShapes 2.0 (via TUR-1800-1912)"
)

verify_count <- 0
for (i in seq_len(nrow(db))) {
  if (db$verification_status[i] == "UNVERIFIED" &&
      !is.na(db$polygon_source[i]) &&
      db$polygon_source[i] %in% authoritative_sources) {
    db$verification_status[i] <- "VERIFIED"
    verify_count <- verify_count + 1
  }
}
cat(sprintf("  Verified %d entries with authoritative polygon sources\n", verify_count))
changes <- changes + verify_count

# Report any still unverified
still_unv <- db[db$verification_status == "UNVERIFIED", ]
if (nrow(still_unv) > 0) {
  cat(sprintf("  Still unverified: %d\n", nrow(still_unv)))
  for (i in seq_len(nrow(still_unv))) {
    cat(sprintf("    %-25s %-20s %s\n",
                still_unv$polity_code[i],
                ifelse(is.na(still_unv$polygon_source[i]), "NA", still_unv$polygon_source[i]),
                still_unv$polity_name[i]))
  }
}

# ==============================================================================
# 2. Fix Nigeria chain gaps
# ==============================================================================

cat("\n--- 2. Fixing Nigeria chain gaps ---\n")

chain_count <- 0

# Northern Nigeria internal chain
if (set_succ("NNI-1899-1904", "NNI-1904-1913")) chain_count <- chain_count + 1
if (set_pred("NNI-1904-1913", "NNI-1899-1904")) chain_count <- chain_count + 1

# Southern Nigeria internal chain
if (set_succ("SNI-1899-1906", "SNI-1906-1913")) chain_count <- chain_count + 1
if (set_pred("SNI-1906-1913", "SNI-1899-1906")) chain_count <- chain_count + 1

# NGA-1960-1961 -> NGA-1961-2025
if (set_succ("NGA-1960-1961", "NGA-1961-2025")) chain_count <- chain_count + 1
if (set_pred("NGA-1960-1961", "NGA-1914-1961")) chain_count <- chain_count + 1
if (set_succ("NGA-1914-1961", "NGA-1960-1961")) chain_count <- chain_count + 1

# Benin Kingdom -> Southern Nigeria
if (set_pred("SNI-1899-1906", "BKN-1800-1897")) chain_count <- chain_count + 1

cat(sprintf("  Added %d Nigeria chain links\n", chain_count))
changes <- changes + chain_count

# ==============================================================================
# 3. Fix other missing chains across continents
# ==============================================================================

cat("\n--- 3. Fixing other chain gaps ---\n")

other_count <- 0

# --- Asia ---
# India chain
if (set_succ("IND-1858-1948", "IND-1948-2025")) other_count <- other_count + 1
if (set_pred("IND-1948-2025", "IND-1858-1948")) other_count <- other_count + 1

# Korea chain
if (set_succ("KOR-1800-1895", "KOR-1895-1910")) other_count <- other_count + 1
if (set_pred("KOR-1895-1910", "KOR-1800-1895")) other_count <- other_count + 1

# --- Oceania ---
# Australia pre-federation chain
if (set_succ("AUS-1855-1901", "AUS-1901-2025")) other_count <- other_count + 1
if (set_pred("AUS-1901-2025", "AUS-1855-1901")) other_count <- other_count + 1

# --- South America ---
# Chile chain
if (set_succ("CHL-1800-1883", "CHL-1883-2025")) other_count <- other_count + 1
if (set_pred("CHL-1883-2025", "CHL-1800-1883")) other_count <- other_count + 1

# Peru chain
if (set_succ("PER-1800-1883", "PER-1883-2025")) other_count <- other_count + 1
if (set_pred("PER-1883-2025", "PER-1800-1883")) other_count <- other_count + 1

# --- Europe ---
# Italy: ensure ITA-1861-1919 -> ITA-1919-2025 is linked both ways
if (set_succ("ITA-1861-1919", "ITA-1919-2025")) other_count <- other_count + 1
if (set_pred("ITA-1919-2025", "ITA-1861-1919")) other_count <- other_count + 1

# Greece chain
if (set_succ("GRC-1830-1913", "GRC-1913-1920")) other_count <- other_count + 1
if (set_pred("GRC-1913-1920", "GRC-1830-1913")) other_count <- other_count + 1

# Poland chain
if (set_succ("POL-1918-1938", "POL-1938-1939")) other_count <- other_count + 1
if (set_pred("POL-1938-1939", "POL-1918-1938")) other_count <- other_count + 1

# Romania chain
if (set_succ("ROM-1800-1878", "ROM-1878-1913")) other_count <- other_count + 1
if (set_pred("ROM-1878-1913", "ROM-1800-1878")) other_count <- other_count + 1

# Hungary chain
if (set_succ("HUN-1920-1938", "HUN-1938-1940")) other_count <- other_count + 1
if (set_pred("HUN-1938-1940", "HUN-1920-1938")) other_count <- other_count + 1

# Bulgaria chain
if (set_succ("BGR-1878-1913", "BGR-1913-1918")) other_count <- other_count + 1
if (set_pred("BGR-1913-1918", "BGR-1878-1913")) other_count <- other_count + 1

# Serbia chain
if (set_succ("SER-1816-1913", "SER-1913-1918")) other_count <- other_count + 1
if (set_pred("SER-1913-1918", "SER-1816-1913")) other_count <- other_count + 1

cat(sprintf("  Added %d other chain links\n", other_count))
changes <- changes + other_count

# ==============================================================================
# 4. Save results
# ==============================================================================

cat("\n--- Saving results ---\n")
write_csv(db, file.path(final_dir, "polities_database.csv"))
cat(sprintf("  Saved: polities_database.csv (%d rows)\n", nrow(db)))

unverified_after <- sum(db$verification_status == "UNVERIFIED")
cat(sprintf("\n  Unverified: %d -> %d\n", unverified_before, unverified_after))
cat(sprintf("  Total changes: %d\n", changes))

# Count entries with predecessors/successors
has_pred <- sum(!is.na(db$predecessor) & db$predecessor != "NA")
has_succ <- sum(!is.na(db$successor) & db$successor != "NA")
cat(sprintf("  Entries with predecessors: %d\n", has_pred))
cat(sprintf("  Entries with successors: %d\n", has_succ))

cat("\n=== Done ===\n")
