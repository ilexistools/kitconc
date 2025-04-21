import os 
from kitconc.kit_corpus import Corpus
import kitconc.kit_util
import nltk 

# 1:
# First let's create a tagged corpus for demo
if not os.path.exists('kitconc_corpora/tagged_sents'):
    os.mkdir('kitconc_corpora/tagged_sents')

corpus = Corpus('kitconc_workspace','ads', 'english')
ids = list(corpus.fileids())

for file_id in ids:
    s = []
    for tagged_sent in corpus.tagged_sents():
        str_sent = ' '.join([nltk.tuple2str(token) for token in tagged_sent])
        s.append(str_sent)
    with open('kitconc_corpora/tagged_sents/file_' + str(file_id) + '.txt', 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(s))

# 2:
# Now, let's load the tagged corpus and make a wordlist
new_corpus = Corpus('kitconc_workspace', 'job_ads', 'english')
new_corpus.add_texts('kitconc_corpora/tagged_sents', tagged = True, show_progress=True)
wordlist = new_corpus.wordlist()
print(wordlist.df.head(10)) 

