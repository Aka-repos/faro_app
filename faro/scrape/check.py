"""Verificación de fuentes (H1): robots.txt, método funcional y volumen estimado."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

import config.settings as S
from faro.loaders import load_fuentes


@dataclass
class FuenteCheck:
    id: str
    nombre: str
    metodo: str
    robots_ok: bool | None = None
    robots_nota: str = ""
    metodo_ok: bool = False
    metodo_nota: str = ""
    volumen_estimado: int = 0
    ultimo_periodo: str | None = None
    condiciones_registradas: bool = False
    errores: list[str] = field(default_factory=list)


def _robots_for(url_base: str) -> tuple[bool | None, str]:
    if not url_base:
        return None, "sin url_base"
    try:
        parsed = urlparse(url_base)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        with httpx.Client(timeout=S.HTTP_TIMEOUT, follow_redirects=True) as client:
            r = client.get(robots_url)
        if r.status_code >= 400:
            return None, f"sin robots.txt (HTTP {r.status_code})"
        rp.parse(r.text.splitlines())
        return rp.can_fetch(S.USER_AGENT, url_base), "robots.txt leído"
    except Exception as e:  # noqa: BLE001
        return None, f"robots.txt no accesible: {e}"


def check_fuentes() -> list[FuenteCheck]:
    """Revisa cada fuente candidata y escribe `data/reports/fuentes_check.json`."""
    fuentes = load_fuentes()
    resultados: list[FuenteCheck] = []
    client = httpx.Client(
        timeout=S.HTTP_TIMEOUT, follow_redirects=True, headers={"User-Agent": S.USER_AGENT}
    )
    for f in fuentes:
        ch = FuenteCheck(
            id=f["id"],
            nombre=f["nombre"],
            metodo=f.get("metodo", ""),
            condiciones_registradas=bool(f.get("condiciones")),
        )
        ch.robots_ok, ch.robots_nota = _robots_for(f.get("url_base", ""))
        try:
            if f.get("metodo") == "rss":
                from faro.scrape.rss import parse_rss

                items = parse_rss(f.get("rss_url", ""), client=client)
                ch.metodo_ok = len(items) > 0
                ch.metodo_nota = f"{len(items)} entradas"
                ch.volumen_estimado = len(items) * 4  # estimación grosera/mes
            elif f.get("metodo") == "api":
                # Sondeo ligero de la API (sin paginar).
                from faro.scrape.apis import _probe_api

                n = _probe_api(f["id"], client)
                ch.metodo_ok = n is not None
                ch.metodo_nota = f"sondeo {n} registros"
                ch.volumen_estimado = (n or 0) * 12
            else:
                # sitemap / html / pdf: HEAD a la url_base.
                r = client.head(f.get("url_base", ""))
                ch.metodo_ok = r.status_code < 400
                ch.metodo_nota = f"HTTP {r.status_code}"
        except Exception as e:  # noqa: BLE001
            ch.errores.append(str(e))
            ch.metodo_nota = f"error: {e}"
        time.sleep(0.2)
        resultados.append(ch)

    S.ensure_dirs()
    (S.REPORTS_DIR / "fuentes_check.json").write_text(
        json.dumps([asdict(c) for c in resultados], ensure_ascii=False, indent=2, default=str)
    )
    return resultados
