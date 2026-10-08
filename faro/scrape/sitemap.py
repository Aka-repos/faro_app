"""Sitemap: lista URLs (soporta sitemapindex y news-sitemap) (H1–H2)."""

from __future__ import annotations

import re
from datetime import UTC, datetime

import config.settings as S

_LOC = re.compile(r"<loc>\s*([^<]+?)\s*</loc>", re.I)
_LAST_MOD = re.compile(r"<lastmod>\s*([^<]+?)\s*</lastmod>", re.I)
_PUB_DATE = re.compile(r"<news:publication_date>\s*([^<]+?)\s*</news:publication_date>", re.I)
_NEWS_TITLE = re.compile(r"<news:title>\s*([^<]+?)\s*</news:title>", re.I)


def _iso(s: str | None) -> str | None:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
        return dt.astimezone(UTC).isoformat()
    except ValueError:
        return None


def _en_ventana(s: str | None) -> bool:
    if not s:
        return True  # sin fecha: se acepta y decide la validación
    dt = _iso(s)
    if not dt:
        return True
    return S.VENTANA_INICIO.isoformat() <= dt < S.VENTANA_FIN.isoformat()


def parse_sitemap(url: str, client=None) -> list[dict]:
    """Devuelve [{url, fecha_publicacion, titulo}] filtrado por la ventana D-01."""
    if not url:
        return []
    try:
        if client is not None:
            r = client.get(url)
            if r is None:
                return []
            text = r.text
        else:
            import httpx

            r = httpx.get(url, timeout=S.HTTP_TIMEOUT, headers={"User-Agent": S.USER_AGENT})
            r.raise_for_status()
            text = r.text
    except Exception:  # noqa: BLE001
        return []

    # Índice de sitemaps: devuelve los <loc> hijos como URLs planas (el recolector los visita).
    if "<sitemapindex" in text.lower():
        return [
            {
                "url": m.group(1).strip(),
                "fecha_publicacion": None,
                "titulo": None,
                "es_indice": True,
            }
            for m in _LOC.finditer(text)
        ]

    out = []
    for block in re.split(r"<url>", text)[1:]:
        loc = _LOC.search(block)
        if not loc:
            continue
        m = _PUB_DATE.search(block)
        if m:
            fecha = m.group(1).strip()
        else:
            lm = _LAST_MOD.search(block)
            fecha = lm.group(1).strip() if lm else None
        titulo = _NEWS_TITLE.search(block)
        fecha_iso = _iso(fecha)
        if not _en_ventana(fecha_iso):
            continue
        out.append(
            {
                "url": loc.group(1).strip(),
                "fecha_publicacion": fecha_iso,
                "titulo": titulo.group(1).strip() if titulo else None,
                "es_indice": False,
            }
        )
    return out
