# -*- coding: utf-8 -*-
from kitconc.kit_corpus import Corpus



corpora = ['ads','bulas','fiction','noticias','jobs','horoscopo']

corpus_name = corpora[0]
corpus = Corpus('d:/kitconc',corpus_name,language='portuguese',encoding='utf-8')

i = 17     
if i == 1:
    wordlist = corpus.wordlist(show_progress=True)
    wordlist.save_excel(corpus.output_path + '/wordlist.xlsx')
if i == 2:
    wtfreq = corpus.wtfreq(show_progress=True)
    wtfreq.save_excel(corpus.output_path + '/wtfreq.xlsx')
if i == 3:
    wfreqinfiles = corpus.wfreqinfiles(show_progress=True)
    wfreqinfiles.save_excel(corpus.output_path + '/wfreqinfiles.xlsx')
if i == 4:
    wordlist = corpus.wordlist(show_progress=True)
    keywords = corpus.keywords(wordlist,stoplist=['ou','este','voc�','seu','ser'],show_progress=True)
    keywords.save_excel(corpus.output_path + '/keywords.xlsx')
if i == 5:
    kwic = corpus.kwic('pesquisa',horizon=5,show_progress=True)
    kwic.sort('R1','R2','R3')
    kwic.save_excel(corpus.output_path + '/kwic.xlsx', highlight=kwic.HIGHLIGHT_L1 + kwic.HIGHLIGHT_R3)
if i == 6:
    conc = corpus.concordance('pesquisa',show_progress=True)
    conc.save_excel(corpus.output_path + '/concordance.xlsx')
if i == 7:
    coll = corpus.collocates('doen�a',left_span=1,right_span=1, coll_pos='ADJ',show_progress=True)
    coll.save_excel(corpus.output_path + '/collocates.xlsx')
if i == 8:
    coll1 = corpus.collocates('mulher',left_span=0,right_span=1, coll_pos='ADJ')
    coll2 = corpus.collocates('homem',left_span=0,right_span=1, coll_pos='ADJ')
    compared = corpus.compared_collocates(coll1, coll2,show_progress=True)
    compared.save_excel(corpus.output_path + '/compared.xlsx')
if i == 9:
    kwic = corpus.kwic('medicamento')
    coll = corpus.collocations(kwic,show_progress=True)
    coll.save_excel(corpus.output_path + '/collocations.xlsx')
if i == 10:
    clusters = corpus.clusters('vida',size=5,min_freq=2, show_progress=True)
    clusters.save_excel(corpus.output_path + '/clusters.xlsx')
if i == 11:
    ngrams = corpus.ngrams(size=3,show_progress=True)
    ngrams.save_excel(corpus.output_path + '/ngrams.xlsx')
if i == 12:
    dispersion = corpus.dispersion('dose',show_progress=True)
    dispersion.save_excel(corpus.output_path + '/dispersion.xlsx')
if i == 13:
    wordlist = corpus.wordlist(show_progress=True)
    keywords = corpus.keywords(wordlist,show_progress=True)
    keywords_dispersion = corpus.keywords_dispersion(keywords,limit=25,show_progress=True)
    keywords_dispersion.save_excel(corpus.output_path + '/keywords_dispersion.xlsx')
if i == 14:
    kwic = corpus.kwic('medicamento')
    coll = corpus.collocations(kwic,show_progress=True)
    coll.plot_colldist('usar', title='Distribuição de *usar*',  show_values=True)

if i == 15:
    node_word = 'dose'
    coll = corpus.collocates(node_word,left_span=1,right_span=1, coll_pos='ADJ', show_progress=True)
    coll.save_excel(corpus.output_path + '/collocates.xlsx')
    coll.plot_collgraph()

if i == 16:
    for word in corpus.tagged_words_get():
        print(corpus.words_count())
        input('')


    
    
    

print('\nDone!')




