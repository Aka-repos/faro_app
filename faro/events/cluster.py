"""Agrupación de noticias en eventos (F-05, T02, T03).

Combina:
1. casi-duplicados por título (rapidfuzz) — misma agencia replicada (CU-03);
2. similitud por coseno de embeddings + ventana de 72 h + entidades compartidas.

Una noticia recirculada conserva su fecha original y no se fusiona con eventos
recientes (T03): el criterio de ventana temporal usa ``fecha_publicacion``.
"""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np

from faro.nlp.entities import extraer_entidades

try:
    from rapidfuzz import fuzz

    _RF = True
except Exception:  # noqa: BLE001
    _RF = False


def _iso_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    except ValueError:
        return None


def _horas(a: datetime, b: datetime) -> float:
    return abs((a - b).total_seconds()) / 3600


class UnionFind:
    def __init__(self, n: int) -> None:
        self.p = list(range(n))

    def find(self, x: int) -> int:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


def _titulo_ratio(a: str, b: str) -> float:
    if not _RF:
        return 1.0 if a.strip().lower() == b.strip().lower() else 0.0
    return fuzz.ratio(a.strip().lower(), b.strip().lower()) / 100.0


def agrupar_eventos(
    noticias: list[dict],
    embeddings: np.ndarray,
    umbral_ratio: float = 0.82,
    umbral_coseno: float = 0.9,
    ventana_h: int = 72,
) -> list[list[int]]:
    """Devuelve listas de índices de noticias que forman cada evento."""
    n = len(noticias)
    uf = UnionFind(n)
    entidades = [extraer_entidades(nc["titulo"]) for nc in noticias]

    for i in range(n):
        for j in range(i + 1, n):
            ratio = _titulo_ratio(noticias[i]["titulo"], noticias[j]["titulo"])
            cos = float(np.dot(embeddings[i], embeddings[j]))
            di = _iso_dt(noticias[i].get("fecha_publicacion"))
            dj = _iso_dt(noticias[j].get("fecha_publicacion"))
            dentro_ventana = di and dj and _horas(di, dj) <= ventana_h
            comparten_entidad = any(
                e["nombre"].lower() in [x["nombre"].lower() for x in entidades[j]]
                for e in entidades[i]
                if e["tipo"] in ("ORG", "LOC")
            )
            if ratio >= umbral_ratio and dentro_ventana:
                uf.union(i, j)
            elif cos >= umbral_coseno and dentro_ventana and comparten_entidad:
                uf.union(i, j)

    grupos: dict[int, list[int]] = {}
    for i in range(n):
        grupos.setdefault(uf.find(i), []).append(i)
    return sorted(grupos.values(), key=lambda g: min(g))
