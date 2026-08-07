#!/usr/bin/env python3
"""Make every published polygon buildable on the sphere, not just in the plane.

WHY THIS EXISTS. Ten of the 703 polygons in data/final/polities_database.gpkg cannot
be loaded by s2geometry at all, so every consumer that asks a spherical question about
them -- a geodesic area, an intersection with a grid cell -- aborts instead of
answering. `make_valid()` leaves three of the ten still unloadable, and two of those
three are GEOS-VALID to begin with, so it has nothing to repair and returns them
unchanged. That is why the obvious fix does not work. Measured on the committed
database before this script existed:

    DEU-1871-1919   Loop 3 is not valid: Edge 0 crosses edge 2      GEOS-valid
    FID-1887-1954   Loop 10 edge 0 has duplicate near loop 11 edge 3
    FJI-1800-2025   Loop 82 edge 4 crosses loop 332 edge 2
    FRA-1800-1871   Loop 1 edge 203 crosses loop 6 edge 1
    FRA-1800-1919   Loop 1 edge 203 crosses loop 6 edge 1
    GBR-1800-1921   Loop 15 edge 340 has duplicate near loop 17 edge 7
    IND-1800-1886   Loop 5 edge 440 crosses loop 13 edge 2
    IRN-1800-1828   Loop 1 edge 7 has duplicate near loop 2 edge 3
    PAP-1800-1870   Loop 2 edge 0 has duplicate near loop 3 edge 2
    SNW-1814-1905   Loop 0 is not valid: Edge 524 crosses edge 528   GEOS-valid

FJI-1800-2025 is the operationally important one: it is LIVE in the present day and
FAOSTAT area 66 routes to it across 203,519 observed rows, so its territory is absent
from anything keyed on the polity polygon rather than reported missing.

WHY GEOS AND S2 DISAGREE, measured rather than assumed. Both GEOS-valid rows carry a
DEGENERATE PINCH: two non-adjacent edges of one ring that touch to within
floating-point representation.

    DEU-1871-1919   ring 3, edges 0 and 2      3.576e-15 deg = 4.0e-10 m apart
    SNW-1814-1905   ring 0, edges 1495 & 1500  3.603e-15 deg = 4.0e-10 m apart

GEOS decides crossing in the plane from the lon/lat doubles it was given, and at that
separation -- about one ULP -- it correctly reports no intersection. s2 first converts
each lon/lat to a unit vector in R3, and that conversion ROUNDS: after it the two
edges cross. So the disagreement is not about geodesics versus straight lines, and it
is not latitude-dependent (the same ring fails at the equator). It is about a pinch
narrow enough that one representation of it self-intersects and the other does not.
Neither engine is wrong; the geometry is degenerate.

Note that s2's edge numbers are its own: it reports SNW-1814-1905 as
"Edge 524 crosses edge 528" because it renumbers after dropping duplicate vertices,
while the pinch is at ring positions 1495 and 1500. Do not go looking at vertex 524.

The remaining eight rows fail for planar reasons GEOS does see -- overlapping parts,
duplicated edges between rings, nested shells.

TWO REPAIRS, AND THE CHOICE BETWEEN THEM IS A DECISION, NOT A DEFAULT.
validate_polygon_validity.py declined to repair the 41 GEOS-invalid polygons for exactly
this reason, and it is right: buffer(0) and make_valid disagree by 12,845 km2 on Qajar
Iran, 0.7% of the country, because a self-overlapping ring can be read as one region
counted once or as two rings whose overlap is spurious. Nothing in the geometry settles
which. So both methods are implemented and selectable, and the default is the one that
moves NOTHING:

  `preserve` (default)  buffer(0), falling back to `node` where buffer(0) leaves the
                        polygon still unloadable. Measured in ESRI:54034 it reproduces
                        the broken polygon's own published area to 0.00 km2 on six of
                        the ten and to under 21 km2 on all ten -- so it makes every
                        polygon measurable while leaving the largest contested area,
                        Iran's 12,845 km2, exactly where the database already had it.
                        buffer(0) suffices for seven of the ten; the three it does not
                        fix (DEU-1871-1919, FJI-1800-2025, SNW-1814-1905) have a method
                        spread of 0 km2, so no decision rides on falling back for them.
                        Full ESRI:54034 deltas against the unrepaired geometry:
                        IND -20.57, FJI -0.33, SNW +0.06, the other seven 0.00.

  `node`                make_valid -> set_precision(1e-9) -> make_valid, always. The
                        middle step is what reaches the pinches, and not because 1e-9
                        degrees (0.1 mm) is a meaningful tolerance: GEOS implements
                        set_precision as full snap-rounding, which re-nodes every
                        intersection and drops components that collapse, so a pinch
                        4e-10 m wide snaps onto a shared node and stops being one. This
                        is the method that treats a self-overlap as double-counting and
                        removes it.

Where the two differ, in ESRI:54034 km2:

    IRN-1800-1828   preserve 1,743,638   node 1,730,793   spread 12,845  (-0.74%)
    FID-1887-1954   preserve   699,133   node   699,076   spread     57
    PAP-1800-1870   preserve    39,269   node    39,222   spread     47
    IND-1800-1886   preserve 4,209,888   node 4,209,848   spread     40
    the other six   spread 0

Four rows carry a real choice and the largest is Iran's. It is the repo owner's call, not
this script's: pass --method node to take it.

The repair is applied ONLY to geometries s2 cannot load. Both methods rewrite the
coordinates they touch, so running either over all 703 would change all 703; leaving the
693 healthy ones alone keeps the change measurable and the artifact diff honest.

Usage:
  python3 scripts/repair_s2_polygons.py                  # preserve, and write
  python3 scripts/repair_s2_polygons.py --dry-run        # report, write nothing
  python3 scripts/repair_s2_polygons.py --method node    # the alternative

The gate that keeps it repaired is scripts/validate_s2_polygons.py, which runs in CI.
build_database.py calls repair_geometry() on write, so a rebuild from the raw sources
produces an already-repaired GeoPackage and this script has nothing to do.
"""
from __future__ import annotations

