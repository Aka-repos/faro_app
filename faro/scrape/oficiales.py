"""Fuentes oficiales (H2): Banco Mundial, USGS, INEC, ACP y SBP.

Regla dura: **nunca inventar un valor**. Si una fuente no se puede automatizar en
~1 h, se transcribe a mano en `data/raw/manual/<fuente>.csv` (trazable) o se deja
faltante. Aquí no se fabrican series.
"""

from __future__ import annotations

import csv
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


def _leer_manual(fuente: str) -> list[dict]:
    """Lee series transcritas a mano desde data/raw/manual/<fuente>.csv."""
    path = S.RAW_DIR / "manual" / f"{fuente}.csv"
    if not path.exists():
        return []
    out = []
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            valor = row.get("valor")
            out.append(
                {
                    "tipo": "serie_oficial",
                    "id": f"of-{fuente}-{row['serie']}-{row['periodo']}",
                    "fuente_id": fuente,
                    "serie": row["serie"],
                    "periodo": row["periodo"],
                    "valor": float(valor) if valor not in (None, "") else None,
                    "unidad": row.get("unidad", ""),
                    "url": row.get("url", ""),
                    "pagina": int(row["pagina"]) if row.get("pagina") else None,
                    "fecha_extraccion": row.get("fecha", ""),
                    "condiciones": "Transcrito a mano; verificar contra la fuente.",
                    "transcrito_por": row.get("transcrito_por", ""),
                }
            )
    return out


def inec() -> list[dict]:
    return _leer_manual("inec")


def acp() -> list[dict]:
    return _leer_manual("acp")


def sbp() -> list[dict]:
    return _leer_manual("sbp")
