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

# --------------------------------------------------------------------------------------
# The bilateral trade pin (issue 112). Lives in the pins cache, under a CONTENT-HASH
# directory, so its path cannot be hard-coded without pinning the hash: resolve by glob.
# --------------------------------------------------------------------------------------
TRADE_BILATERAL = os.environ.get("WHEP_TRADE_BILATERAL", "")
TRADE_BILATERAL_GLOB = os.path.expanduser(
    "~/.cache/pins/url/*/faostat-trade-bilateral.parquet"
)
TRADE_BILATERAL_COLUMNS = (
    "Reporter Country Code", "Reporter Countries",
    "Partner Country Code", "Partner Countries",
    "Item Code", "Item", "Element Code", "Element", "Year", "Unit", "Value",
)

# THREE OF ITS STRING COLUMNS ARE NOT UTF-8. They are latin-1: "Maté leaves",
# "Côte d'Ivoire", "Réunion", "Türkiye". pandas does not cope and does not say why --
#
#   pd.read_parquet(pin)
#   pyarrow.lib.ArrowException: Unknown error: Wrapping Mat? leaves failed
#
# -- which names neither the column nor the encoding, and reads as a corrupt file rather
# than as a decoding choice. Dropping `Item` makes the read succeed and silently discards
# the only human-readable key in the table, which is how a screen over this pin ends up
# keyed on bare numeric codes nobody can review. load_trade_bilateral decodes them.
TRADE_BILATERAL_LATIN1 = ("Reporter Countries", "Partner Countries", "Item")

# Element codes, because the STRINGS are ambiguous here in a second way beyond capital Q:
# five distinct codes all spell themselves "Export Quantity" (5907 No, 5908 Head,
# 5909 1000 Head, 5910 tonnes) and five spell "Import Quantity". Filtering on the string
# and then summing Value adds head of cattle to tonnes of wheat. Measured on the 2026-08
# pin: 5910/5610 are the ONLY codes carrying Unit == "tonnes", 11,420,261 and 11,614,303
# rows, and no non-tonne unit occurs under either.
TRADE_EXPORT_QUANTITY_CODE = 5910
TRADE_IMPORT_QUANTITY_CODE = 5610
TRADE_TONNE_UNIT = "tonnes"


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


DEAD_WIKI_STATUS = ("retired", "superseded")


