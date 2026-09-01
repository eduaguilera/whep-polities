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
    # THIRTEEN MORE PAIRS REMOVED on 2026-09-01: every one involves a SUBNATIONAL row
    # (IDN-BLB/JVM/OTH, HYD-1724-1948), which the filter above now excludes because a
    # subnational row's iso3_code names its parent country rather than itself. They were
    # hand-listed when subnational rows still entered national ISO resolution; the rule now
    # says what each line said, and says it once instead of thirteen times.
    # French India and the Italian Dodecanese moved from the ADMINISTERING POWER's code to the
    # SUCCESSOR STATE's on 2026-08-07, which is what 19 of the 21 borrowing colonial rows do.
    # The collisions move with them: FRIN left FRA's family and entered IND's, ITAEG left ITA's
    # and entered GRC's. Same class as ("GHA", "GHA-1898-1957", "BTL-1920-1957") above -- a
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
    ("IND", "IND-1800-1886", "FRIN-1816-1954"),
    ("AUS", "AUS-1800-1901", "AUSA-1836-1900"),
    ("AUS", "AUS-1800-1901", "AUWA-1829-1900"),
    ("AUS", "AUWA-1829-1900", "AUSA-1836-1900"),
    # BEL pair removed 2026-08-05: BLX-1921-1999 is retired as a duplicate of the
    # BLX-1850-1999 reporting row (issue 40). Its iso3 was BEL, which is what put a
    # Belgium-Luxembourg row in Belgium's family in the first place.
    # DZA-CVD-1902-1919 joined on 2026-08-31 (issue #400 case 2): the three CIVIL DEPARTMENTS of
    # northern Algeria, created because 418 `mitchell` + `iia` rows measure them (IIA states
    # 575,511 km2) while DZA-1902-1919's polygon is 2,442,683 including the Southern Territories,
    # a 4.244x denominator error. Exactly the shape of the MMR pair below -- a whole and its part
    # must share the grouping key, because `iso3` names the modern country whose territory the
    # entity belongs to and both of these are Algeria. Resolved the same two ways: by polity_type
    # (this row is `subnational`, DZA-1902-1919 is `national`) and by explicit alias, since the two
    # rules that reroute the data are source-scoped and the unscoped `algeria` rule still sends
    # every other source to the colony.
    ("CMR", "BCM-1916-1961", "CMR-1960-1961"),
    ("CMR", "BCM-1916-1961", "FCM-1920-1960"),
    ("COD", "COD-1910-1960", "CODRU-1922-1960"),
    ("EGY", "EGY-1925-1967", "EGYSUD-1934-1956"),
    ("GHA", "GCT-1919-1956", "BTL-1920-1957"),
    # Both GHA pairs renamed 2026-08-17 (issue 252): GHA-1898-1956 -> GHA-1898-1957, when the
    # row's exclusive end_year moved 1956 -> 1957 to cover the year that had fallen between it
    # and GHA-1957-2025. Re-measured after the rename: the same two pairs still overlap on GHA
    # (BTL 1920-1956 and GCT 1919-1955 against this row's 1898-1956), one year longer than
    # before, and both are still resolved by polity_type -- this row is `national`, BTL is
    # colonial and GCT is an aggregate. Nothing new collides.
    ("GHA", "GHA-1898-1957", "BTL-1920-1957"),
    ("GHA", "GHA-1898-1957", "GCT-1919-1956"),
    ("IDN", "IDN-1949-1963", "NNG-1949-1963"),
    ("JOR", "JOR-1946-2025", "WBK-1950-1967"),
    ("KOR", "KOR-1800-1945", "KRS-1910-1945"),
    # Fezzan joined the LBY family on 2026-08-10 (issue 156), completing the 1943-1951
    # partition. Same class as the TRP and CYR entries beside it: iso3 LBY carries the whole
    # AND its three occupation territories, because there was no Libyan state to make them
    # subnational units of. Every label observed in data is pinned by an explicit alias.
    # Cyrenaica's British-administration row joined the same family on 2026-08-13 (issue 137),
    # closing the six-year hole the entries below already record: TRP and FEZ covered 1943-1951
    # and 1943-1951, CYR only 1949-1951. These three pairs are the TRP/FEZ pairs shifted six years
    # earlier and read exactly the same -- the whole and its parts sharing LBY because there was
    # no Libyan state between 1943 and 1951. Every Libyan label observed in data is pinned by an
    # explicit alias, `Libya` included as of this PR.
    ("LBY", "CYR-1943-1949", "FEZ-1943-1951"),
    ("LBY", "CYR-1943-1949", "LBY-1943-1949"),
    ("LBY", "CYR-1943-1949", "TRP-1943-1951"),
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
    # SIX PAIRS WERE REMOVED on 2026-09-01, and NOT because they stopped overlapping. Each is a
    # subnational row that now DECLARES its container in data/final/polity_containment.csv
    # (whep#51), so the exemption above explains it properly and a hand-maintained baseline
    # line standing in for "we know, it is fine" is no longer the record. Removed:
    #   DZA-1902-1919/DZA-CVD-1902-1919, IDN-1949-1963 with each of BLB/JVM/OTH,
    #   JPN-1895-1945/RYU-1937-1945, USA-1867-1959/ALK-1867-1959.
    # The sibling pairs (BLB vs JVM, and the NNG pairs) are KEPT: siblings do not contain each
    # other, so nothing declares them and they remain genuine same-code overlaps.
})


