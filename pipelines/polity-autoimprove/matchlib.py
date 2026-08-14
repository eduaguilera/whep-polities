#!/usr/bin/env python3
"""Shared deterministic matching core: label/iso/year -> candidate WHEP polity.

Extracted verbatim from 01_match_and_findings.py so every intake path (layer B,
arbitrary user datasets via 00_intake.py) resolves through ONE rule set.

IMPORTANT: the deterministic pass only proposes a CANDIDATE polity (routing by
alias table, iso family, normalized name, year containment). It does not verify
that the source's reporting territory equals the polity's territory — that is
the assertion-verification workflow's job (see README, "assertion").
"""
import pandas as pd, numpy as np, re, unicodedata, csv, os
from collections import defaultdict

# ---------------------------------------------------------------------------
# THE YEAR CONVENTION, named once so it can be checked rather than assumed.
#
# A polity period is the half-open interval [start_year, end_year): `end_year`
# is EXCLUSIVE. CIV-1893-1900 covers 1893-1899. That is stated in
# wiki/README.md, enforced on the polity_code by
# scripts/validate_code_year_agreement.py, and assumed by every gate.
#
# It was NOT what this matcher implemented. pick_by_year tested
# `start <= year <= end`, so at a transition year — where a predecessor's
# end_year equals its successor's start_year — the ENDED period was a
# candidate, and in any family with a third overlapping row it WON on list
# order. Measured against the consolidated layer-B panel (192,670 rows):
# 12 (label, source, year) tuples covering 190 rows resolved to a period that
# had already ended, among them every India transition (1886, 1893, 1914,
# 1937, 1947, 1949), Greece 1919, Indonesia 1949 and Malaysia 1957. Every one
# of the 12 now resolves to what a strictly exclusive reading would give.
#
# The two R matchers declare and use the same constant, and
# scripts/validate_year_semantics.py fails if any of them stops doing so — the
# point of issue #131 being that a component reading this field the other way
# produces a plausible answer and no error.
#
# NOT the same field, and deliberately unchanged here: alias `year_end` in
# pipelines/polity-autoimprove/state/applied_aliases.csv is INCLUSIVE (see
# scripts/write_label_alias_map.py), so a consistent pair has
# end_year == year_end + 1. Where an alias NAMES a target, its human decision
# is honoured as written; issues #79 and #90 own that seam.
END_YEAR_EXCLUSIVE = True

# The alias registry's OWN year bound reads the OTHER way, and is meant to:
# `year_end` in state/applied_aliases.csv and in the published
# data/final/label_alias_map.csv is INCLUSIVE (scripts/write_label_alias_map.py
# publishes it as "last year (inclusive)"), so a consistent pair has
# end_year == year_end + 1. Two fields, two meanings — that is not the defect.
#
# The defect is that this reading was, like the polity-side one before issue
# #131, written as a bare comparison operator in every component that uses it,
# and an operator cannot be compared across files. A name can. Declared here and
# in pipelines/faostat-era-matching/match.R (which CONVERTS a polity end_year
# into an alias year_end when it emits routing rules), and held together by
# scripts/validate_year_semantics.py.
ALIAS_YEAR_END_INCLUSIVE = True


def covers(start, end, year):
    """Does the polity period contain `year`?

    The single place this repository's Python side decides that question.
    `end` is exclusive when END_YEAR_EXCLUSIVE, so a row with end == year has
    ALREADY ENDED and does not cover it.
    """
    return start <= year < end if END_YEAR_EXCLUSIVE else start <= year <= end


def alias_covers(y0, y1, year):
    """Does an ALIAS rule's year range contain `year`?

    The single place this repository's Python side decides that question. A
    missing bound is unbounded on that side (see match_alias). `y1` is the LAST
    year the rule applies to when ALIAS_YEAR_END_INCLUSIVE — the opposite of
    `covers()` above, deliberately, because it is a different field.
    """
    if year is None or pd.isna(year):
        return False
    if y0 is not None and year < y0:
        return False
    if y1 is not None and (year > y1 if ALIAS_YEAR_END_INCLUSIVE else year >= y1):
        return False
    return True


