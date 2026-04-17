# Lint prompt

Use this periodically (e.g. after a batch of ingests, or monthly) to
check the health of the wiki.

---

You are linting the WHEP polities wiki. Read `wiki/README.md` for the
schema, the coverage goal, and the dual-renderer rule (GitHub +
Obsidian).

**The wiki is the primary source of truth.** The CSV and GeoPackage
under `data/final/` are derived artifacts rebuilt by
`scripts/build_database.py`. Lint never hand-edits them; if they drift
from the wiki, the fix is to re-run the builder, which lint may do.

Walk the whole `wiki/` tree and produce a report.

Check, in order:

1. **Schema conformance.** Every file in `wiki/polities/` (excluding
   `_template.md` and `_aggregates/`) must have the required
   frontmatter fields and the required H2 sections. List violations.

2. **CSV ↔ wiki parity (per-code).** The CSV is regenerated from the
   wiki, so every wiki page must produce exactly one CSV row, matched
   by `polity_code`. The builder already detects count mismatches and
   prints a `✗ ROW COUNT MISMATCH` banner with per-file reasons
   (unreadable YAML frontmatter, missing `polity_code`, duplicate code
   across two files). Lint must:
   - Run `bash scripts/rebuild.sh` and confirm the builder reports
     `Rows written == Wiki pages scanned ✓`.
   - For extra assurance, diff the two code sets explicitly
     (underscore-prefixed files like `_template.md` are excluded by
     the builder and shouldn't be grepped):
     ```bash
     comm -3 \
       <(awk -F, 'NR>1 {print $1}' data/final/polities_database.csv | sort -u) \
       <(grep -h '^polity_code:' wiki/polities/[a-z]*.md | awk '{print $2}' | sort -u)
     ```
     Empty output = clean. Any line in the output is a bug: either a
     CSV row with no wiki page, or a wiki page that failed to produce
     a row. List each code in the report and stop before touching
     other checks — this is the most serious parity violation.

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

8. **Wiki oddity detection** (critical-stance audit, see
   `wiki/README.md`). Scan the wiki's frontmatter and bodies for:
   - **Page labels with entity names incompatible with their time
     range.** Example: a page labeled `USSR (1905-1914)` — USSR did
     not exist until 1922. Look for entity names (USSR, Yugoslavia,
     Czechoslovakia, GDR, etc.) appearing in `polity_name` with
     start dates that predate the entity's founding year.
   - **Overlapping date ranges in the same entity chain.** Group by
     the three-letter prefix of `polity_code` (or by the entity name
     where distinct prefixes refer to the same entity — OTT/TUR,
     DEU/GER). Flag any overlap in `start_year` / `end_year`.
   - **Orphan pages** not reached by any predecessor / successor
     chain: `predecessor: NA` AND no other page lists this code as
     `successor`, AND `start_year > 1800`. Suspect.
   - **Predecessor / successor references to codes with no wiki page.**
   - **Polygon frontmatter issues:**
     - `polygon_source` slug not registered in `scripts/sources.yaml`.
     - `polygon_feature_year` missing on a page whose source has a
       `temporal` block in `sources.yaml`.
     - `polygon_feature_id` missing or empty while `polygon_status:
       assigned`.
     - `polygon_status: missing` with no prose justification in
       `## Territorial extent`.

   For each finding: list the specific `polity_code`(s), explain
   the oddity in one sentence, and recommend a `proposal`-kind
   log entry for human review. Do NOT auto-fix — this is read-only
   auditing.

9. **Coverage-gap detection.** Check for spatiotemporal gaps:
   - Polity pages whose *Predecessors and successors* section has
     `<!-- TODO: page not yet created -->` dangling refs. Count and
     list them — these represent known gaps in the coverage chain.
   - Polity pages with `predecessor: NA` in the prose whose
     `start_year` is after 1800 (the database floor) — where did the
     territory come from?
   - Polity pages whose successor is `NA` but whose `end_year` is
     before 2025 — where did the territory go?
   - Dissolution events (e.g. Austria-Hungary, Ottoman Empire, USSR)
     where the sum of successor states' territory does not plausibly
     account for the parent's territory.

10. **Full rebuild.** Run `bash scripts/rebuild.sh` and inspect the
    report. This rebuilds `data/final/polities_database.{csv,gpkg}`
    and `site/polities.{csv,geojson}` + `site/wiki/` in one step, so
    the derived artifacts always track the current wiki state by the
    end of a lint run.
    - `source not fetched:` lists source slugs whose raw files are
      missing from `data/geodata/`. This isn't a wiki bug — flag for
      the human to run the matching `scripts/sources/<slug>/fetch.*`.
    - `unknown source slug:` points at wiki pages whose
      `polygon_source` isn't in `scripts/sources.yaml`. Must-fix: either
      correct the slug or add the source to `sources.yaml` (the latter
      is script-editing work; log, don't attempt).
    - `feature not found:` points at wiki pages where the declared
      `polygon_feature_id` / `polygon_feature_year` doesn't resolve
      in the raw source. Either the frontmatter is wrong or the source
      changed upstream. Must-fix after investigation.
    - Count wiki pages with `polygon_status: assigned` vs pages where
      the builder actually attached geometry. Any drop is a data bug.

11. **Polygon frontmatter completeness.** Every polity page's YAML
    frontmatter must contain the polygon binding fields
    (`polygon_source`, `polygon_feature_id`, `polygon_feature_year`,
    `polygon_status`, `polygon_area_km2`) and the prose in
    `## Territorial extent` must back them up. Check for:
    - Pages missing any of the five polygon fields. Frontmatter
      schema violations — must-fix.
    - Pages with `polygon_status: assigned` whose
      `## Territorial extent` has boilerplate like "No polygon"
      (contradiction — either frontmatter or prose is wrong).
    - Pages where a proxy polygon is used but the prose doesn't
      explain why the proxy is valid (territory unchanged, etc.).
    - Pages that lack a "Why this entry exists" paragraph entirely.
    - Pages with `polygon_status: missing` and no prose justifying
      the gap.
    Flag all of these as must-fix.

12. **Obsidian compatibility.** The wiki must render and navigate
    correctly in Obsidian. Check for:
    - `<a id="...">` HTML anchors — Obsidian ignores them.
    - Reference-style link definitions (`[ref]: url` at the bottom
      of a file) — Obsidian can't navigate them. All links must be
      inline: `[text](path.md#anchor)`.
    Standard `../` relative paths in inline links are fine.
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
- Running `bash scripts/rebuild.sh` at the end of the lint run so
  `data/final/` and `site/` match the post-lint wiki state. This is
  part of check 10 and should be the final action of every lint
  session that made any frontmatter change.

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
