# -*- coding: utf-8 -*-
"""Tests for the AntConc-inspired features (statistics, search options, new analyses)."""
import math
import os
import zipfile

import pandas as pd
import pytest

from kitconc import py_extras, py_measures
from kitconc.kit_corpus import Corpus
from kitconc.kit_util import prepare_source_folder


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

class TestMeasures:
    def test_two_term_log_likelihood_matches_reference_value(self):
        # Rayson & Garside: 100 in 10,000 vs 50 in 20,000 tokens
        assert round(py_measures.keyness(100, 50, 10000, 20000, 'log-likelihood-2'), 2) == 69.31

    def test_keyness_is_negative_for_underused_words(self):
        assert py_measures.keyness(10, 100, 10000, 20000) < 0
        assert py_measures.keyness(10, 100, 10000, 20000, signed=False) > 0

    def test_log_ratio(self):
        assert py_measures.effect_size(100, 50, 10000, 20000, 'log-ratio') == pytest.approx(2.0)
        # zero reference frequency is smoothed with 0.5
        assert py_measures.effect_size(10, 0, 1000, 1000, 'log-ratio') == pytest.approx(math.log2(10 / 0.5))

    def test_p_value_thresholds(self):
        assert py_measures.p_value_threshold('p<0.05') == 3.84
        assert py_measures.p_value_threshold(0.01) == pytest.approx(6.63, abs=0.01)
        assert py_measures.bonferroni(0.05, 10) == pytest.approx(0.005)

    def test_association_matches_legacy_tscore_and_mi(self):
        from kitconc.py_collocates import mutual_information, tscore
        assert round(py_measures.association(10, 50, 200, 100000, 't-score'), 2) == tscore(10, 50, 200, 100000)
        assert round(py_measures.association(10, 50, 200, 100000, 'mi'), 2) == mutual_information(10, 50, 200, 100000)

    def test_log_dice_maximum_is_14(self):
        assert py_measures.association(10, 10, 10, 1000, 'log-dice') == pytest.approx(14.0)

    def test_dispersion_even_and_uneven(self):
        even = py_measures.dispersion([5, 5, 5, 5], [100, 100, 100, 100])
        assert even['juilland-d'] == pytest.approx(1.0)
        assert even['dp'] == pytest.approx(0.0)
        uneven = py_measures.dispersion([20, 0, 0, 0], [100, 100, 100, 100])
        assert uneven['range'] == 1
        assert uneven['juilland-d'] == pytest.approx(0.0)
        assert uneven['dp'] == pytest.approx(0.75)

    def test_unknown_measure_raises(self):
        with pytest.raises(ValueError):
            py_measures.association(1, 1, 1, 10, 'nope')


# ---------------------------------------------------------------------------
# Search helpers
# ---------------------------------------------------------------------------

class TestSearchHelpers:
    @pytest.mark.parametrize('query, word, expected', [
        ('teach*', 'teacher', True),
        ('teach*', 'reteach', False),
        ('*ing', 'working', True),
        ('colo?r', 'colour', True),
        ('colo?r', 'color', False),
        ('colo+r', 'color', True),
        ('colo+r', 'colour', True),
        ('colo+r', 'colouur', False),
        ('student|pupil', 'pupil', True),
        ('[student,pupil]', 'student', True),
        ('teach', 'teacher', False),
        ('c.t', 'cat', False),
    ])
    def test_wildcards(self, query, word, expected):
        import re
        pattern = py_extras.wildcard_to_regex(query)
        assert (re.match(pattern, word) is not None) is expected

    def test_context_filter_and_exclude(self):
        df = pd.DataFrame({'N': [1, 2, 3], 'LEFT': ['a big', 'the small', 'one'],
                           'NODE': ['cat', 'cat', 'cat'], 'RIGHT': ['sat down', 'ran', 'big dog']})
        assert list(py_extras.context_filter(df, ['big'], 2, 2)['N']) == [1, 3]
        assert list(py_extras.context_filter(df, ['big'], 2, 0)['N']) == [1]
        assert list(py_extras.context_filter(df, ['big'], 2, 2, exclude=True)['N']) == [2]
        assert list(py_extras.context_filter(df, ['big', 'sat'], 2, 2, mode='and')['N']) == [1]

    def test_kwic_pattern_frequency(self):
        df = pd.DataFrame({'N': [1, 2, 3], 'LEFT': ['x', 'y', 'z'], 'NODE': ['go'] * 3,
                           'RIGHT': ['to school', 'home', 'to work']})
        out = py_extras.kwic_pattern_frequency(df, ['R1'])
        assert list(out['PATTERN']) == ['to', 'to', 'home']
        assert list(out['KPF']) == [2, 2, 1]

    def test_filter_by_words_keeps_columns_when_empty(self):
        df = pd.DataFrame({'WORD': ['the'], 'FREQUENCY': [1]})
        out = py_extras.filter_by_words(df, 'WORD', ['the'])
        assert list(out.columns) == ['WORD', 'FREQUENCY'] and len(out) == 0

    def test_lemma_map_formats(self, tmp_path):
        form_lemma = tmp_path / 'fl.tab'
        form_lemma.write_text('is\tbe\nwas\tbe\nit\t-PRON-\n1,000\t1,000\n->\t->\n', encoding='utf-8')
        m = py_extras.load_lemma_map(str(form_lemma))
        assert m['is'] == 'be' and m['was'] == 'be' and 'it' not in m
        headword = tmp_path / 'hw.txt'
        headword.write_text('be\tis\twas\tare\ngo -> went, gone\n', encoding='utf-8')
        m = py_extras.load_lemma_map(str(headword))
        assert m['are'] == 'be' and m['gone'] == 'go' and m['be'] == 'be'


