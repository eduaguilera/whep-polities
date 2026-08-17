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
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from osgeo import ogr, osr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spherical_edges  # noqa: E402  (needs the path above)

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

        # Collect all features that match the id (and temporal window),
        # then break ties by preferring the feature whose start-year equals
        # the queried year. This disambiguates cases like CShapes where two
        # adjacent time-steps share a boundary year (e.g. gwcode 380 has
        # both 1886-1905 and 1905-2019; for year=1905 we want the 1905-one).
        candidates = []
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

            s_year = e_year = None
            if temporal is not None and feature_year is not None:
                s = feat.GetField(temporal["start_column"])
                e = feat.GetField(temporal["end_column"])
                if s is None or e is None:
                    continue
                s_year = int(str(s)[:4])
                e_year = int(str(e)[:4])
                match = temporal.get("match_year", "within")
                if match == "within":
                    if not (s_year <= feature_year <= e_year):
                        continue
                elif match == "exact_start":
                    if s_year != feature_year:
                        continue
            candidates.append((feat.Clone(), s_year))

        if not candidates:
            return None
        # Prefer features where start_year == queried year.
        if feature_year is not None:
            exact = [f for f, s in candidates if s == feature_year]
            if exact:
                return exact[0]
        return candidates[0][0]


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
    "predecessor":          "predecessor",
    "successor":            "successor",
}
CSV_COLUMNS = list(CSV_COLUMN_TO_FM_KEY.keys())


def flatten_row(fm: dict[str, Any]) -> dict[str, Any]:
    row = {}
    for col, fm_key in CSV_COLUMN_TO_FM_KEY.items():
        v = fm.get(fm_key)
        if isinstance(v, list):
            v = "; ".join(str(x) for x in v)
        v = "" if v is None else v
        # A frontmatter value of `NA` means missing, but YAML reads it as the
        # STRING "NA", so it reached the published CSV as text that looks present.
        # The database therefore carried two spellings of missing in one column:
        # iso3_code had 79 rows of "NA" and 3 empty, cow_code 185 and 31. A
        # consumer checking `== ""` found 3 of 82 missing ISO3 codes, and any
        # `!is.na(iso3)` guard treated 79 rows as carrying a valid code — which the
        # ISO3-keyed bridges in the WHEP package do (see eduaguilera/whep#382,
        # where the same artifact had to be undone on the reading side).
        #
        # Normalised here rather than across 266 wiki pages: `NA` is a fine thing
        # to write by hand, and the published artifact is where consistency
        # matters. "NA" is not a legitimate value for any of these fields —
        # Namibia is NAM, not NA.
        if isinstance(v, str) and v.strip() == "NA":
            v = ""
        row[col] = v
    return row


# ---------------------------------------------------------------------------
# GeoPackage writer
# ---------------------------------------------------------------------------

def existing_geometry_count(path: Path) -> int | None:
    """How many non-empty geometries the GeoPackage at `path` already holds."""
    if not path.exists():
        return None
    try:
        ds = ogr.Open(str(path))
        if ds is None:
            return None
        lyr = ds.GetLayer()
        n = sum(1 for f in lyr
                if (g := f.GetGeometryRef()) is not None and not g.IsEmpty())
        return n
    except Exception:
        return None




def gpkg_attribute_mismatches(
    rows: list[dict[str, Any]], gpkg_path: Path
) -> list[tuple[str, str, Any, Any]]:
    """Non-geometry fields where the GeoPackage disagrees with the wiki rows.

    Returns (polity_code, field, in_gpkg, expected). Empty when the file is
    absent or unreadable — a missing GeoPackage is a different problem, and
    reporting it as attribute drift would be misleading.
    """
    if not gpkg_path.exists():
        return []
    ds = ogr.Open(str(gpkg_path))
    if ds is None:
        return []
    lyr = ds.GetLayer(0)
    by_code = {r["polity_code"]: r for r in rows}
    fields = [lyr.GetLayerDefn().GetFieldDefn(i).GetName()
              for i in range(lyr.GetLayerDefn().GetFieldCount())]
    out: list[tuple[str, str, Any, Any]] = []
    lyr.ResetReading()
    for feat in lyr:
        code = feat.GetField("polity_code")
        row = by_code.get(code)
        if row is None:
            out.append((code, "<row>", "present in gpkg", "absent from the wiki"))
            continue
        for f in fields:
            if f not in row:
                continue
            have, want = feat.GetField(f), row.get(f, "")
            if f in ("start_year", "end_year"):
                want_v = int(want) if str(want).strip() else None
                if have != want_v:
                    out.append((code, f, have, want_v))
                continue
            have_s = "" if have is None else str(have)
            want_s = "" if want is None else str(want)
            if have_s != want_s:
                out.append((code, f, have_s, want_s))
    return out


