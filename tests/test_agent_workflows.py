# -*- coding: utf-8 -*-
"""Tests for the composable agent layer: tagsets, expressions, result algebra, corpus tools,
pipelines, recipes, jobs and the MCP resources/prompts/completion surface."""

import asyncio
import json
import time
from pathlib import Path

import pandas as pd
import pytest
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.types import PromptReference

from kitconc.agent import progress
from kitconc.agent.actions import KitconcActions
from kitconc.agent.expressions import ExpressionError, evaluate, evaluate_column, evaluate_mask, log_likelihood
from kitconc.agent.mcp_server import build_server
from kitconc.agent.pipeline import validate_spec
from kitconc.agent.recipes import BUILTIN_DIR
from kitconc.agent.results import ToolFailure
from kitconc.agent.tagsets import build_mapping, categorize, detect_family, parse_pattern
from kitconc.agent.tools import PIPELINE_TOOLS, KitconcTools
from kitconc.kit_corpus import Corpus

# Pre-tagged texts: one sentence per line, word/TAG tokens.
UPOS = {  # spaCy-style Universal POS
    "t1.txt": "The/DET data/NOUN analysis/NOUN team/NOUN uses/VERB machine/NOUN learning/NOUN ./PUNCT\n"
              "Data/NOUN analysis/NOUN is/AUX a/DET process/NOUN of/ADP inspecting/VERB data/NOUN ./PUNCT",
    "t2.txt": "Machine/NOUN learning/NOUN models/NOUN need/VERB clean/ADJ data/NOUN ./PUNCT\n"
              "The/DET data/NOUN analysis/NOUN report/NOUN is/AUX ready/ADJ ./PUNCT",
    "t3.txt": "Good/ADJ data/NOUN quality/NOUN supports/VERB machine/NOUN learning/NOUN ./PUNCT\n"
              "Data/NOUN quality/NOUN means/VERB accurate/ADJ data/NOUN ./PUNCT",
}
UPOS_REF = {
    "r1.txt": "The/DET team/NOUN went/VERB home/NOUN ./PUNCT\nThe/DET weather/NOUN is/AUX good/ADJ ./PUNCT",
    "r2.txt": "A/DET good/ADJ team/NOUN likes/VERB data/NOUN ./PUNCT\nThe/DET home/NOUN is/AUX quiet/ADJ ./PUNCT",
}
MACMORPHO = {  # built-in Portuguese tagger style
    "p1.txt": "O/ART contrato/N de/PREP trabalho/N define/V o/ART salário/N mínimo/ADJ ./PU\n"
              "A/ART jornada/N de/PREP trabalho/N é/V longa/ADJ ./PU",
    "p2.txt": "O/ART salário/N mínimo/ADJ subiu/V ./PU\n"
              "O/ART contrato/N de/PREP trabalho/N foi/V assinado/PCP ./PU",
}
PLAIN = {
    "a.txt": "Corpus tools count words in texts . Words matter .",
    "b.txt": "Corpus tools count words in texts . Words matter .",
    "c.txt": "Another text with different words about corpus tools .",
}


def _write(folder: Path, texts: dict[str, str]) -> Path:
    folder.mkdir(parents=True)
    for name, text in texts.items():
        (folder / name).write_text(text, encoding="utf-8")
    return folder


@pytest.fixture(scope="module")
def ws(tmp_path_factory):
    base = tmp_path_factory.mktemp("workflows")
    workspace = str(base / "ws") + "/"
    Corpus(workspace, "upos", "english").add_texts(str(_write(base / "upos", UPOS)), tagged=True)
    Corpus(workspace, "upos_ref", "english").add_texts(str(_write(base / "upos_ref", UPOS_REF)), tagged=True)
    Corpus(workspace, "pt", "portuguese").add_texts(str(_write(base / "pt", MACMORPHO)), tagged=True)
    plain_src = _write(base / "plain", PLAIN)
    (plain_src / "index.sqlite").write_bytes(b"SQLite format 3\x00" + b"\x00" * 100)
    with pytest.warns(UserWarning):
        Corpus(workspace, "plain", "no-tagging").add_texts(str(plain_src))
    return workspace


