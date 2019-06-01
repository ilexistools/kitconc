# -*- coding: utf-8 -*-
import math 


def load_reference_wordlist(filename):
        reflist = {}
        i = 0
        with open(filename,'r') as fh:
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