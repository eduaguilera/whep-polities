#!/usr/bin/env python3
"""Publish which historical polity covered a modern ISO3's territory before its own rows begin.

An ISO3 code in this database covers only its POST-INDEPENDENCE periods. The colonial or imperial
years for the same territory sit under a code of their own -- Serbian history under `SER`, Tanzania
1891-1961 under `TAN`, the Soviet republics under `F228`. That is deliberate: a colony is not its
successor state, and collapsing British Somaliland into `SOM` would assert a continuity that did not
exist.

The consequence is not deliberate. ANY ISO3-KEYED SOURCE silently reaches nothing for the colonial
era and gets no error back -- the join succeeds and returns zero rows. whep_crops v1.0 is 1.84M rows
keyed exactly that way, and ~1,900 of its observed rows land in that hole (issue 168).

This writes `data/final/iso3_successor_map.csv`: for each (modern iso3, year) that the modern code
does NOT cover, the polity that was actually live, found by walking `predecessor` edges back from
the modern family's earliest row.

DERIVED, NOT HAND-WRITTEN, and that matters. My first attempt was a hand-authored list of code pairs
(`SER -> SRB`, `TAN -> TZA`, ...). Deriving it from the chain graph instead means it cannot drift
from the database, it needs no maintenance when a period is added, and it produced 69 relations where
I would have written a dozen -- including every Soviet republic, which I had not thought of.

WHY IT IS YEAR-RESOLVED RATHER THAN CODE-TO-CODE. A code-level map has to answer "what preceded
SOM?" with one value, and the honest answer is two (British Somaliland and Italian Somaliland,
simultaneously). A year-resolved map does not have that problem: 1935 has its own answer. It also
makes the many-to-one relation visible instead of hiding it behind a single winner.

HOP DEPTH IS RECORDED, AND SHOULD BE CHECKED. The traversal follows every `predecessor` edge, so a
row with several predecessors can lead somewhere wrong a few steps out. `DDR` reaches `AUT-1919-2025`
at depth 3 -- East Germany did not succeed Austria, the walk just wandered through a shared edge.
Depth 1 is a direct statement by the database that A preceded B. Deeper is an inference, and a
consumer should treat it as one:

    depth 1     a predecessor edge says so directly
    depth 2+    reached through intermediate rows; plausible, not asserted

WHAT IT DOES NOT RESOLVE, AND WHY. Of whep_crops' 482 uncovered observed (iso3, year) pairs this
map answers 96 (822 rows), 86 of them at depth 1 -- including the three largest blocks: TZA 465
rows to `TAN`, ISR 230 to `PAL`, SRB 120 to `SCG`/`F248`. The other 386 fail for ONE reason, and it
is not a mapping problem:

    SOM: earliest SOM-1960-2025    predecessor: NONE
    BWA: earliest BWA-1966-2025    predecessor: NONE
    SDN: earliest SUD-1956-2011    predecessor: NONE
    ERI: earliest ERI-1885-1889    predecessor: NONE
    TGO: earliest FTO-1920-1960    predecessor: GTO-1919-1922 (DEAD TARGET)

The historical rows EXIST -- BSS-1884-1960 and ITS-1908-1960 for Somaliland, BEC-1885-1966 for
Bechuanaland -- and nothing links them to their successors. So the walk starts and immediately has
nowhere to go. `validate_chain_integrity` checks that the edges present are coherent; nothing checks
that an independence transition HAS one.

A HEURISTIC FOR FINDING THOSE MISSING EDGES WAS TRIED AND REJECTED -- recorded so nobody repeats it.
Selecting rows with no predecessor that have a span-adjacent candidate (some other row ending exactly
where they start) yields 134 rows, and the candidates are mostly year coincidence:

    ALB-1913-2025 starts 1913 -> candidates CHN-1895-1913, GRC-1881-1913, BGR-1878-1913, MNE-1878-1913

1913 was a busy year; none of those preceded Albania. A few hits are real (BWA-1966-2025 <- BEC-1885-1966,
AOI-1936-1941 <- ETH-1907-1936) but the precision is far too low to gate on, and a gate that is mostly
false positives trains people to ignore it. The missing edges need naming case by case.

Usage:
  python3 scripts/write_iso3_successor_map.py
  python3 scripts/write_iso3_successor_map.py --check
"""
from __future__ import annotations

