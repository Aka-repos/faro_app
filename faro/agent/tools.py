"""Herramientas de solo lectura sobre faro.db (F-08, sección 7.3).

Ninguna herramienta escribe datos, publica ni accede a secretos. Lo que devuelven
se marca como datos, nunca como instrucciones.
"""

from __future__ import annotations

from faro import db


def _rows(conn, sql, params=()):
    return db.fetchall(conn, sql, params)


def buscar_noticias(conn, q="", desde=None, hasta=None, tema=None, limite=20) -> list[dict]:
    sql = "SELECT * FROM noticia WHERE 1=1"
    params: list = []
    if q:
        sql += " AND (titulo LIKE ? OR resumen LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    if desde:
        sql += " AND fecha_publicacion >= ?"
        params.append(desde)
    if hasta:
        sql += " AND fecha_publicacion <= ?"
        params.append(hasta)
    if tema:
        sql += " AND tema = ?"
        params.append(tema)
    sql += " ORDER BY fecha_publicacion DESC LIMIT ?"
    params.append(limite)
    return _rows(conn, sql, tuple(params))


def abrir_evento(conn, evento_id: str) -> dict | None:
    rows = _rows(conn, "SELECT * FROM evento WHERE id=?", (evento_id,))
    if not rows:
        return None
    ev = rows[0]
    ev["noticias"] = _rows(
        conn,
        "SELECT n.* FROM noticia n JOIN evento_noticia en ON n.id=en.noticia_id WHERE en.evento_id=?",
        (evento_id,),
    )
    ev["contexto"] = _rows(conn, "SELECT * FROM evento_contexto WHERE evento_id=?", (evento_id,))
    ev["puntajes"] = _rows(conn, "SELECT * FROM evento_puntaje WHERE evento_id=?", (evento_id,))
    return ev


def ver_procedencias(conn, evento_id: str) -> dict:
    ev = abrir_evento(conn, evento_id)
    if not ev:
        return {"evento_id": evento_id, "n_menciones": 0, "n_medios": 0, "n_procedencias": 0}
    return {
        "evento_id": evento_id,
        "n_menciones": ev.get("n_menciones", 0),
        "n_medios": ev.get("n_medios", 0),
        "n_procedencias": ev.get("n_procedencias", 0),
    }


def consultar_indicador(conn, pais="PAN", indicador="NY.GDP.MKTP.KD.ZG", anio=None) -> list[dict]:
    sql = "SELECT * FROM indicador WHERE pais_iso3=? AND indicador_id=?"
    params: list = [pais, indicador]
    if anio is not None:
        sql += " AND anio=?"
        params.append(anio)
    sql += " ORDER BY anio DESC LIMIT 5"
    return _rows(conn, sql, tuple(params))


def consultar_serie(conn, fuente=None, serie=None, periodo=None) -> list[dict]:
    sql = "SELECT * FROM serie_oficial WHERE 1=1"
    params: list = []
    if fuente:
        sql += " AND fuente_id=?"
        params.append(fuente)
    if serie:
        sql += " AND serie=?"
        params.append(serie)
    if periodo:
        sql += " AND periodo=?"
        params.append(periodo)
    sql += " ORDER BY periodo DESC LIMIT 12"
    return _rows(conn, sql, tuple(params))


def consultar_sbp(conn, serie=None, periodo=None) -> list[dict]:
    return consultar_serie(conn, fuente="sbp", serie=serie, periodo=periodo)


def buscar_sismos(conn, desde=None, hasta=None, mag_min=3.0, limite=10) -> list[dict]:
    sql = "SELECT * FROM sismo WHERE magnitud>=?"
    params: list = [mag_min]
    if desde:
        sql += " AND fecha>=?"
        params.append(desde)
    if hasta:
        sql += " AND fecha<=?"
        params.append(hasta)
    sql += " ORDER BY fecha DESC LIMIT ?"
    params.append(limite)
    return _rows(conn, sql, tuple(params))


def ranking(conn, lente="editorial", n=5) -> list[dict]:
    rows = _rows(
        conn,
        "SELECT * FROM evento_puntaje WHERE lente=? ORDER BY P DESC, U DESC, evento_id ASC LIMIT ?",
        (lente, n),
    )
    for r in rows:
        ev = _rows(conn, "SELECT titulo_canonico, tema FROM evento WHERE id=?", (r["evento_id"],))
        r["titulo_canonico"] = ev[0]["titulo_canonico"] if ev else ""
        r["tema"] = ev[0]["tema"] if ev else ""
    return rows


# Registro de herramientas disponibles (para el agente y para la UI).
HERRAMIENTAS = {
    "buscar_noticias": buscar_noticias,
    "abrir_evento": abrir_evento,
    "ver_procedencias": ver_procedencias,
    "consultar_indicador": consultar_indicador,
    "consultar_serie": consultar_serie,
    "consultar_sbp": consultar_sbp,
    "buscar_sismos": buscar_sismos,
    "ranking": ranking,
}
