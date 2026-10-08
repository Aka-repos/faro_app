"""Ficha de investigación (E-02): qué se reporta, quién, qué respaldado, qué falta."""

from __future__ import annotations

import streamlit as st

from app.db_ui import cargar_evento, df_eventos, sin_datos


def render(lente: str) -> None:
    st.subheader("Ficha de investigación")
    if sin_datos():
        return
    ev = df_eventos(lente)
    if ev.empty:
        st.info("No hay eventos para este lente.")
        return
    evento_id = st.selectbox(
        "Evento",
        ev["id"].tolist(),
        format_func=lambda i: ev.loc[ev["id"] == i, "titulo_canonico"].iloc[0][:70],
    )
    ev = cargar_evento(evento_id)
    if not ev:
        st.warning("Evento no encontrado.")
        return
    st.markdown(f"### {ev['titulo_canonico']}")
    st.write(
        f"Tema: **{ev['tema']}** · menciones **{ev['n_menciones']}** · medios **{ev['n_medios']}**"
        f" · procedencias **{ev['n_procedencias']}**"
    )
    for p in ev["puntajes"]:
        st.markdown(
            f"Puntaje ({p['lente']}): **P={p['P']}** ({p['rango']}) — estado: "
            f"**{p['estado_evidencia']}** · R={p['R']} I={p['I']} U={p['U']} N={p['N']} E={p['E']}"
        )
    st.markdown("#### ¿Qué se reporta?")
    for n in ev["noticias"]:
        fecha = n.get("fecha_publicacion") or n.get("fecha_deteccion") or "sin fecha"
        st.markdown(
            f"- «{n['titulo']}» — *{n['medio']}* ({fecha})"
            + (f" · agencia {n['agencia']}" if n.get("agencia") else "")
        )
    st.markdown("#### Contexto oficial")
    if ev["contexto"]:
        for c in ev["contexto"]:
            st.markdown(f"- `{c['evidencia_id']}` — {c['motivo_enlace'][:80]}")
    else:
        st.write("Sin contexto oficial enlazado.")
    st.markdown("#### ¿Qué falta verificar?")
    st.write("Confirmar cifras con fuente primaria y verificar procedencias independientes.")
