export const meta = {
  name: 'new-polity-create',
  description: 'Create new WHEP polities (wiki-first) with a disciplined polygon-source hierarchy + recorded provenance',
  phases: [
    { title: 'Design',    detail: 'research entity; design polity spec + pick polygon per source-priority; write wiki', model: 'sonnet' },
    { title: 'Integrate', detail: 'serial: write wiki + DB row (+ polygon), one commit per polity', model: 'sonnet' },
    { title: 'Verify',    detail: 're-run matcher; confirm the entity\'s data now routes to the new polity', model: 'sonnet' },
  ],
}
// args arrives as a JSON STRING — parse it.
const A = (typeof args === 'string') ? JSON.parse(args) : (args || {})
const repo = A.repo || '/home/usuario/whep-polities'
const polities = A.polities || []
const M = { model: 'sonnet', effort: 'medium' }
const POLDB = `${repo}/data/final/polities_database.csv`
const GPKG  = `${repo}/data/geodata/polities_polygons.gpkg`

const HIER = `POLYGON SOURCE PRIORITY (try in order; record why if you skip ahead):
1 exact_historical — a GIS source with the ACTUAL territory for this entity+period. CHECK FIRST:
  CShapes 2.0 (states + COLONIAL DEPENDENCIES, 1886+; in ${GPKG} and the cshapes gpkg), Cliopatria/Seshat
  (1618 polities 3400BCE-2024, data/geodata/cliopatria/), CHGIS (China), Paine (precolonial Africa), GHGIS (German regions).
2 composed_union — union of constituent sub-units' historical polygons.
3 period_proxy — copy an adjacent same-entity period polygon if territory ~unchanged; document the diff.
4 modern_proxy / constructed_estimate — LAST RESORT, only after confirming 1-3 don't exist.
You MAY read the gpkgs (geopandas) to CONFIRM a feature exists. Record polygon_source, polygon_method,
polygon_feature_id, polygon_feature_year, polygon_confidence, and polygon_notes. For any proxy/estimate,
state the km2/direction difference from the true territory and mark it "ESTIMATE - not authoritative".
NEVER silently use modern borders; prefer polygon_status=unassigned with a documented reason over a guess.`

const SPEC = { type:'object', additionalProperties:false,
  required:['polity_code','polity_name','iso3','start_year','end_year','polity_type','polygon_method','polygon_confidence','wiki_markdown','csv_row'],
  properties:{ polity_code:{type:'string'}, polity_name:{type:'string'}, iso3:{type:'string'},
    start_year:{type:'integer'}, end_year:{type:'integer'}, polity_type:{type:'string'},
    predecessor:{type:'string'}, successor:{type:'string'},
    polygon_source:{type:'string'}, polygon_method:{type:'string', enum:['exact_historical','composed_union','period_proxy','modern_proxy','constructed_estimate','unassigned']},
    polygon_feature_id:{type:'string'}, polygon_feature_year:{type:'string'},
    polygon_confidence:{type:'string', enum:['high','medium','low']}, polygon_notes:{type:'string'},
    wiki_markdown:{type:'string', description:'full wiki/polities/<code>.md incl frontmatter + ## Territorial extent with provenance'},
    csv_row:{type:'string', description:'one polities_database.csv row matching its 17-column header, using this spec'},
    aliases:{type:'array', description:'verbatim DATA LABELS that must route to this polity (essential when the label carries no iso). Each: original_name + the year sub-range that maps here.',
      items:{type:'object', additionalProperties:false, properties:{ original_name:{type:'string'}, year_start:{type:'integer'}, year_end:{type:'integer'} }}} } }

phase('Design')
const specs = (await parallel(polities.map((p,i) => () =>
  agent(`Create a NEW WHEP historical polity. Entity: "${p.label}" (iso ${p.iso||'?'}), period ${p.period}. Context: ${p.note||''}.\n` +
    `Read ${POLDB} for the 17-column schema, existing predecessor/successor codes, and to avoid code collisions. ${HIER}\n` +
    `Produce the full spec: polity_code (e.g. ${p.iso||'XXX'}-START-END), name, iso3, years, type=national, predecessor/successor (existing WHEP codes), the polygon decision per the hierarchy, the wiki_markdown, the csv_row, and \`aliases\`: the verbatim data label(s) for this entity (e.g. "${p.label}") with the year sub-range that should route here — REQUIRED so the data matches even if the label carries no iso.`,
    { ...M, label:`design:${p.label}`, phase:'Design', schema:SPEC })
))).filter(Boolean)
log(`Designed ${specs.length} polities`)

phase('Integrate')
const done = []
for (const s of specs) {
  const r = await agent(`Create this polity in ${repo}, then STOP. Spec: ${JSON.stringify(s)}\n` +
    `Steps: (1) write the wiki_markdown to wiki/polities/${s.polity_code.toLowerCase()}.md (wiki filenames are LOWERCASE by convention; the polity_code inside the frontmatter stays uppercase); (2) append the csv_row to data/final/polities_database.csv (verify it has the same number of columns as the header); ` +
    `(3) if polygon_method is composed_union/constructed_estimate AND you can build the geometry cheaply (geopandas), write it to data/geodata/constructed/constructed.geojson and set polygon_status=assigned; if exact_historical/period_proxy, the csv_row should already name the source/feature (polygon_status=assigned if you confirmed it, else recommended); ` +
    `(4) for each entry in aliases (${JSON.stringify(s.aliases||[])}), append a row to pipelines/polity-autoimprove/state/applied_aliases.csv (header original_name,source,year_start,year_end,common_name,target_polity_code,confidence,basis,rows) with target_polity_code=${s.polity_code}, so the data label routes to this polity; ` +
    `(5) git add the touched files (wiki, polities_database.csv, applied_aliases.csv) and commit "new polity: ${s.polity_code} (${s.polity_name})" with the repo's required trailers. Do NOT push. Report files changed, commit hash, polygon_method+confidence. No stray files.`,
    { ...M, label:`integrate:${s.polity_code}`, phase:'Integrate' })
  done.push({ code: s.polity_code, method: s.polygon_method, confidence: s.polygon_confidence, result: r })
}

phase('Verify')
const ver = await agent(`Re-run the WHEP matcher and confirm the new polities now receive their data. Run: cd ${repo} && python3 pipelines/polity-autoimprove/01_match_and_findings.py. ` +
  `Then read pipelines/polity-autoimprove/state/findings.json and report, for each of these entities, whether it is STILL an unmatched finding or now resolved: ${JSON.stringify(polities.map(p=>p.label))}. Also report the new overall match_pct.`,
  { ...M, label:'verify', phase:'Verify' })

return { created: done.map(d=>({code:d.code, polygon_method:d.method, confidence:d.confidence})), verify: ver }
