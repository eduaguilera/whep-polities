# Lint prompt

Use this periodically (e.g. after a batch of ingests, or monthly) to
check the health of the wiki.

---

You are linting the WHEP polities wiki. Read `wiki/README.md` for the
schema. Walk the whole `wiki/` tree and produce a report.

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
