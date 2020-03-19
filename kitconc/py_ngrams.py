import os 
import numpy as np 
import pickle 
import re 
import collections 
import tempfile 
import shutil 


def load_dict(dict_path):
    """Loads a dictionary in pickle format."""
    with open(dict_path,'rb') as fh:
        d = pickle.load(fh)
    return d 

def parse_search(workspace,corpus_name,pos):
    """Parses the input search and returns a tuple with encoded word and pos node.
    """
    # load dictionaries for encoding words to numbers
    dict_tags = load_dict(workspace+corpus_name+'/data/idx/tags.pickle')
    dict_tags = {v: k for k, v in dict_tags.items()}
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
    return encoded_pos


def unigrams(arr,encoded_pos):
    if encoded_pos != None:
        dq = collections.deque(maxlen=1)
        counter = collections.Counter()
        for i in range(0,arr.shape[0]):
            if int(arr[i][1]) in encoded_pos:
                dq.append(int(arr[i][0]))
                counter[dq[0]]+=1 
    else:
        dq = collections.deque(maxlen=1)
        counter = collections.Counter()
        for i in range(0,arr.shape[0]):
            dq.append(int(arr[i]))
            counter[dq[0]]+=1
    return counter
    
def bigrams(arr,encoded_pos):
    if encoded_pos != None:
        dq = collections.deque(maxlen=2)
        dqt = collections.deque(maxlen=2)
        dq.append(int(arr[0][0]))
        dqt.append(int(arr[0][1]))
        counter = collections.Counter()
        for i in range(1,arr.shape[0]):
            dq.append(int(arr[i][0]))
            dqt.append(int(arr[i][1]))
            if dqt[0] in encoded_pos[0] and dqt[1] in encoded_pos[1]:
                counter[(dq[0],dq[1])]+=1
    else:
        dq = collections.deque(maxlen=2)
        dq.append(int(arr[0]))
        counter = collections.Counter()
        for i in range(1,arr.shape[0]):
            dq.append(int(arr[i]))
            counter[(dq[0],dq[1])]+=1
    return counter 

def trigrams(arr,encoded_pos):
    if encoded_pos != None:
        dq = collections.deque(maxlen=3)
        dqt = collections.deque(maxlen=3)
        dq.append(int(arr[0][0]))
        dq.append(int(arr[1][0]))
        dqt.append(int(arr[0][1]))
        dqt.append(int(arr[1][1]))
        counter = collections.Counter()
        for i in range(2,arr.shape[0]):
            dq.append(int(arr[i][0]))
            dqt.append(int(arr[i][1]))
            if dqt[0] in encoded_pos[0] and dqt[1] in encoded_pos[1] and dqt[2] in encoded_pos[2]:
                counter[(dq[0],dq[1],dq[2])]+=1
    else:
        dq = collections.deque(maxlen=3)
        dq.append(int(arr[0]))
        dq.append(int(arr[1]))
        counter = collections.Counter()
        for i in range(2,arr.shape[0]):
            dq.append(int(arr[i]))
            counter[(dq[0],dq[1],dq[2])]+=1
        
    return counter

def quadrigrams(arr,encoded_pos):
    if encoded_pos != None:
        dq = collections.deque(maxlen=4)
        dqt = collections.deque(maxlen=4)
        dq.append(int(arr[0][0]))
        dq.append(int(arr[1][0]))
        dq.append(int(arr[2][0]))
        dqt.append(int(arr[0][1]))
        dqt.append(int(arr[1][1]))
        dqt.append(int(arr[2][1]))
        counter = collections.Counter()
        for i in range(3,arr.shape[0]):
            dq.append(int(arr[i][0]))
            dqt.append(int(arr[i][1]))
            if dqt[0] in encoded_pos[0] and dqt[1] in encoded_pos[1] and dqt[2] in encoded_pos[2] and dqt[3] in encoded_pos[3]:
                counter[(dq[0],dq[1],dq[2],dq[3])]+=1
    else:
        dq = collections.deque(maxlen=4)
        dq.append(int(arr[0]))
        dq.append(int(arr[1]))
        dq.append(int(arr[2]))
        counter = collections.Counter()
        for i in range(3,arr.shape[0]):
            dq.append(int(arr[i]))
            counter[(dq[0],dq[1],dq[2],dq[3])]+=1
        
    return counter 
    
