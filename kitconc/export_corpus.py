# -*- coding: utf-8 -*-
"""Create portable ZIP archives for filesystem-based Kitconc corpora."""

from __future__ import annotations

import os
import tempfile
import zipfile
from pathlib import Path


def export(workspace, corpus_name, dest_folder):
    workspace_path = Path(workspace).expanduser().resolve()
    corpus_path = (workspace_path / corpus_name).resolve()
    destination = Path(dest_folder).expanduser().resolve()
    if not (corpus_path / "info.tab").is_file():
        raise FileNotFoundError(f"Corpus not found: {corpus_name}")
    if corpus_path.parent != workspace_path:
        raise ValueError("Corpus must be located directly inside the workspace.")
    if not destination.is_dir():
        raise ValueError(f"Export destination is not a folder: {destination}")
    if destination == corpus_path or corpus_path in destination.parents:
        raise ValueError("Export destination cannot be inside the corpus being exported.")

    target = destination / f"{corpus_name}.zip"
    fd, temporary_name = tempfile.mkstemp(prefix=f".{corpus_name}-", suffix=".zip.tmp", dir=destination)
    os.close(fd)
    try:
        with zipfile.ZipFile(temporary_name, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for root, dirs, files in os.walk(corpus_path):
                dirs.sort(key=str.lower)
                for filename in sorted(files, key=str.lower):
                    if filename.lower().endswith(".xlsx"):
                        continue
                    path = Path(root) / filename
                    if path == corpus_path / "output" / "read_me.txt":
                        continue
                    archive.write(path, path.relative_to(workspace_path).as_posix())
            archive.writestr(f"{corpus_name}/output/read_me.txt", "This is the output folder.")
        os.replace(temporary_name, target)
        return target
    finally:
        Path(temporary_name).unlink(missing_ok=True)


if __name__ == "__main__":
    import sys

    export(sys.argv[1], sys.argv[2], sys.argv[3])
