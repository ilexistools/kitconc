<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/kitconc-logo-dark.png">
    <img src="docs/assets/kitconc-logo-light.png" alt="Kitconc logo" width="190">
  </picture>
</p>

<h1 align="center">Kitconc</h1>

<p align="center">
  <b>Corpus linguistics for Python — and for your AI assistant.</b><br>
  Concordances, keywords, collocations, terminology and corpus comparison that Claude, Codex, Cursor
  or any MCP client can run for you, step by step and with evidence.
</p>

<p align="center">
  <a href="https://pypi.org/project/kitconc/"><img alt="PyPI" src="https://img.shields.io/pypi/v/kitconc?color=19b5b5"></a>
  <a href="https://pypi.org/project/kitconc/"><img alt="Python" src="https://img.shields.io/pypi/pyversions/kitconc"></a>
  <a href="https://github.com/ilexistools/kitconc/actions/workflows/tests.yml"><img alt="Tests" src="https://github.com/ilexistools/kitconc/actions/workflows/tests.yml/badge.svg"></a>
  <a href="LICENSE.txt"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-0a4a4a"></a>
  <a href="docs/MCP.md"><img alt="MCP ready" src="https://img.shields.io/badge/MCP-ready-19b5b5"></a>
  <a href="#install-the-agent-skill"><img alt="Agent skill: Claude and Codex" src="https://img.shields.io/badge/skill-Claude%20%7C%20Codex-0a4a4a"></a>
</p>

<p align="center">
  <a href="#use-kitconc-with-ai">Use with AI</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="docs/MCP.md">MCP docs</a> ·
  <a href="#recipes">Recipes</a> ·
  <a href="#usage-examples">Python examples</a> ·
  <a href="CHANGES.txt">Changelog</a>
</p>

---

Kitconc is a package for Corpus Linguistics and text analysis with Python.
It contains, among other things, tools for creating:

* Corpora (from TXT, PDF, DOCX, ODT, EPUB, HTML/XHTML and XML files)
* Frequency wordlists and lemma (headword) lists
* Keywords (Log-Likelihood, Chi-Square, TF-IDF, Text Dispersion Keyness) against bundled
  reference lists or your own reference corpus, with effect sizes and negative keywords
* Concordance lines (KWIC and sentence-based), with wildcards, context search, random samples
  and KWIC pattern frequency
* Collocates (T-score, MI, MI2, MI3, Log-Likelihood, Dice, LogDice, LogRatio, Z-score and more)
* Clusters, N-gram lists and p-frames (n-grams with open slots)
* Dispersion plots and dispersion measures (Range, Juilland's D, Gries' DP)
* Word clouds, file view and Excel data files
* Semantic search with sentence embeddings
* Term candidates and glossaries, corpus quality checks, subcorpora and corpus comparison

The package is built on top of platforms and packages for scientific research: numpy, pandas, XlsxWriter and matplotlib. Its corpus tokenization and tagging pipeline uses built-in dependency-free components.

**Three ways to use it:** a desktop app (`kitconc-app`), a Python API (`kitconc.kit_corpus.Corpus`),
and an **AI agent interface** — an MCP server, a CLI and a ready-made skill for Claude and Codex.


Use Kitconc with AI
=========

Ask your assistant questions like these and let it do the corpus work:

> *"Check my `contracts` corpus for problems, then build a glossary of its 60 most relevant terms with an example and a definition for each, and export it to `glossary.xlsx`."*
>
> *"How is* sustainability *used in the 2020s news compared with the 2010s? Show keywords, collocates and a few concordance lines."*
>
> *"Compare* big, large *and* huge *in my learner corpus: frequencies, shared and exclusive collocates, and examples."*
>
> *"Which lexical bundles characterize these research articles? Group them by function for an EAP class."*

What the assistant gets:

| Capability | What it means for the agent |
|---|---|
| **55 described tools** | Corpora, concordances, keywords, collocates, clusters, n-grams, p-frames, dispersion, lemmas, terms, definitions, per-text statistics, semantic search |
| **Results that stay on the server** | Every analysis returns a `result_id` and one compact page; the agent filters, joins, scores and enriches results instead of copying tables into the chat |
| **A result algebra** | `result_filter`, `result_derive` (safe expressions: `per_million`, `log_likelihood`, `log_ratio`, `c_value`...), `result_join`, `result_combine`, `result_aggregate`, `result_enrich` (examples, definitions, dispersion, collocates per row), `result_export` |
| **Pipelines and recipes** | Whole studies in one call; 11 editable recipes from corpus QA to domain-specific glossaries |
| **Any POS tagset** | Brown/Penn, Universal POS (spaCy), Mac-Morpho or untagged corpora — term patterns such as `ADJ NOUN` work everywhere |
| **Long jobs** | Background jobs with progress and cancellation for large corpora |
| **Guardrails** | Structured errors with hints, read-only mode, confirmation for destructive actions, built-in guides on measures and methods |

