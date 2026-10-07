"""Grafo de procedencias (F-16) con estética tipo Obsidian: nodos-punto, color por
tipo/estado, etiqueta al pasar el cursor y física forceAtlas2 que se asienta suave.
"""

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
    "medio": "#5B8DEF",
    "agencia": "#B07CD8",
    "entidad": "#2CA6A4",
}
COLOR_EVIDENCIA = {
    "suficiente para el borrador": "#4CAF50",
    "parcial": "#F5B041",
    "insuficiente": "#E74C3C",
}


def _color(d: dict) -> str:
    if d.get("tipo") == "evento":
        return COLOR_EVIDENCIA.get(d.get("estado", ""), "#E8A33D")
    return COLOR_TIPO.get(d.get("tipo", ""), "#9E9E9E")


def _config_obsidian() -> Config:
    """Física forceAtlas2 suave (estilo Obsidian): se asienta, no da vueltas."""
    config = Config(
        width=900,
        height=640,
        directed=True,
        physics=True,
        nodeHighlightBehavior=True,
        highlightColor="#FFD54F",
    )
    # Reemplazamos el dict de física por la estructura correcta de vis-network.
    config.physics = {
        "enabled": True,
        "solver": "forceAtlas2Based",
        "forceAtlas2Based": {
            "gravitationalConstant": -70,
            "centralGravity": 0.02,
            "springLength": 100,
            "springConstant": 0.05,
            "damping": 0.45,
            "avoidOverlap": 0.35,
        },
        "minVelocity": 0.4,
        "maxVelocity": 20,
        "stabilization": {"enabled": True, "iterations": 250, "updateInterval": 25, "fit": True},
    }
    return config


def render(lente: str) -> None:
    st.subheader("Grafo de procedencias")
    st.caption(
        "Estilo Obsidian: agencia → medio → evento → entidad. Pasa el cursor por un nodo para "
        "ver su detalle. El color del evento es el estado de evidencia."
    )
    if sin_datos():
        return
    ev = df_eventos(lente)
    if ev.empty:
        st.info("No hay eventos para este lente.")
        return

    opciones = ["__todos__"] + ev["id"].tolist()
    evento_id = st.selectbox(
        "Alcance",
        opciones,
        index=0,
        format_func=lambda i: (
            "🕸️ Grafo completo (todo el corpus)"
            if i == "__todos__"
            else ev.loc[ev["id"] == i, "titulo_canonico"].iloc[0][:70]
        ),
    )

    G = construir_grafo(conectar(), evento_id=None if evento_id == "__todos__" else evento_id)

    if not _AGRAPH:
        st.info("`streamlit-agraph` no está instalado; mostrando lista de nodos.")
        for n, d in G.nodes(data=True):
            st.markdown(f"- **{d.get('label', n)}** ({d.get('tipo', '?')})")
        return

    # Nodos-punto: tamaño según conexiones; etiqueta solo en eventos (los "hubs").
    grados = dict(G.degree())
    nodos = []
    for n, d in G.nodes(data=True):
        tipo = d.get("tipo", "?")
        label = str(d.get("label", ""))[:26] if tipo == "evento" else None
        size = 20 if tipo == "evento" else 9 + min(grados.get(n, 0), 10) * 1.4
        nodos.append(
            Node(
                id=n,
                title=f"{tipo}: {d.get('label', '')}",
                label=label,
                color=_color(d),
                size=size,
                shape="dot",
                font={"color": "#ffffff", "size": 12, "strokeWidth": 3, "strokeColor": "#222222"},
            )
        )

    aristas = [Edge(source=s, target=t, color="#B0BEC5") for s, t in G.edges()]

    agraph(nodes=nodos, edges=aristas, config=_config_obsidian())

    st.caption(
        "**Leyenda:** 🟣 agencia · 🔵 medio · 🟢 evento (suficiente) · 🟠 evento (parcial) · 🔴 evento (insuficiente) · 🩵 entidad"
    )
