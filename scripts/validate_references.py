#!/usr/bin/env python3
"""Validate that wiki pages only name things that exist.

The wiki is the database's source of truth, so a page can assert something the
database does not contain and nothing notices. Four ways that happened:

  1. FRONTMATTER KEYS. Six pages used CSV *column* names where
     scripts/build_database.py expects *frontmatter* keys — `wiki_status:` for
     `status:`, `iso3_code:` for `iso3:`, `cow_code:` for `cow:`. The builder
     reads only the keys it knows, so it silently dropped them: five polities
     had no status in the database and two had no ISO code, values that look
     present on the page and resolve to nothing. This check re-derives the
     legal key set from the builder's own CSV_COLUMN_TO_FM_KEY map, so the two
     can never drift apart, and reports the CSV-column-name typos by name.

  2. DANGLING CHAIN REFS. `can-1948-2025` listed `predecessor: [CAN-1866-1948]`
     — a code that does not exist; the real predecessor is `CAN-1886-1948`.
     Nothing checked that predecessor/successor codes resolve to real rows, and
     17 more were dangling.

  3. SYMMETRY AND DEAD TARGETS. If A lists B as successor, B should list A as
     predecessor; and a live page should not point its chain at a `retired` or
     `superseded` row (that is how the retired-polity routing bug propagated).
     Both are noisy on legacy data — hundreds of one-sided links survive from
     pre-split chains — so they are reported as WARNINGS and never fail. Fixing
     them is a data cleanup, not a gate.

  4. CODES IN PAGE BODIES. `bra-1800-2025` was titled "Brazil (to 1903)" and
     named a successor `BRA-1903-1909` that did not exist, while the CSV held a
     single 225-year row; `jam-1800-2025` referenced a nonexistent
     `JAM-1886-1962`. Both are the same failure: a body written for a split that
     was never applied.

     Bodies legitimately name codes that do not exist — deleted rows, rejected
     or deferred splits, hypothetical future rows ("a future ALK-1959-2025 row
     would..."). Roughly 160 such mentions are historically accurate prose, so
     bare mentions are only WARNINGS. What fails is a code the page *asserts*
     exists:
       - a code on a `Predecessor:` / `Successor:` line, and
       - a markdown link to a wiki/polities page that is not there.
     Codes inside fenced code blocks are ignored, as are the codes named in a
     retired/superseded page's banner, which deliberately point at the rows
     that replaced it.

  5. TITLE PERIODS. The same "body written for a split that was never applied"
     failure also shows up in the page's own heading, where no code has to be
     named at all: `blz-1800-2025` — a `superseded` umbrella row spanning
     1800-2025 — was titled "# Belize (to 1886)", the name of the *separate*
     `BLZ-1800-1886` row that replaced part of it, and its whole body described
     that pre-1886 row. Check 4 cannot see this: every code the page mentions
     exists. Eight more pages claimed a period their row does not have
     ("# Gambia (to 1889)" on a 1800-2025 row, "# UAE (1913-1971)" on
     1892-2025).

     So a period claimed in the `# ` heading or in `polity_name` — `(to YYYY)`,
     `(from YYYY)`, `(YYYY-YYYY)` — must match the row's own years. `end_year`
     is exclusive here, and the repo writes both conventions in names
     (`BLZ-1800-1886` is "Belize (to 1886)"), so an end claim of `end_year` or
     `end_year - 1` is accepted. The years embedded in the polity CODE are
     accepted too: where a code and its columns disagree the offender is
     scripts/validate_code_year_agreement.py, not the title. A parenthesis that
     names a code, or says SUPERSEDED/RETIRED, is a redirection banner and is
     skipped.

Known legacy failures for checks 2, 4 and 5 are listed in
scripts/validate_references_baseline.txt so the gate gets NEW ones rather than
staying permanently red. That file is a tracked backlog, not an exemption.

Which is why the run also reports baseline lines that NOTHING matches any more.
Measured 2026-08-17: 19 of 52 lines were dead — the page had since stopped naming
the thing (bgd-1947-1971 no longer mentions PAK-1940-1947) or the reference was
repointed — so a third of the "backlog" recorded work already done. They are
reported as a WARNING rather than a failure: a dead line suppresses nothing, and
failing on one would make any page edit that happens to fix a reference turn the
gate red in a PR that never touched this file.

Usage:
  python3 scripts/validate_references.py [--warnings] [--no-baseline]
Exit 1 if any hard check fails.
"""
import argparse
import csv
import glob
import os
import re
import sys

