Kitconc 4.0.1
=============

Kitconc is a package for Corpus Linguistics and text analysis with Python.
It contains, among other things, tools for creating:

* Corpora;
* Frequency wordlists;
* Keywords (Log-Likelihood, Chi-Square, TF-IDF);
* Concordance lines;
* Collocates;
* N-gram lists;
* Dispersion plots;
* Excel data files;
* Semantic search with sentence embeddings.

The package is built on top of platforms and packages for scientific research:
numpy, pandas, XlsxWriter and matplotlib. Corpus tokenization and tagging use built-in dependency-free components.

Requirements
============

Kitconc requires Python 3.10 or later.

Core dependencies (managed by uv):

numpy>=1.26.4,<2.0.0
pandas>=2.2.0,<3.0.0
matplotlib>=3.7.0,<4.0.0
xlsxwriter>=3.2.3,<4.0.0
ttkbootstrap>=1.12.0,<2.0.0
pillow>=12.3.0,<13.0.0
requests>=2.31.0,<3.0.0
chardet>=5.2.0,<6.0.0
pypdf>=4.0.0,<7.0.0
cryptography>=50.0.0,<51.0.0
mcp>=1.0.0,<2.0.0
setuptools>=70.0.0

Optional full dependencies (embeddings, API and local environment):

torch>=2.6,<2.10 (CPU wheels from the configured pytorch-cpu uv index)
transformers>=4.45,<6.0.0
sentence-transformers>=3.0,<6.0.0
sqlite-vec>=0.1.7,<1.0.0
fastapi>=0.110,<1.0.0
uvicorn[standard]>=0.27,<1.0.0
python-dotenv>=1.0.0,<2.0.0

Installation with uv
====================

uv sync

For the complete local environment:

uv sync --all-extras

Run commands with uv run, for example:

uv run kitconc-mcp --transport stdio
uv run pytest

Kitconc App (graphical interface)
=================================

kitconc-app

The desktop app continues to use the filesystem workspace format (info.tab, corpus indexes, and output files). Corpus creation accepts source folders whose paths contain spaces. Corpus names may contain letters, numbers, underscores, dots, and hyphens, except . and ..

ZIP imports are validated and will not replace a corpus already present in the workspace. The default maximum expanded archive size is 2 GiB (KITCONC_MAX_IMPORT_BYTES); URL imports are limited to 512 MiB by default (KITCONC_MAX_DOWNLOAD_BYTES). Export creates or atomically replaces <corpus>.zip in the selected destination and continues to exclude Excel result files.

Agent Layer (internal actions)
==============================

Kitconc now includes an internal action layer for agent/tool orchestration:

* kitconc.agent.actions.KitconcActions
* Full parity with shell commands from kit_cmd.py (do_*)
* Typed schemas in kitconc.agent.schemas
* Contract documentation in kitconc/agent/CONTRACT.md
* Semantic retrieval action: semantic_search(...)

Basic usage:

from kitconc.agent import KitconcActions
actions = KitconcActions("kitconc_workspace")
actions.create("ads", "kitconc_corpora/ads", "english")
actions.use("ads")
rows = actions.keywords(limit=10)

MCP Server (for agent integrations)
===================================

kitconc-mcp --transport stdio

For HTTP clients (recommended):

kitconc-mcp --transport streamable-http --host 127.0.0.1 --port 8001

or (legacy SSE):

kitconc-mcp --transport sse --host 127.0.0.1 --port 8001

Semantic MCP tools::

    semantic_index_status (corpus_name, db_path)
    index_corpus (corpus_name, source_folder, db_path, model_name, chunk_size,
                  chunk_overlap, batch_size, rebuild)
    semantic_search (query, top_k, db_path, model_name, corpus_name)
    export_analysis_result (analysis_result, output_path, sheet_name)

Use index_corpus to create a per-corpus semantic index from TXT, Markdown,
RST, and PDF files in the source folder recorded in info.tab. Set source_folder
when that original path is unavailable. The index is stored under
<workspace>/.semantic_indexes/<corpus>.sqlite3. Existing indexes are retained
unless rebuild=True is requested. Then call semantic_search, optionally after
selecting the corpus with actions.use("name").

Install optional embedding dependencies with:
uv sync --extra full

To save an analysis result, pass its complete response object to
export_analysis_result and set output_path to a filename ending in .tab,
.tsv, or .xlsx. Only the response's rows are written; metadata such as total
is not exported. TAB and TSV files are UTF-8 tab-delimited; XLSX accepts an
optional sheet_name (1-31 characters; invalid characters: ``[]:*?/\\``). Files are written
atomically and replace an existing destination only after a successful
export. Parent directories are created when needed. The result reports the
resolved output_path, format, rows_written, and columns_written.

Example: pass the complete result from wordlist(corpus_name="ads") as
analysis_result, with output_path="C:/exports/wordlist.xlsx" and
sheet_name="Wordlist".

MCP runtime is included in package dependencies
(uv sync is enough).

Agent skills for Claude and Codex
=================================

Install the bundled Kitconc skills without a global pip installation (requires uv):

    uvx --from kitconc kitconc-skill install

This installs the general corpus-analysis skill and the kitconc-recipe-author skill. The latter
guides an assistant to design a reusable recipe from a user's goal, validate the pipeline, run it
when useful, and save it to the active Kitconc workspace. To update an existing installation, add
--force. See the GitHub README for examples and the complete recipe-authoring guide.

What's new in 3.2.0
====================

* Tkinter launcher command -- start GUI with kitconc-app
* Agent action layer -- kitconc.agent.actions.KitconcActions with command parity from kit_cmd.py
* Typed schemas -- available in kitconc.agent.schemas
* MCP server entrypoint -- run with kitconc-mcp
* Semantic search MCP tool -- semantic_search for sqlite-vec indexes
* MCP tools to build per-corpus embedding indexes and inspect index status
* Embedding index hardening -- transactional writes and thread-safe SQLite access
* Progress flag rename -- use verbose=True (replacing show_progress=True)

What's new in 3.1.0
====================

* TF-IDF keywords -- third keyword extraction method alongside Log-Likelihood and Chi-Square
* Keyword filters -- ignore numbers, ignore words with strange characters, minimum word length
* PDF support -- add PDF files directly to a corpus
* Embeddings module -- semantic search with sentence-transformers and SQLite vector storage
* Dialog improvements -- dialog boxes now center correctly in fullscreen and large-window mode

Language resources
==================

Kitconc comes with built-in language resources for Portuguese and English corpora.
It also provides functions for adding your own language resources.

Usage example
=============

See how easy it is to use Kitconc:

`https://ilexis.net.br/kitconc <https://ilexis.net.br/kitconc>`_
