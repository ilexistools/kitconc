# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
import os 
import pickle
import numpy as np
import re  


def load_dict(dict_path):
    with open(dict_path,'rb') as fh:
        d = pickle.load(fh)
    return d 

def save_dict(dict_d,dict_path):
    with open(dict_path,'wb') as fh:
        pickle.dump(dict_d,fh)

def count_words(npy_path):
    counter = dict()
    files = os.listdir(npy_path)
    for filename in files:
        arr=np.load(npy_path + filename)
        i,c = np.unique(arr[:,0], return_counts=True)
        for x in range(i.shape[0]):
            if i[x] in counter:
                counter[i[x]]+=c[x]
            else:
                counter[i[x]]=c[x]
    return counter
    
def make_wordlist(workspace,corpus_name,language,lowercase=True):
    # check wordlist saved 
    if os.path.exists(workspace + corpus_name + '/data/idx/wordlistlc.pickle') == True and lowercase == True:
        with open(workspace + corpus_name + '/data/idx/wordlistlc.pickle','rb') as fh:
            wordlist = pickle.load(fh)
        info = list()
        with open(workspace + corpus_name + '/data/idx/info.pickle','rb') as fh:
            info = pickle.load(fh)
        return (info[0],info[1],info[2],info[3],wordlist)  
    
    # compile regex 
    punct = re.compile('^\W+$')
    
    # make or load wordlist count
    if (os.path.exists(workspace+corpus_name+'/data/idx/wordlist.pickle') == False):
        word_count = count_words(workspace+corpus_name + '/data/npy/')
        save_dict(word_count,workspace+corpus_name+'/data/idx/wordlist.pickle')
    else:
        word_count = load_dict(workspace+corpus_name+'/data/idx/wordlist.pickle')
    
    # load words dictionary
    dict_words = load_dict(workspace+corpus_name+'/data/idx/words.pickle')
    
    # lowercase
    if lowercase == True:
        new_word_count = dict()
        tokens = 0
        for k, v in sorted(word_count.items(), key=lambda item: item[1],reverse=True):
            tokens+=v
            s = dict_words[k].lower()
            if s in new_word_count:
                new_word_count[s]+=v 
            else:
                new_word_count[s]=v
        word_count = None
        dict_words = None
        types = len(new_word_count)
        total = float(tokens)
        wordlist = list()
        n= 0
        hapax = 0
        for s, v in sorted(new_word_count.items(), key=lambda item: item[1],reverse=True):
            if punct.match(s) == None:
                n+=1
                p = (v/total)*100  
                wordlist.append((n,s,v,p))
                if v == 1:
                    hapax+=1
    else:
        for k, v in sorted(word_count.items(), key=lambda item: item[1],reverse=True):
            tokens+=v
        total = float(tokens)
        types = len(word_count)
        wordlist = list()
        for k, v in sorted(word_count.items(), key=lambda item: item[1],reverse=True):
            s = dict_words[k]
            if punct.match(s) == None:
                n+=1
                p = (v/total)*100  
                wordlist.append((n,s,v,p))
                if v == 1:
                    hapax+=1
        word_count = None
        dict_words = None
    type_token = (types/float(tokens))*100
    
    if os.path.exists(workspace + corpus_name + '/data/idx/wordlistlc.pickle') == False and lowercase == True:
        with open(workspace + corpus_name + '/data/idx/wordlistlc.pickle','wb') as fh:
            pickle.dump(wordlist,fh)
        info = [tokens,types,type_token,hapax]
        with open(workspace + corpus_name + '/data/idx/info.pickle','wb') as fh:
            pickle.dump(info,fh)
        with open(workspace + corpus_name + '/info.tab','a',encoding='utf-8') as fh:
            fh.write('\nTokens:\t%s\nTypes:\t%s\nType/token:\t%s' % (tokens,types,type_token))
    return (tokens,types,type_token,hapax,wordlist)  
    
    
