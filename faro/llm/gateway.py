"""Pasarela de LLM (F-10): un cliente, cascada, caché, métricas y enmascarado.

Modos: ``usuario`` (proveedor del usuario) · ``local`` (Ollama) · ``auto``
(usuario -> Ollama -> extractivo). Timeouts 20 s (nube) / 60 s (local). Cada
llamada se registra en JSONL (proveedor, modelo, tokens, costo, latencia) con la
clave enmascarada. Soporta `tools` (llamadas a herramientas) y `esquema` Pydantic.
"""

from __future__ import annotations

import json
import re
import time
from datetime import UTC, datetime

import config.settings as S
from faro.llm import cache, providers

_LOG_PATH = S.DATA_DIR / "logs" / "llm.jsonl"

_KEY_RE = re.compile(r"(sk-[A-Za-z0-9\-_]+|Bearer\s+[A-Za-z0-9\-_\.]+)", re.I)


def _enmascarar(texto: str) -> str:
    return _KEY_RE.sub("[CLAVE_ENMASCARADA]", texto)


def _log(entry: dict) -> None:
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")


def log_ejecucion(entry: dict) -> None:
    """Registra una ejecución (agente o generación) en data/logs/llm.jsonl."""
    _log(entry)


def detectar_capacidades(proveedor: str, modelo: str, api_key: str) -> dict:
    """Sondeo corto de capacidades (sección 7.1)."""
    caps = {"json_esquema": False, "herramientas": False, "precio_conocido": False}
    if not proveedor or not modelo:
        return caps
    try:
        # Sondeo de herramientas con una función ficticia ping().
        r = providers.call_litellm(
            [{"role": "user", "content": "Llama a la herramienta ping."}],
            proveedor,
            modelo,
            api_key,
            timeout=10,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "ping",
                        "description": "Responde pong.",
                        "parameters": {"type": "object", "properties": {}},
                    },
                }
            ],
        )
        caps["herramientas"] = any(
            tc.get("nombre") == "ping" for tc in providers.tool_calls_a_dicts(r["tool_calls"])
        )
        caps["precio_conocido"] = r.get("costo_usd") is not None
    except Exception:  # noqa: BLE001
        caps["herramientas"] = False
    try:
        r = providers.call_litellm(
            [{"role": "user", "content": 'Responde con el JSON exacto: {"ok": true}'}],
            proveedor,
            modelo,
            api_key,
            timeout=10,
            response_format={
                "name": "ok",
                "schema": {"type": "object", "properties": {"ok": {"type": "boolean"}}},
            },
        )
        json.loads(r["texto"])
        caps["json_esquema"] = True
    except Exception:  # noqa: BLE001
        caps["json_esquema"] = False
    return caps


