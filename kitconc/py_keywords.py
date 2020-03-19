# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
import os 
from kitconc.py_wordlist import make_wordlist 
import math 

def load_reference(language):
    d = dict()
    tokens = 0 
    kit_path = os.path.dirname(os.path.abspath(__file__))
    with open(kit_path  + '/data/reflist_' + language + '.tab','r') as fh:
        for line in fh:
            if len(line.strip())!=0:
                f=line.strip().split('\t')
                if len(f)>= 2:
                    d[f[0]] = int(f[1])
                    tokens+=int(f[1])
    return (tokens,d) 

def chi_square(freq_stdc,freq_refc,tk_stdc,tk_refc):
    a = freq_stdc 
    b = freq_refc 
    c = tk_stdc - a 
    d = tk_refc - b 
    N = a + b + c + d
    chi = N * (a*d-b*c)** 2/((a+b)*(c+d)*(a+c)*(b+d))
    chi = round(chi,2) 
    return chi 

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

def make_keywords(workspace,corpus_name,language,measure):
    # load wordlist
    tokens, types, type_token, hapax, wordlist = make_wordlist(workspace,corpus_name,language,True)
    # load reference list
    ref_tokens, ref = load_reference(language)
    # loop
    keywords = list()
    i=0
    for row in wordlist:
        freq_refc = 1
        if row[1] in ref:
            freq_refc = ref[row[1]]
        if measure == 1:
            m = ll(row[2],freq_refc,tokens,ref_tokens)
        else:
            m = chi_square(row[2],freq_refc,tokens,ref_tokens)
        i+=1
        keywords.append([i,row[1],row[2],m])
    return keywords 
        
            
         
    
    
    
    
    
    
    
    
    
    
    
    
