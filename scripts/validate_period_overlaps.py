#!/usr/bin/env python3
"""Check that no two live polities in the same family cover the same year.

A polity code is `PREFIX-start-end`, and the family is the prefix. Within one family the
periods are meant to TILE time, not overlap: a year-aware matcher asked "which polity was
this territory in 1930" must get one answer. When two periods of the same prefix overlap,
the matcher's answer depends on tie-break order rather than on history, so the same label
and year can route to different polities depending on which matcher is asked — and the two
matchers in this repo are already known to disagree in exactly that way.

Found by asking the consumer's crosswalk which area-years resolve to more than one polity,
then checking the whole database rather than only the areas. Four pairs, three families:

  BLX-1850-1999 / BLX-1921-1999   78 years. The known Belgium-Luxembourg overlap
                                  (issue 40). BLX-1850-1999 carries 156,557 observed
                                  rows and BLX-1921-1999 carries none, so the shorter
                                  row is the inert one.
  PER-1825-1884 / PER-1825-1909   59 years, and
  PER-1825-1909 / PER-1884-1909   25 years. Note the shape: PER-1825-1884 and
                                  PER-1884-1909 TILE 1825-1909 exactly, so
                                  PER-1825-1909 is a redundant un-split row that
                                  duplicates both. No aliases and no FAOSTAT mappings
                                  point at any of the three.
  MNE-1913-1915 / MNE-1913-1918   2 years. Two readings of when Montenegro ended —
                                  Austro-Hungarian occupation in 1916 versus joining
                                  Yugoslavia in 1918. Both are defensible, so which one
                                  survives is a historical decision, not a mechanical one.

Baselined bidirectionally rather than asserted to zero: a NEW overlap fails, and a
baselined one that is resolved fails until it leaves the baseline. Dead rows are excluded,
since a retired polity receives no data and cannot make a matcher ambiguous.

SIGNAL B, CROSS-FAMILY, added 2026-08-14 for issue 82.
======================================================

Issue 82's headline is that `MAR-1911-1958` and `MOR-1956-1958` both claimed Moroccan
territory for 1956-1957 and "no gate catches it, because it compares within a prefix by
design". Its option 3 -- extend this gate across families sharing a territory -- was
impossible when the issue was filed, because nothing in the data said which families
share a territory. It is possible now: `data/final/iso3_successor_map.csv` publishes the
link, derived from the predecessor/successor edges, so this gate reads it rather than
guessing from `iso3_code` (the guess the issue was written to stop). 80 family pairs are
linked at hop depth 1; 53 of them have rows that overlap.

WHAT THIS SIGNAL IS AND IS NOT. It is a CHANGE DETECTOR, not a defect list. Two
territory-linked families overlapping in time is usually correct -- a federation and its
member colony are both live and both real -- so all 53 pairs that exist today are
baselined, and what fails is a 54th appearing without review. Measured against the
polygons before the baseline was written, so "none of the 53 is a duplicate" is a
measurement rather than an assumption:

    25 NESTED     one polygon contains the other at >= 0.91 (AOF-1895-1960 contains
                  SEN-1886-1959 at 0.9999; SYL-1944-1953 contains SYR-1946-1967 at
                  1.0000; FRN-1953-1964 contains NRH-1953-1964 at 0.9999)
    25 distinct   IoU <= 0.0001 -- different ground, linked by succession rather than by
                  claiming the same soil (CHN/TWN, KOR/PRK, ERI/ETH, MUS/SYC, BGD/PAK
                  after 1971)
     3 no geometry  RWB-1919-1922/TAN-1891-1920, RWB-1919-1922/TAN-1920-1922 and
                  DEU-1920-1938/SAB-1920-1935. One row of each pair is polygon_status
                  `unassigned`, so there is nothing to measure
     0 DUPLICATE  no pair reaches IoU 0.95, which is the Morocco shape this signal exists
                  for. The Morocco pair itself is gone: MOR-1956-1958 was retired by PR 83.

So it reports zero defects today and would have reported Morocco. That is also why the 53
are baselined in bulk rather than adjudicated one at a time: gating on a mostly-legitimate
set as if it were a defect list trains a reader to ignore it.

WHY IT IS NOT REDUNDANT WITH validate_shared_polygons. That gate asks a GEOMETRIC
question -- do two coexisting rows carry the same ground -- and catches the duplicate
subclass regardless of family. It cannot see a duplicate whose two rows have DIFFERENT
polygons, or no polygon at all: 3 of the 53 pairs here have no geometry to compare, and
the 25 disjoint ones are invisible to it by construction. This signal asks the PERIOD
question about the pairs the database itself says hold one territory.

YEARS COME FROM THE COLUMNS, NOT FROM THE CODE. This gate used to parse the period out of
the `PREFIX-start-end` code. Two rows disagree with their own code and are baselined in
validate_code_year_agreement -- `TAN-1922-1964` really ends 1961 and `NNG-1949-1963`
really ends 1969 -- so the code-derived reading manufactured a 3-year TAN-1922-1964 /
TZA-1961-1964 overlap that the declared periods do not contain, and would equally have
hidden a real one. The code still supplies the FAMILY; the columns supply the period.

Usage:
  python3 scripts/validate_period_overlaps.py
"""
import csv
import json
import os
import re
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLITIES = os.path.join(REPO, "data/final/polities_database.csv")
SUCCESSOR_MAP = os.path.join(REPO, "data/final/iso3_successor_map.csv")
MANIFEST = os.path.join(REPO, "data/final/polities_manifest.json")