```mermaid
flowchart LR
    A["AI assistant<br/>Claude · Codex · Cursor · VS Code"] -- "MCP or kitconc-tool" --> B["Kitconc tools"]
    B --> C[("Workspace<br/>corpora")]
    B --> D["Stored results<br/>result_id"]
    D --> E["Result algebra<br/>filter · join · derive · enrich"]
    E --> F["Pipelines & recipes"]
    F --> G["Answer with evidence<br/>+ .xlsx export"]
```

Quick start
-------------

**1. Install** (Python 3.10+):

For an agent-only setup, you do **not** need to install Kitconc globally with `pip`. With `uv` available, install the bundled skill for Claude and Codex directly from PyPI:

```bash
uvx --from kitconc kitconc-skill install
```

`uvx` downloads Kitconc into a temporary environment to run the installer. The skill can then launch Kitconc tools through `uvx` when needed. To make Kitconc commands available globally, use the persistent installation below instead.

```bash
pip install kitconc            # or: uv tool install kitconc
pip install "kitconc[full]"    # optional: semantic search with sentence embeddings
```

This gives you `kitconc-app` (desktop), `kitconc-mcp` (MCP server), `kitconc-tool` (CLI for agents)
and `kitconc-skill` (skill installer).

**2. Connect your assistant** to a workspace folder (it holds your corpora):

