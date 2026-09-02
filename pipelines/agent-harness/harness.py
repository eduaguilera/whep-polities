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
import builtins
import functools
import csv
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any

# A background run must show progress: Python buffers stdout when it is not a TTY, so a
# redirected run printed nothing for eight minutes and looked hung.
print = functools.partial(builtins.print, flush=True)  # noqa: A001

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
from runner import ClaudeRunner, utc_now  # noqa: E402

DB = REPO / "data" / "final" / "polities_database.csv"
GADM = REPO / "data" / "geodata" / "gadm-4.1" / "gadm41_adm1.gpkg"
SCHEMA = HERE / "schemas" / "routing_verdict.schema.json"
POLICY = HERE / "policy.json"
LEDGER = HERE / "state" / "routing_verdicts.csv"
NUTS_XW = REPO / "data" / "final" / "nuts_code_names.csv"
RUNS = HERE / "state" / "runs"

PANEL = Path(os.environ.get(
    "WHEP_SUBNATIONAL",
    os.path.expanduser("~/Nextcloud/WHEP_ERC 2025/Sources/data_raw/sources_juan/"
                       "whep_production_subnational.parquet")))

LEDGER_FIELDS = ("unit_id", "country", "admin_name", "verdict", "matched_polity_code",
                 "proposed_json", "confidence", "reasoning", "evidence_used", "concerns",
                 "cycle", "model", "effort", "decided_at",
                 "polygon_route", "polygon_source_slug", "polygon_feature_id",
                 "polygon_detail", "polygon_confidence", "polygon_reasoning",
                 "page_written", "page_polity_code",
                 "repair_status", "repair_attempts", "repair_rank", "repair_remaining",
                 "repair_gates_red")

RESIDUAL_MARKERS = ("RESID", "OTHER", "NATIONAL", "UNKNOWN", "TOTAL", "REST")


def nuts_names() -> dict[str, str]:
    """NUTS code -> official Latin name, from Eurostat GISCO's NUTS 2021 attribute table.

    WHY THIS IS NOT OPTIONAL. For the NUTS countries the panel's `admin_name_clean` is the bare
    code -- `ES111`, not a province name -- so 183 of the 431 units arrive with no identifying text
    at all. Without this crosswalk every one of them got `create_new` at medium confidence with an
    explicit "could not confirm the code-to-name mapping" concern, and the model resolved ES111 to
    **Álava** from its own knowledge when Eurostat says **A Coruña** (Álava is ES211). A confidently
    wrong name would have created a polity for the wrong province's data, so the mapping is read
    from a source rather than recalled.
    """
    if not NUTS_XW.is_file():
        return {}
    with open(NUTS_XW, newline="", encoding="utf-8") as fh:
        return {r["nuts_id"]: r["name_latn"] for r in csv.DictReader(fh)}


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
                   sibling_verdicts: list[str],
                   convention: dict[str, Any] | None = None) -> str:
    """Everything deterministic we can say about one unit, as evidence lines."""
    lines: list[str] = []
    a = lines.append
    if convention:
        # A CONSTRAINT, not a suggestion: this is what stops 44 units inventing 44 spans.
        a("COUNTRY CONVENTION — already decided for this country; apply it, do not re-derive it")
        a(f"  system              {convention['system_name']}")
        a(f"  system_start_year   {convention['system_start_year']}"
          f"   ({convention.get('system_start_basis','')[:90]})")
        a(f"  open end_year       {convention['open_end_year']} (EXCLUSIVE) for any still-current "
          f"unit — use exactly this, not a round number and not the data's last year")
        a(f"  container chain     " + ", ".join(
            f"{e['code']}({e['start_year']}-{e['end_year']})"
            for e in convention["container_chain"]))
        if convention.get("naming_pattern"):
            a(f"  naming pattern      {convention['naming_pattern']}")
        a("")
    a(f"UNIT")
    a(f"  admin_unit_id      {unit['unit_id']}")
    a(f"  admin_name_clean   {unit['admin_name']!r}")
    if unit.get("official_name"):
        a(f"  OFFICIAL NAME      {unit['official_name']!r}   (Eurostat GISCO NUTS 2021, "
          f"data/final/nuts_code_names.csv -- authoritative; do NOT resolve the code from memory)")
    elif unit["admin_level"] == "NUTS":
        a(f"  OFFICIAL NAME      NOT FOUND for this code in data/final/nuts_code_names.csv. Do not "
          f"guess the territory from the code: say what is missing instead.")
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

    n = norm(unit.get("official_name") or unit["admin_name"])
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
        xw = nuts_names()
        official = xw.get(str(r["admin_name"]).replace("_", ""), "")
        out.append({"unit_id": uid, "country": country, "admin_name": r["admin_name"],
                    "official_name": official,
                    "admin_level": r["admin_level"], "y0": int(r["y0"]), "y1": int(r["y1"]),
                    "rows": int(r["rows"]), "indicators": r["indicators"],
                    "source": (source.iloc[0] if len(source) else "unknown")})
    return out


