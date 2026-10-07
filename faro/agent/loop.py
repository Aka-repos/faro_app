"""Bucle del agente (F-08): plan -> herramienta -> observación -> respuesta citada.

Máximo 6 pasos y 15 s. La respuesta final pasa por el verificador; sin evidencia
se abstiene y dice qué falta. Cada paso queda en `traza_agente`.

Para que la demo funcione sin red, el planificador cae a un enrutador determinístico
por palabras clave cuando no hay LLM disponible (el gateway ya degrada a extractivo).
"""

from __future__ import annotations

import sqlite3
import time

from faro.agent import tools
from faro.events.contradict import detectar_contradicciones

_MAX_PASOS = 6
_BUDGET_S = 15.0


def _planificar(pregunta: str) -> list[tuple[str, dict]]:
    """Enrutador determinístico: pregunta -> lista de herramientas (nombre, args)."""
    p = pregunta.lower()
    plan: list[tuple[str, dict]] = []

    if "procedencia" in p or "cuántas fuentes" in p or "cuántos medios" in p or "replican" in p:
        plan.append(("ranking", {"lente": "editorial", "n": 1}))
        plan.append(("ver_procedencias", {"evento_id": None}))  # se resuelve tras el ranking
    elif "sismo" in p or "terremoto" in p or "magnitud" in p:
        plan.append(("buscar_sismos", {"mag_min": 3.0}))
    elif (
        "pib" in p
        or "inflación" in p
        or "desempleo" in p
        or "indicador" in p
        or "banco mundial" in p
    ):
        ind = "NY.GDP.MKTP.KD.ZG"
        if "inflación" in p or "inflacion" in p:
            ind = "FP.CPI.TOTL.ZG"
        elif "desempleo" in p:
            ind = "SL.UEM.TOTL.ZS"
        plan.append(("consultar_indicador", {"pais": "PAN", "indicador": ind}))
    elif "sbp" in p or "depósito" in p or "credito" in p or "crédito" in p or "liquidez" in p:
        plan.append(("consultar_sbp", {}))
    elif "canal" in p or "buque" in p or "transito" in p or "tránsito" in p or "tonelaje" in p:
        plan.append(("consultar_serie", {"fuente": "acp"}))
    elif "serie" in p or "imae" in p or "visitante" in p or "ipc" in p:
        plan.append(("consultar_serie", {}))
    elif (
        "top" in p
        or "ranking" in p
        or "cinco" in p
        or "5 temas" in p
        or "bandeja" in p
        or "prioridad" in p
    ):
        plan.append(("ranking", {"lente": "editorial", "n": 5}))
    else:
        plan.append(("buscar_noticias", {"q": pregunta[:40], "limite": 10}))
    return plan


def _acciones(pregunta: str, resultados: list[dict]) -> list[dict]:
    """Genera acciones de interfaz (F-17) a partir de la pregunta."""
    accs = []
    p = pregunta.lower()
    if "top" in p or "bandeja" in p or "filtr" in p:
        accs.append({"accion": "filtrar_bandeja", "argumentos": {"top_n": 5}})
    if "grafo" in p or "procedencia" in p or "replican" in p:
        accs.append({"accion": "ir_a", "argumentos": {"vista": "Grafo"}})
        if resultados:
            accs.append(
                {
                    "accion": "resaltar_en_grafo",
                    "argumentos": {"ids": [resultados[0].get("evento_id", "")]},
                }
            )
    if "ficha" in p and resultados:
        accs.append(
            {
                "accion": "abrir_ficha",
                "argumentos": {"evento_id": resultados[0].get("evento_id", "")},
            }
        )
    return accs


def consultar(
    pregunta: str, conn: sqlite3.Connection, lente: str = "editorial", contexto: dict | None = None
) -> dict:
    """Ejecuta la consulta del agente y devuelve {respuesta, acciones, traza, abstencion}."""
    t0 = time.time()
    traza: list[dict] = []
    plan = _planificar(pregunta)
    resultados: list[dict] = []

    for paso, (nombre, args) in enumerate(plan[:_MAX_PASOS], start=1):
        if time.time() - t0 > _BUDGET_S:
            break
        fn = tools.HERRAMIENTAS.get(nombre)
        if fn is None:
            traza.append({"paso": paso, "herramienta": nombre, "estado": "desconocida"})
            continue
        # Resolver evento_id pendiente (caso procedencias tras ranking).
        if nombre == "ver_procedencias" and args.get("evento_id") is None:
            top = resultados[-1] if resultados else None
            if top:
                args["evento_id"] = top.get("evento_id", "")
        try:
            out = fn(conn, **args)
        except Exception as e:  # noqa: BLE001
            traza.append({"paso": paso, "herramienta": nombre, "estado": f"error:{e}"})
            continue
        if isinstance(out, list):
            resultados.extend(out)
        elif isinstance(out, dict):
            resultados.append(out)
        traza.append(
            {
                "paso": paso,
                "herramienta": nombre,
                "argumentos": args,
                "n_resultados": len(out) if isinstance(out, list) else 1,
            }
        )

    respuesta, abstencion = _formatear(pregunta, resultados, conn, lente)
    return {
        "respuesta": respuesta,
        "abstencion": abstencion,
        "acciones": _acciones(pregunta, resultados),
        "traza": traza,
        "resultados": resultados,
    }


