#!/usr/bin/env python3
"""Check that no NEW pair of polities comes to share an ISO code over the same years.

`iso3` in this database is a territorial grouping key, not a unique identifier: it names
the modern country whose territory a historical entity belongs to. So overlapping entities
sharing a code is by DESIGN, not a defect — British North Borneo, Sarawak and British
Malaya all carry MYS for the same years, as do Hyderabad State and British India with IND.
Fifty-nine such pairs exist and this script does not object to them.

What it objects to is the set GROWING. Resolving by ISO plus year is already ambiguous in
those 59 cases, and the matcher must fall back on tie-break order to choose — which is the
documented cause of FAOSTAT area 131 resolving "Malaysia" in 1961 to British North Borneo
(issue 44). Every new pair adds another place that can happen.

The reason this gate exists now: this branch corrected three `iso3` fields on the principle
that the field names the TERRITORY rather than the era — ANG-1905-1975 to AGO,
FRS-1884-1977 to DJI, SUD-1956-2011 to SDN — which made two colonial FAOSTAT mappings
resolvable and shrank crosscheck_matchers.py's unresolved baseline from three areas to one.
That pattern is worth repeating for other chains, and it is exactly the pattern that could
introduce ambiguity if applied to a pair whose spans OVERLAP. All three of these were safe
(1905-1975 against 1975-2025, and so on: adjacent, never overlapping) and added zero
collisions. This gate is what keeps the next one honest.

Not a substitute for audit_family_shadowing.py, which asks a different question: that one is
about family ordering within a prefix, this one about a code shared ACROSS prefixes.

Usage:
  python3 scripts/validate_iso_collisions.py
"""
import csv
import os
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLITIES = os.path.join(REPO, "data/final/polities_database.csv")

DEAD_STATUS = ("retired", "superseded")

