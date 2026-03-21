# -*- coding: utf-8 -*-
"""Tests for kitconc.py_wordlist — word frequency list generation."""
import numpy as np
import pytest

from kitconc.py_wordlist import count_words


class TestCountWords:
    def test_returns_dict(self, npy_dir):
        result = count_words(npy_dir)
        assert isinstance(result, dict)

    def test_word_id_1_appears_twice(self, npy_dir):
        """Word ID 1 ('the') appears in both text1 and text2 → total count 2."""
        result = count_words(npy_dir)
        assert result[1] == 2

    def test_all_word_ids_present(self, npy_dir):
        """All unique word IDs across both npy files are in the result."""
        result = count_words(npy_dir)
        # text1: [1,2,3], text2: [1,7,8]
        for wid in [1, 2, 3, 7, 8]:
            assert wid in result

    def test_unique_word_counts(self, npy_dir):
        """Words appearing only once have count 1."""
        result = count_words(npy_dir)
        # IDs 2,3,7,8 appear in only one file
        assert result[2] == 1
        assert result[3] == 1
        assert result[7] == 1
        assert result[8] == 1

    def test_empty_dir_returns_empty_dict(self, tmp_path):
        """Empty npy directory → empty counter dict."""
        npy_path = tmp_path / "empty_npy"
        npy_path.mkdir()
        result = count_words(str(npy_path) + "/")
        assert result == {}

    def test_total_token_count(self, npy_dir):
        """Total tokens across all files matches sum of all counts."""
        result = count_words(npy_dir)
        # text1 has 3 tokens, text2 has 3 tokens → 6 total
        assert sum(result.values()) == 6
