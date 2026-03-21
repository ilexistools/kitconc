from __future__ import annotations

import re
from typing import List


_SENT_SPLIT = re.compile(r"(?<=[.!?…])\s+(?=[A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ0-9“\"'(\[])")
_WS = re.compile(r"\s+")


def _normalize_ws(text: str) -> str:
    return _WS.sub(" ", text).strip()


def approx_token_count(text: str) -> int:
    """
    Aproxima tokens sem tokenizer:
    - Em média, 1 token ~ 4 caracteres em inglês; em PT é parecido.
    - Também funciona razoavelmente bem para controlar tamanho de chunk.
    """
    text = text.strip()
    if not text:
        return 0
    # protege contra subestimativa em textos com muitas palavras curtas
    by_chars = max(1, len(text) // 4)
    by_words = max(1, int(len(text.split()) / 0.75))  # ~ 0.75 palavra por token
    # pega uma média conservadora
    return int((by_chars + by_words) / 2)


def chunk_text(
    text: str,
    chunk_size: int = 300,
    chunk_overlap: int = 50,
    min_chunk_size: int = 80,
) -> List[str]:
    """
    Quebra um texto em chunks para RAG.

    Params
    ------
    text : str
        Texto de entrada.
    chunk_size : int
        Tamanho alvo do chunk em tokens aproximados.
    chunk_overlap : int
        Overlap em tokens aproximados entre chunks consecutivos.
    min_chunk_size : int
        Evita criar chunks muito pequenos no final.

    Returns
    -------
    List[str]
        Lista de chunks (strings).
    """
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap deve ser menor que chunk_size.")

    text = text.strip()
    if not text:
        return []

    # 1) Divide em parágrafos "fortes" primeiro
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]

    # 2) Para cada parágrafo, divide em frases (para juntar de forma controlada)
    units: List[str] = []
    for p in paragraphs:
        p = _normalize_ws(p)
        # se o parágrafo já for pequeno, entra como unidade
        if approx_token_count(p) <= chunk_size:
            units.append(p)
            continue

        # senão, divide em frases
        sents = [s.strip() for s in _SENT_SPLIT.split(p) if s.strip()]
        if not sents:
            units.append(p)
            continue

        # se alguma frase for enorme, quebra por "pedaços" de palavras
        for s in sents:
            if approx_token_count(s) <= chunk_size:
                units.append(s)
            else:
                words = s.split()
                buf = []
                for w in words:
                    buf.append(w)
                    if approx_token_count(" ".join(buf)) >= chunk_size:
                        units.append(" ".join(buf))
                        buf = []
                if buf:
                    units.append(" ".join(buf))

    # 3) Agora junta unidades até bater chunk_size
    chunks: List[str] = []
    current: List[str] = []
    current_tokens = 0

    def flush():
        nonlocal current, current_tokens
        if current:
            chunk = _normalize_ws(" ".join(current))
            if chunk:
                chunks.append(chunk)
        current = []
        current_tokens = 0

    for u in units:
        u_tokens = approx_token_count(u)
        if not current:
            current = [u]
            current_tokens = u_tokens
            continue

        # se adicionar estoura o tamanho, fecha chunk
        if current_tokens + u_tokens > chunk_size:
            flush()
            current = [u]
            current_tokens = u_tokens
        else:
            current.append(u)
            current_tokens += u_tokens

    flush()

    # 4) Overlap: faz uma janela deslizante reaproveitando o final do chunk anterior
    if chunk_overlap > 0 and len(chunks) > 1:
        overlapped: List[str] = [chunks[0]]
        for i in range(1, len(chunks)):
            prev = overlapped[-1]
            prev_words = prev.split()
            # pega um "final" do anterior que aproxime o overlap
            # (aprox pelo número de palavras)
            target_words = max(10, int(chunk_overlap * 0.75))  # ~0.75 palavra/token
            tail = " ".join(prev_words[-target_words:]) if len(prev_words) > target_words else prev
            merged = _normalize_ws(tail + " " + chunks[i])
            # se o merged ficou grande demais, mantém só o chunk original (overlap falhou)
            if approx_token_count(merged) > chunk_size + chunk_overlap:
                merged = chunks[i]
            overlapped.append(merged)
        chunks = overlapped

    # 5) Evita um último chunk “micro” juntando com o anterior
    if len(chunks) >= 2 and approx_token_count(chunks[-1]) < min_chunk_size:
        chunks[-2] = _normalize_ws(chunks[-2] + " " + chunks[-1])
        chunks.pop()

    return chunks
