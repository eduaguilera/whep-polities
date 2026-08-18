# polity-autoimprove

A **repeatable, agent-driven workflow** that incrementally improves the WHEP
polities database + wiki, run after run, converging toward the invariant:

> **every production/trade data point is matched to the correct polity, and that
> polity has the right territory (polygon) for the data's year.**

Each run reviews what is not yet resolved, files issues, fixes them wiki-first,
commits one fix per issue, and records state so the **next run starts clean and
skips everything already confirmed correct.** It is meant to be run on a schedule
or on demand until the issue queue is empty.

This pipeline **extends** [`pipelines/pre1961-matching`](../pre1961-matching/README.md)
(the deterministic matcher + confidence audit + the wiki-first "Creating new
polity entries" rules) to the full consolidated dataset and wraps it in an
audit → reconcile → fix → integrate → cleanup loop.

---

## Principles

1. **Wiki is the source of truth.** The database is derived from the wiki. Any
   change to a polity's identity/dates/extent is made in the wiki **first**, then
   propagated to `data/final/polities_database.csv`, then to a polygon.
2. **Aggregates are first-class.** Undivided Germany, the Japanese Empire, the
   full USSR are legitimate polygons and are **kept**. Territorial correctness is
   achieved by *matching each data point to the polity whose polygon fits that
   data's territory* — and creating a more-granular polity when the data is
   granular — **never by editing or shrinking an aggregate polygon.**
3. **Code detects, agents judge.** Deterministic detectors do the cheap,
   reproducible work and attach **numeric evidence**; agents are spent only on
   judgement (verdicts, reconciliation, fixes).
4. **Settle territory from data, not convention.** A territorial verdict must be
   grounded in the data's own magnitudes + spatial containment evidence (see
   `02_territorial_evidence`), not in a remembered labelling convention.
5. **Idempotent & resumable.** Resolved units are marked in the ledger and
   skipped. A run leaves the tree clean so the next run can start immediately.
6. **Auditable.** Every change traces to an issue id, its evidence, and a commit.

---

## Open work is tracked as GitHub issues

Findings that need a decision, a source we do not have, or work that can be
chipped away at independently live in the repo's **issue tracker**, not in
comments or state files. Anything recorded only in a CSV or a wiki page tends to
be rediscovered by accident later.

The state files below are **queues**, and each has an issue that explains what to
do with it:

| file | holds | issue |
|---|---|---|
| `state/assertions.json` | pending assertions to verify | #7, #8 |
| `state/assertion_triage.csv` | the pending queue tiered by what deterministic evidence says about it, with a `verify_order` (written by `12_triage_assertions.py`; a snapshot, because `assertions.json` is gitignored) | #7 |
| `state/assertion_nesting_flags.csv` | pairs of same-source assertions whose candidate polygons nest, with the panel's own arithmetic on whether the outer figures can include the inner | #7 |
| `state/quarantine.csv` | verdicts where two agents disagreed (kept actionable by `reconcile_quarantine.py`) | #20 |
| `state/quarantine_resolved.csv` | append-only audit trail of cleared quarantine rows + why | — |
| `state/new_polity_proposals.json` | proposed polities awaiting sign-off | — |
| `state/suspect_wiki_pages.csv` | pages verification judged wrong or too thin | #19, #25 |
| `state/landuse_corrections.csv` | recoverable bad cells in the FAO land-use series, one row per cell, with an `action` (`replace_value` / `drop_row` / `review_cell` / `review`) saying what an upstream applier may do unattended. `scripts/validate_landuse_corrections.py` re-derives every diagnosis from the row's own numbers | #4 |
| `state/yield_corrections.csv` | single cells whose area x yield is physically impossible | #29, #111 |
| `state/yield_series_corrections.csv` | whole series carrying a scale error, one row per run, with which column moved, the factor that restores the reference yield, and `implied_factor_is_pow10` saying whether that factor really is a decimal shift (it is for 14 of the 28 runs naming a column, so `implied_factor_pow10` alone must not be applied). `repairable_without_source` then says whether the run may be edited WITHOUT the yearbook page, judging the residual against the dispersion the series' OWN clean years show rather than a fixed window: **11 of 39 runs (27 of the 77 flagged cells) are licensed**, and `repair_factor` — an exact 10^n, never the fitted factor — is published for those alone. `scripts/validate_yield_corrections.py` re-derives both tables' every derived column from the numbers in the same row | #111 |
| `state/livestock_corrections.csv` | FAO-1952 meat cells the components/total identity recovers, and carcass weights outside physical bounds | #29 |
| `state/subnational_sums.csv` | fao1952 whole/part blocks where the parts' sum is tested against the stated whole, with an `action` (`mark_aggregate` / `relabel_rows` / `review`). 93 rows are the identity HOLDING, which makes the whole row an unmarked aggregate of its own parts; 4 are the impossible direction. `scripts/validate_subnational_sums.py` re-derives every claim from the row's own three numbers | #29 |
| `state/source_conventions.csv` | what a source's labels actually measure, with how it was corroborated and when it was last re-tested — validated by `scripts/validate_source_conventions.py` and re-measured by `11_retest_conventions.py` | #24, #13 |
| `state/trade_mirror_gaps.csv` + `state/trade_mirror_summary.csv` | the doubly-reported FAOSTAT trade flows whose two sides disagree by more than 1000x **with both sides at or above one tonne** — 12,775 of 6,130,052 mirrored flows (0.208%), written by `12_trade_mirror_gap.py` from a pin outside the repo. The absolute floor is the point: 26,915 of the 39,690 flows above 1000x (67.8%) have their smaller side under a tonne, median 0.1 t against a median 532 t, which is a reporting threshold and not a disagreement. No `implied_correct`/`action` column, because a mirror localises the error to the (exporter, importer) pair and has no third quantity to solve for. `ratio_is_pow10` is paired with `ratio_is_halfdecade`, the SAME window applied at 10^(k+0.5) where a factor of ten cannot land: 372 on the decades against 211 on the control (1.76x), which is what turns "2.9% are on a power of ten" from a share into a measurement. `scripts/validate_trade_mirror_gaps.py` re-tests both halves of the screen and re-derives every derived column, including the control and the quotient | #112 |
| `state/trade_mirror_gaps.csv` + `state/trade_mirror_summary.csv` | the doubly-reported FAOSTAT trade flows whose two sides disagree by more than 1000x **with both sides at or above one tonne** — 12,775 of 6,130,052 mirrored flows (0.208%), written by `12_trade_mirror_gap.py` from a pin outside the repo. The absolute floor is the point: 26,915 of the 39,690 flows above 1000x (67.8%) have their smaller side under a tonne, median 0.1 t against a median 532 t, which is a reporting threshold and not a disagreement. No `implied_correct`/`action` column, because a mirror localises the error to the (exporter, importer) pair and has no third quantity to solve for. `scripts/validate_trade_mirror_gaps.py` re-tests both halves of the screen and re-derives every derived column | #112 |
| `state/entrepot_census.csv` | issue 14's census: every layer-B production series whose source LABEL and ITEM are also entrepôt-classified in the modern pin (193 of them), with both halves of the discriminator side by side — the layer-B intensity ratio and whether the source publishes a tonnage with NO companion area (`arealess`, which a port statistic is and a real crop usually is not) beside the modern flow classes and years — plus a `verdict`. Written by `14_entrepot_census.py`. **0 promoted**: the classification is summed over all partners so it can never name the `origin_iso3` a flag needs, its years reach none of layer B's, and on Djibouti itself it names five items and never coffee. `scripts/validate_trade_direction_tiebreak.py` requires any `promote` to exist in `data/final/source_flow_flags.csv` — the file an aggregate actually reads | #14 |
| `state/source_conventions.csv` | what a source's labels actually measure | #24, #13 |
| `scripts/validate_polygons_baseline.txt` | polities claiming a polygon they lack — **empty since 2026-08-13**, the queue is drained | #3 (closed) |

#### The rule for registering a source convention (issue 24)

A convention is not one opinion about one row. `00_intake.py` attaches every matching
entry to the evidence bundle of every assertion touching that source, so it is a PREMISE
inherited by every later verifier, and a wrong one propagates further than any single
verdict. Two rules follow, and both are enforced by
`scripts/validate_source_conventions.py` rather than by good intentions:

1. **Two independent corroborators before it is registered** — a second blind verifier, an
   independent re-measurement, or a documentary source outside the panel — mirroring the
   blind-review requirement for verdicts. The `corroboration` column records which, from a
   closed vocabulary; an entry standing on one verifier must be named in the gate's
   `SINGLE_CORROBORATOR_BASELINE` with the reason, so it is a decision and not an omission.
2. **Every entry has a mechanical re-test.** Most of these claims are magnitude claims, so
   `11_retest_conventions.py` re-runs the measurement behind each one against the current
   layer-B panel and reports whether the CONCLUSION still holds (an error) and whether the
   FIGURES in the `evidence` column still reproduce (drift, fixed by correcting the
   evidence). It cannot run in CI — the panel is gitignored — so the gate checks instead
   that every registered row is covered by a check, which is what stops the file growing
   entries nothing re-measures.

The first full re-test, 2026-08-17, confirmed all seven conclusions and falsified the
quoted figures in three of them; `apply_verdicts.py` was also appending rows with 7 of the
12 columns, which read back as `flow_type` empty — i.e. as production.

