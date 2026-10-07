"""Contexto oficial (F-06): enlaza evento -> serie/indicador/sismo solo si hay regla."""

from __future__ import annotations

import sqlite3

from faro.loaders import load_mapas


def _evidence_id_serie(row: dict) -> str:
    return f"OF:{row['fuente_id']}:{row['serie']}:{row['periodo']}"


def _evidence_id_indicador(row: dict) -> str:
    return f"WB:{row['pais_iso3']}:{row['indicador_id']}:{row['anio']}"


def _evidence_id_sismo(row: dict) -> str:
    return f"USGS:{row['id']}#mag"


def enlazar_contexto(tema: str, conn: sqlite3.Connection) -> list[dict]:
    """Devuelve [{evidencia_id, motivo_enlace}] para un tema, sin forzar."""
    reglas = load_mapas()["reglas"]
    regla = reglas.get(tema)
    if not regla:
        return []
    motivo = regla.get("motivo", "")
    enlaces: list[dict] = []

    for serie in regla.get("series", []):
        row = conn.execute(
            "SELECT * FROM serie_oficial WHERE serie=? ORDER BY periodo DESC LIMIT 1", (serie,)
        ).fetchone()
        if row:
            d = dict(row)
            enlaces.append({"evidencia_id": _evidence_id_serie(d), "motivo_enlace": motivo})

    for ind in regla.get("indicadores", []):
        row = conn.execute(
            "SELECT * FROM indicador WHERE pais_iso3='PAN' AND indicador_id=? ORDER BY anio DESC LIMIT 1",
            (ind,),
        ).fetchone()
        if row:
            d = dict(row)
            enlaces.append({"evidencia_id": _evidence_id_indicador(d), "motivo_enlace": motivo})

    if regla.get("sismos"):
        rows = conn.execute(
            "SELECT * FROM sismo WHERE magnitud>=3.5 ORDER BY fecha DESC LIMIT 3"
        ).fetchall()
        for row in rows:
            d = dict(row)
            enlaces.append({"evidencia_id": _evidence_id_sismo(d), "motivo_enlace": motivo})

    return enlaces
