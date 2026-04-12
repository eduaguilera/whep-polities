# Autonomous-next prompt

Use this when running the wiki in self-paced autonomous mode via the
`/loop` skill. This prompt tells the agent how to **pick its own next
task** from the wiki's current state, execute it, commit, and decide
whether to continue or stop.

This prompt is paired with the other workflow prompts
(`ingest.md`, `query.md`, `lint.md`) — autonomous-next does not replace
them, it *chooses* among them and then delegates.

---

You are maintaining the WHEP polities wiki in autonomous mode. Read
`wiki/README.md` first for the schema, rules, the **coverage goal**
(complete spatiotemporal coverage — every km², every year, no gaps),
and the **dual-renderer rule** (GitHub + Obsidian). Key link rules:
no `<a id>` HTML anchors, no `../` directory prefixes in links
(use filename-only paths), no reference-style link definitions
(use inline `[text](file.md#anchor)` only), heading text = target
slug. Then execute the four-phase cycle below. Each iteration is ONE cycle and produces
exactly ONE git commit (or ends without a commit if the stop
conditions fire).

## Phase 1 — State inventory

Walk the wiki and collect the current state. Do not skim — cheap
tool calls now prevent bad decisions later. Record at least:

1. **Polity pages:** for each file in `wiki/polities/*.md` (exclude
   `_template.md` and `_aggregates/*`): `polity_code`, `status`
   (draft / reviewed / contested), `sources:`, count of open
   questions, count of dangling polity refs in the bottom reference
   block (marked `<!-- TODO: page not yet created -->`).
2. **Open questions:** grep every polity page for `### oq-`. For each,
   note which page it lives on, whether it has a "Resolved" or
   "Partially resolved" marker, and — critically — which of the
   categories below it falls into. You must read the question body,
   not just the slug.
3. **Source files:** `wiki/sources/*.md` (exclude `_template.md`).
   For each, note the `§`-sections defined and the polity pages
   currently citing it (search for `[<source-slug>` references).
4. **Log entries:** the last ~10 entries in `wiki/log.md`, grouped by
   `kind`. Flag any `proposal`-kind entries: these are changes the
   wiki has proposed to the CSV or the R pipeline that a human has
   not applied yet. They are a drift signal if they accumulate.
5. **CSV ↔ wiki parity snapshot:** `wc -l data/final/polities_database.csv`
   minus 1 for the header. Compare against the polity-page count and
   the `Polities in CSV` line in `wiki/index.md`. Does
   `wiki/index.md` match reality? If not, note for phase 2.
6. **PDFs on disk:** `ls wiki/sources/pdfs/` vs the `pdf_local:`
   frontmatter fields in existing source files. Unused PDFs are an
   opportunity; source files pointing at missing PDFs are a
   provenance gap.
7. **Dangling polity refs:** grep for
   `<!-- TODO: page not yet created -->` across polity pages. These
   are concrete candidates for new polity pages.
8. **CSV oddities** (critical-stance audit, see `wiki/README.md`).
   Scan the CSV for row labels that contradict their time range,
   overlapping rows, orphan rows, missing-entity-row gaps, and
   `notes = NA` on rows whose siblings have content. Do not
   rationalize findings. Each finding is either (a) already
   documented in `docs/` or `wiki/log.md` with a rationale and you
   cite that, or (b) undocumented and becomes a `proposal`-kind
   entry for human review. The Russian Empire / USSR labeling
   issue in `F228-1905-1914` is a canonical example of the kind
   of thing this step catches.

Write the inventory to your own working memory, not to a file. It's
an input to phase 2, not a deliverable.

## Phase 2 — Classify every open question

For each open question collected in phase 1, assign exactly one of
these **tiers**. The tier plus a tiebreaker rule determines the
priority order in phase 3.

### Tier 1 — Easy wins (highest priority)

Questions where resolution takes one action and one source that is
already on disk or reachable without user intervention.

Examples of what qualifies:

- A question that a source **already ingested** has a section
  addressing. (The Biger Ottoman batch is the canonical example:
  Biger was already on disk after the Luxembourg ingest; applying
  it to Tunisia took one read of p.28 and one polity-page edit.)
- A question that a **single CLI command** can answer: `ogrinfo`
  SQL queries on `cshapes2_full.gpkg`, `grep` on a CSV column,
  `awk` on a COW statelist, etc.
- A question the `lint` prompt would handle (typos, broken internal
  references, stale counters in `wiki/index.md`).
- A question whose resolution text has *already been written* into
  a commit message, log entry, or source file and just needs to be
  pulled into the polity page's *Sourced claims* or *Open questions*
  resolution marker.
