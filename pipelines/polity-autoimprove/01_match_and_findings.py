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
from matchlib import Matcher, norm, toks, eff_year as _eff_year, covers as _year_covers
import extdata
from atomic import write_csv_atomic

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

# OCR SPELLING CORRECTIONS (issue 552). A dozen fao1952 labels are misreadings of a label the
# same source also prints correctly -- `Afghaniscan`, `Crechoslovakia`, `Madagascar 4`. Applied
# as a RENAME rather than as aliases, deliberately: `Czechoslovakia` routes per year across
# three F51 periods, so an alias would have to hard-code a span that the year-resolution
# machinery below already gets right. Correcting the spelling defers that decision instead of
# duplicating it. The corrected cells are disjoint from their correctly-spelled sibling's on
# (item, unit, year) in every pair, so this adds observations rather than double-counting them.
_ocr = extdata.load_ocr_corrections()
_before = work["country"].copy()
for (_src, _bad), _good in _ocr.items():
    _hit = (work["source"] == _src) & (work["country"] == _bad)
    work.loc[_hit, "country"] = _good
_n_ocr = int((work["country"] != _before).sum())
print(f"OCR label corrections applied: {_n_ocr:,} row(s) across {len(_ocr)} tabled spelling(s)")
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


# Span of every polity, for scoring how much of a period-average a candidate actually covers.
_SPAN = {r.polity_code: (int(r.start_year), int(r.end_year)) for r in pol.itertuples()
         if pd.notna(r.start_year) and pd.notna(r.end_year)}


def period_span(period):
    """(first, last) of a period-average label like '1934-1938', else None."""
    if not isinstance(period, str):
        return None
    yy = re.findall(r"\d{4}", period)
    if len(yy) < 2:
        return None
    a, b = int(yy[0]), int(yy[-1])
    return (a, b) if a <= b else None


def _covers(code, first, last):
    """How many years of [first, last] the polity is live for.

    `end_year` is EXCLUSIVE, and that reading is NOT re-implemented here as a bare `<`: it is
    matchlib.covers, the single place this repository's Python side decides whether a period
    contains a year (scripts/validate_year_semantics.py is why there is only one). The bare
    comparison this function used to hold was the same shape issue #131 came from, and it is
    also what made the two straddle measurements below disagree by 480 rows.
    """
    span = _SPAN.get(code)
    if not span:
        return 0
    s, e = span
    return sum(1 for y in range(first, last + 1) if _year_covers(s, e, y))


