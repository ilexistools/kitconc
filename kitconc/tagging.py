# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
import os, sys 
import nltk 
import pickle 
import multiprocessing as mp 

class TaggingProcess(object):
    
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
        # load sent tokenizer
        tokenizer_path = self.kit_path + '/data/tokenizer_' + self.language + '.pickle'
        with open(tokenizer_path, 'rb') as fh:
            self.sent_tokenizer = pickle.load(fh)
        # load word tokenizer
        self.word_tokenizer = nltk.toktok.ToktokTokenizer()
        # load tagger
        if self.tagging == True:
            tagger_path = self.kit_path + '/data/tagger_' + self.language  + '.pickle'
            with open(tagger_path, 'rb') as fh:
                self.tagger = pickle.load(fh)
        else:
            self.tagger = nltk.DefaultTagger('*')
        # normalize source_folder path
        if not self.source_folder.endswith('/'):
            self.source_folder = self.source_folder + '/'
    
    
    def escape_quotes(self,s):
        return s.replace("'","´").replace('"','´´')
    
    
    def tag_textfile(self,filename):
        tagged_sents = []
        with open(self.source_folder + filename,'r',encoding=self.encoding) as fh:
            for line in fh:
                if len(line.strip()) != 0:
                    sents = self.sent_tokenizer.tokenize(line.strip())
                    for sent in sents:
                        tagged_sent = self.tagger.tag(self.word_tokenizer.tokenize(sent))
                        str_sent = []
                        for tagged_token in tagged_sent:
                            str_sent.append(nltk.tuple2str(tagged_token))
                        tagged_sents.append(self.escape_quotes(' '.join(str_sent)))
        with open(self.workspace + self.corpus_name + '/data/tagged/' + filename,'w',encoding='utf-8') as fh2:
            fh2.write('\n'.join(tagged_sents).strip()) 
        if self.show_progress == True:
            print(filename)
    
    def notag_textfile(self,filename):
        tokenized_sents = []
        with open(self.source_folder + filename,'r',encoding=self.encoding) as fh:
            for line in fh:
                if len(line.strip()) != 0:
                    sents = self.sent_tokenizer.tokenize(line)
                    for sent in sents:
                        tokenized_sent = '/0 '.join(self.word_tokenizer.tokenize(sent)) + '/0'
                        tokenized_sents.append(tokenized_sent)
        with open(self.workspace + self.corpus_name + '/data/tagged/' + filename,'w',encoding='utf-8') as fh2:
            fh2.write('\n'.join(tokenized_sents).strip()) 
        if self.show_progress == True:
            print(filename)
    
            
    def execute(self):
        # count total files and get textfiles 
        files = os.listdir(self.source_folder)
        self.total_files = len(files)
        self.file_count = 0
        # start process
        p = mp.Pool(mp.cpu_count())
        if self.tagging == True:
            p.map(self.tag_textfile,files)
        else:
            p.map(self.notag_textfile,files)
        # finish
        p.close()
        p.join()
                
          

if __name__ == '__main__':
    step1 = TaggingProcess()
    step1.execute()
    
    
    