def crosswalk_iso() -> dict[str, str]:
    """country label -> iso3, from the crosswalks this repository already maintains.

    Deliberately NOT a hand-written alias dict. An earlier version of this function carried one, and
    it was both wrong (a 6-character prefix match resolved "United States of America" to ARE, so a
    whole country's verdicts were built on the Emirates' rows) and exactly the kind of ad-hoc table
    that has to be extended by hand for every new dataset. These two files are built by the repo's
    own pipelines and cover 24 of the 26 countries in the panel; the remaining labels are resolved by
    asking, once, and banking the answer.
    """
    out: dict[str, str] = {}
    fao = REPO / "data" / "final" / "faostat_area_polity_map.csv"
    if fao.exists():
        for r in csv.DictReader(fao.open(encoding="utf-8")):
            if r.get("iso3"):
                out.setdefault(norm(r["source_label"]), r["iso3"])
    alias = REPO / "data" / "final" / "label_alias_map.csv"
    if alias.exists():
        for r in csv.DictReader(alias.open(encoding="utf-8")):
            code = (r.get("polity_code") or "").split("-")[0]
            if len(code) == 3:
                out.setdefault(norm(r["source_label"]), code)
    return out


ISO_LEDGER = HERE / "state" / "country_iso.json"
ISO_SCHEMA = HERE / "schemas" / "iso_resolution.schema.json"

ISO_PROMPT = """Resolve one country label to the ISO3 code used by this repository's polity table.

The repository's own crosswalks did not answer it, which usually means the label is a short common
name and the table (or the crosswalk) carries a long official one, or the reverse.

Answer null rather than guessing: a wrong code silently builds a whole country's decisions on
another country's rows, which has happened here before.

LABEL
-----
{label}

NATIONAL ROWS IN THE TABLE (name, iso3, span) — the code must be one of these
------------------------------------------------------------------------------
{national}
"""


def resolve_iso(country: str, pols: list[dict[str, str]], runner) -> str:
    """Crosswalk first, then ask once and bank it. No hand-maintained alias table."""
    n = norm(country)
    cw = crosswalk_iso()
    if n in cw:
        return cw[n]
    banked = json.loads(ISO_LEDGER.read_text(encoding="utf-8")) if ISO_LEDGER.exists() else {}
    if country in banked:
        return banked[country].get("iso3_code") or ""
    nat = sorted({(p["polity_name"], p["iso3_code"]) for p in pols
                  if p["polity_type"] == "national" and p["iso3_code"]})
    listing = "\n".join(f"  {name[:52]:54} {iso}" for name, iso in nat)
    res = runner.call(f"iso-{n}", ISO_PROMPT.format(label=country, national=listing), ISO_SCHEMA)
    if not res.ok:
        print(f"  could not resolve {country!r} to an iso3: {res.error}")
        return ""
    r = res.result
    valid = {iso for _, iso in nat}
    if r.get("iso3_code") and r["iso3_code"] not in valid:
        print(f"  {country!r} resolved to {r['iso3_code']}, which is not a national row — refusing")
        r = {**r, "iso3_code": None,
             "basis": r.get("basis", "") + " [HARNESS: refused, code absent from the table]"}
    banked[country] = r
    tmp = ISO_LEDGER.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(banked, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, ISO_LEDGER)
    print(f"  resolved {country!r} -> {r.get('iso3_code')} ({r['confidence']}): {r['basis'][:80]}")
    return r.get("iso3_code") or ""



# ---------------------------------------------------------------------------
# Stage 0 — the country's convention, decided ONCE
# ---------------------------------------------------------------------------
# Per-unit independence produced 44 individually-reasonable Spanish verdicts that disagreed with
# each other: 19 proposed end_year 2026, 18 proposed 2025 and 4 proposed 2100, for provinces sharing
# one administrative history. Nothing in a per-unit prompt can fix that, because no unit can see what
# the others chose. So the country's convention -- when its system began, what a still-current unit's
# exclusive end_year is, and which national rows it nests inside -- is decided once, cached, and
# passed into every unit's evidence as a CONSTRAINT rather than a suggestion.
CONVENTION_SCHEMA = HERE / "schemas" / "country_convention.schema.json"