def period_straddle(code, period):
    """(years_before_start, years_after_end) of a period average that pokes outside its polity.

    Returns (0, 0) for a row that is not a period average, has no polity, or whose average fits
    entirely inside the polity's life. NOTHING IS REASSIGNED HERE -- this is the publish-the-fact
    option, so a consumer can filter by severity while the routing rule is still undecided.

    WHAT A STRADDLE IS. A yearbook prints "average 1934-1938" as one number. `assign()` below
    routes it to whichever candidate is live for the MOST of those five years (#383). That can
    still leave years of the averaged window outside the polity's life, at a founding or a
    dissolution: the Union of South Africa was founded in 1910 and IIA prints a 1909-1913
    average, so one of the five years predates the polity that gets the row. That is a property
    of the source, not a mistake by the matcher, which is why it is PUBLISHED rather than fixed.

    THE COUNT DEPENDS ON THE end_year CONVENTION, AND ONLY ONE OF THE TWO IS THIS REPO'S.
    Measured 2026-08-31 on 9,237 routed period-average rows:

        end_year EXCLUSIVE (matchlib.covers, this repo)      641 rows over 46 (polity, period)
        end_year read as inclusive                           161 rows over 24
        period lands completely outside its polity, either      0

    The 480-row difference is not two answers to one question. Every one of those 480 rows has
    its period's LAST year equal to its polity's `end_year` and nothing else outside -- IND
    1934-1938 on IND-1914-1937, DEU 1934-1938 on DEU-1920-1938 -- and under this repo's
    convention that year belongs to the SUCCESSOR (IND-1937-1947, DEU-1938-1945). So the
    inclusive reading does not find fewer straddles, it silently credits the predecessor with a
    year it does not have. Issue #310's comment of 2026-08-31 reported 161/24; that is the
    inclusive number, and the exclusive one is what the matcher itself acts on.

    THE THREE CANDIDATE RULES, AND WHAT EACH WOULD MOVE. The owner has not chosen. Counts are
    over the 641 flagged rows, re-deriving each rule's answer through `M.assign` so aliases,
    family ranking and the transition-year tie-break apply as they do in production (the 161-row
    inclusive subset is given second, since that is the number the issue quotes):

      1. MOST YEARS OF THE PERIOD -- moves 0 rows (641) / 0 (161). Already in force: this IS
         what `assign()` does since #383, and re-derivation confirms the stored code equals the
         max-coverage choice on 641 of 641. Read STRICTLY, as "the polity must hold a strict
         MAJORITY", it moves 53 (641) / 52 (161) -- but for all 53 no reachable candidate holds
         a majority either, so it is a DROP rule, not a reassignment rule: 29 SBZ-1938-1949 and
         18 PAK-1937-1947 rows become unassigned, because the Soviet zone and Pakistan have no
         predecessor in their own family to hand a 1934-1938 average back to.

      2. PERIOD MIDPOINT -- moves 105 rows (641) / 57 (161), and 98 of the 105 land on NO
         polity at all. Only 7 move to another polity (6 AEF-1910-1960 -> COG-1906-1912, 1
         KEN-1907-1924 -> KEN-1902-1907). The 98 are labels routed by an applied alias whose
         year range does not reach the midpoint -- `Germany Berlin` and `Germany Western` in
         fao1952 resolve only from 1937, so asking for 1936 returns nothing. This is worse than
         the earlier measurement recorded in `assign()` suggested (219 better / 22 worse against
         the old end-year rule): a midpoint is a proxy for coverage, and where the proxy misses
         it does not degrade, it strands the row.

      3. FLAG AND LET CONSUMERS DECIDE -- moves 0 rows. Implemented here and in
         `state/period_straddles.csv`.

    So the decision is between accepting 641 flagged-but-routed rows, dropping 53, or stranding
    98. Two of the three candidates cost more rows than the straddle does.
    """
    span = period_span(period)
    pol_span = _SPAN.get(code)
    if span is None or pol_span is None:
        return (0, 0)
    first, last = span
    s, e = pol_span
    before = sum(1 for y in range(first, last + 1) if y < s)
    # "after" is every averaged year at or past the polity's death, and it is phrased as
    # `not matchlib.covers` rather than `y >= e` on purpose: `y >= e` is the bare comparison that
    # made the 480-row discrepancy above, and writing it here would put a second reading of
    # `end_year` in the same file as the first.
    after = sum(1 for y in range(first, last + 1) if y >= s and not _year_covers(s, e, y))
    return (before, after)


def assign(row):
    """Resolve a row to a polity.

    Dated rows are unchanged. For a PERIOD AVERAGE (`1934-1938`, no year), `eff_year` takes the
    period's END year, and that systematically routes a multi-year average to whichever polity was
    live in its FINAL year. Measured before this change: 560 rows landed on a polity live for a
    MINORITY of the years they average and 10 on a polity live for NONE of them -- a 1934-1938 German
    average on post-Anschluss DEU-1938-1945, and 64 rows on the WZO/SBZ occupation zones, which did
    not exist until 1945.

    So for a period average, try every year in the span and keep the candidate that is live for the
    most of it. Two details make this safe rather than merely better:

      * years are tried from the END BACKWARDS, and a challenger must be STRICTLY better, so the
        end-year answer wins every tie. Whenever coverage is equal the old assignment is preserved
        exactly, and no row can regress.
      * the choice is made by re-calling M.assign with a different year, never by picking a polity
        directly, so aliases, family ranking and the transition-year tie-break all still apply.

    The period midpoint was the obvious alternative and was rejected on measurement: it improves 219
    rows but sends 22 to a polity covering LESS of their period, because a midpoint is only a proxy
    for coverage.
    """
    iso = row.iso3c if isinstance(row.iso3c, str) else None
    src = getattr(row, "source", None)
    span = period_span(getattr(row, "period", None)) if pd.isna(row.year) else None
    if span is None:
        return M.assign(row.country, iso, src, eff_year(row), fam_cache)

    first, last = span
    best = None
    for y in range(last, first - 1, -1):
        got = M.assign(row.country, iso, src, y, fam_cache)
        if got[0] is None:
            continue
        cov = _covers(got[0], first, last)
        if best is None or cov > best[0]:
            best = (cov, got)
    if best is None:
        return M.assign(row.country, iso, src, eff_year(row), fam_cache)
    return best[1]

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
    # Atomic (issue 431). This block READS the ledger, edits it in memory and writes it back over
    # itself, so a truncating write that dies part-way loses the file rather than corrupting it.
    if _rows:
        write_csv_atomic(LEDGER, list(_rows[0].keys()), _rows)
