# ==============================================================================
# Cliopatria Broad Pass: Replace Back-Projected Polygons
# ==============================================================================
# Replace CShapes back-projected polygons with time-appropriate Cliopatria
# boundaries for 12 pre-1886 Italian and German states.
#
# These entries currently use CShapes polygons from 1886+ projected backwards,
# which is inaccurate. Cliopatria provides period-specific boundaries.
#
# Memory-safe: one SQL query per polity.
# ==============================================================================

source("R/00_setup.R")
sf_use_s2(FALSE)

cat("=== Cliopatria Broad Pass: Pre-1886 Polygon Replacements ===\n\n")

db <- read_csv(file.path(final_dir, "polities_database.csv"), show_col_types = FALSE)
poly_path <- file.path(geodata_dir, "polities_polygons.gpkg")
polys <- st_read(poly_path, quiet = TRUE) %>% st_set_crs(4326)

clio_path <- file.path(proj_root, "data", "source", "cliopatria",
                        "cliopatria_polities_only.geojson")
if (!file.exists(clio_path)) {
  tmp_dir <- tempdir()
  unzip(file.path(proj_root, "inputs", "cliopatria.geojson.zip"),
        exdir = tmp_dir, overwrite = TRUE)
  clio_path <- file.path(tmp_dir, "cliopatria_polities_only.geojson")
}

changes <- 0

read_clio <- function(name, from_year, to_year) {
  query <- sprintf(
    "SELECT * FROM cliopatria_polities_only WHERE Name = '%s' AND FromYear <= %d AND ToYear >= %d LIMIT 1",
    gsub("'", "''", name), from_year, to_year)
  tryCatch({
    feat <- st_read(clio_path, query = query, quiet = TRUE)
    if (nrow(feat) > 0) return(st_set_crs(feat[1, ], 4326) %>% st_make_valid())
    NULL
  }, error = function(e) NULL)
}

replace_polygon <- function(code, geom) {
  idx <- which(polys$polity_code == code)
  if (length(idx) > 0) {
    polys[idx, ] <<- st_set_geometry(polys[idx, ], geom)
  } else {
    polys <<- bind_rows(polys, st_sf(polity_code = code, geometry = geom))
  }
}

# Mapping: WHEP code -> (Cliopatria name, from_year, to_year, description)
replacements <- list(
  # Italian pre-unification
  list(code = "SAR-1800-1860", name = "Kingdom of Sardinia",
       fy = 1800, ty = 1813, desc = "Kingdom of Sardinia (Piedmont-Sardinia)"),
  list(code = "TWO-1800-1860", name = "Kingdom of the Two Sicilies",
       fy = 1815, ty = 1819, desc = "Kingdom of the Two Sicilies"),
  list(code = "PAP-1800-1870", name = "Papal States",
       fy = 1800, ty = 1802, desc = "Papal States"),
  list(code = "TUS-1800-1860", name = "Grand Duchy of Tuscany",
       fy = 1800, ty = 1802, desc = "Grand Duchy of Tuscany"),
  list(code = "DMO-1800-1860", name = "Duchy of Modena and Reggio",
       fy = 1815, ty = 1847, desc = "Duchy of Modena and Reggio"),
  list(code = "DPA-1800-1860", name = "Duchy of Parma and Piacenza",
       fy = 1815, ty = 1847, desc = "Duchy of Parma and Piacenza"),
  # German pre-unification
  list(code = "SAX-1800-1871", name = "Electorate of Saxony",
       fy = 1800, ty = 1802, desc = "Electorate/Kingdom of Saxony"),
  list(code = "HAN-1800-1866", name = "Electorate of Hanover",
       fy = 1800, ty = 1802, desc = "Electorate/Kingdom of Hanover"),
  list(code = "NAS-1816-1866", name = "Duchy of Nassau",
       fy = 1815, ty = 1819, desc = "Duchy of Nassau"),
  list(code = "WAL-1816-1870", name = "Principality of Waldeck and Pyrmont",
       fy = 1814, ty = 1819, desc = "Principality of Waldeck and Pyrmont"),
  list(code = "REU-1816-1870", name = "Principality of Reuss-Gera",
       fy = 1815, ty = 1819, desc = "Principality of Reuss-Gera"),
  list(code = "ANH-1864-1870", name = "Duchy of Anhalt",
       fy = 1864, ty = 1865, desc = "Duchy of Anhalt")
)

for (r in replacements) {
  feat <- read_clio(r$name, r$fy, r$ty)
  if (!is.null(feat)) {
    replace_polygon(r$code, st_geometry(feat))
    db$polygon_source[db$polity_code == r$code] <-
      sprintf("Cliopatria (%s %d-%d)", r$name, r$fy, r$ty)
    cat(sprintf("  OK: %-20s <- %s\n", r$code, r$desc))
    changes <- changes + 1
  } else {
    cat(sprintf("  MISS: %-20s %s not found\n", r$code, r$name))
  }
}

# Save
cat(sprintf("\n  Replaced %d polygons\n", changes))
write_csv(db, file.path(final_dir, "polities_database.csv"))

polys <- polys[!duplicated(polys$polity_code, fromLast = TRUE), ]
if (file.exists(poly_path)) file.remove(poly_path)
st_write(polys, poly_path, layer = "polities", quiet = TRUE)
cat(sprintf("  Saved: polities_polygons.gpkg (%d polygons)\n", nrow(polys)))
cat("\n=== Done ===\n")