@pytest.fixture()
def tools(ws):
    return KitconcTools(KitconcActions(ws))


def _rows(payload):
    return [dict(zip(payload["columns"], row)) for row in payload["rows"]]


# ---------------------------------------------------------------------------
# Tagsets
# ---------------------------------------------------------------------------


def test_tagset_families_and_categories():
    assert detect_family(["NN", "NN-TL", "JJ-HL", "IN", "AT", "NP"]) == "ptb_brown"
    assert detect_family(["NOUN", "ADP", "DET", "VERB", "PUNCT"]) == "universal"
    assert detect_family(["N", "PREP", "PREP+ART", "ART", "PU", "IN"]) == "macmorpho"
    assert detect_family(["*"]) == "none"
    assert categorize("NN-TL", "ptb_brown") == "NOUN"
    assert categorize("NP", "ptb_brown") == "PROPN"
    assert categorize("NNS$", "ptb_brown") == "NOUN"
    assert categorize("PREP+ART", "macmorpho") == "ADP"
    assert categorize("IN", "macmorpho") == "X"  # interjection, not a preposition
    assert categorize("AUX", "universal") == "VERB"
    mapping = build_mapping(["NE", "NN", "ADJA"], {"NE": "PROPN", "ADJ*": "ADJ"})
    assert mapping.category("NE") == "PROPN" and mapping.category("ADJA") == "ADJ"


def test_pattern_parsing():
    slots = parse_pattern("ADJ|NOUN word:of tag:NN* *")
    assert slots[0].categories == {"ADJ", "NOUN"}
    assert slots[1].words == {"of"}
    assert slots[2].raw_tags == ("NN*",)
    assert slots[3].any_word
    with pytest.raises(ValueError):
        parse_pattern("NOUNY")


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------


def test_expressions_filter_and_derive():
    frame = pd.DataFrame({"WORD": ["the", "data", "model"], "FREQUENCY": [10, 4, 1], "N-GRAM": ["a b", "c", "d e f"]})
    assert evaluate_mask("FREQUENCY >= 4 and not is_stopword(WORD)", frame).tolist() == [False, True, False]
    assert evaluate_mask("WORD in ['data', 'model']", frame).tolist() == [False, True, True]
    assert evaluate_column("words(col('N-GRAM'))", frame).tolist() == [2, 1, 3]
    assert evaluate_column("if_(FREQUENCY > 2, 'hi', 'lo')", frame).tolist() == ["hi", "hi", "lo"]
    assert evaluate("sum(FREQUENCY)", frame) == 15


def test_statistics():
    assert float(log_likelihood(10, 1000, 10, 1000)) == pytest.approx(0.0)
    assert float(log_likelihood(20, 1000, 10, 1000)) == pytest.approx(3.398, abs=1e-3)
    frame = pd.DataFrame({"TERM": ["stock", "stock purchase", "employee stock purchase plan"], "F": [10, 6, 4]})
    cvalue = evaluate_column("c_value(TERM, F)", frame).tolist()
    # "stock purchase" is nested in the 4-word term: log2(3) * (6 - 4)
    assert cvalue[1] == pytest.approx(3.1699, abs=1e-3)
    assert cvalue[2] == pytest.approx(4 * 2.3219, abs=1e-3)


@pytest.mark.parametrize("expression", ["__import__('os')", "WORD.upper()", "[w for w in WORD]",
                                        "open('x')", "lambda: 1"])
def test_expressions_reject_unsafe_code(expression):
    with pytest.raises(ExpressionError):
        evaluate(expression, pd.DataFrame({"WORD": ["a"]}))


# ---------------------------------------------------------------------------
# Corpus tools
# ---------------------------------------------------------------------------


def test_corpus_tagset_maps_universal_tags(tools):
    payload = tools.corpus_tagset("upos", limit=0)
    assert payload["tagset_family"] == "universal"
    rows = _rows(tools.result_page(payload["result_id"], limit=50))
    assert {r["TAG"]: r["CATEGORY"] for r in rows}["AUX"] == "VERB"


