# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
import os
import pickle  
from string import punctuation
from kitconc.core import Config
import collections 
try:
    import nltk 
except:
    nltk = None 


class Models(object):
    
    def __init__(self):
        self.__path = os.path.dirname(os.path.abspath(__file__))
    
    def save_model (self,model,language):
        lm_path = self.__path + '/data/' + language + '_model.pickle'
        if os.path.exists(lm_path):
            os.remove(lm_path)
        with open(lm_path,'wb') as fh:
            pickle.dump(model,fh)
    
    def remove_model(self,language):
        lm_path = self.__path + '/data/' + language + '_model.pickle'
        if os.path.exists(lm_path):
            os.remove(lm_path)
    
    def list_models(self):
        I = 11
        E = 7
        files = os.listdir(self.__path + '/data/')
        language_models =[]
        d = dict()
        for filename in files:
            if filename.endswith('_model.pickle'):
                try:
                    language = filename[:-13]
                    if language not in d:
                        d[language]=None
                except:
                    pass 
            elif filename.startswith('pos_tagger_'):
                try:
                    size = len(filename)
                    m = size - (I+E)
                    language = filename[I:(I+m)]
                    if language not in d:
                        d[language]=None
                except:
                    pass
        for k in d:
            if k != 'language':
                language_models.append(k)
        return language_models 
        
    
    def save_reflist(self,freqlist,language):
        reflist_path = self.__path + '/data/reflist_' + language + '.tab'
        if os.path.exists(reflist_path):
            os.remove(reflist_path)
        s=[]
        for w,f in freqlist:
            s.append('%s\t%s' % (w,f))
        with open(reflist_path,'w',encoding='utf-8') as fh:
            fh.write('\n'.join(s))
    
    def save_stoplist(self,stoplist,language):
        stoplist_path = self.__path + '/data/stolist_' + language + '.tab'
        if os.path.exists(stoplist_path):
            os.remove(stoplist_path)
        with open(stoplist_path,'w',encoding='utf-8') as fh:
            fh.write('\n'.join(stoplist))
    
    def remove_reflist(self,language):
        reflist_path = self.__path + '/data/reflist_' + language + '.tab'
        if os.path.exists(reflist_path):
            os.remove(reflist_path)
        
    def remove_stoplist(self,language):
        stoplist_path = self.__path + '/data/stoplist_' + language + '.tab'
        if os.path.exists(stoplist_path):
            os.remove(stoplist_path)
        
    def dummy_model(self):
        return DummyModel
    
    def spacy_model(self,model_name,disable=[]):
        return spacyModels().load(model_name,disable=disable)
    
    def nltk_create_model(self,source,language,**kwargs):
        sent_tokenizer = kwargs.get('sent_tokenizer',None)
        word_tokenizer = kwargs.get('word_tokenizer',None)
        pos_tagger = kwargs.get('pos_tagger',None) 
        regexp_word = kwargs.get('regexp_word','\w+')
        reflist_path =kwargs.get('reflist',None)
        stoplist_path = kwargs.get('stoplist',None)
        show_progress = kwargs.get('show_progress',False)
        nltk_model =  nltkTrainModel(sent_tokenizer=sent_tokenizer,word_tokenizer=word_tokenizer,pos_tagger=pos_tagger,regexp_word=regexp_word,
                                     reflist=reflist_path,stoplist=stoplist_path, show_progress=show_progress)
        nltk_model.train(source)
        nltk_model.save(language)
        
        

class Token(object):

    def __init__(self,**kwargs):
        self.text = kwargs.get('text',None)
        self.pos_ = kwargs.get('pos',None)
            
class DummyModel(object):
    
    def __init__(self,text):
        self.sents = []
        self.__get_sents(text)
          
    def __get_sents(self,text):
        for c in ['?','!','.']:
            text = text.replace(c, '%s\n' % c)
        for sent in text.split('\n'):
            if len(sent.strip())!=0:
                for p in punctuation:
                    sent = sent.replace(p,' %s ' % p)
                new_sent = []
                for item in sent.split():
                    if len(item.strip())!=0:
                        token = Token(text=item,pos='*')
                        new_sent.append(token)
                self.sents.append(new_sent)
            
    def __iter__(self):
        for sent in self.sents:
            yield sent

                        
class spacyModels(object):
    
    def __init__(self,**kwargs):
        self.disable = kwargs.get('disable',['ner'])
        
    def load(self,model_name,**kwargs):
        self.disable = kwargs.get('disable',['ner'])
        try:
            import spacy 
            return spacy.load(model_name,disable=self.disable)
        except:
            return None 

