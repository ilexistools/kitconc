from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
# clusters of any size with the search word on the left (or position='right')
clusters = corpus.clusters('experience',size=4,position='left')
print(clusters.df.head(10))
# p-frames: n-grams with open slots, e.g. "the * of"
pframes = corpus.pframes(size=3,slots=[2],verbose=True)
print(pframes.df.head(10))
# lemma list (bundled English list or lemma_file='my_lemmas.txt' in headword-forms format)
lemmas = corpus.lemmalist()
print(lemmas.df.head(10))
pframes.save_excel(corpus.output_path + 'pframes.xlsx')
lemmas.save_excel(corpus.output_path + 'lemmas.xlsx')
