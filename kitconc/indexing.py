# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
import os, sys 
import collections 
import nltk 


class IndexingProcess(object):
    
    def __init__(self):
        # get args
        self.kit_path = sys.argv[1]
        self.workspace =  sys.argv[2]
        self.corpus_name =  sys.argv[3]
        self.language =  sys.argv[4]
        self.encoding =  sys.argv[5]
        self.source_folder =  sys.argv[6]
        self.tagging =  eval(sys.argv[7])
        self.show_progress =  eval(sys.argv[8])
    
    def get_tagged_files(self):
        for filename in os.listdir(self.workspace + self.corpus_name + '/data/tagged'):
            yield filename 
    
    def get_tagged_sents(self,filename):
        with open (self.workspace + self.corpus_name + '/data/tagged/' + filename,'r',encoding=self.encoding) as fh:
            for line in fh:
                if len(line.strip())!=0:
                    yield line.strip()
    
    def get_tagged_tokens(self,sent):
        for token in sent.split(' '):
            yield nltk.str2tuple(token.strip())  
            
    def execute(self):
        fi = 0
        si = 0
        tki = 0
        word_idx = collections.defaultdict()
        wi = 0
        tag_idx = collections.defaultdict()
        ti=0
        files = self.get_tagged_files()
        for filename in files:
            loc = 0
            rows = []
            fi+=1
            tagged_sents = self.get_tagged_sents(filename)
            for sent in tagged_sents:
                si+=1
                tkpos = 0
                for token in self.get_tagged_tokens(sent):
                    loc+=1
                    tki+=1
                    tkpos+=1
                    if token[0] not in word_idx:
                        wi+=1
                        word_idx[token[0]]=wi
                    if token[1] not in tag_idx:
                        ti+=1
                        tag_idx[token[1]]=ti
                    rows.append('\t'.join([str(tki),str(fi),str(si),str(tkpos),str(word_idx[token[0]]),str(tag_idx[token[1]]),str(loc)]) + '\n')
            with open(self.workspace + self.corpus_name + '/data/searches.tab','a',encoding='utf-8') as fh:
                fh.write(''.join(rows)) 
        rows = []
        for k in word_idx:
            rows.append(str(word_idx[k]) + '\t' + k)
        with open(self.workspace + self.corpus_name + '/data/words.tab', 'w', encoding='utf-8') as fh:
            if self.encoding != 'utf-8':
                fh.write( str('\n'.join(rows),'utf-8') )
            else:
                fh.write('\n'.join(rows))
                
        del word_idx 
        rows = []
        for k in tag_idx:
            rows.append(str(tag_idx[k]) + '\t' + k)
        with open(self.workspace + self.corpus_name + '/data/tags.tab', 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(rows))
        del tag_idx
        rows = []
        fi = 0 
        files = self.get_tagged_files() 
        for filename in files:
            fi+=1
            rows.append(str(fi) + '\t' + filename)
        with open(self.workspace + self.corpus_name + '/data/textfiles.tab', 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(rows))
            

if __name__ == '__main__':
    step2 = IndexingProcess()
    step2.execute()
    