#!/usr/bin/env python3
"""Derive the alias rows a routing decision implies, from the ledger, deterministically.

ROUTING HAS TWO HALVES, AND THEY WERE WRITTEN BY DIFFERENT TOOLS. `harness.py` decides which
polity each reporting unit belongs to and records it as coverage segments in
`state/routing_verdicts.csv`. The rule that actually sends the source's rows there is a line in
`pipelines/polity-autoimprove/state/applied_aliases.csv`, and that file was appended to by
`apply_verdicts.py` and by hand. Nothing tied the second half to the first, and the gap is where
most of one day's defects came from:

    USA-CALIFORNIA   routed, page written, CAL-1850-2025 live -- no alias: 34,452 rows to nothing
    ARG-CHACO        second era ARG-CHACO-1951-2025 created for these very years -- never aliased
    COL-CASANARE     back_cast segment naming 'COL-CASANARE', the unit's own id, not a polity
    ITA regions      `matched` to ITA-1919-2025 -- executing that would average a region with Italy

The gates now catch each of these after the fact (validate_routed_units_are_aliased,
validate_coverage_targets, validate_matched_target_territory, validate_name_labels_single_country,
validate_alias_labels_cross_country). This stage closes the gap at the source: the alias rows are
DERIVED from the ledger rather than written separately, so a routing decision and its alias cannot
disagree without this saying so.

WHAT IS DERIVED, per ledger unit and per coverage segment:

    matched   -> an observed rule (disposition '') to the segment's polity, clipped to its span
                 (a polity live at the 2025 CEILING covers 2025 itself; see `in_span`)
    proposed  -> an observed rule to the polity authored for it: the segment's own polity_code if
                 it names one, else the unit's page_polity_code / extra_pages polity whose span
                 contains those years (one per era -- this is what reaches Chaco's second era)
    back_cast -> a `back_cast` rule to the segment's polity for the years BEFORE that polity
                 starts. Years a back_cast segment spends INSIDE its target's span are not
                 derived: a back_cast target inside its own span is the era's national row, and
                 aliasing a region onto its country there is exactly the averaging defect
                 validate_matched_target_territory exists for. They BLOCK --check: 12 such
                 segments (CHL-AP, CHL-AR, COL-AMAZONAS, COL-GUAINIA, ITA-ITF6) sat in the
                 ledger naming the national row at 10-44x the unit's area while the registry
                 routed the unit's own polity, and a report line nobody had to act on let the
                 two halves of the routing disagree indefinitely. Re-recorded 2026-09-24.
    unroutable -> nothing

INDICATOR-SCOPED REGISTRY ROWS (`indicator` non-blank, added 2026-09-25) cover their years for the
purpose of this comparison: a year the registry splits by indicator is routed, and it agrees with
the ledger when ONE of the split's polities is the ledger's (the ledger names the unit's default
territory; the split sends some indicators elsewhere). A split naming none of them is a
`conflict`. Years covered ONLY by scoped rows are listed as `scoped` (non-blocking), because
whatever indicators the split leaves out route nowhere and only a human can say that is right.

Label forms are the unit's `admin_unit_id` and its `admin_name`. The NAME is written only when no
other unit of the ledger or the panel (state/panel_unit_names.csv) carries it: 'Santa Cruz' is both
ARG-SANTACRUZ and BOL-SANTACRUZ, and 'Distrito Federal' is Brazil's unit and also a name the panel
gives MEX-CMX, so a rule on a shared name routes somebody else's rows. A new row reuses the form the
slug already files the unit under; else the unshared name; else the id, which carries its country
and cannot collide.

Slugs are the panel slugs (policy.json `alias_derivation`: `juan-subnational` and the `whep-lab-`
components) that already carry the unit, or `juan-subnational` when none does. The panel's units
are filed under different ones -- ARG-CORDOBA under whep-lab-latam only, ARG-BUENOSAIRES under
juan-subnational -- so a slug that carries a unit for some years must carry it for all its routed
years, and none is demanded that has never carried it. A slug with its own vocabulary
(eurostat-nuts2016 reads FR104 as the official NUTS region, Essonne) is never written: its meaning
of the label is its own.

WHAT IS NEVER DONE:
  * a target that is not a live polity is REFUSED (reported, nothing written)
  * an existing row is never rewritten or deleted -- a year already covered for (unit, slug) is left
    alone; if the existing rule names a different polity than the ledger, that is a CONFLICT and
    is reported for a human, because either side may be the hand-curated truth
  * nothing overlaps an existing label+source range

Usage:
  python3 pipelines/agent-harness/derive_aliases.py --check            # drift report, exit 1
  python3 pipelines/agent-harness/derive_aliases.py --write            # append only what is missing
  python3 pipelines/agent-harness/derive_aliases.py --check --country Argentina
"""
from __future__ import annotations

