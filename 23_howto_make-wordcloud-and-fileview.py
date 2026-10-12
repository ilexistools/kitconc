from kitconc.kit_corpus import Corpus 
corpus = Corpus('kitconc_workspace','ads','english')
# word cloud of the wordlist (without stopwords) saved in the output folder
corpus.wordcloud(filename='wordcloud.png')
# word cloud of the keywords
corpus.wordcloud(corpus.keywords(polarity='positive'),'keywords_cloud.png',colormap='plasma')
# text of one file with the hits of a search term marked
view = corpus.fileview('ad_000.txt','experience')
print(view.hits, view.tokens)
print(view.text)
