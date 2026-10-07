"""Preguntar al agente (F-08, E-04) con traza visible."""

from __future__ import annotations

import streamlit as st

from faro import db
from faro.agent import loop


def render(lente: str) -> None:
    st.subheader("Preguntar al agente")
    st.caption(
        "Herramientas de solo lectura. La respuesta pasa por el verificador; sin evidencia se abstiene."
    )
    pregunta = st.text_input(
        "Pregunta en español", placeholder="¿Qué cinco temas merecen revisión hoy y por qué?"
    )
    if st.button("Consultar") and pregunta:
        conn = db.connect()
        contexto = {"vista": "Agente", "lente": lente}
        try:
            r = loop.consultar(pregunta, conn, lente=lente, contexto=contexto)
        except Exception as e:  # noqa: BLE001
            st.error(str(e))
            conn.close()
            return
        conn.close()
        if r["abstencion"]:
            st.warning("⚠️ Abstención: " + r["respuesta"])
        else:
            st.markdown(r["respuesta"])
        st.markdown("#### Traza del agente")
        for t in r["traza"]:
            st.markdown(
                f"- paso {t['paso']}: `{t['herramienta']}` {t.get('argumentos', {})} → {t.get('n_resultados', 0)} resultados"
            )