import yaml

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLITIES = os.path.join(REPO, "wiki/polities")
CSV_PATH = os.path.join(REPO, "data/final/polities_database.csv")
BASELINE = os.path.join(REPO, "scripts/validate_references_baseline.txt")

ap = argparse.ArgumentParser()
ap.add_argument("--warnings", action="store_true",
                help="list every symmetry/dead-target/prose warning, not just counts")
ap.add_argument("--no-baseline", action="store_true",
                help="ignore the baseline file and report the full legacy backlog")
A = ap.parse_args()

# ---------------------------------------------------------------------------
# The legal frontmatter key set, taken from the builder itself
# ---------------------------------------------------------------------------
# Read out of build_database.py's source rather than imported: importing it pulls
# in osgeo, and this check needs nothing but text. Either way the key set is the
# builder's, so the two cannot drift.
def builder_key_map():
    src = open(os.path.join(REPO, "scripts/build_database.py"), encoding="utf-8").read()
    try:
        body = src.split("CSV_COLUMN_TO_FM_KEY = {", 1)[1].split("}", 1)[0]
    except IndexError:
        sys.exit("scripts/build_database.py no longer declares CSV_COLUMN_TO_FM_KEY; "
                 "this check reads its key set from there")
    return {m.group(1): m.group(2)
            for m in re.finditer(r'"([^"]+)"\s*:\s*"([^"]+)"', body)}


CSV_COLUMN_TO_FM_KEY = builder_key_map()
BUILDER_KEYS = set(CSV_COLUMN_TO_FM_KEY.values())

# CSV column names that are NOT the frontmatter key: writing one of these is the
# typo class this check exists for, so name it explicitly rather than as "unknown".
CSV_ONLY_KEYS = {c: k for c, k in CSV_COLUMN_TO_FM_KEY.items() if c != k}

# Descriptive keys the builder ignores by design. They document a decision on the
# page (why a polygon is a proxy, why a row was retired) and are not written to
# the CSV. Anything outside this set plus BUILDER_KEYS is reported.
DESCRIPTIVE_KEYS = {
    "sources",                      # source slugs cited by the page
    # `container` declares the member -> container edges this page asserts, each with its own
    # validity interval, and is emitted to data/final/polity_containment.csv by
    # scripts/write_polity_containment.py rather than to a CSV column (whep#51). It is descriptive
    # here for the same reason the polygon-decision keys are: the builder does not read it, a
    # separate writer does. Its shape is checked by scripts/validate_polity_containment.py.
    "container",
    "redirect",                     # retired row -> the row that replaced it
    "superseded_by", "superseded_date", "superseded_reason",
    "retired_date", "retired_reason",
    "verification_status",
    "sovereign_iso3",               # e.g. PTIND: colony with no ISO3 of its own
    "polygon_method",               # how a constructed polygon was composed
    "polygon_confidence",
    "last_updated",                 # editorial date, read by nothing on purpose
    "polygon_notes",
    "polygon_status_reason",
    "polygon_approximation_note",
    "polygon_feature_date",         # exact source feature date, where known
    "polygon_vintage", "polygon_vintage_note", "polygon_vintage_proxy",
    "polygon_vintage_drift", "polygon_vintage_drift_note",
}
ALLOWED_KEYS = BUILDER_KEYS | DESCRIPTIVE_KEYS

CODE_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,9}-\d{4}-\d{4}\b")
# a link to another polity page, e.g. [CAN-1886-1948](can-1886-1948.md)
PAGE_LINK_RE = re.compile(r"\]\((?!\.\.|https?:)([a-z0-9][a-z0-9_-]*\.md)(?:#[^)]*)?\)")
CHAIN_LINE_RE = re.compile(r"^\s*[-*>]?\s*\**\s*(?:Predecessor|Successor)s?\b", re.I)
DEAD_STATUSES = ("retired", "superseded")

