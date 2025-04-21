# -*- coding: utf-8 -*-
# Author: jlopes@alumni.usp.br

"""Kitconc classes for the most common Corpus Linguistics methods and analysis.

The Corpora class can be used to create and manage corpora.
The Corpus class has all the functions and methods for data processing and analysis.

How to use
===========

Create a corpus:

    corpora = Corpora('workspace')
    corpus = corpora.create('corpus_name', 'language', 'source_texts_folder_path')

Open an existing corpus:
    corpora = Corpora('workspace')
    corpus = corpora.open('corpus_name')
    or:
    corpus = Corpus('workspace','corpus_name')

"""
import os
import sys
import time  
import subprocess
import pandas as pd
import collections
import platform
import shutil
import pickle
from kitconc import kit_tools
from kitconc import kit_util
from kitconc import kit_data
from kitconc import kit_models
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
    

class Corpus (object):
    """This class is the main component for doing corpus analysis in Kitconc."""
        
    def __init__(self, workspace, corpus_name, language='english', **kwargs):
        """
        Initializes the corpus environment by setting up the workspace, configuring paths,
        and loading or creating corpus information.

        This constructor performs the following steps:
        1. Determines the directory of the current script and sets the resource data path.
        2. Checks whether the code is running in an interactive shell (e.g., Jupyter Notebook).
        3. Defines constants for various statistical measures (mutual information, chi-square,
            log-likelihood, t-score).
        4. Normalizes the workspace path to ensure it ends with a '/'.
        5. Verifies if the workspace directory exists; if not, it creates the directory.
        6. Checks if a corpus with the given name already exists by looking for an 'info.tab'
            file in the corpus folder:
            - If it exists, loads corpus metadata (language and encoding) and sets up paths for
                output, data, and tagged data.
            - If it does not exist, assigns default encoding (UTF-8), creates the necessary
                folder structure (including subdirectories for data, output, npy, idx, tmp1, tmp2,
                tmp3), and saves the corpus information.
        7. Retrieves the Python interpreter name for further processing if needed.

        Parameters:
        workspace (str): The folder path where the corpus will be stored.
        corpus_name (str): A unique identifier for the corpus.
        language (str, optional): The language used for text processing. Defaults to 'english'.
        **kwargs: Additional keyword arguments (reserved for future use).

        Side Effects:
        - Creates directories in the specified workspace if they do not already exist.
        - Loads or saves corpus metadata to/from an 'info.tab' file within the corpus directory.
        """
        # script path
        self.__path = os.path.dirname(os.path.abspath(__file__))
        self.resource_data_path = self.__path + '/data/'
        # check environment
        self.__shell = False
        try:
            from IPython import get_ipython
            shell = get_ipython().__class__.__name__
            if shell == 'ZMQInteractiveShell' or shell == 'Shell':
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
        # get interpreter name
        self.__get_python_interpreter_name()


    # get executable interpreter
    def __get_python_interpreter_name(self):
        fullpath = str(sys.executable).replace('.exe', '').strip()
        self.interpreter_name = 'python'
        if platform.python_implementation() == 'CPython':
            if fullpath.endswith('python'):
                self.interpreter_name = 'python'
            elif fullpath.endswith('python3'):
                self.interpreter_name = 'python3'
            else:
                self.interpreter_name = 'python'
        else:
            if fullpath.endswith('pypy'):
                self.interpreter_name = 'pypy'
            elif fullpath.endswith('pypy3'):
                self.interpreter_name = 'pypy3'
            else:
                self.interpreter_name = 'pypy3'
        self.interpreter_name = sys.executable

    # corpus info
    def __save_corpus_info(self, workspace, corpus_name, language, encoding):
        """
        Saves corpus metadata to a file.

        This method writes the corpus information to an 'info.tab' file located in the corpus
        directory (i.e., workspace + corpus_name + '/'). The metadata includes the workspace path,
        corpus name, language, and text encoding. Each piece of information is separated by a tab
        and written on a separate line.

        Parameters:
        workspace (str): The directory path where the corpus is stored.
        corpus_name (str): The name used to identify the corpus.
        language (str): The language associated with the corpus.
        encoding (str): The text encoding format (e.g., 'utf-8') for the corpus files.
        """
        info = []
        info.append('workspace:' + '\t' + workspace)
        info.append('corpus name:' + '\t' + corpus_name)
        info.append('language:' + '\t' + language)
        info.append('encoding:' + '\t' + encoding)
        with open(workspace + corpus_name + '/info.tab', 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(info))

    
    def __load_corpus_info(self, workspace, corpus_name):
        """
        Loads corpus metadata from a file.

        This method reads the 'info.tab' file located in the corpus directory (i.e., workspace + corpus_name + '/').
        It processes each non-empty line by splitting it on the tab character to extract key-value pairs, where the key
        has its trailing colon removed. The resulting metadata is stored in a dictionary.

        Parameters:
        workspace (str): The directory path where the corpus is stored.
        corpus_name (str): The identifier name for the corpus.

        Returns:
        dict: A dictionary containing corpus metadata with keys such as 'workspace', 'corpus name', 'language', and 'encoding'.
        """
        info = {}
        with open(workspace + corpus_name + '/info.tab', 'r', encoding='utf-8') as fh:
            for line in fh:
                if len(line.strip()) != 0:
                    fields = line.strip().split('\t')
                    if len(fields) >= 2:
                        info[fields[0].replace(':', '')] = fields[1]
        return info

    
    # show progress function
    
    def __progress(self, count, total, suffix=''):
        """
        Displays a progress bar in the terminal.

        This method prints a dynamic progress bar to the standard output (sys.stdout) to indicate the current progress
        of an ongoing task. It calculates the percentage of completion based on the current count and total, and then
        constructs a bar visualization with '=' characters representing progress and '-' characters representing the remainder.
        The progress bar is updated only if the instance is not running in an interactive shell (e.g., Jupyter Notebook).

        Parameters:
        count (int): The current progress count.
        total (int): The total count corresponding to 100% completion.
        suffix (str, optional): An optional string to be appended at the end of the progress bar output.
        """
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


    def has_empty_files(self, folder_path):
        """
        Check if a folder contains any empty files.

        Args:
            folder_path (str): The path to the folder.

        Returns:
            bool: True if at least one empty file is found, False otherwise.
        """
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path) and os.path.getsize(file_path) == 0:
                    return True
        return False

    def add_texts(self, source_folder, **kwargs):
        """
        Adds texts from a source folder to the corpus.

        This method imports text files from the specified source folder into the corpus.
        It first checks for any empty files and raises a ValueError if one is found.
        Depending on the provided options, it can either process the texts as already tagged or tag them
        on-the-fly using a language model. If no language model is provided, the method checks for a saved
        language model and uses it if available; otherwise, it relies on external tagging and indexing scripts.
        
        The process includes:
        1. Validating the source folder to ensure no empty files are present.
        2. Handling optional keyword arguments:
            - tagged (bool): Indicates if texts are already tagged (default is False).
            - language_model (object): A language model for tokenization and tagging (default is None).
            - show_progress (bool): If True, prints progress messages and timing information (default is False).
        3. Normalizing the source folder path to ensure it ends with a '/'.
        4. If the corpus language is set to 'no-tagging', a dummy language model is used.
        5. If no language model is provided:
            a. If texts are not tagged and no saved model is found:
                - Executes an external tagging script to tag the texts.
                - Executes an indexing script to create corpus indexes.
            b. If a saved language model is found:
                - Loads the model from a pickle file.
                - Tags texts manually and writes the tagged output to a temporary directory.
                - Loads the tagged corpus using an external script.
                - Runs the indexing script and then removes the temporary directory.
        6. If a language model is provided:
            - Tags texts on-the-fly and saves the output in a temporary directory.
            - Loads the tagged corpus and builds indexes using external scripts.
            - Cleans up the temporary directory.
        7. Updates the corpus metadata file with the number of text files processed and the source folder path.
        8. Optionally prints the total processing time if progress display is enabled.
        9. Attempts to remove any residual temporary directories (tmp1, tmp2, tmp3).

        Parameters:
        source_folder (str): The folder path where the source texts are stored.
        tagged (bool, optional): If True, indicates that the texts are already tagged. Defaults to False.
        language_model (object, optional): A language model for tokenization and tagging. Defaults to None.
        show_progress (bool, optional): If True, prints progress messages and timing information. Defaults to False.

        Raises:
        ValueError: If an empty file is found in the source folder.
        """
        if self.has_empty_files(source_folder):
            raise ValueError(f"Empty file found. Identify and remove empty files in {source_folder} before proceeding.")
        
        # args 
        tagged = kwargs.get('tagged', False)
        language_model = kwargs.get('language_model', None)
        show_progress = kwargs.get('show_progress', False)
        if not source_folder.endswith('/'):
            source_folder = source_folder + '/'
        
        # time start
        if show_progress:
            t0 = time.time()
            print('New corpus:')
        
        # check generic model for adding texts without tagging
        if self.language == 'no-tagging':
            language_model = kit_models.DummyModel
        
        # make indexes and tag texts as needed
        if language_model is None:
            # check if there's a saved language model
            has_saved_model = False 
            lm_path = self.__path + '/data/' + self.language + '_model.pickle'
            if os.path.exists(lm_path):
                has_saved_model = True
            # For untagged texts
            if not tagged:
                if not has_saved_model:
                    if show_progress:
                        print('Tagging...')
                    resources_path = self.__path + '/data/'
                    subprocess.call([self.interpreter_name, self.__path + '/tagging.py', resources_path, self.workspace, self.corpus_name, self.language, source_folder])
                    if show_progress:
                        print('Making indexes...')
                    subprocess.call([self.interpreter_name, self.__path + '/indexing.py', self.workspace, self.corpus_name, self.language])
                else:
                    if show_progress:
                        print('Tagging...')
                    # Create temp folder
                    if os.path.exists(self.workspace + self.corpus_name + '/data/tmp0'):
                        shutil.rmtree(self.workspace + self.corpus_name + '/data/tmp0/')
                    os.mkdir(self.workspace + self.corpus_name + '/data/tmp0/')
                    # Load model 
                    with open(self.__path + '/data/' + self.language + '_model.pickle', 'rb') as fh:
                        language_model = pickle.load(fh)
                    # Tag texts manually
                    files = os.listdir(source_folder)
                    for filename in files:
                        with open(source_folder + filename, 'r', encoding='utf-8') as fh:
                            text = fh.read()
                        doc = language_model(text)
                        tagged_sents = []
                        for sent in doc.sents:
                            tagged_sents.append(' '.join([(token.text + '/' + token.pos_) for token in sent if len(token.text.strip()) != 0]))
                        with open(self.workspace + self.corpus_name + '/data/tmp0/' + filename, 'w', encoding='utf-8') as fh:
                            fh.write('\n'.join(tagged_sents))
                    if show_progress:
                        print('Loading tagged corpus...')
                    resources_path = self.__path + '/data/'
                    subprocess.call([self.interpreter_name, self.__path + '/tagged.py', resources_path, self.workspace, self.corpus_name, self.language, self.workspace + self.corpus_name + '/data/tmp0/'])
                    if show_progress:
                        print('Making indexes...')
                    subprocess.call([self.interpreter_name, self.__path + '/indexing.py', self.workspace, self.corpus_name, self.language])
                    # Remove temporary folder
                    shutil.rmtree(self.workspace + self.corpus_name + '/data/tmp0/')
            else:
                if show_progress:
                    print('Loading tagged corpus...')
                resources_path = self.__path + '/data/'
                subprocess.call([self.interpreter_name, self.__path + '/tagged.py', resources_path, self.workspace, self.corpus_name, self.language, source_folder])
                if show_progress:
                    print('Making indexes...')
                subprocess.call([self.interpreter_name, self.__path + '/indexing.py', self.workspace, self.corpus_name, self.language])
        else:
            # Use language model on the fly to tag texts (e.g., using spaCy)
            if show_progress:
                print('Tagging...')
            # Create temporary folder
            if os.path.exists(self.workspace + self.corpus_name + '/data/tmp0'):
                shutil.rmtree(self.workspace + self.corpus_name + '/data/tmp0/')
            os.mkdir(self.workspace + self.corpus_name + '/data/tmp0/')
            # Tag texts
            files = [file for file in os.listdir(source_folder) if file not in ['.DS_Store', 'desktop.ini']]
            for filename in files:
                print(filename)
                with open(source_folder + filename, 'r', encoding='utf-8', errors='replace') as fh:
                    text = fh.read()
                doc = language_model(text)
                tagged_sents = []
                for sent in doc.sents:
                    tagged_sents.append(' '.join([(token.text + '/' + token.pos_) for token in sent if len(token.text.strip()) != 0]))
                with open(self.workspace + self.corpus_name + '/data/tmp0/' + filename, 'w', encoding='utf-8') as fh:
                    fh.write('\n'.join(tagged_sents))
            # Load tagged texts    
            if show_progress:
                print('Loading tagged corpus...')
            resources_path = self.__path + '/data/'
            subprocess.call([self.interpreter_name, self.__path + '/tagged.py', resources_path, self.workspace, self.corpus_name, self.language, self.workspace + self.corpus_name + '/data/tmp0/'])
            if show_progress:
                print('Making indexes...')
            subprocess.call([self.interpreter_name, self.__path + '/indexing.py', self.workspace, self.corpus_name, self.language])
            # Remove temporary folder
            shutil.rmtree(self.workspace + self.corpus_name + '/data/tmp0/')
        
        # Append source information to corpus info file
        ntexts = len(os.listdir(source_folder))
        with open(self.workspace + self.corpus_name + '/info.tab', 'a', encoding='utf-8') as fh:
            fh.write('\nTextfiles:\t%s\nSource:\t%s' % (ntexts, source_folder))
        
        # Time end and print total time if progress display is enabled
        if show_progress:
            t1 = time.time()
            total_time = round(t1 - t0, 2)
            print('Total time: %s seconds' % total_time)
        
        # Delete temporary folders
        try:
            shutil.rmtree(self.workspace + self.corpus_name + '/data/tmp1/')
            shutil.rmtree(self.workspace + self.corpus_name + '/data/tmp2/')
            shutil.rmtree(self.workspace + self.corpus_name + '/data/tmp3/')
        except Exception as e:
            print('Error deleting temp folders')
            print(e)

    

    def wordlist(self, **kwargs):
        """
        Generates a frequency word list based on text files.

        This method processes text files from the workspace using the specified corpus name and language.
        It computes important statistics including tokens, types, type-token ratio, and the count of hapaxes.
        Additionally, it constructs a pandas DataFrame containing the word list with the following columns:
        - 'N': the position or ranking of the word,
        - 'WORD': the identified word,
        - 'FREQUENCY': the number of occurrences,
        - '%': the percentage of the word's frequency relative to the total word count.

        Keyword Arguments:
        - lowercase (bool): If True (default), converts all letters to lowercase.
        - min_freq (int): Minimum frequency required for a word to be included in the list (default is 1).
        - show_progress (bool): If True, prints progress messages and the total execution time (default is False).

        Returns:
        Wordlist: An object containing:
            - tokens: A list of all extracted tokens.
            - types: The total number of unique words.
            - typetoken: The type-token ratio, rounded to two decimal places.
            - hapax: The count of words that appear only once.
            - df: A pandas DataFrame with the word list data, filtered to include only words with a frequency
                    greater than or equal to min_freq.
        """
        # args
        show_progress = kwargs.get('show_progress', False)
        min_freq = kwargs.get('min_freq', 1)
        lowercase = kwargs.get('lowercase', True)
        
        # time start
        if show_progress:
            print('Running...')
            t0 = time.time()
        
        # make
        tokens, types, type_token, hapax, xwordlist = make_wordlist(self.workspace, self.corpus_name, self.language, lowercase)
        wlst = kit_tools.Wordlist(tokens=tokens, types=types, typetoken=round(type_token, 2), hapax=hapax)
        wlst.df = pd.DataFrame(xwordlist, columns=['N', 'WORD', 'FREQUENCY', '%'])
        wlst.df = wlst.df[wlst.df.FREQUENCY >= min_freq]
        wlst.df['%'] = wlst.df['%'].apply(lambda x: round(x, 2))
        
        # time end
        if show_progress:
            t1 = time.time()
            total_time = round(t1 - t0, 2)
            print('')
            print('Total time: {} seconds'.format(total_time))
        
        return wlst

    
    def keywords(self, **kwargs):
        """
        Extracts and ranks keywords from the corpus wordlist based on a chosen statistical measure.

        This method computes keywords by applying a statistical measure to the wordlist of the corpus.
        It filters out words present in an optional stoplist, sorts the remaining words by their keyness score,
        and assigns a ranking. The method supports two statistical measures: 'log-likelihood' (default) and 'chi-square'.
        
        Keyword Arguments:
        - measure (str): The statistical measure to use for keyword extraction. Acceptable values are 
                        'log-likelihood' (default) and 'chi-square'. Any other value defaults to 'log-likelihood'.
        - stoplist (list): A list of words to exclude from the keyword extraction process.
        - show_progress (bool): If True, prints progress messages and timing information during processing.
        
        Returns:
        Keywords: An object containing a pandas DataFrame with the following columns:
            - 'N': Ranking index of the keyword.
            - 'WORD': The keyword.
            - 'FREQUENCY': The number of occurrences of the keyword in the corpus.
            - 'KEYNESS': The computed keyness score for the keyword, rounded to two decimal places.
        """
        # args
        measure = kwargs.get('measure', 'log-likelihood')
        stoplist = kwargs.get('stoplist', [])
        show_progress = kwargs.get('show_progress', False)
        
        # get statistical measure identifier
        if measure == 'log-likelihood':
            stat = 1
        elif measure == 'chi-square':
            stat = 2
        else:
            stat = 1
        
        # time start
        if show_progress:
            print('Running...')
            t0 = time.time()
        
        # Generate keywords table
        kwlst = kit_tools.Keywords()
        k = make_keywords(self.workspace, self.corpus_name, self.language, stat)
        kwlst.df = pd.DataFrame(k, columns=['N', 'WORD', 'FREQUENCY', 'KEYNESS'])
        k = None  # Free memory
        
        # Filter out words in stoplist
        kwlst.df = kwlst.df[~kwlst.df['WORD'].isin(stoplist)]
        
        # Sort by keyness score, reassign ranking, and round keyness values
        kwlst.df['KEYNESS'] = kwlst.df['KEYNESS'].apply(lambda x: round(x, 2))
        kwlst.df.sort_values('KEYNESS', ascending=False, inplace=True)
        kwlst.df['N'] = [i + 1 for i in range(len(kwlst.df))]
        kwlst.df.reset_index(drop=True, inplace=True)
        
        # time end
        if show_progress:
            t1 = time.time()
            total_time = round(t1 - t0, 2)
            print('')
            print('Total time: %s seconds' % total_time)
        
        return kwlst

    
    def wtfreq(self, **kwargs):
        """
        Generates a word-tag frequency list based on the corpus text files.

        This method processes the text files within the corpus to build a frequency table that
        contains the occurrence count and percentage for each word along with its associated tag.
        It also allows optional conversion of letters to lowercase and displays progress information.

        Keyword Arguments:
        - lowercase (bool): If True (default), converts all letters to lowercase.
        - show_progress (bool): If True, prints progress messages and timing information during execution.

        Returns:
        WTfreq: An object containing a pandas DataFrame with the following columns:
            - 'N': Sequential index for the word-tag entries.
            - 'WORD': The word extracted from the corpus.
            - 'TAG': The corresponding tag (e.g., part-of-speech).
            - 'FREQUENCY': The number of occurrences of the word-tag pair.
            - '%': The frequency percentage relative to the total, rounded to two decimal places.
        """
        # args
        lowercase = kwargs.get('lowercase', True)
        show_progress = kwargs.get('show_progress', False)
        
        # time start
        if show_progress:
            print('Running...')
            t0 = time.time()
        
        # Generate word-tag frequency list
        lst_wt = make_wtfreq(self.workspace, self.corpus_name, self.language, lowercase)
        
        wt = kit_tools.WTfreq()
        wt.df = pd.DataFrame(lst_wt, columns=['N', 'WORD', 'TAG', 'FREQUENCY', '%'])
        
        # Process DataFrame: round percentages, sort by frequency, and reassign sequential indices
        wt.df['%'] = wt.df['%'].apply(lambda x: round(x, 2))
        wt.df.sort_values('FREQUENCY', ascending=False, inplace=True)
        wt.df['N'] = [i + 1 for i in range(len(wt.df))]
        wt.df.reset_index(drop=True, inplace=True)
        
        # time end and print progress
        if show_progress:
            self.__progress(100, 100, '')
            t1 = time.time()
            total_time = round(t1 - t0, 2)
            print('')
            print('Total time: %s seconds' % total_time)
        
        return wt

    
    def wfreqinfiles(self, **kwargs):
        """
        Generates a frequency list based on word occurrences across corpus text files.

        This method analyzes the corpus text files to determine how frequently each word appears
        across the files (i.e., in how many files each word occurs). It allows optional conversion
        of the text to lowercase and provides progress updates if requested.

        Keyword Arguments:
        - lowercase (bool): If True (default), converts all letters to lowercase.
        - show_progress (bool): If True, prints progress messages and timing information during processing.

        Returns:
        Wfreqinfiles: An object containing a pandas DataFrame with the following columns:
            - 'N': Sequential index for each word.
            - 'WORD': The word extracted from the corpus.
            - 'RANGE': The number of files in which the word appears.
            - '%': The percentage frequency of the word across the corpus, rounded to two decimal places.
        """
        # args
        lowercase = kwargs.get('lowercase', True)
        show_progress = kwargs.get('show_progress', False)
        
        # time start
        if show_progress:
            print('Running...')
            t0 = time.time()
        
        # process word frequency in files
        lst_fif = make_wfreqinfiles(self.workspace, self.corpus_name, self.language, lowercase)
        fif = kit_tools.Wfreqinfiles()
        fif.df = pd.DataFrame(lst_fif, columns=['N', 'WORD', 'RANGE', '%'])
        lst_fif = None
        
        # Process DataFrame: round percentages, sort by RANGE, and reassign sequential indices
        fif.df['%'] = fif.df['%'].apply(lambda x: round(x, 2))
        fif.df.sort_values('RANGE', ascending=False, inplace=True)
        fif.df['N'] = [i + 1 for i in range(len(fif.df))]
        fif.df.reset_index(drop=True, inplace=True)
        
        # time end and print progress
        if show_progress:
            self.__progress(100, 100, '')
            t1 = time.time()
            total_time = round(t1 - t0, 2)
            print('')
            print('Total time: %s seconds' % total_time)
        
        return fif

    
    def kwic(self, node, **kwargs):
        """
        Generates concordance lines for a specified search term or phrase within the corpus.

        This method searches for the given word or phrase (up to 4 words) in the corpus and extracts
        concordance lines that provide the context (words to the left and right) of each occurrence.
        Optional parameters allow filtering by part of speech, controlling case sensitivity, and using
        regular expressions for more advanced matching.

        Parameters:
        node (str): The search word or phrase for which concordance lines will be generated.

        Keyword Arguments:
        pos (str or list, optional): The part of speech (POS) tag(s) for the search term(s). Default is None.
        case_sensitive (bool, optional): If True, the search will be case-sensitive. Default is False.
        regexp (bool, optional): If True, the search term is treated as a regular expression. Default is False.
        horizon (int, optional): The number of words to include on each side of the search term in the concordance. Default is 10.
        limit (int, optional): The maximum number of concordance lines to return. If None, all matches are returned.
        show_progress (bool, optional): If True, prints progress messages and timing information during processing. Default is False.

        Returns:
        Kwic: An object containing a pandas DataFrame with the concordance data. The DataFrame includes the following columns:
                - 'N': Sequential index of the concordance line.
                - 'LEFT': The words to the left of the search term.
                - 'NODE': The search term.
                - 'RIGHT': The words to the right of the search term.
                - 'FILENAME': The name of the file where the match was found.
                - 'TOKEN_ID': The token ID of the match.
                - 'SENT_ID': The sentence ID containing the match.
                - 'FILE_ID': The identifier for the file.
        """
        # args
        node = node.strip()
        pos = kwargs.get('pos', None)
        case_sensitive = kwargs.get('case_sensitive', False)
        regexp = kwargs.get('regexp', False)
        horizon = kwargs.get('horizon', 10)
        limit = kwargs.get('limit', None)
        show_progress = kwargs.get('show_progress', False)
        
        # time start
        if show_progress:
            print('Running...')
            t0 = time.time()
        
        # Process concordance lines
        nl, lst_kwic = make_kwic(self.workspace, self.corpus_name, node, pos, case_sensitive, regexp, horizon)
        kwic = kit_tools.Kwic(node_length=nl)
        kwic.df = pd.DataFrame(lst_kwic, columns=['N', 'LEFT', 'NODE', 'RIGHT', 'FILENAME', 'TOKEN_ID', 'SENT_ID', 'FILE_ID'])
        lst_kwic = None
        
        # Limit results if a limit is specified
        if limit is not None:
            kwic.df = kwic.df.head(limit)
        
        # Reset indices to ensure sequential numbering
        kwic.df['N'] = [i + 1 for i in range(len(kwic.df))]
        kwic.df.reset_index(drop=True, inplace=True)
        
        # time end and progress update
        if show_progress:
            self.__progress(100, 100, '')
            t1 = time.time()
            total_time = round(t1 - t0, 2)
            print('')
            print('Total time: %s seconds' % total_time)
        
        return kwic

    
    def concordance(self, node: str, **kwargs):
        """
        Generates concordance lines for a specified search term or phrase.

        This method searches the corpus for occurrences of a specified search term or phrase (maximum of 4 words)
        and extracts the corresponding concordance lines, providing contextual information for each occurrence.
        Optional parameters allow for filtering by part-of-speech, enforcing case sensitivity, and treating the 
        search term as a regular expression.

        Parameters:
        node (str): The search term or phrase for which to generate concordance lines.

        Keyword Arguments:
        pos (str or list, optional): The part-of-speech tag(s) associated with the search term(s). Default is None.
        case_sensitive (bool, optional): If True, the search will be case-sensitive. Default is False.
        regexp (bool, optional): If True, the search term is interpreted as a regular expression. Default is False.
        limit (int, optional): The maximum number of concordance lines to return. If None, returns all matching lines.
        show_progress (bool, optional): If True, prints progress messages and timing information. Default is False.

        Returns:
        Concordance: An object containing a pandas DataFrame with the following columns:
            - 'N': A sequential index for each concordance line.
            - 'CONCORDANCE': The complete concordance line containing the search term.
            - 'FILENAME': The name of the file where the concordance line was found.
            - 'TOKEN_ID': The token identifier for the search term.
            - 'SENT_ID': The sentence identifier containing the search term.
            - 'FILE_ID': The file identifier.
        """
        # args
        node = node.strip()
        pos = kwargs.get('pos', None)
        case_sensitive = kwargs.get('case_sensitive', False)
        regexp = kwargs.get('regexp', False)
        limit = kwargs.get('limit', None)
        show_progress = kwargs.get('show_progress', False)
        
        # time start
        if show_progress:
            print('Running...')
            t0 = time.time()
        
        # Process concordance lines
        nl, lst_conc = make_concordance(self.workspace, self.corpus_name, node, pos, case_sensitive, regexp)
        conc = kit_tools.Concordance(node_length=nl)
        conc.df = pd.DataFrame(lst_conc, columns=['N', 'CONCORDANCE', 'FILENAME', 'TOKEN_ID', 'SENT_ID', 'FILE_ID'])
        lst_conc = None
        
        # Limit results if a limit is specified
        if limit is not None:
            conc.df = conc.df.head(limit)
        
        # Reset indices for sequential numbering
        conc.df['N'] = [i + 1 for i in range(len(conc.df))]
        conc.df.reset_index(drop=True, inplace=True)
        
        # time end and print progress
        if show_progress:
            self.__progress(100, 100, '')
            t1 = time.time()
            total_time = round(t1 - t0, 2)
            print('')
            print('Total time: %s seconds' % total_time)
        
        return conc

    
    def collocates(self, node: str, **kwargs):
        """
        Extracts a list of collocates for a specified search word.

        This method retrieves collocates from the corpus for the given search word by analyzing the context
        within specified spans to the left and right of the word. It allows filtering by part-of-speech (POS)
        tags for both the search word and the collocates, and supports options for case sensitivity and regular
        expression matching. Additionally, a statistical measure (either t-score or mutual information) is used
        to assess the strength of the association between the search word and its collocates.

        Parameters:
        node (str): The search word for which collocates will be extracted.

        Keyword Arguments:
        pos (str or list, optional): Part-of-speech tag(s) for the search word. Default is None.
        coll_pos (str or list, optional): Part-of-speech tag(s) to filter the collocates. Default is None.
        case_sensitive (bool, optional): If True, the search is case-sensitive. Default is False.
        regexp (bool, optional): If True, treats the search word as a regular expression. Default is False.
        left_span (int, optional): Number of words to consider to the left of the search word. Default is 5.
        right_span (int, optional): Number of words to consider to the right of the search word. Default is 5.
        lowercase (bool, optional): If True, converts text to lowercase before processing. Default is True.
        measure (str or int, optional): Statistical measure for association; use 't-score' (default) or 'mutual information'.
                                        If a string is provided, it will be mapped to an internal identifier.
        limit (int, optional): Maximum number of collocate results to return. If None, all results are returned.
        show_progress (bool, optional): If True, prints progress messages and execution time. Default is False.

        Returns:
        Collocates: An object containing a pandas DataFrame with the following columns:
            - 'N': Sequential index of the collocate entry.
            - 'WORD': The collocate word.
            - 'FREQUENCY': The frequency of the collocate in the corpus.
            - 'LEFT': The left context words.
            - 'RIGHT': The right context words.
            - 'ASSOCIATION': The association score (rounded to two decimal places) indicating the strength
                            of the collocate's relationship with the search word.
        """
        # args
        node = node.strip()
        pos = kwargs.get('pos', None)
        coll_pos = kwargs.get('coll_pos', None)
        case_sensitive = kwargs.get('case_sensitive', False)
        regexp = kwargs.get('regexp', False)
        left_span = kwargs.get('left_span', 5)
        right_span = kwargs.get('right_span', 5)
        lowercase = kwargs.get('lowercase', True)
        measure = kwargs.get('measure', 1)
        limit = kwargs.get('limit', None)
        show_progress = kwargs.get('show_progress', False)
        
        # time start
        if show_progress:
            print('Running...')
            t0 = time.time()
        
        # Determine statistical measure
        if measure == 't-score':
            measure = 1
        elif measure == 'mutual information':
            measure = 2
        
        # Generate collocates list
        lst_coll = make_collocates(self.workspace, self.corpus_name, node, pos, case_sensitive, regexp, 
                                coll_pos, lowercase, left_span, right_span, measure)
        coll = kit_tools.Collocates()
        coll.df = pd.DataFrame(lst_coll, columns=['N', 'WORD', 'FREQUENCY', 'LEFT', 'RIGHT', 'ASSOCIATION'])
        lst_coll = None
        
        # Sort by association score (descending)
        coll.df.sort_values('ASSOCIATION', ascending=False, inplace=True)
        
        # Apply limit if specified
        if limit is not None:
            coll.df = coll.df.head(limit)
        
        # Reset indexes and round association values
        coll.df['ASSOCIATION'] = coll.df['ASSOCIATION'].apply(lambda x: round(x, 2))
        coll.df['N'] = [i + 1 for i in range(len(coll.df))]
        coll.df.reset_index(drop=True, inplace=True)
        
        # time end and display progress if required
        if show_progress:
            self.__progress(100, 100, '')
            t1 = time.time()
            total_time = round(t1 - t0, 2)
            print('')
            print('Total time: %s seconds' % total_time)
        
        return coll

        
    
    def compared_collocates(self, coll1, coll2, **kwargs):
        """
        Compares two sets of collocates and returns a comparison table.

        This method takes two collocate sets (instances of Collocates) and compares them based on
        their frequency and association scores. It filters out collocates with an association score 
        below a specified cutoff, calculates the percentage difference between the association scores 
        of the two sets, and compiles the results into a tabular format. The resulting table includes:
        - 'N': Sequential index.
        - 'WORD': The collocate word.
        - 'FREQ1': Frequency of the word in the first collocate set.
        - 'FREQ2': Frequency of the word in the second collocate set.
        - 'ASSOCIATION1': Association score of the word in the first set.
        - 'ASSOCIATION2': Association score of the word in the second set.
        - 'DIFFERENCE': Percentage difference between the two association scores.

        Parameters:
        coll1 (Collocates): The first set of collocates.
        coll2 (Collocates): The second set of collocates.

        Keyword Arguments:
        stat_cutoff (int, optional): The minimum association score for a collocate to be included 
                                    in the comparison (default is 0).
        show_progress (bool, optional): If True, prints progress messages during processing (default is False).

        Returns:
        ComparedCollocates: An object containing a pandas DataFrame with the comparison results.
        """
        # kwargs
        stat_cutoff = kwargs.get('stat_cutoff', 0)
        show_progress = kwargs.get('show_progress', False)
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        # get all data in dictionaries
        # and filter association measures with stat_cutoff:
        # words = all words from coll1 and coll2
        # w1 = coll1 data dict
        words = collections.defaultdict()
        w1 = collections.defaultdict()
        for row in coll1.df.itertuples(index=False):
            if row[5] >= stat_cutoff:
                k = row[1]
                v = (row[2], row[5])
                w1[k] = v
                if k not in words:
                    words[k] = 0
        del coll1 
        w2 = collections.defaultdict()
        for row in coll2.df.itertuples(index=False):
            if row[5] >= stat_cutoff:
                k = row[1]
                v = (row[2], row[5])
                w2[k] = v
                if k not in words:
                    words[k] = 0
        del coll2
        # put all data together,
        # calculate percent difference,
        # and create the table
        s = []
        s.append('N\tWORD\tFREQ1\tFREQ2\tASSOCIATION1\tASSOCIATION2\tDIFFERENCE')
        i = 0
        total = len(words)
        for w in sorted(words):
            i += 1
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
            # calculate percent difference
            if w1_am <= w2_am:  # ensure n2 is larger
                n1 = w1_am 
                n2 = w2_am 
            else:
                n1 = w2_am 
                n2 = w1_am 
            pd = round(((n2 - n1) / float(n2)) * 100, 2)
            # add to table
            s.append('\t'.join([str(i), str(w), str(w1_f), str(w2_f), str(w1_am), str(w2_am), str(pd)]))
            if show_progress == True:
                self.__progress(i, total, '')
        comparison = kit_tools.ComparedCollocates()
        comparison.read_str('\n'.join(s))
        del s 
        comparison.df.sort_values('DIFFERENCE', ascending=True, inplace=True)
        comparison.df['N'] = [i + 1 for i in range(len(comparison.df))]
        comparison.df.reset_index(drop=True, inplace=True)
        # time end
        if show_progress == True:
            t1 = time.time()
            total_time = round(t1 - t0, 2)
            print('')
            print('Total time: %s seconds' % total_time)
        return comparison

    
    def collocations(self, kwic, **kwargs):
        """
        Extracts collocations from a KWIC (Key Word In Context) object.

        This method analyzes the KWIC data to identify collocates by examining the words 
        surrounding the target term. It computes frequency counts for words occurring in 
        specified left and right context spans, and calculates an association measure (either 
        t-score or mutual information) to evaluate the strength of each collocation. The result 
        is a table that provides detailed positional frequency information as well as a summary 
        of the association strength for each collocate.

        Keyword Arguments:
        lowercase (bool): If True (default), converts text to lowercase before processing.
        horizon (int): The number of words to consider from the left and right of the target 
                        word (range from 1 to 5, default is 5).
        measure (str): The statistical measure for association; either 'tscore' (default) or 
                        'mutual information'.
        show_progress (bool): If True, prints progress messages and execution time. Default is False.

        Returns:
        Collocations: An object containing a pandas DataFrame with the following columns:
            - 'N': Sequential index of the collocate entry.
            - 'WORD': The collocate word.
            - 'L5', 'L4', 'L3', 'L2', 'L1': Frequency counts for positions in the left context 
                (from farthest to nearest).
            - 'R1', 'R2', 'R3', 'R4', 'R5': Frequency counts for positions in the right context 
                (from nearest to farthest).
            - 'LEFT': Total frequency count in the left context.
            - 'RIGHT': Total frequency count in the right context.
            - 'TOTAL': Combined frequency count from both contexts.
            - 'ASSOCIATION': The computed association measure (rounded to two decimal places) 
                            indicating the strength of the collocation.
        """
        import re
        # kwargs
        lowercase = kwargs.get('lowercase', True)
        horizon = kwargs.get('horizon', 5)
        measure = kwargs.get('measure', 'tscore')
        show_progress = kwargs.get('show_progress', False)
        
        # time start
        if show_progress:
            print('Running...')
            t0 = time.time()
        
        # Determine statistical measure identifier
        if measure == 'tscore':
            stat = 1
        elif measure == 'mutual information':
            stat = 2
        
        # Compile pattern to avoid punctuation-only tokens
        ptn = re.compile("^\W+$")
        
        # Create a wordlist and frequency dictionary
        tpl = make_wordlist(self.workspace, self.corpus_name, self.language, lowercase)
        tokens = tpl[0]
        freqlist = collections.defaultdict()
        for row in tpl[4]:
            freqlist[row[1]] = row[2]
        
        # Initialize counters and dictionaries
        left_counter = collections.Counter()
        right_counter = collections.Counter()
        words = collections.defaultdict()
        node_freq = 0
        total = len(kwic.df)
        j = 0
        
        # Process each KWIC entry
        for row in kwic.df.itertuples(index=False):
            j += 1
            node_freq += 1
            # Determine left and right contexts based on the horizon
            if lowercase:
                left = list(reversed(row[1].lower().split(' ')[-horizon:]))
                right = row[1].lower().split(' ')[0:horizon]
            else:
                left = list(reversed(row[1].split(' ')[-horizon:]))
                right = row[1].split(' ')[0:horizon]
            # Count words in the left context
            i = 0
            for word in left:
                if re.search(ptn, word) is None:
                    i += 1
                    left_counter[(i, word)] += 1
                    if word not in words:
                        words[word] = freqlist[word]
            # Count words in the right context
            i = 0
            for word in right:
                if re.search(ptn, word) is None:
                    i += 1
                    right_counter[(i, word)] += 1
                    if word not in words:
                        words[word] = freqlist[word]
            if show_progress:
                self.__progress(j, total, '')
        
        # Cleanup temporary variables
        del kwic  
        del freqlist 
        
        # Build the data table as a string
        s = []
        s.append('\t'.join(['N', 'WORD', 'L5', 'L4', 'L3', 'L2', 'L1', 'R1', 'R2', 'R3', 'R4', 'R5', 'LEFT', 'RIGHT', 'TOTAL', 'ASSOCIATION']))
        i = 0
        for word in words:
            total_left = 0
            total_right = 0
            # Initialize left context frequency list with default zeros
            lv = ['0', '0', '0', '0', '0', '0']
            for hw, freq in left_counter.most_common():
                if hw[1] == word:
                    lv[hw[0]] = str(freq)
                    total_left += freq
            # Initialize right context frequency list with default zeros
            rv = ['0', '0', '0', '0', '0', '0']
            for hw, freq in right_counter.most_common():
                if hw[1] == word:
                    rv[hw[0]] = str(freq)
                    total_right += freq
            # Calculate total frequency and association measure
            total_count = total_left + total_right
            if stat == 1:
                m = kit_util.tscore(total_count, words[word], node_freq, tokens, 1)
            elif stat == 2:
                m = kit_util.mutual_information(total_count, words[word], node_freq, tokens, 1)
            i += 1
            s.append('\t'.join([
                str(i), word, lv[5], lv[4], lv[3], lv[2], lv[1],
                rv[1], rv[2], rv[3], rv[4], rv[5],
                str(total_left), str(total_right), str(total_count), str(m)
            ]))
        
        # Cleanup counters
        words = None
        left_counter = None
        right_counter = None
        
        # Create Collocations object from the data table
        collocations = kit_tools.Collocations()
        collocations.read_str('\n'.join(s))
        del s
        collocations.df.sort_values('ASSOCIATION', ascending=False, inplace=True)
        collocations.df['N'] = [i + 1 for i in range(len(collocations.df))]
        collocations.df.reset_index(drop=True, inplace=True)
        
        # time end and print progress if enabled
        if show_progress:
            t1 = time.time()
            total_time = round(t1 - t0, 2)
            print('')
            print('Total time: %s seconds' % total_time)
        
        return collocations

    
    def clusters(self, word, **kwargs):
        """
        Generates clusters of words based on a search term.

        This method searches the corpus for clusters centered on the specified search word.
        Clusters are extracted using a defined context window (size) and can be filtered by
        part-of-speech tags, case sensitivity, minimum frequency, and minimum range criteria.
        The resulting clusters include details on the cluster text, its overall frequency,
        the range of its occurrence across documents, and its relative frequency percentage.

        Parameters:
        word (str): The search word around which clusters will be generated.

        Keyword Arguments:
        pos (str or list, optional): Part-of-speech tag(s) to filter the search word. Default is None.
        size (int, optional): The number of words to include in each cluster (context window size). Default is 3.
        lowercase (bool, optional): If True (default), converts text to lowercase before processing.
        minfreq (int, optional): The minimum frequency a cluster must have to be included. Default is 1.
        minrange (int, optional): The minimum range (number of documents or distinct contexts) a cluster must cover. Default is 1.
        show_progress (bool, optional): If True, prints progress messages and the total execution time. Default is False.

        Returns:
        Clusters: An object containing a pandas DataFrame with the following columns:
            - 'N': Sequential index of the cluster entry.
            - 'CLUSTER': The text of the cluster.
            - 'FREQUENCY': The frequency count of the cluster in the corpus.
            - 'RANGE': The range frequency indicating the number of distinct contexts in which the cluster appears.
            - '%': The relative frequency percentage of the cluster, rounded to two decimal places.
        """
        # args
        word = word.strip()
        pos = kwargs.get('pos', None)
        size = kwargs.get('size', 3)
        lowercase = kwargs.get('lowercase', True)
        min_freq = kwargs.get('minfreq', 1)
        min_range = kwargs.get('minrange', 1)
        show_progress = kwargs.get('show_progress', False)
        
        # time start
        if show_progress == True:
            print('Running...')
            t0 = time.time()
        
        lst_clusters = make_clusters(self.workspace, self.corpus_name, word, pos, lowercase, size)
        clusters = kit_tools.Clusters()
        clusters.df = pd.DataFrame(lst_clusters, columns=['N', 'CLUSTER', 'FREQUENCY', 'RANGE', '%'])
        lst_clusters = None
        
        # sort clusters by frequency in descending order
        clusters.df.sort_values('FREQUENCY', ascending=False, inplace=True)
        
        # apply filtering based on minimum frequency and range
        clusters.df = clusters.df[(clusters.df.FREQUENCY >= min_freq)]
        clusters.df = clusters.df[(clusters.df.RANGE >= min_range)]
        
        # process DataFrame: round percentage, reassign sequential indexes, and reset index
        clusters.df['%'] = clusters.df['%'].apply(lambda x: round(x, 2))
        clusters.df['N'] = [i + 1 for i in range(len(clusters.df))]
        clusters.df.reset_index(drop=True, inplace=True)
        
        # time end and display total time if progress is enabled
        if show_progress == True:
            t1 = time.time()
            total_time = round(t1 - t0, 2)
            print('')
            print('Total time: %s seconds' % total_time)
        
        return clusters

    
    def ngrams(self, **kwargs):
        """
        Generates a list of n-grams extracted from the corpus.

        This method computes n-grams from the corpus data using the specified parameters.
        It allows for optional filtering by part-of-speech tags, setting the n-gram size (number of words),
        converting text to lowercase, and filtering by minimum frequency and range. The result is returned
        as an object containing a pandas DataFrame with detailed statistics for each n-gram.

        Keyword Arguments:
        - pos (str or list, optional): Part-of-speech tag(s) to filter the n-grams. Default is None.
        - size (int, optional): The size of the n-gram (number of words). Default is 3.
        - lowercase (bool, optional): If True (default), converts text to lowercase before processing.
        - minfreq (int, optional): Minimum frequency required for an n-gram to be included. Default is 1.
        - minrange (int, optional): Minimum range (e.g., number of distinct documents or contexts) for an n-gram. Default is 1.
        - show_progress (bool, optional): If True, prints progress messages and timing information. Default is False.

        Returns:
        Ngrams: An object containing a pandas DataFrame with the following columns:
            - 'N': Sequential index of the n-gram entry.
            - 'N-GRAM': The text of the n-gram.
            - 'FREQUENCY': The frequency count of the n-gram in the corpus.
            - 'RANGE': The number of distinct contexts in which the n-gram appears.
            - '%': The relative frequency percentage of the n-gram, rounded to two decimal places.
        """
        # args
        pos = kwargs.get('pos', None)
        size = kwargs.get('size', 3)
        lowercase = kwargs.get('lowercase', True)
        min_freq = kwargs.get('minfreq', 1)
        min_range = kwargs.get('minrange', 1)
        show_progress = kwargs.get('show_progress', False)
        
        # time start
        if show_progress:
            print('Running...')
            t0 = time.time()
        
        # generate n-grams
        lst_ng = make_ngrams(self.workspace, self.corpus_name, pos, size, lowercase)
        ng = kit_tools.Ngrams()
        ng.df = pd.DataFrame(lst_ng, columns=['N', 'N-GRAM', 'FREQUENCY', 'RANGE', '%'])
        lst_ng = None
        
        # sort by frequency in descending order
        ng.df.sort_values('FREQUENCY', ascending=False, inplace=True)
        
        # filter by minimum frequency and range
        ng.df = ng.df[(ng.df.FREQUENCY >= min_freq)]
        ng.df = ng.df[(ng.df.RANGE >= min_range)]
        
        # reset indexes and round percentage values
        ng.df['%'] = ng.df['%'].apply(lambda x: round(x, 2))
        ng.df['N'] = [i + 1 for i in range(len(ng.df))]
        ng.df.reset_index(drop=True, inplace=True)
        
        # time end and display progress if enabled
        if show_progress:
            t1 = time.time()
            total_time = round(t1 - t0, 2)
            print('')
            print('Total time: %s seconds' % total_time)
        
        return ng


    def dispersion(self, node, **kwargs):
        """
        Generates a dispersion plot data structure for a given search term or phrase.
        
        The method searches for occurrences of the specified term (or phrase up to 4 words) and 
        returns a Dispersion object containing data for plotting dispersion across files.
        
        Parameters:
          node (str): The search word or phrase.
        
        Keyword Arguments:
          pos (str or list, optional): Part-of-speech tag(s) for the search word. Default is None.
          case_sensitive (bool, optional): If True, the search is case-sensitive. Default is False.
          regexp (bool, optional): If True, the search term is treated as a regular expression. Default is False.
          limit (int, optional): Maximum number of concordance lines to consider. Default is None.
          show_progress (bool, optional): If True, displays progress messages and timing info. Default is False.
        
        Returns:
          Dispersion: An object with attributes:
              - df: A pandas DataFrame with columns ['N','FILENAME','TOTAL','HITS','S1','S2','S3','S4','S5'].
              - dpts: Dispersion points data.
              - total_s1, total_s2, total_s3, total_s4, total_s5: Totals for each section.
        """
        node = node.strip()
        pos = kwargs.get('pos', None)
        case_sensitive = kwargs.get('case_sensitive', False)
        regexp = kwargs.get('regexp', False)
        limit = kwargs.get('limit', None)
        show_progress = kwargs.get('show_progress', False)
        
        if show_progress:
            print('Running...')
            t0 = time.time()
        
        totals, dpts, lst_disp = make_dispersion(self.workspace, self.corpus_name, node, pos, case_sensitive, regexp)
        disp = kit_tools.Dispersion(output_path=self.output_path)
        disp.df = pd.DataFrame(lst_disp, columns=['N', 'FILENAME', 'TOTAL', 'HITS', 'S1', 'S2', 'S3', 'S4', 'S5'])
        disp.dpts = dpts
        disp.total_s1, disp.total_s2, disp.total_s3, disp.total_s4, disp.total_s5 = totals
        lst_disp = None
        
        disp.df.sort_values('HITS', ascending=False, inplace=True)
        if limit is not None:
            disp.df = disp.df.head(limit)
        disp.df['N'] = [i + 1 for i in range(len(disp.df))]
        disp.df.reset_index(drop=True, inplace=True)
        
        if show_progress:
            t1 = time.time()
            print('')
            print('Total time: %s seconds' % round(t1 - t0, 2))
        return disp

    def keywords_dispersion(self, keywords, **kwargs):
        """
        Generates a dispersion plot using keyword data.

        Keyword Arguments:
        limit (int, optional): Maximum number of keywords to use. Default is 25.
        lowercase (bool, optional): If True (default), converts text to lowercase before processing.
        show_progress (bool, optional): If True, displays progress messages and timing info. Default is False.

        Returns:
        KeywordsDispersion: An object containing:
            - df: A pandas DataFrame with columns ['N','WORD','KEYNESS','HITS','S1','S2','S3','S4','S5'].
            - dpts: Dispersion points data.
            - total_s1, total_s2, total_s3, total_s4, total_s5: Totals for each section.
        """
        lowercase = kwargs.get('lowercase', True)
        limit = kwargs.get('limit', 25)
        show_progress = kwargs.get('show_progress', False)

        if show_progress:
            print('Running...')
            t0 = time.time()

        # Build a dictionary of keywords with their keyness score (limit applied)
        dict_keywords = {}
        try:
            for i, row in enumerate(keywords.df.itertuples(index=False)):
                dict_keywords[row[1]] = row[3]
                if i + 1 >= limit:
                    break
        except Exception as e:
            print(f"Error processing keywords: {e}")

        totals, dpts, lst_disp = make_keywords_dispersion(self.workspace, self.corpus_name, dict_keywords, lowercase)

        disp = kit_tools.KeywordsDispersion(output_path=self.output_path)
        disp.df = pd.DataFrame(lst_disp, columns=['N', 'WORD', 'KEYNESS', 'HITS', 'S1', 'S2', 'S3', 'S4', 'S5'])
        disp.dpts = dpts

        # Handle unpacking safely
        if isinstance(totals, (tuple, list)) and len(totals) == 5:
            disp.total_s1, disp.total_s2, disp.total_s3, disp.total_s4, disp.total_s5 = totals
        else:
            raise ValueError(f"Unexpected totals format: {totals}. Expected an iterable with 5 elements.")

        disp.df.sort_values('KEYNESS', ascending=False, inplace=True)
        if limit is not None:
            disp.df = disp.df.head(limit)

        disp.df['N'] = [i + 1 for i in range(len(disp.df))]
        disp.df.reset_index(drop=True, inplace=True)

        if show_progress:
            t1 = time.time()
            print('')
            print(f'Total time: {round(t1 - t0, 2)} seconds')

        return disp


    def combolist(self, **kwargs):
        """
        Creates an extended wordlist with additional information.
        
        This method merges data from several sources (wordlist, keywords, file frequency, and tagging)
        to build a comprehensive wordlist containing frequency, keyness, range, part-of-speech (POS), stopword 
        status, and lemma information. An optional custom function can be applied to generate extra category data.
        
        Keyword Arguments:
          max_pos (int, optional): Maximum number of POS tags to include. Default is 1.
          min_freq (int, optional): Minimum frequency threshold for words. Default is 1.
          min_range (int, optional): Minimum range percentage threshold for words. Default is 0.
          negative_keyness (bool, optional): If False, excludes words with negative keyness. Default is True.
          limit (int, optional): Maximum number of words in the final list. Default is None.
          cat (function, optional): A custom function applied to each row to generate additional data for the CAT column.
          show_progress (bool, optional): If True, displays progress messages. Default is False.
        
        Returns:
          Combolist: An object containing a pandas DataFrame with columns:
                     ['N', 'WORD', 'POS', 'FREQUENCY', 'F%', 'KEYNESS', 'RANGE', 'R%', 'STOPWORD', 'LEMMA', 'CAT'].
        """
        min_freq = kwargs.get('min_freq', 1)
        min_range = kwargs.get('min_range', 0)
        negative_keyness = kwargs.get('negative_keyness', True)
        cat = kwargs.get('cat', None)
        limit = kwargs.get('limit', None)
        show_progress = kwargs.get('show_progress', False)
        max_pos = kwargs.get('max_pos', 1)
        
        if show_progress:
            print('Running...')
            t0 = time.time()
        
        # Retrieve and filter the wordlist
        if show_progress:
            print('Wordlist...')
        df = self.wordlist().df.filter(['WORD', 'FREQUENCY', '%'])
        df.columns = ['WORD', 'FREQUENCY', 'F%']
        df = df[df.FREQUENCY >= min_freq]
        
        # Merge with keywords data
        if show_progress:
            print('Keywords...')
        keywords_df = self.keywords().df.filter(['WORD', 'KEYNESS'])
        df = pd.merge(df, keywords_df, on='WORD')
        if not negative_keyness:
            df = df[df.KEYNESS >= 0]
        
        # Merge with file frequency data (wfreqinfiles)
        if show_progress:
            print('Freqinfiles...')
        wfreqinfiles = self.wfreqinfiles().df.filter(['WORD', 'RANGE', '%'])
        wfreqinfiles.columns = ['WORD', 'RANGE', 'R%']
        df = pd.merge(df, wfreqinfiles, on='WORD')
        df = df[df['R%'] >= min_range]
        
        # Merge with word-tag frequency data (wtfreq) to get POS information
        if show_progress:
            print('Wtfreq...')
        wtfreq_obj = self.wtfreq()
        d = {}
        if max_pos == 1:
            for row in wtfreq_obj.df.itertuples(index=False):
                if row[1] not in d:
                    d[row[1]] = row[2]
        else:
            for row in wtfreq_obj.df.itertuples(index=False):
                if row[1] not in d:
                    d[row[1]] = row[2]
                else:
                    if len(d[row[1]].split(' ')) < max_pos:
                        d[row[1]] += ' ' + row[2]
        wt = pd.DataFrame(list(d.items()), columns=['WORD', 'POS'])
        df = pd.merge(df, wt, on='WORD')
        
        # Process stoplist data
        if show_progress:
            print('Stoplist...')
        stoplist = {}
        stoplist_path = self.resource_data_path + 'stoplist_' + self.language + '.tab'
        with open(stoplist_path, 'r', encoding='utf-8') as fh:
            for line in fh:
                if line.strip():
                    stoplist[line.strip()] = 1
        for row in df.itertuples(index=False):
            if row[0] not in stoplist:
                stoplist[row[0]] = 0
        stop = pd.DataFrame(list(stoplist.items()), columns=['WORD', 'STOPWORD'])
        df = pd.merge(df, stop, on='WORD')
        
        # Process lemmas
        if show_progress:
            print('Lemmas...')
        lemmas_path = self.resource_data_path + '/lemmas_' + self.language + '.tab'
        lemma_data = []
        if os.path.exists(lemmas_path):
            lemmas = {}
            with open(lemmas_path, 'r', encoding='utf-8') as fh:
                for line in fh:
                    if line.strip():
                        f = line.strip().split('\t')
                        if len(f) >= 2:
                            lemmas[f[0].strip()] = f[1].strip()
            for row in df.itertuples(index=False):
                lemma_data.append(lemmas.get(row[0], '-'))
        else:
            lemma_data = ['-'] * len(df)
        df['LEMMA'] = lemma_data
        
        # Initialize CAT column (can be later processed by a custom function)
        df['CAT'] = ['-'] * len(df)
        
        # Organize and filter final DataFrame
        df['N'] = [i + 1 for i in range(len(df))]
        df = df[['N', 'WORD', 'POS', 'FREQUENCY', 'F%', 'KEYNESS', 'RANGE', 'R%', 'STOPWORD', 'LEMMA', 'CAT']]
        if limit is not None:
            df = df.head(limit)
        
        cmblist = kit_tools.Combolist()
        cmblist.df = df
        
        if cat is not None:
            try:
                cmblist.cat(cat)
            except Exception as e:
                print(e)
        
        if show_progress:
            t1 = time.time()
            print('')
            print('Total time: %s seconds' % round(t1 - t0, 2))
        return cmblist

    def export(self, target_folder, **kwargs):
        """
        Exports the current corpus to a specified destination folder.
        
        Parameters:
          target_folder (str): The destination folder where the corpus will be saved.
        
        Keyword Arguments:
          show_progress (bool, optional): If True, displays progress messages and timing info. Default is True.
        """
        show_progress = kwargs.get('show_progress', True)
        if show_progress:
            print('Running...')
            t0 = time.time()
        if os.path.exists(target_folder) and os.path.isdir(target_folder):
            try:
                subprocess.call(['python', self.__path + '/export_corpus.py', self.workspace, self.corpus_name, target_folder])
            except Exception as e:
                if show_progress:
                    print("Kitconc cannot export the corpus.\n")
                    print(e)
            finally:
                if show_progress:
                    t1 = time.time()
                    print('')
                    print('Total time: %s seconds' % round(t1 - t0, 2))
        else:
            if show_progress:
                print('The folder path is not valid.')

    def add_from_export(self, filename, **kwargs):
        """
        Imports a corpus from an exported file (ZIP format) into the current workspace.
        
        Parameters:
          filename (str): The path to the corpus ZIP file.
        
        Keyword Arguments:
          show_progress (bool, optional): If True, displays progress messages and timing info. Default is False.
        """
        show_progress = kwargs.get('show_progress', False)
        if show_progress:
            print('Running...')
            t0 = time.time()
        if os.path.exists(filename) and os.path.isfile(filename):
            try:
                import zipfile
                with zipfile.ZipFile(filename, 'r') as zip_ref:
                    zip_ref.extractall(self.workspace)
            except Exception as e:
                if show_progress:
                    print('Kitconc cannot import the corpus.\n')
                    print(e)
            finally:
                if show_progress:
                    t1 = time.time()
                    print('')
                    print('Total time: %s seconds' % round(t1 - t0, 2))
        else:
            if show_progress:
                print('The file path is not valid.')

    # GENERAL FUNCTIONS FOR CORPUS STATISTICS

    def info(self):
        """
        Returns basic statistical information about the corpus (tokens, types, TTR, hapax legomena).
        
        Returns:
          tuple: A tuple containing corpus statistics.
        """
        self.wordlist()
        kd = kit_data.KitData(self.workspace, self.corpus_name, self.language)
        return kd.info_get()

    def tokens(self):
        """
        Returns the total number of tokens in the corpus.
        
        Returns:
          int: The token count.
        """
        kd = kit_data.KitData(self.workspace, self.corpus_name, self.language)
        return kd.tokens_get()

    def types(self):
        """
        Returns the total number of unique words (types) in the corpus.
        
        Returns:
          int: The number of types.
        """
        kd = kit_data.KitData(self.workspace, self.corpus_name, self.language)
        return kd.types_get()

    def ttr(self):
        """
        Returns the type/token ratio (TTR) of the corpus.
        
        Returns:
          float: The TTR value.
        """
        kd = kit_data.KitData(self.workspace, self.corpus_name, self.language)
        return kd.ttr_get()

    def hapax(self):
        """
        Returns the number of hapax legomena (words that occur only once) in the corpus.
        
        Returns:
          int: The hapax count.
        """
        kd = kit_data.KitData(self.workspace, self.corpus_name, self.language)
        return kd.hapax_get()

    def textfiles(self):
        """
        Returns the names of all text files in the corpus.
        
        Returns:
          generator: A generator yielding text file names.
        """
        kd = kit_data.KitData(self.workspace, self.corpus_name, self.language)
        return kd.textfiles_get_names()

    def fileids(self):
        """
        Returns the identifiers of files in the corpus.
        
        Returns:
          generator: A generator yielding file IDs.
        """
        kd = kit_data.KitData(self.workspace, self.corpus_name, self.language)
        return kd.fileids_get()

    def words(self, fileids=None):
        """
        Returns the words from the corpus. Optionally, a subset of file IDs can be specified.
        
        Parameters:
          fileids (list, optional): A list of file IDs to retrieve words from. Default is None (all files).
        
        Returns:
          generator: A generator yielding words.
        """
        kd = kit_data.KitData(self.workspace, self.corpus_name, self.language)
        return kd.words_get(fileids)

    def tagged_words(self, fileids=None):
        """
        Returns the tagged words from the corpus. Optionally, a subset of file IDs can be specified.
        
        Parameters:
          fileids (list, optional): A list of file IDs to retrieve tagged words from. Default is None.
        
        Returns:
          generator: A generator yielding tagged words.
        """
        kd = kit_data.KitData(self.workspace, self.corpus_name, self.language)
        return kd.tagged_words_get(fileids)

    def sents(self, fileids=None):
        """
        Returns sentences from the corpus. Optionally, a subset of file IDs can be specified.
        
        Parameters:
          fileids (list, optional): A list of file IDs to retrieve sentences from. Default is None.
        
        Returns:
          generator: A generator yielding sentences.
        """
        kd = kit_data.KitData(self.workspace, self.corpus_name, self.language)
        return kd.sents_get(fileids)

    def tagged_sents(self, fileids=None):
        """
        Returns tagged sentences from the corpus. Optionally, a subset of file IDs can be specified.
        
        Parameters:
          fileids (list, optional): A list of file IDs to retrieve tagged sentences from. Default is None.
        
        Returns:
          generator: A generator yielding tagged sentences.
        """
        kd = kit_data.KitData(self.workspace, self.corpus_name, self.language)
        return kd.tagged_sents_get(fileids)

    def ndarrays(self, fileids=None):
        """
        Returns numpy arrays from the corpus. These arrays typically represent token, tag, sentence, and file IDs.
        
        Parameters:
          fileids (list, optional): A list of file IDs to retrieve arrays from. Default is None.
        
        Returns:
          generator: A generator yielding numpy arrays.
        """
        kd = kit_data.KitData(self.workspace, self.corpus_name, self.language)
        return kd.ndarrays_get(fileids)

    def ndarrays_filenames(self, fileids=None):
        """
        Returns filenames associated with the numpy arrays from the corpus.
        
        Parameters:
          fileids (list, optional): A list of file IDs to retrieve filenames from. Default is None.
        
        Returns:
          generator: A generator yielding filenames.
        """
        kd = kit_data.KitData(self.workspace, self.corpus_name, self.language)
        return kd.ndarrays_filenames_get(fileids)

    def dict_words(self):
        """
        Returns a dictionary mapping word IDs to words.
        
        Returns:
          dict: A dictionary where keys are IDs and values are words.
        """
        kd = kit_data.KitData(self.workspace, self.corpus_name, self.language)
        return kd.dict_words_get()

    def dict_tags(self):
        """
        Returns a dictionary mapping tag IDs to tags.
        
        Returns:
          dict: A dictionary where keys are IDs and values are tags.
        """
        kd = kit_data.KitData(self.workspace, self.corpus_name, self.language)
        return kd.dict_tags_get()

    def delete(self, corpus_name):
        """
        Deletes the specified corpus from the workspace.
        
        Parameters:
          corpus_name (str): The name of the corpus to delete.
        """
        if os.path.exists(self.workspace + corpus_name):
            shutil.rmtree(self.workspace + corpus_name)


