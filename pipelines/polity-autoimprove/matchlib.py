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

    def __init__(self, polities_csv, applied_aliases_csv=None, common_names_csv=None,
                 verbose=True):
        pol = pd.read_csv(polities_csv)   # source of truth: the repo polities database
        pol["base"] = pol["polity_name"].map(norm)
        pol["s"] = pd.to_numeric(pol["start_year"], errors="coerce")
        pol["e"] = pd.to_numeric(pol["end_year"],   errors="coerce")
        self.pol = pol
        self.valid_codes = set(pol["polity_code"])

        self.iso_fam, self.name_fam, self.tok_fam = defaultdict(list), defaultdict(list), defaultdict(list)
        for _, p in pol.iterrows():
            rec = (p.polity_code, p.polity_name, p.iso3_code, p.s, p.e, p.polity_type)
            if isinstance(p.iso3_code, str) and p.iso3_code.strip():
                self.iso_fam[p.iso3_code.strip().upper()].append(rec)
            self.name_fam[p.base].append(rec)
            t = toks(p.polity_name)
            if t: self.tok_fam[t].append(rec)
        self.code_row = {p.polity_code: (p.polity_code, p.polity_name, p.iso3_code, p.s, p.e, p.polity_type)
                         for _, p in pol.iterrows()}

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
        if applied_aliases_csv and os.path.exists(applied_aliases_csv):
            for r in csv.DictReader(open(applied_aliases_csv)):
                tc = (r.get("target_polity_code") or "").strip()
                if tc not in self.code_row: continue
                self.override_rules.append({
                    "n": norm(r["original_name"]),
                    "src": (r.get("source") or "").strip() or None,
                    "y0": _yr(r.get("year_start")), "y1": _yr(r.get("year_end")),
                    "code": tc})
        self.blanket_override = {ru["n"]: ru["code"] for ru in self.override_rules
                                 if ru["y0"] is None and ru["src"] is None}
        if verbose:
            print(f"applied aliases loaded: {len(self.override_rules)} rules "
                  f"({len(self.blanket_override)} blanket)")

    def match_alias(self, name, source, year):
        """best applied-alias target for (name, source, year); prefer year- then source-specific rules."""
        n = norm(name); src = (source or ""); best = None; score = -1
        for ru in self.override_rules:
            if ru["n"] != n: continue
            if ru["src"] is not None and ru["src"] != src: continue
            if ru["y0"] is not None and (year is None or not (ru["y0"] <= year <= ru["y1"])): continue
            s = (2 if ru["y0"] is not None else 0) + (1 if ru["src"] is not None else 0)
            if s > score: best, score = ru["code"], s
        return best

    @staticmethod
    def pick_by_year(fam, year):
        """from a polity family, pick the row whose [s,e] contains year; prefer national."""
        if pd.isna(year): return None, "no_year"
        cands = [r for r in fam if not pd.isna(r[3]) and not pd.isna(r[4]) and r[3] <= year <= r[4]]
        if not cands: return None, "year_uncovered"
        cands.sort(key=lambda r: 0 if r[5] == "national" else 1)
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
        ac = self.match_alias(name, source, year)
        if ac:
            # HONOR the alias's explicit target when its period covers the year.
            # (Re-picking from the target's ISO family let a same-span sibling
            # polity shadow the named target — e.g. an "Alaska" period polity
            # with iso3=USA absorbing mainland-USA rows aliased to USA-1867-1959.)
            rec = self.code_row.get(ac)
            if rec is not None and not pd.isna(year) and not pd.isna(rec[3]) \
                    and not pd.isna(rec[4]) and rec[3] <= year <= rec[4]:
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
