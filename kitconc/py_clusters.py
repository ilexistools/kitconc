import os 
import numpy as np 
import pickle 
import re 

def load_dict(dict_path):
    """Loads a dictionary in pickle format."""
    with open(dict_path,'rb') as fh:
        d = pickle.load(fh)
    return d 

def parse_search(workspace,corpus_name,node,pos,lowercase):
    """Parses the input search and returns a tuple with encoded word and pos node.
    """
    # load dictionaries for encoding words to numbers
    if lowercase == False:
        dict_words = load_dict(workspace+corpus_name+'/data/idx/wordslc.pickle') # lowercase
    else:
        dict_words = load_dict(workspace+corpus_name+'/data/idx/words.pickle')
        dict_words = {v: k for k, v in dict_words.items()}
    dict_tags = load_dict(workspace+corpus_name+'/data/idx/tags.pickle')
    dict_tags = {v: k for k, v in dict_tags.items()}
    # parse node
    n = []
    if lowercase == False:
        node = node.lower()
    for w in node.strip().split(' '):
        if len(w.strip()) != 0:
            n.append(w.strip())
            break # allow 1 word only
    # parse pos 
    if pos != None:
        p = []
        if type(pos) == list:
            for t in pos:
                if len(t.strip())!= 0:
                    p.append(t.strip())
                    break # allow 1 tag only
        else:
            for t in pos.strip().split(' '):
                if len(t.strip())!=0:
                    p.append(t.strip())
                    break # allow 1 tag only
    # encode node
    encoded_node = []
    for w in n:
        if w in dict_words:
            arr = np.array(dict_words[w],dtype=int)
            encoded_node.append(arr)
        else: # if any word has no match, return None
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


def search_node(npy_path,encoded_node,encoded_pos,size):
    """Searches the node in every text file and gets contexts."""
    files = os.listdir(npy_path)
    contexts = []
    for filename in files:
        # maker arr concatenating with arrays of zeros for preventing index out of bounds
        arr = np.concatenate([np.zeros((size+size,4),dtype=int),np.load(npy_path + filename),np.zeros((size+size,4),dtype=int)])
        # get matching indexes
        ix = arr_search_indexes(arr,encoded_node,encoded_pos)
        # get contexts from indexes
        contexts += get_context(arr,ix,size)
    return contexts 


def arr_search_indexes(arr,search_w,search_t):
    """Searches the node in arr and returns the matching indexes. (Max. 3 words)"""
    size = len(search_w)
    if search_t == None:
        # search only words
        if size == 1:
            ix = np.isin(arr[:,[0]],search_w)
            ix = np.where(ix)[0]
    else:
        # search words and POS
        if size == 1:
            iw = np.isin(arr[:,[0]],search_w)
            it = np.isin(arr[:,[1]],search_t)
            ix = np.where(iw & it)[0]
    return ix 

def get_context(arr,indexes,size):
    """Gets the contexts from indexes."""
    d = dict()
    if size == 1:
        for i in indexes:
            l = (arr[i,0])
            if l in d:
                d[l]+=1
            else:
                d[l]=1
    elif size == 2:
        for i in indexes:
            l = (arr[i-1,0],arr[i,0])
            if l in d:
                d[l]+=1
            else:
                d[l]=1
            l = (arr[i,0],arr[i+1,0])
            if l in d:
                d[l]+=1
            else:
                d[l]=1
    elif size == 3:
        for i in indexes:
            l = (arr[i-2,0],arr[i-1,0],arr[i,0])
            if l in d:
                d[l]+=1
            else:
                d[l]=1
            l = (arr[i-1,0],arr[i,0],arr[i+1,0])
            if l in d:
                d[l]+=1
            else:
                d[l]=1
            l = (arr[i,0],arr[i+1,0],arr[i+2,0])
            if l in d:
                d[l]+=1
            else:
                d[l]=1
    return [d] 
        

def translate(contexts,dict_words,lowercase,total_files,size):
    """Translate numbers back to words in a list format for kitconc KIWC object."""
    clusters = []
    r = dict()
    c = dict() 
    n = dict()
    punct = re.compile('^\W+ | \W+$| \W+ ')
    for d in contexts:
        n=dict()
        for k,v in d.items():
            # translate clusters
            if size == 1:
                if k !=0:
                    if lowercase == True:
                        w = dict_words[k].lower()
                    else:
                        w = dict_words[k]
            else:
                if 0 not in k:
                    if lowercase == True:
                        w = ' '.join([dict_words[i].lower() for i in k])
                    else:
                        w = ' '.join([dict_words[i] for i in k])
            # add translated to new dict
            if len(punct.findall(w)) == 0:
                if w in n:
                    n[w]+=v
                else:
                    n[w]=v
        # count range and append counts
        for w,v in n.items():
            if w in r:
                r[w]+=1
            else:
                r[w]=1
            if w in c:
                c[w]+=v 
            else:
                c[w]=v
    
    contexts = None
    # make clusters
    i = 0 
    for w,v in c.items():
        i+=1
        p = (r[w]/float(total_files))*100
        clusters.append((i,w,v,r[w],p))
    return clusters 
    
def make_clusters(workspace,corpus_name,node,pos,lowercase,size):
    encoded_node,encoded_pos = parse_search(workspace,corpus_name,node,pos,lowercase)
    if encoded_node != None: # search node is OK
        contexts = search_node(workspace+corpus_name + '/data/npy/',encoded_node,encoded_pos,size)
        if len(contexts)!=0:
            total_files = len(os.listdir(workspace+corpus_name + '/data/npy/'))
            dict_words = load_dict(workspace+corpus_name+'/data/idx/words.pickle')
            clusters = translate(contexts,dict_words,lowercase,total_files,size)
        else:
            clusters=[]
    else: # no match in search node, set empty
        clusters = []
    return clusters 
    
    
    
    