def sync_gpkg_attributes(rows: list[dict[str, Any]], out_path: Path) -> str:
    """Update the GeoPackage's non-geometry fields from `rows`, in place.

    Only safe when both sides describe the same set of polities: if the row set
    differs, the shape of the table has changed and a real rebuild is needed, so
    this declines rather than guessing.

    Returns a one-line summary for the caller's message.
    """
    if not out_path.exists():
        return "  (no GeoPackage to sync)"
    ds = ogr.Open(str(out_path), update=1)
    if ds is None:
        return "  (GeoPackage could not be opened for attribute sync)"
    lyr = ds.GetLayer(0)
    by_code = {r["polity_code"]: r for r in rows}

    codes_in_file = set()
    lyr.ResetReading()
    for feat in lyr:
        codes_in_file.add(feat.GetField("polity_code"))
    if codes_in_file != set(by_code):
        ds = None
        return ("  ATTRIBUTES NOT SYNCED: the GeoPackage holds a different set of "
                "polities than the wiki, so a full rebuild is required.")

    fields = [lyr.GetLayerDefn().GetFieldDefn(i).GetName()
              for i in range(lyr.GetLayerDefn().GetFieldCount())]
    changed = 0
    changed_codes: list[str] = []
    lyr.ResetReading()
    for feat in lyr:
        row = by_code[feat.GetField("polity_code")]
        dirty = False
        for f in fields:
            if f not in row:
                continue
            want = row.get(f, "")
            have = feat.GetField(f)
            if f in ("start_year", "end_year"):
                want_v = int(want) if str(want).strip() else None
                if have != want_v:
                    feat.SetField(f, want_v) if want_v is not None else feat.SetFieldNull(f)
                    dirty = True
                continue
            want_s = "" if want is None else str(want)
            have_s = "" if have is None else str(have)
            # An empty value stored as an empty STRING is not the same as NULL, and
            # collapsing both to "" here hid that: the sync reported "already
            # matched" while 79 rows held "" where they should hold NULL.
            needs_null = want_s == "" and have is not None
            if have_s != want_s or needs_null:
                # An empty value must become NULL, not an empty STRING. The
                # GeoPackage writer skips empty fields, which leaves them NULL, so
                # writing "" here would make synced rows differ from written ones —
                # and an empty string reads back as present. Normalising "NA" to
                # empty upstream then syncing it as "" moved the problem rather than
                # fixing it: sf saw 79 empty strings instead of 79 NAs, and
                # `is.na(iso3_code)` still found only 3 of 82 missing codes.
                if want_s == "":
                    feat.SetFieldNull(f)
                else:
                    feat.SetField(f, want_s)
                dirty = True
        if dirty:
            lyr.SetFeature(feat)
            changed += 1
            changed_codes.append(row["polity_code"])
    ds = None
    if changed == 0:
        return "  Attributes already matched the wiki; geometries untouched."
    return (f"  SYNCED {changed} row(s)' attributes in place (geometries "
            f"untouched): {', '.join(sorted(changed_codes)[:8])}"
            + (" ..." if changed > 8 else ""))


def load_s2_repair():
    """The polygon repair from scripts/repair_s2_polygons.py, or a no-op that warns.

    Imported lazily and tolerantly rather than at module scope. `--check` runs in CI
    and touches no geometry, and this builder is otherwise pure GDAL, so a missing
    shapely or spherely must not stop a wiki-to-CSV comparison. When the repair IS
    unavailable the rebuild still succeeds and says so loudly -- and
    validate_s2_polygons.py is the backstop that fails in CI if an unrepaired polygon
    reaches the committed GeoPackage.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import shapely  # noqa: F401 - repair_wkb imports these lazily, so probe here
        import spherely  # noqa: F401

        from repair_s2_polygons import repair_wkb
    except ImportError as exc:
        print(
            f"  ! s2 polygon repair unavailable ({exc}); geometries written as-is. "
            f"Install shapely+spherely (requirements-ci.txt) or "
            f"validate_s2_polygons.py will fail.",
            file=sys.stderr,
        )
        return lambda wkb: None
    return repair_wkb


def load_s2_check():
    """A predicate `wkb -> bool`: can s2 load this, or the repair make it loadable?

    Used by the simplification ladder, which has to know whether a tolerance produced a
    geometry the repair below can still rescue. Unavailable dependencies degrade to "yes"
    -- same tolerance as load_s2_repair, same backstop.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import shapely
        import spherely  # noqa: F401

        from repair_s2_polygons import repair_geometry, s2_failure
    except ImportError:
        return None

    def ok(wkb: bytes) -> bool:
        geom = shapely.from_wkb(wkb)
        if s2_failure(geom) is None:
            return True
        return s2_failure(repair_geometry(geom)) is None

    return ok
