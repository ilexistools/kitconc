import os 
import numpy as np
cimport numpy as np
cimport cython
DTYPE = np.int
ctypedef np.int_t DTYPE_t
import pickle 
import re 

cdef dict load_dict(str dict_path):
    cdef:
        dict d  
    with open(dict_path,'rb') as fh:
        d = dict(pickle.load(fh))
    return d 

cdef tuple parse_search(str workspace,str corpus_name,str node,object pos, object case_sensitive,object regexp):
    """Parses the input search and returns a tuple with encoded word and pos node.
    """
    cdef:
        dict dict_words
        dict dict_tags
        object k 
        object v 
        list n 
        str w 
        list p 
        str t 
        object encoded_node
        object encoded_pos
        list patterns 
        object ptrn
        np.ndarray arr
        list a
         
    # load dictionaries for encoding words to numbers
    if case_sensitive == False:
        dict_words = load_dict(workspace+corpus_name+'/data/idx/wordslc.pickle') # lowercase
    else:
        dict_words = load_dict(workspace+corpus_name+'/data/idx/words.pickle')
        dict_words = {v: k for k, v in dict_words.items()}
    dict_tags = load_dict(workspace+corpus_name+'/data/idx/tags.pickle')
    dict_tags = {v: k for k, v in dict_tags.items()}
    # parse node
    n = []
    if case_sensitive == False:
        node = node.lower()
    for w in node.strip().split(' '):
        if len(w.strip()) != 0:
            n.append(w.strip())
    # parse pos 
    if pos != None:
        p = []
        if type(pos) == list:
            for t in pos:
                if len(t.strip())!= 0:
                    p.append(t.strip())
        else:
            for t in pos.strip().split(' '):
                if len(t.strip())!=0:
                    p.append(t.strip())
    # encode node
    encoded_node = []
    if regexp == False:
        for w in n:
            if w in dict_words:
                arr = np.array(dict_words[w],dtype=int)
                encoded_node.append(arr)
            else: # if any word has no match, return None
                encoded_node = None
                break
    else: # use regexp:
        patterns = []
        for ptrn in n:
            patterns.append(re.compile(ptrn))
        for ptrn in patterns:
            a = []
            for k in dict_words:
                if ptrn.match(k) != None:
                    a+=dict_words[k]
            if len(a)!=0:
                arr = np.array(a,dtype=int)
                encoded_node.append(arr)
            else: # if any pattern has no match, return None
                encoded_node = None
                break 
    # encode pos
    if pos != None:
        encoded_pos = []
        for t in p:
            if t in dict_tags:
                arr = np.array(dict_tags[t],dtype=int)
                encoded_pos.append(arr)
            else: # if any tag has no match, return None
                encoded_pos = None
                break 
    else:
        encoded_pos = None
    return (encoded_node, encoded_pos)


cdef list search_node(str npy_path,object encoded_node,object encoded_pos,int horizon):
    """Searches the node in every text file and gets contexts."""
    cdef:
        int size 
        list files 
        list contexts 
        str filename
        np.ndarray arr
        np.ndarray ix 
    size = len(encoded_node)
    files = os.listdir(npy_path)
    contexts = []
    for filename in files:
        # maker arr concatenating with arrays of zeros for preventing index out of bounds
        arr = np.concatenate([np.zeros((horizon+size,4),dtype=int),np.load(npy_path + filename),np.zeros((horizon+size,4),dtype=int)])
        # get matching indexes
        ix = arr_search_indexes(arr,encoded_node,encoded_pos)
        # get contexts from indexes
        contexts += get_context(arr,ix,horizon,size)
    return contexts 


