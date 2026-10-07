"""APIs: GDELT DOC 2.0, Banco Mundial v2 y USGS FDSN (H2)."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

import config.settings as S

WB_INDICATORS = [
    "NY.GDP.MKTP.KD.ZG",  # crecimiento PIB
    "FP.CPI.TOTL.ZG",  # inflación
    "SL.UEM.TOTL.ZS",  # desempleo
    "SP.POP.TOTL",  # población
    "IT.NET.USER.ZS",  # uso de internet
    "NE.EXP.GNFS.ZS",  # exportaciones/PIB
]
WB_COUNTRIES = ["PAN", "CRI", "COL", "DOM", "MEX", "GTM"]


def _iso(dt) -> str:
    return dt.astimezone(UTC).isoformat() if dt else ""


def gdelt(
    query: str, start: str, end: str, domain: str | None = None, maxrec: int = 250
) -> list[dict]:
    """GDELT DOC 2.0 ArtList por ventana temporal. Devuelve metadatos de enlaces."""
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "startdatetime": start,
        "enddatetime": end,
        "maxrecords": maxrec,
        "sort": "datedesc",
    }
    if domain:
        params["query"] = f"{query} domain:{domain}"
    try:
        r = httpx.get(
            url, params=params, timeout=S.HTTP_TIMEOUT, headers={"User-Agent": S.USER_AGENT}
        )
        r.raise_for_status()
        data = r.json()
    except Exception:  # noqa: BLE001
        return []
    out = []
    for a in data.get("articles", []):
        out.append(
            {
                "id": f"n-{a.get('url', '')}",
                "titulo": a.get("title", ""),
                "url": a.get("url", ""),
                "medio": a.get("domain", ""),
                "fecha_publicacion": a.get("seendate", ""),
                "fecha_deteccion": a.get("seendate", ""),
                "alcance_texto": "titular",
            }
        )
    return out


def banco_mundial() -> list[dict]:
    """Descarga la cuadrícula país x indicador x año (2010–2024), conservando nulos."""
    out = []
    base = "https://api.worldbank.org/v2/country/{c}/indicator/{i}"
    for c in WB_COUNTRIES:
        for i in WB_INDICATORS:
            try:
                r = httpx.get(
                    base.format(c=c, i=i),
                    params={"format": "json", "per_page": 100, "date": "2010:2024"},
                    timeout=S.HTTP_TIMEOUT,
                    headers={"User-Agent": S.USER_AGENT},
                )
                r.raise_for_status()
                payload = r.json()
                if len(payload) < 2:
                    continue
                for row in payload[1]:
                    if row.get("value") is not None:
                        out.append(
                            {
                                "pais_iso3": c,
                                "indicador_id": i,
                                "anio": int(row["date"]),
                                "valor": float(row["value"]),
                                "unidad": _unidad_wb(i),
                                "fuente_url": f"https://api.worldbank.org/v2/country/{c}/indicator/{i}",
                                "fecha_extraccion": _iso(datetime.now(UTC)),
                                "licencia": "CC BY 4.0",
                            }
                        )
            except Exception:  # noqa: BLE001
                continue
    return out


def _unidad_wb(i: str) -> str:
    return {
        "NY.GDP.MKTP.KD.ZG": "% anual",
        "FP.CPI.TOTL.ZG": "% anual",
        "SL.UEM.TOTL.ZS": "% de la fuerza laboral",
        "SP.POP.TOTL": "personas",
        "IT.NET.USER.ZS": "% de la población",
        "NE.EXP.GNFS.ZS": "% del PIB",
    }.get(i, "")


def usgs(start: str, end: str, minmag: float = 3.0) -> list[dict]:
    """USGS FDSN: sismos en la caja regional (5–12, −86..−76) desde 2024."""
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "starttime": start,
        "endtime": end,
        "minmagnitude": minmag,
        "minlatitude": 5.0,
        "maxlatitude": 12.0,
        "minlongitude": -86.0,
        "maxlongitude": -76.0,
    }
    try:
        r = httpx.get(
            url, params=params, timeout=S.HTTP_TIMEOUT, headers={"User-Agent": S.USER_AGENT}
        )
        r.raise_for_status()
        data = r.json()
    except Exception:  # noqa: BLE001
        return []
    out = []
    for f in data.get("features", []):
        p = f.get("properties", {})
        g = f.get("geometry", {})
        coords = g.get("coordinates", [0, 0, 0])
        out.append(
            {
                "id": p.get("id", ""),
                "magnitud": p.get("mag"),
                "fecha": _iso(datetime.fromtimestamp(p.get("time", 0) / 1000, tz=UTC)),
                "lat": coords[1],
                "lon": coords[0],
                "profundidad": coords[2],
                "lugar": p.get("place", ""),
                "status": p.get("status", ""),
                "url": p.get("url", ""),
            }
        )
    return out


def _probe_api(fuente_id: str, client: httpx.Client) -> int | None:
    """Sondeo ligero para `check-sources` (sin descargar todo)."""
    try:
        if fuente_id == "gdelt":
            r = client.get(
                "https://api.gdeltproject.org/api/v2/doc/doc",
                params={"query": "Panama", "mode": "artlist", "format": "json", "maxrecords": 5},
            )
            return len(r.json().get("articles", [])) or None
        if fuente_id == "banco_mundial":
            r = client.get(
                "https://api.worldbank.org/v2/country/PAN/indicator/NY.GDP.MKTP.KD.ZG",
                params={"format": "json", "per_page": 5},
            )
            payload = r.json()
            return len(payload[1]) if len(payload) > 1 else None
        if fuente_id == "usgs":
            r = client.get(
                "https://earthquake.usgs.gov/fdsnws/event/1/query",
                params={"format": "geojson", "starttime": "2024-01-01", "minmagnitude": 5},
            )
            return len(r.json().get("features", [])) or None
    except Exception:  # noqa: BLE001
        return None
    return None