def live_polity_codes(path: str | None = None) -> set:
    """The polity codes an output may legitimately name: present AND not retired/superseded.

    `polity_codes_from_database` answers "does this code exist"; this answers "may data be
    routed to it", which is the question a matcher's output has to satisfy. Routing to a
    retired or superseded row is the mistake DEAD_WIKI_STATUS exists to prevent, and
    `scripts/validate_aliases.py` already rejects it for the alias registry -- so a matcher
    that emits one is emitting something a gate would refuse if it were written by hand.
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
            and (row.get("wiki_status") or "").strip() not in DEAD_WIKI_STATUS
        }


def refuse_orphan_codes(counts, what: str, fix: str, path: str | None = None) -> None:
    """Exit 1 rather than write `what` when it names a polity code data cannot be routed to.

    THE #244 PATTERN, generalised (issue 17). A matcher's output is a crosswalk: rows in,
    polity codes out. When the database moves underneath it -- a re-span, a rename, a
    retirement -- the codes it emits can stop existing, and every consumer downstream then
    LOOKS THE CODE UP AND FINDS NOTHING. Measured on this repo 2026-08-17: one published
    FAOSTAT mapping row pointing at a fabricated `ZZZ-1800-1900` passes NINE of the TEN
    gates that read `data/final/faostat_area_polity_map.csv`, because the one that joins on
    the code (`validate_map_area_year`) SKIPS rows whose code is not live -- an orphan is
    literally invisible to the check that would otherwise catch it. (The tenth,
    `crosscheck_matchers.py`, does catch it by re-resolving every published area through
    matchlib; the outputs THIS function protects have no such second reader, see below.)

    Why the write and not a gate: `matched_rows.parquet` is gitignored, so no gate in CI can
    ever read it, and the five orphan codes carrying 799 rows in issue 243 sat precisely
    there while `territory_basis.csv` published 0 rows for their successors.

    So the refusal belongs at the write, where the bad crosswalk is authored, not in a gate
    downstream. That siting is also what makes it work at all for these matchers: their
    INPUTS live outside the repo (WHEP_LAYERB, the FAOSTAT pins cache), so CI can never run
    them, and a gate expressing this invariant would skip in the only place gates run
    automatically. This runs wherever the matcher runs, which is the only place the defect
    can be introduced.

    `counts` maps polity code -> number of rows carrying it (any iterable of codes works
    too, and is reported without counts). `fix` is the command that regenerates the input.
    """
    if not isinstance(counts, dict):
        from collections import Counter

        counts = Counter(c for c in counts if c)
    live = live_polity_codes(path)
    if not live:
        print(f"WARNING: {what}: no polity database to check codes against; "
              f"orphan-code guard skipped")
        return
    orphans = {c: n for c, n in counts.items() if c and c not in live}
    if not orphans:
        return
    total = sum(orphans.values())
    print(f"FAIL: {what} names {len(orphans)} polity code(s) the database cannot route "
          f"data to, carrying {total:,} row(s). Every consumer looks these codes up and "
          f"finds nothing, silently:")
    for code, n in sorted(orphans.items(), key=lambda t: (-t[1], t[0])):
        why = "retired/superseded" if code in polity_codes_from_database(path) else "absent"
        print(f"  {code}  {n:,} row(s)  [{why}]")
    print(f"  refusing to write. {fix}")
    raise SystemExit(1)


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


def find_trade_bilateral(path: str | None = None) -> str:
    """Resolve the bilateral trade pin's path, or raise naming the env var and the glob.

    WHEP_TRADE_BILATERAL wins; otherwise the newest match of TRADE_BILATERAL_GLOB, because
    the pins cache keys on a content hash and a re-pinned file lands in a new directory.
    """
    import glob

    target = path or TRADE_BILATERAL
    if target:
        if not os.path.exists(target):
            raise FileNotFoundError(
                f"bilateral trade pin not found at {target!r} (from WHEP_TRADE_BILATERAL)."
            )
        return target
    hits = sorted(glob.glob(TRADE_BILATERAL_GLOB), key=os.path.getmtime, reverse=True)
    if not hits:
        raise FileNotFoundError(
            f"bilateral trade pin not found. Looked for {TRADE_BILATERAL_GLOB!r}; set "
            f"WHEP_TRADE_BILATERAL to point at faostat-trade-bilateral.parquet. It lives in "
            f"the maintainer's pins cache, outside this repository."
        )
    return hits[0]


def decode_latin1_columns(table, columns):
    """Return a pandas frame from an arrow `table`, decoding non-UTF-8 columns as latin-1.

    Exists because `.to_pandas()` on the bilateral pin raises `ArrowException: Unknown
    error: Wrapping Mat? leaves failed` -- a message that names no column, no encoding and
    no remedy. The two ways past it without this helper are both wrong: drop the offending
    columns (losing every readable label) or catch and continue (an empty result again).
    """
    import pyarrow as pa

    named = [c for c in columns if c in table.column_names]
    keep = [c for c in table.column_names if c not in named]
    frame = table.select(keep).to_pandas()
    for col in named:
        raw = table[col].combine_chunks().cast(pa.binary()).to_pylist()
        frame[col] = [None if v is None else v.decode("latin-1") for v in raw]
    return frame[[c for c in table.column_names]]


def load_trade_bilateral(path: str | None = None, columns=None):
    """Load the FAOSTAT bilateral trade pin, asserting its columns and its Element values.

    The pin is 46.8M rows by 16 columns, so pass `columns` for a subset -- but the subset
    is asserted against TRADE_BILATERAL_COLUMNS all the same, and `Element` is checked to
    still carry the capital-Q spellings, which is the mismatch that reported "0 flows
    reported from both sides" out of 19.9M rows in issue 112.
    """
    import pyarrow.parquet as pq

    # Schema check FIRST, before the file lookup: it is the half that can run without the
    # pin, and the pipeline's self-test has no pin.
    want = list(columns) if columns else list(TRADE_BILATERAL_COLUMNS)
    unknown = [c for c in want if c not in TRADE_BILATERAL_COLUMNS]
    if unknown:
        raise ExternalDataError(
            f"bilateral trade pin: {unknown} is not in this module's documented schema "
            f"{list(TRADE_BILATERAL_COLUMNS)}. Add it there as well, so a later rename "
            f"upstream raises here instead of returning an empty column."
        )
    target = find_trade_bilateral(path)
    table = pq.read_table(target, columns=want)
    where = f"bilateral trade pin ({os.path.basename(target)})"
    frame = decode_latin1_columns(table, TRADE_BILATERAL_LATIN1)
    require_columns(frame, want, where)
    if "Element" in frame.columns:
        require_any_value(frame, "Element", ["export quantity", "import quantity"], where)
    if "Unit" in frame.columns:
        require_any_value(frame, "Unit", [TRADE_TONNE_UNIT], where)
    return frame


def trade_bilateral_code_names(code_col: str, name_col: str, path: str | None = None):
    """{code: name} for one of the pin's code/label pairs, decoded, without loading it.

    Reading the label columns into pandas alongside 46.8M numeric rows costs several
    gigabytes for three columns that hold 189, 220 and 559 distinct values. Arrow's
    group_by returns the distinct pairs in about a second, so the labels cost nothing --
    and the alternative that "works", dropping them, is how a screen over this pin ends up
    keyed on numeric codes no reviewer can read.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    for col in (code_col, name_col):
        if col not in TRADE_BILATERAL_COLUMNS:
            raise ExternalDataError(
                f"bilateral trade pin: {col!r} is not in this module's documented schema."
            )
    table = pq.read_table(find_trade_bilateral(path), columns=[code_col, name_col])
    if name_col in TRADE_BILATERAL_LATIN1:
        table = table.set_column(
            table.column_names.index(name_col), name_col,
            table[name_col].combine_chunks().cast(pa.binary()),
        )
    pairs = table.group_by([code_col, name_col]).aggregate([])
    out = {}
    for code, name in zip(pairs[code_col].to_pylist(), pairs[name_col].to_pylist()):
        if code is None or name is None:
            continue
        out.setdefault(code, name.decode("latin-1") if isinstance(name, bytes) else name)
    if not out:
        raise ExternalDataError(
            f"bilateral trade pin: {code_col!r}/{name_col!r} yielded no pairs."
        )
    return out


