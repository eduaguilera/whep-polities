# Wiki Log

Chronological record of every non-trivial change to the wiki. Append-only.
Each entry is a dated H2 heading. Newest on top.

Entry format:

```markdown
## YYYY-MM-DD — <slug>
**Touched:** polity-code-1, polity-code-2
**Source:** <source-slug or "none">
**Kind:** ingest | decision | contradiction | proposal | lint

<one or two paragraphs of rationale. Link to pages and sources.>
```

Kinds:
- **ingest** — a new source was added and its claims propagated.
- **decision** — a judgment call affecting the CSV (add/remove/split
  polity, change dates, reclassify type). Must name the human who signed off.
- **contradiction** — two sources disagree on a load-bearing fact; logged
  and left open until a human resolves it.
- **proposal** — a change the wiki suggests to the CSV but has not applied.
- **lint** — bulk cleanup from a lint run.

---

<a id="decision-csv-is-evidence-not-authority"></a>
## 2026-04-11 — decision-csv-is-evidence-not-authority
**Touched:** wiki/README.md, wiki/prompts/ingest.md, wiki/prompts/lint.md, wiki/prompts/autonomous-next.md
**Source:** none (stated by the project maintainer in conversation)
**Kind:** decision

User feedback interrupted an Austria-Hungary research iteration:
"*dont take any of my decisions as a source of truth. dont just read
my current data and say 'this was a conscious decision'. consider
everything might be wrong. do update prompts to keep that in mind.
you can think autonomously*" (2026-04-11).

This is a **meta-rule** about how the wiki treats existing WHEP state.
The rule is simple: **the CSV is evidence, not authority.** Nothing
in `data/final/polities_database.csv`, the `docs/` tree, the R
pipeline, or prior log entries should be treated as correct by
default. Every artifact was produced by fallible humans and
automated processes, and may contain errors, mislabellings,
orphaned rows, stale decisions, or unreviewed oversights.

The rule existed implicitly in the wiki before this entry — the
very first Ottoman ingest found the `TUR-1800-1912` duplication and
filed a proposal entry for it — but the prompts and README did not
make it explicit, and the agent had drifted into rationalizing
oddities rather than auditing them. Three examples from the
session that prompted this decision:

1. **`F228-1905-1914 USSR (1905-1914)`** — the CSV labels this
   row "USSR" but the USSR did not exist until 30 December 1922.
   Either the label is wrong (should be "Russian Empire") or the
   time range is wrong. Both are possible. The agent earlier this
   session called this "mislabeled" without pressing on which
   side of the mislabeling was at fault.
2. **`DEU-1800-1919` and `GER-1800-2025 Germany/Zollverein`**
   overlap entirely across 1800–1919. The agent earlier this
   session speculated "probably an aggregate row for the trade
   regime" without evidence. Under the new rule, speculation is
   forbidden — either cite evidence or file a proposal.
3. **No `PRU` (Prussia) row in the CSV** despite Prussia being
   the core German state 1815–1871. The agent earlier this
   session called this "a design choice worth surfacing". Under
   the new rule, it is a candidate oversight to be documented as
   a proposal unless `docs/` or `log.md` contains evidence that
   Prussia was deliberately absorbed into `DEU`.

**Applied in this entry:**

- **`wiki/README.md`**: added rules #6 and #7 to the "Rules for
  the agent" section (CSV is evidence, not authority; do not
  attribute intent to state without evidence), plus a new
  top-level section *Critical stance: audit, don't deferentially
  cite* with a typology of CSV oddities (row labels vs time
  range, overlapping rows, missing rows, splits at data-source
  cutoffs, orphan rows, `notes = NA`, wrong polity_type).
- **`wiki/prompts/ingest.md`**: inserted a CSV audit substep
  inside phase 2 (identify affected polity pages). The ingest
  flow now cannot silently proceed past a CSV oddity — the agent
  must either cite documented evidence or file a proposal.
- **`wiki/prompts/lint.md`**: added a new check #8, *CSV oddity
  detection*, that scans for the oddity typology described in
  `wiki/README.md` and recommends proposal entries. Read-only;
  does not auto-fix the CSV.
- **`wiki/prompts/autonomous-next.md`**: added CSV oddity
  detection to the phase 1 inventory checklist, and added "a CSV
  oddity that a single `proposal`-kind log entry can document"
  to the Tier 1 (easy wins) list. The Russian Empire / USSR
  labeling issue is named as the canonical example.

**How this changes polity-page writing style:**

Before: "WHEP carries a separate row for X because Y. The repo's
convention is Z."

After: "The current CSV tracks X as row Y. No rationale for this
is documented in `docs/` or `log.md`; see
[log proposal-...] for the audit finding."

Hedging in the body and flagging in the log is strictly better
than speculation in the body and nothing in the log.

**Not touched:** the existing polity pages (Luxembourg, the three
Ottoman rows). Those will be re-audited opportunistically in
future ingests under the new rule. The Ottoman pages already do a
reasonable job at flagging the 1886 split as polygon-source
artifact; the Luxembourg page uses cleaner sourced-claims
language. No immediate rewrites needed.

**Next action:** resume autonomous research on European empires
1850–present, starting with Austria-Hungary, applying the new
critical stance from iteration 1 forward. Specifically: audit
the AUH chain for CSV oddities during phase 1 before any Biger
reads.

---

<a id="autonomous-next-prompt-added"></a>
## 2026-04-11 — autonomous-next-prompt-added
**Touched:** wiki/prompts/autonomous-next.md (new), wiki/README.md
**Source:** none
**Kind:** decision

User requested a self-paced autonomous mode for the wiki where the
agent picks its own next task from the current state rather than
waiting for per-step human direction, inspired by Karpathy's
autoresearch pattern ([user question in conversation, 2026-04-11]).

Added `wiki/prompts/autonomous-next.md` as a documentation-only
change. **No loop has been run yet** — the prompt is stage 1 of a
two-stage rollout:

1. **Stage 1 (this entry)** — write the prompt, commit, let the user
   review the priority rules and guardrails before anything executes.
2. **Stage 2 (future)** — kick off `/loop autonomous-next` with a
   deliberately-low `max_iterations` cap (default: 3 on first run),
   review the iterations, raise the cap only after the user has seen
   it behave.

The prompt encodes a four-phase cycle per iteration (state inventory
→ classify open questions into tiers → pick ONE task → execute,
commit, decide whether to continue) and has explicit hard stop
conditions and a never-autonomously guardrail list.

**Hard guardrails** (not priority penalties — absolute prohibitions):

