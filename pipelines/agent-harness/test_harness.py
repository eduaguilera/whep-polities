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
            "reasoning": "x" * 45, "evidence_used": ["a"],
            "coverage": [{"start_year": 1900, "end_year": 1950, "disposition": "unroutable",
                          "basis": "a residual bucket carries no territory"}]}
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
    assert "held by" in src, "the clash must name the holder"
    assert "Choose a code that is free. Change nothing else." in src, "narrow repair"
    assert "could not find a free polity_code — not written" in src, "failing is better than clobbering"
    # TAKEN must come from the wiki, not the derived CSV. Reading the CSV produced a FALSE clash: a
    # withdrawn page left its row behind, and the unit re-authoring its own page was pushed off
    # ESP-CO-1833-2025 onto the NUTS-derived ESP-ES111-1833-2025 by a stale derived file.
    assert 'taken = {f.stem.upper() for f in (REPO / "wiki" / "polities").glob("*.md")}' in src
    assert "already has a page in wiki/polities/" in src
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


def test_a_route_name_is_never_a_polygon_source():
    """A Coruña's page came back with `polygon_source: new_source_needed` and
    validate_declared_sources arm D rejected it: that is stage 2's route enum written into the
    field that names a source. The two vocabularies are not interchangeable.

    Which slugs are registered is a fact in sources.yaml, so it is read rather than listed here --
    a list in this file would be one more table needing a line per new source.
    """
    slugs = harness.polygon_slugs()
    assert "mapspain-ign" in slugs and "gadm-4.1-adm1" in slugs, sorted(slugs)[:6]
    assert "new_source_needed" not in slugs, "a route must never be a registered slug"

    bad = {"polity_code": "X", "frontmatter": {"polygon_source": "new_source_needed"}}
    obj = harness.bad_polygon_source(bad, slugs)
    assert obj and "That is a polygon ROUTE, not a source." in obj
    assert "`none` is the honest value" in obj

    for ok in ("none", "", None, "mapspain-ign"):
        page = {"polity_code": "X", "frontmatter": {"polygon_source": ok}}
        assert harness.bad_polygon_source(page, slugs) is None, ok
    # a plausible-looking but unregistered slug must still be caught
    assert harness.bad_polygon_source(
        {"polity_code": "X", "frontmatter": {"polygon_source": "gadm-4.2-adm1"}}, slugs)


def test_new_source_needed_cannot_name_an_already_registered_source():
    """Stage 2 routed A Coruña to `new_source_needed` while its own detail said mapspain-ign was
    "already registered in scripts/sources.yaml" -- which it is, with id_column cpro. The
    contradiction then propagated into the page. A registered source needs no new registration."""
    src = (HERE / "harness.py").read_text(encoding="utf-8")
    assert "is ALREADY registered in" in src
    assert "wrong source and naming it was a mistake" in src, "the objection must present the fork"
    # It must NOT push one branch. The first version told the agent to switch to
    # `registered_source_feature` -- and a FRENCH region had proposed `mapspain-ign`, which is
    # Spain-only, so obeying it would have attached another country's boundary: exactly what
    # validate_polygons exists to catch.
    assert "Spain-only" in src and "another country's" in src
    assert "records no extent for any source" in src, "say why the harness cannot decide it"
    # and the mirror case: claiming a registered route for a slug that is not registered
    assert "but source_slug" in src and "is not registered" in src