CONVENTION_PROMPT = """Establish the span and container convention for one country's subnational
reporting units, so that every unit of this country is spanned and named consistently. Return one
object satisfying the schema.

This is decided ONCE for the country and then applied to all its units. Units decided independently
produced three different end_years for provinces sharing one administrative history, which is the
failure this stage removes.

What matters:
- `system_start_year` is when the administrative system these units belong to came into being -- a
  documented reform or reorganisation, not the first year this extract happens to cover.
- `open_end_year` is EXCLUSIVE and must be ONE value for every still-current unit. Prefer the
  containing national row's own end_year: a unit cannot outlive its container, and a round number
  like 2100 asserts a span nobody has evidence for.
- `container_chain` is the national rows a unit of this country sits inside, in order. Each unit's
  containment edges are cut from this chain, so it must be complete and non-overlapping.

You may read the polity table to establish the container chain and its exact spans.

EVIDENCE
--------
{evidence}
"""


def convention_evidence(country: str, iso: str, pols: list[dict[str, str]],
                        units: list[dict[str, Any]]) -> str:
    lines = [f"COUNTRY {country!r}  iso3 {iso}", ""]
    a = lines.append
    a(f"UNITS IN THE PANEL: {len(units)}")
    if units:
        y0 = min(u["y0"] for u in units)
        y1 = max(u["y1"] for u in units)
        lvl = sorted({u["admin_level"] for u in units})
        a(f"  admin_level(s)     {lvl}")
        a(f"  data coverage      {y0}-{y1}   <- NOT a basis for the span; stated so you can see it")
        a(f"  example units      {[u.get('official_name') or u['admin_name'] for u in units[:6]]}")
    a("")
    nat = sorted([p for p in pols if p["iso3_code"] == iso and p["polity_type"] == "national"],
                 key=lambda x: int(x["start_year"]))
    a(f"NATIONAL ROWS FOR {iso} ({len(nat)}) — the container chain must be cut from these")
    for p in nat:
        a(f"  {p['polity_code']:22} {p['polity_name'][:40]:42} {p['start_year']}-{p['end_year']}")
    sub = [p for p in pols if p["iso3_code"] == iso and p["polity_type"] == "subnational"]
    a("")
    a(f"EXISTING SUBNATIONAL ROWS FOR {iso} ({len(sub)}) — their spans are precedent")
    for p in sub[:12]:
        a(f"  {p['polity_code']:26} {p['polity_name'][:38]:40} {p['start_year']}-{p['end_year']}")
    if not sub:
        a("  none — this country has no subnational precedent in the table")
    return "\n".join(lines)


CONVENTION_LEDGER = HERE / "state" / "country_conventions.json"


def load_conventions() -> dict[str, Any]:
    if CONVENTION_LEDGER.exists():
        return json.loads(CONVENTION_LEDGER.read_text(encoding="utf-8"))
    return {}


def save_convention(country: str, conv: dict[str, Any]) -> None:
    # Written as a DECISION, not a cache. A prompt-fingerprint cache is invalidated by --refresh,
    # which would let the country's span silently change between runs and reintroduce exactly the
    # disagreement this stage removes. Re-deciding it now takes an explicit --refresh-convention.
    all_c = load_conventions()
    all_c[country] = conv
    tmp = CONVENTION_LEDGER.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(all_c, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, CONVENTION_LEDGER)


