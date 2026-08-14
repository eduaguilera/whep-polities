#!/usr/bin/env python3
"""Find years where a label's route is decided by FAMILY ORDER rather than by anything real.

`matchlib.pick_by_year` resolves a label to an ISO family, then prefers the member typed
`national`. When that filter leaves exactly one candidate the answer is determined. When it
leaves ZERO (no member is `national`) or MORE THAN ONE, the function falls back to the family
list and takes the first — so the route is decided by the order rows happen to sit in.

That is not a hypothetical. Every case this gate reports today was misrouting real data:

    iso  years        candidates                                    layer-B rows at risk
    MYS  1881-1945    BNB / BSW / GBM (three colonial territories)         207
    LBY  1943-1950    LBY / TRP / CYR / FEZ (all typed `national`)          88
    PNG  1920-1948    TNGU / TPAP                                           26
    NGA  1886-1896    NGA-1886-1914 / NUP-1800-1897                          8

"at risk" is the honest word: 324 rows sat on an order-decided route, and 236 of them were
actually going somewhere wrong. The rest happened to land correctly -- `North Borneo` really
is BNB, `nigeria` really is NGA-1886-1914 -- by luck of list position rather than by anything
that would survive a re-sort.

The worst were not size errors but SUBSTITUTIONS of one territory for another:

  * 197 Mitchell rows labelled `malaysia`, 1898-1945, resolved to BNB-1881-1963 -- British
    North Borneo, i.e. Sabah -- rather than British Malaya. The items are rubber, rice paddy,
    coffee, tobacco and tea: peninsular plantation agriculture. British Malaya dominated
    world rubber output; North Borneo was marginal.
  * 20 rows labelled `Libya Tripolitania` resolved to CYR-1949-1951, the Emirate of
    CYRENAICA. Tripolitania is the west of Libya, Cyrenaica the east, and they were
    separately administered 1943-1951. The data crossed the country.
  * `British Borneo Sarawak` resolved to British North Borneo, and `Papua` to the Territory
    of NEW GUINEA -- two more cases where the label names the territory unambiguously and
    was ignored.

WHY NOTHING CAUGHT THIS. `crosscheck_matchers.py` compares the two matchers and did document
the Malaysia case (issue 44) -- but only at 1961, because it resolves FAOSTAT labels and
FAOSTAT begins in 1961. The 1898-1945 window is structurally outside its reach. Issue 44 was
CLOSED after MYS-1957-1963 was retyped `national`, which fixed 1961 and left 1881-1945
untouched: the retype moved the tie rather than removing it. This gate scans every year from
1800, so a fix that only moves a tie cannot close it again.

The families listed below are legitimate history -- one modern ISO code covering several
simultaneous colonial territories. The defect is never that they coexist; it is that the
choice between them is made by list position. Where real data carries a label naming one of
them, the route belongs in an explicit alias, which is what BASELINE_ORDERED records.

Bidirectional: a new family/candidate-set fails, and a baselined one that stops being
order-decided must be deleted.
"""
from __future__ import annotations

import collections
import csv
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(REPO, "data/final/polities_database.csv")
ALIAS_PATH = os.path.join(REPO, "pipelines/polity-autoimprove/state/applied_aliases.csv")

DEAD_STATUS = ("retired", "superseded")
FIRST_YEAR, LAST_YEAR = 1800, 2025

