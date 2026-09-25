#!/usr/bin/env python3
"""Check that every applied alias can actually route data to a polity.

Why: an alias whose target is unusable does not fail loudly, it does NOTHING.
`matchlib.Matcher` drops a rule whose target is not a known polity code, so a
broken row is indistinguishable from an absent one — the source label simply goes
unmatched and its data falls to whatever the deterministic routes decide.

FIVE such rows were found in the registry, all silently inert, some since the day
they were written:

  `china, taiwan province of`  the LABEL contains a comma and was written
                               UNQUOTED, so every field shifted one column left
                               and the target landed in `confidence`
  `Pakistan` (fao1952)         the same, via a comma in `common_name`
  `British Togoland`           fields written in the wrong columns; the target
                               ended up in `year_start`, leaving it empty
  `Abyssinia`                  target was the bare prefix `ETH`, which names a
                               family rather than a period
  `papua new guinea` (iia)     target GNGU-1884-1914 does not exist (issue #42)

A sixth row was merely redundant rather than inert: `serbia` scoped to a `source`
of "Kingdom of Serbia (independent)", the polity's own name. A correct blanket
rule already covered the label, so nothing was lost — but the value leaked into
the published contract's list of sources, which is why check 5 exists.

Three of the five are what a CSV containing unquoted prose does eventually. This
script exists so the next one is caught by a gate rather than by someone noticing,
years later, that a label never resolved.

Checks:
  1. `polity_code` names a LIVE polity in the database. Dead targets are
     rejected too: routing data to a retired or superseded row is the mistake the
     whole DEAD_STATUS mechanism exists to prevent.
  2. `polity_code` is a full periodised code, not a bare family prefix.
     `ETH` is not a polity; `ETH-1907-1936` is.
  3. `confidence` is one of the expected values, and the year fields are either
     empty or four-digit years. Both are shift detectors: when a column slips,
     these are where the debris lands.
  4. `year_start <= year_end` when both are present.
  5. `source` is a slug or empty, never prose.
  6. a `back_cast` row ends before its target begins (year_end < start_year).
  7. `indicator` (the optional scope, 2026-09-25; blank = any) names a value of the panel's
     own `indicator` vocabulary, and only on a panel slug.
  8. no two rules on one label and source (a blank source counting as every source) claim a
     common year unless their indicator scopes are DISJOINT -- both set, to different values.
  9. the number of scoped rows is pinned, bidirectionally.

Usage:
  python3 scripts/validate_aliases.py
"""
import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALIASES = os.path.join(
    REPO, "pipelines/polity-autoimprove/state/applied_aliases.csv"
)
POLITIES = os.path.join(REPO, "data/final/polities_database.csv")

DEAD_STATUS = ("retired", "superseded")
CONFIDENCE_VALUES = frozenset({"high", "medium", "low", ""})
CODE_RE = re.compile(r"^[A-Za-z0-9]+(-[A-Za-z0-9]+)*-[0-9]{4}-[0-9]{4}$")
# A source is a slug naming where the label came from (`faostat`, `fao1952`,
# `iia-cotton`, `whep-split-2026-06-29`), or empty for a rule that applies to any
# source. Prose here means the column was filled with the wrong thing: one row had
# `source` set to the POLITY'S NAME, "Kingdom of Serbia (independent)", which
# scoped the alias to a source that does not exist. It happened to be harmless — a
# correct blanket rule already covered the label — but it also leaked into the
# published contract's list of sources.
SOURCE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
YEAR_RE = re.compile(r"^[0-9]{4}$")

polities = list(csv.DictReader(open(POLITIES, encoding="utf-8")))
live = {r["polity_code"] for r in polities if r["wiki_status"] not in DEAD_STATUS}
dead = {r["polity_code"] for r in polities if r["wiki_status"] in DEAD_STATUS}

# polity_code -> (start_year, end_year), for the before-target check below. Dead rows included:
# an alias pointing at a dead polity is already reported above, and its years are still wrong.
spans = {}
for _r in polities:
    try:
        spans[_r["polity_code"]] = (int(_r["start_year"]), int(_r["end_year"]))
    except (KeyError, TypeError, ValueError):
        continue

