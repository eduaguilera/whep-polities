# WHEP Polities Wiki

A persistent, compounding knowledge base that backs the judgment calls in
`data/final/polities_database.csv`. Curated by humans, maintained by an LLM
agent against the rules in this file.

This wiki is **not** methodology documentation — that lives in `docs/`. It is
the evidence and reasoning trail behind individual polity decisions.

This wiki is rendered in both **GitHub** (online review, PR diffs) and
**Obsidian** (local research, graph view). All markdown must work in
both renderers. The key constraint: no `<a id="...">` HTML anchors
(Obsidian ignores them). Instead, keep heading text equal to the target
slug so both platforms auto-generate the same `#slug` anchor.

## Coverage goal

The wiki aims for **complete spatiotemporal coverage**: every km² of
land surface, for every year from 1800 to 2025, should be accounted
for by at least one WHEP polity row. Polity pages must therefore be
deeply intertwined — when one polity ends, its successor(s) must
account for all of its territory, and when a polity begins, its
predecessor(s) must be documented. Gaps are bugs.

In practice this means:
- Every polity page's *Predecessors and successors* section must be
  complete: if the territory went somewhere, the successor row must
  exist and link back.
- Dissolution events (Ottoman Empire, Austria-Hungary, USSR) need
  *all* successor states documented, not just the obvious ones.
- Colonial acquisitions by European empires correspond to the *end*
  of a local polity — both sides of the transition must have pages.
- The index should track coverage by continent and flag regions with
  no wiki pages despite having CSV rows.
- Open questions about missing predecessor/successor links are high
  priority — they represent gaps in the spatial coverage model.

## What a WHEP polity is

Before reading anything else in this file, understand this: a WHEP polity is
a **territorial-economic unit** with trade or production data attached, not
a Westphalian legal state. The full rule is in
`wiki/log.md` 2026-04-11 `decision-whep-polity-definition` and is the most
load-bearing rule in the wiki. In short:

- A new polity row is created when the **territory** changes substantially,
  not when the legal status of the unit changes.
- If the territory stays the same, the polity stays a single continuous row
  across regime changes, occupations, personal unions, and periods when
  external state-system datasets (COW, GW, CShapes) do not list it as
  independent.
- A colony with its own trade statistics is a WHEP polity. A legally
  independent state under military occupation whose borders did not move
  is the same WHEP polity before and after.

This means WHEP start/end years **will routinely differ** from COW, GW, or
CShapes independence dates. This is **not** a contradiction. Record the
difference in *Sourced claims*, not *Contradictions*. *Contradictions* is
reserved for disagreements **within the same definition** — two atlases
disagreeing on when a border moved, not WHEP and COW using different
definitions of statehood.

Ingest implication: CShapes, Euratlas, Cliopatria, and historical atlases
(territorial-extent sources) can justify splitting or continuing a WHEP
polity. COW, GW, Polity V, V-Dem (state-system-membership sources) can
inform regime/status notes but **must not** drive start or end years.

## Layers

1. **Raw sources** — `wiki/sources/*.md`, one per external reference
   (atlas, HGIS release, paper, dataset). Immutable once ingested; new
   information becomes a new source file, never an edit.
2. **Polity pages** — `wiki/polities/<slug>.md`, one per polity in the
   database. Synthesized, cross-referenced, every non-trivial claim cited.
3. **Index & log** — `wiki/index.md` (catalog of polity pages + coverage)
   and `wiki/log.md` (chronological record of decisions, contradictions,
   open questions).

## Slug convention

`<polity_code>` from the CSV, lowercased, with `-` preserved:
`cpv-1800-2025.md`, `lux-1839-2025.md`. One file per row in the database.
Aggregate pages (continents, unions) live in `wiki/polities/_aggregates/`.

## Page schema

Every polity page MUST have this frontmatter and these sections. Empty
sections are allowed; missing sections fail lint.

```markdown
---
polity_code: <CSV polity_code>
polity_name: <CSV polity_name>
start_year: <int>
end_year: <int>
type: national | subnational
iso3: <code or NA>
cow: <code or NA>
status: draft | reviewed | contested
last_ingest: <YYYY-MM-DD>
sources: [source-slug-1, source-slug-2]
---

# <polity_name>

## Summary
One paragraph. What this polity is, why it's a distinct row in the database,
the dates and what they mean.

## Territorial extent
Borders over time. Cite the polygon source and any competing delineations.
Flag the years where the polygon is known to be approximate.

## Predecessors and successors
Links to other wiki pages: [[lux-1839-2025]]. Note partial successions
(territory split, population moved, name continuity without legal continuity).

## Sourced claims
Bulleted facts, each with an inline citation `[source-slug §section]`.
This is the load-bearing section — queries synthesize from here.

## Contradictions
Where sources disagree, record both positions and which one the database
follows, with reasoning. Do not silently pick a side.

## Decisions
Link to `log.md` entries that affected this polity
(`[log 2026-04-11 luxembourg-readd]`).

## Open questions
Things the next ingest should try to resolve. Each question is an
H3 heading of the form `### oq-<short-kebab-case>`, followed by a
short title and the question body:

    ### oq-polygon-provenance

    Pre-1886 polygon provenance. The 1839–1885 window is fully
    outside CShapes' scope ...