### Issue 112's claims, one by one (the trade-mirror disposition)

Issue #112 established that FAOSTAT trade mirrors exist and made a dozen specific numerical
claims about them. `12_trade_mirror_gap.py` (issue #274) and `13_trade_entrepot_direction.py`
(issue #291) answered most of them; re-run against the current pins on **2026-08-17**, both
generators produce **byte-identical** output to what is committed, so nothing below is a
vintage artefact. The disposition, so a reader does not have to reconstruct it from three
issue threads:

| #112's claim | status | measured now |
|---|---|---|
| bilateral pin exists with reporter AND partner codes; 46.8M rows | **confirmed** | 46,807,399 rows; 189 reporters, 220 partners, 559 items |
| 19,868,672 tonnage rows, positive value | **confirmed exactly** | 19,868,672 |
| 6,130,052 flows reported from both sides | **confirmed exactly** | 6,130,052 |
| median relative gap 0.348, exactly equal 13.03% | **confirmed exactly** | 0.3481, 13.03% |
| within 1% 15.10%, within 10% 27.54% | **confirmed exactly** (neither was re-derived by #274) | 15.10%, 27.54% |
| >2× 38.43% (2,356,012); >10× 12.49% (765,546) | **confirmed exactly**, and both are the STRICT counts | 2,356,012 / 765,546 strict; 2,468,283 / 777,153 at `>=` |
| headline: **39,804** flows differ by ≥1000× | **arithmetic right, screen wrong** | 39,804 at `>=`, 39,690 strict — but 26,915 (67.8%) have their smaller side under a tonne (median 0.1 t against 532 t), which is a reporting threshold and not a disagreement. **12,775 investigable** |
| "no accounting convention makes an exporter and importer disagree by a factor of a thousand" | **holds for the 12,775, not for the 39,804** | ratio is unbounded as the denominator goes to zero, so two thirds of the tail is a trace consignment against a real flow |
| histogram over the 178,131 flows ≥100×: 92,969 / 67,882 / 14,383 / 2,501 / 364 / 31 | **confirmed exactly**, and one bin is missing from the issue | a 10^8 bin holds **1** flow; the seven bins sum to 178,131 |
| "21,257 of 178,131 (11.9%) within 5% of a clean power of ten" | **count reproduces, description does not** | 21,257 is `\|log10(r) − k\| < 0.05`, a **±12%** ratio window. "Within 5%" read literally gives **9,604 (5.4%)**. Same mis-description #274 found at the 2% window (2.3% reported as 5.0%) |
| **"the ratios cluster on powers of ten … the same signature as #111's"** | **refuted as stated; a modest real excess remains** | a share is not evidence: a 2% ratio window spans 1.74% of a decade, so ~1.7% lands in it by construction. Applying the same window at **10^(k+0.5)**, where a factor of ten cannot reach, catches **211 of 12,775 (1.7%)** against **372 (2.9%)** on the decades — an enrichment of **1.76×**, i.e. **161 flows**, 1.3% of the set. Real, and nothing like a pile-up. `ratio_is_halfdecade` carries the control per row and the gate re-derives it |
| suggested scope 1, a gap table keyed (reporter, partner, item, year) | **done** (#274) | `state/trade_mirror_gaps.csv`, 12,775 rows, 153 reporters, 402 items, 1986–2021 |
| suggested scope 2, "preferring exports will pick wrong roughly half the time in that tail" | **half confirmed, half refuted** | whep's rule keeps the LARGER side in **50.8%** — a coin flip, so a systematic error would be invisible, which was the point. But where a third quantity decides, the rule is **not** wrong half the time: of 49 flows resolved by availability, it keeps the refuted side in **18 (36.7%)** |
| suggested scope 3, "this is whep-side work" | **still true, and it is the whole remainder** | the 18 refuted flows, the preference rule, the pin and the consumer all live in `eduaguilera/whep` |
| the capital-Q trap | **cannot bite here** | `extdata.require_trade_quantity_codes` filters on element CODES (5910/5610) and asserts they still mean tonnes; five distinct codes spell themselves "Export Quantity" |

**What is left open, precisely.** Nothing in this repository: the screen, the control, the
entrepôt label and the availability tie-breaker are all built and gated. What remains is (a)
the **18 flows** where availability refutes the side whep keeps — a change to
`R/bilateral_trade.R`'s preference, which is whep-side; (b) the **3,864** flows with a
production figure that availability refutes on neither side, and the **8,862** with no third
quantity at all, both of which need reporter reliability or a third-party total that no pin
here supplies; and (c) issue #14's `flow_type`/`is_reexport` column, a layer-B schema question.

### Self-checking arithmetic: what each candidate series actually supports

Issue 29 listed five series that might carry an identity worth exploiting, after
the land-use block showed what one buys. Measured against the current layer B,
they are not equally promising, and one of them does not exist as stated:

| candidate | verdict | measured |
|---|---|---|
| area × yield = production | **exploited** — `07_yield_consistency.py` | physical yield bounds; per-cell and per-run correction tables |
| meat components = stated total | **exploited** — `10_livestock_consistency.py` | holds to the tonne for 204 of 218 country-years; 11 bad cells, all recovered |
| carcass weight within physical bounds | **exploited** — `10_livestock_consistency.py` | 5 of 562 cells outside a species' dressed-carcass range |
| heads × carcass weight = meat | **not available as stated** | standing herd is not annual slaughter (pigs turn over faster than once a year), and `item` = "meat" collapses four yearbook columns under one label |
| crop area ≤ arable land | **weak, and 06 already sees the hits** | only 93 fao1952 country-years have both; extracted crop area is a median 15% of arable land, so the bound is slack, and multiple cropping lets it exceed 1 legitimately. The two hard breaches (Netherlands 1951, Germany Western 1951) are both already land-use residuals |
| sub-national parts sum to the whole | **exploited** — `12_subnational_sums.py` | the identity holds EXACTLY on 93 of the 128 (table, item, indicator, unit, period) keys carrying a whole and ≥2 of its parts, and no key at all lands between 0 and 1. 4 keys have parts exceeding their whole, 2 recovered as a label spillover. Only `fao1952` has the structure. The earlier "needs a curated map" reading (75 candidate parents, 291 co-occurrences) came from a bare prefix test over all five sources: filtering composites (`and `, `& `, `Inc `), footnote-marker suffixes, and requiring one row per label per key leaves 28 real families, and keying on the TABLE as well as the year is what makes them comparable |
| trade mirrors | **screened, not recoverable** — `12_trade_mirror_gap.py` | 6,130,052 doubly reported flows, median relative gap 0.348 (an expected CIF/FOB-and-transit gap, not a defect rate). The tail needs an ABSOLUTE floor as well as a ratio: 67.8% of the 39,690 flows above 1000x have their smaller side under a tonne. Both sides >= 1 t leaves 12,775 (0.208%), diffuse over 153 reporters and 402 items, and 2.9% land on a power of ten against 1.7% on a matched half-decade control (1.76x) — so this is not #111's class and no direction can be derived from the pair alone |
| sub-national parts sum to the whole | **open — needs a curated map** | a label-prefix test over layer B's 671 labels finds 75 candidate parents but only 291 parent/child co-occurrences in one (source, table, item, year) block, and most candidates are false (`Netherlands`/`Netherlands Antilles`, `New`/`New Zealand`); median children/parent ratio 0.25 |

**The cross-cutting finding is the error MODE, not the series.** In the FAO-1952
extraction the characteristic fault is a dropped leading `1` — the cell is exactly
1,000 units low. All eleven meat-table mismatches are that, and so are seven of
the land-use residuals in `landuse_corrections.csv` (NLD 1951, JPN 1951, ECU 1949,
GBR 1951, LBR 1948, HUN 1947, SLB 1949). `06_landuse_consistency.py` detects them
but diagnoses none, because its diagnoses (`digits prepended`, `decimal point
dropped`) all describe a value that came out too LARGE. Netherlands 1951 arable
land is recorded as 43 against an implied 1,043 and lands in the table as
`(multiple)`. Extending 06's diagnosis set is issue #4's work, not #29's.

Useful label combinations: `decision-needed` (blocked on a judgement call),
`blocked-on-source` (needs a GIS/reference source we lack), `guard` (a check that
stops a class of error recurring), `backlog` (multi-item, chip away).

## State model — the review ledger

`state/review_ledger.csv` persists what has been reviewed, so re-runs skip
resolved work. Two kinds of review unit:

| unit | key | status values |
|---|---|---|
| **match** (a data label → polity assertion) | `source_label` + `polity_code` | `unreviewed` · `correct` · `issue` · `fixed` |
| **polity** (wiki/extent correctness) | `polity_code` | `unreviewed` · `correct` · `issue` · `fixed` |

Columns: `unit_kind, key, status, issue_id, evidence_hash, protocol_version,
last_run, last_commit`.

- A run **only processes** `unreviewed` units and `issue` units whose fix is not
  yet verified. It **skips** `correct` and `fixed`.
- `evidence_hash` = hash of the deterministic evidence for that unit (all its
  current findings/flags: types, row counts, year spans, sources — computed by
  `01_`/`02_` and stamped onto every finding/flag they emit). A banked
  `correct`/`fixed` unit is skipped **only while the ledger's hash matches the
  unit's current evidence**. If the underlying data changes (hash differs) —
  or the row was banked without a hash — the unit is automatically re-opened
  and resurfaces with a `reopened:` note.
- Banking rules: `correct` verdicts are banked **with** the unit's
  `evidence_hash` (the Cleanup phase copies it from the audited finding/flag);
  `fixed` rows are banked **without** one on purpose — the finding should be
  gone after the fix, and if it ever resurfaces the missing hash reopens it for
  one re-audit, which re-banks it with a fresh hash.
- `protocol_version` = which **rules of verification** the row was banked under
  (assertion rows only; see below). The hash reopens a row when its *data*
  changes, the protocol version reopens it when the *rules* change.
- `WHEP_LEDGER_BACKFILL=1` (env, both `01_` and `02_`): bootstrap mode — banked
  rows with an *empty* hash get the unit's current hash written into the ledger
  instead of reopening. Only for trusted states (rows banked right after their
  review, before hashing existed).

This is what implements your requirement: *"if a row was identified as correctly
matched, the agent should skip it next run"* — and it self-heals when inputs change.

---

## Assertion verification (source onboarding)

The deterministic pass only ROUTES a label to a candidate polity (alias → iso →
name + year containment); it cannot know whether the source's *reporting
territory* under that label equals the polity's territory (union/empire scope,
boundary vintage, combined reporting, wrong split basis). That judgment is done
**once per assertion** — a distinct `(label, source, year_segment) → polity`
claim — and banked. 190k layer-B rows collapse to ~1,030 assertions.

```
00_intake.py           any table (label+year[+iso+value+item]) -> deterministic
                       pass (matchlib.py, shared with 01) -> state/assertions.json:
                       one EVIDENCE BUNDLE per assertion (magnitudes, neighbor
                       segments, candidate meta, evidence_hash, ledger status).
                       Pass --indicator-col when the source reuses ONE item code
                       for several measures, or the bundle's median is taken
                       across incommensurable series (issue #13: FAO-1952's
                       single population item code holds total population,
                       agricultural population and population economically
                       active in agriculture; 80 layer-B item codes carry >1
                       indicator). Opt-in, because qualifying a series changes
                       the evidence hash and REOPENS its banked verdicts.
verify_assertions      one economic-historian agent per pending assertion ->
  .workflow.js         verdict {confirm|reroute|split_reroute|new_polity|
                       not_a_polity|uncertain} + confidence + confirm_kind
                       (verified_equal vs best_available) + evidence_used + basis.
                       A BLIND second verifier re-derives every non-confirm,
                       low-confidence verdict and a 1-in-review_sample slice of
                       confident confirms — it never sees the first verdict, and
                       code compares verdict+target; mismatch -> quarantine.
                       The reviewer is DECORRELATED from the verifier — a
                       different model (opus vs sonnet) under a rotated lens —
                       see "Decorrelating the blind review".
                       Writes state/<args.out> (nothing applied).
16_source_splices.py   where a series switches SOURCE mid-stream, does the value stay on the
                       same scale? Layer B gives every (country, year, item, unit) cell exactly
                       ONE source — zero of 179,096 cells carry two — so a multi-source series
                       is SPLICED and each splice is a seam. 373 seams move the value >30%, 30
                       by >100x. Nine countries show tobacco jumping x101 at a mitchell->iia
                       seam and back at the return seam (Japan 86,000 t -> 8,705,400 -> 84,000),
                       i.e. 40 IIA tobacco cells are implausibly large (logged as
                       iia-tobacco-implausible-magnitudes; the x101 factor holds only where the
                       comparison year is ADJACENT, so it is not a licence to rescale). --write
                       refreshes the TRACKED state/source_splices.csv validate_source_splices.py reads
17_constant_runs.py    does a series repeat one value for years in a way its own resolution
                       refutes? A flat line breaks no magnitude bound, opens no year gap and
                       crosses no seam, so nothing else looked for it — but the rows carry ZERO
                       VARIANCE and read as "unchanged" when nobody knew. Only self-refuting runs
                       count: argentina soybeans resolves 2 ha then sits at exactly 1,000 for 11
                       years; denmark potatoes reads 54,000 for a decade in a series carrying
                       54,100. 246 runs, 1,619 rows, 210 series (juan 1,035, iia 522, mitchell 62;
                       fao1952 nil, as its values are non-integer and have no coarse grid to sit
                       on). --write refreshes state/constant_runs.csv for validate_constant_runs.py
18_isolated_spikes.py  does one year read many times its own neighbours? 05_magnitude_screen.py
                       screens series MEDIANS, so a single bad year is invisible to it: iia
                       cameroon groundnuts runs 61,000 / 620,004,098 / 62,000 ha, median 71,000,
                       against a country of ~47.5M ha. No source seam either — spike and both
                       neighbours are one source. 21 spikes >=20x BOTH neighbours. `indicator` MUST
                       be in the series key: without it 110 hits, 89 fao1952 artefacts comparing
                       indicators rather than years. 342 series unorderable (#367) are skipped and
                       counted. --write refreshes state/isolated_spikes.csv
19_composition_overlaps.py
                       which registered whole/part pairs actually get data on BOTH sides, by ANY
                       routing? The composition gate's double-count arm read only the alias map,
                       but just 205 of 832 label->polity routings come from an alias — 627 (75%)
                       resolve by iso/name/tokenset, and a part reached that way was invisible.
                       13 real overlaps were hidden: AOI<-ERI (66 shared cells), IDN<-its three
                       island groups, JPN<-RYU, MASG<-SGP, SYL<-LBN, AEF<-GAB/CAF/TCD. It also
                       DERIVES separate_series vs sum_risk by counting (item, unit, year) cells on
                       both sides, which used to rest on trust. --write refreshes
                       state/composition_overlaps.csv
20_item_provenance.py  which raw IIA label does each ITEM SERIES come from? 15_label_provenance.py
                       asks this per label; a label can be right for one commodity and wrong for
                       another, and the alias key has no item dimension, so no label-level reroute
                       can fix it. 11 labels mix: australia's `p` is CHRISTMAS ISLAND phosphate,
                       french polynesia's is MAKATEA, syrian arab republic carries Lebanon in COTTON
                       only, usa's `n` is `usa and canada`. Needs the raw extract AND the panel.
                       THE DISTINCTNESS FILTER IS NOT OPTIONAL: >=6 distinct values, or a few round
                       numbers match anything (unfiltered 43 labels, incl. cameroon <- new zealand).
                       --write refreshes state/item_provenance.csv
21_item_product_switches.py
                       does one item series draw on several raw PRODUCTS, switching year to year?
                       australia's `sugar raw centrifugal` alternates cane and BEET (x0.01 down,
                       x873 back), 12 of 33 cells at ~1/300 of the series; sweden's `p` alternates
                       superphosphate and basic slag, so `p` is not a P2O5 total. No source change,
                       so no splice seam; values plausible for their own product, so no magnitude
                       flag; item name constant, so nothing keyed on it notices. Recorded ONLY on
                       oscillation (A...B...A) — comparing product medians confounds this with
                       growth and gave 28 instead of 9. --write refreshes
                       state/item_product_switches.csv
22_item_equivalences.py
                       which raw IIA product does each layer-B ITEM stand for, and is that mapping
                       approved? `wheat`<-spelt/meslin, `flax fibre and tow`<-linseed and `p`<-
                       fertiliser materials were all found by hand; this makes every (item, raw
                       product) pair carry an explicit verdict so the next one fails a gate. Found a
                       fourth on its first run: `other sugar crops n e c`<-`citrus fruits: other`.
                       96 pairs: 24 renames, 51 aggregations, 4 defects, 17 unresolved. --write
                       MERGES: existing verdicts and notes are preserved and only the counts
                       refresh, because overwriting a hand-adjudicated column from a fresh
                       measurement has reversed decisions here before
                       in CI, since the panel is gitignored. Does NOT decide the cause of any
                       one seam: unit mismatch, different coverage and different item definitions
                       are probably all present, and separating them needs the sources.
15_label_provenance    which RAW source label is each layer-B label actually made of? Layer B
  .py                  carries 164 IIA labels; the raw extract carries 403, and nothing here
                       records which went where. Most of that collapse is a benign colonial
                       rename (`french algeria` -> `algeria`); some of it merges DIFFERENT
                       TERRITORIES and is invisible to every other check, because the polygon is
                       stable, the page is coherent and a national series looks plausible at
                       either scale. Fingerprints each label by its (year, value) set and matches
                       against the raw, PRODUCTION-SIDE ONLY (trade rows outnumber production 3:1
                       and produce false matches), then classifies: MIXED (two territories in one
                       label), REDIRECTED (a different name, needing a human to say whether it is
                       a historical rename or a different place), UNDER-EXPLAINED. Found issues
                       312, 315 and the viet nam quarantine. NOT a gate — the raw extract lives
                       outside the repo; SKIPs when absent. `--label X` for one label in full;
                       `--write` re-derives the TRACKED state/iia_label_provenance.csv that
                       validate_iia_label_provenance.py enforces, so tool and table cannot
                       drift — they already did once, when a hand-rolled derivation kept a
                       share-ratio test this script had replaced with a union-gain test.
                       `--assertion 'label|source|LO-HI'` measures ONE assertion's own span,
                       which is what verification actually asks. A label-level signal averages
                       over all years and misses a problem confined to one era: `russian
                       federation` reads `redirected -> ussr` overall, yet its 1909-1913 values
                       have NO dominant source (`russia in europe` 17%, `russia` 13%, `russia in
                       asia` 12% — the empire plus both halves), while 1922-1940 is cleanly 73%
                       `ussr`. Likewise `serbia|iia|1909-1911` is 86% `kingdom of serbs, croats
                       and slovenes` — a state that did not exist yet.
                       `--write-assertions` writes the TRACKED per-assertion table that
                       validate_iia_label_provenance.py prefers over the label table: 247 IIA
                       assertion keys, each measured on its OWN span. It both removes false
                       refusals (`libya|iia|1943-1945` is 100% whole `italian libya` while the
                       LABEL is mixed) and adds true ones the label view averaged away
                       (`china mainland|iia|1922-1931` is `china` + `japan: kwantung leased
                       territory`; `syrian arab republic|iia|1922-1945` is `french syria and
                       lebanon` + `french syria` over 358 values). Both modes apply the SAME
                       co-occurrence and dominance tests: two sources count as concurrent only
                       if each supplies values UNIQUE to it in the same year, and a source is
                       DOMINANT only at 1.5x the chance floor. Without the first, `samoa` read
                       `mixed` when it is `british samoa` then `new zealand western samoa` --
                       one territory renamed. Without the second, `equatorial guinea` reported
                       `bulgaria` as its dominant source, tied at 26% with the plausible one and
                       crowned by an alphabetical tiebreak.
select_tranche.py      picks the next batch to verify: highest-exposure assertions
                       that are pending AND have no banked verdict. Status alone is
                       NOT the filter — apply_verdicts.py writes the ledger, and
                       until 00_intake.py re-runs, a just-verified assertion still
                       reads `pending` (49 do right now). The authority is
                       verdicts_applied.jsonl, whose key is NESTED at
                       record["verdict"]["key"] — reading it top-level yields None
                       for every record, an empty exclusion set, and a re-run of the
                       batch you just finished. Also reports, without selecting,
                       assertions whose candidate no longer exists. --json emits the
                       bare array for the workflow's `keys`. Not a gate.
review_stats.py        measures the review itself out of the banked archive:
                       coverage, coverage of confident confirms (the class the
                       sampler can skip), agreement sliced by model pair and by
                       lens, and the disagreements. --audit-sample N writes a
                       deterministic human-audit sample. Not a gate.
apply_verdicts.py      deterministic execution with contract validation — reroute
                       target must EXIST, must not be retired/superseded, and must
                       COVER the observed span; split_reroute segments must tile it
                       contiguously; confirm must echo the candidate; faostat
                       reroutes -> quarantine (they need a match.R route); a
                       verified_equal resting only on an unreviewed wiki page is
                       downgraded to best_available; a verdict whose
                       verified_evidence_hash no longer matches is refused as
                       STALE. Then:
                       confirm -> ledger correct+hash · reroute -> year/source-scoped
                       alias row + ledger fixed · not_a_polity -> ignored_labels.csv ·
                       new_polity -> new_polity_proposals.json (feed new_polity
                       .workflow.js) · uncertain/disagreement -> quarantine.csv
reconcile_wiki_queues  housekeeping for the two wiki findings queues, which apply_verdicts.py
  .py                  only ever APPENDS to. Drops rows whose polity is gone or is now
                       retired/superseded, and collapses several assertions' findings about
                       ONE page to one row per (page, finding) — keeping the longest text and
                       sending the rest to state/wiki_findings_resolved.csv rather than
                       discarding them. Prints each kept page's measurable state (bytes,
                       source citations, dated note) so `inadequate` can be triaged without
                       opening 30 files. Does NOT judge whether a `wrong` finding still
                       holds — that is prose. Idempotent; --dry-run. First run: BRA-1800-2025
                       was flagged `wrong` on 2026-07-27 for naming a successor that did not
                       exist, which exists now, and JAM-1800-2025 for a claim its page no
                       longer makes — anyone working the queue top-down would have re-fixed
                       two correct pages first.
reconcile_quarantine   housekeeping: drops quarantine rows whose situation is
  .py                  resolved — ledger now `correct`/`fixed` (banked), or the
                       assertion no longer routes to the quarantined `candidate`
                       (route_changed: a new polity, an alias or a matcher fix
                       moved it, so the recorded dispute is about a routing that
                       no longer exists). Route read from assertions.json when
                       present, else re-derived through matchlib; unresolvable
                       rows are KEPT. Every dropped row is appended to
                       state/quarantine_resolved.csv with reason + date and
                       printed — never silently discarded. Idempotent; --dry-run.
```

Onboarding a NEW dataset = run `00_intake.py` on it (`--source-tag mydata`),
chunk the pending keys (~100/run) through the verify workflow, inspect
`verdicts_pending.json`, run `apply_verdicts.py`. Re-runs cost nothing for
banked assertions; an assertion reopens only when its evidence hash changes —
or when the verification protocol does (next section).

The workflow needs `args.keys`. Get them from `select_tranche.py --json` rather than
filtering assertions.json yourself: `status` is stale between `apply_verdicts.py` and
the next `00_intake.py`, so a status-only filter re-selects assertions that already
have verdicts. The agent verdicts are DECISIONS — apply_verdicts.py never re-derives
them, it only validates executability and records them.

#### Sources onboarded so far

| source tag(s) | prepared by | intake result |
|---|---|---|
| `juan`, `mitchell`, `iia`, `fao1952`, `sa_colonial` | `consolidated_layer_b.parquet` (per-row source column) | 192,670 rows → ~1,030 assertions (88.9% routed on labels alone) |
| `faostat` | separate code-keyed matcher (`write_faostat_area_map.py`), not this intake | — |
| `federico_tena` | `prepare_federico_tena.py` (issue 26) | 27,359 rows → 77.3% routed, 269 assertions (242 pending), 32 labels that never route |

### Re-deriving the layer-B assertion queue

The invocation was not written down anywhere, which cost real time: `assertions.json` is
keyed by polity CODE, so every re-span leaves it naming codes that no longer exist, and
without the command there is no way to refresh it. Measured 2026-08-17 before this was run:
23 assertions carrying 1,925 rows named retired codes, two of them already banked.

```bash
python3 pipelines/polity-autoimprove/01_match_and_findings.py     # rebuild matched_rows.parquet
python3 pipelines/polity-autoimprove/00_intake.py \
  --input pipelines/polity-autoimprove/state/matched_rows.parquet \
  --label-col country --year-col year --iso-col iso3c \
  --value-col value --item-col item --unit-col unit \
  --source-col source --prior-code-col whep_code
```

`--iso-col` and `--prior-code-col` are what separate the production run from a label-only
one (88.9% routed against 67.7% for a source that cannot supply them). Run it to `--out` a
temp file first and diff the assertion count before overwriting state: the queue is the
pipeline's memory of what still needs judging, and a bad regeneration is silent.

After the run above: 1,032 -> 1,073 assertions, stale candidates 23 -> 0.

`prepare_federico_tena.py` is what onboarding a new source actually costs: it
reads the tracked `data/external/federico_tena_polities.xlsx` and writes
`state/federico_tena_intake.csv` (gitignored, regenerable), one row per
(polity, series, year) plus the one magnitude the source carries. `00_intake.py`
itself needed no change. Full measurements, the three kinds of gap the unrouted
labels fall into, and what is still unverified are in
[wiki/sources/federico-tena-2019.md](../../wiki/sources/federico-tena-2019.md).

**Two corrections to the first version of that row, both from issue 26 and both
worth reading before onboarding the next source.** (1) It said 48,569 rows and
67.7% routed. 21,210 of those rows did not exist: the sheet's header is three
merged rows, the prep script took its columns by position one GROUP late, and so
emitted each polity's existence window as an `imports` series — for all 243
polities, including the 97 that carry no trade series at all — while labelling the
real imports `exports` and the real exports `population`, a measure the sheet does
not contain. **Read the header rows, not the first data row.** (2) It said 76
labels never route. 44 of those were the same artefact — polities Federico-Tena
lists and reports nothing for — so a "coverage gap" count was really a polity-list
count. The 32 real ones remain open.

The lesson still generalises: a source whose provenance differs from layer B's
routes worse — 77.3% against **88.9%** for layer B measured the same way on
2026-08-17 (192,670 rows, 994 assertions, label-only, i.e. without the `--iso-col`
and `--prior-code-col` its production run gets and Federico-Tena cannot supply) —
not because the matcher is worse but because it names reporting units — Trucial sheikhdoms, Central Asian khanates,
pre-Confederation Canadian provinces — that no 20th-century source does. That
list is the value.

### Protocol version — reopening when the RULES change

The evidence hash answers "did the data change since we judged this?". It cannot
answer "did the *rules* change since we judged this?" — and they do: `confirm_kind`
was tightened to demand a constant territory (13 assertions had to be re-run by
hand, 2 of 13 flipped), and the anti-circularity rule plus `evidence_used` arrived
after ~100 assertions were already banked. Both times the debt was found by
someone remembering it.

So `verify_assertions.workflow.js` — where the substantive rules live — declares

```js
export const PROTOCOL_VERSION = 1
```

with the bump policy and a version history beside it. The version travels the same
way the evidence hash does, **by script, never by agent echo**: the Save phase's
stamping script (whose text the workflow generates, with the constant
interpolated) writes `protocol_version` onto every verdict, `apply_verdicts.py`
banks that value into the ledger, and `00_intake.py` (via `protocol.py`, which
parses the constant out of the `.js` — the workflow sandbox has no filesystem
access, so the dependency can only run in this direction) marks any banked row
stamped **below** the current version as `reopened`, with a
`[reopened: verification protocol v1 -> v2 …]` note. `apply_verdicts.py` also
warns when it is handed a verdict stamped below the current version and banks it
at *its own* version, so stale work reopens instead of masquerading as current.

Bump it when a verdict's **meaning** changes: the VERDICT schema gains, loses or
redefines a field; the definition of a verdict or of `confirm_kind` changes; a new
obligation is added to the historian prompt; `apply_verdicts.py` starts deriving
something from a field the old verdicts do not carry. Do **not** bump for wording,
examples, models or `review_sample` — a bump costs a full re-verification of every
banked assertion, so it has to buy something. Per-row storage (rather than folding
the version into the hash) is deliberate: the debt is then visible row by row, and
a bump reopens exactly the rows that predate it.

`protocol_version` is empty on rows banked by `01_`/`02_` (a different review
unit, not this protocol) and on the pre-assertion-era **bare-label** ledger rows,
which recorded that a label had been looked at and nothing more.

### Bare-label legacy rows are not banked (issue #8)

A bare-label ledger row carries no `evidence_hash`. `00_intake.py` used to report
any assertion covered only by such a row under its own status, `banked_legacy`, and
skip it. Two things were wrong with that:

* the old ledger never recorded a `(label, source, year-span) -> polity` claim, so
  "banked" asserted something that had not been checked; and
* the fallback keys on the **label**, so it was never a closed set of pre-assertion
  rows — it is a **live catch-all**. Any assertion whose full key is missing from the
  ledger inherits "already reviewed" from a bare-label row, *including segments
  created after that label was reviewed*, by a re-span or a new period. This is
  where the retired-polity bug hid: `ARG-1800-2025`, `GRC-1919-2025`,
  `F248-1920-1991` and 18 others absorbed 7,359 rows while every one of those
  assertions read as banked.

Measured on consolidated layer B (2026-08-17, 190,529 rows after the aggregate
filter, 1,073 assertions) the tier held **158 assertions / 4,635 rows over 89
labels** — `fao1952` 90, `mitchell` 32, `iia` 27, `juan` 9 — and none of its keys
appeared in any `state/verdicts_*.json` or in `verdicts_applied.jsonl`. Its largest
member was `serbia|iia|1920-1944` at **573 rows**, which cannot be a legacy
small-row remainder: the label-level review of `serbia` (2026-07-02) predates the
`SER-1918-1945` segment the key now routes to.

So the branch now yields `reopened`, with a note naming the covering bare-label
row. The tier enters the ordinary verification queue by construction and the
catch-all is closed. Against the ledger as of 2026-08-17 the status counts were
`pending` 778 / `reopened` 176 / `banked` 119, the `reopened` figure being the 158
legacy keys plus 18 ordinary reopens.

`state/verdicts_legacy_chunk3.json` then verified **65** of the 158 at assertion
level — **51 confirms** (`banked` 119 -> 170) and **14 quarantined as
`uncertain`**, leaving **107** in the tier (93 never examined + the 14 that were
examined and could not be decided). The 51 are the exact-territory insular and
colonial tail plus eight aggregates confirmed as `best_available` with an explicit
double-count note; nothing was confirmed `verified_equal` on a draft wiki page
alone.

Two blockers for the remaining pass are recorded, not fixed:

* `iia-layerb-magnitude-scale-inconsistent` — `iia` magnitudes in layer B are not
  on a common scale, so `magnitude_continuity`, one of the protocol's checks,
  cannot be applied to the tier's 27 `iia` assertions, the largest among them
  included.
* `layerb-nested-reporting-levels-one-polity` — a polity can receive **two or more
  nesting levels of the same territory from the same source**. Routing all 189,839
  matched rows through the assertion segments and grouping on `(polity_code,
  source, item, indicator, year, unit)` finds **52 cells holding 110 rows** from
  more than one label, none of the colliding values equal: `papua` + `new guinea`
  on PNG-1949-1975, `china` + `china 22 provinces` + `china manchuria` on the CHN
  chain, `germany` + `germany western` + `germany berlin` on DEU-1920-1938 for 1937
  alone, `japan` + `palau` on JPN-1895-1945, `united kingdom` + `united kingdom
  great britain` on GBR-1921-2025, and others. This is what the 14 quarantined
  assertions are blocked on; each names the missing segment where one exists.

### Decorrelating the blind review (issue 27)

Blind review closes **anchoring**: the reviewer never sees the first verdict, so
agreement cannot be deference. It does not close **correlated error**. Until
2026-08-17 both agents were the same model at the same effort, reading the same
bundle under the *same* instructions, so a failure mode inherent to the model or
to the prompt was reproduced rather than caught — and the agreement rate measured
the pipeline's **consistency**, not its accuracy.

What the archive actually says (`review_stats.py`, over the 159 banked verdicts):

| measured | value |
|---|---|
| banked verdicts carrying a review | 51 of 159 (32.1%) |
| confident confirms second-checked | 48 of 156 (30.8%) |
| confident confirms **never** second-checked | 108 (69.2%) |
| agreement among reviewed | 48 agree / 3 disagree (94.1%) |
| reviewed verdicts whose correlation can be assessed | **0** |

Three corrections to the issue's own figures. The exposure is **69%**, not the
75-80% it estimated (`review_sample` was 1 or 2 on several runs, so real coverage
beats the 1-in-5 default). The convergence evidence it cites as 6/6 and 13/13 is
94.1% over the whole archive, not 100% — and the three disagreements are worth
reading one by one, because they are the entire evidential base for "review
catches things":

* `ethiopia|fao1952|1937-1937` and `ethiopia|iia|1938-1938` — genuine
  territorial disputes (Ethiopia proper vs the Italian East Africa aggregate),
  both quarantined, and both later closed by `reconcile_quarantine.py` as
  `route_changed` when the candidate became `ETH-1936-1941`. Neither was ever
  adjudicated on its merits.
* `argentina|juan|1900-1960` — *not* a territorial disagreement at all. Both
  agents chose the same two targets (`ARG-1899-1902`, `ARG-1902-2025`); they
  differed by one year on the boundary, `1900-1902` vs `1900-1901`. The
  verifier's pair overlaps at 1902 and is rejected outright by
  `apply_verdicts.py`'s contiguity contract (`year_start == prev year_end + 1`);
  the reviewer's tiles cleanly. So the one case where the second agent was
  demonstrably RIGHT was an arithmetic slip, not a scope error — which is
  precisely the argument for the deterministic cross-checks issue, and precisely
  what a decorrelated *lens* is unlikely to add much to.

And the last row of the table is the finding that made the issue actionable:
the archive recorded neither the model nor the instructions behind each review,
so "does disagreement rise when the reviewer differs?" was unanswerable from the
data we already had — no experiment was possible, whatever we changed.

So, cheapest first:

1. **Model diversity** — the reviewer runs on a different model than the verifier
   (`review_model`, default `opus`, against `model`, default `sonnet`). Only the
   reviewed ~1/3 pays for the stronger model.
2. **Perspective diversity** — the reviewer gets a different **lens**, rotated
   deterministically by position across `magnitudes` (start from the numbers and
   try to make them refute the routing), `source_documentation` (start from what
   *this publication* meant by the label) and `territorial_history` (reconstruct
   the territory year by year, then test the span). A lens changes where the
   reviewer *starts and what it weights*; it never subtracts a `HISTORIAN`
   obligation.
3. **Lower `review_sample`** — buys coverage linearly, decorrelates nothing.
   Left at 5; use it when the population, not the method, is the worry.
4. **A human audit sample** — the only thing that yields a real error rate.
   `review_stats.py --audit-sample N` writes a deterministic (key-hash-seeded)
   sample of banked confirms with blank `human_verdict`/`human_reason` columns.
   It must be scored **by hand**: an agent scoring it reintroduces exactly the
   correlated error the sample exists to measure, which is the flaw in relying on
   `audit_matches.workflow.js` for this.

Every verdict record now carries `verify_model`, `review_model` and
`review_lens` (they ride the archive through `apply_verdicts.py`), and
`review_stats.py` slices agreement by both — so the same-model **5.9%**
disagreement rate above (3 of 51; **3.9%** if the Argentina boundary slip is
excluded as non-territorial) is the baseline the decorrelated reviewer is
measured against. **None of this is a `PROTOCOL_VERSION` bump**: the bump policy excludes
models and sampling, and a lens cannot change what a verdict *means* — the
VERDICT schema, `confirm_kind` and every `HISTORIAN` obligation are untouched, so
no banked assertion is reopened by it.

What remains open: whether decorrelation *works*. One would expect a
decorrelated pair to disagree MORE often than 5.9% if correlated error was
real, and less often only if the reviewer's lens is simply better. Neither
reading is available until enough reviews are banked with the new metadata, and
the honest error rate needs option 4 — a human, scoring a sample.

---

### Triaging the backlog — what deterministic evidence can and cannot settle (issue #7)

`12_triage_assertions.py` reads `assertions.json` and answers, without spending a
token, where the historian budget should go. Measured 2026-08-17 against a fresh
`00_intake.py` run on the current main (**1,073 assertions; 796 pending/reopened
carrying 94,925 of 189,839 routed rows** — issue #7's "723 of 1,031" is stale, the
queue GREW as polities and aliases were added and as banked rows reopened on
changed evidence):

| tier | assertions | rows | what it means |
|---|---:|---:|---|
| `territory_basis_wrong` | 17 | 3,184 | the panel's own arithmetic rules out the routing's premise (below) |
| `nested_reporting` | 120 | 5,563 | same source reports an outer AND an inner territory in overlapping years |
| `boundary_year` | 1 | 10 | span ends at the candidate's exclusive `end_year` — the accepted convention, not a defect |
| `weak_route` | 122 | 12,535 | name/tokenset only: no iso agreement, no human-written alias |
| `precedent` | 256 | 36,495 | a ranged alias or a banked sibling already decided the ROUTING |
| `thin` | 53 | 272 | ≤5 rows or one distinct year |
| `bulk` | 227 | 36,866 | no deterministic signal at all |

**Deterministic evidence cannot CONFIRM an assertion, and that is structural.** An
assertion exists precisely because the deterministic pass finished: `matchlib`
decided the route and recorded it. What is pending is whether the SOURCE's
reporting territory equals the polity's territory — and the repo's tables are one
side of that comparison, so no check over them can close it. 659 of the 796 have
no deterministic signal whatever; those genuinely need the historian pass.

**What it CAN settle is the opposite direction.** Every layer-B unit is extensive,
so if a label's figures included a nested territory the same source reports
separately, `outer >= inner` would hold in every shared (item, unit, year) cell.
234 same-source nesting pairs exist; in **20 of them inclusion is arithmetically
impossible**, so the source is reporting the outer EXCLUSIVE of the inner and it
is the polity's territory, not the routing, that is wrong. Examples, all
re-derivable from `state/assertion_nesting_flags.csv`:

* Juan's `united kingdom` → `GBR-1800-1921` (313,550 km², Great Britain **and**
  Ireland) while Juan reports `ireland` separately: Irish flax area 22,436 ha
  against the UK's 259 ha in 1901, UK below Ireland in 87 of 637 shared cells,
  concentrated in potatoes, flax and linseed. Juan's UK is Great Britain.
* IIA's and Mitchell's `japan` → `JPN-1895-1945` (626,507 km² — the empire, i.e.
  metropolitan Japan + Korea + Taiwan) while both report Korea and Taiwan
  separately: Japan below Korea in 220 of 394 shared IIA cells (cotton, hemp,
  sesame, soybeans). Those series are metropolitan Japan.
* FAO-1952's `germany` 1938 below its own `germany western`/`germany eastern`;
  `indochina viet nam` below Cambodia and Laos; IIA's `india` below Burma;
  Mali below Upper Volta in IIA and Mitchell.

**13 of those 20 pairs involve an already-BANKED assertion** — Juan's UK/Ireland is
banked on both sides — so the screen contradicts recorded verdicts and those rows
need re-verification, not first verification.

The nesting screen (the flag, not the arithmetic) also independently re-finds the
Ethiopia/`AOI` fold-up that the reading pass found by hand — Mitchell's `ethiopia`
-> `AOI-1936-1941` (1,712,684 km²) against its own `somalia` -> `ITS-1908-1960`
(464,286 km², wholly inside it), 1936-1940. Those two labels share no comparable
(item, unit, year) cell, so the arithmetic returns `no_shared_cells` and the pair
is only a flag; it is the calibration for the screen, not a second settlement.

The inclusion test is the first concrete instance of the deterministic
cross-checks issue #10 asks for (sums, double-counts, continuity) applied to the
assertion queue rather than to a single polity.

Consistency is NOT proof: the 55 pairs where `outer >= inner` holds everywhere
look exactly like a genuine double count would, and 118 pairs share no comparable
cell. Those stay for the historian.

Two more bounds worth knowing before buying tokens: only **66 of 796** candidates
have a `reviewed` wiki page, so for the other 92% a confirm resting on the page
alone is recorded as `best_available` (the anti-circularity rule in
`apply_verdicts.py`) — the pass buys routing assurance, not territorial proof. And
of the 159 verdicts applied so far only **3 (1.9%)** changed a routing, so the
queue's value is mostly in the record it leaves, not in corrections found.

## Pipeline stages

```
                          ┌── ledger (state/) ──┐  skip correct/fixed
                          ▼                      │
 0  MATCH + EVIDENCE   (code) ────────────────────────────────►  review units
      run matcher (pre1961-matching core, generalised);          + numeric evidence
      attach territorial evidence (magnitudes + spatial
      containment); filter out ledger-resolved units
                          │
 1  AUDIT             (agents, fan-out) ──────────►  per unit: verdict
      one agent per unreviewed unit. verdict = `correct`           → ledger=correct
      (numeric-evidence-grounded) OR emit an ISSUE REPORT (json).   → issues[]
                          │
 2  RECONCILE         (1 agent) ──────────────────►  harmonized_issues[]
      ingest all issue reports; dedupe/merge repeated &
      related issues; consolidate evidence; assign fix_type;
      order by dependency (polity fixes before re-matches).
                          │
 3  FIX               (agents, fan-out, worktree-isolated) ──►  change-sets[]
      ONE agent per harmonized issue. Applies the wiki-first
      methodology for its fix_type. Emits a structured CHANGE-SET
      (wiki edits + DB row + polygon decision) — does NOT commit.
                          │
 4  INTEGRATE         (serial integrator) ────────►  one commit per issue
      apply each change-set in dependency order; regenerate DB
      rows from wiki where needed; RE-RUN the matcher to verify
      the issue is resolved (regression); commit one issue at a time.
                          │
 5  CLEANUP           (code) ─────────────────────►  clean tree + report
      update ledger (issue→fixed, verified→correct); write
      run_report.md; ensure working tree is clean for next run.
```

### FAOSTAT-era findings (origin `faostat`)

Stage 0 (`01_match_and_findings.py`, Stage 1b) also ingests the residual
queue of [`pipelines/faostat-era-matching`](../faostat-era-matching/README.md)
— the FAOSTAT (1961+) reporting universe matched by numeric area code — into
`findings.json`, tagged `sources: ["faostat"]`. These are audited and fixed by
the same loop, with two FAOSTAT-specific rules the workflow enforces:

- **Never fix a FAOSTAT finding with an `applied_aliases.csv` row.** That file's
  `source=faostat` rows are regenerated (replace-by-source) by
  `faostat-era-matching/match.R`, which routes by area code and ignores
  hand-added aliases. Fix instead with a **new polity** (wiki + CSV — `match.R`'s
  iso3-family lookup then routes the area) or a **`match.R` route**
  (`manual_prefix` for a different-prefix chain, `manual_span_routes` for
  overlapping periods, grounded in data magnitudes).
- **Integrate re-runs `match.R`** whenever a FAOSTAT-origin fix was applied, so
  the regenerated routing (and `findings.json` via Stage 1b) reflects it before
  Verify checks resolution. This needs the WHEP pins cache (`WHEP_REPO`); without
  it, FAOSTAT fixes stay open for the next run rather than being falsely banked.

### Why change-sets + a serial integrator (not parallel commits)

Fix agents run concurrently, but `polities_database.csv` is a **single shared
file** and git commits to one branch **cannot** be made in parallel without
clobbering. So fix agents work in isolated worktrees and **return** their changes;
the integrator applies them sequentially and makes **one commit per issue**. This
keeps your "one issue → one fix → one commit" intent while staying atomic and
conflict-free. Wiki pages are one-file-per-polity so they rarely conflict; the
CSV and `match.R`/`common_names` patches are the shared files the integrator owns.

---

## Issue report schema (stage 1 output)

```json
{
  "issue_id": "<stable hash of subject+type>",
  "type": "rematch_alias | polity_dates | polity_extent_polygon | missing_polity | double_count | data_error",
  "subject_polity": "<polity_code or null>",
  "subject_label":  "<source data label or null>",
  "period": "<years the issue concerns>",
  "description": "<what's wrong, one paragraph>",
  "evidence": { "magnitudes": [...], "contained_with_concurrent_data": [...], "sources": [...], "rows": N },
  "proposed_fix": "<the agent's suggested remedy>",
  "confidence": "high|medium|low"
}
```

## Harmonized issue (stage 2 output)

A deduplicated, self-contained unit of work: merges every issue report touching
the same subject, unions their evidence, picks the single correct `fix_type`,
and records `supersedes: [issue_id...]`. One harmonized issue → one fix agent →
one commit.

---

## Fix methodology by `fix_type` (all wiki-first where a polity changes)

| fix_type | what the fix agent does | touches |
|---|---|---|
| `rematch_alias` | data label routes to the wrong/none polity but the **right polity exists** → append an `alias_row` to **`state/applied_aliases.csv`** (the file `01_match_and_findings.py` actually reads). No entity change. Optionally also patch the legacy `pre1961-matching/match.R`. | `state/applied_aliases.csv` (+ optional `match.R`) |
| `polity_dates` | a polity's start/end is wrong for the data → **wiki first** (research + update the page's dates & rationale), then the CSV row, then predecessor/successor links. | `wiki/polities/<code>.md` → CSV |
| `polity_extent_polygon` | polygon is wrong-extent for the data it serves → **wiki first** (document the contemporaneous territory + km²), then choose/generate the polygon (CShapes/GADM/Cliopatria/Paine/CHGIS, union, or constructed). Aggregates are kept; route granular data to a granular polity instead. | `wiki/polities/<code>.md` → CSV + polygon |
| `missing_polity` | data has no covering polity → create the wiki page (per `pre1961-matching` "Wiki page requirements"), then CSV row, then polygon. | new `wiki/polities/<code>.md` → CSV + polygon |
| `double_count` | a parent polity's polygon contains sub-territories that report separately → **do not edit the aggregate**; re-route the granular data to the contained polities and document the aggregate's scope on its wiki page. | matching + wiki note |
| `data_error` | a value/unit looks wrong (not a territory issue) → flag in a report; **never silently edit source data.** | report only |

### The alias table: `(name, source, year-range) → polity`

`state/applied_aliases.csv` columns: `source_label, source, year_start, year_end,
common_name, polity_code, confidence, basis, observed_rows` (renamed from
`original_name`/`target_polity_code`/`rows` by issue 95; the whole set is pinned by
`scripts/validate_schema_contract.py`). A single label can route
to **different polities by year and/or source** — empty `source`/`year_*` = applies
to all. `01_match_and_findings.py` picks the most specific matching rule per data row
(year- and source-qualified rules beat blanket ones). Example: `Germany Western`
resolves to West Germany **only for 1949–1951**; its 1937–48 rows stay an open finding.

### What a source label actually means (avoid false precision)

A label like "Germany Western" is **the source's own reporting unit**, with the
source's (often stable, possibly idiosyncratic) territorial definition — it need
**not** correspond to our period splits (Reich / occupied / FRG). Forcing it onto
our boundaries can be *false precision*: the reporter may have meant one consistent
thing across all its years (e.g. some occupied+unoccupied conception), not our
1945/1949 entities. **Do not assume the label maps to our ontology.** Determine what
territory it actually covers by:

- **(a) Source footnotes / explanatory notes** — a **corroborating hint, never authoritative.**
  Extracted footnotes can be OCR-garbled, matched to the wrong row, or mis-attributed, so
  they support or question a verdict but never decide it alone; always weigh them against the
  data. Wired in as `source_notes` (from `state/iia_territorial_notes.csv`, ISO-joined). The
  Nextcloud `Sources/datasets/textracted_footnotes/` tree (~1,642 dirs, currently unsynced)
  is a richer future input.
- **(b) Data-magnitude analysis.** Compare the label's reported staple magnitudes
  against candidate territories' expected figures to *infer* the extent (the method
  that settled "Japan = metropolitan, not empire"; see `02_territorial_evidence.py`).