<details open>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add kitconc -- uvx --from kitconc kitconc-mcp --workspace /path/to/kitconc_workspace
```
</details>

<details>
<summary><b>Codex</b> (<code>~/.codex/config.toml</code>)</summary>

```toml
[mcp_servers.kitconc]
command = "uvx"
args = ["--from", "kitconc", "kitconc-mcp", "--workspace", "/path/to/kitconc_workspace"]
```
</details>

<details>
<summary><b>Claude Desktop, Cursor and other <code>mcpServers</code> clients</b></summary>

```json
{
  "mcpServers": {
    "kitconc": {
      "command": "uvx",
      "args": ["--from", "kitconc", "kitconc-mcp", "--workspace", "/path/to/kitconc_workspace"]
    }
  }
}
```
</details>

<details>
<summary><b>VS Code</b> (<code>.vscode/mcp.json</code>)</summary>

```json
{
  "servers": {
    "kitconc": {
      "type": "stdio",
      "command": "uvx",
      "args": ["--from", "kitconc", "kitconc-mcp", "--workspace", "/path/to/kitconc_workspace"]
    }
  }
}
```
</details>

<details>
<summary><b>HTTP / Docker</b></summary>

```bash
kitconc-mcp --transport streamable-http --host 127.0.0.1 --port 8001 --workspace /path/to/kitconc_workspace
# clients connect to http://127.0.0.1:8001/mcp — see "Installation and usage with Docker" below
```
</details>

**3. Ask.** Start with *"What corpora do I have?"* or *"Create a corpus called `ads` from
`/data/texts/ads` in English and check it for problems."* MCP clients that support prompts also
list every recipe as a prompt (slash command), plus `plan-analysis` for open questions.

### Install the agent skill

The Kitconc skills teach Claude and Codex how to work with corpora and how to author reusable
recipes. The general `kitconc` skill explains analysis and evidence; `kitconc-recipe-author` guides
the user from an analysis goal through recipe design, validation, optional execution and saving.
Both follow the open Agent Skills format and support MCP or the CLI.

```bash
uvx --from kitconc kitconc-skill install                   # no pip install required
kitconc-skill install                                      # if Kitconc is already installed
uvx --from kitconc kitconc-skill install --target codex    # install for Codex only
uvx --from kitconc kitconc-skill install --scope project   # install into this repository
```

The installer installs both skills. Sources: [`kitconc`](kitconc/agent/skill/kitconc/SKILL.md) and
[`kitconc-recipe-author`](kitconc/agent/skill/kitconc-recipe-author/SKILL.md). Copy either folder
manually into any skills directory if you prefer.

### No MCP? Use the CLI

`kitconc-tool` runs exactly the same tools from a terminal and prints JSON, which is ideal for
coding agents and scripts:

```bash
kitconc-tool --workspace ./kitconc_workspace workspace_info
kitconc-tool analyze_kwic '{"corpus": "ads", "node": "experience", "sample": 10}'
kitconc-tool recipe_run '{"name": "glossary-candidates", "params": {"corpus": "ads", "export_path": "glossary.xlsx"}}'
kitconc-tool --list
```

### Recipes

Ready-made, editable pipelines. Agents run them with `recipe_run`, adapt them with
`recipe_show` + `pipeline_run`, and save new ones with `recipe_save`.

To have an assistant guide recipe creation, ask for the outcome in everyday terms, for example:

- “Create a reusable recipe that finds frequent adjective–noun terms and adds corpus examples.”
- “Adapt `glossary-candidates` to compare the results with my reference corpus, validate it, and
  save it as `my-domain-glossary`.”
- “Draft a recipe for comparing two corpora by keyword and log ratio; show me the plan before
  saving.”

The `kitconc-recipe-author` skill checks available corpora and existing recipes, explains the
workflow and its assumptions, validates the pipeline, and can run and save it when requested. A
saved user recipe is stored in `<workspace>/recipes/` and is available through `recipe_list`.
See the [recipe authoring guide](kitconc/agent/guides/recipes.md#creating-a-recipe-with-an-assistant)
for the detailed workflow.

| Recipe | Answers |
|---|---|
| `corpus-qa` | Is the corpus clean? (binary files, duplicates, encoding, outliers) |
| `corpus-profile` | What is this corpus like? (size, texts, content words, keywords, phraseology, terms) |
| `word-profile` | How is this word used? (dispersion, collocates, clusters, definitions, KWIC sample) |
| `synonym-comparison` | How do these near-synonyms differ? (shared vs. exclusive collocates) |
| `collocation-entry` | Collocation-dictionary entry grouped by part of speech |
| `keyword-report` | What is typical of this corpus? (LL + log-ratio, Bonferroni, dispersion, examples) |
| `compare-corpora` | What distinguishes corpus A from corpus B? |
| `word-frequency-comparison` | How frequent are these words across corpora, per million? |
| `lexical-bundles` | Which recurrent sequences and frames characterize the corpus? |
| `glossary-candidates` | Which terms belong in a glossary? (C-value, examples, definitions) |
| `glossary-contrastive` | Which terms are specific to this domain compared with a reference corpus? |

Learn more: [docs/MCP.md](docs/MCP.md) (full reference) · built-in guides on
[measures](kitconc/agent/guides/measures.md), [terminology](kitconc/agent/guides/terminology.md),
[pipelines](kitconc/agent/guides/pipelines.md) and [expressions](kitconc/agent/guides/expressions.md).

#### Create your own recipe

A recipe is a reusable JSON pipeline. It declares the inputs (`params`), the tools to run in order
(`steps`), which step to return (`output`), and notes for interpreting the result. Start from a
built-in recipe with `recipe_show`, or create a new JSON file like this:

```json
{
  "name": "term-shortlist",
  "title": "Term shortlist",
  "description": "Find and rank term candidates, then add example contexts.",
  "tags": ["terminology"],
  "params": {
    "corpus": {"type": "string", "required": true, "description": "Corpus id."},
    "min_freq": {"type": "integer", "default": 3},
    "top": {"type": "integer", "default": 25}
  },
  "steps": [
    {"id": "candidates", "tool": "term_candidates",
     "args": {"corpus": "$params.corpus", "min_freq": "$params.min_freq", "limit": 0}},
    {"id": "scored", "tool": "result_derive",
     "args": {"result_id": "$candidates.result_id",
              "columns": {"CVALUE": "round(c_value(TERM, FREQUENCY), 2)"}, "limit": 0}},
    {"id": "shortlist", "tool": "result_filter",
     "args": {"result_id": "$scored.result_id", "where": "CVALUE > 0",
              "sort_by": "CVALUE", "keep": "$params.top", "limit": "$params.top"}},
    {"id": "evidence", "tool": "result_enrich",
     "args": {"result_id": "$shortlist.result_id", "column": "TERM",
              "corpus": "$params.corpus", "add": ["example"],
              "max_rows": "$params.top", "limit": "$params.top"}}
  ],
  "output": "evidence",
  "interpretation": "Review the examples before deciding which candidates belong in the glossary."
}
```

Each step has a unique `id`, a tool name and its `args`. Reference parameters with `"$params.name"`
and earlier step outputs with expressions such as `"$candidates.result_id"`; a whole-string
reference keeps its original type. Use `${params.name}` when inserting a value inside a longer string.
For example, `"exports/${params.corpus}.xlsx"` creates a corpus-specific export path.

Before saving, you can check the structure and references with `pipeline_validate`. `recipe_save`
also validates them and writes the recipe to `<workspace>/recipes/<name>.json`. Give user recipes a
new name rather than reusing a built-in name, unless you intend to override it. Names use lowercase
letters, digits, hyphens or underscores. Saving an existing user recipe requires `overwrite: true`.

For MCP, call `recipe_save` with the JSON above as its `recipe` argument. With the CLI, save a
request file containing `{"recipe": ...}` (wrap the recipe object above in `recipe`) and run:

```bash
kitconc-tool recipe_save - < recipe-request.json
kitconc-tool recipe_list '{"tag": "terminology"}'
kitconc-tool recipe_run '{"name": "term-shortlist", "params": {"corpus": "ads", "min_freq": 4, "top": 20}}'
```

`recipe_run` returns the per-step status, result IDs, final output and the recipe's interpretation
notes. Keep `limit: 0` on intermediate analysis steps to retain all rows for later filtering; set
limits on the final step to control the returned page.


Requirements
=========

Kitconc requires Python 3.10 or later.

Core dependencies (managed by `uv`):

* numpy>=1.26.4,<2.0.0
* pandas>=2.2.0,<3.0.0
* matplotlib>=3.7.0,<4.0.0
* xlsxwriter>=3.2.3,<4.0.0
* ttkbootstrap>=1.12.0,<2.0.0
* pillow>=12.3.0,<13.0.0
* requests>=2.31.0,<3.0.0
* chardet>=5.2.0,<6.0.0
* pypdf>=4.0.0,<7.0.0
* cryptography>=50.0.0,<51.0.0
* mcp>=1.0.0,<2.0.0 *(for MCP server usage)*
* setuptools>=70.0.0

Optional `full` dependencies (embeddings, API and local environment):

* torch>=2.6,<2.14 *(CPU wheels from the configured `pytorch-cpu` uv index)*
* transformers>=4.45,<6.0.0
* sentence-transformers>=3.0,<6.0.0
* sqlite-vec>=0.1.7,<1.0.0
* fastapi>=0.110,<1.0.0
* uvicorn[standard]>=0.27,<1.0.0
* python-dotenv>=1.0.0,<2.0.0


Installation with pip
=========

```bash
pip install kitconc
pip install "kitconc[full]"   # with semantic search (torch, sentence-transformers)
```

Installation with uv
=========

```bash
uv sync
```

To install the complete local environment, including embeddings and the HTTP API:

```bash
uv sync --all-extras
```

Run commands inside the locked environment with `uv run`, for example:

```bash
uv run kitconc-mcp --transport stdio
uv run kitconc-tool workspace_info
uv run pytest
```

The desktop app continues to use the filesystem workspace format (`info.tab`, corpus indexes, and output files). Corpus creation accepts source folders whose paths contain spaces. Corpus names may contain letters, numbers, underscores, dots, and hyphens, except `.` and `..`.

ZIP imports are validated and will not replace a corpus already present in the workspace. The default maximum expanded archive size is 2 GiB (`KITCONC_MAX_IMPORT_BYTES`); URL imports are limited to 512 MiB by default (`KITCONC_MAX_DOWNLOAD_BYTES`). Export creates or atomically replaces `<corpus>.zip` in the selected destination and continues to exclude Excel result files.


Installation from GitHub
=========

1. Download Kitconc from GitHub;
2. Extract its contents;
3. Open a terminal and navigate to the extracted folder;
4. Install the locked environment with uv:

```bash
uv sync
```


Installation and usage with Docker
=========

Build the image:

```bash
docker build -t kitconc .
```

Run Kitconc MCP server over HTTP (`http://localhost:8001/mcp`) with a persisted workspace:

