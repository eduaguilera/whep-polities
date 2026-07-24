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

# --- intra-span polygon-vintage drift: a single polygon (one vintage) cannot
#     represent a long-lived polity whose borders changed within its span.
#     Flag polities serving data far from their polygon's vintage year. ---
SPAN_MIN, TOL = 25, 15
have={f["polity_code"] for f in flagged}
for code,grp in mm.groupby("whep_code"):
    if code not in polmeta or code in have: continue
    r=polmeta[code]
    fy=r.get("polygon_feature_year")
    if pd.isna(fy): continue
    fy=int(fy); pspan=int(r.end_year)-int(r.start_year)
    iso=code2iso.get(code)
    # only single-record families: multi-period isos (USA, Italy...) already route data to
    # the period whose polygon vintage fits; a lone long-span record (e.g. CAP-1800-1910) cannot.
    nper=int((pol.iso3_code==iso).sum()) if isinstance(iso,str) and iso not in ("nan","","NA") else 1
    if nper>1: continue
    y=pd.to_numeric(grp.year,errors="coerce").dropna()
    if not len(y): continue
    dmin,dmax=int(y.min()),int(y.max())
    drift=max(fy-dmin, dmax-fy)
    if pspan>=SPAN_MIN and drift>=TOL:
        fam=pol[pol.iso3_code==iso].sort_values("start_year") if isinstance(iso,str) else pd.DataFrame()
        flagged.append({"polity_code":code,"polity_name":r.polity_name,"kind":"existing",
            "period":f"{int(r.start_year)}-{int(r.end_year)}","polygon_source":str(r.get('polygon_source')),
            "polygon_feature_year":fy,"polygon_area_km2":(float(r.polygon_area_km2) if pd.notna(r.get('polygon_area_km2')) else None),
            "n_data_rows":int(len(grp)),
            "family_periods":[f"{p.polity_code} {int(p.start_year)}-{int(p.end_year)}" for _,p in fam.iterrows()],
            "evidence":[f"polygon vintage {fy} but data spans {dmin}-{dmax} (drift {drift}y over a {pspan}y polity span) -> the single polygon cannot represent border changes within the span"],
            "flag_reasons":["polygon_vintage_drift: do NOT assume territorial stasis across the polygon vintage"]})
print(f"  + {len([f for f in flagged if any('vintage_drift' in r for r in f['flag_reasons'])])} polygon-vintage-drift flags")

# ledger gating: drop polities a prior run already resolved (status correct/fixed)
# — but ONLY while the flag evidence is unchanged: skip requires the ledger's
# evidence_hash to match the hash of the polity's CURRENT flags; mismatch or
# missing hash reopens the polity. Every flag carries its evidence_hash so the
# Cleanup phase can copy it into review_ledger.csv when banking.
import csv as _csv, hashlib as _hashlib
LEDGER=os.path.join(H,"review_ledger.csv"); _banked={}
if os.path.exists(LEDGER):
    for r in _csv.DictReader(open(LEDGER)):
        if (r.get("status") or "").strip() in ("correct","fixed") and r.get("key"):
            _banked[r["key"].strip()]=r
def _fhash(fs):
    ev=sorted((tuple(f.get("flag_reasons") or []), tuple(f.get("evidence") or [])) for f in fs)
    return _hashlib.sha256(json.dumps(ev,sort_keys=True).encode()).hexdigest()[:16]
# WHEP_LEDGER_BACKFILL=1: bootstrap mode — see 01_match_and_findings.py (same rule).
_bootstrap=bool(os.environ.get("WHEP_LEDGER_BACKFILL"))
_b=len(flagged); _byc={}
for f in flagged: _byc.setdefault(f["polity_code"],[]).append(f)
_keep=[]; _re=0; _bf=0
for _code,_fs in _byc.items():
    _h=_fhash(_fs)
    for f in _fs: f["evidence_hash"]=_h                 # for ledger banking on resolve
    _row=_banked.get(_code)
    if _row is None: _keep.extend(_fs); continue
    _old=(_row.get("evidence_hash") or "").strip()
    if _old==_h: continue                               # banked + unchanged -> skip
    if _bootstrap and not _old:
        _row["evidence_hash"]=_h; _bf+=1; continue
    _re+=1
    for f in _fs: f["flag_reasons"]=list(f.get("flag_reasons") or [])+["reopened: flag evidence changed since banked (or banked without hash)"]
    _keep.extend(_fs)
