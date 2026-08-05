#!/usr/bin/env python3
"""Check that the predecessor/successor graph is a coherent chronology.

Five signals, each of which caught something real on 2026-08-05 that every other gate in
this repo structurally could not see. The existing chain check,
`validate_succession_geography.py`, asks whether two linked territories TOUCH. That is a
question about space. Nothing asked whether the link makes sense in TIME, points at a row
that EXISTS, or forms a coherent graph — so a link could name a nonexistent code, run
backwards, or close a cycle, and stay green forever.

    A. DEAD TARGET      — a predecessor/successor naming a code that is not in the database
    B. IMPOSSIBLE ORDER — a successor whose span ENDS at or before the row's span STARTS
    C. CYCLE            — a cycle in the successor graph, i.e. a chronology that loops
    D. LIVE CEILING     — a LIVE row ending at the 2025 ceiling that declares a successor
    E. BROKEN PAGE LINK — a wiki page linking to a `slug.md` that does not exist

What each found first time out:

  B found ONE edge and it was the whole point of writing the check. `TCD-1920-1960` listed
  `WAD-1800-1912` (Wadai) as a SUCCESSOR — a polity that ended eight years BEFORE Chad's
  colonial row begins. The page's own prose called it a predecessor in the same breath,
  citing "the CSV" as its authority, while the CSV is generated from that very frontmatter.
  Fixing the direction also closed a cycle that C had independently flagged.

  C found two cycles, both since resolved. The second, `GRL <-> ISL`, exposed a SCHEMA
  problem rather than a data typo: Greenland and Iceland each named the other, plus three
  Denmark periods, as successors. None was a successor. The field was being used to mean
  "related to" — specifically sovereignty, which this schema has no field for. Clearing the
  two lists also deleted 8 entries from validate_succession_geography's baseline, where they
  had been accepted as "overseas relationships need not touch". True, and beside the point:
  they were never successions at all. A geometry gate cannot tell you that; it can only
  measure the distance between two things it has been told are related.

  D distinguishes two populations that look identical. Three of the five rows it flags are
  RETIRED or SUPERSEDED and point at the finer rows that replaced them — supersession
  written into `successor:`. That is an overloaded field but a deliberate convention, so
  it is baselined. The other two were LIVE and are now fixed. Only the live ones can mislead
  a consumer, which is why this signal filters on wiki_status.

  E found 26 broken links, and FOUR OF THEM PREDATED the edit that made me look —
  `validate_references` checks citation markers, not inter-page links, so a rename could
  silently orphan every cross-reference to the renamed page. Two were `zaf-1828-2025`, a
  code that never existed; the correct `zaf-1910-2025` was one directory listing away.

Bidirectional, like the other baselines here: a new entry fails, and a baselined entry that
stops reproducing must be deleted.
"""
from __future__ import annotations

import collections
import csv
import os
import pathlib
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(REPO, "data/final/polities_database.csv")
WIKI_DIR = os.path.join(REPO, "wiki/polities")

CEILING = 2025
DEAD_STATUS = ("retired", "superseded")

# --- A: targets that name no row in the database -----------------------------------------
# Every one of these names a real historical entity that simply has no row yet. They are NOT
# typos -- the 9 that were typos were repaired in the same change that added this gate, each
# resolved by the database's own convention that a predecessor ends exactly where its row
# begins. Creating these polities is tracked separately; until then the reference records an
# intent that the database cannot yet satisfy, which is better than deleting it and losing
# the fact that the predecessor existed.
BASELINE_DEAD = {
    ("BRL-1938-1945", "predecessor", "BRL-1920-1938"): "Berlin before the 1938 Greater Berlin boundary; no pre-1938 BRL row exists",
    ("BRL-1945-1949", "successor", "EBL-1949-1990"): "East Berlin 1949-1990; no EBL row exists",
    ("BTL-1920-1957", "predecessor", "GTO-1919-1922"): "German Togoland in the 1919-1922 transitional period, before the British/French partition; no GTO row exists",
    ("FTO-1920-1960", "predecessor", "GTO-1919-1922"): "same GTO gap, from the French side",
    ("CZN-1903-1979", "predecessor", "PAN-1800-1979"): "Panama before the 1903 Canal Zone, i.e. as part of Colombia; the PAN chain starts at 1903",
    ("HUN-1920-1938", "predecessor", "HUN-1919-1920"): "the 1919-1920 Hungarian interregnum; the HUN chain jumps 1918-1919 -> 1920-1938",
    ("SYR-1920-1922", "predecessor", "SYR-1918-1920"): "OETA East / Arab Kingdom of Syria; the SYR chain starts at the 1920 mandate",
    ("TNGU-1920-1949", "predecessor", "GNGU-1884-1914"): "German New Guinea; no GNGU row exists",
    # The only entry here that is not a missing polity: both endpoints are dead rows, so no
    # consumer can traverse the edge. Repointing it would be churn in retired history.
    ("CAN-1948-2025", "predecessor", "CAN-1866-1948"): "CAN-1948-2025 is itself retired and CAN-1866-1948 was re-spanned; a dead row pointing at a dead row",
}

