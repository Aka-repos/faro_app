"""E2E (H6): pregunta -> traza -> ficha -> paquete -> revisión -> fichas.jsonl."""

from __future__ import annotations

import json

import config.settings as S
from faro.agent import loop
from faro.export import generar_fichas, revisar_ficha
from faro.review.states import ESTADOS


def test_recorrido_completo(conn):
    # 1. Pregunta -> traza.
    r = loop.consultar("¿Qué cinco temas merecen revisión hoy y por qué?", conn)
    assert r["respuesta"]
    assert r["traza"]
    assert not r["abstencion"]

    # 2. Fichas -> export fichas.jsonl.
    fichas = generar_fichas(conn, "editorial", n=3)
    assert len(fichas) >= 1
    for f in fichas:
        assert f["id_caso"].startswith("F-")
        assert f["estado_evidencia"] in ("insuficiente", "parcial", "suficiente para el borrador")
        assert f["estado_revision"] == "nuevo"

    # 3. Contrato fichas.jsonl válido.
    lineas = (S.OUT_DIR / "fichas.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lineas) >= 1
    for ln in lineas:
        obj = json.loads(ln)
        assert "id_caso" in obj and "afirmaciones" in obj and "puntaje" in obj


def test_revision_humana(conn):
    fichas = generar_fichas(conn, "editorial", n=1)
    if not fichas:
        return
    ficha_id = conn.execute("SELECT id FROM ficha ORDER BY id LIMIT 1").fetchone()[0]
    revisar_ficha(conn, ficha_id, "aprobado como borrador", "editor", "ok")
    estado = conn.execute("SELECT estado_revision FROM ficha WHERE id=?", (ficha_id,)).fetchone()[0]
    assert estado == "aprobado como borrador"
    assert estado in ESTADOS


def test_estados_validos():
    assert ESTADOS == [
        "nuevo",
        "en revisión",
        "requiere evidencia",
        "aprobado como borrador",
        "descartado",
    ]
