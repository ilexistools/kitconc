# -*- coding: utf-8 -*-
# Author: jlopes@alumni.usp.br
import os
import math
import pickle
import re
from typing import Dict, List, Optional, Tuple

import numpy as np

from kitconc.py_wordlist import make_wordlist

_re_number = re.compile(r'^\d+([.,]\d+)*$')
_re_strange = re.compile(r'[^a-zA-ZÀ-ÿ\-\']')


def load_reference(language: str) -> Tuple[int, Dict[str, int]]:
    d: Dict[str, int] = {}
    tokens = 0
    kit_path = os.path.dirname(os.path.abspath(__file__))
    with open(kit_path + '/data/reflist_' + language + '.tab', 'r') as fh:
        for line in fh:
            if len(line.strip()) != 0:
                f = line.strip().split('\t')
                if len(f) >= 2:
                    d[f[0]] = int(f[1])
                    tokens += int(f[1])
    return (tokens, d)


def chi_square(freq_stdc: int, freq_refc: int, tk_stdc: int, tk_refc: int) -> float:
    a = freq_stdc
    b = freq_refc
    c = tk_stdc - a
    d = tk_refc - b
    N = a + b + c + d
    denom = (a + b) * (c + d) * (a + c) * (b + d)
    if denom == 0:
        return 0.0
    chi = N * (a * d - b * c) ** 2 / denom
    return round(chi, 2)


def ll(freq_stdc: int, freq_refc: int, tk_stdc: int, tk_refc: int) -> float:
    """Calculates the log-likelihood value."""
    if tk_stdc == 0 or tk_refc == 0:
        return 0.0
    O = float(freq_stdc + freq_refc)
    N1 = float(tk_stdc)
    N2 = float(tk_refc)
    total = N1 + N2
    E1 = N1 * O / total
    E2 = N2 * O / total
    v1 = math.log(freq_stdc / E1) if freq_stdc >= 1 and E1 >= 1 else 0
    v2 = math.log(freq_refc / E2) if freq_refc >= 1 and E2 >= 1 else 0
    LL = round(2 * ((freq_stdc * v1) + (freq_refc * v2)), 2)
    Norm_stdc = freq_stdc / N1
    Norm_refc = freq_refc / N2
    if Norm_stdc == 0:
        Norm_stdc = 0.5 / N1
    if Norm_refc == 0:
        Norm_refc = 0.5 / N2
    if Norm_stdc < Norm_refc:
        LL = -LL
    return LL


def available_ref_languages() -> List[str]:
    """Returns a list of languages that have a non-empty reference list."""
    kit_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(kit_path, 'data')
    langs = []
    for filename in os.listdir(data_path):
        if filename.startswith('reflist_') and filename.endswith('.tab'):
            full_path = os.path.join(data_path, filename)
            if os.path.getsize(full_path) > 0:
                langs.append(filename[len('reflist_'):-len('.tab')])
    return sorted(langs)


def make_keywords(workspace: str, corpus_name: str, language: str, measure: int,
                  ref_language: Optional[str] = None,
                  ignore_numbers: bool = True,
                  ignore_strange: bool = True,
                  min_chars: int = 2) -> List[list]:
    # load wordlist
    tokens, types, type_token, hapax, wordlist = make_wordlist(workspace, corpus_name, language, True)
    # determine which reference list to use
    if ref_language is None:
        ref_language = language
    ref_tokens, ref = load_reference(ref_language)
    # loop
    keywords: List[list] = []
    i = 0
    for row in wordlist:
        word = row[1]
        if ignore_numbers and _re_number.match(word):
            continue
        if ignore_strange and _re_strange.search(word):
            continue
        if len(word) < min_chars:
            continue
        freq_refc = ref.get(word, 1)
        m = ll(row[2], freq_refc, tokens, ref_tokens) if measure == 1 else chi_square(row[2], freq_refc, tokens, ref_tokens)
        i += 1
        keywords.append([i, word, row[2], m])
    return keywords


def make_keywords_tfidf(workspace: str, corpus_name: str, language: str,
                        ignore_numbers: bool = True,
                        ignore_strange: bool = True,
                        min_chars: int = 2) -> List[list]:
    """Computes TF-IDF keyword scores across the corpus documents.

    Each source text file is treated as one document.
    TF  = term_freq_in_doc / doc_length
    IDF = log(num_docs / doc_freq)   (natural log)
    Score per term = mean TF-IDF across all documents that contain it.
    """
    data_path = workspace + corpus_name + '/data/'
    npy_path = data_path + 'npy/'
    idx_path = data_path + 'idx/'

    # Load vocabulary: int_id -> word_str  (already inverted by indexing.py)
    with open(idx_path + 'words.pickle', 'rb') as fh:
        id_to_word: Dict[int, str] = pickle.load(fh)

    # Load filenames: keys are (filename, file_id) tuples
    with open(idx_path + 'filenames.pickle', 'rb') as fh:
        dict_filenames = pickle.load(fh)

    # Build per-document term-count dicts from individual npy files
    doc_counts: List[Dict[int, int]] = []
    for key in dict_filenames:
        fname = key[0]
        npy_file = npy_path + fname + '.npy'
        if not os.path.exists(npy_file):
            continue
        arr = np.load(npy_file)
        if arr.ndim == 1:
            word_ids = arr
        else:
            word_ids = arr[:, 0]
        unique_ids, counts = np.unique(word_ids, return_counts=True)
        doc_counts.append({int(uid): int(c) for uid, c in zip(unique_ids, counts)})

    D = len(doc_counts)
    if D == 0:
        return []

    # Document frequency: how many docs contain each word_id
    df: Dict[int, int] = {}
    for tc in doc_counts:
        for wid in tc:
            df[wid] = df.get(wid, 0) + 1

    # Total corpus frequency per word_id (sum across docs)
    corpus_freq: Dict[int, int] = {}
    for tc in doc_counts:
        for wid, cnt in tc.items():
            corpus_freq[wid] = corpus_freq.get(wid, 0) + cnt

    # TF-IDF: accumulate per-doc scores, then average
    # Smoothed IDF (sklearn formula): log((D+1)/(df+1)) + 1  — never zero, even for D=1
    tfidf_sum: Dict[int, float] = {}
    for tc in doc_counts:
        doc_len = sum(tc.values())
        if doc_len == 0:
            continue
        for wid, cnt in tc.items():
            tf = cnt / doc_len
            idf = math.log((D + 1) / (df[wid] + 1)) + 1
            tfidf_sum[wid] = tfidf_sum.get(wid, 0.0) + tf * idf

    # Build result list sorted by descending mean TF-IDF
    keywords: List[list] = []
    i = 0
    for wid, score_sum in sorted(tfidf_sum.items(), key=lambda x: -x[1]):
        word = id_to_word.get(wid, '')
        if not word:
            continue
        if ignore_numbers and _re_number.match(word):
            continue
        if ignore_strange and _re_strange.search(word):
            continue
        if len(word) < min_chars:
            continue
        mean_tfidf = round(score_sum / D, 6)
        freq = corpus_freq.get(wid, 0)
        i += 1
        keywords.append([i, word, freq, mean_tfidf])
    return keywords

    
    
    
    
    
    
    
    
