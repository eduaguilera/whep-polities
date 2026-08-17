#!/usr/bin/env python3
"""The matcher's LOGIC runs in CI, on a committed synthetic fixture.

WHY THIS EXISTS (issue 17). Every program that decides which polity a source label
belongs to reads inputs that are NOT in this repository and are not redistributable:

    WHEP_LAYERB        ~/Nextcloud/.../consolidated_layer_b.parquet   (190k rows)
    WHEP_COMMON_NAMES  ~/Nextcloud/.../common_names.csv
    WHEP_REPO          a WHEP R-package checkout, for the FAOSTAT pins cache

So `01_match_and_findings.py`, `00_intake.py` and the two `match.R` scripts cannot run in
CI, and until now nothing exercised the matching RULES there. What CI did have was
`crosscheck_matchers.py`, which since issue 16 pins 19 golden routes — but every one of
them is a route through the REAL polities database, so each asserts the rules AND the
current 1,073-row database at once. When a period is re-spanned the fixture entry has to
be re-derived, and a rule regression and a legitimate database edit look the same.

This gate separates the two halves. It owns a SYNTHETIC 22-row database and an 8-rule
synthetic alias registry (`tests/fixtures/matcher/`), invented labels and all, in which
each of matchlib's decision rules is reproduced in its smallest form. Nothing here moves
when the real database moves, so a failure is always a change in the RULES.

Three checks, in order of what they protect:

  A. REGISTRY LOADING — how many alias rules survive, which are blanket, which are stale
     (target withdrawn) and which pairs are reported ambiguous. Silent drops are the
     failure mode: a rule aimed at a code that does not exist is discarded without a word.

  B. ROUTING — one case per rule matchlib documents, with the real defect each was written
     against named beside it. The exclusive `end_year` and its two guards (uniqueness,
     polity_type), the dead-status exclusion for BOTH dead statuses, the alias
     specificity order, the half-open alias bound, the honoured boundary year, token-set
     name equality.

  C. THE INTAKE PATH ACTUALLY EXECUTES — `00_intake.py` is run as a subprocess over a
     committed 11-row input, which is the half of issue 17 a pure unit fixture does not
     cover: the pipeline entry point itself, argument parsing, ledger comparison, evidence
     hashing and bundle shape. That run uses the REAL database (00_intake resolves it from
     its own path and offers no override), so it asserts STRUCTURE and invariants — every
     candidate is a live code, every bundle carries a 16-hex evidence_hash, the deliberately
     unresolvable label lands in `unresolved` — and never a specific code, which is exactly
     the coupling check A/B exist to avoid.

THE COVERAGE IS NEW, MEASURED RATHER THAN ASSUMED. Two mutations of matchlib were tried
against both gates. Removing the alias specificity tie-break (`-span`) is caught by BOTH
this gate and `crosscheck_matchers` — so on that one this gate is a cheaper, database-
independent report of the same fact. Keying `bounded` on `y0` alone, i.e. putting back the
half-open bound defect where a rule bounded only ABOVE matched every year, is caught HERE
(the `old kingdom` 2000 case answers SAR-1960-2025) and `crosscheck_matchers` PASSES it
with its agreement and all 19 golden routes intact. That second mutation is the argument
for this file existing.

Deliberately NOT covered, and worth stating plainly: the two R matchers. CI has no R
toolchain, so `pipelines/*/match.R` are still checked only by source text
(`crosscheck_matchers.check_dead_status_declared`). A fixture cannot fix that; a runner
with R can. Issue 16's finding — pre1961-matching/match.R routing 15,526 rows onto dead
polities — was in the half of the code this gate still cannot execute.
"""
import csv
import json
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipelines/polity-autoimprove"))

FIXTURES = os.path.join(REPO, "tests/fixtures/matcher")
FIX_POLITIES = os.path.join(FIXTURES, "polities.csv")
FIX_ALIASES = os.path.join(FIXTURES, "aliases.csv")
FIX_INTAKE = os.path.join(FIXTURES, "intake_input.csv")
INTAKE = os.path.join(REPO, "pipelines/polity-autoimprove/00_intake.py")
REAL_POLITIES = os.path.join(REPO, "data/final/polities_database.csv")

# --- A. what loading the registry must produce -------------------------------------
# The fixture registry has EIGHT rows and only SIX may survive: one targets a `retired`
# polity (stale) and one targets a code that does not exist (unknown). Both are dropped
# silently by matchlib, which is why they are counted here rather than trusted.
EXPECT_RULES = 6
EXPECT_BLANKET = 2          # `riverland colony state` and the un-sourced `twinpeak`
EXPECT_STALE = {"GHO-1800-2025": 1}
EXPECT_AMBIGUOUS_LABELS = {"hinterland"}

