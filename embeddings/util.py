from __future__ import annotations

import csv
import json
from typing import Any, Dict, List

import pypdf


# ------------------------------------------------------------------ #
# Plain text                                                           #
# ------------------------------------------------------------------ #

def read_all_text(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as fh:
        return fh.read()


def write_all_text(file_path: str, text: str) -> None:
    with open(file_path, "w", encoding="utf-8") as fh:
        fh.write(text)


# ------------------------------------------------------------------ #
# PDF                                                                  #
# ------------------------------------------------------------------ #

def read_pdf_pages(file_path: str) -> List[str]:
    """Return a list of strings, one per page."""
    with open(file_path, "rb") as fh:
        reader = pypdf.PdfReader(fh)
        return [page.extract_text() or "" for page in reader.pages]


def read_pdf_text(file_path: str) -> str:
    """Return the full PDF text as a single string."""
    return " ".join(read_pdf_pages(file_path))


# ------------------------------------------------------------------ #
# TSV                                                                  #
# ------------------------------------------------------------------ #

def read_tab_separated_file(file_path: str) -> List[List[str]]:
    with open(file_path, "r", encoding="utf-8") as fh:
        return [line.strip().split("\t") for line in fh]


def write_tab_separated_file(file_path: str, data: List[List[str]]) -> None:
    with open(file_path, "w", encoding="utf-8") as fh:
        for row in data:
            fh.write("\t".join(row) + "\n")


def load_tsv_to_json_list(tsv_path: str) -> List[Dict[str, Any]]:
    """
    Read a TSV file and return a list of dicts.

    The first column must be named ``text``; remaining columns become
    ``metadata``.  The first row is assumed to be the header.
    """
    result: List[Dict[str, Any]] = []
    with open(tsv_path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            d = dict(row)
            result.append({"text": d.pop("text"), "metadata": d})
    return result


# ------------------------------------------------------------------ #
# JSON / JSONL                                                         #
# ------------------------------------------------------------------ #

def read_json_file(file_path: str) -> Any:
    with open(file_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json_file(file_path: str, data: Any) -> None:
    with open(file_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=4)


def read_jsonl_file(file_path: str) -> List[Any]:
    with open(file_path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def write_jsonl_file(file_path: str, data: List[Any]) -> None:
    with open(file_path, "w", encoding="utf-8") as fh:
        for item in data:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")
