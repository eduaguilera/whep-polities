# polity-autoimprove

A **repeatable, agent-driven workflow** that incrementally improves the WHEP
polities database + wiki, run after run, converging toward the invariant:

> **every production/trade data point is matched to the correct polity, and that
> polity has the right territory (polygon) for the data's year.**

Each run reviews what is not yet resolved, files issues, fixes them wiki-first,
commits one fix per issue, and records state so the **next run starts clean and
skips everything already confirmed correct.** It is meant to be run on a schedule
or on demand until the issue queue is empty.

This pipeline **extends** [`pipelines/pre1961-matching`](../pre1961-matching/README.md)
(the deterministic matcher + confidence audit + the wiki-first "Creating new
polity entries" rules) to the full consolidated dataset and wraps it in an
audit → reconcile → fix → integrate → cleanup loop.

---

## Principles

1. **Wiki is the source of truth.** The database is derived from the wiki. Any
   change to a polity's identity/dates/extent is made in the wiki **first**, then
   propagated to `data/final/polities_database.csv`, then to a polygon.
2. **Aggregates are first-class.** Undivided Germany, the Japanese Empire, the
   full USSR are legitimate polygons and are **kept**. Territorial correctness is
   achieved by *matching each data point to the polity whose polygon fits that
   data's territory* — and creating a more-granular polity when the data is
   granular — **never by editing or shrinking an aggregate polygon.**
3. **Code detects, agents judge.** Deterministic detectors do the cheap,
   reproducible work and attach **numeric evidence**; agents are spent only on
   judgement (verdicts, reconciliation, fixes).
4. **Settle territory from data, not convention.** A territorial verdict must be
   grounded in the data's own magnitudes + spatial containment evidence (see
   `02_territorial_evidence`), not in a remembered labelling convention.
5. **Idempotent & resumable.** Resolved units are marked in the ledger and
   skipped. A run leaves the tree clean so the next run can start immediately.
6. **Auditable.** Every change traces to an issue id, its evidence, and a commit.

---

## State model — the review ledger

`state/review_ledger.csv` persists what has been reviewed, so re-runs skip
resolved work. Two kinds of review unit:

| unit | key | status values |
|---|---|---|
| **match** (a data label → polity assertion) | `source_label` + `polity_code` | `unreviewed` · `correct` · `issue` · `fixed` |
| **polity** (wiki/extent correctness) | `polity_code` | `unreviewed` · `correct` · `issue` · `fixed` |

Columns: `unit_kind, key, status, issue_id, evidence_hash, last_run, last_commit`.

- A run **only processes** `unreviewed` units and `issue` units whose fix is not
  yet verified. It **skips** `correct` and `fixed`.
- `evidence_hash` = hash of the deterministic evidence for that unit. If the
  underlying data changes (new source ingested, evidence_hash differs), the unit
  is automatically re-opened to `unreviewed` even if previously `correct`.

This is what implements your requirement: *"if a row was identified as correctly
matched, the agent should skip it next run"* — and it self-heals when inputs change.

---

## Pipeline stages

```
                          ┌── ledger (state/) ──┐  skip correct/fixed
                          ▼                      │
 0  MATCH + EVIDENCE   (code) ────────────────────────────────►  review units
      run matcher (pre1961-matching core, generalised);          + numeric evidence
      attach territorial evidence (magnitudes + spatial
      containment); filter out ledger-resolved units
                          │
 1  AUDIT             (agents, fan-out) ──────────►  per unit: verdict
      one agent per unreviewed unit. verdict = `correct`           → ledger=correct
      (numeric-evidence-grounded) OR emit an ISSUE REPORT (json).   → issues[]
                          │
 2  RECONCILE         (1 agent) ──────────────────►  harmonized_issues[]
      ingest all issue reports; dedupe/merge repeated &
      related issues; consolidate evidence; assign fix_type;
      order by dependency (polity fixes before re-matches).
                          │
 3  FIX               (agents, fan-out, worktree-isolated) ──►  change-sets[]
      ONE agent per harmonized issue. Applies the wiki-first
      methodology for its fix_type. Emits a structured CHANGE-SET
      (wiki edits + DB row + polygon decision) — does NOT commit.
                          │
 4  INTEGRATE         (serial integrator) ────────►  one commit per issue
      apply each change-set in dependency order; regenerate DB
      rows from wiki where needed; RE-RUN the matcher to verify
      the issue is resolved (regression); commit one issue at a time.
                          │
 5  CLEANUP           (code) ─────────────────────►  clean tree + report
      update ledger (issue→fixed, verified→correct); write
      run_report.md; ensure working tree is clean for next run.
```

