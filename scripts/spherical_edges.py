#!/usr/bin/env python3
"""
Planar polygon edges, read as spherical ones: measure and repair the gap.

WHY THIS EXISTS
---------------
Every polygon source in this repository is a PLANAR GIS product stored in
EPSG:4326. A straight border — the 49th parallel, the 22nd parallel — is drawn
by clicking two points, and a planar viewer joins them with a straight line in
lon/lat space, which is the line the treaty describes.

Consumers do not read it that way. `sf` uses s2 by default and any geodesic area
needs a spherical model, and under a spherical model the segment between two
vertices is a GREAT CIRCLE. A great circle between two points at equal latitude
BULGES POLEWARD between them. So a two-vertex 49th-parallel border renders, for
the consumer, as an arc reaching 0.83 degrees into Canada, booking 12.33 Mha of
Canadian prairie to the United States (eduaguilera/whep#529).

Nothing catches that by construction: the two polities still tile the ground
exactly, so USA + CAN = 1.0000 in every cell, no overlap, no gap, total land
conserved, re-aggregation exact. It is a clean MUTUAL DISPLACEMENT, and
conservation checks cannot see misattribution — only non-conservation.

THE REPAIR
----------
Densify: insert vertices along the intended planar line so each resulting
sub-segment's great circle hugs it within a tolerance. Planar-side this is a
no-op by construction (the inserted points lie exactly ON the existing segment,
so no ring can gain a self-intersection); spherical-side it is what makes the
rendered border follow the parallel.

`sf::st_segmentize()` is NOT this operation. On longlat input it densifies along
the EXISTING great circle and is therefore area-preserving — measured own-area
move at 0.01 degrees: exactly 0 for both USA and Canada. What is needed is
densification along the planar line, which `sf` does not offer on longlat.

WHERE IT BELONGS
----------------
After simplification, not before. `build_database.py` runs
`SimplifyPreserveTopology(0.01)` on every polygon, and Douglas-Peucker measures
deviation from the chord IN PLANAR DEGREES — so densified vertices, which lie
exactly on the chord, are the first thing it deletes. Worse, DP is how the worst
case in the database was CREATED: CShapes 2.0 stores the 49th parallel with 124
vertices, 1.95 degrees apart at the widest, and the 0.01-degree simplification
collapses all 124 into one 27.6-degree chord. See `validate_spherical_edges.py`
for the gate and the measurement.

TOLERANCE, AND WHY IT IS 0.001 AND NOT 0.01
-------------------------------------------
`DEFAULT_TOLERANCE_DEG` is the maximum angular distance, in degrees of arc,
between the intended planar line and the great circle that renders it.

The obvious choice is 0.01 degrees, matching the pipeline's own
`--simplify-tolerance`: the build already accepts moving a border 0.01 degrees
planar-side, so why demand more of the spherical rendering? Measured, and
rejected, because the two are not the same KIND of error. Douglas-Peucker error is
a local wobble on a densely digitised line, alternating sign, and its area effect
largely cancels. The great-circle bulge is systematic, one-sided, and integrated
over tens of degrees of border.

Measured on the 20 distinct edges the published database gets wrong, which
displace 27,595,277 ha between them, against the whole-database cost:

    tolerance   residual displaced   vertices           planar-invalid
    0.01        642,937 ha (2.33%)   +140    (+0.02%)   41 (unchanged)
    0.001        88,986 ha (0.32%)   +1,912  (+0.25%)   41 (unchanged)
    0.0001        9,813 ha (0.04%)   +41,231 (+5.33%)   42 (one more)

0.001 is the choice. 0.01 leaves two thirds of a million hectares misattributed
for a saving of 1,772 vertices, which is no saving at all. 0.0001 buys a further
79,000 ha at 20x the vertices AND takes one polygon from planar-valid to
planar-invalid — densifying a near-degenerate sliver is how that happens, and this
database already carries 41 planar-invalid polygons without needing a 42nd.

0.001 degrees of arc is 111 m: 0.2% of the 0.5-degree (~55 km) cell edge every
downstream consumer allocates on, so it cannot move a cell fraction by more than
a fifth of a percent. Exposed as `--densify-tolerance` on `build_database.py` and
`--tolerance` on the gate, so the choice stays auditable and reversible rather
than baked in.

Angular distances are converted with the s2 Earth radius (6371.01 km), because
that is what `sf` uses for `st_area()` under s2 and therefore what a consumer's
numbers will be denominated in.
"""

from __future__ import annotations

import math

import numpy as np

# s2's S2Earth::RadiusMeters(). Used so displaced areas here are directly
# comparable with what sf::st_area() reports for the same geometry.
S2_EARTH_RADIUS_M = 6371010.0