def country_convention(A, runner, pols, iso, units) -> dict[str, Any] | None:
    banked = load_conventions()
    if A.country in banked and not A.refresh_convention:
        c = banked[A.country]
        print(f"  convention: {c['system_name'][:56]}   (banked; --refresh-convention to re-decide)")
        print(f"    system start {c['system_start_year']}   open end_year {c['open_end_year']} "
              f"({c['confidence']})")
        return c
    ev = convention_evidence(A.country, iso, pols, units)
    res = runner.call(f"convention-{norm(A.country)}", CONVENTION_PROMPT.format(evidence=ev),
                      CONVENTION_SCHEMA, refresh=A.refresh_convention)
    if not res.ok:
        print(f"  convention call failed: {res.error} — units will be decided without it")
        return None
    by_code = {p["polity_code"]: p for p in pols}

    def objection(c: dict[str, Any]) -> str | None:
        """The only two things checkable against the table without inventing an answer."""
        bad = [e["code"] for e in c["container_chain"] if e["code"] not in by_code]
        if bad:
            return (f"The container chain names {bad}, which are not polity_codes in the table. "
                    f"Every code must be one you were shown.")
        # The polity CODE string and the end_year COLUMN disagree for some rows, and the column is
        # the authority. Not corrected here on purpose: picking a value for the country would be
        # this harness inventing its span. The disagreement is handed back instead.
        ends = sorted({int(by_code[e["code"]]["end_year"]) for e in c["container_chain"]})
        if c["open_end_year"] not in ends:
            return (f"open_end_year is {c['open_end_year']}, but the containing national row(s) end "
                    f"at {ends} according to their end_year COLUMN. A unit cannot outlive its "
                    f"container, and end_year is EXCLUSIVE so being one year short silently drops a "
                    f"year. Note the code string and the column can differ -- read the column.")
        return None

    c = res.result
    for retry in range(2):
        obj = objection(c)
        if not obj:
            break
        print(f"  convention rejected: {obj[:150]}")
        res = runner.call(f"convention-{norm(A.country)}-retry{retry + 1}",
                          CONVENTION_PROMPT.format(evidence=ev)
                          + f"\n\nA PREVIOUS ANSWER WAS REJECTED\n{'-' * 30}\n{obj}\n"
                            f"It proposed system_start_year {c['system_start_year']} and "
                            f"open_end_year {c['open_end_year']}. Fix only what the objection names.",
                          CONVENTION_SCHEMA, refresh=True)
        if not res.ok:
            print(f"  convention retry failed: {res.error}")
            return None
        c = res.result
    else:
        print(f"  convention still fails after 2 retries — refusing it; units decided without one")
        return None
    save_convention(A.country, c)
    print(f"  convention: {c['system_name'][:56]}")
    print(f"    system start {c['system_start_year']}   open end_year {c['open_end_year']} "
          f"({c['confidence']})")
    print(f"    container chain: "
          + ", ".join(f"{e['code']}({e['start_year']}-{e['end_year']})"
                      for e in c["container_chain"]))
    return c


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
    # --only applies to EVERY stage: a later stage that ignores it acts on a unit nobody asked
    # about, which is how a request for Alaska produced a California page.
    scope = set(A.only) if A.only else None
    todo = [v for v in ledger.values()
            if v.get("country") == A.country and v.get("verdict") == "create_new"
            and not v.get("polygon_route")
            and (scope is None or v["unit_id"] in scope)]
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



# ---------------------------------------------------------------------------
# Stage 3 — author the wiki page for a create_new verdict
# ---------------------------------------------------------------------------
# The polity table is BUILT FROM THE WIKI, one row per page, so the page is the artefact and the CSV
# row is derived. That makes authoring the page the real creation step -- and it is not mechanical.
# A generated stub (14 differing lines in 93, no history, no open questions) satisfies the gates and
# tells a later reader nothing, which is what a previous hand-rolled generator produced.
#
# THE AGENT AUTHORS, THE HARNESS WRITES. Edit and Write stay denied: the agent returns a
# schema-validated object and this module renders and writes the file. So nothing reaches the tree
# unvalidated, the page structure stays uniform across authors, and the content is where judgement
# is allowed to vary. The schema carries minimum lengths and requires at least one open question,
# because "nothing unresolved" is almost always a page that did not look.
WIKI_SCHEMA = HERE / "schemas" / "wiki_page.schema.json"
PAGE_SPEC = REPO / "pipelines" / "pre1961-matching" / "README.md"
EXEMPLAR = REPO / "wiki" / "polities" / "man-1950-1955.md"


def page_spec_text() -> str:
    """The repository's own 'Wiki page requirements' section, quoted to the author verbatim."""
    if not PAGE_SPEC.is_file():
        return "(page-requirements spec not found)"
    txt = PAGE_SPEC.read_text(encoding="utf-8")
    i = txt.find("### Wiki page requirements")
    if i == -1:
        return "(section not found)"
    j = txt.find("## Source boundary definitions", i)
    return txt[i:j if j != -1 else i + 4000]


