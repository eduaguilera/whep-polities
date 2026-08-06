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
    "is_aggregate",
)

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


def load_layer_b(path: str | None = None):
    """Load the consolidated layer-B parquet, asserting its documented columns."""
    import pandas as pd
    p = path or LAYER_B
    if not os.path.exists(p):
        raise FileNotFoundError(
            f"{p} not present. Layer B lives outside the repository, in the maintainer's "
            f"own store; set WHEP_LAYERB to point elsewhere."
        )
    df = pd.read_parquet(p)
    require_columns(df, LAYER_B_COLUMNS, f"layer B ({os.path.basename(p)})")
    return df


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

    print("\nPASS: the guards fire" if ok else "\nFAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(_selftest())
