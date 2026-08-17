#!/usr/bin/env python3
"""Apply verified assertion verdicts (deterministic; the agents only DECIDED).

Reads state/verdicts_pending.json (written by verify_assertions.workflow.js)
plus state/assertions.json (for the evidence bundles), and applies each
non-quarantined verdict:

  confirm      -> ledger: correct + evidence_hash + protocol_version (assertion
                  is banked; skipped until its evidence OR the verification
                  protocol changes)
  reroute      -> year/source-scoped row appended to applied_aliases.csv
                  (NEVER for source=faostat — those routes live in match.R;
                  such verdicts are quarantined instead) + ledger: fixed
  not_a_polity -> state/ignored_labels.csv + ledger: correct + hash
  new_polity   -> state/new_polity_proposals.json (feed new_polity.workflow.js;
                  assertion stays open until the polity exists + re-intake)
  uncertain    -> quarantine
  quarantined  -> state/quarantine.csv for human adjudication + ledger: issue

Idempotent: re-running the same verdicts file changes nothing (alias/ignored
appends are deduped; ledger upserts by key).
"""
import json, csv, os, sys, datetime

H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POLDB = os.path.join(REPO, "data/final/polities_database.csv")
# optional arg: verdicts file (name under state/, or a path) — the verify
# workflow can write a distinct file per run so concurrent runs don't clobber
_v = sys.argv[1] if len(sys.argv) > 1 else "verdicts_pending.json"
VERDICTS = _v if os.path.sep in _v else os.path.join(H, _v)
ASSERTIONS = os.path.join(H, "assertions.json")
LEDGER = os.path.join(H, "review_ledger.csv")
ALIASES = os.path.join(H, "applied_aliases.csv")
IGNORED = os.path.join(H, "ignored_labels.csv")
QUARANTINE = os.path.join(H, "quarantine.csv")
PROPOSALS = os.path.join(H, "new_polity_proposals.json")
ARCHIVE = os.path.join(H, "verdicts_applied.jsonl")     # append-only decision log
WIKI_NOTES = os.path.join(H, "wiki_notes_queue.csv")    # research to fold into wiki pages
CONVENTIONS = os.path.join(H, "source_conventions.csv") # verified source reporting conventions
SUSPECT_PAGES = os.path.join(H, "suspect_wiki_pages.csv")  # pages verifiers judged to be wrong
TODAY = datetime.date.today().isoformat()
LEDGER_FIELDS = ["unit_kind", "key", "status", "issue_id", "evidence_hash",
                 "protocol_version", "last_run", "last_commit"]

# which RULES this verdict was judged under — read from the workflow file (the
# declaration site), never from an agent echo. A row banked below the current
# version is reopened by 00_intake.py, the same way a changed evidence_hash
# reopens one. See protocol.py.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from protocol import protocol_version
PROTOCOL = protocol_version()

verdicts = json.load(open(VERDICTS))
bundles = {a["key"]: a for a in json.load(open(ASSERTIONS))["assertions"]}
# matchable targets only: dead (retired/superseded) polities must never receive
# data, so a verdict routing to one is a contract violation, not a fix.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from matchlib import Matcher
_pol = list(csv.DictReader(open(POLDB)))
dead_codes = {r["polity_code"] for r in _pol if r.get("wiki_status") in Matcher.DEAD_STATUS}
valid_codes = {r["polity_code"] for r in _pol} - dead_codes
span_of = {r["polity_code"]: (int(r["start_year"]), int(r["end_year"]))
           for r in _pol if (r.get("start_year") or "").strip().isdigit()}

# ---------- ledger upsert helpers ----------
ledger = list(csv.DictReader(open(LEDGER))) if os.path.exists(LEDGER) else []
by_key = {(r.get("key") or "").strip().lower(): r for r in ledger}
CUR_PROTOCOL = PROTOCOL   # protocol of the verdict being applied (set per item)
def bank(key, status, evidence_hash="", protocol=None):
    protocol = CUR_PROTOCOL if protocol is None else protocol
    row = by_key.get(key.strip().lower())
    if row is None:
        row = {f: "" for f in LEDGER_FIELDS}
        row.update({"unit_kind": "match", "key": key})
        ledger.append(row); by_key[key.strip().lower()] = row
    row.update({"status": status, "evidence_hash": evidence_hash,
                "protocol_version": protocol, "last_run": TODAY})

