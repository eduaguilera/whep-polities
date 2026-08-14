#!/usr/bin/env python3
"""Pin the column names of every published and intermediate table.

WHY THIS EXISTS. Seven tables in this repository describe the same few things, and they
used to disagree on what to call them. Issue 95 unified the INTERNAL ones; what is left
is what could not be renamed without breaking a consumer:

    the label        polity_name / source_label / country   (was: + original_name,
                                                                    label, area_name)
    the row count    observed_rows / rows_observed          (was: + rows, n_rows)
    the ISO3 code    iso3_code / iso3 / iso3c
    the polity code  polity_code                            (was: + target_polity_code)

`observed_rows` and `rows_observed` are still TRANSPOSITIONS of each other, in two files
that are routinely read together -- but both spellings now live in `data/final/`, which
is a published contract the WHEP R package reads by name, so unifying them needs a
deprecation period rather than a rename (issue 95, option 2; still open). Every
pipeline-internal table now says `source_label`, `observed_rows`, `polity_code`.

`iso3` and `iso3_code` differ by a suffix, same reason: both are published.

The consolidated layer B parquet still has a column literally named `polity_code` that
holds lowercase ISO codes (`fra`, `deu`), because that file is built outside this
repository. It is no longer a live trap HERE: extdata.load_layer_b renames it to
`iso3_lower` on the way in and raises if it ever starts holding real codes. The
parquet's own header is unchanged, so anyone reading it directly still meets the
original name -- which is why it stays documented in EXTERNAL below.

That is not hypothetical. Four analyses in one session read a wrong column name and got
an answer rather than an error: `year_start` for `year_min` returned an empty result read
as "no problems found"; a join on layer B's `polity_code` returned zero for every row and
was nearly published as evidence of absence; `iso3` for `iso3_code` raised KeyError only
because it was reached at all. A misspelled column in a CSV read is not an error, it is
a `None`, and `None` propagates quietly.

WHAT THIS GATE DOES. It asserts the exact column list of each table. A rename shows up
here, at the contract, instead of as a silently empty analysis downstream. It is a
CONTRACT check, not a quality check: it says nothing about the values.

WHAT IT DELIBERATELY DOES NOT DO. It does not require the names to be consistent. The
remaining inconsistencies are all in PUBLISHED files, where unifying them would break the
WHEP R package, which reads them by name. Pinning them means the inconsistency is written
down in one place and cannot quietly grow another spelling. The published half of the
rename (issue 95, option 2) is still open.

The consolidated layer B parquet is NOT gated: it lives outside the repo
(~/Nextcloud/whep/layer_b/), so CI cannot see it. Its schema is documented here instead,
in the EXTERNAL block, because its `polity_code` column is the most misleading name in
the whole set.

Usage:
  python3 scripts/validate_schema_contract.py
"""
import csv
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Exact column lists, in order. Order is pinned too: consumers that read by position
# (R's read.csv with col.names, awk one-liners in this repo's own docs) break on a
# reorder just as surely as on a rename.
CSV_CONTRACT = {
    "data/final/polities_database.csv": [
        "polity_code", "polity_name", "start_year", "end_year", "polity_type",
        "iso3_code", "cow_code", "continent", "wiki_status", "last_ingest",
        "polygon_source", "polygon_feature_id", "polygon_feature_year",
        "polygon_status", "polygon_area_km2", "predecessor", "successor",
    ],
    "data/final/label_alias_map.csv": [
        "source_label", "source", "year_start", "year_end", "polity_code",
        "common_name", "confidence", "observed_rows",
    ],
    "data/final/faostat_area_polity_map.csv": [
        "area_code", "year_start", "year_end", "polity_code", "source_label",
        "iso3", "match_route", "confidence", "rows_observed",
    ],
    # Added with the table itself (issue 103). `row_order` is load-bearing and easy to
    # mistake for decoration: the defect the binding gate detects is that find_feature
    # returns the FIRST match, so reproducing its choice needs the source's own ordering.
    "data/final/polygon_feature_index.csv": [
        "source", "feature_id", "row_order", "start_year", "end_year", "area_km2",
    ],
    # Renamed by issue 95: `original_name` -> `source_label`, `target_polity_code` ->
    # `polity_code`, `rows` -> `observed_rows`. These are pipeline-internal registries,
    # not a published contract, so they could be unified now; `data/final/` could not.
    "pipelines/polity-autoimprove/state/applied_aliases.csv": [
        "source_label", "source", "year_start", "year_end", "common_name",
        "polity_code", "confidence", "basis", "observed_rows",
    ],
    "pipelines/faostat-era-matching/state/faostat_aliases.csv": [
        "source_label", "source", "year_start", "year_end", "common_name",
        "polity_code", "confidence", "basis", "observed_rows", "area_code",
        "iso3", "match_route", "match_status",
    ],
    # The other four faostat-era-matching state files, pinned by issue 95 along with the
    # rename that gave them these names (`area_name` -> `source_label`, `n_rows` ->
    # `observed_rows`). Pinned because they are written by match.R, which cannot run in
    # CI (it needs the WHEP pins cache), and read by 01_match_and_findings.py and two
    # gates, which can -- so a rename on one side would otherwise surface as an empty
    # findings queue rather than as an error.
    "pipelines/faostat-era-matching/state/ambiguous.csv": [
        "source_label", "source", "year_start", "year_end", "common_name",
        "polity_code", "confidence", "basis", "observed_rows", "area_code",
        "iso3", "match_route", "match_status", "note",
    ],
    "pipelines/faostat-era-matching/state/unmatched.csv": [
        "area_code", "source_label", "iso3", "year_start", "year_end", "note",
        "observed_rows", "pins",
    ],
    "pipelines/faostat-era-matching/state/aggregates.csv": [
        "area_code", "source_label", "year_first", "year_last", "observed_rows",
        "pins", "iso3",
    ],
    "pipelines/faostat-era-matching/state/registry_unmapped.csv": [
        "area_code", "source_label", "iso3", "note",
    ],
}

