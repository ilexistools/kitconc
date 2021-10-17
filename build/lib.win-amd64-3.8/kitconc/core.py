# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
import os  
import pickle
import requests, zipfile, io 

class Examples(object):
    """This class is used to download examples and resources."""
    
    def __init__(self):
        self.__path = os.path.dirname(os.path.abspath(__file__))
    
    def download(self,**kwargs):
        """Downloads code examples and resources from kitconc github repository:
        https://github.com/ilexistools/kitconc-examples/archive/master.zip
        :param dest_path: Prints a progress message if value is True
        :type dest_path: str
        :param show_progress: Prints a progress message if value is True
        :type show_progress: boolean
        :return: None
        :rtype: None
        """
        # get args
        dest_path = kwargs.get('dest_path',os.getcwd())
        show_process = kwargs.get('show_process',True)
        # fix path problems
        if not dest_path.endswith('/'):
            dest_path = dest_path + '/'
        
        # check if it was already downloaded
        if os.path.exists(dest_path + 'kitconc-examples')==True:
            print('The kitconc-examples resource already exists!')
        else:
            # start message
            if show_process == True:
                print('Downloading...')
            try:
                url = 'https://github.com/ilexistools/kitconc-examples/archive/master.zip'
                r = requests.get(url)
                z = zipfile.ZipFile(io.BytesIO(r.content))
                z.extractall(dest_path)
                # rename the folder
                if os.path.exists(dest_path + '/kitconc-examples-master')==True:
                    os.rename(dest_path + '/kitconc-examples-master',dest_path + 'kitconc-examples')
                    # files location message
                    if show_process ==True:
                        print('Location: ' + dest_path + 'kitconc-examples')
                print('Done!')
            except:
                print('Download was not possible.')

class Config(object):
    """This class is used to configure kitconc."""
    
    def __init__(self):
        self.__path = os.path.dirname(os.path.abspath(__file__)) 
    
    def get_data_path(self):
        """Returns kitconc data path
        :return: path
        :rtype: str
        """
        return self.__path + '/data/'
    
    def list_data_files(self):
        """Returns a list of files from kitconc data path
        :return: filenames
        :rtype: list
        """
        files = os.listdir(self.get_data_path())
        return files
    
    def add_sent_tokenizer(self,sent_tokenizer,language):
        """Adds a new tokenizer to kitconc resources
        :param sent_tokenizer: a trained sentence tokenizer
        :type sent_tokenizer: object
        :param language: name of language
        :type language: str 
        :return: True or False
        :rtype: boolean
        """
        flag = False 
        try:
            data_path = self.__path + '/data/sent_tokenizer_' + language + '.pickle'
            with open (data_path,'wb') as fh:
                pickle.dump(sent_tokenizer,fh)
            flag = True
        except:
            flag = None
        return flag 
        
    def add_tokenizer(self,tokenizer,language):
        """Adds a new tokenizer to kitconc resources
        :param tokenizer: a trained tokenizer
        :type tokenizer: object
        :param language: name of language
        :type language: str 
        :return: True or False
        :rtype: boolean
        """
        flag = False 
        try:
            data_path = self.__path + '/data/word_tokenizer_' + language + '.pickle'
            with open (data_path,'wb') as fh:
                pickle.dump(tokenizer,fh)
            flag = True
        except:
            flag = None
        return flag  
        
    def add_tagger(self,tagger,language):
        """Adds a new tagger to kitconc resources
        :param tagger: a trained tagger
        :type tagger: object
        :param language: name of language
        :type language: str 
        :return: True or False
        :rtype: boolean
        """
        flag = False 
        try:
            data_path = self.__path + '/data/pos_tagger_' + language + '.pickle'
            with open (data_path,'wb') as fh:
                pickle.dump(tagger,fh)
            flag = True
        except:
            flag = None
        return flag
    
    def add_reflist(self,reflist,language):
        """Adds a new reflist to kitconc resources
        :param reflist: a reference list
        :type reflist: str
        :param language: name of language
        :type language: str 
        :return: True or False
        :rtype: boolean
        """
        flag = False 
        try:
            data_path = self.__path + '/data/reflist_' + language + '.tab'
            with open (data_path,'w',encoding='utf-8') as f:
                f.write(reflist)
            flag = True
        except:
            flag = None
        return flag
    
    def add_stoplist(self,stoplist,language):
        """Adds a new stoplist to kitconc resources
        :param stoplist: a stoplist
        :type stoplist: str
        :param language: name of language
        :type language: str 
        :return: True or False
        :rtype: boolean
        """
        flag = False 
        try:
            data_path = self.__path + '/data/stoplist_' + language + '.tab'
            with open (data_path,'w',encoding='utf-8') as f:
                f.write(stoplist)
            flag = True
        except:
            flag = None
        return flag

