#!/usr/bin/env python3
"""Tests for the agent harness. Every case here is a regression for a bug the smoke run found.

A harness whose only test is "it produced something" cannot tell a good verdict from a plausible one
built on corrupted evidence -- which is the failure this suite exists to prevent. Each test names the
bug it pins.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


runner = _load("runner")
harness = _load("harness")
repair = _load("repair")


def test_cli_schema_strips_only_what_the_cli_rejects():
    """BUG: the CLI exits 1 on `$schema` and on conditional subschemas.

    The projection must drop those and NOTHING else -- dropping `required` or `properties` would
    stop the model being told the shape at all.
    """
    full = json.loads((HERE / "schemas" / "routing_verdict.schema.json").read_text())
    cli = runner.cli_schema(full)
    assert "$schema" not in cli and "allOf" not in cli
    for kept in ("type", "properties", "required", "additionalProperties"):
        assert kept in cli, kept
    # The contract keeps the conditionals: a match verdict naming no code must still be rejected.
    from jsonschema import Draft202012Validator
    v = Draft202012Validator(full)
    assert not v.is_valid({"unit_id": "U", "verdict": "match_existing", "confidence": "high",
                           "reasoning": "x" * 45, "evidence_used": ["a"]})


def test_iso_resolution_does_not_confuse_united_states_with_the_emirates():
    """The regression: a 6-character prefix resolved "United States of America" to ARE.

    The fix is no longer a full-name match plus a hand-written alias dict -- that dict was itself the
    ad-hoc thing, needing a new line for every dataset. Resolution now comes from crosswalks the
    repository already builds, and anything they do not answer is asked once and banked. So this
    test asserts two things: the crosswalk resolves the case that broke, and no alias table has
    grown back inside the harness.
    """
    cw = harness.crosswalk_iso()
    assert cw.get(harness.norm("United States of America")) == "USA"
    assert cw.get(harness.norm("Spain")) == "ESP"
    assert cw.get(harness.norm("Japan")) == "JPN"
    for label in ("United Arab Emirates", "Emirats arabes unis"):
        assert cw.get(harness.norm(label), "ARE") == "ARE"

    src = (HERE / "harness.py").read_text(encoding="utf-8")
    assert "iso_for_country" not in src, "the prefix-matching version must be gone"
    assert '"unitedstatesofamerica"' not in src, "no hand-maintained alias dict in the harness"
    assert "def resolve_iso" in src and "ISO_LEDGER" in src, "asked-once-and-banked is the fallback"

def test_boundary_name_match_is_bidirectional():
    """BUG: the panel calls it 'US Alaska'; a one-directional substring test never matched 'Alaska'.

    Stage 2 had the reverse test and found USA.2_1 while stage 1 reported no boundary at all.
    """
    unit = {"unit_id": "USA-ALASKA", "admin_name": "US Alaska", "country": "United States of America",
            "admin_level": "state", "y0": 1960, "y1": 2025, "rows": 1753,
            "indicators": "area", "source": "USDA NASS Subnational"}
    ev = harness.build_evidence(unit, [], "USA", [("USA.2_1", "Alaska"), ("USA.5_1", "California")],
                                wide=False, sibling_verdicts=[])
    assert "USA.2_1 Alaska" in ev
    assert "USA.5_1" not in ev          # and it must not match everything
    # The length floor stops a short name matching inside an unrelated one.
    short = dict(unit, admin_name="Ohio")
    ev2 = harness.build_evidence(short, [], "USA", [("USA.9_1", "Ohio")], wide=False,
                                 sibling_verdicts=[])
    assert "USA.9_1 Ohio" in ev2


def test_subnational_candidates_are_never_omitted_from_cycle_one():
    """BUG: cycle 1 showed only national rows, hiding ALK-1867-1959 from the Alaska verdict.

    The single most likely `match_existing` candidate is a subnational row, so trimming those is
    exactly backwards. Only the earlier national eras may be trimmed.
    """
    pols = [{"polity_code": "ALK-1867-1959", "polity_name": "Territory of Alaska",
             "iso3_code": "USA", "polity_type": "subnational",
             "start_year": "1867", "end_year": "1959"}]
    pols += [{"polity_code": f"USA-{1800 + i * 10}-{1810 + i * 10}",
              "polity_name": f"United States ({1800 + i * 10})", "iso3_code": "USA",
              "polity_type": "national", "start_year": str(1800 + i * 10),
              "end_year": str(1810 + i * 10)} for i in range(20)]
    unit = {"unit_id": "USA-ALASKA", "admin_name": "US Alaska", "country": "USA",
            "admin_level": "state", "y0": 1960, "y1": 2025, "rows": 1,
            "indicators": "area", "source": "s"}
    ev = harness.build_evidence(unit, pols, "USA", [], wide=False, sibling_verdicts=[])
    assert "ALK-1867-1959" in ev, "a subnational candidate was trimmed on cycle 1"
    assert "trimmed on this cycle" in ev, "trimming must be declared, not silent"


def test_extract_accepts_the_string_envelope_and_rejects_invalid():
    """The CLI returns the payload as a STRING under `result`; a harness expecting an object fails.

    And an object that does not satisfy the contract must be rejected, not passed through.
    """
    from jsonschema import Draft202012Validator
    schema = json.loads((HERE / "schemas" / "routing_verdict.schema.json").read_text())
    v = Draft202012Validator(schema)
    good = {"unit_id": "U", "verdict": "not_a_territory", "confidence": "high",
            "reasoning": "x" * 45, "evidence_used": ["a"]}
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "stdout.json"
        p.write_text(json.dumps({"result": json.dumps(good), "is_error": False}))
        assert runner.ClaudeRunner._extract(p, v) == good
        p.write_text(json.dumps({"result": json.dumps({"verdict": "nonsense"})}))
        assert runner.ClaudeRunner._extract(p, v) is None
        p.write_text("not json at all")
        assert runner.ClaudeRunner._extract(p, v) is None


def test_ledger_round_trip_keeps_stage_two_columns():
    """BUG: stage-1 rows lack the stage-2 keys, and DictWriter raises on a missing field.

    The writer fills them, so a run that reaches stage 2 does not lose stage-1 rows.
    """
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        harness.LEDGER = Path(d) / "l.csv"
        harness.write_ledger({"U": {"unit_id": "U", "country": "C", "verdict": "create_new"}})
        back = harness.read_ledger()
        assert back["U"]["verdict"] == "create_new"
        assert back["U"]["polygon_route"] == ""
        for f in harness.LEDGER_FIELDS:
            assert f in back["U"], f


def test_throttle_regex_is_narrow():
    """A loose match would retry genuine schema failures, which are bugs to fix, not waits."""
    for hit in ("HTTP 429", "status: 429", "429 Too Many Requests", "overloaded_error",
                "Selected model is at capacity", "rate_limit_error"):
        assert runner.THROTTLE_RE.search(hit), hit
    for miss in ("schema validation failed", "temporarily unavailable", "slow rate of progress",
                 "invalid JSON in response"):
        assert not runner.THROTTLE_RE.search(miss), miss


def test_mutating_tools_are_denied_on_the_command_line():
    """A verdict-emitting agent must not edit the tree, and that is enforced by the command."""
    r = runner.ClaudeRunner(run_dir=Path("/tmp"))
    cmd = r._command('{"type":"object"}')
    assert "--disallowed-tools" in cmd
    for tool in ("Edit", "Write", "NotebookEdit"):
        assert tool in cmd, tool
    assert "--permission-mode" in cmd and "bypassPermissions" in cmd


def test_convention_open_end_year_is_taken_from_the_container_column_not_the_code():
    """The polity CODE and the end_year COLUMN disagree for some rows; the column is the authority.

    Spain's national row is ESP-1800-2025 with end_year 2025, so a proposal reading the code happens
    to be right. Where they disagree, a unit spanned from the code outlives or under-runs its own
    container -- and end_year is EXCLUSIVE, so one year short silently drops a year of data.

    The harness does NOT correct the value. Picking one would be the harness deciding a country's
    span from a rule I made up, and the whole point of this stage is that the decision is reasoned
    and recorded. It states the disagreement and asks again, and refuses if that does not resolve.
    """
    src = (HERE / "harness.py").read_text(encoding="utf-8")
    assert "def objection(" in src, "the check must be expressible as a stated objection"
    assert "read the column" in src, "the objection must say which of the two sources is authority"
    assert "-retry" in src and "A PREVIOUS ANSWER WAS REJECTED" in src, "it must re-ask"
    assert "HARNESS CORRECTION" not in src, "no silently invented span"
    assert "units decided without one" in src, "refusal must be a reachable outcome"

def test_convention_is_banked_as_a_decision_and_survives_unit_refresh():
    """--refresh re-asks the UNITS. If it also re-asked the convention, the country's span could
    change between runs, which is the disagreement this stage exists to remove."""
    src = (HERE / "harness.py").read_text(encoding="utf-8")
    assert "refresh=A.refresh_convention" in src, "convention must not be refreshed by --refresh"
    assert "refresh=A.refresh)" in src, "unit calls must still honour --refresh"
    assert "os.replace(tmp, CONVENTION_LEDGER)" in src, "the ledger must be written atomically"


def test_a_red_gate_that_never_names_our_code_is_not_reported_as_clean():
    """`clean` previously meant `no failure mentions our code`, which is not the same thing.

    run_gates filters to failures naming the page's code -- correctly, since this loop must not
    rewrite a page to fix another row. But a gate red only on other rows then contributed nothing,
    the failure list came back empty, and the loop recorded `clean`. The two facts now travel
    separately so the reassuring reading cannot be the default one.
    """
    src = (HERE / "repair.py").read_text(encoding="utf-8")
    assert "def run_gates_detail" in src
    assert "red.append(Path(gate).name)" in src, "every non-zero gate must be recorded as red"
    hsrc = (HERE / "harness.py").read_text(encoding="utf-8")
    assert '"clean" if not red else "clean_for_code"' in hsrc
    assert "repair_gates_red" in hsrc, "the red gate names must reach the ledger"
    # and the resume filter must not treat clean_for_code as unfinished work
    assert '("clean", "clean_for_code", "exhausted")' in hsrc


def test_arithmetic_repair_cannot_launder_a_content_change():
    """ARITHMETIC mode says "touch no prose". Enforce it, because asking did not work.

    A real run fixed one span and also rewrote predecessors_and_successors, decisions and
    open_questions. Losing an open question is the worst case: nobody resolved it, and the page
    stops saying it is open.
    """
    prev = {"polity_code": "X-1-2", "frontmatter": {"end_year": 2025},
            "summary": "kept", "why_this_entry_exists": "kept", "territorial_extent": "kept",
            "predecessors_and_successors": "the original text",
            "sourced_claims": [{"claim": "a"}], "decisions": ["one"],
            "open_questions": ["is the 1927 boundary right?"]}
    new = dict(prev, frontmatter={"end_year": 2026},
               predecessors_and_successors="rewritten",
               decisions=["one", "two"], open_questions=[])
    merged, moved = repair.enforce_arithmetic_narrowness(prev, new)
    assert merged["frontmatter"] == {"end_year": 2026}, "the arithmetic fix must survive"
    assert merged["predecessors_and_successors"] == "the original text"
    assert merged["decisions"] == ["one"]
    assert merged["open_questions"] == ["is the 1927 boundary right?"], "an open question cannot be dropped"
    assert set(moved) == {"predecessors_and_successors", "decisions", "open_questions"}, moved

    # ...and the enforcement must NOT apply when the finding genuinely needs a content judgement
    F = repair.Failure
    assert repair.is_arithmetic_only([F("g", "l", "ARITHMETIC", "op")])
    assert not repair.is_arithmetic_only([F("g", "l", "ARITHMETIC", "op"),
                                          F("g", "l2", "JUDGEMENT", "op")])
    assert not repair.is_arithmetic_only([]), "an empty set is not an arithmetic-only set"


def test_every_schema_compiles_and_survives_the_cli_strip():
    """A schema that does not compile makes the harness refuse every unit, silently and forever.

    Both halves matter: our validator is the contract, so it must compile as Draft 2020-12; and the
    CLI-facing copy is what the model is shown, so it must still be a usable object after the
    unsupported keywords are stripped -- a schema whose entire shape lives in an `allOf` strips to
    nothing and stops constraining the model at all.
    """
    from jsonschema import Draft202012Validator

    found = sorted((HERE / "schemas").glob("*.schema.json"))
    assert len(found) >= 4, f"expected the four stage schemas, found {[f.name for f in found]}"
    for f in found:
        full = json.loads(f.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(full)
        hint = runner.cli_schema(full)
        assert hint.get("type") == "object", f"{f.name}: strips to no type"
        assert hint.get("properties"), f"{f.name}: strips to no properties"
        assert not (set(hint) & set(runner.CLI_UNSUPPORTED)), f"{f.name}: kept a rejected keyword"
        # required must survive the strip, or the model may omit the fields the stage depends on
        assert full.get("required"), f"{f.name}: declares nothing required"


def test_an_unclassified_arm_is_learned_from_the_gate_source_not_from_a_regex_list():
    """UNKNOWN meant no repair was aimed at a real, reported failure.

    The alternative to asking is a regex list over the gates' prose, and that list is what already
    failed: "the container's span" versus "the container span" -- one apostrophe -- dropped a
    fixable arithmetic failure into the do-nothing class. An arm's nature is fixed by what the gate
    compares, so it is asked once per (gate, arm) and banked, never per failing row.
    """
    src = (HERE / "repair.py").read_text(encoding="utf-8")
    assert "def classify_unknown_arms" in src
    assert 'f"{f.gate}|{m.group(1)}"' in src, "the bank key must be (gate, arm)"
    assert "os.replace(tmp, LEARNED_ARMS)" in src, "written atomically"
    # a learned arm must be honoured by the plain classifier too, with no runner in hand
    assert "learned_arms().get(" in src
    # declining is a real outcome: an UNKNOWN answer must not be banked as a classification
    assert 'if r["kind"] == "UNKNOWN":' in src
    hsrc = (HERE / "harness.py").read_text(encoding="utf-8")
    assert "_repair.classify_unknown_arms(fails, runner)" in hsrc

    # and a failure with no arm letter has no stable key, so it must stay UNKNOWN rather than
    # being re-asked on every row forever
    F = repair.Failure
    noarm = F("g.py", "FAIL: something with no arm letter", "UNKNOWN", "unclassified")
    assert repair.ARM_RE.match(noarm.line) is None


def test_a_later_cycle_escalates_what_is_undecided_and_never_repeats_what_is_settled():
    """`--refresh --cycles 2` re-asked all 53 Spanish units a second time.

    Two costs, and the second is the real one: 53 extra calls, and every settled high-confidence
    verdict re-opened under the WIDE candidate net, which exists to help a unit that could not be
    decided at all. --refresh means "re-ask what I decided before" -- that is cycle 1's job. A later
    cycle is an escalation for what is still undecided.
    """
    src = (HERE / "harness.py").read_text(encoding="utf-8")
    assert "if A.refresh and cycle == 1:" in src, "refresh must apply to the first cycle only"
    assert "wide = cycle > 1" in src, "the wide net must remain tied to escalation"

    # the filter itself: only an absent, blank or insufficient_evidence verdict is undecided
    ledger = {"a": {"verdict": "create_new"}, "b": {"verdict": "insufficient_evidence"},
              "c": {"verdict": ""}, "d": {"verdict": "match_existing"},
              "e": {"verdict": "not_a_territory"}}
    undecided = [k for k, v in ledger.items()
                 if v.get("verdict") in (None, "", "insufficient_evidence")]
    assert sorted(undecided) == ["b", "c"], undecided
    assert "d" not in undecided and "e" not in undecided, "a decided verdict is not re-opened"


def test_the_code_convention_is_precedent_not_an_asserted_rule():
    """The prompt asserted that a polity_code must begin with the country's iso3. The table refutes
    it: ALK-1867-1959 (Territory of Alaska) and AUWA-1829-1900 (Western Australia) do not, and 62
    rows in all. A hard check on that rule would have rejected them.

    So the shapes are counted from the table at run time and shown as precedent. Counting rather
    than pinning matters for the same reason the assertion was wrong -- a pinned number goes stale
    silently, and this prompt has already carried one claim the data contradicts.
    """
    pols = [
        {"polity_code": "DZA-CVD-1902-1919", "iso3_code": "DZA", "polity_type": "subnational",
         "polity_name": "x", "start_year": "1902", "end_year": "1919"},
        {"polity_code": "JPN-AICHI-1871-2025", "iso3_code": "JPN", "polity_type": "subnational",
         "polity_name": "y", "start_year": "1871", "end_year": "2025"},
        {"polity_code": "ALK-1867-1959", "iso3_code": "USA", "polity_type": "subnational",
         "polity_name": "Territory of Alaska", "start_year": "1867", "end_year": "1959"},
        {"polity_code": "BDI-1922-1962", "iso3_code": "BDI", "polity_type": "subnational",
         "polity_name": "z", "start_year": "1922", "end_year": "1962"},
        {"polity_code": "ESP-1800-2025", "iso3_code": "ESP", "polity_type": "national",
         "polity_name": "Spain", "start_year": "1800", "end_year": "2025"},
    ]
    out = harness.code_precedent(pols, "JPN")
    assert "Of 4 subnational rows" in out, out          # the national row is not precedent here
    assert "<ISO3>-<SUBUNIT>-<start>-<end>" in out and "<BESPOKE>-<start>-<end>" in out
    assert "ALK-1867-1959" in out, "the counter-example must be shown, not hidden"
    assert "JPN-AICHI-1871-2025" in out
    src = (HERE / "harness.py").read_text(encoding="utf-8")
    assert "`CALI-1850-2026` is wrong" not in src, "the refuted assertion must be gone"


def test_a_taken_polity_code_is_re_asked_not_skipped():
    """`if dest.exists(): SKIP` silently dropped the polity the run was asked to create.

    Whether a code is taken is a fact, so it is checked here rather than asked -- but the page it
    collides with describes a DIFFERENT territory, so the answer is to state the clash and ask for a
    free code, not to print a line that reads like an ordinary no-op.
    """
    src = (HERE / "harness.py").read_text(encoding="utf-8")
    assert "A CODE COLLISION MUST NOT BE A SKIP" in src
    assert "is already in the table, held by" in src, "the clash must name the holder"
    assert "Choose a code that is free. Change nothing else." in src, "narrow repair"
    assert "could not find a free polity_code — not written" in src, "failing is better than clobbering"
    # the surviving skip must be about THIS unit's own page, not any page at that path
    assert 'if dest.exists() and v.get("page_written") and not A.refresh:' in src


def test_an_unreciprocated_chain_edge_is_handed_back_not_written():
    """One asymmetric edge added by this harness fails CI, because the gate baselines BOTH
    directions: 84 predecessor-only edges against a baseline of 83 is a failure.

    The Alaska smoke is the live case. The new ALK-1959-2025 page declared
    `predecessor: [ALK-1867-1959]`; ALK-1867-1959 declares `successor: [USA-1959-2025]` -- the whole
    country, not the state. Detecting that is a fact. Choosing between "the state is the successor"
    and "the country is" is a claim about history, so the objection is handed back with the
    counterpart's real fields rather than reciprocated automatically.
    """
    edges = {"ALK-1867-1959": (set(), {"USA-1959-2025"}),
             "USA-1959-2025": (set(), set())}
    page = {"polity_code": "ALK-1959-2025",
            "frontmatter": {"predecessor": ["ALK-1867-1959"], "successor": []}}
    obj = harness.unreciprocated(page, edges)
    assert obj, "the live failing case must be caught"
    assert "USA-1959-2025" in obj, "the counterpart's ACTUAL field must be shown"
    assert "do not leave the asymmetry unremarked" in obj
    assert "You cannot edit the other page" in obj

    # reciprocated: silent
    ok = {"polity_code": "B", "frontmatter": {"predecessor": ["A"], "successor": []}}
    assert harness.unreciprocated(ok, {"A": (set(), {"B"})}) is None

    # a code that is not in the table is a DIFFERENT arm (dead target) and must not be reported here
    ghost = {"polity_code": "B", "frontmatter": {"predecessor": ["NOPE-1-2"], "successor": []}}
    assert harness.unreciprocated(ghost, {"A": (set(), set())}) is None

    # the successor direction too, not only predecessor
    fwd = {"polity_code": "A", "frontmatter": {"predecessor": [], "successor": ["B"]}}
    assert harness.unreciprocated(fwd, {"B": ({"C"}, set())})


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  PASS  {name}")
        except AssertionError as exc:
            failed += 1
            print(f"  FAIL  {name}: {exc}")
    print(f"\n{'FAIL' if failed else 'PASS'}: {failed} failing")
    sys.exit(1 if failed else 0)
