# -*- coding: utf-8 -*-
"""Tests for kitconc.py_keywords — statistical keyword functions."""
import math

from kitconc.py_keywords import chi_square, ll


class TestChiSquare:
    def test_basic_positive(self):
        """Word more frequent in study corpus → positive chi-square value."""
        result = chi_square(100, 10, 1000, 1000)
        assert result > 0

    def test_symmetry_equal_corpora(self):
        """Same frequency in both corpora → near-zero chi-square."""
        result = chi_square(50, 50, 1000, 1000)
        assert abs(result) < 0.1

    def test_returns_float(self):
        result = chi_square(50, 30, 1000, 1000)
        assert isinstance(result, float)

    def test_rounded_to_two_decimals(self):
        result = chi_square(50, 30, 1000, 1000)
        assert result == round(result, 2)

    def test_high_frequency_word(self):
        """A word with very high study frequency should have large chi-square."""
        result = chi_square(500, 1, 1000, 1000)
        assert result > 100

    def test_zero_denominator_returns_zero(self):
        """If any factor of the denominator is zero, return 0.0 instead of crashing."""
        # c+d = 0 when tk_stdc == freq_stdc and tk_refc == freq_refc
        result = chi_square(1000, 1000, 1000, 1000)
        assert result == 0.0


class TestLL:
    def test_word_overrepresented_in_study(self):
        """Word overrepresented in study corpus → positive LL value."""
        result = ll(100, 10, 1000, 1000)
        assert result > 0

    def test_word_underrepresented_in_study(self):
        """Word underrepresented in study corpus → negative LL value."""
        result = ll(10, 100, 1000, 1000)
        assert result < 0

    def test_symmetry_equal_corpora(self):
        """Same normalised frequency in both corpora → near-zero LL."""
        result = ll(50, 50, 1000, 1000)
        assert abs(result) < 0.1

    def test_returns_float(self):
        result = ll(50, 30, 1000, 1000)
        assert isinstance(result, float)

    def test_rounded_to_two_decimals(self):
        result = ll(50, 30, 1000, 1000)
        assert result == round(result, 2)

    def test_zero_study_frequency(self):
        """Word absent from study corpus → negative LL (word is in reference)."""
        result = ll(0, 100, 1000, 1000)
        assert result <= 0

    def test_different_corpus_sizes(self):
        """Handles corpora of very different sizes without error."""
        result = ll(100, 1000, 500, 100000)
        assert isinstance(result, float)
        assert not math.isnan(result)
        assert not math.isinf(result)
