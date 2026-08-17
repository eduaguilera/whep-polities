#!/usr/bin/env python3
"""Check this repo's matchers against each other, and pin the decisions they encode.

There are three independent implementations of "which polity does this source's
label mean in this year":

  pipelines/faostat-era-matching/match.R   scans the FAOSTAT pins and emits
                                           year-ranged routing aliases
  pipelines/polity-autoimprove/matchlib.py resolves labels by alias, then by
                                           ISO/name family + year containment
  pipelines/pre1961-matching/match.R       the same resolution for the pre-1961
                                           panel, in a third dialect

`matchlib.pick_by_year` carries a comment saying it was written to agree with
match.R on the shared-transition-year rule, so agreement is the intent. Nothing
verified it. Comparing them found three real defects on the first run:

  Serbia 2006-2008 exists TWICE, as SER-2006-2008 and SRB-2006-2008 (issue 43)
  "Malaysia" 1961 resolves to British North Borneo, because four same-iso3
    candidates are all typed `national` so the tie-break cannot discriminate
    (issue 44)
  "Viet Nam" 1967 routes to RVN (South Vietnam alone) by one alias and to
    F237 (combined DRV+RVN) by the other

The comparison must avoid circularity: matchlib READS the aliases match.R writes,
so asking it about a FAOSTAT label would just return match.R's own answer. This
loads matchlib with the `faostat`-sourced rules REMOVED, forcing it to resolve by
its own deterministic routes, and compares that against the published map.

Disagreements are baselined rather than asserted to zero — the three above are
real and open. A NEW one fails, and a baselined one that starts agreeing fails
too, so the list shrinks as the defects are fixed.

EVERY MAPPING IS PROBED AT ITS BOUNDARY YEARS, not only at its midpoint (issue 16).
Until 2026-08-17 this compared the two matchers at `(y0 + y1) // 2` alone, and that
single choice made the gate blind to the one rule every recorded divergence has
turned on: which polity owns a SHARED TRANSITION YEAR. A midpoint is by
construction the year furthest from both edges, so the comparison could not
see the edges at all — selftest_gates said as much in prose, in the docstring
of `mutate_inclusive_end_year`. Probing {y0, midpoint, y1} raised 297 probes to
874 and took the disagreement count from 1 to 9, six of them at areas the
midpoint reading called clean (4, 17, 105, 181, 206, 272).

A GOLDEN FIXTURE (`FIXTURE` below) pins the hard-won routing decisions the issue
listed — Malaysia 1961-63, combined Yemen F249 and Vietnam F237, the Réunion and
French Guiana prefix routes, the Gold Coast composite label, the shared boundary
years HUN/DEU/F51 1938 and IND/PAK 1949, and two dead-polity targets. Each was
decided once, in an issue, and nothing tested it afterwards. The fixture asserts
matchlib's answer exactly; it is not baselined, because each entry is a decision
on the record and a change to it must be argued, not absorbed.

And `check_dead_status_declared` asserts, by source text, that ALL THREE matchers
name both dead statuses. That is the invariant issue 16 found missing from
`pre1961-matching/match.R` entirely — see DEAD_STATUS_DECLARERS below.

THE THIRD MATCHER IS NOW COMPARED BY BEHAVIOUR, not only by source text (issue 16).
Until 2026-08-17 this gate compared TWO of the three implementations and checked the
third, `pipelines/pre1961-matching/match.R`, only by grepping it for two status words.
That was not a choice about what mattered; it was the reachable check. The R matcher
needs an R toolchain CI does not have, its input `data/external/before_1961.csv` is 18 MB
and its output `data/compiled/pre1961/matched.csv` is 19 MB AND GITIGNORED —
`validate_matcher_orphan_guard.py` states the consequence outright: "no gate can ever
read them".

What CI can read is a small COMMITTED table of the R matcher's decisions, which is what
`pipelines/pre1961-matching/write_r_crosswalk.py` now publishes. The R answers are
piecewise constant in the year, so its 124,508-row match collapses to 487 runs over 150
reporting entities, and a run boundary IS a year where the R matcher changes its mind —
i.e. exactly a transition year. Probing {y0, midpoint, y1} of each run gives 1,154 probes
and found 21 disagreements plus 34 probes matchlib cannot resolve at all, in four
mechanisms none of which the source-text check could see:

  * TRANSITION-YEAR ATTRIBUTION, the rule the issue predicted, now measured on the third
    matcher: Greece 1913, Russia 1905, Korea 1948, Israel/Palestine 1948 all go to the
    SUCCESSOR in match.R and to the PREDECESSOR in matchlib, while Sudan 1956 and
    Manchuria 1945 go the other way round. So neither implementation is uniform, and the
    convention `matchlib.pick_by_year`'s comment claims to share is not in fact shared.
  * AN ERA-REWRITE TABLE ONLY R HAS. `normalise_iso` hard-codes 26 (iso3, year-cutoff)
    rewrites, so match.R sends Malawi and Zambia 1953-63 to FRN (the Federation of
    Rhodesia & Nyasaland) and Rwanda pre-1962 to RWB (Ruanda-Urundi), where matchlib
    answers the modern successor. These are territory-scope decisions, not typos:
    FRN is ~1.26M km2 against Nyasaland's ~118k.
  * A NAME-OVERRIDE TABLE ONLY R HAS. 13 labels whose iso3c is literally "NA" —
    "Korea", "Cape Natal", "Indochina", "China, Manchuria Province of" — route by name in
    R and resolve to nothing in matchlib.
  * FAMILY TIE-BREAKS: Libya 1943-49 (LBY against CYR, Cyrenaica) and Ethiopia 1936-41
    (ETH against AOI, Italian East Africa) differ with no alias and no rewrite involved.

There is no circularity to guard against on this arm, unlike the FAOSTAT one: match.R
(pre1961) writes only into `data/compiled/`, which matchlib never reads, so the full
alias registry is used here.

Usage:
  python3 scripts/crosscheck_matchers.py

  # regenerating the R side (needs R + data/external, so NOT runnable in CI):
  Rscript pipelines/pre1961-matching/match.R
  python3 pipelines/pre1961-matching/write_r_crosswalk.py
"""
import csv
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "pipelines/polity-autoimprove"))

