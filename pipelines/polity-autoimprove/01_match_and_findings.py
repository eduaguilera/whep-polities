#!/usr/bin/env python3
"""LayerB polity-completeness harness — Stages 0-2 (deterministic, no agents).

Goal: one data point -> one polity. Resolve every non-aggregate row in
consolidated_layer_b to a WHEP polity; classify the unresolved into findings.

Stage 0  resolve+match   (trust prior ONLY if it's a real period polity_code; bare-iso
                          stubs and the rest -> iso->year-containment, name->year, alias)
Stage 1  detect findings (D2 name_unresolved, D1 coverage_gap, D7 range_violation)
Stage 2  triage+report    (rank; coverage% before/after; findings.json + report.md)
"""
import pandas as pd, numpy as np, json, re, unicodedata, csv, os
from collections import defaultdict

# --- config (repo-relative; external inputs overridable via env) ---
REPO  = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT   = os.path.join(REPO, "pipelines/polity-autoimprove/state")
POLDB = os.path.join(REPO, "data/final/polities_database.csv")          # in repo
# the consolidated layer-B dataset and alias table live in personal Nextcloud (not redistributable)
LB           = os.environ.get("WHEP_LAYERB", "/home/usuario/Nextcloud/whep/layer_b/consolidated_layer_b.parquet")
COMMON_NAMES = os.environ.get("WHEP_COMMON_NAMES",
    "/home/usuario/Nextcloud/WHEP_ERC 2025/Sources/datasets/unclassified_datasets/Other polities/data/whep-source/common_names.csv")
os.makedirs(OUT, exist_ok=True)
# ledger gating: never re-surface units a prior run already resolved (status correct/fixed)
LEDGER = os.path.join(OUT, "review_ledger.csv")
resolved_keys = set()
if os.path.exists(LEDGER):
    for r in csv.DictReader(open(LEDGER)):
        if (r.get("status") or "").strip() in ("correct","fixed") and r.get("key"):
            resolved_keys.add(r["key"].strip().lower())