Until a label's extent is established, prefer a **low-confidence / `assumed` basis**
alias (or leave it an open finding) over a confident mapping. When the source's unit
matches **no** existing WHEP polity, that is a signal to create a polity matching the
**source's** definition — not to shoehorn the data into a polity it doesn't fit.

**The fix agent must research** (web/sources) before changing a wiki page, and
the wiki page edit must satisfy the `## Territorial extent` requirements already
defined in [`pre1961-matching/README.md`](../pre1961-matching/README.md#wiki-page-requirements):
polygon status, why the entry exists / what data it captures, and a locatable
territory description with km².

---

## Territorial verdict rule (stage 1 & 3)

Audit the polygon of the polity **each data label is matched to** against *that
data's* territory, using the deterministic evidence from `02_territorial_evidence`:

- `staple_magnitudes` — the polity's own reported staple values (with units; FAO
  uses "1000 tonnes").
- `contained_with_concurrent_data` — WHEP polities whose polygon sits **inside**
  this one *and* report data in the same years (spatial containment over
  `data/geodata/polities_polygons.gpkg`). If non-empty, the polygon overstates the
  territory its own data covers — **unless** this polity's magnitudes are large
  enough to actually include the contained ones (compare the numbers).

Remedy is always **re-route or add a granular polity** — never edit an aggregate.

