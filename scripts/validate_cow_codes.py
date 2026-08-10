#!/usr/bin/env python3
"""Check that no NEW pair of overlapping polities comes to share a Correlates of War code.

A COW code identifies a STATE in the Correlates of War system. Sharing one across overlapping
polities is therefore semantically odd, but it is also the established pattern here: a colonial
territory carries its metropole's code, so French India shares 220 with France, Portuguese India
shares 235 with Portugal, and the Italian Aegean Islands share 325 with Italy. Twenty-nine such
pairs exist and this script does not object to them.

What it objects to is the set GROWING, because a mis-typed COW code looks exactly like one of those
deliberate shares. Two have already been found by hand:

  FRS-1977-2025 carried 987, which is MICRONESIA, corrected to 522 (Djibouti) in an earlier pass
  ICN-1800-2025 (Canary Islands) carried 20, which is CANADA — five CAN-* polities carry it — and
    the Canaries are not a COW state at all. They are part of Spain, COW 230. Removed rather than set
    to 230: COW identifies states, this row is a sub-national territory, and giving it Spain's code
    would have created a collision instead of fixing one.

The second was found by exactly this check, run by hand, which is why it now exists as a script.
Note what neither an ISO check nor a polygon check would have caught: the Canaries' `iso3` and
geometry were both fine.

Usage:
  python3 scripts/validate_cow_codes.py
"""
import csv
import os
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLITIES = os.path.join(REPO, "data/final/polities_database.csv")

DEAD_STATUS = ("retired", "superseded")

# (cow_code, earlier polity, later polity) for every pair already sharing a code over overlapping
# years. Generated from the database, not hand-listed.
BASELINE = frozenset({
    # PER pairs removed 2026-08-05: PER-1825-1909 is superseded (issue 49).

    ("220", "FRA-1800-1871", "FRIN-1816-1954"),
    ("220", "FRIN-1816-1954", "FRA-1871-1919"),
    ("220", "FRIN-1816-1954", "FRA-1919-2025"),
    ("235", "PRT-1800-2025", "PTIND-1816-1961"),
    ("260", "DEU-1938-1945", "WZO-1938-1949"),
    ("260", "WZO-1938-1949", "DEU-1945-1949"),
    ("325", "ITA-1870-1919", "ITAEG-1912-1947"),
    ("325", "ITAEG-1912-1947", "ITA-1919-2025"),
    # MNE pair removed 2026-08-05: MNE-1913-1915 is retired (issue 62).

    ("380", "SNW-1814-1905", "SWE-1814-1905"),
    ("385", "NOR-1800-2025", "NNI-1899-1904"),
    ("385", "NOR-1800-2025", "NNI-1904-1913"),
    ("411", "STP-1800-2025", "GNQ-1886-1968"),
    ("452", "GHA-1898-1956", "GCT-1919-1956"),
    # Fezzan, added 2026-08-10 (issue 156). cow 620 is Libya; the three occupation
    # territories share it for the same reason they share iso3 LBY -- COW has no code for a
    # military administration, and inventing one would assert an entity COW does not model.
    ("620", "FEZ-1943-1951", "CYR-1949-1951"),
    ("620", "FEZ-1943-1951", "LBY-1949-1951"),
    ("620", "FEZ-1943-1951", "TRP-1943-1951"),
    ("620", "LBY-1943-1949", "FEZ-1943-1951"),
    ("620", "CYR-1949-1951", "LBY-1949-1951"),
    ("620", "LBY-1943-1949", "TRP-1943-1951"),
    ("620", "TRP-1943-1951", "CYR-1949-1951"),
    ("620", "TRP-1943-1951", "LBY-1949-1951"),
    ("640", "OTT-1800-1886", "TUR-1800-1913"),
    ("640", "TUR-1800-1913", "OTT-1886-1908"),
    ("640", "TUR-1800-1913", "OTT-1908-1912"),
    ("750", "HYD-1724-1948", "IND-1800-1886"),
    ("750", "HYD-1724-1948", "IND-1886-1893"),
    ("750", "HYD-1724-1948", "IND-1893-1914"),
    ("750", "HYD-1724-1948", "IND-1914-1937"),
    ("750", "HYD-1724-1948", "IND-1937-1947"),
    ("750", "HYD-1724-1948", "IND-1947-1949"),})


def main() -> int:
    by_cow = defaultdict(list)
    live = 0
    for r in csv.DictReader(open(POLITIES, encoding="utf-8")):
        if (r.get("wiki_status") or "").strip() in DEAD_STATUS:
            continue
        live += 1
        cow = (r.get("cow_code") or "").strip()
        if cow in ("", "NA"):
            continue
        code = r["polity_code"]
        try:
            y0 = int(code.rsplit("-", 2)[1])
            y1 = int(code.rsplit("-", 1)[1])
        except (IndexError, ValueError):
            continue
        by_cow[cow].append((y0, y1, code))

    observed = set()
    for cow, items in by_cow.items():
        items.sort()
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a, b = items[i], items[j]
                if min(a[1], b[1]) > max(a[0], b[0]):
                    observed.add((cow, a[2], b[2]))

    print(f"live polities: {live}")
    print(f"carrying a cow_code: {sum(len(v) for v in by_cow.values())}")
    print(f"distinct cow_codes: {len(by_cow)}")
    print(f"pairs sharing a code over overlapping years: {len(observed)}")

    problems = []
    for cow, a, b in sorted(observed - BASELINE):
        problems.append(
            f"NEW cow_code collision: {a} and {b} both claim {cow} over overlapping years — "
            f"either one is a typo, or a colonial territory is newly sharing its metropole's code"
        )
    for cow, a, b in sorted(BASELINE - observed):
        problems.append(
            f"{a} and {b} no longer share cow {cow} — remove the pair from the baseline"
        )

    if problems:
        print(f"\nFAIL: {len(problems)} change(s) against the baseline\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: cow_code collisions match the baseline exactly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
