
Kitconc
===========

Kitconc is a package for Corpus Linguistics and text analysis with Python. 
It contains, among other things, tools for creating:

* Corpora
* Frequency wordlists
* Keywords
* Concordance lines
* Collocates tables
* N-gram lists
* Excel data files and plots

The package is built on top of platforms and packages for scientific research: NLTK, pandas, XlsxWrite and sckit-learn. 
All in Anaconda Platform.

Requirements
=========

Kitconc requires a Python 3.6.0 instalation along with:

* NLTK
* pandas
* XlsxWrite
* sckit-learn

It is suggested that users install Anaconda Platform as an easy option. 

Installation
=========
(Make sure you have Python 3.6.0 and the required packages.)

1. Download kitconc from GitHub;
2. Extract its contents;
3. Open a terminal and navigate to the 'kitconc-master' folder;
4. Use the following command:
```bash
python setup.py install
```
5. That's it!

Language resources
=========

Kitconc comes with some language resources for portuguese and english corpora.
It also has functions for adding your own language resources.

Usage example
=========

See how easy it is to use Kitconc:


Adding a corpus
-------------
```python
from kitconc.corpus import Corpus 

# create a corpus 
corpus = Corpus('workspace','job_ads', language='english',encoding='utf-8')

# add texts 
corpus.add_texts('JOB_ADS',show_progress=True)
```

Creating a wordlist 
-------------
```python
from kitconc.corpus import Corpus

# access to corpus 
corpus = Corpus('workspace','job_ads', language='english',encoding='utf-8')

# make wordlist 
wordlist = corpus.wordlist()

# print the top 25 most frequent words
print(wordlist.df.head(25))

# save in Excel
wordlist.save_xls(corpus.output_path + 'wordlist.xlsx')
```

Creating and saving keywords in Excel
-------------
```python
from kitconc.corpus import Corpus
corpus = Corpus('c:/kitconc','horoscopo','portuguese','latin-1')
wordlist = corpus.wordlist()
keywords = corpus.keywords(wordlist)
keywords.save_xls('c:/kitconc/keywords.xlsx')
```

Creating and saving concordance lines in Excel
-------------
```python
from kitconc.corpus import Corpus
corpus = Corpus('c:/kitconc','horoscopo','portuguese','latin-1')
concordance = corpus.kwic('vida')
concordance.sort('R1','R2',None)
concordance.save_xls('c:/kitconc/kwic.xlsx',50,['R1','R2'])
```


http://ilexis.net.br/kitconc5
 `<http://ilexis.net.br/kitconc5>`.