class nltkTrainModel(object):
    
    def __init__(self,**kwargs):
        self.sent_tokenizer = kwargs.get('sent_tokenizer',None)
        self.word_tokenizer = kwargs.get('word_tokenizer',None)
        self.pos_tagger = kwargs.get('pos_tagger',None) 
        self.regexp_word = kwargs.get('regexp_word','\w+')
        self.reflist_path =kwargs.get('reflist',None)
        self.reflist = None
        self.stoplist = None
        self.stoplist_path = kwargs.get('stoplist',None)
        self.show_progress = kwargs.get('show_progress',False)
    
    def train(self,source_folder):
        # normalize path 
        if not source_folder.endswith('/'):
            source_folder+='/'
        self.source_folder = source_folder
        # reflist 
        self.reflist = []
        if self.reflist_path != None:
            # load reflist from a file
            if os.path.exists(self.reflist_path) and os.path.isfile(self.reflist_path):
                with open(self.reflist_path,'r',encoding='utf-8') as fh:
                    for line in fh:
                        if len(line.strip())!=0:
                            f = line.strip().split('\t')
                            if len(f)>= 2:
                                self.reflist.append((f[0],int(f[1])))
        else:
            # create a reflist from the source corpus
            punct = [c for c in punctuation]
            counter = collections.Counter()
            for word in self.__read_words():
                counter[word.lower()]+=1
            for k,v in counter.most_common():
                if v > 1:
                    if k not in punct:
                        self.reflist.append((k,v))
        # stoplist
        self.stoplist = []
        if self.stoplist_path != None:
            # load stoplist from a file
            if os.path.exists(self.stoplist_path) and os.path.isfile(self.stoplist_path):
                with open(self.stoplist_path,'r',encoding='utf-8') as fh:
                    for line in fh:
                        if len(line.strip())!=0:
                            self.stoplist.append(line.strip())
        else:
            # just use punctuation
            self.stoplist =  [c for c in punctuation]
        # train sent_tokenizer
        if self.show_progress == True:
            print('Training sentence tokenizer...')
        if self.sent_tokenizer == None:
            trainer = nltk.punkt.PunktTrainer()
            trainer.INCLUDE_ALL_COLLOCS = True
            for text in self.__read_texts():
                trainer.train(text,finalize=False)
            self.sent_tokenizer = nltk.punkt.PunktSentenceTokenizer(trainer.get_params())
            trainer = None
        # train word tokenizer
        if self.show_progress == True:
            print('Training word tokenizer...')
        if self.word_tokenizer == None:
            self.word_tokenizer = nltk.RegexpTokenizer(self.regexp_word)
        # train tagger 
        if self.show_progress == True:
            print('Training pos tagger...')
        # get the most common tag 
        counter = collections.Counter()
        for tag in self.__read_tags():
            counter[tag]+=1
        default_tag = counter.most_common(1)[0][0] 
        # get the data for training and testing
        tagged_sents = list(self.__read_tagged_sents())
        cutoff = int(.75 * len(tagged_sents))
        training_sents = tagged_sents[:cutoff]
        test_sents = tagged_sents[cutoff:] 
        tagged_sents = None
        # train sequential taggers   
        default_tagger = nltk.DefaultTagger(default_tag)
        unigram_tagger = nltk.UnigramTagger(training_sents,backoff=default_tagger)
        self.pos_tagger = nltk.BigramTagger(training_sents,backoff=unigram_tagger)
        # print results
        if self.show_progress == True:
            print('Testing tagger...')
        if self.show_progress == True:
            print ('POS tagger precision: %s' % self.pos_tagger.evaluate(test_sents))
        
        
    def save(self,language):
        if self.sent_tokenizer != None and self.word_tokenizer != None and self.pos_tagger != None:
            if self.show_progress == True:
                print('Saving model...')
            config = Config()
            config.add_sent_tokenizer(self.sent_tokenizer, language)
            config.add_tokenizer(self.word_tokenizer, language)
            config.add_tagger(self.pos_tagger, language)
            s = []
            for item in self.reflist:
                s.append('%s\t%s' % (item[0],item[1]))
            config.add_reflist('\n'.join(s), language)
            s = None
            config.add_stoplist('\n'.join(self.stoplist), language)    
            if self.show_progress == True:
                print('OK.')
        else:
            if self.show_progress == True:
                print('Kitconc cannot save the model. Trained components are missing.')
         
    
    
    def __read_texts(self):
        files = os.listdir(self.source_folder)
        for filename in files:
            text = []
            with open(self.source_folder + filename,'r', encoding='utf-8') as fh:
                for line in fh:
                    if len(line.strip())!=0:
                        raw_sent = [ self.__str2tuple(token)[0] for token in line.strip().split()]
                        text.append(self.__norm_punct(' '.join(raw_sent)))
            yield '\n'.join(text)
        
    def __read_tagged_sents(self):
        files = os.listdir(self.source_folder)
        for filename in files:
            with open(self.source_folder + filename,'r', encoding='utf-8') as fh:
                for line in fh:
                    if len(line.strip())!=0:
                        tagged_sent = [ self.__str2tuple(token) for token in line.strip().split()]
                        yield tagged_sent
    
    
    def __read_raw_sents(self):
        files = os.listdir(self.source_folder)
        for filename in files:
            with open(self.source_folder + filename,'r', encoding='utf-8') as fh:
                for line in fh:
                    if len(line.strip())!=0:
                        raw_sent = [ self.__str2tuple(token)[0] for token in line.strip().split()]
                        yield self.__norm_punct(' '.join(raw_sent))
    
    def __read_tags(self):
        files = os.listdir(self.source_folder)
        for filename in files:
            with open(self.source_folder + filename,'r', encoding='utf-8') as fh:
                for line in fh:
                    if len(line.strip())!=0:
                        tag_sent = [ self.__str2tuple(token)[1] for token in line.strip().split()]
                        for tag in tag_sent:
                            yield tag
    
    def __read_words(self):
        files = os.listdir(self.source_folder)
        for filename in files:
            with open(self.source_folder + filename,'r', encoding='utf-8') as fh:
                for line in fh:
                    if len(line.strip())!=0:
                        word_sent = [self.__str2tuple(token)[0] for token in line.strip().split()]
                        for word in word_sent:
                            yield word
    
    def __str2tuple(self,s):
        sep='/'
        loc = s.rfind(sep)
        if loc >= 0:
            return (s[:loc], s[loc + len(sep) :])
        else:
            return (s, 'N')
    
    def __norm_punct(self,s):
        s = s.replace(' .','.')
        s = s.replace(' ?','?')
        s = s.replace(' !','!')
        s = s.replace(' ,',',')
        s = s.replace(' ;',';')
        s = s.replace(' :',':')
        return s 
    
        


            
             

