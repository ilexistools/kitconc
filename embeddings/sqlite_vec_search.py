from __future__ import annotations

"""
SQLite-backed semantic index using sqlite-vec (vec0 virtual table) + Sentence-Transformers.

What you get
------------
- No Haystack dependency
- Vector search happens inside SQLite via sqlite-vec (vec0)
- Keeps your "MemorySearch-like" API: add() + search()
- Stores documents in a normal table and embeddings in a vec0 virtual table.

sqlite-vec notes
----------------
- Load extension in Python with sqlite_vec.load(conn) after enabling load_extension.
- KNN query pattern:
    SELECT id, distance FROM vec_table
    WHERE embedding MATCH :query AND k = :k;

- You can set cosine distance metric:
    CREATE VIRTUAL TABLE vec_docs USING vec0(
      doc_id INTEGER PRIMARY KEY,
      embedding float[768] distance_metric=cosine
    );
"""

from typing import List, Dict, Any, Optional, Iterable, Tuple
from pathlib import Path
import os
import json
import sqlite3
import threading
import numpy as np

import sqlite_vec  # pip install sqlite-vec
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

_DEFAULT_MODEL = os.getenv("EMBEDDINGS_MODEL", "sentence-transformers/all-mpnet-base-v2")


# ---------------------------- cache utilities -----------------------------

def _models_dir(explicit: Optional[str] = None) -> Path:
    """Return ./models next to this file (or the provided explicit path)."""
    if explicit:
        return Path(explicit).expanduser().resolve()
    return Path(__file__).resolve().parent / "models"


def _setup_caches(models_dir: Optional[str] = None) -> Path:
    """Centralize HuggingFace/ST caches under one directory (default: ./models)."""
    root = _models_dir(models_dir)
    root.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(root))
    os.environ.setdefault("HF_HOME", str(root))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(root))
    return root


def download_model(model_name: str = _DEFAULT_MODEL, models_dir: Optional[str] = None) -> str:
    """Pre-download a model into the local cache and return the repo_id."""
    root = _setup_caches(models_dir)
    SentenceTransformer(model_name, cache_folder=str(root))
    return model_name


# ------------------------------- core class --------------------------------

