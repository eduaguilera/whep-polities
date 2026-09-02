# agent-harness

A Python harness we own, replacing the `.workflow.js` agent loops. It takes a table of reporting
units and finds out, per unit, whether an existing polity already IS that territory, whether one
needs creating, or whether the identifier is not a territory at all.

## Why it exists

The previous loops were `.workflow.js` scripts driven by an external orchestrator. That made the
decisions untestable from here, the model's output trusted rather than validated, and the loop
unavailable to anything but an interactive session. It also meant a human decided *"this country
needs prefectures"* and then configured a generator per country — which does not scale past the
country in front of you and learns nothing from the data.

Here, **"we need provinces here" is an output.**

## Run it

```bash
export WHEP_SUBNATIONAL=/path/to/whep_production_subnational.parquet   # NEVER committed
python3 pipelines/agent-harness/harness.py --country Japan --limit 4
python3 pipelines/agent-harness/harness.py --country "United States of America" \
        --only USA-RESID --polygon-stage
python3 pipelines/agent-harness/test_harness.py
```

`--cycles N` escalates rather than repeats: a unit returning `insufficient_evidence` is re-asked
with a wider candidate net and its siblings' verdicts. `--refresh` re-asks a decided unit, bypassing
both the queue filter and the runner's cache — **on the first cycle only**. `--refresh --cycles 2`
once re-asked all 53 Spanish units twice, re-opening settled high-confidence verdicts under a net
that exists for units nothing could decide. `--refresh-convention` re-decides the country's
convention, which `--refresh` deliberately leaves alone. `--only` targets units without paying to reach them
alphabetically.

## Design

| piece | role |
|---|---|
| `runner.py` | owns the subprocess; one schema-valid result per job, cached and retried |
| `harness.py` | assembles deterministic evidence, runs the cycles, records verdicts |
| `repair.py` | classifies gate failures and aims the narrowest repair at each |
| `schemas/country_convention.schema.json` | stage 0: the country's span, container chain and naming |
| `schemas/routing_verdict.schema.json` | stage 1: match / create / not-a-territory / insufficient |
| `schemas/polygon_route.schema.json` | stage 2: where a proposed boundary comes from |
| `schemas/wiki_page.schema.json` | stage 3: the page, to this repo's page requirements |
| `schemas/failure_class.schema.json` | stage 4: what an unrecognised gate arm actually checks |
| `schemas/iso_resolution.schema.json` | a country label the repo's crosswalks do not answer |
| `policy.json` | model, effort, timeout, budget — tunable without touching code |
| `state/routing_verdicts.csv` | the decision ledger (committed) |
| `state/country_conventions.json` | one span/container convention per country (committed) |
| `state/country_iso.json` | labels resolved by asking, so they are asked once (committed) |
| `state/gate_arm_kinds.json` | gate arms learned from their source (committed) |
| `state/runs/` | per-run prompts, stdout and results (gitignored) |

**A country's convention is decided once, before any of its units.** Spain's 44 `create_new`
verdicts once proposed **five** different end years — 2025 ×17, 2026 ×18, 2100 ×3, 2022 ×1, and one
starting 1927 — for provinces sharing one administrative history, because each unit was decided with
no view of what its siblings chose. Nothing in a per-unit prompt can fix that. Stage 0 establishes
`system_start_year`, one `open_end_year`, the container chain and the naming pattern, and every
unit's evidence then carries them as a constraint. It is banked as a **decision**, not cached:
`--refresh` re-asks the units and leaves the convention alone, because a convention that can change
between runs is the disagreement all over again. `--refresh-convention` re-decides it.

**The start is per-unit; only the end is country-wide.** Stage 0's first version asked for one
`system_start_year` and Spain hid the flaw, because all 50 provinces were created at once by the 1833
reform. The USA is the counterexample: the answer came back **1959**, the year the 50th state joined,
with `system_start_basis` omitted entirely — the field had a `minLength` but was not `required`, so
the constraint never applied. Injected as a constraint, that would have spanned California from 1959.

`system_start_year` is now documented as a **floor**, `unit_start_rule` says how an individual unit's
own start is found, and both bases are required. Re-decided, the USA returns floor **1787** with
*"the year it was admitted to the Union (e.g. Delaware 1787, California 1850, Alaska and Hawaii
1959)"* — and California comes out **1850-2025**, container `USA-1848-1867`. A banked convention is
re-validated against the schema on load, so tightening the contract reaches decisions already made
rather than only countries not yet decided.

