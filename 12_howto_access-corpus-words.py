from kitconc.kit_corpus import Corpus
corpus = Corpus('kitconc_workspace','ads', 'english')
ids = list(corpus.fileids())
words_from_first_file = list(corpus.words(ids[0]))
for word in words_from_first_file:
    print(word)

# tagged words
for tagged_word in corpus.tagged_words(1):
    print(tagged_word)