**Intra-span vintage drift (the Cape Colony case).** A polity record carries a
single polygon at one *vintage year*; that polygon represents only that year. A
long-lived polity whose borders changed within its span (e.g. `CAP-1800-1910`,
one polygon vintage 1886, but Cape Colony expanded through the 1800s) cannot be
represented by one polygon. `02_territorial_evidence.py` flags
`polygon_vintage_drift` when data is matched ≥15y from the polygon's vintage over
a ≥25y span. **An agent must never assume territorial stasis across the vintage.**
Remedy: split the polity at the border-change years (each period its own
polygon), or — if no period polygon is available — document the approximation on
the wiki page (direction + rough magnitude), per the `pre1961-matching`
"Note approximations" rule.

## Territory basis (stage 4) — the "assumed-constant border" sweep

`04_territory_basis.py` makes the vintage-drift concern systematic and
DB-wide, answering: *for the years a polity serves, does its polygon
faithfully represent that period's territory, or is it an assumption?* It
compares each polity's polygon vintage (`polygon_feature_year`) to its own
period `[start_year, end_year]` and emits a graded `territory_basis`:

| basis | meaning |
|-------|---------|
| `measured` | vintage falls inside the period and the span is short enough that one polygon is defensible. |
| `assumed_constant` | a single vintage held across a long span (≥25y) — borders may have changed within it. The bulk of historical data sits here. |
| `back_projected` | vintage is **outside** the period (a later/modern, or earlier, border applied to this period) — the clearest "not the real territory" case. Also any `modern_proxy`/`constructed_estimate` polygon. |
| `unassigned` | no polygon — an **honest gap**, never a false territory (policy: never back-project a modern border; `polygon_status=unassigned`). |

