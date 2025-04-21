# -*- coding: utf-8 -*-
# Author: jlopes@alumni.usp.br
import os, sys 
import pickle 
import multiprocessing as mp 
import collections
  

class Tagging(object):
    
    def __init__(self):
        # get args
        self.resource_path = sys.argv[1]
        self.workspace =  sys.argv[2]
        self.corpus_name =  sys.argv[3]
        self.language =  sys.argv[4]
        self.source_folder =  sys.argv[5]
        # load sent tokenizer
        sent_tokenizer_path = self.resource_path + 'sent_tokenizer_' + self.language + '.pickle'
        with open(sent_tokenizer_path, 'rb') as fh:
            self.sent_tokenizer = pickle.load(fh)
        # load word tokenizer
        word_tokenizer_path = self.resource_path + 'word_tokenizer_' + self.language +  '.pickle'
        with open(word_tokenizer_path, 'rb') as fh:
            self.word_tokenizer = pickle.load(fh)
        # load tagger 
        tagger_path = self.resource_path+ 'pos_tagger_' + self.language +  '.pickle'
        with open(tagger_path, 'rb') as fh:
            self.tagger = pickle.load(fh)
        # normalize source_folder path
        if not self.source_folder.endswith('/'):
            self.source_folder = self.source_folder + '/'
        
    def get_files(self):
        i = 0
        for filename in os.listdir(self.source_folder):
            i+=1
            yield (filename,i)
    
    def get_wfiles(self):
        i = 0
        for filename in os.listdir(self.workspace+self.corpus_name + '/data/tmp2/'):
            i+=1
            yield filename
    
    def get_tfiles(self):
        i = 0
        for filename in os.listdir(self.workspace+self.corpus_name + '/data/tmp3/'):
            i+=1
            yield filename 
    
    def sent2str(self,tagged_sent,sent_id,file_id):
        s = []
        for token in tagged_sent:
            if token[0] not in self.unique_w:
                self.unique_w[token[0]]=None
            if token[1] not in self.unique_t:
                self.unique_t[token[1]]=None
            s.append("%s\t%s\t%s\t%s" % (token[0],token[1],sent_id,file_id))
        return '\n'.join(s)


    def tag_file(self, filename):
        # Ensure tmp1, tmp2, and tmp3 directories exist
        tmp1_dir = os.path.join(self.workspace, self.corpus_name, 'data', 'tmp1')
        tmp2_dir = os.path.join(self.workspace, self.corpus_name, 'data', 'tmp2')
        tmp3_dir = os.path.join(self.workspace, self.corpus_name, 'data', 'tmp3')
        os.makedirs(tmp1_dir, exist_ok=True)
        os.makedirs(tmp2_dir, exist_ok=True)
        os.makedirs(tmp3_dir, exist_ok=True)

        self.unique_w = collections.defaultdict()
        self.unique_t = collections.defaultdict()
        sent_id = 0
        tagged_sents = []
        with open(self.source_folder + filename[0], 'r', encoding='utf-8') as fh:
            for line in fh:
                if len(line.strip()) != 0:
                    sents = self.sent_tokenizer.tokenize(line.strip())
                    for sent in sents:
                        sent_id += 1
                        tagged_sents.append(self.sent2str(self.tagger.tag(self.word_tokenizer.tokenize(sent)), sent_id, filename[1]))
        
        # Write to tmp1 directory
        with open(os.path.join(tmp1_dir, filename[0]), 'w', encoding='utf-8') as fh2:
            fh2.write('\n'.join(tagged_sents))
        
        # Write to tmp2 and tmp3 directories
        with open(os.path.join(tmp2_dir, filename[0]), 'wb') as fh:
            pickle.dump(self.unique_w, fh)
        
        with open(os.path.join(tmp3_dir, filename[0]), 'wb') as fh:
            pickle.dump(self.unique_t, fh)

    
    def unique(self):
        idx = collections.defaultdict()
        i = 0
        # word indexes
        files = self.get_wfiles()
        for filename in files:
            with open(self.workspace + self.corpus_name + '/data/tmp2/' + filename,'rb') as fh:
                d = pickle.load(fh)
            for k in d:
                if k not in idx:
                    i+=1
                    idx[k]=i
        with open(self.workspace + self.corpus_name + '/data/idx/words.pickle','wb') as fh:
            pickle.dump(idx,fh) 
        # tag indexes
        idx = collections.defaultdict()
        i = 0
        files = self.get_tfiles()
        for filename in files:
            with open(self.workspace + self.corpus_name + '/data/tmp3/' + filename,'rb') as fh:
                d = pickle.load(fh)
            for k in d:
                if k not in idx:
                    i+=1
                    idx[k]=i
        with open(self.workspace + self.corpus_name + '/data/idx/tags.pickle','wb') as fh:
            pickle.dump(idx,fh)
        # file indexes
        idx = collections.defaultdict()
        i = 0
        files = self.get_files()
        for filename in files:
            i+=1
            idx[filename]=i 
        with open(self.workspace + self.corpus_name + '/data/idx/filenames.pickle','wb') as fh:
            pickle.dump(idx,fh)
    
    
    def execute(self):
        files = self.get_files()
        p = mp.Pool(mp.cpu_count())
        p.map(self.tag_file,files)
        p.close()
        p.join()
        self.unique()
          

if __name__ == '__main__':
    t = Tagging()
    t.execute()