- No edits to `data/final/polities_database.csv`. Only `proposal`
  log entries.
- No `decision`-kind log entries that establish a repo-wide rule.
  The agent may *draft* a decision and surface it in the iteration
  report, but the entry itself is human-owned.
- No `git push`, no force push, no branch deletion, no
  `--no-verify`.
- No edits to `renv.lock`, `.gitignore`, `wiki/README.md`, or
  anything in `wiki/prompts/`.
- No closed-access source acquisition.
- No `draft → reviewed` status change unless schema requirements
  are met (academic corroboration beyond Wikipedia, no unresolved
  Contradictions, every Sourced claims bullet cited).

**Stop conditions** (any one ends the loop):

- Priority exhausted — only Tier X (user-decision / missing source)
  work remains.
- Iteration cap reached.
- Proposal accumulation — if the loop generates 2+ new `proposal`
  entries without the user having reviewed them, stop for review.
- Repeated failure on the same task.
- New contradiction surfaced.
- Commit failure.

**Priority tiers:**

- Tier 1 — Easy wins (single action + already-available source).
  The Biger Ottoman batch is the canonical example of what this
  tier looks like after a fresh ingest opens up source-expansion
  opportunities.
- Tier 2 — Source expansion (fixed-cost-already-paid ingests).
- Tier 3 — New polity page creation for dangling refs or
  frequently-cited missing polities.
- Tier 4 — Deep work (multi-iteration projects).
- Tier X — Cannot be done autonomously. If the highest-priority
  question is Tier X, skip and move on.

Within a tier, ties are broken by: number of polity pages affected,
recency of the blocking source, proximity to a status change.

**Iteration report format:** every iteration emits an H2 entry of
`kind: autonomous` to `wiki/log.md` with a full audit trail
(inventory, classification, selection, execution, outcome, stop
decision). This is the mechanism against drift — the user can read
the log and see which tier was chosen, why, and whether the loop
was gaming the metric.

**Immediately-executable Tier 1 candidates** the loop would pick up
on its first run (listed here for user reference — not yet
resolved):

- `oq-bosnia-double-count` on `ott-1886-1908`: a single `ogrinfo`
  SQL query on `data/geodata/cshapes2_full.gpkg` for `cowcode=640`
  during 1886–1908 vs the `BOS-1878-1908` polygon, compared via
  `st_intersects`.
- The five remaining partially-resolved open questions where Biger
  content already on disk has sections (BULGARIA, GREECE, SERBIA,
  EGYPT) not yet read that could fully resolve `oq-1830-events`
  and related questions.
- Stale `wiki/index.md` counters if any of the recent ingests
  have drifted them.

Not yet wired to `/loop` — the user will trigger stage 2 manually.

---

<a id="biger-ottoman-batch-ingest"></a>
## 2026-04-11 — biger-ottoman-batch-ingest
**Touched:** OTT-1800-1886, OTT-1886-1908, OTT-1908-1912; wiki/sources/biger-1995.md
**Source:** biger-1995 (existing)
**Kind:** ingest

Second pass through Biger 1995 after the Luxembourg ingest, this
time targeted at the Ottoman successor states that directly
appear on the three OTT polity pages. Four entries read:

- **ALGERIA** (pp.22–28) — 1830 French conquest, 1847 full
  northern control, 1848 three départements, 1881 integration
  with France, 1902-12-24 Sahara annexation, plus the
  1845-03-18 Morocco–Ottoman treaty and the 1910-05-19
  Franco-Ottoman boundary convention (both rarely-cited
  specific dates for formal Franco-Ottoman territorial
  agreements).
- **BOSNIA AND HERZEGOVINA** (pp.85–87) — 1461–1483 Ottoman
  conquest, 1875–1878 Balkan crisis, 1878 start of
  Austro-Hungarian administration, 1878–1918 as a continuous
  "period of Austro-Hungarian rule". **Biger limitation:** he
  does not distinguish the 1878 de facto occupation from the
  1908 formal annexation — recorded in the source file's
  limitations section and flagged on the polity pages.
- **LIBYA** (pp.359–362) — 1835 Ottoman direct rule restored,
  1890 Sanussi vs Ottoman Turks, 1911 Italian invasion,
  1912 Treaty of Ouchy, 1934 "Libya" as a name, 1951-12-24
  independence.
- **TUNISIA** (pp.28, 361, 494) — **exact treaty date for the
  Treaty of Bardo: 12 May 1881** (ALGERIA–TUNISIA, p.28).
  Corroborated in LIBYA–TUNISIA (p.361) and the TUNISIA main
  entry (p.494). Tunisia was an Ottoman province from 1564
  and semi-autonomous from the 17th century.

**Updated `wiki/sources/biger-1995.md`** with four new sections:
`§algeria`, `§bosnia`, `§libya`, `§tunisia`. The existing
`§luxembourg` section is unchanged. All quotes are
sentence-level fair-use under Biger's strict all-rights-reserved
notice.

**Three Ottoman polity pages updated:**

- `ott-1800-1886.md`:
  - **[oq-1830-events] partially resolved.** Biger directly
    corroborates the 1830 French conquest of Algeria with
    multi-page cross-references. The Greek War of Independence
    date range (1821–1829) is confirmed via the GREECE entry
    snapshot already in Wikipedia. The exact 1830 London
    Protocol date for Greek independence and 1830 Serbian
    autonomy mechanism remain not-verbatim-quoted — would need
    a GREECE or SERBIA focused Biger read or a dedicated source.
  - **[oq-further-splits-1830-1878] substantially
    strengthened.** Biger now provides academic anchor dates
    for both candidate split points (1830 and 1878). The
    historical case for splitting this row is solid; the
    remaining blocker is pipeline cost (extracting more
    Cliopatria time-steps for one polity).
  - New sourced claim: the 1830 Algeria loss quote from Biger
    p.22, replacing the earlier Wikipedia-only framing.

- `ott-1886-1908.md`:
  - **[oq-tunisia-boundary] RESOLVED.** Exact date: Treaty of
    Bardo signed 12 May 1881, five years before this row's
    1886 start. The CShapes Ottoman polygon for 1886 onward
    correctly excludes Tunisia; the issue is in the
    predecessor row.
  - 1878 Berlin Congress claim now has dual corroboration
    (Wikipedia + Biger).

