#!/usr/bin/env python3
"""Decide, from the data, which reporting units already have a polity and which need one.

THE POINT. Previously a human decided "this country needs prefectures" and then configured a
generator per country. That does not scale past the country you are looking at, and it learns
nothing from the data. This harness takes a table of reporting units and finds out: for each unit it
assembles deterministic evidence from this repository, asks for one schema-valid verdict, and records
it. "We need provinces here" becomes an OUTPUT.

WHAT IS DETERMINISTIC AND WHAT IS JUDGEMENT, kept strictly apart:

  deterministic (this module)   the unit's coverage; candidate polities by iso3 and by normalised
                                name; whether a boundary feature exists; whether the identifier
                                carries a residual marker
  judgement (the agent)         whether a candidate IS this reporting territory, whether the unit is
                                a territory at all, and what span a new row should carry

The harness never pre-decides. A unit whose id ends `-NATIONAL` is presented WITH that observation
and the national polity as a candidate, and the verdict is the agent's -- because the same shape
("this label is really the country") is sometimes a bucket and sometimes a legitimate whole-territory
report, and hard-coding it is how a config ends up with 26 special cases.

CYCLES ESCALATE RATHER THAN REPEAT. A unit that comes back `insufficient_evidence` is re-asked in
the next cycle with a wider candidate net and its sibling units' verdicts included, so a second pass
can cost more evidence rather than more luck. A unit that comes back decided is never re-asked; the
runner's fingerprint cache means an interrupted run resumes instead of restarting.

Usage:
  python3 pipelines/agent-harness/harness.py --country Australia --limit 8
  python3 pipelines/agent-harness/harness.py --country Chile --cycles 2
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
from runner import ClaudeRunner, utc_now  # noqa: E402

DB = REPO / "data" / "final" / "polities_database.csv"
GADM = REPO / "data" / "geodata" / "gadm-4.1" / "gadm41_adm1.gpkg"
SCHEMA = HERE / "schemas" / "routing_verdict.schema.json"
POLICY = HERE / "policy.json"
LEDGER = HERE / "state" / "routing_verdicts.csv"
RUNS = HERE / "state" / "runs"

PANEL = Path(os.environ.get(
    "WHEP_SUBNATIONAL",
    os.path.expanduser("~/Nextcloud/WHEP_ERC 2025/Sources/data_raw/sources_juan/"
                       "whep_production_subnational.parquet")))

LEDGER_FIELDS = ("unit_id", "country", "admin_name", "verdict", "matched_polity_code",
                 "proposed_json", "confidence", "reasoning", "evidence_used", "concerns",
                 "cycle", "model", "effort", "decided_at",
                 "polygon_route", "polygon_source_slug", "polygon_feature_id",
                 "polygon_detail", "polygon_confidence", "polygon_reasoning")

RESIDUAL_MARKERS = ("RESID", "OTHER", "NATIONAL", "UNKNOWN", "TOTAL", "REST")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    return re.sub(r"[^a-z0-9]", "", s.encode("ascii", "ignore").decode().lower())


def load_policy() -> dict[str, Any]:
    return json.loads(POLICY.read_text(encoding="utf-8")) if POLICY.is_file() else {}


def read_ledger() -> dict[str, dict[str, str]]:
    if not LEDGER.is_file():
        return {}
    with open(LEDGER, newline="", encoding="utf-8") as fh:
        return {r["unit_id"]: r for r in csv.DictReader(fh)}


def write_ledger(rows: dict[str, dict[str, str]]) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    ordered = [{f: rows[k].get(f, "") for f in LEDGER_FIELDS} for k in sorted(rows)]
    tmp = LEDGER.with_suffix(".tmp")
    with open(tmp, "w", newline="\n", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(LEDGER_FIELDS), lineterminator="\n")
        w.writeheader()
        w.writerows(ordered)
    os.replace(tmp, LEDGER)          # atomic: a killed run must not truncate the ledger


def polities() -> list[dict[str, str]]:
    with open(DB, newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh)
                if r.get("wiki_status") not in ("retired", "superseded")]


def gadm_names(iso: str) -> list[tuple[str, str]]:
    """(feature id, name) for the country's admin-1 features, or [] when unavailable."""
    if not GADM.is_file():
        return []
    # No blanket except: a swallowed error here is indistinguishable from "this country has no
    # boundaries", and the second is a finding the harness must report rather than hide.
    import warnings

    import geopandas as gpd
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        g = gpd.read_file(GADM, columns=["GID_0", "GID_1", "NAME_1"])
    hit = [(r.GID_1, r.NAME_1) for r in g[g.GID_0 == iso].itertuples()]
    if not hit:
        # Measured 2026-09-02: the committed gadm-4.1-adm1 file is a SUBSET of 81 countries, not the
        # global layer. Of the panel's 13 multi-unit countries only ESP, USA and JPN are in it, so
        # for the rest a create verdict cannot be given a boundary from this source. Said out loud
        # because a silent [] reads as "no match for this name".
        print(f"  note: gadm-4.1-adm1 carries no features for {iso} "
              f"({g.GID_0.nunique()} countries in the file) — a new polity for this country would "
              f"need a boundary from another source")
    return hit