class Corpora(object):
    """
    Manager class for handling multiple corpora within a workspace.
    
    Provides methods for listing, checking existence, creating, importing, and exporting corpora.
    """

    def __init__(self, workspace, **kwargs):
        """
        Initializes the Corpora manager with a specified workspace.
        
        Parameters:
          workspace (str): The directory path where corpora are stored.
        """
        self.__path = os.path.dirname(os.path.abspath(__file__))
        # Normalize workspace path to ensure it ends with a '/'
        if str(workspace).endswith('/'):
            self.workspace = workspace
        else:
            self.workspace = workspace + '/'
        # Create the workspace directory if it does not exist
        if not os.path.exists(self.workspace):
            os.mkdir(self.workspace)

    def list_all(self):
        """
        Lists all corpora in the workspace.
        
        Returns:
          list: A list of corpus names (subdirectory names).
        """
        c = []
        for item in os.listdir(self.workspace):
            if os.path.isdir(self.workspace + item):
                c.append(item)
        return c

    def exists(self, corpus_name):
        """
        Checks if a corpus exists in the workspace.
        
        Parameters:
          corpus_name (str): The name of the corpus to check.
        
        Returns:
          bool: True if the corpus exists, False otherwise.
        """
        return corpus_name in self.list_all()

    def delete(self, corpus_name):
        """
        Deletes a corpus from the workspace.
        
        Parameters:
          corpus_name (str): The name of the corpus to delete.
        """
        if os.path.exists(self.workspace + corpus_name):
            shutil.rmtree(self.workspace + corpus_name)

    def get_corpus(self, corpus_name):
        """
        Retrieves a Corpus object for the specified corpus.
        
        Parameters:
          corpus_name (str): The name of the corpus.
        
        Returns:
          Corpus: An instance of the Corpus class.
        """
        return Corpus(self.workspace, corpus_name)

    def open(self, corpus_name):
        """
        Opens an existing corpus and returns a Corpus object.
        
        Parameters:
          corpus_name (str): The name of the corpus.
        
        Returns:
          Corpus: An instance of the Corpus class.
        """
        return Corpus(self.workspace, corpus_name)

    def create(self, corpus_name, language, source_texts):
        """
        Creates a new corpus from source texts.
        
        Parameters:
          corpus_name (str): The name for the new corpus.
          language (str): The language of the corpus.
          source_texts (str): The folder path containing the source texts.
        
        Returns:
          Corpus: A new Corpus object.
        """
        corpus = Corpus(self.workspace, corpus_name, language)
        corpus.add_texts(source_texts)
        return corpus

    def import_corpus(self, filename):
        """
        Imports a corpus from a ZIP file into the workspace.
        
        Parameters:
          filename (str): The path to the corpus ZIP file.
        """
        if os.path.exists(filename) and os.path.isfile(filename):
            try:
                import zipfile
                with zipfile.ZipFile(filename, 'r') as zip_ref:
                    zip_ref.extractall(self.workspace)
            except Exception as e:
                print('Kitconc cannot import the corpus.\n')
                print(e)
        else:
            print('The file path is not valid.')

    def import_corpus_from_url(self, url):
        """
        Downloads and imports a corpus from a given URL (ZIP file).
        
        Parameters:
          url (str): The URL of the corpus ZIP file.
        """
        import requests, zipfile, io
        try:
            r = requests.get(url)
            z = zipfile.ZipFile(io.BytesIO(r.content))
            z.extractall(self.workspace)
        except Exception as e:
            print('Download was not possible.')
            print(e)

    def download_raw_texts(self, url, dest=None):
        """
        Downloads raw texts (ZIP file) from a given URL and extracts them.
        
        Parameters:
          url (str): The URL to download the raw texts from.
          dest (str, optional): The destination folder for extraction. If None, extracts to the current directory.
        """
        import requests, zipfile, io
        try:
            r = requests.get(url)
            z = zipfile.ZipFile(io.BytesIO(r.content))
            if dest is None:
                z.extractall()
            else:
                if os.path.exists(dest):
                    z.extractall(dest)
        except Exception as e:
            print('Download was not possible.')
            print(e)
