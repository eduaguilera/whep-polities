#!/usr/bin/env python3
"""Extract the areas the SOURCES state for themselves, and compare them to our polygons.

The IIA yearbooks carry a `country area` table -- six editions between 1909 and 1938 -- in
which every reporting unit is given its own area in km2. That is a different kind of evidence
from anything else in this repo. Every existing area check compares our polygon against
another GIS product (CShapes, GADM, Cliopatria) or against a family median. This compares it
against WHAT THE STATISTICAL AUTHORITY THAT PUBLISHED THE DATA BELIEVED THE TERRITORY TO BE.

That distinction settles a question this repo could not otherwise answer. Issue 159 asks
whether polygons should follow CLAIMED territory (CShapes) or EFFECTIVE CONTROL (Cliopatria,
paine-2024), because the two conventions meet inside 29 families and publish the difference as
a territorial event. The answer is neither-in-the-abstract: polities exist to carry data rows,
so the territorial basis that matters is the one the source used. And the source says.

Tunisia is the clean case. Six IIA editions, 1911 through 1937, all state 125,130-125,180 km2:

    IIA stated                    125,130 km2      six editions, unchanged
    TUN-1800-1881  paine-2024      43,752 km2      0.35x  -- excludes the Saharan south
    TUN-1881-2025  cshapes-2.0    155,482 km2      1.24x  -- modern boundaries
    modern Tunisia                163,610 km2

Both of our polygons are wrong, in opposite directions, and the 3.55x step between them at 1881
is entirely an artifact of the two conventions meeting. The source's own figure sits between
them and does not move across the protectorate boundary, because the territory did not.

WHAT THIS SCRIPT IS NOT. It is not a claim that the yearbooks are more accurate than modern
GIS. They are not: IIA gives Monaco as 21 km2 in five editions and 149 in two others, against
its actual ~2, so the table contains transcription and unit errors of its own. What the stated
area IS authoritative about is the SCOPE the publisher had in mind -- whether the Sahara was
in Tunisia, whether Patagonia was in Chile -- which is exactly what a per-km2 denominator needs
to match. Use it to detect scope mismatches, not to correct coastlines.

The extraction is deliberate about provenance: the tables live outside the repo, under
Nextcloud, so this writes a committed CSV that the gate reads. The gate must not depend on data
CI cannot see -- the lesson from 04_territory_basis.py's --check, which turned main red by
comparing columns that need untracked inputs.

Usage:
  python3 pipelines/polity-autoimprove/08_source_stated_areas.py            # rewrite the CSV
  python3 pipelines/polity-autoimprove/08_source_stated_areas.py --check    # verify it is current
"""
from __future__ import annotations

import glob
import os
import re
import sys

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEST = os.path.join(REPO, "data/final/source_stated_areas.csv")

FAO_GLOB = os.environ.get(
    "WHEP_FAO_LAND_GLOB",
    os.path.expanduser(
        "~/Nextcloud/WHEP_ERC 2025/Sources/data_raw/sources_reviewed/fao/"
        "*/fao_land_*/r_fao_land_*_use_total.xlsx"
    ),
)

# FAO reports land use in hectares, IIA in km2. Conversion is exact, so it is asserted rather
# than assumed: an unrecognised unit raises instead of silently scaling by 1.
HECTARE_UNITS = {"1000 hectares": 10.0, "1000000 hectares": 10000.0}

IIA_GLOB = os.environ.get(
    "WHEP_IIA_LAND_GLOB",
    os.path.expanduser(
        "~/Nextcloud/WHEP_ERC 2025/Sources/data_raw/sources_reviewed/iia/"
        "*/iia_land_*/r_iia_land_*_country_area.xlsx"
    ),
)

# Rows that are continental or world roll-ups rather than reporting units.
AGGREGATE_PREFIXES = ("total", "monde", "world")


def _extract_iia() -> list:
    files = sorted(glob.glob(IIA_GLOB))
    if not files:
        raise FileNotFoundError(
            f"no IIA country_area tables matched {IIA_GLOB!r}. They live outside the repo; set "
            f"WHEP_IIA_LAND_GLOB if your copy is elsewhere."
        )
    rows = []
    for path in files:
        edition = int(re.search(r"_(\d{4})_", os.path.basename(path)).group(1))
        frame = pd.read_excel(path)
        for col in [c for c in frame.columns if re.fullmatch(r"\d{4}", str(c))]:
            for _, row in frame.iterrows():
                label, value = row.get("country"), row[col]
                if pd.isna(label) or pd.isna(value):
                    continue
                label = str(label).strip()
                if label.lower().startswith(AGGREGATE_PREFIXES):
                    continue
                unit = str(row.get("unit", "")).strip()
                if unit and "square kilometer" not in unit:
                    raise ValueError(f"unexpected unit {unit!r} for {label!r} in {path}")
                rows.append({
                    "source": "iia", "edition": edition, "data_year": int(col), "label": label,
                    "continent": ("" if pd.isna(row.get("continent")) else str(row["continent"]).strip()),
                    "stated_area_km2": float(value),
                    "footnote": ("" if pd.isna(row.get("footnotes")) else str(row["footnotes"]).strip()),
                })
    return rows


