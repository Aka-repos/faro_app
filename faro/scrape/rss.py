"""RSS: feedparser, con esquema RegistroNoticia (F-01, H1–H2)."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from urllib.parse import urlparse

import feedparser

_AGENCIAS = ["EFE", "AFP", "AP", "Reuters", "Notimex", "DPA"]


def _iso(dt) -> str | None:
    if not dt:
        return None
    try:
        return dt.astimezone(UTC).isoformat()
    except Exception:  # noqa: BLE001
        return None


def _url_normalizada(url: str) -> str:
    u = urlparse(url.strip())
    return f"{u.netloc.lower()}{u.path.rstrip('/')}"


def _url_id(url: str) -> str:
    return "n-" + hashlib.sha1(_url_normalizada(url).encode("utf-8")).hexdigest()[:16]


def _dominio(url: str) -> str:
    return urlparse(url).netloc.lower()


def _limpiar_html(texto: str) -> str:
    return re.sub(r"<[^>]+>", " ", texto or "").strip()


def detectar_agencia(titulo: str, resumen: str = "") -> tuple[bool, str | None]:
    """Detecta agencia declarada (EFE/AFP/AP/Reuters) en título o resumen."""
    texto = f"{titulo} {resumen}"
    for a in _AGENCIAS:
        if re.search(rf"\b{re.escape(a)}\b", texto, re.I):
            return True, a
    return False, None


def parse_rss(url: str, fuente_id: str = "", medio: str = "", client=None) -> list[dict]:
    """Descarga un RSS y normaliza entradas al esquema RegistroNoticia."""
    if not url:
        return []
    try:
        if client is not None:
            r = client.get(url)
            if r is None:
                return []
            feed = feedparser.parse(r.content)
        else:
            feed = feedparser.parse(url)
    except Exception:  # noqa: BLE001
        return []

    hoy = datetime.now(UTC).isoformat()
    out = []
    for e in feed.entries[:200]:
        url_e = getattr(e, "link", "")
        if not url_e:
            continue
        pub = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
        titulo = _limpiar_html(getattr(e, "title", ""))[:300]
        resumen = _limpiar_html(getattr(e, "summary", ""))[:600]
        es_agencia, agencia = detectar_agencia(titulo, resumen)
        out.append(
            {
                "tipo": "noticia",
                "id": _url_id(url_e),
                "fuente_id": fuente_id,
                "titulo": titulo,
                "url": url_e,
                "medio": medio or fuente_id,
                "dominio": _dominio(url_e),
                "idioma": "es",
                "fecha_publicacion": _iso(pub),
                "fecha_deteccion": _iso(pub),
                "fecha_extraccion": hoy,
                "alcance_texto": "resumen" if resumen else "titular",
                "resumen": resumen or None,
                "es_agencia": es_agencia,
                "agencia": agencia,
                "sintetico": False,
                "via": "rss",
            }
        )
    return out