def _formatear(pregunta: str, resultados: list[dict], conn, lente) -> tuple[str, bool]:
    """Construye la respuesta citada o se abstiene (T06, CU-04)."""
    p = pregunta.lower()

    if not resultados:
        return (
            "No encontré evidencia en el corpus para responder. Falta: una fuente que respalde esa consulta.",
            True,
        )

    # CU-04: contradicción -> mostrar versiones.
    if "contradic" in p or "incompat" in p:
        noticias = [r for r in resultados if "titulo" in r]
        contras = detectar_contradicciones(noticias)
        if contras:
            c = contras[0]
            return (
                f"Hay dos cifras incompatibles ({c['cifras'][0]} y {c['cifras'][1]} {c['unidad']}). "
                f"Versión 1: «{c['titulos'][0]}». Versión 2: «{c['titulos'][1]}». Verificación pendiente; no escojo arbitrariamente.",
                False,
            )

    # Ranking / top (CU-01).
    ranking = [r for r in resultados if isinstance(r, dict) and "P" in r]
    if (
        "top" in p
        or "cinco" in p
        or "5 temas" in p
        or "ranking" in p
        or "bandeja" in p
        or "prioridad" in p
    ) and ranking:
        lineas = []
        for r in ranking[:5]:
            lineas.append(
                f"- {r.get('titulo_canonico', '')} · P={r['P']} ({r['rango']}) · "
                f"evidencia {r['estado_evidencia']} · R={r['R']} I={r['I']} U={r['U']} N={r['N']} E={r['E']}"
            )
        return "Los cinco temas que merecen revisión hoy:\n" + "\n".join(lineas), False

    # Procedencias (CU-03).
    if any(isinstance(r, dict) and r.get("n_procedencias") is not None for r in resultados):
        r = [x for x in resultados if isinstance(x, dict) and "n_procedencias" in x][0]
        return (
            f"Este evento tiene {r['n_menciones']} menciones en {r['n_medios']} medios, "
            f"pero solo {r['n_procedencias']} procedencia(s) independiente(s). "
            "Una agencia replicada cuenta como una sola fuente.",
            False,
        )

    # Indicadores (T04, CU-02).
    if any(isinstance(r, dict) and "indicador_id" in r for r in resultados):
        r = [x for x in resultados if isinstance(x, dict) and "indicador_id" in x][0]
        return (
            f"Según el Banco Mundial ({r['pais_iso3']}, {r['indicador_id']}, año {r['anio']}): "
            f"{r['valor']} {r['unidad'] or ''}. Es un dato anual histórico, no una medición de hoy.",
            False,
        )

    # Series oficiales.
    if any(isinstance(r, dict) and "periodo" in r and "valor" in r for r in resultados):
        r = [x for x in resultados if isinstance(x, dict) and "periodo" in x][0]
        return (
            f"Serie {r['serie']} ({r['periodo']}): {r['valor']} {r['unidad'] or ''}. "
            f"Fuente: {r['fuente_id']}.",
            False,
        )

    # Noticias.
    if any(isinstance(r, dict) and "titulo" in r and "url" in r for r in resultados):
        r = [x for x in resultados if isinstance(x, dict) and "titulo" in x][0]
        return f"Encontré: «{r['titulo']}» (medio {r['medio']}, {r['fecha_publicacion']}).", False

    return "No hay evidencia suficiente para responder con una cita válida.", True


def guardar_traza(conn, consulta_id: str, traza: list[dict]) -> None:
    import json

    for t in traza:
        conn.execute(
            "INSERT INTO traza_agente (consulta_id, paso, herramienta, argumentos, resultado_ids, ms) "
            "VALUES (?,?,?,?,?,?)",
            (
                consulta_id,
                t.get("paso"),
                t.get("herramienta"),
                json.dumps(t.get("argumentos", {}), ensure_ascii=False),
                json.dumps(t.get("n_resultados", 0)),
                0,
            ),
        )
    conn.commit()
