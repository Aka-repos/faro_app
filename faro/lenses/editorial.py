"""Lente editorial (TVN): paquete editorial generado con LLM (M3)."""

from __future__ import annotations

from faro.lenses import _llm
from faro.llm.extractive import generar_editorial
from schemas import PaqueteEditorial

_SYSTEM = (
    "Redacta un paquete editorial para TVN. Solo afirma lo que esté en <datos>; cada afirmación "
    "con su evidencia_id y campo. Distingue hecho, declaración, inferencia e hipótesis. Brief ≤ 250 "
    "palabras, copy ≤ 80 palabras, guion de 45–60 s (104–138 palabras). Si solo hay titular/metadatos, "
    "márcalo. Devuelve JSON con: titulo, enfoque, brief, preguntas, fuentes, verificaciones, guion, "
    "copy_digital, afirmaciones[{texto,tipo,evidencia_id,campo}], vacios[]."
)


def generar_paquete(evento: dict, conn, llm_cfg: dict | None = None) -> dict:
    """Genera brief + guion + copy (LLM si hay proveedor; si no, plantilla extractiva)."""
    plantilla_args = {"evento": evento, "afirmaciones": [], "contexto": evento.get("contexto", [])}
    return _llm.generar(
        conn,
        evento,
        esquema=PaqueteEditorial,
        system_prompt=_SYSTEM,
        plantilla=generar_editorial,
        plantilla_args=plantilla_args,
        llm_cfg=llm_cfg,
        limites={"brief": 250, "copy_digital": 80},
        lente="editorial",
    )