# --- the indicator scope (checks 7-9) -------------------------------------------------------
#
# WHY IT EXISTS. The alias key is (label, source, years), so a panel unit whose INDICATORS are two
# territories cannot be routed. Measured 2026-09-25 on whep_production_subnational.parquet: CHL-LL
# reports crops (area, production, yield) for Los Lagos + Los Rios in every year -- Los Rios has no
# crop row at all and Los Lagos' crops do not step down at the 2007 split -- while its landuse
# (42,302 km2 in every year) and livestock are Los Lagos alone (Los Rios carries its own), under one
# id and one name. CHL-BI is the same shape with Nuble. An optional `indicator` column, BLANK = ANY,
# the convention source_label_item_corrections.csv took for its unit/indicator scope in #700.
#
# The vocabulary is the panel's own `indicator` column, every value it carries (8,929,673 rows,
# measured 2026-09-25). A scope outside it selects no row, and a rule that selects nothing leaves
# those rows routed nowhere -- so a typo fails here, in CI, where the panel is absent.
SCOPE_INDICATORS = frozenset({"area", "production", "yield", "livestock_stock", "landuse"})
# Panel slugs: pipelines/agent-harness/policy.json `alias_derivation` (panel_slug and the
# `whep-lab-` prefix). No other source has a pinned indicator vocabulary, and layer B's
# `indicator` is a table id, not a panel indicator, so matchlib skips scoped rows entirely: a
# scope on a layer-B slug would silently route nothing there.
PANEL_SLUG = "juan-subnational"
PANEL_SLUG_PREFIXES = ("whep-lab-",)
# How many rows carry a scope. PINNED, both ways, and 0 on purpose: the consumer (eduaguilera/whep
# `resolve_polity_label()`, whep issue 1294) must match the column before the first scoped rule is
# published, because one that ignores it sees two rules for one label and years and takes whichever
# it reaches first. Raise this in the same change as the rows, once the consumer honours the scope.
BASELINE_SCOPED_ROWS = 0

rows = list(csv.DictReader(open(ALIASES, encoding="utf-8")))
problems: list[str] = []

for i, r in enumerate(rows, start=2):  # +2: header is line 1
    label = r.get("source_label", "")
    target = (r.get("polity_code") or "").strip()
    conf = (r.get("confidence") or "").strip()
    y0 = (r.get("year_start") or "").strip()
    y1 = (r.get("year_end") or "").strip()

    where = f"line {i}, {label!r}"

    if not target:
        problems.append(
            f"{where}: no polity_code — the alias can never route anything"
        )
    elif not CODE_RE.match(target):
        hint = (
            " (looks like a bare family prefix; an alias must name one period)"
            if "-" not in target
            else ""
        )
        problems.append(f"{where}: target {target!r} is not a polity code{hint}")
    elif target in dead:
        problems.append(
            f"{where}: target {target!r} is RETIRED or SUPERSEDED and must not "
            f"receive data"
        )
    elif target not in live:
        problems.append(
            f"{where}: target {target!r} is not in the polities database"
        )

    src = (r.get("source") or "").strip()
    if src and not SOURCE_RE.match(src):
        problems.append(
            f"{where}: source {src!r} is not a slug — an alias scoped to a source "
            f"that does not exist can never match, and the value leaks into the "
            f"published contract"
        )

    if conf not in CONFIDENCE_VALUES:
        problems.append(
            f"{where}: confidence {conf!r} is not one of "
            f"{sorted(v for v in CONFIDENCE_VALUES if v)} — a column has probably "
            f"shifted (an unquoted comma in the label does this)"
        )
    for field, value in (("year_start", y0), ("year_end", y1)):
        if value and not YEAR_RE.match(value):
            problems.append(
                f"{where}: {field}={value!r} is not a four-digit year — a column "
                f"has probably shifted"
            )
    if YEAR_RE.match(y0) and YEAR_RE.match(y1) and int(y0) > int(y1):
        problems.append(f"{where}: year_start {y0} is after year_end {y1}")

