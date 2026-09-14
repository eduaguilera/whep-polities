#!/usr/bin/env python3
"""Author a polity for a territory that NO reporting unit asks for.

WHY THIS IS A SEPARATE ENTRY POINT. The harness is unit-driven: every stage starts from a row in
the source panel, which is the right default -- issue 400's policy gives a polity to anything we
have data FOR. But a container's members are also expected to TILE it, and WHEP's cell support
needs that: Italy's 18 regions summed to 0.956 of the country because Molise, Valle d'Aosta and
Trentino-Alto Adige's Trento half are simply absent from the panel. No routing verdict will ever
ask for them, and they are real regions.

So this takes the territory as an argument rather than discovering it, and is explicit on the page
that no source demands the row -- which is the fact a later reader most needs, and the caution the
WHEP side raised when two Spanish island units turned out to exist only because of a gap report.

Everything else is shared with stage 3: the same prompt, the same schema, the same objection loop
(code clash, structural checks, duplicate territory, polygon vocabulary, chain reciprocity), and the
same renderer. It is a different question, not a different standard.

Usage:
  python3 pipelines/agent-harness/author_for_completeness.py \
      --name "Molise" --iso ITA --start 1963 --end 2025 \
      --container ITA-1919-2025 --source gadm-4.1-adm1 --feature ITA.12_1 \
      --why "one of Italy's 20 regions; absent from the panel, so no unit routes to it"
"""
from __future__ import annotations

import argparse
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


def main() -> int:
    ap = argparse.ArgumentParser()
    for f in ("name", "iso", "container", "why"):
        ap.add_argument(f"--{f}", required=True)
    ap.add_argument("--start", type=int, required=True)
    ap.add_argument("--end", type=int, required=True)
    ap.add_argument("--source", default="none")
    ap.add_argument("--feature", default="")
    ap.add_argument("--model")
    ap.add_argument("--effort")
    A = ap.parse_args()

    h = _load("harness")
    pol = json.loads((HERE / "policy.json").read_text(encoding="utf-8"))
    run_dir = h.RUNS / "completeness"
    run_dir.mkdir(parents=True, exist_ok=True)
    runner = h.ClaudeRunner(run_dir=run_dir, model=A.model or pol.get("model", "sonnet"),
                            effort=A.effort or pol.get("effort", "low"),
                            timeout=int(pol.get("timeout_seconds", 600)),
                            max_budget_usd=pol.get("max_budget_usd"))
    pols = h.polities()
    by = {p["polity_code"]: p for p in pols}
    if A.container not in by:
        print(f"FAIL: container {A.container} is not in the polity table")
        return 1

    decision = json.dumps({
        "unit_id": "(none — no reporting unit asks for this row)",
        "admin_name": A.name, "country": by[A.container]["polity_name"],
        "routing_reasoning": (
            "NOT created from a data row. " + A.why + " This row exists so its container's members "
            "tile it; say so on the page, and do not imply a source reports this territory "
            "separately when none in this repository does."),
        "routing_concerns": "no source in this repository reports this unit; created for "
                            "container completeness only",
        "era_of_this_page": f"{A.start}-{A.end}, the whole of this territory's modelled span",
        "proposed": {"polity_name": A.name, "iso3": A.iso, "start_year": A.start,
                     "end_year": A.end, "container_code": A.container,
                     "span_basis": A.why},
        "polygon_route": "registered_source_feature" if A.feature else "none_available",
        "polygon_source": A.source, "polygon_feature_id": A.feature,
        "polygon_detail": "", "polygon_reasoning": "assigned by the caller from the named source",
    }, indent=2)

    spec = h.page_spec_text()
    exemplar = h.EXEMPLAR.read_text(encoding="utf-8")[:6000] if h.EXEMPLAR.is_file() else "(none)"
    prompt = h.WIKI_PROMPT.format(spec=spec, exemplar=exemplar, decision=decision,
                                  code_precedent=h.code_precedent(pols, A.iso))
    taken = {f.stem.upper() for f in (h.REPO / "wiki" / "polities").glob("*.md")}
    existing = h.existing_territory_pages(pols, A.iso)
    edges = h.chain_edges(pols)
    slugs = h.polygon_slugs()

    res = runner.call(f"completeness-{h.norm(A.name)}", prompt, h.WIKI_SCHEMA)
    page = res.result if res.ok else None
    for attempt in range(2):
        if page is None:
            break
        obj = None
        if page["polity_code"] in taken:
            obj = f"polity_code {page['polity_code']} already has a page in wiki/polities/."
        obj = (obj or h.structural_page_objection(page, pols, A.iso)
               or h.duplicate_territory_objection(page, {"official_name": A.name}, existing)
               or h.bad_polygon_source(page, slugs) or h.unreciprocated(page, edges))
        if not obj:
            break
        print(f"  REJECT {A.name}: {obj.splitlines()[0][:110]}")
        r2 = runner.call(f"completeness-{h.norm(A.name)}-r{attempt + 1}",
                         prompt + f"\n\nA PREVIOUS ANSWER WAS REJECTED\n{'-' * 30}\n{obj}\n"
                                  f"Fix only what the objection names.", h.WIKI_SCHEMA, refresh=True)
        page = r2.result if r2.ok else None
    if page is None:
        print(f"FAIL: {A.name} — {res.error if not res.ok else 'no usable page'}")
        return 1
    left = (h.structural_page_objection(page, pols, A.iso)
            or h.duplicate_territory_objection(page, {"official_name": A.name}, existing)
            or h.bad_polygon_source(page, slugs) or h.unreciprocated(page, edges))
    if left:
        print(f"REFUSED {A.name}: objection unresolved after retries — {left.splitlines()[0][:110]}")
        return 1
    dest = h.REPO / "wiki" / "polities" / f"{page['polity_code'].lower()}.md"
    dest.write_text(h.render_page(page), encoding="utf-8")
    print(f"  wrote {dest.relative_to(h.REPO)}  ({page['polity_code']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
