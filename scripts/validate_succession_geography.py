#!/usr/bin/env python3
"""Check that a succession link joins two territories that actually touch.

`predecessor` and `successor` say one polity became another. Issue 34's checks catch links
that dangle or point at a dead row, but a link can name a REAL, LIVE polity and still be
wrong — and nothing noticed, because a wrong code looks exactly like a right one.

Comparing the two polygons catches it. NWR-1900-1905, Northwestern Rhodesia, listed its
successor as NNI-1904-1913 — Northern NIGERIA, roughly 4,000 km away on the other side of
Africa. Northwestern Rhodesia merged with Northeastern Rhodesia to form Northern Rhodesia,
which exists here as NRH-1911-1953. Almost certainly a confusion between two codes that both
begin "Northern". Corrected, and it is the reason this script exists.

Non-intersection is a SCREEN, not a verdict. Nine links legitimately join territories that
do not touch, because succession here also covers colonial and administrative transfer
rather than only contiguous partition:

  CAR/GCAR with JPN and DEU   the Caroline Islands passed from German to Japanese rule; a
                              Pacific archipelago never touches either metropole
  CXR with GBM                Christmas Island was administered from Singapore
  SYC with MUS                the Seychelles were administered from Mauritius until 1903
  SMO with SWA                Spanish Morocco and Spanish West Africa were a shared
                              administration, not adjacent ground
  HAWI with USA               Hawaii became a state in 1959; the USA polygon here does not
                              reach across the Pacific
  NNG with IDN                Netherlands New Guinea joined Indonesia in 1963, after the
                              span of the IDN row it points at

  IJB with SNI                the one that is NOT obviously fine. The Ijebu Kingdom was in
                              south-western Nigeria and Southern Nigeria surrounded it, so
                              these two SHOULD intersect. Baselined rather than fixed
                              because the fault is more likely one of the polygons than the
                              link, and diagnosing which needs a polygon decision.

Baselined bidirectionally: a NEW non-intersecting link fails, and a baselined one that comes
to intersect fails until it leaves the list.

Requires the built GeoPackage and skips loudly if geopandas is unavailable, rather than
passing quietly — a check that silently does nothing is how this repo has been bitten before.

Usage:
  python3 scripts/validate_succession_geography.py
"""
import ast
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLITIES_CSV = os.path.join(REPO, "data/final/polities_database.csv")
POLITIES_GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")

BASELINE = frozenset({
    ("CAR-1920-1945", "predecessor", "JPN-1895-1945"),
    ("CXR-1946-1958", "predecessor", "GBM-1895-1946"),
    ("GCAR-1899-1914", "predecessor", "DEU-1871-1919"),
    ("GCAR-1899-1914", "successor", "JPN-1895-1945"),
    ("HAWI-1898-1959", "successor", "USA-1959-2025"),
    ("IJB-1800-1892", "successor", "SNI-1899-1906"),
    ("NNG-1949-1963", "successor", "IDN-1949-1969"),
    ("SMO-1912-1956", "predecessor", "SWA-1884-1912"),
    ("SYC-1903-2025", "predecessor", "MUS-1800-2025"),
})


def parse_links(value: str) -> list:
    v = (value or "").strip()
    if not v or v in ("[]", "NA"):
        return []
    try:
        if v.startswith("["):
            return [str(x).strip() for x in ast.literal_eval(v)]
    except (ValueError, SyntaxError):
        pass
    return [x.strip() for x in v.strip("[]").split(",") if x.strip()]


def main() -> int:
    try:
        import geopandas as gpd
        from shapely.validation import make_valid
    except ImportError as exc:
        print(f"FAIL: geopandas/shapely unavailable ({exc}); cannot compare polygons")
        return 2
    if not os.path.exists(POLITIES_GPKG):
        print(f"FAIL: {POLITIES_GPKG} missing; run scripts/build_database.py first")
        return 2

    rows = list(csv.DictReader(open(POLITIES_CSV, encoding="utf-8")))
    known = {r["polity_code"] for r in rows}

    frame = gpd.read_file(POLITIES_GPKG)
    frame = frame[~frame.geometry.isna() & ~frame.geometry.is_empty]
    # make_valid because several source polygons are self-intersecting, and an invalid
    # geometry makes `intersects` raise rather than answer.
    geom = {c: make_valid(g) for c, g in zip(frame["polity_code"], frame.geometry)}

    observed = set()
    checked = 0
    for r in rows:
        src = r["polity_code"]
        for field in ("predecessor", "successor"):
            for target in parse_links(r.get(field)):
                if target not in known or src not in geom or target not in geom:
                    continue
                checked += 1
                if not geom[src].intersects(geom[target]):
                    observed.add((src, field, target))

    print(f"succession links with geometry on both sides: {checked}")
    print(f"whose polygons do not intersect: {len(observed)}")
    for src, field, target in sorted(observed):
        print(f"   {src:<18} {field:<12} -> {target}")

    problems = []
    for src, field, target in sorted(observed - BASELINE):
        problems.append(
            f"NEW disjoint link: {src} {field} {target} — the two polygons do not touch, "
            f"so either the link names the wrong polity or a polygon is wrong"
        )
    for src, field, target in sorted(BASELINE - observed):
        problems.append(
            f"{src} {field} {target} now intersects — remove it from the baseline"
        )

    if problems:
        print(f"\nFAIL: {len(problems)} change(s) against the baseline\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: disjoint succession links match the baseline exactly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
