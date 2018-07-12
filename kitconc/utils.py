import os
import shutil  
import pickle
import math
from PIL import Image, ImageDraw
from nltk.metrics.association import BigramAssocMeasures
import nltk 

def create_temp_folder(path):
    flag = True 
    try:
        if not os.path.exists(path):
            if not os.path.isfile(path):
                os.mkdir(path)
        flag = True 
    except:
        flag = False 
    return flag 

def remove_temp_folder(path):
    flag = True 
    try:
        if os.path.exists(path):
            if not os.path.isfile(path):
                shutil.rmtree(path)
                
        flag = True 
    except:
        flag = False 
    return flag 
            
def draw_barcode(points):
    # create rectangle
    im = Image.new('RGB', (201,19), (255,255,255))
    dr = ImageDraw.Draw(im)
    dr.rectangle(((0,0),(200,18)), fill="white", outline="blue")
    # draw lines
    for point in points:
        p = (point * 200)/100
        dr.line(((p,0),(p,18)), fill="black", width=1)
    # save file
    return im  

def get_corpus_info(workspace, corpus_name):
    """Gets the corpus_info dictionary object"""
    corpus_path = workspace + corpus_name  
    fh = open(corpus_path + '/info.pickle','rb')
    corpus_info = pickle.load(fh)
    fh.close()
    return corpus_info 

def cleanse(workspace,corpus_name):
    """Deletes a corpus folder"""
    import shutil
    shutil.rmtree(workspace + corpus_name)

def get_chi_square_method():
    bam = BigramAssocMeasures
    return bam.chi_sq

def chi_square(freq_stdc,freq_refc,tk_stdc,tk_refc):
    a = freq_stdc 
    b = freq_refc 
    c = tk_stdc - a 
    d = tk_refc - b 
    N = a + b + c + d
    chi = N * (a*d-b*c)** 2/((a+b)*(c+d)*(a+c)*(b+d))
    chi = round(chi,2) 
    return chi 

def observed_expected(ab,a,b,N, h=1):
    O = ab / float(N)
    E = (a / float(N)) * (b / float(N))
    E =  E * h
    OE = O/E
    return OE 

def mutual_information(ab,a,b,N, h=1):
    O = ab / float(N)
    E = (a / float(N)) * (b / float(N))
    E =  E * h
    OE = O/E
    I = math.log(OE,2)
    I = round(I,2)
    return I 

def tscore(ab,a,b,N, h=1):
    O = ab / float(N)
    E = (a / float(N)) * (b / float(N))
    E =  E * h
    T = (O-E) / (math.sqrt(ab)/float(N))
    T = round(T,2)
    return T

def ll(freq_stdc,freq_refc,tk_stdc,tk_refc):
    """Calculates the log-likelihood value"""
    O = float(freq_stdc+freq_refc)
    N1 = float(tk_stdc)
    N2 = float(tk_refc)
    E1 = N1*O/(N1+N2) 
    E2 = N2*O/(N1+N2)
    if freq_stdc < 1 or E1 < 1:
        v1 = 0
    else:
        v1 = math.log(freq_stdc/E1)
    if freq_refc < 1 or E2 < 1:
        v2 = 0
    else:
        v2 = math.log(freq_refc/E2)
    LL = round(2 * ((freq_stdc * v1)+(freq_refc * v2)),2)
    Norm_stdc = freq_stdc/float(tk_stdc)
    Norm_refc = freq_refc/float(tk_refc)
    if Norm_stdc == 0:
        Norm_stdc = 0.5 / float(tk_stdc)
    if Norm_refc == 0:
        Norm_refc = 0.5 / float(tk_refc)
    if Norm_stdc < Norm_refc:
        LL = - LL
    return LL


def logRatio(freq_stdc,freq_refc,tk_stdc,tk_refc):
    Norm_stdc = freq_stdc/float(tk_stdc)
    Norm_refc = freq_refc/float(tk_refc)
    if Norm_stdc == 0:
        Norm_stdc = 0.5 / float(tk_stdc)
    if Norm_refc == 0:
        Norm_refc = 0.5 / float(tk_refc)
    lr = math.log2((Norm_stdc/Norm_refc))
    return lr

def train_sequential_tagger():
    tagged_sents = nltk.corpus.brown.tagged_sents()
    print(len(tagged_sents))
    train_set = tagged_sents[:50000]
    test_set = tagged_sents[-7000:]
    s = []  
    
    tagger0 = tagger0 = nltk.DefaultTagger('NN')
    print(tagger0.evaluate(test_set))
    
    tagger1 = nltk.UnigramTagger(train_set, backoff=tagger0)
    print(tagger1.evaluate(test_set))
    
    tagger2 = nltk.BigramTagger(train_set, backoff=tagger1)
    print(tagger2.evaluate(test_set))
    
    f = open('/home/lopes/corpora/tagger.pickle','wb')
    pickle.dump(tagger2,f)
    f.close()


def sent2conll2000(sent):
    s = []
    for token in sent:
        s.append(token[0] + ' ' + token[1] + ' O')
    return '\n'.join(s)   


def train_MacMorpho_tagger(**kwargs):
    universal_tagset = kwargs.get('universal_tagset',False)
    data_path = kwargs.get('data_path',None)
    if data_path != None:
        if data_path not in nltk.data.path:
            nltk.data.path.append(data_path)
    
    if universal_tagset ==True:
        sents = nltk.corpus.mac_morpho.tagged_sents(tagset='universal')
    else:
        sents = nltk.corpus.mac_morpho.tagged_sents()
    
    import collections
    counter  = collections.Counter()
    
    for sent in sents:
        print(sent)
        input('')
        
#train_MacMorpho_tagger(universal_tagset=True,data_path = '/home/lopes/nltk_data/')

def load_merge_tags_rules(filename,**kwargs):
    encoding = kwargs.get('encoding','utf-8')
    rules = []
    with open (filename,'r',encoding=encoding) as fh:
        for line in fh:
            if len(line.strip()) !=0:
                fields = line.strip().split('\t')
                if len(fields) >= 3:
                    rule=(fields[0].strip(),fields[1].strip(),fields[2].strip())
                    rules.append(rule)
    return rules 


def remove_lines(filename):
    import pandas as pd
    tb = pd.read_excel(filename)
    print(tb.head())
    keywords = []
    stoplist = ['economia','liquidez','dinheiro', 'maior','menor']
    
    new_tb = tb[~tb['WORD'].isin(stoplist)]

    
    for kv in new_tb.itertuples(index=False):
        if kv[1] in stoplist:
            print (kv[1])
            #keywords.append(str(kv[0]) + '\t' + kv[1] + '\t' + str(kv[2])  +  '\t' + str(kv[3]))
    
    print(new_tb.head())
            
    
     
    
    
    
                
                
                
                
        
    

        
        
        
        

    


