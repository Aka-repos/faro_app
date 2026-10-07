"""Grafo de procedencias (F-16): agencias → medios → eventos → entidades."""

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
    st.caption(
        "**Agencia → medio → evento → entidad.** El color del evento es el estado de evidencia "
        "(verde=suficiente, ámbar=parcial, rojo=insuficiente). Una agencia replicada por varios "
        "medios cuenta como una sola fuente."
    )
    if sin_datos():
        return
    ev = df_eventos(lente)
    if ev.empty:
        st.info("No hay eventos para este lente.")
        return

    # Selector de evento para que el grafo sea legible (por defecto el top 1).
    opciones = ev["id"].tolist()
    evento_id = st.selectbox(
        "Enfocar evento (evita el 'nudo' de todo el corpus)",
        opciones,
        index=0,
        format_func=lambda i: ev.loc[ev["id"] == i, "titulo_canonico"].iloc[0][:70],
    )

    G = construir_grafo(conectar(), evento_id=evento_id)

    if not _AGRAPH:
        st.info("`streamlit-agraph` no está instalado; mostrando lista de nodos.")
        for n, d in G.nodes(data=True):
            st.markdown(f"- **{d.get('label', n)}** ({d.get('tipo', '?')})")
        return

    nodos = [
        Node(
            id=n,
            label=str(d.get("label", n)),
            color=_color(d),
            size=22 if d.get("tipo") == "evento" else 14,
            title=f"{d.get('tipo', '?')}: {d.get('label', '')}",
        )
        for n, d in G.nodes(data=True)
    ]
    aristas = [Edge(source=s, target=t, label=d.get("rel", "")) for s, t, d in G.edges(data=True)]

    # physics=False: sin animación ni "nudo que da vueltas". Layout jerárquico estable.
    config = Config(
        width=900,
        height=650,
        directed=True,
        physics=False,
        hierarchical=True,
        nodeHighlightBehavior=True,
        highlightColor="#ffeb3b",
    )
    agraph(nodes=nodos, edges=aristas, config=config)