- `ott-1908-1912.md`:
  - **[oq-libya-mid-row-change] partially resolved.** Biger
    gives a clean two-phase 1911/1912 framing: Italy
    "established itself in Libya in 1911" (LIBYA–SUDAN, p.361)
    and "In 1912 Italy captured Libya" (LIBYA main, p.359).
    These are consistent with 1911 = Italian invasion + 5
    November 1911 annexation declaration, 1912 = 18 October
    1912 Treaty of Ouchy. The Libya transfer is confirmed as
    a real, >1.5 million km², rapid territorial change
    *inside* this row's window — far above any plausible
    "substantial change" threshold. The remaining question is
    a repo-wide rule (end-of-row grace period, explicit
    sub-split, or polygon-source override) that a human must
    decide.
  - Bonus finding: the 1910-05-19 Franco-Ottoman boundary
    convention was still being demarcated on the ground by a
    joint commission in 1910–1911, immediately before the
    Italian takeover. This strengthens the case that the
    Libya loss was a real rapid change, not a
    polygon-availability artefact.

**Summary of open questions across OTT pages after this ingest:**

- Resolved: `oq-tunisia-boundary` (full), `oq-1830-events`
  (partial, 1830 Algeria confirmed, Greek/Serbian verbatim
  still needed), `oq-libya-mid-row-change` (partial,
  historical facts confirmed, repo-rule decision still
  needed), `oq-further-splits-1830-1878` (historical case
  solid, pipeline cost unresolved).
- Still fully open: `oq-1886-split-is-polygon-not-territory`
  (repo-rule decision), `oq-bosnia-double-count` (needs
  `ogrinfo` query), `oq-1912-1920-gap` (repo-rule decision),
  `oq-muhammad-ali-egypt-1831` (future EGY-* ingest),
  `oq-arab-revolt-1916` (future SAU-* ingest).

**Biger coverage not yet ingested** (for future passes):
BULGARIA, EGYPT, GREECE, IRAQ, LEBANON, SAUDI ARABIA, SERBIA,
SYRIA, YEMEN. These would be relevant when we create polity
pages for those successor states.

---

<a id="biger-1995-luxembourg-ingest"></a>
## 2026-04-11 — biger-1995-luxembourg-ingest
**Touched:** LUX-1839-2025
**Source:** biger-1995 (new)
**Kind:** ingest

User added Biger 1995 (*The Encyclopedia of International
Boundaries*, Facts on File, ISBN 0-8160-3233-5) to
`wiki/sources/pdfs/` under institutional / fair-use access.
552-page reference work; alphabetical by present-day state;
"includes only contemporary international land boundaries" with
historical background sections per boundary. Stricter copyright
than all prior wiki sources — full **all rights reserved**
notice on the copyright page — so the source file and polity
page use sentence-level fair-use quotes only, each with page
citation.

Created `wiki/sources/biger-1995.md` as the primary-source file
(copyright discipline documented up front, structure section on
how the book is organized, then a `§luxembourg` subsection
compiling quotes from the relevant cross-referenced entries).

Targeted read of three sections:

- **LUXEMBOURG** (p.365) — summary entry, medieval background,
  Grand Duchy creation in 1815, post-1830 split, Nassau-Weilburg
  succession.
- **BELGIUM** + **BELGIUM—NETHERLANDS** historical background
  (pp.67–70) — the precise 1831-01-20, 1831-11-15, 1838 dates
  and, most importantly, **"The limits of Eastern Duchy of
  Luxembourg (998 sq. miles [2,584 sq. km.] out of 2,700 sq.
  miles [7,000 sq. km.]) were established by the Treaty of 19
  April 1839"** (p.70).
- **GERMANY—LUXEMBOURG** historical background (pp.238–239) —
  1797 French cession, 1815 Vienna Treaty, 1830 revolt, **"The
  area became independent in its own right in 1848"** (p.239,
  new datum not in Wikipedia), 1867 severance of German
  Confederation ties, and the direct territorial-stability
  statement **"Since 1867 no changes in the boundary line were
  made... one of the most peaceful boundaries in the world
  today"** (p.239).

**Two open questions on `lux-1839-2025` resolved:**

1. `oq-academic-corroboration` — Biger (Tel Aviv University +
   Durham International Boundaries Research Unit) provides exact
   dates and area numbers and is the reference-work citation the
   polity page was waiting for. Status moved from `draft` to
   `reviewed`.
2. `oq-territorial-stability` — Biger's direct 1867→1995
   "no changes in the boundary line" statement (p.239) is the
   academic confirmation of territorial continuity the WHEP
   polity-definition rule requires. The 1839–1867 period is
   covered by the 1839 treaty itself. The WWI and WWII
   occupations interrupted sovereignty but did not alter borders,
   which is why the row remains unbroken.

**Three new facts added to the polity page:**

1. **Exact date of the partition: 19 April 1839** (Biger p.70).
   Previously the page had only the year.
2. **Area numbers: 998 / 2,700 sq mi** — Luxembourg retained ~37%
   of its prior territory. Previously the page had only
   Wikipedia's "geographically larger western part".
3. **1848 as "independent in its own right"** (Biger p.239). A
   novel date not in Wikipedia or COW. Biger places Luxembourg's
   full legal independence at the 1848 constitutional settlement,
   distinct from 1839 (territorial partition) and 1867
   (international-boundary status). Under the WHEP polity
   definition this is a regime change, not a territorial change,
   and does not trigger a split — but it is worth citing.

**One loose-dating note to flag:** Biger writes "severance of
the German Confederation in 1867" (p.239), but the German
Confederation was formally dissolved on 23 August 1866 by the
Peace of Prague; the 1867 event was the Treaty of London (the
Luxembourg Crisis resolution) that withdrew the Prussian garrison
and guaranteed neutrality. Biger's year-level claim is close but
slightly loose on mechanism. Recorded on the polity page and in
the Biger source file's known-limitations section so future
citations are cautious with Biger's narrative phrasing.

**Open questions still open:** `oq-polygon-provenance` (pre-1886
polygon source), `oq-cshapes-1893-start` (CShapes package
internals), `oq-bleu-faostat` (FAOSTAT aggregate convention).
Biger does not address any of these directly; they need
different sources (polygon pipeline inspection, cshapes R
package code, FAOSTAT documentation).

**Status change:** `lux-1839-2025` is now the first and only
page in the wiki at `status: reviewed`.

---

<a id="github-clickable-links"></a>
## 2026-04-11 — github-clickable-links
**Touched:** wiki/README.md, wiki/polities/_template.md, wiki/prompts/lint.md
  (prior), all polity pages, all source files, wiki/log.md, wiki/index.md
**Source:** none
**Kind:** decision

User feedback: `[[wikilinks]]`, bare `[oq-slug]`, and backticked
citations like `` `[cshapes-2.0 §scope]` `` do not render as
clickable links on GitHub. The first is Obsidian-specific syntax;
the second is a markdown reference link with no definition
(renders as literal text); the third is a code span that breaks
the link machinery entirely.

