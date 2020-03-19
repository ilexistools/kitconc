# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
import numpy as np 
import pickle

class KitData(object):
    
    def __init__(self,workspace,corpus_name,language):
        self.workspace = workspace 
        self.corpus_name = corpus_name 
        self.language = language  

    def info_get(self):
        with open (self.workspace + self.corpus_name + '/data/idx/info.pickle', 'rb') as fh:
            info = pickle.load(fh)
        return info
    
    def tokens_get(self):
        info = self.info_get()
        return info[0]
    
    def types_get(self):
        info = self.info_get()
        return info[1]
    
    def ttr_get(self):
        info = self.info_get()
        return info[2]
    
    def hapax_get(self):
        info = self.info_get()
        return info[3]
    
    def textfiles_get_names(self):
        with open(self.workspace + self.corpus_name + '/data/idx/filenames.pickle','rb') as fh:
            d = pickle.load(fh)
        for k in d:
            yield k[0]
    
    def fileids_get(self):
        with open(self.workspace + self.corpus_name + '/data/idx/filenames.pickle','rb') as fh:
            d = pickle.load(fh)
        for k in d:
            yield k[1]
    
    def words_get(self,fileids=None):
        with open(self.workspace + self.corpus_name + '/data/idx/words.pickle','rb') as fh:
            dict_words = pickle.load(fh)
        with open(self.workspace + self.corpus_name + '/data/idx/filenames.pickle','rb') as fh:
            dict_filenames = pickle.load(fh)
        if fileids == None:
            for k in dict_filenames:
                arr = np.load(self.workspace + self.corpus_name + '/data/npy/' + k[0] + '.npy')
                for i in range(0,arr.shape[0]):
                    yield dict_words[arr[i,0]]
        else:
            if type(fileids) != list:
                fileids = [fileids] 
            for k in dict_filenames:
                if k[1] in fileids:
                    arr = np.load(self.workspace + self.corpus_name + '/data/npy/' + k[0] + '.npy')
                    for i in range(0,arr.shape[0]):
                        yield dict_words[arr[i,0]]
    
    def tagged_words_get(self,fileids=None):
        with open(self.workspace + self.corpus_name + '/data/idx/words.pickle','rb') as fh:
            dict_words = pickle.load(fh)
        with open(self.workspace + self.corpus_name + '/data/idx/tags.pickle','rb') as fh:
            dict_tags = pickle.load(fh)
            
        with open(self.workspace + self.corpus_name + '/data/idx/filenames.pickle','rb') as fh:
            dict_filenames = pickle.load(fh)
        if fileids == None:
            for k in dict_filenames:
                arr = np.load(self.workspace + self.corpus_name + '/data/npy/' + k[0] + '.npy')
                for i in range(0,arr.shape[0]):
                    yield (dict_words[arr[i,0]],dict_tags[arr[i,1]])
        else:
            if type(fileids) != list:
                fileids = [fileids] 
            for k in dict_filenames:
                if k[1] in fileids:
                    arr = np.load(self.workspace + self.corpus_name + '/data/npy/' + k[0] + '.npy')
                    for i in range(0,arr.shape[0]):
                        yield (dict_words[arr[i,0]],dict_tags[arr[i,1]])
    
    def sents_get(self,fileids=None):
        with open(self.workspace + self.corpus_name + '/data/idx/words.pickle','rb') as fh:
            dict_words = pickle.load(fh)
        with open(self.workspace + self.corpus_name + '/data/idx/filenames.pickle','rb') as fh:
            dict_filenames = pickle.load(fh)
        if fileids == None:
            for k in dict_filenames:
                arr = np.load(self.workspace + self.corpus_name + '/data/npy/' + k[0] + '.npy')
                arr = np.split(arr[:, 0], np.cumsum(np.unique(arr[:, 2], return_counts=True)[1])[:-1])
                for a in arr:
                    sent = []
                    for i in a:
                        sent.append(dict_words[i])
                    yield sent 
        else:
            if type(fileids) != list:
                fileids = [fileids] 
            for k in dict_filenames:
                if k[1] in fileids:
                    arr = np.load(self.workspace + self.corpus_name + '/data/npy/' + k[0] + '.npy')
                    arr = np.split(arr[:, 0], np.cumsum(np.unique(arr[:, 2], return_counts=True)[1])[:-1])
                    for a in arr:
                        sent = []
                        for i in a:
                            sent.append(dict_words[i])
                        yield sent
    
    def tagged_sents_get(self,fileids=None):
        with open(self.workspace + self.corpus_name + '/data/idx/words.pickle','rb') as fh:
            dict_words = pickle.load(fh)
        with open(self.workspace + self.corpus_name + '/data/idx/filenames.pickle','rb') as fh:
            dict_filenames = pickle.load(fh)
        with open(self.workspace + self.corpus_name + '/data/idx/tags.pickle','rb') as fh:
            dict_tags = pickle.load(fh)
        if fileids == None:
            for k in dict_filenames:
                arr = np.load(self.workspace + self.corpus_name + '/data/npy/' + k[0] + '.npy')
                arr_t = np.split(arr[:, 1], np.cumsum(np.unique(arr[:, 2], return_counts=True)[1])[:-1])
                arr = np.split(arr[:, 0], np.cumsum(np.unique(arr[:, 2], return_counts=True)[1])[:-1])
                for j in range(0,len(arr)):
                    sent = []
                    for i in range(0,arr[j].shape[0]):
                        sent.append((dict_words[arr[j][i]],dict_tags[arr_t[j][i]]))
                    yield sent 
        else:
            if type(fileids) != list:
                fileids = [fileids] 
            for k in dict_filenames:
                if k[1] in fileids:
                    arr = np.load(self.workspace + self.corpus_name + '/data/npy/' + k[0] + '.npy')
                    arr_t = np.split(arr[:, 1], np.cumsum(np.unique(arr[:, 2], return_counts=True)[1])[:-1])
                    arr = np.split(arr[:, 0], np.cumsum(np.unique(arr[:, 2], return_counts=True)[1])[:-1])
                    for j in range(0,len(arr)):
                        sent = []
                        for i in range(0,arr[j].shape[0]):
                            sent.append((dict_words[arr[j][i]],dict_tags[arr_t[j][i]]))
                        yield sent
    
    def ndarrays_get(self,fileids=None):
        with open(self.workspace + self.corpus_name + '/data/idx/filenames.pickle','rb') as fh:
            dict_filenames = pickle.load(fh)
        if fileids == None:
            for k in dict_filenames:
                arr = np.load(self.workspace + self.corpus_name + '/data/npy/' + k[0] + '.npy')
                yield arr 
        else:
            if type(fileids) != list:
                fileids = [fileids] 
            for k in dict_filenames:
                if k[1] in fileids:
                    arr = np.load(self.workspace + self.corpus_name + '/data/npy/' + k[0] + '.npy')
                    yield arr
    
    def ndarrays_filenames_get(self,fileids=None):
        with open(self.workspace + self.corpus_name + '/data/idx/filenames.pickle','rb') as fh:
            dict_filenames = pickle.load(fh)
        if fileids == None:
            for k in dict_filenames:
                yield str(self.workspace + self.corpus_name + '/data/npy/' + k[0] + '.npy')
        else:
            if type(fileids) != list:
                fileids = [fileids] 
            for k in dict_filenames:
                if k[1] in fileids:
                    yield str(self.workspace + self.corpus_name + '/data/npy/' + k[0] + '.npy')
    
    def dict_words_get(self):
        with open(self.workspace + self.corpus_name + '/data/idx/words.pickle','rb') as fh:
            return pickle.load(fh)
    
    def dict_tags_get(self):
        with open(self.workspace + self.corpus_name + '/data/idx/tags.pickle','rb') as fh:
            return pickle.load(fh)
        
    
    
                    
    
                
        
                            
                
        
        
    
    
    
        
    
     
        