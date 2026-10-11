"""Safe import and export helpers for filesystem-based corpora."""

from __future__ import annotations

import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

MAX_ARCHIVE_BYTES = int(os.getenv("KITCONC_MAX_IMPORT_BYTES", str(2 * 1024**3)))
MAX_DOWNLOAD_BYTES = int(os.getenv("KITCONC_MAX_DOWNLOAD_BYTES", str(512 * 1024**2)))
_CORPUS_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")


def _validated_corpus_name(name: str) -> str:
    if name in {".", ".."} or not _CORPUS_NAME.fullmatch(name):
        raise ValueError(f"Invalid corpus name in archive: {name!r}")
    return name


def import_corpus_zip(filename: str | os.PathLike[str], workspace: str | os.PathLike[str]) -> Path:
    """Validate and atomically import a single-root Kitconc corpus archive."""
    workspace_path = Path(workspace).expanduser().resolve()
    workspace_path.mkdir(parents=True, exist_ok=True)
    archive_path = Path(filename).expanduser().resolve()
    if not archive_path.is_file():
        raise FileNotFoundError(f"Corpus archive not found: {archive_path}")

    stage = Path(tempfile.mkdtemp(prefix=".kitconc-import-", dir=workspace_path))
    try:
        with zipfile.ZipFile(archive_path) as archive:
            members = archive.infolist()
            if len(members) > 100_000:
                raise ValueError("Archive contains too many entries.")
            roots: set[str] = set()
            seen_members: set[str] = set()
            total_size = 0
            has_info = False
            for member in members:
                raw_name = member.filename
                if "\\" in raw_name:
                    raise ValueError("Archive contains an invalid path separator.")
                if raw_name in seen_members:
                    raise ValueError("Archive contains duplicate paths.")
                seen_members.add(raw_name)
                raw_parts = raw_name.rstrip('/').split('/')
                if any(part in {"", ".", ".."} for part in raw_parts):
                    raise ValueError("Archive contains an unsafe path.")
                member_path = PurePosixPath(raw_name)
                if member_path.is_absolute() or any(part in {"", ".", ".."} for part in member_path.parts):
                    raise ValueError("Archive contains an unsafe path.")
                if len(member_path.parts) == 1 and member.is_dir():
                    roots.add(_validated_corpus_name(member_path.parts[0]))
                    if len(roots) > 1:
                        raise ValueError("Archive must contain exactly one corpus directory.")
                    continue
                if len(member_path.parts) < 2:
                    raise ValueError("Archive must contain one top-level corpus directory.")
                root = _validated_corpus_name(member_path.parts[0])
                roots.add(root)
                if len(roots) > 1:
                    raise ValueError("Archive must contain exactly one corpus directory.")
                mode = member.external_attr >> 16
                if mode and (mode & 0o170000) == 0o120000:
                    raise ValueError("Archive cannot contain symbolic links.")
                total_size += member.file_size
                if total_size > MAX_ARCHIVE_BYTES:
                    raise ValueError(
                        f"Archive expands beyond the {MAX_ARCHIVE_BYTES}-byte import limit."
                    )
                if member_path.parts[1:] == ("info.tab",) and not member.is_dir():
                    has_info = True

            if len(roots) != 1 or not has_info:
                raise ValueError("Archive must contain a corpus root with info.tab.")
            corpus_name = roots.pop()
            destination = (workspace_path / corpus_name).resolve()
            if destination.parent != workspace_path or destination.exists():
                raise FileExistsError(f"A corpus named {corpus_name!r} already exists.")

            archive.extractall(stage)
            extracted = stage / corpus_name
            if not (extracted / "info.tab").is_file():
                raise ValueError("Extracted archive is missing info.tab.")
            os.replace(extracted, destination)
            return destination
    except zipfile.BadZipFile as exc:
        raise ValueError("The selected file is not a valid ZIP archive.") from exc
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def download_and_import_corpus(url: str, workspace: str | os.PathLike[str]) -> Path:
    """Download a bounded ZIP archive and import it with the same validation."""
    import requests

    workspace_path = Path(workspace).expanduser().resolve()
    workspace_path.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".kitconc-download-", suffix=".zip", dir=workspace_path)
    try:
        total = 0
        with os.fdopen(fd, "wb") as target:
            with requests.get(url, stream=True, timeout=(10, 60)) as response:
                response.raise_for_status()
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > MAX_DOWNLOAD_BYTES:
                    raise ValueError("The download exceeds the configured size limit.")
                for block in response.iter_content(chunk_size=1024 * 1024):
                    if not block:
                        continue
                    total += len(block)
                    if total > MAX_DOWNLOAD_BYTES:
                        raise ValueError("The download exceeds the configured size limit.")
                    target.write(block)
        return import_corpus_zip(temp_name, workspace_path)
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
        Path(temp_name).unlink(missing_ok=True)