import argparse
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLITIES_GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")

# s2geometry's own earth radius, which is also what R's s2 package and therefore
# sf::st_area() use, so an area printed here matches the number a WHEP consumer sees.
EARTH_RADIUS_METERS = 6371010.0

# The grid for the snap-rounding pass, in degrees. Deliberately far below the
# precision of every source (CShapes Europe quantises to 0.02 degrees, GADM 4.1 to
# about 1e-6): the pass earns its place by RE-NODING, not by coarsening. 1e-9 degrees
# is 0.1 mm at the equator, and the pinches it has to close are 4e-10 m wide.
SNAP_GRID_DEGREES = 1e-9


def s2_failure(geom) -> str | None:
    """s2's complaint about `geom`, or None if s2 can load it and measure it.

    Uses spherely, which wraps the same s2geometry library that R's s2 package wraps,
    so the message returned here is character-for-character the message an sf user
    sees from st_area(). That is the point of using it rather than reimplementing the
    spherical predicates: a gate that approximates s2 can pass while the consumer
    still aborts.
    """
    import shapely
    import spherely

    if geom is None or geom.is_empty:
        return None
    try:
        spherely.area(spherely.from_wkb(shapely.to_wkb(geom)))
    except Exception as exc:  # noqa: BLE001 - spherely raises plain RuntimeError
        return str(exc).strip()
    return None


def geodesic_area_km2(geom) -> float:
    """Area on the sphere in km2, by the same route sf::st_area() takes."""
    import shapely
    import spherely

    m2 = spherely.area(
        spherely.from_wkb(shapely.to_wkb(geom)), radius=EARTH_RADIUS_METERS
    )
    return float(m2) / 1e6


METHODS = ("preserve", "node")
DEFAULT_METHOD = "preserve"


def repair_geometry(geom, method: str = DEFAULT_METHOD):
    """Return a geometry s2 can load, or the input unchanged if it already could.

    `method` selects between the two repairs that disagree about a self-overlapping
    ring -- see the module docstring. The default preserves the polygon's published
    area; `node` removes the overlap. Neither is a fallback for the other: `preserve`
    falls back to `node` only where buffer(0) leaves the polygon still unloadable, and
    on those three rows the two methods agree to 0 km2 anyway.
    """
    import shapely

    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}, got {method!r}")
    if s2_failure(geom) is None:
        return geom
    if method == "preserve":
        preserved = _as_multipolygon(geom.buffer(0))
        if s2_failure(preserved) is None:
            return preserved
    noded = shapely.make_valid(
        shapely.set_precision(shapely.make_valid(geom), SNAP_GRID_DEGREES)
    )
    return _as_multipolygon(noded)


def _as_multipolygon(geom):
    """Keep the polygonal parts of a repaired geometry, as a MultiPolygon.

    The `node` method's make_valid returns a GeometryCollection when a defect resolves
    into a polygon plus a dangling edge -- GBR-1800-1921 yields MultiPolygon +
    LineString, IND-1800-1886 MultiPolygon + MultiLineString, both from an overlapping
    part being noded away. buffer(0) does not do this, so under the default method only
    the three fallback rows can reach the branch below; it still has to exist, because
    --method node reaches it for two more.
    The lines carry no area, but the layer this is written back to is declared
    MULTIPOLYGON and GDAL warns that a GeometryCollection in it is not
    GeoPackage-conformant. sf then reads a mixed-type layer, which is how a
    GEOMETRYCOLLECTION reaches the WHEP package's embedded copy and breaks a consumer
    that assumes polygons. So the residue is dropped here, at the one place that
    creates it.
    """
    import shapely

    if geom.geom_type == "MultiPolygon":
        return geom
    if geom.geom_type == "Polygon":
        return shapely.multipolygons([geom])
    parts = [
        p
        for p in shapely.get_parts(geom)
        if p.geom_type in ("Polygon", "MultiPolygon") and not p.is_empty
    ]
    polygons: list = []
    for part in parts:
        polygons.extend(
            shapely.get_parts(part) if part.geom_type == "MultiPolygon" else [part]
        )
    return shapely.multipolygons(polygons)


