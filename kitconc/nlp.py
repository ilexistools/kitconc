# -*- coding: utf-8 -*-
"""Small, dependency-free NLP primitives used by Kitconc.

The corpus pipeline only needs sentence tokenization, word tokenization and a
backoff unigram/bigram tagger.  Keeping those contracts here avoids loading
third-party model classes when a corpus is processed.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import re
from typing import Iterable, Sequence


class SentenceTokenizer:
    """Rule-based sentence tokenizer suitable for corpus preprocessing."""

    _boundary = re.compile(r"(?<=[.!?])(?:[\"'\u00bb\u201d\u2019\u005d)]*)\s+|\r?\n+")

    def tokenize(self, text: str) -> list[str]:
        return [part.strip() for part in self._boundary.split(text) if part.strip()]


class WordTokenizer:
    """Unicode-aware tokenizer preserving punctuation as individual tokens."""

    _token = re.compile(r"\w+(?:['\u2019]\w+)*|[^\w\s]", re.UNICODE)

    def __init__(self, pattern: str | None = None):
        self._token = re.compile(pattern, re.UNICODE) if pattern else self._token

    def tokenize(self, text: str) -> list[str]:
        return self._token.findall(text)


class BigramTagger:
    """Unigram/bigram backoff tagger with a stable, pickleable data model."""

    def __init__(self, bigram: dict[tuple[str | None, str], str] | None = None,
                 unigram: dict[str, str] | None = None, default: str = "NN",
                 affix: dict[str, str] | None = None):
        self.bigram = bigram or {}
        self.unigram = unigram or {}
        self.default = default
        self.affix = affix or {}

    @classmethod
    def train(cls, tagged_sentences: Iterable[Sequence[tuple[str, str]]]) -> "BigramTagger":
        unigram_counts: dict[str, Counter[str]] = defaultdict(Counter)
        bigram_counts: dict[tuple[str | None, str], Counter[str]] = defaultdict(Counter)
        tag_counts: Counter[str] = Counter()
        for sentence in tagged_sentences:
            previous: str | None = None
            for word, tag in sentence:
                unigram_counts[word][tag] += 1
                bigram_counts[(previous, word)][tag] += 1
                tag_counts[tag] += 1
                previous = tag
        default = tag_counts.most_common(1)[0][0] if tag_counts else "NN"
        return cls(
            bigram={key: values.most_common(1)[0][0] for key, values in bigram_counts.items()},
            unigram={key: values.most_common(1)[0][0] for key, values in unigram_counts.items()},
            default=default,
        )

    def tag(self, tokens: Sequence[str]) -> list[tuple[str, str]]:
        result: list[tuple[str, str]] = []
        previous: str | None = None
        for token in tokens:
            tag = self.bigram.get((previous, token), self.unigram.get(token))
            if tag is None:
                affix = getattr(self, "affix", {})
                for suffix in sorted(affix, key=len, reverse=True):
                    if token.endswith(suffix):
                        tag = affix[suffix]
                        break
            if tag is None:
                tag = self.default
            result.append((token, tag))
            previous = tag
        return result

    def evaluate(self, tagged_sentences: Iterable[Sequence[tuple[str, str]]]) -> float:
        total = correct = 0
        for sentence in tagged_sentences:
            predicted = self.tag([word for word, _ in sentence])
            for (_, expected), (_, actual) in zip(sentence, predicted):
                total += 1
                correct += expected == actual
        return correct / total if total else 0.0
