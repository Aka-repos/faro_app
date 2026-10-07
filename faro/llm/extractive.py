"""Modo extractivo (F-10, L-04): generación sin LLM a partir de afirmaciones verificadas.

Siempre funciona, nunca alucina y sirve de baseline de generación. No usa ningún
modelo: rellena una plantilla con hechos ya validados por el verificador.
"""

from __future__ import annotations


def generar_editorial(evento: dict, afirmaciones: list[dict], contexto: list[dict]) -> dict:
    """Paquete editorial extractivo a partir de afirmaciones verificadas."""
    hechos = [a["texto"] for a in afirmaciones if a.get("tipo") in ("hecho", "observacion")]
    inferencias = [a["texto"] for a in afirmaciones if a.get("tipo") in ("inferencia", "hipotesis")]
    citas = [a.get("evidencia_id", "") for a in afirmaciones if a.get("evidencia_id")]

    titulo = evento.get("titulo_canonico", "Evento sin título")
    brief = (
        f"Tema: {evento.get('tema', '')}. {evento.get('n_menciones', 0)} menciones en "
        f"{evento.get('n_medios', 0)} medios y {evento.get('n_procedencias', 0)} procedencias "
        f"independientes. Hechos verificados: {' '.join(hechos[:4]) or 'ninguno disponible.'}"
    )[:250]
    guion = (
        f"En este evento, {' '.join(hechos[:3]) or 'aún no hay hechos verificados'}."
        f" Verificación pendiente: {len(inferencias)} inferencias por confirmar."
    )
    copy = (titulo + ". " + " ".join(hechos[:2]))[:80]
    return {
        "titulo": titulo,
        "enfoque": f"Interés público en {evento.get('tema', '')}.",
        "brief": brief,
        "preguntas": [
            a.get("evidencia_faltante", "") for a in afirmaciones if a.get("tipo") == "inferencia"
        ][:3]
        or ["¿Qué falta verificar?"],
        "fuentes": citas,
        "verificaciones": ["Confirmar cifras con fuente primaria."],
        "guion": guion,
        "copy_digital": copy,
        "afirmaciones": afirmaciones,
        "vacios": [
            {"descripcion": a["texto"], "evidencia_faltante": "confirmar"}
            for a in afirmaciones
            if a.get("tipo") == "inferencia"
        ],
        "basado_solo_titular": evento.get("alcance_texto") == "titular",
    }


def generar_boletin(evento: dict, afirmaciones: list[dict], sectores: list[str]) -> dict:
    """Boletín bancario extractivo."""
    observaciones = [a["texto"] for a in afirmaciones if a.get("tipo") == "observacion"]
    hipotesis = [a["texto"] for a in afirmaciones if a.get("tipo") == "hipotesis"]
    resumen = (
        f"Señal del entorno sobre {evento.get('tema', '')}. "
        f"{' '.join(observaciones[:4]) or 'Sin observaciones verificadas.'}"
    )[:250]
    return {
        "resumen": resumen,
        "sectores": sectores,
        "horizonte": "Corto plazo (1–3 meses), sujeto a confirmación.",
        "evidencia": [a.get("evidencia_id", "") for a in afirmaciones if a.get("evidencia_id")],
        "preguntas": [
            "¿Cuál es la tendencia mensual de la serie oficial?",
            "¿Qué fuente primaria confirma el dato?",
            "¿Hay señal de impacto sectorial?",
        ],
        "afirmaciones": afirmaciones,
        "observaciones": observaciones,
        "hipotesis": hipotesis,
    }
