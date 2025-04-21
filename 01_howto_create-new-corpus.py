from kitconc.kit_corpus import Corpus 
# reference to the corpus
corpus = Corpus('kitconc_workspace','ads','english')
# add texts from source folder
corpus.add_texts('kitconc_corpora/ads',show_progress=True)