```bash
docker run --rm -it \
  -p 8001:8001 \
  -v "$(pwd)/kitconc_workspace:/app/kitconc_workspace" \
  kitconc
```


Kitconc App (graphical interface)
=========

After installation, launch the graphical interface with:

```bash
kitconc-app
```


Agent Layer (internal actions)
=========

Kitconc now includes an internal action layer for agent/tool orchestration:

* `kitconc.agent.actions.KitconcActions`
* Full parity with shell commands from `kit_cmd.py` (`do_*`)
* Typed schemas in `kitconc.agent.schemas`
* Contract documentation in `kitconc/agent/CONTRACT.md`
* Semantic retrieval action: `semantic_search(...)`

Basic usage:

```python
from kitconc.agent import KitconcActions

actions = KitconcActions("kitconc_workspace")
actions.create("ads", "kitconc_corpora/ads", "english")
actions.use("ads")
rows = actions.keywords(limit=10)
print(rows["rows"][:3])
```


MCP Server (for agent integrations)
=========

Kitconc ships an MCP server that lets any MCP client (Claude Code, Claude Desktop, Cursor, VS Code,
custom agents) run corpus studies on a workspace:

```bash
kitconc-mcp --transport stdio --workspace /data/kitconc_workspace
kitconc-mcp --transport streamable-http --host 127.0.0.1 --port 8001 --workspace /data/kitconc_workspace
```

