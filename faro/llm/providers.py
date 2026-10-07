"""Proveedores LLM (F-10, L-01): Ollama local y LiteLLM para proveedores de pago."""

from __future__ import annotations

import config.settings as S


def call_ollama(messages: list[dict], modelo: str | None = None, timeout: int = 60) -> dict:
    """Llama a Ollama (endpoint compatible OpenAI). Sin clave."""
    import httpx

    modelo = modelo or S.OLLAMA_MODELO
    url = f"{S.OLLAMA_BASE_URL.rstrip('/')}/v1/chat/completions"
    payload = {"model": modelo, "messages": messages, "temperature": 0.2}
    try:
        r = httpx.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        return {
            "texto": data["choices"][0]["message"]["content"],
            "proveedor": "ollama",
            "modelo": modelo,
            "tokens_in": data.get("usage", {}).get("prompt_tokens", 0),
            "tokens_out": data.get("usage", {}).get("completion_tokens", 0),
            "costo_usd": 0.0,
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
) -> dict:
    """Llama a un proveedor de pago vía LiteLLM."""
    try:
        import litellm  # type: ignore
    except Exception as e:  # noqa: BLE001
        raise RuntimeError("litellm no instalado") from e

    kwargs = {"model": f"{proveedor}/{modelo}", "messages": messages, "timeout": timeout}
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["api_base"] = base_url
    try:
        resp = litellm.completion(**kwargs)
        return {
            "texto": resp.choices[0].message.content,
            "proveedor": proveedor,
            "modelo": modelo,
            "tokens_in": getattr(resp.usage, "prompt_tokens", 0),
            "tokens_out": getattr(resp.usage, "completion_tokens", 0),
            "costo_usd": float(
                getattr(resp, "_hidden_params", {}).get("response_cost", 0.0) or 0.0
            ),
        }
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"{proveedor}/{modelo} falló: {e}") from e
