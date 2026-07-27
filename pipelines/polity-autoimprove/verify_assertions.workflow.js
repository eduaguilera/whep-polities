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
const reviewSample = Number(A.review_sample) || 5   // spot-review every Nth confident confirm; 1 = review everything
// distinct out file per run so concurrent runs don't clobber each other
const outFile = A.out || 'verdicts_pending.json'
const ASSERTIONS = `${repo}/pipelines/polity-autoimprove/state/assertions.json`
const POLDB = `${repo}/data/final/polities_database.csv`
const M = { model: 'sonnet', effort: 'medium' }

const HISTORIAN = `You are acting as an economic historian verifying a data->polity match for the WHEP historical polities database. The deterministic matcher routed a source label to a candidate polity by name/ISO + year containment — that is ROUTING, not verification. Your job: decide whether the SOURCE'S REPORTING TERRITORY under this label, in these years, equals the CANDIDATE POLITY'S territory. Known failure families you MUST check: (1) union/empire scope — e.g. does "Sweden" pre-1905 mean Sweden proper or the Sweden-Norway union? does "Austria" mean Cisleithania or the whole empire? does "France" include Algeria (administratively part of France)? (2) boundary vintage — data compiled on older borders than the year suggests (e.g. "Germany" 1920 data on 1913 borders); (3) combined reporting — one label carrying two polities' data (e.g. "Yemen" = YAR+PDR before 1990); (4) our own period splits being wrong for this source's reporting basis. EVIDENCE: use the bundle's staple_magnitudes and neighbor_segments — magnitude continuity across our period splits is the tell (a large step suggests a territorial scope change; smooth continuity suggests the same reporting territory). Compare magnitudes against the polity's area/population plausibility. Read the candidate's wiki page for its documented territory. Web research on the source's reporting conventions is allowed and encouraged when in doubt. A confident-wrong verdict is the failure mode this pipeline fears most; "uncertain" is a GRACEFUL, welcome outcome.`

const VERDICT = { type:'object', additionalProperties:false,
  required:['key','verdict','confidence','basis'],
  properties:{
    key:{type:'string'},
    verified_evidence_hash:{type:'string', description:'copy the bundle\'s evidence_hash VERBATIM — it pins which candidate/evidence you judged, so a verdict cannot be applied after the routing changed underneath it'},
    verdict:{type:'string', enum:['confirm','reroute','split_reroute','new_polity','not_a_polity','uncertain']},
    polity_code:{type:'string', description:'REQUIRED for confirm (echo candidate) and reroute (the different existing polity); empty otherwise'},
    split_segments:{type:'array', description:'for split_reroute: the observed span tiled into sub-ranges, each routed to an EXISTING polity (use when the source\'s reporting basis is misaligned with our period splits, e.g. data on pre-war borders published for years our DB assigns to the post-war polity). Segments must cover the whole observed span, in order, without overlap.',
      items:{type:'object', additionalProperties:false, required:['year_start','year_end','polity_code'],
        properties:{ year_start:{type:'integer'}, year_end:{type:'integer'}, polity_code:{type:'string'} } } },
    new_polity_proposal:{type:'object', additionalProperties:false,
      properties:{ name:{type:'string'}, start_year:{type:'integer'}, end_year:{type:'integer'},
        iso3:{type:'string'}, territory_description:{type:'string'},
        predecessor:{type:'string'}, successor:{type:'string'} } },
    confidence:{type:'string', enum:['high','medium','low']},
    confirm_kind:{type:'string', enum:['verified_equal','best_available'], description:'for confirm only: verified_equal = the reporting territory demonstrably equals the candidate\'s; best_available = the match is imperfect but no existing polity fits better (e.g. an occupation/transition span with no dedicated polity) — these are systematically revisited when the polity family changes'},
    wiki_note:{type:'string', description:'anything your research established that the candidate\'s WIKI PAGE should record but does not: an answer to one of its open questions, a quantified approximation, corroboration of its design. One or two sentences, empty string if nothing. This is how verification research accumulates instead of being discarded.'},
    source_convention:{type:'object', additionalProperties:false, description:'OPTIONAL: a reporting convention of the SOURCE ITSELF that you established and that is not already in the bundle\'s source_conventions — i.e. what a label or series actually measures, generalizing beyond this one assertion (e.g. "this source\'s population series is agricultural population, not total"). Omit unless you verified something genuinely new and cross-cutting.',
      properties:{ label_pattern:{type:'string', description:'normalized label substring this applies to, or * for any label in the source'},
        item_pattern:{type:'string', description:'item/series substring this applies to, or * for any'},
        convention:{type:'string'}, evidence:{type:'string'} } },
    basis:{type:'string', description:'one paragraph: what was checked, what decided it'},
    checks:{type:'array', items:{type:'string', enum:['scope','vintage','combined_reporting','split_basis','magnitude_continuity','wiki_territory','web_research']}} } }