def norm(s):
    if s is None or (isinstance(s,float) and np.isnan(s)): return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode()
    s = re.sub(r"\s*\(.*?\)\s*", " ", s)          # drop "(to 1919)" etc.
    s = re.sub(r"^the\s+", "", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

# ---------- load reference ----------
pol = pd.read_csv(POLDB)   # source of truth: the repo polities database
pol["base"] = pol["polity_name"].map(norm)
pol["s"] = pd.to_numeric(pol["start_year"], errors="coerce")
pol["e"] = pd.to_numeric(pol["end_year"],   errors="coerce")

def toks(s):
    """singularized token set, for order-insensitive name matching."""
    return frozenset(t[:-1] if len(t) > 3 and t.endswith("s") else t for t in norm(s).split() if t)

iso_fam, name_fam, tok_fam = defaultdict(list), defaultdict(list), defaultdict(list)
for _,p in pol.iterrows():
    rec = (p.polity_code, p.polity_name, p.iso3_code, p.s, p.e, p.polity_type)
    if isinstance(p.iso3_code,str) and p.iso3_code.strip():
        iso_fam[p.iso3_code.strip().upper()].append(rec)
    name_fam[p.base].append(rec)
    t = toks(p.polity_name)
    if t: tok_fam[t].append(rec)

# alias table: norm(original_name) -> norm(common_name); link to a polity family by base name
cn = pd.read_csv(COMMON_NAMES)
alias = {}
for _,r in cn.iterrows():
    o, c = norm(r["original_name"]), norm(r["common_name"])
    if o and c: alias.setdefault(o, c)

# APPLIED aliases: (original_name [, source] [, year_start-year_end]) -> target_polity_code.
# A label can resolve to DIFFERENT polities by year/source — the SOURCE's reporting unit
# need not match our period splits (see README "What a source label actually means").
code_row = {p.polity_code: (p.polity_code,p.polity_name,p.iso3_code,p.s,p.e,p.polity_type) for _,p in pol.iterrows()}
def _yr(v):
    v = str(v or "").strip()
    return int(v) if v.lstrip("-").isdigit() else None
override_rules = []
PA = os.path.join(OUT, "applied_aliases.csv")   # aliases confirmed by prior runs
if os.path.exists(PA):
    for r in csv.DictReader(open(PA)):
        tc = (r.get("target_polity_code") or "").strip()
        if tc not in code_row: continue
        override_rules.append({"n":norm(r["original_name"]), "src":(r.get("source") or "").strip() or None,
                               "y0":_yr(r.get("year_start")), "y1":_yr(r.get("year_end")), "code":tc})
blanket_override = {ru["n"]:ru["code"] for ru in override_rules if ru["y0"] is None and ru["src"] is None}
print(f"applied aliases loaded: {len(override_rules)} rules ({len(blanket_override)} blanket)")

def match_alias(name, source, year):
    """best applied-alias target for (name, source, year); prefer year- then source-specific rules."""
    n = norm(name); src = (source or ""); best=None; score=-1
    for ru in override_rules:
        if ru["n"] != n: continue
        if ru["src"] is not None and ru["src"] != src: continue
        if ru["y0"] is not None and (year is None or not (ru["y0"] <= year <= ru["y1"])): continue
        s = (2 if ru["y0"] is not None else 0) + (1 if ru["src"] is not None else 0)
        if s > score: best, score = ru["code"], s
    return best

def pick_by_year(fam, year):
    """from a polity family, pick the row whose [s,e] contains year; prefer national."""
    if pd.isna(year): return None, "no_year"
    cands = [r for r in fam if not pd.isna(r[3]) and not pd.isna(r[4]) and r[3] <= year <= r[4]]
    if not cands: return None, "year_uncovered"
    cands.sort(key=lambda r: 0 if r[5]=="national" else 1)
    return cands[0], "ok"

def fam_for_code(code):
    rec = code_row[code]; iso = rec[2]
    if isinstance(iso,str) and iso.strip().upper() in iso_fam: return iso_fam[iso.strip().upper()]
    if rec[1] and norm(rec[1]) in name_fam: return name_fam[norm(rec[1])]
    return [rec]

def resolve_family(name, iso):
    """return (family, how). High-precision only: applied-alias override, iso,
    exact name, token-set equality, or alias-table."""
    n = norm(name)
    if n in blanket_override:                            # year/source-independent applied alias
        return fam_for_code(blanket_override[n]), "applied_alias"
    if isinstance(iso,str) and iso.strip().upper() in iso_fam:
        return iso_fam[iso.strip().upper()], "iso"
    if n in name_fam: return name_fam[n], "name"
    t = toks(name)
    if t in tok_fam: return tok_fam[t], "tokenset"      # "Korea South" == "South Korea"
    if n in alias:                                       # spelling alias -> canonical
        a = alias[n]
        if a in name_fam: return name_fam[a], "alias"
        if toks(a) in tok_fam: return tok_fam[toks(a)], "alias"
    return None, "none"

# ---------- Stage 0: match ----------
df = pd.read_parquet(LB)
work = df[~df.is_aggregate].copy()
# trust a prior polity_code ONLY if it is a real period-specific WHEP polity_code.
# bare-iso stubs (deu, gbr, jpn) carry no period/territory -> do NOT trust them; send
# them to the resolver so iso+year-containment resolves each to its period polity.
valid_codes = set(pol["polity_code"])
trusted = work["polity_code"].where(work["polity_code"].isin(valid_codes))
work["whep_code"] = trusted
work["match_method"] = np.where(trusted.notna(), "prior", "")
_bare = int(work["polity_code"].notna().sum() - trusted.notna().sum())
print(f"bare-iso stubs NOT trusted (sent to resolver): {_bare:,}")

todo = work[work.whep_code.isna()]
# resolve per distinct (country, iso) to avoid recomputing
keys = todo[["country","iso3c"]].drop_duplicates()
fam_cache = {}
for _,k in keys.iterrows():
    fam_cache[(k.country, k.iso3c if isinstance(k.iso3c,str) else None)] = resolve_family(k.country, k.iso3c)

def eff_year(row):
    """row year, or the END year of a period-average label like '1934-1938'."""
    if pd.notna(row.year): return row.year
    if isinstance(row.period, str):
        yy = re.findall(r"\d{4}", row.period)
        if yy: return int(yy[-1])
    return np.nan

def assign(row):
    ey = eff_year(row)
    ac = match_alias(row.country, getattr(row, "source", None), ey)   # year/source-conditional alias first
    if ac:
        rec, st = pick_by_year(fam_for_code(ac), ey)
        if rec is not None: return (rec[0], "matched", "applied_alias")
    fam, how = fam_cache.get((row.country, row.iso3c if isinstance(row.iso3c,str) else None), (None,"none"))
    if fam is None: return (None, "unresolved", how)
    rec, st = pick_by_year(fam, ey)
    if rec is None: return (None, st, how)            # year_uncovered / no_year
    return (rec[0], "matched", how)

res = todo.apply(assign, axis=1, result_type="expand")
res.columns = ["code2","status2","how2"]
work.loc[todo.index, "whep_code"] = res["code2"]
work.loc[todo.index, "match_method"] = np.where(res["code2"].notna(), res["how2"], res["status2"])

matched = work.whep_code.notna()
print(f"Stage 0: {matched.sum():,}/{len(work):,} rows matched ({100*matched.mean():.1f}%)")

# ---------- Stage 1: findings ----------
findings = []
un = work[work.whep_code.isna()]
# group by (country, iso, resolution-status)
for (country, iso, method), grp in un.groupby([un.country, un.iso3c.fillna(""), un.match_method]):
    yrs = pd.to_numeric(grp.year, errors="coerce").dropna()
    ev = {
        "entity": country, "iso_in_data": iso or None,
        "rows": int(len(grp)), "years": (f"{int(yrs.min())}-{int(yrs.max())}" if len(yrs) else None),
        "sources": sorted(grp.source.unique().tolist()),
        "items_sample": sorted(grp.item.dropna().unique().tolist())[:5],
    }
    fam, how = resolve_family(country, iso if iso else None)
    if method == "unresolved" or fam is None:
        ev["finding_type"] = "name_unresolved"           # D2: needs alias OR new polity
        ev["nearest_guess"] = None
    elif method == "no_year":
        # entity known (family found) but rows carry null year values — source data quality issue,
        # NOT a temporal coverage gap. eff_year() already attempts period-column recovery;
        # if period is also null these rows are permanently undatable.
        fam_span = f"{min(r[3] for r in fam if not pd.isna(r[3]))}-{max(r[4] for r in fam if not pd.isna(r[4]))}"
        ev["finding_type"] = "data_error"                # undatable source records
        ev["resolved_family"] = sorted({r[0] for r in fam})
        ev["family_span"] = fam_span
        ev["note"] = "rows lack year values in source; excluded from coverage-gap accounting"
    elif method == "year_uncovered":
        # entity known (family found) but no polity covers these years -> gap / range issue
        fam_span = f"{min(r[3] for r in fam if not pd.isna(r[3]))}-{max(r[4] for r in fam if not pd.isna(r[4]))}"
        ev["finding_type"] = "coverage_gap"              # D1/D7
        ev["resolved_family"] = sorted({r[0] for r in fam})
        ev["family_span"] = fam_span
    else:
        ev["finding_type"] = "other"
    findings.append(ev)

# ---------- Stage 1b: FAOSTAT-era findings (faostat-era-matching state) ----------
# pipelines/faostat-era-matching crosslinks the FAOSTAT (1961+) reporting
# universe by numeric area code and leaves its residual queue in state CSVs.
# Ingest that queue here so the autoimprove loop works FAOSTAT-era gaps the
# same way as Layer-B ones (same finding shapes, same ledger gating).
FAOSTAT_STATE = os.path.join(REPO, "pipelines/faostat-era-matching/state")
def _faostat_era_findings():
    out = []
    unm = os.path.join(FAOSTAT_STATE, "unmatched.csv")
    if os.path.exists(unm):
        for r in csv.DictReader(open(unm)):
            out.append({
                "entity": r["area_name"], "iso_in_data": r.get("iso3") or None,
                "rows": int(float(r.get("n_rows") or 0)),
                "years": f"{r['year_start']}-{r['year_end']}",
                "sources": ["faostat"], "items_sample": [],
                "finding_type": "name_unresolved", "nearest_guess": None,
                "note": f"faostat-era-matching: no polity for FAOSTAT area "
                        f"{r['area_code']}; {r.get('note') or ''}".strip(),
            })
    amb = os.path.join(FAOSTAT_STATE, "ambiguous.csv")
    if os.path.exists(amb):
        by_area = defaultdict(list)
        for r in csv.DictReader(open(amb)):
            by_area[(r["area_code"], r["original_name"])].append(r)
        for (code, name), rs in by_area.items():
            out.append({
                "entity": name, "iso_in_data": rs[0].get("iso3") or None,
                "rows": int(float(rs[0].get("rows") or 0)),
                "years": f"{min(r['year_start'] for r in rs)}-{max(r['year_end'] for r in rs)}",
                "sources": ["faostat"], "items_sample": [],
                "finding_type": "coverage_gap",
                "resolved_family": sorted({r["target_polity_code"] for r in rs}),
                "note": f"faostat-era-matching: overlapping polity periods for "
                        f"FAOSTAT area {code}; settle from data magnitudes and add "
                        f"a manual span route in pipelines/faostat-era-matching/match.R",
            })
    fal = os.path.join(FAOSTAT_STATE, "faostat_aliases.csv")
    if os.path.exists(fal):
        seen = set()
        for r in csv.DictReader(open(fal)):
            basis = r.get("basis") or ""
            if "no covering polity period" in basis and r["area_code"] not in seen:
                seen.add(r["area_code"])
                out.append({
                    "entity": r["original_name"], "iso_in_data": r.get("iso3") or None,
                    "rows": int(float(r.get("rows") or 0)),
                    "years": f"{r['year_start']}-{r['year_end']}",
                    "sources": ["faostat"], "items_sample": [],
                    "finding_type": "coverage_gap",
                    "note": "faostat-era-matching: " + basis,
                })
    return out
_fao_findings = _faostat_era_findings()
print(f"Stage 1b: +{len(_fao_findings)} FAOSTAT-era findings (faostat-era-matching state)")
findings.extend(_fao_findings)

# ---------- Stage 2: triage + report (ledger-gated) ----------
_before = len(findings)
findings = [f for f in findings if f["entity"].strip().lower() not in resolved_keys]
if _before != len(findings):
    print(f"  ledger: skipped {_before-len(findings)} findings already resolved in prior runs")
findings.sort(key=lambda f: (-f["rows"]))
for ft in ("name_unresolved","coverage_gap","data_error","other"):
    bucket=[f for f in findings if f["finding_type"]==ft]
    print(f"  {ft}: {len(bucket)} distinct entities, {sum(f['rows'] for f in bucket):,} rows")

json.dump({"summary": {
            "total_rows": int(len(work)),
            "matched_rows": int(matched.sum()),
            "match_pct": round(100*matched.mean(),1),
            "unmatched_rows": int((~matched).sum()),
          },
          "findings": findings},
          open(f"{OUT}/findings.json","w"), indent=1)
work[["source","country","iso3c","year","item","value","unit","whep_code","match_method"]] \
    .to_parquet(f"{OUT}/matched_rows.parquet", index=False)

# coverage by source after
cov = work.groupby("source").apply(lambda g: pd.Series({
        "rows": len(g), "matched": g.whep_code.notna().sum(),
        "pct": round(100*g.whep_code.notna().mean(),1)})).reset_index()
print("\n=== coverage by source (after Stage 0) ===")
print(cov.to_string(index=False))
print(f"\nwrote findings.json ({len(findings)} findings) + matched_rows.parquet")
