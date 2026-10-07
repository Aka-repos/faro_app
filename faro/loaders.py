"""Carga de archivos YAML de configuración con caché simple."""

from __future__ import annotations

import functools
from typing import Any

import yaml

import config.settings as S


def _load_yaml(path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data


@functools.lru_cache(maxsize=32)
def load_fuentes() -> list[dict[str, Any]]:
    return _load_yaml(S.CONFIG_DIR / "fuentes.yaml").get("fuentes", [])


@functools.lru_cache(maxsize=32)
def load_keywords() -> dict[str, Any]:
    return _load_yaml(S.CONFIG_DIR / "keywords.yaml")


@functools.lru_cache(maxsize=32)
def load_mapas() -> dict[str, Any]:
    return _load_yaml(S.CONFIG_DIR / "mapas.yaml")


@functools.lru_cache(maxsize=32)
def load_sectores() -> list[dict[str, Any]]:
    return _load_yaml(S.CONFIG_DIR / "sectores.yaml").get("sectores", [])


@functools.lru_cache(maxsize=32)
def load_lente(lente: str) -> dict[str, Any]:
    return _load_yaml(S.CONFIG_DIR / "lentes" / f"{lente}.yaml")
