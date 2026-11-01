from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
# keywords against the bundled reference list, with an effect size and a significance threshold
keywords = corpus.keywords(effect=['log-ratio','log-dice'],p_value='p<0.01',verbose=True)
print(keywords.df.head(10))
# negative keywords (words unusually infrequent in the corpus)
negative = corpus.keywords(polarity='negative',min_freq=3)
print(negative.df.head(10))
# keywords against another corpus of the same workspace (e.g. corpus 'reference'):
# keywords = corpus.keywords(ref_corpus='reference',effect='log-ratio')
# keywords = corpus.keywords(measure='text-dispersion',ref_corpus='reference')
keywords.save_excel(corpus.output_path + 'keywords_effect.xlsx')