# 111 m of arc. See "TOLERANCE, AND WHY IT IS 0.001 AND NOT 0.01" above: the
# alternative was measured, not assumed.
DEFAULT_TOLERANCE_DEG = 0.001

# A segment wider than this in longitude is an antimeridian wrap, not a long
# edge: interpolating it linearly would drag the vertex the long way round the
# globe. Three polygons in this database are already s2-invalid and unrepairable
# for antimeridian reasons (eduaguilera/whep#515), so these are left untouched
# and counted rather than silently mangled.
ANTIMERIDIAN_DLON_DEG = 180.0


def unit_vectors(lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    """Unit vectors on the sphere for arrays of degrees, shape (n, 3)."""
    lo = np.radians(np.asarray(lon, dtype=float))
    la = np.radians(np.asarray(lat, dtype=float))
    cos_la = np.cos(la)
    return np.stack([cos_la * np.cos(lo), cos_la * np.sin(lo), np.sin(la)], axis=-1)


def edge_deviation_deg(
    lon1: float, lat1: float, lon2: float, lat2: float, samples: int = 65
) -> float:
    """Max angular gap, in degrees, between the planar line and its great circle.

    The intended line is the linear interpolation in (lon, lat) — what a planar
    GIS draws and what the source author saw. The rendered line is the great
    circle through the same endpoints. The gap is the angular distance from each
    sampled point of the intended line to the great-circle PLANE, which is the
    perpendicular distance to the rendered edge.
    """
    return float(path_deviations_deg([(lon1, lat1), (lon2, lat2)], samples=samples)[0])


def path_deviations_deg(
    coords: np.ndarray, samples: int = 17, chunk: int = 200_000
) -> np.ndarray:
    """`edge_deviation_deg` for every consecutive pair of an (n, 2) path.

    Vectorised because the gate walks every one of the database's ~773,000 edges:
    the scalar form takes minutes, this takes seconds. Antimeridian
    wraps return 0 — they are not long edges and must not be interpolated.

    DEGENERATE EDGES ARE CLAMPED, and that is not defensive decoration. The
    great-circle normal is a cross product, so for two coincident vertices it is
    pure floating-point residue (~1e-16) pointing in an arbitrary direction, and
    normalising it yields a deviation of tens of degrees for an edge of zero
    length. Unclamped, the first run of this on the published database reported a
    46-degree deviation for a repeated vertex in KAZ-1991-2025 and the densifier
    then "repaired" it by inserting nine more copies of the same point, taking one
    polygon from planar-valid to planar-invalid. Both paths therefore clamp the
    deviation to the edge's own angular length, which no honest deviation can
    exceed.
    """
    coords = np.asarray(coords, dtype=float)
    if len(coords) < 2:
        return np.zeros(0)
    lon1, lat1 = coords[:-1, 0], coords[:-1, 1]
    lon2, lat2 = coords[1:, 0], coords[1:, 1]
    out = np.zeros(len(lon1))
    t = np.linspace(0.0, 1.0, samples)[None, :]
    for lo in range(0, len(lon1), chunk):
        hi = min(lo + chunk, len(lon1))
        s = slice(lo, hi)
        a = unit_vectors(lon1[s], lat1[s])
        b = unit_vectors(lon2[s], lat2[s])
        normal = np.cross(a, b)
        norm = np.linalg.norm(normal, axis=1, keepdims=True)
        normal = np.divide(normal, norm, out=np.zeros_like(normal), where=norm > 0)
        lon = lon1[s, None] + (lon2[s] - lon1[s])[:, None] * t
        lat = lat1[s, None] + (lat2[s] - lat1[s])[:, None] * t
        pts = unit_vectors(lon, lat)
        dot = np.einsum("ijk,ik->ij", pts, normal)
        dev = np.degrees(np.abs(np.arcsin(np.clip(dot, -1.0, 1.0)))).max(axis=1)
        span = np.degrees(
            np.arctan2(norm[:, 0], np.clip(np.einsum("ij,ij->i", a, b), -1.0, 1.0))
        )
        dev = np.minimum(dev, span)
        dev[np.abs(lon2[s] - lon1[s]) >= ANTIMERIDIAN_DLON_DEG] = 0.0
        out[s] = dev
    return out


def edge_displaced_area_m2(
    lon1: float, lat1: float, lon2: float, lat2: float, samples: int = 2001
) -> float:
    """Ground area the great circle takes from one side and gives to the other.

    The area of the lune between the intended planar line and the great circle
    that renders it, on the s2 sphere. This is the quantity a per-country total
    is wrong by: it is not lost, it is booked to the neighbour.
    """
    t = np.linspace(0.0, 1.0, samples)
    lon = lon1 + (lon2 - lon1) * t
    lat = lat1 + (lat2 - lat1) * t
    return _spherical_polygon_area_m2(lon, lat)


def rendered_latitudes(
    lon1: float, lat1: float, lon2: float, lat2: float, samples: int = 257
) -> np.ndarray:
    """Latitudes the great circle actually passes through between two vertices.

    This is what the consumer sees, as opposed to the latitudes the planar line
    passes through. For a two-vertex 49th-parallel border it reaches 49.83.
    """
    a, b = unit_vectors([lon1, lon2], [lat1, lat2])
    theta = math.atan2(float(np.linalg.norm(np.cross(a, b))), float(np.dot(a, b)))
    if theta == 0.0:
        return np.array([lat1])
    f = np.linspace(0.0, 1.0, samples)[:, None]
    pts = a * np.sin((1.0 - f) * theta) + b * np.sin(f * theta)
    pts = pts / np.linalg.norm(pts, axis=1, keepdims=True)
    return np.degrees(np.arcsin(np.clip(pts[:, 2], -1.0, 1.0)))


def _spherical_polygon_area_m2(lon: np.ndarray, lat: np.ndarray) -> float:
    """Area of the closed spherical polygon through these vertices, in m^2.

    L'Huilier is fiddly near-degenerate, so this sums the signed spherical
    excess of the triangles fanned from the first vertex, which is stable for
    the sliver shapes a lune is.
    """
    v = unit_vectors(lon, lat)
    total = 0.0
    origin = v[0]
    for i in range(1, len(v) - 1):
        total += _signed_triangle_excess(origin, v[i], v[i + 1])
    return abs(total) * S2_EARTH_RADIUS_M**2


def _signed_triangle_excess(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Signed spherical excess of triangle (a, b, c) via the Van Oosterom form."""
    num = float(np.dot(a, np.cross(b, c)))
    den = 1.0 + float(np.dot(a, b)) + float(np.dot(b, c)) + float(np.dot(c, a))
    return 2.0 * math.atan2(num, den)


def densify_edge(
    lon1: float,
    lat1: float,
    lon2: float,
    lat2: float,
    tolerance_deg: float = DEFAULT_TOLERANCE_DEG,
) -> list[tuple[float, float]]:
    """Intermediate vertices to insert between two endpoints, exclusive.

    Empty when the edge already renders within tolerance, which is the case for
    every densely digitised coastline — so this is a no-op on the overwhelming
    majority of the database and only touches deliberately straight borders.
    """
    if abs(lon2 - lon1) >= ANTIMERIDIAN_DLON_DEG:
        return []
    deviation = edge_deviation_deg(lon1, lat1, lon2, lat2)
    if deviation <= tolerance_deg:
        return []
    # Deviation falls off as the square of the sub-segment length, so k pieces
    # cut it by ~k^2. Start from that estimate and refine until it actually
    # holds, rather than trusting the asymptotic form near a pole.
    pieces = max(2, math.ceil(math.sqrt(deviation / tolerance_deg)))
    for _ in range(24):
        step_dev = edge_deviation_deg(
            lon1,
            lat1,
            lon1 + (lon2 - lon1) / pieces,
            lat1 + (lat2 - lat1) / pieces,
        )
        if step_dev <= tolerance_deg:
            break
        pieces *= 2
    t = np.linspace(0.0, 1.0, pieces + 1)[1:-1]
    return [
        (float(lon1 + (lon2 - lon1) * f), float(lat1 + (lat2 - lat1) * f)) for f in t
    ]


def densify_ring(
    coords: list[tuple[float, float]],
    tolerance_deg: float = DEFAULT_TOLERANCE_DEG,
) -> list[tuple[float, float]]:
    """Densify every edge of one ring. Returns the ring, closed as it came.

    Screens the whole ring with one vectorised deviation pass and only calls
    `densify_edge` on the edges that fail. Calling it per edge instead cost a
    numpy round-trip for each of the database's ~773,000 vertices, which is minutes
    of wall clock for the ~500 edges that actually need work.
    """
    arr = np.asarray(coords, dtype=float)[:, :2]
    if len(arr) < 2:
        return [(float(x), float(y)) for x, y in arr]
    over = set(np.where(path_deviations_deg(arr) > tolerance_deg)[0].tolist())
    if not over:
        return [(float(x), float(y)) for x, y in arr]
    out: list[tuple[float, float]] = [(float(arr[0, 0]), float(arr[0, 1]))]
    for i in range(len(arr) - 1):
        if i in over:
            out.extend(
                densify_edge(
                    arr[i, 0], arr[i, 1], arr[i + 1, 0], arr[i + 1, 1], tolerance_deg
                )
            )
        out.append((float(arr[i + 1, 0]), float(arr[i + 1, 1])))
    return out