// blind review: the reviewer NEVER sees the first verdict (anchoring would make
// agreement meaningless) — it produces its own full VERDICT from the same
// evidence, and the comparison is done in code below.
const sameTarget = (a, b) => {
  if (a.verdict !== b.verdict) return false
  // confirm: both endorse the bundle's candidate by definition (polity_code may
  // be an empty echo); reroute: the named targets must match exactly
  if (a.verdict === 'reroute')
    return (a.polity_code || '') === (b.polity_code || '')
  if (a.verdict === 'split_reroute') {
    const seg = v => JSON.stringify((v.split_segments || []).map(s => [s.year_start, s.year_end, s.polity_code]))
    return seg(a) === seg(b)
  }
  return true   // new_polity / not_a_polity / uncertain: same verdict class suffices
}

if (keys.length === 0) {
  log('WARNING: no assertion keys passed — compute pending keys from state/assertions.json and pass args.keys; this run is a no-op.')
}

phase('Verify')
// review every non-confirm / low-confidence verdict, PLUS a deterministic 1-in-5
// sample of confident confirms — a confident-wrong confirm is the failure mode
// this pipeline fears most, and without sampling it would never be reviewed
const needsReview = (v, i) => v && (v.verdict !== 'confirm' || v.confidence === 'low' || i % reviewSample === 0)
const results = await pipeline(keys,
  key => agent(
    `${HISTORIAN}\nVerify ONE assertion. Read ${ASSERTIONS} and find the assertion object whose "key" equals ${JSON.stringify(key)} (use python3/jq to extract just that object — do not load the whole file into your context). ` +
    `Read the candidate's wiki page (candidate_meta.wiki, repo-relative under ${repo}) and, if useful, the polity family in ${POLDB}. ` +
    `Decide: confirm (reporting territory = candidate's territory for the WHOLE observed span) | reroute (a DIFFERENT existing polity matches the whole span; give polity_code) | split_reroute (the span must be TILED across two or more existing polities — use when the source's reporting basis is misaligned with our period splits, e.g. it keeps publishing on pre-war borders for years our DB assigns to the post-war polity; give split_segments covering the whole observed span in order, no overlaps, each to an EXISTING polity code) | new_polity (no existing polity has this territory; give a proposal) | not_a_polity (aggregate/non-territorial label) | uncertain. ` +
    `Echo the key AND the bundle's evidence_hash (as verified_evidence_hash) verbatim. Ground the basis in the evidence bundle's magnitudes and the wiki territory. ` +
    `For confirm, set confirm_kind: verified_equal (territory demonstrably equals) vs best_available (imperfect but nothing fits better). ` +
    `The bundle's source_conventions field carries what EARLIER verifications established about this source's labels and series — treat those as verified starting points, not guesses. ` +
    `Set wiki_note to anything you established that the candidate's wiki page should record but doesn't (answers to its open questions, quantified approximations, corroboration of its design) — empty if nothing. ` +
    `Set source_convention ONLY if you verified a NEW cross-cutting convention of the source itself that isn't already in source_conventions.`,
    { ...M, label:`verify:${key.slice(0,40)}`, phase:'Verify', schema:VERDICT }),
  (v, key, i) => {
    if (!v) return null
    if (!needsReview(v, i)) return { verdict: v, review: null, quarantined: false }
    // BLIND second verification: same evidence, zero knowledge of the first
    // verdict. The verify prompt is deliberately worded differently so the two
    // agents don't converge by prompt echo alone.
    return agent(
      `${HISTORIAN}\nIndependently verify ONE assertion (you are the second, blind verifier — decide from scratch). ` +
      `Read ${ASSERTIONS} and extract ONLY the assertion object whose "key" equals ${JSON.stringify(key)} (python3/jq — do not load the whole file). ` +
      `Study the candidate's wiki page (candidate_meta.wiki under ${repo}), the family in ${POLDB} if useful, and the web for the source's reporting conventions when in doubt. ` +
      `Return your own verdict (same decision space: confirm/reroute/split_reroute/new_polity/not_a_polity/uncertain), echoing the key and the bundle's evidence_hash (as verified_evidence_hash) verbatim, and citing the evidence that decided it.`,
      { ...M, label:`review:${key.slice(0,40)}`, phase:'Review', schema:VERDICT })
      .then(r => {
        const agrees = r ? sameTarget(v, r) : false
        return { verdict: v, review: r, review_agrees: agrees, quarantined: !agrees }
      })
  })
const verdicts = results.filter(Boolean)
const nQ = verdicts.filter(x => x.quarantined).length
log(`Verify: ${verdicts.length}/${keys.length} verdicts (${nQ} quarantined by reviewer disagreement)`)

phase('Save')
await agent(
  `Write this JSON array to ${repo}/pipelines/polity-autoimprove/state/${outFile} (overwrite; pretty-print). Do NOT commit, do NOT touch any other file. ` +
  `Then print a 3-line summary of verdict counts.\n${JSON.stringify(verdicts).slice(0, 400000)}`,
  { ...M, effort:'low', label:'save-verdicts', phase:'Save' })

return {
  verified: verdicts.length,
  quarantined: nQ,
  by_verdict: verdicts.reduce((m, x) => { const k = x.verdict.verdict; m[k] = (m[k] || 0) + 1; return m }, {}),
  note: `Verdicts are in state/${outFile} — inspect, then run apply_verdicts.py [${outFile}] to bank/apply them.`,
}