def _extract_fao() -> list:
    """FAO's land-use `use_total` table, which extends the reference past IIA's 1937 ceiling.

    Two reasons this is worth having beyond more coverage:

    Its labels are ENGLISH and match the ones the data actually arrives under -- `Libya
    Tripolitania`, `Indochina Viet Nam`, `Gold Coast and Br Togoland` -- where IIA's are French
    and resolve for only 77 of 785. So the same evidence reaches far more polities.

    And it CROSS-CHECKS IIA. Where both state a figure they agree to within a few per cent
    (Chile 741,770 vs 741,767; Libya 1,759,500 vs 1,759,540; Yugoslavia 1.03x; French Togoland
    1.06x) -- with ONE exception, Tunisia, where FAO says 155,830 and IIA says 125,130, a 24.5%
    gap. Two sources agreeing to four digits and a third disagreeing by a quarter is how you
    tell an outlier from a convention.

    CAVEAT ADDED BY ISSUE 196: Libya's agreement is genealogical, not independent. Both figures
    are the same Italian colonial one, published for a Libya whose southern boundary was the
    never-ratified 1935 Laval-Mussolini (Aouzou) line; IIA 1932/1933 give 1,638,000 for the same
    country, and three modern boundary products agree with that. See the docstring of
    scripts/validate_stated_areas.py.
    """
    files = sorted(glob.glob(FAO_GLOB))
    if not files:
        return []
    rows = []
    for path in files:
        edition = int(re.search(r"_(\d{4})_", os.path.basename(path)).group(1))
        frame = pd.read_excel(path)
        for col in [c for c in frame.columns if re.fullmatch(r"\d{4}", str(c))]:
            for _, row in frame.iterrows():
                label, value = row.get("country"), row[col]
                if pd.isna(label) or pd.isna(value):
                    continue
                label = str(label).strip()
                if label.lower().startswith(AGGREGATE_PREFIXES):
                    continue
                unit = str(row.get("unit", "")).strip()
                if unit not in HECTARE_UNITS:
                    raise ValueError(f"unexpected FAO unit {unit!r} for {label!r} in {path}")
                rows.append({
                    "source": "fao", "edition": edition, "data_year": int(col), "label": label,
                    "continent": ("" if pd.isna(row.get("continent")) else str(row["continent"]).strip()),
                    "stated_area_km2": float(value) * HECTARE_UNITS[unit],
                    "footnote": ("" if pd.isna(row.get("footnotes")) else str(row["footnotes"]).strip()),
                })
    return rows


def extract() -> pd.DataFrame:
    rows = _extract_iia() + _extract_fao()
    out = pd.DataFrame(rows).sort_values(["source", "edition", "data_year", "label"])
    return out.reset_index(drop=True)


def main() -> int:
    check = "--check" in sys.argv
    try:
        fresh = extract()
    except FileNotFoundError as exc:
        # The tables are outside the repo, so absence is normal in CI and in a fresh clone.
        # SKIP rather than fail: this script's committed output is what the gate reads.
        print(f"SKIP: {exc}")
        return 0

    if check:
        if not os.path.exists(DEST):
            print(f"FAIL: {DEST} missing; run this script without --check")
            return 1
        committed = pd.read_csv(DEST, keep_default_na=False, dtype=str)
        regenerated = pd.read_csv(
            __import__("io").StringIO(fresh.to_csv(index=False)), keep_default_na=False, dtype=str
        )
        if len(committed) != len(regenerated):
            print(f"FAIL: {os.path.basename(DEST)} is stale "
                  f"({len(committed)} committed rows vs {len(regenerated)} regenerated)")
            return 1
        diff = (committed != regenerated).any(axis=1)
        if diff.any():
            print(f"FAIL: {os.path.basename(DEST)} is stale ({int(diff.sum())} differing rows)")
            for idx in list(committed.index[diff])[:8]:
                print(f"  row {idx}: committed {committed.loc[idx].to_dict()}")
                print(f"           regenerated {regenerated.loc[idx].to_dict()}")
            return 1
        print(f"OK: {os.path.basename(DEST)} matches the yearbooks ({len(fresh):,} statements)")
        return 0

    fresh.to_csv(DEST, index=False)
    print(f"wrote {len(fresh):,} stated-area statements -> {os.path.relpath(DEST, REPO)}")
    print(f"  sources: {sorted(fresh.source.unique())}")
    print(f"  editions: {sorted(fresh.edition.unique())}")
    print(f"  data years: {sorted(fresh.data_year.unique())}")
    print(f"  distinct labels: {fresh.label.nunique()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
