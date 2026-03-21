Kitconc 3.1.0
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

Kitconc requires Python 3.10 or later, along with:

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


Kitconc App (graphical interface)
=========

After installation, launch the graphical interface with:

```bash
python app.py
```


Language resources
=========

Kitconc comes with built-in language resources for Portuguese and English corpora.
It also provides functions for adding your own language resources.


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
corpus.add_texts('kitconc_corpora/ads', show_progress=True)
```

Creating a wordlist
-------------
```python
from kitconc.kit_corpus import Corpus
corpus = Corpus('kitconc_workspace', 'ads', 'english')
wordlist = corpus.wordlist(show_progress=True)
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
keywords = corpus.keywords(show_progress=True)

# Chi-Square
keywords = corpus.keywords(measure='chi-square', show_progress=True)

# TF-IDF (no reference corpus needed)
keywords = corpus.keywords(measure='tf-idf', show_progress=True)

# With filters
keywords = corpus.keywords(
    measure='log-likelihood',
    ignore_numbers=True,
    ignore_strange=True,
    min_chars=2,
    show_progress=True,
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
kwic = corpus.kwic('experience', show_progress=True)
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
concordances = corpus.concordance('experience', show_progress=True)
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
                               coll_pos='IN NN JJ VBN VBD', show_progress=True)
print(collocates.df.head(10))
collocates.save_excel(corpus.output_path + 'collocates.xlsx')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img05.jpg'>See results...</a>

Making clusters
-------------
```python
from kitconc.kit_corpus import Corpus
corpus = Corpus('kitconc_workspace', 'ads', 'english')
clusters = corpus.clusters('experience', size=3, show_progress=True)
print(clusters.df.head(10))
clusters.save_excel(corpus.output_path + 'clusters.xlsx')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img06.jpg'>See results...</a>

Making ngrams
-------------
```python
from kitconc.kit_corpus import Corpus
corpus = Corpus('kitconc_workspace', 'ads', 'english')
ngrams = corpus.ngrams(size=3, pos='NN IN NN', show_progress=True)
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
kwic = corpus.kwic('skills', show_progress=True)
collocations = corpus.collocations(kwic, show_progress=True)
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
                               coll_pos='NN JJ', show_progress=True)
print(collocates.df.head(10))
collocates.save_excel(corpus.output_path + 'collocates.xlsx')
collocates.plot_collgraph(node='skills')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img12.jpg'>View plot...</a>
