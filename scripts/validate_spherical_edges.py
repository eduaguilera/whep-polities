#!/usr/bin/env python3
"""Check that a planar straight border still renders as a straight border.

WHAT THIS CATCHES, AND WHY NOTHING ELSE COULD
---------------------------------------------
Every polygon source here is a planar GIS product. A straight treaty border is
drawn as two vertices and a planar viewer joins them with the straight line the
treaty describes. Consumers do not read it that way: `sf` uses s2 by default, any
geodesic area needs a spherical model, and under a spherical model the segment
between two vertices is a GREAT CIRCLE — which between two points at equal
latitude BULGES POLEWARD.

So the published 49th-parallel US/Canada border, stored as ONE segment 27.6
degrees of longitude wide, renders for the consumer as an arc reaching latitude
49.83: 0.83 degrees (92 km) into Canada, booking 12,327,587 ha of Canadian
prairie to the United States. Measured directly against the shipped data in
eduaguilera/whep#529, where the per-cell shares at latitude 49.25 — cells wholly
north of the treaty line, so the known answer is CAN = 1.0000 — come out USA =
1.0000 for eight consecutive cells.

**Not one existing check could see it, by construction.** USA + CAN = 1.0000 in
every cell: no overlap, no gap, total land conserved, re-aggregation exact,
planar area unchanged to the last bit. It is a clean MUTUAL DISPLACEMENT, and
every gate in this repository is either planar (so blind to it) or
conservation-based (so blind to it). Conservation checks cannot detect
misattribution — only non-conservation. That is the lesson this gate exists to
institutionalise.

TWO CAUSES, AND ONE OF THEM WAS OURS
------------------------------------
The issue attributes the sparse edge to CShapes 2.0. Half right, and the half
that is wrong matters, because it is the half this repository can fix at the
root:

  * CShapes 2.0 stores the 49th parallel DENSELY — 124 vertices, widest gap 1.95
    degrees. The 27.6-degree chord in the published GeoPackage was manufactured
    here, by `build_database.py`'s `SimplifyPreserveTopology(0.01)`.
    Douglas-Peucker measures deviation from the chord IN PLANAR DEGREES, and
    every one of those 124 vertices lies on the chord, so all 124 are deleted.
  * Cliopatria really does store it sparsely: its USA polygon carries the same
    27.64-degree chord in the RAW source, before this repository touches it.

Both are repaired by densifying AFTER simplification, which is what
`build_database.py` now does via `scripts/spherical_edges.py`.

WHAT THIS GATE ASSERTS
----------------------
1. GENERAL. For every edge of every polygon, the great circle that renders it
   stays within `--tolerance` of the planar line it was drawn as. Reports the
   total ground area displaced by the edges that fail, because that number is
   the only honest statement of how wrong per-country totals are.

2. KNOWN ANSWER. For the borders below the answer is known independently of the
   data, because the border IS a parallel of latitude: a run of vertices sitting
   at latitude 48.99 is a straight treaty line, not a coarse sample of a wiggly
   natural feature, so a rendering that reaches 49.83 is wrong by inspection. The
   assertion is therefore that the rendered latitude range does not exceed the
   range of the VERTICES defining it by more than the tolerance.

   Deliberately not asserted against the exact parallel: CShapes puts Egypt's
   22nd-parallel vertices at 22.0039 and the 49th-parallel ones at 48.9974, so an
   absolute test would fail on the source's own digitising offset — a real but
   separate and much smaller matter (~290 m) that densification neither causes nor
   can fix. The absolute rendered extent is PRINTED beside the treaty parallel and
   the first 0.5-degree cell centre on the far side, so the consumer-facing
   consequence is visible without being asserted.

   Cases are pinned by polity code and the gate FAILS if a code goes missing or
   matches no edge, so it cannot quietly stop checking.

Usage:
  python3 scripts/validate_spherical_edges.py [--tolerance 0.001]
"""
from __future__ import annotations

import argparse
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLITIES_GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")

sys.path.insert(0, os.path.join(REPO, "scripts"))

# Borders whose correct shape is known independently of the data, because the
# border IS a parallel of latitude. Each entry is (polity_code, parallel,
# (lon_min, lon_max), far_side_cell_centre, description). `far_side_cell_centre`
# is the centre latitude of the first 0.5-degree grid row lying wholly on the
# other side of the treaty line -- the row that came out 100% USA in
# eduaguilera/whep#529 when the known answer is 100% Canada. It is printed, not
# asserted, because the assertion is about the RENDERING and not about the grid.
#
# Both borders are ones the issue measured, and the same arc appears on both
# polities of a shared border: in the northern hemisphere the great circle bulges
# north, so the polity to the south gains exactly what the polity to the north
# loses. Listing both sides is the point -- it is what makes the mutual
# displacement visible instead of looking like one country's problem.
KNOWN_ANSWER_PARALLELS = (
    (
        "USA-1959-2025",
        49.0,
        (-123.0, -95.0),
        49.25,
        "the 49th parallel, from the Strait of Georgia to the Lake of the Woods",
    ),
    (
        "CAN-1948-2025",
        49.0,
        (-123.0, -95.0),
        49.25,
        "the 49th parallel, from the Strait of Georgia to the Lake of the Woods",
    ),
    (
        "EGY-1925-1967",
        22.0,
        (24.0, 37.0),
        22.25,
        "the 22nd parallel, Egypt's southern administrative boundary",
    ),
)

