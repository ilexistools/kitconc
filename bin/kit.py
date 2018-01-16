# -*- coding: utf-8 -*-
import os, sys,subprocess  
from cmd import Cmd
import argparse
from kitconc.corpus import Corpus
import pickle
import pandas as pd  

  
class KitPrompt(Cmd):
    
    def parse_args(self,s):
        """Parse args from command line"""
        try:
            args = s.strip().split(' ')
        except:
            args = s 
        return args
    
    def load_config(self):
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
                    print ('\n' +'\n'.join(corpora) + '\n')
                else:
                    output_path = self.workspace + self.corpus_in_use + '/output/'
                    files = os.listdir(output_path)
                    contents = []
                    for filename in files:
                        if os.path.isfile(output_path + filename):
                            contents.append(filename)
                    print ('\n' +'\n'.join(contents) + '\n')
            else:
                print('\nNo workspace set.\n')
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
        
    def do_leave(self,s):
        """\nDescription: Sets the current corpus as None.
        \nUsage: leave 
        """
        try:
            if self.corpus_in_use != None:
                self.corpus_in_use = None
                self.prompt = 'kitconc>'
                print ('')
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
                if str(args.filename).endswith('.tab'):
                    output_path  = self.workspace + self.corpus_in_use + '/output/'
                    tb = pd.read_table(output_path + args.filename)
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
        """\nDescription: Makes a frequency list from the current corpus. 
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
        \nUsage: kwic -n [node] --pos [pos] --limit [limit] --sort1 [first] --sort2 [second] --sort3 [third]  
        """
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('-n', action='store', dest='node', type=str)
            parser.add_argument('--pos', action='store', dest='pos', type=str)
            parser.add_argument('--width', action='store', dest='width', type=int)
            parser.add_argument('--limit', action='store', dest='limit', type=int)
            parser.add_argument('--sort1', action='store', dest='sort1', type=str)
            parser.add_argument('--sort2', action='store', dest='sort2', type=str)
            parser.add_argument('--sort3', action='store', dest='sort3', type=str)
            args = parser.parse_args(s.split())
            
            node = args.node.strip() 
            if args.pos is None:
                pos = None
            else:
                pos = args.pos
            
            if args.limit is None:
                limit = 0
            else:
                limit = args.limit 
            
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
            
            if args.width is None:
                width = 65
            else:
                width = args.width
            
            if self.corpus_in_use is not None:
                    corpus_info = self.__corpus_info(self.corpus_in_use)
                    corpus = Corpus(self.workspace,self.corpus_in_use,language=corpus_info['language'],encoding=corpus_info['encoding'])
                    kwic = corpus.kwic(node, pos, 10, limit, True)
                    kwic.sort(sort1, sort2, sort3)  
                    kwic.save_xls(self.workspace + self.corpus_in_use + '/output/kwic.xlsx', width)
        except Exception as e:
                print(e)
        
        

if __name__ == '__main__':
    prompt = KitPrompt()
    prompt.load_config()
    prompt.prompt = 'kitconc>'
    prompt.cmdloop('')




