#!/usr/bin/env python3
"""Loud loaders for the external datasets this pipeline reads.

WHY THIS EXISTS. Six analyses in one session produced a wrong ANSWER rather than an
exception, because pandas and csv both treat a name that is not there as absent data
rather than as a mistake:

  read `year_start` where match_confidence.csv has `year_min`
      -> empty result, nearly reported as "no polities affected"
  join on layer B's `polity_code`, which holds LOWERCASE ISO CODES ("fra"), not polity codes
      -> zero for every row; a table of zeros nearly published as evidence of absence
  read `source_label`/`polity_code` against applied_aliases.csv's
  `original_name`/`target_polity_code`
      -> "0 clipped", reported as success
  read `iso3` where polities_database.csv has `iso3_code`
      -> KeyError; the ONLY one of the six caught immediately, and only by luck of being
         indexed directly rather than filtered on
  filter Element == "Export quantity" on the bilateral trade pin, which spells it
  "Export Quantity" with a capital Q
      -> 0 of 19,868,672 rows matched, printed as "flows reported from both sides: 0"

The last is the clearest case for this module. Zero mirrored flows in a bilateral trade
dataset is absurd on its face, which is the only reason it was questioned. A less obviously
impossible zero would have shipped.

None of the eleven scripts in this pipeline asserts its columns or its categorical values.
This module gives them somewhere to.

WHAT IT DOES NOT DO: it does not normalise or repair. It raises. A pipeline that quietly
copes with a renamed column is how the rename goes unnoticed; the point is to stop.
"""
from __future__ import annotations

import os

# --------------------------------------------------------------------------------------
# Paths. Overridable by environment variable, matching 01_match_and_findings.py's WHEP_LAYERB.
# --------------------------------------------------------------------------------------
LAYER_B = os.environ.get(
    "WHEP_LAYERB",
    os.path.expanduser("~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet"),
)

# The reconciled crop panel (whep_crops v1.0, from Juan). Lives under a gitignored path inside
# the repo by default because it is 103 MB; WHEP_CROPS moves it outside, as layer B is.
WHEP_CROPS = os.environ.get(
    "WHEP_CROPS",
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data/external/whep_crops/whep_crops_v1.0.parquet",
    ),
)

# --------------------------------------------------------------------------------------
# Documented schemas. These are ASSERTED, not hoped for.
# --------------------------------------------------------------------------------------
LAYER_B_COLUMNS = (
    "source", "source_detail", "continent",
    "country",        # THE LABEL. Not `source_label`, not `original_name`, not `label`.
    "item", "item_code", "indicator", "year", "period", "value", "unit",
    "iso3c",          # not `iso3`, not `iso3_code`
    "polity_code",    # HOLDS LOWERCASE ISO CODES ("fra", "deu"), NOT WHEP POLITY CODES.
                      # Joining this to polities_database.polity_code matches NOTHING and
                      # returns zero counts, not an error. Use `country` with the alias map.
                      # load_layer_b RENAMES it to `iso3_lower` so no reader here can make
                      # that join by its obvious-looking name; see LAYER_B_MISNAMED below.
    "is_aggregate",
)

# THE ONE COLUMN WHOSE NAME IS WRONG ABOUT ITS CONTENTS, not merely inconsistent with ours.
# Measured on the current parquet (2026-08-13, 192,670 rows): `polity_code` has 166 distinct
# values, 99.37% of the non-null ones exactly `lower(iso3c)`, and 0 of the 166 equal to any
# polity code in data/final/polities_database.csv. So the join a reader naturally writes --
#     layer_b.merge(polities, on="polity_code")
# -- returns an empty frame and no error. That is issue 95, option 4, and it cost a table of
# zeros nearly published as evidence that no data existed in those years.
#
# The parquet is built outside this repository, so its header cannot be fixed here. Renaming
# on the way IN fixes it for every reader in this repo: the misleading name never exists in
# a frame any script here holds.
LAYER_B_MISNAMED = {"polity_code": "iso3_lower"}

# whep_crops is keyed on ISO3 + item_code + year, NOT on a free-text label -- so it needs no alias
# map, and its coverage question is different from layer B's: does every (iso3, year) resolve to
# exactly one polity?
#
# THE COLUMNS THAT DECIDE WHETHER A ROW MAKES A HISTORICAL CLAIM AT ALL:
#   src_production / src_area / src_yield   a value beginning "backcast" is MODELLED onto a modern
#                                           ISO3 unit, not observed for a historical entity. 55.4%
#                                           of production values are back-cast.
#   state / state_production / ...           `active`, `pre_emergence` (the unit did not exist yet),
#                                           `not_estimable`, `extinct`.
# Matching back-cast or pre_emergence rows to a historical polity is a category error: those rows
# describe a modern territory's past, not a past polity. Filter on both before any coverage claim.
WHEP_CROPS_COLUMNS = (
    "iso3", "item_code", "year", "area", "production", "yield",
    "m_area", "m_production", "m_yield",
    "src_area", "src_production", "src_yield",
    "anchor_area", "anchor_production", "anchor_yield",
    "state", "state_area", "state_production", "state_yield",
)