# How close to the parallel an edge's endpoints must sit to count as part of that
# border. Wide enough to survive a 0.01-degree simplification, narrow enough that
# a coastline running near the same latitude is not swept in.
PARALLEL_BAND_DEG = 0.05

# One degree of arc on the s2 sphere, in km. Only used to print metres beside
# degrees, so a reader does not have to convert in their head.
KM_PER_DEGREE = 6371.010 * 3.141592653589793 / 180.0


def iter_rings(geom):
    """Every exterior and interior ring of a (multi)polygon, as coordinate arrays."""
    import numpy as np

    if geom is None or geom.is_empty:
        return
    parts = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    for part in parts:
        yield np.asarray(part.exterior.coords, dtype=float)[:, :2]
        for hole in part.interiors:
            yield np.asarray(hole.coords, dtype=float)[:, :2]


def scan_general(frame, tolerance, spherical_edges):
    """Edges whose great circle strays further than `tolerance` from their line."""
    import numpy as np

    failures = []
    vertices = 0
    for _, row in frame.iterrows():
        for coords in iter_rings(row.geometry):
            vertices += len(coords)
            deviation = spherical_edges.path_deviations_deg(coords)
            for i in np.where(deviation > tolerance)[0]:
                displaced = spherical_edges.edge_displaced_area_m2(
                    coords[i, 0], coords[i, 1], coords[i + 1, 0], coords[i + 1, 1], 401
                )
                failures.append(
                    {
                        "polity_code": row["polity_code"],
                        "source": row["polygon_source"],
                        "lon1": coords[i, 0],
                        "lat1": coords[i, 1],
                        "lon2": coords[i + 1, 0],
                        "lat2": coords[i + 1, 1],
                        "deviation_deg": float(deviation[i]),
                        "displaced_ha": displaced / 1e4,
                    }
                )
    return failures, vertices


def scan_known_answer(frame, tolerance, spherical_edges):
    """How far each pinned treaty border's rendering leaves its own vertices."""
    import numpy as np

    results = []
    for code, parallel, window, cell_centre, description in KNOWN_ANSWER_PARALLELS:
        lon_min, lon_max = window
        rows = frame[frame["polity_code"] == code]
        base = {
            "polity_code": code,
            "parallel": parallel,
            "cell_centre": cell_centre,
            "description": description,
        }
        if rows.empty:
            results.append({**base, "missing": True})
            continue
        worst = None
        edges = 0
        for coords in iter_rings(rows.iloc[0].geometry):
            on_band = np.abs(coords[:, 1] - parallel) <= PARALLEL_BAND_DEG
            in_window = (coords[:, 0] >= lon_min) & (coords[:, 0] <= lon_max)
            keep = on_band & in_window
            for i in np.where(keep[:-1] & keep[1:])[0]:
                edges += 1
                lats = spherical_edges.rendered_latitudes(
                    coords[i, 0], coords[i, 1], coords[i + 1, 0], coords[i + 1, 1]
                )
                vertex_hi = max(coords[i, 1], coords[i + 1, 1])
                vertex_lo = min(coords[i, 1], coords[i + 1, 1])
                excursion = max(
                    float(lats.max()) - vertex_hi, vertex_lo - float(lats.min())
                )
                if worst is None or excursion > worst[0]:
                    worst = (excursion, float(lats.max()), float(lats.min()))
        results.append(
            {
                **base,
                "missing": False,
                "edges": edges,
                "excursion_deg": None if worst is None else worst[0],
                "rendered_max_lat": None if worst is None else worst[1],
                "rendered_min_lat": None if worst is None else worst[2],
            }
        )
    return results


