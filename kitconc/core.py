# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
import os  
import pickle
import requests, zipfile, io 

    
    
class Examples(object):
    
    def __init__(self):
        self.__path = os.path.dirname(os.path.abspath(__file__))
    
    def download(self,**kwargs):
        """Downloads code examples and resources from kitconc github repository:
        https://github.com/ilexistools/kitconc-examples/archive/master.zip
        
        Parameters
        ----------
        
        - dest_path : str
        A string path where examples must be stored. 
        
        - show_progress : boolean
        Prints a progress message if value is True.
        
        Returns
        -------
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
    
    def __init__(self):
        self.__path = os.path.dirname(os.path.abspath(__file__)) 
    
    def get_data_path(self):
        """Returns kitconc data path"""
        return self.__path + '/data/'
    
    def list_data_files(self):
        """Returns a list of files from kitconc data path"""
        files = os.listdir(self.get_data_path())
        return files 
        
    def add_tokenizer(self,tokenizer,language):
        """Adds a new tokenizer to kitconc resources"""
        flag = False 
        try:
            data_path = self.__path + '/data/tokenizer_' + language + '.pickle'
            with open (data_path,'wb') as fh:
                pickle.dump(tokenizer,fh)
            flag = True
        except:
            flag = None
        return flag  
        
    def add_tagger(self,tagger,language):
        """Adds a new tagger to kitconc resources"""
        flag = False 
        try:
            data_path = self.__path + '/data/tagger_' + language + '.pickle'
            with open (data_path,'wb') as fh:
                pickle.dump(tagger,fh)
            flag = True
        except:
            flag = None
        return flag
    
    def add_reflist(self,reflist,language):
        """Adds a new reflist to kitconc resources"""
        flag = False 
        try:
            data_path = self.__path + '/data/reflist_' + language + '.tab'
            with open (data_path,'w') as f:
                f.write(reflist)
            flag = True
        except:
            flag = None
        return flag

class Resources(object):
    
    def __init__(self):
        self.__path = os.path.dirname(os.path.abspath(__file__)) 
    
    def load_sent_tokenizer(self,language='portuguese'):
        """Returns a stored tokenizer from the data folder according to the specified language."""
        # load tokenizer
        tokenizer = None
        tokenizer_path = self.__path + '/data/tokenizer_' + language + '.pickle'
        with open(tokenizer_path, 'rb') as fh:
            tokenizer = pickle.load(fh)
        return tokenizer
    
    
    def load_tagger(self,language='portuguese'):
        """Returns a stored tagger from the data folder according to the specified language."""
        # load tagger
        tagger = None 
        tagger_path = self.__path + '/data/tagger_' + language  + '.pickle'
        with open(tagger_path, 'rb') as fh:
            tagger = pickle.load(fh)
        return tagger
    
    def train_tagger(self,tagged_sents,**kwargs):
        """Trains a tagger"""
        show_progress = kwargs.get('show_progress',True)
    


 

