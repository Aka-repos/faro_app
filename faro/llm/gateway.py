"""Pasarela de LLM (F-10): un cliente, cascada, caché, métricas y enmascarado.

Modos: ``usuario`` (proveedor del usuario) · ``local`` (Ollama) · ``auto``
(usuario -> Ollama -> extractivo). Timeouts 20 s (nube) / 60 s (local). Cada
llamada se registra en JSONL (proveedor, modelo, tokens, costo, latencia) con la
clave enmascarada.
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
    """Registra una ejecución (agente o generación) en data/logs/llm.jsonl.

    Es la misma fuente que lee la vista Comparador, así que cada consulta del
    agente aparece tanto en el Agente como en el Comparador.
    """
    _log(entry)


def detectar_capacidades(proveedor: str, modelo: str, api_key: str) -> dict:
    """Sondeo corto de capacidades (sección 7.1). Devuelve flags por capacidad."""
    caps = {"json_esquema": None, "herramientas": None, "precio_conocido": False}
    if not proveedor or not modelo:
        return caps
    try:
        r = providers.call_litellm(
            [{"role": "user", "content": 'Responde con el JSON exacto: {"ok": true}'}],
            proveedor,
            modelo,
            api_key,
            timeout=10,
        )
        caps["json_esquema"] = r["texto"].strip().startswith("{")
        caps["precio_conocido"] = r.get("costo_usd", 0.0) >= 0
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
) -> dict:
    """Ejecuta la cascada y devuelve el resultado con metadatos de ejecución."""
    modo = modo or S.LLM_MODO
    proveedor = proveedor or S.LLM_PROVEEDOR
    modelo = modelo or S.LLM_MODELO
    api_key = api_key or S.LLM_API_KEY
    ids = ids_evidencia or []

    key = cache.cache_key(prompt_version, lente, ids, modelo or "extractivo")
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
    # El extractivo es siempre el último respaldo: la demo nunca se cae (D-06, T10).
    orden.append("extractivo")

    for etapa in orden:
        try:
            if etapa == "usuario":
                if not proveedor or not modelo or not api_key:
                    continue
                r = providers.call_litellm(
                    mensajes, proveedor, modelo, api_key, base_url, timeout=20
                )
            elif etapa == "local":
                r = providers.call_ollama(mensajes, modelo=S.OLLAMA_MODELO, timeout=60)
            else:
                # extractivo: plantilla sin LLM.
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
                }

            latencia_ms = int((time.time() - t0) * 1000)
            resultado = {
                "texto": r["texto"],
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

    # No debería llegar aquí (extractivo siempre funciona), pero por seguridad:
    raise RuntimeError("ningún proveedor disponible")


def _enmascarar_dict(d: dict) -> dict:
    return {k: (_enmascarar(v) if isinstance(v, str) else v) for k, v in d.items()}
