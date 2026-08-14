#!/usr/bin/env python3
"""Check that every component reads `end_year` with the SAME convention.

A polity period is `[start_year, end_year)` — `end_year` is EXCLUSIVE. Issue #131
is what happens when a consumer disagrees: `matchlib.Matcher.pick_by_year` tested
`start <= year <= end`, so at a transition year (predecessor `end_year` ==
successor `start_year`) the ENDED period was a candidate, and in any family with
a third overlapping row it won on list order. Measured on the consolidated
layer-B panel, 12 (label, source, year) tuples carrying 190 rows resolved to a
period that had already ended — every India transition among them.

Nothing errored, and that is the whole problem. Both readings produce a plausible
polity, so a measurement taken across the seam is wrong silently. Issue #77
reported "four territory-years fall in no polity at all"; re-derived against the
matchers only ONE remained, because the other three existed under one reading and
not the other. The count was not a counting mistake, it was a convention mistake.

Three checks:

  A  DECLARATION. Every component that resolves a year against a polity period
     declares `END_YEAR_EXCLUSIVE` and USES it. Same pattern, and same reason, as
     validate_constants.py's DEAD_STATUS check: the convention was re-implemented
     in each program as a bare comparison operator, and an operator cannot be
     compared across files. A name can. A component that declares the constant
     and never reads it is decoration, so the reference count is checked too.

  B  DOCUMENTATION. wiki/README.md — the schema document, and the source of truth
     for what the fields mean — must state the convention, and state the one the
     code implements. Issue #131 asserted the convention was "stated that way in
     wiki/README.md". It was not: the file did not contain the word "exclusive"
     at all, only a dozen individual polity pages did. Documentation that a
     reader is told exists and does not is worse than none.

  C  BEHAVIOUR. For every adjacent period pair in one family (predecessor
     `end_year` == successor `start_year`), asking the matcher for the boundary
     year must not return the predecessor. Declaring a convention and
     implementing the other one is precisely the failure this file is about, so
     the gate does not stop at reading constants.

  D  THE OTHER FIELD. Alias `year_end` is INCLUSIVE, so a consistent pair has
     `end_year == year_end + 1`. That reading was left as a bare comparison
     operator in every component when the polity-side one was named, which is
     issue #131's own complaint one field over — so it is named too
     (`ALIAS_YEAR_END_INCLUSIVE`), declared by matchlib.py and by
     faostat-era-matching/match.R, and checked behaviourally: an alias may put
     data on a period that has already ended ONLY where the alias itself writes
     that year down as its `year_end`. That is a human decision and is honoured.
     A BLANKET alias makes no such decision, and 19 of 903 rules were reaching
     their target's `end_year` through one before this check existed.

Usage:
  python3 scripts/validate_year_semantics.py
"""
import ast
import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipelines/polity-autoimprove"))

POLITIES = os.path.join(REPO, "data/final/polities_database.csv")
ALIASES = os.path.join(REPO, "pipelines/polity-autoimprove/state/applied_aliases.csv")
WIKI_README = os.path.join(REPO, "wiki/README.md")

CONSTANT = "END_YEAR_EXCLUSIVE"
ALIAS_CONSTANT = "ALIAS_YEAR_END_INCLUSIVE"

# Every program that decides which polity a YEAR belongs to. Each must declare
# CONSTANT and read it. `lang` selects the parser: Python via AST (so formatting
# cannot break it), R via literal assignment match (there is no R parser here).
DECLARERS = (
    ("pipelines/polity-autoimprove/matchlib.py", "py"),
    ("pipelines/pre1961-matching/match.R", "r"),
    ("pipelines/faostat-era-matching/match.R", "r"),
)

# The convention itself. Flipping this is a database-wide migration (it changes
# the meaning of all 749 periods and the years embedded in every polity_code),
# not a configuration choice — it lives here so the gate has something to compare
# the components against, not so it can be switched.
EXPECTED = True

