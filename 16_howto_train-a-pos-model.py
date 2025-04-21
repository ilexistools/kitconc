import os 
from kitconc.kit_corpus import Corpus
import kitconc.kit_util
import nltk 

# first let's create a tagged corpus for demo
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

# now let's train the model

from kitconc.kit_models import Models

models = Models()
models.nltk_create_model('kitconc_corpora/tagged_sents', 'english-ads', show_progress=True)

# Remove the model
#models.remove_model('english-ads')


    
    




