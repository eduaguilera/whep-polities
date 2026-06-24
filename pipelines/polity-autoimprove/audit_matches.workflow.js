export const meta = {
  name: 'audit-matches',
  description: 'Audit already-matched assertions (suspects + a safe sample) to verify correctness and estimate the safe-bucket error rate',
  phases: [{ title: 'Audit', detail: 'one agent per assertion: is this data->polity match correct (right entity + right period)?', model: 'sonnet' }],
}
// args delivered as a JSON STRING by the runtime — parse it.
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {})
const repo         = A.repo || '/home/usuario/whep-polities'
const review_csv   = A.review_csv || `${repo}/pipelines/polity-autoimprove/state/audit_sample.csv`
const polities_csv = A.polities_csv || `${repo}/data/final/polities_database.csv`
const n            = Number(A.n) || 80
const M = { model: 'sonnet', effort: 'medium' }

const V = { type:'object', additionalProperties:false, required:['polity_code','verdict','reasoning'],
  properties:{ label:{type:'string'}, source:{type:'string'}, polity_code:{type:'string'},
    confidence_class:{type:'string'},
    verdict:{type:'string', enum:['correct','wrong','uncertain']},
    failure:{type:'string', enum:['none','wrong_entity','wrong_period','wrong_territory','aggregate_or_subnational','other']},
    reasoning:{type:'string'} } }

phase('Audit')
const verdicts = (await pipeline(Array.from({length:n},(_,i)=>i), (i) => {
  if (budget.total && budget.remaining() < 20_000) return null
  return agent(
    `Audit ONE WHEP data-to-polity match for correctness. Read the CSV at ${review_csv} and take row index ${i} (0-based; columns: label, source, polity_code, year_min, year_max, n_rows, method, iso_ok, name_ok, confidence_class, risk_flags). ` +
    `Read ${polities_csv} for the polity's name/iso/period. Question: is the data labelled '<label>' from source '<source>' for years <year_min>-<year_max> correctly matched to <polity_code>? ` +
    `Check: (1) right ENTITY (the polity is what the label refers to), (2) right PERIOD (the years fit and there isn't a better period-polity), (3) the polity isn't an aggregate/subnational mismatch. Territorial-extent fineness is a separate track — focus on entity+period here. ` +
    `Set verdict correct/wrong/uncertain and failure type. Return polity_code, label, source, confidence_class verbatim.`,
    { ...M, label:`auditmatch:${i}`, phase:'Audit', schema:V })
})).filter(Boolean)
return { audited: verdicts.length, verdicts }
