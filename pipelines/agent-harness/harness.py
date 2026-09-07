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
import fcntl
import functools
import collections
import csv
import json
import os
import re
import subprocess
import sys
import unicodedata

from jsonschema import Draft202012Validator
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
                 "repair_gates_red", "coverage_json", "coverage_ok")

RESIDUAL_MARKERS = ("RESID", "OTHER", "NATIONAL", "UNKNOWN", "TOTAL", "REST")


def nuts_basis() -> dict[str, str]:
    """code -> the `basis` recorded for its name, which says WHICH vocabulary the code belongs to.

    Not decoration. A code's shape suggests a system and can be wrong about it: PTAV's basis reads
    "the 18 mainland districts (Wikipedia, Districts of Portugal); NOT an official code list", yet
    every Portuguese unit came back named "(NUTS region of Portugal)" and dated to the 1989 NUTS
    classification -- stranding 118 years of district-level data the source actually reports. The
    panel's own `admin_level` column says "NUTS" for both of Portugal's layers, so it cannot settle
    it either. The basis can.
    """
    if not NUTS_XW.is_file():
        return {}
    with NUTS_XW.open(newline="", encoding="utf-8") as fh:
        return {r["nuts_id"]: r.get("basis", "") for r in csv.DictReader(fh)}


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


# unit_ids this process has modified. Only these are written over what is on disk.
DIRTY: set[str] = set()


def mark(unit_id: str) -> None:
    DIRTY.add(unit_id)


def write_ledger(rows: dict[str, dict[str, str]]) -> None:
    """Merge our rows into whatever is on disk now, under an exclusive lock.

    A whole-file write from an in-memory copy loaded at startup is only safe while one run exists.
    With 444 units across 26 countries, running them one country at a time is hours of wall clock
    for no reason -- but two concurrent runs would each write their own stale snapshot and silently
    drop the other's rows, which is the same failure that once turned a request for Alaska into a
    California page, one process further out.

    So the write is a read-modify-write under flock: re-read the file, lay our rows over it, write
    atomically. Our rows win on conflict, which is correct because we are the run that just decided
    them. Any unit_id we have never touched is preserved byte for byte.
    """
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    lock = LEDGER.with_suffix(".lock")
    with open(lock, "w", encoding="utf-8") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            merged = read_ledger()          # whatever any concurrent run has committed
            # ONLY THE ROWS WE ACTUALLY CHANGED. `merged.update(rows)` was the first version, and
            # `rows` is this process's WHOLE ledger as loaded at startup -- so a long-running country
            # overwrote every other country's fresh rows with its own stale copies of units it never
            # touched. 163 pages existed on disk while the ledger recorded 51, and the difference was
            # this line. "Ours are newer by construction" is only true of what we modified.
            merged.update({k: v for k, v in rows.items() if k in DIRTY})
            ordered = [{f: merged[k].get(f, "") for f in LEDGER_FIELDS} for k in sorted(merged)]
            # A distinct temp name per process: two runs sharing one .tmp would interleave writes
            # and os.replace whichever finished last, which is a torn file, not a merge.
            tmp = LEDGER.with_suffix(f".{os.getpid()}.tmp")
            with open(tmp, "w", newline="\n", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(LEDGER_FIELDS), lineterminator="\n")
                w.writeheader()
                w.writerows(ordered)
            os.replace(tmp, LEDGER)      # atomic: a killed run must not truncate the ledger
            rows.clear()
            rows.update(merged)          # the caller's view now includes everyone else's rows
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


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


def double_claim_objection(v: dict[str, Any], unit: dict[str, Any],
                           ledger: dict[str, dict[str, str]], country: str) -> str | None:
    """Is another unit of this country already matched to the same polity for overlapping years?

    Two reporting units cannot both BE the same territory in the same years -- whichever is wrong,
    the data is double-counted into one polity. AUS-VICTORIA came back matching VIC-1851-1900 for
    1860-1899 and then AUS-1901-2025 -- the whole of Australia -- for 1901-2022, which every other
    Australian state could equally claim.

    Checked structurally rather than by polity_type, because the data defeats type-checking here:
    VIC-1851-1900 is itself typed `national` while its sibling AUWA-1829-1900 is typed `colonial`,
    so "a subnational unit matched a national row" does not separate the good case from the bad one.
    Whether the collision means this unit is wrong or the other one is, is a judgement, so it is
    stated and handed back.
    """
    mine = [s for s in (v.get("coverage") or [])
            if s.get("disposition") == "matched" and s.get("polity_code")]
    if not mine:
        return None
    clashes: list[str] = []
    for other in ledger.values():
        if other.get("country") != country or other.get("unit_id") == unit["unit_id"]:
            continue
        try:
            theirs = json.loads(other.get("coverage_json") or "[]")
        except json.JSONDecodeError:
            continue
        for a in mine:
            for b in theirs:
                if b.get("disposition") != "matched" or b.get("polity_code") != a["polity_code"]:
                    continue
                lo = max(a["start_year"], b["start_year"])
                hi = min(a["end_year"], b["end_year"])
                if lo <= hi:
                    clashes.append(
                        f"{a['polity_code']} is claimed for {lo}-{hi} by BOTH this unit and "
                        f"{other['unit_id']} ({other.get('admin_name', '')}).")
    if not clashes:
        return None
    uniq = sorted(set(clashes))
    return ("\n".join(uniq[:6]) + "\n\nTwo reporting units cannot both BE the same territory in "
            "the same years -- the data would be summed into one polity twice. Either this unit is "
            "a different territory that needs its own polity, or the years belong to only one of "
            "them. Note that matching a unit to its own CONTAINER has this shape: every sibling "
            "could claim the container equally, which is what makes it wrong.")


