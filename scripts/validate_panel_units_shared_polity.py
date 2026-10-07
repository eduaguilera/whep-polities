#!/usr/bin/env python3
"""Two reporting units of the subnational panel routed onto ONE polity in the same years.

WHY THIS EXISTS. WHEP takes the MEAN over (polity, item, unit, year). If two panel units land on
one polity and both report a cell, the published value is their average -- and when one unit is a
PART of the other (an island beside its province, a NUTS 3 beside its NUTS 2) that average is a
territorial error no per-unit check can see: each unit is routed "correctly" on its own. Nothing
forbade it. `validate_same_polity_overlaps.py` is the same question for layer B's labels, and reads
a table derived from matched_rows.parquet, which does not cover this panel.

WHAT THE FIRST RUN FOUND (2026-10-07): three pairs, all in Spain's island provinces, and all
the SAME province reported twice under two codes -- not a part beside its whole:

    ESP-35-1927-2025  ESP-ES701 (crops)   + ESP-ES705 (livestock)   Las Palmas
    ESP-38-1927-2025  ESP-ES702 (crops)   + ESP-ES709 (livestock)   Santa Cruz de Tenerife
    ESP-07-1833-2025  ESP-ES531 (crops)   + ESP-ES53  (livestock)   Illes Balears

The panel's Spanish provincial data is two snapshots with different NUTS vintages. Each indicator
family carries exactly 50 Spanish units -- area 50, production 50, livestock_stock 50 -- i.e. the
50 provinces, each once. The livestock family files the two Canary provinces under the NUTS 2016
code of their capital's island (ES705 Gran Canaria, ES709 Tenerife) and Baleares under its NUTS 2
code ES53; the crops family uses the older ES701/ES702 and ES531. A family of 50 that held Tenerife
ISLAND would have no unit at all for La Palma, La Gomera and El Hierro. The two members of each
pair share 0 of their (item, indicator, unit, year) cells -- their indicator sets are disjoint --
so nothing is averaged. The routing is right; the island NUTS names on those codes are not what the
data measures. Each is registered below with that reason.

WHAT THIS CHECKS.

  Everywhere (CI included -- reads only the committed routing ledger):
    A  every pair of distinct units whose routed coverage segments (matched, proposed, back_cast;
       `unroutable` lands nowhere) put them on one polity in overlapping years is REGISTERED in
       SHARED below, with a reason. Bidirectional: a new pair fails (decide whether it is a part
       and its whole -- reroute -- or one territory under two codes -- register), and a registered
       pair that no longer shares a polity fails too, so the list cannot go stale.

  Where the panel is present (WHEP_SUBNATIONAL, or the Nextcloud default; SKIPped by name in CI):
    B  the two units of every registered pair share no (item, indicator, unit, year) cell inside
       their common years. A shared cell is exactly what WHEP would average, so a pair whose
       registration rests on "disjoint content" is refuted the moment the panel gives them one.

Usage:
  python3 scripts/validate_panel_units_shared_polity.py
"""
from __future__ import annotations

import collections
import csv
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(REPO, "pipelines/agent-harness/state/routing_verdicts.csv")
PANEL = os.environ.get(
    "WHEP_SUBNATIONAL",
    os.path.expanduser("~/Nextcloud/WHEP_ERC 2025/Sources/data_raw/sources_juan/"
                       "whep_production_subnational.parquet"))

# Dispositions that put a unit's rows ON a polity. `unroutable` asserts no territory.
LANDS = ("matched", "proposed", "back_cast")

_STAND_IN = ("one province under two NUTS codes, not a part beside its whole: each Spanish indicator "
             "family holds exactly 50 units (the 50 provinces once each); the {fam} family files "
             "this province as {code}. Disjoint indicators, 0 shared cells (2026-10-07).")
# (polity, unit, unit) with the units sorted -> why sharing the polity is not a double count.
SHARED = {
    ("ESP-07-1833-2025", "ESP-ES53", "ESP-ES531"):
        _STAND_IN.format(fam="livestock", code="ES53 (NUTS 2) and the crops family as ES531"),
    ("ESP-35-1927-2025", "ESP-ES701", "ESP-ES705"):
        _STAND_IN.format(fam="livestock", code="ES705 (Gran Canaria's NUTS 2016 code)"),
    ("ESP-38-1927-2025", "ESP-ES702", "ESP-ES709"):
        _STAND_IN.format(fam="livestock", code="ES709 (Tenerife's NUTS 2016 code)"),
}