import argparse
import collections
import csv
import io
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
LEDGER = HERE / "state" / "routing_verdicts.csv"
NAMES = HERE / "state" / "panel_unit_names.csv"
ALIASES = REPO / "pipelines" / "polity-autoimprove" / "state" / "applied_aliases.csv"
DB = REPO / "data" / "final" / "polities_database.csv"
POLICY = HERE / "policy.json"

# `indicator` (appended 2026-09-25) is the optional scope of a registry row: blank = every row of
# the label, a value = only rows whose panel `indicator` equals it. The ledger has no indicator
# dimension, so every row this stage derives is UNSCOPED; scoped rows are hand decisions (a unit
# whose indicators are two territories, like the panel's CHL-LL) and are read, never written.
ALIAS_FIELDS = ("source_label", "source", "year_start", "year_end", "common_name",
                "polity_code", "confidence", "basis", "observed_rows", "disposition",
                "indicator")
DEAD = ("retired", "superseded")
STAMP = "agent-harness derive_aliases"
# Finding kinds that fail --check. `back_cast_inside` joined the first three once its 12 findings
# were re-recorded: a back_cast inside its target's own span names the era's container, which the
# registry does not route, so the ledger and the registry disagree about where the data goes.
BLOCKING = ("missing", "conflict", "refused", "back_cast_inside")
# A live polity whose EXCLUSIVE end_year is this ceiling has no real last year: `CAL-1850-2025`
# ends at 2025 because the registry stops there, not because California did. So the ceiling year
# itself IS covered, and an alias may end at 2025 -- the exception validate_alias_year_coverage.py
# (and validate_map_area_year.py) already make, with the same constant and the same `<= CEILING`
# guard: a year BEYOND the ceiling (a panel reaching 2026) is still outside every polity. Without
# it this stage cut every panel unit's 2025 year (6,354 rows over 50 US states on 2026-09-25)
# while the gate that polices alias years accepted the very rule it refused to write.
CEILING = 2025


def in_span(y: int, start: int, end: int) -> bool:
    """Whether year `y` lies inside a polity running `start` to EXCLUSIVE `end`, the ceiling aside."""
    return start <= y < end or (end >= CEILING and start <= y <= CEILING)


def norm(s: str) -> str:
    """The same normalisation harness.py uses: case, accents and punctuation do not distinguish."""
    s = unicodedata.normalize("NFKD", str(s))
    return re.sub(r"[^a-z0-9]", "", s.encode("ascii", "ignore").decode().lower())


def policy() -> dict[str, Any]:
    p = json.loads(POLICY.read_text(encoding="utf-8")) if POLICY.is_file() else {}
    a = p.get("alias_derivation") or {}
    return {"panel_slug": a.get("panel_slug", "juan-subnational"),
            "panel_slug_prefixes": tuple(a.get("panel_slug_prefixes", ["whep-lab-"]))}


def read_csv(path: Path) -> list[dict[str, str]]:
    csv.field_size_limit(sys.maxsize)
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def live_polities(rows: Iterable[dict[str, str]]) -> dict[str, dict[str, Any]]:
    """code -> {start, end (EXCLUSIVE), name} for every polity that is not retired/superseded."""
    out = {}
    for r in rows:
        if (r.get("wiki_status") or "").strip() in DEAD:
            continue
        try:
            out[r["polity_code"]] = {"start": int(r["start_year"]), "end": int(r["end_year"]),
                                     "name": r.get("polity_name", "")}
        except (TypeError, ValueError):
            continue
    return out


