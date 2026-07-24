#!/usr/bin/env python3
"""Source-agnostic intake: any table with country/area labels + years -> assertions.

This is the entry point for onboarding a NEW dataset (or re-deriving the
existing layer-B universe). It runs the deterministic pass (matchlib: alias ->
iso -> name routing + year containment) and emits one EVIDENCE BUNDLE per
distinct assertion:

    (label, source, year_segment) -> candidate polity

The candidate is UNVERIFIED routing. Verification — "does the source's
reporting territory under this label equal the candidate polity's territory?"
— is agent work (verify_assertions.workflow.js), done once per assertion and
banked in review_ledger.csv with an evidence hash.

Usage:
  python3 pipelines/polity-autoimprove/00_intake.py \
    --input data.parquet --label-col country --year-col year \
    [--iso-col iso3c] [--value-col value] [--item-col item] [--unit-col unit] \
    [--period-col period] [--aggregate-col is_aggregate] [--prior-code-col polity_code] \
    (--source-col source | --source-tag mydata) \
    [--out pipelines/polity-autoimprove/state/assertions.json]

Ledger-aware: assertions whose key (or legacy bare-label key) is banked
correct/fixed with a matching evidence_hash get status "banked"; everything
else is "pending" for the verification workflow.
"""
import pandas as pd, numpy as np, json, csv, os, sys, argparse, hashlib
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from matchlib import Matcher, norm, eff_year

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(REPO, "pipelines/polity-autoimprove/state")
POLDB = os.path.join(REPO, "data/final/polities_database.csv")
COMMON_NAMES = os.environ.get("WHEP_COMMON_NAMES",
    "/home/usuario/Nextcloud/WHEP_ERC 2025/Sources/datasets/unclassified_datasets/Other polities/data/whep-source/common_names.csv")

ap = argparse.ArgumentParser()
ap.add_argument("--input", required=True)
ap.add_argument("--label-col", required=True)
ap.add_argument("--year-col", required=True)
ap.add_argument("--iso-col")
ap.add_argument("--value-col")
ap.add_argument("--item-col")
ap.add_argument("--unit-col")
ap.add_argument("--period-col")
ap.add_argument("--aggregate-col", help="boolean column: True rows are aggregates, dropped")
ap.add_argument("--prior-code-col", help="column with prior polity codes; trusted only if a valid period code")
ap.add_argument("--source-col", help="column naming the source per row")
ap.add_argument("--source-tag", help="fixed source tag when the table is one source")
ap.add_argument("--out", default=os.path.join(OUT_DIR, "assertions.json"))
A = ap.parse_args()
if not A.source_col and not A.source_tag:
    ap.error("one of --source-col / --source-tag is required")

# ---------- load ----------
df = pd.read_parquet(A.input) if A.input.endswith(".parquet") else pd.read_csv(A.input)
n_raw = len(df)
if A.aggregate_col:
    df = df[~df[A.aggregate_col].astype(bool)]
w = pd.DataFrame({
    "label": df[A.label_col],
    "year":  pd.to_numeric(df[A.year_col], errors="coerce"),
    "iso":   df[A.iso_col] if A.iso_col else None,
    "source": df[A.source_col] if A.source_col else A.source_tag,
    "item":  df[A.item_col] if A.item_col else None,
    "value": pd.to_numeric(df[A.value_col], errors="coerce") if A.value_col else np.nan,
    "unit":  df[A.unit_col] if A.unit_col else None,
    "period": df[A.period_col] if A.period_col else None,
})
print(f"input: {n_raw:,} rows ({len(w):,} after aggregate filter)")

# ---------- deterministic pass ----------
M = Matcher(POLDB, applied_aliases_csv=os.path.join(OUT_DIR, "applied_aliases.csv"),
            common_names_csv=COMMON_NAMES)
prior = None
if A.prior_code_col:
    prior = df[A.prior_code_col].where(df[A.prior_code_col].isin(M.valid_codes))
    prior = prior.reindex(w.index)

fam_cache = {}
def _assign(row):
    y = eff_year(row.year, row.period)
    return M.assign(row.label, row.iso, row.source, y, fam_cache) + (y,)

res = w.apply(_assign, axis=1, result_type="expand")
res.columns = ["code", "status", "how", "eff_year"]
w = pd.concat([w, res], axis=1)
if prior is not None:
    trusted = prior.notna()
    w.loc[trusted, "code"] = prior[trusted]
    w.loc[trusted, "status"] = "matched"
    # keep the resolver's 'how' when it agrees; label pure prior-trust distinctly
    w.loc[trusted & (res["code"] != prior), "how"] = "prior"
matched = w.code.notna()
print(f"deterministic pass: {matched.sum():,}/{len(w):,} rows routed ({100*matched.mean():.1f}%)")

