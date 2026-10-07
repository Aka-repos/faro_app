"""HTML: metadatos de artículos con trafilatura (+ Scrapling opcional)."""

from __future__ import annotations

import hashlib
import re

import httpx

import config.settings as S

try:
    import trafilatura

    _TRAFILATURA = True
except Exception:  # noqa: BLE001
    _TRAFILATURA = False


def _slug(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:16]


def extract_article(url: str, html: str | None = None) -> dict:
    """Extrae título, fecha y resumen publicados de una página (nunca el cuerpo completo)."""
    if html is None:
        try:
            html = httpx.get(url, timeout=S.HTTP_TIMEOUT, headers={"User-Agent": S.USER_AGENT}).text
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
                result["resumen"] = resumen
                result["alcance_texto"] = "resumen"
        except Exception:  # noqa: BLE001
            pass
    if not result.get("titulo"):
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
        result["titulo"] = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
    if not result.get("resumen"):
        m = re.search(
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)', html, re.I
        )
        result["resumen"] = m.group(1).strip()[:400] if m else ""
        result["alcance_texto"] = "metadatos"
    result.setdefault("titulo", "")
    result["id"] = f"n-{_slug(url)}"
    return result
