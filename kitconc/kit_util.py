# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
import os,sys  
import math
import time  
import string 

def __progress(count, total, suffix=''):
        bar_len = 30
        filled_len = int(round(bar_len * count / float(total)))
        percents = round(100.0 * count / float(total), 1)
        bar = '=' * filled_len + '-' * (bar_len - filled_len)
        sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', suffix))
        try:
            sys.stdout.flush()  
        except:
            pass
        
def keywords_reference(filename):
    def readlines(filename):
        i = 0
        with open(filename,'r',encoding='utf-8') as fh:
            for line in fh:
                if len(line.strip())!=0:
                    if i != 0:
                        fields = line.strip().split('\t')
                        if len(fields) >=4:
                            yield (fields[1],fields[2])
                    i+=1
    tokens = 0
    reflist = {}
    freqlist = readlines(filename)
    for item in freqlist:
        tokens+= int(item[1])
        if item[0] not in reflist:
            reflist[item[0]]=int(item[1])
    return (reflist,tokens) 
        

def load_reference_wordlist(filename):
        reflist = {}
        i = 0
        with open(filename,'r','utf-8') as fh:
            for line in fh:
                if len(line.strip())!=0:
                    if i != 0:
                        fields = line.strip().split('\t')
                        if len(fields) >=4:
                            if fields[1] not in reflist:
                                reflist[fields[1]]=int(fields[2])
                    i+=1
        return reflist

def sent2conll2000(sent):
    s = []
    for token in sent:
        s.append(token[0] + ' ' + token[1] + ' O')
    return '\n'.join(s)   

    
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

def dump(obj,filename):
    import pickle
    with open(filename,'wb') as fh:
        pickle.dump(obj,fh)

def load(filename):
    import pickle 
    with open(filename,'rb') as fh:
        obj = pickle.load(fh)
    return obj 

def file2utf8(source_file,target_file,source_encoding='mbcs'):
    import codecs
    BLOCKSIZE = 1048576 # or some other, desired size in bytes
    with codecs.open(source_file, "r", source_encoding,errors="surrogateescape") as sourceFile:
        with codecs.open(target_file, "w", "utf-8") as targetFile:
            while True:
                contents = ''.join(filter(lambda x: x in string.printable, sourceFile.read(BLOCKSIZE)))
                if not contents:
                    break
                targetFile.write(contents)
                

def file2utf8b(source_file,target_file,source_encoding='mbcs'):
    import codecs 
    with open(source_file,'rb') as fh1:
        with codecs.open(target_file,'w','utf-8') as fh2:
            while True:
                contents = fh1.read()
                if not contents:
                    break
                fh2.write(contents.decode(source_encoding))

def files2utf8(source_folder,target_folder,source_encoding='mbcs',show_progress=False):
    # time start
    if show_progress == True:
        print('Running...')
        t0 = time.time()
    if source_folder.endswith('/')==False:
        source_folder = source_folder + '/'
    if target_folder.endswith('/') == False:
        target_folder = target_folder + '/'
    if os.path.exists(target_folder)==False:
        os.mkdir(target_folder)
    files = os.listdir(source_folder)
    i = 0
    total = len(files)
    for filename in files:
        i+=1
        if os.path.isfile(source_folder + filename)==True:
            source_encoding = encoding_get(source_folder + filename)
            if source_encoding != 'utf-8':
                file2utf8b(source_folder + filename,target_folder + filename,source_encoding)
            else:
                with open (source_folder + filename,'r', encoding='utf-8') as fh:
                    content = fh.read()
                with open(target_folder + filename,'w', encoding='utf-8') as fh:
                    fh.write(content)
            if show_progress == True:
                __progress(i, total, '')
    # time end
    if show_progress == True:
        t1 = time.time()
        total_time = round(t1 - t0,2) 
        print('')
        print('Total time: %s seconds' % total_time) 

def encoding_get(filename):
    import chardet
    with open (filename,'rb') as fh:
        dados = b''.join([l for l in fh])
        return chardet.detect(dados)['encoding']

    



