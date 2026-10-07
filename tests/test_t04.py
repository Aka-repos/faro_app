"""T04 — Cifra anual del Banco Mundial: país, año y unidad; nunca "de hoy"."""

from __future__ import annotations

from faro import db
from faro.agent import loop


def test_indicador_con_pais_anio_unidad(conn):
    rows = db.fetchall(
        conn,
        "SELECT * FROM indicador WHERE pais_iso3='PAN' AND indicador_id='NY.GDP.MKTP.KD.ZG' ORDER BY anio DESC LIMIT 1",
    )
    assert rows
    r = rows[0]
    assert r["pais_iso3"] == "PAN"
    assert r["anio"] >= 2010
    assert r["unidad"]  # unidad presente


def test_respuesta_nunca_como_hoy(conn):
    r = loop.consultar("¿Cuál fue el crecimiento del PIB de Panamá según el Banco Mundial?", conn)
    assert not r["abstencion"]
    assert "anual" in r["respuesta"].lower()
    assert "no una medición de hoy" in r["respuesta"].lower()
    assert "hoy" not in r["respuesta"].lower().replace("no una medición de hoy", "")
