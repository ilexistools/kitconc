# -*- coding: utf-8 -*-
# Author: jlopes@usp.br
import os, sys,subprocess  
from cmd import Cmd
import argparse
from kitconc import version 
from kitconc.kit_corpus import Corpus
from kitconc.kit_plots import CollGraph
from kitconc import kit_util  
from kitconc.core import Examples 
import re 
import pandas as pd 


  
class Kit(Cmd):
    
    def parse_arg(self,arg):
        if len(arg.strip()) != 0:
            arg = arg.replace('\t','')
            multi_spaces = re.compile(' +')
            multi_tabs = re.compile('\t+')
            arg = multi_spaces.sub(' ',arg)
            arg = arg.strip()
            args = []
            if arg.find('"') != -1 or arg.find("'") != -1:
                arg = arg.replace("'",'"')
                s = []
                status = 0
                for c in arg:
                    if status == 0 and c == '"':
                        status = 1
                    elif status == 0 and c == ' ':
                        s.append('\t')
                    elif status == 1 and c == '"':
                        s.append('\t')
                        status = 0
                    else:
                        s.append(c)
                args = ''.join(s)
                args = multi_tabs.sub('\t',args)
                args = args.split('\t')
            else:
                args = arg.split(' ')
        else:
            args = [] 
        
        if type(args) == list:
            arr = []
            if len(args) > 1:
                for a in args:
                    if len(a)!=0:
                        arr.append(a)
                args = arr 
        return args
    
    def get_parser(self,function_name):
        parser = None
        if function_name == 'help':
            parser = argparse.ArgumentParser()
            parser.prog= "help"
            parser.description='Shows help.'
        
        elif function_name == 'workspace':
            parser = argparse.ArgumentParser()
            parser.prog= "workspace"
            parser.description='Sets or shows the current workspace.'
            parser.add_argument('path', type=str, nargs='+',help='folder path for workspace')
        
        elif function_name == 'ls':
            parser = argparse.ArgumentParser()
            parser.prog= "ls"
            parser.description='Lists corpora or files in the current workspace or output folder.'
        
        elif function_name == 'exit':
            parser = argparse.ArgumentParser()
            parser.prog= "exit"
            parser.description='Ends the program.'
        
        elif function_name == 'quit':
            parser = argparse.ArgumentParser()
            parser.prog= "quit"
            parser.description='Ends the program.'
        
        elif function_name == 'version':
            parser = argparse.ArgumentParser()
            parser.prog= "version"
            parser.description='Show version.'
        
        elif function_name == 'cls':
            parser = argparse.ArgumentParser()
            parser.prog= "cls"
            parser.description='Clears screen.'
        
        elif function_name == 'clear':
            parser = argparse.ArgumentParser()
            parser.prog= "clear"
            parser.description='Clears screen.'
        
        elif function_name == 'home':
            parser = argparse.ArgumentParser()
            parser.prog= "home"
            parser.description='Returns to the current workspace root without any corpus selection.'
        
        elif function_name == 'delete':
            parser = argparse.ArgumentParser()
            parser.prog= "delete"
            parser.description='Deletes a corpus.'
        
        elif function_name == 'cleanse':
            parser = argparse.ArgumentParser()
            parser.prog= "cleanse"
            parser.description='Deletes all files from the output folder.'
            
        elif function_name == 'create':
            parser = argparse.ArgumentParser()
            parser.prog= "create"
            parser.description='Creates a new corpus from text files in a source folder.'
            parser.add_argument('name', type=str, nargs='?',help='corpus name for identification')
            parser.add_argument('source', type=str, nargs='?',help='source folder to add textfiles to the corpus')
            parser.add_argument('language', type=str, nargs='?',help='language')
            
        elif function_name == 'use':
            parser = argparse.ArgumentParser()
            parser.prog= "use"
            parser.description='Sets the current corpus in use.'
            parser.add_argument('name', type=str, nargs='?',help='corpus name')
        
        elif function_name =='open':
            parser = argparse.ArgumentParser()
            parser.prog= "open"
            parser.description='Opens a .xlsx file in the output folder using the default program.'
            parser.add_argument('filename', type=str, nargs='?',help='the name of the .xlsx file')
            
        elif function_name == 'wordlist':
            parser = argparse.ArgumentParser()
            parser.prog= "wordlist"
            parser.description='Makes a frequency word list from the current corpus'
            parser.add_argument('--lowercase', action='store', dest='lowercase', type=str, help='y or n default: y')
        
        elif function_name == 'keywords':
            parser = argparse.ArgumentParser()
            parser.prog= "keywords"
            parser.description='Extracts keywords from the current corpus.'
            parser.add_argument('--measure', action='store', dest='measure', type=str, help='statistic measure (chi-square or log-likelihood) default: log-likelihood')
            parser.add_argument('--stoplist', action='store', dest='stoplist', type=str, help='use the stoplist to filter keywords: (y or n) default:n')
        
        elif function_name == 'kwic':
            parser = argparse.ArgumentParser()
            parser.prog= "kwic"
            parser.description='Generates concordance lines in KWIC format.'
            parser.add_argument('node', type=str, nargs='?',help='search word or phrase')
            parser.add_argument('--pos', action='store', dest='pos', type=str, help='Part of speech (POS) for each search word')
            parser.add_argument('--case', action='store', dest='case', type=str, help='Case sensitive: (y or n) default: y')
            parser.add_argument('--regexp', action='store', dest='regexp', type=str, help='Enable case sensitive and regular expression for search word matching (y or n) default: n')
            parser.add_argument('--horizon', action='store', dest='horizon', type=int, help='Left and right horizon of words - default: 7')
            parser.add_argument('--width', action='store', dest='width', type=int, help='horizon width in characters')
            parser.add_argument('--sort1', action='store', dest='sort1', type=str, help='first sorting (L1,L2,L3,L4,L5,R1,R2,R3,R4 or R5)')
            parser.add_argument('--sort2', action='store', dest='sort2', type=str, help='second sorting (L1,L2,L3,L4,L5,R1,R2,R3,R4 or R5)')
            parser.add_argument('--sort3', action='store', dest='sort3', type=str, help='third sorting (L1,L2,L3,L4,L5,R1,R2,R3,R4 or R5)')
            parser.add_argument('--highlight', action='store', dest='highlight', type=str, help='highlights horizon (Example: L1 R1)')
            parser.add_argument('--limit', action='store', dest='limit', type=int, help='Number of concordance lines to return')
        
        elif function_name == 'concordance':
            parser = argparse.ArgumentParser()
            parser.prog= "concordance"
            parser.description='Generates concordance lines.'
            parser.add_argument('node', type=str, nargs='?',help='search word or phrase')
            parser.add_argument('--pos', action='store', dest='pos', type=str, help='Part of speech (POS) for each search word')
            parser.add_argument('--case', action='store', dest='case', type=str, help='Case sensitive: (y or n) default: y')
            parser.add_argument('--regexp', action='store', dest='regexp', type=str, help='Enable case sensitive and regular expression for search word matching (y or n) default: n')
            parser.add_argument('--limit', action='store', dest='limit', type=int, help='Number of concordance lines to return')
        
        elif function_name == 'collocates':
            parser = argparse.ArgumentParser()
            parser.prog= "collocates"
            parser.description='Extracts a list of collocates.'
            parser.add_argument('node', type=str, nargs='?',help='search word or phrase')
            parser.add_argument('--pos', action='store', dest='pos', type=str, help='Part of speech (POS) for each search word')
            parser.add_argument('--coll_pos', action='store', dest='coll_pos', type=str, help='Part of speech (POS) for collocates')
            parser.add_argument('--case', action='store', dest='case', type=str, help='Case sensitive: (y or n) default: y')
            parser.add_argument('--regexp', action='store', dest='regexp', type=str, help='Enable case sensitive and regular expression for search word matching (y or n) default: n')
            parser.add_argument('--left_span', action='store', dest='left_span', type=int, help='left span size for collocates')
            parser.add_argument('--right_span', action='store', dest='right_span', type=int, help='right span size for collocates')
        
        elif function_name == 'collgraph':
            parser = argparse.ArgumentParser()
            parser.prog= "collgraph"
            parser.description='Extracts a list of collocates and shows a plot.'
            parser.add_argument('node', type=str, nargs='?',help='search word or phrase')
            parser.add_argument('--pos', action='store', dest='pos', type=str, help='Part of speech (POS) for each search word')
            parser.add_argument('--coll_pos', action='store', dest='coll_pos', type=str, help='Part of speech (POS) for collocates')
            parser.add_argument('--case', action='store', dest='case', type=str, help='Case sensitive: (y or n) default: y')
            parser.add_argument('--regexp', action='store', dest='regexp', type=str, help='Enable case sensitive and regular expression for search word matching (y or n) default: n')
            parser.add_argument('--left_span', action='store', dest='left_span', type=int, help='left span size for collocates')
            parser.add_argument('--right_span', action='store', dest='right_span', type=int, help='right span size for collocates')
        
        elif function_name == 'wtfreq':
            parser = argparse.ArgumentParser()
            parser.prog= "wtfreq"
            parser.description='Generates a word tag frequency list based on corpus text files.'
            parser.add_argument('--lowercase', action='store', dest='lowercase', type=str, help='y or n default: y')
        
        elif function_name == 'wfreqinfiles':
            parser = argparse.ArgumentParser()
            parser.prog= "wfreqinfiles"
            parser.description='Generates a frequency list based on word occurrence in corpus text files.'
            parser.add_argument('--lowercase', action='store', dest='lowercase', type=str, help='y or n default: y')
        
        elif function_name == 'clusters':
            parser = argparse.ArgumentParser()
            parser.prog= "clusters"
            parser.description='Generates a list of clusters.'
            parser.add_argument('word', type=str, nargs='?',help='search word or phrase')
            parser.add_argument('--pos', action='store', dest='pos', type=str, help='Part of speech (POS) for each search word ')
            parser.add_argument('--size', action='store', dest='size', type=int, help='size of the cluster')
            parser.add_argument('--minfreq', action='store', dest='minfreq', type=int, help='minimum frequency of the cluster')
            parser.add_argument('--minrange', action='store', dest='minrange', type=int, help='minimum range frequency')
            parser.add_argument('--lowercase', action='store', dest='lowercase', type=str, help='y or n default: y')
            
        elif function_name == 'ngrams':
            parser = argparse.ArgumentParser()
            parser.prog= "ngrams"
            parser.description='Generates a list of n-grams.'
            parser.add_argument('size', type=int, nargs='?',help='size of the cluster (default: 3)')
            parser.add_argument('--pos', action='store', dest='pos', type=str, help='Part of speech (POS) for each word ')
            parser.add_argument('--minfreq', action='store', dest='minfreq', type=int, help='minimum frequency of the cluster')
            parser.add_argument('--minrange', action='store', dest='minrange', type=int, help='minimum range frequency')
            parser.add_argument('--lowercase', action='store', dest='lowercase', type=str, help='y or n default: y')
        
        elif function_name == 'dispersion':
            parser = argparse.ArgumentParser()
            parser.prog= "dispersion"
            parser.description='Generates dispersion plots.'
            parser.add_argument('node', type=str, nargs='?',help='search word or phrase')
            parser.add_argument('--pos', action='store', dest='pos', type=str, help='Part of speech (POS) for each search word')
            parser.add_argument('--case', action='store', dest='case', type=str, help='Case sensitive: (y or n) default: y')
            parser.add_argument('--regexp', action='store', dest='regexp', type=str, help='Enable case sensitive and regular expression for search word matching (y or n) default: n')
            parser.add_argument('--limit', action='store', dest='limit', type=int, help='Number of concordance lines to return')
        
        elif function_name == 'keywords_dispersion':
            parser = argparse.ArgumentParser()
            parser.prog= "keywords_dispersion"
            parser.description='Generates dispersion plots from keywords.'
            parser.add_argument('--lowercase', action='store', dest='lowercase', type=str, help='y or n default: y')
            parser.add_argument('--limit', action='store', dest='limit', type=int, help='Maximum number of keywords to use default: 25')
        
        elif function_name == 'text2utf8':
            parser = argparse.ArgumentParser()
            parser.prog= "text2utf8"
            parser.description='Converts textfiles to utf-8 encoding in a source folder.'
            parser.add_argument('source', type=str, nargs='?',help='source folder with textfiles to be converted')
            parser.add_argument('target', type=str, nargs='?',help='target folder to save the converted files')
        
        elif function_name == 'examples':
            parser = argparse.ArgumentParser()
            parser.prog= "examples"
            parser.description='Downloads examples from github.'
            parser.add_argument('--dest_path', action='store', dest='dest_path', type=str, help='Path to store examples')
            
            
        
        
        else:
            parser = None
        return parser
    
    #
    # OVERRIDES HELP 
    #
    
    def do_help(self,arg):
        if len(arg.strip())!= 0:
            parser = self.get_parser(arg)
            if parser != None:
                print('')
                parser.print_help() 
                print('')
        else:
            commands = []
            commands.append('\nDocumented commands (type help <topic>):')
            commands.append('========================================')
            function_names = []
            for item in sorted([func for func in dir(self) if callable(getattr(self, func))]):
                if item.startswith('do_'):
                    function_names.append( item.replace('do_',''))
            i = 0
            lines = []
            for func in function_names:
                i+=1
                lines.append( str(i) + ') ' + func)
            commands.append('\n'.join(lines))
            print('\n'.join(commands))
            print('')
            
    
    # load workspace
    def load_workspace(self):
        """Loads workspace """
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
        print ("\nKitconc " + version.__version__)
        
    
    def do_cls(self,args):
        """\nClear screen\n"""
        os.system('cls' if os.name=='nt' else 'clear') 
    
    def do_clear(self,args):
        """\nClear screen\n"""
        os.system('cls' if os.name=='nt' else 'clear')
    
    def do_ls(self,args):
        """\nDescription: Lists corpora or files in the output corpus folder.
        \nUsage: ls  
        """
        try:
            if self.workspace is not None:
                if self.corpus_in_use == None:
                    files = os.listdir(self.workspace)
                    corpora = []
                    df = pd.DataFrame(columns=['Name','Language','Texts','Tokens','Types','TTR'])
                    
                    for filename in files:
                        if os.path.isdir(self.workspace + filename):
                            if os.path.exists(self.workspace + filename + '/info.tab') == True:
                                tb = pd.read_table(self.workspace + filename + '/info.tab',header=None)
                                reg = []
                                for row in tb.itertuples(index=False):
                                    if row[0] not in ['workspace:','encoding:']:
                                        reg.append(row[1])
                                if len(reg) >= 6:
                                    df = df.append(pd.Series(reg, index=df.columns ), ignore_index=True)
                                corpora.append(filename)
                    if len(df) !=0:
                        print('')
                        print(df.head(len(df)))
                        print('')

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
    
    def do_open(self,arg):
        try:
            if self.corpus_in_use != None:
                output_path = self.workspace + self.corpus_in_use + '/output/'
                parser = self.get_parser('open')
                args = parser.parse_args(self.parse_arg(arg))
                if args.filename != None:
                    if args.filename.endswith('.xlsx')==False:
                        args.filename= args.filename + '.xlsx'
                    if os.path.exists(output_path + args.filename):
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
                    else:
                        print('\nFile does not exist.')
                        print('')
        except Exception as e:
                print(e)
    
        
    #
    # WORKSPACE 
    #
    
    def do_workspace(self,args):
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
    
    
    def __corpus_exists(self,corpus_name):
        flag = False
        if self.workspace is not None:
            if os.path.exists(self.workspace + '/' + corpus_name + '/info.tab'):
                flag = True
        return flag 
    
    
    def __corpus_info (self,corpus_name):
        info = {}
        with open(self.workspace + corpus_name + '/info.tab','r',encoding='utf-8') as fh:
            for line in fh:
                if len(line.strip()) !=0:
                    fields = line.strip().split('\t')
                    if len(fields) >= 2:
                        info[fields[0].replace(':','')]=fields[1]
        return info
    
    def do_create(self,arg):
        parser = self.get_parser('create')
        args = parser.parse_args(self.parse_arg(arg))
        corpus = Corpus(self.workspace,args.name,args.language)
        corpus.add_texts(args.source, show_progress=True)
    
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
    
    def do_wordlist(self,arg):
        parser = self.get_parser('wordlist')
        args = parser.parse_args(self.parse_arg(arg))
        try:
            if self.corpus_in_use is not None:
                corpus_info = self.__corpus_info(self.corpus_in_use)
                corpus = Corpus(self.workspace,self.corpus_in_use,corpus_info['language'])
                lowercase = True
                if args.lowercase is not None:
                    if args.lowercase == 'n':
                        lowercase = False 
                wordlist = corpus.wordlist(lowercase=lowercase,show_progress=True)
                wordlist.save_excel(self.workspace + self.corpus_in_use + '/output/wordlist.xlsx')
                wordlist = None
                print('')
        except Exception as e:
                print(e)
    
    def do_keywords(self,arg):
        parser = self.get_parser('keywords')
        args = parser.parse_args(self.parse_arg(arg))
        try:
            if self.corpus_in_use is not None:
                corpus_info = self.__corpus_info(self.corpus_in_use)
                corpus = Corpus(self.workspace,self.corpus_in_use,corpus_info['language'])
                measure = corpus.MEASURE_LOGLIKELIHOOD
                stoplist = []
                if args.measure !=None:
                    if args.measure == 'chi-square':
                        measure = corpus.MEASURE_CHI_SQUARE
                if args.stoplist !=None:
                    if args.stoplist == 'y':
                        with open (corpus.resource_data_path + 'stoplist_' + corpus.language + '.tab','r') as fh:
                            for line in fh:
                                if len(line.strip())!= 0:
                                    stoplist.append(line.strip())
                print('Wordlist:')
                wordlist = corpus.wordlist(show_progress=True)
                print('Keywords:')
                keywords = corpus.keywords(wordlist,measure=measure,stoplist=stoplist,show_progress=True)
                keywords.save_excel(self.workspace + self.corpus_in_use + '/output/keywords.xlsx')
                del wordlist
                del keywords 
                print('')
        except Exception as e:
            print(e)
    
    def do_kwic(self,arg):
        parser = self.get_parser('kwic')
        args = parser.parse_args(self.parse_arg(arg))
        try:
            if self.corpus_in_use is not None:
                corpus_info = self.__corpus_info(self.corpus_in_use)
                corpus = Corpus(self.workspace,self.corpus_in_use,corpus_info['language'])
                # args
                arg_pos = None
                arg_case_sensitive = False
                arg_regexp = False
                arg_horizon = 7
                arg_limit = None
                arg_width = 50
                arg_sort1 = None
                arg_sort2 = None
                arg_sort3 = None
                arg_highlight = None
                if args.pos != None:
                    arg_pos = args.pos 
                if args.case != None:
                    if args.case == 'y':
                        arg_case_sensitive = True
                    else: 
                        arg_case_sensitive = False
                if args.regexp != None:
                    if args.regexp == 'y':
                        arg_regexp = True
                    else:
                        arg_regexp = False
                if args.horizon !=None:
                    arg_horizon = int(args.horizon)  
                if args.limit != None:
                    arg_limit = int(args.limit)
                if args.width != None:
                    arg_width = args.width
                if args.sort1 != None:
                    arg_sort1 = args.sort1
                if args.sort2 != None:
                    arg_sort2 = args.sort2 
                if args.sort3 != None:
                    arg_sort3 = args.sort3 
                if args.highlight != None:
                    arg_highlight = args.highlight
                kwic = corpus.kwic(args.node,pos=arg_pos,case_sensitive=arg_case_sensitive,regexp=arg_regexp,horizon=arg_horizon,limit=arg_limit,show_progress=True)
                if arg_sort1 != None:
                    kwic.sort(arg_sort1, arg_sort2, arg_sort3) 
                kwic.save_excel(self.workspace + self.corpus_in_use + '/output/kwic.xlsx',width=arg_width,highlight=arg_highlight)
                print('')
        except Exception as e:
            print(e)
    
    def do_concordance(self,arg):
        parser = self.get_parser('concordance')
        args = parser.parse_args(self.parse_arg(arg))
        try:
            if self.corpus_in_use is not None:
                corpus_info = self.__corpus_info(self.corpus_in_use)
                corpus = Corpus(self.workspace,self.corpus_in_use,corpus_info['language'])
                # args
                arg_pos = None
                arg_case_sensitive = False
                arg_regexp = False
                arg_limit = None
                if args.pos != None:
                    arg_pos = args.pos 
                if args.case != None:
                    if args.case == 'y':
                        arg_case_sensitive = True
                    else: 
                        arg_case_sensitive = False
                if args.regexp != None:
                    if args.regexp == 'y':
                        arg_regexp = True
                    else:
                        arg_regexp = False
                if args.limit != None:
                    arg_limit = int(args.limit)
                concordance = corpus.concordance(args.node,pos=arg_pos,case_sensitive=arg_case_sensitive,regexp=arg_regexp,limit=arg_limit,show_progress=True)
                concordance.save_excel(self.workspace + self.corpus_in_use + '/output/concordance.xlsx')
                print('')
        except Exception as e:
            print(e)
    
    def do_collocates(self,arg):
        parser = self.get_parser('collocates')
        args = parser.parse_args(self.parse_arg(arg))
        try:
            if self.corpus_in_use is not None:
                corpus_info = self.__corpus_info(self.corpus_in_use)
                corpus = Corpus(self.workspace,self.corpus_in_use,corpus_info['language'])
                # args
                arg_pos = None
                arg_coll_pos = None 
                arg_case_sensitive = False
                arg_regexp = False
                arg_left_span = 5
                arg_right_span = 5
                if args.pos != None:
                    arg_pos = args.pos 
                if args.coll_pos !=None:
                    arg_coll_pos = args.coll_pos
                if args.case != None:
                    if args.case == 'y':
                        arg_case_sensitive = True
                    else: 
                        arg_case_sensitive = False
                if args.regexp != None:
                    if args.regexp == 'y':
                        arg_regexp = True
                    else:
                        arg_regexp = False
                if args.left_span != None:
                    arg_left_span = args.left_span
                if args.right_span != None:
                    arg_right_span = args.right_span 
                collocates = corpus.collocates(args.node,pos=arg_pos,coll_pos=arg_coll_pos,left_span=arg_left_span,right_span=arg_right_span,case_sensitive=arg_case_sensitive,regexp=arg_regexp,show_progress=True)
                collocates.save_excel(self.workspace + self.corpus_in_use + '/output/collocates.xlsx')
                print('')
        except Exception as e:
            print(e)
            
    def do_collgraph(self,arg):
        parser = self.get_parser('collgraph')
        args = parser.parse_args(self.parse_arg(arg))
        try:
            if self.corpus_in_use is not None:
                corpus_info = self.__corpus_info(self.corpus_in_use)
                corpus = Corpus(self.workspace,self.corpus_in_use,corpus_info['language'])
                # args
                arg_pos = None
                arg_coll_pos = None 
                arg_case_sensitive = False
                arg_regexp = False
                arg_left_span = 5
                arg_right_span = 5
                if args.pos != None:
                    arg_pos = args.pos 
                if args.coll_pos !=None:
                    arg_coll_pos = args.coll_pos
                if args.case != None:
                    if args.case == 'y':
                        arg_case_sensitive = True
                    else: 
                        arg_case_sensitive = False
                if args.regexp != None:
                    if args.regexp == 'y':
                        arg_regexp = True
                    else:
                        arg_regexp = False
                if args.left_span != None:
                    arg_left_span = args.left_span
                if args.right_span != None:
                    arg_right_span = args.right_span 
                collocates = corpus.collocates(args.node,pos=arg_pos,coll_pos=arg_coll_pos,left_span=arg_left_span,right_span=arg_right_span,case_sensitive=arg_case_sensitive,regexp=arg_regexp,show_progress=True)
                collgraph = CollGraph(node=args.node)
                collgraph.plot_graphcoll(collocates)
                print('')
        except Exception as e:
            print(e)
            
    def do_wtfreq(self,arg):
        parser = self.get_parser('wtfreq')
        args = parser.parse_args(self.parse_arg(arg))
        try:
            if self.corpus_in_use is not None:
                corpus_info = self.__corpus_info(self.corpus_in_use)
                corpus = Corpus(self.workspace,self.corpus_in_use,corpus_info['language'])
                # args
                arg_lowercase = True
                if args.lowercase != None:
                    if args.lowercase != 'y':
                        arg_lowercase = False
                wtfreq = corpus.wtfreq(lowercase=arg_lowercase,show_progress=True)
                wtfreq.save_excel(self.workspace + self.corpus_in_use + '/output/wtfreq.xlsx')
                print('')
        except Exception as e:
            print(e)
    
    def do_wfreqinfiles(self,arg):
        parser = self.get_parser('wfreqinfiles')
        args = parser.parse_args(self.parse_arg(arg))
        try:
            if self.corpus_in_use is not None:
                corpus_info = self.__corpus_info(self.corpus_in_use)
                corpus = Corpus(self.workspace,self.corpus_in_use,corpus_info['language'])
                # args
                arg_lowercase = True
                if args.lowercase != None:
                    if args.lowercase != 'y':
                        arg_lowercase = False
                wfreqinfiles = corpus.wfreqinfiles(lowercase=arg_lowercase,show_progress=True)
                wfreqinfiles.save_excel(self.workspace + self.corpus_in_use + '/output/wfreqinfiles.xlsx')
                print('')
        except Exception as e:
            print(e)
    
    def do_clusters(self,arg):
        parser = self.get_parser('clusters')
        args = parser.parse_args(self.parse_arg(arg))
        try:
            if self.corpus_in_use is not None:
                corpus_info = self.__corpus_info(self.corpus_in_use)
                corpus = Corpus(self.workspace,self.corpus_in_use,corpus_info['language'])
                # args
                arg_pos = None
                arg_size = 3 
                arg_minfreq = 1 
                arg_minrange = 1
                arg_lowercase = True 
                arg_lowercase = True
                
                if args.pos !=None:
                    arg_pos = args.pos 
                if args.size !=None:
                    arg_size = args.size 
                if args.minfreq !=None:
                    arg_minfreq = args.minfreq 
                if args.minrange != None:
                    arg_minrange = args.minrange
                if args.lowercase != None:
                    if args.lowercase != 'y':
                        args.lowercase = False 
                if args.lowercase != None:
                    if args.lowercase != 'y':
                        arg_lowercase = False
                clusters = corpus.clusters(args.word,pos=arg_pos,size=arg_size,minfreq=arg_minfreq,minrange=arg_minrange,lowercase=arg_lowercase,show_progress=True)
                clusters.save_excel(self.workspace + self.corpus_in_use + '/output/clusters.xlsx')
                print('')
        except Exception as e:
            print(e)
    
    def do_ngrams(self,arg):
        parser = self.get_parser('ngrams')
        args = parser.parse_args(self.parse_arg(arg))
        try:
            if self.corpus_in_use is not None:
                corpus_info = self.__corpus_info(self.corpus_in_use)
                corpus = Corpus(self.workspace,self.corpus_in_use,corpus_info['language'])
                # args
                arg_pos = None
                arg_size = 3 
                arg_minfreq = 1 
                arg_minrange = 1
                arg_lowercase = True 
                arg_lowercase = True
                
                if args.pos !=None:
                    arg_pos = args.pos 
                if args.size !=None:
                    arg_size = args.size 
                if args.minfreq !=None:
                    arg_minfreq = args.minfreq 
                if args.minrange != None:
                    arg_minrange = args.minrange
                if args.lowercase != None:
                    if args.lowercase != 'y':
                        args.lowercase = False 
                if args.lowercase != None:
                    if args.lowercase != 'y':
                        arg_lowercase = False
                ngrams = corpus.ngrams(pos=arg_pos,size=arg_size,minfreq=arg_minfreq,minrange=arg_minrange,lowercase=arg_lowercase,show_progress=True)
                ngrams.save_excel(self.workspace + self.corpus_in_use + '/output/ngrams.xlsx')
                print('')
        except Exception as e:
            print(e)
    
    def do_dispersion(self,arg):
        parser = self.get_parser('dispersion')
        args = parser.parse_args(self.parse_arg(arg))
        try:
            if self.corpus_in_use is not None:
                corpus_info = self.__corpus_info(self.corpus_in_use)
                corpus = Corpus(self.workspace,self.corpus_in_use,corpus_info['language'])
                # args
                arg_pos = None
                arg_case_sensitive = False
                arg_regexp = False
                arg_limit = None
                if args.pos != None:
                    arg_pos = args.pos 
                if args.case != None:
                    if args.case == 'y':
                        arg_case_sensitive = True
                    else: 
                        arg_case_sensitive = False
                if args.regexp != None:
                    if args.regexp == 'y':
                        arg_regexp = True
                    else:
                        arg_regexp = False
                if args.limit != None:
                    arg_limit = int(args.limit)
                dispersion = corpus.dispersion(args.node,pos=arg_pos,case_sensitive=arg_case_sensitive,regexp=arg_regexp,limit=arg_limit,show_progress=True)
                dispersion.save_excel(self.workspace + self.corpus_in_use + '/output/dispersion.xlsx')
                print('')
        except Exception as e:
            print(e)
    
    def do_keywords_dispersion(self,arg):
        parser = self.get_parser('keywords_dispersion')
        args = parser.parse_args(self.parse_arg(arg))
        try:
            if self.corpus_in_use is not None:
                corpus_info = self.__corpus_info(self.corpus_in_use)
                corpus = Corpus(self.workspace,self.corpus_in_use,corpus_info['language'])
                # args
                arg_lowercase = True 
                arg_limit = 25
                if args.lowercase != None:
                    arg_lowercase = args.lowercase
                if args.limit != None:
                    arg_limit = int(args.limit)
                wordlist = corpus.wordlist(show_progress=True)
                keywords = corpus.keywords(wordlist,show_progress=True)
                del wordlist 
                keywords_dispersion = corpus.keywords_dispersion(keywords,lowercase=arg_lowercase,limit=arg_limit,show_progress=True)
                keywords_dispersion.save_excel(self.workspace + self.corpus_in_use + '/output/keywords_dispersion.xlsx')
                print('')
        except Exception as e:
            print(e)
    
    def do_text2utf8(self,arg):
        parser = self.get_parser('text2utf8')
        args = parser.parse_args(self.parse_arg(arg))
        try:
            arg_source = args.source
            arg_target = args.target
            if os.path.exists(arg_source) == True:
                if os.path.isdir(arg_source) == True:
                    if os.path.exists(arg_target)==False:
                        os.mkdir(arg_target)
                    kit_util.files2utf8(arg_source, arg_target, 'mbcs', True)
                else:
                    print('The path is not a valid source folder or directory.')
            else:
                print('The path provided is not valid.')
        except Exception as e:
            print(e)
    
    def do_examples(self,arg):
        parser = self.get_parser('examples')
        args = parser.parse_args(self.parse_arg(arg))
        try:
            if args.dest_path !=None:
                ex = Examples()
                ex.download(dest_path=args.dest_path)
            else:
                ex = Examples()
                ex.download()
        except Exception as e:
            print(e)
        
    
    def run(self):
        print('Welcome to the Kitconc shell. Version: %s' % version.__version__)
        print('Type help or ? to list commands.\n')
        self.load_workspace()
        self.prompt = 'kitconc>'
        self.cmdloop('')
        
    

if __name__ == '__main__':
    Kit().run()



