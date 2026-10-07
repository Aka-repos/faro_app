"""T10 — Sin internet: funciona con snapshot y fallback documentado (extractivo)."""

from __future__ import annotations

import json

from faro.llm import gateway


def test_cascada_cae_a_extractivo():
    # Sin proveedor configurado y sin Ollama, `auto` debe caer al extractivo.
    r = gateway.generate(
        [{"role": "user", "content": "genera"}],
        lente="editorial",
        modo="auto",
        proveedor=None,
        modelo=None,
        api_key=None,
        plantilla=lambda: {"titulo": "ok"},
    )
    assert r["proveedor"] == "extractivo"
    assert json.loads(r["texto"])["titulo"] == "ok"


def test_modo_usuario_sin_clave_cae_a_extractivo():
    r = gateway.generate(
        [{"role": "user", "content": "genera"}],
        modo="usuario",
        proveedor=None,
        modelo=None,
        api_key=None,
        plantilla=lambda: {"titulo": "fallback"},
    )
    assert r["proveedor"] == "extractivo"


def test_build_offline_usa_snapshot(built_db):
    # El snapshot (seed) es local; el build no depende de red.
    from faro import db

    conn = db.connect(built_db)
    n = conn.execute("SELECT COUNT(*) c FROM noticia").fetchone()[0]
    conn.close()
    assert n >= 100


def test_sin_red_agente_y_bandeja_responden(built_db, monkeypatch):
    """Bloquea la red (httpx/socket) y verifica que el agente y la bandeja funcionan."""
    import socket

    import httpx

    from faro import db
    from faro.agent import loop, tools

    def _bloquear(*a, **k):
        raise httpx.ConnectError("red bloqueada en test")

    monkeypatch.setattr(httpx.Client, "send", _bloquear)
    monkeypatch.setattr(
        socket, "create_connection", lambda *a, **k: (_ for _ in ()).throw(OSError("offline"))
    )

    conn = db.connect(built_db)
    r = loop.consultar("¿Qué cinco temas merecen revisión hoy?", conn)
    assert r["respuesta"]
    top = tools.ranking(conn, "editorial", 5)
    assert len(top) >= 1
    conn.close()
