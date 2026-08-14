#!/usr/bin/env python3
"""Check that every dissolved state with an ISO 3166-3 code is coded by ONE rule.

ISO 3166-3 is the register of alpha-3 codes withdrawn because the entity stopped
existing: `SUHH` carries the USSR's former `SUN`, `CSHH` Czechoslovakia's `CSK`,
`ZRCD` Zaire's `ZAR`. This database contains polities for a dozen such entities, and
`iso3_code` is the field a consumer joins on, so how those polities are coded decides
whether the consumer can reach them at all.

Issue 55 was filed because three treatments appeared to coexist -- own historic code
(`ANT`, `SCG`), a successor's modern code (`MMR` for Burma, `TLS` for East Timor), and
nothing at all (Czechoslovakia, Yugoslavia, East Germany, the USSR). Only the third was
a defect. The other two are ONE rule seen from two sides, and this gate is that rule
written down as a check rather than left as a comment, which is what the issue asked for:

  If the entity's own polity family CONTINUES into a live polity -- the state still
  exists and only its name and code changed -- every row of the family carries the LIVE
  polity's ISO 3166-1 code, and the 3166-3 code is carried by nobody. Burma became
  Myanmar, Zaire became the DR Congo, Southern Rhodesia became Zimbabwe, the French
  Territory of the Afars and the Issas became Djibouti.

  If the family TERMINATES -- the state dissolved, and its successors are other
  families -- every row in the entity's span carries the entity's OWN 3166-3 code.
  Czechoslovakia, Yugoslavia, the USSR, the Netherlands Antilles, Serbia and Montenegro,
  the Pacific Islands Trust Territory. East Germany is here too: its single successor
  DEU is a live country in its own family, so inheriting DEU would have put an
  East German row in Germany's ISO family -- the failure mode that made "Malaysia"
  resolve to British North Borneo (issue 44).

Note what is NOT hardcoded. Which polities represent an entity is a judgement and is
listed below; the VERDICT -- own code or successor's code -- is derived from whether the
listed rows reach a live polity, so the rule is tested rather than restated. A polity
appearing under the wrong entity, or an entity gaining a live continuation it did not
have, changes the expectation automatically.

Bidirectional, like the other baselines here: a member that stops carrying the expected
code fails, and so does a "continues" entity whose 3166-3 code starts being used.

Usage:
  python3 scripts/validate_dissolved_iso_codes.py
"""
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLITIES = os.path.join(REPO, "data/final/polities_database.csv")

DEAD_STATUS = ("retired", "superseded")

# The year at which a row is still current. RUS-2014-2025 is live and `end_year` is
# EXCLUSIVE here, so a live row ends at or after this.
LIVE_END_YEAR = 2025

# ISO 3166-3 former alpha-3 -> (entity name, the polities that represent it).
#
# Membership only. Every row listed must lie inside the entity's real lifetime; rows of
# the same family that predate or outlive the entity are deliberately absent, which is
# why the F228 prefix contributes three rows and not ten -- SUN is the USSR's code, not
# the Russian Empire's.
ENTITIES = {
    "CSK": ("Czechoslovakia", (
        "F51-1918-1938", "F51-1938-1945", "F51-1945-1947", "F51-1947-1993",
    )),
    "YUG": ("Yugoslavia", (
        "F248-1918-1919", "F248-1919-1920", "F248-1920-1947",
        "F248-1920-1991", "F248-1947-1991", "F248-1991-1992",
    )),
    "DDR": ("German Democratic Republic", (
        "F77-1949-1990",
    )),
    "SUN": ("USSR", (
        # F228-1921-1940 is "RSFSR/USSR": 19 of its 20 years are USSR.
        "F228-1921-1940", "F228-1940-1945", "F228-1945-1991",
    )),
    "ANT": ("Netherlands Antilles", (
        "ANT-1961-2010",
    )),
    "SCG": ("Serbia and Montenegro", (
        "SCG-1992-2006",
    )),
    "PCI": ("Pacific Islands (Trust Territory)", (
        # Also FAOSTAT's code for area 164, which is why it was chosen -- but it IS the
        # 3166-3 former alpha-3 (entry PCHH), and the trusteeship split into four states,
        # so the coincidence lands on the same answer this rule gives.
        "TTPI-1947-1994",
    )),
    "ZAR": ("Zaire", (
        "COD-1885-1891", "COD-1891-1894", "COD-1894-1910",
        "COD-1910-1960", "COD-1960-2025",
    )),
    "BUR": ("Burma", (
        "MMR-1800-1826", "MMR-1826-1852", "MMR-1852-1885", "MMR-1885-2025",
    )),
    "TMP": ("East Timor", (
        "TLS-1800-2025",
    )),
    "RHO": ("Southern Rhodesia", (
        # Southern Rhodesia only. The Federation of Rhodesia and Nyasaland and Northern
        # Rhodesia are different entities and correctly carry FRN, MWI and ZMB.
        "ZWE-1890-1891", "ZWE-1891-1900", "ZWE-1900-1953",
        "SRH-1953-1964", "ZWE-1964-1980", "ZWE-1980-2025",
    )),
    "AFI": ("French Territory of the Afars and the Issas", (
        "FRS-1884-1977", "FRS-1977-2025", "DJI-1886-2025",
    )),
}


