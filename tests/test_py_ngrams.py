# -*- coding: utf-8 -*-
"""Tests for kitconc.py_ngrams — n-gram counting functions."""
import collections
import numpy as np
import pytest

from kitconc.py_ngrams import unigrams, bigrams, trigrams


class TestUnigrams:
    def test_counts_all_words_without_pos_filter(self, flat_array):
        """Without POS filter, every word in the array is counted."""
        counter = unigrams(flat_array, encoded_pos=None)
        assert isinstance(counter, collections.Counter)
        # flat_array has 6 tokens: IDs 1,2,3,4,6,5
        assert sum(counter.values()) == 6

    def test_word_id_frequency(self, flat_array):
        """Word ID 1 appears once → count is 1."""
        counter = unigrams(flat_array, encoded_pos=None)
        assert counter[1] == 1

    def test_counts_with_pos_filter(self, tagged_array):
        """With POS filter matching tag 11 (NN), only NN tokens are counted."""
        # Tag IDs for NN is 11; encode as numpy arrays matching the format
        encoded_pos = [np.array(11)]
        counter = unigrams(tagged_array, encoded_pos=encoded_pos)
        # tagged_array has NN tokens at rows 1 (cat=2) and 5 (mat=5)
        assert sum(counter.values()) == 2

    def test_returns_counter(self, flat_array):
        counter = unigrams(flat_array, encoded_pos=None)
        assert isinstance(counter, collections.Counter)


class TestBigrams:
    def test_returns_counter(self, flat_array):
        """Without POS filter, bigrams() expects a (n,1) word-ID array."""
        counter = bigrams(flat_array, encoded_pos=None)
        assert isinstance(counter, collections.Counter)

    def test_bigram_count_unfiltered(self, flat_array):
        """Without POS filter, bigrams are counted from successive word IDs."""
        counter = bigrams(flat_array, encoded_pos=None)
        # 6 tokens → 5 bigrams
        assert sum(counter.values()) == 5

    def test_specific_bigram(self, flat_array):
        """First bigram (1,2) = 'the cat' should appear once."""
        counter = bigrams(flat_array, encoded_pos=None)
        assert counter[(1, 2)] == 1


class TestTrigrams:
    def test_returns_counter(self, flat_array):
        """Without POS filter, trigrams() expects a (n,1) word-ID array."""
        counter = trigrams(flat_array, encoded_pos=None)
        assert isinstance(counter, collections.Counter)

    def test_trigram_count_unfiltered(self, flat_array):
        """Without POS filter, trigrams are counted from successive word IDs."""
        counter = trigrams(flat_array, encoded_pos=None)
        # 6 tokens → 4 trigrams
        assert sum(counter.values()) == 4

    def test_specific_trigram(self, flat_array):
        """First trigram (1,2,3) = 'the cat sat' should appear once."""
        counter = trigrams(flat_array, encoded_pos=None)
        assert counter[(1, 2, 3)] == 1

    def test_no_trigrams_for_short_array(self):
        """Array with only 2 elements produces no trigrams."""
        arr = np.array([[1], [2]], dtype=np.int32)
        counter = trigrams(arr, encoded_pos=None)
        assert sum(counter.values()) == 0