ALIASES = os.path.join(REPO, "pipelines/polity-autoimprove/state/applied_aliases.csv")
POLITIES = os.path.join(REPO, "data/final/polities_database.csv")
PUBLISHED = os.path.join(REPO, "data/final/faostat_area_polity_map.csv")
PRE1961 = os.path.join(REPO, "pipelines/pre1961-matching/state/r_crosswalk.csv")

# Known disagreements, by FAOSTAT area code. Each is an open defect, not an
# accepted difference — see the issues named above.
# 272 removed 2026-08-05: retiring the duplicate SER-2006-2008 (issue 43, PR 86) left
# one Serbia row for 2006-2007, so match.R and matchlib now agree on area 272. The
# disagreement was a SYMPTOM of the duplicate, not an independent matcher bug.
# 131 removed 2026-08-05 (issue 44): eight polities carried iso3_code MYS and ALL EIGHT
# were typed `national`, so pick_by_year's national preference discriminated nothing and
# family ORDER decided. "Malaysia" 1961 resolved to BNB-1881-1963 (British North Borneo,
# 72,557 km2). Retyping BNB and BSW to `colonial` and MASG to `aggregate` -- all three
# accurate -- let the preference work, and the two matchers now agree.
#
# Keyed by (area_code, probe_year) since 2026-08-17, because the probe set now includes
# both boundary years. An area is no longer clean or dirty as a whole: area 4 agrees at
# 1961 and 1998 and disagrees at 1962 only, and collapsing that to "area 4" would hide
# which year is at stake. The six areas the midpoint reading never asked about:
#
#   (4, 1962)  (105, 1967)  (181, 1964)  (272, 2008)  -- ONE mechanism, four times.
#       An UNSOURCED alias ('algeria' 1919-1962, 'israel' 1948-1967, 'zimbabwe'
#       1953-1964, 'serbia' 2006-2008) carries an INCLUSIVE year_end equal to its
#       target's EXCLUSIVE end_year, so it claims one year past its target's own
#       coverage -- exactly the transition year the successor owns. matchlib's
#       narrower-range preference then hands that year to the predecessor, while the
#       published map hands it to the successor. NOT fixed here: validate_aliases.py
#       measures 198 aliases sitting at that same parity and its comment calls the
#       parity the convention, so clipping four of them is either an inconsistency or
#       the first four of a registry-wide change. Deciding which is a separate issue.
#   (17, 1968)  -- ALREADY RECORDED BY A SECOND GATE, which is the strongest evidence the
#       diagnosis is right: validate_year_semantics.py baselines ("BMU-1684-1968", 1968)
#       as "type guard: successor is `territory`". No alias involved; matchlib reaches it
#       by the `iso` route. Bermuda's
#       two rows are typed UNEQUALLY: BMU-1684-1968 `national`, successor BMU-1968-2025
#       `territory`. pick_by_year only drops an expired predecessor when the row
#       STARTING at the year is no worse a type, so `territory` cannot displace
#       `national` and the ended predecessor wins its own boundary year. Same family of
#       defect as issue 44's Malaysia case, in mirror image: there all eight candidates
#       shared one type so the preference discriminated nothing, here the types differ
#       and the preference discriminates the wrong way. Bermuda was a British
#       colony/overseas territory for the whole span, so one of the two types is wrong;
#       which one is a data question this gate should not answer by itself.
#   (206, 2011)  -- the only one where the PUBLISHED MAP is the party out of step. It
#       gives "Sudan (former)" year_end 2011 (inclusive) while SUD-1956-2011 ends 2011
#       (exclusive), so the map claims a year its own target excludes; matchlib answers
#       SDN-2011-2025. This is NOT an off-by-one to be clipped: South Sudan seceded in
#       July 2011 and FAOSTAT does report 2011 under area 206, so whether the 2011 rows
#       describe the former unified Sudan or the rump state is a real attribution
#       question with data on both sides.
#
# (237, *) is the pre-existing Viet Nam disagreement, unchanged in substance: two
# aliases route the label differently (F237, combined DRV+RVN, against RVN alone). It
# appears three times now only because all three probe years fall inside one mapping.
BASELINE_DIFFERENT = frozenset({
    (4, 1962),
    (17, 1968),
    (105, 1967),
    (181, 1964),
    (206, 2011),
    (237, 1961),
    (237, 1967),
    (237, 1974),
    (272, 2008),
})