def test_term_candidates_with_universal_tags(tools):
    payload = tools.term_candidates("upos", limit=100)
    terms = {r["TERM"]: r for r in _rows(payload)}
    assert terms["machine learning"]["FREQUENCY"] == 3 and terms["machine learning"]["RANGE"] == 3
    assert terms["data analysis"]["FREQUENCY"] == 3
    assert all(r["PATTERN"] for r in terms.values())
    assert "is a" not in terms


def test_term_candidates_head_initial_portuguese(tools):
    terms = {r["TERM"]: r for r in _rows(tools.term_candidates("pt", limit=100))}
    assert terms["salário mínimo"]["PATTERN"] == "NOUN ADJ"
    assert terms["contrato de trabalho"]["FREQUENCY"] == 2


def test_term_candidates_custom_patterns_and_untagged_fallback(tools):
    custom = _rows(tools.term_candidates("upos", patterns=["NOUN word:of VERB"], min_freq=1,
                                         stopword_edges=False, limit=10))
    assert [r["TERM"] for r in custom] == ["process of inspecting"]
    plain = tools.term_candidates("plain", min_freq=2, limit=50)
    assert plain["analysis"] == "term_candidates"
    terms = {r["TERM"] for r in _rows(plain)}
    assert "corpus tools" in terms and "in" not in terms
    with pytest.raises(ToolFailure):
        tools.term_candidates("plain", mode="pos")


def test_context_mine_finds_definitions(tools):
    rows = _rows(tools.context_mine("upos", "data analysis"))
    assert len(rows) == 1 and "process" in rows[0]["SENTENCE"]


def test_text_stats_and_corpus_qa(tools):
    stats = _rows(tools.text_stats("plain", limit=10))
    assert {r["FILENAME"] for r in stats} == set(PLAIN)
    assert "_HASH" not in stats[0]
    qa = tools.corpus_qa("plain")
    checks = {i["check"]: i for i in qa["issues"]}
    assert checks["duplicates"]["files"] == ["a.txt = b.txt"]
    assert checks["source_binaries"]["files"] == ["index.sqlite"]
    assert "untagged" in checks


def test_subcorpus_create(tmp_path):
    src = _write(tmp_path / "src", {f"{y}_{i}.txt": f"Text {i} of year {y} ." for y in (2020, 2021) for i in range(2)})
    workspace = str(tmp_path / "ws") + "/"
    Corpus(workspace, "all", "no-tagging").add_texts(str(src))
    tools = KitconcTools(KitconcActions(workspace))
    created = tools.subcorpus_create("all", "y2020", file_pattern="^2020_")
    assert created["texts"] == 2
    assert tools.corpus_files("y2020")["files"] == ["2020_0.txt", "2020_1.txt"]
    with pytest.raises(ToolFailure):
        tools.subcorpus_create("all", "none", files=["missing.txt"])


# ---------------------------------------------------------------------------
# Result algebra
# ---------------------------------------------------------------------------


def test_join_derive_combine_aggregate(tools):
    domain = tools.term_candidates("upos", min_freq=1, limit=0)
    ref = tools.term_candidates("upos_ref", min_freq=1, limit=0)
    joined = tools.result_join(domain["result_id"], ref["result_id"], on="TERM", right_fields=["FREQUENCY"],
                               suffix="_REF", limit=0)
    assert "FREQUENCY_REF" in joined["columns"]
    scored = tools.result_derive(joined["result_id"], {
        "LL": "log_likelihood(FREQUENCY, corpus_tokens('upos'), FREQUENCY_REF, corpus_tokens('upos_ref'))",
        "LR": "log_ratio(FREQUENCY, corpus_tokens('upos'), FREQUENCY_REF, corpus_tokens('upos_ref'))"}, limit=0)
    absent = _rows(tools.result_filter(scored["result_id"], where="FREQUENCY_REF == 0", sort_by="LL", limit=100))
    assert {"machine learning", "data analysis"} <= {r["TERM"] for r in absent}
    assert all(r["LL"] > 0 and r["LR"] > 0 for r in absent)
    data_row = _rows(tools.result_filter(scored["result_id"], where="TERM == 'data'"))[0]
    assert data_row["FREQUENCY_REF"] == 1  # 'data' also occurs once in the reference corpus
    only_domain = tools.result_combine([domain["result_id"], ref["result_id"]], "difference", key="TERM", limit=100)
    assert "team" not in {r["TERM"] for r in _rows(only_domain)}
    stacked = tools.result_combine([domain["result_id"], ref["result_id"]], "union", key="TERM",
                                   source_column="CORPUS", labels=["upos", "upos_ref"], deduplicate=False, limit=0)
    agg = _rows(tools.result_aggregate(stacked["result_id"], ["TERM"], {"N": "nunique(CORPUS)"}, sort_by="N"))
    assert agg[0]["N"] == 2
    assert tools.results.get(stacked["result_id"]).parents == [domain["result_id"], ref["result_id"]]


