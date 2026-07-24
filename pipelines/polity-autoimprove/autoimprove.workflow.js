export const meta = {
  name: 'polity-autoimprove',
  description: 'Audit -> reconcile -> fix(wiki-first) -> integrate(one commit per issue) loop over the polities DB/wiki. Run after the deterministic 01/02 scripts.',
  phases: [
    { title: 'Audit',     detail: 'one agent per unresolved unit: verdict correct, or emit a typed issue report', model: 'sonnet' },
    { title: 'Reconcile', detail: 'dedupe/merge issue reports into harmonized issues', model: 'sonnet' },
    { title: 'Fix',       detail: 'one agent per harmonized issue (worktree-isolated): wiki-first change-set', model: 'sonnet' },
    { title: 'Integrate', detail: 'serial: apply each change-set, one commit per issue; then regenerate FAOSTAT routing if any fix was FAOSTAT-origin', model: 'sonnet' },
    { title: 'Verify',    detail: 're-run the matcher; confirm which fixes actually resolved', model: 'sonnet' },
    { title: 'Cleanup',   detail: 'ledger: mark only VERIFIED-resolved fixed; others stay open for retry', model: 'sonnet' },
  ],
}
// v1 implementation of pipelines/polity-autoimprove/README.md. Validate with a real run before relying on it.
// args = { repo, findings_path, flagged_path, polities_csv, n_findings, n_flags, max_audit, max_issues }
//
// USAGE (learned from real convergence runs, 2026-06):
//   * n_findings / n_flags MUST be passed — they are the row counts of
//     state/findings.json and state/territorial_flagged.json (this sandbox has no
//     filesystem, so the script can't count them itself). They default to 0, so an
//     arg-less run is a SILENT NO-OP. Compute the counts before launching.
//   * To push COVERAGE (one data point -> one polity), pass n_flags=0 and audit only
//     findings (name_unresolved / coverage_gap -> aliases & new polities). Territorial
//     flags fix EXTENT, not coverage% — run those in a separate pass.
//   * Keep max_audit CLOSE TO max_issues. Auditing many more than you fix just
//     re-audits the deferred issues on the next run (wasted tokens); only `correct`
//     verdicts get banked in the ledger. A clean chunk is ~ max_audit 50 / max_issues 35,
//     repeated (each run's audit set shrinks as the ledger marks units resolved).
//   * FAOSTAT-era findings (origin 'faostat', from pipelines/faostat-era-matching
//     via 01's Stage 1b) are audited alongside Layer-B ones. They are fixed by a
//     NEW POLITY (wiki+CSV) or a match.R route (manual_prefix / manual_span_routes),
//     NEVER by an applied_aliases.csv row. Integrate re-runs faostat-era-matching/
//     match.R to regenerate routing, so Verify needs the WHEP pins cache (WHEP_REPO)
//     to confirm FAOSTAT fixes; without pins those fixes stay open for the next run.
// NOTE: the Workflow runtime delivers `args` as a JSON STRING, not an object — parse it.
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {})
const repo          = A.repo || '/home/usuario/whep-polities'
const findings_path = A.findings_path || `${repo}/pipelines/polity-autoimprove/state/findings.json`
const flagged_path  = A.flagged_path  || `${repo}/pipelines/polity-autoimprove/state/territorial_flagged.json`
const polities_csv  = A.polities_csv  || `${repo}/data/final/polities_database.csv`
const n_findings    = Number(A.n_findings) || 0
const n_flags       = Number(A.n_flags) || 0
const max_issues    = Number(A.max_issues) || 40
const max_audit     = Number(A.max_audit) || (n_findings + n_flags)  // bound per-run audit; default = all remaining
const M = { model: 'sonnet', effort: 'medium' }

// How to fix a FAOSTAT-era finding (origin 'faostat'). These are area-code
// driven: pipelines/faostat-era-matching/match.R regenerates every
// source=faostat row in applied_aliases.csv (replace-by-source) and ignores
// hand-added aliases, so NEVER fix one by appending an alias_row.
const FAOSTAT_FIX = `FAOSTAT-era fix rules (origin 'faostat'): do NOT emit alias_row and do NOT touch applied_aliases.csv — match.R regenerates all source=faostat rows and would wipe it. Fix it one of two ways: (missing_polity) add the polity wiki page + CSV row as usual — match.R's iso3-family lookup routes the area automatically; (faostat_route) emit match_r_patch: either a manual_prefix entry "<area_code>" = "<POLITY_PREFIX>" (when an existing polity chain under a different prefix should own the area, e.g. 7->ANG) OR a manual_span_routes row (area_code, year_start, year_end, target_polity_code, route_basis) to disambiguate OVERLAPPING polity periods, with route_basis grounded in DATA MAGNITUDES (e.g. a production step-change at accession), added to pipelines/faostat-era-matching/match.R.`