Output: `state/territory_basis.csv` (one row per polity). A polity is
`priority_review` when it is `assumed_constant`/`back_projected` **and**
independently flagged by stage 02 (magnitude step-change vs sibling period,
README-known mismatch, vintage drift, or aggregate-contains-concurrent-data)
— i.e. there is real evidence its single polygon misrepresents the territory,
as opposed to a long span whose border was genuinely stable. The
`priority_review` set is the input to the periodize/assign-vintage-polygon
remedy (split at border-change years, each period its own polygon).

The default window is **1860–1961** (`WIN_LO`/`WIN_HI`), the span where WHEP
back-projects modern country borders onto historical production/trade data.

---

## Running

```bash
# deterministic prep (no agents)
python pipelines/polity-autoimprove/01_match_and_findings.py     # match + review units, filtered by ledger
python pipelines/polity-autoimprove/02_territorial_evidence.py   # attach numeric territorial evidence
python pipelines/polity-autoimprove/04_territory_basis.py        # classify each polity's territory_basis (1860-1961 sweep)
python pipelines/polity-autoimprove/reconcile_quarantine.py      # clear resolved quarantine rows (--dry-run to preview)
python pipelines/polity-autoimprove/12_triage_assertions.py      # tier the pending assertion queue + the nesting/inclusion screen (needs 00_intake first)

# the agent loop (Workflow tool) — audit -> reconcile -> fix -> integrate -> cleanup
#   Workflow({ scriptPath: "pipelines/polity-autoimprove/autoimprove.workflow.js", args: {...} })
```