def require_trade_quantity_codes(element_names) -> None:
    """Assert 5910/5610 still mean export/import quantity, given {code: Element} pairs.

    A reader who filters on Element CODES escapes the capital-Q trap and walks into a
    quieter one: if FAOSTAT ever renumbers, 5910 still selects rows and still sums, and the
    answer is simply about something else. So the codes are checked against the labels they
    are supposed to carry -- cheaply, via trade_bilateral_code_names, which does not load
    the 46.8M-row label column.
    """
    keys = {float(k): str(v) for k, v in element_names.items()}
    for code, word in ((TRADE_EXPORT_QUANTITY_CODE, "export"),
                       (TRADE_IMPORT_QUANTITY_CODE, "import")):
        label = keys.get(float(code), "")
        if word not in label.lower() or "quantity" not in label.lower():
            raise ExternalDataError(
                f"bilateral trade pin: Element Code {code} is labelled {label!r}, not a "
                f"{word} quantity. This module's codes are stale; filtering on them still "
                f"returns rows, so the result would be about something else. Present: "
                f"{sorted(keys.items())[:12]}"
            )


def _selftest() -> int:
    """Prove the guards fire. Run: python3 extdata.py"""
    import contextlib
    import io

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

    # The bilateral pin's latin-1 columns, on a synthetic table so this runs anywhere.
    import pyarrow as pa
    table = pa.table({
        "Item Code": pa.array([1.0, 2.0]),
        "Item": pa.array([b"Mat\xe9 leaves", b"Wheat"], type=pa.binary()).cast(
            pa.string(), safe=False),
        "Element": pa.array(["Export Quantity", "Import Quantity"]),
    })
    # Whether to_pandas() RAISES on this fixture is a property of the installed pyarrow, not
    # of the guard. It raises on 19.0.1, which is what the bilateral pin is read with locally
    # ("Wrapping Mat\xe9 leaves failed"), and no longer raises on 25.0.1, which is what a
    # fresh CI runner installs. So this arm reports the environment instead of failing in it:
    # a hazard fixed upstream is not a broken guard, and pinning CI to an old pyarrow to keep
    # the assertion meaningful would be worse than saying which version was tested.
    try:
        table.to_pandas()
        print(f"note: pyarrow {pa.__version__} decodes the latin-1 fixture without raising, "
              f"so the HAZARD is absent here; the decode assertion below still runs")
    except Exception:
        print(f"pass: to_pandas() on a latin-1 string column raises under pyarrow "
              f"{pa.__version__}, as the pin does")
    out = decode_latin1_columns(table, TRADE_BILATERAL_LATIN1)
    if list(out["Item"]) != ["Maté leaves", "Wheat"]:
        print(f"FAIL: latin-1 decode produced {list(out['Item'])}"); ok = False
    elif list(out.columns) != table.column_names:
        print(f"FAIL: decode reordered the columns to {list(out.columns)}"); ok = False
    else:
        print("pass: decode_latin1_columns recovers 'Maté leaves' and keeps column order")

    try:
        require_trade_quantity_codes({5910.0: "Export Value", 5610.0: "Import Quantity"})
        print("FAIL: accepted an element code whose label is not a quantity"); ok = False
    except ExternalDataError as e:
        assert "5910" in str(e)
        print("pass: a renumbered Element Code raises instead of summing the wrong element")
    require_trade_quantity_codes({5910.0: "Export Quantity", 5610.0: "Import Quantity"})

    try:
        load_trade_bilateral(columns=["Item Code", "Reporter Name"])
        print("FAIL: accepted a column absent from the documented schema"); ok = False
    except ExternalDataError as e:
        assert "Reporter Name" in str(e)
        print("pass: a column outside TRADE_BILATERAL_COLUMNS raises before any read")
    except FileNotFoundError:
        print("FAIL: the schema check ran after the file lookup, so it is unreachable "
              "without the pin"); ok = False

    codes = polity_codes_from_database()
    if not codes:
        print("note: data/final/polities_database.csv absent; default-codes case skipped")
    elif not any("-" in c for c in codes):
        print("FAIL: polity_codes_from_database returned nothing that looks like a code"); ok = False
    else:
        print(f"pass: the reverse guard has {len(codes):,} real polity codes to compare "
              f"against BY DEFAULT, so a no-argument load_layer_b() is guarded too")

    # The orphan-code guard (issue 17). Proven both ways, because a guard that never
    # refuses and a guard that always refuses are equally useless.
    live = live_polity_codes()
    if not live:
        print("note: data/final/polities_database.csv absent; orphan-guard cases skipped")
    else:
        dead = polity_codes_from_database() - live
        sample = sorted(live)[0]
        refuse_orphan_codes({sample: 3}, what="selftest", fix="n/a")
        print(f"pass: a crosswalk naming only live codes writes ({sample})")
        for label, code in (("an absent", "ZZZ-1800-1900"),
                            ("a retired/superseded", sorted(dead)[0] if dead else None)):
            if code is None:
                print("note: no retired/superseded row in the database; case skipped")
                continue
            # The refusal prints its own FAIL report; captured so a PASSING selftest does
            # not put the word FAIL in a CI log, and asserted so the report still names
            # the code and its reason rather than merely exiting.
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    refuse_orphan_codes({code: 7}, what="selftest", fix="n/a")
                print(f"FAIL: wrote a crosswalk naming {label} code {code}"); ok = False
            except SystemExit as exc:
                assert exc.code == 1
                assert code in buf.getvalue() and label.split()[-1] in buf.getvalue(), buf.getvalue()
                print(f"pass: {label} code refuses to be written ({code})")

    print("\nPASS: the guards fire" if ok else "\nFAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(_selftest())