class Resources(object):
    
    def __init__(self):
        self.__path = os.path.dirname(os.path.abspath(__file__)) 
    
    def get_data_path(self):
        """Returns kitconc data path
        :return: path
        :rtype: str
        """
        return self.__path + '/data/'
    
    def list_data_files(self):
        """Returns a list of files from kitconc data path
        :return: filenames
        :rtype: list
        """
        files = os.listdir(self.get_data_path())
        return files
    
    def add_sent_tokenizer(self,sent_tokenizer,language):
        """Adds a new tokenizer to kitconc resources
        :param sent_tokenizer: a trained sentence tokenizer
        :type sent_tokenizer: object
        :param language: name of language
        :type language: str 
        :return: True or False
        :rtype: boolean
        """
        flag = False 
        try:
            data_path = self.__path + '/data/sent_tokenizer_' + language + '.pickle'
            with open (data_path,'wb') as fh:
                pickle.dump(sent_tokenizer,fh)
            flag = True
        except:
            flag = None
        return flag 
        
    def add_tokenizer(self,tokenizer,language):
        """Adds a new tokenizer to kitconc resources
        :param tokenizer: a trained tokenizer
        :type tokenizer: object
        :param language: name of language
        :type language: str 
        :return: True or False
        :rtype: boolean
        """
        flag = False 
        try:
            data_path = self.__path + '/data/word_tokenizer_' + language + '.pickle'
            with open (data_path,'wb') as fh:
                pickle.dump(tokenizer,fh)
            flag = True
        except:
            flag = None
        return flag  
        
    def add_tagger(self,tagger,language):
        """Adds a new tagger to kitconc resources
        :param tagger: a trained tagger
        :type tagger: object
        :param language: name of language
        :type language: str 
        :return: True or False
        :rtype: boolean
        """
        flag = False 
        try:
            data_path = self.__path + '/data/pos_tagger_' + language + '.pickle'
            with open (data_path,'wb') as fh:
                pickle.dump(tagger,fh)
            flag = True
        except:
            flag = None
        return flag
    
    def add_reflist(self,reflist,language):
        """Adds a new reflist to kitconc resources
        :param reflist: a reference list
        :type reflist: str
        :param language: name of language
        :type language: str 
        :return: True or False
        :rtype: boolean
        """
        flag = False 
        try:
            data_path = self.__path + '/data/reflist_' + language + '.tab'
            with open (data_path,'w') as f:
                f.write(reflist)
            flag = True
        except:
            flag = None
        return flag
    
    def add_stoplist(self,stoplist,language):
        """Adds a new stoplist to kitconc resources
        :param stoplist: a stoplist
        :type stoplist: str
        :param language: name of language
        :type language: str 
        :return: True or False
        :rtype: boolean
        """
        flag = False 
        try:
            data_path = self.__path + '/data/stoplist_' + language + '.tab'
            with open (data_path,'w') as f:
                f.write(stoplist)
            flag = True
        except:
            flag = None
        return flag
    
    def load_sent_tokenizer(self,language='portuguese'):
        """Returns a stored sentence tokenizer from the data folder according to the specified language.
        :param language: name of language
        :type language: str 
        :return: sentence tokenizer
        :rtype: object
        """
        # load sent_tokenizer
        sent_tokenizer = None
        tokenizer_path = self.__path + '/data/sent_tokenizer_' + language + '.pickle'
        with open(tokenizer_path, 'rb') as fh:
            sent_tokenizer = pickle.load(fh)
        return sent_tokenizer
    
    def load_tokenizer(self,language='portuguese'):
        """Returns a stored word tokenizer from the data folder according to the specified language.
        :param language: name of language
        :type language: str 
        :return: tokenizer
        :rtype: object
        """
        # load tokenizer
        tokenizer = None
        tokenizer_path = self.__path + '/data/word_tokenizer_' + language + '.pickle'
        with open(tokenizer_path, 'rb') as fh:
            tokenizer = pickle.load(fh)
        return tokenizer
    
    def load_tagger(self,language='portuguese'):
        """Returns a stored tagger from the data folder according to the specified language.
        :param language: name of language
        :type language: str 
        :return: tagger
        :rtype: object
        """
        # load tagger
        tagger = None 
        tagger_path = self.__path + '/data/pos_tagger_' + language  + '.pickle'
        with open(tagger_path, 'rb') as fh:
            tagger = pickle.load(fh)
        return tagger
    
    def load_reflist(self,language='portuguese'):
        """Returns a stored reference list from the data folder according to the specified language.
        :param language: name of language
        :type language: str 
        :return: reference list
        :rtype: list
        """
        # load tagger
        reflist = [] 
        ref_path = self.__path + '/data/reflist_' + language  + '.tab'
        with open(ref_path, 'r',encoding='utf-8') as fh:
            for line in fh:
                if len(line.strip())!=0:
                    f = line.strip().split('\t')
                    if len(f) >=2:
                        reflist.append((f[0],f[1]))
        return reflist
    
    def load_stoplist(self,language='portuguese'):
        """Returns a stored stoplist from the data folder according to the specified language.
        :param language: name of language
        :type language: str 
        :return: stoplist
        :rtype: object
        """
        # load tagger
        stoplist = [] 
        stop_path = self.__path + '/data/stoplist_' + language  + '.tab'
        with open(stop_path, 'r',encoding='utf-8') as fh:
            for line in fh:
                if len(line.strip())!=0:
                    stoplist.append(line.strip())
        return stoplist           

 