def render_page(page: dict[str, Any]) -> str:
    fm = page["frontmatter"]
    lines = ["---", f"polity_code: {page['polity_code']}"]
    for k in ("polity_name", "start_year", "end_year"):
        lines.append(f"{k}: {fm[k]}")
    lines += [f"type: {fm['type']}", f"iso3: {fm['iso3']}", f"continent: {fm['continent']}",
              "cow: NA", "status: draft", f"last_ingest: {utc_now()[:10]}",
              "sources: [juan-subnational]",
              f"polygon_source: {fm['polygon_source']}"]
    fid = fm.get("polygon_feature_id")
    lines.append(f"polygon_feature_id: {fid if fid else 'null'}")
    lines += ["polygon_feature_year: null", f"polygon_status: {fm['polygon_status']}"]
    # polygon_area_km2 is deliberately absent: a figure read off the attached geometry cannot be
    # evidence about the territory (issue 195), and the measurement belongs in the prose instead.
    lines.append(f"predecessor: [{', '.join(fm.get('predecessor') or [])}]")
    lines.append(f"successor: [{', '.join(fm.get('successor') or [])}]")
    for edge in fm.get("container") or []:
        if edge is (fm.get("container") or [])[0]:
            lines.append("container:")
        lines += [f"  - code: {edge['code']}", f"    start_year: {edge['start_year']}",
                  f"    end_year: {edge['end_year']}", f"    basis: {edge['basis']}"]
    lines += ["---", "", f"# {fm['polity_name']}", "", "## Summary", "", page["summary"], "",
              "**Why this entry exists.** " + page["why_this_entry_exists"], "",
              "## Territorial extent", "", page["territorial_extent"], "",
              "## Predecessors and successors", "", page["predecessors_and_successors"], "",
              "## Sourced claims", ""]
    lines += [f"- {c}" for c in page["sourced_claims"]]
    lines += ["", "## Decisions", ""]
    for d in page["decisions"]:
        lines += [f"### {d['anchor']}", "", f"**{d['title']}**", "", d["body"], ""]
    lines += ["## Open questions", ""]
    for q in page["open_questions"]:
        lines += [f"### {q['anchor']}", "", f"**{q['title']}**", "", q["body"], ""]
    return "\n".join(lines).rstrip("\n") + "\n"


WIKI_PROMPT = """Author the wiki page for a polity this pipeline has decided to create. Return one
object satisfying the schema; you cannot write files, so the harness renders and writes what you
return.

THE POLITY CODE FOLLOWS THIS REPOSITORY'S CONVENTION, which the schema cannot express: it is
`<ISO3>-<SUBUNIT>-<start>-<end>` for a named part of a country (DZA-CVD-1902-1919,
IDN-BLB-1949-1951, JPN-AICHI-1871-2025), or `<ISO3>-<start>-<end>` where the row IS the whole
territory. Do NOT invent a new iso-like prefix from the unit's name -- `CALI-1850-2026` is wrong,
`USA-CALIFORNIA-1850-2026` is right. `end_year` is EXCLUSIVE.

THE CONTAINER EDGES MUST TILE THE WHOLE SPAN. One edge per era of the containing chain, together
covering start_year to end_year with no gap: a 1850-2026 span containered only by USA-1959-2025
leaves 109 years uncontained, and the containment gate rejects an edge that falls outside either
party's span. Read the polity table for the container's own eras.

This repository BUILDS THE POLITY TABLE FROM THE WIKI -- one row per page -- so this page is the
artefact and the database row is derived from it. A page that satisfies the schema while saying
nothing specific is worse than no page: it passes every check and tells the next reader nothing.

The repository's own page-requirements spec is quoted below and is binding. Note especially that the
territorial extent must give a territory a reader can LOCATE on a modern map with an approximate
km2, and that an area measured from the attached geometry must be labelled as a measurement of the
polygon rather than presented as evidence about the territory.

Write about THIS territory specifically. Its own administrative history, what it was before and
after, why its span starts and ends where it does. Generic prose that would fit any unit of this
type is the failure mode here.

At least one open question is required. If you cannot find anything unresolved, you have not looked
hard enough -- boundary vintage, span endpoints, whether a neighbouring row overlaps, and what the
data does not cover are all live in nearly every case.

You may read files in the repository -- the exemplar page, the polity table, sibling pages -- to
ground what you write.

PAGE-REQUIREMENTS SPEC (binding)
--------------------------------
{spec}

AN EXEMPLAR PAGE, hand-written, for tone and depth
--------------------------------------------------
{exemplar}

THE DECISION THIS PAGE IMPLEMENTS
---------------------------------
{decision}
"""


