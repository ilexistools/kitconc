from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
collocates = corpus.collocates('experience',left_span=2,right_span=2,coll_pos='IN NN JJ VBN VBD',show_progress=True)
print(collocates.df.head(10))
collocates.save_excel(corpus.output_path + 'collocates.xlsx')