from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
dispersion = corpus.dispersion('salary')
print(dispersion.df.head(10))
dispersion.save_excel(corpus.output_path + 'dispersion.xlsx')