# --- D: rows at the ceiling that declare a successor ---------------------------------------
# Only LIVE rows are reported. These three are dead rows using `successor:` for SUPERSESSION
# -- "the finer rows that replaced me" -- which is a real convention in this database even
# though it overloads the field. Left as-is deliberately: rewriting them would need a new
# field, and the rows are unreachable by any consumer.
BASELINE_CEILING = {
    "BLZ-1800-2025": "superseded; lists the four finer BLZ periods that replaced it",
    "IRQ-1921-2025": "superseded; lists the two finer IRQ periods that replaced it",
    "CAN-1948-2025": "retired; points at CAN-1949-2025, the corrected span",
}

# --- E: page links whose target file does not exist ----------------------------------------
# Deliberate forward references to pages that have not been written. `bbc-1885-1895` even
# carries an explicit `<!-- TODO: page not yet created -->` marker at the link site. The rest
# are the A-baseline entities above, referenced from prose as well as frontmatter.
BASELINE_LINKS = {
    ("bec-1885-1966.md", "bbc-1885-1895"): "British Bechuanaland Crown Colony; the link site carries an explicit 'page not yet created' TODO",
    ("fcm-1920-1960.md", "bca-1919-1961"): "British Cameroon; page not yet created",
    ("fto-1920-1960.md", "gto-1919-1922"): "German Togoland transitional period; see BASELINE_DEAD",
    ("hun-1920-1938.md", "hun-1919-1920"): "Hungarian interregnum; see BASELINE_DEAD",
    ("can-1948-2025.md", "can-1866-1948"): "re-spanned Canada row; see BASELINE_DEAD",
    ("syr-1920-1922.md", "syr-1918-1920"): "Arab Kingdom of Syria; see BASELINE_DEAD",
    ("czn-1903-1979.md", "pan-1800-1979"): "pre-1903 Panama; see BASELINE_DEAD",
}


def links(v: str) -> list:
    """Split a chain field.

    On BOTH ';' and ',': build_database.py joins multiple values with '; ', and a parser
    that split on ',' alone hid 13.8% of this graph until PR 132 -- including a link between
    two polities 3,467 km apart. Do not narrow this again.
    """
    return [x.strip() for x in re.split(r"[;,]", (v or "").strip("[]")) if x.strip()]