Claude Code: `claude mcp add kitconc -- uv --directory /path/to/kitconc run kitconc-mcp --workspace /data/kitconc_workspace`

The server is organized as composable building blocks rather than fixed reports:

* **Primitives** — `workspace_info`, `corpus_*` (including `corpus_tagset`, `corpus_qa`,
  `subcorpus_create`), `analyze_*` (wordlist, keywords, KWIC, concordance, collocates, clusters,
  n-grams, p-frames, lemmas, dispersion), `term_candidates` (works with any POS tagset),
  `context_mine`, `text_stats`, `semantic_*`.
* **Results** — analyses store their table on the server (persisted in the workspace) and return a
  `result_id` plus one compact page. `result_filter`, `result_derive` (safe expressions with
  `per_million`, `log_likelihood`, `log_ratio`, `c_value`...), `result_join`, `result_combine`,
  `result_aggregate`, `result_enrich` (examples, definitions, dispersion, collocates per row) and
  `result_export` turn analyses into answers without moving rows through the conversation.
* **Composition** — `pipeline_run` wires tools together in one call; `recipe_*` provides editable,
  documented pipelines: corpus QA, corpus profile, word profile, near-synonyms, collocation entry,
  keyword report, corpus comparison, word frequencies across corpora, lexical bundles, glossary
  candidates (general and domain-specific).
* **Long work** — `job_start` / `job_status` / `job_cancel` run tools, pipelines or recipes in the
  background with progress and persisted status.
* **Context** — MCP resources (`kitconc://corpora`, texts, results, recipes, guides), one prompt per
  recipe plus `plan-analysis`, argument completion, and built-in guides (`guide_read`).

Useful options: `--read-only`, `--tool-set legacy` (previous one-tool-per-method catalog),
`--disk-capacity`, `--job-workers`.