# ---------------------------------------------------------------------------
# Source formats
# ---------------------------------------------------------------------------

def test_prepare_source_folder_converts_documents(tmp_path):
    src = tmp_path / 'src'
    src.mkdir()
    w = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    with zipfile.ZipFile(src / 'a.docx', 'w') as z:
        z.writestr('word/document.xml', f'<w:document xmlns:w="{w}"><w:body><w:p><w:r><w:t>Hello docx</w:t>'
                                        '</w:r></w:p></w:body></w:document>')
    (src / 'b.html').write_text('<html><head><script>x=1</script></head><body><p>Hello &amp; html</p></body></html>',
                                encoding='utf-8')
    (src / 'c.txt').write_text('plain', encoding='utf-8')
    folder, tmp = prepare_source_folder(str(src))
    try:
        assert tmp is not None
        files = sorted(os.listdir(folder))
        assert files == ['a.txt', 'b.txt', 'c.txt']
        assert open(os.path.join(folder, 'a.txt'), encoding='utf-8').read() == 'Hello docx'
        assert open(os.path.join(folder, 'b.txt'), encoding='utf-8').read() == 'Hello & html'
    finally:
        import shutil
        shutil.rmtree(tmp)


def test_prepare_source_folder_plain_text_is_untouched(tmp_path):
    (tmp_path / 'a.txt').write_text('plain', encoding='utf-8')
    folder, tmp = prepare_source_folder(str(tmp_path))
    assert tmp is None


# ---------------------------------------------------------------------------
# Corpus integration (small no-tagging corpora)
# ---------------------------------------------------------------------------

TARGET_TEXTS = {
    't1.txt': 'The new model is working well . The new model is fast .',
    't2.txt': 'A new idea is working . We like the idea of the new model .',
    't3.txt': 'Teachers are teaching new students in the new school .',
}
REFERENCE_TEXTS = {
    'r1.txt': 'The old model is slow . The old house is big .',
    'r2.txt': 'An old idea is there . We like the house .',
}


@pytest.fixture(scope='module')
def corpora(tmp_path_factory):
    base = tmp_path_factory.mktemp('kit')
    for name, texts in (('target', TARGET_TEXTS), ('reference', REFERENCE_TEXTS)):
        src = base / f'src_{name}'
        src.mkdir()
        for filename, text in texts.items():
            (src / filename).write_text(text, encoding='utf-8')
        Corpus(str(base / 'ws'), name, 'no-tagging').add_texts(str(src))
    workspace = str(base / 'ws') + '/'
    return Corpus(workspace, 'target', 'no-tagging'), workspace