def test_empty_results_keep_columns_and_flow_through(tools):
    empty = tools.analyze_wordlist("upos", search="zzzz*", limit=5)
    assert empty["total"] == 0 and empty["columns"][:2] == ["N", "WORD"]
    enriched = tools.result_enrich(empty["result_id"], "WORD", "upos", ["example"])
    assert enriched["total"] == 0
    filtered = tools.result_filter(empty["result_id"], where="FREQUENCY > 1")
    assert filtered["total"] == 0


def test_result_create_enrich_and_errors(tools):
    seeds = tools.result_create(["TERM"], [["data analysis"], ["machine learning"]])
    enriched = _rows(tools.result_enrich(seeds["result_id"], "TERM", "upos",
                                         ["frequency", "dispersion", "example", "definition"]))
    assert enriched[0]["HITS"] == 3 and enriched[0]["DEFINITION_FILE"] == "t1.txt"
    assert enriched[1]["EXAMPLE"]
    with pytest.raises(ToolFailure) as info:
        tools.result_filter(seeds["result_id"], where="NOPE > 1")
    assert info.value.code == "INVALID_EXPRESSION"


# ---------------------------------------------------------------------------
# Pipelines
# ---------------------------------------------------------------------------


def test_pipeline_references_foreach_when_and_errors(tools, tmp_path):
    pipeline = {
        "params": {"corpus": {"required": True}, "words": {"default": ["data", "nope"]},
                   "export": {"default": None}},
        "steps": [
            {"id": "terms", "tool": "term_candidates", "args": {"corpus": "$params.corpus", "limit": 0}},
            {"id": "top", "tool": "result_filter",
             "args": {"result_id": "$terms.result_id", "where": "FREQUENCY >= ${params.min}", "limit": 5}},
            {"id": "per_word", "tool": "analyze_kwic", "foreach": "$params.words", "as": "w",
             "args": {"corpus": "$params.corpus", "node": "$w", "limit": 1}, "continue_on_error": True},
            {"id": "export", "tool": "result_export", "when": "$params.export",
             "args": {"result_id": "$top.result_id", "output_path": "$params.export"}},
        ],
        "output": "top",
    }
    out = tools.pipeline_run(pipeline, {"corpus": "upos", "min": 3})
    status = {s["id"]: s["status"] for s in out["steps"]}
    assert status == {"terms": "ok", "top": "ok", "per_word": "ok", "export": "skipped"}
    assert all(r[3] >= 3 for r in out["output"]["rows"])
    assert set(out["result_ids"]) == {"terms", "top"}
    target = tmp_path / "top.tsv"
    out = tools.pipeline_run(pipeline, {"corpus": "upos", "min": 1, "export": str(target)})
    assert target.exists() and out["steps"][-1]["status"] == "ok"
    with pytest.raises(ToolFailure) as info:
        tools.pipeline_run(pipeline, {})
    assert info.value.code == "MISSING_PARAMS"