cdef np.ndarray arr_search_indexes(np.ndarray arr,object search_w,object search_t):
    """Searches the node in arr and returns the matching indexes. (Max. 3 words)"""
    cdef:
        int size
        np.ndarray ix 
        np.ndarray iw
        np.ndarray it 
        np.ndarray x1 
        np.ndarray x2 
        np.ndarray x3 
        np.ndarray t1
        np.ndarray t2
        np.ndarray t3
        np.ndarray x 
        np.ndarray y 
        np.ndarray z 
    size = len(search_w)
    if search_t == None:
        # search only words
        if size == 1:
            ix = np.isin(arr[:,[0]],search_w)
            ix = np.where(ix)[0]
        elif size == 2:
            # w1
            x1 = np.isin(arr[:,[0]],search_w[0])
            if np.any(x1)==False:
                return np.where(x1)[0]
            # w2 
            x2 = np.isin(arr[:,[0]],search_w[1])
            if np.any(x2)==False:
                return np.where(x2)[0]
            # match indexes
            x = np.arange(0,x1.shape[0]-1)
            y = np.arange(1,x1.shape[0])
            # return indexes
            ix = np.where(x1[x] & x2[y])[0]
            return ix 
        elif size == 3:
            # w1
            x1 = np.isin(arr[:,[0]],search_w[0])
            if np.any(x1)==False:
                return np.where(x1)[0]
            # w2
            x2 = np.isin(arr[:,[0]],search_w[1])
            if np.any(x2)==False:
                return np.where(x2)[0]
            # w3
            x3 = np.isin(arr[:,[0]],search_w[2])
            if np.any(x3)==False:
                return np.where(x3)[0]
            # match indexes
            x = np.arange(0,x1.shape[0]-2)
            y = np.arange(1,x1.shape[0]-1)
            z = np.arange(2,x1.shape[0])
            # return indexes
            ix = np.where(x1[x] & x2[y] & x3[z])[0]
    else:
        # search words and POS
        if size == 1:
            iw = np.isin(arr[:,[0]],search_w)
            it = np.isin(arr[:,[1]],search_t)
            ix = np.where(iw & it)[0]
        elif size == 2:
            # w1 t1
            x1 = np.isin(arr[:,[0]],search_w[0])
            t1 = np.isin(arr[:,[1]],search_t[0])
            if np.any(x1)==False:
                return np.where(x1)[0]
            if np.any(t1)==False:
                return np.where(t1)[0]
            # w2 t2 
            x2 = np.isin(arr[:,[0]],search_w[1])
            t2 = np.isin(arr[:,[1]],search_t[1])
            if np.any(x2)==False:
                return np.where(x2)[0]
            if np.any(t2)==False:
                return np.where(t2)[0]
            # match indexes
            x = np.arange(0,x1.shape[0]-1)
            y = np.arange(1,x1.shape[0])
            # return indexes 
            ix = np.where(x1[x] & t1[x] & x2[y] & t2[y])[0]
        elif size == 3:
            # w1 t1
            x1 = np.isin(arr[:,[0]],search_w[0])
            t1 = np.isin(arr[:,[1]],search_t[0])
            if np.any(x1)==False:
                return np.where(x1)[0]
            if np.any(t1)==False:
                return np.where(t1)[0]
            # w2 t2
            x2 = np.isin(arr[:,[0]],search_w[1])
            t2 = np.isin(arr[:,[1]],search_t[1])
            if np.any(x2)==False:
                return np.where(x2)[0]
            if np.any(t2)==False:
                return np.where(t2)[0]
            # w3 t3
            x3 = np.isin(arr[:,[0]],search_w[2])
            t3 = np.isin(arr[:,[1]],search_t[2])
            if np.any(x3)==False:
                return np.where(x3)[0]
            if np.any(t3)==False:
                return np.where(t3)[0]
            # match indexes
            x = np.arange(0,x1.shape[0]-2)
            y = np.arange(1,x1.shape[0]-1)
            z = np.arange(2,x1.shape[0])
            # return indexes
            ix = np.where(x1[x] & t1[x] & x2[y] & t2[y] & x3[z] & t3[z])[0]
    return ix 

cdef list get_context(np.ndarray arr,np.ndarray indexes,int horizon,int size):
    """Gets the contexts from indexes."""
    cdef:
        np.ndarray neg 
        np.ndarray pos 
        np.ndarray nsize 
        list contexts 
        int i 
        np.ndarray l 
        np.ndarray n 
        np.ndarray r 
        int t 
        int s 
        int f  
    neg = np.arange(horizon,0,-1)
    pos = np.arange(0,horizon,1)
    nsize = np.arange(0,size)
    contexts=[]
    for i in indexes:
        l = arr[i-neg,0]         # left horizon
        n = arr[i+nsize,0]       # node
        r = arr[(i+size)+pos,0]  # right horizon
        t = i                    # token id
        s = arr[i,2]             # sentence id
        f = arr[i,3]             # file id
        contexts.append((l,n,r,t,s,f))
    return contexts 

cdef list translate(list contexts,dict dict_words,dict dict_files):
    """Translate numbers back to words in a list format for kitconc KIWC object."""
    cdef:
        dict files
        list kwic
        object context 
        int i 
        list l 
        list n 
        list r   
    dict_files = {v: k for k, v in dict_files.items()} # reverse keys
    kwic = []
    i = 0
    for context in contexts:
        i+=1
        l = []
        n = []
        r = []
        # left
        for i in context[0]:
            if i != 0:
                l.append(dict_words[i])
        # node
        for i in context[1]:
            if i != 0:
                n.append(dict_words[i])
        # right
        for i in context[2]:
            if i != 0:
                r.append(dict_words[i])
        # add to list
        kwic.append((i, ' '.join(l), ' '.join(n),' '.join(r), dict_files[context[5]][0],str(context[3]),str(context[4]),str(context[5])))
    return kwic
        
    
def make_kwic(str workspace,str corpus_name, str node,object pos, object case_sensitive,object regexp,int horizon):
    cdef:
        object encoded_node
        object encoded_pos 
        int nl 
        list contexts 
        dict dict_words 
        dict dict_files 
        list kwic 
    encoded_node,encoded_pos = parse_search(workspace,corpus_name,node,pos,case_sensitive,regexp)
    if encoded_node != None: # search node is OK
        nl = len(encoded_node)
        contexts = search_node(workspace+corpus_name + '/data/npy/',encoded_node,encoded_pos,horizon)
        if len(contexts)!=0:
            dict_words = load_dict(workspace+corpus_name + '/data/idx/words.pickle')
            dict_files = load_dict(workspace+corpus_name + '/data/idx/filenames.pickle')
            kwic = translate(contexts,dict_words,dict_files)
        else:
            kwic=[]
    else: # no match in search node, set empty
        nl = 0
        kwic = []
    return (nl,kwic) 
    
    
    
    