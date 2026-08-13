#!/usr/bin/env python3
"""Check that "this area has no polity" is still true of every area that claims it.

`pipelines/faostat-era-matching/state/registry_unmapped.csv` lists FAOSTAT reporting areas the
matcher could not route, each carrying the note "registry area with no polity family
(non-country/aggregate)". That note is a CLAIM ABOUT THE POLITIES DATABASE, and nothing checked it.

WHAT THAT COST, on 2026-08-13. PRs 190, 201 and 210 created sixteen polities for territories that
FAOSTAT reports -- Aruba, the Holy See, Mayotte, the Caymans, Gibraltar, Curacao and the rest --
closing issues 185, 187 and 209. Every one of them stayed listed here as having no polity family,
because creating a polity does not touch this file, and `faostat_area_polity_map.csv` is GENERATED
from a registry that reads it. So all sixteen still resolved downstream to `ROW-1850-2025`, an
aggregate with no territory: the polities existed and the data could not reach them, which is
exactly the failure those three issues were filed about.

A consuming session found it, not this repo. That is the gap being closed.

TWO SIGNALS, both cheap and both zero-noise today:

  A. STALE CLAIM     an area listed here whose iso3 IS carried by a live polity. The note is then
                     false, and either a map row is missing or the note needs correcting.
  B. LISTED BOTH WAYS an area listed here that ALSO appears in the published map. One file says it
                     could not be routed and the other says where it routes; a consumer reading
                     either alone gets a different answer.

Signal A is the one that fires on the real defect. Signal B is stricter and catches the half-done
fix -- adding the map row while forgetting to remove the row here.

NOT BASELINED, and that is deliberate. Both counts are zero, so a baseline would only be a place
for the next occurrence to hide. The fourteen areas that remain listed genuinely have no polity:
Antarctica, Bouvet, Heard and McDonald, Svalbard, the Pacific atolls the US administers, the
Neutral Zone, and the two accounting residuals `UXY` "Unspecified" and `OXY` "Others (adjustment)"
which are not territories and should never get one.

Usage:
  python3 scripts/validate_registry_unmapped.py
"""
from __future__ import annotations

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNMAPPED = os.path.join(REPO, "pipelines/faostat-era-matching/state/registry_unmapped.csv")
MAP = os.path.join(REPO, "data/final/faostat_area_polity_map.csv")
DB = os.path.join(REPO, "data/final/polities_database.csv")
DEAD = ("retired", "superseded")


def live_by_iso() -> dict:
    """iso3 -> live polity codes carrying it.

    Dead rows are excluded because a retired polity is not something an area can be routed to, so
    an area whose only same-iso3 polity is superseded really does have nowhere to go.
    """
    out: dict[str, list] = {}
    with open(DB, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if (r.get("wiki_status") or "").strip() in DEAD:
                continue
            iso = (r.get("iso3_code") or "").strip()
            if iso and iso not in ("NA", "NAN"):
                out.setdefault(iso, []).append(r["polity_code"])
    return out


def main() -> int:
    for path in (UNMAPPED, MAP, DB):
        if not os.path.exists(path):
            print(f"SKIP: {os.path.relpath(path, REPO)} missing")
            return 0

    with open(UNMAPPED, encoding="utf-8") as fh:
        unmapped = list(csv.DictReader(fh))
    with open(MAP, encoding="utf-8") as fh:
        mapped = {(r.get("area_code") or "").strip() for r in csv.DictReader(fh)}
    by_iso = live_by_iso()

    stale, both = [], []
    for u in unmapped:
        area = (u.get("area_code") or "").strip()
        iso = (u.get("iso3") or "").strip()
        if iso and iso in by_iso:
            stale.append((area, iso, (u.get("area_name") or "").strip(), by_iso[iso]))
        if area and area in mapped:
            both.append((area, (u.get("area_name") or "").strip()))

    print(f"registry areas listed as having no polity: {len(unmapped)}")
    print(f"published map covers:                      {len(mapped)} areas")
    print(f"A. listed here but their iso3 HAS a live polity: {len(stale)}")
    print(f"B. listed here AND present in the published map: {len(both)}")

    problems = []
    for area, iso, name, codes in sorted(stale, key=lambda t: int(t[0]) if t[0].isdigit() else 0):
        problems.append(
            f"area {area} ({name}) is listed as having no polity family, but iso3 {iso} is carried "
            f"by {', '.join(codes)}. Creating a polity does not update this file, and the FAOSTAT "
            f"map is generated from a registry that reads it — so this area still resolves to "
            f"ROW-1850-2025. Add its map row and remove it from here"
        )
    for area, name in sorted(both, key=lambda t: int(t[0]) if t[0].isdigit() else 0):
        problems.append(
            f"area {area} ({name}) is in BOTH registry_unmapped.csv and the published map — one "
            f"file says it could not be routed and the other says where it routes. Remove it here"
        )

    if problems:
        print(f"\nFAIL: {len(problems)} inconsistent claim(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: every area listed as unmapped really has no live polity to map it to")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