def test_the_start_rule_is_a_default_with_enumerated_departures():
    """Spain's convention contradicted its own evidence, in the same object.

    `system_start_basis` said the 1833 reform made "49 (later 50, with the 1927 split of the Canary
    Islands) provinces"; `unit_start_rule` then said "all units begin at the floor (1833) ... no
    per-unit variation is needed". The per-unit stage inherited the rule and dated Las Palmas 1833 --
    94 years before it existed -- while the fact that refuted it sat two fields away.

    So departures are a required field, and the per-unit evidence presents the rule as a default and
    invites a justified departure. Re-decided, Spain returns 50 provinces at 1833 and exactly the two
    Canary provinces at 1927.
    """
    import json as _json
    schema = _json.loads((HERE / "schemas" / "country_convention.schema.json")
                         .read_text(encoding="utf-8"))
    assert "unit_start_exceptions" in schema["required"], "an empty list must be a stated claim"
    items = schema["properties"]["unit_start_exceptions"]["items"]
    assert items["required"] == ["units", "start_year", "basis"]
    assert "1927 split of the Canary Islands" in \
        schema["properties"]["unit_start_rule"]["description"], "the case must be quoted"

    src = (HERE / "harness.py").read_text(encoding="utf-8")
    assert "DEPARTURES from that rule" in src, "exceptions must reach the per-unit evidence"
    assert "The rule is a default." in src
    assert "Re-read your own" in src and "before returning an empty list" in src

    # the floor must never be presented as the unit's own start
    assert "a FLOOR for the system, NOT " in src


def test_the_ledger_write_merges_instead_of_replacing_the_file():
    """A whole-file write from a startup snapshot is only safe while one run exists.

    444 units across 26 countries is hours of wall clock one country at a time, so countries run
    concurrently -- and two runs each writing their own stale snapshot would silently drop the
    other's rows. That is the same failure that turned a request for Alaska into a California page,
    one process further out.
    """
    src = (HERE / "harness.py").read_text(encoding="utf-8")
    assert "fcntl.flock(lf, fcntl.LOCK_EX)" in src, "the read-modify-write must be locked"
    assert "merged = read_ledger()" in src and "merged.update(rows)" in src, "it must MERGE"
    assert 'LEDGER.with_suffix(f".{os.getpid()}.tmp")' in src, \
        "a shared .tmp between processes is a torn file, not a merge"
    assert "rows.update(merged)" in src, "the caller must see rows another run committed"
    assert "fcntl.flock(lf, fcntl.LOCK_UN)" in src

    # ours must win on a conflicting key, since we are the run that just decided it
    disk = {"A": {"verdict": "old"}, "B": {"verdict": "keep"}}
    mine = {"A": {"verdict": "new"}}
    disk.update(mine)
    assert disk == {"A": {"verdict": "new"}, "B": {"verdict": "keep"}}


def test_coverage_must_tile_the_units_whole_data_span():
    """"All the data is matched" was an impression, not a measurement.

    Of the first 15 match_existing verdicts, FIVE left years outside the matched polity's span and
    nothing in the ledger showed it: AUS-QUEENSLAND has data 1860-2022 and matched QUE-1859-1900,
    stranding 122 years; PER-NATIONAL has 1900-2023 and matched PER-1942-2025, crossing five
    national eras. A single verdict code cannot cover a unit that outlives one polity.
    """
    pols = [{"polity_code": "QUE-1859-1900", "polity_name": "Queensland colony", "iso3_code": "AUS",
             "polity_type": "subnational", "start_year": "1859", "end_year": "1900"}]
    unit = {"unit_id": "AUS-QUEENSLAND", "y0": 1860, "y1": 2022}

    # the live failing shape: one matched segment, 122 years stranded
    v = {"coverage": [{"start_year": 1860, "end_year": 1900, "disposition": "matched",
                       "polity_code": "QUE-1859-1900", "basis": "the colony carries these years"}]}
    obj = harness.coverage_objection(v, unit, pols)
    assert obj and "Data ends at 2022" in obj, obj
    assert "122 year(s) unaccounted for" in obj, obj

    # end_year is EXCLUSIVE on a polity, so 1900 itself is NOT inside QUE-1859-1900
    v2 = {"coverage": [{"start_year": 1860, "end_year": 1900, "disposition": "matched",
                        "polity_code": "QUE-1859-1900", "basis": "x" * 25},
                       {"start_year": 1901, "end_year": 2022, "disposition": "proposed",
                        "basis": "the state needs a polity of its own"}]}
    assert "carries data through 1899" in (harness.coverage_objection(v2, unit, pols) or "")

    # tiled correctly, with the exclusive end respected
    v3 = {"coverage": [{"start_year": 1860, "end_year": 1899, "disposition": "matched",
                        "polity_code": "QUE-1859-1900", "basis": "x" * 25},
                       {"start_year": 1900, "end_year": 2022, "disposition": "proposed",
                        "basis": "the state needs a polity of its own"}]}
    assert harness.coverage_objection(v3, unit, pols) is None

    # gaps, overlaps, a missing code and a ghost code are each named
    for bad, want in (
        ([{"start_year": 1860, "end_year": 1900, "disposition": "proposed", "basis": "x" * 25},
          {"start_year": 1910, "end_year": 2022, "disposition": "proposed", "basis": "x" * 25}],
         "Gap between 1900 and 1910"),
        ([{"start_year": 1860, "end_year": 1950, "disposition": "proposed", "basis": "x" * 25},
          {"start_year": 1940, "end_year": 2022, "disposition": "proposed", "basis": "x" * 25}],
         "overlap"),
        ([{"start_year": 1860, "end_year": 2022, "disposition": "matched", "basis": "x" * 25}],
         "names no polity_code"),
        ([{"start_year": 1860, "end_year": 2022, "disposition": "matched",
           "polity_code": "NOPE-1-2", "basis": "x" * 25}],
         "not a polity_code in the table"),
    ):
        got = harness.coverage_objection({"coverage": bad}, unit, pols) or ""
        assert want in got, (want, got)

    # an empty coverage list is the strongest failure, not a pass
    assert harness.coverage_objection({"coverage": []}, unit, pols)


