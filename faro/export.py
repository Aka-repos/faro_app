"""Exportación de fichas (E-03, contrato fichas.jsonl) y revisión (F-13)."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime

import config.settings as S
from faro import evidence
from faro.agent import tools
from faro.guard import verifier
from faro.llm import extractive
from faro.review.states import ESTADOS


def _afirmaciones_de_evento(conn, evento: dict) -> tuple[list[dict], dict[str, str]]:
    """Construye afirmaciones verificadas y un mapa evidencia_id -> texto."""
    afirmaciones = []
    evidencias = {}
    for c in evento["contexto"]:
        texto = evidence.resolver(conn, c["evidencia_id"])
        if texto:
            evidencias[c["evidencia_id"]] = texto
            afirmaciones.append(
                {
                    "texto": texto,
                    "tipo": "hecho",
                    "evidencia_id": c["evidencia_id"],
                    "campo": "valor",
                }
            )
    return afirmaciones, evidencias


def generar_fichas(conn: sqlite3.Connection, lente: str = "editorial", n: int = 5) -> list[dict]:
    """Genera fichas para el top n y las exporta a data/out/fichas.jsonl."""
    ranking = tools.ranking(conn, lente, n)
    fichas = []
    for r in ranking:
        evento_id = r["evento_id"]
        ev = tools.abrir_evento(conn, evento_id)
        if not ev:
            continue
        afirmaciones, evidencias = _afirmaciones_de_evento(conn, ev)
        solo_titular = any(m.get("alcance_texto") == "titular" for m in ev["noticias"])

        # Verificar afirmaciones.
        verificadas = []
        for a in afirmaciones:
            ok, motivo = verifier.verificar_afirmacion(
                a, evidencias.get(a["evidencia_id"]), lente, solo_titular
            )
            if ok:
                verificadas.append(a)
        if not verificadas:
            # Ficha sin evidencia suficiente: es un caso válido para la demo.
            verificadas = []

        if lente == "editorial":
            borrador = extractive.generar_editorial(ev, verificadas, ev["contexto"])
        else:
            from faro.lenses.banca import mapear_sectores

            sectores = mapear_sectores(ev, ev["noticias"])
            borrador = extractive.generar_boletin(ev, verificadas, [s["nombre"] for s in sectores])

        fichas.append(
            {
                "id_caso": f"F-{evento_id}",
                "modalidad": lente,
                "ids_fuente": [m["id"] for m in ev["noticias"]],
                "afirmaciones": verificadas,
                "citas": [c["evidencia_id"] for c in ev["contexto"]],
                "puntaje": r.get("P"),
                "componentes": {k: r[k] for k in ("R", "I", "U", "N", "E") if k in r},
                "estado_evidencia": r.get("estado_evidencia", "insuficiente"),
                "borrador": borrador,
                "estado_revision": "nuevo",
            }
        )

    S.ensure_dirs()
    with open(S.OUT_DIR / "fichas.jsonl", "w", encoding="utf-8") as fh:
        for f in fichas:
            fh.write(json.dumps(f, ensure_ascii=False) + "\n")

    # Persistir en tablas ficha/afirmacion.
    for f in fichas:
        ficha_id = f"f-{uuid.uuid4().hex[:8]}"
        conn.execute(
            "INSERT INTO ficha (id, evento_id, lente, borrador_json, vacios_json, estado_revision, creado) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                ficha_id,
                f["id_caso"].replace("F-ev-", "ev-"),
                lente,
                json.dumps(f["borrador"], ensure_ascii=False),
                "[]",
                "nuevo",
                datetime.now(UTC).isoformat(),
            ),
        )
        for a in f["afirmaciones"]:
            conn.execute(
                "INSERT INTO afirmacion (ficha_id, texto, tipo, evidencia_id, campo, verificada) "
                "VALUES (?,?,?,?,?,1)",
                (ficha_id, a["texto"], a["tipo"], a.get("evidencia_id"), a.get("campo")),
            )
    conn.commit()
    return fichas


def revisar_ficha(conn, ficha_id: str, estado: str, revisor: str, nota: str = "") -> None:
    if estado not in ESTADOS:
        raise ValueError(f"Estado inválido: {estado}")
    conn.execute(
        "UPDATE ficha SET estado_revision=?, revisor=?, nota_revision=? WHERE id=?",
        (estado, revisor, nota, ficha_id),
    )
    conn.commit()
