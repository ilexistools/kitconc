# -*- coding: utf-8 -*-
# Author: jlopes@alumni.usp.br
"""Additional corpus analyses inspired by AntConc 4.

All functions read the file-based corpus index created by kitconc
(``data/npy/*.npy`` arrays with columns word_id, tag_id, sent_id, file_id and
``data/idx/*.pickle`` dictionaries) and never modify it.
"""
import collections
import itertools
import math
import os
import pickle
import random
import re
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

import numpy as np

_PUNCT = re.compile(r'^\W+$')


def _load(path: str):
    with open(path, 'rb') as fh:
        return pickle.load(fh)


def _npy_files(workspace: str, corpus_name: str) -> List[str]:
    npy_path = workspace + corpus_name + '/data/npy/'
    return [npy_path + f for f in os.listdir(npy_path)]


# ---------------------------------------------------------------------------
# Search helpers
# ---------------------------------------------------------------------------

def wildcard_to_regex(query: str) -> str:
    """Converts an AntConc-style wildcard query into kitconc's token regex syntax.

    Each space-separated token is converted independently:
      ``*``           any sequence of characters (``teach*``, ``*ing``)
      ``?``           exactly one character
      ``+``           zero or one character
      ``a|b``         alternatives (``student|pupil``)
      ``[a,b]``       alternatives (``[student,pupil]``)
    Patterns are anchored at both ends, so ``teach`` does not match ``teacher``.
    """
    tokens = []
    for token in query.strip().split():
        alternatives = []
        if token.startswith('[') and token.endswith(']') and len(token) > 2:
            alternatives = [a for a in token[1:-1].split(',') if a]
        else:
            alternatives = [a for a in token.split('|') if a]
        parts = []
        for alt in alternatives:
            pattern = ''
            for ch in alt:
                if ch == '*':
                    pattern += '.*'
                elif ch == '?':
                    pattern += '.'
                elif ch == '+':
                    pattern += '.?'
                else:
                    pattern += re.escape(ch)
            parts.append(pattern)
        if not parts:
            continue
        body = parts[0] if len(parts) == 1 else '(?:' + '|'.join(parts) + ')'
        tokens.append(body + '$')
    return ' '.join(tokens)


def has_wildcards(query: str) -> bool:
    """True when the query uses wildcard syntax (*, ?, +, | or [a,b])."""
    return bool(re.search(r'[*?+|]|\[[^\]]*,', query))


def load_word_set(source, language: Optional[str] = None, kind: str = 'stoplist') -> Set[str]:
    """Loads a stoplist/allowlist.

    source: a list/set/tuple of words; a path to a text file with one word per
    line (only the first tab-separated column is used); or the string
    'default' to load kitconc's bundled ``stoplist_<language>.tab``.
    Words are lowercased.
    """
    if source is None:
        return set()
    if isinstance(source, str):
        if source == 'default':
            if language is None:
                raise ValueError('A language is required to load the default stoplist.')
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', f'{kind}_{language}.tab')
        else:
            path = source
        words = set()
        with open(path, 'r', encoding='utf-8') as fh:
            for line in fh:
                w = line.strip().split('\t')[0].strip()
                if w:
                    words.add(w.lower())
        return words
    return {str(w).strip().lower() for w in source if str(w).strip()}


def filter_by_words(df, column: str, stoplist=None, allowlist=None, language: Optional[str] = None,
                    split_items: bool = False):
    """Removes rows whose item is in the stoplist or not in the allowlist.

    With ``split_items`` (clusters, n-grams), a row is removed when any of its
    words is in the stoplist, and kept only when all words are in the allowlist.
    """
    stop = load_word_set(stoplist, language)
    allow = load_word_set(allowlist, language)
    if not stop and not allow:
        return df

    def keep(item) -> bool:
        words = str(item).lower().split(' ') if split_items else [str(item).lower()]
        if stop and any(w in stop for w in words):
            return False
        if allow and not all(w in allow for w in words):
            return False
        return True

    return df[df[column].map(keep).astype(bool)]


# ---------------------------------------------------------------------------
# KWIC post-processing
# ---------------------------------------------------------------------------

def _match_token(token: str, terms: Sequence, case_sensitive: bool, regexp: bool) -> bool:
    t = token if case_sensitive else token.lower()
    for term in terms:
        if regexp:
            if term.match(t):
                return True
        elif t == term:
            return True
    return False