# Golden fixture: (source_label, iso3, source, year) -> the polity code matchlib must
# return, using the FULL alias registry (the crosscheck body below strips the faostat
# rules to avoid circularity; the fixture does not, because several of these routes ARE
# faostat/fao1952 aliases and stripping them would test nothing).
#
# Every entry is a decision made in an issue and previously protected by nothing:
#   Malaysia 1961-63    issue 44: all eight MYS candidates were typed `national`, family
#                       ORDER decided, and "Malaysia" 1961 resolved to British North
#                       Borneo (72,557 km2). 1963 must step to MYS-1963-1965.
#   Yemen 1989/1990     F249 is the combined pre-unification reporting unit; 1990 is the
#                       transition year and belongs to the successor.
#   Viet Nam 1974/1975  F237 combines DRV and RVN to 1974 inclusive; 1975 is unified VNM.
#   Réunion, Fr. Guiana prefix routes for rows whose polity_code carries iso3_code=NA, so
#                       an ISO match alone misses them.
#   Gold Coast          composite colonial label, resolvable only with its source.
#   HUN/DEU/F51 1938    shared transition years: 1938 goes to the SUCCESSOR in all three.
#   IND/PAK 1949        the same rule at a partition boundary.
#   Argentina, Brazil   dead-target guards. ARG-1800-2025 (retired) and BRA-1800-2025
#                       (superseded) both span 1800-2025 as `national`, so they outrank
#                       every live successor in any family that still contains them.
#                       Measured: emptying matchlib's DEAD_STATUS makes the Argentina entry
#                       answer ARG-1800-2025 outright. The Brazil entry still answers
#                       BRA-1800-1903, so it is a weaker guard than it looks and is kept
#                       for the second status word rather than for its sensitivity. This is
#                       the invariant issue 16 found the R side missing entirely.
FIXTURE = (
    ("Malaysia", "MYS", "faostat", 1961, "MYS-1957-1963"),
    ("Malaysia", "MYS", "faostat", 1962, "MYS-1957-1963"),
    ("Malaysia", "MYS", "faostat", 1963, "MYS-1963-1965"),
    ("Yemen", "YEM", "faostat", 1989, "F249-1918-1990"),
    ("Yemen", "YEM", "faostat", 1990, "YEM-1990-2025"),
    ("Viet Nam", "VNM", "faostat", 1974, "F237-1954-1975"),
    ("Viet Nam", "VNM", "faostat", 1975, "VNM-1975-2025"),
    ("Reunion", None, "faostat", 1961, "REU-1946-2025"),
    ("French Guiana", None, "faostat", 1961, "GUF-1946-2025"),
    ("Gold Coast", None, "fao1952", 1948, "GHA-1898-1957"),
    ("Hungary", "HUN", None, 1937, "HUN-1920-1938"),
    ("Hungary", "HUN", None, 1938, "HUN-1938-1940"),
    ("Germany", "DEU", None, 1938, "DEU-1938-1945"),
    ("Czechoslovakia", "CSK", None, 1938, "F51-1938-1945"),
    ("India", "IND", None, 1948, "IND-1947-1949"),
    ("India", "IND", None, 1949, "IND-1949-2025"),
    ("Pakistan", "PAK", None, 1949, "PAK-1949-1971"),
    ("Argentina", "ARG", None, 1900, "ARG-1899-1902"),
    ("Brazil", "BRA", None, 1900, "BRA-1800-1903"),
)