def norm(s):
    if s is None or (isinstance(s, float) and np.isnan(s)): return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"\s*\(.*?\)\s*", " ", s)          # drop "(to 1919)" etc.
    s = re.sub(r"^the\s+", "", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def toks(s):
    """singularized token set, for order-insensitive name matching."""
    return frozenset(t[:-1] if len(t) > 3 and t.endswith("s") else t for t in norm(s).split() if t)


def eff_year(year, period=None):
    """the row's year, or the END year of a period-average label like '1934-1938'."""
    if pd.notna(year): return year
    if isinstance(period, str):
        yy = re.findall(r"\d{4}", period)
        if yy: return int(yy[-1])
    return np.nan


def _yr(v):
    v = str(v or "").strip()
    return int(v) if v.lstrip("-").isdigit() else None


class Matcher:
    """Deterministic candidate resolver over the polities DB + alias tables.

    Family record layout (tuple): (polity_code, polity_name, iso3_code,
    start_year, end_year, polity_type) — same as 01's `rec`.
    """

    # wiki_status values whose polities must NEVER receive data: 'retired'
    # (row withdrawn) and 'superseded' (split into finer rows, carries
    # superseded_by). Both remain in the DB for provenance, and a collapsed
    # dead row typically spans ALL years with type=national — so left in the
    # families it silently outranks its own live successors.
    DEAD_STATUS = ("retired", "superseded")

    def __init__(self, polities_csv, applied_aliases_csv=None, common_names_csv=None,
                 verbose=True, dead_status=DEAD_STATUS):
        pol = pd.read_csv(polities_csv)   # source of truth: the repo polities database
        pol["base"] = pol["polity_name"].map(norm)
        pol["s"] = pd.to_numeric(pol["start_year"], errors="coerce")
        pol["e"] = pd.to_numeric(pol["end_year"],   errors="coerce")
        self.pol = pol                    # full table (metadata lookups)
        status = pol.get("wiki_status")
        self.dead_codes = set() if status is None else \
            set(pol.loc[status.isin(dead_status), "polity_code"])
        live = pol[~pol["polity_code"].isin(self.dead_codes)]
        self.valid_codes = set(live["polity_code"])   # matchable codes only

        self.iso_fam, self.name_fam, self.tok_fam = defaultdict(list), defaultdict(list), defaultdict(list)
        for _, p in live.iterrows():
            rec = (p.polity_code, p.polity_name, p.iso3_code, p.s, p.e, p.polity_type)
            if isinstance(p.iso3_code, str) and p.iso3_code.strip():
                self.iso_fam[p.iso3_code.strip().upper()].append(rec)
            self.name_fam[p.base].append(rec)
            t = toks(p.polity_name)
            if t: self.tok_fam[t].append(rec)
        self.code_row = {p.polity_code: (p.polity_code, p.polity_name, p.iso3_code, p.s, p.e, p.polity_type)
                         for _, p in live.iterrows()}
        if verbose and self.dead_codes:
            print(f"excluded from matching: {len(self.dead_codes)} dead polities "
                  f"({'/'.join(dead_status)}): {', '.join(sorted(self.dead_codes))}")

        # spelling-alias table: norm(original_name) -> norm(common_name)
        self.alias = {}
        if common_names_csv and os.path.exists(common_names_csv):
            cn = pd.read_csv(common_names_csv)
            for _, r in cn.iterrows():
                o, c = norm(r["original_name"]), norm(r["common_name"])
                if o and c: self.alias.setdefault(o, c)

        # APPLIED aliases: (original_name [, source] [, year_start-year_end]) -> target_polity_code.
        # A label can resolve to DIFFERENT polities by year/source — the SOURCE's reporting
        # unit need not match our period splits.
        self.override_rules = []
        self.stale_alias_targets = defaultdict(int)   # alias rows aimed at dead polities
        if applied_aliases_csv and os.path.exists(applied_aliases_csv):
            for r in csv.DictReader(open(applied_aliases_csv)):
                tc = (r.get("target_polity_code") or "").strip()
                if tc in self.dead_codes:
                    # the alias itself is stale: let the label fall through to
                    # family resolution (which now sees only live polities)
                    self.stale_alias_targets[tc] += 1
                    continue
                if tc not in self.code_row: continue
                self.override_rules.append({
                    "n": norm(r["original_name"]),
                    "src": (r.get("source") or "").strip() or None,
                    "y0": _yr(r.get("year_start")), "y1": _yr(r.get("year_end")),
                    "code": tc})
        # Blanket means NEITHER bound, for the same reason match_alias below does:
        # keying on `y0` alone classified a rule bounded only above as blanket.
        self.blanket_override = {ru["n"]: ru["code"] for ru in self.override_rules
                                 if ru["y0"] is None and ru["y1"] is None
                                 and ru["src"] is None}
        # AMBIGUITY GUARD: match_alias breaks ties by file order (`if s > score`
        # keeps the first rule at a given specificity). Two rules with the SAME
        # specificity, overlapping years and DIFFERENT targets therefore resolve
        # silently by position in the CSV — which is how a broad medium-confidence
        # "russian federation 1917-1991 -> RSFSR" rule sat unnoticed behind six
        # finer high-confidence rules pointing at the F228 chain. Report them.
        self.ambiguous_alias_pairs = []
        by_label = defaultdict(list)
        for ru in self.override_rules:
            by_label[(ru["n"], ru["src"])].append(ru)
        for (name, src), rules in by_label.items():
            for i, a in enumerate(rules):
                for b in rules[i + 1:]:
                    if a["code"] == b["code"]: continue
                    ab = a["y0"] is not None or a["y1"] is not None
                    bb = b["y0"] is not None or b["y1"] is not None
                    if ab != bb: continue                                  # different specificity
                    if not ab:                                             # both blanket
                        self.ambiguous_alias_pairs.append((name, src, a["code"], b["code"], "blanket"))
                    else:
                        # Treat a missing bound as unbounded on that side, so a half-open
                        # rule is compared against its neighbours rather than skipped.
                        a0 = a["y0"] if a["y0"] is not None else -10**6
                        a1 = a["y1"] if a["y1"] is not None else 10**6
                        b0 = b["y0"] if b["y0"] is not None else -10**6
                        b1 = b["y1"] if b["y1"] is not None else 10**6
                        if not (a0 <= b1 and b0 <= a1): continue
                        lo, hi = max(a0, b0), min(a1, b1)
                        # a ONE-year overlap is the shared transition year of two
                        # adjacent periods (inclusive ranges always touch there) and
                        # is resolved by the successor convention — not ambiguity.
                        if hi - lo < 1: continue
                        self.ambiguous_alias_pairs.append(
                            (name, src, a["code"], b["code"], f"{lo}-{hi}"))
        if verbose:
            print(f"applied aliases loaded: {len(self.override_rules)} rules "
                  f"({len(self.blanket_override)} blanket)")
            if self.ambiguous_alias_pairs:
                print(f"  AMBIGUOUS: {len(self.ambiguous_alias_pairs)} equal-specificity alias "
                      f"pair(s) overlap with different targets — resolved by CSV order, not by rule:")
                for name, src, c1, c2, where in self.ambiguous_alias_pairs[:10]:
                    print(f"    '{name}' [{src or 'any source'}] {where}: {c1} vs {c2}")
            if self.stale_alias_targets:
                n = sum(self.stale_alias_targets.values())
                print(f"  STALE: {n} alias rule(s) target dead polities, ignored -> "
                      f"{dict(self.stale_alias_targets)}; rewrite them to the live successor")

    def match_alias(self, name, source, year):
        """best applied-alias TARGET CODE for (name, source, year), or None."""
        ru = self.match_alias_rule(name, source, year)
        return ru["code"] if ru else None

    def match_alias_rule(self, name, source, year):
        """best applied-alias RULE for (name, source, year).

        Returns the rule rather than just its target because a caller sometimes
        has to know WHAT THE RULE SAID, not only where it points: `assign()`
        honours an alias over a target period that has already ended only when
        the rule itself names that year as its inclusive `year_end`. See there.

        Preference order: year-scoped over blanket, then source-scoped, then —
        among equally-scoped rules — the NARROWER year range. That last
        tie-break matters: without it two year-scoped rules covering the same
        year scored identically and the winner was decided by position in the
        CSV, so a broad 1919-1956 rule silently beat a specific 1949-1951 one.

        A MISSING BOUND IS UNBOUNDED ON THAT SIDE, not blanket on both. This used
        to key everything on `y0`, so a rule bounded only above skipped the year
        test entirely and matched every year. One published alias is
        `italy | iia | (blank) | 1860 -> SAR-1800-1860`, which meant IIA data
        labelled "italy" resolved to Sardinia in the year 2000.

        validate_unranged_aliases.py already permits that row on the stated
        grounds that its `year_end` is "bounded exactly where it matters" — the
        rule it enforces is about the upper bound alone. That was true of the
        gate and false of this matcher, which is the disagreement fixed here:
        two components of one repository read the same field differently, and
        the gate's reasoning is the one worth keeping.
        """
        n = norm(name); src = (source or "")
        best, best_rank = None, None
        for ru in self.override_rules:
            if ru["n"] != n: continue
            if ru["src"] is not None and ru["src"] != src: continue
            bounded = ru["y0"] is not None or ru["y1"] is not None
            lo = ru["y0"] if ru["y0"] is not None else -10**6
            hi = ru["y1"] if ru["y1"] is not None else 10**6
            if bounded and not alias_covers(ru["y0"], ru["y1"], year): continue
            span = (hi - lo) if bounded else 10**6
            rank = ((2 if bounded else 0) + (1 if ru["src"] is not None else 0),
                    -span)                              # higher score, then narrower range
            if best_rank is None or rank > best_rank:
                best, best_rank = ru, rank
        return best

    @staticmethod
    def pick_by_year(fam, year):
        """from a polity family, pick the row covering `year`; prefer national.

        The candidate set is gathered INCLUSIVELY and then narrowed, rather than
        gathered with `covers()` outright, and the difference is the whole of the
        cost line in issue #131. Under a strict exclusive gather, 13 layer-B
        (label, source, year) tuples — 83 rows, Hungary 1919, Syria 1945,
        Senegal 1959, Burkina Faso 1932 among them — stop resolving to anything,
        because their family has no period starting at the boundary year at all.
        Losing those is not a fix; it is the same defect with the sign flipped.

        So: a period that has ENDED (`not covers(...)`, i.e. end_year == year)
        loses to the successor that STARTS here, when that successor is unique at
        its rank and is not a worse polity_type. Otherwise it is kept, and the
        year resolves as it did before.

        Both guards are load-bearing and were measured, not assumed:
          - the UNIQUENESS guard: at Libya 1949 both CYR-1949-1951 (Cyrenaica
            alone) and LBY-1949-1951 (the UN transitional administration) start,
            and both are `national`, so "the successor" is not a fact and family
            order would pick it. Uniqueness is judged at the BEST rank present,
            not over all starters — otherwise Indonesia 1949 stayed on the ended
            IDN-1945-1949 because three subnational Dutch-era reporting units
            also begin in 1949 alongside the one national successor, and the USA
            at 1867 stayed on USA-1848-1867 because ALK-1867-1959 begins there.
          - the TYPE guard: at Ghana 1956 the only row covering the year is
            BTL-1920-1957 — British TOGOLAND, a different territory that merely
            shares iso3 GHA — so dropping GHA-1898-1956 would move whole-Ghana
            data onto it. Czechoslovakia 1918 is likewise held back because the
            row starting there is typed `aggregate`.
        """
        if pd.isna(year): return None, "no_year"
        cands = [r for r in fam if not pd.isna(r[3]) and not pd.isna(r[4]) and r[3] <= year <= r[4]]
        if not cands: return None, "year_uncovered"
        rank = lambda r: 0 if r[5] == "national" else 1
        if len(cands) > 1:
            expired = [r for r in cands if not covers(r[3], r[4], year) and r[3] != year]
            starters = [r for r in cands if r[3] == year and covers(r[3], r[4], year)]
            if starters:                       # uniqueness is judged at the BEST rank
                best = min(rank(r) for r in starters)
                starters = [r for r in starters if rank(r) == best]
            if expired and len(starters) == 1 \
                    and rank(starters[0]) <= min(rank(r) for r in expired):
                cands = [r for r in cands if r not in expired]
        cands.sort(key=rank)
        return cands[0], "ok"

    def fam_for_code(self, code):
        rec = self.code_row[code]; iso = rec[2]
        if isinstance(iso, str) and iso.strip().upper() in self.iso_fam: return self.iso_fam[iso.strip().upper()]
        if rec[1] and norm(rec[1]) in self.name_fam: return self.name_fam[norm(rec[1])]
        return [rec]

    def resolve_family(self, name, iso):
        """return (family, how). High-precision only: applied-alias override, iso,
        exact name, token-set equality, or alias-table."""
        n = norm(name)
        if n in self.blanket_override:                       # year/source-independent applied alias
            return self.fam_for_code(self.blanket_override[n]), "applied_alias"
        if isinstance(iso, str) and iso.strip().upper() in self.iso_fam:
            return self.iso_fam[iso.strip().upper()], "iso"
        if n in self.name_fam: return self.name_fam[n], "name"
        t = toks(name)
        if t in self.tok_fam: return self.tok_fam[t], "tokenset"   # "Korea South" == "South Korea"
        if n in self.alias:                                  # spelling alias -> canonical
            a = self.alias[n]
            if a in self.name_fam: return self.name_fam[a], "alias"
            if toks(a) in self.tok_fam: return self.tok_fam[toks(a)], "alias"
        return None, "none"

    def assign(self, name, iso, source, year, fam_cache=None):
        """full per-row resolution: (candidate_code|None, status, how).
        Same decision order as 01's assign(): year/source-conditional alias first,
        then cached family + year containment."""
        alias_rule = self.match_alias_rule(name, source, year)
        ac = alias_rule["code"] if alias_rule else None
        if ac:
            # HONOR the alias's explicit target when its period covers the year.
            # NOT plain covers() on purpose: an alias row is a HUMAN decision
            # keyed on an INCLUSIVE year_end, so "Libya Tripolitania | fao1952 |
            # ...-1951 -> TRP-1943-1951" asserts that 1951 belongs to
            # Tripolitania. Applying END_YEAR_EXCLUSIVE here would silently
            # overrule that and, measured, would move 12 more tuples / 137 rows —
            # sending whole-Libya 1949 to Cyrenaica alone and Tripolitania 1951 to
            # all of Libya. Whether those alias bounds are right is issues #79/#90;
            # this matcher is not the place to decide it.
            #
            # BUT ONLY WHERE THE RULE ACTUALLY SAID IT. This used to test
            # `rec[3] <= year <= rec[4]` — the INCLUSIVE reading of the TARGET
            # POLITY's `end_year`, which is the exclusive field — for every alias,
            # including the ones that carry no year bound at all. A blanket alias
            # makes no claim about a boundary year, so there was no human decision
            # to honour and the seam of issue #131 survived inside the alias path:
            # 219 of 903 rules could reach their target's `end_year`, and 19 of
            # them did so WITHOUT naming that year as their `year_end`. Now the
            # inclusive reading applies only when `year_end == year`, i.e. when a
            # person wrote that year down; everything else falls through to
            # year-containment in the family, exactly like an unaliased label.
            #
            # Measured effect on the consolidated layer-B panel (192,670 rows,
            # 17,599 (label, source, year, iso3) tuples): ZERO tuples change.
            # Enumerated over the rules themselves, exactly one answer moves —
            # blanket "belgian congo" at 1960 goes from COD-1910-1960 (which ends
            # in 1960 and so does not cover it) to COD-1960-2025, the row that
            # starts there. The other 18 already resolved to the same code by
            # fallback, because their family has no period starting at the
            # boundary.
            # (Re-picking from the target's ISO family let a same-span sibling
            # polity shadow the named target — e.g. an "Alaska" period polity
            # with iso3=USA absorbing mainland-USA rows aliased to USA-1867-1959.)
            rec = self.code_row.get(ac)
            if rec is not None and not pd.isna(year) and not pd.isna(rec[3]) \
                    and not pd.isna(rec[4]) \
                    and (covers(rec[3], rec[4], year)
                         or (ALIAS_YEAR_END_INCLUSIVE
                             and year == rec[4] and alias_rule["y1"] == year)):
                return (ac, "matched", "applied_alias")
            # year outside the target's own span: the alias names a family
            # representative — fall back to year-containment within the family
            rec, st = self.pick_by_year(self.fam_for_code(ac), year)
            if rec is not None: return (rec[0], "matched", "applied_alias")
        key = (name, iso if isinstance(iso, str) else None)
        if fam_cache is not None and key in fam_cache:
            fam, how = fam_cache[key]
        else:
            fam, how = self.resolve_family(name, iso if isinstance(iso, str) else None)
            if fam_cache is not None: fam_cache[key] = (fam, how)
        if fam is None: return (None, "unresolved", how)
        rec, st = self.pick_by_year(fam, year)
        if rec is None: return (None, st, how)               # year_uncovered / no_year
        return (rec[0], "matched", how)
