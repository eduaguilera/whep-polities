# Lint prompt

Use this periodically (e.g. after a batch of ingests, or monthly) to
check the health of the wiki.

---

You are linting the WHEP polities wiki. Read `wiki/README.md` for the
schema, the coverage goal, and the dual-renderer rule (GitHub +
Obsidian). Walk the whole `wiki/` tree and produce a report.

Check, in order:

1. **Schema conformance.** Every file in `wiki/polities/` (excluding
   `_template.md` and `_aggregates/`) must have the required
   frontmatter fields and the required H2 sections. List violations.

2. **CSV ↔ wiki parity.**
   - For every `polity_code` in `data/final/polities_database.csv`,
     is there a matching `wiki/polities/<slug>.md`? List missing pages.
   - For every polity page, does the `polity_code` still appear in
     the CSV? List orphans (the CSV row may have been removed,
     renamed, or merged — each orphan needs human review).

3. **Citation health.** Every bullet in a *Sourced claims* section
   should end with `[<slug> §...]` or `[database]`. List unsupported
   claims. A page with more than 50% `[database]` bullets is a
   candidate for the next ingest — flag it.

4. **Contradiction backlog.** List every page with a non-empty
   *Contradictions* section whose corresponding `log.md` entry is
   older than 90 days with no follow-up. These are decisions the
   human has been sitting on.

5. **Staleness.** List pages whose `last_ingest` is older than one
   year, grouped by continent.

6. **Index freshness.** Rebuild `wiki/index.md` coverage numbers and
   the continent lists. Diff against the existing index; apply the
   update if the diff is purely additive, otherwise propose it in a
   `lint`-kind log entry.

7. **Source reachability.** For each file in `wiki/sources/`, count
   how many polity pages cite it. Zero-citation sources are
   candidates for deletion — flag, do not delete.

8. **CSV oddity detection** (critical-stance audit, see
   `wiki/README.md`). Scan `data/final/polities_database.csv` for:
   - **Row labels that contain entity names incompatible with their
     time range.** Example pattern: the row labeled `USSR
     (1905-1914)` — USSR did not exist until 1922. Look for entity
     names (USSR, Yugoslavia, Czechoslovakia, German Democratic
     Republic, etc.) that appear in row labels or `polity_name`
     columns with start dates that predate the entity's known
     founding year.
   - **Overlapping rows for the same entity.** Group by the
     three-letter prefix of `polity_code` (or the entity name if
     distinct prefixes refer to the same entity, like OTT and TUR,
     or DEU and GER). Flag any overlap in `start_year` / `end_year`
     ranges.
   - **Orphan rows** not reached by any predecessor / successor
     chain. A row whose `predecessor` is `NA`, whose `polity_code`
     does not appear in any other row's `successor` column, and
     whose `start_year` is after the database floor of 1800 is
     suspect.
   - **Rows with `notes = NA`** where sibling rows in the same
     entity chain have substantive notes.
   - **Entities referenced in `predecessor` / `successor` columns
     that don't exist as rows** in the CSV.

   For each finding: list the specific `polity_code`(s), explain
   the oddity in one sentence, and recommend a `proposal`-kind
   log entry for human review. Do NOT auto-fix — this is read-only
   auditing.

9. **Coverage-gap detection.** Check for spatiotemporal gaps:
   - Polity pages whose *Predecessors and successors* section has
     `<!-- TODO: page not yet created -->` dangling refs. Count and
     list them — these represent known gaps in the coverage chain.
   - Polity pages with `predecessor: NA` whose `start_year` is after
     1800 (the database floor) — where did the territory come from?
   - Polity pages whose successor is `NA` but whose `end_year` is
     before 2025 — where did the territory go?
   - Dissolution events (e.g. Austria-Hungary, Ottoman Empire, USSR)
     where the sum of successor states' territory does not plausibly
     account for the parent's territory.
   - CSV rows that are not reachable via any predecessor/successor
     chain from an existing wiki page.

10. **Obsidian compatibility.** The wiki must render and navigate
    correctly in Obsidian. Check for:
    - `<a id="...">` HTML anchors — Obsidian ignores them.
    - `../` directory prefixes in link URLs — Obsidian can't resolve
      them. All cross-directory links must use filename-only paths
      (e.g. `(cshapes-2.0.md#scope)` not `(../sources/cshapes-2.0.md#scope)`).
    - Reference-style link definitions (`[ref]: url` at the bottom
      of a file) — Obsidian can't navigate them. All links must be
      inline: `[text](file.md#anchor)`.
    Flag any violations as must-fix.

Output format:
- **Summary** — counts for each check.
- **Must fix** — schema violations, CSV/wiki parity breaks.
- **Should review** — contradiction backlog, stale pages, zero-cite
  sources.
- **Auto-applied** — list every edit you made (index refresh, missing
  log entries added) with a one-line justification each.

## What lint is allowed to edit

**Always allowed:**
- Frontmatter on any page
- `wiki/index.md` (coverage numbers, continent lists, source list)
- `wiki/log.md` (append `lint`-kind entries)
- Typos: case, spelling, whitespace (e.g. `CShapES` → `CShapes`)
- **Broken internal cross-references**: when a page says
  `see [oq-foo]` or `see [[some-slug]]` and the target does not
  exist on the page or in the wiki, lint may (a) repoint it to the
  correct stable slug if unambiguous, or (b) replace it with a
  `<!-- TODO: broken ref, was "see open question 6" -->` comment
  and flag it in the report.

**Never allowed during a lint run** — these belong in an
`ingest`-kind operation, not lint:
- Adding, removing, or rewording a *Sourced claims* bullet
- Changing the `Summary`, `Territorial extent`, `Contradictions`,
  or `Decisions` body text (even to "update" a stale paragraph)
- Adding or removing sources from a page's `sources:` frontmatter
- Editing any file in `wiki/sources/`
- Editing `wiki/README.md` (schema changes are human decisions)
- Editing `wiki/prompts/*` (meta-changes are human decisions)

The dividing line: lint may repair **navigation, formatting, and
indexing**; only ingest may change **what the page claims**. If
you're unsure which side a fix falls on, put it under "Should
review" in the report and do not touch the file.
