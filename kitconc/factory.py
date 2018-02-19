# -*- coding: utf-8 -*-
import os
import re 
import nltk 
from collections import Counter


class Taggers(object):
    
    def __init__(self):
        self.__path = os.path.dirname(os.path.abspath(__file__))
    
    def train_bigram_tagger(self,tagged_sents, **kwargs):
        # calc training and testing sizes
        test_size = kwargs.get('test_size',25)
        show_progress = kwargs.get('show_progress',False)
        total_sents = len(tagged_sents)
        size1 = round((total_sents * test_size) / 100)
        size2 = total_sents - size1
        # get training and testing sets
        train_set = tagged_sents[:size2]
        test_set = tagged_sents[-size1:]
        tagged_sents = None
        # get the most common tag
        counter = Counter()
        for sent in train_set:
            for token in sent:
                counter[token[1]] +=1
        most_common_tag = counter.most_common(1)[0][0]
        counter = None
        # train 0
        if show_progress == True:
            print('Precision: ')
        tagger0 = nltk.DefaultTagger(most_common_tag)
        print('DefaultTagger: ',round(tagger0.evaluate(test_set),2))
        # train 1
        tagger1 = nltk.UnigramTagger(train_set, backoff=tagger0)
        if show_progress == True:
            print('UnigramTagger: ',round(tagger1.evaluate(test_set),2))
        # train 2
        tagger2 = nltk.BigramTagger(train_set, backoff=tagger1)
        if show_progress == True:
            print('BigramTagger: ',round(tagger2.evaluate(test_set),2))
        return tagger2 
       
        
    def train_trigram_tagger(self,tagged_sents, **kwargs):
        # calc training and testing sizes
        test_size = kwargs.get('test_size',25)
        show_progress = kwargs.get('show_progress',False)
        total_sents = len(tagged_sents)
        size1 = round((total_sents * test_size) / 100)
        size2 = total_sents - size1
        # get training and testing sets
        train_set = tagged_sents[:size2]
        test_set = tagged_sents[-size1:]
        tagged_sents = None
        # get the most common tag
        counter = Counter()
        for sent in train_set:
            for token in sent:
                counter[token[1]] +=1
        most_common_tag = counter.most_common(1)[0][0]
        counter = None
        # train 0
        if show_progress == True:
            print('Precision: ')
        tagger0 = nltk.DefaultTagger(most_common_tag)
        if show_progress == True:
            print('DefaultTagger: ',round(tagger0.evaluate(test_set),2))
        # train 1
        tagger1 = nltk.UnigramTagger(train_set, backoff=tagger0)
        if show_progress == True:
            print('UnigramTagger: ',round(tagger1.evaluate(test_set),2))
        # train 2
        tagger2 = nltk.TrigramTagger(train_set, backoff=tagger1)
        if show_progress == True:
            print('TrigramTagger: ',round(tagger2.evaluate(test_set),2))
        return tagger2
        

class Tokenizers(object):
    
    def __init__(self):
        self.__path = os.path.dirname(os.path.abspath(__file__)) 
     

"""
#tagged_sents = nltk.corpus.brown.tagged_sents(categories='news')
tagged_sents = nltk.corpus.brown.tagged_sents()
taggers = Taggers()
taggers.train_trigram_tagger(tagged_sents, show_progress=True)
"""