**And the rule is a default, with departures enumerated.** Spain's convention then contradicted
itself *within one object*: `system_start_basis` said the 1833 reform made "49 (later 50, with the
1927 split of the Canary Islands) provinces", while `unit_start_rule` said "all units begin at the
floor (1833) ... no per-unit variation is needed". The per-unit stage inherited the rule and dated
Las Palmas **1833 — 94 years before it existed** — with the refuting fact two fields away.
`unit_start_exceptions` is now required, so an empty list is a claim rather than a default, and the
per-unit evidence presents the rule as a default and invites a justified departure. Re-decided,
Spain returns **50 provinces at 1833-2025 and exactly the two Canary provinces at 1927-2025**.

Stage 0 is checked against the polity table but **never corrected**. A container code that is not in
the table, or an `open_end_year` that is not any container's own `end_year` *column* (the code string
and the column disagree for some rows — read the column), is handed back as a stated objection and
asked again, then refused. Choosing the value here would be the harness inventing a country's span.

**Deterministic and judgement are kept apart.** The harness supplies coverage, candidate polities by
iso3 and by normalised name, boundary availability, and identifier markers. The agent decides whether
a candidate *is* the territory, whether the unit is a territory at all, and what span a new row
carries. The harness never pre-decides: a unit whose id ends `-NATIONAL` is presented *with* that
observation and the national polity as a candidate, because the same shape is sometimes a bucket and
sometimes a legitimate whole-territory report, and hard-coding it is how a config grows 26 special
cases.

**The CLI schema is a hint; our validator is the contract.** `--json-schema` rejects a `$schema`
draft ref and does not support conditional subschemas, so those keywords are stripped from the copy
handed to the CLI — but not from the schema we validate against. Rules like *"a `match_existing`
verdict must name a code"* are therefore still enforced, by us, where they are testable. The job
fingerprint covers the full schema, so tightening a rule the CLI never sees still invalidates the
cache.

**Read-only by construction.** `Edit`, `Write` and `NotebookEdit` are denied on the command line
rather than discouraged in the prompt. Applying a verdict is the harness's job, in Python.

## What replacing the workflows still needs

`new_polity.workflow.js` ran three phases. Only the first needs an agent:

| phase | status | note |
|---|---|---|
| **Design** — spec + polygon per source priority | **done** — stages 1 and 2 | |
| **Integrate** — wiki page, DB row, polygon, one commit per polity | **not built** | mechanical; belongs in Python, not an agent |
| **Verify** — re-run the matcher, confirm the data routes | **not built** | `scripts/structural_change_check.py --compare` already does this deterministically |

`verify_assertions.workflow.js` (assertion verification) and `autoimprove.workflow.js` (the
audit→reconcile→fix loop) are **not yet ported**, so they stay. Deleting them now would remove
working source-onboarding before this harness covers it.

`pipelines/subnational-vocabulary/10_generate_pages.py` is **superseded by this harness** and kept
only as the record of how Japan's 46 prefectures were generated. It carries a hand-written
`COUNTRIES` dict — a human decided Japan needed prefectures and then configured a generator for it,
which is the thing this harness exists not to do. Do not add a country to that dict; run stage 0 and
stage 1 here instead.

## Where the harness decides, and where it asks

A deterministic step is worth having only where it is *certainly* right. Where it encodes a guess it
is worse than asking, because it looks like a rule and has to be extended by hand for every new
dataset. Three tables were removed on exactly that ground:

| was | now |
|---|---|
| `{"unitedstatesofamerica": "USA", "russia": "RUS", ...}` | `faostat_area_polity_map.csv` + `label_alias_map.csv`, which this repo already builds and which answer **24 of the panel's 26** countries; the rest are asked once and banked |
| a regex list over the gates' failure prose | the gate's own **source**, read once per `(gate, arm)` and banked |
| `open_end_year` overridden to `max(container ends)` | the disagreement stated back and re-asked |

The regex list is the clearest case: it is what already failed. One apostrophe between *the
container's span* and *the container span* dropped a fixable arithmetic failure into the do-nothing
class, and the fix is not a better regex.

Two deterministic checks are kept, because neither is a guess:

- **a container code either exists in the table or it does not** — refusing an absent one invents
  nothing;
- **arithmetic-mode repairs restore prose from the previous version** — that is a scope constraint,
  and the alternative is asking an agent not to do what it has already done. A real run fixed one
  span and also rewrote `predecessors_and_successors`, `decisions` and `open_questions`, dropping an
  open question nobody had resolved.

## Hardening, and why each defence is there

Every one of these exists because the obvious implementation fails:

- **Output goes to files, never pipes.** Tool descendants inherit the CLI's stdout and stderr, so
  `communicate()` blocks on descendant-held pipe EOF long after the CLI exits — hanging on exactly
  the jobs that did the most work.