### Why change-sets + a serial integrator (not parallel commits)

Fix agents run concurrently, but `polities_database.csv` is a **single shared
file** and git commits to one branch **cannot** be made in parallel without
clobbering. So fix agents work in isolated worktrees and **return** their changes;
the integrator applies them sequentially and makes **one commit per issue**. This
keeps your "one issue → one fix → one commit" intent while staying atomic and
conflict-free. Wiki pages are one-file-per-polity so they rarely conflict; the
CSV and `match.R`/`common_names` patches are the shared files the integrator owns.

---

## Issue report schema (stage 1 output)

```json
{
  "issue_id": "<stable hash of subject+type>",
  "type": "rematch_alias | polity_dates | polity_extent_polygon | missing_polity | double_count | data_error",
  "subject_polity": "<polity_code or null>",
  "subject_label":  "<source data label or null>",
  "period": "<years the issue concerns>",
  "description": "<what's wrong, one paragraph>",
  "evidence": { "magnitudes": [...], "contained_with_concurrent_data": [...], "sources": [...], "rows": N },
  "proposed_fix": "<the agent's suggested remedy>",
  "confidence": "high|medium|low"
}
```

## Harmonized issue (stage 2 output)

A deduplicated, self-contained unit of work: merges every issue report touching
the same subject, unions their evidence, picks the single correct `fix_type`,
and records `supersedes: [issue_id...]`. One harmonized issue → one fix agent →
one commit.

---

## Fix methodology by `fix_type` (all wiki-first where a polity changes)

| fix_type | what the fix agent does | touches |
|---|---|---|
| `rematch_alias` | data label routes to the wrong/none polity but the **right polity exists** → append an `alias_row` to **`state/applied_aliases.csv`** (the file `01_match_and_findings.py` actually reads). No entity change. Optionally also patch the legacy `pre1961-matching/match.R`. | `state/applied_aliases.csv` (+ optional `match.R`) |
| `polity_dates` | a polity's start/end is wrong for the data → **wiki first** (research + update the page's dates & rationale), then the CSV row, then predecessor/successor links. | `wiki/polities/<code>.md` → CSV |
| `polity_extent_polygon` | polygon is wrong-extent for the data it serves → **wiki first** (document the contemporaneous territory + km²), then choose/generate the polygon (CShapes/GADM/Cliopatria/Paine/CHGIS, union, or constructed). Aggregates are kept; route granular data to a granular polity instead. | `wiki/polities/<code>.md` → CSV + polygon |
| `missing_polity` | data has no covering polity → create the wiki page (per `pre1961-matching` "Wiki page requirements"), then CSV row, then polygon. | new `wiki/polities/<code>.md` → CSV + polygon |
| `double_count` | a parent polity's polygon contains sub-territories that report separately → **do not edit the aggregate**; re-route the granular data to the contained polities and document the aggregate's scope on its wiki page. | matching + wiki note |
| `data_error` | a value/unit looks wrong (not a territory issue) → flag in a report; **never silently edit source data.** | report only |

### The alias table: `(name, source, year-range) → polity`

`state/applied_aliases.csv` columns: `original_name, source, year_start, year_end,
common_name, target_polity_code, confidence, basis, rows`. A single label can route
to **different polities by year and/or source** — empty `source`/`year_*` = applies
to all. `01_match_and_findings.py` picks the most specific matching rule per data row
(year- and source-qualified rules beat blanket ones). Example: `Germany Western`
resolves to West Germany **only for 1949–1951**; its 1937–48 rows stay an open finding.

### What a source label actually means (avoid false precision)

A label like "Germany Western" is **the source's own reporting unit**, with the
source's (often stable, possibly idiosyncratic) territorial definition — it need
**not** correspond to our period splits (Reich / occupied / FRG). Forcing it onto
our boundaries can be *false precision*: the reporter may have meant one consistent
thing across all its years (e.g. some occupied+unoccupied conception), not our
1945/1949 entities. **Do not assume the label maps to our ontology.** Determine what
territory it actually covers by:

- **(a) Source footnotes / explanatory notes.** Not yet wired in, but the Nextcloud
  `Sources/datasets/textracted_footnotes/` tree (~1,642 extracted footnote dirs) is a
  concrete future input — read the source's own definition of the unit.
- **(b) Data-magnitude analysis.** Compare the label's reported staple magnitudes
  against candidate territories' expected figures to *infer* the extent (the method
  that settled "Japan = metropolitan, not empire"; see `02_territorial_evidence.py`).