# Adjacent boundaries where the predecessor still wins, each with the reason it
# is NOT the issue-#131 defect. Bidirectional: a pair that starts resolving to
# its successor fails this gate until its entry is removed with a note.
#
# Two distinct causes, neither of them the year convention:
#
#   FAMILY UNREACHABLE (9) — the successor is not in the family that
#   `fam_for_code` resolves for the predecessor, so the predecessor is the ONLY
#   candidate at the boundary year and keeping it is correct: dropping it would
#   leave the year with nothing. ANG-1891-1905 carries no iso3 while
#   ANG-1905-1975 carries AGO; the five F228 (Russia) pairs and BRL, SUD, VCT
#   are the same shape. That is a family-reachability defect and belongs to
#   audit_family_shadowing / validate_period_gaps territory, not here.
#
#   TYPE GUARD (3) — the row starting at the boundary is a WORSE polity_type
#   than the row ending there (BMU-1968-2025 is `territory`, SER-1918-1945 and
#   MAN-1945-1950 are `subnational`, against `national`/`city-territory`
#   predecessors). pick_by_year deliberately refuses to move national-scope data
#   onto a narrower row on a date alone — the same guard that stops whole-Ghana
#   1956 data landing on British Togoland. Fixing these means deciding whether
#   the successor's TYPE is right, which is a data judgement, not a matcher one.
BASELINE_EXPIRED_WINS = frozenset({
    ("ANG-1891-1905", 1905),      # family unreachable: successor carries iso3 AGO
    ("BMU-1684-1968", 1968),      # type guard: successor is `territory`
    ("BRL-1938-1945", 1945),      # family unreachable
    # CONCURRENT FAMILY, not a chain. Added 2026-08-14 with CYR-1943-1949 (issue 198). The LBY
    # family holds eleven rows of which four are simultaneous occupation zones -- CYR, TRP and
    # FEZ all run from 1943, alongside the LBY rows -- so at 1949 several rows are live at once
    # and pick_by_year's assumption that a family is a chronology does not hold; the ended BMA
    # row wins on list position.
    #
    # LATENT, and measured rather than assumed: every alias that can reach 1949 already names
    # CYR-1949-1951 (`Libya Cyrenaica`/fao1952 1949-1951, `Cyrenaica`/mitchell 1949, plus two
    # mitchell variants), the 1943-1948 alias stops at 1948, and all 6 observed layer-B rows
    # labelled Cyrenaica at 1949 route to CYR-1949-1951. So no row reaches this path today.
    # Fixing it means teaching pick_by_year that a family can be concurrent, which is a matcher
    # change, not a data one.
    ("CYR-1943-1949", 1949),
    ("F228-1856-1905", 1905),     # family unreachable
    ("F228-1914-1917", 1917),     # family unreachable
    ("F228-1917-1918", 1918),     # family unreachable
    ("F228-1920-1921", 1921),     # family unreachable
    # ("F228-1921-1940", 1940) removed 2026-08-14: it now resolves to its successor, so the
    # entry had become a place for a real regression to hide. It was baselined as "family
    # unreachable"; PR 230 gave the three USSR rows their ISO 3166-3 code SUN, which is what
    # made F228-1940-1945 reachable from the 1940 boundary -- both rows now read SUN. The four
    # F228 entries above are NOT affected and stay: their successors are pre-USSR rows whose
    # iso3 is blank (F228-1905-1914, -1918-1920) or RUS, so no code links them.
    ("MAN-1932-1945", 1945),      # type guard: successor is `subnational`
    ("SER-1913-1918", 1918),      # type guard: successor is `subnational`
    ("SUD-1934-1956", 1956),      # family unreachable
    ("VCT-1800-1833", 1833),      # family unreachable
})

# ---- check D: the alias field, which reads the other way -------------------
# Components that decide whether an ALIAS rule applies to a year, or that
# CONVERT a polity `end_year` into an alias `year_end`. pre1961-matching/match.R
# is deliberately absent: it resolves polities by period only and never touches
# the alias registry's year bounds, so requiring the constant there would be the
# decoration this gate rejects in check A.
ALIAS_DECLARERS = (
    ("pipelines/polity-autoimprove/matchlib.py", "py"),
    ("pipelines/faostat-era-matching/match.R", "r"),
)
ALIAS_EXPECTED = True

