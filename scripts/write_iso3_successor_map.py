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
does NOT cover, the polity that was actually live, found by walking BOTH chain fields back from
the modern family's earliest row -- `predecessor` edges, plus `successor` edges read in reverse,
because the graph is only 57% symmetric (live rows, measured 2026-08-13) and reading one field sees
barely half of it.

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

WHAT IT DOES NOT RESOLVE, AND WHY.

THE FIRST VERSION OF THIS SECTION WAS WRONG AND IS KEPT HERE AS A WARNING. It said the map answered
96 of whep_crops' 482 uncovered (iso3, year) pairs and that 386 failed for one reason -- the earliest
row of a family having no `predecessor` -- and it listed SOM, BWA, SDN, ERI and TGO as the examples.
Issue 171 was filed off that list. By the time anyone measured it, four of the five were already
resolved, and NOT by adding any edge: this walk reads `successor` in reverse as well (see the comment
in build()), and BSS-1884-1960, ITS-1908-1960, BEC-1885-1966 and SUD-1934-1956 had each named their
successor all along. Measured 2026-08-13:

    SOM  76 pairs, 1884-1959, all depth 1 via BSS-1884-1960
    BWA  81 pairs, 1885-1965, all depth 1 via BEC-1885-1966
    SDN  57 pairs, 1899-1955, depth 1-2 via SUD-1934-1956 / SUD-1899-1934
    ERI  41 pairs, 1952-1992, depth 1 via ETH-1952-1993
    RUS  74 pairs, 1917-1990, depth 1-6 through the F228 chain