- **A timeout is not proof of failure.** The CLI can durably write a schema-valid result and then be
  held open by a descendant; deleting that output forces an identical expensive retry.
- **Throttle detection is deliberately narrow.** Only unambiguous capacity signals retry. Matching
  loose words like *rate* or *unavailable* would silently retry genuine schema failures, which are
  bugs to fix rather than conditions to wait out.
- **Aborting kills the group.** `start_new_session=True` plus `killpg` reaps every command the agent
  launched.
- **Identical work is not repeated.** Jobs are fingerprinted over (prompt, full schema, model,
  effort), so an interrupted run resumes instead of restarting.

## Bugs the first smoke run found

All in the *evidence* layer, all now regression-tested — and all found because the agent flagged them
in its `concerns`, not because a check failed:

1. **`iso3` resolved "United States of America" to `ARE`** (United Arab Emirates) on a 6-character
   prefix match. The verdicts that followed were plausible and built on another country's candidate
   rows — the worst failure available to an evidence layer, because it does not look broken.
2. **Cycle 1 trimmed subnational candidates**, hiding `ALK-1867-1959` (Territory of Alaska) from the
   Alaska verdict — the single most likely `match_existing` candidate. Now only earlier *national*
   eras are trimmed, and the trim is declared.
3. **Boundary name matching was one-directional**, so the panel's `US Alaska` never matched GADM's
   `Alaska`. Stage 2 had the reverse test and found `USA.2_1` while stage 1 reported no boundary.
4. **`--refresh` was inert** — the queue filter excluded decided units, so the flag never reached the
   cache it existed to bust, and the printed verdict was the stale one.
5. **The ledger was replaced instead of merged**, so `--refresh` on stage 1 destroyed the
   `polygon_*` and `page_*` fields stage 2 had written; stage 3 then skipped that unit and authored a
   page for a different one. A request for Alaska produced a page for California.
6. **Later stages ignored `--only`**, acting on units nobody had asked for.
7. **A chain edge was asserted without its counterpart.** The Alaska page declared
   `predecessor: [ALK-1867-1959]`; that row declares `successor: [USA-1959-2025]` — the whole
   country, not the state. `validate_chain_integrity` baselines asymmetry in **both** directions, so
   one such edge (84 predecessor-only against a baseline of 83) fails CI. Detected here as a fact
   and handed back with the counterpart's real fields: reciprocating automatically would give the
   territory two successors and silently pick a reading of history.
8. **`clean` meant "no failure named our code"** — not the same claim. A gate red only on other rows
   contributed nothing to the filtered list, and the empty list read as success. The red gates now
   travel separately from the attributable failures, and the status distinguishes `clean` from
   `clean_for_code`.

## Where it stands

Smoked end to end on the Ivorra/Infante-Amate/Aguilera/González de Molina provincial panel
(`WHEP_SUBNATIONAL`, never committed):

| | |
|---|---|
| Spain | **53 of 53 units decided**, no `insufficient_evidence`: 50 provinces `1833-2025`, the two Canary provinces `1927-2025`, one `match_existing` against a page the harness itself wrote |
| USA | convention floor `1787` with a five-era container chain; California `1850-2025` in `USA-1848-1867`; `USA-RESID` → `not_a_territory`; Alaska → `match_existing` once its row exists |
| stages | 0 convention, 1 routing, 2 polygon, 3 wiki, 4 repair — all exercised on real units |
| pages | `ESP-CO-1833-2025`, `ESP-MD-1833-2025` — authored, gate-clean, committed as `status: draft` |
| tests | 21, all in CI; every one is a defect that reached a real run |

Two things a reader should not assume. The repair loop's **JUDGEMENT** mode has never fired, because
no judgement-class failure has occurred yet — only its ARITHMETIC and clean paths are proven. And
the NUTS crosswalk `data/final/nuts_code_names.csv` has **no fetch script**: its `basis` column cites
the Eurostat GISCO NUTS 2021 table and, for `ES701`/`ES702`, the pre-2021 vintage, but neither is
regenerable from this repo. Those two codes were the only gap in 165 panel units, and the harness
found them the right way — it refused to guess and named the table to check.

## A constraint worth knowing

The committed `gadm-4.1-adm1` file is a **subset of 81 countries**, not the global layer. Of the
panel's 13 multi-unit countries only **ESP, USA and JPN** are present; France, Brazil, Argentina,
Mexico, Colombia, Italy, Portugal, Chile, Bolivia and Australia are not. A `create_new` verdict for
those cannot be given a boundary from what is on disk, which is what stage 2's `new_source_needed`
and `none_available` routes are for.