# Alias rules that can reach their target's `end_year` — a year the target does
# NOT cover — without naming that year as their own `year_end`. There is no human
# decision to honour in those, so the matcher must fall through to
# year-containment in the family instead of taking the alias's word for it.
#
# Measured before the fix: 219 of 903 rules could reach their target's end_year;
# 200 of them declared `year_end` equal to it (a written decision, honoured — the
# "Libya Tripolitania ...-1951 -> TRP-1943-1951" shape) and 19 did not. Of those
# 19, 18 already resolved to the same code by fallback because their family has no
# period starting at the boundary, so exactly one answer moved: blanket
# "belgian congo" at 1960, from COD-1910-1960 to COD-1960-2025. On the
# consolidated layer-B panel (192,670 rows / 17,599 label-source-year-iso tuples)
# ZERO tuples changed.
#
# Empty, and bidirectional like every baseline here: a rule that starts taking its
# target's boundary year without declaring it fails this gate.
BASELINE_UNDECLARED_ALIAS_WINS = frozenset()


def _py_constant(path: str, CONSTANT: str = CONSTANT):
    """value of CONSTANT in a Python file, plus how many times the name appears."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    value = None
    for node in ast.walk(ast.parse(text, filename=path)):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for t in targets:
            if isinstance(t, ast.Name) and t.id == CONSTANT:
                try:
                    value = ast.literal_eval(node.value)
                except ValueError:
                    value = "(not a literal)"
    return value, len(re.findall(rf"\b{CONSTANT}\b", text))


def _r_constant(path: str, CONSTANT: str = CONSTANT):
    """value of CONSTANT in an R file, plus how many times the name appears."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    value = None
    m = re.search(rf"^{CONSTANT}\s*(?:<-|=)\s*(TRUE|FALSE)\b", text, re.M)
    if m:
        value = m.group(1) == "TRUE"
    return value, len(re.findall(rf"\b{CONSTANT}\b", text))


def check_declarations(DECLARERS=DECLARERS, CONSTANT=CONSTANT, EXPECTED=EXPECTED) -> list:
    problems = []
    for rel, lang in DECLARERS:
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            problems.append(f"{rel}: file missing, cannot compare {CONSTANT}")
            continue
        value, uses = (_py_constant if lang == "py" else _r_constant)(path, CONSTANT)
        if value is None:
            problems.append(
                f"{rel}: does not declare {CONSTANT}. Every component that reads "
                f"this year field must, so the reading can be compared across "
                f"files rather than assumed (issue #131)"
            )
            continue
        if value is not EXPECTED:
            problems.append(
                f"{rel}: {CONSTANT} is {value!r}, expected {EXPECTED!r} — this "
                f"component reads the year field the opposite way from the database"
            )
        if uses < 2:
            problems.append(
                f"{rel}: declares {CONSTANT} but never reads it ({uses} mention). "
                f"A declared-and-ignored constant documents a convention the code "
                f"does not follow, which is the defect, not the fix"
            )
    return problems


