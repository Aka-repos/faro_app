"""Orquestador de recolección real (F-01, H1–H2).

Recorre `config/fuentes.yaml` por método (RSS → sitemap → GDELT → oficiales),
deduplica por URL normalizada y escribe `data/raw/{noticias,series,indicadores,sismos}.jsonl`.

Reglas: nunca mezclar con el seed; si hay registros `sintetico: true` en raw, aborta.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import config.settings as S
from faro.loaders import load_fuentes
from faro.quality.validate import normalize_url
from faro.scrape import apis, html, oficiales, politeness, rss, sitemap


def _meses(desde, hasta) -> list[tuple[str, str]]:
    """Lista de (inicio, fin) mensuales en formato GDELT (YYYYMMDDHHMMSS)."""
    import calendar

    out = []
    y, m = desde.year, desde.month
    fin = (hasta.year, hasta.month)
    while (y, m) <= fin:
        ultimo = calendar.monthrange(y, m)[1]
        ini = f"{y:04d}{m:02d}01000000"
        f = f"{y:04d}{m:02d}{ultimo:02d}235959"
        out.append((ini, f))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


def _recolectar_noticias(
    fuentes: list[dict], client: politeness.PoliteClient, desde, hasta
) -> tuple[list[dict], dict]:
    """RSS + sitemap + GDELT -> lista de noticias normalizadas."""
    noticias: list[dict] = []
    reporte: dict[str, dict] = {}

    for f in fuentes:
        if f.get("familia") != "noticias":
            continue
        fid = f["id"]
        medio = f["nombre"]
        reporte[fid] = {"intentos": 0, "ok": 0, "robots": 0, "errores": 0, "en_ventana": 0}

        # RSS
        if f.get("metodo") == "rss" and f.get("rss_url"):
            reporte[fid]["intentos"] += 1
            try:
                filas = rss.parse_rss(f["rss_url"], fuente_id=fid, medio=medio, client=client)
                noticias.extend(filas)
                reporte[fid]["ok"] += len(filas)
            except Exception:  # noqa: BLE001
                reporte[fid]["errores"] += 1

        # Sitemap
        if f.get("sitemap_url"):
            reporte[fid]["intentos"] += 1
            try:
                entradas = sitemap.parse_sitemap(f["sitemap_url"], client=client)
                for e in entradas[:500]:
                    if e.get("es_indice"):
                        sub = sitemap.parse_sitemap(e["url"], client=client)
                        for s2 in sub[:500]:
                            art = html.extract_article(
                                s2["url"], client=client, fuente_id=fid, medio=medio
                            )
                            if art.get("titulo"):
                                noticias.append(art)
                                reporte[fid]["ok"] += 1
                    else:
                        art = html.extract_article(
                            e["url"], client=client, fuente_id=fid, medio=medio
                        )
                        if art.get("titulo"):
                            noticias.append(art)
                            reporte[fid]["ok"] += 1
            except Exception as e:  # noqa: BLE001
                reporte[fid]["errores"] += 1

    # GDELT (12 meses) para TVN y por dominio, y por país+tema.
    try:
        for ini, fin in _meses(desde, hasta):
            for q in ["domain:tvn-2.com", "sourcecountry:PM"]:
                filas = apis.gdelt(q, ini, fin, maxrec=250)
                noticias.extend(filas)
                reporte.setdefault("gdelt", {"intentos": 0, "ok": 0, "robots": 0, "errores": 0})
                reporte["gdelt"]["intentos"] += 1
                reporte["gdelt"]["ok"] += len(filas)
    except Exception:  # noqa: BLE001
        reporte.setdefault("gdelt", {"intentos": 0, "ok": 0, "robots": 0, "errores": 0})
        reporte["gdelt"]["errores"] += 1

    return noticias, reporte


def recolectar(fuentes: list[str] | None = None, desde=None, hasta=None) -> dict:
    """Recolección real completa. Devuelve conteos por tipo y por fuente."""
    desde = desde or S.VENTANA_INICIO
    hasta = hasta or S.VENTANA_FIN
    S.ensure_dirs()

    # Protección: nunca mezclar con el seed.
    for f in S.RAW_DIR.glob("*.jsonl"):
        for linea in f.read_text(encoding="utf-8").splitlines():
            if '"sintetico": true' in linea:
                raise RuntimeError(
                    f"data/raw contiene datos sintéticos ({f.name}). Borra el snapshot o usa make data-seed."
                )

    cfg = load_fuentes()
    if fuentes:
        ids = set(fuentes)
        cfg = [f for f in cfg if f["id"] in ids]

    client = politeness.PoliteClient(rate_limit_s=3.0)
    noticias, reporte = _recolectar_noticias(cfg, client, desde, hasta)

    # Oficiales.
    indicadores = oficiales.banco_mundial()
    sismos = oficiales.usgs()
    series = oficiales.inec() + oficiales.acp() + oficiales.sbp()
    reporte["banco_mundial"] = {"ok": len(indicadores)}
    reporte["usgs"] = {"ok": len(sismos)}
    reporte["oficiales_manual"] = {"ok": len(series)}

    # Deduplicar noticias por URL normalizada, conservando la más completa.
    por_url: dict[str, dict] = {}
    for n in noticias:
        nu = normalize_url(n["url"])
        actual = por_url.get(nu)
        if actual is None or (n.get("fecha_publicacion") and not actual.get("fecha_publicacion")):
            por_url[nu] = n
    noticias = list(por_url.values())

    _escribir("noticias.jsonl", noticias)
    _escribir("series.jsonl", series)
    _escribir("indicadores.jsonl", indicadores)
    _escribir("sismos.jsonl", sismos)

    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    resumen = {
        "fecha": datetime.now(UTC).isoformat(),
        "conteos": {
            "noticias": len(noticias),
            "series": len(series),
            "indicadores": len(indicadores),
            "sismos": len(sismos),
        },
        "por_fuente": reporte,
    }
    (S.REPORTS_DIR / f"recoleccion_{ts}.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2, default=str)
    )
    return resumen


def _escribir(nombre: str, filas: list[dict]) -> None:
    with open(S.RAW_DIR / nombre, "w", encoding="utf-8") as fh:
        for r in filas:
            fh.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
