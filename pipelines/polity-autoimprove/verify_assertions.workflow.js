export const meta = {
  name: 'verify-assertions',
  description: 'One agent per pending assertion (label+source+years -> polity): verify the source\'s reporting territory equals the candidate polity\'s; independent reviewer on risky verdicts; quarantine on disagreement.',
  phases: [
    { title: 'Verify', detail: 'one economic-historian agent per assertion evidence bundle', model: 'sonnet' },
    { title: 'Review', detail: 'independent refuter on non-confirm / low-confidence verdicts; disagreement -> quarantine', model: 'sonnet' },
    { title: 'Save',   detail: 'write verdicts to state/verdicts_pending.json (NOT applied; run apply_verdicts.py)', model: 'sonnet' },
  ],
}
// Verification layer of the assertion pipeline (see README "State model" and
// 00_intake.py). The deterministic pass only ROUTES; this workflow decides.
//
// args = { repo?, keys: ["label|source|y1-y2", ...] }
//   keys = assertion keys to verify this run — compute from state/assertions.json
//   (status "pending"/"reopened"; chunk to ~100 per run). An empty/missing keys
//   list is a no-op with a warning (same caveat as autoimprove's n_findings).
//
// Output: an agent WRITES state/verdicts_pending.json. Nothing is applied to
// the ledger/aliases here — apply_verdicts.py (deterministic) does that, so a
// human can eyeball verdicts before they take effect.
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {})
const repo = A.repo || '/home/usuario/whep-polities'
const keys = Array.isArray(A.keys) ? A.keys : []
const ASSERTIONS = `${repo}/pipelines/polity-autoimprove/state/assertions.json`
const POLDB = `${repo}/data/final/polities_database.csv`
const M = { model: 'sonnet', effort: 'medium' }

const HISTORIAN = `You are acting as an economic historian verifying a data->polity match for the WHEP historical polities database. The deterministic matcher routed a source label to a candidate polity by name/ISO + year containment — that is ROUTING, not verification. Your job: decide whether the SOURCE'S REPORTING TERRITORY under this label, in these years, equals the CANDIDATE POLITY'S territory. Known failure families you MUST check: (1) union/empire scope — e.g. does "Sweden" pre-1905 mean Sweden proper or the Sweden-Norway union? does "Austria" mean Cisleithania or the whole empire? does "France" include Algeria (administratively part of France)? (2) boundary vintage — data compiled on older borders than the year suggests (e.g. "Germany" 1920 data on 1913 borders); (3) combined reporting — one label carrying two polities' data (e.g. "Yemen" = YAR+PDR before 1990); (4) our own period splits being wrong for this source's reporting basis. EVIDENCE: use the bundle's staple_magnitudes and neighbor_segments — magnitude continuity across our period splits is the tell (a large step suggests a territorial scope change; smooth continuity suggests the same reporting territory). Compare magnitudes against the polity's area/population plausibility. Read the candidate's wiki page for its documented territory. Web research on the source's reporting conventions is allowed and encouraged when in doubt. A confident-wrong verdict is the failure mode this pipeline fears most; "uncertain" is a GRACEFUL, welcome outcome.`

const VERDICT = { type:'object', additionalProperties:false,
  required:['key','verdict','confidence','basis'],
  properties:{
    key:{type:'string'},
    verdict:{type:'string', enum:['confirm','reroute','new_polity','not_a_polity','uncertain']},
    polity_code:{type:'string', description:'REQUIRED for confirm (echo candidate) and reroute (the different existing polity); empty otherwise'},
    new_polity_proposal:{type:'object', additionalProperties:false,
      properties:{ name:{type:'string'}, start_year:{type:'integer'}, end_year:{type:'integer'},
        iso3:{type:'string'}, territory_description:{type:'string'},
        predecessor:{type:'string'}, successor:{type:'string'} } },
    confidence:{type:'string', enum:['high','medium','low']},
    basis:{type:'string', description:'one paragraph: what was checked, what decided it'},
    checks:{type:'array', items:{type:'string', enum:['scope','vintage','combined_reporting','split_basis','magnitude_continuity','wiki_territory','web_research']}} } }

const REVIEW = { type:'object', additionalProperties:false, required:['key','agree','reason'],
  properties:{ key:{type:'string'}, agree:{type:'boolean'},
    own_verdict:{type:'string', enum:['confirm','reroute','new_polity','not_a_polity','uncertain']},
    own_polity_code:{type:'string'}, reason:{type:'string'} } }

if (keys.length === 0) {
  log('WARNING: no assertion keys passed — compute pending keys from state/assertions.json and pass args.keys; this run is a no-op.')
}

phase('Verify')
const needsReview = v => v && (v.verdict !== 'confirm' || v.confidence === 'low')
const results = await pipeline(keys,
  key => agent(
    `${HISTORIAN}\nVerify ONE assertion. Read ${ASSERTIONS} and find the assertion object whose "key" equals ${JSON.stringify(key)} (use python3/jq to extract just that object — do not load the whole file into your context). ` +
    `Read the candidate's wiki page (candidate_meta.wiki, repo-relative under ${repo}) and, if useful, the polity family in ${POLDB}. ` +
    `Decide: confirm (reporting territory = candidate's territory) | reroute (a DIFFERENT existing polity matches; give polity_code) | new_polity (no existing polity has this territory; give a proposal) | not_a_polity (aggregate/non-territorial label) | uncertain. ` +
    `Echo the key verbatim. Ground the basis in the evidence bundle's magnitudes and the wiki territory.`,
    { ...M, label:`verify:${key.slice(0,40)}`, phase:'Verify', schema:VERDICT }),
  (v, key) => {
    if (!v) return null
    if (!needsReview(v)) return { verdict: v, review: null, quarantined: false }
    return agent(
      `${HISTORIAN}\nYou are an INDEPENDENT REVIEWER. Another agent verified an assertion and returned this verdict — your job is to try to REFUTE it. ` +
      `Read ${ASSERTIONS} and extract the assertion whose "key" equals ${JSON.stringify(key)} (surgically — python3/jq). Re-derive your own conclusion from the evidence bundle, the wiki page, and (if needed) web research on the source's conventions. ` +
      `Verdict under review: ${JSON.stringify(v)}. ` +
      `Set agree=true ONLY if you independently reach the SAME verdict AND the same target (same polity_code, or materially the same new-polity territory). Default to agree=false when uncertain.`,
      { ...M, label:`review:${key.slice(0,40)}`, phase:'Review', schema:REVIEW })
      .then(r => ({ verdict: v, review: r,
                    quarantined: !(r && r.agree === true) }))
  })
const verdicts = results.filter(Boolean)
const nQ = verdicts.filter(x => x.quarantined).length
log(`Verify: ${verdicts.length}/${keys.length} verdicts (${nQ} quarantined by reviewer disagreement)`)

phase('Save')
await agent(
  `Write this JSON array to ${repo}/pipelines/polity-autoimprove/state/verdicts_pending.json (overwrite; pretty-print). Do NOT commit, do NOT touch any other file. ` +
  `Then print a 3-line summary of verdict counts.\n${JSON.stringify(verdicts).slice(0, 400000)}`,
  { ...M, effort:'low', label:'save-verdicts', phase:'Save' })

return {
  verified: verdicts.length,
  quarantined: nQ,
  by_verdict: verdicts.reduce((m, x) => { const k = x.verdict.verdict; m[k] = (m[k] || 0) + 1; return m }, {}),
  note: 'Verdicts are in state/verdicts_pending.json — inspect, then run apply_verdicts.py to bank/apply them.',
}
