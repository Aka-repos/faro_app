"""Prueba por niveles del modelo configurado en .env (H-8). No imprime la clave.

Uso:  uv run python scripts/probar_llm.py            (niveles 1 a 3)
      uv run python scripts/probar_llm.py --local    (agente con Ollama)
"""

from __future__ import annotations

import sys
import time

import config.settings as S
from faro import db
from faro.agent.loop import consultar
from faro.llm import gateway, providers

PREGUNTAS = [
    ("¿Cuál fue la variación del IMAE en julio de 2026?", "responder con cita OF:inec"),
    ("¿Qué calificación dio S&P a Panamá en septiembre de 2026?", "responder con cita N:"),
    ("¿Cuántos tránsitos diarios permitirá el Canal por El Niño?", "mostrar 32 y 34"),
    ("¿Cuántos turistas visitaron Panamá en 1990?", "abstenerse"),
]


def nivel1() -> bool:
    print("\n== Nivel 1 · conexión directa ==")
    print(f"proveedor={S.LLM_PROVEEDOR!r} modelo={S.LLM_MODELO!r} clave={'sí' if S.LLM_API_KEY else 'NO'}")
    t0 = time.time()
    try:
        r = providers.call_litellm(
            [{"role": "user", "content": "Responde solo con la palabra: ok"}],
            S.LLM_PROVEEDOR,
            S.LLM_MODELO,
            S.LLM_API_KEY,
            timeout=30,
        )
    except Exception as e:  # noqa: BLE001
        print("FALLÓ:", str(e)[:300])
        return False
    print(f"respuesta={r['texto'][:60]!r}  tokens={r.get('tokens_in')}/{r.get('tokens_out')}  "
          f"costo_usd={r.get('costo_usd')}  {time.time() - t0:.1f}s")
    return True


def nivel2() -> dict:
    print("\n== Nivel 2 · capacidades ==")
    caps = gateway.detectar_capacidades(S.LLM_PROVEEDOR, S.LLM_MODELO, S.LLM_API_KEY)
    print(caps)
    return caps


def nivel3(llm_cfg: dict) -> None:
    print(f"\n== Nivel 3 · agente con datos reales ({llm_cfg.get('proveedor')}) ==")
    conn = db.connect()
    for pregunta, esperado in PREGUNTAS:
        t0 = time.time()
        r = consultar(pregunta, conn, llm_cfg=llm_cfg)
        meta = r.get("meta", {})
        citas = sorted({a.get("evidencia_id", "?") for a in r.get("afirmaciones", [])})
        print(f"\nP: {pregunta}\n   esperado: {esperado}")
        print(f"   proveedor={meta.get('proveedor')} modo={meta.get('modo')} {time.time() - t0:.1f}s "
              f"abstención={r.get('abstencion')}")
        if meta.get("error_llm"):
            print(f"   ⚠️ el LLM falló y respondió el determinista: {meta['error_llm']}")
        print(f"   citas={citas[:5]}")
        print(f"   respuesta: {r.get('respuesta', '')[:300]}")
    conn.close()


if __name__ == "__main__":
    if "--local" in sys.argv:
        nivel3({"modo": "local", "proveedor": "ollama", "modelo": S.OLLAMA_MODELO})
        sys.exit(0)
    if not nivel1():
        sys.exit(1)
    caps = nivel2()
    nivel3({"modo": "usuario", "proveedor": S.LLM_PROVEEDOR, "modelo": S.LLM_MODELO,
            "api_key": S.LLM_API_KEY, "capacidades": caps})