# --- aliases beginning before their target polity existed ------------------------------
#
# An alias year_start earlier than its target's start_year routes those years to a polity that
# did not yet exist. Four existed on 2026-08-11 (issue 54) and THREE WERE COPIED RANGES rather
# than decisions, which their own `basis` text showed once read:
#
#   Gold Coast       1821 -> 1898   basis recorded the fao1952 data years as 1937-1951, and
#                                   GHA-1821-1888 and GHA-1888-1898 both exist, so any data
#                                   before 1898 was going to the wrong polity while the right
#                                   ones sat unused
#   Portuguese Timor 1702 -> 1800   1702 predates this database's own start
#   French Morocco   1904 -> 1911   the 1904 start was inherited from MOR-1904-1956, the
#                                   duplicate retired on 2026-06-24, and never re-checked
#                                   against the replacement
#
# The fourth IS a decision, and its basis says so: "Province of Trieste ~700 km2 footprint = FTT;
# cannot attribute to all-Italy ~300000 km2; closest territorial match". For 1937-1946 Trieste was
# Italian and no Free Territory existed, so the alternatives were the whole of Italy -- 430x the
# area -- or dropping the label. It is pinned rather than fixed, which is what makes it a decision
# on the record instead of an unexamined range.
#
# Bidirectional: a fifth fails, and this one fails if it is ever resolved.
#
# Re-measured 2026-08-14 over all 913 published aliases, which closes issue 54 in both
# directions. Beginning before the target: 1 (this pin), down from the issue's 4. Ending after
# the target: 0 alias now ends MORE than one year past its target's coverage, down from the
# issue's 2 -- "tanganyika" and "tanzania" claimed to 1964 against TAN-1922-1964 and were
# clipped to 1960 during the issue-79 work, i.e. they were decided against the COLUMNS reading
# (1922-1961) rather than waiting on the code/columns disagreement the issue expected to settle
# them; TAN's code-vs-columns split itself remains baselined in validate_code_year_agreement.py,
# which is that gate's open item and no longer this one's. The remaining 198 aliases whose
# inclusive year_end equals their target's exclusive end_year are the convention working, and
# validate_alias_year_coverage.py pins that set by identity.
# EMPTIED 2026-09-24: the Trieste rule is now marked `back_cast` (fao1952 states its pre-war columns on
# present boundaries, source_conventions.csv), so it is exempt by design like every other back_cast rule
# and no longer an unexamined range. A new entry must again be a decision with its basis on the record.
BASELINE_BEFORE_TARGET = frozenset()

# A `back_cast` alias BEGINS BEFORE ITS TARGET BY DESIGN, and that is the whole point of the
# disposition. The routing verdict schema has always specified it -- "the source reports these years
# FOR this territory but is projecting it backwards ... so the data routes to the polity while the
# polity's own span still begins when the territory did" -- and until 2026-09-22 nothing could
# express it, so 377,822 panel rows resolved to no polity at all.
#
# This exemption does NOT weaken what the check was built for. Its four original findings were
# UNEXAMINED COPIED RANGES: Gold Coast reaching back to 1821 past two polities that did exist,
# Portuguese Timor to 1702, French Morocco inheriting 1904 from a retired duplicate. None carried a
# disposition; all three were silently wrong about which polity should have the years. A `back_cast`
# row asserts the opposite -- that no polity held this boundary then, which is why the reconstruction
# lands on the modern one -- and it says so in a column a consumer can filter on.
before_target = set()
for r in rows:
    target = (r.get("polity_code") or "").strip()
    span = spans.get(target)
    y0 = (r.get("year_start") or "").strip()
    if not span or not YEAR_RE.match(y0):
        continue
    if (r.get("disposition") or "").strip() == "back_cast":
        continue
    if int(y0) < span[0]:
        before_target.add(((r.get("source_label") or "").strip(),
                           (r.get("source") or "").strip(), target))
for key in sorted(before_target - BASELINE_BEFORE_TARGET):
    problems.append(
        f"alias {key[0]!r} [{key[1] or 'no source'}] begins before {key[2]} existed — those "
        f"years route to a polity that did not yet exist. Clip year_start to the target's "
        f"start_year, or route the earlier years to a polity that does cover them (issue 54)"
    )
# ...and a `back_cast` row must END before its target begins, which is the other half of what the
# disposition asserts. The exemption above is sound only if the row's years are all BEFORE the
# polity existed; a back_cast reaching into its target's own span is an observed rule wearing the
# exemption, and one onto the era's container is the region-averaged-with-its-country defect
# derive_aliases.py blocks as `back_cast_inside`. Holds for every row on 2026-09-24, so it is pinned
# with no baseline.
for i, r in enumerate(rows, start=2):
    if (r.get("disposition") or "").strip() != "back_cast":
        continue
    target = (r.get("polity_code") or "").strip()
    span = spans.get(target)
    y1 = (r.get("year_end") or "").strip()
    if not span:
        continue  # an unknown target is already reported by check 1
    if not YEAR_RE.match(y1):
        problems.append(
            f"line {i}, {r.get('source_label', '')!r}: back_cast row has no year_end -- a "
            f"back_cast must end before {target} begins ({span[0]})"
        )
    elif int(y1) >= span[0]:
        problems.append(
            f"line {i}, {r.get('source_label', '')!r}: back_cast row ends {y1}, not before "
            f"{target} begins ({span[0]}) -- years inside the target's span are observed, not "
            f"back-cast; split the row or drop the disposition for those years"
        )

# --- 7: the scope names a panel indicator, on a panel slug ------------------------------------
def _scope(r):
    return (r.get("indicator") or "").strip()