findings.sort(key=lambda f: (-f["rows"]))
for ft in ("name_unresolved","coverage_gap","data_error","other"):
    bucket=[f for f in findings if f["finding_type"]==ft]
    print(f"  {ft}: {len(bucket)} distinct entities, {sum(f['rows'] for f in bucket):,} rows")

# ORPHAN-CODE GUARD (issue 17, the #244 pattern moved upstream). Stage 04 already refuses to
# write territory_basis.csv from a parquet naming codes the database does not contain -- but it
# is the CONSUMER, so the bad parquet gets authored here and only complained about two stages
# later. Most of what this file emits is filtered against `valid_codes` on the way through, so
# the route an orphan can still take is an APPLIED ALIAS whose target has since been re-spanned
# or retired: matchlib drops an alias with an unknown target, but a target that exists and is
# `retired`/`superseded` resolves and routes rows to a row nothing may point at.
extdata.refuse_orphan_codes(
    work[work.whep_code.notna()].groupby("whep_code").size().to_dict(),
    what="matched_rows.parquet",
    fix=("check the alias registry for a stale target:\n"
         "    python3 scripts/validate_aliases.py\n"
         "  then re-run this stage."),
)

# ---- PERIOD-AVERAGE STRADDLES (issue 310) --------------------------------------------------
# The flag rides on matched_rows.parquet rather than in a table of its own, because every
# consumer of a period-average row already reads that file and none of them can currently tell a
# 1934-1938 average that fits inside its polity from one that does not. `period_straddles.csv`
# beside it is the WORKLIST -- one row per (polity, period) -- not a second copy of the data.
# See period_straddle() for the three candidate routing rules and what each would move.
#
# Zero, not null, where the question does not apply (a dated row, or an unrouted one). A consumer
# separates "no straddle" from "not a period average" with the columns it already has -- `year`
# is non-null for exactly the rows this cannot speak about -- and a nullable Int64 here would
# change the dtype of a column 20-odd downstream tools read positionally-in-spirit.
work["period_years_before_start"] = 0
work["period_years_after_end"] = 0
_pm = work.year.isna() & work.period.notna() & work.whep_code.notna()
if _pm.any():
    _ovh = {(c, p): period_straddle(c, p)
            for c, p in work.loc[_pm, ["whep_code", "period"]].drop_duplicates().itertuples(index=False)}
    _pk = list(zip(work.loc[_pm, "whep_code"], work.loc[_pm, "period"]))
    work.loc[_pm, "period_years_before_start"] = [_ovh[k][0] for k in _pk]
    work.loc[_pm, "period_years_after_end"] = [_ovh[k][1] for k in _pk]
work["period_years_before_start"] = work["period_years_before_start"].astype("int64")
work["period_years_after_end"] = work["period_years_after_end"].astype("int64")
work["period_straddles_polity_span"] = ((work.period_years_before_start > 0)
                                        | (work.period_years_after_end > 0))

