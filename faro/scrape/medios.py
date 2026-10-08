"""Normalización de medios por dominio (M1.3).

Mapa dominio -> (fuente_id, nombre) desde `config/fuentes.yaml`. Las noticias de
GDELT (o de cualquier origen) cuyo dominio sea de un medio del catálogo se
atribuyen a ese medio; si no, quedan como `gdelt`/`<dominio>`.
"""

from __future__ import annotations

from functools import lru_cache

from faro.loaders import load_fuentes


@lru_cache(maxsize=1)
def _mapa() -> list[tuple[str, str, str]]:
    out = []
    for f in load_fuentes():
        if f.get("familia") != "noticias":
            continue
        for d in f.get("dominios", []):
            out.append((d.lower(), f["id"], f["nombre"]))
    return out


def normalizar_medio(dominio: str) -> tuple[str, str] | None:
    """Devuelve (fuente_id, nombre) si el dominio es de un medio del catálogo; si no, None."""
    dom = (dominio or "").lower().strip()
    if not dom:
        return None
    for d, fid, nombre in _mapa():
        if dom == d or dom.endswith("." + d):
            return (fid, nombre)
    return None
