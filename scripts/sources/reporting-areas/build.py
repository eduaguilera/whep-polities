#!/usr/bin/env python3
"""
Build WHEP reporting-area aggregate polygons.

These are not sovereign-country rows. They are spatial reporting units used by
WHEP harmonization tables (for example Belgium-Luxembourg, Africa Other, and
RoW). The geometries are reproducible unions of current GADM 4.1 country /
territory polygons keyed by `polity_code`.

END YEARS MOVED TO 2025 on 2026-08-05 (issue 50). These are statistical reporting buckets,
not historical states: their previous end years of 2013, 2021 and 2023 were artefacts of
when each row was written, not facts about any territory. FAOSTAT still reports every one of
these areas through 2024, so the buckets stopped before the data did and 72 area-years
resolved to nothing. 220 live rows already end at 2025, which is the convention for a row
that covers through 2024.
"""
from __future__ import annotations

from pathlib import Path
import sys

import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union

try:
    from shapely.validation import make_valid
except ImportError:  # pragma: no cover - Shapely < 2 fallback.
    def make_valid(geom):
        return geom.buffer(0)


REPO_ROOT = Path(__file__).resolve().parents[3]
GADM41_ADM0 = REPO_ROOT / "data/geodata/gadm-4.1/gadm41_adm0.gpkg"
OUT = REPO_ROOT / "data/geodata/reporting-areas/reporting_areas.gpkg"


REPORTING_AREAS = {
    "BLX-1850-1999": {
        "name": "Belgium-Luxembourg",
        "components": ["BEL", "LUX"],
        "note": "Union of Belgium and Luxembourg current GADM 4.1 adm0 polygons.",
    },
    "ANT-1961-2010": {
        "name": "Netherlands Antilles",
        "components": ["BES", "CUW", "SXM"],
        "note": "Proxy union of Bonaire/Sint Eustatius/Saba, Curacao, and Sint Maarten current GADM 4.1 adm0 polygons.",
    },
    "RAFR-1850-2025": {
        "name": "Africa Other",
        "components": ["ESH", "MYT", "REU", "SHN"],
        "note": "Union of WHEP Africa Other component territories from regions_full.csv.",
    },
    "RASI-1850-2025": {
        "name": "Asia Other",
        "components": ["FSM", "IOT", "MHL", "MNP", "PLW"],
        "note": "Union of WHEP Asia Other component territories; Pacific Islands Trust Territory is proxied by FSM, MHL, MNP, and PLW.",
    },
    "REUR-1850-2025": {
        "name": "Europe Other",
        "components": ["AND", "FRO", "GIB", "GRL", "LIE", "MCO", "SJM", "SMR", "VAT"],
        "note": "Union of WHEP Europe Other component territories from regions_full.csv.",
    },
    "RLAM-1850-2025": {
        "name": "Latin America Other",
        "components": [
            "ABW", "AIA", "BES", "BMU", "BVT", "CUW", "CYM", "FLK",
            "GLP", "MAF", "MSR", "MTQ", "SGS", "SXM", "TCA", "VGB", "VIR",
        ],
        "note": "Union of WHEP Latin America Other component territories from regions_full.csv; Netherlands Antilles is represented by its current successor island polygons.",
    },
    "RNAM-1850-2025": {
        "name": "North America Other",
        "components": ["SPM", "UMI"],
        "note": "Union of WHEP North America Other component territories from regions_full.csv.",
    },
    "ROCE-1850-2025": {
        "name": "Oceania Other",
        "components": [
            "ASM", "ATF", "CCK", "COK", "CXR", "GUM", "HMD", "KIR",
            "MNP", "NCL", "NFK", "NIU", "PCN", "PLW", "TKL", "UMI", "WLF",
        ],
        "note": "Union of WHEP Oceania Other component territories; Canton/Enderbury is proxied by Kiribati and Johnston/Midway/Wake by US Minor Outlying Islands.",
    },
}


ROW_COMPONENTS = [
    code for code in REPORTING_AREAS
    if code not in {"ROW-1850-2025"}
]


def load_gadm() -> gpd.GeoDataFrame:
    if not GADM41_ADM0.exists():
        raise FileNotFoundError(
            f"{GADM41_ADM0} missing; run scripts/sources/gadm-4.1/fetch.sh first."
        )
    gadm = gpd.read_file(GADM41_ADM0, layer="polygons")
    gadm = gadm[["GID_0", "geometry"]].copy()
    gadm["geometry"] = gadm.geometry.map(make_valid)
    return gadm


def union_components(gadm: gpd.GeoDataFrame, components: list[str]):
    matched = gadm[gadm["GID_0"].isin(components)]
    found = set(matched["GID_0"])
    missing = sorted(set(components) - found)
    if missing:
        raise LookupError(f"Missing GADM adm0 component(s): {', '.join(missing)}")
    return make_valid(unary_union(list(matched.geometry)))


def main() -> int:
    gadm = load_gadm()
    rows = []
    geometries = {}

    for code, spec in REPORTING_AREAS.items():
        geom = union_components(gadm, spec["components"])
        geometries[code] = geom
        rows.append({
            "polity_code": code,
            "polity_name": spec["name"],
            "components": ";".join(spec["components"]),
            "provenance": spec["note"],
            "geometry": geom,
        })
        print(f"  OK   {code}: {spec['name']}")

    row_geom = make_valid(unary_union([geometries[code] for code in ROW_COMPONENTS]))
    rows.append({
        "polity_code": "ROW-1850-2025",
        "polity_name": "Rest of World",
        "components": ";".join(ROW_COMPONENTS),
        "provenance": "Union of WHEP aggregate reporting-area polygons BLX, ANT, RAFR, RASI, REUR, RLAM, RNAM, and ROCE.",
        "geometry": row_geom,
    })
    print("  OK   ROW-1850-2025: Rest of World")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()
    gdf = gpd.GeoDataFrame(pd.DataFrame(rows), geometry="geometry", crs="EPSG:4326")
    gdf.to_file(OUT, layer="reporting_areas", driver="GPKG")
    print(f"Wrote: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