# --- B. routing cases --------------------------------------------------------------
# (label, iso, source, year, expected_code, expected_status, expected_how, why)
# `expected_code` None means the resolver must refuse. Every `why` names the real defect
# the rule was written against, so a failure here reads as a rule regression and not as a
# fixture that needs its numbers refreshed.
CASES = (
    ("Alpina", "XAA", None, 1849, "ALP-1800-1850", "matched", "iso",
     "an ordinary year inside one period"),
    ("Alpina", "XAA", None, 1850, "ALP-1850-1900", "matched", "iso",
     "the shared transition year belongs to the SUCCESSOR: end_year is exclusive "
     "(issue 131, 12 layer-B tuples / 190 rows resolved to a period that had ended)"),
    ("Alpina", "XAA", None, 1900, "ALP-1850-1900", "matched", "iso",
     "the LAST year of the family, where nothing starts: the ended period is KEPT, "
     "because a strictly exclusive gather instead loses 13 tuples / 83 rows outright"),
    ("Echo", "XAD", None, 1949, "ECH-1900-1949", "matched", "iso",
     "the UNIQUENESS guard: two `national` rows start in 1949, so 'the successor' is "
     "not a fact and family order would decide it (real case: Libya 1949, CYR vs LBY)"),
    ("Delta", "XAC", None, 1950, "DEL-1900-1950", "matched", "iso",
     "the TYPE guard: the only row starting in 1950 is a `territory`, so whole-Delta "
     "data must not move onto it (real case: Ghana 1956 vs British Togoland)"),
    ("Ghostland", "XAE", None, 1920, "GHO-1900-1950", "matched", "iso",
     "a RETIRED all-years `national` row must not outrank its live successor "
     "(real case: ARG-1800-2025 taking 3,356 rows, issue 16)"),
    ("Supland", "XAL", None, 1920, "SUP-1900-1950", "matched", "iso",
     "the same for SUPERSEDED, the second dead status, so deleting either word fails"),
    ("South Islandias", None, None, 1950, "SIS-1900-2000", "matched", "tokenset",
     "order-insensitive, singularised token equality resolves a name no exact match "
     "would reach ('Korea South' == 'South Korea')"),
    ("hinterland", None, None, 1935, "HIN-1930-1940", "matched", "applied_alias",
     "among equally-scoped alias rules the NARROWER year range wins. Without that "
     "tie-break the winner is position in the CSV, and the fixture puts the broad rule "
     "first: a broad 1919-1956 rule silently beat a specific 1949-1951 one on the real "
     "registry"),
    ("hinterland", None, None, 1970, "HIN-1900-1980", "matched", "applied_alias",
     "and outside the narrow rule's range the broad one still applies"),
    ("old kingdom", None, None, 1850, "SAR-1800-1860", "matched", "applied_alias",
     "a rule bounded only ABOVE applies below its bound"),
    ("old kingdom", None, None, 1860, "SAR-1800-1860", "matched", "applied_alias",
     "alias `year_end` is INCLUSIVE, so a rule naming the target's own end_year is "
     "honoured there — a human wrote that year down (real case: Tripolitania 1951)"),
    ("old kingdom", None, None, 2000, None, "unresolved", "none",
     "and a MISSING LOWER BOUND IS NOT BLANKET: this used to skip the year test "
     "entirely, so IIA data labelled `italy` resolved to Sardinia in the year 2000. The "
     "fixture family carries a LATER period (SAR-1960-2025) on purpose: without one the "
     "regression hides behind the fall-through, which answers year_uncovered and then "
     "unresolved either way — measured, that is exactly what happened to the first "
     "version of this case"),
    ("riverland colony state", None, None, 1950, "RIV-1910-1960", "matched",
     "applied_alias", "a blanket alias inside its target's span"),
    ("riverland colony state", None, None, 1960, "RIV-1960-2025", "matched",
     "applied_alias",
     "a BLANKET alias makes no claim about a boundary year, so the target's exclusive "
     "end_year applies and the year falls through to the row that starts there (real "
     "case: `belgian congo` at 1960, the one route that moved)"),
    ("twinpeak", None, "fixsrc", 1950, "TWB-1900-2000", "matched", "applied_alias",
     "a SOURCE-scoped rule beats a blanket one"),
    ("twinpeak", None, "othersrc", 1950, "TWA-1900-2000", "matched", "applied_alias",
     "and for any other source the blanket rule still applies"),
    ("ghost route", None, None, 1920, None, "unresolved", "none",
     "a rule whose target is withdrawn is DROPPED, and the label then resolves to "
     "nothing rather than to a dead polity"),
    ("Nowhereland", None, None, 1900, None, "unresolved", "none",
     "an unknown label routes nowhere, which is what makes an unresolved count real"),
    ("Alpina", "XAA", None, 2200, None, "year_uncovered", "iso",
     "a year well past the family's end is refused. The contrast with 1900 above is the "
     "whole subtlety: the ended period is kept only at its own end_year, where the "
     "inclusive gather still reaches it, and not for every later year"),
    ("Alpina", "XAA", None, 1700, None, "year_uncovered", "iso",
     "a year before the family begins is refused, not rounded to the first period"),
)

