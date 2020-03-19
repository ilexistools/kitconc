import os 
import numpy as np
import pickle  

def load_dict(dict_path):
    with open(dict_path,'rb') as fh:
        d = pickle.load(fh)
    return d

def count_wt(npy_path):
    tokens = 0
    counter = dict()
    files = os.listdir(npy_path)
    for filename in files:
        arr= np.load(npy_path + filename)[:,0:2]
        u,c = np.unique(arr, axis=0, return_counts=True)
        for x in range(u.shape[0]):
            k = (u[x][0],u[x][1])
            if k in counter:
                counter[k]+=c[x]
            else:
                counter[k]=c[x]
            tokens+=c[x]
    return (tokens,counter) 

def make_wtfreq(workspace,corpus_name,language,lowercase=True):
    # count wtfreq 
    tokens,wt_count = count_wt(workspace+corpus_name + '/data/npy/')
    # load word and tag dictionaries 
    dict_words = load_dict(workspace+corpus_name+'/data/idx/words.pickle')
    dict_tags = load_dict(workspace+corpus_name+'/data/idx/tags.pickle')
    # translate
    wtfreq = []
    i=0
    if lowercase == True:
        new_wt_count = dict()
        for k, v in sorted(wt_count.items(), key=lambda item: item[1],reverse=True):
            new_k = (dict_words[k[0]].lower(),dict_tags[k[1]])
            if new_k in new_wt_count:
                new_wt_count[new_k]+= v 
            else:
                new_wt_count[new_k]= v
        wt_count = None
        for k, v in sorted(new_wt_count.items(), key=lambda item: item[1],reverse=True):
            i+=1
            p = (v/float(tokens))*100
            wtfreq.append((i,k[0],k[1],v,p))
    else:
        for k, v in sorted(wt_count.items(), key=lambda item: item[1],reverse=True):
            i+=1
            p = (v/float(tokens))*100
            wtfreq.append((i,dict_words[k[0]],dict_tags[k[1]],v,p))
    return wtfreq 