# check 5: a period claimed inside a parenthesis, e.g. "Gambia (to 1889)"
PAREN_RE = re.compile(r"\(([^()]*)\)")
YEAR = r"(1[5-9]\d\d|20\d\d)"
PERIOD_FORMS = (
    ("range", re.compile(r"^" + YEAR + r"\s*[-‒-―]\s*" + YEAR + r"$")),
    ("to", re.compile(r"^(?:to|until|through|up to)\s+" + YEAR + r"$", re.I)),
    ("from", re.compile(r"^(?:from|since)\s+" + YEAR + r"$", re.I)),
)
# a parenthesis that redirects rather than dates the row
BANNER_WORDS = re.compile(r"SUPERSEDED|RETIRED|REPLACED|MERGED|SPLIT", re.I)


def period_claims(text):
    """Periods a title/name claims, as (form, start_or_None, end_or_None, raw)."""
    out = []
    for m in PAREN_RE.finditer(text or ""):
        inner = m.group(1).strip()
        if BANNER_WORDS.search(inner) or CODE_RE.search(inner):
            continue
        for form, rx in PERIOD_FORMS:
            hit = rx.match(inner)
            if not hit:
                continue
            if form == "range":
                out.append((form, int(hit.group(1)), int(hit.group(2)), inner))
            elif form == "to":
                out.append((form, None, int(hit.group(1)), inner))
            else:
                out.append((form, int(hit.group(1)), None, inner))
            break
    return out


def code_years(code):
    """The years embedded in a polity code, or None."""
    m = re.search(r"-(\d{4})-(\d{4})$", str(code or ""))
    return (int(m.group(1)), int(m.group(2))) if m else None


def load_baseline():
    """(page, target) pairs already known to be broken. Format: `page target`."""
    if A.no_baseline or not os.path.exists(BASELINE):
        return set()
    out = set()
    # every line read is a line that must still be matched by something, or it is
    # a dead entry; see BASELINE_USED below.
    for line in open(BASELINE, encoding="utf-8"):
        line = line.split("#")[0].strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            out.add((parts[0], parts[1]))
    return out


def as_codes(value):
    """Frontmatter predecessor/successor may be a list, a scalar, `~` or empty."""
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    else:
        items = re.split(r"[;,]", str(value))
    out = []
    for item in items:
        s = str(item).strip()
        if s and s not in ("~", "NA", "None", "[]"):
            out.append(s)
    return out


def split_page(path):
    text = open(path, encoding="utf-8").read()
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    try:
        fm = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, text[end + 5:]


def body_lines(body):
    """Body lines outside fenced code blocks, as (lineno, text)."""
    out, fenced = [], False
    for i, line in enumerate(body.split("\n"), 1):
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            out.append((i, line))
    return out


