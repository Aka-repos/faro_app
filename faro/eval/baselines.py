"""Baselines simples (D-08): palabras clave y extractivo.

Sirven para medir qué mejora aporta la IA y cuándo no ayuda (sección 8 del reto).
"""

from __future__ import annotations

from faro.nlp.classify import clasificar_baseline


def baseline_clasificar(titulares: list[str]) -> list[str]:
    return [clasificar_baseline(t) for t in titulares]


def baseline_generar(evento: dict) -> dict:
    """Generación extractiva: el piso que cualquier LLM debería superar."""
    titulo = evento.get("titulo_canonico", "")
    return {
        "titulo": titulo,
        "brief": f"Tema {evento.get('tema', '')}: {titulo}. Sin redacción generativa.",
        "copy_digital": titulo[:80],
        "generador": "extractivo",
    }