# Labels matchlib cannot resolve without the faostat alias, so an explicit route is
# REQUIRED. One area, and it is genuinely nominal: the Yugoslav SFR chain sits under
# F248-*, a combined-reporting prefix, and the label "Yugoslav SFR" with iso3 YUG leads
# nowhere at all — status `unresolved`, not `year_uncovered`.
#
# This set used to be {7, 72, 248}, and the two that left are worth recording because the
# stated reason for all three was wrong. The comment claimed each was "a prefix the label
# does not lead to". For Angola and Djibouti the obstacle was TEMPORAL: both areas have two
# published mappings, the modern one resolved fine, and the COLONIAL row returned
# `year_uncovered` because the ISO code attached only to the post-independence polity.
# Correcting three `iso3` fields to name the TERRITORY rather than the era —
# ANG-1905-1975 to AGO, FRS-1884-1977 and FRS-1977-2025 to DJI, SUD-1956-2011 to SDN —
# made both colonial rows resolve, and this baseline's bidirectional arm is what reported
# it. The prefixes were never the problem and are unchanged.
#
# I also first guessed this set would be the four China components, assuming an aggregate
# with no ISO3 would be the hard case. Those resolve fine.
# 248 removed 2026-08-05 (issue 55): giving the Yugoslav rows their ISO 3166-3 code YUG put
# them in an ISO family for the first time, so matchlib can now resolve FAOSTAT area 248 by
# the ISO route. Before, those rows carried no iso3 at all and were reachable only by an
# explicit alias. This is the concrete gain from that change, reported by an independent gate.
BASELINE_UNRESOLVED = frozenset()

