from kitconc.kit_corpus import Corpus
corpus = Corpus('kitconc_workspace','ads', 'english')
sents = list(corpus.sents(1)) # sents from first file
for sent in sents:
    print(sent)

# tagged sents
for sent in corpus.tagged_sents(1):
    print(sent)