def name_owners(ledger: Iterable[dict[str, str]],
                names: Iterable[dict[str, str]] = ()) -> dict[str, set[str]]:
    """normalised name -> the unit ids that carry it, in the ledger or anywhere in the panel."""
    own: dict[str, set[str]] = collections.defaultdict(set)
    for r in list(ledger) + list(names):
        n = norm(r.get("admin_name") or "")
        if n:
            own[n].add(r["unit_id"])
    return own


def label_forms(unit: dict[str, str], owners: dict[str, set[str]]) -> list[str]:
    """The labels a source may use for this unit: its id always, its name only if nobody shares it."""
    forms = [unit["unit_id"]]
    name = (unit.get("admin_name") or "").strip()
    if name and norm(name) != norm(unit["unit_id"]) and owners.get(norm(name), set()) <= {
            unit["unit_id"]}:
        forms.append(name)
    return forms


def extra_codes(raw: str) -> list[str]:
    try:
        parsed = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []
    return [str(e.get("polity_code") or "").strip() for e in parsed
            if isinstance(e, dict) and (e.get("polity_code") or "").strip()]


def _years(a: dict[str, str]) -> range:
    try:
        return range(int(a["year_start"]), int(a["year_end"]) + 1)
    except (TypeError, ValueError):
        return range(0)


def runs(years: Iterable[int]) -> list[tuple[int, int]]:
    """Sorted years -> inclusive (lo, hi) runs."""
    out: list[list[int]] = []
    for y in sorted(set(years)):
        if out and y == out[-1][1] + 1:
            out[-1][1] = y
        else:
            out.append([y, y])
    return [(a, b) for a, b in out]


def intended(unit: dict[str, str], live: dict[str, dict[str, Any]]):
    """What the ledger says this unit's data routes to, year by year, and what it cannot derive.

    Returns (plan, findings). `plan` maps year -> (polity_code, disposition-for-the-alias,
    segment basis). `findings` is a list of (kind, message) for refused targets, clipped years and
    back_cast years inside their target -- none of which is ever written.
    """
    plan: dict[int, tuple[str, str, str]] = {}
    findings: list[tuple[str, str]] = []
    try:
        segs = json.loads(unit.get("coverage_json") or "[]")
    except json.JSONDecodeError:
        return plan, [("refused", f"{unit['unit_id']}: coverage_json does not parse")]
    if isinstance(segs, dict):
        segs = segs.get("segments", [])
    uid = unit["unit_id"]
    page_codes = [c for c in [(unit.get("page_polity_code") or "").strip()]
                  + extra_codes(unit.get("extra_pages") or "") if c]

    for s in segs:
        disp = s.get("disposition")
        if disp not in ("matched", "proposed", "back_cast"):
            continue
        try:
            lo, hi = int(s["start_year"]), int(s["end_year"])
        except (KeyError, TypeError, ValueError):
            findings.append(("refused", f"{uid}: a {disp} segment has no usable years"))
            continue
        where = f"{uid} {lo}-{hi} ({disp})"
        basis = (s.get("basis") or "").strip()
        code = (s.get("polity_code") or "").strip()
        if not code and disp == "matched":
            code = (unit.get("matched_polity_code") or "").strip()

        if disp == "proposed" and not code:
            # The polity was authored AFTER stage 1 decided the segment, so its code lives on the
            # page fields. One page per era; the era is the one whose span holds the year.
            if not page_codes:
                findings.append(("unauthored", f"{where}: proposed, and no page has been "
                                               f"authored for it yet -- nothing to alias"))
                continue
            refused = [c for c in page_codes if c not in live]
            for c in refused:
                findings.append(("refused", f"{where}: authored page {c!r} is not a live polity"))
            cands = [c for c in page_codes if c in live]
            clipped = []
            for y in range(lo, hi + 1):
                alive = [c for c in cands if in_span(y, live[c]["start"], live[c]["end"])]
                if len(alive) == 1:
                    plan[y] = (alive[0], "", basis)
                elif not alive:
                    clipped.append(y)
                else:
                    findings.append(("ambiguous", f"{where}: {y} lies inside {alive}; "
                                                  f"not derived"))
            for a, b in runs(clipped):
                findings.append(("clipped", f"{where}: {a}-{b} lies outside every authored "
                                            f"polity ({', '.join(cands) or 'none live'})"))
            continue

        if not code:
            findings.append(("refused", f"{where}: names no polity_code"))
            continue
        if code not in live:
            # The unit's own id, or a plausible code nobody minted: COL-CASANARE, FRA-BASRHIN-...
            findings.append(("refused", f"{where}: {code!r} is not a live polity -- refused"))
            continue
        p0, p1 = live[code]["start"], live[code]["end"]
        if disp == "back_cast":
            before = [y for y in range(lo, hi + 1) if y < p0]
            inside = [y for y in range(lo, hi + 1) if in_span(y, p0, p1)]
            after = [y for y in range(lo, hi + 1) if y >= p0 and not in_span(y, p0, p1)]
            for y in before:
                plan[y] = (code, "back_cast", basis)
            for a, b in runs(inside):
                findings.append(("back_cast_inside", f"{where}: {a}-{b} is inside {code}'s own "
                                                     f"span ({p0}-{p1}); a back_cast there is the "
                                                     f"era's container, not derived"))
            for a, b in runs(after):
                findings.append(("clipped", f"{where}: {a}-{b} is after {code} ends ({p1})"))
            continue
        # matched, or proposed naming its polity: observed, clipped to the target's span
        for y in range(lo, hi + 1):
            if in_span(y, p0, p1):
                plan[y] = (code, "", basis)
        out = [y for y in range(lo, hi + 1) if not in_span(y, p0, p1)]
        for a, b in runs(out):
            findings.append(("clipped", f"{where}: {a}-{b} is outside {code}'s span {p0}-{p1}"))
    return plan, findings