**Decision:** the wiki now uses **reference-style** markdown links
throughout. Citation identifiers keep the same `[source-slug
§section]` inline form — so grep-based search and lint still
match them — but each file has a reference-definitions block at
the bottom mapping every label to a real URL. Stable IDs
(log-entry slugs, source-file section anchors) are created with
explicit `<a id="slug"></a>` anchors so the URL targets don't
depend on GitHub's heading slugifier, which mangles em-dashes and
other characters. Open questions are now H3 headings
(`### oq-slug`) because GitHub's auto-generated anchor from clean
kebab-case heading text is already good.

**Applied in this touch-up:**

1. **Schema** (`wiki/README.md`): added a *Cross-reference
   conventions* section describing the reference-style pattern,
   the `<a id>` anchor convention, and the rule that citations
   must never be wrapped in backticks.
2. **Template** (`wiki/polities/_template.md`): rewritten to show
   the new pattern end-to-end, including a reference-definitions
   block at the bottom.
3. **Source files** (5 files): added `<a id="slug"></a>` before
   every `### §section` heading so cross-source and
   polity-to-source links can target them. Wikipedia source files
   (`wikipedia-luxembourg-2026-04-11`, `wikipedia-ottoman-2026-04-11`)
   also got inline `<a id="YEAR"></a>` anchors before each
   `§YEAR` bullet so polity pages can cite `§1878`, `§1908`, etc.
   as clickable fragments. Year-range anchors use ASCII hyphens
   (`1877-1878`) even when the bullet text shows an en-dash
   (`§1877–1878`), because anchor IDs must be ASCII.
4. **Log file** (`wiki/log.md`): added `<a id="slug"></a>` before
   every `## YYYY-MM-DD — slug` entry heading. 12 entries
   anchored.
5. **Polity pages** (4 files, Luxembourg + 3 Ottoman):
   - Removed backticks from inline citations.
   - Converted `[[slug]]` wikilinks to `[slug]` reference form.
   - Normalized log refs `[log YYYY-MM-DD — slug]` →
     `[log slug]` (the date is noise — the slug is stable).
   - Converted *Open questions* section from bullets with bold
     prefixes to H3 subheadings (`### oq-slug`) so GitHub
     auto-generates a clean anchor per question.
   - Appended a reference-definitions block at the bottom of
     each file, sorted, with one line per cited label.
   - Dangling refs (polity pages that don't exist yet:
     `nld-1800-1830`, `tur-1913-1914`, `sau-1924-1932`) are
     defined as clickable links to their future file paths. On
     GitHub these render as clickable 404s, which is better than
     literal `[text]` because the reader can see where the link
     *will* go.
6. **Index** (`wiki/index.md`): every polity and source entry is
   now a proper `[name](path.md)` inline link; source list
   entries include "Cited by:" lists with links to each citing
   polity page.

**Verification:** a script walked every polity and source file,
extracted all `[label]` bracket patterns, and checked each
against the corresponding `[label]: url` definitions. All
reference-style links resolve. The only remaining bracket
patterns with no definition are literal polity codes like
`[BOS-1878-1908]`, which are deliberately not links (they are
CSV identifiers, not wiki references).

**Not converted, intentionally:**

- `log.md` body text still has inline `` `slug` `` backticked
  references to other log entries. These are meta (the log
  talking about itself) and aren't expected to be clickable.
  If they ever need to be, a follow-up pass can add a
  reference-definitions block at the bottom of `log.md`.
- `wiki/prompts/*` and `wiki/README.md` don't use citations
  at all — they describe the system, they don't participate in
  it. No conversion needed.

---

<a id="ottoman-first-ingest"></a>
## 2026-04-11 — ottoman-first-ingest
**Touched:** OTT-1800-1886, OTT-1886-1908, OTT-1908-1912
**Source:** cliopatria-v0.1.3 (new), wikipedia-ottoman-2026-04-11 (new), cshapes-2.0, cow-state-system-v2024
**Kind:** ingest

First Ottoman batch ingest. Creates three polity pages and two new
source files.

**New sources:**

