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

<Borders over time. Cite the polygon source from the CSV. Note years
where the polygon is approximate, inherited from a neighbor, or
back-projected.>

## Predecessors and successors

- **Predecessor:** [other-polity-slug] — nature of the transition
- **Successor:** [other-polity-slug] — nature of the transition

## Sourced claims

- Claim one. [source-slug §section]
- Claim two. [source-slug §section]
- Claim from the CSV with no deeper source yet. [database]

## Contradictions

<If two sources disagree, both positions here, plus which one the
database currently follows and why. Never silently pick.>

## Decisions

- [log slug] one-line summary

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
Reference-style link definitions. Add one line per citation used
above. Same-page anchors use `#oq-...`; cross-page anchors use
`path.md#anchor`.
-->

[source-slug §section]: ../sources/source-slug.md#section
[other-polity-slug]: other-polity-slug.md
[database]: ../../data/final/polities_database.csv
[log slug]: ../log.md#slug
[oq-example-slug]: #oq-example-slug
