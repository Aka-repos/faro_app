"""Sitemap: lista URLs de un sitemap.xml (H1–H2)."""

from __future__ import annotations

import re

import httpx

import config.settings as S

_LAST_MOD = re.compile(r"<lastmod>\s*([^<]+?)\s*</lastmod>", re.I)


def parse_sitemap(url: str, client: httpx.Client | None = None) -> list[dict]:
    """Devuelve URLs con fecha si el sitemap las trae."""
    if not url:
        return []
    try:
        if client is not None:
            r = client.get(url)
        else:
            r = httpx.get(url, timeout=S.HTTP_TIMEOUT, headers={"User-Agent": S.USER_AGENT})
        r.raise_for_status()
        text = r.text
    except Exception:  # noqa: BLE001
        return []

    out = []
    # Bloques <url> con <loc> y opcional <lastmod>.
    for block in re.split(r"<url>", text)[1:]:
        loc = re.search(r"<loc>\s*([^<]+?)\s*</loc>", block, re.I)
        if not loc:
            continue
        lm = _LAST_MOD.search(block)
        out.append(
            {
                "url": loc.group(1).strip(),
                "fecha_publicacion": lm.group(1).strip() if lm else None,
            }
        )
    return out
