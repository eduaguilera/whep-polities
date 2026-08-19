#!/usr/bin/env python3
"""Validate the source-conventions registry, because every verifier inherits it.

`pipelines/polity-autoimprove/state/source_conventions.csv` records what a source's
labels and series ACTUALLY measure — IIA "Russian Federation" is the whole USSR, IIA
green coffee under `djibouti` is Ethiopian transit, juan's 1949-1960 "germany" has no
FRG/GDR split. `00_intake.py` attaches every matching entry to the evidence bundle of
every assertion touching that source, so a convention is not one opinion about one row:
it is a PREMISE handed to every later verifier, and one that is wrong or dead propagates
further than any single verdict can.

Issue 24: nothing checked them. Polygons, citations, aliases and flow flags all have
gates; the file that seeds the reasoning behind them had none. The FAO-1952 population
entry is the standing proof — recorded as a firm "about a third of the total" finding,
inherited by every bundle that touched fao1952, and corrected to a five-indicator
explanation only because a human went back and re-measured it.

WHAT THIS CHECKS (structure and reachability — all of it from tracked files, so it runs
in CI):

  A  header and row shape. The registry is APPENDED TO BY SCRIPT
     (`apply_verdicts.py`), and a writer that knows fewer columns than the file has
     silently produces a short row whose `flow_type` reads back as empty — which
     `write_source_flow_flags.py` then treats as `production`, publishing no flag for a
     known double count. A missing column is not a formatting nit here.
  B  required fields present and non-trivial: an entry with no `evidence` is an
     assertion propagating on its own authority.
  C  dates: `verified` and `retested` are ISO dates, not in the future.
  D  reachability. A `label_pattern` that matches NO label the source actually carries
     attaches to nothing: it looks recorded and propagates nowhere. Checked against the
     (source, label) pairs in the review ledger, which is the tracked record of the
     labels intake really saw.
  E  flow_type vocabulary, and `origin_iso3` present exactly when the flow is not
     production — the column a consumer needs to know whose output the figures
     duplicate.
  F  corroboration. The issue's rule: a convention needs two independent
     corroborators before it is registered, mirroring the blind-review requirement for
     verdicts. Entries below that bar must be named in SINGLE_CORROBORATOR_BASELINE
     with the reason, so passive growth cannot add another silently.
  G  re-test coverage. Every row must have a check in
     `pipelines/polity-autoimprove/11_retest_conventions.py`, which re-runs the
     measurement behind it against the layer-B panel. That script cannot run in CI (the
     panel is gitignored), but whether a row is COVERED by it is checkable here, and
     that is what stops the registry growing entries nothing re-tests.

WHAT THIS DELIBERATELY DOES NOT CHECK: whether a convention is TRUE. That needs the
layer-B panel and lives in 11_retest_conventions.py, run by hand and recorded in the
`retest` column. A stale re-test (older than STALE_DAYS) is reported as a WARNING and
does not fail: a gate that turns red on a date with no code change teaches people to
ignore it, and the registry is not the place to spend that credibility.

Usage:
  python3 scripts/validate_source_conventions.py
Exit 1 if any entry is malformed, dead, uncorroborated or un-re-tested.
"""
import csv
import datetime
import importlib.util
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(REPO, "pipelines/polity-autoimprove/state/source_conventions.csv")
LEDGER = os.path.join(REPO, "pipelines/polity-autoimprove/state/review_ledger.csv")
RETEST = os.path.join(REPO, "pipelines/polity-autoimprove/11_retest_conventions.py")
POLDB = os.path.join(REPO, "data/final/polities_database.csv")

# The exact column set, in order. Asserted rather than tolerated: see check A.
COLUMNS = (
    "source", "label_pattern", "item_pattern", "convention", "evidence",
    "verified", "verified_by", "flow_type", "origin_iso3",
    "corroboration", "retested", "retest",
)
REQUIRED = (
    "source", "label_pattern", "item_pattern", "convention", "evidence",
    "verified", "verified_by", "corroboration", "retested", "retest",
)
# An entry short enough to be a label rather than an argument cannot be audited later.
MIN_EVIDENCE = 80
MIN_CONVENTION = 40

