import os 
import numpy as np
cimport numpy as np
cimport cython
DTYPE = np.int
ctypedef np.int_t DTYPE_t
import pickle  
import re 

cdef dict load_dict(str dict_path):
    cdef dict d 
    with open(dict_path,'rb') as fh:
        d = pickle.load(fh)
    return d

cdef tuple count_words(str npy_path):
    cdef:
        dict counter
        list files 
        int total_files 
        str filename
        np.ndarray arr
        np.ndarray u 
        int x 
    counter = dict()
    files = os.listdir(npy_path)
    total_files = len(files)
    for filename in files:
        arr=np.load(npy_path + filename)
        u= np.unique(arr[:,0], return_counts=False)
        for x in range(u.shape[0]):
            if u[x] in counter:
                counter[u[x]]+=1
            else:
                counter[u[x]]=1
    return (total_files, counter)

cdef tuple count_words2(str npy_path):
    cdef:
        dict counter
        list files 
        int total_files 
        int  i 
        str filename
        np.ndarray arr
        np.ndarray u 
        int x
        tuple k  
    counter = dict()
    files = os.listdir(npy_path)
    total_files = len(files)
    i = 0 
    for filename in files:
        i+=1
        arr=np.load(npy_path + filename)
        u= np.unique(arr[:,0], return_counts=False)
        for x in range(u.shape[0]):
            k = (u[x],i) 
            if k in counter:
                counter[k]+=1
            else:
                counter[k]=1
    return (total_files, counter)

def make_wfreqinfiles(str workspace,str corpus_name, str language,bint lowercase):
    cdef:
        object punct
        dict dict_words 
        list wfreqinfiles 
        int i  
        int total_files
        dict wcount 
        dict new_wcount 
        object k 
        int v 
        float p 
        object w   
        
    # compile regex 
    punct = re.compile('^\W+$')
    # load word dictionary
    dict_words = load_dict(workspace+corpus_name+'/data/idx/words.pickle')
    # translate
    wfreqinfiles = []
    i = 0
    if lowercase == True:
        # count words in files
        total_files,wcount = count_words2(workspace+corpus_name + '/data/npy/')
        # count lowercase
        new_wcount = dict()
        for k, v in sorted(wcount.items(), key=lambda item: item[1],reverse=True):
            w = (dict_words[k[0]].lower(),k[1])
            if w not in new_wcount:
                new_wcount[w]=1 
        # sum lowercase
        wcount = dict()
        for k, v in sorted(new_wcount.items(), key=lambda item: item[1],reverse=True):
            if k[0] in wcount:
                wcount[k[0]]+=v 
            else:
                wcount[k[0]]=v
        new_wcount = None 
        # make         
        for k, v in sorted(wcount.items(), key=lambda item: item[1],reverse=True):
            if punct.match(k) == None:
                i+=1
                p = (v/float(total_files))*100
                wfreqinfiles.append((i,k,v,p))
    else:
        # count words in files
        total_files,wcount = count_words(workspace+corpus_name + '/data/npy/')
        for k, v in sorted(wcount.items(), key=lambda item: item[1],reverse=True):
            w = dict_words[k]
            if punct.match(w) == None:
                i+=1
                p = (v/float(total_files))*100
                wfreqinfiles.append((i,w,v,p))
    return wfreqinfiles
            
        
        
        
    
    