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
both the queue filter and the runner's cache. `--only` targets units without paying to reach them
alphabetically.

## Design

| piece | role |
|---|---|
| `runner.py` | owns the subprocess; one schema-valid result per job, cached and retried |
| `harness.py` | assembles deterministic evidence, runs the cycles, records verdicts |
| `schemas/routing_verdict.schema.json` | stage 1: match / create / not-a-territory / insufficient |
| `schemas/polygon_route.schema.json` | stage 2: where a proposed boundary comes from |
| `policy.json` | model, effort, timeout, budget — tunable without touching code |
| `state/routing_verdicts.csv` | the decision ledger (committed) |
| `state/runs/` | per-run prompts, stdout and results (gitignored) |

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

## A constraint worth knowing

The committed `gadm-4.1-adm1` file is a **subset of 81 countries**, not the global layer. Of the
panel's 13 multi-unit countries only **ESP, USA and JPN** are present; France, Brazil, Argentina,
Mexico, Colombia, Italy, Portugal, Chile, Bolivia and Australia are not. A `create_new` verdict for
those cannot be given a boundary from what is on disk, which is what stage 2's `new_source_needed`
and `none_available` routes are for.
