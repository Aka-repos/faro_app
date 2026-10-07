"""Bandeja de agenda (E-01): top priorizado con puntaje y semáforo de evidencia."""

from __future__ import annotations

import streamlit as st

from app.db_ui import df_eventos, sin_datos


def render(lente: str) -> None:
    st.subheader("Bandeja de agenda")
    if sin_datos():
        return
    ev = df_eventos(lente)
    if ev.empty:
        st.info("No hay eventos para este lente.")
        return
    for _, r in ev.head(10).iterrows():
        color = {"alto": "#c62828", "medio": "#f9a825", "bajo": "#2e7d32"}[r["rango"]]
        st.markdown(
            f"**P={r['P']}** · <span style='color:{color}'>● {r['rango']}</span> · "
            f"evidencia: **{r['estado_evidencia']}**<br>{r['titulo_canonico']}",
            unsafe_allow_html=True,
        )
        st.caption(
            f"{r['n_menciones']} menciones · {r['n_medios']} medios · "
            f"{r['n_procedencias']} procedencias · {r['tema']}"
        )
        st.divider()
