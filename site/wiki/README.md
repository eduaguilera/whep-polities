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
- **CShapes splits are not automatically WHEP splits.** CShapes records
  multiple time-steps for administrative changes (independence dates,
  regime changes, colonial transfers) that do not alter territory. The
  test is whether `ST_Area(geom)` changes between CShapes time-steps.
  Same area = same WHEP polity = one row. Different area = territorial
  change = new row. When CShapes has no polygon for a period (pre-1886),
  use Biger, Wikipedia, or other sources to determine whether the
  territory actually changed.
- **No overlapping rows.** Every km² must be assigned to exactly one
  WHEP polity for any given year. If two rows for the same entity have
  overlapping date ranges, one is wrong — either merge them (if same
  territory) or fix the dates (if genuine split). "Umbrella" rows that
  span the full period alongside a sub-chain are never acceptable.

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

## Sister Wiki — WHEP Project Wiki

This polities wiki is one of two LLM wikis in the WHEP project:

- **This wiki** (`~/whep-polities/wiki/`) — Territorial decisions, boundary evidence, political entity chains
- **WHEP project wiki** (`~/whep-wiki/wiki/`) — Full project scope: environmental impacts, trade, planetary boundaries, methods, datasets, literature (37+ ingested papers)

For scientific context on why these territorial decisions matter:
- `~/whep-wiki/wiki/concept-trade-displacement.md` — Why territorial accuracy matters for trade
- `~/whep-wiki/wiki/project-wp3.md` — How trade reconstruction uses polities
- `~/whep-wiki/wiki/data-whep-polities.md` — Technical overview of this database from the project perspective
- `~/whep-wiki/wiki/topic-polities-wiki-bridge.md` — Full bridge reference between both wikis

## Polygon workflow

**Wiki is the source of truth.** `data/final/polities_database.csv` and the
committed `data/final/polities_database.gpkg` are derived artifacts rebuilt
by `scripts/build_database.py` from the wiki's frontmatter plus raw polygon
source files on disk.

**Frontmatter polygon fields** (see `wiki/polities/_template.md`):

- `polygon_source` — slug of a source registered in `scripts/sources.yaml`
  (e.g. `cshapes-2.0`, `gadm-4.1`, `paine-2024`, `histogis-1860-habsburg`,
  `cliopatria`, `constructed`, `none`).
- `polygon_feature_id` — value to match against the source's declared
  `id_column` (e.g. gwcode `305` for CShapes, `AUT` for GADM, `Asante`
  for Paine).
- `polygon_feature_year` — only for sources with a `temporal` block in
  `sources.yaml`; picks a specific time-step.
- `polygon_status` — **load-bearing, not descriptive.** `scripts/validate_polygons.py`
  keys off these values, so choosing the wrong one either hides a real error or
  fails the build:

  | value | means | validator behaviour |
  |---|---|---|
  | `assigned` | the polygon **is** this polity's territory for the period | check A **fails** if the geometry's measured area diverges >25% from `polygon_area_km2` |
  | `proxy` | a stand-in from another period or entity, knowingly inexact | divergence reported, not failed — but the page must document direction and magnitude |
  | `estimate` | approximate, no exact feature exists | same as `proxy` |
  | `polygon_vintage_drift` | the polygon's vintage is unrepresentative of much of the row's span — typically a single snapshot back-projected across a long period. The vintage is usually INSIDE the span, not outside it: every row carrying this value today has a vintage within its own dates (`BRA-1800-1903` uses an 1890 polygon, `IND-1800-1886` an 1880 one). An earlier wording said "sits outside the row's span", which is not how the value is used and led to two rows being mislabelled `proxy`. | same as `proxy` |
  | `unassigned` | **no polygon**, with the reason documented | check C ignores it; this is the honest state when no source exists |

  Check C **fails** when any of `assigned`/`proxy`/`estimate`/`polygon_vintage_drift`
  is declared but the build attached no geometry — a page must not claim a polygon
  it does not have. Prefer `unassigned` with a documented reason over a silent
  modern-borders guess.

  Four legacy values — `derived`, `missing`, `approximate`, `excluded` — predate
  this vocabulary and are **no longer present**: all rows were migrated and
  `build_database.py --check` now rejects anything outside the five above. This
  paragraph said they were "still present in the database" until the migration
  landed without it being updated, which is why validate_constants.py now checks
  this table against the enforced set.
- `polygon_area_km2` — optional sanity-check, and it means **the area of the territory this
  polygon represents**, not the area of the geometry this repository happens to ship.
  Issue 71 asked which, because the two had come apart: `build_database.py` simplifies,
  densifies and repairs before writing, and simplification alone once deleted 42% of the
  Maldives (299.68 km² at source, 172.62 shipped, 791 atolls almost all smaller than the
  0.01° tolerance). An archipelago could then state the truth and fail check A on a correct
  polygon, or state the rendering and understate the country by 42%.

  The two now coincide by construction, not by luck: the build's simplification carries an
  area budget (`SIMPLIFY_MAX_AREA_CHANGE`) and `validate_simplification_loss.py` asserts
  that every shipped polygon stays within 5% of the source it was cut from — measured
  2026-08-13, the largest movement across all 735 is 2.1%. So check A's 25% tolerance tests
  the territory, and a divergence means the declared figure or the binding is wrong, never
  the rendering. Declare the official or source-stated area; do **not** re-measure it off
  the shipped polygon, which is the tautology check A2 counts.