Workflow agents default to **Sonnet / medium effort** (large fan-out; cost; avoids
session limits). Re-run until the ledger has no `unreviewed`/open units.

### Cost control — two independent knobs (and why there's no waste)

The agents **never** audit the 190k data points — stages 01/02 resolve those
deterministically for free. Agents only see the **residual uncertain set**
(findings + territorial flags) that 01/02 could not settle, and the **ledger
removes anything already resolved** before the workflow runs. So:

- `max_audit` — caps how many residual units are **audited** this run (default =
  all remaining). The audit set **shrinks every run** because resolved units are
  ledger-skipped, so you never re-audit a unit that was already confirmed
  `correct`. For a cheap validation run, set `max_audit` small — it audits a
  slice **end-to-end** (audit→fix→commit→ledger), not "audit everything then
  discard".
- `max_issues` — caps how many issues are **fixed/committed** this run.

A run's cost ≈ `min(max_audit, remaining residual units)` audit agents +
`min(max_issues, issues found)` fix/integrate agents. Across runs the residual
set converges to empty.

---

## Invariants a run must leave true (so the next run is clean)

1. Working tree clean (every change committed; no stray files — see note below).
2. `review_ledger.csv` updated: audited→`correct`, fixed issues→`fixed`.
3. `run_report.md` written: units reviewed, issues filed/merged/fixed, coverage %.
4. The matcher re-run shows each fixed issue's data now matches correctly.