const RULES = `WHEP rules: wiki is the SOURCE OF TRUTH (polity changes go wiki->DB->polygon). Aggregate polygons (undivided Germany, Japanese Empire, full USSR) are FIRST-CLASS and kept; fix territory by routing data to the polity whose polygon fits / adding a granular polity, NEVER by editing an aggregate. Settle territorial scope from data magnitudes + spatial-containment evidence, not convention. A polygon represents ONLY its vintage year: NEVER assume a polity's territory was identical in other years of its span. If borders changed within the span (annexations/cessions — e.g. Cape Colony expanded through the 1800s), recommend SPLITTING the polity at the border-change years (each period its own polygon), or, if no polygon is available, DOCUMENT the approximation on the wiki page (direction + rough magnitude). A polygon_vintage_drift flag means data is matched far from the polygon's vintage — treat as a real extent question, not 'correct'. CRITICAL: a SUB-TERRITORY's data must NOT be matched UP to its parent empire/aggregate polity. E.g. 'czech republic'/Bohemia 1910 is a CROWNLAND of Austria-Hungary (~80k km2), NOT the whole empire (~600k km2) — mapping it to the AUH polity overstates ~7x; likewise Slovakia/Croatia/Galicia are NOT all of Austria-Hungary, and Finland/Poland/Baltics are NOT all of the Russian Empire. Match each label to the polity whose territory EQUALS what the data measures; the magnitudes are the tell (a crownland's production is a small fraction of the empire total). If no polity matches that sub-territory, it is a coverage_gap -> create the granular polity (e.g. 'Czech Lands within Austria-Hungary'), do NOT fold it into the empire. When CREATING a polity, source its polygon by PRIORITY: exact historical GIS (CShapes/Cliopatria/CHGIS/Paine/GHGIS) > composed union > period proxy > modern/constructed estimate (LAST resort, flagged "ESTIMATE"); record polygon_source/method/confidence; prefer polygon_status=unassigned with a reason over a silent modern-borders guess. Also emit a routing alias (label->code, year-ranged) into applied_aliases.csv so name-only data routes. Data extending BEFORE a country's earliest WHEP polity (e.g. 'italy' pre-1861, 'australia' pre-1901) is either a date-extension of an existing polity or a missing PREDECESSOR polity (Kingdom of Sardinia, Australian colonies) — decide per the data's territory.`

const ISSUE = { type:'object', additionalProperties:false, required:['verdict','unit_key','unit_kind'],
  properties:{ verdict:{type:'string', enum:['correct','issue']},
    unit_key:{type:'string', description:'the audited unit identifier: polity_code (territorial flag) or data label (finding)'},
    unit_kind:{type:'string', enum:['polity','match']},
    evidence_hash:{type:'string', description:'copy the audited unit\'s evidence_hash field VERBATIM (empty string if the unit has none) — the ledger uses it to skip the unit only while its evidence is unchanged'},
    issue:{ type:'object', additionalProperties:false,
      properties:{ issue_id:{type:'string'}, type:{type:'string', enum:['rematch_alias','faostat_route','polity_dates','polity_extent_polygon','missing_polity','double_count','data_error']},
        origin:{type:'string', enum:['faostat','layerb'], description:'faostat if the audited finding came from faostat-era-matching (its sources==["faostat"] or note starts "faostat-era-matching:"), else layerb'},
        subject_polity:{type:'string'}, subject_label:{type:'string'}, period:{type:'string'},
        description:{type:'string'}, proposed_fix:{type:'string'}, confidence:{type:'string', enum:['high','medium','low']} } } } }
const HARM = { type:'object', additionalProperties:false, required:['harmonized'],
  properties:{ harmonized:{ type:'array', items:{ type:'object', additionalProperties:true, required:['issue_id','type','description'] } } } }