# Unit spellings seen in layer B, mapped into hectares and tonnes. Anything absent from
# both maps is not an area or a production figure: heads, people, bushels, gallons,
# hectolitres, kilograms, number.
AREA_UNITS = {"ha": 1.0, "hectares": 1.0, "1000 hectares": 1e3, "1000 ha": 1e3,
              "1000000 hectares": 1e6}
PROD_UNITS = {"tonnes": 1.0, "t": 1.0, "1000 tonnes": 1e3, "metric tons": 1.0,
              "tons": 1.0}

# THE TWO FAOSTAT PINS DISAGREE ON CAPITALISATION. This is not a style quibble: filtering
# with the wrong one silently matches zero rows out of tens of millions.
#
#   faostat-trade.parquet            Element = "Export quantity"   lowercase q
#   faostat-trade-bilateral.parquet  Element = "Export Quantity"   capital  Q
#
# Compare case-insensitively, always. These are the lowercased forms to compare against.
TRADE_ELEMENTS = ("export quantity", "import quantity", "export value", "import value")


class ExternalDataError(RuntimeError):
    """An external dataset does not look the way this pipeline believes it does."""


def require_columns(df, columns, where: str) -> None:
    """Raise unless every named column is present, naming what is missing AND what is there.

    Printing the actual columns matters more than printing the missing ones: the usual cause
    is a near-miss spelling, and seeing `year_min` beside a request for `year_start` explains
    it instantly.
    """
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ExternalDataError(
            f"{where}: missing column(s) {missing}.\n"
            f"  present: {list(df.columns)}\n"
            f"  If this is an upstream rename, fix the reader AND this module's schema; a\n"
            f"  column that is merely absent returns None and propagates as an empty result."
        )


def require_any_value(df, column: str, expected, where: str, case_insensitive=True):
    """Raise if NONE of `expected` occurs in `column`. Warn if only some do.

    This is the check that would have caught the "Export quantity" / "Export Quantity" case.
    A filter matching zero rows is indistinguishable from a filter matching nothing real,
    and the difference is the whole answer.
    """
    require_columns(df, [column], where)
    series = df[column].dropna().astype(str)
    if case_insensitive:
        series = series.str.lower()
        expected = [str(e).lower() for e in expected]
    present = set(series.unique())
    hit = [e for e in expected if e in present]
    if not hit:
        sample = sorted(present)[:12]
        raise ExternalDataError(
            f"{where}: none of {list(expected)} occurs in column {column!r}.\n"
            f"  actual values (up to 12): {sample}\n"
            f"  A filter on an absent value matches zero rows and reports a clean result."
        )
    if len(hit) < len(expected):
        missing = [e for e in expected if e not in present]
        print(f"  note: {where}: {missing} absent from {column!r}; proceeding with {hit}")
    return hit


def load_whep_crops(path: str | None = None, columns=None):
    """Load whep_crops v1.0, asserting the columns this repo relies on.

    Same contract as load_layer_b: a missing file raises with the env var named, and a renamed
    column raises rather than being coped with. Pass `columns` to read a subset -- the full panel
    is 1.84M rows by 28 columns.
    """
    target = path or WHEP_CROPS
    if not os.path.exists(target):
        raise FileNotFoundError(
            f"whep_crops not found at {target!r}. Set WHEP_CROPS to point at "
            f"whep_crops_v1.0.parquet, or copy it to data/external/whep_crops/ (gitignored)."
        )
    import pandas as pd

    frame = pd.read_parquet(target, columns=list(columns) if columns else None)
    require_columns(frame, columns or WHEP_CROPS_COLUMNS, f"whep_crops ({target})")
    return frame


POLITIES_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data/final/polities_database.csv",
)


def polity_codes_from_database(path: str | None = None) -> set:
    """The published polity codes, for the reverse guard in rename_layer_b_misnamed.

    Exists so that guard cannot be inert BY DEFAULT. `rename_layer_b_misnamed` only refuses
    to relabel a fixed upstream if it is TOLD what a real polity code looks like, and two of
    the three readers here (07_yield_consistency, 10_livestock_consistency) called
    load_layer_b() with no argument -- so for them the check compared against nothing and
    passed for that reason, not because the column was still wrong. A guard that is present
    but supplied with an empty set is the same silence it was written to break.

    Returns an empty set if the CSV is missing, rather than raising: the loader's job is
    layer B, and a repo without data/final is a different problem with its own gates.
    """
    import csv as _csv

    target = path or POLITIES_CSV
    if not os.path.exists(target):
        return set()
    with open(target, newline="", encoding="utf-8") as fh:
        return {
            row["polity_code"]
            for row in _csv.DictReader(fh)
            if row.get("polity_code")
        }


