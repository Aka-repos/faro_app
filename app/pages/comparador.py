"""Comparador de modelos (L-03): nube vs. local — latencia, tokens y costo."""

from __future__ import annotations

import json

import streamlit as st

import config.settings as S


def render(lente: str) -> None:
    st.subheader("Comparador de modelos (nube vs. local)")
    st.caption(
        "Cada vez que el agente o la pasarela genera algo, se registra aquí: proveedor, "
        "modelo, tokens, costo y latencia. Haz una consulta en la vista **Agente** o corre `make eval`."
    )
    log = S.DATA_DIR / "logs" / "llm.jsonl"
    if not log.exists():
        st.info(
            "Aún no hay ejecuciones registradas. Haz una consulta en la vista **Agente** o corre `make eval`."
        )
        return

    filas = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]
    completas = [f for f in filas if "proveedor" in f]
    st.markdown(f"**{len(filas)} ejecuciones registradas** ({len(completas)} completas).")

    if completas:
        import pandas as pd

        df = pd.DataFrame(
            [
                {
                    "proveedor": f.get("proveedor", "?"),
                    "modelo": f.get("modelo", "?"),
                    "lente": f.get("lente", "?"),
                    "tokens_in": f.get("tokens_in", 0),
                    "tokens_out": f.get("tokens_out", 0),
                    "costo_usd": round(f.get("costo_usd", 0.0), 6),
                    "latencia_ms": f.get("latencia_ms", 0),
                }
                for f in completas
            ]
        )
        st.dataframe(df, width="stretch")

    for f in filas[-10:]:
        if "error" in f:
            st.caption(f"⚠️ etapa {f.get('etapa', '?')}: {f.get('error', '')}")
