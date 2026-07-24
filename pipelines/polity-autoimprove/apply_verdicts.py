#!/usr/bin/env python3
"""Apply verified assertion verdicts (deterministic; the agents only DECIDED).

Reads state/verdicts_pending.json (written by verify_assertions.workflow.js)
plus state/assertions.json (for the evidence bundles), and applies each
non-quarantined verdict:

  confirm      -> ledger: correct + evidence_hash (assertion is banked; skipped
                  until its evidence changes)
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
VERDICTS = os.path.join(H, "verdicts_pending.json")
ASSERTIONS = os.path.join(H, "assertions.json")
LEDGER = os.path.join(H, "review_ledger.csv")
ALIASES = os.path.join(H, "applied_aliases.csv")
IGNORED = os.path.join(H, "ignored_labels.csv")
QUARANTINE = os.path.join(H, "quarantine.csv")
PROPOSALS = os.path.join(H, "new_polity_proposals.json")
ARCHIVE = os.path.join(H, "verdicts_applied.jsonl")     # append-only decision log
WIKI_NOTES = os.path.join(H, "wiki_notes_queue.csv")    # research to fold into wiki pages
TODAY = datetime.date.today().isoformat()
LEDGER_FIELDS = ["unit_kind", "key", "status", "issue_id", "evidence_hash", "last_run", "last_commit"]

verdicts = json.load(open(VERDICTS))
bundles = {a["key"]: a for a in json.load(open(ASSERTIONS))["assertions"]}
valid_codes = {r["polity_code"] for r in csv.DictReader(open(POLDB))}

# ---------- ledger upsert helpers ----------
ledger = list(csv.DictReader(open(LEDGER))) if os.path.exists(LEDGER) else []
by_key = {(r.get("key") or "").strip().lower(): r for r in ledger}
def bank(key, status, evidence_hash=""):
    row = by_key.get(key.strip().lower())
    if row is None:
        row = {f: "" for f in LEDGER_FIELDS}
        row.update({"unit_kind": "match", "key": key})
        ledger.append(row); by_key[key.strip().lower()] = row
    row.update({"status": status, "evidence_hash": evidence_hash, "last_run": TODAY})

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
         "new_polity": 0, "uncertain": 0, "quarantined": 0, "skipped_no_bundle": 0}
proposals = json.load(open(PROPOSALS)) if os.path.exists(PROPOSALS) else []
prop_keys = {p["key"] for p in proposals}

for item in verdicts:
    v = item["verdict"]; key = v["key"]; b = bundles.get(key)
    if b is None:
        stats["skipped_no_bundle"] += 1
        print(f"  WARN: no evidence bundle for {key} (stale verdicts file?) — skipped")
        continue
    reviewer = (item.get("review") or {})
    quarantined = bool(item.get("quarantined")) or v["verdict"] == "uncertain"

    # ---- execution-contract validation (the agent DECIDES; code verifies the
    #      decision is executable — never trusts an unchecked ID) ----
    pc = (v.get("polity_code") or "").strip()
    if v["verdict"] == "confirm" and pc and pc != b["candidate"]:
        quarantined = True
        reviewer = {**reviewer, "reason": (reviewer.get("reason") or "") +
                    f" [contract: confirm echoed {pc} but candidate is {b['candidate']}]"}
    if v["verdict"] == "reroute":
        if pc not in valid_codes:
            quarantined = True
            reviewer = {**reviewer, "reason": (reviewer.get("reason") or "") +
                        f" [contract: reroute target {pc or '(empty)'} not in polities DB]"}
        elif pc == b["candidate"]:
            quarantined = True
            reviewer = {**reviewer, "reason": (reviewer.get("reason") or "") +
                        " [contract: reroute target equals the candidate — should be confirm]"}
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
        append_dedup(QUARANTINE,
            ["key", "candidate", "verdict", "polity_code", "confidence", "basis",
             "review_reason", "date"],
            {"key": key, "candidate": b["candidate"], "verdict": v["verdict"],
             "polity_code": v.get("polity_code") or "", "confidence": v["confidence"],
             "basis": v["basis"], "review_reason": reviewer.get("reason") or "",
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
            ["original_name", "source", "year_start", "year_end", "common_name",
             "target_polity_code", "confidence", "basis", "rows"],
            {"original_name": b["label_raw"], "source": b["source"],
             "year_start": y0, "year_end": y1, "common_name": b["label_raw"].lower(),
             "target_polity_code": v["polity_code"], "confidence": v["confidence"],
             "basis": f"assertion-verification: {v['basis'][:300]}",
             "rows": b["rows"]})
        bank(key, "fixed")   # no hash: next intake re-derives the assertion under
        stats["reroute"] += 1  # the new candidate and it verifies/banks fresh
    elif v["verdict"] == "split_reroute":
        # one year/source-scoped alias row per segment; year-scoped rules beat
        # blanket ones in matchlib, so re-intake re-derives one assertion per
        # segment, each verifying/banking independently
        for s in sorted(v["split_segments"], key=lambda s: s["year_start"]):
            append_dedup(ALIASES,
                ["original_name", "source", "year_start", "year_end", "common_name",
                 "target_polity_code", "confidence", "basis", "rows"],
                {"original_name": b["label_raw"], "source": b["source"],
                 "year_start": s["year_start"], "year_end": s["year_end"],
                 "common_name": b["label_raw"].lower(),
                 "target_polity_code": s["polity_code"], "confidence": v["confidence"],
                 "basis": f"assertion-verification (split_reroute): {v['basis'][:280]}",
                 "rows": ""})
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
print(f"applied {len(verdicts)} verdicts: " +
      ", ".join(f"{k}={n}" for k, n in stats.items() if n))
print(f"ledger: {len(ledger)} rows; quarantine/proposals updated where applicable")