GitHub auto-generates the anchor `#oq-polygon-provenance` from the
heading text, so cross-references elsewhere on the page resolve to
that anchor. When an open question is resolved, do not delete —
replace the body with a one-line pointer to the `log.md` entry
that resolved it. This preserves the slug as a stable anchor for
older cross-references.
```

## Cross-reference conventions

All inter-file references MUST be real markdown links so GitHub
renders them as clickable. Use **reference-style** links, defined
once in a block at the bottom of each file. This keeps inline text
scannable (`[cshapes-2.0 §scope]` reads as a citation marker) and
centralizes the URL targets.

```markdown
    The 1878 Congress of Berlin [cshapes-2.0 §coding-changes]
    is the single biggest territorial change in the row ...

    ...

    [cshapes-2.0 §scope]: ../sources/cshapes-2.0.md#scope
    [cshapes-2.0 §coding-changes]: ../sources/cshapes-2.0.md#coding-changes
    [oq-polygon-provenance]: #oq-polygon-provenance
    [log decision-cshapes-is-cow-based]: ../log.md#decision-cshapes-is-cow-based
    [database]: ../../data/final/polities_database.csv
    [ott-1800-1886]: ott-1800-1886.md
```

Conventions:

- Citation identifiers use the literal `source-slug §section` form
  inside square brackets, WITHOUT backticks around them. Backticks
  render the whole thing as code and break the link.
- Same-page open-question references use `#oq-slug`.
- Cross-page polity references use `polity-slug.md` (no slash
  prefix — paths are relative to the current file's directory).
- Log references use `../log.md#slug`. Log entry headings are
  `## slug` (the slug alone, no date prefix), so both GitHub and
  Obsidian auto-generate the `#slug` anchor from the heading text.
  The date goes on a `**Date:** YYYY-MM-DD` line inside the entry.
- Source section references use `../sources/source-slug.md#section`.
  Source file section headings are `### section` (no `§` prefix),
  so both GitHub and Obsidian auto-generate the `#section` anchor.
  The `§` character is used only in inline citation display text
  (`[biger-1995 §austria]`), not in the actual heading.
- `[database]` points at the final CSV so readers can jump to
  the row directly.

When adding a new reference, append its definition to the bottom
block rather than editing inline. The block is what lint and
query prompts inspect to understand what the page depends on.

## Source schema

```markdown
---
source_slug: <short-id>
title: <full title>
author: <author or org>
year: <publication year>
url: <if available>
access_date: <YYYY-MM-DD>
type: atlas | hgis | paper | dataset | gazetteer | other
coverage: <geographic + temporal scope>
---

# <title>

## Why it was ingested
One sentence.

## What it adds
The specific polities/claims/borders this source lets us cite.

## Known limitations
Biases, gaps, date of underlying data, transcription caveats.
```

## Workflows

Prompts for each workflow live in `wiki/prompts/`:

- **Ingest** (`prompts/ingest.md`) — add a new raw source and propagate
  its claims into 5–15 polity pages. Always updates `log.md`.
- **Query** (`prompts/query.md`) — answer a research question from the
  wiki. May file newly-discovered facts back into pages.
- **Lint** (`prompts/lint.md`) — health check: missing citations, orphan
  pages, stale `last_ingest`, contradictions never resolved, polities in
  the CSV with no wiki page (and vice versa).
- **Autonomous-next** (`prompts/autonomous-next.md`) — self-paced
  meta-prompt used with the `/loop` skill. Inventories the wiki state,
  classifies every open question into priority tiers, picks ONE task,
  delegates execution to one of the other three prompts, commits, and
  decides whether to continue. Does not replace the other prompts —
  *chooses among them*. Has explicit Tier-X and never-autonomously
  guardrails (no CSV edits, no `decision`-kind log entries, no
  `git push`, no closed-access source acquisition, no `draft → reviewed`
  status changes unless schema requirements are met).

## Rules for the agent

1. **Never invent citations.** If a claim has no source in `wiki/sources/`,
   either cite `[database]` (meaning: it came from the CSV and has no
   deeper source yet) or move it to *Open questions*.
2. **Sources are immutable.** Correcting an old source means adding a new
   source that supersedes it and updating the affected polity pages.
3. **Record contradictions, don't resolve them silently.** If a new source
   disagrees with an existing page, add it to *Contradictions* and log it.
   A human decides which to follow.
4. **Every edit appends to `log.md`** with date, polity codes touched,
   source slug, and a one-line rationale.
5. **Never edit `data/final/polities_database.csv` from a wiki workflow.**
   The wiki proposes changes in `log.md`; humans apply them.
6. **The CSV is evidence, not authority.** Nothing in the existing WHEP
   state — the CSV, the `docs/` tree, the R pipeline, prior log entries,
   even this wiki's own polity pages — should be treated as correct by
   default. Every artifact was produced by fallible humans and automated
   processes, and may contain errors, mislabellings, orphaned rows,
   stale decisions, or unreviewed oversights. See *Critical stance*
   below. When in doubt, audit first and cite second.
7. **Do not attribute intent to state.** Never write prose that presumes
   a WHEP state — a row, a split, a polygon source, a column value — was
   the result of a conscious design choice unless you can point at
   concrete evidence (a `docs/` section that explains it, a `log.md`
   entry of `kind: decision`, a commit message with rationale). If no
   evidence exists, say so explicitly on the polity page and flag it as
   a candidate oddity.

## Critical stance: audit, don't deferentially cite

The CSV in `data/final/polities_database.csv` is a ~1,400-row dataset
built over several WHEP versions by multiple humans and automated
processes. It contains known errors, legacy artifacts, unreviewed
merges, and oddities that no one has gotten around to fixing. Any
polity page that cites the CSV is citing *one version of one dataset*,
not the ground truth.

When you encounter something that looks off, **treat it as a candidate
bug first**, not a "decision worth surfacing." Things that should
trigger audit mode include:

- **Row labels that contradict their time range.** The canonical
  example from this session: `F228-1905-1914 USSR (1905-1914)` — the
  USSR did not exist in 1905; it was not proclaimed until 30 December
  1922. Either the row label is wrong (should be "Russian Empire") or
  the time range is wrong. Both are possible. Audit.
- **Overlapping rows for the same entity.** `TUR-1800-1912` exists as
  a national row alongside the three `OTT-*` rows covering the same
  period. `DEU-1800-1919` exists alongside `GER-1800-2025
  Germany/Zollverein` covering the same period. Overlap is a signal,
  not a convention.
- **Missing rows for entities that should exist.** There is no `PRU`
  row in the CSV despite Prussia being the largest and most important
  German state from 1815 to 1871 and the leading force behind German
  unification. Either (a) Prussia is deliberately absorbed into `DEU`
  for some defensible reason documented somewhere, or (b) it is an
  oversight. Do not assume (a) without evidence.
- **Splits at dates that match a data-source cutoff rather than a
  historical event.** The `OTT-1800-1886 → OTT-1886-1908` split is at
  1886 because CShapes temporal coverage starts in 1886, not because
  anything happened to the Ottoman Empire on 1886-01-01. Under the
  WHEP polity-definition rule this is inconsistent, and calling it a
  "pragmatic choice" without evidence of that being a deliberate
  exception is rationalization.
- **Orphaned rows** not reached by any predecessor / successor chain.
- **`notes = NA`** on rows where every sibling has substantive notes.
- **Row types (`national` vs `aggregate` vs `subnational`) that don't
  match the entity.** E.g. something labeled `national` that is
  clearly an aggregate.

For each audit finding:

1. **Check `docs/` and `wiki/log.md`** for any human-signed rationale.
   If you find one, cite it on the polity page as the justification.
2. **If no justification exists**, do NOT rationalize it. Add a
   `proposal`-kind log entry naming the specific row(s) or column(s)
   and describing the oddity, with a recommendation and a "for human
   review" note.
3. **Do not silently propagate oddities.** A weird row label is a
   signal, not a fact to be cited verbatim on a polity page. If you
   have to cite it, hedge explicitly: "the current CSV labels this
   row `USSR (1905-1914)`, which is an anachronism — the USSR did
   not exist until 1922 — and has been flagged in
   [log proposal-...]."
4. **Maintain a `contradictions` entry when CSV and external sources
   disagree.** A territorial event that Biger or Wikipedia places in
   1866 but the CSV splits at 1871 is a contradiction, not a
   convenience.

The grading standard: a polity page that reads "WHEP tracks this as
X because of Y (doc reference)" is good. A polity page that reads
"the CSV does X" followed by a paragraph inferring intent is bad.