# --- the THIRD matcher: pipelines/pre1961-matching/match.R ---------------------------
# Keyed by (label, iso3 or "-", probe year), measured 2026-08-17 against the committed
# crosswalk (487 runs, 1,154 probes, 1,099 agreements). Every entry is an OPEN divergence
# with a named mechanism, not an accepted difference. Grouped by mechanism:
#
# 1. TRANSITION-YEAR ATTRIBUTION — the rule issue 16 predicted every divergence would turn
#    on, confirmed on the third matcher. At a year shared by a predecessor and its
#    successor the two implementations pick opposite sides, and NEITHER is consistent:
#      Greece 1913, Russia 1905, Korea 1948, Israel/Palestine 1948  R -> successor
#      Sudan 1956, Manchuria 1945                                   R -> predecessor
#    match.R reaches its answer via `covers()` + `drop_expired_periods`, matchlib via
#    `pick_by_year`'s narrower-range preference or an alias whose INCLUSIVE `year_end`
#    equals its target's EXCLUSIVE `end_year` — the same alias parity the FAOSTAT arm
#    baselines four times above, and the same registry-wide decision is pending there.
#    Not fixed here: choosing the convention changes both matchers' output on real data.
# 2. AN ERA-REWRITE TABLE ONLY match.R HAS (`normalise_iso`, 26 hard-coded rules).
#    Malawi/Zambia 1953-63 -> FRN (Federation of Rhodesia & Nyasaland, ~1.26M km2) and
#    Rwanda pre-1962 -> RWB (Ruanda-Urundi) in R; matchlib answers the modern successor
#    (MWI/NRH/RWA rows of the same span). This is a TERRITORY-SCOPE disagreement, the
#    largest in magnitude here, and porting the table into matchlib would move layer-B
#    routing for three countries — argued, not absorbed.
# 3. FAMILY TIE-BREAKS with no alias and no rewrite: Libya 1943-49 (R LBY-1943-1949 vs
#    matchlib CYR-1943-1949, Cyrenaica alone) and Ethiopia 1936-41 (R ETH-1936-1941 vs
#    matchlib AOI-1936-1941, Italian East Africa). Both are real attribution questions
#    about occupied/partitioned territory, which a matcher gate must not settle by itself.
BASELINE_PRE1961_DIFFERENT = frozenset({
    ("China, Manchuria Province of", "-", 1945),   # R MAN-1932-1945 / CHN-1945-1947
    ("Ethiopia", "ETH", 1936),                     # R ETH-1936-1941 / AOI-1936-1941
    ("Ethiopia", "ETH", 1938),
    ("Ethiopia", "ETH", 1940),
    ("Greece", "GRC", 1913),                       # R GRC-1913-1919 / GRC-1881-1913
    ("Israel/Palestine", "-", 1948),               # R ISR-1948-1967 / PAL-1920-1948
    ("Korea", "-", 1948),                          # R KOR-1948-2025 / KOR-1945-1948
    ("Libya", "LBY", 1945),                        # R LBY-1943-1949 / CYR-1943-1949
    ("Libya", "LBY", 1947),
    ("Libya", "LBY", 1949),
    ("Malawi", "MWI", 1953),                       # R FRN-1953-1964 / MWI-1953-1964
    ("Malawi", "MWI", 1956),
    ("Malawi", "MWI", 1960),
    ("Russian Federation", "RUS", 1905),           # R F228-1905-1914 / F228-1856-1905
    ("Rwanda", "RWA", 1952),                       # R RWB-1922-1962 / RWA-1922-1962
    ("Rwanda", "RWA", 1956),
    ("Rwanda", "RWA", 1960),
    ("Sudan", "SDN", 1956),                        # R SUD-1934-1956 / SUD-1956-2011
    ("Zambia", "ZMB", 1953),                       # R FRN-1953-1964 / NRH-1953-1964
    ("Zambia", "ZMB", 1956),
    ("Zambia", "ZMB", 1960),
})