def context_filter(df, words, left_span: int = 5, right_span: int = 5, mode: str = 'or',
                   exclude: bool = False, case_sensitive: bool = False, regexp: bool = False):
    """Keeps KWIC rows with (or, when ``exclude``, without) context words.

    words: one word or a list of single-token context terms.
    mode: 'or' (any word in the window) or 'and' (all words in the window).
    left_span/right_span: window size in tokens counted from the node.
    """
    if isinstance(words, str):
        words = words.split()
    terms = [w if case_sensitive else w.lower() for w in words if w.strip()]
    if not terms:
        return df
    if regexp:
        terms = [re.compile(t) for t in terms]

    def window(row) -> List[str]:
        left = str(row['LEFT']).split(' ') if str(row['LEFT']) else []
        right = str(row['RIGHT']).split(' ') if str(row['RIGHT']) else []
        return (left[-left_span:] if left_span > 0 else []) + (right[:right_span] if right_span > 0 else [])

    def matches(row) -> bool:
        tokens = window(row)
        found = [any(_match_token(tok, [term], case_sensitive, regexp) for tok in tokens) for term in terms]
        hit = all(found) if mode == 'and' else any(found)
        return not hit if exclude else hit

    if len(df) == 0:
        return df
    return df[df.apply(matches, axis=1).astype(bool)]


def random_sample(df, size: int, seed: Optional[int] = None):
    """Returns a random subset of rows keeping their original order."""
    if size is None or size >= len(df):
        return df
    rng = random.Random(seed)
    idx = sorted(rng.sample(range(len(df)), int(size)))
    return df.iloc[idx]


def _kwic_position(row, position: str) -> str:
    position = position.upper()
    if position in ('N', 'C', 'NODE'):
        return str(row['NODE']).lower()
    side, p = position[0], int(position[1:])
    if side == 'L':
        tokens = str(row['LEFT']).split(' ')
        return tokens[-p].lower() if len(tokens) >= p else ''
    tokens = str(row['RIGHT']).split(' ')
    return tokens[p - 1].lower() if len(tokens) >= p else ''


def kwic_pattern_frequency(df, positions: Sequence[str] = ('R1', 'R2', 'R3'), sort: bool = True):
    """KWIC Pattern Frequency (AntConc's KPF).

    Adds the columns PATTERN (words in the given positions) and KPF (number of
    lines sharing that pattern). When ``sort`` is True, lines are ordered by
    descending KPF and then by pattern.
    """
    df = df.copy()
    positions = [p for p in positions if p]
    df['PATTERN'] = [' '.join(_kwic_position(row, p) for p in positions) for _, row in df.iterrows()] if len(df) else []
    counts = df['PATTERN'].value_counts()
    df['KPF'] = df['PATTERN'].map(counts).astype(int) if len(df) else []
    if sort and len(df):
        df = df.sort_values(['KPF', 'PATTERN'], ascending=[False, True], kind='mergesort')
    return df


# ---------------------------------------------------------------------------
# Per-file frequencies, dispersion and reference corpora
# ---------------------------------------------------------------------------

def word_file_frequencies(workspace: str, corpus_name: str, lowercase: bool = True
                          ) -> Tuple[Dict[str, Dict[int, int]], List[int], List[str]]:
    """Returns ({word: {file_index: freq}}, file_sizes, file_names).

    file_sizes count every token (punctuation included), as kitconc's wordlist does.
    Punctuation-only tokens are not listed.
    """
    dict_words = _load(workspace + corpus_name + '/data/idx/words.pickle')
    npy_path = workspace + corpus_name + '/data/npy/'
    files = sorted(os.listdir(npy_path))
    freqs: Dict[str, Dict[int, int]] = collections.defaultdict(dict)
    sizes = []
    for fi, filename in enumerate(files):
        arr = np.load(npy_path + filename)
        sizes.append(int(arr.shape[0]))
        if arr.shape[0] == 0:
            continue
        ids, counts = np.unique(arr[:, 0], return_counts=True)
        for wid, c in zip(ids.tolist(), counts.tolist()):
            if wid == 0 or wid not in dict_words:
                continue
            w = dict_words[wid].lower() if lowercase else dict_words[wid]
            if _PUNCT.match(w):
                continue
            freqs[w][fi] = freqs[w].get(fi, 0) + c
    names = [os.path.splitext(f)[0] for f in files]
    return dict(freqs), sizes, names


def dispersion_table(workspace: str, corpus_name: str, lowercase: bool = True,
                     words: Optional[Iterable[str]] = None) -> Dict[str, Dict[str, float]]:
    """Dispersion statistics for every word (or the given words) across text files."""
    from kitconc.py_measures import dispersion
    freqs, sizes, _ = word_file_frequencies(workspace, corpus_name, lowercase)
    n_files = len(sizes)
    selected = freqs.keys() if words is None else [w if not lowercase else str(w).lower() for w in words]
    table = {}
    for w in selected:
        per_file = freqs.get(w, {})
        vector = [per_file.get(i, 0) for i in range(n_files)]
        table[w] = dispersion(vector, sizes)
    return table