def span(code: str):
    m = re.search(r"-(\d{4})-(\d{4})$", code or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


def main() -> int:
    if not os.path.exists(CSV_PATH):
        print(f"FAIL: {CSV_PATH} missing; run scripts/build_database.py first")
        return 2

    with open(CSV_PATH, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    by = {r["polity_code"]: r for r in rows}

    def is_live(code):
        r = by.get(code)
        return bool(r) and (r.get("wiki_status") or "").strip() not in DEAD_STATUS

    problems = []
    stale = []

    # A -------------------------------------------------------------------------------------
    dead = {
        (r["polity_code"], f, t)
        for r in rows
        for f in ("predecessor", "successor")
        for t in links(r.get(f))
        if t not in by
    }
    for key in sorted(dead - set(BASELINE_DEAD)):
        problems.append(f"DEAD TARGET: {key[0]} {key[1]} -> {key[2]} names no row in the database")
    for key in sorted(set(BASELINE_DEAD) - dead):
        stale.append(f"BASELINE_DEAD {key} no longer reproduces -- remove it")

    # B -------------------------------------------------------------------------------------
    for r in rows:
        a = r["polity_code"]
        ya = span(a)
        if not ya:
            continue
        for t in links(r.get("successor")):
            yt = span(t)
            if yt and yt[1] <= ya[0]:
                problems.append(
                    f"IMPOSSIBLE ORDER: {a} {ya[0]}-{ya[1]} declares successor {t} "
                    f"{yt[0]}-{yt[1]}, which ends {ya[0] - yt[1]}y BEFORE it starts "
                    f"(is it a predecessor?)"
                )

    # C -------------------------------------------------------------------------------------
    adj = {r["polity_code"]: [t for t in links(r.get("successor")) if t in by] for r in rows}
    colour = collections.defaultdict(int)
    cycles = []
    sys.setrecursionlimit(10000)

    def walk(n, stack):
        colour[n] = 1
        stack.append(n)
        for m in adj.get(n, ()):
            if colour[m] == 1:
                cycles.append(stack[stack.index(m):] + [m])
            elif colour[m] == 0:
                walk(m, stack)
        stack.pop()
        colour[n] = 2

    for n in adj:
        if colour[n] == 0:
            walk(n, [])
    for c in cycles:
        problems.append("CYCLE: " + " -> ".join(c))

    # D -------------------------------------------------------------------------------------
    ceiling = set()
    for r in rows:
        y = span(r["polity_code"])
        if y and y[1] >= CEILING and links(r.get("successor")):
            ceiling.add(r["polity_code"])
    for code in sorted(ceiling):
        if code in BASELINE_CEILING:
            continue
        if not is_live(code):
            problems.append(
                f"LIVE CEILING: {code} is dead but not baselined; if it uses successor for "
                f"supersession add it to BASELINE_CEILING with that reason"
            )
            continue
        problems.append(
            f"LIVE CEILING: {code} is live and runs to {CEILING} yet declares successor "
            f"{links(by[code].get('successor'))} -- a live entity has nothing after it"
        )
    for code in sorted(set(BASELINE_CEILING) - ceiling):
        stale.append(f"BASELINE_CEILING {code!r} no longer declares a successor -- remove it")

    # E -------------------------------------------------------------------------------------
    pages = sorted(pathlib.Path(WIKI_DIR).glob("*.md"))
    slugs = {p.stem for p in pages}
    broken = set()
    for p in pages:
        for m in re.finditer(r"\(([a-z0-9]+-\d{4}-\d{4})\.md\)", p.read_text(encoding="utf-8")):
            if m.group(1) not in slugs:
                broken.add((p.name, m.group(1)))
    for key in sorted(broken - set(BASELINE_LINKS)):
        problems.append(f"BROKEN PAGE LINK: {key[0]} links to {key[1]}.md, which does not exist")
    for key in sorted(set(BASELINE_LINKS) - broken):
        stale.append(f"BASELINE_LINKS {key} no longer broken -- remove it")

    print(f"rows: {len(rows)}")
    print(f"chain edges: {sum(len(links(r.get(f))) for r in rows for f in ('predecessor', 'successor')):,}")
    print(f"dead targets: {len(dead)} ({len(BASELINE_DEAD)} baselined)")
    print(f"cycles: {len(cycles)}")
    print(f"ceiling rows declaring a successor: {len(ceiling)} ({len(BASELINE_CEILING)} baselined, all dead)")
    print(f"broken page links: {len(broken)} ({len(BASELINE_LINKS)} baselined)")

    if problems or stale:
        print(f"\nFAIL: {len(problems) + len(stale)} problem(s)\n")
        for p in problems + stale:
            print(f"  {p}")
        print(
            "\n  A chain link is a claim about chronology. It has to name a row that exists,\n"
            "  point forwards in time, and not loop. Where a link expresses something else --\n"
            "  sovereignty, supersession -- say so explicitly rather than borrowing this field."
        )
        return 1

    print("\nPASS: the succession graph is a coherent chronology")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
