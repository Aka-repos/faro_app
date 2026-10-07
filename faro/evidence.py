"""Resolución de IDs de evidencia (D-05) a texto citable.

Formato (sección 6):
- N:<id>#<campo>
- OF:<fuente>:<serie>:<periodo>
- WB:<pais>:<indicador>:<año>
- USGS:<id>#<atributo>
- SBP:<periodo>:<serie>#p<pagina>
"""

from __future__ import annotations

import sqlite3


def resolver(conn: sqlite3.Connection, evidencia_id: str) -> str | None:
    """Devuelve el texto/dato citado para un ID de evidencia, o None."""
    if not evidencia_id:
        return None
    try:
        if evidencia_id.startswith("N:"):
            nid, _, campo = evidencia_id[2:].partition("#")
            row = conn.execute("SELECT * FROM noticia WHERE id=?", (nid,)).fetchone()
            if not row:
                return None
            return str(dict(row).get(campo or "titulo", ""))
        if evidencia_id.startswith("OF:"):
            _, fuente, serie, periodo = evidencia_id.split(":")
            row = conn.execute(
                "SELECT * FROM serie_oficial WHERE fuente_id=? AND serie=? AND periodo=?",
                (fuente, serie, periodo),
            ).fetchone()
            if not row:
                return None
            d = dict(row)
            return f"{d['serie']} {d['periodo']}: {d['valor']} {d['unidad'] or ''}".strip()
        if evidencia_id.startswith("WB:"):
            _, pais, ind, anio = evidencia_id.split(":")
            row = conn.execute(
                "SELECT * FROM indicador WHERE pais_iso3=? AND indicador_id=? AND anio=?",
                (pais, ind, int(anio)),
            ).fetchone()
            if not row:
                return None
            d = dict(row)
            return f"{d['pais_iso3']} {d['indicador_id']} {d['anio']}: {d['valor']} {d['unidad'] or ''}".strip()
        if evidencia_id.startswith("USGS:"):
            sid, _, attr = evidencia_id[5:].partition("#")
            row = conn.execute("SELECT * FROM sismo WHERE id=?", (sid,)).fetchone()
            if not row:
                return None
            return str(dict(row).get(attr or "magnitud", ""))
        if evidencia_id.startswith("SBP:"):
            periodo_serie, _, pagina = evidencia_id[4:].partition("#p")
            periodo, _, serie = periodo_serie.partition(":")
            row = conn.execute(
                "SELECT * FROM serie_oficial WHERE fuente_id='sbp' AND serie=? AND periodo=?",
                (serie, periodo),
            ).fetchone()
            if not row:
                return None
            d = dict(row)
            return (
                f"SBP {serie} {periodo}: {d['valor']} {d['unidad'] or ''} (p. {d['pagina'] or '?'})"
            )
    except Exception:  # noqa: BLE001
        return None
    return None
