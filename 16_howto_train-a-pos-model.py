import os 
from kitconc.kit_corpus import Corpus
import kitconc.kit_util

# first let's create a tagged corpus for demo
if not os.path.exists('kitconc_corpora/tagged_sents'):
    os.mkdir('kitconc_corpora/tagged_sents')

corpus = Corpus('kitconc_workspace','ads', 'english')
ids = list(corpus.fileids())

for file_id in ids:
    s = []
    for tagged_sent in corpus.tagged_sents():
        str_sent = ' '.join([f'{token[0]}/{token[1]}' for token in tagged_sent])
        s.append(str_sent)
    with open('kitconc_corpora/tagged_sents/file_' + str(file_id) + '.txt', 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(s))

# now let's train the model

from kitconc.kit_models import Models

models = Models()
models.create_model('kitconc_corpora/tagged_sents', 'english-ads', verbose=True)

# Remove the model
#models.remove_model('english-ads')


    
    