# Top-level keys of the published manifest, the consumer contract the WHEP R package
# reads through WHEP_POLITIES_MANIFEST.
MANIFEST_KEYS = [
    "_comment", "claims_polygon_status", "counts", "dead_polity_codes",
    "dead_status", "faostat_area_map", "faostat_unmapped_areas",
    "identity_fields", "identity_sha256", "iso3_successor_map", "label_alias_map",
    "live_polity_codes", "local_iso3_codes", "local_iso3_why",
    "polygon_gap_polity_codes", "source", "territory_families",
    "territory_families_why",
]
# `iso3_successor_map`, `territory_families` and `territory_families_why` added 2026-08-13
# (issue 82). The successor-map CSV was published on 2026-08-06 and was the only published
# table the manifest did not name, so a consumer reading the manifest to find out what
# exists could not find the one file that says which families cover one territory.

# Not gated -- outside the repo, so CI cannot read it. Documented because its
# `polity_code` column is the trap that cost the most.
EXTERNAL = {
    # GITIGNORED, so CI cannot see it -- a local pipeline diagnostic, not a committed
    # artefact. Pinning it here failed CI on the very commit that added this gate:
    # verified locally, where the file exists, and pushed. That is the same mistake this
    # gate exists to prevent, one level up -- an assumption about a file that holds on
    # one machine and not in CI.
    #
    # Documented rather than dropped, because `year_min` is still not `year_start` and
    # that is one of the four silent wrong answers in the docstring above.
    "pipelines/polity-autoimprove/state/match_confidence.csv": [
        "source_label",   # <- was `label` until issue 95
        "source",
        "polity_code",
        "year_min",       # <- STILL NOT `year_start`, DELIBERATELY: this is the span the
        "year_max",       #    data was OBSERVED over, not the span a rule routes. Reading
                          #    year_start here returns None for every row, and an empty
                          #    result that looks clean. See 03_confidence.py.
        "observed_rows",  # <- was `n_rows` until issue 95
        "method", "iso_ok", "name_ok", "confidence_class", "risk_flags",
    ],
    "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet": [
        "source", "source_detail", "continent",
        "country",       # <- THE LABEL. Not `source_label`.
        "item", "item_code", "indicator", "year", "period", "value", "unit",
        "iso3c",         # <- not `iso3`, not `iso3_code`
        "polity_code",   # <- HOLDS LOWERCASE ISO CODES ("fra"), NOT POLITY CODES.
                         #    Joining this to polities_database.polity_code matches
                         #    NOTHING and returns zero counts, not an error. Measured
                         #    2026-08-13: 166 distinct values, 0 of them a real polity
                         #    code. This repo's readers never see the name --
                         #    extdata.load_layer_b renames it to `iso3_lower` (issue 95).
        "is_aggregate",
    ],
}


