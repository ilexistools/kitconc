from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
keywords = corpus.keywords(show_progress=True)
print(keywords.df.head(10))
keywords.save_excel(corpus.output_path + 'keywords.xlsx')