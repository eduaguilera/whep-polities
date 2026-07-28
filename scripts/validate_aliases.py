#!/usr/bin/env python3
"""Check that every applied alias can actually route data to a polity.

Why: an alias whose target is unusable does not fail loudly, it does NOTHING.
`matchlib.Matcher` drops a rule whose target is not a known polity code, so a
broken row is indistinguishable from an absent one — the source label simply goes
unmatched and its data falls to whatever the deterministic routes decide.

Three such rows were found in the registry, all silently inert, and one had been
that way since it was written:

  `china, taiwan province of`  the label contains a comma and was written
                               UNQUOTED, so every field shifted one column left
                               and the target landed in `confidence`
  `British Togoland`           fields written in the wrong columns; the target
                               ended up in `year_start`, leaving it empty
  `Abyssinia`                  target was the bare prefix `ETH`, which names a
                               family rather than a period

The first two are what a CSV with unquoted prose in it does eventually. This
script exists so the next one is caught by a gate rather than by someone
noticing, years later, that a label never resolved.

Checks:
  1. `target_polity_code` names a LIVE polity in the database. Dead targets are
     rejected too: routing data to a retired or superseded row is the mistake the
     whole DEAD_STATUS mechanism exists to prevent.
  2. `target_polity_code` is a full periodised code, not a bare family prefix.
     `ETH` is not a polity; `ETH-1907-1936` is.
  3. `confidence` is one of the expected values, and the year fields are either
     empty or four-digit years. Both are shift detectors: when a column slips,
     these are where the debris lands.
  4. `year_start <= year_end` when both are present.

Usage:
  python3 scripts/validate_aliases.py
"""
import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALIASES = os.path.join(
    REPO, "pipelines/polity-autoimprove/state/applied_aliases.csv"
)
POLITIES = os.path.join(REPO, "data/final/polities_database.csv")

DEAD_STATUS = ("retired", "superseded")
CONFIDENCE_VALUES = {"high", "medium", "low", ""}
CODE_RE = re.compile(r"^[A-Za-z0-9]+(-[A-Za-z0-9]+)*-[0-9]{4}-[0-9]{4}$")
YEAR_RE = re.compile(r"^[0-9]{4}$")

polities = list(csv.DictReader(open(POLITIES, encoding="utf-8")))
live = {r["polity_code"] for r in polities if r["wiki_status"] not in DEAD_STATUS}
dead = {r["polity_code"] for r in polities if r["wiki_status"] in DEAD_STATUS}

rows = list(csv.DictReader(open(ALIASES, encoding="utf-8")))
problems: list[str] = []

for i, r in enumerate(rows, start=2):  # +2: header is line 1
    label = r.get("original_name", "")
    target = (r.get("target_polity_code") or "").strip()
    conf = (r.get("confidence") or "").strip()
    y0 = (r.get("year_start") or "").strip()
    y1 = (r.get("year_end") or "").strip()

    where = f"line {i}, {label!r}"

    if not target:
        problems.append(
            f"{where}: no target_polity_code — the alias can never route anything"
        )
    elif not CODE_RE.match(target):
        hint = (
            " (looks like a bare family prefix; an alias must name one period)"
            if "-" not in target
            else ""
        )
        problems.append(f"{where}: target {target!r} is not a polity code{hint}")
    elif target in dead:
        problems.append(
            f"{where}: target {target!r} is RETIRED or SUPERSEDED and must not "
            f"receive data"
        )
    elif target not in live:
        problems.append(
            f"{where}: target {target!r} is not in the polities database"
        )

    if conf not in CONFIDENCE_VALUES:
        problems.append(
            f"{where}: confidence {conf!r} is not one of "
            f"{sorted(v for v in CONFIDENCE_VALUES if v)} — a column has probably "
            f"shifted (an unquoted comma in the label does this)"
        )
    for field, value in (("year_start", y0), ("year_end", y1)):
        if value and not YEAR_RE.match(value):
            problems.append(
                f"{where}: {field}={value!r} is not a four-digit year — a column "
                f"has probably shifted"
            )
    if YEAR_RE.match(y0) and YEAR_RE.match(y1) and int(y0) > int(y1):
        problems.append(f"{where}: year_start {y0} is after year_end {y1}")

if problems:
    print(f"FAIL: {len(problems)} alias problem(s)\n")
    for p in problems[:40]:
        print(f"  {p}")
    if len(problems) > 40:
        print(f"  ... and {len(problems) - 40} more")
    print(
        "\n  A broken alias is INERT, not loud: the Matcher drops it and the "
        "label silently goes unmatched."
    )
    sys.exit(1)

print(
    f"PASS: all {len(rows)} aliases target a live polity, with well-formed "
    f"years and confidence"
)