def test_the_same_unit_shape_is_shown_how_other_countries_read_it():
    """Thirteen identical <ISO3>-NATIONAL units split 11 match_existing / 2 not_a_territory.

    The cause was in the schema -- not_a_territory listed "a national total wearing a subnational
    label" while match_existing's wording fit it too, so both readings were faithful. Fixed by
    making the test whether anything could EVER be routed to the identifier, and by showing each
    unit how the same id marker was read elsewhere. Keyed on the id's own suffix, so no list of
    markers has to be maintained.
    """
    import json as _json
    schema = _json.loads((HERE / "schemas" / "routing_verdict.schema.json")
                         .read_text(encoding="utf-8"))
    desc = schema["properties"]["verdict"]["description"]
    assert "INCLUDING a national total filed at admin1 level" in desc
    assert "could EVER be routed" in desc
    assert "SPLIT 11-2" in desc, "the divergence that motivated the wording must be recorded"

    src = (HERE / "harness.py").read_text(encoding="utf-8")
    assert "def marker(uid: str)" in src and 'uid.split("-", 1)[1]' in src
    assert "OTHER COUNTRIES' UNITS WITH THE SAME id marker" in src
    assert 'x.get("country") != A.country' in src, "it must look ACROSS countries"


def test_two_units_cannot_both_be_the_same_polity_in_the_same_years():
    """AUS-VICTORIA matched VIC-1851-1900 for 1860-1899 and then AUS-1901-2025 -- the whole of
    Australia -- for 1901-2022. Every other Australian state could claim that equally, and the data
    would be summed into one polity eight times.

    Checked structurally, not by polity_type, because the data defeats type-checking here:
    VIC-1851-1900 is itself typed `national` while its sibling AUWA-1829-1900 is typed `colonial`,
    so "a subnational unit matched a national row" does not separate the good case from the bad.
    """
    ledger = {
        "AUS-QUEENSLAND": {"country": "Australia", "unit_id": "AUS-QUEENSLAND",
                           "admin_name": "Queensland",
                           "coverage_json": json.dumps(
                               [{"start_year": 1901, "end_year": 2022,
                                 "disposition": "matched", "polity_code": "AUS-1901-2025"}])},
    }
    unit = {"unit_id": "AUS-VICTORIA", "y0": 1860, "y1": 2022}
    v = {"coverage": [{"start_year": 1860, "end_year": 1899, "disposition": "matched",
                       "polity_code": "VIC-1851-1900"},
                      {"start_year": 1901, "end_year": 2022, "disposition": "matched",
                       "polity_code": "AUS-1901-2025"}]}
    obj = harness.double_claim_objection(v, unit, ledger, "Australia")
    assert obj and "AUS-1901-2025 is claimed for 1901-2022 by BOTH" in obj, obj
    assert "AUS-QUEENSLAND" in obj, "the other claimant must be named"
    assert "matching a unit to its own CONTAINER has this shape" in obj

    # no overlap in years -> no clash
    v2 = {"coverage": [{"start_year": 1860, "end_year": 1899, "disposition": "matched",
                        "polity_code": "AUS-1901-2025"}]}
    assert harness.double_claim_objection(v2, unit, ledger, "Australia") is None

    # a different country's unit is not a clash, and `proposed` segments never clash
    assert harness.double_claim_objection(v, unit, ledger, "Spain") is None
    v3 = {"coverage": [{"start_year": 1901, "end_year": 2022, "disposition": "proposed"}]}
    assert harness.double_claim_objection(v3, unit, ledger, "Australia") is None