Those four reverse edges were nevertheless WRITTEN DOWN on 2026-08-13, in a second pass on issue
171, and the map did not move by one row (5,169 pairs before and after). SOM-1960-2025 now names
`predecessor: BSS-1884-1960; ITS-1908-1960`, BWA-1966-2025 names BEC-1885-1966 and SUD-1956-2011
names SUD-1934-1956. The reason is not this script -- it already read both fields -- but that all
three pages asserted in prose that the predecessor row did not exist ("no dedicated WHEP row
identified in CSV"), which was false, and two carried open questions asking someone to go looking
for rows that were already in the database. A consumer writing their own one-field traversal, which
is exactly what the first version of this walk was, saw nothing there.

The lesson is not that the numbers went stale -- it is that a docstring quoting a coverage figure is a
measurement with no test behind it, and this one survived long enough to become the premise of an
issue. Regenerate before quoting: the script prints its own totals.

WHAT ACTUALLY REMAINS UNRESOLVED is a much shorter list, and every entry is a MISSING POLITY rather
than a missing edge:

    TGO  0 pairs -- FTO-1920-1960 covers 1920-1960 and names GTO-1919-1922, which is a DEAD TARGET
                    (baselined in validate_chain_integrity). Nothing models German Togoland, so
                    1850-1919 has no answer to give.
    COM  0 pairs -- Comoros was a dependency of Madagascar 1908-1946. The only candidate row is
                    MDG-1882-2025, a single live row conflating the colony with the republic; naming
                    it would assert that Madagascar became the Comoros.
    PAK  0 pairs -- PAK-1937-1947 is a SUB-TERRITORY of British India reported separately, running
                    parallel to IND-1937-1947 rather than after it. Its page declines a predecessor
                    on purpose. A containment relation is not a succession and this schema has no
                    field for one -- the same overloading PR 135 removed from Greenland and Iceland.
    HUN  0 pairs -- correct: HUN-1800-1918 already covers 1850 onward, so there is no gap.

Two entries came OFF that list on 2026-08-13 (issue 171), and both were missing edges after all:

    LBY  0 -> 62 pairs, 1850-1911, via OTT-1908-1912 (Treaty of Ouchy, 18 October 1912). The issue
         said "Ottoman Tripolitania -- no row"; false, the OTT chain runs 1800-1912 and ends in
         exactly Libya's start year. Added symmetrically.
    BFA  0 -> 39 pairs, 1895-1918 and 1932-1946, via AOF-1895-1960, following the convention
         NER-1911-1922 and MRT-1920-1960 already use for carve-outs of French West Africa.

A HEURISTIC FOR FINDING MISSING EDGES WAS TRIED AND REJECTED -- recorded so nobody repeats it.
Selecting rows with no predecessor that have a span-adjacent candidate (some other row ending exactly
where they start) yields 134 rows, and the candidates are mostly year coincidence:

    ALB-1913-2025 starts 1913 -> candidates CHN-1895-1913, GRC-1881-1913, BGR-1878-1913, MNE-1878-1913

1913 was a busy year; none of those preceded Albania. A few hits are real (BWA-1966-2025 <- BEC-1885-1966,
AOI-1936-1941 <- ETH-1907-1936) but the precision is far too low to gate on, and a gate that is mostly
false positives trains people to ignore it. The missing edges need naming case by case.

Note also that the heuristic would have MISSED both edges issue 171 actually needed to have added:
LBY-1912-1919 had no predecessor and OTT-1908-1912 is span-adjacent, so that one it would have found;
but BFA's answer is AOF-1895-1960, whose span CONTAINS both BFA rows rather than abutting them, so no
adjacency rule reaches it. The two real fixes here have opposite shapes.

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

    # THE GRAPH IS ONLY 57% SYMMETRIC, so a walk that reads one field sees barely half of it.
    # Live rows only, matching validate_chain_integrity signal F, measured 2026-08-13:
    #
    #     edges asserted as A.successor = B       548
    #     edges asserted as B.predecessor = A     440
    #     asserted BOTH ways                      357
    #     successor-only  (no reverse predecessor) 191
    #     predecessor-only (no reverse successor)   83
    #
    # (The pinned counts live in validate_chain_integrity.BASELINE_ASYMMETRY. These are here for
    # the reader; that gate is what keeps them honest.)
    #
    # The first version of this walk read `predecessor` only and therefore could not see 194 real
    # relations -- including SOM-1960-2025, whose predecessors BSS-1884-1960 and ITS-1908-1960 BOTH
    # declare `successor: SOM-1960-2025` while SOM declares no predecessor at all. I was about to
    # patch five rows by hand before measuring; reading both fields fixes all 194 at once.
    #
    # So build one backward adjacency from both directions: B's predecessors are everything B names
    # in `predecessor` PLUS everything that names B in its `successor`.
    backward = collections.defaultdict(set)
    for code, row in live.items():
        for target in links(row.get("predecessor")):
            if target in live:
                backward[code].add(target)
        for target in links(row.get("successor")):
            if target in live:
                backward[target].add(code)

    def resolve(iso, year):
        """Walk backward edges outward, returning the first live row containing `year` and the
        depth it was found at.

        START FROM THE ROW ADJACENT TO THE GAP, not from the family's earliest row. The first
        version did the latter and could therefore only explain gaps BEFORE a family begins --
        it silently answered nothing for gaps in the MIDDLE of one, which is a different and
        common shape:

            ERI-1885-1889, ERI-1889-1952, [1952-1992 missing], ERI-1993-2025

        Eritrea was federated with Ethiopia in 1952 and annexed in 1962, so those years belong to
        ETH-1952-1993 -- and ERI-1993-2025 says so outright, `predecessor: ERI-1889-1952;
        ETH-1952-1993`. Walking back from ERI-1885-1889 can never reach a row that starts in 1952,
        so 360 rows of observed Eritrean data resolved to nothing while the answer sat one edge
        away from the other end of the family.

        Starting from the earliest row that begins AFTER `year` makes the walk approach the gap
        from the near side. Falling back to the earliest row overall covers the before-the-family
        case, which is what the original did.
        """
        later = [r for r in by_iso[iso] if span(r)[0] > year]
        start = (min(later, key=lambda r: span(r)[0]) if later
                 else min(by_iso[iso], key=lambda r: span(r)[0]))
        seen, frontier = {start["polity_code"]}, [start["polity_code"]]
        for depth in range(1, MAX_DEPTH + 1):
            nxt = []
            for code in frontier:
                for target in sorted(backward.get(code, ())):
                    if target in seen:
                        continue
                    seen.add(target)
                    parent = live[target]
                    try:
                        lo, hi = span(parent)
                    except (TypeError, ValueError):
                        continue
                    if lo <= year < hi:
                        return parent, depth
                    nxt.append(target)
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
