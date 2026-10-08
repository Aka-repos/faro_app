"""Aplicación de acciones del agente sobre la interfaz (M4.1).

Las acciones solo cambian la vista (st.session_state), nunca la base de datos.
Devuelve una línea legible por acción aplicada.
"""

from __future__ import annotations

import streamlit as st


def aplicar(acciones: list[dict]) -> list[str]:
    lineas = []
    for a in acciones or []:
        nombre = a.get("accion")
        args = a.get("argumentos", {}) or {}
        try:
            if nombre == "filtrar_bandeja":
                st.session_state["filtros_bandeja"] = args
                lineas.append(f"Filtré la bandeja: {args}")
            elif nombre == "abrir_ficha":
                st.session_state["evento_abierto"] = args.get("evento_id")
                st.session_state["vista"] = "🗂️ Ficha"
                lineas.append(f"Abrí la ficha {args.get('evento_id')}")
            elif nombre == "ir_a":
                st.session_state["vista"] = args.get("vista", "📥 Bandeja")
                lineas.append(f"Fui a la vista {args.get('vista')}")
            elif nombre == "resaltar_en_grafo":
                st.session_state["grafo_resaltar"] = args.get("ids", [])
                lineas.append(f"Resalté en el grafo: {args.get('ids')}")
            elif nombre == "mostrar_evidencia":
                st.session_state["evidencia_abierta"] = args.get("evidencia_id")
                lineas.append(f"Mostré la evidencia {args.get('evidencia_id')}")
            else:
                lineas.append(f"Acción desconocida descartada: {nombre}")
        except Exception as e:  # noqa: BLE001
            lineas.append(f"Acción descartada ({nombre}): {e}")
    return lineas
