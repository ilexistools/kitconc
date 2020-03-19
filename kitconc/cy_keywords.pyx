# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
import os 
from kitconc.cy_wordlist import make_wordlist 
import math 

cdef tuple load_reference(str language):
    cdef dict d
    cdef int tokens 
    cdef str kit_path 
    cdef str line 
    cdef list f 
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

cdef float chi_square(int freq_stdc,int freq_refc, int tk_stdc,int tk_refc):
    cdef:
        int a
        int b 
        int c 
        int d 
        int N 
        float chi  
    a = freq_stdc 
    b = freq_refc 
    c = tk_stdc - a 
    d = tk_refc - b 
    N = a + b + c + d
    chi = N * (a*d-b*c)** 2/((a+b)*(c+d)*(a+c)*(b+d))
    chi = round(chi,2) 
    return chi 

cdef float ll(int freq_stdc, int freq_refc, int tk_stdc,int tk_refc):
    """Calculates the log-likelihood value"""
    cdef:
        float O 
        float N1
        float N2
        float E1 
        float E2
        float v1 
        float v2 
        float Norm_stdc
        float Norm_refc 
        float LL  
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

def make_keywords(str workspace, str corpus_name,str language,int measure):
    # load wordlist
    cdef:
        int tokens 
        int types 
        float type_token 
        int hapax 
        list wordlist 
        int ref_tokens 
        dict ref 
        list keywords 
        int i 
        tuple row 
        int freq_refc  
        float m 
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
        
            
         
    
    
    
    
    
    
    
    
    
    
    
    
