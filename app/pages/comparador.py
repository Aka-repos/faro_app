"""Comparador de modelos (L-03): nube vs. local."""

from __future__ import annotations

import json

import streamlit as st

import config.settings as S


def render(lente: str) -> None:
    st.subheader("Comparador de modelos (nube vs. local)")
    log = S.DATA_DIR / "logs" / "llm.jsonl"
    if not log.exists():
        st.info("Aún no hay ejecuciones registradas. Corre consultas del agente o `make eval`.")
        return
    filas = []
    for line in log.read_text(encoding="utf-8").splitlines():
        if line.strip():
            filas.append(json.loads(line))
    st.markdown(f"{len(filas)} ejecuciones registradas.")
    for f in filas[-20:]:
        st.markdown(
            f"- `{f.get('proveedor', '?')}/{f.get('modelo', '?')}` · "
            f"tokens {f.get('tokens_in', 0)}/{f.get('tokens_out', 0)} · "
            f"costo ${f.get('costo_usd', 0):.4f} · {f.get('latencia_ms', 0)} ms · lente {f.get('lente', '?')}"
        )