import collections
import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(REPO, "data/final/polities_database.csv")
DEST = os.path.join(REPO, "data/final/iso3_successor_map.csv")

DEAD_STATUS = ("retired", "superseded")
FIRST_YEAR, LAST_YEAR = 1850, 2025
MAX_DEPTH = 6

FIELDS = (
    "modern_iso3", "year", "polity_code", "polity_iso3", "polity_name", "hop_depth"
)


def links(value: str) -> list:
    """Split a chain field on BOTH ';' and ',' -- build_database joins with '; ', and a parser
    that split on ',' alone hid 13.8% of this graph until PR 132."""
    return [x for x in (p.strip() for p in re.split(r"[;,]", (value or "").strip("[]"))) if x]


def build() -> list:
    with open(CSV_PATH, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    live = {
        r["polity_code"]: r for r in rows
        if (r.get("wiki_status") or "").strip() not in DEAD_STATUS
    }

    def span(row):
        return int(row["start_year"]), int(row["end_year"])

    by_iso = collections.defaultdict(list)
    for r in live.values():
        if r.get("iso3_code"):
            try:
                span(r)
            except (TypeError, ValueError):
                continue
            by_iso[r["iso3_code"]].append(r)

    def covers(iso, year):
        return any(span(r)[0] <= year < span(r)[1] for r in by_iso.get(iso, ()))

    def resolve(iso, year):
        """Walk predecessor edges outward, returning the first live row containing `year`
        and the depth it was found at."""
        start = min(by_iso[iso], key=lambda r: span(r)[0])
        seen, frontier = {start["polity_code"]}, [start]
        for depth in range(1, MAX_DEPTH + 1):
            nxt = []
            for row in frontier:
                for target in links(row.get("predecessor")):
                    parent = live.get(target)
                    if parent is None or target in seen:
                        continue
                    seen.add(target)
                    try:
                        lo, hi = span(parent)
                    except (TypeError, ValueError):
                        continue
                    if lo <= year < hi:
                        return parent, depth
                    nxt.append(parent)
            if not nxt:
                break
            frontier = nxt
        return None, None

    out = []
    for iso in sorted(by_iso):
        for year in range(FIRST_YEAR, LAST_YEAR + 1):
            if covers(iso, year):
                continue
            parent, depth = resolve(iso, year)
            if parent is None:
                continue
            out.append({
                "modern_iso3": iso,
                "year": year,
                "polity_code": parent["polity_code"],
                "polity_iso3": parent.get("iso3_code", ""),
                "polity_name": parent["polity_name"],
                "hop_depth": depth,
            })
    return out


def main() -> int:
    if not os.path.exists(CSV_PATH):
        print(f"FAIL: {CSV_PATH} missing; run scripts/build_database.py first")
        return 2
    fresh = build()

    import io
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(FIELDS))
    writer.writeheader()
    writer.writerows(fresh)
    rendered = buf.getvalue()

    if "--check" in sys.argv:
        if not os.path.exists(DEST):
            print(f"FAIL: {os.path.basename(DEST)} missing; run this script without --check")
            return 1
        with open(DEST, encoding="utf-8") as fh:
            committed = fh.read()
        if committed.replace("\r\n", "\n") != rendered.replace("\r\n", "\n"):
            old = len(committed.splitlines()) - 1
            print(f"FAIL: {os.path.basename(DEST)} is stale "
                  f"({old} committed rows vs {len(fresh)} regenerated)")
            print("  rerun: python3 scripts/write_iso3_successor_map.py")
            return 1
        print(f"OK: {os.path.basename(DEST)} matches the chain graph ({len(fresh):,} pairs)")
        return 0

    with open(DEST, "w", encoding="utf-8", newline="") as fh:
        fh.write(rendered)

    depths = collections.Counter(r["hop_depth"] for r in fresh)
    rel = {(r["modern_iso3"], r["polity_iso3"]) for r in fresh}
    print(f"wrote {len(fresh):,} (modern iso3, year) pairs -> {os.path.relpath(DEST, REPO)}")
    print(f"  modern iso3 codes covered: {len({r['modern_iso3'] for r in fresh})}")
    print(f"  distinct (modern, historical) relations: {len(rel)}")
    print(f"  hop depth: {dict(sorted(depths.items()))}")
    print("\n  depth 1 is a direct predecessor edge; depth 2+ is an inference and is labelled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
