"""M3: el paquete/boletín pasa por el LLM (simulado) y el verificador."""

from __future__ import annotations

import json

from faro.agent import tools
from faro.lenses import banca as lente_banca
from faro.lenses import editorial as lente_editorial
from faro.llm import providers


def _evento(conn):
    top = tools.ranking(conn, "editorial", 1)[0]
    return tools.abrir_evento(conn, top["evento_id"])


def _fake_litellm(texto):
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
        return {
            "texto": texto,
            "proveedor": proveedor,
            "modelo": modelo,
            "tokens_in": 5,
            "tokens_out": 10,
            "costo_usd": 0.001,
            "tool_calls": [],
            "finish_reason": "stop",
        }

    return _call


def test_brief_largo_se_recorta(conn, monkeypatch):
    ev = _evento(conn)
    brief_largo = "palabra " * 400
    texto = json.dumps(
        {
            "titulo": "t",
            "enfoque": "e",
            "brief": brief_largo,
            "preguntas": [],
            "fuentes": [],
            "verificaciones": [],
            "guion": "guion corto",
            "copy_digital": "copy corto",
            "afirmaciones": [],
            "vacios": [],
        }
    )
    monkeypatch.setattr(providers, "call_litellm", _fake_litellm(texto))
    out = lente_editorial.generar_paquete(
        ev,
        conn,
        llm_cfg={"proveedor": "openai", "modelo": "gpt", "api_key": "sk-test", "modo": "usuario"},
    )
    assert len(out["brief"].split()) <= 250
    assert out.get("recortado") is True


def test_cita_inexistente_se_elimina(conn, monkeypatch):
    ev = _evento(conn)
    texto = json.dumps(
        {
            "titulo": "t",
            "enfoque": "e",
            "brief": "b",
            "preguntas": [],
            "fuentes": [],
            "verificaciones": [],
            "guion": "g",
            "copy_digital": "c",
            "afirmaciones": [
                {
                    "texto": "algo inventado",
                    "tipo": "hecho",
                    "evidencia_id": "N:noexiste#titulo",
                    "campo": "titulo",
                }
            ],
            "vacios": [],
        }
    )
    monkeypatch.setattr(providers, "call_litellm", _fake_litellm(texto))
    out = lente_editorial.generar_paquete(
        ev,
        conn,
        llm_cfg={"proveedor": "openai", "modelo": "gpt", "api_key": "sk-test", "modo": "usuario"},
    )
    assert out["afirmaciones"] == []


def test_sin_proveedor_usa_plantilla(conn, monkeypatch):
    # Sin proveedor (modo usuario) y sin Ollama -> cae a la plantilla extractiva.
    def _sin_ollama(*a, **k):
        raise RuntimeError("ollama apagado en test")

    monkeypatch.setattr(providers, "call_ollama", _sin_ollama)
    ev = _evento(conn)
    out = lente_editorial.generar_paquete(ev, conn, llm_cfg={"modo": "usuario"})
    assert out["_meta"]["proveedor"] == "extractivo"


def test_boletin_frase_prohibida_bloqueada(conn, monkeypatch):
    ev = _evento(conn)
    texto = json.dumps(
        {
            "resumen": "r",
            "sectores": [],
            "horizonte": "h",
            "evidencia": [],
            "preguntas": ["a", "b", "c"],
            "afirmaciones": [
                {
                    "texto": "recomendamos comprar acciones",
                    "tipo": "observacion",
                    "evidencia_id": None,
                }
            ],
            "observaciones": [],
            "hipotesis": [],
        }
    )
    monkeypatch.setattr(providers, "call_litellm", _fake_litellm(texto))
    out = lente_banca.generar_boletin_sectorial(
        ev,
        conn,
        llm_cfg={"proveedor": "openai", "modelo": "gpt", "api_key": "sk-test", "modo": "usuario"},
    )
    assert all("compra" not in (a.get("texto", "")).lower() for a in out.get("afirmaciones", []))


def test_cifra_inventada_se_elimina(conn, monkeypatch):
    ev = _evento(conn)
    eid_real = None
    for n in ev["noticias"]:
        eid_real = f"N:{n['id']}#titulo"
        break
    texto = json.dumps(
        {
            "titulo": "t",
            "enfoque": "e",
            "brief": "b",
            "preguntas": [],
            "fuentes": [],
            "verificaciones": [],
            "guion": "g",
            "copy_digital": "c",
            "afirmaciones": [
                {
                    "texto": "hubo 9999 buques",
                    "tipo": "hecho",
                    "evidencia_id": eid_real,
                    "campo": "titulo",
                }
            ],
            "vacios": [],
        }
    )
    monkeypatch.setattr(providers, "call_litellm", _fake_litellm(texto))
    out = lente_editorial.generar_paquete(
        ev,
        conn,
        llm_cfg={"proveedor": "openai", "modelo": "gpt", "api_key": "sk-test", "modo": "usuario"},
    )
    assert out["afirmaciones"] == []