def is_panel_slug(slug: str, cfg: dict[str, Any]) -> bool:
    return slug == cfg["panel_slug"] or slug.startswith(tuple(cfg["panel_slug_prefixes"]))


def slugs_for(rules: list[dict[str, str]], cfg: dict[str, Any]) -> list[str]:
    """The panel slugs that already carry this unit, or the panel's own slug when none does.

    The panel's units are filed under more than one slug -- ARG-CORDOBA under whep-lab-latam,
    ARG-BUENOSAIRES under juan-subnational, AUS-QUEENSLAND under both -- so demanding the panel
    slug of every unit reports 38 units "unaliased" whose data routes perfectly well. A slug that
    carries the unit for some years must carry it for all its routed years; a unit no panel slug
    carries at all (USA-CALIFORNIA) gets the panel's own.
    """
    carried = sorted({a["source"] for a in rules if is_panel_slug(a["source"], cfg)})
    return carried or [cfg["panel_slug"]]


def derive(ledger: list[dict[str, str]], aliases: list[dict[str, str]],
           live: dict[str, dict[str, Any]], owners: dict[str, set[str]],
           cfg: dict[str, Any] | None = None, country: str | None = None) -> dict[str, list]:
    """The rows the ledger implies and the registry lacks, plus everything that blocks the rest.

    Pure: reads nothing from disk, so every defect it exists for is a fixture in test_harness.py.
    """
    cfg = cfg or {"panel_slug": "juan-subnational", "panel_slug_prefixes": ("whep-lab-",)}
    out: dict[str, list] = {"missing": [], "conflict": [], "refused": [], "clipped": [],
                            "back_cast_inside": [], "ambiguous": [], "unauthored": [],
                            "unrecorded": [], "scoped": []}
    by_label: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
    for a in aliases:
        by_label[norm(a["source_label"])].append(a)

    for unit in ledger:
        if country and unit.get("country") != country:
            continue
        plan, findings = intended(unit, live)
        for kind, msg in findings:
            out[kind].append(msg)
        if not plan:
            continue
        forms = label_forms(unit, owners)
        existing = [a for f in forms for a in by_label.get(norm(f), [])]
        # A SHARED name is never written, but it may already route this unit: 'Cordoba' is three
        # countries' unit and the registry's juan rule for it is scoped by year to Argentina's
        # province. It counts as coverage only where it names the polity the ledger wants -- a
        # shared-name rule naming something else is most likely the other unit's rule, which is
        # the name gates' business rather than a conflict for this one.
        name = (unit.get("admin_name") or "").strip()
        shared = ([a for a in by_label.get(norm(name), [])]
                  if name and name not in forms and norm(name) != norm(unit["unit_id"]) else [])
        agreeing_shared = [a for a in shared if any(
            c == a["polity_code"] for c, _d, _b in plan.values())]
        for slug in slugs_for(existing + agreeing_shared, cfg):
            # A blank-source rule applies to every source, so it covers this slug too.
            mine = [a for a in existing if a["source"] in (slug, "")]
            covered: dict[int, set[str]] = collections.defaultdict(set)
            # year -> the indicator scopes covering it, and whether an unscoped row does too.
            scopes: dict[int, set[str]] = collections.defaultdict(set)
            unscoped: set[int] = set()
            for a in mine:
                try:
                    a0, a1 = int(a["year_start"]), int(a["year_end"])
                except (TypeError, ValueError):
                    continue
                ind = (a.get("indicator") or "").strip()
                for y in range(a0, a1 + 1):
                    covered[y].add(a["polity_code"])
                    if ind:
                        scopes[y].add(ind)
                    else:
                        unscoped.add(y)
            split = {}
            for y in sorted(set(scopes) - unscoped):
                if y in plan:
                    split.setdefault(",".join(sorted(scopes[y])), []).append(y)
            for inds, ys in split.items():
                for a, b in runs(ys):
                    out["scoped"].append(f"{unit['unit_id']} [{slug}] {a}-{b}: routed only for "
                                         f"indicator(s) {inds}; any other indicator routes "
                                         f"nowhere in these years")
            for a in shared:
                if a["source"] not in (slug, ""):
                    continue
                try:
                    a0, a1 = int(a["year_start"]), int(a["year_end"])
                except (TypeError, ValueError):
                    continue
                for y in range(a0, a1 + 1):
                    if y in plan and plan[y][0] == a["polity_code"]:
                        covered[y].add(a["polity_code"])
            # The label this slug already uses for the unit; else the unit's own name when nobody
            # shares it (the panel slug files 493 of its 502 rules by name); else the id, which
            # carries its country and cannot collide.
            used = collections.Counter(a["source_label"] for a in mine if a["source"] == slug)
            label = used.most_common(1)[0][0] if used else forms[-1]

            # The other direction of drift: the registry routes years the ledger does not.
            # Reported, never acted on -- the ledger may say `unroutable` where a later hand
            # decision found a territory, and either may be the one to correct.
            extra = sorted(y for a in mine if a["source"] == slug
                           for y in _years(a) if y not in plan)
            for a, b in runs(extra):
                out["unrecorded"].append(f"{unit['unit_id']} [{slug}] {a}-{b}: the registry "
                                         f"routes these years; the ledger routes none of them")

            todo: dict[tuple[str, str], list[int]] = collections.defaultdict(list)
            clash: dict[tuple[str, str], list[int]] = collections.defaultdict(list)
            for y, (code, disp, _b) in sorted(plan.items()):
                have = covered.get(y)
                if not have:
                    todo[(code, disp)].append(y)
                elif code not in have:
                    clash[(code, ",".join(sorted(have)))].append(y)
            for (code, have), ys in clash.items():
                for a, b in runs(ys):
                    out["conflict"].append(
                        f"{unit['unit_id']} [{slug}] {a}-{b}: ledger routes to {code}, the "
                        f"registry already routes {forms} to {have} -- left alone")
            for (code, disp), ys in todo.items():
                for a, b in runs(ys):
                    seg_basis = plan[a][2]
                    out["missing"].append({
                        "source_label": label, "source": slug,
                        "year_start": str(a), "year_end": str(b),
                        "common_name": live[code]["name"], "polity_code": code,
                        "confidence": unit.get("confidence") or "medium",
                        "basis": (f"{STAMP}: derived from the routing ledger, unit "
                                  f"{unit['unit_id']} ({unit.get('admin_name', '')}), coverage "
                                  f"{'back_cast' if disp else 'observed'} {a}-{b} -> {code}. "
                                  f"Segment basis: {seg_basis[:300]}"),
                        "observed_rows": "", "disposition": disp, "indicator": ""})
    return out