def densify_planar_edges(geom: ogr.Geometry, tolerance_deg: float) -> ogr.Geometry:
    """Insert vertices so each edge's GREAT CIRCLE tracks the line it was drawn as.

    Every source here is a planar product: a straight treaty border is two
    vertices, and a planar viewer joins them with the straight line the treaty
    describes. A consumer using s2 -- which `sf` does by default, and which any
    geodesic area requires -- joins them with a GREAT CIRCLE instead, and between
    two points at equal latitude that bulges poleward. The published 49th-parallel
    US/Canada border was one segment 27.6 degrees wide, so it rendered as an arc
    reaching 49.83 and booked 12.33 Mha of Canadian prairie to the United States
    (eduaguilera/whep#529).

    THIS MUST RUN AFTER SIMPLIFICATION, not before, and the ordering is the whole
    fix rather than a detail. Douglas-Peucker measures deviation from the chord in
    PLANAR degrees, so vertices lying on the chord are the first thing it deletes
    -- and that is how the worst case in this database was created rather than
    inherited: CShapes 2.0 stores that border with 124 vertices, widest gap 1.95
    degrees, and `SimplifyPreserveTopology(0.01)` collapses all 124 into one
    chord. Densifying first would simply hand DP more vertices to delete.

    Planar-side this is a no-op by construction -- the inserted points lie exactly
    ON the existing segment, so planar area is unchanged to the bit and no ring can
    gain a self-intersection. Verified on the published database: planar area delta
    0.0, and the planar-invalid count unchanged.
    """
    if tolerance_deg <= 0:
        return geom
    flat = ogr.GT_Flatten(geom.GetGeometryType())
    if flat == ogr.wkbPolygon:
        out = ogr.Geometry(ogr.wkbPolygon)
        for i in range(geom.GetGeometryCount()):
            ring = geom.GetGeometryRef(i)
            coords = [
                (ring.GetX(j), ring.GetY(j)) for j in range(ring.GetPointCount())
            ]
            new_ring = ogr.Geometry(ogr.wkbLinearRing)
            for lon, lat in spherical_edges.densify_ring(coords, tolerance_deg):
                new_ring.AddPoint_2D(lon, lat)
            out.AddGeometry(new_ring)
        return out
    if flat in (ogr.wkbMultiPolygon, ogr.wkbGeometryCollection):
        out = ogr.Geometry(flat)
        for i in range(geom.GetGeometryCount()):
            out.AddGeometry(
                densify_planar_edges(geom.GetGeometryRef(i), tolerance_deg)
            )
        return out
    return geom


