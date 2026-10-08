"""Cortesía de red (D-07): clientes que respetan robots.txt, pausan por dominio y
guardan evidencia de origen.

Reglas:
- User-Agent identificado (config.settings.USER_AGENT).
- robots.txt con caché por dominio; si no responde, se trata como permitido **pero se registra**.
- Pausa por dominio (rate_limit_s de fuentes.yaml, por defecto 3 s).
- 2 reintentos con espera exponencial solo para 429/5xx.
- Cada respuesta cruda se guarda comprimida en data/raw/http/ con un índice JSONL.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import time
from datetime import UTC, datetime
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

import config.settings as S

_HTTP_DIR = S.RAW_DIR / "http"
_INDEX = _HTTP_DIR / "index.jsonl"


class PoliteClient:
    """httpx.Client con cortesía: robots, pausa por dominio, reintentos y evidencia."""

    def __init__(self, rate_limit_s: float = 3.0) -> None:
        self.client = httpx.Client(
            timeout=S.HTTP_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": S.USER_AGENT},
        )
        self.rate_limit_s = rate_limit_s
        self._ultima: dict[str, float] = {}
        self._robots: dict[str, bool | None] = {}
        self.registro: list[dict] = []

    # --- robots -----------------------------------------------------------
    def robots_permite(self, url: str) -> tuple[bool, str]:
        """Devuelve (permitido, nota). Trata robots.txt inaccesible como permitido, registrado."""
        dominio = urlparse(url).netloc
        if dominio in self._robots:
            return self._robots[dominio], "cache"
        try:
            rp = RobotFileParser()
            rp.set_url(f"{urlparse(url).scheme}://{dominio}/robots.txt")
            rp.read()
            self._robots[dominio] = rp.can_fetch(S.USER_AGENT, url)
            return self._robots[dominio], "robots.txt leído"
        except Exception as e:  # noqa: BLE001
            self._robots[dominio] = None  # None = sin robots.txt (permitir, registrado)
            return None, f"robots.txt inaccesible: {e}"

    # --- pausa por dominio -------------------------------------------------
    def _pausar(self, url: str) -> None:
        dominio = urlparse(url).netloc
        ahora = time.monotonic()
        espera = self.rate_limit_s - (ahora - self._ultima.get(dominio, 0.0))
        if espera > 0:
            time.sleep(espera)
        self._ultima[dominio] = time.monotonic()

    # --- petición con reintentos y evidencia ------------------------------
    def get(
        self, url: str, fuente_id: str = "", sin_reintentos: bool = False, **kwargs
    ) -> httpx.Response | None:
        self._pausar(url)
        permitido, nota = self.robots_permite(url)
        if permitido is False:
            self.registro.append(
                {
                    "url": url,
                    "fuente_id": fuente_id,
                    "status": "robots",
                    "nota": nota,
                    "fecha_UTC": _ahora(),
                }
            )
            return None

        # Sin reintentos (para GDELT, que gestiona sus propios 10/20/40 s): una
        # sola petición y devuelve la respuesta tal cual (incluido 429), no None.
        if sin_reintentos:
            try:
                resp = self.client.get(url, **kwargs)
            except httpx.HTTPError as e:  # noqa: BLE001
                self.registro.append(
                    {
                        "url": url,
                        "fuente_id": fuente_id,
                        "status": "error",
                        "nota": str(e),
                        "fecha_UTC": _ahora(),
                    }
                )
                return None
            self._guardar(url, fuente_id, resp.status_code, resp.content)
            return resp

        last_exc: Exception | None = None
        for intento in range(3):
            try:
                resp = self.client.get(url, **kwargs)
                self._guardar(url, fuente_id, resp.status_code, resp.content)
                if resp.status_code in (429, 500, 502, 503, 504) and intento < 2:
                    time.sleep(2**intento)
                    continue
                resp.raise_for_status()
                return resp
            except httpx.HTTPError as e:  # noqa: BLE001
                last_exc = e
                if intento < 2:
                    time.sleep(2**intento)
        self.registro.append(
            {
                "url": url,
                "fuente_id": fuente_id,
                "status": "error",
                "nota": str(last_exc),
                "fecha_UTC": _ahora(),
            }
        )
        return None

    # --- evidencia de origen ----------------------------------------------
    def _guardar(self, url: str, fuente_id: str, status: int, content: bytes) -> None:
        _HTTP_DIR.mkdir(parents=True, exist_ok=True)
        nombre = f"{fuente_id or 'anon'}/{hashlib.sha1(url.encode()).hexdigest()}.gz"
        destino = _HTTP_DIR / nombre
        destino.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(destino, "wb") as fh:
            fh.write(content)
        sha = hashlib.sha256(content).hexdigest()
        fila = {
            "url": url,
            "fuente_id": fuente_id,
            "status": status,
            "fecha_UTC": _ahora(),
            "sha256": sha,
        }
        self.registro.append(fila)
        with open(_INDEX, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(fila, ensure_ascii=False) + "\n")


def _ahora() -> str:
    return datetime.now(UTC).isoformat()


def robots_permite(url: str) -> bool | None:
    """Helper independiente con caché por proceso (para módulos sin PoliteClient)."""
    c = PoliteClient(rate_limit_s=0)
    return c.robots_permite(url)[0]