# ---------- ledger ----------
LEDGER = os.path.join(OUT_DIR, "review_ledger.csv")
banked = {}
if os.path.exists(LEDGER):
    for r in csv.DictReader(open(LEDGER)):
        if (r.get("status") or "").strip() in ("correct", "fixed") and r.get("key"):
            banked[r["key"].strip().lower()] = r

def _hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:16]

# ---------- assertions: one evidence bundle per (label, source, candidate) ----------
polmeta = {r.polity_code: r for _, r in M.pol.iterrows()}
def staples(grp, k=5):
    """median magnitude for the group's top-k items (the data's own scale)."""
    if grp.item.isna().all() or grp.value.isna().all(): return {}
    out = {}
    top = grp.item.value_counts().head(k).index
    for it in top:
        v = grp[grp.item == it].value.dropna()
        if not len(v): continue
        u = grp[grp.item == it].unit.dropna()
        u = str(u.mode().iloc[0]) if len(u) else ""
        out[str(it)] = f"median {v.median():,.0f} {u} (n={len(v)})".strip()
    return out

mm = w[matched]
assertions, by_label_src = [], defaultdict(list)
for (label, src, code), grp in mm.groupby(["label", "source", "code"]):
    yrs = grp.eff_year.dropna()
    y0, y1 = (int(yrs.min()), int(yrs.max())) if len(yrs) else (None, None)
    by_label_src[(label, src)].append((code, y0, y1))
for (label, src, code), grp in mm.groupby(["label", "source", "code"]):
    yrs = grp.eff_year.dropna()
    y0, y1 = (int(yrs.min()), int(yrs.max())) if len(yrs) else (None, None)
    key = f"{norm(label)}|{src}|{y0}-{y1}"
    pm = polmeta.get(code)
    ev = {
        "key": key, "label_raw": str(label), "source": str(src),
        "candidate": code,
        "route": sorted(grp.how.dropna().unique().tolist()),
        "rows": int(len(grp)), "years_observed": f"{y0}-{y1}",
        "n_distinct_years": int(yrs.nunique()),
        "iso_in_data": (sorted({str(i) for i in grp.iso.dropna().unique()}) or [None])[0],
        "items_sample": sorted({str(i) for i in grp.item.dropna().unique()})[:5],
        "staple_magnitudes": staples(grp),
        "neighbor_segments": {f"{a}-{b}": c for c, a, b in by_label_src[(label, src)] if c != code},
        "candidate_meta": None if pm is None else {
            "polity_name": pm.polity_name, "period": f"{pm.start_year}-{pm.end_year}",
            "polity_type": pm.polity_type,
            "area_km2": (None if pd.isna(pm.get("polygon_area_km2")) else float(pm.polygon_area_km2)),
            "polygon_status": pm.get("polygon_status"),
            "wiki": f"wiki/polities/{str(code).lower()}.md"},
    }
    ev["evidence_hash"] = _hash([ev["candidate"], ev["rows"], ev["years_observed"],
                                 ev["items_sample"], ev["staple_magnitudes"]])
    # ledger: full assertion key first, then legacy bare-label key
    row = banked.get(key.lower()) or banked.get(norm(label))
    if row is not None and (row.get("evidence_hash") or "").strip() == ev["evidence_hash"]:
        ev["status"] = "banked"
    elif row is not None and row is banked.get(norm(label)) and not (row.get("evidence_hash") or "").strip():
        # legacy bare-label banking without a hash: treat as banked for label-level
        # verdicts (pre-assertion era); assertion-level verification will supersede it
        ev["status"] = "banked_legacy"
    else:
        ev["status"] = "pending" if row is None else "reopened"
    assertions.append(ev)

# ---------- unresolved (findings-shaped, same as 01) ----------
unresolved = []
un = w[~matched]
for (label, iso, how), grp in un.groupby([un.label, un.iso.fillna(""), un.status]):
    yrs = grp.eff_year.dropna()
    unresolved.append({
        "entity": str(label), "iso_in_data": iso or None, "reason": how,
        "rows": int(len(grp)),
        "years": (f"{int(yrs.min())}-{int(yrs.max())}" if len(yrs) else None),
        "sources": sorted({str(s) for s in grp.source.unique()}),
    })

assertions.sort(key=lambda a: -a["rows"])
counts = pd.Series([a["status"] for a in assertions]).value_counts().to_dict() if assertions else {}
out = {
    "summary": {
        "input": A.input, "rows": int(len(w)), "rows_routed": int(matched.sum()),
        "route_pct": round(100 * matched.mean(), 1),
        "assertions": len(assertions), "by_status": counts,
        "unresolved_labels": len(unresolved),
    },
    "assertions": assertions,
    "unresolved": unresolved,
}
json.dump(out, open(A.out, "w"), indent=1, default=str)
print(f"assertions: {len(assertions)} ({counts}); unresolved labels: {len(unresolved)}")
print(f"wrote {A.out}")