def build_evidence(unit: dict[str, Any], pols: list[dict[str, str]], iso: str,
                   feats: list[tuple[str, str]], *, wide: bool,
                   sibling_verdicts: list[str]) -> str:
    """Everything deterministic we can say about one unit, as evidence lines."""
    lines: list[str] = []
    a = lines.append
    a(f"UNIT")
    a(f"  admin_unit_id      {unit['unit_id']}")
    a(f"  admin_name_clean   {unit['admin_name']!r}")
    a(f"  country_clean      {unit['country']!r}")
    a(f"  admin_level        {unit['admin_level']}")
    a(f"  years              {unit['y0']}-{unit['y1']}")
    a(f"  valued rows        {unit['rows']:,}")
    a(f"  indicators         {unit['indicators']}")
    a(f"  source             {unit['source']}")

    tail = unit["unit_id"].split("-", 1)[1] if "-" in unit["unit_id"] else unit["unit_id"]
    marks = [m for m in RESIDUAL_MARKERS if m in tail.upper()]
    a(f"  identifier markers {marks if marks else 'none'}"
      f"   (observation only -- markers like NATIONAL or RESID often mean a residual bucket or a"
      f" national total in a subnational table, but not always; you decide)")

    n = norm(unit["admin_name"])
    exact = [p for p in pols if norm(p["polity_name"]).startswith(n) or n in norm(p["polity_name"])]
    a("")
    a(f"CANDIDATE POLITIES BY NAME ({len(exact)})")
    for p in exact[:12]:
        a(f"  {p['polity_code']:26} {p['polity_name'][:44]:46} {p['start_year']}-{p['end_year']}"
          f"  type={p['polity_type']}")
    if not exact:
        a("  none -- no existing polity's name resembles this unit's name")

    same_iso = [p for p in pols if p["iso3_code"] == iso]
    a("")
    a(f"POLITIES SHARING iso3 {iso} ({len(same_iso)})")
    # SUBNATIONAL ROWS ARE NEVER OMITTED. Cycle 1 used to show only national rows to keep the
    # prompt small, which hid ALK-1867-1959 -- the Territory of Alaska -- from the Alaska verdict,
    # i.e. exactly the candidate most likely to BE the unit. The agent noticed the omission line and
    # flagged it as a concern, which is the only reason it was caught. What cycle 1 now trims is the
    # far less relevant tail of national eras, and it says how many.
    subnat = [p for p in same_iso if p["polity_type"] != "national"]
    nat = sorted([p for p in same_iso if p["polity_type"] == "national"],
                 key=lambda x: int(x["start_year"]))
    shown_nat = nat if wide else nat[-12:]
    for p in subnat + shown_nat:
        a(f"  {p['polity_code']:26} {p['polity_name'][:44]:46} {p['start_year']}-{p['end_year']}"
          f"  type={p['polity_type']}")
    if len(shown_nat) < len(nat):
        a(f"  ({len(nat) - len(shown_nat)} earlier national era(s) trimmed on this cycle; all "
          f"{len(subnat)} non-national rows for {iso} are shown above)")

    # BOTH directions, and a length floor. The panel prefixes some units with the country ("US
    # Alaska"), so `n in norm(nm)` alone never matches GADM's "Alaska"; stage 2 had the reverse
    # test and found USA.2_1 while stage 1 reported no boundary, and the agent flagged the
    # inconsistency. The floor stops short names matching inside unrelated ones.
    fnames = [f"{gid} {nm}" for gid, nm in feats
              if norm(nm) == n or (len(n) >= 4 and n in norm(nm))
              or (len(norm(nm)) >= 4 and norm(nm) in n)]
    a("")
    a(f"BOUNDARY FEATURES matching the name in gadm-4.1-adm1 ({len(fnames)})")
    for f in fnames[:5]:
        a(f"  {f}")
    if not fnames:
        a(f"  none of the {len(feats)} admin-1 features for {iso} matches this name -- a new polity"
          f" would have no boundary unless one is constructed")

    if sibling_verdicts:
        a("")
        a("VERDICTS ALREADY RECORDED FOR SIBLING UNITS OF THIS COUNTRY")
        for s in sibling_verdicts[:12]:
            a(f"  {s}")
    return "\n".join(lines)


