# -*- coding: utf-8 -*-
"""Regression tests for corpus metadata (info.tab) and source-file filtering."""

import os

import pytest

from kitconc.agent.actions import KitconcActions
from kitconc.kit_corpus import Corpus
from kitconc.kit_util import list_source_files, parse_info_tab, prepare_source_folder

TEXTS = {
    "a.txt": "The new model is working well . The new model is fast .",
    "b.txt": "A new idea is working . We like the idea of the new model .",
}
SQLITE_HEADER = b"SQLite format 3\x00" + b"\x00" * 200


def _write_sources(folder, with_binary=False):
    folder.mkdir()
    for name, text in TEXTS.items():
        (folder / name).write_text(text, encoding="utf-8")
    if with_binary:
        (folder / "index.sqlite").write_bytes(SQLITE_HEADER)
        (folder / "index.sqlite-wal").write_bytes(b"\x37\x7f\x06\x82" + b"\x00" * 64)
    return folder


def test_parse_info_tab_splits_lines_merged_by_older_versions(tmp_path):
    info = tmp_path / "info.tab"
    info.write_text(
        "workspace:\tF:\\ws/\r\ncorpus name:\tJobAds\r\nlanguage:\tenglish\r\n"
        "encoding:\tutf-8Textfiles:\t98\r\nSource:\tF:\\src\r\n\r\n"
        "Tokens:\t300787\r\nTypes:\t5184\r\nType/token:\t1.72",
        encoding="utf-8",
    )
    pairs = dict(parse_info_tab(str(info)))
    assert pairs["encoding"] == "utf-8"
    assert pairs["Textfiles"] == "98"
    assert pairs["Source"] == "F:\\src"
    assert pairs["Type/token"] == "1.72"


def test_list_source_files_skips_binary_and_keeps_utf16_text(tmp_path):
    src = _write_sources(tmp_path / "src", with_binary=True)
    (src / "utf16.txt").write_bytes("ol\u00e1 mundo".encode("utf-16"))
    (src / "Thumbs.db").write_bytes(b"\x00\x01")
    accepted, skipped = list_source_files(str(src))
    assert accepted == ["a.txt", "b.txt", "utf16.txt"]
    assert skipped == ["Thumbs.db", "index.sqlite", "index.sqlite-wal"]


def test_prepare_source_folder_leaves_out_binary_files(tmp_path):
    src = _write_sources(tmp_path / "src", with_binary=True)
    folder, tmp = prepare_source_folder(str(src))
    try:
        assert tmp is not None
        assert sorted(os.listdir(folder)) == sorted(TEXTS)
    finally:
        import shutil

        shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture(scope="module")
def corpus_with_binary_source(tmp_path_factory):
    base = tmp_path_factory.mktemp("ingest")
    src = _write_sources(base / "src", with_binary=True)
    workspace = str(base / "ws") + "/"
    with pytest.warns(UserWarning, match="index.sqlite"):
        Corpus(workspace, "demo", "no-tagging").add_texts(str(src))
    corpus = Corpus(workspace, "demo", "no-tagging")
    corpus.wordlist()  # writes Tokens/Types/Type-token into info.tab
    return corpus, workspace


def test_binary_source_files_are_not_ingested(corpus_with_binary_source):
    corpus, workspace = corpus_with_binary_source
    npy = sorted(os.listdir(workspace + "demo/data/npy"))
    assert npy == [name + ".npy" for name in sorted(TEXTS)]
    dispersion = corpus.dispersion("new")
    assert sorted(dispersion.df["FILENAME"]) == sorted(TEXTS)


def test_info_tab_has_one_field_per_line(corpus_with_binary_source):
    _, workspace = corpus_with_binary_source
    with open(workspace + "demo/info.tab", encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    keys = [line.split("\t", 1)[0] for line in lines]
    assert keys == ["workspace:", "corpus name:", "language:", "encoding:", "Textfiles:", "Source:",
                    "Tokens:", "Types:", "Type/token:"]
    info = KitconcActions(workspace).get_corpus_info("demo")
    assert info["texts"] == len(TEXTS)
    assert info["encoding"] == "utf-8"
    assert info["tokens"] > 0


def test_source_folder_with_only_binary_files_is_rejected(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "only.sqlite").write_bytes(SQLITE_HEADER)
    with pytest.warns(UserWarning):
        with pytest.raises(ValueError, match="no text files"):
            Corpus(str(tmp_path / "ws") + "/", "empty", "no-tagging").add_texts(str(src))
