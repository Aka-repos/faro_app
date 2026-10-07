"""Proveedores LLM (F-10, L-01): Ollama local y LiteLLM para proveedores de pago.

Ambos soportan `tools` (llamadas a herramientas) y `response_format` (JSON Schema).
"""

from __future__ import annotations

import json

import config.settings as S


def call_ollama(
    messages: list[dict],
    modelo: str | None = None,
    timeout: int = 60,
    tools: list[dict] | None = None,
    response_format: dict | None = None,
) -> dict:
    """Llama a Ollama (endpoint compatible OpenAI). Sin clave."""
    import httpx

    modelo = modelo or S.OLLAMA_MODELO
    url = f"{S.OLLAMA_BASE_URL.rstrip('/')}/v1/chat/completions"
    payload: dict = {"model": modelo, "messages": messages, "temperature": 0.2}
    if tools:
        payload["tools"] = tools
    if response_format:
        payload["response_format"] = {"type": "json_schema", "json_schema": response_format}
    try:
        r = httpx.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        msg = data["choices"][0]["message"]
        return {
            "texto": msg.get("content") or "",
            "proveedor": "ollama",
            "modelo": modelo,
            "tokens_in": data.get("usage", {}).get("prompt_tokens", 0),
            "tokens_out": data.get("usage", {}).get("completion_tokens", 0),
            "costo_usd": 0.0,
            "tool_calls": msg.get("tool_calls") or [],
            "finish_reason": data["choices"][0].get("finish_reason"),
        }
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"ollama no disponible: {e}") from e


def call_litellm(
    messages: list[dict],
    proveedor: str,
    modelo: str,
    api_key: str,
    base_url: str | None = None,
    timeout: int = 20,
    tools: list[dict] | None = None,
    response_format: dict | None = None,
) -> dict:
    """Llama a un proveedor de pago vía LiteLLM, con tools/response_format opcionales."""
    try:
        import litellm  # type: ignore
    except Exception as e:  # noqa: BLE001
        raise RuntimeError("litellm no instalado") from e

    kwargs = {"model": f"{proveedor}/{modelo}", "messages": messages, "timeout": timeout}
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["api_base"] = base_url
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    if response_format:
        kwargs["response_format"] = {"type": "json_schema", "json_schema": response_format}
    try:
        resp = litellm.completion(**kwargs)
        msg = resp.choices[0].message
        try:
            costo = float(litellm.completion_cost(resp))
        except Exception:  # noqa: BLE001
            costo = None
        return {
            "texto": msg.content or "",
            "proveedor": proveedor,
            "modelo": modelo,
            "tokens_in": getattr(resp.usage, "prompt_tokens", 0),
            "tokens_out": getattr(resp.usage, "completion_tokens", 0),
            "costo_usd": costo,
            "tool_calls": getattr(msg, "tool_calls", None) or [],
            "finish_reason": resp.choices[0].finish_reason,
        }
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"{proveedor}/{modelo} falló: {e}") from e


def tool_calls_a_dicts(tool_calls) -> list[dict]:
    """Normaliza tool_calls (LiteLLM/Ollama) a [{id, nombre, argumentos}]."""
    out = []
    for tc in tool_calls or []:
        fn = getattr(tc, "function", None) or tc.get("function", {})
        nombre = getattr(fn, "name", None) or fn.get("name", "")
        args = getattr(fn, "arguments", None) or fn.get("arguments", "{}")
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:  # noqa: BLE001
                args = {}
        out.append(
            {
                "id": getattr(tc, "id", None) or tc.get("id", ""),
                "nombre": nombre,
                "argumentos": args,
            }
        )
    return out
