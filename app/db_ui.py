"""Utilidades de UI: apertura de DB y datos para las vistas.

Abrimos una conexión fresca por consulta (sqlite local es barato) para evitar
problemas de caché/hilos con conexiones persistentes en Streamlit.
"""

from __future__ import annotations

import sqlite3

import pandas as pd

import config.settings as S
from faro import db


def conectar() -> sqlite3.Connection:
    return db.connect()


def db_existe() -> bool:
    """True si la base existe y tiene al menos una noticia."""
    if not S.DB_PATH.exists():
        return False
    try:
        conn = conectar()
        n = conn.execute("SELECT COUNT(*) FROM noticia").fetchone()[0]
        conn.close()
        return n > 0
    except Exception:  # noqa: BLE001
        return False


def df_noticias():
    return pd.read_sql_query(
        "SELECT * FROM noticia ORDER BY COALESCE(fecha_publicacion, fecha_deteccion) DESC",
        conectar(),
    )


def df_eventos(lente="editorial"):
    return pd.read_sql_query(
        """SELECT e.*, p.P, p.rango, p.estado_evidencia
           FROM evento e JOIN evento_puntaje p ON p.evento_id=e.id AND p.lente=?
           ORDER BY p.P DESC, p.U DESC, e.id ASC""",
        conectar(),
        params=(lente,),
    )


def df_puntajes(lente="editorial"):
    return pd.read_sql_query(
        "SELECT * FROM evento_puntaje WHERE lente=?", conectar(), params=(lente,)
    )


def cargar_evento(evento_id):
    conn = conectar()
    ev = pd.read_sql_query("SELECT * FROM evento WHERE id=?", conn, params=(evento_id,)).to_dict(
        "records"
    )
    if not ev:
        conn.close()
        return None
    ev = ev[0]
    ev["noticias"] = pd.read_sql_query(
        "SELECT n.* FROM noticia n JOIN evento_noticia en ON n.id=en.noticia_id WHERE en.evento_id=?",
        conn,
        params=(evento_id,),
    ).to_dict("records")
    ev["contexto"] = pd.read_sql_query(
        "SELECT * FROM evento_contexto WHERE evento_id=?", conn, params=(evento_id,)
    ).to_dict("records")
    ev["puntajes"] = pd.read_sql_query(
        "SELECT * FROM evento_puntaje WHERE evento_id=?", conn, params=(evento_id,)
    ).to_dict("records")
    conn.close()
    return ev


def sin_datos() -> bool:
    """Marca común para vistas que dependen del snapshot."""
    if not db_existe():
        import streamlit as st

        st.warning("Todavía no hay datos. Corre `make build` (o `docker compose up`) primero.")
        return True
    return False