- `predecessor`, `successor` — YAML lists of UPPERCASE `polity_code`s
  (`[]` for none). Drives the site's Graph tab edges and the coverage-
  chain integrity checks in lint. Every code listed here should also
  have its own wiki page; lint flags orphan references. The
  `## Predecessors and successors` prose section documents the *nature*
  of each transition (treaty, annexation, dissolution, etc.); the
  frontmatter is the machine-readable reference.

**Source data (`data/geodata/<slug>/`) is never committed.** Each source
has a fetch script under `scripts/sources/<slug>/fetch.{sh,R}` that
re-downloads the raw file from its original location. Run fetch scripts
before running the builder.

**Visualization site** — `site/index.html` (MapLibre GL JS map with year
slider, search, and type filters) reads `site/polities.csv` and
`site/polities.geojson`. Both are regenerated by `bash scripts/rebuild.sh`
(the single entry point that also rebuilds the master GeoPackage).

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

## Prefix convention

A polity code is `PREFIX-startyear-endyear`. The prefix names a **territory**,
not a regime and not a name — so it is the part that answers "is this the same
place?" while the period answers "when?" and `polity_name` carries what it was
called at the time.

This has a consequence that looks like an inconsistency until you know the rule:
**a prefix is NOT always the modern ISO3.** 84 live prefixes differ from their
row's `iso3_code`, and 29 ISO3 families span more than one prefix. Those are
deliberate. A distinct prefix marks a distinct territory that later merged into,
or split away from, the modern state:

| family | prefixes | why |
|---|---|---|
| `USA` | `ALK`, `USA` | Alaska, acquired 1867, is its own territory |
| `IND` | `HYD`, `IND` | Hyderabad acceded in 1948 |
| `LBY` | `CYR`, `TRP`, `LBY` | Cyrenaica and Tripolitania before unification |
| `MYS` | `BNB`, `BSW`, `GBM`, `MASG`, `MYS` | North Borneo, Sarawak, Malaya |
| `GHA` | `BTL`, `GCT`, `GHA` | British Togoland, and the Gold Coast composite |
| `SDN` | `SUD`, `SDN` | `SUD-1899-1934` is 2,579,525 km2 — Sudan INCLUDING what became South Sudan. `SDN-2011-2025` excludes it. Different territory, so a different prefix. |

So when a source label needs routing, resolve it to a **period**, never to a bare
prefix: `ETH` is a family and cannot receive data, `ETH-1907-1936` can. An alias
targeting a bare prefix is rejected by `scripts/validate_aliases.py`.

### Where the convention is not cleanly applied

Four chains use separate prefixes for what is arguably the SAME territory under a
changed regime, rather than a different territory:

`ANG-1905-1975` / `AGO-1975-2025` (Portuguese Angola then Angola), `BEC-1885-1966`
/ `BWA-1966-2025` (Bechuanaland then Botswana), `NRH-*` / `ZMB-1964-2025`, and
`SRH-1953-1964` sitting between `ZWE-1900-1953` and `ZWE-1964-1980`.

Under the rule above these would be one prefix each. They are left as they are on
purpose:

- Renaming changes `polity_code`, which is identity. It invalidates the manifest's
  `identity_sha256`, every alias targeting those codes, the published maps, and
  every downstream copy — for a cosmetic gain.
