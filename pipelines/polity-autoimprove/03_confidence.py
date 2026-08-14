#!/usr/bin/env python3
"""Stage 3 (deterministic): assign a CONFIDENCE CLASS to every match assertion
(label, source, polity, year-range), so we can triage — auto-trust the safe
buckets (after a sample audit), send only the uncertain ones to agents.

A confidence class is NOT a correctness verdict — it records which independent
signals AGREED (iso, name, alias) and which risk flags fired (iso-name mismatch,
boundary year, territorially-flagged polity). Reproducible, free.
"""
import pandas as pd, numpy as np, json, re, unicodedata, os
from collections import defaultdict
REPO=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
H=os.path.join(REPO,"pipelines/polity-autoimprove/state")
POLDB=os.path.join(REPO,"data/final/polities_database.csv")

def norm(s):
    if s is None or (isinstance(s,float) and np.isnan(s)): return ""
    s=unicodedata.normalize("NFKD",str(s).strip().lower()).encode("ascii","ignore").decode()
    s=re.sub(r"\s*\(.*?\)\s*"," ",s); s=re.sub(r"[^a-z0-9 ]"," ",s)
    return re.sub(r"\s+"," ",s).strip()
def toks(s): return {t for t in norm(s).split() if len(t)>=3}

pol=pd.read_csv(POLDB)
P={r.polity_code:{"iso":str(r.iso3_code).upper(),"name":r.polity_name,
                  "toks":toks(r.polity_name),"s":int(r.start_year),"e":int(r.end_year)}
   for _,r in pol.iterrows()}
terr=set()
tf=os.path.join(H,"territorial_flagged.json")
if os.path.exists(tf): terr={f["polity_code"] for f in json.load(open(tf))}

m=pd.read_parquet(os.path.join(H,"matched_rows.parquet"))
mm=m[m.whep_code.notna()].copy()
mm["lab"]=mm.country.astype(str).str.lower().str.strip()
mm["y"]=pd.to_numeric(mm.year,errors="coerce")

rows=[]
for (lab,src,code),g in mm.groupby(["lab","source","whep_code"]):
    if code not in P: continue
    p=P[code]; meth=g.match_method.mode().iloc[0]
    isos={str(x).upper() for x in g.iso3c.dropna().unique()}
    iso_present=bool(isos)
    iso_ok = iso_present and p["iso"] in isos
    iso_conflict = iso_present and not iso_ok
    name_ok = (meth in ("name","tokenset","alias","applied_alias")) or bool(toks(lab) & p["toks"])
    y=g.y.dropna(); ymin,ymax=(int(y.min()),int(y.max())) if len(y) else (None,None)
    # base class
    if meth=="applied_alias":
        cls="asserted_alias"                                  # our own rule (trust = its recorded basis/confidence)
    elif iso_ok and name_ok:
        cls="safe_iso_name"                                   # two signals agree
    elif name_ok and not iso_present:
        cls="ok_name_only"                                    # exact/alias name, no iso to cross-check
    elif iso_ok and not name_ok:
        cls="suspect_iso_only"                                # iso matches, name doesn't (classic silent FP)
    elif iso_conflict:
        cls="suspect_iso_conflict"                            # name matched but data iso disagrees
    else:
        cls="review_weak"
    flags=[]
    if code in terr: flags.append("territory_flag")   # polity has a known territorial/extent question
    rows.append([lab,src,code,ymin,ymax,int(len(g)),meth,iso_ok,name_ok,cls,";".join(flags)])

# Column names are the repo-wide vocabulary (issue 95): the label is `source_label`,
# the row count `observed_rows`. `year_min`/`year_max` deliberately stay: they are the
# span the data was OBSERVED over, not the span a rule routes (`year_start`/`year_end`),
# and collapsing the two would make an alias registry and an observation log look joinable.
out=pd.DataFrame(rows,columns=["source_label","source","polity_code","year_min","year_max",
        "observed_rows","method","iso_ok","name_ok","confidence_class","risk_flags"])
out.to_csv(os.path.join(H,"match_confidence.csv"),index=False)

SAFE={"safe_iso_name","ok_name_only","asserted_alias"}
print(f"assertions: {len(out)} | rows: {out.observed_rows.sum():,}\n")
print("by confidence_class (assertions | rows):")
for c,g in out.groupby("confidence_class").agg(n=("source_label","size"),rows=("observed_rows","sum")).sort_values("rows",ascending=False).iterrows():
    print(f"  {c:22s} {int(g.n):>5} assertions  {int(g.rows):>9,} rows  [{'SAFE' if c in SAFE else 'REVIEW'}]")
flagged=out[out.risk_flags!=""]
print(f"\nwith risk flags (boundary / territory_flag): {len(flagged)} assertions, {flagged.observed_rows.sum():,} rows")
review=out[(~out.confidence_class.isin(SAFE)) | (out.risk_flags!="")]
print(f"\n=> REVIEW set (suspect classes OR risk-flagged): {len(review)} assertions, {review.observed_rows.sum():,} rows")
print(f"=> SAFE & unflagged (sample-audit only):           {len(out)-len(review)} assertions")
