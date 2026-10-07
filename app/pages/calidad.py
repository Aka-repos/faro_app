"""Calidad y pruebas (F-19, catálogo)."""

from __future__ import annotations

import json

import streamlit as st

import config.settings as S
from app.db_ui import conectar


def render(lente: str) -> None:
    st.subheader("Calidad y pruebas")
    conn = conectar()
    try:
        for tabla in (
            "fuente",
            "noticia",
            "serie_oficial",
            "indicador",
            "sismo",
            "evento",
            "cuarentena",
        ):
            n = conn.execute(f"SELECT COUNT(*) c FROM {tabla}").fetchone()[0]
            st.markdown(f"- **{tabla}**: {n}")
    except Exception as e:  # noqa: BLE001
        st.error(str(e))

    calidad = S.REPORTS_DIR / "calidad_v1.json"
    if calidad.exists():
        st.markdown("#### Reporte de calidad")
        st.json(json.loads(calidad.read_text(encoding="utf-8")))

    manifest = S.MANIFEST_PATH
    if manifest.exists():
        with st.expander("manifest.json"):
            st.json(json.loads(manifest.read_text(encoding="utf-8")))
