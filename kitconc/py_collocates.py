import os 
import numpy as np 
import pickle 
import re
import math  
from kitconc.py_wordlist import make_wordlist 

def load_dict(dict_path):
    """Loads a dictionary in pickle format."""
    with open(dict_path,'rb') as fh:
        d = pickle.load(fh)
    return d 

def get_wordlist(workspace,corpus_name,language,lowercase):
    """Gets a wordlist in a dictionary. Returns a tuple with the number of tokens and the dictionary."""
    tpl = make_wordlist(workspace,corpus_name,language,lowercase)
    tokens = tpl[0]
    d = dict()
    for row in tpl[4]:
        d[row[1]] = row[2]
    return (tokens,d)

def parse_search(workspace,corpus_name,node,pos,case_sensitive,regexp,collpos):
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
    # parse collpos 
    if collpos != None:
        collp = []
        if type(collpos) == list:
            for t in collpos:
                if len(t.strip())!= 0:
                    collp.append(t.strip())
        else:
            for t in collpos.strip().split(' '):
                if len(t.strip())!=0:
                    collp.append(t.strip())
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
    # encode collpos
    if collpos != None:
        encoded_collpos = []
        for t in collp:
            if t in dict_tags:
                arr = np.array(dict_tags[t],dtype=int)
                encoded_collpos.append(arr)
            else: # if any tag has no match, return None
                encoded_collpos = None
                break 
    else:
        encoded_collpos = None
    return (encoded_node, encoded_pos, encoded_collpos)


def search_node(npy_path,encoded_node,encoded_pos,encoded_collpos,left_span,right_span):
    """Searches the node in every text file and gets contexts."""
    size = len(encoded_node)
    files = os.listdir(npy_path)
    node_count = 0
    left_arr = np.empty(0,dtype=int)
    right_arr = np.empty(0,dtype=int)
    left_counts = dict()
    right_counts = dict()
    for filename in files:
        # maker arr concatenating with arrays of zeros for preventing index out of bounds
        arr = np.concatenate([np.zeros((left_span+size,4),dtype=int),np.load(npy_path + filename),np.zeros((right_span+size,4),dtype=int)])
        # get matching indexes
        ix = arr_search_indexes(arr,encoded_node,encoded_pos)
        # get contexts from indexes
        r = get_context(arr,ix,size,encoded_collpos,left_span,right_span)
        node_count+=r[0]
        left_arr = np.concatenate((left_arr,r[1]))
        right_arr = np.concatenate((right_arr,r[2]))
    # get left counts
    i,c = np.unique(left_arr, return_counts=True)
    for x in range(i.shape[0]):
        left_counts[i[x]]=c[x]
    # get right counts
    i,c = np.unique(right_arr, return_counts=True)
    for x in range(i.shape[0]):
        right_counts[i[x]]=c[x]
    # return counts
    return (node_count,left_counts,right_counts)


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

def collpos_filter(hor_arr,encoded_collpos):
    """Filters the arr for collocation POS."""
    x = np.isin(hor_arr[:,1],encoded_collpos)
    ix = np.where(x)
    new_arr = hor_arr[ix,0]
    return new_arr.flatten()
    
def get_context(arr,indexes,size,encoded_collpos,left_span,right_span):
    """Gets the contexts from indexes."""
    neg = np.arange(left_span,0,-1)
    pos = np.arange(0,right_span,1)
    left_arr = np.empty(0,dtype=int)
    right_arr = np.empty(0,dtype=int)
    node_count = 0
    if encoded_collpos != None:
        for i in indexes:
            node_count+=1
            # left horizon
            l = arr[i-neg,0:2]
            l = collpos_filter(l, encoded_collpos)
            left_arr = np.concatenate((left_arr,l))          
            # right horizon
            r = arr[(i+size)+pos,0:2]
            r = collpos_filter(r,encoded_collpos) 
            right_arr = np.concatenate((right_arr,r))
    else:
        for i in indexes:
            node_count+=1
            l = arr[i-neg,0]         # left horizon
            r = arr[(i+size)+pos,0]  # right horizon
            right_arr = np.concatenate((right_arr,r.flatten()))
            left_arr = np.concatenate((left_arr,l.flatten()))
    return (node_count,left_arr,right_arr) 


