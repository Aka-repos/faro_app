"""Bandeja de agenda (E-01): top priorizado con puntaje y semáforo de evidencia."""

from __future__ import annotations

import streamlit as st

from app.db_ui import df_eventos, sin_datos, tema_label, top_diverso
from faro.loaders import load_lente


def render(lente: str) -> None:
    if lente == "banca":
        st.subheader("Señales sectoriales (lente bancario)")
        st.caption(
            "Misma bandeja, con pesos bancarios: señales del entorno por sector "
            "(logística, turismo, energía…). No es un score de clientes."
        )
    else:
        st.subheader("Bandeja de agenda")
    if sin_datos():
        return
    ev = df_eventos(lente)
    if ev.empty:
        st.info("No hay eventos para este lente.")
        return
    max_por_tema = int(load_lente(lente).get("diversidad", {}).get("max_por_tema", 3))
    top, diversidad_aplicada = top_diverso(ev, max_por_tema, n=10)
    if diversidad_aplicada:
        st.caption(f"diversidad aplicada: máximo {max_por_tema} eventos por tema")
    for _, r in top.iterrows():
        color = {"alto": "#c62828", "medio": "#f9a825", "bajo": "#2e7d32"}[r["rango"]]
        st.markdown(
            f"**P={r['P']}** · <span style='color:{color}'>● {r['rango']}</span> · "
            f"evidencia: **{r['estado_evidencia']}**<br>{r['titulo_canonico']}",
            unsafe_allow_html=True,
        )
        st.caption(
            f"{r['n_menciones']} menciones · {r['n_medios']} medios · "
            f"{r['n_procedencias']} procedencias · {tema_label(r['tema'])}"
        )
        st.divider()
