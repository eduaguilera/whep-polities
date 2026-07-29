#!/usr/bin/env python3
"""Check that two polities of DIFFERENT families do not share a name over the same years.

validate_period_overlaps.py catches overlaps within one prefix. It cannot see an overlap between
prefixes — and the same territory sometimes has two, because a legacy prefix and an ISO3 one coexist.
Normalising the names and comparing across families finds exactly those.

Three pairs, and all three share one signature: one row carries the ISO3 code, the observed data and
the FAOSTAT mapping, while the other carries a non-ISO legacy prefix as its `iso3`, zero observed
rows and no mapping.

  SER-2006-2008 / SRB-2006-2008   full overlap. The known duplicate (issue 43) — this method
                                  re-derived it independently, after observed_rows and the
                                  two-matcher disagreement.
  TAN-1922-1964 / TZA-1961-1964   overlap 1961-1964. TZA carries 219,893 observed rows, TAN none.
  MAR-1911-1958 / MOR-1956-1958   overlap 1956-1958. MAR carries 261 rows, MOR none.

The last two are NOT duplicates, which is the useful distinction. Tanganyika-era Tanzania and
independent Tanzania are different entities; so are protectorate Morocco and independent Morocco.
What is wrong is the earlier row's END year running past where its successor begins — Tanzania's
should stop at 1961 and Morocco's at 1956.

The impact is LATENT, not live, and it is worth being precise about that because I first wrote it up as
live. Neither inert row is mapped to a FAOSTAT area, so the consumer's add_polity_code() resolves 1962
to TZA-1961-1964 and MAR-1958-1975 deterministically and never sees the twins. That is unlike the
Malaysia case, which is ambiguous precisely because both candidates ARE reachable from area 131. What
remains is that two live polities claim the same years for the same territory, so a direct query on the
database is ambiguous, matchlib resolving by ISO/name family can reach both, and the end years are
historically wrong regardless.

Baselined rather than fixed: changing a polity's period is a data decision, and the wiki pages carry
the historical reasoning that should decide it. Reported on the issues instead.

Usage:
  python3 scripts/validate_cross_family_names.py
"""
import csv
import os
import re
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLITIES = os.path.join(REPO, "data/final/polities_database.csv")

DEAD_STATUS = ("retired", "superseded")

BASELINE = frozenset({
    ("MAR-1911-1958", "MOR-1956-1958"),
    ("SER-2006-2008", "SRB-2006-2008"),
    ("TAN-1922-1964", "TZA-1961-1964"),
})


def normalise(name: str) -> str:
    """Lowercase, drop parenthesised and bracketed qualifiers, squash punctuation.

    The qualifiers are what hide these: "Tanzania (1922-1964)" and "Tanzania (1961-1964)" are
    obviously the same name to a reader and obviously different strings to a computer.
    """
    out = name.lower()
    out = re.sub(r"\s*\([^)]*\)", "", out)
    out = re.sub(r"\s*\[[^\]]*\]", "", out)
    return re.sub(r"[^a-z0-9]+", " ", out).strip()


def faostat_mapped() -> set:
    """Polity codes a consumer can reach through the published FAOSTAT area map.

    Whether a finding is LIVE or merely LATENT turns on this, and it is cheap to compute here rather
    than by querying the consumer. Two findings on this branch were written up as live and had to be
    downgraded after checking: the Tanzania and Morocco period overlaps, whose inert twins are
    unmapped, and area 240's two-era mapping, which is correctly folded. Printing reachability next
    to each case makes the distinction visible instead of remembered.
    """
    path = os.path.join(REPO, "data/final/faostat_area_polity_map.csv")
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as fh:
        return {
            (r.get("polity_code") or "").strip()
            for r in csv.DictReader(fh)
            if (r.get("polity_code") or "").strip()
        }


def main() -> int:
    by_name = defaultdict(list)
    live = 0
    for r in csv.DictReader(open(POLITIES, encoding="utf-8")):
        if (r.get("wiki_status") or "").strip() in DEAD_STATUS:
            continue
        live += 1
        code = r["polity_code"]
        try:
            y0 = int(code.rsplit("-", 2)[1])
            y1 = int(code.rsplit("-", 1)[1])
        except (IndexError, ValueError):
            continue
        by_name[normalise(r["polity_name"])].append((y0, y1, code))

    observed = set()
    for items in by_name.values():
        items.sort()
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a, b = items[i], items[j]
                same_family = a[2].rsplit("-", 2)[0] == b[2].rsplit("-", 2)[0]
                overlaps = min(a[1], b[1]) > max(a[0], b[0])
                if not same_family and overlaps:
                    observed.add(tuple(sorted((a[2], b[2]))))

    print(f"live polities: {live}")
    print(f"distinct normalised names: {len(by_name)}")
    print(f"cross-family name collisions over overlapping years: {len(observed)}")
    mapped = faostat_mapped()
    for a, b in sorted(observed):
        reach = sum(1 for c in (a, b) if c in mapped)
        tag = {0: "latent (neither mapped)", 1: "latent (one mapped)", 2: "LIVE (both mapped)"}[reach]
        print(f"   {a:<18} + {b:<18} {tag}")

    problems = []
    for pair in sorted(observed - BASELINE):
        problems.append(
            f"NEW cross-family name collision: {pair[0]} and {pair[1]} share a name over "
            f"overlapping years — either they are duplicates, or the earlier one's end year runs "
            f"past where its successor begins"
        )
    for pair in sorted(BASELINE - observed):
        problems.append(
            f"{pair[0]} and {pair[1]} no longer collide — remove the pair from the baseline"
        )

    if problems:
        print(f"\nFAIL: {len(problems)} change(s) against the baseline\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: cross-family name collisions match the baseline exactly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
