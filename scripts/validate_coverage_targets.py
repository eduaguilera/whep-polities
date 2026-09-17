#!/usr/bin/env python3
"""A coverage segment that names a polity must name one that exists.

`pipelines/agent-harness/state/routing_verdicts.csv` records, per reporting unit, how every
year of its data is accounted for. Each segment may name the polity the years route to, and
for `back_cast` the schema requires it:

    back_cast: ... so the data routes to the polity while the polity's own span still begins
    when the territory did. NAME THAT POLITY IN polity_code.

WHAT IT FOUND (2026-09-17). 43 segments named a code that had never been minted, and nothing
noticed, because no tool resolves that field:

    BRA-TOCANTINS     1900-1987  ->  'BRA-TOCANTINS'                the unit's own id
    BRA-MATOGROSSODOSUL 1900-1976 -> 'BRA-MATOGROSSO'               a neighbouring unit's id
    FRA-FRF11         1862-1918  ->  'FRA-BASRHIN-1919-2025'        invented; the real row is
                                                                    FRA-67-1919-2025
    USA-NORTHDAKOTA   1879-1888  ->  'NOR-DAKOTA-1889-2025'         invented
    COL-CAQUETA       1915-1980  ->  'CAQUETA-1981-2025'            invented
    PRT-PT11 ... x6   1870-1985  ->  ''                             blank (my own residue)

Two shapes and both are silent: an agent writing the reporting unit's id where a polity code
belongs, and an agent minting a plausible code from a territory name. Neither is a typo a
reader would catch -- 'FRA-BASRHIN-1919-2025' looks exactly like this table's other codes --
and every downstream report keys on the polity table, where these simply do not appear. The
six blank ones were mine, left when Portugal's coverage was rewritten.

Two segments were not just mislabelled but structurally wrong, and their own basis text said
so. FRA-FRJ11 recorded 1862-1870 as `back_cast` while its basis read "the département itself
already existed since 1790" -- the opposite of a back-cast -- and USA-NEWMEXICO recorded a
single 1879-2025 `back_cast` while its basis named only "1879-1911" as pre-statehood, sweeping
a century of observed data in with the reconstruction.

WHAT THIS CHECKS, and deliberately no more:

  A. every non-empty `polity_code` on a segment resolves to a live polity
  B. every `back_cast` segment names one, since the schema requires it

WHAT IT DOES NOT CHECK, because the repo holds two defensible readings and this gate is not
the place to pick one. A `back_cast` target may either be the MODERN unit, whose span begins
after the segment ends (43 segments, the schema's literal words), or the era's NATIONAL
polity, which already covered that ground (12 segments: CHL-AP and CHL-AR to CHL-1899-1902
and CHL-1902-2025, COL-AMAZONAS to COL-1903-1922). Both put the data on a real polity and
record that it is a reconstruction; they disagree about which polity. Requiring either one
would fail the other, so this gate requires only that the target be real.

Reads only committed files, so it runs anywhere; the gitignored panel is not needed.

Usage:
  python3 scripts/validate_coverage_targets.py
"""
import csv
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(REPO, "pipelines/agent-harness/state/routing_verdicts.csv")
POLDB = os.path.join(REPO, "data/final/polities_database.csv")

DEAD = ("retired", "superseded")

# Segments knowingly naming no polity, or one absent from the table, each with the reason.
# Bidirectional: a new one fails, and a resolved one must be removed or this fails too.
BASELINE = {}


def main() -> int:
    if not os.path.exists(LEDGER):
        print(f"SKIP: {os.path.relpath(LEDGER, REPO)} absent")
        return 0

    csv.field_size_limit(sys.maxsize)

    live = set()
    with open(POLDB, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if (r.get("wiki_status") or "").strip() not in DEAD:
                live.add(r["polity_code"])

    unresolved, unnamed = [], []
    segments = 0
    with open(LEDGER, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            raw = (r.get("coverage_json") or "").strip()
            if not raw:
                continue
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                print(f"FAIL: {r['unit_id']} has unparseable coverage_json")
                return 1
            segs = parsed.get("segments", []) if isinstance(parsed, dict) else parsed
            for s in segs:
                segments += 1
                target = (s.get("polity_code") or "").strip()
                disp = s.get("disposition")
                where = f"{r['unit_id']} {s.get('start_year')}-{s.get('end_year')} ({disp})"
                if target:
                    if target not in live:
                        unresolved.append((where, target))
                elif disp == "back_cast":
                    unnamed.append(where)

    problems = [(w, t) for w, t in unresolved if w not in BASELINE]
    problems += [(w, "") for w in unnamed if w not in BASELINE]
    stale = sorted(set(BASELINE) - {w for w, _ in unresolved} - set(unnamed))
    if stale:
        print(f"FAIL: {len(stale)} baseline entr(ies) no longer needed -- remove them:")
        for w in stale:
            print(f"  {w}: {BASELINE[w]}")
        return 1

    if problems:
        print(f"FAIL: {len(problems)} coverage segment(s) name no live polity\n")
        for where, target in problems:
            if target:
                print(f"  {where}\n      names {target!r}, which is not a live polity. An agent "
                      f"writing the reporting unit's own id, or minting a code from a territory "
                      f"name, produces exactly this and nothing else resolves the field.")
            else:
                print(f"  {where}\n      names no polity, and the schema requires a back_cast "
                      f"segment to name the one its data routes to.")
        print("\nThe unit's own `page_polity_code` in the same row is usually the answer.")
        return 1

    print(f"PASS: all {segments} coverage segment(s) name a live polity where they name one "
          f"({len(BASELINE)} baselined)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
