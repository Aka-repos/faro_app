"""Fuentes oficiales (H2): Banco Mundial, USGS, INEC, ACP y SBP.

Regla dura: **nunca inventar un valor**. Si una fuente no se puede automatizar en
~1 h, se transcribe a mano en `data/raw/manual/<fuente>.csv` (trazable) o se deja
faltante. Aquí no se fabrican series.
"""

from __future__ import annotations

import csv
import re
import sys
from datetime import UTC, datetime

import config.settings as S
from faro.scrape import apis

WB_INDICATORS = apis.WB_INDICATORS
WB_COUNTRIES = apis.WB_COUNTRIES
ANIOS = range(2010, 2025)


def banco_mundial() -> list[dict]:
    """Cuadrícula completa 6 países × 6 indicadores × 2010–2024, conservando nulos."""
    observados = apis.banco_mundial()
    clave = {(r["pais_iso3"], r["indicador_id"], r["anio"]) for r in observados}
    out = list(observados)
    hoy = datetime.now(UTC).isoformat()
    for c in WB_COUNTRIES:
        for i in WB_INDICATORS:
            for anio in ANIOS:
                if (c, i, anio) not in clave:
                    out.append(
                        {
                            "tipo": "indicador",
                            "pais_iso3": c,
                            "indicador_id": i,
                            "anio": anio,
                            "valor": None,
                            "unidad": apis._unidad_wb(i),
                            "fuente_url": f"https://api.worldbank.org/v2/country/{c}/indicator/{i}",
                            "fecha_extraccion": hoy,
                            "licencia": "CC BY 4.0",
                        }
                    )
    return out


def usgs(desde: str = "2024-01-01", hasta: str = "2026-10-01", minmag: float = 3.0) -> list[dict]:
    """Sismos USGS en la caja regional, con URL real del evento."""
    out = []
    for s in apis.usgs(desde, hasta, minmag):
        s["tipo"] = "sismo"
        out.append(s)
    return out


_DOMINIOS_OFICIALES = ("inec.gob.pa", "superbancos.gob.pa", "pancanal.com")


def _validar_fila_manual(fuente: str, row: dict) -> str | None:
    """Valida una fila transcrita a mano. Devuelve el motivo si es inválida, o None."""
    from urllib.parse import urlparse

    periodo = (row.get("periodo") or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}", periodo):
        return f"periodo inválido: {periodo!r}"
    if not (S.VENTANA_INICIO.strftime("%Y-%m") <= periodo <= S.VENTANA_FIN.strftime("%Y-%m")):
        return f"periodo fuera de ventana: {periodo}"

    valor = (row.get("valor") or "").strip()
    if valor in ("", None):
        return "valor vacío"
    try:
        float(valor)
    except ValueError:
        return f"valor no numérico: {valor!r}"

    url = (row.get("url") or "").strip()
    dominio = urlparse(url).netloc.lower()
    if not any(dominio == d or dominio.endswith("." + d) for d in _DOMINIOS_OFICIALES):
        return f"dominio no oficial: {dominio!r}"

    if url.lower().endswith(".pdf") and row.get("pagina"):
        try:
            int(row["pagina"])
        except ValueError:
            return f"pagina no entera: {row['pagina']!r}"
    return None


def _leer_manual(fuente: str) -> list[dict]:
    """Lee series transcritas a mano desde data/raw/manual/<fuente>.csv (validando)."""
    path = S.RAW_DIR / "manual" / f"{fuente}.csv"
    if not path.exists():
        return []
    out = []
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            motivo = _validar_fila_manual(fuente, row)
            if motivo:
                print(f"[cuarentena manual/{fuente}.csv] {motivo}: {row}", file=sys.stderr)
                continue
            out.append(
                {
                    "tipo": "serie_oficial",
                    "id": f"of-{fuente}-{row['serie']}-{row['periodo']}",
                    "fuente_id": fuente,
                    "serie": row["serie"].strip(),
                    "periodo": row["periodo"].strip(),
                    "valor": float(row["valor"]),
                    "unidad": row.get("unidad", "").strip(),
                    "url": row.get("url", "").strip(),
                    "pagina": int(row["pagina"]) if row.get("pagina") else None,
                    "fecha_extraccion": row.get("fecha", "").strip(),
                    "condiciones": "Transcrito a mano; verificar contra la fuente.",
                    "transcrito_por": row.get("transcrito_por", "").strip(),
                }
            )
    return out


def inec() -> list[dict]:
    return _leer_manual("inec")


def acp() -> list[dict]:
    return _leer_manual("acp")


def sbp() -> list[dict]:
    return _leer_manual("sbp")
