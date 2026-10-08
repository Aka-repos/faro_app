"""Orquestador de recolección real (F-01, M1).

Recorre `config/fuentes.yaml` por método (RSS → sitemap → GDELT → oficiales),
deduplica por URL normalizada y escribe `data/raw/{noticias,series,indicadores,sismos}.jsonl`.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import config.settings as S
from faro.loaders import load_fuentes, load_keywords
from faro.quality.validate import normalize_url
from faro.scrape import apis, html, oficiales, politeness, rss, sitemap

_TVN_SITEMAPS_DIR = S.REPO_ROOT / "data" / "cache" / "tvn_sitemaps"


def _meses(desde, hasta) -> list[tuple[str, str]]:
    """Meses entre `desde` y `hasta` (hasta EXCLUSIVO)."""
    import calendar

    out = []
    y, m = desde.year, desde.month
    fin = (hasta.year, hasta.month)
    while (y, m) < fin:
        ultimo = calendar.monthrange(y, m)[1]
        out.append((f"{y:04d}{m:02d}01000000", f"{y:04d}{m:02d}{ultimo:02d}235959"))
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


def _en_ventana(fecha: str | None) -> bool:
    """True si la fecha ISO está en [VENTANA_INICIO, VENTANA_FIN); sin fecha -> True."""
    if not fecha:
        return True
    try:
        dt = datetime.fromisoformat(str(fecha).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return S.VENTANA_INICIO <= dt < S.VENTANA_FIN
    except ValueError:
        return True  # la valida validate.py


def _seccion_permitida(url: str, incluir: list[str], excluir: list[str]) -> bool:
    """Filtra por el primer segmento de la ruta (sección)."""
    from urllib.parse import urlparse

    seg = urlparse(url).path.lstrip("/").split("/")[0].lower()
    if not seg:
        return False
    if seg in [x.lower() for x in excluir]:
        return False
    return seg in [x.lower() for x in incluir]


def _muestrear_mes(articulos: list[dict], max_por_mes: int, seed: int = 42) -> list[dict]:
    """Muestreo uniforme por día con semilla fija (máx. max_por_mes por mes)."""
    import random
    from collections import defaultdict

    if len(articulos) <= max_por_mes:
        return articulos
    por_dia: dict[str, list] = defaultdict(list)
    for a in articulos:
        por_dia[(a.get("fecha_publicacion") or "")[:10] or "sin_fecha"].append(a)
    rng = random.Random(seed)
    for dia in por_dia:
        rng.shuffle(por_dia[dia])
    dias = sorted(por_dia.keys())
    muestra: list[dict] = []
    i = 0
    while len(muestra) < max_por_mes:
        avanza = False
        for dia in dias:
            if i < len(por_dia[dia]) and len(muestra) < max_por_mes:
                muestra.append(por_dia[dia][i])
                avanza = True
        i += 1
        if not avanza:
            break
    return muestra


def _obtener_tvn_mes(nombre: str, url: str, cache_dir, client) -> tuple[str | None, str]:
    """Devuelve (texto_xml|None, origen). Lee caché local si existe y no está vacío."""
    local = cache_dir / nombre
    if local.exists() and local.stat().st_size > 0:
        return local.read_text(encoding="utf-8"), "cache local"
    resp = client.get(url, fuente_id="tvn")
    if resp is None or resp.status_code >= 400:
        return None, "sin respuesta (red)"
    texto = resp.text or ""
    if not texto.strip():
        local.write_text("", encoding="utf-8")
        return None, "vacío en el origen"
    local.write_text(texto, encoding="utf-8")
    return texto, "red"


def _recolectar_tvn_sitemaps(f, client, desde, hasta, noticias, reporte) -> None:
    """TVN por sitemaps mensuales (prioridad): tvn_sitemap_contents_AAAA_MM.xml."""
    fid = f["id"]
    medio = f["nombre"]
    max_por_mes = int(f.get("max_por_mes", 150))
    incluir = f.get("secciones_incluir", [])
    excluir = f.get("secciones_excluir", [])
    cache_dir = _TVN_SITEMAPS_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    reporte[fid].setdefault("mensual", [])

    for ini, _fin in _meses(desde, hasta):
        aaaa_mm = f"{ini[:4]}_{ini[4:6]}"
        nombre = f"tvn_sitemap_contents_{aaaa_mm}.xml"
        url = f"https://www.tvn-2.com/{nombre}"
        texto, origen = _obtener_tvn_mes(nombre, url, cache_dir, client)
        if texto is None:
            reporte[fid]["mensual"].append(
                {
                    "mes": ini[:6],
                    "disponibles": 0,
                    "tras_filtro": 0,
                    "muestreadas": 0,
                    "origen": origen,
                }
            )
            print(f"    {fid} {ini[:6]}: 0 ({origen})")
            continue
        entradas = sitemap.parse_tvn_mensual(texto)
        disponibles = len(entradas)
        # Descartar sin título y filtrar por sección.
        filtradas = [
            e
            for e in entradas
            if e.get("titulo") and _seccion_permitida(e["url"], incluir, excluir)
        ]
        tras_filtro = len(filtradas)
        muestra = _muestrear_mes(filtradas, max_por_mes, seed=42)
        for e in muestra:
            noticias.append(
                {
                    "tipo": "noticia",
                    "id": f"n-{_hash_url(e['url'])}",
                    "fuente_id": fid,
                    "titulo": e["titulo"][:300],
                    "url": e["url"],
                    "medio": medio,
                    "dominio": _dominio(e["url"]),
                    "idioma": "es",
                    "fecha_publicacion": e["fecha_publicacion"],
                    "fecha_deteccion": e["fecha_publicacion"],
                    "fecha_extraccion": datetime.now(UTC).isoformat(),
                    "alcance_texto": "titular",
                    "resumen": None,
                    "es_agencia": False,
                    "agencia": None,
                    "sintetico": False,
                    "via": "sitemap",
                }
            )
        reporte[fid]["mensual"].append(
            {
                "mes": ini[:6],
                "disponibles": disponibles,
                "tras_filtro": tras_filtro,
                "muestreadas": len(muestra),
                "origen": origen,
            }
        )
        reporte[fid]["ok"] += len(muestra)
        print(
            f"    {fid} {ini[:6]}: {disponibles} disponibles, {tras_filtro} tras filtro, "
            f"{len(muestra)} muestreadas ({origen})"
        )


def _recolectar_sitemap(f, client, noticias, reporte) -> None:
    """Sitemap acotado (M1.4): respeta max_articulos/max_subsitemaps y news:title."""
    fid = f["id"]
    medio = f["nombre"]
    max_art = int(f.get("max_articulos", 300))
    max_sub = int(f.get("max_subsitemaps", 24))
    reporte[fid].setdefault("omitidas_por_limite", 0)
    reporte[fid].setdefault("omitidas_fuera_de_ventana", 0)

    entradas = sitemap.parse_sitemap(f["sitemap_url"], client=client)
    sub_contados = 0
    articulos: list[dict] = []
    for e in entradas:
        if e.get("es_indice"):
            if sub_contados >= max_sub:
                continue
            sub_contados += 1
            for s2 in sitemap.parse_sitemap(e["url"], client=client):
                if s2.get("es_indice"):
                    continue
                if s2.get("titulo") and s2.get("fecha_publicacion"):
                    # news:title + publication_date -> no abrir la página.
                    articulos.append(
                        {
                            "tipo": "noticia",
                            "id": f"n-{_hash_url(s2['url'])}",
                            "fuente_id": fid,
                            "titulo": s2["titulo"][:300],
                            "url": s2["url"],
                            "medio": medio,
                            "dominio": _dominio(s2["url"]),
                            "idioma": "es",
                            "fecha_publicacion": s2["fecha_publicacion"],
                            "fecha_deteccion": s2["fecha_publicacion"],
                            "fecha_extraccion": datetime.now(UTC).isoformat(),
                            "alcance_texto": "titular",
                            "resumen": None,
                            "es_agencia": False,
                            "agencia": None,
                            "sintetico": False,
                            "via": "sitemap",
                        }
                    )
                else:
                    art = html.extract_article(s2["url"], client=client, fuente_id=fid, medio=medio)
                    if art.get("titulo"):
                        art["via"] = "sitemap"
                        articulos.append(art)
        else:
            if e.get("titulo") and e.get("fecha_publicacion"):
                articulos.append(
                    {
                        "tipo": "noticia",
                        "id": f"n-{_hash_url(e['url'])}",
                        "fuente_id": fid,
                        "titulo": e["titulo"][:300],
                        "url": e["url"],
                        "medio": medio,
                        "dominio": _dominio(e["url"]),
                        "idioma": "es",
                        "fecha_publicacion": e["fecha_publicacion"],
                        "fecha_deteccion": e["fecha_publicacion"],
                        "fecha_extraccion": datetime.now(UTC).isoformat(),
                        "alcance_texto": "titular",
                        "resumen": None,
                        "es_agencia": False,
                        "agencia": None,
                        "sintetico": False,
                        "via": "sitemap",
                    }
                )
            else:
                art = html.extract_article(e["url"], client=client, fuente_id=fid, medio=medio)
                if art.get("titulo"):
                    art["via"] = "sitemap"
                    articulos.append(art)

    # Muestreo uniforme por mes si se supera max_articulos.
    if len(articulos) > max_art:
        reporte[fid]["omitidas_por_limite"] += len(articulos) - max_art
        por_mes: dict[str, list] = {}
        for a in articulos:
            mes = (a.get("fecha_publicacion") or "")[:7] or "sin_fecha"
            por_mes.setdefault(mes, []).append(a)
        muestra = []
        for _mes, filas in por_mes.items():
            k = max(1, round(max_art * len(filas) / len(articulos)))
            paso = max(1, len(filas) // k)
            muestra.extend(filas[::paso][:k])
        articulos = muestra[:max_art]

    noticias.extend(articulos)
    reporte[fid]["ok"] += len(articulos)


def _recolectar_noticias(fuentes, client, desde, hasta) -> tuple[list[dict], dict]:
    """RSS + sitemap + GDELT -> lista de noticias normalizadas."""
    noticias: list[dict] = []
    reporte: dict[str, dict] = {}

    for f in fuentes:
        if f.get("familia") != "noticias" or f["id"] == "gdelt":
            continue
        fid = f["id"]
        if f.get("deshabilitado"):
            reporte[fid] = {"deshabilitado": True, "motivo": f.get("motivo_deshabilitado", "")}
            continue
        reporte[fid] = {
            "intentos": 0,
            "ok": 0,
            "robots": 0,
            "errores": 0,
            "omitidas_por_limite": 0,
            "omitidas_fuera_de_ventana": 0,
        }
        if f.get("metodo") == "rss" and f.get("rss_url"):
            reporte[fid]["intentos"] += 1
            try:
                filas = rss.parse_rss(f["rss_url"], fuente_id=fid, medio=f["nombre"], client=client)
                # Punto 6: descartar ítems fuera de ventana al recolectar (no solo en validación).
                dentro, fuera = [], []
                for x in filas:
                    fecha = x.get("fecha_publicacion") or x.get("fecha_deteccion")
                    (dentro if _en_ventana(fecha) else fuera).append(x)
                reporte[fid]["omitidas_fuera_de_ventana"] += len(fuera)
                noticias.extend(dentro)
                reporte[fid]["ok"] += len(dentro)
                print(f"    {fid}: RSS {len(dentro)} dentro de ventana, {len(fuera)} fuera")
            except Exception as e:  # noqa: BLE001
                reporte[fid]["errores"] += 1
                reporte[fid].setdefault("error", str(e)[:120])
        if f.get("sitemap_mensual"):
            reporte[fid]["intentos"] += 1
            try:
                _recolectar_tvn_sitemaps(f, client, desde, hasta, noticias, reporte)
            except Exception as e:  # noqa: BLE001
                reporte[fid]["errores"] += 1
                reporte[fid].setdefault("error", str(e)[:120])
        elif f.get("sitemap_url"):
            reporte[fid]["intentos"] += 1
            try:
                _recolectar_sitemap(f, client, noticias, reporte)
            except Exception as e:  # noqa: BLE001
                reporte[fid]["errores"] += 1
                reporte[fid].setdefault("error", str(e)[:120])

    # GDELT (M1.2): por mes, con pausa y errores visibles por consulta.
    g = {"intentos": 0, "ok": 0, "errores": 0, "detalle": []}
    keywords = load_keywords()["temas"]
    temas_consulta = []
    for _tema, palabras in keywords.items():
        temas_consulta.append(f"({(' OR '.join(palabras[:3]))})")
    gclient = politeness.PoliteClient(rate_limit_s=6.0)
    for ini, fin in _meses(desde, hasta):
        consultas = [("domain:tvn-2.com", "")] + [("sourcecountry:PM", t) for t in temas_consulta]
        for base, tema in consultas:
            q = f"{base} {tema}".strip()
            g["intentos"] += 1
            filas, error = apis.gdelt(q, ini, fin, maxrec=250, client=gclient)
            if error:
                g["errores"] += 1
                g["detalle"].append({"mes": ini[:6], "query": q, "ok": False, "error": error})
                print(f"    gdelt {ini[:6]} '{q[:40]}': error {error}")
                continue
            noticias.extend(filas)
            g["ok"] += len(filas)
            g["detalle"].append({"mes": ini[:6], "query": q, "ok": True, "n": len(filas)})
            print(f"    gdelt {ini[:6]} '{q[:40]}': {len(filas)} filas")
    reporte["gdelt"] = g

    return noticias, reporte


def recolectar(fuentes: list[str] | None = None, desde=None, hasta=None) -> dict:
    """Recolección real completa. Devuelve conteos por tipo y por fuente.

    Progreso visible por etapa y guardado incremental de noticias.jsonl + reporte
    antes de las fuentes oficiales (punto 5).
    """
    import time as _time

    desde = desde or S.VENTANA_INICIO
    hasta = hasta or S.VENTANA_FIN
    S.ensure_dirs()

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

    t0 = _time.time()
    client = politeness.PoliteClient(rate_limit_s=3.0)
    print(f"[{_time.time() - t0:6.1f}s] Recolectando noticias (RSS + sitemaps + GDELT)...")
    noticias, reporte = _recolectar_noticias(cfg, client, desde, hasta)

    # Deduplicar y guardar incrementalmente ANTES de las fuentes oficiales.
    por_url: dict[str, dict] = {}
    for n in noticias:
        nu = normalize_url(n["url"])
        actual = por_url.get(nu)
        if actual is None or (n.get("fecha_publicacion") and not actual.get("fecha_publicacion")):
            por_url[nu] = n
    noticias = list(por_url.values())
    _escribir("noticias.jsonl", noticias)
    _escribir_reporte_parcial(reporte, len(noticias))
    print(f"[{_time.time() - t0:6.1f}s] Noticias: {len(noticias)} (guardadas en noticias.jsonl).")

    print(f"[{_time.time() - t0:6.1f}s] Banco Mundial...")
    indicadores, fallos_wb = oficiales.banco_mundial()
    print(
        f"[{_time.time() - t0:6.1f}s] Banco Mundial: {len(indicadores)} filas, {len(fallos_wb)} fallos."
    )
    print(f"[{_time.time() - t0:6.1f}s] USGS...")
    sismos = oficiales.usgs()
    print(f"[{_time.time() - t0:6.1f}s] USGS: {len(sismos)} sismos.")
    series_inec = oficiales.inec()
    series_sbp = oficiales.sbp()
    series_acp = oficiales.acp()
    series = series_inec + series_sbp + series_acp
    reporte["banco_mundial"] = {"ok": len(indicadores), "fallos": len(fallos_wb)}
    if fallos_wb:
        reporte["banco_mundial"]["detalle_fallos"] = fallos_wb[:20]
    reporte["usgs"] = {"ok": len(sismos)}
    reporte["inec"] = {"ok": len(series_inec), "no_disponible": len(series_inec) == 0}
    reporte["sbp"] = {"ok": len(series_sbp), "no_disponible": len(series_sbp) == 0}
    # Cambio 2: ACP fuera de alcance -> "no disponible" sin error.
    reporte["acp"] = {"ok": len(series_acp), "no_disponible": True}

    _escribir("series.jsonl", series)
    _escribir("indicadores.jsonl", indicadores)
    _escribir("sismos.jsonl", sismos)

    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    resumen = {
        "fecha": datetime.now(UTC).isoformat(),
        "duracion_s": round(_time.time() - t0, 1),
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
    print(f"[{_time.time() - t0:6.1f}s] Reporte final en reports/recoleccion_{ts}.json.")
    return resumen


def _hash_url(url: str) -> str:
    import hashlib
    from urllib.parse import urlparse

    u = urlparse(url.strip())
    return hashlib.sha1(f"{u.netloc.lower()}{u.path.rstrip('/')}".encode()).hexdigest()[:16]


def _dominio(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).netloc.lower()


def _escribir(nombre: str, filas: list[dict]) -> None:
    with open(S.RAW_DIR / nombre, "w", encoding="utf-8") as fh:
        for r in filas:
            fh.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")


def _escribir_reporte_parcial(reporte: dict, n_noticias: int) -> None:
    """Guarda un reporte parcial (antes de las fuentes oficiales)."""
    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    (S.REPORTS_DIR / f"recoleccion_{ts}_parcial.json").write_text(
        json.dumps(
            {"noticias": n_noticias, "por_fuente": reporte},
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )
