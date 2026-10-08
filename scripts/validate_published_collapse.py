#!/usr/bin/env python3
"""The published historical-production table carries ONE row per consumer key, never a blend.

WHY (issues 451, 367). `.prepare_historical_production()` in the WHEP R package reduces every
(year, area, item, unit) key with `mean(value)`, and so did the harmonized build before handing the
table over. Measured 2026-10-07 on the build's own output, 1,706 published keys held candidates
that disagree, so the consumer published a number equal to none of them: fao1952's two Yugoslav
dry-bean rows (38,000 and 783,000 ha, which SUM to juan's 821,000) were averaged with juan's total.
`state/collapse_groups.csv` (`validate_collapse_groups.py`) describes the same hazard on the raw
panel; this gate polices what the build actually PUBLISHES after its item and unit filters.

`pipelines/historical-production-harmonized/R/resolve_collapse_groups.R` now resolves every key to
one candidate by stated rules and the build writes each non-trivial decision to
`pipelines/historical-production-harmonized/state/collapse_resolutions.csv`. The panel is not
redistributable and absent in CI, so this gate reads that tracked table and RE-DERIVES every
decision from its `candidates` column, using the constants parsed from the R file itself.

Checks:
  A. SHAPE AND VOCABULARY -- the header, the per-source rules, the resolutions, n_candidates equal to
     the number of candidate values listed.
  B. RE-DERIVATION -- each source's rule, the key's resolution, the published source and value are
     what the R rules produce from the listed candidates. This is the arm that catches a hand edit,
     a stale table, or a resolver change that was not regenerated.
  C. NO BLEND -- a published value is one of the published source's own candidates. B implies it;
     it is stated separately because it is the property the consumer relies on.
  D. WITHHELD KEYS ARE DOCUMENTED, BOTH WAYS -- every withheld key is in
     `state/withheld_keys_baseline.csv` with a reason, and every baseline row is still withheld. A new
     withheld key is a new defect: document it (or resolve it upstream) rather than let it vanish
     from the published table unnoticed. A baseline row that no longer applies is stale. Each
     `known_defect` id must name an entry of `data_errors.csv`.
  E. THE BUILD PUBLISHES THROUGH THE RESOLVER -- build.R sources and calls it, refuses to write a
     table with a duplicate key, and no longer averages `value`.
  F. CURATED ANCHORS read as the issues describe them.
"""
import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPE = os.path.join(REPO, "pipelines/historical-production-harmonized")
TABLE = os.path.join(PIPE, "state/collapse_resolutions.csv")
BASELINE = os.path.join(PIPE, "state/withheld_keys_baseline.csv")
RESOLVER = os.path.join(PIPE, "R/resolve_collapse_groups.R")
BUILD = os.path.join(PIPE, "build.R")
DATA_ERRORS = os.path.join(REPO, "pipelines/polity-autoimprove/state/data_errors.csv")

FIELDS = ["year", "polity_code", "item_prod_code", "item_prod_name", "unit", "n_candidates",
          "candidates", "labels", "raw_items", "source_rules", "resolution", "published_source",
          "published_value"]
BASELINE_FIELDS = ["year", "polity_code", "item_prod_code", "unit", "resolution", "known_defect",
                   "reason"]
SOURCE_RULES = frozenset({"single", "identical", "total_beside_parts", "ambiguous"})
RESOLUTIONS = frozenset({"identical", "one_source", "source_precedence", "withheld_ambiguous",
               "withheld_contradiction"})

# --- F. anchors: (year, polity, item_prod_code, unit) -> what the issues say ---------------------
ANCHORS = {
    ("1949", "F248-1947-1991", "176", "ha"): dict(
        resolution="one_source", published_source="juan", published_value="821000",
        why="fao1952 prints Yugoslav dry beans as two rows, 38,000 and 783,000 ha, that SUM to juan's "
            "821,000 total. With no total of its own the fao1952 pair cannot be read, so it drops out "
            "and juan's total is published -- the mean used to publish 547,333"),
    ("1950", "ITA-1919-2025", "560", "tonnes"): dict(
        resolution="source_precedence", published_source="fao1952", published_value="6544000",
        why="issue 367's total beside its own parts: 6,544 = 4,014 + 2,530 thousand t. The total is "
            "kept, and it equals juan's figure"),
    # NOT CONTESTED ANY MORE (issue 375): iia `wheat` is withheld before the resolver by
    # data/final/source_item_withholds.csv, so this key has juan alone and is published as a lone row,
    # which the table does not record. `absent` asserts exactly that; were the item withhold lost,
    # the key would reappear here as a contradiction.
    ("1930", "F51-1918-1938", "15", "tonnes"): dict(
        resolution="absent",
        why="iia's `wheat` here is 311.9 t of spelt and meslin against juan's 1,377,280 t "
            "(iia-wheat-is-spelt-and-meslin): the mean published 688,796, #451 withheld the key, and "
            "the item withhold of issue 375 now leaves juan's figure as the only candidate"),
    ("1934", "F51-1918-1938", "176", "ha"): dict(
        resolution="withheld_contradiction", published_source="", published_value="",
        why="iia's Czechoslovak dry beans are one component, 7,000 ha against juan's 58,000 "
            "(iia-czechoslovakia-beans-component-only): neither can be published as the key's value"),
    ("1945", "ETH-1941-1952", "656", "tonnes"): dict(
        resolution="identical", published_source="iia", published_value="17000",
        why="issue 451's `ethiopia` / `ethiopia pdr`: one series under two spellings, published once"),
}


def parse_constants(text):
    """The resolver's constants, read from the R source so the gate cannot drift from it."""
    out = {}
    m = re.search(r'^PRECEDENCE <- c\(([^)]*)\)', text, re.M)
    out["PRECEDENCE"] = re.findall(r'"([^"]+)"', m.group(1)) if m else None
    for name in ("TBP_TOLERANCE", "CONTRADICTION_RATIO", "IDENTICAL_TOLERANCE"):
        m = re.search(rf'^{name} <- ([0-9.eE+-]+)\s*$', text, re.M)
        out[name] = float(m.group(1)) if m else None
    return out


def same_values(v, tol):
    return (max(v) - min(v)) <= tol * max(1.0, abs(max(v)))


def reduce_one_source(v, k):
    """Mirror of .reduce_one_source(): (rule, value or None). `v` need not be ordered."""
    if len(v) == 1:
        return "single", v[0]
    if same_values(v, k["IDENTICAL_TOLERANCE"]):
        return "identical", v[0]
    top = max(v)
    if len(v) >= 3 and abs(top - (sum(v) - top)) <= k["TBP_TOLERANCE"] * abs(top):
        return "total_beside_parts", top
    return "ambiguous", None


def contradicts(v, k):
    lo, hi = min(v), max(v)
    if lo <= 0:
        return hi > 0
    return hi / lo > k["CONTRADICTION_RATIO"]


def rank(src, k):
    p = k["PRECEDENCE"]
    return p.index(src) if src in p else len(p)


def derive(cands, k):
    """(source_rules dict, resolution, published_source, published_value) from the candidates."""
    order = sorted(cands, key=lambda s: (rank(s, k), s))
    rules, surv = {}, []
    for s in order:
        rule, val = reduce_one_source(cands[s], k)
        rules[s] = rule
        if val is not None:
            surv.append((s, val))
    allv = [x for s in order for x in cands[s]]
    if not surv:
        res = "withheld_ambiguous"
    elif same_values(allv, k["IDENTICAL_TOLERANCE"]):
        res = "identical"
    elif len(surv) == 1:
        res = "one_source"
    elif contradicts([v for _, v in surv], k):
        res = "withheld_contradiction"
    else:
        res = "source_precedence"
    if res.startswith("withheld"):
        return rules, res, "", None
    return rules, res, surv[0][0], surv[0][1]


def parse_candidates(text):
    out = {}
    for part in text.split("|"):
        src, _, vals = part.partition("=")
        out[src] = [float(x) for x in vals.split(";")]
    return out


