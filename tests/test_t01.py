"""T01 — Fechas inválidas y nulos: separa errores, conserva nulos, no bloquea."""

from __future__ import annotations

from faro.quality.validate import validar_noticia, validar_todo


def test_fecha_invalida_a_cuarentena():
    raw = {
        "tipo": "noticia",
        "id": "x",
        "fuente_id": "tvn",
        "titulo": "t",
        "url": "https://a.b/c",
        "medio": "TVN",
        "fecha_publicacion": "no-es-fecha",
    }
    rec, motivo = validar_noticia(raw)
    assert rec is None
    assert motivo == "fecha_publicacion_invalida"


def test_nulos_se_conservan():
    raw = {
        "tipo": "noticia",
        "id": "y",
        "fuente_id": "tvn",
        "titulo": "t",
        "url": "https://a.b/d",
        "medio": "TVN",
        "fecha_publicacion": "2026-01-15T00:00:00+00:00",
        "resumen": None,
        "fecha_deteccion": None,
    }
    rec, motivo = validar_noticia(raw)
    assert rec is not None and motivo is None
    assert rec["resumen"] is None  # no rellenado con cero/vacío


def test_carga_no_se_bloquea():
    raw = {
        "noticia": [
            {
                "tipo": "noticia",
                "id": "a",
                "fuente_id": "tvn",
                "titulo": "ok",
                "url": "https://a.b/1",
                "medio": "TVN",
                "fecha_publicacion": "2026-01-15T00:00:00+00:00",
            },
            {
                "tipo": "noticia",
                "id": "b",
                "fuente_id": "tvn",
                "titulo": "mala",
                "url": "https://a.b/2",
                "medio": "TVN",
                "fecha_publicacion": "INVALIDA",
            },
        ],
        "serie_oficial": [],
        "indicador": [],
        "sismo": [],
    }
    res = validar_todo(raw)
    assert len(res["noticia"]) == 1  # la válida
    assert len(res["cuarentena"]) == 1  # la inválida separada
    assert res["cuarentena"][0]["motivo"] == "fecha_publicacion_invalida"