const CHANGESET = { type:'object', additionalProperties:false, required:['issue_id','fix_type','summary'],
  properties:{ issue_id:{type:'string'}, fix_type:{type:'string'}, summary:{type:'string'},
    wiki_path:{type:'string'}, wiki_content:{type:'string'},
    csv_row:{type:'string', description:'a full polities_database.csv row to add, or empty'},
    csv_edit:{type:'string', description:'description of an edit to an existing row, or empty'},
    alias_row:{type:'object', additionalProperties:false, description:'for rematch_alias (LAYER-B only): append to state/applied_aliases.csv (the file the 01 matcher reads). NEVER for faostat-origin issues.',
      properties:{ original_name:{type:'string'}, common_name:{type:'string'}, target_polity_code:{type:'string'} } },
    match_rule_patch:{type:'string', description:'OPTIONAL: equivalent rule for the legacy pre1961-matching/match.R, or empty'},
    match_r_patch:{type:'string', description:'for faostat_route: the manual_prefix entry or manual_span_routes row to add to pipelines/faostat-era-matching/match.R, or empty'},
    polygon_decision:{type:'string'}, commit_message:{type:'string'} } }

// ---------- Audit ----------
phase('Audit')
const auditOne = (src, i) => {
  if (budget.total && budget.remaining() < 25_000) return null
  return agent(
    `Audit one WHEP review unit. ${RULES}\nRead the JSON array at ${src} and take element index ${i}. ` +
    `Read ${polities_csv} as needed. Decide: is this data->polity match (and the polity's territory for the period) CORRECT? ` +
    `Set unit_key = the polity_code (territorial flag) or the data label (finding), and unit_kind accordingly. ` +
    `Set evidence_hash = the unit's evidence_hash field copied verbatim (empty string if absent). ` +
    `Set issue.origin = "faostat" when the finding came from faostat-era-matching (its sources array is ["faostat"], or its note starts with "faostat-era-matching:"), else "layerb". ` +
    `For a FAOSTAT finding choose issue.type = "missing_polity" when no polity covers the area at all, or "faostat_route" when the note says overlapping/ambiguous polity periods (it needs a match.R route, not an alias). ` +
    `If correct -> verdict "correct". If not -> verdict "issue" with a typed issue report (issue_id = stable kebab of subject+type, choose type, describe, propose a fix). Use the evidence fields when present: staple_magnitudes and contained_with_concurrent_data (the primary, data-grounded evidence), plus source_notes as a HINT ONLY — the source's own footnotes (e.g. "trade with japanese korea" / "1937 vs 1945 boundaries") can be OCR-garbled, mis-matched to the wrong row, or mis-attributed, so use them to corroborate or raise questions, NEVER decide on a footnote alone; weigh them against the data magnitudes and your own reasoning.`,
    { ...M, label:`audit:${src.includes('flagged')?'terr':'find'}:${i}`, phase:'Audit', schema:ISSUE })
}
// bound the per-run audit to max_audit (findings first, then flags). 01/02 already dropped ledger-resolved units.
const auditCalls = [
  ...Array.from({length:n_findings}, (_,i)=>()=>auditOne(findings_path, i)),
  ...Array.from({length:n_flags},   (_,i)=>()=>auditOne(flagged_path, i)),
].slice(0, max_audit)
if (auditCalls.length === 0) {
  log('WARNING: 0 units to audit — n_findings + n_flags is 0 (or everything is ledger-resolved). '
    + 'Pass the current counts of state/findings.json + state/territorial_flagged.json; an arg-less run is a no-op.')
}
const audited = (await parallel(auditCalls)).filter(Boolean)
const issues = audited.filter(a=>a.verdict==='issue' && a.issue).map(a=>a.issue)
const correctUnits = audited.filter(a=>a.verdict==='correct').map(a=>({key:a.unit_key, kind:a.unit_kind, evidence_hash:a.evidence_hash||''}))
log(`Audit: ${audited.length}/${n_findings+n_flags} units audited, ${issues.length} issues, ${correctUnits.length} correct`)

