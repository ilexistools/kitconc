from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
# wildcards: * (any characters), ? (one character), + (zero or one character), a|b, [a,b]
kwic = corpus.kwic('develop*',wildcards=True,verbose=True)
print(kwic.df.head(10))
# context search: lines of 'experience' with 'years' up to 3 words to the left or right
kwic = corpus.kwic('experience',context=['years'],context_span=(3,3))
print(len(kwic.df))
# random sample and KWIC pattern frequency (most frequent R1 R2 patterns first)
kwic = corpus.kwic('experience',sample=30,seed=1).kpf('R1','R2',None)
print(kwic.df[['NODE','RIGHT','PATTERN','KPF']].head(10))
kwic.save_excel(corpus.output_path + 'kwic_kpf.xlsx')