# ---------------------------------------------------------------------------
# Load the database and the pages
# ---------------------------------------------------------------------------
db_status = {}
with open(CSV_PATH, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        db_status[row["polity_code"]] = (row.get("wiki_status") or "").strip()

pages = [p for p in sorted(glob.glob(os.path.join(POLITIES, "*.md")))
         if not os.path.basename(p).startswith("_")]  # _template.md holds placeholders
page_files = {os.path.basename(p) for p in glob.glob(os.path.join(POLITIES, "*.md"))}
baseline = load_baseline()
BASELINE_USED = set()


def baselined(slug, target):
    """True if this finding is baselined, recording that the line was needed."""
    if (slug, target) in baseline:
        BASELINE_USED.add((slug, target))
        return True
    return False

parsed = {}
for path in pages:
    fm, body = split_page(path)
    parsed[os.path.basename(path)[:-3]] = (fm, body)

by_code = {fm.get("polity_code"): (slug, fm)
           for slug, (fm, _) in parsed.items() if fm.get("polity_code")}

print(f"{len(pages)} polity pages; {len(db_status):,} database rows; "
      f"{len(ALLOWED_KEYS)} legal frontmatter keys "
      f"({len(BUILDER_KEYS)} from the builder)")

# ---------------------------------------------------------------------------
# 1. Frontmatter keys the builder does not read
# ---------------------------------------------------------------------------
csv_name_typos, unknown_keys = [], []
for slug, (fm, _) in sorted(parsed.items()):
    for key in fm:
        if key in ALLOWED_KEYS:
            continue
        if key in CSV_ONLY_KEYS:
            csv_name_typos.append((slug, key, CSV_ONLY_KEYS[key]))
        else:
            unknown_keys.append((slug, key))

print(f"\n1. FRONTMATTER KEYS: {len(csv_name_typos)} CSV column name(s) used as a "
      f"key, {len(unknown_keys)} unrecognised key(s)")
for slug, key, want in csv_name_typos:
    print(f"   FAIL {slug:26s} `{key}:` is a CSV column name; the builder reads "
          f"`{want}:` and drops this")
for slug, key in unknown_keys:
    print(f"   FAIL {slug:26s} `{key}:` is read by nothing — a typo, or add it to "
          f"DESCRIPTIVE_KEYS")

# ---------------------------------------------------------------------------
# 2. predecessor / successor codes must resolve
# ---------------------------------------------------------------------------
dangling, dangling_baselined = [], 0
for slug, (fm, _) in sorted(parsed.items()):
    for field in ("predecessor", "successor"):
        for code in as_codes(fm.get(field)):
            if code in db_status:
                continue
            if baselined(slug, code):
                dangling_baselined += 1
                continue
            dangling.append((slug, field, code))

print(f"\n2. DANGLING PREDECESSOR/SUCCESSOR: {len(dangling)} new "
      f"({dangling_baselined} baselined)")
for slug, field, code in dangling:
    print(f"   FAIL {slug:26s} {field}: {code}  (no such row)")

# ---------------------------------------------------------------------------
# 3. symmetry and dead targets — WARNINGS, never fail
# ---------------------------------------------------------------------------
asymmetric, dead = [], []
for slug, (fm, _) in sorted(parsed.items()):
    me = fm.get("polity_code")
    for field, mirror in (("successor", "predecessor"), ("predecessor", "successor")):
        for code in as_codes(fm.get(field)):
            other = by_code.get(code)
            if other is not None and me not in as_codes(other[1].get(mirror)):
                asymmetric.append((slug, field, code, mirror))
    if str(fm.get("status")) in DEAD_STATUSES:
        continue
    for field in ("predecessor", "successor"):
        for code in as_codes(fm.get(field)):
            if db_status.get(code) in DEAD_STATUSES:
                dead.append((slug, field, code, db_status[code]))

print(f"\n3. SYMMETRY AND DEAD TARGETS (warnings, do not fail): "
      f"{len(asymmetric)} one-sided link(s), {len(dead)} link(s) into a "
      f"retired/superseded row")
shown = asymmetric if A.warnings else asymmetric[:5]
for slug, field, code, mirror in shown:
    print(f"   warn {slug:26s} {field}: {code}, but {code} does not list it as "
          f"{mirror}")
if len(shown) < len(asymmetric):
    print(f"   ... {len(asymmetric) - len(shown)} more (--warnings to list all)")
for slug, field, code, status in (dead if A.warnings else dead[:8]):
    print(f"   warn {slug:26s} {field}: {code} is {status}")
if not A.warnings and len(dead) > 8:
    print(f"   ... {len(dead) - 8} more (--warnings to list all)")

# ---------------------------------------------------------------------------
# 4. codes and page links in bodies
# ---------------------------------------------------------------------------
asserted, broken_links, prose = [], [], []
asserted_baselined = broken_baselined = 0
for slug, (fm, body) in sorted(parsed.items()):
    # a retired/superseded page's banner deliberately names its replacements
    banner_codes = set()
    if str(fm.get("status")) in DEAD_STATUSES:
        banner_codes = {str(c) for c in
                        as_codes(fm.get("redirect")) + as_codes(fm.get("superseded_by"))}
    for lineno, line in body_lines(body):
        for m in PAGE_LINK_RE.finditer(line):
            target = m.group(1)
            if target in page_files:
                continue
            if baselined(slug, target):
                broken_baselined += 1
                continue
            broken_links.append((slug, lineno, target))
        for m in CODE_RE.finditer(line):
            code = m.group(0)
            if code in db_status or code in banner_codes:
                continue
            if CHAIN_LINE_RE.match(line):
                if baselined(slug, code):
                    asserted_baselined += 1
                else:
                    asserted.append((slug, lineno, code, line.strip()[:70]))
            else:
                prose.append((slug, lineno, code))

print(f"\n4. CODES IN PAGE BODIES: {len(asserted)} new code(s) asserted as a chain "
      f"neighbour ({asserted_baselined} baselined), {len(broken_links)} broken page "
      f"link(s) ({broken_baselined} baselined)")
for slug, lineno, code, ctx in asserted:
    print(f"   FAIL {slug:26s} L{lineno}: {code} does not exist — {ctx}")
for slug, lineno, target in broken_links:
    print(f"   FAIL {slug:26s} L{lineno}: link to {target}, which is not in "
          f"wiki/polities/")

print(f"\n   {len(prose)} bare prose mention(s) of a nonexistent code "
      f"(warning: deleted rows, rejected splits and hypothetical rows are "
      f"legitimately named)")
for slug, lineno, code in (prose if A.warnings else prose[:5]):
    print(f"   warn {slug:26s} L{lineno}: {code}")
if not A.warnings and len(prose) > 5:
    print(f"   ... {len(prose) - 5} more (--warnings to list all)")

# ---------------------------------------------------------------------------
# 5. periods claimed by the page title / polity_name
# ---------------------------------------------------------------------------
bad_titles, title_baselined = [], 0
for slug, (fm, body) in sorted(parsed.items()):
    try:
        start = int(fm["start_year"])
        end = int(fm["end_year"])
    except (KeyError, TypeError, ValueError):
        continue
    ok_start, ok_end = {start}, {end, end - 1}
    embedded = code_years(fm.get("polity_code"))
    if embedded:                       # code/columns disagreement is another gate's
        ok_start.add(embedded[0])
        ok_end.update((embedded[1], embedded[1] - 1))

    heading = next((line.strip() for _, line in body_lines(body)
                    if line.startswith("# ")), "")
    for where, text in (("title", heading), ("polity_name", fm.get("polity_name"))):
        for form, cs, ce, raw in period_claims(text):
            wrong = ((cs is not None and cs not in ok_start)
                     or (ce is not None and ce not in ok_end))
            if not wrong:
                continue
            if baselined(slug, f"({raw})"):
                title_baselined += 1
                continue
            bad_titles.append((slug, where, raw, start, end))

print(f"\n5. TITLE PERIODS: {len(bad_titles)} claimed period(s) the row does not "
      f"have ({title_baselined} baselined)")
for slug, where, raw, start, end in bad_titles:
    print(f"   FAIL {slug:26s} {where} claims ({raw}), but the row is "
          f"{start}-{end}")

# ---------------------------------------------------------------------------
# 6. baseline lines nothing matched — warnings: a dead line hides no defect, but
#    it records work already done as if it were outstanding
# ---------------------------------------------------------------------------
stale = sorted(baseline - BASELINE_USED)
print(f"\n6. STALE BASELINE LINES (warnings, do not fail): {len(stale)} of "
      f"{len(baseline)} line(s) matched nothing in this run")
for slug, target in (stale if A.warnings else stale[:8]):
    print(f"   warn {slug:26s} {target} is no longer named by the page — delete "
          f"the baseline line")
if not A.warnings and len(stale) > 8:
    print(f"   ... {len(stale) - 8} more (--warnings to list all)")

# ---------------------------------------------------------------------------
fail = bool(csv_name_typos or unknown_keys or dangling or asserted or broken_links
            or bad_titles)
print(f"\n{'FAIL' if fail else 'PASS'}: {len(csv_name_typos) + len(unknown_keys)} "
      f"bad frontmatter key(s), {len(dangling)} dangling chain ref(s), "
      f"{len(asserted)} asserted-but-absent code(s), {len(broken_links)} broken "
      f"page link(s), {len(bad_titles)} bad title period(s); "
      f"{len(asymmetric) + len(dead) + len(prose) + len(stale)} warning(s) ignored")
sys.exit(1 if fail else 0)