def write_gpkg(
    rows: list[dict[str, Any]],
    geometries: dict[str, ogr.Geometry],
    out_path: Path,
    simplify_tolerance: float,
    densify_tolerance: float = spherical_edges.DEFAULT_TOLERANCE_DEG,
    allow_fewer: bool = False,
) -> None:
    # GUARD: the raw polygon sources under data/geodata are gitignored, so a
    # rebuild in a fresh checkout or a git worktree attaches almost nothing and
    # would overwrite the committed GeoPackage with a near-empty one — observed
    # shrinking it from 12.6 MB to 208 KB. `--check` only compares the CSV, so
    # CI would not catch it either. Refuse rather than silently destroy; a
    # legitimate reduction (rows superseded) is rare and can pass --allow-fewer.
    before = existing_geometry_count(out_path)
    after = len(geometries)
    if before is not None and after < before and not allow_fewer:
        # Refusing to rewrite geometries must NOT leave the two published
        # artifacts disagreeing. They are read by different consumers — the
        # manifest is built from the CSV, while the WHEP R package reads the
        # GeoPackage — so an attribute that changed in the wiki but only reached
        # the CSV makes them contradict each other. That happened: retiring
        # GCO-1884-2025 updated the CSV, the guard (correctly) declined the
        # GeoPackage, and the file consumers actually read still said `draft`
        # while the manifest said the row was dead.
        #
        # So sync the non-geometry fields in place first. Geometries are never
        # touched, which is the whole point of the guard.
        synced = sync_gpkg_attributes(rows, out_path)
        raise SystemExit(
            f"\nREFUSING to write {out_path.name}: it currently holds {before} "
            f"geometries and this run attached only {after}.\n"
            f"  Almost certainly the raw polygon sources are missing — they are "
            f"gitignored and fetched per source:\n"
            f"    bash scripts/sources/<slug>/fetch.sh   (see README 'Rebuilding from scratch')\n"
            f"  The CSV was written; only the GeoPackage is untouched, so the "
            f"committed geometries are safe.\n"
            f"  If the reduction is intended (rows superseded), re-run with "
            f"--allow-fewer-geometries.\n"
            f"{synced}")
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

    repair_wkb = load_s2_repair()
    s2_check = load_s2_check()
    s2_repaired: list[str] = []

    defn = lyr.GetLayerDefn()
    repairs = {"repaired": [], "skipped": [], "failed": []}
    simplifies = {"done": 0, "kept": [], "reduced": [], "s2_refined": [], "s2_unresolved": []}
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
                g = _simplify_if_cheap(
                    g, simplify_tolerance, row["polity_code"], simplifies, s2_check
                )
            # After simplification, never before: see densify_planar_edges.
            g = densify_planar_edges(g, densify_tolerance)
            if g.GetGeometryType() != ogr.wkbMultiPolygon:
                g = ogr.ForceToMultiPolygon(g)
            # TWO REPAIRS, DIFFERENT AXES, IN THIS ORDER.
            #
            # s2 first. It is area-PRESERVING and fixes the thing that makes a geometry unloadable
            # by s2geometry -- which is what R's sf uses by default, so it is the failure a consumer
            # actually hits: sf::st_area() and st_intersection() ABORT rather than returning
            # something distorted. Repaired after simplification because simplification is part of
            # what it has to clean up: a Douglas-Peucker pass can leave two non-adjacent edges of a
            # ring touching to within one ULP, which GEOS reads as no intersection and s2 -- which
            # rounds lon/lat onto unit vectors first -- reads as a crossing. Two of the ten
            # unloadable polygons were GEOS-VALID, so no planar check here could have seen them.
            #
            # GEOS second, and only when it costs almost nothing. s2-loadable is not the same as
            # GEOS-valid, and _repair_if_free() closes that gap under an area budget so a rebuild
            # never silently takes the 12,845 km2 IRN-1800-1828 decision. Running it second means it
            # judges the geometry a consumer will actually receive.
            fixed = repair_wkb(bytes(g.ExportToWkb()))
            if fixed is not None:
                g = ogr.CreateGeometryFromWkb(fixed)
                s2_repaired.append(row["polity_code"])
            g = _repair_if_free(g, row["polity_code"], repairs)
            f.SetGeometry(g)
        lyr.CreateFeature(f)

    if simplifies["reduced"]:
        print(f"  simplified {len(simplifies['reduced'])} geometry(ies) at a FINER tolerance: "
              f"the requested one would have cost more than {SIMPLIFY_MAX_AREA_CHANGE:.0%} "
              f"of their area")
        for code, factor, change in sorted(simplifies["reduced"], key=lambda t: t[1]):
            print(f"    {code}: tolerance x{factor:g}, cost {change:.2%}")
    if simplifies["kept"]:
        print(f"  published {len(simplifies['kept'])} geometry(ies) UNSIMPLIFIED: even the finest "
              f"ladder step would have cost more than {SIMPLIFY_MAX_AREA_CHANGE:.0%}")
        for code, change in sorted(simplifies["kept"], key=lambda t: -t[1]):
            print(f"    {code}: coarsest step would have lost {change:.1%}")
    if repairs["repaired"]:
        print(f"  repaired {len(repairs['repaired'])} invalid geometry(ies) at "
              f"<={REPAIR_MAX_AREA_CHANGE:.1%} area cost")
    for code, change in repairs["skipped"]:
        print(f"  LEFT INVALID {code}: repair would move {change:.3%} of its area, above the "
              f"{REPAIR_MAX_AREA_CHANGE:.1%} threshold - decide it on the page")
    for code in repairs["failed"]:
        print(f"  LEFT INVALID {code}: MakeValid produced nothing usable")

    ds = None
    if s2_repaired:
        print(
            f"  s2-repaired {len(s2_repaired)} geometry(ies) on write: "
            + ", ".join(sorted(s2_repaired))
        )
    for code, factor in simplifies["s2_refined"]:
        print(f"  simplified {code} FINER than tolerance x{factor:g}: that step left a "
              f"geometry s2 cannot load and the repair cannot rescue")
    for code, factor in simplifies["s2_unresolved"]:
        print(f"  NO s2-LOADABLE TOLERANCE for {code}: published at x{factor:g}; "
              f"validate_s2_polygons.py will report it")