# `dependency_output` added 2026-08-19 (issue 372): a colony/dependency's MINED output published
# under the administering power's label. Distinct from `entrepot_transit`, which is goods moving
# THROUGH a port -- nothing transits here, the rock is dug on the dependency and reported by the
# metropole. Both are non-production, so check E's origin_iso3 requirement applies unchanged.
FLOW_TYPES = frozenset({"production", "entrepot_transit", "dependency_output"})

# How a convention earned its place. Two independent corroborators is the bar; the
# vocabulary is closed so "corroborated" cannot be asserted in free prose.
CORROBORATION = {
    "two_independent_verifiers": True,     # two blind verifiers reached it separately
    "verifier_plus_measurement": True,     # a verdict plus an independent re-measurement
    "verifier_plus_external_source": True, # a verdict plus documentary evidence outside the panel
    "single_verifier": False,              # one agent, one pass — below the bar
}

# Entries recorded before the two-corroborator rule existed and still below it.
# BIDIRECTIONAL: corroborate one and this gate fails until its entry is deleted.
# EVERY BASELINE MUST BE A frozenset({...}), NOT A BARE {...}.
SINGLE_CORROBORATOR_BASELINE = frozenset({
    # iia "south korea" = the whole Japanese-era peninsula. Re-measured 2026-08-17 and
    # the magnitudes hold (soybean area median 786,278 ha; 'south korea' is the only
    # Korean label iia carries), but that measurement and the original verifier's are
    # the SAME instrument on the SAME panel, so it is not a second independent
    # corroborator. What would clear it: a documentary check that the IIA yearbooks
    # tabulate Chosen as one unit, or a second verifier reaching it blind.
    ("iia", "south korea", "*"),
})

# Re-tests older than this are reported, not failed. See the module docstring.
STALE_DAYS = 400


def norm(s) -> str:
    """00_intake.py's normalisation — the gate must match the consumer's matching."""
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def ledger_pairs() -> set:
    """(source, normalised label) pairs the intake step really produced.

    Read from the review ledger because its keys are `label|source|years` — the tracked
    record of what intake matched. The published alias map is NOT usable for this: it
    carries only the labels that needed an explicit alias (5 juan rows, 30 iia), so a
    perfectly live label like juan "finland" is absent from it and would read as dead.
    """
    if not os.path.exists(LEDGER):
        return set()
    out = set()
    with open(LEDGER, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            parts = (row.get("key") or "").split("|")
            if len(parts) >= 2:
                out.add((parts[1].strip().lower(), norm(parts[0])))
    return out


def retest_keys() -> set:
    """The (source, label_pattern, item_pattern) keys 11_retest_conventions.py covers."""
    if not os.path.exists(RETEST):
        return set()
    spec = importlib.util.spec_from_file_location("retest_conventions", RETEST)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)                  # imports pandas lazily, inside main()
    return set(getattr(mod, "CHECKS", {}))


def alias_labels():
    """Which (source, lowercased label) pairs the PUBLISHED alias map can resolve to a polity.

    Read from data/final/label_alias_map.csv because that is exactly the file
    write_source_flow_flags.py resolves polity_code from -- checking against anything else would
    let a flag pass here and still publish empty.
    """
    path = os.path.join(REPO, "data/final/label_alias_map.csv")
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("polity_code"):
                out.setdefault((row.get("source") or "").strip(), set()).add(
                    (row.get("source_label") or "").strip().lower())
    return out


def iso3_codes() -> set:
    if not os.path.exists(POLDB):
        return set()
    with open(POLDB, encoding="utf-8") as fh:
        return {(r.get("iso3_code") or "").strip().upper()
                for r in csv.DictReader(fh)} - {""}