PROMPT = """You are deciding how one subnational reporting unit from an agricultural statistics
compilation should relate to this repository's polity vocabulary. A polity is a row representing a
territory over a span of years; `end_year` is EXCLUSIVE.

The governing policy: a reporting unit qualifies for a polity row when statistics were collected on
it, whether or not it was a sovereign state. So a province, a prefecture or an occupation zone all
qualify. What does NOT qualify is an identifier that is not a place -- a residual "other/rest"
bucket, or a national total that happens to sit in a subnational table -- because a polity code is
an identity and not an aggregation bucket, and conflating the two silently misattributes data.

Return exactly one verdict object for this unit, satisfying the provided schema.

Rules that decide the hard cases:
- `match_existing` only when an existing candidate IS this reporting territory, not merely when it
  contains it. A prefecture is not its country.
- `create_new` requires a span justified by the administration's own history, never by how far this
  extract happens to run: an extract-defined span must be re-spanned whenever the data grows.
- `not_a_territory` for residual buckets and national totals in a subnational table.
- `insufficient_evidence` is a legitimate answer. Prefer it to a guess, and say in `concerns` what
  evidence would decide it.

You may read files in the repository to check a candidate, but you cannot edit anything.

EVIDENCE
--------
{evidence}
"""


def units_for_country(country: str) -> list[dict[str, Any]]:
    import pandas as pd
    df = pd.read_parquet(PANEL, columns=["country_clean", "admin_unit_id", "admin_name_clean",
                                         "admin_level", "year", "indicator", "value_canonical"])
    df = df[(df.country_clean == country) & df.value_canonical.notna()]
    if df.empty:
        return []
    src = pd.read_parquet(PANEL, columns=["country_clean", "source"])
    source = src[src.country_clean == country]["source"].mode()
    g = df.groupby("admin_unit_id").agg(
        admin_name=("admin_name_clean", "first"), admin_level=("admin_level", "first"),
        y0=("year", "min"), y1=("year", "max"), rows=("year", "size"),
        indicators=("indicator", lambda s: ", ".join(sorted(set(s)))))
    out = []
    for uid, r in g.sort_index().iterrows():
        out.append({"unit_id": uid, "country": country, "admin_name": r["admin_name"],
                    "admin_level": r["admin_level"], "y0": int(r["y0"]), "y1": int(r["y1"]),
                    "rows": int(r["rows"]), "indicators": r["indicators"],
                    "source": (source.iloc[0] if len(source) else "unknown")})
    return out


