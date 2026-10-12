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
import numpy as np
import collections
import platform
import shutil
import pickle
import tempfile
import re
from pathlib import Path
from kitconc.archive import download_and_import_corpus, import_corpus_zip
from kitconc import kit_tools
from kitconc import kit_util
from kitconc import kit_data
from kitconc import kit_models
from kitconc.py_wordlist import make_wordlist
from kitconc.py_keywords import make_keywords, make_keywords_tfidf, available_ref_languages
from kitconc.py_wtfreq import make_wtfreq
from kitconc.py_wfreqinfiles import make_wfreqinfiles
from kitconc.py_kwic import make_kwic 
from kitconc.py_concordance import make_concordance
from kitconc.py_collocates import make_collocates
from kitconc.py_clusters import make_clusters     
from kitconc.py_ngrams import make_ngrams
from kitconc.py_dispersion import make_dispersion
from kitconc.py_keywords_dispersion import make_keywords_dispersion
from kitconc.py_keywords import load_reference, _re_number, _re_strange
from kitconc import py_measures
from kitconc import py_extras


def _run_pipeline(command, stage):
    """Run one indexing stage and surface failures with the stage name."""
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or '').strip()
        raise RuntimeError(
            f"Corpus {stage} failed with exit code {result.returncode}"
            + (f": {detail[-4000:]}" if detail else ".")
        )
    return result
    

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
        except (ImportError, AttributeError):
            pass
        # constants
        self.MEASURE_MUTUAL_INFORMATION = 'mutual information'
        self.MEASURE_CHI_SQUARE = 'chi-square'
        self.MEASURE_LOGLIKELIHOOD = 'log-likelihood'
        self.MEASURE_TSCORE = 't-score'
        # normalize workspace path 
        workspace = str(workspace)
        if workspace.endswith('/'):
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
            if corpus_name in {'.', '..'} or not re.fullmatch(r'[A-Za-z0-9_.-]+', str(corpus_name)):
                raise ValueError('Corpus name may contain only letters, numbers, _, ., and -; it cannot be . or ..')
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
            except OSError:
                pass


    # helpers for optional (AntConc-like) features

    @staticmethod
    def _prepare_query(node, regexp=False, wildcards=False):
        """Converts wildcard queries (teach*, *ing, a|b, [a,b]) to kitconc's token regex syntax."""
        if wildcards and not regexp:
            return py_extras.wildcard_to_regex(node), True
        return node, regexp

    @staticmethod
    def _renumber(df):
        df = df.copy()
        df['N'] = [i + 1 for i in range(len(df))]
        df.reset_index(drop=True, inplace=True)
        return df

    @staticmethod
    def _filter_items(df, column, search, regexp=False, lowercase=True):
        """Keeps rows whose item (or any of its words) matches the search query."""
        query = search if regexp else py_extras.wildcard_to_regex(search)
        flags = re.IGNORECASE if lowercase else 0
        patterns = [re.compile(p, flags) for p in query.split(' ') if p]

        def keep(item):
            words = str(item).split(' ')
            return any(p.match(w) for p in patterns for w in words)

        return df[df[column].map(keep).astype(bool)]

    def _add_dispersion_columns(self, df, column, lowercase=True, keep_columns=True):
        """Adds RANGE, JUILLAND_D and DP columns (or a temporary _RANGE column)."""
        table = py_extras.dispersion_table(self.workspace, self.corpus_name, lowercase,
                                           words=list(df[column]))
        df = df.copy()
        empty = {'range': 0, 'juilland-d': 0.0, 'dp': 0.0}
        key = (lambda w: str(w).lower()) if lowercase else (lambda w: str(w))
        ranges = [int(table.get(key(w), empty)['range']) for w in df[column]]
        if keep_columns:
            df['RANGE'] = ranges
            df['JUILLAND_D'] = [round(table.get(key(w), empty)['juilland-d'], 4) for w in df[column]]
            df['DP'] = [round(table.get(key(w), empty)['dp'], 4) for w in df[column]]
        else:
            df['_RANGE'] = ranges
        return df

    def _reference_data(self, ref_corpus=None, ref_language=None, lowercase=True):
        """Returns (tokens, {word: freq}, {word: range} or None, files or None) for keyness."""
        if ref_corpus is not None:
            if isinstance(ref_corpus, Corpus):
                workspace, name = ref_corpus.workspace, ref_corpus.corpus_name
            else:
                workspace, name = self.workspace, str(ref_corpus)
            if not os.path.exists(workspace + name + '/data/npy'):
                raise ValueError(f'Reference corpus not found: {name}')
            tokens, freq, rng, files = py_extras.corpus_frequency_list(workspace, name, lowercase)
            return tokens, freq, rng, files
        tokens, freq = load_reference(ref_language or self.language)
        return tokens, freq, None, None

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
        """Add texts without leaving a partially updated corpus after failure."""
        source_path = Path(source_folder).expanduser().resolve()
        if not source_path.is_dir():
            raise ValueError(f"Source folder does not exist: {source_path}")
        skipped_names = {'.DS_Store', 'desktop.ini', 'Thumbs.db'}
        source_files = [path for path in source_path.iterdir() if path.is_file() and path.name not in skipped_names]
        if not source_files:
            raise ValueError(f"Source folder contains no files: {source_path}")
        if any(path.stat().st_size == 0 for path in source_files):
            raise ValueError(f"Empty file found in {source_path}; remove it before proceeding.")

        prepared_source, pdf_tmp = kit_util.prepare_source_folder(str(source_path))
        corpus_dir = Path(self.workspace) / self.corpus_name
        data_dir = corpus_dir / "data"
        info_path = corpus_dir / "info.tab"
        had_data = data_dir.is_dir()
        backup_complete = False
        backup_root = None
        info_backup = None
        try:
            backup_root = Path(tempfile.mkdtemp(prefix=".kitconc-data-backup-", dir=corpus_dir.parent))
            backup_data = backup_root / "data"
            info_backup = info_path.read_bytes() if info_path.is_file() else None
            if had_data:
                shutil.copytree(data_dir, backup_data)
                backup_complete = True
            return self._add_texts_prepared(
                prepared_source,
                _source_path=str(source_path),
                _processed_file_count=sum(
                    1 for path in Path(prepared_source).iterdir()
                    if path.is_file() and path.name not in skipped_names
                ),
                **kwargs,
            )
        except Exception:
            if had_data and backup_complete:
                shutil.rmtree(data_dir, ignore_errors=True)
                shutil.copytree(backup_data, data_dir)
            if info_backup is not None:
                info_path.write_bytes(info_backup)
            raise
        finally:
            for name in ("tmp0", "tmp1", "tmp2", "tmp3"):
                shutil.rmtree(data_dir / name, ignore_errors=True)
            if pdf_tmp is not None:
                shutil.rmtree(pdf_tmp, ignore_errors=True)
            if backup_root is not None:
                shutil.rmtree(backup_root, ignore_errors=True)

    def _add_texts_prepared(self, source_folder, **kwargs):
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
            - verbose (bool): If True, prints progress messages and timing information (default is False).
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
        verbose (bool, optional): If True, prints progress messages and timing information. Defaults to False.

        Raises:
        ValueError: If an empty file is found in the source folder.
        """
        # args
        tagged = kwargs.get('tagged', False)
        language_model = kwargs.get('language_model', None)
        verbose = kwargs.get('verbose', False)
        if not source_folder.endswith('/'):
            source_folder = source_folder + '/'
        
        # time start
        if verbose:
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
                    if verbose:
                        print('Tagging...')
                    resources_path = self.__path + '/data/'
                    _run_pipeline([sys.executable, self.__path + '/tagging.py', resources_path, self.workspace, self.corpus_name, self.language, source_folder], 'tagging')
                    if verbose:
                        print('Making indexes...')
                    _run_pipeline([sys.executable, self.__path + '/indexing.py', self.workspace, self.corpus_name, self.language], 'indexing')
                else:
                    if verbose:
                        print('Tagging...')
                    # Create temp folder
                    if os.path.exists(self.workspace + self.corpus_name + '/data/tmp0'):
                        shutil.rmtree(self.workspace + self.corpus_name + '/data/tmp0/')
                    os.mkdir(self.workspace + self.corpus_name + '/data/tmp0/')
                    # Load model 
                    with open(self.__path + '/data/' + self.language + '_model.pickle', 'rb') as fh:
                        language_model = pickle.load(fh)
                    # Tag texts manually
                    files = [name for name in os.listdir(source_folder) if os.path.isfile(os.path.join(source_folder, name))]
                    for filename in files:
                        text = kit_util.read_text_detected(source_folder + filename)
                        doc = language_model(text)
                        tagged_sents = []
                        for sent in doc.sents:
                            tagged_sents.append(' '.join([(token.text + '/' + token.pos_) for token in sent if len(token.text.strip()) != 0]))
                        with open(self.workspace + self.corpus_name + '/data/tmp0/' + filename, 'w', encoding='utf-8') as fh:
                            fh.write('\n'.join(tagged_sents))
                    if verbose:
                        print('Loading tagged corpus...')
                    resources_path = self.__path + '/data/'
                    _run_pipeline([sys.executable, self.__path + '/tagged.py', resources_path, self.workspace, self.corpus_name, self.language, self.workspace + self.corpus_name + '/data/tmp0/'], 'tagged-text import')
                    if verbose:
                        print('Making indexes...')
                    _run_pipeline([sys.executable, self.__path + '/indexing.py', self.workspace, self.corpus_name, self.language], 'indexing')
                    # Remove temporary folder
                    shutil.rmtree(self.workspace + self.corpus_name + '/data/tmp0/')
            else:
                if verbose:
                    print('Loading tagged corpus...')
                resources_path = self.__path + '/data/'
                _run_pipeline([sys.executable, self.__path + '/tagged.py', resources_path, self.workspace, self.corpus_name, self.language, source_folder], 'tagged-text import')
                if verbose:
                    print('Making indexes...')
                _run_pipeline([sys.executable, self.__path + '/indexing.py', self.workspace, self.corpus_name, self.language], 'indexing')
        else:
            # Use language model on the fly to tag texts (e.g., using spaCy)
            if verbose:
                print('Tagging...')
            # Create temporary folder
            if os.path.exists(self.workspace + self.corpus_name + '/data/tmp0'):
                shutil.rmtree(self.workspace + self.corpus_name + '/data/tmp0/')
            os.mkdir(self.workspace + self.corpus_name + '/data/tmp0/')
            # Tag texts
            files = [file for file in os.listdir(source_folder) if os.path.isfile(os.path.join(source_folder, file)) and file not in ['.DS_Store', 'desktop.ini', 'Thumbs.db']]
            for filename in files:
                print(filename)
                text = kit_util.read_text_detected(source_folder + filename)
                doc = language_model(text)
                tagged_sents = []
                for sent in doc.sents:
                    tagged_sents.append(' '.join([(token.text + '/' + token.pos_) for token in sent if len(token.text.strip()) != 0]))
                with open(self.workspace + self.corpus_name + '/data/tmp0/' + filename, 'w', encoding='utf-8') as fh:
                    fh.write('\n'.join(tagged_sents))
            # Load tagged texts    
            if verbose:
                print('Loading tagged corpus...')
            resources_path = self.__path + '/data/'
            _run_pipeline([sys.executable, self.__path + '/tagged.py', resources_path, self.workspace, self.corpus_name, self.language, self.workspace + self.corpus_name + '/data/tmp0/'], 'tagged-text import')
            if verbose:
                print('Making indexes...')
            _run_pipeline([sys.executable, self.__path + '/indexing.py', self.workspace, self.corpus_name, self.language], 'indexing')
            # Remove temporary folder
            shutil.rmtree(self.workspace + self.corpus_name + '/data/tmp0/')
        
        # Append source information to corpus info file
        ntexts = int(kwargs.get('_processed_file_count', 0))
        original_source = kwargs.get('_source_path', source_folder)
        info_path = Path(self.workspace) / self.corpus_name / 'info.tab'
        existing_info = {}
        if info_path.is_file():
            with info_path.open('r', encoding='utf-8') as fh:
                for line in fh:
                    if '\t' in line:
                        key, value = line.rstrip('\r\n').split('\t', 1)
                        existing_info[key.rstrip(':').strip().lower()] = value.strip()
        try:
            total_texts = int(existing_info.get('textfiles', '0')) + ntexts
        except ValueError:
            total_texts = ntexts
        lines = []
        wrote_texts = wrote_source = False
        with info_path.open('r', encoding='utf-8') as fh:
            for line in fh:
                key = line.split('\t', 1)[0].rstrip(':').strip().lower()
                if key == 'textfiles':
                    if not wrote_texts:
                        lines.append(f'Textfiles:\t{total_texts}\n')
                        wrote_texts = True
                elif key == 'source':
                    if not wrote_source:
                        lines.append(f'Source:\t{original_source}\n')
                        wrote_source = True
                else:
                    lines.append(line)
        if not wrote_texts:
            lines.append(f'Textfiles:\t{total_texts}\n')
        if not wrote_source:
            lines.append(f'Source:\t{original_source}\n')
        info_path.write_text(''.join(lines).rstrip('\n') + '\n', encoding='utf-8')
        
        # Time end and print total time if progress display is enabled
        if verbose:
            t1 = time.time()
            total_time = round(t1 - t0, 2)
            print('Total time: %s seconds' % total_time)
        
        # Temporary folders and PDF conversion output are cleaned by add_texts().

    

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
        - min_range (int): Minimum number of text files in which the word occurs (default is 1).
        - search (str): Keeps only words matching this query (wildcards such as ``teach*``,
                        ``*ing`` or ``colour|color``; a regular expression when ``regexp`` is True).
        - regexp (bool): Interprets ``search`` as a regular expression (default is False).
        - stoplist / allowlist: Words to exclude / to keep. A list, a file path (one word per line)
                        or 'default' for the bundled stoplist of the corpus language.
        - dispersion (bool): Adds the columns RANGE, JUILLAND_D and DP (Gries' deviation of
                        proportions) computed over the text files (default is False).
        - verbose (bool): If True, prints progress messages and the total execution time (default is False).

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
        verbose = kwargs.get('verbose', False)
        min_freq = kwargs.get('min_freq', 1)
        lowercase = kwargs.get('lowercase', True)
        
        # time start
        if verbose:
            print('Running...')
            t0 = time.time()
        
        # make
        tokens, types, type_token, hapax, xwordlist = make_wordlist(self.workspace, self.corpus_name, self.language, lowercase)
        wlst = kit_tools.Wordlist(tokens=tokens, types=types, typetoken=round(type_token, 2), hapax=hapax)
        wlst.df = pd.DataFrame(xwordlist, columns=['N', 'WORD', 'FREQUENCY', '%'])
        wlst.df = wlst.df[wlst.df.FREQUENCY >= min_freq]
        wlst.df['%'] = wlst.df['%'].apply(lambda x: round(x, 2))

        # optional filters and dispersion columns
        search = kwargs.get('search', None)
        if search:
            wlst.df = self._filter_items(wlst.df, 'WORD', search, kwargs.get('regexp', False), lowercase)
        wlst.df = py_extras.filter_by_words(wlst.df, 'WORD', kwargs.get('stoplist', None),
                                            kwargs.get('allowlist', None), self.language)
        min_range = kwargs.get('min_range', 1)
        if kwargs.get('dispersion', False) or min_range > 1:
            wlst.df = self._add_dispersion_columns(wlst.df, 'WORD', lowercase,
                                                   keep_columns=kwargs.get('dispersion', False))
            if min_range > 1:
                wlst.df = wlst.df[wlst.df['RANGE' if 'RANGE' in wlst.df else '_RANGE'] >= min_range]
                if '_RANGE' in wlst.df:
                    wlst.df = wlst.df.drop(columns=['_RANGE'])
        if search or kwargs.get('stoplist') or kwargs.get('allowlist') or min_range > 1:
            wlst.df.reset_index(drop=True, inplace=True)

        # time end
        if verbose:
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
                        Also accepted: 'tf-idf', 'log-likelihood-2' (two-term LL), 'chi-square-yates' and
                        'text-dispersion' (keyness of text ranges; requires ``ref_corpus``).
        - stoplist (list): A list of words to exclude from the keyword extraction process
                        (a file path or 'default' are also accepted).
        - allowlist (list): Only these words are kept (list, file path or 'default').
        - ref_language (str): Language of the bundled reference word list (default: corpus language).
        - ref_corpus (str or Corpus): A corpus of the workspace used as reference corpus instead of the
                        bundled word list. Adds the columns REF_FREQUENCY, RANGE and REF_RANGE.
        - effect (str or list): Effect-size measure(s) added as extra columns, e.g. 'log-ratio', 'dice',
                        'log-dice', 'mi', 'mi3', 'rrf', 'drf', 'z-score', 't-score', '%diff', 'odds-ratio'.
        - polarity (str): 'all' (default), 'positive' or 'negative' (negative keywords: words
                        unusually infrequent in the corpus; they are sorted from the most negative).
        - p_value (str or float): Keeps only keywords whose keyness reaches the critical value,
                        e.g. 'p<0.05', 'p<0.01', 0.001.
        - bonferroni (bool): Applies the Bonferroni correction to ``p_value`` (default is False).
        - min_freq / min_range (int): Minimum frequency / number of text files in the corpus.
        - sort_by (str): 'keyness' (default) or 'effect' (the first effect measure).
        - verbose (bool): If True, prints progress messages and timing information during processing.

        Returns:
        Keywords: An object containing a pandas DataFrame with the following columns:
            - 'N': Ranking index of the keyword.
            - 'WORD': The keyword.
            - 'FREQUENCY': The number of occurrences of the keyword in the corpus.
            - 'KEYNESS': The computed keyness score for the keyword, rounded to two decimal places.
            Optional columns are appended after these four.
        """
        # args
        measure = kwargs.get('measure', 'log-likelihood')
        stoplist = kwargs.get('stoplist', [])
        verbose = kwargs.get('verbose', False)
        ref_language = kwargs.get('ref_language', None)
        ignore_numbers = kwargs.get('ignore_numbers', True)
        ignore_strange = kwargs.get('ignore_strange', True)
        min_chars = kwargs.get('min_chars', 2)

        extended = any(kwargs.get(k) not in (None, False, [], 'all', 1, 'keyness') for k in
                       ('ref_corpus', 'effect', 'polarity', 'p_value', 'allowlist', 'min_freq',
                        'min_range', 'sort_by')) \
            or measure in ('log-likelihood-2', 'chi-square-yates', 'text-dispersion') \
            or (stoplist and not isinstance(stoplist, (list, tuple, set)))
        if extended and measure != 'tf-idf':
            return self._keywords_extended(**kwargs)

        # get statistical measure identifier
        use_tfidf = (measure == 'tf-idf')
        if measure == 'log-likelihood':
            stat = 1
        elif measure == 'chi-square':
            stat = 2
        else:
            stat = 1

        # time start
        if verbose:
            print('Running...')
            t0 = time.time()

        # Generate keywords table
        kwlst = kit_tools.Keywords()
        if use_tfidf:
            k = make_keywords_tfidf(self.workspace, self.corpus_name, self.language,
                                    ignore_numbers=ignore_numbers,
                                    ignore_strange=ignore_strange,
                                    min_chars=min_chars)
        else:
            k = make_keywords(self.workspace, self.corpus_name, self.language, stat,
                              ref_language=ref_language,
                              ignore_numbers=ignore_numbers,
                              ignore_strange=ignore_strange,
                              min_chars=min_chars)
        kwlst.df = pd.DataFrame(k, columns=['N', 'WORD', 'FREQUENCY', 'KEYNESS'])
        k = None  # Free memory
        
        # Filter out words in stoplist
        kwlst.df = kwlst.df[~kwlst.df['WORD'].isin(stoplist)]
        
        # Sort by keyness score, reassign ranking, and round keyness values
        decimals = 6 if use_tfidf else 2
        kwlst.df['KEYNESS'] = kwlst.df['KEYNESS'].apply(lambda x: round(x, decimals))
        kwlst.df.sort_values('KEYNESS', ascending=False, inplace=True)
        kwlst.df['N'] = [i + 1 for i in range(len(kwlst.df))]
        kwlst.df.reset_index(drop=True, inplace=True)
        
        # time end
        if verbose:
            t1 = time.time()
            total_time = round(t1 - t0, 2)
            print('')
            print('Total time: %s seconds' % total_time)
        
        return kwlst

    def _keywords_extended(self, **kwargs):
        """Keyword analysis with reference corpora, effect sizes, polarity and p-values."""
        measure = kwargs.get('measure', 'log-likelihood')
        stoplist = kwargs.get('stoplist', None)
        allowlist = kwargs.get('allowlist', None)
        verbose = kwargs.get('verbose', False)
        ref_language = kwargs.get('ref_language', None)
        ref_corpus = kwargs.get('ref_corpus', None)
        ignore_numbers = kwargs.get('ignore_numbers', True)
        ignore_strange = kwargs.get('ignore_strange', True)
        min_chars = kwargs.get('min_chars', 2)
        effect = kwargs.get('effect', None)
        polarity = kwargs.get('polarity', 'all') or 'all'
        p_value = kwargs.get('p_value', None)
        use_bonferroni = kwargs.get('bonferroni', False)
        min_freq = kwargs.get('min_freq', 1) or 1
        min_range = kwargs.get('min_range', 1) or 1
        sort_by = kwargs.get('sort_by', 'keyness') or 'keyness'

        if polarity not in ('all', 'positive', 'negative'):
            raise ValueError("polarity must be 'all', 'positive' or 'negative'")
        if measure == 'log-likelihood' or measure not in py_measures.KEYNESS_MEASURES + ('text-dispersion',):
            measure = 'log-likelihood'
        if measure == 'text-dispersion' and ref_corpus is None:
            raise ValueError("The 'text-dispersion' measure requires a reference corpus (ref_corpus).")
        effects = [] if not effect else ([effect] if isinstance(effect, str) else list(effect))
        for e in effects:
            if e not in py_measures.EFFECT_MEASURES:
                raise ValueError(f'Unknown effect measure: {e}. Use one of {py_measures.EFFECT_MEASURES}')

        if verbose:
            print('Running...')
            t0 = time.time()

        # target data
        tokens, _, _, _, wordlist = make_wordlist(self.workspace, self.corpus_name, self.language, True)
        ref_tokens, ref_freq, ref_range, ref_files = self._reference_data(ref_corpus, ref_language, True)
        need_range = ref_corpus is not None or min_range > 1 or measure == 'text-dispersion'
        tar_range, tar_files = {}, 0
        if need_range:
            _, _, tar_range, tar_files = py_extras.corpus_frequency_list(self.workspace, self.corpus_name, True)

        rows = []
        for row in wordlist:
            word, freq = row[1], row[2]
            if ignore_numbers and _re_number.match(word):
                continue
            if ignore_strange and _re_strange.search(word):
                continue
            if len(word) < min_chars or freq < min_freq:
                continue
            if need_range and tar_range.get(word, 0) < min_range:
                continue
            if ref_corpus is None:
                # the bundled reference list is smoothed with frequency 1 (as in the default analysis)
                rf = ref_freq.get(word, 1)
            else:
                rf = ref_freq.get(word, 0)
            if measure == 'text-dispersion':
                k = py_measures.keyness(tar_range.get(word, 0), ref_range.get(word, 0), tar_files, ref_files,
                                        'log-likelihood')
            elif ref_corpus is None and measure in ('log-likelihood', 'chi-square'):
                # same values as the default analysis with the bundled reference list
                from kitconc.py_keywords import ll as legacy_ll, chi_square as legacy_chi
                if measure == 'log-likelihood':
                    k = legacy_ll(freq, rf, tokens, ref_tokens)
                else:
                    k = legacy_chi(freq, rf, tokens, ref_tokens) * py_measures._sign(freq, rf, tokens, ref_tokens)
            else:
                k = py_measures.keyness(freq, rf, tokens, ref_tokens, measure)
            record = [word, freq, round(k, 2)]
            if ref_corpus is not None:
                record += [rf, tar_range.get(word, 0), ref_range.get(word, 0)]
            for e in effects:
                record.append(round(py_measures.effect_size(freq, rf, tokens, ref_tokens, e), 4))
            rows.append(record)

        # words that occur only in the reference corpus (possible negative keywords)
        if ref_corpus is not None and polarity in ('all', 'negative'):
            target_words = {r[1] for r in wordlist}
            for word, rf in ref_freq.items():
                if word in target_words or len(word) < min_chars:
                    continue
                if ignore_numbers and _re_number.match(word):
                    continue
                if ignore_strange and _re_strange.search(word):
                    continue
                if min_freq > 1 or min_range > 1:
                    continue
                if measure == 'text-dispersion':
                    k = py_measures.keyness(0, ref_range.get(word, 0), tar_files, ref_files, 'log-likelihood')
                else:
                    k = py_measures.keyness(0, rf, tokens, ref_tokens, measure)
                record = [word, 0, round(k, 2), rf, 0, ref_range.get(word, 0)]
                for e in effects:
                    record.append(round(py_measures.effect_size(0, rf, tokens, ref_tokens, e), 4))
                rows.append(record)

        columns = ['WORD', 'FREQUENCY', 'KEYNESS']
        if ref_corpus is not None:
            columns += ['REF_FREQUENCY', 'RANGE', 'REF_RANGE']
        effect_columns = [e.upper() for e in effects]
        columns += effect_columns
        df = pd.DataFrame(rows, columns=columns)

        # filters
        if polarity == 'positive':
            df = df[df.KEYNESS > 0]
        elif polarity == 'negative':
            df = df[df.KEYNESS < 0]
        if p_value is not None:
            p = p_value
            if use_bonferroni:
                p = py_measures.bonferroni(float(str(p).replace('p<', '')), max(len(df), 1))
            critical = py_measures.p_value_threshold(p)
            df = df[df.KEYNESS.abs() >= critical]
        if stoplist is not None and isinstance(stoplist, (list, tuple, set)):
            df = df[~df['WORD'].isin(stoplist)]
        else:
            df = py_extras.filter_by_words(df, 'WORD', stoplist, None, self.language)
        df = py_extras.filter_by_words(df, 'WORD', None, allowlist, self.language)

        # sort
        if sort_by == 'effect' and effect_columns:
            key = effect_columns[0]
        else:
            key = 'KEYNESS'
        df = df.sort_values(key, ascending=(polarity == 'negative'), kind='mergesort')
        df.insert(0, 'N', range(1, len(df) + 1))
        df.reset_index(drop=True, inplace=True)

        kwlst = kit_tools.Keywords()
        kwlst.df = df
        if verbose:
            print('')
            print('Total time: %s seconds' % round(time.time() - t0, 2))
        return kwlst


    def wtfreq(self, **kwargs):
        """
        Generates a word-tag frequency list based on the corpus text files.

        This method processes the text files within the corpus to build a frequency table that
        contains the occurrence count and percentage for each word along with its associated tag.
        It also allows optional conversion of letters to lowercase and displays progress information.

        Keyword Arguments:
        - lowercase (bool): If True (default), converts all letters to lowercase.
        - verbose (bool): If True, prints progress messages and timing information during execution.

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
        verbose = kwargs.get('verbose', False)
        
        # time start
        if verbose:
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
        if verbose:
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
        - verbose (bool): If True, prints progress messages and timing information during processing.

        Returns:
        Wfreqinfiles: An object containing a pandas DataFrame with the following columns:
            - 'N': Sequential index for each word.
            - 'WORD': The word extracted from the corpus.
            - 'RANGE': The number of files in which the word appears.
            - '%': The percentage frequency of the word across the corpus, rounded to two decimal places.
        """
        # args
        lowercase = kwargs.get('lowercase', True)
        verbose = kwargs.get('verbose', False)
        
        # time start
        if verbose:
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
        if verbose:
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
        wildcards (bool, optional): Interprets ``*``, ``?``, ``a|b`` and ``[a,b]`` as wildcards. Default is False.
        context (str or list, optional): Context word(s) required near the node (Context Search). Default is None.
        context_span (int or tuple, optional): Context window in tokens, e.g. 5 or (3, 5) for 3L-5R. Default is 5.
        context_mode (str, optional): 'or' (any context word) or 'and' (all context words). Default is 'or'.
        context_exclude (bool, optional): Keeps only lines WITHOUT the context words. Default is False.
        sample (int, optional): Returns a random sample of this many lines (kept in corpus order).
        seed (int, optional): Random seed for ``sample``.
        verbose (bool, optional): If True, prints progress messages and timing information during processing. Default is False.

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
        verbose = kwargs.get('verbose', False)
        node, regexp = self._prepare_query(node, regexp, kwargs.get('wildcards', False))
        context = kwargs.get('context', None)
        span = kwargs.get('context_span', 5)
        left_span, right_span = (span, span) if isinstance(span, int) else (int(span[0]), int(span[1]))
        search_horizon = max(horizon, left_span, right_span) if context else horizon

        # time start
        if verbose:
            print('Running...')
            t0 = time.time()

        # Process concordance lines
        nl, lst_kwic = make_kwic(self.workspace, self.corpus_name, node, pos, case_sensitive, regexp, search_horizon)
        kwic = kit_tools.Kwic(node_length=nl)
        kwic.df = pd.DataFrame(lst_kwic, columns=['N', 'LEFT', 'NODE', 'RIGHT', 'FILENAME', 'TOKEN_ID', 'SENT_ID', 'FILE_ID'])
        lst_kwic = None

        # Context search (and trimming of the wider search horizon)
        if context:
            kwic.df = py_extras.context_filter(kwic.df, context, left_span, right_span,
                                               kwargs.get('context_mode', 'or'),
                                               kwargs.get('context_exclude', False),
                                               case_sensitive, kwargs.get('context_regexp', False))
            if search_horizon != horizon:
                kwic.df = kwic.df.copy()
                kwic.df['LEFT'] = kwic.df['LEFT'].map(lambda s: ' '.join(str(s).split(' ')[-horizon:]) if horizon > 0 else '')
                kwic.df['RIGHT'] = kwic.df['RIGHT'].map(lambda s: ' '.join(str(s).split(' ')[:horizon]) if horizon > 0 else '')

        # Random sample
        if kwargs.get('sample', None):
            kwic.df = py_extras.random_sample(kwic.df, int(kwargs['sample']), kwargs.get('seed', None))

        # Limit results if a limit is specified
        if limit is not None:
            kwic.df = kwic.df.head(limit)
        
        # Reset indices to ensure sequential numbering
        kwic.df['N'] = [i + 1 for i in range(len(kwic.df))]
        kwic.df.reset_index(drop=True, inplace=True)
        
        # time end and progress update
        if verbose:
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
        wildcards (bool, optional): Interprets ``*``, ``?``, ``a|b`` and ``[a,b]`` as wildcards. Default is False.
        sample (int, optional): Returns a random sample of this many lines; ``seed`` sets the random seed.
        verbose (bool, optional): If True, prints progress messages and timing information. Default is False.

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
        node, regexp = self._prepare_query(node, regexp, kwargs.get('wildcards', False))
        limit = kwargs.get('limit', None)
        verbose = kwargs.get('verbose', False)
        
        # time start
        if verbose:
            print('Running...')
            t0 = time.time()
        
        # Process concordance lines
        nl, lst_conc = make_concordance(self.workspace, self.corpus_name, node, pos, case_sensitive, regexp)
        conc = kit_tools.Concordance(node_length=nl)
        conc.df = pd.DataFrame(lst_conc, columns=['N', 'CONCORDANCE', 'FILENAME', 'TOKEN_ID', 'SENT_ID', 'FILE_ID'])
        lst_conc = None

        # Random sample
        if kwargs.get('sample', None):
            conc.df = py_extras.random_sample(conc.df, int(kwargs['sample']), kwargs.get('seed', None))

        # Limit results if a limit is specified
        if limit is not None:
            conc.df = conc.df.head(limit)
        
        # Reset indices for sequential numbering
        conc.df['N'] = [i + 1 for i in range(len(conc.df))]
        conc.df.reset_index(drop=True, inplace=True)
        
        # time end and print progress
        if verbose:
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
                                        Also accepted: 'mi2', 'mi3', 'log-likelihood', 'log-likelihood-2',
                                        'chi-square', 'dice', 'log-dice', 'log-ratio', 'z-score', 'ms', 'mu'.
        extra_measures (str or list, optional): Further measures added as extra columns (named in upper case),
                                        e.g. ['log-likelihood', 'log-dice'].
        min_freq (int, optional): Minimum co-occurrence frequency (default is 1).
        stoplist / allowlist (optional): Collocates to exclude / to keep (list, file path or 'default').
        wildcards (bool, optional): Interprets ``*``, ``?``, ``a|b`` and ``[a,b]`` in the node as wildcards.
        limit (int, optional): Maximum number of collocate results to return. If None, all results are returned.
        verbose (bool, optional): If True, prints progress messages and execution time. Default is False.

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
        node, regexp = self._prepare_query(node, regexp, kwargs.get('wildcards', False))
        left_span = kwargs.get('left_span', 5)
        right_span = kwargs.get('right_span', 5)
        lowercase = kwargs.get('lowercase', True)
        measure = kwargs.get('measure', 1)
        limit = kwargs.get('limit', None)
        verbose = kwargs.get('verbose', False)
        extra = kwargs.get('extra_measures', None)
        extra = [] if not extra else ([extra] if isinstance(extra, str) else list(extra))
        for m in extra:
            if m not in py_measures.COLLOCATE_MEASURES:
                raise ValueError(f'Unknown association measure: {m}. Use one of {py_measures.COLLOCATE_MEASURES}')

        # time start
        if verbose:
            print('Running...')
            t0 = time.time()

        # Determine statistical measure
        if measure == 't-score':
            measure = 1
        elif measure in ('mutual information', 'mi'):
            measure = 2
        elif isinstance(measure, str) and measure not in py_measures.COLLOCATE_MEASURES:
            import warnings
            warnings.warn(f"Unknown collocate measure '{measure}'; mutual information is used.", stacklevel=2)
            measure = 2

        # Generate collocates list
        details = {}
        lst_coll = make_collocates(self.workspace, self.corpus_name, node, pos, case_sensitive, regexp,
                                coll_pos, lowercase, left_span, right_span, measure, details=details)
        coll = kit_tools.Collocates()
        coll.df = pd.DataFrame(lst_coll, columns=['N', 'WORD', 'FREQUENCY', 'LEFT', 'RIGHT', 'ASSOCIATION'])
        lst_coll = None

        # Optional filters and extra association columns
        min_freq = kwargs.get('min_freq', 1)
        if min_freq > 1:
            coll.df = coll.df[coll.df.FREQUENCY >= min_freq]
        coll.df = py_extras.filter_by_words(coll.df, 'WORD', kwargs.get('stoplist', None),
                                            kwargs.get('allowlist', None), self.language)
        if extra and details:
            freqs = details['collocate_freqs']
            for m in extra:
                coll.df[m.upper()] = [round(py_measures.association(f, details['node_count'], freqs.get(w, 0),
                                                                     details['tokens'], m), 2)
                                      for w, f in zip(coll.df['WORD'], coll.df['FREQUENCY'])]
        elif extra:
            for m in extra:
                coll.df[m.upper()] = []

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
        if verbose:
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
        verbose (bool, optional): If True, prints progress messages during processing (default is False).

        Returns:
        ComparedCollocates: An object containing a pandas DataFrame with the comparison results.
        """
        # kwargs
        stat_cutoff = kwargs.get('stat_cutoff', 0)
        verbose = kwargs.get('verbose', False)
        # time start
        if verbose == True:
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
            if verbose == True:
                self.__progress(i, total, '')
        comparison = kit_tools.ComparedCollocates()
        comparison.read_str('\n'.join(s))
        del s 
        comparison.df.sort_values('DIFFERENCE', ascending=True, inplace=True)
        comparison.df['N'] = [i + 1 for i in range(len(comparison.df))]
        comparison.df.reset_index(drop=True, inplace=True)
        # time end
        if verbose == True:
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
        verbose (bool): If True, prints progress messages and execution time. Default is False.

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
        verbose = kwargs.get('verbose', False)
        
        # time start
        if verbose:
            print('Running...')
            t0 = time.time()
        
        # Determine statistical measure identifier
        if measure == 'tscore':
            stat = 1
        elif measure == 'mutual information':
            stat = 2
        
        # Compile pattern to avoid punctuation-only tokens
        ptn = re.compile(r"^\W+$")
        
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
            if verbose:
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
        if verbose:
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
        position (str, optional): Position of the search word in the cluster: 'both' (default, any position),
                                  'left' (clusters starting with the word) or 'right' (clusters ending with it).
        case_sensitive, regexp, wildcards (bool, optional): Search options. By default only the first word
                                  of the search term is used; multi-word search terms are matched as a phrase
                                  when any extended option (position, size > 3, case_sensitive, regexp,
                                  wildcards) is used.
        stoplist / allowlist (optional): Clusters containing a stoplist word are removed; with an
                                  allowlist, only clusters made of allowed words are kept.
        Any cluster size >= 1 is accepted (sizes above 3 use the extended algorithm).
        verbose (bool, optional): If True, prints progress messages and the total execution time. Default is False.

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
        verbose = kwargs.get('verbose', False)
        
        # time start
        if verbose == True:
            print('Running...')
            t0 = time.time()
        
        position = kwargs.get('position', 'both')
        case_sensitive = kwargs.get('case_sensitive', False)
        regexp = kwargs.get('regexp', False)
        word, regexp = self._prepare_query(word, regexp, kwargs.get('wildcards', False))
        # the original algorithm (sizes 1-3, first word of the search term only) is kept as default
        if size <= 3 and position == 'both' and not regexp and not case_sensitive:
            lst_clusters = make_clusters(self.workspace, self.corpus_name, word, pos, lowercase, size)
        else:
            lst_clusters = py_extras.make_clusters_ext(self.workspace, self.corpus_name, word, pos, lowercase,
                                                       size, position, case_sensitive, regexp)
        clusters = kit_tools.Clusters()
        clusters.df = pd.DataFrame(lst_clusters, columns=['N', 'CLUSTER', 'FREQUENCY', 'RANGE', '%'])
        lst_clusters = None
        
        # sort clusters by frequency in descending order
        clusters.df.sort_values('FREQUENCY', ascending=False, inplace=True)
        
        # apply filtering based on minimum frequency and range
        clusters.df = clusters.df[(clusters.df.FREQUENCY >= min_freq)]
        clusters.df = clusters.df[(clusters.df.RANGE >= min_range)]
        clusters.df = py_extras.filter_by_words(clusters.df, 'CLUSTER', kwargs.get('stoplist', None),
                                                kwargs.get('allowlist', None), self.language, split_items=True)
        
        # process DataFrame: round percentage, reassign sequential indexes, and reset index
        clusters.df['%'] = clusters.df['%'].apply(lambda x: round(x, 2))
        clusters.df['N'] = [i + 1 for i in range(len(clusters.df))]
        clusters.df.reset_index(drop=True, inplace=True)
        
        # time end and display total time if progress is enabled
        if verbose == True:
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
        - search (str, optional): Keeps only n-grams containing a word that matches the query
                                  (wildcards, or a regular expression when ``regexp`` is True).
        - stoplist / allowlist (optional): N-grams containing a stoplist word are removed; with an
                                  allowlist, only n-grams made of allowed words are kept.
        - verbose (bool, optional): If True, prints progress messages and timing information. Default is False.

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
        verbose = kwargs.get('verbose', False)
        
        # time start
        if verbose:
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
        if kwargs.get('search', None):
            ng.df = self._filter_items(ng.df, 'N-GRAM', kwargs['search'], kwargs.get('regexp', False), lowercase)
        ng.df = py_extras.filter_by_words(ng.df, 'N-GRAM', kwargs.get('stoplist', None),
                                          kwargs.get('allowlist', None), self.language, split_items=True)
        
        # reset indexes and round percentage values
        ng.df['%'] = ng.df['%'].apply(lambda x: round(x, 2))
        ng.df['N'] = [i + 1 for i in range(len(ng.df))]
        ng.df.reset_index(drop=True, inplace=True)
        
        # time end and display progress if enabled
        if verbose:
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
          verbose (bool, optional): If True, displays progress messages and timing info. Default is False.
        
          wildcards (bool, optional): Interprets ``*``, ``?``, ``a|b`` and ``[a,b]`` as wildcards. Default is False.
        
        Returns:
          Dispersion: An object with attributes:
              - df: A pandas DataFrame with columns ['N','FILENAME','TOTAL','HITS','S1','S2','S3','S4','S5'].
              - dpts: Dispersion points data.
              - total_s1, total_s2, total_s3, total_s4, total_s5: Totals for each section.
              - stats: corpus-level dispersion of the search term over the text files
                       (range, sd, cv, juilland-d, dp, dp-norm, files, hits).
              - range, juilland_d, dp: shortcuts to the values in ``stats``.
        """
        node = node.strip()
        pos = kwargs.get('pos', None)
        case_sensitive = kwargs.get('case_sensitive', False)
        regexp = kwargs.get('regexp', False)
        limit = kwargs.get('limit', None)
        verbose = kwargs.get('verbose', False)
        
        if verbose:
            print('Running...')
            t0 = time.time()
        
        node, regexp = self._prepare_query(node, regexp, kwargs.get('wildcards', False))
        totals, dpts, lst_disp = make_dispersion(self.workspace, self.corpus_name, node, pos, case_sensitive, regexp)
        disp = kit_tools.Dispersion(output_path=self.output_path)
        disp.df = pd.DataFrame(lst_disp, columns=['N', 'FILENAME', 'TOTAL', 'HITS', 'S1', 'S2', 'S3', 'S4', 'S5'])
        disp.dpts = dpts
        if not totals:  # no hits
            totals = (0, 0, 0, 0, 0)
        disp.total_s1, disp.total_s2, disp.total_s3, disp.total_s4, disp.total_s5 = totals
        disp.stats = self._dispersion_stats(disp.df)
        disp.range = disp.stats['range']
        disp.juilland_d = disp.stats['juilland-d']
        disp.dp = disp.stats['dp']
        lst_disp = None
        
        disp.df.sort_values('HITS', ascending=False, inplace=True)
        if limit is not None:
            disp.df = disp.df.head(limit)
        disp.df['N'] = [i + 1 for i in range(len(disp.df))]
        disp.df.reset_index(drop=True, inplace=True)
        
        if verbose:
            t1 = time.time()
            print('')
            print('Total time: %s seconds' % round(t1 - t0, 2))
        return disp

    def _dispersion_stats(self, df):
        """Corpus-level dispersion of a search term from a dispersion table (all text files)."""
        npy_path = self.workspace + self.corpus_name + '/data/npy/'
        sizes = {}
        for filename in os.listdir(npy_path):
            arr = np.load(npy_path + filename, mmap_mode='r')
            sizes[filename[:-4] if filename.endswith('.npy') else filename] = int(arr.shape[0])
        hits = {str(f): int(h) for f, h in zip(df['FILENAME'], df['HITS'])}
        names = sorted(sizes)
        stats = py_measures.dispersion([hits.get(n, 0) for n in names], [sizes[n] for n in names])
        stats = {k: round(v, 4) for k, v in stats.items()}
        stats['files'] = len(names)
        stats['hits'] = int(sum(hits.values()))
        return stats

    def keywords_dispersion(self, keywords, **kwargs):
        """
        Generates a dispersion plot using keyword data.

        Keyword Arguments:
        limit (int, optional): Maximum number of keywords to use. Default is 25.
        lowercase (bool, optional): If True (default), converts text to lowercase before processing.
        verbose (bool, optional): If True, displays progress messages and timing info. Default is False.

        Returns:
        KeywordsDispersion: An object containing:
            - df: A pandas DataFrame with columns ['N','WORD','KEYNESS','HITS','S1','S2','S3','S4','S5'].
            - dpts: Dispersion points data.
            - total_s1, total_s2, total_s3, total_s4, total_s5: Totals for each section.
        """
        lowercase = kwargs.get('lowercase', True)
        limit = kwargs.get('limit', 25)
        verbose = kwargs.get('verbose', False)

        if verbose:
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

        if verbose:
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
          verbose (bool, optional): If True, displays progress messages. Default is False.
        
        Returns:
          Combolist: An object containing a pandas DataFrame with columns:
                     ['N', 'WORD', 'POS', 'FREQUENCY', 'F%', 'KEYNESS', 'RANGE', 'R%', 'STOPWORD', 'LEMMA', 'CAT'].
        """
        min_freq = kwargs.get('min_freq', 1)
        min_range = kwargs.get('min_range', 0)
        negative_keyness = kwargs.get('negative_keyness', True)
        cat = kwargs.get('cat', None)
        limit = kwargs.get('limit', None)
        verbose = kwargs.get('verbose', False)
        max_pos = kwargs.get('max_pos', 1)
        
        if verbose:
            print('Running...')
            t0 = time.time()
        
        # Retrieve and filter the wordlist
        if verbose:
            print('Wordlist...')
        df = self.wordlist().df.filter(['WORD', 'FREQUENCY', '%'])
        df.columns = ['WORD', 'FREQUENCY', 'F%']
        df = df[df.FREQUENCY >= min_freq]
        
        # Merge with keywords data
        if verbose:
            print('Keywords...')
        keywords_df = self.keywords().df.filter(['WORD', 'KEYNESS'])
        df = pd.merge(df, keywords_df, on='WORD')
        if not negative_keyness:
            df = df[df.KEYNESS >= 0]
        
        # Merge with file frequency data (wfreqinfiles)
        if verbose:
            print('Freqinfiles...')
        wfreqinfiles = self.wfreqinfiles().df.filter(['WORD', 'RANGE', '%'])
        wfreqinfiles.columns = ['WORD', 'RANGE', 'R%']
        df = pd.merge(df, wfreqinfiles, on='WORD')
        df = df[df['R%'] >= min_range]
        
        # Merge with word-tag frequency data (wtfreq) to get POS information
        if verbose:
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
        if verbose:
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
        if verbose:
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
        
        if verbose:
            t1 = time.time()
            print('')
            print('Total time: %s seconds' % round(t1 - t0, 2))
        return cmblist

    def pframes(self, **kwargs):
        """
        Generates n-grams with open slots (phrase-frames or p-frames), e.g. "the * of the".

        Keyword Arguments:
          size (int, optional): N-gram size (default is 4).
          slots (int or list, optional): Number of open slots (every position combination is generated)
                                         or a list of 1-based slot positions, e.g. [2]. Default is 1.
          pos (str, optional): One POS tag per position to filter the n-grams.
          lowercase (bool, optional): Default is True.
          minfreq / minrange (int, optional): Minimum frequency / number of text files. Defaults are 2 and 1.
          min_variants (int, optional): Minimum number of distinct slot fillers (default is 2).
          stoplist / allowlist (optional): Applied to the fixed words of the frame.
          limit (int, optional): Maximum number of rows.
          verbose (bool, optional): Default is False.

        Returns:
          Pframes: an object whose DataFrame has the columns ['N', 'P-FRAME', 'FREQUENCY', 'RANGE', '%',
                   'VARIANTS', 'TTR', 'ENTROPY', 'TOP_VARIANTS'] (TTR = variants/frequency; ENTROPY in bits).
        """
        verbose = kwargs.get('verbose', False)
        if verbose:
            print('Running...')
            t0 = time.time()
        rows = py_extras.make_pframes(self.workspace, self.corpus_name, kwargs.get('size', 4), kwargs.get('slots', 1),
                                      kwargs.get('lowercase', True), kwargs.get('pos', None))
        df = pd.DataFrame(rows, columns=['N', 'P-FRAME', 'FREQUENCY', 'RANGE', '%', 'VARIANTS', 'TTR', 'ENTROPY',
                                         'TOP_VARIANTS'])
        df = df[(df.FREQUENCY >= kwargs.get('minfreq', 2)) & (df.RANGE >= kwargs.get('minrange', 1))
                & (df.VARIANTS >= kwargs.get('min_variants', 2))]
        fixed = df['P-FRAME'].map(lambda f: ' '.join(w for w in f.split(' ') if w != '*'))
        kept = py_extras.filter_by_words(pd.DataFrame({'F': fixed}), 'F', kwargs.get('stoplist', None),
                                         kwargs.get('allowlist', None), self.language, split_items=True)
        df = df.loc[kept.index]
        df = df.sort_values(['FREQUENCY', 'VARIANTS'], ascending=False, kind='mergesort')
        if kwargs.get('limit', None) is not None:
            df = df.head(kwargs['limit'])
        for col, nd in (('%', 2), ('TTR', 3), ('ENTROPY', 3)):
            df[col] = df[col].round(nd)
        result = kit_tools.Pframes()
        result.df = self._renumber(df)
        if verbose:
            print('Total time: %s seconds' % round(time.time() - t0, 2))
        return result

    def lemmalist(self, **kwargs):
        """
        Generates a frequency list of lemmas (headwords), as AntConc's Headword display.

        Keyword Arguments:
          lemma_file (str, optional): Lemma list. Default: the bundled ``lemmas_<language>.tab``.
          lemma_format (str, optional): 'auto' (default), 'form-lemma' (``form<TAB>lemma``) or
                                        'headword-forms' (``headword<TAB>form1<TAB>form2...``, AntConc style).
          min_freq / min_range (int, optional): Minimum frequency / number of text files (default is 1).
          stoplist / allowlist (optional): Applied to lemmas.
          unlisted (bool, optional): Keep words not found in the lemma list as their own lemma (default True).
          verbose (bool, optional): Default is False.

        Returns:
          Lemmalist: an object whose DataFrame has the columns ['N', 'LEMMA', 'FREQUENCY', '%', 'RANGE', 'FORMS'].
        """
        verbose = kwargs.get('verbose', False)
        lemma_file = kwargs.get('lemma_file', None)
        if lemma_file is None:
            lemma_file = self.resource_data_path + 'lemmas_' + self.language + '.tab'
            if not os.path.exists(lemma_file):
                raise ValueError(f'No bundled lemma list for {self.language}; pass lemma_file=...')
        if verbose:
            print('Running...')
            t0 = time.time()
        lemma_map = py_extras.load_lemma_map(lemma_file, kwargs.get('lemma_format', 'auto'))
        freqs, sizes, _ = py_extras.word_file_frequencies(self.workspace, self.corpus_name, True)
        if not kwargs.get('unlisted', True):
            freqs = {w: v for w, v in freqs.items() if w in lemma_map}
        grouped = py_extras.lemma_frequencies(freqs, lemma_map)
        tokens = float(sum(sizes)) or 1.0
        rows = []
        for lemma, (freq, files, forms) in grouped.items():
            rows.append([lemma, freq, round(freq * 100 / tokens, 2), len(files),
                         ' '.join(f'{w}({c})' for w, c in forms.most_common())])
        df = pd.DataFrame(rows, columns=['LEMMA', 'FREQUENCY', '%', 'RANGE', 'FORMS'])
        df = df[(df.FREQUENCY >= kwargs.get('min_freq', 1)) & (df.RANGE >= kwargs.get('min_range', 1))]
        df = py_extras.filter_by_words(df, 'LEMMA', kwargs.get('stoplist', None), kwargs.get('allowlist', None),
                                       self.language)
        df = df.sort_values(['FREQUENCY', 'LEMMA'], ascending=[False, True], kind='mergesort')
        df.insert(0, 'N', range(1, len(df) + 1))
        df.reset_index(drop=True, inplace=True)
        result = kit_tools.Lemmalist()
        result.df = df
        if verbose:
            print('Total time: %s seconds' % round(time.time() - t0, 2))
        return result

    def dispersion_measures(self, words=None, **kwargs):
        """
        Dispersion statistics of words over the text files of the corpus.

        Parameters:
          words (list, optional): Words to analyse. Default: every word in the corpus.

        Keyword Arguments:
          lowercase (bool, optional): Default is True.
          min_freq (int, optional): Minimum frequency (default is 1).

        Returns:
          DispersionMeasures: an object whose DataFrame has the columns ['N', 'WORD', 'FREQUENCY', 'RANGE',
                              'R%', 'SD', 'CV', 'JUILLAND_D', 'DP', 'DP_NORM'], sorted by frequency.
        """
        lowercase = kwargs.get('lowercase', True)
        freqs, sizes, _ = py_extras.word_file_frequencies(self.workspace, self.corpus_name, lowercase)
        selected = list(freqs) if words is None else [w.lower() if lowercase else w for w in words]
        rows = []
        for w in selected:
            per_file = freqs.get(w, {})
            vector = [per_file.get(i, 0) for i in range(len(sizes))]
            st = py_measures.dispersion(vector, sizes)
            rows.append([w, int(sum(vector)), int(st['range']),
                         round(st['range'] * 100 / len(sizes), 2) if sizes else 0.0,
                         round(st['sd'], 4), round(st['cv'], 4), round(st['juilland-d'], 4),
                         round(st['dp'], 4), round(st['dp-norm'], 4)])
        df = pd.DataFrame(rows, columns=['WORD', 'FREQUENCY', 'RANGE', 'R%', 'SD', 'CV', 'JUILLAND_D', 'DP',
                                         'DP_NORM'])
        df = df[df.FREQUENCY >= kwargs.get('min_freq', 1)]
        df = df.sort_values(['FREQUENCY', 'WORD'], ascending=[False, True], kind='mergesort')
        df.insert(0, 'N', range(1, len(df) + 1))
        df.reset_index(drop=True, inplace=True)
        result = kit_tools.DispersionMeasures()
        result.df = df
        return result

    def fileview(self, filename, node=None, **kwargs):
        """
        Shows the text of one corpus file (one sentence per line), optionally marking a search term.

        Parameters:
          filename (str): Name of the text file in the corpus (as in the FILENAME column of other tools).
          node (str, optional): Search term to highlight.

        Keyword Arguments:
          case_sensitive, regexp, wildcards (bool, optional): Search options.
          marker (str, optional): Format used to mark hits (default is '[[{}]]').

        Returns:
          FileView: an object with ``text`` (str), ``hits`` (int), ``tokens`` (int), ``types`` (int),
                    ``filename`` and a DataFrame ``df`` with the hits (N, TOKEN_ID, SENT_ID, HIT).
        """
        npy_file = self.workspace + self.corpus_name + '/data/npy/' + filename + '.npy'
        if not os.path.exists(npy_file):
            raise ValueError(f'File not found in corpus {self.corpus_name}: {filename}')
        arr = np.load(npy_file)
        with open(self.workspace + self.corpus_name + '/data/idx/words.pickle', 'rb') as fh:
            dict_words = pickle.load(fh)
        words = [dict_words.get(int(i), '') for i in arr[:, 0]]
        marks = set()
        hits = []
        if node:
            n, regexp = self._prepare_query(node.strip(), kwargs.get('regexp', False), kwargs.get('wildcards', False))
            case_sensitive = kwargs.get('case_sensitive', False)
            terms = n.split()
            if regexp:
                flags = 0 if case_sensitive else re.IGNORECASE
                pats = [re.compile(t, flags) for t in terms]
                match = lambda w, j: pats[j].match(w) is not None
            else:
                match = (lambda w, j: w == terms[j]) if case_sensitive else (lambda w, j: w.lower() == terms[j].lower())
            size = len(terms)
            for i in range(len(words) - size + 1):
                if all(match(words[i + j], j) for j in range(size)):
                    hits.append((len(hits) + 1, i, int(arr[i, 2]), ' '.join(words[i:i + size])))
                    marks.update(range(i, i + size))
        marker = kwargs.get('marker', '[[{}]]')
        lines, current, sent = [], [], None
        for i, w in enumerate(words):
            s = int(arr[i, 2])
            if sent is not None and s != sent:
                lines.append(' '.join(current))
                current = []
            sent = s
            current.append(marker.format(w) if i in marks else w)
        if current:
            lines.append(' '.join(current))
        view = kit_tools.FileView()
        view.filename = filename
        view.text = '\n'.join(lines)
        view.hits = len(hits)
        view.tokens = len(words)
        view.types = len({w.lower() for w in words if not re.match(r'^\W+$', w)})
        view.df = pd.DataFrame(hits, columns=['N', 'TOKEN_ID', 'SENT_ID', 'HIT'])
        return view

    def wordcloud(self, data=None, filename=None, **kwargs):
        """
        Creates a word cloud image from a result object/DataFrame (e.g. wordlist, keywords, collocates)
        or, by default, from the corpus wordlist.

        Parameters:
          data (optional): A kitconc result object (with ``df``), a DataFrame, a dict {word: value} or text.
                           Default: the corpus wordlist without the bundled stoplist words.
          filename (str, optional): PNG file to save (relative names are saved in the corpus output folder).

        Keyword Arguments (passed to kit_plots.wordcloud): word_column, value_column, max_words, width,
          height, colormap, background, stoplist, font_path, min_font_size, max_font_size, scale ('linear',
          'sqrt' or 'log'), seed.

        Returns:
          PIL.Image.Image
        """
        from kitconc import kit_plots
        if data is None:
            has_stoplist = os.path.exists(self.resource_data_path + 'stoplist_' + self.language + '.tab')
            data = self.wordlist(stoplist='default') if has_stoplist else self.wordlist()
        if filename is not None and not os.path.isabs(filename) and os.path.dirname(filename) == '':
            filename = self.output_path + filename
        if kwargs.get('stoplist') is not None and not isinstance(kwargs.get('stoplist'), (list, set, tuple)):
            kwargs['stoplist'] = py_extras.load_word_set(kwargs['stoplist'], self.language)
        return kit_plots.wordcloud(data, filename, **kwargs)

    def export(self, target_folder, **kwargs):
        """
        Exports the current corpus to a specified destination folder.
        
        Parameters:
          target_folder (str): The destination folder where the corpus will be saved.
        
        Keyword Arguments:
          verbose (bool, optional): If True, displays progress messages and timing info. Default is True.
        """
        verbose = kwargs.get('verbose', True)
        if verbose:
            print('Running...')
            t0 = time.time()
        if not os.path.isdir(target_folder):
            raise ValueError(f'The export destination is not a folder: {target_folder}')
        from kitconc.export_corpus import export as export_zip
        result = export_zip(self.workspace, self.corpus_name, target_folder)
        if verbose:
            t1 = time.time()
            print('')
            print('Total time: %s seconds' % round(t1 - t0, 2))
        return result

    def add_from_export(self, filename, **kwargs):
        """
        Imports a corpus from an exported file (ZIP format) into the current workspace.
        
        Parameters:
          filename (str): The path to the corpus ZIP file.
        
        Keyword Arguments:
          verbose (bool, optional): If True, displays progress messages and timing info. Default is False.
        """
        verbose = kwargs.get('verbose', False)
        if verbose:
            print('Running...')
            t0 = time.time()
        result = import_corpus_zip(filename, self.workspace)
        if verbose:
            t1 = time.time()
            print('')
            print('Total time: %s seconds' % round(t1 - t0, 2))
        return result

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
        workspace = str(workspace)
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

    def create(self, corpus_name, language, source_texts, *, tagged=False, verbose=False):
        """
        Creates a new corpus from source texts.
        
        Parameters:
          corpus_name (str): The name for the new corpus.
          language (str): The language of the corpus.
          source_texts (str): The folder path containing the source texts.
        
        Returns:
          Corpus: A new Corpus object.
        """
        name = str(corpus_name).strip()
        if name in {'.', '..'} or not re.fullmatch(r'[A-Za-z0-9_.-]+', name):
            raise ValueError('Corpus name may contain only letters, numbers, _, ., and -; it cannot be . or ..')
        source = Path(source_texts).expanduser().resolve()
        if not source.is_dir():
            raise ValueError(f'Source folder does not exist: {source}')
        workspace = Path(self.workspace).expanduser().resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        corpus_path = (workspace / name).resolve()
        if corpus_path.parent != workspace:
            raise ValueError('Corpus path must be inside the workspace.')
        corpus_path.mkdir(exist_ok=False)
        try:
            corpus = Corpus(str(workspace), name, language)
            corpus.add_texts(str(source), tagged=tagged, verbose=verbose)
            return corpus
        except Exception:
            shutil.rmtree(corpus_path, ignore_errors=True)
            raise

    def import_corpus(self, filename):
        """
        Imports a corpus from a ZIP file into the workspace.
        
        Parameters:
          filename (str): The path to the corpus ZIP file.
        """
        return import_corpus_zip(filename, self.workspace)

    def import_corpus_from_url(self, url):
        """
        Downloads and imports a corpus from a given URL (ZIP file).
        
        Parameters:
          url (str): The URL of the corpus ZIP file.
        """
        return download_and_import_corpus(url, self.workspace)

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