def write_atomic(path: Path, rows: list[dict[str, str]]) -> None:
    """Build the whole file, then os.replace -- a killed run must not truncate the registry."""
    sio = io.StringIO()
    w = csv.DictWriter(sio, fieldnames=list(ALIAS_FIELDS), lineterminator="\r\n")
    w.writeheader()
    w.writerows({f: r.get(f, "") for f in ALIAS_FIELDS} for r in rows)
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(sio.getvalue())
    os.replace(tmp, path)


def append_atomic(path: Path, rows: list[dict[str, str]]) -> None:
    """Append rows to the registry, leaving every existing byte as it is, then os.replace.

    Rewriting the whole file through DictWriter re-serialises rows it never meant to touch: 300
    registry rows written without a trailing empty `disposition` field came back with one, so a
    52-row append showed up as a 650-line diff that buried the rows actually added.
    """
    old = path.read_bytes()
    sio = io.StringIO()
    w = csv.DictWriter(sio, fieldnames=list(ALIAS_FIELDS), lineterminator="\r\n")
    w.writerows({f: r.get(f, "") for f in ALIAS_FIELDS} for r in rows)
    sep = b"" if not old or old.endswith(b"\n") else b"\r\n"
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    with open(tmp, "wb") as fh:
        fh.write(old + sep + sio.getvalue().encode("utf-8"))
    os.replace(tmp, path)