def test_sibling_evidence_shows_how_a_year_was_disposed_of():
    """Every Australian colony polity ends at 1900 EXCLUSIVE while the states begin 1901, so
    calendar year 1900 is a seam. Within one country it got three different answers -- four units
    called it `unroutable`, three matched it to AUS-1800-1901 -- because a sibling's verdict line
    shows the verdict and not what it did with a year."""
    src = (HERE / "harness.py").read_text(encoding="utf-8")
    assert "def seg_summary(" in src
    assert "s['disposition']" in src and "coverage_json" in src
    assert "'  [' + seg_summary(v) + ']'" in src, "the segments must reach the sibling lines"


def test_unroutable_years_are_pushed_back_on():
    """A TILING IS NOT A ROUTING, and coverage_ok=yes said otherwise.

    Portugal's 23 units tiled their spans perfectly while marking 1870-1988 `unroutable` -- 118
    years, about 90% of the country's 341,508 rows. The cause was upstream: the convention read the
    panel's `admin_level: NUTS` literally and dated every unit to the 1989 NUTS classification, but
    18 of the 23 are DISTRICTS, an administrative division of 1835, and the source reports them from
    1880. A reporting unit that has data for a year had a territory in that year, whatever the
    statistical classification was called.
    """
    unit = {"unit_id": "PRT-PTAV", "y0": 1880, "y1": 2023}
    pols = []
    mostly_unroutable = {"coverage": [
        {"start_year": 1880, "end_year": 1988, "disposition": "unroutable", "basis": "x" * 25},
        {"start_year": 1989, "end_year": 2023, "disposition": "proposed", "basis": "x" * 25}]}
    obj = harness.coverage_objection(mostly_unroutable, unit, pols)
    assert obj, "the live Portuguese shape must be rejected"
    assert "109 of this unit's 144 data years (76%)" in obj, obj
    assert "the territory existed and was being measured" in obj
    assert "not for a year before the classification that currently names the unit was invented" in obj

    # a small genuine seam is still allowed -- the 1900 Australian federation gap is one year
    small = {"coverage": [
        {"start_year": 1880, "end_year": 1899, "disposition": "proposed", "basis": "x" * 25},
        {"start_year": 1900, "end_year": 1900, "disposition": "unroutable", "basis": "x" * 25},
        {"start_year": 1901, "end_year": 2023, "disposition": "proposed", "basis": "x" * 25}]}
    assert harness.coverage_objection(small, unit, pols) is None