class SQLiteVecSearch:
    """
    SQLite-backed index for RAG using sqlite-vec.

    API
    ---
    - add(items)          — index a list of {"text": str, "metadata": dict}
    - search(query, top_k) — KNN semantic search
    - count()             — number of indexed documents
    - vacuum()            — compact the database
    - close()             — release the connection
    - context manager     — ``with SQLiteVecSearch(...) as idx:``

    similarity
    ----------
    With cosine distance metric: similarity = 1 − distance
    """

    def __init__(
        self,
        db_path: str | os.PathLike = "./rag_index.sqlite3",
        *,
        model_name: str = _DEFAULT_MODEL,
        normalize: bool = True,
        device: Optional[str] = None,
        models_dir: Optional[str] = None,
        pragmas: Optional[Dict[str, Any]] = None,
        embedding_batch_size: int = 64,
    ) -> None:
        self.db_path = Path(db_path).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._normalize = normalize
        self._embedding_batch_size = int(max(1, embedding_batch_size))

        # Unify caches, then load the model once
        local_root = _setup_caches(models_dir)
        self._model = SentenceTransformer(
            model_name,
            cache_folder=str(local_root),
            device=device,
        )
        self._dim = int(self._model.get_sentence_embedding_dimension())

        # SQLite connection (autocommit)
        self._conn = sqlite3.connect(
            self.db_path, isolation_level=None, check_same_thread=False
        )
        self._lock = threading.RLock()
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._apply_pragmas(pragmas)
        self._load_sqlite_vec()
        self._create_schema()

    # ------------------------------------------------------------------ #
    # Context manager                                                       #
    # ------------------------------------------------------------------ #

    def __enter__(self) -> "SQLiteVecSearch":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ------------------------------------------------------------------ #
    # SQLite helpers                                                        #
    # ------------------------------------------------------------------ #

    def _load_sqlite_vec(self) -> None:
        with self._lock:
            self._conn.enable_load_extension(True)
            sqlite_vec.load(self._conn)
            self._conn.enable_load_extension(False)
            self._conn.execute("SELECT vec_version()")  # sanity check

    def _apply_pragmas(self, overrides: Optional[Dict[str, Any]]) -> None:
        pragmas: Dict[str, Any] = {
            "journal_mode": "WAL",
            "synchronous": 1,      # NORMAL
            "temp_store": 2,       # MEMORY
            "cache_size": -65536,  # 64 MB
        }
        if overrides:
            pragmas.update(overrides)
        with self._lock:
            cur = self._conn.cursor()
            for k, v in pragmas.items():
                cur.execute(f"PRAGMA {k} = {json.dumps(v)};")
            cur.close()

    def _create_schema(self) -> None:
        with self._lock:
            cur = self._conn.cursor()
            cur.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    text          TEXT    NOT NULL,
                    metadata_json TEXT    NOT NULL
                );

                CREATE TABLE IF NOT EXISTS meta (
                    key   TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_documents_id ON documents(id);
                """
            )
            cur.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
                ("embedding_dim", str(self._dim)),
            )
            cur.execute(
                f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS vec_documents USING vec0(
                    doc_id    INTEGER PRIMARY KEY,
                    embedding float[{self._dim}] distance_metric=cosine
                );
                """
            )
            cur.close()

    # ------------------------------------------------------------------ #
    # Embedding                                                             #
    # ------------------------------------------------------------------ #

    def _embed(self, texts: List[str]) -> np.ndarray:
        """Encode texts to float32 embeddings, optionally L2-normalised."""
        if not texts:
            return np.zeros((0, self._dim), dtype=np.float32)

        arr: np.ndarray = self._model.encode(
            texts,
            batch_size=self._embedding_batch_size,
            convert_to_numpy=True,
            normalize_embeddings=False,
            show_progress_bar=False,
        )
        arr = np.asarray(arr, dtype=np.float32)

        if self._normalize:
            norms = np.linalg.norm(arr, axis=1, keepdims=True) + 1e-12
            arr /= norms

        return arr

    # ------------------------------------------------------------------ #
    # Public API                                                            #
    # ------------------------------------------------------------------ #

    def add(self, items: List[Dict[str, Any]]) -> None:
        """
        Index a batch of documents.

        Parameters
        ----------
        items : list of {"text": str, "metadata": dict}
        """
        if not items:
            return

        texts: List[str] = []
        doc_rows: List[Tuple[str, str]] = []

        for i, it in enumerate(items):
            if not isinstance(it, dict) or "text" not in it or "metadata" not in it:
                raise ValueError(f"Item {i} must be {{'text': str, 'metadata': dict}}.")
            if not isinstance(it["text"], str):
                raise ValueError(f"Item {i}: 'text' must be a string.")
            if not isinstance(it["metadata"], dict):
                raise ValueError(f"Item {i}: 'metadata' must be a dict.")
            texts.append(it["text"])
            doc_rows.append((it["text"], json.dumps(it["metadata"], ensure_ascii=False)))

        with self._lock:
            cur = self._conn.cursor()
            try:
                cur.execute("BEGIN IMMEDIATE")

                doc_ids: List[int] = []
                for row in doc_rows:
                    cur.execute(
                        "INSERT INTO documents(text, metadata_json) VALUES (?, ?)",
                        row,
                    )
                    doc_ids.append(int(cur.lastrowid))

                embs = self._embed(texts)
                if embs.shape[1] != self._dim:
                    raise ValueError(
                        f"Embedding dim mismatch: expected {self._dim}, got {embs.shape[1]}"
                    )

                cur.executemany(
                    "INSERT OR REPLACE INTO vec_documents(doc_id, embedding) VALUES (?, ?)",
                    [(doc_ids[i], embs[i]) for i in range(len(doc_ids))],
                )
                cur.execute("COMMIT")
            except Exception:
                cur.execute("ROLLBACK")
                raise
            finally:
                cur.close()

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Semantic KNN search.

        Returns
        -------
        list of {"rank": int, "similarity": float, "distance": float,
                 "doc": {"text": str, "metadata": dict}}
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string.")

        k = int(max(1, top_k))
        q_emb = self._embed([query])[0]

        with self._lock:
            cur = self._conn.cursor()
            matches = cur.execute(
                """
                SELECT doc_id, distance
                FROM vec_documents
                WHERE embedding MATCH ? AND k = ?;
                """,
                (q_emb, k),
            ).fetchall()
            cur.close()

        if not matches:
            return []

        ids = [int(r[0]) for r in matches]
        dist_map = {int(doc_id): float(dist) for doc_id, dist in matches}
        docs = self._fetch_docs(ids)

        return [
            {
                "rank": rank,
                "similarity": round(1.0 - dist_map[doc_id], 6),
                "distance": round(dist_map[doc_id], 6),
                "doc": docs.get(doc_id, {"text": "", "metadata": {}}),
            }
            for rank, doc_id in enumerate(ids, start=1)
        ]

    def count(self) -> int:
        """Return the number of indexed documents."""
        with self._lock:
            (n,) = self._conn.execute("SELECT COUNT(*) FROM documents").fetchone()
        return int(n)

    def vacuum(self) -> None:
        """Compact the database file."""
        with self._lock:
            self._conn.execute("VACUUM")

    def close(self) -> None:
        """Close the SQLite connection."""
        try:
            with self._lock:
                self._conn.close()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Internal                                                              #
    # ------------------------------------------------------------------ #

    def _fetch_docs(self, ids: Iterable[int]) -> Dict[int, Dict[str, Any]]:
        id_list = list(ids)
        if not id_list:
            return {}
        placeholders = ",".join(["?"] * len(id_list))
        with self._lock:
            rows = self._conn.execute(
                f"SELECT id, text, metadata_json FROM documents WHERE id IN ({placeholders})",
                id_list,
            ).fetchall()
        return {
            int(doc_id): {"text": text, "metadata": json.loads(meta_json)}
            for doc_id, text, meta_json in rows
        }


# ------------------------------- quick demo -------------------------------

if __name__ == "__main__":
    print("Downloading/confirming local model...")
    download_model(_DEFAULT_MODEL)

    data = [
        {"text": "Python é muito usada em ciência de dados.", "metadata": {"id": 1}},
        {"text": "Rust foca em segurança de memória e performance.", "metadata": {"id": 2}},
        {"text": "Java é comum em backends corporativos.", "metadata": {"id": 3}},
    ]

    with SQLiteVecSearch("./demo.sqlite3") as idx:
        idx.add(data)
        print(f"Total docs: {idx.count()}")
        for r in idx.search("linguagens para backend com performance", top_k=3):
            print(
                f"Rank {r['rank']}: similarity={r['similarity']:.4f}  "
                f"text={r['doc']['text']!r}"
            )
