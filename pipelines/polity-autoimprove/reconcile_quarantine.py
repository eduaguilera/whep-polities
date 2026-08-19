#!/usr/bin/env python3
"""Reconcile state/quarantine.csv against current state — keep it an actionable queue.

apply_verdicts.py WRITES quarantine rows (two agents disagreed, or a verdict
failed an execution contract) but nothing ever clears them, so rows survive the
resolution of the very situation they recorded. This is the clearing pass.

A quarantine row is RESOLVED when either:

  banked        the review ledger now shows the assertion `correct`/`fixed` —
                a later verification banked it, so there is nothing to adjudicate.
  route_changed the assertion no longer routes to the `candidate` recorded in the
                row. The disagreement was ABOUT that candidate (e.g. "is this
                'Ethiopia' label really the Italian East Africa aggregate?"); once
                the deterministic pass sends the label somewhere else — a new
                polity was created, an alias was applied, the matcher was fixed —
                the recorded dispute is about a routing that no longer exists. The
                assertion re-derives fresh at the next intake and re-verifies.

Resolved rows are never silently discarded: each is APPENDED to
state/quarantine_resolved.csv with the reason and date (same append-only spirit
as state/verdicts_applied.jsonl) and printed, then dropped from quarantine.csv.

Current routing comes from state/assertions.json when that per-run artefact is
present (authoritative — it is what the verifiers were shown). It is gitignored,
so when absent the route is re-derived deterministically through matchlib from
the polities DB + applied_aliases.csv — the same rule set 00_intake.py uses. A
row whose route cannot be established either way is KEPT (never drop on
ignorance).

Idempotent: a second run finds nothing to resolve and appends nothing (audit
appends are deduped independently of the run date).

Usage:
  python3 reconcile_quarantine.py [--dry-run]
"""
import json, csv, os, sys, datetime
from atomic import write_csv_atomic

H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POLDB = os.path.join(REPO, "data/final/polities_database.csv")
QUARANTINE = os.path.join(H, "quarantine.csv")
RESOLVED = os.path.join(H, "quarantine_resolved.csv")   # append-only audit trail
ASSERTIONS = os.path.join(H, "assertions.json")
LEDGER = os.path.join(H, "review_ledger.csv")
ALIASES = os.path.join(H, "applied_aliases.csv")
# same env override as 00_intake.py / 01_match_and_findings.py (spelling aliases
# live outside the repo); optional here — absent, labels resolve without them
COMMON = os.environ.get("WHEP_COMMON_NAMES",
    "/home/usuario/Nextcloud/WHEP_ERC 2025/Sources/datasets/unclassified_datasets/"
    "Other polities/data/whep-source/common_names.csv")
TODAY = datetime.date.today().isoformat()
DRY = "--dry-run" in sys.argv[1:]

QUAR_FIELDS = ["key", "candidate", "verdict", "polity_code", "confidence", "basis",
               "review_verdict", "review_polity_code", "review_basis", "review_proposal",
               "review_reason", "date"]
RESOLVED_FIELDS = QUAR_FIELDS + ["resolution", "resolution_reason", "current_candidate",
                                 "resolved_by", "resolved_date"]
# date fields excluded: the same resolved row must not re-append on a later day
DEDUP_ON = [f for f in RESOLVED_FIELDS if f not in ("resolved_date",)]
BANKED = ("correct", "fixed")

if not os.path.exists(QUARANTINE):
    print(f"no quarantine file at {QUARANTINE} — nothing to reconcile")
    sys.exit(0)
quar = list(csv.DictReader(open(QUARANTINE)))
if not quar:
    print("quarantine.csv is empty — nothing to reconcile")
    sys.exit(0)

# ---------- current ledger status per assertion key ----------
ledger_status = {}
if os.path.exists(LEDGER):
    for r in csv.DictReader(open(LEDGER)):
        ledger_status[(r.get("key") or "").strip().lower()] = (r.get("status") or "").strip()

# ---------- current route per assertion key ----------
# (a) authoritative: the live evidence bundles, if this run has them
bundle_candidate = {}
if os.path.exists(ASSERTIONS):
    for a in json.load(open(ASSERTIONS))["assertions"]:
        bundle_candidate[a["key"]] = a["candidate"]