def main() -> int:
    import spherical_edges

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--tolerance",
        type=float,
        default=spherical_edges.DEFAULT_TOLERANCE_DEG,
        help="max angular gap in degrees between the planar line and its great "
        "circle (default: the value build_database.py densifies to)",
    )
    args = ap.parse_args()

    try:
        import geopandas as gpd
    except ImportError as exc:
        print(f"FAIL: geopandas unavailable ({exc})")
        return 2
    if not os.path.exists(POLITIES_GPKG):
        print(f"FAIL: {POLITIES_GPKG} missing; run scripts/build_database.py first")
        return 2

    frame = gpd.read_file(POLITIES_GPKG)
    frame = frame[~frame.geometry.isna() & ~frame.geometry.is_empty]

    failures, vertices = scan_general(frame, args.tolerance, spherical_edges)
    tol_km = args.tolerance * KM_PER_DEGREE
    print(f"polygons scanned: {len(frame)}   vertices: {vertices:,}")
    print(f"tolerance: {args.tolerance:g} deg of arc ({tol_km * 1000:.0f} m)")
    print(f"edges whose great circle strays further than that: {len(failures)}")

    problems = []
    if failures:
        total = sum(f["displaced_ha"] for f in failures)
        distinct = {}
        for f in failures:
            key = tuple(
                sorted(
                    [
                        (round(f["lon1"], 6), round(f["lat1"], 6)),
                        (round(f["lon2"], 6), round(f["lat2"], 6)),
                    ]
                )
            )
            distinct.setdefault(key, f)
        distinct_total = sum(f["displaced_ha"] for f in distinct.values())
        print(
            f"distinct border edges behind them: {len(distinct)}, displacing "
            f"{distinct_total:,.1f} ha = {distinct_total / 100:,.0f} km2 of ground"
        )
        print(
            f"summed over every polity period that shares one: {total:,.1f} ha "
            f"= {total / 100:,.0f} km2 of polity area\n"
        )
        worst = sorted(distinct.values(), key=lambda f: -f["displaced_ha"])[:12]
        for f in worst:
            print(
                f"   {f['displaced_ha']:>14,.1f} ha  {f['deviation_deg']:>8.4f} deg  "
                f"{f['polity_code']:<18} {f['source']:<16} "
                f"({f['lon1']:.4f}, {f['lat1']:.4f}) -> "
                f"({f['lon2']:.4f}, {f['lat2']:.4f})"
            )
        if len(distinct) > len(worst):
            print(f"   ... and {len(distinct) - len(worst)} more distinct edges")
        problems.append(
            f"{len(distinct)} distinct edge(s), on {len(failures)} polity period(s), "
            f"render as a great circle straying further than {args.tolerance:g} deg "
            f"from the planar line they were drawn as, misattributing "
            f"{distinct_total:,.0f} ha of ground. Densify them: build_database.py "
            f"does this AFTER simplification via scripts/spherical_edges.py, so a "
            f"failure here means either the build did not run or something wrote "
            f"the GeoPackage another way."
        )

    print("\nknown-answer borders (the border IS a parallel, so its shape is not in doubt):")
    for r in scan_known_answer(frame, args.tolerance, spherical_edges):
        if r["missing"]:
            print(f"   MISSING  {r['polity_code']}  ({r['description']})")
            problems.append(
                f"known-answer case names {r['polity_code']}, which is not in the "
                f"database — the case is no longer checking anything. Repoint it at "
                f"the polity that now carries {r['description']}, do not delete it."
            )
            continue
        if r["excursion_deg"] is None:
            print(f"   NO EDGES {r['polity_code']}  ({r['description']})")
            problems.append(
                f"known-answer case {r['polity_code']} matched no edge within "
                f"{PARALLEL_BAND_DEG} deg of latitude {r['parallel']:g}, so it is "
                f"inert. Its polygon binding or the band has changed."
            )
            continue
        excursion_km = r["excursion_deg"] * KM_PER_DEGREE
        verdict = "ok" if r["excursion_deg"] <= args.tolerance else "LEAVES LINE"
        reaches = (
            "past"
            if r["rendered_max_lat"] >= r["cell_centre"] > r["parallel"]
            or r["rendered_min_lat"] <= r["cell_centre"] < r["parallel"]
            else "short of"
        )
        print(
            f"   {verdict:<12} {r['polity_code']:<18} {r['edges']:>4} edge(s) at "
            f"latitude {r['parallel']:g}; rendered extent "
            f"{r['rendered_min_lat']:.5f}..{r['rendered_max_lat']:.5f}, "
            f"{r['excursion_deg'] * 1000:+.3f} milli-deg ({excursion_km * 1000:+.0f} m) "
            f"beyond its own vertices; {reaches} the {r['cell_centre']:g} cell row"
        )
        if r["excursion_deg"] > args.tolerance:
            problems.append(
                f"{r['polity_code']}'s rendering of {r['description']} leaves the "
                f"line its own vertices describe by {r['excursion_deg']:.5f} deg "
                f"({excursion_km:.1f} km), reaching latitude "
                f"{r['rendered_max_lat']:.5f}. Ground on the far side is booked to "
                f"the wrong polity, and no conservation check can see it because "
                f"the neighbour loses exactly what this polity gains."
            )

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print(
        "\nPASS: every edge renders within tolerance of the line it was drawn as, "
        "and both treaty parallels stay put"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
