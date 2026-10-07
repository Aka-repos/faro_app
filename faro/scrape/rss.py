"""RSS: feedparser (H1–H2)."""

from __future__ import annotations

import hashlib
from datetime import UTC

import feedparser


def _iso(dt) -> str | None:
    if not dt:
        return None
    try:
        return dt.astimezone(UTC).isoformat()
    except Exception:  # noqa: BLE001
        return None


def _url_hash(url: str) -> str:
    return hashlib.sha256(url.strip().encode("utf-8")).hexdigest()[:16]


def parse_rss(url: str, client=None) -> list[dict]:
    """Descarga un RSS y normaliza entradas a dicts de noticia cruda."""
    if not url:
        return []
    try:
        if client is not None:
            r = client.get(url)
            r.raise_for_status()
            feed = feedparser.parse(r.content)
        else:
            feed = feedparser.parse(url)
    except Exception:  # noqa: BLE001
        return []

    out = []
    for e in feed.entries[:200]:
        url_e = getattr(e, "link", "")
        pub = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
        out.append(
            {
                "id": f"n-{_url_hash(url_e)}",
                "titulo": getattr(e, "title", "").strip(),
                "url": url_e,
                "fecha_publicacion": _iso(pub),
                "resumen": (getattr(e, "summary", "") or "")[:600],
                "alcance_texto": "resumen",
            }
        )
    return out
