# -*- coding: utf-8 -*-
"""Shared pytest fixtures for kitconc test suite."""
import os
import pickle
import tempfile

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Word/tag dictionaries
# ---------------------------------------------------------------------------

@pytest.fixture
def word_dict():
    """Maps integer IDs → word strings (simulates words.pickle)."""
    return {
        1: "the", 2: "cat", 3: "sat", 4: "on",
        5: "mat", 6: "a", 7: "dog", 8: "ran",
    }


@pytest.fixture
def tag_dict():
    """Maps integer IDs → POS tag strings (simulates tags.pickle)."""
    return {
        10: "DT", 11: "NN", 12: "VBD", 13: "IN",
    }


# ---------------------------------------------------------------------------
# NumPy arrays
# ---------------------------------------------------------------------------

@pytest.fixture
def tagged_array():
    """2-column array (word_id, tag_id) — used by bigrams/trigrams with POS filter."""
    data = np.array([
        [1, 10],  # the  DT
        [2, 11],  # cat  NN
        [3, 12],  # sat  VBD
        [4, 13],  # on   IN
        [6, 10],  # a    DT
        [5, 11],  # mat  NN
    ], dtype=np.int32)
    return data


@pytest.fixture
def flat_array():
    """1-column view of word IDs — used by unigrams without POS filter."""
    data = np.array([[1], [2], [3], [4], [6], [5]], dtype=np.int32)
    return data


# ---------------------------------------------------------------------------
# Temporary npy directory (for count_words)
# ---------------------------------------------------------------------------

@pytest.fixture
def npy_dir(word_dict, tmp_path):
    """Creates a temp directory with two .npy files mimicking corpus index."""
    npy_path = tmp_path / "npy"
    npy_path.mkdir()

    # File 1: "the cat sat"
    arr1 = np.array([[1, 10], [2, 11], [3, 12]], dtype=np.int32)
    np.save(str(npy_path / "text1.npy"), arr1)

    # File 2: "the dog ran"
    arr2 = np.array([[1, 10], [7, 11], [8, 12]], dtype=np.int32)
    np.save(str(npy_path / "text2.npy"), arr2)

    return str(npy_path) + "/"


# ---------------------------------------------------------------------------
# Temporary workspace structure (for make_wordlist integration tests)
# ---------------------------------------------------------------------------

@pytest.fixture
def workspace(tmp_path, word_dict):
    """Creates a minimal corpus workspace directory structure with pre-built index."""
    corpus = "test_corpus"
    base = tmp_path / corpus
    idx = base / "data" / "idx"
    npy = base / "data" / "npy"
    idx.mkdir(parents=True)
    npy.mkdir(parents=True)
    (base / "output").mkdir()

    # Write words.pickle
    with open(str(idx / "words.pickle"), "wb") as fh:
        pickle.dump(word_dict, fh)

    # Write a npy corpus file: "the cat the dog the"
    arr = np.array([[1, 10], [2, 11], [1, 10], [7, 11], [1, 10]], dtype=np.int32)
    np.save(str(npy / "text1.npy"), arr)

    # Write minimal info.tab
    (base / "info.tab").write_text(
        "Corpus name:\t%s\nLanguage:\tenglish\nTextfiles:\t1\n" % corpus,
        encoding="utf-8",
    )

    return str(tmp_path) + "/", corpus
