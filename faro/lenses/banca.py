"""Lente bancario: sectores (B-02) y boletín generado con LLM (M3)."""

from __future__ import annotations

from faro.lenses import _llm
from faro.llm.extractive import generar_boletin
from faro.loaders import load_sectores
from schemas import Boletin

_SYSTEM = (
    "Redacta un boletín de entorno bancario. Solo afirma lo que esté en <datos>; cada afirmación "
    "con su evidencia_id. Separa observación de hipótesis de impacto (siempre marcada). Resumen ≤ 250 "
    "palabras, 3 preguntas. NO recomiendes compra/venta ni infieras pérdidas, impagos, cartera o "
    "riesgo de clientes. Devuelve JSON con: resumen, sectores, horizonte, evidencia, preguntas, "
    "afirmaciones[], observaciones[], hipotesis[]."
)


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


def generar_boletin_sectorial(evento: dict, conn, llm_cfg: dict | None = None) -> dict:
    """Genera el boletín (LLM si hay proveedor; si no, plantilla extractiva)."""
    sectores = mapear_sectores(evento, evento.get("noticias", []))
    nombres = [s["nombre"] for s in sectores]
    plantilla_args = {"evento": evento, "afirmaciones": [], "sectores": nombres}
    return _llm.generar(
        conn,
        evento,
        esquema=Boletin,
        system_prompt=_SYSTEM,
        plantilla=generar_boletin,
        plantilla_args=plantilla_args,
        llm_cfg=llm_cfg,
        limites={"resumen": 250},
        lente="banca",
    )