// ---------- Reconcile (DETERMINISTIC: group issues by subject — no agent) ----------
phase('Reconcile')
const rnorm = s => (s||"").toString().toLowerCase().replace(/\(.*?\)/g," ").replace(/[^a-z0-9 ]/g," ").replace(/\s+/g," ").trim()
const groups = new Map()
for (const it of issues) {
  const key = (it.subject_polity && it.subject_polity.trim()) || rnorm(it.subject_label) || it.issue_id
  if (!groups.has(key)) groups.set(key, [])
  groups.get(key).push(it)
}
let harmonized = [...groups.values()].map(grp => {
  const tc = {}; for (const g of grp) tc[g.type] = (tc[g.type]||0)+1
  const type = Object.entries(tc).sort((a,b)=>b[1]-a[1])[0][0]
  const a = grp[0]
  const origin = grp.map(g=>g.origin).find(o=>o==='faostat') || 'layerb'
  return { issue_id:a.issue_id, type, origin, subject_polity:a.subject_polity, subject_label:a.subject_label,
           period:a.period, confidence:a.confidence,
           description: grp.map(g=>g.description).filter(Boolean).join(" | ").slice(0,1500),
           proposed_fix: grp.map(g=>g.proposed_fix).filter(Boolean).join(" | ").slice(0,800),
           supersedes: grp.map(g=>g.issue_id) }
}).slice(0, max_issues)   // issues arrive row-ordered; keep the highest-impact
log(`Reconcile (deterministic): ${issues.length} issues -> ${harmonized.length} harmonized`)

// ---------- Fix (worktree-isolated; emit change-sets, do NOT commit) ----------
phase('Fix')
const changesets = (await parallel(harmonized.map(h => () => {
  if (budget.total && budget.remaining() < 30_000) return null
  const isFaostat = h.origin === 'faostat'
  return agent(
    `You are fixing ONE WHEP issue, wiki-first. ${RULES}\n` +
    (isFaostat ? `THIS IS A FAOSTAT-ERA ISSUE. ${FAOSTAT_FIX}\n` : ``) +
    `Issue: ${JSON.stringify(h)}\n` +
    `Research the entity, then produce a CHANGE-SET (do NOT commit, do NOT run git): ` +
    (isFaostat
      ? `for faostat_route, emit match_r_patch (manual_prefix or manual_span_routes entry) — NOT alias_row; for missing_polity, the wiki page content (wiki/polities/<code>.md per the repo's Territorial-extent requirements) + the CSV row + polygon_decision (match.R will route the area via its iso3 family). `
      : `for rematch_alias, emit alias_row {original_name (the verbatim data label), common_name, target_polity_code} — this is appended to state/applied_aliases.csv, the file the 01 matcher actually reads (optionally also match_rule_patch for the legacy match.R); ` +
        `for a polity change (dates/extent/missing), the wiki page content (wiki/polities/<code>.md per the repo's Territorial-extent requirements) + the CSV row/edit + polygon_decision; `) +
    `for data_error, summary only. Provide a one-line commit_message.`,
    { ...M, label:`fix:${h.issue_id}`, phase:'Fix', isolation:'worktree', schema:CHANGESET })
}))).filter(Boolean)
log(`Fix: ${changesets.length} change-sets`)

// ---------- Integrate (SERIAL: one commit per issue) ----------
phase('Integrate')
const applied = []
for (const cs of changesets) {
  const res = await agent(
    `Apply ONE change-set to ${repo} and commit it, then STOP. ${RULES}\nChange-set: ${JSON.stringify(cs)}\n` +
    `Steps: (1) if alias_row present, append it to pipelines/polity-autoimprove/state/applied_aliases.csv (create with header 'original_name,common_name,target_polity_code,confidence,rows' if missing) — but NEVER for a faostat-origin change-set; (2) write wiki_content to wiki_path if present; (3) apply csv_row/csv_edit to data/final/polities_database.csv; (4) apply match_rule_patch to pre1961-matching/match.R only if present; (4b) if match_r_patch present, apply it to pipelines/faostat-era-matching/match.R by adding the entry to the manual_prefix vector or the manual_span_routes tribble (do not append to applied_aliases.csv — match.R regenerates those); (5) git add the touched files and 'git commit -m "<commit_message>"' (end the message with the repo's required Co-Authored-By + Claude-Session trailers). Do NOT push. Report the commit hash and files changed. Leave no untracked stray files.`,
    { ...M, effort:'low', label:`integrate:${cs.issue_id}`, phase:'Integrate' })
  applied.push({ issue_id: cs.issue_id, result: res })
}