- **A CSV oddity that a single `proposal`-kind log entry can
  document.** The Russian Empire / USSR labeling issue, the
  `TUR-1800-1912` duplication, the missing Prussia row, the
  DEU/GER overlap — each of these should become a proposal entry
  the moment it's discovered in a phase 1 inventory. These are
  never "decisions to surface"; they are candidate bugs to
  document. Do not attempt to fix the CSV itself.

### Tier 2 — Source expansion

Questions where a source that has been ingested for one polity has
content applicable to another polity. These are the "fixed cost
already paid" ingests — opening the PDF is free the second time.

- A polity page at `status: draft` whose blocker is
  `oq-academic-corroboration` (or equivalent) and where a source
  already in `wiki/sources/` covers that polity.
- A new CLI or scraped claim from the source that can resolve
  multiple open questions at once.

### Tier 3 — New polity page creation

Questions or structural gaps that resolve by creating a new polity
page from `_template.md`.

- A CSV row with no wiki page whose polity code is referenced by
  multiple existing pages as predecessor / successor / contradiction
  subject. Count how many existing pages cite it — that is the
  tiebreaker.
- A dangling `[slug]` reference with a `<!-- TODO: page not yet
  created -->` marker and at least one citing page.

### Tier 4 — Deep work

Large structural changes that take multiple iterations to complete.

- An ingest of a large new source file with multiple relevant
  sections across many polities (e.g. a historical atlas volume).
- Auditing an entire chain of related polities (e.g. the TUR chain
  1913 → 1920 as a single batch).
- A new `decision`-kind log entry drafted from repeated signals
  across multiple polity pages.

### Tier X — Cannot be done autonomously

Questions that must not be picked up by autonomous mode. If the
next-highest-priority question is in Tier X, **skip it** and move on
to the next one (logging the skip in the iteration report).

- Questions tagged as `decision`-kind in their own text or whose
  resolution requires a repo-rule choice only a human can make
  (examples in the current wiki: `oq-1886-split-is-polygon-not-territory`
  on `ott-1800-1886`; `oq-1912-1920-gap` and the "grace period" part
  of `oq-libya-mid-row-change` on `ott-1908-1912`).
- Questions whose resolution requires a closed-access source the
  agent cannot download (paywalled PDFs without institutional auth;
  archival material).
- Questions that require editing `data/final/polities_database.csv`
  (e.g. the `TUR-1800-1912` duplication proposal).
- Questions that require editing `R/` pipeline code when the user
  has previously indicated the R environment is not in a known-good
  state.
- Anything that touches `renv.lock`, `.gitignore`, or
  `wiki/README.md`.

## Phase 3 — Pick ONE task

Select the next task using this algorithm:

1. Walk tiers in order: Tier 1, then Tier 2, then Tier 3, then Tier 4.
2. Within a tier, break ties by:
   - Number of polity pages affected (more = higher priority).
   - Recency of the blocking source (more recently added = higher —
     the goal is to extract full value from fresh ingests before
     they get buried).
   - Proximity to a status change (a page already at "one question
     away from reviewed" outranks a page with five open questions).
3. If the selected task falls in Tier X, mark it as skipped, remove
   it from consideration, and re-run step 1.
4. If no tasks remain in Tiers 1–4 after Tier X skips, **stop the
   loop** — see phase 4 stop conditions.

Record the choice: which task, which tier, which tiebreakers fired.
This goes in the iteration report.

## Phase 4 — Execute, commit, decide whether to continue

### Execute

Delegate to the matching existing prompt rather than inventing a new
workflow:

- Source expansion or new-source ingest → `wiki/prompts/ingest.md`.
- Lint-level fixes (typos, broken refs, stale index counters,
  missing log entries for recently-touched pages) → `wiki/prompts/lint.md`
  (using its relaxed allowed-edits rules).
- A question-driven research action (running an `ogrinfo` query,
  extracting a specific fact from an existing source file) →
  `wiki/prompts/query.md` with "file discoveries back" enabled so
  the answer lands on the polity page.
- Creating a new polity page → `wiki/polities/_template.md` plus a
  normal ingest flow.

Never take actions outside the allowed list. Never run destructive
operations. Never `git push`. If any execution step would require a
forbidden action, abort the iteration, mark the task as "unable to
complete autonomously", and continue the loop with the next task.

### Commit

Every iteration that changes files produces **exactly one commit**,
with a message of the form:

```
Autonomous iteration N: <one-line task summary>

<2-5 sentences on what was done>

<Open questions resolved / partially resolved / unchanged>

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
```

Iterations that make no file changes (pure lookup or a Tier X skip)
do not commit but still produce an iteration report line in
`wiki/log.md` of `kind: autonomous-skip` so the audit trail is
complete.

### Decide whether to continue

After the commit, evaluate the stop conditions below in order. If
any fires, stop and emit a final summary. Otherwise, schedule the
next iteration and return to phase 1.

## Hard stop conditions

Non-negotiable. If any of these hold after an iteration, stop:

1. **Priority exhausted.** Every remaining open question is in
   Tier X (decision-kind / missing source / CSV edit / R-pipeline /
   closed-access). The wiki has nothing left the loop can do
   without user input.
2. **Iteration cap.** The loop has run for `max_iterations` cycles
   (default: **3** on first run, higher only after a human has
   reviewed the loop's behavior and explicitly raised the cap).
3. **Proposal accumulation.** The number of `proposal`-kind log
   entries without a follow-up `decision` / `ingest` / `lint`
   response grows by 2 or more in a single loop. This means the
   wiki is generating work the user hasn't had a chance to review,
   and the loop should pause for them to catch up.
4. **Repeated failure on the same task.** A task was attempted,
   failed, was re-chosen in a later iteration, and failed again.
   Something structural is wrong; stop and surface it.
5. **Contradiction surfaced.** A new `contradiction`-kind issue
   was discovered that wasn't present in the phase-1 inventory. A
   contradiction is by construction something two sources disagree
   about, which means the agent should stop and report rather than
   pick a side.
6. **Commit failure.** A commit attempt fails (pre-commit hook,
   merge conflict, etc.). Do not retry with workarounds; stop.

## Soft priorities (tiebreakers, not stops)

Use these to prefer one action over another when multiple are
available:

- **Status progression.** Moving a polity page from `draft` to
  `reviewed` is worth more than adding a tenth open question to an
  already-draft page.
- **Coverage breadth.** Adding the first polity page in an empty
  continent outranks adding the eleventh European page.
- **Coverage chain completeness.** Creating a page that closes a
  predecessor/successor gap (a dangling `<!-- TODO: page not yet
  created -->` ref) outranks creating a page that stands alone.
  The wiki's coverage goal requires complete chains — when one
  polity ends, its successor must exist and account for the
  territory.
- **Source efficiency.** Actions that apply one source read to
  multiple polities outrank actions that apply one source read to
  one polity.
- **Log hygiene.** Appending to `wiki/log.md` with an entry that
  cross-references several pages is a small positive tiebreaker —
  it keeps the decision trail current.

## Iteration report format

At the end of each iteration, append one H2 entry to `wiki/log.md`
with kind `autonomous`:

```markdown
## autonomous-<N>-<short-slug>
**Date:** YYYY-MM-DD
**Touched:** <polity codes or "none">
**Source:** <source slug or "none">
**Kind:** autonomous

**Phase 1 (inventory):** <1–2 sentences on the state>

**Phase 2 (classification):** <how many open questions in each
tier, how many Tier X skipped>

**Phase 3 (selection):** <which task was chosen, which tier, why>

**Phase 4 (execution):** <what was done, which existing prompt was
delegated to>

**Outcome:** <open questions resolved / partially resolved; status
changes; new open questions created>

**Stop decision:** <continue / stop + which stop condition fired>
```

## Never-autonomously list (hard guardrails, not tiebreakers)

The following are never done autonomously, no matter how the
priority ranking ends up. This list overrides phase 3.

- No edits to `data/final/polities_database.csv`. Changes to the CSV
  are `proposal`-kind log entries only.
- No `decision`-kind log entries that establish a repo-wide rule.
  The agent may *draft* a decision and surface it in the iteration
  report, but the entry must be added by a human with the
  `kind: decision` header.
- No `git push`, no `git reset --hard`, no force-push, no branch
  deletion, no `git rebase -i`, no `--no-verify`.
- No edits to `renv.lock`, `.gitignore`, `wiki/README.md`, or any
  file in `wiki/prompts/`. The schema and prompts are human-owned.
- No acquisition of closed-access sources (paywalled papers,
  institutional PDFs). Report the gap; the user decides whether to
  download.
- No moving a polity page from `status: draft` to `status: reviewed`
  unless the schema requirements are met: at least one academic or
  reference-work source beyond Wikipedia, zero unresolved
  `Contradictions` section items, every *Sourced claims* bullet
  cited.
- No deleting polity pages, source files, or log entries. Resolved
  open questions are marked resolved in place with a pointer to the
  resolving log entry — they are never deleted.
- No rewriting history. Each iteration adds a fresh commit.

## Final summary (only when the loop stops)

When a hard stop fires, emit a final summary to the user containing:

1. How many iterations ran.
2. How many commits were created and their short SHAs.
3. A count of open questions resolved / partially resolved / added.
4. The list of Tier X questions that were skipped, with the reason
   each was skipped — this is the user's worklist.
5. The stop condition that fired and a one-sentence explanation.
6. Recommended next action (which is usually "human, please resolve
   these N Tier X items and then raise the iteration cap").

This summary is the handoff back to the user. It replaces the usual
end-of-turn prose with something compact and actionable.