def main() -> int:
    if not os.path.exists(REGISTRY):
        print(f"FAIL — {os.path.relpath(REGISTRY, REPO)} is missing; every verifier "
              f"then starts from nothing and re-derives what was already settled")
        return 1

    fails, warns = [], []

    # --- A: header and row shape ---
    with open(REGISTRY, encoding="utf-8") as fh:
        reader = csv.DictReader(fh, restkey="__extra__", restval="__missing__")
        header = tuple(reader.fieldnames or ())
        rows = list(reader)
    if header != COLUMNS:
        missing = [c for c in COLUMNS if c not in header]
        extra = [c for c in header if c not in COLUMNS]
        fails.append(
            f"header is {list(header)}, expected {list(COLUMNS)}"
            + (f"; missing {missing}" if missing else "")
            + (f"; unexpected {extra}" if extra else "")
            + " — a column a writer does not know about becomes an empty field, and an "
              "empty flow_type publishes a known double count as production"
        )
    for i, r in enumerate(rows, start=2):
        short = sorted(k for k, v in r.items() if v == "__missing__")
        if short:
            fails.append(
                f"line {i} ({r.get('source')}/{r.get('label_pattern')}) has "
                f"{len(short)} fewer field(s) than the header: {short} read back as "
                f"empty. A short row is how a script that knows an older column set "
                f"appends — check apply_verdicts.py writes every column in COLUMNS"
            )
        if r.get("__extra__"):
            fails.append(f"line {i} has {len(r['__extra__'])} field(s) beyond the header")

    pairs = ledger_pairs()
    known_sources = {s for s, _ in pairs}
    covered = retest_keys()
    isos = iso3_codes()
    aliases = alias_labels()
    today = datetime.date.today()

    for i, r in enumerate(rows, start=2):
        key = (r.get("source") or "", r.get("label_pattern") or "",
               r.get("item_pattern") or "")
        who = f"line {i} {key[0]}/{key[1]}/{key[2]}"

        # --- B: required fields, and enough of them to audit ---
        for col in REQUIRED:
            if not (r.get(col) or "").strip() or r.get(col) == "__missing__":
                fails.append(f"{who}: `{col}` is empty")
        conv, ev = (r.get("convention") or ""), (r.get("evidence") or "")
        if 0 < len(conv.strip()) < MIN_CONVENTION:
            fails.append(f"{who}: `convention` is {len(conv)} chars, under "
                         f"{MIN_CONVENTION} — a premise every verifier inherits has to "
                         f"say what it means")
        if 0 < len(ev.strip()) < MIN_EVIDENCE:
            fails.append(f"{who}: `evidence` is {len(ev)} chars, under {MIN_EVIDENCE} "
                         f"— an unevidenced convention propagates on its own authority")

        # --- C: dates ---
        for col in ("verified", "retested"):
            val = (r.get(col) or "").strip()
            if not val or val == "__missing__":
                continue
            try:
                d = datetime.date.fromisoformat(val)
            except ValueError:
                fails.append(f"{who}: `{col}` = {val!r} is not an ISO date")
                continue
            if d > today:
                fails.append(f"{who}: `{col}` = {val} is in the future")
            elif col == "retested" and (today - d).days > STALE_DAYS:
                warns.append(f"{who}: last re-tested {val}, {(today - d).days} days ago "
                             f"— rerun 11_retest_conventions.py")

        # --- D: reachability ---
        if key[0] and pairs and key[0] not in known_sources:
            fails.append(f"{who}: source {key[0]!r} appears in no ledger key, so no "
                         f"bundle can ever carry this convention "
                         f"(sources seen: {sorted(known_sources)})")
        elif key[1] not in ("", "*") and pairs:
            lp = norm(key[1])
            if not any(s == key[0] and lp in lab for s, lab in pairs):
                fails.append(
                    f"{who}: label_pattern {key[1]!r} matches no {key[0]} label in the "
                    f"review ledger — 00_intake.py attaches by normalised substring, so "
                    f"this convention attaches to NOTHING. Re-point it at the label the "
                    f"source now carries, or delete it"
                )

        # --- E: flow vocabulary and origin ---
        flow = (r.get("flow_type") or "").strip()
        if flow and flow not in FLOW_TYPES:
            fails.append(f"{who}: flow_type {flow!r} not in {sorted(FLOW_TYPES)} — "
                         f"write_source_flow_flags.py publishes anything that is not "
                         f"`production`, so a typo publishes a flag no consumer knows")
        origin = (r.get("origin_iso3") or "").strip()
        if flow and flow != "production" and not origin:
            fails.append(f"{who}: flow_type {flow!r} with no origin_iso3 — a consumer "
                         f"can see the rows are not production and not whose they are")
        # A non-production flow PUBLISHES a row into data/final/source_flow_flags.csv, and
        # write_source_flow_flags.py resolves its polity_code from the ALIAS MAP. A label that
        # reaches its polity by iso/name matching has no alias row, so the published flag carries
        # an EMPTY polity_code -- and 05_magnitude_screen.py joins on (source, polity_code, item),
        # so it can never match. That is an INERT flag in a published file, which is worse than no
        # flag: it reads as a recorded decision and does nothing. Found 2026-08-19 while registering
        # the iia/australia phosphate finding (issue 372), which is why that one is recorded in
        # `convention` prose instead of being published.
        lp = (r.get("label_pattern") or "").strip()
        if flow and flow != "production" and lp and lp != "*":
            src = (r.get("source") or "").strip()
            if lp.lower() not in aliases.get(src, frozenset()):
                fails.append(
                    f"{who}: flow_type {flow!r} publishes a flow flag, but {lp!r} has no row in "
                    f"data/final/label_alias_map.csv for source {src!r}, so "
                    f"write_source_flow_flags.py resolves an EMPTY polity_code and "
                    f"05_magnitude_screen.py can never join it - an inert flag in a published "
                    f"file. Add the alias, or record the finding in `convention` prose with no "
                    f"flow_type")
        if flow == "production" and origin:
            fails.append(f"{who}: origin_iso3 {origin!r} on a `production` row, which "
                         f"is never published; the convention says these ARE its output")
        if origin and isos and origin.upper() not in isos:
            fails.append(f"{who}: origin_iso3 {origin!r} is no iso3_code in the database")

        # --- F: corroboration ---
        corr = (r.get("corroboration") or "").strip()
        if corr and corr not in CORROBORATION:
            fails.append(f"{who}: corroboration {corr!r} not in "
                         f"{sorted(CORROBORATION)}")
        elif corr and not CORROBORATION[corr] and key not in SINGLE_CORROBORATOR_BASELINE:
            fails.append(
                f"{who}: corroboration is `{corr}` and the entry is not in "
                f"SINGLE_CORROBORATOR_BASELINE. A convention is inherited by every "
                f"verifier touching {key[0]}, so it needs two independent corroborators "
                f"(a second blind verifier, an independent re-measurement, or a "
                f"documentary source) before it is registered — or an explicit baseline "
                f"entry saying why it stands on one"
            )
        if key in SINGLE_CORROBORATOR_BASELINE and CORROBORATION.get(corr):
            fails.append(
                f"{who}: baselined as single-corroborator but now records `{corr}`. "
                f"Delete its SINGLE_CORROBORATOR_BASELINE entry, leaving a comment "
                f"saying what corroborated it"
            )

        # --- G: re-test coverage ---
        if covered and key not in covered:
            fails.append(
                f"{who}: no check in pipelines/polity-autoimprove/11_retest_conventions.py "
                f"covers this entry, so nothing re-measures it. Add one to CHECKS keyed "
                f"exactly ({key[0]!r}, {key[1]!r}, {key[2]!r})"
            )
    if not covered:
        fails.append(
            "pipelines/polity-autoimprove/11_retest_conventions.py exposes no CHECKS, so "
            "re-test coverage cannot be verified for any entry"
        )
    orphans = sorted(covered - {(r.get("source"), r.get("label_pattern"),
                                 r.get("item_pattern")) for r in rows})
    for k in orphans:
        warns.append(f"11_retest_conventions.py defines a check for {k}, which the "
                     f"registry no longer carries")

    print(f"{len(rows)} registered convention(s) over {len(known_sources)} source(s); "
          f"{len(covered)} re-test check(s); ledger carries {len(pairs)} "
          f"(source, label) pair(s)")
    for w in warns:
        print(f"   WARN {w}")
    for f in fails:
        print(f"   FAIL {f}")
    print(f"\n{'FAIL' if fails else 'PASS'}: {len(fails)} problem(s), {len(warns)} "
          f"warning(s) in the source-conventions registry")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
