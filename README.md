Kitconc 
=========

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

The package is built on top of platforms and packages for scientific research: numpy, pandas, XlsxWriter and matplotlib. Its corpus tokenization and tagging pipeline uses built-in dependency-free components.


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

* torch>=2.6,<2.10 *(CPU wheels from the configured `pytorch-cpu` uv index)*
* transformers>=4.45,<6.0.0
* sentence-transformers>=3.0,<6.0.0
* sqlite-vec>=0.1.7,<1.0.0
* fastapi>=0.110,<1.0.0
* uvicorn[standard]>=0.27,<1.0.0
* python-dotenv>=1.0.0,<2.0.0


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

Full documentation: [docs/MCP.md](docs/MCP.md). Python action-layer contract:
[kitconc/agent/CONTRACT.md](kitconc/agent/CONTRACT.md).


Language resources
=========

Kitconc comes with built-in language resources for Portuguese and English corpora.
It also provides functions for adding your own language resources.


What's new (unreleased): AntConc-style analyses
=========

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
lemmas = corpus.lemmalist()                       # or lemma_file='my_lemmas.txt' (AntConc format accepted)
view = corpus.fileview('ad_000.txt', 'new'); print(view.text)
corpus.wordcloud(kw, 'keywords_cloud.png')        # saved in the corpus output folder
```

New CLI commands: `pframes`, `lemmalist`, `dispersion_measures`, `fileview` and `wordcloud`; existing commands
accept new flags (see `help <command>`). Corpus creation also converts DOCX, ODT, EPUB, HTML/XHTML and XML files.
Runnable examples: `19_howto_compare-keywords.py`, `20_howto_advanced-kwic.py`,
`21_howto_measure-dispersion.py`, `22_howto_make-pframes-and-lemmas.py` and `23_howto_make-wordcloud-and-fileview.py`.
A comparison with AntConc is available in `docs/ANTCONC_PESQUISA_E_COMPARACAO.md`.


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
