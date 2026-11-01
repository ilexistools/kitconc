from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
clusters = corpus.clusters('experience',size=3,verbose=True)
print(clusters.df.head(10))
clusters.save_excel(corpus.output_path + 'clusters.xlsx')