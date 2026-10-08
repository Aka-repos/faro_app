"""Generación con LLM para paquete/boletín (M3): evidencia, verificación y límites.

`gateway.generate` con esquema Pydantic + plantilla extractiva de respaldo; el
verificador filtra las afirmaciones; los límites de palabras se aplican en código.
"""

from __future__ import annotations

import json

from faro import evidence as ev_module
from faro.guard import shield, verifier
from faro.llm import gateway


def evidencia_de_evento(evento: dict, conn) -> tuple[list[dict], dict[str, str]]:
    """Arma la evidencia citable del evento: noticias del cluster + contexto oficial."""
    filas = []
    evidencias: dict[str, str] = {}
    for n in evento.get("noticias", []):
        eid = f"N:{n['id']}#titulo"
        texto = n.get("titulo", "")
        evidencias[eid] = texto
        filas.append(
            {
                "evidencia_id": eid,
                "texto": texto,
                "campo": "titulo",
                "alcance_texto": n.get("alcance_texto", "titular"),
                "medio": n.get("medio", ""),
                "fecha": n.get("fecha_publicacion") or n.get("fecha_deteccion") or "",
            }
        )
    for c in evento.get("contexto", []):
        texto = ev_module.resolver(conn, c["evidencia_id"])
        if texto:
            evidencias[c["evidencia_id"]] = texto
            filas.append(
                {
                    "evidencia_id": c["evidencia_id"],
                    "texto": texto,
                    "campo": "valor",
                    "alcance_texto": "resumen",
                    "medio": "",
                    "fecha": "",
                }
            )
    return filas, evidencias


def mensajes_redaccion(system_prompt: str, evento: dict, filas: list[dict]) -> list[dict]:
    datos = json.dumps(
        {"evento": evento.get("titulo_canonico", ""), "evidencia": filas},
        ensure_ascii=False,
        default=str,
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": shield.delimitar_como_dato(datos)},
    ]


def generar(
    conn,
    evento: dict,
    *,
    esquema,
    system_prompt: str,
    plantilla,
    plantilla_args,
    llm_cfg: dict | None,
    limites: dict | None = None,
    lente: str = "editorial",
) -> dict:
    """Genera con LLM (o plantilla si no hay proveedor), verifica y aplica límites."""
    llm_cfg = llm_cfg or {}
    filas, evidencias = evidencia_de_evento(evento, conn)
    solo_titular = bool(filas) and all(
        f["alcance_texto"] in ("titular", "metadatos") for f in filas
    )

    mensajes = mensajes_redaccion(system_prompt, evento, filas)
    r = gateway.generate(
        mensajes,
        lente=lente,
        esquema=esquema,
        plantilla=plantilla,
        plantilla_args=plantilla_args,
        proveedor=llm_cfg.get("proveedor"),
        modelo=llm_cfg.get("modelo"),
        api_key=llm_cfg.get("api_key"),
        base_url=llm_cfg.get("base_url"),
        modo=llm_cfg.get("modo"),
    )
    try:
        salida = esquema.model_validate(json.loads(r["texto"])).model_dump()
    except Exception:  # noqa: BLE001
        # Si el JSON no valida, se usa la plantilla extractiva.
        salida = plantilla(**(plantilla_args or {}))
        r = {
            "proveedor": "extractivo",
            "modelo": "extractivo",
            "tokens_in": 0,
            "tokens_out": 0,
            "costo_usd": 0.0,
            "latencia_ms": 0,
        }

    # Verificador: eliminar afirmaciones que no se sustentan.
    ok_afirmaciones = []
    for a in salida.get("afirmaciones", []):
        ok, _ = verifier.verificar_afirmacion(
            a, evidencias.get(a.get("evidencia_id")), lente, solo_titular
        )
        if ok:
            ok_afirmaciones.append(a)
    salida["afirmaciones"] = ok_afirmaciones

    # Límites en código.
    if limites:
        salida = _aplicar_limites(salida, limites)

    # Etiqueta de titular/metadatos.
    if solo_titular and not salida.get("basado_solo_titular"):
        salida["basado_solo_titular"] = True
    salida["_meta"] = {
        "proveedor": r.get("proveedor", "extractivo"),
        "modelo": r.get("modelo", "extractivo"),
        "tokens_in": r.get("tokens_in", 0),
        "tokens_out": r.get("tokens_out", 0),
        "costo_usd": r.get("costo_usd", 0.0),
        "latencia_ms": r.get("latencia_ms", 0),
        "desde_cache": r.get("desde_cache", False),
    }
    return salida


def _aplicar_limites(salida: dict, limites: dict) -> dict:
    for campo, max_palabras in limites.items():
        texto = salida.get(campo)
        if isinstance(texto, str) and len(texto.split()) > max_palabras:
            salida[campo] = " ".join(texto.split()[:max_palabras])
            salida["recortado"] = True
    return salida
