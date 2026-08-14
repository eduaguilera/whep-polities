#!/usr/bin/env python3
"""LayerB polity-completeness harness — Stages 0-2 (deterministic, no agents).

Goal: one data point -> one polity. Resolve every non-aggregate row in
consolidated_layer_b to a WHEP polity; classify the unresolved into findings.

Stage 0  resolve+match   (trust prior ONLY if it's a real period polity_code; bare-iso
                          stubs and the rest -> iso->year-containment, name->year, alias)
Stage 1  detect findings (D2 name_unresolved, D1 coverage_gap, D7 range_violation)
Stage 2  triage+report    (rank; coverage% before/after; findings.json + report.md)
"""
import pandas as pd, numpy as np, json, re, unicodedata, csv, os, hashlib
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
# — but ONLY while the unit's observable evidence is unchanged (see Stage 2:
# evidence_hash mismatch or missing hash reopens the unit).
LEDGER = os.path.join(OUT, "review_ledger.csv")
banked = {}      # lowercased key -> its ledger row (correct/fixed)
if os.path.exists(LEDGER):
    for r in csv.DictReader(open(LEDGER)):
        if (r.get("status") or "").strip() in ("correct","fixed") and r.get("key"):
            banked[r["key"].strip().lower()] = r

# ---------- matching core (shared): see matchlib.py ----------
# The deterministic pass only proposes CANDIDATES (alias/iso/name routing +
# year containment); assertion-level verification is agent work downstream.
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from matchlib import Matcher, norm, toks, eff_year as _eff_year
import extdata

PA = os.path.join(OUT, "applied_aliases.csv")   # aliases confirmed by prior runs
M = Matcher(POLDB, applied_aliases_csv=PA, common_names_csv=COMMON_NAMES)
pol = M.pol
resolve_family, match_alias = M.resolve_family, M.match_alias
pick_by_year, fam_for_code = M.pick_by_year, M.fam_for_code

# ---------- Stage 0: match ----------
df = pd.read_parquet(LB)
# Layer B's `polity_code` holds LOWERCASE ISO CODES, not polity codes (issue 95,
# option 4). Renamed on the way in, so nothing below can join it to ours by a name
# that looks right and matches nothing. `polity_codes=` makes the rename refuse if
# the upstream file ever starts holding real codes.
valid_codes = set(pol["polity_code"])
df = extdata.rename_layer_b_misnamed(df, polity_codes=valid_codes, where="layer B")
work = df[~df.is_aggregate].copy()
# trust a prior code ONLY if it is a real period-specific WHEP polity_code. Bare-iso
# stubs (deu, gbr, jpn) carry no period/territory -> do NOT trust them; send them to
# the resolver so iso+year-containment resolves each to its period polity. Measured
# 2026-08-13: 0 of layer B's 166 distinct values is a real code, so nothing is
# trusted today -- but the branch stays, because the rename above is what would
# make a fixed upstream visible instead of silent.
trusted = work["iso3_lower"].where(work["iso3_lower"].isin(valid_codes))
work["whep_code"] = trusted
work["match_method"] = np.where(trusted.notna(), "prior", "")
_bare = int(work["iso3_lower"].notna().sum() - trusted.notna().sum())
print(f"bare-iso stubs NOT trusted (sent to resolver): {_bare:,}")

todo = work[work.whep_code.isna()]
# resolve per distinct (country, iso) to avoid recomputing
keys = todo[["country","iso3c"]].drop_duplicates()
fam_cache = {}
for _,k in keys.iterrows():
    fam_cache[(k.country, k.iso3c if isinstance(k.iso3c,str) else None)] = resolve_family(k.country, k.iso3c)

def eff_year(row):
    """row year, or the END year of a period-average label like '1934-1938'."""
    return _eff_year(row.year, getattr(row, "period", None))