def repair_wkb(wkb: bytes, method: str = DEFAULT_METHOD) -> bytes | None:
    """Repair a WKB blob, or None when it needed no repair.

    The seam build_database.py uses, so the builder needs no shapely import of its
    own and the two paths cannot drift apart.
    """
    import shapely

    geom = shapely.from_wkb(wkb)
    if s2_failure(geom) is None:
        return None
    return shapely.to_wkb(repair_geometry(geom, method=method))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="report which geometries would change and by how much, write nothing",
    )
    ap.add_argument(
        "--method",
        choices=METHODS,
        default=DEFAULT_METHOD,
        help="how to resolve a self-overlapping ring: `preserve` (default) keeps the "
             "polygon's published area, `node` treats the overlap as double-counting "
             "and removes it. They differ by 12,845 km2 on IRN-1800-1828 and by 0 on "
             "six of the ten, so this is a per-row decision and not a tuning knob.",
    )
    args = ap.parse_args()

    try:
        import geopandas as gpd
        import shapely
        import spherely  # noqa: F401 - imported for the availability check
        from osgeo import ogr
    except ImportError as exc:
        print(f"FAIL: geopandas/shapely/spherely/osgeo unavailable ({exc})")
        print("  pip install -r requirements-ci.txt  (osgeo comes from python3-gdal)")
        return 2
    ogr.UseExceptions()
    if not os.path.exists(POLITIES_GPKG):
        print(f"FAIL: {POLITIES_GPKG} missing; run scripts/build_database.py first")
        return 2

    def planar_km2(geom) -> float:
        # ESRI:54034 to match validate_polygon_validity.py, so the method spreads
        # printed here are comparable with the ones recorded there.
        return (
            gpd.GeoSeries([geom], crs="EPSG:4326").to_crs("ESRI:54034").area.iloc[0]
            / 1e6
        )

    # Updated feature by feature through OGR rather than rewritten with
    # GeoDataFrame.to_file(), which would re-derive the layer schema and the field
    # types. build_database.py compares the GeoPackage's attributes against the wiki
    # and syncs them in place, so a schema this script invented would show up there as
    # a spurious mismatch. Only the geometry column of the affected rows is touched.
    ds = ogr.Open(POLITIES_GPKG, update=1)
    lyr = ds.GetLayer(0)
    total = lyr.GetFeatureCount()

    changed: list[tuple[str, str, float, float, float]] = []
    unfixed: list[tuple[str, str]] = []
    lyr.ResetReading()
    for feat in lyr:
        ogr_geom = feat.GetGeometryRef()
        if ogr_geom is None:
            continue
        code = feat.GetField("polity_code")
        geom = shapely.from_wkb(bytes(ogr_geom.ExportToWkb()))
        reason = s2_failure(geom)
        if reason is None:
            continue
        repaired = repair_geometry(geom, method=args.method)
        still = s2_failure(repaired)
        if still is not None:
            unfixed.append((code, still))
            continue
        other = "node" if args.method == "preserve" else "preserve"
        alt = repair_geometry(geom, method=other)
        spread = (
            abs(planar_km2(repaired) - planar_km2(alt))
            if s2_failure(alt) is None
            else 0.0
        )
        changed.append(
            (code, reason, planar_km2(geom), planar_km2(repaired), spread)
        )
        if not args.dry_run:
            feat.SetGeometry(ogr.CreateGeometryFromWkb(shapely.to_wkb(repaired)))
            lyr.SetFeature(feat)

    print(f"features in {os.path.basename(POLITIES_GPKG)}: {total}")
    print(f"method: {args.method}   s2 could not load: "
          f"{len(changed) + len(unfixed)}")
    for code, reason, before, after, spread in changed:
        delta = 100.0 * (after - before) / before if before else float("nan")
        print(
            f"  REPAIRED {code:<16} {before:>12,.2f} -> {after:>12,.2f} km2 "
            f"({delta:+.4f}%)  other method would differ by {spread:>9,.0f} km2"
            f"  was: {reason}"
        )
    for code, reason in unfixed:
        print(f"  STILL BROKEN {code:<16} {reason}")

    # An in-place SQLite update leaves the freed pages behind -- 48 KB on the first run
    # here -- so the committed artifact would grow a little every time this ran. VACUUM
    # after the writes, not instead of them.
    if changed and not args.dry_run:
        ds.ExecuteSQL("VACUUM")
    ds = None

    if not changed:
        print("\nNothing to repair.")
        return 1 if unfixed else 0
    if args.dry_run:
        print(f"\n--dry-run: {len(changed)} geometry(ies) NOT written")
        return 0
    print(f"\nWrote {POLITIES_GPKG} ({len(changed)} geometry(ies) repaired)")
    if unfixed:
        print("Some geometries remain unloadable; see validate_s2_polygons.py")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
