Kitconc 3.0.5
=========

Kitconc is a package for Corpus Linguistics and text analysis with Python. 
It contains, among other things, tools for creating:

* Corpora
* Frequency wordlists
* Keywords
* Concordance lines
* Collocates 
* N-gram lists
* Dispersion plots
* Excel data files 

The package is built on top of platforms and packages for scientific research: numpy, pandas, NLTK,  XlsxWrite and matplotlib. 


Requirements
=========

Kitconc requires a Python 3.10.15 (or later) installation along with:

* numpy>=1.24.0,<2.0.0
* pandas>=2.2.0,<3.0.0
* matplotlib>=3.7.0,<4.0.0
* xlsxwriter>=3.2.3,<4.0.0
* ttkbootstrap>=1.12.0,<2.0.0
* pillow>=11.2.0,<12.0.0
* requests>=2.31.0,<3.0.0
* nltk>=3.9.1,<4.0.0
* chardet>=5.2.0,<6.0.0

It is suggested that users install Anaconda Platform as an easy option. 

Installation with pip
=========
(Make sure you have Python 3.10.15 (or later) and the required packages.)

Use the following command:
```bash
pip install kitconc
```

Installation from GitHub
=========
(Make sure you have Python 3.10.15 (or later) and the required packages.)

1. Download Kitconc from GitHub;
2. Extract its contents;
3. Open a terminal and navigate to the 'kitconc-master' folder;
4. Use the following command:
```bash
python setup.py install
```

Installation from GitHub using venv
=========
(Make sure you have Python 3.10.15 (or later) and the required packages.)

1. Download Kitconc from GitHub;
2. Extract its contents;
3. Open a terminal and navigate to the 'kitconc-master' folder;
4. Use the following command for MacOS:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
5. Use the following command for Windows:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Kitconc App (graphical interface)
=========
After installation, use the following command:
```bash
python app.py
```

Language resources
=========

Kitconc comes with some basic language resources for portuguese and english corpora.
It also has functions for adding your own language resources.

Usage example
=========

Adding a corpus
-------------
```python
from kitconc.kit_corpus import Corpus 
# reference to the corpus
corpus = Corpus('kitconc_workspace','ads','english')
# add texts from source folder
corpus.add_texts('kitconc_corpora/ads',show_progress=True)
```

Creating a wordlist 
-------------
```python
from kitconc.kit_corpus import Corpus 
# reference to the corpus
corpus = Corpus('kitconc_workspace','ads','english')
# make wordlist
wordlist = corpus.wordlist(show_progress=True)
# print the top 10 
print(wordlist.df.head(10))
# save Excel file
wordlist.save_excel(corpus.output_path + 'wordlist.xlsx') 
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img01.jpg'>See results...</a>

Extracting keywords 
-------------
```python
from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
keywords = corpus.keywords(show_progress=True)
print(keywords.df.head(10))
keywords.save_excel(corpus.output_path + 'keywords.xlsx')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img02.jpg'>See results...</a>

Creating concordance lines - KWIC 
-------------
```python
from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
kwic = corpus.kwic('experience',show_progress=True)
kwic.sort('R1','R2','R3')
print(kwic.df.head(10))
kwic.save_excel(corpus.output_path + 'kwic.xlsx',highlight='R1 R2 R3')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img03.jpg'>See results...</a>

Creating concordance lines - sentences 
-------------
```python
from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
concordances = corpus.concordance('experience',show_progress=True)
print(concordances.df.head(10))
concordances.save_excel(corpus.output_path + 'concordances.xlsx')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img04.jpg'>See results...</a>

Finding collocates 
-------------
```python
from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
collocates = corpus.collocates('experience',left_span=2,right_span=2,coll_pos='IN NN JJ VBN VBD',show_progress=True)
print(collocates.df.head(10))
collocates.save_excel(corpus.output_path + 'collocates.xlsx')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img05.jpg'>See results...</a>

Making clusters 
-------------
```python
from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
clusters = corpus.clusters('experience',size=3,show_progress=True)
print(clusters.df.head(10))
clusters.save_excel(corpus.output_path + 'clusters.xlsx')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img06.jpg'>See results...</a>

Making ngrams 
-------------
```python
from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
ngrams = corpus.ngrams(size=3,pos='NN IN NN',show_progress=True)
print(ngrams.df.head(10))
ngrams.save_excel(corpus.output_path + 'ngrams.xlsx')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img07.jpg'>See results...</a>

Creating dispersion plots 
-------------
```python
from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
dispersion = corpus.dispersion('salary')
print(dispersion.df.head(10))
dispersion.save_excel(corpus.output_path + 'dispersion.xlsx')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img08.jpg'>See results...</a>

Finding collocations
-------------
```python
from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
kwic = corpus.kwic('skills',show_progress=True)
collocations = corpus.collocations(kwic,show_progress=True)
print(collocations.df.head(10))
collocations.save_excel(corpus.output_path+'collocations.xlsx')
# plot a collocate distribution
collocations.plot_colldist('strong')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img10.jpg'>See results...</a> | 
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img11.jpg'>View plot...</a>

Ploting collocates
-------------
```python
from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
collocates = corpus.collocates('skills',left_span=3,right_span=3,coll_pos='NN JJ',show_progress=True)
print(collocates.df.head(10))
collocates.save_excel(corpus.output_path + 'collocates.xlsx')
# plot collocates
collocates.plot_collgraph(node='skills')
```
<a href='https://raw.githubusercontent.com/ilexistools/kitconc-examples/master/images/img12.jpg'>View plot...</a>