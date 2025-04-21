from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
kwic = corpus.kwic('skills',show_progress=True)
collocations = corpus.collocations(kwic,show_progress=True)
print(collocations.df.head(10))
collocations.save_excel(corpus.output_path+'collocations.xlsx')
# plot a collocate distribution
collocations.plot_colldist('strong')