def main() -> int:
    problems = []
    for path in (TABLE, BASELINE, RESOLVER, BUILD):
        if not os.path.exists(path):
            print(f"FAIL: missing {os.path.relpath(path, REPO)}", file=sys.stderr)
            return 1
    with open(RESOLVER, encoding="utf-8") as fh:
        k = parse_constants(fh.read())
    missing = [n for n, v in k.items() if v is None]
    if missing:
        print(f"FAIL: could not read {missing} from {os.path.relpath(RESOLVER, REPO)}; this gate "
              f"re-derives every decision from them and cannot run without", file=sys.stderr)
        return 1

    with open(TABLE, newline="", encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        if rd.fieldnames != FIELDS:
            print(f"FAIL: {os.path.relpath(TABLE, REPO)} header is {rd.fieldnames}, expected {FIELDS}",
                  file=sys.stderr)
            return 1
        rows = list(rd)
    if not rows:
        print(f"FAIL: {os.path.relpath(TABLE, REPO)} is empty -- every arm would pass by having "
              f"nothing to check", file=sys.stderr)
        return 1

    withheld = {}
    by_key = {}
    for i, r in enumerate(rows, start=2):
        key = (r["year"], r["polity_code"], r["item_prod_code"], r["unit"])
        where = f"line {i} {'/'.join(key)}"
        if key in by_key:
            problems.append(f"A {where}: key listed twice")
        by_key[key] = r
        # --- A ---
        if r["resolution"] not in RESOLUTIONS:
            problems.append(f"A {where}: resolution {r['resolution']!r} not in {sorted(RESOLUTIONS)}")
            continue
        try:
            cands = parse_candidates(r["candidates"])
            n = int(r["n_candidates"])
        except ValueError:
            problems.append(f"A {where}: candidates {r['candidates']!r} or n_candidates not numeric")
            continue
        if sum(len(v) for v in cands.values()) != n:
            problems.append(f"A {where}: n_candidates={n} but {sum(len(v) for v in cands.values())} "
                            f"candidate value(s) listed")
        stated = dict(p.partition("=")[::2] for p in r["source_rules"].split("|"))
        bad = {s: x for s, x in stated.items() if x not in SOURCE_RULES}
        if bad:
            problems.append(f"A {where}: unknown source rule(s) {bad}")
        # --- B ---
        rules, res, src, val = derive(cands, k)
        if stated != rules:
            problems.append(f"B {where}: source_rules {stated} but the candidates give {rules}")
        if r["resolution"] != res:
            problems.append(f"B {where}: resolution {r['resolution']!r} but the candidates give "
                            f"{res!r}")
        if r["published_source"] != src:
            problems.append(f"B {where}: published_source {r['published_source']!r} but precedence "
                            f"{k['PRECEDENCE']} gives {src!r}")
        if val is None:
            if r["published_value"]:
                problems.append(f"B {where}: withheld, yet a published_value is recorded")
            withheld[key] = r
        else:
            try:
                pv = float(r["published_value"])
            except ValueError:
                problems.append(f"B {where}: published_value {r['published_value']!r} not numeric")
                continue
            if abs(pv - val) > 1e-9 * max(1.0, abs(val)):
                problems.append(f"B {where}: published_value {pv:g} but the rules give {val:g}")
            # --- C ---
            own = cands.get(r["published_source"], [])
            if not any(abs(pv - x) <= 1e-9 * max(1.0, abs(x)) for x in own):
                problems.append(f"C {where}: published_value {pv:g} is none of "
                                f"{r['published_source']}'s own candidates {own} -- a blend, which "
                                f"is exactly what the consumer must never receive")

    # --- D ---
    with open(BASELINE, newline="", encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        if rd.fieldnames != BASELINE_FIELDS:
            problems.append(f"D baseline header is {rd.fieldnames}, expected {BASELINE_FIELDS}")
            base = []
        else:
            base = list(rd)
    known = set()
    if os.path.exists(DATA_ERRORS):
        with open(DATA_ERRORS, newline="", encoding="utf-8") as fh:
            known = {r["issue_id"] for r in csv.DictReader(fh)}
    base_keys = {}
    for i, b in enumerate(base, start=2):
        key = (b["year"], b["polity_code"], b["item_prod_code"], b["unit"])
        if key in base_keys:
            problems.append(f"D baseline line {i} {'/'.join(key)}: listed twice")
        base_keys[key] = b
        if not b["reason"].strip():
            problems.append(f"D baseline line {i} {'/'.join(key)}: no reason -- a withheld key is "
                            f"only documented if it says why")
        for kd in filter(None, (x.strip() for x in b["known_defect"].split(";"))):
            if kd not in known:
                problems.append(f"D baseline line {i} {'/'.join(key)}: known_defect {kd!r} is not an "
                                f"entry of data_errors.csv")
    for key, r in sorted(withheld.items()):
        b = base_keys.get(key)
        if b is None:
            problems.append(
                f"D NEW withheld key {'/'.join(key)} ({r['resolution']}; candidates {r['candidates']}) "
                f"is not in {os.path.relpath(BASELINE, REPO)}. It no longer reaches the published "
                f"table; record why (and the data_errors.csv entry that explains it, if any), or fix "
                f"the routing or item mapping that put the candidates on one key")
        elif b["resolution"] != r["resolution"]:
            problems.append(f"D {'/'.join(key)}: baseline says {b['resolution']}, table says "
                            f"{r['resolution']}")
    for key in sorted(set(base_keys) - set(withheld)):
        problems.append(f"D STALE baseline row {'/'.join(key)}: the key is no longer withheld, so "
                        f"remove it -- a baseline that only grows stops describing anything")

    # --- E ---
    with open(BUILD, encoding="utf-8") as fh:
        build = fh.read()
    code = "\n".join(line.split("#", 1)[0] for line in build.splitlines())
    if 'source(file.path(script_dir, "R", "resolve_collapse_groups.R"))' not in code:
        problems.append("E build.R no longer sources R/resolve_collapse_groups.R")
    if "resolve_collapse_groups(" not in code:
        problems.append("E build.R no longer publishes through resolve_collapse_groups()")
    if re.search(r"mean\(\s*\.data\$value", code) or re.search(r"value\s*=\s*mean\(", code):
        problems.append("E build.R averages `value` again: every key with disagreeing candidates "
                        "would publish a number equal to none of them (issue 451)")
    if "still carry more than one row" not in code:
        problems.append("E build.R no longer refuses to write a table with a duplicate key")

    # --- F ---
    for key, want in ANCHORS.items():
        r = by_key.get(key)
        if want["resolution"] == "absent":
            if r is not None:
                problems.append(f"F {'/'.join(key)}: anchor should have ONE candidate and be absent "
                                f"from the table, but reads {r['resolution']!r}. {want['why']}")
            continue
        if r is None:
            problems.append(f"F {'/'.join(key)}: anchor is GONE from the table. {want['why']}")
            continue
        for f, v in want.items():
            if f != "why" and r[f] != v:
                problems.append(f"F {'/'.join(key)}: {f} is {r[f]!r}, expected {v!r}. {want['why']}")

    counts = {}
    for r in rows:
        counts[r["resolution"]] = counts.get(r["resolution"], 0) + 1
    print(f"{len(rows)} published key(s) had competing candidates: "
          + ", ".join(f"{k_} {v}" for k_, v in sorted(counts.items())))
    print(f"withheld keys documented in the baseline: {len(base_keys)}; anchors checked: {len(ANCHORS)}")
    if problems:
        print(f"FAIL: {len(problems)} published-collapse problem(s)", file=sys.stderr)
        for p in problems[:40]:
            print("  - " + p, file=sys.stderr)
        return 1
    print("PASS: every published key resolves to one candidate by the stated rules, and every "
          "withheld key is documented")
    return 0


if __name__ == "__main__":
    sys.exit(main())