def run_wiki_stage(A, runner, ledger) -> None:
    import json as _json
    scope = set(A.only) if A.only else None
    todo = [v for v in ledger.values()
            if v.get("country") == A.country and v.get("verdict") == "create_new"
            and v.get("polygon_route") and not v.get("page_written")
            and (scope is None or v["unit_id"] in scope)]
    if not todo:
        print("\nstage 3 (wiki): nothing to author "
              "(needs a create_new verdict that has been through the polygon stage)")
        return
    spec = page_spec_text()
    exemplar = EXEMPLAR.read_text(encoding="utf-8")[:6000] if EXEMPLAR.is_file() else "(none)"
    print(f"\nstage 3 (wiki): authoring {len(todo)} page(s)")
    for v in todo:
        decision = _json.dumps({
            "unit_id": v["unit_id"], "admin_name": v["admin_name"], "country": v["country"],
            "routing_reasoning": v["reasoning"], "routing_concerns": v["concerns"],
            "proposed": _json.loads(v["proposed_json"]) if v.get("proposed_json") else {},
            "polygon_route": v["polygon_route"], "polygon_source": v["polygon_source_slug"],
            "polygon_feature_id": v["polygon_feature_id"],
            "polygon_detail": v.get("polygon_detail", ""),
            "polygon_reasoning": v.get("polygon_reasoning", ""),
        }, indent=2)
        job = f"wiki-{norm(v['unit_id'])}"
        res = runner.call(job, WIKI_PROMPT.format(spec=spec, exemplar=exemplar,
                                                  decision=decision), WIKI_SCHEMA,
                          refresh=A.refresh)
        if not res.ok:
            print(f"  FAIL  {v['unit_id']:24} {res.error}")
            continue
        page = res.result
        code = page["polity_code"]
        dest = REPO / "wiki" / "polities" / f"{code.lower()}.md"
        if dest.exists() and not A.refresh:
            print(f"  SKIP  {code} — page already exists; --refresh to overwrite")
            continue
        dest.write_text(render_page(page), encoding="utf-8")
        v["page_written"] = str(dest.relative_to(REPO))
        v["page_polity_code"] = code
        write_ledger(ledger)
        nsec = len(page["decisions"]) + len(page["open_questions"])
        print(f"  wrote {dest.relative_to(REPO)}  "
              f"({len(render_page(page).splitlines())} lines, {len(page['sourced_claims'])} claims, "
              f"{len(page['decisions'])} decision(s), {len(page['open_questions'])} open question(s))")



# ---------------------------------------------------------------------------
# Stage 4 — repair a page against the gates, narrowly, and keep the best attempt
# ---------------------------------------------------------------------------
# attempt -> classify -> fix what a script fixes -> re-ask NARROWLY for the rest -> rank -> keep the
# best. Capped, because an uncapped repair loop on an unfixable page burns tokens until someone
# notices. The page on disk at the end is the best-ranked attempt, not the last one: a later attempt
# that fixed the arithmetic and hollowed out the prose must not win by being last.
import repair as _repair