def append_dedup(path, fields, row):
    rows = list(csv.DictReader(open(path))) if os.path.exists(path) else []
    # str() both sides: CSV re-reads are strings, fresh rows may carry ints
    if any(all(str(r.get(k) or "") == str(row.get(k) or "") for k in fields) for r in rows):
        return False
    new = not os.path.exists(path)
    with open(path, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        if new: w.writeheader()
        w.writerow(row)
    return True

# ---------- apply ----------
stats = {"confirm": 0, "reroute": 0, "split_reroute": 0, "not_a_polity": 0,
         "new_polity": 0, "uncertain": 0, "quarantined": 0, "skipped_no_bundle": 0,
         "skipped_stale": 0, "stale_protocol": 0,
         "downgraded_circular": 0, "page_suspect": 0}
proposals = json.load(open(PROPOSALS)) if os.path.exists(PROPOSALS) else []
prop_keys = {p["key"] for p in proposals}

for item in verdicts:
    v = item["verdict"]; key = v["key"]; b = bundles.get(key)
    # PROTOCOL: the verify workflow stamps the version it ran under into each
    # verdict (by script, not by agent echo). Bank THAT, not the current
    # constant — a verdict produced before a rule change must not be recorded as
    # if it had met the new rules; stamping its own version lets 00_intake.py
    # reopen it immediately instead of silently accepting stale work.
    # unstamped (a verdicts file written before the stamp existed) -> assume the
    # current version; an explicit older number is honoured, including 0
    _pv = str(v.get("protocol_version") if v.get("protocol_version") is not None else "").strip()
    CUR_PROTOCOL = int(_pv) if _pv.isdigit() else PROTOCOL
    if CUR_PROTOCOL < PROTOCOL:
        stats["stale_protocol"] += 1
        print(f"  OLD PROTOCOL: {key} was verified under v{CUR_PROTOCOL}, current is "
              f"v{PROTOCOL} — banked at v{CUR_PROTOCOL}, so intake will reopen it")
    if b is None:
        stats["skipped_no_bundle"] += 1
        print(f"  WARN: no evidence bundle for {key} (stale verdicts file?) — skipped")
        continue
    # STALE GUARD: the verdict pins the evidence_hash it judged. If routing has
    # changed since (a matcher fix, a new polity, re-ingested data), the verdict
    # is about a candidate the agent never saw — refuse it and re-verify.
    vh = (v.get("verified_evidence_hash") or "").strip()
    if vh and vh != b["evidence_hash"]:
        stats["skipped_stale"] += 1
        print(f"  STALE: {key} was verified against evidence {vh} but the bundle is now "
              f"{b['evidence_hash']} (candidate {b['candidate']}) — re-verify, not applied")
        continue
    reviewer = (item.get("review") or {})
    quarantined = bool(item.get("quarantined")) or v["verdict"] == "uncertain"

    # ---- ANTI-CIRCULARITY: a verdict resting only on an unreviewed ('draft')
    #      wiki page is an earlier agent's hypothesis confirming itself. It may
    #      still be the best routing available, but it must not be RECORDED as
    #      territorially verified, so verified_equal is downgraded to
    #      best_available (which reopens whenever the family changes). ----
    ev_used = set(v.get("evidence_used") or [])
    corroborating = ev_used - {"wiki_draft"}
    if v["verdict"] == "confirm" and v.get("confirm_kind") == "verified_equal" \
            and ev_used and not corroborating:
        v["confirm_kind"] = "best_available"
        v["basis"] = (v.get("basis") or "") + \
            " [downgraded by apply_verdicts: evidence_used was wiki_draft only — " \
            "an unreviewed page cannot establish verified_equal]"
        stats["downgraded_circular"] += 1

    # ---- execution-contract validation (the agent DECIDES; code verifies the
    #      decision is executable — never trusts an unchecked ID) ----
    pc = (v.get("polity_code") or "").strip()
    if v["verdict"] == "confirm" and pc and pc != b["candidate"]:
        quarantined = True
        reviewer = {**reviewer, "reason": (reviewer.get("reason") or "") +
                    f" [contract: confirm echoed {pc} but candidate is {b['candidate']}]"}
    if v["verdict"] == "reroute":
        oy0, oy1 = (int(x) for x in b["years_observed"].split("-"))
        ts, te = span_of.get(pc, (None, None))
        if pc not in valid_codes:
            quarantined = True
            why = "is retired/superseded — data must never route there" \
                if pc in dead_codes else "not in polities DB"
            reviewer = {**reviewer, "reason": (reviewer.get("reason") or "") +
                        f" [contract: reroute target {pc or '(empty)'} {why}]"}
        elif pc == b["candidate"]:
            quarantined = True
            reviewer = {**reviewer, "reason": (reviewer.get("reason") or "") +
                        " [contract: reroute target equals the candidate — should be confirm]"}
        elif ts is not None and not (ts <= oy0 and oy1 <= te):
            # the target must cover the WHOLE observed span; partial cover means
            # the right answer is split_reroute (tile it) or new_polity (gap)
            quarantined = True
            reviewer = {**reviewer, "reason": (reviewer.get("reason") or "") +
                        f" [contract: reroute target {pc} spans {ts}-{te} but the data "
                        f"spans {oy0}-{oy1} — use split_reroute or new_polity]"}
    if v["verdict"] == "split_reroute":
        segs = v.get("split_segments") or []
        y0, y1 = (int(x) for x in b["years_observed"].split("-"))
        bad = None
        if len(segs) < 2:
            bad = "needs >=2 segments (one segment is a plain reroute/confirm)"
        elif any(s["polity_code"] not in valid_codes for s in segs):
            bad = "segment target(s) not in polities DB: " + \
                  ",".join(s["polity_code"] for s in segs if s["polity_code"] not in valid_codes)
        else:
            segs = sorted(segs, key=lambda s: s["year_start"])
            if segs[0]["year_start"] != y0 or segs[-1]["year_end"] != y1:
                bad = f"segments must tile the observed span {y0}-{y1}"
            elif any(s["year_start"] > s["year_end"] for s in segs):
                bad = "segment with year_start > year_end"
            elif any(segs[i + 1]["year_start"] != segs[i]["year_end"] + 1 for i in range(len(segs) - 1)):
                bad = "segments must be contiguous and non-overlapping"
        if bad:
            quarantined = True
            reviewer = {**reviewer, "reason": (reviewer.get("reason") or "") +
                        f" [contract: split_reroute {bad}]"}
    # faostat reroutes cannot be alias rows (replace-by-source would wipe them):
    # they need a match.R route -> send to quarantine with the pointer.
    if v["verdict"] == "reroute" and b["source"] == "faostat":
        quarantined = True
        reviewer = {**reviewer, "reason": (reviewer.get("reason") or "") +
                    " [faostat reroute must be a match.R route, not an alias row]"}

    if quarantined:
        # record BOTH positions: the second (blind) verifier's counter-verdict is
        # often the better answer, and adjudication needs it side by side
        rp = reviewer.get("new_polity_proposal") or {}
        append_dedup(QUARANTINE,
            ["key", "candidate", "verdict", "polity_code", "confidence", "basis",
             "review_verdict", "review_polity_code", "review_basis", "review_proposal",
             "review_reason", "date"],
            {"key": key, "candidate": b["candidate"], "verdict": v["verdict"],
             "polity_code": v.get("polity_code") or "", "confidence": v["confidence"],
             "basis": v["basis"],
             "review_verdict": reviewer.get("verdict") or "",
             "review_polity_code": reviewer.get("polity_code") or "",
             "review_basis": reviewer.get("basis") or "",
             "review_proposal": json.dumps(rp) if rp else "",
             "review_reason": reviewer.get("reason") or "",
             "date": TODAY})
        bank(key, "issue")
        stats["quarantined" if item.get("quarantined") else "uncertain"] += 1
        continue

    if v["verdict"] == "confirm":
        bank(key, "correct", b["evidence_hash"])
        stats["confirm"] += 1
    elif v["verdict"] == "reroute":
        y0, y1 = b["years_observed"].split("-")
        append_dedup(ALIASES,
            ["source_label", "source", "year_start", "year_end", "common_name",
             "polity_code", "confidence", "basis", "observed_rows"],
            {"source_label": b["label_raw"], "source": b["source"],
             "year_start": y0, "year_end": y1, "common_name": b["label_raw"].lower(),
             "polity_code": v["polity_code"], "confidence": v["confidence"],
             "basis": f"assertion-verification: {v['basis'][:300]}",
             "observed_rows": b["rows"]})
        bank(key, "fixed")   # no hash: next intake re-derives the assertion under
        stats["reroute"] += 1  # the new candidate and it verifies/banks fresh
    elif v["verdict"] == "split_reroute":
        # one year/source-scoped alias row per segment; year-scoped rules beat
        # blanket ones in matchlib, so re-intake re-derives one assertion per
        # segment, each verifying/banking independently
        for s in sorted(v["split_segments"], key=lambda s: s["year_start"]):
            append_dedup(ALIASES,
                ["source_label", "source", "year_start", "year_end", "common_name",
                 "polity_code", "confidence", "basis", "observed_rows"],
                {"source_label": b["label_raw"], "source": b["source"],
                 "year_start": s["year_start"], "year_end": s["year_end"],
                 "common_name": b["label_raw"].lower(),
                 "polity_code": s["polity_code"], "confidence": v["confidence"],
                 "basis": f"assertion-verification (split_reroute): {v['basis'][:280]}",
                 "observed_rows": ""})
        bank(key, "fixed")
        stats["split_reroute"] += 1
    elif v["verdict"] == "not_a_polity":
        append_dedup(IGNORED,
            ["label", "source", "reason", "decided_by", "date"],
            {"label": b["label_raw"], "source": b["source"],
             "reason": v["basis"][:300], "decided_by": "verify-assertions+review",
             "date": TODAY})
        bank(key, "correct", b["evidence_hash"])
        stats["not_a_polity"] += 1
    elif v["verdict"] == "new_polity":
        if key not in prop_keys:
            proposals.append({"key": key, "bundle": b, "proposal": v.get("new_polity_proposal"),
                              "basis": v["basis"], "confidence": v["confidence"], "date": TODAY})
            prop_keys.add(key)
        bank(key, "issue")   # stays open until the polity exists + re-intake
        stats["new_polity"] += 1

# ---------- write ----------
with open(LEDGER, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=LEDGER_FIELDS)
    w.writeheader(); w.writerows(ledger)
if proposals:
    json.dump(proposals, open(PROPOSALS, "w"), indent=1)

# archive every applied verdict (append-only; full basis + review survive here,
# the ledger only holds the outcome) and queue wiki-worthy research
# dedup on (key, basis) so re-running the same verdicts file is a no-op, but a
# later RE-verification of a reopened assertion still archives its new verdict
archived = set()
if os.path.exists(ARCHIVE):
    for l in open(ARCHIVE):
        j = json.loads(l)["verdict"]; archived.add((j["key"], j.get("basis") or ""))
with open(ARCHIVE, "a") as fh:
    for item in verdicts:
        j = item["verdict"]
        if (j["key"], j.get("basis") or "") in archived: continue
        fh.write(json.dumps({"applied": TODAY, **item}) + "\n")
n_notes = 0
for item in verdicts:
    v = item["verdict"]; b = bundles.get(v["key"])
    note = (v.get("wiki_note") or "").strip()
    if note and b:
        n_notes += append_dedup(WIKI_NOTES,
            ["polity_code", "assertion_key", "note", "date"],
            {"polity_code": b["candidate"], "assertion_key": v["key"],
             "note": note, "date": TODAY})
if n_notes:
    print(f"wiki notes queued: {n_notes} -> {WIKI_NOTES} (fold into wiki pages, then clear)")

# pages the verifiers judged to contain errors of their own — a finding about the
# DATABASE, tracked separately from routing verdicts so wiki repair can be driven
n_sus = 0
for item in verdicts:
    v = item["verdict"]; b = bundles.get(v["key"])
    if not (b and (v.get("page_suspect") or v.get("page_inadequate"))): continue
    n_sus += append_dedup(SUSPECT_PAGES,
        ["polity_code", "wiki_status", "finding", "assertion_key", "what_looks_wrong",
         "evidence_used", "date"],
        {"polity_code": b["candidate"],
         "finding": "wrong" if v.get("page_suspect") else "inadequate",
         "wiki_status": (b.get("candidate_meta") or {}).get("wiki_status") or "",
         "assertion_key": v["key"],
         "what_looks_wrong": (v.get("wiki_note") or v.get("basis") or "")[:500],
         "evidence_used": ",".join(v.get("evidence_used") or []),
         "date": TODAY})
if n_sus:
    print(f"WIKI PAGE findings (wrong/inadequate): {n_sus} -> {SUSPECT_PAGES}")

# newly established SOURCE conventions -> the registry 00_intake.py attaches to
# future bundles. Only from verdicts that survived review (a convention
# generalizes beyond its assertion, so a disputed one must not propagate).
#
# The field list must be the registry's FULL column set (issue 24). It used to be the
# seven columns this step knows how to fill, which appended a SHORT row: `flow_type`
# then read back as empty, and write_source_flow_flags.py reads an empty flow_type as
# `production` — so a convention recording a transit flow would have published no flag
# at all, which is exactly the double count that file exists to expose. The columns this
# step cannot decide are written EMPTY on purpose, and validate_source_conventions.py
# fails on them until a human fills them in: a convention arriving from one verifier,
# with nothing re-measuring it, is below the bar for a premise every later verifier
# inherits, and should block rather than accumulate.
CONV_FIELDS = ["source", "label_pattern", "item_pattern", "convention", "evidence",
               "verified", "verified_by", "flow_type", "origin_iso3",
               "corroboration", "retested", "retest"]
n_conv = 0
for item in verdicts:
    if item.get("quarantined"): continue
    v = item["verdict"]; b = bundles.get(v["key"]); sc = v.get("source_convention") or {}
    if not (b and (sc.get("convention") or "").strip()): continue
    n_conv += append_dedup(CONVENTIONS, CONV_FIELDS,
        {"source": b["source"], "label_pattern": sc.get("label_pattern") or "*",
         "item_pattern": sc.get("item_pattern") or "*", "convention": sc["convention"],
         "evidence": sc.get("evidence") or "", "verified": TODAY,
         "verified_by": f"assertion-verification ({v['key']})",
         "flow_type": sc.get("flow_type") or "production",
         "origin_iso3": sc.get("origin_iso3") or "",
         # left for a human: one verifier is one corroborator, and nothing has
         # re-measured this yet.
         "corroboration": sc.get("corroboration") or "",
         "retested": "", "retest": ""})
if n_conv:
    print(f"source conventions learned: {n_conv} -> {CONVENTIONS} (attached to future bundles)")
    print(f"  ACTION REQUIRED: each new entry needs a second independent corroborator, a "
          f"check in 11_retest_conventions.py and a `retested` date before "
          f"scripts/validate_source_conventions.py will pass.")
print(f"applied {len(verdicts)} verdicts: " +
      ", ".join(f"{k}={n}" for k, n in stats.items() if n))
print(f"ledger: {len(ledger)} rows (banked at protocol v{PROTOCOL}); "
      "quarantine/proposals updated where applicable")