# Repairing an invalid polygon is only safe when it does not move territory, so this measures the
# cost first and refuses above a threshold.
#
# WHY IT EXISTS. 44 of 703 published polygons failed is_valid, and an invalid geometry does not
# merely look untidy downstream -- IT HARD-FAILS sf's DEFAULT INTERSECTION. Measured against whep's
# committed snapshot: st_intersection over the 220 live non-aggregate polities of 2015 raises
# "Loop 82 edge 4 crosses loop 332 edge 2" with s2 enabled, which is R's default, and the single
# geometry responsible is FJI-1800-2025. So every downstream R consumer either turns s2 off or
# cannot intersect the polity set at all. That is the real cost of leaving these unrepaired, and it
# is much worse than the cosmetic reading (see eduaguilera/whep#514).
#
# WHY IT IS CONDITIONAL. make_valid is not free everywhere. Measured across all 44:
#
#     repairable with area change <= 0.01%     32
#     repairable with area change <= 0.10%     42
#     total area moved if ALL repaired    12,955 km2
#     of which IRN-1800-1828 alone        12,845 km2   (0.737%)
#
# So 43 of 44 cost 110 km2 BETWEEN THEM, and one costs 12,845 on its own. PR 140 established that
# make_valid and buffer(0) disagree by exactly that amount on Qajar Iran, and that choosing between
# them is a territorial judgement rather than a default. This threshold repairs the 43 and leaves
# the 44th alone, which is the outcome that PR's reasoning asks for.
REPAIR_MAX_AREA_CHANGE = 0.005  # 0.5%: an order of magnitude above the 42, well below IRN's 0.737%

# SIMPLIFICATION IS A FILE-SIZE OPTIMISATION, AND IT WAS SILENTLY DELETING TERRITORY.
#
# `SimplifyPreserveTopology(0.01)` preserves topology, not area. 0.01 degrees is about 1.1 km,
# which is fine for a country and catastrophic for anything whose parts are smaller than that.
# Measured on 2026-08-10 over the 57 rows bound to a gadm-4.1-adm0 feature, published area
# against raw GADM:
#
#     VAT-1929-2025   0.527 ->   0.275 km2   0.521x   the Vatican, 48% deleted
#     MDV-1800-2025 299.684 -> 172.576 km2   0.576x   the Maldives, 1,192 islands
#     NRU-1888-2025  22.151 ->  17.261 km2   0.779x
#     MHL-1874-2025 300.283 -> 252.553 km2   0.841x
#     COK-1800-2025 283.023 -> 240.835 km2   0.851x
#     SYC-1903-2025 491.200 -> 423.039 km2   0.861x
#     TUV-1800-2025  41.726 ->  36.203 km2   0.868x
#
# 15 of the 57 lost more than 5%; two lost more than 25%. Every loser is small, archipelagic or
# both -- exactly the population issue 71 describes, where an archipelago "cannot declare a true
# area" because the declared figure is compared against a geometry that has had its small islands
# thinned away. The declared areas were not wrong; the geometry was.
#
# Nothing caught it because `validate_polygons` check A skips rows where BOTH the claimed and the
# measured area are under --min-km2 200, which is every one of the worst cases by construction.
#
# So simplification now carries an AREA BUDGET, the same shape as REPAIR_MAX_AREA_CHANGE above:
# try it, measure what it cost, and keep the original if it cost too much. A row that cannot be
# simplified cheaply is simply published unsimplified -- it is small, so the file-size argument
# for simplifying it was never worth much anyway.
SIMPLIFY_MAX_AREA_CHANGE = 0.02  # 2%: below every legitimate loss, above rounding on large rows

# THE TOLERANCE IS SCALED TO THE FEATURE, not applied or abandoned.
#
# The first version of this was all-or-nothing: simplify at 0.01, and if that costs more than the
# budget, publish the geometry untouched. Correct on area, expensive on disk -- 40 rows went
# unsimplified and the GeoPackage grew from 14.6 MB to 22.4 MB, +53%, on a binary that is
# committed and rebuilt constantly.
#
# The all-or-nothing framing was the mistake. A geometry that cannot survive 1.1 km of thinning
# usually survives 110 m of it perfectly well, and 110 m of thinning still removes most of the
# vertices. So walk DOWN a ladder and take the coarsest tolerance that stays inside the budget.
SIMPLIFY_LADDER = (1.0, 0.1, 0.01)  # multipliers on the requested tolerance

