#!/usr/bin/env python3
"""Deterministic territorial-evidence pre-step: attach NUMERIC evidence to each
flagged polity so the audit doesn't rely on the agent's prior knowledge.

For each flagged EXISTING polity P:
  - staple_magnitudes: median reported value for key staples (the data's own scale)
  - contained_with_concurrent_data: WHEP polities whose polygon sits inside P's
    polygon AND report layer-B data in the same years (double-count / polygon-
    overstates-data signal, e.g. Korea+Taiwan inside the Japan-empire polygon).
"""
import geopandas as gpd, pandas as pd, json, warnings, os
from collections import defaultdict
warnings.filterwarnings("ignore")
REPO=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
H=os.path.join(REPO,"pipelines/polity-autoimprove/state")     # reads 01's matched_rows + writes territorial_flagged.json
GPKG=os.path.join(REPO,"data/geodata/polities_polygons.gpkg")
POLDB=os.path.join(REPO,"data/final/polities_database.csv")

m=pd.read_parquet(os.path.join(H,"matched_rows.parquet"))
m["v"]=pd.to_numeric(m["value"],errors="coerce")
mm=m[m.whep_code.notna()]
span={}; code2iso={}
pol=pd.read_csv(POLDB)
polmeta={r.polity_code:r for _,r in pol.iterrows()}
for _,r in pol.iterrows():
    span[r.polity_code]=(int(r.start_year),int(r.end_year))
    code2iso[r.polity_code]=str(r.iso3_code)

# --- BUILD the flag set (deterministic): existing matched polities that are
#     territorially sensitive = data-magnitude step-change vs a sibling period,
#     OR a README-documented known polygon/data extent mismatch. ---
KNOWN={"JPN-1895-1945","JPN-1945-1952","F228-1905-1917","ZAF-1828-2025","IND-1937-1947","IND-1947-1949"}
risk=set(); stepev=defaultdict(list)
for iso,fam in pol.groupby("iso3_code"):
    if not isinstance(iso,str) or fam.polity_code.nunique()<2: continue
    codes=fam.polity_code.tolist()
    sub=mm[mm.whep_code.isin(codes)]
    if sub.empty: continue
    for (item,src,unit),gg in sub.groupby([sub.item,sub.source,sub.unit.fillna("")]):
        med=gg.groupby("whep_code").v.median().dropna(); med=med[med>0]
        if len(med)<2: continue
        ratio=med.max()/med.min()
        if ratio>=1.6:
            hi,lo=med.idxmax(),med.idxmin()
            for c in (hi,lo):
                risk.add(c); stepev[c].append(f"{item}/{src}: {med[lo]:.0f}->{med[hi]:.0f} ({ratio:.1f}x) vs sibling period")
flagged=[]
for code in sorted(risk|KNOWN):
    if code not in polmeta: continue
    r=polmeta[code]; iso=code2iso.get(code)
    fam=pol[pol.iso3_code==iso].sort_values("start_year") if isinstance(iso,str) else pd.DataFrame()
    reasons=[]
    if code in risk: reasons.append("magnitude step-change vs sibling period")
    if code in KNOWN: reasons.append("README known polygon/data extent mismatch")
    flagged.append({"polity_code":code,"polity_name":r.polity_name,"kind":"existing",
        "period":f"{int(r.start_year)}-{int(r.end_year)}","polygon_source":str(r.get('polygon_source')),
        "polygon_feature_year":(int(r.polygon_feature_year) if pd.notna(r.get('polygon_feature_year')) else None),
        "polygon_area_km2":(float(r.polygon_area_km2) if pd.notna(r.get('polygon_area_km2')) else None),
        "n_data_rows":int((mm.whep_code==code).sum()),
        "family_periods":[f"{p.polity_code} {int(p.start_year)}-{int(p.end_year)}" for _,p in fam.iterrows()],
        "evidence":stepev.get(code,[])[:5],"flag_reasons":reasons})
# ledger gating: drop polities a prior run already resolved (status correct/fixed)
import csv as _csv
LEDGER=os.path.join(H,"review_ledger.csv"); resolved=set()
if os.path.exists(LEDGER):
    for r in _csv.DictReader(open(LEDGER)):
        if (r.get("status") or "").strip() in ("correct","fixed") and r.get("key"):
            resolved.add(r["key"].strip())