def main() -> int:
    if not os.path.exists(POLITIES):
        print(f"FAIL: {POLITIES} not found")
        return 1

    with open(POLITIES, encoding="utf-8") as fh:
        rows = {r["polity_code"]: r for r in csv.DictReader(fh)}

    def iso(code: str) -> str:
        return (rows[code].get("iso3_code") or "").strip()

    def alive(code: str) -> bool:
        r = rows[code]
        if (r.get("wiki_status") or "").strip() in DEAD_STATUS:
            return False
        try:
            return int(r["end_year"]) >= LIVE_END_YEAR
        except (KeyError, TypeError, ValueError):
            return False

    problems: list[str] = []
    carriers: dict[str, list[str]] = {}
    for code, r in rows.items():
        v = (r.get("iso3_code") or "").strip()
        if v:
            carriers.setdefault(v, []).append(code)

    print(f"ISO 3166-3 entities modelled here: {len(ENTITIES)}")

    for former, (name, members) in sorted(ENTITIES.items()):
        missing = [m for m in members if m not in rows]
        if missing:
            problems.append(
                f"{former} ({name}): listed polity(ies) do not exist: {', '.join(missing)}"
            )
            continue

        live = [m for m in members if alive(m)]
        if live:
            expected = {iso(m) for m in live}
            if len(expected) != 1 or not expected.pop():
                problems.append(
                    f"{former} ({name}): continues into live row(s) "
                    f"{', '.join(sorted(live))} but they do not agree on one iso3_code: "
                    + ", ".join(f"{m}={iso(m)!r}" for m in sorted(live))
                )
                continue
            expected = iso(live[0])
            verdict = f"continues -> live code {expected}"
            # The 3166-3 code must be unused: the point of inheriting the modern code is
            # that the entity is ONE family, and a stray former code would re-split it.
            if former in carriers:
                problems.append(
                    f"{former} ({name}): the family continues into a live polity "
                    f"carrying {expected}, so the 3166-3 code must be unused, but "
                    f"{', '.join(sorted(carriers[former]))} carries it"
                )
        else:
            expected = former
            verdict = f"terminates -> own 3166-3 code {former}"

        wrong = [(m, iso(m)) for m in members if iso(m) != expected]
        print(f"  {former} {name[:44]:<46} {len(members):>2} row(s)  {verdict}")
        for m, got in sorted(wrong):
            problems.append(
                f"{former} ({name}): {m} carries iso3_code {got or '(none)'!r}, "
                f"expected {expected!r} -- {verdict}"
            )

    if problems:
        print(f"\nFAIL: {len(problems)} dissolved-state iso3_code problem(s)\n")
        for p in problems:
            print(f"  {p}")
        print(
            "\nThe rule: a dissolved entity whose family CONTINUES into a live polity "
            "carries that live polity's ISO 3166-1 code; one whose family TERMINATES "
            "carries its own ISO 3166-3 former alpha-3. Blank is never right -- a row "
            "with no iso3_code belongs to no ISO family and a consumer holding the code "
            "reaches nothing, which is how issue 55 was found."
        )
        return 1

    print(
        f"\nPASS: all {len(ENTITIES)} ISO 3166-3 entities follow the rule "
        f"(continuing families carry the live code, terminated ones their own)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