# Entities match.R routes and matchlib cannot resolve AT ALL. Keyed by (label, iso3) and
# NOT by year, deliberately: the mechanism is entity-level — matchlib has no equivalent of
# match.R's `name_override` table (13 labels whose input iso3c is literally the string
# "NA": Korea, Cape Natal, Indochina, Manchuria, Rwanda and Burundi, Cape Province...) and
# no equivalent of the pre-independence arm of `normalise_iso` (SOM pre-1960 -> ITS,
# CSK pre-1918 -> AUH, YUG pre-1918 -> SER, PSE -> PAL, LBY pre-1912 -> OTT, PRK pre-1948
# -> KOR). The year a probe happens to land on is an artefact of which years the panel
# carries, so year-keying these would churn on every regeneration without adding signal.
# Cost of that choice, stated: a NEW unresolved year at an entity already listed here does
# not fail. "Korea" shows why the entities and not the years are the unit — it resolves by
# name at 1948 (see the DIFFERENT baseline) and not at 1954 or 1960.
# 34 probes across these 8 entities as of 2026-08-17.
BASELINE_PRE1961_UNRESOLVED = frozenset({
    ("Cape Natal", "-"),            # name_override -> NAT, then ZAF after Union (1910)
    ("Czechoslovakia", "CSK"),      # pre-1918 -> AUH (Austria-Hungary)
    ("Korea", "-"),                 # name_override -> KOR
    ("Libya", "LBY"),               # pre-1912 -> OTT (Ottoman Empire)
    ("North Korea", "PRK"),         # pre-1948 -> KOR (undivided Korea)
    ("Palestine", "PSE"),           # -> PAL (British Mandate)
    ("Somalia", "SOM"),             # pre-1960 -> ITS (Italian Somaliland)
    ("Yugoslav SFR", "YUG"),        # pre-1918 -> SER (Kingdom of Serbia)
})


# Every program in this repo that decides which polity a label and year belong to. All
# three must exclude dead polities, and until 2026-08-17 one of them did not: issue 16
# found `pre1961-matching/match.R` filtering on years alone, and it routed 15,526 of its
# 124,508 rows to 24 `retired`/`superseded` polities — ARG-1800-2025 took 3,356 of them.
# A collapsed dead row typically spans ALL years as `national`, so it does not merely
# appear as a candidate, it OUTRANKS the live successors it was split into.
#
# Checked by source text rather than by behaviour because two of the three are R and this
# gate is Python. That is a weaker check than running them, and it is the check that would
# have caught the actual defect: the rule was absent from the file entirely, not subtly
# wrong. Both status words must appear, so deleting either half fails.
DEAD_STATUS_DECLARERS = (
    "pipelines/polity-autoimprove/matchlib.py",
    "pipelines/pre1961-matching/match.R",
    "pipelines/faostat-era-matching/match.R",
)


def check_dead_status_declared() -> list:
    """Each matcher must name both dead statuses, so none can route data to a dead row."""
    problems = []
    for rel in DEAD_STATUS_DECLARERS:
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            problems.append(
                f"{rel} is missing, so this gate cannot tell whether it excludes "
                f"retired/superseded polities"
            )
            continue
        text = open(path, encoding="utf-8").read()
        absent = [s for s in ("retired", "superseded") if f'"{s}"' not in text]
        if absent:
            problems.append(
                f"{rel} never names {' or '.join(absent)}, so it can route data to a "
                f"polity the database has withdrawn — the defect issue 16 measured at "
                f"15,526 rows on 24 dead polities in pre1961-matching/match.R"
            )
    return problems


def dead_codes() -> set:
    """polity_codes whose wiki_status forbids them from receiving data."""
    return {
        r["polity_code"]
        for r in csv.DictReader(open(POLITIES, encoding="utf-8"))
        if (r.get("wiki_status") or "").strip() in ("retired", "superseded")
    }


def all_codes() -> set:
    """every polity_code the database carries, dead ones included."""
    return {
        r["polity_code"] for r in csv.DictReader(open(POLITIES, encoding="utf-8"))
    }


