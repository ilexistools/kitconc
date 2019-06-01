# -*- coding: utf-8 -*-
import os, sys  
import collections
import nltk 
import re
from kitconc import kit_tools 
from kitconc import kit_util  
 
class Corpus (object):
    """This class is the main component for doing corpus analysis in Kitconc."""
        
    
    def __init__(self,workspace,corpus_name,**kwargs):
        """
        :param  workspace: A folder path where the corpus will be stored
        :type   workspace: str
        :param corpus_name: A name for corpus identification. 
        :type corpus_name: str
        :param language: The language for text processing. 
        :type language: str 
        :param encoding: The enconding for input texts.
        :type encoding: str 
        """
        # script path
        self.__path = os.path.dirname(os.path.abspath(__file__))
        # normalize workspace path 
        if str(workspace).endswith('/'):
            self.workspace = workspace
        else:
            self.workspace = workspace + '/'
        # check workspace path exists
        # if not create it 
        if os.path.exists(self.workspace) == False:
            os.mkdir(self.workspace)
        # check corpus already exists
        if os.path.exists(self.workspace + corpus_name + '/info.tab'):
            # read info
            info = self.__load_corpus_info(self.workspace, corpus_name)
            self.corpus_name = corpus_name 
            self.language = info['language']
            self.encoding = info['encoding']
            self.output_path = self.workspace + self.corpus_name + '/output/'
            self.tagged_path = self.workspace + self.corpus_name + '/tagged/'
        else:
            # get kwargs
            language = kwargs.get('language','english')
            encoding = kwargs.get('encoding','utf-8')
            # set variables 
            self.corpus_name = corpus_name
            self.language = language 
            self.encoding = encoding
            self.output_path = self.workspace + self.corpus_name + '/output/'
            self.tagged_path = self.workspace + self.corpus_name + '/tagged/'
            # create corpus folder
            if not os.path.exists(self.workspace + self.corpus_name):
                os.mkdir(self.workspace + self.corpus_name)
            if not os.path.exists(self.workspace + self.corpus_name + '/tagged'):
                os.mkdir(self.workspace + self.corpus_name + '/tagged')
            if not os.path.exists(self.workspace + self.corpus_name + '/output'):
                os.mkdir(self.workspace + self.corpus_name + '/output')
            # save info
            self.__save_corpus_info(self.workspace, self.corpus_name, self.language, self.encoding)
            
        
    def __save_corpus_info(self,workspace,corpus_name,language,encoding):
        info = []
        info.append('workspace:' + '\t' + workspace)
        info.append('corpus name:' + '\t' + corpus_name)
        info.append('language:' + '\t' + language)
        info.append('encoding:' + '\t' + encoding)
        with open(workspace + corpus_name + '/info.tab','w',encoding='utf-8') as fh:
            fh.write('\n'.join(info))
    
    def __load_corpus_info (self,workspace,corpus_name):
        info = {}
        with open(workspace + corpus_name + '/info.tab','r',encoding='utf-8') as fh:
            for line in fh:
                if len(line.strip()) !=0:
                    fields = line.strip().split('\t')
                    if len(fields) >= 2:
                        info[fields[0].replace(':','')]=fields[1]
        return info
    
    def __progress(self, count, total, suffix=''):
        bar_len = 30
        filled_len = int(round(bar_len * count / float(total)))
        percents = round(100.0 * count / float(total), 1)
        bar = '=' * filled_len + '-' * (bar_len - filled_len)
        sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', suffix))
        try:
            sys.stdout.flush()  
        except:
            pass 

    
    def add_texts(self,source_folder,**kwargs):
        """
        Adds texts to the corpus. Texts are tagged and saved in a corpus folder for analysis
        :param  souce_folder: A string path where texts for processing are stored
        :type  souce_folder: str
        :param show_progress: Prints a progress message if value is True
        :type  show_progress: str
        :return: True or False
        :rtype: boolean
        """
        import pickle
        # args
        show_progress=kwargs.get('show_progress',False)
        # load tokenizer
        tokenizer_path = self.__path + '/data/tokenizer_' + self.language + '.pickle'
        with open(tokenizer_path, 'rb') as fh:
            tokenizer = pickle.load(fh)
        # load tagger
        tagger_path = self.__path + '/data/tagger_' + self.language  + '.pickle'
        with open(tagger_path, 'rb') as fh:
            tagger = pickle.load(fh)
        # get filenames
        files = os.listdir(source_folder)
        total_files = len(files)
        i = 0
        # tag texts
        for filename in sorted(files):
            if os.path.isfile(source_folder + '/' + filename):
                i +=1
                tagged_sents = []
                with open(source_folder + "/" + filename,'r',encoding=self.encoding) as fh:
                    for line in fh:
                        if len(line.strip()) != 0:
                            for sent in tokenizer.tokenize(line):
                                str_sent = []
                                for token in tagger.tag(nltk.tokenize.word_tokenize(sent, language=self.language)):
                                    str_sent.append(token[0] + '/' + token[1])
                                tagged_sents.append(' '.join(str_sent))
                with open(self.workspace + self.corpus_name + "/tagged/" + filename ,'w',encoding=self.encoding) as fh:
                    fh.write('\n'.join(tagged_sents))
                if show_progress == True:
                    self.__progress(i, total_files,filename)
                    
            else:
                total_files-=1
        return True 
    
    def add_texts_without_tagging(self,source_folder,**kwargs):
        """
        Adds texts to the corpus without tagging.
        :param  souce_folder: A string path where texts for processing are stored
        :type  souce_folder: str
        :param show_progress: Prints a progress message if value is True
        :type  show_progress: str
        :return: True or False
        :rtype: boolean
        """
        import pickle
        # args
        show_progress=kwargs.get('show_progress',False)
        # load tokenizer
        tokenizer_path = self.__path + '/data/tokenizer_' + self.language + '.pickle'
        with open(tokenizer_path, 'rb') as fh:
            tokenizer = pickle.load(fh)
        # get filenames
        files = os.listdir(source_folder)
        total_files = len(files)
        i = 0
        # tag texts
        for filename in sorted(files):
            if os.path.isfile(source_folder + '/' + filename):
                i +=1
                tagged_sents = []
                with open(source_folder + "/" + filename,'r',encoding=self.encoding) as fh:
                    for line in fh:
                        if len(line.strip()) != 0:
                            for sent in tokenizer.tokenize(line):
                                str_sent = []
                                for token in nltk.tokenize.word_tokenize(sent, language=self.language):
                                    str_sent.append(token + '/*')
                                tagged_sents.append(' '.join(str_sent))
                with open(self.workspace + self.corpus_name + "/tagged/" + filename ,'w',encoding=self.encoding) as fh:
                    fh.write('\n'.join(tagged_sents))
                if show_progress == True:
                    self.__progress(i, total_files,filename)
            else:
                total_files-=1
        return True
    
    def add_tagged_texts(self,source_folder,**kwargs):
        """
        Adds tagged texts to the corpus.
        :param  souce_folder: A string path where texts for processing are stored
        :type  souce_folder: str
        :param show_progress: Prints a progress message if value is True
        :type  show_progress: str
        :return: True or False
        :rtype: boolean
        """
        import shutil 
        # args
        show_progress=kwargs.get('show_progress',False)
        # normalize path 
        if str(source_folder).endswith('/'):
            pass 
        else:
            source_folder = source_folder + '/'
        # get filenames
        files = os.listdir(source_folder)
        total_files = len(files)
        i = 0
        # copy
        for filename in sorted(files):
            if os.path.isfile(source_folder + '/' + filename):
                i +=1
                shutil.copyfile(source_folder + filename,self.tagged_path + filename)
                if show_progress == True:
                    self.__progress(i, total_files,filename)
        return True
    
    def cleanse(self):
        """Removes all contents from corpus folders"""  
        import shutil
        shutil.rmtree(self.output_path)
        shutil.rmtree(self.tagged_path)
        # create corpus folder
        if not os.path.exists(self.workspace + self.corpus_name + '/tagged'):
            os.mkdir(self.workspace + self.corpus_name + '/tagged')
        if not os.path.exists(self.workspace + self.corpus_name + '/output'):
            os.mkdir(self.workspace + self.corpus_name + '/output')
        return True
    
    def textfile_get_tagged_sents(self,text_id):
        """Returns tagged sentences from a specified file."""
        # set required paths
        tagged_path = self.workspace + self.corpus_name + "/tagged/"
        # get corpus files in a list 
        files = os.listdir(tagged_path)
        # sort
        sorted(files)
        # get
        filename = files[text_id]
        sents = []
        with open(self.workspace + self.corpus_name + "/tagged/" + filename,'r',encoding=self.encoding) as fh:
            for line in fh:
                tokens = line.strip().split(' ')
                sent = []
                for token in tokens:
                    wt = nltk.str2tuple(token)
                    sent.append(wt)
                sents.append(sent)
        return sents 
    
    def textfile_get_tokenized_sents(self,text_id):
        """Returns tokenized sentences from a specified file."""
        # set required paths
        tagged_path = self.workspace + self.corpus_name + "/tagged/"
        # get corpus files in a list 
        files = os.listdir(tagged_path)
        # sort
        sorted(files)
        # get
        filename = files[text_id]
        sents = []
        with open(self.workspace + self.corpus_name + "/tagged/" + filename,'r',encoding=self.encoding) as fh:
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
            new_sents.append(kit_util.sent2conll2000(sent))
        return '\n\n'.join(new_sents)
    
    
    def textfile_get_tokenized_sent(self,text_id,sent_id):
        """Returns a tokenized sentence from a specified file."""
        # set required paths
        tagged_path = self.workspace + self.corpus_name + "/tagged/"
        # get corpus files in a list 
        files = os.listdir(tagged_path)
        # sort
        sorted(files)
        # get filename 
        textid = 0
        filename = None
        for f in files:
            textid +=1
            if text_id == textid:
                filename = f 
                break
        files = None  
        # get sent
        tokenized_sent = [] 
        sentid = 0
        with open(self.workspace + self.corpus_name + "/tagged/" + filename,'r',encoding=self.encoding) as fh:
            for line in fh:
                if len(line.strip()) != 0:
                    sentid+=1
                    if sent_id == sentid:
                        for token in line.strip().split(' '):
                            tokenized_sent.append(nltk.str2tuple(token)[0])
                        break
        return tokenized_sent
    
    def textfile_get_tagged_sent(self,text_id,sent_id):
        """Returns a tagged sentence from a specified file."""
        # set required paths
        tagged_path = self.workspace + self.corpus_name + "/tagged/"
        # get corpus files in a list 
        files = os.listdir(tagged_path)
        # sort
        sorted(files)
        # get filename 
        textid = 0
        filename = None
        for f in files:
            textid +=1
            if text_id == textid:
                filename = f 
                break
        files = None
        # get sent
        tokenized_sent = [] 
        sentid = 0
        with open(self.workspace + self.corpus_name + "/tagged/" + filename,'r',encoding=self.encoding) as fh:
            for line in fh:
                if len(line.strip()) != 0:
                    sentid+=1
                    if sent_id == sentid:
                        for token in line.strip().split(' '):
                            tokenized_sent.append(nltk.str2tuple(token))
                        break
        return tokenized_sent
                
    
    def texts_count(self):
        """Returns the number of texts in the corpus."""
        tagged_path = self.workspace + self.corpus_name + "/tagged/"
        total_count =  len(os.listdir(tagged_path))
        return total_count 
        
    def texts_get_ids(self):
        """Returns the texts ids from corpus files in a dictionary."""
        # set required paths
        tagged_path = self.workspace + self.corpus_name + "/tagged/"
        # get corpus files in a list 
        files = os.listdir(tagged_path)
        # sort
        sorted(files)
        # get filename 
        textid = 0
        fileids = {}
        for filename in files:
            textid +=1
            fileids[textid] = filename
        return fileids
    
    def texts_get_filenames(self):
        """Returns a list with the filenames in the corpus."""
        # set required paths
        tagged_path = self.workspace + self.corpus_name + "/tagged/"
        # get corpus files in a list 
        files = os.listdir(tagged_path)
        # sort
        sorted(files)
        # get filenames
        filenames = []
        for filename in files:
            filenames.append(filename)
        return filenames
 
    
    def wordlist(self,**kwargs):
        """
        Generates a frequency wordlist based on text files.
        :param lowercase: Letters are converted to lowercase 
        :type lowercase: boolean
        :param show_progress: Prints a progress message if value is True 
        :type show_progress: boolean
        :return: Wordlist
        :rtype: Wordlist
        """
        #args
        show_progress=kwargs.get('show_progress',False)
        lowercase = kwargs.get('lowercase',True)
        pbi = kwargs.get('pbi',int)
        # get corpus files in a list 
        files = os.listdir(self.tagged_path)
        total_files = len(files)
        # loop through files
        ptn = re.compile("^\W+$") # avoid punctuation
        i = 0
        number_of_tokens = 0
        hapax = 0
        counter = collections.Counter()
        for filename in files:
            with open(self.tagged_path+filename,'r',encoding=self.encoding) as fh:
                for line in fh:
                    if len(line.strip()) != 0:
                        for token in line.strip().split(' '):
                            wt = nltk.str2tuple(token)
                            if len(wt) >= 2:
                                if re.search(ptn, wt[0]) == None:
                                    number_of_tokens+=1
                                    if lowercase == True:
                                        counter[wt[0].lower()]+=1
                                    else:
                                        counter[wt[0]]+=1
            # print progress
            if show_progress == True:
                i+=1
                self.__progress(i, total_files,filename)
                pbi = i
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
        wlst = kit_tools.Wordlist(tokens=number_of_tokens,types=number_of_types,typetoken=typetoken, hapax=hapax)
        wlst.read_str('\n'.join(wordlist))
        return  wlst  
                    
    def keywords(self,wordlist,**kwargs):
        """
        Extracts keywords from a wordlist
        :param wordlist: Wordlist object
        :type wordlist: Wordlist
        :param measure: A statistical measure to use (log-likelihood or chi square)
        :type measure : str
        :param show_progress: Prints a progress message if value is True
        :type show_progress: boolean
        :return: Keywords
        :rtype: Keywords
        """
        #args
        measure = kwargs.get('measure','log-likelihood')
        show_progress=kwargs.get('show_progress',False)
        # get statistics measures
        if measure == 'log-likelihood':
            stat = 1
        elif measure == 'chi-square':
            stat = 2
        else:
            stat = 1
        # load reflist 
        reflist = kit_util.load_reference_wordlist(self.__path + '/data/reflist_' + self.language + '.tab')
        tk_refc = sum([reflist[k] for k in reflist])
        # extract keywords
        wfreq = {}
        counter = collections.Counter()
        tk_stdc = wordlist.tokens 
        i = 0
        total = len(wordlist.df)
        for row in wordlist.df.itertuples(index=False):
            wfreq[str(row[1])] = int(row[2])
            freq_refc = 0
            if str(row[1]) in reflist:
                freq_refc = reflist[str(row[1])]
            if stat == 1:
                keyness = kit_util.ll(int(row[2]),freq_refc,tk_stdc,tk_refc)
            elif stat == 2:
                keyness = kit_util.chi_square (int(row[2]),freq_refc,tk_stdc,tk_refc)
            if str(row[1]) not in counter:
                counter[str(row[1])] = keyness
            # print progress
            if show_progress == True:
                i+=1
                self.__progress(i, total,str(row[1]))
        reflist = None
        wordlist = None
        # make keywords table
        keywords = [] 
        keywords.append('N\tWORD\tFREQUENCY\tKEYNESS')
        i = 0
        for kv in counter.most_common():
            i+=1
            keywords.append(str(i) + '\t' + kv[0] + '\t' + str(wfreq[kv[0]])  +  '\t' + str(kv[1]))
        kwlst = kit_tools.Keywords()
        kwlst.read_str('\n'.join(keywords))
        keywords = None 
        return kwlst
    
    def wtfreq(self,**kwargs):
        """
        Generates a word tag frequency list based on corpus text files.
        :param lowercase: Letters are converted to lowercase
        :type lowercase : boolean
        :param show_progress: Prints a progress message if value is True
        :type show_progress: boolean
        :return: WTfreq
        :rtype: WTfreq
        """
        #args
        lowercase = kwargs.get('lowercase',True)
        show_progress=kwargs.get('show_progress',False)
        # get corpus files in a list 
        files = os.listdir(self.tagged_path)
        total_files = len(files)
        # loop through files
        ptn = re.compile("^\W+$") # avoid punctuation
        i = 0
        number_of_tokens = 0
        counter = collections.Counter()
        for filename in files:
            with open(self.tagged_path + '/' + filename,'r',encoding = self.encoding) as fh:
                for line in fh:
                    if len(line.strip()) != 0:
                        tokens = line.strip().split(' ')
                        for token in tokens:
                            wt = nltk.str2tuple(token)
                            if len(wt) >= 2:
                                if re.search(ptn, wt[0]) == None:
                                    number_of_tokens+=1
                                    if lowercase == True:
                                        counter[wt[0].lower() + '\t' + wt[1]]+=1
                                    else:
                                        counter[wt[0] + '\t' + wt[1]]+=1
            # print progress
            if show_progress == True:
                i+=1
                self.__progress(i, total_files,filename)
        i = 0
        wtfreq = []
        wtfreq.append("N\tWORD\tTAG\tFREQUENCY\t%")
        for kv in counter.most_common():
            i+=1
            p = round((kv[1] / float(number_of_tokens)) * 100,2)
            wtfreq.append(str(i) + '\t' + kv[0] + '\t' + str(kv[1]) + '\t' + str(p) )
        counter = None
        wt = kit_tools.WTfreq()
        wt.read_str('\n'.join(wtfreq))
        wtfreq = None 
        return wt
    
    def wfreqinfiles(self,wordlist,**kwargs):
        """
        Generates a frequency list based on word occurrence in corpus text files.
        :param lowercase: Letters are converted to lowercase
        :type lowercase : boolean
        :param show_progress: Prints a progress message if value is True
        :type show_progress: boolean
        :return: Wfreqinfiles
        :rtype: Wfreqinfiles
        """
        #args
        lowercase= kwargs.get('lowercase',True)
        show_progress=kwargs.get('show_progress',False)
        # create a dictionary of words
        words = collections.Counter()
        for row in wordlist.df.itertuples(index=False):
            words[row[1]] = 0
        wordlist = None
        # get corpus files in a list 
        files = os.listdir(self.tagged_path)
        total_files = len(files)
        # loop through files
        i = 0
        ptn = re.compile("^\W+$")
        for filename in files:
            counter = collections.Counter()
            with open(self.tagged_path + '/' +filename,'r',encoding=self.encoding) as fh:
                for line in fh:
                    if len(line.strip()) != 0:
                        tokens = line.strip().split(' ')
                        for token in tokens:
                            wt = nltk.str2tuple(token)
                            if len(wt) >= 2:
                                if re.search(ptn, wt[0]) == None:
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
                self.__progress(i, total_files,filename)
        
        # save table
        i = 0
        tb = []
        tb.append("N\tWORD\tRANGE\t%")
        for kv in words.most_common():
            i+=1
            p = round((kv[1] / float(total_files)) * 100,2)
            tb.append(str(i) + '\t' + str(kv[0]) + '\t' + str(kv[1]) + '\t' + str(p))
        
        words = None
        fif = kit_tools.Wfreqinfiles()
        fif.read_str('\n'.join(tb))
        return fif
    
    def kwic(self,node,**kwargs):
        """
        Generates concordance lines.
        :param node: Search word or phrase (max. 4 words)
        :type node : str
        :param pos: Part of speech (POS) for each search word 
        :type pos: str or list
        :param regex: Enable regular expression for search word matching
        :type regex: boolean
        :param horizon: Left and right horizon of words
        :type horizon: int
        :param limit: Number of concordance lines to return
        :type limit: int
        :param show_progress: Prints a progress message if value is True
        :type show_progress: boolean
        :return: Kwic
        :rtype: Kwic
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
            if not type(pos) == list:
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
        dq = collections.deque(maxlen=node_size)
        # get corpus files in a list 
        files = os.listdir(self.tagged_path)
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
            with open(self.tagged_path + '/' +filename,'r',encoding=self.encoding) as fh:
                for line in fh:
                    if len(line.strip()) != 0:
                        sent_id+=1
                        tokens = line.strip().split(' ')
                        if len(tokens) != 0:
                            word_token_id = 0
                            for token in tokens:
                                word_token_id+=1
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
                                        ids.append((token_id,sent_id,file_id,word_token_id))
            # make kwic
            if len(ids) != 0:
                for idx in ids:
                    j+=1
                    l = (idx[0]-(cols+node_size),idx[0]-node_size)
                    n = (idx[0]-node_size, (idx[0]-node_size)+ node_size)
                    r = (idx[0],idx[0]+cols)
                    kwic_lines.append ( str(j) + '\t' + ' '.join(  text[l[0]:l[1]]) + '\t' +  ' '.join(text[n[0]:n[1]]) + '\t' + ' '.join(text[r[0]:r[1]]) + '\t' + filename + '\t' + str(idx[3]) + '\t' + str(idx[1]) + '\t' +str(file_id))
            
            # print progress
            if show_progress == True:
                i+=1
                self.__progress(i, total_files,filename)
        # make kwic
        files = None
        k = kit_tools.Kwic()
        k.read_str('\n'.join(kwic_lines))
        kwic_lines = None
        return k
     
        
        
        
    def concordance(self,node,**kwargs):
        """
        Generates concordance lines.
        :param node: Search word or phrase (max. 4 words)
        :type node : str
        :param pos: Part of speech (POS) for each search word 
        :type pos: str or list
        :param regex: Enable regular expression for search word matching
        :type regex: boolean
        :param horizon: Left and right horizon of words
        :type horizon: int
        :param limit: Number of concordance lines to return
        :type limit: int
        :param show_progress: Prints a progress message if value is True
        :type show_progress: boolean
        :return: Concordance
        :rtype: Concordance
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
            if not type(pos) == list:
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
        dq = collections.deque(maxlen=node_size)
        # get corpus files in a list 
        files = os.listdir(self.tagged_path)
        total_files = len(files)
        # loop
        sorted(files)
        file_id = 0
        kwic_lines =[]
        kwic_lines.append('N\tLEFT\tNODE\tRIGHT\tFILENAME\tTOKEN_ID\tSENT_ID\tFILE_ID')
        conc_indexes = []
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
            with open(self.tagged_path + '/' +filename,'r',encoding=self.encoding) as fh:
                for line in fh:
                    if len(line.strip()) != 0:
                        sent_id+=1
                        tokens = line.strip().split(' ')
                        if len(tokens) != 0:
                            word_token_id = 0
                            for token in tokens:
                                word_token_id+=1
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
                                        ids.append((token_id,sent_id,file_id,word_token_id))
            # make conc indexes 
            if len(ids) != 0:
                for idx in ids:
                    j+=1
                    conc_indexes.append((filename,idx[3],idx[1],file_id))
            # print progress
            if show_progress == True:
                i+=1
                self.__progress(i, total_files,filename)
        files = None
        s = []
        s.append('N\tCONCORDANCE\tFILENAME\tTOKEN_ID\tSENT_ID\tFILE_ID')
        i = 0
        for item in conc_indexes:
            i+=1
            sent = self.textfile_get_tokenized_sent(item[3], item[2])
            s.append(str(i) + '\t' +  ' '.join(sent) + '\t' + str(item[0]) + '\t' + str(item[1]) + '\t' + str(item[2]) + '\t' + str(item[3]) )
        conc_indexes = None
        # make concordance
        concordance = kit_tools.Concordance()
        concordance.read_str('\n'.join(s))
        s = None 
        return concordance 

    
    def collocates(self,wordlist,node,**kwargs):
        """
        Generates a list of collocates.
        :param wordlist: Wordlist object
        :type wordlist : Wordlist
        :param node: Search word or phrase (max. 4 words) 
        :type node: str 
        :param pos: POS for word or phrase
        :type pos: str or list
        :param coll_pos: POS for filtering
        :type coll_pos: str or list
        :param measure: Statistic measure tscore or mutual information 
        :type measure: str
        :param regex: Enable regular expression for search word matching
        :type regex: boolean
        :param limit: Number of concordance lines to return
        :type limit: int
        :param show_progress: Prints a progress message if value is True
        :type show_progress: boolean
        :return: Collocates
        :rtype: Collocates
        """
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
            if not type(pos) == list:
                pos = pos.strip().split(' ')
        # check coll_pos
        if coll_pos != None:
            if not type(coll_pos) == list:
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
        dq = collections.deque(maxlen=node_size)
        # get corpus files in a list 
        files = os.listdir(self.tagged_path)
        total_files = len(files)
        # counters
        left_counter = collections.Counter()
        right_counter = collections.Counter()
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
            with open(self.tagged_path + '/' +filename,'r',encoding=self.encoding) as fh:
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
                self.__progress(i, total_files,filename)
        
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
        collocates = collections.Counter()
        for k in wfreq:
            lfreq = 0
            rfreq = 0
            if k in left_counter:
                lfreq = left_counter[k]
            if k in right_counter:
                rfreq = right_counter[k]
            total = lfreq + rfreq
            
            if stat == 1:
                m = kit_util.tscore(total, total_matches, wfreq[k], ntokens, 1)
            elif stat == 2:
                m = kit_util.mutual_information(total, total_matches, wfreq[k], ntokens, 1)
            collocates [(k,str(total),str(lfreq),str(rfreq))] = m 
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
        coll = kit_tools.Collocates()
        coll.read_str('\n'.join(tb))
        tb = None
        return coll

    
    def ngrams(self,**kwargs):
        """
        Generates a list of ngrams
        :param size: size of the ngram
        :type size: int
        :param min_freq: minimum frequency of the ngram
        :type min_freq: int
        :param min_range: minimum range frequency 
        :type min_range: int
        :param lowercase: Letters are converted to lowercase 
        :type lowercase: boolean
        :param tag1: POS tag for w1 
        :type tag1: str or list
        :param tag2: POS tag for w2 
        :type tag2: str or list
        :param tag3: POS tag for w3 
        :type tag3: str or list
        :param show_progress: Prints a progress message if value is True
        :type show_progress: boolean
        :return: Ngrams
        :rtype: Ngrams
        """
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
        if not type(tag1) == list:
            tag1 = tag1.strip().split(' ')
        if not type(tag2) == list:
            tag2 = tag2.strip().split(' ')
        if not type(tag3) == list:
            tag3 = tag3.strip().split(' ')
        if not type(tag4) == list:
            tag4 = tag4.strip().split(' ')
        # do not allow size greater than 4 
        # or equalt to 0
        if size > 4:
            size = 4
        if size == 0:
            size = 3
        # get corpus files in a list 
        files = os.listdir(self.tagged_path)
        total_files = len(files)
        # loop through files
        dq = collections.deque(maxlen=size)
        dqtag = collections.deque(maxlen=size)
        ptn = re.compile("^\W+$")
        i = 0
        counter = collections.Counter()
        range_counter = collections.Counter()
        for filename in files:
            temp_counter = collections.Counter()
            with open(self.tagged_path + '/' +filename,'r',encoding=self.encoding) as fh:
                for line in fh:
                    if len(line.strip()) != 0:
                        tokens = line.strip().split(' ')
                        for token in tokens:
                            wt = nltk.str2tuple(token)
                            if len(wt) >= 2:
                                if re.search(ptn, wt[0]) == None:
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
                self.__progress(i, total_files,filename)
                
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
        ngrams = kit_tools.Ngrams()
        ngrams.read_str('\n'.join(tb))
        tb = None
        return  ngrams
    
    def clusters(self,word,**kwargs):
        """
        Generates a list of clusters
        :param word: search word
        :type word: str
        :param size: size of the cluster
        :type size: int
        :param min_freq: minimum frequency of the cluster
        :type min_freq: int
        :param min_range: minimum range frequency 
        :type min_range: int
        :param lowercase: Letters are converted to lowercase 
        :type lowercase: boolean
        :param tag1: POS tag for w1 
        :type tag1: str or list
        :param tag2: POS tag for w2 
        :type tag2: str or list
        :param tag3: POS tag for w3 
        :type tag3: str or list
        :param show_progress: Prints a progress message if value is True
        :type show_progress: boolean
        :return: Clusters
        :rtype: Clusters
        """
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
        if not type(tag1) == list:
            tag1 = tag1.strip().split(' ')
        if not type(tag2) == list:
            tag2 = tag2.strip().split(' ')
        if not type(tag3) == list:
            tag3 = tag3.strip().split(' ')
        if not type(tag4) == list:
            tag4 = tag4.strip().split(' ')
        # do not allow size greater than 4 
        # or equalt to 0
        if size > 4:
            size = 4
        if size == 0:
            size = 3
        # get corpus files in a list 
        files = os.listdir(self.tagged_path)
        total_files = len(files)
        # loop through files
        dq = collections.deque(maxlen=size)
        dqtag = collections.deque(maxlen=size)
        ptn = re.compile("^\W+$")
        i = 0
        counter = collections.Counter()
        range_counter = collections.Counter()
        for filename in files:
            temp_counter = collections.Counter()
            with open(self.tagged_path + '/' +filename,'r',encoding=self.encoding) as fh:
                for line in fh:
                    if len(line.strip()) != 0:
                        tokens = line.strip().split(' ')
                        for token in tokens:
                            wt = nltk.str2tuple(token)
                            if len(wt) >= 2:
                                if re.search(ptn, wt[0]) == None:
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
                self.__progress(i, total_files,filename)
                
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
        clusters = kit_tools.Clusters()
        clusters.read_str('\n'.join(tb))
        tb = None
        return  clusters
    
    def dispersion(self,node,**kwargs):
        """
        Generates a list dispersion
        :param node: search word or phrase
        :type node: str
        :param pos: Part of speech (POS) for each search word 
        :type pos: str or list
        :param regex: Enable regular expression for search word matching
        :type regex: boolean
        :param show_progress: Prints a progress message if value is True
        :type show_progress: boolean
        :return: Dispersion
        :rtype: Dispersion
        """
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
            if not type(pos)==list:
                pos = pos.strip().split(' ')
        # node and dq size 
        node_size = len(node)
        dq = collections.deque(maxlen=node_size)
        # get corpus files in a list 
        files = os.listdir(self.tagged_path)
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
            with open(self.tagged_path + '/' +filename,'r',encoding=self.encoding) as fh:
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
                self.__progress(i, total_files,filename)
        files = None
        # make table
        dispersion = kit_tools.Dispersion(output_path=self.output_path)
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

    def keywords_dispersion(self,keywords,**kwargs):
        """
        Generates a list of keywords dispersion
        :param keywords: Keywords object
        :type keywords: Keywords
        :param lowercase: Letters are converted to lowercase 
        :type lowercase: boolean
        :param limit: limit number of keywords 
        :type limit: int
        :param show_progress: Prints a progress message if value is True
        :type show_progress: boolean
        :return: KeywordsDispersion
        :rtype: KeywordsDispersion
        """
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
        keys = collections.OrderedDict()
        i = 0 
        for row in keywords.df.itertuples(index=False):
            i+=1
            if i > limit:
                break
            keys[row[1]] = row[3]
        keywords = None
        # create keywords dict for points
        keys_points = collections.OrderedDict()
        for k in keys:
            keys_points[k] = list()
        # loop through files
        ptn = re.compile("^\W+$")
        i = 0
        #counter = collections.Counter()
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
                                if re.search(ptn, wt[0]) == None:
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
                self.__progress(i, total_files,filename)
        
        files = None
        # make table
        dispersion = kit_tools.KeywordsDispersion(output_path=self.output_path)
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
    
    def keynessxrange(self,keywords,wfreqinfiles,**kwargs):
        """
        Generates a list of keywords dispersion
        :param keywords: Keywords object
        :type keywords: Keywords
        :param wfreqinfiles: Wfreqinfiles object 
        :type wfreqinfiles: Wfreqinfiles
        :return: Keynessxrange
        :rtype: Keynessxrange
        """
        tb = keywords.df.merge(wfreqinfiles.df,on='WORD',how='left')
        keywords = None
        wfreqinfiles = None
        tb['KEYNESS*RANGE'] = tb['KEYNESS'] * tb['RANGE']
        tb.drop(['KEYNESS','RANGE','%','N_y'],axis=1,inplace=True)
        tb = tb.sort_values('KEYNESS*RANGE', ascending=False)
        tb = tb.reset_index(drop=True)
        tb.columns = ['N', 'WORD','FREQUENCY','KEYNESS*RANGE']
        rank  = [i for i in range(1,len(tb)+1)]
        tb['N'] = rank 
        keyrange = kit_tools.Keynessxrange()
        keyrange.df = tb 
        return keyrange
    
    def compared_collocates(self,coll1,coll2,**kwargs):
        """
        Compares two sets of collocates
        :param coll1: Collocates set 1
        :type coll1: Collocates 
        :param coll2: Collocates set 2
        :type coll2: Collocates
        :param stat_cutoff: Statistic measure cuttoff 
        :type stat_cutoff: int
        :return: ComparedCollocates
        :rtype: ComparedCollocates
        """
        # kwargs
        stat_cutoff = kwargs.get('stat_cutoff',0)
        # get all data in dictionaries
        # and filter association measures with stat_cutoff:
        # words = all words from col1 and col2
        # w1 = col1 data dict
        # w2 = col2 data dict
        words = {}
        w1 = {}
        for row in coll1.df.itertuples(index=False):
            if row[5] >= stat_cutoff:
                k = row[1]
                v = (row[2],row[5])
                w1[k]=v
                if k not in words:
                    words[k]= 0
        coll1 = None 
        w2 = {}
        for row in coll2.df.itertuples(index=False):
            if row[5] >= stat_cutoff:
                k = row[1]
                v = (row[2],row[5])
                w2[k]=v
                if k not in words:
                    words[k]= 0
        coll2 = None
        # put all data together,
        # calculate percent difference
        # and make table   
        tb = []
        tb.append('N\tWORD\tFREQ1\tFREQ2\tASSOCIATION1\tASSOCIATION2\tDIFFERENCE')
        i=0
        for w in sorted(words):
            i+=1
            # get data
            if w in w1:
                w1_f = w1[w][0]
                w1_am = w1[w][1]
            else:
                w1_f = 0
                w1_am = 0.0
            if w in w2:
                w2_f = w2[w][0]
                w2_am = w2[w][1]
            else:
                w2_f = 0
                w2_am = 0.0
            # calcucale percent difference
            if w1_am <= w2_am: # ensure n2 is larger
                n1 = w1_am 
                n2 = w2_am 
            else:
                n1 = w2_am 
                n2 = w1_am 
            pd = round(((n2-n1) / float(n2)) * 100,2)
            # add to table
            tb.append('\t'.join([str(i), str(w),str(w1_f),str(w2_f),str(w1_am),str(w2_am),str(pd)]))

        comparison = kit_tools.ComparedCollocates()
        comparison.read_str('\n'.join(tb))
        tb = None
        comparison.df.sort_values('DIFFERENCE',ascending=True,inplace=True)
        j=0
        for i in comparison.df.index:
            j+=1
            comparison.df.at[i, 'N'] = j
        comparison.df.reset_index(drop=True,inplace=True)
        return comparison 
    
    
    def collocations(self,wordlist,kwic,**kwargs):
        """
        Extracts collocates from kwic
        :param lowercase: Letters are converted to lowercase 
        :type lowercase: boolean
        :param horizon: horizon (from 1 to 5) 
        :type horizon: int
        :param measure: Statistic measure tscore or mutual information 
        :type measure: str
        """
        #kwargs
        lowercase = kwargs.get('lowercase',True) 
        horizon = kwargs.get('horizon',5)
        measure = kwargs.get('measure','tscore')
        # check stat measure
        if measure == 'tscore':
            stat = 1
        elif measure == 'mutual information':
            stat = 2
        # pattern for avoiding punctuation
        ptn = re.compile("^\W+$")
        # wordlist to dic
        freqlist = {}
        tokens = 0
        for row in wordlist.df.itertuples(index=False):
            freqlist[row[1]]=row[2]
            tokens+=row[2]
        wordlist = None 
        # dictionaries and counters
        left_counter = collections.Counter()
        right_counter = collections.Counter()
        words = {}
        node_freq = 0
        for row in kwic.df.itertuples(index=False):
            node_freq+=1
            # get horizons
            if lowercase == True:
                left = list(reversed(row[1].lower().split(' ')[-horizon:]))
                right = row[1].lower().split(' ')[0:horizon]
            else:
                left = list(reversed(row[1].split(' ')[-horizon:]))
                right = row[1].split(' ')[0:horizon]
            # mapping left     
            i = 0
            for word in left:
                if re.search(ptn, word) == None:
                    i+=1
                    left_counter[(i,word)]+=1
                    if word not in words:
                        words[word] = freqlist[word]
            # mapping right
            i=0
            for word in right:
                if re.search(ptn, word) == None:
                    i+=1
                    right_counter[(i,word)]+=1
                    if word not in words:
                        words[word] = freqlist[word]
        kwic = None 
        freqlist = None 
        # make data table
        tb = []
        tb.append('\t'.join(['N','WORD','L5','L4','L3','L2','L1','R1','R2','R3','R4','R5','LEFT','RIGHT','TOTAL','ASSOCIATION']))
        i=0
        for word in words:
            total = 0
            total_left = 0
            total_right = 0
            lv = ['0','0','0','0','0','0']
            for hw,freq  in left_counter.most_common():
                if hw[1] == word:
                    lv[hw[0]] = str(freq)
                    total_left+=freq
            rv = ['0','0','0','0','0','0']
            for hw,freq  in right_counter.most_common():
                if hw[1] == word:
                    rv[hw[0]] = str(freq)
                    total_right+=freq
            # calculate stat measure
            total = total_left + total_right
            if stat == 1:
                m = kit_util.tscore(total, words[word], node_freq, tokens, 1)
            elif stat == 2:
                m = kit_util.mutual_information(total, words[word], node_freq, tokens, 1)
            i+=1
            tb.append('\t'.join([str(i),word,lv[5],lv[4],lv[3],lv[2],lv[1],rv[1],rv[2],rv[3],rv[4],rv[5],str(total_left),str(total_right),str(total),str(m)]))
        words = None
        left_counter =None
        right_counter = None
        collocations = kit_tools.Collocations()
        collocations.read_str('\n'.join(tb))
        tb=None
        collocations.df.sort_values('ASSOCIATION',ascending=False,inplace=True)
        j=0
        for i in collocations.df.index:
            j+=1
            collocations.df.at[i, 'N'] = j
        collocations.df.reset_index(drop=True,inplace=True)
        return collocations


    
        
         
        
         
                         
        
        
        
    
        
        
    
        
                
            
    
   