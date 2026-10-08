"""Punto 1: TVN por sitemaps mensuales."""

from __future__ import annotations

from pathlib import Path

from faro.scrape import collect, sitemap

FIXTURE = Path(__file__).parent / "fixtures" / "tvn_sitemap_mensual.xml"
INCLUIR = ["nacionales", "economia", "contenido-exclusivo"]
EXCLUIR = [
    "tvmax",
    "entretenimiento",
    "mundo",
    "videos",
    "jelou",
    "tvnpass",
    "tu-cara-me-suena",
    "la-loteria",
]


def test_parse_tvn_mensual():
    entradas = sitemap.parse_tvn_mensual(FIXTURE.read_text(encoding="utf-8"))
    assert len(entradas) == 5
    primera = entradas[0]
    assert primera["titulo"] == "Ejecutivo frena ley que proponía descuento del 25% en seguros"
    assert primera["url"].startswith("https://www.tvn-2.com/nacionales/")
    assert primera["fecha_publicacion"]  # lastmod convertido a ISO


def test_seccion_permitida():
    assert (
        collect._seccion_permitida("https://www.tvn-2.com/nacionales/x", INCLUIR, EXCLUIR) is True
    )
    assert collect._seccion_permitida("https://www.tvn-2.com/economia/x", INCLUIR, EXCLUIR) is True
    assert (
        collect._seccion_permitida("https://www.tvn-2.com/contenido-exclusivo/x", INCLUIR, EXCLUIR)
        is True
    )
    assert collect._seccion_permitida("https://www.tvn-2.com/tvmax/x", INCLUIR, EXCLUIR) is False
    assert collect._seccion_permitida("https://www.tvn-2.com/mundo/x", INCLUIR, EXCLUIR) is False


def test_muestrear_mes_uniforme_limite():
    arts = [
        {"fecha_publicacion": f"2025-10-{d:02d}T12:00:00+00:00", "url": f"u{d}-{i}"}
        for d in range(1, 11)
        for i in range(30)
    ]
    muestra = collect._muestrear_mes(arts, 150, seed=42)
    assert len(muestra) == 150
    # repartido entre los días (uniforme por día)
    dias = {(a["fecha_publicacion"] or "")[:10] for a in muestra}
    assert len(dias) >= 8


class _Resp:
    def __init__(self, text=""):
        self.status_code = 200
        self.text = text


class _Cliente:
    def __init__(self, texto):
        self._texto = texto

    def get(self, url, fuente_id="", **kw):
        return _Resp(self._texto)


def test_recolectar_tvn_sitemaps_flujo(monkeypatch, tmp_path):
    from datetime import datetime

    monkeypatch.setattr(collect, "_TVN_SITEMAPS_DIR", tmp_path)
    noticias: list[dict] = []
    reporte = {"tvn": {"intentos": 0, "ok": 0}}
    f = {
        "id": "tvn",
        "nombre": "TVN Panamá",
        "max_por_mes": 150,
        "secciones_incluir": INCLUIR,
        "secciones_excluir": EXCLUIR,
    }
    desde = datetime(2025, 10, 2)
    hasta = datetime(2025, 11, 1)  # solo 2025_10
    client = _Cliente(FIXTURE.read_text(encoding="utf-8"))

    collect._recolectar_tvn_sitemaps(f, client, desde, hasta, noticias, reporte)

    urls = [n["url"] for n in noticias]
    # tvmax y la nota sin título quedan fuera; nacionales/economia/contenido-exclusivo entran.
    assert len(noticias) == 3
    assert all("tvmax" not in u for u in urls)
    assert any("/economia/" in u for u in urls)
    assert any("/contenido-exclusivo/" in u for u in urls)
    # no abrir páginas: alcance textual y via sitemap.
    assert all(n["via"] == "sitemap" and n["alcance_texto"] == "titular" for n in noticias)
    # reporte mensual con los conteos
    mes = reporte["tvn"]["mensual"][0]
    assert mes["disponibles"] == 5
    assert mes["tras_filtro"] == 3
    assert mes["muestreadas"] == 3
    assert mes["origen"] == "red"
