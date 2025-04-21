# -*- coding: utf-8 -*-
# Author: jlopes@alumni.usp.br
import os
import numpy as np
import pickle


def load_dict(dict_path):
    """Carrega um dicionário em formato pickle."""
    with open(dict_path, 'rb') as fh:
        return pickle.load(fh)


def keywords2numbers(workspace, corpus_name, keywords, lowercase):
    """Converte palavras-chave em índices numéricos usando dicionários pré-gerados."""
    dict_path = os.path.join(
        workspace, corpus_name, 'data', 'idx',
        'wordslc.pickle' if lowercase else 'words.pickle'
    )
    dict_words = load_dict(dict_path)

    encoded_keywords = {}
    for w, keyness in keywords.items():
        word_ids = dict_words.get(w)
        if word_ids is not None:
            if isinstance(word_ids, int):
                word_ids = (word_ids,)
            else:
                word_ids = tuple(word_ids)
            encoded_keywords[word_ids] = (w, keyness)
        else:
            print(f"Aviso: '{w}' não encontrada no dicionário.")
    return encoded_keywords


def arr_search_indexes(arr, search_w):
    """Busca índices onde uma palavra ou sequência de palavras (até 3 palavras) ocorre."""
    word_len = len(search_w)
    match_indexes = []
    for i in range(len(arr) - word_len + 1):
        if tuple(arr[i:i + word_len, 0]) == search_w:
            match_indexes.append(i)
    return np.array(match_indexes)


def search_node(npy_path, encoded_keywords):
    """Busca palavras-chave nos arquivos numpy e obtém suas posições relativas."""
    files = [f for f in os.listdir(npy_path) if f.endswith('.npy')]
    dict_positions = {}

    for filename in files:
        arr = np.load(os.path.join(npy_path, filename))
        for k, v in encoded_keywords.items():
            ix = arr_search_indexes(arr, k)
            positions = [round((i / len(arr)) * 100, 2) for i in ix]

            dict_positions.setdefault(k, []).extend(positions)

    data = [
        (v[0], len(dict_positions.get(k, [])), dict_positions.get(k, []), v[1])
        for k, v in encoded_keywords.items()
    ]
    return data


def translate(positions):
    """Organiza as posições das palavras por segmentos percentuais do texto."""
    dispersion = []
    dpts = {}
    totals = [0, 0, 0, 0, 0]

    for i, (word, freq, points, keyness) in enumerate(positions, start=1):
        segments = [0, 0, 0, 0, 0]
        dpts[word] = points

        for point in points:
            idx = min(int(point // 20), 4)
            segments[idx] += 1
            totals[idx] += 1

        dispersion.append((i, word, keyness, freq, *segments))

    return (tuple(totals), dpts, dispersion)


def make_keywords_dispersion(workspace, corpus_name, keywords, lowercase):
    """Integra todas as etapas para gerar dispersão das palavras-chave no corpus."""
    encoded_keywords = keywords2numbers(workspace, corpus_name, keywords, lowercase)
    dispersion, dpts, totals = [], {}, ()

    if encoded_keywords:
        positions = search_node(os.path.join(workspace, corpus_name, 'data', 'npy'), encoded_keywords)
        if positions:
            totals, dpts, dispersion = translate(positions)

    return totals, dpts, dispersion
