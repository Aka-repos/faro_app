"""Métricas (F-15, sección 9.1): numerador/denominador + lista de fallos."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import config.settings as S


def cobertura_citas(afirmaciones: list[dict]) -> dict:
    total = len(afirmaciones)
    if total == 0:
        return {
            "metrica": "cobertura_citas",
            "numerador": 0,
            "denominador": 0,
            "valor": None,
            "nota": "0/0 · sin datos",
            "fallos": [],
        }
    con_evidencia = sum(1 for a in afirmaciones if a.get("evidencia_id"))
    return {
        "metrica": "cobertura_citas",
        "numerador": con_evidencia,
        "denominador": total,
        "valor": (con_evidencia / total),
        "fallos": [a for a in afirmaciones if not a.get("evidencia_id")],
    }


def latencia(casos: list[dict]) -> dict:
    """Mediana y p95 de latencia (ms) sobre los casos con latencia registrada."""
    import statistics

    vals = sorted(c.get("latencia_ms") for c in casos if c.get("latencia_ms") is not None)
    if not vals:
        return {"metrica": "latencia", "n": 0, "mediana_ms": None, "p95_ms": None}
    p95 = vals[int(len(vals) * 0.95) - 1] if len(vals) >= 20 else vals[-1]
    return {
        "metrica": "latencia",
        "n": len(vals),
        "mediana_ms": statistics.median(vals),
        "p95_ms": p95,
    }


def abstencion(casos: list[dict]) -> dict:
    """Abstención correcta (en 'sin respuesta') e incorrecta (en 'sustentada').

    Los casos 'contradiccion' y 'adversarial' se miden aparte (no son errores de
    abstención; en adversarial, rechazar/abstenerse es el comportamiento correcto).
    """
    correctas, incorrectas = 0, 0
    fallos = []
    total_sin_respuesta = 0
    for c in casos:
        t = c.get("tipo")
        if t == "sin_respuesta":
            total_sin_respuesta += 1
            if c.get("abstuvo"):
                correctas += 1
            else:
                fallos.append({"id": c.get("id"), "tipo": "abstencion_faltante"})
        elif t == "sustentada":
            if c.get("abstuvo"):
                incorrectas += 1
                fallos.append({"id": c.get("id"), "tipo": "abstencion_incorrecta"})
    return {
        "metrica": "abstencion",
        "abstencion_correcta": (correctas / total_sin_respuesta) if total_sin_respuesta else 0.0,
        "abstencion_incorrecta": incorrectas,
        "fallos": fallos,
    }


def validez_sustento(revisiones: list[dict]) -> dict:
    """Revisión humana de afirmaciones: válidas / total."""
    total = len(revisiones)
    validas = sum(1 for r in revisiones if r.get("valida"))
    return {
        "metrica": "validez_sustento",
        "numerador": validas,
        "denominador": total,
        "valor": (validas / total) if total else 0.0,
        "fallos": [r for r in revisiones if not r.get("valida")],
    }


def escribir_metricas(metricas: dict) -> str:
    S.ensure_dirs()
    fecha = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    path = S.REPORTS_DIR / f"metrics_{fecha}.json"
    path.write_text(
        json.dumps(metricas, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    _escribir_md(metricas, S.REPORTS_DIR / f"metrics_{fecha}.md")
    return str(path)


def _escribir_md(metricas: dict, path) -> None:
    """Tabla Markdown con numerador/denominador + fallos (WP-5)."""
    lineas = ["# Métricas de la ejecución", "", "| Métrica | Resultado |", "| --- | --- |"]
    abst = metricas.get("abstencion", {})
    if abst:
        lineas.append(f"| Abstención correcta | {abst.get('abstencion_correcta', 0):.2%} |")
        lineas.append(f"| Abstención incorrecta | {abst.get('abstencion_incorrecta', 0)} |")
    cob = metricas.get("cobertura_citas", {})
    if cob:
        lineas.append(
            f"| Cobertura de citas | {cob.get('numerador', 0)}/{cob.get('denominador', 0)} |"
        )
    lineas.append("")
    fallos = (abst.get("fallos") or []) + (cob.get("fallos") or [])
    if fallos:
        lineas.append("## Fallos")
        lineas.append("")
        for f in fallos:
            lineas.append(f"- {f}")
    path.write_text("\n".join(lineas), encoding="utf-8")
