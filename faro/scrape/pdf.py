"""PDF: extracción de tablas de boletines SBP con pdfplumber (B-03)."""

from __future__ import annotations

import io

import httpx

import config.settings as S

try:
    import pdfplumber

    _PDF = True
except Exception:  # noqa: BLE001
    _PDF = False


def extract_pdf_tables(url: str) -> list[dict]:
    """Descarga un PDF y devuelve filas con su número de página de origen."""
    if not _PDF:
        return []
    try:
        r = httpx.get(url, timeout=S.HTTP_TIMEOUT, headers={"User-Agent": S.USER_AGENT})
        r.raise_for_status()
    except Exception:  # noqa: BLE001
        return []
    out = []
    try:
        with pdfplumber.open(io.BytesIO(r.content)) as pdf:
            for pno, page in enumerate(pdf.pages, start=1):
                for table in page.extract_tables() or []:
                    for row in table:
                        cells = [("" if c is None else str(c).strip()) for c in row]
                        if any(cells):
                            out.append({"pagina": pno, "fila": cells})
    except Exception:  # noqa: BLE001
        return []
    return out