# THE LADDER ALSO HAS TO STAY s2-LOADABLE, not only inside the area budget.
#
# Douglas-Peucker can leave two non-adjacent edges of a ring touching to within one ULP.
# GEOS reads that as no intersection; s2 -- which R's `sf` uses by default -- rounds
# lon/lat onto unit vectors and reads it as a crossing, and then st_area() ABORTS. The
# s2 repair below (buffer(0), then a noding fallback) normally cleans it up, and
# validate_s2_polygons.py is the backstop. But repair is not guaranteed: ROW-1850-2025 at
# tolerance 0.01 produces a crossing that NEITHER repair can fix, and the same row at
# 0.001 is clean. It reached the committed file s2-broken-but-repairable for months and
# passed only because buffer(0) happened to succeed on that exact vertex set; changing
# RASI's components (issue 48) changed the union's vertex order and buffer(0) stopped
# working, which is how the fragility surfaced. Simplifying a 53-territory union is
# precisely where it should be expected.
#
# So a ladder step must ALSO produce something s2 can load, after repair, or the ladder
# walks down. The check runs on the step already accepted on area, so the common case
# costs one s2 load per row and nothing else. If no step is both cheap and loadable, the
# cheapest one is published anyway (unchanged behaviour) and named in the output --
# validate_s2_polygons then fails, which is the right place for a defect this build
# cannot resolve.
#
# The walk-down takes HALF-STEPS, and only when s2 forced it. The ladder's own steps are
# decades apart, and dropping a whole decade for a topological reason is expensive on a
# committed binary: ROW-1850-2025 at x1 is 1.1 MB of WKB, at x0.5 1.6 MB and at x0.1
# 4.8 MB, and x0.5 is already s2-clean. So a rejected step is retried at half its
# tolerance before the next decade. The half-steps are unreachable unless an s2 rejection
# happened, which keeps every other row's geometry bit-identical to what the decade ladder
# alone produced -- the point is to fix one row, not to re-simplify 746.
S2_REFINE_FACTOR = 0.5


def _s2_loadable(g, s2_check) -> bool:
    """Would this OGR geometry survive the s2 repair the write path applies below?"""
    if s2_check is None:
        return True
    try:
        return s2_check(bytes(g.ExportToWkb()))
    except Exception:      # a check that cannot run must not fail the build
        return True


def _simplify_if_cheap(g, tolerance: float, polity_code: str, simplifies: dict, s2_check=None):
    """Simplify at the coarsest ladder step that costs less than the budget and stays
    s2-loadable.

    Returns the geometry untouched if even the finest step is too expensive, which is the honest
    outcome: the feature's parts are smaller than anything we could thin them by.
    """
    before = g.GetArea()
    if before <= 0:
        return g
    worst = None
    cheapest = None            # first step inside the budget, s2-loadable or not
    steps = []
    for factor in SIMPLIFY_LADDER:
        steps.append((factor, False))
        steps.append((factor * S2_REFINE_FACTOR, True))
    s2_blocked = False
    for factor, s2_only in steps:
        if s2_only and not s2_blocked:
            continue
        s = g.SimplifyPreserveTopology(tolerance * factor)
        if s is None or s.IsEmpty():
            continue
        change = abs(before - s.GetArea()) / before
        if worst is None:
            worst = change
        if change <= SIMPLIFY_MAX_AREA_CHANGE:
            if cheapest is None:
                cheapest = (s, factor, change)
            if not _s2_loadable(s, s2_check):
                simplifies["s2_refined"].append((polity_code, factor))
                s2_blocked = True
                continue
            simplifies["done"] += 1
            if factor != 1.0:
                simplifies["reduced"].append((polity_code, factor, change))
            return s
    if cheapest is not None:
        s, factor, change = cheapest
        simplifies["done"] += 1
        simplifies["s2_unresolved"].append((polity_code, factor))
        if factor != 1.0:
            simplifies["reduced"].append((polity_code, factor, change))
        return s
    simplifies["kept"].append((polity_code, worst if worst is not None else 1.0))
    return g


def _repair_if_free(g, polity_code: str, repairs: dict):
    """Return a valid geometry if repairing costs almost no area, else the original unchanged."""
    if g.IsValid():
        return g
    fixed = g.MakeValid()
    if fixed is None or not fixed.IsValid():
        repairs["failed"].append(polity_code)
        return g
    before, after = g.GetArea(), fixed.GetArea()
    if before <= 0:
        repairs["failed"].append(polity_code)
        return g
    change = abs(after - before) / before
    if change > REPAIR_MAX_AREA_CHANGE:
        repairs["skipped"].append((polity_code, change))
        return g
    # MakeValid can return a GEOMETRY COLLECTION -- the repaired polygons plus stray lines or
    # points where a self-intersection collapsed -- and ogr.ForceToMultiPolygon does NOT reliably
    # flatten one. PR 178 shipped exactly that: GBR-1800-1921 and IND-1800-1886 were published as
    # GeometryCollection in a layer declared MultiPolygon, and nothing here noticed, because every
    # geometry gate in this repo reads areas or does containment and both work on a collection. It
    # surfaced only when validate_spherical_edges.py (PR 151) walked exterior rings and died on
    # `'GeometryCollection' object has no attribute 'exterior'`.
    #
    # Take the areal members explicitly, recursing through nested collections, and REFUSE the
    # repair if nothing polygonal survives rather than publishing a non-polygon.
    fixed = _polygonal_only(fixed)
    if fixed is None:
        repairs["failed"].append(polity_code)
        return g
    repairs["repaired"].append(polity_code)
    return fixed


