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

const WIKI_SKEPTICISM = ` CRITICAL — THE WIKI IS NOT GROUND TRUTH. Most polity pages (634 of 733) have wiki_status "draft", meaning they were written by an EARLIER AUTOMATED PASS and never reviewed by a human. candidate_meta.wiki_status tells you which you are looking at. Treat a "draft" page as a PRIOR AGENT'S HYPOTHESIS, not as evidence: its territorial claims, areas, dates and "Data routing" decisions may be wrong, and confirming your verdict by citing a draft page is CIRCULAR REASONING — an earlier agent's guess laundered into an apparent verification. To rely on a territorial claim from a draft page you must corroborate it independently: the data's own magnitudes, an external authority (search the web — encyclopaedias, historical-boundary literature, statistical-yearbook documentation, census figures), or a source file you can read. Do NOT treat wiki_status "reviewed" as a guarantee either: 10 of 72 reviewed pages are thin stubs with no source citations at all. candidate_meta.wiki_page gives the page's measurable depth (bytes, source_citations, has_todo_markers) — judge the page on THAT plus the specific claim you need, not on its status label. A page with zero source_citations is an assertion by whoever wrote it, whatever its status says. If the page's own claims look WRONG, say so in wiki_note and set page_suspect — a page that misstates its polity's territory or dates is a finding in its own right, more valuable than the verdict itself. Record honestly in evidence_used what your conclusion actually rests on.`

