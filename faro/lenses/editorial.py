"""Lente editorial (TVN): paquete editorial (E-03, T09)."""

from __future__ import annotations

from faro.llm.extractive import generar_editorial


def generar_paquete(evento: dict, afirmaciones: list[dict], contexto: list[dict]) -> dict:
    """Genera brief + guion + copy a partir de afirmaciones verificadas."""
    return generar_editorial(evento, afirmaciones, contexto)
