# -*- coding: utf-8 -*-
"""Install the Kitconc agent skill for Claude and Codex (``kitconc-skill``).

The skill (``kitconc/agent/skill/kitconc``) follows the open Agent Skills format: a folder with a
``SKILL.md`` (name + description front matter) and reference files. Claude looks for skills in
``~/.claude/skills`` (user) and ``<project>/.claude/skills``; Codex in ``~/.agents/skills`` (user)
and ``<repo>/.agents/skills``.

    kitconc-skill install                    # Claude and Codex, user level
    kitconc-skill install --target codex     # only Codex
    kitconc-skill install --scope project    # into ./.claude/skills and ./.agents/skills
    kitconc-skill install --dest DIR         # any other skills folder
    kitconc-skill path                       # where the bundled skill lives
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SKILL_NAME = "kitconc"
SKILL_SOURCE = Path(__file__).resolve().parent / "skill" / SKILL_NAME
TARGETS = {
    "claude": {"user": Path.home() / ".claude" / "skills", "project": Path(".claude") / "skills"},
    "codex": {"user": Path.home() / ".agents" / "skills", "project": Path(".agents") / "skills"},
}


def install(dest_root: Path, force: bool = False) -> Path:
    """Copies the skill folder into ``dest_root/kitconc``; returns the installed path."""
    if not (SKILL_SOURCE / "SKILL.md").is_file():
        raise FileNotFoundError(f"Bundled skill not found at {SKILL_SOURCE}")
    target = dest_root / SKILL_NAME
    if target.exists():
        if not force:
            raise FileExistsError(f"{target} already exists (use --force to replace it)")
        shutil.rmtree(target)
    dest_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SKILL_SOURCE, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kitconc-skill", description="Install the Kitconc agent skill.")
    sub = parser.add_subparsers(dest="command", required=True)
    inst = sub.add_parser("install", help="Copy the skill into Claude and/or Codex skill folders")
    inst.add_argument("--target", choices=["all", "claude", "codex"], default="all")
    inst.add_argument("--scope", choices=["user", "project"], default="user",
                      help="user = home folder; project = current directory")
    inst.add_argument("--dest", default=None, help="Install into this skills folder instead")
    inst.add_argument("--force", action="store_true", help="Replace an existing installation")
    sub.add_parser("path", help="Print the folder of the bundled skill")
    args = parser.parse_args(argv)

    if args.command == "path":
        print(SKILL_SOURCE)
        return 0
    roots = [Path(args.dest)] if args.dest else [
        TARGETS[name][args.scope] for name in (["claude", "codex"] if args.target == "all" else [args.target])
    ]
    status = 0
    for root in roots:
        try:
            print(f"installed: {install(root.resolve(), force=args.force)}")
        except (FileExistsError, FileNotFoundError, OSError) as exc:
            print(f"skipped: {exc}", file=sys.stderr)
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
