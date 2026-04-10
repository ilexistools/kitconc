Kitconc 
=========

Kitconc is a package for Corpus Linguistics and text analysis with Python.
It contains, among other things, tools for creating:

* Corpora
* Frequency wordlists
* Keywords (Log-Likelihood, Chi-Square, TF-IDF)
* Concordance lines (KWIC and sentence-based)
* Collocates
* N-gram lists
* Dispersion plots
* Excel data files
* Semantic search with sentence embeddings

The package is built on top of platforms and packages for scientific research: numpy, pandas, NLTK, XlsxWriter and matplotlib.


Requirements
=========

Kitconc requires Python 3.10 or later.

Package dependencies (`pip install kitconc`):

* numpy>=1.26.4,<2.0.0
* pandas>=2.2.0,<3.0.0
* matplotlib>=3.7.0,<4.0.0
* xlsxwriter>=3.2.3,<4.0.0
* ttkbootstrap>=1.12.0,<2.0.0
* pillow>=11.2.0,<12.0.0
* requests>=2.31.0,<3.0.0
* nltk>=3.9.1,<4.0.0
* chardet>=5.2.0,<6.0.0
* pypdf>=4.0.0,<7.0.0
* cryptography>=3.1,<47.0.0
* mcp>=1.0.0,<2.0.0 *(for MCP server usage)*
* setuptools>=70.0.0

Additional dependencies listed in `requirements.txt` (full local environment):