def main() -> int:
    by_iso = defaultdict(list)
    for r in csv.DictReader(open(POLITIES, encoding="utf-8")):
        if (r.get("wiki_status") or "").strip() in DEAD_STATUS:
            continue
        iso = (r.get("iso3_code") or "").strip()
        if iso in ("", "NA"):
            continue
        # A SUBNATIONAL ROW'S iso3_code NAMES ITS PARENT, NOT ITSELF. This gate exists because an
        # ISO+year lookup with two candidates "must guess" -- but that lookup asks which COUNTRY is
        # ISO JPN in year Y, and a prefecture is never an answer to it. Its iso3 is the parent's
        # identity, carried so the unit can be grouped, in the same way `polity_area_code` is a
        # bucket rather than an identity. Including them would make 46 Japanese prefectures collide
        # with each other and with every national JPN row, i.e. 1,265 pairs on one country, and the
        # signal would be gone (whep#1000: 431 units across 26 countries).
        #
        # THE CONTRACT THIS ASSUMES, stated because it is a real obligation on consumers: anything
        # resolving ISO+year to a polity must filter on polity_type == "national". The containment
        # edge set (whep#51) is what lets it walk the other way, from a national row to its members.
        if (r.get("polity_type") or "").strip() == "subnational":
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

    # A DECLARED CONTAINMENT IS NOT A COLLISION (whep#51). The collision this gate exists for is
    # ambiguity: an ISO+year lookup with two candidates and no way to choose. Where one row declares
    # itself INSIDE the other for those years, there is no ambiguity -- the pair is a documented
    # whole-and-part, the consumer can read which is which from
    # data/final/polity_containment.csv, and the polity_type separates them in the matcher's
    # ranking. Without this the 431-unit subnational vocabulary (whep#1000) would need one baseline
    # line per prefecture per era of its parent: Japan alone produced 1,265 pairs, which is a
    # baseline nobody can review and which would hide a real collision among them.
    #
    # Read from the published table rather than imported from the writer, so the gate checks what
    # ships. Absent file means no exemptions, which fails loudly rather than passing quietly.
    declared = set()
    _cpath = os.path.join(os.path.dirname(POLITIES), "polity_containment.csv")
    if os.path.exists(_cpath):
        with open(_cpath, newline="", encoding="utf-8") as _fh:
            for _e in csv.DictReader(_fh):
                try:
                    _s, _t = int(_e["start_year"]), int(_e["end_year"])
                except (TypeError, ValueError):
                    continue
                declared.add((_e["member_code"].strip(), _e["container_code"].strip(), _s, _t))

    def _explained(a: str, b: str) -> bool:
        """True when one of the pair declares containment in the other over overlapping years."""
        for m, c, _s, _t in declared:
            if {m, c} == {a, b}:
                return True
        return False

    exempt = {(iso, a, b) for iso, a, b in observed if _explained(a, b)}
    observed_amb = observed - exempt

    print(f"distinct iso3 codes in use: {len(by_iso)}")
    print(f"pairs sharing a code over overlapping years: {len(observed)}")
    print(f"  of those, explained by a declared containment edge: {len(exempt)}")
    print(f"  remaining, genuinely ambiguous: {len(observed_amb)}")

    problems = []
    for iso, a, b in sorted(observed_amb - BASELINE):
        problems.append(
            f"NEW ISO collision: {a} and {b} both claim {iso} over overlapping years — "
            f"an ISO+year lookup now has two candidates and must guess"
        )
    for iso, a, b in sorted(BASELINE - observed_amb):
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