def assign(row):
    return M.assign(row.country, row.iso3c if isinstance(row.iso3c, str) else None,
                    getattr(row, "source", None), eff_year(row), fam_cache)

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
                "entity": r["source_label"], "iso_in_data": r.get("iso3") or None,
                "rows": int(float(r.get("observed_rows") or 0)),
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
            by_area[(r["area_code"], r["source_label"])].append(r)
        for (code, name), rs in by_area.items():
            out.append({
                "entity": name, "iso_in_data": rs[0].get("iso3") or None,
                "rows": int(float(rs[0].get("observed_rows") or 0)),
                "years": f"{min(r['year_start'] for r in rs)}-{max(r['year_end'] for r in rs)}",
                "sources": ["faostat"], "items_sample": [],
                "finding_type": "coverage_gap",
                "resolved_family": sorted({r["polity_code"] for r in rs}),
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
                    "entity": r["source_label"], "iso_in_data": r.get("iso3") or None,
                    "rows": int(float(r.get("observed_rows") or 0)),
                    "years": f"{r['year_start']}-{r['year_end']}",
                    "sources": ["faostat"], "items_sample": [],
                    "finding_type": "coverage_gap",
                    "note": "faostat-era-matching: " + basis,
                })
    return out
_fao_findings = _faostat_era_findings()
print(f"Stage 1b: +{len(_fao_findings)} FAOSTAT-era findings (faostat-era-matching state)")
findings.extend(_fao_findings)

# ---------- Stage 2: triage + report (ledger-gated, evidence-hash aware) ----------
# A banked unit (status correct/fixed) is skipped ONLY while the ledger's
# evidence_hash matches the unit's CURRENT evidence (all findings for the key:
# types, row counts, year spans, sources). Mismatch OR missing hash -> the
# unit reopens (findings resurface, noted) until re-banked WITH the hash:
# every finding carries its evidence_hash so the Cleanup phase can copy it
# into review_ledger.csv when banking.
def _ev_hash(fs):
    ev = sorted((f["finding_type"], f["rows"], f.get("years") or "",
                 ",".join(f.get("sources") or [])) for f in fs)
    return hashlib.sha256(json.dumps(ev, sort_keys=True).encode()).hexdigest()[:16]

# WHEP_LEDGER_BACKFILL=1: bootstrap mode — banked rows with an EMPTY hash get the
# unit's current hash written into the ledger (and stay skipped) instead of
# reopening. Only for trusted states (e.g. rows banked before hashing existed,
# right after their review); default is reopen, so stale bankings never hide.
_bootstrap = bool(os.environ.get("WHEP_LEDGER_BACKFILL"))
_before = len(findings)
_by_key = defaultdict(list)
for f in findings: _by_key[f["entity"].strip().lower()].append(f)
_keep, _reopened, _backfilled = [], 0, 0
for _key, _fs in _by_key.items():
    _h = _ev_hash(_fs)
    for f in _fs: f["evidence_hash"] = _h           # for ledger banking on resolve
    _row = banked.get(_key)
    if _row is None:
        _keep.extend(_fs); continue
    _old = (_row.get("evidence_hash") or "").strip()
    if _old == _h:
        continue                                    # banked + evidence unchanged -> skip
    if _bootstrap and not _old:
        _row["evidence_hash"] = _h; _backfilled += 1; continue
    _reopened += 1
    for f in _fs:
        f["note"] = ((f.get("note") or "") + " [reopened: evidence changed since banked "
                     f"(ledger last_run {_row.get('last_run') or 'n/a'})]").strip()
    _keep.extend(_fs)
findings = _keep
if _before != len(findings) or _reopened or _backfilled:
    print(f"  ledger: skipped {_before-len(findings)} findings already resolved in prior runs"
          + (f"; backfilled {_backfilled} evidence hashes (WHEP_LEDGER_BACKFILL)" if _backfilled else "")
          + (f"; REOPENED {_reopened} units (evidence changed or hash missing)" if _reopened else ""))
if _backfilled:
    _rows = list(csv.DictReader(open(LEDGER)))
    for r in _rows:
        b = banked.get((r.get("key") or "").strip().lower())
        if b is not None and b.get("evidence_hash"): r["evidence_hash"] = b["evidence_hash"]
    with open(LEDGER, "w", newline="") as _fh:
        _w = csv.DictWriter(_fh, fieldnames=list(_rows[0].keys()))
        _w.writeheader(); _w.writerows(_rows)
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
