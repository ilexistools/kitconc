import os
import numpy as np
cimport numpy as np
cimport cython
DTYPE = np.int
ctypedef np.int_t DTYPE_t 
import pickle 

def get_files (str source_folder):
    cdef object filename 
    for filename in os.listdir(source_folder):
        yield filename


cdef dict load_dict(str path):
    with open(path,'rb') as fh:
        return pickle.load(fh)

def make_indexes(str workspace, str corpus_name, str language):
    cdef str source_path 
    cdef object files
    cdef dict dic_w
    cdef dict dic_t 
    cdef list d 
    cdef str line 
    cdef str k 
    cdef int v  
    source_path = workspace + corpus_name + '/data/tmp1/'
    files = get_files(source_path)
    dic_w = load_dict(workspace+corpus_name + '/data/idx/words.pickle')
    dic_t = load_dict(workspace+corpus_name + '/data/idx/tags.pickle')
    for filename in files:
        d = list()
        with open (source_path + filename,'r', encoding='utf-8') as fh:
            for line in fh:
                if len(line.strip())!= 0:
                    f = line.strip().split('\t')
                    d.append((dic_w[f[0]],dic_t[f[1]],f[2],f[3]))
        np.save(workspace + corpus_name + '/data/npy/' + filename, np.array(d,dtype=int), allow_pickle=False)
    
    dic_w = {v: k for k, v in dic_w.items()}
    with open(workspace + corpus_name + '/data/idx/words.pickle','wb') as fh:
        pickle.dump(dic_w,fh)
    
    dic_t = {v: k for k, v in dic_t.items()}
    with open(workspace + corpus_name + '/data/idx/tags.pickle','wb') as fh:
        pickle.dump(dic_t,fh)
                
        
    
    
     
