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

A SECOND check (issue 653) asks a different question: does the code belong to the row's own
country at all? `data/external/cow_state_system.csv` gives every COW code its iso3, so a row whose
`iso3_code` differs from its code's iso3 is either one of the deliberate cases below or a wrong
value. Three rows were wrong and nothing noticed: IDN-1800-1889 and IDN-1889-1945 carried 750
(India) and NNI-1899-1904 / NNI-1904-1913 carried 385 (Norway). The collision check above could
not see them -- the Norway one hid among the baselined shares, the Indonesia ones sat on superseded
rows it skips -- and the polygon pipeline never reads the column, so they corrupted nothing until
a join on it (#651) landed on the wrong country.

The deliberate mismatches are baselined in ISO3_BASELINE, each with its reason: a row whose iso3
is a historical entity name COW files under its successor (OTT/TUR, YUG/SRB, SUN/RUS), or a
dependent territory that carries its metropole's code (FRIN/FRA, ITAEG/ITA). The set may not
grow, and it may not hold an entry that has since been fixed. Rows with no iso3, and codes COW
files under no iso3 ("NA", e.g. East Germany 265), cannot be tested and are skipped.

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

    ("220", "FRA-1800-1860", "FRIN-1816-1954"),
    ("220", "FRIN-1816-1954", "FRA-1860-1871"),
    ("220", "FRIN-1816-1954", "FRA-1871-1919"),
    ("220", "FRIN-1816-1954", "FRA-1919-2025"),
    ("235", "PRT-1800-2025", "PTIND-1816-1961"),
    ("260", "DEU-1938-1945", "WZO-1938-1949"),
    ("260", "WZO-1938-1949", "DEU-1945-1949"),
    ("325", "ITA-1870-1919", "ITAEG-1912-1947"),
    ("325", "ITAEG-1912-1947", "ITA-1919-1947"),
    # MNE pair removed 2026-08-05: MNE-1913-1915 is retired (issue 62).

    ("380", "SNW-1814-1905", "SWE-1814-1905"),
    # NOR/NNI pairs removed (issue 653): NNI-1899-1904 and NNI-1904-1913 carried 385, which is
    # Norway's. They now carry 475, Nigeria's -- the code NGA-1914-1960 already uses.
    # Renamed 2026-08-17 (issue 252): GHA-1898-1956 -> GHA-1898-1957, when the row's exclusive
    # end_year moved 1956 -> 1957 to cover the 1956 hole. The shared cow 452 is unchanged, and so
    # is the reason -- GCT-1919-1956 is the Gold-Coast-plus-Togoland reporting aggregate, which
    # COW has no separate code for.
    ("452", "GHA-1898-1957", "GCT-1919-1956"),
    # Fezzan, added 2026-08-10 (issue 156). cow 620 is Libya; the three occupation
    # territories share it for the same reason they share iso3 LBY -- COW has no code for a
    # military administration, and inventing one would assert an entity COW does not model.
    # British Cyrenaica, added 2026-08-13 (issue 137), on identical grounds: cow 620 is all of
    # Libya and COW codes no military administration separately, so the fourth occupation-era row
    # shares it exactly as the other three do.
    ("620", "CYR-1943-1949", "FEZ-1943-1951"),
    ("620", "CYR-1943-1949", "LBY-1943-1949"),
    ("620", "CYR-1943-1949", "TRP-1943-1951"),
    ("620", "FEZ-1943-1951", "CYR-1949-1951"),
    ("620", "FEZ-1943-1951", "LBY-1949-1951"),
    ("620", "FEZ-1943-1951", "TRP-1943-1951"),
    ("620", "LBY-1943-1949", "FEZ-1943-1951"),
    ("620", "CYR-1949-1951", "LBY-1949-1951"),
    ("620", "LBY-1943-1949", "TRP-1943-1951"),
    ("620", "TRP-1943-1951", "CYR-1949-1951"),
    ("620", "TRP-1943-1951", "LBY-1949-1951"),
    # CYR-1943-1949, added 2026-08-13 (issue 198): the British military administration of
    # Cyrenaica, which had no row while TRP and FEZ covered 1943-1951 in full. Same reasoning as
    # the block above -- COW has no code for a military administration, so 620 is inherited.
    ("620", "CYR-1943-1949", "FEZ-1943-1951"),
    ("620", "CYR-1943-1949", "LBY-1943-1949"),
    ("620", "CYR-1943-1949", "TRP-1943-1951"),
    ("640", "OTT-1800-1886", "TUR-1800-1913"),
    ("640", "TUR-1800-1913", "OTT-1886-1908"),
    ("640", "TUR-1800-1913", "OTT-1908-1912"),
    ("750", "HYD-1724-1948", "IND-1800-1886"),
    ("750", "HYD-1724-1948", "IND-1886-1893"),
    ("750", "HYD-1724-1948", "IND-1893-1914"),
    ("750", "HYD-1724-1948", "IND-1914-1937"),
    ("750", "HYD-1724-1948", "IND-1937-1947"),
    ("750", "HYD-1724-1948", "IND-1947-1949"),})

