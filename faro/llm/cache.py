"""Caché de generación por sha256 (F-10)."""

from __future__ import annotations

import hashlib
import json
import os

import config.settings as S

_CACHE_DIR = S.DATA_DIR / "cache"


def cache_key(prompt_version: str, lente: str, ids_evidencia: list[str], modelo: str) -> str:
    raw = json.dumps([prompt_version, lente, sorted(ids_evidencia), modelo], sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _path(key: str) -> str:
    return os.path.join(_CACHE_DIR, f"{key}.json")


def get(key: str) -> dict | None:
    p = _path(key)
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:  # noqa: BLE001
        return None


def put(key: str, resultado: dict) -> None:
    os.makedirs(_CACHE_DIR, exist_ok=True)
    with open(_path(key), "w", encoding="utf-8") as fh:
        json.dump(resultado, fh, ensure_ascii=False)
