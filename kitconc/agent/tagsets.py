# -*- coding: utf-8 -*-
"""Tagset-agnostic part-of-speech categories.

Kitconc corpora can carry very different tagsets: the built-in English tagger (Brown, with suffixes
such as ``NN-TL``), the built-in Portuguese tagger (Mac-Morpho style: ``N``, ``PREP+ART``), spaCy
(Universal POS: ``NOUN``, ``ADP``), pre-tagged texts or user-trained models (anything). This module
detects the tagset family from the tags present in a corpus and maps each raw tag to a coarse
Universal-style category, so that term patterns such as ``ADJ NOUN`` work on every corpus. Unknown
tags map to ``X`` and can be overridden with an explicit ``tag_map``.
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field

CATEGORIES = ("NOUN", "PROPN", "ADJ", "VERB", "ADV", "ADP", "DET", "PRON", "NUM", "CONJ", "PART",
              "PUNCT", "X")

CATEGORY_DESCRIPTIONS = {
    "NOUN": "common noun",
    "PROPN": "proper noun",
    "ADJ": "adjective (including ordinals in some tagsets)",
    "VERB": "verb or auxiliary",
    "ADV": "adverb",
    "ADP": "preposition/postposition, including contractions such as 'do', 'da' (PREP+ART)",
    "DET": "determiner or article",
    "PRON": "pronoun",
    "NUM": "number",
    "CONJ": "coordinating or subordinating conjunction",
    "PART": "particle (e.g. infinitival 'to', possessive marker)",
    "PUNCT": "punctuation or symbol",
    "X": "other / unknown / untagged",
}

_UNIVERSAL = {
    "NOUN": "NOUN", "PROPN": "PROPN", "ADJ": "ADJ", "VERB": "VERB", "AUX": "VERB", "ADV": "ADV",
    "ADP": "ADP", "DET": "DET", "PRON": "PRON", "NUM": "NUM", "CCONJ": "CONJ", "SCONJ": "CONJ",
    "CONJ": "CONJ", "PART": "PART", "PUNCT": "PUNCT", "SYM": "PUNCT", "INTJ": "X", "X": "X", "SPACE": "PUNCT",
}

# Mac-Morpho (built-in Portuguese tagger) and close variants.
_MACMORPHO = [
    ("NPROP", "PROPN"), ("N", "NOUN"), ("ADJ", "ADJ"), ("VAUX", "VERB"), ("V", "VERB"), ("PCP", "VERB"),
    ("ADV", "ADV"), ("PREP", "ADP"), ("ART", "DET"), ("PROADJ", "DET"), ("PROSUB", "PRON"),
    ("PROPESS", "PRON"), ("PRO-KS", "PRON"), ("PRO", "PRON"), ("NUM", "NUM"), ("KC", "CONJ"),
    ("KS", "CONJ"), ("PDEN", "ADV"), ("CUR", "NUM"), ("PU", "PUNCT"), ("IN", "X"),
]

# Penn Treebank and Brown share most prefixes. Order matters (longest/most specific first).
_PTB_BROWN = [
    ("NNP", "PROPN"), ("NP", "PROPN"), ("NN", "NOUN"), ("NR", "NOUN"), ("JJ", "ADJ"), ("OD", "ADJ"),
    ("VB", "VERB"), ("MD", "VERB"), ("BE", "VERB"), ("HV", "VERB"), ("DO", "VERB"),
    ("WRB", "ADV"), ("RB", "ADV"), ("QL", "ADV"), ("RP", "PART"), ("WDT", "DET"), ("PDT", "DET"),
    ("DT", "DET"), ("AT", "DET"), ("AB", "DET"), ("AP", "DET"), ("WP", "PRON"), ("PRP", "PRON"),
    ("PP", "PRON"), ("PN", "PRON"), ("EX", "PRON"), ("CD", "NUM"), ("CC", "CONJ"), ("CS", "CONJ"),
    ("IN", "ADP"), ("TO", "PART"), ("POS", "PART"), ("UH", "X"), ("FW", "X"), ("LS", "X"), ("SYM", "PUNCT"),
]

# Generic fallbacks for other tagsets (e.g. German STTS, other trained models).
_GENERIC = [
    ("PROPN", "PROPN"), ("NE", "PROPN"), ("NOUN", "NOUN"), ("NN", "NOUN"), ("ADJ", "ADJ"),
    ("APPR", "ADP"), ("APPO", "ADP"), ("PREP", "ADP"), ("ART", "DET"), ("DET", "DET"), ("PRON", "PRON"),
    ("PRO", "PRON"), ("ADV", "ADV"), ("VERB", "VERB"), ("AUX", "VERB"), ("V", "VERB"), ("CARD", "NUM"),
    ("NUM", "NUM"), ("KON", "CONJ"), ("CONJ", "CONJ"), ("PART", "PART"), ("PTK", "PART"), ("N", "NOUN"),
]

_PUNCT_RE = re.compile(r"^[^\w]+$|^\$")


def _base_tag(tag: str) -> str:
    """Strips decorations: Brown suffixes (NN-TL, JJ-HL), FW- prefixes, '+' compounds and '$'."""
    if _PUNCT_RE.match(tag):
        return tag
    base = tag
    if base.startswith("FW-") and len(base) > 3:
        base = base[3:]
    base = base.split("+", 1)[0]
    if "-" in base and base not in {"PRO-KS"} and not base.startswith("-"):
        head = base.split("-", 1)[0]
        if head:
            base = head
    return base.rstrip("$*") or tag


def detect_family(tags) -> str:
    """Guesses the tagset family from the raw tags of a corpus."""
    tags = {t for t in tags if t}
    if not tags or tags <= {"*"}:
        return "none"
    bases = {_base_tag(t) for t in tags}
    if len(bases & set(_UNIVERSAL)) >= max(3, len(bases) // 2):
        return "universal"
    if bases & {"PREP", "ART", "KC", "KS", "PU", "NPROP", "PROADJ", "PROPESS"}:
        return "macmorpho"
    if bases & {"NN", "NNS", "JJ", "IN", "AT", "DT", "VB", "VBD", "NP", "NNP"}:
        return "ptb_brown"
    return "unknown"


def _by_prefix(base: str, rules) -> str | None:
    for prefix, category in rules:
        if base == prefix or base.startswith(prefix):
            return category
    return None


def categorize(tag: str, family: str) -> str:
    """Maps one raw tag to a coarse category for the given family."""
    if tag in ("", "*"):
        return "X"
    if _PUNCT_RE.match(tag):
        return "PUNCT"
    base = _base_tag(tag)
    if family == "universal":
        return _UNIVERSAL.get(base.upper(), "X")
    if family == "macmorpho":
        for name, category in _MACMORPHO:
            if base == name:
                return category
        return _by_prefix(base, _MACMORPHO) or "X"
    if family == "ptb_brown":
        return _by_prefix(base, _PTB_BROWN) or "X"
    if family == "none":
        return "X"
    return _UNIVERSAL.get(base.upper()) or _by_prefix(base, _GENERIC) or "X"


@dataclass
class TagMapping:
    family: str
    categories: dict[str, str] = field(default_factory=dict)

    def category(self, tag: str) -> str:
        return self.categories.get(tag, "X")


def build_mapping(tags, overrides: dict[str, str] | None = None) -> TagMapping:
    """Builds the raw tag -> category mapping. ``overrides`` keys may use glob patterns (``NN*``)."""
    tags = list(tags)
    family = detect_family(tags)
    categories = {tag: categorize(tag, family) for tag in tags}
    for pattern, category in (overrides or {}).items():
        category = category.upper()
        if category not in CATEGORIES:
            raise ValueError(f"Unknown category '{category}' in tag_map. Use one of {', '.join(CATEGORIES)}.")
        for tag in tags:
            if tag == pattern or fnmatch.fnmatchcase(tag, pattern):
                categories[tag] = category
    return TagMapping(family, categories)


# ---------------------------------------------------------------------------
# Token patterns
# ---------------------------------------------------------------------------

HEAD_INITIAL_LANGUAGES = {"portuguese", "spanish", "french", "italian", "catalan", "galician", "romanian"}

TERM_PATTERNS = {
    "head-final": ["NOUN", "ADJ NOUN", "NOUN NOUN", "ADJ NOUN NOUN", "NOUN NOUN NOUN", "ADJ ADJ NOUN",
                   "NOUN ADP NOUN"],
    "head-initial": ["NOUN", "NOUN ADJ", "NOUN ADP NOUN", "NOUN ADJ ADJ", "ADJ NOUN", "NOUN ADP NOUN ADJ",
                     "NOUN ADJ ADP NOUN"],
}


def default_pattern_set(language: str) -> str:
    return "head-initial" if (language or "").lower() in HEAD_INITIAL_LANGUAGES else "head-final"


@dataclass(frozen=True)
class Slot:
    """One position of a token pattern: a set of alternatives."""

    categories: frozenset[str]
    raw_tags: tuple[str, ...]
    words: frozenset[str]
    any_word: bool

    def matches(self, word: str, tag: str, category: str) -> bool:
        if self.any_word and category != "PUNCT":
            return True
        if category in self.categories:
            return True
        if self.words and word.lower() in self.words:
            return True
        return any(fnmatch.fnmatchcase(tag, raw) for raw in self.raw_tags)


def parse_pattern(pattern: str) -> list[Slot]:
    """Parses a token pattern such as ``"ADJ|NOUN NOUN"``, ``"NOUN word:of NOUN"`` or ``"tag:NN* NOUN"``.

    Each space-separated element is one token; ``|`` separates alternatives inside an element.
    Alternatives are a category name, ``tag:<raw tag or glob>``, ``word:<literal word>`` or ``*``
    (any non-punctuation token).
    """
    slots: list[Slot] = []
    elements = pattern.split()
    if not elements:
        raise ValueError("Empty pattern.")
    for element in elements:
        categories, raw_tags, words, any_word = set(), [], set(), False
        for alternative in element.split("|"):
            if not alternative:
                continue
            if alternative == "*":
                any_word = True
            elif alternative.lower().startswith("tag:"):
                raw_tags.append(alternative[4:])
            elif alternative.lower().startswith("word:"):
                words.add(alternative[5:].lower())
            elif alternative.upper() in CATEGORIES:
                categories.add(alternative.upper())
            else:
                raise ValueError(
                    f"Unknown pattern element '{alternative}' in '{pattern}'. Use a category "
                    f"({', '.join(CATEGORIES)}), tag:<raw>, word:<word> or *."
                )
        slots.append(Slot(frozenset(categories), tuple(raw_tags), frozenset(words), any_word))
    return slots