def run_repair_stage(A, runner, ledger, max_attempts: int = 3) -> None:
    import json as _json
    todo = [v for v in ledger.values()
            if v.get("country") == A.country and v.get("page_written")
            and v.get("repair_status") not in ("clean", "clean_for_code", "exhausted")
            and (not A.only or v["unit_id"] in set(A.only))]
    if not todo:
        print("\nstage 4 (repair): nothing to repair")
        return
    print(f"\nstage 4 (repair): {len(todo)} page(s), up to {max_attempts} attempt(s) each")

    for v in todo:
        code = v["page_polity_code"]
        dest = REPO / v["page_written"]
        job0 = f"wiki-{norm(v['unit_id'])}"
        prev = _json.loads((runner.run_dir / "agents" / job0 / "result.json").read_text())
        attempts: list[tuple[tuple[int, int, int], str, dict[str, Any], list]] = []
        all_red: list[str] = []

        for attempt in range(1, max_attempts + 1):
            # The database must reflect the page before the gates can judge it.
            subprocess.run([sys.executable, "scripts/build_database.py"], cwd=str(REPO),
                           capture_output=True, text=True, timeout=1200)
            subprocess.run([sys.executable, "scripts/write_polity_containment.py"], cwd=str(REPO),
                           capture_output=True, text=True, timeout=600)
            fails, red = _repair.run_gates_detail(codes=(code,))
            mech = [f for f in fails if f.kind == "MECHANICAL"]
            if mech:
                did = _repair.mechanical_fixes(fails)
                if did:
                    print(f"  attempt {attempt}: mechanical — {', '.join(did)}")
                    fails, red = _repair.run_gates_detail(codes=(code,))
            # A gate that is red but never names our code is NOT this page's problem to fix and NOT
            # evidence the repo is clean. Say so, and say which gates, so the distinction survives.
            unattributed = [g for g in red if not any(f.gate == g for f in fails)]
            # An arm nobody has classified produces no repair at all. Rather than growing a regex
            # list over the gates' prose -- which is what misrouted one arm over an apostrophe --
            # read the gate's source once per arm and keep the answer.
            fails = _repair.classify_unknown_arms(fails, runner)
            all_red.extend(red)
            rank = _repair.rank(fails)
            attempts.append((rank, render_page(prev), prev, fails))
            kinds = {}
            for f in fails:
                kinds[f.kind] = kinds.get(f.kind, 0) + 1
            print(f"  attempt {attempt}: {code}  failures={kinds or 'none'}  rank={rank}")
            for f in fails[:4]:
                print(f"      [{f.kind}] {f.line[:96]}")
            if not [f for f in fails if f.kind in ("ARITHMETIC", "JUDGEMENT", "UNKNOWN")]:
                v["repair_status"] = "clean" if not red else "clean_for_code"
                if unattributed:
                    print(f"      no failure names {code}, but {len(unattributed)} gate(s) are red "
                          f"on other rows: {', '.join(unattributed)}")
                break
            if attempt == max_attempts:
                v["repair_status"] = "exhausted"
                break
            res = runner.call(f"repair-{norm(v['unit_id'])}-{attempt}",
                              _repair.repair_prompt(fails, _json.dumps(prev, indent=2)),
                              WIKI_SCHEMA, refresh=True)
            if not res.ok:
                print(f"      repair call failed: {res.error}")
                v["repair_status"] = "exhausted"
                break
            cand = res.result
            if _repair.is_arithmetic_only(fails):
                cand, moved = _repair.enforce_arithmetic_narrowness(prev, cand)
                if moved:
                    print(f"      arithmetic mode: restored prose the repair rewrote "
                          f"({', '.join(moved)})")
            prev = cand
            dest.write_text(render_page(prev), encoding="utf-8")

        # Keep the BEST attempt, not the last.
        best_rank, best_text, _best, best_fails = min(attempts, key=lambda t: t[0])
        if best_text != dest.read_text(encoding="utf-8"):
            dest.write_text(best_text, encoding="utf-8")
            print(f"  restored the best-ranked attempt (rank={best_rank}), not the last")
        v["repair_attempts"] = str(len(attempts))
        v["repair_rank"] = str(best_rank)
        v["repair_remaining"] = " | ".join(f"[{f.kind}] {f.line[:80]}" for f in best_fails)
        write_ledger(ledger)
        v["repair_gates_red"] = " | ".join(sorted(set(all_red)))
        print(f"  {code}: {v['repair_status']} after {len(attempts)} attempt(s); "
              f"{len(best_fails)} failure(s) naming {code}"
              + (f"; {len(set(all_red))} gate(s) red overall" if all_red else "; no gate red"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", required=True)
    ap.add_argument("--limit", type=int, default=0, help="units per cycle (0 = all undecided)")
    ap.add_argument("--cycles", type=int, default=1)
    ap.add_argument("--model", default=None)
    ap.add_argument("--effort", default=None)
    ap.add_argument("--refresh-convention", action="store_true",
                    help="re-decide the country's span/container convention (otherwise banked)")
    ap.add_argument("--refresh", action="store_true", help="ignore the fingerprint cache")
    # Targeted re-runs: re-ask one unit after changing its evidence or the prompt, without paying
    # for the whole country to reach it alphabetically.
    ap.add_argument("--only", nargs="*", default=None, metavar="UNIT_ID",
                    help="restrict to these admin_unit_ids")
    ap.add_argument("--repair-stage", action="store_true",
                    help="repair authored pages against the gates, narrowly, keeping the best attempt")
    ap.add_argument("--wiki-stage", action="store_true",
                    help="author the wiki page for each create_new proposal that has a polygon route")
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
    iso = resolve_iso(A.country, pols, runner)
    if not iso:
        print(f"FAIL: {A.country!r} did not resolve to an iso3 in the polity table, so the "
              f"candidate set cannot be assembled. The repo's crosswalks did not answer it and the "
              f"resolution call declined to guess, which is the intended behaviour: a wrong iso3 "
              f"yields plausible verdicts built on another country's rows. Resolve it by adding the "
              f"label to a crosswalk the repo already builds, not to a list inside this harness.")
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

    convention = country_convention(A, runner, pols, iso, units) if units else None

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
        # A rejection must reach the next cycle, or it re-proposes the same span.
        prior_reject = [f"{x['unit_id']}: {x.get('concerns', '')[:150]}"
                        for x in ledger.values()
                        if x.get("country") == A.country
                        and "HARNESS REJECTION" in x.get("concerns", "")]
        siblings = [f"{v['unit_id']} -> {v['verdict']}"
                    f"{' ' + v['matched_polity_code'] if v['matched_polity_code'] else ''}"
                    for v in ledger.values()
                    if v.get("country") == A.country and v.get("verdict")
                    and v["verdict"] != "insufficient_evidence"]
        for u in batch:
            ev = build_evidence(u, pols, iso, feats, wide=wide,
                                sibling_verdicts=siblings + prior_reject[:6],
                                convention=convention)
            job = f"cycle{cycle:02d}-{norm(u['unit_id'])}"
            res = runner.call(job, PROMPT.format(evidence=ev), SCHEMA, refresh=A.refresh)
            if not res.ok:
                print(f"  FAIL  {u['unit_id']:24} {res.error}")
                continue
            v = res.result
            # THE SPAN CHECK THE PROMPT COULD NOT ENFORCE. Ten of Spain's 47 verdicts proposed the
            # extract's own coverage as the span despite the instruction forbidding it, so this is
            # verified rather than requested: endpoints sitting on the data's own first and last
            # year are an extract-defined span, which must be re-spanned whenever the extract grows.
            prop = v.get("proposed") or {}
            if v["verdict"] == "create_new" and prop and prop.get("start_year") == u["y0"] \
                    and prop.get("end_year") in (u["y1"], u["y1"] + 1):
                print(f"  REJECTED  {u['unit_id']:24} span "
                      f"{prop.get('start_year')}-{prop.get('end_year')} is the extract's own "
                      f"coverage ({u['y0']}-{u['y1']}), not an administrative fact")
                v = {**v, "verdict": "insufficient_evidence", "confidence": "low",
                     "proposed": None, "matched_polity_code": None,
                     "concerns": (v.get("concerns") or []) + [
                         f"HARNESS REJECTION: proposed span equals this extract's coverage "
                         f"{u['y0']}-{u['y1']}. Give the span a basis in the administration's "
                         f"history, or say what evidence is missing."]}
            # MERGE, never replace. Stage 1 used to assign a fresh dict, which silently dropped
            # the polygon_* and page_* fields a later stage had written -- so `--refresh` on stage 1
            # un-did stage 2, and stage 3 then skipped that unit and worked on a different one.
            row = dict(ledger.get(u["unit_id"], {}))
            row.update({
                "unit_id": u["unit_id"], "country": A.country, "admin_name": u["admin_name"],
                "verdict": v["verdict"], "matched_polity_code": v.get("matched_polity_code") or "",
                "proposed_json": json.dumps(v["proposed"], sort_keys=True) if v.get("proposed") else "",
                "confidence": v["confidence"], "reasoning": v["reasoning"],
                "evidence_used": " | ".join(v.get("evidence_used", [])),
                "concerns": " | ".join(v.get("concerns", [])),
                "cycle": str(cycle), "model": model, "effort": effort,
                "decided_at": utc_now()})
            # A changed verdict invalidates what the later stages built on it.
            if row.get("verdict") != v["verdict"]:
                for k in ("polygon_route", "polygon_source_slug", "polygon_feature_id",
                          "polygon_detail", "polygon_confidence", "polygon_reasoning",
                          "page_written", "page_polity_code"):
                    row[k] = ""
            ledger[u["unit_id"]] = row
            write_ledger(ledger)
            tag = "cached" if res.cached else "fresh"
            extra = v.get("matched_polity_code") or (
                v["proposed"]["polity_name"] if v.get("proposed") else "")
            print(f"  {v['verdict']:22} {u['unit_id']:24} {v['confidence']:7} {extra[:34]:36}({tag})")

    if A.polygon_stage:
        run_polygon_stage(A, runner, pols, iso, feats, ledger)
    if A.wiki_stage:
        run_wiki_stage(A, runner, ledger)
    if A.repair_stage:
        run_repair_stage(A, runner, ledger)

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