def main() -> int:
    problems = []
    checked = 0

    # Every gated path must be COMMITTED, or this gate passes locally and fails in CI --
    # exactly how it failed on the commit that introduced it. Checked here so the mistake
    # cannot be made twice. Skipped silently when git is unavailable, rather than turning
    # a missing binary into a false alarm.
    try:
        import subprocess
        tracked = set(subprocess.run(
            ["git", "-C", REPO, "ls-files"],
            capture_output=True, text=True, timeout=60, check=True,
        ).stdout.split())
        untracked = [rel for rel in CSV_CONTRACT if rel not in tracked]
        if untracked:
            problems.append(
                "pinned but NOT COMMITTED, so CI cannot read them: "
                + str(untracked)
                + " -- move them to EXTERNAL instead of gating them"
            )
    except Exception:
        pass

    for rel, expected in CSV_CONTRACT.items():
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            problems.append(f"{rel}: missing")
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            actual = next(csv.reader(fh), [])
        checked += 1
        if actual != expected:
            missing = [c for c in expected if c not in actual]
            added = [c for c in actual if c not in expected]
            if missing or added:
                problems.append(
                    f"{rel}: columns changed"
                    + (f"; GONE: {missing}" if missing else "")
                    + (f"; NEW: {added}" if added else "")
                )
            else:
                problems.append(f"{rel}: columns REORDERED\n"
                                f"      expected {expected}\n"
                                f"      actual   {actual}")

    mpath = os.path.join(REPO, "data/final/polities_manifest.json")
    if not os.path.exists(mpath):
        problems.append("data/final/polities_manifest.json: missing")
    else:
        keys = sorted(json.load(open(mpath, encoding="utf-8")).keys())
        checked += 1
        if keys != sorted(MANIFEST_KEYS):
            missing = [k for k in MANIFEST_KEYS if k not in keys]
            added = [k for k in keys if k not in MANIFEST_KEYS]
            problems.append(
                "polities_manifest.json: top-level keys changed"
                + (f"; GONE: {missing}" if missing else "")
                + (f"; NEW: {added}" if added else "")
            )

    print(f"tables with a pinned column list: {checked}")
    print(f"external tables documented but not gated: {len(EXTERNAL)}")

    if problems:
        print(f"\nFAIL: {len(problems)} contract change(s)\n")
        for p in problems:
            print(f"  {p}")
        print("\n  A renamed column is not an error at the read site -- csv.DictReader\n"
              "  returns None for a name that is not there, and None propagates into an\n"
              "  empty result that reads as 'nothing found'. If the rename is intended,\n"
              "  update the contract above AND every reader; the point of this gate is\n"
              "  that the second half cannot be forgotten.")
        return 1

    print("\nPASS: every table's columns match the pinned contract")
    return 0


if __name__ == "__main__":
    sys.exit(main())