Until a label's extent is established, prefer a **low-confidence / `assumed` basis**
alias (or leave it an open finding) over a confident mapping. When the source's unit
matches **no** existing WHEP polity, that is a signal to create a polity matching the
**source's** definition — not to shoehorn the data into a polity it doesn't fit.

**The fix agent must research** (web/sources) before changing a wiki page, and
the wiki page edit must satisfy the `## Territorial extent` requirements already
defined in [`pre1961-matching/README.md`](../pre1961-matching/README.md#wiki-page-requirements):
polygon status, why the entry exists / what data it captures, and a locatable
territory description with km².

---

## Territorial verdict rule (stage 1 & 3)

Audit the polygon of the polity **each data label is matched to** against *that
data's* territory, using the deterministic evidence from `02_territorial_evidence`:

- `staple_magnitudes` — the polity's own reported staple values (with units; FAO
  uses "1000 tonnes").
- `contained_with_concurrent_data` — WHEP polities whose polygon sits **inside**
  this one *and* report data in the same years (spatial containment over
  `data/geodata/polities_polygons.gpkg`). If non-empty, the polygon overstates the
  territory its own data covers — **unless** this polity's magnitudes are large
  enough to actually include the contained ones (compare the numbers).

Remedy is always **re-route or add a granular polity** — never edit an aggregate.

**Intra-span vintage drift (the Cape Colony case).** A polity record carries a
single polygon at one *vintage year*; that polygon represents only that year. A
long-lived polity whose borders changed within its span (e.g. `CAP-1800-1910`,
one polygon vintage 1886, but Cape Colony expanded through the 1800s) cannot be
represented by one polygon. `02_territorial_evidence.py` flags
`polygon_vintage_drift` when data is matched ≥15y from the polygon's vintage over
a ≥25y span. **An agent must never assume territorial stasis across the vintage.**
Remedy: split the polity at the border-change years (each period its own
polygon), or — if no period polygon is available — document the approximation on
the wiki page (direction + rough magnitude), per the `pre1961-matching`
"Note approximations" rule.

---

## Running

```bash
# deterministic prep (no agents)
python pipelines/polity-autoimprove/01_match_and_findings.py     # match + review units, filtered by ledger
python pipelines/polity-autoimprove/02_territorial_evidence.py   # attach numeric territorial evidence

# the agent loop (Workflow tool) — audit -> reconcile -> fix -> integrate -> cleanup
#   Workflow({ scriptPath: "pipelines/polity-autoimprove/autoimprove.workflow.js", args: {...} })
```

Workflow agents default to **Sonnet / medium effort** (large fan-out; cost; avoids
session limits). Re-run until the ledger has no `unreviewed`/open units.

### Cost control — two independent knobs (and why there's no waste)

The agents **never** audit the 190k data points — stages 01/02 resolve those
deterministically for free. Agents only see the **residual uncertain set**
(findings + territorial flags) that 01/02 could not settle, and the **ledger
removes anything already resolved** before the workflow runs. So:

- `max_audit` — caps how many residual units are **audited** this run (default =
  all remaining). The audit set **shrinks every run** because resolved units are
  ledger-skipped, so you never re-audit a unit that was already confirmed
  `correct`. For a cheap validation run, set `max_audit` small — it audits a
  slice **end-to-end** (audit→fix→commit→ledger), not "audit everything then
  discard".
- `max_issues` — caps how many issues are **fixed/committed** this run.

A run's cost ≈ `min(max_audit, remaining residual units)` audit agents +
`min(max_issues, issues found)` fix/integrate agents. Across runs the residual
set converges to empty.

---

## Invariants a run must leave true (so the next run is clean)

1. Working tree clean (every change committed; no stray files — see note below).
2. `review_ledger.csv` updated: audited→`correct`, fixed issues→`fixed`.
3. `run_report.md` written: units reviewed, issues filed/merged/fixed, coverage %.
4. The matcher re-run shows each fixed issue's data now matches correctly.

> **Housekeeping note:** agents must write only to their declared outputs. Stray
> files (e.g. wiki stubs left untracked outside an issue's commit) break the
> "clean tree" invariant. The integrator is the only stage that commits.

---

## Status / provenance

Methodology authored 2026-06-23. The deterministic detectors and the
resolve/territorial-audit workflows were prototyped under
`scratchpad/layerb_harness` and are being ported here. See the project's
data-source inventory and consolidated layer-B build for the input side.
