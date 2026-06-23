export const meta = {
  name: 'polity-autoimprove',
  description: 'Audit -> reconcile -> fix(wiki-first) -> integrate(one commit per issue) loop over the polities DB/wiki. Run after the deterministic 01/02 scripts.',
  phases: [
    { title: 'Audit',     detail: 'one agent per unresolved unit: verdict correct, or emit a typed issue report', model: 'sonnet' },
    { title: 'Reconcile', detail: 'dedupe/merge issue reports into harmonized issues', model: 'sonnet' },
    { title: 'Fix',       detail: 'one agent per harmonized issue (worktree-isolated): wiki-first change-set', model: 'sonnet' },
    { title: 'Integrate', detail: 'serial: apply each change-set, verify, one commit per issue', model: 'sonnet' },
  ],
}
// v1 implementation of pipelines/polity-autoimprove/README.md. Validate with a real run before relying on it.
// args = { repo, findings_path, flagged_path, polities_csv, n_findings, n_flags, max_issues }
const repo          = (args && args.repo) || '/home/usuario/whep-polities'
const findings_path = (args && args.findings_path) || `${repo}/pipelines/polity-autoimprove/state/findings.json`
const flagged_path  = (args && args.flagged_path)  || `${repo}/pipelines/polity-autoimprove/state/territorial_flagged.json`
const polities_csv  = (args && args.polities_csv)  || `${repo}/data/final/polities_database.csv`
const n_findings    = Number(args && args.n_findings) || 0
const n_flags       = Number(args && args.n_flags) || 0
const max_issues    = Number(args && args.max_issues) || 40
const M = { model: 'sonnet', effort: 'medium' }

const RULES = `WHEP rules: wiki is the SOURCE OF TRUTH (polity changes go wiki->DB->polygon). Aggregate polygons (undivided Germany, Japanese Empire, full USSR) are FIRST-CLASS and kept; fix territory by routing data to the polity whose polygon fits / adding a granular polity, NEVER by editing an aggregate. Settle territorial scope from data magnitudes + spatial-containment evidence, not convention.`

const ISSUE = { type:'object', additionalProperties:false, required:['verdict'],
  properties:{ verdict:{type:'string', enum:['correct','issue']},
    issue:{ type:'object', additionalProperties:false,
      properties:{ issue_id:{type:'string'}, type:{type:'string', enum:['rematch_alias','polity_dates','polity_extent_polygon','missing_polity','double_count','data_error']},
        subject_polity:{type:'string'}, subject_label:{type:'string'}, period:{type:'string'},
        description:{type:'string'}, proposed_fix:{type:'string'}, confidence:{type:'string', enum:['high','medium','low']} } } } }
const HARM = { type:'object', additionalProperties:false, required:['harmonized'],
  properties:{ harmonized:{ type:'array', items:{ type:'object', additionalProperties:true, required:['issue_id','type','description'] } } } }
const CHANGESET = { type:'object', additionalProperties:false, required:['issue_id','fix_type','summary'],
  properties:{ issue_id:{type:'string'}, fix_type:{type:'string'}, summary:{type:'string'},
    wiki_path:{type:'string'}, wiki_content:{type:'string'},
    csv_row:{type:'string', description:'a full polities_database.csv row to add, or empty'},
    csv_edit:{type:'string', description:'description of an edit to an existing row, or empty'},
    match_rule_patch:{type:'string', description:'line(s) to add to common_names / match.R, or empty'},
    polygon_decision:{type:'string'}, commit_message:{type:'string'} } }

// ---------- Audit ----------
phase('Audit')
const auditOne = (src, i) => {
  if (budget.total && budget.remaining() < 25_000) return null
  return agent(
    `Audit one WHEP review unit. ${RULES}\nRead the JSON array at ${src} and take element index ${i}. ` +
    `Read ${polities_csv} as needed. Decide: is this data->polity match (and the polity's territory for the period) CORRECT? ` +
    `If yes -> verdict "correct". If not -> verdict "issue" with a typed issue report (issue_id = stable kebab of subject+type, choose type, describe, propose a fix). Use the numeric evidence fields (staple_magnitudes, contained_with_concurrent_data) when present.`,
    { ...M, label:`audit:${src.includes('flagged')?'terr':'find'}:${i}`, phase:'Audit', schema:ISSUE })
}
const auditCalls = [
  ...Array.from({length:n_findings}, (_,i)=>()=>auditOne(findings_path, i)),
  ...Array.from({length:n_flags},   (_,i)=>()=>auditOne(flagged_path, i)),
]
const audited = (await parallel(auditCalls)).filter(Boolean)
const issues = audited.filter(a=>a.verdict==='issue' && a.issue).map(a=>a.issue)
log(`Audit: ${audited.length} units, ${issues.length} issues, ${audited.length-issues.length} correct`)

// ---------- Reconcile ----------
phase('Reconcile')
const recon = await agent(
  `Reconcile these WHEP issue reports into harmonized work units. Merge duplicates and issues touching the same subject; union their evidence; pick ONE fix_type per unit; record supersedes:[ids]. ${RULES}\n\nISSUES:\n${JSON.stringify(issues).slice(0,120000)}`,
  { ...M, label:'reconcile', phase:'Reconcile', schema:HARM })
let harmonized = ((recon && recon.harmonized) || []).slice(0, max_issues)
log(`Reconcile: ${issues.length} issues -> ${harmonized.length} harmonized`)

// ---------- Fix (worktree-isolated; emit change-sets, do NOT commit) ----------
phase('Fix')
const changesets = (await parallel(harmonized.map(h => () => {
  if (budget.total && budget.remaining() < 30_000) return null
  return agent(
    `You are fixing ONE WHEP issue, wiki-first. ${RULES}\nIssue: ${JSON.stringify(h)}\n` +
    `Research the entity, then produce a CHANGE-SET (do NOT commit, do NOT run git): for a polity change, the wiki page content (wiki/polities/<code>.md per the repo's Territorial-extent requirements) + the CSV row/edit + polygon_decision; for rematch_alias, the match_rule_patch only; for data_error, summary only. Provide a one-line commit_message.`,
    { ...M, label:`fix:${h.issue_id}`, phase:'Fix', isolation:'worktree', schema:CHANGESET })
}))).filter(Boolean)
log(`Fix: ${changesets.length} change-sets`)

// ---------- Integrate (SERIAL: one commit per issue) ----------
phase('Integrate')
const applied = []
for (const cs of changesets) {
  const res = await agent(
    `Apply ONE change-set to ${repo} and commit it, then STOP. ${RULES}\nChange-set: ${JSON.stringify(cs)}\n` +
    `Steps: (1) write wiki_content to wiki_path if present; (2) apply csv_row/csv_edit to data/final/polities_database.csv; (3) apply match_rule_patch if present; (4) git add the touched files and 'git commit -m "<commit_message>"' (end the message with the repo's required Co-Authored-By + Claude-Session trailers). Do NOT push. Report the commit hash and files changed. Leave no untracked stray files.`,
    { ...M, label:`integrate:${cs.issue_id}`, phase:'Integrate' })
  applied.push({ issue_id: cs.issue_id, result: res })
}
return {
  units_audited: audited.length,
  correct: audited.length - issues.length,
  issues: issues.length,
  harmonized: harmonized.length,
  changesets: changesets.length,
  committed: applied.length,
  note: 'After this: re-run 01/02 to verify fixes resolved their issues, then update state/review_ledger.csv.',
}