const HISTORIAN = `You are acting as an economic historian verifying a data->polity match for the WHEP historical polities database.${WIKI_SKEPTICISM} The deterministic matcher routed a source label to a candidate polity by name/ISO + year containment — that is ROUTING, not verification. Your job: decide whether the SOURCE'S REPORTING TERRITORY under this label, in these years, equals the CANDIDATE POLITY'S territory. Known failure families you MUST check: (1) union/empire scope — e.g. does "Sweden" pre-1905 mean Sweden proper or the Sweden-Norway union? does "Austria" mean Cisleithania or the whole empire? does "France" include Algeria (administratively part of France)? (2) boundary vintage — data compiled on older borders than the year suggests (e.g. "Germany" 1920 data on 1913 borders); (3) combined reporting — one label carrying two polities' data (e.g. "Yemen" = YAR+PDR before 1990); (4) our own period splits being wrong for this source's reporting basis; (5) SUB-TERRITORY FOLD-UP — the label may be NARROWER than the candidate, not broader. Check this direction explicitly: it is the one most often missed. A label naming a province, island, colony-within-a-federation, mining district or other component ("Makatea" inside French Polynesia, "Bohemia"/"Czech Lands" inside Austria-Hungary, "Manchuria" inside China, "Java and Madura" inside Indonesia, "Western Australia" inside Australia) must NOT be matched up to the parent whose territory is many times larger — that silently attributes a component's output to the whole. Compare the label's own territory against candidate_meta.area_km2: if the label denotes a fraction of the candidate, the verdict is reroute (if a granular polity exists) or new_polity (if it does not), NEVER confirm — and certainly never verified_equal. Only confirm a component label against a parent polity when the parent IS the reporting unit (i.e. the source aggregates that component into the parent's own totals rather than reporting the component separately) — and if you confirm on that basis, say so explicitly and use best_available. (6) ENTREPOT / RE-EXPORT — the territory may never have produced the goods at all, merely handled them. A port or transit colony can carry large figures for a commodity its land cannot grow or mine: Ethiopian coffee routed through Djibouti (French Somaliland) on the 1917 railway, Malayan tin and rubber through Singapore, hinterland output through Hong Kong or Beira. The tell is agronomic or geological impossibility — a commodity whose scale makes no sense for the territory's climate, terrain or size. If you find one, the routing may still be the best available (the source recorded it under that label) but say so in wiki_note and flag the DOUBLE-COUNT risk against the producing polity's own series, because summing both attributes the same output twice. EVIDENCE: use the bundle's staple_magnitudes and neighbor_segments — magnitude continuity across our period splits is the tell (a large step suggests a territorial scope change; smooth continuity suggests the same reporting territory). Compare magnitudes against the polity's area/population plausibility. Read the candidate's wiki page for its documented territory. Web research on the source's reporting conventions is allowed and encouraged when in doubt. A confident-wrong verdict is the failure mode this pipeline fears most; "uncertain" is a GRACEFUL, welcome outcome.`

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
    confirm_kind:{type:'string', enum:['verified_equal','best_available'], description:'for confirm only. verified_equal demands BOTH: (a) the reporting territory equals the candidate\'s, AND (b) it stayed CONSTANT across the whole observed span. If the territory changed mid-span — annexations, cessions, a separation, an occupation — then NO single polity can equal it and the answer is best_available, even when nothing better exists and even when you judge the difference small. "The polygon vintage is imprecise" is NOT a reason to keep verified_equal: a territory that grew or shrank during the span is best_available. best_available is the honest, expected answer for long spans over polities that were never split; it is not a criticism of the routing.'},
    wiki_note:{type:'string', description:'ONLY genuinely NEW information the candidate\'s wiki page does not already contain: an answer to one of its open questions, a contradiction of something it asserts, a quantified approximation it lacks, or a newly discovered data-quality issue. Leave EMPTY for corroboration — "verified/confirmed as documented" is already recorded in the ledger and the verdict archive, and queueing it just creates wiki churn. Most confirms should return an empty wiki_note. One or two sentences when you do have something.'},
    source_convention:{type:'object', additionalProperties:false, description:'OPTIONAL: a reporting convention of the SOURCE ITSELF that you established and that is not already in the bundle\'s source_conventions — i.e. what a label or series actually measures, generalizing beyond this one assertion (e.g. "this source\'s population series is agricultural population, not total"). Omit unless you verified something genuinely new and cross-cutting.',
      properties:{ label_pattern:{type:'string', description:'normalized label substring this applies to, or * for any label in the source'},
        item_pattern:{type:'string', description:'item/series substring this applies to, or * for any'},
        convention:{type:'string'}, evidence:{type:'string'} } },
    evidence_used:{type:'array', description:'REQUIRED, honest: what your conclusion actually rests on. wiki_draft alone means the verdict is circular (an unreviewed earlier agent\'s page confirming itself) — say so rather than hiding it.',
      items:{type:'string', enum:['data_magnitudes','neighbor_continuity','wiki_reviewed','wiki_draft','external_source','web_research','source_file_inspected','prior_source_convention']}},
    page_suspect:{type:'boolean', description:'true if the candidate\'s WIKI PAGE asserts something WRONG (wrong territory, wrong dates, wrong area, a routing decision that does not hold up). Explain in wiki_note. A finding about the database, independent of the routing verdict. Thin-but-not-wrong is NOT page_suspect — use page_inadequate.'},
    page_inadequate:{type:'boolean', description:'true if the page is too THIN to support verification — e.g. it is a bulk CSV-derived stub with no source citations, or it documents only a polygon proxy and says nothing about the territory itself, so you had to establish the territory from outside it. Many pages (634 of 733 are draft, ~987 were once bulk-generated from CSV metadata alone) are in this state; flagging them is how the enrichment backlog gets built. Distinct from page_suspect: inadequate means uninformative, suspect means wrong.'},
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
    `Read the candidate's wiki page (candidate_meta.wiki, repo-relative under ${repo}) — CHECKING candidate_meta.wiki_status first and applying the skepticism rule above — and, if useful, the polity family in ${POLDB}. ` +
    `Decide: confirm (reporting territory = candidate's territory for the WHOLE observed span) | reroute (a DIFFERENT existing polity matches the whole span; give polity_code) | split_reroute (the span must be TILED across two or more existing polities — use when the source's reporting basis is misaligned with our period splits, e.g. it keeps publishing on pre-war borders for years our DB assigns to the post-war polity; give split_segments covering the whole observed span in order, no overlaps, each to an EXISTING polity code) | new_polity (no existing polity has this territory; give a proposal) | not_a_polity (aggregate/non-territorial label) | uncertain. ` +
    `Echo the key AND the bundle's evidence_hash (as verified_evidence_hash) verbatim. Ground the basis in the evidence bundle's magnitudes and the wiki territory. ` +
    `For confirm, set confirm_kind: verified_equal ONLY if the reporting territory both equals the candidate's AND stayed constant across the whole observed span; if it changed mid-span (annexation, cession, separation, occupation) the answer is best_available even when nothing better exists — check the span's history explicitly before claiming verified_equal, especially for spans over ~30 years. ` +
    `The bundle's source_conventions field carries what EARLIER verifications established about this source's labels and series — treat those as verified starting points, not guesses. ` +
    `Set wiki_note ONLY for genuinely new information the page lacks (an answer to one of its open questions, a contradiction, a data-quality issue, a missing quantification) — leave it EMPTY for mere corroboration, which the ledger and verdict archive already capture. ` +
    `Set source_convention ONLY if you verified a NEW cross-cutting convention of the source itself that isn't already in source_conventions. ` +
    `Fill evidence_used honestly. Set page_suspect if the page asserts something WRONG; set page_inadequate if it was simply too thin to support verification (a CSV-derived stub, or polygon-proxy notes only) so you had to establish the territory from outside it — the two are different findings and both are useful.`,
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
// Save, then STAMP each verdict with the bundle's real evidence_hash read from
// assertions.json BY SCRIPT. Agents echo the hash too, but an LLM transcribing a
// 16-hex string is unreliable (observed: one character-level slip that tripped
// the stale guard as a false positive), so the script-derived value is
// authoritative and the echo is advisory only.
await agent(
  `Write this JSON array to ${repo}/pipelines/polity-autoimprove/state/${outFile} (overwrite; pretty-print), then stamp the true evidence hashes into it by RUNNING this exact python (do not hand-edit hashes):\n` +
  "```\n" +
  `python3 - <<'PY'\nimport json\nH="${repo}/pipelines/polity-autoimprove/state"\nV=json.load(open(f"{H}/${outFile}"))\nA={a["key"]:a for a in json.load(open(f"{H}/assertions.json"))["assertions"]}\nn=0\nfor x in V:\n    v=x["verdict"]; b=A.get(v["key"])\n    if not b: continue\n    if v.get("verified_evidence_hash") != b["evidence_hash"]: n+=1\n    v["echoed_evidence_hash"]=v.get("verified_evidence_hash")\n    v["verified_evidence_hash"]=b["evidence_hash"]\njson.dump(V, open(f"{H}/${outFile}","w"), indent=1)\nprint(f"stamped {len(V)} verdicts; corrected {n} echoed hashes")\nPY\n` +
  "```\n" +
  `Do NOT commit and do NOT touch any other file. Then print the python's output plus a 2-line summary of verdict counts.\n${JSON.stringify(verdicts).slice(0, 400000)}`,
  { ...M, effort:'low', label:'save-verdicts', phase:'Save' })

return {
  verified: verdicts.length,
  quarantined: nQ,
  by_verdict: verdicts.reduce((m, x) => { const k = x.verdict.verdict; m[k] = (m[k] || 0) + 1; return m }, {}),
  note: `Verdicts are in state/${outFile} — inspect, then run apply_verdicts.py [${outFile}] to bank/apply them.`,
}
