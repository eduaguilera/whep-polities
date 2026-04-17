#!/usr/bin/env python3
"""
Build data/final/polities_database.{csv,gpkg} from the wiki.

The wiki (wiki/polities/*.md) is the source of truth. Each page's YAML
frontmatter declares identity + an optional polygon binding:

    polygon_source: <slug from scripts/sources.yaml>
    polygon_feature_id: <matches the source's id_column>
    polygon_feature_year: <int, for temporal sources>

For every polity page:
  1. Parse frontmatter.
  2. If polygon_source is set, look up the source in sources.yaml.
  3. Open the source file (must exist at the declared path), find the
     feature where id_column == polygon_feature_id (cast to id_type)
     and, if the source has a temporal block, start <= year <= end (or
     start == year, per match_year policy).
  4. Attach the geometry to the polity row.

Outputs:
  data/final/polities_database.csv    — one row per wiki page
  data/final/polities_database.gpkg   — same rows + geometry (where present)

Missing polygons are logged but don't abort the build. The master GPKG
size is controlled by the simplification step (--simplify-tolerance).
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import Any

import yaml
from osgeo import ogr, osr

ogr.UseExceptions()
osr.UseExceptions()

REPO_ROOT = Path(__file__).resolve().parent.parent
WIKI_DIR = REPO_ROOT / "wiki" / "polities"
SOURCES_YAML = REPO_ROOT / "scripts" / "sources.yaml"
OUT_DIR = REPO_ROOT / "data" / "final"

# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

def parse_frontmatter(md_path: Path) -> dict[str, Any] | None:
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    fm_text = text[4:end]
    try:
        return yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as e:
        print(f"  ! YAML error in {md_path.name}: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Source loading
# ---------------------------------------------------------------------------

def load_sources_config() -> dict[str, dict[str, Any]]:
    with open(SOURCES_YAML) as f:
        cfg = yaml.safe_load(f)
    return cfg["sources"]


class SourceReader:
    """Cache of opened OGR layers, one per source."""

    def __init__(self, sources_cfg: dict[str, dict[str, Any]]):
        self.cfg = sources_cfg
        self._layers: dict[str, ogr.Layer] = {}
        self._datasets: dict[str, Any] = {}  # hold refs so layers stay alive

    def get_layer(self, slug: str) -> ogr.Layer | None:
        if slug in self._layers:
            return self._layers[slug]
        if slug not in self.cfg:
            return None
        entry = self.cfg[slug]
        path = REPO_ROOT / entry["file"]
        if not path.exists():
            return None
        ds = ogr.Open(str(path))
        if ds is None:
            return None
        layer_name = entry.get("layer")
        lyr = ds.GetLayerByName(layer_name) if layer_name else ds.GetLayer(0)
        if lyr is None:
            return None
        self._datasets[slug] = ds
        self._layers[slug] = lyr
        return lyr

    def find_feature(
        self, slug: str, feature_id: Any, feature_year: int | None
    ) -> ogr.Feature | None:
        entry = self.cfg.get(slug)
        if entry is None:
            return None
        lyr = self.get_layer(slug)
        if lyr is None:
            return None

        id_col = entry["id_column"]
        id_type = entry.get("id_type", "str")
        temporal = entry.get("temporal")

        # Cast wiki value to the column type.
        if id_type == "int":
            try:
                fid_val = int(feature_id)
            except (TypeError, ValueError):
                return None
        else:
            fid_val = str(feature_id)

        lyr.ResetReading()
        for feat in lyr:
            v = feat.GetField(id_col)
            if v is None:
                continue
            if id_type == "int":
                try:
                    if int(v) != fid_val:
                        continue
                except (TypeError, ValueError):
                    continue
            else:
                if str(v) != fid_val:
                    continue

            if temporal is not None and feature_year is not None:
                s = feat.GetField(temporal["start_column"])
                e = feat.GetField(temporal["end_column"])
                if s is None or e is None:
                    continue
                # Allow date strings: take the year prefix.
                s_year = int(str(s)[:4])
                e_year = int(str(e)[:4])
                match = temporal.get("match_year", "within")
                if match == "within":
                    if not (s_year <= feature_year <= e_year):
                        continue
                elif match == "exact_start":
                    if s_year != feature_year:
                        continue
            return feat.Clone()
        return None


# ---------------------------------------------------------------------------
# CSV columns (order matches the existing polities_database.csv)
# ---------------------------------------------------------------------------

# CSV column → wiki-frontmatter key. The wiki uses short Obsidian-friendly
# names (iso3, type, cow); the CSV uses the longer names the downstream
# pipelines/pre1961-matching/ expects (iso3_code, polity_type, cow_code).
CSV_COLUMN_TO_FM_KEY = {
    "polity_code": "polity_code",
    "polity_name": "polity_name",
    "start_year":  "start_year",
    "end_year":    "end_year",
    "polity_type": "type",
    "iso3_code":   "iso3",
    "cow_code":    "cow",
    "continent":   "continent",
    "wiki_status": "status",
    "last_ingest": "last_ingest",
    "polygon_source":       "polygon_source",
    "polygon_feature_id":   "polygon_feature_id",
    "polygon_feature_year": "polygon_feature_year",
    "polygon_status":       "polygon_status",
    "polygon_area_km2":     "polygon_area_km2",
}
CSV_COLUMNS = list(CSV_COLUMN_TO_FM_KEY.keys())


def flatten_row(fm: dict[str, Any]) -> dict[str, Any]:
    row = {}
    for col, fm_key in CSV_COLUMN_TO_FM_KEY.items():
        v = fm.get(fm_key)
        if isinstance(v, list):
            v = "; ".join(str(x) for x in v)
        row[col] = "" if v is None else v
    return row


# ---------------------------------------------------------------------------
# GeoPackage writer
# ---------------------------------------------------------------------------

def write_gpkg(
    rows: list[dict[str, Any]],
    geometries: dict[str, ogr.Geometry],
    out_path: Path,
    simplify_tolerance: float,
) -> None:
    if out_path.exists():
        out_path.unlink()
    drv = ogr.GetDriverByName("GPKG")
    ds = drv.CreateDataSource(str(out_path))

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

    lyr = ds.CreateLayer("polities", srs, ogr.wkbMultiPolygon)
    for col in CSV_COLUMNS:
        ftype = ogr.OFTInteger if col in ("start_year", "end_year") else ogr.OFTString
        lyr.CreateField(ogr.FieldDefn(col, ftype))

    defn = lyr.GetLayerDefn()
    for row in rows:
        f = ogr.Feature(defn)
        for col in CSV_COLUMNS:
            val = row[col]
            if val == "" or val is None:
                continue
            if col in ("start_year", "end_year"):
                try:
                    f.SetField(col, int(val))
                except (ValueError, TypeError):
                    pass
            else:
                f.SetField(col, str(val))

        geom = geometries.get(row["polity_code"])
        if geom is not None:
            g = geom.Clone()
            if simplify_tolerance > 0:
                g = g.SimplifyPreserveTopology(simplify_tolerance)
            if g.GetGeometryType() != ogr.wkbMultiPolygon:
                g = ogr.ForceToMultiPolygon(g)
            f.SetGeometry(g)
        lyr.CreateFeature(f)

    ds = None


def write_csv(rows: list[dict[str, Any]], out_path: Path) -> None:
    import csv
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(r)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--simplify-tolerance",
        type=float,
        default=0.01,
        help="Douglas-Peucker tolerance in degrees (0 to disable). "
             "Default 0.01 ≈ 1 km at equator; keeps the master GPKG under 5 MB.",
    )
    args = ap.parse_args()

    sources_cfg = load_sources_config()
    reader = SourceReader(sources_cfg)

    pages = sorted(p for p in WIKI_DIR.glob("*.md")
                   if not p.name.startswith("_"))
    print(f"Wiki pages: {len(pages)}")

    rows: list[dict[str, Any]] = []
    geometries: dict[str, ogr.Geometry] = {}

    n_assigned = 0
    n_missing_source = 0
    n_source_not_fetched = 0
    n_feature_not_found = 0

    missing_sources: set[str] = set()
    skipped_pages: list[tuple[str, str]] = []  # (page name, reason)
    seen_codes: dict[str, Path] = {}            # detect duplicates

    for page in pages:
        fm = parse_frontmatter(page)
        if fm is None:
            skipped_pages.append((page.name, "unreadable frontmatter"))
            continue
        pc = fm.get("polity_code")
        if not pc:
            skipped_pages.append((page.name, "no polity_code in frontmatter"))
            continue
        if pc in seen_codes:
            skipped_pages.append(
                (page.name,
                 f"duplicate polity_code {pc!r} (also in {seen_codes[pc].name})")
            )
            continue
        seen_codes[pc] = page

        rows.append(flatten_row(fm))

        src = fm.get("polygon_source")
        fid = fm.get("polygon_feature_id")
        fyear = fm.get("polygon_feature_year")

        if not src or src == "none":
            continue
        if src not in sources_cfg:
            print(f"  ! {pc}: unknown polygon_source '{src}'", file=sys.stderr)
            n_missing_source += 1
            continue
        if reader.get_layer(src) is None:
            missing_sources.add(src)
            n_source_not_fetched += 1
            continue

        feat = reader.find_feature(src, fid, fyear)
        if feat is None:
            n_feature_not_found += 1
            print(f"  ! {pc}: no match in {src} for id={fid!r} year={fyear}",
                  file=sys.stderr)
            continue

        geom = feat.GetGeometryRef()
        if geom is None:
            n_feature_not_found += 1
            continue
        geometries[pc] = geom.Clone()
        n_assigned += 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "polities_database.csv"
    gpkg_path = OUT_DIR / "polities_database.gpkg"
    write_csv(rows, csv_path)
    write_gpkg(rows, geometries, gpkg_path, args.simplify_tolerance)

    print()
    print(f"Wiki pages scanned:     {len(pages)}")
    print(f"Rows written:           {len(rows)}"
          + ("  ✓" if len(rows) == len(pages) else "  ✗ ROW COUNT MISMATCH"))
    if skipped_pages:
        print(f"Pages skipped:          {len(skipped_pages)}")
        for name, reason in skipped_pages:
            print(f"  - {name}: {reason}", file=sys.stderr)
    print(f"Geometries attached:    {n_assigned}")
    print(f"  source not fetched:   {n_source_not_fetched}"
          f"  (run scripts/sources/<slug>/fetch.*)")
    print(f"  unknown source slug:  {n_missing_source}")
    print(f"  feature not found:    {n_feature_not_found}")
    if missing_sources:
        print(f"  sources to fetch:     {', '.join(sorted(missing_sources))}")
    print()
    print(f"Wrote {csv_path.relative_to(REPO_ROOT)}")
    print(f"Wrote {gpkg_path.relative_to(REPO_ROOT)} "
          f"({gpkg_path.stat().st_size / 1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