class TestCorpusFeatures:
    def test_keywords_with_reference_corpus(self, corpora):
        corpus, _ = corpora
        kw = corpus.keywords(ref_corpus='reference', effect='log-ratio', ignore_strange=False)
        df = kw.df.set_index('WORD')
        assert list(kw.df.columns[:4]) == ['N', 'WORD', 'FREQUENCY', 'KEYNESS']
        assert {'REF_FREQUENCY', 'RANGE', 'REF_RANGE', 'LOG-RATIO'} <= set(kw.df.columns)
        assert df.loc['new', 'KEYNESS'] > 0 and df.loc['new', 'REF_FREQUENCY'] == 0
        assert df.loc['old', 'KEYNESS'] < 0 and df.loc['old', 'FREQUENCY'] == 0

    def test_negative_keywords_and_p_value(self, corpora):
        corpus, _ = corpora
        neg = corpus.keywords(ref_corpus='reference', polarity='negative')
        assert (neg.df.KEYNESS < 0).all() and neg.df.iloc[0]['WORD'] == 'old'
        sig = corpus.keywords(ref_corpus='reference', p_value='p<0.05')
        assert (sig.df.KEYNESS.abs() >= 3.84).all()

    def test_text_dispersion_keyness_requires_reference_corpus(self, corpora):
        corpus, _ = corpora
        with pytest.raises(ValueError):
            corpus.keywords(measure='text-dispersion')
        assert len(corpus.keywords(measure='text-dispersion', ref_corpus='reference').df) > 0

    def test_default_keywords_unchanged_by_effect_column(self, corpora):
        corpus, _ = corpora
        base = corpus.keywords()
        with_effect = corpus.keywords(effect='log-ratio')
        assert list(base.df.columns) == ['N', 'WORD', 'FREQUENCY', 'KEYNESS']
        merged = base.df.merge(with_effect.df, on='WORD')
        assert (merged.KEYNESS_x == merged.KEYNESS_y).all()

    def test_collocates_extra_measures(self, corpora):
        corpus, _ = corpora
        coll = corpus.collocates('new', measure='log-dice', extra_measures=['log-likelihood', 't-score'])
        assert {'LOG-LIKELIHOOD', 'T-SCORE'} <= set(coll.df.columns)
        legacy = corpus.collocates('new').df.set_index('WORD')['ASSOCIATION']
        extra = coll.df.set_index('WORD')['T-SCORE']
        assert (abs(legacy - extra.reindex(legacy.index)) < 0.011).all()

    def test_kwic_options(self, corpora):
        corpus, _ = corpora
        assert set(corpus.kwic('teach*', wildcards=True).df.NODE.str.lower()) == {'teachers', 'teaching'}
        assert len(corpus.kwic('new', context='model', context_span=2).df) == 3
        assert len(corpus.kwic('new', context='model', context_span=2, context_exclude=True).df) == 3
        assert len(corpus.kwic('new', sample=2, seed=1).df) == 2
        kwic = corpus.kwic('new').kpf('R1', None, None)
        assert kwic.df.iloc[0]['PATTERN'] == 'model' and kwic.df.iloc[0]['KPF'] == 3

    def test_clusters_position_and_size(self, corpora):
        corpus, _ = corpora
        left = corpus.clusters('new', size=2, position='left').df
        assert all(c.startswith('new ') for c in left.CLUSTER)
        right = corpus.clusters('new', size=4, position='right').df
        assert all(c.endswith(' new') for c in right.CLUSTER) and len(right) > 0

    def test_pframes(self, corpora):
        corpus, _ = corpora
        df = corpus.pframes(size=3, slots=[2], minfreq=2).df
        row = df[df['P-FRAME'] == 'the * model']
        assert len(row) == 0 or row.iloc[0]['VARIANTS'] >= 2
        frames = corpus.pframes(size=3, slots=[3], minfreq=2, min_variants=1).df
        assert 'the new *' in set(frames['P-FRAME'])

    def test_wordlist_dispersion_and_search(self, corpora):
        corpus, _ = corpora
        wl = corpus.wordlist(dispersion=True)
        row = wl.df.set_index('WORD').loc['new']
        assert row.RANGE == 3 and 0 <= row.DP <= 1
        assert set(corpus.wordlist(search='*ing').df.WORD) == {'working', 'teaching'}
        assert 'the' not in set(corpus.wordlist(stoplist=['the']).df.WORD)

    def test_dispersion_stats_and_no_hits(self, corpora):
        corpus, _ = corpora
        disp = corpus.dispersion('new')
        assert disp.stats['hits'] == 6 and disp.range == 3
        empty = corpus.dispersion('zebra')
        assert len(empty.df) == 0 and empty.stats['hits'] == 0

    def test_lemmalist_and_fileview(self, corpora, tmp_path):
        corpus, _ = corpora
        lemmas = tmp_path / 'lemmas.txt'
        lemmas.write_text('teach\tteachers\tteaching\n', encoding='utf-8')
        df = corpus.lemmalist(lemma_file=str(lemmas)).df.set_index('LEMMA')
        assert df.loc['teach', 'FREQUENCY'] == 2
        view = corpus.fileview('t1.txt', 'new')
        assert view.hits == 2 and '[[new]]' in view.text

    def test_wordcloud(self, corpora, tmp_path):
        corpus, _ = corpora
        target = tmp_path / 'cloud.png'
        image = corpus.wordcloud(filename=str(target), width=400, height=300)
        assert target.exists() and image.size == (400, 300)

    def test_wordlist_case_sensitive_no_longer_fails(self, corpora):
        corpus, _ = corpora
        assert len(corpus.wordlist(lowercase=False).df) > 0
