# -*- coding: utf-8 -*-
import os, sys,subprocess  
from cmd import Cmd
import argparse
from kitconc.corpus import Corpus
import pickle
import pandas as pd  

  
class KitPrompt(Cmd):
    
    def parse_args(self,s):
        """Parses args from command line"""
        try:
            args = s.strip().split(' ')
        except:
            args = s 
        return args
    
    def load_config(self):
        """Loads configuration """
        self.workspace = None
        self.corpus_in_use = None
        try:
            if os.path.exists('kitconc.tmp'):
                with open('kitconc.tmp','r') as fh:
                    workspace = str(fh.read()).strip()
                    if os.path.exists(workspace) and os.path.isdir(workspace):
                        self.workspace = workspace.strip()
        except Exception as e:
                print(e)
                
    #
    # EXIT CONSOLE COMMANDS 
    #
    
    def do_exit(self, args):
        """\nEnds program\n"""
        print ("Finishing...")
        raise SystemExit
    
    def do_quit(self,args):
        """\nEnds program\n"""
        print ("Finishing...")
        raise SystemExit

    def do_version(self,args):
        """\nShows version\n"""
        print ("\nKitconc 5.0.0\n")
    
    def do_dev(self,args):
        """\nShows developer info\n"""
        print ("\nJosé Lopes Moreira Filho\njlopes@usp.br\n")
    
    def do_cls(self,args):
        """\nClear screen\n"""
        os.system('cls' if os.name=='nt' else 'clear') 
    
    def do_clear(self,args):
        """\nClear screen\n"""
        os.system('cls' if os.name=='nt' else 'clear')
    
    #
    # WORKSPACE 
    #
    
    def do_ws(self,args):
        """\nDescription: Sets or shows the current workspace.
        \nUsage: ws [path]
        """
        if args is None or len(args.strip())== 0:
            if self.workspace == None:
                print('\nThere is no current workspace.\n')
            else:
                print('\n' + self.workspace + '\n')
        else:
            if os.path.exists(args.strip()) == True and os.path.isdir(args.strip())==True:
                if args.strip().endswith('/'):
                    self.workspace = args 
                else:
                    self.workspace = args + '/'
                with open('kitconc.tmp','w') as fh:
                    fh.write(self.workspace)
            else:
                print('\nNot a valid workspace.\nThe workspace command takes a path as argument.\n')
    
    def do_ls(self,args):
        """\nDescription: Lists corpora or files in the output corpus folder.
        \nUsage: ls  
        """
        try:
            if self.workspace is not None:
                if self.corpus_in_use == None:
                    files = os.listdir(self.workspace)
                    corpora = []
                    for filename in files:
                        if os.path.isdir(self.workspace + filename):
                            corpora.append(filename)
                    if len(corpora) !=0:
                        print ('\n' +'\n'.join(corpora) + '\n')
                else:
                    output_path = self.workspace + self.corpus_in_use + '/output/'
                    files = os.listdir(output_path)
                    contents = []
                    for filename in files:
                        if os.path.isfile(output_path + filename):
                            contents.append(filename)
                    if len(contents) !=0:
                        print ('\n' +'\n'.join(contents) + '\n')
            else:
                print('\nNo workspace set.\n')
        except Exception as e:
                print(e)
    
    def do_home(self,args):
        """\nDescription: Returns to the current workspace root without any corpus selection.
        \nUsage: home
        """
        try:
            if self.corpus_in_use != None:
                self.corpus_in_use = None
                self.prompt = 'kitconc>'
                print ('')
        except Exception as e:
                print(e)
            
    #
    # util
    #     
    
    def __corpus_exists(self,corpus_name):
        flag = False
        if self.workspace is not None:
            if os.path.exists(self.workspace + '/' + corpus_name + '/info.pickle'):
                flag = True
        return flag 
    
    def __corpus_info(self,corpus_name):
        corpus_info = None
        if self.workspace is not None:
            filename = self.workspace + '/' + corpus_name + '/info.pickle'
            if os.path.exists(filename):
                fh = open(filename,'rb')
                corpus_info = pickle.load(fh)
                fh.close()
        return corpus_info  
                

    #
    # CORPUS
    #
    
    def do_create(self,s):
        """\nDescription: Creates a new corpus from text files in a source folder.
        \nUsage: create -n [name] -f [source_folder] -l [language] --e [encoding]
        """
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('-n', action='store', dest='name', type=str)
            parser.add_argument('-f', action='store', dest='source_folder', type=str)
            parser.add_argument('-l', action='store', dest='language', type=str)
            parser.add_argument('--e', action='store', dest='encoding', type=str)
            args = parser.parse_args(s.split())
        except:
            args = None
        
        if args is not None:
            if args.encoding!=None:
                encoding = args.encoding
            else:
                encoding='utf-8'
            try:
                corpus = Corpus(self.workspace,args.name,language=args.language, encoding = encoding)
                corpus.add_texts(args.source_folder, show_progress=True)
            except Exception as e:
                print(e)
    
    def do_delete(self,s):
        """\nDescription: Deletes a corpus.
        \nUsage: delete [name]
        """
        try:
            corpus_name = s.strip()
            if self.__corpus_exists(corpus_name):
                flag = input('Do you really want to delete the corpus "' + corpus_name + '"? [y,n]')
                if flag.strip().lower() == 'y' and len(corpus_name) != 0 :
                    import shutil
                    shutil.rmtree(self.workspace + corpus_name)
                    print('')
        except Exception as e:
                print(e)
    
    def do_cleanse(self,s):
        """\nDescription: Deletes all files from the output folder.
        \nUsage: cleanse
        """
        try:
            if self.corpus_in_use != None:
                flag = input('Do you really want to delete all files? [y,n]')
                if flag.strip().lower() == 'y':
                    output_path = self.workspace + self.corpus_in_use + '/output/'
                    files = os.listdir(output_path)
                    if len(files) != 0:
                        for filename in files:
                            os.remove(output_path + filename)
                            print('removing ... ' + filename)
        except Exception as e:
                print(e)
                
    
    def do_use(self,s):
        """\nDescription: Sets the current corpus in use.
        \nUsage: use [name]
        """
        try:
            corpus_name = s.strip()
            if self.__corpus_exists(corpus_name):
                corpus_name = s.strip()
                self.corpus_in_use = corpus_name
                print('') 
                self.prompt = 'kitconc/' + self.corpus_in_use + '>'
            else:
                print('\nNo corpus found.\n')
        except Exception as e:
                print(e)
        
        
    
    def do_info(self,s):
        """\nDescription: Shows corpus information.
        \nUsage: info 
        """
        try:
            corpus_info = self.__corpus_info(self.corpus_in_use)
            info =[]
            for k in corpus_info:
                info.append(str(k).upper() + ': ' + corpus_info[k])
            print ('\n' + '\n'.join(info) + '\n')
        except Exception as e:
                print(e)
    
    def do_head(self,s):
        """\nDescription: Displays lines from a file.
        \nUsage: head -f [filename] --lines  
        """
        if self.corpus_in_use != None:
            try:
                parser = argparse.ArgumentParser()
                parser.add_argument('-f', action='store', dest='filename', type=str)
                parser.add_argument('--lines', action='store', dest='lines', type=int)
                args = parser.parse_args(s.split())
                if str(args.filename).endswith('.tab') == False:
                        filename = args.filename + '.tab'
                else:
                    filename = args.filename
                output_path  = self.workspace + self.corpus_in_use + '/output/'
                if os.path.exists(output_path + filename):
                    tb = pd.read_table(output_path + filename)
                    lines = 5
                    if args.lines != None:
                        lines = args.lines 
                    print('')
                    print(tb.head(lines))
                    print('') 
            except Exception as e:
                print(e)
    
    def do_xopen(self,s):
        """\nDescription: Opens a xls(x) file.
        \nUsage: xopen -f [filename]  
        """
        try:
            if self.corpus_in_use != None:
                output_path = self.workspace + self.corpus_in_use + '/output/'
                parser = argparse.ArgumentParser()
                parser.add_argument('-f', action='store', dest='filename', type=str)
                args = parser.parse_args(s.split())
                if str(args.filename).endswith('.xls') or str(args.filename).endswith('.xlsx'):
                    if os.name == 'nt':
                        #on Windows:
                        os.system(output_path + args.filename)
                    else:
                        #on linux:
                        opener ="open" if sys.platform == "darwin" else "xdg-open"
                        output = subprocess.call([opener, output_path + '/' + args.filename])
                        output.trim()
                        output = None
                        print('')
        except Exception as e:
                print(e)
    
    #
    # WORDLIST
    #
    
    def do_wordlist(self,s):
        """\nDescription: Makes a frequency word list from the current corpus. 
        \nUsage: wordlist
        """
        try:
            if self.corpus_in_use is not None:
                corpus_info = self.__corpus_info(self.corpus_in_use)
                corpus = Corpus(self.workspace,self.corpus_in_use,language=corpus_info['language'],encoding=corpus_info['encoding'])
                wordlist = corpus.wordlist(show_progress=True)
                wordlist.save_tab(self.workspace + self.corpus_in_use + '/output/wordlist.tab')
                wordlist.save_xls(self.workspace + self.corpus_in_use + '/output/wordlist.xlsx')
                wordlist = None
        except Exception as e:
                print(e)
    
    #
    # WTFREQ
    #
    
    def do_wtfreq(self,s):
        """\nDescription: Makes a word/tag frequency list from the current corpus. 
        \nUsage: wtfreq
        """
        try:
            if self.corpus_in_use is not None:
                    corpus_info = self.__corpus_info(self.corpus_in_use)
                    corpus = Corpus(self.workspace,self.corpus_in_use,language=corpus_info['language'],encoding=corpus_info['encoding'])
                    wtfreq = corpus.wtfreq(show_progress=True)
                    wtfreq.save_tab(self.workspace + self.corpus_in_use + '/output/wtfreq.tab')
                    wtfreq.save_xls(self.workspace + self.corpus_in_use + '/output/wtfreq.xlsx')
                    wtfreq = None
        except Exception as e:
                print(e)
    
    #
    # WTFREQINFILES
    #
    
    def do_freqinfiles(self,s):
        """\nDescription: Counts the frequency of words in text files. 
        \nUsage: freqinfiles
        """
        try:
            if self.corpus_in_use is not None:
                    corpus_info = self.__corpus_info(self.corpus_in_use)
                    corpus = Corpus(self.workspace,self.corpus_in_use,language=corpus_info['language'],encoding=corpus_info['encoding'])
                    wordlist = corpus.wordlist(show_progress=True)
                    freqinfiles = corpus.freqinfiles(wordlist, show_progress=True) 
                    wordlist = None
                    freqinfiles.save_tab(self.workspace + self.corpus_in_use + '/output/freqinfiles.tab')
                    freqinfiles.save_xls(self.workspace + self.corpus_in_use + '/output/freqinfiles.xlsx')
                    freqinfiles = None
        except Exception as e:
                print(e)
    
    #
    # KEYWORDS
    #
    
    def do_keywords(self,s):
        """\nDescription: Extracts keywords from the current corpus. 
        \nUsage: keywords
        """
        try:
            if self.corpus_in_use is not None:
                    corpus_info = self.__corpus_info(self.corpus_in_use)
                    corpus = Corpus(self.workspace,self.corpus_in_use,language=corpus_info['language'],encoding=corpus_info['encoding'])
                    wordlist = corpus.wordlist(show_progress=True)
                    keywords = corpus.keywords(wordlist, show_progress=True) 
                    wordlist = None
                    keywords.save_tab(self.workspace + self.corpus_in_use + '/output/keywords.tab')
                    keywords.save_xls(self.workspace + self.corpus_in_use + '/output/keywords.xlsx')
                    keywords = None
        except Exception as e:
                print(e)
    
    #
    # KWIC
    #
    
    def do_kwic(self,s):
        """\nDescription: Creates concordance lines. 
        \nUsage: kwic -n [node]
        \n\nOptions: 
        \n--pos [pos]         - (str) POS tag(s) for search node
        \n--regex [regex]     - (str) regular expression
        \n--horizon [horizon] - (int) horizon size
        \n--width [width]     - (int) width in chars
        \n--limit [limit]     - (int) number 
        \n--sort1 [first]     - (str) possible values: L1,L2,L3,L4,R1,R2,R3, or R4
        \n--sort2 [second]    - (str) possible values: L1,L2,L3,L4,R1,R2,R3, or R4
        \n--sort3 [third]     - (str) possible values: L1,L2,L3,L4,R1,R2,R3, or R4
        """
        
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('-n', action='store', dest='node',nargs='+', type=str)
            parser.add_argument('--pos', action='store', dest='pos', type=str)
            parser.add_argument('--regex', action='store', dest='regex', type=str)
            parser.add_argument('--horizon', action='store', dest='horizon', type=int)
            parser.add_argument('--width', action='store', dest='width', type=int)
            parser.add_argument('--limit', action='store', dest='limit', type=int)
            parser.add_argument('--sort1', action='store', dest='sort1', type=str)
            parser.add_argument('--sort2', action='store', dest='sort2', type=str)
            parser.add_argument('--sort3', action='store', dest='sort3', type=str)
            args = parser.parse_args(s.split())
            
            if len(args.node) > 1:
                node = ' '.join(args.node)
            else:
                node = args.node[0].strip()
             
            if args.pos is None:
                pos = None
            else:
                pos = args.pos
            
            if args.regex is None:
                regex = False 
            else:
                if args.regex == '1' or args.regex == 'True':
                    regex = True
            
            if args.horizon is None:
                horizon = 12
            else:
                horizon = int(args.horizon)
            
            if args.width is None:
                width = 65
            else:
                width = args.width  
            
            if args.limit is None:
                limit = 0
            else:
                limit = int(args.limit) 
            
            if args.sort1 is None:
                sort1 = None
            else:
                sort1 = args.sort1
            
            if args.sort2 is None:
                sort2 = None
            else:
                sort2 = args.sort2 
            
            if args.sort3 is None:
                sort3 = None
            else:
                sort3 = args.sort3
            
            if self.corpus_in_use is not None:
                    corpus_info = self.__corpus_info(self.corpus_in_use)
                    corpus = Corpus(self.workspace,self.corpus_in_use,language=corpus_info['language'],encoding=corpus_info['encoding'])
                    kwic = corpus.kwic(node,pos=pos,regex=regex,horizon=horizon,limit=limit,show_progress=True)
                    kwic.sort(sort1, sort2, sort3)  
                    kwic.save_xls(self.workspace + self.corpus_in_use + '/output/kwic.xlsx', width)
        except Exception as e:
                print(e)
        
    #
    # COLOCATES
    #
    
    def do_collocates(self,s):
        """\nDescription: Extracts a list of collocates. 
        \nUsage: collocates -n [node]
        \n\nOptions: 
        \n--pos [pos]         - (str) POS tag(s) for search node
        \n--regex [regex]     - (str) regular expression
        \n--ls [left_span]    - (int) left span size for collocates
        \n--rs [right_span]   - (int) right span size for collocates
        \n--cpos [pos]        - (str) POS tag(s) for collocates
        \n--limit [limit]     - (int) number
        \n--stat [measure]    - (str) statistical measure: tscore or mutual information
        """
        try:
            # parse args
            parser = argparse.ArgumentParser()
            parser.add_argument('-n', action='store', dest='node',nargs='+', type=str)
            parser.add_argument('--pos', action='store', dest='pos',nargs='+', type=str)
            parser.add_argument('--regex', action='store', dest='regex', type=str)
            parser.add_argument('--ls', action='store', dest='ls', type=str)
            parser.add_argument('--rs', action='store', dest='rs', type=str)
            parser.add_argument('--cpos', action='store', dest='cpos',nargs='+', type=str)
            parser.add_argument('--limit', action='store', dest='limit', type=int)
            parser.add_argument('--stat', action='store', dest='stat', type=str)
            args = parser.parse_args(s.split())
            # fix args
            if len(args.node) > 1:
                node = ' '.join(args.node)
            else:
                node = args.node[0].strip()
            if args.pos is None:
                pos = None
            else:
                if len(args.pos) > 1:
                    pos = ' '.join(args.pos)
                else:
                    pos = args.pos[0]
            if args.regex is None:
                regex = False 
            else:
                if args.regex == '1' or args.regex == 'True':
                    regex = True
            if args.ls is not None:
                ls = int(args.ls)
            else:
                ls = 1
            if args.rs is not None:
                rs = int(args.rs)
            else:
                rs = 1
            if args.cpos is not None:
                if len(args.cpos) > 1:
                    cpos = ' '.join(args.cpos)
                else:
                    cpos = args.cpos[0]
            else:
                cpos = None
            if args.limit is None:
                limit = 0
            else:
                limit = int(args.limit)
            if args.stat is None:
                stat = 'tscore'
            else:
                stat = args.stat
            
            # exec
            if self.corpus_in_use is not None:
                corpus_info = self.__corpus_info(self.corpus_in_use)
                corpus = Corpus(self.workspace,self.corpus_in_use,language=corpus_info['language'],encoding=corpus_info['encoding'])
                wordlist = corpus.wordlist()
                collocates = corpus.collocates(wordlist,node,pos=pos,regex=regex,left_span=ls,right_span=rs, 
                                               coll_pos=cpos,limit=limit,measure=stat,show_progress=True)
                collocates.save_xls(self.workspace + self.corpus_in_use + '/output/collocates.xlsx')
        except Exception as e:
                print(e) 
        
        
    #
    # N-GRAMS
    #
    
    def do_ngrams(self,s):
        """\nDescription: Makes a list of n-grams (1 to 4). 
        \nUsage: ngrams -size [size]
        \n\nOptions: 
        \n--minfreq [minfreq]     - (int) minimum frequency
        \n--minrange [minrange]   - (int) minimum frequency in corpus files
        \n--tag1 [pos]            - (str) POS tag for word 1
        \n--tag2 [pos]            - (str) POS tag for word 2
        \n--tag3 [pos]            - (str) POS tag for word 3
        \n--tag4 [pos]            - (str) POS tag for word 4
        """
        try:
            # parse args
            parser = argparse.ArgumentParser()
            parser.add_argument('-size', action='store', dest='size', type=int)
            parser.add_argument('--minfreq', action='store', dest='minfreq', type=int)
            parser.add_argument('--minrange', action='store', dest='minrange', type=int)
            parser.add_argument('--tag1', action='store', dest='tag1', type=str)
            parser.add_argument('--tag2', action='store', dest='tag2', type=str)
            parser.add_argument('--tag3', action='store', dest='tag3', type=str)
            parser.add_argument('--tag4', action='store', dest='tag4', type=str)
            args = parser.parse_args(s.split())
            # fix args
            if args.size is not None:
                if args.size < 1:
                    size = 1
                else:
                    size = args.size
            if args.minfreq is None:
                minfreq = 1
            else:
                minfreq = args.minfreq
            if args.minrange is None:
                minrange = 1
            else:
                minrange = args.minrange
            if args.tag1 is None:
                tag1 = [None]
            else:
                tag1 = args.tag1.strip().split(' ')
            if args.tag2 is None:
                tag2 = [None]
            else:
                tag2 = args.tag2.strip().split(' ')
            if args.tag3 is None:
                tag3 = [None]
            else:
                tag3 = args.tag3.strip().split(' ')
            if args.tag4 is None:
                tag4 = [None]
            else:
                tag4 = args.tag4.strip().split(' ') 
            # exec
            if self.corpus_in_use is not None:
                corpus_info = self.__corpus_info(self.corpus_in_use)
                corpus = Corpus(self.workspace,self.corpus_in_use,language=corpus_info['language'],encoding=corpus_info['encoding'])
                ngrams = corpus.ngrams(size=size,min_freq=minfreq,min_range=minrange,tag1=tag1,tag2=tag2,tag3=tag3,tag4=tag4, show_progress=True)
                ngrams.save_xls(self.workspace + self.corpus_in_use + '/output/ngrams.xlsx')
        except Exception as e:
                print(e) 
        
    #
    # CLUSTERS
    #
    
    def do_clusters(self,s):
        """\nDescription: Makes a list of clusters. 
        \nUsage: clusters -n [node] -size [size]
        \n\nOptions: 
        \n--minfreq [minfreq]     - (int) minimum frequency
        \n--minrange [minrange]   - (int) minimum frequency in corpus files
        \n--tag1 [pos]            - (str) POS tag for word 1
        \n--tag2 [pos]            - (str) POS tag for word 2
        \n--tag3 [pos]            - (str) POS tag for word 3
        \n--tag4 [pos]            - (str) POS tag for word 4
        """
        try:
            # parse args
            parser = argparse.ArgumentParser()
            parser.add_argument('-n', action='store', dest='node', type=str)
            parser.add_argument('-size', action='store', dest='size', type=int)
            parser.add_argument('--minfreq', action='store', dest='minfreq', type=int)
            parser.add_argument('--minrange', action='store', dest='minrange', type=int)
            parser.add_argument('--tag1', action='store', dest='tag1', type=str)
            parser.add_argument('--tag2', action='store', dest='tag2', type=str)
            parser.add_argument('--tag3', action='store', dest='tag3', type=str)
            parser.add_argument('--tag4', action='store', dest='tag4', type=str)
            args = parser.parse_args(s.split())
            # fix args
            if args.node is not None:
                node = args.node
            else:
                node = ''
            if args.size is not None:
                size = args.size
            else:
                size = args.size 
            if args.minfreq is None:
                minfreq = 1
            else:
                minfreq = args.minfreq
            if args.minrange is None:
                minrange = 1
            else:
                minrange = args.minrange
            if args.tag1 is None:
                tag1 = [None]
            else:
                tag1 = args.tag1.strip().split(' ')
            if args.tag2 is None:
                tag2 = [None]
            else:
                tag2 = args.tag2.strip().split(' ')
            if args.tag3 is None:
                tag3 = [None]
            else:
                tag3 = args.tag3.strip().split(' ')
            if args.tag4 is None:
                tag4 = [None]
            else:
                tag4 = args.tag4.strip().split(' ')
            # exec
            if self.corpus_in_use is not None:
                corpus_info = self.__corpus_info(self.corpus_in_use)
                corpus = Corpus(self.workspace,self.corpus_in_use,language=corpus_info['language'],encoding=corpus_info['encoding'])
                clusters = corpus.clusters(node,size=size,min_freq=minfreq,min_range=minrange,tag1=tag1,tag2=tag2,tag3=tag3,tag4=tag4, show_progress=True)
                clusters.save_xls(self.workspace + self.corpus_in_use + '/output/clusters.xlsx')
        except Exception as e:
                print(e)
        
    #
    # DISPERSION
    #
    
    def do_dispersion(self,s):
        """\nDescription: Creates a dispersion plot for each text file. 
        \nUsage: dispersion -n [node] 
        \n\nOptions: 
        \n--pos [pos]       - (str) POS tag(s)
        \n--regex [regex]   - (str) regular expression
        """
        try:
            # parse args
            parser = argparse.ArgumentParser()
            parser.add_argument('-n', action='store', dest='node',nargs='+', type=str)
            parser.add_argument('--pos', action='store', dest='pos', type=str)
            parser.add_argument('--regex', action='store', dest='regex', type=str)
            args = parser.parse_args(s.split())
            # fix args
            if len(args.node) > 1:
                node = ' '.join(args.node)
            else:
                node = args.node[0].strip()
            if args.pos is None:
                pos = None
            else:
                if len(args.pos) > 1:
                    pos = ' '.join(args.pos)
                else:
                    pos = args.pos[0]
            if args.regex is None:
                regex = False 
            else:
                if args.regex == '1' or args.regex == 'True':
                    regex = True
            # exec
            if self.corpus_in_use is not None:
                corpus_info = self.__corpus_info(self.corpus_in_use)
                corpus = Corpus(self.workspace,self.corpus_in_use,language=corpus_info['language'],encoding=corpus_info['encoding'])
                dispersion = corpus.dispersion(node,pos=pos,regex=regex, show_progress=True)
                dispersion.save_xls(self.workspace + self.corpus_in_use + '/output/dispersion.xlsx')
        except Exception as e:
                print(e)
    
    def do_keywords_dispersion(self,s):
        """\nDescription: Creates a dispersion plot for each text file. 
        \nUsage: keywords_dispersion 
        \n\nOptions: 
        \n--limit [number]       - (int) limit of keywords
        """
        try:
            # parse args
            parser = argparse.ArgumentParser()
            parser.add_argument('--limit', action='store', dest='limit', type=str)
            args = parser.parse_args(s.split())
            # fix args
            if args.limit is None:
                limit = 100
            else:
                limit = args.limit
            # exec
            if self.corpus_in_use is not None:
                corpus_info = self.__corpus_info(self.corpus_in_use)
                corpus = Corpus(self.workspace,self.corpus_in_use,language=corpus_info['language'],encoding=corpus_info['encoding'])
                wordlist = corpus.wordlist()
                keywords = corpus.keywords(wordlist)
                wordlist = None
                dispersion = corpus.keywords_dispersion(keywords,limit=limit, show_progress=True)
                keywords = None
                dispersion.save_xls(self.workspace + self.corpus_in_use + '/output/dispersion.xlsx')
        except Exception as e:
                print(e)
        

if __name__ == '__main__':
    prompt = KitPrompt()
    prompt.load_config()
    prompt.prompt = 'kitconc>'
    prompt.cmdloop('')