# (b) fallback: re-derive through the shared deterministic matcher. The key
#     encodes norm(label)|source|y0-y1, which is exactly assign()'s input minus
#     the row's iso — so route every year of the observed span and collect the
#     targets. "changed" only if the recorded candidate appears for NO year.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_M = None
def matcher():
    global _M
    if _M is None:
        from matchlib import Matcher
        _M = Matcher(POLDB, ALIASES, COMMON if os.path.exists(COMMON) else None, verbose=False)
    return _M

def derived_codes(key):
    """set of polity codes the deterministic pass now routes this key to (or None)."""
    try:
        label_n, src, span = key.rsplit("|", 2)
        y0, y1 = (int(x) for x in span.split("-"))
    except ValueError:
        return None
    M = matcher()
    codes = set()
    for y in range(y0, y1 + 1):
        code, _st, _how = M.assign(label_n, None, src, y)
        if code: codes.add(code)
    return codes or None

def append_dedup(path, fields, row, dedup_on=None):
    """append row unless an identical row (on dedup_on, default all fields) exists.

    Mirrors apply_verdicts.py's helper; dedup_on lets the audit trail ignore the
    resolved_date so re-runs cannot duplicate a row.
    """
    keys = dedup_on or fields
    rows = list(csv.DictReader(open(path))) if os.path.exists(path) else []
    if any(all(str(r.get(k) or "") == str(row.get(k) or "") for k in keys) for r in rows):
        return False
    new = not os.path.exists(path)
    with open(path, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        if new: w.writeheader()
        w.writerow(row)
    return True

# ---------- classify ----------
kept, resolved = [], []
for row in quar:
    key = (row.get("key") or "").strip()
    recorded = (row.get("candidate") or "").strip()
    status = ledger_status.get(key.lower(), "")
    if status in BANKED:
        resolved.append((row, "banked", f"review_ledger status is '{status}' — the "
                                       f"assertion was re-verified and banked", ""))
        continue
    if key in bundle_candidate:
        now, src_of = bundle_candidate[key], "assertions.json"
        changed, shown = now != recorded, now
    else:
        codes = derived_codes(key)
        if not codes:
            kept.append((row, f"route not resolvable (no assertions.json bundle and the "
                              f"deterministic pass returns no candidate) — kept"))
            continue
        now, src_of = codes, "matchlib re-derivation"
        changed, shown = recorded not in codes, "|".join(sorted(codes))
    if changed:
        resolved.append((row, "route_changed",
                         f"assertion no longer routes to the quarantined candidate "
                         f"{recorded}; current route is {shown} ({src_of}) — the recorded "
                         f"disagreement was about {recorded} and no longer applies",
                         shown))
    else:
        kept.append((row, f"still routes to {recorded} ({src_of}); ledger status "
                          f"'{status or 'none'}' — open disagreement, kept"))

# ---------- report ----------
print(f"quarantine reconciliation ({TODAY}){'  [DRY RUN]' if DRY else ''}")
print(f"  rows in quarantine.csv: {len(quar)}")
for row, resolution, reason, now in resolved:
    print(f"  DROP  {row.get('key')}  [{resolution}]")
    print(f"        {reason}")
for row, why in kept:
    print(f"  KEEP  {row.get('key')}: {why}")

if not resolved:
    print("nothing to resolve — quarantine.csv unchanged")
    sys.exit(0)
if DRY:
    print(f"dry run: would drop {len(resolved)} row(s) and archive them to {RESOLVED}")
    sys.exit(0)

# ---------- archive, then rewrite ----------
n_arch = 0
for row, resolution, reason, now in resolved:
    n_arch += append_dedup(RESOLVED, RESOLVED_FIELDS,
        {**{f: row.get(f, "") for f in QUAR_FIELDS},
         "resolution": resolution, "resolution_reason": reason,
         "current_candidate": now, "resolved_by": "reconcile_quarantine.py",
         "resolved_date": TODAY},
        dedup_on=DEDUP_ON)
# Atomic (issue 431): quarantine.csv records quarantined series and why, and is not re-derivable.
write_csv_atomic(QUARANTINE, QUAR_FIELDS,
                 [{f: row.get(f, "") for f in QUAR_FIELDS} for row, _ in kept])
print(f"archived {n_arch} row(s) -> {RESOLVED} ({len(resolved) - n_arch} already recorded)")
print(f"quarantine.csv: {len(quar)} -> {len(kept)} row(s) open")