def _polygonal_only(geom):
    """Flatten a MakeValid result to a MultiPolygon, discarding non-areal debris."""
    out = ogr.Geometry(ogr.wkbMultiPolygon)
    stack = [geom]
    while stack:
        g = stack.pop()
        t = ogr.GT_Flatten(g.GetGeometryType())
        if t == ogr.wkbPolygon:
            out.AddGeometry(g)
        elif t in (ogr.wkbMultiPolygon, ogr.wkbGeometryCollection):
            for i in range(g.GetGeometryCount()):
                stack.append(g.GetGeometryRef(i))
    return out if out.GetGeometryCount() else None


def write_csv(rows: list[dict[str, Any]], out_path: Path) -> None:
    import csv
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, lineterminator="\n")
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
    ap.add_argument(
        "--densify-tolerance",
        type=float,
        default=spherical_edges.DEFAULT_TOLERANCE_DEG,
        help="max angular gap in degrees, AFTER simplification, between an edge's "
             "planar line and the great circle a spherical consumer renders it as "
             "(0 to disable). Default 0.001 deg = 111 m; see "
             "scripts/spherical_edges.py for why the number is what it is.",
    )
    ap.add_argument(
        "--allow-fewer-geometries",
        action="store_true",
        help="permit writing a GeoPackage with fewer geometries than the existing "
             "one. Needed only when rows were legitimately superseded; without it "
             "a rebuild missing its polygon sources refuses rather than gutting "
             "the committed file.",
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help="do not write anything: rebuild the CSV in memory from the wiki and "
             "compare it against the committed data/final/polities_database.csv, "
             "exiting non-zero on any difference. Catches a wiki edit that was "
             "never propagated to the database. Needs no polygon sources, so it "
             "runs in CI where data/geodata is absent.",
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

    n_total = len(pages)
    for i, page in enumerate(pages, 1):
        if i % 50 == 0 or i == n_total:
            print(f"  [{i}/{n_total}] processing pages... ({n_assigned} polygons so far)")

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

    if args.check:
        # Compare the wiki-derived rows against the committed CSV without writing.
        # Only the CSV is checked: the GeoPackage needs the polygon sources under
        # data/geodata, which are gitignored, so it cannot be verified in CI.
        # `polygon_status` is load-bearing: validate_polygons.py keys off it
        # and the manifest builds `claims_polygon_status` from it, so a value
        # outside the documented vocabulary silently escapes both. Four legacy
        # values (`derived`, `missing`, `approximate`, `excluded`) sat on 21 rows
        # for exactly that reason — README said not to use them and the migration
        # was never done, leaving 11 rows with geometry outside the claims set.
        POLYGON_STATUS_VOCABULARY = {
            "assigned", "proxy", "estimate", "polygon_vintage_drift",
            "unassigned",
        }
        bad_status = sorted({
            (r["polity_code"], r["polygon_status"]) for r in rows
            if (r.get("polygon_status") or "").strip()
            and r["polygon_status"].strip() not in POLYGON_STATUS_VOCABULARY
        })
        if bad_status:
            print("--check: FAIL — polygon_status values outside the documented "
                  "vocabulary (see wiki/README.md, Page schema)")
            for code, st in bad_status[:10]:
                print(f"  {code}: {st!r}")
            print(f"\n  Allowed: {sorted(POLYGON_STATUS_VOCABULARY)}")
            return 1

        # THE SAME DISCIPLINE FOR polity_type, for the same reason (issue 31).
        # polygon_status sprawled to nine values, four of which no validator could see, and
        # the fix was to enforce a vocabulary here. polity_type had begun the same drift:
        # `statistical` was a VOCABULARY OF ONE -- SYL-1944-1953 alone -- beside 23 rows of
        # identical kind typed `aggregate`.
        #
        # It matters more than tidiness because polity_type BREAKS TIES in
        # matchlib.pick_by_year. A value nothing else uses is a value no ranking rule
        # reaches, so a row carrying it silently sits outside whatever ordering the others
        # obey. That is how "Malaysia" 1961 resolved to British North Borneo (issue 44).
        POLITY_TYPE_VOCABULARY = {
            "national", "colonial", "subnational", "aggregate",
            "territory", "city-territory", "disputed",
        }
        bad_type = sorted({
            (r["polity_code"], r["polity_type"]) for r in rows
            if (r.get("polity_type") or "").strip()
            and r["polity_type"].strip() not in POLITY_TYPE_VOCABULARY
        })
        if bad_type:
            print("--check: FAIL — polity_type values outside the documented vocabulary")
            for code, t in bad_type[:10]:
                print(f"  {code}: {t!r}")
            print(f"\n  Allowed: {sorted(POLITY_TYPE_VOCABULARY)}")
            print("  A one-off type is not merely untidy: polity_type breaks ties in the\n"
                  "  matcher, so a value nothing else uses is a value no ranking rule reaches.")
            return 1

        # No published column may carry the literal string "NA". It means
        # missing, and a second spelling of missing is how a consumer ends up
        # treating 79 absent ISO3 codes as present.
        na_text = [
            (r["polity_code"], c)
            for r in rows for c in CSV_COLUMNS
            if isinstance(r.get(c), str) and r[c].strip() == "NA"
        ]
        if na_text:
            print("--check: FAIL — the literal string \"NA\" reached published "
                  "columns; it must be empty")
            for code, col in na_text[:10]:
                print(f"  {code}.{col}")
            return 1

        import csv, io
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in CSV_COLUMNS})
        expected = buf.getvalue()
        actual = csv_path.read_text(encoding="utf-8") if csv_path.exists() else ""
        if expected == actual:
            # The CSV matching is not sufficient. The two published artifacts are
            # read by DIFFERENT consumers — the manifest is derived from the CSV,
            # while the WHEP R package reads the GeoPackage — so they must agree
            # on attributes or they contradict each other downstream. Geometry
            # cannot be verified here (the polygon sources are gitignored), but
            # attributes can, and attribute drift is what actually bit: retiring
            # GCO-1884-2025 reached the CSV while the GeoPackage kept saying
            # `draft`, so the manifest called the row dead and the file consumers
            # read called it live.
            mismatches = gpkg_attribute_mismatches(rows, gpkg_path)
            if mismatches:
                print("--check: FAIL — the GeoPackage's attributes disagree with "
                      "the wiki-derived rows")
                for code, field, have, want in mismatches[:10]:
                    print(f"  {code}.{field}: gpkg={have!r} expected={want!r}")
                if len(mismatches) > 10:
                    print(f"  ... and {len(mismatches) - 10} more")
                print("\n  Fix: re-run scripts/build_database.py (it syncs "
                      "attributes in place without touching geometries).")
                return 1
            print(f"--check: PASS — the committed CSV and the GeoPackage's "
                  f"attributes match the wiki "
                  f"({len(rows)} rows from {len(pages)} pages)")
            return 0
        exp_lines, act_lines = expected.splitlines(), actual.splitlines()
        print(f"--check: FAIL — the committed CSV does NOT match the wiki")
        print(f"  wiki-derived rows: {len(exp_lines)-1}, committed rows: {len(act_lines)-1}")
        exp_codes = {l.split(",")[0] for l in exp_lines[1:]}
        act_codes = {l.split(",")[0] for l in act_lines[1:]}
        for label, codes in (("only in the wiki", exp_codes - act_codes),
                             ("only in the CSV", act_codes - exp_codes)):
            if codes:
                print(f"  {label}: {', '.join(sorted(codes)[:12])}"
                      + (" ..." if len(codes) > 12 else ""))
        if exp_codes == act_codes:
            import difflib
            diff = list(difflib.unified_diff(act_lines, exp_lines,
                                             "committed", "wiki-derived", lineterm="", n=0))
            print("  same rows, differing content:")
            for line in diff[2:14]:
                print(f"    {line}")
        print("\n  Fix: run scripts/build_database.py and commit data/final/.")
        return 1

    print(f"Writing CSV ({len(rows)} rows)...")
    write_csv(rows, csv_path)
    print(f"Writing GeoPackage ({len(geometries)} geometries, "
          f"simplify={args.simplify_tolerance}, densify={args.densify_tolerance})...")
    write_gpkg(rows, geometries, gpkg_path, args.simplify_tolerance,
               densify_tolerance=args.densify_tolerance,
               allow_fewer=args.allow_fewer_geometries)
    print("Done writing outputs.")

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