def generate(
    mensajes: list[dict],
    *,
    lente: str = "editorial",
    modo: str | None = None,
    ids_evidencia: list[str] | None = None,
    prompt_version: str = "v1",
    proveedor: str | None = None,
    modelo: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    plantilla: callable | None = None,
    plantilla_args: dict | None = None,
    tools: list[dict] | None = None,
    esquema: type | None = None,
) -> dict:
    """Ejecuta la cascada y devuelve {texto, tool_calls, proveedor, modelo, tokens, costo, latencia}.

    - `tools`: JSON Schema de herramientas (se pasan al proveedor; devuelve `tool_calls`).
    - `esquema`: modelo Pydantic para validar la salida final (1 reintento con el error).
    """
    modo = modo or S.LLM_MODO
    proveedor = proveedor or S.LLM_PROVEEDOR
    modelo = modelo or S.LLM_MODELO
    api_key = api_key or S.LLM_API_KEY
    ids = ids_evidencia or []
    tool_names = [t.get("function", {}).get("name", "") for t in (tools or [])]

    # Incluye el modo en la clave: una corrida 'auto' (cayó a Ollama) no debe reutilizar
    # el caché de una corrida 'usuario' (cayó a extractivo) con el mismo mensaje.
    key = cache.cache_key(
        prompt_version, lente, ids, f"{modo}:{modelo or 'extractivo'}", mensajes, tool_names
    )
    hit = cache.get(key)
    if hit:
        hit["desde_cache"] = True
        return hit

    t0 = time.time()
    if modo == "usuario":
        orden = ["usuario"]
    elif modo == "local":
        orden = ["local"]
    else:
        orden = ["usuario", "local"]
    orden.append("extractivo")  # siempre funciona (D-06, T10)

    response_format = None
    if esquema is not None:
        response_format = {"name": esquema.__name__, "schema": esquema.model_json_schema()}

    for etapa in orden:
        try:
            if etapa == "usuario":
                if not proveedor or not modelo or not api_key:
                    continue
                r = providers.call_litellm(
                    mensajes,
                    proveedor,
                    modelo,
                    api_key,
                    base_url,
                    timeout=20,
                    tools=tools,
                    response_format=response_format,
                )
            elif etapa == "local":
                r = providers.call_ollama(
                    mensajes,
                    modelo=S.OLLAMA_MODELO,
                    timeout=60,
                    tools=tools,
                    response_format=response_format,
                )
            else:
                if plantilla is None:
                    raise RuntimeError("modo extractivo sin plantilla")
                salida = plantilla(**(plantilla_args or {}))
                r = {
                    "texto": json.dumps(salida, ensure_ascii=False),
                    "proveedor": "extractivo",
                    "modelo": "extractivo",
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "costo_usd": 0.0,
                    "tool_calls": [],
                    "finish_reason": "stop",
                }

            # Validar salida final contra el esquema Pydantic (1 reintento).
            if esquema is not None:
                ok, err = _validar_esquema(r["texto"], esquema)
                if not ok:
                    mensajes_reintento = mensajes + [
                        {"role": "assistant", "content": r["texto"]},
                        {
                            "role": "user",
                            "content": f"Tu JSON no cumple el esquema: {err}. Corrígelo.",
                        },
                    ]
                    if etapa == "usuario":
                        r = providers.call_litellm(
                            mensajes_reintento,
                            proveedor,
                            modelo,
                            api_key,
                            base_url,
                            timeout=20,
                            response_format=response_format,
                        )
                    elif etapa == "local":
                        r = providers.call_ollama(
                            mensajes_reintento,
                            modelo=S.OLLAMA_MODELO,
                            timeout=60,
                            response_format=response_format,
                        )
                    ok, err = _validar_esquema(r["texto"], esquema)
                    if not ok:
                        raise RuntimeError(f"esquema inválido tras reintento: {err}")

            latencia_ms = int((time.time() - t0) * 1000)
            resultado = {
                "texto": r["texto"],
                "tool_calls": providers.tool_calls_a_dicts(r.get("tool_calls")),
                "finish_reason": r.get("finish_reason"),
                "proveedor": r["proveedor"],
                "modelo": r["modelo"],
                "tokens_in": r["tokens_in"],
                "tokens_out": r["tokens_out"],
                "costo_usd": r["costo_usd"],
                "latencia_ms": latencia_ms,
                "desde_cache": False,
            }
            _log({**_enmascarar_dict(resultado), "lente": lente, "modo": modo})
            cache.put(key, resultado)
            return resultado
        except Exception as e:  # noqa: BLE001
            _log(
                {
                    "error": _enmascarar(str(e)),
                    "etapa": etapa,
                    "lente": lente,
                    "modo": modo,
                    "ts": datetime.now(UTC).isoformat(),
                }
            )
            continue

    raise RuntimeError("ningún proveedor disponible")


def _validar_esquema(texto: str, esquema: type) -> tuple[bool, str]:
    try:
        data = json.loads(texto)
        esquema.model_validate(data)
        return True, ""
    except Exception as e:  # noqa: BLE001
        return False, str(e)[:300]


def _enmascarar_dict(d: dict) -> dict:
    return {k: (_enmascarar(v) if isinstance(v, str) else v) for k, v in d.items()}
