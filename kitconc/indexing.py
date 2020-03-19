import os,sys 
import numpy as np 
import pickle 
import multiprocessing as mp 

class Indexing(object):
    
    def __init__(self):
        self.workspace = sys.argv[1]
        self.corpus_name = sys.argv[2]
        self.language = sys.argv[3]
        self.dic_w = self.load_dict(self.workspace+self.corpus_name + '/data/idx/words.pickle')
        self.dic_t = self.load_dict(self.workspace+self.corpus_name + '/data/idx/tags.pickle')
    
    
    def get_files (self,source_folder):
        for filename in os.listdir(source_folder):
            yield filename

    def load_dict(self,path):
        with open(path,'rb') as fh:
            return pickle.load(fh)
    
    def save_npy(self,filename):
        d = []
        with open (self.workspace + self.corpus_name + '/data/tmp1/' + filename,'r', encoding='utf-8') as fh:
            for line in fh:
                if len(line.strip())!= 0:
                    f = line.strip().split('\t')
                    d.append((self.dic_w[f[0]],self.dic_t[f[1]],f[2],f[3]))
        np.save(self.workspace + self.corpus_name + '/data/npy/' + filename, np.array(d,dtype=int), allow_pickle=False)
    
    def save_inverted_dicts(self):
        self.dic_w = {v: k for k, v in self.dic_w.items()}
        with open(self.workspace + self.corpus_name + '/data/idx/words.pickle','wb') as fh:
            pickle.dump(self.dic_w,fh)
        self.dic_t = {v: k for k, v in self.dic_t.items()}
        with open(self.workspace + self.corpus_name + '/data/idx/tags.pickle','wb') as fh:
            pickle.dump(self.dic_t,fh)
    
    def save_lc_dict(self):
        d = dict()
        for k,v in self.dic_w.items():
            key = k.lower()
            if key in d:
                d[key]+=[v]
            else:
                d[key]=[v]
        with open(self.workspace + self.corpus_name + '/data/idx/wordslc.pickle','wb') as fh:
            pickle.dump(d,fh)
            
        

    def execute(self):
        files = self.get_files(self.workspace + self.corpus_name + '/data/tmp1/')
        p = mp.Pool(mp.cpu_count())
        p.map(self.save_npy,files)
        p.close()
        p.join()
        self.save_lc_dict()
        self.save_inverted_dicts()
      

if __name__ == '__main__':
    idx = Indexing()
    idx.execute()

                
        
    
    
     
