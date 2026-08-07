#!/usr/bin/env python3
"""Check that the predecessor/successor graph is a coherent chronology.

Seven signals, each of which caught something real that every other gate in
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
    F. ASYMMETRY        — A says `successor: B` while B does not say `predecessor: A`, or vice versa
    G. SELF-REPLACING   — a page whose prose says it replaced or superseded ITS OWN code

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

  F was added on 2026-08-06 after the ISO3 successor map (PR 170) came out half-empty. THE GRAPH
  IS ONLY 55% SYMMETRIC:

      edges asserted as A.successor = B        539
      edges asserted as B.predecessor = A     430
      asserted BOTH ways                      345
      successor-only  (no reverse predecessor) 194
      predecessor-only (no reverse successor)   85

  Every per-edge check here reads both fields, so none of them noticed. What breaks is any
  TRAVERSAL: a walk that follows `predecessor` sees 430 of 539 relations and silently misses the
  rest. SOM-1960-2025 is the clean example -- BSS-1884-1960 and ITS-1908-1960 both declare
  `successor: SOM-1960-2025`, and SOM declares no predecessor at all, so walking backwards from
  Somalia found nothing while the relation was sitting there in the other field.

  I was about to hand-patch five rows before measuring. Reading both fields in the map fixed 194
  relations at once and took its whep_crops coverage from 96 pairs to 255. This signal exists so
  the asymmetry shrinks rather than growing, since a consumer writing their own traversal will not
  know to read both.

  The counts are PINNED rather than the edges enumerated -- 279 entries would be unreadable, and
  what matters is the direction of travel.

  G was added on 2026-08-07 and found SEVEN pages at once — every reporting bucket. Each note
  read "End year moved 2021 -> 2025 (issue 50), replacing `RAFR-1850-2025`": its own code, not
  the retired `RAFR-1850-2021` it superseded. So the live page named no predecessor and the
  retired page pointed nowhere forward, leaving the rename undocumented from both ends.

  It survived every other gate BY CONSTRUCTION. Signal E only asks whether a linked page
  EXISTS, and a self-link always exists. The frontmatter was correct throughout — the defect
  was purely a claim in prose, which is where the REASON for a rename lives, and nothing else
  in this repo reads prose for meaning. There is no baseline: seven were found and seven were
  fixed, so the correct count is zero.

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
# Signal F. Pinned counts, not enumerated edges: 279 lines would be unreadable and the useful
# property is that these only go down. Lower them when they do -- the check insists.
BASELINE_ASYMMETRY = {
    "successor_only": 194,
    "predecessor_only": 85,
}

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

    # F -------------------------------------------------------------------------------------
    # LIVE rows only, deliberately. The other signals use every row, because a dead row is still a
    # real target and a dangling reference to one is still dangling. Asymmetry is different: it
    # matters because it breaks TRAVERSAL, and every consumer -- matchlib included -- drops
    # retired and superseded rows before traversing anything. Counting them would pin a number
    # nobody's walk can reach. (Measured both ways: 225/94 over all rows, 194/85 over live.)
    walkable = {c: r for c, r in by.items() if is_live(c)}
    forward = {
        (code, target)
        for code, row in walkable.items()
        for target in links(row.get("successor"))
        if target in walkable
    }
    backward = {
        (target, code)
        for code, row in walkable.items()
        for target in links(row.get("predecessor"))
        if target in walkable
    }
    succ_only = len(forward - backward)
    pred_only = len(backward - forward)
    for name, actual in (("successor_only", succ_only), ("predecessor_only", pred_only)):
        pinned = BASELINE_ASYMMETRY[name]
        if actual > pinned:
            problems.append(
                f"ASYMMETRY: {actual} {name.replace('_', '-')} chain edges, up from {pinned}. "
                f"An edge asserted in one field only is invisible to any traversal that reads the "
                f"other, which is how the ISO3 successor map came out half-empty (PR 170)."
            )
        elif actual < pinned:
            problems.append(
                f"ASYMMETRY: {actual} {name.replace('_', '-')} chain edges, DOWN from {pinned} -- "
                f"lower the pinned count so the improvement is locked in"
            )

    # G -------------------------------------------------------------------------------------
    # A PAGE THAT SAYS IT REPLACED ITSELF NAMES ITS PREDECESSOR NOWHERE.
    #
    # All SEVEN reporting-bucket pages carried this on 2026-08-07. Each had a note reading
    # "End year moved 2021 -> 2025 (issue 50), replacing `RAFR-1850-2025`" -- its own code, not
    # the retired `RAFR-1850-2021` it superseded. So a reader arriving at the live page could
    # not learn which code went away, and a reader arriving at the retired page had nothing
    # pointing forward either.
    #
    # It survived every other gate by construction. Signal E only checks that a linked page
    # EXISTS, and a self-link always exists. The frontmatter was correct throughout -- this is
    # purely a claim in prose, and prose is where the reason for a rename lives. Nothing else
    # reads it.
    #
    # Deliberately narrow: only the "replac*/supersed*" verbs, and only a code matching the
    # page's own. A page may mention its own code freely for any other purpose.
    self_replacing = set()
    for p in pages:
        text = p.read_text(encoding="utf-8")
        m = re.search(r"^polity_code:\s*([A-Z0-9]+-\d{4}-\d{4})", text, re.M)
        if not m:
            continue
        own = m.group(1)
        for vm in re.finditer(r"(replac\w*|supersed\w*)\s+`([A-Z0-9]+-\d{4}-\d{4})`", text, re.I):
            if vm.group(2) == own:
                self_replacing.add((p.name, vm.group(1).lower()))
    for name, verb in sorted(self_replacing):
        problems.append(
            f"SELF-REPLACING PAGE: {name} says it {verb} its own polity_code -- name the code "
            f"it actually superseded, or the retired row is documented nowhere"
        )

    print(f"rows: {len(rows)}")
    print(f"pages claiming to replace themselves: {len(self_replacing)}")
    print(f"chain edges: {sum(len(links(r.get(f))) for r in rows for f in ('predecessor', 'successor')):,}")
    print(f"dead targets: {len(dead)} ({len(BASELINE_DEAD)} baselined)")
    print(f"cycles: {len(cycles)}")
    print(f"ceiling rows declaring a successor: {len(ceiling)} ({len(BASELINE_CEILING)} baselined, all dead)")
    print(f"broken page links: {len(broken)} ({len(BASELINE_LINKS)} baselined)")
    print(f"one-directional chain edges: {succ_only} successor-only, {pred_only} predecessor-only "
          f"(graph is {len(forward & backward) / max(len(forward | backward), 1):.0%} symmetric)")

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