def iso_for_country(country: str, pols: list[dict[str, str]]) -> str:
    """The iso3 this repository already uses for the country, matched on its FULL name.

    A 6-character prefix was tried first and resolved "United States of America" to **ARE**, the
    United Arab Emirates -- both normalise to `united*`. The verdicts that followed were plausible
    and built on the wrong candidate set, which is the worst failure available to an evidence layer:
    it does not look broken. Matching the whole normalised name is what makes the resolution exact,
    and an unresolved country now returns "" so the caller can say so rather than guess a stem.
    """
    n = norm(country)
    exact = [p for p in pols
             if p["polity_type"] == "national" and norm(p["polity_name"]).startswith(n)]
    if exact:
        return exact[0]["iso3_code"]
    # Aliases the repository holds for the same territory under a different name.
    alias = {"unitedstatesofamerica": "USA", "russia": "RUS", "southkorea": "KOR"}
    return alias.get(n, "")



# ---------------------------------------------------------------------------
# Stage 2 — where would a proposed polity's boundary come from?
# ---------------------------------------------------------------------------
# Run only for `create_new` verdicts, because it is the only case that needs a boundary. Kept a
# SEPARATE stage rather than folded into the routing verdict for three reasons: the routing question
# is answerable without it (whether a territory deserves a row does not depend on whether we can
# draw it), a combined schema would let a weak boundary answer drag down a strong routing one, and
# the local source inventory is the kind of evidence that changes independently of the panel.
POLYGON_SCHEMA = HERE / "schemas" / "polygon_route.schema.json"
SOURCES_YAML = REPO / "scripts" / "sources.yaml"


def registered_sources() -> list[dict[str, Any]]:
    if not SOURCES_YAML.is_file():
        return []
    import yaml
    cfg = yaml.safe_load(SOURCES_YAML.read_text(encoding="utf-8")) or {}
    out = []
    for slug, spec in (cfg.get("sources") or {}).items():
        f = spec.get("file")
        out.append({"slug": slug, "file": f or "",
                    "present": bool(f) and (REPO / f).exists(),
                    "id_column": spec.get("id_column", ""),
                    "url": spec.get("url", "")})
    return out


def polygon_evidence(unit: dict[str, Any], proposed: dict[str, Any], iso: str,
                     feats: list[tuple[str, str]], pols: list[dict[str, str]]) -> str:
    lines: list[str] = []
    a = lines.append
    a("PROPOSED POLITY (from the routing verdict)")
    for k in ("polity_name", "iso3", "start_year", "end_year", "container_code"):
        a(f"  {k:16} {proposed.get(k)}")
    a(f"  span_basis       {proposed.get('span_basis','')[:160]}")
    a("")
    a("REGISTERED POLYGON SOURCES (scripts/sources.yaml)")
    for src in registered_sources():
        a(f"  {src['slug']:24} present_locally={str(src['present']):5} "
          f"id_column={src['id_column'] or '-':12} {src['file'][:46]}")
    a("")
    n = norm(unit["admin_name"])
    matches = [f"{gid}  {nm}" for gid, nm in feats if norm(nm) == n or n in norm(nm) or norm(nm) in n]
    a(f"gadm-4.1-adm1 FEATURES FOR {iso}: {len(feats)} total, {len(matches)} matching this name")
    for m in matches[:6]:
        a(f"  {m}")
    if feats and not matches:
        a(f"  no name match; nearest by prefix: "
          f"{[nm for _, nm in feats if norm(nm)[:3] == n[:3]][:5] or 'none'}")
    if not feats:
        a(f"  THIS COUNTRY IS ABSENT from the local gadm-4.1-adm1 file, which is a SUBSET of 81 "
          f"countries rather than the global layer. A registered-source route is therefore not "
          f"available from what is on disk, even if GADM publishes the feature.")
    a("")
    used = {}
    for p in pols:
        if p["iso3_code"] == iso and p.get("polygon_source"):
            used.setdefault(p["polygon_source"], []).append(p["polity_code"])
    a(f"WHAT THIS REPOSITORY ALREADY USES FOR {iso}")
    for src, codes in used.items():
        a(f"  {src:24} {len(codes)} row(s), e.g. {codes[:3]}")
    if not used:
        a("  nothing — no existing polity for this country carries a polygon source")
    return "\n".join(lines)


