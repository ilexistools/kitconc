from __future__ import annotations

import subprocess
import zipfile

import pytest

from kitconc.archive import import_corpus_zip
from kitconc.export_corpus import export
from kitconc.kit_cmd import Kit
from kitconc.kit_corpus import Corpus, Corpora, _run_pipeline


def test_pipeline_timeout_names_failed_stage_and_keeps_cause():
    import sys

    with pytest.raises(RuntimeError, match="tagging timed out") as caught:
        _run_pipeline([sys.executable, "-c", "import time; time.sleep(10)"], "tagging", timeout=0.1)
    assert isinstance(caught.value.__cause__, subprocess.TimeoutExpired)


def test_pipeline_child_receives_eof_on_stdin():
    import sys

    result = _run_pipeline([sys.executable, "-c", "import sys; print(repr(sys.stdin.read()))"],
                           "stdin isolation", timeout=10)
    assert result.stdout.strip() == "''"


def test_command_parser_keeps_quoted_windows_path_spaces():
    args = Kit().parse_arg('demo "C:\\My Texts\\área" english --tagged False')
    assert args == ["demo", "C:\\My Texts\\área", "english", "--tagged", "False"]


def test_corpora_create_accepts_source_path_with_spaces(tmp_path, monkeypatch):
    source = tmp_path / "Meus Textos" / "área"
    source.mkdir(parents=True)
    (source / "one.txt").write_text("hello", encoding="utf-8")
    monkeypatch.setattr(Corpus, "add_texts", lambda self, *_args, **_kwargs: None)

    corpus = Corpora(tmp_path / "workspace").create("demo", "english", source)

    assert corpus.corpus_name == "demo"
    assert (tmp_path / "workspace" / "demo" / "info.tab").is_file()


def test_corpora_create_rejects_existing_or_unsafe_names_without_changes(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    existing = workspace / "demo"
    existing.mkdir()
    (existing / "keep.txt").write_text("keep", encoding="utf-8")

    corpora = Corpora(workspace)
    with pytest.raises(FileExistsError):
        corpora.create("demo", "english", source)
    with pytest.raises(ValueError):
        corpora.create("..", "english", source)

    assert (existing / "keep.txt").read_text(encoding="utf-8") == "keep"
    assert sorted(path.name for path in workspace.iterdir()) == ["demo"]


def test_pipeline_failure_restores_indexes_and_does_not_record_success(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    corpus = Corpus(str(workspace), "demo", "english")
    info_path = workspace / "demo" / "info.tab"
    original_info = info_path.read_bytes()
    source = tmp_path / "source"
    source.mkdir()
    (source / "one.txt").write_text("text", encoding="utf-8")

    def fail_pipeline(_command, stage):
        raise RuntimeError(f"{stage} failed")

    monkeypatch.setattr("kitconc.kit_corpus._run_pipeline", fail_pipeline)
    with pytest.raises(RuntimeError, match="tagging failed"):
        corpus.add_texts(source)

    assert info_path.read_bytes() == original_info
    assert not list((workspace / "demo" / "data").glob("tmp*/*"))
    assert not list(workspace.glob(".kitconc-data-backup-*"))


def test_run_pipeline_reports_stage_and_process_error(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 2, "", "bad input"),
    )
    with pytest.raises(RuntimeError, match="tagging failed.*bad input"):
        _run_pipeline(["python", "tagging.py"], "tagging")


def test_export_and_import_round_trip_legacy_corpus(tmp_path):
    workspace = tmp_path / "source-workspace"
    corpus = workspace / "demo"
    (corpus / "output").mkdir(parents=True)
    (corpus / "info.tab").write_text("corpus name:\tdemo\nlanguage:\tenglish\n", encoding="utf-8")
    (corpus / "data.txt").write_text("preserve me", encoding="utf-8")
    (corpus / "output" / "old.xlsx").write_bytes(b"excluded as before")
    destination = tmp_path / "archives"
    destination.mkdir()

    archive_path = export(workspace, "demo", destination)
    imported_path = import_corpus_zip(archive_path, tmp_path / "restored")

    assert (imported_path / "data.txt").read_text(encoding="utf-8") == "preserve me"
    assert not (imported_path / "output" / "old.xlsx").exists()
    assert not (corpus / "output" / "read_me.txt").exists()


def test_import_rejects_unsafe_zip_and_preserves_workspace(tmp_path):
    archive_path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("demo/info.tab", "language:\tenglish\n")
        archive.writestr("demo/../../outside.txt", "no")
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(ValueError, match="unsafe path"):
        import_corpus_zip(archive_path, workspace)

    assert list(workspace.iterdir()) == []
    assert not (tmp_path / "outside.txt").exists()


def test_import_rejects_corpus_name_collision_without_overwrite(tmp_path):
    archive_path = tmp_path / "demo.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("demo/info.tab", "language:\tenglish\n")
        archive.writestr("demo/data.txt", "incoming")
    workspace = tmp_path / "workspace"
    existing = workspace / "demo"
    existing.mkdir(parents=True)
    (existing / "data.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError):
        import_corpus_zip(archive_path, workspace)

    assert (existing / "data.txt").read_text(encoding="utf-8") == "keep"
    assert len(list(workspace.iterdir())) == 1
