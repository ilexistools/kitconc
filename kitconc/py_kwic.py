import os 
import numpy as np 
import pickle 
import re 

def load_dict(dict_path):
    """Loads a dictionary in pickle format."""
    with open(dict_path,'rb') as fh:
        d = pickle.load(fh)
    return d 

def parse_search(workspace,corpus_name,node,pos,case_sensitive,regexp):
    """Parses the input search and returns a tuple with encoded word and pos node.
    """
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


def search_node(npy_path,encoded_node,encoded_pos,horizon):
    """Searches the node in every text file and gets contexts."""
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


def arr_search_indexes(arr,search_w,search_t):
    """Searches the node in arr and returns the matching indexes. (Max. 3 words)"""
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

def get_context(arr,indexes,horizon,size):
    """Gets the contexts from indexes."""
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

def translate(contexts,dict_words,dict_files):
    """Translate numbers back to words in a list format for kitconc KIWC object."""
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
        
    
def make_kwic(workspace,corpus_name,node,pos,case_sensitive,regexp,horizon):
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
    
    
    
    