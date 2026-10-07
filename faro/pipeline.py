"""Pipeline por lotes: del snapshot crudo a la bandeja priorizada.

Orden: validar -> cargar SQLite -> embeddings -> eventos/procedencias ->
entidades -> contexto -> puntaje -> reportes. Todo offline (D-13).
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime

import config.settings as S
from faro import db
from faro.agent import tools
from faro.context.link import enlazar_contexto
from faro.events.cluster import agrupar_eventos
from faro.events.contradict import detectar_contradicciones
from faro.events.provenance import procedencias_de_evento
from faro.loaders import load_fuentes
from faro.nlp import classify, embed
from faro.nlp.entities import extraer_entidades
from faro.quality import validate
from faro.scoring.score import puntuar_evento


def _iso(s: str | None):
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    except ValueError:
        return None


def cargar_fuentes(conn) -> None:
    cols = (
        "id",
        "nombre",
        "familia",
        "url_base",
        "metodo",
        "robots_ok",
        "condiciones",
        "rate_limit_s",
        "user_agent",
        "licencia",
        "notas",
    )
    filas = [{c: f.get(c) for c in cols} for f in load_fuentes()]
    db.upsert(conn, "fuente", filas)


def _fecha_min_max(noticias: list[dict]) -> tuple[str, str]:
    fechas = [n["fecha_publicacion"] for n in noticias if n.get("fecha_publicacion")]
    if not fechas:
        return "", ""
    return min(fechas), max(fechas)


def _tema_mayoritario(noticias: list[dict]) -> str:
    temas = [n.get("tema") for n in noticias if n.get("tema")]
    return Counter(temas).most_common(1)[0][0] if temas else "economia"


def ingesta(conn) -> dict:
    """Valida el snapshot crudo y carga las tablas de la Capa 1."""
    raw = validate.load_raw()
    if not any(raw.values()):
        from faro.seed import gen_indicadores, gen_noticias, gen_series, gen_sismos, write_raw

        write_raw(gen_noticias(), gen_series(), gen_indicadores(), gen_sismos())
        raw = validate.load_raw()

    validados = validate.validar_todo(raw)
    cargar_fuentes(conn)

    # Clasificar tema si no viene en el registro (baseline de palabras clave).
    for n in validados["noticia"]:
        if not n.get("tema"):
            n["tema"] = classify.clasificar_baseline(n["titulo"])

    db.upsert(conn, "noticia", validados["noticia"])
    db.upsert(conn, "serie_oficial", validados["serie_oficial"])
    db.upsert(conn, "indicador", validados["indicador"])
    db.upsert(conn, "sismo", validados["sismo"])
    db.upsert(conn, "cuarentena", validados["cuarentena"])
    return {
        "noticias": len(validados["noticia"]),
        "series": len(validados["serie_oficial"]),
        "indicadores": len(validados["indicador"]),
        "sismos": len(validados["sismo"]),
        "cuarentena": len(validados["cuarentena"]),
    }


def deducir(conn) -> dict:
    """Capas 2 (deducido): embeddings, eventos, entidades, contexto, puntaje."""
    noticias = db.fetchall(conn, "SELECT * FROM noticia ORDER BY id")
    if not noticias:
        return {"eventos": 0}

    textos = [n["titulo"] for n in noticias]
    matriz = embed.Embedder().encode(textos)

    grupos = agrupar_eventos(noticias, matriz)

    # Limpiar capas deducidas previas para reconstrucción reproducible.
    for t in (
        "evento_noticia",
        "evento_entidad",
        "evento_contexto",
        "evento_puntaje",
        "evento_sector",
        "evento",
        "entidad",
    ):
        conn.execute(f"DELETE FROM {t}")
    conn.commit()

    entidad_id: dict[str, int] = {}
    n_contradicciones = 0
    for gi, grupo in enumerate(grupos, start=1):
        miembros = [noticias[i] for i in grupo]
        tema = _tema_mayoritario(miembros)
        proc = procedencias_de_evento(miembros)
        fecha_primera, fecha_ultima = _fecha_min_max(miembros)
        # Título canónico: el del miembro con más entidades (más informativo).
        canonico = sorted(
            miembros, key=lambda m: len(extraer_entidades(m["titulo"])), reverse=True
        )[0]["titulo"]
        evento = {
            "id": f"ev-{gi:04d}",
            "tema": tema,
            "titulo_canonico": canonico,
            "fecha_primera": fecha_primera,
            "fecha_ultima": fecha_ultima,
            "n_menciones": proc["n_menciones"],
            "n_medios": proc["n_medios"],
            "n_procedencias": proc["n_procedencias"],
        }
        db.upsert(conn, "evento", [evento])
        # Marcar recirculada (fecha_publicacion previa a la ventana) sin ensuciar la tabla evento.
        recirculada = any(
            _iso(noticias[i].get("fecha_publicacion"))
            and _iso(noticias[i]["fecha_publicacion"]) < S.VENTANA_INICIO
            for i in grupo
        )

        for m in miembros:
            conn.execute(
                "INSERT OR REPLACE INTO evento_noticia (evento_id, noticia_id, procedencia_id) VALUES (?,?,?)",
                (evento["id"], m["id"], m.get("agencia") or m["medio"]),
            )

        # Entidades del evento.
        for m in miembros:
            for ent in extraer_entidades(m["titulo"]):
                key = (ent["nombre"].lower(), ent["tipo"])
                if key not in entidad_id:
                    cur = conn.execute(
                        "INSERT INTO entidad (nombre, tipo) VALUES (?,?)",
                        (ent["nombre"], ent["tipo"]),
                    )
                    entidad_id[key] = cur.lastrowid
                conn.execute(
                    "INSERT OR REPLACE INTO evento_entidad (evento_id, entidad_id) VALUES (?,?)",
                    (evento["id"], entidad_id[key]),
                )

        # Contexto oficial.
        for enlace in enlazar_contexto(tema, conn):
            conn.execute(
                "INSERT OR REPLACE INTO evento_contexto (evento_id, evidencia_id, motivo_enlace) VALUES (?,?,?)",
                (evento["id"], enlace["evidencia_id"], enlace["motivo_enlace"]),
            )

        n_contexto = db.fetchall(
            conn, "SELECT COUNT(*) c FROM evento_contexto WHERE evento_id=?", (evento["id"],)
        )[0]["c"]
        for lente in ("editorial", "banca"):
            puntaje = puntuar_evento(
                {**evento, "recirculada": recirculada}, n_contexto=n_contexto, lente=lente
            )
            db.upsert(conn, "evento_puntaje", [puntaje])

        n_contradicciones += len(detectar_contradicciones(miembros))

    conn.commit()
    return {
        "eventos": len(grupos),
        "entidades": len(entidad_id),
        "contradicciones": n_contradicciones,
    }


def reportes(conn, ingesta_res: dict, deducir_res: dict) -> dict:
    """Genera reports (calidad, ranking, manifest)."""
    S.ensure_dirs()
    fuentes = db.fetchall(conn, "SELECT COUNT(*) c FROM noticia GROUP BY medio")
    ranking = tools.ranking(conn, "editorial", 10)
    calidad = {
        "generado": datetime.now(UTC).isoformat(),
        "conteos": ingesta_res,
        "medios_distintos": len(fuentes),
        "noticias_tvn": db.fetchall(conn, "SELECT COUNT(*) c FROM noticia WHERE medio='TVN'")[0][
            "c"
        ],
        "fuera_de_ventana": db.fetchall(
            conn,
            "SELECT COUNT(*) c FROM noticia WHERE fecha_deteccion IS NULL AND fecha_publicacion < ?",
            (S.VENTANA_INICIO.isoformat(),),
        )[0]["c"],
        "cuarentena": db.fetchall(
            conn, "SELECT motivo, COUNT(*) c FROM cuarentena GROUP BY motivo"
        ),
        "top10": ranking,
    }
    (S.REPORTS_DIR / "calidad_v1.json").write_text(
        json.dumps(calidad, ensure_ascii=False, indent=2, default=str)
    )
    (S.REPORTS_DIR / "ranking_v1.json").write_text(
        json.dumps(ranking, ensure_ascii=False, indent=2, default=str)
    )

    from faro.quality.manifest import build_manifest, write_manifest

    conteos = {
        "noticias.jsonl": ingesta_res["noticias"],
        "series.jsonl": ingesta_res["series"],
        "indicadores.jsonl": ingesta_res["indicadores"],
        "sismos.jsonl": ingesta_res["sismos"],
    }
    write_manifest(build_manifest(conteos))
    return calidad


def build(db_path=None) -> dict:
    """Ejecuta el pipeline completo y devuelve un resumen."""
    S.ensure_dirs()
    conn = db.connect(db_path)
    try:
        ing = ingesta(conn)
        ded = deducir(conn)
        rep = reportes(conn, ing, ded)
        return {"ingesta": ing, "deducido": ded, "top10": rep["top10"]}
    finally:
        conn.close()
