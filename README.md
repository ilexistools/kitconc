
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

Kitconc requires a Python 3.6 (or later) instalation along with:

* NLTK
* pandas
* XlsxWrite
* sckit-learn

It is suggested that users install Anaconda Platform as an easy option. 

Installation
=========
(Make sure you have Python 3.6 (or later) and the required packages.)

1. Download kitconc from GitHub;
2. Extract its contents;
3. Open a terminal and navigate to the 'kitconc-master' folder;
4. Use the following command:
```bash
python setup.py install
```

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
# * 'workspace' is the folder path to store the corpus data
# * 'job_ads' is the corpus name
corpus = Corpus('workspace','job_ads', language='english',encoding='utf-8')

# add texts
# * 'JOB_ADS' is the folder path for the raw corpus (.txt files)  
corpus.add_texts('JOB_ADS',show_progress=True)
```

Creating a wordlist 
-------------
```python
from kitconc.corpus import Corpus

# reference to corpus 
corpus = Corpus('workspace','job_ads', language='english',encoding='utf-8')

# make wordlist 
wordlist = corpus.wordlist()

# print the top 25 most frequent words
print(wordlist.df.head(25))

# save in Excel
wordlist.save_xls(corpus.output_path + 'wordlist.xlsx')
```

Extracting keywords 
-------------
```python
from kitconc.corpus import Corpus

# reference to corpus 
corpus = Corpus('workspace','job_ads', language='english',encoding='utf-8')

# make wordlist
wordlist = corpus.wordlist()

# make keywords (Log-likelihood is the default measure)
keywords = corpus.keywords(wordlist)

# for chi-square measure, use:
# keywords = corpus.keywords(wordlist, measure = corpus.CHI_SQUARE)

# print the top 25 keywords
print(keywords.df.head(25))

# save in Excel
keywords.save_xls(corpus.output_path + 'keywords.xlsx') 
```

Creating concordance lines 
-------------
```python
from kitconc.corpus import Corpus

# reference to corpus 
corpus = Corpus('workspace','job_ads', language='english',encoding='utf-8')

# make concordance lines 
kwic = corpus.kwic('experience')

# print 10 lines of concordances
print(kwic.df.head(10))

# save in Excel
kwic.save_xls(corpus.output_path + 'kwic_experience.xlsx')
```

Finding collocates 
-------------
```python
from kitconc.corpus import Corpus

# reference to corpus 
corpus = Corpus('workspace','job_ads', language='english',encoding='utf-8')

# find wordlist 
wordlist = corpus.wordlist()

# make collocates (t-score is the default measure)
collocates = corpus.collocates(wordlist, 'experience',coll_pos='NN JJ', left_span = 3, right_span=3)

#for mutual information, use:
#collocates = corpus.collocates(wordlist, 'experience',coll_pos='NN JJ', left_span = 3, right_span=3,
#measure=corpus.MUTUAL_INFORMATION)

# print top 25 collocates
print(collocates.df.head(25))

# save in Excel
collocates.save_xls(corpus.output_path + 'collocates_experience.xlsx')
```

