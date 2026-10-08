"""Paquete editorial / boletín (E-03, B-04), generado con LLM si hay proveedor (M3)."""

from __future__ import annotations

import streamlit as st

from app.db_ui import cargar_evento, df_eventos, sin_datos
from faro import db
from faro.lenses import banca as lente_banca
from faro.lenses import editorial as lente_editorial


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
    conn = db.connect()
    llm_cfg = st.session_state.get("llm", {})
    if lente == "editorial":
        out = lente_editorial.generar_paquete(ev, conn, llm_cfg=llm_cfg)
        meta = out.pop("_meta", {})
        st.caption(
            f"Generado por **{meta.get('proveedor', 'extractivo')}/{meta.get('modelo', 'extractivo')}**"
            f" · {meta.get('tokens_out', 0)} tokens · ${meta.get('costo_usd', 0):.5f}"
            + (" · ⚠️ recortado" if out.get("recortado") else "")
        )
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
        out = lente_banca.generar_boletin_sectorial(ev, conn, llm_cfg=llm_cfg)
        meta = out.pop("_meta", {})
        st.caption(
            f"Generado por **{meta.get('proveedor', 'extractivo')}/{meta.get('modelo', 'extractivo')}**"
            f" · {meta.get('tokens_out', 0)} tokens"
        )
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
    conn.close()
    st.markdown("#### Citas")
    for c in ev["contexto"]:
        st.markdown(f"- `{c['evidencia_id']}`")