# (iso3, earlier polity, later polity) for every pair that already shares a code over
# overlapping years. Generated from the database, not hand-listed.
BASELINE = frozenset({
    # French India and the Italian Dodecanese moved from the ADMINISTERING POWER's code to the
    # SUCCESSOR STATE's on 2026-08-07, which is what 19 of the 21 borrowing colonial rows do.
    # The collisions move with them: FRIN left FRA's family and entered IND's, ITAEG left ITA's
    # and entered GRC's. Same class as ("GHA", "GHA-1898-1956", "BTL-1920-1957") above -- a
    # colonial row borrowing its successor's code necessarily overlaps that successor's periods.
    # Every one is resolved by polity_type: the IND and GRC rows are `national`, these are not.
    ("GRC", "GRC-1881-1913", "ITAEG-1912-1947"),
    ("GRC", "ITAEG-1912-1947", "GRC-1913-1919"),
    ("GRC", "ITAEG-1912-1947", "GRC-1919-1947"),
    ("IND", "FRIN-1816-1954", "IND-1886-1893"),
    ("IND", "FRIN-1816-1954", "IND-1893-1914"),
    ("IND", "FRIN-1816-1954", "IND-1914-1937"),
    ("IND", "FRIN-1816-1954", "IND-1937-1947"),
    ("IND", "FRIN-1816-1954", "IND-1947-1949"),
    ("IND", "FRIN-1816-1954", "IND-1949-2025"),
    ("IND", "HYD-1724-1948", "FRIN-1816-1954"),
    ("IND", "IND-1800-1886", "FRIN-1816-1954"),
    ("AUS", "AUS-1800-1901", "AUSA-1836-1900"),
    ("AUS", "AUS-1800-1901", "AUWA-1829-1900"),
    ("AUS", "AUWA-1829-1900", "AUSA-1836-1900"),
    # BEL pair removed 2026-08-05: BLX-1921-1999 is retired as a duplicate of the
    # BLX-1850-1999 reporting row (issue 40). Its iso3 was BEL, which is what put a
    # Belgium-Luxembourg row in Belgium's family in the first place.
    ("CMR", "BCM-1916-1961", "CMR-1960-1961"),
    ("CMR", "BCM-1916-1961", "FCM-1920-1960"),
    ("COD", "COD-1910-1960", "CODRU-1922-1960"),
    ("EGY", "EGY-1925-1967", "EGYSUD-1934-1956"),
    ("GHA", "GCT-1919-1956", "BTL-1920-1957"),
    ("GHA", "GHA-1898-1956", "BTL-1920-1957"),
    ("GHA", "GHA-1898-1956", "GCT-1919-1956"),
    ("IDN", "IDN-BLB-1949-1951", "IDN-1949-1969"),
    ("IDN", "IDN-BLB-1949-1951", "IDN-JVM-1949-1951"),
    ("IDN", "IDN-BLB-1949-1951", "IDN-OTH-1949-1951"),
    ("IDN", "IDN-BLB-1949-1951", "NNG-1949-1963"),
    ("IDN", "IDN-JVM-1949-1951", "IDN-1949-1969"),
    ("IDN", "IDN-JVM-1949-1951", "IDN-OTH-1949-1951"),
    ("IDN", "IDN-JVM-1949-1951", "NNG-1949-1963"),
    ("IDN", "IDN-OTH-1949-1951", "IDN-1949-1969"),
    ("IDN", "IDN-OTH-1949-1951", "NNG-1949-1963"),
    ("IDN", "NNG-1949-1963", "IDN-1949-1969"),
    ("IND", "HYD-1724-1948", "IND-1800-1886"),
    ("IND", "HYD-1724-1948", "IND-1886-1893"),
    ("IND", "HYD-1724-1948", "IND-1893-1914"),
    ("IND", "HYD-1724-1948", "IND-1914-1937"),
    ("IND", "HYD-1724-1948", "IND-1937-1947"),
    ("IND", "HYD-1724-1948", "IND-1947-1949"),
    ("JOR", "JOR-1946-2025", "WBK-1950-1967"),
    ("JPN", "JPN-1895-1945", "RYU-1937-1945"),
    ("KOR", "KOR-1800-1945", "KRS-1910-1945"),
    # Fezzan joined the LBY family on 2026-08-10 (issue 156), completing the 1943-1951
    # partition. Same class as the TRP and CYR entries beside it: iso3 LBY carries the whole
    # AND its three occupation territories, because there was no Libyan state to make them
    # subnational units of. Every label observed in data is pinned by an explicit alias.
    ("LBY", "FEZ-1943-1951", "CYR-1949-1951"),
    ("LBY", "FEZ-1943-1951", "LBY-1949-1951"),
    ("LBY", "FEZ-1943-1951", "TRP-1943-1951"),
    ("LBY", "LBY-1943-1949", "FEZ-1943-1951"),
    ("LBY", "CYR-1949-1951", "LBY-1949-1951"),
    ("LBY", "LBY-1943-1949", "TRP-1943-1951"),
    ("LBY", "TRP-1943-1951", "CYR-1949-1951"),
    ("LBY", "TRP-1943-1951", "LBY-1949-1951"),
    # CYR-1943-1949 joined on 2026-08-13 (issue 198), the British military administration of
    # Cyrenaica: the 1943-1948 window previously had TRP and FEZ but no Cyrenaica, because
    # CYR-1949-1951 is the EMIRATE and starts in 1949. Three more pairs, all the same class as
    # the eight above, and the ambiguity is resolved the same way -- by explicit alias, including
    # `Libya Cyrenaica` at 1948, which was resolving to NOTHING before this row existed.
    ("LBY", "CYR-1943-1949", "FEZ-1943-1951"),
    ("LBY", "CYR-1943-1949", "LBY-1943-1949"),
    ("LBY", "CYR-1943-1949", "TRP-1943-1951"),
    ("MMR", "MMR-1852-1885", "MMR-LWR-1852-1885"),
    # MNE pair removed 2026-08-05: MNE-1913-1915 is retired (issue 62).

    ("MYS", "BNB-1881-1963", "GBM-1895-1946"),
    ("MYS", "BNB-1881-1963", "MASG-1946-1963"),
    ("MYS", "BNB-1881-1963", "MYS-1946-1957"),
    ("MYS", "BNB-1881-1963", "MYS-1957-1963"),
    ("MYS", "BSW-1841-1963", "BNB-1881-1963"),
    ("MYS", "BSW-1841-1963", "GBM-1895-1946"),
    ("MYS", "BSW-1841-1963", "MASG-1946-1963"),
    # PAPNG-1920-1949 over its two constituents, added 2026-08-05. Same shape as the MASG and
    # CODRU entries above: a combined reporting unit necessarily shares its iso3 with the
    # polities it combines. An iso3+year lookup for PNG in 1920-1948 does have three answers,
    # and that is why every observed label is pinned by an explicit alias instead of left to
    # resolution order -- see validate_order_decided_families.
    ("PNG", "PAPNG-1920-1949", "TNGU-1920-1949"),
    ("PNG", "TPAP-1906-1949", "PAPNG-1920-1949"),
    ("MYS", "BSW-1841-1963", "MYS-1946-1957"),
    ("MYS", "BSW-1841-1963", "MYS-1957-1963"),
    ("MYS", "MASG-1946-1963", "MYS-1957-1963"),
    ("MYS", "MYS-1946-1957", "MASG-1946-1963"),
    ("NGA", "NUP-1800-1897", "NGA-1886-1914"),
    ("PAN", "CZN-1903-1979", "PAN-1903-1979"),
    # PER pairs removed 2026-08-05: PER-1825-1909 is superseded by the finer
    # PER-1825-1884 / PER-1884-1909 split (issue 49).

    ("PNG", "TPAP-1906-1949", "TNGU-1920-1949"),
    ("TUR", "TUR-1920-2025", "HATAY-1938-1939"),
    ("USA", "ALK-1867-1959", "USA-1867-1959"),})


def main() -> int:
    by_iso = defaultdict(list)
    for r in csv.DictReader(open(POLITIES, encoding="utf-8")):
        if (r.get("wiki_status") or "").strip() in DEAD_STATUS:
            continue
        iso = (r.get("iso3_code") or "").strip()
        if iso in ("", "NA"):
            continue
        code = r["polity_code"]
        try:
            y0 = int(code.rsplit("-", 2)[1])
            y1 = int(code.rsplit("-", 1)[1])
        except (IndexError, ValueError):
            continue
        by_iso[iso].append((y0, y1, code))

    observed = set()
    for iso, items in by_iso.items():
        items.sort()
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a, b = items[i], items[j]
                if min(a[1], b[1]) > max(a[0], b[0]):
                    observed.add((iso, a[2], b[2]))

    print(f"distinct iso3 codes in use: {len(by_iso)}")
    print(f"pairs sharing a code over overlapping years: {len(observed)}")

    problems = []
    for iso, a, b in sorted(observed - BASELINE):
        problems.append(
            f"NEW ISO collision: {a} and {b} both claim {iso} over overlapping years — "
            f"an ISO+year lookup now has two candidates and must guess"
        )
    for iso, a, b in sorted(BASELINE - observed):
        problems.append(
            f"{a} and {b} no longer collide on {iso} — remove the pair from the baseline"
        )

    if problems:
        print(f"\nFAIL: {len(problems)} change(s) against the baseline\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: ISO-code collisions match the baseline exactly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
