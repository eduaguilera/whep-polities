---
polity_code: XXX-YYYY-YYYY
polity_name: <name>
start_year: 0
end_year: 0
type: national
iso3: NA
cow: NA
status: draft
last_ingest: YYYY-MM-DD
sources: []
---

# <polity_name>

## Summary

<One paragraph. What this polity is, why it's a distinct row, what the
start and end years mean — legal creation, de facto sovereignty,
database truncation, etc. Use reference-style citations throughout,
e.g. [source-slug §section], and define the targets at the bottom
of the file.>

## Territorial extent

**Polygon:** <State the polygon status — one of:>
- `Copied from [CODE](code.md) (justification why this proxy is valid,
  e.g. "territory unchanged at independence")` — when a polygon from
  a neighboring period of the same polity was reused.
- `<Source> (e.g. CShapes 2.0, Cliopatria, GADM)` — when the polygon
  comes directly from a spatial dataset.
- `Not yet assigned. **Proxy deliberately not copied** because
  <reason, with km² numbers showing the territory mismatch>.` — when
  available polygons were considered and rejected.
- `Not yet assigned. No polygon available in the GeoPackage for this
  entity or period.`

**Why this entry exists:** <What input data does this polity capture?
What was it previously matched to, and why was that wrong? What
historical source confirms this was a distinct entity? Include the
data country name, ISO code, year range, and approximate row count.>

<Then describe borders over time. Cite the polygon source from the
CSV. Note years where the polygon is approximate, inherited from a
neighbor, or back-projected. Give approximate km² and describe the
territory in terms a reader can locate on a modern map.>

## Predecessors and successors

Coverage goal: every km² must be accounted for. When this polity
ends, successors must cover all its territory. When it begins,
predecessors must explain where the territory came from. Gaps are
bugs — flag them as open questions.

- **Predecessor:** [other-polity-slug](other-polity-slug.md) — nature of the transition
- **Successor:** [other-polity-slug](other-polity-slug.md) — nature of the transition

## Sourced claims

- Claim one. [source-slug §section](../sources/source-slug.md#section)
- Claim two. [source-slug §section](../sources/source-slug.md#section)
- Claim from the CSV with no deeper source yet. [database](../../data/final/polities_database.csv)

## Contradictions

<If two sources disagree, both positions here, plus which one the
database currently follows and why. Never silently pick.>

## Decisions

- [log slug](../log.md#slug) one-line summary

## Open questions

Each question is an H3 heading `### oq-<slug>`. GitHub auto-generates
the anchor from the heading text, so cross-references elsewhere on
the page resolve. When a question is resolved, do not delete —
replace the body with a pointer to the resolving `log.md` entry so
the slug stays a stable anchor.

### oq-example-slug

Short title for the open question, then body explaining what the
next ingest should try to resolve, why it matters, and what source
or investigation would answer it.

<!--
All links use inline markdown format for GitHub + Obsidian
compatibility: [display text](relative/path.md#anchor).
Do NOT use reference-style link definitions.
-->
