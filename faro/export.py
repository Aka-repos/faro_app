"""Exportación de fichas (E-03, contrato fichas.jsonl) y revisión (F-13)."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime

import config.settings as S
from faro import evidence
from faro.agent import tools
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


def generar_fichas(
    conn: sqlite3.Connection, lente: str = "editorial", n: int = 5, llm_cfg: dict | None = None
) -> list[dict]:
    """Genera fichas para el top n (LLM si hay proveedor) y las exporta a fichas.jsonl."""
    ranking = tools.ranking(conn, lente, n)
    fichas = []
    for r in ranking:
        evento_id = r["evento_id"]
        ev = tools.abrir_evento(conn, evento_id)
        if not ev:
            continue

        if lente == "editorial":
            from faro.lenses.editorial import generar_paquete

            borrador = generar_paquete(ev, conn, llm_cfg=llm_cfg)
        else:
            from faro.lenses.banca import generar_boletin_sectorial

            borrador = generar_boletin_sectorial(ev, conn, llm_cfg=llm_cfg)

        meta = borrador.pop("_meta", {})
        fichas.append(
            {
                "id_caso": f"F-{evento_id}",
                "modalidad": lente,
                "ids_fuente": [m["id"] for m in ev["noticias"]],
                "afirmaciones": borrador.get("afirmaciones", []),
                "citas": [c["evidencia_id"] for c in ev["contexto"]],
                "puntaje": r.get("P"),
                "componentes": {k: r[k] for k in ("R", "I", "U", "N", "E") if k in r},
                "estado_evidencia": r.get("estado_evidencia", "insuficiente"),
                "borrador": borrador,
                "estado_revision": "nuevo",
                "meta": meta,
            }
        )

    S.ensure_dirs()
    with open(S.OUT_DIR / "fichas.jsonl", "w", encoding="utf-8") as fh:
        for f in fichas:
            fh.write(json.dumps(f, ensure_ascii=False, default=str) + "\n")

    # Persistir en tablas ficha/afirmacion con metadatos de ejecución (M3.5).
    for f in fichas:
        ficha_id = f"f-{uuid.uuid4().hex[:8]}"
        meta = f.get("meta", {})
        conn.execute(
            "INSERT INTO ficha (id, evento_id, lente, borrador_json, vacios_json, estado_revision, "
            "proveedor, modelo, prompt_version, tokens_in, tokens_out, costo_usd, latencia_ms, "
            "desde_cache, creado) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                ficha_id,
                f["id_caso"].replace("F-ev-", "ev-"),
                lente,
                json.dumps(f["borrador"], ensure_ascii=False, default=str),
                json.dumps(f["borrador"].get("vacios", []), ensure_ascii=False, default=str),
                "nuevo",
                meta.get("proveedor"),
                meta.get("modelo"),
                "v1",
                meta.get("tokens_in", 0),
                meta.get("tokens_out", 0),
                meta.get("costo_usd", 0.0),
                meta.get("latencia_ms", 0),
                int(meta.get("desde_cache", False)),
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