- `wiki/sources/cliopatria-v0.1.3.md` — docs-derived source file for
  Cliopatria v0.1.3 (Seshat Global History Databank), CC BY 4.0,
  ~1,600 polities, 15,690 features, 3400 BCE–2024 CE. Records the
  single-time-step extraction pattern the WHEP pipeline uses
  (`docs/06 §Ottoman entries` literally says "~2% temporal
  coverage"), the ~25–100 km spatial precision, and the list of
  10 WHEP rows that currently use Cliopatria polygons.
- `wiki/sources/wikipedia-ottoman-2026-04-11.md` — combined
  snapshot of two Wikipedia articles:
  `Decline_and_modernization_of_the_Ottoman_Empire` (1800–1908)
  and `Dissolution_of_the_Ottoman_Empire` (1908–1923). Verbatim
  quotes for 1821, 1829, 1831–1833, 1853–1856, 1877–1878, 1878
  (Congress of Berlin), 1908, 1911–1912 (Libya), 1912–1913
  (Balkan Wars), 1913, 1920 (Sèvres), 1922 (sultanate
  abolition). Several 19th-century dates (1830 Greek/Algeria,
  1881 Tunisia, 1882 Egypt, 1885 Eastern Rumelia) could not be
  pinned to verbatim quotes in the current Wikipedia snapshots
  and are listed under the source's *Known limitations* for a
  future ingest.

**New polity pages:**

- `wiki/polities/ott-1800-1886.md` — the anchoring page. Uses
  Cliopatria as polygon source (single 1800 time-step applied
  across 87 years) and CShapes is explicitly outside its
  coverage window. Flags the most important audit finding of
  this ingest: the 1886 split with OTT-1886-1908 is a
  **polygon-source boundary, not a territorial event** — see
  `oq-1886-split-is-polygon-not-territory`. Also flags the
  possibility of further splits at 1830 and 1878 under a strict
  reading of `decision-whep-polity-definition`.
- `wiki/polities/ott-1886-1908.md` — CShapes polygon, captures
  the post-1878 Berlin Congress configuration. Ends at 1908
  (Austro-Hungarian formal annexation of Bosnia + Bulgarian
  independence + Cretan union with Greece — three real events
  on 5 October 1908). Flags `oq-bosnia-double-count`: is Bosnia
  in or out of the Ottoman polygon for 1886–1908, given that a
  separate `BOS-1878-1908` WHEP row also has a polygon?
- `wiki/polities/ott-1908-1912.md` — short four-year terminal
  row. Both endpoints are real events (1908 Bosnia annexation,
  1912 Treaty of Ouchy / Italo-Turkish War end). Flags
  `oq-libya-mid-row-change`: the Libya loss of November 1912
  falls inside the row, which should trigger a split under a
  strict WHEP rule — but the row is short enough that the repo
  apparently chose not to. Also flags `oq-1912-1920-gap`: there
  is no OTT-* row between 1912 and the TUR-* chain; the Balkan
  Wars through WWI to the Republic of Türkiye are all carried
  under TUR codes. The OTT→TUR rename at 1913 is not a
  split-under-the-rule; it should be justified in a separate
  `decision` entry.

**COW finding on this ingest.** COW's `statelist2024.csv` has a
**single continuous tenure row** for `TUR, 640, 1816-01-01 →
2024-12-31`. COW makes no distinction between the Ottoman Empire
and modern Türkiye, and no split at 1886, 1908, 1912, 1922, or
1923. WHEP carries **seven** rows for the same territorial
entity (OTT-1800-1886, OTT-1886-1908, OTT-1908-1912, TUR-1913-1914,
TUR-1914-1918, TUR-1918-1920, TUR-1920-2025) plus a duplicate
`TUR-1800-1912` (see the separate proposal entry). The contrast
is sharp: COW sees one continuous state for 209 years; WHEP sees
seven (eight with the duplicate) in the same window. Under
`decision-whep-polity-definition` the WHEP approach is correct
*in principle* — WHEP's unit of analysis is territorial-economic,
not state-system — but the individual split dates need to be
audited against real territorial change, which this ingest has
now made possible.

Status: all three pages `draft` pending (a) a proper academic
source for the 19th-century events Wikipedia did not give
verbatim quotes for and (b) resolution of the
`oq-1886-split-is-polygon-not-territory` question, which is
bigger than Luxembourg's draft→reviewed blocker because it
affects the split dates themselves, not just the narrative layer.

<a id="proposal-tur-1800-1912-duplication"></a>
## 2026-04-11 — proposal-tur-1800-1912-duplication
**Touched:** TUR-1800-1912 (CSV), OTT-1800-1886, OTT-1886-1908, OTT-1908-1912
**Source:** none
**Kind:** proposal

The CSV contains a row `TUR-1800-1912, Türkiye (to 1912)`
spanning exactly the same entity and time range as the three
`OTT-*` rows that were added when `OTT-1800-1912` was converted
to an aggregate (see `docs/06 §Split Ottoman Empire`). The TUR
row was not removed at that time.

**Observed in the CSV today (`data/final/polities_database.csv`):**

| row | start | end | polity_type | polygon source |
|---|---|---|---|---|
| `OTT-1800-1886` | 1800 | 1886 | national | Cliopatria (1800-1802, 2.66M km²) |
| `OTT-1886-1908` | 1886 | 1908 | national | CShapes 2.0 |
| `OTT-1908-1912` | 1908 | 1912 | national | CShapes 2.0 |
| `TUR-1800-1912` | 1800 | 1912 | national | CShapes 2.0 + CShapes-Europe |

All four rows have `cow=640`. The three OTT rows carry
substantive notes; TUR-1800-1912 has `notes = NA`. The OTT
chain's predecessor/successor links (`NA` → `OTT-1800-1886` →
`OTT-1886-1908` → `OTT-1908-1912` → `TUR-1913-1914;SAU-1924-1932`)
do **not** pass through `TUR-1800-1912` at all — it's a
disconnected node.

**Under the WHEP polity definition**
`[log 2026-04-11 decision-whep-polity-definition]`, the same
territory + same (COW-continuous) entity should be represented
by exactly one polity for any given year. 1800–1912 is currently
represented by **two parallel WHEP polities** — the OTT chain
and the orphan TUR row — which is a direct integrity violation.

**Recommendation (for the user to apply):**

Remove `TUR-1800-1912` from the CSV. The OTT chain is clearly
the live representation (substantive notes, proper
predecessor/successor links, more recent changes). Any references
to `TUR-1800-1912` elsewhere in the CSV or in downstream scripts
need to be repointed at the correct OTT row for the year in
question — a quick grep on `TUR-1800-1912` across `R/`,
`data/whep-source/`, and `data/analysis/` should enumerate them.

The wiki cannot make this change (wiki never edits
`data/final/polities_database.csv` directly per the rules in
`wiki/README.md`). This entry is filed so a human sees it next
time they look at the log.

---

<a id="schema-stable-oq-ids-and-lint-relaxation"></a>
## 2026-04-11 — schema-stable-oq-ids-and-lint-relaxation
**Touched:** wiki/README.md, wiki/prompts/lint.md, wiki/polities/_template.md
**Source:** none
**Kind:** decision

Two meta-changes to the wiki itself, motivated by findings in the
first lint run (`lint-luxembourg`):

1. **Open questions now use stable slug IDs.** Previously numbered
   (`open question 5`), which broke every cross-reference whenever
   a question was resolved and the list renumbered. New rule (in
   `wiki/README.md §Page schema`): each open question starts with
   `**oq-<short-kebab-case>**` and cross-references anywhere on the
   page must use the slug, e.g. "see [oq-polygon-provenance]".
   Resolved questions are struck through and left in place as
   stable anchors rather than deleted.