def check_pre1961(full, dead: set, live: set) -> tuple:
    """Compare matchlib against the THIRD matcher, `pre1961-matching/match.R`.

    The R matcher cannot run in CI, so its decisions are read from the crosswalk
    `write_r_crosswalk.py` publishes from its output. Each row is a run of consecutive
    years over which R's answer is constant, so a run boundary is a year where R changes
    its mind: probing {y0, midpoint, y1} puts two of every three probes ON a transition.

    Returns (probes, agree, different, unresolved, problems).
    """
    problems = []
    if not os.path.exists(PRE1961):
        return 0, 0, {}, {}, [
            f"{os.path.relpath(PRE1961, REPO)} is missing, so the third matcher "
            f"(pre1961-matching/match.R) is compared by source text only — regenerate it "
            f"with: Rscript pipelines/pre1961-matching/match.R && python3 "
            f"pipelines/pre1961-matching/write_r_crosswalk.py"
        ]

    runs = list(csv.DictReader(open(PRE1961, encoding="utf-8")))
    agree, probes, different, unresolved = 0, 0, {}, {}
    for r in runs:
        rcode = r["polity_code"]
        # Freshness and the two invariants the R matcher claims for its own output. An
        # orphan means the database moved under the crosswalk (issue 17); a dead target
        # means the retired/superseded filter did not hold on real data, which is the
        # BEHAVIOURAL form of what DEAD_STATUS_DECLARERS can only check as source text.
        if rcode not in live:
            problems.append(
                f"pre1961 crosswalk routes {r['country']!r} {r['year_start']}-"
                f"{r['year_end']} to {rcode}, which is not in the database — the R "
                f"matcher's crosswalk is stale, regenerate it"
            )
            continue
        if rcode in dead:
            problems.append(
                f"pre1961 crosswalk routes {r['country']!r} {r['year_start']}-"
                f"{r['year_end']} to {rcode}, whose wiki_status is dead — a dead polity "
                f"must never receive data"
            )
            continue
        y0, y1 = int(r["year_start"]), int(r["year_end"])
        # match.R resolves on iso3c first and falls back to polity_name, then country
        # (`resolve_iso`). "NA" is a literal string in this panel, not a missing value.
        label = r["polity_name"] if r["polity_name"] not in ("", "NA") else r["country"]
        iso = r["iso3c"] if r["iso3c"] not in ("", "NA") else None
        for year in sorted({y0, (y0 + y1) // 2, y1}):
            probes += 1
            code, _status, how = full.assign(label, iso, None, year)
            if code == rcode:
                agree += 1
            elif code is None:
                unresolved[(label, iso or "-")] = (rcode, how)
            else:
                different[(label, iso or "-", year)] = (rcode, code, how)
    return probes, agree, different, unresolved, problems


def main() -> int:
    import matchlib

    rows = list(csv.DictReader(open(ALIASES, encoding="utf-8")))
    cols = list(rows[0].keys())
    tmp = tempfile.NamedTemporaryFile(
        "w", suffix=".csv", delete=False, newline="", encoding="utf-8"
    )
    w = csv.DictWriter(tmp, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        if r.get("source") != "faostat":
            w.writerow({c: r.get(c, "") for c in cols})
    tmp.close()

    dead = dead_codes()
    try:
        m = matchlib.Matcher(POLITIES, applied_aliases_csv=tmp.name, verbose=False)
        full = matchlib.Matcher(POLITIES, applied_aliases_csv=ALIASES, verbose=False)
        published = list(csv.DictReader(open(PUBLISHED, encoding="utf-8")))

        agree, probes, different, unresolved = 0, 0, {}, {}
        for r in published:
            area = int(float(r["area_code"]))
            y0, y1 = int(r["year_start"]), int(r["year_end"])
            # {first, midpoint, last}. The boundary years are the whole point: the
            # shared-transition-year rule only ever shows itself at y0 or y1, and a
            # midpoint is the year furthest from both.
            for year in sorted({y0, (y0 + y1) // 2, y1}):
                key = (area, year)
                probes += 1
                code, _status, how = m.assign(
                    r["source_label"], r["iso3"] or None, "faostat", year
                )
                if code == r["polity_code"]:
                    agree += 1
                elif code is None:
                    unresolved[key] = (r["source_label"], r["polity_code"], how)
                else:
                    different[key] = (r["source_label"], r["polity_code"], code, how)

        fixture_failures = []
        for label, iso3, source, year, expect in FIXTURE:
            code, _status, how = full.assign(label, iso3, source, year)
            if code != expect:
                fixture_failures.append(
                    f"fixture {label!r} [{source or 'no source'}] {year}: expected "
                    f"{expect}, matchlib returned {code} ({how})"
                )
            elif code in dead:
                fixture_failures.append(
                    f"fixture {label!r} [{source or 'no source'}] {year} resolves to "
                    f"{code}, whose wiki_status is dead — a dead polity must never "
                    f"receive data"
                )

        (p_probes, p_agree, p_different, p_unresolved,
         p_problems) = check_pre1961(full, dead, all_codes())
    finally:
        os.unlink(tmp.name)

    problems = list(fixture_failures) + check_dead_status_declared() + p_problems
    for label, observed, baseline in (
        ("disagreement", set(different), BASELINE_DIFFERENT),
        ("unresolved", set(unresolved), BASELINE_UNRESOLVED),
    ):
        for area, year in sorted(observed - baseline):
            problems.append(f"NEW {label} at area {area}, year {year}")
        for area, year in sorted(baseline - observed):
            problems.append(
                f"area {area} year {year} is baselined as a {label} but now agrees — "
                f"remove it from the baseline"
            )

    for label, observed, baseline in (
        ("disagreement", set(p_different), BASELINE_PRE1961_DIFFERENT),
        ("unresolved", set(p_unresolved), BASELINE_PRE1961_UNRESOLVED),
    ):
        for key in sorted(observed - baseline):
            detail = (p_different if len(key) == 3 else p_unresolved)[key]
            problems.append(
                f"NEW pre1961 {label} at {key[0]!r} [iso {key[1]}]"
                + (f" year {key[2]}" if len(key) == 3 else "")
                + f": match.R says {detail[0]}, matchlib says "
                + (f"{detail[1]} ({detail[2]})" if len(key) == 3
                   else f"nothing ({detail[1]})")
            )
        for key in sorted(baseline - observed):
            problems.append(
                f"pre1961 {key} is baselined as a {label} against "
                f"pre1961-matching/match.R but now agrees — remove it from the baseline"
            )

    print(f"published FAOSTAT mappings: {len(published)}")
    print(f"  probes (first/mid/last year): {probes}")
    print(f"  the two matchers agree      : {agree}")
    print(f"  different target            : {len(different)}")
    print(f"  matchlib cannot resolve     : {len(unresolved)}")
    print(f"  golden fixture cases        : {len(FIXTURE)}, "
          f"{len(fixture_failures)} failing")
    print(f"  matchers excluding dead rows: "
          f"{len(DEAD_STATUS_DECLARERS) - len(check_dead_status_declared())}"
          f"/{len(DEAD_STATUS_DECLARERS)}")
    if different:
        print("\n  different target:")
        for (area, year), (lbl, a, b, how) in sorted(different.items()):
            print(
                f"    area {area:>4} y={year} {lbl[:24]:<26} match.R={a:<16} "
                f"matchlib={b:<16} ({how})"
            )

    print(f"\npre-1961 crosswalk (pipelines/pre1961-matching/match.R): "
          f"{p_probes} probes")
    print(f"  matchlib agrees             : {p_agree}")
    print(f"  different target            : {len(p_different)}")
    print(f"  matchlib cannot resolve     : {len(p_unresolved)} entit(ies)")
    if p_different:
        print("\n  different target:")
        for (lbl, iso, year), (a, b, how) in sorted(p_different.items()):
            print(
                f"    {lbl[:28]:<30} [{iso:<3}] y={year} match.R={a:<16} "
                f"matchlib={b:<16} ({how})"
            )

    if problems:
        print(f"\nFAIL: {len(problems)} change(s) against the baseline\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: agreement matches the baseline exactly, fixture intact")
    return 0


if __name__ == "__main__":
    sys.exit(main())
