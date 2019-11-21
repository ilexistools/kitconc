# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
import os,sys   
import nltk
import sqlite3
import collections
import re
import time  
import subprocess
from kitconc import kit_tools
from kitconc import kit_util 
from kitconc.sql_factory import sqlFactory
 
class Corpus (object):
    """This class is the main component for doing corpus analysis in Kitconc."""
        
    def __init__(self,workspace,corpus_name,language='english',**kwargs):
        """
        :param  workspace: A folder path where the corpus will be stored
        :type   workspace: str
        :param corpus_name: A name for corpus identification. 
        :type corpus_name: str
        :param language: The language for text processing. 
        :type language: str 
        """
        # script path
        self.__path = os.path.dirname(os.path.abspath(__file__))
        self.resource_data_path = self.__path + '/data/'
        # check environment
        self.__shell = False
        try:
            from IPython import get_ipython
            shell = get_ipython().__class__.__name__
            if shell == 'ZMQInteractiveShell':
                self.__shell = True   # Jupyter notebook or qtconsole
        except:
            pass  
        # constants
        self.MEASURE_MUTUAL_INFORMATION = 'mutual information'
        self.MEASURE_CHI_SQUARE = 'chi-square'
        self.MEASURE_LOGLIKELIHOOD = 'log-likelihood'
        self.MEASURE_TSCORE = 't-score'
        # regex compile
        self.__regex_punct = re.compile('^\W+$')
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
            self.data_path = self.workspace + self.corpus_name + '/data/'
            self.tagged_path = self.workspace + self.corpus_name + '/data/tagged/'
        else:
            # get kwargs
            encoding = 'utf-8' # default
            # set variables 
            self.corpus_name = corpus_name
            self.language = language 
            self.encoding = encoding
            self.output_path = self.workspace + self.corpus_name + '/output/'
            self.data_path = self.workspace + self.corpus_name + '/data/'
            self.tagged_path = self.workspace + self.corpus_name + '/data/tagged/'
            # create corpus folder
            if not os.path.exists(self.workspace + self.corpus_name):
                os.mkdir(self.workspace + self.corpus_name)
            if not os.path.exists(self.workspace + self.corpus_name + '/data'):
                os.mkdir(self.workspace + self.corpus_name + '/data')
            if not os.path.exists(self.workspace + self.corpus_name + '/output'):
                os.mkdir(self.workspace + self.corpus_name + '/output')
            if not os.path.exists(self.workspace + self.corpus_name + '/data/tagged'):
                os.mkdir(self.workspace + self.corpus_name + '/data/tagged')
            # save info
            self.__save_corpus_info(self.workspace, self.corpus_name, self.language, self.encoding)
            # create databases
            self.__create_indexes_db(self.workspace, self.corpus_name)
            
    # corpus info
    
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
    
    # show progress function
    
    def __progress(self, count, total, suffix=''):
        if self.__shell == False:
            bar_len = 30
            filled_len = int(round(bar_len * count / float(total)))
            percents = round(100.0 * count / float(total), 1)
            bar = '=' * filled_len + '-' * (bar_len - filled_len)
            sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', suffix))
            try:
                sys.stdout.flush()  
            except:
                pass 

    
    # easy connections for sqlite3 databases
    
    def __conn_tagged(self):
        return sqlite3.connect(self.workspace + self.corpus_name + '/data/'  + 'tagged.db',isolation_level=None)
    
    def __conn_indexes(self):
        return sqlite3.connect(self.workspace + self.corpus_name + '/data/'  + 'indexes.db',isolation_level=None)
        
    # functions for creating database files
    
    def __create_indexes_db(self,workspace,corpus_name):
        conn = sqlite3.connect(workspace + corpus_name + '/data/'  + 'indexes.db')
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE textfiles (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                textfile VARCHAR(50) NOT NULL
        );""")
        cursor.execute("""
        CREATE TABLE words (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                word VARCHAR(50) NOT NULL
        );""")
        cursor.execute("""
        CREATE TABLE tags (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                tag VARCHAR(10) NOT NULL
        );""")
        cursor.execute("""
        CREATE TABLE searches (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                textfile_id INTEGER NOT NULL,
                sentence_id INTEGER NOT NULL,
                word_pos INTEGER NOT NULL,
                word_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                loc_id INTEGER NOT NULL
        );""")
        conn.close()

    def __insert_textfiles(self,source_folder):
        files = os.listdir(source_folder)
        conn = self.__conn_indexes()
        cursor = conn.cursor() 
        cursor.execute('begin')
        for filename in files:
            cursor.execute("""
            INSERT INTO textfiles (textfile) VALUES ('%s')
            """ % filename)
        conn.commit()
        conn.close()
    
    def __get_textfiles(self):
        """Generator for returning textfile names"""
        conn = self.__conn_indexes()
        cursor = conn.cursor() 
        cursor.execute("""SELECT * FROM textfiles;""")
        for row in cursor.fetchall():
            yield row 
        conn.close()
    
    def __get_textfilenames(self,source_folder):
        """Generator for returning textfile names"""
        for filename in os.listdir(source_folder):
            yield filename 
    
    def __get_text_lines(self,filename):
        """Generator for returning lines from a textfile"""
        with open(filename,'r',encoding=self.encoding) as fh:
            for line in fh:
                if len(line.strip())!=0:
                    yield line.strip() 
    
        
    def __get_word_indexes(self):
        d = collections.defaultdict()
        conn = self.__conn_indexes()
        cursor = conn.cursor() 
        cursor.execute("""SELECT * FROM words;""")
        for row in cursor.fetchall():
            d[row[1]] = row[0]
        conn.close()
        return d 
    
    def __get_tag_indexes(self):
        d = collections.defaultdict()
        conn = self.__conn_indexes()
        cursor = conn.cursor() 
        cursor.execute("""SELECT * FROM tags;""")
        for row in cursor.fetchall():
            d[row[1]] = row[0]
        conn.close()
        return d
    
    def __get_sentence_indexes(self):
        conn = self.__conn_tagged()
        cursor = conn.cursor() 
        cursor.execute("""SELECT * FROM sentences;""")
        for row in cursor.fetchall():
            yield row
        conn.close()
        
    def __create_indexes(self):
        widx = self.__get_word_indexes()
        tidx = self.__get_tag_indexes() 
        sentences = self.__get_sentence_indexes()
        conn = self.__conn_indexes()
        cursor = conn.cursor() 
        cursor.execute('begin')
        fh = open ('d:/data.tab','a')
        fh.write('\t'.join(['textfile_id','sentence_id','word_id','tag_id']) + '\n')
        for sentence in sentences:
            for token in sentence[2].split(' '):
                tpl = nltk.str2tuple(token)
                #cursor.execute("""
                #INSERT INTO searches (textfile_id,sentence_id,word_id,tag_id) VALUES (%s,%s,%s,%s)
                #""" % (sentence[1],sentence[0],widx[tpl[0]],tidx[tpl[1]]) )
                fh.write( '\t'.join([str(sentence[1]),str(sentence[0]),str(widx[tpl[0]]),str(tidx[tpl[1]])]) + '\n'  )
        fh.close()
        conn.commit()
        conn.close()
    
    def __create_keys(self):
        conn = self.__conn_indexes()
        cursor = conn.cursor() 
        cursor.execute('begin')
        cursor.execute("""
        CREATE INDEX idx_word ON searches (word_id);
        """)
        cursor.execute("""
        CREATE INDEX idx_tag ON searches (tag_id);
        """)
        conn.commit()
        conn.close()
        conn = self.__conn_tagged()
        cursor = conn.cursor() 
        cursor.execute('begin')
        cursor.execute("""
        CREATE INDEX idx_textfile ON sentences (textfile_id);
        """)
        conn.commit()
        conn.close()
    
    # add texts functions
    def __get_source_files(self,source_folder):
        for filename in os.listdir(source_folder):
            yield filename 

    def add_texts(self,source_folder,**kwargs):
        # args 
        show_progress = kwargs.get('show_progress',False)
        tagging = kwargs.get('tagging',True)
        # time it start
        if show_progress == True:
            t0 = time.time()
        # step 1 - tagging text
        subprocess.call(['python',self.__path +'/tagging.py',self.__path,self.workspace,self.corpus_name,self.language,self.encoding,
                         source_folder,str(tagging),str(show_progress)])
        # step 2 - making indexes
        subprocess.call(['python',self.__path +'/indexing.py',self.__path,self.workspace,self.corpus_name,self.language,self.encoding,
                         source_folder,str(tagging),str(show_progress)])
        # step 3 - loading indexes to database
        subprocess.call(['python',self.__path +'/uploading.py',self.__path,self.workspace,self.corpus_name,self.language,self.encoding,
                         source_folder,str(tagging),str(show_progress)])
        # remove tagged folder
        try:
            import shutil 
            shutil.rmtree(self.workspace + self.corpus_name + '/data/tagged',ignore_errors=True)
        except:
            pass 
        # add to info 
        s = []
        s.append('Textfiles:\t%s' % self.textfiles_count())
        s.append('Tokens:\t%s' % self.tokens_count())
        s.append('Types:\t%s' % self.types_count())
        s.append('Type/token ratio:\t%s' % self.typetoken_count())
        s.append('Source:\t%s' % source_folder)
        with open(self.workspace + self.corpus_name + '/info.tab','a',encoding='utf-8') as fh:
            fh.write('\n' + '\n'.join(s))
        # time it end 
        if show_progress == True:
            t1 = time.time()
            total_time = round(t1 - t0,2) 
            print('Total time: %s seconds' % total_time)

    def regexp(self,item):
        return self.__regex_punct.match(item) is not None 

    # Basic statistics info
    
    def tokens_count(self):
        """Returns the number of tokens.
        :return: int
        :rtype: int
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS tokens FROM searches")
        tokens = cursor.fetchone()[0]
        conn.close()
        return tokens 
    
    def types_count(self):
        """Returns the number of types.
        :return: int
        :rtype: int
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS types FROM words")
        types = cursor.fetchone()[0]
        conn.close()
        return types
    
    def typetoken_count(self):
        """Returns the type/token ratio.
        :return: float
        :rtype: float
        """
        tokens = self.tokens_count()
        types = self.types_count()
        typetoken = round((types/tokens)*100,2)
        return typetoken
    
    # textfile functions
    
    def textfile_get_id(self,filename):
        """Returns the id number according to the filename of the text.
        :param  filename: The name of the textfile.
        :type   filename: str
        :return: int
        :rtype: int
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM textfiles WHERE textfile = '%s'" % filename)
        try:
            textfile_id = cursor.fetchone()[0]
        except:
            textfile_id = 0
        conn.close()
        return textfile_id
    
    def textfile_get_filename(self,textfile_id):
        """Returns the filename according to the id of the text.
        :param  textfile_id: The id of the textfile.
        :type   textfile_id: int
        :return: str
        :rtype: str
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("SELECT textfile FROM textfiles WHERE id = %s" % textfile_id)
        try:
            filename = cursor.fetchone()[0]
        except:
            filename = ''
        conn.close()
        return filename
        
    def textfile_get(self,textfile_id):
        """Returns the text according to the textfile id
        :param  textfile_id: The id of the textfile.
        :type   textfile_id: int
        :return: list
        :rtype: list
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("""SELECT GROUP_CONCAT(word,' ') AS words
        FROM searches
        INNER JOIN words ON words.id = searches.word_id 
        WHERE textfile_id = %s
        GROUP BY sentence_id """ % textfile_id)
        text = []
        for row in cursor.fetchall():
            text.append(row[0])
        conn.close()
        return text
    
    def textfile_get_str(self,textfile_id):
        """Returns the text according to the textfile id
        :param  textfile_id: The id of the textfile.
        :type   textfile_id: int
        :return: str
        :rtype: str
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("""SELECT GROUP_CONCAT(word,' ') AS words
        FROM searches
        INNER JOIN words ON words.id = searches.word_id 
        WHERE textfile_id = %s
        GROUP BY sentence_id """ % textfile_id)
        text = []
        for row in cursor.fetchall():
            text.append(row[0])
        conn.close()
        return '\n'.join(text)
    
    def textfile_get_tagged(self,textfile_id):
        """Returns the tagged text according to the textfile id
        :param  textfile_id: The id of the textfile.
        :type   textfile_id: int
        :return: list
        :rtype: list
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("""SELECT GROUP_CONCAT(word,' ') AS words, GROUP_CONCAT(tag,' ') AS tags
        FROM searches
        INNER JOIN words ON words.id = searches.word_id 
        INNER JOIN tags ON tags.id = searches.tag_id
        WHERE textfile_id = %s
        GROUP BY sentence_id """ % textfile_id)
        text = []
        for row in cursor.fetchall():
            words = row[0].strip().split(' ')
            tags = row[1].strip().split(' ')
            sent = []
            for i in range(0, len(words)):
                sent.append((words[i], tags[i]))
            text.append(sent)
        conn.close()
        return text
    
    def textfile_get_tagged_str(self,textfile_id):
        """Returns the tagged text according to the textfile id
        :param  textfile_id: The id of the textfile.
        :type   textfile_id: int
        :return: str
        :rtype: str
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("""SELECT GROUP_CONCAT(word,' ') AS words, GROUP_CONCAT(tag,' ') AS tags
        FROM searches
        INNER JOIN words ON words.id = searches.word_id 
        INNER JOIN tags ON tags.id = searches.tag_id
        WHERE textfile_id = %s
        GROUP BY sentence_id """ % textfile_id)
        text = []
        for row in cursor.fetchall():
            words = row[0].strip().split(' ')
            tags = row[1].strip().split(' ')
            sent = []
            for i in range(0, len(words)):
                sent.append(words[i] + '/' + tags[i])
            text.append(' '.join(sent))
        conn.close()
        return '\n'.join(text)
    
    # textfiles functions
    
    def textfiles_count(self):
        """Returns the number of textfiles.
        :return: int
        :rtype: int
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS texts FROM textfiles")
        textfiles = cursor.fetchone()[0]
        conn.close()
        return textfiles
    
    def textfiles_get_ids(self):
        """Returns the id numbers of textfiles.
        :return: list
        :rtype: list
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM textfiles ORDER BY id")
        n = []
        for row in cursor.fetchall():
            n.append(row[0])
        conn.close()
        return n
    
    def textfiles_get_names(self):
        """Returns the names of textfiles.
        :return: generator
        :rtype: generator
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("SELECT textfile FROM textfiles ORDER BY id")
        for row in cursor.fetchall():
            yield row[0]
        conn.close()
        
    
    # words functions
    
    def word_get_id(self,word):
        """Returns the word id number.
        :param word: word
        :type str: str
        :return: int
        :rtype: int
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("""SELECT id FROM words WHERE word = '%s' """ % word)
        word_id = cursor.fetchone()[0]
        conn.close()
        return word_id
    
    def words_count(self):
        """Returns the number of tokens in the corpus.
        :return: int
        :rtype: int
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS words FROM searches")
        total_tokens = cursor.fetchone()[0]
        conn.close()
        return total_tokens
        
    
    def words_get(self):
        """Returns all words (tokens) in the corpus.
        :return: generator
        :rtype: generator
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT word
        FROM searches
        INNER JOIN words ON words.id = searches.word_id 
        GROUP BY word_id
        """)
        for row in cursor.fetchall():
            yield row[0]
        conn.close()
    
    def words_get_tagged(self):
        """Returns all tagged words in the corpus.
        :return: generator
        :rtype: generator
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT word,tag
        FROM searches
        INNER JOIN words ON words.id = searches.word_id 
        INNER JOIN tags ON tags.id = searches.tag_id 
        GROUP BY word_id
        """)
        for row in cursor.fetchall():
            yield (row[0],row[1])
        conn.close()
        
    def tagged_words_get(self):
        """Returns all tagged words in the corpus.
        :return: generator
        :rtype: generator
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT word,tag
        FROM searches
        INNER JOIN words ON words.id = searches.word_id 
        INNER JOIN tags ON tags.id = searches.tag_id 
        GROUP BY word_id
        """)
        for row in cursor.fetchall():
            yield (row[0],row[1])
        conn.close()
    
    # sentences functions
    
    def sentences_count(self):
        """Returns the number of sentences in the corpus.
        :return: int
        :rtype: int
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT(sentence_id)) FROM searches")
        sentences = cursor.fetchone()[0]
        conn.close()
        return sentences
    
    def sentences_get(self):
        """Returns all sentences in the corpus
        :return: generator
        :rtype: generator
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT GROUP_CONCAT(word,' ') AS words
        FROM searches
        INNER JOIN words ON words.id = searches.word_id 
        INNER JOIN tags ON tags.id = searches.tag_id
        GROUP BY sentence_id
        """)
        for row in cursor.fetchall():
            yield row[0].split(' ')
        conn.close()
        
    # sentence functions
    
    def sentence_get(self,sent_id):
        """Returns a sentence by id number.
        :param sent_id: Sentence identification number
        :type int: int
        :return: str
        :rtype: str
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT GROUP_CONCAT(word,' ') AS sentence
        FROM searches
        INNER JOIN words ON words.id = searches.word_id
        WHERE sentence_id = %s
        GROUP BY sentence_id 
        """ % str(sent_id))
        sentence = cursor.fetchone()[0]
        conn.close()
        return sentence
    
    def tagged_sentences_get(self):
        """Returns all tagged sentences in the corpus
        :return: generator
        :rtype: generator
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT GROUP_CONCAT(word,' ') AS words, GROUP_CONCAT(tag,' ') AS tags
        FROM searches
        INNER JOIN words ON words.id = searches.word_id 
        INNER JOIN tags ON tags.id = searches.tag_id
        GROUP BY sentence_id 
        """)
        for row in cursor.fetchall():
            tagged_sent = []
            words = row[0].split(' ')
            tags = row[1].split(' ')
            row = None
            for i in range(0,len(words)):
                tagged_sent.append((words[i],tags[i]))
            yield tagged_sent
        conn.close()
    
    def tagged_sentence_get(self,sent_id):
        """Returns a tagged sentence by id number.
        :param sent_id: Sentence identification number
        :type int: int
        :return: list
        :rtype: list
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT GROUP_CONCAT(word,' ') AS words, GROUP_CONCAT(tag,' ') AS tags
        FROM searches
        INNER JOIN words ON words.id = searches.word_id 
        INNER JOIN tags ON tags.id = searches.tag_id
        WHERE sentence_id = %s
        GROUP BY sentence_id 
        """ % str(sent_id))
        r = cursor.fetchone()
        conn.close()
        tagged_sent = []
        words = r[0].split(' ')
        tags = r[1].split(' ')
        r = None
        for i in range(0,len(words)):
            tagged_sent.append((words[i],tags[i]))
        return tagged_sent 
    
    
    def tag_get_id(self,tag):
        """Returns the tag id number.
        :param tag: tag
        :type str: str
        :return: int
        :rtype: int
        """
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute("""SELECT id FROM tags WHERE tag =  '%s' """ % tag)
        tag_id = cursor.fetchone()[0]
        conn.close()
        return tag_id
        
        
              
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
        # args
        show_progress=kwargs.get('show_progress',False)
        lowercase = kwargs.get('lowercase',True)
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        # process
        tokens = self.tokens_count()
        types = self.types_count()
        typetoken = round((types/tokens)*100,2)
        # functions
        def tolower(s):
            return str(s).lower()
        # conn
        conn = self.__conn_indexes()
        conn.create_function("regexp", 1, self.regexp)
        conn.create_function("tolower", 1, tolower)
        cursor = conn.cursor()
        cursor.execute(sqlFactory().wordlist(lowercase))
        s = []
        s.append("N\tWORD\tFREQUENCY\t%")
        i = 0
        hapax=0
        for row in cursor.fetchall():
            i+=1
            if row[1] == 1:
                hapax+=1
            s.append( '\t'.join([str(i),str(row[0]), str(row[1]), str(round((row[1]/tokens)*100,2))] ))
            if show_progress == True:
                self.__progress(i, types, '')
        conn.close()
        wlst = kit_tools.Wordlist(tokens=tokens,types=types,typetoken=typetoken, hapax=hapax)
        wlst.read_str('\n'.join(s))
        # time end
        if show_progress == True:
            self.__progress(types, types, '')
            t1 = time.time()
            total_time = round(t1 - t0,2) 
            print('')
            print('Total time: %s seconds' % total_time)
        return  wlst  
    
    def keywords(self,wordlist,**kwargs):
        """
        Extracts keywords from a wordlist
        :param wordlist: Wordlist object
        :type wordlist: Wordlist
        :param measure: A statistical measure to use (log-likelihood or chi square)
        :type measure : str
        :param stoplist: a list of words to be filtered out
        :type stoplist: list
        :param show_progress: Prints a progress message if value is True
        :type show_progress: boolean
        :return: Keywords
        :rtype: Keywords
        """
        #args
        measure = kwargs.get('measure','log-likelihood')
        stoplist = kwargs.get('stoplist',[])
        show_progress=kwargs.get('show_progress',False)
        # get statistics measures
        if measure == 'log-likelihood':
            stat = 1
        elif measure == 'chi-square':
            stat = 2
        else:
            stat = 1
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        # load reflist 
        reflist,tk_refc = kit_util.keywords_reference(self.__path + '/data/reflist_' + self.language + '.tab')
        # extract keywords
        wfreq = {}
        counter = collections.Counter()
        tk_stdc = wordlist.tokens 
        i = 0
        total = len(wordlist.df)
        for row in wordlist.df.itertuples(index=False):
            wfreq[str(row[1])] = int(row[2])
            freq_refc = 0
            if str(row[1]).lower() in reflist:
                freq_refc = reflist[str(row[1])]
            if stat == 1:
                keyness = kit_util.ll(int(row[2]),freq_refc,tk_stdc,tk_refc)
            elif stat == 2:
                keyness = kit_util.chi_square (int(row[2]),freq_refc,tk_stdc,tk_refc)
            if row[1] not in stoplist:
                if str(row[1]) not in counter:
                    counter[str(row[1])] = keyness
            # print progress
            if show_progress == True:
                i+=1
                self.__progress(i, total,'')
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
        # time end
        if show_progress == True:
            t1 = time.time()
            total_time = round(t1 - t0,2) 
            print('')
            print('Total time: %s seconds' % total_time) 
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
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        # process
        tokens = self.tokens_count()
        conn = self.__conn_indexes()
        def tolower(s):
            return str(s).lower()
        conn.create_function("regexp", 1, self.regexp)
        conn.create_function("tolower", 1, tolower)
        cursor = conn.cursor()
        cursor.execute(sqlFactory().wtfreq(lowercase))
        s = []
        s.append("N\tWORD\tTAG\tFREQUENCY\t%")
        i = 0
        j = 0
        for row in cursor.fetchall():
            j+=row[2]
            i+=1
            s.append( '\t'.join([str(i),str(row[0]), str(row[1]),str(row[2]), str(round((row[2]/tokens)*100,2))] ))
            if show_progress == True:
                self.__progress(j, tokens, '')
        conn.close()
        wt = kit_tools.WTfreq()
        wt.read_str('\n'.join(s))
        s = None 
        # time end
        if show_progress == True:
            self.__progress(100,100, '')
            t1 = time.time()
            total_time = round(t1 - t0,2) 
            print('')
            print('Total time: %s seconds' % total_time)
        return wt
    
    def wfreqinfiles(self,**kwargs):
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
        lowercase = kwargs.get('lowercase',True)
        show_progress=kwargs.get('show_progress',False)
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        # process
        types = self.types_count()
        ntexts = self.textfiles_count()
        conn = self.__conn_indexes()
        def tolower(s):
            return str(s).lower()
        conn.create_function("regexp", 1, self.regexp)
        conn.create_function('tolower',1,tolower)
        cursor = conn.cursor()
        cursor.execute(sqlFactory().wfreqinfiles(lowercase) )
        s = []
        s.append("N\tWORD\tRANGE\t%")
        i = 0
        for row in cursor.fetchall():
            i+=1
            s.append( '\t'.join([str(i),str(row[0]), str(row[1]),str(round((row[1]/ntexts)*100,2))] ))
            if show_progress == True:
                self.__progress(i, types, '')
        conn.close()
        fif = kit_tools.Wfreqinfiles()
        fif.read_str('\n'.join(s))
        s = None 
        # time end
        if show_progress == True:
            self.__progress(100,100, '')
            t1 = time.time()
            total_time = round(t1 - t0,2) 
            print('')
            print('Total time: %s seconds' % total_time)
        return fif
    
    def kwic(self,node,**kwargs):
        """
        Generates concordance lines.
        :param node: Search word or phrase (max. 4 words)
        :type node : str
        :param pos: Part of speech (POS) for each search word 
        :type pos: str or list
        :param case_sensitive: Enable regular expression for search word matching
        :type case_sensitive: boolean
        :param regexp: Enable regular expression for search matching
        :type regexp: boolean
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
        node = node.strip()
        pos = kwargs.get('pos',None)
        case_sensitive = kwargs.get('case_sensitive',False)
        regexp = kwargs.get('regexp',False)
        horizon = kwargs.get('horizon',10)
        limit = kwargs.get('limit',None)
        show_progress = kwargs.get('show_progress',False)
        # deal with args
        node_length = len(node.split(' '))
        if pos !=None:
            if type(pos)!= list:
                pos = pos.strip().split(' ')
            s = []
            for tag in pos:
                s.append("'" + tag  +"'")
            pos = ','.join(s)
        hleft = horizon + (node_length-1)
        hright = horizon 
        if case_sensitive == True:
            compare_operator = ' = '
        else:
            compare_operator = ' LIKE '
        if limit != None:
            limit_results= 'LIMIT %s' % limit 
        else: 
            limit_results= ''
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        # process
        # create connection
        conn = self.__conn_indexes()
        # set custom functions
        if node_length > 1:
            self.dq = collections.deque(maxlen=node_length)
            def join_words(s): # join words
                self.dq.append(s)
                return ' '.join(self.dq)
            self.dqt = collections.deque(maxlen=node_length)
            def join_tags(s): # join tags
                self.dqt.append(s)
                return ' '.join(self.dqt)
            conn.create_function("join_words", 1, join_words)
            conn.create_function("join_tags", 1, join_tags)
        if regexp == True:
            self.reg_word_p = re.compile(node)
            def regx(s): # regexp
                return self.reg_word_p.match(s) is not None
            conn.create_function("regx", 1, regx)
        cursor = conn.cursor()
        cursor.execute('begin')
        # delete previous temporary table
        cursor.execute(sqlFactory().kwic_drop_temporary_table())
        # search node
        if show_progress == True:
            print('Searching node...' ) 
        cursor.execute(sqlFactory().kwic_search_node(node_length, node, pos, compare_operator, regexp, limit_results))
        # count results
        cursor.execute(sqlFactory().kwic_count_results())
        total_results = cursor.fetchone()[0]
        if show_progress == True:
            print('Results: %s ' % total_results)
        # get kwic data
        if show_progress == True:
            print('Getting context...' )
        cursor.execute(sqlFactory().kwic_data(hleft, hright))
        # format data
        if show_progress == True:
            print('Creating KWIC...')
        i=0
        s=[]
        s.append('N\tLEFT\tNODE\tRIGHT\tFILENAME\tTOKEN_ID\tSENT_ID\tFILE_ID')
        for row in cursor.fetchall():
            i+=1
            conc=row[0].split(' ')
            s.append(str(i) + '\t' + ' '.join(conc[0:horizon]) + '\t' + ' '.join(conc[horizon:horizon++node_length])  + '\t' + ' '.join(conc[horizon+node_length:]) + '\t' + row[1] + '\t' + str(row[2]) + '\t' + str(row[3]) + '\t' + str(row[4]))
            if show_progress == True:
                self.__progress(i,total_results, '')      
        # delete temporary table
        cursor.execute(sqlFactory().kwic_drop_temporary_table())
        # close connection
        conn.commit()                        
        conn.close()
        # make Kwic object
        k = kit_tools.Kwic(node_length=node_length)
        k.read_str('\n'.join(s))
        del s 
        # time end
        if show_progress == True:
            t1 = time.time()
            total_time = round(t1 - t0,2) 
            print('')
            print('Total time: %s seconds' % total_time)
        return k
    
    def concordance(self,node,**kwargs):
        """
        Generates concordance lines.
        :param node: Search word or phrase (max. 4 words)
        :type node : str
        :param pos: Part of speech (POS) for each search word 
        :type pos: str or list
        :param case_sensitive: Enable regular expression for search word matching
        :type case_sensitive: boolean
        :param regexp: Enable regular expression for search matching
        :type regexp: boolean
        :param limit: Number of concordance lines to return
        :type limit: int
        :param show_progress: Prints a progress message if value is True
        :type show_progress: boolean
        :return: Concordance
        :rtype: Concordance
        """
        # args
        node = node.strip()
        pos = kwargs.get('pos',None)
        case_sensitive = kwargs.get('case_sensitive',False)
        regexp = kwargs.get('regexp',False)
        limit = kwargs.get('limit',None)
        show_progress = kwargs.get('show_progress',False)
        # deal with args
        node_length = len(node.split(' '))
        if pos !=None:
            if type(pos)!= list:
                pos = pos.strip().split(' ')
            s = []
            for tag in pos:
                s.append("'" + tag  +"'")
            pos = ','.join(s)
        if case_sensitive == True:
            compare_operator = ' = '
        else:
            compare_operator = ' LIKE '
        if limit != None:
            limit_results= 'LIMIT %s' % limit 
        else: 
            limit_results= ''
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        # process
        # create connection
        conn = self.__conn_indexes()
        # set custom functions
        if node_length > 1:
            self.dq = collections.deque(maxlen=node_length)
            def join_words(s): # join words
                self.dq.append(s)
                return ' '.join(self.dq)
            self.dqt = collections.deque(maxlen=node_length)
            def join_tags(s): # join tags
                self.dqt.append(s)
                return ' '.join(self.dqt)
            conn.create_function("join_words", 1, join_words)
            conn.create_function("join_tags", 1, join_tags)
        if regexp == True:
            self.reg_word_p = re.compile(node)
            def regx(s): # regexp
                return self.reg_word_p.match(s) is not None
            conn.create_function("regx", 1, regx)
        cursor = conn.cursor()
        cursor.execute('begin')
        # delete previous temporary table
        cursor.execute(sqlFactory().conc_drop_temporary_table())
        # search node
        if show_progress == True:
            print('Searching node...' ) 
        cursor.execute(sqlFactory().conc_search_node(node_length, node, pos, compare_operator, regexp, limit_results))
        # count results
        cursor.execute(sqlFactory().conc_count_results())
        total_results = cursor.fetchone()[0]
        if show_progress == True:
            print('Results: %s ' % total_results)
        # get kwic data
        if show_progress == True:
            print('Getting context...' )
        cursor.execute(sqlFactory().conc_data())
        # format data
        if show_progress == True:
            print('Creating concordances...')
        i=0
        s=[]
        s.append('N\tCONCORDANCE\tFILENAME\tTOKEN_ID\tSENT_ID\tFILE_ID')
        for row in cursor.fetchall():
            i+=1
            s.append(str(i) + '\t' + str(row[0]) + '\t' + str(row[1]) + '\t' + str(row[2] - (node_length-1)  ) + '\t' + str(row[3]) + '\t' + str(row[4]))
            if show_progress == True:
                self.__progress(i,total_results, '')      
        # delete temporary table
        cursor.execute(sqlFactory().conc_drop_temporary_table())
        # close connection
        conn.commit()                        
        conn.close()
        # make Kwic object
        concordance = kit_tools.Concordance(node_length=node_length)
        concordance.read_str('\n'.join(s))
        del s 
        # time end
        if show_progress == True:
            t1 = time.time()
            total_time = round(t1 - t0,2) 
            print('')
            print('Total time: %s seconds' % total_time)
        return concordance 
    
    def collocates(self,node,**kwargs):
        """
        Extracts a list of collocates.
        :param node: search word
        :type node : str
        :param pos: Part of speech (POS) for each search word 
        :type pos: str or list
        :param coll_pos: POS for filtering collocates
        :type coll_pos: str or list
        :param case_sensitive: Enable regular expression for search word matching
        :type case_sensitive: boolean
        :param regexp: Enable regular expression for search matching
        :type regexp: boolean
        :param left_span: Left and right horizon of words
        :type left_span: int
        :param right_span: Left and right horizon of words
        :type right_span: int
        :param lowercase: Letters are converted to lowercase 
        :type lowercase: boolean
        :param measure: Statistic measure tscore or mutual information (default: tscore)
        :type measure: str
        :param limit: Number of concordance lines to return
        :type limit: int
        :param show_progress: Prints a progress message if value is True
        :type show_progress: boolean
        :return: Collocates
        :rtype: Collocates
        """
        # args
        node = node.strip()
        pos = kwargs.get('pos',None)
        coll_pos = kwargs.get('coll_pos',None)
        case_sensitive = kwargs.get('case_sensitive',False)
        regexp = kwargs.get('regexp',False)
        left_span = kwargs.get('left_span',5)
        right_span = kwargs.get('right_span',5)
        lowercase = kwargs.get('lowercase',True)
        measure = kwargs.get('measure',1)
        limit = kwargs.get('limit',None)
        show_progress = kwargs.get('show_progress',False)
        # deal with args
        node_length = len(node.split(' '))
        if pos !=None:
            if type(pos)!= list:
                pos = pos.strip().split(' ')
            s = []
            for tag in pos:
                s.append("'" + tag  +"'")
            pos = ','.join(s)
        if coll_pos !=None:
            if type(coll_pos)!= list:
                coll_pos = coll_pos.strip().split(' ')
            s = []
            for tag in coll_pos:
                s.append(str(self.tag_get_id(tag)))
            coll_pos = ','.join(s)
        if measure == 't-score':
            measure = 1
        elif measure == 'mutual information':
            measure = 2 
        if case_sensitive == True:
            compare_operator = ' = '
        else:
            compare_operator = ' LIKE '
        if limit != None:
            limit_results= 'LIMIT %s' % limit 
        else: 
            limit_results= ''
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        # process
        # create connection
        conn = self.__conn_indexes()
        # set custom functions
        if node_length > 1:
            self.dq = collections.deque(maxlen=node_length)
            def join_words(s): # join words
                self.dq.append(s)
                return ' '.join(self.dq)
            self.dqt = collections.deque(maxlen=node_length)
            def join_tags(s): # join tags
                self.dqt.append(s)
                return ' '.join(self.dqt)
            conn.create_function("join_words", 1, join_words)
            conn.create_function("join_tags", 1, join_tags)
        if regexp == True:
            self.reg_word_p = re.compile(node)
            def regx(s): # regexp
                return self.reg_word_p.match(s) is not None
            conn.create_function("regx", 1, regx)
        def tolower(s):
            return str(s).lower()
        conn.create_function("tolower", 1, tolower)
        conn.create_function("regexp", 1, self.regexp)
        cursor = conn.cursor()
        cursor.execute('begin') 
        # delete previous temporary table
        cursor.execute(sqlFactory().coll_drop_temporary_table())
        # search node
        if show_progress == True:
            print('Searching node...' ) 
        sql = sqlFactory().coll_search_node(node_length, node, pos, compare_operator, regexp, limit_results)
        cursor.execute(sql)
        # count results
        cursor.execute(sqlFactory().coll_count_results())
        total_results = cursor.fetchone()[0]
        if show_progress == True:
            print('Results: %s ' % total_results)
        # making wordlist
        tokens = self.tokens_count()
        cursor.execute(sqlFactory().coll_wordlist(lowercase))
        wordlist = collections.defaultdict()
        for row in cursor.fetchall():
            wordlist[str(row[0])] = int(row[1])
        # get kwic data
        if show_progress == True:
            print('Getting context...' )
        all_collocates = collections.defaultdict()
        # count collocates from the left
        sql = sqlFactory().coll_left_data(lowercase,node_length,left_span,coll_pos)
        cursor.execute(sql)
        left_wordlist = collections.defaultdict()
        for row in cursor.fetchall():
            left_wordlist[str(row[0])] = int(row[1])
            all_collocates[row[0]] = None
        # count collocates from the right
        sql = sqlFactory().coll_right_data(lowercase,node_length,right_span,coll_pos)
        cursor.execute(sql)
        right_wordlist = collections.defaultdict()
        for row in cursor.fetchall():
            right_wordlist[str(row[0])] = int(row[1])
            if row[0] not in all_collocates:
                all_collocates[row[0]] = None 
        # format data
        if show_progress == True:
            print('Counting collocates...')
        i=0
        total = len(all_collocates)
        s=[]
        s.append('N\tWORD\tFREQUENCY\tLEFT\tRIGHT\tASSOCIATION')
        for k in all_collocates:
            i+=1
            if k in left_wordlist:
                left_count = left_wordlist[k]
            else:
                left_count=0
                 
            if k in right_wordlist:
                right_count = right_wordlist[k]
            else:
                right_count=0
                
            if measure == 1:
                stat=kit_util.tscore(left_count+right_count, total_results, wordlist[k], tokens, h=1)
            else:
                stat=kit_util.mutual_information(left_count+right_count, total_results, wordlist[k], tokens, h=1)
            
            s.append(str(i) + '\t' + k + '\t' + str(left_count+right_count) + '\t' + str(left_count) + '\t' + str(right_count) + '\t' + str(stat) )
            
            if show_progress == True:
                self.__progress(i,total, '')    
        # delete wordlists
        del wordlist 
        del left_wordlist 
        del right_wordlist   
        # delete temporary table
        cursor.execute(sqlFactory().coll_drop_temporary_table())
        # close connection
        conn.commit()                        
        conn.close()
        # make Collocates object
        # save
        coll = kit_tools.Collocates()
        coll.read_str('\n'.join(s))
        # sort by association and reset index
        coll.df.sort_values('ASSOCIATION',ascending=False,inplace=True)
        coll.df.N = [(i+1)for i in range(0,len(coll.df))]
        coll.df.reset_index(drop=True,inplace=True)
        del s
        # time end
        if show_progress == True:
            t1 = time.time()
            total_time = round(t1 - t0,2) 
            print('')
            print('Total time: %s seconds' % total_time)
        return coll
    
    def compared_collocates(self,coll1,coll2,**kwargs):
        """
        Compares two sets of collocates.
        :param coll1: Collocates set 1
        :type coll1: Collocates 
        :param coll2: Collocates set 2
        :type coll2: Collocates
        :param stat_cutoff: Statistic measure cuttoff (default: 0)
        :type stat_cutoff: int
        :param show_progress: Prints a progress message if value is True
        :type show_progress: boolean
        :return: ComparedCollocates
        :rtype: ComparedCollocates
        """
        # kwargs
        stat_cutoff = kwargs.get('stat_cutoff',0)
        show_progress = kwargs.get('show_progress',False)
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        # get all data in dictionaries
        # and filter association measures with stat_cutoff:
        # words = all words from col1 and col2
        # w1 = col1 data dict
        # w2 = col2 data dict
        words = collections.defaultdict()
        w1 = collections.defaultdict()
        for row in coll1.df.itertuples(index=False):
            if row[5] >= stat_cutoff:
                k = row[1]
                v = (row[2],row[5])
                w1[k]=v
                if k not in words:
                    words[k]= 0
        del coll1 
        w2 = collections.defaultdict()
        for row in coll2.df.itertuples(index=False):
            if row[5] >= stat_cutoff:
                k = row[1]
                v = (row[2],row[5])
                w2[k]=v
                if k not in words:
                    words[k]= 0
        del coll2
        # put all data together,
        # calculate percent difference
        # and make table   
        s = []
        s.append('N\tWORD\tFREQ1\tFREQ2\tASSOCIATION1\tASSOCIATION2\tDIFFERENCE')
        i=0
        total = len(words)
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
            s.append('\t'.join([str(i), str(w),str(w1_f),str(w2_f),str(w1_am),str(w2_am),str(pd)]))
            if show_progress == True:
                self.__progress(i,total, '')

        comparison = kit_tools.ComparedCollocates()
        comparison.read_str('\n'.join(s))
        del s 
        comparison.df.sort_values('DIFFERENCE',ascending=True,inplace=True)
        comparison.df.N = [(i+1)for i in range(0,len(comparison.df))]
        comparison.df.reset_index(drop=True,inplace=True)
        # time end
        if show_progress == True:
            t1 = time.time()
            total_time = round(t1 - t0,2) 
            print('')
            print('Total time: %s seconds' % total_time)
        return comparison 

    
    def collocations(self,kwic,**kwargs):
        """
        Extracts collocates from kwic
        :param lowercase: Letters are converted to lowercase (default: True)
        :type lowercase: boolean
        :param horizon: horizon (from 1 to 5 - default: 5) 
        :type horizon: int
        :param measure: Statistic measure tscore or mutual information (default: tscore)
        :type measure: str
        :param show_progress: Prints a progress message if value is True
        :type show_progress: boolean
        :return: Collocations
        :rtype: Collocations
        """
        #kwargs
        lowercase = kwargs.get('lowercase',True) 
        horizon = kwargs.get('horizon',5)
        measure = kwargs.get('measure','tscore')
        show_progress= kwargs.get('show_progress',False)
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        # check stat measure
        if measure == 'tscore':
            stat = 1
        elif measure == 'mutual information':
            stat = 2
        # pattern for avoiding punctuation
        ptn = re.compile("^\W+$")
        # create connection
        conn = self.__conn_indexes()
        def tolower(s):
            return str(s).lower()
        conn.create_function("tolower", 1, tolower)
        cursor = conn.cursor()
        # wordlist to dic
        tokens = self.tokens_count()
        cursor.execute(sqlFactory().coll_wordlist(lowercase))
        freqlist = collections.defaultdict()
        for row in cursor.fetchall():
            freqlist[str(row[0])] = int(row[1]) 
        # close connection
        conn.close()
        # dictionaries and counters
        left_counter = collections.Counter()
        right_counter = collections.Counter()
        words = collections.defaultdict()
        node_freq = 0
        total = len(kwic.df)
        j=0
        for row in kwic.df.itertuples(index=False):
            j+=1
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
            if show_progress == True:
                self.__progress(j,total, '')
        del kwic  
        del freqlist 
        # make data table
        s = []
        s.append('\t'.join(['N','WORD','L5','L4','L3','L2','L1','R1','R2','R3','R4','R5','LEFT','RIGHT','TOTAL','ASSOCIATION']))
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
            s.append('\t'.join([str(i),word,lv[5],lv[4],lv[3],lv[2],lv[1],rv[1],rv[2],rv[3],rv[4],rv[5],str(total_left),str(total_right),str(total),str(m)]))
        words = None
        left_counter =None
        right_counter = None
        collocations = kit_tools.Collocations()
        collocations.read_str('\n'.join(s))
        del s
        collocations.df.sort_values('ASSOCIATION',ascending=False,inplace=True)
        collocations.df.N = [(i+1)for i in range(0,len(collocations.df))]
        collocations.df.reset_index(drop=True,inplace=True)
        # time end
        if show_progress == True:
            t1 = time.time()
            total_time = round(t1 - t0,2) 
            print('')
            print('Total time: %s seconds' % total_time)
        return collocations
    
    def clusters(self,word,**kwargs):
        """
        Generates a list of clusters
        :param word: search word
        :type word: str
        :param pos: Part of speech (POS) for each search word 
        :type pos: str or list
        :param size: size of the cluster
        :type size: int
        :param lowercase: Letters are converted to lowercase 
        :type lowercase: boolean
        :param min_freq: minimum frequency of the cluster
        :type min_freq: int
        :param min_range: minimum range frequency 
        :type min_range: int
        :param show_progress: Prints a progress message if value is True
        :type show_progress: boolean
        :return: Clusters
        :rtype: Clusters
        """
        # args
        word = word.strip()
        pos = kwargs.get('pos',None)
        size = kwargs.get('size',3)
        lowercase = kwargs.get('lowercase',True)
        min_freq = kwargs.get('min_freq',1)
        min_range = kwargs.get('min_range',1)
        show_progress = kwargs.get('show_progress',False)
        # deal with args
        if pos !=None:
            if type(pos)!= list:
                pos = pos.strip().split(' ')
            s = []
            for tag in pos:
                s.append(self.tag_get_id(tag))
            pos = s 
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        # create connection
        conn = self.__conn_indexes()
        def tolower(s):
            return str(s).lower()
        conn.create_function('tolower',1,tolower)
        cursor = conn.cursor()
        cursor.execute(sqlFactory().clusters_searches_all(lowercase)) 
        total_texts = self.textfiles_count()
        dq_words = collections.deque(maxlen=size)
        dq_tags = collections.deque(maxlen=size)
        counter = collections.Counter()
        dic_clusters = collections.defaultdict()
        idx = 0
        ptn = re.compile("^\W+$")
        file_id = 0 
        total_lines = 0
        # remove previous temp file for creating a new one
        if os.path.exists(self.data_path + '/temp.tab'):
            os.remove(self.data_path + '/temp.tab')
        # search corpus for matches and save counts for each file
        if show_progress == True:
            print('Searching node...' )
        for row in cursor.fetchall():
            if file_id == 0:
                file_id = row[2]
            if row[2] != file_id:
                for k,v in counter.most_common():
                    if k not in dic_clusters:
                        idx+=1
                        dic_clusters[k] = idx 
                    total_lines+=1
                    with open(self.data_path + '/temp.tab','a',encoding=self.encoding) as fh:
                        fh.write(str(dic_clusters[k]) + '\t' + str(v) + '\t' + str(file_id) + '\n')
                file_id = row[2]
                counter.clear()
            dq_words.append(row[0])
            dq_tags.append(row[1])
            if len(dq_words) == size:
                if word in dq_words:
                    flag = True
                    for item in dq_words:
                        if ptn.match(item):
                            flag = False 
                    if pos !=None:
                        if [tag for tag in dq_tags] != pos:
                            flag = False
                    if flag == True:
                        counter[' '.join(dq_words)]+=1
        for k,v in counter.most_common():
            if k not in dic_clusters:
                idx+=1
                dic_clusters[k] = idx
            total_lines+=1
            with open(self.data_path + '/temp.tab','a',encoding=self.encoding) as fh:
                fh.write(str(dic_clusters[k]) + '\t' + str(v) + '\t' + str(file_id) + '\n')
        counter.clear()
        # close connection
        conn.close()
        del dq_words
        del dq_tags 
        if show_progress == True:
            print('Results: %s' % total_lines)
        if total_lines != 0:
            # make generator for reading temp file
            def get_temp_clusters():
                with open(self.data_path + '/temp.tab','r',encoding=self.encoding) as fh:
                    for line in fh:
                        if len(line.strip())!=0:
                            yield [int(i) for i in line.strip().split('\t')] 
            # get data from generator for general and range counting
            if show_progress == True:
                print('Counting clusters...' )
            range_counter = collections.Counter()
            i = 0
            for line in get_temp_clusters():
                i+=1
                counter[line[0]] += line[1]
                if line[0] not in range_counter:
                    range_counter[line[0]] = [line[2]]
                else:
                    range_counter[line[0]]+= [line[2]]
                if show_progress == True:
                    self.__progress(i,total_lines, '')
            # format data
            dic_clusters = {v: k for k, v in dic_clusters.items()} # reverse keys and values
            s = []
            s.append("N\tCLUSTER\tFREQUENCY\tRANGE\t%")
            i = 0
            j=0
            total_lines = len(counter)
            for k,v in counter.most_common():
                j+=1
                if v >= min_freq:
                    r = len(collections.Counter(range_counter[k]))
                    if r >= min_range:
                        i+=1
                        p =  round((r / total_texts)*100,2)
                        s.append("%s\t%s\t%s\t%s\t%s" % (i,dic_clusters[k],v, r, p))
                if show_progress == True:
                    self.__progress(j,total_lines, '')
            del dic_clusters 
            del counter 
            del range_counter
            # make clusters
            clusters = kit_tools.Clusters()
            clusters.read_str('\n'.join(s))
            del s
            # remove temp file 
            if os.path.exists(self.data_path + '/temp.tab'):
                os.remove(self.data_path + '/temp.tab')
            # time end
            if show_progress == True:
                t1 = time.time()
                total_time = round(t1 - t0,2) 
                print('')
                print('Total time: %s seconds' % total_time) 
        else:
            s = []
            s.append("N\tCLUSTER\tFREQUENCY\tRANGE\t%")
            clusters = kit_tools.Clusters()
            clusters.read_str('\n'.join(s))
        return clusters 
    
    def ngrams(self,**kwargs):
        """
        Generates a list of n-grams
        :param pos: Part of speech (POS) for each word 
        :type pos: str or list
        :param size: size of the cluster
        :type size: int
        :param lowercase: Letters are converted to lowercase 
        :type lowercase: boolean
        :param min_freq: minimum frequency of the cluster
        :type min_freq: int
        :param min_range: minimum range frequency 
        :type min_range: int
        :param show_progress: Prints a progress message if value is True
        :type show_progress: boolean
        :return: Clusters
        :rtype: Clusters
        """
        # args
        pos = kwargs.get('pos',None)
        size = kwargs.get('size',3)
        lowercase = kwargs.get('lowercase',True)
        min_freq = kwargs.get('min_freq',1)
        min_range = kwargs.get('min_range',1)
        show_progress = kwargs.get('show_progress',False)
        # deal with args
        if pos !=None:
            if type(pos)!= list:
                pos = pos.strip().split(' ')
            s = []
            for tag in pos:
                s.append(self.tag_get_id(tag))
            pos = s 
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        # create connection
        conn = self.__conn_indexes()
        def tolower(s):
            return str(s).lower()
        conn.create_function('tolower',1,tolower)
        cursor = conn.cursor()
        cursor.execute(sqlFactory().clusters_searches_all(lowercase)) 
        total_texts = self.textfiles_count()
        dq_words = collections.deque(maxlen=size)
        dq_tags = collections.deque(maxlen=size)
        counter = collections.Counter()
        dic_clusters = collections.defaultdict()
        idx = 0
        ptn = re.compile("^\W+$")
        file_id = 0 
        total_lines = 0
        # remove previous temp file for creating a new one
        if os.path.exists(self.data_path + '/temp.tab'):
            os.remove(self.data_path + '/temp.tab')
        # search corpus for matches and save counts for each file
        if show_progress == True:
            print('Searching node...' )
        offset = 100000
        s = []
        j=0 
        for row in cursor.fetchall():
            if file_id == 0:
                file_id = row[2]
            if row[2] != file_id:
                for k,v in counter.most_common():
                    if k not in dic_clusters:
                        idx+=1
                        dic_clusters[k] = idx 
                    total_lines+=1
                    j+=1
                    s.append(str(dic_clusters[k]) + '\t' + str(v) + '\t' + str(file_id))
                    if j == offset:
                        with open(self.data_path + '/temp.tab','a',encoding=self.encoding) as fh:
                            fh.write('\n'.join(s))
                        s = []
                        j = 0
                file_id = row[2]
                counter.clear()
            dq_words.append(row[0])
            dq_tags.append(row[1])
            if len(dq_words) == size:
                flag = True
                for item in dq_words:
                    if ptn.match(item):
                        flag = False 
                if pos !=None:
                    if [tag for tag in dq_tags] != pos:
                        flag = False
                if flag == True:
                    counter[' '.join(dq_words)]+=1
        for k,v in counter.most_common():
            if k not in dic_clusters:
                idx+=1
                dic_clusters[k] = idx
            total_lines+=1
            s.append(str(dic_clusters[k]) + '\t' + str(v) + '\t' + str(file_id))
        if len(s)!=0:
            with open(self.data_path + '/temp.tab','a',encoding=self.encoding) as fh:
                fh.write('\n'.join(s))
            s=[]
        counter.clear()
        # close connection
        conn.close()
        del dq_words
        del dq_tags 
        if show_progress == True:
            print('Results: %s' % total_lines)
        if total_lines != 0:
            # make generator for reading temp file
            def get_temp_clusters():
                with open(self.data_path + '/temp.tab','r',encoding=self.encoding) as fh:
                    for line in fh:
                        if len(line.strip())!=0:
                            yield [int(i) for i in line.strip().split('\t')] 
            # get data from generator for general and range counting
            if show_progress == True:
                print('Counting clusters...' )
            range_counter = collections.Counter()
            i = 0
            for line in get_temp_clusters():
                i+=1
                counter[line[0]] += line[1]
                if line[0] not in range_counter:
                    range_counter[line[0]] = [line[2]]
                else:
                    range_counter[line[0]]+= [line[2]]
                if show_progress == True:
                    self.__progress(i,total_lines, '')
            # format data
            dic_clusters = {v: k for k, v in dic_clusters.items()} # reverse keys and values
            s = []
            s.append("N\tN-GRAM\tFREQUENCY\tRANGE\t%")
            i = 0
            j=0
            total_lines = len(counter)
            for k,v in counter.most_common():
                j+=1
                if v >= min_freq:
                    r = len(collections.Counter(range_counter[k]))
                    if r >= min_range:
                        i+=1
                        p = float( round((r / total_texts)*100,2))
                        s.append("%s\t%s\t%s\t%s\t%s" % (i,dic_clusters[k],v, r, p))
                if show_progress == True:
                    self.__progress(j,total_lines, '')
            del dic_clusters 
            del counter 
            del range_counter
            # make clusters
            ngrams = kit_tools.Ngrams()
            ngrams.read_str('\n'.join(s))
            del s
            # remove temp file 
            if os.path.exists(self.data_path + '/temp.tab'):
                os.remove(self.data_path + '/temp.tab')
            # time end
            if show_progress == True:
                t1 = time.time()
                total_time = round(t1 - t0,2) 
                print('')
                print('Total time: %s seconds' % total_time) 
        else:
            s = []
            s.append("N\tN-GRAM\tFREQUENCY\tRANGE\t%")
            ngrams = kit_tools.Ngrams()
            ngrams.read_str('\n'.join(s))
        return ngrams
    
    def dispersion(self,node,**kwargs):
        """
        Generates dispersion plots.
        :param node: Search word or phrase (max. 4 words)
        :type node : str
        :param pos: Part of speech (POS) for each search word 
        :type pos: str or list
        :param case_sensitive: Enable regular expression for search word matching
        :type case_sensitive: boolean
        :param regexp: Enable regular expression for search matching
        :type regexp: boolean
        :param limit: Number of concordance lines to return
        :type limit: int
        :param show_progress: Prints a progress message if value is True
        :type show_progress: boolean
        :return: Dispersion
        :rtype: Dispersion
        """
        # args
        node = node.strip()
        pos = kwargs.get('pos',None)
        case_sensitive = kwargs.get('case_sensitive',False)
        regexp = kwargs.get('regexp',False)
        limit = kwargs.get('limit',None)
        show_progress = kwargs.get('show_progress',False)
        # deal with args
        node_length = len(node.split(' '))
        if pos !=None:
            if type(pos)!= list:
                pos = pos.strip().split(' ')
            s = []
            for tag in pos:
                s.append("'" + tag  +"'")
            pos = ','.join(s)
        if case_sensitive == True:
            compare_operator = ' = '
        else:
            compare_operator = ' LIKE '
        if limit != None:
            limit_results= 'LIMIT %s' % limit 
        else: 
            limit_results= ''
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        # process
        # create connection
        conn = self.__conn_indexes()
        # set custom functions
        if node_length > 1:
            self.dq = collections.deque(maxlen=node_length)
            def join_words(s): # join words
                self.dq.append(s)
                return ' '.join(self.dq)
            self.dqt = collections.deque(maxlen=node_length)
            def join_tags(s): # join tags
                self.dqt.append(s)
                return ' '.join(self.dqt)
            conn.create_function("join_words", 1, join_words)
            conn.create_function("join_tags", 1, join_tags)
        if regexp == True:
            self.reg_word_p = re.compile(node)
            def regx(s): # regexp
                return self.reg_word_p.match(s) is not None
            conn.create_function("regx", 1, regx)
        cursor = conn.cursor()
        cursor.execute('begin')
        # delete previous temporary table
        cursor.execute(sqlFactory().dispersion_drop_temporary_table())
        # search node
        if show_progress == True:
            print('Searching node...' ) 
        cursor.execute(sqlFactory().dispersion_search_node(node_length, node, pos, compare_operator, regexp, limit_results))
        # count results
        cursor.execute(sqlFactory().dispersion_count_results())
        total_results = cursor.fetchone()[0]
        if show_progress == True:
            print('Results: %s ' % total_results)
        # get dispersion data
        if show_progress == True:
            print('Getting positions...' )
        # count token by file
        cursor.execute(sqlFactory().dispersion_count_by_file())
        tokens_by_file = collections.defaultdict()
        for row in cursor.fetchall():
            tokens_by_file[row[0]] = row[1]
        # get positions
        cursor.execute(sqlFactory().dispersion_data())
        if show_progress == True:
            print('Creating plots...')
        positions = collections.defaultdict()
        i=0
        for row in cursor.fetchall():
            i+=1
            p = round((row[1] / tokens_by_file[row[0]])*100,2)
            if row[0] not in positions:
                positions[row[0]]= [p]
            else:
                positions[row[0]]+= [p]
            if show_progress == True:
                self.__progress(i,total_results, '')      
        # delete temporary table
        cursor.execute(sqlFactory().dispersion_drop_temporary_table())
        # get filenames
        cursor.execute(sqlFactory().dispersion_filenames())
        filenames = collections.defaultdict()
        for row in cursor.fetchall():
            filenames[row[0]]=row[1]
        # close connection
        conn.commit()                        
        conn.close()
        # format data
        data = []
        for k in positions:
            data.append((filenames[k]  ,tokens_by_file[k],len(positions[k]),positions[k]))
        del tokens_by_file
        del positions
        del filenames
        # make table
        dispersion = kit_tools.Dispersion(output_path=self.output_path)
        tb = []
        tb.append('N\tFILENAME\tTOTAL\tHITS\tS1\tS2\tS3\tS4\tS5')
        i = 0
        total_results = len(data)
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
            if show_progress == True:
                self.__progress(i,total_results, '')
        del data 
        dispersion.read_str('\n'.join(tb))
        del tb
        if show_progress == True:
            t1 = time.time()
            total_time = round(t1 - t0,2) 
            print('')
            print('Total time: %s seconds' % total_time)
        return dispersion
    
    def keywords_dispersion(self,keywords,**kwargs):
        """
        Generates dispersion plots from keywords.
        :param limit: Maximum number of keywords to use
        :type limit: int
        :param lowercase: Letters are converted to lowercase 
        :type lowercase: boolean
        :param show_progress: Prints a progress message if value is True
        :type show_progress: boolean
        :return: Dispersion
        :rtype: Dispersion
        """
        # args
        lowercase =kwargs.get('lowercase',True)
        limit = kwargs.get('limit',25)
        show_progress = kwargs.get('show_progress',False)
        # deal with args
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        # process
        # get keywords
        self.__keys = collections.defaultdict()
        i=0
        for row in keywords.df.itertuples(index=False):
            i+=1
            self.__keys[row[1]] = row[3]
            if i >= limit:
                break 
        # create connection
        conn = self.__conn_indexes()
        cursor = conn.cursor()
        cursor.execute('begin')
        # delete previous temporary table
        cursor.execute(sqlFactory().keywords_dispersion_drop_temporary_table())
        # function for matching keys
        def match(s):
            return s in self.__keys is not False 
        conn.create_function("match", 1, match)
        # search node
        if show_progress == True:
            print('Searching keywords...' ) 
        cursor.execute(sqlFactory().keywords_dispersion_searches(lowercase))
        # count results
        cursor.execute(sqlFactory().keywords_dispersion_count_results())
        total_results = cursor.fetchone()[0]
        if show_progress == True:
            print('Results: %s ' % total_results)
        # get dispersion data
        if show_progress == True:
            print('Getting positions...' )
        # count token by file
        cursor.execute(sqlFactory().keywords_dispersion_count_by_file())
        tokens_by_file = collections.defaultdict()
        for row in cursor.fetchall():
            tokens_by_file[row[0]] = row[1]
        # get positions
        cursor.execute(sqlFactory().keywords_dispersion_data())
        if show_progress == True:
            print('Creating plots...')
        positions = collections.defaultdict()
        i=0
        for row in cursor.fetchall():
            i+=1
            p = round((row[1] / tokens_by_file[row[0]])*100,2)
            if str(row[2]).lower() not in positions:
                positions[str(row[2]).lower()]= [p]
            else:
                positions[str(row[2]).lower()]+= [p]
            if show_progress == True:
                self.__progress(i,total_results, '') 
        del tokens_by_file     
        # delete temporary table
        cursor.execute(sqlFactory().dispersion_drop_temporary_table())
        # close connection
        conn.commit()                        
        conn.close()
        # format data
        data = []
        for k in positions:
            data.append((k,len(positions[k]),positions[k],self.__keys[k]))
        del positions
        del self.__keys
        # make table
        dispersion = kit_tools.KeywordsDispersion(output_path=self.output_path)
        tb = []
        tb.append('N\tWORD\tKEYNESS\tHITS\tS1\tS2\tS3\tS4\tS5')
        i = 0
        for d in data:
            i+=1
            s1 = 0
            s2 = 0 
            s3 = 0
            s4 = 0
            s5 = 0
            dispersion.dpts[d[0]] = d[2]
            for point in d[2]:
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
            tb.append(str(i) + '\t' + d[0] + '\t' + str(d[3]) + '\t'  + str(d[1]) + '\t' +  str(s1) + '\t' + str(s2) + '\t' + str(s3) + '\t' + str(s4) + '\t' + str(s5) )
            if show_progress == True:
                self.__progress(i,total_results, '')
        del data 
        dispersion.read_str('\n'.join(tb))
        del tb
        dispersion.df.sort_values('KEYNESS',ascending=False,inplace=True)
        dispersion.df.N = [(i+1)for i in range(0,len(dispersion.df))]
        dispersion.df.reset_index(drop=True,inplace=True)
        if show_progress == True:
            t1 = time.time()
            total_time = round(t1 - t0,2) 
            print('')
            print('Total time: %s seconds' % total_time)
        return dispersion  
            
        
        