def check_documentation() -> list:
    if not os.path.exists(WIKI_README):
        return [f"wiki/README.md missing, cannot verify the documented convention"]
    with open(WIKI_README, encoding="utf-8") as fh:
        text = fh.read()
    stated_exclusive = re.search(
        r"`?end_year`?\s+is\s+\*{0,2}(EXCLUSIVE|exclusive)", text
    )
    stated_inclusive = re.search(
        r"`?end_year`?\s+is\s+\*{0,2}(INCLUSIVE|inclusive)", text
    )
    problems = []
    if EXPECTED and not stated_exclusive:
        problems.append(
            "wiki/README.md does not state that end_year is EXCLUSIVE. It is the "
            "schema document; leaving the convention to individual polity pages is "
            "how issue #131 came to cite a sentence this file never contained"
        )
    if EXPECTED and stated_inclusive:
        problems.append(
            "wiki/README.md says end_year is INCLUSIVE, contradicting "
            f"{CONSTANT}={EXPECTED!r} in the matchers"
        )
    # check D's documentation half. The two fields are only safe to hold different
    # readings if the schema document says BOTH of them and says how they pair;
    # "end_year == year_end + 1" is the sentence a reader needs to convert one to
    # the other without rederiving it, and issues #79/#90 exist because it was
    # rederived, differently, in several places.
    if ALIAS_EXPECTED and not re.search(
        r"`year_end`.{0,300}?\bis\s+\*{0,2}(INCLUSIVE|inclusive)", text, re.S
    ):
        problems.append(
            "wiki/README.md does not state that alias `year_end` is INCLUSIVE, "
            f"while {ALIAS_CONSTANT}={ALIAS_EXPECTED!r} in the matchers. The two "
            "year fields of this repository read opposite ways on purpose; a "
            "schema document that names only one of them is how that becomes a "
            "silent seam (issue #131)"
        )
    if ALIAS_EXPECTED and "end_year == year_end + 1" not in text:
        problems.append(
            "wiki/README.md does not state the pairing `end_year == year_end + 1`. "
            "Without it every consumer converts between the two fields by "
            "rederiving the offset, which is what issues #79 and #90 are"
        )
    return problems


def check_alias_behaviour() -> tuple:
    """(problems, observed) — alias rules that take a boundary year they never claimed.

    An alias `year_end` is INCLUSIVE, so an alias whose `year_end` equals its
    target's `end_year` deliberately asserts a year the target's period (exclusive)
    does not cover. That is a written human decision and the matcher honours it.

    An alias with NO upper bound, or one bounded past that year, asserts nothing
    about the boundary — so honouring it there is not deference to a decision, it
    is the inclusive reading of `end_year` leaking in through the alias path. The
    expected answer in that case is whatever year-containment in the target's
    family gives, which is check C's already-verified `pick_by_year`. Deriving the
    expectation from a different function is what makes this a check rather than a
    restatement of the matcher.
    """
    import matchlib

    if matchlib.ALIAS_YEAR_END_INCLUSIVE is not ALIAS_EXPECTED:
        return ([], frozenset())      # already reported by check_declarations

    m = matchlib.Matcher(POLITIES, applied_aliases_csv=ALIASES, verbose=False)
    observed, detail = set(), {}
    reachable = 0
    for ru in m.override_rules:
        rec = m.code_row.get(ru["code"])
        if rec is None or rec[3] != rec[3] or rec[4] != rec[4]:
            continue                                   # NaN years: schema-contract's job
        end = int(rec[4])
        if not matchlib.alias_covers(ru["y0"], ru["y1"], end):
            continue                                   # the rule cannot be asked about it
        if matchlib.covers(rec[3], rec[4], end):
            continue                                   # unreachable by construction
        reachable += 1
        if ru["y1"] == end:
            continue                                   # written decision: honoured
        got = m.assign(ru["n"], None, ru["src"] or "", end)
        want, _st = m.pick_by_year(m.fam_for_code(ru["code"]), end)
        want_code = want[0] if want is not None else None
        if got is not None and got[0] == ru["code"] and got[0] != want_code:
            key = (ru["n"], ru["src"], end)
            observed.add(key)
            detail[key] = (ru["code"], want_code)

    problems = []
    for key in sorted(observed - BASELINE_UNDECLARED_ALIAS_WINS, key=str):
        code, want_code = detail[key]
        problems.append(
            f"NEW: alias {key[0]!r} (source {key[1]!r}) takes year {key[2]} on "
            f"{code}, whose end_year is {key[2]} so it does not cover it — and the "
            f"alias never declares {key[2]} as its year_end. Year-containment gives "
            f"{want_code}"
        )
    for key in sorted(BASELINE_UNDECLARED_ALIAS_WINS - observed, key=str):
        problems.append(
            f"alias {key[0]!r} (source {key[1]!r}) @ {key[2]} is baselined as taking "
            f"an undeclared boundary year but no longer does — remove it from the "
            f"baseline, with a note saying what was measured"
        )
    print(f"{ALIAS_CONSTANT}: alias rules that can reach their target's end_year: "
          f"{reachable}; taking it without declaring it: {len(observed)} "
          f"(baselined {len(BASELINE_UNDECLARED_ALIAS_WINS)})")
    return problems, observed


