"""FARO — interfaz Streamlit.

Barra lateral: lente, proveedor y clave (solo en memoria), modo (usuario/local/auto)
y fecha de referencia. Siete vistas: Bandeja, Ficha, Paquete, Agente, Grafo,
Comparador y Calidad.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="FARO · Copiloto de inteligencia informativa", layout="wide")

from app.pages import agente, bandeja, calidad, comparador, ficha, grafo, paquete  # noqa: E402

VISTAS = {
    "Bandeja": bandeja.render,
    "Ficha": ficha.render,
    "Paquete editorial / Boletín": paquete.render,
    "Agente": agente.render,
    "Grafo": grafo.render,
    "Comparador": comparador.render,
    "Calidad": calidad.render,
}

# --- Barra lateral ----------------------------------------------------------
with st.sidebar:
    st.title("FARO")
    st.caption("No escribe noticias. Dice qué se sabe, de dónde y qué falta.")
    lente = st.radio("Lente", ["editorial", "banca"], horizontal=True)
    modo = st.radio("Modo LLM", ["auto", "usuario", "local"], horizontal=True)

    with st.expander("Proveedor y clave (BYOK)"):
        proveedor = st.text_input("Proveedor", placeholder="anthropic / openai / deepseek")
        modelo = st.text_input("Modelo", placeholder="claude-sonnet-4 / gpt-4o ...")
        api_key = st.text_input(
            "API key", type="password", help="Vive solo en st.session_state; nunca en disco."
        )
        if api_key:
            st.session_state["faro_api_key"] = api_key
    st.caption("Fecha de referencia: 2026-09-30 23:59 (Panamá)")

    if st.button("Recargar datos"):
        st.cache_resource.clear()
        st.rerun()

# --- Navegación -------------------------------------------------------------
vista = st.radio("Vista", list(VISTAS.keys()), horizontal=True)
VISTAS[vista](lente)
