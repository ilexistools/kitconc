# -*- coding: utf-8 -*-
"""MCP resources, prompts and argument completion for the Kitconc server.

Resources expose read-only context (corpora, texts, stored results, recipes, guides, jobs) for clients
that let users attach them; everything is also reachable through tools for clients that don't.
Prompts turn each recipe into a slash command and add an open ``plan-analysis`` prompt.
"""

from __future__ import annotations

import functools
import io
import json
from typing import Any

from mcp.server.fastmcp.prompts.base import Prompt, PromptArgument
from mcp.types import Completion, PromptReference, ResourceTemplateReference

from kitconc.agent.results import ToolFailure, clean
from kitconc.agent.tools import KitconcTools, list_guides

CORPUS_ARGUMENTS = {"corpus", "corpus_a", "corpus_b", "ref_corpus"}

REPORTING_RULES = (
    "Report in the user's language. State the corpus sizes, measures and thresholds used, quote "
    "concordance lines or example sentences with their file names as evidence, and say what the data "
    "cannot show. Keep large tables on the server (result_id) and show only what supports the answer; "
    "offer result_export for full tables."
)


def _json(value: Any) -> str:
    return json.dumps(clean(value), ensure_ascii=False, indent=2, default=str)


def _guarded(fn):
    """Returns structured errors as the resource text instead of failing the read."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ToolFailure as exc:
            return _json(exc.payload())
    return wrapper


def register_resources(server, tools: KitconcTools) -> None:
    """Registers static resources and resource templates."""

    @server.resource("kitconc://corpora", name="corpora", title="Corpora in the workspace",
                     mime_type="application/json")
    @_guarded
    def corpora() -> str:
        """Corpora in the current workspace with size statistics."""
        return _json(tools.corpus_list())

    @server.resource("kitconc://corpus/{corpus}", name="corpus", title="Corpus metadata",
                     mime_type="application/json")
    @_guarded
    def corpus_info(corpus: str) -> str:
        """Metadata and size statistics of one corpus."""
        return _json(tools.corpus_info(corpus))

    @server.resource("kitconc://corpus/{corpus}/files", name="corpus-files", title="Corpus text files",
                     mime_type="application/json")
    @_guarded
    def corpus_files(corpus: str) -> str:
        """Text file names of a corpus."""
        return _json(tools.corpus_files(corpus, limit=5000))

    @server.resource("kitconc://corpus/{corpus}/files/{filename}", name="corpus-file", title="Corpus text",
                     mime_type="text/plain")
    @_guarded
    def corpus_file(corpus: str, filename: str) -> str:
        """Full text of one corpus file, one sentence per line."""
        return tools.corpus_read_file(corpus, filename, max_lines=5000)["text"]

    @server.resource("kitconc://results/{result_id}", name="result", title="Stored result (TSV)",
                     mime_type="text/tab-separated-values")
    @_guarded
    def result(result_id: str) -> str:
        """All rows of a stored result as tab-separated values."""
        buffer = io.StringIO()
        tools.results.get(result_id).frame.to_csv(buffer, sep="\t", index=False)
        return buffer.getvalue()

    @server.resource("kitconc://recipes", name="recipes", title="Recipes", mime_type="application/json")
    @_guarded
    def recipes() -> str:
        """Available recipes with descriptions and parameters."""
        return _json(tools.recipe_list())

    @server.resource("kitconc://recipes/{name}", name="recipe", title="Recipe JSON", mime_type="application/json")
    @_guarded
    def recipe(name: str) -> str:
        """Full JSON of one recipe."""
        return _json(tools.recipe_show(name))

    @server.resource("kitconc://jobs/{job_id}", name="job", title="Job status", mime_type="application/json")
    @_guarded
    def job(job_id: str) -> str:
        """Status and output of a background job."""
        return _json(tools.job_status(job_id, include_output=True))

    for guide in list_guides():
        _register_guide(server, tools, guide["name"], guide["title"])


def _register_guide(server, tools: KitconcTools, name: str, title: str) -> None:
    @server.resource(f"kitconc://guide/{name}", name=f"guide-{name}", title=title, mime_type="text/markdown")
    def guide() -> str:
        return tools.guide_read(name)["text"]


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


def _coerce(value: str) -> Any:
    """Prompt arguments arrive as strings; accept JSON for lists, numbers and objects."""
    text = (value or "").strip()
    if text[:1] in "[{" or text in ("true", "false", "null") or text.replace(".", "", 1).lstrip("-").isdigit():
        try:
            return json.loads(text)
        except ValueError:
            pass
    if "," in text and not text.startswith(("'", '"')):
        return [part.strip() for part in text.split(",") if part.strip()]
    return text


def _recipe_prompt(tools: KitconcTools, recipe: dict[str, Any]) -> Prompt:
    name = recipe["name"]
    declared = recipe.get("params") or {}
    arguments = []
    for key, decl in declared.items():
        decl = decl if isinstance(decl, dict) else {"default": decl}
        description = decl.get("description", "")
        if decl.get("type") == "array":
            description += " (comma-separated or JSON list)"
        if "default" in decl and decl["default"] is not None:
            description += f" Default: {decl['default']}."
        arguments.append(PromptArgument(name=key, description=description.strip(),
                                        required=bool(decl.get("required"))))

    def render(**kwargs: str) -> str:
        params = {key: _coerce(value) for key, value in kwargs.items() if value not in (None, "")}
        for key, decl in declared.items():
            if isinstance(decl, dict) and decl.get("type") == "array" and isinstance(params.get(key), str):
                params[key] = [params[key]]
        current = tools._recipe(name)[0]
        return (
            f"Task: {current.get('title', name)} — {current.get('description', '')}\n\n"
            f"1. Run the Kitconc tool `recipe_run` with name=\"{name}\" and params={json.dumps(params, ensure_ascii=False)}.\n"
            "   If the corpus is large or the recipe enriches many rows, use `job_start` with the same recipe and "
            "poll `job_status`.\n"
            "2. If a step fails or the question needs something different (other thresholds, patterns, corpora "
            f"or extra steps), call `recipe_show(\"{name}\")`, adapt the pipeline and run it with `pipeline_run`.\n"
            "3. Read the output and, where useful, page intermediate results via their result_ids "
            "(`result_page`, `result_filter`).\n"
            f"4. Interpretation notes: {current.get('interpretation', 'Explain what the results show.')}\n\n"
            f"{REPORTING_RULES}"
        )

    return Prompt(name=name, title=recipe.get("title"), description=recipe.get("description"),
                  arguments=arguments, fn=render)


PLAN_PROMPT = """\
Research question: {question}
{corpus_line}
Plan and carry out a corpus analysis with the Kitconc tools:

