#!/usr/bin/env python3
"""Emit the member -> container edge set from the wiki, one row per (member, container, era).

WHY THIS EXISTS (whep#51, and the 455-unit subnational plan in whep#1000). `predecessor` and
`successor` express SUCCESSION -- what came before and after. They cannot express CONTAINMENT: that
`SER-1918-1945` sat inside Yugoslavia while it existed, or that `ROW-1850-2025` contains its promoted
members. whep#51 records the cost: of 27 aggregate polities, 19 get containment only through a
`polycell_support` overlap layer that needs a multi-GB spatial rebuild, and 8 have no route at all.

THE INTERVAL LIVES ON THE EDGE, NOT ON THE POLITY, and that is the whole design. Two reasons, both
load-bearing:

  1. A CONTAINER CAN CHANGE WHILE THE TERRITORY PERSISTS. Alsace-Lorraine was inside Germany
     1871-1918 and inside France otherwise -- one province, one continuous territory, two containers.
     Put the interval on the polity and you must invent a second polity per container, which is the
     fabrication this vocabulary has been removing. Put it on the edge and it is one row per era.
  2. IT NESTS DEEPER THAN TWO LEVELS. country -> state -> municipality is already in view for Brazil
     (IBGE PAM is municipal), so a single `parent` column would not survive first contact.

`MAN-1945-1950` is the proof in the existing data: it spans 1945-1949 and its container changes
twice inside that span (CHN-1945-1947, then CHN-1947-1949, then CHN-1949-1950). Three edges, one
member, no duplicated polities.

WHAT IT IS NOT. Not inference. This writer states only containment already asserted on a page, in the
same spirit as whep#51's scope boundary -- it does not derive containment from geometry, from
`polity_type == "subnational"`, or from a parent's name appearing in a member's name string. Those
name strings ("Burundi (within Ruanda-Urundi)") are what this replaces, and eleven of them are the
first migration customers: if the edge set cannot reproduce their parents, it is wrong.

AND A CONTAINER CODE IS AN IDENTITY, NOT A BUCKET. `polity_area_code` is an aggregation bucket; this
column names a polity that exists in its own right. Conflating the two silently misattributes data.

Declared on the MEMBER's page, because the member is what knows its parents:

    container:
      - code: CHN-1945-1947
        start_year: 1945
        end_year: 1947
        basis: the Manchuria region inside the Republic of China, before the 1947 constitution

`end_year` is EXCLUSIVE, matching every other span in this repo.

Usage:
  python3 scripts/write_polity_containment.py [--check]
Exit 1 if --check finds the committed table stale, or if any declaration is malformed.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
WIKI = REPO / "wiki" / "polities"
DEST = REPO / "data" / "final" / "polity_containment.csv"
DB = REPO / "data" / "final" / "polities_database.csv"

COLUMNS = ("member_code", "container_code", "start_year", "end_year", "basis")


def frontmatter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    try:
        return yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError as exc:
        print(f"  ! YAML error in {path.name}: {exc}", file=sys.stderr)
        return None


def collect() -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    problems: list[str] = []
    for page in sorted(WIKI.glob("*.md")):
        fm = frontmatter(page)
        if not fm:
            continue
        member = str(fm.get("polity_code") or "").strip()
        decl = fm.get("container")
        if decl in (None, "", []):
            continue
        if not isinstance(decl, list):
            problems.append(f"{page.name}: `container` must be a LIST of mappings, got "
                            f"{type(decl).__name__} -- a bare code cannot carry an interval, which "
                            f"is the whole point of the edge")
            continue
        for i, e in enumerate(decl, start=1):
            if not isinstance(e, dict):
                problems.append(f"{page.name}: container entry {i} is not a mapping")
                continue
            code = str(e.get("code") or "").strip()
            miss = [k for k in ("code", "start_year", "end_year") if e.get(k) in (None, "")]
            if miss:
                problems.append(f"{page.name}: container entry {i} ({code or '?'}) is missing "
                                f"{miss}; an edge without an interval cannot express a container "
                                f"that changes")
                continue
            try:
                s, t = int(e["start_year"]), int(e["end_year"])
            except (TypeError, ValueError):
                problems.append(f"{page.name}: container entry {i} ({code}) has non-integer years")
                continue
            rows.append({"member_code": member, "container_code": code,
                         "start_year": s, "end_year": t,
                         "basis": str(e.get("basis") or "").strip()})
    rows.sort(key=lambda r: (r["member_code"], r["start_year"], r["container_code"]))
    return rows, problems


def render(rows: list[dict]) -> str:
    import io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(COLUMNS), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def main() -> int:
    rows, problems = collect()
    if problems:
        print(f"FAIL: {len(problems)} malformed container declaration(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1

    text = render(rows)
    members = {r["member_code"] for r in rows}
    changing = sorted({r["member_code"] for r in rows
                       if sum(1 for x in rows if x["member_code"] == r["member_code"]) > 1})

    if "--check" in sys.argv[1:]:
        if not DEST.exists():
            print(f"--check: FAIL — {DEST.relative_to(REPO)} does not exist; run without --check")
            return 1
        if DEST.read_text(encoding="utf-8") != text:
            print(f"--check: FAIL — {DEST.relative_to(REPO)} is stale\n")
            print("  the wiki declares containment this table does not carry")
            print("  Run python3 scripts/write_polity_containment.py")
            return 1
        print(f"--check: OK — {len(rows)} containment edge(s) over {len(members)} member(s) "
              f"match the wiki")
        return 0

    DEST.write_text(text, encoding="utf-8")
    print(f"wrote {DEST.relative_to(REPO)}: {len(rows)} edge(s) over {len(members)} member(s)")
    if changing:
        print(f"  members whose container CHANGES within their own span: {len(changing)} "
              f"({', '.join(changing)})")
        print(f"  -- these are the rows a `parent` column could not express")
    return 0


if __name__ == "__main__":
    sys.exit(main())