def mutual_information(ab,a,b,N, h=1):
    """Calculates mutual information."""
    O = ab / float(N)
    E = (a / float(N)) * (b / float(N))
    E =  E * h
    OE = O/E
    I = math.log(OE,2)
    I = round(I,2)
    return I 

def tscore(ab,a,b,N, h=1):
    """Calculates t-score."""
    O = ab / float(N)
    E = (a / float(N)) * (b / float(N))
    E =  E * h
    T = (O-E) / (math.sqrt(ab)/float(N))
    T = round(T,2)
    return T


def calc_association(node_count,left_counts,right_counts,dict_words,wordlist,tokens,lowercase,measure):
    """Translates numbers to words and calculates association. Returns a list of collocates."""
    punct = re.compile('^\W+$')
    collocates = []
    d = dict()
    if lowercase == True:
        # translate lowercase
        tmp = dict()
        for k, v in left_counts.items():
            if k != 0:
                w = dict_words[k].lower()
                if w in tmp:
                    tmp[w]+=v 
                else:
                    tmp[w]=v
        left_counts = tmp 
        tmp = dict()
        for k, v in right_counts.items():
            if k != 0:
                w = dict_words[k].lower()
                if w in tmp:
                    tmp[w]+=v 
                else:
                    tmp[w]=v
        right_counts = tmp 
        tmp = None
        # join left and right
        for w, v in left_counts.items():
            d[w]=[v,0]
        left_counts = None
        for w, v in right_counts.items():
            if w in d:
                vv = d[w]
                d[w]=[vv[0],v]
            else:
                d[w]=[0,v]
        right_counts = None
        dict_words = None
    else:
        # translate and join (case sensitive)
        for k, v in left_counts.items():
            w = dict_words[k]
            d[w]=[v,0]
        left_counts = None
        for k, v in right_counts.items():
            w = dict_words[k]
            if w in d:
                vv = d[w]
                d[w]=[vv[0],v]
            else:
                d[w]=[0,v]
        right_counts = None
        dict_words = None
    # calc association
    s = []
    if measure == 1:
        i = 0 
        for k,v in d.items():
            if punct.match(k) == None:
                i+=1
                b = 0
                if k in wordlist:
                    b = wordlist[k]
                m = tscore(v[0]+v[1],node_count,b,tokens,1)
                s.append("%s\t%s\t%s\t%s\t%s" % (k,v[0]+v[1],node_count,b,tokens) )
                collocates.append((i,k,v[0]+v[1],v[0],v[1],m)) 
    else:
        i = 0 
        for k,v in d.items():
            if punct.match(w) == None:
                i+=1
                b = 0
                if k in wordlist:
                    b = wordlist[k]
                m = mutual_information(v[0]+v[1],node_count,b,tokens,1)
                collocates.append((i,k,v[0]+v[1],v[0],v[1],m))
    return collocates 
        
    
def make_collocates(workspace,corpus_name,node,pos,case_sensitive,regexp,collpos,lowercase,left_span,right_span,measure):
    encoded_node,encoded_pos,encoded_collpos = parse_search(workspace,corpus_name,node,pos,case_sensitive,regexp,collpos)
    if encoded_node != None: # search node is OK
        node_count, left_counts, right_counts = search_node(workspace+corpus_name + '/data/npy/',encoded_node,encoded_pos,encoded_collpos,left_span,right_span)
        if node_count!=0:
            dict_words = load_dict(workspace+corpus_name + '/data/idx/words.pickle')
            language=None
            tokens,wordlist = get_wordlist(workspace,corpus_name,language,lowercase)
            collocates = calc_association(node_count,left_counts,right_counts,dict_words,wordlist,tokens,lowercase,measure)
        else:
            collocates=[]
    else: # no match in search node, set empty
        collocates = []
    return collocates
    
    
    
    