flagged=_keep
if _bf:
    _rows=list(_csv.DictReader(open(LEDGER)))
    for r in _rows:
        b=_banked.get((r.get("key") or "").strip())
        if b is not None and b.get("evidence_hash"): r["evidence_hash"]=b["evidence_hash"]
    with open(LEDGER,"w",newline="") as _fh:
        _w=_csv.DictWriter(_fh,fieldnames=list(_rows[0].keys())); _w.writeheader(); _w.writerows(_rows)
print(f"flagged {len(flagged)} territorially-sensitive existing polities (magnitude-step + known)"
      + (f"; ledger skipped {_b-len(flagged)}" if _b!=len(flagged) else "")
      + (f"; backfilled {_bf} evidence hashes (WHEP_LEDGER_BACKFILL)" if _bf else "")
      + (f"; REOPENED {_re} polities (evidence changed or hash missing)" if _re else ""))

STAPLES=["rice","wheat","maize","cattle","sugar"]
def staples(code):
    g=mm[mm.whep_code==code]; out=[]
    for s in STAPLES:
        gg=g[g["item"].astype(str).str.contains(s,case=False,na=False) & g.unit.astype(str).str.contains("tonne",na=False)]
        v=gg.v.dropna()
        if len(v):
            u=str(gg.unit.mode().iloc[0]) if len(gg.unit.mode()) else "tonnes"
            med=v.median()
            # scale "1000 tonnes" / "1000 metric tons" units so the displayed value is in tonnes
            if "1000" in u:
                med=med*1000
                u=u.replace("1000 ","").replace("1,000 ","").strip()
            out.append(f"{s}={med:,.0f} {u} (n{len(v)})")
    return out
def yrs(code):
    y=mm[mm.whep_code==code].year.dropna()
    return (int(y.min()),int(y.max())) if len(y) else None
def has_data(code): return int((mm.whep_code==code).sum())

# IIA source-footnote evidence: territorial/boundary notes (state/iia_territorial_notes.csv)
# attached to the polities whose matched IIA data labels carry them.
NOTES=os.path.join(H,"iia_territorial_notes.csv"); notes_by_country={}
if os.path.exists(NOTES):
    for r in _csv.DictReader(open(NOTES)):
        c=(r.get("country") or "").strip().lower()
        if c: notes_by_country.setdefault(c,[]).append(
            f"{r['note']} [{str(r.get('year_min') or '')}-{str(r.get('year_max') or '')}, {r.get('n_rows')}r]")
# bridge note country-labels -> ISO (matched_rows carries lowercase-iso whep_codes for core
# rows, so join on ISO not code), then attach to flagged polities by their iso3_code.
lab2iso={}
for lbl,gg in mm.groupby(mm.country.astype(str).str.lower()):
    isos=gg.iso3c.dropna()
    if len(isos): lab2iso[lbl]=str(isos.mode().iloc[0]).upper()
notes_by_iso=defaultdict(list)
for lbl,ns in notes_by_country.items():
    iso=lab2iso.get(lbl)
    if iso:
        for n in ns: notes_by_iso[iso].append(f"'{lbl}': {n}")
def source_notes(code):
    iso=str(code2iso.get(code,"")).upper()
    return notes_by_iso.get(iso,[])[:8]

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
    sn=source_notes(code)
    if sn: f["source_notes"]=sn                        # IIA footnote evidence (boundary/territorial scope)
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
