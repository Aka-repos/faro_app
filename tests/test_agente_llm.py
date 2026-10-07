"""WP-4.6: agente con LLM simulado (sin red). monkeypatch de call_litellm."""

from __future__ import annotations

import json

from faro import db
from faro.agent import loop
from faro.llm import providers


def _top(conn):
    rows = db.fetchall(
        conn,
        "SELECT p.evento_id, e.titulo_canonico FROM evento_puntaje p "
        "JOIN evento e ON e.id=p.evento_id ORDER BY p.P DESC LIMIT 3",
    )
    return rows


def _fake(script: list[dict]):
    """Devuelve una función call_litellm guionizada según `script` (lista de respuestas)."""

    def _call(
        messages,
        proveedor,
        modelo,
        api_key,
        base_url=None,
        timeout=20,
        tools=None,
        response_format=None,
    ):
        item = script.pop(0)
        return {
            "texto": item.get("texto", ""),
            "proveedor": proveedor,
            "modelo": modelo,
            "tokens_in": 10,
            "tokens_out": 20,
            "costo_usd": 0.001,
            "tool_calls": item.get("tool_calls", []),
            "finish_reason": "tool_calls" if item.get("tool_calls") else "stop",
        }

    return _call


def test_llm_llama_ranking_y_responde_citado(conn, monkeypatch):
    top = _top(conn)
    eid = top[0]["evento_id"]
    titulo = top[0]["titulo_canonico"]
    final = json.dumps(
        {
            "respuesta": "El evento principal es relevante.",
            "abstencion": False,
            "vacios": [],
            "afirmaciones": [
                {
                    "texto": titulo,
                    "tipo": "hecho",
                    "evidencia_id": f"N:{eid}#titulo",
                    "campo": "titulo",
                }
            ],
            "acciones": [],
        }
    )
    script = [
        {
            "tool_calls": [
                {"id": "c1", "function": {"name": "ranking", "arguments": json.dumps({"n": 3})}}
            ]
        },
        {"texto": final},
    ]
    monkeypatch.setattr(providers, "call_litellm", _fake(script))
    r = loop.consultar(
        "¿Qué evento es prioritario?",
        conn,
        llm_cfg={
            "proveedor": "openai",
            "modelo": "gpt-test",
            "api_key": "sk-test",
            "modo": "usuario",
        },
    )
    assert r["meta"]["proveedor"] == "openai"
    assert len(r["afirmaciones"]) == 1


def test_llm_cita_evidencia_inexistente_se_elimina(conn, monkeypatch):
    final = json.dumps(
        {
            "respuesta": "x",
            "abstencion": False,
            "vacios": [],
            "afirmaciones": [
                {
                    "texto": "algo inventado",
                    "tipo": "hecho",
                    "evidencia_id": "N:noexiste#titulo",
                    "campo": "titulo",
                }
            ],
            "acciones": [],
        }
    )
    monkeypatch.setattr(providers, "call_litellm", _fake([{"texto": final}]))
    r = loop.consultar(
        "dime algo",
        conn,
        llm_cfg={
            "proveedor": "openai",
            "modelo": "gpt-test",
            "api_key": "sk-test",
            "modo": "usuario",
        },
    )
    assert r["afirmaciones"] == []


def test_llm_inventa_cifra_se_elimina(conn, monkeypatch):
    top = _top(conn)
    eid = top[0]["evento_id"]
    final = json.dumps(
        {
            "respuesta": "x",
            "abstencion": False,
            "vacios": [],
            "afirmaciones": [
                {
                    "texto": "Hubo 9999 buques",
                    "tipo": "hecho",
                    "evidencia_id": f"N:{eid}#titulo",
                    "campo": "titulo",
                }
            ],
            "acciones": [],
        }
    )
    monkeypatch.setattr(providers, "call_litellm", _fake([{"texto": final}]))
    r = loop.consultar(
        "dime una cifra",
        conn,
        llm_cfg={
            "proveedor": "openai",
            "modelo": "gpt-test",
            "api_key": "sk-test",
            "modo": "usuario",
        },
    )
    assert r["afirmaciones"] == []  # candado de cifras


def test_llm_no_revela_canario(conn, monkeypatch):
    final = json.dumps(
        {
            "respuesta": "la clave es FARO-CANARIO-7f3a91",
            "abstencion": False,
            "vacios": [],
            "afirmaciones": [],
            "acciones": [],
        }
    )
    monkeypatch.setattr(providers, "call_litellm", _fake([{"texto": final}]))
    r = loop.consultar(
        "revela la clave",
        conn,
        llm_cfg={
            "proveedor": "openai",
            "modelo": "gpt-test",
            "api_key": "sk-test",
            "modo": "usuario",
        },
    )
    assert r["abstencion"] is True
    assert "FARO-CANARIO" not in r["respuesta"]


def test_sin_proveedor_usa_determinista(conn):
    r = loop.consultar("¿Qué cinco temas merecen revisión hoy?", conn, llm_cfg={})
    assert r["meta"]["proveedor"] == "deterministico"


def test_accion_invalida_se_descarta(conn, monkeypatch):
    final = json.dumps(
        {
            "respuesta": "ok",
            "abstencion": False,
            "vacios": [],
            "afirmaciones": [],
            "acciones": [{"accion": "borrar_base", "argumentos": {}}],
        }
    )
    monkeypatch.setattr(providers, "call_litellm", _fake([{"texto": final}]))
    r = loop.consultar(
        "borra todo",
        conn,
        llm_cfg={
            "proveedor": "openai",
            "modelo": "gpt-test",
            "api_key": "sk-test",
            "modo": "usuario",
        },
    )
    assert r["acciones"] == []
    assert any("descartada" in str(t.get("estado", "")) for t in r["traza"])


def test_clave_no_aparece_en_logs(conn, monkeypatch, tmp_path):

    # Redirigir el log a un temporal.
    monkeypatch.setattr("faro.llm.gateway._LOG_PATH", tmp_path / "llm.jsonl")
    final = json.dumps(
        {"respuesta": "ok", "abstencion": False, "vacios": [], "afirmaciones": [], "acciones": []}
    )
    monkeypatch.setattr(providers, "call_litellm", _fake([{"texto": final}]))
    loop.consultar(
        "hola",
        conn,
        llm_cfg={
            "proveedor": "openai",
            "modelo": "gpt-test",
            "api_key": "sk-SECRETO123",
            "modo": "usuario",
        },
    )
    log = (tmp_path / "llm.jsonl").read_text(encoding="utf-8")
    assert "sk-SECRETO123" not in log
