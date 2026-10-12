# -*- coding: utf-8 -*-
"""Tests for the kitconc-tool CLI and the bundled agent skill (kitconc-skill)."""

import io
import json
import re

import pytest

from kitconc.agent import skill_installer, tool_cli
from kitconc.agent.tools import TOOL_SPECS
from kitconc.kit_corpus import Corpus


@pytest.fixture(scope="module")
def workspace(tmp_path_factory):
    base = tmp_path_factory.mktemp("cli")
    src = base / "src"
    src.mkdir()
    (src / "a.txt").write_text("Corpus tools count words . Corpus tools matter .", encoding="utf-8")
    (src / "b.txt").write_text("Words in corpus tools are counted .", encoding="utf-8")
    Corpus(str(base / "ws"), "demo", "no-tagging").add_texts(str(src))
    return str(base / "ws")


def _run(capsys, *argv):
    code = tool_cli.main(list(argv))
    return code, json.loads(capsys.readouterr().out)


def test_cli_lists_tools_without_job_start(capsys):
    code, payload = _run(capsys, "--list")
    names = {t["tool"] for t in payload["tools"]}
    assert code == 0 and "analyze_kwic" in names and "job_start" not in names
    assert all(t["summary"] for t in payload["tools"])


def test_cli_runs_tools_and_reuses_results(capsys, workspace):
    code, wl = _run(capsys, "--workspace", workspace, "analyze_wordlist", '{"corpus": "demo", "limit": 2}')
    assert code == 0 and wl["returned"] == 2
    code, page = _run(capsys, "--workspace", workspace, "result_page", json.dumps({"result_id": wl["result_id"]}))
    assert code == 0 and page["total"] == wl["total"]


def test_cli_reads_arguments_from_stdin(capsys, workspace, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO('{"name": "corpus-qa", "params": {"corpus": "demo"}}'))
    code, out = _run(capsys, "--workspace", workspace, "recipe_run", "-")
    assert code == 0 and out["recipe"] == "corpus-qa"


@pytest.mark.parametrize("argv, error_code", [
    (["analyze_kwic", '{"corpus": "nope", "node": "x"}'], "CORPUS_NOT_FOUND"),
    (["no_such_tool"], "NOT_FOUND"),
    (["job_start", '{"recipe": "corpus-qa"}'], "INVALID_ARGUMENT"),
    (["analyze_kwic", "not json"], "INVALID_ARGUMENT"),
    (["analyze_kwic", '{"corpus": "demo"}'], "INVALID_ARGUMENT"),
])
def test_cli_errors_are_structured(capsys, workspace, argv, error_code):
    code, out = _run(capsys, "--workspace", workspace, *argv)
    assert code == 1 and out["error"]["code"] == error_code


def test_skill_front_matter_and_references():
    text = (skill_installer.SKILL_SOURCE / "SKILL.md").read_text(encoding="utf-8")
    front = text.split("---")[1]
    name = re.search(r"^name: (.+)$", front, re.M).group(1).strip()
    description = re.search(r"^description: (.+)$", front, re.M).group(1).strip()
    assert name == skill_installer.SKILL_SOURCE.name == "kitconc"
    assert re.fullmatch(r"[a-z0-9-]{1,64}", name) and 50 < len(description) <= 1024
    for ref in re.findall(r"`(references/[\w.-]+\.md)`", text):
        assert (skill_installer.SKILL_SOURCE / ref).is_file(), ref
    tools = {spec.name for spec in TOOL_SPECS}
    mentioned = set(re.findall(r"`([a-z]+_[a-z_]+)`", text)) & {n for n in tools}
    assert {"workspace_info", "recipe_run", "result_filter", "corpus_qa"} <= mentioned
    assert "antconc" not in text.lower()


def test_skill_installs_for_claude_and_codex(tmp_path, monkeypatch):
    monkeypatch.setattr(skill_installer, "TARGETS", {
        "claude": {"user": tmp_path / "home" / ".claude" / "skills", "project": tmp_path / "p" / ".claude" / "skills"},
        "codex": {"user": tmp_path / "home" / ".agents" / "skills", "project": tmp_path / "p" / ".agents" / "skills"},
    })
    assert skill_installer.main(["install"]) == 0
    for root in (".claude", ".agents"):
        installed = tmp_path / "home" / root / "skills" / "kitconc"
        assert (installed / "SKILL.md").is_file() and (installed / "references" / "pipelines.md").is_file()
    assert skill_installer.main(["install", "--target", "codex"]) == 1  # exists without --force
    assert skill_installer.main(["install", "--target", "codex", "--force"]) == 0
    assert skill_installer.main(["install", "--dest", str(tmp_path / "custom")]) == 0
    assert (tmp_path / "custom" / "kitconc" / "SKILL.md").is_file()