def test_pipeline_validation_messages(tools):
    errors = validate_spec({"steps": [
        {"id": "a", "tool": "nope"},
        {"id": "b", "tool": "result_page", "args": {"result_id": "$c.result_id"}},
        {"id": "c", "tool": "corpus_delete", "args": {"corpus": "$params.x"}},
    ]}, set(PIPELINE_TOOLS))
    assert any("unknown or disallowed tool 'nope'" in e for e in errors)
    assert any("'c' is not a param or an earlier step" in e for e in errors)
    assert any("disallowed tool 'corpus_delete'" in e for e in errors)
    assert any("'$params.x' is not declared" in e for e in errors)
    assert tools.pipeline_validate({"steps": [{"tool": "workspace_info"}]})["valid"]


# ---------------------------------------------------------------------------
# Recipes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", sorted(BUILTIN_DIR.glob("*.json")), ids=lambda p: p.stem)
def test_builtin_recipes_are_valid(path):
    recipe = json.loads(path.read_text(encoding="utf-8"))
    assert recipe["name"] == path.stem
    assert recipe.get("title") and recipe.get("description") and recipe.get("interpretation")
    assert validate_spec(recipe, set(PIPELINE_TOOLS)) == []


RECIPE_RUNS = {
    "corpus-profile": {"corpus": "upos", "top": 5},
    "word-profile": {"corpus": "upos", "node": "data", "min_freq": 1, "sample": 2},
    "compare-corpora": {"corpus_a": "upos", "corpus_b": "upos_ref", "p_value": 0.5, "min_range": 1, "min_freq": 1},
    "synonym-comparison": {"corpus": "upos", "words": ["data", "learning"], "min_freq": 1},
    "keyword-report": {"corpus": "upos", "p_value": 0.5, "min_range": 1, "top": 5},
    "glossary-candidates": {"corpus": "upos", "min_freq": 2, "min_range": 1, "top": 5},
    "glossary-contrastive": {"corpus": "upos", "ref_corpus": "upos_ref", "min_freq": 1, "min_range": 1,
                             "min_ll": 0, "min_log_ratio": 0},
    "lexical-bundles": {"corpus": "upos", "size": 2, "min_per_million": 1, "min_range": 1, "examples": 2},
    "collocation-entry": {"corpus": "upos", "node": "data", "min_freq": 1},
    "corpus-qa": {"corpus": "plain"},
    "word-frequency-comparison": {"corpora": ["upos", "upos_ref"], "words": ["data", "team"]},
}


def test_every_builtin_recipe_has_a_run_test():
    assert set(RECIPE_RUNS) == {p.stem for p in BUILTIN_DIR.glob("*.json")}


@pytest.mark.parametrize("name", sorted(RECIPE_RUNS))
def test_builtin_recipes_run(tools, name):
    out = tools.recipe_run(name, RECIPE_RUNS[name])
    assert out["recipe"] == name and out["interpretation"]
    assert all(step["status"] in ("ok", "skipped") for step in out["steps"]), out["steps"]
    assert out["output"] is not None


def test_recipe_save_list_and_override(tools, ws):
    recipe = json.loads((BUILTIN_DIR / "corpus-qa.json").read_text(encoding="utf-8"))
    recipe["title"] = "My QA"
    saved = tools.recipe_save(recipe)
    try:
        assert saved["overrides_builtin"] is True
        assert tools.recipe_show("corpus-qa")["source"] == "user"
        with pytest.raises(ToolFailure):
            tools.recipe_save(recipe)
        with pytest.raises(ToolFailure):
            tools.recipe_save({"name": "Bad Name", "steps": []})
    finally:
        Path(saved["path"]).unlink()
    assert tools.recipe_show("corpus-qa")["source"] == "builtin"
    assert {r["name"] for r in tools.recipe_list(tag="terminology")["recipes"]} == {
        "glossary-candidates", "glossary-contrastive"}


# ---------------------------------------------------------------------------
# Jobs and progress
# ---------------------------------------------------------------------------