def corpus_frequency_list(workspace: str, corpus_name: str, lowercase: bool = True
                          ) -> Tuple[int, Dict[str, int], Dict[str, int], int]:
    """Returns (tokens, {word: freq}, {word: range}, number_of_files) for a corpus in the workspace."""
    freqs, sizes, _ = word_file_frequencies(workspace, corpus_name, lowercase)
    freq = {w: sum(d.values()) for w, d in freqs.items()}
    rng = {w: len(d) for w, d in freqs.items()}
    return sum(sizes), freq, rng, len(sizes)


# ---------------------------------------------------------------------------
# Lemmas
# ---------------------------------------------------------------------------

def load_lemma_map(source: str, fmt: str = 'auto') -> Dict[str, str]:
    """Loads a lemma list and returns {form: lemma} (forms lowercased).

    fmt:
      'form-lemma'      one ``form<TAB>lemma`` pair per line (kitconc bundled lists)
      'headword-forms'  ``headword<TAB>form1<TAB>form2...`` (AntConc lemma lists;
                        ``headword -> form1, form2`` is also accepted)
      'auto'            'headword-forms' if any line has more than two tab-separated
                        fields or uses `` -> ``, otherwise 'form-lemma'
    Placeholder lemmas such as spaCy's ``-PRON-`` are ignored (the form is kept).
    """
    with open(source, 'r', encoding='utf-8') as fh:
        lines = [l.rstrip('\r\n') for l in fh if l.strip() and not l.lstrip().startswith('#')]

    def tab_fields(line: str) -> List[str]:
        return [f.strip() for f in line.split('\t') if f.strip()]

    arrow = re.compile(r'\s->\s')

    def headword_fields(line: str) -> List[str]:
        if arrow.search(line):
            head, _, forms = line.partition('->')
            return [head.strip()] + [f.strip() for f in re.split(r'[,\t]', forms) if f.strip()]
        return tab_fields(line)

    placeholder = re.compile(r'^-[A-Z]+-$')
    if fmt == 'auto':
        fmt = 'headword-forms' if any(len(tab_fields(l)) > 2 or arrow.search(l) for l in lines) else 'form-lemma'
    mapping: Dict[str, str] = {}
    for line in lines:
        f = tab_fields(line) if fmt == 'form-lemma' else headword_fields(line)
        if len(f) < 2:
            continue
        if fmt == 'form-lemma':
            if not placeholder.match(f[1]):
                mapping.setdefault(f[0].lower(), f[1].lower())
        elif fmt == 'headword-forms':
            head = f[0].lower()
            mapping.setdefault(head, head)
            for form in f[1:]:
                mapping.setdefault(form.lower(), head)
        else:
            raise ValueError("fmt must be 'auto', 'form-lemma' or 'headword-forms'")
    return mapping


def lemma_frequencies(freqs: Dict[str, Dict[int, int]], lemma_map: Dict[str, str]
                      ) -> Dict[str, Tuple[int, Set[int], collections.Counter]]:
    """Groups per-file word frequencies by lemma: {lemma: (freq, files, forms)}."""
    result: Dict[str, list] = {}
    for word, per_file in freqs.items():
        lemma = lemma_map.get(word.lower(), word.lower())
        entry = result.setdefault(lemma, [0, set(), collections.Counter()])
        total = sum(per_file.values())
        entry[0] += total
        entry[1].update(per_file.keys())
        entry[2][word] += total
    return {k: (v[0], v[1], v[2]) for k, v in result.items()}


# ---------------------------------------------------------------------------
# Clusters with arbitrary size and node position
# ---------------------------------------------------------------------------

