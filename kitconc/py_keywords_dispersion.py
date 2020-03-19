import os 
import numpy as np 
import pickle 


def load_dict(dict_path):
    """Loads a dictionary in pickle format."""
    with open(dict_path,'rb') as fh:
        d = pickle.load(fh)
    return d 

def keywords2numbers(workspace,corpus_name,keywords,lowercase):
    # load dictionaries for encoding words to numbers
    if lowercase == True:
        dict_words = load_dict(workspace+corpus_name+'/data/idx/wordslc.pickle') # lowercase
    else:
        dict_words = load_dict(workspace+corpus_name+'/data/idx/words.pickle')
        dict_words = {v: k for k, v in dict_words.items()}
    # new keywords dict
    encoded_keywords = dict()
    for w,keyness in keywords.items():
        k = tuple(dict_words[w])
        encoded_keywords[k] = (w,keyness)
    return encoded_keywords 
        
def search_node(npy_path,encoded_keywords,encoded_pos):
    """Searches the node in every text file and gets positions."""
    files = os.listdir(npy_path)
    data = []
    dict_positions = dict()
    # get positions
    for filename in files:
        # load arr 
        arr = np.load(npy_path + filename)
        # get matching indexes
        for k,v in encoded_keywords.items(): # k = encoded_word - v = (word,keyness)
            ix = arr_search_indexes(arr,k,encoded_pos)
            positions = []
            for i in ix.tolist():
                p = round((i / arr.shape[0])*100,2)
                positions.append(p)
            if k in dict_positions:
                dict_positions[k]+=positions
            else:
                dict_positions[k]=positions
    # make data
    for k,v in encoded_keywords.items():
        data.append( (v[0],len(dict_positions[k]),dict_positions[k],v[1])) 
    return data


def arr_search_indexes(arr,search_w,search_t):
    """Searches the node in arr and returns the matching indexes. (Max. 3 words)"""
    ix = np.isin(arr[:,[0]],search_w)
    ix = np.where(ix)[0]
    return ix 


def translate(positions):
    """Translate numbers back to words in a list format for kitconc KIWC object."""
    dispersion = []
    dpts = dict()
    i = 0
    total_s1 = 0
    total_s2 = 0
    total_s3 = 0
    total_s4 = 0
    total_s5 = 0
    
    for d in positions:
        i+=1
        s1 = 0
        s2 = 0 
        s3 = 0
        s4 = 0
        s5 = 0
        dpts[d[0]] = d[2]
        for point in d[2]:
            p = round(point)
            if p >= 0 and p <= 19:
                s1+=1
            elif p >= 20 and p <= 39:
                s2+=1
            elif p >= 40 and p <= 59:
                s3+=1
            elif p >= 60 and p <= 79:
                s4+=1
            elif p >= 80 and p <= 100:
                s5+=1
        total_s1 += s1
        total_s2 += s2
        total_s3 += s3
        total_s4 += s4
        total_s5 += s5
        dispersion.append((i ,d[0],d[3],d[1],s1,s2,s3,s4,s5))
    return ((total_s1,total_s2,total_s3,total_s4,total_s5),dpts,dispersion)
        
    
def make_keywords_dispersion(workspace,corpus_name,keywords,lowercase):
    dispersion=[]
    dpts = dict()
    totals = tuple()
    encoded_keywords = keywords2numbers(workspace, corpus_name, keywords, lowercase)
    if encoded_keywords != None: # search node is OK
        positions = search_node(workspace+corpus_name + '/data/npy/',encoded_keywords,None)
        if len(positions)!=0:
            totals,dpts,dispersion = translate(positions)
    return (totals,dpts,dispersion)
    
    
    
    