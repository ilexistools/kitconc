from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
corpus.export('kitconc_corpora', show_progress=True)