def make_clusters_ext(workspace: str, corpus_name: str, node: str, pos: Optional[str], lowercase: bool,
                      size: int, position: str = 'both', case_sensitive: bool = False,
                      regexp: bool = False) -> List[tuple]:
    """Clusters of any size around a (single- or multi-word) node.

    position: 'left' (node starts the cluster), 'right' (node ends the cluster)
    or 'both' (node in any position). Clusters never cross file boundaries.
    Returns rows (N, CLUSTER, FREQUENCY, RANGE, %).
    """
    from kitconc.py_kwic import parse_search, arr_search_indexes
    if position not in ('left', 'right', 'both'):
        raise ValueError("position must be 'left', 'right' or 'both'")
    encoded_node, encoded_pos = parse_search(workspace, corpus_name, node, pos, case_sensitive, regexp)
    if encoded_node is None:
        return []
    node_len = len(encoded_node)
    if size < node_len:
        raise ValueError('Cluster size must be at least the number of words in the search term.')
    dict_words = _load(workspace + corpus_name + '/data/idx/words.pickle')
    files = _npy_files(workspace, corpus_name)
    freq = collections.Counter()
    rng = collections.Counter()
    if position == 'left':
        offsets = [0]
    elif position == 'right':
        offsets = [size - node_len]
    else:
        offsets = list(range(size - node_len, -1, -1))
    for path in files:
        raw = np.load(path)
        if raw.shape[0] == 0:
            continue
        pad = np.zeros((size + 4, raw.shape[1]), dtype=raw.dtype)
        arr = np.concatenate([pad, raw, pad])
        ix = arr_search_indexes(arr, encoded_node, encoded_pos)
        seen = set()
        for i in ix:
            for off in offsets:
                start = int(i) - off
                ids = arr[start:start + size, 0].tolist()
                if 0 in ids:
                    continue
                words = [dict_words[w] for w in ids]
                if lowercase:
                    words = [w.lower() for w in words]
                if any(_PUNCT.match(w) for w in words):
                    continue
                key = ' '.join(words)
                freq[key] += 1
                seen.add(key)
        for key in seen:
            rng[key] += 1
    total_files = len(files)
    rows = []
    for i, (k, v) in enumerate(freq.items(), start=1):
        rows.append((i, k, v, rng[k], (rng[k] / float(total_files)) * 100 if total_files else 0.0))
    return rows


# ---------------------------------------------------------------------------
# N-grams with open slots (p-frames)
# ---------------------------------------------------------------------------

def _entropy(counter: collections.Counter) -> float:
    total = sum(counter.values())
    if total == 0:
        return 0.0
    return -sum((c / total) * math.log2(c / total) for c in counter.values() if c)


def make_pframes(workspace: str, corpus_name: str, size: int = 4, slots=1, lowercase: bool = True,
                 pos: Optional[str] = None) -> List[tuple]:
    """N-grams with open slots (phrase-frames).

    slots: an int (number of open slots, every combination of interior and edge
    positions is generated) or a list of 1-based slot positions (e.g. [2] for
    "the * of"). Rows: (N, P-FRAME, FREQUENCY, RANGE, %, VARIANTS, TTR, ENTROPY, TOP_VARIANTS).
    """
    if size < 2:
        raise ValueError('P-frames need n-grams of size 2 or more.')
    if isinstance(slots, int):
        if not 1 <= slots < size:
            raise ValueError('The number of open slots must be between 1 and size - 1.')
        slot_sets = list(itertools.combinations(range(size), slots))
    else:
        positions = sorted({int(s) - 1 for s in slots})
        if not positions or positions[0] < 0 or positions[-1] >= size or len(positions) >= size:
            raise ValueError('Slot positions must be between 1 and size and leave at least one fixed word.')
        slot_sets = [tuple(positions)]
    encoded_pos = None
    if pos:
        from kitconc.py_ngrams import parse_search as ngram_parse_search
        encoded_pos = ngram_parse_search(workspace, corpus_name, pos)
        if encoded_pos is None:
            return []
        if len(encoded_pos) != size:
            raise ValueError('The POS filter must have one tag per n-gram position.')
    dict_words = _load(workspace + corpus_name + '/data/idx/words.pickle')
    files = _npy_files(workspace, corpus_name)
    frame_freq = collections.Counter()
    frame_range = collections.Counter()
    frame_variants: Dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for path in files:
        arr = np.load(path)
        if arr.shape[0] < size:
            continue
        ids = arr[:, 0]
        tags = arr[:, 1]
        seen = set()
        for start in range(arr.shape[0] - size + 1):
            window = ids[start:start + size].tolist()
            if encoded_pos is not None:
                t = tags[start:start + size].tolist()
                if not all(t[j] in encoded_pos[j] for j in range(size)):
                    continue
            words = [dict_words.get(w, '') for w in window]
            if lowercase:
                words = [w.lower() for w in words]
            if any((not w) or _PUNCT.match(w) for w in words):
                continue
            for slot_set in slot_sets:
                frame = ' '.join('*' if j in slot_set else words[j] for j in range(size))
                filler = ' '.join(words[j] for j in slot_set)
                frame_freq[frame] += 1
                frame_variants[frame][filler] += 1
                seen.add(frame)
        for frame in seen:
            frame_range[frame] += 1
    total_files = len(files)
    rows = []
    for i, (frame, freq) in enumerate(frame_freq.items(), start=1):
        variants = frame_variants[frame]
        top = ', '.join(f'{w} ({c})' for w, c in variants.most_common(5))
        rows.append((i, frame, freq, frame_range[frame],
                     (frame_range[frame] / float(total_files)) * 100 if total_files else 0.0,
                     len(variants), len(variants) / float(freq), _entropy(variants), top))
    return rows
