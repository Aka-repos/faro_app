"""Grafo de procedencias (F-16)."""

from __future__ import annotations

import streamlit as st

from app.db_ui import conectar, df_eventos
from faro.events.graph import construir_grafo


def render(lente: str) -> None:
    st.subheader("Grafo de procedencias")
    try:
        ev = df_eventos(lente)
    except Exception:  # noqa: BLE001
        st.info("No hay datos. Corre `make build`.")
        return
    if ev.empty:
        st.info("Sin eventos.")
        return
    G = construir_grafo(conectar())
    st.caption(f"Nodos: {G.number_of_nodes()} · Aristas: {G.number_of_edges()}")
    st.markdown(
        "**Medios / agencias → evento → entidades.** Color del evento = estado de evidencia."
    )
    nodos = []
    for n, d in G.nodes(data=True):
        nodos.append(f"• {d.get('label', n)} ({d.get('tipo', '?')})")
    st.text("\n".join(nodos[:40]))
    st.info(
        "Para una vista interactiva completa usa `streamlit-agraph` (se degrada a lista si no está instalado)."
    )
