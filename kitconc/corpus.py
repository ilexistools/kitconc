# -*- coding: utf-8 -*-
import os
import re
import nltk
import pickle
import pandas as pd
from collections import Counter
from collections import deque  
from collections import OrderedDict
from kitconc.wordlist import Wordlist
from kitconc.keywords import Keywords
from kitconc.wtfreq import WTfreq
from kitconc.wfreqinfiles import Wfreqinfiles
from kitconc.kwic import Kwic
from kitconc.collocates import Collocates
from kitconc.ngrams import Ngrams
from kitconc.clusters import Clusters
from kitconc.dispersion import Dispersion
from kitconc.keywords_dispersion import KeywordsDispersion
from kitconc.keynessxrange import Keynessxrange
from kitconc import utils  

class Corpus (object):
    """This class is the main component for doing corpus analysis in Kitconc."""

    #Useful constants here: 
    LOG_LIKELIHOOD = 'log-likelihood'
    CHI_SQUARE = 'chi square'
    MUTUAL_INFORMATION = 'mutual information'
    TSCORE = 'tscore'
    
    # tagging format
    TREE_TAGGER_FORMAT = 'treetagger'
    TAB_SEPARATED_FORMAT = 'tab'
    
    def __init__(self,workspace,corpus_name,language='english',encoding='utf-8'):
        """
        All needed functions for text processing are accessed through this object. 
        
        Parameters
        ----------
        
        - workspace : str
        A folder path where the corpus will be stored.
        Different corpora can have the same workspace.
        
        - corpus_name: str
        A name for corpus identification.
        
        - language : str
        The language for text processing.
        
        - encoding : str
        The enconding for input texts.
        
        Returns
        -------
        Corpus object
        """
        self.__path = os.path.dirname(os.path.abspath(__file__))
        if str(workspace).endswith('/'):
            self.workspace = workspace
        else:
            self.workspace = workspace + '/'
        self.corpus_name = corpus_name
        self.language = language 
        self.encoding = encoding
        self.output_path = self.workspace + self.corpus_name + '/output/'
    
    
    #-----------------------------------------------------------------------------------------------------
    # ADD TEXTS
    #-----------------------------------------------------------------------------------------------------
    
    def add_texts(self,source_folder,**kwargs):
        """
        Adds texts to the corpus.
        Texts are tagged and saved in a corpus folder for analysis.
        
        Parameters
        ----------
        
        - souce_folder : str
        A string path where texts for processing are stored. 
        
        - show_progress : boolean
        Prints a progress message if value is True.
        
        Returns
        -------
        None
        """
        # args
        show_progress=kwargs.get('show_progress',False)
        # create all folders for the new corpus
        if not os.path.exists(self.workspace + self.corpus_name):
            os.mkdir(self.workspace + self.corpus_name)
        if not os.path.exists(self.workspace + self.corpus_name + '/tagged'):
            os.mkdir(self.workspace + self.corpus_name + '/tagged')
        if not os.path.exists(self.workspace + self.corpus_name + '/output'):
            os.mkdir(self.workspace + self.corpus_name + '/output')
        # load tokenizer
        tokenizer_path = self.__path + '/data/tokenizer_' + self.language + '.pickle'
        with open(tokenizer_path, 'rb') as fh:
            tokenizer = pickle.load(fh)
        # load tagger
        tagger_path = self.__path + '/data/tagger_' + self.language  + '.pickle'
        with open(tagger_path, 'rb') as fh:
            tagger = pickle.load(fh)
        # get files
        files = os.listdir(source_folder)
        total_files = len(files)
        i = 0
        # tag other languages 
        for filename in sorted(files):
            i +=1
            tagged_sents = []
            f = open(source_folder + "/" + filename,'r',encoding=self.encoding)
            sents = tokenizer.tokenize(f.read())
            f.close()
            for sent in sents:
                str_sent = []
                for token in tagger.tag(nltk.tokenize.word_tokenize(sent, language=self.language)):
                    if token == ('/','/'): # this is a temporary fix for slash problems
                        token = ('/','|')  # 
                    str_sent.append(nltk.tuple2str(token))
                tagged_sents.append(' '.join(str_sent))
                    
            with open(self.workspace + self.corpus_name + "/tagged/" + filename ,'w',encoding=self.encoding) as fh:
                fh.write('\n'.join(tagged_sents))
            if show_progress == True:
                print("{1}% ..... {0} ".format (filename, round((i/float(total_files)) * 100)) )
        # set corpus info
        corpus_info = {}
        corpus_info['workspace'] = self.workspace
        corpus_info['corpus_name'] = self.corpus_name
        corpus_info['language'] = self.language
        corpus_info['encoding'] = self.encoding
        # save corpus info 
        fh = open(self.workspace + self.corpus_name + '/info.pickle','wb')
        pickle.dump(corpus_info,fh)
        fh.close()

    
    #-----------------------------------------------------------------------------------------------------
    # ADD FROM TAGGED TEXTS
    #-----------------------------------------------------------------------------------------------------

    
    def add_tagged_texts(self,source_folder,**kwargs):
        """
        Adds tagged texts to the corpus.
        Tagged texts are saved in a corpus folder for analysis.
        
        Parameters
        ----------
        
        - souce_folder : str
        A string path where tagged texts are stored.
        
        - tagging_format : str
        A tagged text file format.
        
        - sentence_breakers : list 
        A list of chars for breaking sentences.
        
        - show_progress : boolean
        Prints a progress message if value is True.
        
        Returns
        -------
        None
        """
        # args
        show_progress=kwargs.get('show_progress',False)
        tagging_format = kwargs.get('tagging_format','tab')
        sentence_breakers = kwargs.get('sentence_breakers',['.','?',';','!'])
        # create all folders for the new corpus
        if not os.path.exists(self.workspace + self.corpus_name):
            os.mkdir(self.workspace + self.corpus_name)
        if not os.path.exists(self.workspace + self.corpus_name + '/tagged'):
            os.mkdir(self.workspace + self.corpus_name + '/tagged')
        if not os.path.exists(self.workspace + self.corpus_name + '/output'):
            os.mkdir(self.workspace + self.corpus_name + '/output')
        # get files
        if tagging_format == 'treetagger':
            self.__tree_tagger(source_folder, sentence_breakers, show_progress)
        elif tagging_format == 'tab':
            self.__tab(source_folder, sentence_breakers, show_progress)
        else:
            self.__tab(source_folder, sentence_breakers, show_progress)
            
        # set corpus info
        corpus_info = {}
        corpus_info['workspace'] = self.workspace
        corpus_info['corpus_name'] = self.corpus_name
        corpus_info['language'] = self.language
        corpus_info['encoding'] = self.encoding
        # save corpus info 
        fh = open(self.workspace + self.corpus_name + '/info.pickle','wb')
        pickle.dump(corpus_info,fh)
        fh.close()
        
        
    def __tree_tagger(self,source_folder,sentence_breakers,show_progress):
        files = os.listdir(source_folder)
        total_files = len(files)
        i = 0
        for filename in sorted(files):
            i +=1
            tagged_sents = []
            with open(source_folder + '/' + filename,'r') as fh:
                tagged_sent = []
                for line in fh:
                    if len(line.strip()) != 0:
                        wtl = line.strip().split('\t')
                        wt =  nltk.tuple2str((wtl[0],wtl[1]))
                        tagged_sent.append(wt)
                        if wtl[0] in sentence_breakers:
                            tagged_sents.append(' '.join(tagged_sent))
                            tagged_sent = []
            with open(self.workspace + self.corpus_name + "/tagged/" + filename ,'w',encoding=self.encoding) as fh:
                fh.write('\n'.join(tagged_sents))  
            if show_progress == True:
                print("{1}% ..... {0} ".format (filename, round((i/float(total_files)) * 100)) )
    
    def __tab(self,source_folder,sentence_breakers,show_progress):
        files = os.listdir(source_folder)
        total_files = len(files)
        i = 0
        for filename in sorted(files):
            i +=1
            tagged_sents = []
            with open(source_folder + '/' + filename,'r') as fh:
                tagged_sent = []
                for line in fh:
                    if len(line.strip()) != 0:
                        wtl = line.strip().split('\t')
                        wt =  nltk.tuple2str((wtl[0],wtl[1]))
                        tagged_sent.append(wt)
                        if wtl[0] in sentence_breakers:
                            tagged_sents.append(' '.join(tagged_sent))
                            tagged_sent = []
            with open(self.workspace + self.corpus_name + "/tagged/" + filename ,'w',encoding=self.encoding) as fh:
                fh.write('\n'.join(tagged_sents))  
            if show_progress == True:
                print("{1}% ..... {0} ".format (filename, round((i/float(total_files)) * 100)) )

    
    #-----------------------------------------------------------------------------------------------------
    # JOIN TAGGED WORDS
    #-----------------------------------------------------------------------------------------------------
    
    def merge_tagged_tokens(self,merge_rules,**kwargs):
        """
        Merges tagged tokens in a corpus.
        
        Parameters
        ---------- 
        
        - merge_rules : list of tuples 
        - show_progress : boolean
        Prints a progress message if value is True.
        
        Returns
        -------
        None
        
        """
        #args
        show_progress=kwargs.get('show_progress',False)
        # fix args
        # create a dictionary from merge rules
        dic = {}
        for item in merge_rules:
            if len(item) >= 3:
                k = (item[0] + item[1]) 
                if  k not in dic:
                    dic[k] = item[2]
        
        print(dic)
        input('')
        # set required paths
        tagged_path = self.workspace + self.corpus_name + "/tagged"
        # get corpus files in a list 
        files = os.listdir(tagged_path)
        total_files = len(files)
        # loop
        d = deque(maxlen=2)
        i = 0 
        for filename in files:
            replace_rules = {}
            with open(tagged_path + '/' +filename,'r',encoding=self.encoding) as fh:
                for line in fh:
                    if len(line.strip()) != 0:
                        tokens = line.strip().split(' ')
                        for token in tokens:
                            wt = nltk.str2tuple(token)
                            if len(wt) >= 2:
                                d.append(wt)
                            if len(d) == 2:
                                st = (d[0][0]+d[1][0])
                                if st in dic:
                                    a = ' ' + d[0][0] + '/' + d[0][1] + ' ' + d[1][0] + '/' + d[1][1] + ' '
                                    b = ' ' + dic[st] + '/' + d[0][1] + '+' + d[1][1] + ' '
                                    if a not in replace_rules:
                                        replace_rules[a] = b
            
            # replace in file
            if len(replace_rules) != 0:
                    
                f = open(tagged_path + '/' +filename,'r',encoding=self.encoding)
                contents = f.read()
                f.close()
                
                
                for k in replace_rules:
                    contents = contents.replace(k,replace_rules[k])
                
                f = open(tagged_path + '/' +filename,'w',encoding=self.encoding)
                f.write(contents)
                f.close()
                
            # print progress
            if show_progress == True:
                i+=1
                print("{1}% ..... {0} ".format (filename, round((i/float(total_files)) * 100)) )
                
        d = None
        dic = None
        merge_rules = None
        
        for k in replace_rules:
            print(k,replace_rules[k])
         
    
    #-----------------------------------------------------------------------------------------------------
    # WORDLIST
    #-----------------------------------------------------------------------------------------------------
    
    def wordlist(self,**kwargs):
        """
        Generates a frequency word list based on text files. 
        
        Parameters
        ----------
        
        - lowercase: boolean
        Letters are converted or not to lowercase.
        
        - show_progress : boolean
        Prints a progress message if value is True.
        
        Returns
        -------
        Wordlist object
        """
        #args
        show_progress=kwargs.get('show_progress',False)
        lowercase = kwargs.get('lowercase',True)
        # set required paths
        tagged_path = self.workspace + self.corpus_name + "/tagged"
        # get corpus files in a list 
        files = os.listdir(tagged_path)
        total_files = len(files)
        # loop through files
        ptn = re.compile("\W+")
        i = 0
        number_of_tokens = 0
        hapax = 0
        counter = Counter()
        for filename in files:
            with open(tagged_path + '/' +filename,'r',encoding=self.encoding) as fh:
                for line in fh:
                    if len(line.strip()) != 0:
                        tokens = line.strip().split(' ')
                        for token in tokens:
                            wt = nltk.str2tuple(token)
                            if len(wt) >= 2:
                                if len(re.findall(ptn, wt[0])) == 0:
                                    number_of_tokens+=1
                                    if lowercase == True:
                                        counter[wt[0].lower()]+=1
                                    else:
                                        counter[wt[0]]+=1
            # print progress
            if show_progress == True:
                i+=1
                print("{1}% ..... {0} ".format (filename, round((i/float(total_files)) * 100)) )
        # calc types and type token ratio
        number_of_types = len(counter)
        typetoken = round((number_of_types / float(number_of_tokens))*100,2)
        # filter only words
        i = 0
        wordlist = []
        wordlist.append("N\tWORD\tFREQUENCY\t%")
        for kv in counter.most_common():
            i+=1
            p = round((kv[1] / float(number_of_tokens)) * 100,2) 
            wordlist.append(str(i) + '\t' + kv[0] + '\t' + str(kv[1]) + '\t' + str(p))
            if kv[1] == 1:
                hapax+=1
        counter = None
        wlst = Wordlist(tokens=number_of_tokens,types=number_of_types,typetoken=typetoken, hapax=hapax)
        wlst.read_str('\n'.join(wordlist))
        return  wlst  
    
    #-----------------------------------------------------------------------------------------------------
    # KEYWORDS
    #-----------------------------------------------------------------------------------------------------
    
    def keywords(self,wordlist,**kwargs):
        """
        Generates key words based on corpus text files.
        It compares the input wordlist with a reference wordlist according to the language set.
        
        Parameters
        ----------
        
        - wordlist : Wordlist object
        A wordlist generated based on corpus text files.
        
        - measure : string
        A statistical measure to use (log-likelihood or chi square).
        
        - show_progress : boolean
        Prints a progress message if value is True.
        
        Returns
        -------
        Keywords object
        """
        #args
        measure = kwargs.get('measure','log-likelihood')
        show_progress=kwargs.get('show_progress',False)
        stat = 1
        
        # get statistics measures
        if measure == 'log-likelihood':
            stat = 1
        elif measure == 'chi square':
            stat = 2
        
        # make reflist dictionary
        reftable = pd.read_table(self.__path + '/data/reflist_' + self.language + '.tab')
        reflist = {}
        tk_refc = 0
        for row in reftable.itertuples(index=False):
            if row[1] not in reflist:
                reflist[row[1]] = int(row[2])
                tk_refc+=int(row[2])
        reftable = None
        
        # extract keywords
        wfreq = {}
        counter = Counter()
        tk_stdc = wordlist.tokens 
        i = 0
        total = len(wordlist.df)
        for row in wordlist.df.itertuples(index=False):
            wfreq[str(row[1])] = int(row[2])
            freq_refc = 0
            if str(row[1]) in reflist:
                freq_refc = reflist[str(row[1])]
            if stat == 1:
                keyness = utils.ll(int(row[2]),freq_refc,tk_stdc,tk_refc)
            elif stat == 2:
                keyness = utils.chi_square (int(row[2]),freq_refc,tk_stdc,tk_refc)
                
                
            if str(row[1]) not in counter:
                counter[str(row[1])] = keyness
            # print progress
            if show_progress == True:
                i+=1
                print("{1}% ..... {0} ".format (row[1], round((i/float(total)) * 100)) )
        reflist = None
        wordlist = None
        
        # make keywords table
        keywords = [] 
        keywords.append('N\tWORD\tFREQUENCY\tKEYNESS')
        i = 0
        for kv in counter.most_common():
            i+=1
            keywords.append(str(i) + '\t' + kv[0] + '\t' + str(wfreq[kv[0]])  +  '\t' + str(kv[1]))
        
        kwlst = Keywords()
        kwlst.read_str('\n'.join(keywords))
        keywords = None 
        return kwlst
    
    #-----------------------------------------------------------------------------------------------------
    # WORD TAG FREQUENCY
    #-----------------------------------------------------------------------------------------------------
    
    def wtfreq(self,**kwargs):
        """
        Generates a word tag frequency list based on corpus text files.
        
        Parameters
        ----------
        - lowercase: boolean
        Letters are converted or not to lowercase.
        
        - show_progress : boolean
        Prints a progress message if value is True.
        
        Returns
        -------
        WTfreq object
        """
        #args
        lowercase = kwargs.get('lowercase',True)
        show_progress=kwargs.get('show_progress',False)
        # get corpus files in a list 
        tagged_path = self.workspace + self.corpus_name + '/tagged' 
        files = os.listdir(tagged_path)
        total_files = len(files)
        # loop through files
        ptn = re.compile("\W+")
        i = 0
        number_of_tokens = 0
        counter = Counter()
        for filename in files:
            with open(tagged_path + '/' + filename,'r',encoding = self.encoding) as fh:
                for line in fh:
                    if len(line.strip()) != 0:
                        tokens = line.strip().split(' ')
                        for token in tokens:
                            wt = nltk.str2tuple(token)
                            if len(wt) >= 2:
                                if len(re.findall(ptn, wt[0])) == 0:
                                    number_of_tokens+=1
                                    if lowercase == True:
                                        counter[wt[0].lower() + '\t' + wt[1]]+=1
                                    else:
                                        counter[wt[0] + '\t' + wt[1]]+=1
            # print progress
            if show_progress == True:
                i+=1
                print("{1}% ..... {0} ".format (filename, round((i/float(total_files)) * 100)) )
        
        i = 0
        wtfreq = []
        wtfreq.append("N\tWORD\tTAG\tFREQUENCY\t%")
        for kv in counter.most_common():
            i+=1
            p = round((kv[1] / float(number_of_tokens)) * 100,2)
            wtfreq.append(str(i) + '\t' + kv[0] + '\t' + str(kv[1]) + '\t' + str(p) )
            
                
        counter = None
        
        wt = WTfreq()
        wt.read_str('\n'.join(wtfreq))
        wtfreq = None 
        return wt
    
    #-----------------------------------------------------------------------------------------------------
    # WORD FREQUENCY IN TEXT FILES
    #-----------------------------------------------------------------------------------------------------
    
    def wfreqinfiles(self,wordlist,**kwargs):
        #args
        lowercase= kwargs.get('lowercase',True)
        show_progress=kwargs.get('show_progress',False)
        # set required paths
        tagged_path = self.workspace + self.corpus_name + "/tagged/"
        # create a dictionary of words
        words = Counter()
        for row in wordlist.df.itertuples(index=False):
            words[row[1]] = 0
        wordlist = None
        # get corpus files in a list 
        files = os.listdir(tagged_path)
        total_files = len(files)
        # loop through files
        i = 0
        ptn = re.compile("\W+")
        for filename in files:
            counter = Counter()
            with open(tagged_path + '/' +filename,'r',encoding=self.encoding) as fh:
                for line in fh:
                    if len(line.strip()) != 0:
                        tokens = line.strip().split(' ')
                        for token in tokens:
                            wt = nltk.str2tuple(token)
                            if len(wt) >= 2:
                                if len(re.findall(ptn, wt[0])) == 0:
                                    if lowercase == True:
                                        if wt[0].lower() not in counter:
                                            counter[wt[0].lower()]=1
                                    else:
                                        if wt[0] not in counter:
                                            counter[wt[0]]=1
                                        
            for kv in counter.most_common():
                if kv[0] in words:
                    words[kv[0]]+=1
            counter = None
            # print progress
            if show_progress == True:
                i+=1
                print("{1}% ..... {0} ".format (filename, round((i/float(total_files)) * 100)) )
        
        # save table
        i = 0
        tb = []
        tb.append("N\tWORD\tRANGE\t%")
        for kv in words.most_common():
            i+=1
            p = round((kv[1] / float(total_files)) * 100,2)
            tb.append(str(i) + '\t' + str(kv[0]) + '\t' + str(kv[1]) + '\t' + str(p))
        
        words = None
        
        fif = Wfreqinfiles()
        fif.read_str('\n'.join(tb))
        
        return fif 
    
    #-----------------------------------------------------------------------------------------------------
    # CONCORDANCES
    #-----------------------------------------------------------------------------------------------------
    
    def kwic(self,node,**kwargs):
        """
        Generates concordance lines.
        
        Parameters
        ----------
        
        - node : str
        Search word or phrase (max. 4 words).
        
        - pos : str
        POS for word or phrase.
        
        - regex : boolean
        Use regular expression for search word matching.
        
        - horizon : int    
        Left and right horizon of words.
        
        - limit : int
        Number of concordance lines to return.
        
        - show_progress : boolean
        Prints a progress message if value is True.
        
        Returns
        -------
        Kwic object
        """
        # args
        pos = kwargs.get('pos',None)
        horizon = kwargs.get('horizon',12)
        limit = kwargs.get('limit',0)
        regex = kwargs.get('regex',False) 
        show_progress = kwargs.get('show_progress',False)
        # splits search word
        node = node.strip().split(' ')
        # checks pos for each search word
        if pos == None:
            pos = []
            for i in range(len(node)):
                pos.append(None)
        else:
            pos = pos.strip().split(' ')
        # sets the horizon size
        if horizon < 5:
            horizon = 5
        cols = horizon
        hfix = []
        for i in range(horizon):
            hfix.append((' '))
        # node and dq size 
        node_size = len(node)
        dq = deque(maxlen=node_size)
        # set required paths
        tagged_path = self.workspace + self.corpus_name + "/tagged/"
        # get corpus files in a list 
        files = os.listdir(tagged_path)
        total_files = len(files)
        # loop
        sorted(files)
        file_id = 0
        kwic_lines =[]
        kwic_lines.append('N\tLEFT\tNODE\tRIGHT\tFILENAME\tTOKEN_ID\tSENT_ID\tFILE_ID')
        i = 0
        j = 0
        for filename in files:
            file_id+=1
            sent_id = 0
            token_id = len(hfix)
            ids = []
            text = []
            text = hfix
            # search
            with open(tagged_path + '/' +filename,'r',encoding=self.encoding) as fh:
                for line in fh:
                    if len(line.strip()) != 0:
                        sent_id+=1
                        tokens = line.strip().split(' ')
                        if len(tokens) != 0:
                            for token in tokens:
                                if limit != 0 and len(ids) == limit:
                                    break 
                                token_id+=1
                                wt = nltk.str2tuple(token)
                                # add for text source
                                if len(wt) >= 2:
                                    text.append((wt[0]))
                                    # add for matching
                                    dq.append(wt)
                                    #try match
                                    flag_pos = False
                                    flag_node = False
                                    
                                    if len(dq) == node_size:
                                        # check node matching
                                        # wild char
                                        new_node = [None,None,None,None]
                                        # 1
                                        if node_size == 1:
                                            if node[0] == '*':
                                                new_node[0] = dq[0][0]
                                            else:
                                                new_node[0] = node[0].lower()
                                        # 2
                                        elif node_size == 2:
                                            if node[0] == '*':
                                                new_node[0] = dq[0][0]
                                            else:
                                                new_node[0] = node[0].lower()
                                            if node[1] == '*':
                                                new_node[1] = dq[1][0]
                                            else:
                                                new_node[1] = node[1].lower()
                                        # 3
                                        elif node_size == 3:
                                            if node[0] == '*':
                                                new_node[0] = dq[0][0]
                                            else:
                                                new_node[0] = node[0].lower()
                                            if node[1] == '*':
                                                new_node[1] = dq[1][0]
                                            else:
                                                new_node[1] = node[1].lower()
                                            if node[2] == '*':
                                                new_node[2] = dq[2][0]
                                            else:
                                                new_node[2] = node[2].lower()
                                        # 4
                                        elif node_size == 4:
                                            if node[0] == '*':
                                                new_node[0] = dq[0][0]
                                            else:
                                                new_node[0] = node[0].lower()
                                            if node[1] == '*':
                                                new_node[1] = dq[1][0]
                                            else:
                                                new_node[1] = node[1].lower()
                                            if node[2] == '*':
                                                new_node[2] = dq[2][0]
                                            else:
                                                new_node[2] = node[2].lower()
                                            if node[3] == '*':
                                                new_node[3] = dq[3][0]
                                            else:
                                                new_node[3] = node[3].lower()                                             
                                        # check node matching 
                                        # 1
                                        if node_size == 1:
                                            if regex == False:
                                                if dq[0][0].lower() == new_node[0].lower():
                                                    flag_node = True
                                            else:
                                                if len(re.findall(new_node[0],dq[0][0]))!= 0:
                                                    flag_node = True
                                        # 2
                                        elif node_size == 2:
                                            if regex == False:
                                                if dq[0][0].lower() == new_node[0].lower() and dq[1][0].lower() == new_node[1].lower():
                                                    flag_node = True
                                            else:
                                                if len(re.findall(new_node[0],dq[0][0]))!= 0 and len(re.findall(new_node[1],dq[1][0]))!= 0:
                                                    flag_node = True
                                                
                                        # 3
                                        elif node_size == 3:
                                            if regex == False:
                                                if dq[0][0].lower() == new_node[0].lower() and dq[1][0].lower() == new_node[1].lower() and dq[2][0].lower() == new_node[2].lower():
                                                    flag_node = True
                                            else:
                                                if len(re.findall(new_node[0],dq[0][0]))!= 0 and len(re.findall(new_node[1],dq[1][0]))!= 0 and len(re.findall(new_node[2],dq[2][0]))!= 0:
                                                    flag_node = True
                                        # 4
                                        elif node_size == 4:
                                            if regex == False:
                                                if dq[0][0].lower() == new_node[0].lower() and dq[1][0].lower() == new_node[1].lower() and dq[2][0].lower() == new_node[2].lower() and dq[3][0].lower() == new_node[3].lower():
                                                    flag_node = True
                                            else:
                                                if len(re.findall(new_node[0],dq[0][0]))!= 0 and len(re.findall(new_node[1],dq[1][0]))!= 0 and len(re.findall(new_node[2],dq[2][0]))!= 0 and len(re.findall(new_node[3],dq[3][0]))!= 0:
                                                    flag_node = True
                                        # check pos matching None
                                        if node_size == 1 and pos[0] == None:
                                            flag_pos = True
                                        elif node_size == 2 and pos == [None,None]:
                                            flag_pos = True
                                        elif node_size ==  3 and pos == [None,None,None]:
                                            flag_pos = True
                                        elif node_size == 4 and pos == [None,None,None,None]:
                                            flag_pos = True
                                        else:
                                            # check wild char
                                            new_pos = [None,None,None,None]
                                            # 1
                                            if node_size == 1:
                                                if pos[0] == '*':
                                                    new_pos[0] = dq[0][1]
                                                else:
                                                    new_pos[0] = pos[0] 
                                            # 2    
                                            elif node_size == 2:
                                                    if pos[0] == '*':
                                                        new_pos[0] = dq[0][1]
                                                    else:
                                                        new_pos[0] = pos[0]
                                                    if pos[1] == '*':
                                                        new_pos[1] = dq[1][1]
                                                    else:
                                                        new_pos[1] =pos[1]
                                            # 3 
                                            elif node_size == 3:
                                                    if pos[0] == '*':
                                                        new_pos[0] = dq[0][1]
                                                    else:
                                                        new_pos[0] = pos[0]
                                                    if pos[1] == '*':
                                                        new_pos[1] = dq[1][1]
                                                    else:
                                                        new_pos[1] = pos[1]
                                                    if pos[2] == '*':
                                                        new_pos[2] = dq[2][1]
                                                    else:
                                                        new_pos[2] = pos[2]
                                            # 4
                                            if node_size == 4:
                                                    if pos[0] == '*':
                                                        new_pos[0] = dq[0][1]
                                                    else:
                                                        new_pos[0] = pos[0]
                                                    if pos[1] == '*':
                                                        new_pos[1] = dq[1][1]
                                                    else:
                                                        new_pos[1] = pos[1]
                                                    if pos[2] == '*':
                                                        new_pos[2] = dq[2][1]
                                                    else:
                                                        new_pos[2] = pos[2]
                                                    if pos[3] == '*':
                                                        new_pos[3] = dq[3][1]
                                                    else:
                                                        new_pos[3] = pos[3]
                                                        
                                            # check pos matching not None    
                                            # 1
                                            if len(pos) == 1:
                                                if pos[0] != None and new_pos[0] == dq[0][1]:
                                                    flag_pos = True
                                            # 2
                                            elif len(pos) == 2:
                                                if pos[0] != None and new_pos[0] == dq[0][1] and new_pos[1] == dq[1][1]:
                                                    flag_pos = True
                                            # 3
                                            elif len(pos) == 3:
                                                if pos[0] != None and new_pos[0] == dq[0][1] and new_pos[1] == dq[1][1] and new_pos[2] == dq[2][1]:
                                                    flag_pos = True
                                            # 4
                                            elif len(pos) == 4:
                                                if pos[0] != None and new_pos[0] == dq[0][1] and new_pos[1] == dq[1][1] and new_pos[2] == dq[2][1] and new_pos[3] == dq[3][1]:
                                                    flag_pos = True     
                                            
                                    # add if matching   
                                    if flag_node == True and flag_pos == True:
                                        ids.append((token_id,sent_id,file_id))
            # make kwic
            if len(ids) != 0:
                for idx in ids:
                    j+=1
                    l = (idx[0]-(cols+node_size),idx[0]-node_size)
                    n = (idx[0]-node_size, (idx[0]-node_size)+ node_size)
                    r = (idx[0],idx[0]+cols)
                    kwic_lines.append ( str(j) + '\t' + ' '.join(  text[l[0]:l[1]]) + '\t' +  ' '.join(text[n[0]:n[1]]) + '\t' + ' '.join(text[r[0]:r[1]]) + '\t' + filename + '\t' + str(token_id) + '\t' + str(sent_id) + '\t' +str(file_id))
            
            # print progress
            if show_progress == True:
                i+=1
                print("{1}% ..... {0} ".format (filename, round((i/float(total_files)) * 100)) )
        
        files = None
        
        k = Kwic()
        k.read_str('\n'.join(kwic_lines))
        kwic_lines = None
        return k
    
    #-----------------------------------------------------------------------------------------------------
    # COLLOCATES
    #----------------------------------------------------------------------------------------------------- 
    
    def collocates(self,wordlist,node,**kwargs):
        #args
        left_span = kwargs.get('left_span',1)
        right_span = kwargs.get('right_span',1)
        coll_pos = kwargs.get('coll_pos',None)
        measure = kwargs.get('measure','tscore')
        pos = kwargs.get('pos',None)
        limit = kwargs.get('limit',0)
        regex = kwargs.get('regex',False) 
        show_progress = kwargs.get('show_progress',False)
        # make wordlist dictionary
        dic_wordlist = {}
        ntokens = wordlist.tokens 
        for row in wordlist.df.itertuples(index=False):
            dic_wordlist[str(row[1])]=int(row[2])
        wordlist = None
        # splits search word
        node = node.strip().split(' ')
        
        # checks pos for each search word
        if pos == None:
            pos = []
            for i in range(len(node)):
                pos.append(None)
        else:
            pos = pos.strip().split(' ')
        # check coll_pos
        if coll_pos != None:
            coll_pos = coll_pos.strip().split(' ')
        # sets the horizon size
        horizon = 5
        if horizon < 5:
            horizon = 5
        hfix = []
        for i in range(horizon):
            hfix.append((' '))
        # span sizes
        if left_span > 5:
            left_span = 5
        if right_span > 5:
            left_span = 5
        # stat
        if measure == 'tscore':
            stat = 1
        elif measure == 'mutual information':
            stat = 2
        # node and dq size 
        node_size = len(node)
        dq = deque(maxlen=node_size)
        # set required paths
        tagged_path = self.workspace + self.corpus_name + "/tagged/"
        # get corpus files in a list 
        files = os.listdir(tagged_path)
        total_files = len(files)
        # counters
        left_counter = Counter()
        right_counter = Counter()
        # loop
        sorted(files)
        file_id = 0
        total_matches = 0
        i = 0
        j = 0
        for filename in files:
            file_id+=1
            sent_id = 0
            token_id = len(hfix)
            ids = []
            text = []
            text = hfix
            text_tags = []
            text_tags = hfix.copy()  
            # search
            with open(tagged_path + '/' +filename,'r',encoding=self.encoding) as fh:
                for line in fh:
                    if len(line.strip()) != 0:
                        sent_id+=1
                        tokens = line.strip().split(' ')
                        if len(tokens) != 0:
                            for token in tokens:
                                token_id+=1
                                wt = nltk.str2tuple(token)
                                # add for text source
                                if len(wt) >= 2:
                                    text.append((wt[0]))
                                    if coll_pos != None and coll_pos != [None]:
                                        text_tags.append((wt[1]))
                                    # add for matching
                                    dq.append(wt)
                                    #try match
                                    flag_pos = False
                                    flag_node = False
                                    
                                    if len(dq) == node_size:
                                        # check node matching
                                        # wild char
                                        new_node = [None,None,None,None]
                                        # 1
                                        if node_size == 1:
                                            if node[0] == '*':
                                                new_node[0] = dq[0][0]
                                            else:
                                                new_node[0] = node[0].lower()
                                        # 2
                                        elif node_size == 2:
                                            if node[0] == '*':
                                                new_node[0] = dq[0][0]
                                            else:
                                                new_node[0] = node[0].lower()
                                            if node[1] == '*':
                                                new_node[1] = dq[1][0]
                                            else:
                                                new_node[1] = node[1].lower()
                                        # 3
                                        elif node_size == 3:
                                            if node[0] == '*':
                                                new_node[0] = dq[0][0]
                                            else:
                                                new_node[0] = node[0].lower()
                                            if node[1] == '*':
                                                new_node[1] = dq[1][0]
                                            else:
                                                new_node[1] = node[1].lower()
                                            if node[2] == '*':
                                                new_node[2] = dq[2][0]
                                            else:
                                                new_node[2] = node[2].lower()
                                        # 4
                                        elif node_size == 4:
                                            if node[0] == '*':
                                                new_node[0] = dq[0][0]
                                            else:
                                                new_node[0] = node[0].lower()
                                            if node[1] == '*':
                                                new_node[1] = dq[1][0]
                                            else:
                                                new_node[1] = node[1].lower()
                                            if node[2] == '*':
                                                new_node[2] = dq[2][0]
                                            else:
                                                new_node[2] = node[2].lower()
                                            if node[3] == '*':
                                                new_node[3] = dq[3][0]
                                            else:
                                                new_node[3] = node[3].lower()                                             
                                        # check node matching 
                                        # 1
                                        if node_size == 1:
                                            if regex == False:
                                                if dq[0][0].lower() == new_node[0].lower():
                                                    flag_node = True
                                            else:
                                                if len(re.findall(new_node[0],dq[0][0]))!= 0:
                                                    flag_node = True
                                        # 2
                                        elif node_size == 2:
                                            if regex == False:
                                                if dq[0][0].lower() == new_node[0].lower() and dq[1][0].lower() == new_node[1].lower():
                                                    flag_node = True
                                            else:
                                                if len(re.findall(new_node[0],dq[0][0]))!= 0 and len(re.findall(new_node[1],dq[1][0]))!= 0:
                                                    flag_node = True
                                                
                                        # 3
                                        elif node_size == 3:
                                            if regex == False:
                                                if dq[0][0].lower() == new_node[0].lower() and dq[1][0].lower() == new_node[1].lower() and dq[2][0].lower() == new_node[2].lower():
                                                    flag_node = True
                                            else:
                                                if len(re.findall(new_node[0],dq[0][0]))!= 0 and len(re.findall(new_node[1],dq[1][0]))!= 0 and len(re.findall(new_node[2],dq[2][0]))!= 0:
                                                    flag_node = True
                                        # 4
                                        elif node_size == 4:
                                            if regex == False:
                                                if dq[0][0].lower() == new_node[0].lower() and dq[1][0].lower() == new_node[1].lower() and dq[2][0].lower() == new_node[2].lower() and dq[3][0].lower() == new_node[3].lower():
                                                    flag_node = True
                                            else:
                                                if len(re.findall(new_node[0],dq[0][0]))!= 0 and len(re.findall(new_node[1],dq[1][0]))!= 0 and len(re.findall(new_node[2],dq[2][0]))!= 0 and len(re.findall(new_node[3],dq[3][0]))!= 0:
                                                    flag_node = True
                                        # check pos matching None
                                        if node_size == 1 and pos[0] == None:
                                            flag_pos = True
                                        elif node_size == 2 and pos == [None,None]:
                                            flag_pos = True
                                        elif node_size ==  3 and pos == [None,None,None]:
                                            flag_pos = True
                                        elif node_size == 4 and pos == [None,None,None,None]:
                                            flag_pos = True
                                        else:
                                            # check wild char
                                            new_pos = [None,None,None,None]
                                            # 1
                                            if node_size == 1:
                                                if pos[0] == '*':
                                                    new_pos[0] = dq[0][1]
                                                else:
                                                    new_pos[0] = pos[0] 
                                            # 2    
                                            elif node_size == 2:
                                                    if pos[0] == '*':
                                                        new_pos[0] = dq[0][1]
                                                    else:
                                                        new_pos[0] = pos[0]
                                                    if pos[1] == '*':
                                                        new_pos[1] = dq[1][1]
                                                    else:
                                                        new_pos[1] =pos[1]
                                            # 3 
                                            elif node_size == 3:
                                                    if pos[0] == '*':
                                                        new_pos[0] = dq[0][1]
                                                    else:
                                                        new_pos[0] = pos[0]
                                                    if pos[1] == '*':
                                                        new_pos[1] = dq[1][1]
                                                    else:
                                                        new_pos[1] = pos[1]
                                                    if pos[2] == '*':
                                                        new_pos[2] = dq[2][1]
                                                    else:
                                                        new_pos[2] = pos[2]
                                            # 4
                                            if node_size == 4:
                                                    if pos[0] == '*':
                                                        new_pos[0] = dq[0][1]
                                                    else:
                                                        new_pos[0] = pos[0]
                                                    if pos[1] == '*':
                                                        new_pos[1] = dq[1][1]
                                                    else:
                                                        new_pos[1] = pos[1]
                                                    if pos[2] == '*':
                                                        new_pos[2] = dq[2][1]
                                                    else:
                                                        new_pos[2] = pos[2]
                                                    if pos[3] == '*':
                                                        new_pos[3] = dq[3][1]
                                                    else:
                                                        new_pos[3] = pos[3]
                                                        
                                            # check pos matching not None    
                                            # 1
                                            if len(pos) == 1:
                                                if pos[0] != None and new_pos[0] == dq[0][1]:
                                                    flag_pos = True
                                            # 2
                                            elif len(pos) == 2:
                                                if pos[0] != None and new_pos[0] == dq[0][1] and new_pos[1] == dq[1][1]:
                                                    flag_pos = True
                                            # 3
                                            elif len(pos) == 3:
                                                if pos[0] != None and new_pos[0] == dq[0][1] and new_pos[1] == dq[1][1] and new_pos[2] == dq[2][1]:
                                                    flag_pos = True
                                            # 4
                                            elif len(pos) == 4:
                                                if pos[0] != None and new_pos[0] == dq[0][1] and new_pos[1] == dq[1][1] and new_pos[2] == dq[2][1] and new_pos[3] == dq[3][1]:
                                                    flag_pos = True     
                                            
                                    # add if matching   
                                    if flag_node == True and flag_pos == True:
                                        ids.append((token_id,sent_id,file_id))
                                        total_matches+=1
            # count collocates
            if coll_pos == None or coll_pos == [None]:
                if len(ids) != 0:
                    
                    for idx in ids:
                        j+=1
                        l = (idx[0]-(left_span+node_size),idx[0]-node_size)
                        r = (idx[0],idx[0]+right_span)
                        
                        if len(l) != 0:
                            for w in text[l[0]:l[1]]:
                                left_counter[w.lower()]+=1
                                
                                
                        if len(r) != 0:    
                            for w in text[r[0]:r[1]]:
                                right_counter[w.lower()]+=1
            else: # use coll_pos filter
                if len(ids) != 0:
                    for idx in ids:
                        j+=1
                        l = (idx[0]-(left_span+node_size),idx[0]-node_size)
                        r = (idx[0],idx[0]+right_span)
                        
                        if len(l) != 0:
                            arrText = text[l[0]:l[1]]
                            arrTags = text_tags[l[0]:l[1]]
                            for arri in range(0,len(arrText)):
                                if arrTags[arri] in coll_pos:
                                    left_counter[arrText[arri].lower()]+=1
                                    
                        if len(r) != 0:    
                            arrText = text[r[0]:r[1]]
                            arrTags = text_tags[r[0]:r[1]]
                            for arri in range(0,len(arrText)):
                                if arrTags[arri] in coll_pos:
                                    right_counter[arrText[arri].lower()]+=1
                
            
                    
            # print progress
            if show_progress == True:
                i+=1
                print("{1}% ..... {0} ".format (filename, round((i/float(total_files)) * 100)) )
        
        files = None
        
        # association measure
        # get only collocates frequency from wordlist
        wfreq = {}
        for k in left_counter.most_common():
            if k[0] in dic_wordlist:
                if k[0] not in wfreq:
                    wfreq[k[0]] = dic_wordlist[k[0]]
        for k in right_counter.most_common():
            if k[0] in dic_wordlist:
                if k[0] not in wfreq:
                    wfreq[k[0]] = dic_wordlist[k[0]]
        dic_wordlist = None
        # calculate association measure
        collocates = Counter()
        for k in wfreq:
            lfreq = 0
            rfreq = 0
            if k in left_counter:
                lfreq = left_counter[k]
            if k in right_counter:
                rfreq = right_counter[k]
            total = lfreq + rfreq
            
            if stat == 1:
                m = utils.tscore(total, total_matches, wfreq[k], ntokens, 1)
            elif stat == 2:
                m = utils.mutual_information(total, total_matches, wfreq[k], ntokens, 1)
            
            collocates [(k,str(total),str(lfreq),str(rfreq))] = m 
            #print (k,wfreq[k],lfreq,rfreq,total, m)
            #input('')
        wfreq = None
        left_counter = None
        right_counter = None
        # make table
        tb = []
        tb.append('N\tWORD\tFREQUENCY\tLEFT\tRIGHT\tASSOCIATION')
        i = 0
        for kv in collocates.most_common():
            i+=1
            tb.append(str(i) + '\t' + kv[0][0] + '\t' + kv[0][1] + '\t' + kv[0][2] + '\t' + kv[0][3] + '\t' + str(kv[1]))
            if limit != 0:
                if i >= limit:
                    break
            
        collocates = None
        # save
        coll = Collocates()
        coll.read_str('\n'.join(tb))
        tb = None
        
        
        return coll
    
    #-----------------------------------------------------------------------------------------------------
    # N-GRAMS
    #-----------------------------------------------------------------------------------------------------    
    
    def ngrams(self,**kwargs):
        #args
        size = kwargs.get('size',3)
        lowercase = kwargs.get('lowercase',True)
        min_freq = kwargs.get('min_freq',1)
        min_range = kwargs.get('min_range',1)
        tag1 = kwargs.get('tag1',[None])
        tag2 = kwargs.get('tag2',[None])
        tag3 = kwargs.get('tag3',[None])
        tag4 = kwargs.get('tag4',[None])
        show_progress=kwargs.get('show_progress',False)
        # check tags
        if tag1 != [None]:
            tag1 = tag1.strip().split(' ')
        if tag2 != [None]:
            tag2 = tag2.strip().split(' ')
        if tag3 != [None]:
            tag3 = tag3.strip().split(' ')
        if tag4 != [None]:
            tag4 = tag4.strip().split(' ')
        # do not allow size greater than 4 
        # or equalt to 0
        if size > 4:
            size = 4
        if size == 0:
            size = 3
        # set required paths
        tagged_path = self.workspace + self.corpus_name + "/tagged"
        # get corpus files in a list 
        files = os.listdir(tagged_path)
        total_files = len(files)
        # loop through files
        dq = deque(maxlen=size)
        dqtag = deque(maxlen=size)
        ptn = re.compile("\W+")
        i = 0
        counter = Counter()
        range_counter = Counter()
        for filename in files:
            temp_counter = Counter()
            with open(tagged_path + '/' +filename,'r',encoding=self.encoding) as fh:
                for line in fh:
                    if len(line.strip()) != 0:
                        tokens = line.strip().split(' ')
                        for token in tokens:
                            wt = nltk.str2tuple(token)
                            if len(wt) >= 2:
                                if len(re.findall(ptn, wt[0])) == 0:
                                    dq.append(wt[0])
                                    dqtag.append(wt[1])
                                    # tag filter
                                    flag = True
                                    if len(dq) >= size:
                                        if size == 1:
                                            if tag1 != [None] and dqtag[0] not in tag1:
                                                flag = False
                                        elif size == 2:
                                            if (tag1 != [None] and dqtag[0] not in tag1) or (tag2 != [None] and dqtag[1] not in tag2):
                                                flag = False
                                        elif size == 3:
                                            if (tag1 != [None] and dqtag[0] not in tag1) or (tag2 != [None] and dqtag[1] not in tag2) or (tag3 != [None] and dqtag[2] not in tag3):
                                                flag = False
                                        elif size == 4:
                                            if (tag1 != [None] and dqtag[0] not in tag1) or (tag2 != [None] and dqtag[1] not in tag2) or (tag3 != [None] and dqtag[2] not in tag3) or (tag4 != [None] and dqtag[3] not in tag4):
                                                flag = False
                                    # count frequency in the file for temp
                                    if flag == True:
                                        if len(dq) >= size:
                                            if lowercase == True:
                                                temp_counter[' '.join(dq).lower()]+=1
                                            else:
                                                temp_counter[' '.join(dq)]+=1
            # general counts 
            for kv in temp_counter.most_common():
                # count ngram frequency
                counter[kv[0]]+= kv[1]
                # count range frequency
                range_counter[kv[0]]+=1
            # clear deque
            dq.clear()
            dqtag.clear()
            # print progress
            if show_progress == True:
                i+=1
                print("{1}% ..... {0} ".format (filename, round((i/float(total_files)) * 100)) )
                
        # filter only words
        i = 0
        tb = []
        tb.append("N\tN-GRAM\tFREQUENCY\tRANGE\t%")
        for kv in counter.most_common():
            if kv[1] >= min_freq:
                if range_counter[kv[0]] >= min_range:
                    i+=1
                    p = round((range_counter[kv[0]] / float(total_files)) * 100,2)
                    tb.append(str(i) + '\t' + kv[0] + '\t' + str(kv[1]) + '\t' + str(range_counter[kv[0]]) + '\t' + str(p))
        # free memory
        counter = None
        range_counter = None
        # return table
        ngrams = Ngrams()
        ngrams.read_str('\n'.join(tb))
        tb = None
        return  ngrams  
        
    #-----------------------------------------------------------------------------------------------------
    # CLUSTERS
    #-----------------------------------------------------------------------------------------------------
    
    def clusters(self,word,**kwargs):
        #args
        size = kwargs.get('size',3)
        lowercase = kwargs.get('lowercase',True)
        min_freq = kwargs.get('min_freq',1)
        min_range = kwargs.get('min_range',1)
        tag1 = kwargs.get('tag1',[None])
        tag2 = kwargs.get('tag2',[None])
        tag3 = kwargs.get('tag3',[None])
        tag4 = kwargs.get('tag4',[None])
        show_progress=kwargs.get('show_progress',False)
        # check tags
        if tag1 != [None]:
            tag1 = tag1.strip().split(' ')
        if tag2 != [None]:
            tag2 = tag2.strip().split(' ')
        if tag3 != [None]:
            tag3 = tag3.strip().split(' ')
        if tag4 != [None]:
            tag4 = tag4.strip().split(' ')
        # do not allow size greater than 4 
        # or equalt to 0
        if size > 4:
            size = 4
        if size == 0:
            size = 3
        # set required paths
        tagged_path = self.workspace + self.corpus_name + "/tagged"
        # get corpus files in a list 
        files = os.listdir(tagged_path)
        total_files = len(files)
        # loop through files
        dq = deque(maxlen=size)
        dqtag = deque(maxlen=size)
        ptn = re.compile("\W+")
        i = 0
        counter = Counter()
        range_counter = Counter()
        for filename in files:
            temp_counter = Counter()
            with open(tagged_path + '/' +filename,'r',encoding=self.encoding) as fh:
                for line in fh:
                    if len(line.strip()) != 0:
                        tokens = line.strip().split(' ')
                        for token in tokens:
                            wt = nltk.str2tuple(token)
                            if len(wt) >= 2:
                                if len(re.findall(ptn, wt[0])) == 0:
                                    dq.append(wt[0])
                                    dqtag.append(wt[1])
                                    # tag filter
                                    tag_flag = True
                                    if len(dq) >= size:
                                        if size == 1:
                                            if tag1 != [None] and dqtag[0] not in tag1:
                                                tag_flag = False
                                        elif size == 2:
                                            if (tag1 != [None] and dqtag[0] not in tag1) or (tag2 != [None] and dqtag[1] not in tag2):
                                                tag_flag = False
                                        elif size == 3:
                                            if (tag1 != [None] and dqtag[0] not in tag1) or (tag2 != [None] and dqtag[1] not in tag2) or (tag3 != [None] and dqtag[2] not in tag3):
                                                tag_flag = False
                                        elif size == 4:
                                            if (tag1 != [None] and dqtag[0] not in tag1) or (tag2 != [None] and dqtag[1] not in tag2) or (tag3 != [None] and dqtag[2] not in tag3) or (tag4 != [None] and dqtag[3] not in tag4):
                                                tag_flag = False
                                    
                                    # word filter
                                    word_flag = False
                                    if len(dq) >= size:
                                        if size == 1:
                                            if word.lower() == dq[0].lower():
                                                word_flag = True
                                        elif size == 2:
                                            if word.lower() == dq[0].lower() or word.lower() == dq[1].lower():
                                                word_flag = True
                                        elif size == 3:
                                            if word.lower() == dq[0].lower() or word.lower() == dq[1].lower() or word.lower() == dq[2].lower():
                                                word_flag = True 
                                        elif size == 4:
                                            if word.lower() == dq[0].lower() or word.lower() == dq[1].lower() or word.lower() == dq[2].lower() or word.lower() == dq[3].lower():
                                                word_flag = True
                                        
                                    # count frequency in the file for temp
                                    if tag_flag == True and word_flag == True:
                                        if len(dq) >= size:
                                            if lowercase == True:
                                                temp_counter[' '.join(dq).lower()]+=1
                                            else:
                                                temp_counter[' '.join(dq)]+=1
            # general counts 
            for kv in temp_counter.most_common():
                # count ngram frequency
                counter[kv[0]]+= kv[1]
                # count range frequency
                range_counter[kv[0]]+=1
            # clear deque
            dq.clear()
            dqtag.clear()
            # print progress
            if show_progress == True:
                i+=1
                print("{1}% ..... {0} ".format (filename, round((i/float(total_files)) * 100)) )
                
        # filter only words
        i = 0
        tb = []
        tb.append("N\tCLUSTER\tFREQUENCY\tRANGE\t%")
        for kv in counter.most_common():
            if kv[1] >= min_freq:
                if range_counter[kv[0]] >= min_range:
                    i+=1
                    p = round((range_counter[kv[0]] / float(total_files)) * 100,2)
                    tb.append(str(i) + '\t' + kv[0] + '\t' + str(kv[1]) + '\t' + str(range_counter[kv[0]]) + '\t' + str(p))
        # free memory
        counter = None
        range_counter = None
        # return table
        clusters = Clusters()
        clusters.read_str('\n'.join(tb))
        tb = None
        return  clusters     
        
    #-----------------------------------------------------------------------------------------------------
    # DISPERSION
    #-----------------------------------------------------------------------------------------------------
            
    def dispersion(self,node,**kwargs):
        # args
        pos = kwargs.get('pos',None)
        regex = kwargs.get('regex',False) 
        show_progress = kwargs.get('show_progress',False)
        # splits search word
        node = node.strip().split(' ')
        # checks pos for each search word
        if pos == None:
            pos = []
            for i in range(len(node)):
                pos.append(None)
        else:
            pos = pos.strip().split(' ')
        # node and dq size 
        node_size = len(node)
        dq = deque(maxlen=node_size)
        # set required paths
        tagged_path = self.workspace + self.corpus_name + "/tagged/"
        # get corpus files in a list 
        files = os.listdir(tagged_path)
        total_files = len(files)
        # loop
        data = []
        sorted(files)
        file_id = 0
        i = 0
        for filename in files:
            matching_ids = []
            total_words = 0
            file_id+=1
            word_id = 0
            sent_id = 0
            # search
            with open(tagged_path + '/' +filename,'r',encoding=self.encoding) as fh:
                for line in fh:
                    if len(line.strip()) != 0:
                        sent_id+=1
                        tokens = line.strip().split(' ')
                        if len(tokens) != 0:
                            for token in tokens:
                                wt = nltk.str2tuple(token)
                                # add for text source
                                if len(wt) >= 2:
                                    word_id +=1
                                    total_words+=1
                                    # add for matching
                                    dq.append(wt)
                                    #try match
                                    flag_pos = False
                                    flag_node = False
                                    if len(dq) == node_size:
                                        # check node matching
                                        # wild char
                                        new_node = [None,None,None,None]
                                        # 1
                                        if node_size == 1:
                                            if node[0] == '*':
                                                new_node[0] = dq[0][0]
                                            else:
                                                new_node[0] = node[0].lower()
                                        # 2
                                        elif node_size == 2:
                                            if node[0] == '*':
                                                new_node[0] = dq[0][0]
                                            else:
                                                new_node[0] = node[0].lower()
                                            if node[1] == '*':
                                                new_node[1] = dq[1][0]
                                            else:
                                                new_node[1] = node[1].lower()
                                        # 3
                                        elif node_size == 3:
                                            if node[0] == '*':
                                                new_node[0] = dq[0][0]
                                            else:
                                                new_node[0] = node[0].lower()
                                            if node[1] == '*':
                                                new_node[1] = dq[1][0]
                                            else:
                                                new_node[1] = node[1].lower()
                                            if node[2] == '*':
                                                new_node[2] = dq[2][0]
                                            else:
                                                new_node[2] = node[2].lower()
                                        # 4
                                        elif node_size == 4:
                                            if node[0] == '*':
                                                new_node[0] = dq[0][0]
                                            else:
                                                new_node[0] = node[0].lower()
                                            if node[1] == '*':
                                                new_node[1] = dq[1][0]
                                            else:
                                                new_node[1] = node[1].lower()
                                            if node[2] == '*':
                                                new_node[2] = dq[2][0]
                                            else:
                                                new_node[2] = node[2].lower()
                                            if node[3] == '*':
                                                new_node[3] = dq[3][0]
                                            else:
                                                new_node[3] = node[3].lower()                                             
                                        # check node matching 
                                        # 1
                                        if node_size == 1:
                                            if regex == False:
                                                if dq[0][0].lower() == new_node[0].lower():
                                                    flag_node = True
                                            else:
                                                if len(re.findall(new_node[0],dq[0][0]))!= 0:
                                                    flag_node = True
                                        # 2
                                        elif node_size == 2:
                                            if regex == False:
                                                if dq[0][0].lower() == new_node[0].lower() and dq[1][0].lower() == new_node[1].lower():
                                                    flag_node = True
                                            else:
                                                if len(re.findall(new_node[0],dq[0][0]))!= 0 and len(re.findall(new_node[1],dq[1][0]))!= 0:
                                                    flag_node = True
                                                
                                        # 3
                                        elif node_size == 3:
                                            if regex == False:
                                                if dq[0][0].lower() == new_node[0].lower() and dq[1][0].lower() == new_node[1].lower() and dq[2][0].lower() == new_node[2].lower():
                                                    flag_node = True
                                            else:
                                                if len(re.findall(new_node[0],dq[0][0]))!= 0 and len(re.findall(new_node[1],dq[1][0]))!= 0 and len(re.findall(new_node[2],dq[2][0]))!= 0:
                                                    flag_node = True
                                        # 4
                                        elif node_size == 4:
                                            if regex == False:
                                                if dq[0][0].lower() == new_node[0].lower() and dq[1][0].lower() == new_node[1].lower() and dq[2][0].lower() == new_node[2].lower() and dq[3][0].lower() == new_node[3].lower():
                                                    flag_node = True
                                            else:
                                                if len(re.findall(new_node[0],dq[0][0]))!= 0 and len(re.findall(new_node[1],dq[1][0]))!= 0 and len(re.findall(new_node[2],dq[2][0]))!= 0 and len(re.findall(new_node[3],dq[3][0]))!= 0:
                                                    flag_node = True
                                        # check pos matching None
                                        if node_size == 1 and pos[0] == None:
                                            flag_pos = True
                                        elif node_size == 2 and pos == [None,None]:
                                            flag_pos = True
                                        elif node_size ==  3 and pos == [None,None,None]:
                                            flag_pos = True
                                        elif node_size == 4 and pos == [None,None,None,None]:
                                            flag_pos = True
                                        else:
                                            # check wild char
                                            new_pos = [None,None,None,None]
                                            # 1
                                            if node_size == 1:
                                                if pos[0] == '*':
                                                    new_pos[0] = dq[0][1]
                                                else:
                                                    new_pos[0] = pos[0] 
                                            # 2    
                                            elif node_size == 2:
                                                    if pos[0] == '*':
                                                        new_pos[0] = dq[0][1]
                                                    else:
                                                        new_pos[0] = pos[0]
                                                    if pos[1] == '*':
                                                        new_pos[1] = dq[1][1]
                                                    else:
                                                        new_pos[1] =pos[1]
                                            # 3 
                                            elif node_size == 3:
                                                    if pos[0] == '*':
                                                        new_pos[0] = dq[0][1]
                                                    else:
                                                        new_pos[0] = pos[0]
                                                    if pos[1] == '*':
                                                        new_pos[1] = dq[1][1]
                                                    else:
                                                        new_pos[1] = pos[1]
                                                    if pos[2] == '*':
                                                        new_pos[2] = dq[2][1]
                                                    else:
                                                        new_pos[2] = pos[2]
                                            # 4
                                            if node_size == 4:
                                                    if pos[0] == '*':
                                                        new_pos[0] = dq[0][1]
                                                    else:
                                                        new_pos[0] = pos[0]
                                                    if pos[1] == '*':
                                                        new_pos[1] = dq[1][1]
                                                    else:
                                                        new_pos[1] = pos[1]
                                                    if pos[2] == '*':
                                                        new_pos[2] = dq[2][1]
                                                    else:
                                                        new_pos[2] = pos[2]
                                                    if pos[3] == '*':
                                                        new_pos[3] = dq[3][1]
                                                    else:
                                                        new_pos[3] = pos[3]
                                                        
                                            # check pos matching not None    
                                            # 1
                                            if len(pos) == 1:
                                                if pos[0] != None and new_pos[0] == dq[0][1]:
                                                    flag_pos = True
                                            # 2
                                            elif len(pos) == 2:
                                                if pos[0] != None and new_pos[0] == dq[0][1] and new_pos[1] == dq[1][1]:
                                                    flag_pos = True
                                            # 3
                                            elif len(pos) == 3:
                                                if pos[0] != None and new_pos[0] == dq[0][1] and new_pos[1] == dq[1][1] and new_pos[2] == dq[2][1]:
                                                    flag_pos = True
                                            # 4
                                            elif len(pos) == 4:
                                                if pos[0] != None and new_pos[0] == dq[0][1] and new_pos[1] == dq[1][1] and new_pos[2] == dq[2][1] and new_pos[3] == dq[3][1]:
                                                    flag_pos = True     
                                            
                                    # count if matching   
                                    if flag_node == True and flag_pos == True:
                                        matching_ids.append(word_id) 
            # make data
            points = []
            for mid in matching_ids:
                p = round((mid / float(total_words)) * 100,2)
                points.append(p)
            data.append((filename,total_words,len(points),points))
            
            # print progress
            if show_progress == True:
                i+=1
                print("{1}% ..... {0} ".format (filename, round((i/float(total_files)) * 100)) )
        
        files = None
        
        # make table
        dispersion = Dispersion(output_path=self.output_path)
        tb = []
        tb.append('N\tFILENAME\tTOTAL\tHITS\tS1\tS2\tS3\tS4\tS5')
        i = 0
        for d in data:
            i+=1
            s1 = 0
            s2 = 0 
            s3 = 0
            s4 = 0
            s5 = 0
            dispersion.dpts[d[0]] = d[3]
            for point in d[3]:
                p = round(point)
                if p >= 0 and p <= 19:
                    s1+=1
                elif p >= 20 and p <= 39:
                    s2+=1
                elif p >= 40 and p <= 59:
                    s3+=1
                elif p >= 60 and p <= 79:
                    s4+=1
                elif p >= 80 and p <= 100:
                    s5+=1
                
            dispersion.total_s1 += s1
            dispersion.total_s2 += s2
            dispersion.total_s3 += s3
            dispersion.total_s4 += s4
            dispersion.total_s5 += s5
            tb.append(str(i) + '\t' + str(d[0]) + '\t' + str(d[1]) + '\t' + str(d[2]) + '\t' + str(s1) + '\t' + str(s2) + '\t' + str(s3) + '\t' + str(s4) + '\t' + str(s5))
        
        data = None 
            
        dispersion.read_str('\n'.join(tb))
        
        tb = None
            
        return dispersion
        
    #-----------------------------------------------------------------------------------------------------
    # KEYWORDS PLOT
    #-----------------------------------------------------------------------------------------------------        
        
    def keywords_dispersion(self,keywords,**kwargs):
        #args
        show_progress=kwargs.get('show_progress',False)
        lowercase = kwargs.get('lowercase',True)
        limit = kwargs.get('limit',100)
        # set required paths
        tagged_path = self.workspace + self.corpus_name + "/tagged"
        # get corpus files in a list 
        files = os.listdir(tagged_path)
        total_files = len(files)
        # get keywords 
        keys = OrderedDict()
        i = 0 
        for row in keywords.df.itertuples(index=False):
            i+=1
            if i > limit:
                break
            keys[row[1]] = row[3]
        keywords = None
        # create keywords dict for points
        keys_points = OrderedDict()
        for k in keys:
            keys_points[k] = list()
        # loop through files
        ptn = re.compile("\W+")
        i = 0
        counter = Counter()
        for filename in files:
            total_words = 0  
            word_id = 0
            dic_ids = {}
            with open(tagged_path + '/' +filename,'r',encoding=self.encoding) as fh:
                for line in fh:
                    if len(line.strip()) != 0:
                        tokens = line.strip().split(' ')
                        for token in tokens:
                            wt = nltk.str2tuple(token)
                            if len(wt) >= 2:
                                total_words+=1
                                word_id +=1
                                if len(re.findall(ptn, wt[0])) == 0:
                                    if lowercase == True:
                                        if wt[0].lower() in keys:
                                            if wt[0].lower() not in dic_ids:
                                                dic_ids[wt[0].lower()] = list()
                                                dic_ids[wt[0].lower()].append(word_id)
                                            else:
                                                dic_ids[wt[0].lower()].append(word_id)
                                    else:
                                        if wt[0] in keys:
                                            if wt[0] not in dic_ids:
                                                dic_ids[wt[0]] = list()
                                                dic_ids[wt[0]].append(word_id)
                                            else:
                                                dic_ids[wt[0]].append(word_id)
            # get positions
            for k in dic_ids:
                if len(dic_ids[k]) != 0:
                    for mid in dic_ids[k]:
                        p = round((mid / float(total_words)) * 100,2)
                        keys_points[k].append(p)
                          
            
            # print progress
            if show_progress == True:
                i+=1
                print("{1}% ..... {0} ".format (filename, round((i/float(total_files)) * 100)) )
        
        files = None
        
        
        # make table
        dispersion = KeywordsDispersion(output_path=self.output_path)
        tb = []
        tb.append('N\tWORD\tKEYNESS\tHITS\tS1\tS2\tS3\tS4\tS5')
        i = 0
        for k in keys_points:
            i+=1
            s1 = 0
            s2 = 0 
            s3 = 0
            s4 = 0
            s5 = 0
            dispersion.dpts[k] = keys_points[k]
            for point in keys_points[k]:
                p = round(point)
                if p >= 0 and p <= 19:
                    s1+=1
                elif p >= 20 and p <= 39:
                    s2+=1
                elif p >= 40 and p <= 59:
                    s3+=1
                elif p >= 60 and p <= 79:
                    s4+=1
                elif p >= 80 and p <= 100:
                    s5+=1
            
            dispersion.total_s1 += s1
            dispersion.total_s2 += s2
            dispersion.total_s3 += s3
            dispersion.total_s4 += s4
            dispersion.total_s5 += s5
            
            tb.append(str(i) + '\t' + k + '\t' + str(keys[k]) + '\t'  + str(len(keys_points[k])) + '\t' +  str(s1) + '\t' + str(s2) + '\t' + str(s3) + '\t' + str(s4) + '\t' + str(s5) )
        
        keys = None
        keys_points = None
            
        dispersion.read_str('\n'.join(tb))
        
        tb = None
        
        return  dispersion
        
    #-----------------------------------------------------------------------------------------------------
    # KEYWORDS x RANGE
    #-----------------------------------------------------------------------------------------------------
    
    def keynessxrange(self,keywords,wfreqinfiles,**kwargs):
        tb = keywords.df.merge(wfreqinfiles.df,on='WORD',how='left')
        keywords = None
        wfreqinfiles = None
        tb['KEYNESS*RANGE'] = tb['KEYNESS'] * tb['RANGE']
        tb.drop(['KEYNESS','RANGE','%','N_y'],axis=1,inplace=True)
        tb = tb.sort_values('KEYNESS*RANGE', ascending=False)
        tb = tb.reset_index(drop=True)
        tb.columns = ['N', 'WORD','FREQUENCY','KEYNESS*RANGE']
        j = 0 
        for i, row in tb.iterrows():
            j+=1
            tb.set_value(i,'N',j)
        keyrange = Keynessxrange()
        keyrange.df = tb 
        return keyrange 
    
    
    def textfile_get_tagged_sents(self,text_id):
        # set required paths
        tagged_path = self.workspace + self.corpus_name + "/tagged/"
        # get corpus files in a list 
        files = os.listdir(tagged_path)
        # sort
        sorted(files)
        # get
        text = None 
        filename = files[text_id]
        sents = []
        with open(self.workspace + self.corpus_name + "/tagged/" + filename,'r') as fh:
            for line in fh:
                tokens = line.strip().split(' ')
                sent = []
                for token in tokens:
                    wt = nltk.str2tuple(token)
                    sent.append(wt)
                sents.append(sent)
        return sents 
    
    def textfile_get_tokenized_sents(self,text_id):
        # set required paths
        tagged_path = self.workspace + self.corpus_name + "/tagged/"
        # get corpus files in a list 
        files = os.listdir(tagged_path)
        # sort
        sorted(files)
        # get
        text = None 
        filename = files[text_id]
        sents = []
        with open(self.workspace + self.corpus_name + "/tagged/" + filename,'r') as fh:
            for line in fh:
                tokens = line.strip().split(' ')
                sent = []
                for token in tokens:
                    wt = nltk.str2tuple(token)
                    sent.append(wt[0])
                sents.append(sent)
        return sents
    
    def textfile_to_conll2000(self,text_id):
        sents = self.textfile_get_tagged_sents(text_id)
        new_sents = []
        for sent in sents:
            new_sents.append(utils.sent2conll2000(sent))
        return '\n\n'.join(new_sents)
        
            
        
        
        
        
        
                
            
    
    
            
            
            
            
            
            
            
            
            
        
    
        
        
        
        
        
        
            
        
        
        

        
        
    
      
        
        
                 
         
