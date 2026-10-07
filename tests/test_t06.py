"""T06 — Consulta sin respuesta: abstención explícita, nada inventado."""

from __future__ import annotations

from faro.agent import loop


def test_abstencion_sin_respuesta(conn):
    r = loop.consultar("¿Cuál es la cifra exacta de turistas del año 1990 en este corpus?", conn)
    assert r["abstencion"] is True
    assert "evidencia" in r["respuesta"].lower()


def test_no_inventa_citas(conn):
    r = loop.consultar("¿Cuántos tornados hubo en Panamá en 1987?", conn)
    # No debe citar un ID de evidencia inexistente.
    assert "WB:" not in r["respuesta"]
    assert "OF:" not in r["respuesta"]
    assert r["abstencion"] is True