> **Housekeeping note:** agents must write only to their declared outputs. Stray
> files (e.g. wiki stubs left untracked outside an issue's commit) break the
> "clean tree" invariant. The integrator is the only stage that commits.

---

## Structural-change checklist (split / merge / retire / re-date / create)

A **structural change** is any edit that changes which polities exist or when
they exist: creating a polity, splitting a chain into periods, merging two rows,
retiring/superseding a row, or moving a start/end year. It silently re-routes
data, because the matcher resolves a label by alias → iso3 family + year
containment → name, and none of that is visible in the wiki diff. Four real
failures from one session:

| what happened | which step catches it |
|---|---|
| the Indonesia merge renamed a row to "Dutch East Indies" and **orphaned 23 rows** that had resolved by NAME | 7 |
| the India split typed the new rows `colonial`, so Hyderabad **outranked them and took 36 rows** | 9 |
| the Newfoundland fix put 54 rows of 1948 Canadian data on the wrong side of a boundary — **the total was unchanged** | 6 |
| `ETH-1936-1941` shipped `polygon_area_km2: 1000000`, a rounded placeholder | 3 |

Run the snapshot **before** touching anything — after the edit there is nothing
left to compare against:

```bash
python3 scripts/structural_change_check.py --snapshot   # BEFORE the edit
#   ... make the change (steps 1-4 below) ...
python3 scripts/structural_change_check.py --compare    # AFTER
```

### The eleven steps

| # | step | who |
|---|---|---|
| 0 | `scripts/structural_change_check.py --snapshot` — per-polity matched-row counts, total, resolving labels, areas | script |
| 1 | Write/edit the wiki page(s): frontmatter **and** body, which can contradict each other; say what changed and why | **human/agent** |
| 2 | `python3 scripts/build_database.py` — rebuilds CSV+GPKG and asserts the row count | mechanical |
| 3 | Verify the attached geometry measures what the page claims (equal-area `ESRI:54034`); never write a round placeholder area | mechanical (step 10 checks it) |
| 4 | Mark superseded rows `wiki_status: superseded` **and** `polygon_status: unassigned` | **human/agent** |
| 5 | Re-run the matcher; confirm the **total match count did not drop** | `--compare` §1 |
| 6 | Confirm per-polity counts moved **as intended**, not merely that the total held | `--compare` §2/§3 — reported as REVIEW; only a human can say the movement was the intended one |
| 7 | If the entity's **name** changed, confirm labels that resolved by name still resolve — otherwise add an alias | `--compare` §4 |
| 8 | If a FAOSTAT-era alias targeted a changed code, re-run `pipelines/faostat-era-matching/match.R --accept-diff` | **human/agent** (needs R + FAOSTAT bulk data) |
| 9 | `scripts/audit_family_shadowing.py` — a new row can tie with an existing one on type rank | `--compare` §6 |
| 10 | `scripts/validate_polygons.py`, `scripts/validate_citations.py`, placeholder-area scan | `--compare` §5/§6 (+ CI for the first two) |
| 11 | A `wiki/log.md` entry of kind `decision`, **naming the human who signed off** | **human only** — never an agent's call |

Steps 1, 4, 8 and 11 stay human. Everything else the script does, and it exits
non-zero on: a dropped total, a polity that went from data to zero rows, a label
that stopped resolving, a round `polygon_area_km2` this change introduced, or a
non-zero exit from the shadowing/polygon validators. Per-polity movement and
pre-existing round areas are reported as `REVIEW`, not `FAIL` — they need a
judgement the script cannot make.

### Why it is not in CI

`--compare` needs matched-row counts, which need `01_match_and_findings.py`,
which reads the consolidated layer-B dataset (`WHEP_LAYERB`, ~190k rows) from
personal Nextcloud — not redistributable, so CI cannot see it. It is therefore a
**local** pre/post-change tool and is deliberately absent from
`.github/workflows/validate.yml`; CI keeps running the data-free validators
(`validate_citations`, `build_database --check`, `validate_polygons`,
`audit_family_shadowing`). Issue #17 tracks the CI limitation. The snapshot
lands in `state/structural_snapshot.json`, gitignored like the other per-run
artefacts.

---

## Status / provenance

Methodology authored 2026-06-23. The deterministic detectors and the
resolve/territorial-audit workflows were prototyped under
`scratchpad/layerb_harness` and are being ported here. See the project's
data-source inventory and consolidated layer-B build for the input side.

## New-polity creation (dedicated workflow) + polygon provenance

New-polity creation is **split into its own workflow** (heavier than rematch:
research → wiki → polygon sourcing → DB row; mutates `polities_database.csv` and
writes files, so it uses worktree isolation + serial-integrate). The rematch/audit
loop stays fast and separate.

### Polygon source priority (try in order; never skip ahead without recording why)
1. **Exact historical polygon** — a GIS source with the *actual* territory for that
   entity+period. Check these before anything else:
   - CShapes 2.0 (states + colonial dependencies, 1886+)
   - **Cliopatria / Seshat** (1,618 polities, 3400 BCE–2024 — largely UNTAPPED)
   - CHGIS (China), Paine et al. (precolonial Africa), GHGIS (German historical regions)
   - the repo's existing `data/geodata/polities_polygons.gpkg`
2. **Composed** — union of constituent sub-units' historical polygons (e.g. AOF =
   union of its colonies; a trust territory = union of its islands).
