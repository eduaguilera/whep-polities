#!/usr/bin/env python3
"""Containment edges name real polities, sit inside both spans, and cover every subnational row.

WHY THIS EXISTS (whep#51). `data/final/polity_containment.csv` is the member -> container edge set,
declared on member pages and emitted by `scripts/write_polity_containment.py`. It replaces the
parent-in-the-name-string pattern ("Burundi (within Ruanda-Urundi)"), which no consumer can read.

THE INTERVAL IS ON THE EDGE, and arms B and C are what make that meaningful: an edge that ran outside
either party's span would be asserting containment in a year when one of them did not exist. Two
members already need it -- MAN-1945-1950's container changes twice inside its own span and
SER-1918-1945's three times -- so a `parent` column would have to duplicate those polities to say
the same thing, which is the fabrication this vocabulary is removing.

ARM E IS THE ONE THAT MATTERS FOR THE MIGRATION. Every `subnational` polity must either declare a
container or be named in EXEMPT with a reason. Without that arm the name-string pattern simply
returns: a new subnational row lands with its parent in its title, nothing fails, and the edge set
quietly stops being the answer to "what contains this". The 455-unit subnational plan (whep#1000)
makes that the difference between a vocabulary and a habit.

A CONTAINER CODE IS AN IDENTITY, NOT A BUCKET. This gate checks the code against the polity table,
never against an aggregation vocabulary -- conflating the two is what silently misattributes data.

Six checks:
  A. REAL CODES — every member and container exists in polities_database.csv.
  B. INSIDE THE MEMBER — the edge's years lie within the member's own span.
  C. INSIDE THE CONTAINER — the edge's years lie within the container's span.
  D. NO SELF- OR MUTUAL CONTAINMENT — a polity may not contain itself, and two polities may not
     contain each other over overlapping years.
  E. COVERAGE — every subnational polity declares a container or is exempt with a reason.
  F. LIVE — the edge set is not empty, so A-E cannot pass by having nothing to check.
"""
from __future__ import annotations

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EDGES = os.path.join(REPO, "data/final/polity_containment.csv")
DB = os.path.join(REPO, "data/final/polities_database.csv")

# Subnational rows that legitimately have no container edge, each with the reason. Restated here
# rather than read from the pages: an exemption is a decision, and it should be visible in the gate
# that would otherwise fail.
EXEMPT = {
    # Hyderabad was a princely state under British SUZERAINTY, not a province of British India.
    # Asserting HYD ⊂ IND-* would be inference from the map rather than a relation the sources
    # state, which is exactly the boundary whep#51 draws for this edge set. Left unclaimed until a
    # source states it.
    "HYD-1724-1948": "princely state under suzerainty, not part of British India proper",
}


def main() -> int:
    if not os.path.exists(EDGES):
        print(f"FAIL: {os.path.relpath(EDGES, REPO)} missing; run "
              f"scripts/write_polity_containment.py")
        return 1
    with open(EDGES, newline="", encoding="utf-8") as fh:
        edges = list(csv.DictReader(fh))
    with open(DB, newline="", encoding="utf-8") as fh:
        db = {r["polity_code"]: r for r in csv.DictReader(fh)}

    def span(code):
        r = db.get(code)
        if not r:
            return None
        try:
            return int(r["start_year"]), int(r["end_year"])
        except (TypeError, ValueError):
            return None

    problems: list[str] = []

    # --- F: live ---
    if not edges:
        problems.append(
            "F: the edge set is EMPTY, so checks A-E have nothing to iterate. That is reported rather "
            "than passed: an empty containment table means no polity states what contains it.")

    pairs = set()
    for e in edges:
        m, c = e["member_code"].strip(), e["container_code"].strip()
        try:
            s, t = int(e["start_year"]), int(e["end_year"])
        except (TypeError, ValueError):
            problems.append(f"A: {m} -> {c} has non-integer years")
            continue

        # --- A: real codes ---
        for role, code in (("member", m), ("container", c)):
            if code not in db:
                problems.append(f"A: {m} -> {c}: the {role} code {code!r} is not in "
                                f"polities_database.csv. A containment edge naming a code that "
                                f"does not exist is invisible to every traversal that reads it.")
        if m not in db or c not in db:
            continue

        # --- D: self / mutual ---
        if m == c:
            problems.append(f"D: {m} contains itself")
        if (c, m) in pairs:
            problems.append(f"D: {m} and {c} each declare the other as container over overlapping "
                            f"years; containment is not symmetric")
        pairs.add((m, c))

        # --- B: inside the member's own span ---
        ms, mt = span(m)
        if not (ms <= s and t <= mt):
            problems.append(f"B: {m} -> {c} covers {s}-{t} but the member's own span is {ms}-{mt}. "
                            f"An edge outside the member's life asserts containment for a polity "
                            f"that did not exist in those years.")

        # --- C: inside the container's span ---
        cs, ct = span(c)
        if not (cs <= s and t <= ct):
            problems.append(f"C: {m} -> {c} covers {s}-{t} but the container's span is {cs}-{ct}. "
                            f"Either the interval is wrong or the container is -- this is the check "
                            f"that catches a member attached to the wrong era of its parent.")

    # --- E: coverage ---
    declared = {e["member_code"].strip() for e in edges}
    subnational = {code for code, r in db.items() if r.get("polity_type") == "subnational"}
    uncovered = sorted(subnational - declared - set(EXEMPT))
    for code in uncovered:
        problems.append(
            f"E: {code} is a subnational polity that declares no container and is not in EXEMPT. "
            f"Add a `container:` block to wiki/polities/{code.lower()}.md, or list it in EXEMPT "
            f"with the reason. Without this the parent goes back into the name string, where no "
            f"consumer can read it.")
    stale_exempt = sorted(set(EXEMPT) & declared)
    for code in stale_exempt:
        problems.append(f"E: {code} is in EXEMPT but now declares a container; remove the exemption "
                        f"so the list stays a record of live decisions.")

    changing = sorted({m for m in declared
                       if sum(1 for e in edges if e["member_code"].strip() == m) > 1})
    print(f"{len(edges)} containment edge(s) over {len(declared)} member(s); "
          f"{len(subnational)} subnational polit(ies), {len(EXEMPT)} exempt")
    print(f"  members whose container changes within their own span: {len(changing)} "
          f"{changing if changing else ''}")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1
    print("\nPASS: every containment edge names real polities, sits inside both spans, and every "
          "subnational polity states what contains it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
