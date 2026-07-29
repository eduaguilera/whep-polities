#!/usr/bin/env python3
"""Check that constants duplicated across this repo still agree.

Several load-bearing constants are defined more than once, because the scripts and
the matcher are independent programs with no shared module. That is a reasonable
structure, but it means a one-file edit can make two programs disagree about
something they must not disagree about — and nothing would notice.

The two that matter:

  DEAD_STATUS   which wiki_status values mean "this row must never receive data".
                Defined FIVE times: write_manifest, validate_polygons,
                validate_aliases, validate_spatial_containment, and
                matchlib.Matcher. If the matcher's copy drifted from the
                manifest's, the matcher would route data to a row the published
                contract calls dead — the exact failure the contract exists to
                prevent, arriving through the back door.

  CLAIMS_POLYGON must be the polygon-status vocabulary minus `unassigned`. It is
                defined in write_manifest.py while the vocabulary is enforced in
                build_database.py, with nothing linking them. That gap has already
                cost something: four legacy statuses (`derived`, `approximate`,
                `missing`, `excluded`) sat outside CLAIMS_POLYGON while 11 rows
                carrying them HAD geometry, so consumers were told those rows do
                not claim a polygon. Migrating the statuses fixed the data; this
                check keeps the two definitions from parting again.

Constants are read by parsing each file's AST rather than importing it, so this
works regardless of import side effects, and by matching literals rather than
regexes, so formatting changes do not break it.

Usage:
  python3 scripts/validate_constants.py
"""
import ast
import re
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def literal_assignments(path: str, name: str) -> list:
    """Every literal assigned to `name` anywhere in the file, including inside
    functions. Returns a list because a name may legitimately be assigned once per
    scope, and disagreement between those is itself worth reporting."""
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=path)
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for t in targets:
            if isinstance(t, ast.Name) and t.id == name:
                try:
                    found.append(ast.literal_eval(node.value))
                except ValueError:
                    pass  # not a literal (e.g. a call); nothing to compare
    return found


problems: list[str] = []

# ---------- DEAD_STATUS agreement ----------
dead_sources = {
    "scripts/write_manifest.py": None,
    "scripts/validate_polygons.py": None,
    "scripts/validate_aliases.py": None,
    "scripts/validate_spatial_containment.py": None,
    "pipelines/polity-autoimprove/matchlib.py": None,
}
for rel in list(dead_sources):
    path = os.path.join(REPO, rel)
    if not os.path.exists(path):
        problems.append(f"{rel}: file missing, cannot compare DEAD_STATUS")
        continue
    vals = literal_assignments(path, "DEAD_STATUS")
    if not vals:
        problems.append(f"{rel}: no literal DEAD_STATUS found")
        continue
    dead_sources[rel] = tuple(sorted(vals[0]))

defined = {k: v for k, v in dead_sources.items() if v is not None}
distinct = set(defined.values())
print(f"DEAD_STATUS definitions found: {len(defined)}")
for rel, val in sorted(defined.items()):
    print(f"   {rel:<52}{val}")
if len(distinct) > 1:
    problems.append(
        f"DEAD_STATUS disagrees across files: {sorted(distinct)} — every matcher and "
        f"validator must agree on which rows may never receive data"
    )

# ---------- CLAIMS_POLYGON vs the enforced vocabulary ----------
claims = literal_assignments(os.path.join(REPO, "scripts/write_manifest.py"), "CLAIMS_POLYGON")
vocab = literal_assignments(
    os.path.join(REPO, "scripts/build_database.py"), "POLYGON_STATUS_VOCABULARY"
)
if not claims:
    problems.append("scripts/write_manifest.py: no literal CLAIMS_POLYGON found")
elif not vocab:
    problems.append(
        "scripts/build_database.py: no literal POLYGON_STATUS_VOCABULARY found"
    )
else:
    claims_set, vocab_set = set(claims[0]), set(vocab[0])
    print(f"\nCLAIMS_POLYGON:            {sorted(claims_set)}")
    print(f"POLYGON_STATUS_VOCABULARY: {sorted(vocab_set)}")
    # `unassigned` is the one vocabulary value that asserts NO polygon, so it is the
    # only one that may be outside CLAIMS_POLYGON.
    expected = vocab_set - {"unassigned"}
    if claims_set != expected:
        missing = sorted(expected - claims_set)
        extra = sorted(claims_set - vocab_set)
        detail = []
        if missing:
            detail.append(
                f"in the vocabulary but NOT claiming a polygon: {missing} — a consumer "
                f"would be told rows with these statuses do not claim one"
            )
        if extra:
            detail.append(f"claiming a polygon but not in the vocabulary: {extra}")
        problems.append("CLAIMS_POLYGON is not the vocabulary minus 'unassigned'; " + "; ".join(detail))