3. **Period proxy** — copy an adjacent-period polygon of the *same* entity, only if
   the territory was essentially unchanged; document the difference.
4. **Modern proxy / constructed estimate** — LAST RESORT, only after confirming 1–3
   don't exist.

### Mandatory provenance (recorded on EVERY new polity — never silent)
- `polygon_source`: database + feature id + vintage year actually used.
- `polygon_method` ∈ {`exact_historical`, `composed_union`, `period_proxy`,
  `modern_proxy`, `constructed_estimate`}.
- `polygon_confidence` ∈ {high, medium, low}.
- Wiki `## Territorial extent`: state exactly what was used and why; for a
  proxy/estimate, give the direction + rough km² difference from the true territory
  and mark it **"ESTIMATE — not authoritative"**.

**Rule:** an estimate is acceptable *only* after confirming a real historical
polygon (steps 1–2) doesn't exist, and it must be flagged loudly so it is never
mistaken for ground truth. Prefer leaving `polygon_status=unassigned` with a
documented reason over a silent modern-borders guess.

## Two detectors that do not work, and why (2026-08-05)

Recorded so they are not rebuilt. Both were attempts to generalise the Canada boundary
fix (issue 15) into a sweep for polity periods that inherited a source's break date
instead of the territorial event.

### 1. "start_year sits on a mid-year CShapes break" — 342 hits, not a defect class

A CShapes step beginning on a date other than 1 January means the source is dating a
mid-year political event. Copying that year into `start_year` makes the polity claim the
whole calendar year, including the months before the event.

**342 live polities do this**, 40+ of them across a >=1% area change. But the vast
majority are simply *true*: `ISR-1967-1979` begins with the Six-Day War (1967/06/10),
`DEU-1990-2025` with reunification (1990/10/03), `YEM-1990-2025` with unification
(1990/05/22). The polity genuinely began mid-year, and assigning the whole calendar year
to it is an unavoidable approximation for annual data, not an error.

What made Canada a defect was not the mid-year break but that **the source dated the wrong
event** — the Newfoundland referendum (22 July 1948) rather than the accession (31 March
1949). That is a historical judgement per case and is not mechanically detectable from the
date. The detector therefore cannot separate signal from history.

### 2. "no source's data supports the declared start_year" — a convention artifact

The idea: if every source's data for a polity begins after its `start_year`, the boundary
may be a year early. On `match_confidence.csv`, restricted to polities with >=2
independent sources:

    live polities with >=2 sources        207
      earliest data year - start_year = +1   107   (51.7%)
      ... <= 0                                12

**A +1 gap in half the database is the boundary-year convention, not a per-polity signal.**
A polity's first calendar year is routed to its predecessor, so the successor's data
begins one year after it starts. Any polity will show +1.

This one produced a wrong conclusion before it was checked: `ITA-1919-2025` (start 1919)
has `iia`, `juan` and `mitchell` all beginning at 1920, which was briefly read as three
independent sources corroborating that its boundary was a year early. They corroborate
nothing — 107 polities have the same pattern.

### What survived, for Italy specifically

The one piece of specific evidence is a magnitude test on the smoothest available series.
Italian livestock across the Treaty of Saint-Germain (signed 1919/09/10, in force 1920/07/16),
where the post-treaty polygon is 5.4% larger (284,652 -> 300,049 km2):

    goats  1918: 3,082,000   1919: 3,080,000   1920: 3,080,000   1921: 3,083,000   (cv 0.020)
    sheep  1918: 11,753,000  1919: 11,744,000  1920: 11,744,000  1921: 11,754,000  (cv 0.034)

No step at either year. A 5.4% territorial gain in mountain-pastoral Trentino-South Tyrol
could not be invisible in goats, so the 1919 and 1920 figures are on the pre-treaty basis.

That supports a **narrow** claim — `ITA-1919-2025` claims calendar 1919 with post-treaty
geometry, a one-year 5.4% overstatement — and **not** the Canada-scale case: unlike
`CAN-1948-2025`, which overlapped a live `NFL-1907-1949` and double-counted 398,084 km2,
`ITA-1919-2025` overlaps nothing (`AUH-1908-1918` ends 1917). On that evidence a breaking
two-code rename is not justified; it is recorded on issue 23 instead.

### The transferable lesson

A "broken" alias may be compensating for a wrong period boundary. The `canada` 1948 alias
was territorially correct while pointing at a polity whose columns did not cover 1948, and
retargeting it would have reintroduced the error it was hiding. **Read the rationale column
before treating an alias as the defect.**
