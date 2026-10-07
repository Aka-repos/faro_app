"""Utilidades de UI: apertura de DB y datos para las vistas."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from faro import db


@st.cache_resource
def conectar():
    return db.connect()


def df_noticias():
    return pd.read_sql_query("SELECT * FROM noticia ORDER BY fecha_publicacion DESC", conectar())


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
    return ev