for i, r in enumerate(rows, start=2):
    ind = _scope(r)
    if not ind:
        continue
    src = (r.get("source") or "").strip()
    where = f"line {i}, {r.get('source_label', '')!r} [{src or 'no source'}]"
    if not (src == PANEL_SLUG or src.startswith(PANEL_SLUG_PREFIXES)):
        problems.append(
            f"{where}: indicator scope {ind!r} on a source with no panel indicator vocabulary -- "
            f"the scope exists for the subnational panel's slugs only, and matchlib skips "
            f"scoped rows, so the rule would route nothing")
    elif ind not in SCOPE_INDICATORS:
        problems.append(
            f"{where}: indicator scope {ind!r} is not a panel indicator "
            f"({sorted(SCOPE_INDICATORS)}) -- the rule would select no row")


# --- 8: rules on one label and source that claim a common year --------------------------------
#
# Two rules claiming one row leave the consumer to choose by file order. For UNSCOPED rules that is
# validate_alias_chain_overlaps.py's business (it baselines the historical touches); what is new
# with the scope is this: a scoped rule beside an unscoped one on common years collides, because a
# blank scope means ANY indicator -- so neither may be read as "the default" and the other as "the
# exception". Two scoped rules collide unless their values differ. Labels compared case-folded, as
# the chain gate compares them; a blank `source` applies to every source, as in matchlib.
def _span(r):
    y0 = (r.get("year_start") or "").strip()
    y1 = (r.get("year_end") or "").strip()
    return (int(y0) if YEAR_RE.match(y0) else -10**6, int(y1) if YEAR_RE.match(y1) else 10**6)


by_label: dict = {}
for i, r in enumerate(rows, start=2):
    by_label.setdefault((r.get("source_label") or "").strip().lower(), []).append((i, r))
for label, group in by_label.items():
    if not any(_scope(r) for _, r in group):
        continue
    for k, (ia, a) in enumerate(group):
        for ib, b in group[k + 1:]:
            if not (_scope(a) or _scope(b)):
                continue   # unscoped pairs: the chain gate's
            sa, sb = (a.get("source") or "").strip(), (b.get("source") or "").strip()
            if sa and sb and sa != sb:
                continue
            (a0, a1), (b0, b1) = _span(a), _span(b)
            if max(a0, b0) > min(a1, b1):
                continue
            if _scope(a) and _scope(b) and _scope(a) != _scope(b):
                continue   # disjoint: no row carries two indicators
            problems.append(
                f"lines {ia} and {ib}, {label!r}: rules scoped "
                f"{_scope(a) or '(any)'!r} -> {a.get('polity_code')} and "
                f"{_scope(b) or '(any)'!r} -> {b.get('polity_code')} both claim "
                f"{max(a0, b0)}-{min(a1, b1)}, so file order would decide -- a blank scope "
                f"means ANY indicator; scope every rule in the years it is split")

# --- 9: the number of scoped rows ---------------------------------------------------------------
n_scoped = sum(1 for r in rows if _scope(r))
if n_scoped != BASELINE_SCOPED_ROWS:
    problems.append(
        f"{n_scoped} indicator-scoped alias rows against the pinned {BASELINE_SCOPED_ROWS} -- "
        + ("raise BASELINE_SCOPED_ROWS in the same change, and only once the consumer "
           "(whep resolve_polity_label, whep issue 1294) matches `indicator`: one that ignores "
           "it takes whichever of the split's rules it reaches first"
           if n_scoped > BASELINE_SCOPED_ROWS else
           "a scope was blanked or a scoped row deleted, which widens a rule onto the "
           "indicators the scope existed to leave alone"))

for key in sorted(BASELINE_BEFORE_TARGET - before_target):
    problems.append(
        f"alias {key[0]!r} [{key[1] or 'no source'}] -> {key[2]} is baselined as beginning "
        f"before its target existed but no longer does — remove it from BASELINE_BEFORE_TARGET"
    )

if problems:
    print(f"FAIL: {len(problems)} alias problem(s)\n")
    for p in problems[:40]:
        print(f"  {p}")
    if len(problems) > 40:
        print(f"  ... and {len(problems) - 40} more")
    print(
        "\n  A broken alias is INERT, not loud: the Matcher drops it and the "
        "label silently goes unmatched."
    )
    sys.exit(1)

print(
    f"PASS: all {len(rows)} aliases target a live polity, with well-formed "
    f"years and confidence; {n_scoped} indicator-scoped (pinned {BASELINE_SCOPED_ROWS})"
)