# --- C. what the intake run must produce ------------------------------------------
# Structure only, plus the ONE routing fact the fixture input was built to force: a label
# that exists in no family must be reported unresolved rather than absorbed.
INTAKE_UNRESOLVED_LABEL = "Nowhereland"
INTAKE_MIN_ROUTE_PCT = 50.0
STATUS_VOCAB = {"pending", "reopened", "banked"}


def check_registry(matchlib) -> tuple:
    """A. loading the fixture registry drops exactly the rules it should."""
    problems = []
    m = matchlib.Matcher(FIX_POLITIES, applied_aliases_csv=FIX_ALIASES, verbose=False)
    n = len(m.override_rules)
    if n != EXPECT_RULES:
        problems.append(
            f"fixture registry: {n} alias rule(s) loaded, expected {EXPECT_RULES} — a "
            f"rule was silently dropped or a dropped rule was silently kept"
        )
    if len(m.blanket_override) != EXPECT_BLANKET:
        problems.append(
            f"fixture registry: {len(m.blanket_override)} blanket rule(s), expected "
            f"{EXPECT_BLANKET}. A rule bounded on one side only must NOT count as "
            f"blanket: that is what made an alias bounded at 1860 match the year 2000"
        )
    if dict(m.stale_alias_targets) != EXPECT_STALE:
        problems.append(
            f"fixture registry: stale alias targets {dict(m.stale_alias_targets)}, "
            f"expected {EXPECT_STALE} — a rule aimed at a withdrawn polity must be "
            f"dropped AND counted, since GHO-1800-2025 spans every year as `national`"
        )
    labels = {p[0] for p in m.ambiguous_alias_pairs}
    if labels != EXPECT_AMBIGUOUS_LABELS:
        problems.append(
            f"fixture registry: ambiguous alias labels {sorted(labels)}, expected "
            f"{sorted(EXPECT_AMBIGUOUS_LABELS)}. The report is what tells a maintainer "
            f"two equal-specificity rules overlap; the narrower-range tie-break decides "
            f"which wins, but silence would hide the pair"
        )
    if not problems:
        print(
            f"A. fixture registry: {n} rules ({len(m.blanket_override)} blanket), "
            f"1 stale target dropped, 1 unknown target dropped, "
            f"{len(m.ambiguous_alias_pairs)} ambiguous pair reported"
        )
    return m, problems


def check_routing(m) -> list:
    """B. every documented rule still decides the case it was written for."""
    problems = []
    for label, iso, source, year, expect, expect_status, expect_how, why in CASES:
        code, status, how = m.assign(label, iso, source, year)
        where = f"{label!r} [{source or 'any source'}] {year}"
        if code != expect:
            problems.append(
                f"{where}: expected {expect}, matcher returned {code} "
                f"(status={status}, route={how}). This case protects: {why}"
            )
        elif status != expect_status or how != expect_how:
            problems.append(
                f"{where}: right answer {code} by the WRONG ROUTE — expected "
                f"status={expect_status} route={expect_how}, got status={status} "
                f"route={how}. A rule reached by accident is not a rule. Case: {why}"
            )
    if not problems:
        print(f"B. routing: {len(CASES)}/{len(CASES)} fixture cases resolve as documented")
    return problems


