"""HTML: metadatos de artículos (nunca el cuerpo completo) con PoliteClient."""

from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse

import config.settings as S
from faro.scrape.rss import detectar_agencia

try:
    import trafilatura

    _TRAFILATURA = True
except Exception:  # noqa: BLE001
    _TRAFILATURA = False


def _url_id(url: str) -> str:
    u = urlparse(url.strip())
    return "n-" + hashlib.sha1(f"{u.netloc.lower()}{u.path.rstrip('/')}".encode()).hexdigest()[:16]


def extract_article(
    url: str, html: str | None = None, client=None, fuente_id: str = "", medio: str = ""
) -> dict:
    """Extrae título, fecha y resumen publicados (≤400 caracteres). Nunca guarda el cuerpo."""
    if html is None:
        if client is not None:
            resp = client.get(url, fuente_id=fuente_id)
            if resp is None:
                return {}
            html = resp.text
        else:
            import httpx

            try:
                html = httpx.get(
                    url, timeout=S.HTTP_TIMEOUT, headers={"User-Agent": S.USER_AGENT}
                ).text
            except Exception:  # noqa: BLE001
                return {}

    result: dict = {"url": url}
    if _TRAFILATURA:
        try:
            doc = trafilatura.extract(html, url=url, output_format="json", with_metadata=True)
            if doc:
                import json

                meta = json.loads(doc)
                result["titulo"] = (meta.get("title") or "").strip()
                result["fecha_publicacion"] = meta.get("date")
                resumen = (meta.get("description") or "").strip()
                if not resumen and meta.get("text"):
                    resumen = meta["text"][:400]
                result["resumen"] = resumen[:400] if resumen else None
        except Exception:  # noqa: BLE001
            pass
    if not result.get("titulo"):
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
        result["titulo"] = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
    if not result.get("resumen"):
        m = re.search(
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)', html, re.I
        )
        result["resumen"] = m.group(1).strip()[:400] if m else None

    titulo = result.get("titulo", "")
    resumen = result.get("resumen", "")
    es_agencia, agencia = detectar_agencia(titulo, resumen)
    return {
        "tipo": "noticia",
        "id": _url_id(url),
        "fuente_id": fuente_id,
        "titulo": titulo,
        "url": url,
        "medio": medio or fuente_id,
        "dominio": urlparse(url).netloc.lower(),
        "idioma": "es",
        "fecha_publicacion": result.get("fecha_publicacion"),
        "fecha_deteccion": result.get("fecha_publicacion"),
        "fecha_extraccion": result.get("fecha_extraccion"),
        "alcance_texto": "resumen" if resumen else ("metadatos" if titulo else "titular"),
        "resumen": resumen or None,
        "es_agencia": es_agencia,
        "agencia": agencia,
        "sintetico": False,
        "via": "html",
    }
