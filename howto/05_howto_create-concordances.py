from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
concordances = corpus.concordance('experience',verbose=True)
print(concordances.df.head(10))
concordances.save_excel(corpus.output_path + 'concordances.xlsx')