- The functional problem it would have solved is already solved. A consumer whose
  area maps to only one prefix could not reach the colonial polity, so
  pre-independence years fell through to the modern one. The WHEP R package fixed
  that by mapping such areas to BOTH prefixes (eduaguilera/whep#387), which needs
  no change here.
- `FRS-1884-1977` / `FRS-1977-2025` (French Somaliland, then Djibouti) shows the
  opposite choice on the same question: one prefix for the whole chain, and the
  HISTORICAL one rather than the modern ISO3 `DJI`. So there is no single
  precedent to be consistent with.

Do not "fix" these by renaming without a decision recorded here first.

## Page schema

Every polity page MUST have this frontmatter and these sections. Empty
sections are allowed; missing sections fail lint.

```markdown
---
polity_code: <CSV polity_code>
polity_name: <CSV polity_name>
start_year: <int>
end_year: <int>
type: national | colonial | aggregate | subnational | territory | city-territory | disputed | statistical
iso3: <code or NA>
cow: <code or NA>
status: draft | reviewed | superseded | retired
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

## What `status` commits you to

`status: reviewed` asserts that **a human checked this page's claims against
sources**, and the assertion-verification pipeline relies on it: draft pages are
treated as a prior agent's hypothesis and must be corroborated independently,
whereas a `reviewed` page can be leaned on. So promoting a page is a substantive
act, not bookkeeping.

`scripts/validate_polygons.py` check D therefore **fails** if a `reviewed` page
carries zero source citations or still contains `(to be documented)`. Thirteen
pages were downgraded to `draft` on 2026-07-24 for exactly that reason — they
claimed review while being unsourced stubs, which invited unsourced assertions to
be treated as verified.

`superseded` and `retired` mean the row no longer receives data (it was split,
merged, or withdrawn). Both are excluded from matching entirely — see
`pipelines/polity-autoimprove/matchlib.py`, `DEAD_STATUS` — so a page must not be
left in a dead status while data still needs to route to it.

## Cross-reference conventions

All inter-file references MUST be **inline markdown links** using
standard relative paths. Both GitHub and Obsidian navigate these
correctly.

```markdown
    The 1878 Congress of Berlin
    [cshapes-2.0 §coding-changes](../sources/cshapes-2.0.md#coding-changes)
    is the single biggest territorial change in the row ...

    See [ott-1800-1886](ott-1800-1886.md) for the predecessor.
    Logged at [log decision-foo](../log.md#decision-foo).
```

Conventions:

- **Source citations** from polity pages:
  `[biger-1995 §austria](../sources/biger-1995.md#austria)`.
  The `§` is display-only; the heading in the source file is
  `### austria` (no `§` prefix).
- **Same-page anchors**:
  `[oq-polygon-provenance](#oq-polygon-provenance)`.
- **Cross-page polity references** (same directory):
  `[ott-1800-1886](ott-1800-1886.md)`.
- **Log references** from polity pages:
  `[log slug](../log.md#slug)`. Log entry headings are `## slug`
  (slug alone, no date prefix), so both renderers auto-generate
  `#slug`. The date goes on a `**Date:**` line inside the body.
- **Database link**: `[database](../../data/final/polities_database.csv)`.
- **Do not use reference-style links** (`[text][ref]` +
  `[ref]: url` at the bottom of a file). Obsidian cannot navigate
  them. Always use inline `[text](path)` format.

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

**Splitting, merging, retiring, re-dating or creating a polity** is a
*structural* change: it silently re-routes the data rows that match the affected
polities, and the wiki diff shows none of that. Follow the eleven-step
**structural-change checklist** in
[`pipelines/polity-autoimprove/README.md`](../pipelines/polity-autoimprove/README.md#structural-change-checklist-split--merge--retire--re-date--create)
— snapshot the per-polity row counts *before* the edit with
`python3 scripts/structural_change_check.py --snapshot`, then `--compare` after.
The checklist lives with the pipeline because its central check needs the matcher
and the layer-B dataset; the human steps (writing the page, the `log.md`
`decision` entry naming who signed off) are recorded there alongside.

## Rules for the agent

1. **Never invent citations.** If a claim has no source in `wiki/sources/`,
   either cite `[database]` (meaning: it came from the CSV and has no
   deeper source yet) or move it to *Open questions*.
1b. **Never create skeleton pages from CSV metadata alone.** Every polity
   page must contain at least one sourced claim from an external source
   (Biger, CShapes, COW, Wikipedia, or another academic source) beyond
   just citing `[database]`. A page that only echoes CSV data adds
   nothing — the CSV already exists. Pages are created through the
   ingest workflow with real research, not bulk-generated from the CSV.
   Quality over quantity: 220 sourced pages are worth more than 1386
   empty shells.
2. **Sources are immutable.** Correcting an old source means adding a new
   source that supersedes it and updating the affected polity pages.
3. **Record contradictions, don't resolve them silently.** If a new source
   disagrees with an existing page, add it to *Contradictions* and log it.
   A human decides which to follow.
4. **Every edit appends to `log.md`** with date, polity codes touched,
   source slug, and a one-line rationale.
5. **The agent maintains `data/final/polities_database.csv` directly.**
   When the wiki's sourced findings require CSV changes, the agent
   applies them and logs each change in `log.md`. The R pipeline
   (`R/01_build_master_db.R`) that originally generated the CSV is
   obsolete — the wiki is now the authoritative source and the agent
   is the maintainer.
6. **The wiki is the primary source of truth; the CSV must conform to
   it.** This wiki is built on cited academic sources (Biger, CShapes,
   COW, historical atlases). The CSV in `data/final/polities_database.csv`
   was built by automated processes and contains known errors. When the
   wiki's sourced findings contradict the CSV, the CSV is wrong and
   should be updated — not the other way around. The agent applies
   CSV changes directly (splits, merges, renames, new rows, deletions)
   when backed by sourced wiki findings, and logs each change.
   Structural decisions (new chain architecture, polity-definition
   edge cases) use `decision`-kind log entries.
   Nothing in the existing WHEP state — the CSV, the `docs/` tree, the
   R pipeline, prior log entries — should be treated as correct by
   default. Every artifact was produced by fallible humans and automated
   processes. See *Critical stance* below.
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