def limit_hit(res, where: str, ledger: dict[str, dict[str, str]] | None = None) -> bool:
    """True when a job failed on a usage limit, in which case the caller must stop.

    Added to stage 1 first and only stage 1, which was half a fix: Australia's six units each
    failed separately through stages 2 and 3 with `usage limit reached; resets 3:50pm`, because
    those loops just `continue`d. Every remaining unit fails identically until the reset, so
    carrying on only buries the cause under repetitions of itself.
    """
    if res.ok or not res.error or "usage limit" not in res.error:
        return False
    print(f"\n  STOPPING {where}: {res.error}. Re-run after the reset; "
          f"completed work is already banked.")
    if ledger is not None:
        write_ledger(ledger)
    return True


def coverage_objection(v: dict[str, Any], unit: dict[str, Any],
                       pols: list[dict[str, str]]) -> str | None:
    """Do the coverage segments account for every data year, and does each matched code cover its own?

    Arithmetic, so it is checked rather than asked. The remedy is not: which polity should carry a
    stranded stretch, or whether one must be created, is the judgement the stage exists for. So the
    gap is stated and handed back.

    This is what makes "all the data is matched" a measurable claim instead of an impression. Before
    the field existed, five of fifteen match_existing verdicts silently stranded years -- 122 of them
    for AUS-QUEENSLAND -- and nothing in the ledger showed it.
    """
    segs = v.get("coverage") or []
    if not segs:
        return "No `coverage` segments were given, so no year of this unit's data is accounted for."
    u0, u1 = unit["y0"], unit["y1"]
    by_code = {p["polity_code"]: p for p in pols}
    problems: list[str] = []

    for s in segs:
        if s["start_year"] > s["end_year"]:
            problems.append(f"Segment {s['start_year']}-{s['end_year']} runs backwards.")
        if s["disposition"] == "back_cast" and not s.get("polity_code"):
            problems.append(f"Segment {s['start_year']}-{s['end_year']} is `back_cast` but names no "
                            f"polity_code. A reconstruction is still FOR some territory; say which, "
                            f"or the years are not routed at all.")
        if s["disposition"] == "matched":
            code = s.get("polity_code")
            if not code:
                problems.append(f"Segment {s['start_year']}-{s['end_year']} is `matched` but names "
                                f"no polity_code.")
            elif code not in by_code:
                problems.append(f"Segment {s['start_year']}-{s['end_year']} names {code}, which is "
                                f"not a polity_code in the table.")
            else:
                p = by_code[code]
                p0, p1 = int(p["start_year"]), int(p["end_year"])
                # end_year is EXCLUSIVE on a polity; the segment's end_year is an inclusive data year
                if s["start_year"] < p0 or s["end_year"] >= p1:
                    problems.append(
                        f"Segment {s['start_year']}-{s['end_year']} is matched to {code}, whose own "
                        f"span is {p0}-{p1} (end_year EXCLUSIVE, so it carries data through "
                        f"{p1 - 1}). Those years are not inside it.")

    ordered = sorted(segs, key=lambda s: s["start_year"])
    if ordered[0]["start_year"] > u0:
        problems.append(f"Data starts at {u0} but the first segment starts at "
                        f"{ordered[0]['start_year']}: {ordered[0]['start_year'] - u0} year(s) "
                        f"unaccounted for.")
    if ordered[-1]["end_year"] < u1:
        problems.append(f"Data ends at {u1} but the last segment ends at "
                        f"{ordered[-1]['end_year']}: {u1 - ordered[-1]['end_year']} year(s) "
                        f"unaccounted for.")
    for a, b in zip(ordered, ordered[1:]):
        if b["start_year"] > a["end_year"] + 1:
            problems.append(f"Gap between {a['end_year']} and {b['start_year']}: "
                            f"{b['start_year'] - a['end_year'] - 1} year(s) unaccounted for.")
        elif b["start_year"] <= a["end_year"]:
            problems.append(f"Segments {a['start_year']}-{a['end_year']} and "
                            f"{b['start_year']}-{b['end_year']} overlap.")
    # A TILING IS NOT A ROUTING. Portugal's 23 units tiled their spans perfectly and left
    # 1870-1988 `unroutable` -- 118 years, about 90% of the country's 341,508 rows -- and recorded
    # coverage_ok=yes. `unroutable` is for years nothing could carry; a reporting unit that HAS data
    # for a year had a territory in that year, whatever the statistical classification was called.
    unroutable = sum(s["end_year"] - s["start_year"] + 1
                     for s in segs if s.get("disposition") == "unroutable")
    total = u1 - u0 + 1
    if unroutable and unroutable / total > 0.10:
        problems.append(
            f"{unroutable} of this unit's {total} data years ({unroutable / total:.0%}) are marked "
            f"`unroutable`. The source reports values for those years, so the territory existed and "
            f"was being measured. `unroutable` is for a year nothing could ever carry -- not for a "
            f"year before the classification that currently names the unit was invented. If the "
            f"territory existed under an earlier administration, the polity's span starts then and "
            f"the classification is just its current label; if a different territory reported those "
            f"years, name it. Do not leave measured data with no polity.")
    if not problems:
        return None
    return ("\n".join(problems) + f"\n\nThe segments must tile this unit's whole data span "
            f"{u0}-{u1} with no gap and no overlap. Every year of data has to be accounted for -- by "
            f"a polity that covers it, by a proposal, or by an explicit `unroutable` with a reason. "
            f"Fix only the coverage; leave the verdict alone unless the gap changes it.")


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
        a(f"  earliest possible   {convention['system_start_year']} — a FLOOR for the system, NOT "
          f"this unit's start ({convention.get('system_start_basis','')[:80]})")
        a(f"  start rule (DEFAULT) {convention.get('unit_start_rule','')[:140]}")
        exc = convention.get("unit_start_exceptions") or []
        if exc:
            a(f"  DEPARTURES from that rule ({len(exc)}) — check whether THIS unit is one:")
            for e in exc:
                a(f"    {e['units'][:60]:62} start {e['start_year']}  ({e['basis'][:70]})")
        a("  The rule is a default. If this unit's own history differs — it was created later, or "
          "split from another unit — depart from it and say why in span_basis.")
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
    if unit.get("method_profile"):
        a(f"  HOW VALUES WERE MADE  {unit['method_profile'][:170]}")
        a(f"     A `scaled`, `interpolated` or `fallback` method means the value was allocated or "
          f"reconstructed. A BLANK method means only that the source recorded no derivation for it "
          f"— it does NOT establish that this unit was observed, because the source may have done "
          f"its own aggregation before publishing. Portugal's five NUTS-2 regions are 100% blank "
          f"and run from 1870, and NUTS did not exist until 1989: blank there means passed through, "
          f"not measured. What settles it is the unit's own existence date, not this column. Where "
          f"data predates the unit, that is `back_cast` — the data is FOR this territory without "
          f"the territory having existed yet — and NOT `unroutable`.")
    if unit.get("official_name"):
        a(f"  OFFICIAL NAME      {unit['official_name']!r}   "
          f"(data/final/nuts_code_names.csv -- authoritative; do NOT resolve the code from memory)")
        basis = unit.get("name_basis")
        if basis:
            # The basis says WHICH vocabulary the code belongs to, and that often refutes what the
            # code looks like: PTAV's basis reads "the 18 mainland districts ... NOT an official code
            # list", yet Portugal's units were all named "(NUTS region of Portugal)" and dated to the
            # 1989 NUTS classification, stranding 118 years of district-level data.
            a(f"  NAME PROVENANCE    {basis[:150]}")
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
                                         "admin_level", "year", "indicator", "value_canonical",
                                         "method"])
    df = df[(df.country_clean == country) & df.value_canonical.notna()]
    if df.empty:
        return []
    src = pd.read_parquet(PANEL, columns=["country_clean", "source"])
    source = src[src.country_clean == country]["source"].mode()
    # HOW each value was produced, per unit and era. This is what separates a territory the source
    # OBSERVED from one it reconstructs: Colombia is 74% interpolated_scaled, Spain 97.5% blank.
    # `if "method" in df.columns` was the first version, and `method` was not among the columns
    # read above -- so the guard was always False, every profile came out empty, and nothing looked
    # broken. An absent column is now stated rather than skipped.
    meth = None
    if "method" not in df.columns:
        print("  NOTE: the panel has no `method` column, so observation cannot be separated from "
              "reconstruction and `back_cast` coverage cannot be grounded")
    else:
        m = df.assign(_m=df["method"].fillna("").replace("", "(observed/blank)"))
        meth = (m.groupby(["admin_unit_id", "_m"]).size()
                 .groupby(level=0, group_keys=False)
                 .apply(lambda s: (s / s.sum() * 100).round(1)))
    g = df.groupby("admin_unit_id").agg(
        admin_name=("admin_name_clean", "first"), admin_level=("admin_level", "first"),
        y0=("year", "min"), y1=("year", "max"), rows=("year", "size"),
        indicators=("indicator", lambda s: ", ".join(sorted(set(s)))))
    out = []
    for uid, r in g.sort_index().iterrows():
        xw, bs = nuts_names(), nuts_basis()
        key = str(r["admin_name"]).replace("_", "")
        official = xw.get(key, "")
        prof = ""
        if meth is not None and uid in meth.index.get_level_values(0):
            prof = ", ".join(f"{k}={v}%" for k, v in
                             meth.loc[uid].sort_values(ascending=False).items() if v >= 1.0)
        out.append({"unit_id": uid, "country": country, "admin_name": r["admin_name"],
                    "official_name": official, "name_basis": bs.get(key, ""),
                    "method_profile": prof,
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
- `system_start_year` is a FLOOR, not a value every unit copies. It is the earliest year any unit of
  this system can begin -- a documented reform or founding, not the first year this extract happens
  to cover. Spain's 50 provinces were all created at once in 1833, so there the floor is also every
  unit's start. US states were admitted between 1787 and 1959, so a single number would span
  California from the wrong year. Give the floor AND `unit_start_rule`: how an individual unit's own
  start is found within the system.
- `unit_start_exceptions` lists every unit that does NOT follow that rule. Re-read your own
  `system_start_basis` before returning an empty list: Spain's answer wrote "(later 50, with the
  1927 split of the Canary Islands)" in its basis and then said "all units begin at the floor, no
  per-unit variation is needed" in its rule. Las Palmas was consequently dated 1833, 94 years before
  it existed. The evidence was in the same object as the claim that contradicted it.
- `open_end_year` is EXCLUSIVE and must be ONE value for every still-current unit. Unlike the start,
  this genuinely is country-wide, because a unit cannot outlive its container. Prefer the containing
  national row's own end_year COLUMN; a round number like 2100 asserts a span nobody has evidence for.
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
        # A banked decision is still held to the CURRENT contract. Tightening the schema is how the
        # US answer's missing system_start_basis was caught -- an unjustified 1959 floor that would
        # have spanned every state from the year the 50th joined. Without this, the old answer would
        # be reused forever and the tightening would reach only countries not yet decided.
        errs = list(Draft202012Validator(
            json.loads(CONVENTION_SCHEMA.read_text(encoding="utf-8"))).iter_errors(c))
        if errs:
            print(f"  banked convention for {A.country} no longer satisfies the schema "
                  f"({errs[0].message[:70]}) — re-deciding")
        else:
            print(f"  convention: {c['system_name'][:56]}   (banked; --refresh-convention to "
                  f"re-decide)")
            print(f"    floor {c['system_start_year']}   open end_year {c['open_end_year']} "
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
        starts = sorted({int(by_code[e["code"]]["start_year"]) for e in c["container_chain"]})
        if starts and c["system_start_year"] < starts[0]:
            return (f"system_start_year is {c['system_start_year']}, but the earliest container era "
                    f"in the chain begins {starts[0]}. A unit cannot be contained before its "
                    f"container exists, so no unit of this country can start earlier than "
                    f"{starts[0]} however old its territory is. The US answer gave a 1787 floor "
                    f"against a chain beginning USA-1800-1803, and eleven states were then proposed "
                    f"1787-1792 start years that the wiki stage had to truncate to 1800 on its own. "
                    f"Either the floor is {starts[0]}, or the chain is missing an earlier era — say "
                    f"which in system_start_basis.")
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
    def page_on_disk(v: dict[str, str]) -> bool:
        rel = v.get("page_written") or ""
        return bool(rel) and (REPO / rel).is_file()

    # A unit whose PAGE already exists needs no route: the route was used to write it. Spain spent
    # 45 stage-2 calls re-routing units that were already authored -- 49 of its 51 had pages -- and
    # stage 3 then correctly reported nothing to author. The page is the artefact, so it is the
    # thing to check, exactly as the wiki stage checks it.
    todo = [v for v in ledger.values()
            if v.get("country") == A.country and v.get("verdict") == "create_new"
            and not v.get("polygon_route") and not page_on_disk(v)
            and (scope is None or v["unit_id"] in scope)]
    if not todo:
        print("\nstage 2 (polygon): nothing to route")
        return
    slugs = polygon_slugs()
    existing_pages = existing_territory_pages(pols, iso)
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
            if limit_hit(res, f"{A.country} stage 2", ledger):
                return
            continue
        r = res.result

        # `new_source_needed` NAMING AN ALREADY-REGISTERED SLUG is a contradiction, and it
        # propagated: A Coruña was routed new_source_needed while its own detail said mapspain-ign
        # was "already registered in scripts/sources.yaml" -- which it is, id_column cpro -- and
        # stage 3 then wrote the route name into the page's polygon_source field. Whether a slug is
        # registered is a fact; which route is right is a judgement, so this is handed back.
        for retry in range(2):
            obj = None
            cand = ((r.get("candidate_new_source") or {}).get("name") or "").strip()
            if r["route"] == "registered_source_unfetched" and r.get("source_slug") not in slugs:
                obj = (f"The route is `registered_source_unfetched`, which means the source IS "
                       f"registered — but source_slug {r.get('source_slug')!r} is not among the "
                       f"registered slugs: {', '.join(sorted(slugs))}. If the source is not "
                       f"registered at all, that is `new_source_needed`.")
            if r["route"] == "new_source_needed" and cand in slugs:
                obj = (f"The route is `new_source_needed`, but {cand!r} is ALREADY registered in "
                       f"scripts/sources.yaml, so it needs no new registration. That leaves a fork, "
                       f"and you must pick the right side of it:\n"
                       f"  (a) {cand!r} DOES cover this territory — then the route is "
                       f"`registered_source_feature` with source_slug {cand!r} and the feature "
                       f"named; if its file is not present locally or its licence is unchecked, say "
                       f"so and leave the geometry unattached.\n"
                       f"  (b) {cand!r} does NOT cover this country at all — then it is simply the "
                       f"wrong source and naming it was a mistake; propose one whose extent "
                       f"includes this territory, or answer `none_available`.\n"
                       f"sources.yaml records no extent for any source, so nothing here can decide "
                       f"this for you. A French region was proposed `mapspain-ign`, which is "
                       f"Spain-only, and switching its route would have attached another country's "
                       f"boundary — the exact defect validate_polygons exists to catch.")
            elif r["route"] == "registered_source_feature" and not (
                    r.get("feature_id") or "").strip():
                obj = (f"The route is `registered_source_feature`, which asserts that one specific "
                       f"feature IS this territory's boundary — but no feature_id is given, so the "
                       f"claim cannot be checked. If the source's file is not present locally, that "
                       f"is `registered_source_unfetched`: name the slug and say what must be "
                       f"fetched. Twenty Spanish units took this route naming mapspain-ign with an "
                       f"empty feature_id, and "
                       f"data/geodata/mapspain-ign/provinces.gpkg does not exist here.")
            elif r["route"] == "registered_source_feature" and r.get("source_slug") not in slugs:
                obj = (f"The route is `registered_source_feature` but source_slug "
                       f"{r.get('source_slug')!r} is not registered. Registered slugs are: "
                       f"{', '.join(sorted(slugs))}.")
            if not obj:
                break
            print(f"  REJECT {v['unit_id']:23} {obj[:88]}")
            res = runner.call(f"{job}-obj{retry + 1}",
                              POLYGON_PROMPT.format(evidence=ev)
                              + f"\n\nA PREVIOUS ANSWER WAS REJECTED\n{'-' * 30}\n{obj}\n"
                                f"Fix only what the objection names.",
                              POLYGON_SCHEMA, refresh=True)
            if not res.ok:
                print(f"  FAIL  {v['unit_id']:24} objection retry: {res.error}")
                r = None
                break
            r = res.result
        if r is None:
            continue

        v["polygon_route"] = r["route"]
        v["polygon_source_slug"] = r.get("source_slug") or ""
        v["polygon_feature_id"] = r.get("feature_id") or ""
        v["polygon_detail"] = _json.dumps(
            {k: r.get(k) for k in ("construction", "candidate_new_source", "vintage_risk")
             if r.get(k)}, sort_keys=True)
        v["polygon_confidence"] = r["confidence"]
        mark(v["unit_id"])
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

THE POLITY CODE IS YOURS TO CHOOSE, against the precedent below. It is not a rule this harness can
check: an earlier version of this prompt asserted that a code must begin with the country's iso3,
and the table refutes it -- ALK-1867-1959 (Territory of Alaska) and AUWA-1829-1900 (Western
Australia) do not. What IS true is measured from the table and stated here:

{code_precedent}

Follow the dominant pattern unless the unit is a historical territory with a name of its own, which
is what the bespoke codes are; if you depart from it, say why in `decisions`. `end_year` is
EXCLUSIVE, and the years in the code must equal the years in the frontmatter -- a gate checks that.

`polygon_source` TAKES A REGISTERED SLUG OR `none` — NEVER A ROUTE NAME. The routing decision below
gives you a `polygon_route`, which is a category of answer (`registered_source_feature`,
`registered_source_unfetched`, `new_source_needed`, `none_available`, `construct_from_registered`).
Those are not sources. `polygon_source: new_source_needed` and `polygon_source:
registered_source_unfetched` have both been written here and both were rejected by
validate_declared_sources. When the route is `registered_source_unfetched`, the slug IS the source
(it is registered, just not fetched here) and `polygon_status` is `unassigned`; when the route is
`new_source_needed` or `none_available`, `polygon_source` is `none` and the source you would want
belongs in an open question.

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


def code_precedent(pols: list[dict[str, str]], iso: str) -> str:
    """The code shapes actually in the table, counted now rather than pinned in the prompt.

    Pinned counts go stale silently and this prompt already carried one claim the table refutes.
    """
    sub = [p for p in pols if p["polity_type"] == "subnational"]
    kinds: dict[str, list[str]] = {}
    for p in sub:
        c, i3 = p["polity_code"], p["iso3_code"]
        parts = len(c.split("-"))
        if c.startswith(i3 + "-") and parts == 4:
            k = "<ISO3>-<SUBUNIT>-<start>-<end>"
        elif c.startswith(i3 + "-"):
            k = "<ISO3>-<start>-<end>"
        elif parts == 4:
            k = "<BESPOKE>-<SUBUNIT>-<start>-<end>"
        else:
            k = "<BESPOKE>-<start>-<end>"
        kinds.setdefault(k, []).append(c)
    lines = [f"  Of {len(sub)} subnational rows in the table:"]
    for k, cs in sorted(kinds.items(), key=lambda kv: -len(kv[1])):
        eg = ", ".join(sorted(cs)[:3])
        lines.append(f"    {len(cs):3}  {k:34} e.g. {eg}")
    mine = sorted(p["polity_code"] for p in sub if p["iso3_code"] == iso)
    lines.append(f"  Existing subnational codes for {iso} ({len(mine)}): "
                 + (", ".join(mine[:10]) + (" ..." if len(mine) > 10 else "") if mine
                    else "none -- this country sets its own precedent"))
    return "\n".join(lines)


def polygon_slugs() -> set[str]:
    """The polygon source slugs registered in scripts/sources.yaml, read rather than listed here."""
    import yaml as _yaml
    with (REPO / "scripts" / "sources.yaml").open(encoding="utf-8") as fh:
        return set((_yaml.safe_load(fh) or {}).get("sources", {}).keys())


def bad_polygon_source(page: dict[str, Any], slugs: set[str]) -> str | None:
    """`polygon_source` must name a registered slug or be exactly `none`.

    A ROUTE NAME IS NOT A SOURCE. A Coruña's page came back with
    `polygon_source: new_source_needed` -- stage 2's route enum written into the field that names a
    source -- and validate_declared_sources arm D rejected it. Which slugs are registered is a fact
    in sources.yaml, so it is checked here; but the remedy depends on whether a source exists for
    this territory at all, which is stage 2's judgement, so the objection is handed back.
    """
    fm = page.get("frontmatter") or {}
    v = fm.get("polygon_source") or page.get("polygon_source")
    if v in (None, "", "none", "null") or v in slugs:
        return None
    routes = {"registered_source_feature", "new_source_needed", "none_available",
              "constructed_union"}
    extra = (" That is a polygon ROUTE, not a source. A route says where a boundary would come "
             "from; polygon_source names the registered source it actually came from."
             if v in routes else "")
    return (f"`polygon_source: {v}` names nothing.{extra} It must be one of the slugs registered in "
            f"scripts/sources.yaml -- {', '.join(sorted(slugs))} -- or exactly `none` when no "
            f"geometry is attached. If the boundary is not attached yet, `none` is the honest value, "
            f"and the reason belongs in an open question.")


def chain_edges(pols: list[dict[str, str]]) -> dict[str, tuple[set[str], set[str]]]:
    """code -> (its declared predecessors, its declared successors), from the built table."""
    def split(s: str) -> set[str]:
        return {x.strip() for x in (s or "").replace("[", "").replace("]", "").split(",")
                if x.strip() and x.strip() != "NA"}
    return {p["polity_code"]: (split(p.get("predecessor", "")), split(p.get("successor", "")))
            for p in pols}


def unreciprocated(page: dict[str, Any], edges: dict[str, tuple[set[str], set[str]]]) -> str | None:
    """State any chain edge this page asserts that its counterpart does not answer.

    A FACT, so it is checked rather than asked -- but the REMEDY is a judgement and is left to the
    agent. Alaska is the case that showed why: the new ALK-1959-2025 page declared
    `predecessor: [ALK-1867-1959]`, and ALK-1867-1959 declares `successor: [USA-1959-2025]` -- the
    whole country, not the state. Reciprocating automatically would give the territory two
    successors and quietly decide which reading is right. Refusing the edge outright would throw
    away a claim that is probably correct. Both are decisions about history, so the objection is
    handed back with the counterpart's actual fields shown.

    It matters because validate_chain_integrity baselines asymmetry BIDIRECTIONALLY: 84
    predecessor-only edges where the baseline is 83 fails CI, so one unreciprocated edge added by
    this harness turns the whole run red.
    """
    fm = page.get("frontmatter") or {}
    def listed(key: str) -> list[str]:
        v = fm.get(key) or page.get(key) or []
        return [v] if isinstance(v, str) and v else list(v)

    problems = []
    for code in listed("predecessor"):
        if code not in edges:
            continue                       # a dead target is a different arm, and gated separately
        if page["polity_code"] not in edges[code][1]:
            problems.append(f"This page declares `predecessor: [{code}]`, but {code} declares "
                            f"`successor: {sorted(edges[code][1]) or '[]'}` — not this row.")
    for code in listed("successor"):
        if code not in edges:
            continue
        if page["polity_code"] not in edges[code][0]:
            problems.append(f"This page declares `successor: [{code}]`, but {code} declares "
                            f"`predecessor: {sorted(edges[code][0]) or '[]'}` — not this row.")
    if not problems:
        return None
    return ("\n".join(problems) + "\n\nvalidate_chain_integrity counts one-directional edges "
            "against a baseline in BOTH directions, so an edge only this page asserts fails the "
            "gate. You cannot edit the other page. So either drop the claim, or keep it and record "
            "an open question that names the other page and the exact edit it needs — but do not "
            "leave the asymmetry unremarked.")


def existing_territory_pages(pols: list[dict[str, str]], iso: str) -> list[tuple[str, str]]:
    """(code, name) for pages already representing a territory of this country."""
    return [(p["polity_code"], p["polity_name"]) for p in pols if p["iso3_code"] == iso]


def duplicate_territory_objection(page: dict[str, Any], unit: dict[str, Any],
                                  existing: list[tuple[str, str]]) -> str | None:
    """Does a page already exist for the territory this one is about?

    A polity_code clash is refused and re-asked, which is right -- but it means a SECOND page for
    the same province can be created under a different code, and that is worse than a clash because
    nothing rejects it. It happened for real: runs whose ledger rows were clobbered left 35 authored
    pages unclaimed, and 8 of them could not be matched back to their verdict, so a re-run would
    have authored the same territories again under new codes.

    Name similarity is the only signal available before the page is written, so the finding is
    handed back rather than acted on: two provinces can legitimately share a name stem, and only
    the author can say whether these are one territory or two.
    """
    def core(s: str) -> str:
        # the distinctive part, before any parenthetical qualifier
        return norm(re.sub(r"\(.*?\)", "", str(s)))

    mine = core(page.get("polity_name", "")) or core(unit.get("official_name") or "")
    if len(mine) < 4:
        return None
    hits = [(c, n) for c, n in existing
            if c != page.get("polity_code") and core(n) and len(core(n)) >= 4
            and (core(n) == mine or core(n) in mine or mine in core(n))]
    if not hits:
        return None
    listed = "; ".join(f"{c} ({n})" for c, n in hits[:4])
    return (f"A page already exists for a territory whose name matches this one: {listed}. Two "
            f"polities must not represent the same territory over the same years -- data would be "
            f"counted into both. Either that page IS this reporting unit, in which case this should "
            f"have been `match_existing` and you should say so in `open_questions` rather than "
            f"author a second page; or they are genuinely different territories, in which case say "
            f"in `decisions` what distinguishes them. Do not silently create the second one.")


def run_wiki_stage(A, runner, ledger, pols, iso) -> None:
    import json as _json
    scope = set(A.only) if A.only else None
    def page_missing(v: dict[str, str]) -> bool:
        """A recorded page whose FILE is absent counts as not written.

        The file is the artefact -- this repo builds the polity table from the wiki -- so a ledger
        row pointing at a page that does not exist is a stale claim, and trusting it means the unit
        is skipped forever. USA-CALIFORNIA carried `page_polity_code: CALI-1850-2026` from a run
        whose page was withdrawn for breaking the code convention, and California was consequently
        skipped by every later wiki pass while looking done in the ledger.
        """
        rel = v.get("page_written") or ""
        return not rel or not (REPO / rel).is_file()

    todo = [v for v in ledger.values()
            if v.get("country") == A.country and v.get("verdict") == "create_new"
            and v.get("polygon_route") and page_missing(v)
            and (scope is None or v["unit_id"] in scope)]
    if not todo:
        print("\nstage 3 (wiki): nothing to author "
              "(needs a create_new verdict that has been through the polygon stage)")
        return
    spec = page_spec_text()
    precedent = code_precedent(pols, iso)
    # TAKEN IS DECIDED BY THE WIKI, NOT THE DERIVED CSV. This repo builds the table from the wiki,
    # one row per page, so a page file is what makes a code exist. Reading the CSV instead produced
    # a FALSE clash: a page was withdrawn without rebuilding, the stale row still named the code, and
    # the unit re-authoring its own page was pushed off ESP-CO-1833-2025 onto the NUTS-derived
    # ESP-ES111-1833-2025 -- a worse name, chosen because a derived file had not caught up.
    taken = {f.stem.upper() for f in (REPO / "wiki" / "polities").glob("*.md")}
    edges = chain_edges(pols)
    slugs = polygon_slugs()
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
        prompt = WIKI_PROMPT.format(spec=spec, exemplar=exemplar, decision=decision,
                                    code_precedent=precedent)
        res = runner.call(job, prompt, WIKI_SCHEMA, refresh=A.refresh)
        if not res.ok:
            print(f"  FAIL  {v['unit_id']:24} {res.error}")
            if limit_hit(res, f"{A.country} stage 3", ledger):
                return
            continue
        page = res.result

        # A CODE COLLISION MUST NOT BE A SKIP. Whether a code is taken is a fact, not a judgement,
        # so it is checked here -- but the page it collides with belongs to another territory, and
        # silently skipping drops the polity this run was asked to create while printing a line that
        # looks like an ordinary no-op. Stated back, and asked again.
        for retry in range(2):
            code = page["polity_code"]
            mine = v.get("page_polity_code") == code
            clash = None
            if code in taken and not mine:
                other = next((p for p in pols if p["polity_code"] == code), None)
                held = (f"{other['polity_name']!r} ({other['start_year']}-{other['end_year']})"
                        if other else "a page whose row is not in the built table")
                clash = (f"polity_code {code} already has a page in wiki/polities/, held by "
                         f"{held}. That is a different territory from {v['admin_name']!r}.")
            else:
                claimed = [k for k, r in ledger.items()
                           if r.get("page_polity_code") == code and k != v["unit_id"]]
                if claimed:
                    clash = (f"polity_code {code} was already assigned in this run to "
                             f"{claimed[0]}, a different unit.")
            if not clash:
                clash = duplicate_territory_objection(page, v, existing_pages)
            if not clash:
                clash = bad_polygon_source(page, slugs)
            if not clash:
                clash = unreciprocated(page, edges)
            if not clash:
                break
            print(f"  REJECT {v['unit_id']:23} {clash.splitlines()[0][:88]}")
            res = runner.call(f"{job}-clash{retry + 1}",
                              prompt + f"\n\nA PREVIOUS ANSWER WAS REJECTED\n{'-' * 30}\n{clash}\n"
                                       f"Choose a code that is free. Change nothing else.",
                              WIKI_SCHEMA, refresh=True)
            if not res.ok:
                print(f"  FAIL  {v['unit_id']:24} clash retry: {res.error}")
                page = None
                break
            page = res.result
        if page is None:
            continue
        code = page["polity_code"]
        if code in taken and v.get("page_polity_code") != code and not (
                REPO / "wiki" / "polities" / f"{code.lower()}.md").exists():
            print(f"  FAIL  {v['unit_id']:24} could not find a free polity_code — not written")
            continue
        dest = REPO / "wiki" / "polities" / f"{code.lower()}.md"
        if dest.exists() and v.get("page_written") and not A.refresh:
            print(f"  SKIP  {code} — this unit's page already exists; --refresh to overwrite")
            continue
        dest.write_text(render_page(page), encoding="utf-8")
        v["page_written"] = str(dest.relative_to(REPO))
        v["page_polity_code"] = code
        mark(v["unit_id"])
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
                if limit_hit(res, f"{code} stage 4", ledger):
                    return
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
        mark(v["unit_id"])
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
        #
        # But ONLY on the first cycle. `--refresh --cycles 2` re-asked all 53 Spanish units twice:
        # the second pass paid for 53 more calls to re-decide units that had already returned a
        # high-confidence verdict, and did it with the WIDE candidate net, which exists to help a
        # unit that could not be decided at all. A later cycle is an escalation for what is still
        # undecided, never a repeat of what is settled -- so the filter applies from cycle 2 on
        # whatever the flag says.
        if A.refresh and cycle == 1:
            undecided = units
        else:
            undecided = [u for u in units
                         if ledger.get(u["unit_id"], {}).get("verdict")
                         in (None, "", "insufficient_evidence")]
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
        # THE SAME UNIT SHAPE MUST NOT GET DIFFERENT VERDICTS IN DIFFERENT COUNTRIES. Thirteen
        # identical <ISO3>-NATIONAL units split 11 match_existing / 2 not_a_territory, because each
        # country is decided in isolation and nothing showed how the shape had been read elsewhere.
        # Keyed on the id's own suffix, so it generalises to any repeated marker without a list of
        # markers to maintain.
        def marker(uid: str) -> str:
            return uid.split("-", 1)[1] if "-" in uid else ""

        cross: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
        for x in ledger.values():
            if x.get("verdict") and x.get("country") != A.country:
                m = marker(x["unit_id"])
                if m:
                    cross[m][x["verdict"]] += 1
        def seg_summary(row: dict[str, str]) -> str:
            try:
                segs = json.loads(row.get("coverage_json") or "[]")
            except json.JSONDecodeError:
                return ""
            return "  ".join(
                f"{s['start_year']}-{s['end_year']}:{s['disposition']}"
                f"{'=' + s['polity_code'] if s.get('polity_code') else ''}" for s in segs)

        siblings = [f"{v['unit_id']} -> {v['verdict']}"
                    f"{' ' + v['matched_polity_code'] if v['matched_polity_code'] else ''}"
                    f"{'  [' + seg_summary(v) + ']' if seg_summary(v) else ''}"
                    for v in ledger.values()
                    if v.get("country") == A.country and v.get("verdict")
                    and v["verdict"] != "insufficient_evidence"]
        for u in batch:
            same_shape = cross.get(marker(u["unit_id"]))
            shape_note = ([f"OTHER COUNTRIES' UNITS WITH THE SAME id marker "
                           f"{marker(u['unit_id'])!r}: {dict(same_shape)} — the same shape should "
                           f"not read differently here without a reason"]
                          if same_shape else [])
            ev = build_evidence(u, pols, iso, feats, wide=wide,
                                sibling_verdicts=shape_note + siblings + prior_reject[:6],
                                convention=convention)
            job = f"cycle{cycle:02d}-{norm(u['unit_id'])}"
            res = runner.call(job, PROMPT.format(evidence=ev), SCHEMA, refresh=A.refresh)
            if not res.ok:
                print(f"  FAIL  {u['unit_id']:24} {res.error}")
                if res.error and "usage limit" in res.error:
                    # Every remaining unit would fail identically until the reset. Stopping keeps
                    # the ledger honest and the cause visible; carrying on produced 56 lines of
                    # "no schema-valid result" that read as the model failing to answer.
                    print(f"\n  STOPPING {A.country}: {res.error}. "
                          f"Re-run after the reset; decided units are already banked.")
                    write_ledger(ledger)
                    return 2
                continue
            v = res.result
            # Every data year must be accounted for, and that is arithmetic.
            for attempt in range(2):
                obj = coverage_objection(v, u, pols) or double_claim_objection(v, u, ledger,
                                                                              A.country)
                if not obj:
                    break
                print(f"  COVERAGE  {u['unit_id']:22} {obj.splitlines()[0][:80]}")
                res = runner.call(f"{job}-cov{attempt + 1}",
                                  PROMPT.format(evidence=ev)
                                  + f"\n\nYOUR COVERAGE WAS REJECTED\n{'-' * 27}\n{obj}\n",
                                  SCHEMA, refresh=True)
                if not res.ok:
                    print(f"  FAIL  {u['unit_id']:24} coverage retry: {res.error}")
                    break
                v = res.result
            else:
                obj = coverage_objection(v, u, pols) or double_claim_objection(v, u, ledger,
                                                                              A.country)
                if obj:
                    v = {**v, "concerns": (v.get("concerns") or []) + [
                        f"HARNESS: coverage still does not tile {u['y0']}-{u['y1']} after 2 "
                        f"retries — {obj.splitlines()[0]}"]}
            # THE SPAN CHECK THE PROMPT COULD NOT ENFORCE. Ten of Spain's 47 verdicts proposed the
            # extract's own coverage as the span despite the instruction forbidding it, so this is
            # verified rather than requested: endpoints sitting on the data's own first and last
            # year are an extract-defined span, which must be re-spanned whenever the extract grows.
            prop = v.get("proposed") or {}
            # A UNIT CANNOT PREDATE ITS OWN CONTAINER. Eleven US states were proposed 1787-1792
            # against a chain that begins USA-1800-1803; stage 3 silently truncated each to 1800,
            # so the ledger and the page disagreed and only a cross-check found it.
            if convention and prop.get("start_year"):
                chain_start = min((int(e["start_year"]) for e in convention["container_chain"]),
                                  default=None)
                if chain_start is not None and prop["start_year"] < chain_start:
                    v = {**v, "concerns": (v.get("concerns") or []) + [
                        f"HARNESS: proposed start {prop['start_year']} precedes the earliest "
                        f"container era ({chain_start}); the page cannot contain it and will have "
                        f"to truncate."]}
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
                "coverage_json": json.dumps(v.get("coverage") or [], sort_keys=True),
                "coverage_ok": "yes" if coverage_objection(v, u, pols) is None else "no",
                "cycle": str(cycle), "model": model, "effort": effort,
                "decided_at": utc_now()})
            # A changed verdict invalidates what the later stages built on it.
            if row.get("verdict") != v["verdict"]:
                for k in ("polygon_route", "polygon_source_slug", "polygon_feature_id",
                          "polygon_detail", "polygon_confidence", "polygon_reasoning",
                          "page_written", "page_polity_code"):
                    row[k] = ""
            ledger[u["unit_id"]] = row
            mark(u["unit_id"])
            write_ledger(ledger)
            tag = "cached" if res.cached else "fresh"
            extra = v.get("matched_polity_code") or (
                v["proposed"]["polity_name"] if v.get("proposed") else "")
            print(f"  {v['verdict']:22} {u['unit_id']:24} {v['confidence']:7} {extra[:34]:36}({tag})")

    if A.polygon_stage:
        run_polygon_stage(A, runner, pols, iso, feats, ledger)
    if A.wiki_stage:
        run_wiki_stage(A, runner, ledger, pols, iso)
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