def test_a_units_name_provenance_reaches_its_evidence():
    """A code's shape suggests a vocabulary and can be wrong about it.

    PTAV's crosswalk basis says "the 18 mainland districts ... NOT an official code list", which
    refutes "NUTS region of Portugal" on its own -- and the panel's `admin_level` column says "NUTS"
    for both Portuguese layers, so it cannot settle the question either.
    """
    basis = harness.nuts_basis()
    assert basis.get("PTAV", "").startswith("derived:"), basis.get("PTAV")
    assert "NOT an official code list" in basis["PTAV"]
    assert "GISCO" in basis.get("ES111", ""), basis.get("ES111")
    # the newly resolved districts must carry their own provenance, not inherit GISCO's
    assert "HASC" in basis.get("PTBR", ""), basis.get("PTBR")
    assert "by elimination" in basis.get("PTBG", ""), basis.get("PTBG")

    src = (HERE / "harness.py").read_text(encoding="utf-8")
    assert '"name_basis": bs.get(key, "")' in src, "the basis must travel on the unit"
    assert "NAME PROVENANCE" in src, "and reach the evidence"
    # the evidence must no longer hard-assert GISCO for every code, since the basis can contradict it
    assert "(Eurostat GISCO NUTS 2021, " not in src


def test_back_cast_routes_data_without_inventing_administrative_history():
    """Pushing back on `unroutable` moved 7,978 stranded data-years to only 7,484, because the
    agent could not satisfy the objection: routing them meant either stretching a polity's span
    back to 1900 (inventing administrative history) or abandoning the data. Neither is true.

    The panel says which it is. `method` is blank for 96-100% of Spanish, Portuguese, French,
    Japanese and Australian rows -- direct historical statistics -- while Colombia is 74%
    `interpolated_scaled` plus 23% `scaled`, and Brazil 45% `fallback_interpolated`: every
    subnational value there is an allocation of a national total. COL-CASANARE has data from 1900
    and became a department in 1991.
    """
    import json as _json
    schema = _json.loads((HERE / "schemas" / "routing_verdict.schema.json")
                         .read_text(encoding="utf-8"))
    disp = schema["properties"]["coverage"]["items"]["properties"]["disposition"]
    assert disp["enum"] == ["matched", "proposed", "back_cast", "unroutable"]
    assert "projecting it backwards" in disp["description"]
    assert "invents administrative history" in disp["description"]

    # a back_cast segment must still name the territory it is a reconstruction FOR
    unit = {"unit_id": "COL-CASANARE", "y0": 1900, "y1": 2023}
    nameless = {"coverage": [
        {"start_year": 1900, "end_year": 1990, "disposition": "back_cast", "basis": "x" * 25},
        {"start_year": 1991, "end_year": 2023, "disposition": "proposed", "basis": "x" * 25}]}
    obj = harness.coverage_objection(nameless, unit, [])
    assert obj and "is `back_cast` but names no polity_code" in obj, obj

    # ...and once it does, the years are routed: no unroutable, so no threshold complaint
    named = {"coverage": [
        {"start_year": 1900, "end_year": 1990, "disposition": "back_cast",
         "polity_code": "COL-CASANARE-1991-2025", "basis": "scaled onto the modern boundary"},
        {"start_year": 1991, "end_year": 2023, "disposition": "proposed", "basis": "x" * 25}]}
    assert harness.coverage_objection(named, unit, []) is None


def test_the_method_profile_is_actually_read():
    """`if "method" in df.columns` was the first version, and `method` was not among the columns
    units_for_country reads -- so the guard was always False, every profile came out empty, and
    nothing looked broken. The absence of the column is now stated instead of skipped."""
    src = (HERE / "harness.py").read_text(encoding="utf-8")
    assert '"value_canonical",' in src and '"method"])' in src, \
        "the column must be READ, or the profile is silently empty"
    assert 'if "method" not in df.columns:' in src and "NOTE: the panel has no `method` column" in src
    assert "HOW VALUES WERE MADE" in src, "and it must reach the evidence"
    # A blank method must NOT be presented as proof the unit was observed. The first version said
    # exactly that, and it pushed Portugal's five NUTS-2 regions -- 100% blank, running from 1870,
    # for a classification that did not exist until 1989 -- away from back_cast and into marking
    # 79% of their years unroutable.
    assert "does NOT establish that this unit was observed" in src
    assert "NUTS did not exist until 1989" in src
    assert "not this column" in src, "the unit's existence date settles it, not the method"