def check_intake_runs() -> list:
    """C. 00_intake.py executes end to end on a committed input, in CI."""
    problems = []
    if not os.path.exists(INTAKE):
        return [f"{os.path.relpath(INTAKE, REPO)} is missing, so the intake path cannot "
                f"be exercised at all"]
    out = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    out.close()
    proc = subprocess.run(
        [sys.executable, INTAKE,
         "--input", FIX_INTAKE, "--label-col", "country", "--year-col", "year",
         "--iso-col", "iso3", "--item-col", "item", "--value-col", "value",
         "--unit-col", "unit", "--source-col", "source", "--out", out.name],
        capture_output=True, text=True, timeout=600,
    )
    if proc.returncode != 0:
        os.unlink(out.name)
        return [
            "00_intake.py FAILED on the committed fixture input, so the intake path "
            f"does not run in CI (exit {proc.returncode}):\n"
            + ((proc.stdout or "") + (proc.stderr or ""))[-1500:]
        ]
    try:
        got = json.load(open(out.name, encoding="utf-8"))
    except (OSError, ValueError) as exc:
        os.unlink(out.name)
        return [f"00_intake.py exited 0 but wrote no readable assertions JSON ({exc})"]
    os.unlink(out.name)

    live = {
        r["polity_code"]
        for r in csv.DictReader(open(REAL_POLITIES, encoding="utf-8"))
        if (r.get("wiki_status") or "").strip() not in ("retired", "superseded")
    }
    summary = got.get("summary") or {}
    assertions = got.get("assertions") or []
    if not assertions:
        problems.append(
            "00_intake.py produced ZERO assertions from the fixture input, so exiting 0 "
            "proves nothing about the matcher"
        )
    if float(summary.get("route_pct") or 0) < INTAKE_MIN_ROUTE_PCT:
        problems.append(
            f"00_intake.py routed only {summary.get('route_pct')}% of the fixture rows "
            f"(floor {INTAKE_MIN_ROUTE_PCT}%): the fixture's labels are ordinary ones, so "
            f"this is a routing regression, not a fixture that has gone stale"
        )
    for a in assertions:
        code = a.get("candidate")
        if code not in live:
            problems.append(
                f"00_intake.py routed {a.get('label_raw')!r} to {code}, which is not a "
                f"live polity — the #244 orphan failure, reached through the intake path"
            )
        h = str(a.get("evidence_hash") or "")
        if len(h) != 16 or any(c not in "0123456789abcdef" for c in h):
            problems.append(
                f"assertion {a.get('key')!r} carries evidence_hash {h!r}, not 16 hex "
                f"digits: without it nothing can detect that the evidence has moved"
            )
        if a.get("status") not in STATUS_VOCAB:
            problems.append(
                f"assertion {a.get('key')!r} has status {a.get('status')!r}, outside the "
                f"vocabulary the verification workflow selects on ({sorted(STATUS_VOCAB)})"
            )
    unresolved = {u.get("entity") for u in (got.get("unresolved") or [])}
    if INTAKE_UNRESOLVED_LABEL not in unresolved:
        problems.append(
            f"the fixture's deliberately unroutable label {INTAKE_UNRESOLVED_LABEL!r} is "
            f"not in the intake run's `unresolved` list ({sorted(unresolved)}), so either "
            f"it was absorbed by some family or unresolved rows are not being reported"
        )
    if not problems:
        print(
            f"C. intake path: 00_intake.py ran on {summary.get('rows')} fixture rows, "
            f"routed {summary.get('route_pct')}%, emitted {len(assertions)} assertion "
            f"bundle(s), {len(got.get('unresolved') or [])} unresolved label(s)"
        )
    return problems


def check_helpers(matchlib) -> list:
    """The normalisation the whole crosswalk is keyed on, pinned by example."""
    problems = []
    for got, want, why in (
        (matchlib.norm("The Gambia (to 1919)"), "gambia",
         "a leading article, a parenthetical and case must all normalise away, or one "
         "spelling of a label becomes two assertions"),
        (matchlib.norm("Côte d'Ivoire"), "cote d ivoire",
         "accents fold to ASCII and punctuation becomes a space"),
        (matchlib.toks("Korea, South"), matchlib.toks("South Korea"),
         "token-set equality is order-insensitive"),
        (matchlib.eff_year(float("nan"), "1934-1938"), 1938,
         "a period-average label resolves to its END year, which is the year the "
         "matcher then tests for containment"),
    ):
        if got != want:
            problems.append(f"normalisation changed: got {got!r}, expected {want!r} — {why}")
    if not problems:
        print("   helpers: norm/toks/eff_year pinned by example")
    return problems


def main() -> int:
    for path in (FIX_POLITIES, FIX_ALIASES, FIX_INTAKE):
        if not os.path.exists(path):
            print(f"FAIL: fixture {os.path.relpath(path, REPO)} is missing, so nothing "
                  f"about the matcher is checked here")
            return 2
    try:
        import matchlib
    except ImportError as exc:
        print(f"FAIL: cannot import matchlib ({exc})")
        return 2

    problems = []
    m, probs = check_registry(matchlib)
    problems += probs
    problems += check_routing(m)
    problems += check_helpers(matchlib)
    problems += check_intake_runs()

    if problems:
        print(f"\nFAIL: {len(problems)} matcher-fixture problem(s)")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("PASS: the matcher's rules and the intake path both run in CI, on committed "
          "fixtures that do not move when the database does")
    return 0


if __name__ == "__main__":
    sys.exit(main())
