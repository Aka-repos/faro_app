"""Paquete editorial / boletín (E-03, B-04)."""

from __future__ import annotations

import streamlit as st

from app.db_ui import cargar_evento, df_eventos, sin_datos
from faro import db
from faro.evidence import resolver
from faro.lenses import banca as lente_banca
from faro.llm import extractive


def render(lente: str) -> None:
    st.subheader("Paquete editorial" if lente == "editorial" else "Boletín bancario")
    if sin_datos():
        return
    ev = df_eventos(lente)
    if ev.empty:
        st.info("No hay eventos para este lente.")
        return
    evento_id = st.selectbox(
        "Evento",
        ev["id"].tolist(),
        key="paquete_evento",
        format_func=lambda i: ev.loc[ev["id"] == i, "titulo_canonico"].iloc[0][:70],
    )
    ev = cargar_evento(evento_id)
    if not ev:
        return
    # Construir afirmaciones verificadas desde el contexto oficial.
    conn = db.connect()
    afirmaciones = []
    for c in ev["contexto"]:
        texto = resolver(conn, c["evidencia_id"])
        if texto:
            afirmaciones.append(
                {
                    "texto": texto,
                    "tipo": "hecho",
                    "evidencia_id": c["evidencia_id"],
                    "campo": "valor",
                }
            )
    conn.close()

    if lente == "editorial":
        out = extractive.generar_editorial(ev, afirmaciones, ev["contexto"])
        st.markdown(f"**Título:** {out['titulo']}")
        st.markdown(f"**Enfoque:** {out['enfoque']}")
        st.markdown("#### Brief (≤250 palabras)")
        st.write(out["brief"])
        st.markdown("#### Guion 45–60 s")
        st.write(out["guion"])
        st.markdown("#### Copy (≤80 palabras)")
        st.write(out["copy_digital"])
        st.markdown("#### Preguntas de investigación")
        for q in out["preguntas"]:
            st.markdown(f"- {q}")
    else:
        sectores = lente_banca.mapear_sectores(ev, ev["noticias"])
        out = extractive.generar_boletin(ev, afirmaciones, [s["nombre"] for s in sectores])
        st.markdown("#### Resumen (≤250 palabras)")
        st.write(out["resumen"])
        st.markdown("#### Sectores")
        st.write(", ".join(out["sectores"]) or "—")
        st.markdown("#### Horizonte")
        st.write(out["horizonte"])
        st.markdown("#### Observaciones")
        for o in out["observaciones"]:
            st.markdown(f"- {o}")
        st.markdown("#### Hipótesis (marcadas)")
        for h in out["hipotesis"]:
            st.markdown(f"- {h}")
    st.markdown("#### Citas")
    for c in ev["contexto"]:
        st.markdown(f"- `{c['evidencia_id']}`")
