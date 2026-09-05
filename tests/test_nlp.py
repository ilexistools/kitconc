from kitconc.nlp import BigramTagger, SentenceTokenizer, WordTokenizer


def test_sentence_tokenizer_splits_punctuation_and_newlines():
    tokenizer = SentenceTokenizer()
    assert tokenizer.tokenize("First sentence. Second!\nThird?") == [
        "First sentence.",
        "Second!",
        "Third?",
    ]


def test_word_tokenizer_preserves_punctuation():
    assert WordTokenizer().tokenize("Olá, mundo!") == ["Olá", ",", "mundo", "!"]


def test_bigram_tagger_uses_bigram_then_unigram_then_default():
    tagger = BigramTagger.train([
        [("the", "DT"), ("cat", "NN")],
        [("the", "DT"), ("runs", "VB")],
    ])
    assert tagger.tag(["the", "cat"]) == [("the", "DT"), ("cat", "NN")]
    assert tagger.tag(["unknown"]) == [("unknown", "DT")]