* torch>=2.6,<2.10 *(CPU wheels via `--extra-index-url https://download.pytorch.org/whl/cpu`)*
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
```


Installation from GitHub
=========

1. Download Kitconc from GitHub;
2. Extract its contents;
3. Open a terminal and navigate to the extracted folder;
4. Install with pip:

```bash
pip install .
```

Or using a virtual environment (recommended):

**macOS / Linux**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
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

An MCP server entrypoint is available:

```bash
kitconc-mcp --transport stdio
```

For HTTP clients (recommended, simpler setup):

```bash
kitconc-mcp --transport streamable-http --host 127.0.0.1 --port 8001
```

or (legacy SSE transport):

```bash
kitconc-mcp --transport sse --host 127.0.0.1 --port 8001
```

Notes:

* Tools are auto-generated from `KitconcActions.mcp_tool_catalog()`.
* Includes semantic retrieval tool: `semantic_search` (`query`, `top_k`, `db_path`, `model_name`).
* `mcp` runtime is included in package dependencies (`pip install kitconc` is enough).


MCP Tool Reference (complete)
=========

Kitconc MCP tools are auto-exposed from public methods in `kitconc.agent.actions.KitconcActions`.
The current catalog includes operational tools, utility helpers, and typed wrappers.

Recommended operational tools
-------------

These are the tools most clients should use in normal workflows:

* `workspace(path=None)` - get/set current workspace
* `workspace_status()` - inspect current workspace and selected corpus
* `ls(corpus_name=None)` - list corpora or output files
* `list_corpora()` - list corpus metadata in workspace
* `use(corpus_name)` - select corpus for subsequent commands
* `home()` - clear selected corpus
* `create(name, source, language, tagged=False, verbose=False)` - create corpus from folder
* `delete(corpus_name)` - remove corpus
* `cleanse(corpus_name=None)` - delete output files from a corpus
* `open(filename, corpus_name=None, launch=False)` - resolve generated output file path
* `wordlist(corpus_name=None, lowercase=True, limit=None)` - compute word frequency list
* `keywords(...)` - compute keywords (`log-likelihood`, `chi-square`, `tf-idf`)
* `kwic(node, ...)` - keyword in context
* `concordance(node, ...)` - sentence-style concordance
* `collocates(node, ...)` - collocate statistics
* `collgraph(node, ..., plot=False)` - collocates formatted for graph workflows
* `wtfreq(corpus_name=None, lowercase=True, limit=None)` - word-tag frequency
* `wfreqinfiles(corpus_name=None, lowercase=True, limit=None)` - per-file frequencies
* `clusters(word, ...)` - lexical clusters around a node
* `ngrams(corpus_name=None, ...)` - n-gram extraction
* `dispersion(node, ...)` - dispersion by corpus sections
* `keywords_dispersion(corpus_name=None, ...)` - dispersion for top keywords
* `semantic_search(query, top_k=5, db_path=None, model_name=None)` - vector semantic retrieval
* `text2utf8(source, target=None, source_encoding='mbcs', verbose=False)` - normalize corpus text encoding
* `train_model(source, language=None, reflist=None, stoplist=None, verbose=False)` - train language model resources
* `export_corpus(dest_path, corpus_name=None)` - export corpus as zip
* `import_corpus(filename)` - import exported corpus zip
* `examples(dest_path=None)` - download example corpora
* `version()` / `app_version()` - package version
* `help(command=None)` / `command_help(command=None)` - command help text

Utility methods also exposed by MCP
-------------

These are usually for orchestration and diagnostics:

* `set_workspace(workspace)`
* `save_workspace_file(filename='kitconc.tmp')`
* `from_workspace_file(filename='kitconc.tmp')`
* `list_commands()`
* `list_output_files(corpus_name=None)`
* `list_ref_languages()`
* `corpus_exists(corpus_name)`
* `get_corpus_info(corpus_name)`
* `create_corpus(corpus_name, language, source_folder, tagged=False, verbose=False)`
* `delete_corpus(corpus_name)`

Typed wrappers (migration layer)
-------------

These wrappers accept schema objects and return typed payloads:

* `workspace_typed(request)`
* `create_typed(request)`
* `keywords_typed(request)`
* `kwic_typed(request)`
* `collgraph_typed(request)`
* `dispersion_typed(request)`
* `keywords_dispersion_typed(request)`
* `text2utf8_typed(request)`
* `train_model_typed(request)`
* `semantic_search_typed(request)`

Quick prompt suggestions
-------------

Use prompts like these with your MCP client/agent:

* "Set workspace to `/data/kitconc_workspace`, list corpora, and summarize what is available."
* "Create corpus `ads_en` from `/data/corpora/ads` in English, then select it."
* "Run `wordlist` and `keywords` (log-likelihood, limit 30), then compare top terms."
* "Generate KWIC for `experience` with horizon 7 and show 20 rows."
* "Find collocates for `experience` with `left_span=3`, `right_span=3`, and rank by MI."
* "Run `ngrams` with `size=3` and `minfreq=3`; return top 50."
* "Run `dispersion` for `experience` and explain section totals."
* "Export current corpus to `/data/exports` and return the zip path."
* "Import corpus from `/data/exports/ads_en.zip`, select it, and verify metadata."
* "Run semantic search for `customer loyalty` with top_k 10 using default DB path."

Suggested MCP usage flows
-------------

Flow 1: New corpus to first insights
1. `workspace(path)`
2. `create(name, source, language)`
3. `use(corpus_name)`
4. `wordlist(...)`
5. `keywords(...)`
6. `kwic(node, ...)`

Flow 2: Comparative lexical exploration
1. `use(corpus_name)`
2. `keywords(...)`
3. `collocates(node, ...)`
4. `clusters(word, ...)`
5. `ngrams(...)`
6. `export_corpus(dest_path)`

Flow 3: File hygiene and publishing outputs
1. `ls()`
2. `list_output_files(corpus_name)`
3. `open(filename, launch=False)`
4. `cleanse(corpus_name)` (only when safe to remove files)

Flow 4: Semantic retrieval workflow
1. `use(corpus_name)`
2. (Build or provide embedding DB externally)
3. `semantic_search(query, top_k, db_path)`
4. Combine semantic hits with `kwic`/`concordance` for qualitative inspection

Flow 5: Portability and replication
1. `export_corpus(dest_path, corpus_name)`
2. transfer zip file
3. `import_corpus(filename)`
4. `get_corpus_info(corpus_name)`

Safety notes
-------------

* `delete`, `delete_corpus`, and `cleanse` are destructive and execute immediately.
* `open(..., launch=False)` is safer for server-side environments.
* `collgraph(..., plot=True)` may require a GUI-capable environment; use `plot=False` on headless servers.


Language resources
=========

Kitconc comes with built-in language resources for Portuguese and English corpora.
It also provides functions for adding your own language resources.


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
