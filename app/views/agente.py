"""Preguntar al agente (F-08): chat con traza y métricas por respuesta."""

from __future__ import annotations

import time

import streamlit as st

from faro import db
from faro.agent import loop
from faro.llm.gateway import log_ejecucion

_MSGS = "faro_messages"


def _inicializar() -> None:
    if _MSGS not in st.session_state:
        st.session_state[_MSGS] = []


def _meta_caption(meta: dict) -> str:
    return (
        f"⏱ {meta['latencia_ms']} ms · 🔧 {meta['proveedor']}/{meta['modelo']} · "
        f"{meta['pasos']} pasos · lente {meta['lente']}"
    )


def render(lente: str) -> None:
    st.subheader("Preguntar al agente")
    st.caption(
        "Chat con herramientas de solo lectura. La respuesta pasa por el verificador; "
        "sin evidencia se abstiene. Abajo de cada respuesta ves latencia, proveedor y traza."
    )
    _inicializar()

    # Historial.
    for msg in st.session_state[_MSGS]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                meta = msg.get("meta")
                if meta:
                    st.caption(_meta_caption(meta))
                if msg.get("traza"):
                    with st.expander("🔎 Ver traza del agente"):
                        for t in msg["traza"]:
                            st.markdown(
                                f"- paso {t['paso']}: `{t['herramienta']}` "
                                f"{t.get('argumentos', {})} → {t.get('n_resultados', 0)} resultados"
                            )

    pregunta = st.chat_input("Pregunta en español…")
    if not pregunta:
        return

    # Mensaje del usuario.
    st.session_state[_MSGS].append({"role": "user", "content": pregunta})

    # Ejecutar y medir.
    conn = db.connect()
    t0 = time.perf_counter()
    try:
        r = loop.consultar(
            pregunta, conn, lente=lente, contexto={"vista": "Agente", "lente": lente}
        )
    except Exception as e:  # noqa: BLE001
        conn.close()
        st.session_state[_MSGS].append(
            {"role": "assistant", "content": f"Error: {e}", "meta": None, "traza": []}
        )
        st.rerun()
    latencia_ms = int((time.perf_counter() - t0) * 1000)
    conn.close()

    contenido = ("⚠️ **Abstención:** " + r["respuesta"]) if r["abstencion"] else r["respuesta"]
    meta = {
        "latencia_ms": latencia_ms,
        "proveedor": "deterministico",
        "modelo": "enrutador",
        "pasos": len(r["traza"]),
        "lente": lente,
        "tokens_in": 0,
        "tokens_out": 0,
        "costo_usd": 0.0,
    }

    # Registrar en data/logs/llm.jsonl para que también aparezca en el Comparador.
    log_ejecucion(
        {
            **meta,
            "citas_validas": 0 if r["abstencion"] else 1,
            "citas_total": 1,
            "abstuvo": int(r["abstencion"]),
        }
    )

    st.session_state[_MSGS].append(
        {"role": "assistant", "content": contenido, "meta": meta, "traza": r["traza"]}
    )
    st.rerun()