_str = work[work.period_straddles_polity_span]
_rows = []
for (_code, _period), _g in _str.groupby(["whep_code", "period"]):
    _b, _a = period_straddle(_code, _period)
    _s, _e = _SPAN[_code]
    _f, _l = period_span(_period)
    _srcs = sorted(_g.source.dropna().unique().tolist())
    _rows.append({
        "polity_code": _code, "start_year": _s, "end_year": _e, "period": _period,
        "period_first": _f, "period_last": _l,
        "years_before_start": _b, "years_after_end": _a,
        "direction": "both" if _b and _a else ("before" if _b else "after"),
        "years_covered": _covers(_code, _f, _l), "period_years": _l - _f + 1,
        # yes == the whole overhang is the single year equal to `end_year`, which under this
        # repo's EXCLUSIVE reading belongs to the successor. These are the pairs that vanish if
        # someone measures with an inclusive `end_year`; 480 of the 641 rows sit here, so the
        # column is what makes the two numbers in period_straddle()'s docstring reconcilable
        # from the table instead of on trust.
        "end_year_boundary_only": "yes" if (_b == 0 and _a == 1 and _l == _e) else "no",
        "observed_rows": int(len(_g)), "sources": ";".join(_srcs), "n_sources": len(_srcs),
    })
_rows.sort(key=lambda r: (-r["observed_rows"], r["polity_code"], r["period"]))
# Atomic, and via the shared helper rather than to_csv: this is a tracked file, and a run that
# dies between the truncate and the last row would leave a half-written worklist that reads as a
# shorter problem than it is (issue 431).
write_csv_atomic(f"{OUT}/period_straddles.csv",
                 ["polity_code", "start_year", "end_year", "period", "period_first", "period_last",
                  "years_before_start", "years_after_end", "direction", "years_covered",
                  "period_years", "end_year_boundary_only", "observed_rows", "sources",
                  "n_sources"],
                 _rows)
print(f"period averages: {int(_pm.sum()):,} routed; {len(_str):,} straddle their polity's span "
      f"across {len(_rows)} (polity, period) pair(s) -> state/period_straddles.csv")

json.dump({"summary": {
            "total_rows": int(len(work)),
            "matched_rows": int(matched.sum()),
            "match_pct": round(100*matched.mean(),1),
            "unmatched_rows": int((~matched).sum()),
          },
          "findings": findings},
          open(f"{OUT}/findings.json","w"), indent=1)
# `period` is carried even though nothing in THIS stage needs it downstream: 5.12% of layer B
# (9,865 rows -- fao1952 3,702, iia 6,163) has a null `year` and carries its year only in a
# period-average label like `1909-1913`. This stage already recovers those itself (eff_year(),
# period_span(), and the coverage-scoring at line 131), but it used to DROP the column here, so
# 00_intake.py could not be given `--period-col` -- the option exists and matchlib.eff_year was
# written for exactly this -- and every period row reached it as an undatable year=NA row.
# The consequence was not misrouting (measured: 9,210 of 9,210 routed period rows land in a polity
# whose life overlaps their period label, and routing is 98.7% vs 99.7% for dated rows). It was that
# a label/candidate group whose ONLY overlapping rows are period rows got years_observed
# "None-None", and 12_triage_assertions.py:149 raises ValueError on that -- so the triage queue
# could not be regenerated AT ALL, which is why it drifted (issue 434).
# `indicator` carried for the same reason as `period`: needed downstream and dropped here. Its
# MEANING IS SOURCE-DEPENDENT, which matters more than its presence -- fao1952 uses it for the
# MEASURE (13 values: crops:area, population:population total, ...) while mitchell uses it for
# PROVENANCE (152 values: `page_17_table_1`, `copia de page_17_table_1`). A consumer must decide
# per source; see 25_same_polity_overlaps.py, where keying on it for mitchell would separate the
# very duplicates the table exists to find.
# The three `period_*` columns are APPENDED, after `match_method`, so nothing that reads this
# file by position shifts. They answer, per row, the question `period` alone cannot: whether the
# averaged window pokes outside the polity it was routed to, and by how many years at which end.
work[["source","country","iso3c","year","period","item","indicator","value","unit","whep_code","match_method",
      "period_straddles_polity_span","period_years_before_start","period_years_after_end"]] \
    .to_parquet(f"{OUT}/matched_rows.parquet", index=False)

# coverage by source after
cov = work.groupby("source").apply(lambda g: pd.Series({
        "rows": len(g), "matched": g.whep_code.notna().sum(),
        "pct": round(100*g.whep_code.notna().mean(),1)})).reset_index()
print("\n=== coverage by source (after Stage 0) ===")
print(cov.to_string(index=False))
print(f"\nwrote findings.json ({len(findings)} findings) + matched_rows.parquet")