1. Orient yourself: `workspace_info` (corpora and sizes){qa_hint}. Check `recipe_list` — a recipe may
   already answer the question or be a good starting point (`recipe_show` to see its steps).
2. Translate the question into operations: which units (words, terms, n-grams, texts), which
   comparison (reference corpus, subcorpora via `subcorpus_create`, word lists), which measures
   (`guide_read("measures")`) and which evidence (concordances, examples, definitions).
3. Prefer composition over large pages: analyses return result_ids; combine them with
   result_filter / result_derive / result_join / result_combine / result_aggregate / result_enrich.
   For several steps write a pipeline (`guide_read("pipelines")`), check it with
   `pipeline_validate`, then `pipeline_run` — or `job_start` if it may take minutes.
4. Verify: read KWIC lines or texts behind surprising numbers; watch for duplicates, single-text
   effects (range, DP) and small frequencies.
5. If the workflow is reusable, offer to save it with `recipe_save`.

{rules}
"""


def register_prompts(server, tools: KitconcTools) -> None:
    for item in tools.recipe_list()["recipes"]:
        try:
            recipe = tools._recipe(item["name"])[0]
        except ToolFailure:
            continue
        server.add_prompt(_recipe_prompt(tools, recipe))

    def plan(question: str, corpus: str = "") -> str:
        corpus_line = f"Corpus: {corpus}\n" if corpus else ""
        qa_hint = f" and `corpus_qa(\"{corpus}\")`" if corpus else " and `corpus_qa` on the corpora you will use"
        return PLAN_PROMPT.format(question=question, corpus_line=corpus_line, qa_hint=qa_hint, rules=REPORTING_RULES)

    server.add_prompt(Prompt(
        name="plan-analysis", title="Plan a corpus analysis",
        description="Design and run an analysis for any research question by composing Kitconc tools.",
        arguments=[PromptArgument(name="question", description="The research question.", required=True),
                   PromptArgument(name="corpus", description="Corpus id (optional).", required=False)],
        fn=plan,
    ))


# ---------------------------------------------------------------------------
# Completion
# ---------------------------------------------------------------------------


def register_completion(server, tools: KitconcTools) -> None:
    @server.completion()
    async def complete(ref, argument, context) -> Completion | None:
        name, prefix = argument.name, (argument.value or "").lower()
        values: list[str] = []
        try:
            if name in CORPUS_ARGUMENTS or name == "corpora":
                values = tools._corpus_ids()
            elif isinstance(ref, ResourceTemplateReference) and name == "result_id":
                values = [r["result_id"] for r in tools.results.list(limit=50)]
            elif isinstance(ref, ResourceTemplateReference) and name == "name" and "recipes" in ref.uri:
                values = [r["name"] for r in tools.recipe_list()["recipes"]]
            elif isinstance(ref, ResourceTemplateReference) and name == "job_id":
                values = [j["job_id"] for j in tools.jobs.list()[:50]]
            elif isinstance(ref, ResourceTemplateReference) and name == "filename":
                corpus = (context.arguments or {}).get("corpus") if context else None
                if corpus:
                    values = tools.corpus_files(corpus, limit=5000)["files"]
            elif isinstance(ref, PromptReference) and name == "mode":
                values = ["auto", "pos", "stopwords"]
        except ToolFailure:
            return None
        matches = [v for v in values if v.lower().startswith(prefix)]
        return Completion(values=matches[:100], total=len(matches), hasMore=len(matches) > 100)
