# WHEP Polities Wiki

A persistent, compounding knowledge base that backs the judgment calls in
`data/final/polities_database.csv`. Curated by humans, maintained by an LLM
agent against the rules in this file.

This wiki is **not** methodology documentation — that lives in `docs/`. It is
the evidence and reasoning trail behind individual polity decisions.

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
Things the next ingest should try to resolve.
```

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