_b=len(flagged); flagged=[f for f in flagged if f["polity_code"] not in resolved]
print(f"flagged {len(flagged)} territorially-sensitive existing polities (magnitude-step + known)"
      + (f"; ledger skipped {_b-len(flagged)}" if _b!=len(flagged) else ""))

STAPLES=["rice","wheat","maize","cattle","sugar"]
def staples(code):
    g=mm[mm.whep_code==code]; out=[]
    for s in STAPLES:
        gg=g[g["item"].astype(str).str.contains(s,case=False,na=False) & g.unit.astype(str).str.contains("tonne",na=False)]
        v=gg.v.dropna()
        if len(v):
            u=str(gg.unit.mode().iloc[0]) if len(gg.unit.mode()) else "tonnes"
            out.append(f"{s}={v.median():,.0f} {u} (n{len(v)})")
    return out
def yrs(code):
    y=mm[mm.whep_code==code].year.dropna()
    return (int(y.min()),int(y.max())) if len(y) else None
def has_data(code): return int((mm.whep_code==code).sum())

print("loading polygons...")
g=gpd.read_file(GPKG, layer="polities")
g=g.dissolve(by="polity_code", as_index=False)
g["geometry"]=g.geometry.make_valid()
g=g.to_crs(6933)
g["area"]=g.geometry.area
gidx={r.polity_code:r.geometry for _,r in g.iterrows()}
areaof={r.polity_code:r.area for _,r in g.iterrows()}

ex=[f for f in flagged if f["kind"]=="existing" and f["polity_code"] in gidx]
print(f"computing containment for {len(ex)} flagged existing polities with polygons...")
gsindex=g.sindex
for f in flagged:
    if f["kind"]!="existing": continue
    code=f["polity_code"]
    f.pop("contained_with_concurrent_data",None)      # idempotent: clear stale evidence
    f["flag_reasons"]=[r for r in f.get("flag_reasons",[]) if "spatially contains" not in r]
    f["staple_magnitudes"]=staples(code)
    if code not in gidx: continue
    P=gidx[code]; Pper=span.get(code,(0,9999))
    # candidate intersectors via spatial index
    cand=g.iloc[list(gsindex.query(P, predicate="intersects"))]
    contained=[]
    for _,q in cand.iterrows():
        qc=q.polity_code
        if qc==code: continue
        pre=lambda c: c.rsplit("-",2)[0]              # ISO-START-END -> entity prefix
        if pre(qc)==pre(code): continue               # skip same-entity temporal siblings (same territory over time, not a sub-component)
        try: inter=P.intersection(q.geometry).area
        except: continue
        if areaof[qc]<=0: continue
        ratio=inter/areaof[qc]
        if ratio<0.7: continue                      # q mostly inside P
        qper=span.get(qc,(0,9999))
        if not (qper[0]<=Pper[1] and qper[1]>=Pper[0]): continue   # period overlap
        n=has_data(qc)
        if n==0: continue                            # only flag if it reports concurrently
        contained.append({"code":qc,"name":q.polity_name,"contain_ratio":round(ratio,2),
                          "n_data_rows":n,"data_years":yrs(qc),"staples":staples(qc)})
    if contained:
        contained.sort(key=lambda x:-x["n_data_rows"])
        f["contained_with_concurrent_data"]=contained[:6]
        f.setdefault("flag_reasons",[]).append(f"polygon spatially contains {len(contained)} polity(ies) that report data concurrently -> aggregate-vs-core territorial ambiguity")

json.dump(flagged, open(H+"/territorial_flagged.json","w"), indent=1)
# report the aggregate-overlap cases (the ones with real double-count evidence)
agg=[f for f in flagged if f.get("contained_with_concurrent_data")]
print(f"\n{len(agg)} flagged polities have contained-with-concurrent-data evidence:")
for f in sorted(agg,key=lambda x:-len(x["contained_with_concurrent_data"]))[:12]:
    comps=", ".join(f"{c['code']}({c['n_data_rows']}r)" for c in f["contained_with_concurrent_data"])
    print(f"  {f['polity_code']:16s} own[{'; '.join(f.get('staple_magnitudes',[]))[:40]}]  contains: {comps[:80]}")