// If any fix was FAOSTAT-origin (new polity or a match.R route), regenerate
// the area-code -> polity routing so Verify sees the effect. The FAOSTAT
// matcher is replace-by-source, so hand-edits to applied_aliases.csv don't
// apply — routing MUST be re-derived by re-running match.R.
const faostatTouched = harmonized.some(h => h.origin === 'faostat')
if (faostatTouched) {
  await agent(
    `Regenerate FAOSTAT-era routing after polity/route fixes, then commit. Run: cd ${repo} && Rscript --vanilla pipelines/faostat-era-matching/match.R ` +
    `(it needs a WHEP checkout's pins cache via WHEP_REPO; if it errors because pins are unavailable in this environment, report that plainly and STOP without failing the run). ` +
    `If it succeeds and left pipelines/polity-autoimprove/state/applied_aliases.csv or pipelines/faostat-era-matching/state/* modified, git add those files and commit with message "faostat-era-matching: regenerate routing after polity/route fixes" (end with the repo's required Co-Authored-By + Claude-Session trailers). Do NOT push. Report what changed.`,
    { ...M, effort:'low', label:'integrate:faostat-regen', phase:'Integrate' })
}

// ---------- Verify: re-run the matcher and see which fixes actually resolved ----------
phase('Verify')
const VERIFY = { type:'object', additionalProperties:false, required:['unresolved_keys'],
  properties:{ unresolved_keys:{type:'array', items:{type:'string'}} } }
// key match-units by the DATA LABEL (findings are label-keyed, so Verify/ledger-gating must match on it);
// fall back to polity_code for pure polity-unit issues that carry no data label.
const harmKey = h => (h.subject_label || h.subject_polity || h.issue_id)
const ver = await agent(
  `Re-run the WHEP matcher and report which fixes did NOT resolve. Run: cd ${repo} && python3 pipelines/polity-autoimprove/01_match_and_findings.py (it now reads the just-committed applied_aliases.csv). ` +
  `Then read pipelines/polity-autoimprove/state/findings.json. For each of these subject keys, return it in unresolved_keys IF it STILL appears as a finding entity (i.e. the fix did not route its data): ${JSON.stringify(harmonized.map(harmKey))}`,
  { ...M, label:'verify-rematch', phase:'Verify', schema:VERIFY })
const unresolved = new Set((ver && ver.unresolved_keys) || [])
log(`Verify: ${harmonized.length - unresolved.size}/${harmonized.length} fixes confirmed resolved`)

// ---------- Cleanup: ledger — fixed only the VERIFIED-resolved; others stay open for retry ----------
phase('Cleanup')
// 'correct' rows bank WITH the unit's evidence_hash (a banked row is skipped only
// while its hash matches the unit's current evidence; empty hash = reopens if the
// unit resurfaces). 'fixed' rows bank WITHOUT a hash on purpose: the finding should
// be gone after the fix; if it ever resurfaces (data change / incomplete fix) the
// missing hash reopens it for one re-audit, which re-banks it with a fresh hash.
const ledgerRows = [
  ...correctUnits.map(u => ({ unit_kind:u.kind, key:u.key, status:'correct', evidence_hash:u.evidence_hash })),
  ...harmonized.map(h => ({ unit_kind: h.subject_label ? 'match':'polity', key: harmKey(h),
                            status: unresolved.has(harmKey(h)) ? 'issue' : 'fixed', evidence_hash:'' })),
]
await agent(
  `Update the WHEP review ledger so resolved units are skipped on the next run. Append/merge these rows into ${repo}/pipelines/polity-autoimprove/state/review_ledger.csv ` +
  `(header: unit_kind,key,status,issue_id,evidence_hash,last_run,last_commit; fill last_run with today's date; fill evidence_hash EXACTLY as given in each row, including empty). ` +
  `Rows with status 'fixed' are confirmed resolved; status 'issue' means the fix did NOT resolve and should be retried next run (do not mark those correct/fixed). ` +
  `Do NOT duplicate keys already present (update their status/evidence_hash instead). Then commit ONLY review_ledger.csv with message "autoimprove: update review ledger". Rows:\n${JSON.stringify(ledgerRows).slice(0,60000)}`,
  { ...M, label:'cleanup-ledger', phase:'Cleanup' })

return {
  units_audited: audited.length,
  audit_universe: n_findings + n_flags,
  correct: correctUnits.length,
  issues: issues.length,
  harmonized: harmonized.length,
  committed: applied.length,
  ledger_rows_written: ledgerRows.length,
  note: 'Re-run 01/02 then this workflow to continue; ledger-resolved units are skipped, so each run\'s audit set shrinks.',
}
