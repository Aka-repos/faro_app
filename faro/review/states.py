"""Estados de revisión humana (F-13).

Cinco estados: nuevo, en revisión, requiere evidencia, aprobado como borrador,
descartado. Aprobar un borrador **no** publica nada.
"""

from __future__ import annotations

ESTADOS = ["nuevo", "en revisión", "requiere evidencia", "aprobado como borrador", "descartado"]


def transicion(estado_actual: str, nuevo_estado: str) -> str:
    if nuevo_estado not in ESTADOS:
        raise ValueError(f"Estado inválido: {nuevo_estado}. Válidos: {ESTADOS}")
    return nuevo_estado


def puede_publicar(estado: str) -> bool:
    """Ningún estado habilita publicación automática (T08)."""
    return False


def es_final(estado: str) -> bool:
    return estado in ("aprobado como borrador", "descartado")