def report(res: dict[str, list], verbose: bool = True) -> None:
    labels = {"missing": "alias row(s) the ledger implies and the registry lacks",
              "conflict": "year range(s) where the registry routes the unit elsewhere",
              "refused": "segment target(s) that are not live polities",
              "clipped": "segment range(s) outside their target's span",
              "back_cast_inside": "back_cast range(s) inside their target's own span",
              "ambiguous": "year(s) two authored eras both claim",
              "unauthored": "proposed segment(s) with no page yet",
              "unrecorded": "registry range(s) the ledger does not route (not acted on)",
              "scoped": "year range(s) the registry routes only per indicator (not acted on)"}
    for k, what in labels.items():
        items = res[k]
        print(f"  {len(items):5}  {what}")
        if verbose:
            for it in items[:40]:
                if isinstance(it, dict):
                    print(f"           {it['source_label']!r:28} {it['source']:18} "
                          f"{it['year_start']}-{it['year_end']} -> {it['polity_code']}"
                          f"{'  [back_cast]' if it['disposition'] else ''}")
                else:
                    print(f"           {it}")
            if len(items) > 40:
                print(f"           ... {len(items) - 40} more")


def run(check: bool, country: str | None = None, verbose: bool = True,
        regenerate: bool = True) -> int:
    ledger = read_csv(LEDGER)
    aliases = read_csv(ALIASES)
    live = live_polities(read_csv(DB))
    names = read_csv(NAMES) if NAMES.is_file() else []
    res = derive(ledger, aliases, live, name_owners(ledger, names), policy(), country)
    print(f"derive_aliases: {len(ledger)} ledger unit(s)"
          f"{' in ' + country if country else ''} against {len(aliases)} registry row(s)")
    report(res, verbose)
    blocking = [k for k in BLOCKING if res[k]]
    if check:
        if blocking:
            print(f"FAIL: the routing ledger and applied_aliases.csv disagree "
                  f"({', '.join(blocking)}). `--write` appends the missing rows; conflicts, "
                  f"refusals and back_cast-inside segments need a decision, not a rerun.")
            return 1
        print("PASS: every routed ledger year has its alias, and none is contradicted")
        return 0
    if res["missing"]:
        append_atomic(ALIASES, res["missing"])
        print(f"appended {len(res['missing'])} row(s) to {ALIASES}")
        if regenerate:
            # The published map is derived from the registry, and the manifest fingerprints the
            # map: both --check gates fail until both are rewritten.
            for script in ("write_label_alias_map.py", "write_manifest.py"):
                subprocess.run([sys.executable, str(REPO / "scripts" / script)],
                               cwd=str(REPO), check=True)
    if res["conflict"] or res["refused"] or res["back_cast_inside"]:
        print("NOT RESOLVED: conflicts, refusals and back_cast-inside segments above were left "
              "alone -- each needs a decision")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="report drift; exit 1 if any")
    mode.add_argument("--write", action="store_true", help="append only the missing rows")
    ap.add_argument("--country", default=None, help="restrict to one ledger country")
    ap.add_argument("--quiet", action="store_true", help="counts only")
    A = ap.parse_args()
    return run(A.check, A.country, verbose=not A.quiet)


if __name__ == "__main__":
    sys.exit(main())