# ---------- the FAOSTAT aggregate constants vs match.R ----------
# write_manifest.py publishes group_code_min and deliberate_area_codes so the consumer stops
# re-deriving them. pipelines/faostat-era-matching/match.R acts on the same two values. Two copies of
# one fact, which is what this script exists for.
MATCH_R = os.path.join(REPO, "pipelines/faostat-era-matching/match.R")
manifest_min = literal_assignments(
    os.path.join(REPO, "scripts/write_manifest.py"), "FAOSTAT_GROUP_CODE_MIN"
)
manifest_codes = literal_assignments(
    os.path.join(REPO, "scripts/write_manifest.py"), "FAOSTAT_AGGREGATE_CODES"
)
if os.path.exists(MATCH_R) and manifest_min and manifest_codes:
    with open(MATCH_R, encoding="utf-8") as fh:
        match_src = fh.read()
    # `area_code >= 5000L` and `aggregate_codes <- c(351L)` in R source.
    r_min = re.search(r"area_code\s*>=\s*(\d+)L", match_src)
    r_codes = re.search(r"aggregate_codes\s*<-\s*c\(([^)]*)\)", match_src)
    print(f"\nFAOSTAT group threshold: manifest {manifest_min[0]}", end="")
    if r_min:
        print(f", match.R {r_min.group(1)}")
        if int(r_min.group(1)) != int(manifest_min[0]):
            problems.append(
                f"FAOSTAT group threshold disagrees: write_manifest.py has "
                f"{manifest_min[0]}, match.R has {r_min.group(1)} — the published contract would "
                f"tell consumers a different boundary than the matcher uses"
            )
    else:
        print(" (match.R threshold not found)")
    if r_codes:
        parsed = tuple(
            int(x.strip().rstrip("L"))
            for x in r_codes.group(1).split(",")
            if x.strip()
        )
        print(f"deliberate aggregate codes: manifest {tuple(manifest_codes[0])}, match.R {parsed}")
        if parsed != tuple(manifest_codes[0]):
            problems.append(
                f"deliberate aggregate codes disagree: write_manifest.py has "
                f"{tuple(manifest_codes[0])}, match.R has {parsed}"
            )

# ---------- the wiki's documented vocabulary vs the enforced one ----------
# A third copy of the same fact, in prose. wiki/README.md carries a table of polygon_status
# values, and build_database.py --check points readers at it by name when it rejects a value —
# so if the two disagree, the error message sends people to the wrong list.
#
# It DID disagree. The table described four legacy values as "still present in the database"
# after the migration had removed all of them, because the migration updated the data and the
# gate but not the prose. That is the same defect this script exists for, one medium over.
WIKI_README = os.path.join(REPO, "wiki/README.md")
if vocab and os.path.exists(WIKI_README):
    with open(WIKI_README, encoding="utf-8") as fh:
        readme = fh.read()
    documented = {
        v for v in vocab[0]
        if f"`{v}`" in readme
    }
    missing_from_readme = sorted(set(vocab[0]) - documented)
    print(f"\npolygon_status values documented in wiki/README.md: {len(documented)} of {len(vocab[0])}")
    if missing_from_readme:
        problems.append(
            f"wiki/README.md does not document these enforced polygon_status values: "
            f"{missing_from_readme} — build_database.py --check tells readers to consult that "
            f"table, so it has to be complete"
        )
    # And the removed legacy values must not be described as present.
    for legacy in ("derived", "missing", "approximate", "excluded"):
        if f"`{legacy}`" in readme and "no longer present" not in readme:
            problems.append(
                f"wiki/README.md mentions the legacy value {legacy!r} without saying it has "
                f"been removed"
            )

if problems:
    print(f"\nFAIL: {len(problems)} constant disagreement(s)\n")
    for p in problems:
        print(f"  {p}")
    sys.exit(1)

print("\nPASS: duplicated constants agree, and CLAIMS_POLYGON is the vocabulary "
      "minus 'unassigned'")