def test_a_usage_limit_is_recognised_where_the_cli_actually_puts_it():
    """56 calls in the final routing pass reported `return code 1, no schema-valid result`, which
    reads as the model failing to answer. The real text was

        You've hit your session limit · resets 3:10pm (Europe/Madrid)

    and it sat in the CLI's own `result` field in STDOUT, with stderr empty -- so THROTTLE_RE, which
    only read stderr, could not match it. Nine Portuguese verdicts then looked like a crosswalk gap
    that had already been fixed, because the re-run's calls never landed.

    Asserted against the real captured payload, not a hand-written string, so the shape cannot
    drift out from under the check.
    """
    real = (HERE / "state" / "runs" / "portugal" / "agents" / "cycle02-prtptvi"
            / "stdout.attempt-04.json")
    if real.is_file():
        got = runner.limit_signal(real, "")
        assert got and got.startswith("usage limit reached"), got
        assert "resets 3:10pm (Europe/Madrid)" in got, got
        # the payload that fooled the old check: stderr was empty
        assert not runner.THROTTLE_RE.search("")

    # a capacity throttle is still a throttle, and must NOT be reclassified as a usage limit
    assert runner.THROTTLE_RE.search("429 Too Many Requests")
    assert runner.limit_signal(Path("/nonexistent"), "429 Too Many Requests") is None
    assert runner.limit_signal(Path("/nonexistent"), "overloaded_error") is None
    # ...and a genuine schema failure must stay a schema failure
    assert runner.limit_signal(Path("/nonexistent"), "ValidationError: 'verdict' is required") is None

    src = (HERE / "runner.py").read_text(encoding="utf-8")
    assert 'blobs.append(str(raw.get("result", "")))' in src, "the payload must be read, not just stderr"
    assert "error = limit\n                break" in src, "a limit must not burn the schema retries"

    hsrc = (HERE / "harness.py").read_text(encoding="utf-8")
    assert '"usage limit" in res.error' in hsrc and "STOPPING" in hsrc, \
        "the run must stop rather than fail every remaining unit identically"


def test_registered_source_feature_must_name_a_feature():
    """The route enum forced a false choice, so 20 units made an unverifiable claim.

    All 20 were Spanish, all named mapspain-ign, all with an EMPTY feature_id -- because
    data/geodata/mapspain-ign/provinces.gpkg does not exist in this checkout. That route asserts
    one specific feature IS the boundary, so without a feature it cannot be checked;
    `new_source_needed` was equally false, since the source needs FETCHING, not registering.

    Same lesson as the `unroutable` threshold: before requiring precision, make sure an honest
    answer exists to be precise with.
    """
    import json as _json
    schema = _json.loads((HERE / "schemas" / "polygon_route.schema.json")
                         .read_text(encoding="utf-8"))
    enum = schema["properties"]["route"]["enum"]
    assert "registered_source_unfetched" in enum, enum
    desc = schema["properties"]["route"]["description"]
    assert "20 Spanish units" in desc, "the case that motivated it must be recorded"
    assert "needs fetching rather than registering" in desc

    src = (HERE / "harness.py").read_text(encoding="utf-8")
    assert "no feature_id is given, so the" in src, "an empty feature must be objected to"
    assert "registered_source_unfetched`: name the slug" in src, "and the honest route offered"
    # the new route must itself still name a REGISTERED slug, or it means nothing
    assert '"registered_source_unfetched" and r.get("source_slug") not in slugs' in src
    assert "that is `new_source_needed`." in src

    # a department must not be given a country-boundaries source: FRA-FRF31 (Meurthe-et-Moselle)
    # was routed to cshapes-2.0 reasoning it "should just inherit the country-level polygon".
    # An empty feature_id is what makes that catchable without granularity metadata.
    assert "asserts that one specific " in src


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
