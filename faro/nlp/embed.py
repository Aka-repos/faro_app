"""Embeddings (F-04, L-04): siempre locales y en CPU.

Usa ``intfloat/multilingual-e5-small`` si está instalado (sentence-transformers);
si no, cae a un embedding por hashing de n-gramas de caracteres (determinístico,
sin red, sin descargas) para que el pipeline corra en una máquina limpia.
"""

from __future__ import annotations

import hashlib
import json
import re

import numpy as np

import config.settings as S

try:
    from sentence_transformers import SentenceTransformer  # type: ignore

    _ST = True
except Exception:  # noqa: BLE001
    _ST = False

_MODEL_NAME = "intfloat/multilingual-e5-small"
EMBEDDER_NAME = _MODEL_NAME
_DIM_FALLBACK = 384


def _fallback_embed(text: str, dim: int = _DIM_FALLBACK) -> np.ndarray:
    """Embedding determinístico por hashing de n-gramas (sin modelo)."""
    text = (text or "").lower()
    vec = np.zeros(dim, dtype=np.float32)
    tokens = [text]
    tokens += re.findall(r"[a-záéíóúñü0-9]+", text)
    for w in tokens:
        for ng in (2, 3):
            for i in range(max(0, len(w) - ng + 1)):
                gram = w[i : i + ng]
                idx = int(hashlib.md5(gram.encode("utf-8")).hexdigest(), 16) % dim
                vec[idx] += 1.0
    norm = float(np.linalg.norm(vec))
    return vec / norm if norm > 0 else vec


class Embedder:
    """e5-small (obligatorio fuera de tests, D-11). El fallback por hashing solo en tests."""

    def __init__(self, require_model: bool = True) -> None:
        self._model = None
        if _ST:
            try:
                self._model = SentenceTransformer(_MODEL_NAME)
            except Exception as e:  # noqa: BLE001
                if require_model and not S.PERMITIR_FALLBACK:
                    raise RuntimeError(
                        f"No se pudo cargar {_MODEL_NAME}. Corre `make setup` con red o "
                        f"fija FARO_PERMITIR_FALLBACK=1 solo para pruebas. Detalle: {e}"
                    ) from e
                self._model = None
        self.nombre = _MODEL_NAME if self._model is not None else "hash-ngram-fallback"

    def encode(self, textos: list[str]) -> np.ndarray:
        if self._model is not None:
            # e5 prefiere prefijos query:/passage:; aquí son pasajes.
            vecs = self._model.encode(
                [f"passage: {t}" for t in textos],
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return np.asarray(vecs, dtype=np.float32)
        if not S.PERMITIR_FALLBACK:
            raise RuntimeError("Embedder sin modelo y fallback deshabilitado (WP-2).")
        return np.stack([_fallback_embed(t) for t in textos])


def compute_vectors(textos: list[str], ids: list[str]) -> tuple[np.ndarray, list[str]]:
    emb = Embedder()
    matriz = emb.encode(textos)
    np.save(S.VECTOR_PATH, matriz)
    with open(S.VECTOR_IDX_PATH, "w", encoding="utf-8") as fh:
        json.dump(ids, fh, ensure_ascii=False)
    return matriz, ids


def load_vectors() -> tuple[np.ndarray, list[str]]:
    if not S.VECTOR_PATH.exists():
        raise FileNotFoundError("No hay vectores; corre `make build` primero.")
    matriz = np.load(S.VECTOR_PATH)
    with open(S.VECTOR_IDX_PATH, encoding="utf-8") as fh:
        ids = json.load(fh)
    return matriz, ids


def cosine_search(
    matriz: np.ndarray, query_vec: np.ndarray, top_k: int = 10
) -> list[tuple[int, float]]:
    sims = matriz @ query_vec
    idx = np.argsort(-sims)[:top_k]
    return [(int(i), float(sims[i])) for i in idx]
