export const meta = {
  name: 'document-polity-pages',
  description: 'Fill Territorial extent + Sourced claims on undocumented polity pages, citing ONLY sources that exist in wiki/sources/, so the page can earn wiki_status: reviewed.',
  phases: [
    { title: 'Document', detail: 'one agent per page: research from ingested sources + web, rewrite the thin sections', model: 'sonnet' },
    { title: 'Check',    detail: 'deterministic: every citation must resolve; report per-page result', model: 'sonnet' },
  ],
}
// args = { repo?, codes: ["IND-1914-1937", ...] }
//
// Context: 13 pages carried wiki_status "reviewed" with ZERO source citations
// (see wiki/log.md decision-reviewed-status-audit). They are the input the
// assertion-verification pipeline reads when judging data matches, so an
// undocumented page propagates uncertainty into every verdict that touches it.
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {})
const repo = A.repo || '/home/usuario/whep-polities'
const codes = Array.isArray(A.codes) ? A.codes : []
const M = { model: 'sonnet', effort: 'medium' }

const CITATION_RULE = `CITATIONS — THE HARD RULE. You may cite ONLY sources that already exist as files in ${repo}/wiki/sources/. List that directory first and read the ones relevant to your polity. Never invent a source filename: the wiki already contained 17 citations pointing at files that were never ingested, which is worse than no citation because it looks like evidence. Format is inline markdown, [<slug> §<anchor>](../sources/<slug>.md#<anchor>), and the ANCHOR MUST EXIST — it is the heading text lowercased with non-alphanumerics collapsed to hyphens, so "## Key dates" gives #key-dates. Verify each anchor by grepping the source file's headings before you write it. scripts/validate_citations.py will fail the build on any citation that does not resolve, so a fabricated one will be caught, not merely frowned upon. If a claim you want to make has no support in an ingested source, you have three honest options: (a) cite the CShapes/COW data you can read directly from data/geodata/ or data/final/, (b) state the claim and mark it plainly as uncited general history, or (c) leave it out. Do NOT dress up option (c) as a citation.`

const RESULT = { type:'object', additionalProperties:false, required:['polity_code','wrote','citations_added','sources_cited','summary'],
  properties:{ polity_code:{type:'string'}, wrote:{type:'boolean'},
    citations_added:{type:'integer'},
    sources_cited:{type:'array', items:{type:'string'}, description:'the source slugs you actually cited'},
    territorial_changes_found:{type:'array', items:{type:'string'}, description:'territorial changes you identified INSIDE this row\'s span — the thing that decides whether the row should be split'},
    should_split:{type:'boolean', description:'true if you found a territorial change inside the span that warrants splitting the row per the WHEP territorial-change rule'},
    summary:{type:'string'} } }

if (codes.length === 0) log('WARNING: no codes passed; this run is a no-op.')

phase('Document')
const results = (await parallel(codes.map(code => () => agent(
  `Document the WHEP polity page for ${code} so it can honestly earn wiki_status: reviewed. It is currently a stub: it carries no source citations and its territorial sections are unfilled, which is why it was downgraded to draft.\n\n` +
  `${CITATION_RULE}\n\n` +
  `STEPS: (1) read ${repo}/wiki/polities/${code.toLowerCase()}.md and ${repo}/wiki/README.md (page conventions); ` +
  `(2) list and read the relevant files in ${repo}/wiki/sources/ — biger-1995.md is a large per-country boundary reference, cow-state-system-v2024.md has membership dates, cshapes-2.0.md documents the polygon source; ` +
  `(3) read this polity's row in ${repo}/data/final/polities_database.csv for its polygon binding, and you MAY measure its actual geometry from data/final/polities_database.gpkg with geopandas (equal-area CRS ESRI:54034) to state a real area; ` +
  `(4) research the polity's territorial history for its exact span, using the web where the ingested sources are silent; ` +
  `(5) REWRITE the page's "## Territorial extent" and "## Sourced claims" sections with substance and resolvable citations, preserving the frontmatter EXACTLY as it is (do not touch polygon_* fields or status) and keeping every existing section heading; ` +
  `(6) the single most valuable thing you can add: identify any TERRITORIAL CHANGE that happened INSIDE this row's span. That is what decides whether the row should later be split, and it is what the data-matching pipeline needs. Record each one in territorial_changes_found and set should_split accordingly. If borders were genuinely constant, say so explicitly and explain how you know — that is equally useful.\n\n` +
  `Do NOT change wiki_status yourself and do NOT commit. Report what you cited.`,
  { ...M, label:`doc:${code}`, phase:'Document', schema:RESULT })))).filter(Boolean)

log(`Documented ${results.length}/${codes.length}; ${results.filter(r=>r.should_split).length} report an in-span territorial change`)

phase('Check')
await agent(
  `Run the citation gate and report the result verbatim: cd ${repo} && python3 scripts/validate_citations.py ; echo "EXIT=$?"\n` +
  `Then run: python3 scripts/validate_polygons.py 2>&1 | tail -6\n` +
  `Report both outputs exactly. Do NOT fix anything and do NOT commit — just report, so a human sees whether the documentation pass introduced any unresolvable citation.`,
  { ...M, effort:'low', label:'citation-gate', phase:'Check' })

return {
  documented: results.length,
  total_citations: results.reduce((n,r)=>n+(r.citations_added||0),0),
  pages_reporting_in_span_change: results.filter(r=>r.should_split).map(r=>r.polity_code),
  note: 'Citations verified by scripts/validate_citations.py. Review the pages, then promote wiki_status to reviewed for the ones that now deserve it.',
}
