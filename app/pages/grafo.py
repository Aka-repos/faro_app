"""Grafo de procedencias (F-16): medios, agencias, eventos y entidades (interactivo)."""

from __future__ import annotations

import streamlit as st

from app.db_ui import conectar, df_eventos, sin_datos
from faro.events.graph import construir_grafo

try:
    from streamlit_agraph import Config, Edge, Node, agraph

    _AGRAPH = True
except Exception:  # noqa: BLE001
    _AGRAPH = False

COLOR_TIPO = {
    "medio": "#42a5f5",
    "agencia": "#ab47bc",
    "evento": "#ffa726",
    "entidad": "#66bb6a",
}


def _color(d: dict) -> str:
    if d.get("tipo") == "evento":
        return d.get("color", "#ffa726")
    return COLOR_TIPO.get(d.get("tipo", ""), "#90a4ae")


def render(lente: str) -> None:
    st.subheader("Grafo de procedencias")
    st.caption("Medios / agencias → evento → entidades. El color del evento = estado de evidencia.")
    if sin_datos():
        return
    ev = df_eventos(lente)
    if ev.empty:
        st.info("No hay eventos para este lente.")
        return

    G = construir_grafo(conectar())

    if _AGRAPH:
        nodos = []
        for n, d in G.nodes(data=True):
            nodos.append(
                Node(
                    id=n,
                    label=str(d.get("label", n)),
                    color=_color(d),
                    size=20 if d.get("tipo") == "evento" else 12,
                    shape="dot",
                    title=f"{d.get('tipo', '?')}: {d.get('label', '')}",
                )
            )
        aristas = []
        for s, t, d in G.edges(data=True):
            aristas.append(Edge(source=s, target=t, label=d.get("rel", "")))
        config = Config(
            width=900,
            height=650,
            directed=True,
            physics=True,
            hierarchical=False,
            nodeHighlightBehavior=True,
            highlightColor="#ffeb3b",
            collapsible=True,
        )
        agraph(nodes=nodos, edges=aristas, config=config)
    else:
        st.info("`streamlit-agraph` no está instalado; mostrando lista de nodos.")
        for n, d in G.nodes(data=True):
            st.markdown(f"- **{d.get('label', n)}** ({d.get('tipo', '?')})")