def routed_segments(path):
    """{polity: [(unit, start, end)]} from the ledger's coverage segments that land data."""
    out = collections.defaultdict(list)
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            raw = (row.get("coverage_json") or "").strip()
            if not raw:
                continue
            own = row.get("matched_polity_code") or row.get("page_polity_code") or ""
            for seg in json.loads(raw):
                if seg.get("disposition") not in LANDS:
                    continue
                code = seg.get("polity_code") or own
                if code:
                    out[code].append((row["unit_id"], int(seg["start_year"]), int(seg["end_year"])))
    return out


def shared_pairs(segs):
    """{(polity, unit_a, unit_b): [(lo, hi), ...]} for distinct units overlapping on one polity."""
    pairs = collections.defaultdict(list)
    for code, ss in segs.items():
        for i, (ua, a0, a1) in enumerate(ss):
            for ub, b0, b1 in ss[i + 1:]:
                if ua != ub and a0 <= b1 and b0 <= a1:
                    u, v = sorted((ua, ub))
                    pairs[(code, u, v)].append((max(a0, b0), min(a1, b1)))
    return pairs


def main() -> int:
    problems = []
    try:
        pairs = shared_pairs(routed_segments(LEDGER))
    except (OSError, ValueError, KeyError) as exc:
        print(f"FAIL: cannot read the routing ledger {LEDGER}: {exc}")
        return 1

    # --- A: every shared polity is registered, and every registration is live -------------
    print(f"panel units sharing one polity in overlapping years: {len(pairs)} pair(s) "
          f"(registered {len(SHARED)})")
    for key in sorted(pairs):
        spans = ", ".join(f"{lo}-{hi}" for lo, hi in sorted(set(pairs[key])))
        print(f"  {key[0]}: {key[1]} + {key[2]} ({spans})")
        if key not in SHARED:
            problems.append(
                f"{key[1]} and {key[2]} both route to {key[0]} in {spans} -- WHEP averages any "
                "cell both report. If one unit is part of the other, route the part to its own "
                "polity; if both codes are one territory, register the pair in SHARED with why")
    for key in sorted(set(SHARED) - set(pairs)):
        problems.append(f"registered pair {key} no longer shares a polity -- remove it from SHARED")

    # --- B: registered pairs share no cell, where the panel is present ---------------------
    if not os.path.exists(PANEL):
        print(f"SKIP arm B: panel absent ({PANEL}); shared cells are checked on a maintainer's "
              "machine, not here")
    else:
        import pandas as pd
        units = sorted({u for k in pairs for u in k[1:]})
        p = pd.read_parquet(PANEL, columns=["admin_unit_id", "item_clean", "indicator",
                                            "unit_canonical", "year"],
                            filters=[("admin_unit_id", "in", units)])
        cell = ["item_clean", "indicator", "unit_canonical", "year"]
        for key in sorted(pairs):
            _, u, v = key
            years = {y for lo, hi in pairs[key] for y in range(lo, hi + 1)}
            a = p[(p["admin_unit_id"] == u) & p["year"].isin(years)][cell].drop_duplicates()
            b = p[(p["admin_unit_id"] == v) & p["year"].isin(years)][cell].drop_duplicates()
            both = a.merge(b, on=cell)
            print(f"  {key[0]}: {u} {len(a)} cell(s), {v} {len(b)}, shared {len(both)}")
            if len(both):
                problems.append(
                    f"{u} and {v} share {len(both)} (item, indicator, unit, year) cell(s) on "
                    f"{key[0]}, e.g. {both.iloc[0].tolist()} -- WHEP would average them")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for msg in problems:
            print("  " + msg)
        return 1
    print("\nPASS: every polity two panel units share is registered, and they share no cell")
    return 0


if __name__ == "__main__":
    sys.exit(main())
