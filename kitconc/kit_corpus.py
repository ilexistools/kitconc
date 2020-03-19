# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
import os,sys   
import time  
from kitconc import kit_tools
from kitconc import kit_util
from kitconc import kit_data 
import subprocess
import pandas as pd
import collections 
# cython 
try:
    from cython import __version__
    USING_CYTHON = True
except:
    USING_CYTHON = False
    
if USING_CYTHON == True:
    from kitconc.cy_wordlist import make_wordlist
    from kitconc.cy_keywords import make_keywords
    from kitconc.cy_wtfreq import make_wtfreq
    from kitconc.cy_wfreqinfiles import make_wfreqinfiles
    from kitconc.cy_kwic import make_kwic 
    from kitconc.cy_concordance import make_concordance
    from kitconc.cy_collocates import make_collocates
    from kitconc.cy_clusters import make_clusters     
    from kitconc.cy_ngrams import make_ngrams
    from kitconc.cy_dispersion import make_dispersion
    from kitconc.cy_keywords_dispersion import make_keywords_dispersion
else:
    from kitconc.py_wordlist import make_wordlist
    from kitconc.py_keywords import make_keywords
    from kitconc.py_wtfreq import make_wtfreq
    from kitconc.py_wfreqinfiles import make_wfreqinfiles
    from kitconc.py_kwic import make_kwic 
    from kitconc.py_concordance import make_concordance
    from kitconc.py_collocates import make_collocates
    from kitconc.py_clusters import make_clusters     
    from kitconc.py_ngrams import make_ngrams
    from kitconc.py_dispersion import make_dispersion
    from kitconc.py_keywords_dispersion import make_keywords_dispersion
    print('Warning: Could not use cython or error in pyx file.')
    

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
            # make dirs for processing
            if not os.path.exists(self.workspace + self.corpus_name + '/data/npy'):
                os.mkdir(self.workspace + self.corpus_name + '/data/npy')
            if not os.path.exists(self.workspace + self.corpus_name + '/data/idx'):
                os.mkdir(self.workspace + self.corpus_name + '/data/idx')
            if not os.path.exists(self.workspace + self.corpus_name + '/data/tmp1'):
                os.mkdir(self.workspace + self.corpus_name + '/data/tmp1')
            if not os.path.exists(self.workspace + self.corpus_name + '/data/tmp2'):
                os.mkdir(self.workspace + self.corpus_name + '/data/tmp2')
            if not os.path.exists(self.workspace + self.corpus_name + '/data/tmp3'):
                os.mkdir(self.workspace + self.corpus_name + '/data/tmp3')
            
            
            # save info
            self.__save_corpus_info(self.workspace, self.corpus_name, self.language, self.encoding)
           
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
  

    def add_texts(self,source_folder,**kwargs):
        """Adds texts to a corpus reference from a source folder.
        :param  source_folder: A folder path where the source texts are stored.
        :type   source_folder: str
        :param tagged: If texts are already tagged. 
        :type tagged: boolean
        :param show_progress: Prints a progress message if value is True 
        :type show_progress: boolean
        """
        import shutil
        # args 
        show_progress = kwargs.get('show_progress',False)
        tagged = kwargs.get('tagged',False)
        if not source_folder.endswith('/'):
            source_folder = source_folder + '/'
        # time it start
        if show_progress == True:
            t0 = time.time()
            print('New corpus:')
        # make indexes
        if tagged == False:
            if show_progress == True:
                print('Tagging...')
            resources_path = self.__path + '/data/'
            subprocess.call(['python',self.__path +'/tagging.py', resources_path,self.workspace,self.corpus_name, self.language,source_folder])
            if show_progress == True:
                print('Making indexes...')
            subprocess.call(['python',self.__path +'/indexing.py', self.workspace,self.corpus_name, self.language])
        else:
            if show_progress == True:
                print('Loading tagged corpus...')
            resources_path = self.__path + '/data/'
            subprocess.call(['python',self.__path +'/tagged.py', resources_path,self.workspace,self.corpus_name, self.language,source_folder])
            if show_progress == True:
                print('Making indexes...')
            subprocess.call(['python',self.__path +'/indexing.py', self.workspace,self.corpus_name, self.language])
            
        # add source path to info
        ntexts = len(os.listdir(source_folder))
        with open(self.workspace+self.corpus_name+'/info.tab','a',encoding='utf-8') as fh:
            fh.write('\nTextfiles:\t%s\nSource:\t%s' % (ntexts,source_folder))
        # time it end 
        if show_progress == True:
            t1 = time.time()
            total_time = round(t1 - t0,2) 
            print('Total time: %s seconds' % total_time)
        # delete temporary folders
        shutil.rmtree(self.workspace+self.corpus_name+'/data/tmp1/')
        shutil.rmtree(self.workspace+self.corpus_name+'/data/tmp2/')
        shutil.rmtree(self.workspace+self.corpus_name+'/data/tmp3/')

    def wordlist(self,**kwargs):
        """
        Generates a frequency wordlist based on text files.
        :param lowercase: Letters are converted to lowercase 
        :type lowercase: boolean
        :param min_freq: minimum frequency of the word
        :type min_freq: int
        :param show_progress: Prints a progress message if value is True 
        :type show_progress: boolean
        :return: Wordlist
        :rtype: Wordlist
        """
        # args
        show_progress=kwargs.get('show_progress',False)
        min_freq = kwargs.get('min_freq',1)
        lowercase = kwargs.get('lowercase',True)
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        # make
        tokens, types, type_token, hapax, xwordlist = make_wordlist(self.workspace,self.corpus_name, self.language,lowercase)
        wlst = kit_tools.Wordlist(tokens=tokens,types=types,typetoken=round(type_token,2),hapax=hapax)
        wlst.df = pd.DataFrame(xwordlist,columns=['N','WORD','FREQUENCY','%'])
        wlst.df=wlst.df[(wlst.df.FREQUENCY >= min_freq)] 
        wlst.df['%'] = wlst.df['%'].apply(lambda x: round(x, 2))
        # time end
        if show_progress == True:
            #self.__progress(types, types, '')
            t1 = time.time()
            total_time = round(t1 - t0,2) 
            print('')
            print('Total time: %s seconds' % total_time)
        return  wlst
    
    def keywords(self,**kwargs):
        """
        Extracts keywords from a wordlist
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
        # make keywords table
        kwlst = kit_tools.Keywords()
        k = make_keywords(self.workspace,self.corpus_name,self.language,stat)
        kwlst.df = pd.DataFrame(k,columns=['N','WORD','FREQUENCY','KEYNESS'])
        k = None
        # use stoplist
        kwlst.df = kwlst.df[~kwlst.df['WORD'].isin(stoplist)]
        # sort by keyness and reset index
        kwlst.df['KEYNESS'] = kwlst.df['KEYNESS'].apply(lambda x: round(x, 2))
        kwlst.df.sort_values('KEYNESS',ascending=False,inplace=True)
        kwlst.df.N = [(i+1)for i in range(0,len(kwlst.df))]
        kwlst.df.reset_index(drop=True,inplace=True)
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
        # make wtfreq
        lst_wt = make_wtfreq(self.workspace, self.corpus_name, self.language, lowercase)
        #s.append("N\tWORD\tTAG\tFREQUENCY\t%")
        wt = kit_tools.WTfreq()
        wt.df = pd.DataFrame(lst_wt,columns=['N','WORD','TAG','FREQUENCY','%'])
        # sort by freq and reset index
        wt.df['%'] = wt.df['%'].apply(lambda x: round(x, 2))
        wt.df.sort_values('FREQUENCY',ascending=False,inplace=True)
        wt.df.N = [(i+1)for i in range(0,len(wt.df))]
        wt.df.reset_index(drop=True,inplace=True)
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
        lst_fif = make_wfreqinfiles(self.workspace, self.corpus_name, self.language, lowercase)
        fif = kit_tools.Wfreqinfiles()
        fif.df = pd.DataFrame(lst_fif,columns=['N','WORD','RANGE','%'])
        lst_fif = None
        # sort by freq and reset index
        fif.df['%'] = fif.df['%'].apply(lambda x: round(x, 2))
        fif.df.sort_values('RANGE',ascending=False,inplace=True)
        fif.df.N = [(i+1)for i in range(0,len(fif.df))]
        fif.df.reset_index(drop=True,inplace=True)
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
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        # deal with args
        nl,lst_kwic = make_kwic(self.workspace, self.corpus_name,node,pos,case_sensitive,regexp,horizon)
        kwic = kit_tools.Kwic(node_length=nl)
        kwic.df = pd.DataFrame(lst_kwic,columns=['N','LEFT','NODE','RIGHT','FILENAME','TOKEN_ID','SENT_ID','FILE_ID'])
        lst_kwic = None
        # limit
        if limit != None:
            kwic.df = kwic.df.head(limit)
        # reset indexes 
        kwic.df.N = [(i+1)for i in range(0,len(kwic.df))]
        kwic.df.reset_index(drop=True,inplace=True)
        # time end
        if show_progress == True:
            self.__progress(100,100, '')
            t1 = time.time()
            total_time = round(t1 - t0,2) 
            print('')
            print('Total time: %s seconds' % total_time)
        return kwic 
    
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
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        # deal with args
        nl,lst_conc = make_concordance(self.workspace, self.corpus_name,node,pos,case_sensitive,regexp)
        conc = kit_tools.Concordance(node_length=nl)
        conc.df = pd.DataFrame(lst_conc,columns=['N','CONCORDANCE','FILENAME','TOKEN_ID','SENT_ID','FILE_ID'])
        lst_conc = None
        # limit
        if limit != None:
            conc.df = conc.df.head(limit)
        # reset indexes 
        conc.df.N = [(i+1)for i in range(0,len(conc.df))]
        conc.df.reset_index(drop=True,inplace=True)
        # time end
        if show_progress == True:
            self.__progress(100,100, '')
            t1 = time.time()
            total_time = round(t1 - t0,2) 
            print('')
            print('Total time: %s seconds' % total_time)
        return conc 
    
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
        :param limit: Number of result lines to return
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
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        # make
        if measure == 't-score':
            measure = 1
        elif measure == 'mutual information':
            measure = 2
        lst_coll = make_collocates(self.workspace, self.corpus_name, node, pos, case_sensitive, regexp, coll_pos, lowercase, left_span, right_span,measure)
        coll = kit_tools.Collocates()
        coll.df = pd.DataFrame(lst_coll,columns=['N','WORD','FREQUENCY','LEFT','RIGHT','ASSOCIATION'])
        lst_coll = None
        # sort 
        coll.df.sort_values('ASSOCIATION',ascending=False,inplace=True)
        # limit
        if limit != None:
            coll.df = coll.df.head(limit)
        # reset indexes 
        coll.df['ASSOCIATION'] = coll.df['ASSOCIATION'].apply(lambda x: round(x, 2))
        coll.df.N = [(i+1)for i in range(0,len(coll.df))]
        coll.df.reset_index(drop=True,inplace=True)
        # time end
        if show_progress == True:
            self.__progress(100,100, '')
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
        import re 
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
        # wordlist to dic
        tpl = make_wordlist(self.workspace,self.corpus_name,self.language,lowercase)
        tokens = tpl[0]
        freqlist = collections.defaultdict()
        for row in tpl[4]:
            freqlist[row[1]] = row[2]
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
        :param minfreq: minimum frequency of the cluster
        :type minfreq: int
        :param minrange: minimum range frequency 
        :type minrange: int
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
        min_freq = kwargs.get('minfreq',1)
        min_range = kwargs.get('minrange',1)
        show_progress = kwargs.get('show_progress',False)
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        lst_clusters = make_clusters(self.workspace, self.corpus_name, word, pos, lowercase, size)
        clusters = kit_tools.Clusters()
        clusters.df = pd.DataFrame(lst_clusters,columns=['N','CLUSTER','FREQUENCY','RANGE','%'])
        lst_clusters = None
        # sort 
        clusters.df.sort_values('FREQUENCY',ascending=False,inplace=True)
        # filter
        clusters.df=clusters.df[(clusters.df.FREQUENCY >= min_freq)]
        clusters.df=clusters.df[(clusters.df.RANGE >= min_range)] 
        # reset indexes 
        clusters.df['%'] = clusters.df['%'].apply(lambda x: round(x, 2))
        clusters.df.N = [(i+1)for i in range(0,len(clusters.df))]
        clusters.df.reset_index(drop=True,inplace=True)
        # time end
        if show_progress == True:
            t1 = time.time()
            total_time = round(t1 - t0,2) 
            print('')
            print('Total time: %s seconds' % total_time)
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
        :param minfreq: minimum frequency of the cluster
        :type minfreq: int
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
        min_freq = kwargs.get('minfreq',1)
        min_range = kwargs.get('minrange',1)
        show_progress = kwargs.get('show_progress',False)
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        # make ngrams 
        lst_ng = make_ngrams(self.workspace, self.corpus_name, pos, size, lowercase)
        ng = kit_tools.Ngrams()
        ng.df = pd.DataFrame(lst_ng,columns=['N','N-GRAM','FREQUENCY','RANGE','%'])
        lst_ng = None
        # sort 
        ng.df.sort_values('FREQUENCY',ascending=False,inplace=True)
        # filter
        ng.df=ng.df[(ng.df.FREQUENCY >= min_freq)]
        ng.df=ng.df[(ng.df.RANGE >= min_range)] 
        # reset indexes 
        ng.df['%'] = ng.df['%'].apply(lambda x: round(x, 2))
        ng.df.N = [(i+1)for i in range(0,len(ng.df))]
        ng.df.reset_index(drop=True,inplace=True)
        # time end
        if show_progress == True:
            t1 = time.time()
            total_time = round(t1 - t0,2) 
            print('')
            print('Total time: %s seconds' % total_time)
        return ng
    
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
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        # make dispersion
        totals,dpts,lst_disp=make_dispersion(self.workspace, self.corpus_name, node, pos, case_sensitive,regexp)
        disp = kit_tools.Dispersion(output_path=self.output_path)
        disp.df = pd.DataFrame(lst_disp,columns=['N','FILENAME','TOTAL','HITS','S1','S2','S3','S4','S5'])
        disp.dpts = dpts
        disp.total_s1 = totals[0]
        disp.total_s2 = totals[1]
        disp.total_s3 = totals[2]
        disp.total_s4 = totals[3]
        disp.total_s5 = totals[4] 
        lst_disp = None
        # sort 
        disp.df.sort_values('HITS',ascending=False,inplace=True)
        # limit
        if limit != None:
            disp.df = disp.df.head(limit)
        # reset indexes 
        disp.df.N = [(i+1)for i in range(0,len(disp.df))]
        disp.df.reset_index(drop=True,inplace=True)
        # time end
        if show_progress == True:
            t1 = time.time()
            total_time = round(t1 - t0,2) 
            print('')
            print('Total time: %s seconds' % total_time)
        return disp
    
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
        dict_keywords = dict()
        try:
            i=0
            for row in keywords.df.itertuples(index=False):
                i+=1
                dict_keywords[row[1]] = row[3]
                if i >= limit:
                    break
        except Exception as e:
            print(e) 
        # make dispersion
        totals,dpts,lst_disp=make_keywords_dispersion(self.workspace, self.corpus_name,dict_keywords,lowercase)
        disp = kit_tools.KeywordsDispersion(output_path=self.output_path)
        disp.df = pd.DataFrame(lst_disp,columns=['N','WORD','KEYNESS','HITS','S1','S2','S3','S4','S5'])
        disp.dpts = dpts
        disp.total_s1 = totals[0]
        disp.total_s2 = totals[1]
        disp.total_s3 = totals[2]
        disp.total_s4 = totals[3]
        disp.total_s5 = totals[4] 
        lst_disp = None
        # sort 
        disp.df.sort_values('KEYNESS',ascending=False,inplace=True)
        # limit
        if limit != None:
            disp.df = disp.df.head(limit)
        # reset indexes 
        disp.df.N = [(i+1)for i in range(0,len(disp.df))]
        disp.df.reset_index(drop=True,inplace=True)
        # time end
        if show_progress == True:
            t1 = time.time()
            total_time = round(t1 - t0,2) 
            print('')
            print('Total time: %s seconds' % total_time)
        return disp 
    
    # GENERAL FUNCTIONS 
    
    def info(self):
        """Returns statistical information from the corpus (tokens,types,TTR,hapax)
        :return: tuple
        :rtype: tuple
        """
        kd = kit_data.KitData(self.workspace,self.corpus_name,self.language)
        return kd.info_get()
    
    def tokens(self):
        """Returns the number of tokens.
        :return: int
        :rtype: int
        """
        kd = kit_data.KitData(self.workspace,self.corpus_name,self.language)
        return kd.tokens_get()
    
    def types(self):
        """Returns the number of types.
        :return: int
        :rtype: int
        """
        kd = kit_data.KitData(self.workspace,self.corpus_name,self.language)
        return kd.types_get()
    
    def ttr(self):
        """Returns the type/token ratio.
        :return: float
        :rtype: float
        """
        kd = kit_data.KitData(self.workspace,self.corpus_name,self.language)
        return kd.ttr_get()
    
    def hapax(self):
        """Returns the number of hapax legomena.
        :return: int 
        :rtype: int 
        """
        kd = kit_data.KitData(self.workspace,self.corpus_name,self.language)
        return kd.hapax_get()
    
    def textfiles(self):
        """Returns the names of textfiles.
        :return: generator
        :rtype: generator
        """
        kd = kit_data.KitData(self.workspace,self.corpus_name,self.language)
        return kd.textfiles_get_names()
    
    def fileids(self):
        """Returns the list of file ids.
        :return: generator
        :rtype: generator
        """
        kd = kit_data.KitData(self.workspace,self.corpus_name,self.language)
        return kd.fileids_get()
    
    def words(self,fileids=None):
        """Returns the words from textfiles by ids.
        :return: generator
        :rtype: generator
        """
        kd = kit_data.KitData(self.workspace,self.corpus_name,self.language)
        return kd.words_get(fileids)
    
    def tagged_words(self,fileids=None):
        """Returns the tagged words from textfiles by ids.
        :return: generator
        :rtype: generator
        """
        kd = kit_data.KitData(self.workspace,self.corpus_name,self.language)
        return kd.tagged_words_get(fileids)
    
    def sents(self,fileids=None):
        """Returns sentences from textfiles by ids.
        :return: generator
        :rtype: generator
        """
        kd = kit_data.KitData(self.workspace,self.corpus_name,self.language)
        return kd.sents_get(fileids)
    
    def tagged_sents(self,fileids=None):
        """Returns tagged sentences from textfiles by ids.
        :return: generator
        :rtype: generator
        """
        kd = kit_data.KitData(self.workspace,self.corpus_name,self.language)
        return kd.tagged_sents_get(fileids)
    
    def ndarrays(self,fileids=None):
        """Returns ndarrays from textfiles by ids.
        :return: generator
        :rtype: generator
        """
        kd = kit_data.KitData(self.workspace,self.corpus_name,self.language)
        return kd.ndarrays_get(fileids)
    
    def ndarrays_filenames(self,fileids=None):
        """Returns ndarrays filenames from textfiles by ids.
        :return: generator
        :rtype: generator
        """
        kd = kit_data.KitData(self.workspace,self.corpus_name,self.language)
        return kd.ndarrays_filenames_get(fileids) 
    
    def dict_words(self):
        """Returns a dictionary of id and word.
        :return: dict
        :rtype: dict
        """
        kd = kit_data.KitData(self.workspace,self.corpus_name,self.language)
        return kd.dict_words_get()
    
    def dict_tags(self):
        """Returns a dictionary of id and tag.
        :return: dict
        :rtype: dict
        """
        kd = kit_data.KitData(self.workspace,self.corpus_name,self.language)
        return kd.dict_tags_get()
        
    
   
    
    
        
    
        
    
        
        
        

    
    