The same tools run without a server through `kitconc-tool` (JSON in, JSON out), and the
`kitconc-skill` command installs the Kitconc skill for Claude and Codex (see
[Use Kitconc with AI](#use-kitconc-with-ai)).

Full documentation: [docs/MCP.md](docs/MCP.md). Python action-layer contract:
[kitconc/agent/CONTRACT.md](kitconc/agent/CONTRACT.md).


Language resources
=========

Kitconc comes with built-in language resources for Portuguese and English corpora.
It also provides functions for adding your own language resources.


What's new in 4.0.0
=========

**Agent tool surface (MCP).** `kitconc-mcp` now offers composable tools for AI agents: analyses stored on the
server, a result algebra (filter, derive, join, combine, aggregate, enrich, export), tagset-agnostic term
extraction, corpus QA and subcorpora, pipelines, editable recipes (glossaries, corpus comparison, word profiles,
collocation entries, lexical bundles...) and background jobs. See [docs/MCP.md](docs/MCP.md).

**Agent skill and CLI.** `kitconc-skill install` adds the Kitconc skill to Claude and Codex, and
`kitconc-tool` runs every agent tool from the terminal.

**Upgrading from 3.x.** MCP tool names changed (e.g. `wordlist` -> `analyze_wordlist`, `use` + `kwic` ->
`analyze_kwic(corpus=...)`). Start the server with `--tool-set legacy` to keep the old tools, or follow
"Migrating from 3.x" in [docs/MCP.md](docs/MCP.md). The Python API is unchanged.

**Fixes.** Corpus creation skips binary files in source folders, and corpus metadata (info.tab) is written and read
correctly.

Advanced corpus analyses
-------------

All new options are optional keyword arguments; existing calls return the same results as before.

```python
from kitconc.kit_corpus import Corpus
corpus = Corpus('kitconc_workspace', 'ads', 'english')

# Keywords against another corpus of the workspace, with effect sizes and a significance threshold
kw = corpus.keywords(ref_corpus='reference', effect=['log-ratio', 'log-dice'], p_value='p<0.01')
neg = corpus.keywords(ref_corpus='reference', polarity='negative')       # negative keywords
td = corpus.keywords(measure='text-dispersion', ref_corpus='reference')  # keyness of text ranges

# Collocates with any association measure plus extra measure columns
coll = corpus.collocates('new', measure='log-dice', extra_measures=['log-likelihood', 'mi3'], min_freq=2)

# KWIC: wildcards (* ? + | [a,b]), context search, random sample and KWIC pattern frequency
kwic = corpus.kwic('teach*', wildcards=True, context=['student', 'school'], context_span=(5, 5))
kwic = corpus.kwic('new', sample=50, seed=1).kpf('R1', 'R2', None)

# Clusters of any size with the search word on the left or right; p-frames ("the * of")
clusters = corpus.clusters('new', size=4, position='left')
frames = corpus.pframes(size=4, slots=1)

# Dispersion: corpus-level statistics and per-word measures
disp = corpus.dispersion('new'); print(disp.juilland_d, disp.dp, disp.stats)
dm = corpus.dispersion_measures(['new', 'skills'])
wl = corpus.wordlist(dispersion=True, stoplist='default', search='*ing')

# Lemma list, file view and word cloud
lemmas = corpus.lemmalist()                       # or lemma_file='my_lemmas.txt' (form-lemma or headword-forms)
view = corpus.fileview('ad_000.txt', 'new'); print(view.text)
corpus.wordcloud(kw, 'keywords_cloud.png')        # saved in the corpus output folder
```

New CLI commands: `pframes`, `lemmalist`, `dispersion_measures`, `fileview` and `wordcloud`; existing commands
accept new flags (see `help <command>`). Corpus creation also converts DOCX, ODT, EPUB, HTML/XHTML and XML files.
Runnable examples: `howto/19_howto_compare-keywords.py`, `howto/20_howto_advanced-kwic.py`,
`howto/21_howto_measure-dispersion.py`, `howto/22_howto_make-pframes-and-lemmas.py` and `howto/23_howto_make-wordcloud-and-fileview.py`.


What's new in 3.2.0
=========

* **Tkinter launcher command** — start GUI with `kitconc-app`
* **Agent action layer** — `kitconc.agent.actions.KitconcActions` with command parity from `kit_cmd.py`
* **Typed schemas** — available in `kitconc.agent.schemas`
* **MCP server entrypoint** — run with `kitconc-mcp`
* **Semantic search MCP tool** — `semantic_search` for sqlite-vec indexes
* **Embedding index hardening** — safer transactional writes and thread-safe SQLite access
* **Progress flag rename** — use `verbose=True` (replacing `show_progress=True`)

What's new in 3.1.0
=========

* **TF-IDF keywords** — third keyword extraction method alongside Log-Likelihood and Chi-Square
* **Keyword filters** — ignore numbers, ignore words with strange characters, set minimum word length
* **PDF support** — add PDF files directly to a corpus
* **Embeddings module** — semantic search with sentence-transformers and SQLite vector storage
* **Dialog improvements** — dialog boxes now center correctly in fullscreen and large-window mode


Usage examples
=========

Adding a corpus
-------------
```python
from kitconc.kit_corpus import Corpus
corpus = Corpus('kitconc_workspace', 'ads', 'english')
corpus.add_texts('kitconc_corpora/ads', verbose=True)
```

Creating a wordlist
-------------
```python
from kitconc.kit_corpus import Corpus
corpus = Corpus('kitconc_workspace', 'ads', 'english')
wordlist = corpus.wordlist(verbose=True)
print(wordlist.df.head(10))
wordlist.save_excel(corpus.output_path + 'wordlist.xlsx')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img01.jpg'>See results...</a>

Extracting keywords
-------------
```python
from kitconc.kit_corpus import Corpus
corpus = Corpus('kitconc_workspace', 'ads', 'english')

# Log-Likelihood (default)
keywords = corpus.keywords(verbose=True)

# Chi-Square
keywords = corpus.keywords(measure='chi-square', verbose=True)

# TF-IDF (no reference corpus needed)
keywords = corpus.keywords(measure='tf-idf', verbose=True)

# With filters
keywords = corpus.keywords(
    measure='log-likelihood',
    ignore_numbers=True,
    ignore_strange=True,
    min_chars=2,
    verbose=True,
)

print(keywords.df.head(10))
keywords.save_excel(corpus.output_path + 'keywords.xlsx')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img02.jpg'>See results...</a>

Creating concordance lines - KWIC
-------------
```python
from kitconc.kit_corpus import Corpus
corpus = Corpus('kitconc_workspace', 'ads', 'english')
kwic = corpus.kwic('experience', verbose=True)
kwic.sort('R1', 'R2', 'R3')
print(kwic.df.head(10))
kwic.save_excel(corpus.output_path + 'kwic.xlsx', highlight='R1 R2 R3')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img03.jpg'>See results...</a>

Creating concordance lines - sentences
-------------
```python
from kitconc.kit_corpus import Corpus
corpus = Corpus('kitconc_workspace', 'ads', 'english')
concordances = corpus.concordance('experience', verbose=True)
print(concordances.df.head(10))
concordances.save_excel(corpus.output_path + 'concordances.xlsx')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img04.jpg'>See results...</a>

Finding collocates
-------------
```python
from kitconc.kit_corpus import Corpus
corpus = Corpus('kitconc_workspace', 'ads', 'english')
collocates = corpus.collocates('experience', left_span=2, right_span=2,
                               coll_pos='IN NN JJ VBN VBD', verbose=True)
print(collocates.df.head(10))
collocates.save_excel(corpus.output_path + 'collocates.xlsx')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img05.jpg'>See results...</a>

Making clusters
-------------
```python
from kitconc.kit_corpus import Corpus
corpus = Corpus('kitconc_workspace', 'ads', 'english')
clusters = corpus.clusters('experience', size=3, verbose=True)
print(clusters.df.head(10))
clusters.save_excel(corpus.output_path + 'clusters.xlsx')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img06.jpg'>See results...</a>

Making ngrams
-------------
```python
from kitconc.kit_corpus import Corpus
corpus = Corpus('kitconc_workspace', 'ads', 'english')
ngrams = corpus.ngrams(size=3, pos='NN IN NN', verbose=True)
print(ngrams.df.head(10))
ngrams.save_excel(corpus.output_path + 'ngrams.xlsx')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img07.jpg'>See results...</a>

Creating dispersion plots
-------------
```python
from kitconc.kit_corpus import Corpus
corpus = Corpus('kitconc_workspace', 'ads', 'english')
dispersion = corpus.dispersion('salary')
print(dispersion.df.head(10))
dispersion.save_excel(corpus.output_path + 'dispersion.xlsx')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img08.jpg'>See results...</a>

Finding collocations
-------------
```python
from kitconc.kit_corpus import Corpus
corpus = Corpus('kitconc_workspace', 'ads', 'english')
kwic = corpus.kwic('skills', verbose=True)
collocations = corpus.collocations(kwic, verbose=True)
print(collocations.df.head(10))
collocations.save_excel(corpus.output_path + 'collocations.xlsx')
collocations.plot_colldist('strong')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img10.jpg'>See results...</a> |
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img11.jpg'>View plot...</a>

Plotting collocates
-------------
```python
from kitconc.kit_corpus import Corpus
corpus = Corpus('kitconc_workspace', 'ads', 'english')
collocates = corpus.collocates('skills', left_span=3, right_span=3,
                               coll_pos='NN JJ', verbose=True)
print(collocates.df.head(10))
collocates.save_excel(corpus.output_path + 'collocates.xlsx')
collocates.plot_collgraph(node='skills')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img12.jpg'>View plot...</a>


Development
=========

```bash
uv sync --all-extras --dev
uv run pytest
```

Tests run on every push and pull request (Ubuntu and Windows, Python 3.10 and 3.12). Agent-layer
architecture and extension points are documented in [docs/MCP.md](docs/MCP.md#extending).


License
=========

Kitconc is released under the [MIT License](LICENSE.txt).