DEAD_STATUS = ("retired", "superseded")

# Each entry is the pair of codes, sorted, that may overlap. See the docstring.
BASELINE = frozenset({
    # BLX pair removed 2026-08-05: BLX-1921-1999 is retired (issue 40). This was the
    # LAST same-prefix overlap -- the check now reports 0.
    # Both PER pairs removed 2026-08-05: PER-1825-1909 is superseded by the 1884 split,
    # so neither pair overlaps any more. Issue 62's sibling case.
    # MNE-1913-1915 / MNE-1913-1918 removed 2026-08-05: the 1913-1915 row is retired as
    # a duplicate, so the pair no longer overlaps. Issue 62.
})
# frozenset({...}) rather than a bare {...}: this baseline is now EMPTY, and a bare
# empty literal is a DICT, so `set(observed) - BASELINE` raises TypeError -- the gate
# would crash exactly when the data became correct. validate_spatial_containment
# documents the same trap for the same reason; it bit here on 2026-08-05 when the last
# entry (the BLX pair) was removed.

# SIGNAL B. Every cross-family pair that overlaps today, where the database's own
# succession edges say the two families hold one territory. Bidirectional, like BASELINE
# above: a 54th pair fails, and a baselined pair that stops overlapping fails until its
# line is removed with a note saying what was measured.
#
# All 53 were classified against the polygons before being written down (see the
# docstring): 25 are one polygon inside the other, 25 are different ground, 3 have no
# geometry, and NONE reaches IoU 0.95. This is a starting position, not a defect list.
# The comment on each line is the overlap the two rows declare.
BASELINE_CROSS_FAMILY = frozenset({
    # ("AOF-1895-1960", "SEN-1886-1960") and ("FID-1887-1954", "LAO-1893-1954") were listed
    # here and are REMOVED on 2026-08-14. Not because the overlaps stopped -- AOF and Senegal
    # plainly share 1895-1960 -- but because this signal can only see a pair whose link the
    # PUBLISHED map carries, and iso3_successor_map.csv has no SEN, LAO or CIV rows at all.
    # That is by design, not a defect: the map answers the codes that need a successor
    # mapping, 77 of the 295 live iso3 codes, so a family whose own iso3 is still current
    # never enters it. Keeping the pairs would have pinned an overlap the gate cannot
    # observe, which is the one thing a bidirectional baseline must not contain.
    # French West Africa and its member colonies -- the federation and its parts are both
    # live rows by design, and AOF's polygon contains each of them.
    # The two BFA rows arrive here because PR 232 gave them `predecessor: AOF-1895-1960`
    # (issue 171); the overlap is not new, the territory LINK this check reads is. Upper
    # Volta was carved out of the federation in 1919 and reconstituted inside it in 1947,
    # and AOF ran to 1960 throughout, so both rows genuinely cover both spans.
    ("AOF-1895-1960", "BFA-1919-1932"),                 #  13y 1919-1932
    ("AOF-1895-1960", "BFA-1947-1960"),                 #  13y 1947-1960
    ("AOF-1895-1960", "MRT-1920-1960"),                 #  40y 1920-1960
    ("AOF-1895-1960", "NER-1911-1922"),                 #  11y 1911-1922
    ("AOF-1895-1960", "NER-1922-1947"),                 #  25y 1922-1947
    ("AOF-1895-1960", "NER-1947-1960"),                 #  13y 1947-1960
    # Pakistan and East Pakistan/Bangladesh: one state until 1971, two after, with the
    # BGD polygon inside PAK's for the pre-1971 rows.
    ("BGD-1947-1971", "PAK-1947-1949"),                 #   2y 1947-1949
    ("BGD-1947-1971", "PAK-1949-1971"),                 #  22y 1949-1971
    ("BGD-1971-2025", "PAK-1971-2025"),                 #  54y 1971-2025
    # China against Taiwan and Manchukuo: disjoint ground held concurrently.
    ("CHN-1895-1913", "TWN-1895-1945"),                 #  18y 1895-1913
    ("CHN-1913-1914", "TWN-1895-1945"),                 #   1y 1913-1914
    ("CHN-1914-1921", "TWN-1895-1945"),                 #   7y 1914-1921
    ("CHN-1921-1932", "TWN-1895-1945"),                 #  11y 1921-1932
    ("CHN-1932-1945", "MAN-1932-1945"),                 #  13y 1932-1945
    ("CHN-1932-1945", "TWN-1895-1945"),                 #  13y 1932-1945
    ("CHN-1945-1947", "MAN-1945-1950"),                 #   2y 1945-1947
    ("CHN-1945-1947", "TWN-1945-2025"),                 #   2y 1945-1947
    ("CHN-1947-1949", "MAN-1945-1950"),                 #   2y 1947-1949
    ("CHN-1947-1949", "TWN-1945-2025"),                 #   2y 1947-1949
    ("CHN-1949-1950", "MAN-1945-1950"),                 #   1y 1949-1950
    ("CHN-1949-1950", "TWN-1945-2025"),                 #   1y 1949-1950
    ("CHN-1950-2025", "TWN-1945-2025"),                 #  75y 1950-2025
    # The Saar basin, administered apart from Germany. SAB-1920-1935 has no polygon.
    ("DEU-1920-1938", "SAB-1920-1935"),                 #  15y 1920-1935
    # Eritrea beside Ethiopia, before and after federation. Disjoint polygons.
    ("ERI-1885-1889", "ETH-1800-1889"),                 #   4y 1885-1889
    ("ERI-1889-1952", "ETH-1889-1897"),                 #   8y 1889-1897
    ("ERI-1889-1952", "ETH-1897-1902"),                 #   5y 1897-1902
    ("ERI-1889-1952", "ETH-1902-1907"),                 #   5y 1902-1907
    ("ERI-1889-1952", "ETH-1907-1936"),                 #  29y 1907-1936
    ("ERI-1889-1952", "ETH-1936-1941"),                 #   5y 1936-1941
    ("ERI-1889-1952", "ETH-1941-1952"),                 #  11y 1941-1952
    ("ERI-1993-2025", "ETH-1993-2025"),                 #  32y 1993-2025
    # Macedonia's independence year against the rump Yugoslav aggregate.
    ("F248-1991-1992", "MKD-1991-2025"),                #   1y 1991-1992
    # French Indochina containing Laos; the Rhodesian federation containing Northern
    # Rhodesia; the Pacific trusteeship containing Micronesia and Palau.
    ("FRN-1953-1964", "NRH-1953-1964"),                 #  11y 1953-1964
    ("FSM-1991-2025", "TTPI-1947-1994"),                #   3y 1991-1994
    ("PLW-1991-2025", "TTPI-1947-1994"),                #   3y 1991-1994
    # Precolonial polities against the colonies that absorbed them, over the years the
    # absorption took: Futa Jallon/Guinea, Igala/Northern Nigeria, the Papal States and
    # Italy, Ndebele and Southern Rhodesia, Wadai and Chad.
    ("FTJ-1800-1896", "GIN-1894-1958"),                 #   2y 1894-1896
    ("IGL-1800-1901", "NNI-1899-1904"),                 #   2y 1899-1901
    ("ITA-1861-1866", "PAP-1800-1870"),                 #   5y 1861-1866
    ("ITA-1866-1870", "PAP-1800-1870"),                 #   4y 1866-1870
    ("NDB-1823-1894", "ZWE-1890-1891"),                 #   1y 1890-1891
    ("NDB-1823-1894", "ZWE-1891-1900"),                 #   3y 1891-1894
    ("TCD-1900-1912", "WAD-1800-1912"),                 #  12y 1900-1912
    # Partitions and separations: two states on different ground from the same day.
    ("KOR-1948-2025", "PRK-1948-2025"),                 #  77y 1948-2025
    ("KOS-2008-2025", "SRB-2008-2025"),                 #  17y 2008-2025
    ("MUS-1800-2025", "SYC-1903-2025"),                 # 122y 1903-2025
    ("SMO-1912-1956", "SWA-1912-1958"),                 #  44y 1912-1956
    # New South Wales before the other Australian colonies were carved out of it.
    ("NSW-1800-1900", "QUE-1859-1900"),                 #  41y 1859-1900
    ("NSW-1800-1900", "VIC-1851-1900"),                 #  49y 1851-1900
    # Ruanda-Urundi beside Tanganyika, both out of the same German colony.
    ("RWB-1919-1922", "TAN-1891-1920"),                 #   1y 1919-1920
    ("RWB-1919-1922", "TAN-1920-1922"),                 #   2y 1920-1922
    ("RWB-1922-1962", "TAN-1922-1964"),                 #  39y 1922-1961
    # The Syria-Lebanon mandate aggregate containing Syria.
    ("SYL-1944-1953", "SYR-1922-1945"),                 #   1y 1944-1945
    ("SYL-1944-1953", "SYR-1946-1967"),                 #   7y 1946-1953
})

