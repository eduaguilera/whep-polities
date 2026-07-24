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
- `evidence_hash` = hash of the deterministic evidence for that unit (all its
  current findings/flags: types, row counts, year spans, sources — computed by
  `01_`/`02_` and stamped onto every finding/flag they emit). A banked
  `correct`/`fixed` unit is skipped **only while the ledger's hash matches the
  unit's current evidence**. If the underlying data changes (hash differs) —
  or the row was banked without a hash — the unit is automatically re-opened
  and resurfaces with a `reopened:` note.
- Banking rules: `correct` verdicts are banked **with** the unit's
  `evidence_hash` (the Cleanup phase copies it from the audited finding/flag);
  `fixed` rows are banked **without** one on purpose — the finding should be
  gone after the fix, and if it ever resurfaces the missing hash reopens it for
  one re-audit, which re-banks it with a fresh hash.
- `WHEP_LEDGER_BACKFILL=1` (env, both `01_` and `02_`): bootstrap mode — banked
  rows with an *empty* hash get the unit's current hash written into the ledger
  instead of reopening. Only for trusted states (rows banked right after their
  review, before hashing existed).

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

### FAOSTAT-era findings (origin `faostat`)

Stage 0 (`01_match_and_findings.py`, Stage 1b) also ingests the residual
queue of [`pipelines/faostat-era-matching`](../faostat-era-matching/README.md)
— the FAOSTAT (1961+) reporting universe matched by numeric area code — into
`findings.json`, tagged `sources: ["faostat"]`. These are audited and fixed by
the same loop, with two FAOSTAT-specific rules the workflow enforces:

- **Never fix a FAOSTAT finding with an `applied_aliases.csv` row.** That file's
  `source=faostat` rows are regenerated (replace-by-source) by
  `faostat-era-matching/match.R`, which routes by area code and ignores
  hand-added aliases. Fix instead with a **new polity** (wiki + CSV — `match.R`'s
  iso3-family lookup then routes the area) or a **`match.R` route**
  (`manual_prefix` for a different-prefix chain, `manual_span_routes` for
  overlapping periods, grounded in data magnitudes).
- **Integrate re-runs `match.R`** whenever a FAOSTAT-origin fix was applied, so
  the regenerated routing (and `findings.json` via Stage 1b) reflects it before
  Verify checks resolution. This needs the WHEP pins cache (`WHEP_REPO`); without
  it, FAOSTAT fixes stay open for the next run rather than being falsely banked.

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

- **(a) Source footnotes / explanatory notes** — a **corroborating hint, never authoritative.**
  Extracted footnotes can be OCR-garbled, matched to the wrong row, or mis-attributed, so
  they support or question a verdict but never decide it alone; always weigh them against the
  data. Wired in as `source_notes` (from `state/iia_territorial_notes.csv`, ISO-joined). The
  Nextcloud `Sources/datasets/textracted_footnotes/` tree (~1,642 dirs, currently unsynced)
  is a richer future input.
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

## Territory basis (stage 4) — the "assumed-constant border" sweep

`04_territory_basis.py` makes the vintage-drift concern systematic and
DB-wide, answering: *for the years a polity serves, does its polygon
faithfully represent that period's territory, or is it an assumption?* It
compares each polity's polygon vintage (`polygon_feature_year`) to its own
period `[start_year, end_year]` and emits a graded `territory_basis`:

| basis | meaning |
|-------|---------|
| `measured` | vintage falls inside the period and the span is short enough that one polygon is defensible. |
| `assumed_constant` | a single vintage held across a long span (≥25y) — borders may have changed within it. The bulk of historical data sits here. |
| `back_projected` | vintage is **outside** the period (a later/modern, or earlier, border applied to this period) — the clearest "not the real territory" case. Also any `modern_proxy`/`constructed_estimate` polygon. |
| `unassigned` | no polygon — an **honest gap**, never a false territory (policy: never back-project a modern border; `polygon_status=unassigned`). |

Output: `state/territory_basis.csv` (one row per polity). A polity is
`priority_review` when it is `assumed_constant`/`back_projected` **and**
independently flagged by stage 02 (magnitude step-change vs sibling period,
README-known mismatch, vintage drift, or aggregate-contains-concurrent-data)
— i.e. there is real evidence its single polygon misrepresents the territory,
as opposed to a long span whose border was genuinely stable. The
`priority_review` set is the input to the periodize/assign-vintage-polygon
remedy (split at border-change years, each period its own polygon).

The default window is **1860–1961** (`WIN_LO`/`WIN_HI`), the span where WHEP
back-projects modern country borders onto historical production/trade data.

---

## Running

```bash
# deterministic prep (no agents)
python pipelines/polity-autoimprove/01_match_and_findings.py     # match + review units, filtered by ledger
python pipelines/polity-autoimprove/02_territorial_evidence.py   # attach numeric territorial evidence
python pipelines/polity-autoimprove/04_territory_basis.py        # classify each polity's territory_basis (1860-1961 sweep)

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

## New-polity creation (dedicated workflow) + polygon provenance

New-polity creation is **split into its own workflow** (heavier than rematch:
research → wiki → polygon sourcing → DB row; mutates `polities_database.csv` and
writes files, so it uses worktree isolation + serial-integrate). The rematch/audit
loop stays fast and separate.

### Polygon source priority (try in order; never skip ahead without recording why)
1. **Exact historical polygon** — a GIS source with the *actual* territory for that
   entity+period. Check these before anything else:
   - CShapes 2.0 (states + colonial dependencies, 1886+)
   - **Cliopatria / Seshat** (1,618 polities, 3400 BCE–2024 — largely UNTAPPED)
   - CHGIS (China), Paine et al. (precolonial Africa), GHGIS (German historical regions)
   - the repo's existing `data/geodata/polities_polygons.gpkg`
2. **Composed** — union of constituent sub-units' historical polygons (e.g. AOF =
   union of its colonies; a trust territory = union of its islands).
3. **Period proxy** — copy an adjacent-period polygon of the *same* entity, only if
   the territory was essentially unchanged; document the difference.
4. **Modern proxy / constructed estimate** — LAST RESORT, only after confirming 1–3
   don't exist.

### Mandatory provenance (recorded on EVERY new polity — never silent)
- `polygon_source`: database + feature id + vintage year actually used.
- `polygon_method` ∈ {`exact_historical`, `composed_union`, `period_proxy`,
  `modern_proxy`, `constructed_estimate`}.
- `polygon_confidence` ∈ {high, medium, low}.
- Wiki `## Territorial extent`: state exactly what was used and why; for a
  proxy/estimate, give the direction + rough km² difference from the true territory
  and mark it **"ESTIMATE — not authoritative"**.

**Rule:** an estimate is acceptable *only* after confirming a real historical
polygon (steps 1–2) doesn't exist, and it must be flagged loudly so it is never
mistaken for ground truth. Prefer leaving `polygon_status=unassigned` with a
documented reason over a silent modern-borders guess.