def check_behaviour() -> tuple:
    """(problems, observed) — boundary years where the ENDED period still wins."""
    import matchlib

    if matchlib.END_YEAR_EXCLUSIVE is not EXPECTED:
        return ([], frozenset())      # already reported by check_declarations

    m = matchlib.Matcher(POLITIES, applied_aliases_csv=ALIASES, verbose=False)
    with open(POLITIES, encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["polity_code"] in m.valid_codes]

    families = {}
    for r in rows:
        try:
            s, e = int(r["start_year"]), int(r["end_year"])
        except (TypeError, ValueError):
            continue        # unparseable years are validate_schema_contract's job
        families.setdefault(r["polity_code"].rsplit("-", 2)[0], []).append((s, e, r))

    observed, detail = set(), {}
    for periods in families.values():
        starts = {}
        for s, _e, r in periods:
            starts.setdefault(s, []).append(r["polity_code"])
        for _s, e, r in periods:
            if e not in starts:
                continue                       # no adjacent successor: nothing to test
            rec, _st = m.pick_by_year(m.fam_for_code(r["polity_code"]), e)
            if rec is not None and rec[0] == r["polity_code"]:
                observed.add((r["polity_code"], e))
                detail[(r["polity_code"], e)] = starts[e]

    problems = []
    for key in sorted(observed - BASELINE_EXPIRED_WINS):
        problems.append(
            f"NEW: {key[0]} still wins its own boundary year {key[1]}, but "
            f"end_year is EXCLUSIVE so it does not cover it — "
            f"{', '.join(detail[key])} starts there"
        )
    for key in sorted(BASELINE_EXPIRED_WINS - observed):
        problems.append(
            f"{key[0]} @ {key[1]} is baselined as an expired-period win but now "
            f"resolves to its successor — remove it from the baseline, with a note "
            f"saying what was measured"
        )
    return problems, observed


def main() -> int:
    problems = check_declarations() + check_documentation()
    problems += check_declarations(ALIAS_DECLARERS, ALIAS_CONSTANT, ALIAS_EXPECTED)

    print(f"{CONSTANT}: components declaring it {len(DECLARERS)}, expected {EXPECTED!r}")
    for rel, lang in DECLARERS:
        path = os.path.join(REPO, rel)
        if os.path.exists(path):
            value, uses = (_py_constant if lang == "py" else _r_constant)(path)
            print(f"  {rel}: {value!r} ({uses} mention(s))")
    print(f"{ALIAS_CONSTANT}: components declaring it {len(ALIAS_DECLARERS)}, "
          f"expected {ALIAS_EXPECTED!r}")
    for rel, lang in ALIAS_DECLARERS:
        path = os.path.join(REPO, rel)
        if os.path.exists(path):
            value, uses = (_py_constant if lang == "py" else _r_constant)(
                path, ALIAS_CONSTANT)
            print(f"  {rel}: {value!r} ({uses} mention(s))")

    behaviour, observed = check_behaviour()
    problems += behaviour
    print(f"adjacent boundaries where the ended period still wins: {len(observed)} "
          f"(baselined {len(BASELINE_EXPIRED_WINS)})")
    alias_behaviour, _alias_observed = check_alias_behaviour()
    problems += alias_behaviour

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1
    print("\nPASS: both year conventions declared by every component that reads "
          "them, documented together with how they pair, and implemented")
    return 0


if __name__ == "__main__":
    sys.exit(main())
