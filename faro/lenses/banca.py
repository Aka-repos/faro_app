"""Lente bancario: sectores (B-02) y boletín (B-04, CU-05)."""

from __future__ import annotations

from faro.llm.extractive import generar_boletin
from faro.loaders import load_sectores


def mapear_sectores(evento: dict, noticias: list[dict]) -> list[dict]:
    """Enlaza evento -> sector con la regla (keyword) que lo justifica (B-02)."""
    texto = " ".join([evento.get("titulo_canonico", "")] + [n["titulo"] for n in noticias]).lower()
    sectores = load_sectores()
    out = []
    for s in sectores:
        for kw in s["keywords"]:
            if kw in texto:
                out.append(
                    {
                        "sector_id": s["id"],
                        "nombre": s["nombre"],
                        "regla": f"keyword '{kw}' presente en el evento",
                        "confianza": 0.8,
                    }
                )
                break
    return out


def generar_boletin_sectorial(evento: dict, afirmaciones: list[dict], sectores: list[str]) -> dict:
    return generar_boletin(evento, afirmaciones, sectores)