2. **Lint rule is now split into allowed/forbidden lists.** The
   previous rule ("do not edit polity page content during a lint
   run, lint fixes frontmatter, the index, and the log — not
   claims") was too coarse: it blocked obvious navigation repairs
   like "see open question 6" pointing at a question that doesn't
   exist, and it blocked typo fixes. New rule (in
   `wiki/prompts/lint.md §What lint is allowed to edit`):
   - **Allowed:** frontmatter, index, log, typos, broken internal
     cross-references (repoint or TODO-comment + flag).
   - **Forbidden:** adding/rewording *Sourced claims*, editing
     *Summary*/*Territorial extent*/*Contradictions*/*Decisions*
     body text, changing `sources:`, editing source files, editing
     README.md or any prompt.
   - The dividing line: lint repairs **navigation, formatting,
     indexing**; only ingest changes **what the page claims**.

Template updated (`wiki/polities/_template.md`) to show the new
open-question format with an example slug. Existing Luxembourg
page will be migrated to the new format in the immediately-following
`lux-post-lint-cleanup` ingest.

<a id="lux-post-lint-cleanup"></a>
## 2026-04-11 — lux-post-lint-cleanup
**Touched:** LUX-1839-2025
**Source:** none (claim updates draw on sources already ingested)
**Kind:** ingest

Applies the findings of the `lint-luxembourg` run. Everything lint
flagged but was forbidden from touching.

**Navigation / typo fixes** (would now be allowed under the relaxed
lint rule, but bundled here for atomicity):

- Fixed typo `"CShapES"` → `"CShapes"` in *Territorial extent*.
- Migrated *Open questions* from the old 1–5 numbered format to
  stable slug IDs: `oq-polygon-provenance`,
  `oq-territorial-stability`, `oq-academic-corroboration`,
  `oq-cshapes-1893-start`, `oq-bleu-faostat`. Renamed
  "CShapes 1886–1892 gap narrowed" to the less misleading "Why
  CShapes's first Luxembourg row starts 1893-01-01".
- Repointed the two broken cross-references in *Territorial extent*:
  the 1839–1885 polygon note now points at
  `[oq-polygon-provenance]`, and the old "see open question 6"
  pointer is gone entirely (its content is now a sourced-claim
  statement of resolution, not an open question).

**Claim updates** (these are why this is an `ingest`, not a `lint`):

- Rewrote the *CShapes version coding* paragraph in *Territorial
  extent*. The old text said WHEP "does not record which CShapes
  version was loaded" and framed the COW/GW choice as an open
  question. The new text states the resolution: WHEP loads the
  COW variant, confirmed by schema inspection and by bit-equivalent
  regeneration from `cshp(useGW = FALSE, dependencies = TRUE)`,
  with forward references to the two `log.md` entries that
  established it (`decision-cshapes-is-cow-based` and
  `cshapes-reproducibility-verified`).
- Rebuilt the *Decisions* section. Previously a single stub entry
  for the first ingest; now lists all eight `log.md` entries that
  touched this page or established a rule affecting it, newest
  first, with ★ marking the two repo-wide `decision`-kind rules.
  The new rationale for keeping the page at `status: draft` is
  linked to `[oq-academic-corroboration]` — needs at least one
  academic or reference-work source for the 1839 territorial
  event before it can move to `reviewed`.

No changes to `sources:`, frontmatter (other than already-current
`last_ingest`), or any source file. Status stays `draft`.

---

<a id="lint-luxembourg"></a>
## 2026-04-11 — lint-luxembourg
**Touched:** LUX-1839-2025 (report only), wiki/index.md (auto-applied)
**Source:** none
**Kind:** lint

First lint run on the wiki, scoped to the single Luxembourg page plus
the shared infrastructure it depends on. Executed `wiki/prompts/lint.md`.

**Summary:**

| check | result |
|---|---|
| Schema conformance | PASS — all 10 required frontmatter fields and all 7 required H2 sections present. |
| CSV ↔ wiki parity | PASS — `LUX-1839-2025` exists in `data/final/polities_database.csv:410`. `F15-1800-1999` (Belgium-Luxembourg aggregate) exists and is correctly flagged on the page as a separate row that must not be conflated. No orphan polity pages. |
| Citation health | PASS — 10 `Sourced claims` bullets, every one cited. 1 pure `[database]` bullet (10%), far below the 50% threshold that would flag the page for re-ingest. |
| Contradiction backlog | PASS — section is empty by design with an explanatory note; nothing sitting >90 days. |
| Staleness | PASS — `last_ingest: 2026-04-11` is today. |
| Index freshness | Auto-fixed (see below). |
| Source reachability | PASS — all 3 sources (`cshapes-2.0`, `cow-state-system-v2024`, `wikipedia-luxembourg-2026-04-11`) are cited by Luxembourg; no zero-citation sources. |

**Must fix (body-text issues, not auto-applied per lint rule):**

1. **Broken internal cross-reference, line 52**: *Territorial extent*
   says "See open question 5" for pre-1886 polygon provenance, but
   that question is now **open question 1** after a renumbering. The
   reference points at the wrong bullet (currently BLEU vs F15).
2. **Broken internal cross-reference, line 76**: *Territorial
   extent* says "see open question 6", but there is no open question
   6 (the list has only 5 entries after the same renumbering).
3. **Typo, line 64**: `"silently absent from CShapES."` — should be
   `"CShapes"`. Inside a lint rule, so grep will find it.

**Should review (claim-level drift, not auto-applied):**

4. **Stale "COW vs GW coding" paragraph, lines 71–76.** The page
   text says "The repo's CSV records COW code 212 for Luxembourg
   but does not record which CShapes version was loaded" and tells
   the reader to see open question 6. Both halves are outdated:
   `log.md 2026-04-11 decision-cshapes-is-cow-based` and
   `cshapes-reproducibility-verified` resolved this definitively
   (COW, bit-equivalent to `cshp(useGW=FALSE, dependencies=TRUE)`),
   and `R/00b_fetch_cshapes.R` now records the convention in code.
   The paragraph should be rewritten to state the resolution
   instead of asking the question.
5. **Decisions section is under-populated.** Currently lists only
   `lux-first-ingest`. Should also reference, in rough order of
   relevance to this page:
   - `log 2026-04-11 — decision-whep-polity-definition` (the rule
     that lets Luxembourg start in 1839)
   - `log 2026-04-11 — decision-cshapes-is-cow-based` (the rule
     behind which CShapes timeline applies)
   - `log 2026-04-11 — cshapes-primary-source-upgrade`
   - `log 2026-04-11 — cshapes-reproducibility-verified`
   - `log 2026-04-11 — cow-state-system-v2024-ingest`
6. **Decisions rationale is stale.** The `lux-first-ingest` entry
   says "Status remains `draft` because the narrative layer rests
   on a single tertiary source." Still true (Wikipedia is the only
   narrative source), but the entry doesn't mention that two more
   ingests happened the same day. A fresh rationale: "Remains
   `draft` pending at least one academic or reference-work source
   (Britannica, national history) to corroborate the 1839
   territorial event — see open question 3."

**Auto-applied:**

- `wiki/index.md` — replaced the placeholder
  `"(run \`wc -l data/final/polities_database.csv\`)"` with the
  real row count `1386 (as of 2026-04-11 lint)` under *Coverage →
  Polities in CSV*.
- This log entry.

**Recommendation.** Issues 1–6 are all on the Luxembourg page body,
which the lint rule forbids editing. Apply them manually, or run a
short touch-up ingest that bundles the six fixes into a single
`ingest`-kind log entry (since fix 4 is a claim update, not just a
cross-reference repair, it's better as a real ingest than as a
lint).

---

<a id="cow-state-system-v2024-ingest"></a>
## 2026-04-11 — cow-state-system-v2024-ingest
**Touched:** LUX-1839-2025
**Source:** cow-state-system-v2024 (new)
**Kind:** ingest

Downloaded the Correlates of War State System Membership List v2024
directly from correlatesofwar.org (no authentication needed; public
academic dataset distributed under a citation request, not a
no-redistribute clause). Created `wiki/sources/cow-state-system-v2024.md`
and committed the two core CSVs (`statelist2024.csv`, `system2024.csv`)
under `wiki/sources/data/cow-v2024/` so the wiki is self-contained for
COW claims. Codebook PDF goes to `wiki/sources/pdfs/` which is
gitignored.

Used COW to upgrade three claims on `lux-1839-2025.md`:

1. **Direct citation for Luxembourg's COW state-system dates** (two
   tenure rows, 1920-11-15→1940-05-10 and 1944-09-10→2024-12-31),
   rather than inferring them via CShapes.
2. **Confirms the COW/CShapes alignment** — CShapes's two
   `independent` windows for Luxembourg match COW's two tenure rows
   to the day, which is exactly what the CShapes paper says should
   happen since `useGW=FALSE` loads COW membership as the
   independence criterion.
3. **Narrows (but does not resolve) open question 4** about the
   1893-01-01 CShapes row start. COW does not list Luxembourg until
   1920, so the 1893 row start is NOT a COW membership transition
   (my earlier guess was wrong). It must come from CShapes's
   dependency-tracking sources — the Territorial Change Dataset,
   Biger 1995, or Brownlie & Burns 1979. Full resolution would need
   another source ingest or inspection of the cshapes package
   internals.

Also recorded a small but useful finding for any future COW citation:
COW has revised start dates between vintages (the codebook p.3–4
lists a v2004.1 change moving Brazil's start from 1826-01-01 to
1822-09-07, Afghanistan from 1920 to 1919, Panama from 1920 to 1903).
Any wiki page citing `[cow-state-system-v2024]` is citing v2024
specifically — later COW vintages are a new source file, not an
edit.

---

<a id="cshapes-reproducibility-verified"></a>
## 2026-04-11 — cshapes-reproducibility-verified
**Touched:** (none — verification only)
**Source:** cshapes-2.0
**Kind:** lint

Resolved the provenance gap noted in the earlier
`decision-cshapes-is-cow-based` entry. Installed `cshapes` R package
v2.0 into a scratch library (`/tmp/rlib_cshapes`, not `renv/`) and
ran `cshp(useGW = FALSE, dependencies = TRUE)`, then compared the
output against `data/geodata/cshapes2_full.gpkg`:

- 805 rows in both.
- Identical column set, no `gwcode`.
- All (cowcode, country_name, start, end, status) tuples identical
  after sorting.
- All 805 geometries `st_equals`-identical.

Conclusion: the on-disk gpkg is bit-equivalent in content to the
R package default for `useGW=FALSE, dependencies=TRUE`. This means:

1. The COW finding stands — the R call literally specifies it.
2. The 1893 Luxembourg start is canonical to cshapes 2.0, not a
   local artefact. (Open question 4 on `lux-1839-2025` therefore
   becomes a question about `cshapes` upstream, not about WHEP.)
3. Anyone can regenerate the file deterministically, so lint runs
   do not have to trust the file's provenance.

Recommendation for a future repo change (not applied here — wiki
does not edit pipeline code): add `R/00b_fetch_cshapes.R` with

```r
library(cshapes); library(sf)
cs <- cshp(useGW = FALSE, dependencies = TRUE)
st_write(cs, file.path(geodata_dir, "cshapes2_full.gpkg"),
         delete_dsn = TRUE)
```

and correct `REPRODUCIBILITY.md:162` to point at it. Also add
`cshapes` to `renv.lock`.

<a id="decision-whep-polity-definition"></a>
## 2026-04-11 — decision-whep-polity-definition
**Touched:** (repo-wide; the definition of what a WHEP polity is)
**Source:** none (stated by the project maintainer in conversation)
**Kind:** decision

Records the WHEP definition of a polity. This is the most load-bearing
rule in the wiki and should be cited from every polity page whose
start/end year differs from an external source's independence dating.

**Rule.** A WHEP polity is a **territorial-economic unit** with trade
or production data attached, not a Westphalian legal state. Specifically:

1. **Split rule.** A new polity row is created when the territory
   undergoes a *substantial* territorial change. The triggering event
   is the territorial change itself, not the legal/diplomatic status
   of the unit before or after.
2. **Continuity rule.** If the territory remains the same, the polity
   stays a single continuous row across the full window for which
   trade or production data is available, **even across**:
   - regime changes (monarchy → republic, etc.)
   - wartime occupations that do not alter the final borders
   - entry into or exit from personal unions, customs unions, or
     federations, unless those events coincide with a territorial
     change
   - periods when external state-system datasets (COW, GW, CShapes)
     do not list the unit as an independent state
3. **Independence is not the criterion.** If trade or production data
   exists for a territory, it is a WHEP polity regardless of whether
   any external source considers it independent, a dependency, or
   "N/A". Conversely, a legally independent state with no trade data
   attached is not automatically a WHEP polity.

**Why.** WHEP exists to analyze historical trade and production at
the level of stable economic territories. Legal/diplomatic definitions
of statehood (COW's two-major-power rule, population thresholds, etc.)
do not track the right unit for trade analysis: a colony with its own
customs regime and trade statistics is a trade unit even if COW codes
it as a dependency, and a state under military occupation whose
borders did not move is still the same trade unit afterwards.

**How to apply on polity pages.** When the WHEP start/end year differs
from an external source's independence dating, this is not a
contradiction and should NOT be recorded in a page's *Contradictions*
section. Instead:

- Record the WHEP date in *Summary* and cite this decision entry.
- Record the external source's date in *Sourced claims* as a fact
  about that source, with the note that it uses a different
  definition.
- Use *Contradictions* only for disagreements *within the same
  definition*: e.g. two historical atlases giving different dates
  for the same territorial change, or two sources disagreeing on
  whether a transfer of territory actually happened.

**How to apply at ingest time.** Before creating a new polity page
from an ingested source, check whether the source is tracking
state-system membership (COW, GW, Polity V, V-Dem) or territorial
extent (CShapes, Euratlas, Cliopatria, historical atlases). Only the
second category can justify a *split* in a WHEP polity. The first
category can inform *Sourced claims* about regime type and diplomatic
status but must not drive start/end years.

**Open sub-question.** The rule says "substantial" territorial change
without quantifying it. CShapes uses a 100 × 100 km threshold
`[cshapes-2.0 §coding-changes]`; WHEP does not have a written
threshold. A future `decision` entry should pick a WHEP-specific
threshold or explicitly defer to case-by-case judgement. For now,
existing splits in the CSV stand as precedent.

<a id="decision-cshapes-is-cow-based"></a>
## 2026-04-11 — decision-cshapes-is-cow-based
**Touched:** (repo-wide; applies to every CShapes-citing polity)
**Source:** cshapes-2.0
**Kind:** decision

Resolves open question #6 on `lux-1839-2025` and establishes a repo-wide
convention: **WHEP uses the COW-based version of CShapes 2.0**.

Evidence (direct inspection of `data/geodata/cshapes2_full.gpkg`):

1. **Schema.** The `cshapes` layer contains `cowcode` but no `gwcode`
   column. The paper notes both columns are typically present
   `[cshapes-2.0 §coding-dependencies]`; the absence of `gwcode` here
   is consistent with the COW-only distribution.
2. **Canada acid test.** The paper explicitly names Canada as the
   case that distinguishes the two versions: COW sets independence
   to 1920, GW to 1867 `[cshapes-2.0 §coding-states]`. Our gpkg has
   three Canada rows with `cowcode=20`: 1886-01-01 to 1920-01-09 as
   `colony`, 1920-01-10 to 1948-07-21 as `independent`, and
   1948-07-22 to 2019-12-31 as `independent`. The 1920-01-10 transition
   matches the COW date exactly; the GW 1867 date does not appear.

Provenance caveat: I could not find the R code that actually *writes*
`cshapes2_full.gpkg`. `REPRODUCIBILITY.md` attributes it to R/01, but
R/01 only reads a pre-existing `cshapes.csv` from `data/whep-source/`
— it does not call `cshapes::cshp()` and does not write any gpkg.
Either the gpkg was built by a one-off script not checked in, by a
prior pipeline version, or was downloaded directly from ETH Zurich.
Worth flagging as a reproducibility gap in a future log entry; the
COW finding stands regardless because it is a property of the data
actually on disk.

**Consequence:** every polity page that cites CShapes implicitly
cites the **COW-based** version. Polity start years derived from
`[cshapes-2.0]` must be read against COW's independence criteria
(diplomatic ties to two major powers, population threshold, etc.),
not GW's. For polities that are well-known as COW/GW edge cases
(Canada, Luxembourg, several Central American states before WWII,
possibly Tibet and Orange Free State which GW includes and COW does
not), the page must either note this in Contradictions or justify
the WHEP start year from a non-CShapes source.

<a id="cshapes-primary-source-upgrade"></a>
## 2026-04-11 — cshapes-primary-source-upgrade
**Touched:** LUX-1839-2025
**Source:** cshapes-2.0 (upgraded)
**Kind:** ingest

User downloaded the CShapes 2.0 paper (Schvitz et al. 2022, JCR 66(1))
to `wiki/sources/pdfs/` under institutional access. Rewrote
`wiki/sources/cshapes-2.0.md` from a docs-derived stub (citing
`docs/04` and `docs/06` second-hand) into a primary-source file with
page-anchored verbatim quotes, DOI, and PDF SHA-256 for verification.

Added `wiki/sources/pdfs/` to `.gitignore` with a README explaining
why: PDFs are copyrighted, not redistributable, and the source file
plus hash is sufficient provenance.

Five material facts from the paper that the previous docs-derived
stub did not have:

1. CShapes ships in **two versions** (COW-based and GW-based) that
   differ on pre-1945 independence dates. Canada is 1920 under COW,
   1867 under GW. The repo does not record which version it loaded.
2. Border adjustments smaller than **100 × 100 km** are excluded by
   design. 138 transfers in the Territorial Change Dataset are
   silently dropped, including the 1922 Silesia Plebiscite (9,702 km²)
   and the 1929 Peru-Chile treaty (8,498 km²). Lint rule: any WHEP
   polity hinging on a sub-threshold transfer cannot cite CShapes.
3. Dependencies with population under **250,000** are excluded.
4. **Disputed territories** are assigned to the de facto controller,
   not coded separately. De facto states (Abkhazia, South Ossetia,
   Biafra, RSK) have no CShapes polygon of their own.
5. **Backdated borders** — 152 of 249 units have a single polygon
   copied across 1886–2019. The "1886 polygon" is literally the same
   geometry as the 2019 polygon for those countries.

Corrected a guessed author-list ordering in the previous stub. The
actual byline is Schvitz, Girardin, Rüegger, Weidmann, Cederman,
Gleditsch. The stub had them in a different order — a small reminder
that docs-derived source files can silently carry errors the primary
source would have caught.

Updated `wiki/polities/lux-1839-2025.md` to cite specific CShapes
paper sections (§scope, §coding-states, §coding-changes, §geocoding)
instead of generic `[cshapes-2.0]` tags, and added a sixth open
question about which CShapes version (COW or GW) the repo loads.
Status remains `draft`.

<a id="lux-first-ingest"></a>
## 2026-04-11 — lux-first-ingest
**Touched:** LUX-1839-2025
**Source:** cshapes-2.0, wikipedia-luxembourg-2026-04-11
**Kind:** ingest

First real two-source ingest for the wiki. Created `wiki/sources/cshapes-2.0.md`
(polygon/border evidence, derived from `docs/04_POLYGON_SOURCES.md` and
`docs/06_KNOWN_ISSUES_AND_DECISIONS.md` — no external fetch) and
`wiki/sources/wikipedia-luxembourg-2026-04-11.md` (narrative history, verbatim
quotes from the `History_of_Luxembourg` article snapshotted on 2026-04-11).

Rewrote `wiki/polities/lux-1839-2025.md` from skeleton to a fully-cited draft.
Every factual claim now carries an inline citation. Status kept at `draft`
pending academic corroboration (COW / Polity V) — a single tertiary source
is not enough to mark a page `reviewed`.

Five open questions recorded on the page, the most load-bearing being whether
WHEP's general rule for personal unions is consistent with treating Luxembourg
as an independent polity from 1839 despite the personal union with the
Netherlands lasting until 1890. This is a cross-polity question and should
be resolved via a `decision`-kind log entry, not on the Luxembourg page alone.

<a id="wiki-bootstrap"></a>
## 2026-04-11 — wiki-bootstrap
**Touched:** (none)
**Source:** none
**Kind:** decision

Wiki created. Schema and prompts in place. No polity pages yet beyond the
Luxembourg worked example, which is a skeleton to demonstrate the format,
not a reviewed page.
