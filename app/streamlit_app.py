"""FARO — interfaz Streamlit.

Barra lateral: vista, lente, proveedor y clave (solo en memoria), modo (usuario/local/auto)
y fecha de referencia. Siete vistas: Bandeja, Ficha, Paquete, Agente, Grafo,
Comparador y Calidad.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="FARO · Copiloto de inteligencia informativa", layout="wide")

from app.db_ui import db_existe  # noqa: E402
from app.views import agente, bandeja, calidad, comparador, ficha, grafo, paquete  # noqa: E402

VISTAS = {
    "📥 Bandeja": bandeja.render,
    "🗂️ Ficha": ficha.render,
    "📝 Paquete / Boletín": paquete.render,
    "🤖 Agente": agente.render,
    "🕸️ Grafo": grafo.render,
    "⚖️ Comparador": comparador.render,
    "🧪 Calidad": calidad.render,
}

# --- Barra lateral ----------------------------------------------------------
with st.sidebar:
    st.title("FARO")
    st.caption("No escribe noticias. Dice qué se sabe, de dónde y qué falta.")
    vista = st.radio("Vista", list(VISTAS.keys()))
    st.divider()
    lente = st.radio("Lente", ["editorial", "banca"], horizontal=True)

    if lente == "editorial":
        st.caption(
            "**Lente editorial (TVN):** agenda priorizada, ficha de investigación y "
            "borradores (brief, guion y copy) para el editor."
        )
    else:
        st.caption(
            "**Lente bancario:** boletín de entorno con sectores, horizonte y "
            "preguntas para un analista. No evalúa clientes ni recomienda compra/venta."
        )

    modo = st.radio("Modo LLM", ["auto", "usuario", "local"], horizontal=True)

    with st.expander("Proveedor y clave (BYOK)"):
        proveedor = st.text_input("Proveedor", placeholder="anthropic / openai / deepseek")
        modelo = st.text_input("Modelo", placeholder="claude-sonnet-4 / gpt-4o ...")
        api_key = st.text_input(
            "API key", type="password", help="Vive solo en st.session_state; nunca en disco."
        )
        base_url = st.text_input(
            "Base URL (opcional)", placeholder="solo endpoints compatibles OpenAI"
        )

    # La clave y el proveedor viven solo en st.session_state (nunca en disco, D-12).
    st.session_state["llm"] = {
        "proveedor": proveedor.strip() or None,
        "modelo": modelo.strip() or None,
        "api_key": api_key.strip() or None,
        "base_url": base_url.strip() or None,
        "modo": modo,
    }
    if st.session_state["llm"]["proveedor"] and st.session_state["llm"]["modelo"]:
        st.caption(f"🟢 Modo activo: modelo del usuario ({st.session_state['llm']['proveedor']})")
    elif modo == "local":
        st.caption("🟡 Modo activo: local (Ollama)")
    else:
        st.caption("🟠 Modo activo: respaldo determinista (sin LLM configurado)")
    st.caption("Fecha de referencia: 2026-09-30 23:59 (Panamá)")

    if not db_existe():
        st.warning("⚠️ Sin datos. Corre `make build` (o `docker compose up`) y recarga.")

# --- Vista ------------------------------------------------------------------
VISTAS[vista](lente)
