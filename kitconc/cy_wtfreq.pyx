import os 
import numpy as np
cimport numpy as np
cimport cython
DTYPE = np.int
ctypedef np.int_t DTYPE_t
import pickle  

cdef dict load_dict(str dict_path):
    cdef dict d 
    with open(dict_path,'rb') as fh:
        d = pickle.load(fh)
    return d


cdef tuple count_wt(str npy_path):
    cdef:
        int tokens = 0
        dict counter 
        list files 
        str filename 
        np.ndarray arr
        np.ndarray u
        np.ndarray c
        int x
        tuple k  
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

def make_wtfreq(str workspace, str corpus_name,str language,bint lowercase):
    cdef:
        int tokens 
        dict wt_count 
        dict dict_words
        dict dict_tags 
        list wtfreq 
        dict new_wt_count
        tuple new_k 
        tuple k 
        int v 
        int i 
        float p 
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
