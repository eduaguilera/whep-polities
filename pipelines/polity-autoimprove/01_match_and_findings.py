#!/usr/bin/env python3
"""LayerB polity-completeness harness — Stages 0-2 (deterministic, no agents).

Goal: one data point -> one polity. Resolve every non-aggregate row in
consolidated_layer_b to a WHEP polity; classify the unresolved into findings.

Stage 0  resolve+match   (trust prior polity_code; else iso->year, else name->year)
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

# APPLIED proposed aliases: norm(original_name) -> target_polity_code (stage-3/4 output)
code_row = {p.polity_code: (p.polity_code,p.polity_name,p.iso3_code,p.s,p.e,p.polity_type) for _,p in pol.iterrows()}
override = {}
PA = os.path.join(OUT, "applied_aliases.csv")   # aliases confirmed by prior runs (status=correct)
if os.path.exists(PA):
    for r in csv.DictReader(open(PA)):
        tc = (r.get("target_polity_code") or "").strip()
        if tc in code_row: override[norm(r["original_name"])] = tc
print(f"applied aliases loaded: {len(override)}")

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
    if n in override:                                   # stage-3/4 applied alias
        return fam_for_code(override[n]), "applied_alias"
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
work["whep_code"] = work["polity_code"]            # trust prior matches
work["match_method"] = np.where(work["polity_code"].notna(), "prior", "")

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
    fam, how = fam_cache.get((row.country, row.iso3c if isinstance(row.iso3c,str) else None), (None,"none"))
    if fam is None: return (None, "unresolved", how)
    rec, st = pick_by_year(fam, eff_year(row))
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
    elif method in ("year_uncovered","no_year"):
        # entity known (family found) but no polity covers these years -> gap / range issue
        fam_span = f"{min(r[3] for r in fam if not pd.isna(r[3]))}-{max(r[4] for r in fam if not pd.isna(r[4]))}"
        ev["finding_type"] = "coverage_gap"              # D1/D7
        ev["resolved_family"] = sorted({r[0] for r in fam})
        ev["family_span"] = fam_span
    else:
        ev["finding_type"] = "other"
    findings.append(ev)

# ---------- Stage 2: triage + report ----------
findings.sort(key=lambda f: (-f["rows"]))
for ft in ("name_unresolved","coverage_gap","other"):
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
