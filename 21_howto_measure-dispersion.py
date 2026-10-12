from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
# corpus-level dispersion of a search term (range, Juilland's D, Gries' DP)
dispersion = corpus.dispersion('experience')
print(dispersion.stats)
# dispersion measures for several words
measures = corpus.dispersion_measures(['experience','skills','team'])
print(measures.df)
# wordlist with RANGE, JUILLAND_D and DP columns, without stopwords
wordlist = corpus.wordlist(dispersion=True,stoplist='default')
print(wordlist.df.head(10))
measures.save_excel(corpus.output_path + 'dispersion_measures.xlsx')
