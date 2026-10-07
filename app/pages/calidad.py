"""Calidad y pruebas (F-19): qué datos hay, cuántos, y qué se descartó."""

from __future__ import annotations

import json

import streamlit as st

import config.settings as S
from app.db_ui import conectar, sin_datos


def render(lente: str) -> None:
    st.subheader("Calidad y pruebas")
    st.caption(
        "Aquí ves el **estado del snapshot**: cuántos registros hay de cada tipo, qué se "
        "descartó en cuarentena (T01) y el resumen de calidad e integridad (manifest)."
    )
    if sin_datos():
        return

    conn = conectar()
    conteos = {}
    for tabla in (
        "fuente",
        "noticia",
        "serie_oficial",
        "indicador",
        "sismo",
        "evento",
        "cuarentena",
    ):
        conteos[tabla] = conn.execute(f"SELECT COUNT(*) c FROM {tabla}").fetchone()[0]
    conn.close()

    cols = st.columns(4)
    nombres = {
        "fuente": "Fuentes",
        "noticia": "Noticias",
        "serie_oficial": "Series oficiales",
        "indicador": "Indicadores",
        "sismo": "Sismos",
        "evento": "Eventos",
        "cuarentena": "En cuarentena",
    }
    for i, (tabla, n) in enumerate(conteos.items()):
        cols[i % 4].metric(nombres[tabla], n)

    # Cuarentena: qué se descartó y por qué.
    if conteos["cuarentena"]:
        st.markdown("#### Registros en cuarentena (se descartan, no bloquean la carga)")
        conn = conectar()
        filas = conn.execute(
            "SELECT motivo, COUNT(*) n FROM cuarentena GROUP BY motivo ORDER BY n DESC"
        ).fetchall()
        conn.close()
        st.table([{"motivo": r[0], "cantidad": r[1]} for r in filas])

    calidad = S.REPORTS_DIR / "calidad_v1.json"
    if calidad.exists():
        with st.expander("Reporte de calidad completo (JSON)"):
            st.json(json.loads(calidad.read_text(encoding="utf-8")))

    manifest = S.MANIFEST_PATH
    if manifest.exists():
        with st.expander("manifest.json (hashes SHA-256 e integridad)"):
            st.json(json.loads(manifest.read_text(encoding="utf-8")))