POLYGON_PROMPT = """A routing verdict proposed a NEW polity. Decide where its boundary would come
from, and return one object satisfying the schema.

What matters:
- Prefer a source already registered in `scripts/sources.yaml` AND present locally. A route through
  a file that is not on disk cannot be executed today, so say so rather than implying it can.
- `construct_from_registered` when the territory is a union or difference of registered features
  (a region that is the union of provinces, a mandate minus a partitioned half). Name the members.
- `new_source_needed` when a real boundary exists in the world but no registered source has it. Name
  a specific candidate and set `licence_known` HONESTLY -- false unless the evidence shows it, since
  a source cannot be adopted on an unchecked licence.
- `none_available` when no source is known to digitise this territory for this period. That is a
  legitimate answer for historical units nobody has mapped.
- State `vintage_risk` whenever the feature's date is far from the polity's span. A present-day
  boundary standing in for a 19th-century territory is an approximation that must be stated.

You may read files in the repository to check what a source contains. You cannot edit anything.

EVIDENCE
--------
{evidence}
"""


def run_polygon_stage(A, runner, pols, iso, feats, ledger) -> None:
    import json as _json
    todo = [v for v in ledger.values()
            if v.get("country") == A.country and v.get("verdict") == "create_new"
            and not v.get("polygon_route")]
    if not todo:
        print("\nstage 2 (polygon): nothing to route")
        return
    print(f"\nstage 2 (polygon): {len(todo)} proposed polit(ies)")
    for v in todo:
        proposed = _json.loads(v["proposed_json"]) if v.get("proposed_json") else {}
        unit = {"admin_name": v["admin_name"], "unit_id": v["unit_id"]}
        ev = polygon_evidence(unit, proposed, iso, feats, pols)
        job = f"polygon-{norm(v['unit_id'])}"
        res = runner.call(job, POLYGON_PROMPT.format(evidence=ev), POLYGON_SCHEMA,
                          refresh=A.refresh)
        if not res.ok:
            print(f"  FAIL  {v['unit_id']:24} {res.error}")
            continue
        r = res.result
        v["polygon_route"] = r["route"]
        v["polygon_source_slug"] = r.get("source_slug") or ""
        v["polygon_feature_id"] = r.get("feature_id") or ""
        v["polygon_detail"] = _json.dumps(
            {k: r.get(k) for k in ("construction", "candidate_new_source", "vintage_risk")
             if r.get(k)}, sort_keys=True)
        v["polygon_confidence"] = r["confidence"]
        v["polygon_reasoning"] = r["reasoning"]
        write_ledger(ledger)
        detail = r.get("feature_id") or (
            (r.get("candidate_new_source") or {}).get("name", "")) or (
            (r.get("construction") or {}).get("method", ""))
        print(f"  {r['route']:28} {v['unit_id']:24} {r['confidence']:7} {str(detail)[:34]}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", required=True)
    ap.add_argument("--limit", type=int, default=0, help="units per cycle (0 = all undecided)")
    ap.add_argument("--cycles", type=int, default=1)
    ap.add_argument("--model", default=None)
    ap.add_argument("--effort", default=None)
    ap.add_argument("--refresh", action="store_true", help="ignore the fingerprint cache")
    # Targeted re-runs: re-ask one unit after changing its evidence or the prompt, without paying
    # for the whole country to reach it alphabetically.
    ap.add_argument("--only", nargs="*", default=None, metavar="UNIT_ID",
                    help="restrict to these admin_unit_ids")
    ap.add_argument("--polygon-stage", action="store_true",
                    help="after routing, ask where each create_new proposal's boundary comes from")
    A = ap.parse_args()

    if not PANEL.is_file():
        print(f"SKIP: panel not at {PANEL}\n  set WHEP_SUBNATIONAL (never committed to this repo)")
        return 0

    pol = load_policy()
    model = A.model or pol.get("model", "sonnet")
    effort = A.effort or pol.get("effort", "low")
    run_dir = RUNS / f"{norm(A.country)}"
    run_dir.mkdir(parents=True, exist_ok=True)
    runner = ClaudeRunner(run_dir=run_dir, model=model, effort=effort,
                          timeout=int(pol.get("timeout_seconds", 600)),
                          max_budget_usd=pol.get("max_budget_usd"))

    pols = polities()
    iso = iso_for_country(A.country, pols)
    if not iso:
        print(f"FAIL: no national polity's name matches {A.country!r}, so the candidate set cannot "
              f"be assembled. Add the country's alias rather than letting the harness guess: a "
              f"wrong iso3 yields plausible verdicts built on another country's rows.")
        return 1
    feats = gadm_names(iso)
    units = units_for_country(A.country)
    if A.only:
        wanted = set(A.only)
        missing = wanted - {u["unit_id"] for u in units}
        if missing:
            print(f"FAIL: --only names unit(s) absent from the panel for {A.country}: "
                  f"{sorted(missing)}")
            return 1
        units = [u for u in units if u["unit_id"] in wanted]
    ledger = read_ledger()
    print(f"{A.country}: {len(units)} unit(s); iso3 resolved to {iso}; "
          f"{len(feats)} admin-1 boundary feature(s); model={model} effort={effort}")

    for cycle in range(1, A.cycles + 1):
        # --refresh means RE-ASK, so it must bypass the queue filter as well as the runner's
        # fingerprint cache. Without this the flag was inert: an already-decided unit never entered
        # the batch, so the cache it was meant to bust was never consulted and the printed verdict
        # was the stale one.
        undecided = units if A.refresh else [
            u for u in units
            if ledger.get(u["unit_id"], {}).get("verdict") in (None, "", "insufficient_evidence")]
        if not undecided:
            print(f"cycle {cycle}: nothing undecided")
            break
        batch = undecided[:A.limit] if A.limit else undecided
        wide = cycle > 1                     # escalate evidence rather than repeat the question
        print(f"\ncycle {cycle}: {len(batch)} unit(s)"
              f"{' [wide candidate net]' if wide else ''}")
        siblings = [f"{v['unit_id']} -> {v['verdict']}"
                    f"{' ' + v['matched_polity_code'] if v['matched_polity_code'] else ''}"
                    for v in ledger.values()
                    if v.get("country") == A.country and v.get("verdict")
                    and v["verdict"] != "insufficient_evidence"]
        for u in batch:
            ev = build_evidence(u, pols, iso, feats, wide=wide, sibling_verdicts=siblings)
            job = f"cycle{cycle:02d}-{norm(u['unit_id'])}"
            res = runner.call(job, PROMPT.format(evidence=ev), SCHEMA, refresh=A.refresh)
            if not res.ok:
                print(f"  FAIL  {u['unit_id']:24} {res.error}")
                continue
            v = res.result
            ledger[u["unit_id"]] = {
                "unit_id": u["unit_id"], "country": A.country, "admin_name": u["admin_name"],
                "verdict": v["verdict"], "matched_polity_code": v.get("matched_polity_code") or "",
                "proposed_json": json.dumps(v["proposed"], sort_keys=True) if v.get("proposed") else "",
                "confidence": v["confidence"], "reasoning": v["reasoning"],
                "evidence_used": " | ".join(v.get("evidence_used", [])),
                "concerns": " | ".join(v.get("concerns", [])),
                "cycle": str(cycle), "model": model, "effort": effort, "decided_at": utc_now()}
            write_ledger(ledger)
            tag = "cached" if res.cached else "fresh"
            extra = v.get("matched_polity_code") or (
                v["proposed"]["polity_name"] if v.get("proposed") else "")
            print(f"  {v['verdict']:22} {u['unit_id']:24} {v['confidence']:7} {extra[:34]:36}({tag})")

    if A.polygon_stage:
        run_polygon_stage(A, runner, pols, iso, feats, ledger)

    decided = [v for v in ledger.values() if v.get("country") == A.country]
    from collections import Counter
    # Denominator is the country's FULL unit count, not the --only/-limit slice: "3 of 1 decided"
    # is what the filtered count produced.
    total = len(units_for_country(A.country))
    print(f"\n{A.country}: {len(decided)} of {total} unit(s) decided — "
          f"{dict(Counter(v['verdict'] for v in decided))}")
    print(f"ledger: {LEDGER.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