def rename_layer_b_misnamed(df, polity_codes=None, where: str = "layer B"):
    """Rename layer B's mislabelled `polity_code` to `iso3_lower`, or raise if it changed.

    Renaming is not cosmetic here: the column's NAME is wrong about its CONTENTS, and the
    wrongness is silent (see LAYER_B_MISNAMED). If the upstream file is ever fixed to hold
    real polity codes, renaming them to `iso3_lower` would be the new silent wrong answer --
    so pass `polity_codes` and this raises instead of quietly mislabelling them.
    """
    for old, new in LAYER_B_MISNAMED.items():
        if old not in df.columns:
            continue
        if polity_codes:
            values = set(df[old].dropna().astype(str).unique())
            hits = values & set(polity_codes)
            if hits:
                raise ExternalDataError(
                    f"{where}: column {old!r} now holds REAL polity codes "
                    f"({sorted(hits)[:5]}...). It used to hold lowercase ISO codes, which is "
                    f"why this module renamed it to {new!r}. Drop it from LAYER_B_MISNAMED "
                    f"and join on it, rather than renaming a correct column into a wrong one."
                )
        if new in df.columns:
            raise ExternalDataError(
                f"{where}: cannot rename {old!r} to {new!r} -- {new!r} already exists."
            )
        df = df.rename(columns={old: new})
    return df


def load_layer_b(path: str | None = None, polity_codes=None):
    """Load the consolidated layer-B parquet, asserting its documented columns.

    Returns it with `polity_code` renamed to `iso3_lower` (LAYER_B_MISNAMED), because that
    column holds lowercase ISO codes and joining it to this repo's `polity_code` matches
    nothing while raising nothing.

    `polity_codes` DEFAULTS to the published database's codes, so the reverse guard -- refuse
    to relabel the column once it holds real polity codes -- is live for every caller. It was
    not: this function's two callers passed nothing, so for them the guard compared against an
    empty set.
    """
    import pandas as pd
    p = path or LAYER_B
    if not os.path.exists(p):
        raise FileNotFoundError(
            f"{p} not present. Layer B lives outside the repository, in the maintainer's "
            f"own store; set WHEP_LAYERB to point elsewhere."
        )
    df = pd.read_parquet(p)
    require_columns(df, LAYER_B_COLUMNS, f"layer B ({os.path.basename(p)})")
    return rename_layer_b_misnamed(
        df,
        polity_codes=polity_codes if polity_codes is not None else polity_codes_from_database(),
        where=f"layer B ({os.path.basename(p)})",
    )


def _selftest() -> int:
    """Prove the guards fire. Run: python3 extdata.py"""
    import pandas as pd
    ok = True

    df = pd.DataFrame({"year_min": [1, 2], "n_rows": [3, 4]})
    try:
        require_columns(df, ["year_start"], "selftest")
        print("FAIL: require_columns accepted a missing column"); ok = False
    except ExternalDataError as e:
        assert "year_min" in str(e), "the error should show what IS present"
        print("pass: require_columns raises and shows the near-miss (`year_min`)")

    df = pd.DataFrame({"Element": ["Export Quantity", "Import Quantity"]})
    try:
        # The real bug: lowercase q, case-sensitive comparison.
        require_any_value(df, "Element", ["Export quantity"], "selftest",
                          case_insensitive=False)
        print("FAIL: require_any_value accepted a value that does not occur"); ok = False
    except ExternalDataError as e:
        assert "Export Quantity" in str(e), "the error should show the actual values"
        print("pass: require_any_value raises on the capital-Q mismatch")

    hit = require_any_value(df, "Element", ["Export quantity"], "selftest")
    assert hit == ["export quantity"]
    print("pass: the same comparison succeeds case-insensitively")

    df = pd.DataFrame({"polity_code": ["fra", "deu"], "value": [1, 2]})
    out = rename_layer_b_misnamed(df, polity_codes={"FRA-1800-1871"}, where="selftest")
    assert "polity_code" not in out.columns and list(out["iso3_lower"]) == ["fra", "deu"]
    print("pass: layer B's ISO-holding `polity_code` is renamed to `iso3_lower`")

    df = pd.DataFrame({"polity_code": ["FRA-1800-1871"], "value": [1]})
    try:
        rename_layer_b_misnamed(df, polity_codes={"FRA-1800-1871"}, where="selftest")
        print("FAIL: renamed a column that had started holding real polity codes"); ok = False
    except ExternalDataError as e:
        assert "REAL polity codes" in str(e)
        print("pass: the rename refuses once the column holds real polity codes")

    codes = polity_codes_from_database()
    if not codes:
        print("note: data/final/polities_database.csv absent; default-codes case skipped")
    elif not any("-" in c for c in codes):
        print("FAIL: polity_codes_from_database returned nothing that looks like a code"); ok = False
    else:
        print(f"pass: the reverse guard has {len(codes):,} real polity codes to compare "
              f"against BY DEFAULT, so a no-argument load_layer_b() is guarded too")

    print("\nPASS: the guards fire" if ok else "\nFAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(_selftest())