CODE_RE = re.compile(r"^(.*)-(\d{4})-(\d{4})$")


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


def territory_family_pairs() -> set:
    """Unordered family pairs the database says hold ONE territory.

    Read, not guessed. `iso3_code` cannot answer this -- that is issue 82's whole point --
    but the predecessor/successor edges can, and `write_iso3_successor_map.py` has already
    walked them into `data/final/iso3_successor_map.csv`. Hop depth 1 only: depth 1 is an
    edge the database ASSERTS, depth 2+ is a traversal inference, and inferring a
    territorial identity three hops away would put pairs in this gate that no page claims.

    The manifest is preferred when it carries `territory_families`, because that is the
    PUBLISHED form of the same fact and a check should read the contract a consumer reads.
    Both derivations were compared and produce the same 80 family pairs.
    """
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as fh:
            published = (json.load(fh) or {}).get("territory_families")
        if published:
            return {
                tuple(sorted((modern, holder["family"])))
                for modern, holders in published.items()
                for holder in holders
                if holder.get("family") and holder["family"] != modern
            }

    if not os.path.exists(SUCCESSOR_MAP):
        return set()
    pairs = set()
    with open(SUCCESSOR_MAP, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                if int(r["hop_depth"]) != 1:
                    continue
            except (KeyError, TypeError, ValueError):
                continue
            family = (r.get("polity_code") or "").rsplit("-", 2)[0]
            modern = (r.get("modern_iso3") or "").strip()
            if family and modern and family != modern:
                pairs.add(tuple(sorted((modern, family))))
    return pairs


def overlaps(items_a: list, items_b: list) -> dict:
    """Every overlapping (code, code) pair across two lists of (start, end, code).

    `end_year` is EXCLUSIVE, so a row ending where another begins does not overlap; the
    `hi > lo` rather than `hi >= lo` is that rule and nothing else.
    """
    found = {}
    for a in items_a:
        for b in items_b:
            if a[2] == b[2]:
                continue
            lo, hi = max(a[0], b[0]), min(a[1], b[1])
            if hi > lo:
                found[tuple(sorted((a[2], b[2])))] = (lo, hi, hi - lo)
    return found


def report(title, observed, baseline, mapped, problems, new_msg) -> None:
    print(f"\n{title}: {len(observed)}")
    for pair, (lo, hi, n) in sorted(observed.items(), key=lambda kv: -kv[1][2]):
        reach = sum(1 for c in pair if c in mapped)
        tag = {0: "latent (neither mapped)", 1: "latent (one mapped)",
               2: "LIVE (both mapped)"}[reach]
        flag = "" if pair in baseline else "   <-- NOT BASELINED"
        print(
            f"   {n:>4}y  {pair[0]:<20} overlaps {pair[1]:<20} ({lo}-{hi})  {tag}{flag}"
        )
    for pair in sorted(set(observed) - baseline):
        lo, hi, n = observed[pair]
        problems.append(
            f"{new_msg}: {pair[0]} and {pair[1]} both cover {lo}-{hi} ({n} years)"
        )
    for pair in sorted(baseline - set(observed)):
        problems.append(
            f"{pair[0]} and {pair[1]} are baselined as overlapping but no longer do — "
            f"remove the pair from the baseline, with a note saying what was measured"
        )


def main() -> int:
    families = defaultdict(list)
    live = 0
    for r in csv.DictReader(open(POLITIES, encoding="utf-8")):
        if (r.get("wiki_status") or "").strip() in DEAD_STATUS:
            continue
        live += 1
        m = CODE_RE.match(r["polity_code"])
        if not m:
            # build_database.py gates the code shape, so this should be unreachable.
            continue
        # The period comes from the COLUMNS, not from the code's embedded years: two rows
        # disagree with their own code (validate_code_year_agreement baselines both), and
        # reading the code manufactured a TAN-1922-1964 / TZA-1961-1964 overlap that the
        # declared periods do not contain.
        try:
            start, end = int(r["start_year"]), int(r["end_year"])
        except (TypeError, ValueError, KeyError):
            continue
        families[m.group(1)].append((start, end, r["polity_code"]))

    problems = []
    mapped = faostat_mapped()
    print(f"live polities: {live}")
    print(f"exact-prefix families: {len(families)}")

    same = {}
    for items in families.values():
        items.sort()
        same.update(overlaps(items, items))
    report(
        "overlapping same-family pairs", same, BASELINE, mapped, problems,
        "NEW same-family overlap — a year-aware matcher cannot choose between them on "
        "history alone",
    )

    linked = territory_family_pairs()
    if not linked:
        # A signal that silently checks nothing is worse than no signal: without the
        # successor map this reports zero pairs and would read as "no cross-family
        # overlaps" rather than "not measured".
        problems.append(
            "no territory link is available, so the cross-family signal checked NOTHING "
            "— regenerate data/final/iso3_successor_map.csv with "
            "scripts/write_iso3_successor_map.py"
        )
    print(f"\nterritory-linked family pairs: {len(linked)}")
    cross = {}
    for fa, fb in linked:
        cross.update(overlaps(families.get(fa, []), families.get(fb, [])))
    report(
        "overlapping cross-family pairs sharing a territory", cross,
        BASELINE_CROSS_FAMILY, mapped, problems,
        "NEW cross-family overlap — two families the database says hold one territory "
        "both claim these years, the shape issue 82 reported for Morocco",
    )

    if problems:
        print(f"\nFAIL: {len(problems)} change(s) against the baseline\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print(
        "\nPASS: same-family and cross-family period overlaps match the baselines exactly"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