def _wait(tools, job_id, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = tools.job_status(job_id)
        if status["status"] in ("succeeded", "failed", "cancelled"):
            return status
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def test_job_runs_recipe_and_persists(tools, ws):
    started = tools.job_start(recipe="corpus-qa", params={"corpus": "plain"})
    final = _wait(tools, started["job_id"])
    assert final["status"] == "succeeded" and final["progress"]["fraction"] == 1.0
    output = tools.job_status(started["job_id"], include_output=True)["output"]
    assert output["recipe"] == "corpus-qa"
    fresh = KitconcTools(KitconcActions(ws))  # e.g. after a server restart
    assert fresh.job_status(started["job_id"])["status"] == "succeeded"
    assert started["job_id"] in {j["job_id"] for j in fresh.job_status()["jobs"]}


def test_job_cancel_and_failure(tools):
    def slow():
        for i in range(200):
            progress.report(i, 200, "working")
            time.sleep(0.01)
        return {"done": True}

    job = tools.jobs.start("tool", "slow", {}, slow)
    time.sleep(0.05)
    tools.job_cancel(job["job_id"])
    assert _wait(tools, job["job_id"])["status"] == "cancelled"
    failed = tools.job_start(tool="analyze_kwic", args={"corpus": "missing", "node": "x"})
    final = _wait(tools, failed["job_id"])
    assert final["status"] == "failed" and final["error"]["code"] == "CORPUS_NOT_FOUND"
    with pytest.raises(ToolFailure):
        tools.job_start(tool="corpus_delete", args={"corpus": "upos"})


def test_progress_scopes_compose():
    seen = []
    with progress.install(lambda fraction, message: seen.append((round(fraction, 3), message))):
        with progress.scope(1, 4, "step2"):
            progress.report(1, 2, "half")
    assert (0.375, "step2 / half") in seen


# ---------------------------------------------------------------------------
# MCP surface: resources, prompts, completion, progress notifications
# ---------------------------------------------------------------------------


def _session(ws, scenario):
    async def _run():
        server = build_server(workspace=ws)
        async with create_connected_server_and_client_session(server._mcp_server) as session:
            return await scenario(session)

    return asyncio.run(_run())


def test_mcp_prompts_resources_and_completion(ws):
    async def scenario(session):
        prompts = {p.name for p in (await session.list_prompts()).prompts}
        rendered = await session.get_prompt("glossary-candidates", {"corpus": "upos", "top": "10"})
        plan = await session.get_prompt("plan-analysis", {"question": "Which terms are typical?"})
        resources = {str(r.uri) for r in (await session.list_resources()).resources}
        templates = {t.uriTemplate for t in (await session.list_resource_templates()).resourceTemplates}
        text = await session.read_resource("kitconc://corpus/upos/files/t1.txt")
        corpora = await session.read_resource("kitconc://corpora")
        completion = await session.complete(PromptReference(type="ref/prompt", name="word-profile"),
                                            {"name": "corpus", "value": "up"})
        return prompts, rendered, plan, resources, templates, text, corpora, completion

    prompts, rendered, plan, resources, templates, text, corpora, completion = _session(ws, scenario)
    assert {"glossary-candidates", "word-profile", "plan-analysis"} <= prompts
    message = rendered.messages[0].content.text
    assert 'recipe_run' in message and '"top": 10' in message
    assert "pipeline_run" in plan.messages[0].content.text
    assert {"kitconc://corpora", "kitconc://guide/overview", "kitconc://guide/terminology"} <= resources
    assert "kitconc://results/{result_id}" in templates
    assert "Data analysis is a process" in text.contents[0].text
    assert "upos_ref" in corpora.contents[0].text
    assert completion.completion.values == ["upos", "upos_ref"]


def test_mcp_progress_notifications(ws):
    updates = []

    async def on_progress(value, total, message):
        updates.append((value, total, message))

    async def scenario(session):
        return await session.call_tool("term_candidates", {"corpus": "upos", "limit": 1},
                                       progress_callback=on_progress)

    result = _session(ws, scenario)
    assert not result.isError
    assert updates and updates[-1][1] == 100.0


def test_mcp_guide_read_includes_function_reference(ws):
    async def scenario(session):
        return await session.call_tool("guide_read", {"topic": "expressions"})

    payload = json.loads(_session(ws, scenario).content[0].text)
    assert "Function reference" in payload["text"] and "c_value" in payload["text"]
