"""T09 — Brief/boletín: formato útil, citas pertinentes, hechos vs. inferencias."""

from __future__ import annotations

from faro.llm.extractive import generar_boletin, generar_editorial


def _evento():
    return {
        "id": "ev-1",
        "tema": "economia",
        "titulo_canonico": "Inflación de Panamá se modera",
        "n_menciones": 3,
        "n_medios": 3,
        "n_procedencias": 2,
    }


def _afirmaciones():
    return [
        {
            "texto": "Inflación interanual 2.1% (FP.CPI.TOTL.ZG, 2024)",
            "tipo": "hecho",
            "evidencia_id": "WB:PAN:FP.CPI.TOTL.ZG:2024",
            "campo": "valor",
        },
        {
            "texto": "La tendencia podría continuar a la baja",
            "tipo": "inferencia",
            "evidencia_id": None,
            "campo": None,
        },
    ]


def test_brief_dentro_de_limite():
    out = generar_editorial(_evento(), _afirmaciones(), [])
    assert len(out["brief"].split()) <= 250
    assert len(out["copy_digital"].split()) <= 80


def test_distingue_hechos_de_inferencias():
    out = generar_editorial(_evento(), _afirmaciones(), [])
    hechos = [a for a in out["afirmaciones"] if a["tipo"] == "hecho"]
    inferencias = [a for a in out["afirmaciones"] if a["tipo"] == "inferencia"]
    assert hechos and inferencias


def test_boletin_separa_observacion_e_hipotesis():
    afirm = [
        {
            "texto": "Tránsito del Canal subió 4% en agosto",
            "tipo": "observacion",
            "evidencia_id": "OF:acp:acp_transitos:2026-08",
            "campo": "valor",
        },
        {"texto": "Podría presionar tarifas logísticas", "tipo": "hipotesis", "evidencia_id": None},
    ]
    out = generar_boletin(_evento(), afirm, ["Logística y transporte"])
    assert out["observaciones"]
    assert out["hipotesis"]
    assert len(out["resumen"].split()) <= 250
    assert len(out["preguntas"]) == 3
