from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
ngrams = corpus.ngrams(size=3,pos='NN IN NN',show_progress=True)
print(ngrams.df.head(10))
ngrams.save_excel(corpus.output_path + 'ngrams.xlsx')