COW_STATES = os.path.join(REPO, "data/external/cow_state_system.csv")

# (polity_code, cow_code) for every row whose iso3_code differs from the iso3 COW files its code
# under, and is correct anyway. Generated from the database, not hand-listed.
ISO3_BASELINE = frozenset({
    # Soviet Union and Yugoslavia: COW 365 is "Russia/USSR" and 345 "Yugoslavia/Serbia", filed under
    # the successor iso3 (RUS, SRB); the rows carry the historical entity's own iso3.
    ("F228-1921-1940", "365"), ("F228-1940-1945", "365"), ("F228-1945-1991", "365"),
    ("F248-1918-1919", "345"), ("F248-1919-1920", "345"), ("F248-1920-1947", "345"),
    ("F248-1920-1991", "345"), ("F248-1947-1991", "345"), ("F248-1991-1992", "345"),
    ("SER-1878-1913", "345"),
    # Ottoman Empire: COW 640 is Turkey throughout.
    ("OTT-1800-1886", "640"), ("OTT-1886-1908", "640"), ("OTT-1908-1912", "640"),
    # Pre-unification Italian states and Sweden-Norway's Swedish half: COW has no code for the
    # pre-1861 states, so Sardinia carries Italy's 325; SNW carries Sweden's 380.
    ("SAR-1800-1860", "325"), ("SNW-1814-1905", "380"),
    # Colonial rows carrying the metropole's code, the established pattern (see above).
    ("FRIN-1816-1954", "220"), ("ITAEG-1912-1947", "325"),
    # Northern Nigeria: a protectorate with no COW code of its own; carries the successor state's
    # 475 like NGA-1914-1960, while its own iso3 is NNI (issue 653).
    ("NNI-1899-1904", "475"), ("NNI-1904-1913", "475"),
    # Kosovo: the same country, COW files it under the user-assigned XKX and the row uses KOS.
    ("KOS-2008-2025", "347"),
    # German colonies in Oceania: a retired aggregate carrying its metropole's code.
    ("GCO-1884-2025", "255"),
})


def iso3_observed() -> set:
    """Rows whose iso3_code disagrees with the iso3 COW files their cow_code under."""
    cow_iso = {}
    with open(COW_STATES, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            cow_iso[r["cow_code"].strip()] = (r.get("iso3") or "").strip()
    out = set()
    with open(POLITIES, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            cow = (r.get("cow_code") or "").strip()
            iso = (r.get("iso3_code") or "").strip()
            ref = cow_iso.get(cow, "")
            if cow in ("", "NA") or not iso or ref in ("", "NA"):
                continue
            if iso != ref:
                out.add((r["polity_code"], cow))
    return out


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

    iso_obs = iso3_observed()
    print(f"rows whose cow_code belongs to another iso3: {len(iso_obs)}")
    for code, cow in sorted(iso_obs - ISO3_BASELINE):
        problems.append(
            f"{code} carries cow {cow}, which COW files under a different iso3 than the row's own "
            f"-- a wrong code (check data/external/cow_state_system.csv), or a deliberate "
            f"successor/metropole convention to add to ISO3_BASELINE with its reason"
        )
    for code, cow in sorted(ISO3_BASELINE - iso_obs):
        problems.append(
            f"{code} no longer carries cow {cow} against another iso3 -- remove it from ISO3_BASELINE"
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