# (iso, candidate codes) -> why order decides, and what was done about it.
#
# Being here is NOT approval of the ambiguity. It records that the ambiguity is real history
# and that every label observed in data has been pinned by an explicit alias instead of left
# to list position. If new data arrives under a label these codes could both answer to, the
# alias is the fix -- not a change to this file.
BASELINE_ORDERED = {
    ("MYS", ("BNB-1881-1963", "BSW-1841-1963", "GBM-1895-1946")):
        "British North Borneo, Sarawak and British Malaya coexisted; all three are typed "
        "`colonial`, so no member is `national` and the filter leaves zero. 207 rows pinned "
        "by alias, including 197 `malaysia` rows moved from North Borneo to British Malaya.",
    ("MYS", ("BNB-1881-1963", "BSW-1841-1963")):
        "same three-territory family, in the years before British Malaya is constituted (1895).",
    # Three entries for the 1946-1963 MASG windows stood here when this gate was first
    # written and the gate REJECTED THEM as never reproducing. They were mine, not inherited:
    # I reasoned that a changing candidate set should be reported regardless of outcome, and
    # wrote a comment saying so -- while the code four lines below skips any window with
    # exactly one `national` member, which those windows have. The comment contradicted the
    # implementation and the bidirectional check found it immediately. Removed rather than
    # accommodated: those windows are determined, which is the whole point.
    # BOTH LBY SETS GREW BY ONE ON 2026-08-10, when FEZ-1943-1951 was created and the three
    # occupation territories got polygons (issue 156). The previous version of the second entry
    # ended "NOTE that Fezzan, the third occupied territory, is absent from the database
    # entirely, so this set is not a partition of Libya." IT IS ONE NOW: TRP + CYR + FEZ are
    # unions of disjoint GADM shabiyat whose union reproduces GADM's Libya to 0.0000 km2, with
    # all three pairwise intersections asserted at zero by audit_family_shadowing.
    #
    # A LARGER CANDIDATE SET IS NOT A WORSE ONE HERE. Adding Fezzan makes the sets bigger while
    # making the model MORE determined, because the ambiguity was never between the parts -- it
    # was that Fezzan-labelled data had nowhere to go and would have had to be routed to the
    # all-Libya row, overstating the territory it describes by 3.2x. Every observed label in both
    # windows is pinned by an explicit alias: `Libya`, `Libya Tripolitania`, `Libya Cyrenaica`,
    # `Libya Fezzan`, plus the `Tripolitania` and `Libya: Cyrenaica` variants.
    ("LBY", ("FEZ-1943-1951", "LBY-1943-1949", "TRP-1943-1951")):
        "1943-1948: Tripolitania and Fezzan alongside the all-Libya row, all three `national`, so "
        "the filter leaves three. Cyrenaica is absent from THIS window because CYR-1949-1951 is "
        "the EMIRATE, proclaimed 1949 -- the British military administration of Cyrenaica "
        "1943-1949 has no row, which is a coverage gap recorded on the TRP and FEZ pages.",

    ("LBY", ("CYR-1949-1951", "FEZ-1943-1951", "LBY-1949-1951", "TRP-1943-1951")):
        "1949-1950: all three occupation territories plus the all-Libya UN transitional row, all "
        "four `national`. This is the set that sent 20 Tripolitania rows to Cyrenaica, and 28 rows "
        "labelled `Libya` to Cyrenaica as well. The 1949 member exists because LBY-1949-1951 was "
        "moved from a 1950 start on 2026-08-05 -- before that, NO all-Libya row was live in 1949 "
        "and this gate saw a two-member set. All four are `national` because there was no Libyan "
        "state between 1943 and 1951 for them to be subnational units of.",
    ("PNG", ("PAPNG-1920-1949", "TNGU-1920-1949", "TPAP-1906-1949")):
        "the Territory of Papua and the Territory of New Guinea were administered separately "
        "1920-1949, and PAPNG-1920-1949 is the combined reporting unit over both. None is "
        "`national`, so the filter leaves zero. The two-member version of this key was replaced "
        "on 2026-08-05 when PAPNG was created; ADDING A ROW MADE THIS FAMILY MORE AMBIGUOUS, not "
        "less, and the gate required the key to be updated rather than letting the third "
        "candidate slip in silently. All five observed labels are now pinned: `papua new guinea` "
        "-> PAPNG (1922-1940) and PNG-1949-1975 (1949-1974), `New Guinea` and "
        "`New Guinea australian` -> TNGU, `Papua` -> TPAP.",
    ("NGA", ("NGA-1886-1914", "NUP-1800-1897")):
        "the Niger Coast/Royal Niger Company row overlaps the Nupe emirate 1886-1896. The 8 "
        "observed rows are labelled `nigeria` and resolve to NGA-1886-1914, which is correct, "
        "so no alias was needed -- but the choice is still made by order.",
}


def main() -> int:
    if not os.path.exists(CSV_PATH):
        print(f"FAIL: {CSV_PATH} missing; run scripts/build_database.py first")
        return 2

    with open(CSV_PATH, encoding="utf-8") as fh:
        rows = [
            r for r in csv.DictReader(fh)
            if (r.get("wiki_status") or "").strip() not in DEAD_STATUS
        ]

    families = collections.defaultdict(list)
    for r in rows:
        if r.get("iso3_code"):
            families[r["iso3_code"]].append(r)

    found = collections.defaultdict(list)
    for iso, members in families.items():
        for year in range(FIRST_YEAR, LAST_YEAR + 1):
            try:
                live = [
                    r for r in members
                    if int(r["start_year"]) <= year < int(r["end_year"])
                ]
            except (TypeError, ValueError):
                continue
            if len(live) < 2:
                continue
            national = [r for r in live if (r.get("polity_type") or "") == "national"]
            # Exactly one `national` member => the tie-break decides. Anything else => the
            # fallback takes the first row of the family list, i.e. list position decides.
            if len(national) == 1:
                continue
            key = (iso, tuple(sorted(r["polity_code"] for r in live)))
            found[key].append(year)

    aliased = set()
    if os.path.exists(ALIAS_PATH):
        with open(ALIAS_PATH, encoding="utf-8") as fh:
            aliased = {r["polity_code"] for r in csv.DictReader(fh)}

    problems = []
    for key in sorted(found):
        if key in BASELINE_ORDERED:
            continue
        years = found[key]
        unpinned = [c for c in key[1] if c not in aliased]
        problems.append(
            f"ORDER DECIDES: iso {key[0]} has {len(key[1])} live candidates for "
            f"{len(years)} year(s) {min(years)}-{max(years)} and the `national` tie-break "
            f"cannot separate them: {list(key[1])}"
            + (f" -- no alias routes to {unpinned}" if unpinned else "")
        )
    for key in sorted(set(BASELINE_ORDERED) - set(found)):
        problems.append(
            f"BASELINE_ORDERED {key} is no longer order-decided -- remove it"
        )

    total = sum(len(v) for v in found.values())
    print(f"iso families examined: {len(families)}")
    print(f"order-decided (iso, candidate-set) groups: {len(found)} "
          f"({len(BASELINE_ORDERED)} baselined)")
    print(f"order-decided (iso, year) pairs: {total}")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        print(
            "\n  A route decided by list position is not a route. Either type exactly one\n"
            "  member `national` for those years, or pin every label observed in data with an\n"
            "  explicit alias and record the candidate set here with that reasoning."
        )
        return 1

    print("\nPASS: every order-decided family is recorded and its observed labels are pinned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