def quinquegrams(arr,encoded_pos):
    if encoded_pos != None:
        dq = collections.deque(maxlen=5)
        dqt = collections.deque(maxlen=5)
        dq.append(int(arr[0][0]))
        dq.append(int(arr[1][0]))
        dq.append(int(arr[2][0]))
        dq.append(int(arr[3][0]))
        dqt.append(int(arr[0][1]))
        dqt.append(int(arr[1][1]))
        dqt.append(int(arr[2][1]))
        dqt.append(int(arr[3][1]))
        counter = collections.Counter()
        for i in range(4,arr.shape[0]):
            dq.append(int(arr[i][0]))
            dqt.append(int(arr[i][1]))
            if dqt[0] in encoded_pos[0] and dqt[1] in encoded_pos[1] and dqt[2] in encoded_pos[2] and dqt[3] in encoded_pos[3] and dqt[4] in encoded_pos[4]:
                counter[(dq[0],dq[1],dq[2],dq[3],dq[4])]+=1
    else:
        dq = collections.deque(maxlen=5)
        dq.append(int(arr[0]))
        dq.append(int(arr[1]))
        dq.append(int(arr[2]))
        dq.append(int(arr[3]))
        counter = collections.Counter()
        for i in range(4,arr.shape[0]):
            dq.append(int(arr[i]))
            counter[(dq[0],dq[1],dq[2],dq[3],dq[4])]+=1
    return counter        

    

def count_ngrams(npy_path,encoded_pos,size,tmpdir):
    """Searches the node in every text file and gets contexts."""
    files = os.listdir(npy_path)
    counts = dict()
    for filename in files:
        # maker arr concatenating with arrays of zeros for preventing index out of bounds
        if encoded_pos == None:
            arr = np.load(npy_path + filename)[:,0:1]
        else:
            arr = np.load(npy_path + filename)[:,0:2]
        if size == 1:
            counter = unigrams(arr,encoded_pos)
        if size == 2:
            counter = bigrams(arr,encoded_pos)
        if size == 3:
            counter = trigrams(arr,encoded_pos)
        if size == 4:
            counter = quadrigrams(arr,encoded_pos)
        if size == 5:
            counter = quinquegrams(arr,encoded_pos)
        # count 
        r = dict()
        for k,v in counter.items():
            r[k]=1
            if k in counts:
                counts[k]+=v
            else:
                counts[k]=v
        with open(tmpdir + '/' + filename,'wb') as fh:
            pickle.dump(r,fh)
    return counts

def translate(counts, dict_words,lowercase,total_files,size,tmpdir):
    """Translate numbers back to words in a list format for kitconc."""
    ngrams = []
    files = os.listdir(tmpdir)
    # unigrams 
    if size == 1:
        punct = re.compile('^\W+$')
        # range 
        r = dict()
        for filename in files:
            with open(tmpdir + '/' + filename,'rb') as fh:
                rd = pickle.load(fh)
            d = dict()
            for a in rd:
                if lowercase == True:
                    k = dict_words[a].lower()
                else:
                    k = dict_words[a]
                if len(punct.findall(k)) == 0:
                    if k not in d:
                        d[k]=1
            for k in d:
                if k in r:
                    r[k]+=1
                else:
                    r[k]=1
        
        # ngrams
        c = dict()
        for a,v in counts.items():
            if lowercase == True:
                k = dict_words[a].lower()
            else:
                k = dict_words[a]
            if len(punct.findall(k)) == 0:
                if k in c:
                    c[k]+=v 
                else:
                    c[k]=v
        counts = None
        dict_words = None
    # multigrams
    else:
        punct = re.compile('^\W+ | \W+$| \W+ ')
        # range 
        r = dict()
        for filename in files:
            with open(tmpdir + '/' + filename,'rb') as fh:
                rd = pickle.load(fh)
            d = dict()
            for a in rd:
                if lowercase == True:
                    k = ' '.join([dict_words[i] for i in a]).lower()
                else:
                    k = ' '.join([dict_words[i] for i in a])
                if k not in d:
                    d[k]=1
            for k in d:
                if k in r:
                    r[k]+=1
                else:
                    r[k]=1
        
        # ngrams
        c = dict()
        for a,v in counts.items():
            if lowercase == True:
                k = ' '.join([dict_words[i] for i in a]).lower()
            else:
                k = ' '.join([dict_words[i] for i in a])
            if k in c:
                c[k]+=v 
            else:
                c[k]=v
        counts = None
        dict_words = None
    # make
    i = 0
    for k,v in c.items():
        if len(punct.findall(k)) == 0:
            i+=1
            p = (r[k]/float(total_files))*100
            ngrams.append((i,k,v,r[k],p))
    return ngrams 
        


def make_ngrams(workspace,corpus_name,pos,size,lowercase):
    tmpdir = tempfile.mkdtemp()
    encoded_pos = parse_search(workspace,corpus_name,pos)
    total_files = len(os.listdir(workspace+corpus_name + '/data/npy/'))
    counts = count_ngrams(workspace+corpus_name + '/data/npy/',encoded_pos,size,tmpdir)
    dict_words = load_dict(workspace+corpus_name+'/data/idx/words.pickle')
    ngrams = translate(counts,dict_words,lowercase,total_files,size,tmpdir)
    shutil.rmtree(tmpdir)
    return ngrams 
